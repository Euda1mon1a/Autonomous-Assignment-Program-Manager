# Agent Hierarchy

> **Purpose:** Display the PAI agent organizational structure
> **Trigger:** `/hierarchy`
> **Updated:** 2026-01-03

---

## Command Structure

```
                              ORCHESTRATOR
                     (Strategic Commander - 99/1 Rule)
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
       ARCHITECT              SYNTHESIZER            G-STAFF
      (Technical)            (Integration)         (Army Doctrine)
            │                      │                      │
   ┌────────┴────────┐    ┌───────┴───────┐    ┌─────────┴─────────┐
   │                 │    │               │    │                   │
COORD_PLATFORM  COORD_QUALITY  COORD_OPS  COORD_FRONTEND   G1-G6 + IG/PAO
COORD_ENGINE    COORD_RESILIENCE          COORD_TOOLING
```

---

## Coordinators (COORDs)

| Coordinator | Domain | Specialists |
|-------------|--------|-------------|
| **COORD_PLATFORM** | Infrastructure | DBA, BACKEND_ENGINEER, API_DEVELOPER |
| **COORD_QUALITY** | Testing/QA | QA_TESTER, CODE_REVIEWER, CI_LIAISON |
| **COORD_ENGINE** | Scheduling | SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST |
| **COORD_OPS** | Operations | META_UPDATER, TOOLSMITH, RELEASE_MANAGER |
| **COORD_RESILIENCE** | Compliance | RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR |
| **COORD_FRONTEND** | UI/UX | FRONTEND_ENGINEER, UX_SPECIALIST |
| **COORD_TOOLING** | Tools/Skills | TOOLSMITH, TOOL_QA, TOOL_REVIEWER |
| **COORD_INTEL** | Investigation | Full-stack forensics |
| **COORD_AAR** | After Action | Session review (auto-trigger) |

---

## G-Staff (Army Doctrine)

| Position | Agent | Role |
|----------|-------|------|
| **G-1** | G1_PERSONNEL | Personnel & roster tracking |
| **G-2** | G2_RECON | Intelligence/Reconnaissance (`/search-party`) |
| **G-3** | G3_OPERATIONS | Operations & workflow coordination |
| **G-4** | G4_CONTEXT_MANAGER | RAG/vector context (+ G4_LIBRARIAN) |
| **G-5** | G5_PLANNING | Strategic planning (`/plan-party`) |
| **G-6** | G6_SIGNAL | Signal/Data Processing |
| **IG** | DELEGATION_AUDITOR | Inspector General (session end) |
| **PAO** | HISTORIAN | Public Affairs - significant sessions |

---

## Special Staff

| Agent | Role |
|-------|------|
| **FORCE_MANAGER** | Team assembly, coordinator assignment |
| **DEVCOM_RESEARCH** | R&D - exotic concepts, cross-disciplinary |
| **MEDCOM** | Medical Advisory - ACGME, clinical implications |
| **INCIDENT_COMMANDER** | Crisis response |
| **BURNOUT_SENTINEL** | Workload monitoring |

---

## Specialists (Sample)

| Domain | Agents |
|--------|--------|
| **Scheduling** | SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST, CAPACITY_OPTIMIZER |
| **Platform** | DBA, BACKEND_ENGINEER, API_DEVELOPER, ARCHITECT |
| **Quality** | QA_TESTER, CODE_REVIEWER, CI_LIAISON |
| **Resilience** | RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, BURNOUT_SENTINEL |
| **Knowledge** | KNOWLEDGE_CURATOR, G4_LIBRARIAN, META_UPDATER |
| **Frontend** | FRONTEND_ENGINEER, UX_SPECIALIST |

---

## The 99/1 Rule

**ORCHESTRATOR delegates 99%, executes 1%**

| ORCHESTRATOR Does | ORCHESTRATOR Delegates |
|-------------------|------------------------|
| Git commits/push | All code changes |
| PR creation | All implementation |
| Branch management | All testing |
| Final synthesis | All exploration |

---

## Routing Quick Reference

| Task Type | Route |
|-----------|-------|
| Database/API | ARCHITECT → COORD_PLATFORM |
| Tests/CI | ARCHITECT → COORD_QUALITY |
| Scheduling | ARCHITECT → COORD_ENGINE |
| Docs/Releases | SYNTHESIZER → COORD_OPS |
| Resilience | SYNTHESIZER → COORD_RESILIENCE |
| Frontend | SYNTHESIZER → COORD_FRONTEND |
| Recon | G2_RECON (`/search-party`) |
| Planning | G5_PLANNING (`/plan-party`) |

---

## IDE Safety

**Max 2 direct spawns from ORCHESTRATOR** - route through coordinators to prevent IDE crash.

---

*Run `/hierarchy` anytime for this reference.*
