"""Composition Service Client"""

from typing import Any, Dict, List

from app.config import settings
from app.services.base_client import BaseServiceClient


class CompositionClient(BaseServiceClient):
    """Client for Video Composition microservice"""

    def __init__(self):
        super().__init__(
            base_url=settings.composition_url,
            timeout=30,  # 30 second timeout
            max_retries=3,
        )

    async def compose(
        self,
        scenes: List[Dict[str, Any]],
        audio: Dict[str, Any] = None,
        text_overlays: List[Dict[str, Any]] = None,
    ) -> tuple[Dict[str, Any], float]:
        """
        Compose final video from clips.

        Args:
            scenes: List of scene dicts with video_url, start_time, end_time, transition
            audio: Optional audio configuration
            text_overlays: Optional text overlays

        Returns:
            Tuple of (composition_data dict, cost float)

        Expected result format:
        {
            "video_url": "https://s3.../final.mp4",
            "thumbnail_url": "https://s3.../thumbnail.jpg",
            "duration": 30,
            "resolution": "1080x1920",
            "file_size_mb": 12.5
        }
        """
        payload = {
            "scenes": scenes,
            "audio": audio or {},
            "text_overlays": text_overlays or [],
        }

        response = await self._call_with_retry("POST", "/compose", payload)
        return self._parse_response(response)
