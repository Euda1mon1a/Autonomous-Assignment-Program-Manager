# Hooks and Scripts Consolidation Roadmap

> **Created:** 2026-01-19
> **Last Updated:** 2026-01-19
> **Source:** PLAN_PARTY Analysis (10 probes, 8.5/10 convergence score)
> **Purpose:** Consolidate and optimize repository automation for developer and AI workflows

---

## DEVIATION POLICY (READ FIRST)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║  DEVIATION FROM THIS ROADMAP IS NOT ALLOWED UNLESS:                           ║
║                                                                               ║
║  1. There is a CRITICAL blocker that can ONLY be resolved locally             ║
║  2. Tests are failing and must be fixed before proceeding                     ║
║  3. Security vulnerability is discovered that requires immediate action       ║
║  4. Hook changes break CI/CD pipeline                                         ║
║                                                                               ║
║  IF DEVIATION IS REQUIRED:                                                    ║
║  → STOP and report back with: "DEVIATION REQUIRED: [reason]"                  ║
║  → Wait for human approval before proceeding with alternative path            ║
║  → Document the deviation in this file under "Deviation Log"                  ║
║                                                                               ║
║  DO NOT:                                                                      ║
║  - Add new hooks not in this roadmap                                          ║
║  - Refactor "while you're in there"                                           ║
║  - Change hook behavior without approval                                      ║
║  - Remove hooks without documented justification                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### Deviation Log

| Date | Reason | Approved By | Resolution |
|------|--------|-------------|------------|
| - | - | - | - |

---

## CURRENT STATE INVENTORY

### Git Hooks (3 active)

| Hook | Purpose | Trigger | Location |
|------|---------|---------|----------|
| `pre-commit` | 24-phase validation framework | Before commit | `.pre-commit-config.yaml` |
| `commit-msg` | Conventional commit enforcement | After message | Commitizen |
| `post-merge` | Post-merge actions | After merge | `.git/hooks/` |

### Pre-commit Phases (24 total)

| Phase | ID | Name | Domain | Status |
|-------|-----|------|--------|--------|
| 1 | `pii-scan` | PII/OPSEC scanner | SECURITY_AUDITOR | Blocking |
| 1 | `gitleaks` | Secret detection | SECURITY_AUDITOR | Blocking |
| 2 | `ruff` | Python linting | COORD_QUALITY | Blocking |
| 2 | `ruff-format` | Python formatting | COORD_QUALITY | Blocking |
| 3 | `mypy` | Python type checking | COORD_QUALITY | **Advisory** (`|| true`) |
| 4 | General | 8 file quality hooks | COORD_QUALITY | Blocking |
| 5 | `bandit` | Python security | SECURITY_AUDITOR | **Advisory** (`|| true`) |
| 6 | `eslint` | Frontend linting | COORD_FRONTEND | **Advisory** (`|| true`) |
| 6b | `couatl-killer` | snake_case params | COORD_FRONTEND | Blocking |
| 7 | `tsc` | TypeScript check | COORD_FRONTEND | **Advisory** (`|| true`) |
| 8 | `migration-names` | Alembic ID length | DBA | Blocking |
| 8b | `lichs-phylactery` | Schema snapshot | DBA | Blocking |
| 9 | `mcp-config` | MCP validation | COORD_TOOLING | Blocking |
| 10 | `commitizen` | Commit format | COORD_QUALITY | Blocking |
| 11 | `yamllint` | YAML validation | COORD_QUALITY | Blocking |
| 12 | `acgme-validate` | ACGME compliance | MEDCOM | Blocking |
| 13 | `resilience-check` | N-1/N-2 validation | RESILIENCE_ENGINEER | Blocking |
| 14 | `swap-validate` | Swap safety | SWAP_MANAGER | Blocking |
| 15 | `schedule-integrity` | Schedule data | SCHEDULER | Blocking |
| 16 | `docs-check` | Documentation | META_UPDATER | Blocking |
| 17 | `constraint-registration` | Constraint registry | SCHEDULER | Blocking |
| 18 | `mcp-tools-validate` | MCP tool structure | COORD_TOOLING | Blocking |
| 19 | `test-coverage` | Test reminder | QA_TESTER | Blocking |
| 20 | `bundle-size` | Bundle monitor | COORD_FRONTEND | Blocking |
| 21 | `api-contract` | API sync | ARCHITECT | Blocking |
| 22 | `performance-regression` | Perf check | QA_TESTER | Blocking |
| 23 | `dependency-versions` | Dep guard | ARCHITECT | Blocking |
| 24 | `beholder-bane` | SQLAlchemy anti-magic | SCHEDULER | Blocking |

**D&D-Themed Hooks:** Couatl Killer, Lich's Phylactery, Beholder Bane

### Claude Code Hooks (6 scripts in `.claude/hooks/`)

| Script | Trigger Event | Status | Purpose |
|--------|---------------|--------|---------|
| `pre-bash-validate.sh` | PreToolUse | Active | Dangerous command blocking |
| `pre-bash-dev-check.sh` | PreToolUse | Active | Dev environment validation |
| `post-metrics-collect.sh` | PostToolUse | Active | Usage metrics collection |
| `stop-verify.sh` | Stop | Active | Session end verification |
| `session-start.sh` | (manual) | Partial | No Start event workaround |
| `pre-plan-orchestrator.sh` | (manual) | Partial | Plan mode prep |

**Markdown Guidance Docs (6):** `post-compliance-audit.md`, `post-schedule-generation.md`, etc.

### Shell Scripts (`/scripts/` - 45 total)

| Category | Count | Examples |
|----------|-------|----------|
| Validation | 13 | `validate-acgme-compliance.sh`, `validate-resilience-constraints.sh` |
| Operations | 8 | `start-local.sh`, `rebuild-containers.sh` |
| Database | 6 | `backup-db.sh`, `seed_*.py` |
| Monitoring | 4 | `stack-health.sh`, `diagnose-container-staleness.sh` |
| D&D hooks | 3 | `couatl-killer.sh`, `lichs-phylactery.sh`, `beholder-bane.sh` |
| Backup (overlapping) | 3 | `backup_full_stack.sh`, `full-stack-backup.sh`, `stack-backup.sh` |
| Development | 3 | `dev-setup.sh`, `quick-test.sh` |
| Excel | 2 | `excel_to_json.py`, `json_to_excel.py` |

### CI/CD Workflows (`.github/workflows/` - 17 total)

| Workflow | Purpose | Relationship to Local |
|----------|---------|----------------------|
| `ci.yml` | Main CI pipeline | Mirrors pre-commit phases |
| `quality-gates.yml` | Quality enforcement | Catches bypass attempts |
| `security.yml` | Security scans | Enhanced Gitleaks |
| `pii-scan.yml` | PII detection | Mirrors Phase 1 |
| `code-quality.yml` | Lint/format | Mirrors Phases 2-7 |

---

## GAP ANALYSIS

### Priority 1: Security/Compliance

| Gap | Risk Level | Current State | Impact |
|-----|------------|---------------|--------|
| No pre-push hook | HIGH | Missing | Dangerous ops reach remote |
| Personnel names hardcoded | MEDIUM | `pii-scan.sh:195-196` | Maintenance burden |
| No Gitleaks history scan | MEDIUM | Files only | Secrets in history missed |

### Priority 2: Performance

| Gap | Impact | Current State | Target |
|-----|--------|---------------|--------|
| 24 sequential phases | 15-30s commits | `.pre-commit-config.yaml` | <10s |
| No parallel execution | Wasted time | All sequential | Parallelize 2-7 |

### Priority 3: Reliability

| Gap | Risk | Current State | Recommendation |
|-----|------|---------------|----------------|
| MyPy advisory only | Type bugs | `|| true` in Phase 3 | Graduate to blocking |
| Bandit advisory only | Security issues | `|| true` in Phase 5 | Graduate to blocking |
| ESLint advisory only | Lint issues | `|| true` in Phase 6 | Graduate to blocking |
| TSC advisory only | Type issues | `|| true` in Phase 7 | Graduate to blocking |

### Priority 4: Maintainability

| Gap | Impact | Current State | Recommendation |
|-----|--------|---------------|----------------|
| 3 overlapping backup scripts | Confusion | Deprecated but present | Consolidate to 1 |
| Claude Code hooks incomplete | No RAG injection | session-start workaround | Implement properly |
| Undocumented scripts | Onboarding friction | Missing headers | Add documentation |

---

## DOMAIN OWNERSHIP MAP

| Domain | Coordinator | Scripts Owned |
|--------|-------------|---------------|
| Security/PII | SECURITY_AUDITOR | `pii-scan.sh`, Gitleaks config, `bandit` |
| ACGME Compliance | MEDCOM | `validate-acgme-compliance.sh` |
| Resilience | RESILIENCE_ENGINEER | `validate-resilience-constraints.sh` |
| Swaps | SWAP_MANAGER | `validate-swap-safety.sh` |
| Schedule | SCHEDULER | `validate-schedule-integrity.sh`, `validate-constraint-registration.sh` |
| MCP/Tools | COORD_TOOLING | `validate-mcp-*.sh`, `.claude/hooks/*` |
| Frontend | COORD_FRONTEND | `couatl-killer.sh`, ESLint, TSC |
| Database | DBA | `lichs-phylactery.sh`, backup scripts |
| Operations | COORD_OPS | CI workflows, release scripts |
| Quality | COORD_QUALITY | Ruff, MyPy, general file hooks |

---

## IMPLEMENTATION PHASES

### Phase 1: Quick Wins (2-3 sessions)

**Owner:** COORD_OPS
**Goal:** Reduce friction without breaking workflows
**Risk Level:** LOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT PROTOCOL - PHASE 1                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  After completing EACH task:                                                │
│  1. Test locally: `pre-commit run --all-files`                              │
│  2. COMMIT with descriptive message                                         │
│  3. REPORT: "P1.[N] Complete: [summary]"                                    │
│  4. WAIT for confirmation before next task                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

| ID | Task | Effort | Files | Verification |
|----|------|--------|-------|--------------|
| P1.1 | Enable parallel pre-commit stages 2-7 | 1h | `.pre-commit-config.yaml` | Commit time <10s |
| P1.2 | Consolidate backup scripts to single `stack-backup.sh` | 2h | `scripts/backup*.sh` | Single script, modes work |
| P1.3 | Externalize PII names to `.pii-scan-config.yaml` | 1h | `scripts/pii-scan.sh` | Config file sourced |
| P1.4 | Add documentation headers to undocumented scripts | 2h | `scripts/*.sh` | All scripts have headers |
| P1.5 | Remove deprecated backup scripts | 30m | `scripts/backup_full_stack.sh`, `scripts/full-stack-backup.sh` | Only `stack-backup.sh` remains |

**Verification Checklist:**
- [ ] `pre-commit run --all-files` completes in <10s (was 15-30s)
- [ ] `scripts/stack-backup.sh --mode=quick` works
- [ ] `scripts/stack-backup.sh --mode=full` works
- [ ] `scripts/stack-backup.sh --mode=db` works
- [ ] `scripts/pii-scan.sh` reads from `.pii-scan-config.yaml`
- [ ] All scripts in `/scripts/` have documentation headers

---

### Phase 2: Hook Hardening (2-3 sessions)

**Owner:** COORD_TOOLING
**Goal:** Strengthen safety gates
**Risk Level:** MEDIUM (may block commits initially)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT PROTOCOL - PHASE 2                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Before graduating advisory hooks to blocking:                              │
│  1. Run full check: `mypy backend/app/ --ignore-missing-imports`            │
│  2. Count violations: Document current error count                          │
│  3. Fix violations FIRST, then remove `|| true`                             │
│  4. Test with team before merging                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

| ID | Task | Effort | Files | Verification |
|----|------|--------|-------|--------------|
| P2.1 | Add pre-push hook for remote-aware validation | 1h | `.pre-commit-config.yaml` | Push blocked on failures |
| P2.2 | Fix existing MyPy violations | 2h | `backend/app/**/*.py` | Zero errors |
| P2.3 | Graduate MyPy to blocking (remove `|| true`) | 30m | `.pre-commit-config.yaml` | Commits blocked on type errors |
| P2.4 | Fix existing Bandit violations | 1h | `backend/app/**/*.py` | Zero high/medium issues |
| P2.5 | Graduate Bandit to blocking (remove `|| true`) | 30m | `.pre-commit-config.yaml` | Commits blocked on security issues |
| P2.6 | Audit and fix `|| true` patterns in validate-*.sh | 1h | `scripts/validate-*.sh` | No silent failures |

**Verification Checklist:**
- [ ] `git push` blocked when pre-push hooks fail
- [ ] `mypy backend/app/` returns exit code 0
- [ ] `bandit -r backend/app -ll` returns exit code 0
- [ ] No `|| true` in production validation scripts

---

### Phase 3: AI Workflow Enhancement (3-4 sessions)

**Owner:** COORD_TOOLING
**Goal:** Improve Claude Code integration
**Risk Level:** LOW (additive changes)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT PROTOCOL - PHASE 3                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Test Claude Code hooks in isolated session:                                │
│  1. Create test session                                                     │
│  2. Verify hook triggers correctly                                          │
│  3. Check metrics/logs generated                                            │
│  4. Confirm no workflow disruption                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

| ID | Task | Effort | Files | Verification |
|----|------|--------|-------|--------------|
| P3.1 | Implement RAG context injection in session-start | 3h | `.claude/hooks/session-start.sh` | RAG context auto-loaded |
| P3.2 | Add anomaly detection to post-metrics-collect | 2h | `.claude/hooks/post-metrics-collect.sh` | Alerts on unusual patterns |
| P3.3 | Create hook bypass audit log | 2h | `.claude/hooks/bypass-audit.log` | Bypasses logged with reason |
| P3.4 | Update hooks README with full capabilities | 1h | `.claude/hooks/README.md` | Complete documentation |
| P3.5 | Implement proper Start event handler | 2h | `.claude/hooks/session-start.sh` | No manual workaround needed |

**Verification Checklist:**
- [ ] Session start automatically queries relevant RAG context
- [ ] Metrics collection alerts on anomalies (e.g., >10 tool failures)
- [ ] Hook bypasses logged in `.claude/hooks/bypass-audit.log`
- [ ] `.claude/hooks/README.md` documents all hooks and triggers

---

### Phase 4: Compliance Hardening (2-3 sessions)

**Owner:** COORD_OPS
**Goal:** Military medical context compliance
**Risk Level:** MEDIUM (policy decisions required)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CHECKPOINT PROTOCOL - PHASE 4                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  GPG signing requires human decision:                                       │
│  1. Document requirements (military audit trail needs)                      │
│  2. Present options with pros/cons                                          │
│  3. Get explicit approval before implementation                             │
│  4. If approved, provide setup guide for developers                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

| ID | Task | Effort | Files | Verification |
|----|------|--------|-------|--------------|
| P4.1 | Evaluate GPG signing requirements | 1h | `docs/decisions/GPG_SIGNING_DECISION.md` | Decision documented |
| P4.2 | Add weekly Gitleaks history scan | 2h | `.github/workflows/security.yml` | Weekly scan runs |
| P4.3 | Create hook effectiveness dashboard | 3h | `scripts/hook-metrics.sh` | Metrics visible |
| P4.4 | (If approved) Implement GPG signing enforcement | 2h | `.pre-commit-config.yaml` | Unsigned commits blocked |

**Verification Checklist:**
- [ ] GPG decision documented with rationale
- [ ] Weekly Gitleaks history scan in CI (Actions tab)
- [ ] Hook effectiveness metrics available via `scripts/hook-metrics.sh`
- [ ] (If applicable) GPG signing enforced with developer onboarding guide

---

## RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Parallel pre-commit breaks phase ordering | Medium | High | Test thoroughly, keep sequential fallback |
| Strict MyPy blocks too many commits | High | Medium | Fix all violations FIRST, then graduate |
| Backup consolidation loses functionality | Low | High | Test all modes before removing old scripts |
| Claude hooks break AI workflow | Low | High | Test in isolated session first |
| GPG signing creates onboarding friction | Medium | Medium | Evaluate requirements, provide clear guide |
| Pre-push hook too slow | Medium | Low | Use lightweight checks only |

---

## SUCCESS METRICS

| Metric | Current | Target | Phase | How to Measure |
|--------|---------|--------|-------|----------------|
| Commit time | 15-30s | <10s | 1 | `time pre-commit run --all-files` |
| Backup scripts | 3 | 1 | 1 | `ls scripts/*backup*` |
| MyPy enforcement | Advisory | Blocking | 2 | Check `.pre-commit-config.yaml` |
| Bandit enforcement | Advisory | Blocking | 2 | Check `.pre-commit-config.yaml` |
| Pre-push hook | Missing | Active | 2 | `git push` triggers validation |
| RAG injection | None | Automatic | 3 | Session start loads context |
| Hook bypass logging | None | Complete | 3 | `cat .claude/hooks/bypass-audit.log` |

---

## APPENDIX: File Inventory

### Scripts to Modify

| File | Phase | Change |
|------|-------|--------|
| `.pre-commit-config.yaml` | 1, 2 | Parallelize, add pre-push, remove `|| true` |
| `scripts/pii-scan.sh` | 1 | Source names from config file |
| `scripts/stack-backup.sh` | 1 | Add mode flags |
| `.claude/hooks/session-start.sh` | 3 | RAG injection |
| `.claude/hooks/post-metrics-collect.sh` | 3 | Anomaly detection |
| `.github/workflows/security.yml` | 4 | Weekly history scan |

### Scripts to Create

| File | Phase | Purpose |
|------|-------|---------|
| `.pii-scan-config.yaml` | 1 | External personnel names list |
| `.claude/hooks/bypass-audit.log` | 3 | Hook bypass tracking |
| `scripts/hook-metrics.sh` | 4 | Effectiveness dashboard |
| `docs/decisions/GPG_SIGNING_DECISION.md` | 4 | GPG policy decision |

### Scripts to Remove

| File | Phase | Reason |
|------|-------|--------|
| `scripts/backup_full_stack.sh` | 1 | Deprecated, consolidated |
| `scripts/full-stack-backup.sh` | 1 | Deprecated, consolidated |

---

## RELATED DOCUMENTS

- `HUMAN_TODO.md` - Master priority list entry
- `.claude/hooks/README.md` - Hooks ecosystem documentation
- `.pre-commit-config.yaml` - Pre-commit configuration
- `docs/planning/BLOCK_10_ROADMAP.md` - Template pattern reference

---

*Generated by PLAN_PARTY (G5_PLANNING) - 2026-01-19*
