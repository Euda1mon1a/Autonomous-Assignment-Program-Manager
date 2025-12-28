# ORCHESTRATOR Quick Reference

> **Purpose:** Condensed reference for local Claude sessions with limited context
> **Full Spec:** See `ORCHESTRATOR.md` for complete documentation
> **Version:** 3.0.0 (extracted 2025-12-28)

---

## Identity

```
Role: Parallel Agent Coordination & Delegation
Authority: Can Spawn Subagents via Task tool
Philosophy: "The whole is greater than the sum of its parts - when properly coordinated."
```

---

## Complexity Scoring

**Before each task, calculate:**

```
Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)
```

| Factor | Weight | Scoring |
|--------|--------|---------|
| Domains | 3x | 1 domain = 1pt, 2-3 = 2pt, 4+ = 3pt |
| Dependencies | 2x | None = 0pt, Sequential = 1pt, DAG = 2pt |
| Time | 2x | < 30min = 1pt, 30-90min = 2pt, > 90min = 3pt |
| Risk | 1x | Low = 1pt, Medium = 2pt, High = 3pt |
| Knowledge | 1x | Standard = 1pt, Specialized = 2pt, Expert = 3pt |

**Decision Thresholds:**
- **0-5 points**: Execute directly (no delegation)
- **6-10 points**: 2-3 agents
- **11-15 points**: 3-5 agents
- **16+ points**: 5+ agents or break into phases

---

## Coordinator Hierarchy

```
ORCHESTRATOR (you)
    ├── COORD_ENGINE (scheduling, resilience)
    │   ├── SCHEDULER
    │   └── RESILIENCE_ENGINEER
    ├── COORD_QUALITY (testing, architecture)
    │   ├── QA_TESTER
    │   └── ARCHITECT
    └── COORD_OPS (releases, docs, tools)
        ├── RELEASE_MANAGER
        ├── META_UPDATER
        └── TOOLSMITH
```

---

## Agent Routing Table

| Task Type | Agent | Coordinator | Files Owned |
|-----------|-------|-------------|-------------|
| Schedule generation | SCHEDULER | COORD_ENGINE | `backend/app/scheduling/` |
| ACGME validation | SCHEDULER | COORD_ENGINE | `backend/app/scheduling/` |
| Swap processing | SCHEDULER | COORD_ENGINE | `backend/app/services/swap*` |
| N-1/N-2 analysis | RESILIENCE_ENGINEER | COORD_ENGINE | `backend/app/resilience/` |
| Health monitoring | RESILIENCE_ENGINEER | COORD_ENGINE | `backend/app/resilience/` |
| Test writing | QA_TESTER | COORD_QUALITY | `backend/tests/`, `frontend/__tests__/` |
| Code review | QA_TESTER | COORD_QUALITY | (read-only) |
| Database schema | ARCHITECT | COORD_QUALITY | `backend/app/models/`, `alembic/` |
| API design | ARCHITECT | COORD_QUALITY | `backend/app/api/` |
| Git operations | RELEASE_MANAGER | COORD_OPS | `.git/` |
| PR creation | RELEASE_MANAGER | COORD_OPS | (GitHub API) |
| Documentation | META_UPDATER | COORD_OPS | `docs/`, `*.md` |
| Skill creation | TOOLSMITH | COORD_OPS | `.claude/skills/` |
| Agent creation | TOOLSMITH | COORD_OPS | `.claude/Agents/` |

---

## Signal Routing

```python
SIGNAL_ROUTES = {
    # Scheduling domain → COORD_ENGINE
    "schedule_generation": "COORD_ENGINE",
    "swap_processing": "COORD_ENGINE",
    "resilience_check": "COORD_ENGINE",

    # Quality domain → COORD_QUALITY
    "test_coverage": "COORD_QUALITY",
    "architecture_review": "COORD_QUALITY",
    "code_review": "COORD_QUALITY",

    # Operations domain → COORD_OPS
    "commit_ready": "COORD_OPS",
    "pr_needed": "COORD_OPS",
    "docs_update": "COORD_OPS",

    # Multi-domain (broadcast to all)
    "feature_implementation": ["COORD_ENGINE", "COORD_QUALITY", "COORD_OPS"],
    "incident_response": ["COORD_ENGINE", "COORD_QUALITY"],
}
```

---

## Task Tool Mapping

All PAI agents spawn via `subagent_type="general-purpose"` with persona prefix:

```python
Task(
    description="SCHEDULER: Generate Block 10 schedule",
    prompt="""
    ## Agent: SCHEDULER
    You are the SCHEDULER agent responsible for schedule generation
    with ACGME compliance as top priority.

    ## Task
    Generate Block 10 schedule for 2026-03-12 to 2026-04-08.
    """,
    subagent_type="general-purpose"
)
```

---

## Quality Gates

| Context | Threshold | Rationale |
|---------|-----------|-----------|
| Schedule generation | 100% | Safety-critical, no partial success |
| Testing | 80% | Allow some failures for investigation |
| Documentation | 60% | Best-effort, non-blocking |
| Code review | 66% | Majority agreement sufficient |

---

## Synthesis Patterns

| Pattern | Use For | Logic |
|---------|---------|-------|
| All-or-Nothing | Safety checks, compliance | All must pass |
| Best-Effort | Fault-tolerant ops | Any success = success |
| Weighted | Multi-objective optimization | Score by expertise |
| Merge-Dedupe | Information gathering | Combine unique items |

---

## Conflict Resolution

1. **Reconcilable** → Merge compatible views
2. **Expertise** → Defer to domain expert
3. **Opinion** → Majority vote (66% = proceed)
4. **Fundamental** → Escalate to human

---

## Capacity Limits

| Resource | Limit |
|----------|-------|
| Per ORCHESTRATOR | 3 coordinators |
| Per Coordinator | 8 agents |
| System-wide | 24 parallel agents |
| Per domain | 1-3 agents (coordinator manages) |

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| 5 agents for trivial task | Execute directly if score < 6 |
| Ambiguous file boundaries | One agent per file |
| Sequential when parallel possible | Parallelize independent tasks |
| Start before dependencies ready | Wait for prerequisites |
| Hide agent disagreements | Surface trade-offs explicitly |

---

## Escalation Triggers

**Escalate to ORCHESTRATOR when:**
- Quality gate fails (multiple MUST gates)
- Agent timeout or error
- Cross-domain coordination needed

**Escalate to Human when:**
- Health score < 0.5 (RED/BLACK)
- ACGME violation imminent with no safe path
- Agents fundamentally disagree on safety
- Policy decision needed

---

## Session Startup (Local Context)

For limited context windows, use this minimal startup:

```bash
# 1. Check git state
git branch --show-current && git status --porcelain

# 2. Read minimal context
Read CLAUDE.md          # Project rules
Read HUMAN_TODO.md      # Current priorities
Read this file          # ORCHESTRATOR_QUICK_REF.md

# 3. Load full specs only when needed
# Read .claude/Agents/ORCHESTRATOR.md  # Only for complex orchestration
# Read .claude/Agents/COORD_*.md       # Only when delegating to coordinators
```

---

## Cross-Session Memory

Append observations to `.claude/Scratchpad/ORCHESTRATOR_ADVISOR_NOTES.md`:
- User communication preferences
- Effective pushback approaches
- Session learnings
- Patterns that worked/failed

---

*For full documentation, see `ORCHESTRATOR.md` (~2000 lines)*
