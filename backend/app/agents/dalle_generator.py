"""
DALL-E 3 Generator Agent

Generates educational images using OpenAI's DALL-E 3 model.
"""
from openai import AsyncOpenAI
import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DALLEGenerator:
    """Generates images using DALL-E 3."""

    def __init__(self, api_key: str = None):
        """
        Initialize DALL-E generator.

        Args:
            api_key: OpenAI API key (or reads from OPENAI_API_KEY env)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - DALL-E generation will fail")

        self.client = AsyncOpenAI(api_key=self.api_key)

        # DALL-E 3 pricing (as of 2024)
        self.costs = {
            "standard": 0.040,  # $0.04 per image (1024x1024 or 1792x1024)
            "hd": 0.080  # $0.08 per image HD quality
        }

    async def generate_image(
        self,
        prompt: str,
        style: str = "educational",
        quality: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate image using DALL-E 3.

        Args:
            prompt: Description of image to generate
            style: Style hint ("educational", "realistic", "illustration")
            quality: "standard" or "hd"

        Returns:
            {
                "success": bool,
                "url": str,
                "cost": float,
                "duration": float,
                "prompt_used": str,
                "error": str (if failed)
            }
        """
        start_time = time.time()

        try:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not configured")

            # Build enhanced prompt for educational content
            enhanced_prompt = self._enhance_prompt(prompt, style)

            logger.info(f"Generating DALL-E 3 image: {enhanced_prompt[:100]}...")

            # Call DALL-E 3 API
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size="1792x1024",  # Landscape for video (16:9 aspect ratio)
                quality=quality,  # "standard" or "hd"
                n=1
            )

            image_url = response.data[0].url

            # Calculate cost
            cost = self.costs.get(quality, self.costs["standard"])

            duration = time.time() - start_time

            logger.info(
                f"DALL-E 3 image generated in {duration:.2f}s (${cost})"
            )

            return {
                "success": True,
                "url": image_url,
                "cost": cost,
                "duration": duration,
                "prompt_used": enhanced_prompt,
                "quality": quality
            }

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"DALL-E 3 generation failed: {e}")

            return {
                "success": False,
                "url": None,
                "cost": 0.0,
                "duration": duration,
                "error": str(e)
            }

    def _enhance_prompt(self, base_prompt: str, style: str) -> str:
        """
        Add style guidelines to prompt for consistent educational visuals.

        Args:
            base_prompt: Original prompt
            style: Style hint

        Returns:
            Enhanced prompt with style guidance
        """
        style_guides = {
            "educational": (
                "Educational diagram style, clean and clear, bright colors, "
                "labeled components, appropriate for middle school students "
                "(grades 6-7), scientific accuracy, professional quality, "
                "no text in image"
            ),
            "realistic": (
                "Photorealistic style, high detail, natural lighting, "
                "scientific accuracy, professional photography quality"
            ),
            "illustration": (
                "Hand-drawn illustration style, colorful, engaging for students, "
                "clear visual hierarchy, educational diagram quality"
            ),
            "diagram": (
                "Technical diagram style, clean lines, clear labels, "
                "educational infographic quality, bright colors on white background"
            )
        }

        guide = style_guides.get(style, style_guides["educational"])

        # Combine prompt with style guide
        enhanced = f"{base_prompt}. {guide}"

        # Ensure prompt isn't too long (DALL-E 3 has limits)
        if len(enhanced) > 4000:
            enhanced = enhanced[:3997] + "..."

        return enhanced
