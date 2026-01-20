# Development Guide

## Project Setup Complete ✅

The project structure has been initialized with:

- ✅ Frontend (React + TypeScript + Vite)
- ✅ Backend (Python + FastAPI)
- ✅ Database schema (PostgreSQL with Alembic migrations)
- ✅ Docker Compose configuration
- ✅ Test frameworks (Jest + fast-check, pytest + hypothesis)

## Getting Started

### 1. Start Database Services

```bash
docker compose up -d
```

This starts PostgreSQL and Redis containers.

### 2. Setup Backend

```bash
cd app/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` file with your configuration.

### 3. Run Database Migrations

```bash
cd app/backend
source venv/bin/activate
alembic upgrade head
```

### 4. Setup Frontend

```bash
cd app/frontend
npm install
```

### 5. Start Development Servers

**Backend** (Terminal 1):

```bash
cd app/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (Terminal 2):

```bash
cd app/frontend
npm run dev
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
    └── requirements.txt
```

## Database Schema

### Users Table

- `id` (UUID, PK)
- `email` (String, unique)
- `password_hash` (String)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Notion Tokens Table

- `user_id` (UUID, PK, FK to users)
- `encrypted_token` (String)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Views Table

- `id` (UUID, PK)
- `user_id` (UUID, FK to users)
- `name` (String)
- `database_ids` (Array of Strings)
- `zoom_level` (Float)
- `pan_x` (Float)
- `pan_y` (Float)
- `created_at` (DateTime)
- `updated_at` (DateTime)

## Testing

### Frontend Tests

```bash
cd app/frontend
npm test              # Run once
npm run test:watch    # Watch mode
```

### Backend Tests

```bash
cd app/backend
source venv/bin/activate
pytest                # Run all tests
pytest -v             # Verbose output
pytest --cov=app      # With coverage
```

## API Documentation

Once the backend is running:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Environment Variables

### Backend (.env)

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/notion_relation_view
JWT_SECRET=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
ENCRYPTION_KEY=your-encryption-key-change-this-in-production
FRONTEND_URL=http://localhost:3000
REDIS_URL=redis://localhost:6379
```

## Common Commands

### Database

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Docker

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Restart a service
docker compose restart postgres
```

## Next Steps

Refer to `.kiro/specs/notion-relation-view/tasks.md` for the implementation plan.

The next task is: **Task 2 - Backend: ユーザー認証システムの実装**
