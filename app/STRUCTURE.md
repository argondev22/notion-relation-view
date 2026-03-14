# Project Structure

Complete directory structure for the Notion Relation View application.

## Overview

```
app/
├── client/                 # Frontend (React + TypeScript + Vite)
├── server/                 # Backend (FastAPI + Python)
├── scripts/                # Utility scripts
├── docker-compose.yml      # Docker services configuration
├── .env.example            # Environment variables template
└── README.md               # Main documentation
```

## Frontend Structure (client/)

```
client/
├── src/
│   ├── components/         # React components
│   │   ├── auth/           # Authentication components (to be created)
│   │   ├── graph/          # Graph visualization components (to be created)
│   │   ├── layout/         # Layout components (to be created)
│   │   └── ui/             # Reusable UI components (to be created)
│   ├── contexts/           # React contexts
│   │   ├── AuthContext.tsx         # Authentication context (to be created)
│   │   ├── ThemeContext.tsx        # Theme management context (to be created)
│   │   └── GraphContext.tsx        # Graph data context (to be created)
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.ts              # Authentication hook (to be created)
│   │   ├── useTheme.ts             # Theme hook (to be created)
│   │   └── useGraph.ts             # Graph hook (to be created)
│   ├── services/           # API services
│   │   ├── api.ts                  # API client (to be created)
│   │   ├── authService.ts          # Authentication service (to be created)
│   │   ├── graphService.ts         # Graph data service (to be created)
│   │   └── viewService.ts          # View management service (to be created)
│   ├── types/              # TypeScript types
│   │   ├── auth.ts                 # Authentication types (to be created)
│   │   ├── graph.ts                # Graph types (to be created)
│   │   └── view.ts                 # View types (to be created)
│   ├── utils/              # Utility functions
│   │   ├── theme.ts                # Theme utilities (to be created)
│   │   └── graph.ts                # Graph utilities (to be created)
│   ├── test/               # Test setup
│   │   └── setup.ts        # Test configuration
│   ├── App.tsx             # Main App component
│   ├── App.css             # App styles
│   ├── main.tsx            # Application entry point
│   ├── index.css           # Global styles
│   └── vite-env.d.ts       # Vite environment types
├── public/                 # Static assets
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── tsconfig.node.json      # TypeScript config for Node
├── vite.config.ts          # Vite configuration
├── .eslintrc.cjs           # ESLint configuration
├── Dockerfile              # Docker configuration
├── .gitignore              # Git ignore rules
└── README.md               # Frontend documentation
```

## Backend Structure (server/)

```
server/
├── alembic/                # Database migrations
│   ├── versions/           # Migration files
│   │   └── .gitkeep        # Placeholder
│   ├── env.py              # Alembic environment
│   └── script.py.mako      # Migration template
├── app/
│   ├── core/               # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py       # Application settings
│   │   └── database.py     # Database setup
│   ├── models/             # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py         # User model
│   │   ├── notion_token.py # Notion token model
│   │   └── view.py         # View model
│   ├── schemas/            # Pydantic schemas
│   │   └── __init__.py
│   ├── api/                # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py         # Authentication endpoints (to be created)
│   │   ├── graph.py        # Graph endpoints (to be created)
│   │   ├── notion.py       # Notion endpoints (to be created)
│   │   └── views.py        # View endpoints (to be created)
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Authentication service (to be created)
│   │   ├── notion_service.py       # Notion API service (to be created)
│   │   ├── cache_service.py        # Redis cache service (to be created)
│   │   ├── encryption_service.py   # Token encryption service (to be created)
│   │   └── graph_service.py        # Graph data service (to be created)
│   ├── __init__.py
│   └── main.py             # Application entry point
├── tests/                  # Test files
│   ├── __init__.py
│   ├── unit/               # Unit tests (to be created)
│   ├── integration/        # Integration tests (to be created)
│   └── property/           # Property-based tests (to be created)
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
├── pytest.ini              # Pytest configuration
├── alembic.ini             # Alembic configuration
├── .gitignore              # Git ignore rules
└── README.md               # Backend documentation
```

## Scripts Structure (scripts/)

```
scripts/
└── setup.sh                # Initial setup script
```

## Configuration Files

### Root Level (app/)

- `docker-compose.yml` - Docker services configuration
- `.env.example` - Environment variables template
- `.env` - Actual environment variables (not in git)
- `.gitignore` - Git ignore rules
- `README.md` - Main documentation
- `STRUCTURE.md` - This file

### Frontend (client/)

- `package.json` - Node.js dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `vite.config.ts` - Vite build configuration
- `.eslintrc.cjs` - ESLint linting rules
- `Dockerfile` - Docker image definition

### Backend (server/)

- `requirements.txt` - Python dependencies
- `alembic.ini` - Database migration configuration
- `pytest.ini` - Test configuration
- `Dockerfile` - Docker image definition

## Key Design Decisions

### Frontend

- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type safety and better developer experience
- **Vite**: Fast build tool with HMR
- **Context API**: State management (may add Redux later if needed)
- **Axios**: HTTP client for API calls

### Backend

- **FastAPI**: Modern, fast Python web framework
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management
- **Pydantic**: Data validation and settings management
- **Redis**: Caching layer for Notion API data

### Infrastructure

- **Docker Compose**: Multi-container orchestration
- **PostgreSQL**: Relational database
- **Redis**: In-memory cache
- **Nginx**: Reverse proxy (to be added for production)

## Development Workflow

1. **Make changes** to code in `client/` or `server/`
2. **Hot reload** automatically updates the running application
3. **Run tests** to verify changes
4. **Commit** changes following conventional commits

## Next Steps

After completing Task 1 (Project Structure Setup), the following tasks will implement:

- Task 2: Database schema and models
- Task 3: Google OIDC authentication
- Task 4: Frontend authentication UI
- Task 6: Notion API client
- Task 7: Notion token management
- Task 8: Redis cache
- Task 9: Relation extraction
- Task 11: Graph data construction
- Task 12: Graph visualization
- And more...

See `.kiro/specs/mvp/tasks.md` for the complete implementation plan.
