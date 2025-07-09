# Family Tree App - Quick Setup Guide

This guide will get you up and running with the Family Tree application in under 5 minutes.

## 🚀 One-Command Setup (Recommended)

The fastest way to get started:

```bash
# Make the setup script executable
chmod +x dev-setup.sh

# Run the automated setup
./dev-setup.sh
```

This script will:
- ✅ Check all prerequisites 
- ✅ Install frontend dependencies
- ✅ Start PostgreSQL and FastAPI backend
- ✅ Run database migrations
- ✅ Start the React frontend
- ✅ Open the app in your browser

## 📋 Prerequisites

Before running the setup script, ensure you have:

- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Node.js 18+** - [Install Node.js](https://nodejs.org/)
- **npm** - Comes with Node.js

## 🔧 Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Verify Environment Files

The project includes ready-to-use `.env` files:
- `backend/.env` - Backend configuration
- `frontend/.env` - Frontend configuration

These are pre-configured for development and should work out of the box.

### 2. Start Backend Services

```bash
# Start PostgreSQL and FastAPI
docker-compose up -d

# Wait for services to start (about 30 seconds)
docker-compose logs api

# Run database migrations
docker-compose exec api alembic upgrade head
```

### 3. Start Frontend

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm start
```

## 🌐 Access the Application

After setup:

- **Web App**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## 🛠 Development Workflow

### Backend Development

```bash
# View backend logs
docker-compose logs -f api

# Run migrations after model changes
docker-compose exec api alembic revision --autogenerate -m "Description"
docker-compose exec api alembic upgrade head

# Access backend container
docker-compose exec api bash

# Stop backend services
docker-compose down
```

### Frontend Development

```bash
cd frontend

# Install new packages
npm install package-name

# Run tests
npm test

# Build for production
npm run build
```

### Database Management

```bash
# View database logs
docker-compose logs db

# Connect to database
docker-compose exec db psql -U family_tree_user -d family_tree_db

# Reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

## 🔍 Troubleshooting

### Common Issues

**Docker not starting:**
```bash
# Check Docker is running
docker info

# Restart Docker if needed
```

**Port conflicts:**
```bash
# Check what's using ports 3000, 8000, or 5432
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Stop conflicting services or change ports in docker-compose.yml
```

**Frontend won't start:**
```bash
# Clear npm cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Database connection errors:**
```bash
# Ensure database is ready
docker-compose exec db pg_isready -U family_tree_user

# Check database logs
docker-compose logs db
```

### Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify all services are running: `docker-compose ps`
3. Ensure ports 3000, 8000, and 5432 are available
4. Try resetting: `docker-compose down -v && docker-compose up -d`

## 📁 Project Structure

```
family-tree-app/
├── backend/
│   ├── .env                    # Backend environment variables
│   ├── app/                    # FastAPI application
│   ├── alembic/               # Database migrations
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── .env                    # Frontend environment variables
│   ├── src/                    # React application
│   └── package.json           # Node.js dependencies
├── docker-compose.yml         # Development services
├── dev-setup.sh              # Automated setup script
└── SETUP.md                   # This file
```

## 🔒 Security Note

The included `.env` files contain development-only secrets. For production deployment:

1. Generate secure secrets:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Update `backend/.env` with production values
3. Configure proper CORS origins
4. Use production database credentials
5. Set `DEBUG=false`

## 🎯 Next Steps

Once the app is running:

1. **Register a new account** at http://localhost:3000/register
2. **Create your first family tree** from the dashboard
3. **Add family members** using the interactive interface
4. **Explore the API** at http://localhost:8000/docs

Happy family tree building! 🌳