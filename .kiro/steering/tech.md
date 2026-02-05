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

## Development Execution Guidelines

### Container-First Development

**CRITICAL**: すべての開発関連のコマンド実行、テスト、ビルドは**必ずDockerコンテナ内**で行ってください。

### Why Container Execution?

- 環境の一貫性を保証
- 依存関係の競合を回避
- チーム全体で同じ環境を共有
- ホストマシンの環境を汚染しない

### Execution Rules

#### ✅ Correct Approach

**バックエンド開発・テスト**:
```bash
# コンテナ内でシェルを開く
make shell-backend

# コンテナ内でコマンドを実行
pytest tests/
python -m app.main
alembic revision --autogenerate -m "description"
```

**フロントエンド開発・テスト**:
```bash
# コンテナ内でシェルを開く
make shell-frontend

# コンテナ内でコマンドを実行
npm test
npm run build
npm run lint
```

**ワンライナーでの実行**:
```bash
# バックエンドテスト
docker compose -f app/docker-compose.yml exec backend pytest tests/

# フロントエンドテスト
docker compose -f app/docker-compose.yml exec frontend npm test
```

#### ❌ Incorrect Approach

```bash
# ホストマシンで直接実行 - これは避ける
cd app/backend && pytest tests/
cd app/frontend && npm test
python app/backend/app/main.py
```

### When to Use Each Method

1. **Makefileコマンド** (`make test`, `make test-backend`など)
   - 推奨される方法
   - プロジェクト標準のコマンド
   - 自動的にコンテナ内で実行される

2. **シェルアクセス** (`make shell-backend`, `make shell-frontend`)
   - 複数のコマンドを連続して実行する場合
   - デバッグやインタラクティブな作業
   - 開発中の試行錯誤

3. **docker compose exec**
   - Makefileに定義されていないコマンド
   - CI/CDパイプラインでの使用
   - スクリプト内での自動化

### AI Assistant Guidelines

AIアシスタントがコマンド実行を提案する際は:

1. **常にコンテナ内実行を前提とする**
2. **Makefileコマンドを優先的に提案する**
3. **必要に応じてシェルアクセス方法を説明する**
4. **ホストマシンでの直接実行は提案しない**

### Example Workflows

**新しいマイグレーションの作成**:
```bash
# 1. バックエンドコンテナに入る
make shell-backend

# 2. マイグレーションを作成
alembic revision --autogenerate -m "add user table"

# 3. マイグレーションを適用
alembic upgrade head
```

**テストの実行とデバッグ**:
```bash
# 1. テストを実行（Makefileコマンド）
make test-backend

# 2. 失敗した場合、コンテナ内で詳細確認
make shell-backend
pytest tests/test_specific.py -v
```

**フロントエンドの開発**:
```bash
# 1. 開発サーバーは自動起動（docker-compose）
make up

# 2. テストの実行
make test-frontend

# 3. 追加のnpmコマンドが必要な場合
make shell-frontend
npm run lint
```
