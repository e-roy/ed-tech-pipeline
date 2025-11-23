"""
Replicate API Video Generation Service

Generates video clips using Replicate's hosted models.
Default: Minimax video-01 (~$0.035 per 5s video)
"""
import asyncio
import httpx
import replicate
from typing import Optional, Dict, Any

from app.config import get_settings


class ReplicateVideoService:
    """Service for generating videos using Replicate's API."""

    # Available models on Replicate
    MODELS = {
        "minimax": "minimax/video-01",  # Cheapest ~$0.035/5s
        "kling": "kwaivgi/kling-v1.5-pro",  # Higher quality ~$0.15/5s
        "luma": "luma/dream-machine",  # High quality ~$0.20/5s
        "veo3": "google/veo-3",  # Google Veo 3 - High quality ~$1.20/6s (without audio)
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Replicate video service.

        Args:
            api_key: Replicate API key. If not provided, reads from settings.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        settings = get_settings()
        self.api_key = api_key or settings.REPLICATE_API_KEY

        if not self.api_key:
            logger.error("REPLICATE_API_KEY not configured in ReplicateVideoService")
            raise ValueError("REPLICATE_API_KEY not configured")

        # Create Replicate client with explicit API token (like other agents do)
        self.client = replicate.Client(api_token=self.api_key)
        logger.info(f"ReplicateVideoService initialized with API key (starts with: {self.api_key[:5]}..., length: {len(self.api_key)})")

    async def generate_video(
        self,
        prompt: str,
        model: str = "minimax",
        duration: int = 5,
        seed: Optional[int] = None,
    ) -> str:
        """
        Generate a video from a text prompt.

        Args:
            prompt: Text description of the video to generate
            model: Model to use ("minimax", "kling", "luma", "veo3")
            duration: Approximate video duration (model-dependent)
            seed: Optional random seed for reproducibility

        Returns:
            URL of the generated video
        """
        model_id = self.MODELS.get(model, self.MODELS["minimax"])

        # Run in thread to avoid blocking
        output = await asyncio.to_thread(
            self._run_prediction,
            model_id,
            prompt,
            duration,
            seed
        )

        return output

    def _run_prediction(self, model_id: str, prompt: str, duration: int, seed: Optional[int] = None) -> str:
        """
        Run the prediction synchronously.

        Args:
            model_id: Replicate model identifier
            prompt: Text prompt
            duration: Video duration
            seed: Optional random seed for reproducibility

        Returns:
            URL of the generated video
        """
        # Build input based on model
        if "minimax" in model_id:
            input_data = {
                "prompt": prompt,
                "prompt_optimizer": True,
            }
            # Add seed if provided (Minimax supports seed)
            if seed is not None:
                input_data["seed"] = seed
        elif "kling" in model_id:
            input_data = {
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": "16:9",
            }
            # Add seed if provided (Kling supports seed)
            if seed is not None:
                input_data["seed"] = seed
        elif "luma" in model_id:
            input_data = {
                "prompt": prompt,
                "aspect_ratio": "16:9",
            }
            # Luma may not support seed - only add if provided
            if seed is not None:
                input_data["seed"] = seed
        elif "veo-3" in model_id or "veo3" in model_id:
            input_data = {
                "prompt": prompt,
                "duration": 6,  # 6-second clips to match pipeline
                "aspect_ratio": "16:9",
                "resolution": "1080p",
                "generate_audio": False,  # Disable audio to save cost (agent 5 adds its own audio)
            }
            if seed is not None:
                input_data["seed"] = seed
        else:
            input_data = {
                "prompt": prompt,
            }
            if seed is not None:
                input_data["seed"] = seed

        # Run the model using the client instance (explicit API token)
        try:
            output = self.client.run(model_id, input=input_data)
        except Exception as e:
            # Better error handling to see what Replicate actually returns
            import logging
            import json
            logger = logging.getLogger(__name__)

            # Log full exception details for debugging
            logger.error(f"=" * 80)
            logger.error(f"REPLICATE API ERROR for model '{model_id}'")
            logger.error(f"Exception type: {type(e).__module__}.{type(e).__name__}")
            logger.error(f"Exception message: {str(e)}")
            logger.error(f"Input parameters: {json.dumps(input_data, indent=2)}")

            # Log exception chain
            if hasattr(e, '__cause__') and e.__cause__:
                logger.error(f"Caused by: {type(e.__cause__).__name__}: {str(e.__cause__)}")

            # Check if this is a JSONDecodeError (Replicate returned HTML instead of JSON)
            is_json_error = isinstance(e, json.JSONDecodeError) or (hasattr(e, '__cause__') and isinstance(e.__cause__, json.JSONDecodeError))

            if is_json_error:
                logger.error("ERROR TYPE: Non-JSON response (likely HTML error page)")
                logger.error("PROBABLE CAUSES:")
                logger.error("  1. Model infrastructure issue (502/503/504 server error)")
                logger.error("  2. Model not found or not accessible (404)")
                logger.error("  3. Access denied - requires special permissions (403)")
                logger.error("  4. Model requires billing setup or waitlist approval")

                # Provide user-friendly error messages based on model
                if "veo" in model_id.lower():
                    logger.error(f"=" * 80)
                    raise RuntimeError(
                        f"Google Veo 3 is currently unavailable via Replicate API.\n\n"
                        f"Possible reasons:\n"
                        f"  • Replicate infrastructure issue (temporary)\n"
                        f"  • Model requires special access or billing approval\n"
                        f"  • Model may be in limited preview/waitlist\n"
                        f"  • Your Replicate account may not have access\n\n"
                        f"Recommendation: Try using 'kling' or 'minimax' models instead, "
                        f"or check Replicate's status page and model documentation."
                    )
                else:
                    logger.error(f"=" * 80)
                    raise RuntimeError(
                        f"Model '{model_id}' returned non-JSON response from Replicate.\n"
                        f"This usually indicates:\n"
                        f"  • Server error (502/503/504)\n"
                        f"  • Model not found or inaccessible\n"
                        f"  • Authentication/permission issue\n\n"
                        f"Check Replicate's documentation for this model and verify your account has access."
                    )

            # For other errors, provide helpful context
            logger.error(f"ERROR TYPE: {type(e).__name__}")
            logger.error(f"=" * 80)

            error_message = str(e)
            if "authentication" in error_message.lower() or "unauthorized" in error_message.lower():
                raise RuntimeError(
                    f"Authentication error for model '{model_id}'.\n"
                    f"Verify your REPLICATE_API_KEY is correct and has the necessary permissions."
                )
            elif "rate limit" in error_message.lower() or "throttle" in error_message.lower():
                raise RuntimeError(
                    f"Rate limit exceeded for model '{model_id}'.\n"
                    f"Too many concurrent requests. The system will retry automatically."
                )
            else:
                raise RuntimeError(
                    f"Replicate API error for model '{model_id}': {error_message}\n\n"
                    f"See logs above for full details."
                )

        # Handle different output formats
        if isinstance(output, str):
            return output
        elif isinstance(output, list) and len(output) > 0:
            return output[0]
        elif hasattr(output, 'url'):
            return output.url
        else:
            # Try to iterate (FileOutput objects)
            for item in output:
                if isinstance(item, str):
                    return item
                elif hasattr(item, 'url'):
                    return item.url
            raise RuntimeError(f"Unexpected output format: {output}")

    async def generate_video_from_image(
        self,
        prompt: str,
        image_url: str,
        model: str = "minimax",
        seed: Optional[int] = None,
    ) -> str:
        """
        Generate a video from an image and text prompt.

        Args:
            prompt: Text description of the motion/action
            image_url: URL of the source image
            model: Model to use
            seed: Optional random seed for reproducibility

        Returns:
            URL of the generated video
        """
        model_id = self.MODELS.get(model, self.MODELS["minimax"])

        output = await asyncio.to_thread(
            self._run_image_to_video,
            model_id,
            prompt,
            image_url,
            seed
        )

        return output

    def _run_image_to_video(self, model_id: str, prompt: str, image_url: str, seed: Optional[int] = None) -> str:
        """
        Run image-to-video prediction synchronously.
        """
        if "minimax" in model_id:
            input_data = {
                "prompt": prompt,
                "first_frame_image": image_url,
            }
            if seed is not None:
                input_data["seed"] = seed
        elif "kling" in model_id:
            input_data = {
                "prompt": prompt,
                "start_image": image_url,
                "aspect_ratio": "16:9",
                "duration": 5,  # Explicit 5-second clips
                "cfg_scale": 0.8,  # Higher adherence to source image (default is 0.5)
                "negative_prompt": "camera zoom, rapid panning, morphing, transformation, sudden movements"
            }
            if seed is not None:
                input_data["seed"] = seed
        elif "veo-3" in model_id or "veo3" in model_id:
            input_data = {
                "prompt": prompt,
                "image": image_url,
                "duration": 6,  # 6-second clips to match pipeline
                "aspect_ratio": "16:9",
                "resolution": "1080p",
                "generate_audio": False,  # Disable audio to save cost
            }
            if seed is not None:
                input_data["seed"] = seed
        else:
            input_data = {
                "prompt": prompt,
                "image": image_url,
            }
            if seed is not None:
                input_data["seed"] = seed

        # Run the model using the client instance (explicit API token)
        output = self.client.run(model_id, input=input_data)

        # Handle output format
        if isinstance(output, str):
            return output
        elif isinstance(output, list) and len(output) > 0:
            return output[0]
        elif hasattr(output, 'url'):
            return output.url
        else:
            for item in output:
                if isinstance(item, str):
                    return item
                elif hasattr(item, 'url'):
                    return item.url
            raise RuntimeError(f"Unexpected output format: {output}")


async def generate_scene_videos(
    script: Dict[str, Any],
    api_key: Optional[str] = None,
    model: str = "minimax",
    progress_callback: Optional[callable] = None
) -> Dict[str, str]:
    """
    Generate videos for all script sections.

    Args:
        script: Script data with visual_prompt for each section
        api_key: Replicate API key
        model: Model to use ("minimax", "kling", "luma", "veo3")
        progress_callback: Async callback for progress updates

    Returns:
        Dictionary mapping section names to video URLs
    """
    service = ReplicateVideoService(api_key)
    sections = ["hook", "concept", "process", "conclusion"]
    video_urls = {}

    for i, section in enumerate(sections):
        section_data = script.get(section, {})
        visual_prompt = section_data.get("visual_prompt", "")

        if not visual_prompt:
            # Fallback: generate prompt from text
            text = section_data.get("text", "")
            visual_prompt = f"Cinematic scene: {text[:200]}"

        if progress_callback:
            await progress_callback(f"Generating video {i+1}/4: {section}...")

        try:
            video_url = await service.generate_video(
                prompt=visual_prompt,
                model=model
            )
            video_urls[section] = video_url

        except Exception as e:
            raise RuntimeError(f"Failed to generate video for {section}: {e}")

    return video_urls
