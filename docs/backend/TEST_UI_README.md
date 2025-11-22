# Test UI Guide

## Overview
The test UI provides a visual interface to verify the audio generation pipeline works correctly.

## Files
- `test_ui.html` - Browser-based test interface
- `test_audio_agent.py` - Direct agent testing (no API)
- `test_orchestrator_audio.py` - Full orchestrator integration test

## Using the Test UI

### 1. Start the Backend Server
```bash
cd /Users/mfuechec/Desktop/GauntletProjects/pipeline/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. Open the Test UI
Simply open `test_ui.html` in your browser:
```bash
open test_ui.html
```

Or drag and drop it into Chrome/Firefox/Safari.

### 3. Test Workflow

**Step 1: Create Script**
1. Fill in the user email (default: test@example.com)
2. Customize the 4-part script content:
   - Hook: Opening question/statement
   - Concept: Main educational concept
   - Process: How it works explanation
   - Conclusion: Summary and takeaway
3. Click "Create Script"
4. The script ID and session ID will be auto-filled

**Step 2: Generate Audio**
1. Select a voice from the 6 available options:
   - **Alloy**: Neutral, balanced - Great for education
   - **Echo**: Male, clear - Authoritative
   - **Fable**: British, expressive - Engaging
   - **Onyx**: Deep, authoritative - Professional
   - **Nova**: Female, energetic - Dynamic
   - **Shimmer**: Warm, friendly - Conversational
2. Click "Generate Audio"
3. Wait for processing (typically 5-15 seconds)
4. Listen to generated audio files in the built-in player

### 4. What to Check

✅ **Success Indicators:**
- Status changes: Pending → Running → Success
- 4 audio files generated (hook, concept, process, conclusion)
- Audio plays correctly in browser
- Cost calculation shown (~$0.02 for 60s content)
- Total duration matches expectations

❌ **Failure Indicators:**
- Status shows "Failed"
- Error message in result box
- No audio files generated
- 500/400 errors in browser console

## Direct Testing (Without UI)

### Test Audio Agent Only
```bash
python test_audio_agent.py
```
This tests the OpenAI TTS integration directly without the orchestrator or database.

### Test Full Orchestrator Flow
```bash
python test_orchestrator_audio.py
```
This tests the complete workflow including:
- Database operations (Script, Session, Asset)
- Orchestrator coordination
- S3 upload
- Audio generation

## Troubleshooting

### Backend Not Running
**Error:** "Failed to fetch" or connection refused
**Fix:** Start the backend server first

### Authentication Issues
**Error:** 401 Unauthorized
**Fix:** The test UI uses a default test user. Make sure the user exists in the database or modify the email.

### OpenAI API Issues
**Error:** "OpenAI API error"
**Fix:**
1. Check `.env` has valid `OPENAI_API_KEY`
2. Verify API key has credits
3. Check OpenAI service status

### S3 Upload Failures
**Error:** "S3 upload failed"
**Note:** This is non-critical. Audio files are still saved locally in `output/audio/` and returned to the frontend. S3 is for permanent storage only.

### Audio Files Not Playing
**Issue:** Audio player shows but won't play
**Possible Causes:**
1. Browser security restrictions (CORS)
2. Audio format not supported
3. File path incorrect

**Fix:** Check browser console for errors

## Expected Output

### Console Output (Backend)
```
INFO:     POST /api/generation/generate-audio
🔊 Generating audio for session: test_session_xxx
  Part: hook (58 chars, ~10s target)
  Part: concept (114 chars, ~15s target)
  Part: process (186 chars, ~20s target)
  Part: conclusion (107 chars, ~15s target)
✓ Generated: hook (11.2s, $0.0009)
✓ Generated: concept (17.8s, $0.0017)
✓ Generated: process (28.4s, $0.0028)
✓ Generated: conclusion (16.1s, $0.0016)
💾 Uploading 4 audio files to S3...
✓ Audio generation complete (73.5s, $0.0070)
```

### Browser Output
```json
{
  "status": "success",
  "session_id": "test_session_xxx",
  "audio_files": [
    {
      "part": "hook",
      "url": "https://s3.../hook.mp3",
      "duration": 11.2,
      "cost": 0.0009
    },
    // ... 3 more files
  ],
  "total_duration": 73.5,
  "total_cost": 0.0070
}
```

## API Endpoints Used

### POST /api/generation/generate-audio
**Request:**
```json
{
  "session_id": "test_session_001",
  "script_id": "test_script_001",
  "voice": "alloy",
  "audio_option": "tts"
}
```

**Headers:**
```
Content-Type: application/json
X-User-Email: test@example.com
```

**Response:**
```json
{
  "status": "success",
  "session_id": "test_session_001",
  "audio_files": [...],
  "total_duration": 73.5,
  "total_cost": 0.0070,
  "message": "Audio generated successfully"
}
```

## Next Steps

After verifying the test UI works:

1. **Frontend Integration**: Use the same API endpoint in the Next.js frontend
2. **Database**: Script creation should save to Postgres via API (currently simulated in test UI)
3. **Authentication**: Implement proper JWT authentication instead of X-User-Email header
4. **Task 08**: Build the Educational Compositor to combine audio with visuals
