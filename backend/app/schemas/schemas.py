# backend/app/schemas/schemas.py - Fixed User Schemas

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from fastapi_users import schemas  # IMPORTANT: Import FastAPI Users schemas

# User Schemas - FIXED to inherit from FastAPI Users base classes
class UserRead(schemas.BaseUser[uuid.UUID]):
    id: uuid.UUID
    email: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    subscription_tier: str = "free"
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(schemas.BaseUserCreate):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)

class UserUpdate(schemas.BaseUserUpdate):
    email: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

# Family Tree Schemas
class FamilyTreeBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None

class FamilyTreeCreate(FamilyTreeBase):
    pass

class FamilyTreeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None

class FamilyTreeRead(FamilyTreeBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Person Schemas
# Person Schemas - Fixed to use date instead of datetime

import uuid
from datetime import datetime, date  # Add date import
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from fastapi_users import schemas

# Person Schemas - FIXED: Use date for birth_date/death_date
class PersonBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    maiden_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[date] = None  # Changed from datetime to date
    death_date: Optional[date] = None  # Changed from datetime to date
    birth_place: Optional[str] = Field(None, max_length=255)
    death_place: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = Field(None, max_length=500)

class PersonCreate(PersonBase):
    family_tree_id: uuid.UUID

class PersonUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    maiden_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[date] = None  # Changed from datetime to date
    death_date: Optional[date] = None  # Changed from datetime to date
    birth_place: Optional[str] = Field(None, max_length=255)
    death_place: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = Field(None, max_length=500)

class PersonRead(PersonBase):
    id: uuid.UUID
    family_tree_id: uuid.UUID
    created_at: datetime  # Keep datetime for timestamps
    updated_at: Optional[datetime] = None  # Keep datetime for timestamps

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    class Config:
        from_attributes = True

# NEW RELATIONSHIP SCHEMAS - Phase 2
class RelationshipBase(BaseModel):
    """Base schema for the new relationship system"""
    
    # NEW: Category-based system
    relationship_category: str = Field(
        ..., 
        pattern="^(family_line|partner|sibling|extended_family)$",
        description="Category of relationship: family_line, partner, sibling, extended_family"
    )
    
    # NEW: Generation difference (only for family_line)
    generation_difference: Optional[int] = Field(
        None,
        ge=-1,
        le=1,
        description="Generation difference: -1 (parent), 0 (same generation), +1 (child). Only for family_line relationships."
    )
    
    # Optional relationship subtype for more specificity
    relationship_subtype: Optional[str] = Field(
        None, 
        max_length=50,
        description="Specific subtype: biological, adoptive, step, married, divorced, etc."
    )
    
    # Date information
    start_date: Optional[datetime] = Field(None, description="Start date of relationship (marriage, adoption, etc.)")
    end_date: Optional[datetime] = Field(None, description="End date of relationship (divorce, death, etc.)")
    
    # Status and notes
    is_active: bool = Field(True, description="Whether the relationship is currently active")
    notes: Optional[str] = Field(None, description="Additional notes about the relationship")

    @validator('generation_difference')
    def validate_generation_difference(cls, v, values):
        """Ensure generation_difference is only set for family_line relationships"""
        if 'relationship_category' in values:
            category = values['relationship_category']
            if category == 'family_line' and v is None:
                raise ValueError('generation_difference is required for family_line relationships')
            elif category != 'family_line' and v is not None:
                raise ValueError('generation_difference should only be set for family_line relationships')
        return v

    @validator('relationship_subtype')
    def validate_relationship_subtype(cls, v, values):
        """Validate that subtype is appropriate for the category"""
        if v and 'relationship_category' in values:
            category = values['relationship_category']
            valid_subtypes = {
                'family_line': ['biological', 'adoptive', 'step', 'foster'],
                'partner': ['married', 'engaged', 'dating', 'divorced', 'separated', 'widowed'],
                'sibling': ['biological', 'half', 'step', 'adoptive'],
                'extended_family': ['aunt', 'uncle', 'cousin', 'grandparent', 'grandchild', 'in_law']
            }
            
            if category in valid_subtypes and v not in valid_subtypes[category]:
                raise ValueError(f'Invalid subtype "{v}" for category "{category}". Valid subtypes: {valid_subtypes[category]}')
        
        return v

class RelationshipCreate(RelationshipBase):
    """Schema for creating a new relationship"""
    from_person_id: uuid.UUID = Field(..., description="ID of the first person in the relationship")
    to_person_id: uuid.UUID = Field(..., description="ID of the second person in the relationship")

    @validator('to_person_id')
    def validate_different_people(cls, v, values):
        """Ensure people don't have relationships with themselves"""
        if 'from_person_id' in values and v == values['from_person_id']:
            raise ValueError('A person cannot have a relationship with themselves')
        return v

class RelationshipUpdate(BaseModel):
    """Schema for updating an existing relationship"""
    relationship_category: Optional[str] = Field(
        None, 
        pattern="^(family_line|partner|sibling|extended_family)$"
    )
    generation_difference: Optional[int] = Field(None, ge=-1, le=1)
    relationship_subtype: Optional[str] = Field(None, max_length=50)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

    @validator('generation_difference')
    def validate_generation_difference_update(cls, v, values):
        """Validate generation_difference for updates"""
        # For updates, we can't validate against category if it's not provided
        # The service layer will handle this validation
        return v

class RelationshipRead(RelationshipBase):
    """Schema for reading relationship data"""
    id: uuid.UUID
    from_person_id: uuid.UUID
    to_person_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Enhanced relationship display schemas for frontend
class RelationshipDisplay(BaseModel):
    """Enhanced relationship information for frontend display"""
    id: uuid.UUID
    other_person_id: uuid.UUID
    other_person_name: str
    relationship_category: str
    generation_difference: Optional[int]
    relationship_subtype: Optional[str]
    description: str  # Human-readable description from perspective
    is_active: bool
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    notes: Optional[str]

# File Schemas
class PersonFileBase(BaseModel):
    filename: str
    original_filename: str
    file_type: str
    mime_type: str
    file_size: int
    description: Optional[str] = None

class PersonFileRead(PersonFileBase):
    id: uuid.UUID
    person_id: uuid.UUID
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Graph Data Schemas (for frontend visualization)
class GraphNode(BaseModel):
    id: str
    type: str = "person"
    data: PersonRead

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str  # Maps to relationship_category
    data: RelationshipRead

class FamilyTreeGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# Response Schemas
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str

# Relationship summary schemas for analytics/statistics
class RelationshipSummary(BaseModel):
    """Summary of relationships in a family tree"""
    total_relationships: int
    by_category: dict  # e.g., {"family_line": 15, "partner": 8, "sibling": 12}
    by_subtype: dict   # e.g., {"biological": 20, "adoptive": 3, "married": 8}
    generations_represented: int