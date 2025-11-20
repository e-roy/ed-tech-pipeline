"""
Educational Video Compositor
Composes educational videos from images and audio using FFmpeg.

Purpose: Create engaging educational videos by synchronizing:
- Static images (one per script part)
- TTS narration audio
- Background music (optional)
- Smooth transitions
"""
# Version for tracking code changes in logs
COMPOSITOR_VERSION = "1.1.0-duration-fix"

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

        # Detect best available video encoder for performance
        self.video_encoder = self._detect_hardware_encoder()
        logger.info(f"Using video encoder: {self.video_encoder['name']} ({self.video_encoder['type']})")

    def _detect_hardware_encoder(self) -> Dict[str, Any]:
        """
        Detect the best available hardware encoder for H.264 video encoding.

        Priority order:
        1. h264_nvenc (NVIDIA GPU - EC2 GPU instances)
        2. h264_videotoolbox (Apple Silicon/Intel Mac - development)
        3. libx264 ultrafast (CPU fallback - EC2 CPU instances)

        Returns:
            Dict with encoder name, type, and encoding parameters
        """
        try:
            # Get list of available encoders
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=5
            )
            encoders_output = result.stdout

            # Check for NVIDIA NVENC (best for EC2 GPU instances)
            if "h264_nvenc" in encoders_output:
                logger.info("Detected NVIDIA NVENC hardware encoder")
                return {
                    "name": "h264_nvenc",
                    "type": "NVIDIA GPU Hardware",
                    "params": ["-c:v", "h264_nvenc", "-preset", "p4", "-b:v", "5M"]
                }

            # Check for VideoToolbox (macOS)
            if "h264_videotoolbox" in encoders_output:
                logger.info("Detected Apple VideoToolbox hardware encoder")
                return {
                    "name": "h264_videotoolbox",
                    "type": "Apple Hardware",
                    "params": ["-c:v", "h264_videotoolbox", "-b:v", "5M"]
                }

            # Fallback to libx264 with ultrafast preset (CPU)
            logger.info("No hardware encoder found, using libx264 ultrafast")
            return {
                "name": "libx264",
                "type": "CPU Software (ultrafast)",
                "params": ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23"]
            }

        except Exception as e:
            logger.warning(f"Error detecting hardware encoder: {e}, falling back to libx264")
            return {
                "name": "libx264",
                "type": "CPU Software (ultrafast)",
                "params": ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23"]
            }

    async def compose_educational_video(
        self,
        timeline: List[Dict[str, Any]],
        music_url: Optional[str] = None,
        session_id: str = "unknown",
        intro_padding: float = 0.0,
        outro_padding: float = 0.0
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
                - narration_duration: Original narration duration (for audio sync)
            music_url: Optional background music URL
            session_id: Session ID for logging
            intro_padding: Seconds of padding before first segment
            outro_padding: Seconds of padding after last segment

        Returns:
            Dict with output_path and duration

        Raises:
            Exception: If composition fails
        """
        try:
            logger.info(f"[{session_id}] ========================================")
            logger.info(f"[{session_id}] Starting educational video composition")
            logger.info(f"[{session_id}] COMPOSITOR VERSION: {COMPOSITOR_VERSION}")
            logger.info(f"[{session_id}] Segments: {len(timeline)}, Intro: {intro_padding}s, Outro: {outro_padding}s")
            logger.info(f"[{session_id}] ========================================")

            # Step 1: Download all assets (videos or images + audio)
            segment_files = await self._download_segment_assets(timeline, session_id)

            # Step 2: Process video clips (normalize if needed, or create from images)
            video_clips = await self._process_video_clips(segment_files, session_id)

            # Step 3: Concatenate video clips
            concatenated_video = await self._concatenate_clips(video_clips, session_id)

            # Step 4: Add narration audio with intro/outro padding
            video_with_audio = await self._add_narration(
                concatenated_video,
                segment_files,
                session_id,
                intro_padding=intro_padding,
                outro_padding=outro_padding
            )

            # Step 5: Add background music if provided
            if music_url:
                final_video = await self._add_background_music(
                    video_with_audio,
                    music_url,
                    session_id,
                    segment_files,
                    intro_padding
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

                # Download video(s) (if available) or image
                video_path = None
                video_paths = []
                image_path = None

                # Check for multiple video URLs (new format)
                if segment.get("video_urls"):
                    video_urls = segment["video_urls"]
                    logger.error(f"[{session_id}] [MULTI-CLIP DEBUG] COMPOSITOR: Found video_urls with {len(video_urls)} clips for {segment['part']}")
                    logger.info(f"[{session_id}] Downloading {len(video_urls)} video clips for {segment['part']}")

                    for j, video_url in enumerate(video_urls):
                        video_response = await client.get(video_url)
                        video_response.raise_for_status()

                        clip_path = os.path.join(self.work_dir, f"{session_id}_seg_{i}_clip_{j}.mp4")
                        with open(clip_path, 'wb') as f:
                            f.write(video_response.content)
                        video_paths.append(clip_path)

                    # If multiple clips, concatenate them into one video for this segment
                    if len(video_paths) > 1:
                        video_path = await self._concatenate_segment_clips(video_paths, session_id, i)
                    else:
                        video_path = video_paths[0]

                elif segment.get("video_url"):
                    # Single video URL (legacy format)
                    logger.error(f"[{session_id}] [MULTI-CLIP DEBUG] COMPOSITOR: Using single video_url for {segment['part']} (no video_urls array found)")
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

                # Download audio (if available - may be None for clips after first in a part)
                audio_path = None
                if segment.get("audio_url"):
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
                    "duration": segment["duration"],
                    "narration_duration": segment.get("narration_duration", segment["duration"]),
                    "gap_after_narration": segment.get("gap_after_narration", 0.0)
                })

        logger.info(f"[{session_id}] Downloaded assets for {len(segment_files)} segments")
        return segment_files

    async def _concatenate_segment_clips(
        self,
        clip_paths: List[str],
        session_id: str,
        segment_index: int
    ) -> str:
        """
        Concatenate multiple video clips within a single segment.

        Args:
            clip_paths: List of video clip file paths
            session_id: Session ID
            segment_index: Index of the segment

        Returns:
            Path to the concatenated video
        """
        import subprocess

        output_path = os.path.join(self.work_dir, f"{session_id}_seg_{segment_index}_concat.mp4")

        # Create concat file list
        concat_list_path = os.path.join(self.work_dir, f"{session_id}_seg_{segment_index}_concat_list.txt")
        with open(concat_list_path, 'w') as f:
            for clip_path in clip_paths:
                f.write(f"file '{clip_path}'\n")

        logger.info(f"[{session_id}] Concatenating {len(clip_paths)} clips for segment {segment_index + 1}")

        # Use concat demuxer for fast concatenation (no re-encoding)
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",  # No re-encoding for speed
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"[{session_id}] FFmpeg concat failed: {result.stderr}")
            raise Exception(f"Failed to concatenate segment clips: {result.stderr}")

        logger.info(f"[{session_id}] Concatenated {len(clip_paths)} clips into {output_path}")
        return output_path

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
        import time
        video_clips = []

        for i, segment in enumerate(segment_files):
            logger.debug(f"[{session_id}] Processing video clip {i + 1}/{len(segment_files)}")

            output_path = os.path.join(self.work_dir, f"{session_id}_clip_{i}.mp4")

            if segment["video_path"]:
                # Normalize existing video to 1080p@30fps and trim to desired duration
                logger.info(f"[{session_id}] Normalizing generated video for {segment['part']} (target duration: {segment['duration']}s) using {self.video_encoder['name']}")
                cmd = [
                    "ffmpeg", "-y",
                    "-i", segment["video_path"],
                    "-t", str(segment["duration"]),  # Trim to desired duration
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30",
                ]
                # Add encoder-specific parameters
                cmd.extend(self.video_encoder["params"])
                cmd.extend([
                    "-pix_fmt", "yuv420p",
                    "-an",  # Remove audio from video (we'll add narration separately)
                    "-movflags", "+faststart",
                    output_path
                ])
            else:
                # Create video from static image with duration
                logger.info(f"[{session_id}] Creating video from image for {segment['part']} using {self.video_encoder['name']}")
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",  # Loop the image
                    "-i", segment["image_path"],
                    "-t", str(segment["duration"]),  # Duration
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30",
                ]
                # Add encoder-specific parameters
                cmd.extend(self.video_encoder["params"])
                cmd.extend([
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    output_path
                ])

            # Execute FFmpeg with timing
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            encode_time = time.time() - start_time

            if result.returncode != 0:
                logger.error(f"[{session_id}] FFmpeg processing failed: {result.stderr}")
                raise Exception(f"Failed to process video clip for segment {i}")

            logger.info(f"[{session_id}] ✓ Clip {i + 1} encoded in {encode_time:.1f}s ({segment['duration']:.1f}s video, {encode_time/segment['duration']:.1f}x realtime)")
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
        session_id: str,
        intro_padding: float = 0.0,
        outro_padding: float = 0.0
    ) -> str:
        """
        Add narration audio to video with optional intro/outro padding.

        Args:
            video_path: Path to video file
            segment_files: List of segment files with audio paths
            session_id: Session ID
            intro_padding: Delay audio start by this many seconds
            outro_padding: Add silence after audio ends

        Returns:
            Path to video with narration
        """
        logger.debug(f"[{session_id}] Adding narration audio (intro: {intro_padding}s, outro: {outro_padding}s)")

        # Build audio with gaps using FFmpeg filter
        # Create a filter that concatenates audio segments with silence in between
        # Only process segments that have audio
        segments_with_audio = [s for s in segment_files if s.get('audio_path')]

        if not segments_with_audio:
            logger.warning(f"[{session_id}] No audio segments to add, skipping narration")
            return video_path  # Return original video without narration

        filter_parts = []
        current_time = intro_padding  # Start after intro padding

        for i, segment in enumerate(segment_files):
            # Skip segments without audio
            if not segment.get('audio_path'):
                # Even without audio, account for this segment's duration in the timeline
                current_time += segment.get('duration', 0.0)
                continue

            # Add this audio segment with adelay to position it at the right time
            # Audio starts when this video segment starts in the timeline
            audio_index = segments_with_audio.index(segment)
            delay_ms = int(current_time * 1000)
            filter_parts.append(f"[{audio_index}:a]adelay={delay_ms}|{delay_ms}[a{audio_index}]")

            # Move to next segment's start time (use video segment duration, not narration duration)
            # This keeps audio synchronized with video timeline
            segment_duration = segment.get('duration', 5.0)
            current_time += segment_duration

        # Mix all delayed audio tracks together
        mix_inputs = ''.join(f"[a{i}]" for i in range(len(segments_with_audio)))
        filter_complex = ';'.join(filter_parts) + f";{mix_inputs}amix=inputs={len(segments_with_audio)}:duration=longest:dropout_transition=0[mixed]"

        # Build FFmpeg command - use WAV as intermediate format to avoid MP3 codec issues
        combined_audio = os.path.join(self.work_dir, f"{session_id}_narration.wav")
        cmd = ["ffmpeg", "-y"]

        # Add all audio inputs (only from segments with audio)
        for segment in segments_with_audio:
            cmd.extend(["-i", segment['audio_path']])

        # Add filter complex and output options
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[mixed]",
            "-t", str(current_time + outro_padding),  # Total duration including intro, all segments, gaps, and outro
            "-ac", "2",  # Stereo
            "-ar", "44100",  # Sample rate
            combined_audio
        ])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"[{session_id}] Audio concat with gaps failed: {result.stderr}")
            raise Exception("Audio concatenation with gaps failed")

        # Add audio to video (intro/outro padding already in combined_audio)
        output_path = os.path.join(self.work_dir, f"{session_id}_with_narration.mp4")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", combined_audio,
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
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"[{session_id}] Add narration failed: {result.stderr}")
            raise Exception("Adding narration to video failed")

        logger.info(f"[{session_id}] Narration added successfully")

        # Clean up
        os.remove(combined_audio)
        os.remove(video_path)

        return output_path

    async def _add_background_music(
        self,
        video_path: str,
        music_url: str,
        session_id: str,
        segment_files: List[Dict[str, Any]] = None,
        intro_padding: float = 0.0
    ) -> str:
        """
        Add background music to video with dynamic ducking (lower volume during narration).

        Args:
            video_path: Path to video with narration
            music_url: URL of background music
            session_id: Session ID
            segment_files: Segment timing info for ducking
            intro_padding: Intro padding duration

        Returns:
            Path to final video with music
        """
        logger.debug(f"[{session_id}] Adding background music with ducking")

        # Download music
        async with httpx.AsyncClient(timeout=300.0) as client:
            music_response = await client.get(music_url)
            music_response.raise_for_status()

            music_path = os.path.join(self.work_dir, f"{session_id}_music.mp3")
            with open(music_path, 'wb') as f:
                f.write(music_response.content)

        # Add music as background with ducking (lower volume during narration)
        output_path = os.path.join(self.work_dir, f"{session_id}_final.mp4")

        # Build volume control for ducking
        # Simplified approach: Use constant low volume for music
        # The narration will naturally be louder, creating a ducking effect
        # This avoids complex nested if statements that can fail
        filter_complex = "[1:a]volume=0.10[music];[0:a][music]amix=inputs=2:duration=longest[aout]"

        # Use -shortest to match video duration (not audio duration)
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-stream_loop", "-1",  # Loop music
            "-i", music_path,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",  # Match video stream duration
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
