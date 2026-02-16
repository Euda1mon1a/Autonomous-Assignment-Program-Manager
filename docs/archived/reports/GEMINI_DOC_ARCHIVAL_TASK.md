# Task: Doc Archival — Batch File Moves

**Assigned to:** Gemini CLI
**Date:** 2026-02-15
**Type:** Mechanical file moves (`git mv`) — no content editing
**PR target:** `main`
**Branch name:** `chore/doc-archival-sweep`

---

## Mission

Move ~81 stale session summaries, one-time implementation reports, and old automation logs from active directories to `docs/archived/`. This is purely mechanical — no content changes, no code changes, just `git mv` operations.

## Pre-flight

```bash
git checkout main && git pull origin main
git checkout -b chore/doc-archival-sweep
```

Verify clean working tree before starting:
```bash
git status --porcelain  # Must be empty
```

---

## Part 1: Root-level session summaries → `docs/archived/sessions/`

The `docs/archived/sessions/` directory already exists.

```bash
git mv SESSION_40_SUMMARY.md docs/archived/sessions/
git mv SESSION_44_COMPLETE.md docs/archived/sessions/
git mv SESSION_45_TRANSACTION_LOCKING_FIXES.md docs/archived/sessions/
git mv SESSION_48_SUMMARY.md docs/archived/sessions/
git mv BURN_SESSION_36_SUMMARY.md docs/archived/sessions/
git mv SECURITY_AUDIT_SESSION_48.md docs/archived/sessions/
```

## Part 2: Root-level implementation reports → `docs/archived/reports/`

The `docs/archived/reports/` directory already exists.

```bash
git mv ADMIN_TESTS_SUMMARY.md docs/archived/reports/
git mv BUILD_QUALITY_SUMMARY.md docs/archived/reports/
git mv CONCURRENT_TESTS_IMPLEMENTATION_SUMMARY.md docs/archived/reports/
git mv CONSTRAINT_REGISTRATION_REPORT.md docs/archived/reports/
git mv CONSTRAINT_SYSTEM_RE_ENABLE_REPORT.md docs/archived/reports/
git mv IMPLEMENTATION_SUMMARY_TIME_CRYSTAL.md docs/archived/reports/
git mv INTEGRATION_TESTS_SUMMARY.md docs/archived/reports/
git mv KEYSTONE_IMPLEMENTATION_SUMMARY.md docs/archived/reports/
git mv LOTKA_VOLTERRA_IMPLEMENTATION_SUMMARY.md docs/archived/reports/
git mv NOTIFICATION_SYSTEM_SUMMARY.md docs/archived/reports/
git mv PERFORMANCE_OPTIMIZATION_SUMMARY.md docs/archived/reports/
git mv TASK_COMPLETION_SUMMARY.md docs/archived/reports/
git mv TEST_COVERAGE_REPORT.md docs/archived/reports/
git mv LOCAL_FILE_CLEANUP_REPORT.md docs/archived/reports/
git mv REPO_AUDIT_REPORT.md docs/archived/reports/
git mv AUTH_TEST_GAP_MANIFEST.md docs/archived/reports/
git mv SECURITY_TEST_COVERAGE_REPORT.md docs/archived/reports/
git mv SECURITY_TEST_VULNERABILITY_BREAKDOWN.md docs/archived/reports/
git mv SKIPPED_TESTS_MANIFEST.md docs/archived/reports/
git mv SKIPPED_TESTS_QUICK_REFERENCE.md docs/archived/reports/
git mv PHASE_1_INTEGRATION_SPEC.md docs/archived/reports/
git mv REPO_HYGIENE_PRIORITIES.md docs/archived/reports/
git mv DOCSTRING_IMPROVEMENTS.md docs/archived/reports/
```

## Part 3: Old automation reports → `docs/archived/reports/automation/`

Create the target directory first:
```bash
mkdir -p docs/archived/reports/automation
```

Move all automation reports dated **before 2026-02-10** (43 files). These are the files with timestamps `20260204` through `20260208` in their filenames:

```bash
git mv docs/reports/automation/codex_app_report_20260204-0344.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_app_report_20260205-2131.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_app_report_20260205-2133.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_app_report_20260205-2202.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_bad1_final_salvage_20260205-2247.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2151.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2152.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2153.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2157.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2158.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2213.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2214.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2215.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2216.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2217.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_hunter_20260205-2246.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_cherry_pick_salience_20260205-2206.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_daily_health_20260205-2213.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_daily_health_20260205-2214.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_daily_health_20260205-2217.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safe_prune_plan_20260205-2213.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safe_prune_plan_20260205-2215.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safe_prune_plan_20260205-2246.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safety_audit_20260205-2201.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safety_audit_20260205-2213.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safety_audit_20260205-2214.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safety_audit_20260205-2215.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safety_audit_20260205-2216.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safety_audit_20260205-2217.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_safety_audit_20260205-2249.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_skill_audit_20260205-2204.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_skill_audit_20260205-2205.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_skill_audit_20260205-2213.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_skill_audit_20260205-2214.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_skill_audit_20260205-2215.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_skill_audit_20260205-2216.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_skill_audit_20260205-2217.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_skill_audit_20260205-2249.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_worktree_cleanup_complete_20260205-2249.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_app_report_20260207-1822.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_app_report_20260208-1210.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_app_report_20260208-1224.md docs/archived/reports/automation/
git mv docs/reports/automation/codex_app_report_20260208-1226.md docs/archived/reports/automation/
```

## Part 4: Backend/frontend session reports → `docs/archived/sessions/` and `docs/archived/reports/`

```bash
# Session summaries
git mv backend/SESSION_44_MIGRATION_SUMMARY.md docs/archived/sessions/
git mv frontend/TEST_FIXES_SUMMARY.md docs/archived/sessions/
git mv frontend/COMPONENT_BURN_SESSION_SUMMARY.md docs/archived/sessions/
git mv "frontend/SESSION-35-TEST-COVERAGE-REPORT.md" docs/archived/sessions/
git mv frontend/SESSION_34_FRONTEND_TEST_REPORT.md docs/archived/sessions/
git mv frontend/e2e/SESSION_22_SUMMARY.md docs/archived/sessions/

# Implementation/test reports
git mv backend/CLI_IMPLEMENTATION_SUMMARY.md docs/archived/reports/
git mv backend/RAG_SERVICE_IMPLEMENTATION_SUMMARY.md docs/archived/reports/
git mv backend/TEST_COVERAGE_ANALYSIS.md docs/archived/reports/
git mv backend/TEST_COVERAGE_SUMMARY.md docs/archived/reports/
git mv backend/TEST_IMPLEMENTATION_CHECKLIST.md docs/archived/reports/
```

---

## Commit and PR

```bash
git add -A
git commit -m "chore: archive 81 stale session summaries, reports, and automation logs

Move completed session summaries, one-time implementation reports,
point-in-time test/security snapshots, and pre-Feb-10 automation
logs to docs/archived/. No content changes — git mv only.

Files moved:
- 6 root session summaries → docs/archived/sessions/
- 23 root implementation/test reports → docs/archived/reports/
- 43 old automation reports → docs/archived/reports/automation/
- 6 backend/frontend session reports → docs/archived/sessions/
- 5 backend implementation reports → docs/archived/reports/"

git push origin chore/doc-archival-sweep

gh pr create
  --title "chore: archive 81 stale docs (sessions, reports, automation logs)"
  --body "## Summary
- Move 81 stale markdown files to docs/archived/
- No content changes — purely git mv operations
- Clears root directory of session summaries and one-time reports
- Archives pre-Feb-10 Codex automation logs (keeps recent 24)

## Files Moved
- **6** root session summaries → docs/archived/sessions/
- **23** root reports → docs/archived/reports/
- **43** old automation reports → docs/archived/reports/automation/
- **11** backend/frontend session/test reports → docs/archived/

## What Stays
- All active guidance docs (CLAUDE.md, README.md, CHANGELOG.md, etc.)
- Recent automation reports (Feb 10+)
- Reference material (architecture, research, API docs)
- Module READMEs, OWNERSHIP files, skill definitions

Generated with Gemini CLI"
```

---

## Verification

After all moves, confirm:

```bash
# No session summaries left at root
ls SESSION_*.md BURN_SESSION_*.md SECURITY_AUDIT_SESSION_*.md 2>/dev/null | wc -l
# Expected: 0

# No archived reports left at root
ls *_SUMMARY.md *_REPORT.md *_MANIFEST.md 2>/dev/null
# Expected: only IMPLEMENTATION_SUMMARY.md, RECENT_ACTIVITY.md, SKIPPED_TESTS_README.md remain

# Automation reports: only Feb 10+ remain
ls docs/reports/automation/ | wc -l
# Expected: 24

# Archived files exist in target
ls docs/archived/sessions/ | wc -l
# Expected: 12+

ls docs/archived/reports/ | wc -l
# Expected: 28+

ls docs/archived/reports/automation/ | wc -l
# Expected: 43
```

---

## DO NOT

- Edit any file content
- Touch any `.claude/` files
- Touch any code files (`.py`, `.ts`, `.tsx`)
- Move files not listed in this document
- Modify CLAUDE.md, README.md, CHANGELOG.md, or any active guidance docs
- Move IMPLEMENTATION_SUMMARY.md (the current one, dated 2026-02-14 — this is active)
- Move RECENT_ACTIVITY.md or REPO_AUDIT_REPORT.md if they were updated today
