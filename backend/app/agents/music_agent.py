"""
Music Selection and Processing Agent.

Handles selecting appropriate background music and processing it for videos.
"""
import os
import subprocess
import tempfile
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import MusicTrack
from app.services.storage import StorageService


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
    ) -> Optional[Dict[str, Any]]:
        """
        Select music based on script analysis.

        Args:
            script: The video script with hook, concept, process, conclusion
            video_duration: Total video duration in seconds
            mood_preference: Optional mood override (upbeat, calm, inspiring)

        Returns:
            Selected music track with S3 URL and metadata, or None if no tracks available
        """
        # Analyze script mood if not provided
        if not mood_preference:
            mood_preference = self._analyze_script_mood(script)

        # Query music tracks matching category and sufficient duration
        track = self.db.query(MusicTrack).filter(
            MusicTrack.category == mood_preference,
            MusicTrack.duration >= video_duration
        ).order_by(func.random()).first()

        if not track:
            # Fallback to any track with sufficient duration
            track = self.db.query(MusicTrack).filter(
                MusicTrack.duration >= video_duration
            ).order_by(func.random()).first()

        if not track:
            # No tracks available at all
            print("⚠️  No music tracks found in database")
            return None

        return {
            "track_id": track.track_id,
            "name": track.name,
            "s3_url": track.s3_url,
            "duration": track.duration,
            "category": track.category,
            "volume": 0.15  # 15% volume (background)
        }

    def _analyze_script_mood(self, script: Dict[str, Any]) -> str:
        """
        Analyze script and determine appropriate music mood.

        Uses keyword-based analysis to determine if script is:
        - upbeat: exciting, energetic content
        - calm: explanatory, thoughtful content
        - inspiring: motivational, transformative content
        """
        # Combine all script text
        text_parts = []
        for part in ["hook", "concept", "process", "conclusion"]:
            if part in script and isinstance(script[part], dict):
                text_parts.append(script[part].get("text", ""))

        text = " ".join(text_parts).lower()

        # Keyword-based mood detection
        energetic_keywords = ["exciting", "amazing", "discover", "explore", "wonder", "incredible", "wow"]
        calm_keywords = ["understand", "learn", "explain", "process", "think", "consider", "observe"]
        inspiring_keywords = ["achieve", "grow", "transform", "create", "build", "empower", "potential"]

        # Count keyword matches
        energetic_score = sum(1 for word in energetic_keywords if word in text)
        calm_score = sum(1 for word in calm_keywords if word in text)
        inspiring_score = sum(1 for word in inspiring_keywords if word in text)

        # Return category with highest score
        if energetic_score > calm_score and energetic_score > inspiring_score:
            return "upbeat"
        elif inspiring_score > calm_score and inspiring_score > energetic_score:
            return "inspiring"
        else:
            return "calm"


class MusicProcessingService:
    """
    Trims and adjusts music tracks to match video duration.
    """

    def __init__(self, storage_service: StorageService):
        self.storage_service = storage_service

    async def prepare_music_for_video(
        self,
        music_s3_url: str,
        target_duration: float,
        session_id: str,
        user_id: int,
        fade_in: float = 2.0,
        fade_out: float = 3.0,
        volume: float = 0.15
    ) -> Optional[str]:
        """
        Download, trim, and adjust music track.

        Args:
            music_s3_url: S3 URL of original music track
            target_duration: Desired duration in seconds
            session_id: Session ID for storage
            user_id: User ID for storage
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds
            volume: Volume level (0.0 to 1.0)

        Returns:
            S3 URL of processed music track, or None if processing fails
        """
        try:
            # Download original track from S3
            temp_dir = tempfile.gettempdir()
            original_path = os.path.join(temp_dir, f"music_original_{session_id}.mp3")

            # Download from S3
            await self._download_from_s3(music_s3_url, original_path)

            # Process with FFmpeg
            output_path = os.path.join(temp_dir, f"music_processed_{session_id}.mp3")

            # Build FFmpeg command
            # Trim to duration, add fade in/out, adjust volume
            fade_out_start = max(0, target_duration - fade_out)

            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-i', original_path,
                '-t', str(target_duration),
                '-af', f'afade=t=in:st=0:d={fade_in},afade=t=out:st={fade_out_start}:d={fade_out},volume={volume}',
                '-c:a', 'libmp3lame',
                '-b:a', '128k',
                output_path
            ]

            # Run FFmpeg
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Upload processed track to S3
            upload_result = await self.storage_service.upload_local_file(
                file_path=output_path,
                asset_type="audio",
                session_id=session_id,
                asset_id=f"music_{session_id}",
                user_id=user_id
            )

            # Cleanup temp files
            if os.path.exists(original_path):
                os.remove(original_path)
            if os.path.exists(output_path):
                os.remove(output_path)

            return upload_result["url"]

        except subprocess.CalledProcessError as e:
            print(f"❌ FFmpeg error processing music: {e.stderr}")
            return None
        except Exception as e:
            print(f"❌ Error processing music: {e}")
            return None

    async def _download_from_s3(self, s3_url: str, local_path: str):
        """Download file from S3 URL to local path."""
        import boto3
        import re

        # Parse S3 URL to get bucket and key
        # Format: https://bucket.s3.region.amazonaws.com/key
        match = re.match(r'https://([^.]+)\.s3\.([^.]+)\.amazonaws\.com/(.+)', s3_url)
        if not match:
            raise ValueError(f"Invalid S3 URL format: {s3_url}")

        bucket_name = match.group(1)
        region = match.group(2)
        s3_key = match.group(3)

        # Download
        s3_client = boto3.client('s3', region_name=region)
        s3_client.download_file(bucket_name, s3_key, local_path)
