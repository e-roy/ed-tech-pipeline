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

    async def generate_images(
        self,
        db: Session,
        session_id: str,
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
            images = image_result.data["images"]
            for img_data in images:
                asset = Asset(
                    # id is auto-increment, don't specify
                    session_id=session_id,
                    type="image",  # 'type' column not 'asset_type'
                    url=img_data["url"],  # 'url' column not 'storage_url'
                    approved=False,  # 'approved' not 'user_selected'
                    asset_metadata={  # 'asset_metadata' not 'metadata'
                        "view_type": img_data["view_type"],
                        "seed": img_data["seed"],
                        "model": img_data["model"],
                        "cost": img_data["cost"],
                        "duration": img_data["duration"]
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
        video_prompt: str,
        clip_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate video clips using Luma via Replicate (STUB).

        This method currently returns a stub response to unblock the team.
        Person C will integrate the actual Video Generator Agent here.

        Args:
            db: Database session
            session_id: Session ID for tracking
            video_prompt: Prompt for video generation
            clip_config: Configuration for clip generation

        Returns:
            Dict containing status and stub clip URLs
        """
        # Update session status
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            session.status = "generating_clips"
            session.video_prompt = video_prompt
            session.clip_config = clip_config
            db.commit()

        # Send WebSocket progress update
        await self.websocket_manager.broadcast_status(
            session_id,
            status="generating_clips",
            progress=60,
            details="Starting video clip generation..."
        )

        # STUB: Return mock response
        # TODO (Person C): Replace with actual Video Generator Agent integration
        num_clips = clip_config.get("num_clips", 3) if clip_config else 3
        stub_clips = [
            {
                "url": f"https://stub-clip-{i}.mp4",
                "duration": 5.0,
                "approved": False
            }
            for i in range(num_clips)
        ]

        # Update progress
        await self.websocket_manager.broadcast_status(
            session_id,
            status="clips_generated",
            progress=80,
            details=f"Generated {len(stub_clips)} clips (stub)"
        )

        return {
            "status": "success",
            "session_id": session_id,
            "clips": stub_clips,
            "message": "STUB: Clips would be generated by Luma via Replicate"
        }

    async def compose_final_video(
        self,
        db: Session,
        session_id: str,
        text_config: Optional[Dict[str, Any]] = None,
        audio_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compose final video with text overlays and audio (STUB).

        This method currently returns a stub response to unblock the team.
        Person C will integrate the actual Composition Agent (FFmpeg) here.

        Args:
            db: Database session
            session_id: Session ID for tracking
            text_config: Text overlay configuration
            audio_config: Audio configuration

        Returns:
            Dict containing status and stub final video URL
        """
        # Update session status
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session:
            session.status = "composing"
            session.text_config = text_config
            session.audio_config = audio_config
            db.commit()

        # Send WebSocket progress update
        await self.websocket_manager.broadcast_status(
            session_id,
            status="composing",
            progress=90,
            details="Composing final video..."
        )

        # STUB: Return mock response
        # TODO (Person C): Replace with actual FFmpeg composition
        stub_final_url = f"https://stub-final-video-{session_id}.mp4"

        # Update session with final result
        if session:
            session.status = "completed"
            session.final_video_url = stub_final_url
            session.completed_at = datetime.utcnow()
            db.commit()

        # Update progress
        await self.websocket_manager.broadcast_status(
            session_id,
            status="completed",
            progress=100,
            details="Video composition complete (stub)"
        )

        return {
            "status": "success",
            "session_id": session_id,
            "video_url": stub_final_url,
            "message": "STUB: Final video would be composed with FFmpeg"
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
