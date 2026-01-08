# Session 075 Continued: Activities Separation + Unified Rotation Editor

**Branch:** `session/075-continued-work`
**Date:** 2026-01-09
**STATUS:** ALL PHASES COMPLETE (1-8)

---

## Major Refactor: Separate Activities from Rotations

### Problem Solved
- `RotationTemplate` was storing both rotations (Neurology, FMIT) AND slot-level activities (Academic Sports Medicine Wed AM)
- Fixed-field requirements (fm_clinic_halfdays, specialty_halfdays) limited flexibility
- Two separate editors (grid + sliders) instead of unified UI

### Solution Architecture

**3 New Tables:**
1. `activities` - Slot-level events (FM Clinic, LEC, Specialty)
2. `rotation_activity_requirements` - Dynamic per-activity requirements with soft constraints
3. `weekly_patterns.activity_id` - FK to activities (replacing activity_type string)

---

## Backend Implementation Complete

### 1. Activity Model (`backend/app/models/activity.py`)
```python
Activity:
  id, name, code, display_abbreviation
  activity_category (clinical, educational, time_off, administrative)
  font_color, background_color
  requires_supervision, is_protected, counts_toward_clinical_hours
  display_order, is_archived
```

### 2. RotationActivityRequirement Model (`backend/app/models/rotation_activity_requirement.py`)
```python
RotationActivityRequirement:
  rotation_template_id, activity_id
  min_halfdays, max_halfdays, target_halfdays  # Soft constraints
  applicable_weeks (JSONB)  # [1,2,3] or null for all
  prefer_full_days, preferred_days, avoid_days  # Scheduling preferences
  priority (0-100)  # Higher = more important
```

### 3. WeeklyPattern Update (`backend/app/models/weekly_pattern.py`)
- Added `activity_id` FK (nullable for migration)
- Added `activity` relationship
- Kept `activity_type` for backward compatibility (deprecated)

### 4. Migrations Created
```
backend/alembic/versions/
├── 20260109_add_activities.py        # Create activities table + seed data
├── 20260109_weekly_pattern_fk.py     # Add activity_id to weekly_patterns
├── 20260109_activity_requirements.py # Create dynamic requirements table
```

**Seeded Activities:**
- FM Clinic (clinical), Specialty (clinical), Inpatient (clinical)
- Call (clinical), Procedure (clinical), Elective (clinical)
- Lecture/LEC (educational, protected), Conference (educational, protected)
- Day Off (time_off), Recovery (time_off)

### 5. Pydantic Schemas (`backend/app/schemas/activity.py`)
- ActivityBase, ActivityCreate, ActivityUpdate, ActivityResponse
- ActivityRequirementBase, ActivityRequirementCreate, ActivityRequirementResponse

### 6. ActivityService (`backend/app/services/activity_service.py`)
```python
# Activity CRUD
list_activities(category, include_archived)
get_activity_by_id(activity_id)
get_activity_by_code(code)
create_activity(data)
update_activity(activity_id, data)
archive_activity(activity_id)
delete_activity(activity_id)

# Requirements CRUD
list_requirements_for_template(template_id)
get_requirement_by_id(requirement_id)
create_requirement(template_id, data)
update_requirements_bulk(template_id, requirements)
delete_requirement(requirement_id)
```

### 7. API Endpoints

**/activities:**
```
GET  /activities                    # List with optional category filter
POST /activities                    # Create new activity
GET  /activities/{id}               # Get single activity
PUT  /activities/{id}               # Update activity
DELETE /activities/{id}             # Hard delete (fails if in use)
PUT  /activities/{id}/archive       # Soft delete
```

**/rotation-templates/{id}/activity-requirements:**
```
GET  /{id}/activity-requirements    # List all for rotation
PUT  /{id}/activity-requirements    # Replace all (atomic)
POST /{id}/activity-requirements    # Add single
DELETE /{id}/activity-requirements/{req_id}  # Delete single
```

---

## Frontend Implementation Complete

### Completed
1. `frontend/src/types/activity.ts` - TypeScript types for Activity, ActivityRequirement
2. `frontend/src/hooks/useActivities.ts` - CRUD hooks + activity requirements hooks
3. `frontend/src/components/RotationEditor.tsx` - Unified editor with week tabs, grid, requirements panel
4. `frontend/src/app/admin/rotations/page.tsx` - Filter rotations-only by default + unified editor modal
5. `frontend/src/components/admin/TemplateTable.tsx` - Added `onEditUnified` prop + Sliders icon button

### Unified Editor Layout
```
+-------------------------------------------------------------+
|  [Week 1] [Week 2] [Week 3] [Week 4] [All Weeks]            |
+------------------------------+------------------------------+
|  Weekly Pattern Grid (7x2)   |  Activity Requirements       |
|                              |                              |
|  Mon Tue Wed Thu Fri Sat Sun |  FM Clinic   [====--] 4/10   |
|  AM [C] [C] [L] [S] [S] [-] [-] |  Specialty   [=====-] 5/10   |
|  PM [S] [S] [-] [C] [C] [-] [-] |  Academics   [=-----] 1/10   |
|                              |  + Add Activity              |
|  Lock = Protected            |                              |
+------------------------------+------------------------------+
|  Total: 10/10 Balanced       [Cancel] [Save]                |
+-------------------------------------------------------------+
```

---

## Key Files Modified (This Session)

### Backend - NEW
- `backend/app/models/activity.py`
- `backend/app/models/rotation_activity_requirement.py`
- `backend/app/schemas/activity.py`
- `backend/app/services/activity_service.py`
- `backend/app/api/routes/activities.py`
- `backend/alembic/versions/20260109_add_activities.py`
- `backend/alembic/versions/20260109_weekly_pattern_fk.py`
- `backend/alembic/versions/20260109_activity_requirements.py`

### Backend - MODIFIED
- `backend/app/models/__init__.py` - Export Activity, ActivityCategory, RotationActivityRequirement
- `backend/app/models/weekly_pattern.py` - Added activity_id FK
- `backend/app/models/rotation_template.py` - Added activity_requirements relationship
- `backend/app/api/routes/__init__.py` - Register activities router
- `backend/app/api/routes/rotation_templates.py` - Added activity-requirements endpoints

---

## Plan File Location
`/Users/aaronmontgomery/.claude/plans/luminous-stargazing-wolf.md`

---

## Next Steps
1. Run migrations: `alembic upgrade head`
2. Test API endpoints via Swagger
3. ~~Implement frontend types/hooks~~ DONE
4. ~~Build unified RotationEditor component~~ DONE
5. Wire soft constraints into solver engine (IN PROGRESS - see Phase 8 below)
6. Test unified editor UI with real activities data
7. MCP RAG ingestion of domain document `docs/domain/RESIDENCY_SCHEDULING_MODEL.md`

---

## Phase 8: Solver Integration (COMPLETE)

**Goal:** Wire `RotationActivityRequirement` soft constraints into OR-Tools/PuLP solvers.

### Implementation Complete

**Files Created:**
- `backend/app/scheduling/constraints/activity_requirement.py` - ActivityRequirementConstraint class (~350 lines)
- `backend/tests/scheduling/test_activity_requirement_constraint.py` - 14 unit/integration tests

**Files Modified:**
- `backend/app/scheduling/constraints/base.py` - Added `activity_requirements`, `activity_req_by_template`, `activity_idx`, `activities` to SchedulingContext + helper methods
- `backend/app/scheduling/constraints/__init__.py` - Added export
- `backend/app/scheduling/constraints/manager.py` - Registered constraint in `create_default()` and `create_resilience_aware()`
- `backend/app/scheduling/engine.py` - Added `_load_activities()` and `_load_activity_requirements()` methods, integrated into `_build_context()`

### Key Features
- **Soft constraint** with configurable weight (default 50.0)
- **Target deviation penalty:** `weight * (priority/100) * |actual - target|`
- **Min/max violation penalty:** 10x multiplier for hard floor/ceiling
- **Auto-enable:** Constraint automatically enabled when activity requirements exist
- **Dual solver support:** Implements both `add_to_cpsat()` and `add_to_pulp()`
- **Rich validation:** Returns violations with activity names, template names, and details

### Test Results
All 14 tests passed:
- Initialization tests
- Target/min/max validation
- Priority weighting
- Multiple requirements
- Context integration
- Realistic rotation scenario

### Note
This same architecture supports faculty activity/call solving.
