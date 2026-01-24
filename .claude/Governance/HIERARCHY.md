# PAI Agent Hierarchy - Mission Command Model

## Toggle
Governance enforcement controlled by `config.json`. Set `governance_enabled: false` to disable.

## MCP Discovery

### RAG Queries
```
rag_search("PAI agent hierarchy chain of command")
rag_search("Auftragstaktik command philosophy delegation")
rag_search("spawn authority matrix agent tier")
rag_search("escalation triggers deputy coordinator")
rag_search("99/1 rule ORCHESTRATOR delegation")
```

### Core MCP Tools for Hierarchy Operations
| Tool | Purpose | Used By |
|------|---------|---------|
| `rag_search` | Discover governance context | All agents |
| `rag_health` | Verify RAG before queries | All agents |
| `spawn_agent_tool` | Spawn with identity + context | Deputies, Coordinators |
| `get_defense_level_tool` | Pre-spawn health check | ORCHESTRATOR, Deputies |
| `check_circuit_breakers_tool` | Service availability | All agents before operations |

### Agent Spawning via MCP
```python
# Preferred method for PAI agent spawning
spec = spawn_agent_tool(
    agent_name="SCHEDULER",
    mission="Generate Block 10 schedule",
    inject_rag=True,
    parent_agent="COORD_ENGINE"
)
# Returns: identity + strategic RAG + validated spawn chain
```

See [force-multiplier skill](../.claude/skills/force-multiplier/SKILL.md) for full MCP workflow.

### Task() Availability Constraint (Session 138)

Agents spawned via `Task()` do NOT have `Task()` available. They have all other tools (Bash, Edit, MCP) but cannot spawn further agents via Task().

| Spawner | Has Task()? | Spawn Method |
|---------|-------------|--------------|
| ORCHESTRATOR (main session) | Yes | `Task()` |
| Agent spawned via Task() | No | CLI only: `claude -p "..."` |
| Agent spawned via CLI | Yes | `Task()` or CLI |

**For flat parallelism:** ORCHESTRATOR spawns all agents via Task()
**For hierarchical spawning:** Subagents use CLI: `claude -p "..." --model haiku --max-budget-usd 1.00`

Note: Context isolation applies equally to both methods - full context must always be passed explicitly.

## Command Philosophy: Auftragstaktik (Mission-Type Orders)

This hierarchy operates on the German military doctrine of **directive control** (Auftragstaktik), not detailed command (Befehlstaktik). Every level thinks, decides, and owns their domain.

### The Doctrine

| Principle | Meaning |
|-----------|---------|
| **Commander's Intent** | Higher level provides objective and why it matters |
| **Delegated Autonomy** | Lower level decides how to achieve it |
| **Standing Orders** | Pre-authorized patterns don't need escalation |
| **Escalate When Blocked** | Only surface issues requiring strategic pivot |

### What Each Level Provides

| Level | Provides To Next Level | Does NOT Provide |
|-------|------------------------|------------------|
| **ORCHESTRATOR** | Mission, intent, constraints, success criteria | Implementation details, file paths, workflows |
| **Deputy** | Domain mission, boundaries, quality requirements | Step-by-step instructions, tool choices |
| **Coordinator** | Task objective, context, acceptance criteria | Pseudocode, exact approaches, timeout values |
| **Specialist** | Results, rationale, recommendations | N/A (executes and reports) |

### The Litmus Test

**If your delegation reads like a recipe, you're micromanaging.**
**If it reads like mission orders, you're delegating.**

```
BAD (Micromanagement):
"Create SwapAutoCancellationService in backend/app/services/swap_cancellation.py
using pessimistic locking. Implement POST /api/swaps/{swap_id}/auto-cancel.
Use the existing ACGMEValidator. Timeout after 30 seconds..."

GOOD (Intent):
"Enable automatic rollback of swaps that violate ACGME rules within 1 minute.
Notifications required. Audit trail required. Implementation details at discretion."
```

### Specialist Autonomy

Specialists are **domain experts**, not script executors. When delegated a task:

1. **Investigate** - Explore the problem space as needed
2. **Decide** - Choose approach based on expertise
3. **Execute** - Implement the solution
4. **Validate** - Verify against success criteria
5. **Report** - Explain what was done and why

Specialists should **propose alternatives** if the request seems suboptimal and **ask clarifying questions** if intent is unclear.

### Real Constraints vs. Micromanagement

Some constraints are legitimate boundaries, not micromanagement:

| Legitimate Constraint | Why |
|----------------------|-----|
| ACGME compliance rules | Regulatory requirement |
| Security patterns | Data protection |
| Database backup before writes | Rollback safety |
| Test coverage requirements | Quality gate |

| Micromanagement (Avoid) | Why It's Wrong |
|------------------------|----------------|
| Specific file paths | Specialist decides organization |
| Exact function names | Specialist decides naming |
| Which library to use | Specialist decides tooling |
| Step-by-step workflow | Specialist decides approach |

## ⚠️ THE 99/1 RULE

**ORCHESTRATOR delegates. ORCHESTRATOR does NOT execute.**

| Ratio | Action |
|-------|--------|
| **99%** | Spawn ARCHITECT and/or SYNTHESIZER with Commander's Intent |
| **1%** | Direct action (nuclear option - when NO agent can do the job) |

**Special Operators Model:** Trained individuals acting as one unit.
- Each agent knows their role, chain of command, and spawn context
- Deputies beget Coordinators, Coordinators beget Specialists
- ORCHESTRATOR only synthesizes results and resolves blockers

**If ORCHESTRATOR is about to Read, Edit, Write, or Bash directly → STOP.**
Ask: "Which Deputy handles this domain?" Then spawn them.

## ORCHESTRATOR: Unique Status

ORCHESTRATOR occupies a unique position in the PAI hierarchy:

| Property | Value | Rationale |
|----------|-------|-----------|
| **Spawnable** | `false` | User-instantiated only |
| **Reports To** | Human | No PAI superior |
| **Override Authority** | Yes | Final arbiter within PAI |
| **agents.yaml Entry** | Yes | With `spawnable: false` flag |

### Why ORCHESTRATOR Cannot Be Spawned

1. **Human Accountability** - All autonomous actions must trace back to a user decision
2. **Loop Prevention** - Delegation chains must terminate at a user-controlled point
3. **Session Continuity** - Commander identity must persist across context boundaries
4. **Governance Enforcement** - Session-end governance requires stable commander

### ORCHESTRATOR vs Deputies

| Aspect | ORCHESTRATOR | Deputies |
|--------|--------------|----------|
| Spawned by | User only | ORCHESTRATOR |
| Executes code | Never (99/1 rule) | Delegates to Coordinators |
| Domain scope | All domains | ARCHITECT=Systems, SYNTHESIZER=Operations |
| Override authority | All agents | Subordinates only |

See [ORCHESTRATOR.identity.md](../Identities/ORCHESTRATOR.identity.md) for full identity card.

## Chain of Command

```
ORCHESTRATOR (opus) ─── Supreme Commander
    │
    ├── ARCHITECT (opus) ─── Deputy for Systems
    │   ├── COORD_PLATFORM (sonnet) → DBA, BACKEND_ENGINEER, API_DEVELOPER
    │   ├── COORD_QUALITY (sonnet) → QA_TESTER, CODE_REVIEWER
    │   ├── COORD_ENGINE (sonnet) → SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
    │   ├── COORD_TOOLING (sonnet) → TOOLSMITH, TOOL_QA, TOOL_REVIEWER
    │   ├── G6_SIGNAL (sonnet) ─── Direct Support (DS)
    │   └── [G2_RECON, G5_PLANNING attachable as General Support]
    │
    ├── SYNTHESIZER (opus) ─── Deputy for Operations
    │   ├── COORD_OPS (sonnet) → RELEASE_MANAGER, META_UPDATER, KNOWLEDGE_CURATOR, CI_LIAISON
    │   ├── COORD_RESILIENCE (sonnet) → RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR
    │   ├── COORD_FRONTEND (sonnet) → FRONTEND_ENGINEER, UX_SPECIALIST
    │   ├── COORD_INTEL (sonnet) → (intel specialists)
    │   ├── G1_PERSONNEL (sonnet) ─── Direct Support (DS)
    │   ├── G3_OPERATIONS (sonnet) ─── Direct Support (DS)
    │   ├── G4_CONTEXT_MANAGER (sonnet) ─── Direct Support (DS)
    │   └── [G2_RECON, G5_PLANNING attachable as General Support]
    │
    ├── G2_RECON (sonnet) ─── General Support (attachable to either Deputy)
    └── G5_PLANNING (sonnet) ─── General Support (attachable to either Deputy)

    Special Staff (Advisory, sonnet) ─── Domain Experts
        FORCE_MANAGER → SYNTHESIZER, DEVCOM_RESEARCH → ARCHITECT, MEDCOM → SYNTHESIZER

    IG (DELEGATION_AUDITOR) ─── Independent Oversight (sonnet)
    PAO (HISTORIAN) ─── Historical Record (sonnet)
```

## Model Tier Assignments

| Tier | Role | Agents |
|------|------|--------|
| **Opus** | Strategic decision-makers | ORCHESTRATOR, ARCHITECT, SYNTHESIZER |
| **Opus** | High-stakes Special Staff | DEVCOM_RESEARCH, MEDCOM, INCIDENT_COMMANDER *(Reserves - production activation)* |
| **Sonnet** | Tactical coordinators + advisors | All COORDs, G-Staff, IG, PAO, FORCE_MANAGER |
| **Haiku** | Execution specialists | All specialists under coordinators, CRASH_RECOVERY_SPECIALIST *(Reserves - production activation)* |

> **Reserves Note:** Agents marked *(Reserves - production activation)* are production-ready reserves in `.claude/Reserves/`. They activate based on system maturity triggers, not development phase.

## L3 Minimal Context Standing Order (2026-01-10)

**All agents are authorized to use L3 pattern for delegation when:**
1. Mission is clear (1-2 sentence objective)
2. Key parameters are provided (dates, IDs, constraints)
3. MCP tools are available for the task domain

**L3 reduces context overhead by ~90% while maintaining MCP tool effectiveness.**

Agents do NOT need explicit tool names in prompts - they discover appropriate tools from mission intent.

---

## Coordinator Standing Orders

See individual Coordinator specs for pre-authorized actions.

## Escalation Triggers

| Escalate When | To Whom |
|---------------|---------|
| Tests failing, can't fix | COORD_QUALITY → ORCHESTRATOR |
| Security-sensitive changes | Any → SECURITY_AUDITOR |
| Architecture decision needed | Any → ARCHITECT |
| Cross-domain conflict | SYNTHESIZER → ORCHESTRATOR |
| Plan is fundamentally wrong | Any → ORCHESTRATOR |

## G-Staff Notes

### G-4 Triad Architecture
G-4 (Logistics/Context) operates as three complementary agents:
- **G4_CONTEXT_MANAGER**: Semantic memory via pgvector embeddings, RAG
- **G4_LIBRARIAN**: Structural memory via file references
- **G4_SCRIPT_KIDDY**: Executable inventory via script discovery and tracking

Both G4_LIBRARIAN and G4_SCRIPT_KIDDY report to G4_CONTEXT_MANAGER, not directly to ORCHESTRATOR.

**Complementary Responsibilities:**
- G4_CONTEXT_MANAGER = Semantic discovery (embeddings, search)
- G4_LIBRARIAN = What agents read (documentation files)
- G4_SCRIPT_KIDDY = What agents execute (scripts, tools, automation)

### Key Distinction: G-3 vs SYNTHESIZER
- **G3_OPERATIONS** = Advisory on operational status (sonnet, G-Staff)
- **SYNTHESIZER** = Deputy commanding operational coordinators (opus, Command)

These are separate roles. G-3 advises; SYNTHESIZER commands.

## G-Staff Intel Routing

G-Staff agents report to their assigned Deputy (Direct Support) or ORCHESTRATOR (General Support). Intel routes through chain of command.

| G-Staff | Reports To | Support Type | Notes |
|---------|------------|--------------|-------|
| G-1 PERSONNEL | SYNTHESIZER | Direct Support (DS) | Staffing, roster, utilization |
| G-2 RECON | ORCHESTRATOR | General Support (GS) | Attachable to ARCHITECT or SYNTHESIZER. Leans ARCHITECT. |
| G-3 OPERATIONS | SYNTHESIZER | Direct Support (DS) | Real-time ops, workflow coordination |
| G-4 CONTEXT | SYNTHESIZER | Direct Support (DS) | RAG, context management |
| G-5 PLANNING | ORCHESTRATOR | General Support (GS) | Attachable to ARCHITECT or SYNTHESIZER. Leans ARCHITECT. |
| G-6 SIGNAL | ARCHITECT | Direct Support (DS) | Metrics, data aggregation |

**Routing Guidance:**
- **Direct Support (DS)**: Route through assigned Deputy; escalate to ORCHESTRATOR only if Deputy unavailable
- **General Support (GS)**: Attachable to either Deputy on demand; defaults to ORCHESTRATOR when not attached
- **Cross-Domain**: G2/G5 can be attached to either Deputy based on task domain

## Party Skill Decision Guide

Party skills deploy parallel probes for specific G-Staff advisory functions. Use this guide to select the appropriate party:

| Need | Skill | Owner | Probes |
|------|-------|-------|--------|
| Codebase exploration / reconnaissance | `/search-party` | G2_RECON | 120 (12 G-2s × 10) |
| Implementation planning / strategy | `/plan-party` | G5_PLANNING | 10 |
| Pre-execution readiness validation | `/ops-party` | G3_OPERATIONS | 6 |
| Post-execution validation / testing | `/qa-party` | COORD_QUALITY | 8+ |
| Team composition / staffing analysis | `/roster-party` | G1_PERSONNEL | 6 |
| Historical context gathering | `/context-party` | G4_CONTEXT | 6 |
| System metrics / data aggregation | `/signal-party` | G6_SIGNAL | 6 |
| SOF critical mission (user-invoked) | `/sof-party` | USASOC | 7 (18-series) |

**Selection Criteria:**
- **Before work**: `/search-party` (what exists?), `/context-party` (what did we decide?)
- **During planning**: `/plan-party` (how to implement?), `/roster-party` (who to assign?)
- **Before execution**: `/ops-party` (are we ready?)
- **After execution**: `/qa-party` (did it work?)
- **Metrics needed**: `/signal-party` (what are the numbers?)
- **Critical/cross-domain**: `/sof-party` (user authorization required)

## Script Ownership

Agents must use repository scripts (not raw commands) for consistency.

**Reference:** [SCRIPT_OWNERSHIP.md](./SCRIPT_OWNERSHIP.md)

| Domain | Owner Agent | Key Scripts |
|--------|-------------|-------------|
| Container/CI | CI_LIAISON | `health-check.sh`, `start-celery.sh`, `pre-deploy-validate.sh` |
| Database | DBA | `backup-db.sh`, `seed_*.py` |
| Security | SECURITY_AUDITOR | `pii-scan.sh`, `audit-fix.sh` |
| Scheduling | SCHEDULER | `verify_schedule.py`, `generate_blocks.py` |

**Philosophy:** "It goes up the same way every single time" (ADR-011)
