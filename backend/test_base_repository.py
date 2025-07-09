# backend/test_base_repository.py

"""
Test script for BaseRepository implementation.
Run this to validate Firestore connection and repository operations.

Usage:
    python test_base_repository.py
"""

import asyncio
import logging
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.firestore import firestore_manager, check_firestore_health
from app.repositories.base import BaseRepository, DocumentNotFoundError, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRepository(BaseRepository):
    """Test repository for validation."""
    
    def __init__(self, firestore_client):
        super().__init__(firestore_client, "test_documents")


async def test_firestore_connection():
    """Test basic Firestore connectivity."""
    logger.info("Testing Firestore connection...")
    
    health = await check_firestore_health()
    logger.info(f"Firestore health: {health}")
    
    if health["status"] != "healthy":
        logger.error("Firestore connection failed!")
        return False
    
    logger.info("✅ Firestore connection successful")
    return True


async def test_crud_operations():
    """Test basic CRUD operations."""
    logger.info("Testing CRUD operations...")
    
    # Initialize test repository
    repo = TestRepository(firestore_manager.db)
    
    try:
        # Test Create
        logger.info("Testing CREATE operation...")
        test_data = {
            "name": "Test Document",
            "description": "This is a test document",
            "value": 42
        }
        
        created_doc = await repo.create(test_data)
        doc_id = created_doc["id"]
        logger.info(f"✅ Created document: {doc_id}")
        
        # Verify timestamps were added
        assert "createdAt" in created_doc
        assert "updatedAt" in created_doc
        logger.info("✅ Timestamps added correctly")
        
        # Test Read
        logger.info("Testing READ operation...")
        retrieved_doc = await repo.get_by_id(doc_id)
        assert retrieved_doc is not None
        assert retrieved_doc["name"] == test_data["name"]
        logger.info("✅ Document retrieved correctly")
        
        # Test Update
        logger.info("Testing UPDATE operation...")
        update_data = {"description": "Updated description", "value": 84}
        updated_doc = await repo.update(doc_id, update_data)
        assert updated_doc["description"] == "Updated description"
        assert updated_doc["value"] == 84
        assert updated_doc["name"] == test_data["name"]  # Unchanged field preserved
        logger.info("✅ Document updated correctly")
        
        # Test Query
        logger.info("Testing QUERY operation...")
        filters = [("name", "==", "Test Document")]
        query_results = await repo.query(filters)
        assert len(query_results) >= 1
        assert any(doc["id"] == doc_id for doc in query_results)
        logger.info("✅ Query executed correctly")
        
        # Test Count
        logger.info("Testing COUNT operation...")
        count = await repo.count(filters)
        assert count >= 1
        logger.info(f"✅ Count returned: {count}")
        
        # Test Delete
        logger.info("Testing DELETE operation...")
        deleted = await repo.delete(doc_id)
        assert deleted is True
        logger.info("✅ Document deleted correctly")
        
        # Verify deletion
        deleted_doc = await repo.get_by_id(doc_id)
        assert deleted_doc is None
        logger.info("✅ Deletion verified")
        
        logger.info("✅ All CRUD operations successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ CRUD test failed: {e}")
        return False


async def test_batch_operations():
    """Test batch operations."""
    logger.info("Testing batch operations...")
    
    repo = TestRepository(firestore_manager.db)
    
    try:
        # Test Batch Create
        logger.info("Testing BATCH CREATE...")
        batch_items = [
            {"name": f"Batch Document {i}", "batch_id": i}
            for i in range(3)
        ]
        
        created_docs = await repo.batch_create(batch_items)
        assert len(created_docs) == 3
        doc_ids = [doc["id"] for doc in created_docs]
        logger.info(f"✅ Batch created {len(created_docs)} documents")
        
        # Test Batch Update
        logger.info("Testing BATCH UPDATE...")
        updates = [(doc_id, {"updated": True}) for doc_id in doc_ids]
        updated = await repo.batch_update(updates)
        assert updated is True
        logger.info("✅ Batch update successful")
        
        # Verify updates
        for doc_id in doc_ids:
            doc = await repo.get_by_id(doc_id)
            assert doc["updated"] is True
        logger.info("✅ Batch updates verified")
        
        # Test Batch Delete
        logger.info("Testing BATCH DELETE...")
        deleted = await repo.batch_delete(doc_ids)
        assert deleted is True
        logger.info("✅ Batch delete successful")
        
        # Verify deletions
        for doc_id in doc_ids:
            doc = await repo.get_by_id(doc_id)
            assert doc is None
        logger.info("✅ Batch deletions verified")
        
        logger.info("✅ All batch operations successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Batch test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling scenarios."""
    logger.info("Testing error handling...")
    
    repo = TestRepository(firestore_manager.db)
    
    try:
        # Test document not found
        logger.info("Testing DocumentNotFoundError...")
        try:
            await repo.get_by_id("nonexistent_id")
            # Should return None, not raise exception
            logger.info("✅ Non-existent document returned None")
        except Exception as e:
            logger.error(f"❌ Unexpected error for non-existent document: {e}")
            return False
        
        # Test update non-existent document
        try:
            await repo.update("nonexistent_id", {"test": "data"})
            logger.error("❌ Update should have failed for non-existent document")
            return False
        except DocumentNotFoundError:
            logger.info("✅ DocumentNotFoundError raised correctly")
        
        # Test delete non-existent document
        try:
            await repo.delete("nonexistent_id")
            logger.error("❌ Delete should have failed for non-existent document")
            return False
        except DocumentNotFoundError:
            logger.info("✅ DocumentNotFoundError raised correctly")
        
        # Test validation errors
        try:
            await repo.create({})  # Empty data
            logger.error("❌ Create should have failed for empty data")
            return False
        except ValidationError:
            logger.info("✅ ValidationError raised correctly for empty data")
        
        try:
            await repo.create("not a dict")  # Invalid data type
            logger.error("❌ Create should have failed for invalid data type")
            return False
        except ValidationError:
            logger.info("✅ ValidationError raised correctly for invalid data type")
        
        logger.info("✅ All error handling tests successful!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {e}")
        return False


async def cleanup_test_documents():
    """Clean up any remaining test documents."""
    logger.info("Cleaning up test documents...")
    
    repo = TestRepository(firestore_manager.db)
    
    try:
        # Query all test documents
        test_docs = await repo.query()
        
        if test_docs:
            doc_ids = [doc["id"] for doc in test_docs]
            await repo.batch_delete(doc_ids)
            logger.info(f"✅ Cleaned up {len(doc_ids)} test documents")
        else:
            logger.info("✅ No test documents to clean up")
    
    except Exception as e:
        logger.warning(f"Cleanup failed (non-critical): {e}")


async def main():
    """Run all tests."""
    logger.info("🚀 Starting BaseRepository validation tests...")
    
    tests = [
        ("Firestore Connection", test_firestore_connection),
        ("CRUD Operations", test_crud_operations),
        ("Batch Operations", test_batch_operations),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if await test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    # Cleanup
    await cleanup_test_documents()
    
    # Results
    logger.info(f"\n{'='*50}")
    logger.info(f"TEST RESULTS: {passed}/{total} tests passed")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 All tests passed! BaseRepository is ready for use.")
        return True
    else:
        logger.error("❌ Some tests failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)