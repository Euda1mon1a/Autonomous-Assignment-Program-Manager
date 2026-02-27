# Annual Leap — Perplexity Computer Upload

**Purpose:** Research the transformation from 13 independent block schedulers into a coherent annual program manager.

**Why this matters:** This is the single highest-yield architectural change for the entire project. It transforms a "scheduling tool" into "the thing that runs the residency program."

## Upload Contents

### Models (5 files, ~29KB)
| File | Original Path | Size |
|------|--------------|------|
| `person.py` | `backend/app/models/person.py` | 12KB |
| `person_academic_year.py` | `backend/app/models/person_academic_year.py` | 2KB |
| `block_assignment.py` | `backend/app/models/block_assignment.py` | 7KB |
| `absence.py` | `backend/app/models/absence.py` | 6KB |
| `call_assignment.py` | `backend/app/models/call_assignment.py` | 2KB |

### Scheduling (1 file, ~25KB)
| File | Original Path | Size |
|------|--------------|------|
| `acgme_compliance_engine.py` | `backend/app/scheduling/acgme_compliance_engine.py` | 25KB |

### Constraints (6 files, ~193KB)
| File | Original Path | Size |
|------|--------------|------|
| `call_equity.py` | `backend/app/scheduling/constraints/call_equity.py` | 57KB |
| `acgme.py` | `backend/app/scheduling/constraints/acgme.py` | 40KB |
| `manager.py` | `backend/app/scheduling/constraints/manager.py` | 25KB |
| `config.py` | `backend/app/scheduling/constraints/config.py` | 22KB |
| `base.py` | `backend/app/scheduling/constraints/base.py` | 18KB |
| `equity.py` | `backend/app/scheduling/constraints/equity.py` | 11KB |

### Services (3 files, ~63KB)
| File | Original Path | Size |
|------|--------------|------|
| `half_day_import_service.py` | `backend/app/services/half_day_import_service.py` | 44KB |
| `canonical_schedule_export_service.py` | `backend/app/services/canonical_schedule_export_service.py` | 15KB |
| `longitudinal_validator.py` | `backend/app/services/longitudinal_validator.py` | 4KB |

### Routes (1 file, ~15KB)
| File | Original Path | Size |
|------|--------------|------|
| `admin_block_assignments.py` | `backend/app/api/routes/admin_block_assignments.py` | 15KB |

### Architecture Docs (3 files, ~57KB)
| File | Original Path | Size |
|------|--------------|------|
| `FACULTY_FIX_ROADMAP.md` | `docs/architecture/FACULTY_FIX_ROADMAP.md` | 15KB |
| `excel-stateful-roundtrip-roadmap.md` | `docs/architecture/excel-stateful-roundtrip-roadmap.md` | 27KB |
| `annual-workbook-architecture.md` | `docs/architecture/annual-workbook-architecture.md` | 15KB |

## Research Sections (6)

1. **Longitudinal ACGME Validation** — Cross-block compliance patterns, 1-in-7 sliding window
2. **Academic Year Rollover** — PGY tracking, July 1 graduation, historical data preservation
3. **Cross-Block Equity Optimization** — CP-SAT techniques for longitudinal call equity
4. **Leave Continuity** — Absence management across planning period boundaries
5. **Annual Workbook Design** — Excel multi-period aggregation patterns
6. **Implementation Roadmap** — Dependency graph, risk register, testing strategy

## Total Package
- **19 source files + 2 docs** (PROMPT.md, README.md)
- **~380KB** total
- **Not included:** `engine.py` (170KB, too large) — referenced in prompt for context

## The Five Components Being Researched

| # | Component | Current Status | Key Question |
|---|-----------|---------------|--------------|
| 1 | `person_academic_years` migration | 60% — model exists, migration missing | How to seed without data loss? |
| 2 | Faculty call equity YTD | 70% — architecture designed | How to inject history into CP-SAT? |
| 3 | Cross-block leave continuity | 30% — basic absence CRUD exists | How to sync across boundaries? |
| 4 | Cross-block 1-in-7 boundary | 50% — per-block works | Sliding window algorithm? |
| 5 | Annual workbook YTD_SUMMARY | 40% — export infra exists | Cross-sheet formula patterns? |
