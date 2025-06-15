from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
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

async def check_person_access(person_id: uuid.UUID, current_user: User, db: Session):
    """Helper to verify user can access the person"""
    person_service = PersonService(db)
    person = person_service.get_person(person_id)
    
    family_tree_service = FamilyTreeService(db)
    family_tree = family_tree_service.get_family_tree(person.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this person's files"
        )
    
    return person

@router.post("/upload/{person_id}", response_model=PersonFileRead, status_code=status.HTTP_201_CREATED)
async def upload_file_for_person(
    person_id: uuid.UUID,
    file: UploadFile = File(...),
    description: str = Form(None),
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Upload a file for a specific person"""
    # Check access
    await check_person_access(person_id, current_user, db)
    
    # Upload file
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    try:
        uploaded_file = await file_service.upload_person_file(person_id, file, description)
        return uploaded_file
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/person/{person_id}", response_model=List[PersonFileRead])
async def get_person_files(
    person_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get all files for a specific person"""
    # Check access
    await check_person_access(person_id, current_user, db)
    
    # Get files
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    return file_service.get_person_files(person_id)

@router.get("/download/{file_id}")
async def download_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Download a specific file"""
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    try:
        # Get file info first to check access
        from app.models.database import PersonFile
        db_file = db.query(PersonFile).filter(PersonFile.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
        
        # Check access
        await check_person_access(db_file.person_id, current_user, db)
        
        # Get file content
        content, filename, mime_type = await file_service.get_file_content(file_id)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(content),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.delete("/{file_id}", response_model=MessageResponse)
async def delete_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Delete a specific file"""
    # Get file info first to check access
    from app.models.database import PersonFile
    db_file = db.query(PersonFile).filter(PersonFile.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    
    # Check access
    await check_person_access(db_file.person_id, current_user, db)
    
    # Delete file
    storage = get_file_storage()
    file_service = FileService(db, storage)
    
    success = await file_service.delete_person_file(file_id)
    if success:
        return MessageResponse(message="File deleted successfully")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")