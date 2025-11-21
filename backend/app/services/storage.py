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
import uuid
import json
from typing import Optional, Dict, Any, List
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

    def generate_presigned_url(
        self,
        s3_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a public URL for accessing a file in S3.
        
        Note: This returns a regular S3 URL, not a presigned URL, since the bucket
        is configured with public read access. The expires_in parameter is kept
        for backwards compatibility but is not used.

        Args:
            s3_key: S3 object key
            expires_in: URL expiration time in seconds (kept for backwards compatibility, not used)

        Returns:
            Public S3 URL string

        Raises:
            ValueError: If storage service not configured
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        # Generate regular S3 URL (bucket is publicly readable)
        # Use standard endpoint (s3.amazonaws.com) for us-east-1 buckets
        url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

        logger.debug(f"Generated public S3 URL for {s3_key}")

        return url

    def generate_s3_url_with_fallback(self, s3_key: str) -> List[str]:
        """
        Generate multiple S3 URL variants to try (with fallback endpoints).
        
        Returns a list of URLs to try in order:
        1. Standard endpoint (s3.amazonaws.com) - works for us-east-1
        2. Regional endpoint (s3.{region}.amazonaws.com) - works for other regions

        Args:
            s3_key: S3 object key

        Returns:
            List of URL strings to try in order
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        urls = [
            f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}",  # us-east-1
            f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"  # regional
        ]

        logger.debug(f"Generated {len(urls)} S3 URL variants for {s3_key}")
        return urls

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
                # Note: Bucket policy makes objects publicly readable, ACLs are disabled
            )

            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

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

    def get_user_input_path(self, user_id: int, filename: str) -> str:
        """
        Generate S3 key for user input folder.

        Args:
            user_id: User ID
            filename: Filename to store

        Returns:
            S3 key path: users/{user_id}/input/{filename}
        """
        return f"users/{user_id}/input/{filename}"

    def get_session_path(self, user_id: int, session_id: str, asset_type: str, filename: str) -> str:
        """
        Generate S3 key for session-based storage.

        Args:
            user_id: User ID
            session_id: Session ID
            asset_type: Type of asset (images, videos, audio, final, etc.)
            filename: Filename to store

        Returns:
            S3 key path: users/{user_id}/{session_id}/{asset_type}/{filename}
        """
        return f"users/{user_id}/{session_id}/{asset_type}/{filename}"

    def get_session_prefix(self, user_id: int, session_id: str, asset_type: Optional[str] = None) -> str:
        """
        Generate S3 prefix for listing session files.

        Args:
            user_id: User ID
            session_id: Session ID
            asset_type: Optional asset type filter (images, videos, audio, final, etc.)

        Returns:
            S3 prefix: users/{user_id}/{session_id}/ or users/{user_id}/{session_id}/{asset_type}/
        """
        base = f"users/{user_id}/{session_id}/"
        if asset_type:
            return f"{base}{asset_type}/"
        return base

    def get_nested_session_path(
        self,
        user_id: int,
        session_id: str,
        asset_type: str,
        subfolders: List[str],
        filename: str
    ) -> str:
        """
        Generate S3 key for nested session-based storage with additional subfolders.

        Args:
            user_id: User ID
            session_id: Session ID
            asset_type: Type of asset (images, videos, audio, etc.)
            subfolders: List of subfolder names to nest under asset_type
            filename: Filename to store

        Returns:
            S3 key path: users/{user_id}/{session_id}/{asset_type}/{subfolder1}/{subfolder2}/.../{filename}

        Example:
            get_nested_session_path(123, "abc", "images", ["Template A", "1. Introduction"], "image_1.png")
            -> "users/123/abc/images/Template A/1. Introduction/image_1.png"
        """
        base = f"users/{user_id}/{session_id}/{asset_type}"
        subfolder_path = "/".join(subfolders) if subfolders else ""
        if subfolder_path:
            return f"{base}/{subfolder_path}/{filename}"
        return f"{base}/{filename}"

    def get_user_output_path(self, user_id: int, asset_type: str, filename: str) -> str:
        """
        Generate S3 key for user output folder (deprecated - use get_session_path instead).

        Args:
            user_id: User ID
            asset_type: Type of asset (images, videos, final, audio, etc.)
            filename: Filename to store

        Returns:
            S3 key path: users/{user_id}/output/{asset_type}/{filename}
        """
        return f"users/{user_id}/output/{asset_type}/{filename}"

    async def download_and_upload(
        self,
        replicate_url: str,
        asset_type: str,
        session_id: str,
        asset_id: str,
        user_id: int,
        use_session_structure: bool = True
    ) -> Dict[str, Any]:
        """
        Download a file from Replicate and upload to S3/R2.

        Args:
            replicate_url: URL of the file from Replicate (image or video)
            asset_type: Type of asset ('image', 'video', 'clip', 'final', 'audio')
            session_id: Session ID for organizing files
            asset_id: Unique asset identifier
            user_id: User ID for organizing files in user folders
            use_session_structure: If True, use users/{user_id}/{session_id}/{asset_type} structure

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

            # Determine file extension and content type
            if asset_type == 'image' or asset_type == 'images':
                extension = '.png'
                content_type = 'image/png'
                output_type = 'images'
            elif asset_type in ['video', 'clip', 'videos']:
                extension = '.mp4'
                content_type = 'video/mp4'
                output_type = 'videos'
            elif asset_type == 'final':
                extension = '.mp4'
                content_type = 'video/mp4'
                output_type = 'final'
            elif asset_type == 'audio':
                extension = '.mp3'
                content_type = 'audio/mpeg'
                output_type = 'audio'
            else:
                extension = '.bin'
                content_type = 'application/octet-stream'
                output_type = 'other'

            # Create S3 key using session-based structure
            filename = f"{asset_id}{extension}"
            if use_session_structure:
                s3_key = self.get_session_path(user_id, session_id, output_type, filename)
            else:
                s3_key = self.get_user_output_path(user_id, output_type, filename)

            # Upload to S3
            logger.info(f"Uploading to S3: {s3_key}")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
                # Note: Bucket policy makes objects publicly readable, ACLs are disabled
            )

            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

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

    def list_user_files(
        self,
        user_id: int,
        folder: str,
        asset_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List files in user's input or output folder with metadata.

        Args:
            user_id: User ID
            folder: 'input' or 'output'
            asset_type: Optional asset type filter for output folder (images, videos, final, audio)
            limit: Maximum number of files to return (default 100)
            offset: Number of files to skip (default 0)

        Returns:
            Dict containing:
                - files: List of file info dicts (key, size, last_modified, content_type, presigned_url)
                - total: Total number of files matching the criteria

        Raises:
            ValueError: If storage service not configured or invalid folder
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        if folder not in ['input', 'output']:
            raise ValueError("Folder must be 'input' or 'output'")

        try:
            # Build prefix for listing
            if folder == 'input':
                prefix = f"users/{user_id}/input/"
            else:
                if asset_type:
                    prefix = f"users/{user_id}/output/{asset_type}/"
                else:
                    prefix = f"users/{user_id}/output/"

            # List objects with pagination
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit + offset
            )

            all_objects = []
            for page in page_iterator:
                if 'Contents' in page:
                    all_objects.extend(page['Contents'])

            # Apply offset and limit
            paginated_objects = all_objects[offset:offset + limit]
            total = len(all_objects)

            # Build file info list with presigned URLs
            files = []
            for obj in paginated_objects:
                s3_key = obj['Key']
                # Skip if it's a directory marker
                if s3_key.endswith('/'):
                    continue

                # Generate presigned URL (1 hour expiration)
                presigned_url = self.generate_presigned_url(s3_key, expires_in=3600)

                file_info = {
                    "key": s3_key,
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat() if obj.get('LastModified') else None,
                    "content_type": obj.get('ContentType', 'application/octet-stream'),
                    "presigned_url": presigned_url
                }
                files.append(file_info)

            logger.info(f"Listed {len(files)} files for user {user_id} in {folder} (total: {total})")

            return {
                "files": files,
                "total": total,
                "limit": limit,
                "offset": offset
            }

        except ClientError as e:
            logger.error(f"Failed to list user files: {e}")
            raise Exception(f"File listing failed: {e}")

    def upload_user_input(
        self,
        user_id: int,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Upload user file directly to input folder.

        Args:
            user_id: User ID
            file_content: File bytes to upload
            filename: Original filename (will be made unique with UUID if needed)
            content_type: MIME type of the file

        Returns:
            Dict containing:
                - url: S3 URL of uploaded file
                - key: S3 object key
                - size: File size in bytes

        Raises:
            ValueError: If storage service not configured
            Exception: If upload fails
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            # Generate unique filename if needed (add UUID prefix)
            file_ext = os.path.splitext(filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_ext}"

            # Generate S3 key
            s3_key = self.get_user_input_path(user_id, unique_filename)

            # Upload to S3
            logger.info(f"Uploading user input file to S3: {s3_key}")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
                # Note: Bucket policy makes objects publicly readable, ACLs are disabled
            )

            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

            logger.info(f"User input upload successful: {s3_url}")

            return {
                "url": s3_url,
                "key": s3_key,
                "size": len(file_content),
                "content_type": content_type,
                "original_filename": filename
            }

        except ClientError as e:
            logger.error(f"User input upload failed: {e}")
            raise Exception(f"Upload failed: {e}")

    def upload_prompt_config(
        self,
        user_id: int,
        config_data: dict,
        session_id: str
    ) -> str:
        """
        Store prompt/config as JSON file in input folder.

        Args:
            user_id: User ID
            config_data: Configuration data to store as JSON
            session_id: Session ID for filename

        Returns:
            S3 key of uploaded file

        Raises:
            ValueError: If storage service not configured
            Exception: If upload fails
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            # Generate filename
            filename = f"prompt-{session_id}.json"
            s3_key = self.get_user_input_path(user_id, filename)

            # Convert config to JSON
            json_content = json.dumps(config_data, indent=2).encode('utf-8')

            # Upload to S3
            logger.info(f"Uploading prompt config to S3: {s3_key}")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_content,
                ContentType='application/json'
                # Note: Bucket policy makes objects publicly readable, ACLs are disabled
            )

            logger.info(f"Prompt config upload successful: {s3_key}")

            return s3_key

        except ClientError as e:
            logger.error(f"Prompt config upload failed: {e}")
            raise Exception(f"Upload failed: {e}")

    async def upload_local_file(
        self,
        file_path: str,
        asset_type: str,
        session_id: str,
        asset_id: str,
        user_id: int,
        use_session_structure: bool = True
    ) -> Dict[str, Any]:
        """
        Upload a local file to S3/R2.

        Args:
            file_path: Local path to file
            asset_type: Type of asset ('image', 'video', 'clip', 'final', 'audio')
            session_id: Session ID for organizing files
            asset_id: Unique asset identifier
            user_id: User ID for organizing files in user folders
            use_session_structure: If True, use users/{user_id}/{session_id}/{asset_type} structure

        Returns:
            Dict containing:
                - url: S3 URL of uploaded file
                - key: S3 object key
                - size: File size in bytes

        Raises:
            ValueError: If storage service not configured
            Exception: If upload fails
        """
        if not self.s3_client:
            raise ValueError(
                "Storage service not configured. "
                "Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME in .env"
            )

        try:
            # Read file from local disk
            logger.info(f"Reading local file: {file_path}")

            with open(file_path, 'rb') as f:
                file_content = f.read()

            file_size = len(file_content)
            logger.info(f"Read {file_size} bytes")

            # Determine file extension and content type
            if asset_type == 'image' or asset_type == 'images':
                extension = '.png'
                content_type = 'image/png'
                output_type = 'images'
            elif asset_type in ['video', 'clip', 'videos']:
                extension = '.mp4'
                content_type = 'video/mp4'
                output_type = 'videos'
            elif asset_type == 'final':
                extension = '.mp4'
                content_type = 'video/mp4'
                output_type = 'final'
            elif asset_type == 'audio':
                extension = '.mp3'
                content_type = 'audio/mpeg'
                output_type = 'audio'
            else:
                extension = os.path.splitext(file_path)[1] or '.bin'
                content_type = 'application/octet-stream'
                output_type = 'other'

            # Create S3 key using session-based structure
            filename = f"{asset_id}{extension}"
            if use_session_structure:
                s3_key = self.get_session_path(user_id, session_id, output_type, filename)
            else:
                s3_key = self.get_user_output_path(user_id, output_type, filename)

            # Upload to S3
            logger.info(f"Uploading to S3: {s3_key}")

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type
                # Note: Bucket policy makes objects publicly readable, ACLs are disabled
            )

            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

            logger.info(f"Upload successful: {s3_url}")

            return {
                "url": s3_url,
                "key": s3_key,
                "size": file_size,
                "content_type": content_type
            }

        except FileNotFoundError as e:
            logger.error(f"Local file not found: {e}")
            raise Exception(f"File not found: {e}")

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise Exception(f"Upload failed: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in upload_local_file: {e}")
            raise

    def delete_user_file(self, user_id: int, s3_key: str) -> bool:
        """
        Delete a file from user folders with ownership verification.

        Args:
            user_id: User ID (for ownership verification)
            s3_key: S3 object key to delete

        Returns:
            True if deletion successful

        Raises:
            ValueError: If storage service not configured or user doesn't own the file
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        # Verify user owns the file by checking key prefix
        expected_prefix = f"users/{user_id}/"
        if not s3_key.startswith(expected_prefix):
            raise ValueError(f"File does not belong to user {user_id}")

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            logger.info(f"Deleted user file: {s3_key}")
            return True

        except ClientError as e:
            logger.error(f"File deletion failed: {e}")
            return False

    def read_file(self, s3_key: str) -> bytes:
        """
        Read a file from S3.

        Args:
            s3_key: S3 object key

        Returns:
            File content as bytes

        Raises:
            ValueError: If storage service not configured
            Exception: If file read fails
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            file_content = response['Body'].read()
            logger.debug(f"Read {len(file_content)} bytes from S3: {s3_key}")
            return file_content

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchKey':
                logger.error(f"File not found in S3: {s3_key}")
                raise FileNotFoundError(f"File not found in S3: {s3_key}")
            logger.error(f"Failed to read file from S3: {e}")
            raise Exception(f"Failed to read file from S3: {e}")

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if file exists, False otherwise

        Raises:
            ValueError: If storage service not configured
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == '404' or error_code == 'NoSuchKey':
                return False
            # Re-raise other errors
            logger.error(f"Error checking file existence: {e}")
            raise Exception(f"Error checking file existence: {e}")

    def list_files_by_prefix(self, s3_prefix: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        List files in S3 by prefix with presigned URLs.

        Args:
            s3_prefix: S3 key prefix (e.g., "users/123/session456/images/")
            limit: Maximum number of files to return

        Returns:
            List of file info dicts with keys: key, size, last_modified, presigned_url

        Raises:
            ValueError: If storage service not configured
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=s3_prefix,
                MaxKeys=limit
            )

            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        s3_key = obj['Key']
                        # Skip directory markers
                        if s3_key.endswith('/'):
                            continue

                        # Generate presigned URL
                        presigned_url = self.generate_presigned_url(s3_key, expires_in=3600)

                        files.append({
                            "key": s3_key,
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat() if obj.get('LastModified') else None,
                            "presigned_url": presigned_url
                        })

            logger.debug(f"Listed {len(files)} files with prefix {s3_prefix}")
            return files

        except ClientError as e:
            logger.error(f"Failed to list files by prefix: {e}")
            raise Exception(f"File listing failed: {e}")

    def list_directory_structure(
        self,
        user_id: int,
        prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List directory structure under users/{user_id}/ with folders and files.
        Uses S3 delimiter to get folder structure.

        Args:
            user_id: User ID
            prefix: Optional subdirectory prefix (e.g., "input" or "session_id/images")

        Returns:
            Dict with 'folders' and 'files' lists. Each folder has 'name' and 'path'.
            Each file has 'key', 'size', 'last_modified', 'content_type', 'presigned_url'.
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        base_prefix = f"users/{user_id}/"
        if prefix:
            full_prefix = f"{base_prefix}{prefix}"
            if not full_prefix.endswith('/'):
                full_prefix += '/'
        else:
            full_prefix = base_prefix

        try:
            # List objects with delimiter to separate folders and files
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=full_prefix,
                Delimiter='/'
            )

            folders = []
            files = []

            for page in page_iterator:
                # Get folders (CommonPrefixes)
                if 'CommonPrefixes' in page:
                    for common_prefix in page['CommonPrefixes']:
                        folder_path = common_prefix['Prefix']
                        # Extract folder name (relative to base_prefix)
                        folder_name = folder_path[len(full_prefix):].rstrip('/')
                        folders.append({
                            "name": folder_name,
                            "path": folder_path
                        })

                # Get files (Contents)
                if 'Contents' in page:
                    for obj in page['Contents']:
                        s3_key = obj['Key']
                        # Skip directory markers
                        if s3_key.endswith('/'):
                            continue

                        # Generate presigned URL
                        presigned_url = self.generate_presigned_url(s3_key, expires_in=3600)

                        # Extract file name
                        file_name = s3_key[len(full_prefix):]

                        files.append({
                            "key": s3_key,
                            "name": file_name,
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat() if obj.get('LastModified') else None,
                            "content_type": obj.get('ContentType', 'application/octet-stream'),
                            "presigned_url": presigned_url
                        })

            logger.info(f"Listed directory structure for user {user_id} at prefix '{prefix}': {len(folders)} folders, {len(files)} files")
            
            return {
                "folders": folders,
                "files": files,
                "prefix": full_prefix
            }

        except ClientError as e:
            logger.error(f"Failed to list directory structure: {e}")
            raise Exception(f"Directory listing failed: {e}")

    def copy_file(self, source_key: str, dest_key: str) -> str:
        """
        Copy a file within the same S3 bucket.

        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key

        Returns:
            S3 URL of copied file

        Raises:
            ValueError: If storage service not configured
            Exception: If copy fails
        """
        if not self.s3_client:
            raise ValueError("Storage service not configured")

        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )

            s3_url = f"https://{self.bucket_name}.s3.amazonaws.com/{dest_key}"
            logger.info(f"Copied file from {source_key} to {dest_key}")
            return s3_url

        except ClientError as e:
            logger.error(f"File copy failed: {e}")
            raise Exception(f"Copy failed: {e}")