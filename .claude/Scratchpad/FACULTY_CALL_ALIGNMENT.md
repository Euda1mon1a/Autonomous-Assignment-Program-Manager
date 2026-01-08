# Session 068-073 - Solver + Import System

**Branch:** `session/067-antigravity-faculty-call` | **Date:** 2026-01-07/08

---

## SESSION 073 COMPLETED ✅

### PRs Created
- **PR #662** (merged) - Sessions 067-072: Admin UI, Faculty Call, Schedule Views
- **PR #663** (merged) - Rotation templates documentation
- **PR #664** (pending) - Greedy solver call generation + import script

### Key Accomplishments
1. **Greedy solver now generates faculty call** - 20 call assignments verified
2. **7 new rotation templates created**: FMC, POCUS, SURG-EXP, GYN-CLIN, KAPI-LD, NF-ENDO, NEURO-NF
3. **Block 10 data imported**: 17 residents with rotation assignments
4. **Import script created**: `backend/scripts/import_block_assignments.py`
5. **Full year CSV prepared**: `full_year_assignments.csv` (17 residents × 13 blocks = 221 rows)

### Backup Updated
- Location: `~/backups/scheduler-20260107/`
- Contents: `repo.bundle`, `db.sql.gz`, `rag_documents.sql`, `block_assignments.sql.gz`

---

## SESSION 074 COMPLETED ✅

### Full Year Import - DONE

**File:** `full_year_assignments.csv`
- 17 residents (PGY1: 6, PGY2: 6, PGY3: 5)
- 13 blocks (Jul 2025 - Jun 2026)
- 221 assignments imported

### 17 New Rotation Templates Created
| Abbrev | Name | Type |
|--------|------|------|
| CARDIO | Cardiology | outpatient |
| DERM | Dermatology | outpatient |
| ELEC | Elective | outpatient |
| EM | Emergency Medicine | inpatient |
| FAC-DEV | Faculty Development | education |
| GERI | Geriatrics | outpatient |
| IM | Internal Medicine Ward | inpatient |
| JAPAN | Japan Off-Site Rotation | off |
| MILITARY | Military Duty | off |
| MSK-SEL | Musculoskeletal Selective | outpatient |
| PEDS-CLIN | Pediatrics Clinic | outpatient |
| PEDS-EM | Pediatric Emergency Medicine | inpatient |
| PEDS-SUB | Pediatrics Subspecialty | outpatient |
| PROC | Procedures | procedures |
| PSYCH | Psychiatry | inpatient |
| SEL-MED | Medical Selective | outpatient |
| TAMC-LD | TAMC Labor & Delivery | inpatient |

### GUI Import Lessons Documented
- See: `docs/planning/GUI_IMPORT_LESSONS.md`
- Key insights for Admin UI import feature

---

## PREVIOUS SESSION COMPLETED ✅

### Session 068-070
1. Real Personnel Data Restored (29 people, 60 templates)
2. Immaculate Backup Created: `immaculate_real_personnel_20260107`
3. RAG Updated (personnel, templates, backup reference)
4. People Toggle Bug Fixed (`role` → `type` parameter)
5. Auto-save with Backup Endpoint
6. Week-by-week Pattern Editing
7. Half-block Rotation Support

### Session 071 (Current)
8. **Page Renaming** ✅
   - `/templates` → `/activities`
   - `/admin/templates` → `/admin/rotations`
   - Updated: `Navigation.tsx`, `MobileNav.tsx`, `QuickActions.tsx`
   - Long-term TODO added to `docs/TODO_INVENTORY.md`

9. **Navigation Cleanup** ✅
   - Added `/admin/people` and `/admin/credentials` links
   - Updated Navigation.tsx and MobileNav.tsx

10. **Admin People Bulk Edit Page** ✅
    - `frontend/src/app/admin/people/page.tsx`
    - `frontend/src/components/admin/PeopleTable.tsx`
    - `frontend/src/components/admin/PeopleBulkActionsToolbar.tsx`
    - `frontend/src/hooks/usePeople.ts` - Added `useBulkDeletePeople`, `useBulkUpdatePeople`

11. **Procedure Credentialing Matrix** ✅
    - `frontend/src/app/admin/credentials/page.tsx`
    - `frontend/src/components/admin/CredentialMatrix.tsx`
    - `frontend/src/components/admin/CredentialCellModal.tsx`
    - `frontend/src/components/admin/ExpiringCredentialsAlert.tsx`
    - Hooks already existed in `frontend/src/hooks/useProcedures.ts`

---

## ALL ADMIN UI TASKS COMPLETE

Plan file: `.claude/plans/merry-hatching-torvalds.md`

---

## Key Files Created/Modified This Session

| File | Action |
|------|--------|
| `frontend/src/app/activities/page.tsx` | RENAMED from templates |
| `frontend/src/app/admin/rotations/page.tsx` | RENAMED from admin/templates |
| `frontend/src/app/admin/people/page.tsx` | CREATED |
| `frontend/src/app/admin/credentials/page.tsx` | CREATED |
| `frontend/src/components/admin/PeopleTable.tsx` | CREATED |
| `frontend/src/components/admin/PeopleBulkActionsToolbar.tsx` | CREATED |
| `frontend/src/components/admin/CredentialMatrix.tsx` | CREATED |
| `frontend/src/components/admin/CredentialCellModal.tsx` | CREATED |
| `frontend/src/components/admin/ExpiringCredentialsAlert.tsx` | CREATED |
| `frontend/src/hooks/usePeople.ts` | EXTENDED (batch hooks) |
| `frontend/src/components/Navigation.tsx` | MODIFIED |
| `frontend/src/components/MobileNav.tsx` | MODIFIED |
| `docs/TODO_INVENTORY.md` | MODIFIED (long-term rename TODO) |

---

## Test Credentials
- Username: `admin`
- Password: `admin123`

---

## Solver Improvement Notes (Session 072)

**Testing Results:**
| Algorithm | Status | Blocks | Violations | Runtime |
|-----------|--------|--------|------------|---------|
| greedy | success | 20 | 0 | 0.10s |
| cp_sat | failed/partial | 0-32 | 57 | 0.18-1.72s |
| hybrid | partial | 232 | 32 | 2.39s |

**Issues Identified:**
1. **Rotation template constraints not enforced** - Solver doesn't factor in:
   - `max_residents` (all NULL in DB)
   - `requires_specialty` (all NULL)
   - `requires_procedure_credential` (all false)
   - PGY level eligibility (not in schema)

2. **Missing constraint data** - Templates need populated:
   - Max residents per template per block
   - Specialty/credential requirements
   - PGY level restrictions

3. **Solver progression** - Greedy fast but limited; Hybrid best coverage but violations

**TODO:** Add template constraints as solver constraints, not just assignment targets

**Critical Finding - Empty Constraint Tables:**
| Table | Purpose | Rows |
|-------|---------|------|
| `rotation_halfday_requirements` | FM clinic/specialty/academics per rotation | 0 |
| `block_assignments` | Resident → Rotation per block | 0 |
| `rotation_preferences` | Additional constraints | 0 |
| `resident_weekly_requirements` | Weekly limits | 0 |

**Schema exists but needs data population:**
- `rotation_halfday_requirements.fm_clinic_halfdays` - how many FM clinic half-days
- `rotation_halfday_requirements.specialty_halfdays` - how many specialty half-days
- `rotation_halfday_requirements.specialty_name` - which specialty (Sports Med, OB, etc.)
- `block_assignments` - links resident to rotation for each block

**Without this data, solver assigns anyone to anything.**

**Note:** 5 min testing → longer schedule, but solver ran in seconds (efficient once constraints defined)

---

## Session 072 - Handoff Notes

### Commits Made
1. `b353d414` - feat(admin): Add bulk people editing and credential matrix pages
2. `8b76ae53` - fix(backend): Add settings export to config.py + admin docs

### Backend Fix Applied
- **Issue:** Backend crash - `ImportError: cannot import name 'settings'`
- **Fix:** Added `settings = get_settings()` to `backend/app/core/config.py:553`
- **Result:** Backend healthy, auth working

### Backup Created
- Location: `~/backups/scheduler-20260107/`
- Contents: `repo.bundle` (21MB), `db.sql.gz` (725KB), `.env.backup`

### GUI Testing (Comet)
- All pages tested and working ✅
- Admin dark panels working ✅
- Schedule generation working (greedy: 20 assignments, 0 violations)

### Key Solver Findings

**Faculty Call Generation:**
| Solver | Generates Call? |
|--------|-----------------|
| Greedy | ❌ NO |
| CP-SAT | ✅ YES |
| PuLP | ✅ YES |
| Hybrid | ✅ YES |

**Empty Constraint Tables (Critical Gap):**
- `block_assignments` - 0 rows (resident → rotation per block)
- `rotation_halfday_requirements` - 0 rows (half-days per rotation)
- `rotation_preferences` - 0 rows
- `resident_weekly_requirements` - 0 rows
- `call_assignments` - 0 rows

**Block 10 sample data format (names redacted):**
```
Rotation    Level    Resident
Hilo        R3 PGY3  [Resident_01]
NF/MS:Endo  R3 PGY3  [Resident_02]
FMC         R3 PGY3  [Resident_03]
FMIT 2      R3 PGY3  [Resident_04]
NEURO/NF    R3 PGY3  [Resident_05]
FMIT 2      R2 PGY2  [Resident_06]
SM          R2 PGY2  [Resident_07]
POCUS       R2 PGY2  [Resident_08]
L&D NF      R2 PGY2  [Resident_09]
Surg Exp    R2 PGY2  [Resident_10]
Gyn Clinic  R2 PGY2  [Resident_11]
FMC         R1 PGY1  [Resident_12]
Peds Ward   R1 PGY1  [Resident_13]
Kapi L&D    R1 PGY1  [Resident_14]
Peds NF     R1 PGY1  [Resident_15]
PROC        R1 PGY1  [Resident_16]
IM          R1 PGY1  [Resident_17]
```

### Next Steps (Priority Order)
1. **Add call to greedy solver** OR investigate CP-SAT failures
2. **Populate `block_assignments`** with resident rotation data
3. **Create import script** for rotation data from user's format
4. **Add `rotation_halfday_requirements`** to constrain solver

### Scheduler Order of Operations (Summary)
```
1. Load preserved (FMIT, NF, absences, off-site)
2. Build availability matrix
3. Load residents, faculty, templates
4. Run solver (greedy/cp_sat/pulp/hybrid)
5. Delete old, create new assignments
6. Assign faculty supervision
7. Validate ACGME, commit
```

### Branch Status
- `session/067-antigravity-faculty-call` - 5 commits ahead of origin
- Ready to push or continue work
