#!/usr/bin/env python3
"""
Quick test music seeder - adds placeholder tracks for testing.
These are placeholder entries pointing to publicly available Creative Commons music.
"""
from app.database import SessionLocal
from app.models.database import MusicTrack

# Get database session
db = SessionLocal()

# Test music tracks (using publicly available Creative Commons music)
# These are placeholder URLs - ideally replace with actual royalty-free tracks
TEST_TRACKS = [
    {
        "track_id": "test_calm_01",
        "name": "Test Calm Background",
        "category": "calm",
        "mood": "peaceful",
        "duration": 120,  # 2 minutes - plenty for testing
        "bpm": 75,
        "s3_url": "https://pipeline-backend-assets.s3.us-east-1.amazonaws.com/music/library/test_calm_01.mp3",
        "license_type": "test",
        "attribution": "Test track for development",
        "suitable_for": ["general", "science", "math"]
    },
    {
        "track_id": "test_upbeat_01",
        "name": "Test Upbeat Background",
        "category": "upbeat",
        "mood": "energetic",
        "duration": 120,
        "bpm": 120,
        "s3_url": "https://pipeline-backend-assets.s3.us-east-1.amazonaws.com/music/library/test_upbeat_01.mp3",
        "license_type": "test",
        "attribution": "Test track for development",
        "suitable_for": ["general", "science"]
    },
    {
        "track_id": "test_inspiring_01",
        "name": "Test Inspiring Background",
        "category": "inspiring",
        "mood": "motivational",
        "duration": 120,
        "bpm": 95,
        "s3_url": "https://pipeline-backend-assets.s3.us-east-1.amazonaws.com/music/library/test_inspiring_01.mp3",
        "license_type": "test",
        "attribution": "Test track for development",
        "suitable_for": ["general"]
    }
]

try:
    print("🎵 Seeding test music tracks...\n")

    for track_data in TEST_TRACKS:
        # Check if track already exists
        existing = db.query(MusicTrack).filter(
            MusicTrack.track_id == track_data["track_id"]
        ).first()

        if existing:
            print(f"⏭️  Skipping {track_data['name']} (already exists)")
            continue

        # Add to database
        music_track = MusicTrack(
            track_id=track_data["track_id"],
            name=track_data["name"],
            category=track_data["category"],
            mood=track_data["mood"],
            duration=track_data["duration"],
            bpm=track_data["bpm"],
            s3_url=track_data["s3_url"],
            license_type=track_data["license_type"],
            attribution=track_data["attribution"],
            suitable_for=track_data["suitable_for"]
        )

        db.add(music_track)
        db.commit()

        print(f"✅ Added: {track_data['name']} ({track_data['category']})")

    # Show summary
    total_tracks = db.query(MusicTrack).count()
    print(f"\n✅ Seeding complete! Total tracks in library: {total_tracks}")

except Exception as e:
    print(f"❌ Error seeding database: {e}")
    db.rollback()

finally:
    db.close()
