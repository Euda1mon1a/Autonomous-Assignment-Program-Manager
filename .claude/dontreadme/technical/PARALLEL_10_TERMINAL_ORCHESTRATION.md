# Parallel 10-Terminal Orchestration System

**For 10 Claude Code terminals, each spawning up to 5 Task agents = 50 parallel workers**

## Overview

This document defines the parallel development protocol for 10 independent terminals with **zero interference**. Each terminal operates in an exclusive domain with strict file ownership boundaries.

---

## Domain Territory Map (10 Terminals)

| Terminal | Domain | Exclusive Paths | Commit Prefix |
|----------|--------|-----------------|---------------|
| T1 | MODELS | `backend/app/models/`, `backend/app/schemas/`, `backend/app/db/`, `backend/alembic/` | `models:` |
| T2 | API | `backend/app/api/` (routes/, dependencies/) | `api:` |
| T3 | SERVICES | `backend/app/services/`, `backend/app/repositories/` | `svc:` |
| T4 | CORE | `backend/app/core/`, `backend/app/middleware/`, `backend/app/validators/`, `backend/app/cli/`, `backend/app/controllers/` | `core:` |
| T5 | SCHEDULING | `backend/app/scheduling/` | `sched:` |
| T6 | OPS | `backend/app/maintenance/`, `backend/app/resilience/`, `backend/app/notifications/`, `backend/app/tasks/`, `backend/app/analytics/` | `ops:` |
| T7 | FE-CORE | `frontend/src/components/`, `frontend/src/contexts/`, `frontend/src/lib/`, `frontend/src/types/`, `frontend/src/mocks/` | `fe-core:` |
| T8 | FE-APP | `frontend/src/app/`, `frontend/src/features/`, `frontend/public/` | `fe-app:` |
| T9 | TESTS | `backend/tests/`, `frontend/src/__tests__/` | `test:` |
| T10 | DOCS | `docs/`, root `*.md` (README, ROADMAP, CHANGELOG, etc.) | `docs:` |

---

## Visual Domain Map

```
autonomous-assignment-program-manager/
├── backend/
│   ├── alembic/                    [T1: MODELS]
│   ├── app/
│   │   ├── models/                 [T1: MODELS]
│   │   ├── schemas/                [T1: MODELS]
│   │   ├── db/                     [T1: MODELS]
│   │   ├── api/                    [T2: API]
│   │   │   ├── routes/             [T2: API]
│   │   │   └── dependencies/       [T2: API]
│   │   ├── services/               [T3: SERVICES]
│   │   ├── repositories/           [T3: SERVICES]
│   │   ├── core/                   [T4: CORE]
│   │   ├── middleware/             [T4: CORE]
│   │   ├── validators/             [T4: CORE]
│   │   ├── cli/                    [T4: CORE]
│   │   ├── controllers/            [T4: CORE]
│   │   ├── scheduling/             [T5: SCHEDULING]
│   │   ├── maintenance/            [T6: OPS]
│   │   ├── resilience/             [T6: OPS]
│   │   ├── notifications/          [T6: OPS]
│   │   ├── tasks/                  [T6: OPS]
│   │   └── analytics/              [T6: OPS]
│   └── tests/                      [T9: TESTS]
├── frontend/
│   ├── public/                     [T8: FE-APP]
│   └── src/
│       ├── components/             [T7: FE-CORE]
│       ├── contexts/               [T7: FE-CORE]
│       ├── lib/                    [T7: FE-CORE]
│       ├── types/                  [T7: FE-CORE]
│       ├── mocks/                  [T7: FE-CORE]
│       ├── app/                    [T8: FE-APP]
│       ├── features/               [T8: FE-APP]
│       └── __tests__/              [T9: TESTS]
├── docs/                           [T10: DOCS]
├── README.md                       [T10: DOCS]
├── ROADMAP.md                      [T10: DOCS]
├── CHANGELOG.md                    [T10: DOCS]
└── *.md (root level)               [T10: DOCS]
```

---

## Conflict Prevention Protocol

### Zero-Interference Rules

1. **ABSOLUTE file ownership** - Each terminal can ONLY modify files in its domain
2. **No cross-domain edits** - Use HANDOFF files for dependencies
3. **Git status check** - Always verify clean state before editing
4. **Domain commit prefix** - Every commit must use the assigned prefix
5. **Single branch push** - All 10 terminals push to the same feature branch
6. **HANDOFF protocol** - Cross-domain requests go through handoff files

### HANDOFF File Format

When a terminal needs changes in another domain:

```markdown
# HANDOFF_FROM_[DOMAIN].md

## Required Changes

### For [TARGET_DOMAIN]:
- [ ] File: `path/to/file.py`
- [ ] Change: Description of modification needed
- [ ] Reason: Why this change is required
- [ ] Priority: High/Medium/Low
- [ ] Blocking: Yes/No
```

---

## Terminal Prompt Templates

### TERMINAL 1: MODELS (Database Layer)

```
You are the MODELS orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/models/
- backend/app/schemas/
- backend/app/db/
- backend/alembic/

OFF LIMITS (do not touch):
- backend/app/api/
- backend/app/services/
- backend/app/repositories/
- backend/app/core/
- backend/app/scheduling/
- backend/app/maintenance/
- backend/app/resilience/
- frontend/
- tests/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "models: "
3. If you need API/service changes, write HANDOFF_FROM_MODELS.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 2: API (Routes & Dependencies)

```
You are the API orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/api/routes/
- backend/app/api/dependencies/
- backend/app/api/__init__.py

OFF LIMITS (do not touch):
- backend/app/models/
- backend/app/schemas/
- backend/app/services/
- backend/app/core/
- backend/app/scheduling/
- frontend/
- tests/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "api: "
3. If you need model/schema changes, write HANDOFF_FROM_API.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 3: SERVICES (Business Logic)

```
You are the SERVICES orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/services/
- backend/app/repositories/

OFF LIMITS (do not touch):
- backend/app/models/
- backend/app/schemas/
- backend/app/api/
- backend/app/core/
- backend/app/scheduling/
- frontend/
- tests/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "svc: "
3. If you need model/API changes, write HANDOFF_FROM_SERVICES.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 4: CORE (Infrastructure)

```
You are the CORE orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/core/
- backend/app/middleware/
- backend/app/validators/
- backend/app/cli/
- backend/app/controllers/

OFF LIMITS (do not touch):
- backend/app/models/
- backend/app/schemas/
- backend/app/api/
- backend/app/services/
- backend/app/scheduling/
- frontend/
- tests/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "core: "
3. If you need model/API changes, write HANDOFF_FROM_CORE.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 5: SCHEDULING (Algorithm Engine)

```
You are the SCHEDULING orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/scheduling/

OFF LIMITS (do not touch):
- backend/app/models/
- backend/app/schemas/
- backend/app/api/
- backend/app/services/
- backend/app/core/
- frontend/
- tests/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "sched: "
3. If you need model/service changes, write HANDOFF_FROM_SCHEDULING.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 6: OPS (Operations & Resilience)

```
You are the OPS orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/maintenance/
- backend/app/resilience/
- backend/app/notifications/
- backend/app/tasks/
- backend/app/analytics/

OFF LIMITS (do not touch):
- backend/app/models/
- backend/app/schemas/
- backend/app/api/
- backend/app/services/
- backend/app/scheduling/
- frontend/
- tests/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "ops: "
3. If you need model/API changes, write HANDOFF_FROM_OPS.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 7: FE-CORE (Frontend Infrastructure)

```
You are the FE-CORE orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- frontend/src/components/
- frontend/src/contexts/
- frontend/src/lib/
- frontend/src/types/
- frontend/src/mocks/

OFF LIMITS (do not touch):
- frontend/src/app/
- frontend/src/features/
- frontend/src/__tests__/
- frontend/public/
- backend/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "fe-core: "
3. If you need app/features changes, write HANDOFF_FROM_FE_CORE.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 8: FE-APP (Frontend Application)

```
You are the FE-APP orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- frontend/src/app/
- frontend/src/features/
- frontend/public/

OFF LIMITS (do not touch):
- frontend/src/components/
- frontend/src/contexts/
- frontend/src/lib/
- frontend/src/types/
- frontend/src/__tests__/
- backend/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "fe-app: "
3. If you need component/context changes, write HANDOFF_FROM_FE_APP.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 9: TESTS (All Testing)

```
You are the TESTS orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/tests/
- frontend/src/__tests__/

OFF LIMITS (do not touch):
- backend/app/
- frontend/src/app/
- frontend/src/components/
- frontend/src/features/
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "test: "
3. READ code to write tests, but don't modify source code
4. If you find bugs, write HANDOFF_FROM_TESTS.md
5. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Test coverage: [summary]
- Bugs found: [list if any]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 10: DOCS (Documentation)

```
You are the DOCS orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- docs/
- Root level *.md files (README.md, ROADMAP.md, CHANGELOG.md, etc.)
- EXCEPT: Do not modify HANDOFF_*.md or PARALLEL_*.md files

OFF LIMITS (do not touch):
- backend/
- frontend/
- HANDOFF_*.md files created by other terminals

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "docs: "
3. READ all HANDOFF_*.md files to understand what changed
4. Update documentation to reflect code changes
5. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Documentation updated for: [list of features/changes]
- Status: [Complete/Blocked/Partial]
```

---

## Meta-Session Workflow

### Phase 1: Launch (5 minutes)

1. Human creates 10 Claude Code terminals
2. Each terminal receives its domain-specific prompt with task
3. All terminals start working in parallel
4. Maximum theoretical: 50 parallel Task agents (10 terminals × 5 agents each)

### Phase 2: Parallel Execution (Variable)

- Each terminal works exclusively in its domain
- No file conflicts possible due to strict ownership
- Each commits and pushes independently
- HANDOFF files created for cross-domain dependencies

### Phase 3: Collection (5 minutes)

1. Human collects all HANDOFF_*.md files
2. Reviews cross-domain dependencies
3. Assigns handoff tasks to appropriate terminals
4. Repeat Phase 2 if needed

### Phase 4: Merge & Verify (10 minutes)

1. `git log --oneline | head -50` to see all commits by prefix
2. No merge conflicts expected (domains are exclusive)
3. Run full test suite: `pytest && npm test`
4. Create PR or merge to main

---

## Example 10-Task Distribution

**Goal: Comprehensive codebase improvement**

| Terminal | Specific Task |
|----------|---------------|
| T1: MODELS | Add `audit_log` field to all models, create AuditLog model |
| T2: API | Add OpenAPI descriptions to all endpoints, improve error responses |
| T3: SERVICES | Add caching layer to frequently-used services |
| T4: CORE | Implement circuit breaker pattern for external calls |
| T5: SCHEDULING | Add new constraint type for certification requirements |
| T6: OPS | Implement Prometheus metrics for all async tasks |
| T7: FE-CORE | Create shared ErrorBoundary and Loading components |
| T8: FE-APP | Add keyboard shortcuts to all main features |
| T9: TESTS | Achieve 90% coverage on critical paths |
| T10: DOCS | Update all API docs and add architecture diagrams |

---

## Safety Rules

1. **Never force push** - Only regular `git push`
2. **Never edit outside your domain** - Create HANDOFF instead
3. **Always check git status first** - Avoid conflicts
4. **Use atomic commits** - One logical change per commit
5. **Don't modify HANDOFF files from other domains** - Read only
6. **Report blocking issues immediately** - Don't wait silently

---

## Monitoring Progress

Track all 10 terminals with:

```bash
# See commits by domain
git log --oneline --all | grep -E "^[a-f0-9]+ (models|api|svc|core|sched|ops|fe-core|fe-app|test|docs):"

# Count commits per domain
for prefix in models api svc core sched ops fe-core fe-app test docs; do
  echo "$prefix: $(git log --oneline | grep "^[a-f0-9]* $prefix:" | wc -l)"
done

# Check for any HANDOFF files
ls -la HANDOFF_*.md 2>/dev/null || echo "No handoffs pending"
```

---

## Scaling Notes

- **Current capacity**: 10 terminals × 5 agents = 50 parallel workers
- **File ownership**: 100% exclusive - zero chance of conflict
- **Commit ordering**: Independent - merge order doesn't matter
- **Branch strategy**: All push to same feature branch
- **Conflict resolution**: None needed if domains respected
