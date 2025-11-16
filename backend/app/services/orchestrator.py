"""
Video Generation Orchestrator - Coordinates all microservices.

This is the CRITICAL PATH component that unblocks the entire team.
Updated to integrate script-based image generation workflow.
"""
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
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


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

        # Initialize Person C agents (Video Pipeline)
        # VideoGeneratorAgent uses Veo 3.1 via Replicate
        self.video_generator = VideoGeneratorAgent(replicate_api_key) if replicate_api_key else None
        self.ffmpeg_compositor = FFmpegCompositor()

        # Initialize storage service for S3 uploads
        self.storage_service = StorageService()

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
            images_per_part = options.get("images_per_part", 2) if options else 2
            await self.websocket_manager.broadcast_status(
                session_id,
                status="image_generation",
                progress=20,
                details=f"Generating {images_per_part} images per script part with AI..."
            )

            logger.info(
                f"[{session_id}] Generating {images_per_part} images per part with "
                f"{options.get('model', 'flux-schnell') if options else 'flux-schnell'}"
            )

            image_gen_input = AgentInput(
                session_id=session_id,
                data={
                    "script": script_data,
                    "model": options.get("model", "flux-schnell") if options else "flux-schnell",
                    "images_per_part": images_per_part
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
            # Default to Veo 3.1 via Replicate
            default_model = "veo-3.1"

            video_gen_input = AgentInput(
                session_id=session_id,
                data={
                    "approved_images": image_data_list,
                    "video_prompt": video_prompt,
                    "clip_duration": clip_config.get("clip_duration", 8.0) if clip_config else 8.0,  # Veo 3.1 default is 8s
                    "model": clip_config.get("model", default_model) if clip_config else default_model
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
            # First upload to S3 for permanent storage
            clips = video_result.data["clips"]
            for i, clip_data in enumerate(clips):
                # Generate unique asset ID
                asset_id = f"clip_{uuid.uuid4().hex[:12]}"

                # Download from Replicate and upload to S3
                try:
                    s3_result = await self.storage_service.download_and_upload(
                        replicate_url=clip_data["url"],
                        asset_type="video",
                        session_id=session_id,
                        asset_id=asset_id,
                        user_id=user_id
                    )
                    # Use S3 URL instead of temporary Replicate URL
                    storage_url = s3_result["url"]
                    logger.info(f"[{session_id}] Clip {i+1} uploaded to S3: {storage_url}")
                except Exception as e:
                    # Fall back to Replicate URL if S3 upload fails
                    logger.warning(f"[{session_id}] S3 upload failed for clip {i+1}, using Replicate URL: {e}")
                    storage_url = clip_data["url"]

                asset = Asset(
                    session_id=session_id,
                    type="video",
                    url=storage_url,  # S3 URL or fallback Replicate URL
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
                        "asset_id": asset_id
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
        user_id: int
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

        Returns:
            Dict with status, video_url, duration, segments_count
        """
        try:
            logger.info(f"[{session_id}] Starting educational video composition")

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

            for part in parts:
                # Get first approved image for this part (or first available)
                image_url = images_by_part.get(part, [None])[0] if part in images_by_part else None

                # Get audio for this part
                audio_data = audio_by_part.get(part)

                if image_url and audio_data:
                    timeline_segments.append({
                        "part": part,
                        "image_url": image_url,
                        "audio_url": audio_data["url"],
                        "duration": audio_data["duration"]
                    })
                else:
                    logger.warning(f"[{session_id}] Missing assets for part: {part}")

            if not timeline_segments:
                raise Exception("No valid timeline segments found. Ensure images and audio are generated.")

            logger.info(f"[{session_id}] Built timeline with {len(timeline_segments)} segments")

            # Step 1: Generate video clips from images using image-to-video
            logger.info(f"[{session_id}] Generating video clips from images...")

            await self.websocket_manager.broadcast_status(
                session_id,
                status="generating_videos",
                progress=92,
                details="Generating video clips from images with AI..."
            )

            video_clips = []
            for i, segment in enumerate(timeline_segments):
                logger.info(f"[{session_id}] Generating video for {segment['part']} ({i+1}/{len(timeline_segments)})")

                # Generate video clip from image
                video_input = AgentInput(
                    session_id=session_id,
                    data={
                        "approved_images": [{"url": segment["image_url"]}],
                        "video_prompt": f"Educational visualization for {segment['part']}",
                        "clip_duration": segment["duration"],
                        "model": "gen-4-turbo"  # Cheapest option
                    }
                )

                video_result = await self.video_generator.process(video_input)

                if not video_result.success or not video_result.data.get("clips"):
                    logger.warning(f"[{session_id}] Video generation failed for {segment['part']}, using static image")
                    video_clips.append({
                        "part": segment["part"],
                        "video_url": None,  # Will use static image fallback
                        "image_url": segment["image_url"],
                        "audio_url": segment["audio_url"],
                        "duration": segment["duration"]
                    })
                else:
                    clip_data = video_result.data["clips"][0]

                    # Store video clip in database
                    video_asset = Asset(
                        session_id=session_id,
                        type="video",
                        url=clip_data["url"],
                        approved=True,
                        asset_metadata={
                            "part": segment["part"],
                            "duration": segment["duration"],
                            "cost": clip_data.get("cost", 0.0),
                            "source_image": segment["image_url"]
                        }
                    )
                    db.add(video_asset)

                    video_clips.append({
                        "part": segment["part"],
                        "video_url": clip_data["url"],
                        "image_url": segment["image_url"],
                        "audio_url": segment["audio_url"],
                        "duration": segment["duration"]
                    })

            db.commit()
            logger.info(f"[{session_id}] Generated {len(video_clips)} video clips")

            # Step 2: Use FFmpeg compositor to stitch videos and add audio
            from app.services.educational_compositor import EducationalCompositor

            compositor = EducationalCompositor(work_dir="/tmp/educational_videos")

            composition_result = await compositor.compose_educational_video(
                timeline=video_clips,  # Now includes video URLs
                music_url=music_url,
                session_id=session_id
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
