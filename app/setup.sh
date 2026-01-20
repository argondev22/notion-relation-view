#!/bin/bash

set -e

echo "🚀 Setting up Notion Relation View..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start database services
echo "📦 Starting database services..."
docker compose up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Setup backend
echo "🐍 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Copy .env.example if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

cd ..

# Setup frontend
echo "⚛️  Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
fi

cd ..

echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  Backend:  cd app/backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  Frontend: cd app/frontend && npm run dev"
echo ""
echo "Or use the Makefile commands:"
echo "  make dev-backend"
echo "  make dev-frontend"
