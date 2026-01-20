#!/bin/bash

set -e

echo "🚀 Setting up Notion Relation View with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check and create .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please review and update .env file with your configuration."
    echo "⚠️  IMPORTANT: Change JWT_SECRET and ENCRYPTION_KEY for production!"
fi

# Build and start all services
echo "🐳 Building Docker images..."
docker compose build

echo "📦 Starting all services..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 15

# Check if PostgreSQL is ready
echo "🔍 Checking PostgreSQL..."
until docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

# Run database migrations
echo "🗄️  Running database migrations..."
docker compose exec -T backend alembic upgrade head

echo "✅ Setup complete!"
echo ""
echo "🌐 Services are running:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  ReDoc:     http://localhost:8000/redoc"
echo ""
echo "📝 Configuration:"
echo "  Edit app/.env to change settings"
echo ""
echo "📝 Useful commands:"
echo "  make logs          - View all logs"
echo "  make logs-backend  - View backend logs"
echo "  make logs-frontend - View frontend logs"
echo "  make down          - Stop all services"
echo "  make restart       - Restart all services"
echo "  make test          - Run all tests"



