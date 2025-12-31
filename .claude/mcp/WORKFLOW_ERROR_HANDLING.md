# Workflow Error Handling Patterns

**Purpose**: Standardized error handling across all MCP tool workflows
**Scope**: All 4 workflows (Schedule Generation, Compliance Check, Swap Execution, Resilience Assessment)
**Safety**: TIER 1 (reference guide)
**Last Updated**: 2025-12-31

---

## Overview

All workflows use consistent error handling patterns to ensure reliability, auditability, and user-friendly error reporting.

```
Error Detection
  │
  ├─→ Categorize Error Type
  │     ├─ Tool Failure (timeout, exception)
  │     ├─ Data Error (invalid input, missing data)
  │     ├─ Compliance Error (violation detected)
  │     └─ System Error (database, service down)
  │
  ├─→ Determine Severity
  │     ├─ CRITICAL: Halt workflow
  │     ├─ HIGH: Continue with degradation
  │     └─ MEDIUM: Log and continue
  │
  ├─→ Apply Recovery Strategy
  │     ├─ Retry (transient failures)
  │     ├─ Fallback (cached data, simplified calc)
  │     ├─ Skip Phase (continue next phase)
  │     └─ Abort Workflow (critical failure)
  │
  └─→ Notify & Log
        ├─ User alert
        ├─ Audit log
        └─ Metrics/monitoring
```

---

## Error Categories

### 1. Tool Failures

**Definition**: MCP tool timeout, exception, or unavailable

**Causes**:
- Tool timeout (backend service slow)
- API call fails (network, auth)
- Tool not implemented/registered
- Exception in tool code

**Detection**:
```python
try:
    result = await tool_function(...)
except asyncio.TimeoutError:
    # Tool timed out
    raise ToolTimeoutError(f"Tool {tool_name} exceeded {timeout}s timeout")

except httpx.ConnectError:
    # Network/API error
    raise ToolConnectionError(f"Cannot reach API for {tool_name}")

except Exception as e:
    # Unexpected exception
    raise ToolExecutionError(f"Tool {tool_name} failed: {e}")
```

**Recovery Strategies**:

```
Strategy 1: Retry (for transient failures)
  ├─ Retry up to 3 times
  ├─ Exponential backoff (100ms, 500ms, 2s)
  ├─ Use for: Network timeouts, rate limiting
  └─ Success rate: 70-80% of transient failures

Strategy 2: Fallback to Cached Data
  ├─ If tool result cached from <24h ago
  ├─ Return cached with "degraded" flag
  ├─ Use for: Non-critical analysis tools
  └─ Mark report: "Using cached data from X hours ago"

Strategy 3: Skip Tool (Continue Workflow)
  ├─ Mark result as "SKIPPED"
  ├─ Continue with remaining tools
  ├─ Use for: Optional analysis in Phase 4
  └─ Adjust confidence level in final result

Strategy 4: Use Fallback Calculation
  ├─ Use simplified/approximate calculation
  ├─ Example: Utilization check timeout → use cached utilization
  ├─ Use for: Core tools (validate_schedule)
  └─ Mark as "simplified estimate"

Strategy 5: Abort Workflow
  ├─ Stop immediately
  ├─ Return error to user
  ├─ Use for: Critical tools without fallback
  └─ Example: Schedule validation timeout in Phase 1
```

**Implementation Example**:
```python
async def call_tool_with_fallback(
    tool_func,
    tool_name: str,
    args,
    timeout: float = 5.0,
    allow_cached: bool = True,
    critical: bool = False,
) -> ToolResult:
    """Call tool with comprehensive error handling."""

    # Attempt 1: Normal execution
    try:
        return await asyncio.wait_for(tool_func(*args), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"{tool_name} timed out after {timeout}s")
        # Continue to retry logic

    except Exception as e:
        logger.error(f"{tool_name} raised exception: {e}")
        # Continue to fallback logic

    # Attempt 2: Retry (if transient)
    try:
        logger.info(f"Retrying {tool_name}...")
        await asyncio.sleep(0.1)  # Short delay
        return await asyncio.wait_for(tool_func(*args), timeout=timeout * 2)
    except Exception:
        logger.warning(f"Retry failed for {tool_name}")

    # Attempt 3: Fallback
    if allow_cached:
        cached = get_cached_result(tool_name)
        if cached and not is_stale(cached, max_age_hours=24):
            logger.info(f"Using cached result for {tool_name}")
            return ToolResult(
                data=cached.data,
                source="cache",
                degraded=True,
                warning=f"Using cached data from {cached.timestamp}"
            )

    # Attempt 4: Simplified calculation
    if tool_name == "validate_schedule":
        logger.info("Returning simplified validation")
        return simplified_validation(args)

    # Attempt 5: Abort if critical
    if critical:
        raise ToolUnavailableError(f"Critical tool {tool_name} unavailable")

    # Otherwise return null result
    return ToolResult(
        data=None,
        source="failed",
        degraded=True,
        warning=f"Tool {tool_name} unavailable - skipping"
    )
```

---

### 2. Data Errors

**Definition**: Invalid input, missing data, or data quality issues

**Causes**:
- Invalid date range
- Missing person ID
- Malformed request
- Schedule data corruption
- Query returns no data

**Detection**:
```python
def validate_input(request: ScheduleRequest):
    """Validate request parameters."""

    errors = []

    # Check required fields
    if not request.start_date:
        errors.append("start_date required")
    if not request.end_date:
        errors.append("end_date required")

    # Check data constraints
    if request.start_date > request.end_date:
        errors.append("start_date must be before end_date")

    # Check date range (not too large)
    delta = (request.end_date - request.start_date).days
    if delta > 365:
        errors.append("Date range cannot exceed 365 days")

    # Check for injection/malformation
    if not is_valid_uuid(request.schedule_id):
        errors.append(f"Invalid schedule_id format: {request.schedule_id}")

    if errors:
        raise ValidationError(errors)
```

**Recovery Strategies**:

```
Strategy 1: Return Error (User Input Error)
  ├─ Provide clear error message
  ├─ Suggest fix (e.g., "start_date must be before end_date")
  ├─ Return 400 Bad Request
  └─ Log for monitoring (not escalation)

Strategy 2: Use Default (Missing Optional Data)
  ├─ If optional parameter missing, use default
  ├─ Example: If end_date omitted, use today + 30 days
  ├─ Log default usage
  └─ Inform user in response

Strategy 3: Coerce/Normalize Data
  ├─ String to date conversion
  ├─ UUID normalization
  ├─ Trim whitespace
  ├─ Example: "2025-12-31" → date(2025, 12, 31)
  └─ Validate after coercion

Strategy 4: Partial Data Processing
  ├─ If some data missing, process what's available
  ├─ Mark missing data in results
  ├─ Example: No person in request → analyze schedule globally
  └─ Note: "Some individuals not found - using available data"

Strategy 5: Abort with Clear Error
  ├─ If critical data missing (e.g., schedule_id)
  ├─ Return clear, actionable error
  ├─ Log for escalation
  └─ Return 400 or 404 as appropriate
```

---

### 3. Compliance Errors

**Definition**: ACGME or operational constraint violation detected

**Causes**:
- Schedule violates 80-hour rule
- Supervision ratio inadequate
- No backup available for critical role
- Leave overlap conflict

**Detection**:
```python
def detect_compliance_error(validation_result) -> Optional[ComplianceError]:
    """Check for ACGME compliance violations."""

    if not validation_result.is_compliant:
        return ComplianceError(
            rule_violated=validation_result.violations[0].rule,
            severity="CRITICAL",
            affected_people=validation_result.violations[0].affected_entities,
            message=validation_result.violations[0].description,
        )

    return None
```

**Recovery Strategies**:

```
Strategy 1: Block Operation (Critical Violation)
  ├─ Prevent schedule deployment
  ├─ Prevent swap execution
  ├─ Return error to user
  ├─ Log for compliance audit
  └─ Require manual review + fix

Strategy 2: Request Modification
  ├─ Identify specific violation
  ├─ Suggest remediation (e.g., "reduce Jane's assignments by 2")
  ├─ Allow user to provide alternatives
  └─ Re-validate after changes

Strategy 3: Accept with Waiver
  ├─ Allow override with approval
  ├─ Log decision + approver
  ├─ Create compliance exception record
  └─ Monitor closely going forward

Strategy 4: Defer Decision
  ├─ If borderline (80.5 hours in 80-hour rule)
  ├─ Request manual review by coordinator
  ├─ Provide context + suggestion
  └─ Continue workflow pending review
```

**Example Response**:
```json
{
  "error": "COMPLIANCE_VIOLATION",
  "severity": "CRITICAL",
  "rule": "80_hour_rule",
  "message": "Dr. Smith exceeds 80-hour limit in week 12-15",
  "affected_people": ["person-uuid-1"],
  "violations": [
    {
      "person": "Dr. Smith",
      "week": "2025-12-15:2025-12-22",
      "hours": 82.5,
      "excess": 2.5,
      "suggested_fix": "Remove 1 afternoon block"
    }
  ],
  "action_required": "MODIFICATION_NEEDED",
  "can_override": false,
  "next_steps": "Please modify schedule and resubmit"
}
```

---

### 4. System Errors

**Definition**: Backend service unavailable, database error, or infrastructure issue

**Causes**:
- Database connection pool exhausted
- API service down/unreachable
- Circuit breaker OPEN
- Memory/resource exhaustion

**Detection**:
```python
async def detect_system_error(error: Exception) -> Optional[SystemError]:
    """Detect infrastructure-level errors."""

    if isinstance(error, DatabaseConnectionError):
        return SystemError(
            component="database",
            status="unavailable",
            recovery_time="5-15 minutes typical"
        )

    if isinstance(error, CircuitBreakerOpenError):
        return SystemError(
            component="api_gateway",
            status="circuit_breaker_open",
            recovery_time="auto-recovery in ~5 minutes"
        )

    return None
```

**Recovery Strategies**:

```
Strategy 1: Graceful Degradation
  ├─ Use cached results (if available)
  ├─ Run simplified analysis
  ├─ Return partial results with warnings
  ├─ Mark entire response as "degraded"
  └─ Example: Skip N-2 contingency (keep N-1)

Strategy 2: Automatic Retry with Backoff
  ├─ Retry up to 5 times
  ├─ Exponential backoff (100ms → 10s)
  ├─ Use for: Transient infrastructure issues
  └─ Success rate: 60-70% recover within 30s

Strategy 3: Circuit Breaker
  ├─ Open circuit on repeated failures
  ├─ Fail fast (return error immediately)
  ├─ Half-open test every 30s
  ├─ Close when healthy
  └─ Automatic; user sees "Service temporarily unavailable"

Strategy 4: Queue for Retry
  ├─ Add operation to retry queue
  ├─ Process asynchronously
  ├─ Notify user when complete
  ├─ Use for: Non-urgent operations
  └─ Retry every 5 minutes for 24 hours

Strategy 5: Failover (Multi-region)
  ├─ Switch to secondary service
  ├─ Log failover event
  ├─ Monitor health of secondary
  └─ Not implemented in current system

Strategy 6: Return Cached Schedule
  ├─ If unable to generate/validate
  ├─ Use last known good schedule
  ├─ Mark as "last validated on X"
  ├─ Add warning: "Using cached schedule"
  └─ Update when system recovers
```

**Example Response**:
```json
{
  "error": "SYSTEM_ERROR",
  "message": "Database connection unavailable",
  "component": "database",
  "status": "degraded",
  "recovery_strategy": "Using cached schedule",
  "cached_data": {
    "last_validated": "2025-12-31T10:00:00Z",
    "age_hours": 5,
    "still_valid": true
  },
  "retry_options": {
    "auto_retry": true,
    "next_attempt": "2025-12-31T15:05:00Z",
    "manual_retry": "/api/retry/operation-id"
  },
  "user_action": "Try again in 5 minutes or use cached schedule"
}
```

---

## Cross-Workflow Error Handling

### Workflow: Schedule Generation

| Phase | Error Type | Recovery | Result |
|-------|-----------|----------|--------|
| 1 | Tool timeout | Retry 2x, then fallback | Continue to Phase 2 |
| 2 | Contingency fails | Skip N-2, use cached N-1 | Continue to Phase 3 |
| 3 | Early warning timeout | Partial results, lower confidence | Continue to Phase 4 |
| 4 | Unified index fails | Use Phase 3 signals directly | Proceed to Phase 5 |
| 5 | Generator timeout | Use greedy algorithm | Fallback to simpler approach |
| 6 | Validation fails | Review issues, request fix | Block deployment |

### Workflow: Compliance Check

| Phase | Error Type | Recovery | Result |
|-------|-----------|----------|--------|
| 1 | Validation timeout | Use quick check only | Continue to Phase 2 |
| 2 | Conflict detection fails | Use Phase 1 results only | Continue to Phase 3 |
| 3 | SPC/capability timeout | Skip advanced metrics | Complete with less detail |
| 4 | Synthesis fails | Use max violations count | Generate basic report |
| Any | Report generation fails | Return JSON results only | Skip formatting |

### Workflow: Swap Execution

| Phase | Error Type | Recovery | Result |
|-------|-----------|----------|--------|
| 1 | Validation fails | Reject swap request | User must fix issues first |
| 2 | No candidates found | Escalate to coordinator | Can't auto-match |
| 3 | Impact assessment fails | Manual review required | Coordinator decides |
| 4 | Approval timeout (24h) | Cancel request | User must resubmit |
| 5 | Execution fails | Auto-rollback to backup | Notify both parties |
| 5 | Notification fails | Retry 3x, escalate | Coordinator notifies manually |

### Workflow: Resilience Assessment

| Phase | Error Type | Recovery | Result |
|-------|-----------|----------|--------|
| 1 | Quick status fails | Skip to Phase 2 | Reduced visibility |
| 2 | Contingency fails | Use cached (if <12h) | Reduce detail |
| 3 | Epidemiology fails | Use existing Rt value | Reduce insight |
| 4 | Early warning batch timeout | Return partial results | Lower confidence |
| 5 | Unified index fails | Use weighted avg of signals | Manual synthesis needed |
| 6 | Alerting fails | Log to database, retry | Alert may be delayed |

---

## Error Response Format

All workflows use consistent JSON error responses:

```json
{
  "error": true,
  "error_code": "TOOL_TIMEOUT",
  "error_category": "tool_failure",
  "severity": "HIGH",
  "message": "Tool 'validate_schedule' exceeded 5.0 second timeout",
  "details": {
    "tool_name": "validate_schedule",
    "timeout_seconds": 5.0,
    "elapsed_seconds": 5.003
  },
  "recovery_strategy": "retry",
  "recovery_details": {
    "retry_attempt": 2,
    "max_retries": 3,
    "next_attempt_delay_ms": 500,
    "auto_retry": true
  },
  "user_action": "Workflow will retry automatically. If problem persists, try again in 5 minutes.",
  "technical_notes": "[For debugging] Full stack trace available in logs",
  "workflow": "schedule_generation",
  "workflow_phase": 1,
  "timestamp": "2025-12-31T15:00:00Z",
  "request_id": "req-12345678"
}
```

---

## Logging & Monitoring

### Error Levels

```python
logger.debug("Tool X starting with parameters Y")      # Verbose, not in production logs
logger.info("Tool X completed in 250ms")                # Progress tracking
logger.warning("Tool X timed out, using cached data")   # Issue but handled
logger.error("Tool X failed, aborting workflow")        # Critical, user impacted
logger.critical("Database unavailable, system degraded") # Infrastructure issue
```

### Metrics to Track

```
Tool Performance:
├─ tool_success_rate (% completing without error)
├─ tool_timeout_rate (% timing out)
├─ tool_error_rate (% raising exceptions)
└─ tool_average_latency_ms

Recovery Success:
├─ retry_success_rate (% recovered after retry)
├─ fallback_usage_rate (% using cached/simplified)
├─ workflow_success_rate (% completing end-to-end)
└─ workflow_abort_rate (% halting due to error)

User Experience:
├─ response_time_p50, p95, p99
├─ error_message_clarity (survey)
├─ false_positive_rate (users' perspective)
└─ mean_time_to_recovery (MTTR)
```

### Alert Conditions

```
CRITICAL ALERT (Immediate escalation):
├─ Database unavailable > 5 minutes
├─ Schedule generation failing for all requests
├─ >50% of schedules marked as "degraded"
└─ Multiple tool timeouts in succession

HIGH ALERT (Coordinator notification):
├─ Tool timeout rate > 10%
├─ Schedule compliance failures > 30%
├─ Burnout contagion spreading (Rt > 1.5)
└─ Contingency gaps > 20 blocks

MEDIUM ALERT (Log for trending):
├─ Single tool timeout (transient)
├─ Cache misses > 40%
├─ SPC rule violations
└─ Utilization trending upward
```

---

## Testing Error Paths

### Unit Test Template

```python
async def test_validate_schedule_timeout():
    """Test schedule validation timeout recovery."""

    with mock.patch('tool.validate_schedule') as mock_tool:
        # Simulate timeout
        mock_tool.side_effect = asyncio.TimeoutError()

        result = await call_tool_with_fallback(
            tool_func=mock_tool,
            tool_name="validate_schedule",
            args=[],
            timeout=1.0,
            allow_cached=True,
            critical=False,
        )

        # Assert fallback triggered
        assert result.degraded == True
        assert "cached" in result.source
        assert result.warning is not None

        # Assert retry attempted
        assert mock_tool.call_count >= 1


async def test_compliance_error_blocks_swap():
    """Test that compliance errors block swap execution."""

    # Setup: Schedule with 80-hour violation
    schedule = create_test_schedule(violations=["80_hour"])

    # Execute: Attempt swap
    result = await execute_swap(
        requester_id="RES-001",
        assignment_id="assign-001",
        candidate_id="RES-002",
    )

    # Assert: Blocked
    assert result.status == "BLOCKED"
    assert result.error_code == "COMPLIANCE_VIOLATION"
    assert "80_hour" in result.message
```

---

## Common Patterns

### Pattern 1: Retry with Exponential Backoff

```python
async def retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay_ms: int = 100,
    max_delay_ms: int = 5000,
):
    """Retry with exponential backoff."""
    delay_ms = initial_delay_ms
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                raise
            await asyncio.sleep(delay_ms / 1000)
            delay_ms = min(delay_ms * 2, max_delay_ms)
```

### Pattern 2: Cached Fallback

```python
async def get_with_cache_fallback(
    fetch_func,
    cache_key: str,
    max_age_hours: int = 24,
):
    """Fetch with cached fallback."""
    try:
        return await fetch_func()
    except Exception:
        cached = get_cache(cache_key)
        if cached and not is_stale(cached, max_age_hours):
            logger.warning(f"Using cached result for {cache_key}")
            return cached.data
        raise
```

### Pattern 3: Partial Success

```python
async def collect_results_with_partial_success(
    tasks: List[Coroutine],
    timeout_per_task: float = 5.0,
):
    """Collect results, allowing partial failures."""
    results = []
    for task in tasks:
        try:
            result = await asyncio.wait_for(task, timeout_per_task)
            results.append(("success", result))
        except asyncio.TimeoutError:
            results.append(("timeout", None))
        except Exception as e:
            results.append(("error", str(e)))
    return results
```

---

## References

- **WORKFLOW_SCHEDULE_GENERATION.md**: Phase-specific error handling
- **WORKFLOW_COMPLIANCE_CHECK.md**: Validation error handling
- **WORKFLOW_SWAP_EXECUTION.md**: Transaction error handling
- **WORKFLOW_RESILIENCE_ASSESSMENT.md**: Analytics error handling
- **Circuit Breaker Pattern**: defense_level integration

---

**Last Updated**: 2025-12-31
**Version**: 1.0
**Review Frequency**: Quarterly
