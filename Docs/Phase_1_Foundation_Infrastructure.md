# Phase 1: Foundation & Infrastructure Setup

## Document Purpose
This phase establishes the foundational infrastructure including database setup, data models, API framework, authentication, and session management.

**Estimated Time:** 6 hours (Hour 0-6 of 48-hour sprint)

---

## 1. Project Initialization

### 1.1 Repository Structure

```
pipeline/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── database.py      # SQLAlchemy models
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── prompt_parser.py
│   │   │   ├── image_generator.py
│   │   │   ├── video_generator.py
│   │   │   └── compositor.py
│   │   ├── orchestrator/
│   │   │   ├── __init__.py
│   │   │   └── video_orchestrator.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── sessions.py
│   │   │   ├── generation.py
│   │   │   └── websocket.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── database_service.py
│   │       ├── storage_service.py
│   │       └── websocket_manager.py
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── test_agents.py
│   │   ├── test_integration.py
│   │   └── test_e2e.py
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── dashboard/
│   │   ├── generate/
│   │   └── result/
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── .env.local.example
├── Docs/
│   ├── MVP_PRD.md
│   ├── Phase_0_Overview_Architecture.md
│   ├── Phase_1_Foundation_Infrastructure.md
│   └── ...
└── README.md
```

### 1.2 Backend Requirements (requirements.txt)

```txt
# FastAPI Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Pydantic
pydantic==2.5.0
pydantic-settings==2.1.0

# API Clients
replicate==0.22.0
httpx==0.25.1

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0

# WebSocket
websockets==12.0

# Utilities
python-multipart==0.0.6
aiofiles==23.2.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1

# Code Quality
black==23.11.0
ruff==0.1.6
mypy==1.7.1
```

### 1.3 Frontend Dependencies (package.json)

```json
{
  "name": "ai-ad-video-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.3",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.3.2",
    "@tanstack/react-query": "^5.8.4",
    "axios": "^1.6.2",
    "zustand": "^4.4.7",
    "tailwindcss": "^3.3.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.41",
    "@types/react-dom": "^18.2.17",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "eslint": "^8.54.0",
    "eslint-config-next": "14.0.3"
  }
}
```

### 1.4 Environment Variables

**Backend (.env.example)**

```bash
# API Keys
REPLICATE_API_KEY=r8_xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_ad_video_db

# Storage (S3 or Cloudflare R2)
AWS_ACCESS_KEY_ID=xxxxxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxx
S3_BUCKET_NAME=ai-ad-videos
S3_REGION=us-east-1

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# CORS
FRONTEND_URL=http://localhost:3000

# Environment
ENV=development  # or 'production'

# Server
HOST=0.0.0.0
PORT=8000
```

**Frontend (.env.local.example)**

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 2. Database Setup

### 2.1 PostgreSQL Installation & Setup

**Local Development (macOS):**

```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database
createdb ai_ad_video_db

# Create user (optional)
psql ai_ad_video_db
CREATE USER ai_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_ad_video_db TO ai_user;
```

**Production (Railway):**

1. Go to [railway.app](https://railway.app)
2. Create new project
3. Add PostgreSQL service
4. Copy connection string to `DATABASE_URL`

### 2.2 SQLAlchemy Models (models/database.py)

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from enum import Enum

Base = declarative_base()

class SessionStage(str, Enum):
    CREATED = "created"
    IMAGE_GENERATION = "image_generation"
    IMAGE_SELECTION = "image_selection"
    CLIP_GENERATION = "clip_generation"
    CLIP_SELECTION = "clip_selection"
    FINAL_COMPOSITION = "final_composition"
    COMPLETE = "complete"
    FAILED = "failed"

class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FINAL_VIDEO = "final_video"

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, default=1)  # Demo user for MVP
    stage = Column(SQLEnum(SessionStage), nullable=False, default=SessionStage.CREATED)

    # Prompts
    product_prompt = Column(String(200), nullable=True)
    video_prompt = Column(String(300), nullable=True)

    # Generation metadata
    consistency_seed = Column(Integer, nullable=True)
    style_keywords = Column(JSON, nullable=True)  # Array of strings

    # Asset references (JSON arrays of IDs)
    generated_image_ids = Column(JSON, default=[])
    approved_image_ids = Column(JSON, default=[])
    generated_clip_ids = Column(JSON, default=[])
    approved_clip_ids = Column(JSON, default=[])
    clip_order = Column(JSON, default=[])  # Ordered list of clip IDs
    final_video_id = Column(String(36), nullable=True)

    # Cost tracking
    total_cost = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False)

    # Asset data
    url = Column(String(500), nullable=False)
    metadata = Column(JSON, nullable=True)  # Flexible metadata storage

    # Cost tracking
    cost = Column(Float, nullable=False, default=0.0)
    model_used = Column(String(100), nullable=True)
    generation_time = Column(Float, nullable=True)  # seconds

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GenerationCost(Base):
    __tablename__ = "generation_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)
    model_used = Column(String(100), nullable=False)
    cost_usd = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 2.3 Pydantic Models (models/schemas.py)

```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum
from typing import Optional

class SessionStage(str, Enum):
    CREATED = "created"
    IMAGE_GENERATION = "image_generation"
    IMAGE_SELECTION = "image_selection"
    CLIP_GENERATION = "clip_generation"
    CLIP_SELECTION = "clip_selection"
    FINAL_COMPOSITION = "final_composition"
    COMPLETE = "complete"
    FAILED = "failed"

class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FINAL_VIDEO = "final_video"

# ==================== AGENT MODELS ====================

class AgentInput(BaseModel):
    """Base input model for all agents"""
    session_id: str
    data: dict
    metadata: dict = {}

class AgentOutput(BaseModel):
    """Base output model for all agents"""
    success: bool
    data: dict
    cost: float  # USD
    duration: float  # seconds
    error: Optional[str] = None

# ==================== REQUEST MODELS ====================

class LoginRequest(BaseModel):
    email: str
    password: str

class CreateSessionRequest(BaseModel):
    user_id: int = 1

class GenerateImagesRequest(BaseModel):
    session_id: str
    product_prompt: str = Field(..., min_length=3, max_length=200)
    num_images: int = Field(default=6, ge=4, le=8)
    style_keywords: list[str] = Field(default_factory=list)

class SaveApprovedImagesRequest(BaseModel):
    session_id: str
    approved_image_ids: list[str] = Field(..., min_items=2)

class GenerateClipsRequest(BaseModel):
    session_id: str
    video_prompt: str = Field(..., min_length=10, max_length=300)
    clip_duration: float = Field(default=3.0, ge=2.0, le=4.0)

class SaveApprovedClipsRequest(BaseModel):
    session_id: str
    approved_clip_ids: list[str]
    clip_order: list[str]  # Order of clips in final video

class TextOverlay(BaseModel):
    product_name: str = Field(..., max_length=50)
    cta: str = Field(..., max_length=30)
    font: str = Field(default="Montserrat-Bold")
    color: str = Field(default="#FFFFFF")

class AudioConfig(BaseModel):
    enabled: bool = Field(default=False)
    genre: str = Field(default="upbeat")

class ComposeFinalVideoRequest(BaseModel):
    session_id: str
    text_overlay: TextOverlay
    audio: AudioConfig = Field(default_factory=AudioConfig)
    intro_duration: float = Field(default=1.0)
    outro_duration: float = Field(default=1.0)

# ==================== RESPONSE MODELS ====================

class LoginResponse(BaseModel):
    success: bool
    user_id: int
    email: str
    session_token: str

class ImageAsset(BaseModel):
    id: str
    url: str
    view_type: str
    seed: int
    cost: float
    created_at: datetime

class VideoAsset(BaseModel):
    id: str
    url: str
    source_image_id: str
    duration: float
    resolution: str
    fps: int
    cost: float
    created_at: datetime

class FinalVideo(BaseModel):
    url: str
    duration: float
    resolution: str
    fps: int
    file_size_mb: float
    format: str

class SessionResponse(BaseModel):
    id: str
    user_id: int
    stage: SessionStage
    product_prompt: Optional[str]
    video_prompt: Optional[str]
    consistency_seed: Optional[int]
    generated_images: list[ImageAsset]
    approved_images: list[str]  # Image IDs
    generated_clips: list[VideoAsset]
    approved_clips: list[str]  # Clip IDs
    final_video: Optional[FinalVideo]
    total_cost: float
    created_at: datetime
    updated_at: datetime

class ProgressUpdate(BaseModel):
    session_id: str
    stage: str
    progress: int  # 0-100
    message: str
    current_cost: Optional[float] = None
    timestamp: datetime
```

### 2.4 Database Connection (database.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.config import settings
from app.models.database import Base

# Sync engine for migrations
sync_engine = create_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql://"))

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.ENV == "development",
    pool_size=20,
    max_overflow=40
)

# Session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Create all tables (for development)
def init_db():
    Base.metadata.create_all(bind=sync_engine)
```

### 2.5 Alembic Setup (Migration Tool)

**Initialize Alembic:**

```bash
cd backend
alembic init alembic
```

**Configure alembic.ini:**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://user:password@localhost:5432/ai_ad_video_db
```

**Create initial migration:**

```bash
alembic revision --autogenerate -m "Initial tables"
alembic upgrade head
```

**Seed demo user:**

```sql
-- Run in psql or pgAdmin
INSERT INTO users (email, password_hash) VALUES
('demo@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqaC.U0F1Jya');
-- Password: demo123 (hashed with bcrypt)
```

---

## 3. FastAPI Application Setup

### 3.1 Configuration (config.py)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    REPLICATE_API_KEY: str

    # Database
    DATABASE_URL: str

    # Storage
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    S3_REGION: str = "us-east-1"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Environment
    ENV: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### 3.2 Main Application (main.py)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import auth, sessions, generation, websocket

# Initialize FastAPI app
app = FastAPI(
    title="AI Ad Video Generator API",
    version="1.0.0",
    description="Multi-agent AI system for generating product advertisement videos"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(generation.router, prefix="/api", tags=["Generation"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    if settings.ENV == "development":
        init_db()
    print(f"🚀 Server started on {settings.HOST}:{settings.PORT}")
    print(f"📊 Environment: {settings.ENV}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV == "development"
    )
```

---

## 4. Authentication & Session Management

### 4.1 Authentication Router (routers/auth.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.database import get_db
from app.models.database import User
from app.models.schemas import LoginRequest, LoginResponse
from app.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Demo authentication endpoint
    Accepts demo@example.com / demo123
    """
    # Query user
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Verify password
    if not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return LoginResponse(
        success=True,
        user_id=user.id,
        email=user.email,
        session_token=access_token
    )
```

### 4.2 Session Router (routers/sessions.py)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.database import Session as DBSession, SessionStage
from app.models.schemas import CreateSessionRequest, SessionResponse
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/create")
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new generation session"""
    session_id = str(uuid.uuid4())

    new_session = DBSession(
        id=session_id,
        user_id=request.user_id,
        stage=SessionStage.CREATED
    )

    db.add(new_session)
    await db.commit()

    return {
        "session_id": session_id,
        "stage": SessionStage.CREATED,
        "created_at": datetime.utcnow()
    }

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get session details"""
    result = await db.execute(select(DBSession).where(DBSession.id == session_id))
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # TODO: Populate with assets from database
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        stage=session.stage,
        product_prompt=session.product_prompt,
        video_prompt=session.video_prompt,
        consistency_seed=session.consistency_seed,
        generated_images=[],  # Will be populated in Phase 2
        approved_images=session.approved_image_ids or [],
        generated_clips=[],   # Will be populated in Phase 3
        approved_clips=session.approved_clip_ids or [],
        final_video=None,
        total_cost=session.total_cost,
        created_at=session.created_at,
        updated_at=session.updated_at
    )
```

---

## 5. WebSocket Manager

### 5.1 WebSocket Service (services/websocket_manager.py)

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
import json
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"✅ WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"❌ WebSocket disconnected: {session_id}")

    async def send_progress(self, session_id: str, data: dict):
        """Send progress update to client"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                # Add timestamp if not present
                if "timestamp" not in data:
                    data["timestamp"] = datetime.utcnow().isoformat()

                await websocket.send_json(data)
                print(f"📤 Progress sent to {session_id}: {data.get('message', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error sending progress: {e}")
                self.disconnect(session_id)

    async def broadcast(self, data: dict):
        """Broadcast message to all connected clients"""
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(data)
            except Exception:
                self.disconnect(session_id)

# Global instance
ws_manager = WebSocketManager()
```

### 5.2 WebSocket Router (routers/websocket.py)

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import ws_manager

router = APIRouter()

@router.websocket("/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time progress updates

    Client connects to: ws://localhost:8000/ws/{session_id}
    """
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            # Keep connection alive
            # Client can send ping messages if needed
            data = await websocket.receive_text()

            # Optional: Handle client messages
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
```

---

## 6. Testing Foundation

### 6.1 Test Database Connection

```python
# tests/test_database.py
import pytest
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.database import User

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "demo@example.com"
```

### 6.2 Test Authentication

```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login_success():
    """Test successful login"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "demo@example.com", "password": "demo123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_token" in data

@pytest.mark.asyncio
async def test_login_failure():
    """Test failed login"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": "demo@example.com", "password": "wrong"}
        )
        assert response.status_code == 401
```

---

## 7. Deployment Checklist

### 7.1 Local Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local
npm run dev
```

### 7.2 Verify Setup

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Database connected (check `/health` endpoint)
- [ ] Login works with demo credentials
- [ ] Session creation works
- [ ] WebSocket connection works

---

## 8. Next Steps

**Phase 1 Complete! ✅**

You should now have:
- ✅ Backend FastAPI application running
- ✅ PostgreSQL database with migrations
- ✅ Pydantic models for request/response validation
- ✅ Authentication system (demo login)
- ✅ Session management endpoints
- ✅ WebSocket infrastructure
- ✅ Frontend Next.js scaffold (basic setup)

**Proceed to:** [Phase_2_Core_Agents.md](Phase_2_Core_Agents.md)

---

## Document Metadata

- **Phase:** 1 (Foundation & Infrastructure)
- **Dependencies:** Phase 0 (reviewed)
- **Next Phase:** Phase 2 (Core Agent Implementation)
- **Estimated Duration:** 6 hours
- **Last Updated:** November 14, 2025
