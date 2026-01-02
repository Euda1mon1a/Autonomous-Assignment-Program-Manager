# Antigravity GUI Test Prompt

**Purpose:** Pre-deployment validation of critical GUI functionality
**Date:** 2026-01-01
**Context:** Session 047 completed stack health fixes, preparing for stealth deploy

---

## Test Instructions

Navigate to `http://localhost:3000` and systematically test the following areas. Report any issues found.

---

## 1. Schedule Grid (HIGH PRIORITY)

**Navigate to:** `/schedule`

**Verify:**
- [ ] Block 10 displays (Mar 12 - Apr 8, 2026)
- [ ] All 28 days visible in grid
- [ ] Color coding shows correctly (background colors from rotation templates)
- [ ] Tooltips appear on hover showing full rotation name
- [ ] Resident names display in rows
- [ ] Scrolling works (if many residents)
- [ ] Block navigation arrows work (previous/next block)

**Known good state:** 992 assignments for Block 10

---

## 2. Excel Export (HIGH PRIORITY)

**Navigate to:** `/import-export` → Export tab

**Test:**
- [ ] Click export button
- [ ] Select date range (Block 10: Mar 12 - Apr 8, 2026)
- [ ] Choose Excel format
- [ ] Download completes successfully
- [ ] Open downloaded file - verify data looks correct

**Alternative:** Check if there's an export button directly on `/schedule` page

---

## 3. Excel Import (HIGH PRIORITY)

**Navigate to:** `/import-export` → Import tab

**Test with file:** `backend/examples/sample-data/sanitized block 8 and 9 faculty.xlsx`

- [ ] Click "Start Import" button
- [ ] Upload the Excel file
- [ ] Preview displays parsed data correctly
- [ ] Column mapping appears reasonable
- [ ] (Don't execute import - just verify preview works)

---

## 4. Rotation Templates (MEDIUM PRIORITY)

**Navigate to:** `/admin/rotation-templates` (or similar admin path)

**Verify:**
- [ ] Template list displays
- [ ] Colors show in template cards/rows
- [ ] Click "Edit" on a template
- [ ] Color picker appears with live preview
- [ ] Cancel without saving (don't modify data)

---

## 5. Authentication (MEDIUM PRIORITY)

**Test:**
- [ ] Logout works
- [ ] Login page displays
- [ ] Login with valid credentials works
- [ ] Protected routes redirect to login when not authenticated

---

## 6. Dashboard/Home (LOW PRIORITY)

**Navigate to:** `/` or `/dashboard`

**Verify:**
- [ ] Page loads without errors
- [ ] Key metrics display (if any)
- [ ] Navigation menu works

---

## 7. API Health Check (LOW PRIORITY)

**Navigate to:** `http://localhost:8000/health`

**Verify:**
- [ ] Returns healthy status
- [ ] All services show green/healthy

---

## Report Format

Please report findings as:

```
## GUI Test Results - [Date]

### Passed
- [x] Item that worked

### Failed
- [ ] Item that failed
  - **Error:** Description of what went wrong
  - **Screenshot:** [if applicable]

### Notes
- Any observations or concerns
```

---

## Priority if Short on Time

1. Schedule Grid displays Block 10 correctly
2. Excel Export downloads successfully
3. Excel Import preview works
4. Color coding visible

These are the "stealth deploy" must-haves.
