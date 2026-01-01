---
name: session-end
description: Mandatory session close-out with IG audit, AAR, and optional HISTORIAN. Enforces clean session handoff.
---

***REMOVED*** Session End Skill

> **Purpose:** Clean session close-out with governance checks
> **Trigger:** `/session-end` or `/bye` or `/done`
> **Enforcement:** Controlled by `.claude/Governance/config.json`

***REMOVED******REMOVED*** Checklist (Required)

***REMOVED******REMOVED******REMOVED*** 1. Work State
- [ ] All changes committed or stashed
- [ ] No failing tests introduced
- [ ] Linters pass (ruff, eslint)

***REMOVED******REMOVED******REMOVED*** 2. Documentation
- [ ] CHANGELOG updated if features added
- [ ] TODOs resolved or documented in HUMAN_TODO.md

***REMOVED******REMOVED******REMOVED*** 3. Governance (if enabled)

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

***REMOVED******REMOVED*** Toggle

If `governance_enabled: false` in config.json:
- Checklist still shown
- IG/AAR/HISTORIAN invocation optional
- No blocking

***REMOVED******REMOVED*** Quick Exit (Emergency)

```
/session-end --force
```
Skips all checks. Logs bypass.

***REMOVED******REMOVED*** Output Format

```
================================================================================
                           SESSION END REPORT
================================================================================

***REMOVED******REMOVED*** Work Summary
- Commits: [count]
- Files Modified: [count]
- Tests Added/Modified: [count]

***REMOVED******REMOVED*** Git Status
[output of git status]

***REMOVED******REMOVED*** IG Report (DELEGATION_AUDITOR)
- Total Spawns: [count]
- Chain-of-Command Violations: [count]
- Bypasses: [list with justifications]

***REMOVED******REMOVED*** After Action Review (AAR)
***REMOVED******REMOVED******REMOVED*** What Went Well
- [item]

***REMOVED******REMOVED******REMOVED*** What Could Improve
- [item]

***REMOVED******REMOVED******REMOVED*** Patterns Discovered
- [item]

***REMOVED******REMOVED******REMOVED*** Lessons Learned
- [item]

***REMOVED******REMOVED*** HISTORIAN Entry (if significant)
[Summary for session history]

***REMOVED******REMOVED*** Recommendations for Next Session
- [item]

================================================================================
                              SESSION CLOSED
================================================================================
```

***REMOVED******REMOVED*** Execution Steps

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

***REMOVED******REMOVED*** Integration with Other Skills

- **startup/startupO**: Session-end complements startup for session lifecycle
- **code-review**: Can be invoked before session-end for final review
- **pre-pr-checklist**: Session-end incorporates similar checks

***REMOVED******REMOVED*** Aliases

- `/session-end` - Full protocol
- `/bye` - Alias for `/session-end`
- `/done` - Alias for `/session-end`
- `/session-end --force` - Emergency exit, skips checks
- `/session-end --quick` - Minimal checks, no AAR
