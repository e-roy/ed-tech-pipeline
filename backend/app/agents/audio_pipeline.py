"""
Audio Pipeline Agent - OpenAI TTS Integration
Generates narration audio from script text using OpenAI's TTS API.
Also generates/processes background music for videos.

Based on Phase 07 Tasks (Audio Pipeline).
"""

import asyncio
import os
import time
import tempfile
import logging
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path
from openai import OpenAI
from sqlalchemy.orm import Session
from .base import AgentInput, AgentOutput
from .music_agent import MusicSelectionAgent, MusicProcessingService
from app.config import get_settings

logger = logging.getLogger(__name__)


def get_audio_duration(filepath: str) -> float:
    """
    Get the duration of an audio file using ffprobe.

    Args:
        filepath: Path to the audio file

    Returns:
        Duration in seconds
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", filepath],
            capture_output=True,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.warning(f"Failed to get audio duration for {filepath}: {e}")
        return 0.0


class AudioPipelineAgent:
    """
    Audio Pipeline Agent that generates TTS audio using OpenAI's gpt-4o-mini-tts model.

    The gpt-4o-mini-tts model provides voice instructions capabilities, allowing for
    customized delivery styles. Configured to present content like a teacher giving
    lessons to middle school students with clear, engaging, and encouraging tone.

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

    # Available voices for gpt-4o-mini-tts model
    # Includes original voices plus new additions: ash, ballad, coral, sage, verse
    AVAILABLE_VOICES = {
        "alloy": "Neutral, balanced",
        "ash": "Clear, articulate",
        "ballad": "Expressive, storytelling",
        "coral": "Warm, conversational",
        "echo": "Male, clear",
        "fable": "British, expressive",
        "onyx": "Deep, authoritative",
        "nova": "Female, energetic",
        "sage": "Professional, measured",
        "shimmer": "Warm, friendly",
        "verse": "Poetic, dynamic"
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
            api_key: OpenAI API key (defaults to AWS Secrets Manager, then env var)
            db: Database session for music selection
            storage_service: Storage service for music processing
            websocket_manager: Optional WebSocketManager for progress updates
        """
        settings = get_settings()
        
        # Try to get API key from parameter, then Secrets Manager, then settings
        if api_key:
            self.api_key = api_key
        else:
            # Try Secrets Manager first
            try:
                from app.services.secrets import get_secret
                self.api_key = get_secret("pipeline/openai-api-key")
                logger.debug("Retrieved OPENAI_API_KEY from AWS Secrets Manager")
            except Exception as e:
                logger.debug(f"Could not retrieve OPENAI_API_KEY from Secrets Manager: {e}, falling back to settings")
                self.api_key = settings.OPENAI_API_KEY
        
        self.db = db
        self.storage_service = storage_service
        self.websocket_manager = websocket_manager

        if not self.api_key:
            logger.warning(
                "OPENAI_API_KEY not set. Audio generation will fail. "
                "Add it to AWS Secrets Manager (pipeline/openai-api-key) or .env file."
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

    def _estimate_speech_duration(self, text: str, speed: float = 1.0) -> float:
        """
        Estimate speech duration based on text length.
        OpenAI TTS generates audio at approximately 150 words per minute at 1.0x speed.
        """
        word_count = len(text.split())
        words_per_minute = 150 * speed
        return (word_count / words_per_minute) * 60

    def _calculate_optimal_speed(self, text: str, target_duration: float) -> float:
        """
        Calculate optimal speed to fit text within target duration.
        Pre-calculates speed to avoid regeneration.
        """
        estimated_duration = self._estimate_speech_duration(text, speed=1.0)
        if estimated_duration <= target_duration:
            return 1.0
        required_speed = estimated_duration / target_duration
        return min(required_speed, 1.25)  # Cap at 1.25x

    async def _generate_single_audio(
        self,
        part_name: str,
        part_data: Dict[str, Any],
        voice: str,
        session_id: str,
        cumulative_items: list,
        part_idx: int,
        total_parts: int,
        voice_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate audio for a single script part with optimized single-pass generation."""
        try:
            text = part_data.get("text", "")

            if not text:
                logger.warning(f"[{session_id}] Part '{part_name}' has no text, skipping audio generation")
                return {
                    "success": False,
                    "error": f"Part '{part_name}' has no text"
                }

            # Update cumulative status: mark audio as processing
            item_id = f"audio_{part_name}"
            if cumulative_items:
                await self._update_cumulative_status(
                    session_id,
                    cumulative_items,
                    item_id,
                    "processing"
                )

            # Get target duration and pre-calculate speed (avoids regeneration)
            target_duration = None
            speed = 1.0
            if "duration" in part_data:
                try:
                    target_duration = float(part_data["duration"])
                    speed = self._calculate_optimal_speed(text, target_duration)
                except (ValueError, TypeError):
                    pass

            logger.info(
                f"[{session_id}] Generating audio for '{part_name}' "
                f"({len(text)} chars, voice: {voice}, speed: {speed:.2f}x)"
            )

            # Voice instructions for teacher-like delivery
            default_instructions = "Present the content like a teacher giving a lesson to middle school students. Use a clear, engaging, and encouraging tone that makes the material easy to understand and interesting."
            instructions = voice_instructions if voice_instructions else default_instructions

            # Generate TTS audio in a single pass with pre-calculated speed
            try:
                response = self.client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice=voice,
                    input=text,
                    instructions=instructions,
                    response_format="mp3",
                    speed=speed
                )
            except TypeError:
                # SDK doesn't support instructions - fall back to tts-1
                logger.warning(f"[{session_id}] Using tts-1 fallback")
                response = self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    response_format="mp3",
                    speed=speed
                )

            # Save to temporary file
            temp_dir = tempfile.gettempdir()
            filename = f"audio_{part_name}_{session_id}.mp3"
            filepath = os.path.join(temp_dir, filename)

            with open(filepath, "wb") as f:
                f.write(response.content)

            # Estimate duration from text (skip ffprobe for speed)
            estimated_duration = self._estimate_speech_duration(text, speed)

            # Calculate cost
            char_count = len(text)
            cost = (char_count / 1_000_000) * self.COST_PER_1M_CHARS

            # Get file size
            file_size = os.path.getsize(filepath)

            # Update cumulative status: mark audio as completed
            if cumulative_items:
                await self._update_cumulative_status(
                    session_id,
                    cumulative_items,
                    item_id,
                    "completed"
                )

            # Send WebSocket update for each audio file generated (backward compatibility)
            if self.websocket_manager and not cumulative_items:
                await self.websocket_manager.broadcast_status(
                    session_id,
                    status="audio_generated",
                    progress=50 + (part_idx * 8),
                    details=f"Generated audio {part_idx} of {total_parts}: {part_name.capitalize()}"
                )

            logger.info(
                f"[{session_id}] Generated audio for '{part_name}': "
                f"{estimated_duration:.1f}s, {file_size} bytes, ${cost:.4f}"
            )

            return {
                "success": True,
                "cost": cost,
                "audio_data": {
                    "part": part_name,
                    "filepath": filepath,
                    "url": "",  # Will be filled by orchestrator after S3 upload
                    "duration": round(estimated_duration, 1),
                    "cost": round(cost, 4),
                    "character_count": char_count,
                    "file_size": file_size,
                    "voice": voice
                }
            }

        except Exception as e:
            logger.error(f"[{session_id}] Error generating audio for '{part_name}': {e}", exc_info=True)
            return {
                "success": False,
                "cost": 0.0,
                "error": str(e)
            }

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
            voice_instructions = input.data.get("voice_instructions")
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

            # Generate audio for all parts in parallel
            audio_files = []
            total_cost = 0.0
            total_parts = len(required_parts)

            # Create tasks for all audio parts
            audio_tasks = [
                self._generate_single_audio(
                    part_name=part_name,
                    part_data=script[part_name],
                    voice=voice,
                    session_id=input.session_id,
                    cumulative_items=cumulative_items,
                    part_idx=idx + 1,
                    total_parts=total_parts,
                    voice_instructions=voice_instructions
                )
                for idx, part_name in enumerate(required_parts)
                if script[part_name].get("text", "")  # Only generate if text exists
            ]

            # Generate all audio files in parallel
            audio_results = await asyncio.gather(*audio_tasks, return_exceptions=True)

            # Process results
            for result in audio_results:
                if isinstance(result, Exception):
                    logger.error(f"[{input.session_id}] Audio generation failed with exception: {result}")
                    continue
                elif isinstance(result, dict) and result.get("success"):
                    audio_files.append(result["audio_data"])
                    total_cost += result.get("cost", 0.0)
                else:
                    logger.warning(f"[{input.session_id}] Audio generation failed: {result.get('error', 'Unknown error')}")

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
