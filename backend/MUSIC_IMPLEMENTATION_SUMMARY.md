# Background Music Implementation Summary

## Overview
Background music generation has been integrated into the audio pipeline. When generating audio narration, the system now also selects and processes an appropriate background music track, resulting in **5 audio files** per session:
- 4 narration files (hook, concept, process, conclusion)
- 1 background music file

## Implementation Details

### 1. Database Schema ✅
**Migration**: `cae2ad28fd17_add_music_tracks_table.py`

**New Table**: `music_tracks`
```sql
- track_id (unique identifier)
- name (track name)
- category (upbeat, calm, inspiring)
- mood (energetic, peaceful, motivational, etc.)
- duration (in seconds)
- bpm (beats per minute)
- s3_url (location of track)
- license_type (royalty_free, creative_commons, etc.)
- attribution (required credits)
- suitable_for (array of subject tags)
```

**Session Table Updates**:
```sql
- music_track_id (selected track ID)
- music_s3_url (processed music URL)
- music_volume (default: 0.15 = 15%)
```

### 2. Music Selection Agent ✅
**File**: `app/agents/music_agent.py`

**MusicSelectionAgent**:
- Analyzes script mood using keyword detection
- Selects appropriate music from database based on:
  - Script mood (upbeat/calm/inspiring)
  - Video duration (ensures track is long enough)
- Fallback strategy if no perfect match exists

**Mood Detection Keywords**:
- **Upbeat**: exciting, amazing, discover, explore, wonder, incredible
- **Calm**: understand, learn, explain, process, think, consider
- **Inspiring**: achieve, grow, transform, create, build, empower

### 3. Music Processing Service ✅
**File**: `app/agents/music_agent.py`

**MusicProcessingService**:
- Downloads original track from S3
- Uses FFmpeg to:
  - Trim to exact video duration
  - Add 2s fade-in at start
  - Add 3s fade-out at end
  - Adjust volume to 15% (background level)
- Uploads processed track to S3
- Cleans up temporary files

**FFmpeg Command**:
```bash
ffmpeg -i original.mp3 -t {duration} \
  -af "afade=t=in:st=0:d=2,afade=t=out:st={end}:d=3,volume=0.15" \
  -c:a libmp3lame -b:a 128k output.mp3
```

### 4. Audio Pipeline Integration ✅
**File**: `app/agents/audio_pipeline.py`

**Changes**:
- AudioPipelineAgent now accepts `db` and `storage_service` parameters
- After generating 4 narration files, automatically:
  1. Selects music using MusicSelectionAgent
  2. Processes music using MusicProcessingService
  3. Adds music file to audio_files array
- Music generation failures are handled gracefully (logs warning, continues without music)

**Output Structure**:
```json
{
  "audio_files": [
    {
      "part": "hook",
      "filepath": "/tmp/audio_hook_{session_id}.mp3",
      "url": "https://s3.../audio_hook.mp3",
      "duration": 10.5,
      "cost": 0.002,
      "voice": "alloy"
    },
    // ... concept, process, conclusion ...
    {
      "part": "music",
      "filepath": "/tmp/music_processed_{session_id}.mp3",
      "url": "https://s3.../music.mp3",
      "duration": 55.0,
      "cost": 0.0,
      "track_id": "test_calm_01",
      "name": "Test Calm Background",
      "category": "calm",
      "volume": 0.15
    }
  ],
  "total_duration": 55.0,
  "total_cost": 0.008,
  "has_background_music": true
}
```

### 5. Orchestrator Updates ✅
**File**: `app/services/orchestrator.py`

**Changes**:
- `generate_audio()` now creates AudioPipelineAgent instance with db and storage_service
- Passes `user_id` in audio_input data for music processing

### 6. Test Data ✅
**File**: `seed_test_music.py`

**Test Tracks Added**:
- `test_calm_01` - Test Calm Background (120s, 75 BPM)
- `test_upbeat_01` - Test Upbeat Background (120s, 120 BPM)
- `test_inspiring_01` - Test Inspiring Background (120s, 95 BPM)

**Note**: These are placeholder database entries. The S3 URLs point to locations that don't have actual MP3 files yet. Music processing will fail gracefully and skip music generation until real tracks are uploaded.

## Volume Guidelines

For educational videos, we use these volume levels:
- **Narration**: 100% (0dB) - Primary audio, must be clear
- **Background Music**: 10-20% (-20dB to -14dB) - We use 15%
- **Sound Effects**: 30-50% (-10dB to -6dB) - For future use

## Testing

To test the system:

1. **Run the backend**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

2. **Generate audio** via the API:
   ```bash
   POST /api/generate-audio
   {
     "session_id": "test_xyz",
     "script_id": "script_123",
     "voice": "alloy",
     "audio_option": "tts"
   }
   ```

3. **Check the response**:
   - Should have 5 files in `audio_files` array (if music library has tracks)
   - Should have 4 files if music generation fails (graceful degradation)
   - Last file should have `"part": "music"` if successful

4. **Parallel Generation** (via finalize-script endpoint):
   ```bash
   POST /api/finalize-script
   {
     "session_id": "test_xyz",
     "script_id": "script_123",
     "model": "flux-schnell",
     "images_per_part": 2,
     "voice": "alloy"
   }
   ```
   - Generates images and audio (with music) in parallel

## Next Steps

### Immediate (To Make Music Work)
1. **Upload Real Music Files**:
   - Download royalty-free music from Pixabay, YouTube Audio Library, or Incompetech
   - Upload MP3 files to S3 at: `music/library/{track_id}.mp3`
   - Update `seed_test_music.py` with real S3 URLs
   - Re-run seeder

2. **Test End-to-End**:
   - Create script via test UI
   - Click "Finalize Script" to generate images + audio in parallel
   - Verify 5 audio files are created
   - Check that music volume is appropriate (15%)

### Future Enhancements
1. **Music Preview in UI**:
   - Show selected music track name in test UI
   - Add audio player for background music preview

2. **Manual Music Selection**:
   - Allow users to select music category (upbeat/calm/inspiring)
   - Override automatic mood detection

3. **Video Compositor Integration**:
   - Update FFmpeg compositor to mix narration + background music
   - Implement multi-track audio mixing
   - Add volume ducking (lower music during narration)

4. **Music Library Expansion**:
   - Add 15-20 high-quality royalty-free tracks
   - Categorize by subject (science, math, general)
   - Add different lengths (30s, 60s, 120s)

5. **AI Music Generation** (Optional):
   - Evaluate Mubert, Suno, or AIVA APIs
   - Compare cost vs quality vs library approach
   - A/B test user preferences

## Cost Analysis

### Current Approach (Pre-Licensed Library)
- **Setup Cost**: $0-200 (one-time, for premium library)
- **Per-Video Cost**: $0.00 (no per-use fees)
- **Storage**: ~$0.01/month for 50 tracks
- **Processing**: Negligible (just FFmpeg trimming)

### Alternative (AI Generation)
- **Per-Video Cost**: $0.10-0.50 per track
- **For 1000 videos/month**: $100-500/month
- **Pros**: Custom music, perfect duration matching
- **Cons**: Higher cost, quality variance, generation time

**Recommendation**: Stick with pre-licensed library approach.

## Files Modified/Created

### Created
- `alembic/versions/cae2ad28fd17_add_music_tracks_table.py`
- `app/agents/music_agent.py`
- `app/models/database.py` (MusicTrack model added)
- `seed_music_library.py` (full seeder with manual download)
- `seed_test_music.py` (quick test seeder)
- `MUSIC_STRATEGY.md` (detailed strategy document)
- `MUSIC_IMPLEMENTATION_SUMMARY.md` (this file)

### Modified
- `app/agents/audio_pipeline.py` (added music generation)
- `app/services/orchestrator.py` (pass db/storage to audio pipeline)
- `app/models/database.py` (added music columns to Session)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Audio Generation Flow                     │
└─────────────────────────────────────────────────────────────┘

  1. API Request (generate_audio)
       │
       ├─> Fetch Script from DB
       │
       ├─> Initialize AudioPipelineAgent(db, storage)
       │
       └─> Generate Audio
             │
             ├─> Generate Narration (4 files)
             │    ├─> OpenAI TTS: hook.mp3
             │    ├─> OpenAI TTS: concept.mp3
             │    ├─> OpenAI TTS: process.mp3
             │    └─> OpenAI TTS: conclusion.mp3
             │
             └─> Generate Background Music (1 file)
                  │
                  ├─> MusicSelectionAgent
                  │    ├─> Analyze script mood
                  │    ├─> Query music_tracks table
                  │    └─> Select best match
                  │
                  └─> MusicProcessingService
                       ├─> Download from S3
                       ├─> FFmpeg: trim + fade + volume
                       ├─> Upload processed to S3
                       └─> Return music.mp3

  2. Upload All 5 Files to S3

  3. Store URLs in Assets Table

  4. Return Response with 5 Audio Files
```

## Success Criteria ✅

- [x] Database migration created and applied
- [x] MusicTrack model added
- [x] MusicSelectionAgent implemented
- [x] MusicProcessingService implemented
- [x] AudioPipelineAgent updated to generate music
- [x] Orchestrator passes db and storage_service
- [x] Test tracks seeded into database
- [ ] Real MP3 files uploaded to S3 (pending)
- [ ] End-to-end test with actual music (pending real files)

## Conclusion

The background music system is **fully implemented and ready for testing**. The only missing piece is uploading actual MP3 files to S3. Once real music files are added, the system will automatically:

1. Analyze each script's mood
2. Select appropriate background music
3. Trim and process music to match video duration
4. Upload to S3 alongside narration
5. Return 5 audio files ready for video composition

The implementation is robust with graceful fallback - if music generation fails for any reason, it continues with just the 4 narration files.
