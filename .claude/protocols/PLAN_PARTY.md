# PLAN_PARTY Protocol

> **Purpose:** Coordinated parallel planning with multiple strategy "framings"
> **Status:** Active
> **Priority:** P1
> **Owner:** G5_PLANNING
> **Skill:** `/plan-party`
> **Upstream:** SEARCH_PARTY (reconnaissance feeds planning)
> **Downstream:** ORCHESTRATOR (execution decisions)

---

## Overview

PLAN_PARTY enables parallel generation of implementation strategies from multiple perspectives - like a military planning cell where G-3 Operations synthesizes input from J1-J8 staff sections, each bringing domain-specific planning expertise.

---

## IDE Crash Prevention (CRITICAL)

**DO NOT** have ORCHESTRATOR spawn 10 planning probes directly. This causes IDE seizure and crashes.

**CORRECT Pattern:**
```
ORCHESTRATOR → spawns 1 G5_PLANNING (G-5 Commander)
                    ↓
              G5_PLANNING deploys 10 planning probes internally
              (manages parallelism, synthesizes strategies)
```

**WRONG Pattern:**
```
ORCHESTRATOR → spawns 10 planning probes directly → IDE CRASH
```

The G-5 Commander (G5_PLANNING) absorbs the parallelism complexity. ORCHESTRATOR only ever spawns 1 coordinator.

**Key Insight:** Same goal, different strategies. Synthesizing diverse plans yields better decisions than a single planning thread.

**Relationship to SEARCH_PARTY:**
```
SEARCH_PARTY (10 recon probes) → G2_RECON (intel synthesis)
                                        ↓
PLAN_PARTY (10 plan probes) → PLAN_COORDINATOR (strategy synthesis)
                                        ↓
                              ORCHESTRATOR (execution)
```

---

## Economics: Zero Marginal Wall-Clock Cost

Same as SEARCH_PARTY - parallel planners with the same timeout cost nothing extra in wall-clock time.

```
Sequential (BAD):        Parallel (GOOD):
┌──────────┐             ┌──────────┐
│ Planner 1│ 60s         │ Planner 1│ ┐
├──────────┤             ├──────────┤ │
│ Planner 2│ 60s         │ Planner 2│ │
├──────────┤             ├──────────┤ │
│ Planner 3│ 60s         │ Planner 3│ │
├──────────┤             ├──────────┤ │ 60s total
│    ...   │             │    ...   │ │
├──────────┤             ├──────────┤ │
│ Planner10│ 60s         │ Planner10│ ┘
└──────────┘             └──────────┘
Total: 600s              Total: 60s (10x faster)
```

---

## The Ten Planning Probes (Framings)

| Probe | Framing | Military Analog | What It Produces |
|-------|---------|-----------------|------------------|
| **CRITICAL_PATH** | Time-optimal | G-3 Operations | Minimum-step plan, dependency chain, timeline |
| **RISK_MINIMAL** | Safety-first | G-2 Risk | Conservative approach, fallback at every step, rollback plan |
| **PARALLEL_MAX** | Concurrency-optimal | J-6 Communications | Maximum parallel streams, synchronization points |
| **RESOURCE_MIN** | Lean execution | G-4 Logistics | Smallest agent count, reuse specialists, minimize handoffs |
| **QUALITY_GATE** | Test-driven | J-8 Inspector General | Test-first approach, verification at each step |
| **INCREMENTAL** | Progressive delivery | Agile/Scrum | Small PRs, frequent commits, user feedback loops |
| **DOMAIN_EXPERT** | Specialist-led | Subject Matter Expert | Route to domain coordinators, leverage existing expertise |
| **PRECEDENT** | Pattern-matching | Historian/AAR | Apply proven patterns from similar past tasks |
| **ADVERSARIAL** | Red team | G-2 Threat | What could go wrong? Plan for failure modes |
| **SYNTHESIS** | Multi-objective | J-5 Strategic Plans | Balance all concerns, Pareto-optimal approach |

### Probe Characteristics

#### CRITICAL_PATH Probe
**Focus:** What's the fastest route to completion?
**Outputs:**
- Dependency graph (DAG)
- Minimum steps to completion
- Critical path identification
- Timeline estimate
- Bottleneck warnings

**Questions Asked:**
- What MUST happen sequentially?
- What can be parallelized?
- What's the longest dependency chain?
- Where are the natural checkpoints?

#### RISK_MINIMAL Probe
**Focus:** How do we minimize blast radius?
**Outputs:**
- Risk matrix for each step
- Fallback plan for each step
- Rollback procedures
- Safety gates
- Escalation triggers

**Questions Asked:**
- What can go wrong at each step?
- How do we detect failure early?
- What's the rollback cost?
- Where should we checkpoint?

#### PARALLEL_MAX Probe
**Focus:** Maximum concurrency extraction
**Outputs:**
- Parallelization opportunities
- Stream assignments (A, B, C...)
- Synchronization points
- Merge strategy
- Coordinator assignments

**Questions Asked:**
- Which tasks are truly independent?
- What can 10 agents do simultaneously?
- Where must streams converge?
- What's the ideal coordinator split?

#### RESOURCE_MIN Probe
**Focus:** Lean execution, minimal overhead
**Outputs:**
- Minimum agent count
- Specialist reuse plan
- Handoff minimization
- Context efficiency
- "Do it yourself" vs delegate decision

**Questions Asked:**
- Can ORCHESTRATOR do this directly?
- How many agents are truly needed?
- Can one agent handle multiple steps?
- What's the delegation overhead vs. direct execution?

#### QUALITY_GATE Probe
**Focus:** Test-driven, verification-first
**Outputs:**
- Test strategy per step
- Acceptance criteria
- Coverage requirements
- Pre-commit checks
- CI/CD integration points

**Questions Asked:**
- What tests must pass before each step?
- How do we verify correctness?
- What's the 80% coverage plan?
- When does COORD_QUALITY engage?

#### INCREMENTAL Probe
**Focus:** Progressive delivery, fast feedback
**Outputs:**
- Smallest viable increments
- PR strategy (many small vs few large)
- User feedback integration points
- Feature flag strategy
- Progressive rollout plan

**Questions Asked:**
- What's the smallest shippable unit?
- How quickly can we get user feedback?
- Can we feature-flag partial work?
- What's the "walking skeleton" approach?

#### DOMAIN_EXPERT Probe
**Focus:** Leverage existing coordinator expertise
**Outputs:**
- Coordinator assignment matrix
- Domain boundary respect
- Expert agent selection
- Specialist escalation paths
- Cross-domain coordination needs

**Questions Asked:**
- Which coordinators own this work?
- What domain expertise is required?
- Who are the specialist agents?
- Where are the domain boundaries?

#### PRECEDENT Probe
**Focus:** Apply proven patterns from history
**Outputs:**
- Similar past tasks/sessions
- Applicable patterns
- Lessons learned to apply
- Anti-patterns to avoid
- Success/failure indicators from prior work

**Questions Asked:**
- Have we done something similar before?
- What patterns from SEARCH_PARTY sessions apply?
- What anti-patterns should we avoid?
- What worked last time?

#### ADVERSARIAL Probe
**Focus:** Red team the plan, find weaknesses
**Outputs:**
- Failure mode analysis
- Attack surface identification
- Edge case inventory
- Stress points
- "What kills us?" analysis

**Questions Asked:**
- How does this plan fail?
- What edge cases break it?
- Where's the single point of failure?
- What does COORD_RESILIENCE flag?

#### SYNTHESIS Probe
**Focus:** Balance all concerns, find Pareto frontier
**Outputs:**
- Multi-objective scoring
- Trade-off analysis
- Balanced recommendation
- Stakeholder considerations
- Decision matrix

**Questions Asked:**
- How do we balance speed vs. quality vs. safety?
- What's the Pareto-optimal approach?
- Which trade-offs are acceptable?
- What does the user value most?

---

## Protocol Flow

### Phase 1: Intel Receipt

PLAN_PARTY receives reconnaissance from G2_RECON:

```markdown
## Planning Mission

**Intel Source:** G2_RECON SEARCH_PARTY Brief
**Target:** [Component/Feature/Bug]
**Goal:** [What needs to be accomplished]
**Constraints:** [Time, resources, scope limits]
**Risk Tolerance:** [LOW/MEDIUM/HIGH]
**Priority:** [P0-P3]
```

### Phase 2: Party Deployment

Spawn all 10 planning probes **IN PARALLEL** with identical timeout:

```python
# Pseudocode - spawn all 10 with same timeout
timeout = 90000  # 90 seconds (longer than recon - planning is harder)

spawn_parallel([
    ("CRITICAL_PATH", intel_brief, timeout),
    ("RISK_MINIMAL", intel_brief, timeout),
    ("PARALLEL_MAX", intel_brief, timeout),
    ("RESOURCE_MIN", intel_brief, timeout),
    ("QUALITY_GATE", intel_brief, timeout),
    ("INCREMENTAL", intel_brief, timeout),
    ("DOMAIN_EXPERT", intel_brief, timeout),
    ("PRECEDENT", intel_brief, timeout),
    ("ADVERSARIAL", intel_brief, timeout),
    ("SYNTHESIS", intel_brief, timeout),
])
```

Each probe receives:
- Complete intel brief from G2_RECON
- Their specific framing/lens
- Output format requirements
- Same goal definition

### Phase 3: Collection

Gather plans from all probes. Structure:

```markdown
## Plan Proposal: [PROBE_NAME]

### Strategy Summary
[2-3 sentence approach]

### Steps
1. [Step 1] - [Owner] - [Est. time]
2. [Step 2] - [Owner] - [Est. time]
...

### Dependencies
[DAG representation]

### Risks
- [Risk 1]: [Mitigation]

### Trade-offs
- Prioritizes: [X over Y]

### Confidence: [HIGH/MEDIUM/LOW]
```

### Phase 4: Cross-Reference (Signal Amplification)

**This is where the magic happens.**

Compare plans across probes. Agreements are high-confidence; disagreements reveal trade-offs:

| Agreement Type | Signal Meaning |
|---------------|----------------|
| All 10 agree on Step 1 | High-confidence critical step |
| CRITICAL_PATH vs RISK_MINIMAL disagree | Speed/safety trade-off to surface |
| PARALLEL_MAX and DOMAIN_EXPERT align | Coordinator assignment validated |
| ADVERSARIAL flags what others missed | Hidden risk discovered |
| PRECEDENT matches current approach | Pattern is proven |
| Only SYNTHESIS recommends X | Balanced but unconventional approach |

**Convergence Analysis:**

```markdown
### Convergence Matrix

| Step/Decision | Probes Agreeing | Divergence | Signal |
|--------------|-----------------|------------|--------|
| Start with schema design | 9/10 | INCREMENTAL wants spike first | High confidence |
| Use COORD_ENGINE | 8/10 | RESOURCE_MIN says direct | Consider overhead |
| 3 parallel streams | 6/10 | Split on 2 vs 4 | Medium confidence |
| Test-first | 10/10 | None | Unanimous |
```

### Phase 5: Strategy Selection

Based on convergence analysis, select strategy:

**Selection Criteria:**
1. **Unanimous agreement** → Execute that step
2. **Majority with clear trade-off** → Present options to user
3. **Even split** → Escalate to ORCHESTRATOR for decision
4. **ADVERSARIAL red flag** → Must address before proceeding

**Strategy Selection Matrix:**

| Scenario | User Risk Tolerance | Selection |
|----------|-------------------|-----------|
| High convergence | Any | Execute consensus plan |
| Speed vs Safety split | LOW | RISK_MINIMAL approach |
| Speed vs Safety split | HIGH | CRITICAL_PATH approach |
| Parallelism debate | Time-critical | PARALLEL_MAX approach |
| Parallelism debate | Resource-limited | RESOURCE_MIN approach |

### Phase 6: Synthesis

Deliver integrated execution plan to ORCHESTRATOR:

```markdown
## PLAN_PARTY Execution Plan

### Mission: [What was asked]

### Selected Strategy: [PROBE_NAME] with modifications from [OTHER_PROBES]

### Convergence Score: [N/10 probes agreed on core approach]

### Execution Plan

#### Phase 1: [Name] (Parallel)
| Stream | Owner | Task | Depends On |
|--------|-------|------|------------|
| A | COORD_ENGINE | [task] | - |
| B | COORD_PLATFORM | [task] | - |
| C | COORD_QUALITY | [task] | - |

#### Phase 2: [Name] (Sequential - depends on Phase 1)
| Step | Owner | Task | Gate |
|------|-------|------|------|
| 1 | [agent] | [task] | [test/review] |
| 2 | [agent] | [task] | [test/review] |

### Risk Mitigations (from ADVERSARIAL)
- [Risk 1]: [Mitigation baked into plan]
- [Risk 2]: [Escalation trigger]

### Quality Gates (from QUALITY_GATE)
- [ ] Gate 1: [criteria]
- [ ] Gate 2: [criteria]

### Rollback Plan (from RISK_MINIMAL)
- Checkpoint 1: [what to save]
- Rollback procedure: [how to undo]

### Trade-offs Accepted
- Chose [X] over [Y] because [rationale]

### Disagreements for User Decision
1. [Probe A] vs [Probe B]: [issue] - Recommend: [suggestion]

### Estimated Timeline
- Phase 1: [time]
- Phase 2: [time]
- Total: [time]

### Confidence: [HIGH/MEDIUM/LOW]
```

---

## Integration with SEARCH_PARTY

### Full Intelligence-to-Execution Pipeline

```
User Request
    ↓
ORCHESTRATOR receives task
    ↓
G2_RECON deploys SEARCH_PARTY (10 recon probes)
    ├─ PERCEPTION
    ├─ INVESTIGATION
    ├─ ARCANA
    ├─ HISTORY
    ├─ INSIGHT
    ├─ RELIGION
    ├─ NATURE
    ├─ MEDICINE
    ├─ SURVIVAL
    └─ STEALTH
    ↓
G2_RECON synthesizes Intel Brief
    ↓
PLAN_PARTY deployed (10 planning probes)
    ├─ CRITICAL_PATH
    ├─ RISK_MINIMAL
    ├─ PARALLEL_MAX
    ├─ RESOURCE_MIN
    ├─ QUALITY_GATE
    ├─ INCREMENTAL
    ├─ DOMAIN_EXPERT
    ├─ PRECEDENT
    ├─ ADVERSARIAL
    └─ SYNTHESIS
    ↓
PLAN_COORDINATOR synthesizes Execution Plan
    ↓
ORCHESTRATOR reviews, approves, or escalates to user
    ↓
ORCHESTRATOR spawns coordinators per plan
    ↓
Parallel Execution
    ↓
Result Synthesis
    ↓
User Delivery
```

### Signal Propagation

```
SEARCH_PARTY → Intel Brief → PLAN_PARTY → Execution Plan → ORCHESTRATOR
     ↓                            ↓                           ↓
(10 recon signals)          (10 plan signals)          (execution signals)
     ↓                            ↓                           ↓
Synthesis                    Synthesis                   Synthesis
(G2_RECON)                 (PLAN_COORD)               (COORD_AAR)
```

---

## When to Use PLAN_PARTY

### Good Candidates

- Complex multi-phase implementations
- High-stakes changes (production, compliance)
- Multiple valid approaches exist
- User asked for a plan before execution
- Task touches 3+ coordinator domains
- Previous similar task had issues

### Poor Candidates

- Simple, obvious tasks (just do it)
- Emergency/time-critical (no time for planning)
- Already have a clear, validated plan
- Single-domain, single-agent work

### Decision Rule

```python
def use_plan_party(task: Task, intel: IntelBrief) -> bool:
    """Should we deploy PLAN_PARTY?"""

    PLAN_PARTY_TRIGGERS = [
        task.complexity_score > 10,  # From ORCHESTRATOR rubric
        intel.risk_level in ["HIGH", "CRITICAL"],
        len(intel.domains_affected) >= 3,
        "plan" in task.goal.lower(),
        task.touches_production,
        intel.precedent_had_issues,
        task.user_requested_plan,
    ]

    SKIP_PLANNING = [
        task.complexity_score <= 5,
        task.priority == "P0",  # Emergency, just fix it
        task.type == "trivial_fix",
    ]

    if any(SKIP_PLANNING):
        return False

    return any(PLAN_PARTY_TRIGGERS)
```

---

## TodoWrite Integration

When PLAN_PARTY produces an execution plan, translate to TodoWrite format:

```python
# From PLAN_PARTY output to TodoWrite
def plan_to_todos(execution_plan: ExecutionPlan) -> list[Todo]:
    todos = []

    for phase in execution_plan.phases:
        for task in phase.tasks:
            todos.append({
                "content": task.description,
                "status": "pending",
                "activeForm": task.active_form,
                "parallel_group": phase.name if phase.parallel else None,
                "can_merge_after": task.dependencies,
                "blocks": task.blocks,
                "stream": task.stream,
            })

    return todos
```

Example output:
```
## Tasks (from PLAN_PARTY)

### Phase 1: Schema Design (Parallel)
- [ ] Design database schema (Stream A) - COORD_PLATFORM
- [ ] Design API contract (Stream B) - COORD_PLATFORM
- [ ] Write test specifications (Stream C) - COORD_QUALITY

### Phase 2: Implementation (Sequential, after Phase 1)
- [ ] Create Alembic migration - blocked by: schema-design
- [ ] Implement service layer - blocked by: migration
- [ ] Implement API endpoints - blocked by: service

### Phase 3: Validation (Parallel, after Phase 2)
- [ ] Run test suite (Stream A) - COORD_QUALITY
- [ ] Security audit (Stream B) - COORD_RESILIENCE
- [ ] Documentation (Stream C) - COORD_OPS
```

---

## PLAN_COORDINATOR Agent (Proposed)

### Charter

The PLAN_COORDINATOR (or integrate into ORCHESTRATOR directly) is responsible for:
1. Receiving intel briefs from G2_RECON
2. Deploying PLAN_PARTY (10 planning probes)
3. Synthesizing execution plans
4. Presenting trade-offs to ORCHESTRATOR/user
5. Translating plans to TodoWrite format

### Authority

**Can Independently:**
- Deploy all 10 planning probes
- Synthesize plans from probe output
- Select strategy when convergence is high (8+/10)
- Generate TodoWrite tasks

**Requires Approval:**
- Execute plan (must go through ORCHESTRATOR)
- Select strategy when convergence is low (<6/10)
- Override user risk tolerance

### Integration Options

**Option A: Standalone PLAN_COORDINATOR**
```
ORCHESTRATOR
├─ G2_RECON (recon)
├─ PLAN_COORDINATOR (planning) ← new
├─ COORD_ENGINE
├─ ...
```

**Option B: Integrated into ORCHESTRATOR**
```
ORCHESTRATOR (enhanced with PLAN_PARTY capability)
├─ G2_RECON (recon)
├─ COORD_ENGINE
├─ ...
```

**Option C: COORD_OPS Subfunction**
```
COORD_OPS
├─ RELEASE_MANAGER
├─ TOOLSMITH
├─ PLAN_PARTY_RUNNER ← new specialist
```

**Recommendation:** Option B (integrate into ORCHESTRATOR) for simplicity, or Option A if planning complexity warrants dedicated coordination.

---

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Sequential planning | 10x slower for no benefit | Always parallel |
| Ignoring convergence | Miss high-confidence decisions | Track agreement rates |
| Single-probe planning | Incomplete picture | Deploy full party |
| Planning when obvious | Overhead without value | Skip for simple tasks |
| Ignoring ADVERSARIAL | Hidden risks surface in execution | Always red-team |
| No precedent check | Repeat past mistakes | Always check history |

---

## Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Probe completion rate | 100% | All framings must report |
| Convergence score | > 6/10 typical | High agreement = confidence |
| Plan execution success | > 90% | Plans should be executable |
| Replanning rate | < 10% | Good plans don't need rework |
| User override rate | < 20% | Plans should match user intent |

---

## Related Protocols

- `SEARCH_PARTY.md` - Upstream reconnaissance
- `SIGNAL_PROPAGATION.md` - Inter-agent signaling
- `PARALLELISM_FRAMEWORK.md` - Execution parallelism rules
- `RESULT_STREAMING.md` - Progress visibility

## Related Agents

- `G2_RECON.md` - Provides intel briefs
- `ORCHESTRATOR.md` - Receives execution plans
- `FORCE_MANAGER.md` - May assist with resource allocation

---

*PLAN_PARTY: Ten strategies, one goal, signal-amplified planning. Convergence is confidence.*
