"""
Agent 2 - Test Agent for Processing Pipeline

This is a scaffolding agent for testing the agent processing pipeline.
Functionality will be added between status states.
"""
import asyncio
import json
import logging
import secrets
import time
from typing import Optional
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


async def agent_2_process(
    websocket_manager: WebSocketManager,
    user_id: str,
    session_id: str,
    template_id: str,
    chosen_diagram_id: str,
    script_id: str,
    storage_service: Optional[StorageService] = None,
    video_session_data: Optional[dict] = None
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
        video_session_data: Optional dict with video_session row data (for Full Test mode)
    """
    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()
    
    # Generate supersessionid: original_session_id + 16 character random string
    random_suffix = secrets.token_urlsafe(12)[:16]  # Generate 16 char random string
    supersessionid = f"{session_id}_{random_suffix}"
    
    # Extract data from video_session if provided
    topic = None
    confirmed_facts = None
    generation_script = None
    generated_fields = []
    
    if video_session_data:
        topic = video_session_data.get("topic")
        confirmed_facts = video_session_data.get("confirmed_facts")
        generation_script = video_session_data.get("generated_script")
        
        # Track what needs to be generated
        if not topic:
            generated_fields.append("topic")
            topic = f"Generated topic for session {session_id}"
        if not confirmed_facts:
            generated_fields.append("confirmed_facts")
            confirmed_facts = [{"concept": "Example concept", "details": "Example details"}]
        if not generation_script:
            generated_fields.append("generation_script")
            generation_script = {}
    
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
        logger.info(f"Agent2 starting for session {session_id}, supersessionid: {supersessionid}")
        
        # Report starting status
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "starting",
            "timestamp": int(time.time() * 1000)
        }
        logger.info(f"Agent2 sending starting status for session {session_id}")
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("2", "starting", status_data)
        logger.info(f"Agent2 starting status sent for session {session_id}")
        
        # Wait 2 seconds
        await asyncio.sleep(2)
        
        # TODO: Add initialization/preparation logic here
        
        # Extract script from generation_script or generate it
        script = extract_script_from_generated_script(generation_script)
        script_was_generated = False
        
        if not script or not all(key in script for key in ["hook", "concept", "process", "conclusion"]):
            # Generate script if missing or incomplete
            script_was_generated = True
            if video_session_data and "generation_script" not in generated_fields:
                generated_fields.append("generation_script")
            script = generate_script_structure()
        
        # Report processing status
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "processing",
            "timestamp": int(time.time() * 1000)
        }
        
        # Include video_session data in WebSocket messages ONLY when video_session_data is provided
        if video_session_data:
            status_data["topic"] = topic
            status_data["confirmed_facts"] = confirmed_facts
            status_data["generation_script"] = generation_script
            if generated_fields:
                status_data["generated_fields"] = generated_fields
        
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("2", "processing", status_data)
        
        # Wait 2 seconds
        await asyncio.sleep(2)

        # TODO: Add main agent work here (e.g., storyboard generation)

        # Report finished status
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "finished",
            "timestamp": int(time.time() * 1000)
        }
        
        # Include video_session data in WebSocket messages ONLY when video_session_data is provided
        if video_session_data:
            status_data["topic"] = topic
            status_data["confirmed_facts"] = confirmed_facts
            status_data["generation_script"] = generation_script
            if generated_fields:
                status_data["generated_fields"] = generated_fields
        
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("2", "finished", status_data)
        
        # TODO: Add cleanup/finalization logic here

        # Trigger Agent4 with script, voice, audio_option (matching Agent4's current signature)
        # Remove agent2_data (deprecated - Agent4 is more specific for its needs)
        from app.agents.agent_4 import agent_4_process
        await agent_4_process(
            websocket_manager=websocket_manager,
            user_id=user_id,
            session_id=session_id,
            supersessionid=supersessionid,
            script=script,
            voice="alloy",
            audio_option="tts",
            storage_service=storage_service,
            agent2_data=None  # Deprecated
        )
        
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


def extract_script_from_generated_script(generated_script: Optional[dict]) -> Optional[dict]:
    """
    Extract script structure from generated_script JSONB field.
    Handles different formats: direct hook/concept/process/conclusion, nested under "script", or "segments" array.
    
    Returns:
        Dict with hook, concept, process, conclusion keys, or None if not found
    """
    if not generated_script or not isinstance(generated_script, dict):
        return None
    
    script_parts = {}
    
    # Check if it has hook/concept/process/conclusion directly
    if "hook" in generated_script:
        script_parts = {
            "hook": generated_script.get("hook", {}),
            "concept": generated_script.get("concept", {}),
            "process": generated_script.get("process", {}),
            "conclusion": generated_script.get("conclusion", {})
        }
    # Check if it's nested under "script" key
    elif "script" in generated_script and isinstance(generated_script["script"], dict):
        script_parts = generated_script["script"]
    # Check if it has segments (alternative format)
    elif "segments" in generated_script:
        segments = generated_script["segments"]
        if isinstance(segments, list) and len(segments) >= 4:
            script_parts = {
                "hook": segments[0] if isinstance(segments[0], dict) else {},
                "concept": segments[1] if isinstance(segments[1], dict) else {},
                "process": segments[2] if isinstance(segments[2], dict) else {},
                "conclusion": segments[3] if isinstance(segments[3], dict) else {}
            }
    
    # Validate that we have all required parts
    if script_parts and all(key in script_parts for key in ["hook", "concept", "process", "conclusion"]):
        return script_parts
    
    return None


def generate_script_structure() -> dict:
    """
    Generate a placeholder script structure with hook, concept, process, conclusion.
    
    Returns:
        Dict with hook, concept, process, conclusion parts
    """
    return {
        "hook": {
            "text": "Have you ever wondered how technology is changing the way we work?",
            "duration": "10",
            "key_concepts": [],
            "visual_guidance": "Visual guidance for hook"
        },
        "concept": {
            "text": "Automation and AI are revolutionizing industries by streamlining processes and enhancing productivity.",
            "duration": "15",
            "key_concepts": [],
            "visual_guidance": "Visual guidance for concept"
        },
        "process": {
            "text": "From data analysis to customer service, these technologies learn from patterns and make intelligent decisions. They help businesses save time, reduce errors, and focus on what matters most.",
            "duration": "22",
            "key_concepts": [],
            "visual_guidance": "Visual guidance for process"
        },
        "conclusion": {
            "text": "Embrace the future of work. Start exploring how AI can transform your workflow today!",
            "duration": "10",
            "key_concepts": [],
            "visual_guidance": "Visual guidance for conclusion"
        }
    }

