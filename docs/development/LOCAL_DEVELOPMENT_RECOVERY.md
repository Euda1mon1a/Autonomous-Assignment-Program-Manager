***REMOVED*** Local Development Recovery Procedures

> **Created:** 2025-12-25
> **Purpose:** Step-by-step procedures for recovering from common development issues

---

***REMOVED******REMOVED*** Table of Contents

1. [Full Database Rebuild](***REMOVED***full-database-rebuild)
2. [Schema Mismatch Recovery](***REMOVED***schema-mismatch-recovery)
3. [Backup Restore](***REMOVED***backup-restore)
4. [Docker Container Recovery](***REMOVED***docker-container-recovery)
5. [Constraint Registration Fix](***REMOVED***constraint-registration-fix)
6. [Authentication Issues](***REMOVED***authentication-issues)

---

***REMOVED******REMOVED*** Full Database Rebuild

**When to use:** Fresh start needed, schema corruption, or persistent unexplained errors.

***REMOVED******REMOVED******REMOVED*** Step 1: Stop All Services

```bash
docker-compose down
```

***REMOVED******REMOVED******REMOVED*** Step 2: Remove Database Volume

```bash
docker volume rm autonomous-assignment-program-manager_postgres_data
```

**Note:** This does NOT delete backups in `backups/postgres/`.

***REMOVED******REMOVED******REMOVED*** Step 3: Start Core Services

```bash
***REMOVED*** Exclude n8n to prevent log spam
docker-compose up -d db redis backend celery-worker celery-beat frontend
```

***REMOVED******REMOVED******REMOVED*** Step 4: Wait for PostgreSQL Ready

```bash
***REMOVED*** Wait for healthy status
sleep 10
docker-compose exec db pg_isready -U scheduler
```

***REMOVED******REMOVED******REMOVED*** Step 5: Run Migrations

```bash
cd backend
alembic upgrade head
```

Expected: 30+ migrations applied.

***REMOVED******REMOVED******REMOVED*** Step 6: Seed Data

```bash
***REMOVED*** Ensure requests is installed
pip3 install requests

***REMOVED*** Run seed scripts
python scripts/seed_people.py     ***REMOVED*** 28 people
python scripts/seed_blocks.py     ***REMOVED*** 730 blocks
python scripts/seed_templates.py  ***REMOVED*** 32 templates
```

***REMOVED******REMOVED******REMOVED*** Step 7: Verify

```bash
***REMOVED*** Login test
curl -s -X POST "http://localhost:8000/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "SecureP@ss1234"}'
```

---

***REMOVED******REMOVED*** Schema Mismatch Recovery

**When to use:** API errors about missing columns/tables after backup restore.

***REMOVED******REMOVED******REMOVED*** Symptoms

```
sqlalchemy.exc.ProgrammingError: column "faculty_role" does not exist
```

***REMOVED******REMOVED******REMOVED*** Option A: Apply Missing Migrations

```bash
cd backend

***REMOVED*** Check current version
alembic current

***REMOVED*** Check available migrations
alembic history

***REMOVED*** Apply all pending migrations
alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Option B: Full Rebuild

If migrations can't reconcile state, use [Full Database Rebuild](***REMOVED***full-database-rebuild).

***REMOVED******REMOVED******REMOVED*** Prevention

Always check backup metadata before restore:

```bash
cat backups/postgres/residency_scheduler_*.metadata
```

Compare `alembic_version` with current head:

```bash
cd backend && alembic heads
```

---

***REMOVED******REMOVED*** Backup Restore

**When to use:** Need to restore data from a previous state.

***REMOVED******REMOVED******REMOVED*** Step 1: Locate Backup

```bash
ls -la backups/postgres/
```

***REMOVED******REMOVED******REMOVED*** Step 2: Check Backup Metadata

```bash
cat backups/postgres/residency_scheduler_YYYYMMDD_HHMMSS.metadata
```

Verify `alembic_version` matches current schema.

***REMOVED******REMOVED******REMOVED*** Step 3: Stop Backend

```bash
docker-compose stop backend celery-worker celery-beat
```

***REMOVED******REMOVED******REMOVED*** Step 4: Restore

```bash
***REMOVED*** Decompress and pipe to PostgreSQL
gunzip -c backups/postgres/residency_scheduler_YYYYMMDD_HHMMSS.sql.gz | \
  docker-compose exec -T db psql -U scheduler -d residency_scheduler
```

***REMOVED******REMOVED******REMOVED*** Step 5: Restart Services

```bash
docker-compose up -d backend celery-worker celery-beat
```

***REMOVED******REMOVED******REMOVED*** Step 6: Verify

```bash
***REMOVED*** Check data loaded
curl -s "http://localhost:8000/api/v1/people" \
  -H "Authorization: Bearer $TOKEN" | jq '.total'
```

---

***REMOVED******REMOVED*** Docker Container Recovery

**When to use:** Containers in bad state, stale code, or configuration drift.

***REMOVED******REMOVED******REMOVED*** Check Container Status

```bash
docker-compose ps
```

***REMOVED******REMOVED******REMOVED*** Restart Specific Service

```bash
docker-compose restart backend
```

***REMOVED******REMOVED******REMOVED*** Rebuild and Restart

```bash
docker-compose up -d --build backend
```

***REMOVED******REMOVED******REMOVED*** Nuclear Option: Full Rebuild

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

***REMOVED******REMOVED******REMOVED*** Inject Code Without Rebuild

When Docker builds fail, use docker cp:

```bash
***REMOVED*** Copy updated files
docker cp backend/app/path/to/file.py \
  residency-scheduler-backend:/app/app/path/to/file.py

***REMOVED*** Restart to load
docker-compose restart backend
```

See [DOCKER_WORKAROUNDS.md](DOCKER_WORKAROUNDS.md) for detailed patterns.

---

***REMOVED******REMOVED*** Constraint Registration Fix

**When to use:** Schedule generation fails or missing constraints.

***REMOVED******REMOVED******REMOVED*** Step 1: Verify Registration

```bash
***REMOVED*** In container
docker exec residency-scheduler-backend python3 -c "
from app.scheduling.constraints.manager import ConstraintManager
mgr = ConstraintManager.create_default()
print(f'Total: {len(mgr.constraints)}')
for c in mgr.constraints:
    print(f'  - {c.__class__.__name__}')
"
```

Expected: 25 constraints

***REMOVED******REMOVED******REMOVED*** Step 2: If Missing, Inject Updated Code

```bash
***REMOVED*** Copy all constraint files
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

***REMOVED******REMOVED******REMOVED*** Step 3: Restart Backend

```bash
docker-compose restart backend
```

***REMOVED******REMOVED******REMOVED*** Step 4: Verify Again

Re-run step 1. Should now show 25 constraints.

---

***REMOVED******REMOVED*** Authentication Issues

**When to use:** Login failures, token issues.

***REMOVED******REMOVED******REMOVED*** Check Admin User Exists

```bash
docker-compose exec db psql -U scheduler -d residency_scheduler \
  -c "SELECT username, role FROM users;"
```

***REMOVED******REMOVED******REMOVED*** Reset Admin Password

```bash
***REMOVED*** In backend container
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

***REMOVED******REMOVED******REMOVED*** Create Admin User

If admin doesn't exist:

```bash
***REMOVED*** Via API registration
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecureP@ss1234",
    "role": "admin"
  }'
```

***REMOVED******REMOVED******REMOVED*** Password Requirements

- Minimum 12 characters
- At least 3 of 4 character types:
  - Uppercase letters
  - Lowercase letters
  - Numbers
  - Special characters

---

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Service URLs

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

***REMOVED******REMOVED******REMOVED*** Common Commands

```bash
***REMOVED*** View logs
docker-compose logs -f backend

***REMOVED*** Database shell
docker-compose exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Backend shell
docker-compose exec backend bash

***REMOVED*** Check API health
curl http://localhost:8000/health
```

***REMOVED******REMOVED******REMOVED*** Environment Variables

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

***REMOVED******REMOVED*** Related Documentation

- [DOCKER_WORKAROUNDS.md](DOCKER_WORKAROUNDS.md) - Docker cp patterns
- [SCHEMA_VERSION_TRACKING.md](SCHEMA_VERSION_TRACKING.md) - Version tracking
- [SESSION_20251225_POSTMORTEM.md](SESSION_20251225_POSTMORTEM.md) - Real recovery example
- [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md) - Production issues
