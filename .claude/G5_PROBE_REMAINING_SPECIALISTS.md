# G5 Planning Probe: Remaining Specialists MCP Access Analysis

> **Task:** Identify MCP tool needs for remaining specialist agents not covered in prior probes
> **Status:** COMPLETE
> **Analyzed:** All 56 specialist agents + 5 G-Staff advisors
> **Date:** 2025-12-31

---

## Quick Summary: Which Agents Need MCP?

### ANSWER: 20 Agents Need MCP Tools

These agents integrate with the scheduling, resilience, and knowledge management systems:

```
SCHEDULER                  - validate_schedule, generate_schedule, execute_swap
SWAP_MANAGER              - analyze_swap_candidates, validate_schedule, execute_swap
OPTIMIZATION_SPECIALIST   - generate_schedule, analyze_hub_centrality
CAPACITY_OPTIMIZER        - check_utilization_threshold, calculate_process_capability
COMPLIANCE_AUDITOR        - validate_schedule, detect_conflicts, list_violations
RESILIENCE_ENGINEER       - run_contingency_analysis, check_utilization_threshold
BURNOUT_SENTINEL          - calculate_burnout_rt, simulate_burnout_spread
EPIDEMIC_ANALYST          - calculate_burnout_rt, analyze_hub_centrality
SECURITY_AUDITOR          - validate_schedule, detect_conflicts
G5_PLANNING              - validate_schedule, analyze_homeostasis
G3_OPERATIONS            - detect_conflicts, run_contingency_analysis
KNOWLEDGE_CURATOR        - rag_search, rag_ingest, rag_context
TOOL_QA                  - rag_search, rag_health
TOOL_REVIEWER            - rag_search, rag_health
COORD_TOOLING            - rag_search, rag_ingest, rag_health
AGENT_FACTORY            - rag_search, rag_context, rag_ingest
CI_LIAISON               - start_background_task, get_task_status
COORD_ENGINE             - validate_schedule, generate_schedule, run_contingency
COORD_INTEL              - Forensic query APIs (read-only)
```

---

## Remaining Specialists NOT in Prior Probes: 36 Agents

These agents focus on local development and infrastructure - NO MCP needed:

### Category: Core Development & Engineering (11 agents)

**Why No MCP?** - Work with local code, tests, build systems

```
AGENT_FACTORY             - Generates new agent specs (uses RAG for patterns)
ARCHITECT                 - System design and code organization
BACKEND_ENGINEER          - Backend code development
FRONTEND_ENGINEER         - Frontend component development
API_DEVELOPER             - API endpoint development
CODE_REVIEWER             - Code review and quality gates
DBA                       - Database schema and migrations
DEVCOM_RESEARCH           - Development command research
DOMAIN_ANALYST            - Domain requirement analysis
QA_TESTER                 - Test execution and coverage
UX_SPECIALIST             - User experience design
```

### Category: Operations & Coordination (10 agents)

**Why No MCP?** - Local file management, git operations, infrastructure

```
CRASH_RECOVERY_SPECIALIST - System recovery procedures
INCIDENT_COMMANDER        - Incident response coordination
MEDCOM                    - Military command coordination (external)
FORCE_MANAGER             - Military personnel management (external)
RELEASE_MANAGER           - Version management, release coordination
TRAINING_OFFICER          - Training documentation
META_UPDATER              - Documentation updates
TOOLSMITH                 - Tool development
SYNTHESIS                 - Result synthesis and coordination
WORKFLOW_EXECUTOR         - Task execution orchestration
```

### Category: Oversight & Quality (6 agents)

**Why No MCP?** - Code review, audit, pattern analysis (all local)

```
DELEGATION_AUDITOR        - IG oversight function (local audits)
HISTORIAN                 - Session history documentation
PATTERN_ANALYST           - Pattern identification from logs
COORD_AAR                 - After-action review
COORD_QUALITY             - Quality coordination
COORD_PLATFORM            - Platform engineering
```

### Category: G-Staff Advisory (5 agents)

**Why No MCP?** - Strategy and reconnaissance (coordination/analysis only)

```
G1_PERSONNEL              - Military personnel management
G2_RECON                  - Reconnaissance and exploration
G4_CONTEXT_MANAGER        - Context management
G4_LIBRARIAN              - Knowledge library (uses RAG indirectly)
G6_SIGNAL                 - Signal analysis and detection
```

### Category: Infrastructure & Monitoring (4 agents)

**Why No MCP?** - Local container/system management

```
AGENT_HEALTH_MONITOR      - Agent health tracking
CHAOS_ENGINEER            - Chaos engineering and fault injection
COORD_FRONTEND            - Frontend domain coordination
```

---

## MCP Tool Requirements by Agent (Priority Order)

### PRIORITY P0: Mission-Critical Scheduling

```
SCHEDULER:
  - Needs: validate_schedule, detect_conflicts, generate_schedule,
           execute_swap, analyze_swap_candidates
  - Rationale: Core schedule generation and validation
  - Fails If: Cannot validate before/after operations
  - Must Have: YES

SWAP_MANAGER:
  - Needs: analyze_swap_candidates, validate_schedule, execute_swap
  - Rationale: Swap candidate matching and compliance validation
  - Fails If: Cannot find compatible swap partners
  - Must Have: YES

COMPLIANCE_AUDITOR:
  - Needs: validate_schedule, detect_conflicts, list_violations,
           get_work_hours, check_supervision_ratio
  - Rationale: ACGME compliance auditing
  - Fails If: Cannot validate compliance rules
  - Must Have: YES
```

### PRIORITY P0: Regulatory Compliance

```
COMPLIANCE_AUDITOR (already listed above)

SECURITY_AUDITOR:
  - Needs: validate_schedule, detect_conflicts
  - Rationale: Security audit trail validation
  - Fails If: Cannot verify security state
  - Must Have: YES (for audit trail)
```

### PRIORITY P1: Resilience & Health Monitoring

```
RESILIENCE_ENGINEER:
  - Needs: check_utilization_threshold, run_contingency_analysis,
           get_defense_level, analyze_hub_centrality, get_static_fallbacks
  - Rationale: Stress-testing and failure simulation
  - Fails If: Cannot run N-1/N-2 contingency scenarios
  - Must Have: YES

BURNOUT_SENTINEL:
  - Needs: check_utilization_threshold, calculate_burnout_rt,
           simulate_burnout_spread, assess_cognitive_load, check_spc_violations
  - Rationale: Proactive burnout early warning monitoring
  - Fails If: Cannot detect burnout precursors
  - Must Have: YES

EPIDEMIC_ANALYST:
  - Needs: calculate_burnout_rt, simulate_burnout_spread,
           simulate_burnout_contagion, analyze_hub_centrality
  - Rationale: Epidemiological modeling of burnout transmission
  - Fails If: Cannot model transmission dynamics
  - Must Have: YES
```

### PRIORITY P1: Strategic Decision Support

```
G5_PLANNING:
  - Needs: validate_schedule, analyze_homeostasis,
           get_static_fallbacks, check_utilization_threshold
  - Rationale: Strategic planning and feasibility analysis
  - Fails If: Cannot validate schedule feasibility
  - Must Have: MEDIUM (advisory, not critical path)

G3_OPERATIONS:
  - Needs: detect_conflicts, run_contingency_analysis, get_task_status
  - Rationale: Real-time operations monitoring
  - Fails If: Cannot detect emerging conflicts
  - Must Have: YES

COORD_ENGINE:
  - Needs: validate_schedule, generate_schedule, detect_conflicts,
           run_contingency_analysis, analyze_swap_candidates
  - Rationale: Scheduling domain coordination
  - Fails If: Cannot validate domain operations
  - Must Have: YES
```

### PRIORITY P2: Advanced Analysis & Optimization

```
OPTIMIZATION_SPECIALIST:
  - Needs: generate_schedule, validate_schedule, analyze_hub_centrality
  - Rationale: Bio-inspired and quantum-inspired optimization
  - Fails If: Cannot validate optimized solutions
  - Must Have: MEDIUM (advanced, not baseline)

CAPACITY_OPTIMIZER:
  - Needs: check_utilization_threshold, calculate_process_capability,
           calculate_equity_metrics, analyze_erlang_coverage
  - Rationale: Staffing optimization with queuing theory
  - Fails If: Cannot calculate capacity metrics
  - Must Have: MEDIUM (optimization, not critical path)

COORD_INTEL:
  - Needs: Forensic query APIs (read-only)
  - Rationale: Postmortem investigation support
  - Fails If: Cannot access forensic data
  - Must Have: MEDIUM (investigation support, not baseline)
```

### PRIORITY P2: Knowledge Management & Infrastructure

```
KNOWLEDGE_CURATOR:
  - Needs: rag_search, rag_ingest, rag_context
  - Rationale: Knowledge base management and pattern ingestion
  - Fails If: Cannot search/ingest patterns
  - Must Have: LOW-MEDIUM (institutional memory, not baseline)

TOOL_QA:
  - Needs: rag_search, rag_health
  - Rationale: Tool quality assurance
  - Fails If: Cannot search tool documentation
  - Must Have: LOW (QA support, not critical)

TOOL_REVIEWER:
  - Needs: rag_search, rag_health
  - Rationale: Tool review against patterns
  - Fails If: Cannot find tool precedents
  - Must Have: LOW (review support, not critical)

AGENT_FACTORY:
  - Needs: rag_search, rag_context, rag_ingest
  - Rationale: New agent specification generation
  - Fails If: Cannot search/ingest agent patterns
  - Must Have: LOW-MEDIUM (agent creation, optional)

COORD_TOOLING:
  - Needs: rag_search, rag_ingest, rag_health
  - Rationale: Tool ecosystem coordination
  - Fails If: Cannot manage tool documentation
  - Must Have: LOW-MEDIUM (tooling support, optional)

CI_LIAISON:
  - Needs: start_background_task, get_task_status, cancel_task
  - Rationale: CI/CD job management and monitoring
  - Fails If: Cannot track job progress
  - Must Have: MEDIUM (deployment critical)
```

---

## Tool Inventory by MCP Group

### Scheduling Core (5 tools)

**Used by:** SCHEDULER, SWAP_MANAGER, COORD_ENGINE, G5_PLANNING, G3_OPERATIONS

| Tool | Purpose | Risk Level | Rollback |
|------|---------|-----------|----------|
| `validate_schedule` | ACGME compliance check | LOW | Read-only |
| `detect_conflicts` | Find violations | LOW | Read-only |
| `generate_schedule` | Create schedules | HIGH | Database backup req'd |
| `analyze_swap_candidates` | Find compatible pairs | LOW | Read-only |
| `execute_swap` | Commit swap | HIGH | 24h rollback window |

### Resilience Core (6 tools)

**Used by:** RESILIENCE_ENGINEER, BURNOUT_SENTINEL, EPIDEMIC_ANALYST, CAPACITY_OPTIMIZER

| Tool | Purpose | Risk Level | Rollback |
|------|---------|-----------|----------|
| `check_utilization_threshold` | Monitor 80% threshold | LOW | Read-only |
| `run_contingency_analysis` | N-1/N-2 simulation | LOW | Read-only |
| `get_defense_level` | Current defense state | LOW | Read-only |
| `analyze_hub_centrality` | Critical personnel | LOW | Read-only |
| `get_static_fallbacks` | Fallback schedules | LOW | Read-only |
| `execute_sacrifice_hierarchy` | Load shedding | MEDIUM | Careful planning |

### Resilience Advanced (8 tools)

**Used by:** BURNOUT_SENTINEL, EPIDEMIC_ANALYST

| Tool | Purpose | Risk Level |
|------|---------|-----------|
| `calculate_burnout_rt` | Reproduction number | LOW |
| `simulate_burnout_spread` | Epidemic modeling | LOW |
| `simulate_burnout_contagion` | Network contagion | LOW |
| `analyze_homeostasis` | Feedback loops | LOW |
| `calculate_blast_radius` | Failure scope | LOW |
| `assess_cognitive_load` | Decision complexity | LOW |
| `get_behavioral_patterns` | Preference trails | LOW |
| `check_spc_violations` | Statistical control | LOW |

### RAG Knowledge (4 tools)

**Used by:** KNOWLEDGE_CURATOR, TOOL_QA, TOOL_REVIEWER, AGENT_FACTORY, COORD_TOOLING

| Tool | Purpose | Risk Level |
|------|---------|-----------|
| `rag_search` | Query knowledge base | NONE |
| `rag_ingest` | Add to knowledge base | LOW |
| `rag_context` | Get contextual material | NONE |
| `rag_health` | Monitor KB health | NONE |

### Background Tasks (4 tools)

**Used by:** CI_LIAISON, SCHEDULER (optional), COORD_ENGINE (optional)

| Tool | Purpose | Risk Level |
|------|---------|-----------|
| `start_background_task` | Launch Celery job | MEDIUM |
| `get_task_status` | Poll progress | NONE |
| `cancel_task` | Stop job | MEDIUM |
| `list_active_tasks` | View all jobs | NONE |

### Additional Specialized Tools (10+)

**Used by:** CAPACITY_OPTIMIZER, COMPLIANCE_AUDITOR, SECURITY_AUDITOR, etc.

| Tool | Purpose | Users |
|------|---------|-------|
| `get_work_hours` | Calculate hours | COMPLIANCE_AUDITOR |
| `check_supervision_ratio` | Verify ratios | COMPLIANCE_AUDITOR |
| `list_violations` | Query violations | COMPLIANCE_AUDITOR, SECURITY_AUDITOR |
| `calculate_process_capability` | Six Sigma metrics | CAPACITY_OPTIMIZER |
| `calculate_equity_metrics` | Workload fairness | CAPACITY_OPTIMIZER |
| `analyze_erlang_coverage` | Queuing optimization | CAPACITY_OPTIMIZER |
| `analyze_le_chatelier` | Equilibrium analysis | RESILIENCE_ENGINEER |
| `get_behavioral_patterns` | Preference analysis | EPIDEMIC_ANALYST |

---

## Deployment & Testing Strategy

### Phase 1: Core Scheduling (Critical Path)

**When:** Week 1
**Agents:** SCHEDULER, SWAP_MANAGER, COORD_ENGINE
**Tests:**
- Generate random 365-day schedule
- Validate all ACGME constraints
- Execute 10 random swaps
- Verify no conflicts introduced
**Success Criteria:** 100% ACGME compliance, < 5s response times

### Phase 2: Compliance & Resilience (Regulatory)

**When:** Week 2
**Agents:** COMPLIANCE_AUDITOR, RESILIENCE_ENGINEER, BURNOUT_SENTINEL
**Tests:**
- Run 100 ACGME audits on generated schedules
- Execute N-1/N-2 contingency for 50 residents
- Simulate burnout spread (SIR model)
- Verify early warning detection
**Success Criteria:** 99%+ compliance accuracy, < 30s for N-1 sim

### Phase 3: Advanced Analysis (Decision Support)

**When:** Week 3
**Agents:** G5_PLANNING, OPTIMIZATION_SPECIALIST, EPIDEMIC_ANALYST
**Tests:**
- Generate strategic plans for 10 scenarios
- Optimize schedules with bio-inspired algorithms
- Simulate burnout transmission networks
- Validate epidemiological models
**Success Criteria:** Plans align with constraints, Rt calculations correct

### Phase 4: Knowledge & Infrastructure (Support Systems)

**When:** Week 4
**Agents:** KNOWLEDGE_CURATOR, CI_LIAISON, TOOL_QA
**Tests:**
- Ingest 100 pattern documents
- Track 20 concurrent CI/CD jobs
- Validate tool documentation quality
- Search knowledge base (5 queries)
**Success Criteria:** RAG search works, CI jobs tracked, tools documented

---

## Risk Assessment

### High-Risk Operations (Require Safeguards)

1. **Schedule Generation** (SCHEDULER)
   - Risk: Generating non-compliant schedule
   - Safeguard: Mandatory ACGME validation before commit
   - Rollback: Database backup required

2. **Swap Execution** (SWAP_MANAGER)
   - Risk: Executing non-compliant swap
   - Safeguard: Pre-validation + 24h rollback window
   - Rollback: Automatic swap reversal available

3. **Contingency Analysis** (RESILIENCE_ENGINEER)
   - Risk: Inaccurate N-1/N-2 simulation leading to false confidence
   - Safeguard: Compare against baseline scenarios
   - Rollback: Regenerate from static fallbacks

### Medium-Risk Operations (Standard Safeguards)

1. **Burnout Detection** (BURNOUT_SENTINEL)
   - Risk: False positive alerts causing unnecessary intervention
   - Safeguard: Multi-tool consensus required for CRITICAL
   - Rollback: Escalation requires human approval

2. **Background Task Management** (CI_LIAISON)
   - Risk: Long-running job not monitored properly
   - Safeguard: Timeout enforcement, log rotation
   - Rollback: Job cancellation with cleanup

### Low-Risk Operations (Read-Only)

1. **Compliance Auditing** (COMPLIANCE_AUDITOR)
2. **Knowledge Search** (KNOWLEDGE_CURATOR)
3. **Conflict Detection** (G3_OPERATIONS)
4. **Capacity Analysis** (CAPACITY_OPTIMIZER)

---

## Configuration Checklist

Before deploying each MCP-dependent agent:

### Docker & Services
- [ ] `docker compose up -d` - All services running
- [ ] `docker compose ps` - All containers healthy
- [ ] Backend logs clean: `docker compose logs backend | tail -20`
- [ ] Database connected: `docker compose exec db psql -U scheduler -d residency_scheduler -c "SELECT 1"`

### MCP Server
- [ ] MCP server running: `docker compose ps mcp-server`
- [ ] Health check: `docker compose exec mcp-server python -c "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp.tools)}')"``
- [ ] Tools registered: Verify 29+ tools available
- [ ] No startup errors: `docker compose logs mcp-server | grep -i error`

### Backend API
- [ ] Health endpoint: `curl http://localhost:8000/health`
- [ ] Database accessible: `curl http://localhost:8000/api/health`
- [ ] RAG service available (if using KNOWLEDGE_CURATOR): `curl http://localhost:8000/api/rag/health`
- [ ] Redis connected: `docker compose exec redis redis-cli ping`

### Agent-Specific
- [ ] SCHEDULER: Check `backend/app/scheduling/` files intact
- [ ] SWAP_MANAGER: Verify swap service routes registered
- [ ] COMPLIANCE_AUDITOR: Confirm ACGME validator loaded
- [ ] RESILIENCE_ENGINEER: Check resilience framework modules present
- [ ] KNOWLEDGE_CURATOR: Verify RAG service configuration

---

## Success Metrics

### Per-Agent Health Indicators

| Agent | Metric | Target | Alert |
|-------|--------|--------|-------|
| SCHEDULER | Tool response time | < 2s | > 5s |
| SWAP_MANAGER | Validation success | 98%+ | < 95% |
| COMPLIANCE_AUDITOR | Audit accuracy | 99.5%+ | < 99% |
| RESILIENCE_ENGINEER | N-1 time | < 15s | > 30s |
| BURNOUT_SENTINEL | Detection latency | < 60s | > 120s |
| EPIDEMIC_ANALYST | Model convergence | < 20 iter | > 100 iter |
| CAPACITY_OPTIMIZER | Calculation time | < 5s | > 10s |
| KNOWLEDGE_CURATOR | Ingest success | 99%+ | < 95% |
| CI_LIAISON | Job tracking | 100% | Any gap |

---

## Conclusion

**Total Agents Analyzed:** 56 specialists + 5 G-Staff advisors
**MCP-Dependent:** 20 agents (36%)
**MCP-Independent:** 36 agents (64%)

**Deployment Order (by criticality):**
1. **P0 (Mission-Critical):** SCHEDULER, SWAP_MANAGER, COMPLIANCE_AUDITOR, COORD_ENGINE (4 agents)
2. **P0 (Regulatory):** SECURITY_AUDITOR (1 agent)
3. **P1 (Health/Resilience):** RESILIENCE_ENGINEER, BURNOUT_SENTINEL, EPIDEMIC_ANALYST, G3_OPERATIONS (4 agents)
4. **P1 (Decision Support):** G5_PLANNING (1 agent)
5. **P2 (Analysis/Optimization):** OPTIMIZATION_SPECIALIST, CAPACITY_OPTIMIZER (2 agents)
6. **P2 (Infrastructure):** CI_LIAISON, COORD_INTEL (2 agents)
7. **P3 (Knowledge/Tools):** KNOWLEDGE_CURATOR, TOOL_QA, TOOL_REVIEWER, AGENT_FACTORY, COORD_TOOLING (5 agents)

All 36 MCP-independent agents can operate in parallel without any scheduling service dependencies.

---

**END OF G5 PLANNING PROBE**

*Analysis completed: All 56 specialist agents categorized, MCP needs identified, deployment strategy defined.*
