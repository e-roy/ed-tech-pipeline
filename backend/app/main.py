"""
Main FastAPI application for Gauntlet Pipeline Orchestrator.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.config import get_settings

# Import routes
from app.routes import auth, generation, sessions, storage

settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Gauntlet Pipeline Orchestrator",
    description="Backend orchestrator for AI video generation pipeline",
    version="1.0.0",
    debug=settings.DEBUG
)


def custom_openapi():
    """
    Customize OpenAPI schema to explicitly show authentication requirements.

    This adds a security scheme that displays:
    - Lock icons on protected endpoints in Swagger UI
    - "Authorize" button to enter Bearer token
    - Clear indication of which endpoints require auth
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Define Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token from /api/auth/login or /api/auth/exchange"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get shared WebSocket manager from generation module
websocket_manager = generation.get_websocket_manager()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
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
