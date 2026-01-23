# CCW Cherry-Pick Instructions: Sacred Timeline Consolidation

**Date:** 2026-01-01
**Prepared by:** ORCHESTRATOR (Session 044)
**For:** Claude Code Web (CCW)

---

## Mission

Cherry-pick commits from 8 sacred timeline branches into your branch, then create PR to main.

---

## Cherry-Pick Order (Phase 1 - Low Risk, 16 commits)

Execute in this exact order to minimize conflicts:

### 1. stream-9-YLZJt (1 commit) - Controller Tests
```bash
git cherry-pick origin/claude/stream-9-YLZJt
```
- **Commit:** New test files only
- **Risk:** LOW (no existing file conflicts)
- **Content:** 8 controller test files (+3,787 lines)

### 2. stream-4-wgB7A (1 commit) - Swap Docstrings
```bash
git cherry-pick origin/claude/stream-4-wgB7A
```
- **Commit:** `7b5ebc57` - docs(backend): Add comprehensive Google-style docstrings to swap module
- **Risk:** LOW (documentation only)
- **Content:** swap.py, swap_executor.py docstrings

### 3. stream-6-VQUI0 (9 commits) - Mission Command + Skills
```bash
git cherry-pick origin/claude/stream-6-VQUI0~8..origin/claude/stream-6-VQUI0
```
Or individually:
```bash
git cherry-pick f6eb1ee2  # feat(agents): Add Mission Command sections to 10 agent specs
git cherry-pick 27897d09  # feat(agents): Add Mission Command sections to 9 more agent specs (batch 2)
git cherry-pick ec7e50e8  # feat(agents): Add Mission Command sections to 4 more agent specs (batch 3)
git cherry-pick 0cd9c497  # feat(agents): Add Mission Command sections to coordinator agents (batch B)
git cherry-pick 4f8668e9  # feat(agents): Add Mission Command sections to specialist agents (batch E)
git cherry-pick b6ba0e48  # feat(agents): Add Mission Command sections to specialist agents (batch C)
git cherry-pick b8fdf371  # feat(agents): Add Mission Command sections to coordinator agents (batch A)
git cherry-pick c27329f0  # feat(agents): Add Mission Command sections to specialist agents (batch D)
git cherry-pick 87fb1a86  # feat(skills): Add examples and workflows to 5 core skills
```
- **Risk:** LOW (self-contained to .claude/ directory)
- **Content:** 48+ agent specs, 5 skill enhancements

### 4. stream-2-development-oAN6V (2 commits) - Stub Replacements
```bash
git cherry-pick origin/claude/stream-2-development-oAN6V~1..origin/claude/stream-2-development-oAN6V
```
Or individually:
```bash
git cherry-pick fb447712  # feat(stub-replacement): Replace placeholders with production implementations
git cherry-pick 4f268918  # feat(stub-replacement): Replace placeholders in 5 additional modules
```
- **Risk:** LOW
- **Content:** 13 backend modules with production implementations

### 5. stream-8-H2lJj (3 commits) - Accessibility
```bash
git cherry-pick origin/claude/stream-8-H2lJj~2..origin/claude/stream-8-H2lJj
```
Or individually:
```bash
git cherry-pick 280ae25d  # feat(a11y): Add comprehensive accessibility improvements to frontend components
git cherry-pick 25928659  # feat(a11y): Add accessibility to UI components
git cherry-pick 17cd540c  # feat(a11y): Comprehensive accessibility improvements across 67+ frontend components
```
- **Risk:** MEDIUM (80 frontend files)
- **Content:** ARIA labels, keyboard nav, screen reader support

---

## Phase 2 (Optional - Choose ONE)

### Option A: analyze-improve-repo-16YVp (23 commits)
Large burn with 9 streams of improvements. May overlap with Phase 1.

### Option B: analyze-improve-repo-streams-DUeMr (1 commit)
Single massive commit with comprehensive improvements. May overlap with Option A.

**Recommendation:** Skip Phase 2 for now. Phase 1 captures most value.

---

## Phase 3 (Selective - Advanced)

### review-search-party-protocol-wU0i1
Only cherry-pick these specific improvements:
- Transaction locking fixes
- Distributed lock module
- Security improvements

**Skip:** Session documentation/consolidation commits

---

## Conflict Resolution

If conflicts occur:
1. Use `git checkout --theirs <file>` for incoming changes
2. `git add <file>`
3. `git cherry-pick --continue`

---

## After Cherry-Pick

1. Run tests: `cd backend && pytest`
2. Run linters: `cd backend && ruff check . --fix`
3. Run frontend: `cd frontend && npm run build && npm run lint`
4. Create PR to main

---

## Expected Totals

| Phase | Commits | Files | Risk |
|-------|---------|-------|------|
| Phase 1 | 16 | ~156 | LOW-MEDIUM |
| Phase 2 | 1-23 | ~157 | MEDIUM |
| Phase 3 | ~3 | selective | HIGH |

**Recommended:** Phase 1 only (16 commits)

---

## Branch Cleanup (After PR Merge)

These branches can be deleted after successful merge:
- `origin/claude/stream-2-development-oAN6V`
- `origin/claude/stream-4-wgB7A`
- `origin/claude/stream-6-VQUI0`
- `origin/claude/stream-8-H2lJj`
- `origin/claude/stream-9-YLZJt`

Defer deletion (not cherry-picked):
- `origin/claude/analyze-improve-repo-16YVp`
- `origin/claude/analyze-improve-repo-streams-DUeMr`
- `origin/claude/review-search-party-protocol-wU0i1`

---

*Prepared by SEARCH_PARTY reconnaissance (120 probes deployed)*
