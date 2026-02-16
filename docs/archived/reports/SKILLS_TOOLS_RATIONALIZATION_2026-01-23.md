# Skills ↔ Tools Rationalization Plan

> **Generated:** 2026-01-23 | **Session:** 136
> **Scope:** 92 skills + 137 MCP tools
> **Context:** RAG via pgvector available for documentation

---

## Executive Summary

Cross-analysis of skills and MCP tools reveals significant optimization opportunities:

| Category | Count | Action |
|----------|-------|--------|
| Skills → MCP Tools | 3 | Convert deterministic logic to tools |
| Skills → Should Call Tools | 4 | Add MCP orchestration |
| Skills → RAG | 5 | Move documentation to vector DB |
| Tools → RAG (placeholder) | 10 | Document as mock until backend exists |
| Redundancies | 4 | Consolidate |

---

## Part 1: Skills That Should Become MCP Tools

These skills have **deterministic, calculable logic** that would be better as callable tools.

### P0: Create These Tools

| Skill | Tool Name | Why Tool? | Effort |
|-------|-----------|-----------|--------|
| **coverage-reporter** (8/10) | `coverage_report_tool` | Runs pytest/npm coverage, parses output, calculates trends | 2 days |
| **changelog-generator** (7/10) | `changelog_generator_tool` | Git parsing + categorization rules (has code sample) | 2 days |
| **check-camelcase** (MISSING) | `check_camelcase_tool` | Linting check for axios interceptor compatibility | 1 day |

### P1: Partial Tool Extraction

| Skill | Tool Name | What Moves | What Stays |
|-------|-----------|------------|------------|
| **pre-pr-checklist** (8/10) | `pr_readiness_check_tool` | File counts, test existence, CHANGELOG check | Subjective review stays as skill |

### Tool Interface Examples

```python
# coverage_report_tool
class CoverageReportRequest(BaseModel):
    languages: list[str] = ["python", "typescript"]
    include_trends: bool = True

class CoverageReportResponse(BaseModel):
    overall_coverage: float
    by_language: dict[str, float]
    critical_gaps: list[CoverageGap]
    trend_analysis: TrendAnalysis | None

# changelog_generator_tool
class ChangelogRequest(BaseModel):
    since: str  # git date/tag
    output_format: Literal["standard", "compact", "app_store"] = "standard"

class ChangelogResponse(BaseModel):
    features: list[str]
    bug_fixes: list[str]
    breaking_changes: list[str]
    formatted_output: str
```

---

## Part 2: Skills That Should Orchestrate MCP Tools

These skills describe workflows but **don't actually call the tools**. They should.

### Gold Standards (Already Do It Right)

| Skill | Tools Called | Pattern |
|-------|--------------|---------|
| **safe-schedule-generation** (8/10) | `create_backup_tool`, `list_backups_tool`, `restore_backup_tool` | Safety gates |
| **resilience-dashboard** (9/10) | 8 tools in 3-phase parallel batching | Aggregation |

### Need Tool Integration

| Skill | Should Call | Current State |
|-------|-------------|---------------|
| **SWAP_EXECUTION** (9/10) | `analyze_swap_candidates_tool`, `validate_schedule_tool`, `create_backup_tool` | Documentation only - describes SwapExecutor class but no MCP calls |
| **COMPLIANCE_VALIDATION** (8/10) | `validate_schedule_tool`, `check_mtf_compliance_tool` | Lists tools in text but doesn't call them |
| **schedule-validator** (7/10) | `validate_schedule_tool` | Delegates to other skills instead of calling tool |
| **solver-control** (9/10) | `cancel_task_tool`, `get_task_status_tool` | Direct Redis/API instead of MCP |

### Integration Pattern

```markdown
# SWAP_EXECUTION should become:

## Phase 1: Validation
```python
# Call MCP tools
result = mcp__residency-scheduler__analyze_swap_candidates_tool(...)
validation = mcp__residency-scheduler__validate_schedule_tool(...)
```

## Phase 2: Safety Gate
```python
backup = mcp__residency-scheduler__create_backup_tool(reason="Pre-swap backup")
```

## Phase 3: Execute
[existing swap execution logic]

## Phase 4: Verify
```python
mcp__residency-scheduler__validate_schedule_tool(...)  # Post-swap check
```
```

---

## Part 3: Skills That Should Move to RAG

These skills are **pure documentation** - reference material, not workflows. Better as RAG entries.

### Move to RAG

| Skill | Score | Why RAG? | Query Pattern |
|-------|-------|----------|---------------|
| **hierarchy** | 9/10 | Static org chart, no workflow | `rag_search('agent hierarchy')` |
| **parties** | 8/10 | Static protocol reference | `rag_search('party protocols 120 probes')` |
| **python-testing-patterns** | 9/10 | 612-line cookbook | `rag_search('async test fixtures')` |
| **fastapi-production** | 9/10 | 828-line cookbook | `rag_search('fastapi route patterns')` |
| **context-aware-delegation** | 10/10 | Educational guide on prompt writing | `rag_search('agent context isolation')` |

### Extract Theory, Keep Skill

| Skill | Theory to RAG | Lines | Keep |
|-------|---------------|-------|------|
| **time-crystal-scheduling** (6/10) | Physics theory | ~50 | MCP tool orchestration |
| **foam-topology** (7/10) | Foam physics | ~70 | Visualization workflow |
| **devcom** (5/10) | Exotic concepts list | ~86 | Research orchestration |
| **deep-research** (5/10) | Browser automation steps | ~143 | Search orchestration |

---

## Part 4: MCP Tools That Should Be RAG/Skills

### Placeholder Tools → Document in RAG

10 tools return **mock data** (documented in `PLACEHOLDER_IMPLEMENTATIONS.md`). Until backend services exist, these are effectively documentation.

| Tool | Score | Action |
|------|-------|--------|
| analyze_homeostasis_tool | 4/10 | Add `[MOCK]` to description, document expected behavior in RAG |
| get_static_fallbacks_tool | 4/10 | Same |
| execute_sacrifice_hierarchy_tool | 4/10 | Same |
| calculate_blast_radius_tool | 4/10 | Same |
| analyze_le_chatelier_tool | 4/10 | Same |
| analyze_hub_centrality_tool | 4/10 | Same |
| assess_cognitive_load_tool | 4/10 | Same |
| get_behavioral_patterns_tool | 4/10 | Same |
| analyze_stigmergy_tool | 4/10 | Same |
| check_mtf_compliance_tool | 5/10 | Same |

### Exotic Armory Tools → RAG Documentation

Physics-inspired tools (thermodynamics, Hopfield) lack real-world validation. Their **theory** should be RAG; tools stay for when backend supports them.

| Domain | Tools | Action |
|--------|-------|--------|
| Physics (13 tools) | Entropy, Hopfield, Time Crystal | Extract physics theory to RAG |
| Biology (9 tools) | Epidemiology, Immune | Extract biology analogs to RAG |

---

## Part 5: Redundancies to Consolidate

| Redundancy | Action |
|------------|--------|
| `startupO` + `startupO-legacy` | Delete legacy (identical) |
| `deep-research` + `devcom` | Merge into single research skill |
| `resilience-dashboard` + `resilience-overseer` | overseer is frontend docs; dashboard calls tools → keep dashboard, move overseer to RAG |
| `schedule-validator` + `COMPLIANCE_VALIDATION` | Both validate schedules; consolidate into one that calls `validate_schedule_tool` |

---

## Implementation Plan

### Phase 1: Create New MCP Tools (P0)

**Files to create:**
- `mcp-server/src/scheduler_mcp/tools/coverage_reporter.py`
- `mcp-server/src/scheduler_mcp/tools/changelog_generator.py`
- `mcp-server/src/scheduler_mcp/tools/camelcase_checker.py`
- `mcp-server/tests/tools/test_reporting_tools.py`

**Files to modify:**
- `mcp-server/src/scheduler_mcp/server.py` (register new tools)

### Phase 2: Add Tool Orchestration to Skills (P1)

**Skills to update:**
- `.claude/skills/SWAP_EXECUTION/SKILL.md` - add MCP tool calls
- `.claude/skills/COMPLIANCE_VALIDATION/SKILL.md` - add MCP tool calls
- `.claude/skills/schedule-validator/SKILL.md` - add MCP tool calls
- `.claude/skills/solver-control/SKILL.md` - add MCP tool calls

### Phase 3: Move Skills to RAG (P1)

**Ingest to RAG:**
```bash
# Using rag_ingest tool
rag_ingest(path=".claude/skills/hierarchy/SKILL.md", collection="skills-reference")
rag_ingest(path=".claude/skills/parties/SKILL.md", collection="skills-reference")
rag_ingest(path=".claude/skills/python-testing-patterns/SKILL.md", collection="patterns")
rag_ingest(path=".claude/skills/fastapi-production/SKILL.md", collection="patterns")
rag_ingest(path=".claude/skills/context-aware-delegation/SKILL.md", collection="delegation")
```

**Archive skills:**
- Move to `.claude/skills/archived/` or delete

### Phase 4: Mark Placeholder Tools (P0)

**Files to modify:**
- `mcp-server/src/scheduler_mcp/resilience_integration.py` - add `[MOCK]` to 10 tool descriptions

### Phase 5: Delete Redundancies (P2)

- Delete `.claude/skills/startupO-legacy/`
- Merge `deep-research` + `devcom` → single `research` skill
- Archive `resilience-overseer` to RAG

---

## Verification

1. **New tools work:** `pytest mcp-server/tests/tools/test_reporting_tools.py`
2. **RAG ingestion:** `rag_search('agent hierarchy')` returns content
3. **Skill orchestration:** Run SWAP_EXECUTION skill, verify it calls MCP tools
4. **Placeholder warnings:** Tool descriptions show `[MOCK]` prefix
5. **Redundancies gone:** `ls .claude/skills/startupO-legacy` → not found

---

## Summary Matrix

```
                    DETERMINISTIC    ORCHESTRATION    DOCUMENTATION
                    (Tool)           (Skill)          (RAG)
                    ─────────────────────────────────────────────────
coverage-reporter   ✓ → Tool
changelog-gen       ✓ → Tool
check-camelcase     ✓ → Tool (new)
pre-pr-checklist    partial →        partial stays
SWAP_EXECUTION                       ✓ (add tool calls)
COMPLIANCE_VALID                     ✓ (add tool calls)
hierarchy                                             ✓ → RAG
parties                                               ✓ → RAG
python-testing                                        ✓ → RAG
fastapi-production                                    ✓ → RAG
placeholder tools                                     ✓ document
```

---

*Analysis based on 92 skills + 137 MCP tools. RAG via pgvector available.*
