"""
Educational Video Compositor
Composes educational videos from images and audio using FFmpeg.

Purpose: Create engaging educational videos by synchronizing:
- Static images (one per script part)
- TTS narration audio
- Background music (optional)
- Smooth transitions
"""

import os
import subprocess
import tempfile
import logging
import httpx
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EducationalCompositor:
    """
    Composes educational videos from images and audio assets.

    Features:
    - Synchronize images with narration audio
    - Add background music at low volume
    - Create smooth transitions between segments
    - Output 1080p video optimized for web playback
    """

    def __init__(self, work_dir: Optional[str] = None):
        """
        Initialize educational compositor.

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

    async def compose_educational_video(
        self,
        timeline: List[Dict[str, Any]],
        music_url: Optional[str] = None,
        session_id: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Compose educational video from timeline of video clips/images and audio.

        Args:
            timeline: List of segments, each with:
                - part: Part name (hook, concept, process, conclusion)
                - video_url: URL of the generated video clip (optional)
                - image_url: URL of the image (fallback if no video)
                - audio_url: URL of the narration audio
                - duration: Duration in seconds
            music_url: Optional background music URL
            session_id: Session ID for logging

        Returns:
            Dict with output_path and duration

        Raises:
            Exception: If composition fails
        """
        try:
            logger.info(f"[{session_id}] Starting educational video composition with {len(timeline)} segments")

            # Step 1: Download all assets (videos or images + audio)
            segment_files = await self._download_segment_assets(timeline, session_id)

            # Step 2: Process video clips (normalize if needed, or create from images)
            video_clips = await self._process_video_clips(segment_files, session_id)

            # Step 3: Concatenate video clips
            concatenated_video = await self._concatenate_clips(video_clips, session_id)

            # Step 4: Add narration audio
            video_with_audio = await self._add_narration(
                concatenated_video,
                segment_files,
                session_id
            )

            # Step 5: Add background music if provided
            if music_url:
                final_video = await self._add_background_music(
                    video_with_audio,
                    music_url,
                    session_id
                )
            else:
                final_video = video_with_audio

            # Get video duration
            duration = await self._get_video_duration(final_video)

            logger.info(f"[{session_id}] Educational video composition complete: {final_video}")

            return {
                "output_path": final_video,
                "duration": duration
            }

        except Exception as e:
            logger.error(f"[{session_id}] Educational video composition failed: {e}")
            raise

    async def _download_segment_assets(
        self,
        timeline: List[Dict[str, Any]],
        session_id: str
    ) -> List[Dict[str, str]]:
        """
        Download videos/images and audio for each segment.

        Args:
            timeline: Timeline segments
            session_id: Session ID

        Returns:
            List of dicts with local file paths
        """
        segment_files = []

        async with httpx.AsyncClient(timeout=300.0) as client:
            for i, segment in enumerate(timeline):
                logger.debug(f"[{session_id}] Downloading assets for segment {i + 1}/{len(timeline)}: {segment['part']}")

                # Download video (if available) or image
                video_path = None
                image_path = None

                if segment.get("video_url"):
                    # Download generated video clip
                    logger.info(f"[{session_id}] Downloading video for {segment['part']}")
                    video_response = await client.get(segment["video_url"])
                    video_response.raise_for_status()

                    video_path = os.path.join(self.work_dir, f"{session_id}_seg_{i}_video.mp4")
                    with open(video_path, 'wb') as f:
                        f.write(video_response.content)
                else:
                    # Download image as fallback
                    logger.info(f"[{session_id}] Downloading image for {segment['part']}")
                    image_response = await client.get(segment["image_url"])
                    image_response.raise_for_status()

                    image_path = os.path.join(self.work_dir, f"{session_id}_seg_{i}_image.jpg")
                    with open(image_path, 'wb') as f:
                        f.write(image_response.content)

                # Download audio
                audio_response = await client.get(segment["audio_url"])
                audio_response.raise_for_status()

                audio_path = os.path.join(self.work_dir, f"{session_id}_seg_{i}_audio.mp3")
                with open(audio_path, 'wb') as f:
                    f.write(audio_response.content)

                segment_files.append({
                    "part": segment["part"],
                    "video_path": video_path,
                    "image_path": image_path,
                    "audio_path": audio_path,
                    "duration": segment["duration"]
                })

        logger.info(f"[{session_id}] Downloaded assets for {len(segment_files)} segments")
        return segment_files

    async def _process_video_clips(
        self,
        segment_files: List[Dict[str, str]],
        session_id: str
    ) -> List[str]:
        """
        Process video clips - normalize existing videos or create from images.

        Args:
            segment_files: List of segment file paths
            session_id: Session ID

        Returns:
            List of processed video clip paths
        """
        video_clips = []

        for i, segment in enumerate(segment_files):
            logger.debug(f"[{session_id}] Processing video clip {i + 1}/{len(segment_files)}")

            output_path = os.path.join(self.work_dir, f"{session_id}_clip_{i}.mp4")

            if segment["video_path"]:
                # Normalize existing video to 1080p@30fps
                logger.info(f"[{session_id}] Normalizing generated video for {segment['part']}")
                cmd = [
                    "ffmpeg", "-y",
                    "-i", segment["video_path"],
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    "-an",  # Remove audio from video (we'll add narration separately)
                    "-movflags", "+faststart",
                    output_path
                ]
            else:
                # Create video from static image with duration
                logger.info(f"[{session_id}] Creating video from image for {segment['part']}")
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",  # Loop the image
                    "-i", segment["image_path"],
                    "-t", str(segment["duration"]),  # Duration
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30",
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    output_path
                ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"[{session_id}] FFmpeg processing failed: {result.stderr}")
                raise Exception(f"Failed to process video clip for segment {i}")

            video_clips.append(output_path)

        logger.info(f"[{session_id}] Processed {len(video_clips)} video clips")
        return video_clips

    async def _concatenate_clips(
        self,
        clip_paths: List[str],
        session_id: str
    ) -> str:
        """
        Concatenate video clips into single video.

        Args:
            clip_paths: List of clip file paths
            session_id: Session ID

        Returns:
            Path to concatenated video
        """
        logger.debug(f"[{session_id}] Concatenating {len(clip_paths)} clips")

        # Create concat file
        concat_file = os.path.join(self.work_dir, f"{session_id}_concat_list.txt")
        with open(concat_file, 'w') as f:
            for path in clip_paths:
                f.write(f"file '{path}'\n")

        # Output path
        output_path = os.path.join(self.work_dir, f"{session_id}_concatenated.mp4")

        # Concatenate with concat demuxer
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
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

        # Clean up
        os.remove(concat_file)
        for path in clip_paths:
            os.remove(path)

        return output_path

    async def _add_narration(
        self,
        video_path: str,
        segment_files: List[Dict[str, str]],
        session_id: str
    ) -> str:
        """
        Add narration audio to video.

        Args:
            video_path: Path to video file
            segment_files: List of segment files with audio paths
            session_id: Session ID

        Returns:
            Path to video with narration
        """
        logger.debug(f"[{session_id}] Adding narration audio")

        # Concatenate all audio files
        audio_concat_file = os.path.join(self.work_dir, f"{session_id}_audio_concat.txt")
        with open(audio_concat_file, 'w') as f:
            for segment in segment_files:
                f.write(f"file '{segment['audio_path']}'\n")

        # Concatenate audio
        combined_audio = os.path.join(self.work_dir, f"{session_id}_narration.mp3")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", audio_concat_file,
            "-c", "copy",
            combined_audio
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"[{session_id}] Audio concat failed: {result.stderr}")
            raise Exception("Audio concatenation failed")

        # Add audio to video
        output_path = os.path.join(self.work_dir, f"{session_id}_with_narration.mp4")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", combined_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",  # Match shortest stream duration
            "-movflags", "+faststart",
            output_path
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"[{session_id}] Add narration failed: {result.stderr}")
            raise Exception("Adding narration to video failed")

        logger.info(f"[{session_id}] Narration added successfully")

        # Clean up
        os.remove(audio_concat_file)
        os.remove(combined_audio)
        os.remove(video_path)

        return output_path

    async def _add_background_music(
        self,
        video_path: str,
        music_url: str,
        session_id: str
    ) -> str:
        """
        Add background music to video at low volume.

        Args:
            video_path: Path to video with narration
            music_url: URL of background music
            session_id: Session ID

        Returns:
            Path to final video with music
        """
        logger.debug(f"[{session_id}] Adding background music")

        # Download music
        async with httpx.AsyncClient(timeout=300.0) as client:
            music_response = await client.get(music_url)
            music_response.raise_for_status()

            music_path = os.path.join(self.work_dir, f"{session_id}_music.mp3")
            with open(music_path, 'wb') as f:
                f.write(music_response.content)

        # Add music as background (volume 15%)
        output_path = os.path.join(self.work_dir, f"{session_id}_final.mp4")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-stream_loop", "-1",  # Loop music
            "-i", music_path,
            "-filter_complex", "[1:a]volume=0.15[music];[0:a][music]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
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
            logger.error(f"[{session_id}] Add music failed: {result.stderr}")
            # If adding music fails, just return video without music
            logger.warning(f"[{session_id}] Returning video without background music")
            os.remove(music_path)
            return video_path

        logger.info(f"[{session_id}] Background music added successfully")

        # Clean up
        os.remove(music_path)
        os.remove(video_path)

        return output_path

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
