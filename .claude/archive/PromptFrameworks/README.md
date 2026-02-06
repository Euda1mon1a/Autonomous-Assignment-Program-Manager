# Prompt Frameworks for AI Agents

> **Last Updated:** 2025-12-26
> **Purpose:** Provide structured thinking scaffolds for AI agents working on the Residency Scheduler

---

## What Are Prompt Frameworks?

Prompt frameworks are **structured thinking templates** that help AI agents approach tasks systematically and avoid common pitfalls. They provide:

- **Cognitive scaffolds** for complex, multi-step tasks
- **Safety checklists** to prevent regulatory violations
- **Anti-pattern catalogs** to avoid common mistakes
- **Decision trees** for ambiguous situations
- **Reflection prompts** for continuous improvement

## Why Use These Frameworks?

Working on a medical residency scheduling system requires:

1. **Regulatory compliance** (ACGME rules are non-negotiable)
2. **Data safety** (HIPAA, PERSEC, OPSEC for military medical data)
3. **High reliability** (schedule failures impact patient care)
4. **Complex constraints** (80-hour rule, supervision ratios, N-1 contingency)
5. **Multi-step workflows** (research → plan → execute → verify)

These frameworks ensure agents **think before acting** and follow best practices.

---

## How Agents Should Use These Frameworks

### 1. Load the Appropriate Framework

Before starting a task, identify which framework applies:

- **Building a new feature?** → Use `RESEARCH_AND_BUILD.md`
- **Decomposing a complex task?** → Use `COMPLEX_TASK_DECOMPOSITION.md`
- **Unsure if an approach is safe?** → Check `ANTI_PATTERNS.md`

### 2. Follow the Framework Phases

Resist the urge to jump to implementation. Follow the phases:

```
Research → Plan → Execute → Verify → Reflect
```

### 3. Use Checkpoints

After each phase, pause and verify:

- ✅ Did I complete all steps in this phase?
- ✅ Am I confident in my understanding/plan/implementation?
- ✅ Do I need to loop back to a previous phase?

### 4. Consult Anti-Patterns Proactively

Before committing code, check `ANTI_PATTERNS.md`:

- Am I about to relax a safety constraint?
- Am I duplicating existing code?
- Am I skipping tests or migrations?
- Am I pushing directly to main?

### 5. Reflect and Adapt

After completing a task, use the Reflection phase to:

- Capture what worked well
- Identify what could be improved
- Update frameworks if you discovered a new pattern

---

## Available Frameworks

### Core Frameworks

| Framework | Purpose | When to Use |
|-----------|---------|-------------|
| **[RESEARCH_AND_BUILD.md](RESEARCH_AND_BUILD.md)** | Standard 5-phase workflow for features | Building new features, fixing complex bugs, refactoring |
| **[COMPLEX_TASK_DECOMPOSITION.md](COMPLEX_TASK_DECOMPOSITION.md)** | Break down large tasks into manageable pieces | Multi-day projects, unclear requirements, parallel workstreams |
| **[ANTI_PATTERNS.md](ANTI_PATTERNS.md)** | Common pitfalls and how to avoid them | Before committing, when uncertain, during code review |

### Integration with Existing Infrastructure

These frameworks complement:

- **[OPERATIONAL_MODES.md](../OPERATIONAL_MODES.md)** - When to use which operational mode
- **[SKILL_INDEX.md](../SKILL_INDEX.md)** - Which skills to invoke for specialized tasks
- **[CONSTITUTION.md](../CONSTITUTION.md)** - Core values and principles

---

## Example Usage

### Scenario: Implement Auto-Swap Matcher

**Agent's internal monologue:**

> "The user wants a swap auto-matcher. This is a complex feature with scheduling logic, database queries, ACGME validation, and frontend integration. I should use RESEARCH_AND_BUILD.md."

**Agent loads framework:**

```markdown
Phase 1: Research
- [ ] Understand swap types (1-to-1, absorb)
- [ ] Review existing swap code in `backend/app/services/swap_executor.py`
- [ ] Check ACGME constraints that apply to swaps
- [ ] Find similar matching algorithms in codebase
```

**Agent executes systematically**, checking off each research item before moving to planning.

---

## Framework Versioning

Frameworks evolve as we discover new patterns:

- **v1.0 (2025-12-26)**: Initial frameworks based on Claude.md and AI_RULES_OF_ENGAGEMENT.md
- Updates tracked in `.claude/History/`

---

## Contributing to Frameworks

If you discover a new pattern or anti-pattern:

1. Document it in `.claude/Scratchpad/`
2. Propose addition to relevant framework
3. Update version history

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ BEFORE CODING: Research → Plan                              │
│ DURING CODING: Execute incrementally, test after each step  │
│ BEFORE COMMIT: Verify tests pass, check anti-patterns       │
│ AFTER COMMIT: Reflect on what worked, update learnings      │
└─────────────────────────────────────────────────────────────┘
```

---

**Next Steps:**

1. Read [RESEARCH_AND_BUILD.md](RESEARCH_AND_BUILD.md) for the standard workflow
2. Familiarize yourself with [ANTI_PATTERNS.md](ANTI_PATTERNS.md)
3. Use [COMPLEX_TASK_DECOMPOSITION.md](COMPLEX_TASK_DECOMPOSITION.md) for multi-phase projects
