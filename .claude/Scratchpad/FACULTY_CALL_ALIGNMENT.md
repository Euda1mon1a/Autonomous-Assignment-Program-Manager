# Faculty Call Alignment

> **Branch:** `feat/faculty-call-alignment` (commit `c383e145`)
> **Date:** 2026-01-07
> **Status:** Complete, ready for use

---

## Quick Reference

### Restore This State

```bash
# Code
git checkout feat/faculty-call-alignment

# Database (run inside container or with docker exec)
docker exec scheduler-local-backend python -m scripts.seed_antigravity --clear
```

### Call Types (aligned across stack)

| Type | Description | Day |
|------|-------------|-----|
| `sunday` | Sunday overnight | Sunday |
| `weekday` | Mon-Thu overnight | Mon-Thu |
| `holiday` | Federal holiday call | Holidays |
| `backup` | Backup/second call | Fri-Sat |

### Post-Call Flow

```
Faculty has call on Date X
  → Day X+1 AM: PCAT (Post-Call AM Time)
  → Day X+1 PM: DO (Day Off)
```

---

## Files Modified

| File | Change |
|------|--------|
| `backend/app/models/call_assignment.py` | CHECK constraint → `sunday/weekday/holiday/backup` |
| `backend/app/schemas/call_assignment.py` | CallType enum + validators aligned |
| `backend/scripts/seed_antigravity.py` | Added PCAT/DO templates, faculty call seeding |
| `frontend/src/types/faculty-call.ts` | Removed `senior`, aligned types |
| `frontend/src/features/call-roster/index.ts` | Fixed `isOnCallTemplate` export |

---

## Seed Script Details

### What Gets Created

| Entity | Count | Notes |
|--------|-------|-------|
| Users | 12 | All 8 RBAC roles |
| Residents | 45 | 15 per PGY (1, 2, 3) |
| Faculty | 10 | PD, APD, OIC, Dept Chief, 2x Sports Med, 4x Core |
| Rotation Templates | 16 | Including PCAT, DO |
| Blocks | 730 | Full AY (365 days × AM/PM) |
| Assignments | ~15K | Residents cycling through rotations |
| Faculty Call | ~200 | 6 months of sunday/weekday/holiday/backup |

### Rotation Templates

```
Inpatient, Outpatient Clinic, Night Float, Call, FMIT,
Sports Medicine, Procedures, Conference, Annual Leave,
Sick Leave, TDY, Deployment, Recovery, Off,
Post-Call AM (PCAT), Day Off (DO)
```

---

## Database State

```sql
-- Verify constraint
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'call_assignments'::regclass
  AND conname = 'check_call_type';

-- Check call assignments by type
SELECT call_type, COUNT(*)
FROM call_assignments
GROUP BY call_type;

-- Verify PCAT/DO templates
SELECT name, abbreviation, activity_type
FROM rotation_templates
WHERE abbreviation IN ('PCAT', 'DO');
```

---

## Frontend Integration

### Admin Page
`/admin/faculty-call` - Faculty call management

### Types Location
`frontend/src/types/faculty-call.ts`

### Key Components
- `CallAssignmentTable` - Display/edit call assignments
- `useCallAssignments` hook - Data fetching

---

## API Endpoints

```
GET    /api/v1/call-assignments
POST   /api/v1/call-assignments
GET    /api/v1/call-assignments/{id}
PUT    /api/v1/call-assignments/{id}
DELETE /api/v1/call-assignments/{id}
POST   /api/v1/call-assignments/bulk
GET    /api/v1/call-assignments/coverage
GET    /api/v1/call-assignments/equity
```

---

## Notes

- **Resident call** is handled separately via Night Float rotation assignments, not `call_assignments` table
- **Faculty call** uses `call_assignments` table with types: sunday/weekday/holiday/backup
- **PCAT auto-assignment** not yet implemented - templates exist for manual assignment

---

## Related Files

- `.antigravity/GUI_TEST_PROMPT.md` - GUI testing checklist
- `docs/rag-knowledge/scheduling-policies.md` - Policy reference
- `backend/app/api/routes/call_assignments.py` - API routes
