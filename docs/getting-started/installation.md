# Installation

This guide covers detailed installation instructions for Residency Scheduler.

---

## Docker Installation (Recommended)

### Step 1: Clone Repository

```bash
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database (required)
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@localhost:5432/residency_scheduler

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_64_character_random_secret_key_here

# Frontend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 3: Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 4: Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

---

## Local Development Setup

### Backend Setup

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

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Celery Workers (Optional but Recommended)

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

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | Database password | `secure_password` |
| `SECRET_KEY` | JWT signing key (64 chars) | `openssl rand -hex 32` |
| `NEXT_PUBLIC_API_URL` | API endpoint for frontend | `http://localhost:8000` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `APP_NAME` | Application name | `Residency Scheduler` |
| `CORS_ORIGINS` | Allowed origins (JSON array) | `["http://localhost:3000"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `1440` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |

See [Configuration](configuration.md) for complete reference.

---

## Troubleshooting Installation

### Database Connection Failed

```
Error: Connection refused to localhost:5432
```

**Solution:** Ensure PostgreSQL is running:

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

**Solution:** Start Redis:

```bash
# Docker
docker-compose up -d redis

# Local
redis-server
```

### Port Already in Use

```
Error: Address already in use: 8000
```

**Solution:** Find and kill the process:

```bash
lsof -i :8000
kill -9 <PID>
```

See [Troubleshooting](../troubleshooting.md) for more solutions.
