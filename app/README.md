# Notion Relation View

A web application for visualizing Notion page relations as an interactive graph.

## Project Structure

```
app/
├── frontend/          # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   └── setupTests.ts
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── jest.config.js
│
└── backend/           # Python + FastAPI backend
    ├── app/
    │   ├── main.py
    │   ├── config.py
    │   ├── database.py
    │   └── models/
    ├── migrations/    # Alembic migrations
    ├── tests/
    ├── Dockerfile
    ├── requirements.txt
    └── pyproject.toml
```

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose

### Setup

1. Clone the repository and navigate to the app directory

2. Copy the environment file and configure it:

```bash
cd app
cp .env.example .env
# Edit .env file with your configuration
```

**Important**: Change `JWT_SECRET` and `ENCRYPTION_KEY` in production!

1. Run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

Or use Make from the project root:

```bash
make setup
```

This will:

- Create `.env` file if it doesn't exist
- Build all Docker images
- Start PostgreSQL, Redis, Backend, and Frontend services
- Run database migrations

### Access the Application

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **API Documentation**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## Environment Configuration

The application uses a single `.env` file in the `app/` directory for all configuration.

Copy `.env.example` to `.env` and update the values:

```bash
cd app
cp .env.example .env
```

### Environment Variables by Service

#### PostgreSQL (postgres service)

```env
POSTGRES_USER=postgres              # PostgreSQL username
POSTGRES_PASSWORD=postgres          # PostgreSQL password
POSTGRES_DB=notion_relation_view    # Database name
```

#### Backend (backend service)

```env
# Database connection
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/notion_relation_view

# Redis connection
REDIS_URL=redis://redis:6379

# JWT authentication
JWT_SECRET=dev-secret-key-change-in-production    # ⚠️ CHANGE IN PRODUCTION!
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Encryption for Notion API tokens
ENCRYPTION_KEY=dev-encryption-key-change-in-production    # ⚠️ CHANGE IN PRODUCTION!

# CORS configuration
FRONTEND_URL=http://localhost:3000
```

#### Frontend (frontend service)

```env
VITE_API_URL=http://localhost:8000    # Backend API URL
```

**Security Note**:

- The `.env` file is gitignored and will NOT be committed
- `docker-compose.yml` is safely committed to Git
- Always change `JWT_SECRET` and `ENCRYPTION_KEY` in production!

## Development

### Start Services

```bash
cd app
docker compose up -d
# or from project root
make up
```

### View Logs

```bash
cd app
docker compose logs -f              # All services
docker compose logs -f backend      # Backend only
docker compose logs -f frontend     # Frontend only
# or from project root
make logs
make logs-backend
make logs-frontend
```

### Stop Services

```bash
cd app
docker compose down
# or from project root
make down
```

### Restart Services

```bash
cd app
docker compose restart              # All services
docker compose restart backend      # Backend only
docker compose restart frontend     # Frontend only
# or from project root
make restart
make restart-backend
make restart-frontend
```

## Testing

### Run All Tests

```bash
make test
```

### Run Frontend Tests

```bash
cd app
docker compose exec frontend npm test
# or from project root
make test-frontend
```

### Run Backend Tests

```bash
cd app
docker compose exec backend pytest
# or from project root
make test-backend
```

## Database Management

### Run Migrations

```bash
cd app
docker compose exec backend alembic upgrade head
# or from project root
make db-upgrade
```

### Create New Migration

```bash
cd app
docker compose exec backend alembic revision --autogenerate -m "Your message"
# or from project root
make db-migrate msg="Your migration message"
```

### Rollback Migration

```bash
cd app
docker compose exec backend alembic downgrade -1
# or from project root
make db-downgrade
```

### Access Database Shell

```bash
cd app
docker compose exec postgres psql -U postgres -d notion_relation_view
# or from project root
make db-shell
```

## Shell Access

### Backend Shell

```bash
cd app
docker compose exec backend /bin/bash
# or from project root
make shell-backend
```

### Frontend Shell

```bash
cd app
docker compose exec frontend /bin/sh
# or from project root
make shell-frontend
```

## Architecture

### Services

- **postgres**: PostgreSQL 16 database
- **redis**: Redis 7 for caching
- **backend**: FastAPI application (Python 3.11)
- **frontend**: React + Vite application (Node 20)

### Network

All services run on a shared Docker network (`app-network`) for internal communication.

### Volumes

- `postgres_data`: Persistent PostgreSQL data
- `redis_data`: Persistent Redis data
- Frontend and backend source code are mounted as volumes for hot-reloading

## Environment Variables

Backend environment variables are configured in `docker-compose.yml`:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Secret key for JWT tokens
- `ENCRYPTION_KEY`: Key for encrypting Notion tokens
- `FRONTEND_URL`: Frontend URL for CORS

## Useful Commands

```bash
make build             # Build Docker images
make up                # Start all services
make down              # Stop all services
make logs              # View all logs
make restart           # Restart all services
make test              # Run all tests
make db-upgrade        # Apply database migrations
make db-shell          # Access database shell
make shell-backend     # Access backend shell
make shell-frontend    # Access frontend shell
```

## Troubleshooting

### Services won't start

```bash
make down
make clean
make build
make up
```

### Database connection issues

Check if PostgreSQL is healthy:

```bash
docker compose ps
```

### View service logs

```bash
make logs-backend
make logs-frontend
```

## API Documentation

Once the backend is running, visit:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
