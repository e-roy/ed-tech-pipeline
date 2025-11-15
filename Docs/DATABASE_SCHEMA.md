# Database Schema Design
## AI Ad Video Generator - PostgreSQL Schema

**Version:** 1.0
**Date:** November 14, 2025
**Status:** Implementation-Ready

---

## Overview

This schema supports the multi-stage video generation pipeline with:
- Session state management across generation stages
- Asset tracking (images, videos, final outputs)
- Cost tracking per operation
- Mood board persistence (user selections)
- WebSocket connection mapping

**Design Principles:**
- JSONB for flexible metadata storage
- Enums for type safety
- Indexes on all foreign keys and query-heavy columns
- Timestamps for audit trails
- Soft deletes for data retention

---

## Entity Relationship Diagram

```
┌─────────────┐
│    users    │
└──────┬──────┘
       │
       │ 1:N
       ▼
┌─────────────────────────────────────────────┐
│              sessions                        │
│  - Tracks entire generation workflow state  │
└──────┬──────────────────────────────────────┘
       │
       │ 1:N
       ▼
┌─────────────────────────────────────────────┐
│               assets                         │
│  - Images, video clips, final videos        │
└──────┬──────────────────────────────────────┘
       │
       │ 1:N
       ▼
┌─────────────────────────────────────────────┐
│          generation_costs                    │
│  - Tracks cost per API call                 │
└─────────────────────────────────────────────┘
```

---

## Table Definitions

### 1. `users` Table

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- Soft delete
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Indexes
    CONSTRAINT users_email_unique UNIQUE(email)
);

CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_created_at ON users(created_at DESC);
```

**Notes:**
- For MVP, only demo user exists
- Password hashing uses bcrypt
- `deleted_at` enables soft deletes

---

### 2. `sessions` Table

**Core state management for entire generation workflow**

```sql
-- Custom ENUMs for type safety
CREATE TYPE session_status AS ENUM (
    'created',              -- Session initialized
    'prompting',            -- User entering prompts
    'generating_images',    -- Image generation in progress
    'reviewing_images',     -- User selecting images
    'generating_videos',    -- Video generation in progress
    'reviewing_videos',     -- User selecting video clips
    'composing',            -- Final video composition
    'completed',            -- Final video ready
    'failed',               -- Generation failed
    'cancelled'             -- User cancelled
);

CREATE TYPE product_category AS ENUM (
    'footwear',
    'accessories',
    'electronics',
    'beauty',
    'apparel',
    'home',
    'other'
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Status tracking
    status session_status NOT NULL DEFAULT 'created',
    current_stage VARCHAR(50), -- 'prompt_parsing', 'image_gen', 'video_gen', 'composition'
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

    -- Product information
    product_category product_category,
    user_product_prompt TEXT,
    user_video_prompt TEXT,

    -- Generation parameters (from Prompt Parser Agent)
    consistency_seed INTEGER,
    style_keywords TEXT[], -- Array of keywords

    -- Asset tracking (references to assets table)
    generated_image_ids UUID[] DEFAULT '{}',
    approved_image_ids UUID[] DEFAULT '{}',
    generated_clip_ids UUID[] DEFAULT '{}',
    approved_clip_ids UUID[] DEFAULT '{}',
    final_video_id UUID,

    -- Text overlay configuration
    product_name VARCHAR(100),
    call_to_action VARCHAR(100),
    text_color VARCHAR(7), -- Hex color code
    text_font VARCHAR(50),

    -- Audio configuration
    background_music_enabled BOOLEAN DEFAULT FALSE,
    music_genre VARCHAR(50),
    music_url TEXT,

    -- Cost tracking
    total_cost DECIMAL(10, 4) DEFAULT 0.00,
    estimated_cost DECIMAL(10, 4),

    -- Generation settings
    num_images_requested INTEGER DEFAULT 6,
    clip_duration_seconds DECIMAL(4, 2) DEFAULT 3.0,

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Metadata (flexible JSONB for future additions)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX idx_sessions_user_id ON sessions(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_status ON sessions(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_sessions_updated_at ON sessions(updated_at DESC);
CREATE INDEX idx_sessions_product_category ON sessions(product_category);

-- GIN index for array searches
CREATE INDEX idx_sessions_approved_image_ids ON sessions USING GIN(approved_image_ids);
CREATE INDEX idx_sessions_approved_clip_ids ON sessions USING GIN(approved_clip_ids);
CREATE INDEX idx_sessions_style_keywords ON sessions USING GIN(style_keywords);

-- JSONB index for metadata queries
CREATE INDEX idx_sessions_metadata ON sessions USING GIN(metadata);
```

**Key Features:**
- `UUID` primary key for session IDs (used in WebSocket connections)
- Status enum tracks workflow progression
- Arrays store asset IDs for mood board functionality
- JSONB metadata for extensibility
- Comprehensive indexing for real-time queries

---

### 3. `assets` Table

**Stores all generated content (images, video clips, final videos)**

```sql
CREATE TYPE asset_type AS ENUM (
    'image',           -- Generated product image
    'video_clip',      -- Individual video clip
    'final_video',     -- Composed final video
    'audio'            -- Background music
);

CREATE TYPE asset_source AS ENUM (
    'flux-pro',
    'sdxl',
    'stable-video-diffusion',
    'runway-gen2',
    'musicgen',
    'ffmpeg',
    'user-upload'
);

CREATE TYPE asset_status AS ENUM (
    'generating',      -- API call in progress
    'completed',       -- Successfully generated
    'failed',          -- Generation failed
    'approved',        -- User approved in mood board
    'rejected'         -- User rejected
);

CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,

    -- Asset classification
    type asset_type NOT NULL,
    source asset_source NOT NULL,
    status asset_status NOT NULL DEFAULT 'generating',

    -- File information
    url TEXT NOT NULL,
    storage_path TEXT, -- Path in S3/R2
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),

    -- Asset properties
    resolution VARCHAR(20), -- e.g., "1024x1024", "1920x1080"
    duration_seconds DECIMAL(6, 3), -- For videos/audio
    fps INTEGER, -- For videos

    -- Generation metadata
    generation_cost DECIMAL(10, 4) DEFAULT 0.00,
    generation_time_seconds DECIMAL(8, 2),
    model_version VARCHAR(100),

    -- Image-specific fields
    view_type VARCHAR(50), -- 'front', 'side', 'back', 'detail', 'lifestyle'
    seed INTEGER, -- Consistency seed used
    guidance_scale DECIMAL(4, 2),

    -- Video-specific fields
    source_image_id UUID REFERENCES assets(id), -- For video clips generated from images
    scene_prompt TEXT,
    camera_movement VARCHAR(50),
    motion_intensity DECIMAL(3, 2),

    -- Prompt information
    generation_prompt TEXT,
    negative_prompt TEXT,

    -- User interaction
    user_selected BOOLEAN DEFAULT FALSE,
    selection_order INTEGER, -- Order in mood board

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Flexible metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_assets_session_id ON assets(session_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_assets_type ON assets(type) WHERE deleted_at IS NULL;
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_source ON assets(source);
CREATE INDEX idx_assets_user_selected ON assets(user_selected) WHERE user_selected = TRUE;
CREATE INDEX idx_assets_created_at ON assets(created_at DESC);
CREATE INDEX idx_assets_source_image_id ON assets(source_image_id) WHERE source_image_id IS NOT NULL;

-- GIN index for JSONB
CREATE INDEX idx_assets_metadata ON assets USING GIN(metadata);
```

**Key Features:**
- Single table for all asset types (images, clips, final videos)
- Tracks generation source and cost
- `source_image_id` links video clips to their source images
- `user_selected` and `selection_order` support mood board
- Comprehensive metadata for debugging

---

### 4. `generation_costs` Table

**Detailed cost tracking per API call**

```sql
CREATE TYPE cost_category AS ENUM (
    'llm',              -- Prompt parsing (Llama 3.1)
    'image_generation', -- Flux-Pro, SDXL
    'video_generation', -- Stable Video Diffusion, Runway
    'audio_generation', -- MusicGen
    'composition',      -- FFmpeg processing
    'storage',          -- S3/R2 costs
    'other'
);

CREATE TABLE generation_costs (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    asset_id UUID REFERENCES assets(id) ON DELETE SET NULL,

    -- Cost details
    category cost_category NOT NULL,
    amount DECIMAL(10, 4) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',

    -- API details
    provider VARCHAR(50), -- 'replicate', 'openai', 'aws'
    model_name VARCHAR(100),
    api_call_id VARCHAR(255), -- External API transaction ID

    -- Usage metrics
    tokens_used INTEGER, -- For LLM calls
    seconds_processed DECIMAL(8, 2), -- For video/audio
    api_latency_ms INTEGER,

    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_generation_costs_session_id ON generation_costs(session_id);
CREATE INDEX idx_generation_costs_asset_id ON generation_costs(asset_id);
CREATE INDEX idx_generation_costs_category ON generation_costs(category);
CREATE INDEX idx_generation_costs_created_at ON generation_costs(created_at DESC);
CREATE INDEX idx_generation_costs_provider ON generation_costs(provider);
```

**Key Features:**
- Granular tracking of every API call cost
- Links to both session and specific asset
- Tracks API performance metrics
- Enables cost analytics and budget monitoring

---

### 5. `websocket_connections` Table

**Tracks active WebSocket connections for progress updates**

```sql
CREATE TABLE websocket_connections (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    connection_id VARCHAR(255) UNIQUE NOT NULL, -- WebSocket connection identifier

    -- Connection info
    client_ip VARCHAR(45),
    user_agent TEXT,

    -- Status
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_heartbeat_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    disconnected_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes
CREATE INDEX idx_websocket_session_id ON websocket_connections(session_id);
CREATE INDEX idx_websocket_connection_id ON websocket_connections(connection_id);
CREATE INDEX idx_websocket_active ON websocket_connections(session_id)
    WHERE disconnected_at IS NULL;
```

**Key Features:**
- Maps WebSocket connections to sessions
- Heartbeat tracking for connection health
- Supports multiple tabs (multiple connections per session)

---

## Database Functions & Triggers

### Auto-update `updated_at` timestamp

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Auto-calculate session total cost

```sql
CREATE OR REPLACE FUNCTION calculate_session_total_cost()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sessions
    SET total_cost = (
        SELECT COALESCE(SUM(amount), 0)
        FROM generation_costs
        WHERE session_id = NEW.session_id
    )
    WHERE id = NEW.session_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_session_cost
    AFTER INSERT OR UPDATE ON generation_costs
    FOR EACH ROW
    EXECUTE FUNCTION calculate_session_total_cost();
```

---

## Sample Queries

### Get session with all assets

```sql
SELECT
    s.*,
    (
        SELECT json_agg(a.* ORDER BY a.created_at)
        FROM assets a
        WHERE a.session_id = s.id AND a.type = 'image'
    ) AS images,
    (
        SELECT json_agg(a.* ORDER BY a.created_at)
        FROM assets a
        WHERE a.session_id = s.id AND a.type = 'video_clip'
    ) AS video_clips,
    (
        SELECT json_agg(a.*)
        FROM assets a
        WHERE a.session_id = s.id AND a.type = 'final_video'
    ) AS final_video
FROM sessions s
WHERE s.id = $1;
```

### Get mood board (approved assets)

```sql
SELECT
    a.*
FROM assets a
WHERE
    a.session_id = $1
    AND a.user_selected = TRUE
    AND a.deleted_at IS NULL
ORDER BY a.selection_order ASC, a.created_at ASC;
```

### Get cost breakdown for session

```sql
SELECT
    gc.category,
    gc.provider,
    COUNT(*) AS api_calls,
    SUM(gc.amount) AS total_cost,
    AVG(gc.api_latency_ms) AS avg_latency_ms
FROM generation_costs gc
WHERE gc.session_id = $1
GROUP BY gc.category, gc.provider
ORDER BY total_cost DESC;
```

### Get active sessions for user

```sql
SELECT
    s.*,
    COUNT(DISTINCT a.id) FILTER (WHERE a.type = 'image') AS image_count,
    COUNT(DISTINCT a.id) FILTER (WHERE a.type = 'video_clip') AS clip_count
FROM sessions s
LEFT JOIN assets a ON a.session_id = s.id
WHERE
    s.user_id = $1
    AND s.status != 'completed'
    AND s.deleted_at IS NULL
GROUP BY s.id
ORDER BY s.updated_at DESC;
```

---

## Migration Strategy

### Initial Migration (Alembic)

```python
# alembic/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

def upgrade():
    # Create ENUMs
    op.execute("CREATE TYPE session_status AS ENUM ('created', 'prompting', 'generating_images', 'reviewing_images', 'generating_videos', 'reviewing_videos', 'composing', 'completed', 'failed', 'cancelled')")
    # ... (create all ENUMs)

    # Create tables in order (users → sessions → assets → generation_costs)
    op.create_table('users', ...)
    op.create_table('sessions', ...)
    op.create_table('assets', ...)
    op.create_table('generation_costs', ...)
    op.create_table('websocket_connections', ...)

    # Create indexes
    op.create_index(...)

    # Create triggers
    op.execute("""CREATE OR REPLACE FUNCTION update_updated_at_column() ...""")
    op.execute("""CREATE TRIGGER update_users_updated_at ...""")

def downgrade():
    # Drop in reverse order
    op.drop_table('websocket_connections')
    op.drop_table('generation_costs')
    op.drop_table('assets')
    op.drop_table('sessions')
    op.drop_table('users')

    # Drop ENUMs
    op.execute("DROP TYPE IF EXISTS session_status CASCADE")
```

### Seed Demo User

```sql
-- Demo user for MVP
INSERT INTO users (email, password_hash, full_name)
VALUES (
    'demo@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdQmJq5rMJHvQJJwe', -- bcrypt hash of 'demo123'
    'Demo User'
);
```

---

## Performance Considerations

### Expected Load (MVP)
- Concurrent users: 1-10
- Sessions per day: 50-100
- Assets per session: ~15 (6 images + 6 clips + 1 final video)
- Database size growth: ~500 MB/month

### Scaling Recommendations (Post-MVP)
1. **Connection Pooling:** Use pgBouncer for connection management
2. **Partitioning:** Partition `generation_costs` by `created_at` (monthly)
3. **Archival:** Move completed sessions older than 30 days to cold storage
4. **Read Replicas:** Add read replica for analytics queries

---

## Security Notes

1. **Row-Level Security (RLS):** Consider enabling for multi-tenant scenarios
2. **Encrypted Fields:** Store `password_hash` with bcrypt (cost factor 12)
3. **API Keys:** Never store Replicate/AWS keys in database (use environment variables)
4. **Soft Deletes:** Enable audit trail, comply with data retention policies

---

## SQLAlchemy Models (Python)

See `backend/models/database.py` for ORM implementation:

```python
from sqlalchemy import Column, Integer, String, ARRAY, DECIMAL, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(Enum(SessionStatus), nullable=False, default='created')
    # ... (remaining columns)
```

---

## Testing Data

### Test Session Flow

```sql
-- 1. Create test session
INSERT INTO sessions (user_id, status, user_product_prompt, product_category)
VALUES (1, 'generating_images', 'pink tennis shoes', 'footwear')
RETURNING id;

-- 2. Create test image assets
INSERT INTO assets (session_id, type, source, status, url, view_type, seed, generation_cost)
VALUES
    ('session-uuid-here', 'image', 'flux-pro', 'completed', 'https://...', 'front', 789456, 0.05),
    ('session-uuid-here', 'image', 'flux-pro', 'completed', 'https://...', 'side', 789456, 0.05);

-- 3. Approve images
UPDATE assets
SET user_selected = TRUE, selection_order = 1
WHERE id = 'asset-uuid-1';
```

---

**Next Steps:**
1. Review schema with backend team
2. Run migration on Railway PostgreSQL
3. Implement SQLAlchemy models
4. Write integration tests for critical queries

**Schema Status:** ✅ Ready for Implementation
