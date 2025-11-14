# Architecture Document: AI Video Generation Orchestrator

## Overview
**Project Name**: AI Video Generation Orchestrator
**Version**: 1.0.0-MVP
**Date**: November 14, 2025
**Architect**: Winston (System Architect)
**Competition**: Gauntlet AI Video Generation Challenge

### Description
A FastAPI-based orchestration service that coordinates 4 microservices to generate AI-powered video advertisements from text prompts. The orchestrator manages job lifecycle, tracks costs in real-time, provides progress updates, and ensures reliable delivery of 15-60 second video ads with sub-$2 cost targets.

**Key Characteristics**:
- Async job processing with database-backed state machine
- Real-time progress tracking with granular cost breakdown
- Parallel video generation with visual consistency guarantees
- Resilient error handling with retry logic
- Production-ready observability and monitoring

---

## System Architecture

**Architecture Style**: Microservices with Central Orchestrator

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                      │
│                    [Separate Repository]                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST (Polling)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              AI VIDEO GENERATION ORCHESTRATOR               │
│                                                              │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   FastAPI    │  │ Background  │  │   PostgreSQL     │   │
│  │  REST API    │→ │   Tasks     │→ │   Database       │   │
│  └──────────────┘  └─────────────┘  └──────────────────┘   │
│         │                  │                                │
│         └──────────┬───────┴──────────────────────────────┐ │
│                    ▼                                       │ │
│         ┌──────────────────────────┐                       │ │
│         │  Orchestration Engine    │                       │ │
│         │  • State Machine         │                       │ │
│         │  • Cost Tracking         │                       │ │
│         │  • Progress Updates      │                       │ │
│         │  • Retry Logic           │                       │ │
│         └──────┬───────────────────┘                       │ │
│                │                                            │ │
│       ┌────────┼──────────┬─────────────┬─────────────┐    │ │
│       ▼        ▼          ▼             ▼             ▼    │ │
│  ┌────────┐ ┌─────┐  ┌────────┐  ┌──────────────┐ ┌────┐  │ │
│  │Prompt  │ │Image│  │Video   │  │  Composition │ │ S3 │  │ │
│  │Client  │ │Gen  │  │Gen     │  │  Client      │ │URL │  │ │
│  │(httpx) │ │Clnt │  │Client  │  │  (httpx)     │ │Ref │  │ │
│  └───┬────┘ └──┬──┘  └───┬────┘  └──────┬───────┘ └────┘  │ │
└──────┼─────────┼─────────┼───────────────┼─────────────────┘ │
       │         │         │               │                    │
       ▼         ▼         ▼               ▼                    │
┌──────────┐ ┌──────┐ ┌─────────┐ ┌────────────────┐           │
│ Prompt   │ │Image │ │ Video   │ │  Composition   │           │
│ Parser   │ │ Gen  │ │ Gen     │ │  Service       │           │
│ Service  │ │Service│ │Service  │ │  (FFmpeg)      │           │
└──────────┘ └──────┘ └─────────┘ └────────────────┘           │
   8001        8002       8003           8004                   │
                                                                │
                            ▼                                   │
                   ┌──────────────────┐                         │
                   │   AWS S3         │                         │
                   │  Video Storage   │                         │
                   └──────────────────┘                         │
```

**Architecture Pattern**: **Orchestrator/Coordinator Pattern**
- Central service coordinates distributed microservices
- Async communication via HTTP (REST)
- Database as source of truth for job state
- Background task processing with FastAPI BackgroundTasks

---

## Components

### 1. API Layer (`app/api/`)

**Purpose**: REST API interface for frontend and external clients

**Technology**: FastAPI with Pydantic validation

**Responsibilities**:
- Accept video generation requests (`POST /api/v1/generate-ad`)
- Provide job status endpoints (`GET /api/v1/jobs/{id}`)
- Health check endpoint (`GET /health`)
- Request validation and serialization
- Error response formatting

**Interfaces**:
- **Input**: HTTP REST requests (JSON)
- **Output**: HTTP responses with standardized JSON format
- **Triggers**: Background task for job processing

**Key Files**:
- `app/api/routes.py` - Endpoint definitions
- `app/api/schemas.py` - Pydantic request/response models
- `app/api/middleware.py` - Error handling, CORS, logging

---

### 2. Orchestration Engine (`app/core/orchestrator.py`)

**Purpose**: Main pipeline execution logic and state management

**Technology**: Async Python with asyncio

**Responsibilities**:
- Execute 4-stage pipeline sequentially
- Manage job state transitions (queued → processing → completed/failed)
- Update progress percentage after each stage
- Aggregate costs from all services
- Handle errors and trigger retries
- Store intermediate results (parsed data, reference image, clip URLs)

**Pipeline Stages**:
```python
Stage 1: Prompt Parsing     → 20% progress  (+$0.02-0.05)
Stage 2: Image Generation   → 35% progress  (+$0.10-0.30)
Stage 3: Video Generation   → 85% progress  (+$0.80-1.60)
Stage 4: Composition        → 100% progress (+$0.05-0.10)
```

**Interfaces**:
- **Input**: Job object from database
- **Output**: Updated job with result or error
- **Calls**: All 4 microservice clients
- **Updates**: Database (progress, costs, intermediate results)

**Key Logic**:
```python
async def execute_pipeline(job_id: UUID):
    # Stage 1: Parse prompt
    parsed = await prompt_client.parse(job.prompt, job.duration, ...)
    await update_progress(job_id, stage="prompt_parsing", pct=20, cost=0.05)

    # Stage 2: Generate reference image
    ref_image = await image_client.generate(parsed.scenes[0].prompt, ...)
    await update_progress(job_id, stage="image_generation", pct=35, cost=0.30)

    # Stage 3: Generate videos (PARALLEL)
    clips = await generate_videos_parallel(parsed.scenes, ref_image.url)
    await update_progress(job_id, stage="video_generation", pct=85, cost=1.20)

    # Stage 4: Compose final video
    final = await composition_client.compose(clips, parsed.audio, ...)
    await update_progress(job_id, stage="composition", pct=100, cost=0.10)

    # Mark complete
    await mark_complete(job_id, final.video_url, ...)
```

---

### 3. Microservice Clients (`app/services/`)

**Purpose**: HTTP clients for each external microservice

**Technology**: httpx (async HTTP client)

**Responsibilities**:
- Make HTTP requests to microservices
- Handle timeouts (10s, 15s, 90s, 30s)
- Parse standardized responses (`{success, result, cost, processing_time}`)
- Classify errors (transient vs permanent)
- Implement retry logic with exponential backoff

**Clients**:
1. **PromptParserClient** (`app/services/prompt_parser.py`)
   - Endpoint: `POST {PROMPT_PARSER_URL}/parse`
   - Timeout: 10 seconds
   - Retries: 3 attempts (2s, 4s, 8s backoff)

2. **ImageGenClient** (`app/services/image_gen.py`)
   - Endpoint: `POST {IMAGE_GEN_URL}/generate-image`
   - Timeout: 15 seconds
   - Retries: 3 attempts

3. **VideoGenClient** (`app/services/video_gen.py`)
   - Endpoint: `POST {VIDEO_GEN_URL}/generate-video`
   - Timeout: 90 seconds (video gen is slow)
   - Retries: 3 attempts
   - **Special**: Handles parallel generation with semaphore

4. **CompositionClient** (`app/services/composition.py`)
   - Endpoint: `POST {COMPOSITION_URL}/compose`
   - Timeout: 30 seconds
   - Retries: 3 attempts

**Retry Logic**:
```python
async def call_with_retry(url, payload, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await httpx.post(url, json=payload, timeout=timeout)
            return response.json()
        except (Timeout, ConnectionError) as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

### 4. Job Management (`app/models/`)

**Purpose**: Database models and state management

**Technology**: SQLAlchemy (async) with PostgreSQL

**Responsibilities**:
- Define Job model with all fields
- Manage state transitions
- Validate state changes (e.g., can't go from completed → processing)
- Provide query methods (get by ID, list by status)

**Job State Machine**:
```
┌─────────┐
│ queued  │ (Initial state after POST /generate-ad)
└────┬────┘
     │
     ▼
┌────────────┐
│ processing │ (Background task started)
└────┬───────┘
     │
     ├─────► ┌───────────┐
     │       │ completed │ (Success)
     │       └───────────┘
     │
     └─────► ┌──────┐
             │failed│ (Error)
             └──────┘
```

**Key Methods**:
- `Job.create()` - Create new job
- `Job.get_by_id()` - Retrieve job
- `Job.update_progress()` - Update stage and percentage
- `Job.add_cost()` - Increment cost for a stage
- `Job.mark_complete()` - Set status to completed
- `Job.mark_failed()` - Set status to failed with error details

---

### 5. Cost Tracker (`app/core/cost_tracker.py`)

**Purpose**: Aggregate and track costs per job

**Responsibilities**:
- Parse cost from microservice responses
- Store itemized breakdown per stage
- Calculate running total
- Alert when approaching budget limits ($5 warning, $10 hard limit)
- Generate cost reports

**Cost Breakdown Storage**:
```python
job.cost_prompt_parsing = Decimal("0.05")
job.cost_image_generation = Decimal("0.30")
job.cost_video_generation = Decimal("1.20")
job.cost_composition = Decimal("0.10")
job.cost_total = Decimal("1.65")  # Auto-calculated
```

---

### 6. Database Layer (`app/database.py`)

**Purpose**: PostgreSQL connection and session management

**Technology**: SQLAlchemy (async), asyncpg driver

**Responsibilities**:
- Async connection pooling (min 5, max 20 connections)
- Session management (context managers)
- Transaction handling
- Auto-migrations with Alembic on startup

**Configuration**:
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
)
```

---

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **API Style**: REST (JSON)
- **Key Libraries**:
  - `uvicorn` - ASGI server
  - `pydantic` - Data validation
  - `httpx` - Async HTTP client
  - `sqlalchemy[asyncio]` - Async ORM
  - `alembic` - Database migrations
  - `asyncpg` - PostgreSQL driver
  - `python-dotenv` - Environment variables

### Database
- **Type**: SQL (PostgreSQL)
- **Primary DB**: PostgreSQL 15+
- **ORM**: SQLAlchemy (async)
- **Migration Tool**: Alembic

### Infrastructure
- **Hosting**: Docker containers (AWS ECS, GCP Cloud Run, or Railway)
- **Database Hosting**: Managed PostgreSQL (AWS RDS, GCP Cloud SQL)
- **Storage**: AWS S3 (for video/image URLs)
- **CI/CD**: GitHub Actions (optional for final submission)
- **Monitoring**: Structured logging to stdout (JSON format)

### Development Tools
- **Testing**: pytest, pytest-asyncio
- **Linting**: ruff (fast Python linter)
- **Type Checking**: mypy (optional for final)
- **Containerization**: Docker + Docker Compose

---

## Data Model

### Job Entity

**Description**: Represents a single video generation job

**Table**: `jobs`

**Attributes**:
```sql
id                      UUID PRIMARY KEY
status                  VARCHAR(20) NOT NULL  -- queued, processing, completed, failed
prompt                  TEXT NOT NULL
duration                INTEGER NOT NULL      -- 15-60 seconds
aspect_ratio            VARCHAR(10) NOT NULL  -- 16:9, 9:16, 1:1
brand_guidelines        JSONB                 -- {primary_color, secondary_color, style}

-- Progress Tracking
current_stage           VARCHAR(50)           -- prompt_parsing, image_generation, etc.
stages_completed        TEXT[]                -- Array of completed stages
progress_percentage     INTEGER DEFAULT 0     -- 0-100

-- Intermediate Results
parsed_data             JSONB                 -- From Prompt Parser
reference_image_url     TEXT                  -- From Image Gen
clip_urls               TEXT[]                -- From Video Gen (array of S3 URLs)

-- Final Result
result                  JSONB                 -- {video_url, thumbnail_url, duration, resolution, file_size_mb, scenes_generated}

-- Cost Tracking (DECIMAL for precision)
cost_prompt_parsing     DECIMAL(10, 2) DEFAULT 0.00
cost_image_generation   DECIMAL(10, 2) DEFAULT 0.00
cost_video_generation   DECIMAL(10, 2) DEFAULT 0.00
cost_composition        DECIMAL(10, 2) DEFAULT 0.00
cost_total              DECIMAL(10, 2) DEFAULT 0.00

-- Error Information
error                   JSONB                 -- {code, message, failed_stage, details}

-- Timestamps
created_at              TIMESTAMP DEFAULT NOW()
updated_at              TIMESTAMP DEFAULT NOW()
completed_at            TIMESTAMP
failed_at               TIMESTAMP
```

**Indexes**:
```sql
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_cost_total ON jobs(cost_total);  -- For metrics
```

**Relationships**: None (single-table design for MVP)

---

## API Design

### 1. Generate Ad Video

**Method**: `POST`
**Path**: `/api/v1/generate-ad`
**Description**: Create new video generation job (async, returns immediately)

**Request Body**:
```json
{
  "prompt": "Create a 30 second Instagram ad for luxury watches",
  "duration": 30,
  "aspect_ratio": "9:16",
  "brand_guidelines": {
    "primary_color": "#D4AF37",
    "secondary_color": "#000000",
    "style": "luxury minimalist"
  }
}
```

**Validation**:
- `prompt`: 10-500 characters, required
- `duration`: 15-60 integer, required
- `aspect_ratio`: enum ["16:9", "9:16", "1:1"], required
- `brand_guidelines.primary_color`: hex color regex, optional
- `brand_guidelines.secondary_color`: hex color regex, optional
- `brand_guidelines.style`: max 100 chars, optional

**Response** (201 Created):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2025-11-14T10:30:00Z",
  "estimated_completion_time": "2025-11-14T10:35:00Z"
}
```

**Errors**:
- `400 INVALID_INPUT`: Validation failed

---

### 2. Get Job Status

**Method**: `GET`
**Path**: `/api/v1/jobs/{job_id}`
**Description**: Retrieve job status, progress, costs, and results

**Response** (200 OK - Processing):
```json
{
  "job_id": "550e8400-...",
  "status": "processing",
  "progress": {
    "current_stage": "video_generation",
    "stages_completed": ["prompt_parsing", "image_generation"],
    "stages_remaining": ["video_generation", "composition"],
    "percentage": 60
  },
  "cost": {
    "prompt_parsing": 0.05,
    "image_generation": 0.30,
    "video_generation": 1.20,
    "composition": 0.00,
    "total": 1.55
  },
  "result": null,
  "error": null,
  "created_at": "2025-11-14T10:30:00Z",
  "updated_at": "2025-11-14T10:32:15Z"
}
```

**Response** (200 OK - Completed):
```json
{
  "job_id": "550e8400-...",
  "status": "completed",
  "progress": {"current_stage": "completed", "percentage": 100},
  "cost": {"prompt_parsing": 0.05, "image_generation": 0.30, "video_generation": 1.50, "composition": 0.10, "total": 1.95},
  "result": {
    "video_url": "https://s3.amazonaws.com/bucket/videos/550e8400.mp4",
    "thumbnail_url": "https://s3.amazonaws.com/bucket/thumbnails/550e8400.jpg",
    "duration": 30,
    "resolution": "1080x1920",
    "file_size_mb": 12.5,
    "scenes_generated": 4
  },
  "error": null,
  "created_at": "2025-11-14T10:30:00Z",
  "completed_at": "2025-11-14T10:34:45Z"
}
```

**Response** (200 OK - Failed):
```json
{
  "job_id": "550e8400-...",
  "status": "failed",
  "progress": {"current_stage": "video_generation", "percentage": 45},
  "cost": {"prompt_parsing": 0.05, "image_generation": 0.30, "total": 0.35},
  "result": null,
  "error": {
    "code": "VIDEO_GENERATION_FAILED",
    "message": "Video generation service failed after 3 retries",
    "failed_stage": "video_generation",
    "details": {"service": "video-generation", "attempts": 3, "last_error": "429 Too Many Requests"}
  },
  "created_at": "2025-11-14T10:30:00Z",
  "failed_at": "2025-11-14T10:33:20Z"
}
```

**Errors**:
- `404 NOT_FOUND`: Job ID doesn't exist

---

### 3. Health Check

**Method**: `GET`
**Path**: `/health`
**Description**: Service health and database connectivity

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "ai-video-orchestrator",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2025-11-14T10:30:00Z"
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "unhealthy",
  "service": "ai-video-orchestrator",
  "database": "disconnected",
  "error": "Failed to connect to database"
}
```

---

## Security Architecture

### Authentication (MVP)
**Method**: None (open API)
**Rationale**: MVP focuses on functionality; frontend handles user auth

### Authorization (MVP)
**Method**: None
**Rationale**: All endpoints are public for team testing

### Data Encryption

**At Rest**:
- PostgreSQL: Encrypted volumes (handled by cloud provider)
- S3: Server-side encryption (SSE-S3)

**In Transit**:
- TLS 1.2+ for all HTTP communication
- HTTPS endpoints only (enforced in production)

### Security Considerations (MVP)

1. **Input Validation**:
   - Pydantic models validate all inputs
   - Regex validation for colors, aspect ratios
   - Length limits on prompt (500 chars max)

2. **Rate Limiting**:
   - 10 requests/minute per IP (using slowapi)
   - Prevents abuse of free API

3. **CORS**:
   - Enabled for frontend origin only
   - Wildcards disabled in production

4. **SQL Injection**:
   - SQLAlchemy ORM prevents injection
   - No raw SQL queries

5. **Secrets Management**:
   - Environment variables for all secrets
   - `.env` files excluded from git
   - AWS Secrets Manager for production (optional)

### Future Security Enhancements
- API key authentication
- JWT-based user sessions
- Webhook signature verification
- Video URL signing (time-limited access)

---

## Performance & Scalability

### Performance Targets

**MVP (48 hours)**:
| Metric | Target | Measurement |
|--------|--------|-------------|
| 30-sec ad generation | < 5 minutes | End-to-end pipeline time |
| API response time (create job) | < 500ms | p95 latency |
| API response time (get status) | < 100ms | p95 latency |
| Database queries | < 100ms | Single job lookup |
| Success rate | > 80% | Completed / (Completed + Failed) |
| Concurrent jobs | 5 | Max simultaneous pipelines |

**Final (8 days)**:
| Metric | Target | Measurement |
|--------|--------|-------------|
| 30-sec ad generation | < 3 minutes | End-to-end pipeline time |
| Success rate | > 90% | Completed / (Completed + Failed) |
| Concurrent jobs | 20 | Max simultaneous pipelines |
| Cost per video | < $2.00 | Average total cost |

### Scalability Strategy

**Horizontal Scaling**:
- Stateless API servers (can run multiple instances)
- Database connection pooling (10-20 connections per instance)
- Background tasks scale with number of API instances

**Vertical Scaling**:
- Increase database instance size for higher throughput
- Add read replicas for status queries (future optimization)

**Bottleneck Mitigation**:
1. **Database writes**: Use batching for progress updates (combine stage + cost update)
2. **Microservice timeouts**: Parallel video generation reduces total time
3. **Memory usage**: Stream large responses, don't load entire videos

### Caching

**Layer**: Application (Future Enhancement)
**Technology**: Redis
**Strategy**:
- Cache parsed prompts for identical inputs (key: hash of prompt + duration + aspect_ratio)
- Cache reference images for repeated style references
- TTL: 24 hours

**Not Cached in MVP**:
- Job status (must be real-time)
- Video URLs (generated once, stored in DB)

---

## Deployment Architecture

### Environments

**Development**:
- **URL**: `http://localhost:8000`
- **Config**:
  - Local PostgreSQL (Docker Compose)
  - Mock microservices for testing
  - Debug logging enabled
  - Auto-reload on code changes

**Production**:
- **URL**: `https://api.video-orchestrator.com` (example)
- **Config**:
  - Managed PostgreSQL (AWS RDS)
  - Real microservice URLs
  - INFO-level logging
  - Health check endpoint for load balancer

### Deployment Strategy

**MVP**: Docker Compose (single-server deployment)

**Final**: Container orchestration (AWS ECS or GCP Cloud Run)
- **Strategy**: Rolling deployment
- **Zero-downtime**: Health checks prevent traffic to unhealthy instances
- **Rollback**: Keep previous image tagged, redeploy if needed

### Docker Setup

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  orchestrator:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@db:5432/video_pipeline
      PROMPT_PARSER_URL: http://prompt-parser:8001
      IMAGE_GEN_URL: http://image-gen:8002
      VIDEO_GEN_URL: http://video-gen:8003
      COMPOSITION_URL: http://composition:8004
    depends_on: [db]

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: video_pipeline
      POSTGRES_PASSWORD: password
    volumes: [postgres_data:/var/lib/postgresql/data]

volumes:
  postgres_data:
```

---

## Monitoring & Observability

### Logging

**Tool**: Python `logging` module with structured JSON output

**Levels**:
- **ERROR**: Service failures, unhandled exceptions
- **WARN**: Retries, approaching cost limits ($5+)
- **INFO**: Job state changes, stage completions, HTTP requests
- **DEBUG**: Microservice payloads (dev only)

**Structured Log Format**:
```json
{
  "timestamp": "2025-11-14T10:30:15Z",
  "level": "INFO",
  "job_id": "550e8400-...",
  "stage": "video_generation",
  "message": "Video generation completed",
  "cost": 1.20,
  "duration_seconds": 42.3,
  "service": "orchestrator"
}
```

**Log Destination**:
- **MVP**: stdout (Docker captures logs)
- **Final**: CloudWatch Logs (AWS) or Cloud Logging (GCP)

### Metrics

**Business Metrics** (logged, not yet exposed via endpoint):
- `jobs_created_total` - Counter of all jobs
- `jobs_completed_total` - Counter of successful jobs
- `jobs_failed_total` - Counter of failed jobs
- `success_rate` - Percentage (calculated from counters)
- `average_cost_usd` - Gauge (updated per job)
- `total_cost_usd` - Counter (running total)

**Performance Metrics**:
- `api_request_duration_seconds` - Histogram (p50, p95, p99)
- `pipeline_duration_seconds` - Histogram per stage
- `database_query_duration_seconds` - Histogram

**Resource Metrics** (via Docker/cloud provider):
- CPU usage percentage
- Memory usage MB
- Database connections active
- HTTP connection pool size

**Alert Thresholds** (for final submission):
- Success rate < 85% → WARN
- Average cost > $2.50 → WARN
- API latency p95 > 1s → WARN
- Database connections > 80% of pool → WARN

### Tracing

**Tool**: None for MVP
**Future**: OpenTelemetry for distributed tracing across microservices

---

## Development Practices

### Code Organization

```
pipeline/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app + startup/shutdown
│   ├── config.py                  # Settings (from .env)
│   ├── database.py                # SQLAlchemy engine + session
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # Endpoint definitions
│   │   ├── schemas.py             # Pydantic models
│   │   └── middleware.py          # CORS, error handlers
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # Main pipeline logic
│   │   └── cost_tracker.py        # Cost aggregation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── job.py                 # Job SQLAlchemy model
│   │
│   └── services/
│       ├── __init__.py
│       ├── base_client.py         # Shared HTTP client logic
│       ├── prompt_parser.py       # Prompt Parser client
│       ├── image_gen.py           # Image Gen client
│       ├── video_gen.py           # Video Gen client
│       └── composition.py         # Composition client
│
├── alembic/
│   ├── versions/                  # Migration scripts
│   └── env.py
│
├── tests/
│   ├── test_api.py
│   ├── test_orchestrator.py
│   ├── test_clients.py
│   └── conftest.py                # Pytest fixtures
│
├── .env.example                   # Template for environment vars
├── .gitignore
├── .claudeignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── prd.md
├── ARCHITECTURE.md                # This file
└── README.md                      # Setup + usage instructions
```

### Coding Standards

1. **PEP 8**: Follow Python style guide (enforced by ruff)
2. **Type Hints**: Use for all function signatures
3. **Async/Await**: Async functions for all I/O operations
4. **Error Handling**: Always catch specific exceptions, never bare `except:`
5. **Logging**: Use structured logging with context (job_id, stage)
6. **Constants**: Define at module level in UPPER_CASE
7. **Environment Variables**: All config via `.env`, no hardcoded values

### Testing Strategy

**Unit Tests** (pytest):
- API request validation (Pydantic schemas)
- Job state transitions (model methods)
- Cost calculation logic
- Error classification (transient vs permanent)
- Target: 70% code coverage

**Integration Tests** (pytest with mocks):
- Mock all 4 microservices (httpx-mock)
- Test complete pipeline flow
- Test error scenarios (timeout, 500 errors, invalid responses)
- Test retry logic
- Target: All critical paths covered

**E2E Tests** (optional for final):
- Use real staging microservices
- Generate actual 15-second test video
- Verify video is accessible on S3
- Validate cost tracking accuracy

**Test Commands**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/test_api.py tests/test_orchestrator.py
```

---

## Dependencies & Integrations

### External Services

**1. Prompt Parser Service**
- **Purpose**: Parse text prompt into structured scenes with visual/audio direction
- **Integration**: HTTP POST to `{PROMPT_PARSER_URL}/parse`
- **Request**: `{prompt, duration, aspect_ratio, brand_guidelines}`
- **Response**: `{success, result: {scenes, visual_direction, audio, text_overlays}, cost, processing_time}`
- **Timeout**: 10 seconds
- **Owner**: Team member

**2. Image Generation Service**
- **Purpose**: Generate reference image for visual consistency
- **Integration**: HTTP POST to `{IMAGE_GEN_URL}/generate-image`
- **Request**: `{prompt, style, visual_direction}`
- **Response**: `{success, result: {image_url, seed}, cost, processing_time}`
- **Timeout**: 15 seconds
- **Owner**: Team member

**3. Video Generation Service**
- **Purpose**: Generate video clips from scene prompts + reference image
- **Integration**: HTTP POST to `{VIDEO_GEN_URL}/generate-video`
- **Request**: `{scene_prompt, reference_image_url, duration, aspect_ratio}`
- **Response**: `{success, result: {video_url, duration, resolution}, cost, processing_time}`
- **Timeout**: 90 seconds
- **Owner**: Team member

**4. Composition Service**
- **Purpose**: Stitch clips together with audio and text overlays
- **Integration**: HTTP POST to `{COMPOSITION_URL}/compose`
- **Request**: `{scenes: [{video_url, start_time, end_time, transition}], audio, text_overlays}`
- **Response**: `{success, result: {video_url, thumbnail_url, duration, file_size}, cost, processing_time}`
- **Timeout**: 30 seconds
- **Owner**: Team member

**5. AWS S3**
- **Purpose**: Storage for generated videos, images, thumbnails
- **Integration**: Microservices upload directly, return URLs
- **Authentication**: IAM roles (for microservices)
- **Bucket**: `gauntlet-video-pipeline` (example)
- **Owner**: DevOps/Team

---

## Risks & Technical Debt

### Risks

**1. Microservices Not Ready by MVP**
- **Impact**: Critical (can't test end-to-end)
- **Probability**: Medium
- **Mitigation**:
  - Implement mock services that match contract
  - Use `httpx-mock` for testing
  - Coordinate daily with team on API contract

**2. Video Generation Too Slow**
- **Impact**: High (won't meet 5-minute target)
- **Probability**: Medium
- **Mitigation**:
  - Use parallel generation (implemented)
  - Optimize prompt parsing to reduce clip count
  - Use fastest video models (Pika)
  - Add timeout alerts during testing

**3. Database Performance Issues**
- **Impact**: Medium (slow status updates)
- **Probability**: Low
- **Mitigation**:
  - Add indexes on status and created_at (done in schema)
  - Use connection pooling (configured)
  - Batch progress updates if needed

**4. Cost Overruns**
- **Impact**: High (fail competition requirement)
- **Probability**: Low
- **Mitigation**:
  - Hard limit at $10/job (fail job if exceeded)
  - Warning log at $5/job
  - Use cheap models for testing
  - Monitor costs in real-time

**5. Deadline Pressure**
- **Impact**: High (incomplete MVP)
- **Probability**: High
- **Mitigation**:
  - Focus on MVP essentials only
  - Defer metrics endpoint to final
  - Skip list jobs endpoint if time-constrained
  - Prioritize: health check → create job → get status → orchestrator

### Known Technical Debt

**1. No Webhook Notifications**
- **Priority**: Low
- **Plan**: Frontend can poll; add webhooks in days 4-7 if needed

**2. No Job Cancellation**
- **Priority**: Low
- **Plan**: Add `cancelled` status in final if requested

**3. Sequential Stage Execution**
- **Priority**: Medium
- **Plan**: Could parallelize image gen + prompt parsing, but complexity not worth it for MVP

**4. No Circuit Breaker**
- **Priority**: Low
- **Plan**: Retry logic is sufficient for MVP; add circuit breaker in final for production resilience

**5. Mock Service Dependency**
- **Priority**: High (must resolve before submission)
- **Plan**: Replace mocks with real service URLs by Day 2 evening

---

## Decision Log

### Decision 1: FastAPI BackgroundTasks vs Celery
**Date**: 2025-11-14
**Decision**: Use FastAPI BackgroundTasks for MVP
**Rationale**:
- Simpler setup (no Redis/RabbitMQ required)
- Sufficient for 5 concurrent jobs
- Faster to implement (48-hour deadline)
**Alternatives Considered**:
- Celery: Better for scaling to 100+ concurrent jobs, but adds infrastructure complexity
- Worker polling: Separate process polls for queued jobs, more scalable but slower to implement

---

### Decision 2: S3 for Video Storage
**Date**: 2025-11-14
**Decision**: Use AWS S3 for video/image storage
**Rationale**:
- Production-ready and scalable
- Microservices handle upload (orchestrator just stores URLs)
- Team likely already using S3
**Alternatives Considered**:
- Local filesystem: Simpler but not production-ready
- Database BLOB storage: Not suitable for large videos

---

### Decision 3: Auto-Migrations on Startup
**Date**: 2025-11-14
**Decision**: Run Alembic migrations automatically on app startup
**Rationale**:
- Faster deployment (no separate migration step)
- Acceptable risk for MVP (single developer)
**Alternatives Considered**:
- Manual migrations: Safer for production but adds deployment step

---

### Decision 4: Parallel Video Generation
**Date**: 2025-11-14
**Decision**: Generate video clips in parallel (with semaphore limiting)
**Rationale**:
- Reference image ensures visual consistency
- Critical for meeting 5-minute generation target
- Configurable concurrency limit prevents rate limiting
**Alternatives Considered**:
- Sequential: Safer for consistency but too slow (4min for 4 clips)

---

### Decision 5: No List Jobs Endpoint in MVP
**Date**: 2025-11-14
**Decision**: Skip `GET /api/v1/jobs` endpoint for MVP
**Rationale**:
- Frontend doesn't need it (focuses on single-job workflow)
- Can add in days 4-7 if time permits
**Alternatives Considered**:
- Implement now: Low priority compared to core pipeline

---

### Decision 6: Include Retry Logic in MVP
**Date**: 2025-11-14
**Decision**: Implement exponential backoff retry logic (3 attempts)
**Rationale**:
- Critical for 80%+ success rate
- Only ~30 lines of code
- Transient errors (timeouts, rate limits) are expected
**Alternatives Considered**:
- Defer to final: Too risky, would reduce success rate

---

### Decision 7: Real-Time Progress Updates
**Date**: 2025-11-14
**Decision**: Update database immediately after each stage completes
**Rationale**:
- Meets 2-second update requirement
- Keeps frontend fresh
- Database can handle write frequency
**Alternatives Considered**:
- Batched updates: Would reduce DB load but violate requirements

---

## Next Steps

### Immediate (Now)
1. ✅ Architecture document complete
2. ⏩ Scaffold project structure (Task C)
3. ⏩ Set up database models and migrations
4. ⏩ Implement API endpoints
5. ⏩ Implement orchestrator core logic

### Day 1 Completion Targets
- Working `/health` endpoint
- Database schema created
- API can create jobs (queued status)
- API can retrieve job status
- Mock microservice clients ready for testing

### Day 2 Focus
- Implement real microservice clients
- Complete orchestrator pipeline logic
- Integration testing with team's services
- Docker Compose setup

### Day 3 (MVP Deadline)
- End-to-end testing
- Bug fixes
- Generate sample videos
- Documentation
- Submit by 10:59 PM CT

---

**Document Status**: ✅ Complete and Ready for Implementation
**Reviewed By**: Winston (System Architect)
**Next Action**: Scaffold project structure
