# backend/app/api/v1/endpoints/files.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import io

from app.core.database import get_database_session
from app.core.auth import current_active_user
from app.models.database import User
from app.schemas.schemas import PersonFileRead, MessageResponse
from app.services.file_service import FileService, get_file_storage
from app.services.person_service import PersonService
from app.services.family_tree_service import FamilyTreeService

router = APIRouter()

async def verify_person_access(person_id: uuid.UUID, current_user: User, db: AsyncSession):
    """Helper to verify user can access the person."""
    person_service = PersonService(db)
    person = await person_service.get_person(person_id)
    
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(person.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this person's files"
        )
    
    return person

async def verify_family_tree_access(family_tree_id: uuid.UUID, current_user: User, db: AsyncSession):
    """Helper to verify user can access the family tree."""
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    return family_tree

async def verify_file_access(file_id: uuid.UUID, current_user: User, db: AsyncSession):
    """Helper to verify user can access the file."""
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    db_file = await file_service.get_person_file(file_id)
    await verify_person_access(db_file.person_id, current_user, db)
    
    return db_file

# File upload and management
@router.post("/upload/{person_id}", response_model=PersonFileRead, status_code=status.HTTP_201_CREATED)
async def upload_file_for_person(
    person_id: uuid.UUID,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Upload a file for a specific person."""
    # Check access
    await verify_person_access(person_id, current_user, db)
    
    # Upload file
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    return await file_service.upload_person_file(person_id, file, description)

@router.get("/person/{person_id}", response_model=List[PersonFileRead])
async def get_person_files(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    file_type: Optional[str] = Query(None, description="Filter by file type (image, document, video, audio, other)")
):
    """Get all files for a specific person."""
    # Check access
    await verify_person_access(person_id, current_user, db)
    
    # Get files
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    return await file_service.get_person_files(person_id, file_type)

@router.get("/download/{file_id}")
async def download_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Download a specific file."""
    # Verify access and get file
    db_file = await verify_file_access(file_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    try:
        file_content, file_metadata = await file_service.download_person_file(file_id)
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=file_metadata.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_metadata.original_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.get("/view/{file_id}")
async def view_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """View a file inline (for images, PDFs, etc.)."""
    # Verify access and get file
    db_file = await verify_file_access(file_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    try:
        file_content, file_metadata = await file_service.download_person_file(file_id)
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=file_metadata.mime_type,
            headers={
                "Content-Disposition": f"inline; filename={file_metadata.original_filename}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to view file: {str(e)}"
        )

@router.delete("/{file_id}", response_model=MessageResponse)
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Delete a specific file."""
    # Verify access
    await verify_file_access(file_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    await file_service.delete_person_file(file_id)
    return MessageResponse(message="File deleted successfully")

@router.put("/{file_id}/metadata", response_model=PersonFileRead)
async def update_file_metadata(
    file_id: uuid.UUID,
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Update file metadata (currently only description)."""
    # Verify access
    await verify_file_access(file_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    return await file_service.update_file_metadata(file_id, description)

@router.get("/{file_id}", response_model=PersonFileRead)
async def get_file_metadata(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get file metadata without downloading the file."""
    # Verify access and return file metadata
    return await verify_file_access(file_id, current_user, db)

# Family tree file operations
@router.get("/family-tree/{family_tree_id}", response_model=List[PersonFileRead])
async def get_family_tree_files(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    limit: Optional[int] = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip")
):
    """Get all files in a family tree with optional filtering and pagination."""
    # Check access
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    return await file_service.get_family_tree_files(family_tree_id, file_type, limit, offset)

@router.get("/family-tree/{family_tree_id}/statistics")
async def get_family_tree_file_statistics(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get file statistics for a family tree."""
    # Check access
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    return await file_service.get_file_statistics(family_tree_id)

@router.get("/family-tree/{family_tree_id}/search", response_model=List[PersonFileRead])
async def search_family_tree_files(
    family_tree_id: uuid.UUID,
    search_term: str = Query(..., min_length=1, description="Search term for filename or description"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    file_type: Optional[str] = Query(None, description="Filter by file type")
):
    """Search files by filename or description within a family tree."""
    # Check access
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    return await file_service.search_files(family_tree_id, search_term, file_type)

# Bulk file operations
@router.post("/bulk-upload/{person_id}", response_model=List[PersonFileRead])
async def bulk_upload_files(
    person_id: uuid.UUID,
    files: List[UploadFile] = File(...),
    descriptions: Optional[List[str]] = Form(None),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Upload multiple files for a person."""
    # Check access
    await verify_person_access(person_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    uploaded_files = []
    errors = []
    
    # Ensure descriptions list matches files length if provided
    if descriptions and len(descriptions) != len(files):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of descriptions must match number of files"
        )
    
    for i, file in enumerate(files):
        try:
            description = descriptions[i] if descriptions else None
            uploaded_file = await file_service.upload_person_file(person_id, file, description)
            uploaded_files.append(uploaded_file)
        except Exception as e:
            errors.append(f"File {i} ({file.filename}): {str(e)}")
    
    if errors:
        # Return partial success with error information in a custom header
        # In a production system, you might want to use a different approach for error reporting
        error_msg = "; ".join(errors)
        raise HTTPException(
            status_code=status.HTTP_207_MULTI_STATUS,
            detail=f"Uploaded {len(uploaded_files)} files successfully. Errors: {error_msg}"
        )
    
    return uploaded_files

@router.delete("/person/{person_id}/all", response_model=MessageResponse)
async def delete_all_person_files(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    file_type: Optional[str] = Query(None, description="Only delete files of this type")
):
    """Delete all files for a specific person."""
    # Check access
    await verify_person_access(person_id, current_user, db)
    
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    # Get files to delete
    files_to_delete = await file_service.get_person_files(person_id, file_type)
    
    deleted_count = 0
    errors = []
    
    for file_record in files_to_delete:
        try:
            await file_service.delete_person_file(file_record.id)
            deleted_count += 1
        except Exception as e:
            errors.append(f"File {file_record.original_filename}: {str(e)}")
    
    message = f"Deleted {deleted_count} files"
    if errors:
        message += f". Errors: {'; '.join(errors)}"
    
    return MessageResponse(message=message)

# File type endpoints
@router.get("/types")
async def get_supported_file_types():
    """Get list of supported file types and size limits."""
    storage = get_file_storage()
    # Access file service settings - this could be moved to a settings endpoint
    return {
        "max_file_size_bytes": 10 * 1024 * 1024,  # From settings
        "max_file_size_mb": 10,
        "allowed_mime_types": [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'video/mp4', 'video/avi', 'video/mov', 'audio/mpeg', 'audio/wav'
        ],
        "file_type_categories": {
            "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
            "document": ["application/pdf", "text/plain", "application/msword", 
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
            "video": ["video/mp4", "video/avi", "video/mov"],
            "audio": ["audio/mpeg", "audio/wav"]
        }
    }