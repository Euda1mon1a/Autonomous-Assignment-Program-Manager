# Doc Archival Sweep — Task Manifest

> **Created:** 2026-02-16 | **Agent:** Any (Gemini CLI preferred for mechanical tasks)
> **Branch:** `chore/doc-archival-sweep-feb16` from `main`
> **Commit message:** `chore: archive 77 stale analysis, automation, and session files`

This is a mechanical task: move stale files to `docs/archived/` using `git mv`. No content editing.

---

## Pre-flight

```bash
git checkout main && git pull
git status --porcelain  # Must be empty
git checkout -b chore/doc-archival-sweep-feb16 main
```

---

## Part 1: Analysis Reports (18 files)

All dated Block 10 validation/analysis output from Jan 2026. One-time runs, no ongoing value.

**Target:** `docs/archived/reports/analysis/`

```bash
mkdir -p docs/archived/reports/analysis

git mv docs/analysis/AGENT_ORCHESTRATION_TOOLING_ANALYSIS.md docs/archived/reports/analysis/
git mv docs/analysis/block10_excel_vs_cpsat_20260128.md docs/archived/reports/analysis/
git mv "docs/analysis/block10_mcp_validation_2026-01-27_human.md" docs/archived/reports/analysis/
git mv "docs/analysis/block10_mcp_validation_2026-01-27_llm.md" docs/archived/reports/analysis/
git mv docs/analysis/block10_mcp_validation_20260127_human.md docs/archived/reports/analysis/
git mv docs/analysis/block10_mcp_validation_20260127_llm.md docs/archived/reports/analysis/
git mv docs/analysis/block10_mcp_validation_human_20260127.md docs/archived/reports/analysis/
git mv docs/analysis/block10_mcp_validation_human_20260128.md docs/archived/reports/analysis/
git mv docs/analysis/block10_mcp_validation_llm_20260127.md docs/archived/reports/analysis/
git mv docs/analysis/block10_mcp_validation_llm_20260128.md docs/archived/reports/analysis/
git mv docs/analysis/block10_mcp_validation_raw_20260127_2358.json docs/archived/reports/analysis/
git mv docs/analysis/block10_p0p1_timeoff_run_20260128.md docs/archived/reports/analysis/
git mv docs/analysis/excel-vs-cpsat-block10-comparison.md docs/archived/reports/analysis/
git mv docs/analysis/faculty_cv_conversion_proposal_20260127.md docs/archived/reports/analysis/
git mv docs/analysis/mcp_schedule_tools_run_human.md docs/archived/reports/analysis/
git mv docs/analysis/mcp_schedule_tools_run_llm.md docs/archived/reports/analysis/
git mv docs/analysis/mcp_validation_block10_human.md docs/archived/reports/analysis/
git mv docs/analysis/mcp_validation_block10_llm.md docs/archived/reports/analysis/
```

---

## Part 2: Codex Automation Output (43 files)

Nightly automation plans, reports, triage digests, and audit snapshots. Ephemeral output with no ongoing reference value.

**Target:** `docs/archived/automation/`

```bash
mkdir -p docs/archived/automation

git mv docs/reports/automation/codex_app_plan_20260205-2133.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260205-2202.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260206-0700.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260207-1822.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260208-1210.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260208-1224.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260210-0435.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260211-025737_pass1.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260211-025822_pass2.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260212-0613.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260213-0817.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260213-0817_triaged.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260213-0833.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260214-1111.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260215-0601.json docs/archived/automation/
git mv docs/reports/automation/codex_app_plan_20260216-0808.json docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260210-0435.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260210-2047.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260211-025737_pass1.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260211-025822_pass2.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260212-0613.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260213-0817.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260213-0833.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260214-1111.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260214-1147.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260215-0601.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_20260216-0808.md docs/archived/automation/
git mv docs/reports/automation/codex_app_report_include_clean_20260211-025744.md docs/archived/automation/
git mv docs/reports/automation/codex_app_triage_20260212-0619.md docs/archived/automation/
git mv docs/reports/automation/codex_app_triage_20260213-0817.md docs/archived/automation/
git mv docs/reports/automation/codex_app_triage_20260213-0833.md docs/archived/automation/
git mv docs/reports/automation/codex_automation_profile_20260214-1150.md docs/archived/automation/
git mv docs/reports/automation/codex_branch_triage_20260211-025937_pass1.md docs/archived/automation/
git mv docs/reports/automation/codex_branch_triage_20260211-030002_pass2_commit_scope.md docs/archived/automation/
git mv docs/reports/automation/codex_branch_triage_20260211-030050_pass3_commit_scope.md docs/archived/automation/
git mv docs/reports/automation/codex_branch_triage_20260211-030132_pass4_commit_scope.md docs/archived/automation/
git mv docs/reports/automation/codex_branch_triage_20260211-030219_final.md docs/archived/automation/
git mv docs/reports/automation/codex_branch_triage_20260211-030234_final.md docs/archived/automation/
git mv docs/reports/automation/codex_branch_triage_20260211-030247_final.md docs/archived/automation/
git mv docs/reports/automation/codex_chaff_hold_queue_20260216-0828.json docs/archived/automation/
git mv docs/reports/automation/codex_daily_triage_digest_20260216-0631.md docs/archived/automation/
git mv docs/reports/automation/codex_safety_audit_20260211-2145.md docs/archived/automation/
git mv docs/reports/automation/codex_skill_audit_20260211-2145.md docs/archived/automation/
```

---

## Part 3: Session Summaries & History (3 files)

Dated session transcripts from early development phases.

**Target:** `docs/archived/sessions/`

```bash
# Directory already exists
git mv docs/history/SESSION_060_HISTORIAN.md docs/archived/sessions/
git mv "docs/history/SESSION_2026-01-16_CROSS_DISCIPLINARY_VALIDATION.md" docs/archived/sessions/
git mv "docs/history/SESSION_2026-01-16_FOAM_AND_QUANTUM_INSIGHT.md" docs/archived/sessions/
```

---

## Part 4: Exported Schedule Data (5 files)

Block 10 schedule exports from Jan 2026. Data snapshots, not reference docs.

**Target:** `docs/archived/data/`

```bash
mkdir -p docs/archived/data

git mv docs/priorities/block10_bt2_format.xlsx docs/archived/data/
git mv docs/priorities/block10_full_20260122.xlsx docs/archived/data/
git mv docs/priorities/block10_full_20260122.xml docs/archived/data/
git mv docs/priorities/block10_schedule_20260122.xlsx docs/archived/data/
git mv docs/priorities/block10_schedule_20260122.xml docs/archived/data/
```

---

## Part 5: Development Session/Report Files (4 files)

Completed postmortems, one-time audits, and triage reports.

**Target:** `docs/archived/sessions/` and `docs/archived/reports/`

```bash
git mv docs/development/POSTMORTEM_BLOCK10_SESSION.md docs/archived/sessions/
git mv docs/development/SESSION_SAFETY_CHECKLIST.md docs/archived/sessions/
git mv docs/development/SCHEMA_AUDIT_REPORT.md docs/archived/reports/
git mv docs/development/OPUS_MINI_BRANCH_TRIAGE_REPORT.md docs/archived/reports/
```

---

## Part 6: API & Architecture Session Files (4 files)

One-time validation and session output.

**Target:** `docs/archived/reports/` and `docs/archived/sessions/`

```bash
git mv docs/api/API_SYNC_REPORT.md docs/archived/reports/
git mv docs/api/SESSION_39_VALIDATION_SUMMARY.md docs/archived/sessions/
git mv docs/architecture/DATABASE_INDEX_REPORT.md docs/archived/reports/
git mv docs/architecture/RESILIENCE_FRAMEWORK_SESSION26.md docs/archived/sessions/
```

---

## Verification

```bash
# Count moved files (should be 77)
git diff --cached --name-only | grep "docs/archived/" | wc -l

# Ensure no broken internal links in active docs
grep -r "docs/analysis/" docs/ --include="*.md" -l | grep -v archived
grep -r "docs/history/" docs/ --include="*.md" -l | grep -v archived
grep -r "docs/reports/automation/" docs/ --include="*.md" -l | grep -v archived

# Check that empty source directories can be removed
# (git rm empty dirs automatically, but verify)
ls docs/analysis/ 2>/dev/null && echo "WARN: docs/analysis/ not empty"
ls docs/history/ 2>/dev/null && echo "WARN: docs/history/ not empty"
ls docs/priorities/ 2>/dev/null && echo "WARN: docs/priorities/ not empty"
```

---

## Commit & PR

```bash
git add -A
git commit -m "$(cat <<'EOF'
chore: archive 77 stale analysis, automation, and session files

Move dated Block 10 analyses (18), Codex automation output (43),
session summaries (3), exported data (5), and development
reports/postmortems (8) to docs/archived/.

No content changes. Preserves git history via git mv.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"

git push -u origin chore/doc-archival-sweep-feb16

gh pr create --title "chore: archive 77 stale analysis, automation, and session files" --body "$(cat <<'EOF'
## Summary
- Move 77 dated/ephemeral files to `docs/archived/`
- No content editing — pure `git mv` operations
- Declutters active documentation directories

**Breakdown:**
- 18 Block 10 analysis reports → `docs/archived/reports/analysis/`
- 43 Codex automation output → `docs/archived/automation/`
- 3 session summaries → `docs/archived/sessions/`
- 5 exported schedule data → `docs/archived/data/`
- 4 development reports/postmortems → `docs/archived/reports/` + `docs/archived/sessions/`
- 4 API/architecture session files → `docs/archived/reports/` + `docs/archived/sessions/`

## Test plan
- [ ] Verify no broken links in active docs
- [ ] Confirm file count matches (77)
- [ ] Spot-check git log follows renames

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Files NOT Archived (Intentionally Kept)

These were reviewed but kept because they're active references:

- `docs/development/BEST_PRACTICES_AND_GOTCHAS.md` — referenced by CLAUDE.md
- `docs/development/CODEX_*.md` (8 files) — active Codex operational docs
- `docs/development/AGENT_*.md` — active agent guidance
- `docs/planning/` (54 files) — needs separate triage pass (mix of active roadmaps and completed plans)
- `docs/domain/TAMC_SCHEDULING_CONTEXT.md` — domain reference
- `RECENT_ACTIVITY.md` (root) — auto-generated by sync script, rotated daily

## Deferred: `docs/planning/` Triage

The 54 files in `docs/planning/` need a judgment-based review, not mechanical archival. Many are completed roadmaps or superseded plans, but some may still be active. Recommend a separate session to classify each.
