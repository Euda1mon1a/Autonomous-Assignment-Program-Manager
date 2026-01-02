# Bug Report: Schedule View 28-Day Alignment

> **Identified:** 2026-01-01 (Session 046)
> **Priority:** P2 (UX issue, not blocking)
> **Status:** Diagnosed, fix pending

---

## Problem Statement

Two related issues with schedule navigation:

1. **Wrong date alignment:** Schedule defaults to a 28-day window starting from the current week's **Monday** instead of aligning with actual academic block boundaries (which start on **Thursdays**)

2. **Missing block number:** Navigation shows only date range (e.g., "Dec 18 - Jan 14") but should display **"Block 7 (Dec 18 - Jan 14)"** for clarity

### Expected Behavior
- Schedule should default to the current academic block
- Today (Jan 1, 2026) should show: **"Block 7 (Dec 18 - Jan 14, 2026)"**
- Navigation should display block number prominently

### Actual Behavior
- Schedule shows Dec 30, 2025 → Jan 26, 2026 (Monday-based 28-day window)
- 3-day offset from actual block boundaries
- No block number displayed, only date range

---

## Root Cause

### File 1: `frontend/src/app/schedule/page.tsx` (lines 62-69)

```typescript
const getInitialDates = () => {
  const today = new Date()
  const monday = startOfWeek(today, { weekStartsOn: 1 })  // ← BUG: Uses Monday
  return {
    start: monday,
    end: addDays(monday, 27),
  }
}
```

### File 2: `frontend/src/components/schedule/BlockNavigation.tsx` (lines 21-25)

```typescript
const getCurrentBlockStart = () => {
  const today = new Date()
  const monday = startOfWeek(today, { weekStartsOn: 1 })  // ← BUG: Uses Monday
  return monday
}
```

---

## Fix Options

### Option A: Query Backend for Block Boundaries (Recommended)

```typescript
// Fetch current block from API
const { data: currentBlock } = useQuery({
  queryKey: ['current-block'],
  queryFn: () => get('/blocks/current'),  // Returns block containing today's date
})

const getInitialDates = () => {
  if (currentBlock) {
    return {
      start: new Date(currentBlock.start_date),
      end: new Date(currentBlock.end_date),
      blockNumber: currentBlock.block_number,  // Include block number
    }
  }
  // Fallback to today's date until block loads
  return { start: new Date(), end: addDays(new Date(), 27), blockNumber: null }
}
```

**Pros:** Uses source of truth, handles leap years, Block 0/13 edge cases, includes block number
**Cons:** Requires API call, slight delay on initial load

### BlockNavigation.tsx Update Required

```typescript
// Current display (line 124-125):
<span className="font-medium">
  {format(startDate, 'MMM d')} - {format(endDate, 'MMM d, yyyy')}
</span>

// Should become:
<span className="font-medium">
  Block {blockNumber} ({format(startDate, 'MMM d')} - {format(endDate, 'MMM d, yyyy')})
</span>
```

### Option B: Calculate Block Boundaries Frontend

```typescript
const getBlockForDate = (date: Date): { start: Date; end: Date } => {
  const AY_START = new Date(2025, 6, 1)  // July 1, 2025
  const BLOCK_0_DAYS = 2  // Orientation
  const BLOCK_DAYS = 28

  const daysSinceAYStart = Math.floor((date.getTime() - AY_START.getTime()) / (1000 * 60 * 60 * 24))

  if (daysSinceAYStart < BLOCK_0_DAYS) {
    // Block 0 (Orientation)
    return { start: AY_START, end: addDays(AY_START, 1) }
  }

  const daysAfterBlock0 = daysSinceAYStart - BLOCK_0_DAYS
  const blockNumber = Math.floor(daysAfterBlock0 / BLOCK_DAYS) + 1
  const blockStart = addDays(AY_START, BLOCK_0_DAYS + (blockNumber - 1) * BLOCK_DAYS)

  return { start: blockStart, end: addDays(blockStart, blockNumber === 13 ? 26 : 27) }
}
```

**Pros:** No API call needed
**Cons:** Hardcoded academic year, requires updates each year

---

## Academic Block Reference

| Block | Start (Thu) | End (Wed) | Days |
|-------|-------------|-----------|------|
| 0 | Tue Jul 1 | Wed Jul 2 | 2 |
| 1 | Thu Jul 3 | Wed Jul 30 | 28 |
| ... | ... | ... | 28 |
| 7 | Thu Dec 18 | Wed Jan 14 | 28 |
| ... | ... | ... | 28 |
| 13 | Thu Jun 4 | Tue Jun 30 | 27 |

---

## Related

- Source of truth: `docs/architecture/ACADEMIC_YEAR_BLOCKS.md`
- Backend block API: `/api/v1/blocks`
- useBlocks hook: `frontend/src/lib/hooks/useBlocks.ts`

---

*Bug identified during Session 046 prerequisites investigation*
