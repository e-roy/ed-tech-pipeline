"""Prompt Parser Service Client"""

from typing import Any, Dict

from app.config import settings
from app.services.base_client import BaseServiceClient


class PromptParserClient(BaseServiceClient):
    """Client for Prompt Parser microservice"""

    def __init__(self):
        super().__init__(
            base_url=settings.prompt_parser_url,
            timeout=10,  # 10 second timeout
            max_retries=3,
        )

    async def parse(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        brand_guidelines: Dict[str, Any] = None,
    ) -> tuple[Dict[str, Any], float]:
        """
        Parse prompt into structured scenes.

        Args:
            prompt: Text prompt
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            brand_guidelines: Optional brand guidelines

        Returns:
            Tuple of (parsed_data dict, cost float)

        Expected result format:
        {
            "scenes": [
                {
                    "prompt": "Scene description",
                    "duration": 7,
                    "transition": "fade"
                }
            ],
            "visual_direction": {...},
            "audio": {...},
            "text_overlays": [...]
        }
        """
        payload = {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "brand_guidelines": brand_guidelines or {},
        }

        response = await self._call_with_retry("POST", "/parse", payload)
        return self._parse_response(response)
