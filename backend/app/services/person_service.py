from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import uuid

from app.models.database import Person
from app.schemas.schemas import PersonCreate, PersonUpdate

class PersonService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_person(self, person_data: PersonCreate) -> Person:
        """Create a new person"""
        db_person = Person(**person_data.dict())
        
        self.db.add(db_person)
        await self.db.commit()
        await self.db.refresh(db_person)
        
        return db_person

    async def get_person(self, person_id: uuid.UUID) -> Person:
        """Get a person by ID"""
        stmt = select(Person).where(Person.id == person_id)
        result = await self.db.execute(stmt)
        person = result.scalar_one_or_none()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        return person

    async def get_people_by_family_tree(self, family_tree_id: uuid.UUID) -> List[Person]:
        """Get all people in a family tree"""
        stmt = select(Person).where(
            Person.family_tree_id == family_tree_id
        ).order_by(Person.first_name, Person.last_name)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_person(self, person_id: uuid.UUID, update_data: PersonUpdate) -> Person:
        """Update a person"""
        person = await self.get_person(person_id)
        
        # Update only provided fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(person, field, value)
        
        await self.db.commit()
        await self.db.refresh(person)
        
        return person

    async def delete_person(self, person_id: uuid.UUID) -> None:
        """Delete a person and all associated relationships"""
        person = await self.get_person(person_id)
        
        await self.db.delete(person)
        await self.db.commit()

    async def search_people(self, family_tree_id: uuid.UUID, search_term: str) -> List[Person]:
        """Search for people by name within a family tree"""
        stmt = select(Person).where(
            Person.family_tree_id == family_tree_id,
            (Person.first_name.ilike(f"%{search_term}%") |
             Person.last_name.ilike(f"%{search_term}%") |
             Person.maiden_name.ilike(f"%{search_term}%"))
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()