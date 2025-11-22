# 🎬 Video Generation & Stitching Workflow (OpenAI + AWS)

## Overview
This workflow describes how to generate short video clips using OpenAI models, replace audio with narration, and stitch them together into a final MP4 video using AWS MediaConvert. Logs are sent to CloudWatch for monitoring.

---

## Inputs
- `storyboard.json` (strict schema)
  - `id`: segment identifier
  - `duration`: length of segment in seconds
  - `narration`: narration text (audio provided separately)
  - `visual_guidance`: prompt for visuals
  - `start_time`: timeline alignment
- Narration audio files (WAV/MP3)
- Target video format: **MP4, H.264, 1080p, fixed bitrate**

---

## Workflow Steps

### 1. Parse Storyboard
- Agent reads `segments[]` from `storyboard.json`.
- Each segment defines narration, duration, and visual guidance.

### 2. Generate Clips (OpenAI)
- Use `visual_guidance` → OpenAI image/video generation.
- Enforce:
  - Format: MP4
  - Resolution: 1920x1080
  - Bitrate: 5000k
- Replace any generated audio with provided narration.
- Sync narration to `duration` (trim/pad if needed).
- Save each clip to **AWS S3**.

### 3. Stitch Clips (AWS MediaConvert)
- Concatenate clips into one final video.
- Parameters:
  - `concat_mode`: `"simple"` (default) or `"fade"`
  - `audio_mode`: `"replace"` (always narration)
  - `subtitles`: `false` (parameterized)
- Output: stitched MP4 stored in **S3**.

### 4. Logging (CloudWatch)
- Log per-segment generation success/failure.
- Log MediaConvert job status.
- Log final stitched video URI.

---

## Agent Config Parameters

```json
{
  "video_format": "mp4",
  "resolution": "1920x1080",
  "bitrate": "5000k",
  "concat_mode": "simple",   // or "fade"
  "subtitles": false,
  "audio_mode": "replace",   // narration replaces generated audio
  "log_mode": "cloudwatch-json"
}
Cost Estimate (Per 60-Second Video)
OpenAI (script + visuals): ~$0.10–$0.25

AWS MediaConvert (stitching): ~$0.0075–$0.012

Total (generation + stitching): ≈ $0.12–$0.27

Notes
Narration always replaces generated audio.

Schema is strict → agent can trust fields.

Concatenation mode is parameterized.

No subtitles unless explicitly enabled.

Logs go to CloudWatch.