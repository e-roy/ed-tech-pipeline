"""
Video Generation Orchestrator - Coordinates all microservices.

This is the CRITICAL PATH component that unblocks the entire team.
Updated by Person B to integrate Prompt Parser and Batch Image Generator agents.
"""
from sqlalchemy.orm import Session
from app.models.database import Session as SessionModel, Asset, GenerationCost
from app.services.websocket_manager import WebSocketManager
from app.agents.base import AgentInput
from app.agents.prompt_parser import PromptParserAgent
from app.agents.batch_image_generator import BatchImageGeneratorAgent
from app.agents.video_generator import VideoGeneratorAgent
from app.agents.narrative_builder import NarrativeBuilderAgent
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

        # Initialize AI agents (Person B integration)
        replicate_api_key = settings.REPLICATE_API_KEY
        if not replicate_api_key:
            logger.warning(
                "REPLICATE_API_KEY not set - agents will fail at runtime. "
                "Add it to .env file."
            )

        self.prompt_parser = PromptParserAgent(replicate_api_key) if replicate_api_key else None
        self.image_generator = BatchImageGeneratorAgent(replicate_api_key) if replicate_api_key else None
        self.narrative_builder = NarrativeBuilderAgent(replicate_api_key) if replicate_api_key else None

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
        user_prompt: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate images using Flux via Replicate.

        Integrated by Person B with Prompt Parser and Batch Image Generator agents.

        Args:
            db: Database session
            session_id: Session ID for tracking
            user_prompt: User's prompt for image generation
            options: Additional options (num_images, model, style_keywords, etc.)

        Returns:
            Dict containing status, generated images, and cost information
        """
        try:
            # Validate agents are initialized
            if not self.prompt_parser or not self.image_generator:
                raise ValueError("AI agents not initialized - check REPLICATE_API_KEY")

            # Create or update session in database
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if session:
                session.status = "generating_images"
                session.prompt = user_prompt
                session.options = options
                db.commit()

            # Stage 1: Prompt Parsing
            await self.websocket_manager.broadcast_status(
                session_id,
                status="prompt_parsing",
                progress=10,
                details="Analyzing your prompt with AI..."
            )

            logger.info(f"[{session_id}] Starting prompt parsing")

            prompt_parser_input = AgentInput(
                session_id=session_id,
                data={
                    "user_prompt": user_prompt,
                    "options": options or {}
                }
            )

            prompt_result = await self.prompt_parser.process(prompt_parser_input)

            if not prompt_result.success:
                raise ValueError(f"Prompt parsing failed: {prompt_result.error}")

            # Track cost in database
            self._record_cost(
                db,
                session_id,
                agent="prompt_parser",
                model="meta-llama-3-70b",
                cost=prompt_result.cost,
                duration=prompt_result.duration
            )

            # Stage 2: Image Generation
            num_images = len(prompt_result.data["image_prompts"])
            await self.websocket_manager.broadcast_status(
                session_id,
                status="image_generation",
                progress=30,
                details=f"Generating {num_images} images with AI..."
            )

            logger.info(
                f"[{session_id}] Generating {num_images} images with "
                f"{options.get('model', 'flux-schnell') if options else 'flux-schnell'}"
            )

            image_gen_input = AgentInput(
                session_id=session_id,
                data={
                    "image_prompts": prompt_result.data["image_prompts"],
                    "model": options.get("model", "flux-schnell") if options else "flux-schnell"
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

            # Store generated images in database
            # First upload to S3 for permanent storage
            images = image_result.data["images"]
            for i, img_data in enumerate(images):
                # Generate unique asset ID
                asset_id = f"img_{uuid.uuid4().hex[:12]}"

                # Download from Replicate and upload to S3
                try:
                    s3_result = await self.storage_service.download_and_upload(
                        replicate_url=img_data["url"],
                        asset_type="image",
                        session_id=session_id,
                        asset_id=asset_id,
                        user_id=user_id
                    )
                    # Use S3 URL instead of temporary Replicate URL
                    storage_url = s3_result["url"]
                    logger.info(f"[{session_id}] Image {i+1} uploaded to S3: {storage_url}")
                except Exception as e:
                    # Fall back to Replicate URL if S3 upload fails
                    logger.warning(f"[{session_id}] S3 upload failed for image {i+1}, using Replicate URL: {e}")
                    storage_url = img_data["url"]

                asset = Asset(
                    # id is auto-increment, don't specify
                    session_id=session_id,
                    type="image",  # 'type' column not 'asset_type'
                    url=storage_url,  # S3 URL or fallback Replicate URL
                    approved=False,  # 'approved' not 'user_selected'
                    asset_metadata={  # 'asset_metadata' not 'metadata'
                        "view_type": img_data["view_type"],
                        "seed": img_data["seed"],
                        "model": img_data["model"],
                        "cost": img_data["cost"],
                        "duration": img_data["duration"],
                        "asset_id": asset_id
                    }
                )
                db.add(asset)

            db.commit()

            # Update session status
            if session:
                session.status = "reviewing_images"
                db.commit()

            # Final progress update
            total_cost = prompt_result.cost + image_result.cost
            await self.websocket_manager.broadcast_status(
                session_id,
                status="images_ready",
                progress=100,
                details=f"Generated {len(images)} images! Cost: ${total_cost:.3f}"
            )

            logger.info(
                f"[{session_id}] Image generation complete: "
                f"{len(images)} images, ${total_cost:.3f}"
            )

            return {
                "status": "success",
                "session_id": session_id,
                "images": images,
                "total_cost": total_cost,
                "product_category": prompt_result.data["product_category"],
                "style_keywords": prompt_result.data["style_keywords"]
            }

        except Exception as e:
            logger.error(f"[{session_id}] Image generation failed: {e}")

            # Update session with error (query again since it might not be in scope)
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
