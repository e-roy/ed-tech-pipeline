# FFmpeg Command Reference
## Final Video Composition - AI Ad Generator

**Purpose:** Reference commands for stitching video clips with text overlays and background music

**Date:** November 14, 2025

---

## What the Composition Layer Does

Takes:
- 2-6 approved video clips (from Stable Video Diffusion)
- Text overlay config (product name, CTA)
- Optional background music

Produces:
- Single final ad video (8-12 seconds, 1080p MP4)

---

## Command Sequence

### Step 1: Normalize Clips (Handle Different Resolutions/FPS)

Each clip from Replicate might have different resolutions or frame rates. Normalize them first:

```bash
# For each clip, normalize to 1080p @ 30fps
ffmpeg -i clip_001.mp4 \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30" \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  normalized_001.mp4
```

**What this does:**
- `scale=1920:1080` → Resize to Full HD
- `crop=1920:1080` → Crop if aspect ratio doesn't match
- `fps=30` → Standardize frame rate
- `crf 23` → Quality level (lower = better quality, 18-28 range)
- `movflags +faststart` → Enables web streaming

---

### Step 2: Concatenate Clips

Create a text file listing all normalized clips:

**concat_list.txt:**
```
file 'normalized_001.mp4'
file 'normalized_002.mp4'
file 'normalized_003.mp4'
```

Then concatenate:

```bash
ffmpeg -f concat -safe 0 -i concat_list.txt \
  -c copy \
  concatenated.mp4
```

**What this does:**
- `-f concat` → Use concat demuxer
- `-safe 0` → Allow absolute paths
- `-c copy` → Don't re-encode (fast!)

---

### Step 3: Add Text Overlays

```bash
ffmpeg -i concatenated.mp4 \
  -vf "drawtext=text='AirRun Pro':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=72:fontcolor=white:x=(w-text_w)/2:y=100:enable='between(t,1,3)',
       drawtext=text='Shop Now':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:fontsize=48:fontcolor=yellow:x=(w-text_w)/2:y=900:enable='between(t,8,10)'" \
  -c:v libx264 -preset fast -crf 23 \
  -c:a copy \
  with_text.mp4
```

**What this does:**
- First `drawtext`: Product name centered at top, visible seconds 1-3
- Second `drawtext`: CTA centered at bottom, visible seconds 8-10
- `x=(w-text_w)/2` → Center horizontally
- `enable='between(t,1,3)'` → Show only during that time range

**Dynamic positioning (based on video duration):**
```python
# In Python, calculate CTA timing based on actual video duration
video_duration = get_video_duration(concatenated_file)  # e.g., 9.6 seconds
cta_start = video_duration - 2  # Show CTA in last 2 seconds
cta_end = video_duration
```

---

### Step 4: Add Background Music (Optional)

```bash
ffmpeg -i with_text.mp4 -i background_music.mp3 \
  -filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.3,afade=t=out:st=9:d=1[a1];[a0][a1]amix=inputs=2:duration=first[aout]" \
  -map 0:v -map "[aout]" \
  -c:v copy -c:a aac -b:a 192k \
  final_video.mp4
```

**What this does:**
- `[0:a]volume=1.0` → Keep original video audio at 100%
- `[1:a]volume=0.3` → Background music at 30% volume
- `afade=t=out:st=9:d=1` → Fade out music 1 second before end
- `amix=inputs=2` → Mix both audio streams
- `duration=first` → Match duration of first input (the video)

---

## All-in-One Command (If No Music)

If you're not adding background music, you can combine steps 2-3:

```bash
# 1. Create concat file
echo "file 'normalized_001.mp4'
file 'normalized_002.mp4'
file 'normalized_003.mp4'" > concat_list.txt

# 2. Concatenate + Add Text in one command
ffmpeg -f concat -safe 0 -i concat_list.txt \
  -vf "drawtext=text='AirRun Pro':fontfile=/path/to/font.ttf:fontsize=72:fontcolor=white:x=(w-text_w)/2:y=100:enable='between(t,1,3)',
       drawtext=text='Shop Now':fontfile=/path/to/font.ttf:fontsize=48:fontcolor=yellow:x=(w-text_w)/2:y=900:enable='between(t,8,10)'" \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 128k \
  -movflags +faststart \
  final_video.mp4
```

---

## Python Helper Functions

### Get Video Duration

```python
import subprocess
import json

def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])
```

### Build Dynamic Drawtext Filter

```python
def build_text_overlay_filter(
    product_name: str,
    cta: str,
    video_duration: float,
    text_color: str = 'white',
    font_path: str = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
) -> str:
    """Build FFmpeg drawtext filter for overlays"""

    # Product name: show for first 3 seconds
    product_filter = (
        f"drawtext=text='{product_name}':"
        f"fontfile={font_path}:"
        f"fontsize=72:"
        f"fontcolor={text_color}:"
        f"x=(w-text_w)/2:y=100:"
        f"enable='between(t,1,3)'"
    )

    # CTA: show for last 2 seconds
    cta_start = max(video_duration - 2, 0)
    cta_filter = (
        f"drawtext=text='{cta}':"
        f"fontfile={font_path}:"
        f"fontsize=48:"
        f"fontcolor=yellow:"
        f"x=(w-text_w)/2:y=900:"
        f"enable='between(t,{cta_start},{video_duration})'"
    )

    return f"{product_filter},{cta_filter}"
```

---

## Testing Locally

### Quick Test with Sample Videos

```bash
# Download test videos (or use your own)
wget https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4 -O test1.mp4
wget https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_2mb.mp4 -O test2.mp4

# Normalize them
ffmpeg -i test1.mp4 -vf "scale=1920:1080,fps=30" -c:v libx264 -crf 23 norm1.mp4
ffmpeg -i test2.mp4 -vf "scale=1920:1080,fps=30" -c:v libx264 -crf 23 norm2.mp4

# Create concat file
echo "file 'norm1.mp4'
file 'norm2.mp4'" > test_concat.txt

# Stitch + add text
ffmpeg -f concat -safe 0 -i test_concat.txt \
  -vf "drawtext=text='Test Product':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=100" \
  -c:v libx264 -crf 23 \
  final_test.mp4

# Play the result
ffplay final_test.mp4
```

---

## Railway Docker Setup

Make sure FFmpeg is installed in your Docker container:

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# ... rest of Dockerfile
```

**Verify FFmpeg in container:**
```bash
ffmpeg -version
# Should output FFmpeg version info
```

---

## Common Issues & Solutions

### Issue: Font not found

**Error:** `Cannot load font`

**Solution:**
```bash
# List available fonts
fc-list

# Or bundle a font in your Docker image
COPY fonts/DejaVuSans-Bold.ttf /app/fonts/
```

### Issue: Video codec not supported

**Error:** `Unknown encoder 'libx264'`

**Solution:**
```bash
# Install ffmpeg with libx264 support
apt-get install -y ffmpeg libavcodec-extra
```

### Issue: Out of memory during encoding

**Error:** Process killed (OOM)

**Solution:**
```python
# Reduce CRF (lower quality) or resolution
# OR process clips sequentially instead of all at once
```

---

## Cost & Performance

**Processing Time Estimates:**
- Normalize 4 clips (3s each): ~10-15 seconds
- Concatenate: ~2 seconds (copy mode)
- Add text overlays: ~8-12 seconds (re-encode)
- Add background music: ~5-8 seconds
- **Total: ~30-40 seconds for final composition**

**Cost:** $0 (FFmpeg is free, runs on your server)

---

## Next Steps

1. ✅ Review these commands
2. Test locally with sample videos
3. Integrate into `CompositionAgent` class
4. Test on Railway staging environment
5. Verify final video plays in browser

**Status:** Ready for implementation ✅
