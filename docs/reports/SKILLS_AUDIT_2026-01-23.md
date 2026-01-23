# Skills Audit Report: Intent vs. Achievement

> **Generated:** 2026-01-23 | **Session:** 136
> **Scope:** 92 skills in `.claude/skills/`
> **Methodology:** Read each skill's SKILL.md and evaluate intent vs. likely achievement

---

## Executive Summary

| Rating | Count | Percentage |
|--------|-------|------------|
| **Excellent (9-10)** | 24 | 26% |
| **Strong (8)** | 28 | 30% |
| **Good (7)** | 18 | 20% |
| **Moderate (6)** | 8 | 9% |
| **Weak (4-5)** | 6 | 7% |
| **Missing/Broken (0)** | 3 | 3% |
| **N/A (not a skill)** | 5 | 5% |

**Average Score: 7.6/10** (excluding N/A and missing)

---

## Tier 1: Excellent (9-10/10)

These skills have clear intent, concrete implementation, and high achievability.

| Skill | Score | Why It Works |
|-------|-------|--------------|
| **tamc-excel-scheduling** | 10 | 1,200+ lines; complete scheduler from scratch |
| **context-aware-delegation** | 10 | Foundational L3 pattern; transforms delegation |
| **pr-reviewer** | 10 | Complete workflow with failure modes |
| **SWAP_EXECUTION** | 9 | Safety gates, rollback, audit trail |
| **MCP_ORCHESTRATION** | 9 | Runnable code patterns |
| **spawn-agent** | 9 | Clean MCP abstraction |
| **startupO** | 9 | Complete orchestrator model |
| **hierarchy** | 9 | Clear reference material |
| **historian** | 9 | Narrative structure guidance |
| **code-review** | 9 | Detailed checklist with examples |
| **test-writer** | 9 | Pytest + Jest patterns |
| **python-testing-patterns** | 9 | Advanced async/fixture patterns |
| **lint-monorepo** | 9 | Ruff + ESLint orchestration |
| **database-migration** | 9 | Alembic patterns with safety |
| **fastapi-production** | 9 | Production-ready patterns |
| **frontend-development** | 9 | Next.js 14 comprehensive |
| **react-typescript** | 9 | TS error fixes with examples |
| **docker-containerization** | 9 | Multi-stage, security hardening |
| **security-audit** | 9 | HIPAA/OPSEC focus |
| **tamc-cpsat-constraints** | 9 | CP-SAT model documented |
| **swap-management** | 9 | 986 lines; complete workflow |
| **astronaut** | 9 | Complete browser automation ROE |
| **roster-party** | 9 | Team composition analysis |
| **signal-party** | 9 | Metrics collection pattern |
| **sof-party** | 9 | Rapid assessment framework |
| **resilience-dashboard** | 9 | MCP orchestration pattern |
| **pdf** | 9 | Concrete code patterns |
| **xlsx** | 9 | Import/export with formulas |
| **solver-control** | 9 | Kill-switch with examples |
| **production-incident-responder** | 9 | Crisis response protocol |
| **CORE** | 9 | Central routing logic |

---

## Tier 2: Strong (8/10)

These skills are well-implemented with minor gaps.

| Skill | Score | Notes |
|-------|-------|-------|
| COMPLIANCE_VALIDATION | 8 | Good structure, some edge cases unclear |
| safe-schedule-generation | 8 | Backup-first pattern |
| swap-analyzer | 8 | 4-phase framework |
| ORCHESTRATION_DEBUGGING | 8 | Systematic methodology |
| force-multiplier | 8 | RAG query patterns |
| startupO-lite | 8 | Token-efficient startup |
| startup | 8 | Essential checks |
| governance | 8 | Config toggle |
| usasoc | 8 | Authority model |
| synthesizer | 8 | Deputy invocation |
| session-documentation | 8 | Comprehensive checklist |
| automated-code-fixer | 8 | Safety gates |
| code-quality-monitor | 8 | Health scoring |
| coverage-reporter | 8 | Threshold enforcement |
| pre-pr-checklist | 8 | Documentation gates |
| check-codex | 8 | GitHub Copilot integration |
| RESILIENCE_SCORING | 8 | N-1/N-2 simulations |
| parties | 8 | Parallel deployment docs |
| search-party | 8 | 120 parallel probes |
| qa-party | 8 | Zero marginal cost |
| plan-party | 8 | Multi-perspective planning |
| context-party | 8 | RAG integration |
| stack-audit | 8 | 10-check framework |
| playwright-workflow | 8 | Test organization |
| skill-factory | 8 | Creation template |
| deployment-validator | 8 | 4-phase validation |

---

## Tier 3: Good (7/10)

Useful but missing concrete examples or depth.

| Skill | Score | Gap |
|-------|-------|-----|
| SCHEDULING | 7 | Mostly agent spawning |
| acgme-compliance | 7 | Brief skill description |
| schedule-validator | 7 | WHAT not HOW |
| constraint-preflight | 7 | Dev-focused only |
| agent-factory | 7 | Requires external validation |
| force-manager | 7 | G1 roster dependency |
| crash-recovery | 7 | Recovery uncertainty |
| session-end | 7 | Coordination complexity |
| systematic-debugger | 7 | Generic methodology |
| changelog-generator | 7 | Depends on commit discipline |
| test-scenario-framework | 7 | Sparse documentation |
| medcom | 7 | Advisory-only limits use |
| ops-party | 7 | G-3 function less documented |
| resilience-overseer | 7 | UI reference, not skill |
| foam-topology | 7 | Experimental |
| trajectory-analyzer | 7 | ADK integration unclear |

---

## Tier 4: Moderate (6/10)

Limited utility or narrow scope.

| Skill | Score | Issue |
|-------|-------|-------|
| schedule-optimization | 6 | Placeholder-like |
| schedule-verification | 6 | Human checklist, not AI |
| time-crystal-scheduling | 6 | Theory > practice |
| agent-evaluation | 6 | ROUGE untested |
| cowork-handoff | 6 | Very narrow scope |
| viz-pipeline | 6 | Process doc, not skill |

---

## Tier 5: Weak (4-5/10)

Abstract or non-actionable.

| Skill | Score | Problem |
|-------|-------|---------|
| deep-research | 5 | Abstract, no workflow |
| devcom | 5 | Overlaps deep-research |
| architect | 4 | Just agent delegation |

---

## Tier 6: Missing/Broken (0/10)

| Skill | Issue |
|-------|-------|
| **check-camelcase** | Referenced in CLAUDE.md but skill file not found |
| **fm-residency-scheduling** | Not found in codebase |
| **startupO-legacy** | Duplicate of startupO (redundant) |

---

## Tier 7: Not Actually Skills

| Item | Notes |
|------|-------|
| managed/ | Folder, not skill |

---

## Category Analysis

### Scheduling (15 skills) - Avg: 7.3/10
- **Best:** tamc-excel-scheduling (10), SWAP_EXECUTION (9)
- **Worst:** schedule-verification (6), time-crystal-scheduling (6)
- **Gap:** Too much theory, not enough concrete examples in weaker skills

### Agent/Orchestration (20 skills) - Avg: 8.2/10
- **Best:** context-aware-delegation (10), spawn-agent (9), startupO (9)
- **Worst:** architect (4), agent-evaluation (6)
- **Gap:** Abstract skills need workflow anchors

### Development/Testing (20 skills) - Avg: 8.0/10
- **Best:** pr-reviewer (10), code-review (9), test-writer (9)
- **Worst:** check-camelcase (0 - missing), changelog-generator (7)
- **Gap:** check-camelcase is a critical missing skill

### Utility/Specialized (31 skills) - Avg: 7.8/10
- **Best:** pdf (9), xlsx (9), solver-control (9)
- **Worst:** deep-research (5), devcom (5), architect (4)
- **Gap:** Research skills too abstract

---

## Critical Findings

### 1. Missing Skills (BLOCKING)
- **check-camelcase** - Referenced in CLAUDE.md as critical for axios interceptor compatibility, but skill doesn't exist
- **fm-residency-scheduling** - Referenced but not found

### 2. Gold Standard Skills
These should be templates for improving weaker skills:
- `tamc-excel-scheduling` - 1,200+ lines, complete implementation
- `context-aware-delegation` - Foundational principle that transforms work
- `pr-reviewer` - Complete workflow with failure modes

### 3. Common Weakness Patterns
| Pattern | Count | Fix |
|---------|-------|-----|
| Theory without examples | 8 | Add worked examples |
| Agent delegation only | 4 | Add skill-level guidance |
| Missing trigger conditions | 6 | Add "when to use" section |
| No failure mode coverage | 12 | Add error handling |

### 4. Redundancies
- `startupO` and `startupO-legacy` are identical
- `deep-research` and `devcom` overlap significantly

---

## Recommendations

### Immediate (P0)
1. **Create check-camelcase skill** - Critical gap per CLAUDE.md
2. **Delete or alias startupO-legacy** - Redundant

### Short-term (P1)
3. **Enhance weak scheduling skills** with concrete examples from tamc-excel-scheduling
4. **Add failure modes** to 12 skills lacking them
5. **Consolidate deep-research + devcom** into single research skill

### Medium-term (P2)
6. **Add "when to use" triggers** to 6 skills missing them
7. **Create skill quality checklist** based on gold standard patterns
8. **Audit all skills against skill-factory template**

---

## Score Distribution

```
10/10: ██ (2)
 9/10: █████████████████████████████ (29)
 8/10: ██████████████████████████ (26)
 7/10: ████████████████ (16)
 6/10: ████████ (8)
 5/10: ██ (2)
 4/10: █ (1)
 0/10: ███ (3 missing)
```

---

## For LLM Consumption

### High-Value Skills (Use These)
```
tamc-excel-scheduling, context-aware-delegation, pr-reviewer,
SWAP_EXECUTION, MCP_ORCHESTRATION, spawn-agent, code-review,
test-writer, database-migration, fastapi-production, pdf, xlsx
```

### Avoid/Use Cautiously
```
deep-research (vague), devcom (vague), architect (just delegation),
schedule-optimization (placeholder), check-camelcase (MISSING)
```

### For Complex Tasks, Combine
```
Scheduling: tamc-excel-scheduling + constraint-preflight + safe-schedule-generation
Testing: test-writer + python-testing-patterns + coverage-reporter
Deployment: deployment-validator + qa-party + pr-reviewer
Crisis: production-incident-responder + resilience-dashboard + solver-control
```

---

*Report generated from analysis of 92 skills across 4 categories.*
