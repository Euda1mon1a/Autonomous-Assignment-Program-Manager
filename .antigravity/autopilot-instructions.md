# Antigravity Autopilot Instructions

> **Purpose:** Guidelines for reliable autonomous operation
> **Last Updated:** 2025-12-22
> **Mode:** Autopilot (A) - Single agent, autonomous with guardrails

---

## Operating Principles

### 1. Read Before Write
- **ALWAYS** read a file before editing it
- Understand the existing patterns before making changes
- Check imports, dependencies, and related files

### 2. Minimal Changes
- Make the smallest change that solves the problem
- Don't refactor adjacent code unless explicitly asked
- Don't add features beyond what was requested
- Don't add comments, docstrings, or type hints to code you didn't modify

### 3. Validate Continuously
- Run tests after every significant change
- Check linting before committing
- Verify the fix actually works

### 4. Fail Fast, Recover Smart
- If something breaks, stop immediately
- Don't compound errors with more changes
- Revert if needed, then analyze

---

## Standard Workflows

### When Fixing Bugs

```
1. Reproduce the bug (run failing test or observe error)
2. Read the relevant code
3. Identify root cause (not just symptoms)
4. Make minimal fix
5. Run tests to verify fix
6. Check for regressions
7. Report what was done
```

### When Adding Features

```
1. Understand the requirement fully
2. Check existing patterns in codebase
3. Write tests first (or alongside)
4. Implement following layered architecture
5. Validate all quality gates
6. Document if needed
```

### When Exploring/Researching

```
1. Use Grep/Glob to find relevant files
2. Read files systematically
3. Build understanding before suggesting changes
4. Summarize findings
```

---

## Project-Specific Context

### Architecture
This is a FastAPI + Next.js scheduling application. Follow:
- **Route → Controller → Service → Model** pattern
- **Async all the way** for database operations
- **Pydantic schemas** for all request/response validation

### Critical Areas (Extra Caution)
- `backend/app/scheduling/` - ACGME compliance logic
- `backend/app/core/security.py` - Authentication
- `backend/app/resilience/` - Cross-industry resilience framework
- `backend/alembic/versions/` - Database migrations

### Test Requirements
- All changes need tests
- Minimum 70% coverage
- Run `pytest` before committing

---

## Communication Protocol

### Progress Updates
Report progress at these checkpoints:
1. After understanding the problem
2. After making changes
3. After validation passes/fails
4. When complete or blocked

### When Blocked
Clearly state:
- What you were trying to do
- What failed
- What you've already tried
- What you need to proceed

### Escalation Format
```
ESCALATION REQUIRED:
- Task: [what was being done]
- Blocker: [what prevented completion]
- Attempted: [what was tried]
- Recommendation: [suggested next step]
```

---

## Tool Usage

### Preferred Tools
| Task | Use This | Not This |
|------|----------|----------|
| Read files | `Read` tool | `cat` via Bash |
| Search code | `Grep` tool | `grep` via Bash |
| Find files | `Glob` tool | `find` via Bash |
| Edit files | `Edit` tool | `sed` via Bash |
| Run tests | `Bash` with `pytest` | Direct test execution |

### MCP Tools Available
When MCP server is running:
- `validate_acgme_compliance` - Check schedule compliance
- `run_contingency_analysis` - Analyze absence impact
- `detect_conflicts` - Find scheduling conflicts
- `find_swap_matches` - Match swap candidates

### Skills Auto-Activation
These skills load automatically based on context:
- ACGME questions → `acgme-compliance` skill
- Swap questions → `swap-management` skill
- Test failures → `automated-code-fixer` skill
- System issues → `production-incident-responder` skill

---

## Session Boundaries

### At Session Start
1. Check git status for uncommitted changes
2. Verify services are running (if needed)
3. Understand the current task

### During Session
1. Track progress with TodoWrite
2. Commit logical units of work (if permitted)
3. Don't leave work in broken state

### At Session End
1. Summarize what was accomplished
2. Note any remaining work
3. Ensure tests pass
4. Leave codebase in clean state

---

## Error Handling

### Common Errors and Responses

| Error | Response |
|-------|----------|
| Import error | Check `__init__.py` exports, run full test suite |
| Type error | Run `mypy`, check function signatures |
| Test failure | Read test, understand expectation, fix minimally |
| Database error | Check migrations, verify schema |
| Docker error | Check logs, verify container health |

### Recovery Priority
1. **Stop** - Don't make more changes
2. **Assess** - Understand what went wrong
3. **Revert** - If needed, undo changes
4. **Report** - Explain the situation
5. **Wait** - For guidance if unclear

---

## Performance Guidelines

### Speed vs Quality Trade-off
- Autopilot optimizes for **reliability over speed**
- Take time to understand before acting
- Double-check before destructive operations

### Resource Awareness
- Don't run expensive operations repeatedly
- Cache results when possible
- Be mindful of rate limits on external services

---

## Logging

All Autopilot actions are logged to `.antigravity/logs/autopilot.log`:

```
[2025-12-22T10:00:00Z] SESSION_START
[2025-12-22T10:00:05Z] READ backend/app/services/swap.py
[2025-12-22T10:00:10Z] EDIT backend/app/services/swap.py (lines 45-52)
[2025-12-22T10:00:15Z] BASH pytest tests/test_swap.py -v
[2025-12-22T10:00:30Z] RESULT tests passed (5/5)
[2025-12-22T10:00:35Z] SESSION_END success
```
