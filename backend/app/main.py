"""
Main FastAPI application for Gauntlet Pipeline Orchestrator.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from app.config import get_settings

settings = get_settings()

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
    scriptId: str
    diagramIds: List[str]
    templateIds: List[str]


class ProcessResponse(BaseModel):
    success: bool
    message: str
    sessionId: str
    videoId: str
    videoUrl: str


# Agent 2: Storyboard Generator
async def agent_2_generate_storyboard(
    session_id: str,
    script_id: str,
    diagram_ids: List[str],
    template_ids: List[str]
) -> str:
    """
    Agent 2: Generate storyboard from script, diagrams, and templates.

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
        script_id=request.scriptId,
        diagram_ids=request.diagramIds,
        template_ids=request.templateIds
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
