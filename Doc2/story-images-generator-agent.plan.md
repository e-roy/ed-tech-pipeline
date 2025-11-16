<!-- 84cd4a51-f8b5-4241-bb82-453cecb20f80 97a08bd7-484c-4d8e-8210-71e75e01d8aa -->
# Story Images Generator - FastAPI + Agent Architecture

## Architecture Overview

**Simple API-driven flow:**

```
Frontend/Client → FastAPI Endpoint → Orchestrator → StoryImageGeneratorAgent → S3
WebSocket ← Real-time progress updates
```

1. **API Endpoint** receives request with S3 path to segments.md
2. **Orchestrator** reads files from S3, coordinates workflow, sends WebSocket updates
3. **StoryImageGeneratorAgent** processes segments in parallel, generates images, verifies them
4. **Results** written to S3, status.json updated incrementally, WebSocket provides real-time updates

## Key Decisions

- **Processing**: Parallel segments using `asyncio.gather()` (process in any order, sort results)
- **Diagram handling**: Pass S3 path to agent, agent downloads when needed (lazy loading)
- **Verification**: Always verify every image (no skipping)
- **Status tracking**: Write status.json at start, update incrementally after each segment
- **API response**: Return immediately, use WebSocket for updates
- **Secrets**: Cache globally with TTL (1 hour), Secrets Manager only
- **Errors**: Error codes + brief messages (no stack traces in response)
- **WebSocket**: All updates (per-segment, per-image, overall progress)
- **S3 bucket**: Always `pipeline-backend-assets` (hardcoded)
- **User validation**: Verify user_id from path AND session belongs to user

## Components to Create

### 1. AWS Secrets Manager Secrets

- `pipeline/openrouter-api-key` - OpenRouter API key for image verification
- `pipeline/replicate-api-key` - Replicate API key for image generation

### 2. FastAPI Endpoint: `POST /api/process-story-segments`

- **Location**: `backend/app/routes/generation.py`
- **Authentication**: Uses existing `get_current_user` dependency
- **Request Body**:
  ```json
  {
    "session_id": "session456",
    "s3_path": "users/user123/session456/images/segments.md",
    "options": {
      "num_images": 2,
      "max_passes": 5,
      "max_verification_passes": 3,
      "fast_mode": false
    }
  }
  ```

- **Immediate Response**:
  ```json
  {
    "status": "accepted",
    "session_id": "session456",
    "message": "Processing started, listen to WebSocket for updates"
  }
  ```

- **Responsibilities**:
  - Validate user access (extract user_id from S3 path AND verify session belongs to user)
  - Validate S3 bucket is `pipeline-backend-assets` (hardcoded)
  - Read `config.json` from S3 (if exists, same directory as segments.md, overrides defaults)
  - Call orchestrator to process segments (async, non-blocking)
  - Return immediately with acceptance message
  - WebSocket provides real-time updates

### 3. StoryImageGeneratorAgent

- **Location**: `backend/app/agents/story_image_generator.py`
- **Implements**: `Agent` interface (`async def process(input: AgentInput) -> AgentOutput`)
- **Input Data**:
  ```python
  {
    "segments": [...],  # Parsed segments from segments.md
    "diagram_s3_path": "s3://pipeline-backend-assets/users/user123/session456/images/diagram.png",  # Optional, agent downloads when needed
    "output_s3_prefix": "users/user123/session456/images/",
    "num_images": 2,
    "max_passes": 5,
    "max_verification_passes": 3,
    "fast_mode": False  # Only affects generation speed, verification always happens
  }
  ```

- **Processing**:
  - Process segments in parallel using `asyncio.gather()` (any order)
  - Sort results by segment number before returning
  - Always verify every image (no skipping verification)
  - Download diagram.png from S3 when needed (lazy loading)
- **Output Data**: Returns AgentOutput with results, cost, duration

### 4. Orchestrator Integration

- **Location**: `backend/app/services/orchestrator.py`
- **New Method**: `async def process_story_segments(db, session_id, user_id, s3_path, options) -> Dict`
- **Responsibilities**:
  - Validate user access (extract user_id from S3 path AND verify session belongs to user)
  - Read segments.md from S3 using StorageService
  - Read config.json from S3 (if exists, same directory as segments.md)
  - Extract diagram.png S3 path (same directory as segments.md, pass to agent)
  - Parse segments.md format
  - Write initial status.json to S3 (status: "in_progress")
  - Instantiate StoryImageGeneratorAgent with API keys from Secrets Manager (cached)
  - Send WebSocket updates (per-segment, per-image, overall progress)
  - Call `agent.process(AgentInput(...))` - agent handles diagram download
  - Update status.json incrementally after each segment
  - Handle errors and retries
  - Write final status.json to S3
  - Return results (WebSocket provides updates)

### 5. Secrets Manager Utilities

- **Location**: `backend/app/services/secrets.py` (new file)
- **Function**: `get_secret(secret_name: str) -> str`
- **Implementation**:
  - Global cache: `{secret_name: (value, expiry_timestamp)}`
  - TTL: 1 hour
  - Thread-safe: Use `threading.Lock()` for cache access
  - No fallback to environment variables (Secrets Manager only)
  - Handle errors gracefully

## File Structure

```
backend/
├── app/
│   ├── routes/
│   │   └── generation.py            # Add POST /api/process-story-segments endpoint
│   ├── agents/
│   │   └── story_image_generator.py # New agent (reuses logic from generate_story_images.py)
│   ├── services/
│   │   ├── orchestrator.py          # Add process_story_segments() method
│   │   ├── storage.py               # Already exists, used for S3 operations
│   │   └── secrets.py               # New: Secrets Manager utilities
│   └── config.py                    # May add helper if needed
```

## Implementation Details

### StoryImageGeneratorAgent Implementation

**Key Functions to Port from `generate_story_images.py`:**

- `parse_segments_md()` - Parse segments.md format
- `generate_story_prompts()` - Generate sequential prompts
- `generate_image_via_replicate()` - Replicate API wrapper
- `verify_image_no_labels()` - OpenRouter verification
- Segment processing logic (adapt for parallel async processing)

**Adaptations:**

- Replace filesystem paths with S3 paths
- Use StorageService for S3 read/write
- Use Secrets Manager for API keys (cached globally with TTL)
- Return AgentOutput instead of writing to filesystem
- Process segments in parallel using `asyncio.gather()`
- Process segments in any order, sort results by segment number
- Pass diagram S3 path to agent, agent downloads when needed
- Always verify every image (no skipping verification)

### WebSocket Message Format

Follows existing orchestrator pattern:

```json
{
  "type": "story_image_progress",
  "session_id": "session456",
  "progress": {
    "overall_percentage": 50,
    "segments_completed": 2,
    "segments_total": 4,
    "current_segment": 3,
    "current_segment_progress": {
      "segment_number": 3,
      "images_completed": 1,
      "images_total": 2,
      "current_step": "verifying",
      "current_image": 1
    }
  }
}
```

### Status File Format

Written to: `users/{userid}/{sessionid}/images/status.json`

**Initial (at start):**

```json
{
  "status": "in_progress",
  "started_at": "2024-01-01T00:00:00Z",
  "segments_total": 4,
  "segments_completed": 0,
  "segments_succeeded": 0,
  "segments_failed": 0
}
```

**Updated incrementally (after each segment):**

```json
{
  "status": "in_progress",
  "started_at": "2024-01-01T00:00:00Z",
  "segments_total": 4,
  "segments_completed": 2,
  "segments_succeeded": 2,
  "segments_failed": 0,
  "segment_results": [
    {
      "segment_number": 1,
      "status": "success",
      "images_generated": 2,
      "cost_usd": 0.009,
      "time_seconds": 20.5
    }
  ]
}
```

**Final:**

```json
{
  "status": "completed",
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:05:00Z",
  "segments_total": 4,
  "segments_completed": 4,
  "segments_succeeded": 3,
  "segments_failed": 1,
  "total_images_generated": 7,
  "total_cost_usd": 0.032,
  "total_time_seconds": 75.2,
  "errors": [
    {
      "segment_number": 2,
      "error_code": "IMAGE_GENERATION_FAILED",
      "error_message": "Replicate API timeout after 5 attempts",
      "retry_count": 5
    }
  ],
  "segment_results": [...]
}
```

## Error Handling & Mitigation

All errors return error codes + brief messages (no stack traces in API response). Full details logged server-side.

### Key Error Scenarios:

1. **S3 Access Errors**: Retry with exponential backoff, return HTTP 404/403
2. **Secrets Manager Errors**: Cache with TTL, retry, return HTTP 500
3. **Invalid segments.md**: Validate before processing, return HTTP 400 with validation errors
4. **Missing diagram.png**: Warning (not fatal), continue processing
5. **API Rate Limits**: Exponential backoff with jitter, retry up to 5 times
6. **Image Generation Failures**: Retry with fallback model (SDXL), max 5 attempts
7. **Verification Failures**: Retry verification, regenerate image if needed
8. **Partial Failures**: Return partial results with error details for failed segments

## API Response Format

**Immediate Response (200 OK):**

```json
{
  "status": "accepted",
  "session_id": "session456",
  "message": "Processing started, listen to WebSocket for updates"
}
```

**Final WebSocket Message:**

```json
{
  "type": "story_image_complete",
  "session_id": "session456",
  "status": "success",
  "results": {
    "template_title": "Photosynthesis",
    "segments_total": 4,
    "segments_succeeded": 4,
    "segments_failed": 0,
    "total_images_generated": 8,
    "total_cost_usd": 0.0367,
    "total_time_seconds": 80.7,
    "generation_report_s3_path": "s3://pipeline-backend-assets/..."
  }
}
```

## Implementation Steps

1. Create Secrets Manager secrets (OpenRouter, Replicate API keys)
2. Create `backend/app/services/secrets.py` with global cache and TTL
3. Create `StoryImageGeneratorAgent` class

   - Port logic from generate_story_images.py
   - Adapt for S3 and async processing
   - Implement parallel segment processing with asyncio.gather()

4. Add `process_story_segments()` method to orchestrator

   - Read files from S3
   - Send WebSocket updates
   - Write status.json incrementally
   - Call agent.process()

5. Add POST /api/process-story-segments endpoint

   - Request validation
   - Return immediately
   - Call orchestrator (async)

6. Test with sample segments.md file
7. Update API documentation