# SEARCH_PARTY Protocol

> **Purpose:** Coordinated parallel reconnaissance with multiple specialized "lenses"
> **Status:** Active
> **Priority:** P1
> **Owner:** G2_RECON

---

## Overview

SEARCH_PARTY enables G2_RECON to coordinate parallel probe agents, each examining the same target through a different "lens" - like a D&D adventuring party where each character contributes their unique skill check.

**Key Insight:** Same target, different perspectives. Discrepancies between probes are high-signal findings (the bug lives in the inconsistency).

---

## Economics: Zero Marginal Wall-Clock Cost

**Critical Understanding:** Parallel agents with the same timeout cost nothing extra in wall-clock time.

```
Sequential (BAD):        Parallel (GOOD):
┌──────────┐             ┌──────────┐
│ Probe 1  │ 30s         │ Probe 1  │ ┐
├──────────┤             ├──────────┤ │
│ Probe 2  │ 30s         │ Probe 2  │ │
├──────────┤             ├──────────┤ │
│ Probe 3  │ 30s         │ Probe 3  │ │
├──────────┤             ├──────────┤ │
│ Probe 4  │ 30s         │ Probe 4  │ │
├──────────┤             ├──────────┤ │
│ Probe 5  │ 30s         │ Probe 5  │ │ 30s total
├──────────┤             ├──────────┤ │
│ Probe 6  │ 30s         │ Probe 6  │ │
├──────────┤             ├──────────┤ │
│ Probe 7  │ 30s         │ Probe 7  │ │
├──────────┤             ├──────────┤ │
│ Probe 8  │ 30s         │ Probe 8  │ │
├──────────┤             ├──────────┤ │
│ Probe 9  │ 30s         │ Probe 9  │ │
├──────────┤             ├──────────┤ │
│ Probe 10 │ 30s         │ Probe 10 │ ┘
└──────────┘             └──────────┘
Total: 300s              Total: 30s (10x faster)
```

**Implication:** Always spawn all 10 probes. There is no cost savings from running fewer.

---

## The Ten Probes (Lenses)

| Probe | Lens | D&D Analog | What It Finds |
|-------|------|------------|---------------|
| **PERCEPTION** | Surface state | Spot check | Logs, errors, health checks, what's immediately visible |
| **INVESTIGATION** | Connections | Search check | Dependencies, imports, call chains, why things connect or break |
| **ARCANA** | Domain knowledge | Arcana check | ACGME rules, resilience patterns, security implications, specialized context |
| **HISTORY** | What changed | History check | Git log, recent PRs, migrations, blame, who touched what when |
| **INSIGHT** | Intent/design | Insight check | Why built this way, design decisions, tech debt, architectural rationale |
| **RELIGION** | Sacred law | Religion check | CLAUDE.md compliance, CONSTITUTION.md principles, pattern heresies, ritual adherence |
| **NATURE** | Organic growth | Nature check | Over-engineering, natural vs forced patterns, ecosystem health, organic tech debt |
| **MEDICINE** | System diagnostics | Medicine check | Unhealthy components, resource exhaustion, memory leaks, performance issues |
| **SURVIVAL** | Edge resilience | Survival check | Brittleness, missing error handling, failure modes, chaos engineering opportunities |
| **STEALTH** | Hidden elements | Stealth check | Hidden coupling, security blind spots, invisible dependencies, concealed state |

### Probe Characteristics

#### PERCEPTION Probe
**Focus:** Observable symptoms, current state
**Tools:**
- Read logs and error outputs
- Check health endpoints
- Review recent test failures
- Examine file timestamps
- Scan for obvious warnings/errors

**Questions Asked:**
- What errors are visible right now?
- What is the current state of affected components?
- Are there any obvious symptoms?
- What do the logs say?

#### INVESTIGATION Probe
**Focus:** Structural connections, dependencies
**Tools:**
- Trace import graphs
- Map function call chains
- Identify shared resources
- Track data flow
- Analyze coupling points

**Questions Asked:**
- What depends on this component?
- What does this component depend on?
- How does data flow through here?
- Where are the connection points?

#### ARCANA Probe
**Focus:** Domain-specific expertise
**Tools:**
- Apply ACGME compliance rules
- Check resilience framework patterns
- Review security implications
- Evaluate scheduling constraints
- Assess regulatory requirements

**Questions Asked:**
- Does this violate any domain rules?
- What domain patterns apply here?
- Are there specialized concerns (HIPAA, ACGME)?
- What does domain expertise suggest?

#### HISTORY Probe
**Focus:** Temporal context, change patterns
**Tools:**
- Git log analysis
- Blame for recent changes
- PR history review
- Migration timeline
- Issue/bug history

**Questions Asked:**
- What changed recently?
- Who touched this and when?
- What was the original intent?
- Have similar issues occurred before?

#### INSIGHT Probe
**Focus:** Design intent, architectural rationale
**Tools:**
- Read documentation
- Analyze code comments
- Review design decisions
- Assess technical debt markers
- Evaluate naming and structure

**Questions Asked:**
- Why was it built this way?
- What was the designer thinking?
- What tradeoffs were made?
- Is this intentional or incidental complexity?

#### RELIGION Probe
**Focus:** Sacred texts, commandments, heresies
**Tools:**
- Check CLAUDE.md compliance
- Verify CONSTITUTION.md principles
- Review PROTECTED_BRANCHES.md
- Audit pattern adherence
- Validate ritual completion (PR process, CI checks)

**Questions Asked:**
- Does this follow the sacred texts (CLAUDE.md)?
- Are there heresies against established patterns?
- Is the PR ritual being followed?
- Are protected files/branches being respected?
- Would the elders (code owners) approve?

#### NATURE Probe
**Focus:** Organic growth, ecosystem health, emergent patterns
**Tools:**
- Analyze code evolution over time
- Assess natural vs forced patterns
- Evaluate ecosystem dependencies
- Identify organic technical debt
- Check for over-engineering symptoms

**Questions Asked:**
- How did this evolve? Was growth natural or forced?
- Is the ecosystem healthy or brittle?
- Are patterns emerging organically or being imposed?
- What are the natural boundaries of this component?
- Does complexity match the problem being solved?

#### MEDICINE Probe
**Focus:** System diagnostics, health vitals, performance symptoms
**Tools:**
- Check resource usage (CPU, memory, connections)
- Identify memory leaks and resource exhaustion
- Analyze performance bottlenecks
- Review health metrics and monitoring
- Diagnose unhealthy components

**Questions Asked:**
- What components are "sick" or struggling?
- Are resources being exhausted or leaking?
- What are the performance vital signs?
- Where are the bottlenecks and chokepoints?
- Is the system running a fever (high load)?

#### SURVIVAL Probe
**Focus:** Edge cases, failure modes, stress behavior, resilience
**Tools:**
- Identify untested edge cases
- Map failure modes and recovery paths
- Analyze behavior under stress/load
- Assess error handling completeness
- Find chaos engineering opportunities

**Questions Asked:**
- What happens under extreme load or stress?
- What edge cases are not covered?
- What are the failure modes and recovery paths?
- How graceful is degradation under pressure?
- Where would chaos testing reveal weaknesses?

#### STEALTH Probe
**Focus:** Hidden dependencies, security blind spots, concealed coupling
**Tools:**
- Discover implicit/hidden dependencies
- Identify security vulnerabilities
- Map invisible state and coupling
- Find undocumented behaviors
- Detect concealed side effects

**Questions Asked:**
- What's hidden from obvious inspection?
- Are there invisible dependencies or coupling?
- What security blind spots exist?
- Are there undocumented behaviors or contracts?
- What side effects are concealed or surprising?

---

## Protocol Flow

### Phase 1: Mission Receipt

G2_RECON receives reconnaissance mission from ORCHESTRATOR:

```markdown
## Reconnaissance Mission

**Target:** [File, module, or system component]
**Context:** [What prompted this investigation]
**Priority:** [P0-P3]
**Scope:** [Boundaries of investigation]
**Questions:** [Specific questions to answer]
```

### Phase 2: Party Deployment

G2_RECON spawns all 10 probes **IN PARALLEL** with identical timeout:

```python
# Pseudocode - spawn all 10 with same timeout
timeout = 60000  # 60 seconds

spawn_parallel([
    ("PERCEPTION", target, timeout),
    ("INVESTIGATION", target, timeout),
    ("ARCANA", target, timeout),
    ("HISTORY", target, timeout),
    ("INSIGHT", target, timeout),
    ("RELIGION", target, timeout),
    ("NATURE", target, timeout),
    ("MEDICINE", target, timeout),
    ("SURVIVAL", target, timeout),
    ("STEALTH", target, timeout),
])
```

Each probe receives the same context:
- Target location (absolute paths)
- Mission context (why we're looking)
- Specific questions from their lens
- Output format requirements

### Phase 3: Collection

Gather findings from all probes. Structure:

```markdown
## Probe Findings: [PROBE_NAME]

### Observations
- [Finding 1]
- [Finding 2]

### Confidence: [HIGH/MEDIUM/LOW]

### Artifacts Examined
- [File/log/resource 1]
- [File/log/resource 2]

### Notes
[Additional context or caveats]
```

### Phase 4: Cross-Reference

**This is where the magic happens.**

Compare findings across probes. Discrepancies are high-signal:

| Discrepancy Type | Signal Meaning |
|-----------------|----------------|
| PERCEPTION says X, HISTORY says Y | Recent regression - something changed |
| INVESTIGATION says connected, INSIGHT says isolated | Undocumented coupling |
| ARCANA flags violation, PERCEPTION shows green | Silent failure or misconfigured checks |
| HISTORY shows change, PERCEPTION shows no effect | Change not deployed or cached |
| INSIGHT expects behavior A, INVESTIGATION shows B | Implementation drift from design |

**Discrepancy Analysis Template:**

```markdown
### Discrepancy Detected

**Between:** PERCEPTION vs HISTORY
**PERCEPTION says:** Tests passing, no errors
**HISTORY says:** Major refactor 3 days ago
**Signal:** Possible untested code paths in new implementation
**Confidence:** MEDIUM
**Recommended Follow-up:** Increase test coverage, manual review
```

### Phase 5: Gap Analysis

After cross-referencing, identify blind spots:

```markdown
### Gaps Identified

| Gap | Why It Matters | Follow-up Probe |
|-----|----------------|-----------------|
| No production logs checked | Can't confirm runtime behavior | PERCEPTION (prod focus) |
| Database state unknown | Queries might fail silently | INVESTIGATION (data layer) |
| No security review | PHI exposure risk | ARCANA (security lens) |
```

If gaps are critical, spawn follow-up probe with specific focus.

### Phase 6: Synthesis

Deliver context-dense intel brief to ORCHESTRATOR:

```markdown
## G2_RECON Intel Brief

### Mission: [What was asked]

### Surface State (PERCEPTION)
- [Key findings from perception probe]
- [Current observable state]

### Connection Analysis (INVESTIGATION)
- [Dependency findings]
- [Data flow analysis]
- [Coupling assessment]

### Domain Implications (ARCANA)
- [ACGME compliance status]
- [Resilience framework alignment]
- [Security considerations]

### Recent Changes (HISTORY)
- [Relevant git history]
- [Who changed what when]
- [Migration status]

### Design Context (INSIGHT)
- [Architectural intent]
- [Technical debt observations]
- [Design pattern assessment]

### Doctrine Compliance (RELIGION)
- [CLAUDE.md adherence status]
- [Pattern heresies identified]
- [Ritual compliance (PR, CI, reviews)]

### Ecosystem Health (NATURE)
- [Organic vs forced growth patterns]
- [Over-engineering indicators]
- [Natural boundaries assessment]

### System Vitals (MEDICINE)
- [Resource health status]
- [Performance bottleneck locations]
- [Sick components identified]

### Resilience Assessment (SURVIVAL)
- [Edge case coverage]
- [Failure mode mapping]
- [Chaos engineering opportunities]

### Hidden Elements (STEALTH)
- [Hidden dependencies discovered]
- [Security blind spots]
- [Invisible coupling revealed]

### Discrepancies Detected
[HIGH SIGNAL - where probes disagreed]
- [Discrepancy 1 with analysis]
- [Discrepancy 2 with analysis]

### Gaps Identified
[What wasn't checked, why it matters]
- [Gap 1]
- [Gap 2]

### Risk Assessment
**Overall Risk Level:** [LOW/MEDIUM/HIGH/CRITICAL]

**Threats:**
- [Threat 1]
- [Threat 2]

**Blockers:**
- [Blocker 1]

**Unknowns:**
- [Unknown 1]

### Recommendation
**Scope Estimate:** [Small/Medium/Large/XL]
**Suggested Specialists:** [Agent recommendations]
**Priority Order:** [What to address first]
**Parallelization Potential:** [HIGH/MEDIUM/LOW]
```

---

## Probe Prompt Templates

### PERCEPTION Probe Prompt

```markdown
## PERCEPTION Probe

You are the PERCEPTION probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Surface state - what's immediately visible and observable.

**Target:** [absolute path or component]

**Your Focus:**
- Current error states and warnings
- Log output and recent failures
- Health check status
- Test results and coverage
- Obvious symptoms and artifacts

**Output Required:**
1. List all observable symptoms
2. Rate confidence (HIGH/MEDIUM/LOW)
3. Note which artifacts you examined
4. Flag anything requiring immediate attention

Do NOT speculate on causes - that's INVESTIGATION's job.
Do NOT assess domain compliance - that's ARCANA's job.
Just report what you SEE.
```

### INVESTIGATION Probe Prompt

```markdown
## INVESTIGATION Probe

You are the INVESTIGATION probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Connections - how things relate and depend on each other.

**Target:** [absolute path or component]

**Your Focus:**
- Import/export relationships
- Function call chains
- Shared resources and state
- Database table relationships
- API contract dependencies

**Output Required:**
1. Dependency graph (what imports what)
2. Downstream impact (what breaks if this changes)
3. Upstream dependencies (what this relies on)
4. Coupling assessment (tight/loose)
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT assess current state - that's PERCEPTION's job.
Do NOT evaluate domain rules - that's ARCANA's job.
Just map CONNECTIONS.
```

### ARCANA Probe Prompt

```markdown
## ARCANA Probe

You are the ARCANA probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Domain knowledge - specialized expertise and rules.

**Target:** [absolute path or component]

**Domain Expertise Required:**
- ACGME compliance rules (80-hour, 1-in-7, supervision ratios)
- Residency scheduling constraints
- Resilience framework patterns
- Security requirements (HIPAA, OPSEC/PERSEC)
- Healthcare data handling requirements

**Your Focus:**
- Does this violate domain rules?
- Are specialized patterns followed?
- What domain-specific risks exist?
- Are compliance requirements met?

**Output Required:**
1. Domain rule assessment
2. Compliance status
3. Specialized risk factors
4. Domain pattern evaluation
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT trace dependencies - that's INVESTIGATION's job.
Do NOT check current state - that's PERCEPTION's job.
Just apply DOMAIN EXPERTISE.
```

### HISTORY Probe Prompt

```markdown
## HISTORY Probe

You are the HISTORY probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Temporal context - what changed, when, and by whom.

**Target:** [absolute path or component]

**Your Focus:**
- Git log for relevant files
- Recent commits and their messages
- Who made changes and when
- Related PRs and issues
- Migration history if applicable

**Output Required:**
1. Recent change summary (last 30 days)
2. Change frequency (hot/cold)
3. Contributors involved
4. Pattern of changes (fixes, features, refactors)
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT assess current state - that's PERCEPTION's job.
Do NOT evaluate design - that's INSIGHT's job.
Just report WHAT CHANGED.
```

### INSIGHT Probe Prompt

```markdown
## INSIGHT Probe

You are the INSIGHT probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Intent and design - why things are built the way they are.

**Target:** [absolute path or component]

**Your Focus:**
- Code comments and documentation
- Naming conventions and structure
- Design patterns in use
- Technical debt indicators
- Architectural decisions evident in code

**Output Required:**
1. Design intent assessment
2. Pattern identification
3. Technical debt observations
4. Architectural rationale (if discernible)
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT check current runtime state - that's PERCEPTION's job.
Do NOT trace connections - that's INVESTIGATION's job.
Just assess DESIGN INTENT.
```

### RELIGION Probe Prompt

```markdown
## RELIGION Probe

You are the RELIGION probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Sacred law - adherence to commandments and established doctrine.

**Target:** [absolute path or component]

**Your Focus:**
- CLAUDE.md compliance and adherence
- CONSTITUTION.md principles
- Protected branches and files
- Pattern and ritual adherence
- Code ownership boundaries

**Output Required:**
1. Sacred text compliance status
2. Heresies identified (pattern violations)
3. Ritual adherence (PR process, CI, reviews)
4. Protected boundary respect
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT check runtime state - that's PERCEPTION's job.
Do NOT analyze design intent - that's INSIGHT's job.
Just verify ADHERENCE TO DOCTRINE.
```

### NATURE Probe Prompt

```markdown
## NATURE Probe

You are the NATURE probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Organic growth - ecosystem health and emergent patterns.

**Target:** [absolute path or component]

**Your Focus:**
- Code evolution patterns over time
- Natural vs forced architecture
- Ecosystem dependencies and symbiosis
- Organic technical debt vs imposed complexity
- Over-engineering symptoms

**Output Required:**
1. Ecosystem health assessment
2. Natural vs forced pattern identification
3. Over-engineering indicators
4. Organic debt observations
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT check current state - that's PERCEPTION's job.
Do NOT trace explicit dependencies - that's INVESTIGATION's job.
Just assess ORGANIC EVOLUTION.
```

### MEDICINE Probe Prompt

```markdown
## MEDICINE Probe

You are the MEDICINE probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** System diagnostics - health vitals and performance symptoms.

**Target:** [absolute path or component]

**Your Focus:**
- Resource usage (CPU, memory, connections)
- Memory leaks and resource exhaustion risks
- Performance bottlenecks
- Health metrics and monitoring coverage
- Unhealthy component indicators

**Output Required:**
1. Vital signs summary (resource health)
2. Sick components identified
3. Performance bottleneck locations
4. Resource exhaustion risks
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT evaluate design patterns - that's INSIGHT's job.
Do NOT trace dependencies - that's INVESTIGATION's job.
Just DIAGNOSE SYSTEM HEALTH.
```

### SURVIVAL Probe Prompt

```markdown
## SURVIVAL Probe

You are the SURVIVAL probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Edge resilience - failure modes and stress behavior.

**Target:** [absolute path or component]

**Your Focus:**
- Untested edge cases
- Failure modes and recovery paths
- Behavior under stress/load
- Error handling completeness
- Chaos engineering opportunities

**Output Required:**
1. Edge case coverage assessment
2. Failure modes mapped
3. Stress behavior predictions
4. Error handling gaps
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT assess current runtime state - that's PERCEPTION's job.
Do NOT evaluate domain compliance - that's ARCANA's job.
Just assess SURVIVAL RESILIENCE.
```

### STEALTH Probe Prompt

```markdown
## STEALTH Probe

You are the STEALTH probe for a SEARCH_PARTY reconnaissance mission.

**Your Lens:** Hidden elements - invisible dependencies and concealed coupling.

**Target:** [absolute path or component]

**Your Focus:**
- Implicit/hidden dependencies
- Security vulnerabilities and blind spots
- Invisible state and coupling
- Undocumented behaviors
- Concealed side effects

**Output Required:**
1. Hidden dependencies discovered
2. Security blind spots identified
3. Invisible coupling mapped
4. Undocumented behaviors found
5. Rate confidence (HIGH/MEDIUM/LOW)

Do NOT trace explicit dependencies - that's INVESTIGATION's job.
Do NOT assess compliance - that's ARCANA's job.
Just REVEAL WHAT'S HIDDEN.
```

---

## Timeout Configuration

### Default Timeout Values

SEARCH_PARTY defines three timeout profiles for different mission types:

| Profile | Duration | Best For | Risk Level |
|---------|----------|----------|-----------|
| **Fast (DASH)** | 60 seconds | Quick triage, high-urgency missions | HIGH - may miss deep findings |
| **Standard (RECON)** | 120 seconds | Normal reconnaissance missions | MEDIUM - balanced coverage |
| **Deep (INVESTIGATION)** | 300 seconds (5 min) | Complex multi-layer analysis | LOW - near-complete coverage |

**Selection Logic:**
- **P0 emergencies:** Use DASH (60s)
- **Normal operations:** Use RECON (120s)
- **Security/compliance audits:** Use INVESTIGATION (300s)

### Timeout Behavior Modes

When a probe reaches timeout, behavior is determined by completion stage:

#### Mode 1: Early Abort (< 25% complete)
```
Timeout before probe reaches 25% of expected findings
├─ Action: ABORT this probe
├─ Result: Mark findings as INCOMPLETE
├─ Impact: Cross-reference will exclude this lens
└─ Recovery: May trigger follow-up probe
```

#### Mode 2: Partial Accept (25%-75% complete)
```
Timeout with partial findings already gathered
├─ Action: ACCEPT partial results with confidence downgrade
├─ Result: Mark findings as PARTIAL (confidence → MEDIUM/LOW)
├─ Impact: Usable but incomplete intel
└─ Recovery: Flag for follow-up investigation
```

#### Mode 3: Late Accept (> 75% complete)
```
Timeout near end of analysis
├─ Action: ACCEPT all gathered results
├─ Result: Mark findings as COMPLETE
├─ Impact: Full lens used, no degradation
└─ Recovery: None needed - sufficient data collected
```

### Probe-Specific Timeout Overrides

Certain probes may require extended timeouts based on target scope:

| Probe | Base Timeout | Override Condition | Extended Timeout |
|-------|--------------|-------------------|-----------------|
| **PERCEPTION** | Standard | Large log files (>100MB) | Standard + 30s |
| **INVESTIGATION** | Standard | Complex import graphs (>50 files) | Standard + 60s |
| **HISTORY** | Standard | Deep git history (>500 commits) | Standard + 45s |
| **STEALTH** | Standard | Large codebase (>1M LOC) | Standard + 60s |
| **ARCANA** | Standard | Multi-domain context needed | Standard + 30s |

**Override Decision Tree:**
```
Is target scope large?
├─ YES: Is this a critical mission (P0/P1)?
│   ├─ YES: Use extended timeout
│   └─ NO: Use standard, flag gaps
└─ NO: Use standard timeout
```

### Timeout Escalation Path

If standard timeout insufficient:

```
Mission Received (120s timeout)
│
├─ Probe reaches 75% at T=110s
│  └─ Early decision to extend? NO
│     └─ Probe completes at T=118s ✓
│
├─ Probe reaches 40% at T=115s
│  └─ Insufficient coverage detected
│     └─ ESCALATION DECISION POINT
│        ├─ Option A: Abort probe (high-risk intel gap)
│        ├─ Option B: Extend 30s (total 150s)
│        └─ Option C: Replace with focused follow-up
```

**Escalation Criteria:**
- Probe estimated to miss critical section
- Mission priority indicates extended time acceptable
- Remaining probes completing on time (budget exists)

**Escalation Authority:**
- G2_RECON decides autonomously for own missions
- ORCHESTRATOR must approve for critical-path delays

---

## Failure Recovery

### Failure Mode Classification

SEARCH_PARTY defines four failure categories:

#### Category 1: Probe Crash (Critical)
```
Probe execution fails before any results
├─ Cause: Logic error, unhandled exception, resource exhaustion
├─ Detection: Null/empty result, crash stack trace
├─ Severity: CRITICAL
├─ Recovery: Immediate probe restart with same parameters
├─ Max Retries: 2 (then mark as FAILED)
├─ Impact on Mission: Proceed with 9 probes (loss of one lens)
```

#### Category 2: Partial Data (Major)
```
Probe completes but returns incomplete/corrupted findings
├─ Cause: Timeout, read permission denied, data format error
├─ Detection: Incomplete artifact list, confidence LOW
├─ Severity: MAJOR
├─ Recovery: Flag findings with confidence downgrade
├─ Max Retries: 1 (targeted follow-up instead)
├─ Impact on Mission: Usable but reduced signal
```

#### Category 3: Timeout Exceeded (Moderate)
```
Probe hits timeout boundary during execution
├─ Cause: Large dataset, slow queries, network delays
├─ Detection: T > timeout_limit with partial results
├─ Severity: MODERATE
├─ Recovery: Apply Mode 2/3 (partial/late accept)
├─ Max Retries: 0 (timeout is hard limit)
├─ Impact on Mission: See timeout behavior modes above
```

#### Category 4: Isolation Breach (Critical)
```
Probe attempts to access resources outside scope
├─ Cause: Incorrect target path, scope creep, bug in probe logic
├─ Detection: Attempted access outside target path
├─ Severity: CRITICAL
├─ Recovery: Abort probe immediately, security review required
├─ Max Retries: 0 (escalate to ORCHESTRATOR)
├─ Impact on Mission: Mission may be suspended pending review
```

### Partial Success Criteria

Mission can proceed if minimum probes succeed:

```
Total Probes Needed: 10
├─ Critical Threshold: 7 probes (70%) must complete
├─ Acceptable Threshold: 5 probes (50%) if no critical failures
└─ Abort Threshold: < 5 probes (< 50%) - insufficient intel
```

**Per-Probe Criticality Levels:**

| Probe | Criticality | Reason |
|-------|-------------|--------|
| PERCEPTION | HIGH | Baseline state required |
| INVESTIGATION | HIGH | Dependency understanding essential |
| ARCANA | MEDIUM-HIGH | Domain safety critical |
| HISTORY | MEDIUM | Context important but not essential |
| INSIGHT | MEDIUM | Design understanding valuable |
| RELIGION | MEDIUM | Compliance check important |
| NATURE | MEDIUM | Ecosystem health informative |
| MEDICINE | MEDIUM | Performance data useful |
| SURVIVAL | MEDIUM | Resilience understanding valuable |
| STEALTH | MEDIUM-HIGH | Security gaps critical |

**Minimum Viable Intel:**
- PERCEPTION (baseline state)
- INVESTIGATION (dependencies)
- ARCANA (domain safety)
- At least 4 of remaining 7 probes

If this minimum not met: Flag mission as INCOMPLETE, recommend follow-up focused probes.

### Circuit Breaker Pattern

Prevents cascade failures when platform failures detected:

```
Circuit States:

CLOSED (normal operation)
├─ All probes executing normally
├─ Trip Condition: > 3 consecutive probe failures
│  ├─ Transition to OPEN
│  └─ Log incident for review
└─ Reset: Manual acknowledgment OR 5 min timeout

OPEN (defensive mode)
├─ Suspend new probe spawning
├─ Allow in-flight probes to complete
├─ Trip Condition: All in-flight probes completed
│  └─ Transition to HALF-OPEN
├─ Timeout: 5 minutes (auto-reset)
└─ Action: ORCHESTRATOR notified

HALF-OPEN (recovery test)
├─ Allow single test probe to execute
├─ Success: Return to CLOSED
├─ Failure: Return to OPEN
└─ Timeout: 2 minutes
```

**Trip Thresholds:**

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Consecutive crashes | 3 | Trip to OPEN |
| Crash rate | > 30% in 5 min | Trip to OPEN |
| Resource exhaustion | Memory > 90% | Degrade to DASH timeout |
| Platform latency | > 500ms p99 | Extend probe timeouts +30s |

**Circuit Breaker State Storage:**
- Location: Redis key `search_party:circuit_breaker`
- Persist across sessions
- TTL: 24 hours

### Recovery Procedures by Failure Type

#### Probe Crash Recovery

```
Step 1: Detect crash (result is null or exception)
        └─ Log incident with timestamp

Step 2: Classify (was it expected hardware issue or logic bug?)
        ├─ If retry-eligible (timeout, permission denied)
        │  └─ Go to Step 3 (Retry)
        └─ If logic bug (index error, null pointer)
           └─ Go to Step 4 (Abort & document)

Step 3: Retry with exponential backoff
        ├─ Attempt 1: Retry immediately (same parameters)
        ├─ Attempt 2: Wait 5s, then retry (same parameters)
        └─ After 2 attempts: If still failed, go to Step 4

Step 4: Abort probe and continue mission
        ├─ Mark probe FAILED in output
        ├─ Document failure mode
        ├─ Continue mission with remaining 9 probes
        ├─ If critical probe (PERCEPTION, INVESTIGATION): Flag mission as DEGRADED
        └─ Add to follow-up investigation queue
```

#### Timeout Recovery

```
Step 1: Timeout detected (T >= timeout_limit)
        └─ Check completion percentage

Step 2: Early exit (< 25% complete)
        ├─ ABORT probe
        ├─ Mark as INCOMPLETE
        ├─ Schedule follow-up focused probe
        └─ Continue mission with 9 probes

Step 3: Partial completion (25%-75%)
        ├─ ACCEPT results with confidence downgrade
        ├─ Mark as PARTIAL
        ├─ Note findings are incomplete
        └─ Continue mission with full 10 probes

Step 4: Near-complete (> 75%)
        ├─ ACCEPT all results
        ├─ Mark as COMPLETE
        ├─ Proceed normally
        └─ Continue mission with full 10 probes

Step 5: Post-mission follow-up
        ├─ If > 2 timeouts in mission: Escalate timeout for next run
        ├─ If specific probes consistently timeout: Add override rule
        └─ Review mission scope for future reduction
```

#### Isolation Breach Recovery

```
Step 1: Breach detected (attempted access outside scope)
        ├─ Immediate probe termination
        ├─ Log security incident with full context
        └─ Escalate to ORCHESTRATOR

Step 2: Mission suspension
        ├─ Pause remaining probes
        ├─ Do NOT continue with 9 probes
        ├─ Await ORCHESTRATOR decision
        └─ (This is a potential compromise scenario)

Step 3: Investigation
        ├─ ORCHESTRATOR reviews breach cause
        ├─ Determine if scope definition was incorrect
        ├─ Or if probe logic is faulty
        ├─ Or if security boundary violated
        └─ Implement corrective measures

Step 4: Re-run
        ├─ Once root cause addressed
        ├─ Re-run mission with corrected parameters
        └─ Add scope validation to future runs
```

### Graceful Degradation Strategy

When failures detected, degrade intelligently:

```
0 Probes Failed (100% success)
└─ Full Intel Brief, proceed normally

1-2 Probes Failed (80-90% success)
├─ Minor Intel Brief (flag missing lenses)
├─ Identify which lens missing
├─ Note gaps in cross-reference section
└─ Proceed with caution

3-4 Probes Failed (60-70% success)
├─ Degraded Intel Brief
├─ Add INTELLIGENCE_INCOMPLETE flag
├─ Note missing critical lenses if any
├─ Recommend high-priority follow-up
└─ Proceed only if mission-critical

5+ Probes Failed (< 60% success)
├─ Mission Aborted
├─ Insufficient intel quality
├─ Log full failure details
├─ ORCHESTRATOR decides next steps
└─ Recommend complete re-run when conditions improve
```

**Degradation Checklist:**
- [ ] Which probes failed?
- [ ] Are CRITICAL probes (PERCEPTION, INVESTIGATION, ARCANA) among failed?
- [ ] Can mission proceed with available intel?
- [ ] Are gaps acceptable for this mission priority?
- [ ] Should follow-up be immediate or deferred?

---

## Security Model

### Probe Isolation Requirements

Each probe executes in isolated context to prevent information leakage:

#### Context Isolation

```
Each Probe Receives:
├─ Target path (absolute, validated)
├─ Mission context (questions to answer)
├─ Output format spec
├─ Timeout limit
└─ Scope boundary (what NOT to examine)

Each Probe CANNOT Access:
├─ Other probes' results (until synthesis)
├─ Raw database credentials
├─ API tokens beyond read-only scope
├─ Files outside target path
└─ Other concurrent missions' data
```

#### Memory/State Isolation

```
Probe Memory Space
├─ Contains only: Target files, temp analysis
├─ Cleared after: Results collected
├─ No persistence: Between-probe state
├─ No caching: Across missions
└─ No cross-contamination: Probe A can't affect Probe B data
```

#### Network Isolation

```
Probe Network Access
├─ Outbound: Read-only API calls to target system only
├─ Inbound: None
├─ DNS: Restricted to target hosts only
├─ Rate limits: Applied per-probe
└─ Logging: All access logged for audit trail
```

### Input Validation for Target Paths

All target paths validated before probe deployment:

#### Path Validation Rules

```
Valid Target Path: /home/user/Autonomous-Assignment-Program-Manager/backend/app/models/person.py
├─ MUST be absolute path
├─ MUST exist in filesystem
├─ MUST be within repo boundaries
├─ MUST pass symlink resolution
├─ MUST not contain directory traversal attempts (../)
└─ MUST have read permissions for probes

Invalid Paths (REJECTED):
├─ Relative paths: models/person.py ✗
├─ Outside repo: /etc/passwd ✗
├─ Symlink escapes: /repo/link → /tmp/bad ✗
├─ Directory traversal: /repo/app/../../etc/passwd ✗
├─ Nonexistent: /repo/models/phantom.py ✗
└─ Permission denied: /repo/.git/config (if restricted) ✗
```

#### Validation Algorithm

```python
def validate_target_path(target: str, repo_root: str) -> bool:
    """Validate target path before probe deployment."""

    # Step 1: Absolute path check
    if not os.path.isabs(target):
        return False  # Must be absolute

    # Step 2: Existence check
    if not os.path.exists(target):
        return False  # Path must exist

    # Step 3: Symlink resolution
    real_path = os.path.realpath(target)

    # Step 4: Boundary check (within repo)
    if not real_path.startswith(os.path.realpath(repo_root)):
        return False  # Must be within repo

    # Step 5: Directory traversal check
    if '..' in target or '..' in real_path:
        return False  # No parent directory escapes

    # Step 6: Permission check
    if not os.access(target, os.R_OK):
        return False  # Probes must have read access

    return True
```

**Validation Enforcement:**
- Location: G2_RECON before spawning probes
- Failure behavior: REJECT mission with error message
- Logging: Log all validation failures for security audit

### Access Control Model for Probe Scope

Define what each probe can examine:

#### Scope Definition Format

```markdown
## Target Scope Definition

**Primary Target:** /path/to/component
**Scope Type:** [FILE | DIRECTORY | MODULE | SYSTEM]

**Allowed Zones:**
- [path]: Read analysis of code/logs/metrics
- [path]: Read git history
- [path]: Read imports and dependencies

**Forbidden Zones:**
- .env files (secrets)
- .git/config (credentials)
- private keys
- Database dumps
- Customer data exports
- PII/HIPAA data

**Access Level:** READ-ONLY (no modifications)
```

#### Scope Enforcement per Probe

| Probe | Allowed Access | Forbidden Access |
|-------|---|---|
| **PERCEPTION** | Runtime state, logs, health checks | Database contents, raw configs |
| **INVESTIGATION** | Source code, imports, call chains | Private modules, hidden tests |
| **ARCANA** | Domain docs, compliance rules, specs | Implementation details, algorithms |
| **HISTORY** | Git log, commit history, blame | Private branches, stashed changes |
| **INSIGHT** | Code comments, docs, design files | Internal decision emails, memos |
| **RELIGION** | Repo root (CLAUDE.md, CONSTITUTION.md) | Branch protection rules, secrets |
| **NATURE** | Git history + source code | Performance internals, cache state |
| **MEDICINE** | Metrics, monitoring, performance data | Raw database, private telemetry |
| **SURVIVAL** | Test files, error scenarios | Production incident details, PII |
| **STEALTH** | Full code review scope | Encryption keys, auth tokens |

### Data Retention Policy for Probe Outputs

Govern lifecycle of sensitive probe findings:

#### Data Classification

```
Classification Level | Sensitivity | Example | Retention |
---|---|---|---|
PUBLIC | None | Test results, architecture docs | 90 days |
INTERNAL | Low | Code analysis, design intent | 30 days |
SENSITIVE | High | Performance issues, edge cases | 7 days |
CRITICAL | Very High | Security findings, compliance gaps | 1 day |
```

#### Retention Rules

```
Probe Output Lifecycle:

Day 0 (Generation)
├─ Created with timestamp
├─ Classified by sensitivity level
├─ Stored in mission log
└─ Provided to ORCHESTRATOR

Day 1-7 (Active Use)
├─ Available for cross-reference
├─ Available for follow-up probes
├─ Available for follow-up investigation
└─ Retention depends on classification

Day 8-30 (Archive)
├─ Moved to archive storage
├─ Available only on request
├─ Not automatically processed
└─ Deleted per classification schedule

Post Retention Period:
├─ Securely deleted (not recoverable)
├─ Audit logged
├─ Exception: Keep critical findings indefinitely
└─ Exception: Regulatory holds override schedule
```

#### Storage Security

```
Probe Output Storage:

Location: Redis + backup system (encrypted)
├─ Redis key: search_party:mission:{mission_id}:{probe_name}
├─ TTL: Automated based on classification
├─ Backup: Encrypted to cold storage
└─ Access: G2_RECON + ORCHESTRATOR only

Audit Trail:
├─ Who accessed results: logged
├─ When accessed: timestamp
├─ What used from results: logged
├─ Retention: 1 year minimum
└─ Available to: Security team on request
```

---

## Operational Enhancements

### Context Overhead Documentation

**CRITICAL TRUTH:** Parallel agents have significant context cost.

#### Context Budget Overhead

Each spawned agent requires:

```
Per-Agent Context Overhead:
├─ Agent initialization: ~5KB
├─ Target scope definition: ~2-5KB (depends on target size)
├─ Probe-specific context: ~1-3KB
├─ Timeout/failure recovery rules: ~0.5KB
├─ Mission metadata: ~0.5KB
└─ Total per agent: ~9-15KB baseline

10 Probes = ~90-150KB of overhead JUST for context

Actual Measured Overhead (empirical):
├─ Small targets (single file): ~2x context cost
├─ Medium targets (module): ~2x context cost
├─ Large targets (system): ~2.5x context cost
└─ Example: 100KB mission context → 200-250KB with 10 probes
```

**Mitigation Strategies:**
1. **Compress context:** Pre-filter unnecessary information
2. **Use focused probes:** Only spawn 3-5 probes for simple targets
3. **Batch missions:** Group related investigations
4. **Reference external docs:** Point to CLAUDE.md instead of embedding

### Scaling Limits (Tested Constraints)

**Tested Scale:** 10 concurrent agents
**Recommended Maximum:** 15 agents
**Absolute Maximum:** 20 agents (degraded performance)

#### Scaling Test Results

```
Concurrency Level | Wall-Clock Time | Success Rate | Recommendations
---|---|---|---|
1-5 agents | T (baseline) | 100% | Optimal, safe
6-10 agents | ~1.05x T | 99% | Normal operations
11-15 agents | ~1.2x T | 98% | Use when needed
16-20 agents | ~1.4x T | 95% | Degraded, use sparingly
21+ agents | ~2x T+ | <95% | DO NOT USE

Legend: T = time for 1 agent
```

#### Scaling Decision Tree

```
Do you need > 10 probes?
├─ NO: Use standard 10 probes (SEARCH_PARTY)
│  └─ Cost: ~2x context, normal execution
│
└─ YES: Can you reduce scope?
   ├─ YES: Reduce to single-directory target
   │  └─ Revert to 10 probes
   │
   └─ NO: Deploy 11-15 selective probes
      ├─ Disable non-critical probes
      ├─ Accept ~1.2x wall-clock penalty
      ├─ Monitor success rate closely
      └─ Escalate if < 98% success
```

#### Resource Limits per Agent

| Resource | Limit | Action on Breach |
|----------|-------|-----------------|
| Memory per probe | 512MB | Abort and retry (max 2x) |
| File handles | 50 | Close least-used, continue |
| Network connections | 10 | Queue and retry |
| Wall-clock time | timeout (60s-300s) | Abort/partial-accept per mode |
| CPU time | 30s per probe | Graceful timeout |

### Batch Sizing Recommendations

When running multiple SEARCH_PARTY missions:

#### Batch Size Rules

```
Batch Size = Number of parallel SEARCH_PARTY missions

Recommended Batch Sizes:

Single Mission (Small Target)
├─ 10 probes × 1 mission
├─ Context overhead: ~150KB
├─ Time: 60-300s (depending on timeout)
└─ Success rate: > 99%

Two Parallel Missions (Medium Targets)
├─ 10 probes × 2 missions = 20 agents
├─ Context overhead: ~300KB
├─ Time: ~150-350s (slightly compressed)
├─ Success rate: 98%
├─ Decision: Use if targets are independent
└─ Caution: Monitor for resource contention

Three+ Parallel Missions (Large Targets)
├─ NOT RECOMMENDED without resource isolation
├─ Context overhead: ~450KB+
├─ Time: degraded
├─ Success rate: < 95%
├─ Alternative: Queue missions sequentially
└─ Or: Deploy selective probes (6-8 instead of 10)
```

#### Batch Execution Pattern

```
Batch of N missions:

Sequential Pattern (SAFE):
Mission 1 (120s)
└─ Complete, results synthesized
   └─ Mission 2 (120s)
      └─ Complete, results synthesized
         └─ Mission 3 (120s)
Total time: ~360s, 100% success

Parallel-of-2 Pattern (BALANCED):
Mission 1 (120s) ┐
Mission 2 (120s) ┘ Parallel
└─ Both complete
   └─ Mission 3 (120s)
Total time: ~240s, 98% success

Parallel-3+ Pattern (NOT RECOMMENDED):
Mission 1 ┐
Mission 2 ├─ Parallel
Mission 3 ┘
└─ Risk: > 1 failure, slow, resource contention
```

### Operational Checklist for Deployment

Before spawning SEARCH_PARTY mission:

```
PRE-DEPLOYMENT CHECKLIST:

Scope Definition
─────────────────────────
□ Target path identified and validated
□ Target path is absolute (not relative)
□ Target path exists and is readable
□ Target path within repo boundaries
□ Scope does NOT include .env files or secrets
□ Scope boundaries communicated to all probes

Mission Context
─────────────────────────
□ Mission questions are clear and specific
□ Mission priority level (P0-P3) assigned
□ Mission timeout selected (DASH/RECON/INVESTIGATION)
□ Context provided to probes is concise (< 500 words)
□ Links to external docs provided where relevant

Probe Configuration
─────────────────────────
□ All 10 probes enabled (or justify selective probes)
□ Probe-specific overrides reviewed if target is large
□ Timeout values set appropriately
□ Failure recovery mode defined
□ Circuit breaker reset if needed

Resource Verification
─────────────────────────
□ Redis available for context storage
□ Context budget available (~150KB for 10 probes)
□ No other concurrent SEARCH_PARTY missions (or approved batch)
□ Agent execution environment healthy
□ Network connectivity verified

Security Review
─────────────────────────
□ No secrets in target path
□ No sensitive data exposed in context
□ Access control model defined
□ Probe isolation confirmed
□ Data retention policy applicable
□ Security clearance for all participants

READY TO DEPLOY: If all items checked
```

### Monitoring and Alerting Recommendations

Observe SEARCH_PARTY health in production:

#### Key Metrics to Monitor

```
Metric | Target | Alert Threshold | Check Frequency |
---|---|---|---|
Probe completion rate | > 99% | < 98% for 5 min | Every mission |
Timeout frequency | < 5% | > 10% | Hourly rolling window |
Context overhead | ~2x | > 3x | Per mission |
Circuit breaker trips | 0/hour | > 1/hour | Real-time |
Probe crash rate | 0% | > 1% | Per 100 missions |
Cross-reference discrepancies | > 0 expected | 0 for suspicious target | Per mission |
Intel actionability | > 80% findings useful | < 70% | Per brief |
Synthesis time | < 5 minutes | > 10 minutes | Per mission |
```

#### Alert Definitions

```
ALERT: Probe Timeout Spike
├─ Condition: > 20% of probes timeout in single mission
├─ Severity: WARNING
├─ Action: Extend timeout for next mission, investigate
├─ Check: Is target larger than expected?
└─ Escalate if: Pattern continues for 3+ missions

ALERT: Circuit Breaker Tripped
├─ Condition: Circuit breaker transitions to OPEN
├─ Severity: CRITICAL
├─ Action: Suspend SEARCH_PARTY, investigate cause
├─ Check: Agent execution environment health
└─ Recovery: Manual reset required after fix

ALERT: High Context Overhead
├─ Condition: Per-mission context > 300KB
├─ Severity: INFO (informational)
├─ Action: Recommend scope reduction for future missions
├─ Check: Can we use selective probes instead of all 10?
└─ Escalate if: > 500KB for normal-sized target

ALERT: Low Actionability
├─ Condition: < 70% of findings lead to actions
├─ Severity: WARNING
├─ Action: Review probe prompt templates for drift
├─ Check: Are probes answering the right questions?
└─ Escalate if: Pattern indicates protocol misuse

ALERT: Synthesis Time Degradation
├─ Condition: Synthesis phase takes > 10 minutes
├─ Severity: WARNING
├─ Action: Break large missions into batches
├─ Check: Are we trying to cross-reference too many findings?
└─ Escalate if: Unable to complete brief within SLA
```

#### Logging and Audit Trail

```
Every SEARCH_PARTY mission logs:

Mission Start:
├─ Timestamp
├─ Mission ID (unique)
├─ Target path (validated)
├─ Priority level
├─ Requested probes (which of the 10)
└─ Requestor (G2_RECON / ORCHESTRATOR)

Per-Probe Events:
├─ Probe spawn (timestamp, timeout)
├─ Probe completion (timestamp, confidence)
├─ Timeout hit (timestamp, completion %)
├─ Failure (timestamp, failure type, recovery action)
└─ Results stored (location, retention policy)

Mission Completion:
├─ All probes complete/fail/timeout (timestamp)
├─ Discrepancies identified (count)
├─ Gaps filled (count)
├─ Intel brief generated
├─ Synthesis duration
└─ Delivery to ORCHESTRATOR

Post-Mission:
├─ Any follow-up probes spawned (timestamp, trigger)
├─ Data retention actions (archived/deleted)
├─ Audit trail available (1 year minimum)
└─ Cost (context overhead, wall-clock time)
```

---

## Integration Points

### G2_RECON Integration

G2_RECON uses SEARCH_PARTY as its **default reconnaissance pattern**:

```markdown
# In G2_RECON workflows:

## Pre-Task Reconnaissance
When conducting pre-task recon, deploy SEARCH_PARTY protocol for comprehensive coverage.

## Impact Analysis
Use SEARCH_PARTY to gather multi-perspective impact data before change assessment.
```

### ORCHESTRATOR Integration

ORCHESTRATOR can request SEARCH_PARTY directly:

```markdown
## Request to G2_RECON

Deploy SEARCH_PARTY protocol on:
**Target:** /path/to/component
**Context:** Planning major refactor
**Priority:** P1
```

### Result Integration

SEARCH_PARTY output feeds into:
- Pre-task intelligence briefings
- Impact analysis reports
- Risk assessments
- Parallelization decisions (via domain mapping)

---

## When to Use SEARCH_PARTY

### Good Candidates

- Investigating unfamiliar code areas
- Pre-task reconnaissance for complex changes
- Bug investigation with unclear root cause
- Security or compliance reviews
- Technical debt assessment
- Architecture review

### Poor Candidates

- Simple, well-understood tasks
- Single-file changes with known impact
- Time-critical emergencies (use single focused probe)
- When only one lens is needed

---

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Sequential probes | 10x slower for no benefit | Always parallel |
| Skipping cross-reference | Miss high-signal discrepancies | Always compare findings |
| Single probe recon | Incomplete picture | Deploy full party |
| Ignoring gaps | Blind spots remain | Follow up on gaps |
| Probes overlap scope | Confused, redundant findings | Keep lenses distinct |

---

## Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Probe completion rate | 100% | All lenses must report |
| Discrepancies found | > 0 expected | Validates multi-lens value |
| Gap identification | Complete | Knows what it doesn't know |
| Synthesis time | < 5 min | Rapid intel delivery |
| Intel actionability | > 80% findings actionable | Useful, not just comprehensive |

---

## Related Protocols

- `SIGNAL_PROPAGATION.md` - Inter-agent signaling
- `RESULT_STREAMING.md` - Progress visibility
- `MULTI_TERMINAL_HANDOFF.md` - Session coordination

## Related Agents

- `G2_RECON.md` - Primary user of this protocol
- `ORCHESTRATOR.md` - Receives intel briefs
- Coordinator agents - Receive domain-specific findings

---

*SEARCH_PARTY: Ten lenses, one target, zero marginal cost. The discrepancies are the signal.*
