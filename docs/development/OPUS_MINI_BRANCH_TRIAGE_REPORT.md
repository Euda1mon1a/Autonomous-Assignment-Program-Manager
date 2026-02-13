# Opus 4.6 (Mac Mini) Branch Triage Report

> **Date:** 2026-02-13
> **Source:** 19 `claude/*` branches on `mini` remote
> **Agent:** Claude Opus 4.6 running on Mac Mini
> **Reviewer:** Claude Opus 4.6 (main workstation) + human review

---

## Summary

| Category | Count | Outcome |
|----------|-------|---------|
| **Wheat — clean merge** | 2 | Merged directly (integration tests, route validation tests) |
| **Wheat — cherry-picked** | 12 | Extracted specific files from 12 branches |
| **Chaff — confirmed** | 5 | No value; delete branches |
| **Total** | 19 | 14 wheat (74%), 5 chaff (26%) |

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
