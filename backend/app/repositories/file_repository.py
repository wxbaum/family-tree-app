"""
File Repository for managing file metadata.

Phase 2.5 Implementation Target
"""

from typing import List, Optional, Dict, Any
from google.cloud import firestore

from .base import BaseRepository


class FileRepository(BaseRepository):
    """
    Repository for managing file metadata.
    Uses subcollections: /family_trees/{id}/files
    Actual files stored in Google Cloud Storage.
    """
    
    def __init__(self, firestore_client: firestore.Client):
        super().__init__(firestore_client, "files")
    
    # TODO: Implement in Phase 2.5
    async def get_files_by_person(self, family_tree_id: str, person_id: str, file_type_filter: str = None) -> List[Dict[str, Any]]:
        """Get person's files."""
        pass
    
    async def get_files_by_family_tree(self, family_tree_id: str, file_type_filter: str = None, limit: int = None, offset: int = None) -> List[Dict[str, Any]]:
        """Get tree files with pagination."""
        pass
    
    async def search_files(self, family_tree_id: str, search_term: str) -> List[Dict[str, Any]]:
        """Search by filename/description."""
        pass
    
    async def get_file_statistics(self, family_tree_id: str) -> Dict[str, Any]:
        """File size and count stats."""
        pass