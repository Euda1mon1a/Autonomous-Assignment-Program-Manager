# Session 086 v2.0 - Hierarchical Delegation Experiment Redesign

**Status:** Plan approved, ready for execution
**Context:** v1.0 failed because no delegation occurred

## v1.0 Failures (Why We're Redesigning)
- Neither Pool B nor Pool C spawned subagents
- Task didn't require delegation (139 errors could be done solo)
- USASOC used for tactical task (wrong doctrine)
- 50x1 > 5x10 not tested (only 3 agents total)

## v2.0 Design Summary

### Task: Frontend Test Suite Audit (150+ files)
- Real codebase work with production value
- 150+ independent files = forced parallelization

### Four Pools
1. **Pool A: ARCHITECT Pathway** - ORCHESTRATOR → ARCHITECT → COORD_QUALITY → QA_TESTER ×10+
2. **Pool B: SYNTHESIZER Pathway** - ORCHESTRATOR → SYNTHESIZER → COORD_FRONTEND → FRONTEND_ENGINEER ×10+
3. **Pool C: USASOC Pathway** - ORCHESTRATOR → USASOC → 18A → 18F/18Z ×10+
4. **Pool D: G-Staff Party** - ORCHESTRATOR → ARCHITECT → G2_RECON → /search-party (120 probes)

### Doctrinal Mandates (CRITICAL)
- Deputies FORBIDDEN from direct execution
- Each tier MUST spawn next tier down
- Minimum 10 parallel agents at execution tier
- Minimum 3 hierarchy levels

### Measurement
- Hierarchy Depth (20%) - Target 3+ levels
- Delegation Ratio (20%) - % work by Specialists
- Parallel Factor (20%) - Peak concurrent agents
- Task Completion (25%) - Files audited
- Token Efficiency (15%) - Tokens per file

### Penalties
- Direct execution by Deputy: -50
- Direct execution by Coordinator: -25
- <10 parallel agents: -20
- Hierarchy depth <3: -30

## Key Files
- Full plan: `/Users/aaronmontgomery/.claude/plans/idempotent-crunching-lecun.md`
- v1.0 report: `.claude/scratchpad/session-086-experiment-report.md`
- Governance: `.claude/Governance/HIERARCHY.md`
- Identities: `.claude/Identities/`

## Next Steps
1. Approve plan (ExitPlanMode)
2. Count test files
3. Launch 4 pools in parallel
4. Grade with DELEGATION_AUDITOR
