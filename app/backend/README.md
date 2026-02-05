# Notion Relation View - Backend

FastAPI backend for the Notion Relation View application.

## Architecture

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **Authentication**: Google OIDC + JWT
- **Migrations**: Alembic

## Directory Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   └── env.py           # Alembic environment
├── app/
│   ├── core/            # Core configuration
│   │   ├── config.py    # Application settings
│   │   └── database.py  # Database setup
│   ├── models/          # SQLAlchemy models
│   │   ├── user.py
│   │   ├── notion_token.py
│   │   └── view.py
│   ├── api/             # API endpoints (to be implemented)
│   ├── services/        # Business logic (to be implemented)
│   └── main.py          # Application entry point
├── tests/               # Test files (to be implemented)
├── Dockerfile           # Docker configuration
├── requirements.txt     # Python dependencies
└── alembic.ini         # Alembic configuration
```

## Setup

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (copy from `.env.example`):
   ```bash
   cp ../.env.example .env
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Development

From the `app/` directory:

```bash
docker compose up backend
```

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback one migration:
```bash
alembic downgrade -1
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app
```

## Environment Variables

See `../.env.example` for required environment variables.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: Secret for JWT token signing
- `ENCRYPTION_KEY`: Key for encrypting Notion tokens
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
