# Development Guide

## Project Setup Complete ✅

The project structure has been initialized with:

- ✅ Frontend (React + TypeScript + Vite) - Dockerized
- ✅ Backend (Python + FastAPI) - Dockerized
- ✅ Database schema (PostgreSQL with Alembic migrations)
- ✅ Docker Compose configuration (all services)
- ✅ Test frameworks (Jest + fast-check, pytest + hypothesis)

## Getting Started with Docker

### 1. Start All Services

```bash
cd app
./setup.sh
```

Or from project root:

```bash
make setup
```

This will:
- Build all Docker images
- Start PostgreSQL, Redis, Backend, and Frontend
- Run database migrations

Or manually:

```bash
cd app
docker compose build
docker compose up -d
docker compose exec backend alembic upgrade head
```

### 2. Access Services

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

### 3. View Logs

```bash
cd app
docker compose logs -f              # All services
docker compose logs -f backend      # Backend only
docker compose logs -f frontend     # Frontend only
```

Or from project root:

```bash
make logs
make logs-backend
make logs-frontend
```

## Docker Services

### Frontend Container

- **Base Image**: node:20-alpine
- **Port**: 3000
- **Hot Reload**: Enabled via volume mount
- **Command**: `npm run dev -- --host 0.0.0.0`

### Backend Container

- **Base Image**: python:3.11-slim
- **Port**: 8000
- **Hot Reload**: Enabled via volume mount
- **Command**: `uvicorn app.main:app --reload --host 0.0.0.0`

### PostgreSQL Container

- **Image**: postgres:16-alpine
- **Port**: 5432
- **Database**: notion_relation_view
- **Credentials**: postgres/postgres

### Redis Container

- **Image**: redis:7-alpine
- **Port**: 6379

## Development Workflow

### Making Code Changes

All code changes are automatically reflected due to volume mounts:

**Frontend**:
- Edit files in `app/frontend/src/`
- Vite will hot-reload automatically

**Backend**:
- Edit files in `app/backend/app/`
- Uvicorn will reload automatically

### Running Tests

```bash
# All tests (from project root)
make test

# Frontend only
cd app && docker compose exec frontend npm test
# or from project root
make test-frontend

# Backend only
cd app && docker compose exec backend pytest
# or from project root
make test-backend
```

### Database Operations

```bash
# Apply migrations
cd app && docker compose exec backend alembic upgrade head
# or from project root
make db-upgrade

# Create new migration
cd app && docker compose exec backend alembic revision --autogenerate -m "Add new table"
# or from project root
make db-migrate msg="Add new table"

# Rollback
cd app && docker compose exec backend alembic downgrade -1
# or from project root
make db-downgrade

# Access database shell
cd app && docker compose exec postgres psql -U postgres -d notion_relation_view
# or from project root
make db-shell
```

### Shell Access

```bash
# Backend shell
cd app && docker compose exec backend /bin/bash
# or from project root
make shell-backend

# Frontend shell
cd app && docker compose exec frontend /bin/sh
# or from project root
make shell-frontend
```
make shell-frontend
docker compose exec frontend /bin/sh
```

## Project Structure

```
app/
├── frontend/
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # React components
│   │   ├── types/         # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile         # Frontend Docker image
│   ├── .dockerignore
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── jest.config.js
│
└── backend/
    ├── app/
    │   ├── models/        # SQLAlchemy models
    │   ├── routers/       # API endpoints
    │   ├── schemas/       # Pydantic schemas
    │   ├── services/      # Business logic
    │   ├── main.py
    │   ├── config.py
    │   └── database.py
    ├── migrations/        # Alembic migrations
    ├── tests/
    ├── Dockerfile         # Backend Docker image
    ├── .dockerignore
    └── requirements.txt
```

## Environment Variables

Environment variables are configured in `docker-compose.yml`:

### Backend Environment

```yaml
DATABASE_URL: postgresql://postgres:postgres@postgres:5432/notion_relation_view
REDIS_URL: redis://redis:6379
FRONTEND_URL: http://localhost:3000
JWT_SECRET: dev-secret-key-change-in-production
JWT_ALGORITHM: HS256
JWT_EXPIRATION_MINUTES: 1440
ENCRYPTION_KEY: dev-encryption-key-change-in-production
```

### Frontend Environment

```yaml
VITE_API_URL: http://localhost:8000
```

## Common Commands

### Service Management

```bash
cd app
docker compose up -d    # Start all services
docker compose down     # Stop all services
docker compose restart  # Restart all services
docker compose restart backend  # Restart backend only
docker compose restart frontend # Restart frontend only
docker compose logs -f  # View all logs

# Or from project root
make up
make down
make restart
make restart-backend
make restart-frontend
make logs
```

### Development

```bash
cd app
docker compose up -d    # Start development environment

# Or from project root
make dev                # Start development environment
make test               # Run all tests
make db-upgrade         # Apply migrations
make db-shell           # Database shell
make shell-backend      # Backend shell
make shell-frontend     # Frontend shell
```

### Cleanup

```bash
cd app
docker compose down     # Stop services
docker compose down -v  # Remove volumes too

# Or from project root
make down
make clean              # Clean Docker system
```

## Troubleshooting

### Services won't start

```bash
make down
make clean
make build
make up
```

### Port already in use

Check if ports 3000, 8000, 5432, or 6379 are already in use:

```bash
lsof -i :3000
lsof -i :8000
lsof -i :5432
lsof -i :6379
```

### Database connection issues

```bash
# Check service health
cd app && docker compose ps

# View backend logs
cd app && docker compose logs backend
# or from project root
make logs-backend

# Restart database
cd app && docker compose restart postgres
```

### Frontend not hot-reloading

```bash
# Restart frontend
cd app && docker compose restart frontend
# or from project root
make restart-frontend

# Check logs
cd app && docker compose logs frontend
# or from project root
make logs-frontend
```

### Backend not hot-reloading

```bash
# Restart backend
cd app && docker compose restart backend
# or from project root
make restart-backend

# Check logs
cd app && docker compose logs backend
# or from project root
make logs-backend
```

## Testing

### Frontend Tests

```bash
# Run tests
cd app && docker compose exec frontend npm test

# With coverage
cd app && docker compose exec frontend npm test -- --coverage

# Or from project root
make test-frontend
```

### Backend Tests

```bash
# Run tests
cd app && docker compose exec backend pytest

# Verbose output
cd app && docker compose exec backend pytest -v

# With coverage
cd app && docker compose exec backend pytest --cov=app

# Or from project root
make test-backend
```

## Next Steps

Refer to `.kiro/specs/notion-relation-view/tasks.md` for the implementation plan.

The next task is: **Task 2 - Backend: ユーザー認証システムの実装**
