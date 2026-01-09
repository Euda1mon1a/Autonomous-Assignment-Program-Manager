# Session 082-084: Comprehensive Hook Expansion & Tuning

**Dates:** 2026-01-09
**Branch:** main (direct commits)

---

## Summary

**Session 082:** Consulted all 55 agents (8 advisory domains) to identify hook gaps. Expanded from 11 to 16 git pre-commit phases. Added PostToolUse Claude hook for metrics.

**Session 083:** Tuned hook patterns to eliminate false positives. Graduated ACGME/resilience to blocking mode. Added Phase 17 (constraint registration). Documented all disabled constraints.

**Session 084:** Added Phase 18 (MCP tool validation) for core tools (~34) and armory (~50). Validates BaseTool inheritance, input patterns, error handling, registration, and test coverage.

---

## Hook Ecosystem - Final State (18 Phases)

### Claude Code Hooks (4 total)
| Hook | Event | Domain | Status |
|------|-------|--------|--------|
| pre-bash-validate.sh | PreToolUse:Bash | Security | ✅ Working |
| pre-bash-dev-check.sh | PreToolUse:Bash | Development | ✅ Working |
| post-metrics-collect.sh | PostToolUse | Observability | ✅ Working |
| stop-verify.sh | Stop | Testing | ✅ Working |

### Git Pre-Commit Hooks (17 phases)
| Phase | Hook | Domain | Mode | Status |
|-------|------|--------|------|--------|
| 1 | pii-scan | Security | Blocking | ✅ Enhanced |
| 1 | gitleaks | Security | Blocking | ⚠️ 126 local false positives |
| 2-3 | ruff, mypy | Code Quality | Blocking | ✅ Working |
| 4 | pre-commit-hooks | Code Quality | Blocking | ✅ Working |
| 5 | bandit | Security | Blocking | ✅ Working |
| 6 | eslint | Code Quality | Blocking | ✅ Working |
| 7 | tsc | Type Safety | Blocking | ✅ Working |
| 8 | migration-names | Database | Blocking | ✅ Working |
| 9 | mcp-config | Infrastructure | Blocking | ✅ Working |
| 10 | commitizen | Documentation | Blocking | ✅ Working |
| 11 | yamllint | Code Quality | Blocking | ✅ Working |
| **12** | **acgme-validate** | **Compliance** | **BLOCKING** | ✅ Tuned Session 083 |
| **13** | **resilience-check** | **Resilience** | **BLOCKING** | ✅ Tuned Session 083 |
| **14** | **swap-validate** | **Scheduling** | Warning | ✅ Working |
| **15** | **schedule-integrity** | **Scheduling** | Warning | ✅ Working |
| **16** | **docs-check** | **Documentation** | Warning | ✅ Working |
| **17** | **constraint-registration** | **Scheduling** | Warning | ✅ NEW Session 083 |
| **18** | **mcp-tools-validate** | **MCP Tools** | Warning | ✅ NEW Session 084 |

---

## Session 083 Accomplishments

### 1. Pattern Tuning (Eliminated False Positives)

| Hook | Check | Old Pattern | New Pattern | Result |
|------|-------|-------------|-------------|--------|
| ACGME | Check 4 (bypass) | `acgme.*false` | `skip_acgme\|bypass_acgme\|disable_acgme` | ✅ Passes |
| ACGME | Check 6 (supervision) | `no.*attending` | + filter docstrings | ✅ Passes |
| Resilience | Check 1 (SPOF) | `no.*backup` | + exclude resilience framework | ✅ Passes |
| Resilience | Check 2 (N-1) | `n.?1.*false` | `skip_n1\|bypass_n1\|disable_n1_check` | ✅ Passes |
| Resilience | Check 5 (metrics) | `disable.*burnout` | `skip_burnout_check\|disable_burnout_alert` | ✅ Passes |

**Root cause:** Original patterns too broad - caught legitimate state assignments like `acgme_compliant = False` and result fields like `n1_pass=False`.

### 2. Graduated to Blocking Mode

| Hook | Before | After |
|------|--------|-------|
| ACGME Compliance (Phase 12) | exit 0 (warning) | **exit 1 (blocking)** |
| Resilience N-1/N-2 (Phase 13) | exit 0 (warning) | **exit 1 (blocking)** |

### 3. Phase 17: Constraint Registration Hook

**New file:** `scripts/validate-constraint-registration.sh`

**Checks:**
1. ✅ `__all__` completeness - all imports must be exported
2. ⚠️ Manager registration - 51 exported, 40 registered (11 intentionally optional)
3. ✅ Disabled constraint documentation - all 11 now have comments
4. ✅ Test file exists

### 4. Documented Disabled Constraints

Added explanatory comments above each `manager.disable()` call in `backend/app/scheduling/constraints/manager.py`:

- OvernightCallGeneration: requires explicit opt-in
- PostCallAutoAssignment: requires post-call scheduling enabled
- SM constraints: need SM program data
- FMIT constraints: need FMIT week configuration
- ProtectedSlot/HalfDayRequirement/ActivityRequirement: need rotation config
- Tier 2 resilience: aggressive protection, may over-constrain

---

## Session 083-084 Commits (on main, need push)

| Commit | Description |
|--------|-------------|
| `28836138` | Pattern tuning (Check 2, 4, 5) |
| `ee09996a` | Graduate to blocking + additional tuning (Check 1, 6) |
| `e4d6b35f` | Scratchpad update |
| `e6c2d7c9` | Phase 17 constraint registration hook |
| `4131f50a` | Disabled constraint comments |
| `cd65a928` | Session 083 scratchpad documentation |
| `d035cf5e` | Phase 18 MCP tool validation hook |

---

## Remaining Roadmap

### Completed (Session 082-084)
- ~~Tune ACGME hook patterns~~ ✅
- ~~Tune resilience hook patterns~~ ✅
- ~~Graduate hooks to blocking~~ ✅
- ~~Add constraint registration hook~~ ✅
- ~~MCP tool validation hook~~ ✅

### P1 - High (Next Up)
- **Test coverage threshold hook** - Block commits below coverage threshold

### P2 - Medium
- Bundle size monitoring
- API contract validation

### P3 - Low
- Performance regression hook
- Dependency security scanning (npm/pip audit)
- Docker image scanning

### Deferred
- **Gitleaks config** - 126 findings are mostly docs/tests examples + local log JWTs (not git-tracked)

---

## Architecture Achieved

```
┌─────────────────────────────────────────────────────────────┐
│                    HOOK ECOSYSTEM (18 Phases)               │
├─────────────────────────────────────────────────────────────┤
│ LAYER 1: Claude Code (Real-time AI guardrails)              │
│   PreToolUse:Bash → Security + Dev Experience               │
│   PostToolUse → Metrics Collection                          │
│   Stop → Session Cleanup                                    │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2: Git Pre-Commit (Commit-time validation)            │
│   Phases 1-11 → Code Quality                                │
│   Phases 12-18 → Business Logic                             │
│     12: ACGME Compliance (BLOCKING)                         │
│     13: Resilience N-1/N-2 (BLOCKING)                       │
│     14: Swap Safety (warning)                               │
│     15: Schedule Integrity (warning)                        │
│     16: Documentation (warning)                             │
│     17: Constraint Registration (warning)                   │
│     18: MCP Tool Validation (warning)                       │
├─────────────────────────────────────────────────────────────┤
│ LAYER 3: Guidance Documents (Human workflow)                │
│   post-compliance-audit.md                                  │
│   post-schedule-generation.md                               │
│   post-resilience-test.md                                   │
│   post-swap-execution.md                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Handoff Notes

Session 082-084 established a comprehensive hook ecosystem:

1. **Code Quality** (Phases 1-11) - Standard linting, type checking, security scanning
2. **Business Logic** (Phases 12-18) - ACGME, resilience, scheduling, constraints, MCP tools
3. **Two hooks now block commits** - ACGME and Resilience (after pattern tuning)
4. **Constraint registration** prevents "implemented but not registered" bugs
5. **MCP tool validation** catches BaseTool structure issues in 84 tools (34 core + 50 armory)

**Key insight:** The gap between "good code" and "good schedules" is now monitored. Hooks catch both code quality issues AND domain-specific violations.

**To push:** `git push origin main` (7 commits pending)

o7
