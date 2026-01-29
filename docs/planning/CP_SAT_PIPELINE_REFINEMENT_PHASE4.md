# CP-SAT Pipeline Refinement — Phase 4

Date: 2026-01-29
Scope: Consolidation, cleanup, and technical debt reduction

## Purpose
Phase 4 addresses technical debt identified in the scheduling knowledge audit.
Focus is on reducing duplication, preventing context poisoning, and improving
maintainability before adding new features.

**Next:** See [Phase 5](CP_SAT_PIPELINE_REFINEMENT_PHASE5.md) for post-release
coverage adjustments and Excel round-trip workflows.

**Scope guardrails**
- No new scheduling features (consolidation only)
- All changes must pass existing MCP validation
- Database-backed config changes require migration

---

## Phase 4 Scope

### P4-1 — Extract VAS Configuration Module
**Goal:** Eliminate duplication of VAS faculty names, penalties, and allowed times.

**Status:** ✅ Superseded by credential model (2026-01-29)

**Notes**
- VAS/VASC now use `procedure_credentials` with competency-based penalties.
- No hardcoded faculty name lists remain in the solver/allocator.

---

### P4-2 — Database-Backed VAS Faculty Eligibility
**Goal:** Replace hardcoded faculty names with database configuration.

**Status:** ✅ Complete via procedure credentials (2026-01-29)

**Notes**
- Eligibility + priority are driven by `procedure_credentials.competency_level`.
- Future additions (BTX/COLPO) will reuse the same credential model.

---

### P4-3 — Mark Non-Canonical Constraints
**Goal:** Prevent AI context poisoning from constraints that exist but don't run.

**Status:** 🔲 Not started

**Affected Constraints**
- `ResidentWeeklyClinicConstraint` - data not wired
- `IntegratedWorkloadConstraint` - uses wrong variable names
- `FacultyWeeklyTemplateConstraint` - requires missing variables
- `DeptChiefWednesdayPreferenceConstraint` - preference-only, not registered

**Target**
Add clear markers to each non-canonical constraint:
```python
class ResidentWeeklyClinicConstraint(SoftConstraint):
    """
    ⚠️ NOT_IMPLEMENTED - This constraint is not registered in the manager.
    Data wiring incomplete. Do not reference in AI prompts.

    [existing docstring...]
    """
```

**Acceptance Criteria**
- All non-canonical constraints have `NOT_IMPLEMENTED` in docstring
- `docs/scheduling/NON_CANONICAL_CONSTRAINTS.md` updated with current list
- RAG ingest excludes or flags non-canonical constraint docs

---

### P4-4 — Centralize Activity Code Definitions
**Goal:** Single source of truth for activity code sets.

**Status:** 🔲 Not started

**Current State (fragmented)**
| File | Codes Defined |
|------|---------------|
| `fmc_capacity.py` | FMC_CAPACITY_CODES, PROC_VAS_CODES, SM_CAPACITY_CODES, CV_CODES |
| `activity_solver.py` | Inline sets for clinic, AT, admin |
| `fm_scheduling.py` | LEC_EXEMPT_ROTATIONS, NIGHT_FLOAT_ROTATIONS |
| `vas_allocator.py` | PROTECTED_ACTIVITY_CODES |

**Target**
Create `backend/app/scheduling/constants/activity_codes.py`:
```python
# Activity Code Sets - Single Source of Truth

# Capacity codes
FMC_CAPACITY_CODES = {"C", "C-N", "C-I", "FM_CLINIC", ...}
SM_CAPACITY_CODES = {"SM", "SM_CLINIC", "ASM"}
PROC_CODES = {"PR", "PROC", "PROCEDURE"}  # NOT including VAS
CV_CODES = {"CV"}

# Supervision codes
AT_CODES = {"AT", "PCAT"}
SUPERVISION_REQUIRED_CODES = {"PROC", "PR", "PROCEDURE"}  # VAS excluded

# Protected codes (never override)
PROTECTED_CODES = {"FMIT", "PCAT", "DO", "OFF", "W", "LEAVE"}

# Rotation exemptions
LEC_EXEMPT_ROTATIONS = {"NF", "NF-PM", "NF-ENDO", ...}
NIGHT_FLOAT_ROTATIONS = {"NF", "NF-PM", "NF-ENDO", "NEURO-NF", "PNF"}
```

**Acceptance Criteria**
- Single import point for all activity code sets
- All constraint files import from constants module
- No inline activity code sets in constraint logic

---

### P4-5 — Validate Manual Override Templates
**Goal:** Ensure manual override JSON files reference valid DB templates.

**Status:** 🔲 Not started

**Current State**
- `data/inpatient_time_off_overrides_manual.json` contains template abbreviations
- No validation that these match `rotation_templates.display_abbreviation`

**Target**
Add validation to `apply_inpatient_time_off_overrides.py`:
```python
# Validate all template abbreviations exist in DB
for abbrev in override_data.keys():
    template = session.query(RotationTemplate).filter(
        RotationTemplate.display_abbreviation == abbrev
    ).first()
    if not template:
        logger.warning(f"Override template '{abbrev}' not found in DB - skipping")
```

**Acceptance Criteria**
- Apply script warns on unmatched template abbreviations
- Dry-run mode shows all skipped templates
- Option to fail-fast on unmatched templates (`--strict`)

---

### P4-6 — Document Day-of-Week Conventions
**Goal:** Prevent future bugs from mixing day-of-week conventions.

**Status:** 🔲 Not started

**Current State**
Two conventions exist (both valid, used consistently):
- **Database/weekly_patterns:** 0=Sunday, 1=Monday, ..., 6=Saturday
- **Python weekday():** 0=Monday, 1=Tuesday, ..., 6=Sunday

**Target**
Add to `docs/development/BEST_PRACTICES_AND_GOTCHAS.md`:
```markdown
## Day-of-Week Conventions

⚠️ Two conventions exist - do not mix them!

| Context | Sunday | Monday | Saturday | Used In |
|---------|--------|--------|----------|---------|
| `weekly_patterns.day_of_week` | 0 | 1 | 6 | DB models, time-off scripts |
| Python `date.weekday()` | 6 | 0 | 5 | Date comparisons, call constraints |

When working with weekly_patterns, use the DB convention.
When comparing dates, use Python's weekday().
Never convert between them without explicit mapping.
```

**Acceptance Criteria**
- BEST_PRACTICES_AND_GOTCHAS.md updated
- RAG contains day-of-week convention guidance
- Code review checklist includes day-of-week convention check

---

## Phase 4 Tech Debt Notes

**Deferred from Phase 3:**
- Block quality report ACGME compliance still stubbed (hardcoded 100%)
- `/api/schedule/validate` test failures (legacy redirect issue)

**Known Context Poisoning Risks:**
- Non-canonical constraints (addressed in P4-3)
- Terminology confusion (Outpatient vs Clinic, Block vs AcademicBlock)
- Excel import hardcoded row numbers

---

## Verification

After each P4 item:
```bash
# MCP validation
mcp__residency-scheduler__validate_schedule_tool

# Regenerate Block 10
python scripts/ops/block_regen.py --block 10 --academic-year 2026 --dry-run

# VAS allocation
python scripts/ops/vas_allocator.py --block 10 --academic-year 2026 --dry-run --verbose

# Run tests
cd backend && pytest -x
```

---

## Dependencies

| Item | Depends On | Blocked By |
|------|------------|------------|
| P4-1 | None | - |
| P4-2 | P4-1 | Migration approval |
| P4-3 | None | - |
| P4-4 | P4-1 | - |
| P4-5 | None | - |
| P4-6 | None | - |

**Recommended Order:** P4-1 → P4-4 → P4-3 → P4-6 → P4-5 → P4-2
