# PAI Agent Hierarchy - Mission Command Model

## Toggle
Governance enforcement controlled by `config.json`. Set `governance_enabled: false` to disable.

## Command Philosophy: Mission Command

| Principle | Meaning |
|-----------|---------|
| **Commander's Intent** | ORCHESTRATOR gives objective, not step-by-step orders |
| **Delegated Autonomy** | Coordinators can spawn specialists without asking |
| **Standing Orders** | Pre-authorized patterns don't need escalation |
| **Escalate When Blocked** | Only surface issues that require strategic pivot |

## Chain of Command

```
ORCHESTRATOR (opus) ─── Supreme Commander
    │
    ├── ARCHITECT (opus) ─── Deputy for Systems
    │   ├── COORD_PLATFORM (sonnet) → DBA, BACKEND_ENGINEER, API_DEVELOPER
    │   ├── COORD_QUALITY (sonnet) → QA_TESTER, CODE_REVIEWER
    │   └── COORD_ENGINE (sonnet) → SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
    │
    └── SYNTHESIZER (opus) ─── Deputy for Operations
        ├── COORD_OPS (sonnet) → RELEASE_MANAGER, META_UPDATER, TOOLSMITH
        ├── COORD_RESILIENCE (sonnet) → RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR
        ├── COORD_FRONTEND (sonnet) → FRONTEND_ENGINEER, UX_SPECIALIST
        └── COORD_INTEL (sonnet) → (intel specialists)

    G-Staff (Advisory, sonnet) ─── Advisors to ORCHESTRATOR
        G-1 PERSONNEL, G-2 RECON, G-4 CONTEXT, G-5 PLANNING, G-6 SIGNAL

    Special Staff (Advisory, sonnet) ─── Domain Experts
        FORCE_MANAGER, DEVCOM_RESEARCH, MEDCOM

    IG (DELEGATION_AUDITOR) ─── Independent Oversight (sonnet)
    PAO (HISTORIAN) ─── Historical Record (sonnet)
```

## Model Tier Assignments

| Tier | Role | Agents |
|------|------|--------|
| **Opus** | Strategic decision-makers | ORCHESTRATOR, ARCHITECT, SYNTHESIZER |
| **Sonnet** | Tactical coordinators + advisors | All COORDs, G-Staff, IG, PAO, Special Staff |
| **Haiku** | Execution specialists | All specialists under coordinators |

## Coordinator Standing Orders

See individual Coordinator specs for pre-authorized actions.

## Escalation Triggers

| Escalate When | To Whom |
|---------------|---------|
| Tests failing, can't fix | COORD_QUALITY → ORCHESTRATOR |
| Security-sensitive changes | Any → SECURITY_AUDITOR |
| Architecture decision needed | Any → ARCHITECT |
| Cross-domain conflict | SYNTHESIZER → ORCHESTRATOR |
| Plan is fundamentally wrong | Any → ORCHESTRATOR |
