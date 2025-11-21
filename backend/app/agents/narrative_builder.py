"""
Narrative Builder Agent

This agent generates a structured narrative script for a 60-second video.
It creates a 4-part structure (hook, concept, process, conclusion) with:
- Narration text for each part
- Clip duration suggestions
- Visual guidance for each scene
- Key concepts to highlight
"""

import time
import json
import logging
import uuid
from typing import Optional, List, Dict, Any
import replicate
from app.agents.base import AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class NarrativeBuilderAgent:
    """
    Generates narrative structure and script for educational/promotional videos.

    Input data expected:
    - user_id: str - The ID of the user requesting the narrative
    - topic: str - The main topic/subject of the video
    - learning_objective: str - What the viewer should learn/understand
    - key_points: List[str] - Array of key points to cover

    Output data provided:
    - session_id: str - Unique session ID for this narrative
    - script: dict - The complete script structure with 4 parts
    - cost: float - Cost of the LLM call
    - duration: float - Time taken to generate
    """

    def __init__(self, replicate_api_key: Optional[str] = None):
        """
        Initialize Narrative Builder Agent.
        
        Args:
            replicate_api_key: Replicate API key (defaults to AWS Secrets Manager, then env var)
        """
        # Try to get API key from parameter, then Secrets Manager, then settings
        if replicate_api_key:
            self.api_key = replicate_api_key
        else:
            # Try Secrets Manager first
            try:
                from app.services.secrets import get_secret
                self.api_key = get_secret("pipeline/replicate-api-key")
                logger.debug("Retrieved REPLICATE_API_KEY from AWS Secrets Manager for NarrativeBuilderAgent")
            except Exception as e:
                logger.debug(f"Could not retrieve REPLICATE_API_KEY from Secrets Manager: {e}, falling back to settings")
                from app.config import get_settings
                settings = get_settings()
                self.api_key = settings.REPLICATE_API_KEY
        
        if not self.api_key:
            logger.warning(
                "REPLICATE_API_KEY not set. Narrative generation will fail. "
                "Add it to AWS Secrets Manager (pipeline/replicate-api-key) or .env file."
            )
            self.client = None
        else:
            self.client = replicate.Client(api_token=self.api_key)
        
        self.model = "meta/meta-llama-3-70b-instruct"
        self.cost_per_call = 0.001  # Llama 3 is nearly free

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Main processing method that generates the narrative script.

        Args:
            input: AgentInput containing user_id, topic, learning_objective, and key_points

        Returns:
            AgentOutput with success status, script data, cost, and duration
        """
        try:
            start_time = time.time()

            # Extract input data
            user_id = input.data.get("user_id")
            topic = input.data.get("topic", "")
            learning_objective = input.data.get("learning_objective", "")
            key_points = input.data.get("key_points", [])

            # Validate inputs
            if not topic:
                raise ValueError("Topic is required")
            if not learning_objective:
                raise ValueError("Learning objective is required")
            if not key_points or len(key_points) == 0:
                raise ValueError("At least one key point is required")

            # Generate a new session ID for this narrative
            session_id = str(uuid.uuid4())

            logger.info(f"[{session_id}] Building narrative for topic: {topic}")
            logger.info(f"[{session_id}] User ID: {user_id}, Key Points: {len(key_points)}")

            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(topic, learning_objective, key_points)

            # Call LLM to generate narrative
            llm_response = await self._call_llm(system_prompt, user_prompt)

            # Parse the response into structured script
            script = self._parse_script_response(llm_response)

            # Validate script structure
            self._validate_script(script)

            duration = time.time() - start_time

            logger.info(f"[{session_id}] Narrative built successfully in {duration:.2f}s")

            return AgentOutput(
                success=True,
                data={
                    "session_id": session_id,
                    "script": script,
                    "user_id": user_id,
                    "topic": topic,
                    "learning_objective": learning_objective
                },
                cost=self.cost_per_call,
                duration=duration,
                error=None
            )

        except Exception as e:
            logger.error(f"Narrative building failed: {e}", exc_info=True)
            return AgentOutput(
                success=False,
                data={},
                cost=0.0,
                duration=time.time() - start_time,
                error=str(e)
            )

    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM."""
        return """You are an expert video script writer and educational content creator. Your task is to create engaging, concise scripts for 60-second educational videos.

You must create a script with EXACTLY 4 parts:
1. HOOK (10-15 seconds) - Grab attention, pose a question or intriguing statement
2. CONCEPT (15-20 seconds) - Introduce the main idea/learning objective
3. PROCESS (20-25 seconds) - Explain how it works, key steps, or main points
4. CONCLUSION (10 seconds) - Summarize key takeaway and call-to-action

For each part, you must provide:
- narration: The exact script text to be spoken
- duration: Suggested duration in seconds
- visual_guidance: Description of what should be shown on screen
- key_concepts: Array of 1-3 key terms/concepts to highlight visually

The narration should be:
- Conversational and engaging
- Clear and concise
- Suitable for voice-over
- Timed appropriately for the duration

The visual guidance should be:
- Specific and actionable
- Describe scenes, graphics, text overlays, or animations
- Support the narration

You MUST respond with valid JSON in this exact structure:
{
  "hook": {
    "narration": "string",
    "duration": number,
    "visual_guidance": "string",
    "key_concepts": ["string"]
  },
  "concept": {
    "narration": "string",
    "duration": number,
    "visual_guidance": "string",
    "key_concepts": ["string"]
  },
  "process": {
    "narration": "string",
    "duration": number,
    "visual_guidance": "string",
    "key_concepts": ["string"]
  },
  "conclusion": {
    "narration": "string",
    "duration": number,
    "visual_guidance": "string",
    "key_concepts": ["string"]
  }
}

Do not include any text before or after the JSON object."""

    def _build_user_prompt(
        self,
        topic: str,
        learning_objective: str,
        key_points: List[str]
    ) -> str:
        """Build the user prompt with specific topic and requirements."""
        key_points_formatted = "\n".join([f"- {point}" for point in key_points])

        return f"""Create a 60-second video script about the following topic:

TOPIC: {topic}

LEARNING OBJECTIVE: {learning_objective}

KEY POINTS TO COVER:
{key_points_formatted}

Remember to create an engaging hook, clearly explain the concept, walk through the process/key points, and end with a strong conclusion. The total duration should be approximately 60 seconds across all 4 parts.

Respond with ONLY the JSON object, no additional text."""

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call the Replicate LLM API.

        Args:
            system_prompt: System instructions for the LLM
            user_prompt: User query/request

        Returns:
            str: The LLM's response
        """
        if not self.client:
            raise ValueError("REPLICATE_API_KEY not configured. Set it in AWS Secrets Manager (pipeline/replicate-api-key) or .env file.")
        
        logger.info("Calling Replicate API with Llama 3 70B...")

        output = await self.client.async_run(
            self.model,
            input={
                "system_prompt": system_prompt,
                "prompt": user_prompt,
                "max_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 50
            }
        )

        # Concatenate streaming output
        full_response = "".join([chunk for chunk in output])

        logger.info(f"Received LLM response: {len(full_response)} characters")

        return full_response

    def _parse_script_response(self, response: str) -> dict:
        """
        Parse the LLM response to extract JSON script structure.

        Args:
            response: Raw LLM response string

        Returns:
            dict: Parsed script structure
        """
        # Clean up response
        response = response.strip()

        # Find JSON object boundaries
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON object found in LLM response")

        json_str = response[start_idx:end_idx]

        try:
            script = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"JSON string: {json_str[:500]}...")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

        return script

    def _validate_script(self, script: dict) -> None:
        """
        Validate that the script has all required parts and fields.

        Args:
            script: The parsed script dictionary

        Raises:
            ValueError: If script is missing required parts or fields
        """
        required_parts = ["hook", "concept", "process", "conclusion"]
        required_fields = ["narration", "duration", "visual_guidance", "key_concepts"]

        # Check all parts exist
        for part in required_parts:
            if part not in script:
                raise ValueError(f"Script missing required part: {part}")

            # Check all fields exist in each part
            for field in required_fields:
                if field not in script[part]:
                    raise ValueError(f"Script part '{part}' missing required field: {field}")

            # Validate types
            if not isinstance(script[part]["narration"], str):
                raise ValueError(f"Narration in '{part}' must be a string")

            if not isinstance(script[part]["duration"], (int, float)):
                raise ValueError(f"Duration in '{part}' must be a number")

            if not isinstance(script[part]["visual_guidance"], str):
                raise ValueError(f"Visual guidance in '{part}' must be a string")

            if not isinstance(script[part]["key_concepts"], list):
                raise ValueError(f"Key concepts in '{part}' must be an array")

        # Check total duration is reasonable (45-75 seconds acceptable range)
        total_duration = sum(
            script[part]["duration"] for part in required_parts
        )

        if total_duration < 45 or total_duration > 75:
            logger.warning(
                f"Total script duration {total_duration}s is outside recommended range (45-75s)"
            )
