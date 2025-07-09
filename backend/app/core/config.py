from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://family_tree_user:family_tree_password@localhost:5432/family_tree_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS - using string that will be split, not a List type
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    # Oracle Object Storage
    ORACLE_NAMESPACE: str = ""
    ORACLE_BUCKET_NAME: str = "family-tree-files"
    ORACLE_ACCESS_KEY: str = ""
    ORACLE_SECRET_KEY: str = ""
    ORACLE_REGION: str = "us-ashburn-1"
    
    # Application
    DEBUG: bool = True
    PROJECT_NAME: str = "Family Tree API"
    VERSION: str = "1.0.0"
    
    # File upload settings - using string that will be split, not List type
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,image/gif,image/webp,application/pdf"
    
    # File storage settings
    FILE_STORAGE_TYPE: str = "local"
    UPLOAD_PATH: str = "uploads"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert the comma-separated string to a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert the comma-separated string to a list"""
        return [file_type.strip() for file_type in self.ALLOWED_FILE_TYPES.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()