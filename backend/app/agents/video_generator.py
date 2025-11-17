"""
Video Generator Agent
Person C - Video Pipeline Implementation

Purpose: Convert approved product images into animated video clips using
Image-to-Video models (Veo 3.1 via Replicate), with scene planning via LLM.

Based on PRD Section 4.4.
"""

import json
import time
import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional
import replicate

from app.agents.base import AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class VideoGeneratorAgent:
    """
    Generates video clips from images using AI video generation models.

    Features:
    - Scene planning with Llama 3.1 LLM
    - Parallel video generation via Veo 3.1 (via Replicate)
    - Audio disabled by default
    - Cost tracking per clip
    """

    def __init__(self, replicate_api_key: str):
        """
        Initialize the Video Generator Agent.

        Args:
            replicate_api_key: Replicate API key for video generation
        """
        self.api_key = replicate_api_key
        self.client = replicate.Client(api_token=replicate_api_key)

        # Model configurations (Replicate model IDs)
        self.models = {
            "gen-4-turbo": "minimax/video-01",
            "veo-3.1": "google/veo-3.1",
            "veo-3.1-fast": "google/veo-3.1-fast",
            "stable-video-diffusion": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438"
        }

        # Cost estimates (USD per second of video)
        # Gen-4-Turbo (Minimax Video-01): ~$0.015/sec (cheapest for testing!)
        # Veo 3.1: $0.20/sec without audio, $0.40/sec with audio
        # For 8-second clips: $0.12 (gen-4-turbo) vs $1.60 (veo-3.1)
        self.costs_per_second = {
            "gen-4-turbo": 0.015,  # Cheapest option!
            "veo-3.1": 0.20,  # Without audio
            "veo-3.1-fast": 0.20,  # Without audio
            "stable-video-diffusion": 0.40 / 2.33  # ~$0.17/sec (flat $0.40 for 2.33s clip)
        }

        # LLM for scene planning
        self.llm_model = "meta/meta-llama-3-70b-instruct"

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Generate video clips from approved images.

        Args:
            input: AgentInput containing:
                - data["approved_images"]: List of image objects with URLs
                - data["video_prompt"]: User's scene description
                - data["clip_duration"]: Duration per clip (default 3.0s)
                - data["model"]: Model to use (default "stable-video-diffusion")

        Returns:
            AgentOutput containing:
                - data["clips"]: List of generated clip objects with URLs
                - data["total_cost"]: Total generation cost
                - cost: Total cost
                - duration: Total time taken
        """
        try:
            start_time = time.time()

            # Extract input parameters
            approved_images = input.data["approved_images"]
            video_prompt = input.data.get("video_prompt", "product showcase")
            clip_duration = input.data.get("clip_duration", 3.0)
            model_name = input.data.get("model", "stable-video-diffusion")

            if not approved_images:
                raise ValueError("No approved images provided")

            logger.info(
                f"[{input.session_id}] Generating {len(approved_images)} video clips "
                f"with {model_name}"
            )

            # Step 1: Plan scenes with LLM
            logger.info(f"[{input.session_id}] Planning scenes with LLM")
            scenes = await self._plan_video_scenes(
                approved_images,
                video_prompt,
                input.session_id
            )

            # Step 2: Generate video clips in parallel
            tasks = []
            for i, image_data in enumerate(approved_images):
                # Match scene to image
                scene = next(
                    (s for s in scenes if s["image_view"] == image_data.get("view_type", "unknown")),
                    scenes[0] if scenes else {
                        "scene_prompt": video_prompt,
                        "motion_intensity": 0.5,
                        "camera_movement": "static"
                    }
                )

                task = self._generate_single_clip(
                    session_id=input.session_id,
                    model=model_name,
                    image_url=image_data["url"],
                    scene_prompt=scene["scene_prompt"],
                    duration=clip_duration,
                    source_image_id=image_data.get("id", f"img_{i}"),
                    index=i
                )
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            clips = []
            total_cost = 0.0
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_msg = f"Clip {i} generation failed: {result}"
                    logger.error(f"[{input.session_id}] {error_msg}")
                    errors.append(error_msg)
                    continue

                clips.append(result)
                total_cost += result["cost"]

            duration = time.time() - start_time

            # Determine success (at least one clip generated)
            success = len(clips) > 0

            if success:
                logger.info(
                    f"[{input.session_id}] Generated {len(clips)}/{len(approved_images)} clips "
                    f"in {duration:.2f}s (${total_cost:.2f})"
                )
            else:
                logger.error(
                    f"[{input.session_id}] All clip generations failed"
                )

            return AgentOutput(
                success=success,
                data={
                    "clips": clips,
                    "total_cost": total_cost,
                    "failed_count": len(errors),
                    "errors": errors if errors else None,
                    "scenes_planned": scenes
                },
                cost=total_cost,
                duration=duration,
                error=None if success else "All video clip generations failed"
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{input.session_id}] Video generation failed: {e}")

            return AgentOutput(
                success=False,
                data={},
                cost=0.0,
                duration=duration,
                error=str(e)
            )

    async def _plan_video_scenes(
        self,
        approved_images: List[Dict[str, Any]],
        video_prompt: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to create scene descriptions for each image.

        Args:
            approved_images: List of image objects
            video_prompt: User's overall scene description
            session_id: Session ID for logging

        Returns:
            List of scene objects with prompts and motion parameters
        """
        try:
            system_prompt = """You are a video scene director for product advertisements.

Given:
- Multiple product images with different views (front, side, back, top, detail, lifestyle)
- User's overall scene description

Your task:
Create specific scene descriptions for each image that:
1. Maintain the user's creative vision
2. Enhance each image's unique angle/view
3. Add appropriate motion and cinematography
4. Keep descriptions concise but vivid

Output ONLY valid JSON in this exact format:
{
    "scenes": [
        {
            "image_view": "front",
            "scene_prompt": "detailed scene description with motion",
            "camera_movement": "slow zoom in|pan left|static|follow cam",
            "motion_intensity": 0.5
        }
    ]
}

Motion intensity: 0.0 (minimal) to 1.0 (maximum)
Keep each scene_prompt under 200 characters."""

            # Build user prompt
            image_views = [
                {
                    "view": img.get("view_type", "unknown"),
                    "id": img.get("id", "")
                }
                for img in approved_images
            ]

            user_prompt = f"""User's scene description: {video_prompt}

Product images:
{json.dumps(image_views, indent=2)}

Create scene-specific prompts for each image view."""

            logger.debug(f"[{session_id}] Calling LLM for scene planning")

            # Call Llama 3.1
            output = await self.client.async_run(
                self.llm_model,
                input={
                    "system_prompt": system_prompt,
                    "prompt": user_prompt,
                    "max_tokens": 1500,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )

            # Concatenate streaming output
            full_response = "".join([chunk for chunk in output])

            # Parse JSON response
            full_response = full_response.strip()
            start_idx = full_response.find("{")
            end_idx = full_response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                logger.warning(f"[{session_id}] No JSON found in LLM response, using defaults")
                return self._create_default_scenes(approved_images, video_prompt)

            json_str = full_response[start_idx:end_idx]
            parsed = json.loads(json_str)

            scenes = parsed.get("scenes", [])

            if not scenes:
                logger.warning(f"[{session_id}] No scenes in LLM response, using defaults")
                return self._create_default_scenes(approved_images, video_prompt)

            logger.info(f"[{session_id}] Planned {len(scenes)} scenes with LLM")
            return scenes

        except Exception as e:
            logger.error(f"[{session_id}] Scene planning failed: {e}, using defaults")
            return self._create_default_scenes(approved_images, video_prompt)

    def _create_default_scenes(
        self,
        approved_images: List[Dict[str, Any]],
        video_prompt: str
    ) -> List[Dict[str, Any]]:
        """
        Create default scene descriptions if LLM planning fails.

        Args:
            approved_images: List of image objects
            video_prompt: User's scene description

        Returns:
            List of default scene objects
        """
        default_scenes = []
        for img in approved_images:
            view_type = img.get("view_type", "product")
            default_scenes.append({
                "image_view": view_type,
                "scene_prompt": f"{video_prompt}, {view_type} view",
                "camera_movement": "static",
                "motion_intensity": 0.5
            })

        return default_scenes

    async def _generate_single_clip(
        self,
        session_id: str,
        model: str,
        image_url: str,
        scene_prompt: str,
        duration: float,
        source_image_id: str,
        index: int
    ) -> Dict[str, Any]:
        """
        Generate a single video clip via Replicate API (Veo 3.1 or SVD).

        Args:
            session_id: Session ID for logging
            model: Model name to use
            image_url: Source image URL
            scene_prompt: Scene description
            duration: Clip duration in seconds
            source_image_id: ID of source image
            index: Clip index for logging

        Returns:
            Clip result dict with URL, metadata, cost, duration

        Raises:
            Exception: If video generation fails
        """
        start = time.time()

        try:
            model_id = self.models[model]

            # Configure based on model type
            if model.startswith("veo-"):
                # Veo 3.1 configuration
                # Round duration to nearest valid value (4, 6, or 8 seconds)
                valid_durations = [4, 6, 8]
                duration_seconds = min(valid_durations, key=lambda x: abs(x - duration))

                model_input = {
                    "prompt": scene_prompt,
                    "image": image_url,
                    "duration": duration_seconds,
                    "aspect_ratio": "16:9",
                    "resolution": "1080p",
                    "generate_audio": False  # AUDIO DISABLED
                }

                logger.debug(
                    f"[{session_id}] Generating Veo 3.1 clip {index + 1} "
                    f"(duration: {duration_seconds}s, audio: disabled)"
                )

                # Call Replicate API
                output = await self.client.async_run(model_id, input=model_input)

                # Extract video URL
                if isinstance(output, str):
                    video_url = output
                elif isinstance(output, list) and output:
                    video_url = output[0]
                else:
                    raise ValueError(f"Unexpected output format: {type(output)}")

                if not video_url:
                    raise ValueError("No video URL returned from Replicate")

                generation_time = time.time() - start
                cost = self.costs_per_second[model] * duration_seconds

                logger.debug(
                    f"[{session_id}] Veo 3.1 clip {index + 1} generated in {generation_time:.2f}s"
                )

                return {
                    "id": f"clip_{uuid.uuid4().hex[:8]}",
                    "url": str(video_url),
                    "source_image_id": source_image_id,
                    "duration": duration_seconds,
                    "resolution": "1920x1080",
                    "fps": 24,
                    "cost": cost,
                    "generation_time": generation_time,
                    "model": model,
                    "scene_prompt": scene_prompt[:100] + "...",
                    "motion_intensity": None,
                    "audio_enabled": False
                }

            elif model == "gen-4-turbo":
                # Minimax Video-01 configuration
                # Generates 6-second videos at 720p, 25fps
                duration_seconds = 6.0  # Fixed duration for Minimax Video-01

                model_input = {
                    "prompt": scene_prompt,
                    "first_frame_image": image_url,  # Use image as first frame
                    "prompt_optimizer": True  # Enable prompt optimization for better quality
                }

                logger.debug(
                    f"[{session_id}] Generating Minimax Video-01 clip {index + 1} "
                    f"(duration: {duration_seconds}s, 720p@25fps)"
                )

                # Call Replicate API
                output = await self.client.async_run(model_id, input=model_input)

                # Extract video URL
                if isinstance(output, str):
                    video_url = output
                elif isinstance(output, list) and output:
                    video_url = output[0]
                else:
                    raise ValueError(f"Unexpected output format: {type(output)}")

                if not video_url:
                    raise ValueError("No video URL returned from Replicate")

                generation_time = time.time() - start
                cost = self.costs_per_second[model] * duration_seconds

                logger.debug(
                    f"[{session_id}] Minimax Video-01 clip {index + 1} generated in {generation_time:.2f}s"
                )

                return {
                    "id": f"clip_{uuid.uuid4().hex[:8]}",
                    "url": str(video_url),
                    "source_image_id": source_image_id,
                    "duration": duration_seconds,
                    "resolution": "1280x720",
                    "fps": 25,
                    "cost": cost,
                    "generation_time": generation_time,
                    "model": model,
                    "scene_prompt": scene_prompt[:100] + "...",
                    "motion_intensity": None,
                    "audio_enabled": False
                }

            else:
                # Stable Video Diffusion configuration
                # Motion bucket ID: 0-255 scale (higher = more motion)
                motion_bucket_id = 127  # Default medium motion

                # Choose frames based on duration
                # 14 frames = 2.33s, 25 frames = 4.17s at 6fps
                video_length = "14_frames_with_svd" if duration <= 3 else "25_frames_with_svd_xt"
                num_frames = 14 if video_length == "14_frames_with_svd" else 25
                fps = 6  # SVD default FPS

                model_input = {
                    "input_image": image_url,
                    "motion_bucket_id": motion_bucket_id,
                    "cond_aug": 0.02,
                    "decoding_t": 14,
                    "video_length": video_length,
                    "sizing_strategy": "maintain_aspect_ratio",
                    "frames_per_second": fps
                }

                logger.debug(
                    f"[{session_id}] Generating SVD clip {index + 1} "
                    f"(duration: ~{num_frames/fps:.1f}s)"
                )

                # Call Replicate API
                output = await self.client.async_run(model_id, input=model_input)

                # Extract video URL
                if isinstance(output, str):
                    video_url = output
                elif isinstance(output, list) and output:
                    video_url = output[0]
                else:
                    raise ValueError(f"Unexpected output format: {type(output)}")

                if not video_url:
                    raise ValueError("No video URL returned from Replicate")

                generation_time = time.time() - start
                actual_duration = round(num_frames / fps, 2)
                cost = self.costs_per_second[model] * actual_duration

                logger.debug(
                    f"[{session_id}] SVD clip {index + 1} generated in {generation_time:.2f}s"
                )

                return {
                    "id": f"clip_{uuid.uuid4().hex[:8]}",
                    "url": str(video_url),
                    "source_image_id": source_image_id,
                    "duration": actual_duration,
                    "num_frames": num_frames,
                    "resolution": "1024x576",
                    "fps": fps,
                    "cost": cost,
                    "generation_time": generation_time,
                    "model": model,
                    "scene_prompt": scene_prompt[:100] + "...",
                    "motion_intensity": motion_bucket_id / 255.0,
                    "audio_enabled": False
                }

        except Exception as e:
            generation_time = time.time() - start
            logger.error(
                f"[{session_id}] Clip {index + 1} generation failed "
                f"after {generation_time:.2f}s: {e}"
            )
            raise
