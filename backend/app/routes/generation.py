"""
Generation routes - handles all video generation workflow steps.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid

from app.database import get_db
from app.models.database import Session as SessionModel, Asset, User
from app.routes.auth import get_current_user
from app.services.orchestrator import VideoGenerationOrchestrator
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService

router = APIRouter()

# Global WebSocket manager instance (shared with main.py)
websocket_manager = WebSocketManager()

# Global orchestrator instance
orchestrator = VideoGenerationOrchestrator(websocket_manager)

# Global storage service instance
storage_service = StorageService()


# Request/Response models
class GenerateImagesRequest(BaseModel):
    prompt: str
    num_images: Optional[int] = 4
    aspect_ratio: Optional[str] = "16:9"


class ImageResponse(BaseModel):
    url: str
    approved: bool


class GenerateImagesResponse(BaseModel):
    session_id: str
    status: str
    images: List[Dict[str, Any]]


class SaveApprovedImagesRequest(BaseModel):
    session_id: str
    approved_image_urls: List[str]


class GenerateClipsRequest(BaseModel):
    session_id: str
    video_prompt: str
    num_clips: Optional[int] = 3
    duration: Optional[float] = 5.0


class GenerateClipsResponse(BaseModel):
    session_id: str
    status: str
    clips: List[Dict[str, Any]]


class SaveApprovedClipsRequest(BaseModel):
    session_id: str
    approved_clip_urls: List[str]


class ComposeFinalVideoRequest(BaseModel):
    session_id: str
    text_overlays: Optional[List[Dict[str, Any]]] = None
    audio_url: Optional[str] = None


class ComposeFinalVideoResponse(BaseModel):
    session_id: str
    status: str
    video_url: str


class BuildNarrativeRequest(BaseModel):
    topic: str
    learning_objective: str
    key_points: List[str]


class BuildNarrativeResponse(BaseModel):
    session_id: str
    status: str
    script: Dict[str, Any]
    cost: float
    duration: float


@router.post("/generate-images", response_model=GenerateImagesResponse)
async def generate_images(
    request: GenerateImagesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 1: Generate images using Flux-Schnell via Replicate.

    **Authentication:** Requires X-User-Email header from authenticated frontend.

    Creates a new session and generates images based on user prompt using the Flux-Schnell model.
    Images are stored in S3 and tracked in the database.

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `prompt` (string): Text description of images to generate

    **Optional Parameters:**
    - `num_images` (int): Number of images to generate (default: 4)
    - `aspect_ratio` (string): Image aspect ratio (default: "16:9")

    **Returns:**
    - `session_id`: Unique identifier for this generation session
    - `status`: Generation status
    - `images`: List of generated image URLs
    """
    # Create new session
    session_id = str(uuid.uuid4())
    session = SessionModel(
        id=session_id,
        user_id=current_user.id,
        status="pending",
        prompt=request.prompt
    )
    db.add(session)
    db.commit()

    # Store prompt/config in S3 input folder
    try:
        config_data = {
            "prompt": request.prompt,
            "num_images": request.num_images,
            "aspect_ratio": request.aspect_ratio,
            "session_id": session_id,
            "created_at": session.created_at.isoformat() if session.created_at else None
        }
        storage_service.upload_prompt_config(
            user_id=current_user.id,
            config_data=config_data,
            session_id=session_id
        )
    except Exception as e:
        # Log but don't fail if storage fails
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to store prompt config: {e}")

    # Call orchestrator to generate images
    result = await orchestrator.generate_images(
        db=db,
        session_id=session_id,
        user_id=current_user.id,
        user_prompt=request.prompt,
        options={
            "num_images": request.num_images,
            "aspect_ratio": request.aspect_ratio
        }
    )

    # Check if result is an error
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Image generation failed")
        )

    return {
        "session_id": session_id,
        "status": result["status"],
        "images": result.get("images", [])
    }


@router.post("/save-approved-images")
async def save_approved_images(
    request: SaveApprovedImagesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 2: Save user-approved images to database.

    **Authentication Required:** Include Bearer token in Authorization header.

    User selects which generated images to use for video generation.

    **Required Parameters:**
    - `session_id` (string): Session ID from generate-images
    - `approved_image_urls` (list): URLs of approved images
    """
    # Verify session exists and belongs to user
    session = db.query(SessionModel).filter(
        SessionModel.id == request.session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save approved images as assets
    for url in request.approved_image_urls:
        asset = Asset(
            session_id=session.id,
            type="image",
            url=url,
            approved=True
        )
        db.add(asset)

    # Update session status
    session.status = "images_approved"
    db.commit()

    return {
        "status": "success",
        "session_id": session.id,
        "approved_count": len(request.approved_image_urls)
    }


@router.post("/generate-clips", response_model=GenerateClipsResponse)
async def generate_clips(
    request: GenerateClipsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 3: Generate video clips using Gen-4-Turbo via Replicate.

    **Authentication Required:** Include Bearer token in Authorization header.

    Takes approved images and generates video clips using the Gen-4-Turbo model.
    Clips are stored in S3 and tracked in the database.

    **Required Parameters:**
    - `session_id` (string): Session ID with approved images
    - `video_prompt` (string): Description for video generation

    **Optional Parameters:**
    - `num_clips` (int): Number of clips to generate (default: 3)
    - `duration` (float): Duration per clip in seconds (default: 5.0)
    """
    # Verify session
    session = db.query(SessionModel).filter(
        SessionModel.id == request.session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Call orchestrator to generate clips
    result = await orchestrator.generate_clips(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id,
        video_prompt=request.video_prompt,
        clip_config={
            "num_clips": request.num_clips,
            "duration": request.duration
        }
    )

    return {
        "session_id": request.session_id,
        "status": result["status"],
        "clips": result["clips"]
    }


@router.post("/save-approved-clips")
async def save_approved_clips(
    request: SaveApprovedClipsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 4: Save user-approved video clips to database.

    User selects which generated clips to use in final video.
    """
    # Verify session
    session = db.query(SessionModel).filter(
        SessionModel.id == request.session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save approved clips as assets
    for idx, url in enumerate(request.approved_clip_urls):
        asset = Asset(
            session_id=session.id,
            type="clip",
            url=url,
            approved=True,
            order_index=idx
        )
        db.add(asset)

    # Update session status
    session.status = "clips_approved"
    db.commit()

    return {
        "status": "success",
        "session_id": session.id,
        "approved_count": len(request.approved_clip_urls)
    }


@router.post("/compose-final-video", response_model=ComposeFinalVideoResponse)
async def compose_final_video(
    request: ComposeFinalVideoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 5: Compose final video with text overlays and audio.

    **Authentication Required:** Include Bearer token in Authorization header.

    Combines approved clips with optional text overlays and audio using FFmpeg.
    Final video is stored in S3 and tracked in the database.

    **Required Parameters:**
    - `session_id` (string): Session ID with approved clips

    **Optional Parameters:**
    - `text_overlays` (list): Text overlay configurations
    - `audio_url` (string): URL of audio to add
    """
    # Verify session
    session = db.query(SessionModel).filter(
        SessionModel.id == request.session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Call orchestrator to compose final video
    result = await orchestrator.compose_final_video(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id,
        text_config={"overlays": request.text_overlays} if request.text_overlays else None,
        audio_config={"url": request.audio_url} if request.audio_url else None
    )

    return {
        "session_id": request.session_id,
        "status": result["status"],
        "video_url": result["video_url"]
    }


@router.post("/build-narrative", response_model=BuildNarrativeResponse)
async def build_narrative(
    request: BuildNarrativeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Build a narrative script for a 60-second video using AI.

    **Authentication:** Requires X-User-Email header from authenticated frontend.

    Creates a structured 4-part script (hook, concept, process, conclusion) with:
    - Narration text for each part
    - Clip duration suggestions
    - Visual guidance for each scene
    - Key concepts to highlight

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `topic` (string): Main topic/subject of the video
    - `learning_objective` (string): What the viewer should learn/understand
    - `key_points` (list): Array of key points to cover in the video

    **Returns:**
    - `session_id`: Unique identifier for this narrative session
    - `status`: Generation status ("success" or "error")
    - `script`: The complete 4-part script structure
    - `cost`: Cost of the LLM call in USD
    - `duration`: Time taken to generate the narrative in seconds

    **Example Request:**
    ```json
    {
      "topic": "How Photosynthesis Works",
      "learning_objective": "Understand the basic process of how plants convert sunlight into energy",
      "key_points": [
        "Plants absorb sunlight through chlorophyll",
        "Carbon dioxide and water are converted into glucose",
        "Oxygen is released as a byproduct"
      ]
    }
    ```

    **Example Response:**
    ```json
    {
      "session_id": "abc123...",
      "status": "success",
      "script": {
        "hook": {
          "narration": "Ever wonder how plants turn sunlight into food?",
          "duration": 12,
          "visual_guidance": "Close-up of sunlight hitting green leaves",
          "key_concepts": ["photosynthesis", "sunlight"]
        },
        ...
      },
      "cost": 0.001,
      "duration": 2.5
    }
    ```
    """
    # Validate inputs
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")

    if not request.learning_objective or not request.learning_objective.strip():
        raise HTTPException(status_code=400, detail="Learning objective is required")

    if not request.key_points or len(request.key_points) == 0:
        raise HTTPException(status_code=400, detail="At least one key point is required")

    # Call orchestrator to build narrative
    result = await orchestrator.build_narrative(
        db=db,
        user_id=current_user.id,
        topic=request.topic,
        learning_objective=request.learning_objective,
        key_points=request.key_points
    )

    # Check if result is an error
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Narrative building failed")
        )

    return {
        "session_id": result["session_id"],
        "status": result["status"],
        "script": result["script"],
        "cost": result["cost"],
        "duration": result["duration"]
    }


# Export websocket_manager so it can be used in main.py
def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return websocket_manager
