# PAI v1 Archive — February 2026

This directory contains the archived PAI (Parallel Agentic Infrastructure) v1 framework.

## Why Archived

The PAI v1 framework was built for earlier Claude models (Opus 4, Sonnet 3.5) that needed
extensive scaffolding — identity cards, rigid hierarchies, spawn chains, and governance
ceremonies. With Opus 4.6 and native Agent Teams support, this scaffolding is no longer
necessary.

## What Was Kept

The philosophical core of PAI lives on in the active codebase:

- **Auftragstaktik** (mission-type orders) — in `CLAUDE.md`
- **"System > Intelligence"** — in `.claude/Governance/PAI_SQUARED.md`
- **Permission Tiers** — in `CLAUDE.md`
- **MCP Tool Requirements** — in `CLAUDE.md`
- **Commander's Intent** — in `CLAUDE.md`

## Contents

| Directory | Contents | Count |
|-----------|----------|-------|
| `agents/` | Agent specification files | 55 |
| `identities/` | Agent identity cards | 57 |
| `governance/` | Archived governance docs | 7 |
| `skills/` | Archived skill definitions | ~57 |
| `reserves/` | Production reserve protocols | - |
| `protocols/` | Context party, checkpoint protocols | - |
| `sops/` | Standard operating procedures | - |
| `mcp/` | PAI Agent MCP Bridge | - |

## Restoration

If you need to restore any archived component:
```bash
git mv .claude/archive/<path> .claude/<original_path>
```

The git history preserves the full file history across the move.
