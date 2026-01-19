# GUI Regression Analysis - Schedule Navigation Broken

> **Date:** 2026-01-19
> **Status:** ROOT CAUSE IDENTIFIED
> **Priority:** HIGH - Blocks Block 10 workflow

---

## Problem

Schedule page (`/schedule`) navigation buttons don't work:
- Clicking "Next Block" stays on Block 0
- UI layout looks degraded ("out of whack")
- "Failed to load schedule data" error

---

## Root Cause: Pagination Bug in useBlockRanges()

**File:** `frontend/src/hooks/useBlocks.ts` line 164

```typescript
// BUG: Fetches /blocks without pagination - only gets first page!
const response = await get<ListResponse<Block>>('/blocks')
```

**The Problem:**
1. Database has **1,516 blocks** total
2. `/blocks` endpoint returns paginated results (default ~100 per page)
3. `useBlockRanges()` only fetches the first page
4. Only Block 0 ends up in the `blockRanges` array
5. Navigation can't find Block 1, 2, 3... so buttons do nothing

**Evidence:**
- Block 0 shows date range "Jul 4, 2024 - Jul 28, 2026" (2+ years!)
- This is because all 100 blocks in first page happen to be Block 0
- Database query confirmed: 1,516 blocks exist, but only ~100 returned

---

## Fix Options

### Option A: Add pagination loop (Quick Fix)
```typescript
queryFn: async () => {
  let allBlocks: Block[] = []
  let page = 1
  let hasMore = true

  while (hasMore) {
    const response = await get<ListResponse<Block>>(`/blocks?page=${page}&limit=500`)
    allBlocks = [...allBlocks, ...response.items]
    hasMore = response.items.length === 500
    page++
  }
  // ... rest of grouping logic
}
```

### Option B: Create dedicated backend endpoint (Better)
```python
# backend/app/api/routes/blocks.py
@router.get("/blocks/ranges")
async def get_block_ranges():
    """Return aggregated block ranges without pagination."""
    # SQL: SELECT block_number, MIN(date), MAX(date) GROUP BY block_number
```

### Option C: Use existing block data smarter
The schedule page already has `blockRanges` data from API - check if it's being used correctly.

---

## Other Issues Found

### 1. Absence Type Enum Mismatch
**File:** `backend/app/schemas/absence.py`
- Database has `training` (6 records) and `military_duty` (1 record)
- Pydantic enum doesn't include these
- Causes API validation errors

### 2. Resilience Hub Crash
**File:** `frontend/src/features/resilience/DefenseLevel.tsx`
- `TypeError: Cannot read properties of undefined (reading 'bgColor')`
- Missing null check when API returns no data

### 3. No Assignments in Current Date Range
- Jan 19 - Feb 18, 2026: **0 assignments**
- Block 10 (Mar 12 - Apr 8, 2026): **1,008 assignments**
- Frontend shows "Failed to load" because current range is empty

---

## Database Status (Verified)

| Table | Count |
|-------|-------|
| people | 33 |
| assignments | 5,240 |
| blocks | 1,516 |
| rotation_templates | 87 |
| absences | 129 |
| call_assignments | 366 |

---

## Files to Fix

| Priority | File | Issue |
|----------|------|-------|
| P0 | `frontend/src/hooks/useBlocks.ts:164` | Pagination bug in useBlockRanges |
| P1 | `backend/app/schemas/absence.py` | Add training, military_duty to enum |
| P2 | `frontend/src/features/resilience/DefenseLevel.tsx` | Null check for bgColor |

---

## Stack Status

- All 7 containers: Healthy (21+ hours)
- RAG: 96 documents, healthy
- MCP: Responsive
- Database: Data exists, queries work

**Slowness:** Docker bind mounts on macOS (not resource issue)

---

## Next Steps

1. Fix `useBlockRanges()` pagination to fetch all blocks
2. Test navigation works after fix
3. Fix absence_type enum
4. Fix DefenseLevel null check

---

*Analysis by Claude Code - Chrome browser automation + code review*

---

## COMPACT HANDOFF - Continue After Context Reset

### Task
Fix GUI regressions preventing Block 10 scheduling workflow

### Immediate Fix Required
**File:** `frontend/src/hooks/useBlocks.ts`
**Function:** `useBlockRanges()` starting line 157
**Problem:** Line 164 calls `get<ListResponse<Block>>('/blocks')` without pagination
**Fix:** Add pagination loop to fetch ALL blocks, not just first page

```typescript
// REPLACE line 162-195 with pagination loop:
queryFn: async () => {
  let allBlocks: Block[] = []
  let page = 1
  let hasMore = true

  while (hasMore) {
    const response = await get<ListResponse<Block>>(`/blocks?page=${page}&limit=500`)
    allBlocks = [...allBlocks, ...response.items]
    hasMore = response.items.length === 500
    page++
  }

  // Group blocks by blockNumber and calculate date ranges
  const blockMap = new Map<number, { minDate: string; maxDate: string }>()
  allBlocks.forEach((block) => {
    const existing = blockMap.get(block.blockNumber)
    if (!existing) {
      blockMap.set(block.blockNumber, { minDate: block.date, maxDate: block.date })
    } else {
      if (block.date < existing.minDate) existing.minDate = block.date
      if (block.date > existing.maxDate) existing.maxDate = block.date
    }
  })

  return Array.from(blockMap.entries())
    .map(([blockNumber, { minDate, maxDate }]) => ({
      blockNumber, startDate: minDate, endDate: maxDate,
    }))
    .sort((a, b) => a.blockNumber - b.blockNumber)
}
```

### Secondary Fixes
1. **Absence enum:** Add `training` and `military_duty` to `backend/app/schemas/absence.py`
2. **DefenseLevel crash:** Add null check in `frontend/src/features/resilience/DefenseLevel.tsx`

### Verification After Fix
1. Navigate to `http://localhost:3000/schedule`
2. Click "Next Block" - should advance to Block 1, 2, etc.
3. Navigate to Block 10 (March 2026) - should show 1,008 assignments

### Context
- Stack healthy (7 containers, 21+ hours)
- DB has data: 33 people, 5,240 assignments, 1,516 blocks
- Block 10 data ready: 1,008 assignments for Mar 12 - Apr 8, 2026
- Current date range empty (Jan-Feb 2026 has 0 assignments)
