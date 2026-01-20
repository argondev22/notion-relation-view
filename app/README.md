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
    ├── requirements.txt
    └── pyproject.toml
```

## Setup

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL (via Docker)

### Quick Start

1. Start the database:

```bash
make up
```

2. Install dependencies:

```bash
make setup
```

3. Run database migrations:

```bash
make db-upgrade
```

4. Start the development servers:

Frontend (in one terminal):

```bash
make dev-frontend
```

Backend (in another terminal):

```bash
make dev-backend
```

The frontend will be available at <http://localhost:3000>
The backend API will be available at <http://localhost:8000>

## Development

### Frontend

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Testing**: Jest + fast-check

```bash
cd app/frontend
npm run dev      # Start dev server
npm test         # Run tests
npm run build    # Build for production
```

### Backend

- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **Testing**: pytest + hypothesis

```bash
cd app/backend
source venv/bin/activate
uvicorn app.main:app --reload  # Start dev server
pytest                          # Run tests
```

### Database Migrations

```bash
# Create a new migration
cd app/backend
source venv/bin/activate
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

### Frontend Tests

```bash
cd app/frontend
npm test
```

### Backend Tests

```bash
cd app/backend
source venv/bin/activate
pytest
```

### Run All Tests

```bash
make test
```

## Environment Variables

Copy `.env.example` to `.env` in the backend directory and update the values:

```bash
cd app/backend
cp .env.example .env
```

## API Documentation

Once the backend is running, visit:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
