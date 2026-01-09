# Hooks Ecosystem

> Last Updated: 2026-01-09 (Session 082 - Comprehensive Expansion)

This project uses two hook systems:
1. **Claude Code Hooks** - Intercept AI tool calls
2. **Git Hooks** - Run on git operations (via pre-commit framework)

---

## Claude Code Hooks

Configured in `~/.claude/settings.json`. These intercept Claude Code tool calls.

### Active Hooks

| Hook | Event | File | Domain | Purpose |
|------|-------|------|--------|---------|
| pre-bash-validate | PreToolUse:Bash | `pre-bash-validate.sh` | Security | Block dangerous commands |
| pre-bash-dev-check | PreToolUse:Bash | `pre-bash-dev-check.sh` | Development | Warn about non-dev configs |
| post-metrics-collect | PostToolUse | `post-metrics-collect.sh` | Observability | Collect session metrics |
| stop-verify | Stop | `stop-verify.sh` | Testing | Warn about uncommitted changes |

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

# Test dev check warning
echo '{"tool_input": {"command": "docker-compose up"}}' | ./.claude/hooks/pre-bash-dev-check.sh 2>&1
```

---

## Git Hooks (pre-commit Framework)

Configured in `.pre-commit-config.yaml`. Now runs **16 phases** on commit.

### Installation

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

### Phases

| Phase | Hook | Domain | Advisory Agent |
|-------|------|--------|----------------|
| 1 | PII/OPSEC scanner | Security | SECURITY_AUDITOR |
| 1 | Gitleaks | Security | SECURITY_AUDITOR |
| 2 | Ruff lint | Code Quality | - |
| 2 | Ruff format | Code Quality | - |
| 3 | MyPy | Type Safety | - |
| 4 | pre-commit-hooks | Code Quality | - |
| 5 | Bandit | Security | SECURITY_AUDITOR |
| 6 | ESLint | Code Quality | - |
| 7 | TypeScript | Type Safety | - |
| 8 | Migration names | Database | - |
| 9 | MCP config | Infrastructure | - |
| 10 | Commitizen | Documentation | - |
| 11 | YAMLLint | Code Quality | - |
| **12** | **ACGME Compliance** | **Compliance** | **MEDCOM** |
| **13** | **Resilience N-1/N-2** | **Resilience** | **RESILIENCE_ENGINEER** |
| **14** | **Swap Safety** | **Scheduling** | **SWAP_MANAGER** |
| **15** | **Schedule Integrity** | **Scheduling** | **SCHEDULER** |
| **16** | **Documentation** | **Documentation** | **META_UPDATER** |

### Testing Git Hooks

```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run acgme-validate --all-files
pre-commit run resilience-check --all-files

# Run on staged files only (normal commit behavior)
git add .
pre-commit run
```

---

## Hook Architecture (Session 082)

```
LAYER 1: Claude Code Hooks (Real-time AI guardrails)
├── PreToolUse:Bash
│   ├── pre-bash-validate.sh (security)
│   └── pre-bash-dev-check.sh (dev experience)
├── PostToolUse
│   └── post-metrics-collect.sh (observability)
└── Stop
    └── stop-verify.sh (uncommitted changes)

LAYER 2: Git Pre-Commit Hooks (Commit-time validation)
├── Phases 1-11: Code Quality (existing)
├── Phase 12: ACGME Compliance (MEDCOM)
├── Phase 13: Resilience N-1/N-2 (RESILIENCE_ENGINEER)
├── Phase 14: Swap Safety (SWAP_MANAGER)
├── Phase 15: Schedule Integrity (SCHEDULER)
└── Phase 16: Documentation (META_UPDATER)

LAYER 3: Guidance Documents (Human workflow)
├── post-compliance-audit.md
├── post-schedule-generation.md
├── post-resilience-test.md
└── post-swap-execution.md
```

---

## Advisory Domain Mapping

| Domain | Advisory Agent | Hooks |
|--------|----------------|-------|
| ACGME/Clinical | MEDCOM | Phase 12: validate-acgme-compliance.sh |
| Resilience | RESILIENCE_ENGINEER | Phase 13: validate-resilience-constraints.sh |
| Swaps | SWAP_MANAGER | Phase 14: validate-swap-safety.sh |
| Scheduling | SCHEDULER | Phase 15: validate-schedule-integrity.sh |
| Documentation | META_UPDATER | Phase 16: validate-documentation.sh |
| Security | SECURITY_AUDITOR | Phase 1, 5 + enhanced pii-scan.sh |
| Observability | G6_SIGNAL | PostToolUse: post-metrics-collect.sh |
| Development | - | PreToolUse: pre-bash-dev-check.sh |

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
| Git hook | `.pre-commit-config.yaml` Phase 6 | Commit-time |

---

## Dev Environment Hook (Session 082)

The `pre-bash-dev-check.sh` hook warns about commands that bypass hot reload:

| Pattern | Warning |
|---------|---------|
| `docker-compose up` without `-f *.dev.yml` | Suggests dev config |
| `docker-compose build` | Reminds about volume mounts |
| `npm run build` in frontend | Suggests `npm run dev` |
| `uvicorn` without `--reload` | Adds reload flag |
| `next start` | Suggests `npm run dev` |
| `docker exec ... pytest` | Suggests local pytest |
| `docker exec ... alembic` | Suggests local alembic |

---

## Metrics Collection (Session 082)

The `post-metrics-collect.sh` hook logs session activity to `~/.claude/metrics/session_metrics.jsonl`.

**Metrics tracked:**
- Tool execution counts
- Error rates
- Timestamps

**Log format:** JSON Lines (one JSON object per line)

**Rotation:** Automatic at 10MB

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

### Test individual hooks
```bash
# ACGME
./scripts/validate-acgme-compliance.sh

# Resilience
./scripts/validate-resilience-constraints.sh

# Swap Safety
./scripts/validate-swap-safety.sh

# Schedule Integrity
./scripts/validate-schedule-integrity.sh

# Documentation
./scripts/validate-documentation.sh
```

### PII scan catching test data
The PII scanner catches mock SSNs like `123-45-6789` in test files. Test directories are excluded.
