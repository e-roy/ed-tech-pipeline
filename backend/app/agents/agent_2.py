"""
Agent 2 - Test Agent for Processing Pipeline

This is a scaffolding agent for testing the agent processing pipeline.
Functionality will be added between status states.
"""
import asyncio
import json
import logging
import time
from typing import Optional, Callable, Awaitable
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


async def agent_2_process(
    websocket_manager: Optional[WebSocketManager],
    user_id: str,
    session_id: str,
    template_id: str,
    chosen_diagram_id: str,
    script_id: str,
    storage_service: Optional[StorageService] = None,
    video_session_data: Optional[dict] = None,
    db: Optional[Session] = None,
    status_callback: Optional[Callable[[str, str, str, str, int], Awaitable[None]]] = None
):
    """
    Agent2: First agent in the processing pipeline.
    
    This is scaffolding - functionality will be added between status states.
    
    Args:
        websocket_manager: WebSocket manager for status updates (deprecated, use status_callback)
        user_id: User identifier
        session_id: Session identifier
        template_id: Template identifier
        chosen_diagram_id: Chosen diagram identifier
        script_id: Script identifier
        storage_service: Storage service for S3 operations
        video_session_data: Optional dict with video_session row data (for Full Test mode)
        db: Database session for querying video_session table
        status_callback: Callback function for sending status updates to orchestrator
    """
    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()
    
    # Query video_session table if db is provided
    if db is not None:
        try:
            result = db.execute(
                text(
                    "SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"
                ),
                {"session_id": session_id, "user_id": user_id},
            ).fetchone()
            
            if not result:
                raise ValueError(f"Video session not found for session_id={session_id} and user_id={user_id}")
            
            # Convert result to dict
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
            logger.info(f"Agent2 loaded video_session data for session {session_id}")
        except Exception as e:
            logger.error(f"Agent2 failed to query video_session: {e}")
            raise
    
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
    
    # Helper function to send status (via callback or websocket_manager)
    async def send_status(agentnumber: str, status: str, **kwargs):
        """Send status update via callback or websocket_manager."""
        timestamp = int(time.time() * 1000)
        
        if status_callback:
            # Use callback (preferred - goes through orchestrator)
            await status_callback(
                agentnumber=agentnumber,
                status=status,
                userID=user_id,
                sessionID=session_id,
                timestamp=timestamp,
                **kwargs
            )
        elif websocket_manager:
            # Fallback to direct websocket (for backwards compatibility)
            status_data = {
                "agentnumber": agentnumber,
                "userID": user_id,
                "sessionID": session_id,
                "status": status,
                "timestamp": timestamp,
                **kwargs
            }
            await websocket_manager.send_progress(session_id, status_data)
    
    # Helper function to create JSON status file in S3
    async def create_status_json(agent_number: str, status: str, status_data: dict):
        """Create a JSON file in S3 with status data."""
        if not storage_service.s3_client:
            return  # Skip if storage not configured
        
        timestamp = int(time.time() * 1000)  # Milliseconds timestamp
        filename = f"agent_{agent_number}_{status}_{timestamp}.json"
        # Use scaffold_test/{userId}/{sessionId}/agent2/ path
        s3_key = f"scaffold_test/{user_id}/{session_id}/agent2/{filename}"
        
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
            logger.warning(f"Failed to create status JSON file: {e}")
    
    try:
        logger.info(f"Agent2 starting for session {session_id}")
        
        # Report starting status
        logger.info(f"Agent2 sending starting status for session {session_id}")
        await send_status("Agent2", "starting")
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "status": "starting",
            "timestamp": int(time.time() * 1000)
        }
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
        processing_kwargs = {}
        # Include video_session data in status messages ONLY when video_session_data is provided
        if video_session_data:
            processing_kwargs["topic"] = topic
            processing_kwargs["confirmed_facts"] = confirmed_facts
            processing_kwargs["generation_script"] = generation_script
            if generated_fields:
                processing_kwargs["generated_fields"] = generated_fields
        
        await send_status("Agent2", "processing", **processing_kwargs)
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "status": "processing",
            "timestamp": int(time.time() * 1000),
            **processing_kwargs
        }
        await create_status_json("2", "processing", status_data)
        
        # Wait 2 seconds
        await asyncio.sleep(2)

        # Generate storyboard.json from script data
        storyboard = None
        if script:
            try:
                storyboard = create_storyboard_from_script(script, topic)
                logger.info(f"Agent2 generated storyboard with {len(storyboard.get('segments', []))} segments")
                
                # Upload storyboard.json to S3
                if storage_service.s3_client:
                    s3_key = f"scaffold_test/{user_id}/{session_id}/agent2/storyboard.json"
                    storyboard_json = json.dumps(storyboard, indent=2).encode('utf-8')
                    storage_service.s3_client.put_object(
                        Bucket=storage_service.bucket_name,
                        Key=s3_key,
                        Body=storyboard_json,
                        ContentType='application/json'
                    )
                    logger.info(f"Agent2 uploaded storyboard.json to S3: {s3_key}")
                else:
                    logger.warning("Storage service not configured, skipping storyboard.json upload")
            except Exception as e:
                logger.error(f"Agent2 failed to generate/upload storyboard.json: {e}", exc_info=True)
                # Don't fail the pipeline if storyboard generation fails

        # Report finished status
        finished_kwargs = {}
        # Include video_session data in status messages ONLY when video_session_data is provided
        if video_session_data:
            finished_kwargs["topic"] = topic
            finished_kwargs["confirmed_facts"] = confirmed_facts
            finished_kwargs["generation_script"] = generation_script
            if generated_fields:
                finished_kwargs["generated_fields"] = generated_fields
        
        await send_status("Agent2", "finished", **finished_kwargs)
        status_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "status": "finished",
            "timestamp": int(time.time() * 1000),
            **finished_kwargs
        }
        await create_status_json("2", "finished", status_data)
        
        # TODO: Add cleanup/finalization logic here
        
        # Return completion status for orchestrator
        return {
            "status": "success",
            "script": script,
            "storyboard": storyboard,
            "video_session_data": video_session_data
        }
        
    except Exception as e:
        # Report error status and stop pipeline
        error_kwargs = {
            "error": str(e),
            "reason": f"Agent2 failed: {type(e).__name__}"
        }
        await send_status("Agent2", "error", **error_kwargs)
        error_data = {
            "agentnumber": "Agent2",
            "userID": user_id,
            "sessionID": session_id,
            "status": "error",
            "timestamp": int(time.time() * 1000),
            **error_kwargs
        }
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


def calculate_duration_from_words(narration: str) -> int:
    """
    Calculate duration in seconds based on word count.
    Assumes ~150 words per minute speaking rate.
    
    Args:
        narration: The narration text
        
    Returns:
        Duration in seconds (rounded to nearest integer)
    """
    if not narration:
        return 0
    words = len(narration.split())
    # 150 words per minute = 2.5 words per second
    duration = round((words / 150) * 60)
    return max(1, duration)  # Minimum 1 second


def create_storyboard_from_script(script: dict, topic: Optional[str] = None) -> dict:
    """
    Create a storyboard.json structure from script data.
    
    Args:
        script: Dict with hook, concept, process, conclusion keys
        topic: Optional topic string for context
        
    Returns:
        Dict with storyboard structure including segments, reading_level, total_duration, key_terms_count
    """
    segments = []
    start_time = 0
    all_key_concepts = set()
    
    # Map script parts to segment types
    segment_mapping = [
        ("hook", "hook"),
        ("concept", "concept_introduction"),
        ("process", "process_explanation"),
        ("conclusion", "conclusion")
    ]
    
    for idx, (script_key, segment_type) in enumerate(segment_mapping, start=1):
        if script_key not in script:
            continue
            
        part_data = script[script_key]
        
        # Get narration text (could be "text", "narration", or nested)
        narration = ""
        if isinstance(part_data, dict):
            narration = part_data.get("text") or part_data.get("narration") or part_data.get("narrationtext") or ""
        elif isinstance(part_data, str):
            narration = part_data
        
        if not narration:
            continue
        
        # Calculate duration from word count
        duration = calculate_duration_from_words(narration)
        
        # Get key concepts
        key_concepts = []
        if isinstance(part_data, dict):
            key_concepts = part_data.get("key_concepts", []) or []
            if isinstance(key_concepts, str):
                key_concepts = [key_concepts]
        
        # Add to all_key_concepts set
        for concept in key_concepts:
            if concept:
                all_key_concepts.add(concept)
        
        # Get visual guidance
        visual_guidance = ""
        if isinstance(part_data, dict):
            visual_guidance = part_data.get("visual_guidance") or part_data.get("visual_guidance_preview") or ""
        
        # Get educational purpose (if available, otherwise generate default)
        educational_purpose = ""
        if isinstance(part_data, dict):
            educational_purpose = part_data.get("educational_purpose") or ""
        
        if not educational_purpose:
            # Generate default educational purpose based on segment type
            purpose_map = {
                "hook": "Engage the audience by highlighting the importance or relevance of the topic.",
                "concept_introduction": "Introduce key vocabulary and the basic concept.",
                "process_explanation": "Explain how the process works and its significance.",
                "conclusion": "Summarize the importance and its role in the broader context."
            }
            educational_purpose = purpose_map.get(segment_type, "Educational content for this segment.")
        
        segment = {
            "id": f"seg_{idx:03d}",
            "type": segment_type,
            "duration": duration,
            "narration": narration,
            "start_time": start_time,
            "key_concepts": key_concepts,
            "visual_guidance": visual_guidance,
            "educational_purpose": educational_purpose
        }
        
        segments.append(segment)
        start_time += duration
    
    # Calculate total duration
    total_duration = sum(seg.get("duration", 0) for seg in segments)
    
    # Calculate reading level (default to 6.5 if not available)
    reading_level = "6.5"  # Could be calculated from text complexity in the future
    
    # Count unique key terms
    key_terms_count = len(all_key_concepts)
    
    storyboard = {
        "segments": segments,
        "reading_level": reading_level,
        "total_duration": total_duration,
        "key_terms_count": key_terms_count
    }
    
    return storyboard


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

