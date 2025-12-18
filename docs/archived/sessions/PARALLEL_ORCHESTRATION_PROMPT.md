# Parallel Opus Orchestration System

**For 5 Claude Code terminals, each spawning up to 5 Task agents = 25 parallel workers**

## Overview

This document defines the parallel development protocol for the Autonomous-Assignment-Program-Manager project. Each terminal operates in an exclusive domain to prevent file conflicts.

---

## Domain Territory Map

| Terminal | Domain Name | Exclusive Paths | Commit Prefix |
|----------|-------------|-----------------|---------------|
| T1 | CORE | `backend/app/models/`, `backend/app/schemas/`, `backend/app/db/`, `backend/alembic/` | `core:` |
| T2 | API | `backend/app/api/`, `backend/app/services/`, `backend/app/core/` | `api:` |
| T3 | SCHED | `backend/app/scheduling/` | `sched:` |
| T4 | FE | `frontend/src/`, `frontend/public/` | `fe:` |
| T5 | TEST | `backend/tests/`, `frontend/__tests__/`, `docs/`, root `*.md` | `test:` or `docs:` |

---

## Conflict Prevention Protocol

### Rules for All Terminals

1. **ONLY edit files in YOUR domain** - No exceptions
2. **Check git status before editing** - Ensure no uncommitted changes from other terminals
3. **Use your commit prefix** - Makes merge sequence clear
4. **Push to the designated branch** - All terminals push to the same branch
5. **Create HANDOFF file if you need cross-domain changes** - Write `HANDOFF_FROM_[DOMAIN].md`

### HANDOFF File Format

```markdown
# Handoff from [DOMAIN]

## Required Changes

### For [TARGET_DOMAIN]:
- [ ] File: `path/to/file.py`
- [ ] Change needed: Description of what needs to be added/modified
- [ ] Reason: Why this is needed
- [ ] Blocking: Yes/No (does your work depend on this?)
```

---

## Terminal Prompt Templates

### TERMINAL 1: BACKEND CORE

```
You are the BACKEND CORE orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/models/
- backend/app/schemas/
- backend/app/db/
- backend/alembic/

OFF LIMITS (do not touch):
- backend/app/api/
- backend/app/services/
- backend/app/scheduling/
- frontend/
- tests/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "core: "
3. If you need API/scheduling/frontend changes, write HANDOFF_FROM_CORE.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 2: BACKEND API

```
You are the BACKEND API orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/api/
- backend/app/services/
- backend/app/core/

OFF LIMITS (do not touch):
- backend/app/models/
- backend/app/schemas/
- backend/app/scheduling/
- frontend/
- tests/

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

### TERMINAL 3: SCHEDULING ENGINE

```
You are the SCHEDULING ENGINE orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/app/scheduling/

OFF LIMITS (do not touch):
- backend/app/models/
- backend/app/schemas/
- backend/app/api/
- frontend/
- tests/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "sched: "
3. If you need model/schema/API changes, write HANDOFF_FROM_SCHED.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 4: FRONTEND

```
You are the FRONTEND orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- frontend/src/
- frontend/public/

OFF LIMITS (do not touch):
- backend/
- frontend/__tests__/ (belongs to TEST domain)
- docs/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "fe: "
3. If you need backend API changes, write HANDOFF_FROM_FE.md
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Handoffs needed: [Yes/No, details]
- Status: [Complete/Blocked/Partial]
```

### TERMINAL 5: TESTS & DOCS

```
You are the TESTS & DOCS orchestrator for Autonomous-Assignment-Program-Manager.

BRANCH: claude/[session-branch-name]

YOUR EXCLUSIVE DOMAIN:
- backend/tests/
- frontend/__tests__/
- docs/
- Root *.md files (README.md, CHANGELOG.md, USER_GUIDE.md, etc.)
- EXCEPT: Do not modify HANDOFF_*.md files created by other terminals

OFF LIMITS (do not touch):
- backend/app/
- frontend/src/

YOUR TASK:
[INSERT SPECIFIC TASK]

EXECUTION RULES:
1. Spawn up to 5 parallel Task agents for files in YOUR domain only
2. Commit with prefix "test: " or "docs: "
3. READ all HANDOFF_*.md files to understand what changed
4. Push to branch when complete

REPORT FORMAT:
- Files modified: [list]
- Commits made: [list with hashes]
- Test results: [pass/fail counts]
- Status: [Complete/Blocked/Partial]
```

---

## Meta-Session Workflow

### Phase 1: Launch
1. Human creates 5 Claude Code terminals via Comet
2. Each terminal receives its domain-specific prompt with task
3. All terminals work in parallel

### Phase 2: Execution
- Each terminal spawns up to 5 Task agents within its domain
- Maximum 25 parallel workers
- Each commits and pushes independently

### Phase 3: Collection
1. Human collects all HANDOFF_*.md files
2. Reviews for cross-domain dependencies
3. Resolves any conflicts

### Phase 4: Merge
1. `git log --oneline` to see all commits by prefix
2. Resolve any merge conflicts (rare if domains respected)
3. Run full test suite
4. Create PR or merge to main

---

## Example Task Distribution

**Goal: Implement GPT 5.2 Pro's edge case checklist**

| Terminal | Specific Task |
|----------|---------------|
| T1: CORE | Add `version` field to Assignment, add `generation_lock` to ScheduleRun |
| T2: API | Clean up console.logs, add rate limiting, improve error messages |
| T3: SCHED | Add infeasibility diagnostics, improve solver feedback |
| T4: FE | Handle 207/409 status codes, add conflict resolution UI, cache invalidation |
| T5: TEST | Write E2E tests for new behaviors, update API docs |

---

## Safety Notes

- **Never force push** - Only regular push
- **Never edit outside your domain** - Create HANDOFF instead
- **Always check git status first** - Avoid stepping on uncommitted work
- **Use atomic commits** - One logical change per commit
