# Scheduling Terms and Data Model (Authoritative)

This document defines the meaning of **block**, **rotation**, **activity**, and
**assignment** in this codebase. The goal is to prevent UI/LLM confusion by
locking in precise terminology.

## Academic year (non-Gregorian)

- Academic year runs **July 1 → June 30**.
- The stored `academic_year` is the **starting year** (e.g., `2025` means AY 2025–2026).

Source of truth: `backend/app/utils/academic_blocks.py`.

## Blocks

- A **block** is a time container.
- **Block 0**: orientation (July 1 → day before first Thursday; 0–6 days).
- **Blocks 1–12**: 28 days each, **Thursday → Wednesday**.
- **Block 13**: variable length, ends June 30.

Blocks define *when* rotations occur. They are not rotations.

## Rotations (RotationTemplate)

- A **RotationTemplate** is the rotation itself (multi-week container).
- Rotations span an entire block (or half-block if configured).
- Rotations are *not* Activities. They hold rules about how Activities are
  placed inside the block.

Key model: `backend/app/models/rotation_template.py`.

### RotationTemplate.activity_type

This field is a **category label for the rotation**, not an Activity.

- It is used for **solver filtering** and **constraint selection**.
- Examples: `outpatient`, `clinic`, `inpatient`, `conference`, `education`, `off`.

**Rule:** activity_type is a *subset/category of the rotation* and never the
Activity itself.

## Activities (Activity)

- An **Activity** is a *theoretical assignment unit* (e.g., FM Clinic, Lecture).
- Activities define what can fill a half-day slot.
- Activities can repeat many times across dates and people.

Key model: `backend/app/models/activity.py`.

## Assignments (realized activities)

- An **Assignment** is an Activity **made real** with:
  - specific date
  - specific person (resident/faculty)
  - specific time-of-day

Examples:
- `HalfDayAssignment` = most AM/PM schedule cells.
- `CallAssignment` = call-specific schedule entry.

Key models: `backend/app/models/half_day_assignment.py`,
`backend/app/models/call_assignment.py`.

## How they fit together

```
AcademicYear
  └─ Blocks (0–13, date ranges)
       └─ RotationTemplate (rotation container)
            └─ Activities (theoretical half‑day units)
                 └─ Assignments (Activity + date + person)
```

### Solver behavior (important)

- The CP-SAT half-day solver defaults to **RotationTemplate.activity_type = outpatient**.
- Inpatient/away rotations are preloaded (locked) before solver runs.

Sources:
- `backend/app/scheduling/engine.py` (`_get_rotation_templates`)
- `backend/app/services/sync_preload_service.py`

## UI terminology guidance

To avoid confusion in the GUI:

- **Rotation** = RotationTemplate (multi-week container).
- **Rotation category/setting** = `RotationTemplate.activity_type`.
- **Activity** = theoretical assignment unit (FM clinic, lecture, procedure).
- **Assignment** = Activity scheduled to a person/date.

If UI copy needs a label for `activity_type`, use **“Rotation category”** or
**“Rotation setting”** (not “Activity”).
