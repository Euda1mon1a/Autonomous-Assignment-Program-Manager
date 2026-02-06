# PAI Agent Identity Cards

> **Purpose:** Compact boot context for spawned agents
> **Format:** ~40-60 lines per agent
> **Usage:** Include in spawn prompt for agent self-awareness

## Why Identity Cards?

When agents are spawned via Task(), they receive ONLY the prompt. They don't automatically know:
- Who they are
- Who they report to
- Who they can spawn
- Their standing orders
- When to escalate

Identity cards solve this by providing compact, loadable context.

## Format

```markdown
# [AGENT_NAME] Identity Card

## Identity
- **Role:** [one sentence]
- **Tier:** [Deputy/Coordinator/Specialist/G-Staff/SOF]
- **Model:** [opus/sonnet/haiku]

## Chain of Command
- **Reports To:** [parent agent]
- **Can Spawn:** [list of agents]
- **Escalate To:** [escalation target]

## Standing Orders
1. [Pre-authorized action 1]
2. [Pre-authorized action 2]
...

## Escalation Triggers
- [When to escalate 1]
- [When to escalate 2]

## Key Constraints
- [Constraint 1]
- [Constraint 2]
```

## Usage

When spawning an agent:
```python
Task(
  prompt=f"""
  {read('.claude/Identities/SCHEDULER.identity.md')}

  ## MISSION
  [Task description]
  """,
  subagent_type="general-purpose"
)
```

## Maintenance

Identity cards are derived from full agent specs in `.claude/Agents/`.
When an agent spec changes, update its identity card.
