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
from app.agents.helpers.template_matcher import TemplateMatcher
from app.agents.helpers.psd_customizer import PSDCustomizer
from app.agents.helpers.dalle_generator import DALLEGenerator
from app.services.storage import StorageService
from app.services.image_verifier import ImageVerificationService

logger = logging.getLogger(__name__)


class BatchImageGeneratorAgent:
    """
    Generates images for video scripts using templates (60%) and DALL-E 3 (40%).

    Strategy:
    - Tries to match templates first based on key concepts
    - Falls back to DALL-E 3 for images without template matches
    - Targets 60% template usage to minimize costs
    """

    def __init__(self, openai_api_key: str = None, websocket_manager=None, session_id: Optional[str] = None):
        """
        Initialize the Batch Image Generator Agent.

        Args:
            openai_api_key: OpenAI API key for DALL-E 3
            websocket_manager: Optional WebSocket manager for real-time updates
            session_id: Optional session ID for WebSocket updates
        """
        self.template_matcher = TemplateMatcher()
        self.psd_customizer = PSDCustomizer()
        self.dalle_generator = DALLEGenerator(api_key=openai_api_key)
        self.storage_service = StorageService()
        self.websocket_manager = websocket_manager
        self.session_id = session_id
        self.image_verifier = ImageVerificationService(websocket_manager=websocket_manager, session_id=session_id)

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
            images_per_part_config = input.data.get("images_per_part_config")
            images_per_part = input.data.get("images_per_part", 2)  # Fallback for old API
            prefer_templates = input.data.get("prefer_templates", True)
            use_semantic_progression = input.data.get("use_semantic_progression", False)

            # If per-part config provided, use it; otherwise use uniform count
            if images_per_part_config:
                logger.info(
                    f"[{input.session_id}] Generating images with duration-based scaling: {images_per_part_config}"
                )
            else:
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

                # Get images count for this part
                part_images_count = images_per_part_config.get(part_name, images_per_part) if images_per_part_config else images_per_part

                for i in range(part_images_count):
                    # For 60% templates: use template for first 60% of images
                    # Strategy: template for image 0, DALL-E for image 1 (if 2 images/part)
                    # Or: template, template, DALL-E for 3 images
                    use_template = prefer_templates and (i < int(part_images_count * 0.6) or i == 0)

                    task = self._generate_image_for_script_part(
                        session_id=input.session_id,
                        script_part=script_part,
                        part_name=part_name,
                        image_index=i,
                        prefer_template=use_template,
                        total_images=part_images_count,
                        use_semantic_progression=use_semantic_progression
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

    def _get_progression_keywords(self, image_index: int, total_images: int) -> str:
        """
        Get semantic progression keywords based on image position.

        Creates visual flow:
        - Image 0: Establishing shot, wide view, context
        - Image 1: Medium shot, detail focus
        - Image 2+: Close-up, specific detail

        Args:
            image_index: Current image index (0-based)
            total_images: Total images for this segment

        Returns:
            Comma-separated keywords for visual progression
        """
        if total_images == 1:
            return "balanced composition, clear view"

        # Calculate progression (0.0 = start, 1.0 = end)
        progression = image_index / (total_images - 1)

        if progression < 0.33:
            # Early images: Establish context
            return "establishing shot, wide angle, context view, cinematic framing"
        elif progression < 0.67:
            # Middle images: Focus on details
            return "medium shot, focused composition, key details visible"
        else:
            # Late images: Close-up, emphasis
            return "close-up detail, emphasis on subject, intimate view"

    def _split_narration_for_images(self, text: str, image_index: int, total_images: int) -> str:
        """
        Split narration text to create progressive images that match different
        parts of the narration timeline.

        For image 0: Use first half of narration (early concepts)
        For image 1: Use second half of narration (late concepts)
        For image 2+: Use full narration

        This ensures images appear in sync with what's being narrated.

        Args:
            text: Full narration text
            image_index: Which image this is (0, 1, 2, etc.)
            total_images: Total number of images for this part

        Returns:
            Portion of narration text for this image
        """
        if not text or total_images == 1:
            return text

        # Split by sentences
        sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
        num_sentences = len(sentences)

        if num_sentences <= 1:
            # Only one sentence, can't split meaningfully
            return text

        if image_index == 0 and total_images >= 2:
            # First image: Use first half of sentences (early concepts)
            split_point = max(1, num_sentences // 2)
            result = ' '.join(sentences[:split_point])
            logger.debug(f"Image {image_index}: Early concepts (first {split_point}/{num_sentences} sentences)")
            return result
        elif image_index == 1 and total_images >= 2:
            # Second image: Use second half of sentences (late concepts)
            split_point = num_sentences // 2
            result = ' '.join(sentences[split_point:])
            logger.debug(f"Image {image_index}: Late concepts (last {num_sentences - split_point}/{num_sentences} sentences)")
            return result
        else:
            # Third+ image or fallback: Use full text
            return text

    async def _generate_image_for_script_part(
        self,
        session_id: str,
        script_part: Dict[str, Any],
        part_name: str,
        image_index: int,
        prefer_template: bool = True,
        total_images: int = 2,
        use_semantic_progression: bool = False
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
            total_images: Total number of images for this part

        Returns:
            Dict with URL and metadata

        Raises:
            Exception: If both template and DALL-E generation fail
        """
        start = time.time()

        try:
            visual_guidance = script_part.get("visual_guidance", "")
            key_concepts = script_part.get("key_concepts", [])
            narration_text = script_part.get("text", "")

            # Split narration to create progressive images that match narration timeline
            # Image 0: Early concepts, Image 1: Late concepts
            focused_text = self._split_narration_for_images(narration_text, image_index, total_images)

            # Use the focused text as the visual guidance for this image
            # This ensures each image shows what's being said when it appears on screen
            if focused_text != narration_text:
                logger.info(
                    f"[{session_id}] {part_name} image {image_index + 1}: "
                    f"{'Early' if image_index == 0 else 'Late'} concepts - '{focused_text[:60]}...'"
                )
                focused_guidance = focused_text
            else:
                # Fallback to original visual guidance if we couldn't split
                focused_guidance = visual_guidance

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

                        # Verify image quality
                        logger.info(f"[{session_id}] Verifying {part_name} image {image_index + 1} (template)...")
                        verification_result = await self.image_verifier.verify_image(
                            image_url=url,
                            image_index=image_index
                        )

                        if verification_result.failed:
                            logger.warning(
                                f"[{session_id}] Image {image_index + 1} verification failed: "
                                f"{len(verification_result.failed_checks)} failures"
                            )
                            for check in verification_result.failed_checks:
                                logger.warning(f"  - {check.check_name}: {check.message}")

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
                            },
                            "verification": verification_result.to_dict()
                        }
                    except Exception as e:
                        logger.warning(
                            f"[{session_id}] Template customization failed: {e}, "
                            f"falling back to DALL-E"
                        )
                        # Fall through to DALL-E

            # Generate with DALL-E 3
            # Add semantic progression keywords if enabled
            if use_semantic_progression and total_images > 1:
                progression_keywords = self._get_progression_keywords(image_index, total_images)
                enhanced_guidance = f"{focused_guidance}, {progression_keywords}"
                logger.info(
                    f"[{session_id}] Generating {part_name} image {image_index + 1}/{total_images} "
                    f"with DALL-E 3 ({progression_keywords})"
                )
            else:
                enhanced_guidance = focused_guidance
                logger.info(
                    f"[{session_id}] Generating {part_name} image {image_index + 1} "
                    f"with DALL-E 3"
                )

            result = await self.dalle_generator.generate_image(
                enhanced_guidance,  # Use enhanced guidance with progression
                style="educational"
            )

            if not result['success']:
                raise Exception(result.get('error', 'DALL-E generation failed'))

            # Verify image quality
            logger.info(f"[{session_id}] Verifying {part_name} image {image_index + 1} (DALL-E)...")
            verification_result = await self.image_verifier.verify_image(
                image_url=result['url'],
                image_index=image_index
            )

            if verification_result.failed:
                logger.warning(
                    f"[{session_id}] Image {image_index + 1} verification failed: "
                    f"{len(verification_result.failed_checks)} failures"
                )
                for check in verification_result.failed_checks:
                    logger.warning(f"  - {check.check_name}: {check.message}")

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
                },
                "verification": verification_result.to_dict()
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
