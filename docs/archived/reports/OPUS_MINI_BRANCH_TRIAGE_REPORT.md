# Opus 4.6 (Mac Mini) Branch Triage Report

> **Wave 1:** 2026-02-13 | 19 branches | PR #1119
> **Wave 2:** 2026-02-19 | 21 branches (13 unique tasks) | PRs #1172–#1178
> **Source:** `claude/*` branches on `mini` remote (pruned; recovered from reflog)
> **Agent:** Claude Opus 4.6 running on Mac Mini
> **Reviewer:** Claude Opus 4.6 (main workstation) + agent teams + human review

---

## Summary

### Wave 1 (Feb 10–12 branches, triaged Feb 13)

| Category | Count | Outcome |
|----------|-------|---------|
| **Wheat — clean merge** | 2 | Merged directly (integration tests, route validation tests) |
| **Wheat — cherry-picked** | 12 | Extracted specific files from 12 branches |
| **Chaff — confirmed** | 5 | No value; delete branches |
| **Total** | 19 | 14 wheat (74%), 5 chaff (26%) |

### Wave 2 (Feb 14–19 branches, triaged Feb 19)

| Category | Count | Outcome |
|----------|-------|---------|
| **Wheat — merge as-is** | 1 | Keyboard nav a11y tests (100% additive) |
| **Wheat — cherry-pick + fix** | 6 | Extracted and fixed Codex anti-patterns |
| **Chaff — confirmed** | 6 | Already on main, broken links, or too marginal |
| **Total** | 13 unique tasks (21 branches) | 7 wheat (54%), 6 chaff (46%) |

### Combined Totals

| | Wave 1 | Wave 2 | Overall |
|--|--------|--------|---------|
| Branches reviewed | 19 | 21 | 40 |
| Unique tasks | 19 | 13 | 32 |
| Wheat extracted | 14 (74%) | 7 (54%) | 21 (66%) |
| Chaff discarded | 5 (26%) | 6 (46%) | 11 (34%) |

---

## Failure Pattern Taxonomy

Five recurring failure patterns explain why branches were rejected or needed selective extraction instead of full merge.

### 1. Shared Base Contamination

**Pattern:** All 2026-02-12 branches share ~860 lines of non-task changes (`.codex/`, `TODO.md`, `MERGE_ROADMAP.md`, `faculty_assignment_expansion_service.py`).

**Impact:** Every branch conflicts with main because PR #1117 modified `faculty_assignment_expansion_service.py`. Clean merge is impossible for any 02-12 branch.

**Root cause:** The agent's working tree had uncommitted shared changes when it created feature branches. Each branch forked from the same dirty state.

**Fix:** Before creating feature branches, ensure the working tree is clean. Run `git stash` or commit shared changes to a dedicated branch first.

### 2. Blast Radius Explosion

**Pattern:** `datetime-utcnow` touched 587 files. `type-hints` touched 50 files. `skeleton-primitives` touched 43 files.

**Impact:** Massive branches are unmergeable as-is and require manual cherry-picking of individual files.

**Root cause:** Broad tasks ("fix all datetime.utcnow", "add type hints everywhere") produce branches that touch more files than any reviewer can assess.

**Fix:** Scope tasks to specific directories or modules. "Fix datetime.utcnow in `backend/app/core/`" instead of "Fix datetime.utcnow everywhere."

### 3. Feature Overlap / Already Merged

**Pattern:** `health-deep` endpoint was already merged in PR #1116. `standardize-error` overlapped with `error-normalization` and `audit-routes`.

**Impact:** Wasted compute. The branch does work that's already done.

**Root cause:** The agent doesn't check `origin/main` for recently merged features before starting work.

**Fix:** Before starting a feature branch, run `git log origin/main --oneline -20` and search for the feature. Add a pre-flight check: "Has this already been done on main?"

### 4. Antipattern Introduction

**Pattern:** `error-normalization` creates `{"detail": {"detail": "..."}}` nesting. `standardize-error` introduces `datetime.utcnow()` in new code (the very deprecation another branch fixes). `type-hints` adds `# type: ignore` suppression instead of actual annotations.

**Impact:** The "fix" is worse than the original problem.

**Root cause:** The agent applies the fix pattern mechanically without understanding the downstream effect. FastAPI's `HTTPException(detail=...)` already wraps in `{"detail": ...}`, so passing a dict with `"detail"` key creates double nesting.

**Fix:** Include framework-specific context in the task prompt. "FastAPI HTTPException already wraps `detail` in the response body — do not add a `detail` key inside the detail dict."

### 5. Test-Before-Feature Inversion

**Pattern:** `normalize-validation-tests` writes tests for a `_normalize_validation_result()` function that exists only in the rejected `error-normalization` branch.

**Impact:** Tests for code that will never be merged. Dead on arrival.

**Root cause:** Test generation tasks run against un-merged feature branches instead of main.

**Fix:** Test generation should target code on `main` or explicitly merged features only. Never generate tests for branches still under review.

---

## Recommended Prompt Refinements

### For Bug Fix Tasks

```
Before starting:
1. git fetch origin && git diff origin/main -- [target files] to check for recent changes
2. Scope to specific directories (e.g., backend/app/core/, NOT the entire repo)
3. Ensure working tree is clean before branching

When fixing:
- Test the fix pattern on ONE file first, verify it works, then apply broadly
- For API error responses, check how FastAPI/framework wraps the response
- Never add # type: ignore — add proper type annotations or skip the file
```

### For Feature Tasks

```
Before starting:
1. Check if the feature already exists on main: git log origin/main --grep="feature-keyword"
2. Check if a similar PR is open: gh pr list --search "feature-keyword"
3. Limit scope to 10 files maximum per branch

When implementing:
- One concern per branch (don't mix error handling + test infrastructure)
- Verify Tailwind classes are statically analyzable (no template literals for class names)
- Include only the files relevant to YOUR change (not shared TODO.md, docs, etc.)
```

### For Test Tasks

```
Before starting:
1. Only test code that exists on main (not un-merged branches)
2. Verify the function/endpoint you're testing is importable from main

When writing tests:
- Keep test files < 500 lines
- Use existing conftest.py fixtures, don't create parallel infrastructure
```

---

## Triage Checklist for Future Branches

Use this when reviewing `claude/*` branches from the Mini:

- [ ] **Is the working tree clean?** Check for shared base files (TODO.md, .codex/, MERGE_ROADMAP.md)
- [ ] **Is it already on main?** `git log main --oneline -20 | grep -i "keyword"`
- [ ] **File count < 15?** Branches touching 15+ files need extra scrutiny
- [ ] **Does it introduce deprecated APIs?** Search for `datetime.utcnow`, `datetime.now()` without tz
- [ ] **Are error responses correct?** No nested `{"detail": {"detail": ...}}`
- [ ] **Are type hints real?** No `# type: ignore` suppression
- [ ] **Do tests target merged code?** Tests should test what's on main

---

## Branch Disposition

### Merged / Cherry-picked (PR #1119)

| Branch | What was taken |
|--------|---------------|
| `02-10-add-integration-tests` | Full merge (2 files) |
| `02-10-add-request-validation-tests` | Full merge (3 files) |
| `02-12-create-db-migration-indexes` | Migration file only |
| `02-12-land-native-dev-workflow` | Dev scripts only (14 files) |
| `02-12-fix-invalidate-schedule-cache` | Superseded by cache_utils deletion |
| `02-12-delete-vestigial-cache-utils` | cache/__init__.py + utils.py deletion |
| `02-12-review-useeffect-hooks` | ViewToggle.tsx + useWebSocket.ts fixes |
| `02-10-audit-loading-states` | 59 loading.tsx files |
| `02-12-fix-datetime-utcnow` | 61 core/ + models/ files |
| `02-12-fix-error-normalization` | imports.py + import_staging.py only |
| `02-10-audit-api-routes-errors` | slowapi_limiter.py + main.py only |
| `02-12-add-error-boundaries` | PageErrorBoundary.tsx + 5 error.tsx |
| `02-12-keyboard-navigation` | useGridKeyboardNavigation hook + test |
| `02-12-unify-apierror-type` | api.ts + errors.ts + types/api.ts |

### Confirmed Chaff (delete after review)

| Branch | Reason |
|--------|--------|
| `02-12-skeleton-primitives` | Tailwind dynamic class bug, boilerplate |
| `02-10-type-hints` | `# type: ignore` suppression, not real hints |
| `02-12-normalize-validation-tests` | Tests for un-merged error normalization |
| `02-12-health-deep` | Already merged in PR #1116 |
| `02-12-standardize-error` | datetime.utcnow() bug in new code |

---

## Lessons from Codex Review (PR #1119)

After cherry-picking wheat from 14 branches, the PR went through **7 rounds of Codex review** that caught integration bugs introduced by the cherry-pick process itself. These represent a **6th failure pattern**: half-migrations that pass in isolation but break at integration.

### 6. Half-Migration / Contract Violation

**Pattern:** A cherry-picked change modifies one side of an interface contract but leaves the other side unchanged.

**Impact:** Runtime errors (TypeError), silent data loss (frontend shows generic errors instead of actionable messages), broken rollbacks.

**Examples from PR #1119:**

| Round | Issue | Root Cause |
|-------|-------|-----------|
| 1 | `scripts/dev/*.sh` not executable (P1) | Cherry-pick preserved file content but not mode bits |
| 1 | `--build` flag rejected (P2) | New arg parser didn't account for existing Makefile callers |
| 2 | `audience_auth.py` TypeError (P1) | `datetime.now(UTC)` (aware) vs `utcfromtimestamp()` (naive) |
| 2 | `APIKey.is_expired` TypeError (P1) | Same: aware .now() vs naive DB column |
| 3 | 4 more models with same TypeError (P1) | IPWhitelist, IPBlacklist, OAuth2, CalendarSubscription, Idempotency |
| 4 | Double-nested `{"detail":{"detail":"..."}}` (P2) | Backend error key changed without checking FastAPI wrapping |
| 4 | Frontend `errorData.error` → undefined (P2) | Backend key renamed to `"message"` but frontend reads `"error"` |
| 5 | Rate-limit detail now string, test expects object (P1) | Response shape changed without checking test assertions |
| 5 | Health endpoint `"error"` → `"detail"` (P2) | Key renamed but monitoring/tests expect `"error"` |
| 6 | Migration drops inherited indexes (P1) | Downgrade removes indexes owned by earlier migrations |
| 6 | `make local-up` doesn't exist (P3) | Setup script references wrong Makefile target |

**Root cause:** The Mini's branches were generated in isolation. Each branch modified one side of a contract (e.g., changed `utcnow()` but not `utcfromtimestamp()`, changed backend error keys but not frontend parsing). When cherry-picked onto main, the mismatch surfaces.

**Fix:** Add contract-awareness rules to automation prompts. See `.claude/automation-prompts/preflight.md` for the universal preflight block that addresses this.

### Updated Triage Checklist

Add these to the existing checklist:

- [ ] **Are datetime comparisons consistent?** Both sides must be aware or both naive
- [ ] **Do error response keys match frontend?** `grep -r "detail\.\|error\." frontend/src/hooks/`
- [ ] **Are file permissions correct?** `git diff --stat` should show mode changes for `.sh` files
- [ ] **Does migration downgrade only drop its own objects?** Cross-reference earlier migrations
- [ ] **Do Makefile/script references match actual targets?** `make -n <target>` to verify

---

## Wave 2: Feb 14–19 Branches (Triaged 2026-02-19)

### Context

21 branches appeared in the `mini` remote between Feb 14–19. The remote was pruned, but all commits were recoverable from the local reflog. These branches exhibited the same dirty-tree contamination as Wave 1: ~695–712 files changed / ~17K lines per branch, with actual targeted work buried in the noise.

**Key difference from Wave 1:** These branches forked from a pre-datetime-migration main. The 10 datetime PRs (#1161–#1170) had already been merged to main, meaning every Wave 2 branch carried datetime regressions (`datetime.utcnow()` → should be `datetime.now(UTC)`) as part of its diff.

13 unique task categories were identified across 21 branches. 8 tasks had multiple attempts (Feb 14–16 and Feb 18–19); only the latest attempt was reviewed.

### Triage Method

Agent Teams (3 agents) reviewed branches in parallel:
- **Agent 1 (Backend):** Type hints, test fixes, DB indexes, MCP tools
- **Agent 2 (Frontend + Docs):** Loading states, useEffect hooks, Codex docs, a11y tests, RECENT_ACTIVITY dedup
- **Agent 3 (Infrastructure):** Admin dashboard, OpenTelemetry, budget cron manager

Each agent used `git diff origin/main..COMMIT_SHA -- <targeted_dirs>` to isolate real changes from dirty-tree contamination.

### Extraction Pattern

For each MERGE/MODIFY branch:
1. `git show SHA:path/to/new_file > path/to/new_file` for purely new files
2. `git diff origin/main..SHA -- specific/file | git apply` for modifications
3. Manual review and fix of Codex anti-patterns before committing
4. Migration `down_revision` fixed to current main head (`20260218_drafts_ver_tbl`)

### Wave 2 Verdicts

#### Wheat — Cherry-picked (7 PRs)

| # | Task | PR | Files | Fixes Applied |
|---|------|----|-------|---------------|
| 1 | Frontend loading states | #1172 | 3 new | `git add -f` for gitignored wellness dir |
| 2 | Keyboard nav a11y tests | #1173 | 1 new, 2 modified | Hook integration + focus ring styles |
| 3 | Admin status dashboard | #1174 | 1 new, 1 modified | Extracted `useHealthDeep` hook (not on main) |
| 4 | DB composite indexes | #1175 | 1 new | `down_revision` fixed; BREAK_GLASS_APPROVED enum preserved |
| 5 | Budget-aware cron manager | #1177 | 6 new | 9x `datetime.utcnow()`, 4x `str(e)` leak, missing auth guards |
| 6 | VaR/Shapley MCP tests | #1178 | 1 new, 12 modified | ClearHalfDayAssignments removal, Shapley fallback enhancement |
| 7 | Codex CLI docs | #1176 (CLOSED) | — | Evaluated as DISCARD: broken links, content regression |

#### Chaff — Discarded (6 tasks)

| Task | Reason |
|------|--------|
| Type hints — export services | Low-value annotations, no behavioral change |
| Type hints — upload services | Same as above |
| RECENT_ACTIVITY.md dedup | File already cleaned up by other PRs |
| OpenTelemetry config | Incomplete; missing env-specific config; too risky without testing |
| DEBT-025 failing tests | Tests target code paths already fixed by datetime migration |
| useEffect exhaustive-deps | Most hooks already corrected; remaining are intentional suppressions |

### Wave 2 Anti-Patterns Found (and Fixed)

#### 7. Missing Auth Guards

**Pattern:** Budget API routes had no authentication. All 4 endpoints (`GET /status`, `PUT /config`, `POST /check-task`, `GET /alerts`) were publicly accessible.

**Impact:** Any unauthenticated user could view AI spending, modify budget limits, or trigger budget checks.

**Fix:** Added `Depends(require_admin())` on all routes. Used `require_admin()` from `app.api.dependencies.role_filter` (not the nonexistent `get_current_admin_user`).

#### 8. `detail=str(e)` Stack Trace Leaks

**Pattern:** Budget routes caught exceptions and returned `HTTPException(detail=str(e))`, exposing internal stack traces in API responses.

**Impact:** Information disclosure — attackers can see internal paths, class names, and error chains.

**Fix:** Replaced all 4 instances with static error messages (`"Failed to retrieve budget status"`, etc.).

#### 9. `datetime.utcnow()` in New Code

**Pattern:** Brand-new files (not ported from old code) used `datetime.utcnow()` — the very deprecated API that Wave 1 spent 10 PRs fixing.

**Impact:** Introduces the same technical debt we just eliminated.

**Instances:** 9 in `budget_cron_manager.py`, 3 in `budget_tasks.py` — all fixed to `datetime.now(UTC)`.

#### 10. Broken Link "Fixes"

**Pattern:** Codex CLI docs branch "fixed" AUTH_API.md links by pointing them to nonexistent files (`AUTHENTICATION_SECURITY.md`, `rate-limiting.md`, `JWT_MANAGEMENT.md`). The original links pointed to files that DO exist (`SECURITY_PATTERN_AUDIT.md`, `configuration.md`, `AUDIENCE_AUTH_USAGE.md`).

**Impact:** Would have broken working documentation links.

**Fix:** Entire branch discarded.

### Migration Chain Note

PRs #1175 (composite indexes) and #1177 (budget tables) both use `down_revision = "20260218_drafts_ver_tbl"`. They are independent PRs but if both merge, one must be rebased to chain after the other to avoid an Alembic branch point.

---

## Cumulative Lessons

### For Mini Opus Automation Prompts

1. **Clean tree is non-negotiable.** Wave 1 and Wave 2 both suffered from dirty-tree contamination. The `git status --porcelain` check in `CLAUDE.md` Automated Run Guardrails exists because of this.

2. **Datetime migration awareness.** Any branch forked before a datetime migration carries regressions. Automation prompts should include: "Check if `datetime.utcnow()` exists in your changes — if so, use `datetime.now(UTC)` instead."

3. **Auth is never optional.** New API routes MUST include auth guards. The budget routes shipped with zero authentication. Automation prompts should include: "Every new route MUST use `Depends(require_admin())` or appropriate role filter."

4. **Never expose `str(e)`.** Exception details leak internal state. Use static error messages for HTTP responses.

5. **Verify links before "fixing" them.** The Codex docs branch broke working links by pointing to nonexistent files. Automation prompts should include: "Before changing a documentation link, verify both the old and new targets exist."

6. **Dedup before start is real.** Wave 2 had 8 tasks with duplicate attempts. The latest attempt was always better, but the earlier attempts wasted compute. The `git log origin/main` dedup check matters.

### Triage Efficiency

| Metric | Wave 1 | Wave 2 | Trend |
|--------|--------|--------|-------|
| Branches | 19 | 21 | +10% |
| Wheat rate | 74% | 54% | -20% (more chaff) |
| Fixes per wheat branch | ~1 | ~3 | More anti-patterns |
| PRs produced | 1 (#1119) | 6 (#1172–#1178) | Smaller, focused PRs |
| Triage method | Manual | Agent Teams (3) | Parallelized |

Wave 2 branches were lower quality (more anti-patterns per branch) but the agent team triage method was more efficient at isolating wheat. Individual PRs instead of one omnibus PR also make review and merge easier.
