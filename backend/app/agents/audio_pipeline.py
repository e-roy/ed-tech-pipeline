"""
Audio Pipeline Agent - OpenAI TTS Integration
Generates narration audio from script text using OpenAI's TTS API.
Also generates/processes background music for videos.

Based on Phase 07 Tasks (Audio Pipeline).
"""

import os
import time
import tempfile
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from openai import OpenAI
from sqlalchemy.orm import Session
from .base import AgentInput, AgentOutput
from .music_agent import MusicSelectionAgent, MusicProcessingService

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
                    "filepath": "{temp_dir}/audio_hook_{session_id}.mp3",
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

    def __init__(
        self,
        api_key: Optional[str] = None,
        db: Optional[Session] = None,
        storage_service: Optional[Any] = None,
        websocket_manager=None
    ):
        """
        Initialize the Audio Pipeline Agent.

        Args:
            api_key: OpenAI API key (defaults to env var)
            db: Database session for music selection
            storage_service: Storage service for music processing
            websocket_manager: Optional WebSocketManager for progress updates
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.db = db
        self.storage_service = storage_service
        self.websocket_manager = websocket_manager

        if not self.api_key:
            logger.warning(
                "OPENAI_API_KEY not set. Audio generation will fail. "
                "Add it to .env file."
            )
        else:
            self.client = OpenAI(api_key=self.api_key)

        # Initialize music agents if db and storage are provided
        if self.db:
            self.music_selector = MusicSelectionAgent(db=self.db)
        if self.storage_service:
            self.music_processor = MusicProcessingService(storage_service=self.storage_service)

    async def _update_cumulative_status(
        self,
        session_id: str,
        cumulative_items: list,
        item_id: str,
        new_status: str
    ):
        """Update a single audio item's status and broadcast the full cumulative state."""
        if not cumulative_items or not self.websocket_manager:
            return

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
            cumulative_items = input.data.get("cumulative_items", [])

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
            total_parts = len(required_parts)
            current_part_idx = 0

            for part_name in required_parts:
                current_part_idx += 1
                part_data = script[part_name]
                text = part_data.get("text", "")

                if not text:
                    logger.warning(f"Part '{part_name}' has no text, skipping audio generation")
                    continue

                # Update cumulative status: mark audio as processing
                item_id = f"audio_{part_name}"
                if cumulative_items:
                    await self._update_cumulative_status(
                        input.session_id,
                        cumulative_items,
                        item_id,
                        "processing"
                    )

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

                # Save to temporary file (cross-platform)
                temp_dir = tempfile.gettempdir()
                # Ensure temp directory exists
                os.makedirs(temp_dir, exist_ok=True)
                
                filename = f"audio_{part_name}_{input.session_id}.mp3"
                filepath = os.path.join(temp_dir, filename)

                # Write audio bytes to file
                with open(filepath, "wb") as f:
                    f.write(response.content)
                
                logger.debug(f"[{input.session_id}] Saved audio file to: {filepath}")

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

                # Update cumulative status: mark audio as completed
                if cumulative_items:
                    await self._update_cumulative_status(
                        input.session_id,
                        cumulative_items,
                        item_id,
                        "completed"
                    )

                # Send WebSocket update for each audio file generated (backward compatibility)
                if self.websocket_manager and not cumulative_items:
                    await self.websocket_manager.broadcast_status(
                        input.session_id,
                        status="audio_generated",
                        progress=50 + (current_part_idx * 8),
                        details=f"Generated audio {current_part_idx} of {total_parts}: {part_name.capitalize()}"
                    )

            # Generate background music if music agents are available
            music_file = None
            if self.db and self.storage_service and hasattr(self, 'music_selector'):
                try:
                    logger.info(f"[{input.session_id}] Generating background music...")
                    music_file = await self._generate_background_music(
                        script=script,
                        total_duration=sum(af["duration"] for af in audio_files),
                        session_id=input.session_id,
                        user_id=input.data.get("user_id")
                    )
                    if music_file:
                        audio_files.append(music_file)
                        logger.info(
                            f"[{input.session_id}] Background music added: "
                            f"{music_file['name']}, {music_file['duration']:.1f}s"
                        )
                except Exception as e:
                    logger.warning(
                        f"[{input.session_id}] Background music generation failed: {e}. "
                        "Continuing without music."
                    )

            duration = time.time() - start_time
            total_duration = sum(af["duration"] for af in audio_files if af["part"] != "music")

            logger.info(
                f"[{input.session_id}] Audio generation complete: "
                f"{len(audio_files)} files (4 narration + {'1 music' if music_file else '0 music'}), "
                f"{total_duration:.1f}s total narration, ${total_cost:.4f}"
            )

            return AgentOutput(
                success=True,
                data={
                    "audio_files": audio_files,
                    "total_duration": round(total_duration, 1),
                    "total_cost": round(total_cost, 4),
                    "voice_used": voice,
                    "has_background_music": music_file is not None
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

    async def _generate_background_music(
        self,
        script: Dict[str, Any],
        total_duration: float,
        session_id: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Select background music for the video.

        NOTE: We don't trim the music here - that will happen during video composition
        when we know the exact final video length. For now, we just select an appropriate
        track and return the full original file.

        Args:
            script: Full script with all parts
            total_duration: Total narration duration in seconds (used for selection, not trimming)
            session_id: Session ID for file naming
            user_id: User ID for storage

        Returns:
            Music file metadata dict or None if generation fails
        """
        # Select appropriate music track based on script mood
        # We use a generous duration requirement (120s+) to ensure we have enough music
        selected_music = await self.music_selector.select_music(
            script=script,
            video_duration=120  # Select tracks that are at least 2 minutes long
        )

        if not selected_music:
            logger.warning(f"[{session_id}] No music tracks available in library")
            return None

        # Return the ORIGINAL music track URL (not processed)
        # The video compositor will trim, fade, and mix this later
        return {
            "part": "music",
            "filepath": "",  # No local filepath - direct S3 URL
            "url": selected_music["s3_url"],  # Original S3 URL
            "duration": selected_music["duration"],  # Original full duration
            "cost": 0.0,  # Music is pre-licensed, no per-use cost
            "track_id": selected_music["track_id"],
            "name": selected_music["name"],
            "category": selected_music["category"],
            "volume": 0.15  # Volume will be applied during video composition
        }

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
