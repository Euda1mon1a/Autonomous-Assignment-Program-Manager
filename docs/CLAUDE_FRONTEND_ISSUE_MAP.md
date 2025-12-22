# Frontend Issue Map (Claude Code)

Purpose: map reported UI issues to likely source files and propose concrete fixes.

## 1) “View full schedule” link broken

Likely source:
- `frontend/src/components/schedule/MyScheduleWidget.tsx`

Observation:
- Footer link points to `/schedule/${currentPerson.id}` or `/schedule?person=me`.
- `/schedule?person=me` is ignored; the schedule page does not read query params.

Concrete fixes:
- Prefer a known-valid route: link to `/my-schedule` when `currentPerson` is missing.
- Or wire `/schedule` to accept `person` query and route to `/schedule/[personId]`.

Suggested change (minimal):
- In `frontend/src/components/schedule/MyScheduleWidget.tsx`, replace the fallback href with `/my-schedule`.

## 2) Templates page shows placeholders / weak fields

Likely sources:
- `frontend/src/app/templates/page.tsx`
- `frontend/src/hooks/useSchedule.ts`

Observations:
- `max_supervision_ratio` is rendered unconditionally; if null/undefined, UI shows `1:undefined`.
- Abbreviation and activity values fall back to `???` or “default” if template missing.

Concrete fixes:
- Guard `max_supervision_ratio` before rendering; show “N/A” or omit.
- If a template is missing, show `assignment.activity_override` or `Assignment` instead of `???`.
- If this is simply missing seed data, seed templates (backend).

Suggested change (minimal UI):
- In `frontend/src/app/templates/page.tsx`, render supervision ratio only when `template.max_supervision_ratio` is not null.
- In schedule views (`frontend/src/app/schedule/page.tsx`, `frontend/src/app/my-schedule/page.tsx`, `frontend/src/components/schedule/ScheduleGrid.tsx`), replace `'???'` with a safer fallback like `'Assignment'`.

## 3) Absences list appears empty

Likely sources:
- `frontend/src/app/absences/page.tsx`
- `frontend/src/hooks/useAbsences.ts`

Observations:
- `AbsencesPage` uses `useAbsences()` (deprecated) which still calls `/absences` but has weaker typing.
- If no absence data is seeded, the list will be empty (expected).

Concrete fixes:
- Switch to `useAbsenceList()` for clarity and future stability.
- Add an explicit empty-state hint to prompt “Add Absence” if the list is empty.

Suggested change:
- Replace `useAbsences()` with `useAbsenceList()` in `frontend/src/app/absences/page.tsx`.

## 4) “My Schedule” redirects to login

Likely sources:
- `frontend/src/components/ProtectedRoute.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/app/my-schedule/page.tsx`

Hypothesis:
- Any 401 from API triggers a global redirect in the axios interceptor.
- If `/blocks`, `/assignments`, or `/rotation-templates` returns 401 transiently, the user is pushed to `/login`.

Concrete fixes:
- Narrow the 401 redirect behavior to `/auth/me` (or auth routes only).
- Prefer a non-destructive error state instead of hard redirect.

Suggested change:
- In `frontend/src/lib/api.ts`, only redirect to `/login` when the failing endpoint is auth-related (e.g., `/auth/me`).

## 5) “Add People” modal closes after 1 character (X button focus)

Likely sources:
- `frontend/src/components/Modal.tsx`
- `frontend/src/components/AddPersonModal.tsx`

Observation:
- Modal focuses the first focusable element, which is the close “X” button.
- This can cause confusing focus behavior on open (typing without clicking input).

Concrete fixes:
- Add `autoFocus` to the Name input, or
- Update Modal to focus the first input element instead of the close button.

Suggested change (minimal):
- Add `autoFocus` to the Name input in `frontend/src/components/AddPersonModal.tsx`.

## 6) Block view hard limits should not be user-settable

Likely source:
- `frontend/src/components/schedule/BlockNavigation.tsx`

Observation:
- Date range inputs are editable; users can set arbitrary ranges, but the block view should reflect the fixed 4-week block for a given block date.

Concrete fixes:
- Make the date inputs read-only or remove them in block view.
- Keep navigation via “Previous/Next Block” and “This Block” only.

Suggested change:
- Disable the date inputs in `frontend/src/components/schedule/BlockNavigation.tsx` or render them as read-only display.

---

## Suggested Next Step Order (Fastest UX Wins)
1) Fix “View full schedule” link fallback.  
2) Narrow the 401 redirect in `frontend/src/lib/api.ts`.  
3) Add input autofocus for Add Person modal.  
4) Make block view dates read-only.  
5) Clean up template placeholders and absences list.  
