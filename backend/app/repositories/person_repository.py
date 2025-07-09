# backend/app/repositories/person_repository.py

"""
Person Repository for managing people within family trees.

Phase 2.3 Implementation Target  
"""

from typing import List, Optional, Dict, Any
from google.cloud import firestore

from .base import BaseRepository


class PersonRepository(BaseRepository):
    """
    Repository for managing people in family trees.
    Uses subcollections: /family_trees/{id}/people
    """
    
    def __init__(self, firestore_client: firestore.Client):
        super().__init__(firestore_client, "people")
    
    # TODO: Implement in Phase 2.3
    async def get_people_by_family_tree(self, family_tree_id: str, limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """List people in family tree with pagination."""
        pass
    
    async def search_people(self, family_tree_id: str, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search people by name."""
        pass
    
    async def get_people_count(self, family_tree_id: str) -> int:
        """Count people for statistics."""
        pass
    
    async def batch_create_people(self, family_tree_id: str, people_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk create people."""
        pass
