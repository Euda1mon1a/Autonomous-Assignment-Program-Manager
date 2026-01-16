# Agent Checkpoint Protocol

> **Purpose:** Standardize state persistence for spawned PAI agents
> **Created:** 2026-01-16
> **Status:** Active

---

## Overview

Subagents are born and die with their context. Checkpoints allow agents to:
1. Persist progress across context limits
2. Hand off work to successor agents
3. Enable ORCHESTRATOR supervision
4. Create audit trails for complex operations

---

## When to Checkpoint

### Always Checkpoint
- Before context exhaustion (>80% used)
- At natural task boundaries
- When encountering blockers
- Before risky operations (DB writes, git operations)
- When switching execution modes

### Optional Checkpoint
- After significant progress milestones
- When accumulating findings for synthesis
- Before delegating to sub-agents
- When work may span multiple sessions

---

## File Naming Convention

```
.claude/Scratchpad/AGENT_{AGENT_NAME}_{TIMESTAMP}.md
```

### Examples

```
AGENT_SCHEDULER_20260116_143022.md
AGENT_COMPLIANCE_AUDITOR_20260116_150530.md
AGENT_G2_RECON_20260116_161245.md
```

### Components

| Part | Format | Example |
|------|--------|---------|
| Prefix | `AGENT_` | `AGENT_` |
| Agent Name | UPPER_SNAKE_CASE | `SCHEDULER` |
| Timestamp | `YYYYMMDD_HHMMSS` | `20260116_143022` |
| Extension | `.md` | `.md` |

---

## Checkpoint Format

```markdown
# Agent Checkpoint: {AGENT_NAME}

**Mission:** {Original mission description}
**Status:** {In Progress | Blocked | Completed | Escalated}
**Checkpoint:** {N of M} (if part of series)
**Timestamp:** {ISO 8601}
**Context Used:** {Percentage}%

---

## Progress

### Completed
- [x] {Task 1}
- [x] {Task 2}

### In Progress
- [ ] {Current task with status notes}

### Remaining
- [ ] {Task 3}
- [ ] {Task 4}

---

## State

```json
{
  "key_data": "relevant state",
  "discovered_info": ["item1", "item2"],
  "decisions_made": {
    "decision1": "rationale"
  }
}
```

---

## Findings (if applicable)

### {Category 1}
{Detailed findings}

### {Category 2}
{Detailed findings}

---

## Blockers (if any)

| Blocker | Impact | Resolution Path |
|---------|--------|-----------------|
| {Description} | {How it blocks} | {Suggested action} |

---

## Next Steps

1. {Specific next action}
2. {Specific next action}
3. {Specific next action}

---

## Escalation (if needed)

**To:** {COORDINATOR or ORCHESTRATOR}
**Reason:** {Why escalation needed}
**Decision Needed:** {What needs to be decided}

---

## Resume Instructions

To resume this work:
1. Load checkpoint into context
2. {Specific preparation steps}
3. Call spawn_agent_tool with context containing checkpoint path

```python
spec = spawn_agent_tool(
    agent_name="{AGENT_NAME}",
    mission="RESUME: {Continue mission description}",
    context={
        "checkpoint_path": "{this file path}",
        "state": {checkpoint_state}
    }
)
```

---

*Checkpoint written by {AGENT_NAME} at {timestamp}*
```

---

## State Serialization

### JSON State Block

The `## State` section contains serialized state as JSON. Guidelines:

**Include:**
- IDs and references (block_number, resident_ids, etc.)
- Computed results (validation_errors, optimization_scores)
- Discovery data (file_paths, function_names)
- Decision records (chosen_approach, rejected_alternatives)

**Exclude:**
- Large data (full schedules, entire files)
- Sensitive data (names, PHI)
- Transient state (cursor positions, temp files)

### Example State

```json
{
  "block_number": 10,
  "validation_run": {
    "timestamp": "2026-01-16T14:30:22",
    "errors_found": 3,
    "error_types": ["80_hour_violation", "supervision_gap"]
  },
  "solutions_explored": 15,
  "best_solution_index": 7,
  "best_objective_value": 0.87,
  "next_optimization_target": "fairness_metric"
}
```

---

## Resume Patterns

### Pattern 1: Direct Resume

Agent continues exactly where it left off.

```python
# Load checkpoint
checkpoint = Read(".claude/Scratchpad/AGENT_SCHEDULER_20260116_143022.md")

# Extract state from checkpoint
state = extract_json_state(checkpoint)

# Resume with state
spec = spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="RESUME: Complete Block 10 schedule generation",
    context={"previous_state": state, "checkpoint_path": checkpoint_path}
)
```

### Pattern 2: Handoff Resume

Different agent continues the work.

```python
# SCHEDULER checkpoint indicates need for validation
# COMPLIANCE_AUDITOR picks up

spec = spawn_agent_tool(
    agent_name="COMPLIANCE_AUDITOR",
    mission="Validate SCHEDULER output from checkpoint",
    context={
        "source_checkpoint": ".claude/Scratchpad/AGENT_SCHEDULER_20260116_143022.md",
        "handoff_from": "SCHEDULER"
    }
)
```

### Pattern 3: Escalation Resume

ORCHESTRATOR resumes blocked agent with resolution.

```python
# Agent was blocked, ORCHESTRATOR resolves

spec = spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="RESUME: Continue with resolved blocker",
    context={
        "checkpoint_path": checkpoint_path,
        "blocker_resolution": {
            "original_blocker": "Missing faculty availability",
            "resolution": "Faculty availability loaded to DB",
            "resolved_by": "ORCHESTRATOR"
        }
    }
)
```

---

## Checkpoint Chains

For long-running operations, agents may create multiple checkpoints:

```
AGENT_SCHEDULER_20260116_143022.md  # Checkpoint 1 of 3
AGENT_SCHEDULER_20260116_150045.md  # Checkpoint 2 of 3
AGENT_SCHEDULER_20260116_153012.md  # Checkpoint 3 of 3 (Final)
```

### Chain Metadata

Each checkpoint includes:
- `Checkpoint: N of M` header
- Link to previous checkpoint (if not first)
- Summary of chain progress

```markdown
**Checkpoint:** 2 of 3
**Previous:** AGENT_SCHEDULER_20260116_143022.md

## Chain Summary
- Checkpoint 1: Constraint setup complete
- Checkpoint 2 (this): Solver run complete, validation pending
- Checkpoint 3: (expected) Validation and output
```

---

## Integration with spawn_agent_tool

The MCP tool provides checkpoint support:

### At Spawn Time

```python
spec = spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="Generate Block 10 schedule",
    context={"block_number": 10}
)

# spec includes:
# {
#   "checkpoint_path": ".claude/Scratchpad/AGENT_SCHEDULER_20260116_143022.md",
#   ...
# }
```

### In Spawned Agent

The agent receives the checkpoint path in its prompt:

```markdown
## CHECKPOINT PROTOCOL

Write checkpoint to: {checkpoint_path}
Format: See .claude/Governance/CHECKPOINT_PROTOCOL.md

Checkpoint when:
- Context exceeds 80%
- Task boundary reached
- Blocker encountered
- Before risky operations
```

---

## Audit Trail Integration

Checkpoints complement the audit trail in `.claude/History/agent_invocations/`:

| Record | Location | Purpose |
|--------|----------|---------|
| Invocation | `History/agent_invocations/*.json` | Who spawned whom, when |
| State | `Scratchpad/AGENT_*.md` | What the agent found/did |
| Decision | Agent's final output | Conclusions and recommendations |

---

## Examples

### Minimal Checkpoint

```markdown
# Agent Checkpoint: G2_RECON

**Mission:** Find all ACGME validation implementations
**Status:** Completed
**Timestamp:** 2026-01-16T16:12:45

---

## Findings

Found 3 implementations:
1. `backend/app/scheduling/acgme_validator.py:45` - Main validator
2. `backend/app/services/compliance_service.py:120` - Service wrapper
3. `mcp-server/src/scheduler_mcp/server.py:1240` - MCP tool

---

## Next Steps

1. None - task complete, findings reported to COORD_ENGINE
```

### Complex Checkpoint

```markdown
# Agent Checkpoint: SCHEDULER

**Mission:** Generate Block 10 schedule with new weekly requirements
**Status:** In Progress
**Checkpoint:** 2 of 3
**Timestamp:** 2026-01-16T15:00:45
**Context Used:** 75%
**Previous:** AGENT_SCHEDULER_20260116_143022.md

---

## Progress

### Completed
- [x] Load faculty availability
- [x] Load resident preferences
- [x] Configure ACGME constraints
- [x] Run solver (found 15 solutions)

### In Progress
- [ ] Validate top 3 solutions for ACGME compliance

### Remaining
- [ ] Select best solution based on fairness metric
- [ ] Write to database with backup
- [ ] Create audit trail

---

## State

```json
{
  "block_number": 10,
  "date_range": {
    "start": "2026-03-02",
    "end": "2026-03-29"
  },
  "residents_scheduled": 24,
  "faculty_assigned": 10,
  "solver_results": {
    "solutions_found": 15,
    "solver_time_seconds": 45.2,
    "best_objective": 0.87,
    "top_3_indices": [7, 3, 11]
  },
  "validation_pending": [7, 3, 11]
}
```

---

## Findings

### Coverage Analysis
- FM Clinic: 100% coverage
- Call: 100% coverage
- Night Float: 100% coverage
- FMIT: 4 residents assigned (expected: 4)

### Optimization Notes
- Solution 7 best on workload balance
- Solution 3 best on preference satisfaction
- Solution 11 balanced but lower overall

---

## Next Steps

1. Run ACGME validator on solutions 7, 3, 11
2. Compare fairness metrics (Gini coefficient)
3. Select and checkpoint final solution
4. Proceed to database write in Checkpoint 3

---

## Resume Instructions

To resume this work:
1. Solutions are computed, need validation
2. Validation can proceed independently

```python
spec = spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="RESUME: Validate and select best Block 10 solution",
    context={
        "checkpoint_path": ".claude/Scratchpad/AGENT_SCHEDULER_20260116_150045.md",
        "top_solutions": [7, 3, 11]
    }
)
```

---

*Checkpoint written by SCHEDULER at 2026-01-16T15:00:45*
```

---

## Related Documents

- `.claude/Governance/SPAWN_CHAINS.md` - Agent spawning authority
- `.claude/Governance/HIERARCHY.md` - Command structure
- `.claude/skills/spawn-agent/SKILL.md` - Spawn skill documentation
- `.claude/agents.yaml` - Agent registry

---

*Checkpoints ensure no agent work is lost. Write early, write often.*
