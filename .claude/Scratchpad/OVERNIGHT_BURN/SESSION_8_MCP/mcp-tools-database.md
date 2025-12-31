# MCP Database Query Tools - Comprehensive Documentation

**Status:** Session 8 Reconnaissance Complete
**Date:** 2025-12-30
**Context:** G2_RECON conducting SEARCH_PARTY on MCP database tools
**Lenses Applied:** PERCEPTION, INVESTIGATION, ARCANA, HISTORY, INSIGHT, NATURE, SURVIVAL

---

## Executive Summary

The Residency Scheduler's MCP server provides **database query access through HTTP API** rather than direct database connections. This architectural choice enforces security boundaries, ensures proper authentication, and maintains audit trails for all data access.

**Key Insight:** The MCP server communicates with the FastAPI backend via REST API using JWT authentication, not raw SQL or ORM connections. This is the intentional design pattern.

---

## Architecture Overview

### PERCEPTION: Current Database Access Patterns

```
┌──────────────────────────────────┐
│   AI Assistant (via MCP Client)  │
└──────────────┬───────────────────┘
               │ MCP Protocol (JSON-RPC)
               ▼
┌──────────────────────────────────┐
│   MCP Server (scheduler_mcp)      │  ← Stateless tools
│   - Tools (30+ implementations)   │
│   - Resources (schedule, compliance)
│   - Agent server (agentic loops)  │
└──────────────┬───────────────────┘
               │ HTTP REST API
               │ JWT Authentication
               ▼
┌──────────────────────────────────┐
│   FastAPI Backend (app/api)       │  ← Database gateway
│   - Controllers (request handling)│
│   - Services (business logic)     │
│   - Repositories (data access)    │
└──────────────┬───────────────────┘
               │ SQLAlchemy ORM
               │ Connection Pooling
               ▼
┌──────────────────────────────────┐
│   PostgreSQL Database             │
│   - Assignments, Blocks, People   │
│   - Conflicts, Swaps, Credentials │
│   - Audit trails, Schedule runs   │
└──────────────────────────────────┘
```

### INVESTIGATION: Query Flow

1. **Tool invocation** (e.g., `validate_schedule`)
2. **API Client initialization** (creates JWT token via `/auth/login/json`)
3. **HTTP request** to FastAPI endpoint with auth headers
4. **Backend validation** and database query execution
5. **JSON response** returned to MCP tool
6. **Response transformation** (if needed) for MCP format
7. **Return to AI assistant** via MCP protocol

---

## Tool Inventory

### Category 1: Direct API-Based Tools (via SchedulerAPIClient)

These tools make HTTP requests to the FastAPI backend.

#### Schedule Management Tools

**Tool: `validate_schedule`**
- **Location:** `scheduler_mcp/scheduling_tools.py`
- **API Endpoint:** `GET /api/v1/schedule/validate`
- **Access Level:** Public (no auth required)
- **Returns:** `ScheduleValidationResult`
- **Database Tables Queried:**
  - `assignment` (join with `block`, `person`, `rotation_template`)
  - `block`
  - `person`
- **Query Type:** Read-only analytical
- **Safety:** Validates via ACGME rules (80-hour rule, 1-in-7 rule, supervision ratios)

```python
# Tool invocation example
result = await validate_schedule(
    request=ScheduleValidationRequest(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        check_work_hours=True,
        check_supervision=True,
    )
)
# Returns: ScheduleValidationResult with violations list
```

**Tool: `generate_schedule`**
- **Location:** `api_client.py`
- **API Endpoint:** `POST /api/v1/schedule/generate`
- **Access Level:** Requires authentication
- **Returns:** `dict[str, Any]`
- **Parameters:** start_date, end_date, algorithm, timeout_seconds, clear_existing
- **Database Impact:** WRITE (creates new assignments, optionally deletes existing)
- **Safety:** Solver timeout, clear_existing flag for safety

**Tool: `get_assignments`**
- **Location:** `api_client.py`
- **API Endpoint:** `GET /api/v1/assignments`
- **Access Level:** Requires authentication
- **Parameters:** start_date, end_date, limit (default 100)
- **Returns:** Paginated assignment list
- **Database Tables:** assignment, block, person, rotation_template

**Tool: `run_contingency_analysis`**
- **Location:** `scheduling_tools.py`
- **API Endpoint:** `GET /api/v1/resilience/vulnerability`
- **Access Level:** Requires authentication
- **Returns:** `ContingencyAnalysisResult` with impact assessment
- **Analysis Type:** Scenario planning (faculty absence, mass absence, emergency coverage)
- **Database Scope:** Full schedule analysis with N-1/N-2 vulnerability detection

#### Swap Management Tools

**Tool: `get_swap_candidates`**
- **Location:** `api_client.py`
- **API Endpoint:** `POST /api/v1/schedule/swaps/candidates`
- **Access Level:** Requires authentication
- **Parameters:** person_id, assignment_id, block_id, max_candidates
- **Returns:** Ranked list of compatible swap candidates
- **Query Logic:** Finds people with compatible rotations in preferred date range
- **Ranking:** match_score (0.0-1.0) based on compatibility factors

**Tool: `analyze_swap_candidates`**
- **Location:** `scheduling_tools.py`
- **API Endpoint:** Calls `get_swap_candidates` via API client
- **Returns:** `SwapAnalysisResult` with detailed candidate analysis
- **Safety:** Includes mutual benefit score and approval likelihood

#### Conflict Detection Tools

**Tool: `detect_conflicts`**
- **Location:** `scheduling_tools.py`
- **Conflict Types:** double_booking, work_hour_violation, rest_period_violation, supervision_gap, leave_overlap, credential_mismatch
- **Parameters:** start_date, end_date, conflict_types (optional), include_auto_resolution
- **Returns:** `ConflictDetectionResult` with list of `ConflictInfo`
- **Database Scope:** Full schedule analysis with variant checking

#### Compliance and Metrics Tools

**Tool: `get_compliance_summary`** (Resource)
- **Location:** `resources.py`
- **Type:** MCP Resource (auto-refreshing, subscribable)
- **Queries:** Direct database access via `_get_db_session()`
- **Returns:** `ComplianceSummaryResource` with:
  - ACGME metrics (work hours, consecutive duty, supervision)
  - Violation list (critical/warning)
  - Recommendations
- **Database Tables:** assignment, block, person
- **Calculation:** Rolling 4-week windows, 80-hour rule, 1-in-7 rule

**Tool: `get_schedule_status`** (Resource)
- **Location:** `resources.py`
- **Type:** MCP Resource
- **Returns:** `ScheduleStatusResource` with:
  - Total assignments
  - Active conflicts
  - Pending swaps
  - Coverage metrics
- **Coverage Metrics:** faculty per day, residents per day, understaffed days
- **Last Generated:** Schedule algorithm and timestamp

**Tool: `get_mtf_compliance`**
- **Location:** `api_client.py`
- **API Endpoint:** `GET /api/v1/resilience/mtf-compliance`
- **Returns:** Military Medical Facility compliance status
- **Components:**
  - DRRS readiness rating (C1-C5)
  - Mission capability (FMC/PMC/NMC)
  - Personnel rating (P1-P4)
  - Capability rating (S1-S4)
  - Circuit breaker status
  - Iron Dome status

### Category 2: Resilience & Analysis Tools

These tools analyze system resilience and schedule stability.

#### Resilience Framework Tools

**Tool: `check_utilization_threshold`**
- **Location:** `resilience_integration.py`
- **Analysis:** Checks 80% utilization threshold (queuing theory)
- **Returns:** `UtilizationResponse`
- **Safety Philosophy:** Green/yellow/orange/red/black defense levels

**Tool: `run_contingency_analysis_deep`**
- **Location:** `resilience_integration.py`
- **Advanced Analysis:** N-1/N-2 contingency scenarios
- **Returns:** `ResilienceContingencyResponse`
- **Scope:** Full coverage gap analysis, workload rebalancing impact

**Tool: `calculate_blast_radius`**
- **Location:** `resilience_integration.py`
- **Analysis:** Scope of impact from personnel loss (AWS blast radius isolation)
- **Parameters:** affected_person_ids, start_date, end_date
- **Returns:** `BlastRadiusAnalysisResponse`

**Tool: `execute_sacrifice_hierarchy`**
- **Location:** `resilience_integration.py`
- **Algorithm:** Triage-based load shedding (lowest priority rotations shed first)
- **Returns:** `SacrificeHierarchyResponse`
- **Safety:** Maintains critical coverage, preserves ACGME compliance

#### Time Crystal & Anti-Churn Tools

**Tool: `get_time_crystal_health`**
- **Location:** `time_crystal_tools.py`
- **Analysis:** Schedule stability measurement (rigidity score 0.0-1.0)
- **Returns:** `TimeCrystalHealthResponse`
- **Concept:** Prevent churn by detecting natural cycles (7d, 14d, 28d ACGME windows)

**Tool: `analyze_schedule_rigidity`**
- **Location:** `time_crystal_tools.py`
- **Measurement:** How stable schedule changes are
- **Returns:** `RigidityAnalysisResponse`
- **Use Case:** Detect when small tweaks cause cascade failures

#### Early Warning & Burnout Detection Tools

**Tool: `detect_burnout_precursors`**
- **Location:** `early_warning_integration.py`
- **Algorithm:** STA/LTA seismic detection applied to fatigue signals
- **Returns:** `PrecursorDetectionResponse`
- **Signal Types:** work_hour_creep, night_float_accumulation, consecutive_duty_stretch

**Tool: `run_spc_analysis`**
- **Location:** `early_warning_integration.py`
- **Algorithm:** Statistical Process Control (Western Electric rules)
- **Returns:** `SPCAnalysisResponse`
- **Metrics:** Process capability (Cp, Cpk), out-of-control signals

**Tool: `calculate_fire_danger_index`**
- **Location:** `early_warning_integration.py`
- **Model:** CFFDRS (Canadian Forest Fire Danger Rating System) applied to burnout
- **Returns:** `FireDangerResponse`
- **Components:** Initial Spread Index, Build-up Index, Danger Class

#### Fatigue Risk Management (FRMS)

**Tool: `run_frms_assessment`**
- **Location:** `frms_integration.py`
- **Algorithm:** Chronobiology-based fatigue risk assessment
- **Returns:** `FRMSAssessmentResponse`
- **Components:** Sleep debt analysis, schedule fatigue risk, hazard evaluation
- **Database Scope:** Assignment history, work hour patterns, rest periods

**Tool: `scan_team_fatigue`**
- **Location:** `frms_integration.py`
- **Scope:** Entire team burnout scan
- **Returns:** `TeamFatigueScanResponse`
- **Output:** Per-resident fatigue scores, aggregate team risk

#### Entropy & Thermodynamics Tools

**Tool: `calculate_schedule_entropy`**
- **Location:** `thermodynamics_tools.py`
- **Concept:** Disorder measurement (Shannon entropy)
- **Returns:** `ScheduleEntropyResponse`
- **Interpretation:** High entropy = unpredictable/unstable schedule

**Tool: `optimize_free_energy`**
- **Location:** `thermodynamics_tools.py`
- **Model:** Friston's Free Energy Principle from neuroscience
- **Analysis:** Minimize forecast errors through schedule optimization
- **Returns:** `FreeEnergyOptimizationResponse`

### Category 3: Advanced Analytics Tools

#### Game Theory Tools

**Tool: `analyze_nash_stability`**
- **Location:** `tools/game_theory_tools.py`
- **Analysis:** Equilibrium detection in swap decisions
- **Returns:** `NashStabilityResponse`
- **Use Case:** Ensure swap system reaches stable equilibrium

**Tool: `detect_coordination_failures`**
- **Location:** `tools/game_theory_tools.py`
- **Analysis:** Find communication gaps between teams
- **Returns:** `CoordinationFailuresResponse`

#### Ecological Dynamics Tools

**Tool: `analyze_supply_demand_cycles`**
- **Location:** `tools/ecological_dynamics_tools.py`
- **Model:** Lotka-Volterra predator-prey dynamics
- **Analysis:** Faculty supply vs. resident demand cycles
- **Returns:** `SupplyDemandCyclesResponse`

**Tool: `predict_capacity_crunch`**
- **Location:** `tools/ecological_dynamics_tools.py`
- **Prediction:** When system will exceed capacity
- **Returns:** `CapacityCrunchResponse`

#### Kalman Filtering Tools

**Tool: `analyze_workload_trend`**
- **Location:** `tools/kalman_filter_tools.py`
- **Algorithm:** Kalman filter for state estimation
- **Returns:** `WorkloadTrendResponse`
- **Smoothing:** Removes noise from workload data

**Tool: `detect_workload_anomalies`**
- **Location:** `tools/kalman_filter_tools.py`
- **Detection:** Sudden deviations from expected trend
- **Returns:** `WorkloadAnomalyResponse`

#### Fourier Analysis Tools

**Tool: `detect_schedule_cycles`**
- **Location:** `tools/fourier_analysis_tools.py`
- **Algorithm:** FFT for periodicity detection
- **Returns:** `ScheduleCyclesResponse`
- **Discovery:** 7-day, 14-day, 28-day patterns

**Tool: `analyze_harmonic_resonance`**
- **Location:** `tools/fourier_analysis_tools.py`
- **Analysis:** Feedback loops in schedule iterations
- **Returns:** `HarmonicResonanceResponse`

### Category 4: Validation & Constraint Tools

**Tool: `validate_schedule_by_id`** (ConstraintService Integration)
- **Location:** `tools/validate_schedule.py`
- **Advanced:** Direct constraint evaluation
- **Returns:** `ConstraintValidationResponse`
- **Scope:** Hard constraints, soft constraints, penalty scoring

---

## Database Access Philosophy

### ARCANA: SQLAlchemy 2.0 Patterns

The backend uses modern SQLAlchemy patterns:

```python
# GOOD: Eager loading to prevent N+1 queries
from sqlalchemy.orm import joinedload, selectinload

assignments = (
    db.query(Assignment)
    .options(
        joinedload(Assignment.block),
        joinedload(Assignment.person),
        joinedload(Assignment.rotation_template),
    )
    .filter(...)
    .all()
)

# GOOD: Type-safe selects with select() syntax
from sqlalchemy import select

result = await db.execute(
    select(Person).where(Person.is_resident == True)
)
residents = result.scalars().all()

# GOOD: Connection pooling with pre-ping
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connection validity
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,  # Prevent stale connections
)

# GOOD: Async/await patterns for background tasks
async def async_task():
    with task_session_scope() as session:
        # Database work
        assignments = session.query(Assignment).all()

# GOOD: Read-only repositories for data access
class AssignmentRepository(BaseRepository[Assignment]):
    def get_by_block_and_person(self, block_id, person_id):
        return (
            self.db.query(Assignment)
            .filter(
                Assignment.block_id == block_id,
                Assignment.person_id == person_id,
            )
            .first()
        )
```

### INSIGHT: Safe Database Access for MCP Tools

**Rule 1: No Direct Database Access from MCP**
```python
# WRONG: Direct database access in MCP tool
from app.db.session import SessionLocal

async def bad_tool():
    db = SessionLocal()  # ❌ Bypasses API layer
    assignments = db.query(Assignment).all()
    db.close()
    return assignments

# RIGHT: Use API client
async def good_tool():
    client = await get_api_client()  # ✓ Authenticated HTTP
    result = await client.get_assignments()
    return result
```

**Rule 2: API-Mediated Data Access**
```python
# MCP Tool Architecture
from .api_client import get_api_client

async def validate_schedule(request):
    """All database access goes through FastAPI backend."""
    client = await get_api_client()

    # 1. Authenticate with JWT
    headers = await client._ensure_authenticated()

    # 2. Make HTTP request to backend
    result = await client.validate_schedule(
        start_date=request.start_date.isoformat(),
        end_date=request.end_date.isoformat(),
    )

    # 3. Transform response for MCP format
    return ScheduleValidationResult(**result)
```

**Rule 3: Resource-Based Direct Access (Limited)**

Only MCP Resources may access database directly via `_get_db_session()`:
```python
# MCP Resource (read-only, auto-refreshing)
async def get_schedule_status(start_date=None, end_date=None):
    """MCP Resources can use direct DB access for performance."""
    db = _get_db_session()  # ✓ Allowed for resources only
    try:
        assignments = db.query(Assignment).all()
        # ... analysis
    finally:
        db.close()
```

---

## Authentication & Authorization

### API Client Authentication

The MCP server authenticates with the backend using credentials from environment variables:

**Required Environment Variables:**
```bash
API_BASE_URL=http://backend:8000          # Backend URL
API_USERNAME=mcp-user                      # Service account username
API_PASSWORD=<secure-password>             # Service account password
DATABASE_URL=postgresql://...              # For resources only
```

**Authentication Flow:**
```python
class SchedulerAPIClient:
    async def _login(self) -> None:
        """Authenticate and get JWT token."""
        response = await self.client.post(
            f"{self.config.api_prefix}/auth/login/json",
            json={
                "username": self.config.username,
                "password": self.config.password,
            },
        )
        self._token = response.json()["access_token"]

    async def _ensure_authenticated(self) -> dict[str, str]:
        """Return auth headers with current token."""
        if self._token is None:
            await self._login()
        return {"Authorization": f"Bearer {self._token}"}
```

### Access Levels

| Tool Category | Auth Required | Audit Logged | Risk Level |
|---------------|---------------|--------------|-----------|
| Read-only validation | No | No | LOW |
| Swap candidates | Yes | Yes | MEDIUM |
| Schedule generation | Yes | Yes | HIGH |
| Contingency analysis | Yes | Yes | MEDIUM |
| MTF compliance | Yes | No | LOW |
| Conflict detection | Yes | Yes | MEDIUM |

---

## Guardrails & Safety Mechanisms

### RELIGION: Read-Only Where Appropriate

**Read-Only Resources (Safe for AI):**
- `get_schedule_status` - Schedule analysis
- `get_compliance_summary` - Compliance metrics
- `validate_schedule` - Validation only (no write)
- `detect_conflicts` - Detection only (no resolution)
- `detect_burnout_precursors` - Analysis only
- `run_spc_analysis` - Statistical analysis
- Resilience analysis tools

**Write Operations (Require Approval):**
- `generate_schedule` - Creates assignments
- `execute_swap` - Modifies assignments
- `clear_existing` parameter in schedule gen
- Any tool that calls `DELETE` or `INSERT`

### NATURE: Tool Power Levels

```
┌─────────────────────────────────────┐
│ TIER 1: Analytical (Safe)           │
├─────────────────────────────────────┤
│ - validate_schedule                 │
│ - detect_conflicts                  │
│ - get_compliance_summary            │
│ - detect_burnout_precursors         │
│ - get_schedule_status               │
│ - analyze_swap_candidates           │
│ - run_spc_analysis                  │
│ - calculate_schedule_entropy        │
│ - (30+ analysis tools)              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ TIER 2: Generative (Review needed)  │
├─────────────────────────────────────┤
│ - generate_schedule                 │
│ - run_contingency_analysis          │
│ - execute_sacrifice_hierarchy       │
│ - simulate_burnout_contagion        │
│ - calculate_recovery_distance       │
│ - (agent server autonomous loops)   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ TIER 3: Destructive (Human-only)    │
├─────────────────────────────────────┤
│ - Direct database modifications     │
│ - Clear schedule (without backup)   │
│ - Mass delete operations            │
│ - Direct SQL execution              │
└─────────────────────────────────────┘
```

### SURVIVAL: Error Handling & Recovery

**Safe Error Handling in MCP Tools:**
```python
async def safe_tool(request):
    """Proper error handling pattern."""
    try:
        client = await get_api_client()
        result = await client.some_operation(...)
        return result
    except ValueError as e:
        # Input validation error
        logger.warning(f"Invalid request: {e}")
        raise ValueError(f"Invalid parameters: {e}") from e
    except httpx.HTTPError as e:
        # Backend API error
        logger.error(f"Backend API failed: {e}")
        raise RuntimeError(f"Backend unavailable: {e}") from e
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise RuntimeError(f"Tool execution failed: {e}") from e
```

**Connection Health Monitoring:**
```python
async def health_check() -> bool:
    """Check backend availability."""
    client = await get_api_client()
    return await client.health_check()  # GET /health
```

---

## Usage Examples

### Example 1: Schedule Validation Workflow

```python
from scheduler_mcp.scheduling_tools import (
    validate_schedule,
    ScheduleValidationRequest,
)
from datetime import date

# Validate a specific date range
request = ScheduleValidationRequest(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31),
    check_work_hours=True,
    check_supervision=True,
    check_rest_periods=True,
    check_consecutive_duty=True,
)

result = await validate_schedule(request)

# Inspect results
print(f"Compliance Rate: {result.overall_compliance_rate}")
print(f"Critical Issues: {result.critical_issues}")
for issue in result.issues:
    if issue.severity == ValidationSeverity.CRITICAL:
        print(f"  - {issue.message}")
```

### Example 2: Swap Analysis

```python
from scheduler_mcp.scheduling_tools import (
    analyze_swap_candidates,
    SwapCandidateRequest,
)
from datetime import date

# Find swap candidates for a resident
request = SwapCandidateRequest(
    requester_person_id="PGY2-001",
    assignment_id="assign-123",
    preferred_date_range=(date(2025, 1, 15), date(2025, 1, 20)),
    max_candidates=10,
)

result = await analyze_swap_candidates(request)

# View top candidate
if result.candidates:
    top = result.candidates[0]
    print(f"Match Score: {top.match_score}")
    print(f"Compatibility: {top.compatibility_factors}")
    print(f"Approval Likelihood: {top.approval_likelihood}")
```

### Example 3: Contingency Planning

```python
from scheduler_mcp.scheduling_tools import (
    run_contingency_analysis,
    ContingencyRequest,
    ContingencyScenario,
)
from datetime import date

# Simulate faculty absence scenario
request = ContingencyRequest(
    scenario=ContingencyScenario.FACULTY_ABSENCE,
    affected_person_ids=["FAC-001", "FAC-002"],
    start_date=date(2025, 2, 1),
    end_date=date(2025, 2, 7),
    auto_resolve=False,  # Don't auto-apply solutions
)

result = await run_contingency_analysis(request)

# Review impact
impact = result.impact
print(f"Coverage Gaps: {impact.coverage_gaps}")
print(f"Compliance Violations: {impact.compliance_violations}")
print(f"Workload Increase: {impact.workload_increase_percent}%")

# Review solutions
for option in result.resolution_options:
    print(f"\nOption {option.option_id}: {option.strategy}")
    print(f"  Success Probability: {option.success_probability}")
    print(f"  Effort: {option.estimated_effort}")
```

### Example 4: Resilience Analysis

```python
from scheduler_mcp.resilience_integration import (
    run_contingency_analysis_deep,
    ResilienceContingencyRequest,
)
from datetime import date

# Deep N-1/N-2 analysis
request = ResilienceContingencyRequest(
    scenario="resident_absence",
    affected_ids=["PGY1-001"],
    start_date=date(2025, 2, 1),
    end_date=date(2025, 2, 7),
)

result = await run_contingency_analysis_deep(request)

# Check resilience metrics
print(f"N-1 Vulnerability: {result.n_minus_1_coverage_gap}")
print(f"N-2 Vulnerability: {result.n_minus_2_coverage_gap}")
print(f"Recovery Feasibility: {result.recovery_feasibility_score}")
```

### Example 5: Burnout Detection

```python
from scheduler_mcp.early_warning_integration import (
    detect_burnout_precursors,
    PrecursorDetectionRequest,
    PrecursorSignalType,
)
from datetime import date

# Scan for burnout precursors
request = PrecursorDetectionRequest(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 31),
    signal_types=[
        PrecursorSignalType.WORK_HOUR_CREEP,
        PrecursorSignalType.NIGHT_FLOAT_ACCUMULATION,
    ],
    sensitivity="medium",
)

result = await detect_burnout_precursors(request)

# Review precursor signals
for signal in result.signals:
    print(f"{signal.type}: {signal.magnitude} (confidence: {signal.confidence})")
```

---

## Common Pitfalls & How to Avoid Them

### Pitfall 1: Bypassing the API Client

**Wrong:**
```python
from app.db.session import SessionLocal
from app.models.assignment import Assignment

async def bad_mcp_tool():
    # ❌ Direct database access - no auth, no audit, no API control
    db = SessionLocal()
    assignments = db.query(Assignment).limit(100).all()
    db.close()
    return assignments
```

**Right:**
```python
from .api_client import get_api_client

async def good_mcp_tool():
    # ✓ Authenticated API access
    client = await get_api_client()
    result = await client.get_assignments(limit=100)
    return result
```

### Pitfall 2: Ignoring Authentication Failures

**Wrong:**
```python
async def tool_without_retry():
    client = await get_api_client()
    # If token expires, this will fail silently
    result = await client.some_operation()
    return result
```

**Right:**
```python
async def tool_with_retry():
    try:
        client = await get_api_client()
        result = await client.some_operation()
        return result
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            # Token expired, re-authenticate
            client._token = None
            result = await client.some_operation()
            return result
        raise
```

### Pitfall 3: N+1 Query Problems in Resources

**Wrong:**
```python
async def inefficient_resource():
    db = _get_db_session()
    assignments = db.query(Assignment).all()
    # This triggers N queries when accessing assignment.person
    for a in assignments:
        print(a.person.name)  # ❌ N queries
    db.close()
```

**Right:**
```python
async def efficient_resource():
    db = _get_db_session()
    assignments = (
        db.query(Assignment)
        .options(joinedload(Assignment.person))  # ✓ Single query batch
        .all()
    )
    for a in assignments:
        print(a.person.name)
    db.close()
```

### Pitfall 4: Returning Sensitive Data

**Wrong:**
```python
async def unsafe_tool():
    client = await get_api_client()
    people = await client.get_people()
    # ❌ Returns full names, emails, PII
    return people
```

**Right:**
```python
async def safe_tool():
    client = await get_api_client()
    people = await client.get_people()

    # ✓ Filter to role-based identifiers only
    sanitized = [
        {
            "person_id": p["id"],
            "person_role": f"PGY-{p['pgy_level']}" if p.get("is_resident") else "Faculty",
        }
        for p in people
    ]
    return sanitized
```

---

## Undocumented Query Patterns

### STEALTH: Hidden Query Capabilities

**The ConstraintService Integration:**
Located in `tools/validate_schedule.py`, this provides **advanced constraint evaluation** beyond standard validation:

```python
from .tools.validate_schedule import validate_schedule_by_id

# Direct constraint validation (lower-level than API)
result = await validate_schedule_by_id(
    schedule_id="sched-123",
    constraint_config=ConstraintConfig(
        hard_constraints=["work_hour_limit", "supervision_ratio"],
        soft_constraints=["workload_balance"],
    ),
)
```

**Batch Operations:**
The assignment repository supports batch operations not exposed through standard APIs:

```python
# Behind the scenes: bulk operations
assignment_repo.delete_by_block_ids(block_ids)  # Batch delete
assignment_repo.get_by_block_ids(block_ids)    # Batch get
```

**Direct Schedule Generation Internals:**
The `generate_schedule` tool accepts algorithm selection:

```python
result = await client.generate_schedule(
    start_date=...,
    end_date=...,
    algorithm="greedy",        # Fast, simple
    # algorithm="cp_sat",      # Google OR-Tools constraint solver
    # algorithm="pulp",        # Open-source LP solver
    # algorithm="hybrid",      # Combination approach
    timeout_seconds=120,       # Custom timeout (5-300s)
)
```

**Circuit Breaker Health:**
Direct circuit breaker inspection:

```python
from .circuit_breaker_tools import check_circuit_breakers

status = await check_circuit_breakers()
# Returns: circuit breaker states, health checks, override options
```

---

## Performance Considerations

### Query Optimization

**Connection Pooling:**
- Pool size: 10 (configurable via `DB_POOL_SIZE`)
- Max overflow: 20 (burst connections)
- Pre-ping: True (verify connection validity)
- Recycle: 1800s (prevent stale connections)

**Pagination:**
All list endpoints support pagination:
```python
# Default: page 1, page_size 100
# Max page_size: 500
result = await client.get_assignments(limit=100)  # API returns paginated
```

**Batch Operations:**
For large data sets, use batch endpoints when available:
```python
# Better than looping over individual queries
result = await client.get_assignments(start_date=..., end_date=..., limit=500)
```

---

## Database Tables Accessed

**Core Scheduling Tables:**
- `assignment` - Person assignments to blocks
- `block` - Half-day scheduling blocks
- `person` - Residents and faculty
- `rotation_template` - Rotation definitions

**Conflict & Compliance Tables:**
- `conflict_alert` - Detected scheduling conflicts
- `swap_record` - Swap request history
- `schedule_run` - Schedule generation metadata
- `absence` - Leave and absence records

**Credential & Compliance Tables:**
- `credential` - Faculty certifications
- `certification` - Training records
- `override_audit` - Manual overrides to rules
- `audit_log` - All data modifications

**Resilience Tables:**
- `circuit_breaker_state` - Health check status
- `utilization_metric` - Workload measurements
- `defense_level` - System defense state (GREEN/YELLOW/ORANGE/RED/BLACK)
- `contingency_analysis` - Scenario planning results

---

## Conclusion

The MCP database query architecture prioritizes:

1. **Security**: All database access mediated through authenticated API
2. **Auditability**: All queries logged and traceable
3. **Safety**: Clear separation between read-only and write operations
4. **Performance**: Connection pooling, eager loading, pagination
5. **Resilience**: Error handling, retry logic, health checks

**Key Takeaway:** AI agents should use the API client for all data access, not direct database connections. The 30+ analysis tools provide comprehensive coverage of scheduling, compliance, and resilience domains without requiring raw SQL or ORM knowledge.

