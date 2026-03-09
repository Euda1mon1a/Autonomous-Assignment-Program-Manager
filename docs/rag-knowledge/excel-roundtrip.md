# Excel Stateful Round-Trip Pipeline

> **doc_type:** architecture
> **Source:** Condensed from `docs/architecture/excel-stateful-roundtrip-roadmap.md`
> **Last Updated:** 2026-03-09
> **Purpose:** Excel pipeline phases 1-4, schema hardening tracks

---

## Problem

The Excel export/import pipeline treated `.xlsx` files as dumb visual grids. Coordinators export, edit in Excel, re-import. The import used fuzzy name matching (`difflib.SequenceMatcher` at 0.85), heuristic column discovery, and had no way to detect stale or wrong-block files.

## Vision

Transform exported Excel workbooks into **Stateful Offline Clients** — files carrying their own metadata, identity anchors, input validation, and provenance tracking. In parallel, harden the database schema for proper academic-year scoping and leave accounting.

---

## Excel Pipeline (Phases 1-4) — COMPLETE

### Phase 1: Phantom Database (Hidden Metadata) — DONE

**Goal:** Import rejects wrong-block or stale files before parsing.

Two `veryHidden` sheets injected at export:

1. **`__SYS_META__`** — JSON in A1: `{academic_year, block_number, export_timestamp, export_version}` + SHA-256 schedule checksum
2. **`__REF__`** — Named Ranges: `ValidRotations`, `ValidActivities` (used by Phase 3 dropdowns)

**Backward compatible:** `if "__SYS_META__" in wb.sheetnames:` — legacy files fall through to fuzzy path.

**Key file:** `backend/app/services/excel_metadata.py`

### Phase 2: Spatial UUID Anchoring — DONE

**Goal:** Deterministic person mapping; O(1) diff detection on unchanged rows.

Third `veryHidden` sheet — **`__ANCHORS__`**:

| Column | Content |
|--------|---------|
| A | `person_id` (UUID) |
| B | `block_assignment_id` (UUID) |
| C | `row_hash` (MD5 of person_id + rotations + all day codes) |

Import reads anchors first:
- `person_id` exists → use directly (skip fuzzy matching)
- `row_hash` matches DB → skip entire row (unchanged)
- `row_hash` differs → process row (coordinator changed it)

**Key file:** `TAMCBlockExporter._write_anchor_sheet()` (lines 1059-1101)

### Phase 3: Strict UI Contracts (Data Validation) — DONE

**Goal:** Coordinators select valid codes via Excel dropdowns.

`DataValidation` objects reference Named Ranges from Phase 1:
- Rotation columns → `ValidRotations` dropdown
- Schedule cells → `ValidActivities` dropdown

Import still validates codes (UI layer is redundancy, not replacement).

**Key file:** `TAMCBlockExporter._add_data_validation()` (lines 1014-1040)

### Phase 4: Stateful Leave Overlays — 4a/4b DONE, 4c PENDING

| Sub-phase | Status | What |
|-----------|--------|------|
| 4a | Done | Dynamic `CellIsRule` conditional formatting per activity code from color scheme |
| 4b | Done | `COUNTIF(…,"LV")/2` formula column for leave day counts |
| 4c | Pending | Provenance comments on overridden cells (needs `openpyxl.comments.Comment`) |

**Key files:** `TAMCBlockExporter._add_conditional_formatting()`, `._add_leave_formula_column()`

### Phase Dependencies

```
Phase 1 (metadata) ← Phase 2 (anchoring, uses compute_row_hash)
Phase 1 (named ranges) ← Phase 3 (data validation dropdowns)
Phase 1 + Phase 2 ← Phase 4 (leave overlays + provenance)
```

---

## Schema Hardening

### Track A: Person Academic Years — HIGH PRIORITY (July 1 Deadline)

**Problem:** `Person.pgy_level` is a scalar with no AY scoping. After PGY advancement, historical queries corrupt.

**Solution:** New `person_academic_years` table (person_id x academic_year PK) with AY-scoped `pgy_level`, clinic constraints, call counts.

**Status:**
- Migration exists, Alembic heads merged (PR #1196)
- `_sync_academic_year_call_counts()` implemented (PRs #1199, #1202, #1217)
- 67+ consumers still using `Person.pgy_level` directly — need migration
- `Person.pgy_level` stays deprecated but not dropped (high consumer count)

**Deadline:** July 1, 2026 — PGY advancement is a hard boundary.

### Track C: Leave Single-Source-of-Truth — MEDIUM PRIORITY

**Problem:** Leave exists in 3 places with no sync:
1. `absences` table
2. `block_assignments.leave_days`
3. `half_day_assignments` LV codes

**Solution:** Make `absences` table the sole source. Derive `has_leave` and `leave_days` as `@hybrid_property`. Refresh preloads on CRUD. Import creates absence records from LV codes.

**Three failure patterns prevented:**
1. Orphaned preloads on absence deletion
2. Stale block summary after leave changes
3. Import audit gap (LV codes without absence records)

**Status:** Design complete (Gemini-adjudicated). Not yet implemented.

### Deferred Tracks

- **Track B (Rotation Spans):** 2-column model works. No 3-phase blocks observed. Deferred.
- **Track D (Actual Duty Hours):** AM/PM conservative model is ACGME-safe (6h/slot). Deferred.

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/services/excel_metadata.py` | Shared metadata utilities (write/read/hash) |
| `backend/app/services/tamc_block_exporter.py` | Ground-up exporter (~1200 lines) |
| `backend/app/services/half_day_import_service.py` | Import with anchor/hash support |
| `backend/app/services/import_staging_service.py` | Staging with AY mismatch rejection |
| `backend/app/services/canonical_schedule_export_service.py` | Export orchestration |

---

## Related Documents

- `docs/architecture/excel-stateful-roundtrip-roadmap.md` — Full 622-line roadmap
- `docs/architecture/annual-workbook-architecture.md` — 14-sheet annual workbook vision
- `docs/rag-knowledge/annual-rotation-optimizer.md` — ARO (Track E)
