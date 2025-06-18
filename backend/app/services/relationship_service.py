# backend/app/services/relationship_service.py

import uuid
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from fastapi import HTTPException, status
from enum import Enum

from app.models.database import Relationship, Person, FamilyTree
from app.schemas.schemas import (
    RelationshipCreate, 
    RelationshipUpdate, 
    RelationshipDisplay,
    RelationshipStatistics,
    InferredRelationship,
    RelationshipPath,
    RelationshipValidation
)

class RelationshipCategory(str, Enum):
    """Relationship categories for validation"""
    FAMILY_LINE = "family_line"
    PARTNER = "partner"
    SIBLING = "sibling"
    EXTENDED_FAMILY = "extended_family"

class RelationshipSubtype(str, Enum):
    """Relationship subtypes for validation"""
    # Family line
    BIOLOGICAL_PARENT = "biological_parent"
    ADOPTIVE_PARENT = "adoptive_parent"
    STEP_PARENT = "step_parent"
    FOSTER_PARENT = "foster_parent"
    
    # Partner
    SPOUSE = "spouse"
    DOMESTIC_PARTNER = "domestic_partner"
    ENGAGED = "engaged"
    
    # Sibling
    FULL_SIBLING = "full_sibling"
    HALF_SIBLING = "half_sibling"
    STEP_SIBLING = "step_sibling"
    ADOPTIVE_SIBLING = "adoptive_sibling"
    
    # Extended family
    GRANDPARENT = "grandparent"
    AUNT_UNCLE = "aunt_uncle"
    COUSIN = "cousin"
    NIECE_NEPHEW = "niece_nephew"

class RelationshipService:
    """
    Async service for managing family relationships with comprehensive business logic.
    Handles relationship creation, validation, inference, and graph analysis.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_relationship(self, relationship_data: RelationshipCreate) -> Relationship:
        """
        Create a new relationship with comprehensive validation and business logic.
        
        Args:
            relationship_data: Relationship creation data
            
        Returns:
            Created Relationship instance
            
        Raises:
            HTTPException: If validation fails or creation fails
        """
        try:
            # Validate that both people exist and are in the same family tree
            await self._validate_relationship_people(
                relationship_data.from_person_id, 
                relationship_data.to_person_id
            )
            
            # Check for duplicate relationships
            await self._check_duplicate_relationship(
                relationship_data.from_person_id, 
                relationship_data.to_person_id,
                relationship_data.relationship_category
            )
            
            # Validate business rules
            await self._validate_relationship_rules(relationship_data)
            
            # Create the relationship
            db_relationship = Relationship(**relationship_data.dict())
            
            self.db.add(db_relationship)
            await self.db.commit()
            await self.db.refresh(db_relationship)
            
            # Create reciprocal relationship if needed
            await self._create_reciprocal_relationship(db_relationship)
            
            return db_relationship
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create relationship: {str(e)}"
            )

    async def get_relationship(self, relationship_id: uuid.UUID) -> Relationship:
        """
        Get a relationship by ID.
        
        Args:
            relationship_id: UUID of the relationship
            
        Returns:
            Relationship instance
            
        Raises:
            HTTPException: If relationship not found
        """
        stmt = select(Relationship).where(Relationship.id == relationship_id)
        result = await self.db.execute(stmt)
        relationship = result.scalar_one_or_none()
        
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship not found"
            )
        
        return relationship

    async def update_relationship(self, relationship_id: uuid.UUID, update_data: RelationshipUpdate) -> Relationship:
        """
        Update a relationship with validation.
        
        Args:
            relationship_id: UUID of the relationship
            update_data: Update data with only changed fields
            
        Returns:
            Updated Relationship instance
            
        Raises:
            HTTPException: If relationship not found or update fails
        """
        try:
            relationship = await self.get_relationship(relationship_id)
            
            # Validate business rules if category or subtype is changing
            update_dict = update_data.dict(exclude_unset=True)
            if 'relationship_category' in update_dict or 'relationship_subtype' in update_dict:
                # Create a temporary relationship object for validation
                temp_data = RelationshipCreate(
                    from_person_id=relationship.from_person_id,
                    to_person_id=relationship.to_person_id,
                    relationship_category=update_dict.get('relationship_category', relationship.relationship_category),
                    relationship_subtype=update_dict.get('relationship_subtype', relationship.relationship_subtype),
                    generation_difference=update_dict.get('generation_difference', relationship.generation_difference)
                )
                await self._validate_relationship_rules(temp_data)
            
            # Update only provided fields
            for field, value in update_dict.items():
                setattr(relationship, field, value)
            
            await self.db.commit()
            await self.db.refresh(relationship)
            
            return relationship
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update relationship: {str(e)}"
            )

    async def delete_relationship(self, relationship_id: uuid.UUID) -> None:
        """
        Delete a relationship and its reciprocal if it exists.
        
        Args:
            relationship_id: UUID of the relationship to delete
            
        Raises:
            HTTPException: If relationship not found or deletion fails
        """
        try:
            relationship = await self.get_relationship(relationship_id)
            
            # Find and delete reciprocal relationship
            await self._delete_reciprocal_relationship(relationship)
            
            # Delete the main relationship
            await self.db.delete(relationship)
            await self.db.commit()
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete relationship: {str(e)}"
            )

    async def get_person_relationships(self, person_id: uuid.UUID, category: Optional[str] = None) -> List[Relationship]:
        """
        Get all relationships for a person, optionally filtered by category.
        
        Args:
            person_id: UUID of the person
            category: Optional relationship category filter
            
        Returns:
            List of Relationship instances
        """
        try:
            # Verify person exists
            await self._verify_person_exists(person_id)
            
            stmt = select(Relationship).where(
                or_(
                    Relationship.from_person_id == person_id,
                    Relationship.to_person_id == person_id
                )
            )
            
            if category:
                stmt = stmt.where(Relationship.relationship_category == category)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get person relationships: {str(e)}"
            )

    async def get_family_tree_relationships(self, family_tree_id: uuid.UUID) -> List[Relationship]:
        """
        Get all relationships in a family tree.
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            List of Relationship instances
        """
        try:
            # Verify family tree exists
            await self._verify_family_tree_exists(family_tree_id)
            
            stmt = select(Relationship).join(
                Person, Relationship.from_person_id == Person.id
            ).where(Person.family_tree_id == family_tree_id)
            
            result = await self.db.execute(stmt)
            return list(result.scalars().all())
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get family tree relationships: {str(e)}"
            )

    async def get_relationship_statistics(self, family_tree_id: uuid.UUID) -> RelationshipStatistics:
        """
        Get statistics about relationships in a family tree.
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            RelationshipStatistics object
        """
        try:
            relationships = await self.get_family_tree_relationships(family_tree_id)
            
            total_relationships = len(relationships)
            by_category = {}
            by_subtype = {}
            active_relationships = 0
            
            for rel in relationships:
                # Count by category
                category = rel.relationship_category
                by_category[category] = by_category.get(category, 0) + 1
                
                # Count by subtype
                if rel.relationship_subtype:
                    subtype = rel.relationship_subtype
                    by_subtype[subtype] = by_subtype.get(subtype, 0) + 1
                
                # Count active relationships
                if rel.is_active:
                    active_relationships += 1
            
            return RelationshipStatistics(
                total_relationships=total_relationships,
                by_category=by_category,
                by_subtype=by_subtype,
                active_relationships=active_relationships,
                inactive_relationships=total_relationships - active_relationships
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get relationship statistics: {str(e)}"
            )

    async def find_relationship_path(self, person1_id: uuid.UUID, person2_id: uuid.UUID, max_depth: int = 5) -> RelationshipPath:
        """
        Find the relationship path between two people using graph traversal.
        
        Args:
            person1_id: UUID of the first person
            person2_id: UUID of the second person
            max_depth: Maximum search depth
            
        Returns:
            RelationshipPath object with path and found status
        """
        try:
            # Verify both people exist
            await self._verify_person_exists(person1_id)
            await self._verify_person_exists(person2_id)
            
            if person1_id == person2_id:
                return RelationshipPath(path=[], relationship_found=True)
            
            # Get all relationships for the family tree
            person1 = await self._get_person(person1_id)
            relationships = await self.get_family_tree_relationships(person1.family_tree_id)
            
            # Build adjacency list for graph traversal
            graph = {}
            relationship_map = {}
            
            for rel in relationships:
                if rel.from_person_id not in graph:
                    graph[rel.from_person_id] = []
                if rel.to_person_id not in graph:
                    graph[rel.to_person_id] = []
                
                graph[rel.from_person_id].append(rel.to_person_id)
                relationship_map[(rel.from_person_id, rel.to_person_id)] = rel
                
                # Add reverse direction for undirected relationships
                if rel.relationship_category in ["partner", "sibling"]:
                    graph[rel.to_person_id].append(rel.from_person_id)
                    relationship_map[(rel.to_person_id, rel.from_person_id)] = rel
            
            # BFS to find shortest path
            path = await self._find_shortest_path(graph, relationship_map, person1_id, person2_id, max_depth)
            
            return RelationshipPath(
                path=path,
                relationship_found=len(path) > 0
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to find relationship path: {str(e)}"
            )

    async def infer_missing_relationships(self, family_tree_id: uuid.UUID) -> List[InferredRelationship]:
        """
        Infer missing relationships based on existing ones.
        
        Args:
            family_tree_id: UUID of the family tree
            
        Returns:
            List of InferredRelationship objects
        """
        try:
            inferred_relationships = []
            relationships = await self.get_family_tree_relationships(family_tree_id)
            
            # Build relationship maps
            parent_child_map = {}
            spouse_map = {}
            
            for rel in relationships:
                if rel.relationship_category == "family_line" and rel.generation_difference == -1:
                    # Parent to child relationship
                    if rel.from_person_id not in parent_child_map:
                        parent_child_map[rel.from_person_id] = []
                    parent_child_map[rel.from_person_id].append(rel.to_person_id)
                elif rel.relationship_category == "partner":
                    spouse_map[rel.from_person_id] = rel.to_person_id
                    spouse_map[rel.to_person_id] = rel.from_person_id
            
            # Infer sibling relationships
            for parent_id, children in parent_child_map.items():
                for i, child1 in enumerate(children):
                    for child2 in children[i+1:]:
                        # Check if sibling relationship already exists
                        existing = await self._relationship_exists(child1, child2, "sibling")
                        if not existing:
                            inferred_relationships.append(InferredRelationship(
                                type="sibling",
                                person1_id=str(child1),
                                person2_id=str(child2),
                                confidence="high",
                                reason=f"Both have same parent ({parent_id})"
                            ))
            
            # Infer grandparent relationships
            for parent_id, children in parent_child_map.items():
                if parent_id in parent_child_map:  # Parent has parents (grandparents)
                    grandparents = parent_child_map[parent_id]
                    for grandparent_id in grandparents:
                        for child_id in children:
                            existing = await self._relationship_exists(grandparent_id, child_id, "family_line")
                            if not existing:
                                inferred_relationships.append(InferredRelationship(
                                    type="grandparent",
                                    person1_id=str(grandparent_id),
                                    person2_id=str(child_id),
                                    confidence="high",
                                    reason=f"Parent-child chain through {parent_id}"
                                ))
            
            return inferred_relationships
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to infer relationships: {str(e)}"
            )

    async def validate_relationship(self, relationship_data: RelationshipCreate) -> RelationshipValidation:
        """
        Validate a relationship without creating it.
        
        Args:
            relationship_data: Relationship data to validate
            
        Returns:
            RelationshipValidation object
        """
        try:
            await self._validate_relationship_people(
                relationship_data.from_person_id,
                relationship_data.to_person_id
            )
            
            await self._validate_relationship_rules(relationship_data)
            
            duplicate = await self._check_duplicate_relationship(
                relationship_data.from_person_id,
                relationship_data.to_person_id,
                relationship_data.relationship_category,
                raise_error=False
            )
            
            if duplicate:
                return RelationshipValidation(
                    valid=False,
                    message="Relationship already exists"
                )
            
            return RelationshipValidation(
                valid=True,
                message="Relationship is valid"
            )
            
        except HTTPException as e:
            return RelationshipValidation(
                valid=False,
                message=e.detail
            )
        except Exception as e:
            return RelationshipValidation(
                valid=False,
                message=f"Validation error: {str(e)}"
            )

    # Private helper methods

    async def _validate_relationship_people(self, from_person_id: uuid.UUID, to_person_id: uuid.UUID) -> Tuple[Person, Person]:
        """Validate that both people exist and are in the same family tree."""
        if from_person_id == to_person_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create relationship between person and themselves"
            )
        
        from_person = await self._get_person(from_person_id)
        to_person = await self._get_person(to_person_id)
        
        if from_person.family_tree_id != to_person.family_tree_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both people must be in the same family tree"
            )
        
        return from_person, to_person

    async def _check_duplicate_relationship(self, from_person_id: uuid.UUID, to_person_id: uuid.UUID, 
                                          category: str, raise_error: bool = True) -> bool:
        """Check if a relationship already exists between two people."""
        stmt = select(Relationship).where(
            and_(
                Relationship.from_person_id == from_person_id,
                Relationship.to_person_id == to_person_id,
                Relationship.relationship_category == category
            )
        )
        
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing and raise_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Relationship already exists between these people"
            )
        
        return existing is not None

    async def _validate_relationship_rules(self, relationship_data: RelationshipCreate) -> None:
        """Validate business rules for relationships."""
        category = relationship_data.relationship_category
        subtype = relationship_data.relationship_subtype
        generation_diff = relationship_data.generation_difference
        
        # Validate category-subtype combinations
        valid_subtypes = {
            "family_line": ["biological_parent", "adoptive_parent", "step_parent", "foster_parent"],
            "partner": ["spouse", "domestic_partner", "engaged"],
            "sibling": ["full_sibling", "half_sibling", "step_sibling", "adoptive_sibling"],
            "extended_family": ["grandparent", "aunt_uncle", "cousin", "niece_nephew"]
        }
        
        if category in valid_subtypes and subtype not in valid_subtypes[category]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subtype '{subtype}' for category '{category}'"
            )
        
        # Validate generation differences
        if category == "family_line":
            if generation_diff is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Generation difference required for family_line relationships"
                )
            if abs(generation_diff) != 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Family line relationships must have generation difference of +1 or -1"
                )
        elif category in ["partner", "sibling"]:
            if generation_diff is not None and generation_diff != 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{category} relationships must have generation difference of 0"
                )

    async def _create_reciprocal_relationship(self, relationship: Relationship) -> None:
        """Create reciprocal relationship for bidirectional relationship types."""
        if relationship.relationship_category in ["partner", "sibling"]:
            # Check if reciprocal already exists
            existing = await self._relationship_exists(
                relationship.to_person_id,
                relationship.from_person_id,
                relationship.relationship_category
            )
            
            if not existing:
                reciprocal = Relationship(
                    from_person_id=relationship.to_person_id,
                    to_person_id=relationship.from_person_id,
                    relationship_category=relationship.relationship_category,
                    relationship_subtype=relationship.relationship_subtype,
                    generation_difference=0,  # Always 0 for bidirectional
                    is_active=relationship.is_active,
                    start_date=relationship.start_date,
                    end_date=relationship.end_date,
                    notes=relationship.notes
                )
                self.db.add(reciprocal)
                await self.db.commit()

    async def _delete_reciprocal_relationship(self, relationship: Relationship) -> None:
        """Delete reciprocal relationship if it exists."""
        if relationship.relationship_category in ["partner", "sibling"]:
            stmt = select(Relationship).where(
                and_(
                    Relationship.from_person_id == relationship.to_person_id,
                    Relationship.to_person_id == relationship.from_person_id,
                    Relationship.relationship_category == relationship.relationship_category
                )
            )
            result = await self.db.execute(stmt)
            reciprocal = result.scalar_one_or_none()
            
            if reciprocal:
                await self.db.delete(reciprocal)

    async def _relationship_exists(self, from_person_id: uuid.UUID, to_person_id: uuid.UUID, category: str) -> bool:
        """Check if a relationship exists between two people."""
        stmt = select(Relationship).where(
            and_(
                Relationship.from_person_id == from_person_id,
                Relationship.to_person_id == to_person_id,
                Relationship.relationship_category == category
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _get_person(self, person_id: uuid.UUID) -> Person:
        """Get a person by ID."""
        stmt = select(Person).where(Person.id == person_id)
        result = await self.db.execute(stmt)
        person = result.scalar_one_or_none()
        
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found"
            )
        
        return person

    async def _verify_person_exists(self, person_id: uuid.UUID) -> None:
        """Verify that a person exists."""
        await self._get_person(person_id)

    async def _verify_family_tree_exists(self, family_tree_id: uuid.UUID) -> None:
        """Verify that a family tree exists."""
        stmt = select(FamilyTree).where(FamilyTree.id == family_tree_id)
        result = await self.db.execute(stmt)
        family_tree = result.scalar_one_or_none()
        
        if not family_tree:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family tree not found"
            )

    async def _find_shortest_path(self, graph: Dict[uuid.UUID, List[uuid.UUID]], 
                                 relationship_map: Dict[Tuple[uuid.UUID, uuid.UUID], Relationship],
                                 start: uuid.UUID, end: uuid.UUID, max_depth: int) -> List[Relationship]:
        """Find shortest path between two people using BFS."""
        from collections import deque
        
        if start not in graph or end not in graph:
            return []
        
        queue = deque([(start, [])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) >= max_depth:
                continue
            
            if current == end:
                return path
            
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    relationship = relationship_map.get((current, neighbor))
                    if relationship:
                        queue.append((neighbor, path + [relationship]))
        
        return []