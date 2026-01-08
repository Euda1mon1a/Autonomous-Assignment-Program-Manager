# Session 075: Template Categories + Away-From-Program Tracking

**Branch:** `session/075-continued-work`
**Date:** 2026-01-08

---

## Current Task

Implementing template categories and away-from-program tracking for residents.

### Away-From-Program Rule
- **28 days/year max** before training extension required
- **21 days** = warning threshold
- Academic year: July 1 - June 30
- ALL absence types count (including conference)
- Faculty absences: `is_away_from_program = FALSE`
- Away rotations (Hilo, Okinawa, Kapiolani) are NOT absences

---

## Completed

### Backend (100%)
- `backend/app/models/rotation_template.py` - Added `template_category`
- `backend/app/models/absence.py` - Added `is_away_from_program`
- `backend/alembic/versions/20260108_add_tmpl_cat.py` - Migration
- `backend/alembic/versions/20260108_add_away_prog.py` - Migration
- `backend/app/schemas/rotation_template.py` - `TemplateCategory` enum
- `backend/app/schemas/absence.py` - `ThresholdStatus`, `AwayFromProgramSummary`
- `backend/app/services/absence_service.py` - Tracking logic
- `backend/app/controllers/absence_controller.py` - Controller methods
- `backend/app/api/routes/absences.py` - 3 new endpoints

### Frontend Types (100%)
- `frontend/src/types/admin-templates.ts` - `TemplateCategory`, configs
- `frontend/src/types/api.ts` - `is_away_from_program`, `AwayFromProgramSummary`

---

## In Progress

### A3: Admin Rotations Category Filter
**File:** `frontend/src/app/admin/rotations/page.tsx`
- Add `template_category` to filter state
- Add category dropdown after activity_type filter
- Filter templates by category

### B6: Absence Form Away Checkbox
**Files:**
- `frontend/src/components/AddAbsenceModal.tsx` - Add checkbox
- `frontend/src/components/AbsenceList.tsx` - Add column

### B8: Compliance Dashboard (REQUIRED)
**Files to create:**
- `frontend/src/app/admin/compliance/page.tsx`
- `frontend/src/hooks/useAwayComplianceDashboard.ts`
- `frontend/src/components/admin/AwayComplianceTable.tsx`
- `frontend/src/components/admin/AwayComplianceProgressBar.tsx`

---

## API Endpoints Available

```
GET /absences/compliance/away-from-program       # All residents dashboard
GET /absences/residents/{id}/away-from-program   # Individual summary
GET /absences/residents/{id}/away-from-program/check  # Threshold preview
```

---

## Key Files Modified

| File | Status |
|------|--------|
| `backend/app/models/rotation_template.py` | Done |
| `backend/app/models/absence.py` | Done |
| `backend/app/schemas/*.py` | Done |
| `backend/app/services/absence_service.py` | Done |
| `backend/app/api/routes/absences.py` | Done |
| `frontend/src/types/admin-templates.ts` | Done |
| `frontend/src/types/api.ts` | Done |
| `frontend/src/app/admin/rotations/page.tsx` | In Progress |
| `frontend/src/components/AddAbsenceModal.tsx` | Pending |
| `frontend/src/app/admin/compliance/page.tsx` | Pending |
