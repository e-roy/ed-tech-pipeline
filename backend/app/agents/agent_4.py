"""
Agent 4 - Audio Pipeline Agent

This agent generates TTS audio from script text using OpenAI's TTS API.
It receives a script with hook, concept, process, and conclusion parts,
generates audio for each.

Called via orchestrator in Full Test mode.
"""
import json
import time
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService
from app.agents.audio_pipeline import AudioPipelineAgent
from app.agents.base import AgentInput

logger = logging.getLogger(__name__)

REQUIRED_SCRIPT_PARTS = ["hook", "concept", "process", "conclusion"]


def _extract_script_from_generated_script(generated_script: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
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
        script_parts = {key: generated_script.get(key, {}) for key in REQUIRED_SCRIPT_PARTS}
    # Check if it's nested under "script" key
    elif "script" in generated_script and isinstance(generated_script["script"], dict):
        script_parts = generated_script["script"]
    # Check if it has segments (alternative format)
    elif "segments" in generated_script:
        segments = generated_script["segments"]
        if isinstance(segments, list) and len(segments) >= 4:
            script_parts = {
                key: segments[i] if isinstance(segments[i], dict) else {}
                for i, key in enumerate(REQUIRED_SCRIPT_PARTS)
            }

    # Validate that we have all required parts
    if script_parts and all(key in script_parts for key in REQUIRED_SCRIPT_PARTS):
        return script_parts

    return None


def _normalize_script(script: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize script format: convert 'narration' field to 'text' field if needed."""
    normalized_script = {}
    for part_name in REQUIRED_SCRIPT_PARTS:
        part_data = script.get(part_name, {})
        if isinstance(part_data, dict):
            normalized_part = dict(part_data)
            if "text" not in normalized_part and "narration" in normalized_part:
                normalized_part["text"] = normalized_part["narration"]
            normalized_script[part_name] = normalized_part
        else:
            normalized_script[part_name] = part_data
    return normalized_script


async def _upload_audio_to_s3(
    storage_service: StorageService,
    filepath: str,
    s3_key: str
) -> str:
    """Upload audio file to S3 and return presigned URL."""
    with open(filepath, "rb") as f:
        storage_service.s3_client.put_object(
            Bucket=storage_service.bucket_name,
            Key=s3_key,
            Body=f.read(),
            ContentType='audio/mpeg'
        )
    return storage_service.generate_presigned_url(s3_key, expires_in=86400)


async def agent_4_process(
    websocket_manager: Optional[WebSocketManager],
    user_id: str,
    session_id: str,
    script: Dict[str, Any],
    voice: str = "alloy",
    audio_option: str = "tts",
    storage_service: Optional[StorageService] = None,
    agent2_data: Optional[Dict[str, Any]] = None,
    video_session_data: Optional[dict] = None,
    db: Optional[Session] = None,
    status_callback: Optional[Callable[[str, str, str, str, int], Awaitable[None]]] = None
) -> Dict[str, Any]:
    """
    Agent4: Audio Pipeline - generates TTS audio from script.

    Args:
        websocket_manager: WebSocket manager for status updates (deprecated, use status_callback)
        user_id: User identifier
        session_id: Session identifier
        script: Script with hook, concept, process, conclusion parts
        voice: TTS voice to use (default: alloy)
        audio_option: Audio generation option (tts, upload, none, instrumental)
        storage_service: Storage service for S3 operations
        agent2_data: Data passed from Agent2 (deprecated, unused)
        video_session_data: Optional dict with video_session row data (for Full Test mode)
        db: Database session for querying video_session table
        status_callback: Callback function for sending status updates to orchestrator

    Returns:
        Dict with audio generation results
    """
    storage_service = storage_service or StorageService()

    # Helper to build status data
    def _build_status_data(status: str, **extra_kwargs) -> dict:
        return {
            "agentnumber": "Agent4",
            "userID": user_id,
            "sessionID": session_id,
            "status": status,
            "timestamp": int(time.time() * 1000),
            **extra_kwargs
        }

    # Helper to send status updates
    async def send_status(status: str, **kwargs):
        """Send status update via callback or websocket_manager."""
        status_data = _build_status_data(status, **kwargs)

        if status_callback:
            await status_callback(
                agentnumber="Agent4",
                status=status,
                userID=user_id,
                sessionID=session_id,
                timestamp=status_data["timestamp"],
                **kwargs
            )
        elif websocket_manager:
            await websocket_manager.send_progress(session_id, status_data)

        # Create JSON status file in S3
        if storage_service.s3_client:
            try:
                s3_key = f"users/{user_id}/{session_id}/agent4/agent_4_{status}_{status_data['timestamp']}.json"
                storage_service.s3_client.put_object(
                    Bucket=storage_service.bucket_name,
                    Key=s3_key,
                    Body=json.dumps(status_data, indent=2).encode('utf-8'),
                    ContentType='application/json'
                )
            except Exception as e:
                logger.warning(f"Failed to create status JSON file: {e}")

    try:
        # Query video_session table if db is provided
        if db is not None:
            try:
                logger.info(f"Agent4 querying video_session for session_id={session_id}")
                result = db.execute(
                    sql_text("SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"),
                    {"session_id": session_id, "user_id": user_id},
                ).fetchone()

                if not result:
                    raise ValueError(f"Video session not found for session_id={session_id} and user_id={user_id}")

                video_session_data = dict(result._mapping) if hasattr(result, "_mapping") else {
                    "generated_script": getattr(result, "generated_script", None)
                }
                logger.info(f"Agent4 loaded video_session data for session {session_id}")
            except Exception as e:
                logger.error(f"Agent4 failed to query video_session table: {e}")
                if video_session_data is None:
                    raise
                logger.warning(f"Agent4 falling back to provided video_session_data")

        if video_session_data is None:
            raise ValueError(f"Agent4 requires either db session or video_session_data for session {session_id}")

        # Extract script from generation_script if not provided
        if not script:
            generation_script = video_session_data.get("generated_script")
            if generation_script:
                logger.info(f"Agent4 extracting script from generated_script")
                script = _extract_script_from_generated_script(generation_script)
                if script:
                    logger.info(f"Agent4 extracted script successfully")

        # Validate script
        if not script:
            raise ValueError(
                f"Agent4 could not find script. "
                f"Script must be created by frontend and stored in video_session.generated_script before calling orchestrator. "
                f"Session: {session_id}"
            )

        missing_parts = [p for p in REQUIRED_SCRIPT_PARTS if p not in script]
        if missing_parts:
            raise ValueError(
                f"Agent4 script is missing required parts: {', '.join(missing_parts)}. "
                f"Script must have all parts: {', '.join(REQUIRED_SCRIPT_PARTS)}"
            )

        # Report starting status
        await send_status("starting")
        logger.info(f"Agent4 starting audio generation for session {session_id}")

        # Report processing status
        await send_status("processing")

        # Get OpenAI API key from AWS Secrets Manager
        try:
            from app.services.secrets import get_secret
            openai_key = get_secret("pipeline/openai-api-key")
            logger.debug(f"Retrieved OPENAI_API_KEY from AWS Secrets Manager")
        except Exception as e:
            logger.warning(f"Could not retrieve OPENAI_API_KEY from Secrets Manager: {e}")
            openai_key = None

        # Create AudioPipelineAgent
        audio_agent = AudioPipelineAgent(
            api_key=openai_key,
            db=None,
            storage_service=storage_service,
            websocket_manager=websocket_manager
        )

        # Normalize script format
        normalized_script = _normalize_script(script)

        # Log validation
        logger.info(f"Agent4 normalized script - checking text fields")
        for part_name in REQUIRED_SCRIPT_PARTS:
            part_text = normalized_script.get(part_name, {}).get("text", "")
            if not part_text:
                logger.warning(f"Agent4: Part '{part_name}' has no text - audio generation may fail")

        # Process audio generation
        agent_input = AgentInput(
            session_id=session_id,
            data={
                "script": normalized_script,
                "voice": voice,
                "audio_option": audio_option,
                "user_id": user_id
            }
        )

        logger.info(f"Agent4 processing audio generation")
        audio_result = await audio_agent.process(agent_input)

        if not audio_result.success:
            raise Exception(audio_result.error or "Audio generation failed")

        result_data = audio_result.data

        # Upload audio files to S3
        audio_files_output = []
        background_music_output = None

        for audio_file in result_data.get("audio_files", []):
            filepath = audio_file.get("filepath")
            if not filepath:
                continue

            part = audio_file["part"]

            try:
                if part == "music":
                    s3_key = f"users/{user_id}/{session_id}/agent4/background_music.mp3"
                    music_url = await _upload_audio_to_s3(storage_service, filepath, s3_key)
                    background_music_output = {
                        "url": music_url,
                        "duration": audio_file.get("duration", 60)
                    }
                    logger.info(f"Uploaded background music to S3")
                else:
                    s3_key = f"users/{user_id}/{session_id}/agent4/audio_{part}.mp3"
                    audio_url = await _upload_audio_to_s3(storage_service, filepath, s3_key)
                    audio_files_output.append({
                        "part": part,
                        "url": audio_url,
                        "duration": audio_file.get("duration", 0)
                    })
                    logger.info(f"Uploaded {part} audio to S3")
            except Exception as e:
                logger.warning(f"Failed to upload {part} audio to S3: {e}")

        # Create agent_4_data output
        agent_4_data = {
            "audio_files": audio_files_output,
            "background_music": background_music_output or {"url": "", "duration": 60}
        }

        # Upload agent_4_data to S3
        try:
            s3_key_output = f"users/{user_id}/{session_id}/agent4/agent_4_data.json"
            storage_service.s3_client.put_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key_output,
                Body=json.dumps(agent_4_data, indent=2).encode('utf-8'),
                ContentType='application/json'
            )
            logger.info(f"Agent4 uploaded agent_4_data.json to S3")
        except Exception as e:
            logger.error(f"Agent4 failed to upload agent_4_data.json: {e}", exc_info=True)

        # Report finished status
        await send_status(
            "finished",
            fileCount=len(result_data.get("audio_files", [])),
            progress=100,
            cost=result_data.get("total_cost", 0)
        )

        logger.info(f"Agent4 completed audio generation for session {session_id}")

        return {
            "status": "success",
            "audio_files": result_data.get("audio_files", []),
            "total_duration": result_data.get("total_duration", 0),
            "total_cost": result_data.get("total_cost", 0)
        }

    except Exception as e:
        await send_status("error", error=str(e), reason=f"Agent4 failed: {type(e).__name__}")
        logger.error(f"Agent4 failed for session {session_id}: {e}")
        raise
