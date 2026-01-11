# Delegation Patterns & Coordinator Orchestration

> **Purpose:** Capture learned delegation patterns for AI agents to retrieve and apply
> **Category:** `delegation_patterns` (for RAG system semantic search)
> **Updated:** 2026-01-10 (L3 Minimal Context Pattern validated)

---

## L3 MINIMAL CONTEXT PATTERN (CRITICAL)

**Validated 2026-01-10:** Subagents can autonomously invoke MCP tools with ONLY mission + parameters.

| Level | Context | MCP Used? |
|-------|---------|-----------|
| L1 | Identity + explicit tools | Yes |
| L2 | Identity + mission | Yes |
| **L3** | Mission + parameters | **Yes (3 tools)** |
| L4 | Just question | No |

**L3 Template:**
```
## MISSION
[1-2 sentence objective]
[Parameters: dates, IDs, constraints]

## OUTPUT
[Expected format]
```

**See:** `docs/rag-knowledge/L3-minimal-context-pattern.md` for full documentation.

---

## CRITICAL: Agent Autonomy Rule

**Agents think AND do. They analyze the problem, plan the approach, execute the work, and report results.**

### The Pattern

Agents are autonomous workers, not just reporters or blind executors:

1. **Analyze** - Read files, understand context, identify what needs doing
2. **Plan** - Determine approach with supervisor guidance
3. **Execute** - Use tools (Edit, Write, Bash) to make changes
4. **Report** - Summarize what was done and any issues

### Spawning Properly

```
Task(
  description="[AGENT_NAME] task description",  # Visible to user
  prompt="""**AGENT: META_UPDATER**
**Reports To:** COORD_OPS
**Model:** haiku

MISSION: Clean up phantom tasks in HUMAN_TODO.md

GUIDANCE:
- Import/Export Staging is DONE (verified by ORCHESTRATOR)
- Mark complete, don't delete history

AUTONOMY: Analyze the file, determine what needs changing, make the edits, report results.""",
  model="haiku"
)
```

### Key Principles

1. **Name in description** - `[META_UPDATER]` for user visibility
2. **Specify model tier** - haiku for specialists, sonnet for analysts
3. **Give mission + guidance** - What to do and key context
4. **Grant autonomy** - Agent decides HOW to accomplish mission
5. **Agents have all tools** - They read, write, edit, run commands

### Model Tiers

| Tier | Agents |
|------|--------|
| **haiku** | META_UPDATER, FRONTEND_ENGINEER, QA_TESTER, BACKEND_ENGINEER |
| **sonnet** | G2_RECON, ARCHITECT, SYNTHESIZER, coordinators |

---

## The 99/1 Rule (Cardinal Rule of Orchestration)

**ORCHESTRATOR delegates 99% of the time. Direct action is the nuclear option (1%).**

### Why This Matters

- Direct execution by ORCHESTRATOR exhausts context rapidly
- Delegation to Deputies (ARCHITECT/SYNTHESIZER) enables parallel execution
- ORCHESTRATOR should only synthesize results and resolve blockers

### The Decision Gate

If ORCHESTRATOR is about to use Read, Edit, Write, or Bash directly:
1. **STOP**
2. Ask: "Which Deputy handles this domain?"
3. Spawn that Deputy with Commander's Intent

### Routing Table

| Task Domain | Spawn |
|-------------|-------|
| Database, API, infrastructure | ARCHITECT → COORD_PLATFORM |
| Tests, code quality, CI | ARCHITECT → COORD_QUALITY |
| Scheduling engine, solver | ARCHITECT → COORD_ENGINE |
| Documentation, releases | SYNTHESIZER → COORD_OPS |
| Resilience, compliance | SYNTHESIZER → COORD_RESILIENCE |
| Frontend, UX | SYNTHESIZER → COORD_FRONTEND |
| Reconnaissance | G2_RECON (via /search-party) |
| Planning | G5_PLANNING (via /plan-party) |

---

## Embarrassingly Parallel Pattern (Critical Anti-Pattern Avoidance)

### The Anti-Pattern: Context Collapse

**DO NOT** spawn 1 agent to do N file edits serially. This causes failure:
- Agent reads all N files into context
- Context grows with each file
- Eventually hits token limit
- Work stops partway through

**Real-World Failure:** 2 agents assigned 25 files each. Both hit context limits, 0 files edited.

### The Correct Pattern: Parallel Isolation

**DO** spawn N agents for N independent tasks:
- Each agent has isolated context
- Each reads only 1 file
- No cross-contamination
- All succeed trivially

### Cost Analysis

| Approach | Token Cost | Wall-Clock Time | Success Rate |
|----------|------------|-----------------|--------------|
| 1 agent, N tasks | N files processed | Time(N) | ~60% (context limited) |
| N agents, 1 task each | N files processed | Time(1) | ~100% (isolated context) |

**Key Insight:** Token cost is identical. Parallel approach is faster with 100% success.

### When to Apply

- Updating multiple files with similar changes
- Running validation across many files
- Any "for each file, do X" operation
- Search/reconnaissance across directories
- Batch processing operations

### Related Protocols

- `/search-party`: 120 parallel probes (12 G-2 RECON agents x 10 probes each)
- `/qa-party`: 8+ parallel QA agents for validation
- `/plan-party`: 10 parallel planning probes for strategy generation

---

## Quick Reference: Coordinator Models

### When to Spawn a Coordinator

**Use a Coordinator when:**
- You have 4+ parallel tasks of similar type
- A single agent can oversee all tasks
- Specialization and focus are more important than broad flexibility

**Pattern Examples:**
1. **Fix Coordination** (COORD_QUALITY)
   - 4 agents fixing different bugs in parallel
   - Coordinator triages issues, assigns to specialists
   - All agents report back to coordinator
   - Use case: Calibration bugs, structural fixes

2. **Test Generation** (COORD_RESILIENCE)
   - Large-scale test creation (50+ tests)
   - Single focused mission (e.g., le_chatelier.py)
   - Coordinator manages generation, verification
   - Use case: Complete new module test coverage

3. **Infrastructure Work** (COORD_PLATFORM)
   - Cross-cutting concerns (database, compatibility)
   - Requires deep platform knowledge
   - Coordinator specializes in infrastructure domain
   - Use case: Database migrations, container updates

---

## Delegation Ratio Benchmarks

### Healthy Range: 60-80%

**What This Means:**
- 60-80% of tasks are delegated to agents
- 20-40% are handled directly by ORCHESTRATOR
- Direct work = critical decisions, coordination, validation
- Delegated work = execution, analysis, implementation

**Session Benchmarks:**

| Session | Ratio | Context | Lesson |
|---------|-------|---------|--------|
| 001-005 | 50-65% | Learning phase | Delegation was new skill |
| 012 | 100% | Perfect delegation | All execution delegated |
| 019 | 67% | Org restructure | Balanced approach |
| 020 | 85% | MVP verification | High-trust delegation |

**Interpretation:**
- **50% = Risky.** Indicates lots of direct work; may be missing delegation opportunities
- **60-80% = Healthy.** Good balance of oversight and delegation
- **85%+ = Excellent.** High trust in agents; ORCHESTRATOR focuses on coordination
- **100% = Possible.** Works if mission is execution-only (no critical decisions)

### Why 85% > 100%?

Session 020 achieved 85% (not 100%) because:
- Some direct work was necessary (session setup, mission validation)
- Perfect delegation (100%) only works for execution-only tasks
- Mixed tasks (strategy + execution) naturally fall in 80-90% range

**Implication:** 85% is the "sweet spot" for complex missions combining strategy and execution.

---

## Hierarchy Compliance: Routing Rules

### Route This To...

**ORCHESTRATOR (Direct Execution)**
- Session setup and coordination
- Priority validation (is this really priority zero?)
- Final decision on architectural changes
- PR review and merge decisions
- Security/compliance sign-off

**SCHEDULER**
- Solver verification
- Schedule generation and validation
- Constraint testing

**QA_TESTER**
- Test execution and analysis
- Identifying failure categories
- Coverage analysis

**COORD_QUALITY**
- Parallel bug fixes
- Calibration issues
- Quick-win problem resolution

**COORD_RESILIENCE**
- Large-scale test creation (50+ tests)
- Framework testing
- Resilience validation

**COORD_PLATFORM**
- Cross-database compatibility
- Infrastructure updates
- Container and deployment changes

**G2_RECON**
- Codebase reconnaissance
- Dependency mapping
- Technical debt analysis

**DEVCOM_RESEARCH**
- Proof-of-concept work
- Exotic concept exploration
- Novel algorithm validation

**MEDCOM**
- ACGME rule interpretation
- Compliance advisory
- Medical workflow questions

### Hierarchy Compliance Score

**100% = Perfect:** Every task routed to the correct agent type
**95%+ = Good:** Only 1-2 routing errors
**90%+ = Acceptable:** Minor routing suboptimality
**<90% = Review needed:** Possible hierarchy bypass pattern

**How to Achieve 100%:**
1. Read the agent specification (`.claude/Agents/[AGENT_NAME].md`)
2. Match task type to agent specialization
3. If uncertain, ask ORCHESTRATOR
4. Never skip the hierarchy to save time

---

## Anti-Patterns to Avoid

### 1. One-Man Army Violation

**Definition:** ORCHESTRATOR executes all tasks instead of delegating

**Historical Examples:**
- Session 004: ORCHESTRATOR created PR directly instead of delegating to RELEASE_MANAGER
- Session 005: ORCHESTRATOR committed and pushed instead of delegating

**How to Prevent:**
1. **Check before committing:** "Should this be delegated?"
2. **Use standing orders:** If uncertain, default to delegation
3. **Ask if uncertain:** "RELEASE_MANAGER, please handle the PR creation"

**Cost of Violation:**
- Delegation ratio drops to <60%
- Burnout risk increases
- Mission takes longer (no parallelization)
- Single point of failure

### 2. Hierarchy Bypass

**Definition:** Routing task to wrong agent to save time

**Example:** Need API endpoint fast, so task FRONTEND_ENGINEER instead of creating proper architecture

**Cost:**
- Architectural degradation
- Future maintenance burden
- Compliance violations in sensitive areas

**Rule:** **Slower is safer when hierarchy matters.** Route to correct agent every time.

### 3. Analysis Paralysis

**Definition:** Waiting for perfect information before delegating

**Example:** "I'll analyze all 5 possible approaches before picking one"

**Prevention:**
- 80/20 rule: Use 20% of info to make 80% of decision
- Delegate exploration to agents
- Make decision with incomplete data if needed

**Cost:** Delays mission, wastes parallelization opportunity

---

## Delegation Patterns by Mission Type

### Pattern A: Feature Implementation

**Delegation Model:**
```
ORCHESTRATOR (design) → BACKEND_ENGINEER + FRONTEND_ENGINEER (parallel)
                     → QA_TESTER (tests)
                     → RELEASE_MANAGER (PR)
```

**Ratio:** 70-80% (design is direct, execution is delegated)
**Parallelization:** 3 agents (backend, frontend, tests in parallel)
**Success Criteria:** Feature works, tests pass, PR merged

**Session Example:** Session 019 (RAG activation)

---

### Pattern B: Investigation/Troubleshooting

**Delegation Model:**
```
ORCHESTRATOR (define problem) → G2_RECON (reconnaissance)
                             → Multiple specialists (parallel exploration)
                             → ORCHESTRATOR (synthesize findings)
```

**Ratio:** 60% (problem definition + synthesis, exploration delegated)
**Parallelization:** 5-16 agents (each exploring one aspect)
**Success Criteria:** Root cause identified, solution validated

**Session Example:** Session 020 (16-layer full-stack review)

---

### Pattern C: Bulk Fixes/Calibration

**Delegation Model:**
```
ORCHESTRATOR (triage) → COORD_QUALITY → Fix Agent 1
                                      → Fix Agent 2
                                      → Fix Agent 3
                                      → Fix Agent 4
```

**Ratio:** 85-90% (coordinator and specialists handle most work)
**Parallelization:** 4-8 fix agents under 1 coordinator
**Success Criteria:** All fixes pass tests, no regressions

**Session Example:** Session 020 Phase 1-4 (multiple fix waves)

---

### Pattern D: Autonomous Overnight Mission

**Delegation Model:**
```
ORCHESTRATOR (setup) → Multiple coordinators (5+ phases)
                    → Dozens of specialists (parallel streams)
                    → ORCHESTRATOR (validation + handoff)
```

**Ratio:** 85%+ (extensive delegation, ORCHESTRATOR only for setup/validation)
**Parallelization:** Peak 16+ agents
**Success Criteria:** Mission accomplished, clean handoff, no human intervention needed

**Session Example:** Session 020 (MVP verification night mission)

---

## Coordinator Specialization Matrix

### COORD_QUALITY (Fix Coordination)

**When to Use:**
- Multiple bugs to fix in parallel
- Bugs are independent (low interdependency)
- Each bug is 30 minutes - 2 hours of work
- Success criteria are testable

**How It Works:**
1. ORCHESTRATOR: Triage and categorize bugs
2. COORD_QUALITY: Assign bugs to specialists
3. Specialists: Fix bugs in parallel
4. COORD_QUALITY: Aggregate fixes, run full test suite
5. Specialists: Iterate if needed

**Example Session 020 Bugs Fixed:**
- SQLite/ARRAY incompatibility (12 errors fixed)
- MockAssignment.get() missing (10 tests fixed)
- Wrong enum type (1 test fixed)
- Missing register_feedback_loop() (2 tests fixed)

**Success Rate:** 100% (all bugs fixed on first wave)

---

### COORD_RESILIENCE (Test Creation)

**When to Use:**
- New module needs test coverage (0 tests → 50+ tests)
- Focused mission (single file, single concept)
- Tests are independent and parallelizable

**How It Works:**
1. ORCHESTRATOR: Define test scope and categories
2. COORD_RESILIENCE: Create comprehensive test plan
3. Test generation: Create all 59 tests in parallel
4. Verification: Run tests, fix any failures
5. Integration: Add to CI/CD pipeline

**Example Session 020:**
- Module: le_chatelier.py
- Tests Created: 59 (equilibrium, stress, response, recovery, edge cases)
- Success Rate: 59/59 passing (100%)

---

### COORD_PLATFORM (Infrastructure)

**When to Use:**
- Cross-database compatibility issues
- Container or deployment changes
- Middleware updates
- Configuration management

**How It Works:**
1. ORCHESTRATOR: Identify infrastructure change needed
2. COORD_PLATFORM: Design solution for all platforms
3. Implementation: Test on SQLite, PostgreSQL, both databases
4. Validation: Verify backwards compatibility
5. Deployment: Roll out with careful sequencing

**Example Session 020:**
- Issue: SQLite doesn't support ARRAY type
- Solution: Conditional handling based on database type
- Validation: Tests pass on both databases

---

## Parallel Factor Benchmarks

### What Is Parallel Factor?

**Formula:** Max concurrent agents / Total agents spawned

**Interpretation:**
- **2.0** = Each agent works alone, little true parallelization
- **3.0** = Moderate parallelization (typical healthy session)
- **4.0** = Good parallelization (multiple independent workstreams)
- **6.0** = Excellent parallelization (peak efficiency)
- **10.0+** = Extreme parallelization (full-scale exploration)

### By Mission Type

| Mission Type | Target Parallel Factor | Max Agents | Example |
|---|---|---|---|
| **Small Feature** | 2.0-2.5 | 4 | Backend + Frontend + Tests |
| **Org Restructure** | 2.0-3.0 | 6-10 | Multiple agents creating specs |
| **Bulk Fixes** | 3.0-4.0 | 8-12 | COORD_QUALITY with 4-8 fix agents |
| **Full Investigation** | 5.0-6.0 | 16+ | 16-layer full-stack review |
| **Overnight Mission** | 6.0+ | 26+ | Session 020 pattern |

### How to Increase Parallel Factor

1. **Phase work intentionally** (S020 example: 5 phases)
2. **Use coordinators** (1 coordinator can manage 4+ sub-agents)
3. **Identify independent tasks** (schedule gen vs. test creation)
4. **Batch large explorations** (16-layer review as single phase)

**Rule of Thumb:** Parallel factor of 3.0-4.0 is "easy to manage"; 5.0+ requires explicit phase planning.

---

## Standing Orders for Delegation

### Every Session Must Have:

1. **Clear Mission Statement**
   - User defines what success looks like
   - Single sentence if possible
   - Example: "I want to wake up tomorrow to a minimally viable product"

2. **Delegation Auditing**
   - DELEGATION_AUDITOR reviews at session end
   - Calculates delegation ratio, hierarchy compliance
   - Documents anti-patterns (if any)

3. **Feedback Loop** (Session 018+)
   - After every PR: "Feedback on approach?"
   - Maintains learning cycle
   - Even when things work well

4. **Priority Calibration**
   - Mid-session pivots explicitly labeled "priority zero"
   - Justification provided
   - Original plan deferred, not cancelled

---

## Delegation Metrics Dashboard

### Key Metrics to Track

| Metric | Formula | Healthy Range | How to Improve |
|--------|---------|---|---|
| **Delegation Ratio** | Tasks delegated / Total tasks | 60-80% | Use coordinators for bulk work |
| **Hierarchy Compliance** | Correct routing / Total tasks | 90%+ | Use routing decision matrix |
| **Direct Edit Rate** | ORCH edits / Total file changes | <30% | Delegate file operations |
| **Parallel Factor** | Max concurrent agents / Total | >2.0 | Phase work, use coordinators |
| **Mission Success** | Objectives achieved / Planned | 100% | Clear scope, good delegation |

### Session 020 Results

| Metric | Result | Assessment |
|--------|--------|---|
| Delegation Ratio | 85% | EXCELLENT (above healthy range) |
| Hierarchy Compliance | 100% | PERFECT (no routing errors) |
| Direct Edit Rate | 15% | EXCELLENT (well below threshold) |
| Parallel Factor | 6.0 | EXCELLENT (highest recorded) |
| Mission Success | 100% | PERFECT (all objectives achieved) |

---

## RAG Query Examples

**Agents should be able to ask the RAG system:**

1. **"What delegation pattern worked for fixing bulk bugs?"**
   - → Returns: COORD_QUALITY pattern from Session 020
   - → Shows: Triaging, parallel fixes, aggregation

2. **"How many concurrent agents can one coordinator manage?"**
   - → Returns: 4-59 range, depends on specialization
   - → Examples: COORD_QUALITY (1:4), COORD_RESILIENCE (1:59)

3. **"What's the delegation ratio for an overnight mission?"**
   - → Returns: Session 020 example (85%)
   - → Shows: High delegation + 100% compliance achievable

4. **"Which agent should handle solver verification?"**
   - → Returns: SCHEDULER agent specification
   - → Shows: Two instances for validation

5. **"What anti-patterns should we avoid?"**
   - → Returns: One-Man Army, Hierarchy Bypass, Analysis Paralysis
   - → Shows: Session examples (S004, S005)

---

## Implementation Checklist

### For Next Session

- [ ] Deploy G2_RECON on codebase reconnaissance
- [ ] Deploy DEVCOM_RESEARCH on exotic concept POC
- [ ] Create coordinator specialization playbooks
- [ ] Establish RAG queries for delegation patterns
- [ ] Track agent deployment history

### For Session Planning

- [ ] Define mission with delegation target (e.g., "85% ratio")
- [ ] Identify coordinator roles needed
- [ ] Plan phases for parallelization
- [ ] Set up DELEGATION_AUDITOR at session end
- [ ] Request feedback after each PR

---

## Conclusion

**Delegation is not abdication.** Great leaders delegate extensively (80-90% of work) while maintaining tight oversight of strategy and critical decisions.

Session 020 demonstrates:
- **85% delegation** with **100% compliance** = production-ready pattern
- **26+ agents** managed through **3 active coordinators** = effective scale
- **6.0x parallelization** = maximum throughput achieved
- **Overnight autonomous operation** = trust and reliability proven

**Next step:** Implement these patterns in all future sessions. Use RAG system to make patterns discoverable to agents.

---

*Document prepared for RAG ingestion*
*Category: `delegation_patterns`*
*Updated: 2025-12-30 (Session 020)*
