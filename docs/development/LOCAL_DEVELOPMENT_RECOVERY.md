# Local Development Recovery Procedures

> **Created:** 2025-12-25
> **Purpose:** Step-by-step procedures for recovering from common development issues

---

## Table of Contents

1. [Full Database Rebuild](#full-database-rebuild)
2. [Schema Mismatch Recovery](#schema-mismatch-recovery)
3. [Backup Restore](#backup-restore)
4. [Docker Container Recovery](#docker-container-recovery)
5. [Constraint Registration Fix](#constraint-registration-fix)
6. [Authentication Issues](#authentication-issues)

---

## Full Database Rebuild

**When to use:** Fresh start needed, schema corruption, or persistent unexplained errors.

### Step 1: Stop All Services

```bash
docker-compose down
```

### Step 2: Remove Database Volume

```bash
docker volume rm autonomous-assignment-program-manager_postgres_data
```

**Note:** This does NOT delete backups in `backups/postgres/`.

### Step 3: Start Core Services

```bash
# Exclude n8n to prevent log spam
docker-compose up -d db redis backend celery-worker celery-beat frontend
```

### Step 4: Wait for PostgreSQL Ready

```bash
# Wait for healthy status
sleep 10
docker-compose exec db pg_isready -U scheduler
```

### Step 5: Run Migrations

```bash
cd backend
alembic upgrade head
```

Expected: 30+ migrations applied.

### Step 6: Seed Data

```bash
# Ensure requests is installed
pip3 install requests

# Run seed scripts
python scripts/seed_people.py     # 28 people
python scripts/seed_blocks.py     # 730 blocks
python scripts/seed_templates.py  # 32 templates
```

### Step 7: Verify

```bash
# Login test
curl -s -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "SecureP@ss1234"}'
```

---

## Schema Mismatch Recovery

**When to use:** API errors about missing columns/tables after backup restore.

### Symptoms

```
sqlalchemy.exc.ProgrammingError: column "faculty_role" does not exist
```

### Option A: Apply Missing Migrations

```bash
cd backend

# Check current version
alembic current

# Check available migrations
alembic history

# Apply all pending migrations
alembic upgrade head
```

### Option B: Full Rebuild

If migrations can't reconcile state, use [Full Database Rebuild](#full-database-rebuild).

### Prevention

Always check backup metadata before restore:

```bash
cat backups/postgres/residency_scheduler_*.metadata
```

Compare `alembic_version` with current head:

```bash
cd backend && alembic heads
```

---

## Backup Restore

**When to use:** Need to restore data from a previous state.

### Step 1: Locate Backup

```bash
ls -la backups/postgres/
```

### Step 2: Check Backup Metadata

```bash
cat backups/postgres/residency_scheduler_YYYYMMDD_HHMMSS.metadata
```

Verify `alembic_version` matches current schema.

### Step 3: Stop Backend

```bash
docker-compose stop backend celery-worker celery-beat
```

### Step 4: Restore

```bash
# Decompress and pipe to PostgreSQL
gunzip -c backups/postgres/residency_scheduler_YYYYMMDD_HHMMSS.sql.gz | \
  docker-compose exec -T db psql -U scheduler -d residency_scheduler
```

### Step 5: Restart Services

```bash
docker-compose up -d backend celery-worker celery-beat
```

### Step 6: Verify

```bash
# Check data loaded
curl -s "http://localhost:8000/api/v1/people" \
  -H "Authorization: Bearer $TOKEN" | jq '.total'
```

---

## Docker Container Recovery

**When to use:** Containers in bad state, stale code, or configuration drift.

### Check Container Status

```bash
docker-compose ps
```

### Restart Specific Service

```bash
docker-compose restart backend
```

### Rebuild and Restart

```bash
docker-compose up -d --build backend
```

### Nuclear Option: Full Rebuild

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Inject Code Without Rebuild

When Docker builds fail, use docker cp:

```bash
# Copy updated files
docker cp backend/app/path/to/file.py \
  residency-scheduler-backend:/app/app/path/to/file.py

# Restart to load
docker-compose restart backend
```

See [DOCKER_WORKAROUNDS.md](DOCKER_WORKAROUNDS.md) for detailed patterns.

---

## Constraint Registration Fix

**When to use:** Schedule generation fails or missing constraints.

### Step 1: Verify Registration

```bash
# In container
docker exec residency-scheduler-backend python3 -c "
from app.scheduling.constraints.manager import ConstraintManager
mgr = ConstraintManager.create_default()
print(f'Total: {len(mgr.constraints)}')
for c in mgr.constraints:
    print(f'  - {c.__class__.__name__}')
"
```

Expected: 25 constraints

### Step 2: If Missing, Inject Updated Code

```bash
# Copy all constraint files
docker cp backend/app/scheduling/constraints/manager.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/manager.py

docker cp backend/app/scheduling/constraints/call_equity.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/call_equity.py

docker cp backend/app/scheduling/constraints/fmit.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/fmit.py

docker cp backend/app/scheduling/constraints/inpatient.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/inpatient.py

docker cp backend/app/scheduling/constraints/__init__.py \
  residency-scheduler-backend:/app/app/scheduling/constraints/__init__.py
```

### Step 3: Restart Backend

```bash
docker-compose restart backend
```

### Step 4: Verify Again

Re-run step 1. Should now show 25 constraints.

---

## Authentication Issues

**When to use:** Login failures, token issues.

### Check Admin User Exists

```bash
docker-compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT username, role FROM users;"
```

### Reset Admin Password

```bash
# In backend container
docker exec -it residency-scheduler-backend python3 -c "
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
user = db.query(User).filter(User.username == 'admin').first()
if user:
    user.hashed_password = get_password_hash('SecureP@ss1234')
    db.commit()
    print('Password reset')
else:
    print('Admin user not found')
"
```

### Create Admin User

If admin doesn't exist:

```bash
# Via API registration
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecureP@ss1234",
    "role": "admin"
  }'
```

### Password Requirements

- Minimum 12 characters
- At least 3 of 4 character types:
  - Uppercase letters
  - Lowercase letters
  - Numbers
  - Special characters

---

## Quick Reference

### Service URLs

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### Common Commands

```bash
# View logs
docker-compose logs -f backend

# Database shell
docker-compose exec db psql -U scheduler -d residency_scheduler

# Backend shell
docker-compose exec backend bash

# Check API health
curl http://localhost:8000/health
```

### Environment Variables

Critical variables in `.env`:

```bash
DB_HOST=db
DB_PORT=5432
DB_NAME=residency_scheduler
DB_USER=scheduler
DB_PASSWORD=<secure>
SECRET_KEY=<32+ chars>
```

---

## Volume Strategy & Multi-User Transition

### Current Setup: Bind Mounts (Single Developer)

For local development, we use **bind mounts** (`./data/postgres`, `./data/redis`) because:
- Data survives Docker resets, updates, and `prune` commands
- Easy to verify: `ls data/postgres/` shows actual database files
- Simple backup: `cp -r data/postgres backups/`
- Debugging: Can inspect data without running containers

### When to Use Named Volumes

Switch to named volumes when:
- **Multi-user deployment** - Bind mounts have permission issues across users
- **Production** - Named volumes integrate with Docker Swarm/Kubernetes
- **CI/CD** - Ephemeral containers shouldn't write to host

### Transitioning Back to Named Volumes

**Step 1: Update docker-compose.local.yml**
```yaml
# Change FROM bind mounts:
db:
  volumes:
    - ./data/postgres:/var/lib/postgresql/data
redis:
  volumes:
    - ./data/redis:/data

# TO named volumes:
db:
  volumes:
    - postgres_local_data:/var/lib/postgresql/data
redis:
  volumes:
    - redis_local_data:/data

# Add volume definitions at bottom:
volumes:
  postgres_local_data:
    driver: local
  redis_local_data:
    driver: local
  backend_local_venv:
    driver: local
```

**Step 2: Migrate Data to Named Volumes**
```bash
# Stop containers
docker compose -f docker-compose.local.yml down

# Create named volumes and copy data
docker volume create autonomous-assignment-program-manager_postgres_local_data
docker volume create autonomous-assignment-program-manager_redis_local_data

# Copy postgres data
docker run --rm \
  -v "$(pwd)/data/postgres:/src:ro" \
  -v autonomous-assignment-program-manager_postgres_local_data:/dst \
  alpine cp -a /src/. /dst/

# Copy redis data
docker run --rm \
  -v "$(pwd)/data/redis:/src:ro" \
  -v autonomous-assignment-program-manager_redis_local_data:/dst \
  alpine cp -a /src/. /dst/

# Start with new config
docker compose -f docker-compose.local.yml up -d
```

**Step 3: Verify and Clean Up**
```bash
# Verify data migrated
docker exec scheduler-local-db psql -U scheduler -d residency_scheduler \
  -c "SELECT COUNT(*) FROM people;"

# Once confirmed, optionally remove bind mount data
rm -rf data/postgres data/redis
```

### Backup Strategy by Volume Type

| Setup | Backup Command | Restore Command |
|-------|----------------|-----------------|
| Bind Mount | `cp -r data/postgres backups/` | `cp -r backups/postgres data/` |
| Named Volume | See below | See below |

**Named Volume Backup:**
```bash
docker run --rm \
  -v autonomous-assignment-program-manager_postgres_local_data:/data:ro \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

**Named Volume Restore:**
```bash
docker run --rm \
  -v autonomous-assignment-program-manager_postgres_local_data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "rm -rf /data/* && tar xzf /backup/postgres_backup.tar.gz -C /data"
```

---

## Related Documentation

- [DOCKER_WORKAROUNDS.md](DOCKER_WORKAROUNDS.md) - Docker cp patterns
- [SCHEMA_VERSION_TRACKING.md](SCHEMA_VERSION_TRACKING.md) - Version tracking
- [SESSION_20251225_POSTMORTEM.md](SESSION_20251225_POSTMORTEM.md) - Real recovery example
- [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md) - Production issues
