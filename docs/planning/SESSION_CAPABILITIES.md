# Session Capabilities: Skills, Tools, and MCP

> **Created:** 2025-12-24
> **Purpose:** Document available capabilities for Claude Web and Claude Code (IDE) sessions
> **Branch:** `claude/plan-block-10-roadmap-IDOo9`

---

## Quick Reference

| Capability Type | Count | Status |
|-----------------|-------|--------|
| **Skills (via Skill tool)** | 17 | Ready to invoke |
| **Execution Tools** | 15+ | Native tools available |
| **MCP Tools** | 29 | ~19 functional, ~10 placeholder |
| **MCP Resources** | 2 | Functional |

---

## 1. Skills Available (Invoke via `Skill` tool)

Skills are specialized domain expertise packages. Invoke with the Skill tool.

### Domain-Specific Skills

| Skill Name | Purpose | PII Needed? |
|------------|---------|-------------|
| `acgme-compliance` | ACGME regulatory expertise | No (rules only) |
| `schedule-optimization` | Multi-objective scheduling optimization | Yes (for real data) |
| `swap-management` | Shift swap workflows and matching | Yes (for real data) |
| `safe-schedule-generation` | Backup-first schedule generation | Yes (DB access) |

### Development Skills

| Skill Name | Purpose | PII Needed? |
|------------|---------|-------------|
| `code-review` | Review generated code for quality | No |
| `automated-code-fixer` | Auto-fix test/lint/type errors | No |
| `code-quality-monitor` | Quality gate enforcement | No |
| `test-writer` | Generate pytest/Jest tests | No |
| `database-migration` | Alembic migration expertise | No |
| `pr-reviewer` | Pull request review with standards | No |
| `security-audit` | HIPAA, OPSEC/PERSEC compliance | No |
| `changelog-generator` | Generate changelogs from git history | No |
| `systematic-debugger` | Four-phase debugging workflow | No |

### Document Skills

| Skill Name | Purpose | PII Needed? |
|------------|---------|-------------|
| `xlsx` | Excel import/export for schedules | Yes (for real data) |
| `pdf` | PDF generation and extraction | Yes (for real data) |

### Operations Skills

| Skill Name | Purpose | PII Needed? |
|------------|---------|-------------|
| `production-incident-responder` | Crisis response with resilience tools | Yes (for real data) |

---

## 2. Execution Tools (Native)

These are built-in tools available in every session:

### File Operations

| Tool | Purpose | Claude Web Safe? |
|------|---------|------------------|
| `Read` | Read files | Yes (code, no PII files) |
| `Write` | Create new files | Yes (docs, no PII) |
| `Edit` | Modify existing files | Yes (code, docs) |
| `Glob` | Find files by pattern | Yes |
| `Grep` | Search file contents | Yes |

### Execution

| Tool | Purpose | Claude Web Safe? |
|------|---------|------------------|
| `Bash` | Run shell commands | Limited (no DB, no PII) |
| `Task` | Launch subagents | Yes |

### Web

| Tool | Purpose | Claude Web Safe? |
|------|---------|------------------|
| `WebFetch` | Fetch and analyze URLs | Yes |
| `WebSearch` | Search the web | Yes |

### Workflow

| Tool | Purpose | Claude Web Safe? |
|------|---------|------------------|
| `TodoWrite` | Track task progress | Yes |
| `Skill` | Invoke specialized skills | Depends on skill |
| `SlashCommand` | Execute custom commands | Depends on command |

---

## 3. MCP Tools (Model Context Protocol)

### Functional Tools (19)

| Category | Tool | Works? |
|----------|------|--------|
| **Validation** | `validate_schedule` | Yes |
| **Validation** | `validate_acgme_compliance` | Yes |
| **Conflict** | `detect_conflicts` | Yes |
| **Conflict** | `analyze_swap_candidates` | Yes |
| **Conflict** | `get_conflict_alerts` | Yes |
| **Async** | `start_background_task` | Yes |
| **Async** | `get_task_status` | Yes |
| **Async** | `cancel_task` | Yes |
| **Async** | `list_active_tasks` | Yes |
| **Resilience** | `check_utilization_threshold` | Yes |
| **Resilience** | `get_defense_level` | Yes |
| **Resilience** | `run_contingency_analysis` | Yes |
| **Deployment** | `check_deployment_status` | Yes |
| **Deployment** | `run_pre_deploy_checks` | Yes |
| **Deployment** | `trigger_rollback` | Yes |
| **Deployment** | `get_deployment_history` | Yes |
| **Health** | `health_check` | Yes |
| **Empirical** | `run_module_comparison` | Yes |
| **Empirical** | `benchmark_solver` | Yes |

### Placeholder Tools (10) - Return Mock Data

| Tool | Issue |
|------|-------|
| `analyze_homeostasis` | Returns mock homeostasis data |
| `get_static_fallbacks` | Returns mock fallback schedules |
| `execute_sacrifice_hierarchy` | Returns mock load shedding data |
| `calculate_blast_radius` | Returns mock zone isolation data |
| `analyze_le_chatelier` | Returns mock equilibrium data |
| `analyze_hub_centrality` | Returns mock centrality data |
| `assess_cognitive_load` | Returns mock cognitive load data |
| `get_behavioral_patterns` | Returns mock behavioral data |
| `analyze_stigmergy` | Returns mock stigmergy data |
| `check_mtf_compliance` | Returns mock MTF data |

### Missing Tools (Referenced by Skills but Don't Exist)

| Tool | Referenced By | Priority |
|------|---------------|----------|
| `generate_schedule` | safe-schedule-generation | P0 |
| `execute_swap` | swap-management | P0 |
| `rollback_swap` | swap-management | P1 |
| `bulk_assign` | safe-schedule-generation | P1 |
| `optimize_schedule` | schedule-optimization | P1 |

---

## 4. MCP Resources

| Resource | URI | Status |
|----------|-----|--------|
| Schedule Status | `schedule://status` | Functional |
| Compliance Summary | `schedule://compliance` | Functional |

---

## 5. Claude Web Independent Workstreams

These tasks can be done by Claude (Web) with **no PII access** while Claude Code (IDE) works on Block 10:

### Tier 1: Immediate (No Dependencies)

| # | Task | Skill to Use | Effort |
|---|------|--------------|--------|
| 1 | **Review MCP placeholder implementations** | `code-review` | 4h |
| 2 | **Document solver algorithm** | None (read code) | 3h |
| 3 | **Audit security patterns** | `security-audit` | 3h |
| 4 | **Review test coverage gaps** | `test-writer` | 2h |
| 5 | **Update CLAUDE.md with session learnings** | None | 1h |

### Tier 2: Documentation Tasks

| # | Task | Files Involved | Effort |
|---|------|----------------|--------|
| 6 | **Create operator runbook** | `docs/operations/` | 3h |
| 7 | **Consolidate API documentation** | `docs/api/` | 4h |
| 8 | **Update skill-MCP matrix** | `docs/planning/SKILL_MCP_TOOL_MATRIX.md` | 1h |
| 9 | **Document resilience framework** | `docs/architecture/` | 3h |

### Tier 3: Code Quality (No PII)

| # | Task | Skill to Use | Files |
|---|------|--------------|-------|
| 10 | **Fix eslint warnings** | `automated-code-fixer` | `frontend/src/` |
| 11 | **Add missing TypeDoc comments** | `code-quality-monitor` | `frontend/src/` |
| 12 | **Review error handling patterns** | `code-review` | `backend/app/core/` |

### Tier 4: Architecture Review

| # | Task | Output | Effort |
|---|------|--------|--------|
| 13 | **Analyze solver constraint priorities** | Recommendations | 2h |
| 14 | **Review MCP tool organization** | Refactoring plan | 2h |
| 15 | **Evaluate placeholder replacement strategy** | Implementation plan | 3h |

---

## 6. Skills I Can Invoke Right Now

As Claude (Web), I can use these skills immediately:

```
# Code quality and review
Skill: code-review
Skill: code-quality-monitor
Skill: automated-code-fixer
Skill: security-audit

# Documentation
Skill: changelog-generator
Skill: pr-reviewer

# Domain expertise (no DB needed)
Skill: acgme-compliance  # For rules reference
Skill: systematic-debugger

# Writing tests (for mock data)
Skill: test-writer
Skill: database-migration  # For migration review
```

---

## 7. What Claude Code (IDE) Has That I Don't

| Capability | Claude Code (IDE) | Claude (Web) |
|------------|-------------------|--------------|
| Database access | Direct SQL/ORM | None |
| PII file access | Full | None |
| Docker commands | Full | None |
| Schedule generation | Full | Sanitized output only |
| Real MCP tools | With backend | Placeholder responses |
| pytest with DB | Full | Unit tests only |

---

## 8. Handoff Protocol

### When Claude Code (IDE) Finishes Checkpoint 2:

1. Export sanitized metrics:
   ```bash
   python scripts/export_sanitized_metrics.py --block 10 -o block10_metrics.json
   ```

2. Share JSON output with Claude (Web)

3. Claude (Web) performs analysis using:
   - Coverage gap analysis
   - Fairness metric evaluation
   - Constraint violation patterns
   - Optimization recommendations

### Parallel Work During Block 10 Development:

```
Claude Code (IDE)                    Claude (Web)
─────────────────                    ────────────
Seed database                        Review MCP placeholders
Generate schedule                    Document solver algorithm
Debug violations                     Audit security patterns
Test with real data                  Update CLAUDE.md
Export sanitized metrics ──────────→ Analyze metrics
                                     Generate recommendations
```

---

*Document version: 2025-12-24*
