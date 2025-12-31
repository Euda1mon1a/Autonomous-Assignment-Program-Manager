# Claude Docker Desktop Deployment Notes (macOS)

Purpose: a practical, Docker Desktop–first guide to get the local stack stable without chasing stale mounts or phantom CORS issues.

## Quick Start (Get Green Fast)

1) Rebuild everything (avoid stale file mounts)
```bash
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up -d --build
```

2) Tail backend logs until stable
```bash
docker compose -f docker-compose.local.yml logs -f backend
```

3) Apply migrations
```bash
docker compose -f docker-compose.local.yml exec backend alembic upgrade head
```

4) Seed required data (people + templates)
```bash
docker compose -f docker-compose.local.yml exec backend python -m scripts.seed_people
docker compose -f docker-compose.local.yml exec backend python -m scripts.seed_rotation_templates
```

5) Verify health
```bash
curl -sS http://localhost:8000/health | jq
curl -sS http://localhost:8000/api/v1/health | jq
```

## Docker Desktop macOS Pitfalls (What to Assume First)

- Stale file mounts happen. If the container is running old code, restart Docker Desktop or rebuild the image.
- Prefer `docker compose` (v2) over `docker-compose` (v1). Docker Desktop defaults to v2.
- Avoid live-edit reliance while debugging. Rebuild to ensure what you’re running is what you edited.

## Crashloop Triage (Local Only)

If the backend restarts repeatedly:
```bash
docker compose -f docker-compose.local.yml logs --tail=200 backend
```

Common causes:
- Binary deps mismatch (`numpy>=2.x` will break `pyspc` / `manufacturing`)
- Missing DB columns or version tables
- Bad API base URL redirects causing auth loop symptoms

## Dependency Sanity Check

```bash
docker compose -f docker-compose.local.yml exec backend python - <<'PY'
import numpy, scipy
print("numpy", numpy.__version__)
print("scipy", scipy.__version__)
PY
```

Expected:
- `numpy==1.26.4`
- `scipy==1.15.3`

If not, rebuild backend image.

## Local Wheelhouse (Avoid Slow Downloads)

This repo supports a local wheelhouse for faster, offline-ish builds.
Wheelhouse path (gitignored): `backend/vendor/wheels`

Create it once (requires network):
```bash
./scripts/build-wheelhouse.sh
```

Builds will automatically use the wheelhouse if it contains `.whl` files.
If the wheelhouse is empty, pip falls back to normal installs.

## DB Migrations vs Models

```bash
docker compose -f docker-compose.local.yml exec backend alembic current
docker compose -f docker-compose.local.yml exec backend alembic heads
docker compose -f docker-compose.local.yml exec backend alembic upgrade head
```

If you see `UndefinedColumn` or `UndefinedTable`, a migration is missing or was never applied.

## CORS Looks Broken? Treat It as a Backend Crash

If the browser says “CORS blocked,” check backend logs first. Most “CORS” issues are 500s thrown before CORS headers are added.

Also ensure the frontend uses `/api/v1` directly:
- `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`

## Rate Limiting (Local Dev)

Repeated failures can trigger rate limits and make the UI look broken.
Disable for local dev in `docker-compose.local.yml`:
```
RATE_LIMIT_ENABLED: "false"
```

## When Schedules Won’t Generate

Confirm data exists:
```bash
docker compose -f docker-compose.local.yml exec backend python - <<'PY'
from app.db.session import get_db
from app.models.person import Person
from app.models.rotation_template import RotationTemplate

db = next(get_db())
print("people", db.query(Person).count())
print("rotation_templates", db.query(RotationTemplate).count())
PY
```

If counts are zero, seed them (see Quick Start step 4).

## If Nothing Works (Full Reset)

```bash
docker compose -f docker-compose.local.yml down -v
docker builder prune -af
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml exec backend alembic upgrade head
```

## Log Bundle for Postmortem

```bash
docker compose -f docker-compose.local.yml logs --tail=300 backend > /tmp/backend.log
```

Attach `/tmp/backend.log` to debugging notes.
