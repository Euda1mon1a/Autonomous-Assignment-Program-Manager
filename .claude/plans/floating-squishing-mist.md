# Plan: MCP Tool Adoption & Armory Integration

## Current State

**Branch:** `feature/rag-ingestion`
**Modified:** CLAUDE.md (Phase A complete), SESSION_092_HANDOFF.md

### Progress

| Phase | Status | Description |
|-------|--------|-------------|
| A: CLAUDE.md | ✅ DONE | Added "MCP Tool Requirements (MUST USE)" section |
| B: Skills | ❌ TODO | Update /scheduling, /swap, /startup skills |
| C: Hooks | ❌ TODO | Create pre-schedule-warning.sh |
| D: MCP Prompts | ❌ TODO | Add @mcp.prompt() to server.py |

---

## Armory Assessment

The armory contains **50 specialized tools** in 5 domains, currently NOT loaded by default. Several are production-useful:

### Production-Ready Tools (Candidates for Promotion or Activation)

| Domain | Tool | Production Value |
|--------|------|------------------|
| biology | `calculate_burnout_rt_tool` | Burnout containment metric (Rt < 1 = contained) |
| biology | `simulate_burnout_contagion_tool` | Superspreader detection |
| operations_research | `calculate_equity_metrics_tool` | Gini coefficient for fairness |
| operations_research | `calculate_shapley_workload_tool` | Fair workload distribution |
| resilience_advanced | `analyze_hub_centrality_tool` | Single point of failure detection |
| resilience_advanced | `calculate_blast_radius_tool` | Containment zone analysis |
| physics | `analyze_phase_transitions_tool` | Early warning signals |
| fatigue_detailed | `detect_burnout_precursors_tool` | Seismic-style early warning |

### Current Activation Methods

1. **Environment variable:** `ARMORY_DOMAINS="biology,resilience_advanced"`
2. **Skill-based:** `/armory biology` (skill exists but may not be wired)
3. **Programmatic:** `load_domain("biology")`

### Armory Integration Decision

**Option 1: Promote to Core** - Move highest-value tools to always-loaded
**Option 2: Auto-activate per Skill** - Skills that need them activate domains
**Option 3: Document for Advanced Use** - Keep tucked, document when to reach for them

**Recommendation:** Option 3 (conservative) + Option 2 for `/resilience-dashboard`

---

## Implementation Plan

### Phase D: MCP Prompts (do first - cross-LLM coverage)

**File:** `mcp-server/src/scheduler_mcp/server.py`

Add near other prompt definitions:

```python
@mcp.prompt()
async def tool_usage_requirements() -> list[PromptMessage]:
    """MCP tool usage requirements for all LLMs."""
    return [
        PromptMessage(
            role="system",
            content="""
REQUIRED MCP TOOL USAGE:

1. SCHEDULE VALIDATION: Before any schedule modification, run validate_schedule_tool
2. DOMAIN KNOWLEDGE: Before answering domain questions, query rag_search
3. RESILIENCE: Before capacity changes, check get_defense_level_tool
4. COMPLIANCE: After schedule generation, run check_mtf_compliance_tool

These tools exist to prevent errors and ensure compliance. Use them.

ARMORY (Advanced Analysis):
For deep analysis, activate specialized domains: biology, resilience_advanced, physics, operations_research, fatigue_detailed
Set ARMORY_DOMAINS environment variable or use /armory skill.
            """
        )
    ]
```

### Phase B: Skills Update

**Files to modify:**

| Skill | File | Add Step |
|-------|------|----------|
| /scheduling | `.claude/skills/scheduling/SKILL.md` | "Step 1: Run validate_schedule_tool" |
| /check-compliance | `.claude/skills/check-compliance/SKILL.md` | "Run check_mtf_compliance_tool first" |
| /swap | `.claude/skills/swap/SKILL.md` | "Run analyze_swap_candidates_tool" |
| /startup | `.claude/skills/startup/SKILL.md` | "Check get_defense_level_tool" |
| /resilience-dashboard | `.claude/skills/resilience-dashboard/SKILL.md` | "Activate armory: biology, resilience_advanced" |

### Phase C: Hook Warning

**Create:** `.claude/hooks/pre-schedule-warning.sh`

```bash
#!/bin/bash
# Warn if editing schedule code without running validation

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ "$TOOL_NAME" == "Edit" && "$FILE_PATH" == *schedule* ]]; then
    echo "REMINDER: Use validate_schedule_tool before editing schedule code" >&2
fi

exit 0  # Non-blocking warning
```

**Update:** `.claude/settings.json`

Add to PreToolUse section:
```json
{
  "matcher": "Edit",
  "hooks": [{
    "type": "command",
    "command": ".claude/hooks/pre-schedule-warning.sh"
  }]
}
```

---

## Files to Modify

| File | Change |
|------|--------|
| `mcp-server/src/scheduler_mcp/server.py` | Add @mcp.prompt() for tool requirements |
| `.claude/skills/scheduling/SKILL.md` | Add validate_schedule_tool step |
| `.claude/skills/swap/SKILL.md` | Add analyze_swap_candidates_tool step |
| `.claude/skills/startup/SKILL.md` | Add get_defense_level_tool check |
| `.claude/skills/check-compliance/SKILL.md` | Add check_mtf_compliance_tool step |
| `.claude/skills/resilience-dashboard/SKILL.md` | Add armory activation (if exists) |
| `.claude/hooks/pre-schedule-warning.sh` | New hook |
| `.claude/settings.json` | Add PreToolUse:Edit hook |
| `.claude/Scratchpad/SESSION_092_HANDOFF.md` | Update with armory findings |

---

## Verification

1. **MCP Prompt:** Query `mcp__residency-scheduler__rag_search(query="tool usage requirements")` - should return new prompt
2. **Skills:** Run `/startup` - should show defense level check
3. **Hook:** Edit a schedule file - should see reminder
4. **Armory:** Set `ARMORY_DOMAINS="biology"` and verify tools load

---

## Commit Strategy

When complete:
1. Stage all changes: `git add -A`
2. Commit with message:
   ```
   feat: MCP tool adoption enforcement + armory documentation

   - Add @mcp.prompt() for cross-LLM tool requirements
   - Update skills to require MCP tools before operations
   - Add pre-schedule-warning.sh hook
   - Document armory domains for advanced analysis

   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
   ```
3. Push and create PR

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| MCP prompt not loaded | Test with rag_search for requirements |
| Hook too noisy | Non-blocking (exit 0), can disable |
| Skills broken | Read-only additions, don't modify logic |
| Armory activation complexity | Document only, don't auto-activate |

**Overall:** Low risk, high upside (defense-in-depth for tool adoption)
