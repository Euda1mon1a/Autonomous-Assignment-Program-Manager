# Slash Commands Reference

This document lists all Claude Code IDE slash commands available in this project.

---

## Overview

Slash commands are defined in `.claude/commands/` and provide quick access to common workflows. Use them by typing `/<command-name>` in Claude Code.

---

## Schedule Generation

### `/generate-schedule`

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

### `/verify-schedule`

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

### `/optimize-schedule`

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

### `/check-constraints`

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

## Debugging

### `/debug`

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

### `/debug-explore`

Exploration-first debugging for unclear issues.

**Usage:**
```
/debug-explore "Schedule generation timing out"
```

---

### `/debug-tdd`

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

## Code Quality

### `/write-tests`

Generate test cases for code.

**Usage:**
```
/write-tests backend/app/services/swap_executor.py
```

---

### `/review-code`

Review code for bugs, security, and best practices.

**Usage:**
```
/review-code backend/app/scheduling/engine.py
```

---

### `/review-pr`

Review a pull request.

**Usage:**
```
/review-pr 123
```

---

### `/fix-code`

Automated code fixes (linting, type errors).

**Usage:**
```
/fix-code backend/
```

---

### `/quality-check`

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

## Operations

### `/docker-help`

Docker troubleshooting assistance.

**Usage:**
```
/docker-help "Container won't start"
```

---

### `/incident`

Production incident response.

**Usage:**
```
/incident "API 500 errors on schedule endpoint"
```

---

### `/solver`

Solver control and monitoring.

**Usage:**
```
/solver status
/solver abort
```

---

### `/swap`

Schedule swap management.

**Usage:**
```
/swap request --from "FAC-01" --to "FAC-02" --date 2025-03-15
```

---

## Export

### `/export-pdf`

Generate PDF reports.

**Usage:**
```
/export-pdf --block 10 --type schedule
```

---

### `/export-xlsx`

Generate Excel exports.

**Usage:**
```
/export-xlsx --block 10 --include-coverage
```

---

## Documentation

### `/changelog`

Generate changelog from git history.

**Usage:**
```
/changelog --since v1.2.0
```

---

### `/document-session`

Create session documentation.

**Usage:**
```
/document-session
```

---

### `/security`

Security audit for healthcare/military context.

**Usage:**
```
/security audit
```

---

## Command File Locations

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

## Creating New Commands

To add a new slash command:

1. Create `.claude/commands/<command-name>.md`
2. Include purpose, usage, and expected behavior
3. Reference relevant skills from `.claude/skills/`

**Example template:**
```markdown
# /command-name

## Purpose
What this command does.

## Usage
```
/command-name [arguments]
```

## Process
1. Step one
2. Step two
3. Step three

## Related Skills
- skill-name-1
- skill-name-2
```

---

## Related Documentation

- [Agent Skills Reference](AGENT_SKILLS.md) - Skills that commands invoke
- [AI Rules of Engagement](AI_RULES_OF_ENGAGEMENT.md) - AI behavior guidelines
