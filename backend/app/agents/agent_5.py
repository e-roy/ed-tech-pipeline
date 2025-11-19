"""
Agent 5 - Video Generator using Remotion

Generates a 60-second video from pipeline data:
1. Generates images from visual prompts using DALL-E 2
2. Calculates scene timing to space audio across 60 seconds
3. Renders video using Remotion with Ken Burns effect
4. Uploads final video to S3
"""
import asyncio
import json
import os
import subprocess
import tempfile
import time
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, List
from app.services.websocket_manager import WebSocketManager
from app.services.storage import StorageService
from app.config import get_settings


# Path to Remotion project
# agent_5.py is at: backend/app/agents/agent_5.py
# remotion is at: remotion/
# So we need to go up 3 levels from agent_5.py to backend, then up to pipeline, then into remotion
REMOTION_DIR = Path(__file__).parent.parent.parent.parent / "remotion"


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
    temp_dir: str
) -> str:
    """
    Render video using Remotion CLI.

    Args:
        scenes: List of scene data with imageUrl, audioUrl, timing info
        background_music_url: URL or path to background music
        output_path: Path for output video file
        temp_dir: Temp directory containing local image files

    Returns:
        Path to rendered video
    """
    # Copy images to Remotion's public directory for local access
    remotion_public = REMOTION_DIR / "public"
    remotion_public.mkdir(exist_ok=True)

    # Update scenes to use local file paths
    updated_scenes = []
    for scene in scenes:
        part = scene["part"]
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
        # Use subprocess.run with asyncio.to_thread to avoid uvloop subprocess issues
        import subprocess

        # Log the props for debugging
        print(f"Remotion props: {json.dumps(props, indent=2)}")
        print(f"Remotion dir: {REMOTION_DIR}")
        print(f"Public dir contents: {list(remotion_public.iterdir()) if remotion_public.exists() else 'not found'}")

        cmd = f"bunx remotion render src/index.ts VideoComposition {output_path} --props={props_file.name}"

        result = await asyncio.to_thread(
            subprocess.run,
            cmd,
            cwd=str(REMOTION_DIR),
            capture_output=True,
            text=True,
            shell=True,
            env={**os.environ, "PATH": f"/Users/mfuechec/.bun/bin:{os.environ.get('PATH', '')}"}
        )

        # Log stdout/stderr for debugging
        if result.stdout:
            print(f"Remotion stdout: {result.stdout}")
        if result.stderr:
            print(f"Remotion stderr: {result.stderr}")

        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed: {result.stderr}\n{result.stdout}")

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
    websocket_manager: WebSocketManager,
    user_id: str,
    session_id: str,
    supersessionid: str,
    storage_service: Optional[StorageService] = None,
    pipeline_data: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Agent5: Video generation agent using Remotion.

    Args:
        websocket_manager: WebSocket manager for status updates
        user_id: User identifier
        session_id: Session identifier
        supersessionid: Super session identifier
        storage_service: Storage service for S3 operations
        pipeline_data: Pipeline data including:
            - script: Script with visual_prompt for each section
            - audio_data: Audio files and background music

    Returns:
        The presigned URL of the uploaded video, or None on error
    """
    settings = get_settings()

    # Initialize storage service if not provided
    if storage_service is None:
        storage_service = StorageService()

    # Helper function to create JSON status file in S3
    async def create_status_json(agent_number: str, status: str, status_data: dict):
        """Create a JSON file in S3 with status data."""
        if not storage_service.s3_client:
            return

        timestamp = int(time.time() * 1000)
        filename = f"agent_{agent_number}_{status}_{timestamp}.json"
        s3_key = f"scaffold_test/{user_id}/{supersessionid}/{filename}"

        try:
            json_content = json.dumps(status_data, indent=2).encode('utf-8')
            storage_service.s3_client.put_object(
                Bucket=storage_service.bucket_name,
                Key=s3_key,
                Body=json_content,
                ContentType='application/json'
            )
        except Exception as e:
            print(f"Failed to create status JSON file: {e}")

    video_url = None
    temp_dir = None

    try:
        # Report starting status
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "starting",
            "timestamp": int(time.time() * 1000)
        }
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("5", "starting", status_data)

        # Validate pipeline data
        if not pipeline_data:
            raise ValueError("No pipeline data provided")

        script = pipeline_data.get("script", {})
        audio_data = pipeline_data.get("audio_data", {})
        audio_files = audio_data.get("audio_files", [])
        background_music = audio_data.get("background_music", {})

        if not script:
            raise ValueError("No script data in pipeline")

        # Create temp directory for assets
        temp_dir = tempfile.mkdtemp(prefix="agent5_")

        # Report processing status
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "processing",
            "message": "Generating images from visual prompts...",
            "timestamp": int(time.time() * 1000)
        }
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("5", "processing", status_data)

        # Generate images for each script section
        sections = ["hook", "concept", "process", "conclusion"]
        generated_images = {}

        for i, section in enumerate(sections):
            # Update progress for each image
            status_data = {
                "agentnumber": "Agent5",
                "userID": user_id,
                "sessionID": session_id,
                "supersessionID": supersessionid,
                "status": "processing",
                "message": f"Generating image {i+1}/4: {section}...",
                "timestamp": int(time.time() * 1000)
            }
            await websocket_manager.send_progress(session_id, status_data)

            section_data = script.get(section, {})
            visual_prompt = section_data.get("visual_prompt", "")

            if not visual_prompt:
                # Fallback: generate prompt from text
                text = section_data.get("text", "")
                visual_prompt = f"Cinematic scene representing: {text[:200]}"

            # Generate image
            image_data = await generate_image_dalle(visual_prompt, settings.OPENAI_API_KEY)

            # Save locally
            image_path = os.path.join(temp_dir, f"{section}.png")
            with open(image_path, "wb") as f:
                f.write(image_data)

            # Upload to S3
            s3_key = f"scaffold_test/{user_id}/{supersessionid}/image_{section}.png"
            storage_service.upload_file_direct(image_data, s3_key, "image/png")
            image_url = storage_service.generate_presigned_url(s3_key, expires_in=3600)

            generated_images[section] = image_url

        # Update status for rendering
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "processing",
            "message": "Rendering video with Remotion (this may take 2-4 minutes)...",
            "timestamp": int(time.time() * 1000)
        }
        await websocket_manager.send_progress(session_id, status_data)

        # Calculate scene timing
        scene_timing = calculate_scene_timing(audio_files)

        # Build scenes array for Remotion
        scenes = []
        for timing in scene_timing:
            part = timing["part"]

            # Find matching audio file
            audio_file = next((a for a in audio_files if a["part"] == part), None)
            audio_url = audio_file.get("url", "") if audio_file else ""

            scenes.append({
                "part": part,
                "imageUrl": generated_images.get(part, ""),
                "audioUrl": audio_url,
                "startFrame": timing["startFrame"],
                "durationFrames": timing["durationFrames"],
                "audioDurationFrames": timing["audioDurationFrames"]
            })

        # Get background music URL
        background_music_url = background_music.get("url", "")

        # Render video
        output_path = os.path.join(temp_dir, "output.mp4")
        await render_video_with_remotion(scenes, background_music_url, output_path, temp_dir)

        # Upload video to S3
        import uuid
        video_filename = f"final_video_{uuid.uuid4().hex[:8]}.mp4"
        video_s3_key = f"scaffold_test/{user_id}/{supersessionid}/{video_filename}"

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

        # Report finished status
        status_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "finished",
            "timestamp": int(time.time() * 1000),
            "videoUrl": video_url
        }
        await websocket_manager.send_progress(session_id, status_data)
        await create_status_json("5", "finished", status_data)

        return video_url

    except Exception as e:
        # Report error status
        error_data = {
            "agentnumber": "Agent5",
            "userID": user_id,
            "sessionID": session_id,
            "supersessionID": supersessionid,
            "status": "error",
            "error": str(e),
            "reason": f"Agent5 failed: {type(e).__name__}",
            "timestamp": int(time.time() * 1000)
        }
        await websocket_manager.send_progress(session_id, error_data)
        await create_status_json("5", "error", error_data)
        raise

    finally:
        # Cleanup temp directory
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
