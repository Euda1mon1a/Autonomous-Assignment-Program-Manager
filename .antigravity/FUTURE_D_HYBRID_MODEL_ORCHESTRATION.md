# Hybrid Model Orchestration (FUTURE - CONCEPT ONLY)

> **Status:** CONCEPT - For future evaluation
> **Created:** 2025-12-26
> **Prerequisite:** Qwen Code installed and validated independently

---

## Concept Overview

Claude Code CLI (Opus 4.5) directly manages Qwen instances via integrated terminal:

```
YOU
  │
  ▼
CLAUDE CODE CLI (Opus 4.5) ← Integrated terminal, tactician role
  │
  │  Spawns/manages via Bash:
  │
  ├──► qwen "run pytest backend/tests/" &
  ├──► qwen "run npm test" &
  ├──► qwen "run ruff check . --fix" &
  └──► qwen "grep -r 'pattern' backend/" &
```

**Analogy:** Squad leader in the field directing operators, not a separate command layer.

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
Opus Tactician: "Run backend and frontend tests in parallel"

→ Qwen #1: cd backend && pytest -v
→ Qwen #2: cd frontend && npm test
→ Qwen #3: cd frontend && npm run type-check
→ Qwen #4: cd frontend && npm run lint

← Opus synthesizes results, applies code-review skill if failures
```

### Bulk Linting/Formatting

```
Opus Tactician: "Format and lint the entire codebase"

→ Qwen #1: ruff check backend/ --fix
→ Qwen #2: ruff format backend/
→ Qwen #3: cd frontend && npm run lint:fix
→ Qwen #4: mypy backend/app/ --ignore-missing-imports

← Opus reviews output, commits if clean
```

### Exploration with Synthesis

```
Opus Tactician: "Find all ACGME validation usages and assess coverage"

→ Qwen #1: grep -r "ACGMEValidator" backend/
→ Qwen #2: grep -r "acgme" backend/tests/
→ Qwen #3: grep -r "80.hour\|1.in.7" backend/

← Opus synthesizes findings using acgme-compliance skill
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

Claude Code CLI uses Bash tool to spawn and manage Qwen instances:

```bash
# Parallel execution pattern
qwen "cd backend && pytest tests/unit/" &
qwen "cd frontend && npm run lint" &
qwen "ruff check backend/ --fix" &
wait  # Claude monitors and synthesizes results
```

Key points:
- No SDK wrapper needed - direct CLI invocation
- Claude Code monitors stdout/stderr from Qwen processes
- Claude applies skills to synthesize/review Qwen outputs
- Qwen handles execution; Claude handles reasoning

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
