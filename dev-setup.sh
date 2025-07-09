#!/bin/bash

# ==================================================================
# FAMILY TREE APP - DEVELOPMENT SETUP SCRIPT
# ==================================================================
# This script sets up the development environment and starts the application

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "=============================================="
    echo "$1"
    echo "=============================================="
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker compose > /dev/null 2>&1; then
        print_error "docker compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Check if Node.js is installed
check_nodejs() {
    if ! command -v node > /dev/null 2>&1; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node --version)"
        exit 1
    fi
    print_success "Node.js $(node --version) is installed"
}

# Check if npm is installed
check_npm() {
    if ! command -v npm > /dev/null 2>&1; then
        print_error "npm is not installed. Please install npm and try again."
        exit 1
    fi
    print_success "npm $(npm --version) is installed"
}

# Verify environment files exist
check_env_files() {
    if [ ! -f "backend/.env" ]; then
        print_error "Backend .env file not found. Please ensure backend/.env exists."
        exit 1
    fi
    
    if [ ! -f "frontend/.env" ]; then
        print_error "Frontend .env file not found. Please ensure frontend/.env exists."
        exit 1
    fi
    
    print_success "Environment files found"
}

# Install frontend dependencies
install_frontend_deps() {
    print_status "Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    print_success "Frontend dependencies installed"
}

# Start backend services with Docker
start_backend() {
    print_status "Starting backend services (PostgreSQL + FastAPI)..."
    docker compose up -d db
    
    print_status "Waiting for database to be ready..."
    sleep 10
    
    docker compose up -d api
    print_success "Backend services started"
}

# Wait for backend to be ready
wait_for_backend() {
    print_status "Waiting for backend API to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend API is ready"
            return 0
        fi
        sleep 2
    done
    print_error "Backend API failed to start within 60 seconds"
    exit 1
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    docker compose exec api alembic upgrade head
    print_success "Database migrations completed"
}

# Start frontend development server
start_frontend() {
    print_status "Starting frontend development server..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
    print_success "Frontend started (PID: $FRONTEND_PID)"
}

# Display final information
show_final_info() {
    print_header "🎉 FAMILY TREE APP IS READY!"
    echo ""
    echo "📱 Frontend:     http://localhost:3000"
    echo "🔧 Backend API:  http://localhost:8000"
    echo "📚 API Docs:     http://localhost:8000/docs"
    echo "🐘 Database:     postgresql://localhost:5432/family_tree_db"
    echo ""
    echo "🛑 To stop the application:"
    echo "   Frontend: Ctrl+C in this terminal"
    echo "   Backend:  docker compose down"
    echo ""
    echo "🔍 Useful commands:"
    echo "   View backend logs:  docker compose logs api"
    echo "   View database logs: docker compose logs db"
    echo "   Reset database:     docker compose down -v && docker compose up -d"
    echo ""
}

# Main execution
main() {
    print_header "🚀 FAMILY TREE APP - DEVELOPMENT SETUP"
    
    # Pre-flight checks
    print_status "Running pre-flight checks..."
    check_docker
    check_docker_compose
    check_nodejs
    check_npm
    check_env_files
    
    # Setup and start services
    install_frontend_deps
    start_backend
    wait_for_backend
    run_migrations
    
    # Start frontend (this will block)
    show_final_info
    start_frontend
    
    # Wait for frontend to exit
    wait $FRONTEND_PID
}

# Handle script interruption
cleanup() {
    print_warning "Shutting down..."
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup INT TERM

# Run main function
main "$@"