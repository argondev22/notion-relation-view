# Technology Stack

## Architecture

3-tier full-stack application:
- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL

## Backend Stack

### Core Framework
- **FastAPI** 0.111.0 - Modern async web framework
- **Uvicorn** - ASGI server with standard extras
- **SQLAlchemy** 2.0.31 - ORM for database operations
- **Alembic** 1.13.2 - Database migrations
- **Pydantic** 2.7.4 - Data validation and settings

### Authentication & Security
- **python-jose** - JWT token handling with cryptography
- **passlib** with bcrypt - Password hashing
- **cryptography** 42.0.8 - Encryption utilities

### External APIs
- **httpx** 0.27.0 - Async HTTP client for Notion API

### Testing
- **pytest** 8.2.2 - Test framework
- **pytest-asyncio** 0.23.7 - Async test support
- **hypothesis** 6.103.5 - Property-based testing

## Frontend Stack

### Core Framework
- **React** 18.3.1 - UI library
- **TypeScript** 5.5.3 - Type safety
- **Vite** 5.3.4 - Build tool and dev server

### HTTP Client
- **axios** 1.7.2 - API communication

### Testing
- **Jest** 29.7.0 - Test framework
- **@testing-library/react** 16.0.0 - Component testing
- **@testing-library/jest-dom** 6.4.6 - DOM matchers
- **fast-check** 3.19.0 - Property-based testing

## Development Tools

### Code Quality
- **Prettier** - Code formatting
- **markdownlint-cli2** - Markdown linting
- **Husky** - Git hooks
- **commitlint** - Commit message linting (conventional commits)

### Containerization
- **Docker** - Container runtime
- **Docker Compose** - Multi-service orchestration

## Development Environment

**IMPORTANT**: All application execution, testing, and database operations run inside Docker containers. Never run commands directly on the host machine.

- Backend runs in `backend` container
- Frontend runs in `frontend` container
- Database runs in `postgres` container
- Use `make` commands or `docker compose exec` to interact with services

## Common Commands

### Project Setup
```bash
make init          # Initialize project
make setup         # Build, start services, run migrations
```

### Docker Operations
```bash
make build         # Build Docker images
make up            # Start all services
make down          # Stop all services
make logs          # View all logs
make logs-backend  # View backend logs only
make logs-frontend # View frontend logs only
```

### Database Management
```bash
make db-migrate msg="description"  # Create new migration
make db-upgrade                    # Apply migrations
make db-downgrade                  # Rollback one migration
make db-shell                      # PostgreSQL shell
```

### Testing
```bash
make test          # Run all tests
make test-backend  # Backend tests only (pytest)
make test-frontend # Frontend tests only (jest)
```

### Development
```bash
make dev           # Start dev environment
make restart       # Restart all services
make restart-backend   # Restart backend only
make restart-frontend  # Restart frontend only
```

### Shell Access
```bash
make shell-backend   # Backend container bash
make shell-frontend  # Frontend container shell
```

## Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Database**: localhost:5432 (PostgreSQL)

## Testing Configuration

### Backend (pytest)
- Test discovery: `test_*.py`, `*_test.py`
- Async mode: auto
- Coverage source: `app/` directory
- Excludes: tests, migrations

### Frontend (Jest)
- Environment: jsdom
- TypeScript support via ts-jest
- React Testing Library integration
