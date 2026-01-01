***REMOVED*** CCW Burn Protocol: Safe Parallel Task Execution

> **Purpose:** Prevent cascading failures during high-volume CCW task burns
> **Created:** 2025-12-31
> **Source:** Postmortem from 1000-task burn

---

***REMOVED******REMOVED*** Executive Summary

CCW (Claude Code Web) can generate code but cannot validate it locally. This protocol ensures validation gates catch issues early before they compound across hundreds of files.

---

***REMOVED******REMOVED*** The Core Problem

```
CCW generates code → Looks correct → No local validation → Pattern replicates
                                                              ↓
                                                    100+ files with same bug
```

**Solution:** Insert validation gates to create feedback loops.

---

***REMOVED******REMOVED*** Burn Execution Protocol

***REMOVED******REMOVED******REMOVED*** Phase 1: Pre-Burn Checklist

Before starting any CCW burn:

```bash
***REMOVED*** 1. Verify clean baseline
npm run build        ***REMOVED*** Must pass
npm run type-check   ***REMOVED*** Must pass
npm test             ***REMOVED*** Note current state

***REMOVED*** 2. Create burn branch
git checkout -b ccw/burn-$(date +%Y%m%d)
```

***REMOVED******REMOVED******REMOVED*** Phase 2: Burn Execution with Gates

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

***REMOVED******REMOVED*** Common CCW Failure Patterns

| Pattern | Symptom | Root Cause | Fix |
|---------|---------|------------|-----|
| "Cannot find name 'jest'" | 100+ type errors | Missing @types/jest | `npm i -D @types/jest` |
| "Property X does not exist" | Type mismatch | Wrong property name | Check type definition |
| "Module not found" | Import errors | Wrong import path | Verify file exists |
| "JSX in .ts file" | Parse errors | Wrong file extension | Rename .ts → .tsx |
| "invalid-syntax" | `await sawait ervice` | Token concatenation bug | Manual find/replace |

***REMOVED******REMOVED******REMOVED*** Token Concatenation Bug (Critical)

CCW can corrupt Python/JS by incorrectly splitting tokens:

```python
***REMOVED*** CCW wrote:
result = await sawait ervice.validate()
***REMOVED***              ^^^^^^ ^^^^^^^  <- corrupted

***REMOVED*** Should be:
result = await service.validate()
```

**Detection:**
```bash
grep -rE "[a-z]await [a-z]" . --include="*.py"
```

---

***REMOVED******REMOVED*** CCW Task Constraints

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

***REMOVED******REMOVED*** Quick Reference

```
PRE-BURN:   npm run build && npm run type-check  (must pass)
DURING:     Validate every 20 tasks
POST-BURN:  Full validation suite
FAILURE:    Count unique errors, fix root cause, verify
```

---

*Protocol established after 1000-task burn revealed validation gap.*
