# Scratchpad Distillate - January 2026

> **Source:** 134 scratchpad files archived from Sessions 38-136
> **Distilled:** 2026-01-23
> **Purpose:** Preserve valuable insights before archival

---

## 1. Delegation Metrics & Performance Benchmarks

**Source:** `DELEGATION_METRICS.md`

### Healthy Ranges (Empirically Validated)

| Metric | Formula | Healthy Range | Gold Standard (Session 020) |
|--------|---------|---------------|----------------------------|
| Delegation Ratio | Task invocations / (Task + Edit + Write + Direct Bash) | 60-80% | 85% |
| Hierarchy Compliance | Correctly routed tasks / Total tasks | > 90% | 100% |
| Direct Edit Rate | ORCHESTRATOR edits / Total file modifications | < 30% | 20% |
| Parallel Factor | Max concurrent agents / Total agents spawned | > 1.5 | 6.0x |

### Anti-Patterns Identified

**One-Man Army (Sessions 004-005):**
- ORCHESTRATOR creating PRs directly instead of delegating to RELEASE_MANAGER
- Root cause: "It's faster if I just do it" rationalization
- Fix: Explicit delegation even for "quick" tasks

**Prevention:** If todo says "delegate X" but you're about to do X directly, STOP.

---

## 2. Marathon Execution Patterns

**Source:** `MARATHON_AAR.md` (36-hour marathon)

### Buffer Time Guidelines

- **Plan 25-50% buffer** for unexpected blockers
- **Session buffer:** 30 min between planned sessions
- **Blocker response time:** Max 15 min before escalating

### Pre-Flight Checklist

1. Environment validation (pytest runs, docker up)
2. Dependency check (no cryptography/cffi conflicts)
3. Clear branch state (no uncommitted changes)
4. RAG health check (rag_health tool)

### Key Metrics from Marathon

- 974 lines of new code across 5 sessions
- 149 commits merged
- 65% completion (5/9 sessions) due to environment blocker
- **Lesson:** Environment issues are #1 marathon killer

---

## 3. CCW Debugging Principle

**Source:** `CCW_BURN_POSTMORTEM.md`

### Volume Obscures Simplicity

> 134 identical errors ≠ 134 different problems.
> Pattern-match first, count second.

**The Illusion:** 134 failing files, 6-7 hour estimate
**The Reality:** 1 corrupted token pattern, 5-minute fix

### Token Concatenation Bug Pattern

```python
# CCW corruption:
result = await sawait ervice.validate_schedule()
#              ^^^^^^ ^^^^^^^  <- merged tokens

# Should be:
result = await service.validate_schedule()
```

### Prevention

Run validation gate every ~20 CCW tasks:
```bash
./.claude/scripts/ccw-validation-gate.sh
```

---

## 4. Security Findings Summary

**Source:** `SECURITY_REVIEW_MCP_TOOLS.md`

### Critical Vulnerabilities (2)

1. **PII Exposure in Burnout Tools**
   - Location: `resilience_integration.py` lines 94-130
   - Issue: `faculty_name`, `provider_id` exposed directly
   - HIPAA risk: Burnout data = health information
   - Fix: Anonymize with hash-based references

2. **Hardcoded Default Credentials**
   - Location: `api_client.py` lines 24-25
   - Issue: `username: str = "admin"`, `password: str = "admin123"`
   - Fix: Remove defaults, require env vars

### High Severity (5)

- H-1: Unbounded date range queries (DoS vector)
- H-2: Missing rate limiting on analytics endpoints
- H-3: Discrimination risk in workload equity tools
- H-4: Insufficient input validation on provider IDs
- H-5: Log injection via user-supplied strings

### Good Pattern Reference

`validate_schedule.py` lines 41-56 shows correct anonymization pattern.

---

## 5. Parallel Execution Methodology

**Source:** `100_TASK_PARALLEL_PLAN.md`

### 10-Terminal Decomposition Strategy

| Stream | Terminals | Task Count | Domain |
|--------|-----------|------------|--------|
| A | 1-3 | 30 | MCP Tool Completion |
| B | 4-6 | 25 | Backend Service Tests |
| C | 7-8 | 15 | Frontend Component Tests |
| D | 9 | 10 | Integration/E2E |
| E | 10 | 8 | Security Sweep |
| F | Overflow | 12 | Constraints + DB + Docs |

### Context Bundling Per Domain

**MCP Work:** server.py, api_client.py, tools/, backend routes
**Backend Tests:** services/, constraints/, resilience/, conftest.py
**Frontend Tests:** components/, lib/, __tests__/
**Security:** DATA_SECURITY_POLICY.md, auth.py, security.py

### Files to NEVER Share with CCW

- `.env` (credentials)
- `docs/data/*.json` (real schedule data)
- `.sanitize/` (PII mapping)

---

## 6. ACGME Compliance Gaps

**Source:** `MEDCOM_ACGME_AUDIT.md`

### Documented vs. Enforced Mismatches

| Rule | RAG Doc | Code Enforcement | Status |
|------|---------|------------------|--------|
| 10-hour minimum rest | 10 hours | 8 hours (FRMS only) | GAP |
| Night float limit | Not documented | 6 consecutive max | GAP |
| Call frequency (q3) | Documented | Not enforced | GAP |

### Action Items (Still Open)

1. Add night float section to `docs/rag-knowledge/acgme-rules.md`
2. Reconcile 10-hour rest (RAG) vs 8-hour (code) discrepancy
3. Implement call frequency constraint or document as policy-only

---

## Quick Reference Index

| Topic | Section |
|-------|---------|
| How parallel should my delegation be? | Section 1 (60-80% ratio) |
| What causes marathon failures? | Section 2 (environment issues) |
| Why are 100 errors showing up? | Section 3 (pattern-match first) |
| What security issues to watch for? | Section 4 (PII, credentials, DoS) |
| How to structure parallel CCW work? | Section 5 (domain decomposition) |
| What ACGME rules are gaps? | Section 6 (rest, night float, call freq) |

---

*Distilled from 134 archived scratchpad files. Full files preserved in `.claude/Scratchpad/archive/`*
