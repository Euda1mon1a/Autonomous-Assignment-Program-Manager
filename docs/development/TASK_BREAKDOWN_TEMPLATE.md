# Task Breakdown Template

Use this template to plan parallel work distribution across T1-T5 terminals.

---

## Instructions

1. Copy this template to a new file: `ROUND_XX_PARALLEL_TASKS.md`
2. Fill in the feature name and goal
3. Break down tasks by terminal domain
4. Identify dependencies between terminals
5. Launch terminals with their specific tasks

---

# Task Breakdown: [Feature Name]

**Branch:** `claude/[branch-name]`
**Date:** YYYY-MM-DD

## High-Level Goal

[One sentence description of what we're building]

---

## Status Dashboard

| Terminal | Status | Tasks | Completed | Blocked |
|----------|--------|-------|-----------|---------|
| T1:CORE  | ⏸️     | 0     | 0         | 0       |
| T2:API   | ⏸️     | 0     | 0         | 0       |
| T3:SCHED | ⏸️     | 0     | 0         | 0       |
| T4:FE    | ⏸️     | 0     | 0         | 0       |
| T5:TEST  | ⏸️     | 0     | 0         | 0       |

**Status Key:** ⏸️ Not started | 🟡 In progress | 🟢 Complete | 🔴 Blocked

---

## T1: CORE - Tasks

**Estimated Subagents:** X

| # | Task | File(s) | Depends On | Status |
|---|------|---------|------------|--------|
| 1 | [Task description] | `backend/app/models/xxx.py` | - | [ ] |
| 2 | [Task description] | `backend/app/schemas/xxx.py` | Task 1 | [ ] |
| 3 | [Task description] | `backend/alembic/versions/` | Task 1 | [ ] |

**Handoffs needed:** [None / List what other domains need]

---

## T2: API - Tasks

**Estimated Subagents:** X

| # | Task | File(s) | Depends On | Status |
|---|------|---------|------------|--------|
| 1 | [Task description] | `backend/app/api/routes/xxx.py` | T1 schemas | [ ] |
| 2 | [Task description] | `backend/app/services/xxx.py` | - | [ ] |

**Handoffs needed:** [None / List what other domains need]

---

## T3: SCHED - Tasks

**Estimated Subagents:** X

| # | Task | File(s) | Depends On | Status |
|---|------|---------|------------|--------|
| 1 | [Task description] | `backend/app/scheduling/xxx.py` | - | [ ] |

**Handoffs needed:** [None / List what other domains need]

---

## T4: FE - Tasks

**Estimated Subagents:** X

| # | Task | File(s) | Depends On | Status |
|---|------|---------|------------|--------|
| 1 | [Task description] | `frontend/src/components/xxx.tsx` | T2 API | [ ] |
| 2 | [Task description] | `frontend/src/lib/api.ts` | T2 API | [ ] |

**Handoffs needed:** [None / List what other domains need]

---

## T5: TEST - Tasks

**Estimated Subagents:** X

| # | Task | File(s) | Depends On | Status |
|---|------|---------|------------|--------|
| 1 | [Task description] | `backend/tests/test_xxx.py` | T1-T3 | [ ] |
| 2 | [Task description] | `frontend/__tests__/xxx.test.tsx` | T4 | [ ] |
| 3 | [Task description] | `docs/xxx.md` | All | [ ] |

**Handoffs needed:** [None / Read all HANDOFF_*.md files]

---

## Execution Order

```
Phase 1: [Which terminals can start immediately]
    └── T1, T2, T3 (no dependencies)

Phase 2: [Which terminals wait for Phase 1]
    └── T4 (after T2 API contracts ready)

Phase 3: [Final phase]
    └── T5 (after implementation complete)
```

---

## Dependencies Graph

```
T1 ──┬──> T2 ──┐
     │         ├──> T4 ──> T5
     └──> T3 ──┘
```

---

## Success Criteria

- [ ] All migrations run successfully
- [ ] All existing tests pass
- [ ] New tests written and passing
- [ ] No HANDOFF files remaining unaddressed
- [ ] Documentation updated
- [ ] CHANGELOG updated

---

## Terminal Prompts

### T1 Prompt
```
You are the BACKEND CORE orchestrator.
BRANCH: claude/[branch-name]
YOUR DOMAIN: models/, schemas/, db/, alembic/
YOUR TASKS:
1. [Copy tasks from T1 section]
2. ...
Commit with prefix "core:" and push when complete.
```

### T2 Prompt
```
You are the BACKEND API orchestrator.
BRANCH: claude/[branch-name]
YOUR DOMAIN: api/, services/, core/
YOUR TASKS:
1. [Copy tasks from T2 section]
2. ...
Commit with prefix "api:" and push when complete.
```

### T3 Prompt
```
You are the SCHEDULING ENGINE orchestrator.
BRANCH: claude/[branch-name]
YOUR DOMAIN: scheduling/
YOUR TASKS:
1. [Copy tasks from T3 section]
2. ...
Commit with prefix "sched:" and push when complete.
```

### T4 Prompt
```
You are the FRONTEND orchestrator.
BRANCH: claude/[branch-name]
YOUR DOMAIN: frontend/src/, frontend/public/
YOUR TASKS:
1. [Copy tasks from T4 section]
2. ...
Commit with prefix "fe:" and push when complete.
```

### T5 Prompt
```
You are the TESTS & DOCS orchestrator.
BRANCH: claude/[branch-name]
YOUR DOMAIN: tests/, __tests__/, docs/, root *.md
YOUR TASKS:
1. [Copy tasks from T5 section]
2. ...
Commit with prefix "test:" or "docs:" and push when complete.
```

---

## Post-Execution Checklist

- [ ] All 5 terminals complete
- [ ] Collect HANDOFF_*.md files
- [ ] `git log --oneline -20` to review commits
- [ ] `git pull` to sync all changes
- [ ] Run full test suite: `pytest backend/tests/`
- [ ] Run frontend tests: `npm test`
- [ ] Resolve any merge conflicts
- [ ] Create PR or merge to main
