from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_database_session
from app.core.auth import current_active_user
from app.models.database import User
from app.schemas.schemas import (
    PersonCreate, 
    PersonRead, 
    PersonUpdate,
    MessageResponse
)
from app.services.person_service import PersonService
from app.services.family_tree_service import FamilyTreeService

router = APIRouter()

@router.post("/", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_data: PersonCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new person in a family tree"""
    # Check if user owns the family tree
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(person_data.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add people to this family tree"
        )
    
    person_service = PersonService(db)
    return await person_service.create_person(person_data)

@router.get("/{person_id}", response_model=PersonRead)
async def get_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get a specific person"""
    person_service = PersonService(db)
    person = await person_service.get_person(person_id)
    
    # Check if user owns the family tree
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(person.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this person"
        )
    
    return person

@router.put("/{person_id}", response_model=PersonRead)
async def update_person(
    person_id: uuid.UUID,
    update_data: PersonUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Update a person"""
    person_service = PersonService(db)
    person = await person_service.get_person(person_id)
    
    # Check if user owns the family tree
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(person.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this person"
        )
    
    return await person_service.update_person(person_id, update_data)

@router.delete("/{person_id}", response_model=MessageResponse)
async def delete_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Delete a person"""
    person_service = PersonService(db)
    person = await person_service.get_person(person_id)
    
    # Check if user owns the family tree
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(person.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this person"
        )
    
    await person_service.delete_person(person_id)
    return MessageResponse(message="Person deleted successfully")

@router.get("/family-tree/{family_tree_id}", response_model=List[PersonRead])
async def get_people_in_family_tree(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get all people in a specific family tree"""
    # Check if user owns the family tree
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    person_service = PersonService(db)
    return await person_service.get_people_by_family_tree(family_tree_id)