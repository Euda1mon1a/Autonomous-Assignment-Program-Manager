# Approval Authority Matrix

## Toggle
Controlled by `config.json`.

## Authority Levels

| Action | Approver | Can Delegate? |
|--------|----------|---------------|
| Read any file | Autonomous | N/A |
| Edit test files | Autonomous | N/A |
| Edit code files | Coordinator | To specialist |
| Create new files | Coordinator | To specialist |
| Database migration | Human | Never |
| Git commit | Autonomous | N/A |
| Git push (feature) | Autonomous | N/A |
| Git push (main) | Human | Never |
| PR create | Autonomous | N/A |
| PR merge | Human | Never |
| Delete files | Human | Never |
| Production deploy | Human | Never |

## Escalation Path

```
Specialist → Coordinator → ORCHESTRATOR → Human
```

## Override Protocol

Any rule can be overridden with explicit human approval documented in conversation.

## Action Categories

### Autonomous Actions (No Approval Needed)
- Reading files and documentation
- Running tests and linters
- Creating commits on feature branches
- Pushing to feature branches
- Creating pull requests
- Editing test files

### Coordinator-Approved Actions
- Editing production code files
- Creating new source files
- Modifying configuration files
- Architectural changes within domain

### ORCHESTRATOR-Approved Actions
- Cross-coordinator changes
- Multi-domain refactoring
- Emergency bypasses
- Governance exceptions

### Human-Only Actions
- Database migrations (schema changes)
- Pushing to main/master
- Merging pull requests
- Deleting files
- Production deployments
- Modifying `.env` files
- Force pushes

## Documentation Requirements

### For Bypasses
When bypassing chain of command:
```
BYPASS DOCUMENTATION:
- Action: [what was done]
- Normal Route: [which coordinator would handle]
- Bypass Reason: [why direct access was needed]
- Scope: [single file / multiple files]
- Post-hoc Notification: [coordinator informed Y/N]
```

### For Escalations
When escalating to human:
```
ESCALATION REQUEST:
- Action Requested: [what needs human approval]
- Risk Level: [low/medium/high/critical]
- Reversibility: [can be undone Y/N]
- Urgency: [blocking / non-blocking]
- Context: [why this action is needed]
```
