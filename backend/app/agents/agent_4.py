"""
Agent 4 - Audio Pipeline Agent

This agent generates TTS audio from script text using OpenAI's TTS API.
It receives a script with hook, concept, process, and conclusion parts,
generates audio for each, creates timed narration, mixes with background music,
and outputs a final 60-second audio track.

Called via orchestrator in Full Test mode.
"""
import json
import os
import tempfile
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


async def get_audio_duration(file_path: str) -> float:
    """Get the duration of an audio file using ffprobe."""
    import subprocess
    import json

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        file_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(f"Failed to get audio duration: {result.stderr}")
        return 60.0  # Default fallback

    try:
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        return duration
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to parse audio duration: {e}")
        return 60.0  # Default fallback


async def create_timed_narration_track(audio_file_paths: list[str], output_path: str, total_duration: float = 60.0) -> str:
    """
    Create a timed narration track by placing audio files at calculated intervals across the total duration.
    Each narration plays at the beginning of its segment, with silence/space between narrations.

    Args:
        audio_file_paths: List of paths to audio files in order (hook, concept, process, conclusion)
        output_path: Path for output timed audio file
        total_duration: Total duration in seconds for the final track (default 60s)

    Returns:
        Path to timed audio file
    """
    import subprocess

    num_segments = len(audio_file_paths)
    segment_duration = total_duration / num_segments  # e.g., 60s / 4 = 15s per segment

    # Build ffmpeg filter_complex to place each audio at its segment start time using adelay
    filter_parts = []
    for i in range(num_segments):
        # Calculate delay for this segment (in milliseconds)
        start_time_seconds = i * segment_duration
        delay_ms = int(start_time_seconds * 1000)

        # Add atrim to limit audio to segment_duration, then adelay to position at correct time
        # This prevents narration overlap between segments
        # adelay takes stereo input, so we delay both channels
        filter_parts.append(f"[{i}:a]atrim=0:{segment_duration},adelay={delay_ms}|{delay_ms}[a{i}]")

    # Mix all delayed audio tracks together, then pad to exact total_duration
    mix_inputs = ''.join(f"[a{i}]" for i in range(num_segments))
    # Use apad to pad the mixed audio to exactly total_duration (60s)
    # Set weights to 1 1 1 1 to prevent auto-normalization (keeps voice clips at full volume)
    # Add alimiter to prevent clipping/distortion - instant attack (0.1ms) for no fade-in
    weights = ' '.join(['1'] * num_segments)
    filter_complex = ';'.join(filter_parts) + f";{mix_inputs}amix=inputs={num_segments}:duration=longest:dropout_transition=0:weights={weights},alimiter=limit=0.98:attack=0.1:release=50,apad=whole_dur={total_duration}[mixed]"

    # Build ffmpeg command with direct MP3 inputs
    cmd = ["ffmpeg", "-y"]

    # Add all audio inputs (MP3 files work directly with adelay filter)
    for audio_path in audio_file_paths:
        cmd.extend(["-i", audio_path])

    # Add filter complex and output options
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[mixed]",
        "-ac", "2",  # Stereo
        "-ar", "44100",  # Sample rate
        "-c:a", "libmp3lame",  # MP3 codec
        "-b:a", "128k",  # Bitrate
        output_path
    ])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg timed narration creation failed: {result.stderr}")

    logger.info(f"Created timed narration track: {num_segments} narrations across {total_duration}s")
    return output_path


async def mix_audio_with_background(narration_path: str, background_music_path: str, output_path: str, music_volume: float = 0.3) -> str:
    """
    Mix narration audio with background music.

    Args:
        narration_path: Path to concatenated narration audio
        background_music_path: Path to background music file
        output_path: Path for output mixed audio file
        music_volume: Volume level for background music (0.0-1.0), default 0.3 (30%)

    Returns:
        Path to mixed audio file
    """
    import subprocess

    # Mix narration with background music
    # - Narration at 1.0x volume (full volume, preserved from timed narration track)
    # - Background music at specified volume (default 0.05 = 5%)
    # - Loop music if needed with -stream_loop -1
    # - amix with dropout_transition=0 to prevent volume ducking
    # - weights=1 1 prevents auto-normalization/compression (keeps volumes as-is)
    # - alimiter prevents clipping/distortion - instant attack (0.1ms) for no fade-in
    # - Explicitly set output duration to match narration (60s)
    filter_complex = f"[0:a]volume=1.0[narration];[1:a]volume={music_volume}[music];[narration][music]amix=inputs=2:duration=first:dropout_transition=0:weights=1 1,alimiter=limit=0.98:attack=0.1:release=50[aout]"

    cmd = [
        "ffmpeg", "-y",
        "-i", narration_path,
        "-stream_loop", "-1",  # Loop background music
        "-i", background_music_path,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "libmp3lame",  # Use MP3 codec for consistency
        "-b:a", "128k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio mixing failed: {result.stderr}")

    return output_path


async def agent_4_process(
    websocket_manager: Optional[WebSocketManager],
    user_id: str,
    session_id: str,
    script: Dict[str, Any],
    voice: str = "sage",
    voice_instructions: Optional[str] = None,
    audio_option: str = "tts",
    storage_service: Optional[StorageService] = None,
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
        voice: TTS voice to use (default: sage)
        voice_instructions: Optional voice instructions for gpt-4o-mini-tts model
        audio_option: Audio generation option (tts, upload, none, instrumental)
        storage_service: Storage service for S3 operations
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
        # Pass db to enable background music selection
        audio_agent = AudioPipelineAgent(
            api_key=openai_key,
            db=db,
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
                "voice_instructions": voice_instructions,
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

        # Debug: Log all audio files from result
        logger.info(f"Agent4 received {len(result_data.get('audio_files', []))} audio files from AudioPipelineAgent")
        for af in result_data.get("audio_files", []):
            logger.info(f"  - Part: {af.get('part')}, has filepath: {bool(af.get('filepath'))}, has url: {bool(af.get('url'))}")

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

        # ====================
        # CREATE FINAL MIXED AUDIO (60 seconds)
        # ====================
        logger.info(f"Agent4 creating final mixed audio for session {session_id}")

        temp_dir = None
        final_audio_output = None

        try:
            # Create temp directory for audio processing
            temp_dir = tempfile.mkdtemp(prefix="agent4_audio_")

            # Get local file paths for narration clips (in order: hook, concept, process, conclusion)
            narration_file_paths = []
            for part_name in REQUIRED_SCRIPT_PARTS:
                audio_file = next((af for af in result_data.get("audio_files", []) if af["part"] == part_name), None)
                if audio_file and audio_file.get("filepath"):
                    narration_file_paths.append(audio_file["filepath"])
                else:
                    logger.warning(f"Agent4: Missing audio file for part '{part_name}'")

            if len(narration_file_paths) != 4:
                raise ValueError(f"Agent4: Expected 4 narration files, found {len(narration_file_paths)}")

            # Get background music - download from S3 if needed
            background_music_file = None
            logger.info(f"Agent4 searching for background music in {len(result_data.get('audio_files', []))} audio files")
            for audio_file in result_data.get("audio_files", []):
                if audio_file["part"] == "music":
                    logger.info(f"Agent4 found music part: filepath={audio_file.get('filepath')}, url={audio_file.get('url')}")
                    # Check if we have a local filepath
                    if audio_file.get("filepath"):
                        background_music_file = audio_file["filepath"]
                        logger.info(f"Agent4 using local background music file: {background_music_file}")
                    # Otherwise download from S3 URL
                    elif audio_file.get("url"):
                        import httpx
                        music_url = audio_file["url"]
                        music_download_path = os.path.join(temp_dir, "background_music.mp3")
                        logger.info(f"Agent4 downloading background music from URL: {music_url}")

                        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                            response = await client.get(music_url)
                            response.raise_for_status()
                            with open(music_download_path, "wb") as f:
                                f.write(response.content)

                        background_music_file = music_download_path
                        logger.info(f"Agent4 downloaded background music to: {background_music_file}")
                    else:
                        logger.warning(f"Agent4 music part has no filepath or url!")
                    break

            if not background_music_file:
                logger.warning(f"Agent4 NO BACKGROUND MUSIC FOUND - will create narration-only final audio")

            # Step 1: Create timed narration track (60s with spacing)
            timed_narration_path = os.path.join(temp_dir, "timed_narration.mp3")
            await create_timed_narration_track(narration_file_paths, timed_narration_path, total_duration=60.0)
            logger.info(f"Agent4 created timed narration track: {len(narration_file_paths)} clips across 60s")

            # Step 2: Mix narration with background music (if available)
            final_audio_path = os.path.join(temp_dir, "final_audio.mp3")
            if background_music_file:
                await mix_audio_with_background(
                    timed_narration_path,
                    background_music_file,
                    final_audio_path,
                    music_volume=0.03  # 5% volume for music bed (very low to keep focus on narration)
                )
                logger.info(f"Agent4 mixed narration with background music at 5% volume")
            else:
                # No background music, use timed narration as final audio
                import shutil
                shutil.copy(timed_narration_path, final_audio_path)
                logger.info(f"Agent4 using timed narration only (no background music)")

            # Step 3: Get actual duration of final audio
            actual_duration = await get_audio_duration(final_audio_path)
            logger.info(f"Agent4 final audio actual duration: {actual_duration:.2f}s")

            # Step 4: Upload final_audio.mp3 to S3
            final_audio_s3_key = f"users/{user_id}/{session_id}/agent4/final_audio.mp3"
            final_audio_url = await _upload_audio_to_s3(storage_service, final_audio_path, final_audio_s3_key)
            final_audio_output = {
                "url": final_audio_url,
                "duration": actual_duration,
                "s3_key": final_audio_s3_key
            }
            logger.info(f"Agent4 uploaded final mixed audio to S3: {final_audio_s3_key}")

        except Exception as e:
            logger.error(f"Agent4 failed to create final mixed audio: {e}", exc_info=True)
            # Don't fail the entire process - Agent 5 can fall back to individual files if needed
            logger.warning(f"Agent4 continuing without final mixed audio")
        finally:
            # Clean up temp directory
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

        # Create agent_4_data output
        agent_4_data = {
            "audio_files": audio_files_output,
            "background_music": background_music_output or {"url": "", "duration": 60},
            "final_audio": final_audio_output  # NEW: Final mixed 60s audio track
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
            "total_cost": result_data.get("total_cost", 0),
            "final_audio": final_audio_output  # Final mixed 60s audio track
        }

    except Exception as e:
        await send_status("error", error=str(e), reason=f"Agent4 failed: {type(e).__name__}")
        logger.error(f"Agent4 failed for session {session_id}: {e}")
        raise
