# Hooks Ecosystem

> Last Updated: 2026-01-09 (Session 082)

This project uses two hook systems:
1. **Claude Code Hooks** - Intercept AI tool calls
2. **Git Hooks** - Run on git operations (via pre-commit framework)

---

## Claude Code Hooks

Configured in `~/.claude/settings.json`. These intercept Claude Code tool calls.

### Active Hooks

| Hook | Event | File | Purpose |
|------|-------|------|---------|
| pre-bash-validate | PreToolUse:Bash | `pre-bash-validate.sh` | Block dangerous commands |
| pre-bash-dev-check | PreToolUse:Bash | `pre-bash-dev-check.sh` | Warn about non-dev configs (hot reload) |
| stop-verify | Stop | `stop-verify.sh` | Warn about uncommitted changes |

### Available Scripts (Not Auto-Triggered)

| File | Purpose | Why Not Auto |
|------|---------|--------------|
| `session-start.sh` | Environment checks at session start | No `Start` event in Claude Code |
| `pre-plan-orchestrator.sh` | Complexity scoring before planning | No `EnterPlanMode` event |

**Workaround:** The `/startup` skill covers session-start functionality.

### Documentation Files

These are **guidance documents**, not executable hooks:
- `post-compliance-audit.md` - ACGME compliance audit workflow
- `post-resilience-test.md` - Resilience framework testing
- `post-schedule-generation.md` - Schedule generation validation
- `post-swap-execution.md` - Swap execution audit trail

### Testing Claude Hooks

```bash
# Test pre-bash validation (should pass)
echo '{"tool_input": {"command": "ls"}}' | ./.claude/hooks/pre-bash-validate.sh && echo "OK"

# Test blocked command (should fail with exit 2)
echo '{"tool_input": {"command": "git push --force"}}' | ./.claude/hooks/pre-bash-validate.sh 2>&1
```

---

## Git Hooks (pre-commit Framework)

Configured in `.pre-commit-config.yaml`. Runs 11 phases on commit.

### Installation

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

### Phases

| Phase | Hook | What It Does |
|-------|------|--------------|
| 1 | PII/OPSEC scanner | Catches SSN patterns, .mil emails |
| 1 | Gitleaks | Detects secrets/credentials |
| 2 | Ruff lint | Python linting |
| 2 | Ruff format | Python formatting |
| 3 | MyPy | Python type checking |
| 4 | pre-commit-hooks | Merge conflicts, whitespace, large files |
| 5 | Bandit | Python security scanning |
| **6** | **ESLint** | **TypeScript linting (catches camelCase violations)** |
| 7 | TypeScript | Type checking |
| 8 | Migration names | Validates Alembic revision ID length |
| 9 | MCP config | Validates MCP configuration |
| 10 | Commitizen | Conventional commit format |
| 11 | YAMLLint | YAML syntax validation |

### Testing Git Hooks

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run eslint --all-files

# Run on staged files only (normal commit behavior)
git add .
pre-commit run
```

---

## camelCase Enforcement (Session 081-082)

TypeScript interfaces must use camelCase because the axios interceptor converts snake_case responses.

### Defense Layers

| Layer | Location | Type |
|-------|----------|------|
| ESLint rule | `frontend/eslint.config.js` | Build-time |
| Tests | `frontend/__tests__/lib/api-case-conversion.test.ts` | CI |
| Documentation | `CLAUDE.md` lines 97-104 | Human |
| Skill | `.claude/skills/check-camelcase/` | AI |
| Pattern docs | `.claude/dontreadme/synthesis/PATTERNS.md` | AI |
| **Git hook** | `.pre-commit-config.yaml` Phase 6 | Commit-time |

### Quick Scan

```bash
# Manual scan for snake_case in TypeScript interfaces
grep -rn "[a-z]_[a-z].*:" frontend/src --include="*.ts" --include="*.tsx" | grep -v node_modules

# Or use the skill
/check-camelcase
```

---

## Troubleshooting

### Pre-commit environments stale
```bash
pre-commit clean
pre-commit install
```

### Hook not running
```bash
# Verify hooks are installed
ls -la .git/hooks/pre-commit .git/hooks/commit-msg
```

### PII scan catching test data
The PII scanner catches mock SSNs like `123-45-6789` in test files. This is intentional - review and allowlist if the test data is legitimate.

---

## Dev Environment Hook (Session 082)

The `pre-bash-dev-check.sh` hook warns about commands that bypass hot reload:

### What It Catches

| Pattern | Warning |
|---------|---------|
| `docker-compose up` without `-f *.dev.yml` | Suggests dev config |
| `docker-compose build` | Reminds about volume mounts |
| `npm run build` in frontend | Suggests `npm run dev` |
| `uvicorn` without `--reload` | Adds reload flag |
| `next start` | Suggests `npm run dev` |
| `docker exec ... pytest` | Suggests local pytest |
| `docker exec ... alembic` | Suggests local alembic |

### Testing

```bash
# Should warn about missing dev config
echo '{"tool_input": {"command": "docker-compose up"}}' | ./.claude/hooks/pre-bash-dev-check.sh

# Should pass silently (dev config present)
echo '{"tool_input": {"command": "docker-compose -f docker-compose.dev.yml up"}}' | ./.claude/hooks/pre-bash-dev-check.sh
```
