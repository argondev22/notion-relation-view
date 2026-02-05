# Project Structure

## Root Directory Layout

```
.
├── .devcontainer/          # Dev container configuration for VSCode
├── .github/                # GitHub workflows and templates
│   ├── ISSUE_TEMPLATE/     # Issue templates
│   └── PULL_REQUEST_TEMPLATE/  # PR templates
├── .husky/                 # Git hooks configuration
├── .kiro/                  # Kiro AI assistant configuration
│   ├── settings/           # Kiro settings
│   ├── specs/              # Feature specifications
│   └── steering/           # AI guidance documents
├── .vscode/                # VSCode workspace settings
├── app/                    # Application source code
│   ├── client/             # React frontend
│   └── server/             # FastAPI backend
├── bin/                    # Utility scripts
├── infra/                  # Infrastructure configuration
└── Makefile                # Build and development commands
```

## Key Directories

### `.devcontainer/`
Development container definitions for consistent environments across team members.

### `.github/`
GitHub-specific configurations including CI/CD workflows, issue templates, and PR templates.

### `.kiro/`
AI assistant configuration:
- `specs/`: Feature specifications following spec-driven development
- `steering/`: Guidance documents for AI assistant behavior
- `settings/`: Tool and assistant settings

### `app/`
Main application code organized by service:
- `client/`: Frontend React application
- `server/`: Backend FastAPI application
- Each service has its own README with detailed documentation

### `bin/`
Executable scripts for project automation and utilities.

### `infra/`
Infrastructure as code and deployment configurations.

## Code Organization Principles

- **Service Separation**: Frontend and backend are separate services with clear boundaries
- **Docker-First**: All services run in containers for consistency
- **Documentation Co-location**: Each major component has its own README
- **Configuration at Root**: Shared tooling configuration (Prettier, EditorConfig, etc.) at project root

## File Naming Conventions

- Use kebab-case for directories and configuration files
- Follow language-specific conventions within service directories
- Markdown files use `.md` extension
- Configuration files use appropriate extensions (`.json`, `.yml`, `.jsonc`)

## Code Style

- **Indentation**: 2 spaces (except Makefiles use tabs)
- **Line Endings**: LF (Unix-style)
- **Encoding**: UTF-8
- **Line Width**: 100 characters (Prettier)
- **Trailing Whitespace**: Removed (except in Markdown)
- **Final Newline**: Required

## Commit Message Format

Follow Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Allowed types**: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, deps, docker

**Rules**:
- Type must be lowercase
- Subject cannot be empty or end with period
- Header max 100 characters
- Body max 200 characters per line
