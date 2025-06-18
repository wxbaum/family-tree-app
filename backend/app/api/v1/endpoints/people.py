# backend/app/api/v1/endpoints/people.py

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import date

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

async def verify_family_tree_access(family_tree_id: uuid.UUID, current_user: User, db: AsyncSession):
    """Helper function to verify user owns the family tree."""
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    return family_tree

async def verify_person_access(person_id: uuid.UUID, current_user: User, db: AsyncSession):
    """Helper function to verify user owns the person's family tree."""
    person_service = PersonService(db)
    person = await person_service.get_person(person_id)
    
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(person.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this person"
        )
    
    return person

@router.post("/", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
async def create_person(
    person_data: PersonCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new person in a family tree."""
    # Check if user owns the family tree
    await verify_family_tree_access(person_data.family_tree_id, current_user, db)
    
    person_service = PersonService(db)
    return await person_service.create_person(person_data)

@router.get("/{person_id}", response_model=PersonRead)
async def get_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get a specific person by ID."""
    # Check access and return person
    return await verify_person_access(person_id, current_user, db)

@router.put("/{person_id}", response_model=PersonRead)
async def update_person(
    person_id: uuid.UUID,
    update_data: PersonUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Update a person with new data."""
    # Verify access
    await verify_person_access(person_id, current_user, db)
    
    person_service = PersonService(db)
    return await person_service.update_person(person_id, update_data)

@router.delete("/{person_id}", response_model=MessageResponse)
async def delete_person(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Delete a person and all associated relationships."""
    # Verify access
    await verify_person_access(person_id, current_user, db)
    
    person_service = PersonService(db)
    await person_service.delete_person(person_id)
    return MessageResponse(message="Person deleted successfully")

@router.get("/family-tree/{family_tree_id}", response_model=List[PersonRead])
async def get_people_in_family_tree(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Maximum number of results"),
    offset: Optional[int] = Query(None, ge=0, description="Number of results to skip")
):
    """Get all people in a specific family tree with optional pagination."""
    # Check if user owns the family tree
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    person_service = PersonService(db)
    return await person_service.get_people_by_family_tree(family_tree_id, limit, offset)

@router.get("/family-tree/{family_tree_id}/count")
async def get_people_count(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get the total count of people in a family tree."""
    # Check if user owns the family tree
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    person_service = PersonService(db)
    count = await person_service.get_people_count(family_tree_id)
    return {"count": count}

@router.get("/family-tree/{family_tree_id}/search", response_model=List[PersonRead])
async def search_people(
    family_tree_id: uuid.UUID,
    search_term: str = Query(..., min_length=1, description="Search term for names"),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """Search for people by name within a family tree."""
    # Check if user owns the family tree
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    person_service = PersonService(db)
    return await person_service.search_people(family_tree_id, search_term, limit)

@router.get("/{person_id}/relationships")
async def get_person_relationships(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get all relationships for a person, organized by type."""
    # Verify access
    await verify_person_access(person_id, current_user, db)
    
    person_service = PersonService(db)
    return await person_service.get_person_relationships(person_id)

@router.get("/{person_id}/ancestors", response_model=List[PersonRead])
async def get_person_ancestors(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    generations: Optional[int] = Query(None, ge=1, le=10, description="Number of generations to go back")
):
    """Get ancestors of a person (parents, grandparents, etc.)."""
    # Verify access
    await verify_person_access(person_id, current_user, db)
    
    person_service = PersonService(db)
    return await person_service.get_person_ancestors(person_id, generations)

@router.get("/{person_id}/descendants", response_model=List[PersonRead])
async def get_person_descendants(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    generations: Optional[int] = Query(None, ge=1, le=10, description="Number of generations to go forward")
):
    """Get descendants of a person (children, grandchildren, etc.)."""
    # Verify access
    await verify_person_access(person_id, current_user, db)
    
    person_service = PersonService(db)
    return await person_service.get_person_descendants(person_id, generations)

@router.get("/{person_id}/siblings", response_model=List[PersonRead])
async def get_person_siblings(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get siblings of a person."""
    # Verify access
    await verify_person_access(person_id, current_user, db)
    
    person_service = PersonService(db)
    return await person_service.get_person_siblings(person_id)

@router.get("/{person_id}/age")
async def get_person_age(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    as_of_date: Optional[date] = Query(None, description="Date to calculate age as of (defaults to today)")
):
    """Calculate a person's age as of a specific date."""
    # Verify access
    await verify_person_access(person_id, current_user, db)
    
    person_service = PersonService(db)
    age = await person_service.calculate_person_age(person_id, as_of_date)
    
    return {
        "person_id": str(person_id),
        "age": age,
        "as_of_date": as_of_date or date.today(),
        "has_birth_date": age is not None
    }