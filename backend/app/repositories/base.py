# backend/app/repositories/base.py

import logging
import uuid
from abc import ABC
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from google.cloud import firestore
from google.cloud.firestore import DocumentReference, CollectionReference, Transaction, WriteBatch
from google.cloud import exceptions as gcp_exceptions

from app.core.firestore import get_firestore_client, firestore_manager

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class DocumentNotFoundError(RepositoryError):
    """Raised when a document is not found."""
    pass


class ValidationError(RepositoryError):
    """Raised when data validation fails."""
    pass


class PermissionError(RepositoryError):
    """Raised when access is denied."""
    pass


class BaseRepository(ABC):
    """
    Abstract base repository providing common Firestore operations.
    
    This class abstracts Firestore complexity and provides a consistent interface
    for all entity repositories. It handles both main collections and subcollections,
    automatic timestamp management, validation, error handling, and batch operations.
    
    Attributes:
        collection_name: The base collection name (e.g., 'users', 'family_trees')
        firestore_client: Firestore client instance
        
    Usage:
        # For main collections
        class UserRepository(BaseRepository):
            def __init__(self, firestore_client):
                super().__init__(firestore_client, "users")
        
        # For subcollections
        class PersonRepository(BaseRepository):
            def __init__(self, firestore_client):
                super().__init__(firestore_client, "people")
                
            async def get_by_family_tree(self, family_tree_id: str):
                collection_ref = self.get_subcollection_ref("family_trees", family_tree_id, "people")
                return await self.query([], collection_ref=collection_ref)
    """
    
    def __init__(self, firestore_client: firestore.Client, collection_name: str):
        """
        Initialize the repository.
        
        Args:
            firestore_client: Firestore client instance
            collection_name: Name of the Firestore collection
        """
        self.firestore_client = firestore_client
        self.collection_name = collection_name
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # ================================================================
    # COLLECTION REFERENCE HELPERS
    # ================================================================
    
    def get_collection_ref(self) -> CollectionReference:
        """
        Get the main collection reference.
        
        Returns:
            Firestore collection reference
        """
        return firestore_manager.collection(self.collection_name)
    
    def get_subcollection_ref(self, parent_collection: str, parent_id: str, subcollection: str) -> CollectionReference:
        """
        Get a subcollection reference.
        
        Args:
            parent_collection: Parent collection name (e.g., 'family_trees')
            parent_id: Parent document ID
            subcollection: Subcollection name (e.g., 'people', 'relationships')
            
        Returns:
            Firestore subcollection reference
        """
        return firestore_manager.subcollection(parent_collection, parent_id, subcollection)
    
    def get_document_ref(self, doc_id: str, collection_ref: Optional[CollectionReference] = None) -> DocumentReference:
        """
        Get a document reference.
        
        Args:
            doc_id: Document ID
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            Firestore document reference
        """
        if collection_ref is None:
            collection_ref = self.get_collection_ref()
        return collection_ref.document(doc_id)
    
    # ================================================================
    # CORE CRUD OPERATIONS
    # ================================================================
    
    async def create(self, 
                    data: Dict[str, Any], 
                    doc_id: Optional[str] = None,
                    collection_ref: Optional[CollectionReference] = None) -> Dict[str, Any]:
        """
        Create a new document.
        
        Args:
            data: Document data to create
            doc_id: Optional document ID (auto-generated if None)
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            Created document data with ID and timestamps
            
        Raises:
            ValidationError: If data validation fails
            RepositoryError: If creation fails
        """
        try:
            # Validate data
            validated_data = self._validate_create_data(data)
            
            # Add timestamps
            document_data = self._add_timestamps(validated_data, is_update=False)
            
            # Get collection reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            # Generate ID if not provided
            if doc_id is None:
                doc_id = str(uuid.uuid4())
            
            # Create document
            doc_ref = collection_ref.document(doc_id)
            await doc_ref.set(document_data)
            
            # Return created document with ID
            result = {**document_data, "id": doc_id}
            
            self.logger.info(f"Created document {doc_id} in {collection_ref.path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create document: {e}")
            raise self._handle_firestore_error(e)
    
    async def get_by_id(self, 
                       doc_id: str,
                       collection_ref: Optional[CollectionReference] = None) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            Document data with ID, or None if not found
        """
        try:
            # Get document reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            doc_ref = collection_ref.document(doc_id)
            doc_snapshot = await doc_ref.get()
            
            if not doc_snapshot.exists:
                self.logger.debug(f"Document {doc_id} not found in {collection_ref.path}")
                return None
            
            # Return document data with ID
            data = doc_snapshot.to_dict()
            data["id"] = doc_id
            
            self.logger.debug(f"Retrieved document {doc_id} from {collection_ref.path}")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to get document {doc_id}: {e}")
            raise self._handle_firestore_error(e)
    
    async def update(self, 
                    doc_id: str,
                    data: Dict[str, Any],
                    collection_ref: Optional[CollectionReference] = None) -> Dict[str, Any]:
        """
        Update a document.
        
        Args:
            doc_id: Document ID
            data: Data to update
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            Updated document data
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            ValidationError: If data validation fails
            RepositoryError: If update fails
        """
        try:
            # Validate data
            validated_data = self._validate_update_data(data)
            
            # Add update timestamp
            update_data = self._add_timestamps(validated_data, is_update=True)
            
            # Get document reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            doc_ref = collection_ref.document(doc_id)
            
            # Check if document exists
            if not (await doc_ref.get()).exists:
                raise DocumentNotFoundError(f"Document {doc_id} not found")
            
            # Update document
            await doc_ref.update(update_data)
            
            # Return updated document
            updated_doc = await self.get_by_id(doc_id, collection_ref)
            
            self.logger.info(f"Updated document {doc_id} in {collection_ref.path}")
            return updated_doc
            
        except DocumentNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update document {doc_id}: {e}")
            raise self._handle_firestore_error(e)
    
    async def delete(self, 
                    doc_id: str,
                    collection_ref: Optional[CollectionReference] = None) -> bool:
        """
        Delete a document.
        
        Args:
            doc_id: Document ID
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            True if deleted successfully
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            RepositoryError: If deletion fails
        """
        try:
            # Get document reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            doc_ref = collection_ref.document(doc_id)
            
            # Check if document exists
            if not (await doc_ref.get()).exists:
                raise DocumentNotFoundError(f"Document {doc_id} not found")
            
            # Delete document
            await doc_ref.delete()
            
            self.logger.info(f"Deleted document {doc_id} from {collection_ref.path}")
            return True
            
        except DocumentNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete document {doc_id}: {e}")
            raise self._handle_firestore_error(e)
    
    # ================================================================
    # QUERY OPERATIONS
    # ================================================================
    
    async def query(self,
                   filters: List[Tuple[str, str, Any]] = None,
                   order_by: Optional[str] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None,
                   collection_ref: Optional[CollectionReference] = None) -> List[Dict[str, Any]]:
        """
        Query documents with filters and ordering.
        
        Args:
            filters: List of filter tuples (field, operator, value)
            order_by: Field to order by
            limit: Maximum number of results
            offset: Number of results to skip
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            List of document data with IDs
            
        Example:
            # Query active relationships for a person
            filters = [
                ("fromPersonId", "==", person_id),
                ("isActive", "==", True)
            ]
            results = await repo.query(filters, order_by="createdAt", limit=10)
        """
        try:
            # Get collection reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            # Build query
            query = collection_ref
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply offset
            if offset:
                query = query.offset(offset)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            
            # Convert to list with IDs
            results = []
            async for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)
            
            self.logger.debug(f"Query returned {len(results)} documents from {collection_ref.path}")
            return results
            
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise self._handle_firestore_error(e)
    
    async def count(self,
                   filters: List[Tuple[str, str, Any]] = None,
                   collection_ref: Optional[CollectionReference] = None) -> int:
        """
        Count documents matching filters.
        
        Args:
            filters: List of filter tuples (field, operator, value)
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            Count of matching documents
        """
        try:
            # Get collection reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            # Build query
            query = collection_ref
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Get count
            count_query = query.count()
            result = await count_query.get()
            
            count = result[0][0].value if result else 0
            
            self.logger.debug(f"Count query returned {count} documents from {collection_ref.path}")
            return count
            
        except Exception as e:
            self.logger.error(f"Count query failed: {e}")
            raise self._handle_firestore_error(e)
    
    # ================================================================
    # BATCH OPERATIONS
    # ================================================================
    
    async def batch_create(self,
                          items: List[Dict[str, Any]],
                          collection_ref: Optional[CollectionReference] = None) -> List[Dict[str, Any]]:
        """
        Create multiple documents in a batch operation.
        
        Args:
            items: List of document data to create
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            List of created documents with IDs
            
        Raises:
            ValidationError: If any data validation fails
            RepositoryError: If batch operation fails
        """
        try:
            if not items:
                return []
            
            # Get collection reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            # Prepare batch
            batch = firestore_manager.batch()
            created_items = []
            
            for item_data in items:
                # Validate and prepare data
                validated_data = self._validate_create_data(item_data)
                document_data = self._add_timestamps(validated_data, is_update=False)
                
                # Generate ID
                doc_id = str(uuid.uuid4())
                doc_ref = collection_ref.document(doc_id)
                
                # Add to batch
                batch.set(doc_ref, document_data)
                
                # Add to results
                created_items.append({**document_data, "id": doc_id})
            
            # Commit batch
            await batch.commit()
            
            self.logger.info(f"Batch created {len(created_items)} documents in {collection_ref.path}")
            return created_items
            
        except Exception as e:
            self.logger.error(f"Batch create failed: {e}")
            raise self._handle_firestore_error(e)
    
    async def batch_update(self,
                          updates: List[Tuple[str, Dict[str, Any]]],
                          collection_ref: Optional[CollectionReference] = None) -> bool:
        """
        Update multiple documents in a batch operation.
        
        Args:
            updates: List of (doc_id, update_data) tuples
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            True if batch update succeeded
            
        Raises:
            ValidationError: If any data validation fails
            RepositoryError: If batch operation fails
        """
        try:
            if not updates:
                return True
            
            # Get collection reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            # Prepare batch
            batch = firestore_manager.batch()
            
            for doc_id, update_data in updates:
                # Validate and prepare data
                validated_data = self._validate_update_data(update_data)
                document_data = self._add_timestamps(validated_data, is_update=True)
                
                # Add to batch
                doc_ref = collection_ref.document(doc_id)
                batch.update(doc_ref, document_data)
            
            # Commit batch
            await batch.commit()
            
            self.logger.info(f"Batch updated {len(updates)} documents in {collection_ref.path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Batch update failed: {e}")
            raise self._handle_firestore_error(e)
    
    async def batch_delete(self,
                          doc_ids: List[str],
                          collection_ref: Optional[CollectionReference] = None) -> bool:
        """
        Delete multiple documents in a batch operation.
        
        Args:
            doc_ids: List of document IDs to delete
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            True if batch delete succeeded
            
        Raises:
            RepositoryError: If batch operation fails
        """
        try:
            if not doc_ids:
                return True
            
            # Get collection reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            # Prepare batch
            batch = firestore_manager.batch()
            
            for doc_id in doc_ids:
                doc_ref = collection_ref.document(doc_id)
                batch.delete(doc_ref)
            
            # Commit batch
            await batch.commit()
            
            self.logger.info(f"Batch deleted {len(doc_ids)} documents from {collection_ref.path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Batch delete failed: {e}")
            raise self._handle_firestore_error(e)
    
    # ================================================================
    # TRANSACTION OPERATIONS
    # ================================================================
    
    async def transaction_update(self,
                                transaction: Transaction,
                                doc_id: str,
                                update_data: Dict[str, Any],
                                collection_ref: Optional[CollectionReference] = None) -> Dict[str, Any]:
        """
        Update a document within a transaction.
        
        Args:
            transaction: Firestore transaction
            doc_id: Document ID
            update_data: Data to update
            collection_ref: Optional collection reference (defaults to main collection)
            
        Returns:
            Updated document data
        """
        # Get collection reference
        if collection_ref is None:
            collection_ref = self.get_collection_ref()
        
        # Validate and prepare data
        validated_data = self._validate_update_data(update_data)
        document_data = self._add_timestamps(validated_data, is_update=True)
        
        # Update in transaction
        doc_ref = collection_ref.document(doc_id)
        transaction.update(doc_ref, document_data)
        
        # Note: In a transaction, we can't immediately get the updated document
        # The caller should handle this after the transaction commits
        return {**document_data, "id": doc_id}
    
    # ================================================================
    # UTILITY METHODS
    # ================================================================
    
    def _add_timestamps(self, data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """
        Add timestamp fields to document data.
        
        Args:
            data: Document data
            is_update: Whether this is an update operation
            
        Returns:
            Document data with timestamps
        """
        result = data.copy()
        current_time = datetime.now(timezone.utc)
        
        if not is_update:
            result["createdAt"] = current_time
        
        result["updatedAt"] = current_time
        
        return result
    
    def _validate_create_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data for create operations.
        Override in subclasses for entity-specific validation.
        
        Args:
            data: Document data to validate
            
        Returns:
            Validated document data
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        if not data:
            raise ValidationError("Data cannot be empty")
        
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    def _validate_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data for update operations.
        Override in subclasses for entity-specific validation.
        
        Args:
            data: Document data to validate
            
        Returns:
            Validated document data
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        if not data:
            raise ValidationError("Update data cannot be empty")
        
        # Remove None values and system fields
        excluded_fields = {"id", "createdAt", "updatedAt"}
        return {k: v for k, v in data.items() 
                if v is not None and k not in excluded_fields}
    
    def _handle_firestore_error(self, error: Exception) -> RepositoryError:
        """
        Convert Firestore exceptions to repository exceptions.
        
        Args:
            error: Original Firestore exception
            
        Returns:
            Appropriate RepositoryError subclass
        """
        if isinstance(error, gcp_exceptions.NotFound):
            return DocumentNotFoundError(f"Document not found: {error}")
        elif isinstance(error, gcp_exceptions.PermissionDenied):
            return PermissionError(f"Access denied: {error}")
        elif isinstance(error, gcp_exceptions.InvalidArgument):
            return ValidationError(f"Invalid data: {error}")
        elif isinstance(error, (ValidationError, DocumentNotFoundError, PermissionError)):
            return error
        else:
            return RepositoryError(f"Repository operation failed: {error}")
    
    # ================================================================
    # CASCADE DELETE UTILITIES
    # ================================================================
    
    async def delete_subcollections(self,
                                   doc_id: str,
                                   subcollection_names: List[str],
                                   collection_ref: Optional[CollectionReference] = None) -> bool:
        """
        Delete all documents in specified subcollections.
        Useful for cascade deletes.
        
        Args:
            doc_id: Parent document ID
            subcollection_names: List of subcollection names to delete
            collection_ref: Optional parent collection reference
            
        Returns:
            True if successful
        """
        try:
            # Get parent document reference
            if collection_ref is None:
                collection_ref = self.get_collection_ref()
            
            parent_doc_ref = collection_ref.document(doc_id)
            
            # Delete each subcollection
            for subcollection_name in subcollection_names:
                subcollection_ref = parent_doc_ref.collection(subcollection_name)
                
                # Get all documents in subcollection
                docs = subcollection_ref.stream()
                doc_ids = [doc.id async for doc in docs]
                
                # Batch delete subcollection documents
                if doc_ids:
                    await self.batch_delete(doc_ids, subcollection_ref)
            
            self.logger.info(f"Deleted subcollections {subcollection_names} for document {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete subcollections: {e}")
            raise self._handle_firestore_error(e)