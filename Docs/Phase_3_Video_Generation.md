# Phase 3: Video Generation & Processing

## Document Purpose
This phase implements video clip generation from images and the final composition layer using FFmpeg.

**Estimated Time:** 14 hours (Hour 16-32 of 48-hour sprint)

---

## 1. Video Generator Agent

### 1.1 Purpose & Responsibilities

Convert approved product images into animated video clips using Image-to-Video models, maintaining visual consistency and applying user's scene description.

**Key Features:**
- Scene planning with LLM
- Image-to-Video conversion
- Parallel clip generation
- Motion intensity control
- Multiple model support (SVD, Runway Gen-2)

### 1.2 Video Scene Planning

Before generating videos, use Llama 3.1 to create scene-specific prompts for each image based on the user's overall video description.

### 1.3 Implementation (agents/video_generator.py)

```python
import asyncio
import time
import uuid
import json
from app.models.schemas import AgentInput, AgentOutput
from app.config import settings
import replicate

class VideoGeneratorAgent:
    """
    Video Generator Agent

    Converts product images into video clips using Image-to-Video models.
    Uses LLM for intelligent scene planning per image view.
    """

    def __init__(self):
        self.models = {
            "stable-video-diffusion": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
            "runway-gen2": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438"
            # Note: Update with actual Runway model ID when available
        }
        self.llm_model = "meta/meta-llama-3.1-70b-instruct"

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Generate video clips from images

        Input data expected:
        {
            "approved_images": [
                {
                    "id": str,
                    "url": str,
                    "view_type": str
                },
                ...
            ],
            "video_prompt": str,
            "clip_duration": float (2.0-4.0),
            "model": "stable-video-diffusion" | "runway-gen2"
        }
        """
        start_time = time.time()

        try:
            approved_images = input.data["approved_images"]
            video_prompt = input.data["video_prompt"]
            clip_duration = input.data.get("clip_duration", 3.0)
            model_name = input.data.get("model", "stable-video-diffusion")

            # Step 1: Plan scenes with LLM
            scenes = await self._plan_video_scenes(approved_images, video_prompt)

            # Step 2: Generate video clips in parallel
            tasks = []
            for i, image_data in enumerate(approved_images):
                # Match scene to image view
                scene = next(
                    (s for s in scenes if s["image_view"] == image_data["view_type"]),
                    scenes[0] if scenes else None
                )

                if not scene:
                    # Fallback to simple scene
                    scene = {
                        "scene_prompt": video_prompt,
                        "motion_intensity": 0.5
                    }

                task = self._generate_single_clip(
                    model=model_name,
                    image_url=image_data["url"],
                    scene_prompt=scene["scene_prompt"],
                    motion_intensity=scene["motion_intensity"],
                    duration=clip_duration,
                    source_image_id=image_data["id"],
                    view_type=image_data["view_type"]
                )
                tasks.append(task)

            # Execute all tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            clips = []
            total_cost = 0.0
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    errors.append(f"Clip {i+1} failed: {str(result)}")
                    continue

                clips.append(result)
                total_cost += result["cost"]

            duration = time.time() - start_time

            if len(clips) == 0:
                return AgentOutput(
                    success=False,
                    data={},
                    cost=total_cost,
                    duration=duration,
                    error=f"All video generations failed: {'; '.join(errors)}"
                )

            return AgentOutput(
                success=True,
                data={
                    "clips": clips,
                    "total_cost": total_cost,
                    "successful": len(clips),
                    "failed": len(errors)
                },
                cost=total_cost,
                duration=duration,
                error=None if len(errors) == 0 else f"Partial failures: {'; '.join(errors)}"
            )

        except Exception as e:
            duration = time.time() - start_time
            return AgentOutput(
                success=False,
                data={},
                cost=0.0,
                duration=duration,
                error=str(e)
            )

    async def _plan_video_scenes(
        self,
        approved_images: list[dict],
        video_prompt: str
    ) -> list[dict]:
        """Use LLM to create scene descriptions for each image"""

        system_prompt = """You are a video scene director for product advertisements.

Given:
- Multiple product images with different views (front, side, back, detail, lifestyle)
- User's overall scene description

Your task:
Create specific scene descriptions for each image that:
1. Maintain the user's creative vision
2. Enhance each image's unique angle/view
3. Add appropriate motion and cinematography

Output JSON:
{
    "scenes": [
        {
            "image_view": "front|side|back|top|detail|lifestyle",
            "scene_prompt": "detailed scene description with motion",
            "camera_movement": "slow zoom in|pan left|static|...",
            "motion_intensity": 0.0-1.0
        },
        ...
    ]
}"""

        user_prompt = f"""User's scene description: {video_prompt}

Product images:
{json.dumps([{"view": img["view_type"]} for img in approved_images], indent=2)}

Create scene-specific prompts for each image view."""

        try:
            # Call Llama 3.1
            output = await replicate.async_run(
                self.llm_model,
                input={
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "max_tokens": 1500,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )

            full_response = "".join(output)

            # Extract JSON
            json_start = full_response.find("{")
            json_end = full_response.rfind("}") + 1
            json_str = full_response[json_start:json_end]
            parsed_data = json.loads(json_str)

            return parsed_data.get("scenes", [])

        except Exception as e:
            print(f"⚠️ Scene planning failed: {e}, using default scenes")
            # Return default scenes
            return [
                {
                    "image_view": img["view_type"],
                    "scene_prompt": video_prompt,
                    "motion_intensity": 0.5
                }
                for img in approved_images
            ]

    async def _generate_single_clip(
        self,
        model: str,
        image_url: str,
        scene_prompt: str,
        motion_intensity: float,
        duration: float,
        source_image_id: str,
        view_type: str
    ) -> dict:
        """Generate a single video clip via Replicate API"""

        model_id = self.models[model]
        start = time.time()

        try:
            # Stable Video Diffusion input
            model_input = {
                "image": image_url,
                "motion_bucket_id": int(motion_intensity * 255),  # 0-255 scale
                "cond_aug": 0.02,
                "decoding_t": 14,
                "video_length": "14_frames_with_svd" if duration <= 3 else "25_frames_with_svd_xt",
                "sizing_strategy": "maintain_aspect_ratio",
                "frames_per_second": 30
            }

            # Call Replicate API
            output = await replicate.async_run(model_id, input=model_input)

            generation_time = time.time() - start

            # Extract video URL
            if isinstance(output, str):
                video_url = output
            elif isinstance(output, list):
                video_url = output[0]
            else:
                video_url = str(output)

            # Estimate cost
            cost = 0.80 if model == "stable-video-diffusion" else 1.50

            return {
                "id": f"clip_{uuid.uuid4().hex[:8]}",
                "url": video_url,
                "source_image_id": source_image_id,
                "view_type": view_type,
                "duration": duration,
                "resolution": "1024x576",
                "fps": 30,
                "cost": cost,
                "generation_time": generation_time,
                "model": model
            }

        except Exception as e:
            raise Exception(f"Video generation failed for view '{view_type}': {str(e)}")
```

---

## 2. Composition Layer (FFmpeg)

### 2.1 Purpose & Responsibilities

Stitch approved video clips with intro/outro cards, text overlays, transitions, and optional background music into final ad video.

**Key Features:**
- Intro/outro card generation
- Video stitching with FFmpeg
- Text overlay rendering
- Audio mixing
- 1080p upscaling
- Web-optimized output (MP4)

### 2.2 Storage Service (services/storage_service.py)

```python
import boto3
from botocore.exceptions import ClientError
from app.config import settings
import uuid
from pathlib import Path

class StorageService:
    """
    Storage Service

    Handles file uploads to S3 or compatible storage (Cloudflare R2)
    """

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    async def upload_file(
        self,
        file_path: Path,
        content_type: str = "video/mp4"
    ) -> str:
        """Upload file to S3 and return public URL"""

        try:
            # Generate unique key
            file_extension = file_path.suffix
            object_key = f"videos/{uuid.uuid4().hex}{file_extension}"

            # Upload file
            with open(file_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    self.bucket_name,
                    object_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'ACL': 'public-read'
                    }
                )

            # Generate public URL
            url = f"https://{self.bucket_name}.s3.{settings.S3_REGION}.amazonaws.com/{object_key}"

            return url

        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    async def download_file(self, url: str, local_path: Path):
        """Download file from URL to local path"""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            with open(local_path, 'wb') as f:
                f.write(response.content)
```

### 2.3 Composition Layer Implementation (agents/compositor.py)

```python
import subprocess
import tempfile
import asyncio
import os
import time
from pathlib import Path
from app.models.schemas import AgentInput, AgentOutput
from app.services.storage_service import StorageService

class CompositionLayer:
    """
    Composition Layer

    Uses FFmpeg to stitch video clips, add text overlays,
    intro/outro cards, and background music.
    """

    def __init__(self):
        self.storage = StorageService()

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Compose final video

        Input data expected:
        {
            "selected_clips": [
                {
                    "id": str,
                    "url": str,
                    "duration": float,
                    "order": int
                },
                ...
            ],
            "text_overlay": {
                "product_name": str,
                "cta": str,
                "font": str,
                "color": str
            },
            "audio": {
                "enabled": bool,
                "genre": str
            },
            "intro_duration": float,
            "outro_duration": float
        }
        """
        start_time = time.time()

        try:
            selected_clips = input.data["selected_clips"]
            text_overlay = input.data["text_overlay"]
            audio_config = input.data.get("audio", {})
            intro_duration = input.data.get("intro_duration", 1.0)
            outro_duration = input.data.get("outro_duration", 1.0)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Step 1: Download all clips
                clip_paths = await self._download_clips(selected_clips, temp_path)

                # Step 2: Generate intro card
                intro_path = await self._generate_intro_card(
                    text_overlay["product_name"],
                    intro_duration,
                    temp_path
                )

                # Step 3: Generate outro card
                outro_path = await self._generate_outro_card(
                    text_overlay["cta"],
                    outro_duration,
                    temp_path
                )

                # Step 4: Get background music (optional)
                audio_path = None
                if audio_config.get("enabled"):
                    audio_path = await self._get_background_music(
                        genre=audio_config.get("genre", "upbeat"),
                        duration=intro_duration + sum(c["duration"] for c in selected_clips) + outro_duration,
                        temp_path=temp_path
                    )

                # Step 5: Stitch everything with FFmpeg
                final_video_path = await self._stitch_video(
                    intro_path=intro_path,
                    clip_paths=clip_paths,
                    outro_path=outro_path,
                    audio_path=audio_path,
                    text_overlay=text_overlay,
                    output_path=temp_path / "final_video.mp4"
                )

                # Step 6: Upload to storage
                final_url = await self.storage.upload_file(
                    final_video_path,
                    content_type="video/mp4"
                )

                duration = time.time() - start_time
                file_size_mb = os.path.getsize(final_video_path) / (1024 * 1024)
                total_duration = intro_duration + sum(c["duration"] for c in selected_clips) + outro_duration

                return AgentOutput(
                    success=True,
                    data={
                        "final_video": {
                            "url": final_url,
                            "duration": round(total_duration, 2),
                            "resolution": "1920x1080",
                            "fps": 30,
                            "file_size_mb": round(file_size_mb, 2),
                            "format": "mp4"
                        }
                    },
                    cost=0.50,  # Estimate for storage/processing
                    duration=duration,
                    error=None
                )

        except Exception as e:
            duration = time.time() - start_time
            return AgentOutput(
                success=False,
                data={},
                cost=0.0,
                duration=duration,
                error=str(e)
            )

    async def _download_clips(
        self,
        clips: list[dict],
        temp_path: Path
    ) -> list[Path]:
        """Download all video clips to local temp directory"""

        clip_paths = []

        for i, clip in enumerate(clips):
            clip_path = temp_path / f"clip_{i:02d}.mp4"
            await self.storage.download_file(clip["url"], clip_path)
            clip_paths.append(clip_path)

        return clip_paths

    async def _generate_intro_card(
        self,
        product_name: str,
        duration: float,
        temp_path: Path
    ) -> Path:
        """Generate intro card using FFmpeg"""

        intro_path = temp_path / "intro.mp4"

        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1920x1080:d={duration}",
            "-vf", f"drawtext=text='{product_name}':fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf:fontsize=96:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-y",
            str(intro_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg intro generation failed: {stderr.decode()}")

        return intro_path

    async def _generate_outro_card(
        self,
        cta: str,
        duration: float,
        temp_path: Path
    ) -> Path:
        """Generate outro card using FFmpeg"""

        outro_path = temp_path / "outro.mp4"

        cmd = [
            "ffmpeg",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1920x1080:d={duration}",
            "-vf", f"drawtext=text='{cta}':fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf:fontsize=96:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-y",
            str(outro_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg outro generation failed: {stderr.decode()}")

        return outro_path

    async def _get_background_music(
        self,
        genre: str,
        duration: float,
        temp_path: Path
    ) -> Path:
        """Get background music (stock library for MVP)"""

        # For MVP: Use pre-existing stock music
        # In production, could use MusicGen or licensed music

        music_library = {
            "upbeat": "https://example.com/music/upbeat_30s.mp3",
            "chill": "https://example.com/music/chill_30s.mp3",
            "energetic": "https://example.com/music/energetic_30s.mp3"
        }

        music_url = music_library.get(genre, music_library["upbeat"])
        music_path = temp_path / "background_music.mp3"

        # Download music file
        await self.storage.download_file(music_url, music_path)

        return music_path

    async def _stitch_video(
        self,
        intro_path: Path,
        clip_paths: list[Path],
        outro_path: Path,
        audio_path: Path | None,
        text_overlay: dict,
        output_path: Path
    ) -> Path:
        """Stitch video using FFmpeg"""

        # Create concat file for FFmpeg
        concat_file = output_path.parent / "concat.txt"
        with open(concat_file, "w") as f:
            f.write(f"file '{intro_path}'\n")
            for clip_path in clip_paths:
                f.write(f"file '{clip_path}'\n")
            f.write(f"file '{outro_path}'\n")

        # Build FFmpeg command
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
        ]

        # Add audio if provided
        if audio_path:
            cmd.extend(["-i", str(audio_path)])

        # Video filters (scale to 1080p)
        vf_filters = [
            "scale=1920:1080:force_original_aspect_ratio=decrease",
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
        ]

        cmd.extend([
            "-vf", ",".join(vf_filters),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
        ])

        if audio_path:
            cmd.extend([
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest"  # End when shortest stream ends
            ])

        cmd.extend([
            "-movflags", "+faststart",  # Web optimization
            "-y",  # Overwrite output
            str(output_path)
        ])

        # Execute FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg stitching failed: {stderr.decode()}")

        return output_path
```

---

## 3. Update Orchestrator for Video Flow

### 3.1 Add Video Methods to Orchestrator (orchestrator/video_orchestrator.py)

```python
# Add these methods to VideoGenerationOrchestrator class

from app.agents.video_generator import VideoGeneratorAgent
from app.agents.compositor import CompositionLayer

class VideoGenerationOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.prompt_parser = PromptParserAgent()
        self.image_generator = BatchImageGeneratorAgent()
        self.video_generator = VideoGeneratorAgent()  # NEW
        self.compositor = CompositionLayer()          # NEW

    async def generate_clips(
        self,
        session_id: str,
        video_prompt: str,
        clip_duration: float = 3.0
    ):
        """Generate video clips from approved images"""

        try:
            # Load session
            session = await self._get_session(session_id)

            if not session.approved_image_ids:
                raise Exception("No approved images found")

            session.video_prompt = video_prompt
            session.stage = SessionStage.CLIP_GENERATION

            # Load approved images from database
            result = await self.db.execute(
                select(Asset).where(
                    Asset.id.in_(session.approved_image_ids)
                )
            )
            approved_images = result.scalars().all()

            # Format for agent
            image_data = [
                {
                    "id": img.id,
                    "url": img.url,
                    "view_type": img.metadata.get("view_type", "unknown")
                }
                for img in approved_images
            ]

            # Send progress
            await ws_manager.send_progress(session_id, {
                "stage": "video_planning",
                "progress": 55,
                "message": "Planning video scenes...",
                "session_id": session_id
            })

            # Generate clips
            from app.models.schemas import AgentInput

            generator_input = AgentInput(
                session_id=session_id,
                data={
                    "approved_images": image_data,
                    "video_prompt": video_prompt,
                    "clip_duration": clip_duration,
                    "model": "stable-video-diffusion"
                }
            )

            generator_output = await self.video_generator.process(generator_input)

            if not generator_output.success:
                raise Exception(f"Video generation failed: {generator_output.error}")

            # Log cost
            await self._log_cost(
                session_id,
                "video_generator",
                "stable-video-diffusion",
                generator_output.cost,
                generator_output.duration,
                success=True
            )

            # Save clips to database
            clips = generator_output.data["clips"]
            generated_clip_ids = []

            for i, clip_data in enumerate(clips):
                progress = 55 + int((i / len(clips)) * 35)
                await ws_manager.send_progress(session_id, {
                    "stage": "clip_generation",
                    "progress": progress,
                    "message": f"Saving clip {i+1} of {len(clips)}...",
                    "session_id": session_id
                })

                asset = Asset(
                    id=clip_data["id"],
                    session_id=session_id,
                    asset_type=AssetType.VIDEO,
                    url=clip_data["url"],
                    metadata={
                        "source_image_id": clip_data["source_image_id"],
                        "view_type": clip_data.get("view_type"),
                        "duration": clip_data["duration"],
                        "resolution": clip_data["resolution"],
                        "fps": clip_data["fps"]
                    },
                    cost=clip_data["cost"],
                    model_used=clip_data["model"],
                    generation_time=clip_data["generation_time"]
                )

                self.db.add(asset)
                generated_clip_ids.append(asset.id)

            # Update session
            session.generated_clip_ids = generated_clip_ids
            session.total_cost += generator_output.cost
            session.stage = SessionStage.CLIP_SELECTION

            await self.db.commit()

            # Completion
            await ws_manager.send_progress(session_id, {
                "stage": "complete",
                "progress": 100,
                "message": "Clips ready for review!",
                "session_id": session_id,
                "data": {
                    "clips": clips,
                    "total_cost": session.total_cost
                }
            })

            return {
                "status": "success",
                "clip_count": len(clips),
                "total_cost": session.total_cost
            }

        except Exception as e:
            await self._handle_error(session_id, "clip_generation", e)
            raise

    async def compose_final_video(
        self,
        session_id: str,
        text_overlay: dict,
        audio_config: dict,
        intro_duration: float = 1.0,
        outro_duration: float = 1.0
    ):
        """Compose final video from approved clips"""

        try:
            # Load session
            session = await self._get_session(session_id)

            if not session.approved_clip_ids:
                raise Exception("No approved clips found")

            session.stage = SessionStage.FINAL_COMPOSITION

            # Load approved clips
            result = await self.db.execute(
                select(Asset).where(
                    Asset.id.in_(session.approved_clip_ids)
                )
            )
            approved_clips = result.scalars().all()

            # Format for agent (respect clip_order)
            clip_data = []
            for clip_id in session.clip_order or session.approved_clip_ids:
                clip = next((c for c in approved_clips if c.id == clip_id), None)
                if clip:
                    clip_data.append({
                        "id": clip.id,
                        "url": clip.url,
                        "duration": clip.metadata.get("duration", 3.0),
                        "order": len(clip_data) + 1
                    })

            # Send progress
            await ws_manager.send_progress(session_id, {
                "stage": "final_composition",
                "progress": 92,
                "message": "Composing final video...",
                "session_id": session_id
            })

            # Compose video
            from app.models.schemas import AgentInput

            compositor_input = AgentInput(
                session_id=session_id,
                data={
                    "selected_clips": clip_data,
                    "text_overlay": text_overlay,
                    "audio": audio_config,
                    "intro_duration": intro_duration,
                    "outro_duration": outro_duration
                }
            )

            compositor_output = await self.compositor.process(compositor_input)

            if not compositor_output.success:
                raise Exception(f"Composition failed: {compositor_output.error}")

            # Log cost
            await self._log_cost(
                session_id,
                "compositor",
                "ffmpeg",
                compositor_output.cost,
                compositor_output.duration,
                success=True
            )

            # Save final video
            final_video_data = compositor_output.data["final_video"]
            final_video_id = f"final_{uuid.uuid4().hex[:8]}"

            final_asset = Asset(
                id=final_video_id,
                session_id=session_id,
                asset_type=AssetType.FINAL_VIDEO,
                url=final_video_data["url"],
                metadata=final_video_data,
                cost=compositor_output.cost,
                model_used="ffmpeg",
                generation_time=compositor_output.duration
            )

            self.db.add(final_asset)

            # Update session
            session.final_video_id = final_video_id
            session.total_cost += compositor_output.cost
            session.stage = SessionStage.COMPLETE

            await self.db.commit()

            # Completion
            await ws_manager.send_progress(session_id, {
                "stage": "complete",
                "progress": 100,
                "message": "Your video is ready!",
                "session_id": session_id,
                "data": {
                    "final_video": final_video_data,
                    "total_cost": session.total_cost
                }
            })

            return {
                "status": "success",
                "final_video": final_video_data,
                "total_cost": session.total_cost
            }

        except Exception as e:
            await self._handle_error(session_id, "final_composition", e)
            raise
```

---

## 4. Video Generation API Endpoints

### 4.1 Add to Generation Router (routers/generation.py)

```python
from app.models.schemas import (
    GenerateClipsRequest,
    SaveApprovedClipsRequest,
    ComposeFinalVideoRequest
)

@router.post("/generate-clips")
async def generate_clips(
    request: GenerateClipsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate video clips from approved images"""

    orchestrator = VideoGenerationOrchestrator(db)

    background_tasks.add_task(
        orchestrator.generate_clips,
        session_id=request.session_id,
        video_prompt=request.video_prompt,
        clip_duration=request.clip_duration
    )

    return {
        "status": "processing",
        "estimated_duration": 180,
        "message": "Video clip generation started"
    }

@router.post("/save-approved-clips")
async def save_approved_clips(
    request: SaveApprovedClipsRequest,
    db: AsyncSession = Depends(get_db)
):
    """Save user's approved clips in desired order"""

    from sqlalchemy import select
    from app.models.database import Session as DBSession, SessionStage

    result = await db.execute(
        select(DBSession).where(DBSession.id == request.session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.approved_clip_ids = request.approved_clip_ids
    session.clip_order = request.clip_order
    session.stage = SessionStage.FINAL_COMPOSITION

    await db.commit()

    # Calculate estimated duration
    result = await db.execute(
        select(Asset).where(Asset.id.in_(request.approved_clip_ids))
    )
    clips = result.scalars().all()
    estimated_duration = sum(c.metadata.get("duration", 3.0) for c in clips)

    return {
        "success": True,
        "approved_count": len(request.approved_clip_ids),
        "estimated_duration": round(estimated_duration, 1),
        "message": "Clips saved to mood board"
    }

@router.post("/compose-final-video")
async def compose_final_video(
    request: ComposeFinalVideoRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate final ad video with all elements"""

    orchestrator = VideoGenerationOrchestrator(db)

    background_tasks.add_task(
        orchestrator.compose_final_video,
        session_id=request.session_id,
        text_overlay=request.text_overlay.dict(),
        audio_config=request.audio.dict(),
        intro_duration=request.intro_duration,
        outro_duration=request.outro_duration
    )

    return {
        "status": "processing",
        "estimated_duration": 35,
        "message": "Final video composition started"
    }
```

---

## 5. Testing Phase 3

### 5.1 Test Video Generation

```python
# tests/test_video_agent.py
import pytest
from app.agents.video_generator import VideoGeneratorAgent
from app.models.schemas import AgentInput

@pytest.mark.asyncio
async def test_video_generator():
    """Test Video Generator Agent"""

    agent = VideoGeneratorAgent()

    input_data = AgentInput(
        session_id="test_session",
        data={
            "approved_images": [
                {
                    "id": "img_001",
                    "url": "https://example.com/image1.png",
                    "view_type": "front"
                }
            ],
            "video_prompt": "product floating with dramatic lighting",
            "clip_duration": 3.0,
            "model": "stable-video-diffusion"
        }
    )

    result = await agent.process(input_data)

    assert result.success is True
    assert len(result.data["clips"]) == 1
    assert result.data["clips"][0]["url"].startswith("https://")
```

---

## 6. Deployment Checklist

- [ ] Video Generator Agent implemented and tested
- [ ] Composition Layer with FFmpeg working
- [ ] Storage Service (S3) configured
- [ ] Video generation endpoints functional
- [ ] Final composition endpoint functional
- [ ] FFmpeg installed on deployment server
- [ ] S3 bucket created and accessible
- [ ] Full end-to-end video flow tested

---

## 7. Next Steps

**Phase 3 Complete! ✅**

You should now have:
- ✅ Video Generator Agent (Stable Video Diffusion)
- ✅ Composition Layer (FFmpeg)
- ✅ Storage Service (S3)
- ✅ Complete backend pipeline (images → clips → final video)

**Proceed to:** [Phase_4_Frontend_UI.md](Phase_4_Frontend_UI.md)

---

## Document Metadata

- **Phase:** 3 (Video Generation & Processing)
- **Dependencies:** Phase 2 (completed)
- **Next Phase:** Phase 4 (Frontend & User Interface)
- **Estimated Duration:** 14 hours
- **Last Updated:** November 14, 2025
