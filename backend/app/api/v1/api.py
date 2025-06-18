from fastapi import APIRouter

from app.api.v1.endpoints import family_trees, people, relationships, files

api_router = APIRouter()

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