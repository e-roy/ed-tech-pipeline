"""
Replicate Gemini Image Generator

Generates educational images using Google's Gemini model (nano-banana-pro)
via the Replicate API.
"""
import json
import replicate
import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ReplicateGeminiGenerator:
    """Generates images using Google Gemini via Replicate."""

    def __init__(self, api_key: str = None):
        """
        Initialize Replicate Gemini generator.

        Args:
            api_key: Replicate API key (defaults to AWS Secrets Manager, then env var)
        """
        # Try to get API key from parameter, then Secrets Manager, then env var
        if api_key:
            self.api_key = api_key
        else:
            # Try Secrets Manager first
            try:
                from app.services.secrets import get_secret
                self.api_key = get_secret("pipeline/replicate-api-key")
                logger.debug("Retrieved REPLICATE_API_KEY from AWS Secrets Manager")
            except Exception as e:
                logger.debug(f"Could not retrieve REPLICATE_API_KEY from Secrets Manager: {e}, falling back to env var")
                self.api_key = os.getenv("REPLICATE_API_KEY")

        if not self.api_key:
            logger.warning(
                "REPLICATE_API_KEY not set - Gemini image generation will fail. "
                "Add it to AWS Secrets Manager (pipeline/replicate-api-key) or .env file."
            )
            self.client = None
        else:
            # Create client with API token
            self.client = replicate.Client(api_token=self.api_key)

        self.model = "google/nano-banana"

        # Replicate pricing estimate for Gemini model
        self.estimated_cost_per_image = 0.02  # Approximate cost

    async def generate_image(
        self,
        visual_scene: Dict[str, Any],
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate image using Gemini via Replicate.

        Args:
            visual_scene: Structured scene object from Agent 3 containing:
                - description: Main scene description
                - composition: How elements are arranged
                - lighting: Lighting style
                - camera_angle: Camera perspective
                - key_elements: List of must-have objects
                - mood: Emotional tone
                - color_palette: Colors to use
            quality: Quality setting ("standard" = 2K, "hd" = 4K)

        Returns:
            {
                "success": bool,
                "url": str,  # Direct URL from Replicate
                "cost": float,
                "duration": float,
                "prompt_used": str,
                "error": str (if failed)
            }
        """
        start_time = time.time()

        try:
            if not self.client:
                raise ValueError("REPLICATE_API_KEY not configured")

            # Use visual_scene object as prompt (stringified JSON)
            prompt = json.dumps(visual_scene)

            logger.info(f"Generating Gemini image via Replicate: {prompt[:100]}...")

            # Map quality to resolution
            resolution = "4K" if quality == "hd" else "2K"

            # Run the model using the client instance
            output = self.client.run(
                self.model,
                input={
                    "prompt": prompt,
                    "resolution": resolution,
                    "aspect_ratio": "16:9",  # Landscape for video
                    "output_format": "png",
                    "safety_filter_level": "block_only_high"
                }
            )

            # Get the URL from output
            image_url = output.url() if hasattr(output, 'url') else str(output)

            if not image_url:
                raise ValueError("No image URL returned from Replicate")

            duration = time.time() - start_time

            logger.info(
                f"Gemini image generated in {duration:.2f}s (${self.estimated_cost_per_image:.4f})"
            )

            return {
                "success": True,
                "url": image_url,
                "cost": self.estimated_cost_per_image,
                "duration": duration,
                "prompt_used": prompt,
                "quality": quality,
                "model": self.model
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Gemini image generation failed: {e}")

            return {
                "success": False,
                "url": None,
                "cost": 0.0,
                "duration": duration,
                "error": str(e)
            }
