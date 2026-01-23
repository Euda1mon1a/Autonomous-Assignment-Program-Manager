# Session 109: People Hub - Deferred Refactors

**Date:** 2026-01-14
**Branch:** `temp-people-hub-review` (extracted from stash)
**Status:** Documented for future PR

---

## Summary

During forensic extraction of the People Hub stash, we identified 10 refactored pages that consolidate functionality into the new hub structure. These are **deferred** to a follow-up PR to minimize risk.

---

## Refactored Files Analysis

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `admin/faculty-call/page.tsx` | -696 | **Major consolidation** - functionality moved to People Hub |
| `admin/compliance/page.tsx` | -601 | **Major consolidation** - compliance moved to dedicated page |
| `schedule/[personId]/page.tsx` | -293 | **Consolidated** into my-schedule with tier model |
| `admin/faculty-activities/page.tsx` | -178 | **Consolidated** into activities hub |
| `activities/page.tsx` | +/-480 | **Enhanced** with tab structure |
| `compliance/page.tsx` | +565 | **Enhanced** - received consolidated compliance features |
| `my-schedule/page.tsx` | +116 | **Enhanced** with PersonSelector and tier model |
| `call-roster/page.tsx` | +/-26 | Minor adjustments |
| `CallBulkActionsToolbar.tsx` | +/-6 | Minor adjustments |
| `hooks/index.ts` | +1 | Export addition |

**Net change:** -1010 lines (consolidation wins)

---

## Consolidation Pattern

```
BEFORE (scattered):
├── admin/compliance/page.tsx (601 lines)
├── admin/faculty-call/page.tsx (696 lines)
├── admin/faculty-activities/page.tsx (178 lines)
├── schedule/[personId]/page.tsx (293 lines)
└── my-schedule/page.tsx (basic)

AFTER (consolidated):
├── (hub)/people/page.tsx (new hub)
├── my-schedule/page.tsx (unified with tier model)
├── compliance/page.tsx (enhanced)
└── activities/page.tsx (with tabs)
```

---

## Key Changes by File

### admin/faculty-call/page.tsx (-696 lines)
- Faculty call management moved to People Hub
- Bulk actions toolbar simplified
- Call roster functionality centralized

### admin/compliance/page.tsx (-601 lines)
- Compliance views moved to `/compliance` page
- Admin-specific features retained
- ACGME monitoring consolidated

### schedule/[personId]/page.tsx (-293 lines)
- **Merged with my-schedule/page.tsx**
- Uses URL param `?person={id}` instead of route param
- Tier model controls access:
  - Tier 0: Own schedule only
  - Tier 1+: Can view others via PersonSelector

### my-schedule/page.tsx (+116 lines)
- Added PersonSelector (tier 1+)
- Added tier-based RiskBar labels
- Unified schedule viewing hub

### activities/page.tsx (+/-480 lines)
- Added tab structure
- Imports from `./components` (RotationTemplatesTab, FacultyActivityTemplatesTab)
- Cleaner separation of concerns

### compliance/page.tsx (+565 lines)
- Received consolidated compliance features
- Enhanced with more detailed views
- Standalone compliance hub

---

## Dependencies Created (This Session)

To make the stashed code compile, we created:

1. **`src/lib/tierUtils.ts`** (95 lines)
   - `calculateTierFromRole(role)` → RiskTier
   - `getRiskBarTooltip(tier, isViewingOther)`
   - `getRiskBarLabel(tier, isViewingOther)`
   - `canViewOthers(tier)`, `isAdmin(tier)`

2. **`src/components/schedule/PersonSelector.tsx`** (233 lines)
   - Tier-aware person dropdown
   - Groups by PGY level / Faculty
   - Only renders for tier 1+

3. **`src/app/activities/components/`** (352 lines total)
   - `RotationTemplatesTab.tsx` - Grid view of rotation templates
   - `FacultyActivityTemplatesTab.tsx` - Faculty weekly pattern editor
   - `index.ts` - Barrel export

---

## Recommended Follow-Up

### Phase 1 (This PR)
- ✅ New People Hub components
- ✅ tierUtils library
- ✅ PersonSelector component
- ✅ Activities tab components

### Phase 2 (Future PR)
Apply the 10 refactored files:
```bash
git checkout temp-people-hub-review -- \
  frontend/src/app/activities/page.tsx \
  frontend/src/app/admin/compliance/page.tsx \
  frontend/src/app/admin/faculty-activities/page.tsx \
  frontend/src/app/admin/faculty-call/page.tsx \
  frontend/src/app/call-roster/page.tsx \
  frontend/src/app/compliance/page.tsx \
  frontend/src/app/my-schedule/page.tsx \
  "frontend/src/app/schedule/[personId]/page.tsx" \
  frontend/src/components/admin/CallBulkActionsToolbar.tsx \
  frontend/src/hooks/index.ts
```

### Phase 3 (Future)
- Import/Export Hub (stash@{1}) - 1345 new lines
- Similar consolidation pattern

---

## Stash Status

| Stash | Content | Status |
|-------|---------|--------|
| @{0} | people-hub | **Extracted** (was popped to temp branch) |
| @{1} | import-export-hub | Available for future |
| @{2} | holiday-docs | **Applied** (scratchpad update) |
| @{3} | rag-ingestion | Trivial, can drop |

---

## Verification

All new code passes:
- `npm run type-check` ✅
- `npm run lint` ✅ (no errors)
- Hooks order correct (React rules) ✅
- Types aligned with API (RiskTier, RotationTemplate) ✅
