# Antigravity IDE Configuration

> **Purpose:** Configuration for reliable autonomous AI-assisted development
> **Last Updated:** 2025-12-22

---

## Quick Start

1. Open this repository in Antigravity IDE
2. Antigravity auto-loads configuration from this directory
3. Start with **Review Mode** to learn the patterns
4. Graduate to **Autopilot** when comfortable

---

## Current Status

| Mode | Status | Description |
|------|--------|-------------|
| **A. Autopilot** | ACTIVE | Single agent, autonomous with guardrails |
| **B. Manager View** | FUTURE | Parallel agents (5 max) - not yet activated |
| **C. Auto Triggers** | FUTURE | Webhook/scheduled triggers - not yet activated |
| **D. Hybrid Orchestration** | CONCEPT | Opus tactician + Qwen squad - for evaluation |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `settings.json` | Main IDE configuration |
| `guardrails.md` | Operations requiring human approval |
| `autopilot-instructions.md` | Autonomous operation guidelines |
| `recovery.md` | Failure handling procedures |
| `FUTURE_B_MANAGER_VIEW.md` | Parallel agent config (not active) |
| `FUTURE_C_AUTO_TRIGGERS.md` | Trigger config (not active) |
| `logs/` | Autopilot logs and audit trail |

---

## Reliability Goals

### For Autopilot (A)
- **Target:** 95%+ task completion without escalation
- **Guardrails:** Strict (see `guardrails.md`)
- **Recovery:** Automatic for Level 1-2 failures

### Progression Path
```
Autopilot (A) stable
      ↓
Enable Manager View (B)
      ↓
Manager View stable
      ↓
Enable Auto Triggers (C)
```

---

## Integration with Existing Config

This directory works alongside:
- `.claude/skills/` - Domain knowledge (6 skills)
- `.claude/commands/` - Slash commands (6 commands)
- `mcp-server/` - Backend API tools (16+ tools)
- `CLAUDE.md` - Project guidelines

---

## Logging

Logs are written to `./logs/`:
- `autopilot.log` - All agent actions
- `guardrail-triggers.log` - Blocked operations
- `recovery.log` - Recovery events

Logs are gitignored by default. To track metrics, copy relevant entries to `docs/sessions/`.

---

## Troubleshooting

### Autopilot Not Starting
1. Check `settings.json` is valid JSON
2. Verify `autopilot.enabled: true`
3. Restart Antigravity IDE

### Guardrails Too Strict
1. Review `guardrails.md`
2. Adjust `guardrails.level` in settings (strict/moderate/relaxed)
3. Add specific overrides if needed

### Recovery Not Working
1. Check git status is clean
2. Verify no uncommitted migrations
3. Review `recovery.md` procedures

---

## Contact

For issues with this configuration:
1. Check `docs/guides/AI_AGENT_USER_GUIDE.md`
2. Review session notes in `docs/sessions/`
3. Consult `CLAUDE.md` for project context
