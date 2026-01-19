# PAI² Governance Revision Proposal

**Source:** PLAN_PARTY analysis (10 probes) on `docs/HUMAN_REPORT_ARMY_FM_PHYSICIAN.md`
**Date:** 2026-01-18
**Author:** ORCHESTRATOR + G5_PLANNING
**Status:** AWAITING REVIEW

---

## Executive Summary

The HUMAN_REPORT identified 7 gaps in PAI² (Parallel Agent Infrastructure) governance. This proposal addresses all 7 through a phased approach with parallel execution where possible. All changes are documentation-only with simple rollback.

**Key Decision Required:** Gap 3 has a 5/10 probe split - needs human decision before execution.

---

## The 7 Gaps

| #   | Gap                                | Severity | Problem                                                            |
| --- | ---------------------------------- | -------- | ------------------------------------------------------------------ |
| 1   | No standardized "full kit" handoff | **HIGH** | Deputies lack context to delegate effectively                      |
| 2   | Exceptions not surfaced            | MEDIUM   | USASOC/user/subagent overrides scattered, not in ORCHESTRATOR spec |
| 3   | No ORCHESTRATOR in agents.yaml     | LOW      | Roster missing top commander entry                                 |
| 4   | Standing orders dispersed          | MEDIUM   | Must open each identity card individually                          |
| 5   | MCP audit logs not visible         | LOW      | Only audit mechanisms documented, not log locations                |
| 6   | /force-multiplier lacks RAG health | MEDIUM   | Depends on RAG freshness with no validation                        |
| 7   | No formal offline SOP              | **HIGH** | Degraded operations rely on user discipline                        |

---

## Decision Required: Gap 3

**10 planning probes disagreed (5/5 split):**

### Option A: Add ORCHESTRATOR to agents.yaml
**Supporting probes:** SYNTHESIS, CRITICAL_PATH, RESOURCE_MIN, INCREMENTAL, PRECEDENT

| Pros                            | Cons                                            |
| ------------------------------- | ----------------------------------------------- |
| Registry completeness           | Implies ORCHESTRATOR can be spawned (it cannot) |
| Pattern consistency             | Creates governance paradox                      |
| Highest weighted score (4.25/5) | May confuse spawn_agent_tool                    |

### Option B: Identity card only (RECOMMENDED)
**Supporting probes:** ADVERSARIAL, RISK_MINIMAL, QUALITY_GATE, DOMAIN_EXPERT

| Pros                                        | Cons                     |
| ------------------------------------------- | ------------------------ |
| Preserves unique "supreme commander" status | Incomplete roster        |
| No spawn paradox                            | Special case to document |
| Explicit documentation of uniqueness        |                          |

### Option C: Add with `spawnable: false` flag
**Supporting probes:** (Proposed compromise)

| Pros                              | Cons                               |
| --------------------------------- | ---------------------------------- |
| Best of both options              | Requires agents.yaml schema change |
| Explicit, machine-readable status | More work                          |

**Recommendation:** Option B with explicit HIERARCHY.md documentation.

**Circle one:** `A` / `B` / `C`

---

## Execution Plan

### Phase 1: Foundation Sprint
**Scope:** Gaps 1, 3, 4
**Parallelism:** 3 streams (independent tasks)
**Deliverable:** Single PR

| Stream | Gap | Owner         | File                                          | Notes                    |
| ------ | --- | ------------- | --------------------------------------------- | ------------------------ |
| A      | 3   | COORD_TOOLING | `.claude/Identities/ORCHESTRATOR.identity.md` | Plus HIERARCHY.md update |
| B      | 4   | G2_RECON      | `.claude/Governance/STANDING_ORDERS_INDEX.md` | Generated via script     |
| C      | 1   | ARCHITECT     | `.claude/templates/HANDOFF_KIT_v1.md`         | Context kit template     |

**Script:** `scripts/generate-standing-orders-index.sh` (prevents drift)

### Phase 2: Consolidation
**Scope:** Gaps 2, 6
**Parallelism:** 2 streams (Gap 2 depends on Gap 4)
**Deliverable:** 2 PRs

| Gap | Owner              | File                                       | Dependency  |
| --- | ------------------ | ------------------------------------------ | ----------- |
| 2   | USASOC + COORD_OPS | `.claude/Governance/EXCEPTIONS.md`         | After Gap 4 |
| 6   | G6_SIGNAL          | `.claude/skills/force-multiplier/SKILL.md` | None        |

### Phase 3: Resilience
**Scope:** Gaps 5, 7
**Parallelism:** Sequential (lower priority)
**Deliverable:** 2 PRs

| Gap | Owner       | File                          | Notes                            |
| --- | ----------- | ----------------------------- | -------------------------------- |
| 7   | SYNTHESIZER | `.claude/SOPs/OFFLINE_SOP.md` | Hard blocks, not soft deferrals  |
| 5   | ARCHITECT   | `CLAUDE.md`                   | Document audit log location only |

---

## Files Summary

### To Create

| File                                          | Purpose                                |
| --------------------------------------------- | -------------------------------------- |
| `.claude/Identities/ORCHESTRATOR.identity.md` | Commander identity card                |
| `.claude/Governance/EXCEPTIONS.md`            | Consolidated override catalog          |
| `.claude/Governance/STANDING_ORDERS_INDEX.md` | Generated index of all standing orders |
| `.claude/templates/HANDOFF_KIT_v1.md`         | Standard Deputy context kit            |
| `.claude/SOPs/OFFLINE_SOP.md`                 | Degraded operations playbook           |
| `scripts/generate-standing-orders-index.sh`   | Automation to prevent index drift      |

### To Update

| File                                       | Change                                 |
| ------------------------------------------ | -------------------------------------- |
| `.claude/Governance/HIERARCHY.md`          | Add ORCHESTRATOR unique status section |
| `.claude/skills/force-multiplier/SKILL.md` | Add `rag_health` check before queries  |
| `CLAUDE.md`                                | Add MCP audit log location reference   |

---

## Key Insights from Planning Probes

### ADVERSARIAL (Red Team)
- Gap 3 paradox: Adding ORCHESTRATOR to agents.yaml implies it can be spawned
- Standing orders index must be **generated**, not manually maintained (prevents drift)
- Audit logs must NOT be committed to repo (OPSEC risk)

### SYNTHESIS (Balanced)
- Phase 1 can be fully parallel (3 independent tasks)
- Gap 2 depends on Gap 4 (exceptions need standing orders as reference)
- Defer Gap 5 to Phase 3 (documentation only, no log storage)

### QUALITY_GATE
- Each gap needs verification criteria before marking complete
- Standing orders index should be testable (run script, check output)
- RAG health check should have fallback behavior defined

---

## Verification Criteria

### Phase 1
```bash
# Files exist
ls -la .claude/Identities/ORCHESTRATOR.identity.md
ls -la .claude/Governance/STANDING_ORDERS_INDEX.md
ls -la .claude/templates/HANDOFF_KIT_v1.md

# Script works and output matches
./scripts/generate-standing-orders-index.sh > /tmp/generated.md
diff .claude/Governance/STANDING_ORDERS_INDEX.md /tmp/generated.md
```

### Phase 2
```bash
# Force-multiplier calls rag_health
grep "rag_health" .claude/skills/force-multiplier/SKILL.md

# Exceptions references standing orders
grep "STANDING_ORDERS" .claude/Governance/EXCEPTIONS.md
```

### Phase 3
```bash
# Offline SOP has hard blocks (CANNOT, not SHOULD NOT)
grep -c "CANNOT\|MUST NOT\|PROHIBITED" .claude/SOPs/OFFLINE_SOP.md
# Expected: >= 5
```

---

## Confidence Assessment

| Aspect                | Confidence | Notes                             |
| --------------------- | ---------- | --------------------------------- |
| Gap identification    | HIGH       | Directly from HUMAN_REPORT        |
| Phase 1 parallelism   | HIGH       | Tasks are independent             |
| Gap 2→4 dependency    | MEDIUM     | May be overstated                 |
| Effort estimates      | MEDIUM     | All documentation, no code        |
| Gap 5 deferral safety | HIGH       | Audit logs are external by design |

---

## Open Questions

1. **Gap 3:** Option A, B, or C?
2. **Standing orders script:** Shell script or Python?
3. **Handoff kit template:** How detailed? Include example content?
4. **Phase 3 priority:** Gap 7 (offline SOP) vs Gap 5 (audit docs) first?

---

## Approval

- [x] Gap 3 decision made: C
- [x] Phase 1 approved
- [x] Phase 2 approved
- [x] Phase 3 approved

**Reviewed by:** USER
**Date:** 2026-01-18

---

*Generated by PLAN_PARTY (10 probes). Ready for execution after Gap 3 decision.*
