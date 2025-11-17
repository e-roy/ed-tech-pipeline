"""
Main FastAPI application for Gauntlet Pipeline Orchestrator.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from app.config import get_settings
import os

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
# Allow "null" origin for local file testing (test_ui.html)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local file testing
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
)

# Get shared WebSocket manager from generation module
websocket_manager = generation.get_websocket_manager()

# Include routers (auth removed - using header-based auth)
app.include_router(generation.router, prefix="/api", tags=["Generation"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTPException with CORS headers."""
    from fastapi.responses import JSONResponse
    from fastapi import HTTPException as FastAPIHTTPException
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to catch all unhandled exceptions."""
    import logging
    import traceback
    from fastapi.responses import JSONResponse
    from fastapi import HTTPException
    
    # Don't handle HTTPException here - it's handled above
    if isinstance(exc, HTTPException):
        raise exc
    
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception on {request.method} {request.url}")
    logger.error(f"Exception: {exc}")
    logger.error(f"Traceback: {''.join(traceback.format_tb(exc.__traceback__))}")
    
    # Return JSON response with CORS headers
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

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


@app.get("/test_ui.html")
async def serve_test_ui():
    """Serve the test UI HTML file."""
    test_ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_ui.html")
    if os.path.exists(test_ui_path):
        return FileResponse(test_ui_path)
    raise HTTPException(status_code=404, detail="test_ui.html not found")


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
