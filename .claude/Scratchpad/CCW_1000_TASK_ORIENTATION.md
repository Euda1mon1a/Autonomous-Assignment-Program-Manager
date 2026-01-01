# CCW 1000-Task Orientation: Post-SEARCH_PARTY Intel

> **Date:** 2025-12-31
> **Source:** G2_RECON 12-team reconnaissance
> **Target:** 1000 parallelizable CCW tasks

---

## ⚠️ MANDATORY: Read Before Burning

**READ FIRST:** `.claude/protocols/CCW_BURN_PROTOCOL.md`

### Critical Constraints (From 2025-12-31 Postmortem)

| Constraint | Reason |
|------------|--------|
| Include `import { jest } from '@jest/globals'` | TypeScript needs explicit import |
| Use `.tsx` for files with JSX | `.ts` causes parse errors |
| Don't assume `@types/*` packages exist | Verify or specify installation |
| Don't remove `useMemo`/`useCallback` | Performance regressions |
| Avoid `any` type | Use `unknown` or proper types |

### Validation Gate (Every 20 Tasks)

```bash
./.claude/scripts/ccw-validation-gate.sh
```

If gate fails → STOP → diagnose root cause → fix → resume

---

## Executive Summary

G-2 Intelligence assessed codebase at **B+ health** with targeted improvement areas. CCW tasks focus on code generation that doesn't require local execution.

---

## 5 Workstreams (1000 Tasks Total)

### Stream 1: Frontend Component Tests (400 tasks)
**Priority:** P0 | **Parallelism:** HIGH

**Scope:**
- 232 components, ~25 have tests (10.8% coverage)
- Each component needs: render test, interaction test, error state test

**Targets:**
| Directory | Components | Tasks |
|-----------|------------|-------|
| `src/components/` root | 24 | 72 |
| `src/components/schedule/` | 25 | 75 |
| `src/components/features/` | 59 | 177 |
| `src/components/ui/` | 15 | 45 |
| `src/components/admin/` | 10 | 30 |

**Template:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ComponentName } from './ComponentName';

describe('ComponentName', () => {
  it('renders without crashing', () => {...});
  it('handles user interaction', () => {...});
  it('displays error state correctly', () => {...});
});
```

---

### Stream 2: TypeScript Type Safety (200 tasks)
**Priority:** P1 | **Parallelism:** HIGH

**CRITICAL (Block CI):**
| File | Issue | Tasks |
|------|-------|-------|
| `src/__mocks__/next/navigation.ts` | Jest types missing | 5 |
| `src/__mocks__/next/router.ts` | Jest types missing | 5 |
| `src/test-utils/index.tsx` | expect/jest namespace | 5 |

**HIGH (ESLint warnings):**
| File | `any` Count | Tasks |
|------|-------------|-------|
| `src/utils/debounce.ts` | 25 | 15 |
| `src/utils/memoization.ts` | 8 | 10 |
| `src/utils/lazy-loader.ts` | 7 | 8 |
| `src/types/chat.ts` | 4 | 5 |
| `src/lib/validation/*.ts` | 15 | 20 |
| `src/hooks/*.ts` | 30+ | 50 |
| `src/components/**/*.tsx` | 60+ | 77 |

---

### Stream 3: Hook Tests (100 tasks)
**Priority:** P2 | **Parallelism:** HIGH

**Untested Hooks (12):**
| Hook | Complexity | Tasks |
|------|------------|-------|
| useAuth | HIGH | 12 |
| useAdminScheduling | HIGH | 10 |
| useClaudeChat | MEDIUM | 8 |
| useGameTheory | MEDIUM | 8 |
| useHealth | LOW | 5 |
| useInfiniteQuery | MEDIUM | 8 |
| useOptimisticUpdate | HIGH | 10 |
| useProcedures | MEDIUM | 8 |
| useRAG | MEDIUM | 8 |
| useResilience | HIGH | 10 |
| useWebSocket | HIGH | 10 |
| useAdminUsers | LOW | 3 |

---

### Stream 4: Backend Docstrings (200 tasks)
**Priority:** P3 | **Parallelism:** MEDIUM

**Scope:** 111 service files need Google-style docstrings

**Targets:**
| Directory | Files | Functions | Tasks |
|-----------|-------|-----------|-------|
| `app/services/` | 45 | ~200 | 80 |
| `app/scheduling/` | 30 | ~150 | 60 |
| `app/resilience/` | 20 | ~100 | 40 |
| `app/api/routes/` | 16 | ~80 | 20 |

**Template:**
```python
def function_name(param1: Type, param2: Type) -> ReturnType:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this happens
    """
```

---

### Stream 5: TODO/FIXME Resolution (100 tasks)
**Priority:** P4 | **Parallelism:** MEDIUM

**High-Value Targets:**
| File | TODOs | Tasks |
|------|-------|-------|
| `scheduling/penrose_efficiency.py` | 10 | 15 |
| `scheduling/free_energy_integration.py` | 2 | 5 |
| `scheduling/quantum/qubo_template_selector.py` | 1 | 3 |
| `resilience/thermodynamics.py` | 4 | 8 |
| `api/routes/*.py` | 9 | 15 |
| `services/swap_validation.py` | 2 | 5 |

**NotImplementedError Stubs (20+ files):**
| Category | Files | Tasks |
|----------|-------|-------|
| Analytics stubs | 5 | 15 |
| Export stubs | 3 | 10 |
| Monitoring stubs | 4 | 12 |
| Other stubs | 8 | 12 |

---

## Task Distribution Summary

| Stream | Tasks | % of Total |
|--------|-------|------------|
| Frontend Component Tests | 400 | 40% |
| TypeScript Type Safety | 200 | 20% |
| Hook Tests | 100 | 10% |
| Backend Docstrings | 200 | 20% |
| TODO Resolution | 100 | 10% |
| **TOTAL** | **1000** | 100% |

---

## Wave Execution Plan

### Wave 1: Critical Path (Parallel)
- Stream 2 CRITICAL tasks (15 tasks) - Unblock CI type-check
- Stream 1 first 50 components

### Wave 2: High Impact (Parallel)
- Stream 1 remaining 350 component tests
- Stream 2 remaining 185 type fixes
- Stream 3 all 100 hook tests

### Wave 3: Polish (Parallel)
- Stream 4 all 200 docstrings
- Stream 5 all 100 TODO resolutions

---

## CCW Session Allocation

| Session | Stream | Task Range | Est. Output |
|---------|--------|------------|-------------|
| 1-4 | Frontend Tests | 1-400 | 100/session |
| 5-6 | TypeScript | 401-600 | 100/session |
| 7 | Hook Tests | 601-700 | 100/session |
| 8-9 | Docstrings | 701-900 | 100/session |
| 10 | TODOs | 901-1000 | 100/session |

---

## Quality Gates

Each CCW output must:
1. Follow existing patterns in codebase
2. Use proper types (no new `any`)
3. Include error handling
4. Match CLAUDE.md style guidelines

---

## Files CCW Cannot Touch

- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/db/session.py`
- Any `.env` files
- Existing migrations

---

*Generated from G-2 SEARCH_PARTY reconnaissance*
*Ready for CCW deployment*
