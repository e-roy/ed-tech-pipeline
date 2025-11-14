"""Pydantic schemas for request/response validation"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
import re


# Request Schemas


class BrandGuidelines(BaseModel):
    """Brand guidelines for video generation"""

    primary_color: Optional[str] = Field(None, description="Primary brand color (hex)")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color (hex)")
    style: Optional[str] = Field(None, max_length=100, description="Brand style description")

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_hex_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate hex color format"""
        if v is None:
            return v
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("Color must be in hex format (#RRGGBB)")
        return v


class GenerateAdRequest(BaseModel):
    """Request to generate a video ad"""

    prompt: str = Field(..., min_length=10, max_length=500, description="Video prompt")
    duration: int = Field(..., ge=15, le=60, description="Video duration in seconds")
    aspect_ratio: str = Field(..., description="Video aspect ratio")
    brand_guidelines: Optional[BrandGuidelines] = None

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        """Validate aspect ratio is one of allowed values"""
        allowed = ["16:9", "9:16", "1:1"]
        if v not in allowed:
            raise ValueError(f"Aspect ratio must be one of {allowed}")
        return v


# Response Schemas


class ProgressResponse(BaseModel):
    """Progress information"""

    current_stage: Optional[str] = None
    stages_completed: list[str] = Field(default_factory=list)
    stages_remaining: list[str] = Field(default_factory=list)
    percentage: int = 0
    estimated_completion_time: Optional[datetime] = None


class CostBreakdown(BaseModel):
    """Cost breakdown by stage"""

    prompt_parsing: Decimal = Decimal("0.00")
    image_generation: Decimal = Decimal("0.00")
    video_generation: Decimal = Decimal("0.00")
    composition: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")


class VideoResult(BaseModel):
    """Final video result"""

    video_url: str
    thumbnail_url: str
    duration: int
    resolution: str
    file_size_mb: float
    scenes_generated: int


class ErrorDetails(BaseModel):
    """Error details"""

    code: str
    message: str
    failed_stage: Optional[str] = None
    details: Optional[dict] = None


class GenerateAdResponse(BaseModel):
    """Response after creating a video generation job"""

    job_id: UUID
    status: str
    created_at: datetime
    estimated_completion_time: Optional[datetime] = None


class JobStatusResponse(BaseModel):
    """Job status response"""

    job_id: UUID
    status: str
    progress: ProgressResponse
    cost: CostBreakdown
    result: Optional[VideoResult] = None
    error: Optional[ErrorDetails] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    service: str
    version: str
    database: str
    timestamp: datetime
