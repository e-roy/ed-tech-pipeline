"""Image Generation Service Client"""

from typing import Any, Dict

from app.config import settings
from app.services.base_client import BaseServiceClient


class ImageGenClient(BaseServiceClient):
    """Client for Image Generation microservice"""

    def __init__(self):
        super().__init__(
            base_url=settings.image_gen_url,
            timeout=15,  # 15 second timeout
            max_retries=3,
        )

    async def generate(
        self,
        prompt: str,
        style: str = None,
        visual_direction: Dict[str, Any] = None,
    ) -> tuple[Dict[str, Any], float]:
        """
        Generate reference image for visual consistency.

        Args:
            prompt: Image generation prompt
            style: Optional style override
            visual_direction: Optional visual direction from prompt parser

        Returns:
            Tuple of (image_data dict, cost float)

        Expected result format:
        {
            "image_url": "https://s3.../image.jpg",
            "seed": 12345,
            "model": "flux-pro"
        }
        """
        payload = {
            "prompt": prompt,
            "style": style,
            "visual_direction": visual_direction or {},
        }

        response = await self._call_with_retry("POST", "/generate-image", payload)
        return self._parse_response(response)
