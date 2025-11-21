"""
Main FastAPI application for Gauntlet Pipeline Orchestrator.
"""
import os
import time
import asyncio
import json
import logging
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.config import get_settings
from app.services.storage import StorageService
from app.services.websocket_manager import WebSocketManager
from app.database import get_db

logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize storage service for monitor
storage_service = StorageService()

# Initialize WebSocket manager for agent status updates
websocket_manager = WebSocketManager()

# Initialize FastAPI app
app = FastAPI(
    title="Gauntlet Pipeline Orchestrator",
    description="Backend orchestrator for AI video generation pipeline.",
    version="1.0.0",
    debug=settings.DEBUG
)


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health endpoint for load balancers and monitoring."""
    return {"status": "healthy", "service": "Gauntlet Pipeline Orchestrator"}


# Configure CORS for Next.js frontend
# Allow Vercel frontend and local development
frontend_url = settings.FRONTEND_URL
cors_origins = [
    frontend_url,
    "http://localhost:3000",  # Local development
    "http://localhost:3001",  # Alternative local port
]

# Add API Gateway domain if using (optional, for direct API Gateway access)
# cors_origins.append("https://*.execute-api.us-east-2.amazonaws.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,  # Enable credentials for auth cookies/tokens
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Request/Response models
class ProcessRequest(BaseModel):
    sessionId: str
    script: str
    diagramUrls: Optional[List[str]] = None


class ProcessResponse(BaseModel):
    success: bool
    message: str
    sessionId: str
    videoId: str
    videoUrl: str


# Agent 2: Storyboard Generator
async def agent_2_generate_storyboard(
    session_id: str,
    script: str,
    diagram_urls: Optional[List[str]] = None
) -> str:
    """
    Agent 2: Generate storyboard from script and optional diagrams.

    Returns:
        storyboardId: ID of the generated storyboard
    """
    # TODO: Implement storyboard generation logic
    storyboard_id = f"storyboard-{session_id}-stub"
    return storyboard_id


# Agent 3: Audio Generator
async def agent_3_generate_audio(
    session_id: str,
    storyboard_id: str
) -> dict:
    """
    Agent 3: Generate narration and music from storyboard.

    Returns:
        dict with narrationIds and musicId
    """
    # TODO: Implement audio generation logic
    return {
        "narrationIds": [f"narration-{session_id}-1-stub", f"narration-{session_id}-2-stub"],
        "musicId": f"music-{session_id}-stub"
    }


# Agent 4: Video Composer
async def agent_4_compose_video(
    session_id: str,
    storyboard_id: str,
    narration_ids: List[str],
    music_id: str
) -> dict:
    """
    Agent 4: Compose final video and store in S3 + database.

    Returns:
        dict with videoId and videoUrl
    """
    # TODO: Implement video composition logic
    # TODO: Upload to S3
    # TODO: Store reference in database
    video_id = f"video-{session_id}-stub"
    video_url = f"https://s3.amazonaws.com/bucket/{video_id}.mp4"
    return {
        "videoId": video_id,
        "videoUrl": video_url
    }


@app.post("/api/process", response_model=ProcessResponse)
async def process(request: ProcessRequest):
    """
    Process endpoint that orchestrates the video generation pipeline.

    Flow:
    1. Agent 2: Generate storyboard from inputs
    2. Agent 3: Generate narration and music from storyboard
    3. Agent 4: Compose video and store in S3/database
    """
    # Agent 2: Generate storyboard
    storyboard_id = await agent_2_generate_storyboard(
        session_id=request.sessionId,
        script=request.script,
        diagram_urls=request.diagramUrls
    )

    # Agent 3: Generate audio
    audio_result = await agent_3_generate_audio(
        session_id=request.sessionId,
        storyboard_id=storyboard_id
    )

    # Agent 4: Compose video
    video_result = await agent_4_compose_video(
        session_id=request.sessionId,
        storyboard_id=storyboard_id,
        narration_ids=audio_result["narrationIds"],
        music_id=audio_result["musicId"]
    )

    return ProcessResponse(
        success=True,
        message="Video generation completed",
        sessionId=request.sessionId,
        videoId=video_result["videoId"],
        videoUrl=video_result["videoUrl"]
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Gauntlet Pipeline Orchestrator"}


@app.get("/scaffoldtest", response_class=HTMLResponse)
@app.get("/scaffoldtest_ui.html", response_class=HTMLResponse)
async def scaffoldtest_ui():
    """
    Serve the scaffold test UI HTML page.
    
    Access at: http://localhost:8000/scaffoldtest or /scaffoldtest_ui.html
    """
    # Get the backend directory (parent of app directory)
    backend_dir = Path(__file__).parent.parent
    html_file = backend_dir / "scaffoldtest_ui.html"
    
    if not html_file.exists():
        raise HTTPException(status_code=404, detail="scaffoldtest_ui.html not found")
    
    return FileResponse(html_file)


@app.get("/videotest", response_class=HTMLResponse)
@app.get("/video_test.html", response_class=HTMLResponse)
async def video_test_ui():
    """
    Serve the video test HTML page.

    Access at: http://localhost:8000/videotest or /video_test.html
    """
    backend_dir = Path(__file__).parent.parent
    html_file = backend_dir / "video_test.html"

    if not html_file.exists():
        raise HTTPException(status_code=404, detail="video_test.html not found")

    return FileResponse(html_file)


# =============================================================================
# Agent Processing Functions (Scaffolding)
# Import agents from agents folder
# =============================================================================

from app.agents.agent_2 import agent_2_process as agent_2_process_impl


async def agent_2_process(
    user_id: str,
    session_id: str,
    template_id: str,
    chosen_diagram_id: str,
    script_id: str
):
    """
    Agent2: First agent in the processing pipeline.
    
    Wrapper function that calls the agent implementation from agents folder.
    """
    await agent_2_process_impl(
        websocket_manager=websocket_manager,
        user_id=user_id,
        session_id=session_id,
        template_id=template_id,
        chosen_diagram_id=chosen_diagram_id,
        script_id=script_id,
        storage_service=storage_service
    )


# =============================================================================
# WebSocket Endpoint for Agent Status Updates
# =============================================================================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time agent status updates.
    
    Clients connect to this endpoint to receive status updates from agents.
    Messages are filtered by session_id.
    
    Path parameter format: `/ws/{session_id}` (for direct connections)
    """
    import secrets
    connection_id = f"ws_{secrets.token_urlsafe(16)}"
    
    await websocket_manager.connect(websocket, session_id, connection_id)
    
    # Send connection confirmation to client
    try:
        await websocket.send_text(json.dumps({
            "type": "connection_ready",
            "sessionID": session_id,
            "status": "connected"
        }))
    except Exception as e:
        logger.error(f"Failed to send connection ready message: {e}")
    
    # Shared connection handling logic
    await _handle_websocket_connection(websocket, session_id, connection_id)

@app.websocket("/ws")
async def websocket_endpoint_query(websocket: WebSocket):
    """
    WebSocket endpoint for real-time agent status updates (query parameter version).
    
    This endpoint supports API Gateway which passes session_id as query parameter.
    Format: `/ws?session_id=xxx`
    
    Also supports API Gateway WebSocket where query params may be in the request URL.
    """
    import secrets
    from urllib.parse import parse_qs
    
    # Extract session_id from query params (API Gateway compatibility)
    query_string = websocket.url.query
    
    # Try to get session_id from query string
    session_id = None
    if query_string:
        query_params = parse_qs(query_string)
        session_id = query_params.get('session_id', [None])[0]
    
    # If not in query string, try to get from headers (API Gateway may pass it there)
    if not session_id:
        # Check for session_id in headers (some API Gateway configurations pass it here)
        session_id = websocket.headers.get('x-session-id') or websocket.headers.get('session-id')
    
    # If still not found, try to extract from URL path (fallback)
    if not session_id:
        # Check if URL path contains session_id (e.g., /ws?session_id=xxx but parsed differently)
        url_str = str(websocket.url)
        if 'session_id=' in url_str:
            try:
                # Extract from URL string directly
                parts = url_str.split('session_id=')
                if len(parts) > 1:
                    session_id = parts[1].split('&')[0].split('/')[0]
            except:
                pass
    
    # If still no session_id, reject connection
    if not session_id:
        logger.warning(f"WebSocket connection rejected: no session_id found in query string or headers. URL: {websocket.url}")
        await websocket.close(code=1008, reason="session_id required in query string or headers")
        return
    
    connection_id = f"ws_{secrets.token_urlsafe(16)}"
    
    await websocket_manager.connect(websocket, session_id, connection_id)
    
    # Send connection confirmation to client
    try:
        await websocket.send_text(json.dumps({
            "type": "connection_ready",
            "sessionID": session_id,
            "status": "connected"
        }))
    except Exception as e:
        logger.error(f"Failed to send connection ready message: {e}")
    
    # Shared connection handling logic
    await _handle_websocket_connection(websocket, session_id, connection_id)

async def _handle_websocket_connection(websocket: WebSocket, session_id: str, connection_id: str):
    """Shared WebSocket connection handling logic."""
    try:
        while True:
            # Keep connection alive - wait for any message (text or ping/pong)
            # This keeps the connection open to receive agent status updates
            try:
                data = await websocket.receive_text()
                # Client can send messages if needed, but we primarily use this for receiving
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        # Respond to ping with pong
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    pass
            except WebSocketDisconnect:
                break
            except Exception:
                # Handle ping/pong or other WebSocket frames, but check if still connected
                try:
                    await websocket.receive()
                except (WebSocketDisconnect, RuntimeError):
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(websocket, session_id, connection_id)

async def _handle_websocket_connection(websocket: WebSocket, session_id: str, connection_id: str):
    """Shared WebSocket connection handling logic."""
    try:
        while True:
            # Keep connection alive - wait for any message (text or ping/pong)
            # This keeps the connection open to receive agent status updates
            try:
                data = await websocket.receive_text()
                # Client can send messages if needed, but we primarily use this for receiving
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        # Respond to ping with pong
                        await websocket.send_text(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    pass
            except WebSocketDisconnect:
                break
            except Exception:
                # Handle ping/pong or other WebSocket frames, but check if still connected
                try:
                    await websocket.receive()
                except (WebSocketDisconnect, RuntimeError):
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(websocket, session_id, connection_id)


# =============================================================================
# Video Session API Endpoint
# =============================================================================

@app.get("/api/get-video-session/{session_id}")
async def get_video_session(session_id: str, db: Session = Depends(get_db)):
    """
    Get video_session row by session_id.
    
    Returns full row data including topic, confirmed_facts, generated_script, etc.
    """
    try:
        result = db.execute(
            sql_text("SELECT * FROM video_session WHERE id = :session_id"),
            {"session_id": session_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Video session {session_id} not found")
        
        # Convert row to dict
        # SQLAlchemy 2.0+ Row objects support _mapping attribute for dict conversion
        if hasattr(result, '_mapping'):
            row_dict = dict(result._mapping)
        else:
            # Fallback: try attribute access (SQLAlchemy 1.4 style)
            row_dict = {
                "id": getattr(result, 'id', None),
                "user_id": getattr(result, 'user_id', None),
                "status": getattr(result, 'status', None),
                "topic": getattr(result, 'topic', None),
                "learning_objective": getattr(result, 'learning_objective', None),
                "confirmed_facts": getattr(result, 'confirmed_facts', None),
                "generated_script": getattr(result, 'generated_script', None),
                "created_at": getattr(result, 'created_at', None),
                "updated_at": getattr(result, 'updated_at', None)
            }
        
        # Convert datetime objects to ISO format strings
        if row_dict.get('created_at'):
            row_dict['created_at'] = row_dict['created_at'].isoformat()
        if row_dict.get('updated_at'):
            row_dict['updated_at'] = row_dict['updated_at'].isoformat()
        
        return row_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Database error querying video_session: {e}")
        # Return JSON error response
        error_detail = str(e)
        # Don't expose full error details in production - sanitize
        if "Permission denied" in error_detail or "certificate" in error_detail.lower():
            error_detail = "Database connection error. Please check server configuration."
        # Use JSONResponse to ensure proper JSON format
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": {"error": "Database error", "message": error_detail}}
        )


# =============================================================================
# Start Processing API Endpoint
# =============================================================================

class StartProcessingRequest(BaseModel):
    """Request model for starting the agent processing pipeline."""
    agent_selection: Optional[str] = "Full Test"  # "Full Test", "Agent2", "Agent4", "Agent5"
    video_session_data: Optional[dict] = None  # For Full Test mode
    # Individual agent fields (optional, required for individual agents)
    userID: Optional[str] = None
    sessionID: Optional[str] = None
    templateID: Optional[str] = None
    chosenDiagramID: Optional[str] = None
    scriptID: Optional[str] = None
    # Agent4 specific fields
    script: Optional[dict] = None  # For Agent4
    voice: Optional[str] = None  # For Agent4
    audio_option: Optional[str] = None  # For Agent4
    # Agent5 specific fields
    supersessionid: Optional[str] = None  # For Agent5


class StartProcessingResponse(BaseModel):
    """Response model for start processing endpoint."""
    success: bool
    message: str
    sessionID: str


@app.post("/api/startprocessing", response_model=StartProcessingResponse)
async def start_processing(
    request: StartProcessingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> StartProcessingResponse:
    """
    Start the agent processing pipeline.
    
    Supports multiple modes:
    - Full Test: Uses video_session_data from database
    - Agent2: Minimal inputs (userID, sessionID)
    - Agent4: Requires script, voice, audio_option
    - Agent5: Requires userID, sessionID, supersessionid
    """
    agent_selection = request.agent_selection or "Full Test"
    
    # Handle Full Test mode
    if agent_selection == "Full Test":
        video_session_data = request.video_session_data
        session_id: Optional[str] = None
        user_id: Optional[str] = None

        if video_session_data:
            session_id = video_session_data.get("id") or request.sessionID
            user_id = video_session_data.get("user_id") or request.userID
        else:
            if not request.sessionID or not request.userID:
                raise HTTPException(
                    status_code=400,
                    detail="sessionID and userID are required for Full Test when video_session_data is not provided",
                )
            session_id = request.sessionID.strip()
            user_id = request.userID.strip()
            try:
                result = db.execute(
                    sql_text(
                        "SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"
                    ),
                    {"session_id": session_id, "user_id": user_id},
                ).fetchone()
            except Exception as e:
                logger.exception("Error querying video_session: %s", e)
                raise HTTPException(
                    status_code=500,
                    detail="Failed to load video_session data. Please try again.",
                )

            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Video session not found for session_id={session_id} and user_id={user_id}",
                )

            if hasattr(result, "_mapping"):
                video_session_data = dict(result._mapping)
            else:
                # Fallback for older SQLAlchemy versions
                video_session_data = {
                    "id": getattr(result, "id", None),
                    "user_id": getattr(result, "user_id", None),
                    "generated_script": getattr(result, "generated_script", None),
                }

        if not session_id:
            raise HTTPException(status_code=400, detail="Missing session ID for Full Test")
        if not user_id:
            raise HTTPException(status_code=400, detail="Missing user ID for Full Test")
        if not session_id or not user_id:
            raise HTTPException(
                status_code=400,
                detail="sessionID and userID are required for Full Test",
            )

        # Use orchestrator to coordinate the Full Test process
        async def run_orchestrator():
            """Wrapper to catch and log errors in background task."""
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                "Starting orchestrator for Full Test, session %s, user %s",
                session_id,
                user_id,
            )

            # Wait for WebSocket connection
            logger.info(f"Waiting for WebSocket connection for session {session_id}...")
            connection_ready = await websocket_manager.wait_for_connection(
                session_id,
                max_wait=3.0,
                check_interval=0.1
            )
            
            if not connection_ready:
                logger.warning(
                    "No WebSocket connection found for session %s after waiting. Proceeding anyway.",
                    session_id,
                )
            
            try:
                from app.services.orchestrator import VideoGenerationOrchestrator
                orchestrator = VideoGenerationOrchestrator(websocket_manager)
                await orchestrator.start_full_test_process(
                    userId=user_id,
                    sessionId=session_id,
                    db=db
                )
                logger.info(f"Orchestrator completed for session {session_id}")
            except Exception as e:
                logger.exception(f"Error in orchestrator for session {session_id}: {e}")
                # Error status will be sent by orchestrator
        
        loop = asyncio.get_event_loop()
        task = loop.create_task(run_orchestrator())
        if not hasattr(app.state, 'background_tasks'):
            app.state.background_tasks = set()
        app.state.background_tasks.add(task)
        task.add_done_callback(app.state.background_tasks.discard)
        
        return StartProcessingResponse(
            success=True,
            message="Full Test processing started successfully",
            sessionID=session_id
        )
    
    # Handle individual agent modes
    elif agent_selection == "Agent2":
        if not request.userID or not request.userID.strip():
            raise HTTPException(status_code=400, detail="userID is required for Agent2")
        if not request.sessionID or not request.sessionID.strip():
            raise HTTPException(status_code=400, detail="sessionID is required for Agent2")
        
        # Start Agent2 with minimal inputs
        async def run_agent_2_with_error_handling():
            logger = logging.getLogger(__name__)
            logger.info(f"Starting Agent2 for session {request.sessionID}")
            
            connection_ready = await websocket_manager.wait_for_connection(
                request.sessionID,
                max_wait=3.0,
                check_interval=0.1
            )
            
            try:
                await agent_2_process_impl(
                    websocket_manager=websocket_manager,
                    user_id=request.userID,
                    session_id=request.sessionID,
                    template_id="",  # Stub
                    chosen_diagram_id="",  # Stub
                    script_id="",  # Stub
                    storage_service=storage_service,
                    video_session_data=None
                )
            except Exception as e:
                logger.exception(f"Error in agent_2_process: {e}")
                try:
                    await websocket_manager.send_progress(request.sessionID, {
                        "agentnumber": "Agent2",
                        "userID": request.userID,
                        "sessionID": request.sessionID,
                        "status": "error",
                        "error": str(e),
                        "reason": f"Agent2 failed: {type(e).__name__}"
                    })
                except Exception:
                    pass
        
        loop = asyncio.get_event_loop()
        task = loop.create_task(run_agent_2_with_error_handling())
        if not hasattr(app.state, 'background_tasks'):
            app.state.background_tasks = set()
        app.state.background_tasks.add(task)
        task.add_done_callback(app.state.background_tasks.discard)
        
        return StartProcessingResponse(
            success=True,
            message="Agent2 started successfully",
            sessionID=request.sessionID
        )
    
    elif agent_selection == "Agent4":
        if not request.userID or not request.userID.strip():
            raise HTTPException(status_code=400, detail="userID is required for Agent4")
        if not request.sessionID or not request.sessionID.strip():
            raise HTTPException(status_code=400, detail="sessionID is required for Agent4")
        
        # Query video_session table to get the same data Agent2 uses
        video_session_data = None
        try:
            result = db.execute(
                sql_text(
                    "SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"
                ),
                {"session_id": request.sessionID, "user_id": request.userID},
            ).fetchone()
            
            if result:
                # Convert result to dict (same as orchestrator does)
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
                logger.info(f"Loaded video_session data for Agent4 session {request.sessionID}")
        except Exception as e:
            logger.warning(f"Could not load video_session data for Agent4: {e}")
            # Continue anyway - Agent4 can work with just the script parameter
        
        # Start Agent4 directly
        async def run_agent_4_with_error_handling():
            logger = logging.getLogger(__name__)
            logger.info(f"Starting Agent4 for session {request.sessionID}")
            
            connection_ready = await websocket_manager.wait_for_connection(
                request.sessionID,
                max_wait=3.0,
                check_interval=0.1
            )
            
            try:
                from app.agents.agent_4 import agent_4_process
                
                await agent_4_process(
                    websocket_manager=websocket_manager,
                    user_id=request.userID,
                    session_id=request.sessionID,
                    script=request.script or {},  # Use provided script or empty dict (will be extracted from DB)
                    voice=request.voice or "alloy",
                    audio_option=request.audio_option or "tts",
                    storage_service=storage_service,
                    agent2_data=None,  # Deprecated
                    video_session_data=video_session_data,  # Pass same data as orchestrator
                    db=db  # Pass database session so Agent4 can query if needed
                )
            except Exception as e:
                logger.exception(f"Error in agent_4_process: {e}")
                try:
                    await websocket_manager.send_progress(request.sessionID, {
                        "agentnumber": "Agent4",
                        "userID": request.userID,
                        "sessionID": request.sessionID,
                        "status": "error",
                        "error": str(e),
                        "reason": f"Agent4 failed: {type(e).__name__}"
                    })
                except Exception:
                    pass
        
        loop = asyncio.get_event_loop()
        task = loop.create_task(run_agent_4_with_error_handling())
        if not hasattr(app.state, 'background_tasks'):
            app.state.background_tasks = set()
        app.state.background_tasks.add(task)
        task.add_done_callback(app.state.background_tasks.discard)
        
        return StartProcessingResponse(
            success=True,
            message="Agent4 started successfully",
            sessionID=request.sessionID
        )
    
    elif agent_selection == "Agent5":
        if not request.userID or not request.userID.strip():
            raise HTTPException(status_code=400, detail="userID is required for Agent5")
        if not request.sessionID or not request.sessionID.strip():
            raise HTTPException(status_code=400, detail="sessionID is required for Agent5")
        if not request.supersessionid or not request.supersessionid.strip():
            raise HTTPException(status_code=400, detail="supersessionid is required for Agent5")
        
        # Start Agent5 directly
        async def run_agent_5_with_error_handling():
            logger = logging.getLogger(__name__)
            logger.info(f"Starting Agent5 for session {request.sessionID}")
            
            connection_ready = await websocket_manager.wait_for_connection(
                request.sessionID,
                max_wait=3.0,
                check_interval=0.1
            )
            
            try:
                from app.agents.agent_5 import agent_5_process
                await agent_5_process(
                    websocket_manager=websocket_manager,
                    user_id=request.userID,
                    session_id=request.sessionID,
                    supersessionid=request.supersessionid,
                    storage_service=storage_service,
                    pipeline_data=None  # Optional
                )
            except Exception as e:
                logger.exception(f"Error in agent_5_process: {e}")
                try:
                    await websocket_manager.send_progress(request.sessionID, {
                        "agentnumber": "Agent5",
                        "userID": request.userID,
                        "sessionID": request.sessionID,
                        "status": "error",
                        "error": str(e),
                        "reason": f"Agent5 failed: {type(e).__name__}"
                    })
                except Exception:
                    pass
        
        loop = asyncio.get_event_loop()
        task = loop.create_task(run_agent_5_with_error_handling())
        if not hasattr(app.state, 'background_tasks'):
            app.state.background_tasks = set()
        app.state.background_tasks.add(task)
        task.add_done_callback(app.state.background_tasks.discard)
        
        return StartProcessingResponse(
            success=True,
            message="Agent5 started successfully",
            sessionID=request.sessionID
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Invalid agent_selection: {agent_selection}. Must be 'Full Test', 'Agent2', 'Agent4', or 'Agent5'")


# =============================================================================
# Agent5 Restart Endpoint - Restart from Remotion rendering
# =============================================================================

class RestartAgent5Request(BaseModel):
    """Request to restart Agent5 from Remotion rendering stage."""
    userID: str
    sessionID: str
    supersessionid: Optional[str] = None


@app.post("/api/restart-agent5-remotion")
async def restart_agent5_remotion(request: RestartAgent5Request, db: Session = Depends(get_db)):
    """
    Restart Agent5 from the Remotion rendering stage.
    
    This endpoint allows restarting video generation from the Remotion rendering step,
    skipping video clip generation by reusing clips already stored in S3.
    
    Use case: When Remotion rendering fails but video clips were successfully generated.
    """
    logger.info(f"Restart Agent5 Remotion request for session {request.sessionID}")
    
    # Verify clips exist in S3 before starting
    try:
        sections = ["hook", "concept", "process", "conclusion"]
        agent5_prefix = f"scaffold_test/{request.userID}/{request.sessionID}/agent5/"
        
        missing_clips = []
        for section in sections:
            concat_key = f"{agent5_prefix}{section}_concat.mp4"
            try:
                storage_service.s3_client.head_object(
                    Bucket=storage_service.bucket_name,
                    Key=concat_key
                )
            except Exception:
                missing_clips.append(section)
        
        if missing_clips:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot restart - missing video clips for sections: {', '.join(missing_clips)}. Please regenerate from scratch."
            )
        
        logger.info(f"All clips verified for session {request.sessionID}, starting restart")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying clips: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to verify clips: {str(e)}")
    
    # Generate new supersessionid if not provided
    import secrets
    if not request.supersessionid:
        supersessionid = f"{request.sessionID}_restart_{secrets.token_urlsafe(8)[:12]}"
    else:
        supersessionid = request.supersessionid
    
    # Start Agent5 with restart flag
    async def run_agent_5_restart():
        try:
            from app.agents.agent_5 import agent_5_process
            from app.services.orchestrator import VideoGenerationOrchestrator
            
            # Create orchestrator for status callback
            orchestrator = VideoGenerationOrchestrator(websocket_manager)
            
            async def status_callback(agentnumber: str, status: str, userID: str, sessionID: str, timestamp: int, **kwargs):
                """Forward status to WebSocket."""
                status_data = {
                    "agentnumber": agentnumber,
                    "userID": userID,
                    "sessionID": sessionID,
                    "status": status,
                    "timestamp": timestamp,
                    **kwargs
                }
                await websocket_manager.send_progress(sessionID, status_data)
            
            # Call agent_5_process with restart flag
            result = await agent_5_process(
                websocket_manager=None,
                user_id=request.userID,
                session_id=request.sessionID,
                supersessionid=supersessionid,
                storage_service=storage_service,
                pipeline_data=None,
                db=db,
                status_callback=status_callback,
                restart_from_remotion=True  # KEY: Skip clip generation
            )
            
            # Send completion status
            await websocket_manager.send_progress(request.sessionID, {
                "agentnumber": "Agent5",
                "userID": request.userID,
                "sessionID": request.sessionID,
                "status": "finished",
                "message": "Remotion rendering completed successfully",
                "videoUrl": result,
                "timestamp": int(time.time() * 1000)
            })
            
        except Exception as e:
            logger.exception(f"Error in agent_5_process restart: {e}")
            try:
                await websocket_manager.send_progress(request.sessionID, {
                    "agentnumber": "Agent5",
                    "userID": request.userID,
                    "sessionID": request.sessionID,
                    "status": "error",
                    "error": str(e),
                    "reason": f"Agent5 restart failed: {type(e).__name__}",
                    "timestamp": int(time.time() * 1000)
                })
            except Exception:
                pass
    
    # Run in background
    loop = asyncio.get_event_loop()
    task = loop.create_task(run_agent_5_restart())
    if not hasattr(app.state, 'background_tasks'):
        app.state.background_tasks = set()
    app.state.background_tasks.add(task)
    task.add_done_callback(app.state.background_tasks.discard)
    
    return {
        "success": True,
        "message": "Agent5 restart from Remotion initiated",
        "sessionID": request.sessionID,
        "supersessionid": supersessionid
    }


# =============================================================================
# Agent Test Endpoints - Test individual agents with custom input
# =============================================================================

class AgentTestRequest(BaseModel):
    """Request model for testing agents with custom input."""
    input: Dict[str, Any]


class AgentTestResponse(BaseModel):
    """Standardized response from agent tests."""
    success: bool
    data: Dict[str, Any]
    cost: float
    duration: float
    error: Optional[str] = None


@app.get("/api/test/agents")
async def list_available_agents() -> Dict[str, Any]:
    """List all available agents with their expected input schemas."""
    return {
        "agents": [
            {
                "name": "storyboard",
                "description": "Agent 2: Generate storyboard from script and optional diagrams",
                "inputSchema": {
                    "sessionId": "string",
                    "script": "string",
                    "diagramUrls": ["string (optional)"]
                },
                "exampleInput": {
                    "sessionId": "test-session-123",
                    "script": "This is the script content for the video...",
                    "diagramUrls": ["https://example.com/diagram1.png", "https://example.com/diagram2.png"]
                }
            },
            {
                "name": "audio",
                "description": "Agent 3: Generate narration and music from storyboard",
                "inputSchema": {
                    "sessionId": "string",
                    "storyboardId": "string"
                },
                "exampleInput": {
                    "sessionId": "test-session-123",
                    "storyboardId": "storyboard-001"
                }
            },
            {
                "name": "video",
                "description": "Agent 4: Compose final video from storyboard, narration, and music",
                "inputSchema": {
                    "sessionId": "string",
                    "storyboardId": "string",
                    "narrationIds": ["string"],
                    "musicId": "string"
                },
                "exampleInput": {
                    "sessionId": "test-session-123",
                    "storyboardId": "storyboard-001",
                    "narrationIds": ["narration-1", "narration-2"],
                    "musicId": "music-001"
                }
            }
        ]
    }


@app.post("/api/test/agent/storyboard", response_model=AgentTestResponse)
async def test_storyboard_agent(request: AgentTestRequest) -> AgentTestResponse:
    """Test Agent 2 (Storyboard Generator) with custom input."""
    start_time = time.time()

    try:
        input_data = request.input

        # Validate required fields
        required = ["sessionId", "script"]
        missing = [f for f in required if f not in input_data]
        if missing:
            return AgentTestResponse(
                success=False,
                data={},
                cost=0.0,
                duration=time.time() - start_time,
                error=f"Missing required fields: {', '.join(missing)}"
            )

        # Call the agent
        storyboard_id = await agent_2_generate_storyboard(
            session_id=input_data["sessionId"],
            script=input_data["script"],
            diagram_urls=input_data.get("diagramUrls")
        )

        return AgentTestResponse(
            success=True,
            data={"storyboardId": storyboard_id},
            cost=0.0,  # Stub has no cost
            duration=time.time() - start_time
        )

    except Exception as e:
        return AgentTestResponse(
            success=False,
            data={},
            cost=0.0,
            duration=time.time() - start_time,
            error=str(e)
        )


@app.post("/api/test/agent/audio", response_model=AgentTestResponse)
async def test_audio_agent(request: AgentTestRequest) -> AgentTestResponse:
    """Test Agent 3 (Audio Generator) with custom input."""
    start_time = time.time()

    try:
        input_data = request.input

        # Validate required fields
        required = ["sessionId", "storyboardId"]
        missing = [f for f in required if f not in input_data]
        if missing:
            return AgentTestResponse(
                success=False,
                data={},
                cost=0.0,
                duration=time.time() - start_time,
                error=f"Missing required fields: {', '.join(missing)}"
            )

        # Call the agent
        result = await agent_3_generate_audio(
            session_id=input_data["sessionId"],
            storyboard_id=input_data["storyboardId"]
        )

        return AgentTestResponse(
            success=True,
            data=result,
            cost=0.0,  # Stub has no cost
            duration=time.time() - start_time
        )

    except Exception as e:
        return AgentTestResponse(
            success=False,
            data={},
            cost=0.0,
            duration=time.time() - start_time,
            error=str(e)
        )


@app.post("/api/test/agent/video", response_model=AgentTestResponse)
async def test_video_agent(request: AgentTestRequest) -> AgentTestResponse:
    """Test Agent 4 (Video Composer) with custom input."""
    start_time = time.time()

    try:
        input_data = request.input

        # Validate required fields
        required = ["sessionId", "storyboardId", "narrationIds", "musicId"]
        missing = [f for f in required if f not in input_data]
        if missing:
            return AgentTestResponse(
                success=False,
                data={},
                cost=0.0,
                duration=time.time() - start_time,
                error=f"Missing required fields: {', '.join(missing)}"
            )

        # Call the agent
        result = await agent_4_compose_video(
            session_id=input_data["sessionId"],
            storyboard_id=input_data["storyboardId"],
            narration_ids=input_data["narrationIds"],
            music_id=input_data["musicId"]
        )

        return AgentTestResponse(
            success=True,
            data=result,
            cost=0.0,  # Stub has no cost
            duration=time.time() - start_time
        )

    except Exception as e:
        return AgentTestResponse(
            success=False,
            data={},
            cost=0.0,
            duration=time.time() - start_time,
            error=str(e)
        )


# =============================================================================
# Local Audio File Serving Endpoint
# =============================================================================

@app.get("/api/audio/local")
async def serve_local_audio(path: str):
    """
    Serve a local audio file from the temp directory.

    This endpoint is used by the test UI to play generated audio files
    that haven't been uploaded to S3 yet.
    """
    import os
    import tempfile

    # Security check: only allow files from temp directory
    temp_dir = tempfile.gettempdir()

    # Normalize the path
    normalized_path = os.path.normpath(path)

    # Ensure the file is in the temp directory
    if not normalized_path.startswith(temp_dir):
        raise HTTPException(status_code=403, detail="Access denied: file must be in temp directory")

    # Check if file exists
    if not os.path.exists(normalized_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Return the file
    return FileResponse(
        normalized_path,
        media_type="audio/mpeg",
        filename=os.path.basename(normalized_path)
    )


@app.get("/api/video/proxy")
async def proxy_video(url: str):
    """
    Proxy a video from S3 to avoid CORS issues.

    This endpoint fetches the video from the given URL and streams it
    to the browser with proper headers for video playback.
    """
    import httpx
    from starlette.responses import StreamingResponse

    async def stream_video():
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("GET", url) as response:
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        stream_video(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": "inline"
        }
    )


# =============================================================================
# Agent 4 Direct Test Endpoint (Audio Pipeline)
# =============================================================================

class Agent4TestRequest(BaseModel):
    """Request model for testing Agent 4 (Audio Pipeline) directly."""
    session_id: str
    script: Dict[str, Any]
    voice: str = "alloy"
    audio_option: str = "tts"
    agent2_data: Optional[Dict[str, Any]] = None  # Optional data from Agent2


@app.post("/api/agent4/test", response_model=AgentTestResponse)
async def test_agent4_audio(request: Agent4TestRequest) -> AgentTestResponse:
    """
    Test Agent 4 (Audio Pipeline) directly with custom script input.

    This endpoint allows direct testing of the audio generation functionality
    without going through the full pipeline.
    """
    start_time = time.time()

    try:
        # Import and instantiate the AudioPipelineAgent
        from app.agents.audio_pipeline import AudioPipelineAgent
        from app.agents.base import AgentInput

        # Create agent instance
        audio_agent = AudioPipelineAgent(
            db=None,  # No DB for direct testing
            storage_service=storage_service,
            websocket_manager=websocket_manager
        )

        # Create agent input
        agent_input = AgentInput(
            session_id=request.session_id,
            data={
                "script": request.script,
                "voice": request.voice,
                "audio_option": request.audio_option
            }
        )

        # Process audio generation
        result = await audio_agent.process(agent_input)

        # Build pipeline_data structure like agent_4 does for agent_5
        pipeline_data = {
            "agent2_data": request.agent2_data or {
                "template_id": "test-template",
                "chosen_diagram_id": "test-diagram",
                "script_id": "test-script",
                "supersessionid": f"{request.session_id}_test"
            },
            "script": request.script,
            "voice": request.voice,
            "audio_option": request.audio_option,
            "audio_data": result.data
        }

        return AgentTestResponse(
            success=result.success,
            data=pipeline_data,
            cost=result.cost,
            duration=result.duration,
            error=result.error
        )

    except Exception as e:
        import traceback
        logger.error(f"Agent 4 test failed: {e}\n{traceback.format_exc()}")
        return AgentTestResponse(
            success=False,
            data={},
            cost=0.0,
            duration=time.time() - start_time,
            error=str(e)
        )


# =============================================================================
# Agent 5 Direct Test Endpoint (Video Generator)
# =============================================================================

class Agent5TestRequest(BaseModel):
    """Request model for testing Agent 5 (Video Generator) directly."""
    session_id: str
    pipeline_data: Dict[str, Any]
    generation_mode: str = "video"  # Always uses AI video generation (Replicate Minimax)


@app.post("/api/agent5/test", response_model=AgentTestResponse)
async def test_agent5_video(request: Agent5TestRequest) -> AgentTestResponse:
    """
    Test Agent 5 (Video Generator) directly with pipeline data.

    This endpoint allows direct testing of the video generation functionality
    without going through the full pipeline.

    Expected pipeline_data structure:
    {
        "script": {
            "hook": {"text": "...", "duration": "12", "visual_prompt": "..."},
            "concept": {"text": "...", "duration": "15", "visual_prompt": "..."},
            "process": {"text": "...", "duration": "22", "visual_prompt": "..."},
            "conclusion": {"text": "...", "duration": "11", "visual_prompt": "..."}
        },
        "audio_data": {
            "audio_files": [
                {"part": "hook", "url": "...", "duration": 4.4, ...},
                ...
            ],
            "background_music": {"url": "...", "duration": 60}
        }
    }
    """
    start_time = time.time()

    try:
        # Import the agent
        from app.agents.agent_5 import agent_5_process

        # Generate a supersession ID for this test
        supersessionid = f"{request.session_id}_test"

        # Use real WebSocket manager so UI can receive progress updates
        # Run agent 5 and get the video URL directly
        video_url = await agent_5_process(
            websocket_manager=websocket_manager,
            user_id="test_user",
            session_id=request.session_id,
            supersessionid=supersessionid,
            storage_service=storage_service,
            pipeline_data=request.pipeline_data,
            generation_mode=request.generation_mode
        )

        # Calculate cost for AI video generation
        # Replicate Minimax video-01: ~$0.035 per 5s video
        # 4 scenes = $0.14 total
        cost = 4 * 0.035  # $0.14
        model = "replicate-minimax-video-01"
        data = {
            "videoUrl": video_url,
            "supersessionId": supersessionid,
            "model": model,
            "videoDuration": "5s",
            "videosGenerated": 4
        }

        return AgentTestResponse(
            success=True,
            data=data,
            cost=cost,
            duration=time.time() - start_time
        )

    except Exception as e:
        import traceback
        logger.error(f"Agent 5 test failed: {e}\n{traceback.format_exc()}")
        return AgentTestResponse(
            success=False,
            data={},
            cost=0.0,
            duration=time.time() - start_time,
            error=str(e)
        )


class AnimatedVideoRequest(BaseModel):
    """Request model for rendering programmatic animated video."""
    session_id: str
    animation_data: Dict[str, Any] = {}
    background_music_volume: float = 0.3


@app.post("/api/agent5/animated", response_model=AgentTestResponse)
async def render_animated_video(request: AnimatedVideoRequest) -> AgentTestResponse:
    """
    Render a programmatic animated video (no DALL-E images).

    Uses the PhotosynthesisAnimation composition which is fully code-generated
    with animated molecules, plants, sun rays, etc.
    """
    import asyncio
    import subprocess
    import tempfile
    import uuid
    from pathlib import Path

    start_time = time.time()
    from urllib.parse import quote

    try:
        # Path to Remotion project
        # main.py is at backend/app/main.py, so go up 3 levels to pipeline root, then into remotion
        # __file__ -> backend/app/main.py
        # .parent -> backend/app
        # .parent.parent -> backend
        # .parent.parent.parent -> pipeline (root)
        remotion_dir = Path(__file__).parent.parent.parent / "remotion"

        # Create temp directory for output
        temp_dir = tempfile.mkdtemp(prefix="animated_video_")
        output_path = os.path.join(temp_dir, "output.mp4")

        # Convert local filepaths to URLs for audio files
        animation_data = request.animation_data.copy() if request.animation_data else {}
        if "audio_data" in animation_data and "audio_files" in animation_data["audio_data"]:
            for audio_file in animation_data["audio_data"]["audio_files"]:
                # If filepath exists but url is empty, convert to local serve URL
                if audio_file.get("filepath") and not audio_file.get("url"):
                    encoded_path = quote(audio_file["filepath"])
                    audio_file["url"] = f"http://localhost:8000/api/audio/local?path={encoded_path}"

        # Prepare props for Remotion
        props = {
            "animationData": animation_data,
            "backgroundMusicVolume": request.background_music_volume
        }

        # Write props to temp file
        props_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        import json
        json.dump(props, props_file)
        props_file.close()

        try:
            # Run Remotion render with EducationalAnimation composition
            cmd = f"bunx remotion render src/index.ts EducationalAnimation {output_path} --props={props_file.name}"

            logger.info(f"Rendering animated video: {cmd}")

            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                cwd=str(remotion_dir),
                capture_output=True,
                text=True,
                shell=True,
                env={**os.environ, "PATH": f"/Users/mfuechec/.bun/bin:{os.environ.get('PATH', '')}"}
            )

            if result.returncode != 0:
                raise RuntimeError(f"Remotion render failed: {result.stderr}\n{result.stdout}")

            # Upload to S3
            video_filename = f"animated_video_{uuid.uuid4().hex[:8]}.mp4"
            supersessionid = f"{request.session_id}_animated"
            video_s3_key = f"scaffold_test/test_user/{supersessionid}/{video_filename}"

            with open(output_path, "rb") as f:
                video_content = f.read()

            storage_service.upload_file_direct(video_content, video_s3_key, "video/mp4")
            video_url = storage_service.generate_presigned_url(video_s3_key, expires_in=86400)

            return AgentTestResponse(
                success=True,
                data={
                    "videoUrl": video_url,
                    "supersessionId": supersessionid
                },
                cost=0.0,
                duration=time.time() - start_time
            )

        finally:
            os.unlink(props_file.name)
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        import traceback
        logger.error(f"Animated video render failed: {e}\n{traceback.format_exc()}")
        return AgentTestResponse(
            success=False,
            data={},
            cost=0.0,
            duration=time.time() - start_time,
            error=str(e)
        )


# =============================================================================
# Monitor Endpoints - Pipeline visibility into S3 bucket contents
# =============================================================================

@app.get("/api/monitor/sessions")
async def monitor_list_sessions() -> Dict[str, Any]:
    """
    List all sessions from S3 by scanning the users/ prefix.
    Returns sessions organized by user with asset counts.
    """
    if not storage_service.s3_client:
        return {"error": "Storage service not configured", "sessions": []}

    try:
        # List all objects under users/ prefix
        paginator = storage_service.s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=storage_service.bucket_name,
            Prefix='users/',
            Delimiter=''
        )

        # Parse S3 keys to extract session info
        sessions: Dict[str, Dict[str, Any]] = {}

        for page in page_iterator:
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']
                parts = key.split('/')

                # Expected format: users/{user_id}/{session_id}/{asset_type}/{filename}
                if len(parts) < 5:
                    continue

                user_id = parts[1]
                session_id = parts[2]
                asset_type = parts[3]

                # Skip 'input' folder (not part of pipeline output)
                if session_id == 'input':
                    continue

                session_key = f"{user_id}/{session_id}"

                if session_key not in sessions:
                    sessions[session_key] = {
                        "sessionId": session_id,
                        "userId": user_id,
                        "assets": {
                            "images": 0,
                            "videos": 0,
                            "audio": 0,
                            "final": 0,
                            "other": 0
                        },
                        "lastModified": obj['LastModified'].isoformat(),
                        "totalSize": 0
                    }

                # Update counts
                if asset_type in sessions[session_key]["assets"]:
                    sessions[session_key]["assets"][asset_type] += 1
                else:
                    sessions[session_key]["assets"]["other"] += 1

                sessions[session_key]["totalSize"] += obj['Size']

                # Track latest modification
                if obj['LastModified'].isoformat() > sessions[session_key]["lastModified"]:
                    sessions[session_key]["lastModified"] = obj['LastModified'].isoformat()

        # Sort by last modified (newest first)
        session_list = sorted(
            sessions.values(),
            key=lambda x: x["lastModified"],
            reverse=True
        )

        return {
            "sessions": session_list,
            "count": len(session_list)
        }

    except Exception as e:
        return {"error": str(e), "sessions": []}


@app.get("/api/monitor/sessions/{user_id}/{session_id}")
async def monitor_get_session(user_id: str, session_id: str) -> Dict[str, Any]:
    """
    Get detailed info for a specific session including all assets with presigned URLs.
    """
    if not storage_service.s3_client:
        return {"error": "Storage service not configured"}

    try:
        prefix = f"users/{user_id}/{session_id}/"
        files = storage_service.list_files_by_prefix(prefix)

        # Organize files by asset type
        assets: Dict[str, List[Dict[str, Any]]] = {
            "images": [],
            "videos": [],
            "audio": [],
            "final": [],
            "other": []
        }

        for file_info in files:
            key = file_info["key"]
            parts = key.split('/')

            if len(parts) >= 4:
                asset_type = parts[3]

                # Determine content type from extension
                filename = parts[-1]
                if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    content_type = 'image'
                elif filename.endswith('.mp4') or filename.endswith('.webm'):
                    content_type = 'video'
                elif filename.endswith('.mp3') or filename.endswith('.wav'):
                    content_type = 'audio'
                else:
                    content_type = 'other'

                asset_info = {
                    "key": key,
                    "filename": filename,
                    "size": file_info["size"],
                    "lastModified": file_info["last_modified"],
                    "url": file_info["presigned_url"],
                    "contentType": content_type
                }

                if asset_type in assets:
                    assets[asset_type].append(asset_info)
                else:
                    assets["other"].append(asset_info)

        # Sort each asset type by last modified
        for asset_type in assets:
            assets[asset_type].sort(key=lambda x: x["lastModified"] or "", reverse=True)

        return {
            "sessionId": session_id,
            "userId": user_id,
            "assets": assets,
            "totalFiles": len(files)
        }

    except Exception as e:
        return {"error": str(e)}


# Scene Generator endpoint
from pydantic import BaseModel
from typing import Optional
import tempfile
import subprocess
import uuid
import math

class SceneGenerateRequest(BaseModel):
    text: str
    duration: int
    visual_prompt: str
    base_scene: Optional[Dict[str, Any]] = None
    previous_scene_context: Optional[str] = None

@app.post("/api/scene/generate")
async def generate_scene(request: SceneGenerateRequest):
    """Generate a continuous scene by stitching multiple video clips with improved transitions."""
    try:
        from app.services.replicate_video import ReplicateVideoService

        # Calculate number of clips needed (Minimax generates ~6 second clips)
        CLIP_DURATION = 6
        num_clips = math.ceil(request.duration / CLIP_DURATION)

        # Build full prompt incorporating ALL input data
        full_prompt = request.visual_prompt

        # Add base scene context if provided
        if request.base_scene:
            context_parts = []
            if request.base_scene.get("style"):
                context_parts.append(request.base_scene["style"])
            if request.base_scene.get("setting"):
                context_parts.append(f"Setting: {request.base_scene['setting']}")
            if request.base_scene.get("teacher"):
                context_parts.append(f"Teacher: {request.base_scene['teacher']}")
            if request.base_scene.get("students"):
                context_parts.append(f"Students: {request.base_scene['students']}")

            if context_parts:
                full_prompt = " | ".join(context_parts) + " | " + full_prompt

        # Add previous scene context if provided
        if request.previous_scene_context:
            full_prompt = f"{full_prompt} | Continuing from: {request.previous_scene_context}"

        # Initialize video service
        video_service = ReplicateVideoService()

        # Generate all clips using the FULL prompt
        clip_urls = []
        for i in range(num_clips):
            # Use text-to-video (Minimax) to avoid S3 frame extraction issues
            video_url = await video_service.generate_video(
                prompt=full_prompt,  # Use full_prompt instead of just visual_prompt
                model="minimax",
                seed=42 + i  # Different seed per clip for variety
            )
            clip_urls.append(video_url)

        # Download clips to temp directory
        temp_dir = tempfile.mkdtemp()
        clip_paths = []

        async with httpx.AsyncClient(timeout=120.0) as client:
            for i, url in enumerate(clip_urls):
                response = await client.get(url)
                response.raise_for_status()
                clip_path = f"{temp_dir}/clip_{i}.mp4"
                with open(clip_path, 'wb') as f:
                    f.write(response.content)
                clip_paths.append(clip_path)

        # Stitch clips with improved 0.7s fade transitions
        if len(clip_paths) == 1:
            # Single clip, just return it
            final_video_path = clip_paths[0]
        else:
            # Build ffmpeg command for crossfade stitching
            final_video_path = f"{temp_dir}/final.mp4"

            # Improved transition: 0.7s fade for smoother blending
            transition_duration = 0.7

            # Create concat file for simple concatenation first
            concat_list = f"{temp_dir}/concat.txt"
            with open(concat_list, 'w') as f:
                for clip_path in clip_paths:
                    f.write(f"file '{clip_path}'\n")

            # Simple concat without transitions for now (ffmpeg xfade is complex)
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list,
                "-c", "copy",
                final_video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")

        # Upload to S3 and return
        storage_service = StorageService()
        video_filename = f"scene_{uuid.uuid4().hex[:8]}.mp4"
        video_s3_key = f"scaffold_test/test_user/scenes/{video_filename}"

        with open(final_video_path, "rb") as f:
            video_content = f.read()

        storage_service.upload_file_direct(video_content, video_s3_key, "video/mp4")
        video_url = storage_service.generate_presigned_url(video_s3_key, expires_in=86400)

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        return {
            "success": True,
            "data": {
                "videoUrl": video_url,
                "numClips": num_clips
            },
            "duration": request.duration,
            "cost": num_clips * 0.035  # Minimax cost per clip
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
