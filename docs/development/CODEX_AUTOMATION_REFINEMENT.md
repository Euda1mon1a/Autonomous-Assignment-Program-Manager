# Codex Automation Refinement Plan

Date: 2026-02-13  
Scope: Codex macOS automation outputs for this repository

## Executive summary

Current Codex automations produce useful signal, but too much mixed/noisy output lands in triage. The highest-yield path is to standardize backend env preflight, tighten prompt scopes, and enforce a deterministic wheat/chaff merge policy.

## Wheat to standardize

1. Async session correctness fixes
- Example harvested: `backend/app/api/routes/resident_weekly_requirements.py` (`await db.delete(...)` in async routes).
- Refinement: keep "Missing Await Detector" as a daily automation and require file:line fix evidence.

2. Hook tests aligned to current implementation
- Example harvested: `frontend/__tests__/hooks/useClaudeChat.test.tsx` replacing stale skipped tests.
- Refinement: prefer tests that validate current websocket/session behavior over legacy API assumptions.

3. Service-level backend coverage additions
- Example harvested: `backend/tests/services/test_faculty_assignment_expansion_service.py`.
- Refinement: mixed outputs are acceptable when they add unique backend behavioral coverage and avoid redundant frontend test duplication.

## Chaff patterns to suppress

1. Broad docs/style churn without behavior changes.
2. Large cross-cutting backend edits with mixed semantics and low verification.
3. Duplicate frontend hook tests that overlap existing test suites.
4. Worktree-only analysis artifacts presented as code changes.

## Automation prompt refinements

1. Add mandatory env preflight for all backend commands run in Codex worktrees.
- Required wrapper: `python3 .codex/scripts/codex_worktree_env_exec.py -- <backend command>`

2. Require "minimal-scope edits" in prompts.
- Constrain each run to one subsystem (for example: one route file + matching tests).

3. Require "dedupe check" before adding new tests.
- Search existing test locations first; only add tests for uncovered behavior.

4. Require "proof block" in output.
- Include changed files, focused test command, pass/fail status, and unresolved risks.

## Merge policy for future triage

1. Auto-accept
- Single-purpose runtime correctness fixes with targeted tests.

2. Selective salvage
- Mixed bundles where at least one file adds unique coverage or low-risk type hygiene.

3. Auto-archive
- Multi-domain churn lacking focused validation.

## PII and secret safety controls

1. Never commit `.env`, `.env.*`, tokens, database credentials, or copied command outputs containing secrets.
2. Run a secrets/PII grep on staged diffs before commit.
3. Reject automation outputs that embed runtime env values in markdown or tests.

## Operational checklist

1. Generate report: `python3 .codex/scripts/codex_automation_report.py`
2. Generate plan: `python3 .codex/scripts/codex_automation_triage.py --plan`
3. Harvest only wheat + selective mixed wheat.
4. Validate with focused tests.
5. Run PII/secrets scan on staged files.
6. Commit and open PR with explicit wheat/chaff rationale.
