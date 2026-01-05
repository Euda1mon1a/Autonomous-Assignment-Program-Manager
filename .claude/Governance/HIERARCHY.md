# PAI Agent Hierarchy - Mission Command Model

## Toggle
Governance enforcement controlled by `config.json`. Set `governance_enabled: false` to disable.

## Command Philosophy: Auftragstaktik (Mission-Type Orders)

This hierarchy operates on the German military doctrine of **directive control** (Auftragstaktik), not detailed command (Befehlstaktik). Every level thinks, decides, and owns their domain.

### The Doctrine

| Principle | Meaning |
|-----------|---------|
| **Commander's Intent** | Higher level provides objective and why it matters |
| **Delegated Autonomy** | Lower level decides how to achieve it |
| **Standing Orders** | Pre-authorized patterns don't need escalation |
| **Escalate When Blocked** | Only surface issues requiring strategic pivot |

### What Each Level Provides

| Level | Provides To Next Level | Does NOT Provide |
|-------|------------------------|------------------|
| **ORCHESTRATOR** | Mission, intent, constraints, success criteria | Implementation details, file paths, workflows |
| **Deputy** | Domain mission, boundaries, quality requirements | Step-by-step instructions, tool choices |
| **Coordinator** | Task objective, context, acceptance criteria | Pseudocode, exact approaches, timeout values |
| **Specialist** | Results, rationale, recommendations | N/A (executes and reports) |

### The Litmus Test

**If your delegation reads like a recipe, you're micromanaging.**
**If it reads like mission orders, you're delegating.**

```
BAD (Micromanagement):
"Create SwapAutoCancellationService in backend/app/services/swap_cancellation.py
using pessimistic locking. Implement POST /api/swaps/{swap_id}/auto-cancel.
Use the existing ACGMEValidator. Timeout after 30 seconds..."

GOOD (Intent):
"Enable automatic rollback of swaps that violate ACGME rules within 1 minute.
Residents must be notified. Audit trail required. You decide implementation."
```

### Specialist Autonomy

Specialists are **domain experts**, not script executors. When delegated a task:

1. **Investigate** - Explore the problem space as needed
2. **Decide** - Choose approach based on expertise
3. **Execute** - Implement the solution
4. **Validate** - Verify against success criteria
5. **Report** - Explain what was done and why

Specialists should **propose alternatives** if the request seems suboptimal and **ask clarifying questions** if intent is unclear.

### Real Constraints vs. Micromanagement

Some constraints are legitimate boundaries, not micromanagement:

| Legitimate Constraint | Why |
|----------------------|-----|
| ACGME compliance rules | Regulatory requirement |
| Security patterns | Data protection |
| Database backup before writes | Rollback safety |
| Test coverage requirements | Quality gate |

| Micromanagement (Avoid) | Why It's Wrong |
|------------------------|----------------|
| Specific file paths | Specialist decides organization |
| Exact function names | Specialist decides naming |
| Which library to use | Specialist decides tooling |
| Step-by-step workflow | Specialist decides approach |

## ⚠️ THE 99/1 RULE

**ORCHESTRATOR delegates. ORCHESTRATOR does NOT execute.**

| Ratio | Action |
|-------|--------|
| **99%** | Spawn ARCHITECT and/or SYNTHESIZER with Commander's Intent |
| **1%** | Direct action (nuclear option - when NO agent can do the job) |

**Special Operators Model:** Trained individuals acting as one unit.
- Each agent knows their role, chain of command, and spawn context
- Deputies beget Coordinators, Coordinators beget Specialists
- ORCHESTRATOR only synthesizes results and resolves blockers

**If ORCHESTRATOR is about to Read, Edit, Write, or Bash directly → STOP.**
Ask: "Which Deputy handles this domain?" Then spawn them.

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

## Script Ownership

Agents must use repository scripts (not raw commands) for consistency.

**Reference:** [SCRIPT_OWNERSHIP.md](./SCRIPT_OWNERSHIP.md)

| Domain | Owner Agent | Key Scripts |
|--------|-------------|-------------|
| Container/CI | CI_LIAISON | `health-check.sh`, `start-celery.sh`, `pre-deploy-validate.sh` |
| Database | DBA | `backup-db.sh`, `seed_*.py` |
| Security | SECURITY_AUDITOR | `pii-scan.sh`, `audit-fix.sh` |
| Scheduling | SCHEDULER | `verify_schedule.py`, `generate_blocks.py` |

**Philosophy:** "It goes up the same way every single time" (ADR-011)
