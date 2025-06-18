# backend/app/api/v1/endpoints/relationships.py

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_database_session
from app.core.auth import current_active_user
from app.models.database import User
from app.schemas.schemas import (
    RelationshipCreate, 
    RelationshipRead, 
    RelationshipUpdate,
    RelationshipDisplay,
    RelationshipStatistics,
    RelationshipPath,
    RelationshipValidation,
    InferredRelationship,
    MessageResponse
)
from app.services.relationship_service import RelationshipService
from app.services.person_service import PersonService
from app.services.family_tree_service import FamilyTreeService

router = APIRouter()

async def verify_person_access(person_id: uuid.UUID, current_user: User, db: AsyncSession):
    """Helper function to verify user owns the person's family tree."""
    person_service = PersonService(db)
    person = await person_service.get_person(person_id)
    
    family_tree_service = FamilyTreeService(db)
    family_tree = await family_tree_service.get_family_tree(person.family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    return person

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

# CRUD Operations
@router.post("/", response_model=RelationshipRead, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    relationship_data: RelationshipCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new relationship between two people."""
    # Check if user owns both people's family trees
    await verify_person_access(relationship_data.from_person_id, current_user, db)
    await verify_person_access(relationship_data.to_person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return await relationship_service.create_relationship(relationship_data)

@router.get("/{relationship_id}", response_model=RelationshipRead)
async def get_relationship(
    relationship_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get a specific relationship by ID."""
    relationship_service = RelationshipService(db)
    relationship = await relationship_service.get_relationship(relationship_id)
    
    # Verify access through either person in the relationship
    try:
        await verify_person_access(relationship.from_person_id, current_user, db)
    except HTTPException:
        await verify_person_access(relationship.to_person_id, current_user, db)
    
    return relationship

@router.put("/{relationship_id}", response_model=RelationshipRead)
async def update_relationship(
    relationship_id: uuid.UUID,
    update_data: RelationshipUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Update a relationship."""
    relationship_service = RelationshipService(db)
    relationship = await relationship_service.get_relationship(relationship_id)
    
    # Verify access through either person in the relationship
    try:
        await verify_person_access(relationship.from_person_id, current_user, db)
    except HTTPException:
        await verify_person_access(relationship.to_person_id, current_user, db)
    
    return await relationship_service.update_relationship(relationship_id, update_data)

@router.delete("/{relationship_id}", response_model=MessageResponse)
async def delete_relationship(
    relationship_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Delete a relationship and its reciprocal if it exists."""
    relationship_service = RelationshipService(db)
    relationship = await relationship_service.get_relationship(relationship_id)
    
    # Verify access through either person in the relationship
    try:
        await verify_person_access(relationship.from_person_id, current_user, db)
    except HTTPException:
        await verify_person_access(relationship.to_person_id, current_user, db)
    
    await relationship_service.delete_relationship(relationship_id)
    return MessageResponse(message="Relationship deleted successfully")

# Person-specific relationship endpoints
@router.get("/person/{person_id}", response_model=List[RelationshipRead])
async def get_person_relationships(
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    category: Optional[str] = Query(None, description="Filter by relationship category")
):
    """Get all relationships for a specific person."""
    # Verify access
    await verify_person_access(person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return await relationship_service.get_person_relationships(person_id, category)

# Family tree relationship endpoints
@router.get("/family-tree/{family_tree_id}", response_model=List[RelationshipRead])
async def get_family_tree_relationships(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get all relationships in a family tree."""
    # Verify access
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return await relationship_service.get_family_tree_relationships(family_tree_id)

@router.get("/family-tree/{family_tree_id}/statistics", response_model=RelationshipStatistics)
async def get_relationship_statistics(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get statistics about relationships in a family tree."""
    # Verify access
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return await relationship_service.get_relationship_statistics(family_tree_id)

# Advanced relationship analysis
@router.get("/path/{person1_id}/{person2_id}", response_model=RelationshipPath)
async def find_relationship_path(
    person1_id: uuid.UUID,
    person2_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum search depth")
):
    """Find the relationship path between two people."""
    # Verify access to both people
    await verify_person_access(person1_id, current_user, db)
    await verify_person_access(person2_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return await relationship_service.find_relationship_path(person1_id, person2_id, max_depth)

@router.get("/family-tree/{family_tree_id}/infer", response_model=List[InferredRelationship])
async def infer_missing_relationships(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Infer missing relationships based on existing ones."""
    # Verify access
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return await relationship_service.infer_missing_relationships(family_tree_id)

@router.post("/validate", response_model=RelationshipValidation)
async def validate_relationship(
    relationship_data: RelationshipCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Validate a relationship without creating it."""
    # Check if user owns both people's family trees
    await verify_person_access(relationship_data.from_person_id, current_user, db)
    await verify_person_access(relationship_data.to_person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return await relationship_service.validate_relationship(relationship_data)

# Bulk operations
@router.post("/bulk", response_model=List[RelationshipRead])
async def create_multiple_relationships(
    relationships_data: List[RelationshipCreate],
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    continue_on_error: bool = Query(False, description="Continue creating relationships if one fails")
):
    """Create multiple relationships in a single operation."""
    relationship_service = RelationshipService(db)
    created_relationships = []
    errors = []
    
    for i, relationship_data in enumerate(relationships_data):
        try:
            # Verify access for each relationship
            await verify_person_access(relationship_data.from_person_id, current_user, db)
            await verify_person_access(relationship_data.to_person_id, current_user, db)
            
            # Create the relationship
            relationship = await relationship_service.create_relationship(relationship_data)
            created_relationships.append(relationship)
            
        except Exception as e:
            error_msg = f"Relationship {i}: {str(e)}"
            errors.append(error_msg)
            
            if not continue_on_error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create relationships. {error_msg}. Created {len(created_relationships)} relationships before failure."
                )
    
    if errors and continue_on_error:
        # Return created relationships with warning about errors
        # Note: In a real implementation, you might want to return this information in headers or a different response format
        pass
    
    return created_relationships

@router.delete("/family-tree/{family_tree_id}/category/{category}", response_model=MessageResponse)
async def delete_relationships_by_category(
    family_tree_id: uuid.UUID,
    category: str,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Delete all relationships of a specific category in a family tree."""
    # Verify access
    await verify_family_tree_access(family_tree_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    relationships = await relationship_service.get_family_tree_relationships(family_tree_id)
    
    deleted_count = 0
    for relationship in relationships:
        if relationship.relationship_category == category:
            await relationship_service.delete_relationship(relationship.id)
            deleted_count += 1
    
    return MessageResponse(message=f"Deleted {deleted_count} relationships of category '{category}'")