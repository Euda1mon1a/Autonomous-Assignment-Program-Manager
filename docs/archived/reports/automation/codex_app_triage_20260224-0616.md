# Codex App Automation Triage

- Generated: 2026-02-24 06:16 local
- Inputs:
  - `docs/reports/automation/codex_app_report_20260224-0610.md`
  - `docs/reports/automation/codex_app_plan_20260224-0612.json`
- Scope: sort current Codex macOS automation worktrees into actionable signal vs noise.

## Snapshot

- Worktrees reported: 84
- Worktrees scanned: 161
- All reported worktrees share the same HEAD commit (`e36c5509`).
- Largest noisy duplicate clusters:
  - 35 worktrees with the same 45-file change set (42 signal / 3 noise)
  - 15 worktrees with the same 66-file change set (63 signal / 3 noise)

## Wheat (Actionable First)

These are the highest signal-to-noise worktrees with focused diffs.

1. `/Users/aaronmontgomery/.codex/worktrees/544a/Autonomous-Assignment-Program-Manager`
   - Add tests only:
     - `backend/tests/services/test_upload_processors.py`
     - `frontend/src/__tests__/hooks/useAssignmentsForRange.test.tsx`
   - Recommendation: keep and validate.
2. `/Users/aaronmontgomery/.codex/worktrees/06bc/Autonomous-Assignment-Program-Manager`
   - Add test:
     - `frontend/src/hooks/useScheduleDrafts.test.tsx`
   - Recommendation: keep and validate.
3. `/Users/aaronmontgomery/.codex/worktrees/9ece/Autonomous-Assignment-Program-Manager`
   - Expand hook tests:
     - `frontend/src/__tests__/hooks/useHealth.test.tsx`
   - Recommendation: keep and validate.
4. `/Users/aaronmontgomery/.codex/worktrees/0bd0/Autonomous-Assignment-Program-Manager`
   - Test determinism fix:
     - `backend/tests/unit/test_multi_objective.py` (`np.random.seed(42)`)
   - Recommendation: keep and validate.
5. `/Users/aaronmontgomery/.codex/worktrees/bf0a/Autonomous-Assignment-Program-Manager`
   - Focused typing/runtime-safety cleanup in 5 backend files.
   - Recommendation: keep for targeted review.
6. `/Users/aaronmontgomery/.codex/worktrees/77d0/Autonomous-Assignment-Program-Manager`
   - Type-safety cleanup in test fixtures/async helpers + `useDebounce`.
   - Recommendation: keep for targeted review.
7. `/Users/aaronmontgomery/.codex/worktrees/c0c6/Autonomous-Assignment-Program-Manager`
   - Small typing updates in `token_blacklist` + `useDebounce`.
   - Recommendation: keep for targeted review.
8. `/Users/aaronmontgomery/.codex/worktrees/3e8e/Autonomous-Assignment-Program-Manager`
   - Type robustness adjustments in parser/privacy/profiler/rotation-code paths.
   - Recommendation: keep for targeted review.

## Chaff (Deprioritize / Archive)

1. Duplicate mega-diff cluster (35 worktrees):
   - Same 45-file sweep touching backend/frontend/scripts/docs + scratchpad.
   - Examples: `8d37`, `1060`, `df29`, `a02d`, `604a`.
   - Recommendation: archive/deprioritize as redundant churn.
2. Duplicate mega-diff cluster (15 worktrees):
   - Same 66-file sweep including large docs/ml context churn.
   - Examples: `e01e`, `1ee9`, `3c09`, `a38c`, `b564`.
   - Recommendation: archive/deprioritize as redundant churn.
3. Report-only artifacts (3 worktrees):
   - `async_sync_type_mismatch_report.md` only.
   - Worktrees: `b54f`, `3ae3`, `1e2f`.
   - Recommendation: archive.
4. Generated API type drift only (3 worktrees):
   - `frontend/src/types/api-generated.ts` + `.api-generated.hash`.
   - Worktrees: `c94f`, `3531`, `71c4`.
   - Recommendation: defer unless contract-sync is active.
5. Documentation-wide churn bundles:
   - `ff43`, `b105`, `28ce` mostly doc/stat/link/count updates.
   - Recommendation: defer; promote only if docs refresh is explicitly requested.

## Notes

- The triage tooling currently trims the first status line (`strip()`), which can drop one leading character from the first parsed path in each worktree. This does not change the high-level triage outcome but can slightly affect exact path grouping.

## Next Step Commands

- Inspect one wheat worktree:
  - `git -C /Users/aaronmontgomery/.codex/worktrees/544a/Autonomous-Assignment-Program-Manager status -sb`
  - `git -C /Users/aaronmontgomery/.codex/worktrees/544a/Autonomous-Assignment-Program-Manager diff`
- Repeat for each wheat candidate, then cherry-pick or copy selectively.
