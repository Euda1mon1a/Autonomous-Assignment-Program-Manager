# Full-Stack Residency Scheduler — Combined Audit Report
## AAPM (Autonomous Assignment Program Manager)
### Tripler Army Medical Center, Honolulu, Hawaii

**Audit Date:** February 26, 2026  
**System:** FastAPI + PostgreSQL + OR-Tools CP-SAT 9.8.3296 + Next.js 14  
**Scope:** 6-section audit per Combined Audit Prompt  

---

## Gate 0: OR-Tools Verification

**Status: PASSED**  
OR-Tools 9.8.3296 installed and verified. CP-SAT solver returns OPTIMAL status on test model. Sections 1 and 4 proceed.

---

## Audit Summary Dashboard

| Section | Title | Key Metric | Status |
|---------|-------|-----------|--------|
| 1 | CP-SAT Weight Sweep | 2,100 iterations, 98.6% OPTIMAL | ✅ Complete |
| 2 | Excel Import Chaos Monkey | 65 files tested, 3 BUGs, 12 silent issues | ✅ Complete |
| 3 | ACGME Regulatory Intelligence | 15 findings, 1 CRITICAL code fix | ✅ Complete |
| 4 | Constraint Research | Top 5 recommendations, ~11 dev-days total | ✅ Complete |
| 5 | Full-Stack Security Audit | 35 findings: 10 CRITICAL, 9 HIGH | ✅ Complete |
| 6 | API Contract Audit | 94 routes audited, 65 mismatches found | ✅ Complete |

---

## Critical Action Items (Do First)

| # | Finding | Source | Fix Time |
|---|---------|--------|----------|
| 1 | **41+ endpoints have NO auth guard** — exposes military readiness data, personnel PII, ACGME compliance to anonymous callers | Sec 5 (SEC-001 through SEC-010), Sec 6 | ~2 hours |
| 2 | **Virus scanner permanently disabled** — `_scan_for_viruses()` always returns `{"clean": True}` | Sec 5 (SEC-015) | ~4 hours |
| 3 | **MIN_REST_BETWEEN_SHIFTS=8** is incomplete — missing binding 14-hour post-24hr-call Core requirement (ACGME §6.21.a) | Sec 3 (REC-1) | ~1 hour |
| 4 | **SQL/XSS injection via Excel import** — provider names stored verbatim without sanitization | Sec 2 (BUG-01, BUG-02, BUG-03) | ~2 hours |
| 5 | **Deprecated `num_search_workers`** — replace with `num_workers`, raise to 8, add `num_violation_ls=1` | Sec 4 (Rec 1) | ~2 hours |
| 6 | **ExportJobStatsResponse camelCase mismatch** — constructor uses camelCase kwargs breaking contract | Sec 6 (P0) | ~30 min |

---

## Section 1: CP-SAT Weight Sweep

**Full report:** `section1_output/section1_report.md`  
**Raw data:** `section1_output/section1_results.csv` (2,100 rows)  
**Code:** `section1_output/section1_sweep_harness.py`, `section1_output/section1_synthetic_data.py`

### Key Findings

- **2,100 configurations** evaluated via Latin Hypercube Sampling over 6-dimensional weight space
- **98.6% OPTIMAL** solve rate, average 1.06s per run
- **All solved runs achieved 100% coverage** — the problem is not over-constrained at 12-resident scale
- **Current weights (1000/10/5) are within the optimal range** — no urgent changes needed
- **COVERAGE_WEIGHT is a scale parameter**, not a quality driver (Spearman ρ = +0.988 with objective magnitude, ≈0 with quality metrics)
- **Template balance is structurally enforced** by hard constraints, making the soft weight nearly irrelevant

### Top 5 Configurations

| Rank | COVERAGE_W | EQUITY_PEN_W | TEMPLATE_BAL_W | Equity Score | Solve Time |
|------|-----------|-------------|----------------|-------------|-----------|
| 1 | 750 | 1 | 15 | 6.0 (best) | 0.91s |
| 2 | 1000 | 50 | 20 | 6.0 (best) | 1.04s |
| 3 | 1500 | 10 | 10 | 6.0 (best) | 1.08s |
| 4 | 100 | 20 | 25 | 6.0 (best) | 0.81s |
| 5 | 250 | 35 | 1 | 6.0 (best) | 0.70s |

### Recommendation
Optionally reduce COVERAGE_WEIGHT to 500-750 and raise EQUITY_PENALTY_WEIGHT to 35 for ~10pp improvement in P(equity ≤ 7). Scale-up beyond 12 residents will require a targeted re-sweep.

---

## Section 2: Excel Import Chaos Monkey

**Full report:** `section2_output/section2_report.md`  
**Test files:** `section2_output/section2_corrupted_files/` (65 .xlsx files)  
**Results:** `section2_output/section2_results.csv`

### Results Summary

| Classification | Count |
|---------------|-------|
| [SAFE] | 62 |
| [BUG] | 3 |
| Silent wrong-output | 12+ |
| Crashes | 0 |
| Timeouts | 0 |

### 3 Confirmed Bugs

| Bug | File | Severity | Issue |
|-----|------|----------|-------|
| BUG-01 | D01_sql_injection.xlsx | HIGH | SQL injection strings stored verbatim as provider names |
| BUG-02 | D02_xss_injection.xlsx | HIGH | XSS `<script>` payloads stored verbatim |
| BUG-03 | D03_path_traversal.xlsx | MEDIUM | Path traversal strings `../../etc/passwd` stored verbatim |

### Top Silent Issues

1. **Date scan capped at 15 columns** — schedules >15 date columns silently truncated (xlsx_import.py:439)
2. **Duplicate providers silently overwritten** — last-write-wins with no warning
3. **Formula cells read as empty** → classified as OFF with no warning
4. **No length limits** on provider names or slot values (32KB+ strings accepted)

### 10 Hardening Recommendations (R1-R10)
See full report for code-level fixes including input sanitization, date range validation, duplicate detection, and length limits.

---

## Section 3: ACGME Regulatory Intelligence Monitor

**Full report:** `section3_output/section3_report.md`  
**Sources cited:** 24 URLs from ACGME, DHA, ABFM, CMS, JGME

### Findings Summary

| Risk Level | Count | Key Items |
|-----------|-------|-----------|
| CRITICAL | 1 | MIN_REST incomplete — missing 14-hr post-call Core rule |
| HIGH | 3 | Telehealth supervision codified; CPR Interim Revision July 2026; CPR Major Revision targeting 2028 |
| MEDIUM | 6 | FM patient panel tracking, CLER 3.0, ABFM 15 competencies, institutional requirements |
| LOW | 5 | Core CEWH params confirmed stable, DoD 6000.13 unchanged |

### Immediate Code Fix Required

```python
# Current (INSUFFICIENT)
MIN_REST_BETWEEN_SHIFTS = 8  # hours

# Required — add binding Core requirement
MIN_REST_BETWEEN_SHIFTS = 8        # hours (Detail, aspirational)
MIN_REST_AFTER_24HR_CALL = 14      # hours (Core, binding — ACGME §6.21.a)
```

### All Core CEWH Parameters Confirmed Compliant
MAX_WEEKLY_HOURS=80, MAX_CONSECUTIVE_DAYS=6, PGY1/PGY2-3 supervision ratios, 1-in-7 rule, moonlighting prohibition — all confirmed unchanged through at least July 2028.

### New: Telehealth Supervision (HIGH)
ACGME codified direct supervision via telecommunication (effective July 2025). Scheduler needs a `supervision_modality` field to distinguish physical vs. telehealth direct supervision.

---

## Section 4: Constraint Research — Top 5 Recommendations

**Full report:** `section4_output/section4_report.md` (818 lines, 47KB)  
**Research base:** 5 prior research files (195KB total)

### Top 5 Recommendations

| # | Title | Priority | Effort | Expected Improvement |
|---|-------|----------|--------|---------------------|
| 1 | Replace deprecated `num_search_workers` → `num_workers`, raise to 8, add `num_violation_ls=1` | P0 | 2 hours | 20-40% faster solve |
| 2 | Add Phase-1→Phase-2 solution hints (warm-start) | P0 | 4 hours | 30-60% faster first-feasible |
| 3 | Replace `max_template_count` with per-template block-level sum constraints | P1 | 1 day | 15-30% tighter LP relaxation |
| 4 | Upgrade equity penalty from range to MAD using `add_abs_equality` | P1 | 1 day | 35-50% reduction in equity variance |
| 5 | Integrate SMAC3 Bayesian weight tuning | P2 | 3 days | 10-25% composite objective improvement |

### Implementation Roadmap (~11 developer-days)
- Week 1, Day 1: Rec 1 (deprecation fix, 2h)
- Week 1, Days 2-3: Rec 2 (warm-start hints, 4h)
- Week 2, Day 1: Rec 3 (block-level sum constraints, 1d)
- Week 2, Day 2: Rec 4 (MAD equity penalty, 1d)
- Weeks 3-4: Rec 5 (SMAC3 tuner, 3d)

---

## Section 5: Full-Stack Security Audit

**Full report:** `section5_output/section5_report.md` (1,257 lines, 61KB)

### Findings by Severity

| Severity | Count | Examples |
|----------|-------|---------|
| CRITICAL | 10 | 41+ endpoints missing auth, unauthenticated file upload, schedule data exposed |
| HIGH | 9 | Virus scanner disabled, admin password in response, solver DoS vectors |
| MEDIUM | 10 | Cookie hardening, error leakage, missing security headers, solver timeout abuse |
| LOW | 6 | Audit trail quality, schema coupling, predictable bootstrap credentials |

### Most Severe: Authentication Failures

- **resilience.py:** 41 of ~60 endpoints have NO auth guard — exposes Iron Dome status, DRRS ratings, N-1/N-2 vulnerability matrices, MTF readiness data
- **imports.py:** Both file-upload endpoints completely unauthenticated
- **schedule.py:** `GET /validate` and `GET /{start_date}/{end_date}` exposed anonymously with full PII
- **auth.py:** `initialize-admin` returns password in response body (DEBUG-gated)

### 11 Quick Wins (~2 hours total)
The full report includes 11 copy-pasteable fixes that address 22 of 35 findings.

---

## Section 6: API Contract Audit

**Full report:** `section6_output/section6_report.md` (561 lines, 48KB)

### Route Inventory: 94 Endpoints Audited

| File | Routes | Missing Auth | Missing Rate Limit | Missing response_model |
|------|--------|-------------|-------------------|----------------------|
| auth.py | 8 | 3 (public by design) | 4 | 2 |
| imports.py | 2 | **2** | 2 | 1 |
| exports.py | 10 | 0 | 8 | 0 |
| schedule.py | 20 | **4** | 15 | 5 |
| resilience.py | 54 | **41** | 50+ | 30+ |

### Contract Mismatches

| Issue Type | Count | Priority |
|-----------|-------|----------|
| Missing authentication on data-bearing endpoints | 6 | P0 |
| camelCase constructor mismatch (ExportJobStatsResponse) | 1 | P0 |
| JSONResponse bypasses response_model validation | 9 | P1 |
| No response_model declared | 8 | P1 |
| Raw dict returns bypass Pydantic serialization | 4 | P1 |
| Missing rate limits on mutation endpoints | 22 | P2 |
| Inconsistent error response shapes | 7 | P3 |

### Confirmed Known Issues

1. **exports.py:507-517** — ExportJobStatsResponse uses camelCase kwargs (`totalJobs`, `activeJobs`) — CONFIRMED contract mismatch
2. **imports.py parse_xlsx** — NO auth guard — CONFIRMED
3. **schedule.py GET /validate** — NO auth guard — CONFIRMED
4. **resilience.py GET /health** — NO auth guard — CONFIRMED

---

## Cross-Section Overlap Analysis

Several findings appear across multiple sections, confirming their importance:

| Finding | Sections |
|---------|----------|
| Missing auth guards on imports/schedule/resilience endpoints | Sec 5 + Sec 6 |
| Input sanitization for Excel import pipeline | Sec 2 + Sec 5 |
| Deprecated `num_search_workers` parameter | Sec 1 + Sec 4 |
| Telehealth supervision gap | Sec 3 (regulatory) |
| ExportJobStatsResponse camelCase | Sec 5 + Sec 6 |
| Weight tuning at current scale shows no trade-offs | Sec 1 + Sec 4 |

---

## Consolidated Priority Matrix

### P0 — Block Deployment (Fix This Week)
1. Add auth guards to ALL unguarded endpoints (~47 endpoints)
2. Add MIN_REST_AFTER_24HR_CALL = 14 hours
3. Add input sanitization for Excel import provider names
4. Enable real virus scanning
5. Fix ExportJobStatsResponse camelCase keys
6. Replace deprecated `num_search_workers`

### P1 — Fix Within 30 Days
7. Add rate limits to all mutation/compute endpoints
8. Declare response_model on all endpoints returning structured data
9. Add telehealth supervision modality field
10. Add Phase-1→Phase-2 warm-start hints
11. Replace max_template_count with block-level sum constraints
12. Upgrade equity penalty to MAD formulation
13. Increase date scan column limit in xlsx_import.py
14. Add duplicate provider detection

### P2 — Fix Within 90 Days
15. Integrate SMAC3 Bayesian weight tuning
16. Add FM patient panel continuity tracking
17. Add GMEC compliance reporting module
18. Externalize all hardcoded ACGME parameters to config
19. Add work compression/intensity monitoring

### P3 — Monitor / Backlog
20. Monitor ACGME CPR Major Revision (July 2028 target)
21. Prepare for July 2026 FM-specific CPR modifications
22. ABFM 15-competency coverage tracking
23. Standardize error response format across all endpoints

---

## Artifacts Delivered

| Section | Files | Location |
|---------|-------|----------|
| 1 | sweep_harness.py, synthetic_data.py, results.csv (2,100 rows), report.md | `section1_output/` |
| 2 | chaos_generator.py, test_harness.py, 65 corrupted .xlsx files, results.csv, report.md | `section2_output/` |
| 3 | report.md (15 findings, 24 source URLs, quarterly monitoring schedule) | `section3_output/` |
| 4 | report.md (Top 5 recommendations with code-level specificity, cross-reference matrix) | `section4_output/` |
| 5 | report.md (35 findings, remediation matrix, 11 quick wins) | `section5_output/` |
| 6 | report.md (94-route inventory, contract mismatches table, auth audit) | `section6_output/` |

---

*Report compiled February 26, 2026. All section reports available in workspace directories.*
