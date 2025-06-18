# backend/app/api/v1/endpoints/relationships.py

from typing import List, Dict, Any
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
    RelationshipDisplay,
    RelationshipSummary,
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

# CRUD Operations
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

# Person-specific relationship queries
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

@router.get("/person/{person_id}/display", response_model=List[RelationshipDisplay])
async def get_person_relationships_display(
    person_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get relationships for a person with display-friendly formatting"""
    # Check if user owns the person's family tree
    await check_person_ownership(person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return relationship_service.get_person_relationships_display(person_id)

@router.get("/person/{person_id}/family-line", response_model=Dict[str, List])
async def get_person_family_line(
    person_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get family line relationships (parents and children) for a person"""
    # Check if user owns the person's family tree
    await check_person_ownership(person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return relationship_service.get_family_line_relationships(person_id)

@router.get("/person/{person_id}/partners")
async def get_person_partners(
    person_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get all partners/spouses for a person"""
    # Check if user owns the person's family tree
    await check_person_ownership(person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return relationship_service.get_partners(person_id)

@router.get("/person/{person_id}/siblings")
async def get_person_siblings(
    person_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get all siblings for a person"""
    # Check if user owns the person's family tree
    await check_person_ownership(person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    return relationship_service.get_siblings(person_id)

# Family tree relationship queries
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

@router.get("/family-tree/{family_tree_id}/statistics", response_model=Dict[str, Any])
async def get_family_tree_relationship_statistics(
    family_tree_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get relationship statistics for a family tree"""
    # Check if user owns the family tree
    family_tree_service = FamilyTreeService(db)
    family_tree = family_tree_service.get_family_tree(family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    relationship_service = RelationshipService(db)
    return relationship_service.get_family_statistics(family_tree_id)

# Advanced relationship features
@router.get("/path/{person1_id}/{person2_id}")
async def get_relationship_path(
    person1_id: uuid.UUID,
    person2_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Find the relationship path between two people"""
    # Check if user owns both people's family trees
    await check_person_ownership(person1_id, current_user, db)
    await check_person_ownership(person2_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    path = relationship_service.get_relationship_path(person1_id, person2_id)
    
    if path:
        return {"path": path, "relationship_found": True}
    else:
        return {"path": [], "relationship_found": False}

@router.get("/family-tree/{family_tree_id}/infer")
async def infer_relationships(
    family_tree_id: uuid.UUID,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get inferred relationship suggestions for a family tree"""
    # Check if user owns the family tree
    family_tree_service = FamilyTreeService(db)
    family_tree = family_tree_service.get_family_tree(family_tree_id)
    
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    relationship_service = RelationshipService(db)
    return relationship_service.infer_relationships(family_tree_id)

# Utility endpoints
@router.get("/categories")
async def get_relationship_categories():
    """Get available relationship categories and their valid subtypes"""
    return {
        "categories": {
            "family_line": {
                "description": "Parent-child relationships",
                "requires_generation_difference": True,
                "valid_subtypes": ["biological", "adoptive", "step", "foster"],
                "generation_values": {
                    "-1": "from_person is parent of to_person",
                    "1": "from_person is child of to_person"
                }
            },
            "partner": {
                "description": "Romantic partnerships and marriages",
                "requires_generation_difference": False,
                "valid_subtypes": ["married", "engaged", "dating", "divorced", "separated", "widowed"],
                "bidirectional": True
            },
            "sibling": {
                "description": "Sibling relationships",
                "requires_generation_difference": False,
                "valid_subtypes": ["biological", "half", "step", "adoptive"],
                "bidirectional": True
            },
            "extended_family": {
                "description": "Extended family relationships",
                "requires_generation_difference": False,
                "valid_subtypes": ["aunt", "uncle", "cousin", "grandparent", "grandchild", "in_law"],
                "bidirectional": False  # Direction matters for some extended family
            }
        }
    }

@router.post("/validate")
async def validate_relationship(
    relationship_data: RelationshipCreate,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Validate a relationship without creating it"""
    # Check if user owns both people's family trees
    await check_person_ownership(relationship_data.from_person_id, current_user, db)
    await check_person_ownership(relationship_data.to_person_id, current_user, db)
    
    relationship_service = RelationshipService(db)
    
    try:
        # We'll create a temporary validation - this will run all validation logic
        # but we won't commit to the database
        relationship_service._validate_relationship_people(
            relationship_data.from_person_id, 
            relationship_data.to_person_id
        )
        relationship_service._check_duplicate_relationship(
            relationship_data.from_person_id, 
            relationship_data.to_person_id,
            relationship_data.relationship_category
        )
        relationship_service._validate_relationship_rules(relationship_data)
        
        return {"valid": True, "message": "Relationship is valid"}
    
    except HTTPException as e:
        return {"valid": False, "message": e.detail}