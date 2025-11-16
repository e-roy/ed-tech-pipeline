"""
Batch Image Generator Agent

Purpose: Generate multiple images for video scripts using:
- 60% Educational Templates (customized with text overlays)
- 40% DALL-E 3 AI Generation

Each script part (hook, concept, process, conclusion) gets 2-3 images.
"""

import time
import asyncio
import logging
from typing import Optional, Dict, List, Any
from io import BytesIO

from app.agents.base import AgentInput, AgentOutput
from app.agents.template_matcher import TemplateMatcher
from app.agents.psd_customizer import PSDCustomizer
from app.agents.dalle_generator import DALLEGenerator
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class BatchImageGeneratorAgent:
    """
    Generates images for video scripts using templates (60%) and DALL-E 3 (40%).

    Strategy:
    - Tries to match templates first based on key concepts
    - Falls back to DALL-E 3 for images without template matches
    - Targets 60% template usage to minimize costs
    """

    def __init__(self, openai_api_key: str = None):
        """
        Initialize the Batch Image Generator Agent.

        Args:
            openai_api_key: OpenAI API key for DALL-E 3
        """
        self.template_matcher = TemplateMatcher()
        self.psd_customizer = PSDCustomizer()
        self.dalle_generator = DALLEGenerator(api_key=openai_api_key)
        self.storage_service = StorageService()

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Generate images for each part of a video script.

        Args:
            input: AgentInput containing:
                - data["script"]: Script object with {hook, concept, process, conclusion}
                - data["images_per_part"]: Number of images per script part (default: 2)
                - data["prefer_templates"]: Prefer templates over AI (default: True)

        Returns:
            AgentOutput containing:
                - data["micro_scenes"]: {
                    hook: {images: [{image: url, metadata: {...}}]},
                    concept: {images: [{image: url, metadata: {...}}]},
                    process: {images: [{image: url, metadata: {...}}]},
                    conclusion: {images: [{image: url, metadata: {...}}]},
                  }
                - data["cost"]: Total cost for all images
                - data["stats"]: {templates_used: int, dalle_used: int}
                - cost: Total cost (same as data["cost"])
                - duration: Total time taken
        """
        try:
            start_time = time.time()

            # Extract input parameters
            script = input.data["script"]
            images_per_part = input.data.get("images_per_part", 2)
            prefer_templates = input.data.get("prefer_templates", True)

            logger.info(
                f"[{input.session_id}] Generating {images_per_part} images per script part "
                f"(prefer_templates={prefer_templates})"
            )

            # Generate images for each script part in parallel
            script_parts = ["hook", "concept", "process", "conclusion"]
            all_tasks = []
            task_metadata = []  # Track which task belongs to which part

            for part_name in script_parts:
                script_part = script[part_name]

                for i in range(images_per_part):
                    # For 60% templates: use template for first 60% of images
                    # Strategy: template for image 0, DALL-E for image 1 (if 2 images/part)
                    # Or: template, template, DALL-E for 3 images
                    use_template = prefer_templates and (i < int(images_per_part * 0.6) or i == 0)

                    task = self._generate_image_for_script_part(
                        session_id=input.session_id,
                        script_part=script_part,
                        part_name=part_name,
                        image_index=i,
                        prefer_template=use_template
                    )
                    all_tasks.append(task)
                    task_metadata.append({"part_name": part_name, "index": i})

            # Execute all tasks concurrently
            results = await asyncio.gather(*all_tasks, return_exceptions=True)

            # Organize results by script part
            micro_scenes = {
                "hook": {"images": []},
                "concept": {"images": []},
                "process": {"images": []},
                "conclusion": {"images": []}
            }

            total_cost = 0.0
            errors = []
            templates_used = 0
            dalle_used = 0

            for i, result in enumerate(results):
                part_name = task_metadata[i]["part_name"]

                if isinstance(result, Exception):
                    error_msg = f"{part_name} image {task_metadata[i]['index']} failed: {result}"
                    logger.error(f"[{input.session_id}] {error_msg}")
                    errors.append(error_msg)
                    continue

                # Add image to corresponding script part
                micro_scenes[part_name]["images"].append({
                    "image": result["url"],
                    "metadata": result["metadata"]
                })
                total_cost += result["cost"]

                # Track stats
                if result["metadata"]["source"] == "template":
                    templates_used += 1
                else:
                    dalle_used += 1

            duration = time.time() - start_time

            # Check if we have at least some images generated
            total_images = sum(len(part["images"]) for part in micro_scenes.values())
            success = total_images > 0

            if success:
                template_pct = (templates_used / total_images * 100) if total_images > 0 else 0
                logger.info(
                    f"[{input.session_id}] Generated {total_images} total images "
                    f"({templates_used} templates, {dalle_used} DALL-E) "
                    f"in {duration:.2f}s (${total_cost:.2f})"
                )
                logger.info(f"[{input.session_id}] Template usage: {template_pct:.1f}%")
            else:
                logger.error(
                    f"[{input.session_id}] All image generations failed"
                )

            return AgentOutput(
                success=success,
                data={
                    "micro_scenes": micro_scenes,
                    "cost": total_cost,
                    "stats": {
                        "templates_used": templates_used,
                        "dalle_used": dalle_used,
                        "total_images": total_images
                    },
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

    async def _generate_image_for_script_part(
        self,
        session_id: str,
        script_part: Dict[str, Any],
        part_name: str,
        image_index: int,
        prefer_template: bool = True
    ) -> dict:
        """
        Generate a single image for a script part.
        Tries template first (if prefer_template), then DALL-E 3 as fallback.

        Args:
            session_id: Session ID for logging
            script_part: Script part object with {text, duration, key_concepts, visual_guidance}
            part_name: Name of script part (hook, concept, process, conclusion)
            image_index: Image index for this part (0-2)
            prefer_template: Try template before DALL-E

        Returns:
            Dict with URL and metadata

        Raises:
            Exception: If both template and DALL-E generation fail
        """
        start = time.time()

        try:
            visual_guidance = script_part.get("visual_guidance", "")
            key_concepts = script_part.get("key_concepts", [])

            # Try template first if preferred
            if prefer_template:
                template_match = self.template_matcher.match_template(
                    visual_guidance,
                    key_concepts
                )

                if template_match:
                    logger.info(
                        f"[{session_id}] Using template '{template_match['name']}' "
                        f"for {part_name} image {image_index + 1}"
                    )

                    # Customize template with text overlays
                    customizations = {
                        "title": key_concepts[0] if key_concepts else "",
                        "labels": key_concepts[:3]
                    }

                    try:
                        customized_image_bytes = self.psd_customizer.customize_template(
                            template_match['preview_url'],
                            customizations
                        )

                        # Upload customized template to S3
                        # (For now, return a placeholder - storage integration needed)
                        url = template_match['preview_url']  # TODO: Upload customized version

                        duration = time.time() - start

                        return {
                            "url": url,
                            "cost": 0.0,  # Templates are free
                            "metadata": {
                                "part_name": part_name,
                                "image_index": image_index,
                                "duration": duration,
                                "source": "template",
                                "template_id": template_match['template_id'],
                                "template_name": template_match['name'],
                                "key_concepts": key_concepts,
                                "visual_guidance": visual_guidance[:200]
                            }
                        }
                    except Exception as e:
                        logger.warning(
                            f"[{session_id}] Template customization failed: {e}, "
                            f"falling back to DALL-E"
                        )
                        # Fall through to DALL-E

            # Generate with DALL-E 3
            logger.info(
                f"[{session_id}] Generating {part_name} image {image_index + 1} "
                f"with DALL-E 3"
            )

            result = await self.dalle_generator.generate_image(
                visual_guidance,
                style="educational"
            )

            if not result['success']:
                raise Exception(result.get('error', 'DALL-E generation failed'))

            duration = time.time() - start

            return {
                "url": result['url'],
                "cost": result['cost'],
                "metadata": {
                    "part_name": part_name,
                    "image_index": image_index,
                    "duration": duration,
                    "source": "dalle3",
                    "quality": result.get('quality', 'standard'),
                    "key_concepts": key_concepts,
                    "visual_guidance": visual_guidance[:200],
                    "prompt_used": result.get('prompt_used', '')[:200]
                }
            }

        except Exception as e:
            duration = time.time() - start
            logger.error(
                f"[{session_id}] {part_name} image {image_index + 1} generation failed "
                f"after {duration:.2f}s: {e}"
            )
            raise

    def close(self):
        """Cleanup resources."""
        if hasattr(self, 'template_matcher'):
            self.template_matcher.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
