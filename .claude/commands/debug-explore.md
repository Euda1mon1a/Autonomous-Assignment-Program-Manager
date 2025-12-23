<!--
Exploration-first debugging for complex issues where root cause is unclear.
Usage: /project:debug-explore [symptom-description]
Arguments: $ARGUMENTS
-->

***REMOVED*** Debug Exploration: $ARGUMENTS

**CRITICAL: DO NOT WRITE CODE OR FIX ANYTHING DURING THIS EXPLORATION.**

This command is for understanding problems, not solving them.

***REMOVED******REMOVED*** Phase 1: Gather Evidence

***REMOVED******REMOVED******REMOVED*** Check Logs
```bash
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Recent backend logs (if using Docker)
docker-compose logs backend --tail=200 2>/dev/null || echo "Docker not running"

***REMOVED*** Check for error patterns
grep -ri "error\|exception\|failed\|violation" backend/logs/ 2>/dev/null | tail -50

***REMOVED*** Celery task logs
grep -i "task\|celery" backend/logs/*.log 2>/dev/null | tail -30
```

***REMOVED******REMOVED******REMOVED*** Check System State
```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

***REMOVED*** Database health
python -c "from app.db.session import engine; print('DB OK')" 2>&1

***REMOVED*** Redis health
redis-cli ping 2>/dev/null || echo "Redis not available"

***REMOVED*** Recent test failures
pytest --collect-only 2>&1 | grep -i "error" | head -20
```

***REMOVED******REMOVED******REMOVED*** Examine Recent Changes
```bash
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Recent commits to relevant files
git log --oneline -20 -- backend/app/scheduling/
git log --oneline -20 -- backend/app/services/

***REMOVED*** Files changed recently
git diff HEAD~5 --name-only | grep -E "\.py$"
```

***REMOVED******REMOVED*** Phase 2: Form Hypotheses

Based on the evidence, list 5-7 possible causes:

| ***REMOVED*** | Hypothesis | Evidence For | Evidence Against | Test Method |
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

***REMOVED******REMOVED*** Phase 3: Targeted Investigation

For the top 2-3 hypotheses, investigate deeper:

***REMOVED******REMOVED******REMOVED*** Hypothesis 1: [Name]

Key files to examine:
- [ ] File 1: `backend/app/...`
- [ ] File 2: `backend/app/...`

Questions to answer:
1. What is the expected behavior?
2. What could cause deviation?
3. Are there edge cases not handled?

***REMOVED******REMOVED******REMOVED*** Hypothesis 2: [Name]

Key files to examine:
- [ ] File 1: `backend/app/...`
- [ ] File 2: `backend/app/...`

Questions to answer:
1. What is the expected behavior?
2. What could cause deviation?
3. Are there edge cases not handled?

***REMOVED******REMOVED*** Phase 4: Document Findings

Create a findings document:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Create debug session notes
cat > debug-session-$ARGUMENTS.md << 'EOF'
***REMOVED*** Debug Session: $ARGUMENTS

***REMOVED******REMOVED*** Date: $(date +%Y-%m-%d)

***REMOVED******REMOVED*** Symptom
[Describe what's happening]

***REMOVED******REMOVED*** Evidence Gathered
- Logs: [summary]
- System state: [summary]
- Recent changes: [summary]

***REMOVED******REMOVED*** Hypotheses
1. [Most likely] - Confidence: X%
2. [Second] - Confidence: X%
3. [Third] - Confidence: X%

***REMOVED******REMOVED*** Recommended Next Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

***REMOVED******REMOVED*** Files to Modify (if proceeding to fix)
- `backend/app/...` - [reason]
- `backend/app/...` - [reason]

***REMOVED******REMOVED*** Tests to Add
- Test for edge case A
- Test for edge case B
EOF
```

***REMOVED******REMOVED*** Phase 5: Decision Point

After exploration, choose one:

***REMOVED******REMOVED******REMOVED*** Option A: Proceed to Fix
If root cause is clear:
```
/project:debug-tdd [issue-description]
```

***REMOVED******REMOVED******REMOVED*** Option B: Add Diagnostics
If more data needed:
```
***REMOVED*** Add strategic logging and reproduce
```

***REMOVED******REMOVED******REMOVED*** Option C: Escalate
If unclear after exploration:
- Document findings in `debug-session-*.md`
- Use `/clear` to reset context
- Resume with fresh perspective
- Consider parallel investigation with subagents

***REMOVED******REMOVED*** Key Code Locations by Domain

| Domain | Primary Files |
|--------|---------------|
| **Scheduling** | `backend/app/scheduling/engine.py`, `constraints/` |
| **ACGME** | `backend/app/services/constraints/acgme.py`, `scheduling/constraints/acgme.py` |
| **Swaps** | `backend/app/services/swap_*.py` |
| **Assignments** | `backend/app/services/assignment_service.py` |
| **Resilience** | `backend/app/resilience/` |
| **Auth** | `backend/app/api/routes/auth.py`, `app/core/security.py` |
| **Database** | `backend/app/models/`, `db/session.py` |

***REMOVED******REMOVED*** Exploration Guidelines

1. **Read before assuming** - Don't guess; verify
2. **Check tests first** - Tests document expected behavior
3. **Follow the data** - Trace data flow through the system
4. **Question assumptions** - "Known" facts may be wrong
5. **Document everything** - Future-you will thank you

***REMOVED******REMOVED*** Common Investigation Patterns

***REMOVED******REMOVED******REMOVED*** For Data Issues
```python
***REMOVED*** Add to relevant function temporarily
import json
print(f"DEBUG INPUT: {json.dumps(data, default=str, indent=2)}")
```

***REMOVED******REMOVED******REMOVED*** For Async Issues
```python
***REMOVED*** Check if awaits are being used correctly
import asyncio
print(f"Event loop running: {asyncio.get_event_loop().is_running()}")
```

***REMOVED******REMOVED******REMOVED*** For Database Issues
```python
***REMOVED*** Log SQL queries
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
```
