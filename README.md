# Family Tree API - Backend

A modern FastAPI backend for managing family trees with user authentication, person management, and relationship tracking.

## 🎯 Features

### ✅ **Implemented**
- **User Authentication** - JWT-based registration, login, and user management
- **Family Tree Management** - CRUD operations for family trees with ownership validation
- **Person Management** - Add, edit, delete people with comprehensive biographical data
- **Relationship Support** - Database schema ready for family relationships (spouse, parent, child, adopted)
- **Graph Data Export** - Family tree data formatted for frontend visualization
- **File Storage Architecture** - Local file storage with pluggable interface for cloud storage
- **Async Database** - Full async SQLAlchemy with PostgreSQL
- **Data Validation** - Pydantic schemas with proper date handling
- **API Documentation** - Auto-generated OpenAPI/Swagger docs

### 🚧 **Ready for Implementation**
- **Relationship Creation API** - Backend endpoints exist, need frontend integration
- **File Upload/Download** - Service layer complete, endpoints ready
- **Cloud Storage** - Oracle Object Storage interface prepared

## 🛠 Technology Stack

- **FastAPI** - Modern Python web framework with automatic API docs
- **PostgreSQL** - Robust relational database with graph-like relationship modeling
- **SQLAlchemy 2.0** - Async ORM with modern Python syntax
- **FastAPI Users** - Complete authentication system with JWT
- **Alembic** - Database migration management
- **Pydantic** - Data validation and serialization
- **Docker** - Containerized development and deployment

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/          # API route handlers
│   │   ├── family_trees.py        # Family tree CRUD operations
│   │   ├── people.py              # Person management
│   │   ├── relationships.py       # Family relationship endpoints
│   │   └── files.py               # File upload/download (ready)
│   ├── core/                      # Core configuration and utilities
│   │   ├── auth.py                # Authentication setup
│   │   ├── config.py              # Application settings
│   │   └── database.py            # Async database configuration
│   ├── models/                    # Database models
│   │   └── database.py            # SQLAlchemy models with relationships
│   ├── schemas/                   # Pydantic schemas
│   │   └── schemas.py             # Request/response models
│   ├── services/                  # Business logic layer
│   │   ├── family_tree_service.py # Family tree operations
│   │   ├── person_service.py      # Person CRUD with async support
│   │   ├── relationship_service.py # Relationship management
│   │   └── file_service.py        # File storage abstraction
│   └── main.py                    # FastAPI application setup
├── alembic/                       # Database migrations
├── Dockerfile                     # Container configuration
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (handled by Docker)

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env with the generated secret key
```

### 2. Run with Docker (Recommended)
```bash
# From project root
docker-compose up --build

# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 3. Local Development Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Database Schema

### Core Tables
- **users** - User accounts with subscription support
- **family_trees** - Family tree containers owned by users
- **people** - Individual family members with biographical data
- **relationships** - Graph edges connecting people (spouse, parent, child, etc.)
- **person_files** - File attachments for people (photos, documents)

### Key Features
- **UUID primary keys** for better security and distribution
- **Async-first design** with proper SQLAlchemy 2.0 patterns
- **Graph-like relationships** using junction tables
- **Flexible date handling** supporting both full datetime and date-only inputs
- **File storage abstraction** ready for local or cloud storage

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (returns JWT)
- `GET /users/me` - Get current user info

### Family Trees
- `GET /api/v1/family-trees/` - List user's family trees
- `POST /api/v1/family-trees/` - Create new family tree
- `GET /api/v1/family-trees/{id}` - Get family tree details
- `PUT /api/v1/family-trees/{id}` - Update family tree
- `DELETE /api/v1/family-trees/{id}` - Delete family tree
- `GET /api/v1/family-trees/{id}/graph` - Get graph data for visualization

### People
- `POST /api/v1/people/` - Add person to family tree
- `GET /api/v1/people/{id}` - Get person details
- `PUT /api/v1/people/{id}` - Update person
- `DELETE /api/v1/people/{id}` - Delete person
- `GET /api/v1/people/family-tree/{id}` - List people in family tree

### Relationships (Ready)
- `POST /api/v1/relationships/` - Create relationship
- `GET /api/v1/relationships/{id}` - Get relationship details
- `PUT /api/v1/relationships/{id}` - Update relationship
- `DELETE /api/v1/relationships/{id}` - Delete relationship

## 🧪 Testing the API

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "testpassword123"}'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=testpassword123"
```

### 3. Create Family Tree
```bash
curl -X POST "http://localhost:8000/api/v1/family-trees/" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Smith Family Tree", "description": "Our family history"}'
```

## 🔒 Security Features

- **JWT Authentication** with configurable expiration
- **Password hashing** with bcrypt
- **Request validation** with Pydantic
- **SQL injection protection** with SQLAlchemy
- **CORS configuration** for frontend integration
- **User isolation** - users can only access their own data

## 📈 Performance Optimizations

- **Async database operations** for better concurrency
- **Connection pooling** with configurable pool sizes
- **Database indexing** on frequently queried fields
- **Efficient graph queries** for family tree visualization
- **Pagination support** ready for large datasets

## 🐳 Docker Configuration

The application is fully containerized with:
- **Multi-stage Dockerfile** for optimized image size
- **Health checks** for reliable container orchestration
- **Volume mounting** for development
- **Environment variable configuration**
- **Non-root user** for security

## 🚀 Production Deployment

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
SECRET_KEY=your-secure-secret-key

# Optional
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com
MAX_FILE_SIZE=10485760  # 10MB
```

### Database Migrations
```bash
# Apply migrations in production
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

## 🔄 Recent Updates

- **Fixed async SQLAlchemy** - Fully converted to async/await patterns
- **Enhanced date validation** - Supports both datetime and date-only inputs
- **Improved error handling** - Better error messages and status codes
- **Graph visualization support** - Optimized endpoints for React Flow
- **File storage abstraction** - Ready for cloud storage integration

## 🎯 Next Steps

1. **Implement relationship creation** in frontend
2. **Add file upload functionality** 
3. **Integrate cloud storage** (Oracle/AWS S3)
4. **Add search and filtering** capabilities
5. **Implement data export** features
6. **Add comprehensive testing** suite

## 🤝 Contributing

1. Create feature branch from main
2. Run tests and ensure migrations work
3. Update API documentation if needed
4. Submit pull request with description

## 📝 License

This project is part of a family tree management application built with modern web technologies.