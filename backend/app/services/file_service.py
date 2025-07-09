# backend/app/services/file_service.py

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, List, Dict, Any
import os
import uuid
import shutil
import mimetypes
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles

from app.models.database import PersonFile, Person, FamilyTree
from app.core.config import settings

class FileStorageInterface(ABC):
    """Abstract interface for file storage - easily swappable for different storage backends."""
    
    @abstractmethod
    async def upload_file(self, file: UploadFile, file_path: str) -> str:
        """Upload file and return the storage path."""
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """Download file contents."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file and return success status."""
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """Get URL to access the file."""
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        pass

class LocalFileStorage(FileStorageInterface):
    """Local file system storage implementation with async file operations."""
    
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True, parents=True)
    
    async def upload_file(self, file: UploadFile, file_path: str) -> str:
        """Upload file to local storage with async operations."""
        try:
            full_path = self.base_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use aiofiles for async file operations
            async with aiofiles.open(full_path, "wb") as buffer:
                content = await file.read()
                await buffer.write(content)
            
            # Reset file pointer for potential reuse
            await file.seek(0)
            
            return str(file_path)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from local storage with async operations."""
        try:
            full_path = self.base_path / file_path
            
            if not full_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            async with aiofiles.open(full_path, "rb") as buffer:
                return await buffer.read()
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download file: {str(e)}"
            )
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage."""
        try:
            full_path = self.base_path / file_path
            
            if full_path.exists():
                full_path.unlink()
                return True
            return False
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    async def get_file_url(self, file_path: str) -> str:
        """Get URL for local file access."""
        return f"/files/{file_path}"
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage."""
        full_path = self.base_path / file_path
        return full_path.exists()

class FileService:
    """
    Async service for managing person files with pluggable storage backends.
    Handles file uploads, downloads, metadata management, and validation.
    """
    
    def __init__(self, db: AsyncSession, storage: FileStorageInterface = None):
        self.db = db
        self.storage = storage or LocalFileStorage()
        
        # File validation settings - use the property method for allowed file types
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_file_types = settings.allowed_file_types_list
    
    async def upload_person_file(
        self, 
        person_id: uuid.UUID, 
        file: UploadFile,
        description: Optional[str] = None
    ) -> PersonFile:
        """Upload a file for a specific person with comprehensive validation."""
        # Validate file
        await self._validate_file(file)
        
        # Verify person exists
        await self._verify_person_exists(person_id)
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename or "")[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = f"people/{person_id}/{unique_filename}"
        
        # Upload to storage
        stored_path = await self.storage.upload_file(file, file_path)
        
        # Create database record
        file_record = PersonFile(
            person_id=person_id,
            filename=unique_filename,
            original_filename=file.filename or "unknown",
            file_path=stored_path,
            file_type=self._get_file_type(file.content_type or ""),
            mime_type=file.content_type or "application/octet-stream",
            file_size=len(await file.read()),
            description=description
        )
        
        # Reset file pointer after reading size
        await file.seek(0)
        
        self.db.add(file_record)
        await self.db.commit()
        await self.db.refresh(file_record)
        
        return file_record
    
    async def get_person_file(self, file_id: uuid.UUID) -> PersonFile:
        """Get a person file by ID."""
        stmt = select(PersonFile).where(PersonFile.id == file_id)
        result = await self.db.execute(stmt)
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return file_record
    
    async def download_person_file(self, file_id: uuid.UUID) -> tuple[bytes, str, str]:
        """Download a person file."""
        file_record = await self.get_person_file(file_id)
        file_content = await self.storage.download_file(file_record.file_path)
        
        return file_content, file_record.original_filename, file_record.mime_type
    
    async def delete_person_file(self, file_id: uuid.UUID) -> bool:
        """Delete a person file."""
        file_record = await self.get_person_file(file_id)
        
        # Delete from storage
        storage_deleted = await self.storage.delete_file(file_record.file_path)
        
        # Delete from database
        await self.db.delete(file_record)
        await self.db.commit()
        
        return storage_deleted
    
    async def get_person_files(self, person_id: uuid.UUID, file_type: Optional[str] = None) -> List[PersonFile]:
        """Get all files for a person."""
        stmt = select(PersonFile).where(PersonFile.person_id == person_id)
        
        if file_type:
            stmt = stmt.where(PersonFile.file_type == file_type)
        
        stmt = stmt.order_by(PersonFile.uploaded_at.desc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file against business rules."""
        # Check filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Check content type
        if file.content_type not in self.allowed_file_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(self.allowed_file_types)}"
            )
        
        # Check file size
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer
        
        if file_size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size {file_size} bytes exceeds maximum {self.max_file_size} bytes"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty files are not allowed"
            )

    def _get_file_type(self, mime_type: str) -> str:
        """Categorize file by MIME type."""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type in ['application/pdf', 'text/plain', 'application/msword', 
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'document'
        else:
            return 'other'

    async def _get_person(self, person_id: uuid.UUID) -> Person:
        """Get person with family tree relationship loaded."""
        stmt = select(Person).where(Person.id == person_id)
        result = await self.db.execute(stmt)
        person = result.scalar_one_or_none()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        return person

    async def _verify_person_exists(self, person_id: uuid.UUID) -> None:
        """Verify that a person exists."""
        await self._get_person(person_id)

# Factory function for dependency injection
def get_file_storage() -> FileStorageInterface:
    """Factory function to get the appropriate file storage implementation."""
    storage_type = getattr(settings, 'FILE_STORAGE_TYPE', 'local')
    
    if storage_type == 'local':
        upload_path = getattr(settings, 'UPLOAD_PATH', 'uploads')
        return LocalFileStorage(upload_path)
    elif storage_type == 'oracle':
        # TODO: Implement Oracle Object Storage
        raise NotImplementedError("Oracle Object Storage not implemented yet")
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")