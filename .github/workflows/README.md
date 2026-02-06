# GitHub Actions Workflows

## Overview

This directory contains CI/CD workflows for automated testing and code quality checks.

## Workflows

### 1. Common Formatting and Linting
**File**: `common-formatting-and-linting.yml`

**Triggers**: Push/PR to `main`

**Jobs**:
- ✅ Prettier - Check code formatting (JS/TS/JSON/YAML/MD)
- ✅ Markdownlint - Lint Markdown files
- ✅ yamllint - Lint YAML files
- ✅ actionlint - Lint GitHub Actions workflows

### 2. Python Code Quality
**File**: `python-quality.yml`

**Triggers**: Push/PR to `main` (when Python files change)

**Jobs**:
- ✅ **Lint** - Ruff + Flake8
- ✅ **Format** - Black + isort check
- ✅ **Type Check** - mypy
- ✅ **Test** - pytest with PostgreSQL

**Duration**: ~3-5 minutes

### 3. Python Code Quality (Fast)
**File**: `python-quality-fast.yml`

**Triggers**: Push to feature branches (when Python files change)

**Jobs**:
- ✅ **Ruff** - Fast linting and format check

**Duration**: ~30 seconds

**Purpose**: Quick feedback during development

### 4. Dependabot Auto Merge
**File**: `dependabot-auto-merge.yml`

**Triggers**: Dependabot PRs

**Purpose**: Automatically merge minor/patch dependency updates

## Workflow Strategy

### Main Branch (Comprehensive)
```
Push to main → Full quality checks
├── Common formatting (Prettier, Markdown, YAML)
└── Python quality (Ruff, Black, isort, mypy, pytest)
```

### Feature Branches (Fast)
```
Push to feature/* → Fast checks only
└── Python quality (Ruff only)
```

### Pull Requests
```
PR to main → Full quality checks
├── Common formatting
└── Python quality (all tools)
```

## Local Development

Before pushing, run quality checks locally:

```bash
# Quick check (recommended before commit)
make quality-check

# Individual checks
make lint-backend        # Lint only
make format-backend      # Format only
make type-check          # Type check only
```

## Status Badges

Add to your README.md:

```markdown
![Python Code Quality](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/python-quality.yml/badge.svg)
![Common Formatting](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/common-formatting-and-linting.yml/badge.svg)
```

## Troubleshooting

### Workflow fails on Python files

1. Run locally first:
   ```bash
   make quality-check
   ```

2. Fix issues:
   ```bash
   make lint-backend-fix
   ```

3. Commit and push

### Workflow is too slow

- Feature branches use fast workflow (Ruff only)
- Main branch uses comprehensive checks
- Consider caching dependencies (already configured)

### Tests fail in CI but pass locally

- Check environment variables in workflow
- Ensure PostgreSQL service is running
- Verify Python version matches (3.11)

## Adding New Checks

To add a new quality check:

1. Add tool to `app/backend/requirements.txt`
2. Add step to `python-quality.yml`
3. Test locally with `make quality-check`
4. Update this README

## Performance Optimization

Current optimizations:
- ✅ Pip cache enabled
- ✅ Path filters (only run on relevant changes)
- ✅ Fast workflow for feature branches
- ✅ Parallel jobs where possible

## Security

- Secrets are managed via GitHub Secrets
- No sensitive data in workflows
- Dependabot auto-merge only for minor/patch updates
