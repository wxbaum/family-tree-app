from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_database_session
from app.core.auth import current_active_user
from app.models.database import User
from app.schemas.schemas import (
    RelationshipCreate, 
    RelationshipRead, 
    RelationshipUpdate,
    MessageResponse
)
from app.services.relationship_service import RelationshipService
from app.services.person_service import PersonService
from app.services.family_tree_service import FamilyTreeService

router = APIRouter()

async def check_person_ownership(person_id: uuid.UUID, current_user: User, db: Session):
    """Helper function to check if user owns the family tree containing the person"""
    person_service = PersonService(db)
    person = person_service.get_person(person_id)
    
    family_tree_service = FamilyTreeService(db)
    family_tree = family_tree_service.get_family_tree(person.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    return person

@router.post("/", response_model=RelationshipRead, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    relationship_data: RelationshipCreate,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new relationship between two people"""
    # Check if user owns both people's family trees
    await check_person_ownership(relationship_data.from_person_id, current_user, db)
    await check_person_ownership(relationship_data.to_person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return relationship_service.create_relationship(relationship_data)

@router.get("/{relationship_id}", response_model=RelationshipRead)
async def get_relationship(
    relationship_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get a specific relationship"""
    relationship_service = RelationshipService(db)
    relationship = relationship_service.get_relationship(relationship_id)
    
    # Check if user owns both people's family trees
    await check_person_ownership(relationship.from_person_id, current_user, db)
    await check_person_ownership(relationship.to_person_id, current_user, db)
    
    return relationship

@router.put("/{relationship_id}", response_model=RelationshipRead)
async def update_relationship(
    relationship_id: uuid.UUID,
    update_data: RelationshipUpdate,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Update a relationship"""
    relationship_service = RelationshipService(db)
    relationship = relationship_service.get_relationship(relationship_id)
    
    # Check if user owns both people's family trees
    await check_person_ownership(relationship.from_person_id, current_user, db)
    await check_person_ownership(relationship.to_person_id, current_user, db)
    
    return relationship_service.update_relationship(relationship_id, update_data)

@router.delete("/{relationship_id}", response_model=MessageResponse)
async def delete_relationship(
    relationship_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Delete a relationship"""
    relationship_service = RelationshipService(db)
    relationship = relationship_service.get_relationship(relationship_id)
    
    # Check if user owns both people's family trees
    await check_person_ownership(relationship.from_person_id, current_user, db)
    await check_person_ownership(relationship.to_person_id, current_user, db)
    
    relationship_service.delete_relationship(relationship_id)
    return MessageResponse(message="Relationship deleted successfully")

@router.get("/person/{person_id}", response_model=List[RelationshipRead])
async def get_person_relationships(
    person_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get all relationships for a specific person"""
    # Check if user owns the person's family tree
    await check_person_ownership(person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return relationship_service.get_person_relationships(person_id)

@router.get("/family-tree/{family_tree_id}", response_model=List[RelationshipRead])
async def get_family_tree_relationships(
    family_tree_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get all relationships in a specific family tree"""
    # Check if user owns the family tree
    family_tree_service = FamilyTreeService(db)
    family_tree = family_tree_service.get_family_tree(family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    relationship_service = RelationshipService(db)
    return relationship_service.get_family_tree_relationships(family_tree_id)