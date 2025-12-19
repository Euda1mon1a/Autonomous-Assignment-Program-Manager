***REMOVED*** Comprehensive Installation Guide

> **Last Updated:** 2025-12-19
>
> **Purpose:** Complete installation instructions for Residency Scheduler on macOS, Linux, and Windows

---

***REMOVED******REMOVED*** Table of Contents

1. [Prerequisites](***REMOVED***prerequisites)
2. [Quick Start (Docker)](***REMOVED***quick-start-docker)
3. [Development Setup (Manual)](***REMOVED***development-setup-manual)
4. [Database Setup](***REMOVED***database-setup)
5. [Background Services](***REMOVED***background-services)
6. [Verification](***REMOVED***verification)
7. [Common Issues](***REMOVED***common-issues)
8. [Platform-Specific Notes](***REMOVED***platform-specific-notes)

---

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** Operating System Requirements

This application has been tested on:

- **macOS**: 11.0 (Big Sur) or later
- **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 34+, RHEL/CentOS 8+
- **Windows**: 10/11 with WSL2 (recommended) or native Windows

***REMOVED******REMOVED******REMOVED*** Required Software

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Docker & Docker Compose (Recommended)

**macOS:**
```bash
***REMOVED*** Install Docker Desktop from https://www.docker.com/products/docker-desktop
***REMOVED*** Or using Homebrew:
brew install --cask docker
```

**Linux (Ubuntu/Debian):**
```bash
***REMOVED*** Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

***REMOVED*** Install dependencies
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

***REMOVED*** Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

***REMOVED*** Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

***REMOVED*** Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

***REMOVED*** Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker
```

**Windows:**
```powershell
***REMOVED*** Install Docker Desktop with WSL2 backend
***REMOVED*** Download from: https://www.docker.com/products/docker-desktop

***REMOVED*** Or using Chocolatey:
choco install docker-desktop
```

**Verify Installation:**
```bash
docker --version
docker compose version
```

Expected output:
```
Docker version 24.0.0 or higher
Docker Compose version v2.20.0 or higher
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Git

**macOS:**
```bash
***REMOVED*** Using Homebrew
brew install git

***REMOVED*** Or install Xcode Command Line Tools
xcode-select --install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y git
```

**Windows:**
```powershell
***REMOVED*** Using Chocolatey
choco install git

***REMOVED*** Or download from: https://git-scm.com/download/win
```

**Verify:**
```bash
git --version
***REMOVED*** Expected: git version 2.30.0 or higher
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Node.js 18+ and npm (For Manual Setup)

**macOS:**
```bash
***REMOVED*** Using Homebrew
brew install node@18

***REMOVED*** Or using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install 18
nvm use 18
```

**Linux:**
```bash
***REMOVED*** Using NodeSource repository (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

***REMOVED*** Or using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install 18
nvm use 18
```

**Windows:**
```powershell
***REMOVED*** Download from: https://nodejs.org/en/download

***REMOVED*** Or using Chocolatey
choco install nodejs-lts
```

**Verify:**
```bash
node --version  ***REMOVED*** Expected: v18.0.0 or higher
npm --version   ***REMOVED*** Expected: 9.0.0 or higher
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Python 3.11+ (For Manual Setup)

**macOS:**
```bash
***REMOVED*** Using Homebrew
brew install python@3.11

***REMOVED*** Verify
python3.11 --version
```

**Linux (Ubuntu/Debian):**
```bash
***REMOVED*** Add deadsnakes PPA for latest Python
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update

***REMOVED*** Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

***REMOVED*** Verify
python3.11 --version
```

**Windows:**
```powershell
***REMOVED*** Download from: https://www.python.org/downloads/

***REMOVED*** Or using Chocolatey
choco install python --version=3.11.0

***REMOVED*** Verify
python --version
```

**Expected:** Python 3.11.0 or higher

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. PostgreSQL 15+ (For Manual Setup Only)

Only needed if running without Docker.

**macOS:**
```bash
***REMOVED*** Using Homebrew
brew install postgresql@15
brew services start postgresql@15

***REMOVED*** Add to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Linux (Ubuntu/Debian):**
```bash
***REMOVED*** Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update

***REMOVED*** Install PostgreSQL 15
sudo apt-get install -y postgresql-15 postgresql-contrib-15

***REMOVED*** Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
```powershell
***REMOVED*** Download installer from: https://www.postgresql.org/download/windows/

***REMOVED*** Or using Chocolatey
choco install postgresql15
```

**Verify:**
```bash
psql --version
***REMOVED*** Expected: psql (PostgreSQL) 15.0 or higher
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 6. Redis (For Manual Setup Only)

Only needed if running without Docker.

**macOS:**
```bash
***REMOVED*** Using Homebrew
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y redis-server

***REMOVED*** Start service
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**
```powershell
***REMOVED*** Redis is not officially supported on Windows
***REMOVED*** Use Docker or WSL2 instead

***REMOVED*** In WSL2:
sudo apt-get install redis-server
sudo service redis-server start
```

**Verify:**
```bash
redis-cli ping
***REMOVED*** Expected: PONG
```

***REMOVED******REMOVED******REMOVED*** Hardware Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB free space

**Recommended:**
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 20+ GB free space (SSD preferred)

**For Production:**
- CPU: 8+ cores
- RAM: 16+ GB
- Disk: 50+ GB SSD

---

***REMOVED******REMOVED*** Quick Start (Docker)

This is the **recommended** method for both development and production deployments.

***REMOVED******REMOVED******REMOVED*** Step 1: Clone the Repository

```bash
***REMOVED*** Clone repository
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git

***REMOVED*** Navigate to project directory
cd Autonomous-Assignment-Program-Manager
```

***REMOVED******REMOVED******REMOVED*** Step 2: Configure Environment Variables

```bash
***REMOVED*** Copy environment template
cp .env.example .env
```

Edit `.env` file with your settings:

```bash
***REMOVED*** Use your preferred text editor
nano .env
***REMOVED*** or
vim .env
***REMOVED*** or
code .env  ***REMOVED*** VS Code
```

**Required Configuration:**

```env
***REMOVED*** Database Password (REQUIRED)
***REMOVED*** Use a strong password - minimum 12 characters
DB_PASSWORD=your_secure_database_password_here

***REMOVED*** Secret Key (REQUIRED)
***REMOVED*** Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'
***REMOVED*** MUST be 64+ characters, random
SECRET_KEY=your_secret_key_here_generate_a_random_64_char_string

***REMOVED*** Redis Password (REQUIRED for production)
***REMOVED*** Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
REDIS_PASSWORD=your_redis_password_here_generate_a_random_string

***REMOVED*** Backend API URL for frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

***REMOVED*** CORS Origins (JSON array format)
CORS_ORIGINS=["http://localhost:3000"]

***REMOVED*** n8n Configuration (Optional - for workflow automation)
N8N_USER=admin
N8N_PASSWORD=your_n8n_password_here
N8N_WEBHOOK_URL=http://localhost:5678
```

**Generate Secure Secrets:**

```bash
***REMOVED*** Generate SECRET_KEY (64 characters)
python -c 'import secrets; print(secrets.token_urlsafe(64))'

***REMOVED*** Generate DB_PASSWORD
python -c 'import secrets; print(secrets.token_urlsafe(32))'

***REMOVED*** Generate REDIS_PASSWORD
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

***REMOVED******REMOVED******REMOVED*** Step 3: Start All Services

```bash
***REMOVED*** Start all containers in detached mode
docker compose up -d

***REMOVED*** Expected output:
***REMOVED*** [+] Running 8/8
***REMOVED***  ✔ Network residency-scheduler_app-network   Created
***REMOVED***  ✔ Volume "residency-scheduler_postgres_data" Created
***REMOVED***  ✔ Volume "residency-scheduler_redis_data"    Created
***REMOVED***  ✔ Container residency-scheduler-db           Started
***REMOVED***  ✔ Container residency-scheduler-redis        Started
***REMOVED***  ✔ Container residency-scheduler-backend      Started
***REMOVED***  ✔ Container residency-scheduler-celery-worker Started
***REMOVED***  ✔ Container residency-scheduler-celery-beat  Started
***REMOVED***  ✔ Container residency-scheduler-frontend     Started
```

***REMOVED******REMOVED******REMOVED*** Step 4: Initialize Database

```bash
***REMOVED*** Run database migrations
docker compose exec backend alembic upgrade head

***REMOVED*** Expected output:
***REMOVED*** INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
***REMOVED*** INFO  [alembic.runtime.migration] Will assume transactional DDL.
***REMOVED*** INFO  [alembic.runtime.migration] Running upgrade -> abc123, Initial schema
```

***REMOVED******REMOVED******REMOVED*** Step 5: Access the Application

Open your browser and navigate to:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **n8n Workflows** (optional): http://localhost:5678

**Default Admin Login** (if seed data is loaded):
- Email: `admin@example.com`
- Password: Check seed data script in `backend/app/db/seed.py`

***REMOVED******REMOVED******REMOVED*** Step 6: View Logs (Optional)

```bash
***REMOVED*** View all logs
docker compose logs -f

***REMOVED*** View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery-worker

***REMOVED*** View last 100 lines
docker compose logs --tail=100 backend
```

***REMOVED******REMOVED******REMOVED*** Step 7: Stop Services

```bash
***REMOVED*** Stop all containers
docker compose down

***REMOVED*** Stop and remove volumes (CAUTION: deletes data)
docker compose down -v
```

---

***REMOVED******REMOVED*** Development Setup (Manual)

For development without Docker, or when you need to run services individually.

***REMOVED******REMOVED******REMOVED*** Prerequisites Check

Before starting, ensure all required software is installed:

```bash
***REMOVED*** Check versions
python3.11 --version  ***REMOVED*** Should be 3.11.0+
node --version        ***REMOVED*** Should be 18.0.0+
npm --version         ***REMOVED*** Should be 9.0.0+
psql --version        ***REMOVED*** Should be PostgreSQL 15+
redis-cli --version   ***REMOVED*** Should be 6.0+
git --version         ***REMOVED*** Should be 2.30+
```

***REMOVED******REMOVED******REMOVED*** Backend Setup

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Navigate to Backend Directory

```bash
cd backend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Create Virtual Environment

```bash
***REMOVED*** Create virtual environment
python3.11 -m venv venv

***REMOVED*** Activate virtual environment
***REMOVED*** macOS/Linux:
source venv/bin/activate

***REMOVED*** Windows (Command Prompt):
venv\Scripts\activate.bat

***REMOVED*** Windows (PowerShell):
venv\Scripts\Activate.ps1
```

Your prompt should now show `(venv)` prefix.

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Install Dependencies

```bash
***REMOVED*** Install all requirements
pip install -r requirements.txt

***REMOVED*** This will install:
***REMOVED*** - FastAPI 0.124.4
***REMOVED*** - SQLAlchemy 2.0.45
***REMOVED*** - Pydantic 2.12.5
***REMOVED*** - Alembic 1.17.2
***REMOVED*** - And 50+ other dependencies
```

**Expected time:** 2-5 minutes depending on network speed.

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Configure Backend Environment

```bash
***REMOVED*** Copy backend environment template
cp .env.example .env
```

Edit `backend/.env`:

```env
***REMOVED*** Database Configuration
DATABASE_URL=postgresql://scheduler:your_password@localhost:5432/residency_scheduler
DB_PASSWORD=your_password

***REMOVED*** Security
SECRET_KEY=your_64_character_secret_key_here

***REMOVED*** Redis
REDIS_URL=redis://:your_redis_password@localhost:6379/0
REDIS_PASSWORD=your_redis_password

***REMOVED*** Celery
CELERY_BROKER_URL=redis://:your_redis_password@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:your_redis_password@localhost:6379/0

***REMOVED*** Application
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]

***REMOVED*** Rate Limiting
RATE_LIMIT_ENABLED=true
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 6. Create PostgreSQL Database

```bash
***REMOVED*** Create database user
***REMOVED*** macOS/Linux:
sudo -u postgres psql -c "CREATE USER scheduler WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE residency_scheduler OWNER scheduler;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;"

***REMOVED*** Or using psql directly:
psql -U postgres
```

In PostgreSQL shell:
```sql
CREATE USER scheduler WITH PASSWORD 'your_password';
CREATE DATABASE residency_scheduler OWNER scheduler;
GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;
\q
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 7. Run Database Migrations

```bash
***REMOVED*** Ensure you're in backend/ directory with venv activated
alembic upgrade head

***REMOVED*** Expected output:
***REMOVED*** INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
***REMOVED*** INFO  [alembic.runtime.migration] Will assume transactional DDL.
***REMOVED*** INFO  [alembic.runtime.migration] Running upgrade -> 123abc, initial schema
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 8. Start Backend Server

```bash
***REMOVED*** Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

***REMOVED*** Expected output:
***REMOVED*** INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
***REMOVED*** INFO:     Started reloader process [12345] using WatchFiles
***REMOVED*** INFO:     Started server process [12346]
***REMOVED*** INFO:     Waiting for application startup.
***REMOVED*** INFO:     Application startup complete.
```

**Backend is now running at:** http://localhost:8000

Test it:
```bash
curl http://localhost:8000/health
***REMOVED*** Expected: {"status":"healthy"}
```

***REMOVED******REMOVED******REMOVED*** Frontend Setup

Open a **new terminal window** (keep backend running).

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Navigate to Frontend Directory

```bash
cd frontend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Install Dependencies

```bash
***REMOVED*** Install npm packages
npm install

***REMOVED*** This will install:
***REMOVED*** - Next.js 14.0.4
***REMOVED*** - React 18.2.0
***REMOVED*** - TailwindCSS 3.3.0
***REMOVED*** - TypeScript 5.0+
***REMOVED*** - And 100+ other dependencies
```

**Expected time:** 2-5 minutes depending on network speed.

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Configure Frontend Environment

```bash
***REMOVED*** Copy frontend environment template
cp .env.example .env.local
```

Edit `frontend/.env.local`:

```env
***REMOVED*** Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

***REMOVED*** Optional: Analytics, monitoring, etc.
***REMOVED*** NEXT_PUBLIC_GA_ID=your_google_analytics_id
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Start Development Server

```bash
***REMOVED*** Start Next.js development server
npm run dev

***REMOVED*** Expected output:
***REMOVED***   ▲ Next.js 14.0.4
***REMOVED***   - Local:        http://localhost:3000
***REMOVED***   - Network:      http://192.168.1.x:3000
***REMOVED***
***REMOVED***  ✓ Ready in 2.5s
```

**Frontend is now running at:** http://localhost:3000

***REMOVED******REMOVED******REMOVED*** Backend Testing

```bash
***REMOVED*** In backend directory with venv activated
cd backend

***REMOVED*** Run all tests
pytest

***REMOVED*** Run with coverage
pytest --cov=app --cov-report=html

***REMOVED*** Run specific test file
pytest tests/test_auth.py

***REMOVED*** Run tests with verbose output
pytest -v

***REMOVED*** Run only ACGME compliance tests
pytest -m acgme
```

***REMOVED******REMOVED******REMOVED*** Frontend Testing

```bash
***REMOVED*** In frontend directory
cd frontend

***REMOVED*** Run all tests
npm test

***REMOVED*** Run with coverage
npm run test:coverage

***REMOVED*** Run in watch mode
npm run test:watch

***REMOVED*** Type checking
npm run type-check

***REMOVED*** Linting
npm run lint
npm run lint:fix
```

---

***REMOVED******REMOVED*** Database Setup

***REMOVED******REMOVED******REMOVED*** Manual PostgreSQL Configuration

If you need to configure PostgreSQL manually (not using Docker):

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Create Database and User

```bash
***REMOVED*** Connect as postgres superuser
sudo -u postgres psql

***REMOVED*** Or on macOS:
psql postgres
```

Execute these SQL commands:

```sql
-- Create user
CREATE USER scheduler WITH PASSWORD 'your_secure_password';

-- Create database
CREATE DATABASE residency_scheduler OWNER scheduler;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;

-- Connect to the database
\c residency_scheduler

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO scheduler;

-- Exit
\q
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Configure PostgreSQL Access (Linux)

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Add this line:
```
***REMOVED*** TYPE  DATABASE              USER       ADDRESS        METHOD
local   residency_scheduler   scheduler                 md5
host    residency_scheduler   scheduler  127.0.0.1/32   md5
host    residency_scheduler   scheduler  ::1/128        md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Test Connection

```bash
***REMOVED*** Test connection
psql -U scheduler -d residency_scheduler -h localhost

***REMOVED*** Enter password when prompted
***REMOVED*** You should see:
***REMOVED*** residency_scheduler=>
```

***REMOVED******REMOVED******REMOVED*** Running Migrations

```bash
***REMOVED*** Navigate to backend directory
cd backend

***REMOVED*** Activate virtual environment (if not already activated)
source venv/bin/activate

***REMOVED*** Check current migration status
alembic current

***REMOVED*** View migration history
alembic history

***REMOVED*** Upgrade to latest version
alembic upgrade head

***REMOVED*** Rollback one migration
alembic downgrade -1

***REMOVED*** Rollback to specific version
alembic downgrade abc123

***REMOVED*** Create new migration
alembic revision --autogenerate -m "Add new field to Person"
```

***REMOVED******REMOVED******REMOVED*** Loading Seed Data (Optional)

```bash
***REMOVED*** In backend directory with venv activated
cd backend

***REMOVED*** Run seed script (if available)
python -m app.db.seed

***REMOVED*** Or create sample data manually via API
```

***REMOVED******REMOVED******REMOVED*** Database Backup and Restore

**Backup:**
```bash
***REMOVED*** Using Docker
docker compose exec db pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

***REMOVED*** Manual installation
pg_dump -U scheduler -h localhost residency_scheduler > backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
***REMOVED*** Using Docker
docker compose exec -T db psql -U scheduler residency_scheduler < backup_20251219.sql

***REMOVED*** Manual installation
psql -U scheduler -h localhost residency_scheduler < backup_20251219.sql
```

---

***REMOVED******REMOVED*** Background Services

***REMOVED******REMOVED******REMOVED*** Redis Setup

Redis is used for:
- Celery message broker
- Session storage
- Rate limiting
- Caching

**Start Redis (Manual Installation):**

```bash
***REMOVED*** macOS
brew services start redis

***REMOVED*** Linux
sudo systemctl start redis-server

***REMOVED*** Windows (WSL2)
sudo service redis-server start

***REMOVED*** Verify
redis-cli ping
***REMOVED*** Expected: PONG
```

**Configure Redis Password:**

Edit Redis configuration:
```bash
***REMOVED*** macOS
nano /opt/homebrew/etc/redis.conf

***REMOVED*** Linux
sudo nano /etc/redis/redis.conf
```

Add/uncomment:
```
requirepass your_redis_password_here
```

Restart Redis:
```bash
***REMOVED*** macOS
brew services restart redis

***REMOVED*** Linux
sudo systemctl restart redis-server
```

Test with password:
```bash
redis-cli -a your_redis_password_here ping
***REMOVED*** Expected: PONG
```

***REMOVED******REMOVED******REMOVED*** Celery Workers

Celery is used for background tasks:
- Resilience health checks (every 15 minutes)
- N-1/N-2 contingency analysis (daily)
- Email notifications
- Schedule conflict detection

**Start Celery Worker:**

Open a new terminal window:

```bash
***REMOVED*** Navigate to backend
cd backend

***REMOVED*** Activate virtual environment
source venv/bin/activate

***REMOVED*** Start worker
celery -A app.core.celery_app worker --loglevel=info -Q default,resilience,notifications

***REMOVED*** Expected output:
***REMOVED***  -------------- celery@hostname v5.x.x
***REMOVED*** --- ***** -----
***REMOVED*** -- ******* ---- [config]
***REMOVED*** - *** --- * --- .> app:         app.core.celery_app
***REMOVED*** - ** ---------- .> transport:   redis://:**@localhost:6379/0
***REMOVED*** - ** ---------- .> results:     redis://:**@localhost:6379/0
***REMOVED*** - *** --- * --- .> concurrency: 8 (prefork)
***REMOVED*** -- ******* ---- .> task events: OFF
***REMOVED*** --- ***** -----
***REMOVED***  -------------- [queues]
***REMOVED***                 .> default           exchange=default(direct) key=default
***REMOVED***                 .> resilience        exchange=resilience(direct) key=resilience
***REMOVED***                 .> notifications     exchange=notifications(direct) key=notifications
```

**Start Celery Beat (Scheduler):**

Open another new terminal window:

```bash
***REMOVED*** Navigate to backend
cd backend

***REMOVED*** Activate virtual environment
source venv/bin/activate

***REMOVED*** Start beat scheduler
celery -A app.core.celery_app beat --loglevel=info

***REMOVED*** Expected output:
***REMOVED*** LocalTime -> 2025-12-19 10:00:00
***REMOVED*** Configuration ->
***REMOVED***     . broker -> redis://:**@localhost:6379/0
***REMOVED***     . loader -> celery.loaders.app.AppLoader
***REMOVED***     . scheduler -> celery.beat.PersistentScheduler
***REMOVED***     . db -> celerybeat-schedule
***REMOVED***     . logfile -> [stderr]@%INFO
***REMOVED***     . maxinterval -> 5.00 minutes (300s)
```

**Using Helper Script (Recommended):**

```bash
***REMOVED*** From project root
cd scripts

***REMOVED*** Make script executable (first time only)
chmod +x start-celery.sh

***REMOVED*** Start worker + beat together
./start-celery.sh both

***REMOVED*** Start worker only
./start-celery.sh worker

***REMOVED*** Start beat only
./start-celery.sh beat
```

**Verify Celery:**

```bash
***REMOVED*** In backend directory with venv activated
python verify_celery.py

***REMOVED*** Expected output:
***REMOVED*** ✓ Celery worker is running
***REMOVED*** ✓ Celery beat is running
***REMOVED*** ✓ Registered tasks: 15
```

**Monitor Celery:**

```bash
***REMOVED*** Inspect active tasks
celery -A app.core.celery_app inspect active

***REMOVED*** Inspect scheduled tasks
celery -A app.core.celery_app inspect scheduled

***REMOVED*** Inspect registered tasks
celery -A app.core.celery_app inspect registered

***REMOVED*** Worker statistics
celery -A app.core.celery_app inspect stats
```

---

***REMOVED******REMOVED*** Verification

***REMOVED******REMOVED******REMOVED*** Health Checks

After installation, verify all services are running:

**Backend Health:**
```bash
curl http://localhost:8000/health

***REMOVED*** Expected:
***REMOVED*** {"status":"healthy","timestamp":"2025-12-19T10:00:00.000Z"}
```

**Backend API Documentation:**

Open browser: http://localhost:8000/docs

You should see Swagger UI with all API endpoints.

**Frontend:**

Open browser: http://localhost:3000

You should see the login page.

**Database Connection:**
```bash
***REMOVED*** Using Docker
docker compose exec backend python -c "from app.db.session import engine; print('Connected' if engine else 'Failed')"

***REMOVED*** Manual installation
cd backend
source venv/bin/activate
python -c "from app.db.session import engine; print('Connected' if engine else 'Failed')"
```

**Redis Connection:**
```bash
redis-cli -a your_password ping
***REMOVED*** Expected: PONG
```

**Celery Workers:**
```bash
***REMOVED*** In backend directory with venv activated
celery -A app.core.celery_app inspect ping

***REMOVED*** Expected:
***REMOVED*** -> celery@hostname: OK
***REMOVED***     pong
```

***REMOVED******REMOVED******REMOVED*** Running Tests

**Backend Tests:**
```bash
cd backend
source venv/bin/activate

***REMOVED*** Run all tests
pytest

***REMOVED*** Expected output should show all tests passing:
***REMOVED*** ======================== test session starts =========================
***REMOVED*** collected 150 items
***REMOVED***
***REMOVED*** tests/test_auth.py::test_login ✓
***REMOVED*** tests/test_auth.py::test_register ✓
***REMOVED*** ...
***REMOVED*** ======================== 150 passed in 12.34s ========================
```

**Frontend Tests:**
```bash
cd frontend

***REMOVED*** Run tests
npm test

***REMOVED*** Expected output:
***REMOVED*** PASS  src/components/Login.test.tsx
***REMOVED*** PASS  src/components/Dashboard.test.tsx
***REMOVED*** ...
***REMOVED*** Test Suites: 25 passed, 25 total
***REMOVED*** Tests:       100 passed, 100 total
```

***REMOVED******REMOVED******REMOVED*** Service Status Check

**Docker:**
```bash
docker compose ps

***REMOVED*** Expected output:
***REMOVED*** NAME                                 STATUS              PORTS
***REMOVED*** residency-scheduler-backend          Up (healthy)        0.0.0.0:8000->8000/tcp
***REMOVED*** residency-scheduler-celery-beat      Up
***REMOVED*** residency-scheduler-celery-worker    Up (healthy)
***REMOVED*** residency-scheduler-db               Up (healthy)        5432/tcp
***REMOVED*** residency-scheduler-frontend         Up                  0.0.0.0:3000->3000/tcp
***REMOVED*** residency-scheduler-redis            Up (healthy)        6379/tcp
```

**Manual Installation:**
```bash
***REMOVED*** Check if all processes are running
pgrep -a uvicorn    ***REMOVED*** Backend
pgrep -a celery     ***REMOVED*** Celery worker & beat
pgrep -a node       ***REMOVED*** Frontend
pgrep -a postgres   ***REMOVED*** PostgreSQL
pgrep -a redis      ***REMOVED*** Redis
```

---

***REMOVED******REMOVED*** Common Issues

***REMOVED******REMOVED******REMOVED*** 1. Port Already in Use

**Error:**
```
Error: bind: address already in use
Error: Cannot assign requested address: 0.0.0.0:8000
```

**Solution:**

Find and kill the process using the port:

```bash
***REMOVED*** Find process on port 8000 (backend)
lsof -i :8000

***REMOVED*** Or on Linux
sudo netstat -tlnp | grep :8000

***REMOVED*** Kill the process
kill -9 <PID>

***REMOVED*** For frontend (port 3000)
lsof -i :3000
kill -9 <PID>

***REMOVED*** For PostgreSQL (port 5432)
lsof -i :5432
kill -9 <PID>
```

**Or change ports in configuration:**

Edit `docker-compose.yml` or `.env`:
```yaml
***REMOVED*** Change backend port
ports:
  - "8001:8000"  ***REMOVED*** Use 8001 instead

***REMOVED*** Update NEXT_PUBLIC_API_URL
NEXT_PUBLIC_API_URL=http://localhost:8001
```

***REMOVED******REMOVED******REMOVED*** 2. Database Connection Failed

**Error:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "localhost", port 5432 failed
```

**Solutions:**

**Check if PostgreSQL is running:**
```bash
***REMOVED*** Docker
docker compose ps db
docker compose up -d db

***REMOVED*** Manual installation (Linux)
sudo systemctl status postgresql
sudo systemctl start postgresql

***REMOVED*** macOS
brew services list
brew services start postgresql@15
```

**Check connection parameters:**
```bash
***REMOVED*** Test connection
psql -U scheduler -h localhost -d residency_scheduler

***REMOVED*** If connection fails, check:
***REMOVED*** 1. Username is correct (should be 'scheduler')
***REMOVED*** 2. Database exists
***REMOVED*** 3. Password matches .env file
***REMOVED*** 4. Host is correct (localhost or 127.0.0.1)
```

**Check pg_hba.conf (Manual installation only):**
```bash
***REMOVED*** Linux
sudo nano /etc/postgresql/15/main/pg_hba.conf

***REMOVED*** macOS
nano /opt/homebrew/var/postgresql@15/pg_hba.conf

***REMOVED*** Add if missing:
***REMOVED*** TYPE  DATABASE              USER       ADDRESS        METHOD
local   residency_scheduler   scheduler                 md5
host    residency_scheduler   scheduler  127.0.0.1/32   md5

***REMOVED*** Restart PostgreSQL
sudo systemctl restart postgresql  ***REMOVED*** Linux
brew services restart postgresql@15  ***REMOVED*** macOS
```

**Check if database exists:**
```bash
psql -U postgres -c "\l" | grep residency_scheduler

***REMOVED*** If not found, create it:
psql -U postgres -c "CREATE DATABASE residency_scheduler OWNER scheduler;"
```

***REMOVED******REMOVED******REMOVED*** 3. Redis Connection Failed

**Error:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Solution:**

```bash
***REMOVED*** Check if Redis is running
redis-cli ping

***REMOVED*** If not running, start it:

***REMOVED*** Docker
docker compose up -d redis

***REMOVED*** macOS
brew services start redis
brew services list

***REMOVED*** Linux
sudo systemctl start redis-server
sudo systemctl status redis-server

***REMOVED*** Windows (WSL2)
sudo service redis-server start
```

**Test Redis connection:**
```bash
***REMOVED*** Without password
redis-cli ping

***REMOVED*** With password
redis-cli -a your_redis_password ping

***REMOVED*** Expected: PONG
```

**Check Redis configuration:**
```bash
***REMOVED*** macOS
cat /opt/homebrew/etc/redis.conf | grep requirepass

***REMOVED*** Linux
cat /etc/redis/redis.conf | grep requirepass

***REMOVED*** Should match REDIS_PASSWORD in .env
```

***REMOVED******REMOVED******REMOVED*** 4. Node/Python Version Issues

**Error:**
```
Error: The engine "node" is incompatible with this module. Expected version ">=18.0.0".
```

**Solution:**

**Install correct Node.js version:**
```bash
***REMOVED*** Using nvm (recommended)
nvm install 18
nvm use 18
nvm alias default 18

***REMOVED*** Verify
node --version
***REMOVED*** Should be v18.x.x or higher
```

**Error:**
```
ImportError: This package requires Python 3.11 or higher
```

**Solution:**

```bash
***REMOVED*** Check Python version
python --version
python3 --version
python3.11 --version

***REMOVED*** If 3.11 not available, install it:

***REMOVED*** macOS
brew install python@3.11

***REMOVED*** Linux (Ubuntu/Debian)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv

***REMOVED*** Create venv with correct version
python3.11 -m venv venv
source venv/bin/activate
```

***REMOVED******REMOVED******REMOVED*** 5. Docker Memory Limits

**Error:**
```
ERROR: for backend  Cannot create container for service backend: insufficient memory
```

**Solution:**

Increase Docker memory allocation:

**Docker Desktop (macOS/Windows):**
1. Open Docker Desktop
2. Go to Settings → Resources
3. Increase Memory to at least 4 GB (8 GB recommended)
4. Click "Apply & Restart"

**Docker on Linux:**
```bash
***REMOVED*** Check current limits
docker info | grep Memory

***REMOVED*** Docker uses host memory by default on Linux
***REMOVED*** If containers are being killed, check system memory:
free -h

***REMOVED*** Check Docker container memory usage
docker stats
```

**Reduce memory usage by disabling some services:**

Create `docker-compose.override.yml`:
```yaml
version: '3.8'

services:
  ***REMOVED*** Disable n8n if not needed
  n8n:
    profiles:
      - optional
```

Run without optional services:
```bash
docker compose up -d
```

***REMOVED******REMOVED******REMOVED*** 6. Alembic Migration Errors

**Error:**
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Solution:**

```bash
***REMOVED*** Check current migration
cd backend
alembic current

***REMOVED*** Check migration history
alembic history

***REMOVED*** If database is ahead of code:
alembic downgrade <revision>

***REMOVED*** If code is ahead of database:
alembic upgrade head

***REMOVED*** If migrations are corrupted, reset (CAUTION: loses data):
alembic downgrade base
alembic upgrade head
```

**Error:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "persons" already exists
```

**Solution:**

```bash
***REMOVED*** Stamp current database state
alembic stamp head

***REMOVED*** Or if you need to recreate:
***REMOVED*** CAUTION: This drops all data
cd backend
python
>>> from app.db.base import Base
>>> from app.db.session import engine
>>> Base.metadata.drop_all(bind=engine)
>>> Base.metadata.create_all(bind=engine)
>>> exit()

***REMOVED*** Then run migrations
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** 7. Permission Denied Errors (Linux)

**Error:**
```
Permission denied: '/var/lib/postgresql/data'
```

**Solution:**

```bash
***REMOVED*** Fix Docker volume permissions
sudo chown -R 999:999 postgres_data/

***REMOVED*** Or recreate volumes
docker compose down -v
docker compose up -d
```

**Error:**
```bash
bash: ./start-celery.sh: Permission denied
```

**Solution:**
```bash
chmod +x scripts/start-celery.sh
chmod +x scripts/*.sh
```

***REMOVED******REMOVED******REMOVED*** 8. Frontend Build Errors

**Error:**
```
Error: Cannot find module 'next/babel'
```

**Solution:**

```bash
cd frontend

***REMOVED*** Remove node_modules and lock file
rm -rf node_modules package-lock.json

***REMOVED*** Clear npm cache
npm cache clean --force

***REMOVED*** Reinstall
npm install
```

**Error:**
```
TypeError: Cannot read property 'map' of undefined
```

**Solution:**

Check API connection:
```bash
***REMOVED*** Verify backend is running
curl http://localhost:8000/health

***REMOVED*** Check NEXT_PUBLIC_API_URL in .env.local
cat .env.local | grep NEXT_PUBLIC_API_URL

***REMOVED*** Should match backend URL
```

***REMOVED******REMOVED******REMOVED*** 9. Celery Worker Not Starting

**Error:**
```
[ERROR/MainProcess] consumer: Cannot connect to redis://localhost:6379/0
```

**Solution:**

```bash
***REMOVED*** Check Redis is running
redis-cli ping

***REMOVED*** Check CELERY_BROKER_URL in .env
cat backend/.env | grep CELERY_BROKER_URL

***REMOVED*** Should be: redis://:password@localhost:6379/0

***REMOVED*** Test connection
redis-cli -a your_password ping
```

**Error:**
```
ImportError: No module named 'app.core.celery_app'
```

**Solution:**

```bash
***REMOVED*** Ensure you're in backend directory
cd backend

***REMOVED*** Ensure venv is activated
source venv/bin/activate

***REMOVED*** Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

***REMOVED*** Try starting again
celery -A app.core.celery_app worker --loglevel=info
```

***REMOVED******REMOVED******REMOVED*** 10. CORS Errors in Browser

**Error in browser console:**
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solution:**

Update `backend/.env`:
```env
CORS_ORIGINS=["http://localhost:3000"]
```

Or for development (less secure):
```env
CORS_ORIGINS=["*"]
```

Restart backend:
```bash
***REMOVED*** Docker
docker compose restart backend

***REMOVED*** Manual
***REMOVED*** Ctrl+C to stop, then:
uvicorn app.main:app --reload
```

---

***REMOVED******REMOVED*** Platform-Specific Notes

***REMOVED******REMOVED******REMOVED*** macOS

**Apple Silicon (M1/M2/M3) Notes:**

Some Python packages may need Rosetta 2:
```bash
***REMOVED*** Install Rosetta 2 if needed
softwareupdate --install-rosetta

***REMOVED*** Use arch command if needed
arch -arm64 brew install python@3.11
```

**PostgreSQL installation:**
```bash
***REMOVED*** PostgreSQL binaries location
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

***REMOVED*** Add to ~/.zshrc for persistence
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
```

**Services management:**
```bash
***REMOVED*** List all services
brew services list

***REMOVED*** Start all required services
brew services start postgresql@15
brew services start redis

***REMOVED*** Stop services
brew services stop postgresql@15
brew services stop redis
```

***REMOVED******REMOVED******REMOVED*** Linux (Ubuntu/Debian)

**System dependencies:**
```bash
***REMOVED*** Install system dependencies
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    libpq-dev \
    python3.11-dev \
    libssl-dev \
    libffi-dev \
    libmagic1
```

**Service management:**
```bash
***REMOVED*** Enable services to start on boot
sudo systemctl enable postgresql
sudo systemctl enable redis-server

***REMOVED*** Check service status
sudo systemctl status postgresql
sudo systemctl status redis-server

***REMOVED*** View logs
sudo journalctl -u postgresql -f
sudo journalctl -u redis-server -f
```

***REMOVED******REMOVED******REMOVED*** Windows

**Windows Subsystem for Linux (WSL2) - Recommended:**

```powershell
***REMOVED*** Install WSL2
wsl --install

***REMOVED*** Set WSL2 as default
wsl --set-default-version 2

***REMOVED*** Install Ubuntu
wsl --install -d Ubuntu-22.04

***REMOVED*** Then follow Linux instructions inside WSL2
```

**Native Windows:**

- Use Docker Desktop (easier)
- Or install all dependencies natively:
  - Python from python.org
  - Node.js from nodejs.org
  - PostgreSQL from postgresql.org
  - Redis via WSL2 or Docker

**File path issues:**
```powershell
***REMOVED*** Use forward slashes or escaped backslashes
DATABASE_URL=postgresql://scheduler:password@localhost:5432/residency_scheduler

***REMOVED*** Not:
DATABASE_URL=postgresql://scheduler:password@localhost\:5432\residency_scheduler
```

**Line endings:**
```bash
***REMOVED*** Convert CRLF to LF for bash scripts
dos2unix scripts/start-celery.sh

***REMOVED*** Or in git
git config --global core.autocrlf input
```

---

***REMOVED******REMOVED*** Next Steps

After successful installation:

1. **Read the Quick Start Guide**: [docs/getting-started/quickstart.md](../getting-started/quickstart.md)
2. **Configure the Application**: [docs/getting-started/configuration.md](../getting-started/configuration.md)
3. **Review Architecture**: [docs/architecture/](../architecture/)
4. **API Documentation**: http://localhost:8000/docs
5. **User Guide**: [docs/user-guide/](../user-guide/)

***REMOVED******REMOVED******REMOVED*** Development Resources

- **CLAUDE.md**: Project development guidelines
- **TODO_TRACKER.md**: Implementation roadmap
- **Testing Guide**: Run `pytest` in backend, `npm test` in frontend
- **API Reference**: [docs/api/](../api/)

***REMOVED******REMOVED******REMOVED*** Production Deployment

For production deployment:

1. **Review Security Checklist**: [docs/deployment/security.md](../deployment/security.md)
2. **Configure SSL/TLS**: Set up reverse proxy (nginx/Caddy)
3. **Set up monitoring**: Prometheus + Grafana
4. **Configure backups**: Database backup strategy
5. **Review macOS deployment**: [docs/getting-started/macos-deploy.md](../getting-started/macos-deploy.md)

---

***REMOVED******REMOVED*** Getting Help

***REMOVED******REMOVED******REMOVED*** Documentation

- **Main README**: [README.md](../../README.md)
- **Troubleshooting**: [docs/troubleshooting.md](../troubleshooting.md)
- **API Documentation**: [docs/api/](../api/)
- **Architecture Docs**: [docs/architecture/](../architecture/)

***REMOVED******REMOVED******REMOVED*** Community

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions and share ideas

***REMOVED******REMOVED******REMOVED*** Logs and Debugging

**View all logs (Docker):**
```bash
docker compose logs -f
```

**Check specific service:**
```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery-worker
docker compose logs -f db
```

**Enter container for debugging:**
```bash
***REMOVED*** Backend
docker compose exec backend bash

***REMOVED*** Database
docker compose exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Redis
docker compose exec redis redis-cli -a your_password
```

---

***REMOVED******REMOVED*** Summary

You should now have:

- ✅ All prerequisites installed (Docker, Git, Node.js, Python, etc.)
- ✅ Repository cloned and configured
- ✅ Environment variables set up
- ✅ Services running (backend, frontend, database, Redis, Celery)
- ✅ Database initialized with migrations
- ✅ Application accessible at http://localhost:3000

**Verification Checklist:**

```bash
***REMOVED*** All should return success
curl http://localhost:8000/health  ***REMOVED*** Backend
curl http://localhost:3000         ***REMOVED*** Frontend
redis-cli -a password ping         ***REMOVED*** Redis
docker compose ps                  ***REMOVED*** All containers running
```

If you encounter any issues not covered here, check:
- [docs/troubleshooting.md](../troubleshooting.md)
- [GitHub Issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)

---

**Last Updated:** 2025-12-19
**Tested On:** macOS 14, Ubuntu 22.04, Windows 11 (WSL2)
**Docker Version:** 24.0.0+
**Docker Compose:** v2.20.0+
