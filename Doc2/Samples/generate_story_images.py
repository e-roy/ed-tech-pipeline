"""
Generate sequential storytelling images for video production.

This script:
1. Reads segment hook JSON files to extract narration and visual guidance
2. Generates sequential images for storytelling/video
3. Verifies images have no text/labels using Gemini vision
4. Regenerates images until all are clean (no text/labels)

Usage:
    python generate_story_images.py --num-images 3 --max-passes 5
    python generate_story_images.py --topic Photosynthesis --num-images 2 --max-passes 3
"""

import os
import json
import argparse
import time
import random
import base64
import requests
import re
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        # Fallback for older Python versions
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load .env from same directory as script
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[INFO] Loaded environment variables from {env_path}")
except ImportError:
    pass

# API endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"

# Model IDs
BASE_IMAGE_MODEL_QUALITY = "black-forest-labs/flux-dev"  # Flux-dev for better quality
BASE_IMAGE_MODEL_FAST = "black-forest-labs/flux-schnell"  # Flux-schnell for fast/cheap
FALLBACK_IMAGE_MODEL = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
VERIFICATION_MODEL = "openai/gpt-4o-mini"  # Vision model for verification (cheapest paid option with good rate limits)

# Image dimensions (16:9 aspect ratio)
IMAGE_WIDTH = 1792
IMAGE_HEIGHT = 1024

# Cost rates (approximate, per operation)
COST_RATES = {
    "flux-dev": 0.0035,  # ~$0.003-0.004 per image
    "flux-schnell": 0.003,  # ~$0.003 per image
    "sdxl": 0.0029,  # ~$0.0029 per image
    "gemini-verification": 0.00025,  # ~$0.0002-0.0003 per verification (legacy name, now using gpt-4o-mini)
    "gpt-4o-mini-verification": 0.00015,  # ~$0.00015 per verification (cheapest paid vision model)
}


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be filesystem-safe.
    Replaces invalid characters with underscores.
    """
    # Remove or replace invalid filesystem characters
    # Windows: < > : " / \ | ? *
    # Unix: / and null
    invalid_chars = r'[<>:"/\\|?*\x00]'
    sanitized = re.sub(invalid_chars, '_', name)
    # Remove leading/trailing spaces and dots (Windows doesn't allow these)
    sanitized = sanitized.strip(' .')
    # Replace multiple consecutive underscores with single underscore
    sanitized = re.sub(r'_+', '_', sanitized)
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed"
    return sanitized


def get_openrouter_key() -> str:
    """Get OpenRouter API key from environment."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY not found in environment variables")
    return key


def get_replicate_key() -> str:
    """Get Replicate API key from environment."""
    key = os.getenv("REPLICATE_KEY")
    if not key:
        raise ValueError("REPLICATE_KEY not found in environment variables")
    return key


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def parse_segments_md(segments_file: Path) -> Tuple[Optional[str], List[Dict]]:
    """
    Parse segments.md file to extract template title and segments.
    
    Args:
        segments_file: Path to segments.md file
    
    Returns:
        Tuple of (template_title, list_of_segments)
        Each segment dict contains: number, title, duration, narrationtext, visual_guidance_preview
    """
    if not segments_file.exists():
        print(f"[ERROR] segments.md not found: {segments_file}")
        return None, []
    
    with open(segments_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Extract template title
    template_title = None
    lines = content.split("\n")
    for line in lines:
        if line.startswith("Template:"):
            template_title = line.split("Template:")[1].strip()
            break
    
    if not template_title:
        print(f"[ERROR] Template title not found in segments.md")
        return None, []
    
    # Sanitize template title
    template_title = sanitize_filename(template_title)
    
    # Parse segments
    segments = []
    current_segment = None
    in_narration = False
    narration_lines = []
    
    for i, line in enumerate(lines):
        # Match segment header: **Segment X: Title (time-time seconds)**
        if line.startswith("**Segment") and ":" in line:
            # Save previous segment if exists
            if current_segment:
                if narration_lines:
                    current_segment["narrationtext"] = "\n".join(narration_lines).strip().strip('"').strip()
                segments.append(current_segment)
            
            # Parse new segment
            # Format: **Segment 1: Hook (0-10 seconds)**
            segment_match = line.replace("**", "").strip()
            if ":" in segment_match:
                parts = segment_match.split(":", 1)
                segment_num_title = parts[0].replace("Segment", "").strip()
                segment_num = segment_num_title.split()[0]
                segment_title = parts[1].split("(")[0].strip()
                
                # Extract duration from parentheses by calculating range
                # Format: (0-10 seconds) -> duration = 10 - 0 = 10
                duration = 0
                if "(" in line and ")" in line:
                    duration_part = line[line.find("(")+1:line.find(")")]
                    # Extract two numbers (start and end)
                    numbers = re.findall(r'(\d+)', duration_part)
                    if len(numbers) >= 2:
                        start_time = int(numbers[0])
                        end_time = int(numbers[1])
                        duration = end_time - start_time
                    elif len(numbers) == 1:
                        # Fallback: if only one number, use it as duration
                        duration = int(numbers[0])
                
                # Sanitize segment title
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
            # Look for narration text (between ``` markers or after "Narration text")
            if "Narration text" in line or "narration text" in line.lower():
                in_narration = True
                continue
            elif line.strip().startswith("```"):
                if in_narration and not narration_lines:
                    continue  # Opening ```
                elif in_narration and narration_lines:
                    # Closing ``` - done with narration
                    current_segment["narrationtext"] = "\n".join(narration_lines).strip().strip('"').strip()
                    narration_lines = []
                    in_narration = False
                    continue
            elif in_narration:
                narration_lines.append(line)
            # Look for visual guidance (handle both formats and concatenate)
            elif "Visual guidance" in line or "visual guidance" in line.lower():
                # Extract text after colon
                if ":" in line:
                    guidance = line.split(":", 1)[1].strip().strip('"').strip()
                    # Concatenate if already has content
                    if current_segment["visual_guidance_preview"]:
                        current_segment["visual_guidance_preview"] += " " + guidance
                    else:
                        current_segment["visual_guidance_preview"] = guidance
    
    # Save last segment
    if current_segment:
        if narration_lines:
            current_segment["narrationtext"] = "\n".join(narration_lines).strip().strip('"').strip()
        segments.append(current_segment)
    
    # Validate segments before returning
    if not segments:
        print(f"[ERROR] No segments found in segments.md")
        return None, []
    
    # Check for duplicate segment numbers
    segment_numbers = [s["number"] for s in segments]
    duplicates = [num for num in segment_numbers if segment_numbers.count(num) > 1]
    if duplicates:
        print(f"[ERROR] Duplicate segment numbers found: {sorted(set(duplicates))}")
        return None, []
    
    # Validate all segments have required data
    for segment in segments:
        if not segment.get("narrationtext", "").strip():
            print(f"[ERROR] Segment {segment['number']} ({segment['title']}) is missing narration text")
            return None, []
        if not segment.get("visual_guidance_preview", "").strip():
            print(f"[ERROR] Segment {segment['number']} ({segment['title']}) is missing visual guidance preview")
            return None, []
    
    # Sort segments by number
    segments.sort(key=lambda x: x["number"])
    
    return template_title, segments


def create_segment_json(segment_data: Dict, output_path: Path) -> bool:
    """Create a segment JSON file from segment data."""
    json_data = {
        "duration": segment_data.get("duration", 0),
        "narrationtext": segment_data.get("narrationtext", ""),
        "visual_guidance_preview": segment_data.get("visual_guidance_preview", "")
    }
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create segment JSON: {e}")
        return False


def load_segment_hook(topic_dir: Path) -> Optional[Dict]:
    """Load segment JSON file from topic directory (segment{number}.json, segment.json, or Segment1.hook.json)."""
    # Try segment{number}.json first (e.g., segment1.json, segment2.json)
    segment_files = list(topic_dir.glob("segment*.json"))
    if segment_files:
        # Use the first segment file found
        hook_file = segment_files[0]
    else:
        # Fallback to segment.json or Segment1.hook.json for backward compatibility
        hook_file = topic_dir / "segment.json"
        if not hook_file.exists():
            hook_file = topic_dir / "Segment1.hook.json"
    
    if not hook_file.exists():
        print(f"[ERROR] No segment JSON file found in {topic_dir}")
        return None
    
    with open(hook_file, "r", encoding="utf-8") as f:
        return json.load(f)


def find_diagram_reference(topic_dir: Path) -> Optional[Path]:
    """Find diagram reference image (diagram.png or diagram.gif) in topic directory."""
    for ext in [".png", ".gif", ".jpg", ".jpeg"]:
        diagram_path = topic_dir / f"diagram{ext}"
        if diagram_path.exists():
            return diagram_path
    return None


def diagram_to_base64(diagram_path: Path) -> str:
    """Convert diagram image to base64 string for API."""
    with open(diagram_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def generate_story_prompts(hook_data: Dict, num_images: int, has_diagram: bool = False) -> List[str]:
    """
    Generate sequential storytelling prompts from hook data.
    
    Creates sequential moments that build toward answering the question in narrationtext.
    Each image shows a different frame of the narrationtext story progression.
    
    Args:
        hook_data: Segment hook data with narrationtext and visual_guidance_preview
        num_images: Number of sequential images to generate
        has_diagram: Whether a diagram reference is available
    
    Returns:
        List of prompts for sequential storytelling images
    """
    narration = hook_data.get("narrationtext", "")
    visual_guidance = hook_data.get("visual_guidance_preview", "")
    
    # Remove text-related terms from visual guidance to avoid confusion
    text_terms = ["text overlay", "text", "labels", "caption", "annotation", "writing", "lettering"]
    for term in text_terms:
        visual_guidance = visual_guidance.replace(term, "").replace(term.title(), "").replace(term.upper(), "")
    # Clean up extra spaces
    visual_guidance = " ".join(visual_guidance.split())
    
    # Base style instruction for consistency
    style_base = "Educational storytelling style, cinematic 16:9 composition"
    if has_diagram:
        style_base += ", matching the style and color palette of the reference diagram"
    
    no_labels = "NO TEXT, NO LABELS, NO WORDS, NO LETTERING, NO TYPography, NO WRITING, NO ANNOTATIONS, NO CAPTIONS, NO WATERMARKS, NO SIGNATURES. Pure visual storytelling only. Absolutely no text elements whatsoever."
    
    # Create sequential moments that build toward answering the question
    prompts = []
    
    if num_images == 1:
        # Single image: combine question and answer
        prompt = f"{style_base}. {visual_guidance}. {narration}. Visual storytelling moment that answers the question."
        prompts.append(f"{prompt} {no_labels}")
    elif num_images == 2:
        # Two images: question moment and answer moment
        prompts.append(
            f"{style_base}, establishing shot. {visual_guidance}. "
            f"Opening moment: The question is posed visually. {no_labels}"
        )
        prompts.append(
            f"{style_base}, main scene. {narration}. "
            f"Answering moment: Visual answer to the question, clear narrative progression. {no_labels}"
        )
    elif num_images >= 3:
        # Three or more images: question → discovery → answer progression
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
        # Additional frames if more than 3 images
        for i in range(3, num_images):
            frame_num = i + 1
            prompts.append(
                f"{style_base}, scene {frame_num}. {narration}. "
                f"Frame {frame_num}: Continued visual progression, maintaining narrative flow and style consistency. {no_labels}"
            )
    
    return prompts


def generate_image_via_replicate(
    prompt: str,
    output_path: Path,
    generation_attempt: int = 0,
    max_retries: int = 2,
    fast_mode: bool = False,
    diagram_reference: Optional[Path] = None,
    verbose: bool = False
) -> Tuple[bool, Dict]:
    """
    Generate image using Replicate API.
    
    Args:
        prompt: Text prompt for image generation
        output_path: Path to save generated image
        generation_attempt: Current generation attempt (for fallback logic)
        max_retries: Maximum retry attempts on API failure
        fast_mode: If True, use flux-schnell (fast/cheap), else use flux-dev (quality)
        diagram_reference: Optional path to diagram image for style reference
    
    Returns:
        Tuple of (success: bool, metadata: Dict with model_used, cost, time_seconds)
    """
    api_key = get_replicate_key()
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # Track timing
    start_time = time.time()
    
    # Determine which model to use
    if fast_mode:
        current_model = BASE_IMAGE_MODEL_FAST
        print(f"    [INFO] Using fast mode: {current_model}")
    else:
        current_model = BASE_IMAGE_MODEL_QUALITY
        print(f"    [INFO] Using quality mode: {current_model}")
    
    use_fallback = (generation_attempt >= 2 and "flux" in current_model.lower())
    if use_fallback:
        current_model = FALLBACK_IMAGE_MODEL
        print(f"    [INFO] Switching to fallback model: {FALLBACK_IMAGE_MODEL}")
    
    # Determine cost based on model
    model_name_lower = current_model.lower()
    if "flux-dev" in model_name_lower or ("flux" in model_name_lower and "schnell" not in model_name_lower):
        cost = COST_RATES["flux-dev"]
    elif "flux-schnell" in model_name_lower or "schnell" in model_name_lower:
        cost = COST_RATES["flux-schnell"]
    elif "sdxl" in model_name_lower:
        cost = COST_RATES["sdxl"]
    else:
        cost = COST_RATES["flux-dev"]  # Default fallback
    
    # Add style reference to prompt if diagram available (for consistency)
    if diagram_reference and diagram_reference.exists():
        style_ref = "Style reference: match the artistic style, color palette, and visual elements of the reference diagram. "
        prompt = style_ref + prompt
    
    # Prepare input parameters based on model
    # Negative prompt for text avoidance (used by Flux models)
    negative_prompt = (
        "text, letters, words, typography, labels, captions, annotations, writing, "
        "lettering, spelling, words on image, text overlay, watermark, signature, "
        "inscription, script, font, typeface, characters, symbols as text, "
        "alphanumeric, numbers as text, any readable text, any written text, "
        "any printed text, any handwritten text, any visible text, text elements, "
        "signs, banners, posters with text, labels on objects, text in image"
    )
    
    if "flux" in current_model.lower() and "schnell" in current_model.lower():
        # Flux-schnell: fast and cheap, limited to 4 steps
        input_params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": IMAGE_WIDTH,
            "height": IMAGE_HEIGHT,
            "output_format": "png",
            "output_quality": 90,
            "num_outputs": 1,
            "num_inference_steps": 4  # Max for flux-schnell
        }
        # Try to add image reference if model supports it (some flux models do)
        if diagram_reference and diagram_reference.exists():
            try:
                diagram_b64 = diagram_to_base64(diagram_reference)
                # Try adding as image input (may not be supported by all models)
                input_params["image"] = f"data:image/png;base64,{diagram_b64}"
                print(f"    [INFO] Added diagram reference as visual input")
            except Exception as e:
                print(f"    [WARN] Could not add diagram reference as image input: {e}")
                # Style reference already added to prompt above
    elif "flux" in current_model.lower():
        # Flux-dev: better quality, more steps
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
        # Try to add image reference if model supports it
        if diagram_reference and diagram_reference.exists():
            try:
                diagram_b64 = diagram_to_base64(diagram_reference)
                input_params["image"] = f"data:image/png;base64,{diagram_b64}"
                print(f"    [INFO] Added diagram reference as visual input")
            except Exception as e:
                print(f"    [WARN] Could not add diagram reference as image input: {e}")
                # Style reference already added to prompt above
    elif "sdxl" in current_model.lower():
        # SDXL with negative prompt (using same negative prompt as Flux)
        # (Style reference already added to prompt above)
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
        # Generic parameters
        # (Style reference already added to prompt above)
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
    
    # Retry logic
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"    [WARN] Retrying generation (attempt {attempt + 1}/{max_retries + 1})...")
                time.sleep(3)
            
            # Create prediction
            if verbose:
                print(f"    [VERBOSE] API Request:")
                print(f"      URL: {REPLICATE_API_URL}")
                print(f"      Model: {current_model}")
                print(f"      Prompt length: {len(prompt)} chars")
                print(f"      Input params keys: {list(input_params.keys())}")
            
            request_start = time.time()
            response = requests.post(
                REPLICATE_API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )
            request_time = time.time() - request_start
            
            if verbose:
                print(f"    [VERBOSE] API Response:")
                print(f"      Status: {response.status_code}")
                print(f"      Request time: {request_time:.2f}s")
                if response.status_code == 200:
                    try:
                        resp_data = response.json()
                        print(f"      Prediction ID: {resp_data.get('id', 'N/A')}")
                    except:
                        pass
            
            if response.status_code not in [200, 201]:
                error_msg = f"API returned status code: {response.status_code}"
                try:
                    error_data = response.json()
                    error_detail = error_data.get("error", "") or error_data.get("detail", "")
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                if attempt < max_retries:
                    print(f"    [WARN] {error_msg}, retrying...")
                    continue
                print(f"    [ERROR] {error_msg}")
                elapsed_time = time.time() - start_time
                metadata = {
                    "model_used": current_model,
                    "cost": 0.0,
                    "time_seconds": elapsed_time,
                    "error": True
                }
                return (False, metadata)
            
            # Get prediction ID
            prediction_data = response.json()
            prediction_id = prediction_data.get("id")
            prediction_url = prediction_data.get("urls", {}).get("get")
            
            if verbose:
                print(f"    [VERBOSE] Prediction created:")
                print(f"      ID: {prediction_id}")
                print(f"      Status: {prediction_data.get('status', 'N/A')}")
            
            if not prediction_id:
                if attempt < max_retries:
                    continue
                print(f"    [ERROR] No prediction ID in response")
                elapsed_time = time.time() - start_time
                metadata = {
                    "model_used": current_model,
                    "cost": 0.0,
                    "time_seconds": elapsed_time,
                    "error": True
                }
                return (False, metadata)
            
            # Poll for result
            print(f"    [INFO] Prediction ID: {prediction_id[:8]}...")
            print(f"    [INFO] Waiting for image generation (this may take 10-30 seconds)...")
            max_polls = 60
            poll_interval = 5
            poll_count = 0
            
            for poll in range(max_polls):
                poll_count += 1
                time.sleep(poll_interval)
                
                poll_start = time.time()
                get_response = requests.get(
                    prediction_url or f"{REPLICATE_API_URL}/{prediction_id}",
                    headers=headers,
                    timeout=30
                )
                poll_time = time.time() - poll_start
                
                if verbose and poll_count % 5 == 1:  # Log every 5th poll
                    print(f"    [VERBOSE] Poll #{poll_count}: Time={poll_time:.2f}s")
                
                if get_response.status_code != 200:
                    if poll < max_polls - 1:
                        continue
                    print(f"    [ERROR] Failed to get prediction status")
                    elapsed_time = time.time() - start_time
                    metadata = {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": elapsed_time,
                        "error": True
                    }
                    return (False, metadata)
                
                prediction = get_response.json()
                status = prediction.get("status")
                
                if status == "succeeded":
                    output = prediction.get("output")
                    if not output:
                        print(f"    [ERROR] No output in prediction result")
                        elapsed_time = time.time() - start_time
                        metadata = {
                            "model_used": current_model,
                            "cost": 0.0,
                            "time_seconds": elapsed_time,
                            "error": True
                        }
                        return (False, metadata)
                    
                    image_url = output[0] if isinstance(output, list) else output
                    
                    # Download image
                    print(f"    [INFO] Image ready, downloading...")
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    image_bytes = img_response.content
                    
                    # Save image
                    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(image_bytes)
                    
                    file_size = os.path.getsize(output_path)
                    elapsed_time = time.time() - start_time
                    print(f"    [OK] Image downloaded and saved ({file_size:,} bytes)")
                    
                    metadata = {
                        "model_used": current_model,
                        "cost": cost,
                        "time_seconds": elapsed_time,
                        "file_size_bytes": file_size,
                        "prompt_length": len(prompt)
                    }
                    return (True, metadata)
                    
                elif status == "failed":
                    error_msg = prediction.get("error", "Unknown error")
                    print(f"    [ERROR] Prediction failed: {error_msg}")
                    if attempt < max_retries:
                        break  # Break polling loop, will retry
                    elapsed_time = time.time() - start_time
                    metadata = {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": elapsed_time,
                        "error": True
                    }
                    return (False, metadata)
                    
                elif status in ["starting", "processing"]:
                    if poll % 6 == 0:  # Print every 30 seconds
                        print(f"    [INFO] Still processing... ({poll * poll_interval}s elapsed)")
                    continue
                else:
                    if attempt < max_retries:
                        break
                    print(f"    [ERROR] Unknown prediction status: {status}")
                    elapsed_time = time.time() - start_time
                    metadata = {
                        "model_used": current_model,
                        "cost": 0.0,
                        "time_seconds": elapsed_time,
                        "error": True
                    }
                    return (False, metadata)
            
            # If we get here, polling timed out
            if attempt < max_retries:
                continue
            print(f"    [ERROR] Prediction timed out after {max_polls * poll_interval}s")
            elapsed_time = time.time() - start_time
            metadata = {
                "model_used": current_model,
                "cost": 0.0,
                "time_seconds": elapsed_time,
                "error": True
            }
            return (False, metadata)
            
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                print(f"    [WARN] Request timeout, retrying...")
                continue
            print(f"    [ERROR] Request timeout after {max_retries + 1} attempts")
            elapsed_time = time.time() - start_time
            metadata = {
                "model_used": current_model,
                "cost": 0.0,
                "time_seconds": elapsed_time,
                "error": True
            }
            return (False, metadata)
        except Exception as e:
            if attempt < max_retries:
                print(f"    [WARN] Error: {e}, retrying...")
                continue
            print(f"    [ERROR] Error: {e}")
            import traceback
            traceback.print_exc()
            elapsed_time = time.time() - start_time
            metadata = {
                "model_used": current_model,
                "cost": 0.0,
                "time_seconds": elapsed_time,
                "error": True
            }
            return (False, metadata)
    
    # Final fallback if all retries exhausted
    elapsed_time = time.time() - start_time
    metadata = {
        "model_used": current_model,
        "cost": 0.0,
        "time_seconds": elapsed_time,
        "error": True
    }
    return (False, metadata)


def verify_image_no_labels(image_path: Path, max_passes: int = 5, verbose: bool = False) -> Tuple[bool, Dict, str, Dict]:
    """
    Verify image has no text, labels, or words using Gemini vision.
    
    Args:
        image_path: Path to image file
        max_passes: Maximum verification attempts
    
    Returns:
        Tuple of (success, verification_result, error_message, metadata_dict)
        metadata_dict contains: cost, time_seconds, attempts_made
    """
    api_key = get_openrouter_key()
    image_b64 = image_to_base64(str(image_path))
    
    # Track timing and attempts
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
        attempt_start = time.time()
        try:
            if verbose:
                print(f"    [VERBOSE] Verification attempt {attempt + 1}:")
                print(f"      Model: {VERIFICATION_MODEL}")
                print(f"      Image size: {os.path.getsize(image_path):,} bytes")
                print(f"      Base64 length: {len(image_b64):,} chars")
            
            request_start = time.time()
            response = requests.post(
                OPENROUTER_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
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
            request_time = time.time() - request_start
            
            if verbose:
                print(f"      Status: {response.status_code}")
                print(f"      Request time: {request_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if verbose:
                    print(f"      Response length: {len(content)} chars")
                    if len(content) < 500:
                        print(f"      Response content: {content[:200]}...")
                
                try:
                    result = json.loads(content)
                    has_text = result.get("has_text", True)
                    has_annotations = result.get("has_annotations", True)
                    confidence = result.get("confidence", 0.0)
                    
                    if verbose:
                        print(f"      Verification result:")
                        print(f"        has_text: {has_text}")
                        print(f"        has_annotations: {has_annotations}")
                        print(f"        confidence: {confidence:.2f}")
                    
                    # Calculate cost for this verification
                    verification_cost = COST_RATES.get("gpt-4o-mini-verification", COST_RATES["gemini-verification"])
                    total_cost += verification_cost
                    attempt_time = time.time() - attempt_start
                    
                    # Success if no text and no annotations
                    success = not has_text and not has_annotations
                    
                    if success:
                        elapsed_time = time.time() - start_time
                        print(f"    [OK] Verification passed!")
                        print(f"      - Text detected: No")
                        print(f"      - Annotations: No")
                        print(f"      - Confidence: {confidence:.2f}")
                        
                        metadata = {
                            "cost": total_cost,
                            "time_seconds": elapsed_time,
                            "attempts_made": attempts_made,
                            "confidence": confidence
                        }
                        return (True, result, "", metadata)
                    else:
                        # Still charge for verification attempt
                        error_msg = (
                            f"Text/annotations detected: has_text={has_text}, "
                            f"has_annotations={has_annotations}, confidence={confidence:.2f}"
                        )
                        if attempt < max_passes - 1:
                            print(f"    [WARN] Attempt {attempt + 1}/{max_passes}: {error_msg}")
                            time.sleep(2)
                            continue
                        
                        elapsed_time = time.time() - start_time
                        metadata = {
                            "cost": total_cost,
                            "time_seconds": elapsed_time,
                            "attempts_made": attempts_made,
                            "confidence": confidence
                        }
                        return (False, result, error_msg, metadata)
                        
                except json.JSONDecodeError:
                    verification_cost = COST_RATES.get("gpt-4o-mini-verification", COST_RATES["gemini-verification"])
                    total_cost += verification_cost
                    if attempt < max_passes - 1:
                        print(f"    [WARN] Attempt {attempt + 1}/{max_passes}: Invalid JSON response, retrying...")
                        time.sleep(2)
                        continue
                    elapsed_time = time.time() - start_time
                    metadata = {
                        "cost": total_cost,
                        "time_seconds": elapsed_time,
                        "attempts_made": attempts_made
                    }
                    return (False, {}, "Invalid JSON response from verification model", metadata)
            else:
                # Handle rate limits with exponential backoff
                if response.status_code == 429:
                    verification_cost = COST_RATES.get("gpt-4o-mini-verification", COST_RATES["gemini-verification"])
                    total_cost += verification_cost
                    base_wait = 5
                    wait_time = min(base_wait * (2 ** attempt), 60)
                    jitter = random.uniform(0, 5)
                    wait_time = wait_time + jitter
                    print(f"    [WARN] Rate limited, waiting {wait_time:.1f}s (exponential backoff)...")
                    if attempt < max_passes - 1:
                        time.sleep(wait_time)
                        continue
                    elapsed_time = time.time() - start_time
                    metadata = {
                        "cost": total_cost,
                        "time_seconds": elapsed_time,
                        "attempts_made": attempts_made
                    }
                    return (False, {}, f"Rate limited after {max_passes} attempts", metadata)
                
                verification_cost = COST_RATES.get("gpt-4o-mini-verification", COST_RATES["gemini-verification"])
                total_cost += verification_cost
                error_text = response.text
                if attempt < max_passes - 1:
                    print(f"    [WARN] Attempt {attempt + 1}/{max_passes}: API error {response.status_code}")
                    time.sleep(2)
                    continue
                elapsed_time = time.time() - start_time
                metadata = {
                    "cost": total_cost,
                    "time_seconds": elapsed_time,
                    "attempts_made": attempts_made
                }
                return (False, {}, f"API error {response.status_code}: {error_text[:200]}", metadata)
                
        except Exception as e:
            verification_cost = COST_RATES.get("gpt-4o-mini-verification", COST_RATES["gemini-verification"])
            total_cost += verification_cost
            if attempt < max_passes - 1:
                print(f"    [WARN] Attempt {attempt + 1}/{max_passes}: Error - {e}")
                time.sleep(2)
                continue
            elapsed_time = time.time() - start_time
            metadata = {
                "cost": total_cost,
                "time_seconds": elapsed_time,
                "attempts_made": attempts_made
            }
            return (False, {}, f"Error: {e}", metadata)
    
    elapsed_time = time.time() - start_time
    metadata = {
        "cost": total_cost,
        "time_seconds": elapsed_time,
        "attempts_made": attempts_made
    }
    return (False, {}, "All verification attempts failed", metadata)


def process_segments_from_md(
    segments_file: Path,
    diagram_file: Optional[Path],
    num_images: int = 3,
    max_passes: int = 5,
    max_verification_passes: int = 5,
    fast_mode: bool = False,
    dry_run: bool = False,
    retry_failed: bool = False,
    verbose: bool = False
) -> int:
    """
    Process segments.md file and generate images for each segment.
    
    Args:
        segments_file: Path to segments.md file
        diagram_file: Optional path to diagram.png for style reference
        num_images: Number of sequential images to generate per segment
        max_passes: Maximum regeneration attempts per image
        max_verification_passes: Maximum verification API attempts per image
        fast_mode: If True, use fast/cheap model
    
    Returns:
        Total number of successfully generated images across all segments
    """
    # Parse segments.md
    template_title, segments = parse_segments_md(segments_file)
    if not template_title or not segments:
        print(f"[ERROR] Failed to parse segments.md")
        return 0
    
    print(f"\n{'='*60}")
    print(f"Processing segments from: {segments_file.name}")
    print(f"Template: {template_title}")
    print(f"Segments found: {len(segments)}")
    print(f"Images per segment: {num_images}")
    print(f"{'='*60}\n")
    
    # Create base directory structure with number suffix if exists
    base_dir_name = template_title
    base_dir = segments_file.parent / base_dir_name
    counter = 1
    max_attempts = 100
    
    while base_dir.exists() and counter <= max_attempts:
        base_dir_name = f"{template_title}_{counter}"
        base_dir = segments_file.parent / base_dir_name
        counter += 1
    
    if counter > max_attempts:
        print(f"[ERROR] Could not find available folder name after {max_attempts} attempts")
        return 0
    
    if counter > 1:
        print(f"[INFO] Template folder '{template_title}' exists, using '{base_dir_name}' instead")
    
    base_dir.mkdir(exist_ok=True)
    
    # Convert and copy diagram if provided
    if diagram_file and diagram_file.exists():
        target_diagram = base_dir / "diagram.png"
        if not target_diagram.exists():
            try:
                # Convert diagram to PNG if needed
                if diagram_file.suffix.lower() != ".png":
                    print(f"[INFO] Converting diagram from {diagram_file.suffix} to PNG...")
                    img = Image.open(diagram_file)
                    # Convert RGBA to RGB if necessary (for JPEG compatibility)
                    if img.mode == "RGBA":
                        # Create white background
                        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
                        img = rgb_img
                    elif img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")
                    img.save(target_diagram, "PNG")
                    print(f"[OK] Converted and saved diagram to: {target_diagram}")
                else:
                    # Just copy if already PNG
                    import shutil
                    shutil.copy2(diagram_file, target_diagram)
                    print(f"[OK] Copied diagram to: {target_diagram}")
            except Exception as e:
                print(f"[ERROR] Failed to convert/copy diagram: {e}")
                return 0
    
    # Dry-run mode: validate and show what would be generated
    if dry_run:
        print(f"\n{'='*60}")
        print(f"DRY-RUN MODE: Validation Only")
        print(f"{'='*60}\n")
        
        # Validate diagram file if provided
        if diagram_file:
            if not diagram_file.exists():
                print(f"[ERROR] Diagram file not found: {diagram_file}")
                return 0
            try:
                # Try to open and read the diagram to verify it's readable
                img = Image.open(diagram_file)
                img.verify()  # Verify it's a valid image
                print(f"[OK] Diagram file validated: {diagram_file.name}")
                print(f"      Format: {img.format}, Size: {img.size}")
            except Exception as e:
                print(f"[ERROR] Diagram file is not readable or invalid: {e}")
                return 0
        else:
            print(f"[WARN] No diagram file provided - images will be generated without style reference")
        
        print(f"\nTemplate: {template_title}")
        print(f"Base directory: {base_dir}")
        print(f"Segments to process: {len(segments)}")
        print(f"Images per segment: {num_images}")
        print(f"\nSegment breakdown:")
        for segment in segments:
            print(f"  Segment {segment['number']}: {segment['title']}")
            print(f"    Duration: {segment['duration']}s")
            narration_text = segment['narrationtext'][:60]
            try:
                print(f"    Narration: {narration_text}...")
            except UnicodeEncodeError:
                narration_safe = narration_text.encode('ascii', 'replace').decode('ascii')
                print(f"    Narration: {narration_safe}...")
            print(f"    Visual guidance: {segment['visual_guidance_preview'][:60]}...")
            output_folder = base_dir / f"{segment['number']}. {segment['title']}"
            print(f"    Output folder: {output_folder}")
        print(f"\n[OK] Validation passed - all segments are valid")
        
        # Calculate cost estimates
        model_cost = COST_RATES["flux-schnell"] if fast_mode else COST_RATES["flux-dev"]
        verification_cost = COST_RATES.get("gpt-4o-mini-verification", COST_RATES["gemini-verification"])
        
        total_images = len(segments) * num_images
        estimated_generation_cost = total_images * model_cost * max_passes  # Worst case: all retries
        estimated_verification_cost = total_images * verification_cost * max_verification_passes
        total_estimated_cost = estimated_generation_cost + estimated_verification_cost
        
        print(f"\n{'='*60}")
        print(f"COST ESTIMATES")
        print(f"{'='*60}")
        print(f"Total estimated cost: ${total_estimated_cost:.4f}")
        print(f"\nPer-segment breakdown:")
        for segment in segments:
            seg_images = num_images
            seg_gen_cost = seg_images * model_cost * max_passes
            seg_ver_cost = seg_images * verification_cost * max_verification_passes
            seg_total = seg_gen_cost + seg_ver_cost
            print(f"  Segment {segment['number']} ({segment['title']}): ${seg_total:.4f}")
            print(f"    - Generation: ${seg_gen_cost:.4f} ({seg_images} images × {max_passes} max passes)")
            print(f"    - Verification: ${seg_ver_cost:.4f} ({seg_images} images × {max_verification_passes} max passes)")
        print(f"\nPer-image breakdown:")
        img_gen_cost = model_cost * max_passes
        img_ver_cost = verification_cost * max_verification_passes
        img_total = img_gen_cost + img_ver_cost
        print(f"  Per image: ${img_total:.4f}")
        print(f"    - Generation: ${img_gen_cost:.4f} (worst case: {max_passes} attempts)")
        print(f"    - Verification: ${img_ver_cost:.4f} (worst case: {max_verification_passes} attempts)")
        print(f"\nNote: Actual costs may be lower if images pass verification on first attempt")
        print(f"[INFO] Run without --dry-run to generate images")
        return 0
    
    total_successful = 0
    template_total_cost = 0.0
    template_total_time = 0.0
    template_start_time = time.time()
    all_segment_reports = []
    created_segments = []  # Track created segments for cleanup on Ctrl+C
    successful_segments = []  # Track successful segments
    failed_segments = []  # Track failed segments
    failed_segments_info = []  # Track failed segment details for report
    
    # Lock for thread-safe printing and cost tracking
    print_lock = threading.Lock()
    cost_lock = threading.Lock()
    
    def process_single_segment(segment: Dict) -> Tuple[int, Dict, bool, Path]:
        """Process a single segment and return (successful_count, report_data, success_flag, segment_dir)."""
        segment_num = segment["number"]
        segment_title = segment["title"]
        segment_dir_name = f"{segment_num}. {segment_title}"
        segment_dir = base_dir / segment_dir_name
        
        # Handle existing segment folders with number suffix
        counter = 1
        original_segment_dir = segment_dir
        max_attempts = 100
        while segment_dir.exists() and counter <= max_attempts:
            segment_dir_name = f"{segment_num}. {segment_title}_{counter}"
            segment_dir = base_dir / segment_dir_name
            counter += 1
        
        if counter > max_attempts:
            with print_lock:
                print(f"[ERROR] Segment {segment_num}: Could not find available folder name after {max_attempts} attempts")
            return (0, {}, False, segment_dir)
        
        if counter > 1:
            with print_lock:
                print(f"[INFO] Segment {segment_num}: Folder '{original_segment_dir.name}' exists, using '{segment_dir_name}' instead")
        
        segment_dir.mkdir(exist_ok=True)
        
        try:
            with print_lock:
                print(f"\n{'='*60}")
                print(f"[SEGMENT {segment_num}] Processing: {segment_title}")
                print(f"Duration: {segment['duration']}s")
                print(f"{'='*60}\n")
            
            # Create segment{number}.json (lowercase, no spaces)
            segment_json_filename = f"segment{segment_num}.json"
            segment_json_path = segment_dir / segment_json_filename
            if not create_segment_json(segment, segment_json_path):
                with print_lock:
                    print(f"[ERROR] Segment {segment_num}: Failed to create {segment_json_filename}")
                return (0, {}, False, segment_dir)
            
            with print_lock:
                print(f"[SEGMENT {segment_num}] Created {segment_json_filename}: {segment_json_path}")
            
            # Generate images for this segment
            segment_successful = generate_story_images(
                directory=str(segment_dir),
                num_images=num_images,
                max_passes=max_passes,
                max_verification_passes=max_verification_passes,
                fast_mode=fast_mode
            )
            
            # Check if segment generation was successful
            if segment_successful < num_images:
                with print_lock:
                    print(f"[ERROR] Segment {segment_num}: Only {segment_successful}/{num_images} images generated")
                return (segment_successful, {}, False, segment_dir)
            
            # Load segment's generation report if it exists
            segment_report_data = {}
            segment_report_path = segment_dir / "generated_images" / "generation_report.json"
            if segment_report_path.exists():
                try:
                    with open(segment_report_path, "r", encoding="utf-8") as f:
                        segment_report = json.load(f)
                        segment_report_data = {
                            "segment_number": segment_num,
                            "segment_title": segment_title,
                            "segment_duration": segment["duration"],
                            "report": segment_report
                        }
                except Exception as e:
                    with print_lock:
                        print(f"[WARN] Segment {segment_num}: Failed to load segment report: {e}")
            
            with print_lock:
                print(f"[SEGMENT {segment_num}] Complete: {segment_successful}/{num_images} images generated")
            
            return (segment_successful, segment_report_data, True, segment_dir)
            
        except Exception as e:
            with print_lock:
                error_msg = str(e)
                try:
                    print(f"[ERROR] Segment {segment_num}: Processing failed: {error_msg}")
                except UnicodeEncodeError:
                    error_safe = error_msg.encode('ascii', 'replace').decode('ascii')
                    print(f"[ERROR] Segment {segment_num}: Processing failed: {error_safe}")
            return (0, {}, False, segment_dir)
    
    # Handle retry-failed mode
    if retry_failed:
        # Find the most recent template report to identify failed segments
        template_report_path = base_dir / "generation_report.json"
        if not template_report_path.exists():
            # Try to find template directory
            base_dir_candidates = [segments_file.parent / template_title]
            for i in range(1, 100):
                base_dir_candidates.append(segments_file.parent / f"{template_title}_{i}")
            
            for candidate_dir in reversed(base_dir_candidates):  # Check newest first
                candidate_report = candidate_dir / "generation_report.json"
                if candidate_report.exists():
                    template_report_path = candidate_report
                    base_dir = candidate_dir
                    print(f"[INFO] Found previous run in: {base_dir.name}")
                    break
        
        if template_report_path.exists():
            try:
                with open(template_report_path, "r", encoding="utf-8") as f:
                    prev_report = json.load(f)
                    failed_seg_nums = prev_report.get("failed_segments", [])
                    if failed_seg_nums:
                        failed_nums = {seg["segment_number"] for seg in failed_seg_nums}
                        segments = [s for s in segments if s["number"] in failed_nums]
                        print(f"[INFO] Retrying {len(segments)} failed segment(s): {sorted(failed_nums)}")
                    else:
                        print(f"[INFO] No failed segments found in previous run")
                        return 0
            except Exception as e:
                print(f"[ERROR] Failed to read previous report: {e}")
                return 0
        else:
            print(f"[ERROR] No previous generation report found. Run without --retry-failed first.")
            return 0
    
    # Progress tracking
    completed_count = 0
    total_segments = len(segments)
    
    try:
        # Process all segments in parallel
        with ThreadPoolExecutor(max_workers=len(segments)) as executor:
            # Submit all segments for processing
            future_to_segment = {
                executor.submit(process_single_segment, segment): segment 
                for segment in segments
            }
            
            # Process results as they complete (real-time)
            for future in as_completed(future_to_segment):
                segment = future_to_segment[future]
                segment_num = segment["number"]
                
                try:
                    successful_count, report_data, success, seg_dir = future.result()
                    completed_count += 1
                    
                    # Update progress bar
                    with print_lock:
                        print(f"\n[PROGRESS] [{completed_count}/{total_segments} segments complete]")
                    
                    if success:
                        successful_segments.append((segment_num, seg_dir))
                        total_successful += successful_count
                        if report_data:
                            all_segment_reports.append(report_data)
                            # Aggregate costs and times
                            if "report" in report_data and "summary" in report_data["report"]:
                                with cost_lock:
                                    template_total_cost += report_data["report"]["summary"].get("total_cost_usd", 0.0)
                                    template_total_time += report_data["report"]["summary"].get("total_time_seconds", 0.0)
                    else:
                        error_msg = f"Only {successful_count}/{num_images} images generated"
                        failed_segments.append((segment_num, seg_dir))
                        failed_segments_info.append({
                            "segment_number": segment_num,
                            "segment_title": segment["title"],
                            "error_message": error_msg
                        })
                        # Remove failed segment directory
                        if seg_dir and seg_dir.exists():
                            try:
                                shutil.rmtree(seg_dir)
                                with print_lock:
                                    print(f"[INFO] Removed failed segment directory: {seg_dir.name}")
                            except Exception as e:
                                with print_lock:
                                    print(f"[WARN] Failed to remove segment directory {seg_dir.name}: {e}")
                
                except Exception as e:
                    completed_count += 1
                    error_msg = f"Exception during processing: {str(e)}"
                    with print_lock:
                        print(f"[ERROR] Segment {segment_num}: {error_msg}")
                        print(f"[PROGRESS] [{completed_count}/{total_segments} segments complete]")
                    failed_segments.append((segment_num, None))
                    failed_segments_info.append({
                        "segment_number": segment_num,
                        "segment_title": segment.get("title", "Unknown"),
                        "error_message": error_msg
                    })
    
    except KeyboardInterrupt:
        print(f"\n\n[INFO] Interrupted by user (Ctrl+C)")
        print(f"[INFO] Cleaning up all partial results...")
        # Clean up all created segments (including successful ones on Ctrl+C)
        for seg_dir in [base_dir / f"{s['number']}. {s['title']}" for s in segments]:
            if seg_dir.exists():
                try:
                    shutil.rmtree(seg_dir)
                    print(f"[INFO] Removed: {seg_dir.name}")
                except Exception as e:
                    print(f"[WARN] Failed to remove {seg_dir.name}: {e}")
        # Remove base directory if empty or only contains diagram
        if base_dir.exists():
            try:
                contents = list(base_dir.iterdir())
                if len(contents) == 0 or (len(contents) == 1 and contents[0].name == "diagram.png"):
                    shutil.rmtree(base_dir)
                    print(f"[INFO] Removed template directory: {base_dir.name}")
            except Exception as e:
                print(f"[WARN] Failed to remove template directory: {e}")
        return 0
    
    except Exception as e:
        print(f"\n[ERROR] Processing failed: {e}")
        # On general failure, keep successful segments, only remove failed ones
        for seg_num, seg_dir in failed_segments:
            if seg_dir and seg_dir.exists():
                try:
                    shutil.rmtree(seg_dir)
                    print(f"[INFO] Removed failed segment directory: {seg_dir.name}")
                except Exception as e2:
                    print(f"[WARN] Failed to remove segment directory {seg_dir.name}: {e2}")
        return total_successful
    
    except KeyboardInterrupt:
        print(f"\n\n[INFO] Interrupted by user (Ctrl+C)")
        print(f"[INFO] Cleaning up partial results...")
        # Clean up all created segments
        for seg_dir in created_segments:
            if seg_dir.exists():
                try:
                    shutil.rmtree(seg_dir)
                    print(f"[INFO] Removed: {seg_dir.name}")
                except Exception as e:
                    print(f"[WARN] Failed to remove {seg_dir.name}: {e}")
        # Remove base directory if empty or only contains diagram
        if base_dir.exists():
            try:
                contents = list(base_dir.iterdir())
                if len(contents) == 0 or (len(contents) == 1 and contents[0].name == "diagram.png"):
                    shutil.rmtree(base_dir)
                    print(f"[INFO] Removed template directory: {base_dir.name}")
            except Exception as e:
                print(f"[WARN] Failed to remove template directory: {e}")
        return 0
    
    except Exception as e:
        print(f"\n[ERROR] Processing failed: {e}")
        print(f"[INFO] Cleaning up partial results...")
        # Clean up all created segments
        for seg_dir in created_segments:
            if seg_dir.exists():
                try:
                    shutil.rmtree(seg_dir)
                    print(f"[INFO] Removed: {seg_dir.name}")
                except Exception as e2:
                    print(f"[WARN] Failed to remove {seg_dir.name}: {e2}")
        # Remove base directory if empty or only contains diagram
        if base_dir.exists():
            try:
                contents = list(base_dir.iterdir())
                if len(contents) == 0 or (len(contents) == 1 and contents[0].name == "diagram.png"):
                    shutil.rmtree(base_dir)
                    print(f"[INFO] Removed template directory: {base_dir.name}")
            except Exception as e2:
                print(f"[WARN] Failed to remove template directory: {e2}")
        return 0
    
    template_elapsed_time = time.time() - template_start_time
    
    # Print summary of successful vs failed segments
    if failed_segments:
        print(f"\n[WARN] {len(failed_segments)} segment(s) failed, {len(successful_segments)} segment(s) succeeded")
    else:
        print(f"\n[SUCCESS] All {len(successful_segments)} segments processed successfully")
    
    # Create template-level summary report (with only successful segments)
    template_report = {
        "template_title": template_title,
        "segments_requested": len(segments),
        "segments_succeeded": len(successful_segments),
        "segments_failed": len(failed_segments),
        "total_images_requested": len(segments) * num_images,
        "total_images_generated": total_successful,
        "summary": {
            "total_cost": template_total_cost,
            "total_time_seconds": template_total_time,
            "total_elapsed_time_seconds": template_elapsed_time,
            "average_cost_per_image": template_total_cost / total_successful if total_successful > 0 else 0.0,
            "average_time_per_image": template_total_time / total_successful if total_successful > 0 else 0.0
        },
        "segments": all_segment_reports,  # Only includes successful segments
        "failed_segments": failed_segments_info  # Includes failed segments with error messages
    }
    
    # Save template-level report (with timestamp if exists)
    template_report_path = base_dir / "generation_report.json"
    if template_report_path.exists():
        # Create timestamped version
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        timestamped_path = base_dir / f"generation_report_{timestamp}.json"
        try:
            shutil.copy2(template_report_path, timestamped_path)
            print(f"[INFO] Existing template report backed up to: {timestamped_path.name}")
        except Exception as e:
            print(f"[WARN] Failed to backup existing template report: {e}")
    
    try:
        with open(template_report_path, "w", encoding="utf-8") as f:
            json.dump(template_report, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Template-level report saved: {template_report_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save template report: {e}")
    
    print(f"\n{'='*60}")
    print(f"ALL SEGMENTS COMPLETE")
    print(f"{'='*60}")
    print(f"Total images generated: {total_successful}/{len(segments) * num_images}")
    print(f"Total cost: ${template_total_cost:.4f}")
    print(f"Total time: {template_elapsed_time:.1f}s ({template_elapsed_time/60:.1f} minutes)")
    print(f"Template directory: {base_dir}")
    print(f"Template report: {template_report_path}")
    
    return total_successful


def generate_story_images(
    directory: Optional[str] = None,
    topic: Optional[str] = None,
    num_images: int = 3,
    max_passes: int = 5,
    max_verification_passes: int = 5,
    fast_mode: bool = False,
    verbose: bool = False
) -> int:
    """
    Generate sequential storytelling images for a topic.
    
    Args:
        directory: Full path to directory containing Segment1.hook.json (takes precedence over topic)
        topic: Topic name (e.g., "Photosynthesis") - used if directory not provided
        num_images: Number of sequential images to generate
        max_passes: Maximum regeneration attempts per image (if verification fails)
        max_verification_passes: Maximum verification API attempts per image (for rate limits, retries)
        fast_mode: If True, use fast/cheap model (flux-schnell), else use quality model (flux-dev)
    
    Returns:
        Number of successfully generated images
    """
    # Setup paths
    if directory:
        # Use provided directory path
        topic_dir = Path(directory)
        if not topic_dir.is_absolute():
            # If relative, make it relative to current working directory
            topic_dir = Path.cwd() / topic_dir
    elif topic:
        # Use topic name to find directory in Samples folder
        samples_dir = Path(__file__).parent
        topic_dir = samples_dir / topic
    else:
        print(f"[ERROR] Either --directory or --topic must be provided")
        return 0
    
    if not topic_dir.exists():
        print(f"[ERROR] Directory not found: {topic_dir}")
        return 0
    
    if not topic_dir.is_dir():
        print(f"[ERROR] Path is not a directory: {topic_dir}")
        return 0
    
    # Load segment hook data
    topic_name = topic_dir.name
    
    print(f"\n{'='*60}")
    print(f"Generating story images")
    print(f"Directory: {topic_dir}")
    print(f"Topic: {topic_name}")
    print(f"Number of images: {num_images}")
    print(f"Max regeneration passes: {max_passes}")
    print(f"Max verification passes: {max_verification_passes}")
    print(f"Mode: {'Fast (flux-schnell)' if fast_mode else 'Quality (flux-dev)'}")
    print(f"Aspect ratio: 16:9 ({IMAGE_WIDTH}x{IMAGE_HEIGHT})")
    print(f"{'='*60}\n")
    
    hook_data = load_segment_hook(topic_dir)
    if not hook_data:
        return 0
    
    print(f"[OK] Loaded segment hook data")
    print(f"  Narration: {hook_data.get('narrationtext', '')[:80]}...")
    print(f"  Visual guidance: {hook_data.get('visual_guidance_preview', '')}")
    
    # Find diagram reference for style consistency
    # First check in topic_dir, then check parent directory (template level)
    diagram_ref = find_diagram_reference(topic_dir)
    if not diagram_ref:
        # Check parent directory (template level)
        parent_dir = topic_dir.parent
        diagram_ref = find_diagram_reference(parent_dir)
    
    if diagram_ref:
        print(f"[OK] Found diagram reference: {diagram_ref.name}")
        print(f"  Will use as visual style reference for consistency")
    else:
        print(f"[WARN] No diagram reference found (diagram.png/gif)")
        print(f"  Images will be generated without style reference")
    
    # Generate prompts
    prompts = generate_story_prompts(hook_data, num_images, has_diagram=(diagram_ref is not None))
    print(f"\n[INFO] Generated {len(prompts)} sequential prompts for storytelling")
    print(f"  Each image represents a different frame of the narration story progression")
    
    # Create output directory
    output_dir = topic_dir / "generated_images"
    output_dir.mkdir(exist_ok=True)
    
    # Generate images
    successful_images = 0
    generated_images = []
    
    # Track overall statistics
    total_start_time = time.time()
    total_cost = 0.0
    image_metadata = []
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n{'-'*60}")
        print(f"Image {i}/{num_images}")
        print(f"{'-'*60}")
        
        image_path = output_dir / f"story_image_{i:02d}.png"
        
        # Track per-image statistics
        image_start_time = time.time()
        image_cost = 0.0
        image_generation_metadata = []
        image_verification_metadata = []
        
        # Generate image with verification loop
        image_generated = False
        verification_passed = False
        
        for gen_attempt in range(max_passes):
            print(f"\n  Generation Attempt {gen_attempt + 1}/{max_passes}")
            
            if verbose:
                print(f"  [VERBOSE] Full prompt for image {i}:")
                print(f"    {prompt[:200]}..." if len(prompt) > 200 else f"    {prompt}")
            
            # Generate image
            print(f"  Step 1: Generating image...")
            gen_start_time = time.time()
            gen_success, gen_meta = generate_image_via_replicate(
                prompt=prompt,
                output_path=image_path,
                generation_attempt=gen_attempt,
                fast_mode=fast_mode,
                diagram_reference=diagram_ref,
                verbose=verbose
            )
            
            if gen_success:
                image_generated = True
                image_cost += gen_meta["cost"]
                image_generation_metadata.append(gen_meta)
                file_size = os.path.getsize(image_path)
                gen_elapsed = time.time() - gen_start_time
                print(f"  [OK] Image generated successfully ({file_size:,} bytes)")
                print(f"      Cost: ${gen_meta['cost']:.4f}, Time: {gen_meta['time_seconds']:.1f}s")
                if verbose:
                    print(f"      Model used: {gen_meta.get('model_used', 'N/A')}")
                    print(f"      Generation elapsed: {gen_elapsed:.2f}s")
                
                # Verify image has no labels
                print(f"\n  Step 2: Verifying image (no text/labels check)...")
                verify_start_time = time.time()
                verify_success, verify_result, verify_error, verify_meta = verify_image_no_labels(
                    image_path,
                    max_passes=max_verification_passes,
                    verbose=verbose
                )
                verify_elapsed = time.time() - verify_start_time
                
                if verbose:
                    print(f"  [VERBOSE] Verification elapsed: {verify_elapsed:.2f}s")
                    print(f"      Attempts made: {verify_meta.get('attempts_made', 0)}")
                    print(f"      Total verification cost: ${verify_meta.get('cost', 0.0):.4f}")
                
                image_cost += verify_meta["cost"]
                image_verification_metadata.append(verify_meta)
                
                if verify_success:
                    print(f"  [OK] Verification passed - image is clean!")
                    print(f"      Cost: ${verify_meta['cost']:.4f}, Time: {verify_meta['time_seconds']:.1f}s")
                    verification_passed = True
                    generated_images.append(image_path)
                    successful_images += 1
                    
                    # Record image metadata
                    image_elapsed = time.time() - image_start_time
                    image_metadata.append({
                        "image_number": i,
                        "filename": image_path.name,
                        "total_cost": image_cost,
                        "total_time_seconds": image_elapsed,
                        "generation_attempts": len(image_generation_metadata),
                        "verification_attempts": len(image_verification_metadata),
                        "generation_details": image_generation_metadata,
                        "verification_details": image_verification_metadata,
                        "final_model": gen_meta["model_used"],
                        "prompt_snippet": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "verification_confidence": verify_result.get("confidence", 0.0)
                    })
                    total_cost += image_cost
                    break
                else:
                    print(f"  [WARN] Verification failed: {verify_error}")
                    if gen_attempt < max_passes - 1:
                        print(f"  [INFO] Regenerating image (waiting {min(3 * (2 ** gen_attempt), 15)}s)...")
                        time.sleep(min(3 * (2 ** gen_attempt), 15))
                        continue
                    else:
                        print(f"  [ERROR] Failed to generate clean image after {max_passes} attempts")
                        print(f"    Saved image for inspection: {image_path}")
                        break
            else:
                if gen_attempt < max_passes - 1:
                    print(f"  [WARN] Image generation failed, retrying...")
                    time.sleep(3)
                    continue
                else:
                    print(f"  [ERROR] Failed to generate image after {max_passes} attempts")
                    break
    
    # Calculate totals
    total_elapsed = time.time() - total_start_time
    total_minutes = int(total_elapsed // 60)
    total_seconds = int(total_elapsed % 60)
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {successful_images}/{num_images} images generated successfully")
    print(f"{'='*60}")
    
    if successful_images > 0:
        print(f"\n[SUCCESS] Generated images saved to: {output_dir}")
        for img_path in generated_images:
            print(f"  - {img_path.name} ({os.path.getsize(img_path):,} bytes)")
    
    # Cost and time summary
    print(f"\n{'='*60}")
    print(f"COST & TIME SUMMARY")
    print(f"{'='*60}")
    print(f"Total Processing Time: {total_minutes}m {total_seconds}s ({total_elapsed:.1f} seconds)")
    print(f"Total Estimated Cost: ${total_cost:.4f}")
    print(f"\nPer Image Breakdown:")
    for img_meta in image_metadata:
        img_time = img_meta["total_time_seconds"]
        img_mins = int(img_time // 60)
        img_secs = int(img_time % 60)
        print(f"  Image {img_meta['image_number']}: ${img_meta['total_cost']:.4f} | {img_mins}m {img_secs}s ({img_time:.1f}s)")
        print(f"    - Generation: ${sum(g['cost'] for g in img_meta['generation_details']):.4f} | {sum(g['time_seconds'] for g in img_meta['generation_details']):.1f}s")
        print(f"    - Verification: ${sum(v['cost'] for v in img_meta['verification_details']):.4f} | {sum(v['time_seconds'] for v in img_meta['verification_details']):.1f}s")
    
    # Generate detailed report
    report_data = {
        "summary": {
            "total_images_requested": num_images,
            "total_images_generated": successful_images,
            "total_cost_usd": round(total_cost, 4),
            "total_time_seconds": round(total_elapsed, 2),
            "total_time_human": f"{total_minutes}m {total_seconds}s",
            "mode": "fast" if fast_mode else "quality",
            "aspect_ratio": f"{IMAGE_WIDTH}x{IMAGE_HEIGHT}",
            "max_regeneration_passes": max_passes,
            "max_verification_passes": max_verification_passes
        },
        "cost_breakdown": {
            "total_generation_cost": round(sum(sum(g["cost"] for g in img["generation_details"]) for img in image_metadata), 4),
            "total_verification_cost": round(sum(sum(v["cost"] for v in img["verification_details"]) for img in image_metadata), 4),
            "cost_rates_used": COST_RATES
        },
        "time_breakdown": {
            "total_generation_time_seconds": round(sum(sum(g["time_seconds"] for g in img["generation_details"]) for img in image_metadata), 2),
            "total_verification_time_seconds": round(sum(sum(v["time_seconds"] for v in img["verification_details"]) for img in image_metadata), 2),
            "total_waiting_time_seconds": round(total_elapsed - sum(sum(g["time_seconds"] for g in img["generation_details"]) for img in image_metadata) - sum(sum(v["time_seconds"] for v in img["verification_details"]) for img in image_metadata), 2)
        },
        "images": image_metadata,
        "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save JSON report
    report_path = output_dir / "generation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"\n[INFO] Detailed report saved to: {report_path}")
    
    if successful_images == 0:
        print(f"\n[ERROR] No images were generated successfully")
    
    return successful_images


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate sequential storytelling images for video production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process segments.md file (recommended)
  python generate_story_images.py --segments "Doc2/Samples/segments.md" --diagram "Doc2/Samples/Photosynthesis/diagram.png" --num-images 2
  
  # Using directory path (single segment)
  python generate_story_images.py --directory "Doc2/Samples/Photosynthesis/1. Hook"
  python generate_story_images.py --directory "C:/path/to/segment" --num-images 2
  
  # Using topic name (searches in Samples folder)
  python generate_story_images.py --topic Photosynthesis --num-images 3
        """
    )
    parser.add_argument(
        "--segments",
        type=str,
        default=None,
        help="Path to segments.md file (processes all segments in the file)"
    )
    parser.add_argument(
        "--diagram",
        type=str,
        default=None,
        help="Path to diagram.png file (for style reference, used with --segments)"
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=None,
        help="Full path to directory containing segment.json (takes precedence over --topic)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Topic name (searches in Samples folder, used if --directory not provided)"
    )
    parser.add_argument(
        "--num-images",
        type=int,
        default=3,
        help="Number of sequential images to generate (default: 3)"
    )
    parser.add_argument(
        "--max-passes",
        type=int,
        default=5,
        help="Maximum regeneration attempts per image if verification fails (default: 5)"
    )
    parser.add_argument(
        "--max-verification-passes",
        type=int,
        default=5,
        help="Maximum verification API attempts per image (for rate limits, retries) (default: 5)"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use fast/cheap model (flux-schnell) instead of quality model (flux-dev)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate segments.md and show what would be generated without actually generating images"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only failed segments from the last run (reads from generation_report.json)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (API requests/responses, detailed timing, full prompts)"
    )
    
    args = parser.parse_args()
    
    try:
        # Process segments.md if provided
        if args.segments:
            # --diagram is required when using --segments
            if not args.diagram:
                print("[ERROR] --diagram is required when using --segments")
                parser.print_help()
                return 1
            
            segments_path = Path(args.segments)
            if not segments_path.is_absolute():
                segments_path = Path.cwd() / segments_path
            
            diagram_path = Path(args.diagram)
            if not diagram_path.is_absolute():
                diagram_path = Path.cwd() / diagram_path
            
            if not diagram_path.exists():
                print(f"[ERROR] Diagram file not found: {diagram_path}")
                return 1
            
            successful = process_segments_from_md(
                segments_file=segments_path,
                diagram_file=diagram_path,
                num_images=args.num_images,
                max_passes=args.max_passes,
                max_verification_passes=args.max_verification_passes,
                fast_mode=args.fast,
                dry_run=args.dry_run,
                retry_failed=args.retry_failed,
                verbose=args.verbose
            )
        else:
            # Default to Photosynthesis if neither directory nor topic provided
            if not args.directory and not args.topic:
                args.topic = "Photosynthesis"
                print(f"[INFO] No directory or topic specified, using default: {args.topic}")
            
            successful = generate_story_images(
                directory=args.directory,
                topic=args.topic,
                num_images=args.num_images,
                max_passes=args.max_passes,
                max_verification_passes=args.max_verification_passes,
                fast_mode=args.fast
            )
        
        if successful == 0:
            print("\n[ERROR] No images were generated. Check error messages above.")
            return 1
        
        return 0
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
