# Session 075 Continued: Activities Separation + Faculty Weekly Editor

**Branch:** `session/075-continued-work`
**Date:** 2026-01-09
**STATUS:** Phases 1-11 COMPLETE, Phase 12 (Faculty Weekly Editor) IN PROGRESS

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

---

## Phase 9: Domain Knowledge RAG Ingest + Audit (COMPLETE)

**Date:** 2026-01-08 (continued session)

### Domain Understanding Ingested

1. **Core Hierarchy:** Block → Rotation Template → BlockAssignment → Assignment
2. **Assignment vs Activity:** Complementary layers (schedule output vs vocabulary catalog)
3. **Inpatient vs Outpatient:** 12/14 vs 10/14 half-days, weekend work, call/leave eligibility
4. **Resident vs Faculty Call:** Residents rotate through inpatient; faculty take overnight Sun-Thu

### RAG Audit - Issues Found & Corrected

| Issue | Problem | Correction |
|-------|---------|------------|
| **Wednesday constraint** | Only mentioned PM weeks 1-3 | W1-3: PM Lecture (HARD). W4: AM Lecture + PM Advising (HARD) |
| **Conference tracking** | Template table said "No" | Conferences COUNT toward 28-day for residents |
| **Deployment** | Military docs implied residents could deploy | Residents CANNOT deploy (faculty only) |
| **"Near-hard" language** | Priority 91-100 called "near-hard" | Protected slots are HARD constraints |
| **Week 4 "exception"** | Framed as soft/flexible | Week 4 is a different HARD pattern |

### Key Business Rules Clarified

**Away From Program vs Annual Leave:**
| Type | Away (28-day) | Annual Leave |
|------|---------------|--------------|
| Vacation | YES | YES |
| Conference | YES | NO |
| Medical/Sick | YES | NO |
| Day Off (rotation) | NO | N/A |

**Core Rule:** If not in rotation template → days away from program.

### Documents Ingested to RAG
1. Domain understanding (9 chunks) - `scheduling_policy`
2. Domain model doc (2 chunks) - `scheduling_policy`
3. Critical corrections v1 (1 chunk) - `scheduling_policy`
4. Authoritative corrections v2 (2 chunks) - `scheduling_policy`

**Total:** 14 new chunks (263 → 277 documents)

### File Updated
- `docs/domain/RESIDENCY_SCHEDULING_MODEL.md` - Fixed Template Categories table, Wednesday constraints, priority levels, deployment clarification

---

## Phase 10: Canonical Domain Document + TDY Corrections (COMPLETE)

**Date:** 2026-01-09 (continued session)

### Canonical Document Created

**File:** `docs/domain/DOMAIN_KNOWLEDGE.md` (~435 lines)

**Purpose:** Single source of truth for scheduling domain, usable by humans and LLMs without RAG.

**Key Sections:**
1. Terminology Glossary (Block, Rotation, Activity, Assignment, Slot, AT, PCAT, DO)
2. Academic Year Structure (14 blocks: 0-13, Thu-Wed cycle, Block 0 fudge factor)
3. Rotations & Templates (inpatient vs outpatient, weekly patterns)
4. Activities & Assignments (vocabulary vs scheduled, four-layer stack)
5. Supervision Requirements (AT calculation: PGY-1=0.5, PGY-2/3=0.25, +1 for procedures)
6. Call Models (resident call vs faculty call, PCAT/DO rules)
7. Protected Time (Wednesday constraints HARD)
8. Time Away Rules (28-day limit, TDY vs Deployment)
9. ACGME Compliance (80-hour, 1-in-7, tiers)
10. Constraint Hierarchy (Tier 0-3)

### TDY vs Deployment Correction (CRITICAL)

**Previous Error:** Docs said "Residents cannot deploy" and implied TDY was faculty-only.

**Correct Understanding:**
| Duty Type | Residents | Faculty |
|-----------|-----------|---------|
| **TDY** | YES | YES |
| **Deployment** | NO | YES |

**TDY and Away-From-Program:**
| TDY Type | Counts Toward 28-Day? |
|----------|----------------------|
| Away rotation (Hilo etc.) | NO (still training) |
| Conference | YES |
| Non-training military duty | YES |

**Key Insight:** TDY orders depend on location/distance. Away rotations that require TDY orders still count as training, NOT away-from-program.

### 730 Blocks Terminology Fixed

**Problem:** `user-guide-faq.md` and some RAG chunks used "730 blocks/year" (AM/PM as blocks).

**Correction:** Block = 28-day period. AM/PM periods are "slots". 14 blocks/year, 56 slots/block.

### Files Modified
1. `docs/domain/DOMAIN_KNOWLEDGE.md` - Created canonical document
2. `docs/domain/RESIDENCY_SCHEDULING_MODEL.md` - Added pointer to canonical
3. `docs/rag-knowledge/scheduling-policies.md` - Fixed block definition
4. `docs/rag-knowledge/user-guide-faq.md` - Fixed block definition
5. `docs/rag-knowledge/military-specific.md` - Added TDY clarification

### RAG Updates
- Canonical doc ingested (8 chunks)
- TDY correction ingested (1 chunk)
- user-guide-faq.md refresh triggered (Celery task)
- Total: 277 → 286 documents

### Terminology Standardized
| Term | Meaning |
|------|---------|
| Block | 28-day scheduling period (14/year) |
| Slot | Half-day period (AM/PM) |
| Activity | Vocabulary/catalog item |
| Assignment | Actualized scheduled slot |
| TDY | Temporary Duty (both can do) |
| Deployment | Combat/operational (faculty only) |
| AT | Attending Time (supervision unit) |
| PCAT | Post Call Attending Time |
| DO | Direct Observation |

---

## Phase 11: RAG Cleanup (COMPLETE)

**Date:** 2026-01-09

Cleaned up RAG "slop" - reduced from 256 chunks to ~28 clean chunks.

---

## Phase 12: Faculty Weekly Activity Editor (IN PROGRESS)

**Date:** 2026-01-09
**Plan:** `/Users/aaronmontgomery/.claude/plans/dreamy-growing-crayon.md`

### Purpose
Build UI for managing faculty weekly activity templates and week-specific overrides. Faculty are available when NOT absent AND NOT on FMIT. This is where administrative scheduling happens (APD doing 2 half-days clinic, OIC blocking Monday admin, etc.).

### Key Activities (CRITICAL CORRECTIONS)
| Activity | Code | Category | Notes |
|----------|------|----------|-------|
| **AT** | `at` | clinical | **SUPERVISION** - counts toward ratios |
| **FM Clinic** | `fm_clinic` | clinical | Family Medicine clinic |
| **SM Clinic** | `sm_clinic` | clinical | Sports Medicine clinic |
| **GME** | `gme` | administrative | Graduate Medical Education |
| **DFM** | `dfm` | administrative | Dept Family Medicine admin |
| **PCAT** | `pcat` | clinical | **SUPERVISION** - Post Call Attending Time |
| **DO** | `do` | clinical | **SUPERVISION** - Direct Observation |

**CRITICAL:** AT, PCAT, DO are all **supervision activities** (`provides_supervision = true`) that count toward supervision ratios. NOT time_off or administrative.

### Role → Activity Permissions
| Role | Activities | Default |
|------|------------|---------|
| PD | GME, AT, PCAT, DO | GME |
| APD | GME, AT, PCAT, DO, FM Clinic | GME |
| OIC | DFM, GME, AT, PCAT, DO, FM Clinic | DFM |
| Dept Chief | DFM, AT, PCAT, DO, FM Clinic | DFM |
| Sports Med | SM Clinic, AT, PCAT, DO | SM Clinic |
| Core | AT, PCAT, DO, FM Clinic, GME | (none) |
| Adjunct | AT, PCAT, DO | (none) |

### Database Tables
1. `faculty_weekly_templates` - Default 7×2 patterns per faculty
2. `faculty_weekly_overrides` - Week-specific exceptions
3. `faculty_activity_permissions` - Role → Activity mapping

### Files Created
**Backend:**
- `backend/alembic/versions/20260109_faculty_weekly.py` - Migration + seed data
- `backend/app/models/faculty_weekly_template.py`
- `backend/app/models/faculty_weekly_override.py`
- `backend/app/schemas/faculty_activity.py`
- `backend/app/services/faculty_activity_service.py`
- `backend/app/api/routes/faculty_activities.py`
- `backend/app/scheduling/constraints/faculty_weekly_template.py`

**Frontend:**
- `frontend/src/types/faculty-activity.ts`
- `frontend/src/hooks/useFacultyActivities.ts`
- `frontend/src/components/FacultyWeeklyEditor.tsx`
- `frontend/src/components/FacultyMatrixView.tsx`
- `frontend/src/app/admin/faculty-activities/page.tsx`

### Commits
1. `9ee9f8ae` - feat: Add faculty weekly activity editor (full stack)
2. `xxxxxxxx` - feat: Add Faculty Templates to navigation
3. `44c7741d` - feat: Add inline faculty role editing in matrix view
4. `c011fc7b` - fix: Remove broken join() code in get_permitted_activities

### Bug Fixed (CRITICAL)
**File:** `backend/app/services/faculty_activity_service.py`
**Issue:** Lines 531-536 had broken `.join()` code that crashed before working SQL could run
**Error:** `TypeError: Select.join() missing 1 required positional argument: 'target'`
**Fix:** Removed dead code, now activities load correctly

### Current Status
- ✅ Database: All tables created, permissions seeded
- ✅ Backend API: All endpoints working (fixed created_at/updated_at missing in queries)
- ✅ Frontend: Editor, matrix view, admin page complete
- ✅ Navigation: "Faculty Templates" in admin menu
- ✅ Inline role editing: Works from matrix view
- ✅ Activity palette: Working, shows activities by role
- ✅ Faculty roles: All 12 faculty now have roles set in DB
- ✅ **3 BUGS FIXED** (commit a95d4d9c) - abbreviations, roles display, save handler

### Bugs Fixed

**Bug 1: Activity Abbreviations Wrong** ✅ FIXED (a95d4d9c)
- **Root Cause:** API returns `display_abbreviation` (snake_case), frontend expected `displayAbbreviation` (camelCase)
- **Fix:** `FacultyWeeklyEditor.tsx:155` - Added fallback for snake_case

**Bug 2: Faculty Roles Not Displayed** ✅ FIXED (a95d4d9c)
- **Root Cause:** API returns `faculty_role`, frontend expected `facultyRole`
- **Fix:** `FacultyMatrixView.tsx` - Added snake_case fallback

**Bug 3: Save Handler Missing try/catch** ✅ FIXED (a95d4d9c)
- **Fix:** Added try/catch and `onClose?.()` call

**Bug 4: personId undefined - saves to /faculty/undefined/** ✅ FIXED (47adb15b)
- **Root Cause:** API returns `person_id`, frontend expected `personId`
- **Fix:** Added `getPersonId()` helper in FacultyMatrixView.tsx
- **Result:** Role updates NOW WORK (verified Montgomery, LaBounty)

**Bug 5: Activity Override Save - UNIQUE CONSTRAINT ERROR** 🔴 CURRENT BUG
- **Error:** `duplicate key value violates unique constraint "uq_faculty_weekly_override_slot"`
- **Root Cause:** Backend tries INSERT when should UPSERT (slot already exists)
- **File:** `backend/app/services/faculty_activity_service.py` - `create_override()` method
- **Fix Needed:** Use UPSERT (INSERT ON CONFLICT UPDATE) or check existence first

### Snake_case/camelCase Systematic Issue
API returns snake_case, frontend expects camelCase. Fields affected:
- `person_id` → `personId`
- `faculty_role` → `facultyRole`
- `display_abbreviation` → `displayAbbreviation`
- `activity_id` → `activityId`
- `effective_date` → `effectiveDate`

**Long-term fix:** Add response transformer in API hooks to convert snake_case to camelCase.

### Next Steps (After Verification)
1. **Test full CRUD flow** - Create template, save, verify persistence, refresh page
2. **Test Week mode** - Create override for specific week
3. **Phase 6: Constraint Integration** - Register `FacultyWeeklyTemplateConstraint` in solver

### Commits This Session
- `9ee9f8ae` - feat: Add faculty weekly activity editor (full stack)
- `44c7741d` - feat: Add inline faculty role editing in matrix view
- `c011fc7b` - fix: Remove broken join() code in get_permitted_activities
- `a95d4d9c` - fix: Faculty Weekly Editor UI bugs (abbreviations, roles, save)
- `47adb15b` - fix: Use person_id from API (snake_case fix) - ROLE SAVES WORK NOW
- `1cb3c8df` - docs: Update scratchpad

### NEXT SESSION: Fix Bug 5
**File:** `backend/app/services/faculty_activity_service.py`
**Method:** `create_override()` (around line 300-350)
**Fix:** Change INSERT to UPSERT (INSERT ON CONFLICT DO UPDATE)

### Faculty Roles Set (2026-01-09)
```
Aaron Montgomery: pd
Alex LaBounty: apd
Bridget Colgan: oic
Joe Napierala: dept_chief
Jimmy Chu: sports_med
Blake Van Brunt, Brian Dahl, Chelsea Tagawa, Chris McGuire, Sarah Kinkennon, Zach Bevis, Zach McRae: core
```

### Database Status (Verified)
```
=== Faculty Activity Permissions ===
adjunct: 3 activities
apd: 5 activities
core: 5 activities
dept_chief: 5 activities
oic: 6 activities
pd: 4 activities
sports_med: 4 activities

=== Activities ===
at: Attending Time (active)
dfm: Dept Family Medicine (active)
do: Direct Observation (active)
fm_clinic: FM Clinic (active)
gme: Graduate Medical Education (active)
pcat: Post-Call Attending Time (active)
sm_clinic: Sports Medicine Clinic (active)
```

### Next Steps
1. Set faculty roles in DB (currently all NULL)
2. Test full template CRUD (create, view, edit, save)
3. Test week-specific override flow
4. Verify constraint integration with solver
