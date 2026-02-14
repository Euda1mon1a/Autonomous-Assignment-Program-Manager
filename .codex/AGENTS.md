# Codex Agent Instructions

> Codex reads this file before starting work. These rules are MANDATORY.
> See also: `docs/development/AGENTS.md` for monitoring patterns.

---

## HARD BOUNDARIES (NEVER CROSS)

These are non-negotiable. Violating any of these makes your entire output worthless and wastes human review time. If in doubt, do NOT make the change.

### Validation & Types
- **NEVER** remove or relax Pydantic validation constraints (`min_length`, `max_length`, `ge`, `le`, `regex`, `pattern`)
- **NEVER** weaken type annotations (e.g., `dict[str, int]` → `dict[str, Any]`)
- **NEVER** add `extra="allow"` or `model_config = ConfigDict(extra="allow")` to Pydantic models
- **NEVER** change `Literal[...]` types to plain `str`

### Error Handling & Security
- **NEVER** change error messages from generic to `str(e)` — this leaks internal details to API consumers
- **NEVER** add try/except blocks that silently swallow errors or fall back to alternate behavior — this creates ghost state (e.g., job persisted but never scheduled)
- **NEVER** reduce authentication or authorization checks
- **NEVER** remove rate limiting
- **NEVER** log sensitive data (names, schedules, PII, credentials)
- **NEVER** commit real resident/faculty names, schedule assignments, or deployment data (OPSEC/PERSEC — military medical context)

### Code Structure
- **NEVER** change function signatures or return types without updating ALL callers
- **NEVER** register a FastAPI router at multiple prefixes — this creates duplicate OpenAPI entries and namespace collisions
- **NEVER** change algorithm thresholds, constants, or numerical parameters unless that is the explicit purpose of your task
- **NEVER** modify more than 30 files in a single branch — if your change touches more, your scope is too broad

### Scheduling & Compliance
- **NEVER** modify scheduling logic, ACGME compliance rules, or constraint definitions
- **NEVER** modify database models without creating an Alembic migration
- **NEVER** edit existing Alembic migration files — create new ones to fix issues

---

## Code Change Safety Classification

Before making any change, classify it:

| Change Type | Safety | Rule |
|---|---|---|
| Add `from e` to exception handlers | SAFE | Always do this |
| Reorder imports alphabetically | SAFE | Always do this |
| Fix `datetime.utcnow()` → `datetime.now(UTC)` | SAFE | But fix BOTH sides of comparisons |
| Remove unused imports | CHECK | Verify nothing references them first |
| Add type annotations | CHECK | Use `TYPE_CHECKING` for import-only types |
| Remove Pydantic field constraints | **FORBIDDEN** | See Hard Boundaries |
| Add normalization/conversion functions | **FORBIDDEN** | The axios interceptor handles snake_case ↔ camelCase conversion. Backend should NEVER do this. |
| Change Pydantic Field defaults | **FORBIDDEN** | Without explicit human instruction |
| Add try/except fallback patterns | **FORBIDDEN** | Silent failures mask real bugs |
| Change error message text to `str(e)` | **FORBIDDEN** | Leaks internals |
| Register router at new prefix | **FORBIDDEN** | Without explicit human instruction |

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
- **Limit scope to ONE directory per run** (e.g., `backend/app/services/`)
- Run tests/lints to validate before committing
- Re-read the HARD BOUNDARIES section above before committing

### 4. Validate — Did it work?

- Check that tests pass
- Check that the change is meaningful (not trivial/cosmetic)
- **Verify you did not accidentally change any validation constraints, error messages, or return types**
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

## Files to NEVER Modify

These files require explicit human approval before ANY changes:

**Backend Core:**
- `backend/app/core/config.py` — Application configuration
- `backend/app/core/security.py` — Auth/hashing
- `backend/app/db/base.py`, `session.py` — DB config
- `backend/app/main.py` — App initialization

**Database:**
- `backend/app/models/*.py` — Changes require a new Alembic migration
- `backend/alembic/versions/*.py` — Never edit existing migrations

**Scheduling & Compliance:**
- `backend/app/scheduling/acgme_validator.py` — ACGME compliance rules
- `backend/app/scheduling/engine.py` — Schedule generation engine
- `backend/app/scheduling/constraints/` — Constraint definitions

**Security:**
- `backend/app/api/routes/auth.py` — Authentication
- `backend/app/resilience/*.py` — Resilience framework

**Environment:**
- `.env` — Never commit
- `docker-compose.yml` — Careful testing needed

---

## Security Requirements

This is a **military medical residency scheduler**. Security is not optional.

1. **Never log sensitive data** — No names, schedules, PII in logs
2. **Use Pydantic for all inputs** — Never bypass validation with `extra="allow"`
3. **SQLAlchemy ORM only** — No raw SQL strings
4. **Generic error messages** — HTTP responses must NOT contain `str(e)`, stack traces, or internal paths
5. **Never commit secrets** — Use environment variables
6. **Validate file paths** — Prevent path traversal
7. **Use `~column` not `not column`** for SQLAlchemy boolean negation

---

## API Type Contract (CRITICAL)

### Naming Convention
- **Backend (Python):** snake_case everywhere
- **Frontend (TypeScript):** camelCase for interface properties
- **Axios interceptor converts automatically** (snake_case ↔ camelCase)
- **DO NOT add backend normalization functions** for case conversion — the interceptor handles this

```typescript
// CORRECT - TypeScript interfaces use camelCase
interface Person {
  pgyLevel: number;
  createdAt: string;
  isActive: boolean;
}

// WRONG - will cause undefined at runtime
interface Person {
  pgy_level: number;  // Axios converts to pgyLevel, this won't match
}
```

### Enum Values Stay snake_case (Gorgon's Gaze)
Axios converts KEYS only, not VALUES. Database stores snake_case values.

```typescript
// CORRECT
type SwapType = 'one_to_one' | 'absorb';

// WRONG - will never match API responses
type SwapType = 'oneToOne' | 'absorb';
```

### URL Query Parameters Stay snake_case (Couatl Killer)
URL params go directly to API - interceptor doesn't convert them.

```typescript
// CORRECT
router.push(`/schedule?block_id=${id}&include_inactive=true`);

// WRONG
router.push(`/schedule?blockId=${id}&includeInactive=true`);
```

### Type Regeneration (STANDING ORDER)
After ANY backend schema change (`backend/app/schemas/*.py`):

```bash
cd frontend && npm run generate:types
git add frontend/src/types/api-generated.ts frontend/src/types/.api-generated.hash
```

---

## Automated Run Guardrails

### 1. Clean Tree Before Branch
```bash
git status --porcelain  # Must be empty
```
If dirty, `git stash` or abort. Never fork from a dirty tree.

### 2. Dedup Before Start
```bash
git fetch origin
git log origin/main --oneline -20 | grep -i "keyword"
gh pr list --search "keyword"
```
If the feature already exists on main or has an open PR, skip it.

### 3. Scope by Directory
- Good: "Fix datetime.utcnow in `backend/app/core/`"
- Bad: "Fix datetime.utcnow everywhere"

### 4. Contract-Aware Changes
If you change backend error keys → CHECK frontend error parsing.
If you change datetime functions → fix BOTH sides of comparisons.
If you change API response shapes → regenerate frontend types.
If you change FastAPI HTTPException detail → don't nest: `detail={"detail": "..."}` creates double-wrapping.

### 5. Test Only Merged Code
Never generate tests for un-merged feature branches. Only test code on `main`.

---

## Known Failure Patterns (Feb 2026 Audit)

These patterns were identified in a deep audit of Codex CLI output. Each one caused real bugs. **DO NOT repeat them.**

### "Normalization Layer" Anti-Pattern
Adding `_normalize_*()` functions to convert between snake_case/camelCase in route handlers. The axios interceptor already handles this. These functions add 100+ lines of dead weight per endpoint, manufacture fake data for missing fields (random UUIDs, "unknown" defaults), and mask data integrity issues instead of surfacing them.

### "Flexible Validation" Anti-Pattern
Removing `min_length`, `max_length`, or other Pydantic constraints to "make the API more flexible." Example: removing `min_length=32` from webhook secrets enabled 1-character HMAC secrets. Example: removing `min_length=1` from search queries enabled full-table scans via empty queries.

### "Improved Error Messages" Anti-Pattern
Replacing generic error messages like `"Invalid request parameters"` with `str(e)`. This leaks internal implementation details (column names, validation logic, file paths) to API consumers. The original generic messages are intentional security practice.

### "Route Alias" Anti-Pattern
Registering the same router at multiple URL prefixes for "backward compatibility." Creates duplicate OpenAPI spec entries, namespace collisions with other routers, and untested new routes that never existed before.

### "Defensive Fallback" Anti-Pattern
Wrapping operations in try/except with a silent fallback path. Example: if `scheduler.add_job()` fails, falling back to `persistence.create_job()` creates a job record that will never execute — the client gets a success response but the job is dead.

---

## Model Selection: Spark vs Regular Codex

If you are running as `gpt-5.3-codex-spark`, you are the **speed tier** — optimized for interactive, small-scope work.

**Spark scope limits:**
- Single-file fixes only (typos, `from e`, import cleanup, type annotations)
- Guardrail compliance checks
- Quick debugging with instant feedback
- If your task touches >5 files, switch to regular `gpt-5.3-codex` or flag for human

**Spark must still follow ALL guardrails above.** Speed does not exempt you from safety classification.

**If running as `gpt-5.3-codex` (default for automations):** No additional scope limits beyond the standard guardrails.

---

## Conventions

See `docs/development/AGENTS.md` for:
- Code rot detection patterns
- Consistency drift checks
- Type safety enforcement
- Performance pattern detection
