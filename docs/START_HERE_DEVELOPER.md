# Welcome, Developer!

> Your starting point for contributing to Residency Scheduler

Whether you're a human developer or an AI agent, this guide gets you oriented quickly.

---

## Essential Reading (In Order)

| Priority | Document | Time | Why |
|----------|----------|------|-----|
| 1 | **[CLAUDE.md](../CLAUDE.md)** | 15 min | **REQUIRED** - Project guidelines |
| 2 | [Architecture Overview](architecture/overview.md) | 10 min | System design |
| 3 | [Development Setup](development/setup.md) | 30 min | Local environment |
| 4 | [Best Practices](development/BEST_PRACTICES_AND_GOTCHAS.md) | 10 min | Common pitfalls |

---

## For AI Agents

### Your Documentation Home
**[.claude/dontreadme/INDEX.md](../.claude/dontreadme/INDEX.md)** - Start here for LLM-focused context

### Essential RAG Queries

```python
# Delegation philosophy (CRITICAL)
rag_search('Auftragstaktik doctrine')

# Common pitfalls
rag_search('common pitfalls')

# Agent patterns
rag_search('context isolation agents')

# Session handoff
rag_search('session handoff protocol')

# MCP configuration
rag_search('MCP configuration type http')
```

### Agent Identity Cards
Located in `.claude/Identities/`. When spawning agents via `Task()`, include the identity card content.

### MCP Tools Available
34+ tools via `mcp__residency-scheduler__*`. Key categories:
- Schedule validation
- Compliance checking
- Resilience analysis
- RAG search/ingest

---

## For Human Developers

### Quick Setup

```bash
# Clone and setup backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd frontend
npm install

# Start development
docker-compose up -d  # Database, Redis
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

Full guide: [Development Setup](development/setup.md)

### Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Backend | FastAPI | 0.109.0 |
| ORM | SQLAlchemy | 2.0.25 (async) |
| Validation | Pydantic | 2.5.3 |
| Frontend | Next.js | 14.0.4 |
| UI | React | 18.2.0 |
| Styling | TailwindCSS | 3.3.0 |
| Database | PostgreSQL | 15 |
| Cache | Redis | Latest |

### Code Style

**Backend (Python)**:
- PEP 8 compliant
- Type hints required
- Google-style docstrings
- 100 char line limit
- Async for DB operations

**Frontend (TypeScript)**:
- Strict mode enabled
- No `any` types
- PascalCase for components
- `use` prefix for hooks

**Critical**: Backend uses `snake_case`, frontend uses `camelCase`. Auto-converted by axios interceptor.

### Quality Gates

Before every PR:

```bash
# Backend
cd backend
ruff check . --fix
ruff format .
pytest

# Frontend
cd frontend
npm run lint:fix
npm test
```

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Endpoints
│   │   ├── controllers/     # Request handling
│   │   ├── services/        # Business logic
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── scheduling/      # Schedule engine
│   │   └── resilience/      # Resilience framework
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # React components
│   │   ├── features/       # Feature modules
│   │   └── lib/            # Utilities
│   └── tests/
├── mcp-server/             # MCP tools server
├── docs/                   # Human documentation
└── .claude/                # AI agent infrastructure
```

---

## Key Patterns

### Layered Architecture
```
Route → Controller → Service → Repository → Model
```
- Routes are thin
- Business logic in services
- Pydantic for validation
- Use `Depends()` for injection

### Database Changes
Always use Alembic migrations:
```bash
cd backend
alembic revision --autogenerate -m "short_description"
alembic upgrade head
```

**Important**: Revision IDs must be ≤64 characters.

### Testing
- All changes require tests
- Backend: `pytest`
- Frontend: `jest` + Playwright
- E2E: 6 Playwright specs

---

## Common Tasks

### Add API Endpoint

1. Create route in `backend/app/api/routes/`
2. Add Pydantic schemas in `backend/app/schemas/`
3. Implement service logic in `backend/app/services/`
4. Write tests in `backend/tests/`
5. Regenerate frontend types: `cd frontend && npm run generate:types`

### Add React Component

1. Create in `frontend/src/components/` or `frontend/src/features/`
2. Use TypeScript strict mode
3. Follow [component standards](../FRONTEND_COMPONENT_STANDARDS.md)
4. Add tests in `frontend/tests/`

### Add MCP Tool

1. Create tool in `mcp-server/src/scheduler_mcp/tools/`
2. Follow `@mcp.tool()` decorator pattern
3. Add to server.py registration
4. Test via Claude Code

---

## Getting Unstuck

### Build Failures
```bash
# Clear caches
rm -rf backend/__pycache__ frontend/.next frontend/node_modules/.cache

# Reinstall dependencies
cd backend && pip install -r requirements.txt
cd frontend && rm -rf node_modules && npm install
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d
cd backend && alembic upgrade head
```

### Test Failures
```bash
# Run specific test
pytest tests/path/to/test.py -v

# Run with debug output
pytest --capture=no -v
```

---

## Learn More

### Essential Documentation
- [CLAUDE.md](../CLAUDE.md) - **READ FIRST**
- [Architecture](architecture/README.md) - System design
- [API Reference](api/README.md) - Endpoints
- [Best Practices](development/BEST_PRACTICES_AND_GOTCHAS.md) - Patterns & gotchas

### For Contributors
- [Contributing Guide](development/contributing.md)
- [Code Style Guide](development/code-style.md)
- [Testing Guide](development/testing.md)
- [PR Review Process](development/pr-review.md)

### Domain Knowledge
- [ACGME Rules](rag-knowledge/acgme-rules.md) - Compliance rules
- [Scheduling Concepts](rag-knowledge/scheduling-policies.md) - Domain model
- [Resilience Framework](guides/RESILIENCE_FRAMEWORK_GUIDE.md) - System resilience

---

## Get Help

1. **Check documentation** - Most answers are already documented
2. **Search codebase** - Similar patterns likely exist
3. **Ask in PR** - For code-specific questions
4. **[Troubleshooting](troubleshooting.md)** - Common issues

---

*Welcome to the project. Build something great.*
