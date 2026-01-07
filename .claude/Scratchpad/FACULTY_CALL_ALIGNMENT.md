# Faculty Call Alignment

**Branch:** `session/067-antigravity-faculty-call` | **Date:** 2026-01-07

## Dev Environment (CRITICAL)

**USE THIS COMMAND:**
```bash
docker-compose -f docker-compose.local.yml up -d --build
```

| Service | Hot Reload | Notes |
|---------|------------|-------|
| Backend | ✓ Yes | Volume mount + uvicorn --reload |
| Frontend | ✓ Yes | Volume mount + npm run dev |
| MCP | ✓ Yes | Port 8080 |

**DO NOT USE:** `docker-compose.yml + docker-compose.dev.yml` (broken frontend)

## Call Types

| Type | When | Count (full AY) |
|------|------|-----------------|
| `sunday` | Sunday | 52 |
| `weekday` | Mon-Thu | 206 |
| `holiday` | Federal holidays | 4 |
| `backup` | Fri-Sat | 103 |

**Total:** 365 assignments | **Jan 2026:** 31 assignments

## Files Changed

- `backend/app/controllers/call_assignment_controller.py` - Added `model_validate()` to fix API crash
- `backend/app/schemas/call_assignment.py` - `call_date` aliased to `date`
- `frontend/src/app/admin/faculty-call/page.tsx` - Null safety in transform

## Quick Reference

| Task | Command |
|------|---------|
| Start dev | `docker-compose -f docker-compose.local.yml up -d` |
| View logs | `docker-compose -f docker-compose.local.yml logs -f backend` |
| Rebuild | `docker-compose -f docker-compose.local.yml up -d --build` |
| Check staleness | `./scripts/diagnose-container-staleness.sh` |

## DB Constraint

If call_type errors, update constraint:
```sql
ALTER TABLE call_assignments DROP CONSTRAINT check_call_type;
ALTER TABLE call_assignments ADD CONSTRAINT check_call_type
  CHECK (call_type IN ('sunday', 'weekday', 'holiday', 'backup'));
```

## URLs

- `/admin/faculty-call` - Faculty call management (31 Jan assignments)
- `/admin/templates` - PCAT/DO templates
