# Block 0 Fudge Factor - Critical Date Alignment

> **CRITICAL:** This is a P0 issue. Without correct Block 0 handling, ALL rotation dates will be wrong throughout the system.

## The Problem

Medical residency programs operate on an **Academic Year (AY)** that starts July 1st, not January 1st. The schedule is divided into 13 four-week blocks:

| Block | Dates (AY 2025-2026) |
|-------|---------------------|
| Block 1 | Jul 1 - Jul 28 |
| Block 2 | Jul 29 - Aug 25 |
| ... | ... |
| Block 13 | Jun 3 - Jun 30 |

**Block 0** is a special case: it represents the partial week before Block 1 officially starts, OR the alignment period when the academic year doesn't start exactly on a Monday.

## Why It Keeps Breaking

This calculation touches multiple layers:

1. **Seed Script** (`backend/scripts/seed_antigravity.py`)
   - `_calculate_block_number()` method
   - Block generation in `_seed_blocks()`

2. **Backend Scheduling** (`backend/app/scheduling/`)
   - Block date range calculations
   - Assignment date validation

3. **Frontend Display** (`frontend/src/`)
   - Block navigation components
   - Date picker logic
   - Schedule grid rendering

When ANY of these gets the offset wrong, the entire schedule shifts.

## The Fudge Factor

The "fudge factor" is the day-of-week offset needed to align Block 1 with the actual start of rotations.

```python
# Example: If July 1, 2025 is a Tuesday
# Block 1 should start on the MONDAY of that week (June 30)
# OR the following Monday (July 7) depending on program policy

def get_block_start_date(academic_year: int, block_number: int) -> date:
    ay_start = date(academic_year, 7, 1)

    # THE FUDGE: Align to Monday
    days_since_monday = ay_start.weekday()  # 0=Mon, 6=Sun
    if days_since_monday > 0:
        # Option A: Roll back to previous Monday (Block 0 covers the gap)
        block_1_start = ay_start - timedelta(days=days_since_monday)
        # Option B: Roll forward to next Monday (no Block 0)
        # block_1_start = ay_start + timedelta(days=(7 - days_since_monday))

    return block_1_start + timedelta(weeks=4 * (block_number - 1))
```

## Regression History

| Date | Issue | Fix Location |
|------|-------|--------------|
| 2026-01-06 | Block dates off for Block 10+ | TBD |
| [Previous] | Block 0 missing | seed script |
| [Previous] | Off-by-one in frontend | date picker |

## Testing Requirements

**BEFORE MERGING ANY DATE-RELATED CHANGES:**

```python
def test_block_dates_align_with_academic_year():
    """Block 1 must start on or near July 1."""
    block_1 = get_block_start_date(2025, 1)
    assert block_1.month == 7 or (block_1.month == 6 and block_1.day >= 28)

def test_block_dates_are_consecutive():
    """No gaps or overlaps between blocks."""
    for i in range(1, 13):
        block_end = get_block_end_date(2025, i)
        next_start = get_block_start_date(2025, i + 1)
        assert next_start == block_end + timedelta(days=1)

def test_all_blocks_are_28_days():
    """Each block is exactly 4 weeks."""
    for i in range(1, 14):
        start = get_block_start_date(2025, i)
        end = get_block_end_date(2025, i)
        assert (end - start).days == 27  # 28 days inclusive
```

## Quick Diagnosis

If block dates look wrong:

1. **Check seed script output:**
   ```bash
   docker compose exec backend python -c "
   from scripts.seed_antigravity import AntigravitySeed
   s = AntigravitySeed(None, 2025)
   print(f'AY Start: {s.ay_start}')
   print(f'Block 1 calc: {s._calculate_block_number(s.ay_start)}')"
   ```

2. **Check database blocks:**
   ```sql
   SELECT block_number, start_date, end_date
   FROM blocks
   WHERE start_date >= '2025-07-01'
   ORDER BY start_date LIMIT 5;
   ```

3. **Check frontend date picker:**
   - Open DevTools > Network
   - Navigate blocks and watch API calls
   - Verify date params match expected block ranges

## Fix Checklist

When fixing Block 0 issues:

- [ ] Update seed script `_calculate_block_number()`
- [ ] Update seed script `_seed_blocks()`
- [ ] Verify backend `Block` model date validation
- [ ] Check frontend block navigation component
- [ ] Run full test suite
- [ ] Re-seed and visually verify in GUI
- [ ] Add regression test if not already covered

---

*This document exists because this bug has regressed multiple times. Please update the regression history table when fixing.*
