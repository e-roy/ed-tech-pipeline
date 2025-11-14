"""Video Generation Service Client"""

import asyncio
from typing import Any, Dict, List

from app.config import settings
from app.services.base_client import BaseServiceClient


class VideoGenClient(BaseServiceClient):
    """Client for Video Generation microservice"""

    def __init__(self):
        super().__init__(
            base_url=settings.video_gen_url,
            timeout=90,  # 90 second timeout (video gen is slow)
            max_retries=3,
        )

    async def generate(
        self,
        scene_prompt: str,
        reference_image_url: str,
        duration: int,
        aspect_ratio: str,
    ) -> tuple[Dict[str, Any], float]:
        """
        Generate video clip for a single scene.

        Args:
            scene_prompt: Scene description
            reference_image_url: Reference image URL for consistency
            duration: Clip duration in seconds
            aspect_ratio: Video aspect ratio

        Returns:
            Tuple of (video_data dict, cost float)

        Expected result format:
        {
            "video_url": "https://s3.../clip.mp4",
            "duration": 7,
            "resolution": "1080x1920"
        }
        """
        payload = {
            "scene_prompt": scene_prompt,
            "reference_image_url": reference_image_url,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        }

        response = await self._call_with_retry("POST", "/generate-video", payload)
        return self._parse_response(response)

    async def generate_parallel(
        self,
        scenes: List[Dict[str, Any]],
        reference_image_url: str,
        aspect_ratio: str,
    ) -> tuple[List[Dict[str, Any]], float]:
        """
        Generate video clips for multiple scenes in parallel.

        Uses semaphore to limit concurrent requests and avoid rate limits.

        Args:
            scenes: List of scene dicts with 'prompt' and 'duration'
            reference_image_url: Reference image URL for consistency
            aspect_ratio: Video aspect ratio

        Returns:
            Tuple of (list of video_data dicts, total cost)
        """
        semaphore = asyncio.Semaphore(settings.max_parallel_video_generations)

        async def generate_with_limit(scene: Dict[str, Any], index: int):
            """Generate single video with semaphore limiting"""
            async with semaphore:
                result, cost = await self.generate(
                    scene_prompt=scene.get("prompt", ""),
                    reference_image_url=reference_image_url,
                    duration=scene.get("duration", 5),
                    aspect_ratio=aspect_ratio,
                )
                # Add scene index to result for tracking
                result["scene_index"] = index
                return result, cost

        # Generate all clips in parallel (limited by semaphore)
        tasks = [
            generate_with_limit(scene, i) for i, scene in enumerate(scenes)
        ]
        results = await asyncio.gather(*tasks)

        # Separate results and costs
        clips = [r[0] for r in results]
        total_cost = sum(r[1] for r in results)

        return clips, total_cost
