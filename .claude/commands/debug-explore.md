<!--
Exploration-first debugging for complex issues where root cause is unclear.
Usage: /project:debug-explore [symptom-description]
Arguments: $ARGUMENTS
-->

# Debug Exploration: $ARGUMENTS

**CRITICAL: DO NOT WRITE CODE OR FIX ANYTHING DURING THIS EXPLORATION.**

This command is for understanding problems, not solving them.

## Phase 1: Gather Evidence

### Check Logs
```bash
cd /home/user/Autonomous-Assignment-Program-Manager

# Recent backend logs (if using Docker)
docker-compose logs backend --tail=200 2>/dev/null || echo "Docker not running"

# Check for error patterns
grep -ri "error\|exception\|failed\|violation" backend/logs/ 2>/dev/null | tail -50

# Celery task logs
grep -i "task\|celery" backend/logs/*.log 2>/dev/null | tail -30
```

### Check System State
```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Database health
python -c "from app.db.session import engine; print('DB OK')" 2>&1

# Redis health
redis-cli ping 2>/dev/null || echo "Redis not available"

# Recent test failures
pytest --collect-only 2>&1 | grep -i "error" | head -20
```

### Examine Recent Changes
```bash
cd /home/user/Autonomous-Assignment-Program-Manager

# Recent commits to relevant files
git log --oneline -20 -- backend/app/scheduling/
git log --oneline -20 -- backend/app/services/

# Files changed recently
git diff HEAD~5 --name-only | grep -E "\.py$"
```

## Phase 2: Form Hypotheses

Based on the evidence, list 5-7 possible causes:

| # | Hypothesis | Evidence For | Evidence Against | Test Method |
|---|------------|--------------|------------------|-------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Think hard about which hypothesis is most likely.**

Rank hypotheses by:
- Likelihood (based on evidence)
- Impact (severity if true)
- Testability (ease of validation)

## Phase 3: Targeted Investigation

For the top 2-3 hypotheses, investigate deeper:

### Hypothesis 1: [Name]

Key files to examine:
- [ ] File 1: `backend/app/...`
- [ ] File 2: `backend/app/...`

Questions to answer:
1. What is the expected behavior?
2. What could cause deviation?
3. Are there edge cases not handled?

### Hypothesis 2: [Name]

Key files to examine:
- [ ] File 1: `backend/app/...`
- [ ] File 2: `backend/app/...`

Questions to answer:
1. What is the expected behavior?
2. What could cause deviation?
3. Are there edge cases not handled?

## Phase 4: Document Findings

Create a findings document:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

# Create slug from argument (replace spaces/special chars with dashes)
SLUG=$(echo "$ARGUMENTS" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//' | sed 's/-$//')
FILENAME="debug-session-${SLUG:-unknown}.md"

# Create debug session notes
cat > "$FILENAME" << 'EOF'
# Debug Session: $ARGUMENTS

## Date: $(date +%Y-%m-%d)

## Symptom
[Describe what's happening]

## Evidence Gathered
- Logs: [summary]
- System state: [summary]
- Recent changes: [summary]

## Hypotheses
1. [Most likely] - Confidence: X%
2. [Second] - Confidence: X%
3. [Third] - Confidence: X%

## Recommended Next Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Files to Modify (if proceeding to fix)
- `backend/app/...` - [reason]
- `backend/app/...` - [reason]

## Tests to Add
- Test for edge case A
- Test for edge case B
EOF
```

## Phase 5: Decision Point

After exploration, choose one:

### Option A: Proceed to Fix
If root cause is clear:
```
/project:debug-tdd [issue-description]
```

### Option B: Add Diagnostics
If more data needed:
```
# Add strategic logging and reproduce
```

### Option C: Escalate
If unclear after exploration:
- Document findings in `debug-session-*.md`
- Use `/clear` to reset context
- Resume with fresh perspective
- Consider parallel investigation with subagents

## Key Code Locations by Domain

| Domain | Primary Files |
|--------|---------------|
| **Scheduling** | `backend/app/scheduling/engine.py`, `constraints/` |
| **ACGME** | `backend/app/services/constraints/acgme.py`, `scheduling/constraints/acgme.py` |
| **Swaps** | `backend/app/services/swap_*.py` |
| **Assignments** | `backend/app/services/assignment_service.py` |
| **Resilience** | `backend/app/resilience/` |
| **Auth** | `backend/app/api/routes/auth.py`, `app/core/security.py` |
| **Database** | `backend/app/models/`, `db/session.py` |

## Exploration Guidelines

1. **Read before assuming** - Don't guess; verify
2. **Check tests first** - Tests document expected behavior
3. **Follow the data** - Trace data flow through the system
4. **Question assumptions** - "Known" facts may be wrong
5. **Document everything** - Future-you will thank you

## Common Investigation Patterns

### For Data Issues
```python
# Add to relevant function temporarily
import json
print(f"DEBUG INPUT: {json.dumps(data, default=str, indent=2)}")
```

### For Async Issues
```python
# Check if awaits are being used correctly
import asyncio
print(f"Event loop running: {asyncio.get_event_loop().is_running()}")
```

### For Database Issues
```python
# Log SQL queries
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
```
