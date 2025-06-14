from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from fastapi_users.db import SQLAlchemyBaseUserTable
import uuid
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class User(SQLAlchemyBaseUserTable[uuid.UUID], Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Subscription fields
    subscription_tier = Column(String, default="free", nullable=False)
    subscription_expires = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    family_trees = relationship("FamilyTree", back_populates="owner", cascade="all, delete-orphan")

class FamilyTree(Base):
    __tablename__ = "family_trees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="family_trees")
    people = relationship("Person", back_populates="family_tree", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_family_trees_owner_id', 'owner_id'),
    )

class Person(Base):
    __tablename__ = "people"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    family_tree_id = Column(UUID(as_uuid=True), ForeignKey("family_trees.id"), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    maiden_name = Column(String(100), nullable=True)
    birth_date = Column(DateTime, nullable=True)
    death_date = Column(DateTime, nullable=True)
    birth_place = Column(String(255), nullable=True)
    death_place = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Display information
    profile_photo_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    family_tree = relationship("FamilyTree", back_populates="people")
    files = relationship("PersonFile", back_populates="person", cascade="all, delete-orphan")
    
    # Relationship edges - outgoing relationships
    relationships_from = relationship(
        "Relationship", 
        foreign_keys="Relationship.from_person_id",
        back_populates="from_person",
        cascade="all, delete-orphan"
    )
    
    # Relationship edges - incoming relationships
    relationships_to = relationship(
        "Relationship",
        foreign_keys="Relationship.to_person_id", 
        back_populates="to_person"
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_people_family_tree_id', 'family_tree_id'),
        Index('ix_people_names', 'first_name', 'last_name'),
    )
    
    @property
    def full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

class Relationship(Base):
    __tablename__ = "relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    to_person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    
    # Relationship type: spouse, parent, child, adopted_child, adopted_parent
    relationship_type = Column(String(50), nullable=False)
    
    # Optional date information
    start_date = Column(DateTime, nullable=True)  # marriage date, birth date, adoption date
    end_date = Column(DateTime, nullable=True)    # divorce date, death affecting relationship
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    from_person = relationship("Person", foreign_keys=[from_person_id], back_populates="relationships_from")
    to_person = relationship("Person", foreign_keys=[to_person_id], back_populates="relationships_to")
    
    # Indexes
    __table_args__ = (
        Index('ix_relationships_from_person', 'from_person_id'),
        Index('ix_relationships_to_person', 'to_person_id'),
        Index('ix_relationships_type', 'relationship_type'),
        Index('ix_relationships_active', 'is_active'),
    )

class PersonFile(Base):
    __tablename__ = "person_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path in object storage
    file_type = Column(String(50), nullable=False)   # image, pdf, document
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)      # Size in bytes
    
    # Optional metadata
    description = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    person = relationship("Person", back_populates="files")
    
    # Indexes
    __table_args__ = (
        Index('ix_person_files_person_id', 'person_id'),
        Index('ix_person_files_type', 'file_type'),
    )