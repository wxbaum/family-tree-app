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
                    detail=f"File not found: {file_path}"
                )
            
            async with aiofiles.open(full_path, "rb") as f:
                return await f.read()
                
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
                
                # Clean up empty directories
                try:
                    full_path.parent.rmdir()
                except OSError:
                    pass  # Directory not empty, which is fine
                
                return True
            return False
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    async def get_file_url(self, file_path: str) -> str:
        """Get URL to access the file via API."""
        return f"/api/v1/files/download/{file_path}"
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage."""
        full_path = self.base_path / file_path
        return full_path.exists()

class OracleObjectStorage(FileStorageInterface):
    """Oracle Object Storage implementation - production ready interface."""
    
    def __init__(self, namespace: str, bucket: str, access_key: str, secret_key: str, region: str, endpoint: str):
        self.namespace = namespace
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.endpoint = endpoint
        # TODO: Initialize OCI client when implementing
        # self.client = oci.object_storage.ObjectStorageClient(config)
    
    async def upload_file(self, file: UploadFile, file_path: str) -> str:
        """Upload file to Oracle Object Storage."""
        # TODO: Implement Oracle Object Storage upload
        raise NotImplementedError("Oracle Object Storage not implemented yet")
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from Oracle Object Storage."""
        # TODO: Implement Oracle Object Storage download
        raise NotImplementedError("Oracle Object Storage not implemented yet")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Oracle Object Storage."""
        # TODO: Implement Oracle Object Storage delete
        raise NotImplementedError("Oracle Object Storage not implemented yet")
    
    async def get_file_url(self, file_path: str) -> str:
        """Generate signed URL for Oracle Object Storage."""
        # TODO: Generate signed URL for Oracle Object Storage
        raise NotImplementedError("Oracle Object Storage not implemented yet")
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in Oracle Object Storage."""
        # TODO: Implement file existence check
        raise NotImplementedError("Oracle Object Storage not implemented yet")

class FileService:
    """
    Async service for managing person files with pluggable storage backends.
    Handles file uploads, downloads, metadata management, and validation.
    """
    
    def __init__(self, db: AsyncSession, storage: FileStorageInterface = None):
        self.db = db
        self.storage = storage or LocalFileStorage()
        
        # File validation settings
        self.max_file_size = getattr(settings, 'MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB default
        self.allowed_file_types = getattr(settings, 'ALLOWED_FILE_TYPES', [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'video/mp4', 'video/avi', 'video/mov', 'audio/mpeg', 'audio/wav'
        ])

    async def upload_person_file(
        self, 
        person_id: uuid.UUID, 
        file: UploadFile,
        description: Optional[str] = None
    ) -> PersonFile:
        """
        Upload a file for a specific person with comprehensive validation.
        
        Args:
            person_id: UUID of the person
            file: Uploaded file object
            description: Optional file description
            
        Returns:
            Created PersonFile instance
            
        Raises:
            HTTPException: If validation fails or upload fails
        """
        try:
            # Verify person exists and get their details
            person = await self._get_person(person_id)
            
            # Validate file
            await self._validate_file(file)
            
            # Generate unique filename and path
            file_extension = Path(file.filename).suffix.lower() if file.filename else ""
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Create hierarchical storage path: owner_id/family_tree_id/person_id/filename
            file_path = f"{person.family_tree.owner_id}/{person.family_tree_id}/{person_id}/{unique_filename}"
            
            # Get file size
            content = await file.read()
            file_size = len(content)
            await file.seek(0)  # Reset file pointer
            
            # Upload to storage
            storage_path = await self.storage.upload_file(file, file_path)
            
            # Determine file type from MIME type
            file_type = self._get_file_type(file.content_type)
            
            # Create database record
            db_file = PersonFile(
                person_id=person_id,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=storage_path,
                file_type=file_type,
                mime_type=file.content_type,
                file_size=file_size,
                description=description
            )
            
            self.db.add(db_file)
            await self.db.commit()
            await self.db.refresh(db_file)
            
            return db_file
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            # Clean up uploaded file if database operation failed
            try:
                await self.storage.delete_file(file_path)
            except:
                pass  # Don't mask the original error
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )

    async def download_person_file(self, file_id: uuid.UUID) -> tuple[bytes, PersonFile]:
        """
        Download a person file by ID.
        
        Args:
            file_id: UUID of the file
            
        Returns:
            Tuple of (file_content, file_metadata)
            
        Raises:
            HTTPException: If file not found
        """
        try:
            # Get file metadata
            db_file = await self.get_person_file(file_id)
            
            # Download from storage
            file_content = await self.storage.download_file(db_file.file_path)
            
            return file_content, db_file
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download file: {str(e)}"
            )

    async def get_person_file(self, file_id: uuid.UUID) -> PersonFile:
        """
        Get person file metadata by ID.
        
        Args:
            file_id: UUID of the file
            
        Returns:
            PersonFile instance
            
        Raises:
            HTTPException: If file not found
        """
        stmt = select(PersonFile).where(PersonFile.id == file_id)
        result = await self.db.execute(stmt)
        db_file = result.scalar_one_or_none()
        
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return db_file

    async def get_person_files(self, person_id: uuid.UUID, file_type: Optional[str] = None) -> List[PersonFile]:
        """
        Get all files for a specific person, optionally filtered by type.
        
        Args:
            person_id: UUID of the person
            file_type: Optional file type filter (image, document, video, audio, other)
            
        Returns:
            List of PersonFile instances
        """
        try:
            # Verify person exists
            await self._verify_person_exists(person_id)
            
            stmt = select(PersonFile).where(PersonFile.person_id == person_id)
            
            if file_type:
                stmt = stmt.where(PersonFile.file_type == file_type)
            
            stmt = stmt.order_by(PersonFile.created_at.desc())
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get person files: {str(e)}"
            )

    async def delete_person_file(self, file_id: uuid.UUID) -> None:
        """
        Delete a person file and its storage.
        
        Args:
            file_id: UUID of the file to delete
            
        Raises:
            HTTPException: If file not found or deletion fails
        """
        try:
            # Get file metadata
            db_file = await self.get_person_file(file_id)
            
            # Delete from storage
            storage_deleted = await self.storage.delete_file(db_file.file_path)
            
            # Delete from database
            await self.db.delete(db_file)
            await self.db.commit()
            
            if not storage_deleted:
                # Log warning but don't fail - database cleanup is more important
                print(f"Warning: Storage file not found during deletion: {db_file.file_path}")
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )

    async def update_file_metadata(self, file_id: uuid.UUID, description: Optional[str] = None) -> PersonFile:
        """
        Update file metadata (currently only description).
        
        Args:
            file_id: UUID of the file
            description: New description
            
        Returns:
            Updated PersonFile instance
        """
        try:
            db_file = await self.get_person_file(file_id)
            
            if description is not None:
                db_file.description = description
            
            await self.db.commit()
            await self.db.refresh(db_file)
            
            return db_file
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update file metadata: {str(e)}"
            )

    async def get_family_tree_files(self, family_tree_id: uuid.UUID, file_type: Optional[str] = None, 
                                   limit: Optional[int] = None, offset: Optional[int] = None) -> List[PersonFile]:
        """
        Get all files in a family tree with optional filtering and pagination.
        
        Args:
            family_tree_id: UUID of the family tree
            file_type: Optional file type filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of PersonFile instances
        """
        try:
            # Verify family tree exists
            await self._verify_family_tree_exists(family_tree_id)
            
            stmt = select(PersonFile).join(
                Person, PersonFile.person_id == Person.id
            ).where(Person.family_tree_id == family_tree_id)
            
            if file_type:
                stmt = stmt.where(PersonFile.file_type == file_type)
            
            stmt = stmt.order_by(PersonFile.created_at.desc())
            
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get family tree files: {str(e)}"
            )

    async def get_file_statistics(self, family_tree_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get file statistics for a family tree.
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            Dictionary with file statistics
        """
        try:
            files = await self.get_family_tree_files(family_tree_id)
            
            total_files = len(files)
            total_size = sum(f.file_size for f in files)
            
            # Count by file type
            by_type = {}
            for f in files:
                file_type = f.file_type
                by_type[file_type] = by_type.get(file_type, 0) + 1
            
            # Count by MIME type
            by_mime = {}
            for f in files:
                mime_type = f.mime_type
                by_mime[mime_type] = by_mime.get(mime_type, 0) + 1
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "by_file_type": by_type,
                "by_mime_type": by_mime,
                "average_file_size_bytes": round(total_size / total_files, 2) if total_files > 0 else 0
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get file statistics: {str(e)}"
            )

    async def search_files(self, family_tree_id: uuid.UUID, search_term: str, 
                          file_type: Optional[str] = None) -> List[PersonFile]:
        """
        Search files by filename or description.
        
        Args:
            family_tree_id: UUID of the family tree
            search_term: Term to search for
            file_type: Optional file type filter
            
        Returns:
            List of matching PersonFile instances
        """
        try:
            stmt = select(PersonFile).join(
                Person, PersonFile.person_id == Person.id
            ).where(
                Person.family_tree_id == family_tree_id,
                (
                    PersonFile.original_filename.ilike(f"%{search_term}%") |
                    PersonFile.description.ilike(f"%{search_term}%")
                )
            )
            
            if file_type:
                stmt = stmt.where(PersonFile.file_type == file_type)
            
            stmt = stmt.order_by(PersonFile.created_at.desc())
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search files: {str(e)}"
            )

    # Private helper methods

    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file against business rules."""
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

    async def _verify_family_tree_exists(self, family_tree_id: uuid.UUID) -> None:
        """Verify that a family tree exists."""
        stmt = select(FamilyTree).where(FamilyTree.id == family_tree_id)
        result = await self.db.execute(stmt)
        family_tree = result.scalar_one_or_none()
        
        if not family_tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family tree not found"
            )

# Factory function for dependency injection
def get_file_storage() -> FileStorageInterface:
    """
    Factory function to get the appropriate file storage implementation.
    This can be configured based on environment or settings.
    """
    storage_type = getattr(settings, 'FILE_STORAGE_TYPE', 'local')
    
    if storage_type == 'local':
        upload_path = getattr(settings, 'UPLOAD_PATH', 'uploads')
        return LocalFileStorage(upload_path)
    elif storage_type == 'oracle':
        # Oracle Object Storage configuration
        return OracleObjectStorage(
            namespace=getattr(settings, 'ORACLE_NAMESPACE', ''),
            bucket=getattr(settings, 'ORACLE_BUCKET', ''),
            access_key=getattr(settings, 'ORACLE_ACCESS_KEY', ''),
            secret_key=getattr(settings, 'ORACLE_SECRET_KEY', ''),
            region=getattr(settings, 'ORACLE_REGION', ''),
            endpoint=getattr(settings, 'ORACLE_ENDPOINT', '')
        )
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")

# Export for easy importing
__all__ = [
    "FileService",
    "FileStorageInterface", 
    "LocalFileStorage",
    "OracleObjectStorage",
    "get_file_storage"
]