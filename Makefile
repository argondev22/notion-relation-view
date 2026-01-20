.PHONY: init build up down logs clean setup db-migrate db-upgrade test dev

init:
	@chmod +x ./bin/init-project.sh
	@./bin/init-project.sh

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
	@cd app && docker compose exec backend alembic upgrade head
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Services running:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

# Database commands
db-migrate:
	@cd app && docker compose exec backend alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	@cd app && docker compose exec backend alembic upgrade head

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
