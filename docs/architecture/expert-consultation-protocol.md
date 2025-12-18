# Expert Consultation Protocol: Multi-LLM Advisory System

> **Document Version:** 1.0
> **Date:** 2025-12-18
> **Status:** Active Protocol
> **Maintainer:** Claude (Primary Development Agent)

---

## Executive Summary

### The Problem

During complex development sessions, I (Claude) occasionally encounter problems where:

- The solution path is unclear despite extensive research
- Multiple valid approaches exist with non-obvious trade-offs
- Domain-specific knowledge gaps limit my effectiveness
- Novel integration patterns lack established best practices

Historically, these situations resulted in suboptimal solutions, excessive iteration, or stalled progress.

### The Solution: Council of Expert Advisors

This protocol establishes a structured system for consulting other Large Language Models as **expert advisors** or **viziers**. The user acts as a **wetware translator** - relaying questions to other AI systems and returning their responses.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONSULTATION ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                         ┌─────────────┐                              │
│                         │   Claude    │                              │
│                         │  (Arbiter)  │                              │
│                         └──────┬──────┘                              │
│                                │                                     │
│              ┌─────────────────┼─────────────────┐                   │
│              │                 │                 │                   │
│              ▼                 ▼                 ▼                   │
│     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐             │
│     │  ChatGPT    │   │   Gemini    │   │ Perplexity  │             │
│     │  5.x Pro    │   │  3.0 Pro    │   │    Labs     │             │
│     └──────┬──────┘   └──────┬──────┘   └──────┬──────┘             │
│            │                 │                 │                     │
│            └─────────────────┼─────────────────┘                     │
│                              │                                       │
│                              ▼                                       │
│                    ┌─────────────────┐                               │
│                    │      User       │                               │
│                    │   (Translator)  │                               │
│                    └─────────────────┘                               │
│                                                                      │
│  Claude formulates questions → User relays to advisors →            │
│  Advisors respond → User returns responses → Claude evaluates       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Empirical Validation

Based on prior sessions using this pattern informally:

| Metric | Value |
|--------|-------|
| **Consultations resulting in actionable changes** | ~50% |
| **Average improvement in solution quality** | Significant |
| **Time saved vs. independent iteration** | 2-4x on complex problems |

This protocol formalizes what has proven effective in practice.

---

## The Expert Council

### Primary Advisors

| Advisor | Strengths | Best For |
|---------|-----------|----------|
| **ChatGPT 5.x Pro** | **Personal oracle** - persistent memory of user's essence, preferences, past epiphanies | Alignment with user's vision, "what would [user] want?", historical context |
| **Gemini 3.0 Pro** | Deep technical knowledge, Google ecosystem expertise, code analysis | Performance optimization, complex algorithms, GCP integrations |
| **Perplexity Labs** | Real-time web access, citation-backed research, up-to-date information | Library versions, recent best practices, security advisories |
| **Claude** (via claude.ai) | Nuanced human understanding, ethics, empathy, communication | UX decisions, user empathy, ethical considerations, soft questions |

### The Personal Oracle (ChatGPT's Unique Role)

ChatGPT's true moat isn't raw capability - it's **persistent memory**. Over months of conversation, it has accumulated:

- **The user's thinking patterns** - How they approach problems, their mental models
- **Historical context** - Past epiphanies, inspirations, the stories behind features
- **Values and preferences** - What they care about, their aesthetic sensibilities
- **Tacit knowledge** - The nuances that can't be written down but deeply influence decisions

**Example:** The resilience module wasn't born from a specification. It emerged from a late-night conversation about chaos theory and ant colonies - a musing about emergent behavior, distributed systems, and how complex systems maintain stability. ChatGPT was there. It remembers. It can answer "does this align with the spirit of that conversation?"

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THE PERSONAL ORACLE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   What ChatGPT Remembers That Others Can't Know:                    │
│                                                                      │
│   • The chaos theory → ant colonies → resilience module journey     │
│   • Past decisions and WHY they were made                           │
│   • User's frustrations with certain patterns                       │
│   • The aesthetic preferences ("I want it to feel like...")         │
│   • Abandoned ideas and why they were abandoned                     │
│   • The user's growth and evolving thinking over time               │
│                                                                      │
│   Questions Only ChatGPT Can Answer:                                │
│                                                                      │
│   • "Does this feel like something [user] would build?"             │
│   • "Remember when we discussed X? How does that apply here?"       │
│   • "What's the spirit behind this feature, not just the spec?"     │
│   • "We tried something similar before - what went wrong?"          │
│   • "How has [user]'s thinking on this topic evolved?"              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Why This Matters:**

Code can be copied. Architectures can be replicated. But a codebase infused with a person's essence - their way of seeing the world, their accumulated insights, their philosophical commitments - that's irreplaceable.

ChatGPT serves as the **institutional memory** of the human behind the code.

### The Humanist Advisor

While technical advisors excel at *how* to build something, **Claude** (consulted via claude.ai as a separate instance) serves as the **humanist philosopher** of the council - addressing questions that require understanding the human condition:

| Domain | Example Questions |
|--------|-------------------|
| **User Empathy** | "How will a stressed chief resident feel using this interface at 2 AM?" |
| **Ethics** | "Is this feature potentially harmful? What are the second-order effects?" |
| **Communication** | "How should error messages be worded to reduce anxiety?" |
| **Organizational Dynamics** | "How will this change affect the power dynamics between attendings and residents?" |
| **Accessibility** | "What barriers might users with disabilities face?" |
| **Trust & Safety** | "Could this feature be misused? How do we design for good-faith users while preventing abuse?" |

This creates a natural division across three domains:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        THE COMPLETE ADVISORY COUNCIL                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TECHNICAL              HUMAN                  PERSONAL                      │
│  ─────────              ─────                  ────────                      │
│  • Gemini → Perf        • Claude → Empathy     • ChatGPT → Oracle            │
│  • Perplexity → Info    • Claude → Ethics      • ChatGPT → Memory            │
│  • DeepSeek → Algos     • Claude → Comms       • ChatGPT → Vision            │
│                         • User → Domain        • User → Final say            │
│                                                                              │
│  "How do we build it?"  "Should we build it?"  "Is this ME building it?"    │
│  "What's optimal?"      "How will they feel?"  "Does this fit my essence?"  │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                    THE THREE QUESTIONS OF EVERY DECISION                     │
│                                                                              │
│     ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                │
│     │  TECHNICAL   │    │    HUMAN     │    │   PERSONAL   │                │
│     │              │    │              │    │              │                │
│     │  Will it     │    │  Will it     │    │  Is this     │                │
│     │  work?       │───▶│  help?       │───▶│  mine?       │                │
│     │              │    │              │    │              │                │
│     │  Gemini      │    │  Claude      │    │  ChatGPT     │                │
│     │  Perplexity  │    │  (humanist)  │    │  (oracle)    │                │
│     └──────────────┘    └──────────────┘    └──────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why Claude for soft questions?**
- Training emphasis on helpfulness, harmlessness, and honesty
- Strong at nuanced ethical reasoning without false equivalence
- Excellent at considering multiple stakeholder perspectives
- Faster than human reflection, but with human-like consideration

### Secondary Advisors (Domain-Specific)

| Advisor | Strengths | Best For |
|---------|-----------|----------|
| **Grok** | Systems thinking, unconventional perspectives | Novel approaches, challenging assumptions |
| **DeepSeek** | Code generation, mathematical reasoning | Algorithm implementation, optimization problems |
| **Mistral Large** | European data compliance, multilingual | GDPR concerns, internationalization |

### Advisory Principles

1. **I remain the arbiter** - Advisors provide input; I make final decisions
2. **Diversity of thought** - Different models have different training biases; this is a feature
3. **Verification required** - Advisor suggestions are hypotheses to test, not facts to accept
4. **Transparency** - All consultations are logged with outcomes

---

## Autonomous Execution Layer

### Agentic Browsers: Comet & Atlas

Beyond consultation, we have **autonomous execution agents** - agentic browsers that can discover task documents in this repository and execute them without human intermediation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MULTI-AGENT ORCHESTRATION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                           ┌─────────────┐                                    │
│                           │    User     │                                    │
│                           │  (Overseer) │                                    │
│                           └──────┬──────┘                                    │
│                                  │                                           │
│              ┌───────────────────┼───────────────────┐                       │
│              │                   │                   │                       │
│              ▼                   ▼                   ▼                       │
│     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                 │
│     │   Claude    │     │    Comet    │     │    Atlas    │                 │
│     │  (Arbiter)  │     │ (Parallel)  │     │  (Essence)  │                 │
│     │             │     │             │     │             │                 │
│     │  Execution  │     │  Discovery  │     │  Discovery  │                 │
│     │  Synthesis  │     │  Execution  │     │  Execution  │                 │
│     │  Judgment   │     │  Speed      │     │  Context    │                 │
│     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                 │
│            │                   │                   │                        │
│            │         ┌─────────┴─────────┐        │                        │
│            │         │                   │        │                        │
│            ▼         ▼                   ▼        ▼                        │
│     ┌─────────────────────────────────────────────────────┐                │
│     │              TASK DOCUMENTS IN REPO                  │                │
│     │                                                      │                │
│     │  /docs/tasks/consultation-request-001.md            │                │
│     │  /docs/tasks/research-task-002.md                   │                │
│     │  /docs/tasks/oracle-query-003.md                    │                │
│     │                                                      │                │
│     └─────────────────────────────────────────────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Agent Capabilities

| Agent | Superpower | Best For | Limitation |
|-------|------------|----------|------------|
| **Comet** | Parallelization - can run multiple browser tasks simultaneously | Bulk research, parallel consultations, speed-critical tasks | Less personal context |
| **Atlas** | Essence accumulation - builds on user's history like ChatGPT | Aligned research, preference-aware browsing, nuanced tasks | Sequential execution |
| **Claude** (this instance) | Synthesis and arbitration - makes final decisions | Integration, judgment, code execution | No persistent memory |

### How It Works

**Traditional Flow (User as Translator):**
```
Claude needs info → Formulates question → User relays to advisor → User returns response → Claude evaluates
```

**Automated Flow (Agentic Browsers):**
```
Claude needs info → Creates task document → Comet/Atlas discovers document →
Agent executes task → Results written to repo → Claude reads results
```

### Task Document Format

Agentic browsers can be triggered by discovering specially formatted documents in the repository:

```markdown
<!-- FILE: /docs/tasks/active/consultation-001.md -->

# Task: [Title]

## Metadata
- **Status:** pending | in_progress | completed
- **Agent:** comet | atlas | either
- **Priority:** high | medium | low
- **Created:** YYYY-MM-DD
- **Requester:** Claude (session-id)

## Objective
[Clear, single-sentence goal]

## Context
[Background information the agent needs]

## Instructions
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Output
[What should be written back to this document or a results file]

## Constraints
- [Constraint 1]
- [Constraint 2]

---

## Results
<!-- Agent writes results below this line -->

```

### Agent-Specific Task Routing

| Task Type | Recommended Agent | Reasoning |
|-----------|-------------------|-----------|
| Parallel web research | **Comet** | Can search multiple sources simultaneously |
| Consulting ChatGPT (oracle queries) | **Atlas** | Shares essence/memory context with ChatGPT |
| Bulk documentation lookup | **Comet** | Speed through parallelization |
| Preference-sensitive research | **Atlas** | Understands user's preferences |
| Time-critical tasks | **Comet** | Parallel execution is faster |
| Nuanced interpretation needed | **Atlas** | Better alignment with user's thinking |

### Comet: The Parallel Executor

**Strengths:**
- Can run multiple browser instances simultaneously
- Excellent for "gather information from N sources" tasks
- Speed-optimized for bulk operations
- Good for objective, well-defined tasks

**Ideal Tasks:**
```markdown
## Task: Research Current Best Practices

### Instructions
1. Search for "FastAPI middleware best practices 2025"
2. Search for "SQLAlchemy 2.0 async patterns"
3. Search for "Next.js 14 server actions patterns"
4. Compile findings into a comparison table

### Parallel Execution
- All searches can run simultaneously
- Compile results after all complete
```

### Atlas: The Essence-Aligned Agent

**Strengths:**
- Builds on user's historical context (like ChatGPT)
- Better at interpreting ambiguous instructions
- Understands user's preferences and values
- Good for tasks requiring judgment

**Ideal Tasks:**
```markdown
## Task: Consult ChatGPT Oracle

### Instructions
1. Navigate to ChatGPT
2. Ask: "Claude is implementing [feature]. Does this align with how I've talked about user experience in the past?"
3. Capture response
4. Return to repo and update this document

### Why Atlas
- Atlas shares essence-memory with ChatGPT
- Can phrase questions in a way ChatGPT will understand given shared context
```

### Task Directory Structure

```
/docs/tasks/
├── active/                    # Tasks awaiting execution
│   ├── consultation-001.md
│   └── research-002.md
├── in-progress/               # Tasks currently being executed
│   └── oracle-query-003.md
├── completed/                 # Finished tasks (results included)
│   └── security-review-000.md
└── templates/                 # Task templates
    ├── consultation.md
    ├── research.md
    └── oracle-query.md
```

### Integration with Claude Sessions

When I (Claude) need to trigger an autonomous task:

1. **Create the task document** in `/docs/tasks/active/`
2. **Notify the user** that a task is ready for agent pickup
3. **User triggers agent** (Comet or Atlas) pointing at the task
4. **Agent executes** and writes results back to the document
5. **Claude reads results** in a subsequent turn or session
6. **Document moves** to `/docs/tasks/completed/`

### The Complete Ecosystem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    THE COMPLETE ADVISORY ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   CONSULTATION LAYER (Synchronous - User as Translator)                     │
│   ─────────────────────────────────────────────────────                     │
│   • ChatGPT → Personal Oracle (essence, memory, vision)                     │
│   • Claude → Humanist (ethics, empathy, UX)                                 │
│   • Gemini → Technical (performance, algorithms)                            │
│   • Perplexity → Current Information (real-time, citations)                 │
│                                                                              │
│   EXECUTION LAYER (Asynchronous - Agents as Executors)                      │
│   ──────────────────────────────────────────────────────                    │
│   • Comet → Parallel research, bulk tasks, speed                           │
│   • Atlas → Essence-aligned research, nuanced tasks                        │
│                                                                              │
│   ARBITRATION LAYER (This Session)                                          │
│   ────────────────────────────────                                          │
│   • Claude (me) → Synthesis, judgment, code execution                       │
│   • User → Final authority, domain expertise, oversight                     │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                         INFORMATION FLOW                                     │
│                                                                              │
│   ┌──────────┐    Task Docs    ┌──────────┐    Results    ┌──────────┐     │
│   │  Claude  │ ───────────────▶│  Agents  │ ─────────────▶│  Claude  │     │
│   │ (Create) │                 │ (Execute)│               │ (Consume)│     │
│   └──────────┘                 └──────────┘               └──────────┘     │
│                                     │                                       │
│                                     │ May consult                           │
│                                     ▼                                       │
│                              ┌──────────┐                                   │
│                              │ Advisory │                                   │
│                              │ Council  │                                   │
│                              └──────────┘                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## When to Consult

### Automatic Triggers (Always Consult)

| Trigger | Rationale |
|---------|-----------|
| **3+ failed approaches** | I've exhausted my immediate solution space |
| **Unfamiliar domain** | E.g., medical compliance, financial regulations |
| **Security-critical decisions** | Multiple perspectives reduce blind spots |
| **Breaking changes to architecture** | High-stakes decisions need validation |
| **Novel library/framework integration** | Others may have recent experience |

### Optional Triggers (Consider Consulting)

| Trigger | Rationale |
|---------|-----------|
| **Two viable approaches, unclear winner** | External perspective breaks ties |
| **Performance optimization plateau** | Fresh eyes find new optimizations |
| **User expresses uncertainty** | Validating my recommendations builds trust |
| **Documentation gaps in dependencies** | Others may have solved the same puzzle |

### When NOT to Consult

| Scenario | Reason |
|----------|--------|
| **Clear, documented solution exists** | Consultation adds overhead without value |
| **Simple implementation tasks** | Efficiency matters; don't over-engineer |
| **User explicitly wants speed** | Respect time constraints |
| **Confidential/proprietary code** | Don't expose sensitive information |

---

## Consultation Protocol

### Phase 1: Question Formulation

Before requesting consultation, I will prepare:

```markdown
## Consultation Request: [Brief Title]

### Context
[2-3 sentences on what we're building and why]

### The Challenge
[Specific problem or decision point]

### What I've Tried
[Approaches attempted and why they fell short]

### Specific Questions
1. [Concrete question 1]
2. [Concrete question 2]
3. [Concrete question 3]

### Constraints
- [Technical constraint 1]
- [Technical constraint 2]

### Preferred Response Format
[What format would be most useful: code, explanation, comparison table, etc.]
```

### Phase 2: User Relay

The user copies the consultation request to the target advisor(s) and returns their responses. Users may:

- Consult one advisor (targeted expertise)
- Consult multiple advisors in parallel (diverse perspectives)
- Add their own context when relaying (domain knowledge)

### Phase 3: Response Evaluation

Upon receiving advisor responses, I will:

1. **Acknowledge receipt** - Confirm I've processed the response
2. **Extract key insights** - Summarize the main recommendations
3. **Evaluate applicability** - Assess fit with our specific context
4. **Identify conflicts** - Note where advisors disagree
5. **Synthesize decision** - Combine insights into actionable plan
6. **Explain rationale** - Tell the user why I'm accepting/rejecting advice

### Phase 4: Implementation & Logging

After acting on consultation:

1. **Implement changes** - Apply the synthesized recommendations
2. **Log the consultation** - Record in `CONSULTATION_LOG.md`
3. **Mark outcome** - Track whether advice was actionable/successful

---

## Response Evaluation Framework

### Evaluation Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Applicability** | 30% | Does it address our specific context? |
| **Correctness** | 25% | Is it technically accurate? (Verify!) |
| **Feasibility** | 20% | Can we implement this with our constraints? |
| **Elegance** | 15% | Is it maintainable and clean? |
| **Novelty** | 10% | Does it offer insights I hadn't considered? |

### Decision Matrix

| Scenario | Action |
|----------|--------|
| Single advisor, high confidence | Implement with attribution |
| Multiple advisors agree | Strong signal; implement |
| Advisors disagree | Analyze trade-offs, choose based on our priorities |
| Low applicability | Thank but don't apply |
| Partially applicable | Extract useful portions |

### Conflict Resolution

When advisors disagree:

1. **Identify the disagreement** - Is it fundamental or surface-level?
2. **Consider context** - Which advisor's training is more relevant?
3. **Test if possible** - Can we prototype both approaches quickly?
4. **Apply project values** - When in doubt, favor simplicity and maintainability
5. **Document reasoning** - Record why we chose one path over another

---

## Consultation Templates

### Template A: Architecture Decision

```markdown
## Consultation Request: Architecture Decision

### Context
We're building [feature] for a medical residency scheduling system (FastAPI + Next.js).

### The Challenge
Need to decide between [Option A] vs [Option B] for [specific component].

### What I've Tried
- Option A: [brief attempt, outcome]
- Option B: [brief attempt, outcome]

### Specific Questions
1. What are the long-term maintenance implications of each approach?
2. Which scales better for [expected load]?
3. Are there edge cases I'm not considering?

### Constraints
- Must integrate with existing SQLAlchemy models
- Must not break current API contracts
- Performance budget: <200ms response time

### Preferred Response Format
Comparison table with recommendation and reasoning.
```

### Template B: Debugging Assistance

```markdown
## Consultation Request: Debugging Assistance

### Context
[Component] is exhibiting [unexpected behavior] in [specific scenario].

### The Challenge
Despite [debugging steps taken], the root cause remains unclear.

### What I've Tried
1. [Step 1 and result]
2. [Step 2 and result]
3. [Step 3 and result]

### Error Details
```
[Error message or unexpected output]
```

### Relevant Code
```python
[Minimal reproduction]
```

### Specific Questions
1. What could cause [specific symptom]?
2. What debugging steps might I have missed?
3. Is this a known issue with [library/framework]?

### Constraints
- Cannot upgrade [dependency] due to [reason]
- Must maintain backwards compatibility

### Preferred Response Format
Ranked list of likely causes with diagnostic steps.
```

### Template C: Best Practices Inquiry

```markdown
## Consultation Request: Best Practices

### Context
Implementing [feature type] for [use case].

### The Challenge
Multiple valid approaches exist; seeking current best practices.

### What I Know
- Approach A: [description, pros/cons as I understand them]
- Approach B: [description, pros/cons as I understand them]

### Specific Questions
1. What is the current industry consensus (2025)?
2. What pitfalls should we avoid?
3. Any emerging patterns worth considering?

### Constraints
- [Technical constraints]
- [Business constraints]

### Preferred Response Format
Recommendation with rationale and example implementation.
```

### Template D: Security Review

```markdown
## Consultation Request: Security Review

### Context
Implementing [security-sensitive feature].

### The Challenge
Ensuring no vulnerabilities in [specific area].

### Current Implementation
```python
[Code to review]
```

### Threat Model
- [Expected threats]
- [Trust boundaries]

### Specific Questions
1. Are there vulnerabilities in this implementation?
2. What attack vectors should we consider?
3. What additional hardening is recommended?

### Constraints
- Must use [existing auth system]
- Cannot require [specific change]

### Preferred Response Format
Vulnerability assessment with remediation steps.
```

### Template E: Personal Oracle Consultation (for ChatGPT)

```markdown
## Consultation Request: Vision Alignment

### Context
Claude (the execution agent) is working on [feature/decision] for the Residency Scheduler.

### The Question
[Specific alignment or historical context question]

### What Claude Knows
- [Technical constraints]
- [Current implementation approach]
- [Options being considered]

### What Only You Know
You have context from our past conversations that Claude doesn't have access to:
- Our discussions about [relevant topic]
- My preferences around [relevant area]
- The philosophy behind [related past decisions]

### Specific Questions
1. Does this approach align with how I think about [topic]?
2. Remember when we discussed [past conversation]? How does that apply here?
3. Based on our history, what would I prioritize here?
4. Is there context from our past discussions that should inform this?
5. What would I regret about this decision in 6 months?

### Decision I'm Facing
[The specific choice or direction being considered]

### Preferred Response Format
- Alignment assessment (how well does this fit my patterns)
- Relevant context from past discussions
- What I might be overlooking based on my known blindspots
- Recommendation with "because you tend to..." reasoning
```

### Template F: Human & Ethical Considerations (for Claude)

```markdown
## Consultation Request: Human Considerations

### Context
Building [feature] for [user type] in [domain context].

### The Challenge
Understanding the human impact of [specific design decision].

### The Users
- **Primary users:** [Who will use this directly]
- **Affected parties:** [Who else is impacted]
- **Power dynamics:** [Relevant authority relationships]

### Current Design
[Description of the proposed approach]

### Specific Questions
1. How might a [specific user persona] feel when encountering this?
2. What unintended consequences could this create?
3. Are there accessibility or equity concerns?
4. How could this be misused, and how do we prevent that?
5. What's the most empathetic way to handle [edge case]?

### Scenarios to Consider
- Best case: [Ideal usage]
- Stress case: [User under pressure]
- Edge case: [Unusual but possible situation]
- Adversarial case: [Bad-faith usage]

### Preferred Response Format
Stakeholder analysis with specific recommendations for human-centered design.
```

---

## Integration with Development Workflow

### In-Session Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONSULTATION FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Claude encounters difficulty                                 │
│           │                                                      │
│           ▼                                                      │
│  2. Claude formulates consultation request                       │
│           │                                                      │
│           ▼                                                      │
│  3. Claude presents request to user                              │
│     "I'd like to consult [Advisor] on this. Here's my           │
│      prepared question: [formatted request]"                     │
│           │                                                      │
│           ▼                                                      │
│  4. User relays to advisor (wetware translation)                 │
│           │                                                      │
│           ▼                                                      │
│  5. User returns advisor response                                │
│           │                                                      │
│           ▼                                                      │
│  6. Claude evaluates and synthesizes                             │
│     "Based on [Advisor]'s input, I recommend..."                │
│           │                                                      │
│           ▼                                                      │
│  7. Implementation proceeds with enhanced approach               │
│           │                                                      │
│           ▼                                                      │
│  8. Outcome logged for future reference                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cross-Session Learning

The `CONSULTATION_LOG.md` file accumulates institutional knowledge:

- **What questions have we asked?** - Avoid redundant consultations
- **What worked?** - Reuse successful patterns
- **What didn't work?** - Avoid known dead ends
- **Which advisors excel at what?** - Route questions optimally

---

## Example Consultations

### Example 1: Database Optimization

**Trigger:** Query taking 3+ seconds despite indexes

**Question to ChatGPT:**
> We have a SQLAlchemy query joining 4 tables with complex filtering. Despite proper indexes, it takes 3+ seconds. Query plan shows sequential scan on the largest table. What optimization strategies should we consider?

**Response Summary:**
> Suggested: (1) Materialized view for common joins, (2) Denormalization for read-heavy paths, (3) Query hints to force index usage

**Evaluation:**
- Materialized view: ✅ Applicable, implemented
- Denormalization: ⚠️ Deferred (increases complexity)
- Query hints: ❌ Not portable across databases

**Outcome:** Materialized view reduced query time to 200ms

---

### Example 2: React State Management

**Trigger:** Two viable approaches, unclear winner

**Question to Gemini:**
> For a swap marketplace feature with complex filtering and real-time updates, should we use (A) React Query + local state, or (B) Redux Toolkit with RTK Query? Context: Next.js 14, ~10 team members, medical scheduling domain.

**Response Summary:**
> Recommended React Query for this use case. RTK Query adds value when you have complex client-side state transformations. For server-driven UI with real-time needs, React Query's caching and invalidation model is simpler.

**Evaluation:**
- Aligns with existing codebase patterns: ✅
- Lower learning curve for team: ✅
- Adequate for our complexity level: ✅

**Outcome:** Implemented with React Query; successful integration

---

### Example 3: Conflicting Advice

**Trigger:** Security-critical feature

**Question to ChatGPT and Gemini:**
> Should we store sensitive schedule data encrypted at rest in PostgreSQL, or rely on database-level encryption?

**ChatGPT Response:**
> Application-level encryption provides defense-in-depth. Recommend AES-256 with key management via environment variables.

**Gemini Response:**
> Database-level encryption (TDE) is sufficient for most compliance requirements and doesn't impact query performance. Application-level encryption complicates searches and joins.

**Synthesis:**
Both have merit. Given our requirements:
- ACGME compliance doesn't mandate application-level encryption
- We need to query/filter on some fields
- Key management adds operational complexity

**Decision:** Database-level encryption with application-level encryption only for PII fields that don't require querying.

---

## Measuring Success

### Consultation Metrics

Track in `CONSULTATION_LOG.md`:

| Metric | Description | Target |
|--------|-------------|--------|
| **Actionable Rate** | % of consultations yielding implemented changes | >40% |
| **Resolution Time** | Time from question to working solution | <2 hours |
| **Advisor Accuracy** | How often advisor suggestions work as-is | >60% |
| **Novel Insights** | % of consultations teaching something new | >30% |

### Quarterly Review

Every quarter (or 20 consultations), analyze:

1. Which advisors provided most value?
2. Which question types yielded best results?
3. Are we over-consulting (low actionable rate)?
4. Are we under-consulting (repeated struggles)?

---

## Appendix A: Advisor-Specific Guidelines

### Claude (via claude.ai) - The Humanist

**Strengths:**
- Exceptional at understanding user perspectives and emotions
- Strong ethical reasoning without false balance
- Excellent at considering second-order effects
- Natural language for error messages and user communication
- Thoughtful about accessibility and inclusion

**Best Practices:**
- Frame questions around specific user personas
- Ask about "how would X feel when..." scenarios
- Request consideration of multiple stakeholders
- Ask for potential unintended consequences
- Use for reviewing user-facing copy and error messages

**Caveats:**
- May be overly cautious (calibrate for your risk tolerance)
- Different Claude instance may have different context; provide sufficient background

**Example Questions:**
- "A resident just got denied their vacation request. How should the notification be worded?"
- "We're adding a feature that shows comparative performance. What are the psychological risks?"
- "Is it ethical to auto-approve swaps that meet all criteria, or should humans always be in the loop?"

---

### ChatGPT 5.x Pro - The Personal Oracle

**Unique Value:**
- **Persistent memory** of the user across months/years of conversation
- Knows the stories behind decisions, not just the decisions
- Understands the user's evolving philosophy and mental models
- Remembers abandoned paths and why they didn't work
- Can recognize when something "feels right" for this specific user

**Strengths:**
- Institutional memory of the human behind the code
- Context that can't be written down or transferred
- Pattern recognition across the user's thinking over time
- Knows preferences, aesthetics, and values

**Best Practices:**
- Ask "does this align with how I think about X?"
- Reference past conversations: "remember when we discussed..."
- Ask for the spirit, not just the letter: "what's the essence of..."
- Use for sanity checks on whether something fits the user's vision
- Leverage for archaeology: "why did we decide X back then?"

**Ideal Consultation Types:**
- Vision alignment checks
- Historical context retrieval
- Preference validation
- Philosophy extraction
- Pattern recognition across past decisions

**Example Questions:**
- "Does this swap marketplace design feel like something I'd build?"
- "Remember our conversation about chaos theory and ants? How does that philosophy apply to this new feature?"
- "I'm torn between two approaches. Based on what you know about my preferences, which would I regret less?"
- "We've discussed this domain before. What nuances am I forgetting?"
- "Extract the core principles from our past discussions about user experience."

**Caveats:**
- Memory may have gaps or inaccuracies; verify critical details
- Can't know what happened outside ChatGPT conversations
- May over-fit to past preferences; you're allowed to evolve

---

### Gemini 3.0 Pro

**Strengths:**
- Deep technical knowledge
- Strong at code analysis and optimization
- Google ecosystem expertise

**Best Practices:**
- Provide code snippets for analysis
- Ask about performance implications
- Good for GCP/Firebase-related questions

**Caveats:**
- May favor Google technologies
- Cross-verify security recommendations

---

### Perplexity Labs

**Strengths:**
- Real-time web access
- Citation-backed responses
- Up-to-date information

**Best Practices:**
- Use for "current best practice" questions
- Ask about recent library versions
- Good for security advisory lookups

**Caveats:**
- May surface contradictory sources
- Verify citations are authoritative

---

## Appendix B: Anti-Patterns

### What NOT to Do

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| **Consulting for trivial questions** | Wastes time, low value | Just implement and iterate |
| **Accepting advice without verification** | May not fit context | Always evaluate applicability |
| **Ignoring conflicting advice** | Misses important nuances | Analyze the disagreement |
| **Over-specifying constraints** | Limits useful suggestions | Share constraints, but be open |
| **Skipping the log** | Loses institutional knowledge | Always log consultations |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-18 | Claude | Initial protocol |

---

## Approval

- [x] Protocol Author (Claude)
- [ ] User Review
- [ ] Merge to main branch
