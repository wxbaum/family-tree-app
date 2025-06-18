from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_family_tree(self, owner_id: uuid.UUID, family_tree_data: FamilyTreeCreate) -> FamilyTree:
        """Create a new family tree"""
        db_family_tree = FamilyTree(
            owner_id=owner_id,
            **family_tree_data.dict()
        )
        
        self.db.add(db_family_tree)
        await self.db.commit()
        await self.db.refresh(db_family_tree)
        
        return db_family_tree

    async def get_family_tree(self, family_tree_id: uuid.UUID) -> FamilyTree:
        """Get a family tree by ID"""
        stmt = select(FamilyTree).where(FamilyTree.id == family_tree_id)
        result = await self.db.execute(stmt)
        family_tree = result.scalar_one_or_none()
        
        if not family_tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family tree not found"
            )
        
        return family_tree

    async def get_user_family_trees(self, owner_id: uuid.UUID) -> List[FamilyTree]:
        """Get all family trees for a user"""
        stmt = select(FamilyTree).where(
            FamilyTree.owner_id == owner_id
        ).order_by(FamilyTree.created_at.desc())
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_family_tree(self, family_tree_id: uuid.UUID, update_data: FamilyTreeUpdate) -> FamilyTree:
        """Update a family tree"""
        family_tree = await self.get_family_tree(family_tree_id)
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(family_tree, field, value)
        
        await self.db.commit()
        await self.db.refresh(family_tree)
        
        return family_tree

    async def delete_family_tree(self, family_tree_id: uuid.UUID) -> None:
        """Delete a family tree and all associated data"""
        family_tree = await self.get_family_tree(family_tree_id)
        
        await self.db.delete(family_tree)
        await self.db.commit()

    async def get_family_tree_graph(self, family_tree_id: uuid.UUID) -> FamilyTreeGraph:
        """Get family tree data formatted for graph visualization"""
        # Get all people in the family tree
        people_stmt = select(Person).where(Person.family_tree_id == family_tree_id)
        people_result = await self.db.execute(people_stmt)
        people = people_result.scalars().all()
        
        # Get all relationships in the family tree
        person_ids = [person.id for person in people]
        
        if not person_ids:
            return FamilyTreeGraph(nodes=[], edges=[])
        
        relationships_stmt = select(Relationship).where(
            Relationship.from_person_id.in_(person_ids),
            Relationship.to_person_id.in_(person_ids)
        )
        relationships_result = await self.db.execute(relationships_stmt)
        relationships = relationships_result.scalars().all()
        
        # Create graph nodes
        nodes = []
        for person in people:
            person_read = PersonRead.from_orm(person)
            node = GraphNode(
                id=str(person.id),
                type="person",
                data=person_read
            )
            nodes.append(node)
        
        # Create graph edges
        edges = []
        for relationship in relationships:
            relationship_read = RelationshipRead.from_orm(relationship)
            edge = GraphEdge(
                id=str(relationship.id),
                source=str(relationship.from_person_id),
                target=str(relationship.to_person_id),
                type=relationship.relationship_type,
                data=relationship_read
            )
            edges.append(edge)
        
        return FamilyTreeGraph(nodes=nodes, edges=edges)