# Session Progress - 2026-01-19 (Block 10 GUI)

> **Status:** PR #758 READY FOR MERGE
> **PR:** https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/pull/758
> **Branch:** `feat/block10-gui-human-corrections`

---

## Completed This Session

### 1. Block Navigation Fix
**Root Cause:** Blocks from different academic years (AY 2024, AY 2025) had same `block_number` and were merged by `useBlockRanges`, creating 2-year spans.

**Fix:** Group blocks by `${academicYear}-${blockNum}` composite key instead of just `blockNumber`.

**Files:**
- `frontend/src/hooks/useBlocks.ts` - Added `academicYear` calculation, composite key grouping

### 2. People API 500 Fix
**Root Cause:** `performs_procedures` field was NULL in DB but schema expected boolean.

**Fix:** Added field validator to coerce NULL → False.

**File:** `backend/app/schemas/person.py`

### 3. Couatl Killer Violations
**Root Cause:** Query params sent as camelCase but backend expects snake_case.

**Fix:** Changed to snake_case (`start_date`, `end_date`, `block_number`).

**Files:**
- `frontend/src/hooks/useBlocks.ts`
- `frontend/src/api/resilience.ts`

---

## Verified Working

- Block 8 (current) → Block 9 → **Block 10 (Mar 13 - Apr 9, 2025)** ✅
- Proper 4-week date ranges (not 2-year spans)
- Schedule data loading with assignments
- People loading correctly

---

## WebSocket "Reconnecting" Status

**Not a bug** - user is not logged in. Anonymous viewing works, but real-time updates require auth.

---

## Remaining Issue: Activity Template Editing

User wants to correct a few display abbreviations (e.g., "ACS" → "aSM" for Academic Sports Medicine).

**Current State:**
- Activity Hub shows templates with abbreviations
- Cards are NOT clickable - no edit modal opens
- `RotationTemplatesTab.tsx` has `canEdit` prop but click handling incomplete

**Next Steps:**
1. Investigate `RotationTemplatesTab.tsx` click handling
2. Add/fix edit modal for templates
3. Or provide direct DB update for quick fix

---

## Codex Feedback (Partially Addressed)

| Item | Status |
|------|--------|
| Block filters camelCase query params | ✅ Fixed |
| WebSocket URL construction | ⏳ Separate issue (user not logged in) |
| Resilience hooks calling non-existent endpoints | ⏳ Separate PR |
| Absence enum sync drift | ⏳ Separate PR |

---

## Commits in PR #758

1. `3cda8053` - fix: Block navigation, people API validation, and Couatl Killer violations
2. `7bfb844f` - docs: Add Block 10 GUI fixes to MASTER_PRIORITY_LIST

---

*Last Updated: 2026-01-19*
