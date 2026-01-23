# Session 131: Templates Hub + CP-SAT Template Logic

**Date:** 2026-01-22
**Branch:** `feature/rotation-faculty-templates`
**Status:** COMPLETE - Templates Hub wired, CP-SAT logic documented

---

## What Was Done

### 1. Templates Hub Implementation
- Created `/templates` page with tier-based access
- Wired up all panels: RotationsPanel, MySchedulePanel, FacultyPanel, MatrixPanel
- Uses Green/Amber/Red RiskBar pattern from Swaps Hub

### 2. CP-SAT Template Logic Analysis
**Document:** `docs/reports/ROTATION_TEMPLATE_HALFDAY_COMPARISON.md`

Analyzed how rotation templates should be translated for CP-SAT solver.

---

## Critical CP-SAT Insight: Inpatient Rotations are 100% Fixed

**ALL 31 inpatient rotations are SOLVER INPUT, not variables.**

The solver does NOT optimize inpatient assignments. It reads them as **constants** that:
1. **Consume supervision capacity** (faculty attending required)
2. **Consume physical space** (ward beds, ICU beds, etc.)
3. **Block slots** (can't double-book a resident)

### Inpatient Rotations (31 total)

| Category | Templates | Constraint Impact |
|----------|-----------|-------------------|
| **FMIT** | FMIT-PGY1, FMIT-PGY2, FMIT-PGY3, FMIT-FAC-AM/PM | Ward census, faculty supervision |
| **Night Float** | NF, NF-AM, NF-PM, NF-CARDIO, NF-FMIT-PGY1, NF-LD, NF-NICU-PGY1, NF-PEDS-PGY1, NF-DERM-PGY2, NF-MED-SEL | Night coverage capacity |
| **Combined** | C+N, D+N, NIC, NEURO-1ST-NF-2ND, NF-1ST-ENDO-2ND | Split-block patterns |
| **ICU/NICU** | ICU, NICU | Critical care census |
| **L&D** | LAD, TAMC-LD, NF-LD | Labor coverage |
| **Peds** | NBN, PEDS-EM, PEDS-WARD-PGY1 | Pediatric census |
| **IM** | IM, IM-PGY1 | Medicine ward census |
| **Psych** | PSYCH | Psych unit census |
| **EM** | EM | ED coverage |

### PGY-Specific Clinic Days (FMIT)

| PGY | Clinic Day | Time | Rationale |
|-----|------------|------|-----------|
| PGY-1 | Wednesday | AM | Staggered for ward coverage |
| PGY-2 | Tuesday | PM | Staggered for ward coverage |
| PGY-3 | Monday | PM | Supervises intern clinic (C-I) |

### CP-SAT Treatment

```python
# Inpatient templates are CONSTANTS
# They create constraints for faculty/space allocation:

for resident in block_assignments:
    template = resident.rotation_template

    if template.activity_type == 'inpatient':
        # All 56 slots are FIXED - load from weekly_patterns
        for slot in template.weekly_patterns:
            # Mark slot as occupied
            model.Add(assignment[resident][slot] == slot.activity_id)

            # Increment location census
            if slot.activity in [FMIT, IM, PEDS_WARD]:
                ward_census[slot.location][slot.time] += 1
            elif slot.activity in [ICU, NICU]:
                icu_census[slot.location][slot.time] += 1
            elif slot.activity == NF:
                night_coverage[slot.time] += 1

            # Require supervision if on service
            if slot.requires_supervision:
                model.Add(
                    sum(faculty_assigned[slot.location][slot.time]) >=
                    supervision_ratio[slot.activity]
                )
```

---

## Template Classification Summary

| Class | Examples | Solver Role |
|-------|----------|-------------|
| **A: 100% Fixed** | All inpatient (31), NF, Leave, Off-site | Input constants, create constraints |
| **B: Partially Fixed** | FMC, outpatient with fixed academics | Some fixed slots + count constraints |
| **C: Count-Only** | Electives, selectives | Full solver freedom within counts |

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `docs/reports/ROTATION_TEMPLATE_HALFDAY_COMPARISON.md` | Full CP-SAT translation guide |
| `frontend/src/app/templates/page.tsx` | Templates Hub main page |
| `frontend/src/app/templates/_components/*.tsx` | Panel components |
| `docs/user-guide/templates.md` | User documentation |

---

## Database State

**Backup:** `backups/20260122_102856_Pre-Codex half-day rotation template values/`

| Table | Current State | Target State |
|-------|---------------|--------------|
| `rotation_templates` | 87 templates | No change |
| `weekly_patterns` | 5-9 patterns per template (incomplete) | 56 patterns for Class A templates |
| `rotation_halfday_requirements` | 0 entries | Counts for Class B/C templates |

---

## Resume Command

```
Continue from session 131. Branch: feature/rotation-faculty-templates

Key insight: ALL inpatient rotations (31) are 100% fixed - CP-SAT treats them as
input constants that consume supervision/space, NOT as optimization variables.

Read docs/reports/ROTATION_TEMPLATE_HALFDAY_COMPARISON.md for full CP-SAT logic.
Read docs/scratchpad/session-131-templates-hub.md for context.
```

---

## Next Steps for Codex

1. **Populate `weekly_patterns`** for all Class A templates (inpatient, NF, leave, off-site)
   - Full 56-slot patterns
   - `is_protected=true` for all slots

2. **Populate `rotation_halfday_requirements`** for Class B/C templates
   - Extract counts from Excel
   - Mark fixed slots in `weekly_patterns`

3. **Validate** supervision and space constraints are derivable from populated data
