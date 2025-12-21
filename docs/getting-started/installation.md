***REMOVED*** Installation

This guide covers detailed installation instructions for Residency Scheduler.

---

***REMOVED******REMOVED*** Docker Installation (Recommended)

***REMOVED******REMOVED******REMOVED*** Step 1: Clone Repository

```bash
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager
```

***REMOVED******REMOVED******REMOVED*** Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
***REMOVED*** Database (required)
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@localhost:5432/residency_scheduler

***REMOVED*** Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_64_character_random_secret_key_here

***REMOVED*** Frontend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

***REMOVED******REMOVED******REMOVED*** Step 3: Start Services

```bash
***REMOVED*** Start all services
docker-compose up -d

***REMOVED*** View logs
docker-compose logs -f

***REMOVED*** Check status
docker-compose ps
```

***REMOVED******REMOVED******REMOVED*** Step 4: Initialize Database

```bash
***REMOVED*** Run migrations
docker-compose exec backend alembic upgrade head
```

---

***REMOVED******REMOVED*** Local Development Setup

***REMOVED******REMOVED******REMOVED*** Backend Setup

```bash
cd backend

***REMOVED*** Create virtual environment
python -m venv venv
source venv/bin/activate  ***REMOVED*** Windows: venv\Scripts\activate

***REMOVED*** Install dependencies
pip install -r requirements.txt

***REMOVED*** Set up database (requires PostgreSQL)
createdb residency_scheduler

***REMOVED*** Run migrations
alembic upgrade head

***REMOVED*** Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

***REMOVED******REMOVED******REMOVED*** Frontend Setup

```bash
cd frontend

***REMOVED*** Install dependencies
npm install

***REMOVED*** Start development server
npm run dev
```

***REMOVED******REMOVED******REMOVED*** Celery Workers (Optional but Recommended)

```bash
cd backend

***REMOVED*** Start Redis (required for Celery)
redis-server

***REMOVED*** Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

***REMOVED*** Start Celery beat scheduler (in another terminal)
celery -A app.core.celery_app beat --loglevel=info
```

---

***REMOVED******REMOVED*** Environment Variables

***REMOVED******REMOVED******REMOVED*** Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | Database password | `secure_password` |
| `SECRET_KEY` | JWT signing key (64 chars) | `openssl rand -hex 32` |
| `NEXT_PUBLIC_API_URL` | API endpoint for frontend | `http://localhost:8000` |

***REMOVED******REMOVED******REMOVED*** Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `APP_NAME` | Application name | `Residency Scheduler` |
| `CORS_ORIGINS` | Allowed origins (JSON array) | `["http://localhost:3000"]` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `15` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |

See [Configuration](configuration.md) for complete reference.

---

***REMOVED******REMOVED*** Troubleshooting Installation

***REMOVED******REMOVED******REMOVED*** Database Connection Failed

```
Error: Connection refused to localhost:5432
```

**Solution:** Ensure PostgreSQL is running:

```bash
***REMOVED*** Docker
docker-compose up -d db

***REMOVED*** Local
sudo systemctl start postgresql
```

***REMOVED******REMOVED******REMOVED*** Redis Connection Failed

```
Error: Connection refused to localhost:6379
```

**Solution:** Start Redis:

```bash
***REMOVED*** Docker
docker-compose up -d redis

***REMOVED*** Local
redis-server
```

***REMOVED******REMOVED******REMOVED*** Port Already in Use

```
Error: Address already in use: 8000
```

**Solution:** Find and kill the process:

```bash
lsof -i :8000
kill -9 <PID>
```

See [Troubleshooting](../troubleshooting.md) for more solutions.
