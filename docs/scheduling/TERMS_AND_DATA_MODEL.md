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
- There are two block concepts in the backend:
  - **AcademicBlock (Block 0–13)** = 28‑day containers that rotations span.
  - **Block (half‑day)** = AM/PM schedulable unit tied to a specific date.
- **Block 0**: orientation (July 1 → day before first Thursday; 0–6 days).
- **Blocks 1–12**: 28 days each, **Thursday → Wednesday**.
- **Block 13**: variable length, ends June 30.

Rotations span **AcademicBlocks**. Assignments land on **half‑day Blocks**.

## Rotations (RotationTemplate)

- A **RotationTemplate** is the rotation itself (multi-week container).
- Rotations span an entire block (or half-block if configured).
- Rotations are *not* Activities. They hold rules about how Activities are
  placed inside the block.

Key model: `backend/app/models/rotation_template.py`.

### RotationTemplate.rotation_type

This field is a **category/setting label for the rotation**, not an Activity.

- It is used for **solver filtering** and **constraint selection**.
- For **rotation templates** (`template_category = rotation`), the only valid
  values are **`inpatient`** or **`outpatient`**.
- For **non-rotation templates** (time_off/absence/educational), rotation_type
  reflects the category (`off`, `absence`, `recovery`, `education`, etc.).

**Rule:** rotation_type is a *subset/category of the rotation* and never the
Activity itself.

## Activities (Activity)

- An **Activity** is a *theoretical assignment unit* (e.g., FM Clinic, Lecture).
- Activities define what can fill a half-day slot.
- Activities can repeat many times across dates and people.

Key model: `backend/app/models/activity.py`.

### Clinic vs Outpatient (terminology)

- **Outpatient** = rotation setting (`rotation_type = outpatient`) for rotations
  whose half-days are **solved** (not preloaded).
- **Clinic** = an **Activity** for **Family Medicine Clinic (FMC)** continuity
  sessions (`fm_clinic`, `C`, `C-N`, etc.).
- **Activity types** are slot‑level (e.g., `fm_clinic`, `specialty`, `procedure`,
  `conference`). They live inside a rotation’s weekly pattern.

**Important:** `fm_clinic` is **not** a placeholder for “outpatient.” It means
**FMC continuity clinic** specifically.

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
  └─ AcademicBlocks (0–13, date ranges)
       └─ RotationTemplate (rotation container)
            └─ Activities (theoretical half‑day units)
                 └─ Assignments (Activity + date + person)
                      └─ Blocks (half‑day AM/PM slots)
```

### Solver behavior (important)

- The CP-SAT half-day solver only assigns **outpatient rotations**
  (`rotation_type = outpatient`, `template_category = rotation`).
- **Inpatient rotations** and **non-rotation templates** (off/absence/recovery/
  education) are preloaded/locked before the solver runs.

### FMC physical capacity (activity-level)

- Physical capacity is **assignment-level**, not rotation-level.
- `HalfDayAssignment.counts_toward_fmc_capacity = true` means the slot consumes
  **FMC physical capacity**.
- **SM** (resident supervision) counts as **1** per slot regardless of how many
  learners are assigned.

Sources:
- `backend/app/scheduling/engine.py` (`_get_rotation_templates`)
- `backend/app/services/sync_preload_service.py`

## UI terminology guidance

To avoid confusion in the GUI:

- **Rotation** = RotationTemplate (multi-week container).
- **Rotation category/setting** = `RotationTemplate.rotation_type`.
- **Activity** = theoretical assignment unit (FM clinic, lecture, procedure).
- **Assignment** = Activity scheduled to a person/date.

If UI copy needs a label for `rotation_type`, use **“Rotation category”** or
**“Rotation setting”** (not “Activity”).

## Naming rules (backend + docs)

- If it is **rotation‑related**, do **not** use “activity” in the name.
- Reserve “activity” for **slot‑level** Activities and Assignments only.
