# Family Tree API - Backend

## Setup Instructions

### 1. Initial Project Setup

```bash
# Navigate to your project directory
cd family-tree-app

# Create the backend directory structure
mkdir -p backend/app/{api/v1/endpoints,core,models,schemas,services}
mkdir -p backend/alembic
```

### 2. Create Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy the environment template
cp .env.example .env

# Edit .env file with your actual values:
# - Update SECRET_KEY (generate a secure random key)
# - Add Oracle Object Storage credentials when ready
# - Update database credentials if different from defaults
```

### 4. Database Setup

Make sure PostgreSQL is running, then:

```bash
# Initialize Alembic
alembic init alembic

# Generate first migration
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### 5. Run the Development Server

```bash
# From the backend directory
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Using Docker (Alternative)

```bash
# From the project root directory
docker-compose up --build
```

## API Documentation

Once running, visit:
- API Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Testing the API

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

### 3. Create a Family Tree
```bash
# Use the access token from login response
curl -X POST "http://localhost:8000/api/v1/family-trees/" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "My Family Tree", "description": "Our family history"}'
```

## Next Steps

1. **Phase 2**: Add file upload capabilities with Oracle Object Storage
2. **Phase 3**: Build the React frontend
3. **Phase 4**: Implement React Flow visualization
4. **Phase 5**: Production deployment

## Development Notes

- The API uses FastAPI Users for authentication
- PostgreSQL with graph-like relationships via junction tables
- All endpoints require authentication except registration/login
- UUID primary keys for better security and distribution
- Proper error handling and validation throughout