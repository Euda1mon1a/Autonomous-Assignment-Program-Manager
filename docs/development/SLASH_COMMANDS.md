***REMOVED*** Slash Commands Reference

This document lists all Claude Code IDE slash commands available in this project.

---

***REMOVED******REMOVED*** Overview

Slash commands are defined in `.claude/commands/` and provide quick access to common workflows. Use them by typing `/<command-name>` in Claude Code.

---

***REMOVED******REMOVED*** Schedule Generation

***REMOVED******REMOVED******REMOVED*** `/generate-schedule`

Run schedule generation for a specific block.

**Usage:**
```
/generate-schedule --block 10 --year 2025
```

**Actions:**
- Backs up database before running
- Seeds inpatient assignments
- Runs solver
- Validates output

---

***REMOVED******REMOVED******REMOVED*** `/verify-schedule`

Human verification checklist for generated schedules.

**Usage:**
```
/verify-schedule --block 10
```

**Checks:**
- FMIT assignments correct
- Call coverage complete
- Night Float assigned
- Clinic days populated
- Absences respected

---

***REMOVED******REMOVED******REMOVED*** `/optimize-schedule`

Multi-objective schedule optimization.

**Usage:**
```
/optimize-schedule --block 10 --objective coverage
```

**Objectives:**
- Coverage maximization
- Equity balancing
- Continuity preservation

---

***REMOVED******REMOVED******REMOVED*** `/check-constraints`

Validate constraints on existing schedule.

**Usage:**
```
/check-constraints --block 10
```

**Validates:**
- ACGME compliance (80-hour rule, 1-in-7)
- Supervision ratios
- FMIT blocking rules
- Post-call recovery

---

***REMOVED******REMOVED*** Debugging

***REMOVED******REMOVED******REMOVED*** `/debug`

General debugging workflow.

**Usage:**
```
/debug "Residents getting double-booked on Night Float"
```

**Process:**
1. Explore - Understand the issue
2. Plan - Form hypothesis
3. Fix - Implement solution
4. Verify - Test the fix

---

***REMOVED******REMOVED******REMOVED*** `/debug-explore`

Exploration-first debugging for unclear issues.

**Usage:**
```
/debug-explore "Schedule generation timing out"
```

---

***REMOVED******REMOVED******REMOVED*** `/debug-tdd`

Test-driven debugging workflow.

**Usage:**
```
/debug-tdd "ACGME validation false positive"
```

**Process:**
1. Write failing test
2. Confirm failure
3. Fix until green

---

***REMOVED******REMOVED*** Code Quality

***REMOVED******REMOVED******REMOVED*** `/write-tests`

Generate test cases for code.

**Usage:**
```
/write-tests backend/app/services/swap_executor.py
```

---

***REMOVED******REMOVED******REMOVED*** `/review-code`

Review code for bugs, security, and best practices.

**Usage:**
```
/review-code backend/app/scheduling/engine.py
```

---

***REMOVED******REMOVED******REMOVED*** `/review-pr`

Review a pull request.

**Usage:**
```
/review-pr 123
```

---

***REMOVED******REMOVED******REMOVED*** `/fix-code`

Automated code fixes (linting, type errors).

**Usage:**
```
/fix-code backend/
```

---

***REMOVED******REMOVED******REMOVED*** `/quality-check`

Run full quality validation.

**Usage:**
```
/quality-check
```

**Runs:**
- Ruff linting
- Type checking
- Test suite
- Security audit

---

***REMOVED******REMOVED*** Operations

***REMOVED******REMOVED******REMOVED*** `/docker-help`

Docker troubleshooting assistance.

**Usage:**
```
/docker-help "Container won't start"
```

---

***REMOVED******REMOVED******REMOVED*** `/incident`

Production incident response.

**Usage:**
```
/incident "API 500 errors on schedule endpoint"
```

---

***REMOVED******REMOVED******REMOVED*** `/solver`

Solver control and monitoring.

**Usage:**
```
/solver status
/solver abort
```

---

***REMOVED******REMOVED******REMOVED*** `/swap`

Schedule swap management.

**Usage:**
```
/swap request --from "FAC-01" --to "FAC-02" --date 2025-03-15
```

---

***REMOVED******REMOVED*** Export

***REMOVED******REMOVED******REMOVED*** `/export-pdf`

Generate PDF reports.

**Usage:**
```
/export-pdf --block 10 --type schedule
```

---

***REMOVED******REMOVED******REMOVED*** `/export-xlsx`

Generate Excel exports.

**Usage:**
```
/export-xlsx --block 10 --include-coverage
```

---

***REMOVED******REMOVED*** Documentation

***REMOVED******REMOVED******REMOVED*** `/changelog`

Generate changelog from git history.

**Usage:**
```
/changelog --since v1.2.0
```

---

***REMOVED******REMOVED******REMOVED*** `/document-session`

Create session documentation.

**Usage:**
```
/document-session
```

---

***REMOVED******REMOVED******REMOVED*** `/security`

Security audit for healthcare/military context.

**Usage:**
```
/security audit
```

---

***REMOVED******REMOVED*** Command File Locations

All command definitions are in `.claude/commands/`:

```
.claude/commands/
├── changelog.md
├── check-constraints.md
├── debug.md
├── docker-help.md
├── document-session.md
├── export-pdf.md
├── export-xlsx.md
├── fix-code.md
├── generate-schedule.md
├── incident.md
├── optimize-schedule.md
├── quality-check.md
├── review-code.md
├── review-pr.md (not shown - use /review-pr)
├── security.md
├── solver.md
├── swap.md
├── verify-schedule.md
└── write-tests.md
```

---

***REMOVED******REMOVED*** Creating New Commands

To add a new slash command:

1. Create `.claude/commands/<command-name>.md`
2. Include purpose, usage, and expected behavior
3. Reference relevant skills from `.claude/skills/`

**Example template:**
```markdown
***REMOVED*** /command-name

***REMOVED******REMOVED*** Purpose
What this command does.

***REMOVED******REMOVED*** Usage
```
/command-name [arguments]
```

***REMOVED******REMOVED*** Process
1. Step one
2. Step two
3. Step three

***REMOVED******REMOVED*** Related Skills
- skill-name-1
- skill-name-2
```

---

***REMOVED******REMOVED*** Related Documentation

- [Agent Skills Reference](AGENT_SKILLS.md) - Skills that commands invoke
- [AI Rules of Engagement](AI_RULES_OF_ENGAGEMENT.md) - AI behavior guidelines
