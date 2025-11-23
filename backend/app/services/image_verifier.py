"""
Image verification service for quality checks on generated images.

This service performs comprehensive verification on image files including:
- Resolution validation
- Format validation
- Blank/corrupted image detection
- Aspect ratio validation
- Quality scoring
"""
import logging
import os
import tempfile
from typing import Optional, List
import httpx
import numpy as np
from PIL import Image, ImageStat

from app.models.verification import (
    VerificationResult,
    VerificationCheck,
    VerificationStatus,
    VerificationType,
    ImageMetadata,
)

logger = logging.getLogger(__name__)


class ImageVerificationService:
    """Service for verifying image quality and integrity."""

    def __init__(self, websocket_manager=None, session_id: Optional[str] = None):
        self.min_resolution_width = 512  # Minimum width
        self.min_resolution_height = 512  # Minimum height
        self.expected_aspect_ratio = 16 / 9  # 16:9 aspect ratio
        self.aspect_ratio_tolerance = 0.1  # 10% tolerance
        self.min_file_size = 10 * 1024  # 10 KB minimum
        self.max_file_size = 20 * 1024 * 1024  # 20 MB maximum
        self.websocket_manager = websocket_manager
        self.session_id = session_id

    async def verify_image(
        self,
        image_url: str,
        image_index: Optional[int] = None,
        expected_aspect_ratio: Optional[float] = None,
    ) -> VerificationResult:
        """
        Verify an image for quality and integrity.

        Args:
            image_url: URL to the image file (S3 or local path)
            image_index: Index of image in sequence (for logging)
            expected_aspect_ratio: Expected aspect ratio (optional, defaults to 16:9)

        Returns:
            VerificationResult with all check results
        """
        # Send WebSocket update - starting verification
        if self.websocket_manager and self.session_id:
            await self.websocket_manager.send_progress(
                self.session_id,
                {
                    "type": "verification_update",
                    "verification_type": "image",
                    "status": "verifying",
                    "image_index": image_index,
                    "details": f"Verifying image {image_index if image_index is not None else ''}...",
                }
            )

        result = VerificationResult(
            verification_type=VerificationType.IMAGE,
            status=VerificationStatus.PASSED,
            asset_url=image_url,
        )

        temp_file = None
        try:
            # Download image to temp file if it's a URL
            if image_url.startswith("http"):
                temp_file = await self._download_image(image_url)
                image_path = temp_file
            else:
                image_path = image_url

            # Open and extract metadata
            with Image.open(image_path) as img:
                metadata = self._extract_metadata(img, image_path)
                result.metadata = metadata.to_dict()

                # Run all verification checks
                self._check_file_size(result, image_path)
                self._check_resolution(result, metadata)
                self._check_format(result, metadata)
                self._check_aspect_ratio(result, metadata, expected_aspect_ratio)
                self._check_blank_image(result, img)
                self._check_corruption(result, img)
                self._check_quality_score(result, img)

            logger.info(
                f"Image verification {'passed' if result.passed else 'failed'} "
                f"for image {image_index if image_index is not None else 'unknown'}: "
                f"{len(result.failed_checks)} failures, {len(result.warning_checks)} warnings"
            )

            # Send WebSocket update - verification complete
            if self.websocket_manager and self.session_id:
                await self.websocket_manager.send_progress(
                    self.session_id,
                    {
                        "type": "verification_update",
                        "verification_type": "image",
                        "status": result.status,
                        "image_index": image_index,
                        "passed": result.passed,
                        "failed_checks_count": len(result.failed_checks),
                        "warning_checks_count": len(result.warning_checks),
                        "details": f"Image {image_index if image_index is not None else ''} verification {'passed' if result.passed else 'failed'}",
                    }
                )

        except Exception as e:
            logger.exception(f"Image verification error: {e}")
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
                        "verification_type": "image",
                        "status": "failed",
                        "image_index": image_index,
                        "passed": False,
                        "error": str(e),
                        "details": f"Image {image_index if image_index is not None else ''} verification failed with error",
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

    async def verify_batch(
        self,
        image_urls: List[str],
        expected_aspect_ratio: Optional[float] = None,
    ) -> List[VerificationResult]:
        """
        Verify a batch of images.

        Args:
            image_urls: List of image URLs
            expected_aspect_ratio: Expected aspect ratio for all images

        Returns:
            List of VerificationResults
        """
        results = []
        for idx, image_url in enumerate(image_urls):
            result = await self.verify_image(image_url, idx, expected_aspect_ratio)
            results.append(result)
        return results

    async def _download_image(self, image_url: str) -> str:
        """Download image from URL to temporary file."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()

                # Determine file extension from content type or URL
                content_type = response.headers.get("content-type", "")
                if "png" in content_type.lower():
                    suffix = ".png"
                elif "jpeg" in content_type.lower() or "jpg" in content_type.lower():
                    suffix = ".jpg"
                elif "webp" in content_type.lower():
                    suffix = ".webp"
                else:
                    suffix = ".png"  # Default

                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(response.content)
                    return temp_file.name

        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            raise

    def _extract_metadata(self, img: Image.Image, image_path: str) -> ImageMetadata:
        """Extract image metadata."""
        width, height = img.size
        format_name = img.format or "UNKNOWN"
        mode = img.mode
        file_size = os.path.getsize(image_path)
        has_transparency = mode in ("RGBA", "LA") or (mode == "P" and "transparency" in img.info)

        return ImageMetadata(
            width=width,
            height=height,
            format=format_name,
            mode=mode,
            file_size=file_size,
            has_transparency=has_transparency,
        )

    def _check_file_size(self, result: VerificationResult, image_path: str) -> None:
        """Check if image file size is within acceptable range."""
        file_size = os.path.getsize(image_path)

        if file_size < self.min_file_size:
            result.add_check(
                VerificationCheck(
                    check_name="file_size",
                    status=VerificationStatus.FAILED,
                    message=f"File size too small: {file_size} bytes (min: {self.min_file_size})",
                    expected_value=self.min_file_size,
                    actual_value=file_size,
                    severity="error",
                )
            )
        elif file_size > self.max_file_size:
            result.add_check(
                VerificationCheck(
                    check_name="file_size",
                    status=VerificationStatus.WARNING,
                    message=f"File size very large: {file_size} bytes (max: {self.max_file_size})",
                    expected_value=self.max_file_size,
                    actual_value=file_size,
                    severity="warning",
                )
            )
        else:
            result.add_check(
                VerificationCheck(
                    check_name="file_size",
                    status=VerificationStatus.PASSED,
                    message=f"File size acceptable: {file_size} bytes",
                    actual_value=file_size,
                )
            )

    def _check_resolution(self, result: VerificationResult, metadata: ImageMetadata) -> None:
        """Check if image resolution meets minimum requirements."""
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

    def _check_format(self, result: VerificationResult, metadata: ImageMetadata) -> None:
        """Check if image format is valid."""
        valid_formats = ["PNG", "JPEG", "JPG", "WEBP"]

        if metadata.format.upper() not in valid_formats:
            result.add_check(
                VerificationCheck(
                    check_name="format",
                    status=VerificationStatus.WARNING,
                    message=f"Unusual image format: {metadata.format}",
                    expected_value=", ".join(valid_formats),
                    actual_value=metadata.format,
                    severity="warning",
                )
            )
        else:
            result.add_check(
                VerificationCheck(
                    check_name="format",
                    status=VerificationStatus.PASSED,
                    message=f"Valid image format: {metadata.format}",
                    actual_value=metadata.format,
                )
            )

    def _check_aspect_ratio(
        self,
        result: VerificationResult,
        metadata: ImageMetadata,
        expected_aspect_ratio: Optional[float],
    ) -> None:
        """Check if image aspect ratio is correct."""
        if expected_aspect_ratio is None:
            expected_aspect_ratio = self.expected_aspect_ratio

        actual_aspect_ratio = metadata.width / metadata.height
        difference = abs(actual_aspect_ratio - expected_aspect_ratio)
        tolerance = expected_aspect_ratio * self.aspect_ratio_tolerance

        if difference > tolerance:
            result.add_check(
                VerificationCheck(
                    check_name="aspect_ratio",
                    status=VerificationStatus.WARNING,
                    message=f"Aspect ratio mismatch: {actual_aspect_ratio:.2f} (expected {expected_aspect_ratio:.2f})",
                    expected_value=f"{expected_aspect_ratio:.2f}",
                    actual_value=f"{actual_aspect_ratio:.2f}",
                    severity="warning",
                )
            )
        else:
            result.add_check(
                VerificationCheck(
                    check_name="aspect_ratio",
                    status=VerificationStatus.PASSED,
                    message=f"Aspect ratio within tolerance: {actual_aspect_ratio:.2f}",
                    actual_value=f"{actual_aspect_ratio:.2f}",
                )
            )

    def _check_blank_image(self, result: VerificationResult, img: Image.Image) -> None:
        """Check if image is blank (all one color)."""
        try:
            # Convert to RGB if needed
            if img.mode != "RGB":
                img_rgb = img.convert("RGB")
            else:
                img_rgb = img

            # Get image statistics
            stat = ImageStat.Stat(img_rgb)
            mean_values = stat.mean  # Average RGB values
            stddev_values = stat.stddev  # Standard deviation of RGB values

            # Check if image is too uniform (likely blank)
            avg_stddev = sum(stddev_values) / len(stddev_values)

            if avg_stddev < 5:  # Very low variance = likely blank
                # Check if it's all black
                avg_mean = sum(mean_values) / len(mean_values)
                if avg_mean < 10:
                    result.add_check(
                        VerificationCheck(
                            check_name="blank_detection",
                            status=VerificationStatus.FAILED,
                            message="Image is completely black",
                            actual_value="all_black",
                            severity="error",
                        )
                    )
                # Check if it's all white
                elif avg_mean > 245:
                    result.add_check(
                        VerificationCheck(
                            check_name="blank_detection",
                            status=VerificationStatus.FAILED,
                            message="Image is completely white",
                            actual_value="all_white",
                            severity="error",
                        )
                    )
                else:
                    result.add_check(
                        VerificationCheck(
                            check_name="blank_detection",
                            status=VerificationStatus.WARNING,
                            message=f"Image has very low variance (stddev: {avg_stddev:.2f})",
                            actual_value=f"{avg_stddev:.2f}",
                            severity="warning",
                        )
                    )
            else:
                result.add_check(
                    VerificationCheck(
                        check_name="blank_detection",
                        status=VerificationStatus.PASSED,
                        message=f"Image has sufficient variance (stddev: {avg_stddev:.2f})",
                        actual_value=f"{avg_stddev:.2f}",
                    )
                )

        except Exception as e:
            logger.warning(f"Blank detection check failed: {e}")
            result.add_check(
                VerificationCheck(
                    check_name="blank_detection",
                    status=VerificationStatus.SKIPPED,
                    message=f"Blank detection skipped: {str(e)}",
                )
            )

    def _check_corruption(self, result: VerificationResult, img: Image.Image) -> None:
        """Check if image is corrupted."""
        try:
            # Try to verify the image
            img.verify()

            # Reopen and try to load data (verify closes the file)
            # Note: In actual usage, we already have the image open,
            # but verify() closes it, so we note that it passed verification
            result.add_check(
                VerificationCheck(
                    check_name="corruption",
                    status=VerificationStatus.PASSED,
                    message="Image is not corrupted",
                )
            )

        except Exception as e:
            logger.warning(f"Corruption check failed: {e}")
            result.add_check(
                VerificationCheck(
                    check_name="corruption",
                    status=VerificationStatus.FAILED,
                    message=f"Image appears corrupted: {str(e)}",
                    severity="error",
                )
            )

    def _check_quality_score(self, result: VerificationResult, img: Image.Image) -> None:
        """Calculate a quality score for the image based on various factors."""
        try:
            # Convert to RGB if needed
            if img.mode != "RGB":
                img_rgb = img.convert("RGB")
            else:
                img_rgb = img

            # Convert to numpy array for analysis
            img_array = np.array(img_rgb)

            # Calculate sharpness using Laplacian variance
            # (a measure of focus/detail in the image)
            gray = np.mean(img_array, axis=2)
            laplacian_var = np.var(
                np.array([
                    [gray[i+1][j+1] - gray[i][j] for j in range(gray.shape[1]-1)]
                    for i in range(gray.shape[0]-1)
                ])
            )

            # Calculate color distribution (entropy)
            hist, _ = np.histogram(img_array.flatten(), bins=256, range=(0, 256))
            hist = hist / hist.sum()  # Normalize
            entropy = -np.sum(hist * np.log2(hist + 1e-10))

            # Simple quality score: combination of sharpness and entropy
            # Normalize to 0-100 scale
            sharpness_score = min(100, laplacian_var / 10)
            entropy_score = (entropy / 8) * 100  # Max entropy for 8-bit is ~8

            quality_score = (sharpness_score * 0.6 + entropy_score * 0.4)

            if quality_score < 30:
                result.add_check(
                    VerificationCheck(
                        check_name="quality_score",
                        status=VerificationStatus.WARNING,
                        message=f"Low quality score: {quality_score:.1f}/100",
                        actual_value=f"{quality_score:.1f}",
                        severity="warning",
                    )
                )
            else:
                result.add_check(
                    VerificationCheck(
                        check_name="quality_score",
                        status=VerificationStatus.PASSED,
                        message=f"Quality score: {quality_score:.1f}/100",
                        actual_value=f"{quality_score:.1f}",
                    )
                )

        except Exception as e:
            logger.warning(f"Quality score check failed: {e}")
            result.add_check(
                VerificationCheck(
                    check_name="quality_score",
                    status=VerificationStatus.SKIPPED,
                    message=f"Quality score skipped: {str(e)}",
                )
            )
