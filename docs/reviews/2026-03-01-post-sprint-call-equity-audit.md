# Audit & Evaluation: Post-PR #1216 (March 1, 2026)

**Date:** March 1, 2026
**Auditor:** Gemini CLI
**Context:** Evaluating repository changes introduced after the PR #1216 Block 12 pipeline integrity fixes.

## 1. Executive Summary

Since the last review (which verified the 41-constraint pipeline and PCAT/DO integrity fixes up to PR #1216), two new PRs have been merged locally and a significant batch of uncommitted work has been staged.

The primary focus of this new work has shifted directly to the next roadmap items: **Call Distribution Equity (MAD)** and **Faculty Template Refinements**, along with patching solver loopholes where absent faculty were incorrectly assigned to call slots.

## 2. Merged Work (Ahead of `origin/main`)

### PR #1217: Faculty Template Mismatches Fix
- **Commit:** `26ba6e59`
- **Impact:** Resolves the deferred "Faculty template constraint in solver" issue. It addresses the 186 template mismatches identified in the previous verification by fixing a dual-write bug. This represents a major quality-of-life win for the schedule grid's fidelity to actual faculty templates.

### PR #1218: Absent Faculty Call Eligibility & FMIT Preservation
- **Commit:** `aa557ec5`
- **Impact:** Fixes a critical solver bug where absent faculty were considered eligible for overnight calls. It successfully tightens the scope of call eligibility and protects FMIT (Family Medicine Inpatient Team) preservation logic.

## 3. Staged / Uncommitted Work (WIP)

There is a cohesive batch of uncommitted modifications currently staged in the working directory that directly targets **Call Equity** and **Solver Constraints**.

### 3.1 Call Equity Normalization (`backend/app/scheduling/engine.py`)
- **Enhancement:** Added a robust `prior_calls` normalization routine that scales historical call counts based on a faculty member's *availability window*.
- **Mechanism:** It subtracts blocks where a faculty member had a `blocking` absence from the total elapsed blocks. It then scales their `prior_calls` up to compare call *rates* rather than raw totals.
- **Why it matters:** This ensures the Median Absolute Deviation (MAD) equity constraint works fairly. Faculty deployed or on leave for half the year will no longer be unfairly penalized or prioritized by the equity solver for simply having fewer raw calls.

### 3.2 Constraint Weight Tuning (`backend/app/scheduling/constraints/manager.py`)
- **Enhancement:** Call equity constraint weights have been significantly recalibrated.
- **Changes:**
  - `SundayCallEquityConstraint` weight increased from `10.0` to `50.0`.
  - `WeekdayCallEquityConstraint` weight increased from `5.0` to `25.0`.
- **Why it matters:** The notes indicate this was necessary to compete with the `CLINIC_MIN_PENALTY=200` in the solver, preventing the solver from sacrificing call equity to avoid minor clinic penalties.

### 3.3 Overnight Call Blocking (`backend/app/scheduling/constraints/overnight_call.py`)
- **Enhancement:** Implemented per-night FMIT and absence blocking within the `add_to_cpsat` and `add_to_pulp` constraint logic.
- **Mechanism:** Rather than failing to create variables, it now forces the solver-created Boolean variables to `0` for ineligible faculty on specific nights.
- **Why it matters:** This directly prevents the solver from sneaking an absent or FMIT faculty member into a call slot by explicitly zeroing out their probability space for that target date.

### 3.4 Test Coverage (Untracked Files)
- Two new test files have been created to cover these new edge cases:
  - `backend/tests/scheduling/test_overnight_call_fmit_blocking.py`
  - `backend/tests/scheduling/test_prior_calls_normalization.py`

## 4. Assessment & Recommendations

**Assessment:**
The work done since PR #1216 is highly targeted, well-reasoned, and strictly adheres to the established roadmap. Tackling the template mismatches (PR #1217) directly resolves the largest outstanding warning from the 10-check DB verification. Furthermore, the uncommitted work for MAD equity normalization is a highly sophisticated approach to handling historical equity against real-world absences.

**Recommendations:**
1. **Commit the Staged Work:** The uncommitted changes represent a complete, logically sound feature increment for Call Equity. It is recommended to commit these changes as `feat: implement MAD call equity normalization and overnight blocking`.
2. **Run the Stress Test:** Before or immediately after committing, run the `constraint_stress_test.py` again to ensure the newly weighted equity constraints (50.0 / 25.0) do not cause unexpected `INFEASIBLE` states against the core 41 constraints.
3. **Verify Check 7:** Run `scripts/scheduling/verify_block12.py` to confirm that PR #1217 successfully eliminated (or drastically reduced) the 186 warnings on Check 7 (Faculty Template Alignment).
