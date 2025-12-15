# Setup Guide

This guide provides detailed instructions for setting up the Residency Scheduler development environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Setup](#docker-setup)
- [Local Development Setup](#local-development-setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Git | 2.30+ | Version control |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Container orchestration |

### For Local Development (Optional)

| Software | Version | Purpose |
|----------|---------|---------|
| Node.js | 20.0+ | Frontend runtime |
| npm | 10.0+ | Package manager |
| Python | 3.11+ | Backend runtime |
| PostgreSQL | 15+ | Database (if not using Docker) |

### Verify Prerequisites

```bash
# Check versions
git --version
docker --version
docker-compose --version

# For local development
node --version
npm --version
python --version
psql --version
```

---

## Quick Start

The fastest way to get started is with Docker:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Verify services are running
docker-compose ps

# 5. Access the application
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## Docker Setup

### Production Configuration

The default `docker-compose.yml` is configured for production:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (data will be lost)
docker-compose down -v
```

### Development Configuration

Use the development configuration for hot-reloading:

```bash
# Start with development config
docker-compose -f docker-compose.dev.yml up -d

# Frontend changes will hot-reload
# Backend changes will auto-restart
```

### Service Details

| Service | Port | Description |
|---------|------|-------------|
| postgres | 5432 | PostgreSQL database |
| backend | 8000 | FastAPI application |
| frontend | 3000 | Next.js application |

### Docker Commands

```bash
# Build images
docker-compose build

# Rebuild specific service
docker-compose build backend

# View running containers
docker-compose ps

# View logs for specific service
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

# Run database migrations manually
docker-compose exec backend alembic upgrade head

# Access PostgreSQL
docker-compose exec postgres psql -U scheduler -d residency_scheduler
```

---

## Local Development Setup

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Verify installation
npm list next react
```

### Database Setup (Local PostgreSQL)

If running PostgreSQL locally instead of Docker:

```bash
# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE residency_scheduler;
CREATE USER scheduler WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;
\q
```

Update your `.env` file:
```bash
DATABASE_URL=postgresql://scheduler:your_password@localhost:5432/residency_scheduler
```

---

## Environment Configuration

### Environment File

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PASSWORD` | - | PostgreSQL password |
| `SECRET_KEY` | - | JWT signing key (min 32 chars) |
| `DEBUG` | `false` | Enable debug mode |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

### Example .env File

```bash
# Database
DB_PASSWORD=secure_database_password_here

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_super_secret_key_at_least_32_characters_long

# Application
DEBUG=false

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Generate Secret Key

```bash
# Linux/macOS
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Backend Configuration

Additional backend settings in `backend/app/core/config.py`:

```python
# Application
APP_NAME = "Residency Scheduler"
APP_VERSION = "1.0.0"

# Database
DATABASE_URL = "postgresql://scheduler:password@localhost:5432/residency_scheduler"

# Security
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# CORS
CORS_ORIGINS = ["http://localhost:3000"]
```

---

## Database Setup

### Run Migrations

```bash
# With Docker
docker-compose exec backend alembic upgrade head

# Local development
cd backend
alembic upgrade head
```

### Create New Migration

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Apply migration
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Reset Database

```bash
# With Docker (removes all data)
docker-compose down -v
docker-compose up -d

# Local PostgreSQL
dropdb residency_scheduler
createdb residency_scheduler
alembic upgrade head
```

### Seed Data (Optional)

```bash
# Access backend shell
docker-compose exec backend python

# In Python shell:
from app.db.session import SessionLocal
from app.models import Person, RotationTemplate

db = SessionLocal()

# Create sample rotation template
template = RotationTemplate(
    name="Morning Clinic",
    activity_type="clinic",
    abbreviation="MC",
    max_residents=4,
    requires_supervision=True
)
db.add(template)
db.commit()
```

---

## Running the Application

### With Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

Terminal 1 - Database (if using Docker for DB only):
```bash
docker-compose up -d postgres
```

Terminal 2 - Backend:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 3 - Frontend:
```bash
cd frontend
npm run dev
```

### First-Time Setup

1. Access the application at http://localhost:3000
2. Click "Register" to create the first user (becomes admin)
3. Log in with your credentials
4. Create rotation templates via Settings
5. Add residents and faculty via People page
6. Generate your first schedule

---

## Running Tests

### Backend Tests

```bash
# With Docker
docker-compose exec backend pytest

# Local development
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_scheduling_engine.py

# Run tests by marker
pytest -m unit        # Unit tests
pytest -m integration # Integration tests
pytest -m acgme       # ACGME compliance tests

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Frontend Tests

```bash
# With Docker
docker-compose exec frontend npm test

# Local development
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch

# E2E tests (requires running application)
npm run test:e2e

# E2E with browser UI
npm run test:e2e:ui
```

### Test Coverage Requirements

- Minimum 70% coverage for branches, functions, lines, and statements
- Coverage reports generated in:
  - Backend: `backend/htmlcov/index.html`
  - Frontend: `frontend/coverage/lcov-report/index.html`

---

## Troubleshooting

### Common Issues

#### Docker: Port Already in Use

```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
```

#### Docker: Container Won't Start

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild images
docker-compose build --no-cache

# Remove all containers and volumes
docker-compose down -v
docker-compose up -d
```

#### Backend: Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection settings in .env
# Verify DATABASE_URL format:
# postgresql://user:password@host:port/database

# Test connection
docker-compose exec backend python -c "from app.db.session import engine; print(engine.url)"
```

#### Backend: Migration Failed

```bash
# Check current migration state
alembic current

# View migration history
alembic history

# Reset migrations (development only)
alembic downgrade base
alembic upgrade head
```

#### Frontend: Module Not Found

```bash
# Clear node_modules and reinstall
rm -rf node_modules
rm package-lock.json
npm install
```

#### Frontend: API Connection Failed

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check NEXT_PUBLIC_API_URL in .env
# Ensure no trailing slash
```

#### Permission Denied (Linux)

```bash
# Docker socket permissions
sudo usermod -aG docker $USER
# Log out and back in

# File permissions
sudo chown -R $USER:$USER .
```

### Getting Help

1. Check the [documentation](../docs/)
2. Search [existing issues](https://github.com/your-org/residency-scheduler/issues)
3. Create a new issue with:
   - Operating system and version
   - Docker/Node/Python versions
   - Full error message and stack trace
   - Steps to reproduce

### Useful Commands

```bash
# Check Docker system
docker system df
docker system prune -a

# Check disk space
df -h

# Monitor Docker resources
docker stats

# Check network connectivity
docker network ls
docker network inspect residency-scheduler_default
```

---

## Next Steps

After setup is complete:

1. Review [API Reference](API_REFERENCE.md) for endpoint documentation
2. Read [Architecture](ARCHITECTURE.md) for system overview
3. Check [Testing Guide](TESTING.md) for test conventions
4. See [Contributing Guide](../CONTRIBUTING.md) for development workflow
