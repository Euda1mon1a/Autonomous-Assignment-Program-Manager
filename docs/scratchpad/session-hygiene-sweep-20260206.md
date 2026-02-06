# Session: Repo Hygiene Sweep + Security Hardening + Codex Adoption

**Date:** 2026-02-06
**Branch:** `main` (multiple PRs merged)
**Status:** COMPLETE

---

## PRs Merged This Session

| PR | Title | Key Changes |
|----|-------|-------------|
| #829 | Repo hygiene sweep | Fixed 55+ broken doc links from PAI archive, archived 4 obsolete scripts, deduped settings.json hooks, pruned branches (24->9) |
| #830 | Bandit security hardening | 37 files, 40+ warnings resolved (defusedxml, AST eval replacer, tmp paths, SQL parameterization). Fixed short-circuit regression flagged by Codex. |
| #831 | Codex test coverage | 6 test files adopted from Codex worktree 00c5. Fixed interceptor mock in useImportStaging (user caught the real issue). |
| #832 | Credential penalty ramp + questionnaire | Wired FACULTY_CREDENTIAL_MISMATCH_PENALTY env var, supervision variable re-keying, schedule alignment questionnaire for human review. |

---

## Security Actions

- **Repo made private** (`gh repo edit --visibility private`)
- **soharaa** collaborator investigated: read-only access, 4 orphaned commits in GitHub Insights (unreachable from any branch/PR), low risk
- **Branch protection**: Requires GitHub Pro on private repos ($4/mo). Deferred; added to HUMAN_TODO.
- **Main branch unprotected**: Relying on discipline + 33 pre-commit hooks for now

---

## Codex Integration

### Worktree Review
- 17 Codex worktrees found
- **00c5**: 6 new test files -> adopted in PR #831
- **028d**: Bandit security fixes -> cherry-picked in PR #830
- **ac32**: Mypy "fixes" (blanket `ignore_errors = true`) -> **SKIPPED** (hides 4,335 real errors)

### Codex Automation Reports (0100 run)
- Reviewed all reports from 2100-2300 HST run
- All commits from `bad1` worktree previously salvaged (PR #814)
- Only new finding: skill duplication across `.codex/skills` and `.claude/skills` (already in HUMAN_TODO)

### Codex Review Findings Addressed
- PR #829: P2 - hook path portability (fixed: switched to relative path)
- PR #830: P2 - BoolOp short-circuit regression (fixed: lazy evaluation)
- PR #831: P2 - interceptor mock shape (user fixed: keep `batch_id` not `batchId`)

---

## CP-SAT Lockdown Audit

**Result: 100% locked down.** Triple-layered enforcement:
1. Route level: HTTP 400 rejects non-CP-SAT when `DEBUG=False`
2. Engine level: Force-converts all algorithms to `cp_sat`
3. Docker: `DEBUG=false` in production config

Credential penalty ramp fully wired: `FACULTY_CREDENTIAL_MISMATCH_PENALTY` env var -> activity solver objective function (default: 15).

---

## New Documents Created

- `docs/guides/SCHEDULE_ALIGNMENT_QUESTIONNAIRE.md` - 11-section human review checklist for CP-SAT output
- `.gitignore` entry for `docs/guides/SCHEDULE_ALIGNMENT_ANSWERS*.md` (filled-in answers stay local)

---

## Lessons Learned

1. **Interceptor mock direction matters**: When testing hooks that bypass axios, the mock should return snake_case (backend format), not camelCase. The hook's mapping IS the thing being tested.
2. **Mypy blanket suppression is worse than noise**: `ignore_errors = true` for 501 files hides real bugs. Incremental module-level suppression is the right approach.
3. **GitHub Pro required for private repo branch protection**: Free plan only supports protection/rulesets on public repos.
4. **Codex P2 comments are consistently high quality**: 3/3 P2 findings this session were legitimate issues worth fixing.

---

*Session complete. Repo is private, security hardened, docs cleaned, CP-SAT locked in.*
