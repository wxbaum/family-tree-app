# backend/app/services/person_service.py

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, status
import uuid
from datetime import date, datetime

from app.models.database import Person, Relationship, FamilyTree
from app.schemas.schemas import PersonCreate, PersonUpdate

class PersonService:
    """
    Async service for managing people in family trees.
    Handles person CRUD operations, search, and relationship queries.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_person(self, person_data: PersonCreate) -> Person:
        """
        Create a new person in a family tree.
        
        Args:
            person_data: Person creation data
            
        Returns:
            Created Person instance
            
        Raises:
            HTTPException: If creation fails or family tree doesn't exist
        """
        try:
            # Verify family tree exists
            await self._verify_family_tree_exists(person_data.family_tree_id)
            
            # Validate dates if provided
            if person_data.birth_date and person_data.death_date:
                if person_data.birth_date >= person_data.death_date:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Birth date must be before death date"
                    )
            
            db_person = Person(**person_data.dict())
            
            self.db.add(db_person)
            await self.db.commit()
            await self.db.refresh(db_person)
            
            return db_person
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create person: {str(e)}"
            )

    async def get_person(self, person_id: uuid.UUID) -> Person:
        """
        Get a person by ID.
        
        Args:
            person_id: UUID of the person
            
        Returns:
            Person instance
            
        Raises:
            HTTPException: If person not found
        """
        stmt = select(Person).where(Person.id == person_id)
        result = await self.db.execute(stmt)
        person = result.scalar_one_or_none()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        return person

    async def get_people_by_family_tree(self, family_tree_id: uuid.UUID, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Person]:
        """
        Get all people in a family tree with optional pagination.
        
        Args:
            family_tree_id: UUID of the family tree
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of Person instances
        """
        try:
            stmt = select(Person).where(
                Person.family_tree_id == family_tree_id
            ).order_by(Person.first_name, Person.last_name)
            
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get people: {str(e)}"
            )

    async def get_people_count(self, family_tree_id: uuid.UUID) -> int:
        """
        Get the total count of people in a family tree.
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            Total count of people
        """
        try:
            stmt = select(func.count(Person.id)).where(Person.family_tree_id == family_tree_id)
            result = await self.db.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get people count: {str(e)}"
            )

    async def update_person(self, person_id: uuid.UUID, update_data: PersonUpdate) -> Person:
        """
        Update a person with new data.
        
        Args:
            person_id: UUID of the person
            update_data: Update data with only changed fields
            
        Returns:
            Updated Person instance
            
        Raises:
            HTTPException: If person not found or update fails
        """
        try:
            person = await self.get_person(person_id)
            
            # Validate dates if both are provided
            update_dict = update_data.dict(exclude_unset=True)
            birth_date = update_dict.get('birth_date', person.birth_date)
            death_date = update_dict.get('death_date', person.death_date)
            
            if birth_date and death_date and birth_date >= death_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Birth date must be before death date"
                )
            
            # Update only provided fields
            for field, value in update_dict.items():
                setattr(person, field, value)
            
            await self.db.commit()
            await self.db.refresh(person)
            
            return person
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update person: {str(e)}"
            )

    async def delete_person(self, person_id: uuid.UUID) -> None:
        """
        Delete a person and all associated relationships.
        This is a cascading delete operation.
        
        Args:
            person_id: UUID of the person to delete
            
        Raises:
            HTTPException: If person not found or deletion fails
        """
        try:
            person = await self.get_person(person_id)
            
            # Cascading delete is handled by database relationships
            await self.db.delete(person)
            await self.db.commit()
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete person: {str(e)}"
            )

    async def search_people(self, family_tree_id: uuid.UUID, search_term: str, limit: Optional[int] = 50) -> List[Person]:
        """
        Search for people by name within a family tree.
        
        Args:
            family_tree_id: UUID of the family tree
            search_term: Search term to match against names
            limit: Maximum number of results (default 50)
            
        Returns:
            List of matching Person instances
        """
        try:
            stmt = select(Person).where(
                and_(
                    Person.family_tree_id == family_tree_id,
                    or_(
                        Person.first_name.ilike(f"%{search_term}%"),
                        Person.last_name.ilike(f"%{search_term}%"),
                        Person.maiden_name.ilike(f"%{search_term}%")
                    )
                )
            ).order_by(Person.first_name, Person.last_name)
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search people: {str(e)}"
            )

    async def get_person_relationships(self, person_id: uuid.UUID) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all relationships for a person, organized by type.
        
        Args:
            person_id: UUID of the person
            
        Returns:
            Dictionary of relationships organized by category
        """
        try:
            # Verify person exists
            await self.get_person(person_id)
            
            # Get relationships where this person is the source
            outgoing_stmt = select(Relationship).where(Relationship.from_person_id == person_id)
            outgoing_result = await self.db.execute(outgoing_stmt)
            outgoing_relationships = outgoing_result.scalars().all()
            
            # Get relationships where this person is the target
            incoming_stmt = select(Relationship).where(Relationship.to_person_id == person_id)
            incoming_result = await self.db.execute(incoming_stmt)
            incoming_relationships = incoming_result.scalars().all()
            
            # Organize by category
            relationships_by_category = {}
            
            for rel in outgoing_relationships:
                category = rel.relationship_category
                if category not in relationships_by_category:
                    relationships_by_category[category] = []
                
                # Get the target person
                target_person = await self.get_person(rel.to_person_id)
                relationships_by_category[category].append({
                    "relationship_id": str(rel.id),
                    "person_id": str(target_person.id),
                    "person_name": f"{target_person.first_name} {target_person.last_name or ''}".strip(),
                    "relationship_subtype": rel.relationship_subtype,
                    "generation_difference": rel.generation_difference,
                    "is_active": rel.is_active,
                    "direction": "outgoing"
                })
            
            for rel in incoming_relationships:
                category = rel.relationship_category
                if category not in relationships_by_category:
                    relationships_by_category[category] = []
                
                # Get the source person
                source_person = await self.get_person(rel.from_person_id)
                relationships_by_category[category].append({
                    "relationship_id": str(rel.id),
                    "person_id": str(source_person.id),
                    "person_name": f"{source_person.first_name} {source_person.last_name or ''}".strip(),
                    "relationship_subtype": rel.relationship_subtype,
                    "generation_difference": rel.generation_difference,
                    "is_active": rel.is_active,
                    "direction": "incoming"
                })
            
            return relationships_by_category
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get person relationships: {str(e)}"
            )

    async def get_person_ancestors(self, person_id: uuid.UUID, generations: Optional[int] = None) -> List[Person]:
        """
        Get ancestors of a person (parents, grandparents, etc.).
        
        Args:
            person_id: UUID of the person
            generations: Number of generations to go back (None for all)
            
        Returns:
            List of ancestor Person instances
        """
        try:
            # Verify person exists
            await self.get_person(person_id)
            
            # This is a simplified implementation - a full implementation would
            # recursively traverse the family_line relationships with negative generation_difference
            stmt = select(Person).join(
                Relationship, Person.id == Relationship.from_person_id
            ).where(
                and_(
                    Relationship.to_person_id == person_id,
                    Relationship.relationship_category == "family_line",
                    Relationship.generation_difference < 0  # Ancestors have negative generation difference
                )
            )
            
            if generations:
                stmt = stmt.where(Relationship.generation_difference >= -generations)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get ancestors: {str(e)}"
            )

    async def get_person_descendants(self, person_id: uuid.UUID, generations: Optional[int] = None) -> List[Person]:
        """
        Get descendants of a person (children, grandchildren, etc.).
        
        Args:
            person_id: UUID of the person
            generations: Number of generations to go forward (None for all)
            
        Returns:
            List of descendant Person instances
        """
        try:
            # Verify person exists
            await self.get_person(person_id)
            
            # This is a simplified implementation - a full implementation would
            # recursively traverse the family_line relationships with positive generation_difference
            stmt = select(Person).join(
                Relationship, Person.id == Relationship.to_person_id
            ).where(
                and_(
                    Relationship.from_person_id == person_id,
                    Relationship.relationship_category == "family_line",
                    Relationship.generation_difference > 0  # Descendants have positive generation difference
                )
            )
            
            if generations:
                stmt = stmt.where(Relationship.generation_difference <= generations)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get descendants: {str(e)}"
            )

    async def get_person_siblings(self, person_id: uuid.UUID) -> List[Person]:
        """
        Get siblings of a person.
        
        Args:
            person_id: UUID of the person
            
        Returns:
            List of sibling Person instances
        """
        try:
            # Verify person exists
            await self.get_person(person_id)
            
            # Get siblings through sibling relationships
            siblings_stmt = select(Person).join(
                Relationship, 
                or_(
                    and_(Person.id == Relationship.to_person_id, Relationship.from_person_id == person_id),
                    and_(Person.id == Relationship.from_person_id, Relationship.to_person_id == person_id)
                )
            ).where(
                and_(
                    Relationship.relationship_category == "sibling",
                    Person.id != person_id  # Exclude the person themselves
                )
            )
            
            result = await self.db.execute(siblings_stmt)
            return list(result.scalars().all())
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get siblings: {str(e)}"
            )

    async def calculate_person_age(self, person_id: uuid.UUID, as_of_date: Optional[date] = None) -> Optional[int]:
        """
        Calculate a person's age as of a specific date.
        
        Args:
            person_id: UUID of the person
            as_of_date: Date to calculate age as of (defaults to today)
            
        Returns:
            Age in years, or None if birth date not available
        """
        try:
            person = await self.get_person(person_id)
            
            if not person.birth_date:
                return None
            
            if as_of_date is None:
                as_of_date = date.today()
            
            # Use death date if person is deceased and as_of_date is after death
            end_date = as_of_date
            if person.death_date and as_of_date > person.death_date:
                end_date = person.death_date
            
            age = end_date.year - person.birth_date.year
            if end_date.month < person.birth_date.month or \
               (end_date.month == person.birth_date.month and end_date.day < person.birth_date.day):
                age -= 1
            
            return age
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to calculate age: {str(e)}"
            )

    async def _verify_family_tree_exists(self, family_tree_id: uuid.UUID) -> FamilyTree:
        """
        Verify that a family tree exists.
        
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