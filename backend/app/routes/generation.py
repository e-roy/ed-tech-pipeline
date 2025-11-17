"""
Generation routes - handles all video generation workflow steps.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import threading
import logging
import asyncio
import json

from app.database import get_db
from app.models.database import Session as SessionModel, Asset, User
from app.routes.auth import get_current_user
from app.services.orchestrator import VideoGenerationOrchestrator
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/test/ping")
async def test_ping():
    """Simple test endpoint to verify server is responding."""
    return {"status": "ok", "message": "Server is running"}

@router.options("/test/save-script")
async def test_save_script_options():
    """Handle OPTIONS preflight for save-script endpoint."""
    return {"status": "ok"}

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
    desired_duration: Optional[float] = 60.0  # Default to 60 seconds


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
        user_id=current_user.id,
        desired_duration=request.desired_duration
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

    logger.info(f"Received save-script request for script_id: {request.script_id}, user_id: {current_user.id}")
    
    try:
        # Validate request data
        if not request.script_id:
            raise HTTPException(status_code=400, detail="script_id is required")
        
        # Create script in database
        script = Script(
            id=request.script_id,
            user_id=current_user.id,
            hook=request.hook,
            concept=request.concept,
            process=request.process,
            conclusion=request.conclusion
        )

        logger.debug(f"Attempting to save script: {script.id}")
        db.merge(script)
        db.commit()
        db.refresh(script)
        
        logger.info(f"Successfully saved script: {script.id}")

        return SaveTestScriptResponse(
            status="success",
            script_id=request.script_id,
            message="Test script saved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error saving test script: {e}")
        # Return detailed error for debugging
        error_detail = f"Failed to save script: {str(e)}"
        if "could not connect" in str(e).lower() or "connection" in str(e).lower():
            error_detail += " (Database connection issue - check DATABASE_URL in .env file)"
        elif "does not exist" in str(e).lower() or "relation" in str(e).lower():
            error_detail += " (Database table missing - run migrations: alembic upgrade head)"
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


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


# Track processing state per session (for concurrent request handling)
_processing_sessions: Dict[str, bool] = {}
_processing_lock = threading.Lock()


class ProcessStorySegmentsRequest(BaseModel):
    session_id: str
    s3_path: str
    options: Optional[Dict[str, Any]] = {
        "num_images": 2,
        "max_passes": 5,
        "max_verification_passes": 3,
        "fast_mode": False
    }


class ProcessStorySegmentsResponse(BaseModel):
    status: str
    session_id: str
    message: str


@router.post("/process-story-segments", response_model=ProcessStorySegmentsResponse)
async def process_story_segments(
    request: ProcessStorySegmentsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process story segments from segments.md and generate images.
    
    This endpoint:
    1. Validates segments.md format (primary validation)
    2. Checks for concurrent requests (reject if already processing)
    3. Reads config.json if exists
    4. Starts async processing via orchestrator
    5. Returns immediately with acceptance message
    
    Real-time progress is available via WebSocket.
    """
    import threading
    from app.agents.story_image_generator import parse_segments_md
    
    session_id = request.session_id
    s3_path = request.s3_path
    
    # Validate S3 bucket (must be pipeline-backend-assets, hardcoded)
    if not s3_path.startswith("users/"):
        raise HTTPException(
            status_code=400,
            detail="S3 path must start with 'users/'"
        )
    
    # Extract user_id from S3 path and verify session belongs to user
    path_parts = s3_path.split("/")
    if len(path_parts) < 3:
        raise HTTPException(
            status_code=400,
            detail="Invalid S3 path format. Expected: users/{user_id}/{session_id}/..."
        )
    
    try:
        path_user_id = int(path_parts[1])
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID in S3 path"
        )
    
    # Verify session belongs to user
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or does not belong to user"
        )
    
    # Verify user_id from path matches current user
    if path_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="S3 path user ID does not match authenticated user"
        )
    
    # Check for concurrent requests
    with _processing_lock:
        if session_id in _processing_sessions and _processing_sessions[session_id]:
            raise HTTPException(
                status_code=409,
                detail=f"Session {session_id} is already being processed"
            )
        _processing_sessions[session_id] = True
    
    try:
        # Primary validation: Read and validate segments.md format
        try:
            segments_content = storage_service.read_file(s3_path)
            segments_text = segments_content.decode("utf-8")
            
            template_title, segments = parse_segments_md(segments_text)
            
            if not template_title or not segments:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid segments.md format: missing template title or segments"
                )
            
            # Validate all segments have required data
            validation_errors = []
            for segment in segments:
                if not segment.get("narrationtext", "").strip():
                    validation_errors.append(
                        f"Segment {segment['number']} ({segment['title']}) is missing narration text"
                    )
                if not segment.get("visual_guidance_preview", "").strip():
                    validation_errors.append(
                        f"Segment {segment['number']} ({segment['title']}) is missing visual guidance preview"
                    )
            
            if validation_errors:
                raise HTTPException(
                    status_code=400,
                    detail=f"Validation errors: {'; '.join(validation_errors)}"
                )
            
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"segments.md not found at S3 path: {s3_path}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Error validating segments.md: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to validate segments.md: {str(e)}"
            )
        
        # Start async processing in background
        async def process_async():
            try:
                # Create new DB session for background task
                from app.database import SessionLocal
                background_db = SessionLocal()
                try:
                    await orchestrator.process_story_segments(
                        db=background_db,
                        session_id=session_id,
                        user_id=current_user.id,
                        s3_path=s3_path,
                        options=request.options or {}
                    )
                finally:
                    background_db.close()
            except Exception as e:
                logger.exception(f"Error in async processing for session {session_id}: {e}")
            finally:
                # Clear processing flag
                with _processing_lock:
                    _processing_sessions[session_id] = False
        
        # Start background task
        asyncio.create_task(process_async())
        
        return ProcessStorySegmentsResponse(
            status="accepted",
            session_id=session_id,
            message="Processing started, listen to WebSocket for updates"
        )
    
    except HTTPException:
        # Clear processing flag on validation error
        with _processing_lock:
            _processing_sessions[session_id] = False
        raise
    except Exception as e:
        # Clear processing flag on unexpected error
        with _processing_lock:
            _processing_sessions[session_id] = False
        logger.exception(f"Unexpected error in process_story_segments endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


class GenerateStoryImagesRequest(BaseModel):
    session_id: str
    script_id: str
    template_title: Optional[str] = "Educational Video"
    num_images: Optional[int] = 2
    max_passes: Optional[int] = 5
    max_verification_passes: Optional[int] = 3
    fast_mode: Optional[bool] = False
    diagram_s3_path: Optional[str] = None


class GenerateStoryImagesResponse(BaseModel):
    status: str
    session_id: str
    message: str
    template_title: Optional[str] = None


@router.post("/generate-story-images", response_model=GenerateStoryImagesResponse)
async def generate_story_images(
    request: GenerateStoryImagesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate story images from a script using the StoryImageGeneratorAgent.
    
    This endpoint:
    1. Retrieves the script from the database
    2. Converts script format (hook/concept/process/conclusion) to segments format
    3. Calls the story image generation agent
    4. Returns immediately with acceptance message
    
    Real-time progress is available via WebSocket.
    """
    from app.models.database import Script
    
    session_id = request.session_id
    script_id = request.script_id
    
    # Get or create session
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        # Auto-create session if it doesn't exist (for test UI convenience)
        session = SessionModel(
            id=session_id,
            user_id=current_user.id,
            status="pending"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        logger.info(f"Auto-created session {session_id} for user {current_user.id}")
    
    # Get script from database
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=404,
            detail=f"Script {script_id} not found or does not belong to user"
        )
    
    # Check for concurrent requests
    with _processing_lock:
        if session_id in _processing_sessions and _processing_sessions[session_id]:
            raise HTTPException(
                status_code=409,
                detail=f"Session {session_id} is already being processed"
            )
        _processing_sessions[session_id] = True
    
    try:
        # Convert script to segments format
        segments = []
        segment_mapping = [
            ("hook", "Hook"),
            ("concept", "Concept Introduction"),
            ("process", "Process Explanation"),
            ("conclusion", "Conclusion")
        ]
        
        start_time = 0
        for idx, (script_key, segment_title) in enumerate(segment_mapping, 1):
            script_part = getattr(script, script_key, {})
            if isinstance(script_part, dict):
                narration = script_part.get("text", "")
                visual_guidance = script_part.get("visual_guidance", "")
                duration_str = script_part.get("duration", "10")
                
                # Parse duration
                try:
                    duration = int(duration_str)
                except (ValueError, TypeError):
                    duration = 10
                
                segments.append({
                    "number": idx,
                    "title": segment_title,
                    "duration": duration,
                    "narrationtext": narration,
                    "visual_guidance_preview": visual_guidance
                })
                
                start_time += duration
        
        if not segments:
            raise HTTPException(
                status_code=400,
                detail="Script has no valid segments to process"
            )
        
        # Prepare S3 paths
        output_s3_prefix = f"users/{current_user.id}/{session_id}/images/"
        
        # Start async processing
        async def process_async():
            try:
                from app.database import SessionLocal
                background_db = SessionLocal()
                try:
                    # Call orchestrator's process_story_segments method
                    # But we need to create segments.md content first
                    from app.agents.story_image_generator import parse_segments_md
                    import json
                    
                    # Create segments.md content
                    template_title = request.template_title or "Educational Video"
                    segments_md_content = f"Template: {template_title}\n\n"
                    
                    for seg in segments:
                        start = sum(s["duration"] for s in segments[:segments.index(seg)])
                        end = start + seg["duration"]
                        segments_md_content += f"**Segment {seg['number']}: {seg['title']} ({start}-{end} seconds)**\n\n"
                        segments_md_content += f"- Narration text:\n  ```\n  {seg['narrationtext']}\n  ```\n"
                        segments_md_content += f"- Visual guidance preview: {seg['visual_guidance_preview']}\n\n"
                    
                    # Upload segments.md to S3
                    segments_s3_key = f"{output_s3_prefix}segments.md"
                    storage_service.upload_file_direct(
                        segments_md_content.encode("utf-8"),
                        segments_s3_key,
                        content_type="text/markdown"
                    )
                    
                    # Upload diagram if provided
                    if request.diagram_s3_path:
                        # Copy diagram to the images directory
                        try:
                            diagram_bytes = storage_service.read_file(request.diagram_s3_path)
                            diagram_s3_key = f"{output_s3_prefix}diagram.png"
                            storage_service.upload_file_direct(
                                diagram_bytes,
                                diagram_s3_key,
                                content_type="image/png"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to copy diagram: {e}")
                    
                    # Call orchestrator
                    options = {
                        "num_images": request.num_images,
                        "max_passes": request.max_passes,
                        "max_verification_passes": request.max_verification_passes,
                        "fast_mode": request.fast_mode
                    }
                    
                    await orchestrator.process_story_segments(
                        db=background_db,
                        session_id=session_id,
                        user_id=current_user.id,
                        s3_path=segments_s3_key,
                        options=options
                    )
                finally:
                    background_db.close()
            except Exception as e:
                logger.exception(f"Error in async story image generation for session {session_id}: {e}")
            finally:
                # Clear processing flag
                with _processing_lock:
                    _processing_sessions[session_id] = False
        
        # Start background task
        asyncio.create_task(process_async())
        
        return GenerateStoryImagesResponse(
            status="accepted",
            session_id=session_id,
            message="Story image generation started, listen to WebSocket for updates",
            template_title=request.template_title
        )
    
    except HTTPException:
        # Clear processing flag on validation error
        with _processing_lock:
            _processing_sessions[session_id] = False
        raise
    except Exception as e:
        # Clear processing flag on unexpected error
        with _processing_lock:
            _processing_sessions[session_id] = False
        logger.exception(f"Unexpected error in generate_story_images endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


class GetStoryImagesRequest(BaseModel):
    session_id: str


class StoryImageSegmentInfo(BaseModel):
    segment_number: int
    segment_title: str
    images: List[Dict[str, Any]]  # List of {s3_key, presigned_url, image_number}
    cost: float
    time_seconds: float
    status: str


class GetStoryImagesResponse(BaseModel):
    status: str
    template_title: Optional[str] = None
    segments_total: int
    segments_succeeded: int
    segments_failed: int
    total_images_generated: int
    total_cost_usd: float
    total_time_seconds: float
    segments: List[StoryImageSegmentInfo]
    failed_segments: List[Dict[str, Any]]
    status_s3_key: Optional[str] = None


@router.get("/story-images/{session_id}", response_model=GetStoryImagesResponse)
async def get_story_images(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get story image generation results for a session.
    
    Returns:
    - Status information from status.json
    - List of segments with their generated images
    - Presigned URLs for all images
    """
    # Verify session belongs to user
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or does not belong to user"
        )
    
    # Read status.json from S3
    status_s3_key = f"users/{current_user.id}/{session_id}/images/status.json"
    
    try:
        if not storage_service.file_exists(status_s3_key):
            raise HTTPException(
                status_code=404,
                detail="Story image generation not started or status.json not found"
            )
        
        status_content = storage_service.read_file(status_s3_key)
        status_data = json.loads(status_content.decode("utf-8"))
        
        # Extract template title from segments directory structure
        images_prefix = f"users/{current_user.id}/{session_id}/images/"
        template_title = None
        
        # Try to find template directory
        all_files = storage_service.list_files_by_prefix(images_prefix, limit=1000)
        for file_info in all_files:
            key = file_info["key"]
            # Look for pattern: users/{user_id}/{session_id}/images/{TemplateName}/...
            parts = key.replace(images_prefix, "").split("/")
            if len(parts) > 0 and parts[0] and not parts[0].endswith(".md") and not parts[0].endswith(".json"):
                template_title = parts[0]
                break
        
        # Build segment info with images
        segments_info = []
        # Try to get segment results from status_data, or build from successful_segments
        segment_results = status_data.get("segment_results", [])
        if not segment_results:
            # Fallback: try to get from successful_segments if available
            successful_segments = status_data.get("successful_segments", [])
            if successful_segments:
                segment_results = successful_segments
        
        for seg_result in segment_results:
            seg_num = seg_result.get("segment_number")
            seg_title = seg_result.get("segment_title", f"Segment {seg_num}")
            
            # Find images for this segment
            segment_prefix = f"{images_prefix}{template_title or 'Untitled'}/{seg_num}. {seg_title}/generated_images/"
            segment_files = storage_service.list_files_by_prefix(segment_prefix, limit=100)
            
            # Filter to only image files and sort by image number
            image_files = [
                f for f in segment_files 
                if f["key"].endswith((".png", ".jpg", ".jpeg"))
            ]
            image_files.sort(key=lambda x: x["key"])
            
            # Format images with image numbers
            images = []
            for idx, img_file in enumerate(image_files, 1):
                images.append({
                    "s3_key": img_file["key"],
                    "presigned_url": img_file["presigned_url"],
                    "image_number": idx
                })
            
            segments_info.append(StoryImageSegmentInfo(
                segment_number=seg_num,
                segment_title=seg_title,
                images=images,
                cost=seg_result.get("cost", 0.0),
                time_seconds=seg_result.get("time_seconds", 0.0),
                status="success" if seg_result.get("success") else "failed"
            ))
        
        # Get failed segments info
        failed_segments = status_data.get("errors", [])
        
        return GetStoryImagesResponse(
            status=status_data.get("status", "unknown"),
            template_title=template_title,
            segments_total=status_data.get("segments_total", 0),
            segments_succeeded=status_data.get("segments_succeeded", 0),
            segments_failed=status_data.get("segments_failed", 0),
            total_images_generated=status_data.get("total_images_generated", 0),
            total_cost_usd=status_data.get("total_cost_usd", 0.0),
            total_time_seconds=status_data.get("total_time_seconds", 0.0),
            segments=segments_info,
            failed_segments=failed_segments,
            status_s3_key=status_s3_key
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting story images: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve story images: {str(e)}"
        )


class RegenerateSegmentRequest(BaseModel):
    session_id: str
    script_id: str
    segment_number: int
    template_title: Optional[str] = "Educational Video"
    num_images: Optional[int] = 2
    max_passes: Optional[int] = 5
    max_verification_passes: Optional[int] = 3
    fast_mode: Optional[bool] = False
    diagram_s3_path: Optional[str] = None


@router.post("/regenerate-segment", response_model=GenerateStoryImagesResponse)
async def regenerate_segment(
    request: RegenerateSegmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate images for a specific segment.
    
    This endpoint:
    1. Retrieves the script from database
    2. Extracts the specific segment
    3. Regenerates images for that segment only
    4. Updates the segment's images in S3
    """
    from app.models.database import Script
    from app.agents.story_image_generator import StoryImageGeneratorAgent, generate_story_prompts
    from app.services.secrets import get_secret
    import asyncio
    
    session_id = request.session_id
    script_id = request.script_id
    segment_number = request.segment_number
    
    # Verify session belongs to user
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or does not belong to user"
        )
    
    # Get script from database
    script = db.query(Script).filter(
        Script.id == script_id,
        Script.user_id == current_user.id
    ).first()
    
    if not script:
        raise HTTPException(
            status_code=404,
            detail=f"Script {script_id} not found or does not belong to user"
        )
    
    # Convert script to segments format and find the target segment
    segment_mapping = [
        ("hook", "Hook", 1),
        ("concept", "Concept Introduction", 2),
        ("process", "Process Explanation", 3),
        ("conclusion", "Conclusion", 4)
    ]
    
    target_segment = None
    for script_key, segment_title, seg_num in segment_mapping:
        if seg_num == segment_number:
            script_part = getattr(script, script_key, {})
            if isinstance(script_part, dict):
                narration = script_part.get("text", "")
                visual_guidance = script_part.get("visual_guidance", "")
                duration_str = script_part.get("duration", "10")
                
                try:
                    duration = int(duration_str)
                except (ValueError, TypeError):
                    duration = 10
                
                target_segment = {
                    "number": seg_num,
                    "title": segment_title,
                    "duration": duration,
                    "narrationtext": narration,
                    "visual_guidance_preview": visual_guidance
                }
                break
    
    if not target_segment:
        raise HTTPException(
            status_code=400,
            detail=f"Segment {segment_number} not found in script"
        )
    
    # Check for concurrent requests
    with _processing_lock:
        processing_key = f"{session_id}_segment_{segment_number}"
        if processing_key in _processing_sessions and _processing_sessions[processing_key]:
            raise HTTPException(
                status_code=409,
                detail=f"Segment {segment_number} is already being regenerated"
            )
        _processing_sessions[processing_key] = True
    
    try:
        # Prepare S3 paths
        output_s3_prefix = f"users/{current_user.id}/{session_id}/images/"
        template_title = request.template_title or "Educational Video"
        
        # Start async processing
        async def process_async():
            try:
                from app.database import SessionLocal
                background_db = SessionLocal()
                try:
                    # Get API keys
                    openrouter_key = get_secret("pipeline/openrouter-api-key")
                    replicate_key = get_secret("pipeline/replicate-api-key")
                    
                    # Instantiate agent
                    agent = StoryImageGeneratorAgent(
                        storage_service=storage_service,
                        openrouter_api_key=openrouter_key,
                        replicate_api_key=replicate_key
                    )
                    
                    # Download diagram if provided
                    diagram_bytes = None
                    if request.diagram_s3_path:
                        try:
                            diagram_bytes = storage_service.read_file(request.diagram_s3_path)
                        except Exception as e:
                            logger.warning(f"Failed to download diagram: {e}")
                    
                    # Process single segment
                    segment_result = await agent._process_segment(
                        segment=target_segment,
                        template_title=template_title,
                        diagram_bytes=diagram_bytes,
                        output_s3_prefix=output_s3_prefix,
                        num_images=request.num_images,
                        max_passes=request.max_passes,
                        max_verification_passes=request.max_verification_passes,
                        fast_mode=request.fast_mode
                    )
                    
                    logger.info(f"Segment {segment_number} regeneration complete: {segment_result.get('success')}")
                    
                finally:
                    background_db.close()
            except Exception as e:
                logger.exception(f"Error regenerating segment {segment_number}: {e}")
            finally:
                with _processing_lock:
                    _processing_sessions[processing_key] = False
        
        # Start background task
        asyncio.create_task(process_async())
        
        return GenerateStoryImagesResponse(
            status="accepted",
            session_id=session_id,
            message=f"Segment {segment_number} regeneration started",
            template_title=template_title
        )
    
    except HTTPException:
        with _processing_lock:
            _processing_sessions[processing_key] = False
        raise
    except Exception as e:
        with _processing_lock:
            _processing_sessions[processing_key] = False
        logger.exception(f"Unexpected error in regenerate_segment endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )