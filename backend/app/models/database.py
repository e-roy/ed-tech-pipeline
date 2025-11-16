"""
Database models for Gauntlet Pipeline.

Models based on DATABASE_SCHEMA.md specification.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Session(Base):
    """Session model for video generation workflow."""

    __tablename__ = "sessions"

    id = Column(String(255), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    # Possible statuses: pending, generating_images, images_approved,
    # generating_clips, clips_approved, composing, completed, failed

    # Prompts and configuration
    prompt = Column(Text, nullable=True)
    video_prompt = Column(Text, nullable=True)
    options = Column(JSON, nullable=True)  # Image generation options
    clip_config = Column(JSON, nullable=True)  # Video clip configuration
    text_config = Column(JSON, nullable=True)  # Text overlay configuration
    audio_config = Column(JSON, nullable=True)  # Audio configuration

    # Results
    final_video_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")
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


class Script(Base):
    """Script model for video generation."""

    __tablename__ = "scripts"

    id = Column(String(255), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Script structure with four parts
    # Each part has: {text: str, duration: str, key_concepts: list[str], visual_guidance: str}
    hook = Column(JSON, nullable=False)
    concept = Column(JSON, nullable=False)
    process = Column(JSON, nullable=False)
    conclusion = Column(JSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<Script(id={self.id}, user_id={self.user_id})>"


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
