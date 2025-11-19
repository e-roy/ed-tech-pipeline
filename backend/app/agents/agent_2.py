"""
Agent 2 - Test Agent for Processing Pipeline

This is a scaffolding agent for testing the agent processing pipeline.
Functionality will be added between status states.
"""
import asyncio
import json
import secrets
import time
from typing import Optional
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService


async def agent_2_process(
    websocket_manager: WebSocketManager,
    user_id: str,
    session_id: str,
    template_id: str,
    chosen_diagram_id: str,
    script_id: str,
    storage_service: Optional[StorageService] = None
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
        storage_service: Storage service for S3 operations
    """
    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()
    
    # Generate supersessionid: original_session_id + 16 character random string
    random_suffix = secrets.token_urlsafe(12)[:16]  # Generate 16 char random string
    supersessionid = f"{session_id}_{random_suffix}"
    
    # Helper function to create JSON status file in S3
    async def create_status_json(agent_number: str, status: str, status_data: dict):
        """Create a JSON file in S3 with status data."""
        if not storage_service.s3_client:
            return  # Skip if storage not configured
        
        timestamp = int(time.time() * 1000)  # Milliseconds timestamp
        filename = f"agent_{agent_number}_{status}_{timestamp}.json"
        s3_key = f"scaffold_test/{user_id}/{supersessionid}/{filename}"
        
        try:
            json_content = json.dumps(status_data, indent=2).encode('utf-8')
            storage_service.s3_client.put_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key,
                Body=json_content,
                ContentType='application/json'
            )
        except Exception as e:
            # Log but don't fail the pipeline if JSON creation fails
            print(f"Failed to create status JSON file: {e}")
    
    try:
        # Report starting status
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "starting",
            "timestamp": int(time.time() * 1000)
        }
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("2", "starting", status_data)
        
        # Wait 2 seconds
        await asyncio.sleep(2)
        
        # TODO: Add initialization/preparation logic here
        
        # Report processing status
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "processing",
            "timestamp": int(time.time() * 1000)
        }
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("2", "processing", status_data)
        
        # Wait 2 seconds
        await asyncio.sleep(2)
        
        # TODO: Add main agent work here (e.g., image generation, processing)
        
        # Report finished status
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "finished",
            "timestamp": int(time.time() * 1000)
        }
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("2", "finished", status_data)
        
        # TODO: Add cleanup/finalization logic here
        
        # Trigger Agent4 with userID, sessionID, and supersessionid
        from app.agents.agent_4 import agent_4_process
        await agent_4_process(websocket_manager, user_id, session_id, supersessionid, storage_service)
        
    except Exception as e:
        # Report error status and stop pipeline
        error_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "error",
            "error": str(e),
            "reason": f"Agent2 failed: {type(e).__name__}",
            "timestamp": int(time.time() * 1000)
        }
        await websocket_manager.send_progress(session_id, error_data)
        await create_status_json("2", "error", error_data)
        raise  # Stop pipeline on error

