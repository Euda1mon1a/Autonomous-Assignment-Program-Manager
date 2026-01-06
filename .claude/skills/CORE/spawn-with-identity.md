# Spawn with Identity Pattern

## Purpose
Ensure all spawned agents receive their identity card for proper self-awareness.

## Pattern

### Basic Spawn
```python
# WRONG - Agent doesn't know who they are
Task(prompt="Generate a schedule for Block 10", subagent_type="general-purpose")

# RIGHT - Agent knows their identity
Task(
  prompt=f"""
  {read('.claude/Identities/SCHEDULER.identity.md')}

  ## MISSION
  Generate a schedule for Block 10.
  """,
  subagent_type="general-purpose"
)
```

### Spawn Through Coordinator
```python
# Coordinator spawns specialist with identity
Task(
  prompt=f"""
  {read('.claude/Identities/COORD_ENGINE.identity.md')}

  ## MISSION
  Spawn SCHEDULER to generate Block 10 schedule.

  When spawning SCHEDULER, include their identity card:
  .claude/Identities/SCHEDULER.identity.md
  """,
  subagent_type="general-purpose"
)
```

### Chain Enforcement
Coordinators should ONLY spawn specialists in their domain:
- COORD_ENGINE → SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
- COORD_PLATFORM → DBA, BACKEND_ENGINEER, API_DEVELOPER
- etc.

See `.claude/Governance/SPAWN_CHAINS.md` for full matrix.

## Identity Card Format

Each identity card contains:
1. **Identity** - Role, tier, model
2. **Chain of Command** - Reports to, can spawn, escalate to
3. **Standing Orders** - Pre-authorized actions
4. **Escalation Triggers** - When to escalate
5. **Constraints** - What NOT to do
6. **Charter** - One-line philosophy

## Missing Identity Card?

If an agent doesn't have an identity card:
1. Check `.claude/Identities/` for the file
2. If missing, the agent spec exists but no card was generated
3. Create one following `.claude/Identities/TEMPLATE.identity.md`

---

## Examples

### Example 1: Direct Specialist Spawn

```python
# ORCHESTRATOR spawning ARCHITECT directly
Task(
  prompt=f"""
  {read('.claude/Identities/ARCHITECT.identity.md')}

  ## MISSION
  Design a new database schema for procedure credentialing tracking.

  ## CONTEXT
  - Current models: Person, Assignment, Schedule
  - Need to track: procedure type, competency level, supervision requirements
  - Integration: Must link to existing Person model

  ## CONSTRAINTS
  - Must maintain backward compatibility
  - Migration must be reversible
  - Follow ACGME supervision ratio rules

  ## OUTPUT FORMAT
  Return:
  1. SQLAlchemy model definition
  2. Migration strategy
  3. API contract changes
  4. Rollback plan
  """,
  subagent_type="general-purpose"
)
```

### Example 2: Coordinator Spawning Multiple Specialists

```python
# COORD_PLATFORM spawning multiple specialists
Task(
  prompt=f"""
  {read('.claude/Identities/COORD_PLATFORM.identity.md')}

  ## MISSION
  Implement user impersonation 'View As' feature.

  ## DELEGATION PLAN
  1. Spawn DBA for schema design (include .claude/Identities/DBA.identity.md)
  2. Spawn BACKEND_ENGINEER for API implementation (include .claude/Identities/BACKEND_ENGINEER.identity.md)
  3. Spawn FRONTEND_ENGINEER for UI components (include .claude/Identities/FRONTEND_ENGINEER.identity.md)

  ## COORDINATION
  - DBA designs schema first
  - BACKEND_ENGINEER implements API using DBA's schema
  - FRONTEND_ENGINEER builds UI using BACKEND_ENGINEER's API

  Ensure each specialist receives their identity card in their spawn prompt.
  """,
  subagent_type="general-purpose"
)
```

### Example 3: Parallel Spawn with Identities

```python
# Spawning multiple QA agents in parallel, each with identity
tasks = [
  Task(
    description="QA_TESTER: Backend tests",
    prompt=f"""
    {read('.claude/Identities/QA_TESTER.identity.md')}

    ## MISSION
    Write pytest tests for SwapExecutor.execute_swap()

    ## TARGET
    /backend/app/services/swap_executor.py

    ## COVERAGE
    - Successful one-to-one swap
    - Swap with ACGME violation (should fail)
    - Rollback within 24-hour window
    - Rollback after 24-hour window (should fail)
    """,
    subagent_type="general-purpose"
  ),
  Task(
    description="QA_TESTER: Frontend tests",
    prompt=f"""
    {read('.claude/Identities/QA_TESTER.identity.md')}

    ## MISSION
    Write Jest tests for SwapRequestModal component

    ## TARGET
    /frontend/components/SwapRequestModal.tsx

    ## COVERAGE
    - Rendering with valid data
    - Form validation
    - Submit flow
    - Error handling
    """,
    subagent_type="general-purpose"
  )
]
```

---

## Identity Card Best Practices

### DO:
- ✅ Always include identity card at start of prompt
- ✅ Use `read()` to load identity card content
- ✅ Include mission, constraints, and output format after identity
- ✅ Verify identity card exists before spawning
- ✅ Follow chain of command when spawning through coordinators

### DON'T:
- ❌ Spawn agents without identity cards
- ❌ Copy/paste identity card content (use `read()` for freshness)
- ❌ Bypass chain of command (ORCHESTRATOR → Specialist directly)
- ❌ Modify identity cards mid-session (they're frozen at spawn time)
- ❌ Create ad-hoc identities (use TEMPLATE to formalize)

---

## Troubleshooting

### Agent doesn't follow chain of command
**Problem:** Agent spawns specialists outside its authority.
**Solution:** Ensure identity card clearly lists authorized spawn targets.

### Agent doesn't know its constraints
**Problem:** Agent violates constraints or requires escalation.
**Solution:** Verify identity card is loaded at spawn time, not mid-task.

### Identity card not found
**Problem:** `read('.claude/Identities/AGENT.identity.md')` fails.
**Solution:**
1. Check file exists: `ls .claude/Identities/`
2. Verify naming: Should be `AGENT_NAME.identity.md`
3. Create using TEMPLATE if missing

### Agent behavior doesn't match identity
**Problem:** Agent acts differently than identity card specifies.
**Solution:** Remember context isolation - identity must be in spawn prompt, not assumed from file system.

---

## Related Documentation

- `.claude/skills/context-aware-delegation/SKILL.md` - Full context isolation guide
- `.claude/Identities/TEMPLATE.identity.md` - Template for new identity cards
- `.claude/Identities/README.md` - Identity card system overview
- `.claude/Governance/SPAWN_CHAINS.md` - Chain of command matrix
- `.claude/Governance/HIERARCHY.md` - Command philosophy (Auftragstaktik)

---

## Version

- **Created:** 2026-01-06
- **Author:** Claude Code Session
- **Purpose:** Standardize identity card loading in agent spawns

---

*Identity cards ensure agents know who they are, who they report to, and what they're authorized to do. Never spawn an agent without their identity.*
