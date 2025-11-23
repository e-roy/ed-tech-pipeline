"""
Agent 4 - Audio Pipeline Agent

This agent generates TTS audio from script text using OpenAI's TTS API.
It receives a script with hook, concept, process, and conclusion parts,
generates audio for each.

Called via orchestrator in Full Test mode.
"""
import asyncio
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
        agent2_data: Data passed from Agent2 (template_id, diagram_id, script_id, etc.) - deprecated
        video_session_data: Optional dict with video_session row data (for Full Test mode) - same as Agent2 uses
        db: Database session for querying video_session table
        status_callback: Callback function for sending status updates to orchestrator

    Returns:
        Dict with audio generation results
    """
    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()
    
    # Query video_session table if db is provided (same as Agent2)
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
            
            # Convert result to dict (same as Agent2 does)
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
            logger.info(f"Agent4 loaded video_session data for session {session_id}")
        except Exception as e:
            logger.error(f"Agent4 failed to query video_session: {e}")
            raise
    
    # Extract data from video_session (same as Agent2 does)
    topic = None
    confirmed_facts = None
    generation_script = None
    
    if video_session_data:
        topic = video_session_data.get("topic")
        confirmed_facts = video_session_data.get("confirmed_facts")
        generation_script = video_session_data.get("generated_script")
        logger.info(f"Agent4 extracted data from video_session: topic={bool(topic)}, confirmed_facts={bool(confirmed_facts)}, generated_script={bool(generation_script)}")
        
        # Debug: Log the structure of generation_script
        if generation_script:
            logger.info(f"Agent4 generation_script type: {type(generation_script)}")
            if isinstance(generation_script, dict):
                logger.info(f"Agent4 generation_script keys: {list(generation_script.keys())}")
                # Log first level of nested structure
                for key in list(generation_script.keys())[:5]:  # Limit to first 5 keys
                    value = generation_script[key]
                    if isinstance(value, dict):
                        logger.info(f"Agent4 generation_script['{key}'] is dict with keys: {list(value.keys())}")
                    else:
                        logger.info(f"Agent4 generation_script['{key}'] type: {type(value)}")
    
    # Extract script from generation_script (same as Agent2 does)
    if not script and generation_script:
        from app.agents.agent_2 import extract_script_from_generated_script

        logger.info(f"[SCRIPT TRACE] Agent4 extracting script from generation_script")
        logger.info(f"[SCRIPT TRACE] generation_script type: {type(generation_script)}")
        if isinstance(generation_script, dict):
            logger.info(f"[SCRIPT TRACE] generation_script top-level keys: {list(generation_script.keys())}")

        script = extract_script_from_generated_script(generation_script)
        if script:
            logger.info(f"[SCRIPT TRACE] Agent4 extracted script successfully for session {session_id}")
            logger.info(f"[SCRIPT TRACE] Extracted script keys: {list(script.keys())}")
            # Log what fields each part has
            for part_name in ["hook", "concept", "process", "conclusion"]:
                if part_name in script and isinstance(script[part_name], dict):
                    part_keys = list(script[part_name].keys())
                    logger.info(f"[SCRIPT TRACE] script['{part_name}'] keys: {part_keys}")
                    # Log the actual text field value (first 100 chars)
                    text_value = script[part_name].get("text", script[part_name].get("narration", script[part_name].get("narrationtext", "")))
                    logger.info(f"[SCRIPT TRACE] script['{part_name}'] text preview: {text_value[:100] if text_value else '(empty)'}")
        else:
            logger.warning(f"[SCRIPT TRACE] Agent4 extract_script_from_generated_script returned None or empty for session {session_id}")
    
    # If script is still empty, wait for Agent2 to write it (they run in parallel)
    if not script and db is not None:
        logger.info(f"Agent4 waiting for Agent2 to generate script for session {session_id}")
        max_retries = 30  # Wait up to 30 seconds
        retry_count = 0
        while not script and retry_count < max_retries:
            await asyncio.sleep(1)  # Wait 1 second between retries
            retry_count += 1
            
            # Re-query database for updated script
            result = db.execute(
                sql_text(
                    "SELECT generated_script FROM video_session WHERE id = :session_id AND user_id = :user_id"
                ),
                {"session_id": session_id, "user_id": user_id},
            ).fetchone()
            
            if result:
                if hasattr(result, "_mapping"):
                    generated_script = dict(result._mapping).get("generated_script")
                else:
                    generated_script = getattr(result, "generated_script", None)
                
                if generated_script:
                    from app.agents.agent_2 import extract_script_from_generated_script
                    extracted_script = extract_script_from_generated_script(generated_script)
                    if extracted_script:
                        script = extracted_script
                        logger.info(f"Agent4 found script after {retry_count} seconds")
                        break
        
        if not script:
            raise ValueError(
                f"Agent4 could not find script in video_session after waiting {max_retries} seconds. "
                f"Agent2 may not have generated the script yet or there was an error. "
                f"Topic: {bool(topic)}, Confirmed Facts: {bool(confirmed_facts)}, Generation Script: {bool(generation_script)}"
            )

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
        # Use users/{userId}/{sessionId}/agent4/ path
        s3_key = f"users/{user_id}/{session_id}/agent4/{filename}"

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

    result_data = {}

    try:
        # Report starting status
        await send_status("Agent4", "starting")
        status_data = {
            "agentnumber": "Agent4",
            "userID": user_id,
            "sessionID": session_id,
            "status": "starting",
            "timestamp": int(time.time() * 1000)
        }
        await create_status_json("4", "starting", status_data)

        logger.info(f"Agent4 starting audio generation for session {session_id}")

        # Report processing status
        await send_status("Agent4", "processing")
        status_data = {
            "agentnumber": "Agent4",
            "userID": user_id,
            "sessionID": session_id,
            "status": "processing",
            "timestamp": int(time.time() * 1000)
        }
        await create_status_json("4", "processing", status_data)

        # Get OpenAI API key from AWS Secrets Manager
        try:
            from app.services.secrets import get_secret
            openai_key = get_secret("pipeline/openai-api-key")
            logger.debug(f"Retrieved OPENAI_API_KEY from AWS Secrets Manager for Agent4")
        except Exception as e:
            logger.warning(f"Could not retrieve OPENAI_API_KEY from Secrets Manager: {e}, AudioPipelineAgent will use fallback")
            openai_key = None
        
        # Create AudioPipelineAgent instance with explicit API key
        audio_agent = AudioPipelineAgent(
            api_key=openai_key,  # Explicitly pass key from Secrets Manager
            db=None,  # No DB needed for TTS
            storage_service=storage_service,
            websocket_manager=websocket_manager
        )

        # Validate script before processing
        if not script:
            raise ValueError(
                "Agent4 cannot generate audio without a script. "
                "Script must be provided or available in video_session.generated_script"
            )
        
        required_parts = ["hook", "concept", "process", "conclusion"]
        missing_parts = [p for p in required_parts if p not in script]
        if missing_parts:
            raise ValueError(
                f"Agent4 script is missing required parts: {', '.join(missing_parts)}. "
                f"Script must have all parts: hook, concept, process, conclusion"
            )

        # Normalize script format: AudioPipelineAgent expects "text" field, but Agent2 generates "narration"
        # Convert "narration" to "text" for each part if needed
        normalized_script = {}
        for part_name in required_parts:
            part_data = script.get(part_name, {})
            if isinstance(part_data, dict):
                normalized_part = dict(part_data)
                # If "text" doesn't exist but "narration" does, copy narration to text
                if "text" not in normalized_part and "narration" in normalized_part:
                    normalized_part["text"] = normalized_part["narration"]
                normalized_script[part_name] = normalized_part
            else:
                normalized_script[part_name] = part_data
        
        # Log script format validation
        logger.info(f"Agent4 normalized script format - checking text fields for audio generation")
        for part_name in required_parts:
            part_text = normalized_script.get(part_name, {}).get("text", "")
            if not part_text:
                logger.warning(f"Agent4: Part '{part_name}' has no text field after normalization - audio generation may fail")
            else:
                logger.info(f"Agent4: Part '{part_name}' has {len(part_text)} characters of text ready for TTS")

        # Create agent input
        agent_input = AgentInput(
            session_id=session_id,
            data={
                "script": normalized_script,
                "voice": voice,
                "audio_option": audio_option,
                "user_id": user_id
            }
        )

        # Process audio generation
        logger.info(f"Agent4 processing audio generation with script parts: {list(script.keys())}")
        audio_result = await audio_agent.process(agent_input)

        if not audio_result.success:
            raise Exception(audio_result.error or "Audio generation failed")

        result_data = audio_result.data

        # Read agent_2_data.json from S3
        agent_2_data = {}
        try:
            s3_key_agent2 = f"users/{user_id}/{session_id}/agent2/agent_2_data.json"
            response = storage_service.s3_client.get_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key_agent2
            )
            agent_2_data = json.loads(response['Body'].read().decode('utf-8'))
            logger.info(f"Agent4 loaded agent_2_data.json from S3: {s3_key_agent2}")
        except Exception as e:
            logger.warning(f"Agent4 could not load agent_2_data.json from S3: {e}")

        # Upload audio files to S3 and build agent_4_data structure
        audio_files_output = []
        background_music_output = None

        if result_data.get("audio_files"):
            for audio_file in result_data["audio_files"]:
                if audio_file.get("filepath"):
                    if audio_file["part"] == "music":
                        # Handle background music
                        s3_key = f"users/{user_id}/{session_id}/agent4/background_music.mp3"
                        try:
                            with open(audio_file["filepath"], "rb") as f:
                                storage_service.s3_client.put_object(
                                    Bucket=storage_service.bucket_name,
                                    Key=s3_key,
                                    Body=f.read(),
                                    ContentType='audio/mpeg'
                                )
                            # Generate presigned URL
                            music_url = storage_service.generate_presigned_url(s3_key, expires_in=86400)  # 24 hours for testing
                            background_music_output = {
                                "url": music_url,
                                "duration": audio_file.get("duration", 60)
                            }
                            logger.info(f"Uploaded background music to S3: {s3_key}")
                        except Exception as e:
                            logger.warning(f"Failed to upload background music to S3: {e}")
                    else:
                        # Handle narration audio
                        s3_key = f"users/{user_id}/{session_id}/agent4/audio_{audio_file['part']}.mp3"
                        try:
                            with open(audio_file["filepath"], "rb") as f:
                                storage_service.s3_client.put_object(
                                    Bucket=storage_service.bucket_name,
                                    Key=s3_key,
                                    Body=f.read(),
                                    ContentType='audio/mpeg'
                                )
                            # Generate presigned URL
                            audio_url = storage_service.generate_presigned_url(s3_key, expires_in=86400)  # 24 hours for testing
                            audio_files_output.append({
                                "part": audio_file["part"],
                                "url": audio_url,
                                "duration": audio_file.get("duration", 0)
                            })
                            logger.info(f"Uploaded audio file to S3: {s3_key}")
                        except Exception as e:
                            logger.warning(f"Failed to upload audio file to S3: {e}")

        # Create combined output structure with agent_2_data and agent_4_data
        combined_output = {
            "agent_2_data": agent_2_data,
            "agent_4_data": {
                "audio_files": audio_files_output,
                "background_music": background_music_output if background_music_output else {
                    "url": "",
                    "duration": 60
                }
            }
        }

        # Upload combined output to S3 as agent_4_output.json
        try:
            s3_key_output = f"users/{user_id}/{session_id}/agent4/agent_4_output.json"
            output_json = json.dumps(combined_output, indent=2).encode('utf-8')
            storage_service.s3_client.put_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key_output,
                Body=output_json,
                ContentType='application/json'
            )
            logger.info(f"Agent4 uploaded agent_4_output.json to S3: {s3_key_output}")
        except Exception as e:
            logger.error(f"Agent4 failed to upload agent_4_output.json: {e}", exc_info=True)

        # Report finished status
        finished_kwargs = {
            "fileCount": len(result_data.get("audio_files", [])),
            "progress": 100,
            "cost": result_data.get("total_cost", 0)
        }
        await send_status("Agent4", "finished", **finished_kwargs)
        status_data = {
            "agentnumber": "Agent4",
            "userID": user_id,
            "sessionID": session_id,
            "status": "finished",
            "timestamp": int(time.time() * 1000),
            **finished_kwargs
        }
        await create_status_json("4", "finished", status_data)

        logger.info(f"Agent4 completed audio generation for session {session_id}")

        # Return result data for orchestrator
        return {
            "status": "success",
            "audio_files": result_data.get("audio_files", []),
            "total_duration": result_data.get("total_duration", 0),
            "total_cost": result_data.get("total_cost", 0)
        }

    except Exception as e:
        # Report error status and stop pipeline
        error_kwargs = {
            "error": str(e),
            "reason": f"Agent4 failed: {type(e).__name__}"
        }
        await send_status("Agent4", "error", **error_kwargs)
        error_data = {
            "agentnumber": "Agent4",
            "userID": user_id,
            "sessionID": session_id,
            "status": "error",
            "timestamp": int(time.time() * 1000),
            **error_kwargs
        }
        await create_status_json("4", "error", error_data)
        logger.error(f"Agent4 failed for session {session_id}: {e}")
        raise  # Stop pipeline on error
