# backend/app/api/v1/api.py

from fastapi import APIRouter

from app.api.v1.endpoints import family_trees, people, relationships, files

api_router = APIRouter()

# Include all endpoint routers with proper prefixes and tags
api_router.include_router(
    family_trees.router, 
    prefix="/family-trees", 
    tags=["family-trees"]
)

api_router.include_router(
    people.router, 
    prefix="/people", 
    tags=["people"]
)

api_router.include_router(
    relationships.router, 
    prefix="/relationships", 
    tags=["relationships"]
)

api_router.include_router(
    files.router, 
    prefix="/files", 
    tags=["files"]
)

# Health check endpoint for the API
@api_router.get("/health")
async def api_health_check():
    """Health check endpoint for the API v1."""
    return {
        "status": "healthy",
        "version": "v1",
        "endpoints": {
            "family_trees": "/api/v1/family-trees",
            "people": "/api/v1/people", 
            "relationships": "/api/v1/relationships",
            "files": "/api/v1/files"
        }
    }