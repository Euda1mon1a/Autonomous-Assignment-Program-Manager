# Hybrid Model Orchestration (FUTURE - CONCEPT ONLY)

> **Status:** CONCEPT - For future evaluation
> **Created:** 2025-12-26
> **Prerequisite:** Qwen Code installed and validated independently

---

## Concept Overview

Three-tier architecture separating strategic planning from tactical execution:

```
YOU
  │
  ↓ (strategic planning, conversation)
CLAUDE CODE WEB (Opus 4.5) ← Planning layer
  │
  ↓ (execution handoff)
ANTIGRAVITY IDE (Opus 4.5) ← Tactician with integrated terminal
  │
  │  Spawns/manages Qwen terminals:
  │
  ├──► qwen terminal 1: pytest backend/tests/
  ├──► qwen terminal 2: npm run lint
  ├──► qwen terminal 3: ruff check . --fix
  └──► qwen terminal 4: grep -r 'pattern' backend/
```

**Roles:**
- **Claude Code Web**: Strategic planning with user, high-level decomposition
- **Antigravity Opus 4.5**: Tactical execution, manages Qwen squad
- **Qwen instances**: Skill-blind operators for parallelized grunt work

---

## Rationale

| Factor | Single Claude | Hybrid (Opus + Qwen Squad) |
|--------|---------------|----------------------------|
| **Cost** | Pay per token | Opus for reasoning, Qwen free tier for grunt work |
| **Speed** | Serial execution | 4 parallel Qwen instances (38-80 tok/s) |
| **Parallelism** | 1 task at a time | 4+ concurrent tasks |
| **Reasoning** | Deep, consistent | Opus handles complex; Qwen handles simple |

---

## Critical Constraint: Skill Compatibility

**Qwen cannot use `.claude/skills/`** - this is the key architectural constraint.

### Skill-Required Tasks (Opus Only)

Tasks requiring domain knowledge encoded in skills:

- ACGME compliance validation (`acgme-compliance`)
- Security audits (`security-audit`)
- Database migrations (`database-migration`)
- Constraint validation (`constraint-preflight`)
- Code review synthesis (`code-review`)
- Safe schedule generation (`safe-schedule-generation`)
- Swap execution (`swap-management`)

### Skill-Free Tasks (Qwen Squad)

Simple, self-contained operations:

- `pytest backend/tests/`
- `npm test`, `npm run lint`, `npm run type-check`
- `ruff check . --fix && ruff format .`
- `mypy backend/app/`
- grep/glob exploration
- Simple file scaffolding
- Git status/diff/log

---

## Task Routing Logic

```
Incoming Task
     │
     ▼
┌─────────────────────┐
│ Needs domain skill? │
└─────────────────────┘
     │
 YES │         NO
     │          │
     ▼          ▼
  OPUS 4.5   QWEN SQUAD
  (Skills)   (Tools only)
```

---

## Example Workflows

### Parallel Test Execution

```
Claude Web: "We need to verify all tests pass before the PR"
     ↓
Antigravity Opus: Decomposes, spawns Qwen terminals

→ Qwen terminal 1: cd backend && pytest -v
→ Qwen terminal 2: cd frontend && npm test
→ Qwen terminal 3: cd frontend && npm run type-check
→ Qwen terminal 4: cd frontend && npm run lint

← Antigravity synthesizes results, applies code-review skill if failures
← Reports summary to Claude Web for user communication
```

### Bulk Linting/Formatting

```
Claude Web: "Clean up the codebase before release"
     ↓
Antigravity Opus: Decomposes, spawns Qwen terminals

→ Qwen terminal 1: ruff check backend/ --fix
→ Qwen terminal 2: ruff format backend/
→ Qwen terminal 3: cd frontend && npm run lint:fix
→ Qwen terminal 4: mypy backend/app/ --ignore-missing-imports

← Antigravity reviews output, commits if clean
```

### Exploration with Synthesis

```
Claude Web: "Assess ACGME validation coverage in the codebase"
     ↓
Antigravity Opus: Decomposes, spawns Qwen terminals

→ Qwen terminal 1: grep -r "ACGMEValidator" backend/
→ Qwen terminal 2: grep -r "acgme" backend/tests/
→ Qwen terminal 3: grep -r "80.hour\|1.in.7" backend/

← Antigravity synthesizes findings using acgme-compliance skill
← Reports analysis to Claude Web for strategic discussion
```

---

## Qwen Code Setup (Reference)

```bash
# Installation
npm install -g @qwen-code/qwen-code@latest
# or
brew install qwen-code

# Authentication
# - Qwen OAuth: 2,000 free requests/day
# - Or: OPENAI_API_KEY with custom base URL

# Config location
~/.qwen/settings.json
```

Key features (v0.5.0):
- 4 concurrent instances in one terminal
- VS Code integration bundled
- 38-80 tokens/sec execution speed

---

## Implementation Approach

Antigravity IDE (Opus 4.5) manages Qwen terminals directly:

```bash
# Antigravity spawns parallel Qwen terminals
qwen "cd backend && pytest tests/unit/" &
qwen "cd frontend && npm run lint" &
qwen "ruff check backend/ --fix" &
wait  # Antigravity monitors and synthesizes results
```

**Key points:**
- Claude Code Web plans strategy with user
- Antigravity Opus 4.5 receives objectives, decomposes into parallel tasks
- Antigravity spawns/monitors Qwen terminals for skill-free operations
- Antigravity applies skills to synthesize/review Qwen outputs
- Qwen handles fast execution; Opus handles reasoning

---

## Prerequisites Before Implementation

1. [ ] Qwen Code installed: `npm install -g @qwen-code/qwen-code@latest`
2. [ ] Qwen authenticated (OAuth or API key)
3. [ ] Qwen evaluated independently for reliability on simple tasks
4. [ ] Skill-free task boundary clearly defined
5. [ ] Error handling pattern established (Qwen fail → Claude retry?)

---

## Open Questions

1. **Qwen reliability**: Does Qwen output need Opus review before acting on it?
2. **Context sharing**: How does Qwen get enough context without skills?
3. **Error recovery**: If Qwen fails, does Opus retry or take over?
4. **Rate limits**: How do Qwen's 2,000 free requests/day impact throughput?
5. **Local Qwen**: Should we evaluate Ollama-hosted Qwen3-Coder for full offline?

---

## Related Documentation

- [Manager View (Future B)](FUTURE_B_MANAGER_VIEW.md) - Parallel agent patterns (Claude-only)
- [SDK Orchestration Roadmap](ROADMAP_SDK_ORCHESTRATION.md) - SDK-based alternative
- [Settings](settings.json) - Model configuration
- [Qwen Code GitHub](https://github.com/QwenLM/qwen-code) - Qwen CLI documentation

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-26 | Document as future concept | Evaluate Qwen independently first |

---

*This document captures a concept for future evaluation. Do not implement until prerequisites are met and Qwen has been independently validated.*
