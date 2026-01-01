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

# 2. Document baseline
echo "Build: PASS, Type-check: PASS, Tests: X passing" > burn-baseline.txt

# 3. Create burn branch
git checkout -b ccw/burn-$(date +%Y%m%d)
```

### Phase 2: Burn Execution with Gates

**Gate Frequency:** Every 20 tasks OR every new file pattern

```
Tasks 1-20   → Validation Gate → Pass? Continue : Stop & Fix
Tasks 21-40  → Validation Gate → Pass? Continue : Stop & Fix
Tasks 41-60  → Validation Gate → Pass? Continue : Stop & Fix
...
```

**Validation Gate Script:**

```bash
#!/bin/bash
# .claude/scripts/ccw-validation-gate.sh

echo "=== CCW Validation Gate ==="

# Type check (catches missing types, bad imports)
npm run type-check
if [ $? -ne 0 ]; then
    echo "❌ TYPE-CHECK FAILED - Stop burn, diagnose, fix"
    exit 1
fi

# Build (catches module resolution, JSX issues)
npm run build 2>&1 | tail -5
if [ $? -ne 0 ]; then
    echo "❌ BUILD FAILED - Stop burn, diagnose, fix"
    exit 1
fi

echo "✅ Validation gate passed - Continue burn"
```

### Phase 3: Post-Burn Validation

After burn completes:

```bash
# Full validation suite
npm run type-check   # Must pass
npm run build        # Must pass
npm run lint         # Document warnings
npm test             # Compare to baseline

# Commit if all pass
git add -A
git commit -m "feat: CCW burn $(date +%Y%m%d) - [description]"
```

---

## Common CCW Failure Patterns

| Pattern | Symptom | Root Cause | Fix |
|---------|---------|------------|-----|
| "Cannot find name 'jest'" | 100+ type errors | Missing @types/jest | `npm i -D @types/jest` |
| "Property X does not exist" | Type mismatch | Using wrong property name | Check actual type definition |
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
# Python
grep -rE "[a-z]await [a-z]" . --include="*.py"

# JavaScript/TypeScript
grep -rE "[a-z]await [a-z]" . --include="*.ts" --include="*.tsx"
```

**Fix:** Manual find/replace, no auto-fix available.

---

## CCW Task Prompt Template

Include these constraints in CCW prompts:

```markdown
## CCW Task: [Description]

### Constraints (MUST follow)
- [ ] Verify @types packages exist for testing libraries
- [ ] Include explicit imports (no implicit globals)
- [ ] Use .tsx extension for files with JSX
- [ ] Match existing patterns in codebase
- [ ] Check type definitions before using property names

### Anti-Patterns (MUST avoid)
- [ ] Don't use `any` type
- [ ] Don't remove useMemo/useCallback
- [ ] Don't assume globals are available
- [ ] Don't create new patterns without checking existing ones
```

---

## Burn Size Guidelines

| Burn Size | Tasks | Gate Frequency | Risk Level |
|-----------|-------|----------------|------------|
| Small | 1-50 | Every 10 | Low |
| Medium | 50-200 | Every 20 | Medium |
| Large | 200-500 | Every 20 | High |
| Marathon | 500+ | Every 20 + hourly full check | Very High |

---

## Recovery Protocol

If burn introduces failures:

### Step 1: Diagnose (Don't Panic)

```bash
# Count unique errors (not total errors)
npm run type-check 2>&1 | grep "error TS" | sort -u | wc -l

# Usually: Many errors = Few root causes
```

### Step 2: Pattern Match

Look for the SAME error across multiple files:
- "Cannot find name X" → Missing import or @types package
- "Property X does not exist" → Wrong property name
- "Module not found" → Path issue

### Step 3: Fix Root Cause

Fix ONE file, then apply same fix to all affected files.

### Step 4: Verify

```bash
npm run type-check  # Should now pass
npm run build       # Should now pass
```

---

## Quick Reference

```
PRE-BURN:   npm run build && npm run type-check  (must pass)
DURING:     Validate every 20 tasks
POST-BURN:  Full validation suite
FAILURE:    Count unique errors, fix root cause, verify
```

---

## Related Documents

- `.claude/Scratchpad/CCW_BURN_POSTMORTEM.md` - Detailed postmortem
- `.claude/Scratchpad/CCW_1000_TASK_ORIENTATION.md` - Task workstreams
- `.claude/docs/CCW_PARALLELIZATION_ANALYSIS.md` - Architecture comparison

---

*Protocol established after 1000-task burn revealed validation gap.*
*Single missing package caused 134 file failures.*
*Prevention: Validate early, validate often.*
