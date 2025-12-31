# Claude Deployment: Getting Unstuck (Docker Desktop macOS)

Purpose: a fast, local-only playbook to get the stack running and stable when deployment fails or the backend crashloops on Docker Desktop for macOS.

## 0) One-Screen Triage (Crashloop)

Checklist:
- Confirm which container is restarting.
- Capture the last error message and stack trace.
- Check whether the error is import/dependency, migration/schema, or config.

Commands:
```bash
docker ps -a | grep scheduler
docker compose -f docker-compose.local.yml logs --tail=200 backend
```

If the backend is restarting:
```bash
docker compose -f docker-compose.local.yml logs -f backend
```

## 1) Validate Dependencies in the Running Image

Most crashloops here have been from binary dependency mismatches.

Commands:
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

If versions differ, rebuild the image:
```bash
docker compose -f docker-compose.local.yml up -d --build backend
```

## 2) Check DB Migrations vs Models

If you see `UndefinedColumn` or `relation does not exist`, the DB is behind:

Commands:
```bash
docker compose -f docker-compose.local.yml exec backend alembic current
docker compose -f docker-compose.local.yml exec backend alembic heads
docker compose -f docker-compose.local.yml exec backend alembic upgrade head
```

If the error persists, check whether the migration exists:
```bash
ls backend/alembic/versions | rg -i "<column_or_table_name>"
```

## 3) Confirm API Base URL (Avoid 307 CORS Redirect)

The backend redirects `/api/*` -> `/api/v1/*` and the redirect drops CORS headers.

Make sure the frontend uses `/api/v1` directly:
- `docker-compose.local.yml` should set `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`
- `frontend/src/lib/api.ts` default should be `/api/v1`

After changing env, rebuild frontend:
```bash
docker compose -f docker-compose.local.yml up -d --build frontend
```

## 4) Ensure Cookies Are Sent (Auth Looks Broken Otherwise)

Symptom: login 200, then 401 on next request.

Make sure axios has credentials enabled:
- `frontend/src/lib/api.ts` has `withCredentials: true`

Check cookies in the browser devtools:
- Look for `access_token` cookie
- If `Secure` is true on HTTP, it will not be sent

## 5) Verify Required Data Exists (People + Templates)

Schedule generation fails without people and rotation templates. Confirm both before running schedules.

Commands:
```bash
# Count people (requires DB access)
docker compose -f docker-compose.local.yml exec backend python - <<'PY'
from app.db.session import get_db
from app.models.person import Person
from app.models.rotation_template import RotationTemplate

db = next(get_db())
print("people", db.query(Person).count())
print("rotation_templates", db.query(RotationTemplate).count())
PY
```

If counts are zero, seed data locally:
```bash
docker compose -f docker-compose.local.yml exec backend python -m scripts.seed_people
docker compose -f docker-compose.local.yml exec backend python -m scripts.seed_rotation_templates
```

## 6) Nuke-and-Rebuild (When State Is Corrupt)

Use this when you suspect stale layers, wrong wheels, or broken schema state.

```bash
docker compose -f docker-compose.local.yml down
docker rmi autonomous-assignment-program-manager-backend 2>/dev/null || true
docker rmi autonomous-assignment-program-manager-frontend 2>/dev/null || true
docker builder prune -af
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml exec backend alembic upgrade head
```

If the schema is irreparably out of sync and you can lose data:
```bash
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up -d --build
```

## 7) Docker Desktop macOS Notes (File Sync)

If the backend container shows stale code:
- Restart Docker Desktop to clear VirtioFS/gRPC FUSE caches.
- Prefer `docker compose up -d --build` over live-editing files when debugging.

## 8) Known Failure Patterns to Watch

1) Crashloop due to numpy incompatibility
- If `numpy>=2.x` sneaks in, `pyspc` and `manufacturing` will break.
- Fix by ensuring the requirements pin is honored and rebuilding the image.

2) Missing columns/tables
- Look for `UndefinedColumn` or `UndefinedTable` in logs.
- Fix by applying migrations or generating missing ones.

3) CORS errors from 307 redirects
- Always use `/api/v1` directly from the frontend.

4) Docker Desktop file sync staleness (macOS)
- If the container sees old files, rebuild or restart Docker Desktop.

## 9) Minimal Health Checks

```bash
curl -sS http://localhost:8000/health | jq
curl -sS http://localhost:8000/api/v1/health | jq
```

## 10) When You Need a Log Bundle

```bash
docker compose -f docker-compose.local.yml logs --tail=300 backend > /tmp/backend.log
```

Attach `/tmp/backend.log` to your next debugging note.

---

If you still get a crashloop after Step 5, paste the last 50 lines of backend logs and the output of:
```bash
docker compose -f docker-compose.local.yml ps
```
