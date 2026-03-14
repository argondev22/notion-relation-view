# CLAUDE.md

## Project: Notion Relation View

An interactive graph visualization tool for Notion page relationships.

## Specifications & Design Documents

All project specifications are managed under `.kiro/`. Read these documents before starting implementation work.

### Steering (Project-wide guidelines)

- `.kiro/steering/product.md` — Product overview and purpose
- `.kiro/steering/tech.md` — Technology stack, build system, and development commands (**all commands must run inside Docker containers**)
- `.kiro/steering/structure.md` — Project structure, file naming conventions, and commit format (Conventional Commits)
- `.kiro/steering/language.md` — All code, comments, and commit messages must be in English
- `.kiro/steering/ai-role.md` — AI assistant role definition and interaction guidelines

### MVP Spec

- `.kiro/specs/mvp/requirements.md` — Functional requirements with user stories and acceptance criteria (10 requirements)
- `.kiro/specs/mvp/design.md` — System design: architecture, data models, security, testing strategy
- `.kiro/specs/mvp/tasks.md` — Implementation task list with subtasks and status tracking

### Subscription Management Spec

- `.kiro/specs/subscription-management/requirements.md` — Pricing tiers (Free/Pro), payment processing, access control (19 requirements)
- `.kiro/specs/subscription-management/design.md` — Design document (not yet written)
- `.kiro/specs/subscription-management/tasks.md` — Task list (not yet written)

## Key Rules

- **Docker-first**: All development commands, tests, and builds run inside Docker containers. Use Makefile commands or `docker compose exec`.
- **English only (code)**: Source code, comments, docstrings, and commit messages must be in English.
- **Japanese OK (docs)**: Documentation under `docs/` and PR descriptions may be written in Japanese.
- **Conventional Commits**: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`, `ci:`, `perf:`, `build:`
- **Check tasks.md before working**: Refer to the relevant `tasks.md` to understand current progress and pick up the next pending task.
- **Development process**: When updating practices or knowledge about the development process, update `docs/development-process.md`.
