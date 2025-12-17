***REMOVED*** Getting Started

This guide will help you install, configure, and run the Residency Scheduler application.

---

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** Required Software
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for version control

***REMOVED******REMOVED******REMOVED*** For Local Development (Optional)
- **Python** 3.11+
- **Node.js** 18+ and **npm** 9+
- **PostgreSQL** 15
- **Redis** 7

---

***REMOVED******REMOVED*** Installation

***REMOVED******REMOVED******REMOVED*** Option 1: Docker (Recommended)

The easiest way to run Residency Scheduler is using Docker Compose.

```bash
***REMOVED*** Clone the repository
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager

***REMOVED*** Copy environment file
cp .env.example .env

***REMOVED*** Edit configuration (see Configuration section)
nano .env

***REMOVED*** Start all services
docker-compose up -d

***REMOVED*** View logs
docker-compose logs -f
```

***REMOVED******REMOVED******REMOVED*** Option 2: Local Development

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend Setup

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

***REMOVED******REMOVED******REMOVED******REMOVED*** Frontend Setup

```bash
cd frontend

***REMOVED*** Install dependencies
npm install

***REMOVED*** Start development server
npm run dev
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Celery Workers (Optional but Recommended)

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

***REMOVED******REMOVED*** Initial Configuration

***REMOVED******REMOVED******REMOVED*** Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Required Settings

```env
***REMOVED*** Database
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@localhost:5432/residency_scheduler

***REMOVED*** Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_64_character_random_secret_key_here

***REMOVED*** Frontend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Optional Settings

```env
***REMOVED*** Application
DEBUG=false
APP_NAME=Residency Scheduler
APP_VERSION=1.0.0

***REMOVED*** CORS (JSON array of allowed origins)
CORS_ORIGINS=["http://localhost:3000"]

***REMOVED*** Token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=1440

***REMOVED*** Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

See [Configuration](Configuration) for all available options.

---

***REMOVED******REMOVED*** Verify Installation

***REMOVED******REMOVED******REMOVED*** Check Services

```bash
***REMOVED*** Check all containers are running
docker-compose ps

***REMOVED*** Expected output:
***REMOVED*** NAME                    STATUS
***REMOVED*** backend                 Up
***REMOVED*** frontend                Up
***REMOVED*** db                      Up
***REMOVED*** redis                   Up
***REMOVED*** celery-worker           Up
***REMOVED*** celery-beat             Up
```

***REMOVED******REMOVED******REMOVED*** Test Endpoints

```bash
***REMOVED*** Backend health check
curl http://localhost:8000/health

***REMOVED*** Expected: {"status": "healthy"}

***REMOVED*** API documentation
open http://localhost:8000/docs
```

***REMOVED******REMOVED******REMOVED*** Access the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

---

***REMOVED******REMOVED*** First Steps

***REMOVED******REMOVED******REMOVED*** 1. Create Admin Account

On first launch, create an administrator account:

```bash
***REMOVED*** Using the API
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

***REMOVED******REMOVED******REMOVED*** 2. Configure Academic Year

1. Log in as admin
2. Navigate to **Settings** → **Academic Year**
3. Set the start and end dates for your academic year
4. Configure block settings (typically 730 blocks per year)

***REMOVED******REMOVED******REMOVED*** 3. Add People

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

***REMOVED******REMOVED******REMOVED*** 4. Create Rotation Templates

Define your rotation types:

1. Go to **Templates** → **Create Template**
2. Configure:
   - Template name (e.g., "ICU", "Clinic", "Call")
   - Duration
   - Capacity limits
   - Required supervision ratios
3. Save the template

***REMOVED******REMOVED******REMOVED*** 5. Generate Your First Schedule

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

***REMOVED******REMOVED*** Running Tests

***REMOVED******REMOVED******REMOVED*** Backend Tests

```bash
cd backend

***REMOVED*** Run all tests
pytest

***REMOVED*** Run with coverage
pytest --cov=app --cov-report=html

***REMOVED*** Run specific test file
pytest tests/test_schedule_service.py

***REMOVED*** Run ACGME compliance tests
pytest -m acgme
```

***REMOVED******REMOVED******REMOVED*** Frontend Tests

```bash
cd frontend

***REMOVED*** Run unit tests
npm test

***REMOVED*** Run with coverage
npm run test:coverage

***REMOVED*** Run E2E tests
npm run test:e2e

***REMOVED*** Run E2E with UI
npm run test:e2e:ui
```

---

***REMOVED******REMOVED*** Common Setup Issues

***REMOVED******REMOVED******REMOVED*** Database Connection Failed

```
Error: Connection refused to localhost:5432
```

**Solution**: Ensure PostgreSQL is running:
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

**Solution**: Start Redis:
```bash
***REMOVED*** Docker
docker-compose up -d redis

***REMOVED*** Local
redis-server
```

***REMOVED******REMOVED******REMOVED*** Migration Errors

```
Error: Can't locate revision
```

**Solution**: Reset migrations:
```bash
cd backend
alembic downgrade base
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Port Already in Use

```
Error: Address already in use: 8000
```

**Solution**: Find and kill the process:
```bash
lsof -i :8000
kill -9 <PID>
```

---

***REMOVED******REMOVED*** Next Steps

- Read the [User Guide](User-Guide) to learn how to use the application
- Review [Architecture](Architecture) to understand the system design
- Check [Configuration](Configuration) for advanced settings
- See [Development](Development) if you want to contribute

---

***REMOVED******REMOVED*** Getting Help

If you encounter issues:

1. Check the [Troubleshooting](Troubleshooting) guide
2. Review logs: `docker-compose logs -f [service_name]`
3. Search existing [GitHub Issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)
4. Open a new issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs and error messages
   - Environment details
