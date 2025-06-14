from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from fastapi_users import schemas
import uuid

# User Schemas
class UserRead(schemas.BaseUser[uuid.UUID]):
    id: uuid.UUID
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    subscription_tier: str = "free"
    subscription_expires: Optional[datetime] = None
    created_at: datetime

class UserCreate(schemas.BaseUserCreate):
    email: EmailStr
    password: str

class UserUpdate(schemas.BaseUserUpdate):
    password: Optional[str] = None
    email: Optional[EmailStr] = None

# Family Tree Schemas
class FamilyTreeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class FamilyTreeCreate(FamilyTreeBase):
    pass

class FamilyTreeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class FamilyTreeRead(FamilyTreeBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Person Schemas
class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    maiden_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    birth_place: Optional[str] = Field(None, max_length=255)
    death_place: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None

class PersonCreate(PersonBase):
    family_tree_id: uuid.UUID

class PersonUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    maiden_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[datetime] = None
    death_date: Optional[datetime] = None
    birth_place: Optional[str] = Field(None, max_length=255)
    death_place: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = None
    profile_photo_url: Optional[str] = None

class PersonRead(PersonBase):
    id: uuid.UUID
    family_tree_id: uuid.UUID
    profile_photo_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    full_name: str
    
    class Config:
        from_attributes = True

# Relationship Schemas
class RelationshipBase(BaseModel):
    relationship_type: str = Field(..., pattern="^(spouse|parent|child|adopted_child|adopted_parent)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    notes: Optional[str] = None

class RelationshipCreate(RelationshipBase):
    from_person_id: uuid.UUID
    to_person_id: uuid.UUID

class RelationshipUpdate(BaseModel):
    relationship_type: Optional[str] = Field(None, pattern="^(spouse|parent|child|adopted_child|adopted_parent)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class RelationshipRead(RelationshipBase):
    id: uuid.UUID
    from_person_id: uuid.UUID
    to_person_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

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
    type: str
    data: RelationshipRead

class FamilyTreeGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# Response Schemas
class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    detail: str