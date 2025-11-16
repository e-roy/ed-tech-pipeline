"""
Audio Pipeline Agent - OpenAI TTS Integration
Generates narration audio from script text using OpenAI's TTS API.

Based on Phase 07 Tasks (Audio Pipeline).
"""

import os
import time
import logging
from typing import Optional
from pathlib import Path
from openai import OpenAI
from .base import AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class AudioPipelineAgent:
    """
    Audio Pipeline Agent that generates TTS audio using OpenAI.

    Input format:
        {
            "script": {
                "hook": {"text": str, "duration": str, ...},
                "concept": {"text": str, "duration": str, ...},
                "process": {"text": str, "duration": str, ...},
                "conclusion": {"text": str, "duration": str, ...}
            },
            "voice": str (optional, defaults to "alloy"),
            "audio_option": "tts" | "upload" | "none" | "instrumental"
        }

    Output format:
        {
            "audio_files": [
                {
                    "part": "hook",
                    "filepath": "/tmp/audio_hook.mp3",
                    "url": "",  # Empty until S3 upload by orchestrator
                    "duration": 9.8,
                    "cost": 0.015
                },
                ...
            ],
            "total_duration": 57.7,
            "total_cost": 0.06
        }
    """

    # OpenAI TTS pricing: $15 per 1M characters
    COST_PER_1M_CHARS = 15.00

    # Default voice: alloy (neutral, balanced)
    DEFAULT_VOICE = "alloy"

    # Available voices
    AVAILABLE_VOICES = {
        "alloy": "Neutral, balanced",
        "echo": "Male, clear",
        "fable": "British, expressive",
        "onyx": "Deep, authoritative",
        "nova": "Female, energetic",
        "shimmer": "Warm, friendly"
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Audio Pipeline Agent.

        Args:
            api_key: OpenAI API key (defaults to env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            logger.warning(
                "OPENAI_API_KEY not set. Audio generation will fail. "
                "Add it to .env file."
            )
        else:
            self.client = OpenAI(api_key=self.api_key)

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Process script and generate TTS audio for each part.

        Args:
            input: AgentInput with script and voice configuration

        Returns:
            AgentOutput with audio files, costs, and duration
        """
        start_time = time.time()

        try:
            # Validate API key
            if not self.api_key:
                raise ValueError(
                    "OPENAI_API_KEY not configured. "
                    "Set it in .env or pass to constructor."
                )

            # Extract input data
            script = input.data.get("script", {})
            voice = input.data.get("voice", self.DEFAULT_VOICE)
            audio_option = input.data.get("audio_option", "tts")

            # Handle non-TTS options
            if audio_option != "tts":
                return self._handle_non_tts_option(audio_option, start_time)

            # Validate script structure
            if not script:
                raise ValueError("Script is required in input.data")

            required_parts = ["hook", "concept", "process", "conclusion"]
            missing_parts = [p for p in required_parts if p not in script]
            if missing_parts:
                raise ValueError(
                    f"Script missing required parts: {', '.join(missing_parts)}"
                )

            # Validate voice
            if voice not in self.AVAILABLE_VOICES:
                logger.warning(
                    f"Voice '{voice}' not recognized, using default '{self.DEFAULT_VOICE}'"
                )
                voice = self.DEFAULT_VOICE

            # Generate audio for each part
            audio_files = []
            total_cost = 0.0

            for part_name in required_parts:
                part_data = script[part_name]
                text = part_data.get("text", "")

                if not text:
                    logger.warning(f"Part '{part_name}' has no text, skipping audio generation")
                    continue

                logger.info(
                    f"[{input.session_id}] Generating audio for '{part_name}' "
                    f"({len(text)} chars, voice: {voice})"
                )

                # Generate TTS audio using OpenAI
                response = self.client.audio.speech.create(
                    model="tts-1",  # Use tts-1 (faster, cheaper) or tts-1-hd (higher quality)
                    voice=voice,
                    input=text,
                    response_format="mp3"
                )

                # Save to temporary file
                filename = f"audio_{part_name}_{input.session_id}.mp3"
                filepath = f"/tmp/{filename}"

                # Write audio bytes to file
                with open(filepath, "wb") as f:
                    f.write(response.content)

                # Get file size for verification
                file_size = os.path.getsize(filepath)

                # Calculate cost (based on character count)
                char_count = len(text)
                cost = (char_count / 1_000_000) * self.COST_PER_1M_CHARS

                # Estimate duration based on speaking rate (~150 words/min)
                words = len(text.split())
                estimated_duration = (words / 150) * 60  # seconds

                audio_files.append({
                    "part": part_name,
                    "filepath": filepath,
                    "url": "",  # Will be filled by orchestrator after S3 upload
                    "duration": round(estimated_duration, 1),
                    "cost": round(cost, 4),
                    "character_count": char_count,
                    "file_size": file_size,
                    "voice": voice
                })

                total_cost += cost

                logger.info(
                    f"[{input.session_id}] Generated audio for '{part_name}': "
                    f"{estimated_duration:.1f}s, {file_size} bytes, ${cost:.4f}"
                )

            duration = time.time() - start_time
            total_duration = sum(af["duration"] for af in audio_files)

            logger.info(
                f"[{input.session_id}] Audio generation complete: "
                f"{len(audio_files)} files, {total_duration:.1f}s total, "
                f"${total_cost:.4f}"
            )

            return AgentOutput(
                success=True,
                data={
                    "audio_files": audio_files,
                    "total_duration": round(total_duration, 1),
                    "total_cost": round(total_cost, 4),
                    "voice_used": voice
                },
                cost=total_cost,
                duration=duration
            )

        except Exception as e:
            error_msg = f"Audio generation failed: {str(e)}"
            logger.error(f"[{input.session_id}] {error_msg}", exc_info=True)

            return AgentOutput(
                success=False,
                data={},
                cost=0.0,
                duration=time.time() - start_time,
                error=error_msg
            )

    def _handle_non_tts_option(
        self,
        audio_option: str,
        start_time: float
    ) -> AgentOutput:
        """
        Handle non-TTS audio options (upload, none, instrumental).

        For now, these return success with empty audio files.
        TODO: Implement upload and instrumental options.
        """
        logger.info(f"Audio option '{audio_option}' selected (non-TTS)")

        return AgentOutput(
            success=True,
            data={
                "audio_files": [],
                "total_duration": 0.0,
                "total_cost": 0.0,
                "audio_option": audio_option,
                "message": f"Audio option '{audio_option}' - no TTS generated"
            },
            cost=0.0,
            duration=time.time() - start_time
        )

    async def get_available_voices(self) -> list[dict]:
        """
        Get available voices from OpenAI TTS.

        Returns:
            List of voice objects with id, name, and description
        """
        return [
            {
                "voice_id": voice_id,
                "name": voice_id.capitalize(),
                "description": description
            }
            for voice_id, description in self.AVAILABLE_VOICES.items()
        ]
