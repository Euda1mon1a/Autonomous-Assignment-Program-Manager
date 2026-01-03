# G5 Planning Probe: Complete Index

> **Mission:** G-5 Staff Planning probe to identify MCP access needs for remaining specialists
> **Status:** COMPLETE
> **Completion Date:** 2025-12-31
> **Batch:** All remaining specialists (all 56 agents analyzed)
> **Output:** 3 comprehensive analysis documents

---

## Probe Deliverables

### Document 1: Full MCP Access Analysis
**File:** `.claude/MCP_ACCESS_ANALYSIS.md`
**Purpose:** Comprehensive MCP tool inventory and agent mapping
**Contents:**
- Executive summary (20 agents require MCP, 36 don't)
- Detailed agent-by-agent MCP requirements
- MCP tool reference guide (all 29+ tools)
- Deployment strategy (4 phases)
- Implementation checklist
- Monitoring & metrics dashboard

**Use When:** You need complete architectural understanding of MCP integration

---

### Document 2: Remaining Specialists Analysis
**File:** `.claude/G5_PROBE_REMAINING_SPECIALISTS.md`
**Purpose:** Quick assessment of which agents need MCP and why
**Contents:**
- Quick summary (which 20 agents need MCP)
- Remaining 36 agents (organized by category)
- MCP tool requirements by priority (P0, P1, P2)
- Tool inventory with risk assessment
- Deployment & testing strategy
- Risk mitigation for high-risk operations
- Configuration checklist
- Success metrics per agent

**Use When:** You need to understand remaining specialists and prioritize deployment

---

### Document 3: Agent MCP Dependency Matrix
**File:** `.claude/AGENT_MCP_MATRIX.md`
**Purpose:** Quick reference lookup table for all 61 agents
**Contents:**
- Summary table (all 61 agents with MCP needs)
- Detailed listings of MCP-required agents
- MCP-independent agents (36 total)
- Tool group summary (which agents use each tool group)
- Dependency graph (how agents relate)
- Deployment checklist (phased approach)
- Quick reference decision table
- Key statistics

**Use When:** You need a quick lookup or want to see the whole picture at once

---

## Analysis Results Summary

### What We Learned

#### MCP-Dependent Agents: 20 Total

**Mission-Critical (P0):** 6 agents
- SCHEDULER - Schedule generation with ACGME validation
- SWAP_MANAGER - Swap execution with compliance checking
- COORD_ENGINE - Scheduling domain coordinator
- COMPLIANCE_AUDITOR - ACGME compliance auditing
- SECURITY_AUDITOR - Security audit trail validation
- RESILIENCE_ENGINEER - Failure simulation and N-1/N-2 testing

**Health Monitoring (P1):** 5 agents
- BURNOUT_SENTINEL - Early warning system for burnout
- EPIDEMIC_ANALYST - Burnout transmission modeling
- G3_OPERATIONS - Real-time operations monitoring
- G5_PLANNING - Strategic planning and feasibility analysis

**Support & Analysis (P2-P3):** 9 agents
- OPTIMIZATION_SPECIALIST - Bio-inspired and quantum optimization
- CAPACITY_OPTIMIZER - Staffing optimization with queuing theory
- COORD_INTEL - Investigation support with forensic APIs
- CI_LIAISON - CI/CD job management
- KNOWLEDGE_CURATOR - Knowledge base management (RAG)
- TOOL_QA - Tool quality assurance
- TOOL_REVIEWER - Tool documentation review
- AGENT_FACTORY - New agent specification generation
- COORD_TOOLING - Tool ecosystem coordination

#### MCP-Independent Agents: 36 Total

These agents focus on code development, infrastructure, testing, and oversight:

**Development (11):** ARCHITECT, BACKEND_ENGINEER, FRONTEND_ENGINEER, API_DEVELOPER, DBA, CODE_REVIEWER, QA_TESTER, DEVCOM_RESEARCH, DOMAIN_ANALYST, UX_SPECIALIST, SYNTHESIZER

**Operations (9):** CRASH_RECOVERY_SPECIALIST, INCIDENT_COMMANDER, RELEASE_MANAGER, META_UPDATER, TOOLSMITH, TRAINING_OFFICER, MEDCOM, FORCE_MANAGER, WORKFLOW_EXECUTOR

**Oversight (6):** DELEGATION_AUDITOR, HISTORIAN, PATTERN_ANALYST, COORD_AAR, COORD_QUALITY, COORD_PLATFORM

**G-Staff (5):** G1_PERSONNEL, G2_RECON, G4_CONTEXT_MANAGER, G4_LIBRARIAN, G6_SIGNAL

**Infrastructure (3):** AGENT_HEALTH_MONITOR, CHAOS_ENGINEER, COORD_FRONTEND

**Command (1):** ORCHESTRATOR (delegates only)

---

### Key Findings

1. **33% of agents require MCP** (20 out of 61)
   - These are the "systems-facing" agents that interact with the scheduling engine
   - The other 67% are "code-facing" agents that work with local files and tests

2. **Clear dependency hierarchy:**
   - P0: Schedule generation, validation, compliance (6 agents) - these CANNOT skip MCP
   - P1: Resilience, operations, planning (5 agents) - health monitoring and decision support
   - P2: Optimization, investigation, deployment (5 agents) - advanced capabilities
   - P3: Knowledge management, tooling (5 agents) - infrastructure support

3. **MCP tools cluster into 6 groups:**
   - Scheduling core (5 tools) - used by 10 agents
   - Resilience core (6 tools) - used by 4 agents
   - Resilience advanced (8+ tools) - used by 4 agents
   - RAG knowledge (4 tools) - used by 5 agents
   - Background tasks (4 tools) - used by 3 agents
   - Additional specialized tools - used by 3 agents

4. **High-risk operations requiring safeguards:**
   - Schedule generation (needs backup + validation)
   - Swap execution (needs pre-validation + 24h rollback)
   - Contingency analysis (needs accuracy verification)

5. **No critical gaps:** All 36 MCP-independent agents can operate in parallel without dependencies on the scheduling system

---

## Document Navigation Guide

### If You Need To...

**Understand which agents need MCP:**
→ Start with `AGENT_MCP_MATRIX.md` (quick table)
→ Then read `G5_PROBE_REMAINING_SPECIALISTS.md` (detailed explanation)

**Plan deployment strategy:**
→ Read `G5_PROBE_REMAINING_SPECIALISTS.md` (4 phases)
→ Reference `MCP_ACCESS_ANALYSIS.md` (detailed implementation)

**Get complete technical details:**
→ Read `MCP_ACCESS_ANALYSIS.md` (comprehensive reference)

**Make quick decisions:**
→ Use `AGENT_MCP_MATRIX.md` (decision tables)

**Understand agent dependencies:**
→ Check `AGENT_MCP_MATRIX.md` (dependency graph)
→ Cross-reference with `MCP_ACCESS_ANALYSIS.md` (detailed relationships)

**Configure a specific agent:**
→ Look up agent in `AGENT_MCP_MATRIX.md`
→ Find tool requirements
→ Reference tool specs in `MCP_ACCESS_ANALYSIS.md`

---

## Priority-Based Implementation Path

### Phase 1: Core Scheduling (Week 1)
**Goal:** Enable basic schedule generation and validation
**Agents (4):** SCHEDULER, SWAP_MANAGER, COORD_ENGINE, OPTIMIZATION_SPECIALIST
**Key Tools:** Scheduling core (5)
**Success Criteria:**
- Generate 365-day schedule without violations
- Execute 10 swaps without errors
- Response times < 5 seconds

**Deployment:**
1. Enable SCHEDULER with schedule validation
2. Enable SWAP_MANAGER with swap execution
3. Enable COORD_ENGINE with quality gates
4. Enable OPTIMIZATION_SPECIALIST with algorithm validation
5. Run integration tests (all 4 agents working together)
6. Verify no ACGME violations introduced

---

### Phase 2: Compliance & Resilience (Week 2)
**Goal:** Add compliance auditing and resilience testing
**Agents (4):** COMPLIANCE_AUDITOR, SECURITY_AUDITOR, RESILIENCE_ENGINEER, G3_OPERATIONS
**Key Tools:** Scheduling validation (2), Resilience core (6)
**Success Criteria:**
- Run 100 compliance audits with 99%+ accuracy
- Execute N-1/N-2 tests in < 30 seconds
- Detect all compliance violations

**Deployment:**
1. Enable COMPLIANCE_AUDITOR for audit workflows
2. Enable SECURITY_AUDITOR for audit trail validation
3. Enable RESILIENCE_ENGINEER for failure simulation
4. Enable G3_OPERATIONS for conflict monitoring
5. Run resilience tests (N-1, N-2 scenarios)
6. Validate audit accuracy against known violations

---

### Phase 3: Burnout & Strategic Planning (Week 3)
**Goal:** Add health monitoring and strategic planning
**Agents (3):** BURNOUT_SENTINEL, EPIDEMIC_ANALYST, G5_PLANNING
**Key Tools:** Resilience advanced (8), Strategic tools (3)
**Success Criteria:**
- Detect burnout early warnings (< 60s latency)
- Model burnout transmission with accurate Rt
- Generate feasible strategic plans

**Deployment:**
1. Enable BURNOUT_SENTINEL for early warning
2. Enable EPIDEMIC_ANALYST for transmission modeling
3. Enable G5_PLANNING for strategic planning
4. Run burnout detection tests (simulate burnout events)
5. Validate epidemic model against baseline scenarios
6. Test strategic plan generation

---

### Phase 4: Advanced Support Systems (Week 4)
**Goal:** Add optimization, investigation, and knowledge management
**Agents (5):** CAPACITY_OPTIMIZER, COORD_INTEL, CI_LIAISON, KNOWLEDGE_CURATOR, TOOL_ECOSYSTEM (TOOL_QA, TOOL_REVIEWER, AGENT_FACTORY, COORD_TOOLING)
**Key Tools:** Advanced analysis (4), Forensics (1), RAG (4), Background tasks (4)
**Success Criteria:**
- Calculate capacity metrics accurately
- Query forensic data successfully
- Track CI/CD jobs effectively
- Search knowledge base with correct results

**Deployment:**
1. Enable CAPACITY_OPTIMIZER for staffing optimization
2. Enable COORD_INTEL for forensic queries
3. Enable CI_LIAISON for job tracking
4. Enable KNOWLEDGE_CURATOR for knowledge management
5. Enable tool ecosystem agents (TOOL_QA, TOOL_REVIEWER, AGENT_FACTORY, COORD_TOOLING)
6. Run end-to-end integration tests

---

## Risk Mitigation Strategies

### High-Risk Operations (Require Safeguards)

**1. Schedule Generation (SCHEDULER)**
- Risk: Non-compliant schedule deployed
- Safeguards:
  - Mandatory ACGME validation before commit
  - Database backup required
  - Dry-run validation before writing
- Rollback: Restore from backup

**2. Swap Execution (SWAP_MANAGER)**
- Risk: Non-compliant swap executed
- Safeguards:
  - Pre-validation checks
  - 24-hour rollback window
  - Audit trail maintained
- Rollback: Automatic swap reversal

**3. Contingency Analysis (RESILIENCE_ENGINEER)**
- Risk: Inaccurate N-1/N-2 simulation
- Safeguards:
  - Compare against baseline scenarios
  - Validate against known failure modes
  - Cross-check results
- Rollback: Regenerate from static fallbacks

### Medium-Risk Operations (Standard Safeguards)

**1. Burnout Detection (BURNOUT_SENTINEL)**
- Risk: False positive alerts
- Safeguards:
  - Multi-tool consensus required for escalation
  - Document uncertainty levels
  - Human approval for interventions

**2. Background Job Management (CI_LIAISON)**
- Risk: Job monitoring failure
- Safeguards:
  - Timeout enforcement
  - Log rotation and archival
  - Automatic job cancellation on timeout

### Low-Risk Operations (Read-Only)

- Compliance auditing (COMPLIANCE_AUDITOR)
- Knowledge searching (KNOWLEDGE_CURATOR)
- Conflict detection (G3_OPERATIONS)
- Capacity analysis (CAPACITY_OPTIMIZER)

---

## Success Metrics

### Per-Agent Health Indicators

| Agent | Metric | Target | Alert |
|-------|--------|--------|-------|
| SCHEDULER | Tool response time | < 2s | > 5s |
| SWAP_MANAGER | Validation success | 98%+ | < 95% |
| COMPLIANCE_AUDITOR | Audit accuracy | 99.5%+ | < 99% |
| RESILIENCE_ENGINEER | N-1 sim time | < 15s | > 30s |
| BURNOUT_SENTINEL | Alert latency | < 60s | > 120s |
| EPIDEMIC_ANALYST | Model convergence | < 20 iter | > 100 iter |
| CAPACITY_OPTIMIZER | Calc time | < 5s | > 10s |
| KNOWLEDGE_CURATOR | Ingest success | 99%+ | < 95% |
| CI_LIAISON | Job tracking | 100% | Any gap |

### System-Level Health

- All 20 MCP agents healthy: > 95% uptime
- No MCP tool timeouts: < 0.1% timeout rate
- Compliance accuracy: > 99.5%
- Resilience testing: < 30s for N-1/N-2
- Knowledge base: > 1000 documented patterns

---

## Integration Points

### With Existing Systems

**FastAPI Backend:**
- All MCP agents call HTTP endpoints on `http://backend:8000/api/*`
- Requires docker-compose networking configured
- Health check: `GET /health` endpoint

**Database (PostgreSQL):**
- Direct queries via MCP database access
- Requires active database connection
- Backup/restore via MCP tools

**Redis:**
- Background task queue (Celery)
- Session/cache storage
- Required for async operations

**MCP Server:**
- 29+ scheduling and resilience tools
- Runs in Docker container
- Exposes tools via OpenAI specification

### Dependencies Between Agents

```
ORCHESTRATOR (command)
  ├─> ARCHITECT (system design)
  │   └─> COORD_ENGINE (scheduling)
  │       ├─> SCHEDULER (generation) [requires validate_schedule]
  │       ├─> SWAP_MANAGER (swaps) [requires execute_swap]
  │       └─> OPTIMIZATION_SPECIALIST (optimization) [requires generate_schedule]
  │
  └─> SYNTHESIZER (operations)
      ├─> COORD_RESILIENCE (resilience)
      │   ├─> COMPLIANCE_AUDITOR (compliance) [requires validate_schedule]
      │   ├─> SECURITY_AUDITOR (security) [requires validate_schedule]
      │   ├─> RESILIENCE_ENGINEER (resilience) [requires run_contingency]
      │   ├─> BURNOUT_SENTINEL (burnout) [requires calculate_burnout_rt]
      │   └─> EPIDEMIC_ANALYST (epidemic) [requires calculate_burnout_rt]
      │
      └─> COORD_OPS (operations)
          └─> CI_LIAISON (deployment) [requires background task tools]
```

---

## Conclusion

This G5 Planning Probe analyzed all 56 specialist agents plus 5 G-Staff advisors and determined:

1. **20 agents require MCP integration** (organized by criticality: P0 → P3)
2. **36 agents operate independently** (development, infrastructure, oversight)
3. **Clear deployment path** (4 phases, 1 week each)
4. **Comprehensive tool mapping** (29+ tools, organized into 6 groups)
5. **Risk mitigation strategies** for high-risk operations

**Recommendation:** Deploy in phases starting with P0 critical agents (scheduling, compliance, resilience), then progressively enable support systems. The 36 MCP-independent agents can operate in parallel without any scheduling system dependencies.

---

## Document Cross-References

### From MCP_ACCESS_ANALYSIS.md
- Full inventory of all 29+ MCP tools
- Detailed agent-by-agent requirements
- Complete deployment strategy
- Implementation checklist and monitoring

### From G5_PROBE_REMAINING_SPECIALISTS.md
- Priority-based deployment (P0, P1, P2, P3)
- Tool requirements by agent
- Risk assessment matrix
- Configuration checklist
- Success metrics

### From AGENT_MCP_MATRIX.md
- Quick reference table (all 61 agents)
- Dependency graph
- Tool group summary
- Quick decision tables

---

**END OF G5 PROBE INDEX**

*Master index for MCP access analysis. Use this document to navigate the three detailed analysis reports.*
