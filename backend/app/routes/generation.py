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
    session_id: str
    script_id: str
    model: Optional[str] = "flux-schnell"
    images_per_part: Optional[int] = 2


class ImageResponse(BaseModel):
    url: str
    approved: bool


class MicroSceneResponse(BaseModel):
    hook: Dict[str, Any]
    concept: Dict[str, Any]
    process: Dict[str, Any]
    conclusion: Dict[str, Any]
    cost: str


class GenerateImagesResponse(BaseModel):
    session_id: str
    status: str
    micro_scenes: MicroSceneResponse


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
    Step 1: Generate images from a video script.

    **Authentication:** Requires X-User-Email header from authenticated frontend.

    Takes a script ID from the database and generates 2-3 images per script part
    (hook, concept, process, conclusion) based on visual guidance.
    Images are stored in S3 and tracked in the database.

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `session_id` (string): Session ID for tracking this generation
    - `script_id` (string): ID of the script in the database

    **Optional Parameters:**
    - `model` (string): Model to use ("flux-pro", "flux-dev", "flux-schnell", "sdxl") (default: "flux-schnell")
    - `images_per_part` (int): Number of images per script part (default: 2)

    **Returns:**
    - `session_id`: Session ID for tracking
    - `status`: Generation status
    - `micro_scenes`: Object with hook, concept, process, conclusion images and cost
    """
    # Call orchestrator to generate images from script
    result = await orchestrator.generate_images(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id,
        script_id=request.script_id,
        options={
            "model": request.model,
            "images_per_part": request.images_per_part
        }
    )

    # Check if result is an error
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Image generation failed")
        )

    return {
        "session_id": request.session_id,
        "status": result["status"],
        "micro_scenes": result["micro_scenes"]
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


class GenerateAudioRequest(BaseModel):
    session_id: str
    script_id: str
    voice: Optional[str] = "alloy"  # Default: alloy (OpenAI voices: alloy, echo, fable, onyx, nova, shimmer)
    audio_option: Optional[str] = "tts"  # tts, upload, none, instrumental


class GenerateAudioResponse(BaseModel):
    session_id: str
    status: str
    audio_files: List[Dict[str, Any]]
    total_duration: float
    total_cost: float


class FinalizeScriptRequest(BaseModel):
    session_id: str
    script_id: str
    # Image generation options
    model: Optional[str] = "flux-schnell"
    images_per_part: Optional[int] = 2
    # Audio generation options
    voice: Optional[str] = "alloy"
    audio_option: Optional[str] = "tts"


class FinalizeScriptResponse(BaseModel):
    session_id: str
    status: str
    micro_scenes: MicroSceneResponse
    audio_files: List[Dict[str, Any]]
    total_duration: float
    total_cost: float


class ComposeVideoRequest(BaseModel):
    session_id: str


class ComposeVideoResponse(BaseModel):
    session_id: str
    status: str
    video_url: str
    duration: float
    segments_count: int


@router.post("/generate-audio", response_model=GenerateAudioResponse)
async def generate_audio(
    request: GenerateAudioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate audio narration from script using OpenAI TTS.

    **Authentication Required:** Include X-User-Email header.

    Takes a script ID and generates TTS audio for each part (hook, concept, process, conclusion).
    Audio files are stored in S3 and tracked in the database.

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `session_id` (string): Session ID for tracking
    - `script_id` (string): ID of the script in the database

    **Optional Parameters:**
    - `voice` (string): OpenAI voice - "alloy", "echo", "fable", "onyx", "nova", "shimmer" (default: "alloy")
    - `audio_option` (string): Audio option - "tts", "upload", "none", "instrumental" (default: "tts")

    **Returns:**
    - `session_id`: Session ID for tracking
    - `status`: Generation status
    - `audio_files`: List of generated audio files with URLs and metadata
    - `total_duration`: Total audio duration in seconds
    - `total_cost`: Total generation cost in USD
    """
    # Call orchestrator to generate audio from script
    result = await orchestrator.generate_audio(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id,
        script_id=request.script_id,
        audio_config={
            "voice": request.voice,
            "audio_option": request.audio_option
        }
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return {
        "session_id": request.session_id,
        "status": result["status"],
        "audio_files": result.get("audio_files", []),
        "total_duration": result.get("total_duration", 0.0),
        "total_cost": result.get("total_cost", 0.0)
    }


@router.post("/finalize-script", response_model=FinalizeScriptResponse)
async def finalize_script(
    request: FinalizeScriptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalize script by generating both images and audio simultaneously.

    **Authentication Required:** Include X-User-Email header.

    Takes a script ID and generates:
    - Images for each part (hook, concept, process, conclusion) using template + DALL-E
    - Audio narration for each part using OpenAI TTS

    Both processes run in parallel for maximum efficiency.

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `session_id` (string): Session ID for tracking
    - `script_id` (string): ID of the script in the database

    **Optional Parameters:**
    - `model` (string): Image model - "flux-schnell", "flux-dev", "flux-pro", "sdxl" (default: "flux-schnell")
    - `images_per_part` (int): Number of images per script part (default: 2)
    - `voice` (string): OpenAI TTS voice - "alloy", "echo", "fable", "onyx", "nova", "shimmer" (default: "alloy")
    - `audio_option` (string): Audio option - "tts", "upload", "none", "instrumental" (default: "tts")

    **Returns:**
    - `session_id`: Session ID for tracking
    - `status`: Generation status
    - `micro_scenes`: Object with hook, concept, process, conclusion images and cost
    - `audio_files`: List of generated audio files with URLs and metadata
    - `total_duration`: Total audio duration in seconds
    - `total_cost`: Combined cost of image and audio generation
    """
    # Call orchestrator to generate images and audio simultaneously
    result = await orchestrator.finalize_script(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id,
        script_id=request.script_id,
        image_options={
            "model": request.model,
            "images_per_part": request.images_per_part
        },
        audio_config={
            "voice": request.voice,
            "audio_option": request.audio_option
        }
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Script finalization failed"))

    return {
        "session_id": request.session_id,
        "status": result["status"],
        "micro_scenes": result.get("micro_scenes", {}),
        "audio_files": result.get("audio_files", []),
        "total_duration": result.get("total_duration", 0.0),
        "total_cost": result.get("total_cost", 0.0)
    }


@router.post("/compose-video", response_model=ComposeVideoResponse)
async def compose_video(
    request: ComposeVideoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compose final educational video from generated images and audio.

    **Authentication Required:** Include X-User-Email header.

    This endpoint combines all generated assets (images, audio, background music)
    into a complete educational video using FFmpeg. It creates a video with:
    - Images from each script part (hook, concept, process, conclusion)
    - TTS narration audio synchronized with each part
    - Optional background music
    - Transitions and timing based on audio duration

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `session_id` (string): Session ID containing generated images and audio

    **Returns:**
    - `session_id`: Session ID for tracking
    - `status`: Composition status
    - `video_url`: URL of the composed video
    - `duration`: Total video duration in seconds
    - `segments_count`: Number of segments in the video
    """
    # Verify session exists and belongs to user
    session = db.query(SessionModel).filter(
        SessionModel.id == request.session_id,
        SessionModel.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Call orchestrator to compose video from educational assets
    result = await orchestrator.compose_educational_video(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Video composition failed"))

    return {
        "session_id": request.session_id,
        "status": result["status"],
        "video_url": result.get("video_url", ""),
        "duration": result.get("duration", 0.0),
        "segments_count": result.get("segments_count", 4)
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


# Test endpoint - Save pre-written script
class SaveTestScriptRequest(BaseModel):
    script_id: str
    hook: Dict[str, Any]
    concept: Dict[str, Any]
    process: Dict[str, Any]
    conclusion: Dict[str, Any]


class SaveTestScriptResponse(BaseModel):
    status: str
    script_id: str
    message: str


@router.post("/test/save-script", response_model=SaveTestScriptResponse)
async def save_test_script(
    request: SaveTestScriptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test endpoint to save a pre-written script to the database.
    For testing purposes only - allows test UI to create scripts without AI.
    """
    from app.models.database import Script

    # Create script in database
    script = Script(
        id=request.script_id,
        user_id=current_user.id,
        hook=request.hook,
        concept=request.concept,
        process=request.process,
        conclusion=request.conclusion
    )

    db.merge(script)
    db.commit()

    return {
        "status": "success",
        "script_id": request.script_id,
        "message": "Test script saved successfully"
    }


@router.get("/scripts/{script_id}")
async def get_script(
    script_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a script by ID.
    Returns the full script data including hook, concept, process, and conclusion.
    """
    from app.models.database import Script

    # Query script from database
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()

    if not script:
        raise HTTPException(status_code=404, detail=f"Script with ID {script_id} not found")

    return {
        "script_id": script.id,
        "user_id": script.user_id,
        "hook": script.hook,
        "concept": script.concept,
        "process": script.process,
        "conclusion": script.conclusion,
        "created_at": script.created_at.isoformat() if script.created_at else None
    }


# Export websocket_manager so it can be used in main.py
def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return websocket_manager
