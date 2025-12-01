"""
Database models for Gauntlet Pipeline.

Models based on DATABASE_SCHEMA.md specification.

Architecture:
- Frontend video_session: Source of truth for content (topic, script, facts, learning objectives)
- Backend sessions: Source of truth for media production (video generation, music, assets, costs)
- Auth is handled by frontend's auth_user table (UUID string IDs)
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


# User model removed - auth is now handled by frontend's auth_user table
# See migration: c3d4e5f6g7h8_refactor_sessions_use_auth_user.py


class Session(Base):
    """
    Session model for video generation workflow (media production).

    This table tracks the media production pipeline:
    - Video generation status and progress
    - Music configuration
    - Final video output and verification
    - Associated assets and costs

    Content data (scripts, facts, learning objectives) lives in frontend's video_session table.
    User authentication is handled by frontend's auth_user table.
    """

    __tablename__ = "sessions"

    id = Column(String(255), primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)  # References auth_user.id (UUID string)
    status = Column(String(50), nullable=False, default="pending")
    # Possible statuses: pending, generating_images, images_approved,
    # generating_clips, clips_approved, composing, completed, failed

    # Music configuration (needed for media creation)
    music_track_id = Column(String(255), nullable=True)
    music_s3_url = Column(Text, nullable=True)
    music_volume = Column(Float, nullable=True, default=0.15)

    # Results
    final_video_url = Column(String(500), nullable=True)

    # Final video verification fields
    final_video_verification_status = Column(String(50), nullable=True)  # 'passed', 'failed', 'warning', 'skipped'
    final_video_verification_data = Column(JSON, nullable=True)  # Detailed verification check results
    final_video_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assets = relationship("Asset", back_populates="session", cascade="all, delete-orphan")
    costs = relationship("GenerationCost", back_populates="session", cascade="all, delete-orphan")
    websocket_connections = relationship("WebSocketConnection", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(id={self.id}, status={self.status})>"


class Asset(Base):
    """Asset model for generated images and video clips."""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("sessions.id"), nullable=False)
    type = Column(String(50), nullable=False)  # 'image' or 'clip'
    url = Column(String(500), nullable=False)
    approved = Column(Boolean, default=False)
    order_index = Column(Integer, nullable=True)  # For ordering clips

    # Metadata
    asset_metadata = Column(JSON, nullable=True)  # Additional info (dimensions, duration, etc.)

    # Verification fields
    verification_status = Column(String(50), nullable=True)  # 'passed', 'failed', 'warning', 'skipped'
    verification_data = Column(JSON, nullable=True)  # Detailed verification check results
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="assets")

    def __repr__(self):
        return f"<Asset(id={self.id}, type={self.type}, approved={self.approved})>"


class GenerationCost(Base):
    """Cost tracking for external services."""

    __tablename__ = "generation_costs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("sessions.id"), nullable=False)
    service = Column(String(100), nullable=False)  # 'replicate', 'openai', 's3', etc.
    cost = Column(Float, nullable=False, default=0.0)
    tokens_used = Column(Integer, nullable=True)  # For LLM services
    details = Column(JSON, nullable=True)  # Additional cost breakdown

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("Session", back_populates="costs")

    def __repr__(self):
        return f"<GenerationCost(id={self.id}, service={self.service}, cost={self.cost})>"


# Script model removed - now using video_session.generated_script column instead
# See migration: drop_scripts_table.py


class Template(Base):
    """Educational template for visual generation."""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # e.g., 'biology', 'astronomy', 'earth_science'
    keywords = Column(JSON, nullable=False)  # Array of keywords for matching
    psd_url = Column(String(500), nullable=True)  # URL to PSD file (if available)
    preview_url = Column(String(500), nullable=False)  # URL to preview PNG
    editable_layers = Column(JSON, nullable=True)  # Info about editable text layers

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Template(id={self.template_id}, name={self.name}, category={self.category})>"


class WebSocketConnection(Base):
    """Track active WebSocket connections for real-time updates."""

    __tablename__ = "websocket_connections"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("sessions.id"), nullable=False)
    connection_id = Column(String(255), unique=True, nullable=False)
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    disconnected_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="websocket_connections")

    def __repr__(self):
        return f"<WebSocketConnection(id={self.id}, session_id={self.session_id})>"


class MusicTrack(Base):
    """Music track library for background audio."""

    __tablename__ = "music_tracks"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # upbeat, calm, inspiring
    mood = Column(String(50), nullable=True)  # energetic, peaceful, motivational
    duration = Column(Integer, nullable=False)  # in seconds
    bpm = Column(Integer, nullable=True)  # beats per minute
    s3_url = Column(Text, nullable=False)
    license_type = Column(String(100), nullable=True)  # royalty_free, creative_commons, etc.
    attribution = Column(Text, nullable=True)
    suitable_for = Column(ARRAY(String(255)), nullable=True)  # ['science', 'math', 'general']

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MusicTrack(track_id={self.track_id}, name={self.name}, category={self.category})>"
