# Offline Operations & Long-Term Maintainability

> **Purpose**: Ensure this system works on an air-gapped network for 10+ years
> **Last Updated**: 2024-12

---

## Design Philosophy

This system is designed for **institutional longevity**. The original developers may not be available. Internet access may not exist. The person maintaining this might be learning as they go.

### Core Principles

1. **Zero cloud dependencies for core scheduling**
2. **Self-contained Docker deployment**
3. **Obvious code over clever code**
4. **Documentation explains WHY, not just WHAT**
5. **Graceful degradation when components fail**

---

## What Works Offline (Core System)

| Component | Offline? | Notes |
|-----------|----------|-------|
| Schedule generation | ✅ Yes | Constraint solver runs locally |
| ACGME validation | ✅ Yes | All rules are local code |
| User authentication | ✅ Yes | Local JWT, local database |
| Import/Export | ✅ Yes | CSV/Excel processing is local |
| Conflict detection | ✅ Yes | Database queries only |
| Swap management | ✅ Yes | All local logic |
| Daily manifest | ✅ Yes | Database queries only |
| Resilience monitoring | ✅ Yes | Local calculations |

## What Requires Network (Optional Features)

| Component | Required? | Fallback |
|-----------|-----------|----------|
| LLM advisor (autonomous module) | ❌ Optional | Loop runs without it, uses deterministic rules |
| AI-assisted suggestions | ❌ Optional | Manual scheduling works fine |
| Email notifications | ❌ Optional | Check the web UI instead |
| Webhook integrations | ❌ Optional | Disable in settings |
| External calendar sync | ❌ Optional | Manual export/import |

### Autonomous Scheduling Module

The `app.autonomous` package implements a self-improving scheduling loop. It's designed with the principle: **"Python is authoritative, LLM is advisory"**.

- The core loop (`AutonomousLoop`) runs entirely offline
- The evaluator (`ScheduleEvaluator`) uses deterministic ACGME rules
- The generator (`CandidateGenerator`) uses local constraint solvers
- The LLM advisor (`LLMAdvisor`) is **optional** - if no API key, it's simply skipped

To run autonomous scheduling offline:
```python
from app.autonomous import AutonomousLoop

# No LLM client = offline mode
loop = AutonomousLoop.from_config(scenario="baseline", llm_client=None)
result = loop.run(max_iterations=200)
```

---

## Deployment for Air-Gapped Networks

### Prerequisites (One-Time Setup)

On an internet-connected machine:

```bash
# 1. Pull all Docker images
docker-compose pull

# 2. Save images to files
docker save autonomous-assignment-program-manager-backend > backend.tar
docker save autonomous-assignment-program-manager-frontend > frontend.tar
docker save postgres:15 > postgres.tar
docker save redis:7 > redis.tar

# 3. Copy these files + the entire repo to the air-gapped machine
```

On the air-gapped machine:

```bash
# 1. Load Docker images
docker load < backend.tar
docker load < frontend.tar
docker load < postgres.tar
docker load < redis.tar

# 2. Start the system
docker-compose up -d
```

### Python Dependencies (Pre-Vendored)

All Python wheels are pre-built in `vendor/wheels/`. The Dockerfile uses these instead of downloading from PyPI:

```dockerfile
# Uses local wheels, no network needed
RUN pip install --no-index --find-links=/wheels -r requirements.txt
```

To update wheels (on internet-connected machine):
```bash
pip download -r requirements.txt -d vendor/wheels/
```

---

## Data Backup & Recovery

### Daily Backup (Recommended)

```bash
# Backup database
docker-compose exec db pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

# Backup location: Keep on separate physical drive
```

### Restore from Backup

```bash
# Stop the system
docker-compose down

# Restore database
docker-compose up -d db
docker-compose exec -T db psql -U scheduler residency_scheduler < backup_20250115.sql

# Start everything
docker-compose up -d
```

---

## Troubleshooting Without Internet

### Common Issues

**"Cannot connect to database"**
```bash
# Check if database container is running
docker ps | grep db

# Check database logs
docker-compose logs db --tail 50

# Restart database
docker-compose restart db
```

**"Backend won't start"**
```bash
# Check backend logs
docker-compose logs backend --tail 100

# Common fix: database migrations
docker-compose exec backend alembic upgrade head
```

**"Frontend shows blank page"**
```bash
# Check frontend logs
docker-compose logs frontend --tail 50

# Rebuild frontend (if source changed)
docker-compose up -d --build frontend
```

### Nuclear Option (Full Reset)

If nothing works and you need to start fresh:

```bash
# WARNING: This deletes all data
docker-compose down -v  # -v removes volumes (data)
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Re-seed initial data
docker-compose exec backend python -m app.db.seed
```

---

## Component Replacement Guide

### If You Need to Replace the Database

PostgreSQL 15 is used. Compatible alternatives:
- PostgreSQL 14-16 (minor config changes)
- SQLite (for single-user, modify SQLAlchemy config)

### If You Need to Replace the Frontend Framework

The frontend is React/Next.js. The backend API is framework-agnostic:
- All endpoints documented in `/api/docs`
- Any frontend that can make HTTP requests will work
- Mobile app, desktop app, or even command-line tools can use the API

### If You Need to Replace Python

The core logic is in:
- `backend/app/scheduling/` - Schedule generation
- `backend/app/scheduling/validator.py` - ACGME rules

These are pure Python with minimal dependencies. Could be ported to:
- Java, C#, Go, or any language with constraint solver libraries
- The ACGME rules are documented in `docs/architecture/acgme-compliance.md`

---

## Excel Integration (VBA Module)

The `scripts/excel/CSVAutoExport.bas` module has **zero external dependencies**:

- Uses only built-in Windows components (ADODB.Stream)
- Works with Excel 2007 and later
- No internet access required
- No installation beyond copy-paste into VBA editor

This is the recommended way to get schedule data from Excel to the web app.

---

## Contact & Support

If the original developers are unavailable:

1. **Read the docs**: `docs/` contains comprehensive documentation
2. **Check the tests**: `backend/tests/` shows expected behavior
3. **API documentation**: Visit `http://localhost:8000/docs` when running
4. **Code comments**: We've tried to explain the "why" throughout

The system was designed to be self-explanatory. Take your time, read the code, and don't be afraid to experiment on a test copy first.

---

## Version Compatibility Matrix

| Component | Minimum Version | Tested With | Notes |
|-----------|----------------|-------------|-------|
| Docker | 20.10+ | 24.0 | Docker Desktop or Engine |
| Docker Compose | 2.0+ | 2.21 | V2 syntax used |
| PostgreSQL | 14 | 15 | 16 also works |
| Python | 3.11 | 3.12 | Backend runtime |
| Node.js | 18 | 22 | Frontend build |
| Excel | 2007 | 365 | VBA module |
| Windows | 7+ | 11 | For Excel VBA |
| macOS | 10.15+ | 14 | Docker Desktop |
| Linux | Any | Ubuntu 22.04 | Docker native |
