# Error Handling Workflow

Comprehensive error recovery strategies for MCP tool orchestration.

## Overview

MCP tools can fail for various reasons. This workflow provides systematic error classification, retry logic, fallback strategies, and escalation triggers.

## Error Classification

### Transient Errors (Retry)

Errors that are temporary and likely to succeed on retry:

| Error Type | Cause | Retry Strategy |
|------------|-------|----------------|
| **Connection Timeout** | Network latency, server load | 3 retries, exponential backoff |
| **Database Lock** | Concurrent transaction conflict | 3 retries, 100ms delay |
| **Rate Limit** | Too many requests | Wait + retry (use headers) |
| **Service Unavailable** | Backend restarting, health check | 3 retries, 2s delay |
| **Temporary Resource** | Celery queue full, Redis busy | 3 retries, 1s delay |

### Permanent Errors (Fail Fast)

Errors that will not succeed on retry:

| Error Type | Cause | Action |
|------------|-------|--------|
| **Invalid Input** | Schema validation failure | Return error to caller |
| **Resource Not Found** | schedule_id doesn't exist | Return error to caller |
| **Authentication Failed** | Invalid token/credentials | Escalate to human |
| **Permission Denied** | Insufficient privileges | Escalate to human |
| **Data Constraint Violation** | ACGME rule violated | Return error with suggestions |
| **Unimplemented Feature** | Tool not yet implemented | Route to alternative tool |

### Degraded Errors (Graceful Degradation)

Errors where partial functionality is acceptable:

| Error Type | Fallback Strategy |
|------------|-------------------|
| **Backend API Down** | Use cached data (compliance summary, schedule status) |
| **Celery Worker Offline** | Synchronous execution (if <30s), or fail gracefully |
| **MCP Server Degraded** | Skip non-critical tools, continue with essential tools |
| **Partial Data Available** | Return partial results with warning |

## Retry Logic

### Standard Retry Pattern

```python
import asyncio
from typing import Any, Callable, TypeVar

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    *args,
    **kwargs
) -> T:
    """
    Retry function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Backoff multiplier (2.0 = double each time)

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)

        except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    f"All {max_retries} retries failed for {func.__name__}: {e}"
                )
                raise

            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)

            logger.warning(
                f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                f"after {delay:.1f}s: {e}"
            )

            await asyncio.sleep(delay)

        except (ValueError, KeyError, TypeError) as e:
            # Permanent error - don't retry
            logger.error(f"Permanent error in {func.__name__}: {e}")
            raise

    # Should never reach here, but for type safety
    raise last_exception
```

### Tool-Specific Retry Configuration

```python
TOOL_RETRY_CONFIG = {
    # Core scheduling tools - moderate retry
    "validate_schedule_tool": {
        "max_retries": 3,
        "base_delay": 1.0,
        "retryable_errors": [ConnectionError, TimeoutError],
    },
    "detect_conflicts_tool": {
        "max_retries": 3,
        "base_delay": 1.0,
        "retryable_errors": [ConnectionError, TimeoutError],
    },

    # Background task tools - aggressive retry
    "start_background_task_tool": {
        "max_retries": 5,
        "base_delay": 0.5,
        "retryable_errors": [ConnectionError, TimeoutError, RuntimeError],
    },
    "get_task_status_tool": {
        "max_retries": 5,
        "base_delay": 0.5,
        "retryable_errors": [ConnectionError, TimeoutError],
    },

    # Deployment tools - conservative retry
    "promote_to_production_tool": {
        "max_retries": 1,  # Deployment should be idempotent but cautious
        "base_delay": 5.0,
        "retryable_errors": [ConnectionError],
    },

    # Read-only tools - aggressive retry
    "schedule_status_resource": {
        "max_retries": 5,
        "base_delay": 0.5,
        "retryable_errors": [ConnectionError, TimeoutError],
    },
}
```

### Usage Example

```python
from scheduler_mcp.server import mcp

async def call_tool_with_retry(tool_name: str, **params):
    """Call MCP tool with automatic retry logic."""

    tool = mcp.get_tool(tool_name)
    retry_config = TOOL_RETRY_CONFIG.get(tool_name, {
        "max_retries": 3,
        "base_delay": 1.0,
        "retryable_errors": [ConnectionError, TimeoutError],
    })

    return await retry_with_backoff(
        tool.fn,
        max_retries=retry_config["max_retries"],
        base_delay=retry_config["base_delay"],
        **params
    )
```

## Fallback Strategies

### Fallback Chain

Define fallback tools if primary tool fails:

```python
TOOL_FALLBACKS = {
    "validate_schedule_by_id_tool": [
        "validate_schedule_tool",  # Use date-range validation instead
    ],

    "analyze_swap_candidates_tool": [
        # If backend API fails, no fallback (returns empty candidates)
        None
    ],

    "check_utilization_threshold_tool": [
        # Use cached metrics if resilience framework unavailable
        "get_cached_utilization_metrics"
    ],

    "run_contingency_analysis_resilience_tool": [
        "run_contingency_analysis_tool",  # Use basic contingency analysis
    ],
}

async def call_with_fallback(primary_tool: str, fallback_tool: str | None, **params):
    """Call tool with fallback if primary fails."""

    try:
        return await call_tool_with_retry(primary_tool, **params)

    except Exception as e:
        logger.warning(
            f"Primary tool {primary_tool} failed: {e}. "
            f"Trying fallback: {fallback_tool}"
        )

        if fallback_tool is None:
            # No fallback available
            raise

        try:
            return await call_tool_with_retry(fallback_tool, **params)
        except Exception as fallback_error:
            logger.error(f"Fallback tool {fallback_tool} also failed: {fallback_error}")
            raise
```

### Cached Data Fallback

For read-only tools, use cached data if available:

```python
from datetime import datetime, timedelta
from typing import Any

CACHE: dict[str, tuple[datetime, Any]] = {}
CACHE_TTL = timedelta(minutes=5)

async def get_with_cache_fallback(tool_name: str, cache_key: str, **params):
    """Try tool, fallback to cache if failed."""

    try:
        result = await call_tool_with_retry(tool_name, **params)

        # Update cache on success
        CACHE[cache_key] = (datetime.now(), result)

        return result

    except Exception as e:
        logger.warning(f"Tool {tool_name} failed: {e}. Checking cache...")

        # Check cache
        if cache_key in CACHE:
            cached_time, cached_result = CACHE[cache_key]

            age = datetime.now() - cached_time
            if age < CACHE_TTL:
                logger.info(f"Using cached result (age: {age.total_seconds():.0f}s)")
                return cached_result
            else:
                logger.warning(f"Cached result too old ({age}). Raising error.")

        raise
```

## Error Logging Requirements

### Structured Error Logging

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def log_tool_error(
    tool_name: str,
    error: Exception,
    params: dict,
    retry_attempt: int | None = None,
    context: dict | None = None,
):
    """Log tool error with structured data."""

    error_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool_name": tool_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "params": params,
        "retry_attempt": retry_attempt,
        "context": context or {},
        "stack_trace": traceback.format_exc() if logger.level <= logging.DEBUG else None,
    }

    logger.error(f"Tool error: {json.dumps(error_record, indent=2)}")
```

### Error Metrics

Track error rates for monitoring:

```python
from collections import defaultdict

ERROR_METRICS = defaultdict(lambda: {
    "total_calls": 0,
    "total_errors": 0,
    "transient_errors": 0,
    "permanent_errors": 0,
    "retries_exhausted": 0,
})

def record_tool_call(tool_name: str, success: bool, error_type: str | None = None):
    """Record tool call for metrics."""

    metrics = ERROR_METRICS[tool_name]
    metrics["total_calls"] += 1

    if not success:
        metrics["total_errors"] += 1

        if error_type in ["ConnectionError", "TimeoutError"]:
            metrics["transient_errors"] += 1
        else:
            metrics["permanent_errors"] += 1

def get_error_rate(tool_name: str) -> float:
    """Calculate error rate for tool."""

    metrics = ERROR_METRICS[tool_name]
    if metrics["total_calls"] == 0:
        return 0.0

    return metrics["total_errors"] / metrics["total_calls"]
```

## Escalation Triggers

### When to Escalate to Human

Escalate immediately if:

1. **Critical production error**
   - `promote_to_production_tool` fails
   - `rollback_deployment_tool` fails
   - `execute_sacrifice_hierarchy_tool` (non-simulation) fails

2. **Security concern**
   - `run_security_scan_tool` detects critical vulnerabilities
   - Authentication/authorization errors

3. **Data integrity risk**
   - Database constraint violations
   - Schedule generation produces invalid schedule
   - ACGME compliance violations detected

4. **Repeated failures**
   - Same tool fails >5 times in 5 minutes
   - Error rate exceeds 50% for any tool
   - All fallbacks exhausted

### Escalation Procedure

```python
from enum import Enum

class EscalationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

async def escalate_error(
    level: EscalationLevel,
    tool_name: str,
    error: Exception,
    context: dict,
):
    """Escalate error to human operator."""

    escalation_message = {
        "level": level.value,
        "timestamp": datetime.utcnow().isoformat(),
        "tool_name": tool_name,
        "error": str(error),
        "context": context,
        "recommended_action": get_recommended_action(tool_name, error),
    }

    # Log with appropriate severity
    if level == EscalationLevel.EMERGENCY:
        logger.critical(f"EMERGENCY ESCALATION: {json.dumps(escalation_message)}")
        # Send alert via monitoring system
        await send_alert(escalation_message)

    elif level == EscalationLevel.CRITICAL:
        logger.error(f"CRITICAL ESCALATION: {json.dumps(escalation_message)}")
        await send_alert(escalation_message)

    elif level == EscalationLevel.WARNING:
        logger.warning(f"WARNING ESCALATION: {json.dumps(escalation_message)}")

    else:
        logger.info(f"INFO ESCALATION: {json.dumps(escalation_message)}")


def get_recommended_action(tool_name: str, error: Exception) -> str:
    """Get recommended human action for error."""

    if tool_name == "promote_to_production_tool":
        return (
            "1. Check deployment logs\n"
            "2. Verify staging smoke tests passed\n"
            "3. Check for open incidents\n"
            "4. Consider manual deployment or rollback"
        )

    if tool_name == "run_security_scan_tool":
        return (
            "1. Review detected vulnerabilities\n"
            "2. Check CVE database for severity\n"
            "3. Plan patching strategy\n"
            "4. Block deployment if critical vulnerabilities"
        )

    if isinstance(error, ValueError):
        return (
            "1. Review input parameters\n"
            "2. Check API documentation\n"
            "3. Verify data format matches schema"
        )

    return "Review error logs and tool documentation"
```

## Error Handling Examples

### Example 1: Handle Validation Error

```python
try:
    result = await call_tool_with_retry(
        "validate_schedule_tool",
        start_date="2025-01-01",
        end_date="2025-01-31",
    )

    if not result.is_valid:
        logger.warning(
            f"Schedule validation failed: {result.critical_issues} critical issues"
        )

        # Non-exception failure - handle gracefully
        return {
            "status": "validation_failed",
            "issues": result.issues,
            "recommended_fixes": [issue.suggested_fix for issue in result.issues],
        }

except ValueError as e:
    # Invalid input - permanent error
    logger.error(f"Invalid validation parameters: {e}")
    return {"status": "error", "message": str(e)}

except ConnectionError as e:
    # Transient error - retries already attempted
    logger.error(f"Backend unreachable after retries: {e}")
    await escalate_error(
        EscalationLevel.CRITICAL,
        "validate_schedule_tool",
        e,
        {"start_date": "2025-01-01", "end_date": "2025-01-31"},
    )
    raise
```

### Example 2: Handle Background Task Failure

```python
try:
    # Start background task
    task_result = await call_tool_with_retry(
        "start_background_task_tool",
        task_type="resilience_contingency",
        params={"days_ahead": 90},
    )

    task_id = task_result.task_id

    # Poll for completion
    max_polls = 60  # 5 minutes with 5s delay
    for poll in range(max_polls):
        await asyncio.sleep(5)

        status = await call_tool_with_retry(
            "get_task_status_tool",
            task_id=task_id,
        )

        if status.status == "success":
            return status.result

        elif status.status == "failure":
            logger.error(f"Background task failed: {status.error}")

            # Try to cancel any related tasks
            await call_tool_with_retry("cancel_task_tool", task_id=task_id)

            # Escalate
            await escalate_error(
                EscalationLevel.WARNING,
                "start_background_task_tool",
                RuntimeError(status.error),
                {"task_type": "resilience_contingency", "task_id": task_id},
            )
            raise RuntimeError(f"Task failed: {status.error}")

    # Timeout - task still running
    logger.warning(f"Task {task_id} timeout after 5 minutes")
    return {"status": "timeout", "task_id": task_id}

except Exception as e:
    logger.error(f"Failed to start background task: {e}")
    raise
```

### Example 3: Handle Deployment Error with Rollback

```python
async def safe_production_deployment(staging_version: str, approval_token: str):
    """Deploy to production with automatic rollback on failure."""

    deployment_id = None

    try:
        # Promote to production
        promote_result = await call_tool_with_retry(
            "promote_to_production_tool",
            staging_version=staging_version,
            approval_token=approval_token,
            dry_run=False,
        )

        deployment_id = promote_result.deployment_id

        # Monitor deployment
        for _ in range(10):  # Check for 5 minutes
            await asyncio.sleep(30)

            status = await call_tool_with_retry(
                "get_deployment_status_tool",
                deployment_id=deployment_id,
            )

            if status.deployment.status == "success":
                logger.info(f"Deployment {deployment_id} succeeded")
                return {"status": "success", "deployment_id": deployment_id}

            elif status.deployment.status == "failure":
                logger.error(f"Deployment {deployment_id} failed")
                raise RuntimeError("Deployment failed during execution")

        # Still in progress
        return {"status": "in_progress", "deployment_id": deployment_id}

    except Exception as e:
        logger.error(f"Deployment error: {e}")

        if deployment_id:
            # Attempt automatic rollback
            logger.warning(f"Attempting rollback of deployment {deployment_id}")

            try:
                rollback_result = await call_tool_with_retry(
                    "rollback_deployment_tool",
                    environment="production",
                    reason=f"Automatic rollback due to deployment failure: {e}",
                    dry_run=False,
                )

                logger.info(f"Rollback initiated: {rollback_result.status}")

            except Exception as rollback_error:
                # Rollback failed - EMERGENCY
                await escalate_error(
                    EscalationLevel.EMERGENCY,
                    "rollback_deployment_tool",
                    rollback_error,
                    {
                        "deployment_id": deployment_id,
                        "original_error": str(e),
                    },
                )
                raise

        # Re-raise original error
        raise
```

## Best Practices

1. **Classify errors before retrying** - Don't retry permanent errors
2. **Use exponential backoff** - Avoid thundering herd
3. **Limit retry attempts** - Fail fast on persistent issues
4. **Log all errors** - Structured logging for debugging
5. **Monitor error rates** - Track metrics for each tool
6. **Escalate appropriately** - Critical errors need human attention
7. **Implement circuit breakers** - Stop calling failing tools
8. **Cache when possible** - Reduce load on struggling services
9. **Test error paths** - Ensure error handling actually works
10. **Document known issues** - See `../Reference/tool-error-patterns.md`

## Related Files

- `tool-composition.md` - Error propagation in tool chains
- `../Reference/tool-error-patterns.md` - Known failure modes by tool
- `../Reference/composition-examples.md` - Error handling in workflows
