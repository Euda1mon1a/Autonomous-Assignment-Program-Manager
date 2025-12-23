# Session Salvage Dump

This document consolidates all useful outcomes from the session for review and PR.

## 1) Docs / Process

- `docs/development/AI_RULES_OF_ENGAGEMENT.md`
- `docs/development/CLAUDE_GIT_SAFE_SYNC_CHECKLIST.md`
- `docs/development/CLAUDE_MERGE_ISSUES_LOG.md`
- `docs/development/ORPHANED_BRANCH_MERGE_STATUS.md`
- `docs/development/SHORT_TERM_BLINDSPOTS_RECOMMENDATIONS.md`
- `docs/development/SESSION_ACTIVITY_LAST_16_HOURS.md`
- `docs/development/CODEX_SYSTEM_OVERVIEW.md`
- `docs/development/CLAUDE_SESSION_SUMMARY_UPDATE.md`
- `docs/development/CLAUDE_REVIEW_PATCHES.md`
- `docs/development/CLAUDE_REVIEW_PATCHES_2.md`
- `docs/development/CLAUDE_REVIEW_PATCHES_3.md`
- `docs/development/CLAUDE_REVIEW_PATCHES_5.md`
- `docs/development/CLAUDE_REVIEW_PATCHES_6.md`
- `docs/development/CLAUDE_REVIEW_PATCHES_7.md`
- `docs/development/AI_RULES_OF_ENGAGEMENT.md`

## 2) Admin/User Guides

- `docs/user-guide/USER_GUIDE.md` (operational safeguards section)
- `docs/admin-manual/index.md`:
  - Operational lessons
  - Clinician-friendly “main/origin” explanation
  - Parallel AI sessions (split terminal not shared context)

## 3) Hooks / AI Guidance

- `.claude/hooks/session-start.sh` (prints rules at session start)
- `CLAUDE.md` (AI Rules of Engagement section added)

## 4) DB Observations (Read-only)

- Block 10 (2026-03-10 → 2026-04-06) has 56 blocks, 44 assignments currently.
- Assignments are mostly `FMIT AM`/`FMIT PM` + small number of Procedure PM.
- A successful hybrid run logged 80 assignments but did not persist (likely deletion-on-failure issue).
- People counts: 17 residents / 12 faculty.

## 5) High-Value Findings

- Data loss risk: assignments deleted before a successful solve.
- Missing provenance: assignments not linked to schedule runs.
- Manual overrides should be protected and auditable.
- Block-half logic should respect academic year boundaries.

## 6) Suggested Follow-ups

- PR the above docs/hook changes only.
- Validate schedule-run persistence fix (Patch 7) in a separate PR.
- Confirm NF post-call constraint registration and outputs.
