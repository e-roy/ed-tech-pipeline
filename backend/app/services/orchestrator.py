"""
Video Generation Orchestrator - Coordinates all microservices.

This is the CRITICAL PATH component that unblocks the entire team.
Updated to integrate script-based image generation workflow.
"""
# Version for tracking code changes in logs
ORCHESTRATOR_VERSION = "1.2.0-semantic-progression"

from sqlalchemy.orm import Session
from app.models.database import Session as SessionModel, Asset, GenerationCost, Script
from app.services.websocket_manager import WebSocketManager
from app.agents.base import AgentInput
from app.agents.prompt_parser import PromptParserAgent
from app.agents.batch_image_generator import BatchImageGeneratorAgent
from app.agents.video_generator import VideoGeneratorAgent
from app.agents.narrative_builder import NarrativeBuilderAgent
from app.agents.audio_pipeline import AudioPipelineAgent
from app.services.ffmpeg_compositor import FFmpegCompositor
from app.services.storage import StorageService
from app.config import get_settings
from typing import Dict, Any, Optional, List
import uuid
import os
import json
import asyncio
import time
import traceback
import secrets
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


def _write_errors_json(storage_service: StorageService, session_folder: str, error_data: Dict[str, Any]) -> None:
    """
    Write errors.json to the session folder in S3.
    
    Args:
        storage_service: Storage service instance
        session_folder: S3 path to session folder (e.g., "users/{user_id}/{session_id}")
        error_data: Dictionary containing error information
    """
    try:
        errors_s3_key = f"{session_folder}/errors.json"
        errors_json = json.dumps(error_data, indent=2, default=str)
        storage_service.upload_file_direct(
            errors_json.encode("utf-8"),
            errors_s3_key,
            content_type="application/json"
        )
        logger.info(f"Created errors.json at {errors_s3_key}")
    except Exception as e:
        logger.error(f"Failed to write errors.json: {e}")


async def _wait_for_images_folder(storage_service: StorageService, images_prefix: str, max_wait_seconds: int = 30, check_interval: float = 1.0) -> bool:
    """
    Wait for the images folder to be created (at least one file exists with the prefix).
    
    Args:
        storage_service: Storage service instance
        images_prefix: S3 prefix for images folder (e.g., "users/{user_id}/{session_id}/images/")
        max_wait_seconds: Maximum time to wait in seconds
        check_interval: Interval between checks in seconds
    
    Returns:
        True if images folder exists, False if timeout
    """
    start_time = time.time()
    
    while True:
        try:
            # Check if any files exist with the images prefix
            files = storage_service.list_files_by_prefix(images_prefix, limit=1)
            if files:
                logger.info(f"Images folder confirmed: found {len(files)} file(s) with prefix {images_prefix}")
                return True
        except Exception as e:
            logger.debug(f"Error checking images folder: {e}")
        
        elapsed = time.time() - start_time
        if elapsed >= max_wait_seconds:
            logger.warning(f"Timeout waiting for images folder after {elapsed:.1f}s")
            return False
        
        await asyncio.sleep(check_interval)
        logger.debug(f"Waiting for images folder... ({elapsed:.1f}s elapsed)")


class VideoGenerationOrchestrator:
    """
    Orchestrates the video generation pipeline across multiple services.

    Flow:
    1. Generate Images (Flux via Replicate)
    2. Generate Video Clips (Luma via Replicate)
    3. Compose Final Video (FFmpeg + Text/Audio overlay)
    """

    def __init__(self, websocket_manager: WebSocketManager):
        """
        Initialize the orchestrator.

        Args:
            websocket_manager: WebSocket manager for real-time updates
        """
        self.websocket_manager = websocket_manager

        # Initialize AI agents
        openai_api_key = settings.OPENAI_API_KEY
        replicate_api_key = settings.REPLICATE_API_KEY

        if not openai_api_key:
            logger.warning(
                "OPENAI_API_KEY not set - image and audio generation will fail. "
                "Add it to .env file."
            )

        if not replicate_api_key:
            logger.warning(
                "REPLICATE_API_KEY not set - some agents will fail at runtime. "
                "Add it to .env file."
            )

        self.prompt_parser = PromptParserAgent(replicate_api_key) if replicate_api_key else None
        self.image_generator = BatchImageGeneratorAgent(openai_api_key) if openai_api_key else None
        self.narrative_builder = NarrativeBuilderAgent(replicate_api_key) if replicate_api_key else None
        self.audio_pipeline = AudioPipelineAgent(openai_api_key) if openai_api_key else None

        # Initialize storage service for S3 uploads
        self.storage_service = StorageService()

        # Initialize Person C agents (Video Pipeline)
        # VideoGeneratorAgent uses Veo 3.1 via Replicate and uploads clips to S3
        self.video_generator = VideoGeneratorAgent(replicate_api_key, self.storage_service) if replicate_api_key else None
        
        # Initialize FFmpeg compositor (optional - only needed for video composition)
        try:
            self.ffmpeg_compositor = FFmpegCompositor()
        except RuntimeError as e:
            logger.warning(f"FFmpeg not available: {e}. Video composition will not work.")
            self.ffmpeg_compositor = None

    async def generate_images(
        self,
        db: Session,
        session_id: str,
        user_id: int,
        script_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate images from a video script.

        New workflow: Receives a script from the database, generates 2-3 images
        per script part (hook, concept, process, conclusion), uploads to S3,
        and returns micro_scenes structure.

        Args:
            db: Database session
            session_id: Session ID for tracking
            user_id: User ID making the request
            script_id: ID of the script in the database
            options: Additional options (model, images_per_part, etc.)

        Returns:
            Dict containing status, micro_scenes, and cost information
        """
        try:
            # Validate image generator is initialized
            if not self.image_generator:
                raise ValueError("Image generator not initialized - check REPLICATE_API_KEY")

            # Fetch script from database
            script = db.query(Script).filter(Script.id == script_id).first()
            if not script:
                raise ValueError(f"Script {script_id} not found")

            # Verify ownership
            if script.user_id != user_id:
                raise ValueError("Unauthorized: Script does not belong to this user")

            # Create or update session in database
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session:
                session = SessionModel(
                    id=session_id,
                    user_id=user_id,
                    status="generating_images",
                    prompt=f"Script-based generation: {script_id}",
                    options=options
                )
                db.add(session)
            else:
                session.status = "generating_images"
                session.prompt = f"Script-based generation: {script_id}"
                session.options = options
            db.commit()

            # Build script object for image generator
            script_data = {
                "hook": script.hook,
                "concept": script.concept,
                "process": script.process,
                "conclusion": script.conclusion
            }

            # Stage 1: Image Generation
            # Scale images based on segment duration
            # Calculate images per part based on duration
            images_per_part_config = {}
            for part_name in ["hook", "concept", "process", "conclusion"]:
                part_data = getattr(script, part_name)
                if part_data and isinstance(part_data, dict):
                    duration = float(part_data.get("duration", 10))
                    # Base: 1 image per 5 seconds, minimum 2, maximum 6
                    images_count = max(2, min(6, int(duration / 5) + 1))
                    images_per_part_config[part_name] = images_count
                else:
                    images_per_part_config[part_name] = 2

            total_images = sum(images_per_part_config.values())
            logger.info(f"[{session_id}] Images per part: {images_per_part_config}, Total: {total_images}")

            await self.websocket_manager.broadcast_status(
                session_id,
                status="image_generation",
                progress=20,
                details=f"Generating {total_images} images with semantic progression..."
            )

            image_gen_input = AgentInput(
                session_id=session_id,
                data={
                    "script": script_data,
                    "model": options.get("model", "flux-schnell") if options else "flux-schnell",
                    "images_per_part_config": images_per_part_config,  # Pass per-part config
                    "use_semantic_progression": True  # Enable semantic linking
                }
            )

            image_result = await self.image_generator.process(image_gen_input)

            if not image_result.success:
                raise ValueError(f"Image generation failed: {image_result.error}")

            # Track costs
            self._record_cost(
                db,
                session_id,
                agent="image_generator",
                model=options.get("model", "flux-schnell") if options else "flux-schnell",
                cost=image_result.cost,
                duration=image_result.duration
            )

            # Stage 2: Upload images to S3
            await self.websocket_manager.broadcast_status(
                session_id,
                status="uploading_images",
                progress=60,
                details="Uploading images to storage..."
            )

            micro_scenes = image_result.data["micro_scenes"]

            # Upload all images to S3 and update URLs
            for part_name in ["hook", "concept", "process", "conclusion"]:
                images = micro_scenes[part_name]["images"]

                for i, img_data in enumerate(images):
                    # Generate unique asset ID
                    asset_id = f"img_{part_name}_{i}_{uuid.uuid4().hex[:8]}"

                    # Download from Replicate and upload to S3
                    try:
                        s3_result = await self.storage_service.download_and_upload(
                            replicate_url=img_data["image"],
                            asset_type="image",
                            session_id=session_id,
                            asset_id=asset_id,
                            user_id=user_id
                        )
                        # Update image URL to S3 URL
                        img_data["image"] = s3_result["url"]
                        logger.info(f"[{session_id}] {part_name} image {i+1} uploaded to S3")
                    except Exception as e:
                        # Keep Replicate URL if S3 upload fails
                        logger.warning(
                            f"[{session_id}] S3 upload failed for {part_name} image {i+1}, "
                            f"using Replicate URL: {e}"
                        )

                    # Store in database
                    asset = Asset(
                        session_id=session_id,
                        type="image",
                        url=img_data["image"],
                        approved=True,  # Auto-approve like audio
                        asset_metadata={
                            "part": part_name,  # Use "part" to match audio convention
                            "part_index": i,
                            "asset_id": asset_id,
                            **img_data["metadata"]
                        }
                    )
                    db.add(asset)

            db.commit()

            # Update session status
            session.status = "images_ready"
            db.commit()

            # Final progress update
            total_cost = image_result.cost
            await self.websocket_manager.broadcast_status(
                session_id,
                status="images_ready",
                progress=100,
                details=f"Generated images for all script parts! Cost: ${total_cost:.3f}"
            )

            logger.info(
                f"[{session_id}] Script-based image generation complete: ${total_cost:.3f}"
            )

            # Build response with micro_scenes structure
            return {
                "status": "success",
                "session_id": session_id,
                "micro_scenes": {
                    "hook": micro_scenes["hook"],
                    "concept": micro_scenes["concept"],
                    "process": micro_scenes["process"],
                    "conclusion": micro_scenes["conclusion"],
                    "cost": str(total_cost)
                }
            }

        except Exception as e:
            logger.error(f"[{session_id}] Image generation failed: {e}")

            # Update session with error
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "failed"
                db.commit()

            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Image generation failed: {str(e)}"
            )

            return {
                "status": "error",
                "session_id": session_id,
                "message": str(e)
            }

    def _record_cost(
        self,
        db: Session,
        session_id: str,
        agent: str,
        model: str,
        cost: float,
        duration: float
    ):
        """
        Record agent execution cost in database.

        Args:
            db: Database session
            session_id: Session ID
            agent: Agent name
            model: Model used
            cost: Cost in USD
            duration: Duration in seconds
        """
        cost_record = GenerationCost(
            session_id=session_id,
            service=agent,  # Maps to 'service' column
            cost=cost,       # Maps to 'cost' column
            details={         # Store additional details in JSON field
                "model": model,
                "duration_seconds": duration,
                "agent": agent
            }
        )
        db.add(cost_record)
        db.commit()

    async def generate_clips(
        self,
        db: Session,
        session_id: str,
        user_id: int,
        video_prompt: str,
        clip_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate video clips using Stable Video Diffusion via Replicate.

        Integrated by Person C with Video Generator Agent.

        Args:
            db: Database session
            session_id: Session ID for tracking
            video_prompt: Prompt for video generation
            clip_config: Configuration for clip generation

        Returns:
            Dict containing status, generated clips, and cost information
        """
        try:
            # Validate video generator is initialized
            if not self.video_generator:
                raise ValueError("Video Generator not initialized - check REPLICATE_API_KEY")

            # Update session status
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "generating_clips"
                session.video_prompt = video_prompt
                session.clip_config = clip_config
                db.commit()

            # Get approved images from database
            approved_images = db.query(Asset).filter(
                Asset.session_id == session_id,
                Asset.type == "image",
                Asset.approved == True
            ).all()

            if not approved_images:
                raise ValueError("No approved images found for video generation")

            # Convert to format expected by Video Generator
            image_data_list = [
                {
                    "id": str(img.id),
                    "url": img.url,
                    "view_type": img.asset_metadata.get("view_type", "unknown") if img.asset_metadata else "unknown"
                }
                for img in approved_images
            ]

            # Send WebSocket progress update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="generating_clips",
                progress=60,
                details=f"Generating {len(image_data_list)} video clips with AI..."
            )

            logger.info(f"[{session_id}] Generating clips from {len(image_data_list)} approved images")

            # Call Video Generator Agent
            # Default to Gen-4-Turbo (fastest and cheapest for testing: $0.015/sec vs $0.20/sec)
            default_model = "gen-4-turbo"

            video_gen_input = AgentInput(
                session_id=session_id,
                data={
                    "approved_images": image_data_list,
                    "video_prompt": video_prompt,
                    "clip_duration": clip_config.get("clip_duration", 3.0) if clip_config else 3.0,  # Shorter clips for faster processing
                    "model": clip_config.get("model", default_model) if clip_config else default_model,
                    "user_id": user_id  # Pass user_id for S3 upload in video_generator
                }
            )

            video_result = await self.video_generator.process(video_gen_input)

            if not video_result.success:
                raise ValueError(f"Video generation failed: {video_result.error}")

            # Track costs
            self._record_cost(
                db,
                session_id,
                agent="video_generator",
                model=clip_config.get("model", default_model) if clip_config else default_model,
                cost=video_result.cost,
                duration=video_result.duration
            )

            # Store generated clips in database
            # Clips are already uploaded to S3 by video_generator
            clips = video_result.data["clips"]
            for i, clip_data in enumerate(clips):
                # Clips already have S3 URLs from video_generator
                storage_url = clip_data["url"]
                logger.info(f"[{session_id}] Clip {i+1} already in S3: {storage_url}")

                asset = Asset(
                    session_id=session_id,
                    type="video",
                    url=storage_url,  # S3 URL from video_generator
                    approved=False,
                    asset_metadata={
                        "source_image_id": clip_data["source_image_id"],
                        "duration": clip_data["duration"],
                        "resolution": clip_data["resolution"],
                        "fps": clip_data["fps"],
                        "model": clip_data["model"],
                        "scene_prompt": clip_data["scene_prompt"],
                        "motion_intensity": clip_data["motion_intensity"],
                        "cost": clip_data["cost"],
                        "generation_time": clip_data["generation_time"],
                        "asset_id": clip_data.get("id", f"clip_{uuid.uuid4().hex[:12]}")
                    }
                )
                db.add(asset)

            db.commit()

            # Update session status
            if session:
                session.status = "reviewing_clips"
                db.commit()

            # Update progress
            await self.websocket_manager.broadcast_status(
                session_id,
                status="clips_generated",
                progress=80,
                details=f"Generated {len(clips)} video clips! Cost: ${video_result.cost:.2f}"
            )

            logger.info(
                f"[{session_id}] Clip generation complete: "
                f"{len(clips)} clips, ${video_result.cost:.2f}"
            )

            return {
                "status": "success",
                "session_id": session_id,
                "clips": clips,
                "total_cost": video_result.cost,
                "scenes_planned": video_result.data.get("scenes_planned", [])
            }

        except Exception as e:
            logger.error(f"[{session_id}] Clip generation failed: {e}")

            # Update session with error
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "failed"
                db.commit()

            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Clip generation failed: {str(e)}"
            )

            return {
                "status": "error",
                "session_id": session_id,
                "message": str(e)
            }

    async def compose_final_video(
        self,
        db: Session,
        session_id: str,
        user_id: int,
        text_config: Optional[Dict[str, Any]] = None,
        audio_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compose final video with text overlays and audio using FFmpeg.

        Integrated by Person C with FFmpeg Compositor.

        Args:
            db: Database session
            session_id: Session ID for tracking
            text_config: Text overlay configuration
            audio_config: Audio configuration

        Returns:
            Dict containing status and final video URL
        """
        try:
            # Update session status
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "composing"
                session.text_config = text_config
                session.audio_config = audio_config
                db.commit()

            # Get approved clips from database
            approved_clips = db.query(Asset).filter(
                Asset.session_id == session_id,
                Asset.type == "video",
                Asset.approved == True
            ).all()

            if not approved_clips:
                raise ValueError("No approved clips found for composition")

            # Convert to format expected by FFmpeg Compositor
            clip_data_list = [
                {
                    "url": clip.url,
                    "duration": clip.asset_metadata.get("duration", 3.0) if clip.asset_metadata else 3.0
                }
                for clip in approved_clips
            ]

            # Send WebSocket progress update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="composing",
                progress=90,
                details=f"Composing {len(clip_data_list)} clips into final video..."
            )

            logger.info(f"[{session_id}] Composing final video from {len(clip_data_list)} approved clips")

            # Call FFmpeg Compositor
            composition_result = await self.ffmpeg_compositor.compose_final_video(
                clips=clip_data_list,
                text_config=text_config,
                audio_config=audio_config,
                session_id=session_id
            )

            final_video_path = composition_result["output_path"]
            duration = composition_result.get("duration", 0.0)

            logger.info(f"[{session_id}] Video composed at: {final_video_path}")

            # Store final video in database
            final_asset = Asset(
                session_id=session_id,
                type="final_video",
                url=final_video_path,  # Local path for now (TODO: upload to S3)
                approved=True,
                asset_metadata={
                    "duration": duration,
                    "num_clips": len(clip_data_list),
                    "text_config": text_config,
                    "audio_config": audio_config,
                    "resolution": "1920x1080",
                    "fps": 30
                }
            )
            db.add(final_asset)

            # Update session with final result
            if session:
                session.status = "completed"
                session.final_video_url = final_video_path
                session.completed_at = datetime.utcnow()
                db.commit()

            # Update progress
            await self.websocket_manager.broadcast_status(
                session_id,
                status="completed",
                progress=100,
                details="Video composition complete!"
            )

            logger.info(
                f"[{session_id}] Final video complete: "
                f"{duration:.1f}s, {len(clip_data_list)} clips"
            )

            return {
                "status": "success",
                "session_id": session_id,
                "video_url": final_video_path,
                "duration": duration,
                "num_clips": len(clip_data_list)
            }

        except Exception as e:
            logger.error(f"[{session_id}] Video composition failed: {e}")

            # Update session with error
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "failed"
                db.commit()

            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Video composition failed: {str(e)}"
            )

            return {
                "status": "error",
                "session_id": session_id,
                "message": str(e)
            }

    async def build_narrative(
        self,
        db: Session,
        user_id: int,
        topic: str,
        learning_objective: str,
        key_points: list[str]
    ) -> Dict[str, Any]:
        """
        Build a narrative script for a 60-second video using the Narrative Builder agent.

        Args:
            db: Database session
            user_id: User ID requesting the narrative
            topic: Main topic/subject of the video
            learning_objective: What the viewer should learn
            key_points: Array of key points to cover

        Returns:
            Dict containing session_id, script, and cost information
        """
        try:
            # Validate narrative builder is initialized
            if not self.narrative_builder:
                raise ValueError("Narrative Builder not initialized - check REPLICATE_API_KEY")

            logger.info(f"[User {user_id}] Building narrative for topic: {topic}")

            # Call Narrative Builder Agent
            narrative_input = AgentInput(
                session_id="",  # Will be generated by the agent
                data={
                    "user_id": user_id,
                    "topic": topic,
                    "learning_objective": learning_objective,
                    "key_points": key_points
                }
            )

            narrative_result = await self.narrative_builder.process(narrative_input)

            if not narrative_result.success:
                raise ValueError(f"Narrative building failed: {narrative_result.error}")

            # Extract session ID and script from result
            session_id = narrative_result.data["session_id"]
            script = narrative_result.data["script"]

            # Create session in database to track this narrative
            session = SessionModel(
                id=session_id,
                user_id=user_id,
                status="completed",
                prompt=f"Narrative: {topic}"
            )
            db.add(session)
            db.commit()

            # Track cost in database
            self._record_cost(
                db,
                session_id,
                agent="narrative_builder",
                model="meta-llama-3-70b",
                cost=narrative_result.cost,
                duration=narrative_result.duration
            )

            logger.info(
                f"[{session_id}] Narrative built successfully for user {user_id}, "
                f"cost: ${narrative_result.cost:.4f}"
            )

            return {
                "status": "success",
                "session_id": session_id,
                "script": script,
                "cost": narrative_result.cost,
                "duration": narrative_result.duration,
                "topic": topic,
                "learning_objective": learning_objective
            }

        except Exception as e:
            logger.error(f"[User {user_id}] Narrative building failed: {e}")

            return {
                "status": "error",
                "message": str(e)
            }

    async def generate_audio(
        self,
        db: Session,
        session_id: str,
        user_id: int,
        script_id: str,
        audio_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate audio narration from script using ElevenLabs TTS.

        Args:
            db: Database session
            session_id: Session ID for tracking
            user_id: User ID making the request
            script_id: ID of the script in the database
            audio_config: Audio configuration (voice_id, audio_option, etc.)

        Returns:
            Dict containing status, audio files, and cost information
        """
        try:
            # Validate audio pipeline is initialized
            if not self.audio_pipeline:
                raise ValueError("Audio pipeline not initialized - check ELEVENLABS_API_KEY")

            # Fetch script from database
            script = db.query(Script).filter(Script.id == script_id).first()
            if not script:
                raise ValueError(f"Script {script_id} not found")

            # Verify ownership
            if script.user_id != user_id:
                raise ValueError("Unauthorized: Script does not belong to this user")

            # Update session status
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "generating_audio"
                session.audio_config = audio_config
                db.commit()

            # Build script object for audio pipeline
            script_data = {
                "hook": script.hook,
                "concept": script.concept,
                "process": script.process,
                "conclusion": script.conclusion
            }

            # Send WebSocket progress update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="audio_generation",
                progress=70,
                details="Generating audio narration with AI..."
            )

            logger.info(f"[{session_id}] Generating audio with voice {audio_config.get('voice', 'alloy')}")

            # Call Audio Pipeline Agent
            # Re-initialize audio pipeline with db and storage for music generation
            audio_pipeline_with_music = AudioPipelineAgent(
                api_key=settings.OPENAI_API_KEY,
                db=db,
                storage_service=self.storage_service
            )

            audio_input = AgentInput(
                session_id=session_id,
                data={
                    "script": script_data,
                    "voice": audio_config.get("voice") if audio_config else None,
                    "audio_option": audio_config.get("audio_option", "tts") if audio_config else "tts",
                    "user_id": user_id  # Add user_id for music processing
                }
            )

            audio_result = await audio_pipeline_with_music.process(audio_input)

            if not audio_result.success:
                raise ValueError(f"Audio generation failed: {audio_result.error}")

            # Track costs
            self._record_cost(
                db,
                session_id,
                agent="audio_pipeline",
                model="openai-tts-1",
                cost=audio_result.cost,
                duration=audio_result.duration
            )

            # Upload audio files to S3 and store in database
            audio_files = audio_result.data.get("audio_files", [])

            for audio_data in audio_files:
                # Generate unique asset ID
                asset_id = f"audio_{audio_data['part']}_{uuid.uuid4().hex[:8]}"

                # Skip S3 upload for music files (already in S3)
                if audio_data["part"] == "music":
                    # Music file already has S3 URL, no upload needed
                    logger.info(f"[{session_id}] Music file already in S3: {audio_data['url']}")
                else:
                    # Upload narration files to S3
                    try:
                        s3_result = await self.storage_service.upload_local_file(
                            file_path=audio_data["filepath"],
                            asset_type="audio",
                            session_id=session_id,
                            asset_id=asset_id,
                            user_id=user_id
                        )
                        # Update URL to S3 URL
                        audio_data["url"] = s3_result["url"]
                        logger.info(f"[{session_id}] {audio_data['part']} audio uploaded to S3")
                    except Exception as e:
                        # Keep local filepath if S3 upload fails
                        logger.warning(
                            f"[{session_id}] S3 upload failed for {audio_data['part']} audio, "
                            f"using local path: {e}"
                        )
                        audio_data["url"] = audio_data["filepath"]

                # Store in database
                asset = Asset(
                    session_id=session_id,
                    type="audio",
                    url=audio_data["url"],
                    approved=True,  # Auto-approve audio
                    asset_metadata={
                        "part": audio_data["part"],
                        "duration": audio_data["duration"],
                        "cost": audio_data["cost"],
                        "character_count": audio_data.get("character_count", 0),
                        "file_size": audio_data.get("file_size", 0),
                        "voice": audio_data.get("voice", "alloy"),
                        "asset_id": asset_id
                    }
                )
                db.add(asset)

            db.commit()

            # Update session status
            if session:
                session.status = "audio_complete"
                db.commit()

            # Final progress update
            total_cost = audio_result.cost
            total_duration = audio_result.data.get("total_duration", 0)

            await self.websocket_manager.broadcast_status(
                session_id,
                status="audio_complete",
                progress=85,
                details=f"Generated audio narration! Duration: {total_duration}s, Cost: ${total_cost:.3f}"
            )

            logger.info(
                f"[{session_id}] Audio generation complete: "
                f"{len(audio_files)} files, {total_duration}s, ${total_cost:.3f}"
            )

            return {
                "status": "success",
                "session_id": session_id,
                "audio_files": audio_files,
                "total_duration": total_duration,
                "total_cost": total_cost
            }

        except Exception as e:
            logger.error(f"[{session_id}] Audio generation failed: {e}")

            # Update session with error
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "failed"
                db.commit()

            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Audio generation failed: {str(e)}"
            )

            return {
                "status": "error",
                "session_id": session_id,
                "message": str(e)
            }

    async def finalize_script(
        self,
        db: Session,
        session_id: str,
        user_id: int,
        script_id: str,
        image_options: Optional[Dict[str, Any]] = None,
        audio_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Finalize script by generating both images and audio simultaneously.

        Args:
            db: Database session
            session_id: Session ID for tracking
            user_id: User ID making the request
            script_id: ID of the script in the database
            image_options: Image generation options (model, images_per_part)
            audio_config: Audio configuration (voice, audio_option)

        Returns:
            Dict containing status, micro_scenes, audio_files, and cost information
        """
        import asyncio

        try:
            logger.info(f"[{session_id}] Starting script finalization (parallel image + audio generation)")

            # Fetch script from database
            script = db.query(Script).filter(Script.id == script_id).first()
            if not script:
                raise ValueError(f"Script {script_id} not found")

            # Verify ownership
            if script.user_id != user_id:
                raise ValueError("Unauthorized: Script does not belong to this user")

            # Update session status
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session:
                # Create new session
                session = SessionModel(
                    id=session_id,
                    user_id=user_id,
                    status="finalizing",
                    prompt=f"Script-based generation: {script_id}",
                    options={"image_options": image_options, "audio_config": audio_config}
                )
                db.add(session)
            else:
                session.status = "finalizing"
                session.options = {"image_options": image_options, "audio_config": audio_config}

            db.commit()

            # Send WebSocket progress update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="finalizing",
                progress=50,
                details="Generating images and audio in parallel..."
            )

            # Run image and audio generation in parallel using asyncio.gather
            image_task = self.generate_images(
                db=db,
                session_id=session_id,
                user_id=user_id,
                script_id=script_id,
                options=image_options or {}
            )

            audio_task = self.generate_audio(
                db=db,
                session_id=session_id,
                user_id=user_id,
                script_id=script_id,
                audio_config=audio_config or {}
            )

            # Wait for both tasks to complete
            image_result, audio_result = await asyncio.gather(image_task, audio_task)

            # Check for errors
            if image_result.get("status") == "error":
                raise ValueError(f"Image generation failed: {image_result.get('message')}")

            if audio_result.get("status") == "error":
                raise ValueError(f"Audio generation failed: {audio_result.get('message')}")

            # Calculate total cost
            image_cost = float(image_result.get("micro_scenes", {}).get("cost", "0").replace("$", ""))
            audio_cost = audio_result.get("total_cost", 0.0)
            total_cost = image_cost + audio_cost

            # Update session status
            session.status = "finalized"
            db.commit()

            # Final progress update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="finalized",
                progress=100,
                details=f"Script finalized! Images + Audio complete. Total: ${total_cost:.3f}"
            )

            logger.info(
                f"[{session_id}] Script finalization complete: "
                f"Images: ${image_cost:.3f}, Audio: ${audio_cost:.3f}, Total: ${total_cost:.3f}"
            )

            return {
                "status": "success",
                "session_id": session_id,
                "micro_scenes": image_result.get("micro_scenes", {}),
                "audio_files": audio_result.get("audio_files", []),
                "total_duration": audio_result.get("total_duration", 0.0),
                "total_cost": total_cost
            }

        except Exception as e:
            logger.error(f"[{session_id}] Script finalization failed: {e}")

            # Update session with error
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "failed"
                db.commit()

            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Script finalization failed: {str(e)}"
            )

            return {
                "status": "error",
                "session_id": session_id,
                "message": str(e)
            }

    async def compose_educational_video(
        self,
        db: Session,
        session_id: str,
        user_id: int,
        desired_duration: float = 60.0
    ) -> Dict[str, Any]:
        """
        Compose final educational video from generated images and audio.

        Combines:
        - Images from each script part (hook, concept, process, conclusion)
        - TTS narration audio for each part
        - Background music (if available)

        Args:
            db: Database session
            session_id: Session ID containing generated assets
            user_id: User ID for ownership verification
            desired_duration: Desired total video duration in seconds (default: 60.0)

        Returns:
            Dict with status, video_url, duration, segments_count
        """
        try:
            logger.info(f"[{session_id}] ========================================")
            logger.info(f"[{session_id}] Starting educational video composition")
            logger.info(f"[{session_id}] ORCHESTRATOR VERSION: {ORCHESTRATOR_VERSION}")
            logger.info(f"[{session_id}] Desired duration: {desired_duration}s")
            logger.info(f"[{session_id}] ========================================")

            # Update session status
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "composing_video"
                db.commit()

            # Broadcast WebSocket update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="composing_video",
                progress=90,
                details="Composing final educational video with FFmpeg..."
            )

            # Get all assets for this session
            assets = db.query(Asset).filter(Asset.session_id == session_id).all()

            # Organize assets by type and part
            images_by_part = {}
            audio_by_part = {}
            music_url = None

            for asset in assets:
                asset_type = asset.type
                metadata = asset.asset_metadata or {}

                if asset_type == "image":
                    part = metadata.get("part", "")
                    # Check approved flag from database column, not metadata
                    if part and asset.approved:
                        if part not in images_by_part:
                            images_by_part[part] = []
                        images_by_part[part].append(asset.url)

                elif asset_type == "audio":
                    part = metadata.get("part", "")
                    if part and part != "music":
                        audio_by_part[part] = {
                            "url": asset.url,
                            "duration": metadata.get("duration", 5.0)
                        }
                    elif part == "music":
                        music_url = asset.url

            # Build timeline for video composition
            parts = ["hook", "concept", "process", "conclusion"]
            timeline_segments = []

            # First pass: Calculate total narration duration
            total_narration_duration = 0.0
            for part in parts:
                audio_data = audio_by_part.get(part)
                if audio_data:
                    total_narration_duration += audio_data["duration"]

            logger.info(f"[{session_id}] Total narration duration: {total_narration_duration}s, Desired duration: {desired_duration}s")

            # Calculate how much to extend each clip
            # Add intro/outro padding (2 seconds each)
            intro_padding = 2.0
            outro_padding = 2.0

            # Available time for segments after padding
            available_time = desired_duration - intro_padding - outro_padding

            # Calculate extension factor
            if total_narration_duration > 0:
                extension_factor = available_time / total_narration_duration
            else:
                extension_factor = 1.0

            # Don't shrink videos, only extend
            extension_factor = max(extension_factor, 1.0)

            logger.info(f"[{session_id}] Extension factor: {extension_factor:.2f}x")

            # Get the script to extract narration text for video prompts
            script = db.query(Script).filter(Script.id == session.prompt.split(": ")[-1]).first() if session and session.prompt else None

            for part in parts:
                # Get ALL approved images for this part (not just the first)
                images_for_part = images_by_part.get(part, []) if part in images_by_part else []

                # Get audio for this part
                audio_data = audio_by_part.get(part)

                # Get script text for this part to use in video prompts
                script_text = None
                if script:
                    part_data = getattr(script, part, None)
                    if part_data and isinstance(part_data, dict):
                        script_text = part_data.get("text", "")

                if images_for_part and audio_data:
                    # Extend the duration based on desired_duration
                    extended_duration = audio_data["duration"] * extension_factor

                    # Calculate the gap after narration (extended time - narration time)
                    gap_after_narration = extended_duration - audio_data["duration"]

                    timeline_segments.append({
                        "part": part,
                        "images": images_for_part,  # Store ALL images for this part
                        "audio_url": audio_data["url"],
                        "duration": extended_duration,
                        "narration_duration": audio_data["duration"],  # Keep original for audio sync
                        "gap_after_narration": gap_after_narration,  # Gap to add after this narration
                        "script_text": script_text  # Add script text for video prompts
                    })
                    logger.info(f"[{session_id}] {part}: {len(images_for_part)} images available for cycling")
                else:
                    logger.warning(f"[{session_id}] Missing assets for part: {part}")

            if not timeline_segments:
                raise Exception("No valid timeline segments found. Ensure images and audio are generated.")

            logger.info(f"[{session_id}] Built timeline with {len(timeline_segments)} segments")

            # Step 1: Generate video clips from images using image-to-video (IN PARALLEL!)
            # Smart multi-clip generation: Each 6s gen-4-turbo clip covers ~6 seconds
            # Calculate how many clips we need per section to reach desired duration

            CLIP_DURATION = 6.0  # gen-4-turbo generates 6-second clips
            MAX_RETRIES = 2  # Retry failed generations

            # Calculate total clips needed
            total_clips_needed = 0
            clips_per_segment = {}

            for segment in timeline_segments:
                # How many 6-second clips do we need for this segment's duration?
                clips_needed = max(1, int(segment["duration"] / CLIP_DURATION + 0.5))
                clips_per_segment[segment["part"]] = clips_needed
                total_clips_needed += clips_needed

            logger.info(f"[{session_id}] Generating {total_clips_needed} video clips ({clips_per_segment}) in parallel...")

            await self.websocket_manager.broadcast_status(
                session_id,
                status="generating_videos",
                progress=92,
                details=f"Generating {total_clips_needed} video clips in parallel with AI..."
            )

            # Create all video generation tasks with retry logic
            async def generate_clip_with_retry(segment, clip_index, total_clips_for_segment):
                """Generate a single video clip with retry logic."""
                part = segment['part']
                script_text = segment.get('script_text', '')
                images = segment.get('images', [])

                # Cycle through available images intelligently:
                # - If we have 2 images and 3 clips: distribute as [img0, img1, img1]
                # - If we have 2 images and 2 clips: distribute as [img0, img1]
                # - If we have 1 image and N clips: use [img0, img0, img0, ...]
                # Strategy: Map clip_index linearly across available images
                num_images = len(images)
                if num_images == 0:
                    logger.error(f"[{session_id}] No images available for {part}!")
                    return {"part": part, "success": False}

                # Calculate which image to use for this clip
                # For 2 images, 3 clips: [0, 1, 1] (early concept, late concept, late concept)
                # For 2 images, 2 clips: [0, 1] (early concept, late concept)
                if total_clips_for_segment == 1:
                    image_index = 0  # Use first image if only one clip
                else:
                    # Linear distribution: spread clips across available images
                    image_index = min(int(clip_index * num_images / total_clips_for_segment), num_images - 1)

                image_url = images[image_index]

                logger.info(f"[{session_id}] {part} clip {clip_index + 1}/{total_clips_for_segment}: using image {image_index + 1}/{num_images}")

                for attempt in range(MAX_RETRIES + 1):
                    try:
                        logger.info(f"[{session_id}] Generating clip {clip_index + 1}/{total_clips_for_segment} for {part} (attempt {attempt + 1}/{MAX_RETRIES + 1})")

                        # Use the actual script text as the prompt for contextual animation
                        # This makes the video animation match what's being narrated!
                        if script_text:
                            # For multiple clips, add variety to camera movements
                            camera_styles = [
                                "smooth camera movement",
                                "gentle pan and zoom",
                                "subtle camera motion"
                            ]
                            camera_style = camera_styles[clip_index % len(camera_styles)]
                            prompt = f"{script_text} - Educational video with {camera_style}"
                        else:
                            # Fallback if no script text available
                            prompt = f"Educational visualization for {part} with smooth camera movement"

                        video_input = AgentInput(
                            session_id=session_id,
                            data={
                                "approved_images": [{"url": image_url}],
                                "video_prompt": prompt,
                                "clip_duration": CLIP_DURATION,
                                "model": "gen-4-turbo",
                                "user_id": user_id  # Pass user_id for S3 upload in video_generator
                            }
                        )

                        video_result = await self.video_generator.process(video_input)

                        if video_result.success and video_result.data.get("clips"):
                            clip_data = video_result.data["clips"][0]
                            logger.info(f"[{session_id}] ✓ Successfully generated clip {clip_index + 1} for {part}")
                            return {
                                "part": part,
                                "video_url": clip_data["url"],
                                "image_url": image_url,
                                "duration": CLIP_DURATION,
                                "clip_data": clip_data,
                                "clip_index": clip_index,
                                "success": True
                            }
                        else:
                            error_msg = video_result.error or "Unknown error"
                            logger.warning(f"[{session_id}] Attempt {attempt + 1} failed for {part} clip {clip_index + 1}: {error_msg}")

                            if attempt < MAX_RETRIES:
                                await asyncio.sleep(2)  # Brief delay before retry
                                continue

                    except Exception as e:
                        logger.error(f"[{session_id}] Exception generating {part} clip {clip_index + 1} (attempt {attempt + 1}): {e}")
                        if attempt < MAX_RETRIES:
                            await asyncio.sleep(2)
                            continue

                # All retries failed
                logger.error(f"[{session_id}] ✗ Failed to generate clip {clip_index + 1} for {part} after {MAX_RETRIES + 1} attempts")
                return {
                    "part": part,
                    "video_url": None,
                    "image_url": image_url,
                    "duration": CLIP_DURATION,
                    "clip_index": clip_index,
                    "success": False
                }

            # Build task list: multiple clips per segment
            import asyncio
            tasks = []
            for segment in timeline_segments:
                clips_needed = clips_per_segment[segment["part"]]
                for clip_idx in range(clips_needed):
                    tasks.append(generate_clip_with_retry(segment, clip_idx, clips_needed))

            logger.info(f"[{session_id}] Running {len(tasks)} video generation tasks in parallel with retry...")
            video_clip_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results and organize by part
            clips_by_part = {}
            for part in parts:
                clips_by_part[part] = []

            successful_count = 0
            failed_count = 0

            for result in video_clip_results:
                if isinstance(result, Exception):
                    logger.error(f"[{session_id}] Clip failed with exception: {result}")
                    failed_count += 1
                    continue

                part = result["part"]

                if result["success"]:
                    # Store successful video clip in database
                    video_asset = Asset(
                        session_id=session_id,
                        type="video",
                        url=result["video_url"],
                        approved=True,
                        asset_metadata={
                            "part": part,
                            "duration": result["duration"],
                            "cost": result["clip_data"].get("cost", 0.0),
                            "source_image": result["image_url"],
                            "clip_index": result["clip_index"]
                        }
                    )
                    db.add(video_asset)
                    clips_by_part[part].append(result)
                    successful_count += 1
                else:
                    failed_count += 1

            db.commit()

            logger.info(f"[{session_id}] Generated {successful_count}/{len(video_clip_results)} video clips successfully ({failed_count} failed)")

            # Build final timeline with multiple clips per segment
            # IMPORTANT: Only the first clip of each part gets the audio_url
            # This prevents repeated narration when we have multiple clips per part
            video_clips = []
            for segment in timeline_segments:
                part = segment["part"]
                audio_url = segment["audio_url"]
                narration_duration = segment["narration_duration"]
                gap_after_narration = segment["gap_after_narration"]
                extended_duration = segment["duration"]  # The extended duration we calculated

                # Get all clips for this part
                part_clips = clips_by_part[part]

                if part_clips:
                    # Calculate duration per clip to distribute extended_duration proportionally
                    # This ensures the total timeline matches the extension_factor
                    num_clips = len(part_clips)
                    duration_per_clip = extended_duration / num_clips

                    logger.info(f"[{session_id}] {part}: Distributing {extended_duration:.2f}s across {num_clips} clips ({duration_per_clip:.2f}s each)")

                    # Use generated clips
                    for idx, clip in enumerate(part_clips):
                        # Only first clip gets audio, others get None
                        clip_audio_url = audio_url if idx == 0 else None
                        clip_narration_duration = narration_duration if idx == 0 else 0.0
                        clip_gap = gap_after_narration if idx == len(part_clips) - 1 else 0.0  # Gap only on last clip

                        video_clips.append({
                            "part": part,
                            "video_url": clip["video_url"],
                            "image_url": clip["image_url"],
                            "audio_url": clip_audio_url,
                            "duration": duration_per_clip,  # Use calculated duration, not actual clip duration
                            "narration_duration": clip_narration_duration,
                            "gap_after_narration": clip_gap
                        })
                else:
                    # Fallback to static image
                    logger.warning(f"[{session_id}] No video clips for {part}, using static image")
                    # Use the first image from the segment's images list
                    images = segment.get("images", [])
                    first_image_url = images[0] if images else None

                    if first_image_url:
                        video_clips.append({
                            "part": part,
                            "video_url": None,
                            "image_url": first_image_url,
                            "audio_url": audio_url,
                            "duration": segment["duration"],
                            "narration_duration": narration_duration,
                            "gap_after_narration": gap_after_narration
                        })
                    else:
                        logger.error(f"[{session_id}] No images available for {part} fallback!")

            # Step 2: Use FFmpeg compositor to stitch videos and add audio
            from app.services.educational_compositor import EducationalCompositor

            compositor = EducationalCompositor(work_dir="/tmp/educational_videos")

            composition_result = await compositor.compose_educational_video(
                timeline=video_clips,  # Now includes video URLs
                music_url=music_url,
                session_id=session_id,
                intro_padding=intro_padding,
                outro_padding=outro_padding
            )

            video_path = composition_result["output_path"]
            duration = composition_result["duration"]

            # Upload video to S3
            logger.info(f"[{session_id}] Uploading composed video to S3")

            upload_result = await self.storage_service.upload_local_file(
                file_path=video_path,
                asset_type="final",
                session_id=session_id,
                asset_id=f"final_video_{uuid.uuid4().hex[:8]}",
                user_id=user_id
            )

            video_url = upload_result["url"]

            # Store in database
            final_video_asset = Asset(
                session_id=session_id,
                type="final",
                url=video_url,
                approved=True,
                asset_metadata={
                    "duration": duration,
                    "segments_count": len(timeline_segments),
                    "has_music": music_url is not None
                }
            )
            db.add(final_video_asset)

            # Update session
            if session:
                session.status = "completed"
                session.final_video_url = video_url
                session.completed_at = datetime.now()
                db.commit()

            # Broadcast completion
            await self.websocket_manager.broadcast_status(
                session_id,
                status="completed",
                progress=100,
                details=f"Educational video complete! Duration: {duration}s"
            )

            logger.info(f"[{session_id}] Educational video composition complete: {video_url}")

            return {
                "status": "success",
                "session_id": session_id,
                "video_url": video_url,
                "duration": duration,
                "segments_count": len(timeline_segments)
            }

        except Exception as e:
            logger.error(f"[{session_id}] Educational video composition failed: {e}")

            # Update session status
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "failed"
                db.commit()

            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Video composition failed: {str(e)}"
            )

            return {
                "status": "error",
                "session_id": session_id,
                "message": str(e)
            }

    async def get_session_status(
        self,
        db: Session,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a generation session.

        Args:
            db: Database session
            session_id: Session ID to query

        Returns:
            Dict containing session status or None if not found
        """
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None

        return {
            "session_id": session.id,
            "status": session.status,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "final_video_url": session.final_video_url
        }

    async def process_story_segments(
        self,
        db: Session,
        session_id: str,
        user_id: int,
        s3_path: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process story segments from segments.md and generate images.

        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            s3_path: S3 path to segments.md (e.g., "users/user123/session456/images/segments.md")
            options: Processing options (num_images, max_passes, max_verification_passes, fast_mode)

        Returns:
            Dict with processing results
        """
        from app.agents.story_image_generator import StoryImageGeneratorAgent, parse_segments_md
        from app.services.secrets import get_secret
        from datetime import datetime
        import json
        
        # Validate S3 bucket
        if not s3_path.startswith("users/"):
            raise ValueError("S3 path must start with 'users/'")
        
        # Extract paths using StorageService helpers
        segments_s3_key = s3_path
        diagram_s3_key = self.storage_service.get_session_path(user_id, session_id, "images", "diagram.png")
        config_s3_key = self.storage_service.get_session_path(user_id, session_id, "images", "config.json")
        status_s3_key = self.storage_service.get_session_path(user_id, session_id, "images", "status.json")
        # Create timestamp file for reference
        timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        timestamp_s3_key = self.storage_service.get_session_path(user_id, session_id, "images", f"{timestamp_str}.json")
        output_s3_prefix = self.storage_service.get_session_prefix(user_id, session_id, "images")
        
        initial_status = None
        try:
            # Read segments.md from S3
            logger.info(f"[{session_id}] Reading segments.md from S3: {segments_s3_key}")
            segments_content = self.storage_service.read_file(segments_s3_key)
            segments_text = segments_content.decode("utf-8")
            
            # Parse segments.md
            template_title, segments = parse_segments_md(segments_text)
            if not template_title or not segments:
                raise ValueError("Failed to parse segments.md: invalid format or missing data")
            
            logger.info(f"[{session_id}] Parsed {len(segments)} segments for template: {template_title}")
            
            # Read config.json if exists
            config = {}
            if self.storage_service.file_exists(config_s3_key):
                try:
                    config_content = self.storage_service.read_file(config_s3_key)
                    config = json.loads(config_content.decode("utf-8"))
                    logger.info(f"[{session_id}] Loaded config.json from S3")
                except Exception as e:
                    logger.warning(f"[{session_id}] Failed to read config.json: {e}, using defaults")
            
            # Merge config with options (options take precedence)
            num_images = options.get("num_images", config.get("num_images", 2))
            # Validate and limit num_images to maximum of 3
            if num_images > 3:
                logger.warning(f"[{session_id}] num_images ({num_images}) exceeds maximum of 3, limiting to 3")
                num_images = 3
            if num_images < 1:
                raise ValueError("num_images must be at least 1")
            max_passes = options.get("max_passes", config.get("max_passes", 5))
            max_verification_passes = options.get("max_verification_passes", config.get("max_verification_passes", 3))
            fast_mode = options.get("fast_mode", config.get("fast_mode", False))
            
            # Check if diagram exists
            diagram_s3_path = None
            if self.storage_service.file_exists(diagram_s3_key):
                diagram_s3_path = diagram_s3_key
                logger.info(f"[{session_id}] Found diagram.png at: {diagram_s3_key}")
            else:
                logger.warning(f"[{session_id}] No diagram.png found, images will be generated without style reference")
            
            # Write initial status.json
            initial_status = {
                "status": "in_progress",
                "started_at": datetime.utcnow().isoformat() + "Z",
                "segments_total": len(segments),
                "segments_completed": 0,
                "segments_succeeded": 0,
                "segments_failed": 0
            }
            self.storage_service.upload_file_direct(
                json.dumps(initial_status, indent=2).encode("utf-8"),
                status_s3_key,
                content_type="application/json"
            )
            
            # Create empty timestamp file at the same level
            try:
                self.storage_service.upload_file_direct(
                    b"{}",
                    timestamp_s3_key,
                    content_type="application/json"
                )
                logger.info(f"[{session_id}] Created timestamp file: {timestamp_s3_key}")
            except Exception as ts_error:
                logger.warning(f"[{session_id}] Failed to create timestamp file: {ts_error}")
            
            # Send WebSocket update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="processing_story_segments",
                progress=0,
                details=f"Starting processing: {len(segments)} segments, {num_images} images per segment"
            )
            
            # Get API keys from Secrets Manager
            try:
                logger.info(f"[{session_id}] Retrieving API keys from Secrets Manager...")
                openrouter_key = get_secret("pipeline/openrouter-api-key")
                replicate_key = get_secret("pipeline/replicate-api-key")
                logger.info(f"[{session_id}] Successfully retrieved API keys")
            except Exception as e:
                error_msg = f"Failed to retrieve API keys: {e}"
                logger.error(f"[{session_id}] {error_msg}")
                # Update status.json immediately with the error
                error_status = {
                    "status": "failed",
                    "started_at": initial_status.get("started_at") if initial_status else datetime.utcnow().isoformat() + "Z",
                    "completed_at": datetime.utcnow().isoformat() + "Z",
                    "segments_total": len(segments) if segments else 0,
                    "segments_completed": 0,
                    "segments_succeeded": 0,
                    "segments_failed": 0,
                    "error": error_msg
                }
                try:
                    self.storage_service.upload_file_direct(
                        json.dumps(error_status, indent=2).encode("utf-8"),
                        status_s3_key,
                        content_type="application/json"
                    )
                    logger.info(f"[{session_id}] Updated status.json with API key retrieval error")
                except Exception as status_error:
                    logger.error(f"[{session_id}] Failed to update status.json: {status_error}")
                # Send error WebSocket update
                try:
                    await self.websocket_manager.broadcast_status(
                        session_id,
                        status="error",
                        progress=0,
                        details=error_msg
                    )
                except Exception as ws_error:
                    logger.error(f"[{session_id}] Failed to send WebSocket error update: {ws_error}")
                raise ValueError(error_msg)
            
            # Instantiate agent
            agent = StoryImageGeneratorAgent(
                storage_service=self.storage_service,
                openrouter_api_key=openrouter_key,
                replicate_api_key=replicate_key
            )
            
            # Prepare agent input
            agent_input = AgentInput(
                session_id=session_id,
                data={
                    "segments": segments,
                    "diagram_s3_path": diagram_s3_path,
                    "output_s3_prefix": output_s3_prefix,
                    "num_images": num_images,
                    "max_passes": max_passes,
                    "max_verification_passes": max_verification_passes,
                    "fast_mode": fast_mode,
                    "template_title": template_title
                },
                metadata={
                    "user_id": user_id,
                    "s3_path": s3_path
                }
            )
            
            # Process segments (agent handles parallel processing)
            logger.info(f"[{session_id}] Starting image generation for {len(segments)} segments")
            agent_output = await agent.process(agent_input)
            
            # Update status.json with final results
            final_status = {
                "status": "completed" if agent_output.success else "partial_failure",
                "started_at": initial_status["started_at"],
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "segments_total": len(segments),
                "segments_completed": len(segments),
                "segments_succeeded": agent_output.data.get("segments_succeeded", 0),
                "segments_failed": agent_output.data.get("segments_failed", 0),
                "total_images_generated": agent_output.data.get("total_images_generated", 0),
                "total_cost_usd": agent_output.cost,
                "total_time_seconds": agent_output.duration,
                "segment_results": agent_output.data.get("successful_segments", []),
                "errors": [
                    {
                        "segment_number": seg.get("segment_number"),
                        "segment_title": seg.get("segment_title"),
                        "error": seg.get("error")
                    }
                    for seg in agent_output.data.get("failed_segments", [])
                ]
            }
            
            self.storage_service.upload_file_direct(
                json.dumps(final_status, indent=2).encode("utf-8"),
                status_s3_key,
                content_type="application/json"
            )
            
            # Send final WebSocket update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="story_images_complete" if agent_output.success else "story_images_partial",
                progress=100,
                details=f"Completed: {agent_output.data.get('segments_succeeded', 0)}/{len(segments)} segments, "
                       f"{agent_output.data.get('total_images_generated', 0)} images, "
                       f"${agent_output.cost:.4f} cost"
            )
            
            # Send detailed WebSocket message
            await self.websocket_manager.send_progress(session_id, {
                "type": "story_image_complete",
                "status": "success" if agent_output.success else "partial",
                "results": {
                    "template_title": template_title,
                    "segments_total": len(segments),
                    "segments_succeeded": agent_output.data.get("segments_succeeded", 0),
                    "segments_failed": agent_output.data.get("segments_failed", 0),
                    "total_images_generated": agent_output.data.get("total_images_generated", 0),
                    "total_cost_usd": agent_output.cost,
                    "total_time_seconds": agent_output.duration,
                    "status_s3_key": status_s3_key
                }
            })
            
            return {
                "status": "success" if agent_output.success else "partial",
                "session_id": session_id,
                "template_title": template_title,
                "segments_total": len(segments),
                "segments_succeeded": agent_output.data.get("segments_succeeded", 0),
                "segments_failed": agent_output.data.get("segments_failed", 0),
                "total_images_generated": agent_output.data.get("total_images_generated", 0),
                "total_cost_usd": agent_output.cost,
                "total_time_seconds": agent_output.duration,
                "status_s3_key": status_s3_key
            }
        
        except Exception as e:
            logger.exception(f"[{session_id}] Error processing story segments: {e}")
            
            # Update status.json with error
            started_at = initial_status.get("started_at") if initial_status else datetime.utcnow().isoformat() + "Z"
            error_status = {
                "status": "failed",
                "started_at": started_at,
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }
            try:
                self.storage_service.upload_file_direct(
                    json.dumps(error_status, indent=2).encode("utf-8"),
                    status_s3_key,
                    content_type="application/json"
                )
            except:
                pass  # Ignore errors writing status
            
            # Send error WebSocket update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Processing failed: {str(e)}"
            )
            
            raise

    async def process_hardcode_story_with_audio(
        self,
        db: Session,
        session_id: str,
        user_id: int,
        hook_text: str,
        concept_text: str,
        process_text: str,
        conclusion_text: str,
        template_title: str,
        s3_path: str,
        image_options: Dict[str, Any],
        voice: str = "alloy",
        audio_option: str = "tts"
    ) -> Dict[str, Any]:
        """
        Process hardcode story segments: generate both images and audio in parallel.
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID
            hook_text: Text for hook segment
            concept_text: Text for concept segment
            process_text: Text for process segment
            conclusion_text: Text for conclusion segment
            template_title: Template title
            s3_path: S3 path to segments.md
            image_options: Options for image generation (num_images, max_passes, etc.)
            voice: Voice for TTS (default: "alloy")
            audio_option: Audio option (default: "tts")
        
        Returns:
            Dict with both image and audio generation results
        
        Raises:
            ValueError: If either image or audio generation fails
        """
        from app.agents.story_image_generator import StoryImageGeneratorAgent, parse_segments_md
        from app.agents.audio_pipeline import AudioPipelineAgent
        from app.services.secrets import get_secret
        from app.agents.base import AgentInput
        from datetime import datetime
        import json
        import asyncio
        
        logger.info(f"[{session_id}] Starting hardcode story processing with images and audio in parallel")

        # Track start time for status.json and elapsed calculations
        start_time_dt = datetime.utcnow()
        start_time = time.time()
        initial_status = None
        status_s3_key = self.storage_service.get_session_path(user_id, session_id, "images", "status.json")
        # Create timestamp file for reference
        timestamp_str = start_time_dt.strftime("%Y%m%d_%H%M%S")
        timestamp_s3_key = self.storage_service.get_session_path(user_id, session_id, "images", f"{timestamp_str}.json")

        # Write initial status.json
        try:
            initial_status = {
                "status": "in_progress",
                "started_at": start_time_dt.isoformat() + "Z",
                "segments_total": 4,  # Hardcode always has 4 segments
                "segments_completed": 0,
                "segments_succeeded": 0,
                "segments_failed": 0,
                "generating_images": True,
                "generating_audio": True
            }
            self.storage_service.upload_file_direct(
                json.dumps(initial_status, indent=2).encode("utf-8"),
                status_s3_key,
                content_type="application/json"
            )
            
            # Create empty timestamp file at the same level
            try:
                self.storage_service.upload_file_direct(
                    b"{}",
                    timestamp_s3_key,
                    content_type="application/json"
                )
                logger.info(f"[{session_id}] Created timestamp file: {timestamp_s3_key}")
            except Exception as ts_error:
                logger.warning(f"[{session_id}] Failed to create timestamp file: {ts_error}")
        except Exception as e:
            logger.warning(f"[{session_id}] Failed to write initial status.json: {e}")
        
        # Helper function to estimate duration from text (words/150 * 60 seconds)
        def estimate_duration(text: str) -> float:
            words = len(text.split())
            return round((words / 150) * 60, 1)
        
        # Build script object for audio pipeline
        script_data = {
            "hook": {
                "text": hook_text,
                "duration": str(estimate_duration(hook_text))
            },
            "concept": {
                "text": concept_text,
                "duration": str(estimate_duration(concept_text))
            },
            "process": {
                "text": process_text,
                "duration": str(estimate_duration(process_text))
            },
            "conclusion": {
                "text": conclusion_text,
                "duration": str(estimate_duration(conclusion_text))
            }
        }
        
        # Get API keys
        try:
            logger.info(f"[{session_id}] Retrieving API keys from Secrets Manager...")
            openrouter_key = get_secret("pipeline/openrouter-api-key")
            replicate_key = get_secret("pipeline/replicate-api-key")
            openai_key = settings.OPENAI_API_KEY
            if not openai_key:
                raise ValueError("OPENAI_API_KEY not configured in settings")
            logger.info(f"[{session_id}] Successfully retrieved API keys")
        except Exception as e:
            error_msg = f"Failed to retrieve API keys: {e}"
            logger.error(f"[{session_id}] {error_msg}")
            raise ValueError(error_msg)
        
        # Initialize agents
        image_agent = StoryImageGeneratorAgent(
            storage_service=self.storage_service,
            openrouter_api_key=openrouter_key,
            replicate_api_key=replicate_key,
            websocket_manager=self.websocket_manager
        )
        
        audio_agent = AudioPipelineAgent(
            api_key=openai_key,
            db=db,
            storage_service=self.storage_service,
            websocket_manager=self.websocket_manager
        )
        
        # Prepare image generation input (from segments.md)
        output_s3_prefix = self.storage_service.get_session_prefix(user_id, session_id, "images")
        
        # Read and parse segments.md
        segments_content = self.storage_service.read_file(s3_path)
        segments_text = segments_content.decode("utf-8")
        parsed_template_title, segments = parse_segments_md(segments_text)
        
        # Check if diagram exists
        diagram_s3_path = None
        diagram_s3_key = self.storage_service.get_session_path(user_id, session_id, "images", "diagram.png")
        if self.storage_service.file_exists(diagram_s3_key):
            diagram_s3_path = diagram_s3_key

        # Initialize cumulative status items for all images and audio BEFORE creating AgentInputs
        num_images_per_segment = image_options.get("num_images", 2)
        cumulative_items = []

        # Add image items for each segment
        for seg in segments:
            seg_num = seg.get("number")  # Fixed: use "number" not "segment_number"
            seg_title = seg.get("title", f"Segment {seg_num}")
            for img_num in range(1, num_images_per_segment + 1):
                cumulative_items.append({
                    "id": f"image_seg{seg_num}_img{img_num}",
                    "name": f"Image {img_num} - {seg_title}",
                    "status": "pending",
                    "type": "image"
                })

        # Add audio items for each part
        for part_name in ["hook", "concept", "process", "conclusion"]:
            cumulative_items.append({
                "id": f"audio_{part_name}",
                "name": f"Audio - {part_name.capitalize()}",
                "status": "pending",
                "type": "audio"
            })

        image_input = AgentInput(
            session_id=session_id,
            data={
                "segments": segments,
                "diagram_s3_path": diagram_s3_path,
                "output_s3_prefix": output_s3_prefix,
                "num_images": image_options.get("num_images", 2),
                "max_passes": image_options.get("max_passes", 5),
                "max_verification_passes": image_options.get("max_verification_passes", 3),
                "fast_mode": image_options.get("fast_mode", False),
                "template_title": template_title,
                "cumulative_items": cumulative_items  # Pass the cumulative status items
            },
            metadata={
                "user_id": user_id,
                "s3_path": s3_path
            }
        )

        # Prepare audio generation input
        audio_input = AgentInput(
            session_id=session_id,
            data={
                "script": script_data,
                "voice": voice,
                "audio_option": audio_option,
                "user_id": user_id,
                "cumulative_items": cumulative_items  # Pass the cumulative status items
            }
        )

        # Send initial WebSocket update with cumulative items
        await self.websocket_manager.broadcast_status(
            session_id,
            status="processing_hardcode_story",
            progress=0,
            details="Starting image and audio generation in parallel...",
            items=cumulative_items
        )
        
        # Get session folder for errors.json
        # session_folder should be "users/{user_id}/{session_id}"
        session_folder = f"users/{user_id}/{session_id}"
        
        # Run both in parallel
        logger.info(f"[{session_id}] Starting parallel image and audio generation")
        try:
            image_task = image_agent.process(image_input)
            audio_task = audio_agent.process(audio_input)
            
            # Wait for both to complete
            image_result, audio_result = await asyncio.gather(
                image_task,
                audio_task,
                return_exceptions=True
            )
            
            # Check for exceptions
            if isinstance(image_result, Exception):
                error_msg = f"Image generation raised exception: {str(image_result)}"
                logger.error(f"[{session_id}] {error_msg}")
                _write_errors_json(
                    self.storage_service,
                    session_folder,
                    {
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "error_type": "ImageGenerationException",
                        "error_message": str(image_result),
                        "traceback": None
                    }
                )
                raise ValueError(f"Image generation failed: {str(image_result)}")
            
            if isinstance(audio_result, Exception):
                error_msg = f"Audio generation raised exception: {str(audio_result)}"
                logger.error(f"[{session_id}] {error_msg}")
                _write_errors_json(
                    self.storage_service,
                    session_folder,
                    {
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "error_type": "AudioGenerationException",
                        "error_message": str(audio_result),
                        "traceback": None
                    }
                )
                raise ValueError(f"Audio generation failed: {str(audio_result)}")
            
            # Check for failures
            if not image_result.success:
                error_msg = image_result.error or "Image generation failed"
                logger.error(f"[{session_id}] Image generation failed: {error_msg}")
                _write_errors_json(
                    self.storage_service,
                    session_folder,
                    {
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "error_type": "ImageGenerationFailure",
                        "error_message": error_msg,
                        "agent_output": {
                            "success": False,
                            "error": image_result.error,
                            "cost": image_result.cost,
                            "duration": image_result.duration
                        }
                    }
                )
                raise ValueError(f"Image generation failed: {error_msg}")
            
            if not audio_result.success:
                error_msg = audio_result.error or "Audio generation failed"
                logger.error(f"[{session_id}] Audio generation failed: {error_msg}")
                _write_errors_json(
                    self.storage_service,
                    session_folder,
                    {
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "error_type": "AudioGenerationFailure",
                        "error_message": error_msg,
                        "agent_output": {
                            "success": False,
                            "error": audio_result.error,
                            "cost": audio_result.cost,
                            "duration": audio_result.duration
                        }
                    }
                )
                raise ValueError(f"Audio generation failed: {error_msg}")
            
            # Both succeeded - send progress update
            interim_elapsed = time.time() - start_time
            interim_cost = image_result.cost + audio_result.cost
            await self.websocket_manager.broadcast_status(
                session_id,
                status="images_and_audio_generated",
                progress=50,
                details=f"Generated {image_result.data.get('total_images_generated', 0)} images and {len(audio_result.data.get('audio_files', []))} audio files",
                elapsed_time=interim_elapsed,
                total_cost=interim_cost
            )

            # Wait for images folder before uploading audio
            logger.info(f"[{session_id}] Waiting for images folder to be created before uploading audio...")
            images_folder_exists = await _wait_for_images_folder(
                self.storage_service,
                output_s3_prefix,
                max_wait_seconds=30,
                check_interval=1.0
            )
            
            if not images_folder_exists:
                logger.warning(f"[{session_id}] Images folder not found after waiting, but proceeding with audio upload")
            
            # Upload audio files to S3
            audio_files = audio_result.data.get("audio_files", [])
            logger.info(f"[{session_id}] Audio agent returned {len(audio_files)} audio files")
            
            if not audio_files:
                logger.warning(f"[{session_id}] No audio files returned from audio agent!")
            
            uploaded_audio_files = []
            
            for audio_data in audio_files:
                logger.debug(f"[{session_id}] Processing audio file: {audio_data.get('part', 'unknown')}")
                # Skip music files (they're already in S3)
                if audio_data.get("part") == "music":
                    uploaded_audio_files.append(audio_data)
                    continue
                
                # Get part name first
                part_name = audio_data.get("part", "unknown")
                
                filepath = audio_data.get("filepath")
                if not filepath:
                    logger.error(f"[{session_id}] Audio file for {part_name} has no filepath, skipping upload")
                    continue
                
                if not os.path.exists(filepath):
                    logger.error(
                        f"[{session_id}] Audio file not found at path: {filepath}, skipping upload. "
                        f"File may have been cleaned up or path is incorrect."
                    )
                    # Try to list temp directory to debug
                    temp_dir = os.path.dirname(filepath) if filepath else "/tmp"
                    if os.path.exists(temp_dir):
                        try:
                            temp_files = os.listdir(temp_dir)
                            logger.debug(f"[{session_id}] Files in {temp_dir}: {temp_files[:10]}")
                        except:
                            pass
                    continue
                
                logger.info(f"[{session_id}] Found audio file for {part_name} at: {filepath}")

                # Upload to S3
                audio_s3_key = self.storage_service.get_session_path(user_id, session_id, "audio", f"{part_name}.mp3")
                
                try:
                    with open(filepath, "rb") as f:
                        audio_bytes = f.read()
                    
                    self.storage_service.upload_file_direct(
                        audio_bytes,
                        audio_s3_key,
                        content_type="audio/mpeg"
                    )
                    
                    # Generate presigned URL
                    presigned_url = self.storage_service.generate_presigned_url(
                        audio_s3_key,
                        expires_in=3600
                    )
                    
                    uploaded_audio_files.append({
                        **audio_data,
                        "s3_key": audio_s3_key,
                        "url": presigned_url
                    })
                    
                    logger.info(f"[{session_id}] Uploaded audio file {part_name} to {audio_s3_key}")
                    
                    # Clean up temporary file
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        logger.warning(f"[{session_id}] Failed to remove temp file {filepath}: {e}")
                        
                except Exception as e:
                    logger.error(f"[{session_id}] Failed to upload audio file {part_name}: {e}")
                    # Continue with other files
            
            # Update status.json with combined results
            combined_status = {
                "status": "completed",
                "started_at": initial_status.get("started_at") if initial_status else start_time.isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "segments_total": len(segments),
                "segments_completed": len(segments),
                "segments_succeeded": image_result.data.get("segments_succeeded", 0),
                "segments_failed": image_result.data.get("segments_failed", 0),
                "total_images_generated": image_result.data.get("total_images_generated", 0),
                "total_audio_files": len(uploaded_audio_files),
                "total_cost_usd": image_result.cost + audio_result.cost,
                "total_time_seconds": image_result.duration + audio_result.duration,
                "image_cost": image_result.cost,
                "audio_cost": audio_result.cost,
                "voice_used": voice,
                "audio_files": uploaded_audio_files
            }
            
            try:
                self.storage_service.upload_file_direct(
                    json.dumps(combined_status, indent=2).encode("utf-8"),
                    status_s3_key,
                    content_type="application/json"
                )
                logger.info(f"[{session_id}] Updated status.json with combined results")
            except Exception as e:
                logger.warning(f"[{session_id}] Failed to update status.json: {e}")
            
            # Both succeeded - stop here and return results
            # Video generation will be triggered separately by user
            elapsed_time = time.time() - start_time
            total_cost = image_result.cost + audio_result.cost

            logger.info(
                f"[{session_id}] Image and audio generation completed successfully. "
                f"Images: ${image_result.cost:.4f}, Audio: ${audio_result.cost:.4f}. "
                f"Total: ${total_cost:.4f}, Time: {elapsed_time:.1f}s"
            )

            # Prepare image URLs from successful segments
            image_urls = []
            for seg in image_result.data.get("successful_segments", []):
                for img in seg.get("generated_images", []):  # Fixed: use "generated_images" not "images"
                    # Generate presigned URL for the image
                    s3_key = img.get("s3_key")
                    if s3_key:
                        try:
                            presigned_url = self.storage_service.generate_presigned_url(
                                s3_key,
                                expires_in=3600  # 1 hour
                            )
                            image_urls.append({
                                "url": presigned_url,
                                "segment": seg.get("segment_number"),
                                "segment_title": seg.get("segment_title")
                            })
                        except Exception as e:
                            logger.warning(f"[{session_id}] Failed to generate presigned URL for {s3_key}: {e}")

            # Prepare audio URLs
            audio_urls = []
            for audio in uploaded_audio_files:
                if audio.get("part") != "music":  # Exclude background music
                    audio_urls.append({
                        "url": audio.get("url"),
                        "part": audio.get("part"),
                        "duration": audio.get("duration")
                    })

            # Send final success WebSocket update for images/audio with URLs
            await self.websocket_manager.broadcast_status(
                session_id,
                status="images_audio_complete",
                progress=100,
                details=f"Generated {image_result.data.get('total_images_generated', 0)} images and {len(uploaded_audio_files)} audio files",
                elapsed_time=elapsed_time,
                total_cost=total_cost,
                items=None  # Clear cumulative items on completion
            )

            # Send a separate message with the actual URLs for display
            await self.websocket_manager.send_progress(
                session_id,
                {
                    "type": "assets_ready",
                    "images": image_urls,
                    "audio": audio_urls
                }
            )

            return {
                "status": "success",
                "session_id": session_id,
                "template_title": template_title,
                "elapsed_time": elapsed_time,
                "total_cost": total_cost,
                "image_result": {
                    "segments_succeeded": image_result.data.get("segments_succeeded", 0),
                    "segments_failed": image_result.data.get("segments_failed", 0),
                    "total_images_generated": image_result.data.get("total_images_generated", 0),
                    "cost": image_result.cost,
                    "duration": image_result.duration,
                    "successful_segments": image_result.data.get("successful_segments", [])
                },
                "audio_result": {
                    "audio_files": uploaded_audio_files,
                    "total_duration": audio_result.data.get("total_duration", 0.0),
                    "cost": audio_result.cost,
                    "duration": audio_result.duration,
                    "voice_used": voice
                }
            }
            
        except ValueError as ve:
            # Write error to errors.json
            session_folder = f"users/{user_id}/{session_id}"
            _write_errors_json(
                self.storage_service,
                session_folder,
                {
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "error_type": "ValueError",
                    "error_message": str(ve),
                    "context": "Image or audio generation failed",
                    "traceback": None
                }
            )
            
            # Update status.json with error
            error_status = {
                "status": "failed",
                "started_at": initial_status.get("started_at") if initial_status else start_time.isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "error": str(ve)
            }
            try:
                self.storage_service.upload_file_direct(
                    json.dumps(error_status, indent=2).encode("utf-8"),
                    status_s3_key,
                    content_type="application/json"
                )
            except:
                pass
            
            # Send error WebSocket update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Processing failed: {str(ve)}"
            )
            
            # Re-raise ValueError (these are our intentional failures)
            raise
        except Exception as e:
            logger.exception(f"[{session_id}] Unexpected error in parallel processing: {e}")
            
            # Write error to errors.json
            session_folder = f"users/{user_id}/{session_id}"
            _write_errors_json(
                self.storage_service,
                session_folder,
                {
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "context": "Unexpected error during hardcode story processing",
                    "traceback": traceback.format_exc()
                }
            )
            
            # Update status.json with error
            error_status = {
                "status": "failed",
                "started_at": initial_status.get("started_at") if initial_status else start_time.isoformat() + "Z",
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "error": str(e)
            }
            try:
                self.storage_service.upload_file_direct(
                    json.dumps(error_status, indent=2).encode("utf-8"),
                    status_s3_key,
                    content_type="application/json"
                )
            except:
                pass
            
            # Send error WebSocket update
            await self.websocket_manager.broadcast_status(
                session_id,
                status="error",
                progress=0,
                details=f"Processing failed: {str(e)}"
            )
            
            raise ValueError(f"Processing failed: {str(e)}")

    async def compose_hardcode_video(
        self,
        session_id: str,
        user_id: int,
        image_result: Any,
        audio_files: List[Dict[str, Any]],
        diagram_s3_key: str,
        segments: List[Dict[str, Any]],
        output_s3_prefix: str,
        template_title: str
    ) -> Dict[str, Any]:
        """
        Compose video from hardcode story images and audio.
        
        Uses diagram as primary image for each segment, with generated images
        as mood/inspiration. Generates one video clip per segment, then composes
        final video with audio.
        
        Args:
            session_id: Session ID
            user_id: User ID
            image_result: AgentOutput from story image generator
            audio_result: AgentOutput from audio pipeline
            diagram_s3_key: S3 key to diagram.png
            segments: List of parsed segments
            output_s3_prefix: S3 prefix for output
            template_title: Template title
        
        Returns:
            Dict with video result including final_video_s3_key, total_cost, etc.
        """
        from app.agents.base import AgentInput
        from app.services.educational_compositor import EducationalCompositor
        import asyncio
        
        logger.info(f"[{session_id}] Starting hardcode video composition")
        
        # Map segment numbers to parts
        segment_to_part = {
            1: "hook",
            2: "concept",
            3: "process",
            4: "conclusion"
        }
        
        # Organize data by part
        successful_segments = image_result.data.get("successful_segments", [])
        if not successful_segments:
            raise ValueError("No successful image segments found. Cannot generate video without images.")
        
        if not segments:
            raise ValueError("No segments provided. Cannot generate video without segment data.")
        
        audio_files_by_part = {}
        for audio_file in audio_files:
            part = audio_file.get("part")
            if part and part != "music":
                audio_files_by_part[part] = audio_file
        
        # Check if diagram exists (optional - will fallback to generated images)
        diagram_url = None
        if self.storage_service.file_exists(diagram_s3_key):
            diagram_url = self.storage_service.generate_presigned_url(
                diagram_s3_key,
                expires_in=3600
            )
            logger.info(f"[{session_id}] Using diagram for video generation")
        else:
            logger.info(f"[{session_id}] No diagram found - will use generated images for video")
        
        # Generate video clips for each segment - PARALLEL PROCESSING
        video_clips = []
        total_video_cost = 0.0
        total_segments_for_video = len(successful_segments)

        if not self.video_generator:
            raise ValueError("Video generator not initialized - check REPLICATE_API_KEY")

        # Constants for video generation
        CLIP_DURATION = 6.0  # gen-4-turbo generates 6-second clips

        # Define async function for generating multiple related video clips for a segment
        async def generate_segment_video_clips(segment_result, segment_index):
            """Generate multiple related video clips for a segment to fill the audio duration."""
            import time
            import math

            segment_num = segment_result.get("segment_number")
            part = segment_to_part.get(segment_num)

            if not part:
                logger.warning(f"[{session_id}] Unknown segment number {segment_num}, skipping")
                return None

            # Get audio for this part
            audio_file = audio_files_by_part.get(part)
            if not audio_file:
                logger.warning(f"[{session_id}] No audio file for {part}, skipping video generation")
                return None

            # Validate audio file has URL
            audio_url = audio_file.get("url") or audio_file.get("presigned_url")
            if not audio_url:
                logger.warning(f"[{session_id}] Audio file for {part} has no URL, skipping video generation")
                return None

            # Get duration (ensure it's a float)
            audio_duration = float(audio_file.get("duration", 10.0))

            # Calculate how many 6-second clips we need
            clips_needed = max(1, math.ceil(audio_duration / CLIP_DURATION))

            logger.error(f"[{session_id}] [MULTI-CLIP DEBUG] {part}: audio_duration={audio_duration:.1f}s, CLIP_DURATION={CLIP_DURATION}s, clips_needed={clips_needed}")

            # Get generated images
            generated_images = segment_result.get("generated_images", [])

            # Get segment data for narration text
            segment_data = next((s for s in segments if s.get("number") == segment_num), None)
            narration_text = segment_data.get("narrationtext", "") if segment_data else ""

            # Determine base image to use
            if diagram_url:
                base_image_url = diagram_url
                image_source = "diagram"
            else:
                if not generated_images:
                    logger.warning(f"[{session_id}] No diagram or generated images for {part}, skipping video generation")
                    return None
                img_key = generated_images[0].get("s3_key")
                if not img_key:
                    logger.warning(f"[{session_id}] No valid image key for {part}, skipping video generation")
                    return None
                base_image_url = self.storage_service.generate_presigned_url(img_key, expires_in=3600)
                image_source = "generated image"

            logger.info(f"[{session_id}] Generating {clips_needed} video clips for {part} (segment {segment_num}, {audio_duration:.1f}s audio) using {image_source}")

            # Send WebSocket update before generating
            start_time = time.time()
            await self.websocket_manager.broadcast_status(
                session_id,
                status="generating_video_clip",
                progress=85 + (segment_index * 3),
                details=f"[{segment_index + 1}/{total_segments_for_video}] Generating {clips_needed} clips for {part.capitalize()}... (estimated {clips_needed * 60}-{clips_needed * 120}s)"
            )

            # Generate related prompts for sequential clips
            # Split narration into chunks for each clip to create a narrative flow
            words = narration_text.split()
            words_per_clip = max(1, len(words) // clips_needed) if words else 0

            clip_prompts = []
            for i in range(clips_needed):
                # Get portion of narration for this clip
                start_word = i * words_per_clip
                end_word = start_word + words_per_clip if i < clips_needed - 1 else len(words)
                clip_narration = " ".join(words[start_word:end_word]) if words else ""

                # Create progressive camera movements for visual continuity
                camera_movements = [
                    "slow zoom in, focusing on key details",
                    "gentle pan across the content, revealing information",
                    "smooth tracking shot following the visual flow",
                    "gradual zoom out to show context and connections"
                ]
                camera_move = camera_movements[i % len(camera_movements)]

                # Build the prompt with continuity cues
                if i == 0:
                    prompt = f"Opening shot: {clip_narration}. {camera_move}. Educational style with clear visuals."
                elif i == clips_needed - 1:
                    prompt = f"Concluding shot: {clip_narration}. {camera_move}. Smooth transition to end."
                else:
                    prompt = f"Continuation: {clip_narration}. {camera_move}. Maintain visual flow from previous shot."

                clip_prompts.append(prompt)

            # Generate all clips for this segment
            generated_clips = []
            total_clip_cost = 0.0

            for clip_idx in range(clips_needed):
                try:
                    video_input = AgentInput(
                        session_id=session_id,
                        data={
                            "approved_images": [{"url": base_image_url}],
                            "video_prompt": clip_prompts[clip_idx],
                            "clip_duration": CLIP_DURATION,
                            "model": "gen-4-turbo",
                            "user_id": user_id
                        }
                    )

                    clip_result = await self.video_generator.process(video_input)

                    if clip_result.success and clip_result.data.get("clips"):
                        clip_data = clip_result.data["clips"][0]
                        generated_clips.append({
                            "url": clip_data["url"],
                            "duration": CLIP_DURATION,
                            "cost": clip_result.cost
                        })
                        total_clip_cost += clip_result.cost
                        logger.info(f"[{session_id}] Generated clip {clip_idx + 1}/{clips_needed} for {part}")
                    else:
                        error_msg = clip_result.error or "Unknown error"
                        logger.warning(f"[{session_id}] Clip {clip_idx + 1}/{clips_needed} failed for {part}: {error_msg}")

                except Exception as e:
                    error_details = str(e) if str(e) else f"{type(e).__name__} occurred"
                    logger.error(f"[{session_id}] Exception generating clip {clip_idx + 1}/{clips_needed} for {part}: {error_details}")

            generation_time = time.time() - start_time

            if generated_clips:
                # Return info with multiple video URLs
                clip_info = {
                    "part": part,
                    "video_urls": [c["url"] for c in generated_clips],  # Multiple URLs
                    "video_url": generated_clips[0]["url"],  # Keep single URL for compatibility
                    "audio_url": audio_url,
                    "duration": audio_duration,
                    "actual_video_duration": len(generated_clips) * CLIP_DURATION,
                    "narration_duration": audio_duration,
                    "gap_after_narration": 0.0,
                    "script_text": narration_text,
                    "cost": total_clip_cost,
                    "clips_count": len(generated_clips)
                }

                logger.error(f"[{session_id}] [MULTI-CLIP DEBUG] {part}: Successfully generated {len(generated_clips)} clips, video_urls has {len(clip_info['video_urls'])} URLs")

                # Send success notification
                await self.websocket_manager.broadcast_status(
                    session_id,
                    status="video_clip_completed",
                    progress=85 + ((segment_index + 1) * 3),
                    details=f"✓ [{segment_index + 1}/{total_segments_for_video}] {len(generated_clips)} clips for {part.capitalize()} generated in {generation_time:.1f}s"
                )

                logger.info(f"[{session_id}] ✓ Generated {len(generated_clips)} clips for {part} in {generation_time:.1f}s (${total_clip_cost:.3f})")
                return clip_info
            else:
                # All clips failed - use fallback
                logger.error(f"[{session_id}] All clips failed for {part}, using fallback")

                # Send WebSocket notification about video generation failure
                await self.websocket_manager.broadcast_status(
                    session_id,
                    status="warning",
                    progress=85 + ((segment_index + 1) * 3),
                    details=f"⚠ [{segment_index + 1}/{total_segments_for_video}] Video generation failed for {part}, using static image fallback"
                )

                # Fallback: use static image (diagram or first generated image)
                fallback_image_key = diagram_s3_key if diagram_url else (generated_images[0].get("s3_key") if generated_images else None)
                if fallback_image_key:
                    image_url = self.storage_service.generate_presigned_url(
                        fallback_image_key,
                        expires_in=3600
                    )
                    return {
                        "part": part,
                        "video_url": None,  # Will be created from static image
                        "image_url": image_url,
                        "audio_url": audio_url,
                        "duration": audio_duration,
                        "narration_duration": audio_duration,
                        "gap_after_narration": 0.0,
                        "script_text": narration_text,
                        "cost": 0.0
                    }
                else:
                    logger.error(f"[{session_id}] No fallback image available for {part}")
                    await self.websocket_manager.broadcast_status(
                        session_id,
                        status="error",
                        progress=85 + ((segment_index + 1) * 3),
                        details=f"❌ [{segment_index + 1}/{total_segments_for_video}] Video generation failed for {part} and no fallback image available"
                    )
                    return None

        # Send initial notification about parallel video generation
        await self.websocket_manager.broadcast_status(
            session_id,
            status="generating_videos_parallel",
            progress=85,
            details=f"Generating {total_segments_for_video} video clips in parallel... (estimated {total_segments_for_video * 30}-{total_segments_for_video * 40}s total)"
        )

        # Generate all video clips in parallel using asyncio.gather
        logger.info(f"[{session_id}] Starting parallel video generation for {total_segments_for_video} segments")
        tasks = []
        for i, segment_result in enumerate(successful_segments):
            task = generate_segment_video_clips(segment_result, i)
            tasks.append(task)

        # Execute all video generation tasks in parallel
        video_clip_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and collect successful clips
        for i, result in enumerate(video_clip_results):
            if isinstance(result, Exception):
                error_msg = str(result) if str(result) else f"{type(result).__name__} occurred"
                logger.error(f"[{session_id}] Video clip task {i+1} raised exception: {error_msg}")
                continue

            if result is not None:
                video_clips.append(result)
                total_video_cost += result.get("cost", 0.0)
        
        if not video_clips:
            raise ValueError("No video clips generated")
        
        # Compose final video using EducationalCompositor
        logger.info(f"[{session_id}] Composing final video from {len(video_clips)} clips")
        
        await self.websocket_manager.broadcast_status(
            session_id,
            status="composing_final_video",
            progress=95,
            details="Composing final video with FFmpeg..."
        )
        
        if not self.ffmpeg_compositor:
            raise ValueError("FFmpeg compositor not available")
        
        # Use EducationalCompositor for final composition
        compositor = EducationalCompositor(work_dir="/tmp/educational_videos")
        
        # Get music URL if available
        music_url = None
        for audio_file in audio_files:
            if audio_file.get("part") == "music":
                music_url = audio_file.get("url")
                break
        
        final_video_result = await compositor.compose_educational_video(
            timeline=video_clips,
            music_url=music_url,
            session_id=session_id,
            intro_padding=2.0,
            outro_padding=2.0
        )
        
        # Upload final video to S3
        final_video_s3_key = self.storage_service.get_session_path(user_id, session_id, "final", "final_video.mp4")
        
        # Download final video from compositor result
        final_video_path = final_video_result.get("output_path")
        if final_video_path and os.path.exists(final_video_path):
            with open(final_video_path, "rb") as f:
                video_bytes = f.read()
            
            self.storage_service.upload_file_direct(
                video_bytes,
                final_video_s3_key,
                content_type="video/mp4"
            )
            
            # Generate presigned URL
            final_video_url = self.storage_service.generate_presigned_url(
                final_video_s3_key,
                expires_in=86400  # 24 hours
            )
            
            # Clean up local file
            try:
                os.remove(final_video_path)
            except:
                pass
            
            logger.info(f"[{session_id}] Final video uploaded to {final_video_s3_key}")
        else:
            raise ValueError("Final video file not found after composition")
        
        return {
            "status": "success",
            "final_video_s3_key": final_video_s3_key,
            "final_video_url": final_video_url,
            "video_clips_count": len(video_clips),
            "total_cost": total_video_cost,
            "duration": final_video_result.get("duration", 0.0)
        }

    async def start_full_test_process(
        self,
        userId: str,
        sessionId: str,
        db: Session
    ) -> None:
        """
        Start the Full Test pipeline process.
        
        Coordinates Agent2 and Agent4 in parallel, then Agent5 sequentially.
        Creates S3 folder structure, sends orchestrator status updates, and forwards
        standardized agent status messages to WebSocket.
        
        Args:
            userId: User identifier
            sessionId: Session identifier
            db: Database session for querying video_session table
        """
        from app.agents.agent_2 import agent_2_process
        from app.agents.agent_4 import agent_4_process
        from app.agents.agent_5 import agent_5_process
        from sqlalchemy import text
        
        try:
            # Send orchestrator starting status
            await self._send_orchestrator_status(
                userId, sessionId, "starting",
                {"message": "Orchestrator starting Full Test process"}
            )
            
            # Create S3 folder structure: scaffold_test/{userId}/{sessionId}/
            s3_folder_prefix = f"scaffold_test/{userId}/{sessionId}/"
            
            # Create timestamp.json with Unix timestamp
            timestamp = int(time.time())
            timestamp_json = str(timestamp)
            timestamp_s3_key = f"{s3_folder_prefix}timestamp.json"
            
            try:
                self.storage_service.upload_file_direct(
                    timestamp_json.encode('utf-8'),
                    timestamp_s3_key,
                    content_type='application/json'
                )
                logger.info(f"Created timestamp.json at {timestamp_s3_key} with timestamp {timestamp}")
            except Exception as e:
                logger.warning(f"Failed to create timestamp.json: {e}")
                # Continue anyway - timestamp.json is not critical
            
            # Create status callback function for agents
            async def status_callback(
                agentnumber: str,
                status: str,
                userID: str,
                sessionID: str,
                timestamp: int,
                **kwargs
            ) -> None:
                """
                Status callback function that standardizes and forwards agent status messages.
                
                Args:
                    agentnumber: Agent identifier ("Agent2", "Agent4", "Agent5")
                    status: Status value ("starting", "processing", "finished", "error")
                    userID: User identifier
                    sessionID: Session identifier
                    timestamp: Unix timestamp in milliseconds
                    **kwargs: Additional fields (error, reason, videoUrl, progress, etc.)
                """
                # Build standardized status message
                status_data = {
                    "agentnumber": agentnumber,
                    "userID": userID,
                    "sessionID": sessionID,
                    "status": status,
                    "timestamp": timestamp
                }
                
                # Add optional fields from kwargs
                if "error" in kwargs:
                    status_data["error"] = kwargs["error"]
                if "reason" in kwargs:
                    status_data["reason"] = kwargs["reason"]
                if "videoUrl" in kwargs:
                    status_data["videoUrl"] = kwargs["videoUrl"]
                if "progress" in kwargs:
                    status_data["progress"] = kwargs["progress"]
                if "fileCount" in kwargs:
                    status_data["fileCount"] = kwargs["fileCount"]
                if "cost" in kwargs:
                    status_data["cost"] = kwargs["cost"]
                
                # Add any other UI information from kwargs
                for key, value in kwargs.items():
                    if key not in ["error", "reason", "videoUrl", "progress", "fileCount", "cost"]:
                        status_data[key] = value
                
                # Forward to WebSocket (with reconnection handling)
                try:
                    await self.websocket_manager.send_progress(sessionID, status_data)
                except Exception as ws_error:
                    logger.warning(f"Failed to send status via WebSocket (will retry): {ws_error}")
                    # Continue processing - WebSocket reconnection will be handled
            
            # Send orchestrator processing status
            await self._send_orchestrator_status(
                userId, sessionId, "processing",
                {"message": "Orchestrator triggering Agent2 and Agent4 in parallel"}
            )
            
            # Query video_session table to verify it exists
            try:
                result = db.execute(
                    text(
                        "SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"
                    ),
                    {"session_id": sessionId, "user_id": userId},
                ).fetchone()
                
                if not result:
                    raise ValueError(f"Video session not found for session_id={sessionId} and user_id={userId}")
                
                # Convert result to dict if needed
                if hasattr(result, "_mapping"):
                    video_session_data = dict(result._mapping)
                else:
                    video_session_data = {
                        "id": getattr(result, "id", None),
                        "user_id": getattr(result, "user_id", None),
                        "topic": getattr(result, "topic", None),
                        "confirmed_facts": getattr(result, "confirmed_facts", None),
                        "generated_script": getattr(result, "generated_script", None),
                    }
            except Exception as e:
                logger.error(f"Error querying video_session: {e}")
                await self._send_orchestrator_status(
                    userId, sessionId, "error",
                    {"error": str(e), "reason": f"Database query failed: {type(e).__name__}"}
                )
                raise
            
            # Trigger Agent2 and Agent4 in parallel
            agent2_task = agent_2_process(
                websocket_manager=None,  # Not used - using callback instead
                user_id=userId,
                session_id=sessionId,
                template_id="",  # Not used in Full Test
                chosen_diagram_id="",  # Not used in Full Test
                script_id="",  # Not used in Full Test
                storage_service=self.storage_service,
                video_session_data=video_session_data,
                db=db,
                status_callback=status_callback
            )
            
            # Agent4 will extract script from video_session if needed
            # Generate supersessionid for Agent4
            agent4_supersessionid = f"{sessionId}_{secrets.token_urlsafe(12)[:16]}"
            
            agent4_task = agent_4_process(
                websocket_manager=None,  # Not used - using callback instead
                user_id=userId,
                session_id=sessionId,
                supersessionid=agent4_supersessionid,
                script={},  # Will be extracted from video_session by Agent4
                voice="alloy",
                audio_option="tts",
                storage_service=self.storage_service,
                agent2_data=None,
                db=db,
                status_callback=status_callback
            )
            
            # Run both agents in parallel
            try:
                agent2_result, agent4_result = await asyncio.gather(agent2_task, agent4_task)
                logger.info(f"Agent2 and Agent4 completed successfully for session {sessionId}")
            except Exception as e:
                logger.error(f"Agent2 or Agent4 failed: {e}")
                await self._send_orchestrator_status(
                    userId, sessionId, "error",
                    {"error": str(e), "reason": f"Agent execution failed: {type(e).__name__}"}
                )
                raise
            
            # After Agent2+Agent4 complete successfully, trigger Agent5 synchronously
            await self._send_orchestrator_status(
                userId, sessionId, "processing",
                {"message": "Agent2 and Agent4 completed, starting Agent5"}
            )
            
            try:
                # Agent5 will scan S3 folders to discover content
                # Generate supersessionid for Agent5
                agent5_supersessionid = f"{sessionId}_{secrets.token_urlsafe(12)[:16]}"
                
                agent5_result = await agent_5_process(
                    websocket_manager=None,  # Not used - using callback instead
                    user_id=userId,
                    session_id=sessionId,
                    supersessionid=agent5_supersessionid,
                    storage_service=self.storage_service,
                    pipeline_data=None,  # Agent5 will scan S3 instead
                    generation_mode="video",
                    db=db,
                    status_callback=status_callback
                )
                
                # Extract video URL from Agent5 result
                video_url = agent5_result if isinstance(agent5_result, str) else None
                
                # Send orchestrator finished status with video link and all info
                await self._send_orchestrator_status(
                    userId, sessionId, "finished",
                    {
                        "message": "Full Test process completed successfully",
                        "videoUrl": video_url,
                        "agent2Result": agent2_result,
                        "agent4Result": agent4_result,
                        "agent5Result": agent5_result
                    }
                )
                
                logger.info(f"Full Test process completed successfully for session {sessionId}")
                
            except Exception as e:
                logger.error(f"Agent5 failed: {e}")
                await self._send_orchestrator_status(
                    userId, sessionId, "error",
                    {"error": str(e), "reason": f"Agent5 failed: {type(e).__name__}"}
                )
                raise
                
        except Exception as e:
            logger.exception(f"Orchestrator error in start_full_test_process: {e}")
            # Try to send error status (may fail if WebSocket is down)
            try:
                await self._send_orchestrator_status(
                    userId, sessionId, "error",
                    {"error": str(e), "reason": f"Orchestrator failed: {type(e).__name__}"}
                )
            except:
                pass
            raise
    
    async def _send_orchestrator_status(
        self,
        userId: str,
        sessionId: str,
        status: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Helper method to send orchestrator status updates in standardized format.
        
        Args:
            userId: User identifier
            sessionId: Session identifier
            status: Status value ("starting", "processing", "finished", "error")
            extra_data: Additional data to include in status message
        """
        status_data = {
            "agentnumber": "Orchestrator",
            "userID": userId,
            "sessionID": sessionId,
            "status": status,
            "timestamp": int(time.time() * 1000)
        }
        
        if extra_data:
            status_data.update(extra_data)
        
        try:
            await self.websocket_manager.send_progress(sessionId, status_data)
        except Exception as e:
            logger.warning(f"Failed to send orchestrator status via WebSocket: {e}")
            # Continue processing - WebSocket reconnection will be handled