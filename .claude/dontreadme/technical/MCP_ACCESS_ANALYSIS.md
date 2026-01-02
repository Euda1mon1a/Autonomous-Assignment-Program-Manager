# G5 Planning Probe: MCP Access Analysis for Special Staff

**Analysis Date:** 2026-01-01
**MCP Server Version:** 29 Jan 2026 Build (85 tools available)
**Batch:** Special Staff (FORCE_MANAGER, DEVCOM_RESEARCH, MEDCOM, DELEGATION_AUDITOR, HISTORIAN)

---

## Executive Summary

Five special staff agents require MCP tool access for their advisory/management roles:

| Agent | Tools | Priority | Access Type |
|-------|-------|----------|------------|
| **FORCE_MANAGER** | 4 (Task Management) | HIGH | Execution + Monitoring |
| **DEVCOM_RESEARCH** | 8 (RAG + Benchmarking) | HIGH | Research Sandbox |
| **MEDCOM** | 8 (RAG + Analytics) | MEDIUM | Read-Only Advisory |
| **DELEGATION_AUDITOR** | 5 (Monitoring + Analysis) | MEDIUM | Read-Only Observer |
| **HISTORIAN** | 3 (RAG + Knowledge) | LOW | Archive + Context |

---

## Detailed Analysis

### FORCE_MANAGER
**Role:** Task Force Assembly & Lifecycle Management (Special Staff)

**MCP Tools Needed:**
- `start_background_task` - Activate assembled task forces
- `get_task_status` - Monitor task force execution progress
- `cancel_task` - Deactivate/cancel task forces if needed
- `list_active_tasks` - Track active task forces system-wide

**Rationale:**
FORCE_MANAGER assembles agents into task forces and manages their lifecycle (PENDING → ACTIVATED → OPERATING → COMPLETED → DEACTIVATED). Task management tools provide visibility and control without direct execution authority.

**Priority:** HIGH

**Workflow Integration:**
1. Receives mission objective from ORCHESTRATOR
2. Assembles optimal agent mix from G1_PERSONNEL availability
3. Uses `start_background_task` to activate task force under coordinator
4. Monitors via `get_task_status` through execution phases
5. Uses `cancel_task` if task force becomes blocked/redundant
6. Reports completion status back to ORCHESTRATOR

**Access Model:** Execution (can start/cancel tasks) + Monitoring (can query status)

---

### DEVCOM_RESEARCH
**Role:** Advanced R&D & Cross-Disciplinary Concept Exploration (Special Staff)

**MCP Tools Needed:**

**RAG/Knowledge Base (4 tools):**
- `rag_search` - Search knowledge base for applicable research papers, algorithms, concepts
- `rag_ingest` - Archive research findings and implementation guides
- `rag_context` - Retrieve context on exotic frontier concepts (Tier 5 modules)
- `rag_health` - Verify RAG system operational status

**Benchmarking & Assessment (4 tools):**
- `benchmark_resilience` - Test research prototypes against resilience metrics
- `ablation_study` - Determine impact of individual exotic concepts
- `module_usage_analysis` - Analyze scheduling impact of proposed concepts
- `run_frms_assessment` - Assess feasibility of research proposals

**Rationale:**
DEVCOM conducts exploratory research on cross-disciplinary concepts (physics, biology, mathematics, etc.) for scheduling applications. RAG tools support literature research and knowledge capture. Benchmarking tools validate prototypes before handoff to production teams. Notably, DEVCOM does NOT get execution tools (deployment, production) - research is sandboxed, not production.

**Priority:** HIGH

**Workflow Integration:**
1. Receives research directive from ORCHESTRATOR or G-6 handoff
2. Uses `rag_search` to survey applicable literature
3. Uses `rag_context` to understand existing exotic modules
4. Develops proof-of-concept prototype
5. Uses `benchmark_resilience` to validate against resilience metrics
6. Uses `ablation_study` to measure individual concept contributions
7. Uses `rag_ingest` to archive research findings + implementation guide
8. Submits handoff to ORCHESTRATOR for production routing

**Access Model:** Research Sandbox (RAG + Analysis, NO production execution)

---

### MEDCOM
**Role:** Medical Advisory Services (Advisory-Only, Translation Role)

**MCP Tools Needed:**

**RAG/Knowledge Base (2 tools - READ-ONLY):**
- `rag_search` - Search medical/clinical knowledge base for ACGME rationale, medical literature
- `rag_context` - Retrieve ACGME rule interpretations and clinical context

**Burnout/Fatigue Analysis (6 tools - READ-ONLY):**
- `get_unified_critical_index` - Translate system health metrics to clinical meaning
- `calculate_burnout_rt` - Compute burnout reproduction number for physician interpretation
- `detect_burnout_precursors` - Flag early warning signs for physician awareness
- `get_fatigue_score` - Retrieve fatigue metrics for clinical interpretation
- `scan_team_fatigue` - Identify team-level fatigue patterns
- `analyze_sleep_debt` - Provide sleep debt context for physician decision-making

**Rationale:**
MEDCOM translates technical scheduling metrics into clinical language for physician decision-making. This agent is **ADVISORY-ONLY** - it surfaces information, never makes medical decisions or directs actions. All tools are READ-ONLY (data retrieval and analysis), never execution/modification. MEDCOM explicitly defers all decisions to the physician.

**Key Constraint:** MEDCOM has NO execution authority. Even with "GRANT" recommendation, these are strictly informational/analytical tools.

**Priority:** MEDIUM

**Workflow Integration:**
1. Receives advisory request from ORCHESTRATOR (e.g., "translate resilience metrics")
2. Uses `rag_search` to get clinical context for metrics
3. Uses `calculate_burnout_rt` to compute metric value
4. Uses `analyze_sleep_debt` or `scan_team_fatigue` to gather clinical context
5. Provides translation to physician: "Rt=1.3 suggests burnout spreading exponentially (SIR model analogy)"
6. Explicitly states: "Physician determines what action, if any, to take"
7. NO recommendations, NO decisions made by MEDCOM

**Access Model:** Read-Only Advisory (Data retrieval + Analysis, NO decisions/execution/directives)

---

### DELEGATION_AUDITOR
**Role:** ORCHESTRATOR Efficiency Monitoring & Delegation Pattern Analysis

**MCP Tools Needed:**
- `list_active_tasks` - Track which agents are active and their status
- `get_checkpoint_status` - Monitor task force completion rates
- `analyze_schedule_periodicity` - Identify recurring execution patterns
- `module_usage_analysis` - Analyze which agent specializations are used
- `benchmark_constraints` - Measure delegation effectiveness against baselines

**Rationale:**
DELEGATION_AUDITOR monitors how effectively ORCHESTRATOR delegates work vs. executing directly. It provides visibility into agent utilization, task force completion rates, and delegation pattern trends. This is a **READ-ONLY OBSERVER** role with no execution authority.

**Priority:** MEDIUM

**Workflow Integration:**
1. At session end, receives action summary from ORCHESTRATOR
2. Uses `list_active_tasks` to verify task force lifecycle tracking
3. Uses `benchmark_constraints` to measure delegation quality
4. Uses `analyze_schedule_periodicity` to detect recurring delegation patterns
5. Uses `module_usage_analysis` to see which specializations are over/under-used
6. Generates delegation audit report with metrics
7. Reports anti-patterns and improvement trends to ORCHESTRATOR

**Access Model:** Read-Only Observer (Monitoring + Analysis, NO execution)

---

### HISTORIAN
**Role:** Session Narrative Documentation & Institutional Memory (Documenter)

**MCP Tools Needed:**
- `rag_ingest` - Archive session narratives and poignant moments
- `rag_search` - Search prior narratives for continuity and context
- `rag_context` - Retrieve prior session context for narrative linkage

**Rationale:**
HISTORIAN preserves human-readable narratives of poignant sessions (breakthroughs, failures, design decisions) for Dr. Montgomery's understanding of system evolution. RAG tools enable archiving narratives and accessing context for longitudinal documentation.

**Priority:** LOW

**Workflow Integration:**
1. ORCHESTRATOR invokes HISTORIAN for poignant session (breakthrough, failure, design decision)
2. Receives context, artifacts, and narrative summary
3. Uses `rag_search` to find related prior narratives for continuity
4. Uses `rag_context` to retrieve historical context
5. Writes narrative markdown file documenting session
6. Uses `rag_ingest` to archive narrative in knowledge base
7. Notifies ORCHESTRATOR when complete

**Access Model:** Knowledge Archive (RAG operations only, NO execution/analysis)

---

## Tool Inventory by Category

### Available Tools: 85 Total

**Categories:**

| Category | Count | Available Tools |
|----------|-------|-----------------|
| **Scheduling & Validation** | 5 | validate_schedule, validate_schedule_by_id, detect_conflicts, analyze_swap_candidates, validate_deployment |
| **Resilience & Analysis** | 22 | run_contingency_analysis, check_utilization_threshold, get_defense_level, run_contingency_analysis_resilience, get_static_fallbacks, execute_sacrifice_hierarchy, analyze_homeostasis, calculate_blast_radius, analyze_le_chatelier, analyze_hub_centrality, assess_cognitive_load, get_behavioral_patterns, analyze_stigmergy, check_mtf_compliance, calculate_recovery_distance, assess_creep_fatigue, detect_critical_slowing_down, detect_schedule_changepoints, get_unified_critical_index |
| **Performance & Optimization** | 15 | benchmark_solvers, benchmark_constraints, ablation_study, benchmark_resilience, module_usage_analysis, calculate_shapley_workload, analyze_schedule_periodicity, optimize_erlang_coverage, calculate_erlang_metrics, calculate_process_capability, calculate_equity_metrics, generate_lorenz_curve, calculate_schedule_entropy, analyze_phase_transitions, optimize_free_energy |
| **Advanced Analytics** | 25 | calculate_burnout_rt, simulate_burnout_spread, simulate_burnout_contagion, check_circuit_breakers, get_breaker_health, test_half_open, override_circuit_breaker, assess_immune_response, check_memory_cells, analyze_antibody_response, get_entropy_monitor_state, calculate_time_crystal_objective, analyze_energy_landscape, calculate_hopfield_energy, find_nearby_attractors, measure_basin_depth, detect_spurious_attractors, detect_burnout_precursors, predict_burnout_magnitude, run_spc_analysis, calculate_workload_process_capability, calculate_fire_danger_index, calculate_batch_fire_danger, run_frms_assessment, get_checkpoint_status, get_time_crystal_health, get_fatigue_score, analyze_sleep_debt, evaluate_fatigue_hazard, scan_team_fatigue, assess_schedule_fatigue_risk |
| **Task Management** | 4 | start_background_task, get_task_status, cancel_task, list_active_tasks |
| **Deployment & Operations** | 10 | run_security_scan, run_smoke_tests, promote_to_production, rollback_deployment, get_deployment_status, list_deployments |
| **RAG/Knowledge** | 4 | rag_search, rag_context, rag_health, rag_ingest |

---

## Access Control Matrix

### FORCE_MANAGER
```
GRANT:
  - start_background_task  (Activate task forces)
  - get_task_status        (Monitor execution)
  - cancel_task            (Deactivate if needed)
  - list_active_tasks      (System-wide tracking)

DENY:
  - All scheduling tools (validate_schedule, detect_conflicts, etc.)
  - All deployment tools (promote_to_production, rollback_deployment)
  - All analysis tools (except task management)
  - All resilience execution tools (execute_sacrifice_hierarchy, etc.)

RATIONALE:
Manages task lifecycle, not execution. Coordinators execute tasks.
```

### DEVCOM_RESEARCH
```
GRANT:
  - rag_search             (Literature research)
  - rag_ingest             (Archive findings)
  - rag_context            (Exotic module context)
  - rag_health             (System check)
  - benchmark_resilience   (Prototype validation)
  - ablation_study         (Impact analysis)
  - module_usage_analysis  (Scheduling impact)
  - run_frms_assessment    (Feasibility check)

DENY:
  - All deployment tools (promote_to_production, rollback_deployment)
  - All production execution tools (schedule generation, swap execution)
  - All security tools (run_security_scan)
  - All operational tools (run_smoke_tests)

RATIONALE:
Research sandbox. Prototype and validate, but no production access.
Handoff to COORD_* teams for production implementation.
```

### MEDCOM
```
GRANT (READ-ONLY):
  - rag_search             (Clinical context)
  - rag_context            (ACGME rules)
  - get_unified_critical_index     (Translate metrics)
  - calculate_burnout_rt            (Burnout reproduction)
  - detect_burnout_precursors       (Early warnings)
  - get_fatigue_score               (Fatigue data)
  - scan_team_fatigue               (Team patterns)
  - analyze_sleep_debt              (Sleep context)

DENY (ALL OTHERS):
  - All execution/modification tools
  - All deployment tools
  - All scheduling tools
  - All operational/background task tools

RATIONALE:
Advisory-only. Surface information for physician decision-making.
No execution authority. No recommendations. No decisions.
```

### DELEGATION_AUDITOR
```
GRANT (READ-ONLY):
  - list_active_tasks              (Task tracking)
  - get_checkpoint_status          (Completion rates)
  - analyze_schedule_periodicity   (Pattern detection)
  - module_usage_analysis          (Specialization usage)
  - benchmark_constraints          (Effectiveness measurement)

DENY (ALL OTHERS):
  - All execution/modification tools
  - All deployment/operational tools
  - All scheduling tools

RATIONALE:
Observer role. Monitor delegation patterns, report metrics.
No execution authority. Read-only monitoring only.
```

### HISTORIAN
```
GRANT:
  - rag_ingest             (Archive narratives)
  - rag_search             (Find prior narratives)
  - rag_context            (Retrieve context)

DENY (ALL OTHERS):
  - All execution tools
  - All analysis tools
  - All operational tools

RATIONALE:
Knowledge archive only. Document poignant sessions, preserve context.
No execution authority. Archive operations only.
```

---

## Implementation Notes

1. **No Overlapping Execution:** Each agent has distinct MCP tool set with minimal overlap
2. **Read-Only for Advisory:** MEDCOM and AUDITOR are strictly read-only (no modifications)
3. **Research Sandbox:** DEVCOM gets RAG + benchmarking, explicitly NOT production deployment
4. **Task Lifecycle Separation:** FORCE_MANAGER manages task lifecycle, coordinators execute
5. **RAG Shared:** RAG tools (search, context, ingest) available to DEVCOM, MEDCOM, HISTORIAN
6. **No Medical Decisions:** MEDCOM has NO tools that could be construed as decision-making (no swaps, no executions, no recommendations)
7. **Monitoring Only:** DELEGATION_AUDITOR and HISTORIAN have zero execution capabilities

---

## Risk Assessment

### Low Risk
- **FORCE_MANAGER:** Task management tools are low-risk (queueing, not execution)
- **HISTORIAN:** RAG operations are safe (archival, no system modification)

### Medium Risk
- **MEDCOM:** Read-only tools, but burnout metrics are sensitive (mitigated by advisory-only role)
- **DELEGATION_AUDITOR:** Read-only observer (no risk if properly limited)

### Medium-High Risk
- **DEVCOM_RESEARCH:** Benchmarking tools could trigger heavy computation (recommend resource limits)

---

## Summary Table

```
AGENT                  TOOLS   PRIORITY  ACCESS TYPE           RISK
─────────────────────────────────────────────────────────────────
FORCE_MANAGER          4       HIGH      Execution + Monitor    Low
DEVCOM_RESEARCH        8       HIGH      Research Sandbox       Med-High
MEDCOM                 8       MEDIUM    Read-Only Advisory     Medium
DELEGATION_AUDITOR     5       MEDIUM    Read-Only Observer     Low
HISTORIAN              3       LOW       Archive Only           Low
─────────────────────────────────────────────────────────────────
TOTAL                  28
```

---

## Next Steps

1. Implement access control matrix in MCP server config
2. Add RBAC to each agent spec (Tools field)
3. Test tool access for each agent
4. Monitor DEVCOM_RESEARCH resource usage (benchmarking)
5. Audit MEDCOM output for advisory-only compliance
