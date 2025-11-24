# Pipeline Backend API Documentation

This document describes the actual API endpoints exposed by the Pipeline backend orchestrator.

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production (ALB)**: `https://api.classclipscohort3.com`

## Interactive Documentation

- **Swagger UI**: `/docs`
- **OpenAPI JSON**: `/openapi.json`

---

## Health & System

### GET `/`
**Health check endpoint**

Response:
```json
{
  "status": "healthy",
  "service": "Gauntlet Pipeline Orchestrator",
  "version": "1.0.0"
}
```

### GET `/health`
**Detailed health check**

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "services": {
    "orchestrator": "ready",
    "websocket": "ready"
  }
}
```

---

## Authentication (`/api/auth`)

All generation and session endpoints require authentication via Bearer token.

### POST `/api/auth/login`
**Login to get access token**

Request (Form Data):
- `username`: `demo@example.com`
- `password`: `demo123`

Response:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### POST `/api/auth/exchange`
**Exchange NextAuth session for backend JWT**

This allows the frontend to exchange a NextAuth session (identified by email) for a backend JWT token.

Request:
```json
{
  "email": "user@example.com"
}
```

Response:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### GET `/api/auth/me`
**Get current user info**

Headers:
- `Authorization: Bearer <token>`

Response:
```json
{
  "id": 1,
  "email": "demo@example.com",
  "created_at": "2025-01-15T10:30:00"
}
```

---

## Generation Workflow (`/api`)

### POST `/api/generate-images`
**Step 1: Generate images from text prompt**

Generates images using Flux-Schnell via Replicate. Creates a new session.

Headers:
- `Authorization: Bearer <token>`

Request:
```json
{
  "prompt": "man buys hat",
  "num_images": 4,
  "aspect_ratio": "16:9"
}
```

Response:
```json
{
  "session_id": "uuid-string",
  "status": "completed",
  "images": [
    {
      "url": "https://...",
      "index": 0
    }
  ]
}
```

### POST `/api/save-approved-images`
**Step 2: Save user-selected images**

User approves which generated images to use for video generation.

Headers:
- `Authorization: Bearer <token>`

Request:
```json
{
  "session_id": "uuid-string",
  "approved_image_urls": [
    "https://...",
    "https://..."
  ]
}
```

Response:
```json
{
  "status": "success",
  "session_id": "uuid-string",
  "approved_count": 2
}
```

### POST `/api/generate-clips`
**Step 3: Generate video clips from approved images**

Generates video clips using Gen-4-Turbo via Replicate.

Headers:
- `Authorization: Bearer <token>`

Request:
```json
{
  "session_id": "uuid-string",
  "video_prompt": "elegant hat showcase with smooth camera movement",
  "num_clips": 2,
  "duration": 8.0
}
```

Response:
```json
{
  "session_id": "uuid-string",
  "status": "completed",
  "clips": [
    {
      "url": "https://...",
      "index": 0,
      "duration": 8.0
    }
  ]
}
```

### POST `/api/save-approved-clips`
**Step 4: Save user-selected video clips**

User approves which generated clips to use in final video.

Headers:
- `Authorization: Bearer <token>`

Request:
```json
{
  "session_id": "uuid-string",
  "approved_clip_urls": [
    "https://...",
    "https://..."
  ]
}
```

Response:
```json
{
  "status": "success",
  "session_id": "uuid-string",
  "approved_count": 2
}
```

### POST `/api/compose-final-video`
**Step 5: Compose final video with clips, text, and audio**

Combines approved clips with optional text overlays and audio using FFmpeg.

Headers:
- `Authorization: Bearer <token>`

Request:
```json
{
  "session_id": "uuid-string",
  "text_overlays": [
    {
      "text": "Chapter 1",
      "start_time": 0.0,
      "duration": 2.0
    }
  ],
  "audio_url": "https://..."
}
```

Response:
```json
{
  "session_id": "uuid-string",
  "status": "completed",
  "video_url": "https://..."
}
```

---

## Sessions (`/api/sessions`)

### GET `/api/sessions/`
**List all sessions for current user**

Query parameters:
- `limit`: Maximum sessions to return (default 10)
- `offset`: Number of sessions to skip (default 0)

Headers:
- `Authorization: Bearer <token>`

Response:
```json
[
  {
    "id": "uuid-string",
    "status": "completed",
    "prompt": "man buys hat",
    "video_prompt": "elegant hat showcase",
    "final_video_url": "https://...",
    "created_at": "2025-01-15T10:30:00",
    "completed_at": "2025-01-15T10:35:00",
    "assets": [
      {
        "id": 1,
        "type": "image",
        "url": "https://...",
        "approved": true,
        "order_index": null,
        "created_at": "2025-01-15T10:31:00"
      }
    ]
  }
]
```

### GET `/api/sessions/{session_id}`
**Get detailed information about a session**

Headers:
- `Authorization: Bearer <token>`

Response: Same as session object above.

### GET `/api/sessions/{session_id}/costs`
**Get cost breakdown for a session**

Headers:
- `Authorization: Bearer <token>`

Response:
```json
{
  "session_id": "uuid-string",
  "total_cost": 0.25,
  "breakdown": [
    {
      "service": "replicate_flux",
      "cost": 0.012,
      "tokens_used": null,
      "details": {
        "model": "flux-schnell",
        "num_images": 4
      }
    },
    {
      "service": "replicate_luma",
      "cost": 0.24,
      "tokens_used": null,
      "details": {
        "model": "gen-4-turbo",
        "duration_seconds": 16
      }
    }
  ]
}
```

---

## Storage (`/api/storage`)

### POST `/api/storage/upload-input`
**Upload a file to user's input folder**

Headers:
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

Request (multipart/form-data):
- `file`: File to upload

Response:
```json
{
  "url": "https://...",
  "key": "users/1/input/filename.jpg",
  "size": 102400,
  "content_type": "image/jpeg",
  "original_filename": "filename.jpg"
}
```

### POST `/api/storage/upload-prompt-config`
**Store prompt configuration as JSON**

Creates a file named `prompt-{session_id}.json` in user's input folder.

Headers:
- `Authorization: Bearer <token>`

Request:
```json
{
  "config_data": {
    "prompt": "man buys hat",
    "num_images": 4,
    "aspect_ratio": "16:9"
  },
  "session_id": "uuid-string"
}
```

Response:
```json
{
  "status": "success",
  "key": "users/1/input/prompt-uuid.json",
  "session_id": "uuid-string"
}
```

### GET `/api/storage/files`
**List files in user's folders**

Query parameters:
- `folder`: `input` or `output` (required)
- `asset_type`: Filter for output folder (`images`, `videos`, `final`, `audio`) - optional
- `limit`: Maximum files to return (default 100)
- `offset`: Number of files to skip (default 0)

Headers:
- `Authorization: Bearer <token>`

Response:
```json
{
  "files": [
    {
      "key": "users/1/output/images/image1.png",
      "size": 204800,
      "last_modified": "2025-01-15T10:31:00",
      "content_type": "image/png",
      "presigned_url": "https://..."
    }
  ],
  "total": 10,
  "limit": 100,
  "offset": 0
}
```

### GET `/api/storage/files/{file_key}/presigned-url`
**Get presigned URL for accessing a file**

Path parameters:
- `file_key`: S3 key of the file (e.g., `users/1/output/images/image1.png`)

Query parameters:
- `expires_in`: URL expiration time in seconds (default 3600)

Headers:
- `Authorization: Bearer <token>`

Response:
```json
{
  "presigned_url": "https://...",
  "expires_in": 3600
}
```

### DELETE `/api/storage/files/{file_key}`
**Delete a file from user's folders**

Path parameters:
- `file_key`: S3 key of the file

Headers:
- `Authorization: Bearer <token>`

Response:
```json
{
  "status": "success",
  "message": "File deleted successfully",
  "key": "users/1/input/file.jpg"
}
```

---

## WebSocket (`/ws/{session_id}`)

Real-time progress updates during generation.

### Connection
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data);
};
```

### Message Format
```json
{
  "event": "image_generation_progress",
  "session_id": "uuid-string",
  "progress": 0.5,
  "message": "Generating image 2 of 4"
}
```

---

## Error Responses

All endpoints may return the following error formats:

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
```json
{
  "detail": "Session not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Image generation failed"
}
```

---

## Notes

- All generation endpoints actually call Replicate services - they are **not stubbed**
- Images are generated using Flux-Schnell
- Videos are generated using Gen-4-Turbo
- All assets are stored in AWS S3
- WebSocket connections provide real-time progress updates
- Session data and costs are tracked in PostgreSQL (Neon)
