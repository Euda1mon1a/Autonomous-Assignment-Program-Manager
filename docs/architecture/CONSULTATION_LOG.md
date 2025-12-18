# Expert Consultation Log

> **Purpose:** Track all LLM consultations, their outcomes, and lessons learned.
> **Maintained by:** Claude (Primary Development Agent)
> **Protocol:** See [Expert Consultation Protocol](./expert-consultation-protocol.md)

---

## Quick Stats

| Metric | All Time | Last 30 Days |
|--------|----------|--------------|
| Total Consultations | 0 | 0 |
| Actionable Rate | - | - |
| Average Resolution Time | - | - |

*Stats update automatically based on logged entries below.*

---

## Consultation Entries

### Template for New Entries

```markdown
---

## C-[XXX]: [Brief Title]

**Date:** YYYY-MM-DD
**Session:** [Session identifier or PR number]
**Advisor(s):** [ChatGPT / Gemini / Perplexity / Multiple]
**Category:** [Architecture / Debugging / Best Practices / Security / Performance]
**Trigger:** [Why consultation was initiated]

### The Question

[Brief summary of what was asked]

### Advisor Response(s)

**[Advisor Name]:**
> [Key points from response]

### Evaluation

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Applicability | | |
| Correctness | | |
| Feasibility | | |
| Elegance | | |
| Novelty | | |

### Decision

**Accepted:** [Yes / Partial / No]
**Rationale:** [Why this decision was made]

### Implementation

[What was actually implemented based on this consultation]

### Outcome

**Status:** [Success / Partial Success / Did Not Work / Pending]
**Impact:** [Measurable result if applicable]
**Lessons Learned:** [What we learned for future consultations]

---
```

---

## Log Entries

*No consultations logged yet. This log will grow as consultations occur.*

<!--
================================================================================
                        LOGGED CONSULTATIONS BEGIN BELOW
================================================================================
Add new entries above this comment, following the template.
Most recent entries should appear first (reverse chronological order).
-->

---

## Consultation Index by Category

### Architecture Decisions
*None yet*

### Debugging Assistance
*None yet*

### Best Practices
*None yet*

### Security Reviews
*None yet*

### Performance Optimization
*None yet*

---

## Advisor Performance Summary

### Claude (via claude.ai) - The Humanist
| Metric | Value |
|--------|-------|
| Total Consultations | 0 |
| Actionable Rate | - |
| Average Applicability | - |
| Specialties | User Empathy, Ethics, Communication, UX |

### ChatGPT 5.x Pro
| Metric | Value |
|--------|-------|
| Total Consultations | 0 |
| Actionable Rate | - |
| Average Applicability | - |
| Specialties | Architecture, API Design |

### Gemini 3.0 Pro
| Metric | Value |
|--------|-------|
| Total Consultations | 0 |
| Actionable Rate | - |
| Average Applicability | - |
| Specialties | Code Analysis, Performance |

### Perplexity Labs
| Metric | Value |
|--------|-------|
| Total Consultations | 0 |
| Actionable Rate | - |
| Average Applicability | - |
| Specialties | Current Best Practices, Research |

### Other Advisors
| Metric | Value |
|--------|-------|
| Total Consultations | 0 |
| Actionable Rate | - |

---

## Quarterly Reviews

### Q1 2025 Review
*Not yet conducted*

---

## Common Patterns & Lessons

### What Works Well
*To be populated based on experience*

### Common Pitfalls
*To be populated based on experience*

### Advisor Routing Guide
*Based on accumulated data, guidance on which advisor to use for which question types*

---

## Brittleness Log

> *"It will break, but I will review, consult you and we can incorporate."*

Track failures here. Each failure is a learning opportunity.

### Failure Entry Template
```markdown
### F-[XXX]: [Brief Description]

**Date:** YYYY-MM-DD
**Cascade/Task:** [Link to task document]
**Failure Mode:**
- [ ] Platform changed access rules
- [ ] Agent misinterpreted task
- [ ] Cascade timing issue
- [ ] Advisor hallucinated
- [ ] Other: [describe]

**What Happened:**
[Description of the failure]

**Root Cause:**
[Analysis after investigation]

**Adaptation Made:**
[How we updated the system in response]

**Status:** documented | analyzed | adapted | resolved
```

### Logged Failures
*None yet. The system is new. Failures will come, and we'll learn from them.*

---

## Agent Access Matrix Updates

Track changes to platform restrictions here.

| Date | Change | Discovered By | Adaptation |
|------|--------|---------------|------------|
| 2025-12-18 | Initial matrix documented | User | Baseline established |

### Current Matrix (as of 2025-12-18)
| Agent | ChatGPT | Perplexity | Gemini | Claude | Claude Code |
|-------|---------|------------|--------|--------|-------------|
| Comet | ✅ | ❌ | ✅ | ✅ | ✅ |
| Atlas | ❌ | ✅ | ✅ | ✅ | ✅ |
| User | ✅ | ✅ | ✅ | ✅ | ✅ |

*Update this table when platform restrictions change.*

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-18 | Claude | Initial log structure |
