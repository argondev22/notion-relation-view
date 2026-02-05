# Technology Stack

## Build System

- **Make**: Primary build orchestration tool
- **Docker Compose**: Multi-service environment management
- **Dev Containers**: VSCode development environment

## Tech Stack

### Frontend
- React (client application)
- Port: 3000

### Backend
- FastAPI (Python web framework)
- Alembic (database migrations)
- Port: 8000

### Database
- PostgreSQL

## Development Tools

- **Prettier**: Code formatting (100 char line width, 2 space indent)
- **Markdownlint**: Markdown linting and formatting
- **Husky**: Git hooks for pre-commit checks
- **Commitlint**: Conventional commit message enforcement

## Common Commands

### Project Initialization
```bash
make init              # Initialize project (first time setup)
                       # - Creates .env file
                       # - Builds containers
                       # - Starts services
                       # - Runs migrations
                       # - Checks health
```

### Docker Operations
```bash
make build             # Build Docker images
make up                # Start all services
make down              # Stop all services
make logs              # View all logs
make logs-backend      # View backend logs only
make logs-frontend     # View frontend logs only
make restart           # Restart all services
make health            # Check service health
```

### Development
```bash
make dev               # Start development environment
make setup             # Build, start, and run migrations
```

### Database
```bash
make db-migrate msg="description"  # Create new migration
make db-upgrade                    # Apply migrations
make db-downgrade                  # Rollback one migration
make db-shell                      # Access PostgreSQL shell
```

### Testing
```bash
make test              # Run all tests
make test-frontend     # Run frontend tests only
make test-backend      # Run backend tests only
```

### Shell Access
```bash
make shell-backend     # Backend container shell
make shell-frontend    # Frontend container shell
```

### Code Quality
```bash
npm run format         # Format all code with Prettier
npm run format:check   # Check formatting without changes
npm run lint:markdown  # Lint markdown files
```

## Service URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Prerequisites

- Docker
- VSCode with Dev Containers extension (`anysphere.remote-containers`)
- UNIX/Linux-based OS (Windows users: use WSL2)
