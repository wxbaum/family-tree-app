# backend/alembic/versions/001_complete_initial_schema.py

"""Complete initial schema with new relationship system

Revision ID: 001_complete_initial_schema
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_complete_initial_schema'
down_revision = None  # This is the first migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Create complete initial schema with new relationship system"""
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('subscription_tier', sa.String(50), nullable=False, default='free'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create family_trees table
    op.create_table('family_trees',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create people table
    op.create_table('people',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('family_tree_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('family_trees.id'), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('maiden_name', sa.String(100), nullable=True),
        sa.Column('birth_date', sa.DateTime(), nullable=True),
        sa.Column('death_date', sa.DateTime(), nullable=True),
        sa.Column('birth_place', sa.String(255), nullable=True),
        sa.Column('death_place', sa.String(255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profile_photo_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create relationships table with NEW SYSTEM
    op.create_table('relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('from_person_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('people.id'), nullable=False),
        sa.Column('to_person_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('people.id'), nullable=False),
        
        # NEW: Category-based system
        sa.Column('relationship_category', sa.String(50), nullable=False),
        
        # NEW: Generation difference (only for family_line)
        sa.Column('generation_difference', sa.Integer(), nullable=True),
        
        # NEW: Relationship subtype
        sa.Column('relationship_subtype', sa.String(50), nullable=True),
        
        # Date information
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        
        # Additional information
        sa.Column('notes', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Create person_files table
    op.create_table('person_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('people.id'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_family_trees_owner_id', 'family_trees', ['owner_id'])
    op.create_index('ix_people_family_tree_id', 'people', ['family_tree_id'])
    op.create_index('ix_people_names', 'people', ['first_name', 'last_name'])
    op.create_index('ix_relationships_from_person', 'relationships', ['from_person_id'])
    op.create_index('ix_relationships_to_person', 'relationships', ['to_person_id'])
    op.create_index('ix_relationships_category', 'relationships', ['relationship_category'])
    op.create_index('ix_relationships_generation', 'relationships', ['generation_difference'])
    op.create_index('ix_relationships_active', 'relationships', ['is_active'])
    op.create_index('ix_relationships_person_category', 'relationships', ['from_person_id', 'relationship_category'])
    op.create_index('ix_relationships_bidirectional', 'relationships', ['from_person_id', 'to_person_id'])
    op.create_index('ix_person_files_person_id', 'person_files', ['person_id'])
    op.create_index('ix_person_files_type', 'person_files', ['file_type'])
    
    # Create constraints for relationships
    op.create_check_constraint(
        'check_relationship_category',
        'relationships',
        "relationship_category IN ('family_line', 'partner', 'sibling', 'extended_family')"
    )
    
    op.create_check_constraint(
        'check_generation_difference',
        'relationships',
        "generation_difference IS NULL OR generation_difference IN (-1, 0, 1)"
    )
    
    op.create_check_constraint(
        'check_family_line_generation',
        'relationships',
        "(relationship_category != 'family_line') OR (generation_difference IS NOT NULL)"
    )
    
    op.create_check_constraint(
        'check_generation_only_family_line',
        'relationships',
        "(relationship_category = 'family_line') OR (generation_difference IS NULL)"
    )


def downgrade() -> None:
    """Drop all tables"""
    
    # Drop constraints first
    op.drop_constraint('check_relationship_category', 'relationships')
    op.drop_constraint('check_generation_difference', 'relationships')
    op.drop_constraint('check_family_line_generation', 'relationships')
    op.drop_constraint('check_generation_only_family_line', 'relationships')
    
    # Drop indexes
    op.drop_index('ix_family_trees_owner_id', 'family_trees')
    op.drop_index('ix_people_family_tree_id', 'people')
    op.drop_index('ix_people_names', 'people')
    op.drop_index('ix_relationships_from_person', 'relationships')
    op.drop_index('ix_relationships_to_person', 'relationships')
    op.drop_index('ix_relationships_category', 'relationships')
    op.drop_index('ix_relationships_generation', 'relationships')
    op.drop_index('ix_relationships_active', 'relationships')
    op.drop_index('ix_relationships_person_category', 'relationships')
    op.drop_index('ix_relationships_bidirectional', 'relationships')
    op.drop_index('ix_person_files_person_id', 'person_files')
    op.drop_index('ix_person_files_type', 'person_files')
    
    # Drop tables in reverse order
    op.drop_table('person_files')
    op.drop_table('relationships')
    op.drop_table('people')
    op.drop_table('family_trees')
    op.drop_table('users')