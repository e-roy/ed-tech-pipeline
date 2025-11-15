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

router = APIRouter()

# Global WebSocket manager instance (shared with main.py)
websocket_manager = WebSocketManager()

# Global orchestrator instance
orchestrator = VideoGenerationOrchestrator(websocket_manager)


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


@router.post("/generate-images", response_model=GenerateImagesResponse)
async def generate_images(
    request: GenerateImagesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 1: Generate images using Flux via Replicate.

    Creates a new session and generates images based on user prompt.
    Currently returns stub responses to unblock team.
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

    # Call orchestrator to generate images
    result = await orchestrator.generate_images(
        db=db,
        session_id=session_id,
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

    User selects which generated images to use for video generation.
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
    Step 3: Generate video clips using Luma via Replicate.

    Takes approved images and generates video clips.
    Currently returns stub responses to unblock team.
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

    Combines approved clips with text and audio to create final video.
    Currently returns stub responses to unblock team.
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
        text_config={"overlays": request.text_overlays} if request.text_overlays else None,
        audio_config={"url": request.audio_url} if request.audio_url else None
    )

    return {
        "session_id": request.session_id,
        "status": result["status"],
        "video_url": result["video_url"]
    }


# Export websocket_manager so it can be used in main.py
def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return websocket_manager
