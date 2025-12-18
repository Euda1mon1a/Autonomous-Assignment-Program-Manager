***REMOVED*** macOS Deployment Guide

> **Complete guide for deploying Residency Scheduler on macOS via Terminal**
> **Last Updated:** 2025-12-18

This guide provides step-by-step instructions for deploying the entire Residency Scheduler stack on macOS using Terminal.

---

***REMOVED******REMOVED*** Table of Contents

1. [Prerequisites](***REMOVED***prerequisites)
2. [Quick Deploy (5 Minutes)](***REMOVED***quick-deploy-5-minutes)
3. [Full Local Development Setup](***REMOVED***full-local-development-setup)
4. [Verification](***REMOVED***verification)
5. [Optional Components](***REMOVED***optional-components)
6. [macOS-Specific Troubleshooting](***REMOVED***macos-specific-troubleshooting)
7. [Useful Commands Reference](***REMOVED***useful-commands-reference)

---

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** Install Homebrew (Package Manager)

If you don't have Homebrew installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, follow the instructions to add Homebrew to your PATH (usually displayed at the end of installation).

***REMOVED******REMOVED******REMOVED*** Install Required Software

```bash
***REMOVED*** Install Git
brew install git

***REMOVED*** Install Docker Desktop for macOS
brew install --cask docker

***REMOVED*** Start Docker Desktop (required before using docker commands)
open -a Docker
```

**Wait for Docker Desktop to fully start** (you'll see the Docker icon in your menu bar become stable).

***REMOVED******REMOVED******REMOVED*** Verify Installations

```bash
***REMOVED*** Check versions
git --version          ***REMOVED*** Should be 2.x+
docker --version       ***REMOVED*** Should be 20.10+
docker-compose --version  ***REMOVED*** Should be 2.0+

***REMOVED*** Verify Docker is running
docker info
```

---

***REMOVED******REMOVED*** Quick Deploy (5 Minutes)

For the fastest deployment using Docker:

***REMOVED******REMOVED******REMOVED*** Step 1: Clone the Repository

```bash
cd ~  ***REMOVED*** Or your preferred directory
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager
```

***REMOVED******REMOVED******REMOVED*** Step 2: Configure Environment

```bash
***REMOVED*** Copy the environment template
cp .env.example .env

***REMOVED*** Generate a secure secret key
SECRET_KEY=$(openssl rand -hex 32)
echo "Generated SECRET_KEY: $SECRET_KEY"

***REMOVED*** Edit .env file with your favorite editor
nano .env
***REMOVED*** Or use VS Code: code .env
```

**Required `.env` settings:**

```env
***REMOVED*** Database
DB_PASSWORD=your_secure_password_here

***REMOVED*** Security (paste your generated SECRET_KEY)
SECRET_KEY=your_64_character_secret_key_here
WEBHOOK_SECRET=your_32_character_webhook_secret

***REMOVED*** Frontend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

***REMOVED******REMOVED******REMOVED*** Step 3: Start All Services

```bash
***REMOVED*** Build and start all containers
docker-compose up -d

***REMOVED*** Watch the logs (Ctrl+C to exit log view)
docker-compose logs -f
```

***REMOVED******REMOVED******REMOVED*** Step 4: Verify Deployment

```bash
***REMOVED*** Check all services are running
docker-compose ps

***REMOVED*** Test backend health
curl http://localhost:8000/health

***REMOVED*** Open frontend in browser
open http://localhost:3000

***REMOVED*** Open API documentation
open http://localhost:8000/docs
```

**That's it!** Your Residency Scheduler is now running.

---

***REMOVED******REMOVED*** Full Local Development Setup

For development with hot-reloading and debugging capabilities:

***REMOVED******REMOVED******REMOVED*** Install Development Dependencies

```bash
***REMOVED*** Install Python 3.11+
brew install python@3.11

***REMOVED*** Install Node.js 18+
brew install node@18

***REMOVED*** Install PostgreSQL 15
brew install postgresql@15

***REMOVED*** Install Redis
brew install redis

***REMOVED*** Optional: Install k6 for load testing
brew install k6
```

***REMOVED******REMOVED******REMOVED*** Start Local Services

```bash
***REMOVED*** Start PostgreSQL
brew services start postgresql@15

***REMOVED*** Start Redis
brew services start redis

***REMOVED*** Verify services are running
brew services list
```

***REMOVED******REMOVED******REMOVED*** Setup Backend

```bash
cd backend

***REMOVED*** Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

***REMOVED*** Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

***REMOVED*** Create the database
createdb residency_scheduler

***REMOVED*** Run database migrations
alembic upgrade head

***REMOVED*** Copy backend environment file
cp .env.example .env

***REMOVED*** Start development server with hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

***REMOVED******REMOVED******REMOVED*** Setup Frontend (New Terminal)

```bash
cd frontend

***REMOVED*** Install Node dependencies
npm install

***REMOVED*** Copy frontend environment file
cp .env.example .env.local

***REMOVED*** Start development server
npm run dev
```

***REMOVED******REMOVED******REMOVED*** Start Celery Workers (New Terminal)

For background task processing:

```bash
cd backend
source venv/bin/activate

***REMOVED*** Start worker and beat scheduler
../scripts/start-celery.sh both

***REMOVED*** Or start them separately:
***REMOVED*** Terminal 1: celery -A app.core.celery_app worker --loglevel=info
***REMOVED*** Terminal 2: celery -A app.core.celery_app beat --loglevel=info
```

***REMOVED******REMOVED******REMOVED*** Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Web application |
| Backend API | http://localhost:8000 | REST API |
| API Docs (Swagger) | http://localhost:8000/docs | Interactive API documentation |
| API Docs (ReDoc) | http://localhost:8000/redoc | Alternative API documentation |

---

***REMOVED******REMOVED*** Verification

***REMOVED******REMOVED******REMOVED*** Check Service Health

```bash
***REMOVED*** Backend health check
curl http://localhost:8000/health
***REMOVED*** Expected: {"status": "healthy"}

***REMOVED*** Detailed health check
curl http://localhost:8000/health/ready

***REMOVED*** Check database connection
docker-compose exec db psql -U scheduler -d residency_scheduler -c "SELECT 1;"
```

***REMOVED******REMOVED******REMOVED*** Run Tests

```bash
***REMOVED*** Backend tests
cd backend
source venv/bin/activate
pytest

***REMOVED*** Frontend tests
cd frontend
npm test

***REMOVED*** Run with coverage
pytest --cov=app --cov-report=html  ***REMOVED*** Backend
npm run test:coverage               ***REMOVED*** Frontend
```

***REMOVED******REMOVED******REMOVED*** Create First Admin User

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

***REMOVED******REMOVED*** Optional Components

***REMOVED******REMOVED******REMOVED*** Load Testing with k6

```bash
***REMOVED*** Install k6 (if not already installed)
brew install k6

***REMOVED*** Navigate to load tests
cd load-tests

***REMOVED*** Install npm dependencies
npm install

***REMOVED*** Run smoke test
npm run test:smoke

***REMOVED*** Run load test
npm run test:load
```

***REMOVED******REMOVED******REMOVED*** Monitoring Stack (Prometheus + Grafana)

```bash
***REMOVED*** Start monitoring services
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

***REMOVED*** Access Grafana
open http://localhost:3001
***REMOVED*** Default credentials: admin / admin
```

***REMOVED******REMOVED******REMOVED*** n8n Workflow Automation

```bash
***REMOVED*** Start n8n
docker-compose -f n8n/docker-compose.yml up -d

***REMOVED*** Access n8n
open http://localhost:5678
```

---

***REMOVED******REMOVED*** macOS-Specific Troubleshooting

***REMOVED******REMOVED******REMOVED*** Docker Desktop Not Starting

**Symptom:** Docker commands fail with "Cannot connect to the Docker daemon"

**Solution:**

```bash
***REMOVED*** Start Docker Desktop from Applications
open -a Docker

***REMOVED*** Or start via command line
open --background -a Docker

***REMOVED*** Wait for Docker to fully start (check menu bar icon)
***REMOVED*** Then verify:
docker info
```

***REMOVED******REMOVED******REMOVED*** Port Already in Use

**Symptom:** `Error: Address already in use`

**Solution:**

```bash
***REMOVED*** Find process using the port (e.g., port 8000)
lsof -i :8000

***REMOVED*** Kill the process
kill -9 <PID>

***REMOVED*** Or use a different port
uvicorn app.main:app --port 8001
```

***REMOVED******REMOVED******REMOVED*** PostgreSQL Connection Refused

**Symptom:** `Connection refused to localhost:5432`

**Solution:**

```bash
***REMOVED*** Check if PostgreSQL is running
brew services list

***REMOVED*** Start PostgreSQL
brew services start postgresql@15

***REMOVED*** Restart if needed
brew services restart postgresql@15

***REMOVED*** Verify connection
psql -h localhost -U postgres -l
```

***REMOVED******REMOVED******REMOVED*** Redis Connection Refused

**Symptom:** `Connection refused to localhost:6379`

**Solution:**

```bash
***REMOVED*** Start Redis
brew services start redis

***REMOVED*** Test connection
redis-cli ping
***REMOVED*** Expected: PONG
```

***REMOVED******REMOVED******REMOVED*** Homebrew Services Not Starting

**Symptom:** `brew services start` doesn't work

**Solution:**

```bash
***REMOVED*** Check service status
brew services list

***REMOVED*** View service logs
cat ~/Library/Logs/Homebrew/postgresql@15.log
cat ~/Library/Logs/Homebrew/redis.log

***REMOVED*** Try running directly to see errors
/opt/homebrew/opt/postgresql@15/bin/postgres -D /opt/homebrew/var/postgresql@15
```

***REMOVED******REMOVED******REMOVED*** Python Virtual Environment Issues

**Symptom:** `command not found: python` or wrong Python version

**Solution:**

```bash
***REMOVED*** Check Python installations
which python3
python3 --version

***REMOVED*** Use specific Python version
python3.11 -m venv venv

***REMOVED*** Activate virtual environment
source venv/bin/activate

***REMOVED*** Verify active Python
which python
python --version
```

***REMOVED******REMOVED******REMOVED*** Node.js Version Issues

**Symptom:** Frontend build fails due to Node version

**Solution:**

```bash
***REMOVED*** Check Node version
node --version

***REMOVED*** Install correct version
brew install node@18

***REMOVED*** Link the correct version
brew unlink node
brew link node@18

***REMOVED*** Or use nvm for version management
brew install nvm
nvm install 18
nvm use 18
```

***REMOVED******REMOVED******REMOVED*** File Permission Issues

**Symptom:** Permission denied errors

**Solution:**

```bash
***REMOVED*** Fix ownership of project directory
sudo chown -R $(whoami) ~/Autonomous-Assignment-Program-Manager

***REMOVED*** Fix Homebrew permissions
sudo chown -R $(whoami) /opt/homebrew
```

***REMOVED******REMOVED******REMOVED*** Docker Compose Memory Issues

**Symptom:** Containers crash or run slowly

**Solution:**

1. Open Docker Desktop
2. Go to Settings (gear icon)
3. Click Resources
4. Increase Memory to at least 4GB
5. Click "Apply & Restart"

---

***REMOVED******REMOVED*** Useful Commands Reference

***REMOVED******REMOVED******REMOVED*** Docker Commands

```bash
***REMOVED*** Start all services
docker-compose up -d

***REMOVED*** Stop all services
docker-compose down

***REMOVED*** View logs (all services)
docker-compose logs -f

***REMOVED*** View logs (specific service)
docker-compose logs -f backend

***REMOVED*** Restart a service
docker-compose restart backend

***REMOVED*** Rebuild containers
docker-compose up -d --build

***REMOVED*** Access container shell
docker-compose exec backend bash

***REMOVED*** Access database
docker-compose exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Check resource usage
docker stats
```

***REMOVED******REMOVED******REMOVED*** Development Commands

```bash
***REMOVED*** Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload      ***REMOVED*** Start server
pytest                              ***REMOVED*** Run tests
alembic upgrade head               ***REMOVED*** Run migrations
alembic revision --autogenerate -m "description"  ***REMOVED*** Create migration

***REMOVED*** Frontend
cd frontend
npm run dev                        ***REMOVED*** Start dev server
npm test                           ***REMOVED*** Run tests
npm run build                      ***REMOVED*** Production build
npm run lint:fix                   ***REMOVED*** Fix lint issues

***REMOVED*** Celery
cd backend && source venv/bin/activate
../scripts/start-celery.sh both    ***REMOVED*** Start worker + beat
python verify_celery.py            ***REMOVED*** Verify Celery status
```

***REMOVED******REMOVED******REMOVED*** Service Management (Homebrew)

```bash
***REMOVED*** List all services
brew services list

***REMOVED*** Start services
brew services start postgresql@15
brew services start redis

***REMOVED*** Stop services
brew services stop postgresql@15
brew services stop redis

***REMOVED*** Restart services
brew services restart postgresql@15
brew services restart redis
```

***REMOVED******REMOVED******REMOVED*** Generate Secrets

```bash
***REMOVED*** Generate SECRET_KEY (64 characters)
openssl rand -hex 32

***REMOVED*** Or using Python
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

***REMOVED******REMOVED*** Quick Reference Card

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

***REMOVED******REMOVED*** Next Steps

After successful deployment:

1. **Create admin account** - Register first user with admin role
2. **Configure academic year** - Set up scheduling periods
3. **Add personnel** - Import residents and faculty
4. **Create rotation templates** - Define rotation types
5. **Generate schedule** - Create your first schedule

See the [Quick Start Guide](quickstart.md) for detailed first steps.

---

***REMOVED******REMOVED*** Related Documentation

- [Installation Guide](installation.md) - Platform-agnostic installation
- [Configuration](configuration.md) - Environment variables reference
- [Troubleshooting](../troubleshooting.md) - General troubleshooting
- [User Guide](../user-guide/index.md) - Using the application
- [Load Testing](../../load-tests/README.md) - Performance testing guide

---

**Need help?** Open an issue on [GitHub](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)
