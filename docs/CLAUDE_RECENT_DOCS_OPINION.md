# Opinionated Read of Recent Docs (for Claude Code)

Purpose: reconcile the most recent local docs and give a single, Docker Desktop–first path to success.

## What the Recent Docs Say (In Plain English)

The latest docs repeat the same core failure modes:
- Docker Desktop on macOS can serve stale files; rebuild images instead of relying on live mounts.
- Most “CORS” issues are backend crashes or 307 redirects; use `/api/v1` directly.
- Schedule generation fails if people + rotation templates aren’t seeded.
- Migration drift is common; run `alembic upgrade head` early.
- Dependency mismatches (numpy/scipy) have caused crashloops.

## Opinion: Too Many Checklists, One Useful Path

There are now multiple overlapping guides:
- `docs/development/DEPLOYMENT_TROUBLESHOOTING.md`
- `docs/development/SESSION_14_LESSONS_LEARNED.md`
- `docs/CLAUDE_DEPLOYMENT_GETTING_UNSTUCK.md`
- `docs/CLAUDE_DOCKER_DESKTOP_DEPLOYMENT_NOTES.md`
- `docs/CLAUDE_LOCAL_DEPLOYMENT_CHECKLIST.md`

They are consistent, but the duplication increases confusion. For Docker Desktop on macOS, use this priority order:
1) `docs/CLAUDE_DOCKER_DESKTOP_DEPLOYMENT_NOTES.md` (fast start)
2) `docs/CLAUDE_DEPLOYMENT_GETTING_UNSTUCK.md` (deep triage)
3) `docs/development/DEPLOYMENT_TROUBLESHOOTING.md` (reference)

Ignore the rest unless you need context or postmortem detail.

## Single “Get It Running” Path (Mac Docker Desktop)

```bash
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml exec backend alembic upgrade head
docker compose -f docker-compose.local.yml exec backend python -m scripts.seed_people
docker compose -f docker-compose.local.yml exec backend python -m scripts.seed_rotation_templates
curl -sS http://localhost:8000/api/v1/health | jq
```

If it still fails, tail backend logs:
```bash
docker compose -f docker-compose.local.yml logs -f backend
```

## Minimum Checks Before Running Schedules

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

If either count is zero, schedules will fail. Seed first.

## Non-Negotiables (Local-Only Reality)

- Use `docker compose` (v2). Docker Desktop defaults to v2.
- Use `/api/v1` from the frontend to avoid 307 CORS traps.
- Rebuild images when debugging; hot mounts are unreliable on macOS.
- Treat “CORS blocked” as “backend crashed” until logs prove otherwise.

## Opinionated Recommendations

- Avoid disabling audit/versioning plugins as a “fix” unless you are explicitly in local-only mode.
- Keep the local wheelhouse in `backend/vendor/wheels` to speed builds and reduce network noise.
- Prefer a single “source of truth” doc for day-to-day ops; the rest should be references only.
