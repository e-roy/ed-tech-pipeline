"""
Storage routes - handle user file uploads, listing, and management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json

from app.database import get_db
from app.models.database import User
from app.routes.auth import get_current_user
from app.services.storage import StorageService

router = APIRouter()

# Initialize storage service
storage_service = StorageService()


# Response models
class FileInfo(BaseModel):
    """File information model."""
    key: str
    size: int
    last_modified: Optional[str]
    content_type: str
    presigned_url: str


class FileListResponse(BaseModel):
    """File list response model."""
    files: List[FileInfo]
    total: int
    limit: int
    offset: int


class UploadInputResponse(BaseModel):
    """Upload input file response model."""
    url: str
    key: str
    size: int
    content_type: str
    original_filename: str


class UploadPromptConfigRequest(BaseModel):
    """Upload prompt config request model."""
    config_data: dict
    session_id: str


class PresignedUrlResponse(BaseModel):
    """Presigned URL response model."""
    presigned_url: str
    expires_in: int


class FolderInfo(BaseModel):
    """Folder information model."""
    name: str
    path: str


class DirectoryFileInfo(BaseModel):
    """File information model for directory listing."""
    key: str
    name: str
    size: int
    last_modified: Optional[str]
    content_type: str
    presigned_url: str


class DirectoryStructureResponse(BaseModel):
    """Directory structure response model."""
    folders: List[FolderInfo]
    files: List[DirectoryFileInfo]
    prefix: str


@router.post("/upload-input", response_model=UploadInputResponse)
async def upload_input_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a user file to the input folder.

    Accepts any file type via multipart/form-data.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Get content type from file or default
        content_type = file.content_type or 'application/octet-stream'
        
        # Upload to S3
        result = storage_service.upload_user_input(
            user_id=current_user.id,
            file_content=file_content,
            filename=file.filename or "upload",
            content_type=content_type
        )
        
        return UploadInputResponse(
            url=result["url"],
            key=result["key"],
            size=result["size"],
            content_type=result["content_type"],
            original_filename=result["original_filename"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload-prompt-config")
async def upload_prompt_config(
    request: UploadPromptConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store prompt/config as JSON file in input folder.

    Creates a file named prompt-{session_id}.json in the user's input folder.
    """
    try:
        s3_key = storage_service.upload_prompt_config(
            user_id=current_user.id,
            config_data=request.config_data,
            session_id=request.session_id
        )
        
        return {
            "status": "success",
            "key": s3_key,
            "session_id": request.session_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files", response_model=FileListResponse)
async def list_user_files(
    folder: str,
    asset_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List files in user's input or output folder.

    Query parameters:
    - folder: 'input' or 'output' (required)
    - asset_type: Optional filter for output folder (images, videos, final, audio)
    - limit: Maximum number of files to return (default 100)
    - offset: Number of files to skip (default 0)
    """
    try:
        if folder not in ['input', 'output']:
            raise HTTPException(
                status_code=400,
                detail="Folder must be 'input' or 'output'"
            )
        
        result = storage_service.list_user_files(
            user_id=current_user.id,
            folder=folder,
            asset_type=asset_type,
            limit=limit,
            offset=offset
        )
        
        # Convert to FileInfo models
        file_list = [
            FileInfo(
                key=f["key"],
                size=f["size"],
                last_modified=f["last_modified"],
                content_type=f["content_type"],
                presigned_url=f["presigned_url"]
            )
            for f in result["files"]
        ]
        
        return FileListResponse(
            files=file_list,
            total=result["total"],
            limit=result["limit"],
            offset=result["offset"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File listing failed: {str(e)}")


@router.get("/files/{file_key:path}/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(
    file_key: str,
    expires_in: int = 3600,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a presigned URL for accessing a file.

    Verifies that the file belongs to the current user.
    """
    try:
        # Verify user owns the file
        expected_prefix = f"users/{current_user.id}/"
        if not file_key.startswith(expected_prefix):
            raise HTTPException(
                status_code=403,
                detail="File does not belong to user"
            )
        
        presigned_url = storage_service.generate_presigned_url(
            s3_key=file_key,
            expires_in=expires_in
        )
        
        return PresignedUrlResponse(
            presigned_url=presigned_url,
            expires_in=expires_in
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {str(e)}")


@router.delete("/files/{file_key:path}")
async def delete_user_file(
    file_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file from user's folders.

    Verifies that the file belongs to the current user before deletion.
    """
    try:
        success = storage_service.delete_user_file(
            user_id=current_user.id,
            s3_key=file_key
        )
        
        if success:
            return {
                "status": "success",
                "message": "File deleted successfully",
                "key": file_key
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="File deletion failed"
            )
    
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")


@router.get("/directory", response_model=DirectoryStructureResponse)
async def list_directory_structure(
    prefix: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List directory structure under users/{user_id}/ with folders and files.
    
    Query parameters:
    - prefix: Optional subdirectory prefix (e.g., "input" or "session_id/images")
    
    Returns folders and files in the specified directory.
    """
    try:
        result = storage_service.list_directory_structure(
            user_id=current_user.id,
            prefix=prefix
        )
        
        # Convert to response models
        folder_list = [
            FolderInfo(name=f["name"], path=f["path"])
            for f in result["folders"]
        ]
        
        file_list = [
            DirectoryFileInfo(
                key=f["key"],
                name=f["name"],
                size=f["size"],
                last_modified=f["last_modified"],
                content_type=f["content_type"],
                presigned_url=f["presigned_url"]
            )
            for f in result["files"]
        ]
        
        return DirectoryStructureResponse(
            folders=folder_list,
            files=file_list,
            prefix=result["prefix"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Directory listing failed: {str(e)}")

