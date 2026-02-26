# Perplexity Computer Integration Roadmap

> **Created:** 2026-02-26 | **Status:** Ready for execution
> **Context:** Perplexity Computer launched 2026-02-25 — cloud-based agentic AI with persistent execution sandbox, 19-model orchestration, async background tasks

## Motivation

AAPM has three categories of work that benefit from autonomous multi-hour execution loops that no current tool provides:

1. **Empirical solver weight optimization** — Running CP-SAT thousands of times to find Pareto-optimal penalty weights (currently hand-tuned)
2. **Adversarial import pipeline testing** — Generating and testing hundreds of corrupted Excel files against the import validators
3. **Continuous regulatory monitoring** — Weekly ACGME/DHA policy scanning mapped to constraint parameters

These tasks require an execution sandbox (install packages, run code, self-correct on errors, iterate for hours) — not just research or code generation.

## OPSEC Boundary

**No identifiable data leaves the local environment.** Perplexity Computer receives only:
- Algorithm code (solver logic, constraint definitions, weight constants)
- Schema definitions (Pydantic models, import/export shapes)
- Enum/constant values (rotation codes, activity codes, validation boundaries)
- Template structure files (column layout, not filled data)

**Never uploaded:** `.env`, `config.py`, database dumps, real schedule exports, resident/faculty names, military-specific identifiers.

---

## Gate 0: Sandbox Compatibility Test

Test whether OR-Tools installs in Perplexity Computer's sandbox:

```
pip install ortools>=9.8,<9.9
python3 -c "from ortools.sat.python import cp_model; m = cp_model.CpModel(); x = m.new_int_var(0,10,'x'); m.maximize(x); s = cp_model.CpSolver(); s.solve(m); print(f'OR-Tools works. x={s.value(x)}')"
```

- **Pass** → Proceed to Prototype 1 (weight tuning)
- **Fail** → Skip to Prototype 2 (Excel fuzzer, only needs openpyxl)

---

## Prototype 1: CP-SAT Weight Sweep

**Goal:** Empirically find Pareto-optimal soft constraint weights by running the solver thousands of times with mutated weights against synthetic data.

**Problem:** AAPM has 25+ hand-tuned penalty weights across two solvers. Small changes in one weight can cascade through others. Manual tuning is slow and unlikely to find global optima.

### Current Weight Configuration

```python
# solvers.py (high-level)
COVERAGE_WEIGHT = 1000
EQUITY_PENALTY_WEIGHT = 10
TEMPLATE_BALANCE_WEIGHT = 5

# activity_solver.py (activity-level, lines 88-129)
FACULTY_CLINIC_SHORTFALL_PENALTY = 10
FACULTY_CLINIC_OVERAGE_PENALTY = 40
FACULTY_GME_SHORTFALL_PENALTY = 15
FACULTY_GME_OVERAGE_PENALTY = 30
OIC_CLINICAL_AVOID_PENALTY = 18
FACULTY_ADMIN_EQUITY_PENALTY = 12
FACULTY_AT_EQUITY_PENALTY = 12
FACULTY_ACADEMIC_EQUITY_PENALTY = 8
RESIDENT_CLINIC_EQUITY_PENALTY = 8
FACULTY_CREDENTIAL_MISMATCH_PENALTY = 15
FACULTY_ADMIN_BONUS = 1
PHYSICAL_CAPACITY_SOFT_PENALTY = 10
ACTIVITY_MIN_SHORTFALL_PENALTY = 10
CLINIC_MIN_SHORTFALL_PENALTY = 25
ACTIVITY_MAX_OVERAGE_PENALTY = 20
CLINIC_MAX_OVERAGE_PENALTY = 40
AT_COVERAGE_SHORTFALL_PENALTY = 50
PROC_VAS_EXTRA_UNITS = 4
SM_ALIGNMENT_SHORTFALL_PENALTY = 30
VAS_ALIGNMENT_SHORTFALL_PENALTY = 30
CV_TARGET_SHORTFALL_PENALTY = 25
CV_DAILY_SPREAD_PENALTY = 6
VAS_OVERRIDE_PENALTY = 8
```

### Files to Upload

| File | Lines | Content |
|------|-------|---------|
| `backend/app/scheduling/solvers.py` | 1-75 + SolverResult | Weight constants + solver architecture |
| `backend/app/scheduling/activity_solver.py` | 1-130 | All 25+ penalty weights |
| `backend/app/scheduling/constraints/config.py` | 55-353 | Priority levels + ACGME weights |
| `backend/app/scheduling/constraints.py` | ConstraintManager class | Constraint system |
| `backend/tests/factories/schedule_factory.py` | All | Synthetic data generation |
| `backend/app/schemas/import_export.py` | All | Input/output shapes |

### Prompt

```
I have a medical residency scheduling system using Google OR-Tools CP-SAT
(>=9.8,<9.9). The solver assigns activities to half-day slots with 25+ soft
constraint penalty weights that were hand-tuned.

TASK:
1. Read uploaded files to understand solver architecture
2. Write a synthetic data generator: 28-day block, 12 residents (PGY 1-3),
   8 faculty, 6 outpatient rotation types
3. Write a test harness that:
   a. Runs the activity solver with current weights
   b. Scores: coverage %, equity (std dev per person), supervision ratio
      breaches, back-to-back call frequency
   c. Mutates weights ±10% per dimension
   d. Runs 2000+ iterations (take as long as needed)
   e. Tracks the Pareto frontier
4. Deliver:
   - Top 5 Pareto-optimal weight configurations
   - Comparison: current vs each candidate
   - Sensitivity analysis: which weights matter most vs inert
   - A Python dict to paste as replacement constants
```

### Expected Output
A replacement weight dictionary with empirical justification, plus sensitivity analysis identifying which weights are load-bearing vs. noise.

### Estimated Credits: 500-1000

---

## Prototype 2: Excel Import Chaos Monkey

**Goal:** Fuzz the Excel import pipeline to find unhandled exceptions (500 errors) that should be clean validation errors (422).

### Files to Upload

| File | Content |
|------|---------|
| `backend/app/services/xlsx_import.py` | Core parser (1944 lines) |
| `backend/app/services/block_assignment_import_service.py` | Block rotation parsing |
| `backend/app/services/half_day_import_service.py` | Half-day import |
| `backend/app/services/upload/validators.py` | File validation |
| `backend/app/core/file_security.py` | Security checks |
| `backend/app/schemas/import_export.py` | Pydantic schemas |
| `backend/app/schemas/block_assignment_import.py` | Block assignment schemas |
| `backend/app/services/preload/constants.py` | Rotation codes (100+ aliases) |
| `backend/data/BlockTemplate2_Official.xlsx` | Template structure |
| `backend/examples/sample-data/Current AY 25-26 SANITIZED.xlsx` | Example input |

### Fuzzing Vectors

```
Structural:    empty sheets, wrong names, missing headers, extra sheets
Data types:    dates as text, floats in int fields, numbers as strings
Codes:         invalid rotations, mixed case, Unicode, specials
Boundaries:    >69 rows, block 0/-1/14/1000, empty imports
Merged cells:  merged across boundaries, None in merged regions
File-level:    corrupted ZIP, MIME mismatch, oversized, path traversal
Duplicates:    same resident+block twice, overlapping assignments
Encoding:      UTF-8 BOM, Latin-1, emoji, 255+ char strings
```

### Prompt

```
Act as a chaos monkey for a medical scheduling Excel import pipeline.

Study the uploaded template and code, then generate 50+ corrupted .xlsx files.
For each, document:
- What was corrupted
- Which code path it exercises (file + function)
- Whether Pydantic catches it [SAFE] or it likely raises unhandled [BUG]

Deliver: categorized report of [SAFE] vs [BUG], corruption recipes for each
[BUG], and recommended defensive code additions.
```

### Expected Output
A prioritized list of unhandled edge cases with exact reproduction recipes for regression tests.

### Estimated Credits: 300-500

---

## Prototype 3: ACGME Regulatory Intelligence Monitor

**Goal:** Weekly detection of ACGME/DHA rule changes mapped to AAPM constraint parameters.

### Files to Upload: None

### Constraint Parameters to Provide

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

### Prompt (Scheduled Weekly)

```
Regulatory intelligence monitor for military FM residency scheduling.

Search weekly: acgme.org (Common Program Requirements, FM Review Committee),
JGME, health.mil (DHA GME policy), aamc.org, CMS Conditions of Participation.

For each finding report:
- SOURCE (URL + date)
- CHANGE (what changed)
- IMPACT (which constraint parameter affected)
- SEVERITY (CRITICAL/HIGH/LOW)
- ACTION (exact parameter change needed)

If no changes: report "No changes detected" with date range and sources checked.
```

### Expected Output
Weekly structured report. Most weeks will be "no changes." When there is a change, it maps directly to a parameter in `backend/app/scheduling/validators/`.

### Estimated Credits: 50-100/week (~400/month)

---

## Prototype 4: Constraint Research Agent

**Goal:** Research OR-Tools best practices and academic scheduling literature for optimization opportunities.

### Files to Upload: Same as Prototype 1

### Prompt

```
Research for a CP-SAT medical scheduling system (OR-Tools 9.8.x):

1. OR-Tools docs, GitHub issues, forums:
   - Soft constraint weight tuning best practices
   - Symmetry breaking for personnel scheduling
   - Search strategy configuration for ~12×56×6×25 problem size

2. Academic literature (2023-2026):
   - "constraint programming medical scheduling"
   - "nurse rostering problem" (closest well-studied analog)
   - "Pareto optimization scheduling constraints"
   - Automated weight tuning for CP solvers

Deliver: Top 5 actionable recommendations with code-level specificity,
expected improvement, risk of regression. All sources cited with URLs.
```

### Estimated Credits: 200-300

---

## Execution Schedule

| Week | Action | Credits |
|------|--------|---------|
| 1, Day 1 | Gate 0: OR-Tools sandbox test | ~5 |
| 1, Day 1 | Prototype 3: Set up ACGME weekly monitor | ~100 |
| 1, Day 2-3 | Prototype 1 (if Gate 0 passes) or Prototype 2 | 500-1000 |
| 2 | Run whichever of 1/2 wasn't done Week 1 | 300-500 |
| 2 | Review first ACGME monitoring report | — |
| 3 | Prototype 4 if weight tuning revealed opportunities | 200-300 |
| 3 | Assessment: worth the $200/mo? | — |

### Steady-State Budget

| Item | Credits/Month |
|------|---------------|
| ACGME weekly monitor | ~400 |
| Quarterly weight re-tuning | ~100 (amortized) |
| Ad-hoc research | ~100-400 |
| **Total** | **~500-900** |

Within 10,000 monthly included credits.

---

## Integration with AAPM Development

### Weight Tuning Results → Code
Optimal weights from Prototype 1 become a PR updating constants in:
- `backend/app/scheduling/solvers.py:69-71`
- `backend/app/scheduling/activity_solver.py:88-129`

### Fuzzer Results → Tests
Each [BUG] from Prototype 2 becomes a regression test in:
- `backend/tests/services/test_xlsx_import.py`
- `backend/tests/services/test_upload_validators.py`

### ACGME Alerts → ADRs
Regulatory changes from Prototype 3 become ADRs in:
- `docs/decisions/ADR-YYYY-MM-DD-acgme-{change}.md`

With corresponding validator updates in:
- `backend/app/scheduling/validators/`

### Research Findings → Solver Config
Recommendations from Prototype 4 inform:
- `backend/app/scheduling/solvers.py` (search strategies, solver parameters)
- `backend/app/scheduling/constraints/config.py` (priority scaling)
