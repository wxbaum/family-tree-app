# backend/app/services/relationship_service.py

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status

from app.models.database import Relationship, Person
from app.schemas.schemas import RelationshipCreate, RelationshipUpdate, RelationshipDisplay

class RelationshipService:
    """
    NEW RELATIONSHIP SERVICE - Phase 2
    
    Handles the improved relationship system with:
    - Category-based relationships (family_line, partner, sibling, extended_family)
    - Generation tracking for family_line relationships
    - Bidirectional relationship logic
    - Clean relationship inference
    """
    
    def __init__(self, db: Session):
        self.db = db

    def create_relationship(self, relationship_data: RelationshipCreate) -> Relationship:
        """
        Create a new relationship with improved validation and logic
        """
        # Validate that both people exist and are in the same family tree
        self._validate_relationship_people(relationship_data.from_person_id, relationship_data.to_person_id)
        
        # Check for duplicate relationships
        self._check_duplicate_relationship(
            relationship_data.from_person_id, 
            relationship_data.to_person_id,
            relationship_data.relationship_category
        )
        
        # Validate business rules
        self._validate_relationship_rules(relationship_data)
        
        # Create the relationship
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

    def update_relationship(self, relationship_id: uuid.UUID, update_data: RelationshipUpdate) -> Relationship:
        """Update a relationship with validation"""
        relationship = self.get_relationship(relationship_id)
        
        # Create a temporary object to validate the full updated relationship
        temp_data = RelationshipCreate(
            from_person_id=relationship.from_person_id,
            to_person_id=relationship.to_person_id,
            relationship_category=update_data.relationship_category or relationship.relationship_category,
            generation_difference=update_data.generation_difference if update_data.generation_difference is not None else relationship.generation_difference,
            relationship_subtype=update_data.relationship_subtype or relationship.relationship_subtype,
            start_date=update_data.start_date if update_data.start_date is not None else relationship.start_date,
            end_date=update_data.end_date if update_data.end_date is not None else relationship.end_date,
            is_active=update_data.is_active if update_data.is_active is not None else relationship.is_active,
            notes=update_data.notes or relationship.notes
        )
        
        # Validate the updated relationship
        self._validate_relationship_rules(temp_data)
        
        # Apply updates
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(relationship, field, value)
        
        self.db.commit()
        self.db.refresh(relationship)
        
        return relationship

    def delete_relationship(self, relationship_id: uuid.UUID) -> None:
        """Delete a relationship"""
        relationship = self.get_relationship(relationship_id)
        
        self.db.delete(relationship)
        self.db.commit()

    def get_person_relationships(self, person_id: uuid.UUID) -> List[Relationship]:
        """Get all relationships for a specific person (bidirectional)"""
        return self.db.query(Relationship).filter(
            or_(
                Relationship.from_person_id == person_id,
                Relationship.to_person_id == person_id
            ),
            Relationship.is_active == True
        ).all()

    def get_person_relationships_display(self, person_id: uuid.UUID) -> List[RelationshipDisplay]:
        """
        Get relationships for display with proper perspective interpretation
        """
        relationships = self.get_person_relationships(person_id)
        display_relationships = []
        
        for rel in relationships:
            # Determine the other person and perspective
            if rel.from_person_id == person_id:
                other_person_id = rel.to_person_id
                is_from_perspective = True
            else:
                other_person_id = rel.from_person_id
                is_from_perspective = False
            
            # Get other person's name
            other_person = self.db.query(Person).filter(Person.id == other_person_id).first()
            if not other_person:
                continue
            
            # Generate description from current person's perspective
            description = self._get_relationship_description(rel, is_from_perspective)
            
            display_relationships.append(RelationshipDisplay(
                id=rel.id,
                other_person_id=other_person_id,
                other_person_name=other_person.full_name,
                relationship_category=rel.relationship_category,
                generation_difference=rel.generation_difference,
                relationship_subtype=rel.relationship_subtype,
                description=description,
                is_active=rel.is_active,
                start_date=rel.start_date,
                end_date=rel.end_date,
                notes=rel.notes
            ))
        
        return display_relationships

    def get_family_tree_relationships(self, family_tree_id: uuid.UUID) -> List[Relationship]:
        """Get all relationships in a family tree"""
        # Get all people in the family tree
        people_ids = self.db.query(Person.id).filter(
            Person.family_tree_id == family_tree_id
        ).subquery()
        
        return self.db.query(Relationship).filter(
            Relationship.from_person_id.in_(people_ids),
            Relationship.to_person_id.in_(people_ids)
        ).all()

    # NEW: Enhanced relationship querying methods
    def get_family_line_relationships(self, person_id: uuid.UUID) -> Dict[str, List[Person]]:
        """
        Get family line relationships organized by type
        Returns: {"parents": [...], "children": [...]}
        """
        relationships = self.db.query(Relationship).filter(
            or_(
                Relationship.from_person_id == person_id,
                Relationship.to_person_id == person_id
            ),
            Relationship.relationship_category == "family_line",
            Relationship.is_active == True
        ).all()
        
        parents = []
        children = []
        
        for rel in relationships:
            if rel.from_person_id == person_id:
                # Person is the "from" person
                if rel.generation_difference == -1:
                    # Person is parent of to_person, so to_person is child
                    child = self.db.query(Person).filter(Person.id == rel.to_person_id).first()
                    if child:
                        children.append(child)
                elif rel.generation_difference == 1:
                    # Person is child of to_person, so to_person is parent
                    parent = self.db.query(Person).filter(Person.id == rel.to_person_id).first()
                    if parent:
                        parents.append(parent)
            else:
                # Person is the "to" person
                if rel.generation_difference == -1:
                    # from_person is parent of person, so from_person is parent
                    parent = self.db.query(Person).filter(Person.id == rel.from_person_id).first()
                    if parent:
                        parents.append(parent)
                elif rel.generation_difference == 1:
                    # from_person is child of person, so from_person is child
                    child = self.db.query(Person).filter(Person.id == rel.from_person_id).first()
                    if child:
                        children.append(child)
        
        return {"parents": parents, "children": children}

    def get_partners(self, person_id: uuid.UUID) -> List[Person]:
        """Get all partners/spouses of a person"""
        partner_relationships = self.db.query(Relationship).filter(
            or_(
                Relationship.from_person_id == person_id,
                Relationship.to_person_id == person_id
            ),
            Relationship.relationship_category == "partner",
            Relationship.is_active == True
        ).all()
        
        partner_ids = []
        for rel in partner_relationships:
            if rel.from_person_id == person_id:
                partner_ids.append(rel.to_person_id)
            else:
                partner_ids.append(rel.from_person_id)
        
        return self.db.query(Person).filter(Person.id.in_(partner_ids)).all()

    def get_siblings(self, person_id: uuid.UUID) -> List[Person]:
        """Get all siblings of a person"""
        sibling_relationships = self.db.query(Relationship).filter(
            or_(
                Relationship.from_person_id == person_id,
                Relationship.to_person_id == person_id
            ),
            Relationship.relationship_category == "sibling",
            Relationship.is_active == True
        ).all()
        
        sibling_ids = []
        for rel in sibling_relationships:
            if rel.from_person_id == person_id:
                sibling_ids.append(rel.to_person_id)
            else:
                sibling_ids.append(rel.from_person_id)
        
        return self.db.query(Person).filter(Person.id.in_(sibling_ids)).all()

    # Private helper methods
    def _validate_relationship_people(self, from_person_id: uuid.UUID, to_person_id: uuid.UUID) -> None:
        """Validate that both people exist and are in the same family tree"""
        from_person = self.db.query(Person).filter(Person.id == from_person_id).first()
        to_person = self.db.query(Person).filter(Person.id == to_person_id).first()
        
        if not from_person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="From person not found"
            )
        
        if not to_person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="To person not found"
            )
        
        if from_person.family_tree_id != to_person.family_tree_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both people must be in the same family tree"
            )

    def _check_duplicate_relationship(self, from_person_id: uuid.UUID, to_person_id: uuid.UUID, category: str) -> None:
        """Check for duplicate relationships (bidirectional)"""
        existing = self.db.query(Relationship).filter(
            or_(
                and_(
                    Relationship.from_person_id == from_person_id,
                    Relationship.to_person_id == to_person_id
                ),
                and_(
                    Relationship.from_person_id == to_person_id,
                    Relationship.to_person_id == from_person_id
                )
            ),
            Relationship.relationship_category == category,
            Relationship.is_active == True
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A {category} relationship already exists between these people"
            )

    def _validate_relationship_rules(self, relationship_data: RelationshipCreate) -> None:
        """Validate business rules for relationships"""
        
        # Rule 1: Generation difference validation
        if relationship_data.relationship_category == "family_line":
            if relationship_data.generation_difference is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Generation difference is required for family_line relationships"
                )
            if relationship_data.generation_difference not in [-1, 1]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Generation difference must be -1 (parent) or +1 (child) for family_line relationships"
                )
        else:
            if relationship_data.generation_difference is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Generation difference should only be set for family_line relationships"
                )
        
        # Rule 2: Self-relationship validation (already handled in schema)
        
        # Rule 3: Category-specific validations
        if relationship_data.relationship_category == "partner":
            # Partners should not have multiple active partner relationships (optional business rule)
            self._validate_partner_exclusivity(relationship_data.from_person_id, relationship_data.to_person_id)
        
        # Rule 4: Validate relationship subtype
        self._validate_relationship_subtype(relationship_data.relationship_category, relationship_data.relationship_subtype)

    def _validate_partner_exclusivity(self, person1_id: uuid.UUID, person2_id: uuid.UUID) -> None:
        """
        Optional: Validate that people don't have multiple active partner relationships
        This is a business rule that may vary by application requirements
        """
        # Check if person1 already has an active partner
        existing_partner1 = self.db.query(Relationship).filter(
            or_(
                Relationship.from_person_id == person1_id,
                Relationship.to_person_id == person1_id
            ),
            Relationship.relationship_category == "partner",
            Relationship.is_active == True
        ).first()
        
        # Check if person2 already has an active partner
        existing_partner2 = self.db.query(Relationship).filter(
            or_(
                Relationship.from_person_id == person2_id,
                Relationship.to_person_id == person2_id
            ),
            Relationship.relationship_category == "partner",
            Relationship.is_active == True
        ).first()
        
        if existing_partner1:
            person1 = self.db.query(Person).filter(Person.id == person1_id).first()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{person1.full_name if person1 else 'Person'} already has an active partner relationship"
            )
        
        if existing_partner2:
            person2 = self.db.query(Person).filter(Person.id == person2_id).first()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{person2.full_name if person2 else 'Person'} already has an active partner relationship"
            )

    def _validate_relationship_subtype(self, category: str, subtype: Optional[str]) -> None:
        """Validate that relationship subtype is appropriate for the category"""
        if not subtype:
            return
        
        valid_subtypes = {
            'family_line': ['biological', 'adoptive', 'step', 'foster'],
            'partner': ['married', 'engaged', 'dating', 'divorced', 'separated', 'widowed'],
            'sibling': ['biological', 'half', 'step', 'adoptive'],
            'extended_family': ['aunt', 'uncle', 'cousin', 'grandparent', 'grandchild', 'in_law']
        }
        
        if category in valid_subtypes and subtype not in valid_subtypes[category]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Invalid subtype "{subtype}" for category "{category}". Valid subtypes: {valid_subtypes[category]}'
            )

    def _get_relationship_description(self, relationship: Relationship, is_from_perspective: bool) -> str:
        """
        Generate human-readable relationship description from a person's perspective
        """
        category = relationship.relationship_category
        subtype = relationship.relationship_subtype
        generation_diff = relationship.generation_difference
        
        if category == "family_line":
            if is_from_perspective:
                # Person is the "from" person
                if generation_diff == -1:
                    return f"Parent ({subtype or 'biological'})"
                elif generation_diff == 1:
                    return f"Child ({subtype or 'biological'})"
            else:
                # Person is the "to" person, so reverse the perspective
                if generation_diff == -1:
                    return f"Child ({subtype or 'biological'})"
                elif generation_diff == 1:
                    return f"Parent ({subtype or 'biological'})"
        
        elif category == "partner":
            if subtype:
                return f"Partner ({subtype})"
            return "Partner"
        
        elif category == "sibling":
            if subtype:
                return f"Sibling ({subtype})"
            return "Sibling"
        
        elif category == "extended_family":
            if subtype:
                return f"Extended Family ({subtype})"
            return "Extended Family"
        
        return f"{category.replace('_', ' ').title()}"

    # NEW: Advanced relationship analysis methods
    def get_relationship_path(self, person1_id: uuid.UUID, person2_id: uuid.UUID) -> Optional[List[Relationship]]:
        """
        Find the shortest relationship path between two people
        Useful for determining how people are related
        """
        # This is a complex graph traversal problem
        # For now, we'll implement a basic version that finds direct relationships
        direct_relationship = self.db.query(Relationship).filter(
            or_(
                and_(
                    Relationship.from_person_id == person1_id,
                    Relationship.to_person_id == person2_id
                ),
                and_(
                    Relationship.from_person_id == person2_id,
                    Relationship.to_person_id == person1_id
                )
            ),
            Relationship.is_active == True
        ).first()
        
        if direct_relationship:
            return [direct_relationship]
        
        # TODO: Implement multi-hop relationship finding using BFS
        # This would find relationships like "cousin" (through shared grandparents)
        return None

    def get_family_statistics(self, family_tree_id: uuid.UUID) -> Dict[str, Any]:
        """Get statistics about relationships in a family tree"""
        relationships = self.get_family_tree_relationships(family_tree_id)
        
        stats = {
            "total_relationships": len(relationships),
            "by_category": {},
            "by_subtype": {},
            "active_relationships": 0,
            "inactive_relationships": 0
        }
        
        for rel in relationships:
            # Count by category
            category = rel.relationship_category
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            # Count by subtype
            if rel.relationship_subtype:
                subtype = rel.relationship_subtype
                stats["by_subtype"][subtype] = stats["by_subtype"].get(subtype, 0) + 1
            
            # Count by status
            if rel.is_active:
                stats["active_relationships"] += 1
            else:
                stats["inactive_relationships"] += 1
        
        return stats

    def infer_relationships(self, family_tree_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Infer potential relationships based on existing data
        For example, if A is parent of B and A is parent of C, then B and C might be siblings
        """
        inferred_relationships = []
        
        # Get all family_line relationships
        family_relationships = self.db.query(Relationship).filter(
            Relationship.relationship_category == "family_line",
            Relationship.is_active == True
        ).join(Person, Person.id == Relationship.from_person_id).filter(
            Person.family_tree_id == family_tree_id
        ).all()
        
        # Group by parent-child relationships
        parent_children = {}
        for rel in family_relationships:
            if rel.generation_difference == -1:  # from_person is parent
                parent_id = rel.from_person_id
                child_id = rel.to_person_id
            else:  # to_person is parent
                parent_id = rel.to_person_id
                child_id = rel.from_person_id
            
            if parent_id not in parent_children:
                parent_children[parent_id] = []
            parent_children[parent_id].append(child_id)
        
        # Infer sibling relationships
        for parent_id, children in parent_children.items():
            if len(children) > 1:
                for i, child1 in enumerate(children):
                    for child2 in children[i+1:]:
                        # Check if sibling relationship already exists
                        existing = self.db.query(Relationship).filter(
                            or_(
                                and_(
                                    Relationship.from_person_id == child1,
                                    Relationship.to_person_id == child2
                                ),
                                and_(
                                    Relationship.from_person_id == child2,
                                    Relationship.to_person_id == child1
                                )
                            ),
                            Relationship.relationship_category == "sibling"
                        ).first()
                        
                        if not existing:
                            inferred_relationships.append({
                                "type": "sibling",
                                "person1_id": child1,
                                "person2_id": child2,
                                "confidence": "high",
                                "reason": f"Both are children of the same parent"
                            })
        
        return inferred_relationships