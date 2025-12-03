"""
Agent 3 - Script Processing and Base Scene Generation

Processes video session data and generates JSON output for video generation.

Outputs agent_3_data.json containing:
  - storyboard: Segment timing, narration, visual guidance, and visual_scene for each section
  - base_scene: Visual consistency settings (style, setting, teacher, students)
"""
import json
import logging
import os
import time
from typing import Optional, Callable, Awaitable, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from openai import AsyncOpenAI
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService
from app.config import get_settings

logger = logging.getLogger(__name__)

# Segment type mapping
SEGMENT_TYPES = {
    "hook": "hook",
    "concept": "concept_introduction",
    "process": "process_explanation",
    "conclusion": "conclusion"
}


async def agent_3_process(
    websocket_manager: Optional[WebSocketManager],
    user_id: str,
    session_id: str,
    storage_service: Optional[StorageService] = None,
    video_session_data: Optional[dict] = None,
    db: Optional[Session] = None,
    status_callback: Optional[Callable[[str, str, str, str, int], Awaitable[None]]] = None
) -> Dict[str, Any]:
    """Process video session data and generate script, storyboard, and base scene."""
    if storage_service is None:
        storage_service = StorageService()

    async def send_status(status: str, **kwargs):
        timestamp = int(time.time() * 1000)
        if status_callback:
            await status_callback(
                agentnumber="Agent3", status=status, userID=user_id,
                sessionID=session_id, timestamp=timestamp, **kwargs
            )
        elif websocket_manager:
            await websocket_manager.send_progress(session_id, {
                "agentnumber": "Agent3", "userID": user_id, "sessionID": session_id,
                "status": status, "timestamp": timestamp, **kwargs
            })

    try:
        logger.info(f"Agent3 starting for session {session_id}")
        await send_status("starting")

        # Load video session data
        data = await _load_video_session_data(db, user_id, session_id, video_session_data)

        await send_status("processing", message="Extracting script...")

        # Extract script
        script = _extract_script(data.get("generated_script"))
        if not script:
            raise ValueError(f"No valid script found for session {session_id}")
        logger.info(f"Agent3 extracted script with sections: {list(script.keys())}")

        # Create storyboard
        storyboard = _create_storyboard(script)
        logger.info(f"Agent3 created storyboard with {len(storyboard['segments'])} segments")

        # Generate visual_scene for each segment (for image generation)
        await send_status("processing", message="Generating visual scenes...")
        storyboard = await _generate_visual_scenes(
            storyboard=storyboard,
            topic=data.get("topic"),
            child_interest=data.get("child_interest")
        )
        logger.info("Agent3 generated visual_scene for storyboard segments")

        # Generate base scene (for video generation)
        await send_status("processing", message="Generating base scene...")
        base_scene = await _generate_base_scene(
            topic=data.get("topic"),
            child_age=data.get("child_age"),
            child_interest=data.get("child_interest"),
            confirmed_facts=data.get("confirmed_facts"),
            learning_objective=data.get("learning_objective")
        )
        logger.info("Agent3 generated base_scene")

        # Upload to S3 (storyboard contains all script data in segments)
        agent_3_data = {"storyboard": storyboard, "base_scene": base_scene}
        if storage_service.s3_client:
            s3_key = f"users/{user_id}/{session_id}/agent3/agent_3_data.json"
            storage_service.s3_client.put_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key,
                Body=json.dumps(agent_3_data, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Agent3 uploaded to S3: {s3_key}")

        await send_status("finished", message="Script processing complete")
        return {"status": "success", "storyboard": storyboard,
                "base_scene": base_scene, "agent_3_data": agent_3_data}

    except Exception as e:
        logger.error(f"Agent3 failed for session {session_id}: {e}", exc_info=True)
        await send_status("error", error=str(e), reason=f"Agent3 failed: {type(e).__name__}")
        raise


async def _load_video_session_data(
    db: Optional[Session], user_id: str, session_id: str, fallback_data: Optional[dict]
) -> dict:
    """Load video session data from database or use fallback."""
    if db is not None:
        try:
            result = db.execute(
                sql_text("SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"),
                {"session_id": session_id, "user_id": user_id}
            ).fetchone()
            if not result:
                raise ValueError(f"Video session not found: {session_id}")
            return dict(result._mapping)
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            if fallback_data:
                return fallback_data
            raise

    if fallback_data:
        return fallback_data
    raise ValueError("Agent3 requires either db session or video_session_data")


def _extract_script(generated_script: Optional[dict]) -> Optional[dict]:
    """Extract script from generated_script field."""
    if not generated_script or not isinstance(generated_script, dict):
        return None

    # Format 1: Direct keys {"hook": {...}, "concept": {...}, ...}
    if "hook" in generated_script:
        return {k: generated_script.get(k, {}) for k in ["hook", "concept", "process", "conclusion"]}

    # Format 2: Nested {"script": {...}}
    if "script" in generated_script and isinstance(generated_script["script"], dict):
        nested = generated_script["script"]
        if "hook" in nested:
            return nested

    # Format 3: Segments array {"segments": [{type: "hook"}, ...]}
    if "segments" in generated_script and isinstance(generated_script["segments"], list):
        segments = generated_script["segments"]
        script = {}
        type_to_key = {
            "hook": "hook",
            "concept_introduction": "concept",
            "process_explanation": "process",
            "conclusion": "conclusion"
        }
        for seg in segments:
            if isinstance(seg, dict) and seg.get("type") in type_to_key:
                key = type_to_key[seg["type"]]
                script[key] = {
                    "text": seg.get("narration", ""),
                    "narration": seg.get("narration", ""),
                    "visual_guidance": seg.get("visual_guidance", ""),
                    "key_concepts": seg.get("key_concepts", []),
                    "educational_purpose": seg.get("educational_purpose", ""),
                    "duration": seg.get("duration")
                }
        if all(k in script for k in ["hook", "concept", "process", "conclusion"]):
            return script

    return None


def _create_storyboard(script: dict) -> dict:
    """Create storyboard with segment timing from script."""
    segments = []
    start_time = 0
    key_concepts_count = 0

    for idx, (script_key, segment_type) in enumerate(SEGMENT_TYPES.items(), start=1):
        part = script.get(script_key, {})

        # Get narration text
        narration = ""
        if isinstance(part, dict):
            narration = part.get("text") or part.get("narration") or ""
        elif isinstance(part, str):
            narration = part

        if not narration:
            continue

        # Get duration from source script
        duration = 15  # default
        if isinstance(part, dict) and part.get("duration"):
            try:
                duration = int(part["duration"])
            except (ValueError, TypeError):
                pass

        # Get other fields from script or use defaults
        visual_guidance = part.get("visual_guidance", "") if isinstance(part, dict) else ""
        key_concepts = part.get("key_concepts", []) if isinstance(part, dict) else []
        if isinstance(key_concepts, str):
            key_concepts = [key_concepts]
        key_concepts_count += len(key_concepts)

        segments.append({
            "id": f"seg_{idx:03d}",
            "type": segment_type,
            "duration": duration,
            "start_time": start_time,
            "narration": narration,
            "visual_guidance": visual_guidance or f"Visual for {script_key}",
            "key_concepts": key_concepts,
            "educational_purpose": part.get("educational_purpose", "") if isinstance(part, dict) else ""
        })
        start_time += duration

    return {
        "segments": segments,
        "total_duration": sum(s["duration"] for s in segments),
        "reading_level": "6.5",
        "key_terms_count": key_concepts_count
    }


async def _generate_base_scene(
    topic: Optional[str] = None,
    child_age: Optional[str] = None,
    child_interest: Optional[str] = None,
    confirmed_facts: Optional[list] = None,
    learning_objective: Optional[str] = None
) -> dict:
    """Generate base scene using OpenAI or fallback to static values."""
    client = _get_openai_client()
    if not client:
        return _get_fallback_base_scene()

    # Handle confirmed_facts - could be list of strings or list of dicts
    facts_text = "general educational content"
    if confirmed_facts:
        if isinstance(confirmed_facts[0], str):
            facts_text = ", ".join(confirmed_facts)
        elif isinstance(confirmed_facts[0], dict):
            # Extract fact text from dicts (handle various key names)
            facts_text = ", ".join(
                f.get("fact") or f.get("text") or f.get("content") or str(f)
                for f in confirmed_facts
            )

    prompt = f"""Generate a base scene for a Pixar/Disney-style educational video.

Topic: {topic or "general education"}
Target age: {child_age or "8-10 years old"}
Child's interests: {child_interest or "learning"}
Key facts: {facts_text}
Learning objective: {learning_objective or "educational engagement"}

Return JSON with:
- style: Animation style (Pixar/Disney 3D, lighting, colors) ~60 words
- setting: Environment description (location, decorations, furniture) ~80 words
- teacher: Teacher character (name, appearance, clothing, personality) ~80 words
- students: Student characters (count, diversity, named students, engagement) ~100 words"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        base_scene = json.loads(response.choices[0].message.content)
        logger.info(f"Generated base_scene via OpenAI")
        return base_scene
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        return _get_fallback_base_scene()


def _get_openai_client() -> Optional[AsyncOpenAI]:
    """Get OpenAI client."""
    settings = get_settings()
    api_key = None

    if settings.USE_AWS_SECRETS:
        try:
            from app.services.secrets import get_secret
            api_key = get_secret("pipeline/openai-api-key")
        except Exception:
            pass

    if not api_key:
        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")

    return AsyncOpenAI(api_key=api_key) if api_key else None


def _get_fallback_base_scene() -> dict:
    """Static fallback base scene."""
    return {
        "style": "Pixar/Disney-quality 3D animation with soft lighting, warm colors, detailed textures, kid-friendly aesthetic, consistent character designs",
        "setting": "Bright modern classroom with cream walls, wood floors, large windows, student desks, teacher's desk with globe, colorful posters, bookshelf",
        "teacher": "Ms. Rivera, early 30s, warm tan skin, dark brown ponytail, brown eyes, friendly smile, sky blue cardigan, white shirt, navy pants, encouraging manner",
        "students": "8 diverse animated children with expressive eyes, various appearances, casual clothes, engaged and attentive. Key students: Maya (glasses, braids), Oliver (curly orange hair), Sofia (blonde ponytail), James (short black hair)"
    }


async def _generate_visual_scenes(
    storyboard: dict,
    topic: Optional[str] = None,
    child_interest: Optional[str] = None
) -> dict:
    """Generate visual_scene objects for each storyboard segment using LLM.

    Args:
        storyboard: Storyboard dict with segments
        topic: Video topic for context
        child_interest: Child's interest for thematic elements

    Returns:
        Updated storyboard with visual_scene added to each segment
    """
    client = _get_openai_client()
    if not client:
        logger.warning("No OpenAI client available, using fallback visual scenes")
        return _add_fallback_visual_scenes(storyboard)

    segments = storyboard.get("segments", [])
    if not segments:
        return storyboard

    # Build context for the LLM
    segments_context = []
    for seg in segments:
        segments_context.append({
            "type": seg.get("type"),
            "narration": seg.get("narration", "")[:200],
            "visual_guidance": seg.get("visual_guidance", ""),
            "key_concepts": seg.get("key_concepts", [])
        })

    prompt = f"""Generate detailed visual scene descriptions for AI image generation.

Topic: {topic or "educational content"}
Child's interest: {child_interest or "learning"}

For each segment below, create a visual_scene object optimized for AI image generation.
The visual_scene should translate the abstract visual_guidance into concrete, renderable scene details.

IMPORTANT RULES FOR AI IMAGE GENERATION:
- Avoid requesting text, labels, captions, or writing in the scene
- Avoid split screens or multiple panels - describe ONE cohesive scene
- Avoid abstract concepts - describe concrete, visible elements
- Avoid transitions or animations - describe a single moment in time

Segments:
{json.dumps(segments_context, indent=2)}

Return JSON with this exact structure:
{{
  "visual_scenes": [
    {{
      "segment_type": "hook",
      "visual_scene": {{
        "description": "Main scene description - what the viewer sees (2-3 sentences)",
        "composition": "How elements are arranged in frame (foreground, background, focal point)",
        "lighting": "Lighting style and mood (warm, cool, dramatic, soft, etc.)",
        "camera_angle": "Camera perspective (wide shot, close-up, eye level, bird's eye, etc.)",
        "key_elements": ["list", "of", "must-have", "visual", "objects"],
        "mood": "Emotional tone of the scene (exciting, calm, mysterious, etc.)",
        "color_palette": ["primary", "colors", "to", "use"]
      }}
    }}
  ]
}}

Generate visual_scene for each of the {len(segments)} segments in order."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        visual_scenes = result.get("visual_scenes", [])

        # Map visual_scenes back to segments by type
        scene_by_type = {vs.get("segment_type"): vs.get("visual_scene") for vs in visual_scenes}

        for seg in segments:
            seg_type = seg.get("type")
            if seg_type in scene_by_type:
                seg["visual_scene"] = scene_by_type[seg_type]
            else:
                # Fallback for missing segments
                seg["visual_scene"] = _get_fallback_visual_scene(seg)

        logger.info(f"Generated visual_scene for {len(visual_scenes)} segments via OpenAI")
        return storyboard

    except Exception as e:
        logger.error(f"OpenAI visual_scene generation failed: {e}")
        return _add_fallback_visual_scenes(storyboard)


def _add_fallback_visual_scenes(storyboard: dict) -> dict:
    """Add fallback visual_scene to each segment when LLM is unavailable."""
    for seg in storyboard.get("segments", []):
        seg["visual_scene"] = _get_fallback_visual_scene(seg)
    return storyboard


def _get_fallback_visual_scene(segment: dict) -> dict:
    """Generate a basic fallback visual_scene from segment data."""
    visual_guidance = segment.get("visual_guidance", "")
    key_concepts = segment.get("key_concepts", [])

    return {
        "description": visual_guidance or f"Educational scene about {', '.join(key_concepts) if key_concepts else 'the topic'}",
        "composition": "centered subject with supportive background elements",
        "lighting": "warm, inviting studio lighting",
        "camera_angle": "eye level medium shot",
        "key_elements": key_concepts[:5] if key_concepts else ["educational content"],
        "mood": "engaging and educational",
        "color_palette": ["blue", "green", "warm yellow", "white"]
    }
