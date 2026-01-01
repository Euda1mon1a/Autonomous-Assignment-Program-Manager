# CCW Burn Postmortem: 1000-Task Parallel Execution

> **Date:** 2025-12-31
> **Issue:** Type-check failures across 134 files
> **Root Cause:** Missing `@types/jest`
> **Fix Time:** ~1 minute
> **Diagnostic Time:** ~30 minutes

---

## The Illusion of Complexity

**What it looked like:** 134 files failing, 6-7 hour remediation estimate

**What it actually was:** 1 missing package + 2 missing imports

---

## Root Cause Chain

```
@types/jest not in package.json
         ↓
TypeScript doesn't recognize `jest` global
         ↓
Every jest.fn() call = "Cannot find name 'jest'"
         ↓
134 files × same error = apparent catastrophe
```

---

## Why CCW Made This Mistake

CCW operates **without local execution context**:

| CCW Can Do | CCW Cannot Do |
|------------|---------------|
| Generate code | Run `npm install` |
| Read files | Run `npm run type-check` |
| Search patterns | Run `npm test` |
| Follow patterns | Verify patterns work |

**The generated code was syntactically valid JavaScript** - it just didn't type-check because TypeScript needs the type definitions.

---

## The Actual Fix

```bash
# Step 1: Add types (5 seconds)
npm install --save-dev @types/jest

# Step 2: Add imports to 2 mock files (30 seconds)
# frontend/src/__mocks__/next/navigation.ts
# frontend/src/__mocks__/next/router.ts
import { jest } from '@jest/globals';
```

**Total: 3 files changed, ~1 minute of work**

---

## Key Insight

> **Volume obscures simplicity.**
>
> 134 identical errors ≠ 134 different problems.
> Pattern-match first, count second.

---

## Prevention Protocol

### For Future CCW Burns

**MANDATORY: Validation Gate Every 20 Tasks**

```bash
# Run after every ~20 CCW-generated files
npm run type-check
npm run build
```

If either fails → STOP → diagnose → fix root cause → resume

### CCW Task Prompt Additions

```yaml
constraints:
  - Verify @types packages exist for any testing library used
  - Include imports for globals (jest, expect, describe, it)
  - Check tsconfig.json for type roots
```

---

## Metrics

| Metric | Value |
|--------|-------|
| Tasks executed | 1000 |
| Files affected | 134 |
| Unique root causes | 1 |
| Fix complexity | Trivial |
| Time to diagnose | 30 min |
| Time to fix | 1 min |

---

## Lesson Learned

**CCW parallel burns are safe IF you add validation gates.**

The problem wasn't parallelization - it was running 1000 tasks with zero feedback loops. A single `npm run type-check` after task #20 would have caught this.

---

*Document created: 2025-12-31*
*Ready for next burn with validation gates*
