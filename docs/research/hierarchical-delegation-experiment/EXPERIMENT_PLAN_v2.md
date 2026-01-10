# Plan: Hierarchical Delegation Experiment v2.0 - Total Redesign

**Date:** 2026-01-10
**Status:** Planning
**Type:** Comprehensive Hierarchy + Doctrine + Parallelization Test
**Previous Version:** v1.0 (Session 086) - FAILED due to no actual delegation

---

## Why v1.0 Failed

The previous experiment was fundamentally flawed:

| Failure | Root Cause | Fix in v2.0 |
|---------|-----------|-------------|
| No delegation occurred | Task didn't require it | Structural + doctrinal mandate |
| SOF vs Conventional not tested | Both operated solo | Force hierarchy traversal |
| 50x1 principle not tested | Only 3 agents, not 50 | 100+ file task requiring parallelization |
| Wrong force selection | USASOC for tactical task | Match doctrine to mission type |

---

## v2.0 Experiment Design

### Objectives (All Three)
1. **Test hierarchy traversal** - Verify ORCHESTRATOR → Deputy → Coordinator → Specialist chain
2. **Compare SOF vs Conventional** - Fair comparison on equivalent tasks
3. **Maximize parallel efficiency** - Test 50×1 > 5×10 with real parallelization

### Hypothesis
Proper hierarchical delegation with parallelization will outperform both solo execution AND improper force structure selection, regardless of SOF vs Conventional doctrine.

---

## Task Selection: Real Codebase Work

### Candidate Tasks (100+ independent subtasks)

**Option A: Full Frontend Test Suite Audit**
- 150+ test files in `frontend/__tests__/` and `frontend/src/**/__tests__/`
- Each file = 1 independent audit task
- Output: Coverage gaps, mock quality, assertion completeness
- Real value: Improve test suite quality

**Option B: Codebase-Wide Documentation Audit**
- 200+ TypeScript/Python files lacking JSDoc/docstrings
- Each file = 1 independent documentation task
- Output: Function documentation coverage report
- Real value: Improve code documentation

**Option C: API Contract Verification**
- Backend endpoints vs Frontend API client alignment
- 50+ endpoints to verify
- Output: Contract mismatches, type drift
- Real value: Prevent integration bugs

**SELECTED: Option A (Frontend Test Suite Audit)**
- Reason: Clear parallelization (1 file = 1 agent), measurable outcomes, real value
- Scale: ~150 files requiring parallel agents

---

## Force Structures (v2.0)

### Pool A: ARCHITECT Pathway (Conventional - Technical)
```
ORCHESTRATOR
└── ARCHITECT (Deputy)
    └── COORD_QUALITY (Coordinator)
        └── QA_TESTER × N (Specialists - 1 per file batch)
```
- **Doctrine**: Hierarchical chain of command
- **Mandate**: MUST spawn at least 10 parallel QA_TESTER agents
- **Model Mix**: Opus → Sonnet → Haiku

### Pool B: SYNTHESIZER Pathway (Conventional - Operations)
```
ORCHESTRATOR
└── SYNTHESIZER (Deputy)
    └── COORD_FRONTEND (Coordinator)
        └── FRONTEND_ENGINEER × N (Specialists - 1 per file batch)
```
- **Doctrine**: Hierarchical chain of command
- **Mandate**: MUST spawn at least 10 parallel FRONTEND_ENGINEER agents
- **Model Mix**: Opus → Sonnet → Sonnet

### Pool C: USASOC Pathway (SOF - Wide Lateral)
```
ORCHESTRATOR
└── USASOC (Deputy)
    └── 18A_DETACHMENT_COMMANDER (ODA Lead)
        ├── 18F_INTEL × N (Reconnaissance - parallel)
        └── 18Z_OPERATIONS × N (Execution - parallel)
```
- **Doctrine**: Wide lateral authority, mission-type orders
- **Mandate**: MUST spawn at least 10 parallel 18-series operators
- **Model Mix**: Opus → Opus → Sonnet

### Pool D: G-Staff Party (Parallel Probes)
```
ORCHESTRATOR
└── ARCHITECT (Deputy)
    └── G2_RECON
        └── /search-party (120 probes)
```
- **Doctrine**: Maximum parallelization via party deployment
- **Mandate**: Deploy full 120-probe search-party
- **Model Mix**: Opus → Sonnet → Haiku × 120

---

## Doctrinal Mandates (CRITICAL)

Each pool receives explicit delegation requirements in their mission prompt:

### Universal Mandate
```
## DELEGATION REQUIREMENT (MANDATORY)

You are FORBIDDEN from executing file-level work directly.
You MUST delegate to the appropriate tier:
- Deputies delegate to Coordinators
- Coordinators delegate to Specialists
- Specialists execute

VIOLATION: Any direct Read/Edit/Write on test files by non-Specialist tier
is a protocol violation and will be scored as FAILURE.

Your job is COMMAND, not EXECUTION.
```

### Hierarchy Traversal Requirement
```
## HIERARCHY TRAVERSAL (MANDATORY)

Each tier MUST spawn the next tier down:
- ORCHESTRATOR → Deputy (1 spawn minimum)
- Deputy → Coordinator (1 spawn minimum)
- Coordinator → Specialist (10 spawns minimum)

Total delegation depth: 3 levels minimum
Total parallel agents: 10+ minimum at execution tier
```

### Parallelization Requirement
```
## PARALLELIZATION (MANDATORY)

The execution tier MUST operate in parallel:
- Split 150 files across 10+ agents
- Each agent handles 10-15 files maximum
- Agents run concurrently (not sequentially)

This tests the 50×1 > 5×10 principle.
```

---

## Measurement Criteria

| Metric | Weight | How Measured |
|--------|--------|--------------|
| Hierarchy Depth | 20% | Levels traversed (target: 3+) |
| Delegation Ratio | 20% | % work done by Specialists vs higher tiers |
| Parallel Factor | 20% | Peak concurrent agents |
| Task Completion | 25% | Files audited / total files |
| Token Efficiency | 15% | Tokens per file audited |

### Violation Penalties
- Direct execution by Deputy: -50 points
- Direct execution by Coordinator: -25 points
- < 10 parallel agents: -20 points
- Hierarchy depth < 3: -30 points

---

## Execution Plan

### Phase 1: Preparation
1. Count actual test files: `find frontend -name "*.test.tsx" -o -name "*.test.ts" | wc -l`
2. Prepare file lists for each pool (equal distribution)
3. Load identity cards for all agents in each pathway

### Phase 2: Parallel Launch (4 Pools)
Launch all 4 pools simultaneously in background:
- Pool A: ARCHITECT pathway
- Pool B: SYNTHESIZER pathway
- Pool C: USASOC pathway
- Pool D: G2_RECON /search-party

### Phase 3: Observation
- Monitor delegation patterns via task logs
- Count spawned agents per pool
- Track hierarchy depth achieved

### Phase 4: Grading
- DELEGATION_AUDITOR: Verify hierarchy compliance
- G6_SIGNAL: Quantitative metrics
- COORD_AAR: Lessons learned

---

## Key Files

- Plan: `/Users/aaronmontgomery/.claude/plans/idempotent-crunching-lecun.md`
- Scratchpad: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/scratchpad/`
- Identities: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Identities/`
- Governance: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Governance/`

---

## Status: READY FOR EXECUTION

v2.0 addresses all v1.0 failures:
- ✅ Mandatory delegation (doctrinal)
- ✅ Full hierarchy traversal (3+ levels)
- ✅ Parallel execution (10+ agents)
- ✅ Real codebase work (test audit)
- ✅ 4 pools comparing doctrines

---

## Replication Notes

To replicate this experiment in another codebase:

1. **Identify 100+ independent files** for audit/remediation
2. **Define clear success criteria** (e.g., 0 TypeScript errors)
3. **Create agent identity cards** in `.claude/Identities/`
4. **Include doctrinal mandates** in mission prompts
5. **Launch pools in parallel** via Task() with `run_in_background=true`
6. **Grade with neutral panel** (G6_SIGNAL, CODE_REVIEWER, DELEGATION_AUDITOR)

The key insight from v1.0: **Tasks must structurally require delegation**. 139 errors across 58 files could be done solo. 150+ files with mandatory 10+ parallel agents forces delegation.
