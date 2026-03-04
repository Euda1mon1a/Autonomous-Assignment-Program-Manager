# FMIT Week Display Bug Investigation

**Date:** 2026-01-03
**Status:** Investigation Complete - Bug Confirmed
**Severity:** P2 (Display inconsistency, not data corruption)

## Summary

FMIT weeks display as Thu-Wed in some views instead of the correct Fri-Thu boundary.

## Root Cause Analysis

The bug stems from **inconsistency between constraint logic and display logic**:

### Correct Implementation (Backend Constraints)

**File:** `backend/app/scheduling/constraints/fmit.py`
**Lines:** 45-67

```python
def get_fmit_week_dates(any_date: date) -> tuple[date, date]:
    """
    Get the Friday-Thursday FMIT week containing the given date.

    FMIT weeks run from Friday to Thursday, independent of calendar weeks.
    ...
    """
    # Friday = weekday 4
    day_of_week = any_date.weekday()

    if day_of_week >= 4:  # Fri(4), Sat(5), Sun(6)
        days_since_friday = day_of_week - 4
    else:  # Mon(0), Tue(1), Wed(2), Thu(3)
        days_since_friday = day_of_week + 3

    friday = any_date - timedelta(days=days_since_friday)
    thursday = friday + timedelta(days=6)
    return friday, thursday
```

The constraint system correctly defines FMIT weeks as **Friday (weekday 4) to Thursday (weekday 3)**.

### Incorrect Implementation (Backend Service)

**File:** `backend/app/services/fmit_scheduler_service.py`
**Lines:** 721-732

```python
def _get_week_start(self, any_date: date) -> date:
    """
    Get the Monday of the week containing the given date.
    ...
    """
    days_since_monday = any_date.weekday()
    return any_date - timedelta(days=days_since_monday)
```

This function returns **Monday** as the week start, but FMIT weeks should start on **Friday**.

### Incorrect Implementation (Frontend Timeline)

**File:** `frontend/src/features/fmit-timeline/types.ts`
**Lines:** 258-286

```typescript
export function getWeeksInRange(startDate: string, endDate: string): TimePeriod[] {
  const periods: TimePeriod[] = [];
  const start = new Date(startDate);
  // ...
  const current = new Date(start);
  // ...
  while (current <= end) {
    const weekStart = new Date(current);
    const weekEnd = new Date(current);
    weekEnd.setDate(weekEnd.getDate() + 6);
    // ...
    current.setDate(current.getDate() + 7);  // Simply advances by 7 days
  }
}
```

This function uses **arbitrary date-based iteration** (starting from whatever `startDate` is passed) without adjusting to Friday-Thursday boundaries.

## Impact

1. **Display inconsistency:** FMIT timeline shows weeks that don't match the actual FMIT constraint boundaries
2. **User confusion:** Coordinators may misunderstand when FMIT weeks actually start/end
3. **No data corruption:** The constraint system correctly enforces Fri-Thu, so schedule data is correct

## Recommended Fixes

### Fix 1: Backend Service (Quick Fix)

Update `fmit_scheduler_service.py` to use `get_fmit_week_dates()` from `constraints/fmit.py`:

```python
from app.scheduling.constraints.fmit import get_fmit_week_dates

def _get_week_start(self, any_date: date) -> date:
    """Get the Friday of the FMIT week containing the given date."""
    friday, _ = get_fmit_week_dates(any_date)
    return friday
```

### Fix 2: Frontend Timeline (Required)

Update `getWeeksInRange()` in `types.ts` to align with FMIT Friday-Thursday boundaries:

```typescript
export function getWeeksInRange(startDate: string, endDate: string): TimePeriod[] {
  const periods: TimePeriod[] = [];
  const start = new Date(startDate);
  const end = new Date(endDate);
  const today = new Date();

  // Adjust start to previous Friday (FMIT week boundary)
  const current = new Date(start);
  const dayOfWeek = current.getDay(); // 0=Sun, 5=Fri
  if (dayOfWeek !== 5) {
    // Move to previous Friday
    const daysToFriday = (dayOfWeek + 2) % 7; // Days since last Friday
    current.setDate(current.getDate() - daysToFriday);
  }

  let weekNum = 1;
  while (current <= end) {
    const weekStart = new Date(current); // Friday
    const weekEnd = new Date(current);
    weekEnd.setDate(weekEnd.getDate() + 6); // Thursday

    const isCurrent = today >= weekStart && today <= weekEnd;

    periods.push({
      label: `Week ${weekNum}`,
      start_date: weekStart.toISOString().split('T')[0],
      end_date: (weekEnd > end ? end : weekEnd).toISOString().split('T')[0],
      is_current: isCurrent,
    });

    current.setDate(current.getDate() + 7); // Next Friday
    weekNum++;
  }

  return periods;
}
```

## Files Requiring Changes

| File | Line(s) | Change Type |
|------|---------|-------------|
| `backend/app/services/fmit_scheduler_service.py` | 721-732 | Fix `_get_week_start()` |
| `frontend/src/features/fmit-timeline/types.ts` | 258-286 | Fix `getWeeksInRange()` |

## Testing Requirements

1. Unit test for `get_fmit_week_dates()` (already exists in constraint tests)
2. Unit test for corrected `_get_week_start()` returning Friday
3. Frontend test for `getWeeksInRange()` returning Fri-Thu periods
4. E2E test verifying FMIT timeline displays correct boundaries

## Decision Required

**Complexity Assessment:** Medium
- Backend fix is straightforward (import existing function)
- Frontend fix requires understanding FMIT business logic
- Risk is low since constraint enforcement is already correct

**Recommendation:** Create separate PR to fix this issue with proper test coverage.

---

*Investigation by SYNTHESIZER (AO-2) on 2026-01-03*
