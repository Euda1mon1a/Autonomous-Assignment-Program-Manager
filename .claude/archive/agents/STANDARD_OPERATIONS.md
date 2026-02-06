# Standard Operations Reference

> **Purpose:** Canonical scripts and tools for all agents to use consistently
> **Include in:** Agent specs via "See: `.claude/Agents/STANDARD_OPERATIONS.md`"

---

## CI/Quality Scripts

**Always use these scripts - never ad-hoc commands:**

### Backend (Python)

```bash
# Linting (MUST run before commit)
cd backend && ruff check . --fix && ruff format .

# Tests
cd backend && pytest                           # All tests
cd backend && pytest tests/unit/               # Unit only
cd backend && pytest -x                        # Stop on first failure
cd backend && pytest --cov=app --cov-report=term  # With coverage

# Type checking (if mypy configured)
cd backend && mypy app/
```

### Frontend (TypeScript/React)

```bash
# Linting (MUST run before commit)
cd frontend && npm run lint:fix

# Type checking (MUST pass before commit)
cd frontend && npm run type-check

# Tests
cd frontend && npm test                        # All tests
cd frontend && npm run test:coverage           # With coverage

# Build verification
cd frontend && npm run build
```

### Full Stack Health

```bash
# Stack health check (run before starting work)
./scripts/stack-health.sh

# Full validation (run before PR)
./scripts/stack-health.sh --full
```

### Docker Operations

```bash
# Rebuild after code changes (not just restart!)
docker compose up -d --build <service>

# View logs
docker compose logs -f <service>

# Health status
docker compose ps
```

### Database Migrations

```bash
# Apply migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"

# Rollback one
cd backend && alembic downgrade -1
```

---

## RAG Knowledge Base

**MCP tools for semantic search across project documentation:**

```
mcp__residency-scheduler__rag_search(query, top_k=5, doc_type=None)
mcp__residency-scheduler__rag_context(query, max_tokens=2000)
mcp__residency-scheduler__rag_health()
```

### Available doc_types

| Type | Content |
|------|---------|
| `acgme_rules` | ACGME duty hour requirements, supervision ratios |
| `scheduling_policy` | Block structure, rotation templates, constraints |
| `swap_system` | Swap types, approval workflow, rollback |
| `military_specific` | TDY, deployment, PERSEC/OPSEC |
| `resilience_concepts` | N-1/N-2, defense in depth, utilization thresholds |
| `user_guide_faq` | Common questions, UI workflows |
| `ai_patterns` | Session learnings, effective prompts |
| `delegation_patterns` | Agent coordination, context isolation |
| `exotic_concepts` | Advanced resilience (metastability, spin glass, etc.) |

### When to Use RAG

- **Before answering compliance questions** - search `acgme_rules`
- **Before modifying scheduling logic** - search `scheduling_policy`
- **Before swap operations** - search `swap_system`
- **When unsure about domain concepts** - search relevant doc_type

---

## Quality Gates (Pre-Commit Checklist)

**ALL agents must verify before committing:**

```bash
# 1. Backend lint clean
cd backend && ruff check . && ruff format . --check

# 2. Frontend lint + types clean
cd frontend && npm run lint && npm run type-check

# 3. Tests pass
cd backend && pytest
cd frontend && npm test

# 4. Build succeeds (frontend)
cd frontend && npm run build
```

**Shortcut - use stack health:**
```bash
./scripts/stack-health.sh --full
```

---

## Git Operations

```bash
# Status check
git status
git diff --stat

# Branch operations
git checkout -b feature/description
git fetch origin main
git rebase origin/main

# Commit (use heredoc for multi-line)
git commit -m "$(cat <<'EOF'
type(scope): description

Body explaining why.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"

# PR creation
gh pr create --title "type(scope): description" --body "..."
```

---

## Common Mistakes to Avoid

| Wrong | Right |
|-------|-------|
| `docker compose restart backend` | `docker compose up -d --build backend` |
| `grep -r "pattern" .` | Use `Grep` tool |
| `cat file.py` | Use `Read` tool |
| Running lint ad-hoc | Use standard scripts above |
| Guessing ACGME rules | Search RAG first |

---

*All agents should reference this file for consistent operations.*
