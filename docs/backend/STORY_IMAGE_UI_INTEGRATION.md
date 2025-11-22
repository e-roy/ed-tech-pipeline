# Story Image Generation Agent - Test UI Integration

## Overview

The Test UI's "Step 1: Create Script" section has been integrated with the `StoryImageGeneratorAgent` to generate sequential storytelling images.

## What Was Hooked Up

### 1. New API Endpoint: `POST /api/generate-story-images`

**Location:** `backend/app/routes/generation.py`

**What it does:**
- Takes a script from the database (created by test UI)
- Converts script format (hook/concept/process/conclusion) to segments format
- Creates `segments.md` in S3
- Calls the `StoryImageGeneratorAgent` via orchestrator
- Returns immediately, processes asynchronously

**Request Body:**
```json
{
  "session_id": "test_session_xxx",
  "script_id": "test_script_xxx",
  "template_title": "Educational Video",  // Optional
  "num_images": 2,                        // Optional, default: 2
  "max_passes": 5,                        // Optional, default: 5
  "max_verification_passes": 3,           // Optional, default: 3
  "fast_mode": false,                      // Optional, default: false
  "diagram_s3_path": null                 // Optional S3 path to diagram.png
}
```

**Response:**
```json
{
  "status": "accepted",
  "session_id": "test_session_xxx",
  "message": "Story image generation started, listen to WebSocket for updates",
  "template_title": "Educational Video"
}
```

### 2. Test UI Button: "🎨 Generate Story Images"

**Location:** `backend/test_ui.html`

**What it does:**
- Appears in Step 1 after script is created
- Calls `/api/generate-story-images` endpoint
- Prompts for template title and optional diagram S3 path
- Shows status updates

## How It Works

### Flow:

1. **User creates script** in test UI (Step 1)
   - Script saved to database with hook/concept/process/conclusion

2. **User clicks "🎨 Generate Story Images"**
   - Test UI calls `/api/generate-story-images`
   - Endpoint retrieves script from database
   - Converts to segments format:
     ```
     hook → Segment 1: Hook
     concept → Segment 2: Concept Introduction
     process → Segment 3: Process Explanation
     conclusion → Segment 4: Conclusion
     ```

3. **Backend processing:**
   - Creates `segments.md` file in S3
   - Uploads diagram if provided
   - Calls orchestrator → StoryImageGeneratorAgent
   - Agent processes segments in parallel
   - Generates images via Replicate
   - Verifies images via OpenRouter (GPT-4o-mini)
   - Uploads results to S3

4. **Results:**
   - Images saved to: `users/{user_id}/{session_id}/images/{TemplateName}/{segment_number}. {title}/generated_images/`
   - Status updates via WebSocket
   - Final status in `status.json` at: `users/{user_id}/{session_id}/images/status.json`

## What You Need to Provide

### From Test UI:
- **Script** (already created by "Create Script" button)
  - Hook text
  - Concept text
  - Process text
  - Conclusion text
  - Visual guidance (from script parts)

### Optional Parameters:
- **Template Title** - Prompted when clicking button (default: "Educational Video")
- **Diagram S3 Path** - Optional, for style reference (prompted when clicking button)
- **num_images** - Currently hardcoded to 2 (can add UI controls later)
- **max_passes** - Currently hardcoded to 5
- **max_verification_passes** - Currently hardcoded to 3
- **fast_mode** - Currently hardcoded to false

## What Gets Hooked Up Automatically

1. **Script → Segments Conversion**
   - Automatically converts 4-part script to 4 segments
   - Maps durations from script parts
   - Extracts narration text and visual guidance

2. **S3 File Creation**
   - Creates `segments.md` automatically
   - Copies diagram if provided
   - Creates proper folder structure

3. **Agent Processing**
   - Parallel segment processing
   - Image generation with verification
   - Cost and time tracking
   - Error handling

4. **WebSocket Updates**
   - Real-time progress updates
   - Per-segment status
   - Overall progress percentage

## Example Usage

1. Open test UI in browser
2. Fill in script parts (hook, concept, process, conclusion)
3. Click "Create Script"
4. Click "🎨 Generate Story Images"
5. Enter template title (or use default)
6. Enter diagram S3 path (or leave blank)
7. Wait for processing (check WebSocket or status.json)
8. Images will be in S3 at: `users/{user_id}/{session_id}/images/{TemplateName}/...`

## Output Structure

```
users/
  {user_id}/
    {session_id}/
      images/
        segments.md                    # Created automatically
        diagram.png                    # If provided
        status.json                    # Processing status
        {TemplateName}/                # e.g., "Educational Video"
          1. Hook/
            generated_images/
              image_1.png
              image_2.png
          2. Concept Introduction/
            generated_images/
              image_1.png
              image_2.png
          ...
```

## Next Steps (Optional Enhancements)

1. **Add UI controls** for:
   - num_images
   - max_passes
   - max_verification_passes
   - fast_mode

2. **Add diagram upload** to test UI (currently requires S3 path)

3. **Display generated images** in test UI (currently only in S3)

4. **WebSocket connection** in test UI for real-time updates

