# PAI Agent Spawning Guide

> **Last Updated:** 2026-01-16
> **Feature Branch:** `feat/mcp-agent-spawning`
> **Status:** Active

---

## Overview

The PAI (Programmable AI) Agent Spawning system enables Claude Code to delegate specialized tasks to purpose-built AI agents. Each agent has defined capabilities, chain-of-command relationships, and governance rules.

This system is part of the **PAI² Framework** (Parallel Agentic Infrastructure × Personal Artificial Intelligence), which builds on [Daniel Miessler's PAI](https://github.com/danielmiessler/Personal_AI_Infrastructure) and extends it for multi-agent orchestration in institutional contexts.

### Why Use Agent Spawning?

| Benefit | Description |
|---------|-------------|
| **Specialization** | Domain-specific agents (SCHEDULER, COMPLIANCE_AUDITOR) outperform generalists |
| **Governance** | Spawn chains enforce accountability and proper context flow |
| **Tiered Resources** | Match model capability (haiku/sonnet/opus) to task complexity |
| **Audit Trail** | All spawns are logged for compliance and debugging |
| **Checkpointing** | Agents persist state for long-running or interrupted work |

### Key Concepts

- **Spawn Chain**: Parent-child authorization rules (who can spawn whom)
- **Identity Card**: Agent definition with standing orders and escalation triggers
- **Checkpoint**: State persistence for resumption across context limits
- **Agent Registry**: Central manifest of all available agents (`.claude/agents.yaml`)

### PAI² Core Principles

The spawning system follows four guiding principles from the PAI² framework:

| Principle | Description |
|-----------|-------------|
| **Delegate, Don't Direct** | Give mission intent, not step-by-step recipes |
| **Parallelize Where Possible** | Independent tasks run concurrently via party skills |
| **Escalate When Blocked** | Agents own their domain but escalate at boundaries |
| **Tools Over Intelligence** | MCP tools encode domain knowledge the model doesn't have |

**Mission-Type Orders (Auftragstaktik)**

Write missions as intent, not instructions:

| Bad (Recipe) | Good (Mission) |
|--------------|----------------|
| "Create SwapCancellationService in backend/app/services/..." | "Enable automatic swap rollback for ACGME violations. Audit trail required." |
| "Run pytest tests/test_scheduler.py -v" | "Validate scheduler changes don't break existing behavior" |
| "Add a try/catch around line 45" | "Make the swap executor resilient to database timeouts" |

---

## Quick Start

### Using the `/spawn-agent` Skill

The simplest way to spawn an agent:

```bash
/spawn-agent SCHEDULER Generate Block 10 schedule with ACGME compliance
/spawn-agent COMPLIANCE_AUDITOR Audit Block 10 for work hour violations
/spawn-agent G2_RECON Find all constraint implementations in the codebase
```

### Using the MCP Tool Directly

For programmatic spawning in orchestration workflows:

```python
# 1. Call the MCP factory tool
spec = mcp__residency-scheduler__spawn_agent_tool(
    agent_name="COMPLIANCE_AUDITOR",
    mission="Audit Block 10 for ACGME violations",
    context={"block_number": 10}
)

# 2. Execute via Task()
Task(
    prompt=spec["full_prompt"],
    subagent_type=spec["subagent_type"],  # "general-purpose"
    model=spec["model"],                   # haiku/sonnet/opus
    max_turns=spec["max_turns"],           # 5/20/50 based on tier
    description=f"{spec['agent_name']}: {spec['mission'][:30]}..."
)
```

### Common Agent Use Cases

| Agent | Use Case | Tier |
|-------|----------|------|
| `SCHEDULER` | Schedule generation, CP-SAT solver operations | Specialist |
| `COMPLIANCE_AUDITOR` | ACGME compliance validation | Specialist |
| `SWAP_MANAGER` | Schedule swap execution and validation | Specialist |
| `G2_RECON` | Codebase exploration and reconnaissance | G-Staff |
| `COORD_ENGINE` | Scheduling engine coordination | Coordinator |
| `ARCHITECT` | Architecture decisions, design work | Deputy |

---

## How It Works

### Spawn Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        SPAWN WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. ORCHESTRATOR/Parent calls spawn_agent_tool                   │
│           │                                                      │
│           ▼                                                      │
│  2. MCP Tool validates spawn chain                               │
│     ┌──────────────────────────────────┐                        │
│     │  Can parent spawn this child?    │                        │
│     │  - Check agents.yaml can_spawn   │                        │
│     │  - Log violation if unauthorized │                        │
│     └──────────────────────────────────┘                        │
│           │                                                      │
│           ▼                                                      │
│  3. MCP Tool loads identity card                                 │
│     ┌──────────────────────────────────┐                        │
│     │  .claude/Identities/AGENT.md     │                        │
│     │  - Standing orders               │                        │
│     │  - Escalation triggers           │                        │
│     │  - Key constraints               │                        │
│     └──────────────────────────────────┘                        │
│           │                                                      │
│           ▼                                                      │
│  4. MCP Tool injects RAG context (if enabled)                    │
│     ┌──────────────────────────────────┐                        │
│     │  Query: mission + relevant_docs  │                        │
│     │  Returns: domain-specific context│                        │
│     └──────────────────────────────────┘                        │
│           │                                                      │
│           ▼                                                      │
│  5. MCP Tool returns AgentSpec                                   │
│     ┌──────────────────────────────────┐                        │
│     │  - full_prompt                   │                        │
│     │  - model (haiku/sonnet/opus)     │                        │
│     │  - max_turns (5/20/50)           │                        │
│     │  - checkpoint_path               │                        │
│     │  - escalation_target             │                        │
│     └──────────────────────────────────┘                        │
│           │                                                      │
│           ▼                                                      │
│  6. Claude Code executes via Task()                              │
│     ┌──────────────────────────────────┐                        │
│     │  Task(                           │                        │
│     │    prompt=spec.full_prompt,      │                        │
│     │    model=spec.model,             │                        │
│     │    max_turns=spec.max_turns      │                        │
│     │  )                               │                        │
│     └──────────────────────────────────┘                        │
│           │                                                      │
│           ▼                                                      │
│  7. Agent writes checkpoint before termination                   │
│           │                                                      │
│           ▼                                                      │
│  8. Audit trail logged                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Spawn Chain Validation

Agents can only be spawned by their authorized parents. This enforces:

- **Accountability**: Clear ownership of delegated work
- **Context Flow**: Proper handoff of mission parameters
- **Predictable Escalation**: Known path back up the chain

**Example Chain:**
```
ORCHESTRATOR
    └── ARCHITECT (Deputy)
            └── COORD_ENGINE (Coordinator)
                    └── SCHEDULER (Specialist)
```

If `SCHEDULER` tries to spawn `ARCHITECT`, the tool returns an error:
```
Error: Spawn chain violation: SCHEDULER cannot spawn ARCHITECT
Resolution: ARCHITECT should be spawned by: ORCHESTRATOR
```

### Tier-Based Model Selection

| Tier | Model | Max Turns | Use Case |
|------|-------|-----------|----------|
| **Deputy** | opus | 50 | Strategic, cross-domain work |
| **Coordinator** | sonnet | 20 | Multi-step domain coordination |
| **Specialist** | haiku | 5 | Single-shot focused tasks |
| **G-Staff** | sonnet | 15-20 | Advisory/research roles |
| **SOF** | varies | varies | Special operations |

**Rule:** Match task complexity to tier. Don't spawn opus for simple validation.

### Audit Trail Generation

Every spawn is logged to `.claude/History/agent_invocations/`:

```json
{
  "invocation_id": "20260116_143022_SCHEDULER",
  "timestamp": "2026-01-16T14:30:22",
  "agent_name": "SCHEDULER",
  "tier": "Specialist",
  "model": "haiku",
  "mission": "Generate Block 10 schedule",
  "parent_agent": "COORD_ENGINE",
  "spawn_chain_valid": true,
  "rag_injected": true,
  "checkpoint_path": ".claude/Scratchpad/AGENT_SCHEDULER_20260116_143022.md"
}
```

---

## Agent Registry

### Location

`.claude/agents.yaml`

### Structure

```yaml
version: "1.0"
generated: "2026-01-16"

agents:
  SCHEDULER:
    tier: Specialist
    model: haiku
    archetype: Generator
    role: "Schedule generation specialist - CP-SAT solver operations"
    reports_to: COORD_ENGINE
    can_spawn: []  # Terminal specialist
    max_turns: 5
    tools_access: [validate_schedule, generate_schedule, detect_conflicts]
    relevant_doc_types: [scheduling, constraints]

  COORD_ENGINE:
    tier: Coordinator
    model: sonnet
    archetype: Generator
    role: "Coordinator for Scheduling Engine & Optimization"
    reports_to: ARCHITECT
    can_spawn: [SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST]
    max_turns: 20
    tools_access: [validate_schedule, generate_schedule, detect_conflicts]
    relevant_doc_types: [scheduling, constraints, acgme]
```

### Key Fields

| Field | Description |
|-------|-------------|
| `tier` | Deputy, Coordinator, Specialist, G-Staff, SOF, Special, Oversight |
| `model` | haiku, sonnet, opus |
| `archetype` | Researcher, Validator, Generator, Critic, Synthesizer |
| `reports_to` | Parent agent in chain of command |
| `can_spawn` | List of agents this agent can spawn |
| `max_turns` | Maximum agentic turns (API round-trips) |
| `tools_access` | MCP tools this agent can use |
| `relevant_doc_types` | RAG document types to inject |

### Adding New Agents

1. Create identity card: `.claude/Identities/NEW_AGENT.identity.md`
2. Add entry to `.claude/agents.yaml`
3. Update parent's `can_spawn` list
4. Test spawn chain with `/spawn-agent NEW_AGENT test mission`

---

## Identity Cards

### Location

`.claude/Identities/`

### Format

```markdown
# SCHEDULER Identity Card

## Identity
- **Role:** Schedule generation specialist - CP-SAT solver operations
- **Tier:** Specialist
- **Model:** haiku

## Boot Instruction (EXECUTE FIRST)
Read `.claude/Governance/CAPABILITIES.md` to discover your available tools.

## Chain of Command
- **Reports To:** COORD_ENGINE
- **Can Spawn:** None (terminal specialist)
- **Escalate To:** COORD_ENGINE

## Standing Orders (Execute Without Asking)
1. Generate schedules using CP-SAT solver with defined constraints
2. Validate all schedules against ACGME compliance rules
3. Create database backups before any schedule write operations
4. Run constraint propagation and optimization loops
5. Log solver metrics and decision variables

## Escalation Triggers (MUST Escalate)
- ACGME violations detected in generated schedule
- Solver timeout exceeding 5 minutes
- Unresolvable constraint conflicts
- Resource exhaustion (memory/CPU)
- Database backup failures before write operations

## Key Constraints
- Do NOT write schedules without backup verification
- Do NOT modify ACGME compliance rules
- Do NOT skip constraint validation steps
- Do NOT proceed if solver is infeasible

## One-Line Charter
"Generate compliant schedules efficiently, validate exhaustively, protect data."
```

### Required Sections

| Section | Purpose |
|---------|---------|
| **Identity** | Role, tier, model |
| **Boot Instruction** | First action upon spawn |
| **Chain of Command** | Reporting structure |
| **Standing Orders** | Pre-authorized actions |
| **Escalation Triggers** | When to escalate |
| **Key Constraints** | Non-negotiable rules |
| **One-Line Charter** | Mission philosophy |

---

## Checkpoint Protocol

### When Agents Checkpoint

| Trigger | Description |
|---------|-------------|
| Context exhaustion | >80% context used |
| Task boundary | Natural stopping point |
| Blocker encountered | Can't proceed without help |
| Risky operation | Before DB writes, git operations |
| Milestone reached | Significant progress worth saving |

### Checkpoint File Format

**Location:** `.claude/Scratchpad/AGENT_{NAME}_{TIMESTAMP}.md`

**Example:** `AGENT_SCHEDULER_20260116_143022.md`

```markdown
# Agent Checkpoint: SCHEDULER

**Mission:** Generate Block 10 schedule with new weekly requirements
**Status:** In Progress
**Checkpoint:** 2 of 3
**Timestamp:** 2026-01-16T15:00:45
**Context Used:** 75%

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
  "solver_results": {
    "solutions_found": 15,
    "best_objective": 0.87,
    "top_3_indices": [7, 3, 11]
  },
  "validation_pending": [7, 3, 11]
}
```

---

## Next Steps

1. Run ACGME validator on solutions 7, 3, 11
2. Compare fairness metrics (Gini coefficient)
3. Select and checkpoint final solution

---

## Resume Instructions

To resume this work:
```python
spec = spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="RESUME: Complete Block 10 schedule generation",
    context={
        "checkpoint_path": ".claude/Scratchpad/AGENT_SCHEDULER_20260116_150045.md",
        "top_solutions": [7, 3, 11]
    }
)
```

---

*Checkpoint written by SCHEDULER at 2026-01-16T15:00:45*
```

### Resume Patterns

#### Direct Resume
Agent continues exactly where it left off:

```python
checkpoint = Read(".claude/Scratchpad/AGENT_SCHEDULER_20260116_143022.md")
spec = spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="RESUME: Complete Block 10 schedule generation",
    context={"checkpoint_path": checkpoint_path}
)
```

#### Handoff Resume
Different agent picks up the work:

```python
spec = spawn_agent_tool(
    agent_name="COMPLIANCE_AUDITOR",
    mission="Validate SCHEDULER output from checkpoint",
    context={
        "source_checkpoint": ".claude/Scratchpad/AGENT_SCHEDULER_20260116_143022.md",
        "handoff_from": "SCHEDULER"
    }
)
```

#### Escalation Resume
ORCHESTRATOR resolves a blocker and resumes:

```python
spec = spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="RESUME: Continue with resolved blocker",
    context={
        "checkpoint_path": checkpoint_path,
        "blocker_resolution": {
            "original_blocker": "Missing faculty availability",
            "resolution": "Faculty availability loaded to DB"
        }
    }
)
```

---

## MCP Tool Reference

### `spawn_agent_tool`

**Purpose:** Prepare a PAI agent for spawning via Claude Code Task()

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_name` | string | Yes | Agent identifier from `.claude/agents.yaml` |
| `mission` | string | Yes | Task description using mission-type orders |
| `context` | dict | No | System state to inject (block_number, etc.) |
| `inject_rag` | bool | No | Query RAG for context (default: true) |
| `inject_skills` | list | No | Skills to inject (auto-matches if None) |
| `parent_agent` | string | No | Parent agent for spawn chain validation |

#### Return Value

```python
{
    "agent_name": "SCHEDULER",
    "tier": "Specialist",
    "model": "haiku",
    "full_prompt": "## BOOT CONTEXT\n[identity card]\n\n## MISSION\n...",
    "max_turns": 5,
    "subagent_type": "general-purpose",
    "checkpoint_path": ".claude/Scratchpad/AGENT_SCHEDULER_20260116_143022.md",
    "escalation_target": "COORD_ENGINE",
    "tools_access": ["validate_schedule", "generate_schedule", "detect_conflicts"],
    "can_spawn": [],
    "spawn_chain_valid": true,
    "identity_found": true,
    "rag_context": "[injected domain context]"
}
```

#### Example Usage

```python
# Basic spawn
spec = mcp__residency-scheduler__spawn_agent_tool(
    agent_name="COMPLIANCE_AUDITOR",
    mission="Audit Block 10 for ACGME violations"
)

# With spawn chain validation
spec = mcp__residency-scheduler__spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="Generate Block 10 schedule",
    parent_agent="COORD_ENGINE",
    context={"block_number": 10, "academic_year": 2026}
)

# Without RAG (faster, less context)
spec = mcp__residency-scheduler__spawn_agent_tool(
    agent_name="G2_RECON",
    mission="Find all test files",
    inject_rag=False
)
```

---

## Troubleshooting

### Spawn Chain Violation

**Error:**
```
Error: Spawn chain violation: SCHEDULER cannot spawn ARCHITECT
```

**Resolution:**
1. Check `can_spawn` list in `.claude/agents.yaml`
2. Find authorized parent for target agent
3. Either escalate to correct parent or invoke as ORCHESTRATOR

### Missing Identity Card

**Error:**
```
Error: Identity card not found for agent: NEW_AGENT
```

**Resolution:**
1. Check if agent exists in `.claude/agents.yaml`
2. Create identity card at `.claude/Identities/NEW_AGENT.identity.md`
3. Follow template structure from `.claude/Identities/TEMPLATE.identity.md`

### RAG Injection Failure

**Error:**
```
Warning: RAG context injection failed: [error details]
```

**Resolution:**
1. Check RAG server health: `mcp__residency-scheduler__rag_health`
2. Verify `relevant_doc_types` in agents.yaml are valid
3. Spawn with `inject_rag=False` as workaround

### Agent Registry Not Found

**Error:**
```
Error: Agent registry not found at .claude/agents.yaml
```

**Resolution:**
1. Verify `.claude/agents.yaml` exists
2. Check for YAML syntax errors: `python -c "import yaml; yaml.safe_load(open('.claude/agents.yaml'))"`
3. Regenerate from identity cards if needed

### Checkpoint Resume Failure

**Error:**
```
Error: Cannot parse checkpoint state from [path]
```

**Resolution:**
1. Verify checkpoint file exists and is readable
2. Check JSON in `## State` section is valid
3. Manually extract state and pass in context dict

---

## Best Practices

### Do's (PAI² Aligned)

- **Delegate, don't direct**: Write missions as intent, not step-by-step recipes
- **Match tier to task**: Use haiku for simple validation, opus for strategic work
- **Parallelize independent work**: Use party skills for concurrent agent spawning
- **Write checkpoints early**: Don't wait until context exhaustion
- **Include state in checkpoints**: JSON block enables clean resume
- **Validate spawn chains**: Use `parent_agent` parameter for governance
- **Log escalations**: Always explain why you're escalating
- **Trust MCP tools**: They encode domain knowledge the model doesn't have

### Don'ts

- **Don't write recipe missions**: "Add try/catch on line 45" → "Make swap executor resilient"
- **Don't bypass spawn chains**: Even if you can invoke directly, respect hierarchy
- **Don't spawn Deputies for simple tasks**: Expensive and unnecessary
- **Don't ignore escalation triggers**: Identity cards define them for a reason
- **Don't hardcode agent names**: Use agents.yaml for discoverable registry
- **Don't skip RAG for domain tasks**: Context injection improves quality
- **Don't serialize independent tasks**: Use parallel spawning when possible

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `.claude/Governance/PAI_SQUARED.md` | **PAI² framework philosophy and principles** |
| `.claude/agents.yaml` | Agent registry (tiers, models, spawn chains) |
| `.claude/Identities/` | Identity cards with standing orders |
| `.claude/Governance/SPAWN_CHAINS.md` | Spawn authority matrix |
| `.claude/Governance/CHECKPOINT_PROTOCOL.md` | Full checkpoint specification |
| `.claude/Governance/HIERARCHY.md` | Command structure philosophy |
| `.claude/skills/spawn-agent/SKILL.md` | `/spawn-agent` skill documentation |
| `docs/development/AGENT_SKILLS.md` | All agent skills reference |

### External References

- [Daniel Miessler's PAI](https://github.com/danielmiessler/Personal_AI_Infrastructure) - Original framework inspiration
- [Building a Personal AI Infrastructure](https://danielmiessler.com/blog/personal-ai-infrastructure) - Background blog post

---

*PAI²: System over intelligence. Delegate with governance, parallelize with purpose, checkpoint with discipline.*
