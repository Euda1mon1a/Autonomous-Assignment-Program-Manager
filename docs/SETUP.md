***REMOVED*** Setup Guide

This guide provides detailed instructions for setting up the Residency Scheduler development environment.

***REMOVED******REMOVED*** Table of Contents

- [Prerequisites](***REMOVED***prerequisites)
- [Quick Start](***REMOVED***quick-start)
- [Docker Setup](***REMOVED***docker-setup)
- [Local Development Setup](***REMOVED***local-development-setup)
- [Environment Configuration](***REMOVED***environment-configuration)
- [Database Setup](***REMOVED***database-setup)
- [Running the Application](***REMOVED***running-the-application)
- [Running Tests](***REMOVED***running-tests)
- [Troubleshooting](***REMOVED***troubleshooting)

---

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Git | 2.30+ | Version control |
| Docker | 20.10+ | Containerization |
| Docker Compose | 2.0+ | Container orchestration |

***REMOVED******REMOVED******REMOVED*** For Local Development (Optional)

| Software | Version | Purpose |
|----------|---------|---------|
| Node.js | 20.0+ | Frontend runtime |
| npm | 10.0+ | Package manager |
| Python | 3.11+ | Backend runtime |
| PostgreSQL | 15+ | Database (if not using Docker) |

***REMOVED******REMOVED******REMOVED*** Verify Prerequisites

```bash
***REMOVED*** Check versions
git --version
docker --version
docker-compose --version

***REMOVED*** For local development
node --version
npm --version
python --version
psql --version
```

---

***REMOVED******REMOVED*** Quick Start

The fastest way to get started is with Docker:

```bash
***REMOVED*** 1. Clone the repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

***REMOVED*** 2. Copy environment file
cp .env.example .env

***REMOVED*** 3. Start all services
docker-compose up -d

***REMOVED*** 4. Verify services are running
docker-compose ps

***REMOVED*** 5. Access the application
***REMOVED*** Frontend: http://localhost:3000
***REMOVED*** Backend:  http://localhost:8000
***REMOVED*** API Docs: http://localhost:8000/docs
```

---

***REMOVED******REMOVED*** Docker Setup

***REMOVED******REMOVED******REMOVED*** Production Configuration

The default `docker-compose.yml` is configured for production:

```bash
***REMOVED*** Start services
docker-compose up -d

***REMOVED*** View logs
docker-compose logs -f

***REMOVED*** Stop services
docker-compose down

***REMOVED*** Stop and remove volumes (data will be lost)
docker-compose down -v
```

***REMOVED******REMOVED******REMOVED*** Development Configuration

Use the development configuration for hot-reloading:

```bash
***REMOVED*** Start with development config
docker-compose -f docker-compose.dev.yml up -d

***REMOVED*** Frontend changes will hot-reload
***REMOVED*** Backend changes will auto-restart
```

***REMOVED******REMOVED******REMOVED*** Service Details

| Service | Port | Description |
|---------|------|-------------|
| postgres | 5432 | PostgreSQL database |
| backend | 8000 | FastAPI application |
| frontend | 3000 | Next.js application |

***REMOVED******REMOVED******REMOVED*** Docker Commands

```bash
***REMOVED*** Build images
docker-compose build

***REMOVED*** Rebuild specific service
docker-compose build backend

***REMOVED*** View running containers
docker-compose ps

***REMOVED*** View logs for specific service
docker-compose logs -f backend

***REMOVED*** Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

***REMOVED*** Run database migrations manually
docker-compose exec backend alembic upgrade head

***REMOVED*** Access PostgreSQL
docker-compose exec postgres psql -U scheduler -d residency_scheduler
```

---

***REMOVED******REMOVED*** Local Development Setup

***REMOVED******REMOVED******REMOVED*** Backend Setup

```bash
***REMOVED*** Navigate to backend directory
cd backend

***REMOVED*** Create virtual environment
python -m venv venv

***REMOVED*** Activate virtual environment
***REMOVED*** Linux/macOS:
source venv/bin/activate
***REMOVED*** Windows:
venv\Scripts\activate

***REMOVED*** Install dependencies
pip install -r requirements.txt

***REMOVED*** Install development dependencies (optional)
pip install -r requirements-dev.txt

***REMOVED*** Verify installation
python -c "import fastapi; print(fastapi.__version__)"
```

***REMOVED******REMOVED******REMOVED*** Frontend Setup

```bash
***REMOVED*** Navigate to frontend directory
cd frontend

***REMOVED*** Install dependencies
npm install

***REMOVED*** Verify installation
npm list next react
```

***REMOVED******REMOVED******REMOVED*** Database Setup (Local PostgreSQL)

If running PostgreSQL locally instead of Docker:

```bash
***REMOVED*** Create database and user
sudo -u postgres psql

***REMOVED*** In PostgreSQL shell:
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

***REMOVED******REMOVED*** Environment Configuration

***REMOVED******REMOVED******REMOVED*** Environment File

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

***REMOVED******REMOVED******REMOVED*** Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PASSWORD` | - | PostgreSQL password |
| `SECRET_KEY` | - | JWT signing key (min 32 chars) |
| `DEBUG` | `false` | Enable debug mode |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

***REMOVED******REMOVED******REMOVED*** Example .env File

```bash
***REMOVED*** Database
DB_PASSWORD=secure_database_password_here

***REMOVED*** Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_super_secret_key_at_least_32_characters_long

***REMOVED*** Application
DEBUG=false

***REMOVED*** Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

***REMOVED******REMOVED******REMOVED*** Generate Secret Key

```bash
***REMOVED*** Linux/macOS
openssl rand -hex 32

***REMOVED*** Python
python -c "import secrets; print(secrets.token_hex(32))"
```

***REMOVED******REMOVED******REMOVED*** Backend Configuration

Additional backend settings in `backend/app/core/config.py`:

```python
***REMOVED*** Application
APP_NAME = "Residency Scheduler"
APP_VERSION = "1.0.0"

***REMOVED*** Database
DATABASE_URL = "postgresql://scheduler:password@localhost:5432/residency_scheduler"

***REMOVED*** Security
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  ***REMOVED*** 24 hours

***REMOVED*** CORS
CORS_ORIGINS = ["http://localhost:3000"]
```

---

***REMOVED******REMOVED*** Database Setup

***REMOVED******REMOVED******REMOVED*** Run Migrations

```bash
***REMOVED*** With Docker
docker-compose exec backend alembic upgrade head

***REMOVED*** Local development
cd backend
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Create New Migration

```bash
***REMOVED*** Generate migration from model changes
alembic revision --autogenerate -m "description of changes"

***REMOVED*** Apply migration
alembic upgrade head

***REMOVED*** Rollback one migration
alembic downgrade -1
```

***REMOVED******REMOVED******REMOVED*** Reset Database

```bash
***REMOVED*** With Docker (removes all data)
docker-compose down -v
docker-compose up -d

***REMOVED*** Local PostgreSQL
dropdb residency_scheduler
createdb residency_scheduler
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Seed Data (Optional)

```bash
***REMOVED*** Access backend shell
docker-compose exec backend python

***REMOVED*** In Python shell:
from app.db.session import SessionLocal
from app.models import Person, RotationTemplate

db = SessionLocal()

***REMOVED*** Create sample rotation template
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

***REMOVED******REMOVED*** Running the Application

***REMOVED******REMOVED******REMOVED*** With Docker (Recommended)

```bash
***REMOVED*** Start all services
docker-compose up -d

***REMOVED*** Access:
***REMOVED*** Frontend: http://localhost:3000
***REMOVED*** Backend: http://localhost:8000
***REMOVED*** API Docs: http://localhost:8000/docs
```

***REMOVED******REMOVED******REMOVED*** Local Development

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

***REMOVED******REMOVED******REMOVED*** First-Time Setup

1. Access the application at http://localhost:3000
2. Click "Register" to create the first user (becomes admin)
3. Log in with your credentials
4. Create rotation templates via Settings
5. Add residents and faculty via People page
6. Generate your first schedule

---

***REMOVED******REMOVED*** Running Tests

***REMOVED******REMOVED******REMOVED*** Backend Tests

```bash
***REMOVED*** With Docker
docker-compose exec backend pytest

***REMOVED*** Local development
cd backend
source venv/bin/activate

***REMOVED*** Run all tests
pytest

***REMOVED*** Run with coverage
pytest --cov=app --cov-report=html

***REMOVED*** Run specific test file
pytest tests/test_scheduling_engine.py

***REMOVED*** Run tests by marker
pytest -m unit        ***REMOVED*** Unit tests
pytest -m integration ***REMOVED*** Integration tests
pytest -m acgme       ***REMOVED*** ACGME compliance tests

***REMOVED*** Verbose output
pytest -v

***REMOVED*** Stop on first failure
pytest -x
```

***REMOVED******REMOVED******REMOVED*** Frontend Tests

```bash
***REMOVED*** With Docker
docker-compose exec frontend npm test

***REMOVED*** Local development
cd frontend

***REMOVED*** Run unit tests
npm test

***REMOVED*** Run with coverage
npm run test:coverage

***REMOVED*** Watch mode
npm run test:watch

***REMOVED*** E2E tests (requires running application)
npm run test:e2e

***REMOVED*** E2E with browser UI
npm run test:e2e:ui
```

***REMOVED******REMOVED******REMOVED*** Test Coverage Requirements

- Minimum 70% coverage for branches, functions, lines, and statements
- Coverage reports generated in:
  - Backend: `backend/htmlcov/index.html`
  - Frontend: `frontend/coverage/lcov-report/index.html`

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Common Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** Docker: Port Already in Use

```bash
***REMOVED*** Find process using port
lsof -i :3000
lsof -i :8000

***REMOVED*** Kill process
kill -9 <PID>

***REMOVED*** Or change ports in docker-compose.yml
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Docker: Container Won't Start

```bash
***REMOVED*** Check logs
docker-compose logs backend
docker-compose logs frontend

***REMOVED*** Rebuild images
docker-compose build --no-cache

***REMOVED*** Remove all containers and volumes
docker-compose down -v
docker-compose up -d
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend: Database Connection Failed

```bash
***REMOVED*** Check PostgreSQL is running
docker-compose ps postgres

***REMOVED*** Check connection settings in .env
***REMOVED*** Verify DATABASE_URL format:
***REMOVED*** postgresql://user:password@host:port/database

***REMOVED*** Test connection
docker-compose exec backend python -c "from app.db.session import engine; print(engine.url)"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend: Migration Failed

```bash
***REMOVED*** Check current migration state
alembic current

***REMOVED*** View migration history
alembic history

***REMOVED*** Reset migrations (development only)
alembic downgrade base
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Frontend: Module Not Found

```bash
***REMOVED*** Clear node_modules and reinstall
rm -rf node_modules
rm package-lock.json
npm install
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Frontend: API Connection Failed

```bash
***REMOVED*** Verify backend is running
curl http://localhost:8000/health

***REMOVED*** Check NEXT_PUBLIC_API_URL in .env
***REMOVED*** Ensure no trailing slash
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Permission Denied (Linux)

```bash
***REMOVED*** Docker socket permissions
sudo usermod -aG docker $USER
***REMOVED*** Log out and back in

***REMOVED*** File permissions
sudo chown -R $USER:$USER .
```

***REMOVED******REMOVED******REMOVED*** Getting Help

1. Check the [documentation](../docs/)
2. Search [existing issues](https://github.com/your-org/residency-scheduler/issues)
3. Create a new issue with:
   - Operating system and version
   - Docker/Node/Python versions
   - Full error message and stack trace
   - Steps to reproduce

***REMOVED******REMOVED******REMOVED*** Useful Commands

```bash
***REMOVED*** Check Docker system
docker system df
docker system prune -a

***REMOVED*** Check disk space
df -h

***REMOVED*** Monitor Docker resources
docker stats

***REMOVED*** Check network connectivity
docker network ls
docker network inspect residency-scheduler_default
```

---

***REMOVED******REMOVED*** Next Steps

After setup is complete:

1. Review [API Reference](API_REFERENCE.md) for endpoint documentation
2. Read [Architecture](ARCHITECTURE.md) for system overview
3. Check [Testing Guide](TESTING.md) for test conventions
4. See [Contributing Guide](../CONTRIBUTING.md) for development workflow
