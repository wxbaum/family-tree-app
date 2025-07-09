# backend/app/core/firestore.py

import os
import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore import Client as FirestoreClient
from google.cloud import exceptions as gcp_exceptions

from app.core.config import settings

logger = logging.getLogger(__name__)

class FirestoreManager:
    """
    Singleton manager for Firebase Admin SDK and Firestore client.
    Handles initialization, connection testing, and provides a clean interface
    for Firestore operations throughout the application.
    """
    
    _instance: Optional['FirestoreManager'] = None
    _firestore_client: Optional[FirestoreClient] = None
    _firebase_app: Optional[firebase_admin.App] = None
    
    def __new__(cls) -> 'FirestoreManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase only once."""
        if self._firestore_client is None:
            self._initialize_firebase()
    
    def _initialize_firebase(self) -> None:
        """
        Initialize Firebase Admin SDK with appropriate credentials.
        Supports both service account files and application default credentials.
        """
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                logger.info("Initializing Firebase Admin SDK...")
                
                # Try service account file first (for local development)
                if (hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and 
                    settings.FIREBASE_CREDENTIALS_PATH and 
                    os.path.exists(settings.FIREBASE_CREDENTIALS_PATH)):
                    
                    logger.info(f"Using service account file: {settings.FIREBASE_CREDENTIALS_PATH}")
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    self._firebase_app = firebase_admin.initialize_app(cred, {
                        'projectId': settings.GOOGLE_CLOUD_PROJECT
                    })
                
                else:
                    # Use Application Default Credentials (for Cloud Run deployment)
                    logger.info("Using Application Default Credentials")
                    self._firebase_app = firebase_admin.initialize_app(options={
                        'projectId': settings.GOOGLE_CLOUD_PROJECT
                    })
                
                logger.info("Firebase Admin SDK initialized successfully")
            
            else:
                logger.info("Firebase Admin SDK already initialized")
                self._firebase_app = firebase_admin.get_app()
            
            # Initialize Firestore client
            self._firestore_client = firestore.client()
            logger.info("Firestore client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise RuntimeError(f"Firebase initialization failed: {e}")
    
    @property
    def db(self) -> FirestoreClient:
        """Get the Firestore client instance."""
        if self._firestore_client is None:
            raise RuntimeError("Firestore client not initialized")
        return self._firestore_client
    
    def collection(self, path: str) -> firestore.CollectionReference:
        """
        Get a collection reference with optional prefix for testing isolation.
        
        Args:
            path: Collection path (e.g., 'users', 'family_trees')
            
        Returns:
            Firestore collection reference
        """
        if hasattr(settings, 'FIRESTORE_COLLECTION_PREFIX') and settings.FIRESTORE_COLLECTION_PREFIX:
            full_path = f"{settings.FIRESTORE_COLLECTION_PREFIX}{path}"
        else:
            full_path = path
            
        return self._firestore_client.collection(full_path)
    
    def subcollection(self, parent_path: str, parent_id: str, subcollection_name: str) -> firestore.CollectionReference:
        """
        Get a subcollection reference with optional prefix.
        
        Args:
            parent_path: Parent collection path (e.g., 'family_trees')
            parent_id: Parent document ID
            subcollection_name: Subcollection name (e.g., 'people', 'relationships')
            
        Returns:
            Firestore subcollection reference
        """
        parent_collection = self.collection(parent_path)
        return parent_collection.document(parent_id).collection(subcollection_name)
    
    async def test_connection(self) -> bool:
        """
        Test Firestore connection by attempting a simple read operation.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to read from a test collection
            test_collection = self.collection('_connection_test')
            
            # This will fail gracefully if we don't have read permissions,
            # but will succeed if Firestore is accessible
            docs = test_collection.limit(1).stream()
            
            # Consume the iterator to actually make the request
            list(docs)
            
            logger.info("Firestore connection test successful")
            return True
            
        except gcp_exceptions.PermissionDenied:
            # This is actually expected - we don't have read permissions on this collection
            # But it means Firestore is reachable
            logger.info("Firestore connection test successful (permission denied expected)")
            return True
            
        except Exception as e:
            logger.error(f"Firestore connection test failed: {e}")
            return False
    
    def get_project_id(self) -> str:
        """Get the current Google Cloud project ID."""
        return settings.GOOGLE_CLOUD_PROJECT
    
    def batch(self) -> firestore.WriteBatch:
        """Create a new write batch for atomic operations."""
        return self._firestore_client.batch()
    
    def transaction(self) -> firestore.Transaction:
        """Create a new transaction for atomic read-write operations."""
        return self._firestore_client.transaction()


# Global singleton instance
firestore_manager = FirestoreManager()


# FastAPI dependency injection functions
async def get_firestore_client() -> FirestoreClient:
    """
    FastAPI dependency to inject Firestore client.
    
    Returns:
        Configured Firestore client instance
    """
    return firestore_manager.db


async def get_firestore_manager() -> FirestoreManager:
    """
    FastAPI dependency to inject Firestore manager.
    
    Returns:
        Firestore manager instance with helper methods
    """
    return firestore_manager


# Convenience functions for common operations
def get_collection(path: str) -> firestore.CollectionReference:
    """Convenience function to get a collection reference."""
    return firestore_manager.collection(path)


def get_subcollection(parent_path: str, parent_id: str, subcollection_name: str) -> firestore.CollectionReference:
    """Convenience function to get a subcollection reference."""
    return firestore_manager.subcollection(parent_path, parent_id, subcollection_name)


# Health check function
async def check_firestore_health() -> dict:
    """
    Health check function for monitoring Firestore connectivity.
    
    Returns:
        Health status dictionary
    """
    try:
        is_connected = await firestore_manager.test_connection()
        return {
            "service": "firestore",
            "status": "healthy" if is_connected else "unhealthy",
            "project_id": firestore_manager.get_project_id(),
            "details": "Connection successful" if is_connected else "Connection failed"
        }
    except Exception as e:
        return {
            "service": "firestore",
            "status": "unhealthy",
            "project_id": firestore_manager.get_project_id(),
            "details": f"Health check failed: {str(e)}"
        }