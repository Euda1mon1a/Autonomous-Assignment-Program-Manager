# Session 14 Frontend Issues

> **Date:** 2025-12-22
> **Status:** Documented from user testing
> **Backend Status:** Working (schedule generation, API responses verified)

---

## Issues Identified

### 1. View Full Schedule Link Broken - FIXED (Unverified)
- **Location:** Dashboard ScheduleSummary component
- **Symptom:** Link pointed to "/" instead of "/schedule"
- **Root Cause:** `href="/"` in ScheduleSummary.tsx line 113
- **Fix:** Changed to `href="/schedule"`
- **Status:** FIXED
- **File:** `frontend/src/components/dashboard/ScheduleSummary.tsx`

### 2. View Templates Shows Placeholders
- **Location:** Templates page
- **Symptom:** Not displaying rotation templates correctly
- **Investigation Notes:**
  - API endpoint `/api/v1/rotation-templates` returns correctly: 5 templates with all fields
  - `useRotationTemplates` hook calls correct endpoint
  - Response format matches expected `ListResponse<RotationTemplate>` type
  - TemplateCard component displays: name, activity_type, abbreviation, max_residents, max_supervision_ratio
  - All fields have valid data in API response
- **Possible Causes:**
  1. Page stuck in loading state (showing CardSkeleton placeholders)
  2. Auth issue causing redirect before data loads
  3. React Query caching stale data
  4. Browser console error preventing render
- **Debug Steps Needed:**
  1. Check browser console for JavaScript errors
  2. Check Network tab for /rotation-templates request
  3. Verify response contains items array with 5 templates
- **Status:** API verified working - likely browser-side issue
- **Priority:** Medium

### 3. Absences Page Empty
- **Location:** Absences view
- **Symptom:** No data displayed
- **Note:** No absence data has been seeded - this may be expected behavior
- **Priority:** Low (needs seeding first)

### 4. Add People Input Bug - FIXED (Unverified)
- **Location:** Add People modal / Modal.tsx
- **Symptom:** After entering one character, the X (close) button becomes selected
- **Root Cause:** Modal.tsx focused first focusable element (X button in header) instead of first input
- **Fix:** Changed focus logic to prioritize input/select/textarea elements over buttons
- **Status:** FIXED
- **File:** `frontend/src/components/Modal.tsx`

### 5. My Schedule Redirects to Login - FIXED (Needs Browser Verification)
- **Location:** /my-schedule route
- **Symptom:** Navigating to My Schedule redirects to login even when authenticated
- **Root Causes Found:**
  1. **Missing `/auth/check` endpoint**: Frontend `checkAuth()` called `/auth/check` but backend only has `/auth/me`
  2. **Aggressive 401 redirect**: API interceptor redirected to `/login` on ANY 401, including `/auth/me` calls during auth check
- **Fixes Applied:**
  1. Changed `checkAuth()` in `frontend/src/lib/auth.ts` to use `/auth/me` instead of `/auth/check`
  2. Updated API interceptor in `frontend/src/lib/api.ts` to skip 401 redirect for `/auth/` endpoints
- **Verification Notes:**
  - Backend cookie auth verified working via curl (Set-Cookie header present, /auth/me returns user with cookie)
  - CORS configured correctly (allow_credentials=true, allow_origin=http://localhost:3000)
  - SSR shows "Checking authentication..." because auth runs client-side (expected for SSR)
- **Status:** FIXED - needs browser testing to confirm
- **Files Modified:**
  - `frontend/src/lib/auth.ts` - line 265-268
  - `frontend/src/lib/api.ts` - line 167-170
- **Priority:** HIGH - requires browser verification

### 6. Block View Date Selection - FIX NOT VERIFIED
- **Location:** Block/Schedule view
- **Symptom:** Block dates are settable/editable
- **Expected:** Should display hard limits based on block date (read-only)
- **Root Cause:** Date inputs in BlockNavigation.tsx allowed arbitrary date selection
- **Fix:** Replaced editable date inputs with read-only styled display. Navigation via Previous/Next Block and This Block buttons only.
- **Status:** FIX PREPARED, NOT VERIFIED IN BUILD
- **File:** `frontend/src/components/schedule/BlockNavigation.tsx`

---

## Working Features

- Compliance dashboard - functioning
- Help page - stable (never broken)
- Settings page - admin toggle works
- Login - working after fixes
- Schedule generation via API - working

---

## Backend Verification

All backend APIs verified working:
- `/api/v1/assignments` - returns 80 assignments for Block 7
- `/api/v1/schedule/generate` - generates schedules successfully
- `/api/v1/auth/login/json` - authentication working
- 730 blocks seeded for AY 2025-2026
- 30 rotation templates seeded
- 14 people seeded (5 faculty, 9 residents)

---

## Next Steps

### Completed (Code Fixes Applied, Need Browser Verification)
1. View Full Schedule link fix (`href="/schedule"`)
2. Add People modal focus fix (prioritize inputs over buttons)
3. BlockNavigation read-only dates (replaced inputs with display)
4. Auth flow fixes:
   - `checkAuth()` now uses `/auth/me` instead of non-existent `/auth/check`
   - 401 redirect skips `/auth/` endpoints to prevent redirect loop

### Remaining (Browser Testing Required)
1. **Verify auth flow** - login, check cookie in DevTools, navigate to protected pages
2. **Verify View Full Schedule link** - click from dashboard
3. **Verify Add People focus** - open modal, check cursor is in name input
4. **Verify block navigation** - dates should be read-only display
5. **Test Templates page** - should show templates after auth works
6. **Seed absence data** - for testing absences page

---

## Open Questions (Speed Check)

These are intentionally blunt because the repo moves fast:

1. Is the BlockNavigation "read-only dates" change actually in the running build, or just in notes?
   - **Answer:** Change IS in source code (`frontend/src/components/schedule/BlockNavigation.tsx`). Docker rebuild in progress. Not yet verified in running UI.

2. Are we treating "documented" investigations (e.g., My Schedule redirect) as completed, or still open until verified?
   - **Decision:** Keep open until verified.

3. Should "API verified working" for Templates be considered resolved, or keep it open until UI renders correctly?
   - **Answer:** Keep open until UI renders correctly. API working ≠ UI working (could be loading state, auth race, React Query issue).

---

## NEW ISSUE: Faculty-Inpatient Year View Shows Zeros

### Issue Discovered During Testing
- **Location:** /schedule with Faculty-Inpatient view
- **Symptom:** All faculty show 0 inpatient weeks, empty grid

### Root Cause Analysis (COMPLETED)
**NOT a frontend bug** - this is a data/seeding issue.

Database verification:
```
 total_assignments | with_template | without_template |   type
-------------------+---------------+------------------+----------
                40 |             0 |               40 | faculty
                40 |            40 |                0 | resident
```

- **Resident assignments** (40): ALL have `rotation_template_id` → `activity_type = 'inpatient'`
- **Faculty assignments** (40): NONE have `rotation_template_id` → `activity_type = NULL`

The frontend code correctly filters by `activity_type === 'inpatient'` (line 92-94 in FacultyInpatientWeeksView.tsx).
The issue is that the schedule generator/seeder creates faculty assignments without linking rotation templates.

### Frontend Code Reference
```typescript
// FacultyInpatientWeeksView.tsx:92-94
if (
  (am && am.activityType?.toLowerCase() === 'inpatient') ||
  (pm && pm.activityType?.toLowerCase() === 'inpatient')
) {
  count++
```

### Required Fix
**Backend/Seeder change needed:** When creating faculty assignments, ensure `rotation_template_id` is set to the appropriate inpatient template.

Location to investigate:
- `backend/app/scheduling/engine.py` - how faculty assignments are created
- Seed scripts that generate test data

### Status
- **Frontend:** Working correctly (no change needed)
- **Backend:** Needs investigation - faculty assignments missing rotation_template_id

---

*Document created during Session 14 user testing.*
