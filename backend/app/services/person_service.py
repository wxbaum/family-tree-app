from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid

from app.models.database import Person
from app.schemas.schemas import PersonCreate, PersonUpdate

class PersonService:
    def __init__(self, db: Session):
        self.db = db

    def create_person(self, person_data: PersonCreate) -> Person:
        """Create a new person"""
        db_person = Person(**person_data.dict())
        
        self.db.add(db_person)
        self.db.commit()
        self.db.refresh(db_person)
        
        return db_person

    def get_person(self, person_id: uuid.UUID) -> Person:
        """Get a person by ID"""
        person = self.db.query(Person).filter(Person.id == person_id).first()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        return person

    def get_people_by_family_tree(self, family_tree_id: uuid.UUID) -> List[Person]:
        """Get all people in a family tree"""
        return self.db.query(Person).filter(
            Person.family_tree_id == family_tree_id
        ).order_by(Person.first_name, Person.last_name).all()

    def update_person(self, person_id: uuid.UUID, update_data: PersonUpdate) -> Person:
        """Update a person"""
        person = self.get_person(person_id)
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(person, field, value)
        
        self.db.commit()
        self.db.refresh(person)
        
        return person

    def delete_person(self, person_id: uuid.UUID) -> None:
        """Delete a person and all associated relationships"""
        person = self.get_person(person_id)
        
        self.db.delete(person)
        self.db.commit()

    def search_people(self, family_tree_id: uuid.UUID, search_term: str) -> List[Person]:
        """Search for people by name within a family tree"""
        return self.db.query(Person).filter(
            Person.family_tree_id == family_tree_id,
            (Person.first_name.ilike(f"%{search_term}%") |
             Person.last_name.ilike(f"%{search_term}%") |
             Person.maiden_name.ilike(f"%{search_term}%"))
        ).all()