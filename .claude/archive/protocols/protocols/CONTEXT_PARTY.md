# CONTEXT_PARTY Protocol

> **Purpose:** Coordinated parallel historical context gathering with 6 specialized probes
> **Status:** Active
> **Priority:** P1
> **Owner:** G4_CONTEXT_MANAGER
> **Skill:** `/context-party`
> **Upstream:** SEARCH_PARTY (current state), session history, RAG knowledge base
> **Downstream:** PLAN_PARTY (planning informed by history), ORCHESTRATOR (decision making)

---

## Overview

CONTEXT_PARTY enables parallel gathering of historical context from multiple perspectives - like a military G-4 Logistics section managing "context logistics" to ensure the right information reaches the right decision-makers at the right time.

Just as G-4 manages supplies, ammunition, fuel, and equipment, G4_CONTEXT_MANAGER manages context, precedent, decisions, and knowledge - the "logistics" that make effective planning possible.

---

## IDE Crash Prevention (CRITICAL)

**DO NOT** have ORCHESTRATOR spawn 6 context probes directly. This causes IDE seizure and crashes.

**CORRECT Pattern:**
```
ORCHESTRATOR → spawns 1 G4_CONTEXT_MANAGER
                    ↓
              G4_CONTEXT_MANAGER deploys 6 context probes internally
              (manages parallelism, synthesizes context)
```

**WRONG Pattern:**
```
ORCHESTRATOR → spawns 6 context probes directly → IDE CRASH
```

The G-4 Context Manager absorbs the parallelism complexity. ORCHESTRATOR only ever spawns 1 coordinator.

**Key Insight:** Same task, different historical lenses. Synthesizing diverse context sources yields better decisions than a single context thread.

**Relationship to SEARCH_PARTY and PLAN_PARTY:**
```
SEARCH_PARTY (current state intel) → G2_RECON (state synthesis)
                                          ↓
CONTEXT_PARTY (historical intel) → G4_CONTEXT_MANAGER (context synthesis)
                                          ↓
PLAN_PARTY (strategy generation) → G5_PLANNING (plan synthesis)
                                          ↓
                                   ORCHESTRATOR (execution)
```

---

## Economics: Zero Marginal Wall-Clock Cost

Same as SEARCH_PARTY and PLAN_PARTY - parallel context probes with the same timeout cost nothing extra in wall-clock time.

```
Sequential (BAD):        Parallel (GOOD):
┌────────────┐           ┌────────────┐
│ PRECEDENT  │ 90s       │ PRECEDENT  │ ┐
├────────────┤           ├────────────┤ │
│ PATTERNS   │ 90s       │ PATTERNS   │ │
├────────────┤           ├────────────┤ │
│ CONSTRAINTS│ 90s       │ CONSTRAINTS│ │ 90s total
├────────────┤           ├────────────┤ │
│ DECISIONS  │ 90s       │ DECISIONS  │ │
├────────────┤           ├────────────┤ │
│ FAILURES   │ 90s       │ FAILURES   │ │
├────────────┤           ├────────────┤ │
│ KNOWLEDGE  │ 90s       │ KNOWLEDGE  │ ┘
└────────────┘           └────────────┘
Total: 540s              Total: 90s (6x faster)
```

**Implication:** Always spawn all 6 probes when context gathering is needed. There is no cost savings from running fewer.

---

## The Six Context Probes

| Probe | Lens | RAG Strategy | What It Finds |
|-------|------|--------------|---------------|
| **PRECEDENT** | Past solutions | Search `session_learnings`, `ai_pattern` | How similar problems were solved, proven approaches |
| **PATTERNS** | Recurring themes | Cross-doc_type search, temporal analysis | Cross-session patterns, repeated approaches, trends |
| **CONSTRAINTS** | Known limits | Search `acgme_rules`, `scheduling_policy` | Documented constraints, gotchas, warnings, hard limits |
| **DECISIONS** | ADRs/choices | Search `decision_history` | Architectural decisions, rationale, trade-offs |
| **FAILURES** | Past issues | Search `bug_fix`, `session_learnings` | What broke before, root causes, fixes, prevention |
| **KNOWLEDGE** | Domain expertise | Search by specific `doc_type` | ACGME rules, scheduling policies, resilience concepts |

### Probe Characteristics

#### PRECEDENT Probe
**Focus:** How have we solved similar problems before?

**RAG Queries:**
```bash
# Search for similar past solutions
rag_search("similar to [task description]", doc_type="session_learnings", limit=10)
rag_search("precedent [domain] [pattern]", doc_type="ai_pattern", limit=5)
```

**Outputs:**
- Similar past tasks and their solutions
- Proven approaches that worked
- Approaches that failed and why
- Reusable components or patterns
- Confidence assessment (how similar is the precedent?)

**Questions Asked:**
- Has this exact problem been solved before?
- What similar problems have we tackled?
- What approaches worked? What didn't?
- Can we reuse existing solutions?
- What lessons were learned?

**Synthesis:**
- Rank precedents by similarity to current task
- Extract reusable patterns
- Flag outdated precedents (superseded by later decisions)
- Recommend most applicable approach

#### PATTERNS Probe
**Focus:** What recurring themes exist across sessions?

**RAG Queries:**
```bash
# Search for patterns across all doc types
rag_search("pattern [domain]", limit=15)
rag_search("recurring [theme]", limit=10)
rag_search("anti-pattern [domain]", limit=5)
```

**Outputs:**
- Cross-session recurring patterns
- Repeated design approaches
- Emergent architectural themes
- Anti-patterns to avoid
- Evolution of thinking over time

**Questions Asked:**
- What patterns keep emerging?
- Have we solved this category of problem before?
- What design approaches do we consistently use?
- What mistakes do we repeatedly make?
- How has our approach evolved?

**Synthesis:**
- Identify high-frequency patterns (appear in 3+ sessions)
- Track pattern evolution (how patterns change over time)
- Flag anti-patterns (patterns that consistently lead to problems)
- Recommend pattern application to current task

#### CONSTRAINTS Probe
**Focus:** What are the known limits and gotchas?

**RAG Queries:**
```bash
# Search for constraints and limitations
rag_search("constraint [domain]", doc_type="acgme_rules", limit=10)
rag_search("constraint [domain]", doc_type="scheduling_policy", limit=10)
rag_search("gotcha [technology]", doc_type="session_learnings", limit=5)
rag_search("limitation [feature]", limit=5)
```

**Outputs:**
- Hard limits that cannot be violated (ACGME, policy)
- Known performance bottlenecks
- Edge cases and corner cases
- Warning signs and red flags
- Gotchas and pitfalls

**Questions Asked:**
- What constraints apply to this task?
- What are the hard limits we can't violate?
- What gotchas should we watch for?
- What edge cases exist?
- What limitations will we hit?

**Synthesis:**
- Categorize constraints by severity (MUST, SHOULD, COULD)
- Identify constraints that apply to current task
- Flag potential constraint violations in proposed approach
- Recommend constraint-respecting strategies

#### DECISIONS Probe
**Focus:** What architectural decisions are relevant?

**RAG Queries:**
```bash
# Search for architectural decisions
rag_search("decision [topic]", doc_type="decision_history", limit=10)
rag_search("ADR [domain]", doc_type="decision_history", limit=5)
rag_search("architecture choice [component]", doc_type="session_learnings", limit=5)
```

**Outputs:**
- Relevant architectural decisions (ADRs)
- Rationale for past choices
- Trade-offs that were made
- Reversible vs irreversible decisions
- Decision dependencies and lineage

**Questions Asked:**
- What architectural decisions affect this task?
- Why were those decisions made?
- What trade-offs were accepted?
- Are any decisions now outdated?
- What new decisions are needed?

**Synthesis:**
- Build decision dependency graph
- Identify relevant active decisions
- Flag superseded decisions
- Detect conflicting decisions (escalate if found)
- Recommend new decisions needed

#### FAILURES Probe
**Focus:** What has broken before and why?

**RAG Queries:**
```bash
# Search for past failures and bugs
rag_search("bug [component]", doc_type="bug_fix", limit=10)
rag_search("failure [domain]", doc_type="session_learnings", limit=10)
rag_search("broke [feature]", limit=5)
rag_search("root cause [issue]", doc_type="bug_fix", limit=5)
```

**Outputs:**
- Past failures and root causes
- Bug patterns and common mistakes
- Regression history
- Fix effectiveness (did the fix work?)
- Failure mode analysis

**Questions Asked:**
- What has broken in this area before?
- What were the root causes?
- How were failures fixed?
- Did the fixes hold or regress?
- What failure modes should we prevent?

**Synthesis:**
- Identify failure patterns relevant to current task
- Extract prevention strategies from past fixes
- Flag regression risks
- Recommend defensive measures
- Highlight "fragile" areas

#### KNOWLEDGE Probe
**Focus:** What domain knowledge is relevant?

**RAG Queries:**
```bash
# Search domain-specific knowledge
rag_search("ACGME [topic]", doc_type="acgme_rules", limit=10)
rag_search("scheduling [concept]", doc_type="scheduling_policy", limit=10)
rag_search("resilience [pattern]", doc_type="resilience_concepts", limit=5)
rag_search("military medical [context]", doc_type="military_specific", limit=5)
```

**Outputs:**
- Relevant ACGME rules and compliance knowledge
- Scheduling policies and constraints
- Resilience framework concepts
- Military medical context
- User guides and FAQs

**Questions Asked:**
- What domain rules apply?
- What policies govern this area?
- What compliance requirements exist?
- What domain-specific knowledge is needed?
- What documentation should be referenced?

**Synthesis:**
- Extract applicable domain rules
- Identify compliance requirements
- Map domain knowledge to task requirements
- Recommend knowledge gaps to fill
- Link to authoritative documentation

---

## Context Synthesis

After all 6 probes report back, G4_CONTEXT_MANAGER performs synthesis:

### 1. Cross-Reference Findings

**Goal:** Identify where probes agree or disagree

```python
def cross_reference(probe_reports: list[ProbeReport]) -> Synthesis:
    agreements = find_agreements(probe_reports)      # High confidence
    disagreements = find_disagreements(probe_reports) # High signal
    gaps = find_gaps(probe_reports)                  # Need new decisions

    return Synthesis(agreements, disagreements, gaps)
```

**High-Confidence Signals (Multiple Probes Agree):**
- PRECEDENT + PATTERNS both recommend approach X → Strong signal
- CONSTRAINTS + KNOWLEDGE both flag limit Y → Must respect
- DECISIONS + FAILURES both reference decision Z → Relevant ADR

**High-Signal Conflicts (Probes Disagree):**
- PRECEDENT says X, DECISIONS say Y → Precedent may be outdated
- PATTERNS shows trend A, FAILURES show A broke → Potential anti-pattern
- CONSTRAINTS limit X, PRECEDENT did X → Constraint added later

### 2. Conflict Resolution

**Conflict Types and Resolution Strategies:**

| Conflict Type | Resolution Strategy |
|--------------|---------------------|
| PRECEDENT vs DECISIONS | Newer decision wins (if dated); escalate if unclear |
| PATTERNS vs FAILURES | Pattern may be anti-pattern; flag for review |
| CONSTRAINTS vs PRECEDENT | Constraint wins (compliance); precedent is now invalid |
| KNOWLEDGE vs FAILURES | Knowledge may be stale; failure is ground truth |
| DECISIONS (Session X) vs DECISIONS (Session Y) | Architectural drift; ESCALATE to ARCHITECT |

### 3. Confidence Scoring

**Confidence Formula:**
```
Confidence = (Probes in Agreement / Total Probes) × Recency Weight × Relevance Score

High Confidence:    4+ probes agree, recent context, high relevance
Medium Confidence:  2-3 probes agree, some older context, medium relevance
Low Confidence:     0-1 probes, old context, or unclear relevance
```

**Confidence Examples:**

```markdown
## HIGH Confidence (85%)
- 5/6 probes agree: Use capacity allocation pattern from Sessions 42, 45, 48
- Recent: All references from last 2 months
- Relevant: Exact match to current task

## MEDIUM Confidence (60%)
- 3/6 probes agree: Apply resilience scoring framework
- Older: References from 4-6 months ago
- Relevant: Similar but not exact match

## LOW Confidence (30%)
- 1/6 probes: Mentions related approach
- Old: Reference from 8+ months ago
- Relevance: Tangentially related
```

### 4. Gap Identification

**Gap Types:**

| Gap Type | Meaning | Action |
|----------|---------|--------|
| No Precedent | Novel situation, no past solution | Flag for new approach, capture outcome |
| No Constraint | Uncovered area, no documented limit | Proceed with caution, document if found |
| No Decision | Unresolved architectural choice | ESCALATE to ARCHITECT or ORCHESTRATOR |
| No Failure Data | Untested area, no known issues | Recommend defensive measures |
| No Knowledge | Missing domain expertise | Query RAG more broadly, escalate if critical |

### 5. Context Brief Generation

**Output Structure:**

```markdown
## CONTEXT_PARTY Brief: [Task Name]

### Executive Summary
- **Confidence:** [HIGH/MEDIUM/LOW] ([N]%)
- **Recommendation:** [Follow precedent X / New approach needed / Mixed strategy]
- **Conflicts Detected:** [N] ([List critical conflicts])
- **Gaps Identified:** [N] ([List critical gaps])

### Key Findings by Probe

#### PRECEDENT
- [Finding 1]
- [Finding 2]
- **Recommendation:** [Specific action based on precedent]

#### PATTERNS
- [Pattern 1]
- [Pattern 2]
- **Anti-Patterns to Avoid:** [List]

#### CONSTRAINTS
- **Hard Limits:** [List]
- **Gotchas:** [List]
- **Recommendation:** [Constraint-respecting approach]

#### DECISIONS
- **Relevant ADRs:** [List with rationale]
- **Decision Dependencies:** [Graph or list]
- **New Decisions Needed:** [List]

#### FAILURES
- **Past Failures:** [List with root causes]
- **Regression Risks:** [List]
- **Prevention Strategy:** [Specific defensive measures]

#### KNOWLEDGE
- **Domain Rules:** [ACGME, policy, etc.]
- **Compliance Requirements:** [List]
- **Documentation:** [Links to authoritative sources]

### Cross-Probe Analysis

#### Agreements (High Confidence)
- [Agreement 1]: [N] probes agree
- [Agreement 2]: [N] probes agree

#### Conflicts (High Signal)
- **CONFLICT:** [Probe A] vs [Probe B]
  - **A says:** [Position]
  - **B says:** [Position]
  - **Resolution:** [Strategy]
  - **Escalation:** [YES/NO - to whom?]

#### Gaps (Action Needed)
- **Gap:** [What's missing]
  - **Impact:** [How this affects task]
  - **Action:** [Recommended next step]

### Recommendations

1. **Primary Approach:** [Based on highest-confidence findings]
2. **Constraints to Respect:** [Critical limits]
3. **Anti-Patterns to Avoid:** [Specific warnings]
4. **Defensive Measures:** [Based on FAILURES probe]
5. **New Decisions Required:** [Escalate to ARCHITECT/ORCHESTRATOR]

### RAG Coverage Report

- **Total Chunks Retrieved:** [N]
- **Doc Types Searched:** [List]
- **Date Range:** [Oldest] to [Newest]
- **Coverage Assessment:** [Comprehensive / Partial / Sparse]
```

---

## RAG Integration

### API Usage Patterns

#### Backend Running (Preferred)

```bash
# G4_CONTEXT_MANAGER uses RAG API when backend is available

# PRECEDENT Probe
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "schedule capacity allocation past approaches",
    "limit": 10,
    "doc_type": "session_learnings"
  }'

# PATTERNS Probe
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "recurring scheduling pattern capacity",
    "limit": 15
  }'

# CONSTRAINTS Probe
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ACGME work hour capacity limit",
    "limit": 10,
    "doc_type": "acgme_rules"
  }'

# DECISIONS Probe
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "architecture decision capacity allocation",
    "limit": 5,
    "doc_type": "decision_history"
  }'

# FAILURES Probe
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "scheduling engine failure capacity overflow",
    "limit": 5,
    "doc_type": "bug_fix"
  }'

# KNOWLEDGE Probe
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "scheduling policy capacity constraints",
    "limit": 10,
    "doc_type": "scheduling_policy"
  }'
```

#### MCP Tools (If Available)

```python
# When MCP tools are available through ORCHESTRATOR

# PRECEDENT Probe
result = rag_search(
    query="similar past solution [task]",
    limit=10,
    doc_type="session_learnings"
)

# Build formatted context for agent prompts
context = rag_context(
    query="capacity allocation precedent",
    max_chunks=5
)

# Health check before deployment
health = rag_health()
if not health['embedding_service_ok']:
    # Fall back to markdown search
    fallback_to_markdown_search()
```

#### Fallback Strategy (Backend Unavailable)

```python
# When RAG API is not available, fall back to file search

# PRECEDENT: Search session history
search_files(".claude/dontreadme/sessions/SESSION_*_HANDOFF.md")

# PATTERNS: Search synthesis documents
search_files(".claude/dontreadme/synthesis/PATTERNS.md")

# CONSTRAINTS: Search ACGME and policy docs
search_files("docs/rag-knowledge/acgme-rules.md")
search_files("docs/rag-knowledge/scheduling-policies.md")

# DECISIONS: Search decision log
search_files(".claude/dontreadme/synthesis/DECISIONS.md")

# FAILURES: Search session AARs and bug reports
search_files(".claude/dontreadme/sessions/SESSION_*_AAR.md")

# KNOWLEDGE: Search domain docs
search_files("docs/rag-knowledge/*.md")
```

---

## Context Lifecycle: Closing the Loop

**CRITICAL:** Context gathering is not complete until new learnings are ingested back into RAG.

### After Task Completion

1. **G4_CONTEXT_MANAGER captures outcome:**
   - Was precedent followed? Did it work?
   - Were new patterns discovered?
   - Were constraints encountered?
   - Were new decisions made?
   - Did anything break? Root cause?
   - What new knowledge was gained?

2. **Ingest new context to RAG:**
   ```bash
   curl -X POST http://localhost:8000/api/rag/ingest \
     -H "Content-Type: application/json" \
     -d '{
       "content": "Session [N] applied capacity allocation pattern from Session 42. Result: [outcome]. Lesson: [learning].",
       "doc_type": "session_learnings",
       "metadata": {
         "session": "[N]",
         "date": "[date]",
         "task": "[task]",
         "outcome": "[success/failure]"
       }
     }'
   ```

3. **Update decision history if new ADR:**
   ```bash
   curl -X POST http://localhost:8000/api/rag/ingest \
     -H "Content-Type: application/json" \
     -d '{
       "content": "Decision: [decision]. Rationale: [why]. Trade-offs: [what was sacrificed].",
       "doc_type": "decision_history",
       "metadata": {
         "decision_type": "architecture",
         "date": "[date]",
         "reversible": true/false
       }
     }'
   ```

4. **Mark superseded context if decision changed:**
   - Update old decision with "SUPERSEDED BY [new decision]"
   - Maintain decision lineage

5. **Close the context loop:**
   ```
   CONTEXT_PARTY (gather history)
         ↓
   PLAN_PARTY (apply history)
         ↓
   EXECUTION (implement plan)
         ↓
   G4_CONTEXT_MANAGER (capture outcome) ──┐
         ↑                                 │
         └─────────────────────────────────┘
              (Future CONTEXT_PARTY benefits)
   ```

---

## Escalation Rules

| Situation | Escalate To | Reason |
|-----------|-------------|--------|
| Conflicting decisions from different sessions | ARCHITECT | Architectural drift requiring resolution |
| Context contains HIPAA/OPSEC sensitive data | SECURITY_AUDITOR | Privacy/compliance review needed |
| Precedent violates current constraints | ORCHESTRATOR | Precedent is now invalid, new approach needed |
| No precedent for high-stakes task | ORCHESTRATOR | Human judgment required |
| Multiple anti-patterns detected | CODE_REVIEWER | Code quality review needed |
| RAG system unavailable and context critical | ORCHESTRATOR | Cannot gather context, abort or manual research |
| Probe failure rate > 33% | G4_CONTEXT_MANAGER | Circuit breaker, abort deployment |

---

## Failure Recovery

### Minimum Viable Context

Mission can proceed if at least these probes succeed:
- **PRECEDENT** (baseline: has this been done?) ✓
- **CONSTRAINTS** (safety: what can't we do?) ✓
- **KNOWLEDGE** (domain: what rules apply?) ✓
- At least **2 of remaining 3** probes

If minimum not met: ESCALATE to ORCHESTRATOR for manual context gathering.

### Circuit Breaker States

| State | Condition | Action |
|-------|-----------|--------|
| **CLOSED** (Normal) | < 2 probe failures | Continue normal operations |
| **OPEN** (Tripped) | ≥ 3 probe failures | Abort CONTEXT_PARTY, fall back to manual |
| **HALF-OPEN** (Testing) | After cooldown | Try 3 probes; if succeed, return to CLOSED |

### Probe Timeout Handling

```python
def deploy_probes_with_timeout(probes: list, timeout: int = 90):
    """Deploy probes with timeout and failure recovery"""

    results = []
    failures = 0

    # Deploy all probes in parallel
    futures = [probe.deploy_async(timeout=timeout) for probe in probes]

    # Wait for all with timeout
    for future in futures:
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            results.append(result)
        except asyncio.TimeoutError:
            failures += 1
            log_warning(f"Probe timeout: {future.probe_name}")
        except Exception as e:
            failures += 1
            log_error(f"Probe error: {future.probe_name} - {e}")

    # Check circuit breaker
    if failures >= 3:
        circuit_breaker.open()
        raise ContextGatheringFailure("Too many probe failures")

    # Check minimum viable context
    if not has_minimum_viable_context(results):
        raise InsufficientContextError("Minimum viable context not met")

    return results
```

---

## Timeout Profiles

| Profile | Duration | Best For | Coverage |
|---------|----------|----------|----------|
| **QUICK** | 60s | Fast context check, simple tasks | 4-6 probes expected |
| **STANDARD** | 90s | Normal context gathering (default) | 5-6 probes expected |
| **DEEP** | 180s | Comprehensive historical analysis | 6 probes expected |

---

## Workflow Integration

### Full Intelligence-to-Execution Pipeline

```
User Request: Complex task
    ↓
ORCHESTRATOR receives task
    ↓
┌─────────────────────────────────────┐
│ Phase 1: RECONNAISSANCE             │
│ G2_RECON deploys SEARCH_PARTY       │
│ (Current state intel - what exists) │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Phase 2: CONTEXT GATHERING          │
│ G4_CONTEXT_MANAGER deploys          │
│ CONTEXT_PARTY                       │
│ (Historical intel - what we know)   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Phase 3: PLANNING                   │
│ G5_PLANNING deploys PLAN_PARTY      │
│ (Strategy - what to do)             │
│ Informed by: current state +        │
│              historical context     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Phase 4: EXECUTION                  │
│ ORCHESTRATOR executes plan          │
│ Coordinators perform work           │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Phase 5: CONTEXT CAPTURE            │
│ G4_CONTEXT_MANAGER captures outcome │
│ Ingests learnings to RAG            │
│ (Closes the loop)                   │
└─────────────────────────────────────┘
```

### Decision Tree: When to Deploy CONTEXT_PARTY

```
Is this a novel feature with no historical analog?
├─ YES → SKIP context-party (no precedent exists)
└─ NO → Continue

Is this an emergency (P0)?
├─ YES → SKIP context-party (no time for history)
└─ NO → Continue

Do you already have complete context?
├─ YES → SKIP context-party (context already known)
└─ NO → Continue

Is this a complex or high-stakes task?
├─ YES → DEPLOY context-party (need full context)
└─ NO → Continue

Did SEARCH_PARTY reveal questions about history?
├─ YES → DEPLOY context-party (answer historical questions)
└─ NO → Optional, depends on task complexity
```

---

## Related Protocols

- **SEARCH_PARTY:** Current state reconnaissance (complements CONTEXT_PARTY)
- **PLAN_PARTY:** Strategy generation (downstream consumer of context)
- **Session Handoff:** Context capture at session boundaries
- **RAG Knowledge Base Management:** Context ingestion and curation

---

## Metrics and Monitoring

### Context Gathering Effectiveness

**Track these metrics:**

| Metric | Target | Meaning |
|--------|--------|---------|
| **Probe Success Rate** | ≥ 83% (5/6) | Probes successfully complete |
| **Minimum Context Met** | 100% | Critical probes always succeed |
| **Conflict Detection Rate** | Tracked | How often conflicts found |
| **Context Application Rate** | ≥ 70% | Gathered context is actually used |
| **RAG Coverage** | ≥ 50% tasks | How often RAG has relevant info |
| **Wall-Clock Time** | ≤ 90s | Parallel deployment efficiency |

### Context Quality Score

```
Quality = (Relevance × Recency × Confidence) / 100

Where:
  Relevance: 0-100 (how applicable to current task)
  Recency: 0-100 (100 = this week, decay over time)
  Confidence: 0-100 (probe agreement score)

Target: Quality ≥ 60 for effective context
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-06 | Initial CONTEXT_PARTY protocol |

---

*CONTEXT_PARTY: Logistics wins wars. Context logistics wins scheduling. Remember what matters, find what you need, learn from what you did.*
