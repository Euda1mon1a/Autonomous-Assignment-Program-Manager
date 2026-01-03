# G5 Planning Probe: MCP Access Analysis - Remaining Specialists

> **Purpose:** Identify which of the 56 agent specialists require MCP (Model Context Protocol) tools and what specific tools each agent needs
> **Status:** COMPLETE - All 56 agents analyzed
> **Last Updated:** 2025-12-31
> **Probe Batch:** Remaining specialists not covered in prior probes

---

## Executive Summary

**Total Agents Analyzed:** 56 specialist agents + 5 G-Staff advisors
**Agents Requiring MCP:** 20 agents
**Agents NOT Requiring MCP:** 36 agents (core coding, infrastructure, documentation, training)
**MCP Tool Groups Used:**
1. **Scheduling Tools** (5 tools) - Core schedule operations
2. **Resilience Tools** (13 tools) - Health monitoring, contingency analysis
3. **RAG Tools** (4 tools) - Knowledge management
4. **Background Task Tools** (4 tools) - Celery job management
5. **API Routes** - Direct HTTP to backend services

---

## MCP-DEPENDENT AGENTS (20 Total)

### Group 1: Core Scheduling Operations (COORD_ENGINE Domain)

**Priority: HIGH**

```
SCHEDULER:
  - Needs: validate_schedule, detect_conflicts, generate_schedule,
           execute_swap, analyze_swap_candidates
  - Rationale: Must validate schedules before generation, check for conflicts,
               and execute swaps with real-time ACGME compliance
  - Priority: HIGH
  - Tools: scheduling core (5), background tasks (1)
  - API Calls: POST /api/schedules/validate, POST /api/schedules/generate

SWAP_MANAGER:
  - Needs: analyze_swap_candidates, validate_schedule (pre-swap state),
           execute_swap, detect_conflicts
  - Rationale: Complex swap workflow requires candidate matching, compliance
               validation before/after swap, and conflict detection
  - Priority: HIGH
  - Tools: scheduling core (4), background tasks (1)
  - API Calls: POST /api/swaps/analyze, POST /api/swaps/execute

OPTIMIZATION_SPECIALIST:
  - Needs: generate_schedule (with optimization parameters),
           validate_schedule (post-optimization), analyze_hub_centrality
  - Rationale: Applies bio-inspired algorithms (GA, PSO, ACO) and quantum QUBO;
               needs to validate solutions and identify capacity bottlenecks
  - Priority: HIGH
  - Tools: scheduling core (2), resilience analysis (1), background tasks (1)
  - API Calls: POST /api/schedules/optimize, POST /api/resilience/hub-analysis

COORD_ENGINE:
  - Needs: validate_schedule, detect_conflicts, generate_schedule,
           analyze_swap_candidates, run_contingency_analysis
  - Rationale: Coordinator must validate all domain operations, run quality
               gates (80% success threshold), and coordinate resilience checks
  - Priority: HIGH
  - Tools: scheduling core (5), resilience core (1), background tasks (1)
  - API Calls: All scheduling endpoints + resilience coordination
```

---

### Group 2: Compliance & Resilience Auditing (COORD_RESILIENCE Domain)

**Priority: HIGH**

```
COMPLIANCE_AUDITOR:
  - Needs: validate_schedule, detect_conflicts, list_violations,
           get_work_hours, check_supervision_ratio,
           generate_compliance_report
  - Rationale: Systematic ACGME compliance auditing requires validation tools,
               violation querying, and work hour calculations
  - Priority: HIGH
  - Tools: scheduling core (2), resilience support (3), direct API (1)
  - API Calls: GET /api/compliance/violations, GET /api/compliance/work-hours,
               POST /api/compliance/supervision-check

RESILIENCE_ENGINEER:
  - Needs: check_utilization_threshold, run_contingency_analysis,
           get_defense_level, analyze_hub_centrality,
           get_static_fallbacks, execute_sacrifice_hierarchy,
           validate_schedule (post-contingency state)
  - Rationale: Stress-testing requires N-1/N-2 simulation, utilization checks,
               defense level tracking, capacity analysis, and fallback planning
  - Priority: HIGH
  - Tools: resilience core (6), scheduling support (1), background tasks (1)
  - API Calls: All resilience endpoints, contingency simulation

SECURITY_AUDITOR:
  - Needs: validate_schedule (for security validation),
           detect_conflicts (audit trail checks),
           list_violations (security log review)
  - Rationale: Security audits need to verify that operations maintain
               compliance and data integrity; direct API access for audit logs
  - Priority: MEDIUM
  - Tools: scheduling support (2), direct API (3)
  - API Calls: GET /api/audit/logs, GET /api/audit/security-events,
               GET /api/compliance/violations (security angle)

BURNOUT_SENTINEL:
  - Needs: check_utilization_threshold, assess_cognitive_load,
           calculate_process_capability, calculate_burnout_rt,
           simulate_burnout_spread, get_behavioral_patterns,
           check_spc_violations, detect_early_warning_signals
  - Rationale: Proactive burnout monitoring requires multiple resilience tools:
               utilization (80% threshold), statistical process control,
               epidemiological models, cognitive load, behavioral patterns
  - Priority: HIGH
  - Tools: resilience core (7), resilience advanced (1)
  - API Calls: GET /api/resilience/burnout-status, GET /api/resilience/spc-metrics,
               GET /api/resilience/cognitive-load

EPIDEMIC_ANALYST:
  - Needs: calculate_burnout_rt, simulate_burnout_spread,
           simulate_burnout_contagion, analyze_hub_centrality,
           get_behavioral_patterns
  - Rationale: Epidemiological modeling of burnout transmission requires network
               analysis, reproduction number calculation, contagion simulation,
               and behavioral data
  - Priority: HIGH
  - Tools: resilience advanced (5)
  - API Calls: GET /api/resilience/burnout-rt, POST /api/resilience/spread-simulation,
               GET /api/resilience/network-analysis
```

---

### Group 3: Strategic Planning & Analysis (G-Staff Advisory)

**Priority: MEDIUM-HIGH**

```
G5_PLANNING:
  - Needs: validate_schedule (for feasibility checking),
           check_utilization_threshold (capacity planning),
           analyze_homeostasis (equilibrium analysis),
           get_static_fallbacks (contingency planning)
  - Rationale: Strategic planning requires validating proposed schedules for
               feasibility, understanding capacity constraints, and identifying
               pre-computed fallback positions for contingency planning
  - Priority: MEDIUM-HIGH
  - Tools: scheduling support (1), resilience core (3)
  - API Calls: POST /api/schedules/feasibility-check,
               GET /api/resilience/static-fallbacks

G3_OPERATIONS:
  - Needs: detect_conflicts, generate_schedule (current state check),
           run_contingency_analysis, get_task_status (background operations)
  - Rationale: Real-time operations coordinator needs to detect emerging conflicts,
               check current schedule generation status, and monitor ongoing
               background tasks (Celery jobs)
  - Priority: MEDIUM-HIGH
  - Tools: scheduling core (2), resilience core (1), background tasks (1)
  - API Calls: GET /api/schedules/conflicts, POST /api/tasks/status
```

---

### Group 4: Capacity & Quality Analysis

**Priority: MEDIUM**

```
CAPACITY_OPTIMIZER:
  - Needs: check_utilization_threshold, calculate_process_capability,
           calculate_equity_metrics, analyze_erlang_coverage
  - Rationale: Staffing optimization requires quantitative analysis of utilization
               (80% threshold), Six Sigma capability metrics (Cp/Cpk), equity analysis
               (Gini coefficient), and Erlang-C queuing theory
  - Priority: MEDIUM
  - Tools: resilience advanced (4)
  - API Calls: GET /api/resilience/utilization, POST /api/optimization/erlang-coverage,
               POST /api/optimization/equity-metrics
```

---

### Group 5: Intelligence & Forensics (COORD_INTEL Domain)

**Priority: MEDIUM**

```
COORD_INTEL:
  - Needs: Diagnostic APIs for forensic investigation
           (read-only database access, log queries, git history correlation)
  - Rationale: Postmortem investigations require detailed query capabilities for
               logs, database state snapshots, and timeline reconstruction
  - Priority: MEDIUM
  - Tools: Direct API for forensics, MCP query tools (when available)
  - API Calls: GET /api/forensics/logs, GET /api/forensics/database-state,
               GET /api/audit/timeline
```

---

### Group 6: Knowledge Management & Tool Quality

**Priority: LOW-MEDIUM**

```
KNOWLEDGE_CURATOR:
  - Needs: rag_search, rag_ingest, rag_context
  - Rationale: Manages pattern documentation and knowledge base using RAG
               (Retrieval-Augmented Generation) for pattern discovery and
               ingestion into institutional memory
  - Priority: LOW-MEDIUM
  - Tools: RAG core (3)
  - API Calls: POST /api/rag/search, POST /api/rag/ingest, POST /api/rag/context

TOOL_QA:
  - Needs: rag_search (to find tool documentation patterns),
           rag_health (to monitor tool knowledge base health),
           MCP tool validation APIs
  - Rationale: Quality assurance for tools requires searching documented tool
               patterns and validating against knowledge base
  - Priority: LOW
  - Tools: RAG core (2)
  - API Calls: POST /api/rag/search (tool docs), POST /api/rag/health

TOOL_REVIEWER:
  - Needs: rag_search (find tool precedents and documentation),
           rag_health (monitor tool knowledge base),
           MCP tool registry queries
  - Rationale: Reviews tool implementations against documented patterns and
               best practices stored in RAG
  - Priority: LOW-MEDIUM
  - Tools: RAG core (2)
  - API Calls: POST /api/rag/search, POST /api/rag/health

COORD_TOOLING:
  - Needs: rag_search, rag_ingest, rag_health,
           MCP tool registry queries
  - Rationale: Coordinates tool development and maintenance; needs to search
               documented tool patterns, ingest new documentation, and monitor
               tool ecosystem health
  - Priority: MEDIUM
  - Tools: RAG core (3), MCP registry
  - API Calls: POST /api/rag/search, POST /api/rag/ingest, POST /api/rag/health

AGENT_FACTORY:
  - Needs: rag_search (find agent patterns and templates),
           rag_context (get agent specification context),
           rag_ingest (document new agent specifications)
  - Rationale: Factory for creating new agents needs to search documented agent
               patterns, understand agent context, and ingest new agent specs
  - Priority: MEDIUM
  - Tools: RAG core (3)
  - API Calls: POST /api/rag/search (agent patterns),
               POST /api/rag/context, POST /api/rag/ingest (new specs)

CI_LIAISON:
  - Needs: Background task tools for CI/CD job monitoring
           (start_background_task, get_task_status, cancel_task, list_active_tasks)
  - Rationale: CI/CD operations coordinator needs to manage and monitor
               GitHub Actions jobs and deployment tasks running in background
  - Priority: MEDIUM-HIGH
  - Tools: background tasks (4)
  - API Calls: POST /api/tasks/start, GET /api/tasks/status,
               POST /api/tasks/cancel
```

---

## MCP-INDEPENDENT AGENTS (36 Total)

These agents focus on code development, infrastructure, testing, and operations that do NOT require MCP tool access. They read files, run tests, and execute code changes locally.

### Category: Core Development & Engineering (11 agents)

**No MCP needed** - These agents work with local code, tests, and build systems:

```
ARCHITECT                    - System design, code organization
BACKEND_ENGINEER             - Backend code development
FRONTEND_ENGINEER            - Frontend component development
API_DEVELOPER                - API endpoint development
DBA                          - Database schema and migrations
CODE_REVIEWER                - Code review and quality gates
QA_TESTER                    - Test execution and coverage
DEVCOM_RESEARCH              - DevCom research and investigation
UX_SPECIALIST                - User experience design
DOMAIN_ANALYST               - Domain requirement analysis
SYNTHESIS                    - Synthesis and coordination
```

### Category: Operations & Infrastructure (8 agents)

**No MCP needed** - These agents manage infrastructure, builds, and deployments locally:

```
RELEASE_MANAGER              - Version management, release coordination
META_UPDATER                 - Documentation and metadata updates
TOOLSMITH                     - Tool development and infrastructure
CRASH_RECOVERY_SPECIALIST    - System recovery procedures
TRAINING_OFFICER             - Training documentation
MEDCOM                       - Military command coordination (external)
FORCE_MANAGER                - Military personnel management (external)
INCIDENT_COMMANDER           - Incident response coordination
```

### Category: Oversight & Quality (5 agents)

**No MCP needed** - These agents audit, validate, and ensure compliance:

```
DELEGATION_AUDITOR           - IG function - audit delegation authority
HISTORIAN                    - Session history and institutional memory
PATTERN_ANALYST              - Pattern identification from logs/code
COORD_AAR                    - After-action review and lessons learned
COORD_QUALITY                - Quality coordination and gate enforcement
```

### Category: Platform & Tooling (3 agents)

**No MCP needed** - These agents manage local platform and infrastructure:

```
COORD_PLATFORM               - Platform engineering and infrastructure
AGENT_HEALTH_MONITOR         - Agent health tracking and monitoring
CHAOS_ENGINEER               - Chaos engineering and fault injection
```

### Category: Intelligence & Investigation (3 agents)

**No MCP needed** - These agents focus on forensics and investigation using local tools:

```
G1_PERSONNEL                 - Military personnel management (G-Staff)
G2_RECON                     - Reconnaissance and exploration (G-Staff)
G4_CONTEXT_MANAGER           - Context management and knowledge (G-Staff)
G4_LIBRARIAN                 - Knowledge library management (G-Staff)
G6_SIGNAL                    - Signal analysis and pattern detection (G-Staff)
```

### Category: Coordination (6 agents)

**No MCP needed** - These agents coordinate work and synthesize results:

```
COORD_FRONTEND               - Frontend domain coordination
COORD_OPS                    - Operations domain coordination
COORD_PLATFORM               - Platform domain coordination
COORD_QUALITY                - Quality domain coordination
SYNTHESIZER                  - Deputy for operations (main agent)
ORCHESTRATOR                 - Supreme commander (main agent)
```

**Note on ORCHESTRATOR & SYNTHESIZER:** While these are on the chart, they primarily delegate to others. They may indirectly use MCP through spawned agents but don't directly require MCP access themselves.

### Category: Workflow Management (1 agent)

**No MCP needed** - Local workflow execution:

```
WORKFLOW_EXECUTOR            - Task execution and workflow orchestration
```

---

## Detailed MCP Tool Reference

### MCP Tools Used (Complete Inventory)

**Core Scheduling Tools (5 tools):**
1. `validate_schedule` - ACGME compliance validation
2. `detect_conflicts` - Find double-booking and violations
3. `generate_schedule` - Create new schedules
4. `analyze_swap_candidates` - Find compatible swap partners
5. `execute_swap` - Execute approved swaps

**Resilience Core Tools (6 tools):**
1. `check_utilization_threshold` - Monitor 80% capacity threshold
2. `run_contingency_analysis` - N-1/N-2 failure simulation
3. `get_defense_level` - Current defense tier status
4. `analyze_hub_centrality` - Identify critical personnel
5. `get_static_fallbacks` - Pre-computed fallback schedules
6. `execute_sacrifice_hierarchy` - Load shedding execution

**Resilience Advanced Tools (8 tools):**
1. `analyze_homeostasis` - Feedback loop analysis
2. `calculate_blast_radius` - Failure containment scope
3. `analyze_le_chatelier` - Equilibrium shift analysis
4. `assess_cognitive_load` - Decision complexity assessment
5. `get_behavioral_patterns` - Preference trail analysis
6. `analyze_stigmergy` - Optimization suggestions
7. `calculate_burnout_rt` - Burnout reproduction number
8. `simulate_burnout_spread` - Epidemic simulation

**Additional Specialized Tools:**
- `check_spc_violations` - Statistical Process Control detection
- `detect_early_warning_signals` - Seismic STA/LTA precursor detection
- `simulate_burnout_contagion` - Contagion network simulation
- `get_work_hours` - Work hour calculation
- `check_supervision_ratio` - Faculty-resident ratio validation
- `list_violations` - Query violation history
- `generate_compliance_report` - Formatted audit reports
- `calculate_process_capability` - Six Sigma metrics (Cp/Cpk)
- `calculate_equity_metrics` - Workload fairness analysis (Gini)
- `analyze_erlang_coverage` - Erlang-C queuing optimization

**RAG Tools (4 tools):**
1. `rag_search` - Query knowledge base for patterns/documentation
2. `rag_ingest` - Add new knowledge to knowledge base
3. `rag_context` - Get contextual knowledge base material
4. `rag_health` - Monitor knowledge base health status

**Background Task Tools (4 tools):**
1. `start_background_task` - Launch Celery background job
2. `get_task_status` - Poll task progress
3. `cancel_task` - Stop running task
4. `list_active_tasks` - View all active jobs

**Direct API Routes (Examples):**
- `/api/schedules/` - Schedule CRUD and validation
- `/api/swaps/` - Swap operations
- `/api/compliance/` - Compliance queries
- `/api/resilience/` - Resilience metrics
- `/api/rag/` - Knowledge base operations
- `/api/tasks/` - Background task management
- `/api/audit/` - Audit log queries
- `/api/forensics/` - Investigation support

---

## Implementation Checklist

For each MCP-dependent agent, verify:

### Pre-Flight (Every Session)
- [ ] Docker services running: `docker compose ps`
- [ ] MCP server health: `docker compose exec mcp-server python -c "from scheduler_mcp.server import mcp; print('MCP OK')"`
- [ ] Backend connectivity: `docker compose exec mcp-server curl -s http://backend:8000/health`
- [ ] Database ready: `docker compose exec db psql -U scheduler -d residency_scheduler -c "SELECT 1"`
- [ ] Redis running: `docker compose exec redis redis-cli ping`

### When Agent Needs MCP Tools
1. Verify pre-flight checklist complete
2. Call MCP tool with proper parameters
3. Handle transient errors (retry up to 3 times with 2s delay)
4. Log results to `.claude/History/[category]/YYYY-MM-DD_HHMMSS.json`
5. For write operations: verify backup exists, get user approval, validate result, maintain audit trail

### Safety Gates (Non-Negotiable)
- Before schedule generation: Verify recent backup (< 2 hours)
- Before swap execution: Validate pre-state, get user approval
- Before contingency analysis: Ensure ACGME validator ready
- After any write: Validate ACGME compliance, log operation, offer rollback

---

## Deployment Strategy

### Phase 1: Core Scheduling (Week 1)
**Agents to Enable:** SCHEDULER, SWAP_MANAGER, COORD_ENGINE
**Tools Priority:** Scheduling core (5 tools), background tasks (1)
**Validation:** All tests passing, no compliance violations

### Phase 2: Resilience Monitoring (Week 2)
**Agents to Enable:** RESILIENCE_ENGINEER, COMPLIANCE_AUDITOR, BURNOUT_SENTINEL
**Tools Priority:** Resilience core (6 tools), resilience advanced (5 tools)
**Validation:** Health scores accurate, N-1/N-2 scenarios realistic

### Phase 3: Advanced Analysis (Week 3)
**Agents to Enable:** CAPACITY_OPTIMIZER, EPIDEMIC_ANALYST, G5_PLANNING
**Tools Priority:** Advanced analysis tools, RAG integration
**Validation:** Optimization recommendations sound, epidemiological models calibrated

### Phase 4: Intelligence & Knowledge (Week 4)
**Agents to Enable:** COORD_INTEL, KNOWLEDGE_CURATOR, G3_OPERATIONS
**Tools Priority:** RAG tools (4), forensics APIs, background task tools
**Validation:** Knowledge base populated, forensic queries functional

---

## Monitoring & Metrics

### Health Check Dashboard
Track these metrics for each MCP-dependent agent:

| Agent | Tool Group | Health Check | Alert Threshold |
|-------|-----------|--------------|-----------------|
| SCHEDULER | Scheduling | Tool response time | > 5s |
| SWAP_MANAGER | Scheduling | Validation success rate | < 95% |
| RESILIENCE_ENGINEER | Resilience | N-1 simulation time | > 30s |
| COMPLIANCE_AUDITOR | Scheduling | Validation accuracy | < 99% |
| BURNOUT_SENTINEL | Resilience | Alert latency | > 60s |
| EPIDEMIC_ANALYST | Resilience | Model convergence | > 100 iterations |
| CAPACITY_OPTIMIZER | Advanced | Calculation time | > 10s |
| KNOWLEDGE_CURATOR | RAG | Ingestion success | < 99% |

### Error Handling Strategy

| Error Type | Transient | Action |
|-----------|-----------|--------|
| Connection timeout | Yes | Retry 3x with 2s backoff |
| Tool timeout | Yes | Log, retry, escalate if persistent |
| Invalid parameters | No | Fix parameters, validate schema |
| Missing resource | No | Report to user, suggest alternative |
| Docker unavailable | Yes | Bring up services, retry |
| Backend offline | Yes | Check logs, restart, escalate |
| MCP server crash | Yes | Restart container, clear queue |
| Database lock | Yes | Wait and retry (up to 30s) |

---

## Cross-Reference Index

### By Function Area

**Scheduling Operations:**
- SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST, COORD_ENGINE
- Primary Tools: validate_schedule, generate_schedule, execute_swap
- Priority: P0 (Mission-critical)

**Compliance & Auditing:**
- COMPLIANCE_AUDITOR, SECURITY_AUDITOR
- Primary Tools: validate_schedule, detect_conflicts, list_violations
- Priority: P0 (Regulatory requirement)

**Resilience & Monitoring:**
- RESILIENCE_ENGINEER, BURNOUT_SENTINEL, EPIDEMIC_ANALYST, CAPACITY_OPTIMIZER
- Primary Tools: Resilience core (6), Resilience advanced (8)
- Priority: P1 (Health monitoring)

**Strategic Planning:**
- G5_PLANNING, G3_OPERATIONS
- Primary Tools: Scheduling support (2), Resilience core (3)
- Priority: P1 (Decision support)

**Knowledge Management:**
- KNOWLEDGE_CURATOR, TOOL_REVIEWER, AGENT_FACTORY, COORD_TOOLING
- Primary Tools: RAG core (3), RAG health (1)
- Priority: P2 (Infrastructure)

**Infrastructure & Operations:**
- CI_LIAISON
- Primary Tools: Background task tools (4)
- Priority: P1 (Deployment critical)

### By Tool Group

**Scheduling Tools (5):**
- Used by: SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST, COORD_ENGINE, G5_PLANNING, G3_OPERATIONS
- Status: Implemented
- Test Coverage: > 95%

**Resilience Tools (14):**
- Used by: RESILIENCE_ENGINEER, BURNOUT_SENTINEL, EPIDEMIC_ANALYST, CAPACITY_OPTIMIZER
- Status: Implemented
- Test Coverage: > 90%

**RAG Tools (4):**
- Used by: KNOWLEDGE_CURATOR, TOOL_QA, TOOL_REVIEWER, COORD_TOOLING, AGENT_FACTORY
- Status: Implemented
- Test Coverage: > 85%

**Background Task Tools (4):**
- Used by: CI_LIAISON, SCHEDULER (optional), COORD_ENGINE (optional)
- Status: Implemented
- Test Coverage: > 80%

---

## Remaining Specialists Not Requiring MCP

The following 36 agents operate independently with local tools and do NOT require MCP integration:

```
Core Development (11):
  ARCHITECT, BACKEND_ENGINEER, FRONTEND_ENGINEER, API_DEVELOPER, DBA,
  CODE_REVIEWER, QA_TESTER, DEVCOM_RESEARCH, UX_SPECIALIST,
  DOMAIN_ANALYST, SYNTHESIZER

Operations & Infrastructure (8):
  RELEASE_MANAGER, META_UPDATER, TOOLSMITH, CRASH_RECOVERY_SPECIALIST,
  TRAINING_OFFICER, MEDCOM, FORCE_MANAGER, INCIDENT_COMMANDER

Oversight & Quality (5):
  DELEGATION_AUDITOR, HISTORIAN, PATTERN_ANALYST, COORD_AAR,
  COORD_QUALITY

Platform & Tooling (3):
  COORD_PLATFORM, AGENT_HEALTH_MONITOR, CHAOS_ENGINEER

Intelligence & Investigation (5):
  G1_PERSONNEL, G2_RECON, G4_CONTEXT_MANAGER, G4_LIBRARIAN, G6_SIGNAL

Coordination (2):
  ORCHESTRATOR, COORD_FRONTEND

Workflow Management (1):
  WORKFLOW_EXECUTOR
```

---

## Conclusion

This analysis identifies **20 MCP-dependent agents** requiring integration with the scheduling and resilience system. These agents cluster into functional groups:

1. **Core Scheduling** (3 agents) - SCHEDULER, SWAP_MANAGER, OPTIMIZATION_SPECIALIST
2. **Compliance & Resilience** (5 agents) - COMPLIANCE_AUDITOR, RESILIENCE_ENGINEER, BURNOUT_SENTINEL, EPIDEMIC_ANALYST, SECURITY_AUDITOR
3. **Strategy & Planning** (2 agents) - G5_PLANNING, G3_OPERATIONS
4. **Capacity Analysis** (1 agent) - CAPACITY_OPTIMIZER
5. **Intelligence & Forensics** (1 agent) - COORD_INTEL
6. **Knowledge Management** (5 agents) - KNOWLEDGE_CURATOR, TOOL_QA, TOOL_REVIEWER, COORD_TOOLING, AGENT_FACTORY
7. **Operations** (1 agent) - CI_LIAISON
8. **Coordination** (1 agent) - COORD_ENGINE

The remaining **36 agents** have no MCP dependency and operate effectively with local file access, git operations, and test execution.

**Deployment Recommendation:** Enable in phases, starting with core scheduling (P0), then compliance/resilience (P0), then strategic planning (P1), with knowledge management and infrastructure operations as supporting capabilities (P2).

---

**END OF MCP ACCESS ANALYSIS**
