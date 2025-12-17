# Development Guide

Guide for contributing to Residency Scheduler.

---

## Overview

Thank you for your interest in contributing! This guide covers everything you need to start developing.

---

## Development Sections

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-laptop: [Setup](setup.md)
Development environment setup.
</div>

<div class="feature-card" markdown>
### :material-source-branch: [Contributing](contributing.md)
Contribution guidelines and workflow.
</div>

<div class="feature-card" markdown>
### :material-test-tube: [Testing](testing.md)
Testing strategies and commands.
</div>

<div class="feature-card" markdown>
### :material-format-paint: [Code Style](code-style.md)
Coding standards and conventions.
</div>

</div>

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

---

## Project Structure

```
residency-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # API endpoints
│   │   ├── controllers/      # Request handlers
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Data access
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── scheduling/       # Scheduling engine
│   │   └── resilience/       # Resilience framework
│   ├── tests/                # Backend tests
│   └── alembic/              # Migrations
│
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   ├── features/         # Feature modules
│   │   ├── components/       # Reusable components
│   │   └── lib/              # Utilities
│   ├── __tests__/            # Frontend tests
│   └── e2e/                  # E2E tests
│
├── docs/                     # Documentation
└── docker-compose.yml        # Container orchestration
```

---

## Contribution Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** your changes (`pytest`, `npm test`)
5. **Commit** with clear messages
6. **Push** to your fork
7. **Open** a Pull Request

---

## Code Quality

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on commit:

- **Ruff** - Python linting
- **Black** - Python formatting
- **MyPy** - Type checking
- **ESLint** - JavaScript/TypeScript linting

### Test Coverage

Maintain 70%+ coverage:

```bash
# Backend
pytest --cov=app --cov-report=html

# Frontend
npm run test:coverage
```

---

## Need Help?

- Read the [Architecture](../architecture/index.md) docs
- Check [existing issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)
- Open a discussion for questions
