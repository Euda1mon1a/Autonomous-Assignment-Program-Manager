# Security Review: MCP Resilience Tools

**Date:** 2025-12-28
**Reviewer:** Security Auditor Agent
**Scope:** 13+ new MCP tools exposing resilience framework capabilities
**Status:** COMPLETED

---

## Executive Summary

This security review examines the newly added MCP tools that expose the resilience framework. The review identified **2 Critical**, **5 High**, **8 Medium**, and **6 Low** severity findings. The most significant concerns are potential PII exposure through burnout analytics tools and insufficient date range validation that could enable DoS attacks.

**Overall Risk Assessment: MEDIUM-HIGH**

The tools are well-architected with Pydantic validation, but several critical gaps exist around data anonymization and rate limiting that must be addressed before production deployment.

---

## Files Reviewed

| File | Purpose | Lines |
|------|---------|-------|
| `mcp-server/src/scheduler_mcp/server.py` | Main MCP server & tool registration | 1621 |
| `mcp-server/src/scheduler_mcp/resilience_integration.py` | Resilience framework wrappers | 2351 |
| `mcp-server/src/scheduler_mcp/early_warning_integration.py` | Burnout early warning tools | 1262 |
| `mcp-server/src/scheduler_mcp/optimization_tools.py` | Erlang/Process/Equity tools | 939 |
| `mcp-server/src/scheduler_mcp/composite_resilience_tools.py` | Advanced resilience analytics | 1051 |
| `mcp-server/src/scheduler_mcp/tools/validate_schedule.py` | Schedule validation tool | 243 |
| `mcp-server/src/scheduler_mcp/api_client.py` | Backend API client | 289 |

---

## Findings by Severity

### CRITICAL (2)

#### C-1: PII Exposure in Burnout Epidemiology Tools

**Location:** `resilience_integration.py` lines 94-130, 1317-1378

**Description:** The `ContingencyAnalysisResponse`, `BurnoutRtResponse`, and related models expose faculty/resident names directly:

```python
class VulnerabilityInfo(BaseModel):
    faculty_id: str
    faculty_name: str  # <-- PII EXPOSED
    severity: str
    ...

class SuperspreaderInfo(BaseModel):
    provider_id: str  # <-- PII with identifiable patterns
    secondary_cases: int
    ...

class HubCentralityInfo(BaseModel):
    faculty_id: str
    faculty_name: str  # <-- PII EXPOSED
    centrality_score: float
    ...
```

**Impact:**
- HIPAA violation risk - burnout data is health-related information
- OPSEC/PERSEC violation - exposes military personnel patterns
- Reputational harm if burnout scores are leaked with identifiable names

**Recommendation:**
1. Replace all `faculty_name`/`provider_name` fields with anonymized references (e.g., "Provider-A1", "Faculty-Hub-001")
2. Add a sanitization layer before returning any response
3. Implement the same pattern used in `validate_schedule.py` (see good example on line 41-56)

**Example Fix:**
```python
def _anonymize_provider_id(provider_id: str) -> str:
    """Create a consistent but non-identifying reference."""
    import hashlib
    hash_suffix = hashlib.sha256(provider_id.encode()).hexdigest()[:6]
    return f"Provider-{hash_suffix}"
```

---

#### C-2: Default API Credentials Hardcoded

**Location:** `api_client.py` lines 24-25

**Description:** Default credentials are hardcoded in the `APIConfig` class:

```python
class APIConfig(BaseModel):
    ...
    username: str = "admin"
    password: str = "admin123"  # <-- HARDCODED CREDENTIAL
```

While these are overridden by environment variables when available, the defaults are dangerous if `.env` is misconfigured.

**Impact:**
- Credential exposure in error messages or logs
- Accidental production deployment with default credentials
- Code scanning tools will flag this

**Recommendation:**
1. Remove default values or use obviously invalid placeholders:
```python
username: str = ""  # REQUIRED: Set via API_USERNAME env var
password: str = ""  # REQUIRED: Set via API_PASSWORD env var
```
2. Add validation that fails startup if credentials are empty

---

### HIGH (5)

#### H-1: Unbounded Date Range Queries (DoS Vector)

**Location:** `server.py` lines 219-258, `resilience_integration.py`

**Description:** The `parse_date_range()` function and several tools accept arbitrary date ranges without upper bounds:

```python
def parse_date_range(date_range: str) -> tuple[date, date]:
    # ...
    elif ":" in date_range:
        parts = date_range.split(":")
        if len(parts) == 2:
            start = date.fromisoformat(parts[0].strip())
            end = date.fromisoformat(parts[1].strip())
            return start, end  # <-- NO VALIDATION OF RANGE SIZE
```

**Impact:**
- Query for 10-year date range could exhaust database resources
- Memory exhaustion from loading millions of records
- Backend timeout causing cascading failures

**Recommendation:**
```python
MAX_DATE_RANGE_DAYS = 365  # Maximum 1 year

def parse_date_range(date_range: str) -> tuple[date, date]:
    # ... existing parsing ...

    # Add validation
    if (end - start).days > MAX_DATE_RANGE_DAYS:
        raise ValueError(f"Date range cannot exceed {MAX_DATE_RANGE_DAYS} days")
    if end < start:
        raise ValueError("End date must be after start date")

    return start, end
```

---

#### H-2: Missing Rate Limiting on Resilience Tools

**Location:** All tools in `server.py`

**Description:** No rate limiting is implemented on MCP tools. An attacker or misconfigured client could call expensive tools like `run_contingency_analysis_resilience_tool` or `benchmark_solvers_tool` thousands of times.

**Impact:**
- Resource exhaustion on backend
- Denial of service
- Excessive costs if running in cloud

**Recommendation:**
1. Implement tool-level rate limiting using token bucket or sliding window
2. Add request quotas per tool category:
   - Analytics tools: 10/minute
   - Heavy computation (benchmark, contingency): 2/minute
   - Status/read-only: 60/minute

**Example Implementation:**
```python
from functools import wraps
import time

_rate_limits = {}

def rate_limit(calls_per_minute: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = func.__name__
            now = time.time()
            window_start = now - 60

            # Clean old entries
            _rate_limits[key] = [t for t in _rate_limits.get(key, []) if t > window_start]

            if len(_rate_limits.get(key, [])) >= calls_per_minute:
                raise ValueError(f"Rate limit exceeded: {calls_per_minute}/minute for {key}")

            _rate_limits.setdefault(key, []).append(now)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

#### H-3: Burnout Scores Could Enable Discrimination

**Location:** `early_warning_integration.py`, `resilience_integration.py`

**Description:** Tools expose burnout scores, danger classifications, and risk assessments that could be misused:

```python
class FireDangerResponse(BaseModel):
    resident_id: str
    danger_class: DangerClassEnum  # LOW, MODERATE, HIGH, VERY_HIGH, EXTREME
    fwi_score: float
    requires_intervention: bool  # <-- Could be used for adverse actions
    ...

class CreepFatigueAssessment(BaseModel):
    resident_id: str
    overall_risk: str  # "high" could lead to discrimination
    estimated_days_to_failure: int  # <-- Highly sensitive
    ...
```

**Impact:**
- Could be used for discriminatory personnel decisions
- Legal liability under ADA/employment law
- Chilling effect on seeking help if residents know they're being scored

**Recommendation:**
1. Add access control - only authorized wellness coordinators should see individual-level data
2. Aggregate data by default, require elevated permissions for individual assessments
3. Add audit logging for all burnout score access
4. Include disclaimer in responses about proper use

---

#### H-4: No Authentication Check on MCP Tools

**Location:** `server.py` - all `@mcp.tool()` decorated functions

**Description:** MCP tools do not verify caller authentication before executing. While the MCP protocol may provide some context, the tools themselves don't validate permissions.

**Impact:**
- Unauthorized access to sensitive health/burnout data
- Ability to trigger expensive computations
- Potential data exfiltration

**Recommendation:**
1. Implement tool-level permission checks:
```python
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check MCP context for auth token
            ctx = get_mcp_context()
            if not ctx.has_permission(permission):
                raise PermissionError(f"Requires {permission} permission")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@mcp.tool()
@require_permission("resilience:read")
async def check_utilization_threshold_tool(...):
    ...
```

2. Define permission tiers:
   - `resilience:read` - View aggregated metrics
   - `resilience:individual` - View individual-level data
   - `resilience:write` - Execute sacrifice hierarchy, deploy fallbacks
   - `resilience:admin` - Full access including benchmarks

---

#### H-5: Error Messages May Leak Sensitive Information

**Location:** Multiple files, exception handling patterns

**Description:** Several tools include raw exception details in error messages:

```python
# resilience_integration.py line 783-785
except Exception as e:
    logger.error(f"Contingency analysis failed: {e}")
    raise RuntimeError(f"Failed to run contingency analysis: {e}") from e

# early_warning_integration.py line 463-465
except Exception as e:
    logger.error(f"Precursor detection failed: {e}")
    raise RuntimeError(f"Failed to detect burnout precursors: {e}") from e
```

**Impact:**
- Stack traces may expose internal paths
- Database errors could leak schema information
- Personnel IDs in error context

**Recommendation:**
1. Use generic error messages for external responses
2. Log detailed errors internally with correlation IDs
3. Example pattern:
```python
except Exception as e:
    error_id = uuid.uuid4().hex[:8]
    logger.error(f"[{error_id}] Contingency analysis failed: {e}", exc_info=True)
    raise RuntimeError(f"Contingency analysis failed. Error ID: {error_id}. Contact support.") from None
```

---

### MEDIUM (8)

#### M-1: MD5 Used for UUID Generation

**Location:** `early_warning_integration.py` lines 343-346, 693-696, 1009-1012

**Description:** MD5 is used to generate deterministic UUIDs from resident IDs:

```python
import hashlib
hash_bytes = hashlib.md5(request.resident_id.encode()).digest()
resident_uuid = UUID(bytes=hash_bytes)
```

**Impact:**
- MD5 is cryptographically broken
- Collision attacks could allow impersonation
- Not a direct vulnerability but violates security best practices

**Recommendation:** Use SHA-256 instead:
```python
hash_bytes = hashlib.sha256(request.resident_id.encode()).digest()[:16]
resident_uuid = UUID(bytes=hash_bytes)
```

---

#### M-2: Time Series Data Not Bounded

**Location:** `early_warning_integration.py` lines 74-75, 147-149

**Description:** Time series inputs for precursor detection and SPC analysis have `min_length=1` but no maximum length:

```python
class PrecursorDetectionRequest(BaseModel):
    time_series: list[float] = Field(
        min_length=1, description="Time series data..."
    )

class SPCAnalysisRequest(BaseModel):
    weekly_hours: list[float] = Field(
        min_length=1, description="Weekly work hours..."
    )
```

**Impact:**
- Memory exhaustion with very long time series
- Slow computation times

**Recommendation:** Add maximum length validation:
```python
time_series: list[float] = Field(
    min_length=1,
    max_length=1000,  # Maximum 1000 data points
    description="Time series data..."
)
```

---

#### M-3: Batch Operations Without Size Limits

**Location:** `early_warning_integration.py` lines 257-262

**Description:** `BatchFireDangerRequest` allows unlimited batch sizes:

```python
class BatchFireDangerRequest(BaseModel):
    residents: list[FireDangerRequest] = Field(
        description="List of resident data for batch processing"
    )
```

**Impact:**
- Could process thousands of residents in one call
- Memory/CPU exhaustion

**Recommendation:**
```python
residents: list[FireDangerRequest] = Field(
    max_length=100,  # Maximum 100 residents per batch
    description="List of resident data (max 100 per request)"
)
```

---

#### M-4: `auto_resolve` Parameter Could Enable Unintended Changes

**Location:** `server.py` lines 447, 471

**Description:** The `run_contingency_analysis_tool` has an `auto_resolve: bool = False` parameter that could trigger automatic schedule changes:

```python
async def run_contingency_analysis_tool(
    ...
    auto_resolve: bool = False,  # <-- Dangerous if True
) -> ContingencyAnalysisResult:
```

**Impact:**
- Automated changes without human review
- Could cascade into compliance violations

**Recommendation:**
1. Require explicit confirmation for auto_resolve
2. Add audit logging when auto_resolve is used
3. Consider removing this parameter from the MCP tool entirely

---

#### M-5: Simulation Mode Not Enforced

**Location:** `resilience_integration.py` line 821

**Description:** The `execute_sacrifice_hierarchy` function has `simulate_only: bool = True` but relies on caller to set it:

```python
async def execute_sacrifice_hierarchy(
    target_level: LoadSheddingLevelEnum,
    simulate_only: bool = True,  # Default is safe, but...
) -> SacrificeHierarchyResponse:
```

**Impact:**
- Accidental execution of load shedding could suspend critical activities

**Recommendation:**
1. Always require explicit confirmation for non-simulation mode
2. Add audit logging for production execution
3. Consider requiring two-phase commit (request -> confirm)

---

#### M-6: Provider Hours Dict Keys Not Validated

**Location:** `optimization_tools.py` lines 735-745

**Description:** The `calculate_equity_metrics` function accepts arbitrary string keys without validation:

```python
async def calculate_equity_metrics(
    provider_hours: dict[str, float],
    intensity_weights: dict[str, float] | None = None,
) -> EquityMetricsResponse:
```

**Impact:**
- Keys could contain injection payloads
- Keys could be excessively long strings

**Recommendation:** Add key validation:
```python
MAX_KEY_LENGTH = 64
VALID_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

for key in provider_hours.keys():
    if len(key) > MAX_KEY_LENGTH:
        raise ValueError(f"Provider ID too long: max {MAX_KEY_LENGTH} chars")
    if not VALID_KEY_PATTERN.match(key):
        raise ValueError(f"Provider ID contains invalid characters: {key}")
```

---

#### M-7: Log Level Configurable via CLI

**Location:** `server.py` lines 1592-1595

**Description:** The `--log-level` CLI argument allows setting DEBUG level:

```python
parser.add_argument(
    "--log-level",
    default=os.getenv("LOG_LEVEL", "INFO"),
    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    ...
)
```

**Impact:**
- DEBUG logs may contain sensitive data
- Should not be exposed in production

**Recommendation:**
1. Remove DEBUG from production choices
2. Or ensure all DEBUG logs are sanitized

---

#### M-8: Missing Input Validation for `max_candidates` and `max_servers`

**Location:** `server.py` line 515, `optimization_tools.py` line 233

**Description:** Parameters like `max_candidates` have upper bounds (50), but validation happens client-side:

```python
max_candidates: int = 10,  # Docstring says "1-50" but not enforced
```

**Impact:**
- Could request thousands of candidates
- Resource exhaustion

**Recommendation:** Use Pydantic's `Field` for validation:
```python
max_candidates: int = Field(default=10, ge=1, le=50)
```

---

### LOW (6)

#### L-1: Inconsistent Error Handling Patterns

**Location:** Throughout codebase

**Description:** Some functions return fallback responses on error, others raise exceptions. This inconsistency makes error handling unpredictable.

**Recommendation:** Standardize on one pattern (prefer raising exceptions with proper error types).

---

#### L-2: Placeholder Responses in Production

**Location:** Multiple files

**Description:** Many tools return placeholder/mock data when backend is unavailable. While graceful degradation is good, the placeholders could be confusing.

**Recommendation:** Clearly mark placeholder data in metadata:
```python
metadata={"is_placeholder": True, "reason": "backend_unavailable"}
```

---

#### L-3: No Request/Response Logging

**Location:** All tools

**Description:** Tool invocations are not logged for audit purposes.

**Recommendation:** Add structured logging for each tool call (sanitized):
```python
logger.info("tool_invocation", extra={
    "tool": "check_utilization_threshold",
    "user_id": ctx.user_id,
    "timestamp": datetime.utcnow().isoformat()
})
```

---

#### L-4: No Timeout on Background Task Status Polling

**Location:** `server.py` lines 598-619

**Description:** `get_task_status_tool` doesn't timeout if Celery is unresponsive.

**Recommendation:** Add timeout parameter with default.

---

#### L-5: Deprecation Warnings in Dependencies

**Location:** `composite_resilience_tools.py`

**Description:** Uses `datetime.utcnow()` which is deprecated in Python 3.12.

**Recommendation:** Use `datetime.now(timezone.utc)` instead.

---

#### L-6: No Schema Version in Responses

**Location:** All response models

**Description:** Response schemas have no version field, making future compatibility changes difficult.

**Recommendation:** Add `schema_version: str = "1.0"` to response models.

---

## Recommendations Summary

### Immediate Actions (Before Deployment)

1. **Anonymize all PII in responses** - Replace names with anonymized references
2. **Remove hardcoded credentials** - Fail startup if credentials not configured
3. **Add date range bounds** - Maximum 365-day queries
4. **Implement rate limiting** - Token bucket per tool category

### Short-Term (Next Sprint)

5. Add authentication/authorization layer to tools
6. Implement audit logging for all tool invocations
7. Standardize error handling with correlation IDs
8. Bound all list inputs (time_series, batch sizes)

### Medium-Term (Next Quarter)

9. Add permission tiers for burnout/health data access
10. Implement request quotas and monitoring
11. Add schema versioning
12. Create security test suite for MCP tools

---

## HIPAA Compliance Considerations

The burnout analytics tools process health-related information (burnout scores, fatigue assessments, epidemiological data). Under HIPAA:

1. **PHI Identification:** Burnout scores combined with provider IDs constitute PHI
2. **Minimum Necessary:** Only authorized wellness coordinators should access individual data
3. **Audit Trail:** All access to burnout data must be logged
4. **Data Sanitization:** Responses must be anonymized for non-privileged users

**Recommendation:** Conduct formal HIPAA privacy impact assessment before production deployment.

---

## OPSEC/PERSEC Considerations

Per CLAUDE.md security requirements, schedule data reveals duty patterns for military medical personnel:

1. **Never expose real names** in API responses
2. **Never log identifiable schedule patterns**
3. **Aggregate data** for external reporting
4. **Sanitize error messages** that might contain duty information

---

## Appendix: Good Security Patterns Found

The codebase already implements several good security patterns:

### `validate_schedule.py` - Excellent Input Sanitization

```python
@field_validator("schedule_id")
@classmethod
def validate_schedule_id(cls, v: str) -> str:
    """Validate schedule_id for security."""
    dangerous_patterns = [
        "..", "/", "\\", "<", ">", "'", '"',
        ";", "&", "|", "$", "`", "\n", "\r", "\x00",
    ]
    for pattern in dangerous_patterns:
        if pattern in v:
            raise ValueError("schedule_id contains invalid characters")
    ...
```

This pattern should be applied to other ID inputs.

### Pydantic Field Validation

Good use of Pydantic `Field` with constraints:
```python
utilization_rate: float = Field(ge=0.0, le=1.0)
```

This should be extended to all numeric inputs.

---

**Review Completed:** 2025-12-28
**Next Review Recommended:** After addressing Critical/High findings
