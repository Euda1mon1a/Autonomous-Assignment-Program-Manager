# Full-Stack Residency Scheduler — Combined Audit Prompt

Upload all files from this folder, then paste the prompt below.

---

## System Overview

Military Family Medicine residency scheduling system. Tech stack:
- **Backend:** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Celery
- **Frontend:** Next.js 14 (App Router) + TypeScript + TailwindCSS
- **Solver:** Google OR-Tools CP-SAT (>=9.8,<9.9) with 25+ soft constraint penalty weights
- **Security context:** Military medical data — OPSEC/PERSEC critical. All uploaded files are source code only, no PII.

**Uploaded file layout:**
- `core/` — App init, config, security, file upload security
- `scheduling/` — CP-SAT solver, activity solver (25+ weights), constraint priority config
- `services/` — Excel import pipeline, export converter, upload validators, rotation constants
- `schemas/` — Pydantic validation models for import/export
- `routes/` — FastAPI API endpoints (auth, schedule, imports, exports, resilience)
- `frontend/` — Axios interceptors (snake↔camel conversion), JWT auth + token refresh
- `testing/` — Synthetic schedule data factory
- `templates/` — Excel template + sanitized example workbook

---

## Gate 0: OR-Tools Sandbox Test

```
pip install ortools>=9.8,<9.9
python3 -c "from ortools.sat.python import cp_model; m = cp_model.CpModel(); x = m.new_int_var(0,10,'x'); m.maximize(x); s = cp_model.CpSolver(); s.solve(m); print(f'OR-Tools works. x={s.value(x)}')"
```

- **Pass** → Proceed to all sections
- **Fail** → Skip Sections 1 & 4 (they need OR-Tools), do the rest

---

## Section 1: CP-SAT Weight Sweep

**Files:** `scheduling/solvers.py`, `scheduling/activity_solver.py`, `scheduling/constraints_config.py`, `testing/schedule_factory.py`, `schemas/import_export.py`

I have a medical residency scheduling system using Google OR-Tools CP-SAT (>=9.8,<9.9). The solver assigns activities to half-day slots with 25+ soft constraint penalty weights that were hand-tuned.

TASK:
1. Read uploaded files to understand solver architecture
2. Write a synthetic data generator: 28-day block, 12 residents (PGY 1-3), 8 faculty, 6 outpatient rotation types
3. Write a test harness that:
   a. Runs the activity solver with current weights
   b. Scores: coverage %, equity (std dev per person), supervision ratio breaches, back-to-back call frequency
   c. Mutates weights ±10% per dimension
   d. Runs 2000+ iterations (take as long as needed)
   e. Tracks the Pareto frontier
4. Deliver:
   - Top 5 Pareto-optimal weight configurations
   - Comparison: current vs each candidate
   - Sensitivity analysis: which weights matter most vs inert
   - A Python dict to paste as replacement constants

---

## Section 2: Excel Import Chaos Monkey

**Files:** `services/xlsx_import.py`, `services/half_day_import_service.py`, `services/upload_validators.py`, `core/file_security.py`, `schemas/import_export.py`, `schemas/block_assignment_import.py`, `services/preload_constants.py`, `templates/BlockTemplate2_Official.xlsx`, `templates/Current AY 25-26 SANITIZED.xlsx`

Act as a chaos monkey for a medical scheduling Excel import pipeline.

Study the uploaded template and code, then generate 50+ corrupted .xlsx files. For each, document:
- What was corrupted
- Which code path it exercises (file + function)
- Whether Pydantic catches it [SAFE] or it likely raises unhandled [BUG]

Fuzzing vectors to cover:
- Structural:    empty sheets, wrong names, missing headers, extra sheets
- Data types:    dates as text, floats in int fields, numbers as strings
- Codes:         invalid rotations, mixed case, Unicode, specials
- Boundaries:    >69 rows, block 0/-1/14/1000, empty imports
- Merged cells:  merged across boundaries, None in merged regions
- File-level:    corrupted ZIP, MIME mismatch, oversized, path traversal
- Duplicates:    same resident+block twice, overlapping assignments
- Encoding:      UTF-8 BOM, Latin-1, emoji, 255+ char strings

Deliver: categorized report of [SAFE] vs [BUG], corruption recipes for each [BUG], and recommended defensive code additions.

---

## Section 3: ACGME Regulatory Intelligence Monitor

**Files:** None required (uses inline constants below)

Regulatory intelligence monitor for military FM residency scheduling.

Current constraint parameters:
```
MAX_WEEKLY_HOURS = 80 (rolling 4-week average)
MAX_CONTINUOUS_DUTY = 28 hours (24+4)
MIN_REST_BETWEEN_DUTY = 10 hours
MAX_CONSECUTIVE_DAYS = 6 (1-in-7 rule)
HOURS_PER_HALF_DAY = 6
PGY1_SUPERVISION_RATIO = 1:2
PGY2_3_SUPERVISION_RATIO = 1:4
CALL_FREQUENCY = every-3rd-night (~10/28 days)
MAX_CONSECUTIVE_NIGHTS = 2
MIN_CALL_SPACING = 2 days
MIN_ROTATION_LENGTH = 7 days
POST_DEPLOYMENT_RECOVERY = 7 days
```

Search weekly: acgme.org (Common Program Requirements, FM Review Committee), JGME, health.mil (DHA GME policy), aamc.org, CMS Conditions of Participation.

For each finding report:
- SOURCE (URL + date)
- CHANGE (what changed)
- IMPACT (which constraint parameter affected)
- SEVERITY (CRITICAL/HIGH/LOW)
- ACTION (exact parameter change needed)

If no changes: report "No changes detected" with date range and sources checked.

---

## Section 4: Constraint Research

**Files:** Same as Section 1

Research for a CP-SAT medical scheduling system (OR-Tools 9.8.x):

1. OR-Tools docs, GitHub issues, forums:
   - Soft constraint weight tuning best practices
   - Symmetry breaking for personnel scheduling
   - Search strategy configuration for ~12x56x6x25 problem size

2. Academic literature (2023-2026):
   - "constraint programming medical scheduling"
   - "nurse rostering problem" (closest well-studied analog)
   - "Pareto optimization scheduling constraints"
   - Automated weight tuning for CP solvers

Deliver: Top 5 actionable recommendations with code-level specificity, expected improvement, risk of regression. All sources cited with URLs.

---

## Section 5: Full-Stack Security Audit

**Files:** `core/main.py`, `core/security.py`, `core/config.py`, `core/file_security.py`, `frontend/api.ts`, `frontend/auth.ts`, `routes/auth.py`

Review the following attack surfaces:

1. **Middleware stack** (`main.py`): Review CORS config, error handlers, trusted host middleware for OWASP Top 10 compliance. Check for information leakage in error responses.

2. **JWT implementation** (`security.py`): Check for timing attacks in token validation, token reuse/replay, secret rotation gaps, bcrypt cost factor adequacy.

3. **Config & secrets** (`config.py`): Verify secret validation completeness — are there any settings that should be secrets but aren't validated? Check for default values that could be exploited.

4. **File upload security** (`file_security.py`): Test for path traversal, ZIP bombs, MIME type confusion, symlink attacks, filename injection.

5. **Axios interceptors** (`api.ts`): Check if snake↔camelCase conversion could introduce XSS vectors. Review error handling for credential leaks.

6. **Token refresh** (`auth.ts`): Check for race conditions in concurrent refresh, token storage security, refresh token rotation.

7. **Auth routes** (`routes/auth.py`): Review login/logout/refresh for rate limiting, enumeration attacks, session fixation.

Deliver: Prioritized findings by severity (CRITICAL/HIGH/MEDIUM/LOW) with specific file:line references and recommended fixes.

---

## Section 6: API Contract Audit

**Files:** `routes/*.py`, `schemas/*.py`, `frontend/api.ts`

1. Compare route definitions with Pydantic schemas — are there endpoints accepting unvalidated input?
2. Check for missing auth guards (`Depends(get_current_user)`) on sensitive endpoints
3. Check for inconsistent error response shapes across routes
4. Verify snake_case↔camelCase contract alignment:
   - Backend routes return snake_case keys
   - Frontend `api.ts` interceptor converts to camelCase
   - URL query params must stay snake_case (interceptor doesn't touch URLs)
   - Enum values must stay snake_case (interceptor only converts keys, not values)
5. Check for endpoints that return raw SQLAlchemy models instead of Pydantic schemas

Deliver: Contract mismatches table with route, expected schema, actual response shape, and fix priority.
