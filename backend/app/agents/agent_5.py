"""
Agent 5 - Video Generator using FFmpeg

Generates a 60-second video from pipeline data:
1. Generates AI videos in parallel using Replicate (Minimax)
2. Downloads and concatenates all narration audio files
3. Mixes concatenated narration with background music
4. Concatenates all video clips into one video
5. Combines final video with final audio
6. Uploads final video to S3

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
import resource
import signal

logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Awaitable
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService
from app.services.replicate_video import ReplicateVideoService
from app.services.video_verifier import VideoVerificationService
from app.config import get_settings


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


# DEPRECATED: Remotion-based rendering has been replaced with ffmpeg-based concatenation
# Keeping these functions commented out for reference
#
# def calculate_scene_timing(audio_files: List[Dict], fps: int = 30, total_duration: int = 60) -> List[Dict]:
#     """
#     Calculate scene timing to distribute audio across 60 seconds.
#
#     Returns scene data with start frames and durations.
#     """
#     total_frames = total_duration * fps
#     num_scenes = len(audio_files)
#
#     # Calculate spacing between scenes
#     scene_duration_frames = total_frames // num_scenes
#
#     scenes = []
#     for i, audio in enumerate(audio_files):
#         start_frame = i * scene_duration_frames
#         duration_frames = scene_duration_frames
#
#         # Last scene gets any remaining frames
#         if i == num_scenes - 1:
#             duration_frames = total_frames - start_frame
#
#         audio_duration_seconds = audio.get("duration", 5.0)
#         audio_duration_frames = int(audio_duration_seconds * fps)
#
#         scenes.append({
#             "part": audio["part"],
#             "startFrame": start_frame,
#             "durationFrames": duration_frames,
#             "audioDurationFrames": audio_duration_frames
#         })
#
#     return scenes
#
#
# async def render_video_with_remotion(
#     scenes: List[Dict],
#     background_music_url: str,
#     output_path: str,
#     temp_dir: str,
#     websocket_manager: Optional[WebSocketManager] = None,
#     session_id: Optional[str] = None,
#     user_id: Optional[str] = None,
#     supersessionid: Optional[str] = None,
#     status_callback: Optional[Callable[[str, str, str, str, int], Awaitable[None]]] = None
# ) -> str:
#     """DEPRECATED - Replaced with ffmpeg-based concatenation"""
#     pass


async def create_timed_narration_track(audio_file_paths: List[str], output_path: str, total_duration: float = 60.0) -> str:
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

        # Add adelay filter to position this audio at the correct time
        # adelay takes stereo input, so we delay both channels
        filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")

    # Mix all delayed audio tracks together, extending to total duration
    mix_inputs = ''.join(f"[a{i}]" for i in range(num_segments))
    filter_complex = ';'.join(filter_parts) + f";{mix_inputs}amix=inputs={num_segments}:duration=longest:dropout_transition=0[mixed]"

    # Build ffmpeg command with direct MP3 inputs
    cmd = ["ffmpeg", "-y"]

    # Add all audio inputs (MP3 files work directly with adelay filter)
    for audio_path in audio_file_paths:
        cmd.extend(["-i", audio_path])

    # Add filter complex and output options
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[mixed]",
        "-t", str(total_duration),  # Set total duration to 60s
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
    # - Narration at 100% volume
    # - Background music at specified volume (default 30%)
    # - Loop music if needed with -stream_loop -1
    # - Use duration of narration (first input) with -shortest
    filter_complex = f"[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=first[aout]"

    cmd = [
        "ffmpeg", "-y",
        "-i", narration_path,
        "-stream_loop", "-1",  # Loop background music
        "-i", background_music_path,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg audio mixing failed: {result.stderr}")

    return output_path


async def concatenate_all_video_clips(clip_paths: List[str], output_path: str) -> str:
    """
    Concatenate all video clips into a single video file.

    Args:
        clip_paths: List of paths to video clips in order
        output_path: Path for output concatenated video file

    Returns:
        Path to concatenated video file
    """
    import subprocess

    # Create concat list file for ffmpeg
    concat_list = output_path.replace('.mp4', '_concat_list.txt')
    with open(concat_list, 'w') as f:
        for clip_path in clip_paths:
            f.write(f"file '{clip_path}'\n")

    # Concatenate using ffmpeg with stream copy (fast, no re-encoding)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        output_path
    ]

    # Set PATH to ensure ffmpeg is accessible
    env = os.environ.copy()
    bun_paths_to_add = [
        '/home/ec2-user/.bun/bin',
        os.path.expanduser('~/.bun/bin'),
        '/usr/local/bin',
        '/opt/homebrew/bin',
    ]
    current_path = env.get('PATH', '')
    new_path_parts = [p for p in bun_paths_to_add if os.path.isdir(p)]
    new_path_parts.append(current_path)
    env['PATH'] = ':'.join(new_path_parts)

    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg video concatenation failed: {result.stderr}")

    # Clean up concat list
    os.unlink(concat_list)

    return output_path


async def extract_last_frame_as_base64(video_url: str) -> str:
    """
    Extract the last frame from a video and return it as a base64 data URI.

    Args:
        video_url: URL to the video file

    Returns:
        Base64 data URI string (data:image/png;base64,...)
    """
    import base64
    import io
    import httpx

    # Download video (use long timeout for large files from Replicate)
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.get(video_url)
        response.raise_for_status()
        video_bytes = response.content

    # Save to temp file for FFmpeg processing
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
        temp_video.write(video_bytes)
        temp_video_path = temp_video.name

    try:
        # Use FFmpeg to extract last frame as PNG to stdout
        cmd = [
            "ffmpeg",
            "-sseof", "-3",  # Start 3 seconds from end
            "-i", temp_video_path,
            "-frames:v", "1",  # Extract 1 frame
            "-f", "image2pipe",  # Output to pipe
            "-c:v", "png",  # PNG format
            "-"  # Output to stdout
        ]

        result = subprocess.run(cmd, capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg frame extraction failed: {result.stderr.decode()}")

        # Convert frame bytes to base64 data URI
        frame_b64 = base64.b64encode(result.stdout).decode('utf-8')
        data_uri = f"data:image/png;base64,{frame_b64}"

        logger.info(f"Extracted last frame as base64 ({len(frame_b64)} chars)")
        return data_uri

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_video_path)
        except:
            pass


async def combine_video_and_audio(video_path: str, audio_path: str, output_path: str) -> str:
    """
    Combine video and audio into final output file.

    Args:
        video_path: Path to concatenated video file
        audio_path: Path to mixed audio file
        output_path: Path for final output video file

    Returns:
        Path to final video file
    """
    import subprocess

    # Combine video + audio
    # - Copy video stream (no re-encoding)
    # - Encode audio as AAC
    # - Loop video to match audio duration (60s)
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",  # Loop video indefinitely
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-t", "60",  # Limit to 60 seconds (matches audio duration)
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg video+audio combination failed: {result.stderr}")

    return output_path


def sanitize_video_prompt(prompt: str) -> str:
    """
    Sanitize video prompt to prevent text, numbers, equations, and math from appearing.

    Best practices for Minimax video-01:
    - Remove mentions of text, equations, formulas, numbers, labels
    - Focus on visual, physical elements only
    - Keep prompts concise and action-focused

    Args:
        prompt: Original visual prompt

    Returns:
        Sanitized prompt focused on pure visual elements
    """
    import re

    # Keywords that might trigger text/math generation
    text_keywords = [
        r'\btext\b', r'\blabel\b', r'\bequation\b', r'\bformula\b', r'\bnumber\b',
        r'\bwriting\b', r'\bwritten\b', r'\bdiagram\b', r'\bchart\b', r'\bgraph\b',
        r'\bmath\b', r'\bcalculation\b', r'\bsymbol\b', r'\bnotation\b',
        r'\boverlay\b', r'\bcaption\b', r'\btitle\b', r'\bsubtitle\b',
        r'\bword\b', r'\bletter\b', r'\bcharacter\b', r'\bfigure\b'
    ]

    # Remove text-triggering keywords (case-insensitive)
    sanitized = prompt
    for keyword in text_keywords:
        sanitized = re.sub(keyword, '', sanitized, flags=re.IGNORECASE)

    # Clean up extra whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()

    # Add anti-text prefix if not already present
    if 'NO TEXT' not in sanitized.upper() and 'CLEAN VISUAL' not in sanitized.upper():
        sanitized = f"CLEAN VISUAL ANIMATION, NO TEXT, NO NUMBERS: {sanitized}"

    return sanitized


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
    restart_from_concat: bool = False  # Skip generation, reuse existing clips from S3
) -> Optional[str]:
    """
    Agent5: Video generation agent using FFmpeg.

    Generates a complete video by:
    1. Generating AI video clips in parallel using Replicate (Minimax)
    2. Concatenating all narration audio files
    3. Mixing narration with background music
    4. Concatenating all video clips
    5. Combining final video with final audio

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

    Returns:
        The presigned URL of the uploaded video, or None on error
    """
    settings = get_settings()

    # Get Replicate API key from Secrets Manager or settings
    replicate_api_key = None

    # Skip AWS Secrets Manager if USE_AWS_SECRETS is False (local development)
    if not settings.USE_AWS_SECRETS:
        logger.debug("USE_AWS_SECRETS=False, using REPLICATE_API_KEY from .env for Agent5")
        replicate_api_key = settings.REPLICATE_API_KEY
    else:
        try:
            from app.services.secrets import get_secret
            replicate_api_key = get_secret("pipeline/replicate-api-key")
            if replicate_api_key:
                logger.info(f"Retrieved REPLICATE_API_KEY from AWS Secrets Manager for Agent5 (length: {len(replicate_api_key)})")
            else:
                logger.warning("REPLICATE_API_KEY retrieved from Secrets Manager but is None or empty")
        except Exception as e:
            logger.error(f"Could not retrieve REPLICATE_API_KEY from Secrets Manager: {e}, falling back to settings")
            replicate_api_key = settings.REPLICATE_API_KEY

    if not replicate_api_key:
        logger.error("REPLICATE_API_KEY not set - video generation will fail")
        raise ValueError("REPLICATE_API_KEY not configured. Check AWS Secrets Manager (pipeline/replicate-api-key) or .env file.")
    else:
        logger.info(f"Using REPLICATE_API_KEY for Agent5 (starts with: {replicate_api_key[:5]}...)")

    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()

    # Initialize video verifier for quality checks
    video_verifier = VideoVerificationService(
        websocket_manager=websocket_manager,
        session_id=session_id
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
            return

        timestamp = int(time.time() * 1000)
        filename = f"agent_{agent_number}_{status}_{timestamp}.json"
        # Use users/{userId}/{sessionId}/agent5/ path
        s3_key = f"users/{user_id}/{session_id}/agent5/{filename}"

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
    
    # Initialize cost tracking early (before any operations that might fail)
    total_cost = 0.0
    cost_per_section = {}

    try:
        # Report starting status
        await send_status("Agent5", "starting", supersessionID=supersessionid, cost=total_cost)
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
        agent2_prefix = f"users/{user_id}/{session_id}/agent2/"
        agent4_prefix = f"users/{user_id}/{session_id}/agent4/"
        
        script = {}
        storyboard = {}
        audio_files = []
        background_music = {}
        
        # Initialize agent data variables at function scope (needed for nested functions)
        agent_2_data = {}
        agent_4_data = {}
        
        try:
            # Scan Agent2 folder for script/data files
            agent2_files = storage_service.list_files_by_prefix(agent2_prefix, limit=1000)
            logger.info(f"Found {len(agent2_files)} files in Agent2 folder")

            # Look for agent_2_data.json first (most complete source)
            agent_2_data_key = f"{agent2_prefix}agent_2_data.json"
            try:
                obj = storage_service.s3_client.get_object(
                    Bucket=storage_service.bucket_name,
                    Key=agent_2_data_key
                )
                content = obj["Body"].read().decode('utf-8')
                loaded_agent_2_data = json.loads(content)
                logger.info(f"Agent5 loaded agent_2_data.json from {agent_2_data_key}")

                # Extract script and storyboard from agent_2_data
                if loaded_agent_2_data.get("script"):
                    script = loaded_agent_2_data["script"]
                    logger.info("[AGENT5 TRACE] Extracted script from agent_2_data.json")
                    for part_name in ["hook", "concept", "process", "conclusion"]:
                        if part_name in script and isinstance(script[part_name], dict):
                            text_preview = script[part_name].get("text", "")[:100] if script[part_name].get("text") else "(empty)"
                            logger.info(f"[AGENT5 TRACE] script['{part_name}'] text preview: {text_preview}")
                            visual_preview = script[part_name].get("visual_guidance", "")[:100] if script[part_name].get("visual_guidance") else "(empty)"
                            logger.info(f"[AGENT5 TRACE] script['{part_name}'] visual_guidance preview: {visual_preview}")

                # Extract storyboard from agent_2_data (replaces storyboard.json)
                if loaded_agent_2_data.get("storyboard"):
                    storyboard = loaded_agent_2_data["storyboard"]
                    logger.info(f"[AGENT5 TRACE] Extracted storyboard from agent_2_data.json with {len(storyboard.get('segments', []))} segments")

                # Store agent_2_data for later use
                agent_2_data = loaded_agent_2_data

            except Exception as e:
                logger.debug(f"Agent5 could not load agent_2_data.json: {e}, will try other sources")

            # Look for storyboard.json (fallback source)
            if not script:
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
                            logger.info("[AGENT5 TRACE] Extracted script from storyboard.json")
                            for part_name in ["hook", "concept", "process", "conclusion"]:
                                if part_name in script:
                                    text_preview = script[part_name].get("text", "")[:100] if script[part_name].get("text") else "(empty)"
                                    logger.info(f"[AGENT5 TRACE] script['{part_name}'] text preview: {text_preview}")
                                    visual_preview = script[part_name].get("visual_guidance", "")[:100] if script[part_name].get("visual_guidance") else "(empty)"
                                    logger.info(f"[AGENT5 TRACE] script['{part_name}'] visual_guidance preview: {visual_preview}")
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
                        # Verify object exists before generating presigned URL
                        try:
                            storage_service.s3_client.head_object(
                                Bucket=storage_service.bucket_name,
                                Key=key
                            )
                            audio_url = storage_service.generate_presigned_url(key, expires_in=86400)
                            audio_files.append({
                                "part": part,
                                "url": audio_url,
                                "s3_key": key,  # Store S3 key for error handling
                                "duration": 5.0  # Default duration, could be extracted from metadata
                            })
                            logger.debug(f"Added audio file for part '{part}': {key}")
                        except Exception as e:
                            logger.warning(f"Failed to verify/generate URL for audio file {key}: {e}")
                            # Continue with other files
                elif "background_music" in key.lower() or "music" in key.lower():
                    # Verify object exists before generating presigned URL
                    try:
                        storage_service.s3_client.head_object(
                            Bucket=storage_service.bucket_name,
                            Key=key
                        )
                        background_music_url = storage_service.generate_presigned_url(key, expires_in=86400)
                        background_music = {
                            "url": background_music_url,
                            "s3_key": key,  # Store S3 key for error handling
                            "duration": 60  # Default duration
                        }
                        logger.debug(f"Added background music: {key}")
                    except Exception as e:
                        logger.warning(f"Failed to verify/generate URL for background music {key}: {e}")
                        # Continue without background music
            
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
                logger.info(f"Agent5 loaded storyboard with {len(storyboard.get('segments', []))} segments")
            else:
                logger.info("Agent5 did not find storyboard, using script data only")
                
        except Exception as e:
            logger.error(f"Agent5 failed to scan S3 folders: {e}")
            raise ValueError(f"Failed to discover Agent2/Agent4 content from S3: {str(e)}")

        # Create temp directory for assets
        temp_dir = tempfile.mkdtemp(prefix="agent5_")

        # Build visual prompts and segment durations for each section
        sections = ["hook", "concept", "process", "conclusion"]
        visual_prompts = {}  # Store prompts for parallel generation
        segment_durations = {}  # Store segment durations (in seconds)

        for part in sections:
            # Get section data and visual prompt
            section_data = script.get(part, {})
            # Check for both visual_prompt and visual_guidance (Agent 2 uses visual_guidance)
            visual_prompt = section_data.get("visual_prompt", "") or section_data.get("visual_guidance", "")

            # Debug logging for prompt verification
            logger.info(f"[VISUAL PROMPT TRACE] Section '{part}' - section_data keys: {list(section_data.keys())}")
            logger.info(f"[VISUAL PROMPT TRACE] Section '{part}' - visual_prompt from script: '{visual_prompt[:100] if visual_prompt else '(empty)'}'")
            logger.info(f"[VISUAL PROMPT TRACE] Section '{part}' - duration from script: {section_data.get('duration', '(not set)')}")

            # Also log text and visual_guidance if present
            if "text" in section_data:
                logger.info(f"[VISUAL PROMPT TRACE] Section '{part}' - text preview: {section_data['text'][:100] if section_data['text'] else '(empty)'}")
            if "visual_guidance" in section_data:
                logger.info(f"[VISUAL PROMPT TRACE] Section '{part}' - visual_guidance: {section_data['visual_guidance'][:100] if section_data['visual_guidance'] else '(empty)'}")

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
                        logger.info(f"[VISUAL PROMPT TRACE] Found storyboard segment for '{part}': {segment_type}")
                        # Use visual_guidance from storyboard if available
                        storyboard_visual = storyboard_segment.get("visual_guidance", "")
                        logger.info(f"[VISUAL PROMPT TRACE] Storyboard visual_guidance for '{part}': {storyboard_visual[:100] if storyboard_visual else '(empty)'}")
                        if storyboard_visual and not visual_prompt:
                            visual_prompt = storyboard_visual
                            logger.info(f"[VISUAL PROMPT TRACE] Using storyboard visual_guidance as visual_prompt for '{part}'")
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

            # Store segment duration (from storyboard or script, with defaults)
            duration_str = section_data.get("duration")
            if duration_str:
                try:
                    segment_durations[part] = float(duration_str)
                except (ValueError, TypeError):
                    # Fallback to defaults if duration is invalid
                    default_durations = {"hook": 10.0, "concept": 15.0, "process": 20.0, "conclusion": 15.0}
                    segment_durations[part] = default_durations.get(part, 15.0)
            else:
                # Use default segment durations from segments.md
                default_durations = {"hook": 10.0, "concept": 15.0, "process": 20.0, "conclusion": 15.0}
                segment_durations[part] = default_durations.get(part, 15.0)

            # Log the visual prompt and duration for verification
            logger.info(f"[{session_id}] Section '{part}' visual prompt: {visual_prompt[:100]}...")
            logger.info(f"[{session_id}] Section '{part}' duration: {segment_durations[part]}s")

        # Generate all videos in parallel using asyncio.gather
        # Track completion for progress updates
        completed_videos = []
        
        # Cost tracking
        # Minimax video-01: ~$0.035 per 5-6 second clip
        COST_PER_CLIP = 0.035  # USD per clip (5-6 seconds)
        # Note: total_cost and cost_per_section are already initialized at function start (line 453-454)

        # Constants for video generation
        CLIP_DURATION = 6.0  # Minimax generates 6-second clips
        
        # Rate limiting: Max 4 concurrent Replicate API calls to avoid overwhelming the service
        MAX_CONCURRENT_REPLICATE_CALLS = 4
        replicate_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REPLICATE_CALLS)

        # Calculate clips needed per section based on segment durations
        clips_per_section = {}
        for section in sections:
            # Use segment duration (from storyboard/script or defaults)
            segment_duration = segment_durations[section]
            clips_needed = max(1, math.ceil(segment_duration / CLIP_DURATION))
            clips_per_section[section] = clips_needed
            logger.info(f"[{session_id}] Section '{section}': {segment_duration}s → {clips_needed} clips ({CLIP_DURATION}s each)")

        total_clips = sum(clips_per_section.values())
        
        # Define video generation function (used only if not restarting)
        async def generate_section_video(section: str) -> tuple[str, List[str]]:
            """Generate multiple video clips for a section and return (section, list_of_clip_paths)"""
            import httpx

            prompt = visual_prompts[section]
            clips_needed = clips_per_section[section]

            logger.info(f"[{session_id}] Generating {clips_needed} clips for section '{section}'")
            logger.info(f"[{session_id}] Using prompt for '{section}': {prompt[:150]}...")

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

            # Sanitize the base prompt to remove text-triggering keywords
            prompt_sanitized = sanitize_video_prompt(prompt)
            logger.info(f"[{session_id}] Original prompt for '{section}': {prompt[:150]}")
            logger.info(f"[{session_id}] Sanitized prompt for '{section}': {prompt_sanitized[:150]}")

            # Build consistency anchor (keep visual-only elements)
            consistency_anchor = ""
            if style or setting or teacher_desc or students_desc:
                consistency_parts = []
                if style:
                    # Sanitize style to remove any text references
                    style_sanitized = sanitize_video_prompt(style)
                    consistency_parts.append(style_sanitized)
                if setting:
                    # Sanitize setting
                    setting_sanitized = sanitize_video_prompt(setting)
                    # Limit setting length to avoid overly long prompts
                    setting_words = setting_sanitized.split()[:30]  # Max 30 words for setting
                    consistency_parts.append(f"Setting: {' '.join(setting_words)}")
                if teacher_desc:
                    # Keep teacher description concise and visual-only
                    teacher_words = teacher_desc.split()[:20]  # Max 20 words
                    consistency_parts.append(f"Teacher: {' '.join(teacher_words)}")
                if students_desc:
                    # Keep students description concise
                    students_words = students_desc.split()[:20]  # Max 20 words
                    consistency_parts.append(f"Students: {' '.join(students_words)}")
                consistency_anchor = " | ".join(consistency_parts) + " | "

            # Generate progressive prompts for each clip position
            # Keep prompts concise - Minimax works best with shorter, focused prompts
            clip_prompts = []
            for i in range(clips_needed):
                # Create clip-specific temporal and action cues based on position
                if clips_needed == 1:
                    # Single clip: use sanitized prompt with visual-only modifiers
                    clip_prompt = f"{consistency_anchor}{prompt_sanitized}, smooth cinematic movement, clean animation"
                elif i == 0:
                    # First clip: Opening/beginning of action (keep concise)
                    clip_prompt = f"{consistency_anchor}OPENING SHOT: {prompt_sanitized}, camera slowly pushes in, characters beginning action, clean visual composition"
                elif i == clips_needed - 1:
                    # Final clip: Conclusion of action (keep concise)
                    clip_prompt = f"{consistency_anchor}FINAL SHOT: {prompt_sanitized}, camera holds steady, characters completing action, same composition as previous clip"
                else:
                    # Middle clips: Progression of action (keep concise)
                    clip_prompt = f"{consistency_anchor}SHOT {i+1}: {prompt_sanitized}, camera maintains angle, characters mid-action, continuous motion"

                clip_prompts.append(clip_prompt)

            # Generate deterministic seed for this section
            # Use hash of section name to get consistent seed per section
            import hashlib
            section_hash = int(hashlib.md5(section.encode()).hexdigest()[:8], 16)
            section_seed = section_hash % 100000  # Keep seed in reasonable range

            logger.info(f"[{session_id}] Using seed {section_seed} for all clips in {section}")

            # Generate clips sequentially with continuity (image-to-video for clips 2+)
            generated_clips = []
            previous_clip_url = None

            for clip_idx, clip_prompt in enumerate(clip_prompts):
                async with replicate_semaphore:
                    if clip_idx == 0:
                        # First clip: text-to-video
                        logger.info(f"[{session_id}] Generating clip {clip_idx+1}/{clips_needed} (text-to-video)")
                        clip_url = await generate_video_replicate(
                            clip_prompt,
                            replicate_api_key,
                            model="minimax",
                            seed=section_seed
                        )
                    else:
                        # Subsequent clips: extract last frame from previous clip, then image-to-video
                        logger.info(f"[{session_id}] Generating clip {clip_idx+1}/{clips_needed} (image-to-video with continuity)")

                        # Extract last frame as base64 from previous clip
                        frame_data_uri = await extract_last_frame_as_base64(previous_clip_url)

                        # Generate next clip from the frame
                        service = ReplicateVideoService(replicate_api_key)
                        clip_url = await service.generate_video_from_image(
                            prompt=clip_prompt,
                            image_url=frame_data_uri,
                            model="minimax",
                            seed=section_seed
                        )

                    generated_clips.append(clip_url)
                    previous_clip_url = clip_url

            # Calculate cost for this section
            section_cost = len(generated_clips) * COST_PER_CLIP
            cost_per_section[section] = section_cost

            # Update progress with cost info
            for clip_idx in range(len(generated_clips)):
                completed_videos.append(f"{section}_{clip_idx}")
                # Calculate current total cost for progress updates
                current_total_cost = sum(cost_per_section.values())
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
                    },
                    cost=current_total_cost,
                    cost_breakdown=cost_per_section
                )

            # Download and verify all clips with retry logic
            MAX_CLIP_RETRIES = 2
            COST_PER_CLIP = 0.09  # ~$0.035/6s for Minimax + padding
            clip_paths = []

            async with httpx.AsyncClient(timeout=120.0) as client:
                for i, clip_url in enumerate(generated_clips):
                    clip_verified = False
                    failed_check_names = []

                    for retry_attempt in range(MAX_CLIP_RETRIES + 1):
                        try:
                            # Download clip
                            response = await client.get(clip_url)
                            response.raise_for_status()
                            clip_path = os.path.join(temp_dir, f"{section}_clip_{i}.mp4")
                            with open(clip_path, 'wb') as f:
                                f.write(response.content)

                            # VERIFY CLIP (includes all 8 checks: file, duration, resolution, frames, audio, integrity, visual, text)
                            logger.info(f"[{session_id}] Verifying {section} clip {i + 1}/{len(generated_clips)}...")
                            verification_result = await video_verifier.verify_clip(
                                video_url=clip_path,
                                expected_duration=6.0,  # Minimax generates 6-second clips
                                clip_index=i
                            )

                            if verification_result.passed:
                                # SUCCESS - Clip verified, save and continue
                                clip_paths.append(clip_path)

                                # Save verified clip to S3 for restart capability
                                clip_s3_key = f"users/{user_id}/{session_id}/agent5/{section}_clip_{i}.mp4"
                                try:
                                    with open(clip_path, 'rb') as f:
                                        clip_content = f.read()
                                    storage_service.upload_file_direct(clip_content, clip_s3_key, "video/mp4")
                                    logger.info(f"[{session_id}] ✓ Clip {i + 1} verified and saved for {section}")
                                except Exception as e:
                                    logger.warning(f"[{session_id}] Failed to save clip to S3 {clip_s3_key}: {e}")

                                clip_verified = True
                                break
                            else:
                                # VERIFICATION FAILED
                                failed_check_names = [c.check_name for c in verification_result.failed_checks]
                                logger.warning(
                                    f"[{session_id}] Clip {i + 1} for {section} failed verification: {failed_check_names} "
                                    f"(attempt {retry_attempt + 1}/{MAX_CLIP_RETRIES + 1})"
                                )

                                if retry_attempt < MAX_CLIP_RETRIES:
                                    # REGENERATE CLIP
                                    logger.info(f"[{session_id}] Regenerating {section} clip {i + 1}...")

                                    # Get the clip prompt (need to reconstruct it)
                                    clip_prompt = clip_prompts[i]

                                    # Enhanced prompt if text was detected
                                    if any('text' in check_name for check_name in failed_check_names):
                                        clip_prompt = f"NO TEXT, NO CAPTIONS, NO OVERLAYS, PURE VISUAL ANIMATION: {clip_prompt}"
                                        logger.info(f"[{session_id}] Using enhanced anti-text prompt for retry")

                                    # Regenerate clip with same logic as original generation
                                    async with replicate_semaphore:
                                        if i == 0:
                                            # First clip: text-to-video
                                            clip_url = await generate_video_replicate(
                                                clip_prompt,
                                                replicate_api_key,
                                                model="minimax",
                                                seed=section_seed
                                            )
                                        else:
                                            # Subsequent clips: extract last frame from previous clip, then image-to-video
                                            previous_clip_url = clip_url if retry_attempt > 0 else generated_clips[i - 1]
                                            frame_data_uri = await extract_last_frame_as_base64(previous_clip_url)

                                            service = ReplicateVideoService(replicate_api_key)
                                            clip_url = await service.generate_video_from_image(
                                                prompt=clip_prompt,
                                                image_url=frame_data_uri,
                                                model="minimax",
                                                seed=section_seed
                                            )

                                    # Track retry cost
                                    cost_per_section[section] += COST_PER_CLIP
                                    current_total_cost += COST_PER_CLIP

                                    # Send status update about retry
                                    await send_status(
                                        "Agent5", "processing",
                                        supersessionID=supersessionid,
                                        message=f"Regenerating {section} clip {i + 1} (retry {retry_attempt + 1})",
                                        cost=current_total_cost,
                                        cost_breakdown=cost_per_section
                                    )

                                    await asyncio.sleep(2)  # Brief delay before retry
                                    continue

                        except Exception as e:
                            logger.error(f"[{session_id}] Error processing clip {i + 1} for {section} (attempt {retry_attempt + 1}): {e}")
                            if retry_attempt < MAX_CLIP_RETRIES:
                                await asyncio.sleep(2)
                                continue

                    if not clip_verified:
                        raise RuntimeError(
                            f"Failed to generate valid clip {i + 1} for {section} after {MAX_CLIP_RETRIES + 1} attempts. "
                            f"Failed checks: {failed_check_names}"
                        )

            logger.info(f"[{session_id}] Downloaded and saved {len(generated_clips)} clips for {section}")

            return (section, clip_paths)
        
        # Handle restart mode: download existing clips from S3
        all_clip_paths = []
        if restart_from_concat:
            logger.info(f"[{session_id}] Restart mode: Downloading existing clips from S3")
            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message="Restart mode: Loading existing clips from S3...",
                cost=0.0
            )
            
            agent5_prefix = f"users/{user_id}/{session_id}/agent5/"
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=False) as client:
                for section in sections:
                    section_clips = []
                    clip_index = 0
                    while True:
                        clip_s3_key = f"{agent5_prefix}{section}_clip_{clip_index}.mp4"
                        try:
                            # Check if clip exists in S3
                            storage_service.s3_client.head_object(
                                Bucket=storage_service.bucket_name,
                                Key=clip_s3_key
                            )
                            # Download clip with fallback URLs
                            clip_urls = storage_service.generate_s3_url_with_fallback(clip_s3_key)
                            clip_downloaded = False
                            for clip_url in clip_urls:
                                try:
                                    response = await client.get(clip_url)
                                    # Handle redirects manually
                                    if response.status_code in [301, 302, 303, 307, 308]:
                                        redirect_url = response.headers.get('Location')
                                        response = await client.get(redirect_url)
                                    response.raise_for_status()
                                    clip_path = os.path.join(temp_dir, f"{section}_clip_{clip_index}.mp4")
                                    with open(clip_path, 'wb') as f:
                                        f.write(response.content)
                                    section_clips.append(clip_path)
                                    clip_index += 1
                                    clip_downloaded = True
                                    break
                                except Exception:
                                    continue
                            if not clip_downloaded:
                                # No more clips for this section
                                break
                        except Exception:
                            # No more clips for this section
                            break
                    
                    if not section_clips:
                        raise ValueError(f"No clips found in S3 for section: {section}")
                    
                    all_clip_paths.extend(section_clips)
                    logger.info(f"[{session_id}] Loaded {len(section_clips)} clips for {section} from S3")
            
            logger.info(f"[{session_id}] Restart mode: Loaded {len(all_clip_paths)} total clips from S3")
            total_cost = 0.0  # No cost for restart (clips already generated)
        else:
            # Generate all videos in parallel (fully parallelized)
            logger.info(f"[{session_id}] Generating all {len(sections)} sections in parallel")

            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message=f"Generating all {len(sections)} videos in parallel...",
                cost=0.0
            )

            # Process all sections in parallel
            section_results = await asyncio.gather(
                *[generate_section_video(section) for section in sections]
            )

            # Collect all clip paths in order (hook, concept, process, conclusion)
            for section in sections:
                # Find the result for this section
                section_result = next((result for result in section_results if result[0] == section), None)
                if section_result:
                    section_name, clip_paths = section_result
                    all_clip_paths.extend(clip_paths)

        # Calculate final total cost (only if not restart mode)
        if not restart_from_concat:
            total_cost = sum(cost_per_section.values())
            logger.info(f"[{session_id}] Completed all sections. Total cost: ${total_cost:.4f}")

            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message=f"All clips generated ({len(all_clip_paths)} total). Starting audio/video concatenation...",
                cost=total_cost,
                cost_breakdown=cost_per_section
            )
        else:
            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message=f"Restart mode: Loaded {len(all_clip_paths)} clips. Starting concatenation...",
                cost=0.0
            )

        # ====================
        # AUDIO CONCATENATION
        # ====================

        # Track if we need to regenerate audio (separate from restart_from_concat flag)
        need_to_regenerate_audio = True
        
        if restart_from_concat:
            # In restart mode, try to download existing final audio from S3
            logger.info(f"[{session_id}] Restart mode: Attempting to load existing final audio from S3")
            final_audio_s3_key = f"users/{user_id}/{session_id}/agent5/final_audio.mp3"
            final_audio_path = os.path.join(temp_dir, "final_audio.mp3")
            
            try:
                # Check if final audio exists in S3
                storage_service.s3_client.head_object(
                    Bucket=storage_service.bucket_name,
                    Key=final_audio_s3_key
                )
                # Download existing final audio with fallback URLs
                audio_urls = storage_service.generate_s3_url_with_fallback(final_audio_s3_key)
                audio_downloaded = False
                async with httpx.AsyncClient(timeout=120.0, follow_redirects=False) as client:
                    for audio_url in audio_urls:
                        try:
                            response = await client.get(audio_url)
                            # Handle redirects manually
                            if response.status_code in [301, 302, 303, 307, 308]:
                                redirect_url = response.headers.get('Location')
                                response = await client.get(redirect_url)
                            response.raise_for_status()
                            with open(final_audio_path, 'wb') as f:
                                f.write(response.content)
                            logger.info(f"[{session_id}] Restart mode: Loaded existing final audio from S3")
                            audio_downloaded = True
                            break
                        except Exception:
                            continue
                
                if audio_downloaded:
                    need_to_regenerate_audio = False  # Audio loaded successfully, skip regeneration
                else:
                    raise Exception("Failed to download final audio from all fallback URLs")
            except Exception as e:
                logger.warning(f"[{session_id}] Restart mode: Could not load existing audio, regenerating: {e}")
                # Fall through to normal audio processing
                need_to_regenerate_audio = True  # Need to regenerate audio
        
        if need_to_regenerate_audio:
            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message="Step 1/4: Creating timed narration track (60-second timeline)...",
                cost=total_cost,
                cost_breakdown=cost_per_section
            )

            # Download all audio files to temp directory (reuse single HTTP client)
            import httpx
            audio_file_paths = []
            # Disable follow_redirects and handle redirects manually to avoid 301 errors
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=False) as client:
                for audio_file in audio_files:
                    part = audio_file["part"]
                    url = audio_file["url"]
                    s3_key = audio_file.get("s3_key", "unknown")
                    
                    downloaded = False
                    last_error = None
                    
                    # Get all possible URLs (including fallbacks)
                    all_urls = [url] + storage_service.generate_s3_url_with_fallback(s3_key)
                    # Remove duplicates while preserving order
                    seen = set()
                    urls_to_try = []
                    for u in all_urls:
                        if u not in seen:
                            seen.add(u)
                            urls_to_try.append(u)
                    
                    # Try each URL until one works
                    for attempt_url in urls_to_try:
                        try:
                            logger.debug(f"[{session_id}] Downloading audio for part '{part}' from {attempt_url}")
                            response = await client.get(attempt_url)
                            
                            # Handle redirects manually
                            if response.status_code in [301, 302, 303, 307, 308]:
                                redirect_url = response.headers.get('Location')
                                logger.debug(f"[{session_id}] Got redirect to: {redirect_url}, following...")
                                response = await client.get(redirect_url)
                            
                            response.raise_for_status()
                            audio_path = os.path.join(temp_dir, f"audio_{part}.mp3")
                            with open(audio_path, 'wb') as f:
                                f.write(response.content)
                            audio_file_paths.append(audio_path)
                            logger.info(f"[{session_id}] Successfully downloaded audio for part '{part}' ({len(response.content)} bytes)")
                            downloaded = True
                            break
                        except Exception as e:
                            logger.debug(f"[{session_id}] URL failed: {attempt_url} - {e}")
                            last_error = e
                            continue
                    
                    if not downloaded:
                        logger.error(f"[{session_id}] Failed to download audio for part '{part}' after trying {len(urls_to_try)} URLs")
                        raise ValueError(f"Failed to download audio file for part '{part}' from S3. Last error: {last_error}")

            # Create timed narration track (places narrations at 0s, 15s, 30s, 45s across 60s timeline)
            timed_narration_path = os.path.join(temp_dir, "timed_narration.mp3")
            await create_timed_narration_track(audio_file_paths, timed_narration_path, total_duration=60.0)
            logger.info(f"[{session_id}] Created timed narration track with {len(audio_file_paths)} narrations across 60 seconds")

            # ====================
            # AUDIO MIXING
            # ====================

            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message="Step 2/4: Mixing narration with background music...",
                cost=total_cost,
                cost_breakdown=cost_per_section
            )

            # Download background music
            background_music_url = background_music.get("url", "")
            if background_music_url:
                background_music_s3_key = background_music.get("s3_key", "unknown")
                # Disable follow_redirects and handle redirects manually to avoid 301 errors
                async with httpx.AsyncClient(timeout=120.0, follow_redirects=False) as client:
                    music_downloaded = False
                    
                    # Get all possible URLs (including fallbacks)
                    all_urls = [background_music_url] + storage_service.generate_s3_url_with_fallback(background_music_s3_key)
                    # Remove duplicates while preserving order
                    seen = set()
                    urls_to_try = []
                    for u in all_urls:
                        if u not in seen:
                            seen.add(u)
                            urls_to_try.append(u)
                    
                    # Try each URL until one works
                    for attempt_url in urls_to_try:
                        try:
                            logger.debug(f"[{session_id}] Downloading background music from {attempt_url}")
                            response = await client.get(attempt_url)
                            
                            # Handle redirects manually
                            if response.status_code in [301, 302, 303, 307, 308]:
                                redirect_url = response.headers.get('Location')
                                logger.debug(f"[{session_id}] Got redirect to: {redirect_url}, following...")
                                response = await client.get(redirect_url)
                            
                            response.raise_for_status()
                            background_music_path = os.path.join(temp_dir, "background_music.mp3")
                            with open(background_music_path, 'wb') as f:
                                f.write(response.content)
                            logger.info(f"[{session_id}] Successfully downloaded background music ({len(response.content)} bytes)")
                            music_downloaded = True
                            break
                        except Exception as e:
                            logger.debug(f"[{session_id}] URL failed for background music: {attempt_url} - {e}")
                            continue
                    
                    if not music_downloaded:
                        logger.warning(f"[{session_id}] All download attempts failed for background music, continuing without it")
                        background_music_url = ""  # Continue without background music

                # Mix timed narration with background music
                final_audio_path = os.path.join(temp_dir, "final_audio.mp3")
                await mix_audio_with_background(
                    timed_narration_path,
                    background_music_path,
                    final_audio_path,
                    music_volume=0.3
                )
                logger.info(f"[{session_id}] Mixed timed narration with background music")
                
                # Save final audio to S3 for future restarts
                try:
                    with open(final_audio_path, 'rb') as f:
                        audio_content = f.read()
                    final_audio_s3_key = f"users/{user_id}/{session_id}/agent5/final_audio.mp3"
                    storage_service.upload_file_direct(audio_content, final_audio_s3_key, "audio/mpeg")
                    logger.debug(f"[{session_id}] Saved final audio to S3: {final_audio_s3_key}")
                except Exception as e:
                    logger.warning(f"[{session_id}] Failed to save final audio to S3: {e}")
            else:
                # No background music, use timed narration as-is
                final_audio_path = timed_narration_path
                logger.info(f"[{session_id}] No background music, using timed narration only")
                
                # Save final audio to S3 for future restarts
                try:
                    with open(final_audio_path, 'rb') as f:
                        audio_content = f.read()
                    final_audio_s3_key = f"users/{user_id}/{session_id}/agent5/final_audio.mp3"
                    storage_service.upload_file_direct(audio_content, final_audio_s3_key, "audio/mpeg")
                    logger.debug(f"[{session_id}] Saved final audio to S3: {final_audio_s3_key}")
                except Exception as e:
                    logger.warning(f"[{session_id}] Failed to save final audio to S3: {e}")

        # ====================
        # VIDEO CONCATENATION
        # ====================

        step_num = "3/4" if not restart_from_concat else "1/2"
        await send_status(
            "Agent5", "processing",
            supersessionID=supersessionid,
            message=f"Step {step_num}: Concatenating all {len(all_clip_paths)} video clips...",
            cost=total_cost if not restart_from_concat else 0.0,
            cost_breakdown=cost_per_section if not restart_from_concat else {}
        )

        # Concatenate all video clips
        concatenated_video_path = os.path.join(temp_dir, "concatenated_video.mp4")
        await concatenate_all_video_clips(all_clip_paths, concatenated_video_path)
        logger.info(f"[{session_id}] Concatenated {len(all_clip_paths)} video clips")

        # ====================
        # FINAL VIDEO + AUDIO COMBINATION
        # ====================

        step_num = "4/4" if not restart_from_concat else "2/2"
        await send_status(
            "Agent5", "processing",
            supersessionID=supersessionid,
            message=f"Step {step_num}: Combining video and audio...",
            cost=total_cost if not restart_from_concat else 0.0,
            cost_breakdown=cost_per_section if not restart_from_concat else {}
        )

        # Combine video and audio
        output_path = os.path.join(temp_dir, "output.mp4")
        await combine_video_and_audio(
            concatenated_video_path,
            final_audio_path,
            output_path
        )
        logger.info(f"[{session_id}] Combined video and audio into final output")

        # VERIFY FINAL VIDEO before upload
        logger.info(f"[{session_id}] Verifying final composed video...")
        final_verification_result = await video_verifier.verify_final_video(
            video_url=output_path,
            expected_duration=60.0  # Expected 60-second final video
        )

        if final_verification_result.failed:
            failed_checks = [c.check_name for c in final_verification_result.failed_checks]
            logger.error(
                f"[{session_id}] Final video failed verification: {failed_checks}"
            )
            for check in final_verification_result.failed_checks:
                logger.error(f"  - {check.check_name}: {check.message}")

            raise RuntimeError(
                f"Final video quality check failed: {failed_checks}. "
                "Cannot upload video that does not meet quality standards."
            )
        else:
            logger.info(f"[{session_id}] ✓ Final video passed all 8 verification checks")

        # Upload video to S3 - use users/{userId}/{sessionId}/final/ path
        import uuid
        video_filename = f"final_video_{uuid.uuid4().hex[:8]}.mp4"
        video_s3_key = f"users/{user_id}/{session_id}/final/{video_filename}"

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

        # Report finished status with video link and cost
        await send_status(
            "Agent5", "finished",
            supersessionID=supersessionid,
            videoUrl=video_url,
            progress=100,
            cost=total_cost if not restart_from_concat else 0.0,
            cost_breakdown=cost_per_section if not restart_from_concat else {}
        )
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "finished",
            "timestamp": int(time.time() * 1000),
            "videoUrl": video_url,
            "cost": total_cost,
            "cost_breakdown": cost_per_section
        }
        await create_status_json("5", "finished", status_data)

        return video_url

    except Exception as e:
        # Report error status with cost information (even if failed)
        error_kwargs = {
            "error": str(e),
            "reason": f"Agent5 failed: {type(e).__name__}",
            "supersessionID": supersessionid if 'supersessionid' in locals() else None
        }
        
        # Include cost information (always available, initialized at function start)
        error_kwargs["cost"] = total_cost
        if cost_per_section:
            error_kwargs["cost_breakdown"] = cost_per_section
        
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
