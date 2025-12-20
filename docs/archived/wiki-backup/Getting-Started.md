# Getting Started

This guide will help you install, configure, and run the Residency Scheduler application.

---

## Prerequisites

### Required Software
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for version control

### For Local Development (Optional)
- **Python** 3.11+
- **Node.js** 18+ and **npm** 9+
- **PostgreSQL** 15
- **Redis** 7

---

## Installation

### Option 1: Docker (Recommended)

The easiest way to run Residency Scheduler is using Docker Compose.

```bash
# Clone the repository
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager

# Copy environment file
cp .env.example .env

# Edit configuration (see Configuration section)
nano .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database (requires PostgreSQL)
createdb residency_scheduler

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Celery Workers (Optional but Recommended)

```bash
cd backend

# Start Redis (required for Celery)
redis-server

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Start Celery beat scheduler (in another terminal)
celery -A app.core.celery_app beat --loglevel=info
```

---

## Initial Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

#### Required Settings

```env
# Database
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@localhost:5432/residency_scheduler

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_64_character_random_secret_key_here

# Frontend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Optional Settings

```env
# Application
DEBUG=false
APP_NAME=Residency Scheduler
APP_VERSION=1.0.0

# CORS (JSON array of allowed origins)
CORS_ORIGINS=["http://localhost:3000"]

# Token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

See [Configuration](Configuration) for all available options.

---

## Verify Installation

### Check Services

```bash
# Check all containers are running
docker-compose ps

# Expected output:
# NAME                    STATUS
# backend                 Up
# frontend                Up
# db                      Up
# redis                   Up
# celery-worker           Up
# celery-beat             Up
```

### Test Endpoints

```bash
# Backend health check
curl http://localhost:8000/health

# Expected: {"status": "healthy"}

# API documentation
open http://localhost:8000/docs
```

### Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

---

## First Steps

### 1. Create Admin Account

On first launch, create an administrator account:

```bash
# Using the API
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "secure_password",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

Or use the registration form in the web interface.

### 2. Configure Academic Year

1. Log in as admin
2. Navigate to **Settings** → **Academic Year**
3. Set the start and end dates for your academic year
4. Configure block settings (typically 730 blocks per year)

### 3. Add People

Add residents and faculty members:

1. Go to **People** → **Add Person**
2. Enter details:
   - Name
   - Email
   - Role (Resident/Faculty)
   - PGY Level (for residents)
   - Specialty
3. Save and repeat for all personnel

Or import from Excel:

1. Go to **Settings** → **Import Data**
2. Download the template
3. Fill in your data
4. Upload the completed file

### 4. Create Rotation Templates

Define your rotation types:

1. Go to **Templates** → **Create Template**
2. Configure:
   - Template name (e.g., "ICU", "Clinic", "Call")
   - Duration
   - Capacity limits
   - Required supervision ratios
3. Save the template

### 5. Generate Your First Schedule

1. Go to **Schedule** → **Generate**
2. Select:
   - Date range
   - Scheduling algorithm
   - Priority weights
3. Click **Generate Schedule**
4. Review the generated schedule
5. Check compliance violations
6. Export or publish

---

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_schedule_service.py

# Run ACGME compliance tests
pytest -m acgme
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E with UI
npm run test:e2e:ui
```

---

## Common Setup Issues

### Database Connection Failed

```
Error: Connection refused to localhost:5432
```

**Solution**: Ensure PostgreSQL is running:
```bash
# Docker
docker-compose up -d db

# Local
sudo systemctl start postgresql
```

### Redis Connection Failed

```
Error: Connection refused to localhost:6379
```

**Solution**: Start Redis:
```bash
# Docker
docker-compose up -d redis

# Local
redis-server
```

### Migration Errors

```
Error: Can't locate revision
```

**Solution**: Reset migrations:
```bash
cd backend
alembic downgrade base
alembic upgrade head
```

### Port Already in Use

```
Error: Address already in use: 8000
```

**Solution**: Find and kill the process:
```bash
lsof -i :8000
kill -9 <PID>
```

---

## Next Steps

- Read the [User Guide](User-Guide) to learn how to use the application
- Review [Architecture](Architecture) to understand the system design
- Check [Configuration](Configuration) for advanced settings
- See [Development](Development) if you want to contribute

---

## Platform-Specific Guides

### macOS Users

For a comprehensive macOS-specific deployment guide with Homebrew, Docker Desktop, and Terminal commands, see:

**[macOS Deploy Guide](../docs/getting-started/macos-deploy.md)** - Complete guide covering:
- Homebrew installation and prerequisites
- Docker Desktop setup
- Quick deploy (5 minutes)
- Full local development setup
- macOS-specific troubleshooting
- Useful commands reference

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](Troubleshooting) guide
2. Review logs: `docker-compose logs -f [service_name]`
3. Search existing [GitHub Issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)
4. Open a new issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs and error messages
   - Environment details
