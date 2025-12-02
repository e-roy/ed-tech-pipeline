"""
Generation routes - handles all video generation workflow steps.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import threading
import logging
import asyncio
import json

from app.database import get_db
from app.models.database import Session as SessionModel
from app.routes.auth import get_current_user, CurrentUser
from app.services.orchestrator import VideoGenerationOrchestrator
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


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
    # script_id removed - now reads from video_session.generated_script
    model: Optional[str] = "flux-schnell"
    images_per_part: Optional[int] = 2


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


@router.post("/generate-images", response_model=GenerateImagesResponse)
async def generate_images(
    request: GenerateImagesRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 1: Generate images from a video script.

    **Authentication:** Requires X-User-Email header from authenticated frontend.

    Reads script from video_session.generated_script and generates 2-3 images per script part
    (hook, concept, process, conclusion) based on visual guidance.
    Images are stored in S3 and tracked in the database.

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `session_id` (string): Session ID (script is read from video_session.generated_script)

    **Optional Parameters:**
    - `model` (string): Model to use ("flux-pro", "flux-dev", "flux-schnell", "sdxl") (default: "flux-schnell")
    - `images_per_part` (int): Number of images per script part (default: 2)

    **Returns:**
    - `session_id`: Session ID for tracking
    - `status`: Generation status
    - `micro_scenes`: Object with hook, concept, process, conclusion images and cost
    """
    # Call orchestrator to generate images from script (now uses session_id to find script)
    result = await orchestrator.generate_images(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id,
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


class GenerateAudioRequest(BaseModel):
    session_id: str
    # script_id removed - now reads from video_session.generated_script
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
    # script_id removed - now reads from video_session.generated_script
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate audio narration from script using OpenAI TTS.

    **Authentication Required:** Include X-User-Email header.

    Reads script from video_session.generated_script and generates TTS audio for each part
    (hook, concept, process, conclusion). Audio files are stored in S3 and tracked in the database.

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `session_id` (string): Session ID (script is read from video_session.generated_script)

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
    # Call orchestrator to generate audio from script (now uses session_id to find script)
    result = await orchestrator.generate_audio(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id,
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Finalize script by generating both images and audio simultaneously.

    **Authentication Required:** Include X-User-Email header.

    Reads script from video_session.generated_script and generates:
    - Images for each part (hook, concept, process, conclusion) using template + DALL-E
    - Audio narration for each part using OpenAI TTS

    Both processes run in parallel for maximum efficiency.

    **Required Headers:**
    - `X-User-Email` (string): User's email from NextAuth session

    **Required Parameters:**
    - `session_id` (string): Session ID (script is read from video_session.generated_script)

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
    # Call orchestrator to generate images and audio simultaneously (now uses session_id to find script)
    result = await orchestrator.finalize_script(
        db=db,
        session_id=request.session_id,
        user_id=current_user.id,
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
    current_user: CurrentUser = Depends(get_current_user),
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


# Test endpoint - Save pre-written script
class SaveTestScriptRequest(BaseModel):
    session_id: str  # Now uses session_id instead of script_id
    hook: Dict[str, Any]
    concept: Dict[str, Any]
    process: Dict[str, Any]
    conclusion: Dict[str, Any]


class SaveTestScriptResponse(BaseModel):
    status: str
    session_id: str  # Returns session_id instead of script_id
    message: str


@router.post("/test/save-script", response_model=SaveTestScriptResponse)
async def save_test_script(
    request: SaveTestScriptRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test endpoint to save a pre-written script to video_session.generated_script.
    For testing purposes only - allows test UI to create scripts without AI.

    Now stores script in video_session table instead of separate scripts table.
    """
    from sqlalchemy import text as sql_text

    logger.info(f"Received save-script request for session_id: {request.session_id}, user_id: {current_user.id}")

    try:
        # Validate request data
        if not request.session_id:
            raise HTTPException(status_code=400, detail="session_id is required")

        # current_user.id now directly contains auth_user.id (UUID string from frontend)
        auth_user_id = current_user.id
        logger.info(f"Using auth_user.id: {auth_user_id} for email: {current_user.email}")

        # Build the generated_script JSON structure
        generated_script = {
            "hook": request.hook,
            "concept": request.concept,
            "process": request.process,
            "conclusion": request.conclusion
        }

        # Check if video_session exists
        result = db.execute(
            sql_text("SELECT id FROM video_session WHERE id = :session_id AND user_id = :user_id"),
            {"session_id": request.session_id, "user_id": auth_user_id}
        ).fetchone()

        if result:
            # Update existing video_session
            db.execute(
                sql_text("""
                    UPDATE video_session
                    SET generated_script = :script, updated_at = NOW()
                    WHERE id = :session_id AND user_id = :user_id
                """),
                {
                    "script": json.dumps(generated_script),
                    "session_id": request.session_id,
                    "user_id": auth_user_id
                }
            )
            logger.info(f"Updated generated_script in existing video_session: {request.session_id}")
        else:
            # Create new video_session with the script
            db.execute(
                sql_text("""
                    INSERT INTO video_session (id, user_id, status, generated_script, created_at, updated_at)
                    VALUES (:session_id, :user_id, 'script_created', :script, NOW(), NOW())
                """),
                {
                    "session_id": request.session_id,
                    "user_id": auth_user_id,
                    "script": json.dumps(generated_script)
                }
            )
            logger.info(f"Created new video_session with script: {request.session_id}")

        db.commit()

        return SaveTestScriptResponse(
            status="success",
            session_id=request.session_id,
            message="Test script saved to video_session successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        if db:
            try:
                db.rollback()
            except Exception:
                pass  # Ignore rollback errors
        logger.exception(f"Error saving test script: {e}")
        # Return detailed error for debugging
        error_detail = f"Failed to save script: {str(e)}"
        if "could not connect" in str(e).lower() or "connection" in str(e).lower():
            error_detail += " (Database connection issue - check DATABASE_URL in .env file)"
        elif "does not exist" in str(e).lower() or "relation" in str(e).lower():
            error_detail += " (Database table missing - ensure video_session table exists)"
        elif "violates foreign key" in str(e).lower():
            error_detail += " (Foreign key error - ensure auth_user exists with matching email)"
        raise HTTPException(
            status_code=500,
            detail=error_detail
        )


@router.get("/scripts/{session_id}")
async def get_script(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a script by session ID from video_session.generated_script.
    Returns the full script data including hook, concept, process, and conclusion.

    Now reads from video_session table instead of separate scripts table.
    """
    from sqlalchemy import text as sql_text

    # current_user.id now directly contains auth_user.id (UUID string from frontend)
    auth_user_id = current_user.id

    # Query script from video_session table
    result = db.execute(
        sql_text("""
            SELECT id, user_id, generated_script, created_at
            FROM video_session
            WHERE id = :session_id AND user_id = :user_id
        """),
        {"session_id": session_id, "user_id": auth_user_id}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail=f"Script with session ID {session_id} not found")

    # Parse generated_script JSON
    generated_script = result.generated_script if result.generated_script else {}
    if isinstance(generated_script, str):
        generated_script = json.loads(generated_script)

    return {
        "session_id": result.id,
        "user_id": result.user_id,
        "hook": generated_script.get("hook", {}),
        "concept": generated_script.get("concept", {}),
        "process": generated_script.get("process", {}),
        "conclusion": generated_script.get("conclusion", {}),
        "created_at": result.created_at.isoformat() if result.created_at else None
    }


# Export websocket_manager so it can be used in main.py
def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return websocket_manager


# Track processing state per session (for concurrent request handling)
_processing_sessions: Dict[str, bool] = {}
_processing_lock = threading.Lock()


class GenerateStoryImagesRequest(BaseModel):
    session_id: str
    # script_id removed - now reads from video_session.generated_script
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate story images from a script using the StoryImageGeneratorAgent.

    This endpoint:
    1. Retrieves the script from video_session.generated_script
    2. Converts script format (hook/concept/process/conclusion) to segments format
    3. Calls the story image generation agent
    4. Returns immediately with acceptance message

    Real-time progress is available via WebSocket.
    """
    from sqlalchemy import text as sql_text

    session_id = request.session_id

    # Get or create backend session
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

    # current_user.id now directly contains auth_user.id (UUID string from frontend)
    auth_user_id = current_user.id

    # Get script from video_session table
    result = db.execute(
        sql_text("""
            SELECT id, user_id, generated_script
            FROM video_session
            WHERE id = :session_id AND user_id = :user_id
        """),
        {"session_id": session_id, "user_id": auth_user_id}
    ).fetchone()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Video session {session_id} not found or does not belong to user"
        )

    # Parse generated_script JSON
    generated_script = result.generated_script if result.generated_script else {}
    if isinstance(generated_script, str):
        generated_script = json.loads(generated_script)

    if not generated_script:
        raise HTTPException(
            status_code=404,
            detail=f"No script found in video_session {session_id}"
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
            script_part = generated_script.get(script_key, {})
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
        
        # Prepare S3 paths using StorageService helpers
        output_s3_prefix = storage_service.get_session_prefix(current_user.id, session_id, "images")
        
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
                    
                    # Validate and limit num_images to maximum of 3
                    validated_num_images = request.num_images or 2
                    if validated_num_images > 3:
                        logger.warning(f"num_images ({validated_num_images}) exceeds maximum of 3, limiting to 3")
                        validated_num_images = 3
                    if validated_num_images < 1:
                        raise ValueError("num_images must be at least 1")
                    
                    # Call orchestrator
                    options = {
                        "num_images": validated_num_images,
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


class TestWebhookRequest(BaseModel):
    """Request model for webhook testing."""
    session_id: str
    webhook_secret: Optional[str] = None  # Optional - if provided, overrides AWS Secrets Manager/config


class WebhookTestResult(BaseModel):
    """Result of a single webhook test."""
    status: str  # "video_complete" or "video_failed"
    success: bool
    request_payload: Dict[str, Any]
    response_status_code: Optional[int]
    response_body: Optional[Dict[str, Any]]
    error: Optional[str]


class TestWebhookResponse(BaseModel):
    """Response model for webhook testing."""
    success: bool
    webhook_url: str
    results: List[WebhookTestResult]
    message: str


@router.post("/test/webhook", response_model=TestWebhookResponse)
async def test_webhook(request: TestWebhookRequest):
    """
    Test endpoint to send test webhook calls for both video_complete and video_failed statuses.
    Uses webhook URL and secret from config/AWS Secrets Manager.
    """
    import httpx
    from app.config import get_settings
    from app.services.orchestrator import _get_webhook_secret
    
    settings = get_settings()
    webhook_url = settings.WEBHOOK_URL
    
    # Use provided webhook_secret if given, otherwise get from AWS Secrets Manager/config
    if request.webhook_secret:
        webhook_secret = request.webhook_secret
        logger.info("Using webhook_secret provided in request (overriding AWS Secrets Manager/config)")
    else:
        webhook_secret = _get_webhook_secret()
    
    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="WEBHOOK_SECRET not configured. Cannot test webhook."
        )
    
    if not webhook_url:
        raise HTTPException(
            status_code=500,
            detail="WEBHOOK_URL not configured. Cannot test webhook."
        )
    
    results = []
    dummy_video_url = "https://example.com/test-video.mp4"
    
    # Test both statuses
    test_cases = [
        {
            "status": "video_complete",
            "video_url": dummy_video_url
        },
        {
            "status": "video_failed",
            "video_url": ""
        }
    ]
    
    for test_case in test_cases:
        status = test_case["status"]
        video_url = test_case["video_url"]
        
        request_payload = {
            "sessionId": request.session_id,
            "videoUrl": video_url,
            "status": status
        }
        
        result = WebhookTestResult(
            status=status,
            success=False,
            request_payload=request_payload,
            response_status_code=None,
            response_body=None,
            error=None
        )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook_url,
                    headers={
                        "Content-Type": "application/json",
                        "x-webhook-secret": webhook_secret
                    },
                    json=request_payload
                )
                
                result.response_status_code = response.status_code
                
                try:
                    result.response_body = response.json()
                except Exception:
                    result.response_body = {"raw_text": response.text}
                
                result.success = response.is_success
                
                if not result.success:
                    result.error = f"HTTP {response.status_code}: {response.text[:200]}"
                    
        except httpx.HTTPStatusError as e:
            result.response_status_code = e.response.status_code
            result.error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            try:
                result.response_body = e.response.json()
            except Exception:
                result.response_body = {"raw_text": e.response.text}
        except httpx.RequestError as e:
            result.error = f"Network error: {str(e)}"
        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"
        
        results.append(result)
    
    # Determine overall success
    all_success = all(r.success for r in results)
    
    return TestWebhookResponse(
        success=all_success,
        webhook_url=webhook_url,
        results=results,
        message=f"Tested {len(results)} webhook calls. {'All succeeded' if all_success else 'Some failed'}."
    )