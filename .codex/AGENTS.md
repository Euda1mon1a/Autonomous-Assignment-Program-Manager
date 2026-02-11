# Codex Agent Instructions

> Codex reads this file before starting work. See also: `docs/development/AGENTS.md` for monitoring patterns.

---

## The Planning Cycle (OPERATING PROCEDURE)

Every automation run and interactive session follows this cycle. Do not skip steps.

### 1. Research — What's the current state?

Before touching code, build situational awareness:

- **Read `RECENT_ACTIVITY.md`** (project root) — auto-generated every 15 min by `sync-claude-activity.sh`. Shows what Claude coder completed in the last 24h and what branches are active.
- **Read `TODO.md`** — shared task list. Items marked `[x]` are done. Items with `(claude-coder)` were completed by the other agent.
- **Read `FEEDBACK.md`** (`.codex/FEEDBACK.md`) — learnings from previous runs. Check for patterns, known issues, and suggestions from your past self.
- **Check branches**: `git branch -a | grep 'claude/\|codex/'` — see what's in flight.
- **Fetch from Mini**: `git fetch mini` — get Claude's latest work.

### 2. Plan — What should I work on?

Based on research, decide what's highest-impact and NOT already done:

- **Skip** anything listed as DONE in `RECENT_ACTIVITY.md`
- **Skip** anything marked `[x]` in `TODO.md`
- **Skip** anything with an active `claude/*` branch covering the same area
- **Prefer** work that complements Claude's output (Claude does mechanical fixes; you do deeper analysis)
- **Prefer** work that Claude can't do (ACGME audits, contract sync, test gap detection — these need the full AAPM context that only runs on the laptop)

### 3. Execute — Do the work

- Work on a `codex/*` branch, never directly on `main`
- One focused change per branch
- Run tests/lints to validate before committing

### 4. Validate — Did it work?

- Check that tests pass
- Check that the change is meaningful (not trivial/cosmetic)
- If the automation found nothing to do, that's a valid outcome — log it

### 5. Feedback — What did I learn?

**Append findings to `.codex/FEEDBACK.md`** after every run:

```markdown
## [automation-name] — YYYY-MM-DD HH:MM

**Outcome**: [completed | nothing-to-do | skipped-duplicate | failed]
**Overlap with Claude**: [yes/no — describe if yes]
**Insight**: [what did this run teach us?]
**Suggestion**: [anything to improve for next run?]
```

This creates a persistent learning loop. Future runs read FEEDBACK.md in step 1 and avoid repeating mistakes.

---

## Multi-Agent Coordination

You are not the only agent working on this codebase. A **Claude Code agent (Opus 4.6)** runs autonomously on a Mac Mini (always-on server) via `claude-coder.sh`.

### Order of Operations

1. **Claude coder** — runs throughout the day on the Mac Mini, picks tasks from `TODO.md`, works in git worktrees, commits to `claude/*` branches, pushes to bare repo
2. **Codex** — runs during sleeping hours (~0100-0500 HST), performs automated health checks, code quality sweeps, deeper analysis
3. **Human** — reviews accumulated branches in the morning

### Branch Naming

| Agent | Prefix | Example |
|-------|--------|---------|
| Claude | `claude/` | `claude/2026-02-10-fix-import-errors` |
| Codex | `codex/` | `codex/type-coverage-expansion` |
| Human | feature/ | `feature/new-swap-ui` |

### Complementary Roles

| Domain | Claude (Mini, daytime) | Codex (Laptop, nighttime) |
|--------|----------------------|--------------------------|
| TODO.md mechanical tasks | Primary executor | Skip — Claude handles these |
| Code quality sweeps | Via TODO items | Deeper analysis (mypy, bandit, contract sync) |
| Bug scanning | Light (task-based) | Deep (daily-bug-scan) |
| Architecture drift | No | Yes — contract sync, constraint drift |
| ACGME compliance | No | Yes — dedicated automations |
| Security sweeps | Pre-merge gate only | Yes — bandit, PII health |
| Test gap detection | No | Yes |
| Documentation freshness | No | Yes |
| Morning brief | No | Yes — 0500 HST summary |

### Conflict Resolution

If a `claude/*` branch touches files you want to modify:
- **Prefer Claude's version** for mechanical fixes (imports, lint, types)
- **Build on it** if you have deeper analysis to add
- **Skip it** if the work is equivalent
- **Log it** in FEEDBACK.md so the pattern is tracked

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
