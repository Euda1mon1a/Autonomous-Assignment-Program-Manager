# Claude Local Deployment Checklist

Purpose: local-only steps for validating Session 14 changes and preventing deployment regressions.

## Preconditions
- You are working on the local workspace (not browser-only).
- Docker Desktop (macOS) or equivalent local runtime is available.

## Step 1: Confirm Workspace State
- Verify you are on the intended branch and up-to-date with local changes.
- Confirm Session 14 docs reference the same branch/commit you are testing.

Suggested commands:
```bash
git status -sb
git log --oneline -n 5
```

## Step 2: Rebuild Local Containers (Avoid Stale Mounts)
- Docker Desktop can serve stale files; rebuild images to ensure code parity.

Suggested commands:
```bash
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up -d --build
```

## Step 3: Verify Backend Starts Cleanly
- Tail logs and confirm no crashloop or ImportError.

Suggested commands:
```bash
docker compose -f docker-compose.local.yml logs -f backend
```

## Step 4: Check Dependency Constraints
- Confirm numpy/scipy pins are applied in the running image.

Suggested commands:
```bash
docker compose -f docker-compose.local.yml exec backend python - <<'PY'
import numpy, scipy
print("numpy", numpy.__version__)
print("scipy", scipy.__version__)
PY
```

## Step 5: Run Targeted Tests Locally
- The Session 14 summary claims new tests; run them locally to validate.

Suggested commands:
```bash
docker compose -f docker-compose.local.yml exec backend pytest \
  backend/tests/events/test_schedule_events.py \
  backend/tests/tasks/test_compliance_report_tasks.py \
  backend/tests/api/test_portal_dashboard.py
```

## Step 6: Validate Migrations and DB Health
- Ensure Alembic is aligned with current models before deployment.

Suggested commands:
```bash
docker compose -f docker-compose.local.yml exec backend alembic current
docker compose -f docker-compose.local.yml exec backend alembic heads
```

## Step 7: Confirm API Health
- Check backend responds and key endpoints are reachable.

Suggested commands:
```bash
curl -sS http://localhost:8000/health | jq
curl -sS http://localhost:8000/api/v1/health | jq
```

## Step 8: Record Outcomes
- If any failure occurs, capture logs and the exact command output.
- Attach these to the deployment summary for traceability.

Suggested commands:
```bash
docker compose -f docker-compose.local.yml logs --tail=200 backend > /tmp/backend.log
```

## Notes
- This checklist is local-only and assumes Docker Desktop or equivalent runtime.
- Do not trust docs alone; validate in the running containers.
