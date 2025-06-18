# backend/app/api/v1/endpoints/family_trees.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_database_session
from app.core.auth import current_active_user
from app.models.database import User
from app.schemas.schemas import (
    FamilyTreeCreate, 
    FamilyTreeRead, 
    FamilyTreeUpdate,
    FamilyTreeGraph,
    MessageResponse
)
from app.services.family_tree_service import FamilyTreeService

router = APIRouter()

@router.post("/", response_model=FamilyTreeRead, status_code=status.HTTP_201_CREATED)
async def create_family_tree(
    family_tree_data: FamilyTreeCreate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Create a new family tree for the current user."""
    service = FamilyTreeService(db)
    return await service.create_family_tree(current_user.id, family_tree_data)

@router.get("/", response_model=List[FamilyTreeRead])
async def get_user_family_trees(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of results"),
    offset: Optional[int] = Query(None, ge=0, description="Number of results to skip"),
    search: Optional[str] = Query(None, description="Search term for name or description")
):
    """Get all family trees for the current user with optional pagination and search."""
    service = FamilyTreeService(db)
    
    if search:
        return await service.search_family_trees(current_user.id, search)
    else:
        return await service.get_user_family_trees(current_user.id, limit, offset)

@router.get("/count")
async def get_family_tree_count(
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get the total count of family trees for the current user."""
    service = FamilyTreeService(db)
    count = await service.get_family_tree_count(current_user.id)
    return {"count": count}

@router.get("/{family_tree_id}", response_model=FamilyTreeRead)
async def get_family_tree(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get a specific family tree by ID."""
    service = FamilyTreeService(db)
    family_tree = await service.get_family_tree(family_tree_id)
    
    # Check ownership
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    return family_tree

@router.put("/{family_tree_id}", response_model=FamilyTreeRead)
async def update_family_tree(
    family_tree_id: uuid.UUID,
    update_data: FamilyTreeUpdate,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Update a family tree."""
    service = FamilyTreeService(db)
    family_tree = await service.get_family_tree(family_tree_id)
    
    # Check ownership
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this family tree"
        )
    
    return await service.update_family_tree(family_tree_id, update_data)

@router.delete("/{family_tree_id}", response_model=MessageResponse)
async def delete_family_tree(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Delete a family tree and all associated data."""
    service = FamilyTreeService(db)
    family_tree = await service.get_family_tree(family_tree_id)
    
    # Check ownership
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this family tree"
        )
    
    await service.delete_family_tree(family_tree_id)
    return MessageResponse(message="Family tree deleted successfully")

@router.get("/{family_tree_id}/graph", response_model=FamilyTreeGraph)
async def get_family_tree_graph(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get family tree data formatted for graph visualization."""
    service = FamilyTreeService(db)
    family_tree = await service.get_family_tree(family_tree_id)
    
    # Check ownership
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    return await service.get_family_tree_graph(family_tree_id)

@router.get("/{family_tree_id}/statistics")
async def get_family_tree_statistics(
    family_tree_id: uuid.UUID,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(current_active_user)
):
    """Get statistics for a family tree (person count, relationship count, etc.)."""
    service = FamilyTreeService(db)
    family_tree = await service.get_family_tree(family_tree_id)
    
    # Check ownership
    if family_tree.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family tree"
        )
    
    return await service.get_family_tree_statistics(family_tree_id)