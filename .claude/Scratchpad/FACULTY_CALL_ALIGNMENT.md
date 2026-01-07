# Faculty Call Alignment

**Branch:** `feat/faculty-call-alignment` | **Date:** 2026-01-07

## Restore

```bash
git checkout feat/faculty-call-alignment
docker exec residency-scheduler-backend python -m scripts.seed_antigravity --clear
```

## Call Types

| Type | When | Seeded |
|------|------|--------|
| `sunday` | Sunday night | 25 |
| `weekday` | Mon-Thu night | 101 |
| `holiday` | Federal holidays | 3 |
| `backup` | Fri-Sat | 52 |

**Post-call:** PCAT AM + DO PM (templates exist, manual assignment)

## Files Changed

- `backend/app/models/call_assignment.py` - CHECK constraint
- `backend/app/schemas/call_assignment.py` - CallType enum
- `backend/scripts/seed_antigravity.py` - PCAT/DO + faculty call seeding
- `frontend/src/types/faculty-call.ts` - Removed `senior`
- `frontend/src/features/call-roster/index.ts` - Fixed export

## Verify

```sql
SELECT call_type, COUNT(*) FROM call_assignments GROUP BY call_type;
SELECT abbreviation FROM rotation_templates WHERE abbreviation IN ('PCAT','DO');
```

## URLs

- `/admin/faculty-call` - Faculty call management
- `/admin/rotation-templates` - Verify PCAT/DO
- API: `/api/v1/call-assignments`

## Notes

- Resident call = Night Float rotation (not call_assignments table)
- Faculty call = call_assignments table
- Docker issue: If frontend breaks after antigravity, run `docker compose build --no-cache frontend`
