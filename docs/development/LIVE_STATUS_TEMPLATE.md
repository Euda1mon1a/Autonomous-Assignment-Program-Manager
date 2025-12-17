***REMOVED*** Live Session Status Template

Use this template during active parallel sessions. Each terminal appends updates to track real-time progress.

---

***REMOVED******REMOVED*** Instructions

1. Copy to `LIVE_STATUS.md` at session start
2. Each terminal updates its section when:
   - Starting work
   - Completing a task
   - Getting blocked
   - Creating commits
3. Human reviews periodically to monitor progress

---

***REMOVED*** Live Session Status

***REMOVED******REMOVED*** Session Info

**Session ID:** [round-XX / feature-name]
**Branch:** `claude/[branch-name]`
**Started:** YYYY-MM-DD HH:MM UTC
**Status:** 🟡 In Progress

---

***REMOVED******REMOVED*** Quick Dashboard

| Terminal | Status | Progress | Commits | Handoffs |
|----------|--------|----------|---------|----------|
| T1:CORE  | ⏸️     | 0/0      | 0       | 0        |
| T2:API   | ⏸️     | 0/0      | 0       | 0        |
| T3:SCHED | ⏸️     | 0/0      | 0       | 0        |
| T4:FE    | ⏸️     | 0/0      | 0       | 0        |
| T5:TEST  | ⏸️     | 0/0      | 0       | 0        |

**Status Key:** ⏸️ Not started | 🟡 Active | 🟢 Complete | 🔴 Blocked | ⏳ Waiting

---

***REMOVED******REMOVED*** T1: CORE

**Status:** ⏸️ Not Started
**Started:** -
**Last Update:** -

***REMOVED******REMOVED******REMOVED*** Progress
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

***REMOVED******REMOVED******REMOVED*** Commits
_None yet_

***REMOVED******REMOVED******REMOVED*** Notes
_None_

---

***REMOVED******REMOVED*** T2: API

**Status:** ⏸️ Not Started
**Started:** -
**Last Update:** -

***REMOVED******REMOVED******REMOVED*** Progress
- [ ] Task 1
- [ ] Task 2

***REMOVED******REMOVED******REMOVED*** Commits
_None yet_

***REMOVED******REMOVED******REMOVED*** Notes
_None_

---

***REMOVED******REMOVED*** T3: SCHED

**Status:** ⏸️ Not Started
**Started:** -
**Last Update:** -

***REMOVED******REMOVED******REMOVED*** Progress
- [ ] Task 1

***REMOVED******REMOVED******REMOVED*** Commits
_None yet_

***REMOVED******REMOVED******REMOVED*** Notes
_None_

---

***REMOVED******REMOVED*** T4: FE

**Status:** ⏸️ Not Started
**Started:** -
**Last Update:** -

***REMOVED******REMOVED******REMOVED*** Progress
- [ ] Task 1
- [ ] Task 2

***REMOVED******REMOVED******REMOVED*** Commits
_None yet_

***REMOVED******REMOVED******REMOVED*** Notes
_None_

---

***REMOVED******REMOVED*** T5: TEST

**Status:** ⏸️ Not Started
**Started:** -
**Last Update:** -

***REMOVED******REMOVED******REMOVED*** Progress
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

***REMOVED******REMOVED******REMOVED*** Commits
_None yet_

***REMOVED******REMOVED******REMOVED*** Notes
_None_

---

***REMOVED******REMOVED*** Handoff Queue

| From | To | File | Status | Description |
|------|----|------|--------|-------------|
| - | - | - | - | _No handoffs yet_ |

---

***REMOVED******REMOVED*** Blockers

| Terminal | Blocked Since | Reason | Waiting For |
|----------|---------------|--------|-------------|
| - | - | - | _No blockers_ |

---

***REMOVED******REMOVED*** Session Log

| Time (UTC) | Terminal | Event |
|------------|----------|-------|
| HH:MM | - | Session started |

---

***REMOVED******REMOVED*** Example Updates

***REMOVED******REMOVED******REMOVED*** When a terminal starts:
```markdown
***REMOVED******REMOVED*** T1: CORE

**Status:** 🟡 Active
**Started:** 14:30 UTC
**Last Update:** 14:30 UTC

***REMOVED******REMOVED******REMOVED*** Progress
- [ ] Add version field to Assignment
- [ ] Update schemas
- [ ] Create migration
```

***REMOVED******REMOVED******REMOVED*** When a task completes:
```markdown
***REMOVED******REMOVED******REMOVED*** Progress
- [x] Add version field to Assignment ✓
- [x] Update schemas ✓
- [ ] Create migration

***REMOVED******REMOVED******REMOVED*** Commits
- `abc1234` core: Add version field to Assignment model
- `def5678` core: Update AssignmentResponse schema
```

***REMOVED******REMOVED******REMOVED*** When blocked:
```markdown
**Status:** 🔴 Blocked
**Last Update:** 14:45 UTC

***REMOVED******REMOVED******REMOVED*** Notes
Blocked: Need T1 to add `solver_score` field to Assignment model.
Created: HANDOFF_FROM_SCHED.md
```

***REMOVED******REMOVED******REMOVED*** When complete:
```markdown
**Status:** 🟢 Complete
**Started:** 14:30 UTC
**Completed:** 15:15 UTC

***REMOVED******REMOVED******REMOVED*** Progress
- [x] All tasks complete ✓

***REMOVED******REMOVED******REMOVED*** Commits
- `abc1234` core: Add version field
- `def5678` core: Update schemas
- `ghi9012` core: Create migration 003
```
