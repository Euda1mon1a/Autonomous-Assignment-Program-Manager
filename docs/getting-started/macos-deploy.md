# macOS Deployment Guide

> **Complete guide for deploying Residency Scheduler on macOS via Terminal**
> **Last Updated:** 2025-12-18

This guide provides step-by-step instructions for deploying the entire Residency Scheduler stack on macOS using Terminal.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deploy (5 Minutes)](#quick-deploy-5-minutes)
3. [Full Local Development Setup](#full-local-development-setup)
4. [Verification](#verification)
5. [Optional Components](#optional-components)
6. [macOS-Specific Troubleshooting](#macos-specific-troubleshooting)
7. [Useful Commands Reference](#useful-commands-reference)

---

## Prerequisites

### Install Homebrew (Package Manager)

If you don't have Homebrew installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, follow the instructions to add Homebrew to your PATH (usually displayed at the end of installation).

### Install Required Software

```bash
# Install Git
brew install git

# Install Docker Desktop for macOS
brew install --cask docker

# Start Docker Desktop (required before using docker commands)
open -a Docker
```

**Wait for Docker Desktop to fully start** (you'll see the Docker icon in your menu bar become stable).

### Verify Installations

```bash
# Check versions
git --version          # Should be 2.x+
docker --version       # Should be 20.10+
docker-compose --version  # Should be 2.0+

# Verify Docker is running
docker info
```

---

## Quick Deploy (5 Minutes)

For the fastest deployment using Docker:

### Step 1: Clone the Repository

```bash
cd ~  # Or your preferred directory
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager
```

### Step 2: Configure Environment

```bash
# Copy the environment template
cp .env.example .env

# Generate a secure secret key
SECRET_KEY=$(openssl rand -hex 32)
echo "Generated SECRET_KEY: $SECRET_KEY"

# Edit .env file with your favorite editor
nano .env
# Or use VS Code: code .env
```

**Required `.env` settings:**

```env
# Database
DB_PASSWORD=your_secure_password_here

# Security (paste your generated SECRET_KEY)
SECRET_KEY=your_64_character_secret_key_here
WEBHOOK_SECRET=your_32_character_webhook_secret

# Frontend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Start All Services

```bash
# Build and start all containers
docker-compose up -d

# Watch the logs (Ctrl+C to exit log view)
docker-compose logs -f
```

### Step 4: Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Open frontend in browser
open http://localhost:3000

# Open API documentation
open http://localhost:8000/docs
```

**That's it!** Your Residency Scheduler is now running.

---

## Full Local Development Setup

For development with hot-reloading and debugging capabilities:

### Install Development Dependencies

```bash
# Install Python 3.11+
brew install python@3.11

# Install Node.js 18+
brew install node@18

# Install PostgreSQL 15
brew install postgresql@15

# Install Redis
brew install redis

# Optional: Install k6 for load testing
brew install k6
```

### Start Local Services

```bash
# Start PostgreSQL
brew services start postgresql@15

# Start Redis
brew services start redis

# Verify services are running
brew services list
```

### Setup Backend

```bash
cd backend

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create the database
createdb residency_scheduler

# Run database migrations
alembic upgrade head

# Copy backend environment file
cp .env.example .env

# Start development server with hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Setup Frontend (New Terminal)

```bash
cd frontend

# Install Node dependencies
npm install

# Copy frontend environment file
cp .env.example .env.local

# Start development server
npm run dev
```

### Start Celery Workers (New Terminal)

For background task processing:

```bash
cd backend
source venv/bin/activate

# Start worker and beat scheduler
../scripts/start-celery.sh both

# Or start them separately:
# Terminal 1: celery -A app.core.celery_app worker --loglevel=info
# Terminal 2: celery -A app.core.celery_app beat --loglevel=info
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Web application |
| Backend API | http://localhost:8000 | REST API |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API documentation |
| API Docs (ReDoc) | http://localhost:8000/redoc | Alternative API documentation |

---

## Verification

### Check Service Health

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Detailed health check
curl http://localhost:8000/health/ready

# Check database connection
docker-compose exec db psql -U scheduler -d residency_scheduler -c "SELECT 1;"
```

### Run Tests

```bash
# Backend tests
cd backend
source venv/bin/activate
pytest

# Frontend tests
cd frontend
npm test

# Run with coverage
pytest --cov=app --cov-report=html  # Backend
npm run test:coverage               # Frontend
```

### Create First Admin User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "YourSecurePassword123!",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

---

## Optional Components

### Load Testing with k6

```bash
# Install k6 (if not already installed)
brew install k6

# Navigate to load tests
cd load-tests

# Install npm dependencies
npm install

# Run smoke test
npm run test:smoke

# Run load test
npm run test:load
```

### Monitoring Stack (Prometheus + Grafana)

```bash
# Start monitoring services
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Access Grafana
open http://localhost:3001
# Default credentials: admin / admin
```

### n8n Workflow Automation

```bash
# Start n8n
docker-compose -f n8n/docker-compose.yml up -d

# Access n8n
open http://localhost:5678
```

---

## macOS-Specific Troubleshooting

### Docker Desktop Not Starting

**Symptom:** Docker commands fail with "Cannot connect to the Docker daemon"

**Solution:**

```bash
# Start Docker Desktop from Applications
open -a Docker

# Or start via command line
open --background -a Docker

# Wait for Docker to fully start (check menu bar icon)
# Then verify:
docker info
```

### Port Already in Use

**Symptom:** `Error: Address already in use`

**Solution:**

```bash
# Find process using the port (e.g., port 8000)
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --port 8001
```

### PostgreSQL Connection Refused

**Symptom:** `Connection refused to localhost:5432`

**Solution:**

```bash
# Check if PostgreSQL is running
brew services list

# Start PostgreSQL
brew services start postgresql@15

# Restart if needed
brew services restart postgresql@15

# Verify connection
psql -h localhost -U postgres -l
```

### Redis Connection Refused

**Symptom:** `Connection refused to localhost:6379`

**Solution:**

```bash
# Start Redis
brew services start redis

# Test connection
redis-cli ping
# Expected: PONG
```

### Homebrew Services Not Starting

**Symptom:** `brew services start` doesn't work

**Solution:**

```bash
# Check service status
brew services list

# View service logs
cat ~/Library/Logs/Homebrew/postgresql@15.log
cat ~/Library/Logs/Homebrew/redis.log

# Try running directly to see errors
/opt/homebrew/opt/postgresql@15/bin/postgres -D /opt/homebrew/var/postgresql@15
```

### Python Virtual Environment Issues

**Symptom:** `command not found: python` or wrong Python version

**Solution:**

```bash
# Check Python installations
which python3
python3 --version

# Use specific Python version
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify active Python
which python
python --version
```

### Node.js Version Issues

**Symptom:** Frontend build fails due to Node version

**Solution:**

```bash
# Check Node version
node --version

# Install correct version
brew install node@18

# Link the correct version
brew unlink node
brew link node@18

# Or use nvm for version management
brew install nvm
nvm install 18
nvm use 18
```

### File Permission Issues

**Symptom:** Permission denied errors

**Solution:**

```bash
# Fix ownership of project directory
sudo chown -R $(whoami) ~/Autonomous-Assignment-Program-Manager

# Fix Homebrew permissions
sudo chown -R $(whoami) /opt/homebrew
```

### Docker Compose Memory Issues

**Symptom:** Containers crash or run slowly

**Solution:**

1. Open Docker Desktop
2. Go to Settings (gear icon)
3. Click Resources
4. Increase Memory to at least 4GB
5. Click "Apply & Restart"

---

## Useful Commands Reference

### Docker Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend

# Restart a service
docker-compose restart backend

# Rebuild containers
docker-compose up -d --build

# Access container shell
docker-compose exec backend bash

# Access database
docker-compose exec db psql -U scheduler -d residency_scheduler

# Check resource usage
docker stats
```

### Development Commands

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload      # Start server
pytest                              # Run tests
alembic upgrade head               # Run migrations
alembic revision --autogenerate -m "description"  # Create migration

# Frontend
cd frontend
npm run dev                        # Start dev server
npm test                           # Run tests
npm run build                      # Production build
npm run lint:fix                   # Fix lint issues

# Celery
cd backend && source venv/bin/activate
../scripts/start-celery.sh both    # Start worker + beat
python verify_celery.py            # Verify Celery status
```

### Service Management (Homebrew)

```bash
# List all services
brew services list

# Start services
brew services start postgresql@15
brew services start redis

# Stop services
brew services stop postgresql@15
brew services stop redis

# Restart services
brew services restart postgresql@15
brew services restart redis
```

### Generate Secrets

```bash
# Generate SECRET_KEY (64 characters)
openssl rand -hex 32

# Or using Python
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Quick Reference Card

| Action | Command |
|--------|---------|
| **Start Docker** | `open -a Docker` |
| **Clone repo** | `git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git` |
| **Start all (Docker)** | `docker-compose up -d` |
| **View logs** | `docker-compose logs -f` |
| **Stop all** | `docker-compose down` |
| **Health check** | `curl http://localhost:8000/health` |
| **Open frontend** | `open http://localhost:3000` |
| **Open API docs** | `open http://localhost:8000/docs` |
| **Run backend tests** | `cd backend && pytest` |
| **Run frontend tests** | `cd frontend && npm test` |

---

## Next Steps

After successful deployment:

1. **Create admin account** - Register first user with admin role
2. **Configure academic year** - Set up scheduling periods
3. **Add personnel** - Import residents and faculty
4. **Create rotation templates** - Define rotation types
5. **Generate schedule** - Create your first schedule

See the [Quick Start Guide](quickstart.md) for detailed first steps.

---

## Related Documentation

- [Installation Guide](installation.md) - Platform-agnostic installation
- [Configuration](configuration.md) - Environment variables reference
- [Troubleshooting](../troubleshooting.md) - General troubleshooting
- [User Guide](../user-guide/index.md) - Using the application
- [Load Testing](../../load-tests/README.md) - Performance testing guide

---

**Need help?** Open an issue on [GitHub](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)
