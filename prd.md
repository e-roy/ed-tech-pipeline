# Product Requirements Document: AI Video Generation Orchestrator

**Project**: Gauntlet AI Video Generation Challenge
**Category**: Ad Creative Pipeline (Category 2)
**Document Version**: 1.0
**Date**: November 14, 2025
**Author**: Technical Lead

---

## Executive Summary

The AI Video Generation Orchestrator is the central coordination service for an end-to-end ad creative generation pipeline. It manages job lifecycle, coordinates microservices, tracks costs, monitors progress, and ensures successful delivery of 15-60 second AI-generated video advertisements.

**Competition Context**:
- **MVP Deadline**: 48 hours (Sunday, Nov 17, 10:59 PM CT)
- **Final Submission**: 8 days (Saturday, Nov 23, 10:59 PM CT)
- **Prize**: $5,000 for best pipeline
- **Cost Target**: Under $200 per video (we're targeting under $2 per video)

**Success Criteria**:
- Generate publication-ready 15-60 second video ads from text prompts
- Maintain visual consistency across 3-5 clips per video
- Track and report costs per video with sub-$2 target
- Provide real-time progress updates during generation
- 90%+ successful generation rate
- Complete generation in under 5 minutes for 30-second ads

---

## Problem Statement

Building AI video generation requires coordinating multiple AI models (LLMs, image generation, video generation) and video processing tools. The challenge is:

1. **Orchestration Complexity**: Managing sequential and parallel tasks across multiple services
2. **Cost Control**: Video generation APIs are expensive; must track and optimize costs
3. **Consistency**: Maintaining visual coherence across independently generated clips
4. **Progress Visibility**: Users need to see what's happening during the 2-5 minute generation
5. **Error Handling**: Any service can fail; system must be resilient
6. **Speed**: Must complete 30-second ad in under 5 minutes

The orchestrator solves these problems by providing a single API that manages the entire pipeline, handles failures gracefully, tracks costs meticulously, and keeps users informed.

---

## Goals and Non-Goals

### Goals

**Primary Goals (MVP - 48 hours)**:
- ✅ Accept text prompt and generate complete 15-60 second ad video
- ✅ Coordinate 4 microservices (Prompt Parser, Image Gen, Video Gen, Composition)
- ✅ Track job status with real-time progress updates
- ✅ Log and report costs per video with itemized breakdown
- ✅ Handle failures gracefully with detailed error messages
- ✅ Store job history in PostgreSQL database
- ✅ Provide REST API for job creation and status checking
- ✅ Deploy as containerized service

**Secondary Goals (Final - 8 days)**:
- 🎯 Implement retry logic with exponential backoff
- 🎯 Add webhook notifications for job completion
- 🎯 Support batch generation (multiple videos from one prompt)
- 🎯 Add caching for repeated prompts/reference images
- 🎯 Metrics endpoint for monitoring (jobs/hour, success rate, avg cost)
- 🎯 Admin dashboard for job management

### Non-Goals

**Out of Scope**:
- ❌ The orchestrator does NOT implement AI model logic (delegated to microservices)
- ❌ No user authentication/authorization (MVP is open API)
- ❌ No video storage management (services return URLs, we just store references)
- ❌ No frontend UI (team member building separate Next.js frontend)
- ❌ No A/B testing logic (handled by frontend, orchestrator just generates)
- ❌ No payment processing or billing

---

## User Stories

### Primary User: Frontend Developer (Team Member)

**Story 1: Generate Ad Video**
```
As a frontend developer
I want to submit an ad generation request via API
So that users can create video ads from text prompts

Acceptance Criteria:
- POST /api/v1/generate-ad accepts prompt, duration, aspect_ratio, brand_guidelines
- Returns job_id immediately (async operation)
- Job is created in database with status "queued"
- HTTP 201 response with job details
```

**Story 2: Check Generation Progress**
```
As a frontend developer
I want to poll job status
So that I can show users real-time progress

Acceptance Criteria:
- GET /api/v1/jobs/{job_id} returns current status
- Progress includes: current_stage, stages_completed, percentage
- Stages: prompt_parsing → image_generation → video_generation → composition
- Updates occur within 2 seconds of stage changes
```

**Story 3: Retrieve Completed Video**
```
As a frontend developer
I want to get the final video URL when generation completes
So that users can download/view their ad

Acceptance Criteria:
- GET /api/v1/jobs/{job_id} returns video_url when status = "completed"
- Response includes: video_url, thumbnail_url, duration, resolution, file_size
- Cost breakdown shows itemized expenses
- Video URL is publicly accessible (from S3/cloud storage)
```

**Story 4: Handle Failures**
```
As a frontend developer
I want detailed error information when generation fails
So that I can show users actionable error messages

Acceptance Criteria:
- Failed jobs have status = "failed"
- Error object includes: code, message, failed_stage
- Partial costs are still tracked (for stages that completed)
- Error messages are user-friendly, not raw exceptions
```

### Secondary User: DevOps Engineer (Team Member)

**Story 5: Monitor System Health**
```
As a DevOps engineer
I want health check endpoints
So that I can monitor service availability

Acceptance Criteria:
- GET /health returns 200 when service is healthy
- Includes database connectivity check
- Returns service version and uptime
```

**Story 6: Track Costs and Metrics**
```
As a DevOps engineer
I want aggregated metrics
So that I can monitor pipeline performance and costs

Acceptance Criteria:
- GET /api/v1/metrics returns: total_jobs, success_rate, avg_cost, avg_duration
- Filterable by time range (last hour, day, week)
- Database queries are optimized (under 100ms response)
```

---

## Technical Architecture

**Architecture Diagram**: [Workflowy Brainlift Diagram](https://workflowy.com/s/gauntlet-ai-video-ge/DU6xAqfBk5XyIBmS)

### System Context

```
┌─────────────┐
│   Frontend  │ (Next.js - separate repo)
│   (Team)    │
└──────┬──────┘
       │ HTTP REST
       ▼
┌─────────────────────────────────────┐
│   AI Video Generation Orchestrator  │
│   (This Service)                     │
│                                      │
│  • Job Management                   │
│  • Microservice Coordination        │
│  • Cost Tracking                    │
│  • Progress Updates                 │
│  • Error Handling                   │
└──┬────────┬────────┬────────┬───────┘
   │        │        │        │
   ▼        ▼        ▼        ▼
┌──────┐ ┌─────┐ ┌──────┐ ┌────────┐
│Prompt│ │Image│ │Video │ │Compose │
│Parser│ │Gen  │ │Gen   │ │Service │
└──────┘ └─────┘ └──────┘ └────────┘
  (Team)  (Team)  (Team)    (Team)
```

### Core Components

**1. API Layer** (`app/api/`)
- FastAPI application with REST endpoints
- Request validation using Pydantic models
- Response serialization
- Error handling middleware

**2. Orchestration Engine** (`app/core/orchestrator.py`)
- Main pipeline execution logic
- Sequential task coordination
- Service health checks before execution
- Retry logic with exponential backoff

**3. Microservice Clients** (`app/services/`)
- HTTP clients for each microservice
- Standardized request/response handling
- Timeout management (60s for video gen, 10s for others)
- Error classification (transient vs permanent)

**4. Job Management** (`app/models/job.py`)
- SQLAlchemy ORM for job persistence
- Status transitions: queued → processing → completed/failed
- Progress tracking with stage updates
- Cost accumulation

**5. Cost Tracker** (`app/core/cost_tracker.py`)
- Aggregates costs from all service responses
- Stores itemized breakdown per job
- Alerts when approaching budget limits
- Calculates running totals

**6. Database Layer** (`app/database.py`)
- Async PostgreSQL connection pooling
- Transaction management
- Alembic migrations

---

## API Specification

### 1. Generate Ad Video

**Endpoint**: `POST /api/v1/generate-ad`

**Request Body**:
```json
{
  "prompt": "Create a 30 second Instagram ad for luxury watches with elegant gold aesthetics",
  "duration": 30,
  "aspect_ratio": "9:16",
  "brand_guidelines": {
    "primary_color": "#D4AF37",
    "secondary_color": "#000000",
    "style": "luxury minimalist"
  }
}
```

**Response** (201 Created):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2025-11-14T10:30:00Z",
  "estimated_completion_time": "2025-11-14T10:35:00Z"
}
```

**Validations**:
- `duration`: 15-60 seconds
- `aspect_ratio`: "16:9", "9:16", or "1:1"
- `prompt`: 10-500 characters
- `brand_guidelines`: optional, validated color hex codes

### 2. Get Job Status

**Endpoint**: `GET /api/v1/jobs/{job_id}`

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": {
    "current_stage": "video_generation",
    "stages_completed": ["prompt_parsing", "image_generation"],
    "stages_remaining": ["video_generation", "composition"],
    "percentage": 60,
    "estimated_completion_time": "2025-11-14T10:34:30Z"
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

**When Completed** (status = "completed"):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": {
    "current_stage": "completed",
    "percentage": 100
  },
  "cost": {
    "prompt_parsing": 0.05,
    "image_generation": 0.30,
    "video_generation": 1.50,
    "composition": 0.10,
    "total": 1.95
  },
  "result": {
    "video_url": "https://storage.example.com/videos/550e8400.mp4",
    "thumbnail_url": "https://storage.example.com/thumbnails/550e8400.jpg",
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

**When Failed** (status = "failed"):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": {
    "current_stage": "video_generation",
    "percentage": 45
  },
  "cost": {
    "prompt_parsing": 0.05,
    "image_generation": 0.30,
    "total": 0.35
  },
  "result": null,
  "error": {
    "code": "VIDEO_GENERATION_FAILED",
    "message": "Video generation service failed after 3 retries: API rate limit exceeded",
    "failed_stage": "video_generation",
    "details": {
      "service": "video-generation",
      "attempts": 3,
      "last_error": "429 Too Many Requests"
    }
  },
  "created_at": "2025-11-14T10:30:00Z",
  "failed_at": "2025-11-14T10:33:20Z"
}
```

### 3. List Jobs

**Endpoint**: `GET /api/v1/jobs?status=completed&limit=20&offset=0`

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "job_id": "...",
      "status": "completed",
      "created_at": "...",
      "cost_total": 1.95
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

### 4. Health Check

**Endpoint**: `GET /health`

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "ai-video-orchestrator",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "database": "connected",
  "timestamp": "2025-11-14T10:30:00Z"
}
```

### 5. Metrics (Bonus)

**Endpoint**: `GET /api/v1/metrics?time_range=24h`

**Response** (200 OK):
```json
{
  "time_range": "24h",
  "total_jobs": 247,
  "completed_jobs": 223,
  "failed_jobs": 24,
  "success_rate": 90.3,
  "average_cost_usd": 1.87,
  "average_duration_seconds": 245,
  "total_cost_usd": 461.89,
  "jobs_per_hour": 10.3
}
```

---

## Pipeline Flow

### Complete Generation Flow

```
1. User submits prompt via POST /api/v1/generate-ad
   ↓
2. Orchestrator creates Job (status: queued) in database
   ↓
3. Orchestrator updates Job (status: processing)
   ↓
4. STAGE 1: Prompt Parser Service
   → Send: {prompt, duration, aspect_ratio, brand_guidelines}
   ← Receive: {scenes: [...], visual_direction: {...}, audio: {...}, text_overlays: [...]}
   → Update progress: 20% (stages_completed: ["prompt_parsing"])
   → Update cost: +$0.05
   ↓
5. STAGE 2: Image Generation Service
   → Send: {prompt: scene[0].prompt, style, visual_direction}
   ← Receive: {image_url, seed}
   → Store reference_image_url in Job
   → Update progress: 35% (stages_completed: ["prompt_parsing", "image_generation"])
   → Update cost: +$0.30
   ↓
6. STAGE 3: Video Generation Service (PARALLEL for each scene)
   For each scene in scenes[]:
     → Send: {scene.prompt, reference_image_url, duration, aspect_ratio}
     ← Receive: {video_url, duration, resolution}
     → Store clip URLs in Job
     → Update progress: 35% → 85% (incremental per clip)
     → Update cost: +$1.20 per clip
   ↓
7. STAGE 4: Composition Service
   → Send: {scenes: [{video_url, start_time, end_time, transition}], audio, text_overlays}
   ← Receive: {video_url, thumbnail_url, duration, file_size}
   → Store final video URL in Job
   → Update progress: 100%
   → Update cost: +$0.10
   ↓
8. Orchestrator updates Job (status: completed)
   → Store result: {video_url, thumbnail_url, ...}
   → Calculate total cost
   → Record completion time
   ↓
9. User polls GET /api/v1/jobs/{job_id} and retrieves video_url
```

### Error Handling Flow

```
If any stage fails:
1. Catch exception from microservice
2. Classify error:
   - Transient (timeout, rate limit) → Retry with exponential backoff
   - Permanent (invalid input, model error) → Fail immediately
3. Update Job (status: failed)
4. Store error details: {code, message, failed_stage, details}
5. Store partial costs (for stages that completed)
6. Log error for debugging
7. Return error in GET /api/v1/jobs/{job_id} response
```

---

## Database Schema

### Jobs Table

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) NOT NULL,  -- queued, processing, completed, failed

    -- Input
    prompt TEXT NOT NULL,
    duration INTEGER NOT NULL,
    aspect_ratio VARCHAR(10) NOT NULL,
    brand_guidelines JSONB,

    -- Progress
    current_stage VARCHAR(50),
    stages_completed TEXT[],
    progress_percentage INTEGER DEFAULT 0,

    -- Intermediate Results
    parsed_data JSONB,  -- From Prompt Parser
    reference_image_url TEXT,  -- From Image Gen
    clip_urls TEXT[],  -- From Video Gen

    -- Final Result
    result JSONB,  -- {video_url, thumbnail_url, duration, resolution, file_size}

    -- Cost Tracking
    cost_prompt_parsing DECIMAL(10, 2) DEFAULT 0,
    cost_image_generation DECIMAL(10, 2) DEFAULT 0,
    cost_video_generation DECIMAL(10, 2) DEFAULT 0,
    cost_composition DECIMAL(10, 2) DEFAULT 0,
    cost_total DECIMAL(10, 2) DEFAULT 0,

    -- Error
    error JSONB,  -- {code, message, failed_stage, details}

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,

    -- Indexes
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_created_at (created_at DESC)
);
```

---

## Service Integration Contracts

### Microservice Standard Response

All microservices MUST return:

```json
{
  "success": true/false,
  "result": { /* service-specific data */ },
  "cost": 1.25,  // USD
  "processing_time": 3.4,  // seconds
  "metadata": { /* optional debug info */ }
}
```

### Service Endpoints

**Prompt Parser**: `POST {PROMPT_PARSER_URL}/parse`
**Image Gen**: `POST {IMAGE_GEN_URL}/generate-image`
**Video Gen**: `POST {VIDEO_GEN_URL}/generate-video`
**Composition**: `POST {COMPOSITION_URL}/compose`

### Timeouts

- Prompt Parser: 10 seconds
- Image Generation: 15 seconds
- Video Generation: 90 seconds (video gen is slow)
- Composition: 30 seconds

### Retry Policy

- Transient errors: 3 retries with exponential backoff (2s, 4s, 8s)
- Permanent errors: Fail immediately
- Circuit breaker: After 5 consecutive failures, stop calling service for 60s

---

## Cost Model

### Target Costs (Per 30-Second Ad)

| Stage | Cost | Notes |
|-------|------|-------|
| Prompt Parsing | $0.02 - 0.05 | GPT-4o tokens |
| Image Generation | $0.10 - 0.30 | FLUX or SD-XL |
| Video Generation (4 clips) | $0.80 - 1.60 | Pika @ $0.20-0.40/clip |
| Composition | $0.05 - 0.10 | FFmpeg compute |
| **Total** | **$0.97 - 2.05** | ✅ Well under $200 target |

### Cost Optimization Strategies

1. **Tiered Model Usage**: Use cheap models for testing, expensive for finals
2. **Caching**: Cache parsed prompts and reference images for identical inputs
3. **Clip Length Optimization**: Generate exactly the needed duration, no excess
4. **Parallel Generation**: Generate all clips concurrently to save time (not cost)
5. **Budget Alerts**: Log warning when job exceeds $5, fail if exceeds $10

---

## Performance Requirements

### MVP Targets (48 Hours)

| Metric | Target | Rationale |
|--------|--------|-----------|
| 30-sec ad generation | < 5 minutes | Competition requirement |
| Success rate | > 80% | Acceptable for MVP |
| API response time | < 500ms | For job creation/status |
| Database queries | < 100ms | Fast status checks |
| Concurrent jobs | 5 | MVP handles sequential + some parallel |

### Final Targets (8 Days)

| Metric | Target | Rationale |
|--------|--------|-----------|
| 30-sec ad generation | < 3 minutes | Optimized pipeline |
| Success rate | > 90% | Production quality |
| Concurrent jobs | 20 | Handle burst traffic |
| Cost per video | < $2.00 | Beat competition requirement |

---

## Error Handling

### Error Categories

**1. User Input Errors (400)**
- Invalid prompt (too short, too long)
- Invalid duration (not 15-60)
- Invalid aspect ratio
- Missing required fields

**2. Service Errors (502/503)**
- Microservice timeout
- Microservice returns error
- Rate limit exceeded
- Invalid response format

**3. System Errors (500)**
- Database connection failure
- Internal logic error
- Unhandled exception

### Error Response Format

```json
{
  "error": {
    "code": "VIDEO_GENERATION_TIMEOUT",
    "message": "Video generation service timed out after 90 seconds",
    "stage": "video_generation",
    "details": {
      "service_url": "http://video-gen:8003",
      "timeout_seconds": 90,
      "retries_attempted": 2
    }
  }
}
```

### Error Codes

- `INVALID_INPUT`: User input validation failed
- `SERVICE_UNAVAILABLE`: Microservice health check failed
- `PROMPT_PARSING_FAILED`: Prompt Parser returned error
- `IMAGE_GENERATION_FAILED`: Image Gen returned error
- `VIDEO_GENERATION_FAILED`: Video Gen returned error
- `COMPOSITION_FAILED`: Composition service returned error
- `TIMEOUT`: Service exceeded timeout
- `RATE_LIMIT_EXCEEDED`: Hit API rate limit
- `COST_LIMIT_EXCEEDED`: Job exceeded budget
- `INTERNAL_ERROR`: Unexpected system error

---

## Testing Strategy

### Unit Tests

Test individual components:
- API request validation
- Job state transitions
- Cost calculation logic
- Error classification

### Integration Tests

Test orchestrator with mock services:
- Mock all 4 microservices
- Test complete pipeline flow
- Test error scenarios (service failures, timeouts)
- Test cost accumulation

### E2E Tests

Test with real services (in staging):
- Generate actual video from prompt
- Verify all stages complete
- Check final video is accessible
- Validate cost tracking

### Load Tests

- 10 concurrent job submissions
- Verify no race conditions in database
- Check API response times under load

---

## Deployment

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/video_pipeline

# Microservices
PROMPT_PARSER_URL=http://prompt-parser:8001
IMAGE_GEN_URL=http://image-gen:8002
VIDEO_GEN_URL=http://video-gen:8003
COMPOSITION_URL=http://composition:8004

# Configuration
MAX_COST_PER_VIDEO=10.00
API_TIMEOUT_SECONDS=120
MAX_CONCURRENT_JOBS=10

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=https://...  # Error tracking (optional)
```

### Docker Compose (Development)

```yaml
version: '3.8'
services:
  orchestrator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/video_pipeline
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: video_pipeline
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Production Deployment

- Deploy on AWS ECS, GCP Cloud Run, or Railway
- Use managed PostgreSQL (RDS, Cloud SQL)
- Set up health check endpoint for load balancer
- Enable auto-scaling based on CPU/memory
- Configure logging to CloudWatch/Stackdriver

---

## Monitoring and Observability

### Metrics to Track

**Business Metrics**:
- Total jobs created (counter)
- Jobs by status (gauge): queued, processing, completed, failed
- Success rate (gauge): completed / (completed + failed)
- Average cost per video (gauge)
- Total revenue potential (if charging users)

**Performance Metrics**:
- API request latency (histogram)
- Pipeline duration by stage (histogram)
- Database query time (histogram)
- Microservice response time (histogram)

**Resource Metrics**:
- CPU usage
- Memory usage
- Database connections
- HTTP connection pool

### Logging

**Log Levels**:
- ERROR: Service failures, unhandled exceptions
- WARN: Retries, approaching cost limits
- INFO: Job state changes, stage completions
- DEBUG: Microservice requests/responses (in dev only)

**Structured Logging**:
```json
{
  "timestamp": "2025-11-14T10:30:15Z",
  "level": "INFO",
  "job_id": "550e8400-...",
  "stage": "video_generation",
  "message": "Video generation completed",
  "cost": 1.20,
  "duration_seconds": 42.3
}
```

---

## Security Considerations

### MVP (Low Priority)

- No authentication (open API)
- Rate limiting: 10 requests/minute per IP
- Input validation to prevent injection
- CORS enabled for frontend origin

### Future

- API key authentication
- User account system
- Payment integration
- Video access control (signed URLs)

---

## Success Criteria

### MVP (48 Hours) - MUST HAVE

✅ **Functional**:
- Generate complete 30-second ad from prompt
- All 4 pipeline stages execute successfully
- Video output is downloadable
- Cost is tracked and under $2

✅ **Technical**:
- API endpoints work (POST /generate-ad, GET /jobs/{id})
- Database persists jobs
- Services integrate via HTTP
- Error handling returns useful messages

✅ **Documentation**:
- README with setup instructions
- API documentation
- Integration guide for team

### Final (8 Days) - NICE TO HAVE

🎯 **Quality**:
- 90%+ success rate
- < 3 minute generation time
- Robust retry logic
- Comprehensive error handling

🎯 **Features**:
- Metrics endpoint
- Webhook notifications
- Caching for repeated prompts
- Admin dashboard (if time permits)

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Microservices not ready by MVP | Critical | Medium | Implement mock services for testing |
| Video generation is too slow | High | High | Use fastest models (Pika), optimize parallel processing |
| Costs exceed budget | High | Low | Strict cost tracking, alerts, use cheap models for testing |
| Database performance issues | Medium | Low | Index key columns, use connection pooling |
| Service integration bugs | Medium | Medium | Comprehensive integration tests |
| Deadline pressure | High | High | Focus on MVP essentials, defer nice-to-haves |

---

## Timeline

### Day 1 (Friday, Nov 14) - 8 hours
- ✅ Write PRD (this document)
- ⏱️ Set up repo structure
- ⏱️ Implement database models
- ⏱️ Implement API endpoints (generate-ad, get job)
- ⏱️ Write basic orchestrator logic (without real services)

### Day 2 (Saturday, Nov 15) - 12 hours
- ⏱️ Implement microservice clients
- ⏱️ Integrate with team's services (as they become available)
- ⏱️ Test end-to-end flow with mock services
- ⏱️ Deploy to staging environment
- ⏱️ Write tests

### Day 3 (Sunday, Nov 16) - 12 hours **[MVP DEADLINE]**
- ⏱️ Integration testing with real services
- ⏱️ Fix bugs found during testing
- ⏱️ Generate 2 sample videos for submission
- ⏱️ Write documentation
- ⏱️ Deploy to production
- ✅ **SUBMIT MVP by 10:59 PM CT**

### Days 4-7 (Mon-Thu) - Improvements
- Add retry logic
- Implement caching
- Add metrics endpoint
- Performance optimization
- More comprehensive tests

### Day 8 (Friday, Nov 22) - Polish
- Final testing
- Generate showcase videos
- Update documentation
- Prepare demo video

### Day 9 (Saturday, Nov 23) - **[FINAL DEADLINE]**
- Last-minute fixes
- ✅ **SUBMIT FINAL by 10:59 PM CT**

---

## Appendix

### Tech Stack Summary

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy
- **HTTP Client**: httpx (async)
- **Testing**: pytest
- **Deployment**: Docker + Docker Compose

### Key Dependencies

- fastapi, uvicorn
- sqlalchemy, alembic, psycopg2
- httpx, aiohttp
- pydantic, pydantic-settings
- python-dotenv

### Open Questions

1. ❓ Where will final videos be stored? (S3, GCS, or local for MVP?)
2. ❓ Do we need webhook notifications or is polling acceptable?
3. ❓ Should we support canceling in-progress jobs?
4. ❓ Do we need video preview/thumbnail generation?

### References

- Competition Brief: See attached documents
- TPM Report: Technical stack recommendations
- Team Slack: #video-pipeline channel

---

**Document Status**: ✅ Ready for Review
**Next Steps**: Team review → Begin implementation
**Questions**: Contact technical lead

---

*This PRD is a living document and will be updated as requirements evolve.*
