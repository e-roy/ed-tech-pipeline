# Technical Architecture Document
## AI Ad Video Generator - Implementation Blueprint

**Version:** 1.0
**Date:** November 14, 2025
**Architect:** Winston (System Architect Agent)
**Status:** Implementation-Ready
**Sprint Duration:** 48 Hours

---

## Table of Contents

1. [Critical Architecture Decisions](#1-critical-architecture-decisions)
2. [File Storage Architecture](#2-file-storage-architecture)
3. [FFmpeg Composition Layer](#3-ffmpeg-composition-layer)
4. [WebSocket Architecture](#4-websocket-architecture)
5. [Error Recovery Strategy](#5-error-recovery-strategy)
6. [Authentication & Security](#6-authentication--security)
7. [System Integration Flows](#7-system-integration-flows)
8. [Performance Optimization](#8-performance-optimization)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Risk Mitigation](#10-risk-mitigation)

---

## 1. Critical Architecture Decisions

### 1.1 Why Image-to-Video Instead of Text-to-Video?

**Decision:** Use Image Generation → Image-to-Video pipeline

**Rationale:**
- **Visual Consistency:** Text-to-video models hallucinate product details (wrong colors, logo placement, etc.)
- **User Control:** Users can approve/reject images before expensive video generation
- **Cost Efficiency:** Fix product appearance early (images are $0.05 vs videos at $0.80)
- **Quality:** Flux-Pro produces better product photography than any text-to-video model

**Trade-off:** Adds one extra workflow step, but saves $$ and improves quality

---

### 1.2 Direct Function Calls vs Message Queue

**Decision:** Use direct async function calls for MVP

**Why NOT a message queue (for MVP)?**

| Consideration | Message Queue | Direct Calls (MVP) |
|--------------|---------------|-------------------|
| **Implementation Time** | 8-12 hours | 2 hours |
| **Complexity** | High (RabbitMQ, workers, retry logic) | Low (native async/await) |
| **Debugging** | Difficult (distributed tracing) | Easy (single process logs) |
| **Scalability** | Excellent (1000s of concurrent jobs) | Good enough (10-50 concurrent) |
| **MVP Fit** | Overkill | Perfect |

**Migration Path:** Architecture is designed to swap in Redis/RabbitMQ post-MVP (Agent interface is queue-ready)

---

### 1.3 PostgreSQL vs NoSQL for Session State

**Decision:** PostgreSQL with JSONB

**Rationale:**
- Session state is **relational** (sessions → assets → costs)
- ACID guarantees prevent race conditions (concurrent asset updates)
- JSONB provides NoSQL flexibility where needed (metadata)
- Railway provides managed PostgreSQL (one less service to manage)

**Alternative Considered:** MongoDB - rejected due to weak relational queries

---

## 2. File Storage Architecture

### 2.1 Asset Flow: Replicate → S3 → Frontend

**Problem:** Replicate URLs expire after 24 hours. We need persistent storage.

```
┌──────────────────────────────────────────────────────────────────┐
│                      ASSET FLOW PIPELINE                          │
└──────────────────────────────────────────────────────────────────┘

1. GENERATION PHASE
   Replicate API
        ↓ (generates asset)
   Temporary Replicate URL
   (expires in 24h)
        ↓
   Backend downloads to /tmp
        ↓
   Upload to S3/R2
        ↓
   Save permanent URL to database

2. DELIVERY PHASE
   Frontend requests asset
        ↓
   Backend generates signed URL (valid 1 hour)
        ↓
   Frontend displays from S3
```

### 2.2 Storage Service Implementation

```python
# backend/services/storage.py
import boto3
import httpx
from typing import BinaryIO
from pathlib import Path

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name='us-east-1'
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')

    async def download_and_upload(
        self,
        replicate_url: str,
        asset_type: str,  # 'image', 'video', 'audio'
        session_id: str,
        asset_id: str
    ) -> dict:
        """Download from Replicate and upload to S3"""

        # 1. Download from Replicate to temp file
        temp_path = f"/tmp/{asset_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(replicate_url)
            response.raise_for_status()

            with open(temp_path, 'wb') as f:
                f.write(response.content)

        # 2. Determine file extension
        content_type = response.headers.get('content-type')
        extension = self._get_extension(content_type, asset_type)

        # 3. Build S3 key with organization
        s3_key = f"sessions/{session_id}/{asset_type}s/{asset_id}{extension}"

        # 4. Upload to S3
        file_size = Path(temp_path).stat().st_size
        self.s3_client.upload_file(
            temp_path,
            self.bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'max-age=31536000',  # 1 year
            }
        )

        # 5. Clean up temp file
        Path(temp_path).unlink()

        # 6. Return permanent URL
        return {
            'url': f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}",
            'storage_path': s3_key,
            'file_size_bytes': file_size,
            'mime_type': content_type
        }

    def generate_presigned_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Generate signed URL for secure frontend access"""
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': storage_path
            },
            ExpiresIn=expires_in  # 1 hour default
        )

    def _get_extension(self, content_type: str, asset_type: str) -> str:
        mapping = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'video/mp4': '.mp4',
            'audio/mpeg': '.mp3',
            'audio/wav': '.wav'
        }
        return mapping.get(content_type, f".{asset_type}")
```

### 2.3 S3 Bucket Configuration

**Bucket Structure:**
```
ai-ad-videos-mvp/
├── sessions/
│   ├── {session-uuid}/
│   │   ├── images/
│   │   │   ├── {asset-uuid}.png
│   │   │   └── {asset-uuid}.png
│   │   ├── videos/
│   │   │   ├── {asset-uuid}.mp4
│   │   │   └── {asset-uuid}.mp4
│   │   ├── audio/
│   │   │   └── {asset-uuid}.mp3
│   │   └── final/
│   │       └── {final-video-uuid}.mp4
```

**Bucket Policy (S3):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::ai-ad-videos-mvp/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": [
            "YOUR_BACKEND_IP/32",
            "VERCEL_IP_RANGE"
          ]
        }
      }
    }
  ]
}
```

**Lifecycle Policy (Auto-cleanup):**
```json
{
  "Rules": [
    {
      "Id": "DeleteOldSessions",
      "Status": "Enabled",
      "Prefix": "sessions/",
      "Expiration": {
        "Days": 30
      }
    }
  ]
}
```

### 2.4 Alternative: Cloudflare R2 (Lower Cost)

**Cost Comparison (per 1000 videos):**
- S3: ~$0.023/GB storage + $0.09/GB egress = **$2.30**
- R2: ~$0.015/GB storage + **$0 egress** = **$0.38**

**R2 Setup:**
```python
# backend/services/storage.py (R2 variant)
self.s3_client = boto3.client(
    's3',
    endpoint_url=f'https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com',
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name='auto'  # R2 uses 'auto'
)
```

**Recommendation:** Use R2 for production (80% cost savings on storage)

---

## 3. FFmpeg Composition Layer

### 3.1 Core Challenge

**Problem:** Stitch 2-6 video clips with:
- Text overlays (product name + CTA)
- Background music
- Smooth transitions
- Consistent resolution (1080p)

### 3.2 FFmpeg Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               FFMPEG COMPOSITION PIPELINE                    │
└─────────────────────────────────────────────────────────────┘

INPUT:
- 4 video clips (1024x576, 3s each, different FPS)
- Background music (60s MP3)
- Text overlay config (product name, CTA, color, font)

STEPS:
1. Normalize clips (scale to 1080p, standardize FPS to 30)
2. Create concat file
3. Add text overlays with drawtext filter
4. Mix audio (clips + background music)
5. Encode final MP4 (H.264, AAC audio)

OUTPUT:
- final_video.mp4 (1920x1080, 30fps, H.264)
```

### 3.3 Working FFmpeg Commands

#### Step 1: Normalize Individual Clips

```bash
# Normalize each clip to 1080p @ 30fps
ffmpeg -i clip_001.mp4 \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30" \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  normalized_001.mp4
```

**Explanation:**
- `scale=1920:1080:force_original_aspect_ratio=increase` → Scale up/down
- `crop=1920:1080` → Crop to exact size if aspect ratio doesn't match
- `fps=30` → Standardize frame rate
- `crf 23` → Quality (18=high quality, 28=lower quality)
- `movflags +faststart` → Enable streaming (metadata at start)

#### Step 2: Create Concat File

```bash
# concat_list.txt
file 'normalized_001.mp4'
file 'normalized_002.mp4'
file 'normalized_003.mp4'
file 'normalized_004.mp4'
```

#### Step 3: Concatenate Clips

```bash
ffmpeg -f concat -safe 0 -i concat_list.txt \
  -c copy \
  concatenated.mp4
```

#### Step 4: Add Text Overlays

```bash
ffmpeg -i concatenated.mp4 \
  -vf "drawtext=text='AirRun Pro':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=72:fontcolor=white:x=(w-text_w)/2:y=100:enable='between(t,1,3)',
       drawtext=text='Shop Now':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:fontsize=48:fontcolor=yellow:x=(w-text_w)/2:y=900:enable='between(t,8,10)'" \
  -c:v libx264 -preset fast -crf 23 \
  -c:a copy \
  with_text.mp4
```

**Explanation:**
- First `drawtext`: Product name (center top, seconds 1-3)
- Second `drawtext`: CTA (center bottom, seconds 8-10)
- `enable='between(t,1,3)'` → Show only during time range

#### Step 5: Add Background Music

```bash
ffmpeg -i with_text.mp4 -i background_music.mp3 \
  -filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.3,afade=t=out:st=9:d=1[a1];[a0][a1]amix=inputs=2:duration=first[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k \
  final_video.mp4
```

**Explanation:**
- `[0:a]volume=1.0` → Keep original video audio at 100%
- `[1:a]volume=0.3` → Background music at 30%
- `afade=t=out:st=9:d=1` → Fade out music 1 second before end
- `amix=inputs=2` → Mix both audio tracks

### 3.4 Python Implementation

```python
# backend/agents/composition_agent.py
import subprocess
import tempfile
from pathlib import Path

class CompositionAgent:
    def __init__(self):
        self.ffmpeg_path = "ffmpeg"  # Assumes ffmpeg in PATH

    async def compose_final_video(
        self,
        clips: list[dict],
        text_config: dict,
        audio_config: dict,
        output_path: str
    ) -> dict:
        """Compose final video from clips"""

        start_time = time.time()

        # 1. Download clips to temp directory
        temp_dir = tempfile.mkdtemp()
        clip_paths = []

        for i, clip in enumerate(clips):
            clip_path = Path(temp_dir) / f"clip_{i:03d}.mp4"
            await self._download_file(clip['url'], clip_path)
            clip_paths.append(clip_path)

        # 2. Normalize clips
        normalized_paths = []
        for i, clip_path in enumerate(clip_paths):
            normalized_path = Path(temp_dir) / f"normalized_{i:03d}.mp4"
            await self._normalize_clip(clip_path, normalized_path)
            normalized_paths.append(normalized_path)

        # 3. Create concat file
        concat_file = Path(temp_dir) / "concat_list.txt"
        with open(concat_file, 'w') as f:
            for path in normalized_paths:
                f.write(f"file '{path}'\n")

        # 4. Concatenate
        concatenated = Path(temp_dir) / "concatenated.mp4"
        await self._concatenate_clips(concat_file, concatenated)

        # 5. Add text overlays
        with_text = Path(temp_dir) / "with_text.mp4"
        await self._add_text_overlays(concatenated, with_text, text_config)

        # 6. Add background music (if enabled)
        if audio_config.get('enabled'):
            music_path = await self._download_music(audio_config['url'], temp_dir)
            await self._add_background_music(with_text, music_path, output_path)
        else:
            # Just copy if no music
            shutil.copy(with_text, output_path)

        # 7. Cleanup temp files
        shutil.rmtree(temp_dir)

        duration = time.time() - start_time
        file_size = Path(output_path).stat().st_size

        return {
            'success': True,
            'output_path': output_path,
            'duration_seconds': duration,
            'file_size_bytes': file_size,
            'resolution': '1920x1080',
            'estimated_cost': 0.50  # FFmpeg processing cost estimate
        }

    async def _normalize_clip(self, input_path: Path, output_path: Path):
        """Normalize clip to 1080p @ 30fps"""
        cmd = [
            self.ffmpeg_path,
            '-i', str(input_path),
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',  # Overwrite output
            str(output_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg normalization failed: {stderr.decode()}")

    async def _add_text_overlays(self, input_path: Path, output_path: Path, text_config: dict):
        """Add text overlays with drawtext filter"""

        # Build drawtext filters
        filters = []

        # Product name (show for first 3 seconds)
        if text_config.get('product_name'):
            filters.append(
                f"drawtext=text='{text_config['product_name']}':"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                f"fontsize=72:"
                f"fontcolor={text_config.get('text_color', 'white')}:"
                f"x=(w-text_w)/2:y=100:"
                f"enable='between(t,1,3)'"
            )

        # CTA (show for last 2 seconds)
        if text_config.get('call_to_action'):
            video_duration = await self._get_duration(input_path)
            start_time = video_duration - 2

            filters.append(
                f"drawtext=text='{text_config['call_to_action']}':"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                f"fontsize=48:"
                f"fontcolor=yellow:"
                f"x=(w-text_w)/2:y=900:"
                f"enable='between(t,{start_time},{video_duration})'"
            )

        vf_filter = ','.join(filters) if filters else 'null'

        cmd = [
            self.ffmpeg_path,
            '-i', str(input_path),
            '-vf', vf_filter,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'copy',
            '-y',
            str(output_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg text overlay failed: {stderr.decode()}")

    async def _get_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        return float(stdout.decode().strip())
```

### 3.5 FFmpeg Installation (Railway Dockerfile)

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . /app
WORKDIR /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 4. WebSocket Architecture

### 4.1 Connection Management

**Challenge:** Map `session_id` → WebSocket connection for real-time progress updates

```python
# backend/services/websocket_manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio
import json

class WebSocketManager:
    def __init__(self):
        # session_id → list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.connection_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection and register it"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = []

        self.active_connections[session_id].append(websocket)

        # Start heartbeat task
        task = asyncio.create_task(self._heartbeat(websocket, session_id))
        self.connection_tasks[id(websocket)] = task

        print(f"✅ WebSocket connected: session={session_id}, total={len(self.active_connections[session_id])}")

    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)

            # Clean up empty session
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

        # Cancel heartbeat task
        task = self.connection_tasks.pop(id(websocket), None)
        if task:
            task.cancel()

        print(f"❌ WebSocket disconnected: session={session_id}")

    async def send_progress(self, session_id: str, message: dict):
        """Send progress update to all connections for a session"""
        if session_id not in self.active_connections:
            return

        # Convert to JSON
        json_message = json.dumps(message)

        # Send to all connections (supports multiple browser tabs)
        dead_connections = []

        for connection in self.active_connections[session_id]:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                print(f"⚠️ Failed to send to connection: {e}")
                dead_connections.append(connection)

        # Clean up dead connections
        for connection in dead_connections:
            await self.disconnect(connection, session_id)

    async def _heartbeat(self, websocket: WebSocket, session_id: str):
        """Send periodic pings to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(30)  # Ping every 30 seconds
                await websocket.send_json({"type": "ping"})
        except Exception:
            # Connection closed
            await self.disconnect(websocket, session_id)

# Global instance
ws_manager = WebSocketManager()
```

### 4.2 FastAPI WebSocket Endpoint

```python
# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await ws_manager.connect(websocket, session_id)

    try:
        while True:
            # Receive messages from client (for heartbeat pong)
            data = await websocket.receive_text()

            # Handle pong responses
            if data == "pong":
                continue

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, session_id)
```

### 4.3 Frontend WebSocket Hook

```typescript
// frontend/hooks/useWebSocket.ts
'use client'

import { useEffect, useState, useRef, useCallback } from 'react'

interface ProgressUpdate {
  stage: string
  progress: number
  message: string
  current_cost?: number
}

export function useWebSocket(sessionId: string) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<ProgressUpdate | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectAttempts = useRef(0)

  const connect = useCallback(() => {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/${sessionId}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('✅ WebSocket connected')
      setIsConnected(true)
      reconnectAttempts.current = 0
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      // Handle ping
      if (data.type === 'ping') {
        ws.send('pong')
        return
      }

      // Handle progress updates
      setLastMessage(data)
    }

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('🔌 WebSocket disconnected')
      setIsConnected(false)

      // Auto-reconnect with exponential backoff
      if (reconnectAttempts.current < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
        console.log(`🔄 Reconnecting in ${delay}ms...`)

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++
          connect()
        }, delay)
      }
    }

    wsRef.current = ws
  }, [sessionId])

  useEffect(() => {
    connect()

    return () => {
      // Cleanup on unmount
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [connect])

  return { isConnected, lastMessage }
}
```

### 4.4 WebSocket Message Format

```typescript
// Progress update messages
{
  "stage": "image_generation",
  "progress": 45,
  "message": "Generating image 3 of 6...",
  "current_cost": 0.15,
  "metadata": {
    "current_image": 3,
    "total_images": 6,
    "model": "flux-pro"
  }
}

// Error messages
{
  "stage": "image_generation",
  "progress": 45,
  "message": "Generation failed",
  "error": "Replicate API timeout",
  "retry_available": true
}

// Completion messages
{
  "stage": "complete",
  "progress": 100,
  "message": "Images ready for review!",
  "current_cost": 0.30,
  "asset_count": 6
}
```

---

## 5. Error Recovery Strategy

### 5.1 Error Categories & Handling

| Error Type | Example | Recovery Strategy | User Impact |
|-----------|---------|-------------------|-------------|
| **Replicate API Timeout** | Request takes >5min | Retry once after 30s delay | Show "Retrying..." message |
| **Replicate Rate Limit** | 429 Too Many Requests | Wait 60s, then retry | Show "Server busy, retrying..." |
| **NSFW Filter Triggered** | Image flagged as inappropriate | Modify prompt, retry once | Show "Please modify your prompt" |
| **Partial Generation Failure** | 3/6 images succeed | Continue with successful images | Show warning, allow proceeding |
| **FFmpeg Crash** | Out of memory | Reduce resolution, retry | Show error, suggest shorter video |
| **S3 Upload Failure** | Network timeout | Retry 3 times with backoff | Show upload progress |
| **Database Connection Lost** | PostgreSQL restart | Reconnect with exponential backoff | Show "Reconnecting..." |
| **WebSocket Disconnect** | Network issue | Auto-reconnect (see 4.3) | Show "Connection lost" banner |

### 5.2 Retry Logic Implementation

```python
# backend/utils/retry.py
import asyncio
import functools
from typing import Callable, Any

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """Retry function with exponential backoff"""

    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            if attempt == max_retries - 1:
                # Last attempt failed, raise error
                raise

            print(f"⚠️ Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay *= backoff_factor

# Usage in agents
async def generate_image_with_retry(prompt_data):
    return await retry_with_backoff(
        lambda: replicate_api.generate_image(prompt_data),
        max_retries=3,
        exceptions=(ReplicateAPIError, httpx.TimeoutException)
    )
```

### 5.3 Session Recovery

**Problem:** User closes browser during generation. How to resume?

**Solution:** Session state is persisted in PostgreSQL at every stage

```python
# backend/services/session_recovery.py

class SessionRecoveryService:
    async def resume_session(self, session_id: str):
        """Resume a session from database state"""

        session = await db.get_session(session_id)

        # Check session status and resume at appropriate stage
        if session.status == 'generating_images':
            # Check which images completed
            completed_images = await db.get_assets(
                session_id=session_id,
                type='image',
                status='completed'
            )

            if len(completed_images) < session.num_images_requested:
                # Resume image generation
                return await orchestrator.resume_image_generation(session_id)
            else:
                # Move to next stage
                return await orchestrator.start_image_review(session_id)

        elif session.status == 'generating_videos':
            # Similar logic for video generation
            pass

        elif session.status == 'composing':
            # Check if composition completed
            pass

        return {"status": "ready", "session": session}
```

### 5.4 Cost Budget Protection

```python
# backend/utils/cost_guard.py

class CostGuard:
    MAX_COST_PER_SESSION = 200.00  # $200 budget

    async def check_budget(self, session_id: str, estimated_next_cost: float):
        """Check if adding next operation exceeds budget"""

        session = await db.get_session(session_id)
        projected_total = session.total_cost + estimated_next_cost

        if projected_total > self.MAX_COST_PER_SESSION:
            raise BudgetExceededException(
                f"Operation would exceed budget: ${projected_total:.2f} > ${self.MAX_COST_PER_SESSION}"
            )

# Usage in orchestrator
await cost_guard.check_budget(session_id, estimated_cost=2.40)  # Before video generation
```

---

## 6. Authentication & Security

### 6.1 MVP Authentication Strategy

**Decision:** Simple JWT authentication with demo user

```python
# backend/auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def authenticate_user(email: str, password: str):
    user = await db.get_user_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
```

### 6.2 Login Endpoint

```python
# backend/routes/auth.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/api/auth/login")
async def login(credentials: LoginRequest):
    user = await authenticate_user(credentials.email, credentials.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }
```

### 6.3 Protected Endpoint Example

```python
# backend/utils/auth_middleware.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.get_user(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Usage in routes
@router.post("/api/generate-images")
async def generate_images(
    request: GenerateImagesRequest,
    current_user = Depends(get_current_user)
):
    # Only authenticated users can access
    session = await orchestrator.generate_images(
        user_id=current_user.id,
        prompt=request.prompt
    )
    return session
```

### 6.4 Frontend Auth Flow

```typescript
// frontend/lib/auth.ts
export async function login(email: string, password: string) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })

  if (!response.ok) {
    throw new Error('Login failed')
  }

  const data = await response.json()

  // Store token in localStorage
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('user', JSON.stringify(data.user))

  return data
}

export function getAuthToken(): string | null {
  return localStorage.getItem('access_token')
}

export function isAuthenticated(): boolean {
  return !!getAuthToken()
}

// API client with auth
export async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken()

  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  }

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers
  })

  if (response.status === 401) {
    // Token expired, redirect to login
    localStorage.removeItem('access_token')
    window.location.href = '/login'
  }

  return response
}
```

### 6.5 Security Checklist

- [x] JWT tokens with expiration (24 hours)
- [x] Password hashing with bcrypt (cost factor 12)
- [x] HTTPS only (enforced by Vercel/Railway)
- [x] CORS configured (whitelist frontend domain)
- [x] API rate limiting (to prevent abuse of Replicate budget)
- [x] Input validation with Pydantic
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] XSS prevention (React escapes by default)
- [ ] CSRF tokens (not needed for JWT bearer tokens)
- [ ] API key rotation strategy (post-MVP)

---

## 7. System Integration Flows

### 7.1 Complete Image Generation Flow

```
USER                FRONTEND            BACKEND             REPLICATE          DATABASE
  │                    │                   │                    │                 │
  │  1. Enter prompt   │                   │                    │                 │
  ├───────────────────>│                   │                    │                 │
  │                    │                   │                    │                 │
  │                    │ 2. POST /api/generate-images          │                 │
  │                    ├──────────────────>│                    │                 │
  │                    │                   │                    │                 │
  │                    │                   │ 3. Create session  │                 │
  │                    │                   ├───────────────────────────────────>│
  │                    │                   │                    │                 │
  │                    │                   │ 4. Call Prompt Parser Agent         │
  │                    │                   ├───────────────────>│                 │
  │                    │                   │                    │                 │
  │                    │                   │ 5. Parse prompt (LLM)               │
  │                    │                   │<───────────────────┤                 │
  │                    │                   │                    │                 │
  │                    │                   │ 6. Save consistency_seed            │
  │                    │                   ├───────────────────────────────────>│
  │                    │                   │                    │                 │
  │                    │                   │ 7. Loop: Generate 6 images          │
  │                    │                   │ ┌──────────────────────────────┐    │
  │                    │                   │ │ For each image:              │    │
  │                    │                   │ │  - Call Flux-Pro API         │    │
  │                    │                   ├─┤  - Download from Replicate   │    │
  │                    │                   │ │  - Upload to S3              │    │
  │                    │                   │ │  - Save asset to DB          │    │
  │                    │                   │ │  - Send WebSocket progress   │    │
  │                    │<──────────────────┼─┤  - Track cost                │    │
  │  Progress update   │                   │ └──────────────────────────────┘    │
  │<───────────────────┤                   │                    │                 │
  │  "Image 3 of 6"    │                   │                    │                 │
  │                    │                   │                    │                 │
  │                    │                   │ 8. All images complete              │
  │                    │                   ├───────────────────────────────────>│
  │                    │                   │                    │                 │
  │                    │ 9. Return image URLs                   │                 │
  │                    │<──────────────────┤                    │                 │
  │                    │                   │                    │                 │
  │ 10. Display images │                   │                    │                 │
  │<───────────────────┤                   │                    │                 │
```

### 7.2 Video Generation Flow (with Scene Planning)

```
FRONTEND            ORCHESTRATOR        PROMPT PARSER      IMAGE GEN         VIDEO GEN
   │                     │                    │                │                 │
   │ POST /api/          │                    │                │                 │
   │ generate-clips      │                    │                │                 │
   ├────────────────────>│                    │                │                 │
   │                     │                    │                │                 │
   │                     │ 1. Get approved    │                │                 │
   │                     │    images from DB  │                │                 │
   │                     │                    │                │                 │
   │                     │ 2. Call LLM to plan scenes         │                 │
   │                     ├───────────────────>│                │                 │
   │                     │                    │                │                 │
   │                     │ 3. Scene prompts   │                │                 │
   │                     │<───────────────────┤                │                 │
   │                     │  (front view:      │                │                 │
   │                     │   "running motion" │                │                 │
   │                     │   side view:       │                │                 │
   │                     │   "slow pan")      │                │                 │
   │                     │                    │                │                 │
   │                     │ 4. For each approved image:         │                 │
   │                     │    ┌────────────────────────────────────────────┐    │
   │                     │    │ - Get image URL from DB                    │    │
   │                     │    │ - Match to scene prompt                    │    │
   │                     │    │ - Call Stable Video Diffusion             │─┐  │
   │                     │    │   (image-to-video)                        │ │  │
   │                     │    │ - Download video from Replicate           │ │  │
   │                     │    │ - Upload to S3                            │<┘  │
   │                     │    │ - Save to DB                              │    │
   │                     │    │ - Send WebSocket update                   │    │
   │<────────────────────┼────┤ - Track cost                              │    │
   │ Progress: "Clip 2/4"│    └────────────────────────────────────────────┘    │
   │                     │                    │                │                 │
   │                     │ 5. Return clip URLs                 │                 │
   │<────────────────────┤                    │                │                 │
   │                     │                    │                │                 │
   │ Display clips       │                    │                │                 │
```

---

## 8. Performance Optimization

### 8.1 Critical Path Analysis

**Total Time Budget: 48 hours**

| Task | Estimated Time | Risk Level | Mitigation |
|------|---------------|------------|------------|
| Database schema implementation | 2 hours | Low | Schema is ready ✅ |
| FastAPI backend setup | 3 hours | Low | Standard pattern |
| Next.js frontend setup | 3 hours | Low | Standard pattern |
| Replicate API integration | 4 hours | Medium | Test with mock data first |
| FFmpeg composition | 6 hours | **HIGH** | Prototype commands ASAP ⚠️ |
| WebSocket implementation | 3 hours | Medium | Use standard patterns |
| S3/R2 integration | 2 hours | Low | boto3 is well-documented |
| UI components | 8 hours | Medium | Use Tailwind + shadcn/ui |
| Testing & debugging | 10 hours | High | Reserve for unknowns |
| Deployment | 4 hours | Medium | Railway + Vercel are fast |
| **BUFFER** | 3 hours | - | Padding for issues |

### 8.2 Parallelization Strategy

**Hour 0-4: Foundation (Parallel Tracks)**
- Track 1: Backend dev sets up FastAPI + DB
- Track 2: Frontend dev sets up Next.js + UI skeleton
- Track 3: DevOps sets up Railway + Vercel

**Hour 4-12: Core Features (Parallel)**
- Track 1: Backend implements image generation flow
- Track 2: Frontend builds image generation UI
- Track 3: Test FFmpeg commands manually

**Hour 12-24: Video Generation**
- Track 1: Backend implements video generation + FFmpeg
- Track 2: Frontend builds video UI + WebSocket
- Track 3: Integration testing

**Hour 24-40: Polish & Testing**
- All hands on deck for integration testing
- Bug fixes
- Cost tracking verification

**Hour 40-48: Deploy & Demo**
- Production deployment
- Demo video recording
- Documentation

### 8.3 API Response Time Targets

| Endpoint | Target | Actual (Expected) | Notes |
|----------|--------|-------------------|-------|
| POST /api/auth/login | <200ms | ~150ms | Database query |
| POST /api/generate-images | <2s (initial response) | ~1.5s | Async job, returns immediately |
| GET /api/sessions/{id} | <300ms | ~200ms | Single DB query with joins |
| POST /api/generate-clips | <2s (initial response) | ~1.5s | Async job |
| POST /api/compose-final | <5s | ~3s | Kicks off FFmpeg job |
| WebSocket /ws/{session_id} | <100ms (connect) | ~50ms | Persistent connection |

---

## 9. Deployment Architecture

### 9.1 Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │      VERCEL CDN EDGE         │
          │   (Next.js Frontend)         │
          │   - Static assets            │
          │   - SSR for initial load     │
          │   - Auto HTTPS               │
          └──────────────┬───────────────┘
                         │
                         │ HTTPS
                         ▼
          ┌──────────────────────────────┐
          │    RAILWAY (Backend API)     │
          │   - FastAPI application      │
          │   - WebSocket server         │
          │   - FFmpeg processing        │
          │   - Auto HTTPS               │
          └──────┬───────────────┬───────┘
                 │               │
                 │               │
    ┌────────────▼───┐      ┌───▼─────────────┐
    │  RAILWAY       │      │  CLOUDFLARE R2  │
    │  POSTGRESQL    │      │  (File Storage) │
    │  - Sessions    │      │  - Images       │
    │  - Assets      │      │  - Videos       │
    │  - Costs       │      │  - Audio        │
    └────────────────┘      └─────────────────┘
                                     │
                 ┌───────────────────┤
                 │                   │
          ┌──────▼──────┐     ┌─────▼────────┐
          │  REPLICATE  │     │  REPLICATE   │
          │  Flux-Pro   │     │  Stable      │
          │  (Images)   │     │  Video Diff  │
          └─────────────┘     └──────────────┘
```

### 9.2 Railway Configuration

**railway.toml**
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[deploy.environmentVariables]]
name = "PYTHON_VERSION"
value = "3.11"
```

**backend/Dockerfile**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations on startup (optional)
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### 9.3 Vercel Configuration

**vercel.json**
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "@api_url",
    "NEXT_PUBLIC_WS_URL": "@ws_url"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        }
      ]
    }
  ]
}
```

### 9.4 Environment Variables Checklist

**Backend (Railway)**
```bash
# API Keys
REPLICATE_API_KEY=r8_xxx
AWS_ACCESS_KEY_ID=AKIA_xxx
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET_NAME=ai-ad-videos-mvp

# Database (auto-provided by Railway)
DATABASE_URL=postgresql://xxx

# JWT
JWT_SECRET_KEY=xxx  # Generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256

# CORS
FRONTEND_URL=https://your-app.vercel.app

# Environment
ENV=production
```

**Frontend (Vercel)**
```bash
NEXT_PUBLIC_API_URL=https://your-api.railway.app
NEXT_PUBLIC_WS_URL=wss://your-api.railway.app
```

---

## 10. Risk Mitigation

### 10.1 Critical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **FFmpeg doesn't work on Railway** | High (no final video) | Medium | Test FFmpeg in Railway staging environment TODAY |
| **Replicate API rate limits** | High (can't generate) | Low | Pre-purchase credits, implement exponential backoff |
| **Video generation too slow (>5min/clip)** | Medium (poor UX) | Medium | Set timeout at 3min, show clear progress |
| **Database connection pool exhausted** | Medium (API errors) | Low | Use pgBouncer, set max_connections=20 |
| **S3 costs exceed budget** | Low (operational cost) | Low | Use Cloudflare R2 (free egress) |
| **WebSocket doesn't work through Vercel** | Medium (no progress UI) | Low | Vercel supports WebSockets, test early |
| **Text overlay fonts missing on Railway** | Low (fallback works) | Medium | Bundle fonts in Docker image |

### 10.2 Technical Unknowns (Prototype ASAP)

1. **FFmpeg text overlay with custom fonts** → Test in next 2 hours ⚠️
2. **Replicate Stable Video Diffusion quality** → Generate sample video with test image
3. **Railway cold start time** → Test WebSocket reconnection
4. **Next.js WebSocket handling** → Build minimal example

### 10.3 Contingency Plans

**If FFmpeg fails:**
- Fallback: Use Replicate's video composition API (if available)
- Nuclear option: Ship without text overlays for MVP

**If Replicate rate limits:**
- Use SDXL instead of Flux-Pro (cheaper, faster)
- Reduce default image count from 6 → 4

**If video generation too slow:**
- Add "estimated time" indicator (3-5 minutes)
- Allow users to queue multiple sessions

---

## Appendix: Quick Start Commands

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Database (local)
docker run --name postgres-mvp \
  -e POSTGRES_PASSWORD=dev123 \
  -e POSTGRES_DB=ai_ad_generator \
  -p 5432:5432 \
  -d postgres:15
```

### Testing FFmpeg

```bash
# Test video stitching
ffmpeg -f concat -safe 0 -i test_concat.txt \
  -c copy output.mp4

# Test text overlay
ffmpeg -i input.mp4 \
  -vf "drawtext=text='TEST':fontsize=72:x=100:y=100" \
  output_with_text.mp4
```

---

**Architecture Status:** ✅ **Ready for Implementation**

**Next Steps:**
1. ✅ Review database schema
2. 🔄 Prototype FFmpeg commands (in progress)
3. ⏳ Start backend implementation
4. ⏳ Start frontend implementation

**Estimated Implementation Time:** 44 hours (with 4-hour buffer)
