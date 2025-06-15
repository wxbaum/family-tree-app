from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
import os
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.database import PersonFile
from app.core.config import settings

class FileStorageInterface(ABC):
    """Abstract interface for file storage - easily swappable"""
    
    @abstractmethod
    async def upload_file(self, file: UploadFile, file_path: str) -> str:
        """Upload file and return the storage path"""
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """Download file contents"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """Get URL to access the file"""
        pass

class LocalFileStorage(FileStorageInterface):
    """Local file storage implementation"""
    
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    async def upload_file(self, file: UploadFile, file_path: str) -> str:
        """Upload file to local storage"""
        full_path = self.base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return str(file_path)
    
    async def download_file(self, file_path: str) -> bytes:
        """Download file from local storage"""
        full_path = self.base_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(full_path, "rb") as f:
            return f.read()
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        full_path = self.base_path / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    async def get_file_url(self, file_path: str) -> str:
        """Get URL to access the file via API"""
        return f"/api/v1/files/{file_path}"

class OracleObjectStorage(FileStorageInterface):
    """Oracle Object Storage implementation - placeholder for future"""
    
    def __init__(self, namespace: str, bucket: str, access_key: str, secret_key: str, region: str):
        self.namespace = namespace
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        # TODO: Initialize OCI client
    
    async def upload_file(self, file: UploadFile, file_path: str) -> str:
        # TODO: Implement Oracle Object Storage upload
        raise NotImplementedError("Oracle Object Storage not implemented yet")
    
    async def download_file(self, file_path: str) -> bytes:
        # TODO: Implement Oracle Object Storage download
        raise NotImplementedError("Oracle Object Storage not implemented yet")
    
    async def delete_file(self, file_path: str) -> bool:
        # TODO: Implement Oracle Object Storage delete
        raise NotImplementedError("Oracle Object Storage not implemented yet")
    
    async def get_file_url(self, file_path: str) -> str:
        # TODO: Generate signed URL for Oracle Object Storage
        raise NotImplementedError("Oracle Object Storage not implemented yet")

class FileService:
    """Service for managing person files with pluggable storage"""
    
    def __init__(self, db: Session, storage: FileStorageInterface = None):
        self.db = db
        self.storage = storage or LocalFileStorage()
    
    async def upload_person_file(
        self, 
        person_id: uuid.UUID, 
        file: UploadFile,
        description: Optional[str] = None
    ) -> PersonFile:
        """Upload a file for a person"""
        
        # Validate file type
        if file.content_type not in settings.ALLOWED_FILE_TYPES:
            raise ValueError(f"File type {file.content_type} not allowed")
        
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size {file_size} exceeds maximum {settings.MAX_FILE_SIZE}")
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create storage path: user_id/family_tree_id/person_id/filename
        from app.services.person_service import PersonService
        person_service = PersonService(self.db)
        person = person_service.get_person(person_id)
        
        file_path = f"{person.family_tree.owner_id}/{person.family_tree_id}/{person_id}/{unique_filename}"
        
        # Upload to storage
        storage_path = await self.storage.upload_file(file, file_path)
        
        # Create database record
        db_file = PersonFile(
            person_id=person_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=storage_path,
            file_type=self._get_file_type(file.content_type),
            mime_type=file.content_type,
            file_size=file_size,
            description=description
        )
        
        self.db.add(db_file)
        self.db.commit()
        self.db.refresh(db_file)
        
        return db_file
    
    async def get_file_content(self, file_id: uuid.UUID) -> tuple[bytes, str, str]:
        """Get file content, filename, and mime type"""
        db_file = self.db.query(PersonFile).filter(PersonFile.id == file_id).first()
        if not db_file:
            raise ValueError("File not found")
        
        content = await self.storage.download_file(db_file.file_path)
        return content, db_file.original_filename, db_file.mime_type
    
    async def delete_person_file(self, file_id: uuid.UUID) -> bool:
        """Delete a person's file"""
        db_file = self.db.query(PersonFile).filter(PersonFile.id == file_id).first()
        if not db_file:
            return False
        
        # Delete from storage
        await self.storage.delete_file(db_file.file_path)
        
        # Delete from database
        self.db.delete(db_file)
        self.db.commit()
        
        return True
    
    def get_person_files(self, person_id: uuid.UUID) -> list[PersonFile]:
        """Get all files for a person"""
        return self.db.query(PersonFile).filter(
            PersonFile.person_id == person_id
        ).order_by(PersonFile.uploaded_at.desc()).all()
    
    def _get_file_type(self, mime_type: str) -> str:
        """Determine file type from mime type"""
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type == "application/pdf":
            return "pdf"
        else:
            return "document"

# Factory function for easy switching
def get_file_storage() -> FileStorageInterface:
    """Factory function to get the appropriate storage implementation"""
    
    # For now, always return local storage
    # Later, check config and return Oracle/AWS/etc.
    if settings.ORACLE_NAMESPACE and settings.ORACLE_ACCESS_KEY:
        # TODO: Return Oracle Object Storage when implemented
        pass
    
    return LocalFileStorage()