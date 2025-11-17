"""
Story Image Generator Agent

Generates sequential storytelling images for video production based on segments.md.
Processes segments in parallel, generates images via Replicate, and verifies them
using OpenRouter vision models.
"""
import asyncio
import base64
import json
import logging
import random
import re
import time
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
import requests

from app.agents.base import Agent, AgentInput, AgentOutput
from app.services.storage import StorageService
from app.services.secrets import get_secret

logger = logging.getLogger(__name__)

# API endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"

# Model IDs
BASE_IMAGE_MODEL_QUALITY = "black-forest-labs/flux-dev"
BASE_IMAGE_MODEL_FAST = "black-forest-labs/flux-schnell"
FALLBACK_IMAGE_MODEL = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
VERIFICATION_MODEL = "openai/gpt-4o-mini"

# Image dimensions (16:9 aspect ratio)
IMAGE_WIDTH = 1792
IMAGE_HEIGHT = 1024

# Cost rates (approximate, per operation)
COST_RATES = {
    "flux-dev": 0.0035,
    "flux-schnell": 0.003,
    "sdxl": 0.0029,
    "gpt-4o-mini-verification": 0.00015,
}


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be filesystem-safe."""
    invalid_chars = r'[<>:"/\\|?*\x00]'
    sanitized = re.sub(invalid_chars, '_', name)
    sanitized = sanitized.strip(' .')
    sanitized = re.sub(r'_+', '_', sanitized)
    if not sanitized:
        sanitized = "unnamed"
    return sanitized


def parse_segments_md(content: str) -> Tuple[Optional[str], List[Dict]]:
    """
    Parse segments.md content to extract template title and segments.
    
    Returns:
        Tuple of (template_title, list_of_segments)
    """
    # Extract template title
    template_title = None
    lines = content.split("\n")
    for line in lines:
        if line.startswith("Template:"):
            template_title = line.split("Template:")[1].strip()
            break
    
    if not template_title:
        logger.error("Template title not found in segments.md")
        return None, []
    
    template_title = sanitize_filename(template_title)
    
    # Parse segments
    segments = []
    current_segment = None
    in_narration = False
    narration_lines = []
    
    for i, line in enumerate(lines):
        if line.startswith("**Segment") and ":" in line:
            if current_segment:
                if narration_lines:
                    current_segment["narrationtext"] = "\n".join(narration_lines).strip().strip('"').strip()
                segments.append(current_segment)
            
            segment_match = line.replace("**", "").strip()
            if ":" in segment_match:
                parts = segment_match.split(":", 1)
                segment_num_title = parts[0].replace("Segment", "").strip()
                segment_num = segment_num_title.split()[0]
                segment_title = parts[1].split("(")[0].strip()
                
                duration = 0
                if "(" in line and ")" in line:
                    duration_part = line[line.find("(")+1:line.find(")")]
                    numbers = re.findall(r'(\d+)', duration_part)
                    if len(numbers) >= 2:
                        start_time = int(numbers[0])
                        end_time = int(numbers[1])
                        duration = end_time - start_time
                    elif len(numbers) == 1:
                        duration = int(numbers[0])
                
                segment_title = sanitize_filename(segment_title)
                
                current_segment = {
                    "number": int(segment_num),
                    "title": segment_title,
                    "duration": duration,
                    "narrationtext": "",
                    "visual_guidance_preview": ""
                }
                narration_lines = []
                in_narration = False
        elif current_segment:
            if "Narration text" in line or "narration text" in line.lower():
                in_narration = True
                continue
            elif line.strip().startswith("```"):
                if in_narration and not narration_lines:
                    continue
                elif in_narration and narration_lines:
                    current_segment["narrationtext"] = "\n".join(narration_lines).strip().strip('"').strip()
                    narration_lines = []
                    in_narration = False
                    continue
            elif in_narration:
                narration_lines.append(line)
            elif "Visual guidance" in line or "visual guidance" in line.lower():
                if ":" in line:
                    guidance = line.split(":", 1)[1].strip().strip('"').strip()
                    if current_segment["visual_guidance_preview"]:
                        current_segment["visual_guidance_preview"] += " " + guidance
                    else:
                        current_segment["visual_guidance_preview"] = guidance
    
    if current_segment:
        if narration_lines:
            current_segment["narrationtext"] = "\n".join(narration_lines).strip().strip('"').strip()
        segments.append(current_segment)
    
    if not segments:
        logger.error("No segments found in segments.md")
        return None, []
    
    # Check for duplicate segment numbers
    segment_numbers = [s["number"] for s in segments]
    duplicates = [num for num in segment_numbers if segment_numbers.count(num) > 1]
    if duplicates:
        logger.error(f"Duplicate segment numbers found: {sorted(set(duplicates))}")
        return None, []
    
    # Validate all segments have required data
    for segment in segments:
        if not segment.get("narrationtext", "").strip():
            logger.error(f"Segment {segment['number']} ({segment['title']}) is missing narration text")
            return None, []
        if not segment.get("visual_guidance_preview", "").strip():
            logger.error(f"Segment {segment['number']} ({segment['title']}) is missing visual guidance preview")
            return None, []
    
    segments.sort(key=lambda x: x["number"])
    
    return template_title, segments


def generate_story_prompts(segment_data: Dict, num_images: int, has_diagram: bool = False) -> List[str]:
    """Generate sequential storytelling prompts from segment data."""
    narration = segment_data.get("narrationtext", "")
    visual_guidance = segment_data.get("visual_guidance_preview", "")
    
    # Remove text-related terms from visual guidance
    text_terms = ["text overlay", "text", "labels", "caption", "annotation", "writing", "lettering"]
    for term in text_terms:
        visual_guidance = visual_guidance.replace(term, "").replace(term.title(), "").replace(term.upper(), "")
    visual_guidance = " ".join(visual_guidance.split())
    
    style_base = "Educational storytelling style, cinematic 16:9 composition"
    if has_diagram:
        style_base += ", matching the style and color palette of the reference diagram"
    
    no_labels = "NO TEXT, NO LABELS, NO WORDS, NO LETTERING, NO TYPography, NO WRITING, NO ANNOTATIONS, NO CAPTIONS, NO WATERMARKS, NO SIGNATURES. Pure visual storytelling only. Absolutely no text elements whatsoever."
    
    prompts = []
    
    if num_images == 1:
        prompt = f"{style_base}. {visual_guidance}. {narration}. Visual storytelling moment that answers the question."
        prompts.append(f"{prompt} {no_labels}")
    elif num_images == 2:
        prompts.append(
            f"{style_base}, establishing shot. {visual_guidance}. "
            f"Opening moment: The question is posed visually. {no_labels}"
        )
        prompts.append(
            f"{style_base}, main scene. {narration}. "
            f"Answering moment: Visual answer to the question, clear narrative progression. {no_labels}"
        )
    elif num_images >= 3:
        prompts.append(
            f"{style_base}, establishing shot. {visual_guidance}. "
            f"Frame 1: Opening moment - The question is posed visually, curious and engaging. {no_labels}"
        )
        prompts.append(
            f"{style_base}, middle scene. {narration}. "
            f"Frame 2: Discovery moment - Visual progression toward the answer, engaging narrative. {no_labels}"
        )
        prompts.append(
            f"{style_base}, conclusion scene. {narration}. "
            f"Frame 3: Answer moment - Visual conclusion that answers the question, satisfying narrative resolution. {no_labels}"
        )
        for i in range(3, num_images):
            frame_num = i + 1
            prompts.append(
                f"{style_base}, scene {frame_num}. {narration}. "
                f"Frame {frame_num}: Continued visual progression, maintaining narrative flow and style consistency. {no_labels}"
            )
    
    return prompts


class StoryImageGeneratorAgent:
    """
    Agent for generating sequential storytelling images from segments.md.
    
    Processes segments in parallel, generates images via Replicate, and verifies
    them using OpenRouter vision models.
    """
    
    def __init__(
        self,
        storage_service: StorageService,
        openrouter_api_key: str,
        replicate_api_key: str,
        websocket_manager=None
    ):
        """
        Initialize the agent.

        Args:
            storage_service: StorageService instance for S3 operations
            openrouter_api_key: OpenRouter API key for verification
            replicate_api_key: Replicate API key for image generation
            websocket_manager: Optional WebSocketManager for progress updates
        """
        self.storage_service = storage_service
        self.openrouter_api_key = openrouter_api_key
        self.replicate_api_key = replicate_api_key
        self.websocket_manager = websocket_manager
    
    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Process story segments and generate images.
        
        Input data should contain:
        - segments: List of parsed segments from segments.md
        - diagram_s3_path: Optional S3 path to diagram.png
        - output_s3_prefix: S3 prefix for output (e.g., "users/user123/session456/images/")
        - num_images: Number of images per segment
        - max_passes: Maximum regeneration attempts per image
        - max_verification_passes: Maximum verification attempts per image
        - fast_mode: Use fast/cheap model if True
        
        Returns:
            AgentOutput with results, cost, and duration
        """
        start_time = time.time()
        total_cost = 0.0
        
        try:
            data = input.data
            segments = data.get("segments", [])
            diagram_s3_path = data.get("diagram_s3_path")
            output_s3_prefix = data.get("output_s3_prefix", "")
            num_images = data.get("num_images", 2)
            max_passes = data.get("max_passes", 5)
            max_verification_passes = data.get("max_verification_passes", 3)
            fast_mode = data.get("fast_mode", False)
            template_title = data.get("template_title", "Untitled")
            cumulative_items = data.get("cumulative_items", [])

            if not segments:
                return AgentOutput(
                    success=False,
                    data={},
                    cost=0.0,
                    duration=time.time() - start_time,
                    error="No segments provided"
                )

            # Download diagram if provided
            diagram_bytes = None
            if diagram_s3_path:
                try:
                    diagram_bytes = self.storage_service.read_file(diagram_s3_path)
                    logger.info(f"Downloaded diagram from S3: {diagram_s3_path}")
                except Exception as e:
                    logger.warning(f"Failed to download diagram: {e}, continuing without style reference")

            # Create a lock for thread-safe cumulative_items updates
            items_lock = asyncio.Lock()

            # Process segments in parallel
            total_segments = len(segments)
            segment_tasks = [
                self._process_segment(
                    segment,
                    template_title,
                    diagram_bytes,
                    output_s3_prefix,
                    num_images,
                    max_passes,
                    max_verification_passes,
                    fast_mode,
                    input.session_id,
                    total_segments,
                    cumulative_items,
                    items_lock
                )
                for segment in segments
            ]
            
            segment_results = await asyncio.gather(*segment_tasks, return_exceptions=True)
            
            # Process results
            successful_segments = []
            failed_segments = []
            total_images_generated = 0
            
            for i, result in enumerate(segment_results):
                segment = segments[i]
                if isinstance(result, Exception):
                    logger.error(f"Segment {segment['number']} failed with exception: {result}")
                    failed_segments.append({
                        "segment_number": segment["number"],
                        "segment_title": segment["title"],
                        "error": str(result)
                    })
                elif isinstance(result, dict):
                    if result.get("success"):
                        successful_segments.append(result)
                        total_images_generated += result.get("images_generated", 0)
                        total_cost += result.get("cost", 0.0)
                    else:
                        failed_segments.append({
                            "segment_number": segment["number"],
                            "segment_title": segment["title"],
                            "error": result.get("error", "Unknown error")
                        })
            
            # Sort successful segments by number
            successful_segments.sort(key=lambda x: x.get("segment_number", 0))
            
            duration = time.time() - start_time
            
            return AgentOutput(
                success=len(successful_segments) > 0,
                data={
                    "template_title": template_title,
                    "segments_total": len(segments),
                    "segments_succeeded": len(successful_segments),
                    "segments_failed": len(failed_segments),
                    "total_images_generated": total_images_generated,
                    "successful_segments": successful_segments,
                    "failed_segments": failed_segments
                },
                cost=total_cost,
                duration=duration,
                error=None if len(failed_segments) == 0 else f"{len(failed_segments)} segments failed"
            )
        
        except Exception as e:
            logger.exception(f"Error in StoryImageGeneratorAgent.process: {e}")
            return AgentOutput(
                success=False,
                data={},
                cost=total_cost,
                duration=time.time() - start_time,
                error=str(e)
            )
    
    async def _update_cumulative_status(
        self,
        session_id: str,
        cumulative_items: list,
        items_lock: asyncio.Lock,
        item_id: str,
        new_status: str
    ):
        """Update a single item's status and broadcast the full cumulative state."""
        if not cumulative_items or not items_lock or not self.websocket_manager:
            return

        async with items_lock:
            # Find and update the item
            for item in cumulative_items:
                if item["id"] == item_id:
                    item["status"] = new_status
                    break

            # Count completed items for progress calculation
            completed_count = sum(1 for item in cumulative_items if item["status"] == "completed")
            total_count = len(cumulative_items)
            progress = int((completed_count / total_count) * 100) if total_count > 0 else 0

            # Generate details message
            processing_items = [item for item in cumulative_items if item["status"] == "processing"]
            if processing_items:
                details = f"Processing: {processing_items[0]['name']}"
            else:
                details = f"Completed {completed_count} of {total_count} items"

            # Broadcast the full cumulative state
            await self.websocket_manager.broadcast_status(
                session_id,
                status="generating_images_audio",
                progress=progress,
                details=details,
                items=cumulative_items
            )

    async def _process_segment(
        self,
        segment: Dict,
        template_title: str,
        diagram_bytes: Optional[bytes],
        output_s3_prefix: str,
        num_images: int,
        max_passes: int,
        max_verification_passes: int,
        fast_mode: bool,
        session_id: str,
        total_segments: int,
        cumulative_items: list = None,
        items_lock: asyncio.Lock = None
    ) -> Dict:
        """Process a single segment and generate images."""
        segment_start_time = time.time()
        segment_num = segment["number"]
        segment_title = segment["title"]

        # Send initial WebSocket update (still keep this for backward compatibility)
        if self.websocket_manager and not cumulative_items:
            await self.websocket_manager.broadcast_status(
                session_id,
                status="generating_images",
                progress=10 + (segment_num - 1) * 10,
                details=f"Generating images for segment {segment_num} of {total_segments}: {segment_title}"
            )
        
        try:
            # Generate prompts
            prompts = generate_story_prompts(segment, num_images, has_diagram=(diagram_bytes is not None))
            
            # Generate images
            generated_images = []
            segment_cost = 0.0
            
            for img_idx, prompt in enumerate(prompts):
                image_num = img_idx + 1
                success = False
                gen_attempt = 0

                # Update cumulative status: mark image as processing
                item_id = f"image_seg{segment_num}_img{image_num}"
                if cumulative_items and items_lock:
                    await self._update_cumulative_status(
                        session_id,
                        cumulative_items,
                        items_lock,
                        item_id,
                        "processing"
                    )

                while not success and gen_attempt < max_passes:
                    gen_attempt += 1

                    # Generate image
                    gen_success, gen_metadata = await self._generate_image_via_replicate(
                        prompt,
                        gen_attempt,
                        fast_mode,
                        diagram_bytes
                    )

                    if not gen_success:
                        segment_cost += gen_metadata.get("cost", 0.0)
                        if gen_attempt < max_passes:
                            await asyncio.sleep(2)  # Brief delay before retry
                            continue
                        break

                    image_bytes = gen_metadata.get("image_bytes")
                    if not image_bytes:
                        break

                    segment_cost += gen_metadata.get("cost", 0.0)

                    # Verify image
                    verify_success, verify_result, verify_error, verify_metadata = await self._verify_image_no_labels(
                        image_bytes,
                        max_verification_passes
                    )

                    segment_cost += verify_metadata.get("cost", 0.0)

                    if verify_success:
                        # Upload to S3
                        s3_key = f"{output_s3_prefix}{template_title}/{segment_num}. {segment_title}/generated_images/image_{image_num}.png"
                        self.storage_service.upload_file_direct(
                            image_bytes,
                            s3_key,
                            content_type="image/png"
                        )

                        # Remove image_bytes from metadata before serialization (it's already uploaded to S3)
                        gen_metadata_serializable = {k: v for k, v in gen_metadata.items() if k != "image_bytes"}
                        verify_metadata_serializable = {k: v for k, v in verify_metadata.items() if k != "image_bytes"}

                        generated_images.append({
                            "image_number": image_num,
                            "s3_key": s3_key,
                            "generation_metadata": gen_metadata_serializable,
                            "verification_metadata": verify_metadata_serializable
                        })

                        # Update cumulative status: mark image as completed
                        if cumulative_items and items_lock:
                            await self._update_cumulative_status(
                                session_id,
                                cumulative_items,
                                items_lock,
                                item_id,
                                "completed"
                            )

                        success = True

                        # Send WebSocket update for each image generated
                        if self.websocket_manager:
                            await self.websocket_manager.broadcast_status(
                                session_id,
                                status="image_generated",
                                progress=10 + (segment_num - 1) * 10 + (image_num * 2),
                                details=f"Generated image {image_num} of {num_images} for segment {segment_num}: {segment_title}"
                            )

                        break
                    else:
                        if gen_attempt < max_passes:
                            logger.warning(f"Segment {segment_num}, Image {image_num}: Verification failed, regenerating...")
                            await asyncio.sleep(1)
                
                if not success:
                    logger.error(f"Segment {segment_num}, Image {image_num}: Failed after {max_passes} attempts")
            
            segment_duration = time.time() - segment_start_time
            
            return {
                "success": len(generated_images) == num_images,
                "segment_number": segment_num,
                "segment_title": segment_title,
                "images_generated": len(generated_images),
                "images_expected": num_images,
                "cost": segment_cost,
                "time_seconds": segment_duration,
                "generated_images": generated_images,
                "error": None if len(generated_images) == num_images else f"Only {len(generated_images)}/{num_images} images generated"
            }
        
        except Exception as e:
            logger.exception(f"Error processing segment {segment_num}: {e}")
            return {
                "success": False,
                "segment_number": segment_num,
                "segment_title": segment_title,
                "images_generated": 0,
                "images_expected": num_images,
                "cost": 0.0,
                "time_seconds": time.time() - segment_start_time,
                "generated_images": [],
                "error": str(e)
            }
    
    async def _generate_image_via_replicate(
        self,
        prompt: str,
        generation_attempt: int = 0,
        fast_mode: bool = False,
        diagram_bytes: Optional[bytes] = None
    ) -> Tuple[bool, Dict]:
        """Generate image using Replicate API."""
        headers = {
            "Authorization": f"Token {self.replicate_api_key}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        
        # Determine model
        if fast_mode:
            current_model = BASE_IMAGE_MODEL_FAST
        else:
            current_model = BASE_IMAGE_MODEL_QUALITY
        
        use_fallback = (generation_attempt >= 2 and "flux" in current_model.lower())
        if use_fallback:
            current_model = FALLBACK_IMAGE_MODEL
        
        # Determine cost
        model_name_lower = current_model.lower()
        if "flux-dev" in model_name_lower or ("flux" in model_name_lower and "schnell" not in model_name_lower):
            cost = COST_RATES["flux-dev"]
        elif "flux-schnell" in model_name_lower or "schnell" in model_name_lower:
            cost = COST_RATES["flux-schnell"]
        elif "sdxl" in model_name_lower:
            cost = COST_RATES["sdxl"]
        else:
            cost = COST_RATES["flux-dev"]
        
        # Add style reference if diagram available
        if diagram_bytes:
            style_ref = "Style reference: match the artistic style, color palette, and visual elements of the reference diagram. "
            prompt = style_ref + prompt
        
        # Negative prompt
        negative_prompt = (
            "text, letters, words, typography, labels, captions, annotations, writing, "
            "lettering, spelling, words on image, text overlay, watermark, signature, "
            "inscription, script, font, typeface, characters, symbols as text, "
            "alphanumeric, numbers as text, any readable text, any written text, "
            "any printed text, any handwritten text, any visible text, text elements, "
            "signs, banners, posters with text, labels on objects, text in image"
        )
        
        # Prepare input parameters
        if "flux" in current_model.lower() and "schnell" in current_model.lower():
            input_params = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "output_format": "png",
                "output_quality": 90,
                "num_outputs": 1,
                "num_inference_steps": 4
            }
            if diagram_bytes:
                try:
                    diagram_b64 = base64.b64encode(diagram_bytes).decode("utf-8")
                    input_params["image"] = f"data:image/png;base64,{diagram_b64}"
                except Exception:
                    pass
        elif "flux" in current_model.lower():
            input_params = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "output_format": "png",
                "output_quality": 90,
                "num_outputs": 1,
                "num_inference_steps": 28
            }
            if diagram_bytes:
                try:
                    diagram_b64 = base64.b64encode(diagram_bytes).decode("utf-8")
                    input_params["image"] = f"data:image/png;base64,{diagram_b64}"
                except Exception:
                    pass
        elif "sdxl" in current_model.lower():
            input_params = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "num_outputs": 1,
                "scheduler": "K_EULER",
                "num_inference_steps": 20,
                "guidance_scale": 7.5,
                "output_format": "png"
            }
        else:
            input_params = {
                "prompt": prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "output_format": "png"
            }
        
        payload = {
            "version": current_model,
            "input": input_params
        }
        
        try:
            # Create prediction
            response = requests.post(
                REPLICATE_API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code not in [200, 201]:
                error_msg = f"API returned status code: {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", "") or error_data.get("detail", "")
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                logger.error(error_msg)
                return (False, {
                    "model_used": current_model,
                    "cost": 0.0,
                    "time_seconds": time.time() - start_time,
                    "error": True
                })
            
            prediction_data = response.json()
            prediction_id = prediction_data.get("id")
            prediction_url = prediction_data.get("urls", {}).get("get")
            
            if not prediction_id:
                logger.error("No prediction ID in response")
                return (False, {
                    "model_used": current_model,
                    "cost": 0.0,
                    "time_seconds": time.time() - start_time,
                    "error": True
                })
            
            # Poll for result
            max_polls = 60
            poll_interval = 5
            
            for poll in range(max_polls):
                await asyncio.sleep(poll_interval)
                
                try:
                    get_response = requests.get(
                        prediction_url or f"{REPLICATE_API_URL}/{prediction_id}",
                        headers=headers,
                        timeout=30
                    )
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Request error while polling (attempt {poll + 1}/{max_polls}): {e}")
                    if poll < max_polls - 1:
                        continue
                    logger.error("Failed to get prediction status after retries")
                    return (False, {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": time.time() - start_time,
                        "error": True,
                        "error_message": f"Network error: {str(e)}"
                    })
                
                if get_response.status_code != 200:
                    logger.warning(f"Non-200 status code {get_response.status_code} while polling (attempt {poll + 1}/{max_polls})")
                    if poll < max_polls - 1:
                        continue
                    logger.error("Failed to get prediction status")
                    return (False, {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": time.time() - start_time,
                        "error": True,
                        "error_message": f"HTTP {get_response.status_code}: {get_response.text[:200]}"
                    })
                
                try:
                    prediction = get_response.json()
                except ValueError as e:
                    logger.warning(f"Invalid JSON response while polling (attempt {poll + 1}/{max_polls}): {e}")
                    if poll < max_polls - 1:
                        continue
                    logger.error("Failed to parse prediction response")
                    return (False, {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": time.time() - start_time,
                        "error": True,
                        "error_message": "Invalid JSON response from Replicate API"
                    })
                
                status = prediction.get("status")
                
                if status == "succeeded":
                    output = prediction.get("output")
                    if not output:
                        logger.error("No output in prediction result")
                        return (False, {
                            "model_used": current_model,
                            "cost": 0.0,
                            "time_seconds": time.time() - start_time,
                            "error": True
                        })
                    
                    image_url = output[0] if isinstance(output, list) else output
                    
                    # Download image
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    image_bytes = img_response.content
                    
                    elapsed_time = time.time() - start_time
                    
                    return (True, {
                        "model_used": current_model,
                        "cost": cost,
                        "time_seconds": elapsed_time,
                        "image_bytes": image_bytes,
                        "file_size_bytes": len(image_bytes)
                    })
                
                elif status == "failed":
                    error_msg = prediction.get("error", "Unknown error")
                    logger.error(f"Prediction failed: {error_msg}")
                    return (False, {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": time.time() - start_time,
                        "error": True
                    })
                
                elif status in ["starting", "processing"]:
                    logger.debug(f"Prediction status: {status} (poll {poll + 1}/{max_polls})")
                    continue
                elif status == "canceled":
                    logger.error("Prediction was canceled")
                    return (False, {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": time.time() - start_time,
                        "error": True,
                        "error_message": "Prediction was canceled"
                    })
                else:
                    logger.error(f"Unknown prediction status: {status} (full response: {prediction})")
                    # Don't continue polling on unknown status - return error immediately
                    return (False, {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": time.time() - start_time,
                        "error": True,
                        "error_message": f"Unknown status: {status}"
                    })
            
            # Timeout
            logger.error(f"Prediction timed out after {max_polls * poll_interval}s")
            return (False, {
                "model_used": current_model,
                "cost": 0.0,
                "time_seconds": time.time() - start_time,
                "error": True
            })
        
        except Exception as e:
            logger.exception(f"Error generating image: {e}")
            return (False, {
                "model_used": current_model,
                "cost": 0.0,
                "time_seconds": time.time() - start_time,
                "error": True
            })
    
    async def _verify_image_no_labels(
        self,
        image_bytes: bytes,
        max_passes: int = 5
    ) -> Tuple[bool, Dict, str, Dict]:
        """Verify image has no text, labels, or words using OpenRouter vision model."""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        start_time = time.time()
        attempts_made = 0
        total_cost = 0.0
        
        verification_prompt = """Analyze this image and respond with JSON only.

Check:
1. Does the image contain ANY text, labels, words, lettering, or readable characters? (has_text: true/false)
2. Are there any watermarks, signatures, or annotations? (has_annotations: true/false)
3. How confident are you? (confidence: 0.0-1.0)

Respond ONLY with valid JSON in this exact format:
{
  "has_text": false,
  "has_annotations": false,
  "confidence": 0.95
}"""
        
        for attempt in range(max_passes):
            attempts_made += 1
            try:
                response = requests.post(
                    OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "HTTP-Referer": "https://github.com/your-repo",
                        "X-Title": "Story Image Generator",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": VERIFICATION_MODEL,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": verification_prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/png;base64,{image_b64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    try:
                        result = json.loads(content)
                        has_text = result.get("has_text", True)
                        has_annotations = result.get("has_annotations", True)
                        confidence = result.get("confidence", 0.0)
                        
                        verification_cost = COST_RATES["gpt-4o-mini-verification"]
                        total_cost += verification_cost
                        
                        success = not has_text and not has_annotations
                        
                        if success:
                            elapsed_time = time.time() - start_time
                            return (True, result, "", {
                                "cost": total_cost,
                                "time_seconds": elapsed_time,
                                "attempts_made": attempts_made,
                                "confidence": confidence
                            })
                        else:
                            error_msg = (
                                f"Text/annotations detected: has_text={has_text}, "
                                f"has_annotations={has_annotations}, confidence={confidence:.2f}"
                            )
                            if attempt < max_passes - 1:
                                await asyncio.sleep(2)
                                continue
                            
                            elapsed_time = time.time() - start_time
                            return (False, result, error_msg, {
                                "cost": total_cost,
                                "time_seconds": elapsed_time,
                                "attempts_made": attempts_made,
                                "confidence": confidence
                            })
                    
                    except json.JSONDecodeError:
                        verification_cost = COST_RATES["gpt-4o-mini-verification"]
                        total_cost += verification_cost
                        if attempt < max_passes - 1:
                            await asyncio.sleep(2)
                            continue
                        elapsed_time = time.time() - start_time
                        return (False, {}, "Invalid JSON response from verification model", {
                            "cost": total_cost,
                            "time_seconds": elapsed_time,
                            "attempts_made": attempts_made
                        })
                else:
                    if response.status_code == 429:
                        verification_cost = COST_RATES["gpt-4o-mini-verification"]
                        total_cost += verification_cost
                        base_wait = 5
                        wait_time = min(base_wait * (2 ** attempt), 60)
                        jitter = random.uniform(0, 5)
                        wait_time = wait_time + jitter
                        if attempt < max_passes - 1:
                            await asyncio.sleep(wait_time)
                            continue
                        elapsed_time = time.time() - start_time
                        return (False, {}, f"Rate limited after {max_passes} attempts", {
                            "cost": total_cost,
                            "time_seconds": elapsed_time,
                            "attempts_made": attempts_made
                        })
                    
                    verification_cost = COST_RATES["gpt-4o-mini-verification"]
                    total_cost += verification_cost
                    error_text = response.text
                    if attempt < max_passes - 1:
                        await asyncio.sleep(2)
                        continue
                    elapsed_time = time.time() - start_time
                    return (False, {}, f"API error {response.status_code}: {error_text[:200]}", {
                        "cost": total_cost,
                        "time_seconds": elapsed_time,
                        "attempts_made": attempts_made
                    })
            
            except Exception as e:
                verification_cost = COST_RATES["gpt-4o-mini-verification"]
                total_cost += verification_cost
                if attempt < max_passes - 1:
                    await asyncio.sleep(2)
                    continue
                elapsed_time = time.time() - start_time
                return (False, {}, f"Error: {e}", {
                    "cost": total_cost,
                    "time_seconds": elapsed_time,
                    "attempts_made": attempts_made
                })
        
        elapsed_time = time.time() - start_time
        return (False, {}, "All verification attempts failed", {
            "cost": total_cost,
            "time_seconds": elapsed_time,
            "attempts_made": attempts_made
        })

