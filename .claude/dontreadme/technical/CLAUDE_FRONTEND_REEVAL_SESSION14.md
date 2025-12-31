# Frontend Re-evaluation (Session 14 Input)

Purpose: capture the user-reported frontend issues, align them with Session 14 notes, and highlight what still needs verification in the local build.

## Reference
- `docs/development/SESSION_14_FRONTEND_ISSUES.md`

## User-Reported Issues (Latest Input)

1) View full schedule link broken  
2) Templates page shows placeholders  
3) Absences empty  
4) Compliance works  
5) Help works  
6) Settings toggled for admin  
7) Add people modal bug: one character entered and X close selected  
8) My schedule redirects to login after interaction  
9) Block view should show hard limits based on block date (not settable)

## Alignment With Session 14 Notes

Already marked fixed in Session 14 doc:
- View full schedule link (ScheduleSummary)  
- Add people modal focus bug (Modal focus behavior)  

If these still reproduce locally, assume stale build or a second, different codepath.

Open / unresolved in Session 14 doc:
- Templates placeholders  
- My schedule redirects to login  
- Block view date inputs should be read-only  
- Absences empty (likely no seed data)

## What Still Needs Local Verification

1) Confirm “fixed” changes are present in the running frontend
- `frontend/src/components/dashboard/ScheduleSummary.tsx`
- `frontend/src/components/Modal.tsx`

2) My Schedule redirect cause
- Check if `/blocks` or `/assignments` returns 401 and triggers the global redirect in `frontend/src/lib/api.ts`.

3) Templates placeholders
- Confirm `/api/v1/rotation-templates` returns items in the Network tab and that the page is not stuck in a loading state.

4) Absences
- Confirm absences are actually seeded before treating this as a UI bug.

5) Block view “hard limits”
- Block date inputs are editable in `frontend/src/components/schedule/BlockNavigation.tsx`; if desired, make them read-only.

## Suggested Next Action Order (Local Build)

1) Rebuild frontend (Docker Desktop): `docker compose -f docker-compose.local.yml up -d --build frontend`
2) Verify the two “fixed” items are resolved.
3) Check My Schedule redirect with Network tab open.
4) Confirm templates API data and rendering state.
5) Seed absences before re-evaluating the absences view.
