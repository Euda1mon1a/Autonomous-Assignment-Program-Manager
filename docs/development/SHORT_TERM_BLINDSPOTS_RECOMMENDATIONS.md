# Short-Term Blindspots and Recommendations

This document captures likely blindspots in the current short-term vision and concrete recommendations for each.

## 1) Data provenance / lineage

Issue: Records lack a clear source-of-truth marker (seed vs manual vs import), which makes cleanup and reruns fragile.

Recommendation:
- Add a `source` field (and optional `external_id`) for Person, RotationTemplate, Block, Assignment, Absence.
- Require imports to set these fields; forbid seed data from being overwritten by sync jobs unless explicitly flagged.

## 2) Academic year boundaries

Issue: Logic assumes July 1 and 28-day blocks; year rollover and leap-year edge cases aren’t validated.

Recommendation:
- Add a unit test for `block_half` across June/July boundaries and leap years.
- Use `BLOCK_LENGTH_DAYS` and academic year config everywhere block periods are computed.

## 3) Absence semantics (blocking vs partial)

Issue: Absence import defaults to blocking, which may over-constrain the solver if the data includes partial absences.

Recommendation:
- Map absence categories to `is_blocking` based on absence type.
- Add a CLI flag to the import script to toggle blocking defaults.

## 4) FMIT preservation vs supervision conflicts

Issue: Preserved FMIT assignments aren’t considered in supervision assignment, risking double-booking.

Recommendation:
- Exclude preserved FMIT faculty from `_assign_faculty` for the same block.
- Optionally mark those blocks as “occupied” in the availability matrix.

## 5) Rotation naming normalization

Issue: Hardcoded rules depend on stable rotation names; naming drift across imports can silently break constraints.

Recommendation:
- Normalize rotation names and abbreviations on import.
- Add a validation step that fails fast if required hardcoded rotations (NF, PC, FMIT, NICU) are missing.

## 6) Post-generation audit gaps

Issue: No automated validation that required half-day allocations (e.g., post-NF PC day adjustments) match generated assignments.

Recommendation:
- Add a post-generation audit report for half-day requirements vs actuals.
- Surface violations in ScheduleResponse and logs.

## 7) API contract mismatches

Issue: Small mismatches (e.g., time_of_day=ALL) cause 400s and are easy to miss.

Recommendation:
- Add contract tests for all schedule-related filters.
- Where feasible, interpret sentinel values instead of failing (e.g., `ALL` -> omit filter).

## 8) Manual overrides and swap provenance

Issue: Manual edits (GUI overrides, swaps, emergency holiday decisions) can conflict with solver outputs and may be overwritten without clear provenance.

Recommendation:
- Add per-assignment provenance fields (e.g., `origin=solver|manual|swap|import`).
- Record override reason and timestamp (e.g., `manual_override_reason`, `manual_override_at`).
- Prevent automated regeneration from overwriting manual or swap assignments unless explicitly allowed.

## 9) Human-only Excel behaviors not modeled yet

Issue: The Excel schedule encodes human-only behaviors that aren’t represented in the data model, which can lead to silent mismatches or lost intent.

Recommendation:
- Add optional per-assignment notes (free-text).
- Support tentative vs committed assignments (status flag).
- Allow partial coverage rules (e.g., clinic canceled for specific teams only).
- Define defaults explicitly (e.g., blank cell implies clinic) in templates.
- Support non-policy swaps with explicit approval metadata.
- Add per-block eligibility exclusions (temporary do-not-assign lists).
- Model variable staffing caps (clinic room count changes by week).
- Support non-standard holidays/closures with manual override flags.
- Allow split roles within a half-day (shared assignments).
- Support carry-over preferences (stay on rotation unless bumped).
- Add priority overrides (must-schedule flags) with rationale.
- Preserve visual grouping/ordering as a UI concern (not a hidden rule).
