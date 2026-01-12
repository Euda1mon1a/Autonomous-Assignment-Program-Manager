# Session 2026-01-12: Couatl Killer (Query Param Fix)

## TL;DR
Fixed GUI failure after UI consolidation. Root cause: camelCase query params in URLs (axios interceptor only converts body, not query strings). Created pre-commit hook to prevent recurrence.

## Commits (5 total)
```
7450104b refactor: Rename query param hook to Couatl Killer
79429aa4 feat: Add pre-commit hook to prevent camelCase query params
b029530d fix: Convert remaining camelCase query params to snake_case
4f8c66e5 fix: Use snake_case query params for backend API compatibility
30e42e2a fix: Frontend consolidation cleanup + API proxy fix (prior)
```

## Root Cause
```typescript
// WRONG - axios interceptor doesn't convert URL query strings
get(`/assignments?startDate=${date}&pageSize=500`)

// CORRECT - backend expects snake_case
get(`/assignments?start_date=${date}&page_size=500`)
```

## New Pre-commit Hook: Couatl Killer
- **File:** `scripts/couatl-killer.sh`
- **Hook ID:** `couatl-killer` (Phase 6b)
- **Pattern:** Catches `startDate|endDate|pageSize|personId|...`
- **Escape:** `// @query-param-ok` comment

## Files Fixed (19 violations across 12+ files)
- Hooks: useAssignmentsForRange, useSchedule, useAbsences, usePeople, useSwaps, useFacultyActivities
- Components: my-schedule, CalendarExportButton, AbsenceGrid, ScheduleGrid, PersonalScheduleHub, UpcomingAssignmentsPreview, BlockAnnualView, drag views
- Features: conflicts/hooks, audit/hooks

## RAG Ingested
- Minimum Viable Context (MVC) document for agent spawning

## Dev Environment
- Frontend dev server was running at :3002 (background task b9bdf66)
- Docker containers healthy

## Remaining Unstaged (from prior sessions)
- backend/app/api/routes/assignments.py
- frontend/src/hooks/index.ts
- Various .claude/Scratchpad/*.md files
- docs/scheduling/

## Key Learnings
1. Axios interceptor converts BODY keys only, not URL query strings
2. TypeScript types don't catch runtime string issues
3. Pre-commit hooks with grep are effective for pattern enforcement
