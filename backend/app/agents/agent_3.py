"""
Agent 3 - Script Processing and Base Scene Generation

A cleaner, simplified version of Agent 2 that processes video session data
and generates the JSON output needed by Agent 5 for video generation.

Outputs:
- agent_3_data.json containing:
  - script: Extracted script with hook, concept, process, conclusion sections
  - storyboard: Segment timing and visual guidance
  - base_scene: Visual consistency settings (style, setting, teacher, students)
"""
import asyncio
import json
import logging
import re
import time
from typing import Optional, Callable, Awaitable, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


async def agent_3_process(
    websocket_manager: Optional[WebSocketManager],
    user_id: str,
    session_id: str,
    storage_service: Optional[StorageService] = None,
    video_session_data: Optional[dict] = None,
    db: Optional[Session] = None,
    status_callback: Optional[Callable[[str, str, str, str, int], Awaitable[None]]] = None
) -> Dict[str, Any]:
    """
    Agent 3: Script processing and base scene generation.

    Queries video_session table for script data, creates storyboard with timing,
    and generates base_scene for visual consistency across all video clips.

    Args:
        websocket_manager: WebSocket manager for status updates (deprecated, use status_callback)
        user_id: User identifier
        session_id: Session identifier
        storage_service: Storage service for S3 operations
        video_session_data: Optional dict with video_session row data (fallback if db unavailable)
        db: Database session for querying video_session table
        status_callback: Callback function for sending status updates to orchestrator

    Returns:
        Dict with status, script, storyboard, and base_scene

    Raises:
        ValueError: If script is missing or incomplete
    """
    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()

    # Helper function to send status updates
    async def send_status(status: str, **kwargs):
        """Send status update via callback or websocket_manager."""
        timestamp = int(time.time() * 1000)

        if status_callback:
            await status_callback(
                agentnumber="Agent3",
                status=status,
                userID=user_id,
                sessionID=session_id,
                timestamp=timestamp,
                **kwargs
            )
        elif websocket_manager:
            status_data = {
                "agentnumber": "Agent3",
                "userID": user_id,
                "sessionID": session_id,
                "status": status,
                "timestamp": timestamp,
                **kwargs
            }
            await websocket_manager.send_progress(session_id, status_data)

    try:
        logger.info(f"Agent3 starting for session {session_id}")
        await send_status("starting")

        # ===================
        # STEP 1: Load video_session data
        # ===================
        video_session_data = await _load_video_session_data(
            db, user_id, session_id, video_session_data
        )

        topic = video_session_data.get("topic")
        confirmed_facts = video_session_data.get("confirmed_facts")
        generated_script = video_session_data.get("generated_script")
        learning_objective = video_session_data.get("learning_objective")
        child_age = video_session_data.get("child_age")
        child_interest = video_session_data.get("child_interest")

        await send_status("processing", message="Extracting script from video session...")

        # ===================
        # STEP 2: Extract and validate script
        # ===================
        script = _extract_script(generated_script)

        if not script:
            raise ValueError(
                f"Agent3 cannot proceed without a valid script. "
                f"Session {session_id} has missing or incomplete generated_script."
            )

        logger.info(f"Agent3 extracted script with sections: {list(script.keys())}")

        # ===================
        # STEP 3: Create storyboard with timing
        # ===================
        storyboard = _create_storyboard(script, topic)
        logger.info(f"Agent3 created storyboard with {len(storyboard.get('segments', []))} segments")

        # ===================
        # STEP 4: Generate base_scene for visual consistency
        # ===================
        base_scene = _generate_base_scene(
            script=script,
            storyboard=storyboard,
            topic=topic,
            confirmed_facts=confirmed_facts,
            learning_objective=learning_objective,
            child_age=child_age,
            child_interest=child_interest
        )
        logger.info(f"Agent3 generated base_scene with style, setting, teacher, students")

        # ===================
        # STEP 5: Upload agent_3_data.json to S3
        # ===================
        agent_3_data = {
            "script": script,
            "storyboard": storyboard,
            "base_scene": base_scene
        }

        if storage_service.s3_client:
            s3_key = f"users/{user_id}/{session_id}/agent3/agent_3_data.json"
            agent_3_data_json = json.dumps(agent_3_data, indent=2).encode('utf-8')
            storage_service.s3_client.put_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key,
                Body=agent_3_data_json,
                ContentType='application/json'
            )
            logger.info(f"Agent3 uploaded agent_3_data.json to S3: {s3_key}")

        await send_status("finished", message="Script processing complete")

        return {
            "status": "success",
            "script": script,
            "storyboard": storyboard,
            "base_scene": base_scene,
            "agent_3_data": agent_3_data
        }

    except Exception as e:
        logger.error(f"Agent3 failed for session {session_id}: {e}", exc_info=True)
        await send_status("error", error=str(e), reason=f"Agent3 failed: {type(e).__name__}")
        raise


async def _load_video_session_data(
    db: Optional[Session],
    user_id: str,
    session_id: str,
    fallback_data: Optional[dict]
) -> dict:
    """Load video_session data from database or use fallback."""

    if db is not None:
        try:
            logger.info(f"Agent3 querying video_session for session_id={session_id}")
            result = db.execute(
                sql_text(
                    "SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"
                ),
                {"session_id": session_id, "user_id": user_id},
            ).fetchone()

            if not result:
                raise ValueError(f"Video session not found: session_id={session_id}, user_id={user_id}")

            if hasattr(result, "_mapping"):
                return dict(result._mapping)
            else:
                return {
                    "id": getattr(result, "id", None),
                    "user_id": getattr(result, "user_id", None),
                    "topic": getattr(result, "topic", None),
                    "confirmed_facts": getattr(result, "confirmed_facts", None),
                    "generated_script": getattr(result, "generated_script", None),
                    "learning_objective": getattr(result, "learning_objective", None),
                    "child_age": getattr(result, "child_age", None),
                    "child_interest": getattr(result, "child_interest", None),
                }
        except Exception as e:
            logger.error(f"Agent3 database query failed: {e}")
            if fallback_data:
                logger.warning("Agent3 using fallback video_session_data")
                return fallback_data
            raise

    if fallback_data:
        return fallback_data

    raise ValueError("Agent3 requires either db session or video_session_data")


def _extract_script(generated_script: Optional[dict]) -> Optional[dict]:
    """
    Extract script structure from generated_script JSONB field.

    Handles formats:
    - Direct: {"hook": {...}, "concept": {...}, ...}
    - Nested: {"script": {"hook": {...}, ...}}
    - Segments array: {"segments": [{...}, {...}, ...]}

    Returns:
        Dict with hook, concept, process, conclusion keys, or None if invalid
    """
    if not generated_script or not isinstance(generated_script, dict):
        return None

    script_parts = {}

    # Format 1: Direct keys
    if "hook" in generated_script:
        script_parts = {
            "hook": generated_script.get("hook", {}),
            "concept": generated_script.get("concept", {}),
            "process": generated_script.get("process", {}),
            "conclusion": generated_script.get("conclusion", {})
        }
    # Format 2: Nested under "script" key
    elif "script" in generated_script and isinstance(generated_script["script"], dict):
        script_parts = generated_script["script"]
    # Format 3: Segments array
    elif "segments" in generated_script:
        segments = generated_script["segments"]
        if isinstance(segments, list) and len(segments) >= 4:
            script_parts = {
                "hook": segments[0] if isinstance(segments[0], dict) else {},
                "concept": segments[1] if isinstance(segments[1], dict) else {},
                "process": segments[2] if isinstance(segments[2], dict) else {},
                "conclusion": segments[3] if isinstance(segments[3], dict) else {}
            }

    # Validate all required parts exist
    required_keys = ["hook", "concept", "process", "conclusion"]
    if script_parts and all(key in script_parts for key in required_keys):
        return script_parts

    return None


def _create_storyboard(script: dict, topic: Optional[str] = None) -> dict:
    """
    Create storyboard with segment timing and visual guidance.

    Args:
        script: Dict with hook, concept, process, conclusion keys
        topic: Optional topic for context

    Returns:
        Dict with segments, reading_level, total_duration, key_terms_count
    """
    segments = []
    start_time = 0
    all_key_concepts = set()

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

        # Extract narration text
        narration = ""
        if isinstance(part_data, dict):
            narration = (
                part_data.get("text") or
                part_data.get("narration") or
                part_data.get("narrationtext") or
                ""
            )
        elif isinstance(part_data, str):
            narration = part_data

        if not narration:
            continue

        # Calculate duration from word count (150 wpm)
        words = len(narration.split())
        duration = max(1, round((words / 150) * 60))

        # Extract key concepts
        key_concepts = []
        if isinstance(part_data, dict):
            key_concepts = part_data.get("key_concepts", []) or []
            if isinstance(key_concepts, str):
                key_concepts = [key_concepts]

        all_key_concepts.update(c for c in key_concepts if c)

        # Get visual guidance
        visual_guidance = ""
        if isinstance(part_data, dict):
            visual_guidance = (
                part_data.get("visual_guidance") or
                part_data.get("visual_guidance_preview") or
                ""
            )

        # Default visual guidance if missing
        if not visual_guidance:
            defaults = {
                "hook": "Engaging opening scene that captures attention",
                "concept_introduction": "Clear visual introduction of the main concept",
                "process_explanation": "Step-by-step visual explanation of the process",
                "conclusion": "Summarizing visual that reinforces key points"
            }
            visual_guidance = defaults.get(segment_type, "Educational scene")

        # Get educational purpose
        educational_purpose = ""
        if isinstance(part_data, dict):
            educational_purpose = part_data.get("educational_purpose", "")

        if not educational_purpose:
            purpose_defaults = {
                "hook": "Engage the audience by highlighting the importance of the topic.",
                "concept_introduction": "Introduce key vocabulary and the basic concept.",
                "process_explanation": "Explain how the process works and its significance.",
                "conclusion": "Summarize the importance and broader context."
            }
            educational_purpose = purpose_defaults.get(segment_type, "Educational content.")

        segments.append({
            "id": f"seg_{idx:03d}",
            "type": segment_type,
            "duration": duration,
            "narration": narration,
            "start_time": start_time,
            "key_concepts": key_concepts,
            "visual_guidance": visual_guidance,
            "educational_purpose": educational_purpose
        })

        start_time += duration

    return {
        "segments": segments,
        "reading_level": "6.5",
        "total_duration": sum(seg["duration"] for seg in segments),
        "key_terms_count": len(all_key_concepts)
    }


def _generate_base_scene(
    script: dict,
    storyboard: Optional[dict] = None,
    topic: Optional[str] = None,
    confirmed_facts: Optional[list] = None,
    learning_objective: Optional[str] = None,
    child_age: Optional[str] = None,
    child_interest: Optional[str] = None
) -> dict:
    """
    Generate base_scene for visual consistency across all video clips.

    Returns:
        Dict with style, setting, teacher, students as strings
    """
    # Style is always consistent (Pixar/Disney quality)
    style = (
        "Pixar/Disney-quality 3D animation with soft subsurface scattering on skin, "
        "detailed fabric textures, realistic hair dynamics, warm depth of field blur "
        "on background, smooth CGI quality, kid-friendly educational aesthetic, "
        "consistent character rigs and models throughout all scenes"
    )

    # Build setting from classroom base + topic-specific elements
    setting = _build_setting(storyboard, script, topic, confirmed_facts)

    # Infer age if not provided
    avg_age = _infer_age(child_age, learning_objective, topic, confirmed_facts)

    # Generate teacher description (age-adaptive)
    teacher = _generate_teacher_description(avg_age)

    # Generate students description (age and interest-adaptive)
    students = _generate_students_description(avg_age, child_interest)

    return {
        "style": style,
        "setting": setting,
        "teacher": teacher,
        "students": students
    }


def _build_setting(
    storyboard: Optional[dict],
    script: dict,
    topic: Optional[str],
    confirmed_facts: Optional[list]
) -> str:
    """Build setting description from visual guidance and topic."""

    # Base classroom description
    classroom = (
        "Bright modern elementary classroom with cream-colored walls and light blue trim, "
        "light honey-colored wood floors, large windows along left wall"
    )

    # Add topic-specific decorations
    topic_elements = []
    if topic:
        topic_lower = topic.lower()
        if any(kw in topic_lower for kw in ["plant", "photosynthesis", "nature"]):
            topic_elements.append("potted green ferns on windowsill, trees visible outside")
        elif any(kw in topic_lower for kw in ["space", "planet", "astronomy"]):
            topic_elements.append("space posters on walls, model solar system")
        elif any(kw in topic_lower for kw in ["animal", "biology"]):
            topic_elements.append("animal posters on walls, terrarium on shelf")
        else:
            topic_elements.append("trees and blue sky visible outside")

    if not topic_elements:
        topic_elements.append("trees and blue sky visible outside")

    # Standard classroom furniture
    furniture = (
        "8 small wooden student desks in 2 rows, teacher's desk at front with globe, "
        "colorful alphabet poster on wall, tall bookshelf with multicolored books"
    )

    setting = f"{classroom}, {', '.join(topic_elements)}, {furniture}"

    # Truncate to max 90 words
    words = setting.split()
    if len(words) > 90:
        setting = " ".join(words[:90]) + "..."

    return setting


def _infer_age(
    child_age: Optional[str],
    learning_objective: Optional[str],
    topic: Optional[str],
    confirmed_facts: Optional[list]
) -> int:
    """Infer average age from available data. Returns integer age."""

    if child_age:
        # Parse age range (e.g., "6-7", "8-10", "6+")
        match = re.search(r'(\d+)\s*[-_to]\s*(\d+)', str(child_age), re.IGNORECASE)
        if match:
            return (int(match.group(1)) + int(match.group(2))) // 2

        numbers = re.findall(r'\d+', str(child_age))
        if numbers:
            return int(numbers[0])

    # Infer from learning_objective
    if learning_objective:
        lo_lower = learning_objective.lower()
        if "preschool" in lo_lower or "kindergarten" in lo_lower:
            return 5
        if "grade 1" in lo_lower or "grade 2" in lo_lower:
            return 7
        if "grade 3" in lo_lower or "grade 4" in lo_lower:
            return 9
        if "grade 5" in lo_lower or "grade 6" in lo_lower:
            return 11
        if "middle school" in lo_lower:
            return 13

    # Default to middle elementary
    return 9


def _generate_teacher_description(avg_age: int) -> str:
    """Generate teacher description based on student age."""

    base = (
        "Ms. Rivera, animated woman in early 30s, warm medium tan skin tone, "
        "shoulder-length dark brown hair in neat ponytail with side-swept bangs, "
        "warm brown eyes with expressive eyebrows, friendly smile, "
        "light sky blue cardigan over white button-up shirt, "
        "dark navy blue dress pants, tan flat shoes"
    )

    if avg_age <= 7:
        style = (
            "enthusiastic hand gestures, warm encouraging smile, "
            "uses simple clear language appropriate for young learners"
        )
    elif avg_age <= 10:
        style = (
            "expressive animated eyebrows, warm encouraging smile, "
            "confident posture, moves smoothly around classroom"
        )
    else:
        style = (
            "confident teaching style with clear explanations, "
            "engages students with thought-provoking questions"
        )

    return f"{base}, {style}"


def _generate_students_description(avg_age: int, child_interest: Optional[str]) -> str:
    """Generate students description based on age and interests."""

    # Age-based settings
    if avg_age <= 7:
        count = 6
        age_desc = f"{avg_age}-year-old"
        engagement = "wide-eyed wonder, eager to learn, sitting in small colorful chairs"
    elif avg_age <= 10:
        count = 8
        age_desc = f"{avg_age}-year-old"
        engagement = "engaged and attentive, seated in semi-circle facing teacher"
    else:
        count = 8
        age_desc = f"{avg_age}-year-old"
        engagement = "thoughtful expressions, taking notes, seated in organized rows"

    base = (
        f"{count} diverse animated {age_desc} children with signature Pixar "
        f"big expressive eyes, various skin tones and hairstyles, "
        f"casual school clothes (t-shirts, jeans, dresses)"
    )

    # Add interest-based elements
    interest_elements = []
    if child_interest:
        interest_lower = child_interest.lower()
        if "science" in interest_lower:
            interest_elements.append("science-themed t-shirts")
        if "art" in interest_lower:
            interest_elements.append("colorful art supplies on desks")
        if "sport" in interest_lower:
            interest_elements.append("athletic wear")
        if "music" in interest_lower:
            interest_elements.append("musical instruments visible")
        if "space" in interest_lower:
            interest_elements.append("space-themed accessories")

    if interest_elements:
        base += f", {', '.join(interest_elements)}"

    base += f", {engagement}"

    # Key students
    key_students = [
        "Maya (girl with glasses and black braids, green t-shirt)",
        "Oliver (boy with curly orange hair, blue striped polo)",
        "Sofia (girl with blonde ponytail, purple dress)"
    ]

    if avg_age > 7:
        key_students.extend([
            "James (boy with short black hair, yellow t-shirt)",
            "Aisha (girl with natural curly black hair, pink hoodie)",
            "Ethan (boy with brown hair, red sweater)"
        ])

    return f"{base}. Key students: {', '.join(key_students)}"
