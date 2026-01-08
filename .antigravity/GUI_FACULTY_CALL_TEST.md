# Antigravity GUI Test: Faculty Call Alignment

**Purpose:** Validate faculty call functionality after type alignment
**Date:** 2026-01-07
**Branch:** `session/067-antigravity-faculty-call`
**Reference:** `.claude/Scratchpad/FACULTY_CALL_ALIGNMENT.md`

---

## Pre-Test Setup

Before testing, ensure data is seeded:

```bash
docker exec scheduler-local-backend python -m scripts.seed_antigravity --clear
```

Expected output includes:
- ~200 faculty call assignments (sunday/weekday/holiday/backup)
- PCAT and DO rotation templates

---

## Test Instructions

Navigate to `http://localhost:3000` and test the following areas.

---

## 1. Faculty Call Admin Page (HIGH PRIORITY)

**Navigate to:** `/admin/faculty-call`

**Verify:**
- [ ] Page loads without errors
- [ ] Call assignments table displays data
- [ ] Call type column shows: Sunday, Weekday, Holiday, Backup
- [ ] Call type badges have correct colors:
  - Sunday: Blue
  - Weekday: Green/Emerald
  - Holiday: Amber/Yellow
  - Backup: Purple
- [ ] Date filtering works
- [ ] Faculty filtering works
- [ ] Call type filtering works (dropdown should have 4 options)

**Data Check:**
```sql
-- Should return ~200 assignments
SELECT call_type, COUNT(*)
FROM call_assignments
GROUP BY call_type;
```

---

## 2. Call Assignment CRUD (HIGH PRIORITY)

**Test Create:**
- [ ] Click "Add Call Assignment" (or similar)
- [ ] Form shows call_type dropdown with 4 options
- [ ] Select a faculty member
- [ ] Select a date
- [ ] Select call type (try each: sunday, weekday, holiday, backup)
- [ ] Submit succeeds (no 422 errors)

**Test Edit:**
- [ ] Click edit on existing assignment
- [ ] Change call type
- [ ] Save succeeds

**Test Delete:**
- [ ] Select assignment(s)
- [ ] Delete operation works

---

## 3. Call Roster View (MEDIUM PRIORITY)

**Navigate to:** `/call-roster` (or wherever call roster lives)

**Verify:**
- [ ] Calendar/list view loads
- [ ] Faculty call assignments appear
- [ ] Color coding matches call types
- [ ] Clicking on assignment shows details

---

## 4. PCAT/DO Templates (MEDIUM PRIORITY)

**Navigate to:** `/admin/rotation-templates`

**Verify:**
- [ ] "Post-Call AM" (PCAT) template exists
  - Activity type: recovery
  - Abbreviation: PCAT
  - Color: Yellow
- [ ] "Day Off" (DO) template exists
  - Activity type: off
  - Abbreviation: DO
  - Color: Gray

---

## 5. Schedule Grid Integration (LOW PRIORITY)

**Navigate to:** `/schedule`

**Verify:**
- [ ] PCAT assignments (if any) display correctly
- [ ] DO assignments (if any) display correctly
- [ ] Tooltip shows correct rotation name

---

## 6. API Verification (LOW PRIORITY)

**Test with curl or browser:**

```bash
# List call assignments (requires auth)
curl -s http://localhost:8000/api/v1/call-assignments?limit=5

# Should return items with call_type in: sunday, weekday, holiday, backup
```

---

## Known Issues to Watch For

1. **422 Unprocessable Entity** - Would indicate call_type mismatch
2. **Empty call roster** - Check if seed ran successfully
3. **Missing PCAT/DO templates** - Need reseed
4. **"senior" call type** - Should NOT appear (was removed)

---

## Report Format

```markdown
## Faculty Call GUI Test Results - [Date]

### Environment
- Branch: session/067-antigravity-faculty-call
- Seed run: Yes/No
- Call assignments count: [number]

### Passed
- [x] Item that worked

### Failed
- [ ] Item that failed
  - **Error:** Description
  - **Screenshot:** [if applicable]

### Notes
- Observations or concerns
```

---

## Success Criteria

**Minimum for Pass:**
1. Faculty call admin page loads with data
2. All 4 call types display correctly (sunday/weekday/holiday/backup)
3. CRUD operations work without 422 errors
4. PCAT and DO templates visible

**Full Pass:**
- All items checked above
- No console errors
- No 422/500 API errors
