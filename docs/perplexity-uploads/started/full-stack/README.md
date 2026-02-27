# Full-Stack Perplexity Computer Upload

Combined upload folder for Perplexity Computer sessions. Contains deduplicated source files covering the full stack — scheduling solver, import/export pipeline, security, API routes, and frontend contract surface.

## Usage

1. Upload all files from this folder to Perplexity Computer
2. Paste the contents of `PROMPT.md` as the session prompt
3. Perplexity Computer will work through 6 sections (Gate 0 + 5 audit tracks)

## File Manifest

| Upload Path | Original Source Path | Size |
|-------------|---------------------|------|
| **core/** | | |
| `core/main.py` | `backend/app/main.py` | 18K |
| `core/config.py` | `backend/app/core/config.py` | 24K |
| `core/security.py` | `backend/app/core/security.py` | 16K |
| `core/file_security.py` | `backend/app/core/file_security.py` | 11K |
| **scheduling/** | | |
| `scheduling/solvers.py` | `backend/app/scheduling/solvers.py` | 96K |
| `scheduling/activity_solver.py` | `backend/app/scheduling/activity_solver.py` | 152K |
| `scheduling/constraints_config.py` | `backend/app/scheduling/constraints/config.py` | 22K |
| **services/** | | |
| `services/xlsx_import.py` | `backend/app/services/xlsx_import.py` | 68K |
| `services/half_day_import_service.py` | `backend/app/services/half_day_import_service.py` | 44K |
| `services/xml_to_xlsx_converter.py` | `backend/app/services/xml_to_xlsx_converter.py` | 58K |
| `services/upload_validators.py` | `backend/app/services/upload/validators.py` | 12K |
| `services/preload_constants.py` | `backend/app/services/preload/constants.py` | 3K |
| **schemas/** | | |
| `schemas/import_export.py` | `backend/app/schemas/import_export.py` | 8K |
| `schemas/block_assignment_import.py` | `backend/app/schemas/block_assignment_import.py` | 12K |
| **routes/** | | |
| `routes/auth.py` | `backend/app/api/routes/auth.py` | 14K |
| `routes/schedule.py` | `backend/app/api/routes/schedule.py` | 61K |
| `routes/imports.py` | `backend/app/api/routes/imports.py` | 13K |
| `routes/resilience.py` | `backend/app/api/routes/resilience.py` | 114K |
| `routes/exports.py` | `backend/app/api/routes/exports.py` | 17K |
| **frontend/** | | |
| `frontend/api.ts` | `frontend/src/lib/api.ts` | 15K |
| `frontend/auth.ts` | `frontend/src/lib/auth.ts` | 19K |
| **testing/** | | |
| `testing/schedule_factory.py` | `backend/tests/factories/schedule_factory.py` | 15K |
| **templates/** | | |
| `templates/BlockTemplate2_Official.xlsx` | `backend/data/BlockTemplate2_Official.xlsx` | 16K |
| `templates/Current AY 25-26 SANITIZED.xlsx` | `backend/examples/sample-data/Current AY 25-26 SANITIZED.xlsx` | 104K |

## Sections Covered

| # | Section | Original Prototype | New? |
|---|---------|-------------------|------|
| 0 | Gate 0: OR-Tools test | `gate0/` | No |
| 1 | CP-SAT Weight Sweep | `prototype1-weight-sweep/` | No |
| 2 | Excel Import Chaos Monkey | `prototype2-excel-fuzzer/` | No |
| 3 | ACGME Regulatory Monitor | `prototype3-acgme-monitor/` | No |
| 4 | Constraint Research | `prototype4-constraint-research/` | No |
| 5 | Full-Stack Security Audit | — | **Yes** |
| 6 | API Contract Audit | — | **Yes** |

## Notes

- This folder is gitignored — it contains copies of source files, not originals
- No PII: all files are source code or sanitized templates
- Total size: ~900KB (within Perplexity Computer upload limits)
- Replaces the 4 separate prototype folders that had duplicated files
