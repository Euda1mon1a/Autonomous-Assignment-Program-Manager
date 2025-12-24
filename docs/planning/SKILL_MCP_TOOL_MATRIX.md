# Skill to MCP Tool Matrix

> **Purpose:** Track which skills reference which MCP tools
> **Issue:** Some skills reference tools that don't exist or are placeholders

---

## Skills Overview

| Skill | MCP Integration | Status |
|-------|-----------------|--------|
| `safe-schedule-generation` | Heavy | Tools missing |
| `swap-management` | Medium | Mostly working |
| `schedule-optimization` | Medium | Mostly working |
| `production-incident-responder` | Heavy | Placeholders |
| `acgme-compliance` | Light | Working |

---

## safe-schedule-generation

**File:** `.claude/skills/safe-schedule-generation/SKILL.md`

| Referenced Tool | Exists? | Works? |
|-----------------|---------|--------|
| `generate_schedule` | **NO** | - |
| `execute_swap` | **NO** | - |
| `bulk_assign` | **NO** | - |
| `validate_schedule` | Yes | Yes |
| `detect_conflicts` | Yes | Yes |
| `analyze_swap_candidates` | Yes | Yes |
| `health_check` | Yes | Yes |

**Gap:** Core write operations (`generate_schedule`, `execute_swap`) don't exist in MCP.

---

## swap-management

**File:** `.claude/skills/swap-management/SKILL.md`

| Referenced Tool | Exists? | Works? |
|-----------------|---------|--------|
| `analyze_swap_compatibility` | Yes | Yes |
| `validate_swap` | Yes | Yes |
| `execute_swap` | **NO** | - |
| `rollback_swap` | **NO** | - |
| `get_swap_history` | **NO** | - |

**Gap:** Swap execution tools missing. Analysis tools work.

---

## schedule-optimization

**File:** `.claude/skills/schedule-optimization/SKILL.md`

| Referenced Tool | Exists? | Works? |
|-----------------|---------|--------|
| `generate_schedule` | **NO** | - |
| `optimize_schedule` | **NO** | - |
| `analyze_schedule_health` | **NO** | - |
| `generate_pareto_schedules` | **NO** | - |
| `validate_schedule` | Yes | Yes |
| `run_contingency_analysis_resilience_tool` | Yes | Placeholder |

**Gap:** All optimization tools missing. Only validation works.

---

## production-incident-responder

**File:** `.claude/skills/production-incident-responder/SKILL.md`

| Referenced Tool | Exists? | Works? |
|-----------------|---------|--------|
| `check_utilization_threshold_tool` | Yes | Yes |
| `get_defense_level_tool` | Yes | Yes |
| `run_contingency_analysis_resilience_tool` | Yes | Placeholder |
| `get_static_fallbacks_tool` | Yes | **Placeholder** |
| `execute_sacrifice_hierarchy_tool` | Yes | **Placeholder** |
| `analyze_homeostasis_tool` | Yes | **Placeholder** |
| `calculate_blast_radius_tool` | Yes | **Placeholder** |
| `analyze_le_chatelier_tool` | Yes | **Placeholder** |
| `analyze_hub_centrality_tool` | Yes | **Placeholder** |
| `get_behavioral_patterns_tool` | Yes | **Placeholder** |
| `assess_cognitive_load_tool` | Yes | **Placeholder** |
| `analyze_stigmergy_tool` | Yes | **Placeholder** |
| `check_mtf_compliance_tool` | Yes | **Placeholder** |

**Gap:** 10 of 13 resilience tools return placeholder data.

---

## acgme-compliance

**File:** `.claude/skills/acgme-compliance/SKILL.md`

| Referenced Tool | Exists? | Works? |
|-----------------|---------|--------|
| `validate_schedule` | Yes | Yes |
| (Validation tools) | Yes | Yes |

**Status:** Fully functional.

---

## Summary

### Missing Tools (Need Implementation)

| Tool | Referenced By | Priority |
|------|---------------|----------|
| `generate_schedule` | safe-schedule-generation, schedule-optimization | P0 |
| `execute_swap` | safe-schedule-generation, swap-management | P0 |
| `rollback_swap` | swap-management | P1 |
| `bulk_assign` | safe-schedule-generation | P1 |
| `optimize_schedule` | schedule-optimization | P1 |
| `get_swap_history` | swap-management | P2 |
| `analyze_schedule_health` | schedule-optimization | P2 |
| `generate_pareto_schedules` | schedule-optimization | P2 |

### Placeholder Tools (Need Backend Integration)

| Tool | Referenced By | Priority |
|------|---------------|----------|
| `run_contingency_analysis_resilience_tool` | production-incident-responder | P0 |
| `get_static_fallbacks_tool` | production-incident-responder | P0 |
| `execute_sacrifice_hierarchy_tool` | production-incident-responder | P0 |
| `analyze_homeostasis_tool` | production-incident-responder | P1 |
| `calculate_blast_radius_tool` | production-incident-responder | P1 |
| 5 more... | production-incident-responder | P2 |

---

## Recommendations

### Option A: Update Skills to Match Reality
- Remove references to non-existent tools
- Document what's actually available
- Provide manual alternatives

### Option B: Implement Missing Tools
- Add `generate_schedule` with backup verification
- Add `execute_swap` with validation
- Replace resilience placeholders

### Option C: Hybrid Approach (Recommended)
1. **P0:** Add core write tools (`generate_schedule`, `execute_swap`)
2. **P1:** Fix critical placeholders (static fallbacks, sacrifice hierarchy)
3. **P2:** Update skills to reflect current state
4. **P3:** Implement remaining nice-to-haves

---

## Validation Command

Check which tools actually exist in MCP server:

```bash
grep -E "@mcp\.tool\(\)" mcp-server/src/scheduler_mcp/server.py | wc -l
# Currently: 34 tools

grep -E "async def.*_tool\(" mcp-server/src/scheduler_mcp/server.py | \
  sed 's/.*async def //' | sed 's/(.*$//' | sort
```

---

*Skill-MCP tool matrix - December 2024*
