"""
Agent 2 - Test Agent for Processing Pipeline

This is a scaffolding agent for testing the agent processing pipeline.
Functionality will be added between status states.
"""
import asyncio
from typing import Optional
from app.services.websocket_manager import WebSocketManager


async def agent_2_process(
    websocket_manager: WebSocketManager,
    user_id: str,
    session_id: str,
    template_id: str,
    chosen_diagram_id: str,
    script_id: str
):
    """
    Agent2: First agent in the processing pipeline.
    
    This is scaffolding - functionality will be added between status states.
    
    Args:
        websocket_manager: WebSocket manager for status updates
        user_id: User identifier
        session_id: Session identifier
        template_id: Template identifier
        chosen_diagram_id: Chosen diagram identifier
        script_id: Script identifier
    """
    try:
        # Report starting status
        await websocket_manager.send_progress(session_id, {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "status": "starting"
        })
        
        # Wait 2 seconds
        await asyncio.sleep(2)
        
        # TODO: Add initialization/preparation logic here
        
        # Report processing status
        await websocket_manager.send_progress(session_id, {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "status": "processing"
        })
        
        # Wait 2 seconds
        await asyncio.sleep(2)
        
        # TODO: Add main agent work here (e.g., image generation, processing)
        
        # Report finished status
        await websocket_manager.send_progress(session_id, {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "status": "finished"
        })
        
        # TODO: Add cleanup/finalization logic here
        
        # Trigger Agent4 with userID and sessionID
        from app.agents.agent_4 import agent_4_process
        await agent_4_process(websocket_manager, user_id, session_id)
        
    except Exception as e:
        # Report error status and stop pipeline
        await websocket_manager.send_progress(session_id, {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "status": "error",
            "error": str(e),
            "reason": f"Agent2 failed: {type(e).__name__}"
        })
        raise  # Stop pipeline on error

