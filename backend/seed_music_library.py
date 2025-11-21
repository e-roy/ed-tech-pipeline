#!/usr/bin/env python3
"""
Seed music library with royalty-free tracks.

Downloads music from Pixabay and uploads to S3, then adds to database.
NOTE: You'll need to manually download tracks from Pixabay first due to rate limits.
"""
import os
import sys
import boto3
from dotenv import load_dotenv
from app.database import SessionLocal
from app.models.database import MusicTrack

# Load environment
load_dotenv()

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "pipeline-backend-assets")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

# Initialize S3 client
s3_client = boto3.client("s3", region_name=AWS_REGION)

# Music tracks to seed (manually download from Pixabay first)
# https://pixabay.com/music/
MUSIC_TRACKS = [
    {
        "track_id": "upbeat_energetic_01",
        "name": "Energetic Learning",
        "category": "upbeat",
        "mood": "energetic",
        "duration": 60,
        "bpm": 120,
        "license_type": "pixabay",
        "attribution": "Music by Pixabay",
        "suitable_for": ["science", "math", "general"],
        "local_file": "music_library/upbeat_energetic_01.mp3"
    },
    {
        "track_id": "upbeat_bright_01",
        "name": "Bright Education",
        "category": "upbeat",
        "mood": "bright",
        "duration": 60,
        "bpm": 125,
        "license_type": "pixabay",
        "attribution": "Music by Pixabay",
        "suitable_for": ["science", "general"],
        "local_file": "music_library/upbeat_bright_01.mp3"
    },
    {
        "track_id": "upbeat_playful_01",
        "name": "Playful Curiosity",
        "category": "upbeat",
        "mood": "playful",
        "duration": 60,
        "bpm": 115,
        "license_type": "pixabay",
        "attribution": "Music by Pixabay",
        "suitable_for": ["science", "general"],
        "local_file": "music_library/upbeat_playful_01.mp3"
    },
    {
        "track_id": "calm_gentle_01",
        "name": "Gentle Focus",
        "category": "calm",
        "mood": "gentle",
        "duration": 60,
        "bpm": 80,
        "license_type": "pixabay",
        "attribution": "Music by Pixabay",
        "suitable_for": ["math", "general"],
        "local_file": "music_library/calm_gentle_01.mp3"
    },
    {
        "track_id": "calm_soft_01",
        "name": "Soft Study",
        "category": "calm",
        "mood": "soft",
        "duration": 60,
        "bpm": 75,
        "license_type": "pixabay",
        "attribution": "Music by Pixabay",
        "suitable_for": ["general"],
        "local_file": "music_library/calm_soft_01.mp3"
    },
    {
        "track_id": "calm_peaceful_01",
        "name": "Peaceful Learning",
        "category": "calm",
        "mood": "peaceful",
        "duration": 60,
        "bpm": 70,
        "license_type": "pixabay",
        "attribution": "Music by Pixabay",
        "suitable_for": ["general"],
        "local_file": "music_library/calm_peaceful_01.mp3"
    },
    {
        "track_id": "inspiring_motivational_01",
        "name": "Motivational Discovery",
        "category": "inspiring",
        "mood": "motivational",
        "duration": 60,
        "bpm": 95,
        "license_type": "pixabay",
        "attribution": "Music by Pixabay",
        "suitable_for": ["science", "general"],
        "local_file": "music_library/inspiring_motivational_01.mp3"
    },
    {
        "track_id": "inspiring_hopeful_01",
        "name": "Hopeful Education",
        "category": "inspiring",
        "mood": "hopeful",
        "duration": 60,
        "bpm": 90,
        "license_type": "pixabay",
        "attribution": "Music by Pixabay",
        "suitable_for": ["general"],
        "local_file": "music_library/inspiring_hopeful_01.mp3"
    },
]


def upload_music_to_s3(local_path: str, track_id: str) -> str:
    """Upload music file to S3 and return URL."""
    s3_key = f"music/library/{track_id}.mp3"

    # Check if file exists
    if not os.path.exists(local_path):
        print(f"❌ File not found: {local_path}")
        print(f"   Please download from Pixabay and place in music_library/")
        return None

    # Upload to S3
    try:
        with open(local_path, "rb") as f:
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=f,
                ContentType="audio/mpeg"
            )

        # Generate URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"✅ Uploaded: {s3_url}")
        return s3_url

    except Exception as e:
        print(f"❌ Upload failed for {local_path}: {e}")
        return None


def seed_database():
    """Seed music tracks into database."""
    db = SessionLocal()

    try:
        print("🎵 Starting music library seeding...\n")

        for track_data in MUSIC_TRACKS:
            # Check if track already exists
            existing = db.query(MusicTrack).filter(
                MusicTrack.track_id == track_data["track_id"]
            ).first()

            if existing:
                print(f"⏭️  Skipping {track_data['name']} (already exists)")
                continue

            # Upload to S3
            s3_url = upload_music_to_s3(track_data["local_file"], track_data["track_id"])

            if not s3_url:
                print(f"⚠️  Skipping {track_data['name']} (upload failed)\n")
                continue

            # Add to database
            music_track = MusicTrack(
                track_id=track_data["track_id"],
                name=track_data["name"],
                category=track_data["category"],
                mood=track_data["mood"],
                duration=track_data["duration"],
                bpm=track_data["bpm"],
                s3_url=s3_url,
                license_type=track_data["license_type"],
                attribution=track_data["attribution"],
                suitable_for=track_data["suitable_for"]
            )

            db.add(music_track)
            db.commit()

            print(f"✅ Added to database: {track_data['name']}\n")

        print("✅ Music library seeding complete!")

        # Show summary
        total_tracks = db.query(MusicTrack).count()
        print(f"\n📊 Total tracks in library: {total_tracks}")

    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()

    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("MUSIC LIBRARY SEEDER")
    print("=" * 60)
    print()
    print("NOTE: This script requires music files to be downloaded first.")
    print("Please download royalty-free music from Pixabay and place in:")
    print("  music_library/upbeat_*.mp3")
    print("  music_library/calm_*.mp3")
    print("  music_library/inspiring_*.mp3")
    print()
    print("Pixabay Music: https://pixabay.com/music/")
    print("=" * 60)
    print()

    # Check if music_library directory exists
    if not os.path.exists("music_library"):
        print("⚠️  Creating music_library/ directory...")
        os.makedirs("music_library")
        print("📁 Please add MP3 files to music_library/ before running again.")
        sys.exit(0)

    # Count available files
    mp3_files = [f for f in os.listdir("music_library") if f.endswith(".mp3")]
    if len(mp3_files) == 0:
        print("⚠️  No MP3 files found in music_library/")
        print("📁 Please download and add MP3 files before running again.")
        sys.exit(0)

    print(f"Found {len(mp3_files)} MP3 files in music_library/\n")

    response = input("Proceed with upload? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    seed_database()
