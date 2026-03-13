# DB Schema Reference — Gotchas, Invariants, and Landmines

> Generated 2026-03-12 · Quick-reference for agents editing scheduling models or services

---

## 1. The Three-Table Contract

```
block_assignments → assignment → half_day_assignments
    (INTENT)        (DECISION)    (GROUND TRUTH)
```

| Table                  | Grain                       | FK to block system         | ~Rows/block        |
| ---------------------- | --------------------------- | -------------------------- | ------------------ |
| `block_assignments`    | person × block × block_half | `academic_blocks.id`       | 36 (18 × 2 halves) |
| `assignments`          | person × block × role       | `blocks.id` (legacy)       | 18                 |
| `half_day_assignments` | person × date × AM/PM       | *none* (uses actual dates) | ~1,000             |

> [!CAUTION]
> `assignments` uses `blocks.id` (legacy). `block_assignments` uses `academic_blocks.id`. These are **different tables**. Never assume they reference the same FK. When writing cross-table queries, join through `person_id` + date range, not through a shared block FK.

---

## 2. Block-Half Invariants

Every resident has **exactly 2 `BlockAssignment` rows per block** (`block_half=1` and `block_half=2`).

- **Full-block rotation** (e.g., FMIT): both rows share the same `rotation_template_id`
- **Split rotation** (e.g., DERM/NF): half 1 → DERM, half 2 → NF

### The Triple-Encoding of Combined Rotations

Combined rotations are encoded in **three places simultaneously**. All three must stay consistent:

| Location                                                                | Example for DERM/NF                                |
| ----------------------------------------------------------------------- | -------------------------------------------------- |
| `RotationTemplate.name`                                                 | `"DERM/NF"` (the canonical combined template)      |
| `RotationTemplate.first_half_component_id` / `second_half_component_id` | Self-referential FKs → DERM template, NF template  |
| `BlockAssignment` rows                                                  | 2 rows: `block_half=1` → DERM, `block_half=2` → NF |

> [!IMPORTANT]
> When creating or editing combined rotation templates, you must set `first_half_component_id` and `second_half_component_id`. The `InpatientHeadcountConstraint` and `sync_preload_service` depend on these to do week-aware NF counting.

### Block-Half Grouping Pattern

6+ services perform the same "group by resident, merge halves" dance:

```python
by_resident: dict[UUID, dict[int, BlockAssignment]] = {}
for assignment in block_assignments:
    by_resident.setdefault(assignment.resident_id, {})[assignment.block_half] = assignment
```

Services doing this: `preload_service`, `sync_preload_service`, `block_schedule_export_service`, `block_assignment_import_service`, `half_day_xml_exporter`, `schedule_draft_service`.

### Block-Half Date Scoping

```python
if assignment.block_half == 1:
    # Days 1–14 of the block
elif assignment.block_half == 2:
    # Days 15–28 of the block
```

Utility: `app.utils.academic_blocks.get_block_half(date)` returns 1 or 2 for any date.

---

## 3. Source Priority System

`half_day_assignments.source` controls overwrite rules. **Higher priority sources cannot be overwritten by lower ones.**

```
preload (1) > manual (2) > solver (3) > template (4)
```

| Source     | Meaning                                    | Locked?                                |
| ---------- | ------------------------------------------ | -------------------------------------- |
| `preload`  | FMIT, call, absences, protected activities | ✅ NEVER overwritten                    |
| `manual`   | Human override (coordinator)               | ✅ NEVER overwritten by solver          |
| `solver`   | CP-SAT computed                            | ❌ Can be overwritten by preload/manual |
| `template` | Default from WeeklyPattern                 | ❌ Lowest priority                      |

### Locked Activity Codes (`activity_locking.py`)

These codes always get `source=preload`:

```
FMIT, LV, LV-AM, LV-PM, W, W-AM, W-PM, PC, PCAT, DO,
LEC, LEC-PM, ADV, SIM, HAFP, USAFP, BLS, DEP, PI, MM,
HOL, TDY, CCC, ORIENT, OFF, OFF-AM, OFF-PM
```

Additionally, any activity with `activity_category="time_off"` or `is_protected=True` is auto-locked.

> [!WARNING]
> The locked codes list in `activity_locking.py` and the blocking codes list are **different sets**. `_LOCKED_CODES` controls source priority. `_BLOCKING_CODES` controls whether the solver should skip a slot entirely. Editing one without checking the other will create inconsistencies.

---

## 4. Import Round-Trip Landmines

### Metadata Gate
Import rejects files where the `__SYS_META__` sheet's block number or academic year doesn't match the target. No partial imports across blocks.

### UUID Anchoring vs. Fuzzy Fallback
- Exports embed `person_id` UUIDs in the hidden `__ANCHORS__` sheet
- Import uses UUIDs for identity (not names)
- Legacy files without `__ANCHORS__` fall back to fuzzy name matching — this is fragile with common surnames

### Diff Guard
Imports changing >20% of cells trigger a warning. This is a soft gate (warning, not rejection).

### The Block-Half Sibling Problem on Import
When importing a split rotation change, the import service must:
1. Find the existing `block_half=1` row
2. Delete any `block_half=2` sibling
3. Re-create both halves as a pair

If only one half is updated and the sibling deletion is skipped, you get orphaned half-rows → downstream services that group by resident will see incomplete pairs.

### `is_override` vs. `source`
These are **independent fields** on `half_day_assignments`:
- `is_override=True` means the cell was manually changed (import or GUI edit)
- `source="manual"` or `source="import"` means where it came from
- A preloaded activity can have `is_override=True` if a coordinator overrode it — the `source` stays `"manual"`, not `"preload"`

---

## 5. The `assignments` Table: Legacy Bridge

The `assignments` table (FK to `blocks.id`) is the **legacy solver output** with explainability fields:

```python
explain_json     # Full DecisionExplanation
confidence       # 0–1 score
score            # Objective score
alternatives_json # Top alternatives considered
audit_hash       # SHA-256 integrity check
```

It also has `__versioned__ = {}` (SQLAlchemy-Continuum audit trail).

> [!NOTE]
> `block_assignments` does NOT have versioning. `half_day_assignments` does NOT have versioning. Only `assignments` and `rotation_templates` have `__versioned__`. If you need an audit trail for half-day changes, the `ImportBatch` / `ImportStagedAssignment` staging tables and the `overridden_by` / `overridden_at` fields are the mechanism.

---

## 6. `RotationTemplate` Flags That Interact

| Flag                       | Effect                                                                                            |
| -------------------------- | ------------------------------------------------------------------------------------------------- |
| `is_block_half_rotation`   | Template is 14 days, not 28. Controls `block_half` row creation.                                  |
| `leave_eligible`           | Whether scheduled leave is allowed. Emergency absences always generate conflicts.                 |
| `includes_weekend_work`    | Whether weekends are auto-populated or left as OFF.                                               |
| `first_half_component_id`  | Self-FK for combined rotation first half (e.g., DERM in DERM/NF).                                 |
| `second_half_component_id` | Self-FK for combined rotation second half (e.g., NF in DERM/NF).                                  |
| `is_archived`              | Soft delete. Archived templates should be excluded from solver but preserved for historical data. |

> [!IMPORTANT]
> `is_block_half_rotation=True` on the **component** templates (DERM, NF individually), not on the combined template (DERM/NF). The combined template is a full-block wrapper. Setting this flag wrong breaks the `block_half` row logic in `annual_rotation_service` and `block_scheduler_service`.

---

## 7. Common Mistakes to Avoid

| Mistake                                                                      | Why It Breaks                                                                                   |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Querying `block_assignments` with only `block_half=1`                        | Misses the second half of split rotations                                                       |
| Joining `assignments` to `block_assignments` via block FK                    | They reference different block tables                                                           |
| Setting `source="preload"` on a solver-computed activity                     | Permanently locks the slot; solver can never reclaim it                                         |
| Creating a `BlockAssignment` without both `block_half` rows                  | Every downstream consumer expects exactly 2 rows per resident per block                         |
| Editing `_LOCKED_CODES` without updating `_BLOCKING_CODES`                   | Solver may assign over locked activities, or skip non-locked ones                               |
| Forgetting `is_block_half_rotation` flag when adding a new combined template | `annual_rotation_service` and `block_scheduler_service` won't create the 2-row split correctly  |
| Using `assignment.block_id` to scope dates                                   | `blocks.id` may not have the same date range as `academic_blocks.id` for the same logical block |

---

## 8. Key Utilities

| Utility                                     | Location                     | Purpose                                    |
| ------------------------------------------- | ---------------------------- | ------------------------------------------ |
| `get_block_half(date)`                      | `app.utils.academic_blocks`  | Returns 1 or 2 for any calendar date       |
| `get_block_number_for_date(date)`           | `app.utils.academic_blocks`  | Returns block number (1–13) for a date     |
| `is_activity_preloaded(activity)`           | `app.utils.activity_locking` | Should this activity be locked as preload? |
| `is_activity_blocking_for_solver(activity)` | `app.utils.activity_locking` | Should solver skip this slot entirely?     |
| `is_code_preloaded(code)`                   | `app.utils.activity_locking` | Raw code lookup against locked set         |
