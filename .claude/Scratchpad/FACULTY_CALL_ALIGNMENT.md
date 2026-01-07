# Faculty Call Alignment

**Branch:** `session/067-antigravity-faculty-call` | **Date:** 2026-01-07

## Restore This State

```bash
git checkout session/067-antigravity-faculty-call
docker-compose -f docker-compose.local.yml up -d --build

# DB constraint (if call_type errors)
docker exec scheduler-local-db psql -U scheduler -d residency_scheduler -c "
  ALTER TABLE call_assignments DROP CONSTRAINT IF EXISTS check_call_type;
  ALTER TABLE call_assignments ADD CONSTRAINT check_call_type
    CHECK (call_type IN ('sunday', 'weekday', 'holiday', 'backup'));
"
```

## Dev Environment

**CORRECT:** `docker-compose -f docker-compose.local.yml up -d`

| Service | Hot Reload | Port |
|---------|------------|------|
| Backend | ✓ | 8000 |
| Frontend | ✓ | 3000 |
| MCP | ✓ | 8080 |

**WRONG:** `docker-compose.yml + docker-compose.dev.yml` (broken frontend)

## Fixes Applied

| File | Fix |
|------|-----|
| `backend/app/controllers/call_assignment_controller.py` | Added `model_validate()` |
| `backend/app/api/routes/rotation_templates.py` | Added `model_validate()` |
| `backend/app/schemas/rotation_template.py` | Added `academic`, `clinical`, `leave` to valid types |
| `backend/app/schemas/call_assignment.py` | `call_date` aliased to `date` |
| `frontend/src/app/admin/faculty-call/page.tsx` | Null safety in transform |
| `backend/scripts/seed_antigravity.py` | Fixed `.append()` bug on int counter |

## Data

| Type | Count | Jan 2026 |
|------|-------|----------|
| sunday | 52 | 4 |
| weekday | 206 | 17 |
| holiday | 4 | 1 |
| backup | 103 | 9 |
| **Total** | **365** | **31** |

## URLs

- `/admin/faculty-call` - Faculty call (31 Jan assignments)
- `/admin/templates` - PCAT/DO templates

## Known Issues Pattern

**Symptom:** React error "Objects are not valid as a React child"
**Cause:** Controller returns raw ORM without `model_validate()`
**Fix:** `items=[Schema.model_validate(item) for item in result["items"]]`
