# backend/app/core/firestore.py - Google Cloud Version

import os
import logging
from typing import Optional
from google.cloud import firestore
from google.cloud.firestore import Client as FirestoreClient
from google.cloud import exceptions as gcp_exceptions
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

from app.core.config import settings

logger = logging.getLogger(__name__)

class FirestoreManager:
    """
    Singleton manager for Google Cloud Firestore client.
    Uses Google Cloud Firestore directly (no Firebase Admin SDK).
    Handles initialization, connection testing, and provides a clean interface
    for Firestore operations throughout the application.
    """
    
    _instance: Optional['FirestoreManager'] = None
    _firestore_client: Optional[FirestoreClient] = None
    _project_id: Optional[str] = None
    
    def __new__(cls) -> 'FirestoreManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Google Cloud Firestore only once."""
        if self._firestore_client is None:
            self._initialize_firestore()
    
    def _initialize_firestore(self) -> None:
        """
        Initialize Google Cloud Firestore client with appropriate credentials.
        Supports service account files, environment variables, and Application Default Credentials.
        """
        try:
            logger.info("Initializing Google Cloud Firestore client...")
            
            # Method 1: Service account key file (for local development)
            service_account_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '')
            if service_account_path and os.path.exists(service_account_path):
                logger.info(f"Using service account file: {service_account_path}")
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
            
            # Method 2: Environment variable GOOGLE_APPLICATION_CREDENTIALS
            elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                logger.info(f"Using GOOGLE_APPLICATION_CREDENTIALS: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
            
            # Method 3: Application Default Credentials (for Cloud deployment or gcloud auth)
            else:
                logger.info("Using Application Default Credentials")
            
            # Initialize Firestore client
            # This will automatically use credentials in this order:
            # 1. GOOGLE_APPLICATION_CREDENTIALS environment variable
            # 2. User credentials from gcloud auth application-default login
            # 3. Service account attached to Cloud resource (Cloud Run, GCE, etc.)
            
            self._firestore_client = firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            self._project_id = settings.GOOGLE_CLOUD_PROJECT
            
            logger.info(f"Google Cloud Firestore client initialized successfully for project: {self._project_id}")
            
        except DefaultCredentialsError as e:
            logger.error(f"Authentication failed: {e}")
            logger.error("Solutions:")
            logger.error("1. Download service account key and set FIREBASE_CREDENTIALS_PATH in .env")
            logger.error("2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            logger.error("3. Run 'gcloud auth application-default login'")
            raise RuntimeError(f"Google Cloud authentication failed: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Firestore: {e}")
            raise RuntimeError(f"Firestore initialization failed: {e}")
    
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
            
            logger.info("Google Cloud Firestore connection test successful")
            return True
            
        except gcp_exceptions.PermissionDenied:
            # This is actually expected - we don't have read permissions on this collection
            # But it means Firestore is reachable
            logger.info("Google Cloud Firestore connection test successful (permission denied expected)")
            return True
            
        except Exception as e:
            logger.error(f"Google Cloud Firestore connection test failed: {e}")
            return False
    
    def get_project_id(self) -> str:
        """Get the current Google Cloud project ID."""
        return self._project_id or settings.GOOGLE_CLOUD_PROJECT
    
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