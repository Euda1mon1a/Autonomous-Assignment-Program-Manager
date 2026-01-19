# CLAUDE.md - Project Guidelines for Autonomous Claude Work

> **Last Updated:** 2026-01-03 | **Purpose:** Guidelines for AI-assisted development on the Residency Scheduler

---

## Project Overview

**Residency Scheduler**: Full-stack application for medical residency scheduling with ACGME compliance.

**Core Features:** Automated schedule generation, ACGME compliance monitoring (80-hour rule, 1-in-7, supervision ratios), emergency coverage, swap management, procedure credentialing, resilience framework.

**Context:** Military medical residency scheduling. All work must consider: data security, audit trails, error handling (no leaks), access control.

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.109.0 | Web framework |
| SQLAlchemy | 2.0.25 | ORM (async) |
| Pydantic | 2.5.3 | Validation |
| Alembic | 1.13.1 | Migrations |
| PostgreSQL | 15 | Database |
| Redis | Latest | Cache/broker |
| Celery | 5.x | Background tasks |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.0.4 | App Router |
| React | 18.2.0 | UI |
| TypeScript | 5.0+ | Type safety |
| TailwindCSS | 3.3.0 | Styling |
| TanStack Query | 5.17.0 | Data fetching |

### Infrastructure

Docker + Docker Compose, MCP Server (29+ AI tools), Prometheus, Grafana

---

## Architecture Patterns

**Layered Architecture:** Route -> Controller -> Service -> Repository -> Model

```
backend/app/
├── api/routes/       # Endpoints
├── controllers/      # Request handling
├── services/         # Business logic
├── models/           # SQLAlchemy ORM
├── schemas/          # Pydantic schemas
├── scheduling/       # Engine & validator
├── resilience/       # Framework
└── core/             # Config, security
```

**Rules:** Routes thin, logic in services, Pydantic for validation, async everywhere, use `Depends()`.

---

## Code Style

**Python:** PEP 8, type hints required, Google-style docstrings, 100 char lines, async for DB ops.
**TypeScript:** Strict mode, no `any`, PascalCase components, `use` prefix for hooks.
**Naming:** Classes=PascalCase, functions=snake_case, constants=UPPER_SNAKE_CASE.

### API Type Naming Convention (CRITICAL)

**Backend uses snake_case, Frontend uses camelCase.** The axios interceptor in `frontend/src/lib/api.ts` automatically converts between them:
- Response: snake_case → camelCase (for frontend)
- Request: camelCase → snake_case (for API)

**TypeScript interfaces MUST use camelCase:**
```typescript
// ✓ CORRECT
interface Person {
  pgyLevel: number;
  createdAt: string;
  isActive: boolean;
}

// ✗ WRONG (will cause undefined at runtime)
interface Person {
  pgy_level: number;
  created_at: string;
  is_active: boolean;
}
```

**Why this matters:** TypeScript types don't affect runtime. If types say `created_at` but axios converts to `createdAt`, code will access `undefined`.

**Enforcement:** ESLint `@typescript-eslint/naming-convention` rule catches violations. Run:
```bash
cd frontend && npm run lint
```

**Skill:** Use `/check-camelcase` to scan for violations.

### URL Query Parameters (Couatl Killer)

**URL query params MUST use snake_case**, even in frontend code:
```typescript
// ✓ CORRECT
const params = new URLSearchParams({ block_id: '123', include_inactive: 'true' });
router.push(`/schedule?person_id=${id}`);

// ✗ WRONG (backend expects snake_case)
const params = new URLSearchParams({ blockId: '123', includeInactive: 'true' });
router.push(`/schedule?personId=${id}`);
```

**Why:** Query params go directly to the API. The axios interceptor only converts request/response bodies, not URL parameters.

### SQLAlchemy Boolean Negation (Beholder Bane)

**Use `~column` not `not column`** for SQLAlchemy boolean filters:
```python
# ✓ CORRECT
query.filter(~Person.is_active)
query.filter(Person.is_deleted == False)  # noqa: E712

# ✗ WRONG (returns Python bool, not SQL expression)
query.filter(not Person.is_active)
```

**Why:** `not` is Python's boolean operator and returns `True`/`False`. `~` invokes SQLAlchemy's `__invert__` to generate proper SQL `NOT` clause.

> RAG: `rag_search('code style examples')` for detailed patterns

---

## Testing Requirements

**ALL code changes must include tests.** Run before commit:
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`

If tests fail, DO NOT COMMIT.

> RAG: `rag_search('testing patterns')` for examples

---

## Security Requirements

### OPSEC/PERSEC (Military Medical Data)

**Never commit:** Resident/faculty names, schedule assignments, absence/leave records, TDY/deployment data.

| Data Type | Handling |
|-----------|----------|
| Names | Local only, use synthetic IDs for demos |
| Schedules | Local only |
| Credentials | Environment variables |

**Gitignored:** `docs/data/*.json`, `*.dump`, `*.sql`, `.env*`

### Authentication & Authorization

- JWT httpOnly cookies (XSS-resistant)
- 12+ char passwords with complexity
- Rate limiting on auth endpoints
- 8 RBAC roles (Admin, Coordinator, Faculty, Resident, Clinical Staff, RN, LPN, MSA)

### Security Best Practices

1. Never log sensitive data
2. Use Pydantic for all inputs
3. SQLAlchemy ORM only (no raw SQL)
4. Validate file paths (path traversal)
5. Never commit secrets
6. Don't leak info in errors

### Secret Validation

App refuses to start if `SECRET_KEY`/`WEBHOOK_SECRET` are empty, <32 chars, or defaults.

```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

---

## Files and Patterns to Never Modify

### Critical Files - Never Modify Without Permission

**Backend Core:**
- `backend/app/core/config.py` - Configuration
- `backend/app/core/security.py` - Auth/hashing
- `backend/app/db/base.py`, `session.py` - DB config
- `backend/app/main.py` - App init

**Database:**
- `backend/app/models/*.py` - Changes require migration
- `backend/alembic/versions/*.py` - Never edit existing

**Environment:**
- `.env` - Never commit
- `docker-compose.yml` - Careful testing needed

### Patterns to Avoid

1. Don't bypass auth or skip auth checks
2. Don't disable rate limiting
3. Don't use sync DB calls
4. Don't hardcode secrets
5. Don't expose sensitive data in responses
6. Don't modify ACGME compliance rules

### High-Risk Areas

- `backend/app/scheduling/acgme_validator.py`
- `backend/app/scheduling/engine.py`
- `backend/app/api/routes/auth.py`
- `backend/app/resilience/*.py`

### Database Safety Rules

#### Lich's Phylactery (Schema Snapshots)

When models or migrations change, the pre-commit hook auto-generates `backend/schema.sql`:
- Contains schema only (no data) - safe to commit
- Enables schema resurrection without running all migrations
- Auto-staged on commit when DB files change

**If you modify `backend/app/models/*.py` or add migrations:**
1. Ensure DB container is running: `docker compose up -d db`
2. The hook will auto-dump schema on commit
3. If skipped (DB not running), manually run: `./scripts/lichs-phylactery.sh`

#### Backup Before Destructive Operations

**MUST create backup before:**
- Schedule generation (bulk writes)
- Swap execution (multi-table updates)
- Migration rollbacks
- Any `DELETE` or `TRUNCATE` operations

**MCP backup tools:**
```python
# Before destructive operation
mcp__residency-scheduler__create_backup_tool(reason="Pre-generation backup")

# Verify backup exists
mcp__residency-scheduler__get_backup_status_tool()

# If something goes wrong
mcp__residency-scheduler__restore_backup_tool(backup_id="...")
```

**Skill:** Use `/safe-schedule-generation` which enforces backup-first workflow.

#### Migration Safety

- **Never edit existing migrations** - create new ones to fix issues
- **Revision IDs ≤ 64 chars** - format: `YYYYMMDD_short_desc`
- **Test rollback** before merging: `alembic downgrade -1` then `alembic upgrade head`
- **No data migrations in schema migrations** - separate concerns

---

## AI Rules of Engagement

### Command Philosophy: Auftragstaktik

This project operates on **mission-type orders** (Auftragstaktik), not detailed command. Each level provides intent; each level decides how.

**The Litmus Test:**
> "If your delegation reads like a recipe, you're micromanaging."
> "If it reads like mission orders, you're delegating."

**Key Principles:**
- **Commander's Intent**: Higher level provides objective + why
- **Delegated Autonomy**: Lower level decides how
- **Standing Orders**: Pre-authorized patterns skip escalation
- **Escalate When Blocked**: Only strategic pivots surface up

> RAG: `rag_search('Auftragstaktik doctrine')` for full delegation patterns
> See: `.claude/Governance/HIERARCHY.md` for command philosophy

### Commander's Intent

**Mission:** Deliver a production-ready military medical residency scheduler that is ACGME-compliant, operationally secure, and institutionally resilient.

**End State:** Program coordinators generate valid schedules autonomously. System handles edge cases gracefully. Audit trails complete.

**Left Boundary (NEVER CROSS):**
- No OPSEC/PERSEC violations (names, schedules, deployments)
- No ACGME compliance shortcuts
- No silent failures (all errors logged/escalated)
- No security bypasses (auth, rate limiting, input validation)

**Right Boundary (ALWAYS DO):**
- Tests pass before commit
- Linters clean
- Audit trail for schedule changes
- Graceful degradation over hard failure

### Decision Rights

| Tier | Act Autonomously | Escalate Up |
|------|------------------|-------------|
| **Specialist** | Implementation details, test fixes, bug patches | Architecture changes, new dependencies, scope creep |
| **Coordinator** | Task decomposition, agent selection, retry logic | Blocked >2 attempts, cross-domain impact, unclear requirements |
| **Deputy** | Strategic pivots within domain, resource allocation | User-facing changes, cross-deputy coordination, policy changes |
| **ORCHESTRATOR** | 99% delegation, workflow orchestration | Container ops (1%), user preference unclear, boundary violations |

**When in doubt:** Act within boundaries. Escalate if approaching a boundary.

### Report Tool/Environment Issues

If a tool fails repeatedly (e.g., `ruff: command not found`), **tell the user** instead of silently working around it. They can often fix it quickly (install locally, add to PATH, etc.). Don't waste cycles on workarounds when a 30-second fix exists.

Examples of things to report:
- Missing CLI tools (ruff, pytest, etc.)
- Permission errors
- Docker containers not running
- Environment variables not set
- Repeated test failures with unclear cause

### Resources Available

**Tools:** 34+ MCP tools via `mcp__*` prefix. Key domains: scheduling, validation, resilience, RAG search.
**Hazards:** Run `rag_search('common pitfalls')` before novel approaches. Known issues: CCW token bugs, import removal, docker volume masking.
**Agents:** See `.claude/Agents/` for full roster. Spawn based on domain expertise, not availability.
**Codebase:** `backend/app/` (FastAPI), `frontend/src/` (Next.js), `.claude/` (PAI governance).

### MCP Tool Requirements (MUST USE)

The MCP tools exist to prevent errors and ensure compliance. **Use them.**

**Before Schedule Work:**
MUST run: `mcp__residency-scheduler__validate_schedule_tool`
- Catches ACGME violations before implementation
- Validates constraints, coverage gaps, supervision ratios

**Before Domain Questions:**
MUST query: `mcp__residency-scheduler__rag_search`
- Contains policies, ACGME rules, scheduling patterns
- 67+ documents indexed with semantic search

**Before Resilience Changes:**
MUST check: `mcp__residency-scheduler__get_defense_level_tool`
- Shows current utilization and N-1/N-2 status
- Prevents capacity decisions that degrade resilience

**Tool Quick Reference:**

| Scenario | MCP Tool | Why |
|----------|----------|-----|
| ACGME questions | `rag_search` | Knows the rules |
| Schedule validation | `validate_schedule_tool` | Catches violations |
| Resilience status | `get_defense_level_tool` | Shows system health |
| System health | `check_circuit_breakers_tool` | Service status |
| Compliance report | `check_mtf_compliance_tool` | Military compliance |
| Swap analysis | `analyze_swap_candidates_tool` | Safe swap matching |

### Core Policy

- Full autonomy for local work
- All GitHub changes go through PR
- No direct pushes to `main`

### Permission Tiers

**Tier 1: Autonomous**
| Operation | Allowed |
|-----------|---------|
| `git add/commit/push` | Yes (feature branches) |
| `gh pr create/view` | Yes |
| Read/edit code | Yes |
| Run tests/linters | Yes |

**Tier 2: Review-Required**
| Operation | Approval |
|-----------|----------|
| `git merge/rebase/reset` | Ask |
| `alembic` migrations | Ask |
| `docker-compose` | Ask |
| Edit security files | Ask |

**Tier 3: Blocked**
| Operation | Status |
|-----------|--------|
| `git push origin main` | Denied |
| `git push --force` | Denied |
| `DROP TABLE/TRUNCATE` | Denied |
| Read `.env` | Denied |

### Environment Detection

Before changes, AI MUST:
1. Identify interface type (Web=Suggestion, CLI=Direct Edit)
2. Check git context (`git branch --show-current`)
3. If on main, create feature branch first

### Branching Workflow

1. Create feature branch off `origin/main`
2. Commit on feature branch only
3. Push feature branch
4. Open PR, wait for approval

### Guardrails

- No `--allow-unrelated-histories` without approval
- Use rebase, not merge commits on main
- If histories diverge, stop and ask

### Required Checks

- Backend: `ruff check . --fix && ruff format .`
- Frontend: `npm run lint:fix`
- CI must pass before merge

### Agent Spawning (MANDATORY)

When spawning ANY PAI agent via Task(), you MUST:
1. Read `.claude/Identities/[AGENT_NAME].identity.md`
2. Include it as `## BOOT CONTEXT` at the start of the prompt

```
Task(
  prompt="""
  ## BOOT CONTEXT
  [contents of identity card]

  ## MISSION
  [task description]
  """
)
```

**No exceptions.** Identity cards contain chain of command, spawn authority, and standing orders.

---

## Development Workflow

Follow layered architecture. Write tests. Run tests before commit. Use Alembic for DB changes.

> RAG: `rag_search('development workflow')` for detailed steps

---

## Migration Naming Convention

**CRITICAL:** Alembic revision IDs must be **64 characters or less**.

The `alembic_version.version_num` column has been extended to `varchar(128)`, but we enforce a 64-char limit for safety margin and to encourage concise naming.

### Format

```
YYYYMMDD_short_description
```

### Examples

| Good (under 64 chars) | Bad (too long) |
|-----------------------|----------------|
| `20260105_res_weekly_reqs` | `20260105_add_resident_weekly_requirements_with_fm_clinic_scheduling` |
| `20260103_add_activity_log` | `20260103_add_activity_log_table_for_audit_tracking_purposes` |
| `20251220_gateway_auth` | `20251220_add_gateway_authentication_and_authorization_tables` |

### Rules

1. **Date prefix:** Always start with `YYYYMMDD_`
2. **Use abbreviations:** `req` not `requirement`, `col` not `column`
3. **Be concise:** Focus on the what, not the why
4. **Pre-commit check:** A hook validates length before commit

### Validation

```bash
# Check all migrations
./scripts/validate-migration-names.sh

# The pre-commit hook runs automatically on staged migrations
```

> **History:** The default Alembic column is `varchar(32)` which caused repeated container startup failures. Migration `20260105_ext_ver_col` extended it to `varchar(128)`.

---

## Common Commands

> RAG: `rag_search('common commands')` for full command reference

**Quick Reference:**
- Backend server: `uvicorn app.main:app --reload`
- Tests: `pytest` / `npm test`
- Migrations: `alembic upgrade head`
- Docker: `docker-compose up -d`

---

## Getting Help

### Documentation

**Humans:** `docs/` (user-guide, admin-manual, architecture, api)
**AI Agents:** `.claude/dontreadme/INDEX.md` (start here)

### Key References

- **`docs/development/BEST_PRACTICES_AND_GOTCHAS.md`** - **READ THIS FIRST** (common bugs, debugging flowcharts)
- `.claude/dontreadme/synthesis/PATTERNS.md` - Implementation patterns
- `.claude/dontreadme/synthesis/DECISIONS.md` - Architectural decisions
- `docs/development/AGENT_SKILLS.md` - AI skills reference

### Audit & Logs

| Log Type | Location | Purpose |
|----------|----------|---------|
| Application logs | `logs/app.log` | Backend application events |
| Offline events | `logs/offline_events.log` | System outages and recovery |
| Schedule audit | Database `activity_log` table | Schedule modification history |
| Agent governance | Session transcripts | PAI agent actions and decisions |

**Governance Review:** DELEGATION_AUDITOR reviews offline logs weekly. See `.claude/SOPs/OFFLINE_SOP.md` for offline procedures.

### RAG Queries

- `rag_search('Auftragstaktik doctrine')` - **Delegation philosophy (critical)**
- `rag_search('ACGME compliance')` - Compliance rules
- `rag_search('resilience framework')` - Cross-industry patterns
- `rag_search('debugging workflow')` - Troubleshooting guide
- `rag_search('common pitfalls')` - Known gotchas
- `rag_search('context isolation agents')` - Agent spawning patterns
- `rag_search('parallel agent efficiency')` - 50×1 > 5×10 (critical)
- `rag_search('standing orders session')` - Cross-session guidance
- `rag_search('session handoff protocol')` - Handoff patterns
- `rag_search('CCW error patterns')` - Token bugs, import removal
- `rag_search('MCP configuration type http')` - MCP client config (critical)
- `rag_search('docker volume mount masking')` - Container state gotcha

---

## Documentation Updates

Update docs when changing: API (docstrings + `docs/api/`), features (README), config (`.env.example`).

---

*This is a scheduling app for military medical residency. Data security and ACGME compliance are critical.*
