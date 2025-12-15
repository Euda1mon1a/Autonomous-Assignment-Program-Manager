***REMOVED*** Environment Setup Guide

This guide provides detailed instructions for setting up a local development environment for the Residency Scheduler application.

***REMOVED******REMOVED*** Table of Contents

1. [Prerequisites](***REMOVED***prerequisites)
2. [Quick Start with Docker](***REMOVED***quick-start-with-docker)
3. [Local Development Setup](***REMOVED***local-development-setup)
4. [Environment Configuration](***REMOVED***environment-configuration)
5. [Database Setup](***REMOVED***database-setup)
6. [Running the Application](***REMOVED***running-the-application)
7. [IDE Configuration](***REMOVED***ide-configuration)
8. [Troubleshooting](***REMOVED***troubleshooting)

---

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** Required Software

| Software | Minimum Version | Check Command |
|----------|-----------------|---------------|
| Git | 2.30+ | `git --version` |
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |

***REMOVED******REMOVED******REMOVED*** For Local Development (Without Docker)

| Software | Minimum Version | Check Command |
|----------|-----------------|---------------|
| Python | 3.11+ | `python --version` |
| Node.js | 20.0+ | `node --version` |
| npm | 10.0+ | `npm --version` |
| PostgreSQL | 15+ | `psql --version` |

***REMOVED******REMOVED******REMOVED*** Verify Prerequisites

```bash
***REMOVED*** Check all versions
git --version
docker --version
docker compose version

***REMOVED*** For local development
python --version
node --version
npm --version
psql --version
```

---

***REMOVED******REMOVED*** Quick Start with Docker

The fastest way to get a development environment running:

```bash
***REMOVED*** 1. Clone the repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

***REMOVED*** 2. Create environment file
cp .env.example .env

***REMOVED*** 3. Edit .env with secure values
***REMOVED*** - Set DB_PASSWORD to a secure password
***REMOVED*** - Set SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")

***REMOVED*** 4. Start all services
docker compose up -d

***REMOVED*** 5. Verify services are running
docker compose ps

***REMOVED*** 6. View logs (optional)
docker compose logs -f
```

***REMOVED******REMOVED******REMOVED*** Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| Backend | http://localhost:8000 | FastAPI application |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |

***REMOVED******REMOVED******REMOVED*** Docker Commands Reference

```bash
***REMOVED*** Start services
docker compose up -d

***REMOVED*** Stop services
docker compose down

***REMOVED*** Rebuild after code changes
docker compose up -d --build

***REMOVED*** View logs
docker compose logs -f backend    ***REMOVED*** Backend logs
docker compose logs -f frontend   ***REMOVED*** Frontend logs

***REMOVED*** Execute commands in containers
docker compose exec backend bash
docker compose exec frontend sh

***REMOVED*** Run database migrations
docker compose exec backend alembic upgrade head

***REMOVED*** Access PostgreSQL
docker compose exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Reset database (WARNING: destroys all data)
docker compose down -v
docker compose up -d
```

***REMOVED******REMOVED******REMOVED*** Development vs Production Docker

Use the development configuration for hot-reloading:

```bash
***REMOVED*** Development (with hot-reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

***REMOVED*** Production
docker compose up -d
```

---

***REMOVED******REMOVED*** Local Development Setup

For a more responsive development experience, run services locally.

***REMOVED******REMOVED******REMOVED*** Backend Setup

```bash
***REMOVED*** Navigate to backend directory
cd backend

***REMOVED*** Create Python virtual environment
python -m venv venv

***REMOVED*** Activate virtual environment
***REMOVED*** Linux/macOS:
source venv/bin/activate
***REMOVED*** Windows (PowerShell):
.\venv\Scripts\Activate.ps1
***REMOVED*** Windows (Command Prompt):
venv\Scripts\activate.bat

***REMOVED*** Upgrade pip
pip install --upgrade pip

***REMOVED*** Install dependencies
pip install -r requirements.txt

***REMOVED*** Install development dependencies (optional but recommended)
pip install black ruff mypy pytest pytest-cov pytest-asyncio

***REMOVED*** Verify installation
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
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

If not using Docker for the database:

**Linux (Ubuntu/Debian):**
```bash
***REMOVED*** Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

***REMOVED*** Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

***REMOVED*** Create database and user
sudo -u postgres psql
```

**macOS (Homebrew):**
```bash
***REMOVED*** Install PostgreSQL
brew install postgresql@15

***REMOVED*** Start PostgreSQL service
brew services start postgresql@15

***REMOVED*** Create database and user
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

***REMOVED******REMOVED*** Environment Configuration

***REMOVED******REMOVED******REMOVED*** Environment File

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

***REMOVED******REMOVED******REMOVED*** Required Variables

```bash
***REMOVED*** =============================================================================
***REMOVED*** Database Configuration
***REMOVED*** =============================================================================
DB_PASSWORD=your_secure_database_password

***REMOVED*** =============================================================================
***REMOVED*** Security Configuration
***REMOVED*** =============================================================================
***REMOVED*** Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_64_character_secret_key_here

***REMOVED*** =============================================================================
***REMOVED*** Application Settings
***REMOVED*** =============================================================================
DEBUG=true  ***REMOVED*** Set to false in production

***REMOVED*** =============================================================================
***REMOVED*** CORS Configuration
***REMOVED*** =============================================================================
CORS_ORIGINS=["http://localhost:3000"]

***REMOVED*** =============================================================================
***REMOVED*** Frontend Configuration
***REMOVED*** =============================================================================
NEXT_PUBLIC_API_URL=http://localhost:8000
```

***REMOVED******REMOVED******REMOVED*** Generate Secret Key

```bash
***REMOVED*** Python
python -c "import secrets; print(secrets.token_hex(32))"

***REMOVED*** OpenSSL
openssl rand -hex 32

***REMOVED*** Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

***REMOVED******REMOVED******REMOVED*** Environment-Specific Configuration

Create separate environment files for different contexts:

```bash
.env              ***REMOVED*** Local development (git-ignored)
.env.example      ***REMOVED*** Template (committed to git)
.env.test         ***REMOVED*** Testing configuration
.env.production   ***REMOVED*** Production configuration (git-ignored)
```

---

***REMOVED******REMOVED*** Database Setup

***REMOVED******REMOVED******REMOVED*** Run Migrations

```bash
***REMOVED*** With Docker
docker compose exec backend alembic upgrade head

***REMOVED*** Local development
cd backend
source venv/bin/activate
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Migration Commands

```bash
***REMOVED*** Check current migration state
alembic current

***REMOVED*** View migration history
alembic history --verbose

***REMOVED*** Create new migration (auto-generate from model changes)
alembic revision --autogenerate -m "description of changes"

***REMOVED*** Apply specific migration
alembic upgrade <revision_id>

***REMOVED*** Rollback one migration
alembic downgrade -1

***REMOVED*** Rollback to specific migration
alembic downgrade <revision_id>

***REMOVED*** Rollback all migrations
alembic downgrade base
```

***REMOVED******REMOVED******REMOVED*** Seed Data (Optional)

Create initial test data:

```bash
***REMOVED*** Access Python shell
docker compose exec backend python
***REMOVED*** or locally:
cd backend && source venv/bin/activate && python
```

```python
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

***REMOVED*** Create sample resident
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

***REMOVED******REMOVED*** Running the Application

***REMOVED******REMOVED******REMOVED*** Option 1: Full Docker Stack

```bash
***REMOVED*** Start everything
docker compose up -d

***REMOVED*** Access:
***REMOVED*** Frontend: http://localhost:3000
***REMOVED*** Backend: http://localhost:8000
```

***REMOVED******REMOVED******REMOVED*** Option 2: Hybrid (Docker DB + Local Services)

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

***REMOVED******REMOVED******REMOVED*** Option 3: Fully Local

Requires local PostgreSQL installation.

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate

***REMOVED*** Set database URL for local PostgreSQL
export DATABASE_URL=postgresql://scheduler:your_password@localhost:5432/residency_scheduler

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

***REMOVED******REMOVED******REMOVED*** First-Time Application Setup

1. Navigate to http://localhost:3000
2. Click "Register" to create the first user (becomes admin)
3. Log in with your credentials
4. Create rotation templates via Settings
5. Add residents and faculty via People page
6. Generate your first schedule

---

***REMOVED******REMOVED*** IDE Configuration

***REMOVED******REMOVED******REMOVED*** VS Code

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

***REMOVED******REMOVED******REMOVED*** PyCharm / IntelliJ

1. Open the project root directory
2. Configure Python interpreter:
   - Settings → Project → Python Interpreter
   - Add Interpreter → Existing → Select `backend/venv/bin/python`
3. Enable Black formatter:
   - Settings → Tools → Black → Enable on save
4. Configure ESLint for frontend:
   - Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Docker Issues

**Port already in use:**
```bash
***REMOVED*** Find process using port
lsof -i :3000
lsof -i :8000

***REMOVED*** Kill process
kill -9 <PID>

***REMOVED*** Or change ports in docker-compose.yml
```

**Container won't start:**
```bash
***REMOVED*** Check logs
docker compose logs backend
docker compose logs frontend

***REMOVED*** Rebuild images
docker compose build --no-cache

***REMOVED*** Remove all containers and volumes
docker compose down -v
docker compose up -d
```

**Permission denied:**
```bash
***REMOVED*** Add user to docker group (Linux)
sudo usermod -aG docker $USER
***REMOVED*** Log out and back in

***REMOVED*** Or fix file permissions
sudo chown -R $USER:$USER .
```

***REMOVED******REMOVED******REMOVED*** Backend Issues

**Database connection failed:**
```bash
***REMOVED*** Check PostgreSQL is running
docker compose ps db

***REMOVED*** Verify DATABASE_URL
docker compose exec backend python -c "from app.db.session import engine; print(engine.url)"

***REMOVED*** Test connection manually
psql postgresql://scheduler:password@localhost:5432/residency_scheduler
```

**Import errors:**
```bash
***REMOVED*** Ensure virtual environment is activated
source backend/venv/bin/activate

***REMOVED*** Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend

***REMOVED*** Reinstall dependencies
pip install -r requirements.txt
```

**Migration errors:**
```bash
***REMOVED*** Check current state
alembic current

***REMOVED*** View history
alembic history

***REMOVED*** Reset migrations (development only!)
alembic downgrade base
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Frontend Issues

**Module not found:**
```bash
***REMOVED*** Clear node_modules and reinstall
rm -rf node_modules
rm package-lock.json
npm install
```

**API connection failed:**
```bash
***REMOVED*** Verify backend is running
curl http://localhost:8000/health

***REMOVED*** Check NEXT_PUBLIC_API_URL in .env
***REMOVED*** Ensure no trailing slash
```

**Build errors:**
```bash
***REMOVED*** Clear Next.js cache
rm -rf .next
npm run dev
```

***REMOVED******REMOVED******REMOVED*** Common Solutions

| Problem | Solution |
|---------|----------|
| "EACCES permission denied" | Run with sudo or fix npm permissions |
| "ENOSPC: no space left" | Clear Docker images: `docker system prune -a` |
| "Connection refused" | Check service is running and port is correct |
| "Module not found" | Reinstall dependencies, check import paths |
| "Database does not exist" | Run migrations: `alembic upgrade head` |

---

***REMOVED******REMOVED*** Next Steps

After setup is complete:

1. Review [Architecture](./architecture.md) to understand the codebase
2. Read [Workflow](./workflow.md) for development practices
3. Check [Testing](./testing.md) for test guidelines
4. See [Code Style](./code-style.md) for conventions

---

*Last Updated: December 2024*
