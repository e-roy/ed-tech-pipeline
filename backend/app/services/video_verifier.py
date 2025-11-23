"""
Video verification service for quality checks on generated video clips.

This service performs comprehensive verification on video files including:
- Duration validation
- Resolution validation
- Frame integrity checks
- Audio validation
- Corruption detection
"""
import logging
import os
import tempfile
from typing import Optional
import httpx
import cv2
import ffmpeg

from app.models.verification import (
    VerificationResult,
    VerificationCheck,
    VerificationStatus,
    VerificationType,
    VideoMetadata,
)

logger = logging.getLogger(__name__)


class VideoVerificationService:
    """Service for verifying video quality and integrity."""

    def __init__(self, websocket_manager=None, session_id: Optional[str] = None):
        self.min_resolution_width = 720  # Minimum 720p
        self.min_resolution_height = 480
        self.duration_tolerance = 1.0  # ±1 second tolerance
        self.frame_sample_rate = 10  # Sample every 10th frame
        self.websocket_manager = websocket_manager
        self.session_id = session_id

    async def verify_clip(
        self,
        video_url: str,
        expected_duration: Optional[float] = None,
        clip_index: Optional[int] = None,
    ) -> VerificationResult:
        """
        Verify a video clip for quality and integrity.

        Args:
            video_url: URL to the video file (S3 or local path)
            expected_duration: Expected duration in seconds (optional)
            clip_index: Index of clip in sequence (for logging)

        Returns:
            VerificationResult with all check results
        """
        # Send WebSocket update - starting verification
        if self.websocket_manager and self.session_id:
            await self.websocket_manager.send_progress(
                self.session_id,
                {
                    "type": "verification_update",
                    "verification_type": "video_clip",
                    "status": "verifying",
                    "clip_index": clip_index,
                    "details": f"Verifying video clip {clip_index if clip_index is not None else ''}...",
                }
            )

        result = VerificationResult(
            verification_type=VerificationType.VIDEO_CLIP,
            status=VerificationStatus.PASSED,
            asset_url=video_url,
        )

        temp_file = None
        try:
            # Download video to temp file if it's a URL
            if video_url.startswith("http"):
                temp_file = await self._download_video(video_url)
                video_path = temp_file
            else:
                video_path = video_url

            # Extract metadata using FFprobe
            metadata = self._extract_metadata(video_path)
            result.metadata = metadata.to_dict()

            # Run all verification checks
            self._check_file_exists(result, video_path)
            self._check_duration(result, metadata, expected_duration)
            self._check_resolution(result, metadata)
            self._check_frame_count(result, metadata)
            self._check_audio(result, metadata)
            self._check_frame_integrity(result, video_path)
            self._check_visual_consistency(result, video_path)

            logger.info(
                f"Video verification {'passed' if result.passed else 'failed'} "
                f"for clip {clip_index if clip_index is not None else 'unknown'}: "
                f"{len(result.failed_checks)} failures, {len(result.warning_checks)} warnings"
            )

            # Send WebSocket update - verification complete
            if self.websocket_manager and self.session_id:
                await self.websocket_manager.send_progress(
                    self.session_id,
                    {
                        "type": "verification_update",
                        "verification_type": "video_clip",
                        "status": result.status,
                        "clip_index": clip_index,
                        "passed": result.passed,
                        "failed_checks_count": len(result.failed_checks),
                        "warning_checks_count": len(result.warning_checks),
                        "details": f"Video clip {clip_index if clip_index is not None else ''} verification {'passed' if result.passed else 'failed'}",
                    }
                )

        except Exception as e:
            logger.exception(f"Video verification error: {e}")
            result.status = VerificationStatus.FAILED
            result.error_message = str(e)
            result.add_check(
                VerificationCheck(
                    check_name="verification_execution",
                    status=VerificationStatus.FAILED,
                    message=f"Verification failed with error: {str(e)}",
                    severity="error",
                )
            )

            # Send WebSocket update - verification failed
            if self.websocket_manager and self.session_id:
                await self.websocket_manager.send_progress(
                    self.session_id,
                    {
                        "type": "verification_update",
                        "verification_type": "video_clip",
                        "status": "failed",
                        "clip_index": clip_index,
                        "passed": False,
                        "error": str(e),
                        "details": f"Video clip {clip_index if clip_index is not None else ''} verification failed with error",
                    }
                )

        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file}: {e}")

        return result

    async def verify_final_video(
        self,
        video_url: str,
        expected_duration: Optional[float] = None,
    ) -> VerificationResult:
        """
        Verify the final composed video.

        Args:
            video_url: URL to the final video file
            expected_duration: Expected total duration in seconds

        Returns:
            VerificationResult with all check results
        """
        # Send WebSocket update - starting final video verification
        if self.websocket_manager and self.session_id:
            await self.websocket_manager.send_progress(
                self.session_id,
                {
                    "type": "verification_update",
                    "verification_type": "final_video",
                    "status": "verifying",
                    "details": "Verifying final composed video...",
                }
            )

        result = await self.verify_clip(video_url, expected_duration)
        result.verification_type = VerificationType.FINAL_VIDEO

        # Send WebSocket update - final video verification complete
        if self.websocket_manager and self.session_id:
            await self.websocket_manager.send_progress(
                self.session_id,
                {
                    "type": "verification_update",
                    "verification_type": "final_video",
                    "status": result.status,
                    "passed": result.passed,
                    "failed_checks_count": len(result.failed_checks),
                    "warning_checks_count": len(result.warning_checks),
                    "details": f"Final video verification {'passed' if result.passed else 'failed'}",
                }
            )

        return result

    async def _download_video(self, video_url: str) -> str:
        """Download video from URL to temporary file."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(video_url)
                response.raise_for_status()

                # Create temp file with .mp4 extension
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                    temp_file.write(response.content)
                    return temp_file.name

        except Exception as e:
            logger.error(f"Failed to download video from {video_url}: {e}")
            raise

    def _extract_metadata(self, video_path: str) -> VideoMetadata:
        """Extract video metadata using FFprobe."""
        try:
            probe = ffmpeg.probe(video_path)

            # Get video stream
            video_stream = next(
                (s for s in probe["streams"] if s["codec_type"] == "video"), None
            )
            if not video_stream:
                raise ValueError("No video stream found in file")

            # Get audio stream
            audio_stream = next(
                (s for s in probe["streams"] if s["codec_type"] == "audio"), None
            )

            # Extract metadata
            duration = float(video_stream.get("duration", 0))
            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))

            # Calculate frame count
            nb_frames = video_stream.get("nb_frames")
            if nb_frames:
                frame_count = int(nb_frames)
            else:
                # Estimate from duration and fps
                fps_str = video_stream.get("r_frame_rate", "30/1")
                fps_num, fps_den = map(int, fps_str.split("/"))
                fps = fps_num / fps_den if fps_den > 0 else 30
                frame_count = int(duration * fps)

            # Get FPS
            fps_str = video_stream.get("r_frame_rate", "30/1")
            fps_num, fps_den = map(int, fps_str.split("/"))
            fps = fps_num / fps_den if fps_den > 0 else 30

            # Audio info
            has_audio = audio_stream is not None
            audio_duration = float(audio_stream.get("duration", 0)) if audio_stream else None

            # File size
            file_size = os.path.getsize(video_path) if os.path.exists(video_path) else None

            return VideoMetadata(
                duration=duration,
                width=width,
                height=height,
                frame_count=frame_count,
                fps=fps,
                has_audio=has_audio,
                audio_duration=audio_duration,
                codec=video_stream.get("codec_name"),
                file_size=file_size,
            )

        except Exception as e:
            logger.error(f"Failed to extract metadata from {video_path}: {e}")
            raise

    def _check_file_exists(self, result: VerificationResult, video_path: str) -> None:
        """Check if video file exists and is accessible."""
        if not os.path.exists(video_path):
            result.add_check(
                VerificationCheck(
                    check_name="file_exists",
                    status=VerificationStatus.FAILED,
                    message=f"Video file does not exist: {video_path}",
                    severity="error",
                )
            )
        elif os.path.getsize(video_path) == 0:
            result.add_check(
                VerificationCheck(
                    check_name="file_exists",
                    status=VerificationStatus.FAILED,
                    message="Video file is empty (0 bytes)",
                    severity="error",
                )
            )
        else:
            result.add_check(
                VerificationCheck(
                    check_name="file_exists",
                    status=VerificationStatus.PASSED,
                    message="Video file exists and is accessible",
                    actual_value=os.path.getsize(video_path),
                )
            )

    def _check_duration(
        self,
        result: VerificationResult,
        metadata: VideoMetadata,
        expected_duration: Optional[float],
    ) -> None:
        """Check if video duration matches expected value."""
        if expected_duration is None:
            result.add_check(
                VerificationCheck(
                    check_name="duration",
                    status=VerificationStatus.SKIPPED,
                    message="No expected duration provided",
                )
            )
            return

        duration_diff = abs(metadata.duration - expected_duration)
        if duration_diff > self.duration_tolerance:
            result.add_check(
                VerificationCheck(
                    check_name="duration",
                    status=VerificationStatus.FAILED,
                    message=f"Duration mismatch: {duration_diff:.2f}s difference",
                    expected_value=expected_duration,
                    actual_value=metadata.duration,
                    severity="error",
                )
            )
        elif duration_diff > self.duration_tolerance / 2:
            result.add_check(
                VerificationCheck(
                    check_name="duration",
                    status=VerificationStatus.WARNING,
                    message=f"Duration slightly off: {duration_diff:.2f}s difference",
                    expected_value=expected_duration,
                    actual_value=metadata.duration,
                    severity="warning",
                )
            )
        else:
            result.add_check(
                VerificationCheck(
                    check_name="duration",
                    status=VerificationStatus.PASSED,
                    message=f"Duration within tolerance: {metadata.duration:.2f}s",
                    expected_value=expected_duration,
                    actual_value=metadata.duration,
                )
            )

    def _check_resolution(self, result: VerificationResult, metadata: VideoMetadata) -> None:
        """Check if video resolution meets minimum requirements."""
        if metadata.width < self.min_resolution_width or metadata.height < self.min_resolution_height:
            result.add_check(
                VerificationCheck(
                    check_name="resolution",
                    status=VerificationStatus.FAILED,
                    message=f"Resolution too low: {metadata.width}x{metadata.height}",
                    expected_value=f"{self.min_resolution_width}x{self.min_resolution_height}",
                    actual_value=f"{metadata.width}x{metadata.height}",
                    severity="error",
                )
            )
        else:
            result.add_check(
                VerificationCheck(
                    check_name="resolution",
                    status=VerificationStatus.PASSED,
                    message=f"Resolution meets requirements: {metadata.width}x{metadata.height}",
                    actual_value=f"{metadata.width}x{metadata.height}",
                )
            )

    def _check_frame_count(self, result: VerificationResult, metadata: VideoMetadata) -> None:
        """Check if video has a valid number of frames."""
        if metadata.frame_count <= 0:
            result.add_check(
                VerificationCheck(
                    check_name="frame_count",
                    status=VerificationStatus.FAILED,
                    message="Invalid frame count: 0 frames",
                    actual_value=metadata.frame_count,
                    severity="error",
                )
            )
        elif metadata.frame_count < metadata.fps * 0.5:  # Less than 0.5 seconds of content
            result.add_check(
                VerificationCheck(
                    check_name="frame_count",
                    status=VerificationStatus.WARNING,
                    message=f"Very low frame count: {metadata.frame_count} frames",
                    actual_value=metadata.frame_count,
                    severity="warning",
                )
            )
        else:
            result.add_check(
                VerificationCheck(
                    check_name="frame_count",
                    status=VerificationStatus.PASSED,
                    message=f"Frame count valid: {metadata.frame_count} frames",
                    actual_value=metadata.frame_count,
                )
            )

    def _check_audio(self, result: VerificationResult, metadata: VideoMetadata) -> None:
        """Check if video has audio and if audio duration matches video."""
        if not metadata.has_audio:
            # Not having audio is a warning, not a failure (some clips may not need audio)
            result.add_check(
                VerificationCheck(
                    check_name="audio",
                    status=VerificationStatus.WARNING,
                    message="Video has no audio track",
                    severity="warning",
                )
            )
        elif metadata.audio_duration:
            duration_diff = abs(metadata.audio_duration - metadata.duration)
            if duration_diff > 0.5:
                result.add_check(
                    VerificationCheck(
                        check_name="audio",
                        status=VerificationStatus.WARNING,
                        message=f"Audio/video duration mismatch: {duration_diff:.2f}s",
                        expected_value=metadata.duration,
                        actual_value=metadata.audio_duration,
                        severity="warning",
                    )
                )
            else:
                result.add_check(
                    VerificationCheck(
                        check_name="audio",
                        status=VerificationStatus.PASSED,
                        message="Audio track present and synced",
                        actual_value=metadata.audio_duration,
                    )
                )

    def _check_frame_integrity(self, result: VerificationResult, video_path: str) -> None:
        """Check video frames for corruption by sampling frames."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                result.add_check(
                    VerificationCheck(
                        check_name="frame_integrity",
                        status=VerificationStatus.FAILED,
                        message="Unable to open video file for frame analysis",
                        severity="error",
                    )
                )
                return

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            corrupted_frames = []

            # Sample frames at regular intervals
            for frame_idx in range(0, total_frames, self.frame_sample_rate):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret or frame is None:
                    corrupted_frames.append(frame_idx)
                elif frame.size == 0:
                    corrupted_frames.append(frame_idx)

            cap.release()

            if corrupted_frames:
                result.add_check(
                    VerificationCheck(
                        check_name="frame_integrity",
                        status=VerificationStatus.FAILED,
                        message=f"Found {len(corrupted_frames)} corrupted frames",
                        actual_value=corrupted_frames[:10],  # List first 10
                        severity="error",
                    )
                )
            else:
                result.add_check(
                    VerificationCheck(
                        check_name="frame_integrity",
                        status=VerificationStatus.PASSED,
                        message=f"All sampled frames readable ({total_frames // self.frame_sample_rate} checked)",
                    )
                )

        except Exception as e:
            logger.warning(f"Frame integrity check failed: {e}")
            result.add_check(
                VerificationCheck(
                    check_name="frame_integrity",
                    status=VerificationStatus.WARNING,
                    message=f"Frame integrity check failed: {str(e)}",
                    severity="warning",
                )
            )

    def _check_visual_consistency(self, result: VerificationResult, video_path: str) -> None:
        """Check for visual consistency by comparing frames."""
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                result.add_check(
                    VerificationCheck(
                        check_name="visual_consistency",
                        status=VerificationStatus.SKIPPED,
                        message="Unable to open video for visual analysis",
                    )
                )
                return

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Check first, middle, and last frames
            frames_to_check = [0, total_frames // 2, max(0, total_frames - 1)]
            frames = []

            for frame_idx in frames_to_check:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    frames.append(frame)

            cap.release()

            if len(frames) < 3:
                result.add_check(
                    VerificationCheck(
                        check_name="visual_consistency",
                        status=VerificationStatus.WARNING,
                        message="Could not read enough frames for consistency check",
                        severity="warning",
                    )
                )
                return

            # Check if frames are completely black or white (common artifact)
            issues = []
            for idx, frame in enumerate(frames):
                mean_brightness = frame.mean()
                if mean_brightness < 10:
                    issues.append(f"Frame {frames_to_check[idx]} is nearly black")
                elif mean_brightness > 245:
                    issues.append(f"Frame {frames_to_check[idx]} is nearly white")

            if issues:
                result.add_check(
                    VerificationCheck(
                        check_name="visual_consistency",
                        status=VerificationStatus.WARNING,
                        message=f"Visual artifacts detected: {', '.join(issues)}",
                        severity="warning",
                    )
                )
            else:
                result.add_check(
                    VerificationCheck(
                        check_name="visual_consistency",
                        status=VerificationStatus.PASSED,
                        message="Visual consistency check passed",
                    )
                )

        except Exception as e:
            logger.warning(f"Visual consistency check failed: {e}")
            result.add_check(
                VerificationCheck(
                    check_name="visual_consistency",
                    status=VerificationStatus.SKIPPED,
                    message=f"Visual consistency check skipped: {str(e)}",
                )
            )
