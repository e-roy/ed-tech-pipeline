"""
Batch Image Generator Agent
Person B - Hours 4-8: Batch Image Generation

Purpose: Generate multiple product images in parallel using structured prompts
from Prompt Parser Agent, ensuring visual consistency via seed control.

Based on PRD Section 4.3.
"""

import time
import asyncio
import logging
from typing import Optional
import replicate

from app.agents.base import AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class BatchImageGeneratorAgent:
    """
    Generates multiple product images in parallel using AI image generation.

    Uses Flux-Pro or SDXL via Replicate to generate consistent product
    images from structured prompts.
    """

    def __init__(self, replicate_api_key: str):
        """
        Initialize the Batch Image Generator Agent.

        Args:
            replicate_api_key: Replicate API key for image generation
        """
        self.api_key = replicate_api_key
        self.client = replicate.Client(api_token=replicate_api_key)

        # Model configurations
        self.models = {
            "flux-pro": "black-forest-labs/flux-pro",
            "flux-dev": "black-forest-labs/flux-dev",
            "flux-schnell": "black-forest-labs/flux-schnell",
            "sdxl": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
        }

        # Cost estimates (USD per image)
        self.costs = {
            "flux-pro": 0.05,
            "flux-dev": 0.025,
            "flux-schnell": 0.003,
            "sdxl": 0.01
        }

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Generate multiple images in parallel from structured prompts.

        Args:
            input: AgentInput containing:
                - data["image_prompts"]: List of prompt objects from Prompt Parser
                - data["model"]: Model to use ("flux-pro", "flux-dev", "flux-schnell", "sdxl")

        Returns:
            AgentOutput containing:
                - data["images"]: List of generated image objects with URLs
                - data["total_cost"]: Total cost for all images
                - cost: Total cost (same as data["total_cost"])
                - duration: Total time taken
        """
        try:
            start_time = time.time()

            # Extract input parameters
            image_prompts = input.data["image_prompts"]
            model_name = input.data.get("model", "flux-schnell")  # Default to schnell for testing

            if model_name not in self.models:
                raise ValueError(
                    f"Invalid model '{model_name}'. "
                    f"Choose from: {list(self.models.keys())}"
                )

            logger.info(
                f"[{input.session_id}] Generating {len(image_prompts)} images "
                f"with {model_name}"
            )

            # Generate images in parallel
            tasks = []
            for i, prompt_data in enumerate(image_prompts):
                task = self._generate_single_image(
                    session_id=input.session_id,
                    model=model_name,
                    prompt_data=prompt_data,
                    index=i
                )
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            images = []
            total_cost = 0.0
            errors = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_msg = f"Image {i} generation failed: {result}"
                    logger.error(f"[{input.session_id}] {error_msg}")
                    errors.append(error_msg)
                    continue

                images.append(result)
                total_cost += result["cost"]

            duration = time.time() - start_time

            # Determine success (at least one image generated)
            success = len(images) > 0

            if success:
                logger.info(
                    f"[{input.session_id}] Generated {len(images)}/{len(image_prompts)} images "
                    f"in {duration:.2f}s (${total_cost:.2f})"
                )
            else:
                logger.error(
                    f"[{input.session_id}] All image generations failed"
                )

            return AgentOutput(
                success=success,
                data={
                    "images": images,
                    "total_cost": total_cost,
                    "failed_count": len(errors),
                    "errors": errors if errors else None
                },
                cost=total_cost,
                duration=duration,
                error=None if success else "All image generations failed"
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{input.session_id}] Batch image generation failed: {e}")

            return AgentOutput(
                success=False,
                data={},
                cost=0.0,
                duration=duration,
                error=str(e)
            )

    async def _generate_single_image(
        self,
        session_id: str,
        model: str,
        prompt_data: dict,
        index: int
    ) -> dict:
        """
        Generate a single image via Replicate API.

        Args:
            session_id: Session ID for logging
            model: Model name to use
            prompt_data: Prompt object with prompt, seed, etc.
            index: Image index for logging

        Returns:
            Image result dict with URL, metadata, cost, duration

        Raises:
            Exception: If image generation fails
        """
        start = time.time()

        try:
            model_id = self.models[model]

            # Build model input based on model type
            if model.startswith("flux"):
                model_input = self._build_flux_input(prompt_data)
            else:  # SDXL
                model_input = self._build_sdxl_input(prompt_data)

            logger.debug(
                f"[{session_id}] Generating image {index + 1} "
                f"({prompt_data.get('view_type', 'unknown')} view)"
            )

            # Call Replicate API
            output = await self.client.async_run(model_id, input=model_input)

            # Extract image URL (output format varies by model)
            if isinstance(output, list):
                image_url = output[0] if output else None
            else:
                image_url = output

            if not image_url:
                raise ValueError("No image URL returned from Replicate")

            duration = time.time() - start
            cost = self.costs[model]

            logger.debug(
                f"[{session_id}] Image {index + 1} generated in {duration:.2f}s"
            )

            return {
                "url": str(image_url),
                "view_type": prompt_data.get("view_type", "unknown"),
                "seed": prompt_data.get("seed", 0),
                "cost": cost,
                "duration": duration,
                "model": model,
                "resolution": "1024x1024",
                "prompt": prompt_data.get("prompt", "")[:100] + "..."  # Truncate for storage
            }

        except Exception as e:
            duration = time.time() - start
            logger.error(
                f"[{session_id}] Image {index + 1} generation failed "
                f"after {duration:.2f}s: {e}"
            )
            raise

    def _build_flux_input(self, prompt_data: dict) -> dict:
        """
        Build input parameters for Flux models.

        Args:
            prompt_data: Prompt object from Prompt Parser

        Returns:
            Flux model input dict
        """
        return {
            "prompt": prompt_data["prompt"],
            "guidance": prompt_data.get("guidance_scale", 7.5),
            "num_outputs": 1,
            "aspect_ratio": "1:1",
            "output_format": "png",
            "output_quality": 100,
            "safety_tolerance": 2,
            "seed": prompt_data.get("seed", 0)
        }

    def _build_sdxl_input(self, prompt_data: dict) -> dict:
        """
        Build input parameters for SDXL model.

        Args:
            prompt_data: Prompt object from Prompt Parser

        Returns:
            SDXL model input dict
        """
        return {
            "prompt": prompt_data["prompt"],
            "negative_prompt": prompt_data.get(
                "negative_prompt",
                "blurry, distorted, low quality, watermark, text"
            ),
            "width": 1024,
            "height": 1024,
            "guidance_scale": prompt_data.get("guidance_scale", 7.5),
            "num_inference_steps": 50,
            "seed": prompt_data.get("seed", 0)
        }
