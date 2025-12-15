# Environment Setup Guide

This guide provides detailed instructions for setting up a local development environment for the Residency Scheduler application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start with Docker](#quick-start-with-docker)
3. [Local Development Setup](#local-development-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Running the Application](#running-the-application)
7. [IDE Configuration](#ide-configuration)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Minimum Version | Check Command |
|----------|-----------------|---------------|
| Git | 2.30+ | `git --version` |
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |

### For Local Development (Without Docker)

| Software | Minimum Version | Check Command |
|----------|-----------------|---------------|
| Python | 3.11+ | `python --version` |
| Node.js | 20.0+ | `node --version` |
| npm | 10.0+ | `npm --version` |
| PostgreSQL | 15+ | `psql --version` |

### Verify Prerequisites

```bash
# Check all versions
git --version
docker --version
docker compose version

# For local development
python --version
node --version
npm --version
psql --version
```

---

## Quick Start with Docker

The fastest way to get a development environment running:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

# 2. Create environment file
cp .env.example .env

# 3. Edit .env with secure values
# - Set DB_PASSWORD to a secure password
# - Set SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")

# 4. Start all services
docker compose up -d

# 5. Verify services are running
docker compose ps

# 6. View logs (optional)
docker compose logs -f
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| Backend | http://localhost:8000 | FastAPI application |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |

### Docker Commands Reference

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Rebuild after code changes
docker compose up -d --build

# View logs
docker compose logs -f backend    # Backend logs
docker compose logs -f frontend   # Frontend logs

# Execute commands in containers
docker compose exec backend bash
docker compose exec frontend sh

# Run database migrations
docker compose exec backend alembic upgrade head

# Access PostgreSQL
docker compose exec db psql -U scheduler -d residency_scheduler

# Reset database (WARNING: destroys all data)
docker compose down -v
docker compose up -d
```

### Development vs Production Docker

Use the development configuration for hot-reloading:

```bash
# Development (with hot-reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production
docker compose up -d
```

---

## Local Development Setup

For a more responsive development experience, run services locally.

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
venv\Scripts\activate.bat

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional but recommended)
pip install black ruff mypy pytest pytest-cov pytest-asyncio

# Verify installation
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
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

If not using Docker for the database:

**Linux (Ubuntu/Debian):**
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

**macOS (Homebrew):**
```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create database and user
psql postgres
```

**In PostgreSQL shell:**
```sql
-- Create user
CREATE USER scheduler WITH PASSWORD 'your_secure_password';

-- Create database
CREATE DATABASE residency_scheduler OWNER scheduler;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;

-- Exit
\q
```

---

## Environment Configuration

### Environment File

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

### Required Variables

```bash
# =============================================================================
# Database Configuration
# =============================================================================
DB_PASSWORD=your_secure_database_password

# =============================================================================
# Security Configuration
# =============================================================================
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_64_character_secret_key_here

# =============================================================================
# Application Settings
# =============================================================================
DEBUG=true  # Set to false in production

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ORIGINS=["http://localhost:3000"]

# =============================================================================
# Frontend Configuration
# =============================================================================
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Generate Secret Key

```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL
openssl rand -hex 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Environment-Specific Configuration

Create separate environment files for different contexts:

```bash
.env              # Local development (git-ignored)
.env.example      # Template (committed to git)
.env.test         # Testing configuration
.env.production   # Production configuration (git-ignored)
```

---

## Database Setup

### Run Migrations

```bash
# With Docker
docker compose exec backend alembic upgrade head

# Local development
cd backend
source venv/bin/activate
alembic upgrade head
```

### Migration Commands

```bash
# Check current migration state
alembic current

# View migration history
alembic history --verbose

# Create new migration (auto-generate from model changes)
alembic revision --autogenerate -m "description of changes"

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### Seed Data (Optional)

Create initial test data:

```bash
# Access Python shell
docker compose exec backend python
# or locally:
cd backend && source venv/bin/activate && python
```

```python
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

# Create sample resident
resident = Person(
    name="Dr. Jane Smith",
    email="jane.smith@hospital.org",
    type="resident",
    pgy_level=2,
    is_active=True
)
db.add(resident)

db.commit()
print("Seed data created successfully!")
```

---

## Running the Application

### Option 1: Full Docker Stack

```bash
# Start everything
docker compose up -d

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### Option 2: Hybrid (Docker DB + Local Services)

**Terminal 1 - Database:**
```bash
docker compose up -d db
```

**Terminal 2 - Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 3: Fully Local

Requires local PostgreSQL installation.

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate

# Set database URL for local PostgreSQL
export DATABASE_URL=postgresql://scheduler:your_password@localhost:5432/residency_scheduler

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### First-Time Application Setup

1. Navigate to http://localhost:3000
2. Click "Register" to create the first user (becomes admin)
3. Log in with your credentials
4. Create rotation templates via Settings
5. Add residents and faculty via People page
6. Generate your first schedule

---

## IDE Configuration

### VS Code

**Recommended Extensions:**

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode"
  ]
}
```

**Workspace Settings (.vscode/settings.json):**

```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "editor.tabSize": 2,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

### PyCharm / IntelliJ

1. Open the project root directory
2. Configure Python interpreter:
   - Settings → Project → Python Interpreter
   - Add Interpreter → Existing → Select `backend/venv/bin/python`
3. Enable Black formatter:
   - Settings → Tools → Black → Enable on save
4. Configure ESLint for frontend:
   - Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint

---

## Troubleshooting

### Docker Issues

**Port already in use:**
```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change ports in docker-compose.yml
```

**Container won't start:**
```bash
# Check logs
docker compose logs backend
docker compose logs frontend

# Rebuild images
docker compose build --no-cache

# Remove all containers and volumes
docker compose down -v
docker compose up -d
```

**Permission denied:**
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Log out and back in

# Or fix file permissions
sudo chown -R $USER:$USER .
```

### Backend Issues

**Database connection failed:**
```bash
# Check PostgreSQL is running
docker compose ps db

# Verify DATABASE_URL
docker compose exec backend python -c "from app.db.session import engine; print(engine.url)"

# Test connection manually
psql postgresql://scheduler:password@localhost:5432/residency_scheduler
```

**Import errors:**
```bash
# Ensure virtual environment is activated
source backend/venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

# Reinstall dependencies
pip install -r requirements.txt
```

**Migration errors:**
```bash
# Check current state
alembic current

# View history
alembic history

# Reset migrations (development only!)
alembic downgrade base
alembic upgrade head
```

### Frontend Issues

**Module not found:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules
rm package-lock.json
npm install
```

**API connection failed:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check NEXT_PUBLIC_API_URL in .env
# Ensure no trailing slash
```

**Build errors:**
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

### Common Solutions

| Problem | Solution |
|---------|----------|
| "EACCES permission denied" | Run with sudo or fix npm permissions |
| "ENOSPC: no space left" | Clear Docker images: `docker system prune -a` |
| "Connection refused" | Check service is running and port is correct |
| "Module not found" | Reinstall dependencies, check import paths |
| "Database does not exist" | Run migrations: `alembic upgrade head` |

---

## Next Steps

After setup is complete:

1. Review [Architecture](./architecture.md) to understand the codebase
2. Read [Workflow](./workflow.md) for development practices
3. Check [Testing](./testing.md) for test guidelines
4. See [Code Style](./code-style.md) for conventions

---

*Last Updated: December 2024*
