from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
import uuid

from app.models.database import Relationship, Person
from app.schemas.schemas import RelationshipCreate, RelationshipUpdate

class RelationshipService:
    def __init__(self, db: Session):
        self.db = db

    def create_relationship(self, relationship_data: RelationshipCreate) -> Relationship:
        """Create a new relationship between two people"""
        # Validate that both people exist
        from_person = self.db.query(Person).filter(
            Person.id == relationship_data.from_person_id
        ).first()
        to_person = self.db.query(Person).filter(
            Person.id == relationship_data.to_person_id
        ).first()
        
        if not from_person or not to_person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both people not found"
            )
        
        # Validate that both people are in the same family tree
        if from_person.family_tree_id != to_person.family_tree_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both people must be in the same family tree"
            )
        
        # Check for duplicate relationships
        existing = self.db.query(Relationship).filter(
            Relationship.from_person_id == relationship_data.from_person_id,
            Relationship.to_person_id == relationship_data.to_person_id,
            Relationship.relationship_type == relationship_data.relationship_type,
            Relationship.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This relationship already exists"
            )
        
        db_relationship = Relationship(**relationship_data.dict())
        
        self.db.add(db_relationship)
        self.db.commit()
        self.db.refresh(db_relationship)
        
        return db_relationship

    def get_relationship(self, relationship_id: uuid.UUID) -> Relationship:
        """Get a relationship by ID"""
        relationship = self.db.query(Relationship).filter(
            Relationship.id == relationship_id
        ).first()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship not found"
            )
        
        return relationship

    def get_person_relationships(self, person_id: uuid.UUID) -> List[Relationship]:
        """Get all relationships for a specific person"""
        return self.db.query(Relationship).filter(
            or_(
                Relationship.from_person_id == person_id,
                Relationship.to_person_id == person_id
            )
        ).all()

    def get_family_tree_relationships(self, family_tree_id: uuid.UUID) -> List[Relationship]:
        """Get all relationships in a family tree"""
        # Get all people in the family tree first
        people = self.db.query(Person).filter(
            Person.family_tree_id == family_tree_id
        ).all()
        
        person_ids = [person.id for person in people]
        
        return self.db.query(Relationship).filter(
            Relationship.from_person_id.in_(person_ids),
            Relationship.to_person_id.in_(person_ids)
        ).all()

    def update_relationship(self, relationship_id: uuid.UUID, update_data: RelationshipUpdate) -> Relationship:
        """Update a relationship"""
        relationship = self.get_relationship(relationship_id)
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(relationship, field, value)
        
        self.db.commit()
        self.db.refresh(relationship)
        
        return relationship

    def delete_relationship(self, relationship_id: uuid.UUID) -> None:
        """Delete a relationship"""
        relationship = self.get_relationship(relationship_id)
        
        self.db.delete(relationship)
        self.db.commit()

    def get_spouses(self, person_id: uuid.UUID) -> List[Person]:
        """Get all spouses of a person"""
        spouse_relationships = self.db.query(Relationship).filter(
            or_(
                (Relationship.from_person_id == person_id) & (Relationship.relationship_type == "spouse"),
                (Relationship.to_person_id == person_id) & (Relationship.relationship_type == "spouse")
            ),
            Relationship.is_active == True
        ).all()
        
        spouse_ids = []
        for rel in spouse_relationships:
            if rel.from_person_id == person_id:
                spouse_ids.append(rel.to_person_id)
            else:
                spouse_ids.append(rel.from_person_id)
        
        return self.db.query(Person).filter(Person.id.in_(spouse_ids)).all()

    def get_children(self, person_id: uuid.UUID) -> List[Person]:
        """Get all children of a person"""
        child_relationships = self.db.query(Relationship).filter(
            Relationship.from_person_id == person_id,
            or_(
                Relationship.relationship_type == "child",
                Relationship.relationship_type == "adopted_child"
            ),
            Relationship.is_active == True
        ).all()
        
        child_ids = [rel.to_person_id for rel in child_relationships]
        
        return self.db.query(Person).filter(Person.id.in_(child_ids)).all()

    def get_parents(self, person_id: uuid.UUID) -> List[Person]:
        """Get all parents of a person"""
        parent_relationships = self.db.query(Relationship).filter(
            Relationship.to_person_id == person_id,
            or_(
                Relationship.relationship_type == "parent",
                Relationship.relationship_type == "adopted_parent"
            ),
            Relationship.is_active == True
        ).all()
        
        parent_ids = [rel.from_person_id for rel in parent_relationships]
        
        return self.db.query(Person).filter(Person.id.in_(parent_ids)).all()