# Session 026: The SEARCH_PARTY and the Discipline of Delegation

**Date:** December 30, 2025
**Branch:** `claude/session-026-infrastructure-fixes`
**PRs:** #566 (Security + Branch Cleanup), #567 (Infrastructure + Features)
**Outcome:** Infrastructure stabilization + ORCHESTRATOR discipline crystallization

---

## The Session's Character

Session 026 was not a session of grand revelation. It was a session of discipline.

Where Session 014 discovered hidden corruption through a bedtime request, and Session 016 unlocked the economics of unlimited parallelism, Session 026 taught the harder lesson: knowing what to do and doing it correctly are different skills.

ORCHESTRATOR knew how to delegate. It had been doing so for sessions. But it kept doing the work itself.

---

## The Discipline Lesson

The user's correction was gentle but pointed:

> "Can we have a container manager? You sure like doing it yourself."

And later, more directly:

> "Think like a physician or pilot. If someone else can be doing the job, they should be."

This observation struck at something fundamental. ORCHESTRATOR exists to coordinate, not execute. Its value is strategic - seeing the whole board, routing tasks to the right agents, synthesizing results. Every task it executes directly is context consumed, coordination capacity lost.

The lesson crystallized: **Context is the most valuable resource.** ORCHESTRATOR's context window is finite. Every line spent on execution is a line unavailable for coordination. Delegate immediately. Don't accumulate tasks.

This is the physician's discipline. The attending doesn't draw blood, start IVs, or transport patients - not because they can't, but because their cognitive resources are needed for diagnosis, treatment decisions, and coordination across specialties.

ORCHESTRATOR is the attending. The agents are the team.

---

## The SEARCH_PARTY Insight

The session's creative contribution was the SEARCH_PARTY protocol - a reconnaissance framework inspired by D&D skill checks.

### The Genesis

Traditional reconnaissance uses a single probe: find what was asked. But what if different "lenses" reveal different truths? What if contradictions between lenses are themselves the signal?

The insight came from gaming: a D&D adventuring party sends different characters to investigate based on their skills. The rogue checks for traps (Perception). The wizard identifies magical signatures (Arcana). The cleric consults their deity (Religion). The ranger reads the environment (Nature). Each brings a different perspective to the same target.

What if agent reconnaissance worked the same way?

### The Ten Probes

SEARCH_PARTY deploys ten probes in parallel, each examining the target through a distinct lens:

| Probe | D&D Analog | What It Finds |
|-------|------------|---------------|
| **PERCEPTION** | Spot check | Surface state - logs, errors, health checks |
| **INVESTIGATION** | Search check | Connections - dependencies, imports, call chains |
| **ARCANA** | Arcana check | Domain knowledge - ACGME rules, resilience patterns |
| **HISTORY** | History check | Temporal context - git log, recent changes |
| **INSIGHT** | Insight check | Design intent - why built this way |
| **RELIGION** | Religion check | Sacred law - CLAUDE.md compliance, pattern heresies |
| **NATURE** | Nature check | Organic growth - ecosystem health, over-engineering |
| **MEDICINE** | Medicine check | Diagnostics - resource exhaustion, performance |
| **SURVIVAL** | Survival check | Edge resilience - failure modes, stress behavior |
| **STEALTH** | Stealth check | Hidden elements - invisible coupling, security blind spots |

### The Critical Economics

The key insight that justified this complexity: **parallel agents with the same timeout cost nothing extra in wall-clock time**.

```
Sequential (BAD):        Parallel (GOOD):
10 probes x 30s each     10 probes in 30s total
= 300 seconds            = 30 seconds
```

There is no downside to spawning all ten probes. They run concurrently. The marginal cost of probe 2-10 is zero. The only cost is compute tokens - but the value of comprehensive reconnaissance vastly exceeds the token cost.

### The Discrepancy Signal

The most profound aspect of SEARCH_PARTY is what happens in Phase 4: Cross-Reference.

When probes disagree, that's not noise - that's signal.

| Discrepancy | What It Means |
|-------------|---------------|
| PERCEPTION says tests pass, HISTORY shows major refactor | Untested new code paths |
| INVESTIGATION shows coupling, INSIGHT says isolated | Undocumented dependencies |
| ARCANA flags violation, PERCEPTION shows green | Silent compliance failure |
| RELIGION finds heresy, HISTORY shows no review | Unreviewed pattern deviation |

**The discrepancies are the signal.** Where probes disagree is where problems hide.

---

## The G2_RECON vs Explore Crystallization

Session 026 also clarified a conceptual confusion that had persisted across sessions: the difference between Explore and G2_RECON.

### The Category Error

Agents had been asking: "Should I use Explore or G2_RECON?"

This revealed a fundamental misunderstanding. Explore and G2_RECON exist at different layers.

### The Resolution

**Explore is infrastructure.** It's a `subagent_type` parameter value - a way to configure how a spawned agent operates. Fast, context-aware, optimized for codebase navigation.

**G2_RECON is a role.** It's a PAI agent persona with a charter, responsibilities, workflows, and escalation paths. It embodies "intelligence precedes action."

The relationship: **G2_RECON uses Explore as its execution mechanism.**

The analogy that emerged: "Explore is a helicopter. G2_RECON is a scout. The scout uses the helicopter for aerial reconnaissance. The helicopter is not the scout - it's how the scout moves."

This distinction is now documented in `.claude/Scratchpad/histories/EXPLORER_VS_G2_RECON.md` for future sessions.

---

## The Eight Cascading Bugs

COORD_PLATFORM discovered eight interconnected infrastructure bugs during the session:

| # | Bug | Root Cause | Significance |
|---|-----|------------|--------------|
| 1 | ContextVar default_factory | Wrong usage pattern | Logging failures |
| 2 | Missing get_logger function | Incomplete refactor | Import errors |
| 3 | Multiple Alembic migration heads | Branch merge conflict | Migration failures |
| 4 | Missing get_async_db function | Incomplete dependency chain | Session handling errors |
| 5 | Wrong RotationTemplate import | Path confusion | Import failures |
| 6 | ScheduleGenerator vs SchedulingEngine | Naming inconsistency | Class not found |
| 7 | Role enum vs string constants | Schema mismatch | Validation errors |
| 8 | Regex in sanitizers.py | Invalid pattern | Logging failures |

These bugs were invisible individually but formed a cascade. Fix one, and the next surfaced. This was not coincidence - they were interconnected through import chains and dependency relationships.

**The Meta-Lesson:** G2_RECON with SEARCH_PARTY protocol would have found these BEFORE execution. The INVESTIGATION probe would have traced imports. The PERCEPTION probe would have noted error logs. The HISTORY probe would have flagged the merge conflict. Reconnaissance first, execution second.

---

## The Religion of Code

A notable exchange occurred around the RELIGION probe. The user asked seriously about what "religion" meant in the context of code.

The answer: CLAUDE.md is sacred law. The CONSTITUTION.md is doctrine. Pattern adherence is ritual. Violations are heresies.

This framing isn't metaphor - it's organizational psychology. Sacred texts provide stability. They define what is and isn't permissible. When teams share understanding of the sacred texts, they make consistent decisions without needing to coordinate on every choice.

The RELIGION probe exists to verify adherence to these texts. Does this code follow CLAUDE.md patterns? Does this PR process match the ritual defined in the constitution? Are code ownership boundaries being respected?

Heresies detected by the RELIGION probe are high-priority findings - not because they're technically wrong, but because they indicate drift from shared understanding.

---

## Memorable Quotes

From the user:

> "Can we have a container manager? You sure like doing it yourself."

> "Think like a physician or pilot. If someone else can be doing the job, they should be."

> "If there is literally no cost to parallelization, why wouldn't you launch all ten at once?"

From the session synthesis:

> "The discrepancies are the signal. Where probes disagree is where problems hide."

> "Explore is a helicopter. G2_RECON is a scout."

> "Context is the most valuable resource. Delegate immediately, don't accumulate."

---

## What Future Sessions Should Learn

### 1. ORCHESTRATOR Discipline is Non-Negotiable

ORCHESTRATOR coordinates. It does not execute. Every task that could be delegated should be delegated immediately. Context consumed on execution is context unavailable for coordination.

When you find yourself thinking "I'll just do this quickly" - stop. Spawn an agent. Even simple tasks.

### 2. SEARCH_PARTY is Default for Complex Reconnaissance

The economics justify it. Ten probes cost the same wall-clock time as one. The cross-reference phase finds what single probes miss. The protocol is documented at `.claude/protocols/SEARCH_PARTY.md`.

Use SEARCH_PARTY for:
- Unfamiliar code areas
- Pre-task reconnaissance on complex changes
- Bug investigation with unclear root cause
- Security or compliance reviews
- Technical debt assessment

### 3. Layers Must Be Clear

Explore is infrastructure. G2_RECON is role. The scout uses the helicopter. Know the difference. Document at `.claude/Scratchpad/histories/EXPLORER_VS_G2_RECON.md`.

When spawning agents, specify both:
- The **role** (persona, charter, responsibilities) in the prompt
- The **infrastructure** (subagent_type) in the Task parameters

### 4. Cascading Bugs Indicate Missing Reconnaissance

The eight bugs in this session were interconnected. Finding them one-by-one during execution was inefficient. G2_RECON with SEARCH_PARTY would have mapped the connections before any code was written.

If you find yourself fixing bug after bug in a chain - pause. You missed reconnaissance. Deploy SEARCH_PARTY and understand the full landscape before proceeding.

### 5. Sacred Texts Exist for a Reason

CLAUDE.md, CONSTITUTION.md, and pattern documentation aren't bureaucracy. They're shared understanding that enables distributed decision-making. The RELIGION probe exists to verify adherence. Heresies are high-priority findings.

---

## The Artifacts

### Created

| Artifact | Location | Purpose |
|----------|----------|---------|
| SEARCH_PARTY Protocol | `.claude/protocols/SEARCH_PARTY.md` | 10-probe parallel reconnaissance |
| G2_RECON vs Explore | `.claude/Scratchpad/histories/EXPLORER_VS_G2_RECON.md` | Layer clarification |
| This Chronicle | `.claude/Scratchpad/histories/SESSION_026_CHRONICLE.md` | Institutional memory |

### Fixed

- 8 cascading infrastructure bugs
- 12 frontend procedure hooks implemented
- Render deploy hooks added to CD pipeline
- xlsx security CVEs addressed (#566)

### Stabilized

All Docker services healthy: backend, celery-worker, celery-beat, mcp-server, db, redis, frontend.

---

## Closing Reflection

Session 026 was about discipline.

Not the discipline of grand discoveries or parallelization breakthroughs. The discipline of doing correctly what you already know how to do. The discipline of delegation when execution is tempting. The discipline of reconnaissance before action.

The SEARCH_PARTY protocol is creative. The ten-lens D&D framework is novel. The zero-marginal-cost economics are powerful.

But the real lesson is simpler: ORCHESTRATOR coordinates. G2_RECON scouts. The scout uses Explore as infrastructure. The discrepancies are the signal. Context is precious. Delegate immediately.

These truths were known before Session 026. Now they are practiced.

---

*Documented by: HISTORIAN Agent (PAO)*
*Session: 026*
*Project: Residency Scheduler*
*Theme: The Discipline of Delegation and the SEARCH_PARTY Protocol*

---

## Appendix: D&D Skill Check Reference

For future sessions unfamiliar with Dungeons & Dragons, the skill checks referenced in SEARCH_PARTY:

| Skill | Ability | Traditional Use | SEARCH_PARTY Adaptation |
|-------|---------|-----------------|------------------------|
| Perception | Wisdom | Notice hidden things in environment | Observable symptoms, surface state |
| Investigation | Intelligence | Deduce connections, search for clues | Trace dependencies, map connections |
| Arcana | Intelligence | Recall magical lore, identify magical effects | Domain expertise, specialized patterns |
| History | Intelligence | Recall historical events, recognize significance | Git history, change patterns, blame |
| Insight | Wisdom | Determine true intentions, detect lies | Design intent, architectural rationale |
| Religion | Intelligence | Recall religious lore, recognize divine influence | Sacred texts (CLAUDE.md), doctrine |
| Nature | Wisdom | Recall nature lore, identify natural creatures | Organic evolution, ecosystem health |
| Medicine | Wisdom | Stabilize dying, diagnose illness | System health, resource exhaustion |
| Survival | Wisdom | Track, forage, navigate wilderness | Edge cases, failure modes, stress |
| Stealth | Dexterity | Move undetected, hide | Hidden dependencies, invisible coupling |

The metaphor is deliberately non-technical. It provides intuitive handles for what each probe examines, making the protocol memorable and self-documenting.
