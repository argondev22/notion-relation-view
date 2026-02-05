.PHONY: init build up down logs clean setup db-migrate db-upgrade test dev health

init:
	@echo "🚀 Setting up Notion Relation View..."
	@echo ""
	@if [ ! -f app/.env ]; then \
		echo "📝 Creating .env file from .env.example..."; \
		cp app/.env.example app/.env; \
		echo "✅ .env file created"; \
		echo "⚠️  Please edit app/.env and add your Google OAuth credentials"; \
		echo ""; \
	else \
		echo "✅ .env file already exists"; \
		echo ""; \
	fi
	@if ! docker info > /dev/null 2>&1; then \
		echo "❌ Docker is not running. Please start Docker and try again."; \
		exit 1; \
	fi
	@echo "✅ Docker is running"
	@echo ""
	@echo "🔨 Building Docker containers..."
	@cd app && docker compose build
	@echo "✅ Containers built"
	@echo ""
	@echo "🚀 Starting services..."
	@cd app && docker compose up -d
	@echo "✅ Services started"
	@echo ""
	@echo "⏳ Waiting for PostgreSQL to be ready..."
	@sleep 10
	@echo "🗄️  Running database migrations..."
	@cd app && docker compose exec -T backend alembic upgrade head
	@echo "✅ Database migrations completed"
	@echo ""
	@$(MAKE) health
	@echo ""
	@echo "🎉 Setup complete!"
	@echo ""
	@echo "📋 Next steps:"
	@echo "  1. Edit app/.env and add your Google OAuth credentials"
	@echo "  2. Restart services: make restart"
	@echo "  3. Open http://localhost:3000 in your browser"
	@echo ""
	@echo "📚 Useful commands:"
	@echo "  - View logs: make logs"
	@echo "  - Stop services: make down"
	@echo "  - Restart services: make restart"
	@echo ""

# Docker commands
build:
	@cd app && docker compose build

up:
	@cd app && docker compose up -d

down:
	@cd app && docker compose down

logs:
	@cd app && docker compose logs -f

logs-backend:
	@cd app && docker compose logs -f backend

logs-frontend:
	@cd app && docker compose logs -f frontend

clean:
	@docker system prune -f
	@docker volume prune -f

# Setup commands
setup: build up
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Running database migrations..."
	@cd app && docker compose exec -T backend alembic upgrade head
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Services running:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Health check
health:
	@echo "🏥 Checking service health..."
	@echo ""
	@if curl -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "✅ Backend is healthy (http://localhost:8000)"; \
	else \
		echo "⚠️  Backend health check failed"; \
	fi
	@if curl -s http://localhost:3000 > /dev/null 2>&1; then \
		echo "✅ Frontend is running (http://localhost:3000)"; \
	else \
		echo "⚠️  Frontend health check failed"; \
	fi

# Database commands
db-migrate:
	@cd app && docker compose exec backend alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	@cd app && docker compose exec -T backend alembic upgrade head

db-downgrade:
	@cd app && docker compose exec backend alembic downgrade -1

# Test commands
test:
	@cd app && docker compose exec frontend npm test
	@cd app && docker compose exec backend pytest

test-frontend:
	@cd app && docker compose exec frontend npm test

test-backend:
	@cd app && docker compose exec backend pytest

# Development commands
dev: up
	@echo "Development environment is running"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

restart:
	@cd app && docker compose restart

restart-backend:
	@cd app && docker compose restart backend

restart-frontend:
	@cd app && docker compose restart frontend

# Shell access
shell-backend:
	@cd app && docker compose exec backend /bin/bash

shell-frontend:
	@cd app && docker compose exec frontend /bin/sh

# Database shell
db-shell:
	@cd app && docker compose exec postgres psql -U postgres -d notion_relation_view
