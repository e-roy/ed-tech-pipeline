"""
Agent 2 - Test Agent for Processing Pipeline

This is a scaffolding agent for testing the agent processing pipeline.
Functionality will be added between status states.
"""
import asyncio
import json
import logging
import re
import time
from typing import Optional, Callable, Awaitable
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
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
                sql_text(
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
                    "learning_objective": getattr(result, "learning_objective", None),
                    "child_age": getattr(result, "child_age", None),
                    "child_interest": getattr(result, "child_interest", None),
                }
            logger.info(f"Agent2 loaded video_session data for session {session_id}")
        except Exception as e:
            logger.error(f"Agent2 failed to query video_session: {e}")
            raise
    
    # Extract data from video_session if provided
    topic = None
    confirmed_facts = None
    generation_script = None
    learning_objective = None
    child_age = None
    child_interest = None
    generated_fields = []
    
    if video_session_data:
        topic = video_session_data.get("topic")
        confirmed_facts = video_session_data.get("confirmed_facts")
        generation_script = video_session_data.get("generated_script")
        learning_objective = video_session_data.get("learning_objective")
        child_age = video_session_data.get("child_age")
        child_interest = video_session_data.get("child_interest")
        
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
        # Use users/{userId}/{sessionId}/agent2/ path
        s3_key = f"users/{user_id}/{session_id}/agent2/{filename}"
        
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
                    s3_key = f"users/{user_id}/{session_id}/agent2/storyboard.json"
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
        
        # Generate base_scene with detailed characters and visual direction
        # Raise immediately and stop Agent2 if generation fails
        base_scene = None
        if script:
            base_scene = generate_base_scene(
                script=script,
                storyboard=storyboard,
                topic=topic,
                confirmed_facts=confirmed_facts,
                learning_objective=learning_objective,
                child_age=child_age,
                child_interest=child_interest
            )
            logger.info(f"Agent2 generated base_scene with style, setting, teacher, and students")
            
            # Validate base_scene has all required fields (empty strings are treated as valid)
            if not isinstance(base_scene, dict):
                raise ValueError(f"Agent2 base_scene generation failed: base_scene must be a dict, got {type(base_scene)}")
            
            required_fields = ["style", "setting", "teacher", "students"]
            missing_fields = [field for field in required_fields if field not in base_scene]
            if missing_fields:
                raise ValueError(f"Agent2 base_scene generation failed: missing required fields: {missing_fields}")
        
        # Create and upload agent_2_data.json with script and base_scene
        if script and storage_service.s3_client:
            try:
                # Ensure base_scene is always a dict (use empty dict if None, though this shouldn't happen after validation)
                agent_2_data = {
                    "script": script,
                    "storyboard": storyboard,
                    "base_scene": base_scene if isinstance(base_scene, dict) else {}
                }
                
                # Upload agent_2_data.json to S3
                s3_key = f"users/{user_id}/{session_id}/agent2/agent_2_data.json"
                agent_2_data_json = json.dumps(agent_2_data, indent=2).encode('utf-8')
                storage_service.s3_client.put_object(
                    Bucket=storage_service.bucket_name,
                    Key=s3_key,
                    Body=agent_2_data_json,
                    ContentType='application/json'
                )
                logger.info(f"Agent2 uploaded agent_2_data.json to S3: {s3_key}")
            except Exception as e:
                logger.error(f"Agent2 failed to upload agent_2_data.json: {e}", exc_info=True)
                # Don't fail the pipeline if agent_2_data.json upload fails

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


def generate_base_scene(
    script: dict,
    storyboard: Optional[dict] = None,
    topic: Optional[str] = None,
    confirmed_facts: Optional[list] = None,
    learning_objective: Optional[str] = None,
    child_age: Optional[str] = None,
    child_interest: Optional[str] = None
) -> dict:
    """
    Generate a base_scene object with detailed characters and visual direction.
    This provides consistency across all video clips generated by Agent5.
    
    Derives information from:
    - storyboard segments (visual_guidance, key_concepts)
    - video_session_data (topic, confirmed_facts, learning_objective, child_age, child_interest)
    - script (visual_prompt if available)
    
    Args:
        script: Dict with hook, concept, process, conclusion keys
        storyboard: Optional storyboard dict with segments
        topic: Optional topic string for context
        confirmed_facts: Optional list of confirmed facts
        learning_objective: Optional learning objective
        child_age: Optional child age (e.g., "6-7", "8-10", "11-12")
        child_interest: Optional child interest
        
    Returns:
        Dict with style, setting, teacher, and students as strings (as expected by Agent5)
    """
    # Style is always hardcoded
    style = "Pixar/Disney-quality 3D animation with soft subsurface scattering on skin, detailed fabric textures, realistic hair dynamics, warm depth of field blur on background, smooth CGI quality, kid-friendly educational aesthetic, consistent character rigs and models throughout all scenes"
    
    # Derive setting from multiple sources
    setting_parts = []
    
    # Validate storyboard structure
    if storyboard and not storyboard.get("segments"):
        raise ValueError("Storyboard exists but has no segments - cannot generate base_scene")
    
    # Extract visual guidance from storyboard segments (primary source)
    # Use all segments, fill missing visual_guidance with narration text and segment-type defaults
    visual_guidance_texts = []
    if storyboard and storyboard.get("segments"):
        segment_type_names = {
            "hook": "Hook",
            "concept_introduction": "Concept",
            "process_explanation": "Process",
            "conclusion": "Conclusion"
        }
        
        for segment in storyboard["segments"]:
            visual_guid = segment.get("visual_guidance", "")
            segment_type = segment.get("type", "")
            narration = segment.get("narration", "")
            
            # Get segment type name for separator
            segment_name = segment_type_names.get(segment_type, "Segment")
            
            if visual_guid and isinstance(visual_guid, str) and visual_guid.strip():
                visual_guidance_texts.append(f"{segment_name}: {visual_guid.strip()}")
            else:
                # Fill missing visual_guidance with narration text and segment-type default
                guidance_parts = []
                
                # Use narration text if available
                if narration and isinstance(narration, str) and narration.strip():
                    guidance_parts.append(narration.strip())
                
                # Add segment-type based default
                segment_defaults = {
                    "hook": "Engaging opening scene that captures attention",
                    "concept_introduction": "Clear visual introduction of the main concept",
                    "process_explanation": "Step-by-step visual explanation of the process",
                    "conclusion": "Summarizing visual that reinforces key points"
                }
                default_desc = segment_defaults.get(segment_type, "Educational scene appropriate for this segment")
                guidance_parts.append(default_desc)
                
                if guidance_parts:
                    combined_guidance = ". ".join(guidance_parts)
                    visual_guidance_texts.append(f"{segment_name}: {combined_guidance}")
    
    # Extract visual prompts from script (secondary source, still considered)
    visual_prompts = []
    for part_key in ["hook", "concept", "process", "conclusion"]:
        if part_key in script:
            part_data = script[part_key]
            if isinstance(part_data, dict):
                visual_prompt = part_data.get("visual_prompt", "")
                if visual_prompt and isinstance(visual_prompt, str) and visual_prompt.strip():
                    visual_prompts.append(visual_prompt.strip())
    
    # Combine visual guidance information (visual_guidance takes precedence but visual_prompt still considered)
    if visual_guidance_texts:
        # Primary: Use visual guidance from storyboard
        combined_visual = " ".join(visual_guidance_texts)
        # Secondary: Add visual prompts as additional context if available
        if visual_prompts:
            combined_visual += ". Additional visual context: " + " ".join(visual_prompts)
        setting_parts.append(combined_visual)
    elif visual_prompts:
        # Fallback: Use visual prompts from script if no visual guidance
        setting_parts.append(" ".join(visual_prompts))
    
    # Add topic-specific classroom elements
    classroom_base = "Bright modern elementary classroom with cream-colored walls and light blue trim along the bottom, light honey-colored wood floors with subtle grain, large floor-to-ceiling windows along left wall"
    
    # Enhance classroom based on topic and confirmed_facts
    topic_elements = []
    if topic:
        topic_lower = topic.lower()
        if "plant" in topic_lower or "photosynthesis" in topic_lower or "nature" in topic_lower:
            topic_elements.append("showing animated green oak trees and blue sky outside, potted green ferns on white windowsill, small fern plant on teacher's desk")
        elif "space" in topic_lower or "planet" in topic_lower or "astronomy" in topic_lower:
            topic_elements.append("showing animated starry sky and planets visible outside, space-themed posters on walls, model solar system hanging from ceiling")
        elif "animal" in topic_lower or "biology" in topic_lower:
            topic_elements.append("showing animated nature scene outside, animal posters on walls, small terrarium on windowsill")
        else:
            topic_elements.append("showing animated green oak trees and blue sky outside")
    
    def extract_text_from_value(value, depth=0, max_depth=3):
        """Recursively extract text from nested structures, with depth limit to avoid infinite loops."""
        if depth > max_depth:
            return []
        
        texts = []
        if isinstance(value, str):
            texts.append(value.lower())
        elif isinstance(value, dict):
            for v in value.values():
                texts.extend(extract_text_from_value(v, depth + 1, max_depth))
        elif isinstance(value, list):
            for item in value:
                texts.extend(extract_text_from_value(item, depth + 1, max_depth))
        return texts
    
    if confirmed_facts:
        # Extract key concepts from confirmed facts (handle various structures)
        # Use depth-limited recursion to avoid infinite loops
        concepts = []
        if isinstance(confirmed_facts, list):
            for fact in confirmed_facts:
                if isinstance(fact, dict):
                    # Try different possible keys
                    concept = fact.get("concept", "") or fact.get("name", "") or fact.get("title", "")
                    if concept:
                        concepts.append(str(concept).lower())
                    # Also check details field
                    details = fact.get("details", "") or fact.get("description", "") or fact.get("text", "")
                    if details:
                        concepts.append(str(details).lower())
                elif isinstance(fact, str):
                    concepts.append(fact.lower())
                else:
                    # Handle nested structures with depth limit
                    concepts.extend(extract_text_from_value(fact, max_depth=3))
        elif isinstance(confirmed_facts, dict):
            # Handle dict structure with depth limit
            concepts.extend(extract_text_from_value(confirmed_facts, max_depth=3))
        elif isinstance(confirmed_facts, str):
            concepts.append(confirmed_facts.lower())
        
        # Add relevant classroom decorations based on concepts (aggressive deduplication)
        plant_keywords = ["plant", "photo", "leaf", "tree", "fern", "flower", "garden"]
        space_keywords = ["space", "planet", "astronaut", "solar", "star", "galaxy", "moon"]
        animal_keywords = ["animal", "creature", "bird", "mammal", "fish", "insect", "reptile"]
        
        has_plant = any(any(kw in c for kw in plant_keywords) for c in concepts)
        has_space = any(any(kw in c for kw in space_keywords) for c in concepts)
        has_animal = any(any(kw in c for kw in animal_keywords) for c in concepts)
        
        # Check for duplicates more aggressively (check if similar content already exists)
        if has_plant:
            existing_plant = any(any(kw in e.lower() for kw in ["fern", "plant", "tree", "leaf", "flower"]) for e in topic_elements)
            if not existing_plant:
                topic_elements.append("potted green ferns on white windowsill")
        if has_space:
            existing_space = any(any(kw in e.lower() for kw in ["space", "planet", "solar", "star", "astronaut"]) for e in topic_elements)
            if not existing_space:
                topic_elements.append("space-themed educational posters")
        if has_animal:
            existing_animal = any(any(kw in e.lower() for kw in ["animal", "creature", "bird", "mammal"]) for e in topic_elements)
            if not existing_animal:
                topic_elements.append("animal posters on walls")
    
    if not topic_elements:
        topic_elements.append("showing animated green oak trees and blue sky outside")
    
    classroom_details = f"{classroom_base}, {', '.join(topic_elements)}, 8 small wooden student desks in 2 rows of 4 with light brown maple wood finish and blue plastic chairs, teacher's large wooden desk at front right with globe"
    
    if topic_elements and "space" not in " ".join(topic_elements).lower():
        classroom_details += " and small fern plant"
    
    classroom_details += ", colorful alphabet poster and periodic table on front wall, large world map above whiteboard, tall bookshelf with bright multicolored book spines against back wall, student artwork pinned to bulletin board on right wall"
    
    # Combine all setting information
    if setting_parts:
        visual_context = " ".join(setting_parts)
        setting = f"{classroom_details}. Visual context: {visual_context}"
    else:
        setting = classroom_details
    
    # Truncate setting to max 90 words, prioritizing classroom description
    setting_words = setting.split()
    if len(setting_words) > 90:
        # Count words in classroom_details
        classroom_words = classroom_details.split()
        classroom_word_count = len(classroom_words)
        
        # If classroom alone exceeds 90, truncate it
        if classroom_word_count > 90:
            setting = " ".join(classroom_words[:90]) + "..."
        else:
            # Preserve full classroom, truncate visual context
            remaining_words = 90 - classroom_word_count - 2  # Reserve 2 words for "Visual context:"
            if remaining_words > 0 and setting_parts:
                visual_context_words = visual_context.split()
                if len(visual_context_words) > remaining_words:
                    truncated_visual = " ".join(visual_context_words[:remaining_words]) + "..."
                    setting = f"{classroom_details}. Visual context: {truncated_visual}"
                else:
                    # Visual context fits, keep as is
                    setting = f"{classroom_details}. Visual context: {visual_context}"
            else:
                # No room for visual context, just use classroom
                setting = classroom_details
    
    # Derive child age and infer if not provided
    inferred_age = child_age
    if not inferred_age:
        # Try to infer from learning_objective first
        if learning_objective:
            learning_lower = learning_objective.lower()
            if "elementary" in learning_lower or "grade 1" in learning_lower or "grade 2" in learning_lower or "first grade" in learning_lower or "second grade" in learning_lower:
                inferred_age = "6-7"
            elif "grade 3" in learning_lower or "grade 4" in learning_lower or "third grade" in learning_lower or "fourth grade" in learning_lower:
                inferred_age = "8-10"
            elif "grade 5" in learning_lower or "grade 6" in learning_lower or "fifth grade" in learning_lower or "sixth grade" in learning_lower:
                inferred_age = "11-12"
            elif "preschool" in learning_lower or "pre-k" in learning_lower or "kindergarten" in learning_lower:
                inferred_age = "4-5"
            elif "middle school" in learning_lower or "grade 7" in learning_lower or "grade 8" in learning_lower:
                inferred_age = "12-14"
        
        # Try to infer from topic if still not found
        if not inferred_age and topic:
            topic_lower = topic.lower()
            # Look for age-related keywords in topic
            if "preschool" in topic_lower or "kindergarten" in topic_lower:
                inferred_age = "4-5"
            elif "elementary" in topic_lower:
                inferred_age = "8-10"
            elif "middle school" in topic_lower:
                inferred_age = "12-14"
        
        # Try to infer from confirmed_facts if still not found
        if not inferred_age and confirmed_facts:
            facts_text = ""
            if isinstance(confirmed_facts, list):
                for fact in confirmed_facts:
                    if isinstance(fact, dict):
                        facts_text += " " + str(fact.get("concept", "")) + " " + str(fact.get("details", ""))
                    elif isinstance(fact, str):
                        facts_text += " " + fact
            elif isinstance(confirmed_facts, str):
                facts_text = confirmed_facts
            
            facts_lower = facts_text.lower()
            if "preschool" in facts_lower or "kindergarten" in facts_lower:
                inferred_age = "4-5"
            elif "elementary" in facts_lower or "grade 1" in facts_lower or "grade 2" in facts_lower:
                inferred_age = "6-7"
            elif "grade 3" in facts_lower or "grade 4" in facts_lower:
                inferred_age = "8-10"
            elif "grade 5" in facts_lower or "grade 6" in facts_lower:
                inferred_age = "11-12"
            elif "middle school" in facts_lower:
                inferred_age = "12-14"
        
        # Default to middle elementary if can't infer
        if not inferred_age:
            inferred_age = "8-10"
    
    # Parse age range (handle various formats: "6-7", "6 to 7", "ages 6-7", "6-7 years", "6", "6+", "under 6", etc.)
    # Take first pair if multiple pairs found
    age_min = None
    age_max = None
    
    # Look for age range patterns first (e.g., "6-7", "6 to 7", "ages 6-7")
    age_range_pattern = re.search(r'(\d+)\s*[-_to]\s*(\d+)', str(inferred_age), re.IGNORECASE)
    if age_range_pattern:
        age_min = int(age_range_pattern.group(1))
        age_max = int(age_range_pattern.group(2))
    else:
        # Extract all numbers from age string
        age_numbers = re.findall(r'\d+', str(inferred_age))
        
        if age_numbers:
            age_min = int(age_numbers[0])
            if len(age_numbers) > 1:
                # Multiple numbers but not in range format - take first pair
                age_max = int(age_numbers[1])
            else:
                # Single number - check for modifiers
                inferred_lower = str(inferred_age).lower()
                if "+" in inferred_lower or "and up" in inferred_lower or "up" in inferred_lower:
                    age_max = 12  # Assume up to 12 for "6+"
                elif "under" in inferred_lower or "below" in inferred_lower or "less than" in inferred_lower:
                    age_max = age_min
                    age_min = max(4, age_min - 2)  # Assume 2 years below
                else:
                    age_max = age_min  # Single age, use as both min and max
    
    # Calculate average age
    if age_min is not None and age_max is not None:
        avg_age = (age_min + age_max) // 2
    else:
        # Default if parsing fails
        avg_age = 8
    
    # Generate teacher description based on age
    if avg_age <= 7:
        teacher = "Ms. Rivera, animated woman in early 30s, warm medium tan skin tone, shoulder-length dark brown hair in neat ponytail with side-swept bangs, warm brown eyes with expressive eyebrows, friendly smile showing white teeth, average height with professional build, animated in signature Pixar character style, light sky blue cardigan sweater over crisp white button-up shirt, dark navy blue dress pants, comfortable tan flat shoes, small silver stud earrings, enthusiastic hand gestures when teaching, expressive animated eyebrows, warm and encouraging smile, uses open palm gestures, stands with confident posture, moves smoothly around classroom, uses simple clear language appropriate for young learners"
    elif avg_age <= 10:
        teacher = "Ms. Rivera, animated woman in early 30s, warm medium tan skin tone, shoulder-length dark brown hair in neat ponytail with side-swept bangs, warm brown eyes with expressive eyebrows, friendly smile showing white teeth, average height with professional build, animated in signature Pixar character style, light sky blue cardigan sweater over crisp white button-up shirt, dark navy blue dress pants, comfortable tan flat shoes, small silver stud earrings, enthusiastic hand gestures when teaching, expressive animated eyebrows, warm and encouraging smile, uses open palm gestures, stands with confident posture, moves smoothly around classroom"
    else:
        teacher = "Ms. Rivera, animated woman in early 30s, warm medium tan skin tone, shoulder-length dark brown hair in neat ponytail with side-swept bangs, warm brown eyes with expressive eyebrows, friendly smile showing white teeth, average height with professional build, animated in signature Pixar character style, light sky blue cardigan sweater over crisp white button-up shirt, dark navy blue dress pants, comfortable tan flat shoes, small silver stud earrings, confident teaching style with clear explanations, expressive animated eyebrows, warm and encouraging smile, uses open palm gestures, stands with confident posture, moves smoothly around classroom, engages students with thought-provoking questions"
    
    # Generate students description based on age and interest
    if avg_age <= 5:
        age_desc = f"{avg_age}-year-old"
        student_count = 6
        engagement = "wide-eyed wonder, eager to learn, sitting in small colorful chairs"
    elif avg_age <= 7:
        age_desc = f"{avg_age}-year-old"
        student_count = 6
        engagement = "wide-eyed wonder, eager to learn, sitting in small colorful chairs"
    elif avg_age <= 10:
        age_desc = f"{avg_age}-year-old"
        student_count = 8
        engagement = "engaged and attentive expressions, seated in semi-circle facing teacher"
    elif avg_age <= 12:
        age_desc = f"{avg_age}-year-old"
        student_count = 8
        engagement = "thoughtful and engaged expressions, taking notes, seated in organized rows facing teacher"
    else:
        age_desc = f"{avg_age}-year-old"
        student_count = 8
        engagement = "thoughtful and engaged expressions, taking detailed notes, seated in organized rows facing teacher"
    
    # Build student descriptions with interest-based details (combine multiple interests)
    # Best practice: Split on common delimiters (and, &, comma, or) and detect each interest separately
    interest_elements = []
    if child_interest:
        # Split on common delimiters to handle "science and art" or "music, sports"
        interest_parts = re.split(r'\s+and\s+|\s*&\s*|\s*,\s*|\s+or\s+', str(child_interest), flags=re.IGNORECASE)
        
        # Check each part for interests
        for interest_part in interest_parts:
            interest_lower = interest_part.strip().lower()
            if not interest_lower:
                continue
                
            # Check for multiple interests and combine them
            if "science" in interest_lower or "experiment" in interest_lower:
                if not any("science" in elem for elem in interest_elements):
                    interest_elements.append("wearing science-themed t-shirts with beakers or atoms")
            if "art" in interest_lower or "draw" in interest_lower or "painting" in interest_lower:
                if not any("art" in elem for elem in interest_elements):
                    interest_elements.append("with colorful art supplies visible on desks")
            if "sport" in interest_lower or "athletic" in interest_lower or "soccer" in interest_lower or "basketball" in interest_lower or "football" in interest_lower:
                if not any("athletic" in elem or "sport" in elem for elem in interest_elements):
                    interest_elements.append("wearing athletic wear or sports-themed clothing")
            if "music" in interest_lower or "sing" in interest_lower or "instrument" in interest_lower:
                if not any("music" in elem for elem in interest_elements):
                    interest_elements.append("with musical instruments or music notes visible")
            if "animal" in interest_lower or "nature" in interest_lower or "pet" in interest_lower:
                if not any("animal" in elem or "nature" in elem for elem in interest_elements):
                    interest_elements.append("wearing animal-themed clothing or nature-inspired accessories")
            if "space" in interest_lower or "astronaut" in interest_lower or "planet" in interest_lower:
                if not any("space" in elem for elem in interest_elements):
                    interest_elements.append("with space-themed accessories or rocket designs")
            if "reading" in interest_lower or "book" in interest_lower or "story" in interest_lower:
                if not any("book" in elem for elem in interest_elements):
                    interest_elements.append("with books visible on desks")
    
    students_base = f"{student_count} diverse animated {age_desc} children with signature Pixar big expressive eyes and stylized features, various skin tones and hairstyles, all wearing casual school clothes (t-shirts, jeans, dresses)"
    
    if interest_elements:
        students_base += f", {', '.join(interest_elements)}"
    
    students_base += f", {engagement}"
    
    # Add key student characters (age-appropriate)
    if avg_age <= 5:
        key_students = [
            "Maya (girl with round glasses and black hair in two braids, light brown skin, green t-shirt with flower design, eager and raises hand often)",
            "Oliver (boy with curly bright orange-red hair, pale skin with freckles, blue and white striped polo shirt, curious expression)"
        ]
    elif avg_age <= 7:
        key_students = [
            "Maya (girl with round glasses and black hair in two braids, light brown skin, green t-shirt with flower design, eager and raises hand often)",
            "Oliver (boy with curly bright orange-red hair, pale skin with freckles, blue and white striped polo shirt, curious expression)",
            "Sofia (girl with long blonde hair in ponytail, light skin, purple dress with white collar, thoughtful and takes notes)"
        ]
    elif avg_age <= 10:
        key_students = [
            "Maya (girl with round glasses and black hair in two braids, light brown skin, green t-shirt with flower design, eager and raises hand often)",
            "Oliver (boy with curly bright orange-red hair, pale skin with freckles, blue and white striped polo shirt, curious expression)",
            "Sofia (girl with long blonde hair in ponytail, light skin, purple dress with white collar, thoughtful and takes notes)",
            "James (boy with short black hair and darker skin, bright yellow t-shirt, wide smile and excited demeanor)",
            "Aisha (girl with brown skin and natural curly black hair in puffs, pink hoodie, asks questions)",
            "Ethan (boy with straight brown hair, medium skin, red sweater, focused and concentrating)"
        ]
    else:
        key_students = [
            "Maya (girl with round glasses and black hair in two braids, light brown skin, green t-shirt, focused and takes detailed notes)",
            "Oliver (boy with curly bright orange-red hair, pale skin with freckles, blue polo shirt, analytical expression)",
            "Sofia (girl with long blonde hair in ponytail, light skin, purple cardigan, thoughtful and asks insightful questions)",
            "James (boy with short black hair and darker skin, bright yellow t-shirt, engaged and participates actively)",
            "Aisha (girl with brown skin and natural curly black hair, pink hoodie, asks thoughtful questions)",
            "Ethan (boy with straight brown hair, medium skin, red sweater, focused and concentrating)"
        ]
    
    students = f"{students_base}. Key students include: {', '.join(key_students)}"
    
    base_scene = {
        "style": style,
        "setting": setting,
        "teacher": teacher,
        "students": students
    }
    
    return base_scene

