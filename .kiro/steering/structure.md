# Project Structure

## Root Directory

```
.
├── .kiro/                    # Kiro AI assistant configuration
│   ├── specs/                # Feature specifications
│   └── steering/             # AI guidance documents
├── .github/                  # GitHub workflows and templates
├── .devcontainer/            # Dev container configuration
├── app/                      # Application source code
├── bin/                      # Utility scripts
└── docs/                     # Project documentation
```

## Application Structure (`app/`)

### Backend (`app/backend/`)

```
backend/
├── app/
│   ├── models/               # SQLAlchemy database models
│   │   ├── user.py           # User model
│   │   ├── notion_token.py   # Notion API token storage
│   │   └── view.py           # View configuration model
│   ├── routers/              # FastAPI route handlers
│   │   └── auth.py           # Authentication endpoints
│   ├── schemas/              # Pydantic schemas for validation
│   │   └── auth.py           # Auth request/response schemas
│   ├── services/             # Business logic layer
│   │   ├── auth_service.py   # Authentication logic
│   │   └── notion_client.py  # Notion API integration
│   ├── config.py             # Application configuration
│   ├── database.py           # Database connection setup
│   └── main.py               # FastAPI application entry point
├── migrations/               # Alembic database migrations
│   ├── versions/             # Migration version files
│   └── env.py                # Alembic environment config
├── tests/                    # Test suite
│   ├── test_*.py             # Unit tests
│   └── test_*_properties.py  # Property-based tests
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Python project config (pytest, coverage)
└── Dockerfile                # Backend container definition
```

### Frontend (`app/frontend/`)

```
frontend/
├── src/
│   ├── api/                  # API client layer
│   │   └── client.ts         # Axios configuration
│   ├── components/           # React components
│   ├── types/                # TypeScript type definitions
│   │   └── index.ts          # Shared types
│   ├── App.tsx               # Root component
│   ├── main.tsx              # Application entry point
│   └── index.css             # Global styles
├── package.json              # Node dependencies and scripts
├── tsconfig.json             # TypeScript configuration
├── vite.config.ts            # Vite build configuration
├── jest.config.js            # Jest test configuration
└── Dockerfile                # Frontend container definition
```

## Documentation (`docs/`)

- `API.yml` - OpenAPI specification
- `ARCHITECTURE.md` - System architecture documentation
- `DATABASE.md` - Database schema documentation
- `PRODUCT.md` - Product vision and requirements
- `SETUP.md` - Setup instructions
- `UI.md` - UI/UX guidelines

## Configuration Files

### Code Quality
- `.prettierrc.json` - Prettier formatting rules
- `.prettierignore` - Files to exclude from formatting
- `.markdownlint.jsonc` - Markdown linting rules
- `.editorconfig` - Editor configuration
- `.commitlintrc.json` - Commit message rules

### Git
- `.gitignore` - Git ignore patterns
- `.gitattributes` - Git attributes
- `.husky/` - Git hooks (commit-msg validation)

### Docker
- `app/docker-compose.yml` - Multi-service orchestration
- `app/backend/Dockerfile` - Backend image
- `app/frontend/Dockerfile` - Frontend image

## Naming Conventions

### Python (Backend)
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Test files: `test_*.py` or `*_test.py`
- Property tests: `test_*_properties.py`

### TypeScript (Frontend)
- Files: `camelCase.ts`, `PascalCase.tsx` (components)
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Types/Interfaces: `PascalCase`
- Test files: `*.test.tsx`

### Database
- Tables: `snake_case` (plural)
- Columns: `snake_case`
- Indexes: `ix_{table}_{column}`
- Foreign keys: `fk_{table}_{column}`

## Key Patterns

### Backend Architecture
- **Layered structure**: Routes → Services → Models
- **Dependency injection**: Database sessions via FastAPI dependencies
- **Async/await**: All route handlers and database operations
- **Pydantic validation**: Request/response schemas
- **Alembic migrations**: All schema changes tracked

### Frontend Architecture
- **Component-based**: Reusable React components
- **Type safety**: TypeScript for all code
- **API abstraction**: Centralized axios client
- **Testing**: Unit tests with React Testing Library

### Testing Strategy
- **Unit tests**: Core functionality and edge cases
- **Property-based tests**: Universal properties with Hypothesis (Python) and fast-check (TypeScript)
- **Integration tests**: API endpoints with test database
- **Test isolation**: Each test uses fresh database state
