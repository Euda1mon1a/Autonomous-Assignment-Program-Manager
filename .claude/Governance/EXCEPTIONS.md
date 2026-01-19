# PAI Exception Catalog

> **Purpose:** Consolidated record of authorized governance overrides
> **Version:** 1.0
> **Last Updated:** 2026-01-19

---

## MCP Discovery

### RAG Queries
```
rag_search("exception catalog governance override")
rag_search("tier 2 exception authorization")
rag_search("governance override documented justification")
rag_search("exception request process approval")
```

### Related MCP Tools
| Tool | Purpose |
|------|---------|
| `rag_search` | Find existing exceptions by type or domain |
| `rag_ingest` | Index new exceptions after documentation |
| `check_circuit_breakers_tool` | Verify system state before exception use |

### Exception Validation
Before invoking an exception, agents SHOULD:
1. `rag_search("exception [EXC-NUMBER]")` - Verify exception is active
2. Check exception scope matches current context
3. Document exception use in session transcript

---

## Overview

Exceptions are documented deviations from standard PAI governance. Every exception MUST be:
1. **Authorized** by an agent with override authority
2. **Documented** in this catalog
3. **Justified** with clear rationale
4. **Bounded** with expiration or review date

**Philosophy:** Exceptions prove the rule, not break it. If an exception becomes routine, update the rule.

---

## Exception Tiers

| Tier | Authority Required | Examples |
|------|-------------------|----------|
| **Tier 1** | Human only | Security bypasses, ACGME shortcuts, OPSEC violations |
| **Tier 2** | Deputy (with documentation) | Architecture deviations, new dependencies, workflow changes |
| **Tier 3** | Coordinator (with justification) | Tool preferences, pattern variations, minor deviations |

**Tier 1 exceptions can NEVER be approved by any PAI agent.**

---

## Active Exceptions

### Exception Template

```markdown
### EXC-[NUMBER]: [Short Title]

**Status:** Active | Expired | Revoked
**Tier:** 1 | 2 | 3
**Authorized By:** [Agent or Human]
**Date:** YYYY-MM-DD
**Expires:** YYYY-MM-DD | On condition | Never (permanent)

**Rule Being Overridden:**
[Standard rule that this exception bypasses]

**Justification:**
[Why this exception is necessary]

**Scope:**
[Where/when this exception applies]

**Conditions:**
- [Specific conditions under which exception is valid]

**Review Trigger:**
[What would cause this exception to be reviewed]
```

---

### EXC-001: L3 Minimal Context Pattern

**Status:** Active
**Tier:** 3
**Authorized By:** ARCHITECT
**Date:** 2026-01-10
**Expires:** Never (permanent standing order)

**Rule Being Overridden:**
Standard MCP spawning includes full identity card and strategic RAG context.

**Justification:**
L3 pattern reduces context overhead by ~90% while maintaining MCP tool effectiveness. Agents discover tools from mission intent rather than pre-loaded context.

**Scope:**
All agent spawning when:
- Mission is clear (1-2 sentence objective)
- Key parameters are provided (dates, IDs, constraints)
- MCP tools are available for the task domain

**Conditions:**
- Mission must be unambiguous
- Key parameters must be explicit
- Must NOT be used for novel/exploratory tasks

**Review Trigger:**
Agent confusion or mission failure due to insufficient context.

---

### EXC-002: Direct Tool Execution (1% Rule)

**Status:** Active
**Tier:** 2
**Authorized By:** ORCHESTRATOR (implicit via 99/1 Rule)
**Date:** 2026-01-01
**Expires:** Never (permanent)

**Rule Being Overridden:**
ORCHESTRATOR delegates all work to Deputies.

**Justification:**
Some trivial tasks (single file read, status check) don't warrant full delegation chain. The 1% nuclear option exists for efficiency on truly simple operations.

**Scope:**
ORCHESTRATOR only, for operations where:
- No subordinate agent exists for the domain
- Delegation overhead exceeds task complexity
- Immediate human response is required

**Conditions:**
- Must be genuinely trivial (< 2 tool calls)
- Must NOT involve code changes
- Must NOT involve architectural decisions
- Must NOT involve schedule modifications

**Review Trigger:**
If ORCHESTRATOR's 1% usage exceeds 5% of actions.

---

### EXC-003: Parallel Party Deployment Without Coordinator

**Status:** Active
**Tier:** 3
**Authorized By:** SYNTHESIZER
**Date:** 2026-01-15
**Expires:** Never (permanent)

**Rule Being Overridden:**
Agents should route through their chain of command.

**Justification:**
Party skills (search-party, qa-party, etc.) are designed for rapid parallel deployment. Requiring coordinator approval would negate the speed benefit.

**Scope:**
Any agent spawning party probes for reconnaissance or validation.

**Conditions:**
- Must use established party skill
- Must NOT modify code during party execution
- Must synthesize results before taking action

**Review Trigger:**
Party results leading to incorrect actions.

---

## Historical Exceptions (Expired/Revoked)

### EXC-H001: Emergency Direct DB Access

**Status:** Revoked
**Tier:** 2
**Originally Authorized By:** ARCHITECT
**Date:** 2026-01-02
**Revoked:** 2026-01-05

**Reason for Revocation:**
Backup procedures now fully automated. No longer necessary to bypass ORM for emergency access.

---

## Exception Request Process

### For Tier 3 Exceptions
1. Coordinator documents justification
2. Coordinator applies exception with self-audit
3. Exception logged in this catalog
4. Deputy reviews in next session

### For Tier 2 Exceptions
1. Coordinator requests via escalation
2. Deputy evaluates and documents
3. Exception logged in this catalog
4. Human notified in session summary

### For Tier 1 Exceptions
1. Agent identifies need for Tier 1 override
2. Agent STOPS and escalates to Human
3. Human makes decision
4. If approved, Human documents in this catalog

---

## Exception Metrics

| Period | Tier 1 | Tier 2 | Tier 3 | Total |
|--------|--------|--------|--------|-------|
| 2026-01 | 0 | 2 | 5 | 7 |

**Health Indicator:**
- Tier 1 should always be 0 (agent-initiated)
- Tier 2 should be < 5 per month
- Tier 3 should be < 20 per month
- If exceptions grow, review underlying rules

---

## Related Documents

- [HIERARCHY.md](./HIERARCHY.md) - Command structure and authority
- [STANDING_ORDERS_INDEX.md](./STANDING_ORDERS_INDEX.md) - Pre-authorized actions
- [CONSTITUTION.md](./CONSTITUTION.md) - Core governance principles

---

*Maintained by DELEGATION_AUDITOR and ORCHESTRATOR*
