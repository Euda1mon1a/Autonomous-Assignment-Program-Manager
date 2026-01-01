---
name: governance
description: Toggle PAI governance enforcement on/off. Control chain-of-command routing and session-end requirements.
---

# Governance Control Skill

> **Purpose:** Toggle governance enforcement without editing config files
> **Trigger:** `/governance [on|off|status]`
> **Config:** `.claude/Governance/config.json`

---

## Commands

### Check Status

```
/governance
/governance status
```

Shows current enforcement state for all settings.

### Toggle All Governance

```
/governance on    # Enable all enforcement
/governance off   # Disable all enforcement
```

### Toggle Specific Settings

```
/governance chain on      # Enable chain-of-command routing
/governance chain off     # Disable chain-of-command routing

/governance session on    # Enable session-end enforcement
/governance session off   # Disable session-end enforcement

/governance bypass on     # Allow single-file bypass
/governance bypass off    # Require coordinator for all tasks
```

---

## Implementation

When this skill is invoked, Claude should:

### For Status Check

```bash
cat .claude/Governance/config.json
```

Then display:
```
## Governance Status

| Setting | Status |
|---------|--------|
| governance_enabled | ✅ ON / ❌ OFF |
| chain_of_command_enforcement | ✅ ON / ❌ OFF |
| session_end_enforcement | ✅ ON / ❌ OFF |
| bypass_allowed_for_single_file | ✅ ON / ❌ OFF |
```

### For Toggle Commands

Update `.claude/Governance/config.json` with new values:

**`/governance off`** sets:
```json
{
  "governance_enabled": false,
  ...
}
```

**`/governance on`** sets:
```json
{
  "governance_enabled": true,
  ...
}
```

**`/governance chain off`** sets:
```json
{
  "chain_of_command_enforcement": false,
  ...
}
```

---

## Quick Reference

| Command | Effect |
|---------|--------|
| `/governance` | Show status |
| `/governance on` | Enable all |
| `/governance off` | Disable all |
| `/governance chain off` | Allow direct specialist spawning |
| `/governance session off` | Skip session-end checks |
| `/governance bypass off` | Require coordinator for ALL tasks |

---

## When to Disable

**Disable governance for:**
- Emergency P0 fixes (speed over process)
- Solo exploration sessions
- Quick prototyping

**Keep enabled for:**
- Production changes
- Multi-agent coordination
- Anything touching compliance/security

---

## Related

- `.claude/Governance/config.json` - Raw config file
- `.claude/Governance/HIERARCHY.md` - Chain of command
- `/session-end` - Session close-out (respects governance toggle)
- `/startupO` - Shows governance status at session start
