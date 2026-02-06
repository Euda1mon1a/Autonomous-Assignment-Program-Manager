# Quality Gate Specification for 16 GUI Bug Fixes

**Purpose:** Define acceptance criteria and verification strategy for GUI bug fixes.
**Audience:** QA, developers, plan-party probes
**Automation Level:** Mixed (automated + manual verification)

---

## Bug Categorization & Verification Strategy

### P0 Bugs (Critical Path - All Auto + Manual)

#### 1. Block 0 Fudge Factor (Date Handling)
**Component:** `ScheduleCalendar.tsx`, Block view navigation
**Acceptance Criteria:**
- Block 0 dates render correctly (no off-by-one errors)
- Date picker returns canonical dates (YYYY-MM-DD format)
- Boundary dates (start/end of fiscal year) render without shifting
- Timezone-agnostic (tests use `localDate()` helper)

**Verification:**
- **Automated:** Jest test with date boundary cases (Dec 31 → Jan 1 transition)
- **Manual:** Navigate to Block 0 in UI, verify calendar dates align with backend `/blocks` endpoint
- **Test File:** `frontend/__tests__/components/schedule/ScheduleCalendar.test.tsx` (new)

---

#### 2. Conflicts API 404 Errors
**Component:** Conflicts page + API client
**Acceptance Criteria:**
- `/api/v1/conflicts` endpoint returns 200 (not 404)
- Conflict list populates or shows empty state (not error toast)
- Empty conflict list renders "No conflicts" message
- Error handling gracefully captures backend 404s without crashes

**Verification:**
- **Automated:** Mock API calls with 200/404 responses; verify error boundary doesn't crash
- **Manual:** Login → navigate to conflicts page → verify no 404 error toast
- **Special Test:** Verify endpoint exists: `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/conflicts`
- **Test File:** `frontend/__tests__/features/conflicts/ConflictsList.test.tsx` (enhance)

---

#### 3. Swap Permissions (Authorization)
**Component:** Swap request form + approval panel
**Acceptance Criteria:**
- Residents can create swaps for their own assignments
- Residents cannot create swaps for others' assignments
- Coordinators can approve/reject all swaps
- UI disables swap button if user lacks permission (grayed out, tooltip)
- API rejects unauthorized swap requests with 403 (caught client-side)

**Verification:**
- **Automated:** Mock user roles (resident, coordinator, admin); test button state changes
- **Manual:** Login as resident → attempt own swap (works), others' swap (disabled)
- **Edge Case:** Test cross-resident swap attempts (should fail with permission error)
- **Test File:** `frontend/__tests__/features/swap-marketplace/SwapRequestForm.test.tsx` (enhance)

---

### P1 Bugs (Feature Completeness - Auto + Manual)

#### 4. Month/Week Views Empty
**Component:** `MonthView.tsx`, `WeekView.tsx`
**Acceptance Criteria:**
- Views render calendar grid (not blank page)
- Assignments populate or show empty state
- Pagination/navigation works (prev/next buttons update view)
- No loading skeleton flickers after data loads

**Verification:**
- **Automated:** Mock `useScheduleView()` hook; verify grid renders with mock data
- **Manual:** Navigate schedule page → toggle Month → Week views → verify content appears
- **Test File:** `frontend/__tests__/components/schedule/MonthView.test.tsx` (new)

---

#### 5. Call Roster Empty
**Component:** `CallRoster.tsx`, `CallCard.tsx`
**Acceptance Criteria:**
- Call roster fetches assignments with `role: 'on_call'` filter
- Contact info displays (name, phone, email)
- No data → shows "No call assignments" message
- Shift badges render (Night, Day, etc.)

**Verification:**
- **Automated:** Mock `useAssignments()` to return empty array; verify empty state message
- **Manual:** Navigate to call-roster page → verify list appears or empty message shows
- **Test File:** `frontend/__tests__/features/call-roster/CallRoster.test.tsx` (exists, verify comprehensiveness)

---

#### 6. Import Table Missing
**Component:** `ImportPreview.tsx`
**Acceptance Criteria:**
- CSV preview renders as table (not raw text)
- Headers map to columns (PersonID, Name, Activity, etc.)
- Row count matches uploaded file
- No JavaScript errors in console

**Verification:**
- **Automated:** Render `<ImportPreview data={mockCSV} />` with known CSV; verify table DOM
- **Manual:** Upload test CSV → verify preview renders as table with correct columns
- **Test File:** `frontend/__tests__/features/import-export/ImportPreview.test.tsx` (new)

---

#### 7. CSV Export Fails
**Component:** `ExcelExportButton.tsx`, export service
**Acceptance Criteria:**
- Export button generates valid CSV file
- Downloaded file has `.csv` extension
- File contains header row + data rows
- No 500 errors from API export endpoint

**Verification:**
- **Automated:** Mock fetch response with CSV blob; verify filename and content type
- **Manual:** Click "Export CSV" button → verify file downloads with correct name
- **Special Test:** Parse downloaded CSV and validate row count matches
- **Test File:** `frontend/__tests__/components/ExcelExportButton.test.tsx` (enhance)

---

### P2 Bugs (Polish - Auto + Manual)

#### 8. Sticky Header
**Component:** `ScheduleCalendar.tsx` (CSS: `sticky top-0 z-10`)
**Acceptance Criteria:**
- Date header stays visible when scrolling down
- Header background opaque (not transparent)
- No overlap with data rows
- Z-index correct (not covered by modals)

**Verification:**
- **Manual:** Scroll large schedule grid horizontally/vertically → header stays fixed
- **No Auto Test:** Sticky positioning is CSS-based; visual regression tests required (Playwright/Chromatic)
- **Note:** Flag for visual regression testing in CI

---

#### 9. Nav Dropdowns (Mobile Menu)
**Component:** `MobileNav.tsx`, responsive menu
**Acceptance Criteria:**
- Dropdown opens on click (not hover, mobile-safe)
- Closes when clicking outside
- Chevron icon rotates (visual feedback)
- Links in dropdown are clickable

**Verification:**
- **Automated:** Mock mobile viewport; test click handlers and aria states
- **Manual:** View on mobile device → tap menu icon → verify dropdown opens/closes
- **Test File:** `frontend/__tests__/components/MobileNav.test.tsx` (new)

---

#### 10. Manifest Redesign (Daily Manifest)
**Component:** `DailyManifest.tsx`
**Acceptance Criteria:**
- New layout renders (flexbox/grid structure)
- Staffing summary visible (counts by role)
- No layout shifts (CLS < 0.1)
- Responsive on mobile

**Verification:**
- **Automated:** Render component; verify key elements present (via data-testid)
- **Manual:** View on desktop and mobile → verify layout looks polished
- **Note:** Visual design acceptance by product owner required

---

#### 11. People Card Clickable
**Component:** Person card in People list
**Acceptance Criteria:**
- Card has cursor pointer on hover
- Click navigates to person detail page
- Link target is correct (`/people/{personId}`)

**Verification:**
- **Automated:** Render card; verify onClick handler calls navigate with correct ID
- **Manual:** Click person card → verify navigation works
- **Test File:** `frontend/__tests__/components/schedule/PersonalScheduleCard.test.tsx` (new)

---

#### 12. PGY Filter
**Component:** Schedule page filter dropdown
**Acceptance Criteria:**
- Filter dropdown renders with options (PGY 1, 2, 3, All)
- Selecting PGY filters visible residents
- Filter state persists in URL query param or localStorage
- Unselecting shows all residents again

**Verification:**
- **Automated:** Mock `usePeople()` with mixed PGY levels; test filter state changes
- **Manual:** Select PGY filter → verify roster updates
- **Test File:** `frontend/__tests__/components/schedule/ViewToggle.test.tsx` (enhance)

---

## Verification Checklist Template

For each bug fix, verify:

```
[ ] Code change reviewed (architecture matches patterns)
[ ] Tests added/updated (>80% coverage of changes)
[ ] All tests pass locally (npm test --watch)
[ ] No console errors/warnings in browser
[ ] Acceptance criteria met (manual verification)
[ ] No regressions in related features
[ ] PR description documents changes
[ ] CHANGELOG updated
```

---

## Testing Tools & Patterns

**Framework:** Jest + React Testing Library
**Mocking:** `jest.mock('@/lib/hooks')` for API/data hooks
**Helpers:** `render()`, `screen.getByTestId()`, `fireEvent.click()`
**Async:** `waitFor()` for async state updates
**Date Testing:** Use `localDate(year, month, day)` helper to avoid timezone issues

---

## Hard-to-Verify Fixes

**Flag these for special attention:**

1. **Sticky Header (#8)** - CSS-only, needs visual regression testing (Playwright/Chromatic)
2. **Nav Dropdowns (#9)** - Mobile interaction testing requires device or responsive testing framework
3. **Manifest Redesign (#10)** - Visual design acceptance required (not automated)

---

## Batch Verification Order

**Batch 1 (Critical):** Blocks 0, Conflicts API, Swap permissions → Smoke tests required
**Batch 2 (Data):** Month/Week/Call roster, Import, CSV export → Integration tests required
**Batch 3 (Polish):** Sticky, Nav, Manifest, Clickable, PGY filter → Manual UX verification

**Total Automated Tests:** ~10 new test files
**Estimated Manual Time:** 2-3 hours (full UAT)
**CI Gate:** All tests pass + no visual regressions
