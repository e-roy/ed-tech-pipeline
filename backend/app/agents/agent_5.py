"""
Agent 5 - Video Generator using FFmpeg

Generates a 60-second video from pipeline data:
1. Generates AI videos sequentially using Replicate (Kling v1.5 Pro)
2. Downloads and concatenates all narration audio files
3. Mixes concatenated narration with background music
4. Concatenates all video clips into one video
5. Combines final video with final audio
6. Uploads final video to S3

Uses Kling v1.5 Pro for AI-generated video clips (~$0.15/5s video)
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
from app.agents.helpers.replicate_gemini_generator import ReplicateGeminiGenerator


async def generate_video_replicate(
    prompt: str,
    api_key: str,
    model: str = "veo3",
    progress_callback: Optional[callable] = None,
    seed: Optional[int] = None
) -> str:
    """
    Generate a video using Replicate (Google Veo 3 by default).

    Args:
        prompt: Visual description for the video
        api_key: Replicate API key
        model: Model to use ("veo3", "kling", "minimax", "luma")
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
    Includes validation and multiple fallback strategies.

    Args:
        video_url: URL to the video file

    Returns:
        Base64 data URI string (data:image/png;base64,...)
    """
    import base64
    import io
    import httpx
    from PIL import Image

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
        # Try multiple extraction strategies in order of preference
        strategies = [
            # Strategy 1: Extract from 0.1s before end (safer than 0.033s)
            {
                "name": "0.1s before end",
                "cmd": ["ffmpeg", "-sseof", "-0.1", "-i", temp_video_path,
                       "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"]
            },
            # Strategy 2: Extract from 0.5s before end (even safer)
            {
                "name": "0.5s before end",
                "cmd": ["ffmpeg", "-sseof", "-0.5", "-i", temp_video_path,
                       "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"]
            },
            # Strategy 3: Extract last keyframe
            {
                "name": "last keyframe",
                "cmd": ["ffmpeg", "-i", temp_video_path, "-vf", "select='eq(pict_type,I)'",
                       "-vsync", "vfr", "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"]
            }
        ]

        for strategy in strategies:
            logger.info(f"Trying frame extraction strategy: {strategy['name']}")

            result = subprocess.run(strategy["cmd"], capture_output=True, check=False)

            if result.returncode != 0:
                logger.warning(f"Strategy '{strategy['name']}' failed: {result.stderr.decode()[:200]}")
                continue

            # Check if we got any output
            if not result.stdout or len(result.stdout) < 100:
                logger.warning(f"Strategy '{strategy['name']}' returned empty/tiny output ({len(result.stdout)} bytes)")
                continue

            # Validate it's a valid PNG using PIL
            try:
                img = Image.open(io.BytesIO(result.stdout))
                width, height = img.size
                logger.info(f"Strategy '{strategy['name']}' succeeded: {width}x{height} PNG ({len(result.stdout)} bytes)")

                # Verify minimum dimensions (avoid 1x1 or corrupt images)
                if width < 10 or height < 10:
                    logger.warning(f"Strategy '{strategy['name']}' produced tiny image: {width}x{height}")
                    continue

                # Convert to base64 data URI
                frame_b64 = base64.b64encode(result.stdout).decode('utf-8')
                data_uri = f"data:image/png;base64,{frame_b64}"

                logger.info(f"Successfully extracted valid frame ({len(frame_b64)} chars)")
                return data_uri

            except Exception as e:
                logger.warning(f"Strategy '{strategy['name']}' produced invalid PNG: {e}")
                continue

        # All strategies failed
        raise RuntimeError(
            f"All frame extraction strategies failed. Tried: {', '.join(s['name'] for s in strategies)}"
        )

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


async def _download_with_fallback(
    primary_url: str,
    s3_key: str,
    output_path: str,
    storage_service: StorageService,
    client: httpx.AsyncClient,
    session_id: str,
    file_description: str = "file"
) -> bool:
    """
    Download a file from S3 with fallback URLs and redirect handling.

    Args:
        primary_url: Primary presigned URL
        s3_key: S3 key for generating fallback URLs
        output_path: Local path to save downloaded file
        storage_service: Storage service instance
        client: httpx client (should have follow_redirects=False)
        session_id: Session ID for logging
        file_description: Description for logging (e.g., "audio for hook", "background music")

    Returns:
        True if download succeeded, False otherwise
    """
    # Get all possible URLs (including fallbacks)
    all_urls = [primary_url] + storage_service.generate_s3_url_with_fallback(s3_key)

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
            logger.debug(f"[{session_id}] Downloading {file_description} from {attempt_url[:100]}...")
            response = await client.get(attempt_url)

            # Handle redirects manually
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location')
                logger.debug(f"[{session_id}] Got redirect to: {redirect_url[:100]}..., following...")
                response = await client.get(redirect_url)

            response.raise_for_status()

            with open(output_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"[{session_id}] Successfully downloaded {file_description} ({len(response.content)} bytes)")
            return True

        except Exception as e:
            logger.debug(f"[{session_id}] URL failed: {attempt_url[:100]}... - {e}")
            continue

    logger.error(f"[{session_id}] Failed to download {file_description} after trying {len(urls_to_try)} URLs")
    return False


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
    restart_from_concat: bool = False,  # Skip generation, reuse existing clips from S3
    model: str = "wan-video/wan-2.2-i2v-fast"  # Video generation model: "veo3", "kling", "minimax", "luma", "wan-video/wan-2.2-i2v-fast" 
) -> Optional[str]:
    """
    Agent5: Video generation agent using FFmpeg.

    Generates a complete video by:
    1. Generating AI video clips sequentially using Replicate (configurable model)
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
            - storyboard: Storyboard with segments containing narration, visual_scene, etc.
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

        # Scan S3 folders for Agent3 and Agent4 content
        agent3_prefix = f"users/{user_id}/{session_id}/agent3/"
        agent4_prefix = f"users/{user_id}/{session_id}/agent4/"

        storyboard = {}
        audio_files = []
        background_music = {}

        # Initialize agent data variables at function scope (needed for nested functions)
        agent_3_data = {}
        agent_4_data = {}

        try:
            # Load agent_3_data.json (storyboard is the single source of truth)
            agent_3_data_key = f"{agent3_prefix}agent_3_data.json"
            try:
                obj = storage_service.s3_client.get_object(
                    Bucket=storage_service.bucket_name,
                    Key=agent_3_data_key
                )
                content = obj["Body"].read().decode('utf-8')
                agent_3_data = json.loads(content)
                logger.info(f"Agent5 loaded agent_3_data.json from {agent_3_data_key}")

                # Extract storyboard (contains all script data in segments)
                if agent_3_data.get("storyboard"):
                    storyboard = agent_3_data["storyboard"]
                    logger.info(f"Agent5 loaded storyboard with {len(storyboard.get('segments', []))} segments")

                    # Log segment info for debugging
                    for seg in storyboard.get("segments", []):
                        seg_type = seg.get("type", "unknown")
                        narration_preview = seg.get("narration", "")[:100] if seg.get("narration") else "(empty)"
                        logger.debug(f"[AGENT5] Segment '{seg_type}': {narration_preview}...")

            except Exception as e:
                logger.warning(f"Agent5 could not load agent_3_data.json: {e}")

            # If pipeline_data is provided, use it (for backwards compatibility)
            if pipeline_data:
                agent_3_data = pipeline_data.get("agent_3_data", agent_3_data)
                agent_4_data = pipeline_data.get("agent_4_data", {})

                if agent_3_data.get("storyboard"):
                    storyboard = agent_3_data["storyboard"]
                elif pipeline_data.get("storyboard"):
                    storyboard = pipeline_data["storyboard"]

                audio_files = agent_4_data.get("audio_files", audio_files)
                background_music = agent_4_data.get("background_music", background_music)

                if not audio_files:
                    audio_data = pipeline_data.get("audio_data", {})
                    audio_files = audio_data.get("audio_files", audio_files)
                    background_music = audio_data.get("background_music", background_music)

            # Validate storyboard
            if not storyboard or not storyboard.get("segments"):
                raise ValueError("No storyboard data found in S3 or pipeline_data")

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
                                "s3_key": key,
                                "duration": 5.0
                            })
                            logger.debug(f"Added audio file for part '{part}': {key}")
                        except Exception as e:
                            logger.warning(f"Failed to verify/generate URL for audio file {key}: {e}")
                elif "background_music" in key.lower() or "music" in key.lower():
                    try:
                        storage_service.s3_client.head_object(
                            Bucket=storage_service.bucket_name,
                            Key=key
                        )
                        background_music_url = storage_service.generate_presigned_url(key, expires_in=86400)
                        background_music = {
                            "url": background_music_url,
                            "s3_key": key,
                            "duration": 60
                        }
                        logger.debug(f"Added background music: {key}")
                    except Exception as e:
                        logger.warning(f"Failed to verify/generate URL for background music {key}: {e}")

            if not audio_files:
                raise ValueError("No audio files found in S3 or pipeline_data")

        except Exception as e:
            logger.error(f"Agent5 failed to scan S3 folders: {e}")
            raise ValueError(f"Failed to discover Agent3/Agent4 content from S3: {str(e)}")

        # Create temp directory for assets
        temp_dir = tempfile.mkdtemp(prefix="agent5_")

        # Build visual scenes and segment durations for each section from storyboard
        sections = ["hook", "concept", "process", "conclusion"]
        visual_scenes = {}  # Store visual_scene objects for image generation
        section_seeds = {}  # Store seeds for consistency
        segment_durations = {}  # Store segment durations (in seconds)

        # Map section keys to storyboard segment types
        segment_type_map = {
            "hook": "hook",
            "concept": "concept_introduction",
            "process": "process_explanation",
            "conclusion": "conclusion"
        }

        # Build lookup dict from storyboard segments
        segments_by_type = {}
        for seg in storyboard.get("segments", []):
            segments_by_type[seg.get("type")] = seg

        for part in sections:
            segment_type = segment_type_map.get(part)
            segment = segments_by_type.get(segment_type, {})

            # Get seed from segment (if available)
            section_seeds[part] = segment.get("seed")

            # Get visual_scene from storyboard segment
            visual_scene = segment.get("visual_scene")

            # Fallback: create basic visual_scene from visual_guidance or narration
            if not visual_scene:
                visual_guidance = segment.get("visual_guidance", "")
                if not visual_guidance:
                    narration = segment.get("narration", "")
                    visual_guidance = f"Educational scene about {narration[:100]}"

                visual_scene = {
                    "description": visual_guidance,
                    "composition": "centered subject with educational context",
                    "lighting": "warm, inviting studio lighting",
                    "camera_angle": "eye level medium shot",
                    "key_elements": segment.get("key_concepts", [])[:5],
                    "mood": "engaging and educational",
                    "color_palette": ["blue", "green", "warm yellow"]
                }

            visual_scenes[part] = visual_scene

            # Get duration from storyboard segment with defaults
            default_durations = {"hook": 10.0, "concept": 15.0, "process": 20.0, "conclusion": 15.0}
            duration = segment.get("duration")
            if duration:
                try:
                    segment_durations[part] = float(duration)
                except (ValueError, TypeError):
                    segment_durations[part] = default_durations.get(part, 15.0)
            else:
                segment_durations[part] = default_durations.get(part, 15.0)

            # Log the visual scene info
            logger.info(f"[{session_id}] Section '{part}': {segment_durations[part]}s, visual_scene: {visual_scene.get('description', '')[:100]}...")

        # Generate all videos in parallel using asyncio.gather
        # Track completion for progress updates
        completed_videos = []
        
        # Cost tracking (model-dependent)
        model_costs = {
            "veo3": 1.20,      # Google Veo 3: ~$1.20 per 6s
            "kling": 0.18,     # Kling v1.5 Pro: ~$0.15/5s = $0.18/6s
            "minimax": 0.042,  # Minimax: ~$0.035/5s = $0.042/6s
            "luma": 0.24,      # Luma: ~$0.20/5s = $0.24/6s
            "wan-i2v": 0.025,  # WAN 2.2 I2V Fast: ~$0.02/5s at 720p
            "wan-video/wan-2.2-i2v-fast": 0.025,  # Direct model ID
        }
        COST_PER_CLIP = model_costs.get(model, 0.025)  # USD per clip (default to wan-i2v cost)
        # Note: total_cost and cost_per_section are already initialized at function start (line 453-454)

        # Constants for video generation
        CLIP_DURATION = 6.0  # Target 6-second clips
        
        # Rate limiting: Max 4 concurrent Replicate API calls to avoid overwhelming the service
        MAX_CONCURRENT_REPLICATE_CALLS = 4
        replicate_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REPLICATE_CALLS)

        # Calculate clips needed per section based on segment durations
        clips_per_section = {}
        for section in sections:
            # Use segment duration (from storyboard or defaults)
            segment_duration = segment_durations[section]
            clips_needed = max(1, math.ceil(segment_duration / CLIP_DURATION))
            clips_per_section[section] = clips_needed
            logger.info(f"[{session_id}] Section '{section}': {segment_duration}s → {clips_needed} clips ({CLIP_DURATION}s each)")

        total_clips = sum(clips_per_section.values())
        
        # Define video generation function (used only if not restarting)
        async def generate_section_video(section: str) -> tuple[str, List[str]]:
            """Generate multiple video clips for a section and return (section, list_of_clip_paths)"""
            import httpx

            # Get visual_scene description for video prompt
            visual_scene = visual_scenes[section]
            scene_description = visual_scene.get("description", "")
            clips_needed = clips_per_section[section]

            logger.info(f"[{session_id}] Generating {clips_needed} clips for section '{section}'")
            logger.info(f"[{session_id}] Using scene description for '{section}': {scene_description[:150]}...")

            # Get base_scene for visual consistency across all clips
            # Check both new format (agent_3_data) and old format (root level)
            if agent_3_data:
                base_scene = agent_3_data.get("base_scene", {})
            elif pipeline_data:
                base_scene = pipeline_data.get("base_scene", {})
            else:
                base_scene = {}

            # Build base_scene context string for video prompts
            def to_string(val):
                if isinstance(val, dict):
                    return " ".join(str(v) for v in val.values() if v)
                return str(val) if val else ""

            base_scene_parts = []
            if base_scene.get("style"):
                base_scene_parts.append(f"Style: {to_string(base_scene['style'])}")
            if base_scene.get("setting"):
                setting_str = to_string(base_scene["setting"])
                # Limit setting length
                setting_words = setting_str.split()[:30]
                base_scene_parts.append(f"Setting: {' '.join(setting_words)}")
            if base_scene.get("teacher"):
                teacher_str = to_string(base_scene["teacher"])
                teacher_words = teacher_str.split()[:20]
                base_scene_parts.append(f"Teacher: {' '.join(teacher_words)}")
            if base_scene.get("students"):
                students_str = to_string(base_scene["students"])
                students_words = students_str.split()[:20]
                base_scene_parts.append(f"Students: {' '.join(students_words)}")

            base_scene_context = " | ".join(base_scene_parts) + " | " if base_scene_parts else ""

            # Generate progressive prompts for each clip position
            clip_prompts = []
            for i in range(clips_needed):
                # Create clip-specific temporal and action cues based on position
                if clips_needed == 1:
                    clip_prompt = f"{base_scene_context}{scene_description}, smooth cinematic movement"
                elif i == 0:
                    clip_prompt = f"{base_scene_context}OPENING SHOT: {scene_description}, camera slowly pushes in, beginning of action"
                elif i == clips_needed - 1:
                    clip_prompt = f"{base_scene_context}FINAL SHOT: {scene_description}, camera holds steady, completing action"
                else:
                    clip_prompt = f"{base_scene_context}SHOT {i+1}: {scene_description}, camera maintains angle, continuous motion"

                clip_prompts.append(clip_prompt)

            # Get seed from storyboard segment or generate deterministic fallback
            section_seed = section_seeds.get(section)
            if section_seed is None:
                # Fallback: use hash of section name to get consistent seed per section
                import hashlib
                section_hash = int(hashlib.md5(section.encode()).hexdigest()[:8], 16)
                section_seed = section_hash % 100000  # Keep seed in reasonable range
                logger.info(f"[{session_id}] No seed from Agent 2, using generated seed {section_seed} for {section}")
            else:
                logger.info(f"[{session_id}] Using Agent 2 seed {section_seed} for all clips in {section}")

            # Generate clips sequentially with continuity (image-to-video for clips 2+)
            generated_clips = []
            previous_clip_url = None

            for clip_idx, clip_prompt in enumerate(clip_prompts):
                async with replicate_semaphore:
                    if clip_idx == 0:
                        # First clip: Check if we have a generated image for this section
                        section_image_url = section_images.get(section)

                        if section_image_url:
                            # Use image-to-video with generated Gemini image
                            logger.info(f"[{session_id}] Generating clip {clip_idx+1}/{clips_needed} (image-to-video from Gemini image)")
                            try:
                                service = ReplicateVideoService(replicate_api_key)
                                clip_url = await service.generate_video_from_image(
                                    prompt=clip_prompt,
                                    image_url=section_image_url,
                                    model=model,
                                    seed=section_seed
                                )
                            except Exception as e:
                                # Graceful fallback: if image-to-video fails, use text-to-video with Minimax
                                # (Kling doesn't support text-to-video, so we must use a different model)
                                logger.warning(f"[{session_id}] Image-to-video failed for {section}: {e}. Falling back to text-to-video with Minimax.")
                                clip_url = await generate_video_replicate(
                                    clip_prompt,
                                    replicate_api_key,
                                    model="minimax",  # Minimax supports text-to-video
                                    seed=section_seed
                                )
                        else:
                            # Fallback: text-to-video (if no generated image available)
                            logger.info(f"[{session_id}] Generating clip {clip_idx+1}/{clips_needed} (text-to-video - no image available)")
                            clip_url = await generate_video_replicate(
                                clip_prompt,
                                replicate_api_key,
                                model=model,
                                seed=section_seed
                            )
                    else:
                        # Subsequent clips: extract last frame from previous clip, then image-to-video
                        logger.info(f"[{session_id}] Generating clip {clip_idx+1}/{clips_needed} (image-to-video with continuity)")

                        try:
                            # Extract last frame as base64 from previous clip
                            frame_data_uri = await extract_last_frame_as_base64(previous_clip_url)

                            # Generate next clip from the frame
                            service = ReplicateVideoService(replicate_api_key)
                            clip_url = await service.generate_video_from_image(
                                prompt=clip_prompt,
                                image_url=frame_data_uri,
                                model=model,
                                seed=section_seed
                            )
                        except Exception as e:
                            # Graceful fallback: if frame extraction or image-to-video fails, use text-to-video with Minimax
                            # (Kling doesn't support text-to-video, so we must use a different model)
                            logger.warning(f"[{session_id}] Frame continuity failed for clip {clip_idx+1}: {e}. Falling back to text-to-video with Minimax.")
                            clip_url = await generate_video_replicate(
                                clip_prompt,
                                replicate_api_key,
                                model="minimax",  # Minimax supports text-to-video
                                seed=section_seed
                            )

                    generated_clips.append(clip_url)
                    previous_clip_url = clip_url

            # Calculate cost for this section
            section_cost = len(generated_clips) * COST_PER_CLIP
            cost_per_section[section] = section_cost

            # Initialize current_total_cost before loops
            current_total_cost = sum(cost_per_section.values())

            # Update progress with cost info
            for clip_idx in range(len(generated_clips)):
                completed_videos.append(f"{section}_{clip_idx}")
                # Update current total cost for progress updates
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

            # Download and verify all clips (single attempt, no regeneration)
            clip_paths = []

            async with httpx.AsyncClient(timeout=120.0) as client:
                for i, clip_url in enumerate(generated_clips):
                    try:
                        # Download clip
                        response = await client.get(clip_url)
                        response.raise_for_status()
                        clip_path = os.path.join(temp_dir, f"{section}_clip_{i}.mp4")
                        with open(clip_path, 'wb') as f:
                            f.write(response.content)

                        # SKIP per-clip verification - adds overhead with no actionable outcome
                        # (clips are always accepted regardless of result, final video verification still runs)
                        # logger.info(f"[{session_id}] Verifying {section} clip {i + 1}/{len(generated_clips)}...")
                        # verification_result = await video_verifier.verify_clip(
                        #     video_url=clip_path,
                        #     expected_duration=6.0,  # Veo 3 generates 6-second clips
                        #     clip_index=i
                        # )
                        #
                        # if verification_result.passed:
                        #     logger.info(f"[{session_id}] ✓ Clip {i + 1} passed verification for {section}")
                        # else:
                        #     # Log verification failures as warnings but continue with clip
                        #     failed_check_names = [c.check_name for c in verification_result.failed_checks]
                        #     logger.warning(
                        #         f"[{session_id}] ⚠ Clip {i + 1} for {section} failed verification: {failed_check_names}. "
                        #         f"Continuing with clip anyway (regeneration disabled)."
                        #     )
                        #     for check in verification_result.failed_checks:
                        #         logger.warning(f"[{session_id}]   - {check.check_name}: {check.message}")

                        clip_paths.append(clip_path)

                        # Save clip to S3 for restart capability
                        clip_s3_key = f"users/{user_id}/{session_id}/agent5/{section}_clip_{i}.mp4"
                        try:
                            with open(clip_path, 'rb') as f:
                                clip_content = f.read()
                            storage_service.upload_file_direct(clip_content, clip_s3_key, "video/mp4")
                            logger.info(f"[{session_id}] Saved clip {i + 1} to S3 for {section}")
                        except Exception as e:
                            logger.warning(f"[{session_id}] Failed to save clip to S3 {clip_s3_key}: {e}")

                    except Exception as e:
                        logger.error(f"[{session_id}] Error downloading/processing clip {i + 1} for {section}: {e}")
                        raise RuntimeError(f"Failed to download clip {i + 1} for {section}: {e}")

            logger.info(f"[{session_id}] Downloaded and saved {len(generated_clips)} clips for {section}")

            return (section, clip_paths)

        # Handle restart mode: download existing clips from S3
        all_clip_paths = []
        section_images = {}  # Initialize (will be populated with Gemini images if not in restart mode)

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
            # ====================
            # IMAGE GENERATION PHASE (Gemini via Replicate)
            # ====================
            # Generate images for all 4 sections using storyboard visual scenes
            # These images will be used as the starting frame for video generation

            logger.info(f"[{session_id}] Starting image generation (Gemini) for {len(sections)} sections")

            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message="Generating images with Gemini for each section...",
                cost=0.0
            )

            # Initialize Gemini generator with Replicate API key
            image_generator = ReplicateGeminiGenerator(api_key=replicate_api_key)

            # Store generated images for each section
            section_images = {}
            image_generation_cost = 0.0

            # Generate images in parallel for all sections
            async def generate_section_image(section: str) -> tuple[str, Optional[str]]:
                """Generate a Gemini image for a section with retry logic. Returns (section, image_url)"""
                visual_scene = visual_scenes[section]

                logger.info(f"[{session_id}] Generating image for '{section}' with Gemini")
                logger.info(f"[{session_id}] Visual scene for '{section}': {visual_scene.get('description', '')[:150]}...")

                # Retry logic: up to 3 attempts
                max_retries = 3
                for attempt in range(1, max_retries + 1):
                    try:
                        logger.info(f"[{session_id}] Gemini generation attempt {attempt}/{max_retries} for '{section}'")

                        # Generate image with Gemini - pass visual_scene object directly
                        result = await image_generator.generate_image(
                            visual_scene=visual_scene,
                            quality="standard"  # ~$0.02 per image
                        )

                        if result.get("success"):
                            image_url = result["url"]
                            logger.info(f"[{session_id}] Successfully generated image for '{section}' on attempt {attempt}/{max_retries}: {image_url[:100]}...")
                            return (section, image_url)
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            logger.warning(f"[{session_id}] Failed to generate image for '{section}' (attempt {attempt}/{max_retries}): {error_msg}")
                            if attempt < max_retries:
                                continue  # Retry
                            else:
                                logger.error(f"[{session_id}] All {max_retries} attempts exhausted for '{section}'")
                                return (section, None)

                    except Exception as e:
                        logger.error(f"[{session_id}] Exception generating image for '{section}' (attempt {attempt}/{max_retries}): {e}")
                        if attempt < max_retries:
                            continue  # Retry
                        else:
                            logger.error(f"[{session_id}] All {max_retries} attempts exhausted for '{section}'")
                            return (section, None)

                # Fallback (should never reach here, but just in case)
                return (section, None)

            # Generate all images in parallel
            image_results = await asyncio.gather(*[generate_section_image(section) for section in sections])

            # Store results and calculate cost
            for section, image_url in image_results:
                if image_url:
                    section_images[section] = image_url
                    image_generation_cost += 0.02  # Gemini estimated cost per image
                    logger.info(f"[{session_id}] Stored image for '{section}'")
                else:
                    logger.warning(f"[{session_id}] No image generated for '{section}' - will fall back to text-to-video")

            logger.info(f"[{session_id}] Completed image generation. Generated {len(section_images)}/{len(sections)} images. Cost: ${image_generation_cost:.4f}")

            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message=f"Generated {len(section_images)}/{len(sections)} images with Gemini. Starting video generation...",
                cost=image_generation_cost
            )

            # ====================
            # VIDEO GENERATION PHASE
            # ====================

            # Generate all videos in parallel (fully parallelized)
            logger.info(f"[{session_id}] Generating all {len(sections)} sections in parallel")

            # Model display names
            model_names = {
                "veo3": "Google Veo 3",
                "kling": "Kling v1.5 Pro",
                "minimax": "Minimax Video-01",
                "luma": "Luma Dream Machine",
                "wan-i2v": "WAN 2.2 I2V Fast",
                "wan-video/wan-2.2-i2v-fast": "WAN 2.2 I2V Fast",
            }
            model_display = model_names.get(model, model)

            await send_status(
                "Agent5", "processing",
                supersessionID=supersessionid,
                message=f"Generating videos in parallel with {model_display}...",
                cost=image_generation_cost
            )

            # Process sections in parallel for maximum speed
            section_results = await asyncio.gather(*[generate_section_video(section) for section in sections])

            # Collect all clip paths in order (hook, concept, process, conclusion)
            for section in sections:
                # Find the result for this section
                section_result = next((result for result in section_results if result[0] == section), None)
                if section_result:
                    section_name, clip_paths = section_result
                    all_clip_paths.extend(clip_paths)

        # Calculate final total cost (only if not restart mode)
        if not restart_from_concat:
            total_cost = sum(cost_per_section.values()) + image_generation_cost
            logger.info(f"[{session_id}] Completed all sections. Video cost: ${sum(cost_per_section.values()):.4f}, Image cost: ${image_generation_cost:.4f}, Total cost: ${total_cost:.4f}")

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
        # DOWNLOAD FINAL AUDIO FROM AGENT 4
        # ====================
        # Agent 4 creates the final mixed 60-second audio (narration + music)
        # We just need to download it here

        await send_status(
            "Agent5", "processing",
            supersessionID=supersessionid,
            message="Downloading final audio from Agent 4...",
            cost=total_cost if not restart_from_concat else 0.0,
            cost_breakdown=cost_per_section if not restart_from_concat else {}
        )

        final_audio_path = os.path.join(temp_dir, "final_audio.mp3")
        final_audio_s3_key = f"users/{user_id}/{session_id}/agent4/final_audio.mp3"

        # Try to get final_audio from agent_4_data (if loaded from S3)
        final_audio_url = None
        if agent_4_data and agent_4_data.get("final_audio"):
            final_audio_url = agent_4_data["final_audio"].get("url")
            logger.info(f"[{session_id}] Found final_audio URL in agent_4_data")

        if not final_audio_url:
            # Generate presigned URL directly
            final_audio_url = storage_service.generate_presigned_url(final_audio_s3_key, expires_in=86400)
            logger.info(f"[{session_id}] Generated presigned URL for final_audio")

        # Download final audio
        import httpx
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=False) as client:
            success = await _download_with_fallback(
                primary_url=final_audio_url,
                s3_key=final_audio_s3_key,
                output_path=final_audio_path,
                storage_service=storage_service,
                client=client,
                session_id=session_id,
                file_description="final mixed audio from Agent 4"
            )

            if not success:
                raise ValueError(f"Failed to download final audio from Agent 4. Expected at: {final_audio_s3_key}")

        logger.info(f"[{session_id}] Downloaded final mixed audio from Agent 4 (60s narration + music)")

        # ====================
        # VIDEO CONCATENATION
        # ====================

        step_num = "1/2" if not restart_from_concat else "1/2"
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

        step_num = "2/2"
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
