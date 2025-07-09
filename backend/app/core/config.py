# backend/app/core/config.py

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """
    Application settings for Family Tree API.
    Clean Firestore-based configuration with no legacy SQL dependencies.
    """
    
    # ================================================================
    # GOOGLE CLOUD / FIREBASE CONFIGURATION
    # ================================================================
    
    # Firebase Project Settings
    GOOGLE_CLOUD_PROJECT: str = "family-tree-app"
    FIREBASE_CREDENTIALS_PATH: str = ""  # Path to service account JSON (optional for local dev)
    
    # Firestore Settings
    FIRESTORE_COLLECTION_PREFIX: str = ""  # For testing isolation (e.g., "test_")
    
    # Google Cloud Storage Settings
    GCS_BUCKET_NAME: str = "family-tree-app-files"
    
    # ================================================================
    # APPLICATION SETTINGS
    # ================================================================
    
    # Application Metadata
    PROJECT_NAME: str = "Family Tree API"
    VERSION: str = "2.0.0"  # Major version bump for Firestore rewrite
    DEBUG: bool = True
    
    # Security Settings (still needed for custom JWT operations if any)
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ================================================================
    # CORS CONFIGURATION
    # ================================================================
    
    # CORS Origins (comma-separated string)
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert the comma-separated string to a list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # ================================================================
    # FILE UPLOAD CONFIGURATION
    # ================================================================
    
    # File Upload Limits
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Allowed File Types (comma-separated string)
    ALLOWED_FILE_TYPES: str = (
        "image/jpeg,image/png,image/gif,image/webp,"
        "application/pdf,text/plain,"
        "video/mp4,video/avi,video/mov,"
        "audio/mpeg,audio/wav"
    )
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert the comma-separated string to a list"""
        return [file_type.strip() for file_type in self.ALLOWED_FILE_TYPES.split(",")]
    
    # File Type Categories for Frontend
    @property
    def file_type_categories(self) -> dict:
        """Organize file types by category for frontend use"""
        return {
            "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
            "document": ["application/pdf", "text/plain"],
            "video": ["video/mp4", "video/avi", "video/mov"], 
            "audio": ["audio/mpeg", "audio/wav"]
        }
    
    # ================================================================
    # ASTROLOGY FEATURE CONFIGURATION
    # ================================================================
    
    # Zodiac Signs for Validation
    WESTERN_ZODIAC_SIGNS: List[str] = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]
    
    CHINESE_ZODIAC_SIGNS: List[str] = [
        "rat", "ox", "tiger", "rabbit", "dragon", "snake",
        "horse", "goat", "monkey", "rooster", "dog", "pig"
    ]
    
    # ================================================================
    # LOGGING CONFIGURATION
    # ================================================================
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ================================================================
    # DEVELOPMENT / TESTING SETTINGS
    # ================================================================
    
    # Testing
    TESTING: bool = False
    TEST_DATABASE_PREFIX: str = "test_"
    
    # Development Features
    ENABLE_API_DOCS: bool = True
    ENABLE_CORS: bool = True
    
    # ================================================================
    # RATE LIMITING (Future Implementation)
    # ================================================================
    
    # API Rate Limits (requests per minute)
    API_RATE_LIMIT_PER_MINUTE: int = 100
    FILE_UPLOAD_RATE_LIMIT_PER_MINUTE: int = 10
    
    # ================================================================
    # CONFIGURATION VALIDATION
    # ================================================================
    
    def validate_configuration(self) -> bool:
        """
        Validate that required configuration is present.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        # Validate Google Cloud Project
        if not self.GOOGLE_CLOUD_PROJECT:
            raise ValueError("GOOGLE_CLOUD_PROJECT is required")
        
        # Validate file size limits
        if self.MAX_FILE_SIZE <= 0:
            raise ValueError("MAX_FILE_SIZE must be positive")
        
        # Validate that we have some allowed file types
        if not self.allowed_file_types_list:
            raise ValueError("At least one file type must be allowed")
        
        # Validate secret key in production
        if not self.DEBUG and self.SECRET_KEY == "your-secret-key-change-this-in-production":
            raise ValueError("SECRET_KEY must be changed in production")
        
        return True
    
    # ================================================================
    # PYDANTIC CONFIGURATION
    # ================================================================
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'
        
        # Allow extra fields for future extensibility
        extra = "ignore"


# Create settings instance
settings = Settings()

# Validate configuration on import
try:
    settings.validate_configuration()
except ValueError as e:
    print(f"Configuration validation failed: {e}")
    # In production, you might want to exit here
    # For development, we'll continue with a warning
    if not settings.DEBUG:
        raise