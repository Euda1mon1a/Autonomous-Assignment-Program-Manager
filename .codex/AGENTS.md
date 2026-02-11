# Codex Agent Instructions

> Codex reads this file before starting work. See also: `docs/development/AGENTS.md` for monitoring patterns.

---

## Multi-Agent Coordination (IMPORTANT)

You are not the only agent working on this codebase. A **Claude Code agent (Opus 4.6)** runs autonomously on a Mac Mini (always-on server) via a cron-based coder script (`claude-coder.sh`). Understanding the coordination model prevents duplicate work, merge conflicts, and wasted effort.

### Order of Operations

1. **Claude coder runs first** — throughout the day on the Mac Mini, picking tasks from `TODO.md`, working in git worktrees, committing to `claude/*` branches, pushing to a bare repo (`~/repos/aapm.git` on Mini).
2. **Codex runs second** — during sleeping hours (~2300-0500 HST), performing automated health checks, code quality sweeps, and focused improvements.
3. **Human reviews** — in the morning, reviewing accumulated `claude/*` and `codex/*` branches.

### Branch Naming

| Agent | Branch prefix | Example |
|-------|--------------|---------|
| Claude coder | `claude/` | `claude/2026-02-10-fix-import-errors` |
| Codex automations | `codex/` | `codex/type-coverage-expansion` |
| Human/interactive | feature branches | `feature/new-swap-ui` |

**Never commit directly to `main`.** Both agents use feature branches.

### Shared State: TODO.md

Both agents read `TODO.md` in the project root. Claude marks tasks `[x]` when complete. Before starting a task:
1. Check if it's already marked complete in `TODO.md`
2. Check for existing `claude/*` branches that may have already addressed it: `git branch -r | grep claude/`
3. If Claude already did the work, skip it or build on it

### Pulling Claude's Work

Claude pushes to the Mac Mini bare repo. The laptop has a `mini` remote configured:
```bash
git fetch mini
git log mini/main..HEAD   # see what's on Mini but not here
```

Before starting work, especially on tasks that overlap with Claude's TODO.md items, fetch from Mini to avoid redoing work.

### What Claude Handles vs What Codex Handles

| Domain | Claude (Mini, daytime) | Codex (Laptop, nighttime) |
|--------|----------------------|--------------------------|
| TODO.md mechanical tasks | Yes — primary executor | No — skip items Claude is doing |
| Code quality (lint, types, format) | Yes — via TODO items | Yes — deeper sweeps |
| Bug scanning | Light (task-based) | Deep (daily-bug-scan automation) |
| Architecture drift | No | Yes — contract sync, constraint drift |
| ACGME compliance audits | No | Yes — dedicated automations |
| Security sweeps | Pre-merge gate only | Yes — bandit, PII health |
| Test gap detection | No | Yes — dedicated automation |
| Documentation freshness | No | Yes — dedicated automation |
| Morning brief | No | Yes — 0500 HST summary |

### Conflict Resolution

If you find a `claude/*` branch that touches the same files you want to modify:
- **Prefer Claude's version** if it's a mechanical fix (imports, lint, types)
- **Build on it** if you have deeper analysis to add
- **Skip it** if the work is equivalent
- Log what you found in your automation memory.md so the pattern is tracked

---

## Project Context

**Residency Scheduler** - Military medical residency scheduling with ACGME compliance.

- **Backend**: FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery/Redis
- **Frontend**: Next.js 14, React 18, TailwindCSS
- **MCP Server**: 34+ AI tools for scheduling, validation, resilience

---

## Conventions

See `docs/development/AGENTS.md` for:
- Code rot detection patterns
- Consistency drift checks
- Type safety enforcement
- Performance pattern detection

---

## API Type Contract (CRITICAL)

### Naming Convention
- **Backend (Python):** snake_case everywhere
- **Frontend (TypeScript):** camelCase for interface properties
- **Axios interceptor converts automatically** (snake_case ↔ camelCase)

```typescript
// ✓ CORRECT - TypeScript interfaces use camelCase
interface Person {
  pgyLevel: number;
  createdAt: string;
  isActive: boolean;
}

// ✗ WRONG - will cause undefined at runtime
interface Person {
  pgy_level: number;  // Axios converts to pgyLevel, this won't match
}
```

### Enum Values Stay snake_case (Gorgon's Gaze)
Axios converts KEYS only, not VALUES. Database stores snake_case values.

```typescript
// ✓ CORRECT
type SwapType = 'one_to_one' | 'absorb';

// ✗ WRONG - will never match API responses
type SwapType = 'oneToOne' | 'absorb';
```

### URL Query Parameters Stay snake_case (Couatl Killer)
URL params go directly to API - interceptor doesn't convert them.

```typescript
// ✓ CORRECT
router.push(`/schedule?block_id=${id}&include_inactive=true`);

// ✗ WRONG
router.push(`/schedule?blockId=${id}&includeInactive=true`);
```

### Type Regeneration (STANDING ORDER)
After ANY backend schema change (`backend/app/schemas/*.py`):

```bash
cd frontend && npm run generate:types
git add frontend/src/types/api-generated.ts
```

Pre-commit hooks (`api-contract`, `modron-march`) will block if types drift.

---

## Full Guidelines

See `CLAUDE.md` in project root for complete project guidelines including:
- Architecture patterns
- Security requirements
- Testing requirements
- Git workflow
