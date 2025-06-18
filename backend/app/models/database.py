# backend/app/models/database.py

import uuid
from sqlalchemy import Column, String, Text, Boolean, Date, DateTime, ForeignKey, Integer, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    subscription_tier = Column(String(50), default="free", nullable=False)
    
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
    birth_date = Column(Date, nullable=True)  # Changed from DateTime
    death_date = Column(Date, nullable=True)  # Changed from DateTime
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
    """
    NEW RELATIONSHIP SYSTEM - Phase 2
    
    Represents bidirectional relationships between people with category-based organization.
    Single record represents both directions of the relationship.
    """
    __tablename__ = "relationships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    to_person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    
    # NEW: Relationship category instead of specific types
    # Categories: family_line, partner, sibling, extended_family
    relationship_category = Column(String(50), nullable=False)
    
    # NEW: Generation difference - only for family_line relationships
    # -1 = from_person is parent of to_person
    # +1 = from_person is child of to_person
    # null = not applicable (partner, sibling, extended_family)
    # Constraints: only -1, 0, +1 allowed (no grandparents direct links)
    generation_difference = Column(Integer, nullable=True)
    
    # Optional date information
    start_date = Column(DateTime, nullable=True)  # marriage date, adoption date, etc.
    end_date = Column(DateTime, nullable=True)    # divorce date, death affecting relationship
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # NEW: Relationship subtype for more specific categorization
    # Examples: 
    # - family_line: "biological", "adoptive", "step"
    # - partner: "married", "engaged", "dating", "divorced"
    # - sibling: "biological", "half", "step", "adoptive"
    # - extended_family: "aunt", "uncle", "cousin", "grandparent", "grandchild"
    relationship_subtype = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    from_person = relationship("Person", foreign_keys=[from_person_id], back_populates="relationships_from")
    to_person = relationship("Person", foreign_keys=[to_person_id], back_populates="relationships_to")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_relationships_from_person', 'from_person_id'),
        Index('ix_relationships_to_person', 'to_person_id'),
        Index('ix_relationships_category', 'relationship_category'),
        Index('ix_relationships_generation', 'generation_difference'),
        Index('ix_relationships_active', 'is_active'),
        # Composite index for common queries
        Index('ix_relationships_person_category', 'from_person_id', 'relationship_category'),
        Index('ix_relationships_bidirectional', 'from_person_id', 'to_person_id'),
    )
    
    def __repr__(self):
        return f"<Relationship {self.relationship_category}({self.generation_difference}) {self.from_person_id}->{self.to_person_id}>"

class PersonFile(Base):
    __tablename__ = "person_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("people.id"), nullable=False)
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'photo', 'document', 'video', etc.
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
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