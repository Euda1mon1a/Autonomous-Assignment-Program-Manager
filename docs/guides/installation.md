# Comprehensive Installation Guide

> **Last Updated:** 2025-12-19
>
> **Purpose:** Complete installation instructions for Residency Scheduler on macOS, Linux, and Windows

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Development Setup (Manual)](#development-setup-manual)
4. [Database Setup](#database-setup)
5. [Background Services](#background-services)
6. [Verification](#verification)
7. [Common Issues](#common-issues)
8. [Platform-Specific Notes](#platform-specific-notes)

---

## Prerequisites

### Operating System Requirements

This application has been tested on:

- **macOS**: 11.0 (Big Sur) or later
- **Linux**: Ubuntu 20.04+, Debian 11+, Fedora 34+, RHEL/CentOS 8+
- **Windows**: 10/11 with WSL2 (recommended) or native Windows

### Required Software

#### 1. Docker & Docker Compose (Recommended)

**macOS:**
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
# Or using Homebrew:
brew install --cask docker
```

**Linux (Ubuntu/Debian):**
```bash
# Remove old versions
sudo apt-get remove docker docker-engine docker.io containerd runc

# Install dependencies
sudo apt-get update
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker
```

**Windows:**
```powershell
# Install Docker Desktop with WSL2 backend
# Download from: https://www.docker.com/products/docker-desktop

# Or using Chocolatey:
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

#### 2. Git

**macOS:**
```bash
# Using Homebrew
brew install git

# Or install Xcode Command Line Tools
xcode-select --install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y git
```

**Windows:**
```powershell
# Using Chocolatey
choco install git

# Or download from: https://git-scm.com/download/win
```

**Verify:**
```bash
git --version
# Expected: git version 2.30.0 or higher
```

#### 3. Node.js 18+ and npm (For Manual Setup)

**macOS:**
```bash
# Using Homebrew
brew install node@18

# Or using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install 18
nvm use 18
```

**Linux:**
```bash
# Using NodeSource repository (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Or using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install 18
nvm use 18
```

**Windows:**
```powershell
# Download from: https://nodejs.org/en/download

# Or using Chocolatey
choco install nodejs-lts
```

**Verify:**
```bash
node --version  # Expected: v18.0.0 or higher
npm --version   # Expected: 9.0.0 or higher
```

#### 4. Python 3.11+ (For Manual Setup)

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Verify
python3.11 --version
```

**Linux (Ubuntu/Debian):**
```bash
# Add deadsnakes PPA for latest Python
sudo apt-get update
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Verify
python3.11 --version
```

**Windows:**
```powershell
# Download from: https://www.python.org/downloads/

# Or using Chocolatey
choco install python --version=3.11.0

# Verify
python --version
```

**Expected:** Python 3.11.0 or higher

#### 5. PostgreSQL 15+ (For Manual Setup Only)

Only needed if running without Docker.

**macOS:**
```bash
# Using Homebrew
brew install postgresql@15
brew services start postgresql@15

# Add to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Linux (Ubuntu/Debian):**
```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update

# Install PostgreSQL 15
sudo apt-get install -y postgresql-15 postgresql-contrib-15

# Start service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
```powershell
# Download installer from: https://www.postgresql.org/download/windows/

# Or using Chocolatey
choco install postgresql15
```

**Verify:**
```bash
psql --version
# Expected: psql (PostgreSQL) 15.0 or higher
```

#### 6. Redis (For Manual Setup Only)

Only needed if running without Docker.

**macOS:**
```bash
# Using Homebrew
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y redis-server

# Start service
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**
```powershell
# Redis is not officially supported on Windows
# Use Docker or WSL2 instead

# In WSL2:
sudo apt-get install redis-server
sudo service redis-server start
```

**Verify:**
```bash
redis-cli ping
# Expected: PONG
```

### Hardware Requirements

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

## Quick Start (Docker)

This is the **recommended** method for both development and production deployments.

### Step 1: Clone the Repository

```bash
# Clone repository
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git

# Navigate to project directory
cd Autonomous-Assignment-Program-Manager
```

### Step 2: Configure Environment Variables

```bash
# Copy environment template
cp .env.example .env
```

Edit `.env` file with your settings:

```bash
# Use your preferred text editor
nano .env
# or
vim .env
# or
code .env  # VS Code
```

**Required Configuration:**

```env
# Database Password (REQUIRED)
# Use a strong password - minimum 12 characters
DB_PASSWORD=your_secure_database_password_here

# Secret Key (REQUIRED)
# Generate with: python -c 'import secrets; print(secrets.token_urlsafe(64))'
# MUST be 64+ characters, random
SECRET_KEY=your_secret_key_here_generate_a_random_64_char_string

# Redis Password (REQUIRED for production)
# Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
REDIS_PASSWORD=your_redis_password_here_generate_a_random_string

# Backend API URL for frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# CORS Origins (JSON array format)
CORS_ORIGINS=["http://localhost:3000"]

# n8n Configuration (Optional - for workflow automation)
N8N_USER=admin
N8N_PASSWORD=your_n8n_password_here
N8N_WEBHOOK_URL=http://localhost:5678
```

**Generate Secure Secrets:**

```bash
# Generate SECRET_KEY (64 characters)
python -c 'import secrets; print(secrets.token_urlsafe(64))'

# Generate DB_PASSWORD
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# Generate REDIS_PASSWORD
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### Step 3: Start All Services

```bash
# Start all containers in detached mode
docker compose up -d

# Expected output:
# [+] Running 8/8
#  ✔ Network residency-scheduler_app-network   Created
#  ✔ Volume "residency-scheduler_postgres_data" Created
#  ✔ Volume "residency-scheduler_redis_data"    Created
#  ✔ Container residency-scheduler-db           Started
#  ✔ Container residency-scheduler-redis        Started
#  ✔ Container residency-scheduler-backend      Started
#  ✔ Container residency-scheduler-celery-worker Started
#  ✔ Container residency-scheduler-celery-beat  Started
#  ✔ Container residency-scheduler-frontend     Started
```

### Step 4: Initialize Database

```bash
# Run database migrations
docker compose exec backend alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade -> abc123, Initial schema
```

### Step 5: Access the Application

Open your browser and navigate to:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **n8n Workflows** (optional): http://localhost:5678

**Default Admin Login** (if seed data is loaded):
- Email: `admin@example.com`
- Password: Check seed data script in `backend/app/db/seed.py`

### Step 6: View Logs (Optional)

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f celery-worker

# View last 100 lines
docker compose logs --tail=100 backend
```

### Step 7: Stop Services

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (CAUTION: deletes data)
docker compose down -v
```

---

## Development Setup (Manual)

For development without Docker, or when you need to run services individually.

### Prerequisites Check

Before starting, ensure all required software is installed:

```bash
# Check versions
python3.11 --version  # Should be 3.11.0+
node --version        # Should be 18.0.0+
npm --version         # Should be 9.0.0+
psql --version        # Should be PostgreSQL 15+
redis-cli --version   # Should be 6.0+
git --version         # Should be 2.30+
```

### Backend Setup

#### 1. Navigate to Backend Directory

```bash
cd backend
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

Your prompt should now show `(venv)` prefix.

#### 3. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

#### 4. Install Dependencies

```bash
# Install all requirements
pip install -r requirements.txt

# This will install:
# - FastAPI 0.124.4
# - SQLAlchemy 2.0.45
# - Pydantic 2.12.5
# - Alembic 1.17.2
# - And 50+ other dependencies
```

**Expected time:** 2-5 minutes depending on network speed.

#### 5. Configure Backend Environment

```bash
# Copy backend environment template
cp .env.example .env
```

Edit `backend/.env`:

```env
# Database Configuration
DATABASE_URL=postgresql://scheduler:your_password@localhost:5432/residency_scheduler
DB_PASSWORD=your_password

# Security
SECRET_KEY=your_64_character_secret_key_here

# Redis
REDIS_URL=redis://:your_redis_password@localhost:6379/0
REDIS_PASSWORD=your_redis_password

# Celery
CELERY_BROKER_URL=redis://:your_redis_password@localhost:6379/0
CELERY_RESULT_BACKEND=redis://:your_redis_password@localhost:6379/0

# Application
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

#### 6. Create PostgreSQL Database

```bash
# Create database user
# macOS/Linux:
sudo -u postgres psql -c "CREATE USER scheduler WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE residency_scheduler OWNER scheduler;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;"

# Or using psql directly:
psql -U postgres
```

In PostgreSQL shell:
```sql
CREATE USER scheduler WITH PASSWORD 'your_password';
CREATE DATABASE residency_scheduler OWNER scheduler;
GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;
\q
```

#### 7. Run Database Migrations

```bash
# Ensure you're in backend/ directory with venv activated
alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade -> 123abc, initial schema
```

#### 8. Start Backend Server

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process [12345] using WatchFiles
# INFO:     Started server process [12346]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

**Backend is now running at:** http://localhost:8000

Test it:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### Frontend Setup

Open a **new terminal window** (keep backend running).

#### 1. Navigate to Frontend Directory

```bash
cd frontend
```

#### 2. Install Dependencies

```bash
# Install npm packages
npm install

# This will install:
# - Next.js 14.0.4
# - React 18.2.0
# - TailwindCSS 3.3.0
# - TypeScript 5.0+
# - And 100+ other dependencies
```

**Expected time:** 2-5 minutes depending on network speed.

#### 3. Configure Frontend Environment

```bash
# Copy frontend environment template
cp .env.example .env.local
```

Edit `frontend/.env.local`:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics, monitoring, etc.
# NEXT_PUBLIC_GA_ID=your_google_analytics_id
```

#### 4. Start Development Server

```bash
# Start Next.js development server
npm run dev

# Expected output:
#   ▲ Next.js 14.0.4
#   - Local:        http://localhost:3000
#   - Network:      http://192.168.1.x:3000
#
#  ✓ Ready in 2.5s
```

**Frontend is now running at:** http://localhost:3000

### Backend Testing

```bash
# In backend directory with venv activated
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run tests with verbose output
pytest -v

# Run only ACGME compliance tests
pytest -m acgme
```

### Frontend Testing

```bash
# In frontend directory
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix
```

---

## Database Setup

### Manual PostgreSQL Configuration

If you need to configure PostgreSQL manually (not using Docker):

#### 1. Create Database and User

```bash
# Connect as postgres superuser
sudo -u postgres psql

# Or on macOS:
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

#### 2. Configure PostgreSQL Access (Linux)

Edit `/etc/postgresql/15/main/pg_hba.conf`:

```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Add this line:
```
# TYPE  DATABASE              USER       ADDRESS        METHOD
local   residency_scheduler   scheduler                 md5
host    residency_scheduler   scheduler  127.0.0.1/32   md5
host    residency_scheduler   scheduler  ::1/128        md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

#### 3. Test Connection

```bash
# Test connection
psql -U scheduler -d residency_scheduler -h localhost

# Enter password when prompted
# You should see:
# residency_scheduler=>
```

### Running Migrations

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if not already activated)
source venv/bin/activate

# Check current migration status
alembic current

# View migration history
alembic history

# Upgrade to latest version
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123

# Create new migration
alembic revision --autogenerate -m "Add new field to Person"
```

### Loading Seed Data (Optional)

```bash
# In backend directory with venv activated
cd backend

# Run seed script (if available)
python -m app.db.seed

# Or create sample data manually via API
```

### Database Backup and Restore

**Backup:**
```bash
# Using Docker
docker compose exec db pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

# Manual installation
pg_dump -U scheduler -h localhost residency_scheduler > backup_$(date +%Y%m%d).sql
```

**Restore:**
```bash
# Using Docker
docker compose exec -T db psql -U scheduler residency_scheduler < backup_20251219.sql

# Manual installation
psql -U scheduler -h localhost residency_scheduler < backup_20251219.sql
```

---

## Background Services

### Redis Setup

Redis is used for:
- Celery message broker
- Session storage
- Rate limiting
- Caching

**Start Redis (Manual Installation):**

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis-server

# Windows (WSL2)
sudo service redis-server start

# Verify
redis-cli ping
# Expected: PONG
```

**Configure Redis Password:**

Edit Redis configuration:
```bash
# macOS
nano /opt/homebrew/etc/redis.conf

# Linux
sudo nano /etc/redis/redis.conf
```

Add/uncomment:
```
requirepass your_redis_password_here
```

Restart Redis:
```bash
# macOS
brew services restart redis

# Linux
sudo systemctl restart redis-server
```

Test with password:
```bash
redis-cli -a your_redis_password_here ping
# Expected: PONG
```

### Celery Workers

Celery is used for background tasks:
- Resilience health checks (every 15 minutes)
- N-1/N-2 contingency analysis (daily)
- Email notifications
- Schedule conflict detection

**Start Celery Worker:**

Open a new terminal window:

```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate

# Start worker
celery -A app.core.celery_app worker --loglevel=info -Q default,resilience,notifications

# Expected output:
#  -------------- celery@hostname v5.x.x
# --- ***** -----
# -- ******* ---- [config]
# - *** --- * --- .> app:         app.core.celery_app
# - ** ---------- .> transport:   redis://:**@localhost:6379/0
# - ** ---------- .> results:     redis://:**@localhost:6379/0
# - *** --- * --- .> concurrency: 8 (prefork)
# -- ******* ---- .> task events: OFF
# --- ***** -----
#  -------------- [queues]
#                 .> default           exchange=default(direct) key=default
#                 .> resilience        exchange=resilience(direct) key=resilience
#                 .> notifications     exchange=notifications(direct) key=notifications
```

**Start Celery Beat (Scheduler):**

Open another new terminal window:

```bash
# Navigate to backend
cd backend

# Activate virtual environment
source venv/bin/activate

# Start beat scheduler
celery -A app.core.celery_app beat --loglevel=info

# Expected output:
# LocalTime -> 2025-12-19 10:00:00
# Configuration ->
#     . broker -> redis://:**@localhost:6379/0
#     . loader -> celery.loaders.app.AppLoader
#     . scheduler -> celery.beat.PersistentScheduler
#     . db -> celerybeat-schedule
#     . logfile -> [stderr]@%INFO
#     . maxinterval -> 5.00 minutes (300s)
```

**Using Helper Script (Recommended):**

```bash
# From project root
cd scripts

# Make script executable (first time only)
chmod +x start-celery.sh

# Start worker + beat together
./start-celery.sh both

# Start worker only
./start-celery.sh worker

# Start beat only
./start-celery.sh beat
```

**Verify Celery:**

```bash
# In backend directory with venv activated
python verify_celery.py

# Expected output:
# ✓ Celery worker is running
# ✓ Celery beat is running
# ✓ Registered tasks: 15
```

**Monitor Celery:**

```bash
# Inspect active tasks
celery -A app.core.celery_app inspect active

# Inspect scheduled tasks
celery -A app.core.celery_app inspect scheduled

# Inspect registered tasks
celery -A app.core.celery_app inspect registered

# Worker statistics
celery -A app.core.celery_app inspect stats
```

---

## Verification

### Health Checks

After installation, verify all services are running:

**Backend Health:**
```bash
curl http://localhost:8000/health

# Expected:
# {"status":"healthy","timestamp":"2025-12-19T10:00:00.000Z"}
```

**Backend API Documentation:**

Open browser: http://localhost:8000/docs

You should see Swagger UI with all API endpoints.

**Frontend:**

Open browser: http://localhost:3000

You should see the login page.

**Database Connection:**
```bash
# Using Docker
docker compose exec backend python -c "from app.db.session import engine; print('Connected' if engine else 'Failed')"

# Manual installation
cd backend
source venv/bin/activate
python -c "from app.db.session import engine; print('Connected' if engine else 'Failed')"
```

**Redis Connection:**
```bash
redis-cli -a your_password ping
# Expected: PONG
```

**Celery Workers:**
```bash
# In backend directory with venv activated
celery -A app.core.celery_app inspect ping

# Expected:
# -> celery@hostname: OK
#     pong
```

### Running Tests

**Backend Tests:**
```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Expected output should show all tests passing:
# ======================== test session starts =========================
# collected 150 items
#
# tests/test_auth.py::test_login ✓
# tests/test_auth.py::test_register ✓
# ...
# ======================== 150 passed in 12.34s ========================
```

**Frontend Tests:**
```bash
cd frontend

# Run tests
npm test

# Expected output:
# PASS  src/components/Login.test.tsx
# PASS  src/components/Dashboard.test.tsx
# ...
# Test Suites: 25 passed, 25 total
# Tests:       100 passed, 100 total
```

### Service Status Check

**Docker:**
```bash
docker compose ps

# Expected output:
# NAME                                 STATUS              PORTS
# residency-scheduler-backend          Up (healthy)        0.0.0.0:8000->8000/tcp
# residency-scheduler-celery-beat      Up
# residency-scheduler-celery-worker    Up (healthy)
# residency-scheduler-db               Up (healthy)        5432/tcp
# residency-scheduler-frontend         Up                  0.0.0.0:3000->3000/tcp
# residency-scheduler-redis            Up (healthy)        6379/tcp
```

**Manual Installation:**
```bash
# Check if all processes are running
pgrep -a uvicorn    # Backend
pgrep -a celery     # Celery worker & beat
pgrep -a node       # Frontend
pgrep -a postgres   # PostgreSQL
pgrep -a redis      # Redis
```

---

## Common Issues

### 1. Port Already in Use

**Error:**
```
Error: bind: address already in use
Error: Cannot assign requested address: 0.0.0.0:8000
```

**Solution:**

Find and kill the process using the port:

```bash
# Find process on port 8000 (backend)
lsof -i :8000

# Or on Linux
sudo netstat -tlnp | grep :8000

# Kill the process
kill -9 <PID>

# For frontend (port 3000)
lsof -i :3000
kill -9 <PID>

# For PostgreSQL (port 5432)
lsof -i :5432
kill -9 <PID>
```

**Or change ports in configuration:**

Edit `docker-compose.yml` or `.env`:
```yaml
# Change backend port
ports:
  - "8001:8000"  # Use 8001 instead

# Update NEXT_PUBLIC_API_URL
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### 2. Database Connection Failed

**Error:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "localhost", port 5432 failed
```

**Solutions:**

**Check if PostgreSQL is running:**
```bash
# Docker
docker compose ps db
docker compose up -d db

# Manual installation (Linux)
sudo systemctl status postgresql
sudo systemctl start postgresql

# macOS
brew services list
brew services start postgresql@15
```

**Check connection parameters:**
```bash
# Test connection
psql -U scheduler -h localhost -d residency_scheduler

# If connection fails, check:
# 1. Username is correct (should be 'scheduler')
# 2. Database exists
# 3. Password matches .env file
# 4. Host is correct (localhost or 127.0.0.1)
```

**Check pg_hba.conf (Manual installation only):**
```bash
# Linux
sudo nano /etc/postgresql/15/main/pg_hba.conf

# macOS
nano /opt/homebrew/var/postgresql@15/pg_hba.conf

# Add if missing:
# TYPE  DATABASE              USER       ADDRESS        METHOD
local   residency_scheduler   scheduler                 md5
host    residency_scheduler   scheduler  127.0.0.1/32   md5

# Restart PostgreSQL
sudo systemctl restart postgresql  # Linux
brew services restart postgresql@15  # macOS
```

**Check if database exists:**
```bash
psql -U postgres -c "\l" | grep residency_scheduler

# If not found, create it:
psql -U postgres -c "CREATE DATABASE residency_scheduler OWNER scheduler;"
```

### 3. Redis Connection Failed

**Error:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Solution:**

```bash
# Check if Redis is running
redis-cli ping

# If not running, start it:

# Docker
docker compose up -d redis

# macOS
brew services start redis
brew services list

# Linux
sudo systemctl start redis-server
sudo systemctl status redis-server

# Windows (WSL2)
sudo service redis-server start
```

**Test Redis connection:**
```bash
# Without password
redis-cli ping

# With password
redis-cli -a your_redis_password ping

# Expected: PONG
```

**Check Redis configuration:**
```bash
# macOS
cat /opt/homebrew/etc/redis.conf | grep requirepass

# Linux
cat /etc/redis/redis.conf | grep requirepass

# Should match REDIS_PASSWORD in .env
```

### 4. Node/Python Version Issues

**Error:**
```
Error: The engine "node" is incompatible with this module. Expected version ">=18.0.0".
```

**Solution:**

**Install correct Node.js version:**
```bash
# Using nvm (recommended)
nvm install 18
nvm use 18
nvm alias default 18

# Verify
node --version
# Should be v18.x.x or higher
```

**Error:**
```
ImportError: This package requires Python 3.11 or higher
```

**Solution:**

```bash
# Check Python version
python --version
python3 --version
python3.11 --version

# If 3.11 not available, install it:

# macOS
brew install python@3.11

# Linux (Ubuntu/Debian)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv

# Create venv with correct version
python3.11 -m venv venv
source venv/bin/activate
```

### 5. Docker Memory Limits

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
# Check current limits
docker info | grep Memory

# Docker uses host memory by default on Linux
# If containers are being killed, check system memory:
free -h

# Check Docker container memory usage
docker stats
```

**Reduce memory usage by disabling some services:**

Create `docker-compose.override.yml`:
```yaml
version: '3.8'

services:
  # Disable n8n if not needed
  n8n:
    profiles:
      - optional
```

Run without optional services:
```bash
docker compose up -d
```

### 6. Alembic Migration Errors

**Error:**
```
alembic.util.exc.CommandError: Target database is not up to date.
```

**Solution:**

```bash
# Check current migration
cd backend
alembic current

# Check migration history
alembic history

# If database is ahead of code:
alembic downgrade <revision>

# If code is ahead of database:
alembic upgrade head

# If migrations are corrupted, reset (CAUTION: loses data):
alembic downgrade base
alembic upgrade head
```

**Error:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.DuplicateTable) relation "persons" already exists
```

**Solution:**

```bash
# Stamp current database state
alembic stamp head

# Or if you need to recreate:
# CAUTION: This drops all data
cd backend
python
>>> from app.db.base import Base
>>> from app.db.session import engine
>>> Base.metadata.drop_all(bind=engine)
>>> Base.metadata.create_all(bind=engine)
>>> exit()

# Then run migrations
alembic upgrade head
```

### 7. Permission Denied Errors (Linux)

**Error:**
```
Permission denied: '/var/lib/postgresql/data'
```

**Solution:**

```bash
# Fix Docker volume permissions
sudo chown -R 999:999 postgres_data/

# Or recreate volumes
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

### 8. Frontend Build Errors

**Error:**
```
Error: Cannot find module 'next/babel'
```

**Solution:**

```bash
cd frontend

# Remove node_modules and lock file
rm -rf node_modules package-lock.json

# Clear npm cache
npm cache clean --force

# Reinstall
npm install
```

**Error:**
```
TypeError: Cannot read property 'map' of undefined
```

**Solution:**

Check API connection:
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check NEXT_PUBLIC_API_URL in .env.local
cat .env.local | grep NEXT_PUBLIC_API_URL

# Should match backend URL
```

### 9. Celery Worker Not Starting

**Error:**
```
[ERROR/MainProcess] consumer: Cannot connect to redis://localhost:6379/0
```

**Solution:**

```bash
# Check Redis is running
redis-cli ping

# Check CELERY_BROKER_URL in .env
cat backend/.env | grep CELERY_BROKER_URL

# Should be: redis://:password@localhost:6379/0

# Test connection
redis-cli -a your_password ping
```

**Error:**
```
ImportError: No module named 'app.core.celery_app'
```

**Solution:**

```bash
# Ensure you're in backend directory
cd backend

# Ensure venv is activated
source venv/bin/activate

# Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Try starting again
celery -A app.core.celery_app worker --loglevel=info
```

### 10. CORS Errors in Browser

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
# Docker
docker compose restart backend

# Manual
# Ctrl+C to stop, then:
uvicorn app.main:app --reload
```

---

## Platform-Specific Notes

### macOS

**Apple Silicon (M1/M2/M3) Notes:**

Some Python packages may need Rosetta 2:
```bash
# Install Rosetta 2 if needed
softwareupdate --install-rosetta

# Use arch command if needed
arch -arm64 brew install python@3.11
```

**PostgreSQL installation:**
```bash
# PostgreSQL binaries location
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# Add to ~/.zshrc for persistence
echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> ~/.zshrc
```

**Services management:**
```bash
# List all services
brew services list

# Start all required services
brew services start postgresql@15
brew services start redis

# Stop services
brew services stop postgresql@15
brew services stop redis
```

### Linux (Ubuntu/Debian)

**System dependencies:**
```bash
# Install system dependencies
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
# Enable services to start on boot
sudo systemctl enable postgresql
sudo systemctl enable redis-server

# Check service status
sudo systemctl status postgresql
sudo systemctl status redis-server

# View logs
sudo journalctl -u postgresql -f
sudo journalctl -u redis-server -f
```

### Windows

**Windows Subsystem for Linux (WSL2) - Recommended:**

```powershell
# Install WSL2
wsl --install

# Set WSL2 as default
wsl --set-default-version 2

# Install Ubuntu
wsl --install -d Ubuntu-22.04

# Then follow Linux instructions inside WSL2
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
# Use forward slashes or escaped backslashes
DATABASE_URL=postgresql://scheduler:password@localhost:5432/residency_scheduler

# Not:
DATABASE_URL=postgresql://scheduler:password@localhost\:5432\residency_scheduler
```

**Line endings:**
```bash
# Convert CRLF to LF for bash scripts
dos2unix scripts/start-celery.sh

# Or in git
git config --global core.autocrlf input
```

---

## Next Steps

After successful installation:

1. **Read the Quick Start Guide**: [docs/getting-started/quickstart.md](../getting-started/quickstart.md)
2. **Configure the Application**: [docs/getting-started/configuration.md](../getting-started/configuration.md)
3. **Review Architecture**: [docs/architecture/](../architecture/)
4. **API Documentation**: http://localhost:8000/docs
5. **User Guide**: [docs/user-guide/](../user-guide/)

### Development Resources

- **CLAUDE.md**: Project development guidelines
- **TODO_TRACKER.md**: Implementation roadmap
- **Testing Guide**: Run `pytest` in backend, `npm test` in frontend
- **API Reference**: [docs/api/](../api/)

### Production Deployment

For production deployment:

1. **Review Security Checklist**: [docs/deployment/security.md](../deployment/security.md)
2. **Configure SSL/TLS**: Set up reverse proxy (nginx/Caddy)
3. **Set up monitoring**: Prometheus + Grafana
4. **Configure backups**: Database backup strategy
5. **Review macOS deployment**: [docs/getting-started/macos-deploy.md](../getting-started/macos-deploy.md)

---

## Getting Help

### Documentation

- **Main README**: [README.md](../../README.md)
- **Troubleshooting**: [docs/troubleshooting.md](../troubleshooting.md)
- **API Documentation**: [docs/api/](../api/)
- **Architecture Docs**: [docs/architecture/](../architecture/)

### Community

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions and share ideas

### Logs and Debugging

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
# Backend
docker compose exec backend bash

# Database
docker compose exec db psql -U scheduler -d residency_scheduler

# Redis
docker compose exec redis redis-cli -a your_password
```

---

## Summary

You should now have:

- ✅ All prerequisites installed (Docker, Git, Node.js, Python, etc.)
- ✅ Repository cloned and configured
- ✅ Environment variables set up
- ✅ Services running (backend, frontend, database, Redis, Celery)
- ✅ Database initialized with migrations
- ✅ Application accessible at http://localhost:3000

**Verification Checklist:**

```bash
# All should return success
curl http://localhost:8000/health  # Backend
curl http://localhost:3000         # Frontend
redis-cli -a password ping         # Redis
docker compose ps                  # All containers running
```

If you encounter any issues not covered here, check:
- [docs/troubleshooting.md](../troubleshooting.md)
- [GitHub Issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)

---

**Last Updated:** 2025-12-19
**Tested On:** macOS 14, Ubuntu 22.04, Windows 11 (WSL2)
**Docker Version:** 24.0.0+
**Docker Compose:** v2.20.0+
