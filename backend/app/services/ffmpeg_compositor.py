"""
FFmpeg Composition Layer
Person C - FFmpeg Video Composition

Purpose: Compose final videos from multiple clips with text overlays,
transitions, and optional background music using FFmpeg.
"""

import os
import subprocess
import tempfile
import logging
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegCompositor:
    """
    Handles video composition using FFmpeg.

    Features:
    - Concatenate multiple video clips
    - Add text overlays (product name, CTA)
    - Add background music
    - Normalize video resolution and FPS
    - Output 1080p final video
    """

    def __init__(self, work_dir: Optional[str] = None):
        """
        Initialize FFmpeg compositor.

        Args:
            work_dir: Working directory for temporary files (default: system temp)
        """
        self.work_dir = work_dir or tempfile.gettempdir()
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)

        # Verify FFmpeg is installed
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            logger.info(f"FFmpeg found: {result.stdout.split()[2]}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"FFmpeg not found or not working: {e}")
            raise RuntimeError("FFmpeg is required but not installed")

    async def compose_final_video(
        self,
        clips: List[Dict[str, Any]],
        text_config: Optional[Dict[str, Any]] = None,
        audio_config: Optional[Dict[str, Any]] = None,
        session_id: str = "unknown"
    ) -> Dict[str, str]:
        """
        Compose final video from clips with text and audio.

        Args:
            clips: List of clip objects with 'url' key
            text_config: Text overlay configuration (product_name, call_to_action, etc.)
            audio_config: Audio configuration (enabled, genre, url)
            session_id: Session ID for logging and file naming

        Returns:
            Dict with 'output_path' key containing path to final video

        Raises:
            Exception: If composition fails
        """
        try:
            logger.info(f"[{session_id}] Starting video composition with {len(clips)} clips")

            # Step 1: Download and normalize clips
            normalized_clips = await self._download_and_normalize_clips(clips, session_id)

            # Step 2: Concatenate clips
            concatenated_path = await self._concatenate_clips(normalized_clips, session_id)

            # Step 3: Add text overlays
            if text_config and (text_config.get("product_name") or text_config.get("call_to_action")):
                video_with_text = await self._add_text_overlays(
                    concatenated_path,
                    text_config,
                    session_id
                )
            else:
                video_with_text = concatenated_path

            # Step 4: Add background music (if enabled)
            if audio_config and audio_config.get("enabled"):
                final_path = await self._add_background_music(
                    video_with_text,
                    audio_config,
                    session_id
                )
            else:
                final_path = video_with_text

            logger.info(f"[{session_id}] Video composition complete: {final_path}")

            return {
                "output_path": final_path,
                "duration": await self._get_video_duration(final_path)
            }

        except Exception as e:
            logger.error(f"[{session_id}] Video composition failed: {e}")
            raise

    async def _download_and_normalize_clips(
        self,
        clips: List[Dict[str, Any]],
        session_id: str
    ) -> List[str]:
        """
        Download clips and normalize to consistent format.

        Args:
            clips: List of clip objects
            session_id: Session ID

        Returns:
            List of paths to normalized clip files
        """
        import httpx

        normalized_paths = []

        for i, clip in enumerate(clips):
            try:
                clip_url = clip.get("url", "")
                if not clip_url:
                    logger.warning(f"[{session_id}] Clip {i} has no URL, skipping")
                    continue

                # Download clip
                logger.debug(f"[{session_id}] Downloading clip {i + 1}/{len(clips)}")

                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.get(clip_url)
                    response.raise_for_status()

                # Save to temp file
                temp_input = os.path.join(
                    self.work_dir,
                    f"{session_id}_clip_{i}_raw.mp4"
                )

                with open(temp_input, 'wb') as f:
                    f.write(response.content)

                # Normalize: 1920x1080, 30fps, h264
                temp_output = os.path.join(
                    self.work_dir,
                    f"{session_id}_clip_{i}_normalized.mp4"
                )

                logger.debug(f"[{session_id}] Normalizing clip {i + 1} to 1080p@30fps")

                cmd = [
                    "ffmpeg", "-y",  # Overwrite output
                    "-i", temp_input,
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-movflags", "+faststart",
                    temp_output
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode != 0:
                    logger.error(f"[{session_id}] FFmpeg normalize failed: {result.stderr}")
                    raise Exception(f"Clip {i} normalization failed")

                normalized_paths.append(temp_output)

                # Clean up raw file
                os.remove(temp_input)

            except Exception as e:
                logger.error(f"[{session_id}] Failed to process clip {i}: {e}")
                # Continue with other clips

        logger.info(f"[{session_id}] Normalized {len(normalized_paths)}/{len(clips)} clips")

        return normalized_paths

    async def _concatenate_clips(
        self,
        clip_paths: List[str],
        session_id: str
    ) -> str:
        """
        Concatenate normalized clips into single video.

        Args:
            clip_paths: List of normalized clip file paths
            session_id: Session ID

        Returns:
            Path to concatenated video
        """
        if not clip_paths:
            raise ValueError("No clips to concatenate")

        if len(clip_paths) == 1:
            # Only one clip, no concatenation needed
            return clip_paths[0]

        logger.debug(f"[{session_id}] Concatenating {len(clip_paths)} clips")

        # Create concat file
        concat_file = os.path.join(self.work_dir, f"{session_id}_concat_list.txt")
        with open(concat_file, 'w') as f:
            for path in clip_paths:
                f.write(f"file '{path}'\n")

        # Output path
        output_path = os.path.join(self.work_dir, f"{session_id}_concatenated.mp4")

        # Concatenate with concat demuxer (fast, no re-encoding)
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",  # Copy streams without re-encoding
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"[{session_id}] FFmpeg concat failed: {result.stderr}")
            raise Exception("Video concatenation failed")

        logger.info(f"[{session_id}] Concatenation complete")

        # Clean up concat file and individual clips
        os.remove(concat_file)
        for path in clip_paths:
            os.remove(path)

        return output_path

    async def _add_text_overlays(
        self,
        input_path: str,
        text_config: Dict[str, Any],
        session_id: str
    ) -> str:
        """
        Add text overlays (product name and CTA).

        Args:
            input_path: Input video path
            text_config: Text configuration
            session_id: Session ID

        Returns:
            Path to video with text overlays
        """
        logger.debug(f"[{session_id}] Adding text overlays")

        product_name = text_config.get("product_name", "")
        call_to_action = text_config.get("call_to_action", "")
        text_color = text_config.get("text_color", "#FFFFFF")
        font = text_config.get("text_font", "DejaVuSans-Bold")

        # Build drawtext filters
        filters = []

        if product_name:
            # Product name: bottom-left, first 70% of video
            filters.append(
                f"drawtext=text='{product_name}':fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf"
                f":fontsize=72:fontcolor={text_color}:x=100:y=h-200"
                f":enable='lt(t,7)'"  # Show for first 7 seconds
            )

        if call_to_action:
            # CTA: center, last 30% of video
            filters.append(
                f"drawtext=text='{call_to_action}':fontfile=/System/Library/Fonts/Supplemental/Arial Bold.ttf"
                f":fontsize=96:fontcolor={text_color}:x=(w-text_w)/2:y=(h-text_h)/2"
                f":enable='gt(t,7)'"  # Show after 7 seconds
            )

        if not filters:
            return input_path

        filter_complex = ",".join(filters)

        output_path = os.path.join(self.work_dir, f"{session_id}_with_text.mp4")

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", filter_complex,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "copy",  # Copy audio
            "-movflags", "+faststart",
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )

        if result.returncode != 0:
            logger.error(f"[{session_id}] FFmpeg text overlay failed: {result.stderr}")
            raise Exception("Text overlay failed")

        logger.info(f"[{session_id}] Text overlays added")

        # Clean up input
        os.remove(input_path)

        return output_path

    async def _add_background_music(
        self,
        input_path: str,
        audio_config: Dict[str, Any],
        session_id: str
    ) -> str:
        """
        Add background music to video.

        Args:
            input_path: Input video path
            audio_config: Audio configuration
            session_id: Session ID

        Returns:
            Path to video with background music
        """
        logger.debug(f"[{session_id}] Adding background music")

        # For MVP, skip music generation
        # In production, would download/generate music file
        # For now, just return the input path
        logger.info(f"[{session_id}] Background music (stub - not implemented)")

        return input_path

    async def _get_video_duration(self, video_path: str) -> float:
        """
        Get video duration in seconds.

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                return float(result.stdout.strip())
            except ValueError:
                return 0.0

        return 0.0
