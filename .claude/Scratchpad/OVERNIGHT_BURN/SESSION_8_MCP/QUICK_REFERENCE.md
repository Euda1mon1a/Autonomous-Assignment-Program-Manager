# MCP Database Tools - Quick Reference Guide

**Last Updated:** 2025-12-30
**For:** Claude Code and AI Agents
**Purpose:** Fast lookup of MCP database capabilities

---

## The Big Picture in 30 Seconds

```
You (AI Agent)
     ↓
MCP Server (34+ specialized tools)
     ↓ (Always via HTTP API + JWT auth)
FastAPI Backend
     ↓
PostgreSQL Database

Rules:
✓ Use the API client (get_api_client)
✗ Never access DB directly from MCP
✓ Tier 1 tools (analysis) - Always safe
⚠ Tier 2 tools (generation) - Need review
✗ Tier 3 tools (destructive) - Humans only
```

---

## Most Common Tools

### 1. Validate Schedule (Read-Only)
```python
from scheduler_mcp.scheduling_tools import validate_schedule, ScheduleValidationRequest
from datetime import date

result = await validate_schedule(
    request=ScheduleValidationRequest(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        check_work_hours=True,
        check_supervision=True,
    )
)
# Returns: Compliance rate, violations list, recommendations
# TIER: 1 (Safe)
```

### 2. Detect Conflicts (Read-Only)
```python
from scheduler_mcp.scheduling_tools import detect_conflicts, ConflictDetectionRequest

result = await detect_conflicts(
    request=ConflictDetectionRequest(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        conflict_types=["double_booking", "work_hour_violation"],
    )
)
# Returns: Conflict list with severity, affected people, resolution options
# TIER: 1 (Safe)
```

### 3. Analyze Swap Candidates (Read-Only)
```python
from scheduler_mcp.scheduling_tools import analyze_swap_candidates, SwapCandidateRequest

result = await analyze_swap_candidates(
    request=SwapCandidateRequest(
        requester_person_id="PGY2-001",
        assignment_id="assign-123",
        max_candidates=10,
    )
)
# Returns: Ranked candidates with match scores and compatibility
# TIER: 1 (Safe)
```

### 4. Run Contingency Analysis (Analysis)
```python
from scheduler_mcp.scheduling_tools import run_contingency_analysis, ContingencyRequest, ContingencyScenario

result = await run_contingency_analysis(
    request=ContingencyRequest(
        scenario=ContingencyScenario.FACULTY_ABSENCE,
        affected_person_ids=["FAC-001"],
        start_date=date(2025, 2, 1),
        end_date=date(2025, 2, 7),
        auto_resolve=False,  # Don't actually apply changes
    )
)
# Returns: Impact assessment, resolution options
# TIER: 2 (Review-ready)
```

### 5. Detect Burnout Precursors (Read-Only)
```python
from scheduler_mcp.early_warning_integration import detect_burnout_precursors, PrecursorDetectionRequest

result = await detect_burnout_precursors(
    request=PrecursorDetectionRequest(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        sensitivity="medium",
    )
)
# Returns: Precursor signals with magnitude and confidence
# TIER: 1 (Safe)
```

### 6. Generate Schedule (Write - REQUIRES APPROVAL)
```python
from scheduler_mcp.api_client import get_api_client

client = await get_api_client()
result = await client.generate_schedule(
    start_date="2025-01-01",
    end_date="2025-01-31",
    algorithm="greedy",        # or "cp_sat", "pulp", "hybrid"
    timeout_seconds=120,
    clear_existing=False,      # Don't delete existing first
)
# Returns: Generated assignments, validation results
# TIER: 2 (Requires approval before applying)
```

---

## Tool Categories at a Glance

### Read-Only Analysis (TIER 1 - Always Safe)
| Tool | Purpose | API Call |
|------|---------|----------|
| `validate_schedule` | Check ACGME compliance | GET `/schedule/validate` |
| `detect_conflicts` | Find scheduling conflicts | GET `/conflicts/analyze` |
| `get_compliance_summary` | ACGME metrics and violations | Direct DB (Resource) |
| `get_schedule_status` | Current schedule overview | Direct DB (Resource) |
| `detect_burnout_precursors` | STA/LTA burnout detection | Analysis only |
| `run_spc_analysis` | Statistical process control | Analysis only |
| `analyze_swap_candidates` | Find compatible swap partners | POST `/swaps/candidates` |
| `calculate_schedule_entropy` | Measure schedule disorder | Thermodynamics model |

### Scenario Analysis (TIER 2 - Review Before Apply)
| Tool | Purpose | Can Modify |
|------|---------|-----------|
| `run_contingency_analysis` | Impact of absences | No (preview only) |
| `run_contingency_analysis_deep` | N-1/N-2 vulnerability analysis | No |
| `calculate_recovery_distance` | Edits needed to recover from shock | No |
| `simulate_burnout_contagion` | Fatigue spread prediction | No |

### Generation (TIER 2 - Human Approval Required)
| Tool | Purpose | Creates |
|------|---------|---------|
| `generate_schedule` | Create new assignments | Assignments |
| `execute_sacrifice_hierarchy` | Load shedding decisions | Cancellations |

### Destructive (TIER 3 - Humans Only)
| Tool | Purpose | Blocked From |
|------|---------|-------------|
| Delete operations | Remove assignments | MCP (CLI only) |
| Clear schedule | Wipe all assignments | MCP (CLI only) |
| Direct SQL | Raw queries | MCP (always) |

---

## Database Tables You Can Query

**Core Tables:**
- `assignment` - Person assignments to blocks
- `block` - Half-day scheduling blocks (730/year)
- `person` - Residents and faculty
- `rotation_template` - Rotation definitions

**Conflict/Compliance:**
- `conflict_alert` - Detected conflicts
- `swap_record` - Swap requests
- `absence` - Leave records

**Credentials:**
- `credential` - Faculty certifications
- `certification` - Training records

**Resilience:**
- `circuit_breaker_state` - System health
- `utilization_metric` - Workload measurements
- `defense_level` - System state (GREEN/YELLOW/ORANGE/RED/BLACK)

---

## Authentication Setup

**Required Environment Variables:**
```bash
API_BASE_URL=http://backend:8000
API_USERNAME=mcp-user
API_PASSWORD=<secure-password>
```

**How It Works:**
1. `get_api_client()` creates client
2. First call triggers `POST /auth/login/json`
3. JWT token stored in memory
4. All subsequent calls use `Authorization: Bearer {token}` header
5. Token auto-refreshed on 401 response

---

## Common Patterns

### Pattern 1: Check Compliance First
```python
# Always validate before making changes
result = await validate_schedule(
    request=ScheduleValidationRequest(
        start_date=start,
        end_date=end,
        check_work_hours=True,
        check_supervision=True,
    )
)
if result.is_valid:
    print(f"✓ Schedule compliant ({result.overall_compliance_rate:.1%})")
else:
    print(f"✗ {result.critical_issues} critical issues")
    for issue in result.issues:
        if issue.severity == "critical":
            print(f"  - {issue.message}")
```

### Pattern 2: Analyze Before Approving
```python
# Simulate impact before approval
result = await run_contingency_analysis(
    request=ContingencyRequest(
        scenario=scenario,
        affected_person_ids=ids,
        start_date=start,
        end_date=end,
        auto_resolve=False,  # Just analyze, don't apply
    )
)
print(f"Impact: {result.impact.coverage_gaps} coverage gaps")
print(f"Options: {len(result.resolution_options)} solutions available")
# Human reviews and approves/rejects before calling again with auto_resolve=True
```

### Pattern 3: Get Current Status
```python
# Resources auto-update and can be subscribed to
status = await get_schedule_status(
    start_date=date.today(),
    end_date=date.today() + timedelta(days=30),
)
print(f"Assignments: {status.total_assignments}")
print(f"Coverage Rate: {status.coverage_metrics.coverage_rate:.1%}")
print(f"Active Conflicts: {status.active_conflicts}")
```

### Pattern 4: Error Handling
```python
try:
    result = await validate_schedule(request)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        logger.error("Authentication failed - check credentials")
    elif e.response.status_code == 404:
        logger.error("Endpoint not found")
    else:
        logger.error(f"Backend error: {e.response.status_code}")
except ValueError as e:
    logger.error(f"Invalid parameters: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

---

## Power Levels

```
TIER 1 (SAFE - No Approval Needed)
├─ All analysis tools (30+)
├─ Compliance checking
├─ Conflict detection
├─ Swap analysis
├─ Burnout precursor detection
├─ Resilience analysis
└─ → Can use autonomously

TIER 2 (REVIEW - Human Approval)
├─ Schedule generation
├─ Contingency scenario planning
├─ Sacrifice hierarchy (load shedding)
├─ Burnout contagion simulation
└─ → Must preview before applying

TIER 3 (DESTRUCTIVE - Humans Only)
├─ Delete assignments
├─ Clear entire schedules
├─ Direct SQL execution
└─ → Cannot invoke from MCP
```

---

## Avoiding Common Mistakes

### ✗ WRONG: Direct Database Access
```python
# This will fail - no direct DB from MCP!
from app.db.session import SessionLocal
db = SessionLocal()
result = db.query(Assignment).all()
```

### ✓ RIGHT: Use API Client
```python
# This works - authenticated API
client = await get_api_client()
result = await client.get_assignments()
```

### ✗ WRONG: Ignoring Auth Errors
```python
# Token might expire - no retry
result = await client.some_operation()
```

### ✓ RIGHT: Handle Auth Gracefully
```python
try:
    result = await client.some_operation()
except httpx.HTTPStatusError as e:
    if e.response.status_code == 401:
        # Re-authenticate and retry
        client._token = None
        result = await client.some_operation()
```

### ✗ WRONG: Returning PII
```python
# Leaks resident names!
people = await client.get_people()
return people  # ❌ Contains names, emails
```

### ✓ RIGHT: Sanitize Results
```python
people = await client.get_people()
sanitized = [
    {"role": f"PGY-{p['pgy_level']}", "id": p['id']}
    for p in people
]
return sanitized  # ✓ No PII
```

---

## Performance Tips

1. **Pagination:** Use `limit=100` to `500`, not unlimited
2. **Date Ranges:** Narrow date ranges where possible
3. **Eager Loading:** Resources use `joinedload()` to prevent N+1 queries
4. **Batch Operations:** Use `get_by_block_ids()` instead of looping
5. **Caching:** Results are cached at API layer when possible
6. **Timeout Control:** Set explicit timeouts for long operations

---

## Testing Your Setup

```python
from scheduler_mcp.api_client import get_api_client

# Test authentication
client = await get_api_client()
is_alive = await client.health_check()
print(f"Backend status: {'UP' if is_alive else 'DOWN'}")

# Test a simple query
people = await client.get_people(limit=10)
print(f"Found {len(people)} people")
```

---

## Where to Find More Info

**Full Documentation:**
- `.claude/Scratchpad/OVERNIGHT_BURN/SESSION_8_MCP/mcp-tools-database.md`

**Code References:**
- Tool implementations: `/mcp-server/src/scheduler_mcp/`
- API client: `/mcp-server/src/scheduler_mcp/api_client.py`
- Resources: `/mcp-server/src/scheduler_mcp/resources.py`
- Backend services: `/backend/app/services/`
- Repositories: `/backend/app/repositories/`

---

## Emergency Contacts

**If Backend Down:**
```bash
docker-compose ps           # Check services
docker-compose logs backend # View error logs
docker-compose restart backend
```

**If Authentication Fails:**
```bash
# Check credentials in docker-compose.yml
# MCP_USER and MCP_PASSWORD environment vars
docker-compose exec backend python -c \
  "from app.core.security import hash_password; print(hash_password('new-password'))"
```

**If Queries Hang:**
```bash
# Check database connections
docker-compose exec db psql -U scheduler -d residency_scheduler -c "SELECT count(*) FROM pg_stat_activity;"
# May need to increase pool_size if too many connections
```

---

## TL;DR - Absolute Essentials

1. Always use `get_api_client()` for data access
2. Check tool tier before invoking (TIER 1 = safe, TIER 2 = review, TIER 3 = forbidden)
3. Validate schedule before making changes
4. Simulate impact before approving generation
5. Handle authentication errors gracefully
6. Never return PII (use role identifiers instead)
7. Prefer pagination over unlimited queries
8. Check `/health` if things seem broken

**You're good to go!** 🚀

