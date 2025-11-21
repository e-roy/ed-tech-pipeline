#!/usr/bin/env python3
"""
Upload music files from Downloads to S3.
"""
import os
import boto3
from dotenv import load_dotenv

# Load environment
load_dotenv()

# S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "pipeline-backend-assets")
AWS_REGION = os.getenv("AWS_REGION", "us-east-2")

# Initialize S3 client
s3_client = boto3.client("s3", region_name=AWS_REGION)

# Files to upload
MUSIC_FILES = [
    {
        "local_path": os.path.expanduser("~/Downloads/calm:peaceful.mp3"),
        "s3_key": "music/library/test_calm_01.mp3",
        "name": "Test Calm Background"
    },
    {
        "local_path": os.path.expanduser("~/Downloads/upbeat:energetic.mp3"),
        "s3_key": "music/library/test_upbeat_01.mp3",
        "name": "Test Upbeat Background"
    },
    {
        "local_path": os.path.expanduser("~/Downloads/inspiring:motivational.mp3"),
        "s3_key": "music/library/test_inspiring_01.mp3",
        "name": "Test Inspiring Background"
    }
]

print("🎵 Uploading music files to S3...\n")
print(f"Bucket: {S3_BUCKET_NAME}")
print(f"Region: {AWS_REGION}\n")

for music_file in MUSIC_FILES:
    local_path = music_file["local_path"]
    s3_key = music_file["s3_key"]
    name = music_file["name"]

    # Check if file exists
    if not os.path.exists(local_path):
        print(f"❌ File not found: {local_path}")
        continue

    file_size = os.path.getsize(local_path)
    print(f"📤 Uploading {name}...")
    print(f"   Local: {local_path}")
    print(f"   Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"   S3 Key: {s3_key}")

    try:
        # Upload to S3
        with open(local_path, "rb") as f:
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=f,
                ContentType="audio/mpeg"
            )

        # Generate URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        print(f"✅ Uploaded successfully!")
        print(f"   URL: {s3_url}\n")

    except Exception as e:
        print(f"❌ Upload failed: {e}\n")

print("✅ Upload process complete!")
print("\nNext step: Test audio generation via the test UI")
print("The system will now automatically use these tracks as background music.")
