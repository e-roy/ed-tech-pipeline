"""
Agent 5 - Video Generator using Remotion

Generates a 60-second video from pipeline data:
1. Generates AI videos in parallel using Replicate (Minimax)
2. Calculates scene timing to space audio across 60 seconds
3. Renders video using Remotion
4. Uploads final video to S3

Uses Replicate Minimax for AI-generated video clips (~$0.035/5s video)
"""
import asyncio
import json
import math
import os
import subprocess
import tempfile
import time
import httpx
import logging

logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Awaitable
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService
from app.services.replicate_video import ReplicateVideoService
from app.config import get_settings


# Path to Remotion project
# agent_5.py is at: backend/app/agents/agent_5.py
# remotion is at: remotion/
# So we need to go up 3 levels from agent_5.py to backend, then up to pipeline, then into remotion
REMOTION_DIR = Path(__file__).parent.parent.parent.parent / "remotion"


async def generate_video_replicate(
    prompt: str,
    api_key: str,
    model: str = "minimax",
    progress_callback: Optional[callable] = None,
    seed: Optional[int] = None
) -> str:
    """
    Generate a video using Replicate (Minimax video-01 by default).

    Args:
        prompt: Visual description for the video
        api_key: Replicate API key
        model: Model to use ("minimax", "kling", "luma")
        progress_callback: Optional callback for progress updates
        seed: Optional random seed for reproducibility

    Returns:
        URL of the generated video
    """
    service = ReplicateVideoService(api_key)
    return await service.generate_video(
        prompt=prompt,
        model=model,
        seed=seed
    )


async def generate_image_dalle(prompt: str, api_key: str, max_retries: int = 3) -> bytes:
    """Generate an image using DALL-E 2 with retry logic."""
    # Use longer timeout and http2=False to avoid uvloop SSL issues
    async with httpx.AsyncClient(timeout=120.0, http2=False) as client:
        last_error = None

        for attempt in range(max_retries):
            try:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-2",
                        "prompt": prompt,
                        "n": 1,
                        "size": "1024x1024",
                        "response_format": "url"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    image_url = data["data"][0]["url"]

                    # Download the image
                    image_response = await client.get(image_url)
                    return image_response.content

                # Check if it's a server error (5xx) - retry these
                if response.status_code >= 500:
                    last_error = f"DALL-E API server error (attempt {attempt + 1}/{max_retries}): {response.text}"
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue

                # For other errors (4xx), don't retry
                raise RuntimeError(f"DALL-E API error: {response.text}")

            except httpx.RequestError as e:
                last_error = f"Network error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise RuntimeError(last_error)

        raise RuntimeError(last_error or "DALL-E API failed after retries")


def calculate_scene_timing(audio_files: List[Dict], fps: int = 30, total_duration: int = 60) -> List[Dict]:
    """
    Calculate scene timing to distribute audio across 60 seconds.

    Returns scene data with start frames and durations.
    """
    total_frames = total_duration * fps
    num_scenes = len(audio_files)

    # Calculate spacing between scenes
    scene_duration_frames = total_frames // num_scenes

    scenes = []
    for i, audio in enumerate(audio_files):
        start_frame = i * scene_duration_frames
        duration_frames = scene_duration_frames

        # Last scene gets any remaining frames
        if i == num_scenes - 1:
            duration_frames = total_frames - start_frame

        audio_duration_seconds = audio.get("duration", 5.0)
        audio_duration_frames = int(audio_duration_seconds * fps)

        scenes.append({
            "part": audio["part"],
            "startFrame": start_frame,
            "durationFrames": duration_frames,
            "audioDurationFrames": audio_duration_frames
        })

    return scenes


async def render_video_with_remotion(
    scenes: List[Dict],
    background_music_url: str,
    output_path: str,
    temp_dir: str,
    websocket_manager: Optional[WebSocketManager] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    supersessionid: Optional[str] = None
) -> str:
    """
    Render video using Remotion CLI.

    Args:
        scenes: List of scene data with imageUrl/videoUrl, audioUrl, timing info
        background_music_url: URL or path to background music
        output_path: Path for output video file
        temp_dir: Temp directory containing local image files
        websocket_manager: Optional WebSocket manager for progress updates
        session_id: Optional session ID for progress updates
        user_id: Optional user ID for progress updates
        supersessionid: Optional supersession ID for progress updates

    Returns:
        Path to rendered video
    """
    # Copy images to Remotion's public directory for local access
    remotion_public = REMOTION_DIR / "public"
    remotion_public.mkdir(exist_ok=True)

    # Update scenes based on visual type
    updated_scenes = []
    for scene in scenes:
        part = scene["part"]
        visual_type = scene.get("visualType", "image")

        if visual_type == "video":
            # For video mode, keep the URL as-is (Remotion will fetch from URL)
            updated_scenes.append(scene)
        else:
            # For image mode, copy local files to Remotion public dir
            local_image_path = os.path.join(temp_dir, f"{part}.png")

            # Copy image to Remotion public dir
            if os.path.exists(local_image_path):
                dest_path = remotion_public / f"{part}.png"
                import shutil
                shutil.copy2(local_image_path, dest_path)
                # Use relative path from Remotion's perspective
                image_url = f"{part}.png"
            else:
                image_url = scene.get("imageUrl", "")

            updated_scenes.append({
                **scene,
                "imageUrl": image_url
            })

    # Prepare props for Remotion
    props = {
        "scenes": updated_scenes,
        "backgroundMusicUrl": background_music_url,
        "backgroundMusicVolume": 0.3
    }

    # Write props to temp file
    props_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(props, props_file)
    props_file.close()

    try:
        # Run Remotion render
        import subprocess
        import re

        # Log the props for debugging
        print(f"Remotion props: {json.dumps(props, indent=2)}")
        print(f"Remotion dir: {REMOTION_DIR}")
        print(f"Public dir contents: {list(remotion_public.iterdir()) if remotion_public.exists() else 'not found'}")

        cmd = f"bunx remotion render src/index.ts VideoComposition {output_path} --props={props_file.name}"

        # Use Popen to stream output and send progress updates
        # Use system PATH (includes bun from systemd service or current environment)
        process = subprocess.Popen(
            cmd,
            cwd=str(REMOTION_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            env=os.environ.copy(),  # Use current environment PATH as-is
            bufsize=1
        )

        output_lines = []
        last_progress_update = 0

        # Stream output and parse progress
        def read_output():
            nonlocal last_progress_update
            for line in iter(process.stdout.readline, ''):
                output_lines.append(line)
                print(line, end='')

                # Parse rendering progress: "Rendered 100/1800"
                match = re.search(r'Rendered (\d+)/(\d+)', line)
                if match and websocket_manager and session_id:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    percent = int((current / total) * 100)

                    # Only send updates every 5% to avoid flooding
                    if percent >= last_progress_update + 5 or current == total:
                        last_progress_update = percent
                        # Schedule the async send in the event loop
                        import asyncio
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.run_coroutine_threadsafe(
                                    websocket_manager.send_progress(session_id, {
                                        "agentnumber": "Agent5",
                                        "userID": user_id or "",
                                        "sessionID": session_id,
                                        "supersessionID": supersessionid or "",
                                        "status": "processing",
                                        "message": f"Rendering video: {percent}% ({current}/{total} frames)",
                                        "timestamp": int(time.time() * 1000),
                                        "progress": {
                                            "stage": "rendering",
                                            "current": current,
                                            "total": total,
                                            "percent": percent
                                        }
                                    }),
                                    loop
                                )
                        except Exception as e:
                            print(f"Failed to send render progress: {e}")

        # Run the output reading in a thread
        await asyncio.to_thread(read_output)
        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"Remotion render failed:\n{''.join(output_lines)}")

        # Check output file size
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"Output video size: {file_size} bytes")
        else:
            print(f"Output file not found at {output_path}")

        return output_path

    finally:
        # Clean up props file
        os.unlink(props_file.name)
        # Clean up copied images from public dir
        for scene in scenes:
            part = scene["part"]
            public_image = remotion_public / f"{part}.png"
            if public_image.exists():
                public_image.unlink()


async def agent_5_process(
    websocket_manager: Optional[WebSocketManager],
    user_id: str,
    session_id: str,
    supersessionid: str,
    storage_service: Optional[StorageService] = None,
    pipeline_data: Optional[Dict[str, Any]] = None,
    generation_mode: str = "video",  # Kept for backwards compatibility, always uses video
    db: Optional[Session] = None,
    status_callback: Optional[Callable[[str, str, str, str, int], Awaitable[None]]] = None,
    restart_from_remotion: bool = False
) -> Optional[str]:
    """
    Agent5: Video generation agent using Remotion.

    Args:
        websocket_manager: WebSocket manager for status updates (deprecated, use status_callback)
        user_id: User identifier
        session_id: Session identifier
        supersessionid: Super session identifier
        storage_service: Storage service for S3 operations
        pipeline_data: Pipeline data including:
            - script: Script with visual_prompt for each section
            - audio_data: Audio files and background music
        generation_mode: Deprecated - always uses AI video generation
        db: Database session for querying video_session table
        status_callback: Callback function for sending status updates to orchestrator
        restart_from_remotion: If True, skip clip generation and restart from Remotion rendering

    Returns:
        The presigned URL of the uploaded video, or None on error
    """
    settings = get_settings()

    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()

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
            return

        timestamp = int(time.time() * 1000)
        filename = f"agent_{agent_number}_{status}_{timestamp}.json"
        # Use scaffold_test/{userId}/{sessionId}/agent5/ path
        s3_key = f"scaffold_test/{user_id}/{session_id}/agent5/{filename}"

        try:
            json_content = json.dumps(status_data, indent=2).encode('utf-8')
            storage_service.s3_client.put_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key,
                Body=json_content,
                ContentType='application/json'
            )
        except Exception as e:
            logger.warning(f"Failed to create status JSON file: {e}")

    video_url = None
    temp_dir = None

    try:
        # Report starting status
        await send_status("Agent5", "starting", supersessionID=supersessionid)
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "starting",
            "timestamp": int(time.time() * 1000)
        }
        await create_status_json("5", "starting", status_data)

        # Scan S3 folders for Agent2 and Agent4 content
        agent2_prefix = f"scaffold_test/{user_id}/{session_id}/agent2/"
        agent4_prefix = f"scaffold_test/{user_id}/{session_id}/agent4/"
        
        script = {}
        storyboard = {}
        audio_files = []
        background_music = {}
        
        try:
            # Scan Agent2 folder for script/data files
            agent2_files = storage_service.list_files_by_prefix(agent2_prefix, limit=1000)
            logger.info(f"Found {len(agent2_files)} files in Agent2 folder")
            
            # Look for storyboard.json first (preferred source)
            storyboard_key = f"{agent2_prefix}storyboard.json"
            try:
                obj = storage_service.s3_client.get_object(
                    Bucket=storage_service.bucket_name,
                    Key=storyboard_key
                )
                content = obj["Body"].read().decode('utf-8')
                storyboard = json.loads(content)
                logger.info(f"Agent5 loaded storyboard.json from {storyboard_key}")
                
                # Extract script from storyboard segments if available
                if storyboard.get("segments"):
                    # Convert storyboard segments to script format for compatibility
                    script_parts = {}
                    for segment in storyboard["segments"]:
                        segment_type = segment.get("type", "")
                        if segment_type == "hook":
                            script_parts["hook"] = {
                                "text": segment.get("narration", ""),
                                "duration": str(segment.get("duration", 0)),
                                "key_concepts": segment.get("key_concepts", []),
                                "visual_guidance": segment.get("visual_guidance", "")
                            }
                        elif segment_type == "concept_introduction":
                            script_parts["concept"] = {
                                "text": segment.get("narration", ""),
                                "duration": str(segment.get("duration", 0)),
                                "key_concepts": segment.get("key_concepts", []),
                                "visual_guidance": segment.get("visual_guidance", "")
                            }
                        elif segment_type == "process_explanation":
                            script_parts["process"] = {
                                "text": segment.get("narration", ""),
                                "duration": str(segment.get("duration", 0)),
                                "key_concepts": segment.get("key_concepts", []),
                                "visual_guidance": segment.get("visual_guidance", "")
                            }
                        elif segment_type == "conclusion":
                            script_parts["conclusion"] = {
                                "text": segment.get("narration", ""),
                                "duration": str(segment.get("duration", 0)),
                                "key_concepts": segment.get("key_concepts", []),
                                "visual_guidance": segment.get("visual_guidance", "")
                            }
                    if script_parts:
                        script = script_parts
                        logger.info("Agent5 extracted script from storyboard.json")
            except Exception as e:
                logger.debug(f"Agent5 could not load storyboard.json: {e}, will try other sources")
            
            # Look for script JSON files or status files that might contain script data (fallback)
            if not script:
                for file_info in agent2_files:
                    key = file_info.get("key", file_info.get("Key", ""))
                    if "script" in key.lower() or "finished" in key.lower():
                        # Skip storyboard.json as we already tried it
                        if "storyboard.json" in key:
                            continue
                        # Try to download and parse
                        try:
                            obj = storage_service.s3_client.get_object(
                                Bucket=storage_service.bucket_name,
                                Key=key
                            )
                            content = obj["Body"].read().decode('utf-8')
                            data = json.loads(content)
                            if "generation_script" in data:
                                script = data["generation_script"]
                            elif "script" in data:
                                script = data["script"]
                        except Exception as e:
                            logger.debug(f"Failed to parse file {key}: {e}")
                            pass
            
            # Scan Agent4 folder for audio files
            agent4_files = storage_service.list_files_by_prefix(agent4_prefix, limit=1000)
            logger.info(f"Found {len(agent4_files)} files in Agent4 folder")
            
            for file_info in agent4_files:
                key = file_info.get("key", file_info.get("Key", ""))
                if key.endswith(".mp3"):
                    # Extract part name from filename (e.g., audio_hook.mp3 -> hook)
                    filename = key.split("/")[-1]
                    if filename.startswith("audio_"):
                        part = filename.replace("audio_", "").replace(".mp3", "")
                        audio_url = storage_service.generate_presigned_url(key, expires_in=86400)
                        audio_files.append({
                            "part": part,
                            "url": audio_url,
                            "duration": 5.0  # Default duration, could be extracted from metadata
                        })
                elif "background_music" in key.lower() or "music" in key.lower():
                    background_music_url = storage_service.generate_presigned_url(key, expires_in=86400)
                    background_music = {
                        "url": background_music_url,
                        "duration": 60  # Default duration
                    }
            
            # If no pipeline_data provided and we couldn't find files, try querying database
            if not pipeline_data and not script and not audio_files:
                if db is not None:
                    try:
                        result = db.execute(
                            sql_text(
                                "SELECT * FROM video_session WHERE id = :session_id AND user_id = :user_id"
                            ),
                            {"session_id": session_id, "user_id": user_id},
                        ).fetchone()
                        
                        if result:
                            if hasattr(result, "_mapping"):
                                video_session_data = dict(result._mapping)
                            else:
                                video_session_data = {
                                    "id": getattr(result, "id", None),
                                    "user_id": getattr(result, "user_id", None),
                                    "generated_script": getattr(result, "generated_script", None),
                                }
                            
                            # Extract script from video_session
                            if video_session_data.get("generated_script"):
                                from app.agents.agent_2 import extract_script_from_generated_script
                                extracted_script = extract_script_from_generated_script(video_session_data.get("generated_script"))
                                if extracted_script:
                                    script = extracted_script
                    except Exception as db_error:
                        logger.warning(f"Agent5 failed to query video_session as fallback: {db_error}")
                
                # If still no script or audio files, raise error
                if not script and not audio_files:
                    raise ValueError(f"No content found in S3 folders or database. Agent2: {len(agent2_files)} files, Agent4: {len(agent4_files)} files")
            
            # Initialize agent data variables (needed for nested functions)
            agent_2_data = {}
            agent_4_data = {}
            
            # If pipeline_data is provided, use it (for backwards compatibility)
            if pipeline_data:
                agent_2_data = pipeline_data.get("agent_2_data", {})
                agent_4_data = pipeline_data.get("agent_4_data", {})
                
                if agent_2_data or agent_4_data:
                    script = agent_2_data.get("script", script)
                    # Use storyboard from agent_2_data if available, otherwise keep what we loaded
                    if agent_2_data.get("storyboard"):
                        storyboard = agent_2_data.get("storyboard")
                    audio_files = agent_4_data.get("audio_files", audio_files)
                    background_music = agent_4_data.get("background_music", background_music)
                else:
                    script = pipeline_data.get("script", script)
                    # Use storyboard from pipeline_data if available
                    if pipeline_data.get("storyboard"):
                        storyboard = pipeline_data.get("storyboard")
                    audio_data = pipeline_data.get("audio_data", {})
                    audio_files = audio_data.get("audio_files", audio_files)
                    background_music = audio_data.get("background_music", background_music)
            
            if not script:
                raise ValueError("No script data found in S3 or pipeline_data")
            if not audio_files:
                raise ValueError("No audio files found in S3 or pipeline_data")
            
            # Log storyboard status
            if storyboard:
                logger.info(f"Agent5 loaded storyboard.json with {len(storyboard.get('segments', []))} segments")
            else:
                logger.info("Agent5 did not find storyboard.json, using script data only")
                
        except Exception as e:
            logger.error(f"Agent5 failed to scan S3 folders: {e}")
            raise ValueError(f"Failed to discover Agent2/Agent4 content from S3: {str(e)}")

        # Create temp directory for assets
        temp_dir = tempfile.mkdtemp(prefix="agent5_")

        # Calculate scene timing first
        scene_timing = calculate_scene_timing(audio_files)

        # Build the complete scenes structure BEFORE video generation
        # This is what will be displayed and sent to Remotion
        sections = ["hook", "concept", "process", "conclusion"]
        scenes = []
        visual_prompts = {}  # Store prompts for parallel generation

        for timing in scene_timing:
            part = timing["part"]

            # Find matching audio file
            audio_file = next((a for a in audio_files if a["part"] == part), None)
            audio_url = audio_file.get("url", "") if audio_file else ""

            # Get section data and visual prompt
            section_data = script.get(part, {})
            visual_prompt = section_data.get("visual_prompt", "")
            
            # If storyboard is available, try to get enhanced data from it
            if storyboard and storyboard.get("segments"):
                # Map part to storyboard segment type
                segment_type_map = {
                    "hook": "hook",
                    "concept": "concept_introduction",
                    "process": "process_explanation",
                    "conclusion": "conclusion"
                }
                segment_type = segment_type_map.get(part)
                
                # Find matching segment in storyboard
                if segment_type:
                    storyboard_segment = next(
                        (seg for seg in storyboard["segments"] if seg.get("type") == segment_type),
                        None
                    )
                    if storyboard_segment:
                        # Use visual_guidance from storyboard if available
                        if storyboard_segment.get("visual_guidance") and not visual_prompt:
                            visual_prompt = storyboard_segment.get("visual_guidance")
                        # Use key_concepts from storyboard if available
                        if storyboard_segment.get("key_concepts") and not section_data.get("key_concepts"):
                            section_data["key_concepts"] = storyboard_segment.get("key_concepts")
                        # Use duration from storyboard if available
                        if storyboard_segment.get("duration") and not section_data.get("duration"):
                            section_data["duration"] = str(storyboard_segment.get("duration"))
            
            if not visual_prompt:
                # Fallback: generate prompt from text
                text = section_data.get("text", "")
                visual_prompt = f"Cinematic scene representing: {text[:200]}"

            visual_prompts[part] = visual_prompt

            # Get animation data from script if available
            animation_data = section_data.get("animation", None)

            scene = {
                "part": part,
                "audioUrl": audio_url,
                "startFrame": timing["startFrame"],
                "durationFrames": timing["durationFrames"],
                "audioDurationFrames": timing["audioDurationFrames"],
                "visualType": "video",
                "videoUrl": "",  # Will be populated after generation
                "visualPrompt": visual_prompt  # Include prompt in the JSON
            }

            # Add animation data if present
            if animation_data:
                scene["animation"] = animation_data

            scenes.append(scene)

        # Send the unified JSON structure that will be used for generation
        await send_status(
            "Agent5", "processing",
            supersessionID=supersessionid,
            message="Generating all 4 AI videos in parallel...",
            generationPayload={
                "scenes": scenes,
                "backgroundMusicUrl": background_music.get("url", ""),
                "backgroundMusicVolume": 0.3
            }
        )
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "processing",
            "message": "Generating all 4 AI videos in parallel...",
            "timestamp": int(time.time() * 1000),
            "generationPayload": {
                "scenes": scenes,
                "backgroundMusicUrl": background_music.get("url", ""),
                "backgroundMusicVolume": 0.3
            }
        }
        await create_status_json("5", "processing", status_data)

        # Generate all videos in parallel using asyncio.gather
        # Track completion for progress updates
        completed_videos = []

        # Constants for video generation
        CLIP_DURATION = 6.0  # Minimax generates 6-second clips

        # Calculate clips needed per section based on scene timing
        clips_per_section = {}
        for scene in scenes:
            part = scene["part"]
            scene_duration = scene["durationFrames"] / 30.0  # Convert frames to seconds
            clips_needed = max(1, math.ceil(scene_duration / CLIP_DURATION))
            clips_per_section[part] = clips_needed

        total_clips = sum(clips_per_section.values())
        
        # RESTART LOGIC: If restarting from Remotion, skip clip generation and load from S3
        if restart_from_remotion:
            logger.info(f"[{session_id}] Restarting from Remotion - loading existing clips from S3")
            
            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message=f"Verifying {total_clips} clips in S3 for restart..."
            )
            
            # Verify and load clips from S3
            generated_visuals = {}
            agent5_prefix = f"scaffold_test/{user_id}/{session_id}/agent5/"
            
            for section in sections:
                concat_key = f"{agent5_prefix}{section}_concat.mp4"
                
                # Check if concatenated clip exists
                try:
                    storage_service.s3_client.head_object(
                        Bucket=storage_service.bucket_name,
                        Key=concat_key
                    )
                    # Generate presigned URL
                    concat_url = storage_service.generate_presigned_url(concat_key, expires_in=3600)
                    generated_visuals[section] = concat_url
                    logger.info(f"[{session_id}] Found existing clip for {section}: {concat_key}")
                except Exception as e:
                    logger.error(f"[{session_id}] Missing clip for {section}: {e}")
                    raise ValueError(f"Cannot restart - missing video clip for section '{section}'. Please regenerate from scratch.")
            
            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message=f"All {total_clips} clips verified, skipping to Remotion rendering..."
            )
            
            # Skip to line 880 (update scenes with loaded URLs)
            # We'll set a flag to skip the generation block
            skip_generation = True
        else:
            skip_generation = False

        # Only generate videos if not restarting
        if not skip_generation:
            async def generate_section_video(section: str) -> tuple[str, str]:
                """Generate multiple video clips for a section and return (section, concatenated_url)"""
                import subprocess
                import httpx

                prompt = visual_prompts[section]
                clips_needed = clips_per_section[section]

                logger.info(f"[{session_id}] Generating {clips_needed} clips for {section}")

                # Extract base_scene parameters if present for consistency
                # Check both new format (agent_2_data) and old format (root level)
                if agent_2_data:
                    base_scene = agent_2_data.get("base_scene", {})
                elif pipeline_data:
                    base_scene = pipeline_data.get("base_scene", {})
                else:
                    base_scene = {}
                style = base_scene.get("style", "")
                setting = base_scene.get("setting", "")
                teacher_desc = base_scene.get("teacher", "")
                students_desc = base_scene.get("students", "")

                # Build consistency anchor
                consistency_anchor = ""
                if style or setting or teacher_desc or students_desc:
                    consistency_parts = []
                    if style:
                        consistency_parts.append(style)
                    if setting:
                        consistency_parts.append(f"Setting: {setting}")
                    if teacher_desc:
                        consistency_parts.append(f"Teacher: {teacher_desc}")
                    if students_desc:
                        consistency_parts.append(f"Students: {students_desc}")
                    consistency_anchor = " | ".join(consistency_parts) + " | "

                # Generate progressive prompts for each clip position
                clip_prompts = []
                for i in range(clips_needed):
                    # Create clip-specific temporal and action cues based on position
                    if clips_needed == 1:
                        # Single clip: use full prompt as-is
                        clip_prompt = f"{consistency_anchor}{prompt}, smooth cinematic movement, maintaining consistent visual style throughout"
                    elif i == 0:
                        # First clip: Opening/beginning of action
                        clip_prompt = f"{consistency_anchor}OPENING SHOT: {prompt}, camera slowly pushes in, characters beginning action, establishing shot with clear framing"
                    elif i == clips_needed - 1:
                        # Final clip: Conclusion of action
                        clip_prompt = f"{consistency_anchor}CONTINUING FINAL SHOT: {prompt}, camera holds steady from previous angle, characters completing action, maintaining exact same composition and lighting as previous clip"
                    else:
                        # Middle clips: Progression of action
                        clip_prompt = f"{consistency_anchor}MID-SEQUENCE SHOT {i+1}: {prompt}, camera maintains previous angle and framing, characters mid-action, same positioning and lighting"

                    clip_prompts.append(clip_prompt)

                # Generate deterministic seed for this section
                # Use hash of section name to get consistent seed per section
                import hashlib
                section_hash = int(hashlib.md5(section.encode()).hexdigest()[:8], 16)
                section_seed = section_hash % 100000  # Keep seed in reasonable range

                logger.info(f"[{session_id}] Using seed {section_seed} for all clips in {section}")

                # Generate all clips for this section with same seed
                generated_clips = []
                for clip_idx, clip_prompt in enumerate(clip_prompts):
                    video_url = await generate_video_replicate(
                        clip_prompt,
                        settings.REPLICATE_API_KEY,
                        model="minimax",
                        seed=section_seed  # Same seed for all clips in this section
                    )
                    generated_clips.append(video_url)

                    # Update progress
                    completed_videos.append(f"{section}_{clip_idx}")
                    await send_status(
                        "Agent5",
                        "processing",
                        supersessionID=supersessionid,
                        message=f"Generated clip {len(completed_videos)}/{total_clips} ({section} {clip_idx+1}/{clips_needed})",
                        progress={
                            "stage": "video_generation",
                            "completed": len(completed_videos),
                            "total": total_clips,
                            "section": section
                        }
                    )

                # If only one clip, return it directly
                if len(generated_clips) == 1:
                    return (section, generated_clips[0])

                # Concatenate multiple clips
                # Download all clips to temp files
                clip_paths = []
                async with httpx.AsyncClient(timeout=120.0) as client:
                    for i, clip_url in enumerate(generated_clips):
                        response = await client.get(clip_url)
                        response.raise_for_status()
                        clip_path = os.path.join(temp_dir, f"{section}_clip_{i}.mp4")
                        with open(clip_path, 'wb') as f:
                            f.write(response.content)
                        clip_paths.append(clip_path)

                # Create concat list file
                concat_list_path = os.path.join(temp_dir, f"{section}_concat_list.txt")
                with open(concat_list_path, 'w') as f:
                    for clip_path in clip_paths:
                        f.write(f"file '{clip_path}'\n")

                # Concatenate clips using ffmpeg
                output_path = os.path.join(temp_dir, f"{section}_concatenated.mp4")
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_list_path,
                    "-c", "copy",
                    output_path
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"FFmpeg concat failed for {section}: {result.stderr}")
                    # Fallback to first clip
                    return (section, generated_clips[0])

                # Upload concatenated video to S3 for Remotion to access
                with open(output_path, 'rb') as f:
                    concat_content = f.read()

                # Use scaffold_test/{userId}/{sessionId}/agent5/ path
                concat_s3_key = f"scaffold_test/{user_id}/{session_id}/agent5/{section}_concat.mp4"
                storage_service.upload_file_direct(concat_content, concat_s3_key, "video/mp4")
                concat_url = storage_service.generate_presigned_url(concat_s3_key, expires_in=3600)

                logger.info(f"[{session_id}] Concatenated {len(generated_clips)} clips for {section}")

                return (section, concat_url)

            # Run all 4 video generations in parallel
            results = await asyncio.gather(
                *[generate_section_video(section) for section in sections]
            )

            # Map results back to sections
            generated_visuals = {section: url for section, url in results}

        # Update scenes with generated video URLs
        for scene in scenes:
            part = scene["part"]
            scene["videoUrl"] = generated_visuals.get(part, "")
            # Remove the visual prompt from final output (was just for display)
            if "visualPrompt" in scene:
                del scene["visualPrompt"]

        # Update status for rendering
        await send_status(
            "Agent5", "processing",
            supersessionID=supersessionid,
            message="Rendering video with Remotion (this may take 2-4 minutes)..."
        )
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "processing",
            "message": "Rendering video with Remotion (this may take 2-4 minutes)...",
            "timestamp": int(time.time() * 1000)
        }

        # Get background music URL
        background_music_url = background_music.get("url", "")

        # Render video
        output_path = os.path.join(temp_dir, "output.mp4")
        await render_video_with_remotion(
            scenes,
            background_music_url,
            output_path,
            temp_dir,
            websocket_manager=websocket_manager,  # render_video_with_remotion may still use it
            session_id=session_id,
            user_id=user_id,
            supersessionid=supersessionid
        )

        # Upload video to S3 - use scaffold_test/{userId}/{sessionId}/agent5/ path
        import uuid
        video_filename = f"final_video_{uuid.uuid4().hex[:8]}.mp4"
        video_s3_key = f"scaffold_test/{user_id}/{session_id}/agent5/{video_filename}"

        # Debug: Check file before upload
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"Uploading video: {output_path} ({file_size} bytes) to {video_s3_key}")
        else:
            print(f"ERROR: Output file not found at {output_path}")

        # Read file contents before uploading
        with open(output_path, "rb") as f:
            video_content = f.read()

        storage_service.upload_file_direct(video_content, video_s3_key, "video/mp4")
        video_url = storage_service.generate_presigned_url(video_s3_key, expires_in=86400)  # 24 hours for testing
        print(f"Video uploaded successfully: {video_url}")

        # Report finished status with video link
        await send_status(
            "Agent5", "finished",
            supersessionID=supersessionid,
            videoUrl=video_url,
            progress=100
        )
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "finished",
            "timestamp": int(time.time() * 1000),
            "videoUrl": video_url
        }
        await create_status_json("5", "finished", status_data)

        return video_url

    except Exception as e:
        # Report error status
        error_kwargs = {
            "error": str(e),
            "reason": f"Agent5 failed: {type(e).__name__}",
            "supersessionID": supersessionid if 'supersessionid' in locals() else None
        }
        await send_status("Agent5", "error", **error_kwargs)
        error_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "status": "error",
            "timestamp": int(time.time() * 1000),
            **error_kwargs
        }
        await create_status_json("5", "error", error_data)
        raise

    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
