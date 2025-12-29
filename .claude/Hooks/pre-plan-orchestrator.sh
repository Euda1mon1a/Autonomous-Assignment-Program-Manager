***REMOVED***!/bin/bash
***REMOVED*** Pre-Plan Hook: ORCHESTRATOR Reminders
***REMOVED*** Triggered before EnterPlanMode to inject delegation expectations

cat << 'EOF'
***REMOVED******REMOVED*** ORCHESTRATOR Pre-Plan Checklist

Before drafting your plan, evaluate:

***REMOVED******REMOVED******REMOVED*** 1. Complexity Score
```
Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)
```
- 0-5: Execute directly (no delegation)
- 6-10: 2-3 agents
- 11-15: 3-5 agents
- 16+: 5+ agents or phases

***REMOVED******REMOVED******REMOVED*** 2. Delegation Default
If score > 5, your plan MUST show:
- Named PAI agents (SCHEDULER, ARCHITECT, QA_TESTER, etc.)
- Parallel vs sequential streams
- Phase barriers if dependencies exist

***REMOVED******REMOVED******REMOVED*** 3. Session Context
Check ORCHESTRATOR_ADVISOR_NOTES.md for cross-session decisions that may affect this plan.

***REMOVED******REMOVED******REMOVED*** 4. Pre-existing State
Consider running baseline checks (tests, lint) BEFORE planning fixes.
EOF
