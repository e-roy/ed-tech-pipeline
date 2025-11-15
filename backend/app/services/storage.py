"""
Storage Service for S3/R2
Person C - Hours 2-4: Storage Service Implementation

Purpose: Handle file uploads to S3/Cloudflare R2 and generate presigned URLs
for serving generated images and videos.
"""

import os
import boto3
import httpx
import logging
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageService:
    """
    Handles file storage operations with AWS S3 or Cloudflare R2.

    Supports:
    - Downloading files from Replicate URLs
    - Uploading to S3/R2
    - Generating presigned URLs for client access
    """

    def __init__(self):
        """Initialize S3 client with credentials from settings."""
        self.s3_client = None
        self.bucket_name = settings.S3_BUCKET_NAME

        # Only initialize if credentials are provided
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                logger.info(f"Storage service initialized with bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self.s3_client = None
        else:
            logger.warning(
                "AWS credentials not configured. Storage service will not work. "
                "Add AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME to .env"
            )

    async def download_and_upload(
        self,
        replicate_url: str,
        asset_type: str,
        session_id: str,
        asset_id: str
    ) -> Dict[str, Any]:
        """
        Download a file from Replicate and upload to S3/R2.

        Args:
            replicate_url: URL of the file from Replicate (image or video)
            asset_type: Type of asset ('image' or 'video')
            session_id: Session ID for organizing files
            asset_id: Unique asset identifier

        Returns:
            Dict containing:
                - url: S3 URL of uploaded file
                - key: S3 object key
                - size: File size in bytes

        Raises:
            ValueError: If storage service not configured
            Exception: If download or upload fails
        """
        if not self.s3_client:
            raise ValueError(
                "Storage service not configured. "
                "Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME in .env"
            )

        try:
            # Download file from Replicate
            logger.info(f"Downloading {asset_type} from Replicate: {replicate_url}")

            async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout for videos
                response = await client.get(replicate_url)
                response.raise_for_status()
                file_content = response.content

            file_size = len(file_content)
            logger.info(f"Downloaded {file_size} bytes")

            # Determine file extension
            extension = '.png' if asset_type == 'image' else '.mp4'

            # Create S3 key: sessions/{session_id}/{asset_type}s/{asset_id}.{ext}
            s3_key = f"sessions/{session_id}/{asset_type}s/{asset_id}{extension}"

            # Determine content type
            content_type = 'image/png' if asset_type == 'image' else 'video/mp4'

            # Upload to S3
            logger.info(f"Uploading to S3: {s3_key}")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                # Make files publicly readable (or use presigned URLs)
                # ACL='public-read'  # Uncomment if bucket allows public access
            )

            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

            logger.info(f"Upload successful: {s3_url}")

            return {
                "url": s3_url,
                "key": s3_key,
                "size": file_size,
                "content_type": content_type
            }

        except httpx.HTTPError as e:
            logger.error(f"Failed to download from Replicate: {e}")
            raise Exception(f"Download failed: {e}")

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise Exception(f"Upload failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in download_and_upload: {e}")
            raise

    def generate_presigned_url(
        self,
        s3_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a presigned URL for accessing a file in S3.

        Args:
            s3_key: S3 object key
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL string

        Raises:
            ValueError: If storage service not configured
            Exception: If URL generation fails
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expires_in
            )

            logger.debug(f"Generated presigned URL for {s3_key} (expires in {expires_in}s)")

            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise Exception(f"Presigned URL generation failed: {e}")

    def upload_file_direct(
        self,
        file_content: bytes,
        s3_key: str,
        content_type: str = 'application/octet-stream'
    ) -> str:
        """
        Upload file content directly to S3.

        Args:
            file_content: File bytes to upload
            s3_key: S3 object key
            content_type: MIME type of the file

        Returns:
            S3 URL of uploaded file

        Raises:
            ValueError: If storage service not configured
            Exception: If upload fails
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
            )

            s3_url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

            logger.info(f"Direct upload successful: {s3_url}")

            return s3_url

        except ClientError as e:
            logger.error(f"Direct upload failed: {e}")
            raise Exception(f"Upload failed: {e}")

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: S3 object key to delete

        Returns:
            True if deletion successful

        Raises:
            ValueError: If storage service not configured
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            logger.info(f"Deleted file: {s3_key}")
            return True

        except ClientError as e:
            logger.error(f"File deletion failed: {e}")
            return False
