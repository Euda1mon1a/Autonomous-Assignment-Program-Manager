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
