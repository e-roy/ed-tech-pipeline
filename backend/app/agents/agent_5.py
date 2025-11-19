"""
Agent 5 - Test Agent for Processing Pipeline

This is a scaffolding agent for testing the agent processing pipeline.
Functionality will be added between status states.
"""
import asyncio
from app.services.websocket_manager import WebSocketManager


async def agent_5_process(
    websocket_manager: WebSocketManager,
    user_id: str,
    session_id: str
):
    """
    Agent5: Third and final agent in the processing pipeline.
    
    This is scaffolding - functionality will be added between status states.
    
    Args:
        websocket_manager: WebSocket manager for status updates
        user_id: User identifier
        session_id: Session identifier
    """
    try:
        # Report starting status
        await websocket_manager.send_progress(session_id, {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "status": "starting"
        })
        
        # Wait 5 seconds
        await asyncio.sleep(5)
        
        # TODO: Add initialization/preparation logic here
        
        # Report processing status
        await websocket_manager.send_progress(session_id, {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "status": "processing"
        })
        
        # Wait 5 seconds
        await asyncio.sleep(5)
        
        # TODO: Add main agent work here (e.g., final processing, output generation)
        
        # Report finished status
        await websocket_manager.send_progress(session_id, {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "status": "finished"
        })
        
        # TODO: Add cleanup/finalization logic here
        
    except Exception as e:
        # Report error status and stop pipeline
        await websocket_manager.send_progress(session_id, {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "status": "error",
            "error": str(e),
            "reason": f"Agent5 failed: {type(e).__name__}"
        })
        raise  # Stop pipeline on error

