from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get database session
def get_database_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database utility functions
def create_database():
    """Create all database tables"""
    from app.models.database import Base
    Base.metadata.create_all(bind=engine)

def drop_database():
    """Drop all database tables"""
    from app.models.database import Base
    Base.metadata.drop_all(bind=engine)