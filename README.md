# Template for Development

## Overview

A comprehensive project template that provides a ready-to-use development environment with modern tooling and best practices. This template accelerates project setup by including pre-configured development containers, GitHub workflows, and standardized templates for issues and pull requests.

## Features

### 🚀 Development Environment Template

- **Dev Containers**: Instant development environment setup with VSCode
- **Docker Compose**: Easy multi-service environment management
- **GitHub Templates**: Standardized issue and PR templates

### 📱 Sample Application

- **Full-Stack Architecture**: 3-tier architecture with React + FastAPI + PostgreSQL
- **Real-time Features**: Instant data updates with button clicks
- **Data Persistence**: Click history management with PostgreSQL
- **API Documentation**: Auto-generated documentation with Swagger UI
- **Responsive UI**: Modern web interface

## Architecture

```mermaid
sequenceDiagram
    autonumber
    actor CL as Client (React)
    participant SV as Server (FastAPI)
    participant DB as Database (PostgreSQL)
    CL->>SV: HTTP Request (API Call)
    SV->>DB: SQL Query
    DB->>SV: Query Result
    SV->>CL: JSON Response
```

## Directory Structure

```text
.
├── .devcontainer/                # Development container configuration
├── .github/                      # GitHub configuration
│   ├── ISSUE_TEMPLATE/           # GitHub issue templates
│   └── PULL_REQUEST_TEMPLATE/    # GitHub PR templates
├── .vscode/                      # VSCode configuration
├── app/                          # Complete application directory (source code, Docker configs, etc.)
│   ├── client/                   # React frontend application
│   └── server/                   # FastAPI backend application
├── bin/                          # Utility scripts
└── docs/                         # Project documentation
```

> **📖 For detailed information about each service, please refer to their respective README files:**
>
> - **Client (React)**: [`app/client/README.md`](app/client/README.md)
> - **Server (FastAPI)**: [`app/server/README.md`](app/server/README.md)

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)
- [Dev Containers](https://containers.dev/) extension (`anysphere.remote-containers`) for VSCode
- UNIX/Linux-based OS (Windows users should use WSL2)

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repo-url> <project-name>
   cd <project-name>
   ```

2. **Initialize the project**

   ```bash
   make init
   ```

   This command will:
   - Create `.env` file from `.env.example`
   - Build Docker containers
   - Start all services
   - Run database migrations
   - Check service health

3. **Configure Google OAuth** (required for authentication)
   - Edit `app/.env` and add your Google OAuth credentials
   - Restart services: `make restart`

4. **Access your application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
