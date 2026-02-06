# CCW Burn Protocol: Safe Parallel Task Execution

> **Purpose:** Prevent cascading failures during high-volume CCW task burns
> **Created:** 2025-12-31
> **Source:** Postmortem from 1000-task burn

---

## Executive Summary

CCW (Claude Code Web) can generate code but cannot validate it locally. This protocol ensures validation gates catch issues early before they compound across hundreds of files.

---

## The Core Problem

```
CCW generates code → Looks correct → No local validation → Pattern replicates
                                                              ↓
                                                    100+ files with same bug
```

**Solution:** Insert validation gates to create feedback loops.

---

## Burn Execution Protocol

### Phase 1: Pre-Burn Checklist

Before starting any CCW burn:

```bash
# 1. Verify clean baseline
npm run build        # Must pass
npm run type-check   # Must pass
npm test             # Note current state

# 2. Create burn branch
git checkout -b ccw/burn-$(date +%Y%m%d)
```

### Phase 2: Burn Execution with Gates

**Gate Frequency:** Every 20 tasks OR every new file pattern

```
Tasks 1-20   → Validation Gate → Pass? Continue : Stop & Fix
Tasks 21-40  → Validation Gate → Pass? Continue : Stop & Fix
...
```

**Validation Gate:**
```bash
./.claude/scripts/ccw-validation-gate.sh
```

---

## Common CCW Failure Patterns

| Pattern | Symptom | Root Cause | Fix |
|---------|---------|------------|-----|
| "Cannot find name 'jest'" | 100+ type errors | Missing @types/jest | `npm i -D @types/jest` |
| "Property X does not exist" | Type mismatch | Wrong property name | Check type definition |
| "Module not found" | Import errors | Wrong import path | Verify file exists |
| "JSX in .ts file" | Parse errors | Wrong file extension | Rename .ts → .tsx |
| "invalid-syntax" | `await sawait ervice` | Token concatenation bug | Manual find/replace |

### Token Concatenation Bug (Critical)

CCW can corrupt Python/JS by incorrectly splitting tokens:

```python
# CCW wrote:
result = await sawait ervice.validate()
#              ^^^^^^ ^^^^^^^  <- corrupted

# Should be:
result = await service.validate()
```

**Detection:**
```bash
grep -rE "[a-z]await [a-z]" . --include="*.py"
```

---

## CCW Task Constraints

Include in CCW prompts:

```yaml
constraints:
  - Include explicit imports (no implicit globals)
  - Use .tsx extension for files with JSX
  - Don't assume @types/* packages exist
  - Don't remove useMemo/useCallback
  - Avoid `any` type - use `unknown` or proper types
```

---

---

## Pre-Merge Quality Gates

### Decontamination Checklist

Before merging any CCW burn branch to main:

```bash
# 1. Run stack audit
python3 scripts/ops/stack_audit.py

# Must show: ✅ GREEN status (all checks pass)
# If YELLOW or RED: Fix issues before merging
```

**Stack audit validates:**
- Frontend type-check, lint, build
- Backend lint (Ruff), type-check (mypy)
- Migration state consistency
- Docker container health
- API endpoint health
- Backup freshness

### Error Signature Detection

Run automated detection for known CCW error patterns:

```bash
# Token concatenation
grep -rE "[a-z]await [a-z]" backend --include="*.py" | grep -v venv

# Missing imports (if file has async/await but no import)
grep -l "async def\|await " backend/**/*.py | \
  xargs grep -L "from typing import\|import asyncio"

# Orphaned test files (tests without corresponding source)
# Manual review of git diff --name-status
```

---

## Rollback Procedure

If CCW burn introduces issues after merge:

### Option 1: Revert Merge Commit (Safest)

```bash
# Find the merge commit
git log --oneline --merges -10

# Revert the merge (creates new revert commit)
git revert -m 1 <merge-commit-sha>

# Push revert
git push origin main
```

### Option 2: Reset to Pre-Merge State (Dangerous)

**⚠️ Only if merge was very recent and no one else pulled**

```bash
# Find the commit before the merge
git log --oneline -10

# Reset main to pre-merge state
git reset --hard <pre-merge-commit-sha>

# Force push (requires approval)
git push --force origin main
```

### Option 3: Cherry-Pick Good Changes

If CCW burn has both good and bad changes:

```bash
# Create new branch from main (before merge)
git checkout -b ccw/burn-cherry-pick <pre-merge-commit-sha>

# Cherry-pick specific good commits from burn branch
git cherry-pick <good-commit-1> <good-commit-2>

# Test, then merge
python3 scripts/ops/stack_audit.py
git checkout main && git merge ccw/burn-cherry-pick
```

---

## Quick Reference

```
PRE-BURN:    npm run build && npm run type-check  (must pass)
             git checkout -b ccw/burn-$(date +%Y%m%d)

DURING:      Validate every 20 tasks via ccw-validation-gate.sh

PRE-MERGE:   python3 scripts/ops/stack_audit.py  (must be GREEN)
             Error signature detection (token corruption, missing imports)

POST-MERGE:  Verify CI passes, run smoke tests

ROLLBACK:    git revert -m 1 <merge-commit> (safest)
             OR git reset --hard (dangerous, needs approval)
```

---

*Protocol established after 1000-task burn revealed validation gap.*
*Updated 2026-01-04: Added pre-merge gates, stack audit requirement, rollback procedures.*
