.PHONY: init build up down logs clean setup-frontend setup-backend db-migrate db-upgrade test

init:
	@chmod +x ./bin/init-project.sh
	@./bin/init-project.sh

# Docker commands
build:
	@docker compose build

up:
	@docker compose up -d

down:
	@docker compose down

logs:
	@docker compose logs -f

clean:
	@docker system prune -f
	@docker volume prune -f

# Setup commands
setup-frontend:
	@cd app/frontend && npm install

setup-backend:
	@cd app/backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt

setup: up setup-frontend setup-backend
	@echo "Setup complete! Run 'make db-migrate' to create database tables."

# Database commands
db-migrate:
	@cd app/backend && . venv/bin/activate && alembic revision --autogenerate -m "Initial migration"

db-upgrade:
	@cd app/backend && . venv/bin/activate && alembic upgrade head

# Test commands
test:
	@cd app/frontend && npm test
	@cd app/backend && . venv/bin/activate && pytest

# Development commands
dev-frontend:
	@cd app/frontend && npm run dev

dev-backend:
	@cd app/backend && . venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
