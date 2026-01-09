# Session 079: Comprehensive camelCase Fixes

**Date:** 2026-01-09
**PR:** #670

## Problem
Multiple admin pages and features broken due to snake_case → camelCase mismatch.
The axios interceptor converts API responses to camelCase, but frontend code was accessing snake_case properties (returning `undefined`).

## Root Cause
Session 078 fixed some pages, but the issue was pervasive across the codebase.

## Files Fixed (21 total across 2 commits)

### Commit 1: Initial fixes
- `useAdminUsers.ts` - transformApiUser() field names
- `people/page.tsx` - pgy_level filter state
- `rotations/page.tsx` - is_archived
- `compliance/page.tsx` - threshold_status, days_used, etc.
- `faculty-call/page.tsx` - call_type, pcat_created, etc.
- `game-theory/page.tsx` - 20+ snake_case fields

### Commit 2: Comprehensive sweep
- `rotations/page.tsx` - activityType, templateCategory filters
- `swaps/page.tsx` - executedAt, sourceFacultyName, etc.
- `fmit/import/page.tsx` - weekNumber, isHolidayCall, etc.
- `import/[id]/page.tsx` - batch/preview properties
- `settings/page.tsx` - workHoursPerWeek, etc.
- `schedule/page.tsx` - event.eventType
- `daily-manifest/types.ts` - all interface fields
- `daily-manifest/*.tsx` - all property accesses
- `procedures/ProcedureForm.tsx` - form data fields

## Pattern
All fixes follow: `something_case` → `somethingCase`

## Verification
- /admin/rotations - templates display correctly
- /admin/people - shows 29/29 people
- /daily-manifest - loads correctly
- Other admin pages functional

## Next Steps
- Merge PR #670
- Monitor for any remaining snake_case issues
