"""Job Model - Represents a video generation job"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY,
    DECIMAL,
    Integer,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Job(Base):
    """Video generation job"""

    __tablename__ = "jobs"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # queued, processing, completed, failed

    # Input
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(10), nullable=False)
    brand_guidelines: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Progress
    current_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    stages_completed: Mapped[Optional[list]] = mapped_column(ARRAY(Text), nullable=True)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)

    # Intermediate Results
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    reference_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clip_urls: Mapped[Optional[list]] = mapped_column(ARRAY(Text), nullable=True)

    # Final Result
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Cost Tracking
    cost_prompt_parsing: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00")
    )
    cost_image_generation: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00")
    )
    cost_video_generation: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00")
    )
    cost_composition: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00")
    )
    cost_total: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal("0.00")
    )

    # Error
    error: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)

    def __repr__(self) -> str:
        return f"<Job {self.id} status={self.status}>"
