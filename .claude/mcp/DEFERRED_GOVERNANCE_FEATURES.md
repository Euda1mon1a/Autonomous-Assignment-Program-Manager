# Deferred Governance Features

> **Purpose:** Document valuable features from PR #724 not cherry-picked to PR #725
> **Created:** 2026-01-16
> **Source:** `claude/subagents-mcp-orchestrators-hr437` branch
> **Status:** Deferred, not abandoned

---

## Context

PR #724 explored a modular `pai_bridge/` architecture with sophisticated governance features. PR #725 took a simpler monolithic approach in `spawn_agent_tool`. This document preserves the deferred features for future implementation, especially as the system scales.

---

## Why This Matters at Scale

### Current State (Single MTF)
- One program coordinator
- One set of agents
- Direct oversight possible
- Mistakes are catchable

### Future State (Multi-MTF Deployment)
- Every Military Treatment Facility running this system
- Multiple residency programs per MTF
- LLMs making autonomous scheduling decisions
- ACGME compliance across dozens of programs
- **No human in the loop for routine operations**

At scale, governance isn't optional—it's the difference between:
- A helpful tool vs. a liability
- ACGME compliance vs. program probation
- Resident wellbeing vs. burnout epidemics

---

## Deferred Feature 1: Tool Preconditions

### What It Is

A safety gate system that prevents dangerous tool sequences:

```python
TOOL_PRECONDITIONS: dict[str, list[str]] = {
    "execute_swap": [
        "backup_verified",      # Database backup must exist
        "validate_called",      # validate_schedule must be called first
    ],
    "generate_schedule": [
        "backup_verified",      # Database backup must exist
    ],
    "execute_sacrifice_hierarchy": [
        "defense_level_checked",  # get_defense_level must be called first
        "requires_approval",      # Human approval required
    ],
}
```

### Why It Matters

**Without preconditions:**
```
LLM: "I'll just call execute_swap to fix this conflict..."
→ Swap executes without validation
→ Introduces 80-hour violation
→ Not caught until weekly audit
→ ACGME finding
```

**With preconditions:**
```
LLM: "I'll call execute_swap..."
→ Precondition check: "validate_schedule not called"
→ Tool blocked with clear error
→ LLM forced to validate first
→ Violation caught before execution
```

### Scale Implications

| Scenario | Without Preconditions | With Preconditions |
|----------|----------------------|-------------------|
| Single swap | Manual review catches issues | Automated safety |
| Bulk swaps (10+) | Human can't review all | Each swap validated |
| Multi-MTF (50 programs) | Inconsistent enforcement | Uniform safety gates |
| LLM-driven operations | No guardrails | Enforced sequences |

### Implementation Complexity

**Low** - The validation logic already exists in `spawn_agent_tool`. Adding precondition checks requires:
1. Define `TOOL_PRECONDITIONS` dict
2. Track `tools_called` in session context
3. Check preconditions before tool execution
4. Return clear error if unmet

### Recommendation

**Implement when:** LLM-driven scheduling becomes production (not just Claude Code assistance)

---

## Deferred Feature 2: Agent-Tool Access Matrix

### What It Is

Explicit mapping of which agents can call which MCP tools:

```python
AGENT_TOOL_MATRIX: dict[str, list[str]] = {
    "SCHEDULER": [
        "validate_schedule",
        "generate_schedule",
        "detect_conflicts",
        "analyze_swap_candidates",
        "execute_swap",
    ],
    "COMPLIANCE_AUDITOR": [
        "validate_schedule",
        "detect_conflicts",
        "rag_search",
    ],
    "ORCHESTRATOR": [],  # Deputies delegate, don't use tools directly
    # ... 30+ agents mapped
}
```

### Why It Matters

**Current state:** Any agent can call any MCP tool. We trust the identity card's "tools_access" list.

**Problem at scale:** An agent spawned by a compromised or confused parent could:
- Call tools outside its domain
- Escalate privileges through tool access
- Bypass governance through direct tool calls

### Scale Implications

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent calls wrong tool | Confusion, audit trail pollution | Whitelist enforcement |
| Agent escalates via tools | Security violation | Matrix-based access control |
| Audit trail integrity | Can't trust what agents did | Tool access logging |

### Implementation Complexity

**Medium** - Requires intercepting tool calls in the MCP server or Claude Code layer.

### Recommendation

**Implement when:** Agents are spawned by external systems (not just Claude Code ORCHESTRATOR)

---

## Deferred Feature 3: Structured Audit Logging

### What It Is

Typed audit records for all governance decisions:

```python
@dataclass
class ToolAccessRecord:
    timestamp: datetime
    agent_name: str
    agent_tier: str
    tool_name: str
    allowed: bool
    reason: str
    invocation_id: UUID

@dataclass
class SpawnRecord:
    timestamp: datetime
    parent_agent: str
    child_agent: str
    allowed: bool
    reason: str
    invocation_id: UUID
```

### Why It Matters

**Current state:** Audit trail is JSON blob with whatever fields we remembered to include.

**At scale:** IG auditors need to answer:
- "Who authorized this schedule change?"
- "What tool sequence led to this violation?"
- "Which agents were involved in this decision chain?"

Structured records enable:
- Automated compliance reports
- Pattern detection (agent behaving outside norms)
- Forensic reconstruction of incidents

### Scale Implications

| Query | Current | With Structured Logs |
|-------|---------|---------------------|
| "Show all denied tool accesses" | Grep JSON files | `SELECT * WHERE allowed=false` |
| "Trace decision chain for swap X" | Manual reconstruction | Join on invocation_id |
| "Agents with most escalations" | Not possible | Aggregate query |

### Implementation Complexity

**Low** - Just discipline in what we log. The `spawn_agent_tool` already writes JSON audit entries.

### Recommendation

**Implement now** - Low cost, high value. Just standardize the audit record schema.

---

## Deferred Feature 4: Pydantic Models for Type Safety

### What It Is

Strongly-typed models for agent invocation:

```python
class AgentIdentity(BaseModel):
    name: str
    role: str
    tier: Literal["Deputy", "Coordinator", "Specialist", "G-Staff"]
    model: Literal["opus", "sonnet", "haiku"]
    reports_to: str
    can_spawn: list[str]
    # ... full schema

class AgentInvocationRequest(BaseModel):
    mission: str
    context: dict[str, Any] | None = None
    require_approval: bool = False
    parent_agent: str | None = None

class AgentResult(BaseModel):
    status: Literal["success", "error", "escalated", "blocked"]
    result: Any
    tools_used: list[str]
    escalation_events: list[EscalationEvent]
    audit_trail_path: str
```

### Why It Matters

**Current state:** Dicts everywhere. Easy to misspell keys, forget fields, pass wrong types.

**At scale:** Integration errors multiply. A typo in one MTF's integration becomes:
- Silent failures
- Missing audit data
- Inconsistent behavior across sites

### Scale Implications

Type safety catches errors at:
- Development time (IDE warnings)
- Test time (Pydantic validation)
- Runtime (before damage occurs)

vs. catching errors at:
- Audit time (too late)
- Incident time (really too late)

### Implementation Complexity

**Medium** - Requires defining models and updating callers. Good candidate for incremental adoption.

### Recommendation

**Implement when:** External systems integrate with spawn_agent_tool API

---

## Deferred Feature 5: Escalation Detection

### What It Is

Pattern matching to detect when agents should escalate:

```python
ESCALATION_PATTERNS = [
    "violation",
    "timeout",
    "failure",
    "conflict",
    "exhaustion",
    "blocked",
]

def _check_escalation_triggers(self, result: str) -> list[str]:
    """Detect if result indicates need for escalation."""
    triggered = []
    result_lower = result.lower()
    for pattern in ESCALATION_PATTERNS:
        if pattern in result_lower:
            triggered.append(pattern)
    return triggered
```

### Why It Matters

**Current state:** Agents decide when to escalate based on identity card triggers. But they might not recognize they should.

**At scale:** Undetected escalation needs cause:
- Agents spinning on unsolvable problems
- Context exhaustion without handoff
- Silent failures

### Scale Implications

| Scenario | Without Detection | With Detection |
|----------|------------------|----------------|
| Solver timeout | Agent retries indefinitely | Escalates to COORD_ENGINE |
| ACGME violation found | Might continue anyway | Forces escalation |
| Constraint conflict | Thrashes | Surfaces to human |

### Implementation Complexity

**Low** - Just regex/string matching on agent results before returning.

### Recommendation

**Implement when:** Agents run autonomously without human monitoring

---

## Implementation Priority Matrix

| Feature | Complexity | Value at Scale | Implement When |
|---------|------------|----------------|----------------|
| **Structured Audit Logging** | Low | Critical | Now |
| **Tool Preconditions** | Low | Critical | LLM production use |
| **Escalation Detection** | Low | High | Autonomous agents |
| **Pydantic Models** | Medium | High | External integrations |
| **Agent-Tool Matrix** | Medium | Medium | Multi-system deployment |

---

## Source Code Reference

The full implementation is preserved in the closed PR #724 branch:

```bash
# View the deferred code
git fetch origin claude/subagents-mcp-orchestrators-hr437
git show origin/claude/subagents-mcp-orchestrators-hr437:mcp-server/src/scheduler_mcp/pai_bridge/tool_validator.py
git show origin/claude/subagents-mcp-orchestrators-hr437:mcp-server/src/scheduler_mcp/pai_bridge/models.py
git show origin/claude/subagents-mcp-orchestrators-hr437:mcp-server/src/scheduler_mcp/pai_bridge/executor.py
```

---

## Decision Record

**Date:** 2026-01-16
**Decision:** Defer modular governance features, ship monolithic spawn_agent_tool
**Rationale:**
- Current use case (Claude Code assistance) doesn't require full governance
- Simpler implementation enables faster iteration
- Features preserved for future scaling

**Revisit when:**
- LLMs make autonomous scheduling decisions in production
- Multiple MTFs deploy the system
- External systems integrate with agent spawning
- Audit/compliance requirements increase

---

*"The best time to add governance is before you need it. The second best time is now."*
