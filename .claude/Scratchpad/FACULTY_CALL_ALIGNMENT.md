# Faculty Call Alignment

**Branch:** `session/067-antigravity-faculty-call` | **Date:** 2026-01-07

## Restore This State

```bash
git checkout session/067-antigravity-faculty-call
docker-compose -f docker-compose.local.yml up -d --build

# Update DB constraint (if needed)
docker exec scheduler-local-db psql -U scheduler -d residency_scheduler -c "
  ALTER TABLE call_assignments DROP CONSTRAINT IF EXISTS check_call_type;
  ALTER TABLE call_assignments ADD CONSTRAINT check_call_type
    CHECK (call_type IN ('sunday', 'weekday', 'holiday', 'backup'));
"

# Seed call data (365 assignments for AY 2025-2026)
docker exec scheduler-local-backend python -c "
import asyncio
from datetime import date, timedelta
from uuid import uuid4
from sqlalchemy import text
from app.db.session import async_engine

async def seed():
    async with async_engine.begin() as conn:
        await conn.execute(text('TRUNCATE call_assignments CASCADE'))
        faculty = [r[0] for r in (await conn.execute(text(\"SELECT id FROM people WHERE type='faculty' LIMIT 10\"))).fetchall()]
        start, end, count = date(2025,7,1), date(2026,6,30), 0
        current = start
        while current <= end:
            dow = current.weekday()
            fid = faculty[(current-start).days % len(faculty)]
            ct = 'holiday' if (current.month,current.day) in {(1,1),(7,4),(11,11),(12,25)} else 'sunday' if dow==6 else 'weekday' if dow<4 else 'backup'
            await conn.execute(text('INSERT INTO call_assignments (id,date,person_id,call_type,is_weekend,is_holiday) VALUES (:i,:d,:p,:c,:w,:h)'),
                {'i':str(uuid4()),'d':current,'p':str(fid),'c':ct,'w':dow in(5,6),'h':(current.month,current.day) in {(1,1),(7,4),(11,11),(12,25)}})
            count += 1; current += timedelta(days=1)
        print(f'Seeded {count} call assignments')
asyncio.run(seed())
"
```

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
