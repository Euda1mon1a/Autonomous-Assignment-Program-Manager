***REMOVED*** Development Guide

Guide for contributing to Residency Scheduler.

---

***REMOVED******REMOVED*** Overview

Thank you for your interest in contributing! This guide covers everything you need to start developing.

---

***REMOVED******REMOVED*** Development Sections

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
***REMOVED******REMOVED******REMOVED*** :material-laptop: [Setup](setup.md)
Development environment setup.
</div>

<div class="feature-card" markdown>
***REMOVED******REMOVED******REMOVED*** :material-source-branch: [Contributing](contributing.md)
Contribution guidelines and workflow.
</div>

<div class="feature-card" markdown>
***REMOVED******REMOVED******REMOVED*** :material-test-tube: [Testing](testing.md)
Testing strategies and commands.
</div>

<div class="feature-card" markdown>
***REMOVED******REMOVED******REMOVED*** :material-format-paint: [Code Style](code-style.md)
Coding standards and conventions.
</div>

</div>

---

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

***REMOVED******REMOVED******REMOVED*** Setup

```bash
***REMOVED*** Clone repository
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager

***REMOVED*** Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

***REMOVED*** Frontend
cd ../frontend
npm install
```

***REMOVED******REMOVED******REMOVED*** Running Tests

```bash
***REMOVED*** Backend tests
cd backend
pytest

***REMOVED*** Frontend tests
cd frontend
npm test
```

---

***REMOVED******REMOVED*** Project Structure

```
residency-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/routes/       ***REMOVED*** API endpoints
│   │   ├── controllers/      ***REMOVED*** Request handlers
│   │   ├── services/         ***REMOVED*** Business logic
│   │   ├── repositories/     ***REMOVED*** Data access
│   │   ├── models/           ***REMOVED*** SQLAlchemy models
│   │   ├── schemas/          ***REMOVED*** Pydantic schemas
│   │   ├── scheduling/       ***REMOVED*** Scheduling engine
│   │   └── resilience/       ***REMOVED*** Resilience framework
│   ├── tests/                ***REMOVED*** Backend tests
│   └── alembic/              ***REMOVED*** Migrations
│
├── frontend/
│   ├── src/
│   │   ├── app/              ***REMOVED*** Next.js App Router
│   │   ├── features/         ***REMOVED*** Feature modules
│   │   ├── components/       ***REMOVED*** Reusable components
│   │   └── lib/              ***REMOVED*** Utilities
│   ├── __tests__/            ***REMOVED*** Frontend tests
│   └── e2e/                  ***REMOVED*** E2E tests
│
├── docs/                     ***REMOVED*** Documentation
└── docker-compose.yml        ***REMOVED*** Container orchestration
```

---

***REMOVED******REMOVED*** Contribution Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** your changes (`pytest`, `npm test`)
5. **Commit** with clear messages
6. **Push** to your fork
7. **Open** a Pull Request

---

***REMOVED******REMOVED*** Code Quality

***REMOVED******REMOVED******REMOVED*** Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on commit:

- **Ruff** - Python linting
- **Black** - Python formatting
- **MyPy** - Type checking
- **ESLint** - JavaScript/TypeScript linting

***REMOVED******REMOVED******REMOVED*** Test Coverage

Maintain 70%+ coverage:

```bash
***REMOVED*** Backend
pytest --cov=app --cov-report=html

***REMOVED*** Frontend
npm run test:coverage
```

---

***REMOVED******REMOVED*** Need Help?

- Read the [Architecture](../architecture/index.md) docs
- Check [existing issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)
- Open a discussion for questions
