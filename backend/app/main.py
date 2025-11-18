"""
Main FastAPI application for Gauntlet Pipeline Orchestrator.
"""
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.services.storage import StorageService

settings = get_settings()

# Initialize storage service for monitor
storage_service = StorageService()

# Initialize FastAPI app
app = FastAPI(
    title="Gauntlet Pipeline Orchestrator",
    description="Backend orchestrator for AI video generation pipeline.",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
