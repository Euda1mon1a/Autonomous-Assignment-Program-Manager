# Spawn Chain Enforcement

> **Status:** HARD ENFORCEMENT
> **Effective:** 2026-01-06

## Philosophy

Agents can only be spawned by their documented parents. This maintains:
- Clear accountability
- Proper context passing
- Predictable escalation paths

## Spawn Authority Matrix

### Deputies (Can spawn Coordinators + G-Staff)

| Deputy | Can Spawn |
|--------|-----------|
| ARCHITECT | COORD_PLATFORM, COORD_QUALITY, COORD_ENGINE, COORD_TOOLING, G6_SIGNAL, G2_RECON*, G5_PLANNING*, DEVCOM_RESEARCH |
| SYNTHESIZER | COORD_OPS, COORD_RESILIENCE, COORD_FRONTEND, COORD_INTEL, COORD_AAR, G1_PERSONNEL, G3_OPERATIONS, G4_CONTEXT_MANAGER, G2_RECON*, G5_PLANNING*, FORCE_MANAGER, MEDCOM, CRASH_RECOVERY, INCIDENT_COMMANDER |
| USASOC | 18A through 18Z, ANY agent (wide lateral authority) |

*G2 and G5 are General Support - attachable to either Deputy

### Coordinators (Can spawn Specialists)

| Coordinator | Can Spawn |
|-------------|-----------|
| COORD_PLATFORM | DBA, BACKEND_ENGINEER, API_DEVELOPER |
| COORD_QUALITY | QA_TESTER, CODE_REVIEWER |
| COORD_ENGINE | SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST |
| COORD_TOOLING | TOOLSMITH, TOOL_QA, TOOL_REVIEWER, AGENT_FACTORY |
| COORD_OPS | RELEASE_MANAGER, META_UPDATER, CI_LIAISON, HISTORIAN |
| COORD_RESILIENCE | RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR |
| COORD_FRONTEND | FRONTEND_ENGINEER, UX_SPECIALIST |
| COORD_INTEL | (intel specialists) |
| COORD_AAR | (uses IG, HISTORIAN for AAR process) |

### G-Staff (Can spawn their parties)

| G-Staff | Party | Spawns |
|---------|-------|--------|
| G1_PERSONNEL | /roster-party | 6 probes |
| G2_RECON | /search-party | 120 probes |
| G3_OPERATIONS | /ops-party | 6 probes |
| G4_CONTEXT_MANAGER | /context-party | 6 probes |
| G5_PLANNING | /plan-party | 10 probes |
| G6_SIGNAL | /signal-party | 6 probes |

### SOF Operators (Can task across domains)

18A_DETACHMENT_COMMANDER can task any Coordinator or Specialist when USASOC is active.

## Violations

If an agent attempts to spawn outside their authority:
1. Log the violation
2. Route request to proper parent
3. Report in session-end IG audit

## Exceptions

- USASOC has wide lateral authority (by design)
- User can invoke any agent directly
- Emergency situations documented with justification
