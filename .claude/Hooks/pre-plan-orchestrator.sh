#!/bin/bash
# Pre-Plan Hook: ORCHESTRATOR Reminders
# Triggered before EnterPlanMode to inject delegation expectations

cat << 'EOF'
## ORCHESTRATOR Pre-Plan Checklist

Before drafting your plan, evaluate:

### 1. Complexity Score
```
Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)
```
- 0-5: Execute directly (no delegation)
- 6-10: 2-3 agents
- 11-15: 3-5 agents
- 16+: 5+ agents or phases

### 2. Delegation Default
If score > 5, your plan MUST show:
- Named PAI agents (SCHEDULER, ARCHITECT, QA_TESTER, etc.)
- Parallel vs sequential streams
- Phase barriers if dependencies exist

### 3. Session Context
Check ORCHESTRATOR_ADVISOR_NOTES.md for cross-session decisions that may affect this plan.

### 4. Pre-existing State
Consider running baseline checks (tests, lint) BEFORE planning fixes.
EOF
