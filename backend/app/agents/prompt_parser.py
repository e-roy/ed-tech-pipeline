"""
Prompt Parser Agent
Person B - Hour 2-4: Prompt Parser Agent Implementation

Purpose: Transform user's natural language prompt into structured,
optimized prompts for image generation with visual consistency controls.

Based on PRD Section 4.2.
"""

import json
import time
import random
import logging
from typing import Optional
import replicate

from app.agents.base import AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class PromptParserAgent:
    """
    Transforms user prompts into structured image generation prompts.

    Uses Llama 3.1 70B via Replicate to analyze product descriptions
    and generate consistent, professional prompts for multiple viewing angles.
    """

    def __init__(self, replicate_api_key: str):
        """
        Initialize the Prompt Parser Agent.

        Args:
            replicate_api_key: Replicate API key for LLM access
        """
        self.api_key = replicate_api_key
        self.client = replicate.Client(api_token=replicate_api_key)
        # Use the latest working Llama model
        self.model = "meta/meta-llama-3-70b-instruct"

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Process user prompt and generate structured image prompts.

        Args:
            input: AgentInput containing:
                - data["user_prompt"]: User's product description
                - data["options"]["num_images"]: Number of images to generate (default: 6)
                - data["options"]["style_keywords"]: Optional style hints

        Returns:
            AgentOutput containing:
                - data["consistency_seed"]: Seed for visual consistency
                - data["style_keywords"]: Extracted style keywords
                - data["product_category"]: Detected product category
                - data["image_prompts"]: List of structured prompts with metadata
        """
        try:
            start_time = time.time()

            # Extract input parameters
            user_prompt = input.data["user_prompt"]
            num_images = input.data.get("options", {}).get("num_images", 6)
            style_keywords = input.data.get("options", {}).get("style_keywords", [])

            logger.info(
                f"[{input.session_id}] Parsing prompt: '{user_prompt}' "
                f"for {num_images} images"
            )

            # Generate consistency seed (same seed = similar visual style)
            consistency_seed = random.randint(100000, 999999)

            # Build LLM system prompt
            system_prompt = self._build_system_prompt(num_images)

            # Call Replicate Llama 3.1
            llm_response = await self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                style_keywords=style_keywords
            )

            # Parse JSON response from LLM
            parsed_data = self._parse_llm_response(llm_response)

            # Add generation parameters to each prompt
            for prompt_obj in parsed_data["image_prompts"]:
                prompt_obj["seed"] = consistency_seed
                prompt_obj["guidance_scale"] = 7.5
                prompt_obj["variation_strength"] = 0.3

            duration = time.time() - start_time

            logger.info(
                f"[{input.session_id}] Generated {len(parsed_data['image_prompts'])} prompts "
                f"in {duration:.2f}s"
            )

            return AgentOutput(
                success=True,
                data={
                    "consistency_seed": consistency_seed,
                    "style_keywords": parsed_data["style_keywords"],
                    "product_category": parsed_data["product_category"],
                    "image_prompts": parsed_data["image_prompts"]
                },
                cost=0.001,  # Llama 3.1 is nearly free
                duration=duration,
                error=None
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[{input.session_id}] Prompt parsing failed: {e}")

            return AgentOutput(
                success=False,
                data={},
                cost=0.0,
                duration=duration,
                error=str(e)
            )

    def _build_system_prompt(self, num_images: int) -> str:
        """
        Build the LLM system prompt for generating image prompts.
        Supports both product photography and advertising narrative modes.

        Args:
            num_images: Number of images to generate prompts for

        Returns:
            System prompt string
        """
        return f"""You are an expert prompt engineer for AI advertising video generation.

Your task: Extract subjects from the user's input and generate {num_images} varied image prompts.

STEP 1: SUBJECT EXTRACTION
Analyze the input and identify ALL subjects (people, objects, products, animals, etc.).

Examples:
- "man buys hat" → subjects: ["man", "hat"]
- "woman drinks coffee" → subjects: ["woman", "coffee"]
- "red sports car" → subjects: ["sports car"]
- "dog plays with ball" → subjects: ["dog", "ball"]

STEP 2: GENERATE VARIATIONS
For each subject, generate multiple variations with different:
- Poses/angles (front, side, 3/4 view, close-up)
- Styles/types (if applicable)
- Lighting/mood
- Composition

Distribute {num_images} total prompts across all subjects.
If 2 subjects: generate ~{num_images//2} variations of each
If 1 subject: generate {num_images} variations of it

STEP 3: PROMPT STRUCTURE
Each prompt should be detailed and specific:
"[SHOT TYPE] professional photo of [SUBJECT with details], [POSE/ANGLE], [LIGHTING], [BACKGROUND], clean advertising photography, 8K, sharp focus"

Examples:
- "Medium shot professional photo of businessman in navy suit, front view facing camera with confident smile, soft studio lighting, white background, clean advertising photography, 8K, sharp focus"
- "Close-up professional photo of brown fedora hat, side angle showing brim detail, dramatic side lighting, neutral gray background, clean advertising photography, 8K, sharp focus"

STEP 4: OUTPUT FORMAT - Return ONLY valid JSON:
{{
    "subjects": ["subject1", "subject2", ...],
    "style_keywords": ["advertising", "professional", "clean"],
    "image_prompts": [
        {{
            "prompt": "[Detailed prompt]",
            "negative_prompt": "blurry, low quality, distorted, amateur, watermark, text, multiple subjects",
            "subject": "which subject this variation shows",
            "variation_type": "front|side|close-up|3-4-view|detail"
        }},
        ... ({num_images} total)
    ]
}}

CRITICAL RULES:
- Each prompt generates ONE clear subject (not multiple subjects in same image)
- Variations should be diverse (different angles, poses, styles)
- Professional advertising quality
- Clean, simple backgrounds (white, gray, or simple solid colors)
- No text, watermarks, or clutter"""

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        style_keywords: list[str]
    ) -> str:
        """
        Call Replicate Llama 3.1 API.

        Args:
            system_prompt: System prompt with instructions
            user_prompt: User's product description
            style_keywords: Optional style hints from user

        Returns:
            LLM response as string

        Raises:
            Exception: If API call fails
        """
        # Build user message with optional style hints
        user_message = f"Product description: {user_prompt}"
        if style_keywords:
            user_message += f"\nStyle preferences: {', '.join(style_keywords)}"

        logger.debug(f"Calling Replicate LLM: {self.model}")

        # Call Replicate API
        output = await self.client.async_run(
            self.model,
            input={
                "system_prompt": system_prompt,
                "prompt": user_message,
                "max_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9
            }
        )

        # Concatenate streaming output
        full_response = "".join([chunk for chunk in output])

        logger.debug(f"LLM response length: {len(full_response)} chars")

        return full_response

    def _parse_llm_response(self, response: str) -> dict:
        """
        Parse and validate LLM JSON response.

        Args:
            response: Raw LLM response string

        Returns:
            Parsed and validated data dict

        Raises:
            ValueError: If response is invalid JSON or missing required fields
        """
        try:
            # Try to extract JSON from response (LLM might add extra text)
            response = response.strip()

            # Find JSON object boundaries
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON object found in response")

            json_str = response[start_idx:end_idx]
            parsed = json.loads(json_str)

            # Validate required fields
            required_fields = ["style_keywords", "image_prompts"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")

            # Add subjects if not present (backward compatibility)
            if "subjects" not in parsed:
                parsed["subjects"] = []

            # Add product_category for backward compatibility
            if "product_category" not in parsed:
                parsed["product_category"] = parsed.get("subjects", ["unknown"])[0] if parsed.get("subjects") else "unknown"

            # Validate image_prompts structure
            if not isinstance(parsed["image_prompts"], list):
                raise ValueError("image_prompts must be a list")

            for i, prompt_obj in enumerate(parsed["image_prompts"]):
                required_prompt_fields = ["prompt", "negative_prompt"]
                for field in required_prompt_fields:
                    if field not in prompt_obj:
                        raise ValueError(
                            f"Missing field '{field}' in image_prompt {i}"
                        )

                # Add view_type for backward compatibility if variation_type exists
                if "variation_type" in prompt_obj and "view_type" not in prompt_obj:
                    prompt_obj["view_type"] = prompt_obj["variation_type"]
                elif "view_type" not in prompt_obj and "variation_type" not in prompt_obj:
                    prompt_obj["view_type"] = "variation"

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response: {response[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

        except Exception as e:
            logger.error(f"Failed to validate LLM response: {e}")
            raise
