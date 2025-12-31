# Explorer vs G2_RECON: Understanding the Distinction

> **Author:** HISTORIAN
> **Date:** 2025-12-30
> **Context:** Session 025 - Educational documentation for future Claude sessions

---

## The Question

During multi-agent orchestration, a common point of confusion arises:

*"Should I use Explore or G2_RECON for reconnaissance tasks?"*

This question reveals a category error. **Explore and G2_RECON exist at different conceptual layers.** They are not alternatives to choose between---they are different things entirely, and one typically *uses* the other.

This document clarifies the distinction to prevent future confusion.

---

## Two Different Layers

### Layer 1: Technical Infrastructure (subagent_type)

**What is `Explore`?**

`Explore` is a **value passed to the Task tool's `subagent_type` parameter**. It is technical infrastructure---a way to configure how a spawned agent operates.

```python
Task(
  prompt="Find all ACGME validation code",
  subagent_type="Explore"  # <-- This is infrastructure configuration
)
```

**Key Characteristics of `Explore`:**

| Aspect | Detail |
|--------|--------|
| **What it is** | A Task tool parameter value |
| **Purpose** | Fast codebase exploration |
| **Context behavior** | CAN see prior conversation (unlike `general-purpose`) |
| **Specialization** | Finding files, searching code, answering codebase questions |
| **Has a charter?** | No - it's a capability mode, not a persona |
| **Has responsibilities?** | No - it does whatever the prompt asks |
| **Model tier** | Optimized for speed (typically haiku-class) |

The other common `subagent_type` values are:
- `general-purpose` - Isolated context, full capability
- `Plan` - Can see context, specialized for planning
- `claude-code-guide` - Documentation search specialist

**Think of `subagent_type` as selecting an engine configuration:**
- `Explore` = Fast engine with context visibility
- `general-purpose` = Full engine, isolated context

### Layer 2: Organizational Role (PAI Agent)

**What is `G2_RECON`?**

`G2_RECON` is a **PAI (Parallel Agent Infrastructure) agent**---an organizational role with a charter, responsibilities, constraints, and defined relationships to other agents.

The name comes from Army staff doctrine:
- **G-2** = Intelligence section in military staff structure
- **RECON** = Reconnaissance mission

**Key Characteristics of G2_RECON:**

| Aspect | Detail |
|--------|--------|
| **What it is** | An agent persona/role |
| **Purpose** | Gather intelligence BEFORE action |
| **Defined in** | `.claude/Agents/G2_RECON.md` (762 lines) |
| **Has a charter?** | Yes - "Intelligence precedes action" |
| **Has responsibilities?** | Yes - 5 workflows, escalation rules, output formats |
| **Reports to** | ORCHESTRATOR |
| **Authority level** | Propose-Only (Researcher archetype) |
| **Philosophy** | "Know the terrain before the battle" |

**G2_RECON's defined workflows:**
1. Pre-Task Reconnaissance
2. Impact Analysis
3. Technical Debt Reconnaissance
4. Cross-Session Pattern Analysis

**G2_RECON's escalation chain:**
- Security vulnerabilities --> COORD_QUALITY
- Exposed secrets --> ORCHESTRATOR (IMMEDIATE)
- Architectural concerns --> ARCHITECT
- Production stability risk --> COORD_PLATFORM

---

## The Relationship

Here is the critical insight:

> **G2_RECON *uses* `Explore` as its execution mechanism.**

When ORCHESTRATOR needs reconnaissance, it spawns G2_RECON as a persona. That spawn happens via the Task tool, which requires a `subagent_type`. G2_RECON typically uses `Explore` because:
- Reconnaissance needs fast codebase traversal
- Reconnaissance benefits from seeing conversation context
- G2_RECON doesn't need full `general-purpose` capabilities for read-only scouting

**The invocation looks like this:**

```python
Task(
  prompt="""
  ## Agent: G2_RECON

  You are the G2_RECON agent responsible for intelligence and reconnaissance.

  ## Task
  Execute Pre-Task Reconnaissance for the swap executor refactor.

  ## Scope
  /backend/app/services/swap_executor.py

  Return a brief intelligence briefing.
  """,
  subagent_type="Explore"  # The execution mechanism
)
```

Notice: The **persona** (G2_RECON) is defined in the **prompt**. The **subagent_type** (Explore) is the **infrastructure** that runs the agent.

---

## Analogy: Role vs Tool

**Military Analogy (fitting for G-Staff):**

| Concept | Military Parallel |
|---------|-------------------|
| `Explore` | A helicopter |
| `general-purpose` | A truck |
| `G2_RECON` | A scout |

A scout (G2_RECON) might use a helicopter (Explore) for aerial reconnaissance. The helicopter is not the scout---it's how the scout moves. The scout could also use a truck (general-purpose) for different terrain.

**Software Analogy:**

| Concept | Software Parallel |
|---------|-------------------|
| `subagent_type` | Programming language runtime |
| PAI Agent | Application built on that runtime |
| `Explore` | Fast, context-aware runtime (like Node.js) |
| `general-purpose` | Full-featured, isolated runtime (like JVM) |
| `G2_RECON` | A specific application (like a security scanner) |

You don't ask "Should I use Python or a web scraper?" You use Python (runtime) *to build* the web scraper (application).

---

## Quick Reference

| Aspect | Explore | G2_RECON |
|--------|---------|----------|
| **Layer** | Infrastructure | Role |
| **Type** | `subagent_type` parameter value | PAI agent persona |
| **Defined where** | Claude's Task tool behavior | `.claude/Agents/G2_RECON.md` |
| **Has charter?** | No | Yes |
| **Has workflows?** | No | Yes (4 defined) |
| **Has escalation rules?** | No | Yes |
| **Reports to anyone?** | No | ORCHESTRATOR |
| **Can see prior context?** | Yes | Depends on `subagent_type` used |
| **Optimized for** | Speed, codebase navigation | Intelligence gathering, risk assessment |
| **Relationship** | Tool/capability | Role that uses tools |

---

## When to Use Each

### Use `Explore` subagent_type when:

1. **Quick codebase questions** - "Where is X defined?"
2. **File discovery** - "Find all files that import Y"
3. **Simple searches** - No complex reasoning or output format needed
4. **Context-aware tasks** - Need to reference prior conversation

```python
# Example: Simple exploration
Task(
  prompt="Find all files that contain ACGME validation logic",
  subagent_type="Explore"
)
```

### Use G2_RECON (as a persona) when:

1. **Structured reconnaissance** - Need Pre-Task Intelligence Briefing format
2. **Risk assessment** - Want severity ratings and mitigation recommendations
3. **Impact analysis** - Need dependency graphs and affected test identification
4. **Cross-session patterns** - Looking for recurring issues and technical debt
5. **Accountability** - Need clear escalation paths and audit trail

```python
# Example: Full reconnaissance with persona
Task(
  prompt="""
  ## Agent: G2_RECON

  Execute the Impact Analysis workflow for proposed changes to:
  /backend/app/services/swap_executor.py

  Questions to answer:
  1. What modules depend on this file?
  2. What tests cover this functionality?
  3. What is the rollback risk?

  Output: Full Impact Analysis Report format per your charter.
  """,
  subagent_type="Explore"  # or "general-purpose" if deeper analysis needed
)
```

### The Decision Tree

```
Need codebase information?
    |
    |-- Simple search/question --> Use Explore directly
    |
    |-- Need structured analysis with:
        |-- Risk ratings
        |-- Formatted briefings
        |-- Escalation awareness
        |-- Defined workflows
        |
        +--> Spawn G2_RECON persona (usually with Explore subagent_type)
```

---

## Common Mistakes

### Mistake 1: Treating them as alternatives

```
WRONG: "Should I use Explore or G2_RECON?"
RIGHT: "Should I do a quick Explore search, or spawn G2_RECON for structured recon?"
```

### Mistake 2: Using G2_RECON without specifying subagent_type

```python
# This doesn't work - G2_RECON is not a subagent_type
Task(
  prompt="Do reconnaissance",
  subagent_type="G2_RECON"  # ERROR: Invalid subagent_type
)
```

### Mistake 3: Expecting Explore to follow G2_RECON protocols

```python
# Explore won't produce G2 output format unless told
Task(
  prompt="Scout the swap executor",
  subagent_type="Explore"
)
# Result: Ad-hoc output, no risk matrix, no escalation awareness
```

### Mistake 4: Over-engineering simple searches

```python
# Overkill for "where is X?"
Task(
  prompt="""
  ## Agent: G2_RECON
  Execute Pre-Task Reconnaissance to find the ACGME validator file.
  Produce full Intelligence Briefing with risk assessment...
  """,
  subagent_type="Explore"
)

# Just do this instead:
Task(
  prompt="Find the ACGME validator implementation file",
  subagent_type="Explore"
)
```

---

## For ORCHESTRATOR: Choosing the Right Approach

| Scenario | Approach | Rationale |
|----------|----------|-----------|
| "Where is file X?" | `Explore` directly | Simple search, no persona needed |
| "What does function Y do?" | `Explore` directly | Quick lookup |
| "Is this refactor risky?" | G2_RECON with `Explore` | Need risk assessment format |
| "What will break if we change Z?" | G2_RECON Impact Analysis | Structured dependency analysis |
| "Audit technical debt in module" | G2_RECON Tech Debt Recon | Defined workflow exists |
| "Find patterns in recent failures" | G2_RECON Cross-Session | Need historical pattern analysis |
| "Security vulnerability scan" | G2_RECON --> escalates to COORD_QUALITY | Defined escalation path |

---

## Summary

**Explore is a vehicle. G2_RECON is a soldier.**

The soldier uses the vehicle to accomplish missions. You don't ask "Should I use a Humvee or a soldier?" You deploy soldiers who may use Humvees.

Similarly:
- `Explore` is infrastructure (how the agent runs)
- G2_RECON is a persona (what the agent does)

When in doubt:
- Simple search? --> Just use `Explore`
- Structured intelligence? --> Spawn G2_RECON (using `Explore` or `general-purpose` as the mechanism)

---

## References

- **G2_RECON Spec:** `.claude/Agents/G2_RECON.md`
- **Context-Aware Delegation:** `.claude/skills/context-aware-delegation/SKILL.md`
- **ORCHESTRATOR Agent:** `.claude/Agents/ORCHESTRATOR.md`
- **StartupO Skill:** `.claude/skills/startupO/SKILL.md` (subagent_type table)

---

*Documented by HISTORIAN Agent - Session 025*

*"Clear distinctions prevent confused actions. Know your layers."*
