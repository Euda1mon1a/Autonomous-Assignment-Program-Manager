# Test Implementation Checklist for GUI Bug Fixes

Use this checklist when writing tests for each bug fix. Copy the section for your bug.

---

## P0 Critical Bugs

### Bug #1: Block 0 Fudge Factor (Dates)
**Test File:** `frontend/__tests__/components/schedule/ScheduleCalendar.test.tsx`

```
Automated Tests:
[ ] Date boundary: Dec 31 renders as last day of block, Jan 1 as first day of next
[ ] Date picker returns YYYY-MM-DD format (never MM/DD/YYYY or locale-specific)
[ ] Fiscal year boundary doesn't shift dates (test Jan 1 and Dec 31 transitions)
[ ] localDate(2024, 1, 1) creates Jan 1, 2024 (not Dec 31, 2023)
[ ] Block navigation: prev/next don't lose day precision
[ ] Timezone-agnostic: test passes in UTC and other timezones

Manual Verification:
[ ] Open UI, navigate to Block 0
[ ] Verify dates in calendar match backend /blocks endpoint
[ ] Check fiscal year boundaries render correctly
```

---

### Bug #2: Conflicts API 404
**Test File:** `frontend/__tests__/features/conflicts/ConflictsList.test.tsx`

```
Automated Tests:
[ ] Mock API returns 200 with empty array -> shows "No conflicts" message
[ ] Mock API returns 200 with conflict data -> renders list
[ ] Mock API returns 404 -> Error boundary catches, no crash
[ ] Mock API returns 500 -> Shows error toast (not white screen)
[ ] Error handler extracts correct message from API response
[ ] Retry button works (triggers refetch)
[ ] Loading state shows skeleton before data loads

Manual Verification:
[ ] curl http://localhost:8000/api/v1/conflicts -> 200 OK (endpoint exists)
[ ] Navigate to /conflicts page -> no 404 error toast
[ ] Check console -> no unhandled promise rejections
```

---

### Bug #3: Swap Permissions
**Test File:** `frontend/__tests__/features/swap-marketplace/SwapRequestForm.test.tsx`

```
Automated Tests:
[ ] Resident user: swap button enabled for own assignment, disabled for others
[ ] Coordinator user: swap button always enabled
[ ] Admin user: swap button always enabled
[ ] Button text changes: "Disabled: No permission" tooltip on hover
[ ] Form submission: API called with user_id and assignment_id
[ ] API returns 403 -> error toast "You don't have permission"
[ ] API returns 200 -> success toast, form clears
[ ] Cross-resident swap rejected at API level (catch 403)

Manual Verification:
[ ] Login as Resident A
[ ] Own assignment: "Request Swap" button enabled
[ ] Other resident's assignment: button grayed out, tooltip shows
[ ] Click disabled button -> no action
[ ] Login as Coordinator
[ ] Both buttons enabled (can request swaps for anyone)
```

---

## P1 Feature-Critical Bugs

### Bug #4: Month/Week Views Empty
**Test File:** `frontend/__tests__/components/schedule/MonthView.test.tsx`

```
Automated Tests:
[ ] useScheduleView() returns 'month' -> MonthView renders
[ ] useScheduleView() returns 'week' -> WeekView renders
[ ] Mock empty assignments -> shows grid with no data highlights
[ ] Mock populated assignments -> shows color-coded cells
[ ] Previous/Next buttons update currentDate state
[ ] Calendar grid has 7 columns (Sun-Sat)
[ ] No loading skeleton after data loads (skeleton removed)

Manual Verification:
[ ] Navigate /schedule page
[ ] Click "Month" button -> month view renders
[ ] Click "Week" button -> week view renders
[ ] Click prev/next -> calendar updates
[ ] No blank white space where data should be
```

---

### Bug #5: Call Roster Empty
**Test File:** `frontend/__tests__/features/call-roster/CallRoster.test.tsx`

```
Automated Tests:
[ ] useAssignments() called with filter role='on_call'
[ ] Empty assignments -> renders "No on-call assignments"
[ ] Populated assignments -> renders CallCard for each
[ ] Each CallCard displays: name, phone, email, shift badge
[ ] Shift badges: Night, Day, Weekend colored appropriately
[ ] Contact info section expandable/collapsible
[ ] Sort by shift/name works (if implemented)

Manual Verification:
[ ] Navigate /call-roster
[ ] Verify list appears or "No data" message
[ ] Click contact card -> contact info expands
[ ] Phone/email numbers visible and clickable (tel:/mailto: links)
```

---

### Bug #6: Import Table Missing
**Test File:** `frontend/__tests__/features/import-export/ImportPreview.test.tsx`

```
Automated Tests:
[ ] CSV mock data renders as <table> (not <pre> or plain text)
[ ] <thead> has correct column headers (PersonID, Name, Activity, etc.)
[ ] <tbody> has correct number of rows matching mock data
[ ] Rows render with correct data in cells
[ ] No console errors during render
[ ] Table is scrollable (if >10 rows)

Manual Verification:
[ ] Navigate /import-export
[ ] Upload test CSV (sample: backend/tests/fixtures/import.csv)
[ ] Verify preview renders as table
[ ] Verify column count matches CSV
[ ] Verify row count matches CSV
```

---

### Bug #7: CSV Export Fails
**Test File:** `frontend/__tests__/components/ExcelExportButton.test.tsx`

```
Automated Tests:
[ ] Mock fetch response: blob with CSV content-type
[ ] Click export button -> fetch called to /api/v1/export
[ ] Response handling: creates Blob from response
[ ] Filename: matches pattern "schedule_YYYY-MM-DD.csv"
[ ] Download triggered: URL.createObjectURL called
[ ] Link removed after download (no DOM pollution)
[ ] Error handling: 500 response -> error toast

Manual Verification:
[ ] Click "Export CSV" button
[ ] Verify file downloads to downloads folder
[ ] Verify filename has correct date
[ ] Open file in text editor -> valid CSV format
[ ] Parse CSV -> row count matches schedule
```

---

## P2 Polish Bugs

### Bug #8: Sticky Header
**NOTE:** CSS-only, requires visual regression testing

```
Manual Verification (No Automated Test):
[ ] Load large schedule (>20 people)
[ ] Scroll down vertically -> date header stays at top
[ ] Header background is opaque (not see-through)
[ ] No overlap between header and data rows
[ ] Z-index correct: header above data, below modals
[ ] Horizontal scroll: header stays in place
[ ] Responsive: works on mobile (header height adjusts)

Visual Regression Testing (CI):
[ ] Add to Playwright visual regression suite
[ ] Capture screenshot: scrolled schedule with sticky header visible
[ ] Compare against baseline in main branch
```

---

### Bug #9: Nav Dropdowns (Mobile Menu)
**Test File:** `frontend/__tests__/components/MobileNav.test.tsx`

```
Automated Tests (Mobile Viewport):
[ ] Render with viewport: { width: 375, height: 667 } (iPhone)
[ ] Menu icon visible (hamburger ≡)
[ ] Dropdown hidden by default (hidden class or display:none)
[ ] Click menu icon -> dropdown opens (opacity: 1, visible)
[ ] Click outside dropdown -> dropdown closes
[ ] Chevron icon rotates 180° when open
[ ] Links in dropdown: onClick handlers fire navigation
[ ] Keyboard: Esc closes dropdown (a11y)

Manual Verification:
[ ] View on iPhone/Android or Chrome DevTools mobile mode
[ ] Tap menu icon -> dropdown slides in
[ ] Verify all links visible in dropdown
[ ] Tap a link -> navigates to page
[ ] Tap background -> dropdown closes
```

---

### Bug #10: Manifest Redesign
**Test File:** `frontend/__tests__/features/daily-manifest/DailyManifest.test.tsx`

```
Automated Tests:
[ ] Component renders without error
[ ] Staffing summary visible (data-testid="staffing-summary")
[ ] Role counts displayed (Faculty: X, Residents: Y, etc.)
[ ] Activity breakdown visible (if in spec)
[ ] Responsive grid: 1 column on mobile, 2+ on desktop
[ ] No layout shift (CLS metric: component stable after render)
[ ] Data updates when schedule changes

Manual Verification:
[ ] Design review: compare to design mockup
[ ] Desktop layout: clean, organized, readable
[ ] Mobile layout: stacked vertically, no overflow
[ ] Colors: staffing levels color-coded (green=full, red=understaffed)
[ ] Product owner sign-off: "Approved" comment in PR
```

---

### Bug #11: People Card Clickable
**Test File:** `frontend/__tests__/components/schedule/PersonalScheduleCard.test.tsx`

```
Automated Tests:
[ ] Card renders with person data (name, pgy_level)
[ ] Card has cursor: pointer on hover (CSS class)
[ ] onClick handler called when card clicked
[ ] Navigation target: /people/{personId}
[ ] Correct person ID passed to navigate
[ ] Link works with keyboard: Enter key triggers navigation

Manual Verification:
[ ] Navigate /people page
[ ] Hover over card -> cursor changes to pointer
[ ] Click card -> navigates to /people/{id}
[ ] URL updates correctly
[ ] Person detail page loads for correct person
```

---

### Bug #12: PGY Filter
**Test File:** `frontend/__tests__/components/schedule/ViewToggle.test.tsx`

```
Automated Tests:
[ ] Filter dropdown renders with options: PGY 1, 2, 3, All
[ ] Selecting "PGY 1" -> filters residents with pgy_level=1
[ ] Other PGY residents hidden
[ ] Selecting "All" -> shows all residents again
[ ] Filter state saved to URL: ?pgy=1
[ ] Refresh page -> filter persists (from URL param)
[ ] Filter state saved to localStorage (if offline support)
[ ] UI visual indicator shows active filter (checkmark or highlight)

Manual Verification:
[ ] Open /schedule page
[ ] Click filter dropdown
[ ] Select "PGY 2" -> roster updates, shows only PGY 2
[ ] Select "All" -> all PGY levels visible again
[ ] Refresh page -> PGY 2 filter still active (if saved)
```

---

## Universal Test Checklist (All Tests)

Before submitting any test file:

```
Code Quality:
[ ] Follows React Testing Library best practices
[ ] Uses screen.getByTestId() over document.querySelector
[ ] Async tests use waitFor() or findBy*
[ ] Mocks are at module level (jest.mock at top)
[ ] No hardcoded IDs; use data-testid attributes

Coverage:
[ ] >80% line coverage for components under test
[ ] Happy path tested (main flow)
[ ] Error path tested (API errors, edge cases)
[ ] Empty state tested (no data)
[ ] Loading state tested (before data loads)

Maintainability:
[ ] Test names describe what is being tested (not "should work")
[ ] Setup data (mocks) clearly separated from tests
[ ] Avoid test interdependencies (each test standalone)
[ ] Use helpers: mockPeople(), mockAssignments() for reuse

Performance:
[ ] No hardcoded delays (use waitFor instead of setTimeout)
[ ] Tests run <1 second each (no slow tests)
[ ] Batch similar tests in describe blocks
```

---

## Running Tests During Development

```bash
# Run all tests
npm test

# Run tests matching pattern
npm test -- CallRoster

# Run with coverage
npm test -- --coverage

# Watch mode (re-run on file changes)
npm test -- --watch

# Verbose output
npm test -- --verbose
```

---

## If Test Fails

```
Step 1: Read error message carefully
Step 2: Check mock data matches component expectations
Step 3: Verify DOM selectors (data-testid values)
Step 4: Check async handling (use waitFor for async state)
Step 5: Console.log mock calls to debug: console.log(useAssignments.mock.calls)
Step 6: Run single test in isolation: npm test -- CallRoster.test.tsx --testNamePattern="should render"
Step 7: Ask for help if stuck >15 mins
```
