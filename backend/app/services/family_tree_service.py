from typing import List
from sqlalchemy.orm import Session
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
    def __init__(self, db: Session):
        self.db = db

    def create_family_tree(self, owner_id: uuid.UUID, family_tree_data: FamilyTreeCreate) -> FamilyTree:
        """Create a new family tree"""
        db_family_tree = FamilyTree(
            owner_id=owner_id,
            **family_tree_data.dict()
        )
        
        self.db.add(db_family_tree)
        self.db.commit()
        self.db.refresh(db_family_tree)
        
        return db_family_tree

    def get_family_tree(self, family_tree_id: uuid.UUID) -> FamilyTree:
        """Get a family tree by ID"""
        family_tree = self.db.query(FamilyTree).filter(
            FamilyTree.id == family_tree_id
        ).first()
        
        if not family_tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family tree not found"
            )
        
        return family_tree

    def get_user_family_trees(self, owner_id: uuid.UUID) -> List[FamilyTree]:
        """Get all family trees for a user"""
        return self.db.query(FamilyTree).filter(
            FamilyTree.owner_id == owner_id
        ).order_by(FamilyTree.created_at.desc()).all()

    def update_family_tree(self, family_tree_id: uuid.UUID, update_data: FamilyTreeUpdate) -> FamilyTree:
        """Update a family tree"""
        family_tree = self.get_family_tree(family_tree_id)
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(family_tree, field, value)
        
        self.db.commit()
        self.db.refresh(family_tree)
        
        return family_tree

    def delete_family_tree(self, family_tree_id: uuid.UUID) -> None:
        """Delete a family tree and all associated data"""
        family_tree = self.get_family_tree(family_tree_id)
        
        self.db.delete(family_tree)
        self.db.commit()

    def get_family_tree_graph(self, family_tree_id: uuid.UUID) -> FamilyTreeGraph:
        """Get family tree data formatted for graph visualization"""
        # Get all people in the family tree
        people = self.db.query(Person).filter(
            Person.family_tree_id == family_tree_id
        ).all()
        
        # Get all relationships in the family tree
        person_ids = [person.id for person in people]
        relationships = self.db.query(Relationship).filter(
            Relationship.from_person_id.in_(person_ids),
            Relationship.to_person_id.in_(person_ids)
        ).all()
        
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