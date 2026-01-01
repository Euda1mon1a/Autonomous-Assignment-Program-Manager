***REMOVED*** PAI Agent Hierarchy

***REMOVED******REMOVED*** Toggle
Governance enforcement controlled by `config.json`. Set `governance_enabled: false` to disable.

***REMOVED******REMOVED*** Chain of Command

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

***REMOVED******REMOVED*** Routing Table

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

***REMOVED******REMOVED*** Bypass Rules

When `bypass_allowed_for_single_file: true`:
- ORCHESTRATOR may spawn specialist directly for trivial single-file tasks
- Must document bypass reason
- Coordinator still informed post-hoc

When `chain_of_command_enforcement: false`:
- All bypasses allowed
- No routing checks

***REMOVED******REMOVED*** Coordinator Responsibilities

***REMOVED******REMOVED******REMOVED*** COORD_OPS (Operations Coordinator)
- Manages tooling, documentation, and release processes
- Owns: TOOLSMITH, META_UPDATER, RELEASE_MANAGER
- Authority: Skill creation, documentation updates, release preparation

***REMOVED******REMOVED******REMOVED*** COORD_ENGINE (Scheduling Engine Coordinator)
- Manages core scheduling functionality
- Owns: SCHEDULER, SWAP_MANAGER
- Authority: Schedule generation, swap execution, constraint validation

***REMOVED******REMOVED******REMOVED*** COORD_PLATFORM (Platform Coordinator)
- Manages infrastructure and backend systems
- Owns: ARCHITECT, DBA, BACKEND_ENGINEER
- Authority: Architecture decisions, database operations, API development

***REMOVED******REMOVED******REMOVED*** COORD_FRONTEND (Frontend Coordinator)
- Manages UI and user experience
- Owns: FRONTEND_ENGINEER, UX_SPECIALIST
- Authority: Component development, UI/UX decisions

***REMOVED******REMOVED******REMOVED*** COORD_QUALITY (Quality Coordinator)
- Manages testing and code review
- Owns: QA_TESTER, CODE_REVIEWER
- Authority: Test strategy, code quality gates

***REMOVED******REMOVED******REMOVED*** COORD_RESILIENCE (Resilience Coordinator)
- Manages compliance, security, and system resilience
- Owns: RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR
- Authority: Compliance validation, security audits, resilience monitoring
