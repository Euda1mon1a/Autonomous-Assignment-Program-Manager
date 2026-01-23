# GUI Wiring Gaps Report

> **Date:** 2026-01-20
> **Purpose:** Document frontend GUI pages that exist but lack database wiring
> **Priority:** Critical for Block 10 operational use

---

## Executive Summary

Many admin GUI pages exist but cannot modify scheduling-critical data because:
1. Backend Pydantic schemas don't expose all DB model fields
2. Frontend types don't match backend schemas
3. API endpoints don't support the full range of updates needed

---

## Gap 1: Faculty Scheduling Constraints (CRITICAL)

### What Exists
- **DB Model:** `Person` has `min_clinic_halfdays_per_week`, `max_clinic_halfdays_per_week`, `admin_type`
- **GUI:** `/admin/people` page exists with PeopleTable, AddPersonModal

### What's Missing

| Layer | Gap |
|-------|-----|
| `backend/app/schemas/person.py` | Fields not in `PersonBase`, `PersonResponse`, `PersonUpdate` |
| `frontend/src/types/api.ts` | Fields not in `Person`, `PersonUpdate` interfaces |
| `frontend/src/components/admin/PeopleTable.tsx` | No columns for these fields |
| `frontend/src/components/AddPersonModal.tsx` | No form fields for these values |

### Impact
- Cannot change Montgomery from APD → PD via GUI
- Cannot adjust faculty clinic caps when duties change
- Must use raw SQL or migrations to update these values

### Fix Required
```
1. Backend: Add fields to PersonBase, PersonResponse, PersonUpdate schemas
2. Frontend: Regenerate types (npm run generate:types)
3. Frontend: Add form fields to AddPersonModal
4. Frontend: Add editable columns to PeopleTable
```

---

## Gap 2: Rotation Template Activity Requirements

### What Exists
- **DB Tables:** `rotation_templates`, `rotation_half_day_requirements`, `activity_requirements`
- **GUI:** `/admin/rotations` page with TemplateTable, WeeklyGridEditor, HalfDayRequirementsEditor

### What May Be Missing
- Verify: Can GUI create/edit activity requirements?
- Verify: Can GUI set which activities are "protected" (solver can't move)?
- Verify: Half-day requirement editor wired to actual DB?

### Hooks Used
- `useAdminTemplates` - likely wired
- `useWeeklyPattern` - verify DB writes
- `useHalfDayRequirements` - verify DB writes
- `useActivityRequirements` - verify DB writes

---

## Gap 3: Constraint Enable/Disable (FUTURE)

### Current State
- Constraints are hardcoded in `backend/app/scheduling/constraints/*.py`
- No database table for constraint configuration
- No GUI to enable/disable constraints

### Future Need
- `constraint_configs` table with: name, enabled, weight, parameters
- Admin GUI to toggle constraints on/off
- Per-schedule-run tracking of which constraints were active

---

## Gap 4: FMIT/Call Preload Management

### What Exists
- **DB Tables:** `inpatient_preloads`, `call_assignment`
- **GUI:** `/admin/fmit/import` page, `/admin/faculty-call` page

### Verify
- Can FMIT preloads be created/edited via GUI?
- Can faculty call assignments be created/edited?
- Is there bulk import from Excel?

---

## Gap 5: Half-Day Assignment Viewer/Editor

### What Exists
- **DB Table:** `half_day_assignments` (source='preload'|'manual'|'solver'|'template')
- **GUI:** `/admin/debugger` page shows assignments

### What May Be Missing
- Manual override editor (set source='manual' to lock a slot)
- Visual diff between schedule drafts
- Conflict highlighter when manual overrides break constraints

---

## Recommended Fix Priority

| Priority | Gap | Effort | Impact |
|----------|-----|--------|--------|
| P1 | Faculty constraints in Person schema | Small | High - blocks operational use |
| P2 | Verify rotation template wiring | Medium | Medium - may already work |
| P3 | FMIT/Call preload management | Medium | High - needed for Block 10 |
| P4 | Manual override editor | Large | Medium - workaround via SQL |
| P5 | Constraint config table | Large | Low - can hardcode for now |

---

## Verification Commands

```bash
# Check if backend schemas expose faculty fields
grep -n "min_clinic\|max_clinic\|admin_type" backend/app/schemas/*.py

# Check frontend types
grep -n "minClinic\|maxClinic\|adminType" frontend/src/types/*.ts

# Check API endpoints
grep -n "min_clinic\|max_clinic\|admin_type" backend/app/api/routes/people.py
```

---

## Action Plan for P1 (Faculty Constraints)

### Step 1: Backend Schema Update
File: `backend/app/schemas/person.py`

Add to `PersonBase`:
```python
min_clinic_halfdays_per_week: int | None = Field(None, ge=0, le=10)
max_clinic_halfdays_per_week: int | None = Field(None, ge=0, le=10)
admin_type: str | None = Field(None, pattern="^(GME|DFM|SM)$")
is_adjunct: bool | None = None
```

### Step 2: Regenerate Frontend Types
```bash
cd frontend && npm run generate:types
```

### Step 3: Update AddPersonModal
Add form fields for:
- `minClinicHalfdaysPerWeek` (number input, 0-10)
- `maxClinicHalfdaysPerWeek` (number input, 0-10)
- `adminType` (dropdown: GME, DFM, SM)
- `isAdjunct` (checkbox)

### Step 4: Update PeopleTable
Add columns (editable inline or via modal):
- Clinic Min/Max
- Admin Type
- Adjunct?

---

*This report identifies wiring gaps between existing GUI and database. Most GUI exists - it just needs the schema/API layer completed.*
