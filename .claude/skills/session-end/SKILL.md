---
name: session-end
description: Mandatory session close-out with IG audit, AAR, and optional HISTORIAN. Enforces clean session handoff.
---

# Session End Skill

> **Purpose:** Clean session close-out with governance checks
> **Trigger:** `/session-end` or `/bye` or `/done`
> **Enforcement:** Controlled by `.claude/Governance/config.json`

## Checklist (Required)

### 1. Work State
- [ ] All changes committed or stashed
- [ ] No failing tests introduced
- [ ] Linters pass (ruff, eslint)

### 2. Documentation
- [ ] CHANGELOG updated if features added
- [ ] TODOs resolved or documented in HUMAN_TODO.md

### 3. Governance (if enabled)

**Invoke DELEGATION_AUDITOR (IG):**
- Spawn count for session
- Chain-of-command violations
- Bypass justifications

**Invoke COORD_AAR (After Action Review):**
- What went well
- What could improve
- Patterns discovered
- Lessons learned

**Invoke HISTORIAN (if significant session):**
- Major features completed
- Architectural decisions
- Notable incidents

## Toggle

If `governance_enabled: false` in config.json:
- Checklist still shown
- IG/AAR/HISTORIAN invocation optional
- No blocking

## Quick Exit (Emergency)

```
/session-end --force
```
Skips all checks. Logs bypass.

## Output Format

```
================================================================================
                           SESSION END REPORT
================================================================================

## Work Summary
- Commits: [count]
- Files Modified: [count]
- Tests Added/Modified: [count]

## Git Status
[output of git status]

## IG Report (DELEGATION_AUDITOR)
- Total Spawns: [count]
- Chain-of-Command Violations: [count]
- Bypasses: [list with justifications]

## After Action Review (AAR)
### What Went Well
- [item]

### What Could Improve
- [item]

### Patterns Discovered
- [item]

### Lessons Learned
- [item]

## HISTORIAN Entry (if significant)
[Summary for session history]

## Recommendations for Next Session
- [item]

================================================================================
                              SESSION CLOSED
================================================================================
```

## Execution Steps

1. **Check Git State**
   ```bash
   git status
   git diff --stat
   ```

2. **Run Linters**
   ```bash
   cd backend && ruff check . --fix
   cd frontend && npm run lint:fix
   ```

3. **Verify Tests**
   ```bash
   cd backend && pytest --tb=no -q
   cd frontend && npm test -- --passWithNoTests
   ```

4. **Check Governance Config**
   ```bash
   cat .claude/Governance/config.json
   ```

5. **Generate IG Report** (if governance enabled)
   - Review session for agent spawns
   - Check for chain-of-command violations
   - Document any bypasses

6. **Conduct AAR** (if governance enabled)
   - Reflect on session outcomes
   - Identify improvements
   - Capture patterns and lessons

7. **Update HISTORIAN** (if significant session)
   - Write to `.claude/History/sessions/`
   - Include major decisions and outcomes

8. **Final Handoff**
   - Summarize state for next session
   - Note any pending work

## Integration with Other Skills

- **startup/startupO**: Session-end complements startup for session lifecycle
- **code-review**: Can be invoked before session-end for final review
- **pre-pr-checklist**: Session-end incorporates similar checks

## Aliases

- `/session-end` - Full protocol
- `/bye` - Alias for `/session-end`
- `/done` - Alias for `/session-end`
- `/session-end --force` - Emergency exit, skips checks
- `/session-end --quick` - Minimal checks, no AAR
