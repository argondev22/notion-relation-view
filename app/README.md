# Notion Relation View - Application

Complete application setup with frontend, backend, and infrastructure.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Initial Setup

1. **Initialize the project** (from project root):

    ```bash
    make init
    ```

    This command will:
    - Create `.env` file from `.env.example`
    - Build Docker containers
    - Start all services
    - Run database migrations
    - Check service health

2. **Configure Google OIDC** (required for authentication):
    - Go to [Google Cloud Console](https://console.cloud.google.com/)
    - Create a new project or select existing one
    - Enable Google+ API
    - Create OAuth 2.0 credentials
    - Add authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
    - Edit `.env` file and add your Client ID and Client Secret

3. **Restart services**:

    ```bash
    make restart
    ```

4. **Access the application**:
    - Frontend: http://localhost:3000
    - Backend API: http://localhost:8000
    - API Docs: http://localhost:8000/docs

### Health Check

Check if all services are running properly:

```bash
make health
```

## Services

### Frontend (Port 3000)

React + TypeScript application with Vite

**Development**:

```bash
cd client
npm install
npm run dev
```

See [client/README.md](./client/README.md) for details.

### Backend (Port 8000)

FastAPI Python application

**Development**:

```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload
```

See [server/README.md](./server/README.md) for details.

### PostgreSQL (Port 5432)

Database for storing user data, tokens, and views

**Access**:

```bash
docker compose exec postgres psql -U postgres -d notion_relation_view
```

### Redis (Port 6379)

Cache for Notion API data

**Access**:

```bash
docker compose exec redis redis-cli
```

## Docker Commands

All commands should be run from the project root directory.

### Start services

```bash
make up
```

### Stop services

```bash
make down
```

### View logs

```bash
make logs              # All services
make logs-backend      # Backend only
make logs-frontend     # Frontend only
```

### Rebuild services

```bash
make build
make up
```

### Restart services

```bash
make restart           # All services
make restart-backend   # Backend only
make restart-frontend  # Frontend only
```

### Shell access

```bash
make shell-backend     # Backend container
make shell-frontend    # Frontend container
```

## Database Management

All commands should be run from the project root directory.

### Create migration

```bash
make db-migrate msg="description"
```

### Apply migrations

```bash
make db-upgrade
```

### Rollback migration

```bash
make db-downgrade
```

### Database shell

```bash
make db-shell
```

## Testing

### Run all tests

```bash
make test
```

### Run frontend tests only

```bash
make test-frontend
```

### Run backend tests only

```bash
make test-backend
```

### Run with coverage (backend)

```bash
cd app && docker compose exec backend pytest --cov=app
```

## Environment Variables

Key environment variables (see `.env.example`):

### Required

- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret

### Optional (have defaults)

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - JWT signing secret (change in production!)
- `ENCRYPTION_KEY` - Token encryption key (change in production!)
- `FRONTEND_URL` - Frontend URL for CORS
- `VITE_API_URL` - Backend API URL for frontend

## Architecture

```text
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│   Browser   │─────▶│   Frontend  │─────▶│   Backend    │
│             │      │  (React)    │      │  (FastAPI)   │
└─────────────┘      └─────────────┘      └──────┬───────┘
                                                  │
                                    ┌─────────────┼─────────────┐
                                    │             │             │
                              ┌─────▼─────┐ ┌────▼─────┐ ┌────▼──────┐
                              │ PostgreSQL│ │  Redis   │ │ Notion API│
                              │           │ │          │ │           │
                              └───────────┘ └──────────┘ └───────────┘
```

## Development Workflow

1. Make changes to code
2. Changes are automatically reloaded (hot reload enabled)
3. Run tests to verify
4. Commit changes

## Troubleshooting

### Services won't start

```bash
# Check logs
make logs

# Rebuild containers
make down
make build
make up
```

### Database connection errors

```bash
# Check if PostgreSQL is running
cd app && docker compose ps postgres

# Check PostgreSQL logs
make logs-backend

# Restart PostgreSQL
cd app && docker compose restart postgres
```

### Frontend can't connect to backend

- Check `VITE_API_URL` in `app/.env`
- Verify backend is running: `make health`
- Check CORS settings in backend

### Redis connection errors

```bash
# Check if Redis is running
cd app && docker compose ps redis

# Test Redis connection
cd app && docker compose exec redis redis-cli ping
```

### Check service health

```bash
make health
```

## Production Deployment

See deployment documentation (to be created) for production setup instructions.

Key considerations:

- Change `JWT_SECRET` and `ENCRYPTION_KEY`
- Use managed PostgreSQL and Redis services
- Set up proper HTTPS
- Configure production CORS settings
- Set up monitoring and logging
