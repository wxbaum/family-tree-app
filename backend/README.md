# Family Tree API - Backend

A production-ready FastAPI backend for managing family trees with comprehensive relationship tracking, file management, and graph analytics.

## 🎯 Features

### ✅ **Core Functionality**
- **User Authentication** - JWT-based registration, login, and user management with FastAPI Users
- **Family Tree Management** - Complete CRUD operations with ownership validation and statistics
- **Person Management** - Comprehensive biographical data with relationship queries and age calculation
- **Advanced Relationships** - Graph-based relationship system with inference and path finding
- **File Management** - Production-ready file storage with local and cloud storage support
- **Graph Analytics** - React Flow compatible data export with relationship statistics
- **Search & Filtering** - Full-text search across people, family trees, and files
- **Bulk Operations** - Efficient handling of multiple operations with error handling

### 🏗️ **Architecture Highlights**
- **Async Throughout** - Full async/await patterns with AsyncSession for optimal performance
- **Service Layer** - Clean separation of business logic with comprehensive error handling
- **Graph Database** - Relationship modeling with generation tracking and bidirectional support
- **Pluggable Storage** - Abstract file storage interface supporting local and Oracle Object Storage
- **Comprehensive Validation** - Pydantic schemas with business rule enforcement
- **Production Security** - Proper authentication, authorization, and data validation

## 🛠 Technology Stack

- **FastAPI** - Modern Python web framework with automatic OpenAPI documentation
- **PostgreSQL** - Robust relational database with graph-like relationship modeling
- **SQLAlchemy 2.0** - Async ORM with modern Python syntax and optimized queries
- **FastAPI Users** - Complete authentication system with JWT tokens
- **Alembic** - Database migration management and version control
- **Pydantic V2** - Data validation, serialization, and type safety
- **Docker** - Containerized development and deployment ready

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/          # API route handlers
│   │   ├── family_trees.py        # Family tree CRUD with statistics
│   │   ├── people.py              # Person management with relationships  
│   │   ├── relationships.py       # Advanced relationship management
│   │   └── files.py               # File upload/download with validation
│   ├── core/                      # Core configuration and utilities
│   │   ├── auth.py                # Async authentication setup
│   │   ├── config.py              # Application settings and environment
│   │   └── database.py            # Async database configuration
│   ├── models/                    # Database models
│   │   └── database.py            # SQLAlchemy models with relationships
│   ├── schemas/                   # Pydantic schemas
│   │   └── schemas.py             # Request/response models with validation
│   ├── services/                  # Business logic layer (ALL ASYNC)
│   │   ├── family_tree_service.py # Family tree operations with analytics
│   │   ├── person_service.py      # Person CRUD with relationship queries
│   │   ├── relationship_service.py # Relationship management and inference
│   │   └── file_service.py        # File storage with pluggable backends
│   └── main.py                    # FastAPI application with async startup
├── alembic/                       # Database migrations
├── uploads/                       # Local file storage (development)
├── Dockerfile                     # Production container configuration
├── requirements.txt               # Python dependencies
├── docker-compose.yml             # Development environment
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Docker & Docker Compose (recommended)

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env with your configuration:
# - SECRET_KEY (use generated key above)
# - DATABASE_URL (PostgreSQL connection)
# - File storage settings (local or Oracle Object Storage)
```

### 2. Run with Docker (Recommended)
```bash
# From project root - starts PostgreSQL and API
docker-compose up --build

# API available at: http://localhost:8000
# API documentation: http://localhost:8000/docs
# Alternative docs: http://localhost:8000/redoc
```

### 3. Local Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 API Endpoints

### **Authentication**
- `POST /auth/register` - User registration
- `POST /auth/login` - User login with JWT token
- `GET /users/me` - Get current user profile

### **Family Trees** (`/api/v1/family-trees/`)
- `GET /` - List user's family trees (with pagination & search)
- `POST /` - Create new family tree
- `GET /{id}` - Get family tree details
- `PUT /{id}` - Update family tree
- `DELETE /{id}` - Delete family tree (cascading)
- `GET /{id}/graph` - Get React Flow compatible graph data
- `GET /{id}/statistics` - Get comprehensive statistics

### **People** (`/api/v1/people/`)
- `GET /family-tree/{id}` - List people in family tree (with pagination)
- `GET /family-tree/{id}/search` - Search people by name
- `POST /` - Create new person
- `GET /{id}` - Get person details
- `PUT /{id}` - Update person
- `DELETE /{id}` - Delete person (with relationships)
- `GET /{id}/relationships` - Get person's relationships
- `GET /{id}/ancestors` - Get ancestors (with generation limit)
- `GET /{id}/descendants` - Get descendants (with generation limit)
- `GET /{id}/siblings` - Get siblings
- `GET /{id}/age` - Calculate age as of specific date

### **Relationships** (`/api/v1/relationships/`)
- `POST /` - Create relationship with validation
- `GET /{id}` - Get relationship details
- `PUT /{id}` - Update relationship
- `DELETE /{id}` - Delete relationship (and reciprocals)
- `GET /family-tree/{id}` - Get all relationships in family tree
- `GET /family-tree/{id}/statistics` - Get relationship statistics
- `GET /path/{person1_id}/{person2_id}` - Find relationship path
- `GET /family-tree/{id}/infer` - Infer missing relationships
- `POST /validate` - Validate relationship before creation
- `POST /bulk` - Create multiple relationships

### **Files** (`/api/v1/files/`)
- `POST /upload/{person_id}` - Upload file for person
- `GET /person/{id}` - Get person's files (with type filtering)
- `GET /download/{file_id}` - Download file
- `GET /view/{file_id}` - View file inline
- `DELETE /{file_id}` - Delete file
- `GET /family-tree/{id}` - Get all files in family tree
- `GET /family-tree/{id}/statistics` - Get file usage statistics
- `GET /family-tree/{id}/search` - Search files by name/description
- `POST /bulk-upload/{person_id}` - Upload multiple files
- `GET /types` - Get supported file types and limits

## 🗄️ Database Schema

### **Core Tables**
- **users** - User accounts with subscription tiers
- **family_trees** - Family tree containers with metadata
- **people** - Individual family members with biographical data
- **relationships** - Graph edges with category and generation tracking
- **person_files** - File attachments with metadata and storage paths

### **Key Relationships**
- Users own multiple family trees
- Family trees contain multiple people
- People connected by typed relationships (family_line, partner, sibling, extended_family)
- People can have multiple file attachments
- Relationships support bidirectional and generational modeling

## ⚙️ Configuration

### **Environment Variables**
```bash
# Application
SECRET_KEY=your_secret_key_here
PROJECT_NAME="Family Tree API"
VERSION="1.0.0"
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/familytree

# File Storage
FILE_STORAGE_TYPE=local  # or 'oracle'
UPLOAD_PATH=uploads
MAX_FILE_SIZE=10485760   # 10MB
ALLOWED_FILE_TYPES=image/jpeg,image/png,application/pdf

# Oracle Object Storage (if using)
ORACLE_NAMESPACE=your_namespace
ORACLE_BUCKET=your_bucket
ORACLE_ACCESS_KEY=your_access_key
ORACLE_SECRET_KEY=your_secret_key
ORACLE_REGION=your_region
```

### **File Storage Options**

#### **Local Storage (Development)**
```python
# Automatic for development
FILE_STORAGE_TYPE=local
UPLOAD_PATH=uploads
```

#### **Oracle Object Storage (Production)**
```python
# For production deployment
FILE_STORAGE_TYPE=oracle
ORACLE_NAMESPACE=your_namespace
ORACLE_BUCKET=family-tree-files
# ... other Oracle settings
```

## 🧪 Testing

### **Run Tests**
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_people.py -v
```

### **API Testing**
```bash
# Test user registration
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "testpassword123"}'

# Test login
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=testpassword123"

# Test protected endpoint
curl -X GET "http://localhost:8000/api/v1/family-trees/" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🚀 Production Deployment

### **Docker Deployment**
```bash
# Build production image
docker build -t family-tree-api .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e SECRET_KEY=your_production_secret \
  family-tree-api
```

### **Database Migration**
```bash
# Generate migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### **Performance Optimization**
- **Connection Pooling**: Configured for high concurrency
- **Async Operations**: Non-blocking I/O throughout
- **Database Indexes**: Optimized queries for large datasets
- **File Storage**: Pluggable storage for scalability
- **Caching Headers**: Proper HTTP caching for static content

## 🔧 Development

### **Code Quality**
```bash
# Format code
black app/
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
```

### **Database Management**
```bash
# Create new migration
alembic revision -m "Add new feature"

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Update models"

# Check current migration status
alembic current

# View migration history
alembic history
```

## 📈 Monitoring & Logging

### **Health Checks**
- `GET /health` - Basic health check
- `GET /api/v1/health` - API health with version info
- Built-in FastAPI metrics and request logging

### **Error Handling**
- Comprehensive error responses with detail messages
- Automatic transaction rollback on failures
- File cleanup on failed operations
- Consistent HTTP status codes

## 🔒 Security Features

- **JWT Authentication** with secure token generation
- **Password Hashing** with bcrypt
- **Input Validation** with Pydantic schemas
- **SQL Injection Protection** with SQLAlchemy ORM
- **File Upload Validation** with type and size limits
- **CORS Configuration** for secure cross-origin requests
- **Rate Limiting** ready for production deployment

## 📝 API Documentation

The API provides comprehensive documentation:

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🎯 Production Ready

This backend is production-ready with:
- ✅ **Comprehensive async architecture**
- ✅ **Robust error handling and validation**
- ✅ **Scalable database design**
- ✅ **Complete test coverage**
- ✅ **Security best practices**
- ✅ **Performance optimization**
- ✅ **Production deployment configuration**

The API provides a solid foundation for building sophisticated family tree applications with advanced relationship modeling and file management capabilities.