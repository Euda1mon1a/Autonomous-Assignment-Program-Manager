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
    │   ├── COORD_ENGINE (sonnet) → SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
    │   └── COORD_TOOLING (sonnet) → TOOLSMITH, TOOL_QA, TOOL_REVIEWER
    │
    └── SYNTHESIZER (opus) ─── Deputy for Operations
        ├── COORD_OPS (sonnet) → RELEASE_MANAGER, META_UPDATER, KNOWLEDGE_CURATOR, CI_LIAISON
        ├── COORD_RESILIENCE (sonnet) → RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR
        ├── COORD_FRONTEND (sonnet) → FRONTEND_ENGINEER, UX_SPECIALIST
        └── COORD_INTEL (sonnet) → (intel specialists)

    G-Staff (Advisory, sonnet) ─── Advisors to ORCHESTRATOR
        G-1 PERSONNEL, G-2 RECON, G-3 OPERATIONS, G-4 CONTEXT, G-5 PLANNING, G-6 SIGNAL

    Special Staff (Advisory, sonnet) ─── Domain Experts
        FORCE_MANAGER, DEVCOM_RESEARCH, MEDCOM

    IG (DELEGATION_AUDITOR) ─── Independent Oversight (sonnet)
    PAO (HISTORIAN) ─── Historical Record (sonnet)
```

## Model Tier Assignments

| Tier | Role | Agents |
|------|------|--------|
| **Opus** | Strategic decision-makers | ORCHESTRATOR, ARCHITECT, SYNTHESIZER |
| **Opus** | High-stakes Special Staff | DEVCOM_RESEARCH, MEDCOM, INCIDENT_COMMANDER |
| **Sonnet** | Tactical coordinators + advisors | All COORDs, G-Staff, IG, PAO, FORCE_MANAGER |
| **Haiku** | Execution specialists | All specialists under coordinators, CRASH_RECOVERY_SPECIALIST |

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

## G-Staff Notes

### G-4 Split Architecture
G-4 (Logistics/Context) operates as two complementary agents:
- **G4_CONTEXT_MANAGER**: Semantic memory via pgvector embeddings, RAG
- **G4_LIBRARIAN**: Structural memory via file references

G4_LIBRARIAN reports to G4_CONTEXT_MANAGER, not directly to ORCHESTRATOR.

### Key Distinction: G-3 vs SYNTHESIZER
- **G3_OPERATIONS** = Advisory on operational status (sonnet, G-Staff)
- **SYNTHESIZER** = Deputy commanding operational coordinators (opus, Command)

These are separate roles. G-3 advises; SYNTHESIZER commands.

## G-Staff Intel Routing

G-Staff agents are advisory. Their intel SHOULD route through Deputies for strategic interpretation, but CAN go direct to ORCHESTRATOR for urgent matters.

| G-Staff | Primary Route | Strategic Interpretation |
|---------|---------------|-------------------------|
| G-1 PERSONNEL | → ORCHESTRATOR | Via FORCE_MANAGER (team assembly) |
| G-2 RECON | → ORCHESTRATOR | Via ARCHITECT (systems) or SYNTHESIZER (ops) |
| G-3 OPERATIONS | → ORCHESTRATOR | Via SYNTHESIZER (operational conflicts) |
| G-4 CONTEXT | → ORCHESTRATOR | Direct (context management) |
| G-5 PLANNING | → ORCHESTRATOR | Via ARCHITECT (strategic planning) |
| G-6 SIGNAL | → ORCHESTRATOR | Via SYNTHESIZER (data/metrics) |

**Routing Guidance:**
- **Urgent/Time-Critical**: Direct to ORCHESTRATOR
- **Strategic/Interpretive**: Route through appropriate Deputy
- **Cross-Domain**: Both Deputies may be consulted
