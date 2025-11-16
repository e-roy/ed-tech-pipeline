"""
Main FastAPI application for Gauntlet Pipeline Orchestrator.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.config import get_settings

# Import routes
from app.routes import generation, sessions, storage

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Gauntlet Pipeline Orchestrator",
    description="Backend orchestrator for AI video generation pipeline. "
                "Authentication is handled by frontend (NextAuth) via request headers.",
    version="1.0.0",
    debug=settings.DEBUG
)

# Configure CORS for Next.js frontend
# Restrict to known frontend domains for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "https://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-User-Id", "X-User-Email"],
)

# Get shared WebSocket manager from generation module
websocket_manager = generation.get_websocket_manager()

# Include routers (auth removed - using header-based auth)
app.include_router(generation.router, prefix="/api", tags=["Generation"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Gauntlet Pipeline Orchestrator",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB check
        "services": {
            "orchestrator": "ready",
            "websocket": "ready"
        }
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time progress updates.

    Args:
        websocket: WebSocket connection
        session_id: Session ID to track
    """
    await websocket_manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back for now (can be extended for client commands)
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
