<!--
Generate multi-terminal coordination document for parallel session work.
Creates structured handoff protocol for marathon sessions across multiple terminals.
Use when coordinating 5-10 terminal parallel execution.
-->

Arguments: $ARGUMENTS

---

***REMOVED******REMOVED*** Overview

This command generates a structured handoff document for coordinating parallel work across multiple terminals or sessions.

***REMOVED******REMOVED*** Usage

```
/handoff-session                         ***REMOVED*** Default 5 streams, 10 terminals
/handoff-session --streams=3             ***REMOVED*** Limit to 3 work streams
/handoff-session --terminals=5           ***REMOVED*** Limit to 5 terminals
/handoff-session "MCP tools marathon"    ***REMOVED*** Named session
```

***REMOVED******REMOVED*** Options

| Option | Default | Description |
|--------|---------|-------------|
| `--streams` | 5 | Number of parallel work streams |
| `--terminals` | 10 | Number of terminals to coordinate |
| `--output` | Scratchpad | Output location |

***REMOVED******REMOVED*** Behavior

1. **Analyze Current State** - Check git status, open tasks

2. **Generate Assignment Matrix**:
   ```
   Terminal 1-3: Stream A (MCP tools, scheduling engine)
   Terminal 4-6: Stream B (Backend tests, compliance)
   Terminal 7-8: Stream C (Frontend development)
   Terminal 9:   Stream D (Integration, cross-domain)
   Terminal 10:  Stream E (Security, performance)
   ```

3. **Create Handoff Document** at `.claude/Scratchpad/PARALLEL_SESSION_[timestamp].md`

4. **Define Checkpoints** - Synchronization points for streams

***REMOVED******REMOVED*** Output Format

```markdown
***REMOVED*** Parallel Session: [Name]

> Started: [timestamp]
> Terminals: 10
> Streams: 5

***REMOVED******REMOVED*** Stream Assignment

| Stream | Terminals | Domain | Coordinator |
|--------|-----------|--------|-------------|
| A | 1-3 | MCP/Scheduling | COORD_ENGINE |
| B | 4-6 | Backend Tests | COORD_QUALITY |
| C | 7-8 | Frontend | COORD_FRONTEND |
| D | 9 | Integration | COORD_OPS |
| E | 10 | Security | COORD_QUALITY |

***REMOVED******REMOVED*** Current Status

***REMOVED******REMOVED******REMOVED*** Stream A (Terminals 1-3)
**Status:** In Progress (40%)
**Last Commit:** abc123
**Blocking:** None
**Next:** Complete tool registration

***REMOVED******REMOVED******REMOVED*** Stream B (Terminals 4-6)
**Status:** Waiting
**Blocked By:** Stream A (integration point)
**Next:** Begin test execution after checkpoint

***REMOVED******REMOVED*** Checkpoints

1. [ ] Checkpoint 1: All schemas aligned (Streams A, B)
2. [ ] Checkpoint 2: Integration tests pass (Streams A, B, D)
3. [ ] Checkpoint 3: Security review complete (Stream E)

***REMOVED******REMOVED*** Signal State

| Signal | Stream | Time |
|--------|--------|------|
| STARTED | A | 10:00 |
| PROGRESS(40%) | A | 10:15 |
| BLOCKED | B | 10:10 |
```

***REMOVED******REMOVED*** Related Commands

- `/parallel-explore` - Codebase exploration
- `/parallel-implement` - Multi-agent implementation
- `/parallel-test` - Test execution
