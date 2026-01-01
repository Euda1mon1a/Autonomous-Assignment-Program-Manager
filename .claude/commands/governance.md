<!--
Toggle PAI governance enforcement on/off.
Control chain-of-command routing and session-end requirements.
Usage: /governance [on|off|status|chain|session|bypass]
-->

Invoke the **governance** skill to manage PAI governance settings.

***REMOVED******REMOVED*** Required Actions

Based on the argument provided, execute ONE of the following:

***REMOVED******REMOVED******REMOVED*** No argument or `status` → Show Current Status

1. Read `.claude/Governance/config.json`
2. Display this table with actual values:

```markdown
***REMOVED******REMOVED*** Governance Status

| Setting | Status |
|---------|--------|
| governance_enabled | ✅ ON or ❌ OFF |
| chain_of_command_enforcement | ✅ ON or ❌ OFF |
| session_end_enforcement | ✅ ON or ❌ OFF |
| bypass_allowed_for_single_file | ✅ ON or ❌ OFF |
```

***REMOVED******REMOVED******REMOVED*** `on` → Enable All Governance

Update `.claude/Governance/config.json`:
```json
{
  "governance_enabled": true,
  "chain_of_command_enforcement": true,
  "session_end_enforcement": true,
  "bypass_allowed_for_single_file": true,
  "notes": "Set governance_enabled to false to disable all governance checks"
}
```

Confirm: "✅ Governance ENABLED. All enforcement active."

***REMOVED******REMOVED******REMOVED*** `off` → Disable All Governance

Update `.claude/Governance/config.json`:
```json
{
  "governance_enabled": false,
  "chain_of_command_enforcement": false,
  "session_end_enforcement": false,
  "bypass_allowed_for_single_file": true,
  "notes": "Set governance_enabled to false to disable all governance checks"
}
```

Confirm: "❌ Governance DISABLED. Free operation mode."

***REMOVED******REMOVED******REMOVED*** `chain on/off` → Toggle Chain of Command

Update only `chain_of_command_enforcement` in config. Show status table after.

***REMOVED******REMOVED******REMOVED*** `session on/off` → Toggle Session End Enforcement

Update only `session_end_enforcement` in config. Show status table after.

***REMOVED******REMOVED******REMOVED*** `bypass on/off` → Toggle Single-File Bypass

Update only `bypass_allowed_for_single_file` in config. Show status table after.

***REMOVED******REMOVED*** Quick Reference

| Command | Effect |
|---------|--------|
| `/governance` | Show status |
| `/governance on` | Enable all |
| `/governance off` | Disable all |
| `/governance chain off` | Allow direct specialist spawning |
| `/governance session off` | Skip session-end checks |
| `/governance bypass off` | Require coordinator for ALL tasks |
