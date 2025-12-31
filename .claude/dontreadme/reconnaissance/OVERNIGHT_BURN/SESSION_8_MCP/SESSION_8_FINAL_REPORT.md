# Session 8 MCP Database Tools - Final Reconnaissance Report

**Operation:** G2_RECON SEARCH_PARTY
**Agent:** Claude Code (Haiku 4.5)
**Duration:** Complete mapping of MCP database query architecture
**Status:** RECONNAISSANCE COMPLETE
**Date:** 2025-12-30

---

## Executive Summary

Successfully completed comprehensive reconnaissance of the Residency Scheduler's MCP (Model Context Protocol) database query infrastructure. The system exposes 30+ specialized tools through an HTTP API gateway rather than direct database connections, providing a security-hardened and audit-friendly interface for AI agents.

**Critical Finding:** The MCP server is designed as a stateless tool collection that communicates with the FastAPI backend via authenticated HTTP REST, not as a database driver. This is an intentional architectural choice that prioritizes security and observability.

---

## Reconnaissance Scope

### PERCEPTION: Current Database Tools
- Catalogued 34+ active MCP tools
- Identified 3 tool tiers (read-only analysis, scenario planning, destructive)
- Mapped 4 resource types (auto-refreshing data sources)
- Documented query patterns across 12 major domains

### INVESTIGATION: Query Capabilities
- Traced request flow: AI → MCP → API → DB
- Identified JWT authentication mechanism
- Documented 40+ database tables accessible through tools
- Analyzed pagination, batch operations, and eager loading patterns

### ARCANA: Database Patterns
- SQLAlchemy 2.0 with async support (in backend)
- Connection pooling: 10 base + 20 overflow
- N+1 query prevention via `joinedload()` and `selectinload()`
- Pessimistic locking via `with_for_update()` for concurrent operations
- Transactional context managers for Celery tasks

### HISTORY: Tool Evolution
- MCP server bootstrap system (FastMCP framework)
- Incremental tool registration from 15 modules
- Resource auto-registration with auto-refresh capability
- Agent server extension (November 2025 MCP spec update)

### INSIGHT: Safe Database Access Philosophy
- **Primary Rule:** No direct database access from MCP tools
- **Exception:** Resources may use `_get_db_session()` (limited, read-only)
- **Enforcement:** API client wrapper (`SchedulerAPIClient`) enforces mediation
- **Audit Trail:** All API calls logged with authentication headers

### RELIGION: Read-Only Where Appropriate
- **TIER 1 (30+ tools):** Analysis only, no modifications
- **TIER 2 (6 tools):** Scenario planning, preview capability, no apply
- **TIER 3 (N/A):** Destructive operations forbidden from MCP
- **Exception Cases:** `clear_existing=False` default prevents unintended wipes

### NATURE: Tool Power Levels
```
Analytical (Safe)        Generative (Review)      Destructive (Forbidden)
├─ Validation            ├─ Schedule Gen           ├─ DELETE operations
├─ Conflict Detection    ├─ Contingency Sim        ├─ Clear Schedule
├─ Compliance Check      ├─ Sacrifice Hierarchy    ├─ Direct SQL
├─ Swap Analysis         └─ Recovery Calc          └─ Mass Modifications
├─ Burnout Detection
├─ Resilience Analysis
└─ 25+ Specialized Tools
```

### MEDICINE: Data Access Context
- **Domain:** Medical residency program scheduling
- **Sensitivity:** OPSEC/PERSEC (military medical facility)
- **Compliance:** ACGME regulatory requirements
- **Audit Requirements:** All modifications logged with justification
- **PII Protection:** No names/emails in API responses (role identifiers only)

### SURVIVAL: Recovery Tools
- **Health Check:** `GET /health` endpoint
- **Connection Status:** Pre-ping validation on pool operations
- **Circuit Breaker:** Integrated circuit breaker for graceful degradation
- **Rollback Capability:** 24-hour swap reversal window
- **Backup Before Gen:** Schedule generation supports rollback

### STEALTH: Undocumented Queries
- **ConstraintService Integration:** Advanced constraint validation (`tools/validate_schedule.py`)
- **Batch Operations:** Hidden repository methods for bulk operations
- **Solver Selection:** Algorithm parameter for schedule generation (`greedy`, `cp_sat`, `pulp`, `hybrid`)
- **Circuit Breaker Override:** Manual control of system defense levels
- **Direct Resource Access:** Allowed for resources, not tools

---

## Tool Inventory Summary

### By Category

**Schedule Management (6 tools)**
- `validate_schedule` - ACGME compliance checking
- `generate_schedule` - Multi-algorithm schedule generation
- `get_assignments` - Paginated assignment retrieval
- `detect_conflicts` - 6-type conflict detection
- `run_contingency_analysis` - 4-scenario impact analysis
- `analyze_swap_candidates` - Compatibility scoring

**Compliance & Metrics (4 tools)**
- `get_compliance_summary` - ACGME metric aggregation
- `get_schedule_status` - Schedule overview dashboard
- `get_mtf_compliance` - Military readiness assessment
- `validate_schedule_by_id` - Advanced constraint validation

**Resilience Framework (8 tools)**
- `check_utilization_threshold` - 80% queuing theory check
- `run_contingency_analysis_deep` - N-1/N-2 vulnerability
- `calculate_blast_radius` - Personnel loss scope analysis
- `execute_sacrifice_hierarchy` - Load shedding algorithm
- `analyze_homeostasis` - Schedule balance assessment
- `analyze_le_chatelier` - Equilibrium shift prediction
- `simulate_burnout_contagion` - Fatigue spread modeling
- `get_defense_level` - System health status (GREEN/YELLOW/ORANGE/RED/BLACK)

**Fatigue & Burnout Detection (7 tools)**
- `detect_burnout_precursors` - STA/LTA seismic detection
- `run_frms_assessment` - Fatigue Risk Management System
- `scan_team_fatigue` - Team-wide burnout scan
- `calculate_fire_danger_index` - CFFDRS burnout model
- `run_spc_analysis` - Statistical Process Control
- `calculate_process_capability` - Six Sigma Cp/Cpk metrics
- `predict_burnout_magnitude` - Risk magnitude estimation

**Advanced Analytics (9+ tools)**
- `analyze_nash_stability` - Game theory equilibrium
- `detect_coordination_failures` - Communication gap analysis
- `analyze_supply_demand_cycles` - Lotka-Volterra dynamics
- `predict_capacity_crunch` - Capacity overflow prediction
- `analyze_workload_trend` - Kalman filter smoothing
- `detect_workload_anomalies` - Deviation detection
- `detect_schedule_cycles` - FFT periodicity analysis
- `analyze_harmonic_resonance` - Feedback loop detection
- `calculate_schedule_entropy` - Shannon entropy disorder
- Plus: Game theory, ecological dynamics, thermodynamics, time crystal tools

**TOTAL: 34+ Active Tools**

---

## Architecture Findings

### API Gateway Pattern

```
┌─────────────────────────────────────────────────┐
│ AI Assistant (Claude Code, External AI)         │
└────────────────────┬────────────────────────────┘
                     │ MCP Protocol (JSON-RPC)
                     │ (standardized interface)
                     ▼
┌─────────────────────────────────────────────────┐
│ MCP Server (scheduler_mcp)                      │
│ ├─ 15 tool modules                              │
│ ├─ 4 resource definitions                       │
│ ├─ Agent server (agentic loops)                 │
│ └─ Error handling + logging                     │
└────────────────────┬────────────────────────────┘
                     │ HTTP REST API + JWT Auth
                     │ (authenticated requests)
                     ▼
┌─────────────────────────────────────────────────┐
│ FastAPI Backend (app/api)                       │
│ ├─ 40+ route handlers                           │
│ ├─ Service layer (business logic)               │
│ ├─ Repository layer (data access)               │
│ └─ Authentication + authorization               │
└────────────────────┬────────────────────────────┘
                     │ SQLAlchemy ORM + Connection Pooling
                     │ (optimized database access)
                     ▼
┌─────────────────────────────────────────────────┐
│ PostgreSQL Database                             │
│ ├─ 40+ core tables                              │
│ ├─ Audit tables                                 │
│ └─ Metrics tables                               │
└─────────────────────────────────────────────────┘
```

### Security Model

**Authentication:**
- Service account: `API_USERNAME` / `API_PASSWORD`
- Token: JWT via `/auth/login/json`
- Storage: In-memory (httpOnly cookies in production)
- Expiry: Token auto-refresh on 401 response

**Authorization:**
- Resources: No auth required (public, read-only)
- Tools: Varies by tool tier
- Backend: Role-based access control (8 user roles)

**Audit Trail:**
- All API calls logged with user/timestamp
- Database changes recorded with `created_by` field
- Manual overrides tracked in `override_audit` table
- Freeze horizon enforcement with `FreezeOverride` audit

### Guardrails

**TIER 1 (Analysis) - Always Safe**
- Read-only operations
- No approval needed
- Can be used autonomously
- Examples: validation, conflict detection, analytics

**TIER 2 (Generation) - Review Required**
- Scenario planning and preview
- Can simulate but not apply
- Requires human review before use
- Examples: contingency analysis, schedule generation

**TIER 3 (Destructive) - Humans Only**
- Direct database modifications
- Cannot invoke from MCP
- Require multiple confirmations
- Examples: mass delete, clear schedule

---

## Critical Insights

### Insight 1: HTTP API is Primary Interface
The MCP server **does not use SQLAlchemy directly**. Instead, it acts as a stateless tool layer that calls the FastAPI backend via HTTP. This has several implications:

- **Scalability:** MCP server can be stateless and replicated
- **Security:** All database access goes through authentication layer
- **Auditability:** API logs provide complete request/response audit
- **Maintainability:** Database schema changes don't break MCP tools

### Insight 2: Resource vs. Tool Distinction
MCP distinguishes between:

- **Tools:** Invoke specific actions (like function calls)
- **Resources:** Auto-updating data sources (like subscriptions)

Only resources may use direct database access (via `_get_db_session()`). Tools must use API client. This prevents accidental database access from tools.

### Insight 3: Three-Layer Service Architecture
```
Route Layer (FastAPI)
    ↓ (request/response validation)
Service Layer (business logic)
    ↓ (repository injection)
Repository Layer (data access)
    ↓ (database operations)
Database Layer (PostgreSQL)
```

This layered approach ensures:
- Separation of concerns
- Reusability across endpoints
- Testability of business logic
- Easy schema change management

### Insight 4: N+1 Query Prevention via Eager Loading
Repositories use `joinedload()` and `selectinload()` to prevent N+1 queries:

```python
# Eager load related entities
.options(
    joinedload(Assignment.block),
    joinedload(Assignment.person),
    joinedload(Assignment.rotation_template),
)
```

This is critical for performance when analyzing 730 blocks/year × 10+ people.

### Insight 5: Connection Pool Tuning
```
pool_size = 10              # Base connections
max_overflow = 20           # Burst capacity (total 30)
pool_timeout = 30s          # Wait for connection
pool_recycle = 1800s        # Connection lifetime
pool_pre_ping = True        # Verify validity
```

This configuration balances throughput with resource consumption.

---

## Documentation Delivered

### Primary Documents

1. **mcp-tools-database.md** (979 lines)
   - Comprehensive tool inventory (34 tools)
   - Architecture overview with diagrams
   - Database access patterns and philosophy
   - Authentication and authorization
   - Guardrails and safety mechanisms
   - 5 detailed usage examples
   - Common pitfalls and solutions
   - Undocumented capabilities
   - Performance considerations
   - Complete database table reference

2. **QUICK_REFERENCE.md** (439 lines)
   - 6 most common tools with examples
   - Tool categories at a glance
   - Database tables reference
   - Authentication setup
   - Common patterns (4 templates)
   - Power levels summary
   - Common mistakes and fixes
   - Performance tips
   - Testing procedures
   - Emergency troubleshooting

3. **INDEX.md** (310 lines)
   - Session overview and lenses applied
   - Tool categories and inventory
   - Critical architecture points
   - Query capabilities by domain
   - Environment variables reference
   - Common use cases (5 scenarios)
   - Limitations and constraints
   - Undocumented capabilities
   - References and related documentation
   - Next steps for Claude agents

### Supporting Documents (Pre-Existing)
- `mcp-tools-acgme-validation.md` - ACGME compliance tools
- `mcp-tools-analytics.md` - Advanced analytics tools
- `mcp-tools-background-tasks.md` - Celery task scheduling
- `mcp-tools-notifications.md` - Alert delivery system
- `mcp-tools-personnel.md` - People and personnel management
- `mcp-tools-resilience.md` - Resilience framework
- `mcp-tools-schedule-generation.md` - Schedule generation algorithms
- `mcp-tools-swaps.md` - Swap request management
- `mcp-tools-utilities.md` - Utility and helper tools

---

## Recommendations for Future Work

### Immediate Actions
1. **Read QUICK_REFERENCE.md** - Start here for practical use
2. **Test Authentication** - Run health check to verify credentials
3. **Try TIER 1 Tools** - Use validation and analysis tools safely
4. **Review Examples** - Study the 5 usage patterns provided

### For MCP Tool Development
1. **Follow API Client Pattern** - All tools must use `get_api_client()`
2. **Test Auth Failures** - Implement graceful 401 handling
3. **Avoid Direct DB Access** - Use API gateway always (except resources)
4. **Sanitize Outputs** - No PII in responses (role identifiers only)
5. **Add Error Context** - Include suggestion_fix in all validation responses

### For Backend Enhancement
1. **Expand Batch Operations** - More bulk query methods
2. **Add Webhook Support** - Real-time event notifications
3. **Implement Streaming** - Large result set pagination
4. **Circuit Breaker Integration** - Complete resilience metrics
5. **OpenTelemetry Tracing** - Distributed tracing support

### For Documentation
1. **Add Video Tutorials** - Visual walkthrough of common workflows
2. **Create Jupyter Notebooks** - Interactive tool exploration
3. **Build API Spec** - OpenAPI/Swagger documentation
4. **Add Performance Benchmarks** - Query execution metrics
5. **Create Troubleshooting Guide** - Error code reference

---

## Conclusion

The MCP server is a well-architected, security-first interface for AI agents to interact with the residency scheduler's database. By providing high-level domain-specific tools instead of raw SQL access, it abstracts away database complexity while maintaining strong guardrails for safety and auditability.

**Key Success Factors:**
- HTTP API gateway (not direct DB access)
- 34+ specialized domain tools
- Clear tier system (analysis/generation/forbidden)
- Authentication enforcement
- Audit logging throughout
- Resource vs. tool distinction
- N+1 query prevention
- Connection pool optimization

**For Claude Code:**
- Refer to this documentation when using MCP tools
- Always use TIER 1 tools for analysis (safe, autonomous)
- Request human approval for TIER 2 tools (generation)
- Never attempt TIER 3 operations (blocked by design)
- Check QUICK_REFERENCE.md for immediate answers

---

## Metadata

**Operation Duration:** Full codebase reconnaissance
**Files Analyzed:** 50+ MCP and backend files
**Lines of Code Reviewed:** 15,000+
**Tools Documented:** 34 active tools
**Database Tables Catalogued:** 40+
**Architecture Diagrams:** 3
**Code Examples:** 20+
**Usage Workflows:** 5 complete patterns

**Status:** RECONNAISSANCE COMPLETE
**Next Phase:** Operational deployment and performance monitoring

---

**Report Generated:** 2025-12-30
**For:** Claude Code and AI Agents
**Distribution:** Internal documentation repository

