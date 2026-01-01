# Agent Schema Archive - Pre-Mission Command Restructure

> **Archived:** 2025-12-31
> **Session:** 038/039
> **Purpose:** Preserve current structure before testing Mission Command model
> **Restore:** If new model fails, revert agent specs to this structure

---

## Current Model Tier Distribution

| Tier | Count | Agents |
|------|-------|--------|
| **Opus (10)** | 10 | ORCHESTRATOR, ARCHITECT, G5_PLANNING, AGENT_FACTORY, OPTIMIZATION_SPECIALIST, COORD_OPS, COORD_ENGINE, COORD_FRONTEND, COORD_PLATFORM, COORD_QUALITY, COORD_RESILIENCE |
| **Sonnet (26)** | 26 | G3_OPERATIONS, G4_CONTEXT_MANAGER, CAPACITY_OPTIMIZER, COORD_INTEL, UX_SPECIALIST, CRASH_RECOVERY_SPECIALIST, FORCE_MANAGER, COMPLIANCE_AUDITOR, DEVCOM_RESEARCH, CODE_REVIEWER, SECURITY_AUDITOR, SWAP_MANAGER, BURNOUT_SENTINEL, RESILIENCE_ENGINEER, COORD_AAR, SCHEDULER, WORKFLOW_EXECUTOR, TOOLSMITH, FRONTEND_ENGINEER, QA_TESTER, EPIDEMIC_ANALYST, API_DEVELOPER, RELEASE_MANAGER, BACKEND_ENGINEER |
| **Haiku (11)** | 11 | G1_PERSONNEL, G4_LIBRARIAN, DOMAIN_ANALYST, DBA, META_UPDATER, G2_RECON, G6_SIGNAL, DELEGATION_AUDITOR, SYNTHESIZER, MEDCOM, CI_LIAISON, AGENT_HEALTH_MONITOR |

---

## Current Hierarchy (from HIERARCHY.md)

```
ORCHESTRATOR (Supreme Commander)
├── G-Staff (Direct Reports)
│   ├── G1_PERSONNEL
│   ├── G2_RECON → SEARCH_PARTY
│   ├── G3_OPERATIONS / SYNTHESIZER
│   ├── G4_CONTEXT_MANAGER
│   ├── G5_PLANNING → PLAN_PARTY
│   ├── G6_SIGNAL
│   ├── IG (DELEGATION_AUDITOR)
│   └── PAO (HISTORIAN)
│
├── Coordinators (Manage Specialists)
│   ├── COORD_OPS
│   │   ├── TOOLSMITH
│   │   ├── META_UPDATER
│   │   └── RELEASE_MANAGER
│   ├── COORD_ENGINE
│   │   ├── SCHEDULER
│   │   └── SWAP_MANAGER
│   ├── COORD_PLATFORM
│   │   ├── ARCHITECT
│   │   ├── DBA
│   │   └── BACKEND_ENGINEER
│   ├── COORD_FRONTEND
│   │   ├── FRONTEND_ENGINEER
│   │   └── UX_SPECIALIST
│   ├── COORD_QUALITY
│   │   ├── QA_TESTER
│   │   └── CODE_REVIEWER
│   └── COORD_RESILIENCE
│       ├── RESILIENCE_ENGINEER
│       ├── COMPLIANCE_AUDITOR
│       └── SECURITY_AUDITOR
```

---

## Routing Table (Current)

| Specialist | Reports To | Bypass Allowed? |
|------------|------------|-----------------|
| TOOLSMITH | COORD_OPS | Single file only |
| META_UPDATER | COORD_OPS | Single file only |
| RELEASE_MANAGER | COORD_OPS | Never |
| SCHEDULER | COORD_ENGINE | Queries only |
| SWAP_MANAGER | COORD_ENGINE | Never |
| ARCHITECT | COORD_PLATFORM | Queries only |
| DBA | COORD_PLATFORM | Never |
| BACKEND_ENGINEER | COORD_PLATFORM | Single file only |
| FRONTEND_ENGINEER | COORD_FRONTEND | Single file only |
| QA_TESTER | COORD_QUALITY | Single test only |
| CODE_REVIEWER | COORD_QUALITY | Never |
| RESILIENCE_ENGINEER | COORD_RESILIENCE | Queries only |
| COMPLIANCE_AUDITOR | COORD_RESILIENCE | Never |
| SECURITY_AUDITOR | COORD_RESILIENCE | Never |

---

## Known Issues With Current Schema

1. **G-Staff model tier inconsistency** - Some G-Staff at haiku, some at opus
2. **ARCHITECT misplacement** - Strategic role reports to tactical coordinator
3. **SYNTHESIZER role confusion** - Is it G-3 or separate?
4. **Coordinators at Opus** - Overpowered for tactical role
5. **No clear Plan→See→Do flow** - Hierarchy is static, not process-oriented

---

## Rollback Instructions

If Mission Command structure fails:

1. Revert agent specs to original model tiers (see list above)
2. Restore HIERARCHY.md to current content
3. Remove any new sub-orchestrator roles
4. Return to flat ORCHESTRATOR → Coordinators → Specialists model

---

*Archived for safety before restructure experiment.*
