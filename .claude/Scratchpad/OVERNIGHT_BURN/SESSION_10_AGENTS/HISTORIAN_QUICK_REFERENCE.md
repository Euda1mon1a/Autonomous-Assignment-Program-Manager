# HISTORIAN Quick Reference Card

> **For ORCHESTRATOR & QA_TESTER**
> Print this, use it when making HISTORIAN decisions

---

## When to Invoke HISTORIAN

**Quick Test:** Score the session (0-3 points each):

```
Domain Insight:      [0=None  1=Minor  2=Clear  3=Paradigm]
Architecture:        [0=None  1=Minor  2=Scaling  3=New Capability]
Process:             [0=None  1=Refinement  2=Pattern  3=Reusable]
Meta-Learning:       [0=None  1=Tactical  2=Cognitive  3=About Learning]

TOTAL: ___ / 12

≥ 3 points? YES → Invoke HISTORIAN
            NO → Skip (use handoff doc instead)
```

---

## Six Chronicle Patterns

### Pattern 1: The Revelation
**When:** Mystery → Investigation → Discovery
**Example:** Session 014 (Block 10 empty, why?)
**Structure:** Anomaly → Clue chain → Breakthrough → Implication

### Pattern 2: The Paradigm Shift
**When:** Habit → Question → New Understanding
**Example:** Session 016 (Parallelization is free!)
**Structure:** Established practice → Cognitive dissonance → Realization → Validation

### Pattern 3: The Gap-Filling
**When:** Excellent architecture + Missing ergonomics
**Example:** Session 025 (Signal amplification)
**Structure:** Affirm excellence → Identify gap → Parallel fixes → New capability

### Pattern 4: The Enterprise Scale
**When:** Unprecedented coordination/metrics achieved
**Example:** Session 020 (26 agents, 6.0x parallelization)
**Structure:** Mission → Reconnaissance → Phased execution → Metrics

### Pattern 5: The Data Integrity
**When:** System works, but data is wrong
**Example:** Session 014 (Only odd blocks exist)
**Structure:** Normal op → Anomaly → Investigation → Root cause → Horror → Fix

### Pattern 6: The Cross-Disciplinary
**When:** Foreign domain solves your problem
**Example:** Burnout SIR model (epidemiology → scheduling)
**Structure:** Problem → Analogy → Adaptation → Validation

---

## Six Narrative Techniques

1. **Emotional Arc** - Include challenge, frustration, insight, relief (7-beat)
2. **Evidence First** - Present clues sequentially, reach conclusion naturally
3. **Concrete Examples** - Use actual names, numbers, specific code
4. **Trade-Offs** - Acknowledge what we gained AND what we accepted
5. **Metaphors** - Use clinical, infrastructure, chemistry, biology sources
6. **Failure Docs** - Include what didn't work and why

---

## Quality Gate Checklist (Pre-Publication)

**Content (8 items):**
- [ ] Non-technical readers understand it
- [ ] Context is self-contained
- [ ] Narrative arc present (beginning-middle-end)
- [ ] Emotional beats included
- [ ] Failures mentioned (not just successes)
- [ ] Implications clear
- [ ] Trade-offs acknowledged
- [ ] Concrete examples used

**Structure (5 items):**
- [ ] Title is evocative (not just topic)
- [ ] Metadata accurate (date, duration, participants)
- [ ] Section headings clear
- [ ] Transitions logical
- [ ] Closing is reflective

**Accuracy (5 items):**
- [ ] Facts verified against git log
- [ ] Quotes exact or paraphrased
- [ ] Attribution correct
- [ ] Code examples actual
- [ ] Impact claims supported

**PASS if ≥18/20 items checked**

---

## Delegation Template (Minimal)

When sending session to HISTORIAN:

```
Session: 026
Title: The [Revelation/Pattern/Discovery]
Outcome: Success / Partial / Blocked

Challenge: [What problem?]

Journey: [What happened? Tried? Breakthrough?]

Resolution: [What did we ultimately do?]

Key Insights:
- Domain: [Something about the domain]
- Architecture: [Something about the system]
- Process: [Something about how we work]
- Meta: [Something about learning]

Artifacts: PR #XXX, Commits: abc123d, Files: [list]
```

---

## Selection Scoring Examples

### Example 1: Block Revelation (Session 014)
- Domain: 3 (ACGME blocks, clinical semantics)
- Arch: 3 (UI masking data integrity)
- Process: 1 (standard debugging)
- Meta: 2 (false hypothesis, pivot moment)
- **Score: 9 → YES, invoke HISTORIAN**

### Example 2: Routine Bug Fix
- Domain: 0 (no domain insight)
- Arch: 0 (isolated fix)
- Process: 0 (standard procedure)
- Meta: 0 (nothing new learned)
- **Score: 0 → NO, skip HISTORIAN**

### Example 3: New Feature Completed
- Domain: 1 (minor domain requirement)
- Arch: 1 (standard implementation)
- Process: 0 (expected work)
- Meta: 0 (no learning)
- **Score: 2 → NO, skip HISTORIAN**

### Example 4: Paradigm Shift (Session 016)
- Domain: 0 (not domain-specific)
- Arch: 2 (parallelization insight)
- Process: 3 (habit pattern, reusable)
- Meta: 3 (knowing vs applying, AI cognition)
- **Score: 8 → YES, invoke HISTORIAN**

---

## Session vs. Chronicle Guide

| Aspect | Handoff Doc | HISTORIAN Chronicle |
|--------|------------|-------------------|
| **When** | Every session | Only poignant (≥3 score) |
| **What** | What got done | Why decisions matter |
| **Who writes** | Session agent | HISTORIAN |
| **Audience** | Developers | Dr. Montgomery + all audiences |
| **Tone** | Technical | Narrative |
| **Length** | 200-500 words | 1,000-2,000 words |
| **Example** | SESSION_025_HANDOFF.md | SESSION_014_THE_BLOCK_REVELATION.md |

---

## ORCHESTRATOR Decision Flow

```
Session ends
    ↓
[Score dimensions: Domain, Arch, Process, Meta]
    ↓
Score < 3?
    ├─ YES → Create handoff doc only
    └─ NO → Continue...
    ↓
Known pattern?
    ├─ YES → Note pattern type
    └─ NO → Identify unique pattern
    ↓
[Prepare delegation context]
    ↓
/invoke HISTORIAN "Session XXX: [Title]"
    ├─ Context provided
    ├─ Pattern noted
    ├─ Artifacts linked
    └─ Key insights listed
    ↓
HISTORIAN produces: SESSION_XXX_TITLE.md
    ↓
QA_TESTER validates (quality gate checklist)
    ↓
META_UPDATER links to technical docs
    ↓
Chronicle becomes institutional memory
```

---

## Seven Questions to Ask

**Before invoking HISTORIAN:**

1. Did we learn something surprising about the domain?
2. Did we make a decision future-us will wonder about?
3. Did we struggle with complexity that revealed system limits?
4. Will Dr. Montgomery need context to understand this choice?
5. Is this a pattern that will repeat?
6. What would it cost to rediscover this?
7. Will someone need this answer in six months?

**If 2+ answers are YES → Invoke HISTORIAN**

---

## Tone Checklist

HISTORIAN should sound:

- [ ] **Accessible** - No jargon without explanation
- [ ] **Honest** - Includes failures and dead ends
- [ ] **Narrative** - Tells a story, not a list
- [ ] **Technical** - Precise when it matters
- [ ] **Reflective** - Philosophical note at end
- [ ] **Human** - Shows emotion and struggle

**Pass if 5/6 checked**

---

## Common Mistakes to Avoid

| Mistake | How to Spot | Fix |
|---------|-----------|-----|
| Over-technical | Jargon requires lookup | Explain with analogy |
| Blame language | "We were wrong" | "We learned" |
| No emotion | Reads like log | Add struggle moments |
| Too long | > 2,500 words | Split into two chronicles |
| Missing failures | Only successes shown | Include dead ends |
| Vague implications | "This was important" | Spell out why it matters |
| No concrete examples | Generic statements | Use actual names/numbers |

---

## Quick Links

- **Full specification:** `agents-historian-enhanced.md` (1,195 lines)
- **Investigation summary:** `SEARCH_PARTY_INVESTIGATION_SUMMARY.md`
- **Example chronicles:** `.claude/Scratchpad/histories/`
  - SESSION_014_THE_BLOCK_REVELATION.md
  - SESSION_016_THE_PARALLELIZATION_REVELATION.md
  - HISTORIAN_SESSION_020.md
  - SIGNAL_AMPLIFICATION_SESSION_025.md

---

## Remember

> HISTORIAN isn't about documenting everything.
> It's about preserving the poignant moments.
> The ones that reveal the system's true nature.
> The ones future-us will be grateful for.

---

*Last Updated: 2025-12-30*
*Use with: agents-historian-enhanced.md (v2.0.0)*
