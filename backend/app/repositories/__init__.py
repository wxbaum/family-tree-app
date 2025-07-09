# backend/app/repositories/__init__.py

"""
Repository package for Family Tree application.

This package implements the Repository Pattern for Firestore data access,
providing a clean abstraction layer between business logic and data persistence.

All repositories inherit from BaseRepository which provides:
- Common CRUD operations
- Firestore-specific functionality (subcollections, batches, transactions)
- Automatic timestamp management
- Consistent error handling
- Validation and logging
"""

__all__ = [
    "BaseRepository",
    "UserRepository", 
    "FamilyTreeRepository",
    "PersonRepository",
    "RelationshipRepository", 
    "FileRepository"
]