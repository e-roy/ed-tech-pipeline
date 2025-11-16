# Music Strategy for Educational Videos

## Architecture

### Storage Structure
```
S3 Bucket: pipeline-backend-assets
└── music/
    ├── library/              (Pre-uploaded music library)
    │   ├── upbeat/
    │   │   ├── energetic_learning_60s.mp3
    │   │   ├── bright_education_60s.mp3
    │   │   └── playful_curiosity_60s.mp3
    │   ├── calm/
    │   │   ├── gentle_focus_60s.mp3
    │   │   ├── soft_study_60s.mp3
    │   │   └── peaceful_learning_60s.mp3
    │   └── inspiring/
    │       ├── motivational_discovery_60s.mp3
    │       └── hopeful_education_60s.mp3
    └── sessions/             (Trimmed/processed tracks per session)
        └── {session_id}/
            └── background_music.mp3
```

### Database Schema Addition
```sql
-- Music tracks table
CREATE TABLE music_tracks (
    id SERIAL PRIMARY KEY,
    track_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,  -- upbeat, calm, inspiring
    mood VARCHAR(50),                -- energetic, peaceful, motivational
    duration INTEGER NOT NULL,       -- in seconds
    bpm INTEGER,                     -- beats per minute
    s3_url TEXT NOT NULL,
    license_type VARCHAR(100),       -- royalty_free, creative_commons, etc.
    attribution TEXT,
    suitable_for VARCHAR(255)[],     -- ['science', 'math', 'general']
    created_at TIMESTAMP DEFAULT NOW()
);

-- Session music selection
ALTER TABLE sessions ADD COLUMN music_track_id VARCHAR(255);
ALTER TABLE sessions ADD COLUMN music_s3_url TEXT;
ALTER TABLE sessions ADD COLUMN music_volume FLOAT DEFAULT 0.15; -- 15% volume
```

## Option 1: Pre-Selected Music Library (RECOMMENDED)

### Sources for Royalty-Free Music
1. **Pixabay Audio** (https://pixabay.com/music/)
   - Free for commercial use
   - No attribution required
   - Large library

2. **YouTube Audio Library** (https://studio.youtube.com/channel/UCuploads/music)
   - Free, some require attribution
   - Educational-friendly

3. **Free Music Archive** (https://freemusicarchive.org/)
   - Creative Commons licensed
   - Educational use allowed

4. **Incompetech** (https://incompetech.com/)
   - Kevin MacLeod's library
   - Requires attribution
   - Very educational-friendly

### Implementation Steps

#### 1. Music Selection Agent
```python
class MusicSelectionAgent:
    """
    Selects appropriate background music based on script content and mood.
    """

    def __init__(self, db: Session):
        self.db = db

    async def select_music(
        self,
        script: Dict[str, Any],
        video_duration: float,
        mood_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select music based on script analysis.

        Args:
            script: The video script
            video_duration: Total video duration in seconds
            mood_preference: Optional mood override (upbeat, calm, inspiring)

        Returns:
            Selected music track with S3 URL and metadata
        """

        # Analyze script mood if not provided
        if not mood_preference:
            mood_preference = await self._analyze_script_mood(script)

        # Query music tracks
        track = self.db.query(MusicTrack).filter(
            MusicTrack.category == mood_preference,
            MusicTrack.duration >= video_duration
        ).order_by(func.random()).first()

        if not track:
            # Fallback to any track with sufficient duration
            track = self.db.query(MusicTrack).filter(
                MusicTrack.duration >= video_duration
            ).order_by(func.random()).first()

        return {
            "track_id": track.track_id,
            "name": track.name,
            "s3_url": track.s3_url,
            "duration": track.duration,
            "category": track.category,
            "volume": 0.15  # 15% volume (background)
        }

    async def _analyze_script_mood(self, script: Dict[str, Any]) -> str:
        """
        Use LLM to analyze script and determine appropriate music mood.
        """
        # Combine all script text
        text = " ".join([
            script.get("hook", {}).get("text", ""),
            script.get("concept", {}).get("text", ""),
            script.get("process", {}).get("text", ""),
            script.get("conclusion", {}).get("text", "")
        ])

        # Simple keyword-based analysis (or use LLM for more sophisticated)
        energetic_keywords = ["exciting", "amazing", "discover", "explore", "wonder"]
        calm_keywords = ["understand", "learn", "explain", "process", "think"]
        inspiring_keywords = ["achieve", "grow", "transform", "create", "build"]

        text_lower = text.lower()

        if any(word in text_lower for word in energetic_keywords):
            return "upbeat"
        elif any(word in text_lower for word in inspiring_keywords):
            return "inspiring"
        else:
            return "calm"
```

#### 2. Music Processing Service
```python
class MusicProcessingService:
    """
    Trims and adjusts music tracks to match video duration.
    """

    async def prepare_music_for_video(
        self,
        music_s3_url: str,
        target_duration: float,
        session_id: str,
        fade_in: float = 2.0,
        fade_out: float = 3.0,
        volume: float = 0.15
    ) -> str:
        """
        Download, trim, and adjust music track.

        Returns:
            S3 URL of processed music track
        """
        # Download original track
        local_path = f"/tmp/music_original_{session_id}.mp3"
        await self._download_from_s3(music_s3_url, local_path)

        # Process with FFmpeg
        output_path = f"/tmp/music_processed_{session_id}.mp3"

        # Trim to duration, add fade in/out, adjust volume
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', local_path,
            '-t', str(target_duration),
            '-af', f'afade=t=in:st=0:d={fade_in},afade=t=out:st={target_duration-fade_out}:d={fade_out},volume={volume}',
            '-c:a', 'libmp3lame',
            '-b:a', '128k',
            output_path
        ]

        subprocess.run(ffmpeg_cmd, check=True)

        # Upload processed track to S3
        s3_url = await self.storage_service.upload_local_file(
            file_path=output_path,
            asset_type="audio",
            session_id=session_id,
            asset_id=f"music_{session_id}",
            user_id=user_id
        )

        # Cleanup
        os.remove(local_path)
        os.remove(output_path)

        return s3_url["url"]
```

#### 3. Update Video Compositor
```python
class VideoCompositor:
    """
    Combines images, narration, and background music.
    """

    async def compose_with_music(
        self,
        images: List[str],
        narration_tracks: List[str],
        music_track: Optional[str] = None,
        output_path: str = "final_video.mp4"
    ):
        """
        Compose video with images, narration, and optional background music.
        """

        # Build complex FFmpeg filter
        if music_track:
            # Mix narration (100% volume) with music (15% volume)
            filter_complex = (
                # Concatenate all narration clips
                f"[1:a][2:a][3:a][4:a]concat=n=4:v=0:a=1[narration];"
                # Load background music
                f"[5:a]volume=0.15[music];"
                # Mix narration and music
                f"[narration][music]amix=inputs=2:duration=shortest[audio]"
            )

            cmd = [
                'ffmpeg',
                '-i', 'video_no_audio.mp4',
                '-i', narration_tracks[0],
                '-i', narration_tracks[1],
                '-i', narration_tracks[2],
                '-i', narration_tracks[3],
                '-i', music_track,
                '-filter_complex', filter_complex,
                '-map', '0:v',
                '-map', '[audio]',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                output_path
            ]
        else:
            # No music, just narration
            # ... existing logic
            pass
```

## Option 2: AI Music Generation (Future Enhancement)

### Services to Consider:
1. **Suno AI** (https://suno.ai/)
   - API available
   - Custom music generation
   - ~$0.50 per track

2. **Mubert API** (https://mubert.com/)
   - Royalty-free AI music
   - Generate based on mood/duration
   - $0.10-0.30 per track

3. **AIVA** (https://www.aiva.ai/)
   - Professional AI composer
   - Licensing for commercial use
   - $11-$33/month plans

**Pros:**
- ✅ Custom music per video
- ✅ Perfect duration matching
- ✅ Mood-matched to content

**Cons:**
- ❌ Additional API costs ($0.10-0.50/video)
- ❌ Generation time (10-30 seconds)
- ❌ Quality variance
- ❌ Licensing complexity

## Recommended Implementation Timeline

### Phase 1 (Immediate - Week 1)
1. Create music tracks table in database
2. Upload 10-15 royalty-free tracks to S3
3. Add music selection to script finalization
4. Update compositor to mix music + narration

### Phase 2 (Week 2-3)
1. Implement LLM-based mood analysis
2. Add music trimming/processing service
3. Add volume/fade controls in UI
4. Music preview in test UI

### Phase 3 (Future)
1. Evaluate AI music generation services
2. A/B test user preference (library vs generated)
3. Implement based on data

## Cost Analysis

### Pre-Selected Library (Recommended)
- One-time setup: $0 (free sources) or $50-200 (premium library)
- Per-video cost: $0
- Storage cost: ~$0.01/month for 50 tracks

### AI Generation (Alternative)
- Per-video cost: $0.10-0.50
- For 1000 videos/month: $100-500/month
- Higher quality control needed

## Music Volume Guidelines

For educational videos:
- **Narration**: 100% (0dB)
- **Background Music**: 10-20% (-20dB to -14dB)
- **Sound Effects**: 30-50% (-10dB to -6dB)

This ensures narration is always clear and audible.
