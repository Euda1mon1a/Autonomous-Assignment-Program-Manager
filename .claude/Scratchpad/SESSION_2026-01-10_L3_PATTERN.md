# Session 2026-01-10: L3 Minimal Context Pattern

## TL;DR
**Auftragstaktik works at L3.** Subagents can autonomously invoke MCP tools with just mission + parameters. No explicit tool names or identity cards required.

## Test Results

| Level | Context | MCP Used? |
|-------|---------|-----------|
| L1 | Identity + explicit tools | ✓ Yes (1 tool) |
| L2 | Identity + mission | ✓ Yes (1 tool + RAG) |
| **L3** | Mission + params only | **✓ Yes (3 tools!)** |
| L4 | Just question | ✗ No |

## L3 Template
```
## MISSION
[1-2 sentence objective]
[Parameters: dates, IDs, constraints]

## OUTPUT
[Expected format]
```

## PR #684
- Branch: `test/subagent-mcp-access`
- 7 files, 347 insertions
- RAG: 5 chunks added to `delegation_patterns`

## Key Files Updated
- `docs/rag-knowledge/L3-minimal-context-pattern.md` (NEW - 222 lines)
- `.claude/skills/CORE/delegation-patterns.md` (+40 lines)
- `.claude/skills/context-aware-delegation/SKILL.md` (+45 lines)
- `.claude/Governance/HIERARCHY.md` (+12 lines - L3 Standing Order)

## 4-Layer Infrastructure (commit f63e7049)
- A: `CLAUDE.md` (264-293) - MCP requirements
- B: Skills with MCP requirements (SCHEDULING, acgme-compliance, swap-management, startup)
- C: `.claude/settings.json` (enableAllProjectMcpServers: true)
- D: `server.py` (441-506) - @mcp.prompt() injection

## Next Steps
- Merge PR #684
- Use L3 pattern for future delegations
- Monitor if agents consistently use MCP tools with L3 prompts
