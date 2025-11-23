"""
Verification models for quality checks on generated assets.

These models define the structure for verification results used throughout
the verification layer for both images and videos.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class VerificationStatus(str, Enum):
    """Status of a verification check."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class VerificationType(str, Enum):
    """Type of verification being performed."""
    VIDEO_CLIP = "video_clip"
    FINAL_VIDEO = "final_video"
    IMAGE = "image"
    AUDIO = "audio"


@dataclass
class VerificationCheck:
    """Individual verification check result."""
    check_name: str
    status: VerificationStatus
    message: str
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    severity: str = "info"  # info, warning, error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "message": self.message,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "severity": self.severity,
        }


@dataclass
class VerificationResult:
    """Result of a verification operation on an asset."""

    verification_type: VerificationType
    status: VerificationStatus
    asset_url: str
    checks: List[VerificationCheck] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    verified_at: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Whether verification passed."""
        return self.status == VerificationStatus.PASSED

    @property
    def failed(self) -> bool:
        """Whether verification failed."""
        return self.status == VerificationStatus.FAILED

    @property
    def has_warnings(self) -> bool:
        """Whether verification has warnings."""
        return any(check.status == VerificationStatus.WARNING for check in self.checks)

    @property
    def failed_checks(self) -> List[VerificationCheck]:
        """Get all failed checks."""
        return [check for check in self.checks if check.status == VerificationStatus.FAILED]

    @property
    def warning_checks(self) -> List[VerificationCheck]:
        """Get all warning checks."""
        return [check for check in self.checks if check.status == VerificationStatus.WARNING]

    def add_check(self, check: VerificationCheck) -> None:
        """Add a verification check to the result."""
        self.checks.append(check)

        # Update overall status based on check severity
        if check.status == VerificationStatus.FAILED and check.severity == "error":
            self.status = VerificationStatus.FAILED
        elif check.status == VerificationStatus.WARNING and self.status == VerificationStatus.PASSED:
            self.status = VerificationStatus.WARNING

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "verification_type": self.verification_type.value,
            "status": self.status.value,
            "asset_url": self.asset_url,
            "checks": [check.to_dict() for check in self.checks],
            "metadata": self.metadata,
            "verified_at": self.verified_at.isoformat(),
            "error_message": self.error_message,
            "has_warnings": self.has_warnings,
            "failed_checks_count": len(self.failed_checks),
            "warning_checks_count": len(self.warning_checks),
        }

    def __repr__(self) -> str:
        return (
            f"<VerificationResult(type={self.verification_type.value}, "
            f"status={self.status.value}, checks={len(self.checks)})>"
        )


@dataclass
class VideoMetadata:
    """Metadata extracted from a video file."""
    duration: float
    width: int
    height: int
    frame_count: int
    fps: float
    has_audio: bool
    audio_duration: Optional[float] = None
    codec: Optional[str] = None
    file_size: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "frame_count": self.frame_count,
            "fps": self.fps,
            "has_audio": self.has_audio,
            "audio_duration": self.audio_duration,
            "codec": self.codec,
            "file_size": self.file_size,
        }


@dataclass
class ImageMetadata:
    """Metadata extracted from an image file."""
    width: int
    height: int
    format: str
    mode: str  # RGB, RGBA, etc.
    file_size: int
    has_transparency: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "mode": self.mode,
            "file_size": self.file_size,
            "has_transparency": self.has_transparency,
        }
