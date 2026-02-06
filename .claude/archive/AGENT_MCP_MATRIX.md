# Agent MCP Dependency Matrix

> **Quick Reference:** Which agents need MCP tools?
> **Status:** Complete snapshot of all 56 specialist agents + 5 G-Staff
> **Purpose:** Quick lookup for agent deployment and tool planning

---

## Summary Table: All 61 Agents

| Agent | MCP Needed | Tool Groups | Priority | Criticality |
|-------|-----------|-------------|----------|------------|
| **SCHEDULER** | YES | Scheduling (5), Tasks (1) | P0 | CRITICAL |
| **SWAP_MANAGER** | YES | Scheduling (4), Tasks (1) | P0 | CRITICAL |
| **COORD_ENGINE** | YES | Scheduling (5), Resilience (1), Tasks (1) | P0 | CRITICAL |
| **COMPLIANCE_AUDITOR** | YES | Scheduling (2), Resilience support (3) | P0 | REGULATORY |
| **SECURITY_AUDITOR** | YES | Scheduling (2), API audit (1) | P0 | REGULATORY |
| **RESILIENCE_ENGINEER** | YES | Resilience core (6), Scheduling (1), Tasks (1) | P1 | CRITICAL |
| **BURNOUT_SENTINEL** | YES | Resilience advanced (8) | P1 | CRITICAL |
| **EPIDEMIC_ANALYST** | YES | Resilience advanced (5) | P1 | CRITICAL |
| **CAPACITY_OPTIMIZER** | YES | Resilience advanced (4) | P2 | DECISION-SUPPORT |
| **OPTIMIZATION_SPECIALIST** | YES | Scheduling (2), Resilience (1), Tasks (1) | P2 | DECISION-SUPPORT |
| **G5_PLANNING** | YES | Scheduling (1), Resilience (3) | P1 | DECISION-SUPPORT |
| **G3_OPERATIONS** | YES | Scheduling (2), Resilience (1), Tasks (1) | P1 | OPERATIONS |
| **KNOWLEDGE_CURATOR** | YES | RAG (3) | P2 | INFRASTRUCTURE |
| **COORD_INTEL** | YES | API forensics (1) | P2 | INVESTIGATION |
| **CI_LIAISON** | YES | Background tasks (4) | P1 | DEPLOYMENT |
| **TOOL_QA** | YES | RAG (2) | P3 | QUALITY |
| **TOOL_REVIEWER** | YES | RAG (2) | P3 | QUALITY |
| **AGENT_FACTORY** | YES | RAG (3) | P3 | INFRASTRUCTURE |
| **COORD_TOOLING** | YES | RAG (3) | P3 | INFRASTRUCTURE |
| **API_DEVELOPER** | MAYBE | API tools (optional) | P2 | OPTIONAL |
| | | | | |
| **ARCHITECT** | NO | - | - | CODE |
| **BACKEND_ENGINEER** | NO | - | - | CODE |
| **FRONTEND_ENGINEER** | NO | - | - | CODE |
| **DBA** | NO | - | - | CODE |
| **API_DEVELOPER** | NO | - (code) | - | CODE |
| **CODE_REVIEWER** | NO | - | - | CODE |
| **QA_TESTER** | NO | - | - | CODE |
| **DEVCOM_RESEARCH** | NO | - | - | CODE |
| **DOMAIN_ANALYST** | NO | - | - | CODE |
| **UX_SPECIALIST** | NO | - | - | CODE |
| **CRASH_RECOVERY_SPECIALIST** | NO | - | - | OPS |
| **INCIDENT_COMMANDER** | NO | - | - | OPS |
| **RELEASE_MANAGER** | NO | - | - | OPS |
| **META_UPDATER** | NO | - | - | OPS |
| **TOOLSMITH** | NO | - | - | OPS |
| **TRAINING_OFFICER** | NO | - | - | OPS |
| **MEDCOM** | NO | - | - | OPS |
| **FORCE_MANAGER** | NO | - | - | OPS |
| **WORKFLOW_EXECUTOR** | NO | - | - | OPS |
| **DELEGATION_AUDITOR** | NO | - | - | OVERSIGHT |
| **HISTORIAN** | NO | - | - | OVERSIGHT |
| **PATTERN_ANALYST** | NO | - | - | OVERSIGHT |
| **COORD_AAR** | NO | - | - | OVERSIGHT |
| **COORD_QUALITY** | NO | - | - | OVERSIGHT |
| **COORD_PLATFORM** | NO | - | - | OVERSIGHT |
| **COORD_FRONTEND** | NO | - | - | OVERSIGHT |
| **AGENT_HEALTH_MONITOR** | NO | - | - | OPS |
| **CHAOS_ENGINEER** | NO | - | - | OPS |
| **SYNTHESIZER** | NO | (delegates only) | - | COMMAND |
| **ORCHESTRATOR** | NO | (delegates only) | - | COMMAND |
| **G1_PERSONNEL** | NO | - | - | G-STAFF |
| **G2_RECON** | NO | - | - | G-STAFF |
| **G4_CONTEXT_MANAGER** | NO | - | - | G-STAFF |
| **G4_LIBRARIAN** | NO | - | - | G-STAFF |
| **G6_SIGNAL** | NO | - | - | G-STAFF |

---

## MCP-Required Agents: Detailed Listing

### P0: Mission-Critical Scheduling (4 agents)

```
SCHEDULER
  ├─ Scheduling Core Tools (5): validate_schedule, generate_schedule,
  │  detect_conflicts, analyze_swap_candidates, execute_swap
  ├─ Background Tasks (1): start_background_task (optional)
  ├─ Criticality: MISSION-CRITICAL
  └─ Cannot function without: validate_schedule, generate_schedule

SWAP_MANAGER
  ├─ Scheduling Core Tools (4): analyze_swap_candidates, validate_schedule,
  │  execute_swap, detect_conflicts
  ├─ Background Tasks (1): start_background_task (optional)
  ├─ Criticality: MISSION-CRITICAL
  └─ Cannot function without: analyze_swap_candidates, execute_swap

COORD_ENGINE
  ├─ Scheduling Core Tools (5): validate_schedule, generate_schedule,
  │  detect_conflicts, analyze_swap_candidates, execute_swap
  ├─ Resilience Core (1): run_contingency_analysis
  ├─ Background Tasks (1): start_background_task (optional)
  ├─ Criticality: MISSION-CRITICAL
  └─ Cannot function without: validate_schedule (quality gate enforcement)

OPTIMIZATION_SPECIALIST
  ├─ Scheduling Core Tools (2): generate_schedule, validate_schedule
  ├─ Resilience Advanced (1): analyze_hub_centrality
  ├─ Background Tasks (1): start_background_task (optional)
  ├─ Criticality: MISSION-CRITICAL (for optimization)
  └─ Cannot function without: generate_schedule, validate_schedule
```

### P0: Regulatory Compliance (1 agent)

```
COMPLIANCE_AUDITOR
  ├─ Scheduling Core Tools (2): validate_schedule, detect_conflicts
  ├─ Additional Tools (4): get_work_hours, check_supervision_ratio,
  │  list_violations, generate_compliance_report
  ├─ Criticality: REGULATORY-CRITICAL
  └─ Cannot function without: validate_schedule
```

### P0: Security & Audit (1 agent)

```
SECURITY_AUDITOR
  ├─ Scheduling Core Tools (2): validate_schedule, detect_conflicts
  ├─ Direct API (1): GET /api/audit/logs
  ├─ Criticality: REGULATORY-CRITICAL
  └─ Cannot function without: validate_schedule (for audit trail)
```

### P1: Resilience & Health Monitoring (4 agents)

```
RESILIENCE_ENGINEER
  ├─ Resilience Core Tools (6): check_utilization_threshold,
  │  run_contingency_analysis, get_defense_level, analyze_hub_centrality,
  │  get_static_fallbacks, execute_sacrifice_hierarchy
  ├─ Scheduling Support (1): validate_schedule
  ├─ Background Tasks (1): start_background_task
  ├─ Criticality: CRITICAL
  └─ Cannot function without: run_contingency_analysis

BURNOUT_SENTINEL
  ├─ Resilience Advanced Tools (8): check_utilization_threshold,
  │  assess_cognitive_load, calculate_process_capability,
  │  calculate_burnout_rt, simulate_burnout_spread, get_behavioral_patterns,
  │  check_spc_violations, detect_early_warning_signals
  ├─ Criticality: CRITICAL
  └─ Cannot function without: calculate_burnout_rt

EPIDEMIC_ANALYST
  ├─ Resilience Advanced Tools (5): calculate_burnout_rt,
  │  simulate_burnout_spread, simulate_burnout_contagion,
  │  analyze_hub_centrality, get_behavioral_patterns
  ├─ Criticality: CRITICAL
  └─ Cannot function without: calculate_burnout_rt

G3_OPERATIONS
  ├─ Scheduling Core Tools (2): detect_conflicts, generate_schedule
  ├─ Resilience Core (1): run_contingency_analysis
  ├─ Background Tasks (1): get_task_status
  ├─ Criticality: OPERATIONAL
  └─ Cannot function without: detect_conflicts (real-time monitoring)
```

### P1: Strategic Planning (1 agent)

```
G5_PLANNING
  ├─ Scheduling Support (1): validate_schedule
  ├─ Resilience Core (3): check_utilization_threshold,
  │  analyze_homeostasis, get_static_fallbacks
  ├─ Criticality: DECISION-SUPPORT
  └─ Cannot function without: validate_schedule (feasibility checking)
```

### P1: Deployment & Operations (1 agent)

```
CI_LIAISON
  ├─ Background Task Tools (4): start_background_task, get_task_status,
  │  cancel_task, list_active_tasks
  ├─ Criticality: DEPLOYMENT-CRITICAL
  └─ Cannot function without: start_background_task (job management)
```

### P2: Advanced Analysis & Optimization (1 agent)

```
CAPACITY_OPTIMIZER
  ├─ Resilience Advanced Tools (4): check_utilization_threshold,
  │  calculate_process_capability, calculate_equity_metrics,
  │  analyze_erlang_coverage
  ├─ Criticality: OPTIMIZATION
  └─ Cannot function without: calculate_process_capability
```

### P2: Investigation Support (1 agent)

```
COORD_INTEL
  ├─ Direct Forensics APIs (1): GET /api/forensics/logs,
  │  GET /api/forensics/database-state, GET /api/audit/timeline
  ├─ Criticality: INVESTIGATION
  └─ Cannot function without: Forensic query APIs
```

### P3: Knowledge Management (5 agents)

```
KNOWLEDGE_CURATOR
  ├─ RAG Tools (3): rag_search, rag_ingest, rag_context
  ├─ Criticality: INFRASTRUCTURE
  └─ Cannot function without: rag_search, rag_ingest

TOOL_QA
  ├─ RAG Tools (2): rag_search, rag_health
  ├─ Criticality: QUALITY
  └─ Cannot function without: rag_search

TOOL_REVIEWER
  ├─ RAG Tools (2): rag_search, rag_health
  ├─ Criticality: QUALITY
  └─ Cannot function without: rag_search

AGENT_FACTORY
  ├─ RAG Tools (3): rag_search, rag_context, rag_ingest
  ├─ Criticality: INFRASTRUCTURE
  └─ Cannot function without: rag_search (agent pattern discovery)

COORD_TOOLING
  ├─ RAG Tools (3): rag_search, rag_ingest, rag_health
  ├─ Criticality: INFRASTRUCTURE
  └─ Cannot function without: rag_search
```

---

## MCP-Independent Agents (36 agents)

All of these operate with **NO MCP dependency** - they use local files, git, and test execution:

### Core Development (11)
ARCHITECT, BACKEND_ENGINEER, FRONTEND_ENGINEER, API_DEVELOPER, DBA, CODE_REVIEWER, QA_TESTER, DEVCOM_RESEARCH, DOMAIN_ANALYST, UX_SPECIALIST, SYNTHESIZER

### Operations & Infrastructure (9)
CRASH_RECOVERY_SPECIALIST, INCIDENT_COMMANDER, RELEASE_MANAGER, META_UPDATER, TOOLSMITH, TRAINING_OFFICER, MEDCOM, FORCE_MANAGER, WORKFLOW_EXECUTOR

### Oversight & Governance (6)
DELEGATION_AUDITOR, HISTORIAN, PATTERN_ANALYST, COORD_AAR, COORD_QUALITY, COORD_PLATFORM

### G-Staff Advisory (5)
G1_PERSONNEL, G2_RECON, G4_CONTEXT_MANAGER, G4_LIBRARIAN, G6_SIGNAL

### Infrastructure & Monitoring (3)
AGENT_HEALTH_MONITOR, CHAOS_ENGINEER, COORD_FRONTEND

### Command (1)
ORCHESTRATOR (delegates only - doesn't execute)

---

## Tool Group Summary

### Scheduling Core (5 tools, 10 agents)
```
validate_schedule         → SCHEDULER, SWAP_MANAGER, COORD_ENGINE,
                            OPTIMIZATION_SPECIALIST, G5_PLANNING,
                            SECURITY_AUDITOR, COMPLIANCE_AUDITOR

detect_conflicts          → SWAP_MANAGER, COORD_ENGINE,
                            SECURITY_AUDITOR, COMPLIANCE_AUDITOR,
                            G3_OPERATIONS

generate_schedule         → SCHEDULER, COORD_ENGINE,
                            OPTIMIZATION_SPECIALIST, G3_OPERATIONS

analyze_swap_candidates   → SWAP_MANAGER, COORD_ENGINE

execute_swap             → SCHEDULER, SWAP_MANAGER, COORD_ENGINE
```

### Resilience Core (6 tools, 4 agents)
```
check_utilization_threshold    → RESILIENCE_ENGINEER, BURNOUT_SENTINEL,
                                 CAPACITY_OPTIMIZER, G5_PLANNING

run_contingency_analysis       → RESILIENCE_ENGINEER, COORD_ENGINE,
                                 G3_OPERATIONS

get_defense_level             → RESILIENCE_ENGINEER

analyze_hub_centrality        → RESILIENCE_ENGINEER,
                                 OPTIMIZATION_SPECIALIST,
                                 EPIDEMIC_ANALYST

get_static_fallbacks          → RESILIENCE_ENGINEER, G5_PLANNING

execute_sacrifice_hierarchy   → RESILIENCE_ENGINEER
```

### Resilience Advanced (8+ tools, 4 agents)
```
calculate_burnout_rt          → BURNOUT_SENTINEL, EPIDEMIC_ANALYST

simulate_burnout_spread       → BURNOUT_SENTINEL, EPIDEMIC_ANALYST

simulate_burnout_contagion    → EPIDEMIC_ANALYST

assess_cognitive_load         → BURNOUT_SENTINEL

calculate_process_capability  → BURNOUT_SENTINEL, CAPACITY_OPTIMIZER

get_behavioral_patterns       → BURNOUT_SENTINEL, EPIDEMIC_ANALYST

check_spc_violations          → BURNOUT_SENTINEL

analyze_homeostasis           → G5_PLANNING

calculate_blast_radius        → RESILIENCE_ENGINEER

analyze_le_chatelier          → RESILIENCE_ENGINEER

calculate_equity_metrics      → CAPACITY_OPTIMIZER

analyze_erlang_coverage       → CAPACITY_OPTIMIZER

detect_early_warning_signals  → BURNOUT_SENTINEL
```

### RAG Tools (4 tools, 5 agents)
```
rag_search                    → KNOWLEDGE_CURATOR, TOOL_QA,
                                 TOOL_REVIEWER, AGENT_FACTORY,
                                 COORD_TOOLING

rag_ingest                    → KNOWLEDGE_CURATOR, AGENT_FACTORY,
                                 COORD_TOOLING

rag_context                   → KNOWLEDGE_CURATOR, AGENT_FACTORY

rag_health                    → TOOL_QA, TOOL_REVIEWER, COORD_TOOLING
```

### Background Tasks (4 tools, 3 agents)
```
start_background_task         → CI_LIAISON, SCHEDULER (optional),
                                 COORD_ENGINE (optional)

get_task_status               → CI_LIAISON, G3_OPERATIONS

cancel_task                   → CI_LIAISON

list_active_tasks             → CI_LIAISON
```

### Additional Specialized (6 tools, 3 agents)
```
get_work_hours                → COMPLIANCE_AUDITOR

check_supervision_ratio       → COMPLIANCE_AUDITOR

list_violations               → COMPLIANCE_AUDITOR, SECURITY_AUDITOR

generate_compliance_report    → COMPLIANCE_AUDITOR

Forensic APIs                 → COORD_INTEL

Audit log APIs                → SECURITY_AUDITOR
```

---

## Dependency Graph

### Core Scheduling Path (P0)
```
ORCHESTRATOR
    └─> ARCHITECT
        └─> COORD_ENGINE (requires validate_schedule, generate_schedule)
            ├─> SCHEDULER (requires validate_schedule, generate_schedule)
            ├─> SWAP_MANAGER (requires analyze_swap_candidates, execute_swap)
            └─> OPTIMIZATION_SPECIALIST (requires generate_schedule, validate_schedule)
```

### Compliance Path (P0)
```
ORCHESTRATOR
    └─> SYNTHESIZER
        └─> COORD_RESILIENCE
            └─> COMPLIANCE_AUDITOR (requires validate_schedule)
            └─> SECURITY_AUDITOR (requires validate_schedule)
```

### Resilience Path (P1)
```
ORCHESTRATOR
    └─> SYNTHESIZER
        └─> COORD_RESILIENCE
            ├─> RESILIENCE_ENGINEER (requires run_contingency_analysis)
            ├─> BURNOUT_SENTINEL (requires calculate_burnout_rt)
            └─> EPIDEMIC_ANALYST (requires calculate_burnout_rt)
```

### Strategic Planning Path (P1)
```
ORCHESTRATOR
    └─> G5_PLANNING (requires validate_schedule, analyze_homeostasis)
    └─> G3_OPERATIONS (requires detect_conflicts, get_task_status)
```

---

## Deployment Checklist

### Before Enabling Any MCP Agent

- [ ] Docker services all running: `docker compose ps`
- [ ] MCP server healthy: `docker compose exec mcp-server python -c "from scheduler_mcp.server import mcp; print('OK')"`
- [ ] Backend API responding: `curl http://localhost:8000/health`
- [ ] Database connected: `docker compose exec db psql -U scheduler -d residency_scheduler -c "SELECT 1"`
- [ ] Redis running: `docker compose exec redis redis-cli ping`

### Phase 1: Enable P0 Scheduling Agents
1. SCHEDULER
2. SWAP_MANAGER
3. COORD_ENGINE
4. OPTIMIZATION_SPECIALIST

### Phase 2: Enable P0 Compliance Agents
5. COMPLIANCE_AUDITOR
6. SECURITY_AUDITOR

### Phase 3: Enable P1 Resilience Agents
7. RESILIENCE_ENGINEER
8. BURNOUT_SENTINEL
9. EPIDEMIC_ANALYST
10. G3_OPERATIONS
11. G5_PLANNING

### Phase 4: Enable P2+ Support Agents
12. CAPACITY_OPTIMIZER
13. CI_LIAISON
14. COORD_INTEL
15. KNOWLEDGE_CURATOR
16. TOOL_QA
17. TOOL_REVIEWER
18. AGENT_FACTORY
19. COORD_TOOLING

---

## Quick Reference: "Does Agent X Need MCP?"

**Quick answer table:**

| Does it... | Then MCP |
|-----------|---------|
| Generate/validate schedules? | YES |
| Execute/analyze swaps? | YES |
| Run resilience tests (N-1/N-2)? | YES |
| Monitor burnout/workload? | YES |
| Call APIs directly? | MAYBE (check list above) |
| Audit compliance? | YES |
| Search knowledge base? | YES |
| Manage background jobs? | YES |
| Write/edit code? | NO |
| Run local tests? | NO |
| Review pull requests? | NO |
| Update documentation? | NO (unless RAG) |
| Coordinate agents? | NO |
| Read git history? | NO |

---

## Key Stats

- **Total Agents:** 61 (56 specialists + 5 G-Staff)
- **MCP-Dependent:** 20 agents (33%)
- **MCP-Independent:** 41 agents (67%)
- **MCP Tools Required:** 29+ tools
- **Critical Agents:** 10 (P0, cannot skip)
- **Optional Agents:** 5 (P3, infrastructure only)

---

**END OF AGENT MCP MATRIX**

*Use this as your quick reference for agent deployment and tool planning.*
