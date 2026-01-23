# Session 101 Handoff: Inpatient Rotation Pattern Fallbacks

**Date:** 2026-01-14
**Branch:** `feat/exotic-explorations`
**Status:** IN PROGRESS - Adding belt-and-suspenders for ALL inpatient rotations

---

## TL;DR for Next Session

**Belt and Suspenders Approach:** All inpatient rotations need explicit pattern handling in the expansion service as fallback. Primary source is imported xlsx data; expansion service provides safety net if gaps exist.

**Completed:**
- KAP pattern: `_get_kapiolani_assignment()` ✅
- LDNF pattern: `_get_ldnf_assignment()` ✅
- All 24 ROSETTA tests passing ✅

**TODO - Add explicit handling for:**
- FMIT (FM Inpatient Team) - stamps FMIT all day
- NF (Night Float) - OFF AM / NF PM
- PedNF (Peds Night Float) - OFF AM / PedNF PM
- PedW (Peds Ward) - stamps PedW all day
- IM (Internal Medicine) - stamps IM all day, works weekends

---

## Implementation Pattern

Follow the same pattern as KAP/LDNF:

### 1. Add Constants
```python
FMIT_ROTATIONS = frozenset(["FMIT", "FMIT 2", "FM Inpatient Team"])
NF_ROTATIONS = frozenset(["NF", "Night Float"])
PEDNF_ROTATIONS = frozenset(["PedNF", "Peds NF", "Peds Night Float"])
PEDW_ROTATIONS = frozenset(["PedW", "Peds Ward", "Pediatrics Ward"])
IM_ROTATIONS = frozenset(["IM", "Internal Medicine"])
```

### 2. Add Pattern Methods
```python
def _get_fmit_assignment(self, current_date, time_of_day, is_last_wed) -> str:
    if is_last_wed:
        return "LEC" if time_of_day == "AM" else "ADV"
    return "FMIT"  # All day FMIT

def _get_nf_assignment(self, current_date, time_of_day, is_last_wed) -> str:
    if is_last_wed:
        return "LEC" if time_of_day == "AM" else "ADV"
    return "OFF" if time_of_day == "AM" else "NF"

def _get_pednf_assignment(self, current_date, time_of_day, is_last_wed) -> str:
    if is_last_wed:
        return "LEC" if time_of_day == "AM" else "ADV"
    return "OFF" if time_of_day == "AM" else "PedNF"

def _get_pedw_assignment(self, current_date, time_of_day, is_last_wed) -> str:
    if is_last_wed:
        return "LEC" if time_of_day == "AM" else "ADV"
    return "PedW"  # All day PedW

def _get_im_assignment(self, current_date, time_of_day, is_last_wed) -> str:
    if is_last_wed:
        return "LEC" if time_of_day == "AM" else "ADV"
    return "IM"  # All day IM (works weekends)
```

### 3. Add to Slot Assignment Loop
Add blocks similar to KAP/LDNF handling at ~line 575 in `_expand_single_block_assignment()`.

---

## Files

| File | Status |
|------|--------|
| `backend/app/services/block_assignment_expansion_service.py` | IN PROGRESS |
| `docs/scheduling/EXPANSION_SERVICE_BUGS.md` | Reference |
| `docs/scheduling/EXPANSION_SERVICE_FIXES.md` | Reference |

---

## Test Commands

```bash
# Run ROSETTA tests
docker exec residency-scheduler-backend pytest tests/scheduling/test_expansion_vs_rosetta.py -v

# Re-export and compare
docker exec residency-scheduler-backend python -c "
from datetime import date
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.block_format_exporter import BlockFormatExporter

DATABASE_URL = settings.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

async def export():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        exporter = BlockFormatExporter(session)
        xlsx_bytes = await exporter.export(date(2026, 3, 12), date(2026, 4, 8))
        with open('/app/Block10_OUTPUT.xlsx', 'wb') as f:
            f.write(xlsx_bytes)
        print(f'Exported {len(xlsx_bytes)} bytes')
    await engine.dispose()

asyncio.run(export())
"
docker cp residency-scheduler-backend:/app/Block10_OUTPUT.xlsx ./Block10_OUTPUT.xlsx
```

---

## References

- **Plan:** `.claude/plans/dynamic-giggling-sprout.md`
- **Ground Truth:** `docs/scheduling/Block10_ROSETTA_CORRECT.xlsx`
- **Bug Report:** `docs/scheduling/EXPANSION_SERVICE_BUGS.md`
- **Fix Guide:** `docs/scheduling/EXPANSION_SERVICE_FIXES.md`
