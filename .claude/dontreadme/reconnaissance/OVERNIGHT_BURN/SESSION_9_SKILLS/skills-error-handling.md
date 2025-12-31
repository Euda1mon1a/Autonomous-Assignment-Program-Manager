***REMOVED*** Skills Error Handling Patterns & Recovery Strategies
***REMOVED******REMOVED*** Comprehensive Documentation for Autonomous Skill Operation

**Purpose:** Document all error handling patterns, recovery strategies, retry configuration, and user feedback mechanisms for reliable skill autonomy.

**Last Updated:** 2025-12-30
**Scope:** Error handling across 73+ skills, MCP orchestration, swap execution, ACGME validation, and resilience framework.

---

***REMOVED******REMOVED*** Table of Contents

1. [Error Pattern Classification](***REMOVED***error-pattern-classification)
2. [Transient vs Permanent Errors](***REMOVED***transient-vs-permanent-errors)
3. [Retry Strategy Framework](***REMOVED***retry-strategy-framework)
4. [Fallback & Degradation](***REMOVED***fallback--degradation)
5. [Error Logging & Metrics](***REMOVED***error-logging--metrics)
6. [Escalation Triggers](***REMOVED***escalation-triggers)
7. [User Feedback Patterns](***REMOVED***user-feedback-patterns)
8. [Recovery Strategies by Domain](***REMOVED***recovery-strategies-by-domain)
9. [Swallowed Error Detection](***REMOVED***swallowed-error-detection)
10. [Error Granularity](***REMOVED***error-granularity)
11. [Testing Error Paths](***REMOVED***testing-error-paths)
12. [Monitoring Dashboard](***REMOVED***monitoring-dashboard)

---

***REMOVED******REMOVED*** Error Pattern Classification

***REMOVED******REMOVED******REMOVED*** PERCEPTION: Current Error Landscape

Skills encounter **8 major error categories**:

| Category | Frequency | Severity | Recovery |
|----------|-----------|----------|----------|
| **Connection Errors** | Common | Medium | Retry with backoff |
| **Validation Errors** | Common | Low | Return to user |
| **Timeout Errors** | Occasional | High | Async task + polling |
| **Database Errors** | Occasional | High | Retry or rollback |
| **Authorization Errors** | Rare | Critical | Escalate immediately |
| **Data Integrity Errors** | Rare | Critical | Rollback + alert |
| **Resource Exhaustion** | Rare | High | Queue + retry |
| **Configuration Errors** | Very Rare | Critical | Manual intervention |

***REMOVED******REMOVED******REMOVED*** INVESTIGATION: Error Propagation Path

```
User Request
    ↓
Skill Entry Point (error-aware)
    ↓
API Call / Database Query / Service Operation
    ↓
Error Occurs
    ↓
Error Classifier (transient vs permanent)
    ↓
Recovery Strategy Application
    ├─ Retry (if transient)
    ├─ Fallback (if available)
    ├─ Degrade (if partial acceptable)
    ├─ Escalate (if critical)
    └─ Report (always)
    ↓
User Feedback
```

---

***REMOVED******REMOVED*** Transient vs Permanent Errors

***REMOVED******REMOVED******REMOVED*** ARCANA: Error Handling Patterns

***REMOVED******REMOVED******REMOVED******REMOVED*** Transient Errors (Retry)

**Definition:** Errors that are temporary and likely to succeed on retry.

```python
***REMOVED*** Transient error classification
TRANSIENT_ERRORS = {
    ConnectionError: {
        "max_retries": 3,
        "base_delay": 1.0,
        "backoff": "exponential",
        "reason": "Network latency, server temporarily unavailable"
    },
    asyncio.TimeoutError: {
        "max_retries": 3,
        "base_delay": 2.0,
        "backoff": "exponential",
        "reason": "Service under load, slow response"
    },
    RuntimeError: {
        "max_retries": 5,
        "base_delay": 0.5,
        "backoff": "exponential",
        "reason": "Celery queue full, worker busy"
    },
    sqlalchemy.exc.OperationalError: {
        "max_retries": 5,
        "base_delay": 0.5,
        "backoff": "exponential",
        "reason": "Database lock contention, connection lost"
    }
}
```

**Signal Examples:**
- `TimeoutError: Request timed out after 30s`
- `ConnectionError: Failed to connect to http://backend:8000`
- `OperationalError: database is locked`
- `ConnectionError: No active Celery workers found`

***REMOVED******REMOVED******REMOVED******REMOVED*** Permanent Errors (Fail Fast)

**Definition:** Errors that will not succeed on retry - respond immediately.

```python
***REMOVED*** Permanent error classification
PERMANENT_ERRORS = {
    ValueError: {
        "action": "return_error",
        "reason": "Input validation failed - data structure issue"
    },
    KeyError: {
        "action": "return_error",
        "reason": "Required data missing - impossible to retry"
    },
    TypeError: {
        "action": "return_error",
        "reason": "Type mismatch - code issue, not environment"
    },
    HTTPError_404: {
        "action": "return_error",
        "reason": "Resource not found - retry won't help"
    },
    HTTPError_401: {
        "action": "escalate",
        "reason": "Authentication failed - human intervention needed"
    },
    HTTPError_403: {
        "action": "escalate",
        "reason": "Permission denied - authorization issue"
    },
    ConstraintViolationError: {
        "action": "escalate",
        "reason": "ACGME rule violated - requires human decision"
    }
}
```

**Signal Examples:**
- `ValueError: Invalid constraint_config must be one of ['default', 'minimal', 'strict']`
- `KeyError: 'schedule_id' required`
- `HTTPError: 404 Not Found`
- `ConstraintViolationError: 80-hour violation would occur`

***REMOVED******REMOVED******REMOVED******REMOVED*** Degraded Errors (Graceful Degradation)

**Definition:** Errors where partial functionality is acceptable.

```python
***REMOVED*** Degraded error handling
DEGRADED_ERRORS = {
    "backend_api_timeout": {
        "fallback": "use_cached_data",
        "caching_strategy": "last_24h_cache",
        "user_feedback": "Using cached data - limited real-time accuracy"
    },
    "celery_worker_offline": {
        "fallback": "sync_execution_if_under_30s",
        "timeout": 30,
        "user_feedback": "Processing synchronously - may take longer"
    },
    "partial_data_available": {
        "fallback": "return_partial_with_warning",
        "severity": "warning",
        "user_feedback": "Some data unavailable - showing available results"
    }
}
```

---

***REMOVED******REMOVED*** Retry Strategy Framework

***REMOVED******REMOVED******REMOVED*** HISTORY: Error Recovery Evolution

***REMOVED******REMOVED******REMOVED******REMOVED*** Standard Exponential Backoff Pattern

```python
import asyncio
from typing import TypeVar, Callable, Any

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    *args,
    **kwargs
) -> T:
    """
    Retry async function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Cap on delay between retries (default: 30.0)
        exponential_base: Backoff multiplier (default: 2.0)
        jitter: Add randomness to prevent thundering herd (default: True)

    Returns:
        Function result

    Raises:
        Last exception if all retries fail

    Example:
        result = await retry_with_backoff(
            validate_schedule,
            max_retries=3,
            base_delay=1.0,
            schedule_id="sched-123"
        )
    """
    import random
    import logging

    logger = logging.getLogger(__name__)
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

            ***REMOVED*** Calculate delay with exponential backoff
            delay = base_delay * (exponential_base ** attempt)

            ***REMOVED*** Cap at max_delay
            delay = min(delay, max_delay)

            ***REMOVED*** Add jitter (±10% randomness)
            if jitter:
                jitter_amount = delay * 0.1
                delay = delay + random.uniform(-jitter_amount, jitter_amount)

            logger.warning(
                f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                f"after {delay:.2f}s: {type(e).__name__}: {e}"
            )

            await asyncio.sleep(delay)

        except (ValueError, KeyError, TypeError) as e:
            ***REMOVED*** Permanent error - don't retry
            logger.error(
                f"Permanent error in {func.__name__}: {type(e).__name__}: {e}"
            )
            raise

    ***REMOVED*** Should never reach here, but for type safety
    if last_exception:
        raise last_exception
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Tool-Specific Retry Configuration

```python
***REMOVED*** Configuration for each skill/tool
TOOL_RETRY_CONFIG = {
    ***REMOVED*** Core validation tools - moderate retry
    "validate_schedule_tool": {
        "max_retries": 3,
        "base_delay": 1.0,
        "retryable_errors": [ConnectionError, asyncio.TimeoutError],
        "rationale": "Validation is often slow but eventually succeeds"
    },

    ***REMOVED*** Background task tools - aggressive retry
    "start_background_task_tool": {
        "max_retries": 5,
        "base_delay": 0.5,
        "retryable_errors": [ConnectionError, asyncio.TimeoutError, RuntimeError],
        "rationale": "Task queuing can be transient, workers may be restarting"
    },

    ***REMOVED*** Deployment tools - conservative retry
    "promote_to_production_tool": {
        "max_retries": 1,
        "base_delay": 5.0,
        "retryable_errors": [ConnectionError],
        "rationale": "Deployment should be idempotent but we retry cautiously"
    },

    ***REMOVED*** Read-only tools - aggressive retry
    "schedule_status_resource": {
        "max_retries": 5,
        "base_delay": 0.5,
        "retryable_errors": [ConnectionError, asyncio.TimeoutError],
        "rationale": "Safe to retry, no side effects"
    },

    ***REMOVED*** ACGME validation - moderate retry
    "check_compliance_tool": {
        "max_retries": 3,
        "base_delay": 1.0,
        "retryable_errors": [ConnectionError, asyncio.TimeoutError],
        "rationale": "Compliance checks may timeout on large schedules"
    }
}

def get_retry_config(tool_name: str) -> dict:
    """Get retry configuration for tool."""
    return TOOL_RETRY_CONFIG.get(tool_name, {
        "max_retries": 3,
        "base_delay": 1.0,
        "retryable_errors": [ConnectionError, asyncio.TimeoutError],
    })
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Retry Loop with Circuit Breaker

```python
from enum import Enum
from datetime import datetime, timedelta
import logging

class CircuitState(Enum):
    CLOSED = "closed"      ***REMOVED*** Normal operation
    OPEN = "open"          ***REMOVED*** Failing, reject requests
    HALF_OPEN = "half_open"  ***REMOVED*** Testing if recovered

class CircuitBreaker:
    """Prevent cascading failures by breaking circuits."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        logger = logging.getLogger(__name__)

        if self.state == CircuitState.OPEN:
            ***REMOVED*** Check if recovery timeout has elapsed
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                logger.warning(f"Circuit entering HALF_OPEN state for {func.__name__}")
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError(f"Circuit OPEN for {func.__name__}. Try again later.")

        try:
            result = await func(*args, **kwargs)

            ***REMOVED*** Success - reset circuit
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit CLOSED for {func.__name__} (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit OPEN for {func.__name__}: "
                    f"{self.failure_count} failures in {self.recovery_timeout}s"
                )
                self.state = CircuitState.OPEN

            raise

***REMOVED*** Usage
schedule_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

async def validate_schedule_safe(schedule_id: str):
    """Validate with circuit breaker protection."""
    return await schedule_breaker.call(
        validate_schedule_tool,
        schedule_id=schedule_id
    )
```

---

***REMOVED******REMOVED*** Fallback & Degradation

***REMOVED******REMOVED******REMOVED*** INSIGHT: Graceful Degradation Philosophy

**Core Principle:** If primary path fails, use secondary path rather than complete failure.

***REMOVED******REMOVED******REMOVED******REMOVED*** Fallback Chain Pattern

```python
TOOL_FALLBACKS = {
    "validate_schedule_by_id_tool": {
        "fallbacks": ["validate_schedule_tool"],
        "description": "Fall back to date-range validation"
    },

    "check_utilization_threshold_tool": {
        "fallbacks": ["get_cached_utilization_metrics"],
        "description": "Use cached metrics if real-time unavailable"
    },

    "run_contingency_analysis_resilience_tool": {
        "fallbacks": ["run_contingency_analysis_tool"],
        "description": "Use basic contingency analysis if resilience unavailable"
    },

    "analyze_swap_candidates_tool": {
        "fallbacks": [],  ***REMOVED*** No fallback available
        "description": "Returns empty candidates if backend down"
    }
}

async def call_with_fallback(
    primary_tool: str,
    fallback_tools: list[str] | None = None,
    **params
) -> dict:
    """
    Call tool with automatic fallback chain.

    Args:
        primary_tool: Primary tool to try
        fallback_tools: List of fallback tools in order
        **params: Tool parameters

    Returns:
        Result from successful tool call

    Raises:
        Exception: If all tools fail
    """
    import logging

    logger = logging.getLogger(__name__)

    ***REMOVED*** Get fallbacks from config if not provided
    if fallback_tools is None:
        fallback_tools = TOOL_FALLBACKS.get(primary_tool, {}).get("fallbacks", [])

    tools_to_try = [primary_tool] + fallback_tools

    for i, tool_name in enumerate(tools_to_try):
        try:
            logger.info(f"Attempting tool: {tool_name}")

            result = await call_tool_with_retry(tool_name, **params)

            if i > 0:
                logger.warning(
                    f"Fallback used: {tool_name} (primary {primary_tool} failed)"
                )

            return {
                "success": True,
                "tool_used": tool_name,
                "result": result,
                "fallback_used": i > 0
            }

        except Exception as e:
            logger.warning(f"Tool {tool_name} failed: {type(e).__name__}: {e}")

            if i == len(tools_to_try) - 1:
                ***REMOVED*** Last tool failed
                logger.error(f"All tools failed: {[t for t in tools_to_try]}")
                raise

    raise RuntimeError(f"No tools available: {tools_to_try}")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Cached Data Fallback

```python
from datetime import datetime, timedelta
from typing import Any
import logging

logger = logging.getLogger(__name__)

CACHE: dict[str, tuple[datetime, Any]] = {}
CACHE_TTL = timedelta(minutes=5)
CACHE_STALE_WARNING = timedelta(minutes=10)

async def get_with_cache_fallback(
    tool_name: str,
    cache_key: str,
    cache_ttl: timedelta = CACHE_TTL,
    **params
) -> dict:
    """
    Try tool, fallback to cache if failed.

    Args:
        tool_name: Tool to call
        cache_key: Cache key for results
        cache_ttl: Cache validity period
        **params: Tool parameters

    Returns:
        Result dict with cache_hit, cache_age fields
    """
    try:
        ***REMOVED*** Try to get fresh data
        result = await call_tool_with_retry(tool_name, **params)

        ***REMOVED*** Update cache on success
        CACHE[cache_key] = (datetime.now(), result)

        return {
            "success": True,
            "data": result,
            "cache_hit": False,
            "cache_age": None,
            "tool": tool_name
        }

    except Exception as e:
        logger.warning(
            f"Tool {tool_name} failed: {type(e).__name__}. "
            f"Checking cache for {cache_key}"
        )

        ***REMOVED*** Check cache
        if cache_key not in CACHE:
            logger.error(f"Cache miss for {cache_key}")
            raise

        cached_time, cached_result = CACHE[cache_key]
        age = datetime.now() - cached_time

        ***REMOVED*** Check if cache is still valid
        if age < cache_ttl:
            logger.info(
                f"Using cached result for {cache_key} "
                f"(age: {age.total_seconds():.0f}s)"
            )
            return {
                "success": True,
                "data": cached_result,
                "cache_hit": True,
                "cache_age": age.total_seconds(),
                "cache_status": "fresh",
                "tool": f"{tool_name} (cached)"
            }

        elif age < CACHE_STALE_WARNING:
            logger.warning(
                f"Using stale cached result for {cache_key} "
                f"(age: {age.total_seconds():.0f}s, limit: {cache_ttl.total_seconds():.0f}s)"
            )
            return {
                "success": True,
                "data": cached_result,
                "cache_hit": True,
                "cache_age": age.total_seconds(),
                "cache_status": "stale",
                "warning": "Cached data is stale",
                "tool": f"{tool_name} (stale cache)"
            }

        else:
            logger.error(
                f"Cached result for {cache_key} too old "
                f"({age.total_seconds():.0f}s > {CACHE_STALE_WARNING.total_seconds():.0f}s)"
            )
            raise RuntimeError(
                f"Tool failed and cached data is stale. "
                f"Last cache update: {(age.total_seconds() / 60):.0f} minutes ago"
            )
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Partial Results with Degradation

```python
async def get_with_partial_degradation(
    tool_name: str,
    required_fields: list[str],
    optional_fields: list[str] = None,
    **params
) -> dict:
    """
    Accept partial results if required fields available.

    Args:
        tool_name: Tool to call
        required_fields: Fields that must be present
        optional_fields: Fields that are nice-to-have
        **params: Tool parameters

    Returns:
        Result with degradation_level field
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        result = await call_tool_with_retry(tool_name, **params)
        return {
            "success": True,
            "data": result,
            "degradation_level": "none",
            "missing_fields": []
        }

    except Exception as e:
        logger.warning(f"Tool {tool_name} failed: {e}")

        ***REMOVED*** Try partial execution or cached partial data
        try:
            partial_result = await get_partial_data(tool_name, required_fields, **params)

            ***REMOVED*** Check if required fields present
            missing = [f for f in required_fields if f not in partial_result]

            if not missing:
                logger.warning(
                    f"Returning partial results from {tool_name}. "
                    f"Missing optional fields: {[f for f in (optional_fields or []) if f not in partial_result]}"
                )
                return {
                    "success": True,
                    "data": partial_result,
                    "degradation_level": "partial",
                    "missing_fields": [f for f in (optional_fields or []) if f not in partial_result]
                }
            else:
                logger.error(
                    f"Required fields missing: {missing}. "
                    f"Cannot return partial results."
                )
                raise

        except Exception as partial_error:
            logger.error(f"Partial fallback also failed: {partial_error}")
            raise RuntimeError(
                f"Tool {tool_name} failed. "
                f"Partial fallback: {partial_error}"
            )
```

---

***REMOVED******REMOVED*** Error Logging & Metrics

***REMOVED******REMOVED******REMOVED*** RELIGION: All Errors Handled?

**Principle:** Every error must be logged, classified, and tracked.

***REMOVED******REMOVED******REMOVED******REMOVED*** Structured Error Logging

```python
import logging
import json
import traceback
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

def log_tool_error(
    tool_name: str,
    error: Exception,
    params: dict,
    retry_attempt: int | None = None,
    context: dict | None = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
):
    """
    Log tool error with structured data.

    Args:
        tool_name: Name of tool that failed
        error: Exception object
        params: Tool parameters
        retry_attempt: Retry number (if retrying)
        context: Additional context (user_id, session_id, etc.)
        severity: Error severity level
    """
    error_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "tool_name": tool_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_classification": classify_error(error),
        "params": sanitize_params(params),  ***REMOVED*** Remove sensitive data
        "retry_attempt": retry_attempt,
        "context": context or {},
        "stack_trace": traceback.format_exc() if logger.level <= logging.DEBUG else None,
        "severity": severity.value
    }

    ***REMOVED*** Log based on severity
    if severity == ErrorSeverity.CRITICAL:
        logger.critical(f"Tool error: {json.dumps(error_record, indent=2)}")
    elif severity == ErrorSeverity.ERROR:
        logger.error(f"Tool error: {json.dumps(error_record, indent=2)}")
    elif severity == ErrorSeverity.WARNING:
        logger.warning(f"Tool warning: {json.dumps(error_record, indent=2)}")
    else:
        logger.info(f"Tool info: {json.dumps(error_record, indent=2)}")

def classify_error(error: Exception) -> str:
    """Classify error for monitoring."""
    if isinstance(error, ConnectionError):
        return "transient_connection"
    elif isinstance(error, asyncio.TimeoutError):
        return "transient_timeout"
    elif isinstance(error, ValueError):
        return "permanent_validation"
    elif isinstance(error, KeyError):
        return "permanent_missing_data"
    else:
        return "unknown"

def sanitize_params(params: dict) -> dict:
    """Remove sensitive data from params before logging."""
    sensitive_keys = {"password", "token", "secret", "api_key", "auth"}
    sanitized = {}

    for key, value in params.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value

    return sanitized
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Metrics Tracking

```python
from collections import defaultdict
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ToolMetrics:
    """Track metrics for tool execution."""

    def __init__(self):
        self.metrics = defaultdict(lambda: {
            "total_calls": 0,
            "total_errors": 0,
            "transient_errors": 0,
            "permanent_errors": 0,
            "retries_exhausted": 0,
            "fallback_used": 0,
            "degradation_used": 0,
            "total_duration_ms": 0,
            "error_rate_percent": 0.0,
            "avg_retry_count": 0.0
        })
        self.call_durations = defaultdict(list)
        self.retry_counts = defaultdict(list)

    def record_call(
        self,
        tool_name: str,
        success: bool,
        error_type: str | None = None,
        duration_ms: int = 0,
        retry_count: int = 0,
        fallback_used: bool = False,
        degradation_used: bool = False
    ):
        """Record tool call for metrics."""
        metrics = self.metrics[tool_name]
        metrics["total_calls"] += 1
        metrics["total_duration_ms"] += duration_ms

        if retry_count > 0:
            self.retry_counts[tool_name].append(retry_count)
            metrics["avg_retry_count"] = sum(self.retry_counts[tool_name]) / len(self.retry_counts[tool_name])

        if not success:
            metrics["total_errors"] += 1

            if error_type in ["ConnectionError", "TimeoutError"]:
                metrics["transient_errors"] += 1
            else:
                metrics["permanent_errors"] += 1

        if fallback_used:
            metrics["fallback_used"] += 1

        if degradation_used:
            metrics["degradation_used"] += 1

        ***REMOVED*** Update error rate
        if metrics["total_calls"] > 0:
            metrics["error_rate_percent"] = (metrics["total_errors"] / metrics["total_calls"]) * 100

    def get_metrics(self, tool_name: str) -> dict:
        """Get current metrics for tool."""
        return self.metrics[tool_name]

    def get_health_summary(self) -> dict:
        """Get overall health summary."""
        total_calls = sum(m["total_calls"] for m in self.metrics.values())
        total_errors = sum(m["total_errors"] for m in self.metrics.values())

        ***REMOVED*** Find unhealthy tools
        unhealthy = [
            (name, m["error_rate_percent"])
            for name, m in self.metrics.items()
            if m["error_rate_percent"] > 5.0  ***REMOVED*** >5% error rate
        ]

        return {
            "total_tools": len(self.metrics),
            "total_calls": total_calls,
            "total_errors": total_errors,
            "overall_error_rate_percent": (total_errors / total_calls * 100) if total_calls > 0 else 0,
            "healthy_tools": len(self.metrics) - len(unhealthy),
            "unhealthy_tools": unhealthy,
            "avg_call_duration_ms": sum(m["total_duration_ms"] for m in self.metrics.values()) / total_calls if total_calls > 0 else 0
        }

***REMOVED*** Global metrics instance
tool_metrics = ToolMetrics()

def record_tool_metrics(tool_name: str, **kwargs):
    """Record metrics for tool call."""
    tool_metrics.record_call(tool_name, **kwargs)

def get_tool_health():
    """Get tool health summary."""
    return tool_metrics.get_health_summary()
```

---

***REMOVED******REMOVED*** Escalation Triggers

***REMOVED******REMOVED******REMOVED*** NATURE: Error Granularity & Severity

**Escalation Decision Tree:**

```
Error Occurs
    │
    ├─ Transient? (timeout, connection)
    │   └─ Retry with backoff → Success? → Return
    │   └─ Retries exhausted? → Escalate MEDIUM
    │
    ├─ Validation Error? (invalid input)
    │   └─ Return error to user → No escalation
    │
    ├─ Critical Production Error? (deployment failure, data loss risk)
    │   └─ Escalate CRITICAL → Human decision → Rollback
    │
    ├─ Compliance Violation? (ACGME, security)
    │   └─ Escalate CRITICAL → Block operation
    │
    ├─ Authorization Error? (auth failed, permission denied)
    │   └─ Escalate CRITICAL → Log security event
    │
    └─ Repeated Failures? (same tool >5 times in 5min)
        └─ Escalate MEDIUM → Enable circuit breaker
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Escalation Levels

```python
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EscalationLevel(str, Enum):
    INFO = "info"              ***REMOVED*** Log only
    WARNING = "warning"         ***REMOVED*** Log + monitoring alert
    CRITICAL = "critical"       ***REMOVED*** Alert + human required
    EMERGENCY = "emergency"     ***REMOVED*** Immediate human + incident ticket

async def escalate_error(
    level: EscalationLevel,
    tool_name: str,
    error: Exception,
    context: dict,
    recommended_actions: list[str] | None = None
):
    """
    Escalate error to human operator.

    Args:
        level: Escalation severity level
        tool_name: Tool that failed
        error: Exception object
        context: Operation context
        recommended_actions: Suggested fixes
    """
    escalation_message = {
        "level": level.value,
        "timestamp": datetime.utcnow().isoformat(),
        "tool_name": tool_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "recommended_actions": recommended_actions or []
    }

    if level == EscalationLevel.EMERGENCY:
        logger.critical(f"EMERGENCY ESCALATION: {json.dumps(escalation_message)}")
        await send_pagerduty_alert(escalation_message)
        await create_incident_ticket(escalation_message)

    elif level == EscalationLevel.CRITICAL:
        logger.error(f"CRITICAL ESCALATION: {json.dumps(escalation_message)}")
        await send_slack_alert(escalation_message, channel="***REMOVED***critical-alerts")
        await create_incident_ticket(escalation_message)

    elif level == EscalationLevel.WARNING:
        logger.warning(f"WARNING ESCALATION: {json.dumps(escalation_message)}")
        await send_slack_alert(escalation_message, channel="***REMOVED***warnings")

    else:
        logger.info(f"INFO: {json.dumps(escalation_message)}")

def get_recommended_action(tool_name: str, error: Exception) -> list[str]:
    """Get recommended human actions for error."""
    actions = []

    ***REMOVED*** Tool-specific recommendations
    if tool_name == "promote_to_production_tool":
        actions = [
            "1. Check deployment logs for details",
            "2. Verify staging smoke tests passed",
            "3. Check for open security incidents",
            "4. Decide: retry deployment or rollback?"
        ]

    elif tool_name == "run_security_scan_tool":
        actions = [
            "1. Review detected vulnerabilities in scan report",
            "2. Check CVE database for severity",
            "3. Plan patching strategy",
            "4. Block deployment if critical vulnerabilities found"
        ]

    elif "validate" in tool_name:
        actions = [
            "1. Check validation error details",
            "2. Review violated constraints",
            "3. Modify schedule to satisfy constraints",
            "4. Re-run validation"
        ]

    ***REMOVED*** Error-type recommendations
    if isinstance(error, ConnectionError):
        actions.append("Check backend service status - may be down or overloaded")
    elif isinstance(error, asyncio.TimeoutError):
        actions.append("Operation timed out - may need to split into smaller chunks")
    elif isinstance(error, ValueError):
        actions.append("Review input parameters - check API documentation")

    return actions or ["Review error logs and contact support"]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Escalation Criteria

```python
class EscalationCriteria:
    """Determine when to escalate errors."""

    ***REMOVED*** Critical errors - escalate immediately
    CRITICAL_PATTERNS = [
        r".*production.*failed",
        r".*deployment.*failed",
        r".*rollback.*failed",
        r".*data.*corruption",
        r".*ACGME.*critical.*violation",
        r".*security.*critical",
        r".*database.*deadlock.*repeated"
    ]

    ***REMOVED*** Escalation thresholds
    ERROR_RATE_THRESHOLD = 0.05  ***REMOVED*** 5% error rate = escalate
    REPEATED_FAILURE_THRESHOLD = 5  ***REMOVED*** Same error >5 times = escalate
    REPEATED_FAILURE_WINDOW = 300  ***REMOVED*** Within 5 minutes

    @staticmethod
    def should_escalate_immediate(error: Exception, tool_name: str) -> bool:
        """Check if error requires immediate escalation."""
        import re

        error_str = f"{tool_name}: {str(error)}".lower()

        for pattern in EscalationCriteria.CRITICAL_PATTERNS:
            if re.search(pattern, error_str, re.IGNORECASE):
                return True

        ***REMOVED*** Authorization errors always escalate
        if isinstance(error, (PermissionError, AuthenticationError)):
            return True

        return False

    @staticmethod
    def should_escalate_due_to_rate(error_rate: float) -> bool:
        """Check if escalate due to error rate."""
        return error_rate > EscalationCriteria.ERROR_RATE_THRESHOLD

    @staticmethod
    def should_escalate_due_to_repeated(
        tool_name: str,
        recent_errors: list[tuple[datetime, Exception]]
    ) -> bool:
        """Check if escalate due to repeated failures."""
        from datetime import timedelta

        now = datetime.now()
        recent_window = [
            e for e in recent_errors
            if now - e[0] < timedelta(seconds=EscalationCriteria.REPEATED_FAILURE_WINDOW)
        ]

        return len(recent_window) >= EscalationCriteria.REPEATED_FAILURE_THRESHOLD
```

---

***REMOVED******REMOVED*** User Feedback Patterns

***REMOVED******REMOVED******REMOVED*** MEDICINE: Recovery Context & Communication

**Core Principle:** Users need to understand what happened and what's being done about it.

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Response Structure

```python
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class ErrorResponse:
    """Structured error response for skill execution failures."""

    ***REMOVED*** Required
    success: bool = False
    error_type: str  ***REMOVED*** e.g., "validation_error", "timeout", "permission_denied"
    message: str     ***REMOVED*** User-friendly message

    ***REMOVED*** Contextual
    details: Optional[dict] = None      ***REMOVED*** Technical details (optional)
    recovery_options: Optional[list[str]] = None  ***REMOVED*** What user can do
    retry_eligible: bool = False        ***REMOVED*** Can skill retry?
    retry_info: Optional[dict] = None   ***REMOVED*** When retry will happen
    escalated: bool = False             ***REMOVED*** Has this been escalated?

    ***REMOVED*** Operational
    tool_name: Optional[str] = None
    execution_time_ms: int = 0
    retry_count: int = 0

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "success": self.success,
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
            "recovery_options": self.recovery_options,
            "retry_eligible": self.retry_eligible,
            "retry_info": self.retry_info,
            "escalated": self.escalated,
            "tool_name": self.tool_name,
            "execution_time_ms": self.execution_time_ms,
            "retry_count": self.retry_count
        }
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Messages by Category

```python
ERROR_MESSAGES = {
    "validation_error": {
        "template": "Input validation failed: {reason}",
        "recovery": [
            "Check the error details below",
            "Fix the invalid parameter",
            "Retry the operation"
        ]
    },

    "timeout": {
        "template": "Operation timed out after {duration}s",
        "recovery": [
            "The system may be overloaded",
            "Operation is running in background - check status later",
            "Try again in a few minutes",
            "Contact support if issue persists"
        ]
    },

    "connection_error": {
        "template": "Cannot connect to {service}",
        "recovery": [
            "Check your network connection",
            "Verify the backend service is running",
            "Wait a moment and retry",
            "Contact support if issue persists"
        ]
    },

    "permission_denied": {
        "template": "You don't have permission to {action}",
        "recovery": [
            "Contact your administrator to request access",
            "Use a different account with proper permissions",
            "Check the documentation for required roles"
        ]
    },

    "acgme_violation": {
        "template": "Operation would violate ACGME rule: {rule}",
        "recovery": [
            "Review the specific constraint violated",
            "Modify your request to satisfy the constraint",
            "Contact Program Director if you need an exception"
        ]
    },

    "not_found": {
        "template": "{resource} does not exist",
        "recovery": [
            "Verify the ID or name is correct",
            "Check if the resource was recently deleted",
            "Use available resources: {suggestions}"
        ]
    },

    "retry_exhausted": {
        "template": "Operation failed after {retry_count} retries",
        "recovery": [
            "The system may be experiencing issues",
            "Try again in a few minutes",
            "Contact support with this error: {error_id}"
        ]
    },

    "degraded_operation": {
        "template": "Operating in degraded mode: {reason}",
        "recovery": [
            "Using cached data (may not be current)",
            "Some features may be unavailable",
            "Check back when full service is restored"
        ]
    }
}

def format_error_response(
    error_type: str,
    **template_params
) -> ErrorResponse:
    """Format error response with user-friendly message."""

    config = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["validation_error"])
    message = config["template"].format(**template_params)
    recovery = config["recovery"]

    return ErrorResponse(
        success=False,
        error_type=error_type,
        message=message,
        recovery_options=recovery
    )
```

***REMOVED******REMOVED******REMOVED******REMOVED*** User Feedback During Retry

```python
async def call_with_feedback(
    tool_name: str,
    **params
) -> ErrorResponse | dict:
    """
    Call tool with user feedback during retry.

    Returns:
        Either ErrorResponse (on failure) or success dict
    """
    import logging
    from datetime import datetime

    logger = logging.getLogger(__name__)
    start_time = datetime.now()

    config = get_retry_config(tool_name)
    max_retries = config["max_retries"]

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"[Attempt {attempt + 1}/{max_retries + 1}] {tool_name}")

            ***REMOVED*** Provide feedback to user about attempt
            if attempt > 0:
                logger.info(
                    f"Retry {attempt}/{max_retries}: {tool_name} "
                    f"(last error: {last_error_type})"
                )

            result = await call_tool_with_timeout(
                tool_name,
                timeout=30,
                **params
            )

            ***REMOVED*** Success
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return {
                "success": True,
                "data": result,
                "execution_time_ms": duration_ms,
                "retry_count": attempt,
                "tool_used": tool_name
            }

        except Exception as e:
            last_error_type = type(e).__name__
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            ***REMOVED*** Check if error is retryable
            if not isinstance(e, tuple(config["retryable_errors"])):
                ***REMOVED*** Permanent error
                logger.error(
                    f"Permanent error in {tool_name}: {last_error_type}: {e}"
                )

                return format_error_response(
                    "validation_error",
                    reason=str(e)
                )

            if attempt == max_retries:
                ***REMOVED*** All retries exhausted
                logger.error(
                    f"All {max_retries} retries exhausted for {tool_name}"
                )

                return format_error_response(
                    "retry_exhausted",
                    retry_count=max_retries,
                    error_id=f"{tool_name}-{start_time.isoformat()}"
                )

            ***REMOVED*** Will retry
            delay = calculate_backoff_delay(attempt, config["base_delay"])
            logger.warning(
                f"Retry in {delay:.1f}s: {tool_name} "
                f"({last_error_type})"
            )

    return format_error_response(
        "retry_exhausted",
        retry_count=max_retries,
        error_id=f"{tool_name}-unknown"
    )
```

---

***REMOVED******REMOVED*** Recovery Strategies by Domain

***REMOVED******REMOVED******REMOVED*** SURVIVAL: Retry Strategies

***REMOVED******REMOVED******REMOVED******REMOVED*** Schedule Generation Failure Recovery

```python
async def recover_from_schedule_generation_failure(
    error: Exception,
    schedule_request: dict,
    attempt: int
) -> dict | ErrorResponse:
    """
    Recovery strategy for schedule generation failures.

    Args:
        error: Exception that occurred
        schedule_request: Original generation request
        attempt: Retry attempt number

    Returns:
        ErrorResponse or recovery suggestion
    """
    import logging

    logger = logging.getLogger(__name__)

    error_type = type(error).__name__

    ***REMOVED*** Pattern 1: INFEASIBLE (no solution found)
    if "INFEASIBLE" in str(error):
        logger.error("Schedule generation: INFEASIBLE problem")
        return format_error_response(
            "acgme_violation",
            rule="Conflicting constraints make schedule impossible",
            details={
                "suggestion": "Reduce constraints or increase resource allocation",
                "suggested_actions": [
                    "Review hard constraints for conflicts",
                    "Consider relaxing soft constraints",
                    "Increase faculty allocation if possible"
                ]
            }
        )

    ***REMOVED*** Pattern 2: Timeout (taking too long)
    elif isinstance(error, asyncio.TimeoutError):
        logger.warning(f"Schedule generation: Timeout on attempt {attempt}")

        ***REMOVED*** Move to background task for large schedules
        if attempt == 1:
            return {
                "status": "async_started",
                "message": "Large schedule detected - processing in background",
                "task_id": await start_background_generation(schedule_request),
                "check_status_url": "/api/tasks/{task_id}/status"
            }
        else:
            return format_error_response(
                "timeout",
                duration=30,
                recovery=[
                    "Schedule is very large or constraints are complex",
                    "Processing continues in background",
                    "Check status using task ID",
                    f"Expected completion: ~{5 * attempt} minutes"
                ]
            )

    ***REMOVED*** Pattern 3: Database errors (locks, deadlocks)
    elif "deadlock" in str(error).lower() or "locked" in str(error).lower():
        logger.warning(f"Schedule generation: Database lock on attempt {attempt}")

        if attempt < 3:
            return {
                "retry": True,
                "delay": 0.5 * (2 ** attempt),  ***REMOVED*** Exponential backoff
                "message": "Database is busy - retrying with backoff"
            }
        else:
            return format_error_response(
                "connection_error",
                service="database"
            )

    ***REMOVED*** Pattern 4: Insufficient resources
    elif "not enough" in str(error).lower() or "insufficient" in str(error).lower():
        return format_error_response(
            "validation_error",
            reason=str(error),
            recovery=[
                "Insufficient faculty/resources for request",
                "Increase allocation or modify requirements",
                "Contact coordinator for resource planning"
            ]
        )

    ***REMOVED*** Default: Unknown error
    else:
        logger.error(f"Schedule generation: Unknown error {error_type}: {error}")
        return format_error_response(
            "validation_error",
            reason=f"Unexpected error: {error_type}"
        )
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Swap Execution Failure Recovery

```python
***REMOVED*** See: /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/skills/SWAP_EXECUTION/Reference/swap-failure-modes.md

***REMOVED*** 5 Failure Modes with Recovery:
***REMOVED*** 1. Work Hour Creep (80-hour violation)
***REMOVED*** 2. Continuity Breaks (patient handoff risk)
***REMOVED*** 3. Coverage Gaps (insufficient staffing)
***REMOVED*** 4. Moonlighting Conflicts (double-booking)
***REMOVED*** 5. Fairness Violations (inequitable workload)

***REMOVED*** Each has automated detection + remediation suggestions
```

***REMOVED******REMOVED******REMOVED******REMOVED*** ACGME Validation Failure Recovery

```python
async def recover_from_acgme_validation_failure(
    error: Exception,
    schedule_id: str
) -> dict | ErrorResponse:
    """
    Recovery for ACGME compliance violations.

    Args:
        error: Validation error
        schedule_id: Schedule that failed validation

    Returns:
        ErrorResponse with suggested fixes
    """
    import logging
    from app.services.acgme_validator import get_violations

    logger = logging.getLogger(__name__)

    ***REMOVED*** Get detailed violations
    violations = await get_violations(schedule_id)

    ***REMOVED*** Categorize violations
    critical = [v for v in violations if v.severity == "critical"]
    warnings = [v for v in violations if v.severity == "warning"]

    if critical:
        logger.error(f"Critical ACGME violations in {schedule_id}: {len(critical)}")

        return format_error_response(
            "acgme_violation",
            rule=f"{len(critical)} critical violations found",
            details={
                "violations": [
                    {
                        "rule": v.rule_name,
                        "violator": v.person_name,
                        "specific": v.details,
                        "suggested_fix": v.suggested_fix
                    }
                    for v in critical
                ],
                "next_steps": [
                    "Review each violation",
                    "Modify schedule to satisfy violations",
                    "Re-validate schedule"
                ]
            }
        )

    elif warnings:
        logger.warning(f"Warning-level ACGME issues in {schedule_id}: {len(warnings)}")

        return {
            "success": False,
            "status": "warnings_present",
            "warning_count": len(warnings),
            "warnings": [
                {
                    "rule": w.rule_name,
                    "severity": "warning",
                    "details": w.details
                }
                for w in warnings
            ],
            "message": f"Schedule has {len(warnings)} warnings but can proceed with caution"
        }

    else:
        ***REMOVED*** No violations found - validation should have passed
        logger.error(f"Validation error for {schedule_id} but no violations found")
        return format_error_response(
            "validation_error",
            reason="Validation failed but cause unclear - review logs"
        )
```

---

***REMOVED******REMOVED*** Swallowed Error Detection

***REMOVED******REMOVED******REMOVED*** STEALTH: Hidden Errors

**Principle:** Never silently fail - log all errors even if handled gracefully.

```python
import logging
import functools

logger = logging.getLogger(__name__)

***REMOVED*** Swallowed error detection
SWALLOWED_ERROR_LOG = []

def detect_swallowed_errors(func):
    """
    Decorator to detect functions that silently handle errors.

    Logs any exception caught without re-raising or logging.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            ***REMOVED*** Log swallowed error
            logger.warning(
                f"Swallowed error in {func.__name__}: "
                f"{type(e).__name__}: {e}"
            )

            ***REMOVED*** Add to tracking
            SWALLOWED_ERROR_LOG.append({
                "function": func.__name__,
                "error_type": type(e).__name__,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })

            ***REMOVED*** Re-raise to prevent swallowing
            raise

    return wrapper

***REMOVED*** Usage
@detect_swallowed_errors
async def validate_schedule(schedule_id: str):
    """Validates schedule - any errors must be raised."""
    ***REMOVED*** ...
    pass

***REMOVED*** Audit swallowed errors periodically
def audit_swallowed_errors():
    """Check for patterns of swallowed errors."""
    if not SWALLOWED_ERROR_LOG:
        logger.info("No swallowed errors detected")
        return

    logger.error(
        f"AUDIT: {len(SWALLOWED_ERROR_LOG)} swallowed errors detected:\n"
        + "\n".join(
            f"  - {e['function']}: {e['error_type']}"
            for e in SWALLOWED_ERROR_LOG
        )
    )

    ***REMOVED*** Clear log
    SWALLOWED_ERROR_LOG.clear()
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Swallowing Patterns to Avoid

```python
***REMOVED*** BAD: Silently catches and ignores error
try:
    result = await validate_schedule(schedule_id)
except Exception:
    pass  ***REMOVED*** ← SWALLOWED ERROR

***REMOVED*** GOOD: Either re-raise or handle explicitly
try:
    result = await validate_schedule(schedule_id)
except ValueError as e:
    ***REMOVED*** Validation error - return to user
    logger.warning(f"Validation failed: {e}")
    return format_error_response("validation_error", reason=str(e))
except Exception as e:
    ***REMOVED*** Unexpected error - escalate
    logger.error(f"Unexpected error: {e}", exc_info=True)
    await escalate_error(EscalationLevel.CRITICAL, "validate_schedule", e, {})
    raise

***REMOVED*** GOOD: Conditional handling based on error type
try:
    result = await validate_schedule(schedule_id)
except (ConnectionError, asyncio.TimeoutError) as e:
    ***REMOVED*** Transient error - retry
    return await retry_with_backoff(validate_schedule, schedule_id=schedule_id)
except ValueError as e:
    ***REMOVED*** Permanent error - return to user
    return format_error_response("validation_error", reason=str(e))
except Exception as e:
    ***REMOVED*** Unknown error - escalate
    logger.error(f"Unknown error: {e}", exc_info=True)
    raise
```

---

***REMOVED******REMOVED*** Error Granularity

***REMOVED******REMOVED******REMOVED*** NATURE: Error Specificity Levels

**Principle:** Errors should be specific enough to guide recovery, not generic.

```python
***REMOVED*** LEVEL 1: Generic (Bad)
raise Exception("Operation failed")

***REMOVED*** LEVEL 2: Category (Better)
raise ValueError("Invalid input")

***REMOVED*** LEVEL 3: Specific (Best)
raise ValueError(
    "Invalid constraint_config: 'invalid'. "
    "Must be one of: ['default', 'minimal', 'strict', 'resilience']"
)

***REMOVED*** LEVEL 4: Actionable (Excellent)
raise ValueError(
    f"Invalid constraint_config: {provided_config!r}. "
    f"Must be one of: {VALID_CONFIGS}. "
    f"Suggestion: Use 'default' for standard ACGME compliance"
)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Context Levels

```python
class ErrorContextLevel:
    """Define how much context to include in error."""

    ***REMOVED*** Level 1: Minimal - Just the error type
    ***REMOVED*** Use for: User-facing errors (don't leak internals)
    MINIMAL = "minimal"

    ***REMOVED*** Level 2: Basic - Error type + message
    ***REMOVED*** Use for: Standard errors
    BASIC = "basic"

    ***REMOVED*** Level 3: Detailed - Message + suggestions
    ***REMOVED*** Use for: Validation errors
    DETAILED = "detailed"

    ***REMOVED*** Level 4: Full - Everything + stack trace + context
    ***REMOVED*** Use for: Debug/development
    FULL = "full"

def format_error_by_context(
    error: Exception,
    context_level: str = ErrorContextLevel.BASIC,
    user_facing: bool = False
) -> dict:
    """
    Format error with appropriate detail level.

    Args:
        error: Exception to format
        context_level: How much detail to include
        user_facing: Is this shown to user? (sanitize if true)

    Returns:
        Formatted error dict
    """
    import traceback

    error_dict = {
        "type": type(error).__name__,
        "message": str(error)
    }

    if context_level == ErrorContextLevel.MINIMAL:
        ***REMOVED*** User-facing, minimal info
        error_dict["message"] = "An error occurred. Please try again."

    elif context_level == ErrorContextLevel.BASIC:
        ***REMOVED*** Standard error format
        error_dict["message"] = str(error)

    elif context_level == ErrorContextLevel.DETAILED:
        ***REMOVED*** Include suggestions
        error_dict.update({
            "message": str(error),
            "suggestions": get_suggestions_for_error(error),
            "recovery_steps": get_recovery_steps(error)
        })

    elif context_level == ErrorContextLevel.FULL:
        ***REMOVED*** Full debugging info
        error_dict.update({
            "message": str(error),
            "stack_trace": traceback.format_exc(),
            "suggestions": get_suggestions_for_error(error),
            "recovery_steps": get_recovery_steps(error),
            "timestamp": datetime.now().isoformat()
        })

    return error_dict
```

---

***REMOVED******REMOVED*** Testing Error Paths

***REMOVED******REMOVED******REMOVED*** MEDICINE: Error Scenario Testing

**Principle:** Every error path must be tested, not just happy path.

```python
***REMOVED*** Test file: tests/test_error_handling.py

import pytest
from unittest.mock import patch
import asyncio

class TestErrorHandling:
    """Test error handling across skills."""

    @pytest.mark.asyncio
    async def test_validation_error_returns_error_response(self):
        """Validation errors should return ErrorResponse, not raise."""
        with patch('validate_schedule_tool') as mock_validate:
            mock_validate.side_effect = ValueError("Invalid schedule")

            result = await call_with_feedback(
                "validate_schedule_tool",
                schedule_id="test"
            )

            ***REMOVED*** Should return ErrorResponse, not raise
            assert isinstance(result, ErrorResponse)
            assert result.error_type == "validation_error"
            assert not result.success

    @pytest.mark.asyncio
    async def test_transient_error_retries(self):
        """Transient errors should retry automatically."""
        call_count = 0

        async def failing_tool():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return {"status": "success"}

        result = await retry_with_backoff(
            failing_tool,
            max_retries=3,
            base_delay=0.01
        )

        assert result["status"] == "success"
        assert call_count == 3  ***REMOVED*** Failed twice, succeeded on third

    @pytest.mark.asyncio
    async def test_timeout_error_with_fallback(self):
        """Timeout errors should try fallback tool."""
        with patch('call_tool_with_retry') as mock_call:
            ***REMOVED*** Primary fails, fallback succeeds
            mock_call.side_effect = [
                asyncio.TimeoutError("Primary timeout"),
                {"status": "fallback_success"}
            ]

            result = await call_with_fallback(
                "primary_tool",
                fallback_tools=["fallback_tool"],
                param="value"
            )

            assert result["fallback_used"]
            assert result["tool_used"] == "fallback_tool"

    @pytest.mark.asyncio
    async def test_permanent_error_no_retry(self):
        """Permanent errors should not retry."""
        call_count = 0

        async def failing_tool():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")  ***REMOVED*** Permanent error

        with pytest.raises(ValueError):
            await retry_with_backoff(
                failing_tool,
                max_retries=3,
                base_delay=0.01
            )

        ***REMOVED*** Should not retry permanent error
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Circuit breaker should open after threshold failures."""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1
        )

        async def failing_tool():
            raise ConnectionError("Connection failed")

        ***REMOVED*** Fail 3 times
        for _ in range(3):
            with pytest.raises(ConnectionError):
                await breaker.call(failing_tool)

        ***REMOVED*** Circuit should be OPEN
        assert breaker.state == CircuitState.OPEN

        ***REMOVED*** Should reject without calling tool
        with pytest.raises(RuntimeError, match="Circuit OPEN"):
            await breaker.call(failing_tool)

    @pytest.mark.asyncio
    async def test_cache_fallback_on_timeout(self):
        """Cache fallback should return cached data on tool timeout."""
        ***REMOVED*** Seed cache with old data
        cache_key = "test-schedule"
        cached_data = {"cached": True, "age_minutes": 5}
        CACHE[cache_key] = (datetime.now() - timedelta(minutes=5), cached_data)

        with patch('call_tool_with_retry') as mock_call:
            mock_call.side_effect = asyncio.TimeoutError("Timeout")

            result = await get_with_cache_fallback(
                "schedule_tool",
                cache_key=cache_key,
                cache_ttl=timedelta(minutes=10),
                schedule_id="test"
            )

            ***REMOVED*** Should return cached data
            assert result["cache_hit"]
            assert result["cache_status"] == "fresh"
            assert result["data"] == cached_data

    def test_error_metrics_tracking(self):
        """Error metrics should track all failures."""
        metrics = ToolMetrics()

        ***REMOVED*** Record successful call
        metrics.record_call(
            "validate_tool",
            success=True,
            duration_ms=100
        )

        ***REMOVED*** Record failed call
        metrics.record_call(
            "validate_tool",
            success=False,
            error_type="TimeoutError",
            duration_ms=30000  ***REMOVED*** Timeout after 30s
        )

        ***REMOVED*** Check metrics
        tool_metrics = metrics.get_metrics("validate_tool")
        assert tool_metrics["total_calls"] == 2
        assert tool_metrics["total_errors"] == 1
        assert tool_metrics["error_rate_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_escalation_on_critical_error(self):
        """Critical errors should trigger escalation."""
        with patch('send_pagerduty_alert') as mock_alert:
            await escalate_error(
                EscalationLevel.EMERGENCY,
                tool_name="promote_to_production_tool",
                error=RuntimeError("Deployment failed, rollback failed"),
                context={"deployment_id": "d-123"}
            )

            ***REMOVED*** Should send alert
            assert mock_alert.called
            call_args = mock_alert.call_args[0][0]
            assert call_args["level"] == "emergency"
```

---

***REMOVED******REMOVED*** Monitoring Dashboard

***REMOVED******REMOVED******REMOVED*** INSIGHT: Observable Errors

**Key Metrics to Monitor:**

```
Tool Health Dashboard
│
├─ Error Rate by Tool
│   ├─ validate_schedule_tool: 2.1% (GOOD)
│   ├─ swap_executor_tool: 5.2% (WARNING)
│   └─ generate_schedule_tool: 12.3% (CRITICAL - investigate)
│
├─ Retry Statistics
│   ├─ Avg retry count: 1.2
│   ├─ Retry success rate: 87% (good)
│   └─ Exhausted retries: 3 in last hour
│
├─ Fallback Usage
│   ├─ Times fallback triggered: 12 in last 24h
│   ├─ Primary tool failure rate: 0.8%
│   └─ Fallback success rate: 95%
│
├─ Response Times
│   ├─ p50: 120ms
│   ├─ p95: 850ms
│   └─ p99: 4200ms
│
├─ Escalations
│   ├─ INFO level: 45
│   ├─ WARNING level: 8
│   ├─ CRITICAL level: 1 (investigate immediately)
│   └─ EMERGENCY level: 0
│
└─ Data Integrity
    ├─ Validation failures: 2 in 24h
    ├─ Rollbacks: 1 in 24h
    └─ Data corruption: 0
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Prometheus Metrics Configuration

```python
from prometheus_client import Counter, Histogram, Gauge

***REMOVED*** Error counters
skill_errors_total = Counter(
    'skill_errors_total',
    'Total skill execution errors',
    ['skill_name', 'error_type', 'severity']
)

***REMOVED*** Retry metrics
skill_retries_total = Counter(
    'skill_retries_total',
    'Total skill execution retries',
    ['skill_name', 'retry_attempt']
)

skill_retry_exhausted = Counter(
    'skill_retry_exhausted_total',
    'Times skill retries were exhausted',
    ['skill_name']
)

***REMOVED*** Timing metrics
skill_execution_duration = Histogram(
    'skill_execution_duration_seconds',
    'Skill execution duration',
    ['skill_name', 'outcome']
)

***REMOVED*** Fallback metrics
skill_fallback_used = Counter(
    'skill_fallback_used_total',
    'Times fallback was used',
    ['primary_skill', 'fallback_skill']
)

***REMOVED*** Escalation metrics
escalations_total = Counter(
    'escalations_total',
    'Total error escalations',
    ['escalation_level']
)

***REMOVED*** Current health
skill_error_rate = Gauge(
    'skill_error_rate',
    'Current error rate by skill',
    ['skill_name']
)

***REMOVED*** Usage example
def record_skill_execution(
    skill_name: str,
    success: bool,
    duration_sec: float,
    error_type: str | None = None,
    severity: str = "info"
):
    """Record metrics for skill execution."""

    if not success:
        skill_errors_total.labels(
            skill_name=skill_name,
            error_type=error_type or "unknown",
            severity=severity
        ).inc()

    skill_execution_duration.labels(
        skill_name=skill_name,
        outcome="success" if success else "failure"
    ).observe(duration_sec)
```

---

***REMOVED******REMOVED*** Best Practices Summary

1. **Classify before retrying** - Don't retry permanent errors
2. **Use exponential backoff** - Avoid thundering herd problem
3. **Limit retry attempts** - Fail fast on persistent issues
4. **Log all errors** - Structured logging for debugging
5. **Monitor error rates** - Track metrics per tool
6. **Escalate appropriately** - Critical errors need human attention
7. **Implement circuit breakers** - Stop calling failing tools
8. **Cache when possible** - Reduce load on struggling services
9. **Provide fallbacks** - Degrade gracefully instead of failing
10. **Test error paths** - Ensure error handling actually works
11. **Communicate with users** - Clear, actionable error messages
12. **Never swallow errors** - Log all exceptions explicitly

---

***REMOVED******REMOVED*** Quick Reference Guide

***REMOVED******REMOVED******REMOVED*** Error Classification Decision Tree

```
Is error transient (timeout, connection)?
├─ YES → Retry with exponential backoff (3-5 attempts)
└─ NO → Check if permanent

Is error validation (input incorrect)?
├─ YES → Return error to user immediately
└─ NO → Check if critical

Is error critical (security, data loss)?
├─ YES → Escalate CRITICAL → Block operation → Alert human
└─ NO → Check if recoverable

Can operation degrade gracefully?
├─ YES → Use cache/fallback → Return partial results
└─ NO → Escalate ERROR → Return error response
```

***REMOVED******REMOVED******REMOVED*** Retry Configuration Quick Reference

| Tool Category | Max Retries | Base Delay | Backoff |
|---|---|---|---|
| Validation Tools | 3 | 1.0s | Exponential |
| Background Tasks | 5 | 0.5s | Exponential |
| Read-Only Tools | 5 | 0.5s | Exponential |
| Deployment Tools | 1 | 5.0s | Exponential |
| Schedule Generation | 2 | 2.0s | Exponential |

***REMOVED******REMOVED******REMOVED*** Escalation Matrix

| Severity | Action | Response Time |
|---|---|---|
| INFO | Log only | None |
| WARNING | Alert + log | 15 min |
| CRITICAL | Alert + incident | 5 min |
| EMERGENCY | PagerDuty + incident | Immediate |

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Maintained By:** G2_RECON Session 9
**Status:** Ready for skill deployment
