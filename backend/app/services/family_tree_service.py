# backend/app/services/family_tree_service.py

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
import uuid

from app.models.database import FamilyTree, Person, Relationship
from app.schemas.schemas import (
    FamilyTreeCreate, 
    FamilyTreeUpdate, 
    FamilyTreeGraph,
    GraphNode,
    GraphEdge,
    PersonRead,
    RelationshipRead
)

class FamilyTreeService:
    """
    Async service for managing family trees with comprehensive CRUD operations.
    Handles family tree creation, updates, deletion, and graph data export.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_family_tree(self, owner_id: uuid.UUID, family_tree_data: FamilyTreeCreate) -> FamilyTree:
        """
        Create a new family tree for the specified owner.
        
        Args:
            owner_id: UUID of the user creating the family tree
            family_tree_data: Family tree creation data
            
        Returns:
            Created FamilyTree instance
            
        Raises:
            HTTPException: If creation fails
        """
        try:
            db_family_tree = FamilyTree(
                owner_id=owner_id,
                **family_tree_data.dict()
            )
            
            self.db.add(db_family_tree)
            await self.db.commit()
            await self.db.refresh(db_family_tree)
            
            return db_family_tree
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create family tree: {str(e)}"
            )

    async def get_family_tree(self, family_tree_id: uuid.UUID) -> FamilyTree:
        """
        Get a family tree by ID.
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            FamilyTree instance
            
        Raises:
            HTTPException: If family tree not found
        """
        stmt = select(FamilyTree).where(FamilyTree.id == family_tree_id)
        result = await self.db.execute(stmt)
        family_tree = result.scalar_one_or_none()
        
        if not family_tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family tree not found"
            )
        
        return family_tree

    async def get_user_family_trees(self, owner_id: uuid.UUID, limit: Optional[int] = None, offset: Optional[int] = None) -> List[FamilyTree]:
        """
        Get all family trees for a user with optional pagination.
        
        Args:
            owner_id: UUID of the user
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of FamilyTree instances
        """
        stmt = select(FamilyTree).where(
            FamilyTree.owner_id == owner_id
        ).order_by(FamilyTree.created_at.desc())
        
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_family_tree_count(self, owner_id: uuid.UUID) -> int:
        """
        Get the total count of family trees for a user.
        
        Args:
            owner_id: UUID of the user
            
        Returns:
            Total count of family trees
        """
        stmt = select(func.count(FamilyTree.id)).where(FamilyTree.owner_id == owner_id)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def update_family_tree(self, family_tree_id: uuid.UUID, update_data: FamilyTreeUpdate) -> FamilyTree:
        """
        Update a family tree with new data.
        
        Args:
            family_tree_id: UUID of the family tree
            update_data: Update data with only changed fields
            
        Returns:
            Updated FamilyTree instance
            
        Raises:
            HTTPException: If family tree not found or update fails
        """
        try:
            family_tree = await self.get_family_tree(family_tree_id)
            
            # Update only provided fields
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(family_tree, field, value)
            
            await self.db.commit()
            await self.db.refresh(family_tree)
            
            return family_tree
            
        except HTTPException:
            raise  # Re-raise HTTPExceptions from get_family_tree
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update family tree: {str(e)}"
            )

    async def delete_family_tree(self, family_tree_id: uuid.UUID) -> None:
        """
        Delete a family tree and all associated data (people, relationships, files).
        This is a cascading delete operation.
        
        Args:
            family_tree_id: UUID of the family tree to delete
            
        Raises:
            HTTPException: If family tree not found or deletion fails
        """
        try:
            family_tree = await self.get_family_tree(family_tree_id)
            
            # Cascading delete is handled by database relationships
            await self.db.delete(family_tree)
            await self.db.commit()
            
        except HTTPException:
            raise  # Re-raise HTTPExceptions from get_family_tree
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete family tree: {str(e)}"
            )

    async def get_family_tree_statistics(self, family_tree_id: uuid.UUID) -> dict:
        """
        Get statistics for a family tree (person count, relationship count, etc.).
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Verify family tree exists
            await self.get_family_tree(family_tree_id)
            
            # Count people
            people_stmt = select(func.count(Person.id)).where(Person.family_tree_id == family_tree_id)
            people_result = await self.db.execute(people_stmt)
            people_count = people_result.scalar() or 0
            
            # Count relationships - need to join through people to get family tree relationships
            relationships_stmt = select(func.count(Relationship.id)).join(
                Person, Relationship.from_person_id == Person.id
            ).where(Person.family_tree_id == family_tree_id)
            relationships_result = await self.db.execute(relationships_stmt)
            relationships_count = relationships_result.scalar() or 0
            
            return {
                "people_count": people_count,
                "relationships_count": relationships_count,
                "generation_span": await self._calculate_generation_span(family_tree_id),
                "largest_generation": await self._calculate_largest_generation(family_tree_id)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get family tree statistics: {str(e)}"
            )

    async def get_family_tree_graph(self, family_tree_id: uuid.UUID) -> FamilyTreeGraph:
        """
        Get family tree data formatted for graph visualization with React Flow.
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            FamilyTreeGraph with nodes and edges for visualization
            
        Raises:
            HTTPException: If family tree not found or graph generation fails
        """
        try:
            # Verify family tree exists
            await self.get_family_tree(family_tree_id)
            
            # Get all people in the family tree
            people_stmt = select(Person).where(Person.family_tree_id == family_tree_id)
            people_result = await self.db.execute(people_stmt)
            people = people_result.scalars().all()
            
            # Get all relationships for this family tree
            relationships_stmt = select(Relationship).join(
                Person, Relationship.from_person_id == Person.id
            ).where(Person.family_tree_id == family_tree_id)
            relationships_result = await self.db.execute(relationships_stmt)
            relationships = relationships_result.scalars().all()
            
            # Convert to graph format
            nodes = []
            for person in people:
                nodes.append(GraphNode(
                    id=str(person.id),
                    type="person",
                    data={
                        "id": str(person.id),
                        "first_name": person.first_name,
                        "last_name": person.last_name or "",
                        "birth_date": person.birth_date.isoformat() if person.birth_date else None,
                        "death_date": person.death_date.isoformat() if person.death_date else None,
                        "birth_place": person.birth_place,
                        "death_place": person.death_place,
                        "profile_photo_url": person.profile_photo_url
                    },
                    position={"x": 0, "y": 0}  # Frontend will handle positioning
                ))
            
            edges = []
            for relationship in relationships:
                edges.append(GraphEdge(
                    id=str(relationship.id),
                    source=str(relationship.from_person_id),
                    target=str(relationship.to_person_id),
                    type="relationship",
                    data={
                        "relationship_category": relationship.relationship_category,
                        "relationship_subtype": relationship.relationship_subtype,
                        "generation_difference": relationship.generation_difference,
                        "is_active": relationship.is_active,
                        "start_date": relationship.start_date.isoformat() if relationship.start_date else None,
                        "end_date": relationship.end_date.isoformat() if relationship.end_date else None
                    }
                ))
            
            return FamilyTreeGraph(
                family_tree_id=str(family_tree_id),
                nodes=nodes,
                edges=edges
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate family tree graph: {str(e)}"
            )

    async def search_family_trees(self, owner_id: uuid.UUID, search_term: str) -> List[FamilyTree]:
        """
        Search family trees by name or description.
        
        Args:
            owner_id: UUID of the user
            search_term: Search term to match against name or description
            
        Returns:
            List of matching FamilyTree instances
        """
        try:
            stmt = select(FamilyTree).where(
                and_(
                    FamilyTree.owner_id == owner_id,
                    (
                        FamilyTree.name.ilike(f"%{search_term}%") |
                        FamilyTree.description.ilike(f"%{search_term}%")
                    )
                )
            ).order_by(FamilyTree.name)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search family trees: {str(e)}"
            )

    async def _calculate_generation_span(self, family_tree_id: uuid.UUID) -> int:
        """
        Calculate the generation span (difference between oldest and youngest generations).
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            Generation span as integer
        """
        try:
            # This is a simplified calculation - in a real implementation you'd
            # need to traverse the relationship graph to determine generations
            stmt = select(
                func.max(Relationship.generation_difference),
                func.min(Relationship.generation_difference)
            ).join(Person, Relationship.from_person_id == Person.id).where(
                Person.family_tree_id == family_tree_id
            )
            
            result = await self.db.execute(stmt)
            row = result.first()
            
            if row and row[0] is not None and row[1] is not None:
                return abs(row[0] - row[1])
            return 0
            
        except Exception:
            return 0

    async def _calculate_largest_generation(self, family_tree_id: uuid.UUID) -> int:
        """
        Calculate the size of the largest generation.
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            Size of largest generation
        """
        try:
            # This is a simplified calculation - would need proper generation tracking
            people_stmt = select(func.count(Person.id)).where(Person.family_tree_id == family_tree_id)
            result = await self.db.execute(people_stmt)
            return result.scalar() or 0
            
        except Exception:
            return 0