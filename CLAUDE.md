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

---

## Development Workflow

Follow layered architecture. Write tests. Run tests before commit. Use Alembic for DB changes.

> RAG: `rag_search('development workflow')` for detailed steps

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

- `.claude/dontreadme/synthesis/PATTERNS.md` - Implementation patterns
- `.claude/dontreadme/synthesis/DECISIONS.md` - Architectural decisions
- `docs/development/AGENT_SKILLS.md` - AI skills reference

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
