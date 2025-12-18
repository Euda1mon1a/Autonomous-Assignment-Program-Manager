***REMOVED*** MCP Error Handling Documentation

***REMOVED******REMOVED*** Overview

The MCP error handling middleware provides a comprehensive suite of tools for managing errors, retries, and service resilience in the Scheduler MCP server. It includes:

- **Custom exception hierarchy** for structured error responses
- **Automatic retry logic** with exponential backoff and jitter
- **Circuit breaker pattern** for service resilience
- **Error handler decorator** for automatic error transformation
- **Metrics tracking** for monitoring and observability
- **Correlation IDs** for distributed tracing

***REMOVED******REMOVED*** Table of Contents

1. [Quick Start](***REMOVED***quick-start)
2. [Exception Classes](***REMOVED***exception-classes)
3. [Error Handler Decorator](***REMOVED***error-handler-decorator)
4. [Retry Logic](***REMOVED***retry-logic)
5. [Circuit Breaker](***REMOVED***circuit-breaker)
6. [Error Metrics](***REMOVED***error-metrics)
7. [Best Practices](***REMOVED***best-practices)
8. [Examples](***REMOVED***examples)

---

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Basic Usage

```python
from scheduler_mcp.error_handling import (
    mcp_error_handler,
    MCPValidationError,
)

@mcp_error_handler
async def my_tool(param: str) -> dict:
    """Tool with automatic error handling."""
    if not param:
        raise MCPValidationError(
            message="Parameter cannot be empty",
            field="param",
        )
    return {"result": "success"}
```

***REMOVED******REMOVED******REMOVED*** With Retry Logic

```python
from scheduler_mcp.error_handling import (
    mcp_error_handler,
    RetryConfig,
)

@mcp_error_handler(
    retry_config=RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        exponential_base=2.0,
    )
)
async def fetch_from_api() -> dict:
    """API call with automatic retries."""
    ***REMOVED*** API call implementation
    pass
```

***REMOVED******REMOVED******REMOVED*** With Circuit Breaker

```python
from scheduler_mcp.error_handling import (
    mcp_error_handler,
    CircuitBreakerConfig,
)

@mcp_error_handler(
    circuit_breaker_name="database",
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=5,
        timeout=60.0,
    )
)
async def query_database(query: str) -> dict:
    """Database query with circuit breaker protection."""
    ***REMOVED*** Database query implementation
    pass
```

---

***REMOVED******REMOVED*** Exception Classes

***REMOVED******REMOVED******REMOVED*** Exception Hierarchy

```
MCPToolError (base)
├── MCPValidationError (input validation)
├── MCPServiceUnavailable (backend service down)
├── MCPRateLimitError (rate limit exceeded)
├── MCPAuthenticationError (auth failed)
├── MCPTimeoutError (operation timeout)
└── MCPCircuitOpenError (circuit breaker open)
```

***REMOVED******REMOVED******REMOVED*** MCPToolError (Base Class)

All MCP exceptions inherit from this base class.

```python
from scheduler_mcp.error_handling import MCPToolError, MCPErrorCode

error = MCPToolError(
    message="User-friendly error message",
    error_code=MCPErrorCode.INTERNAL_ERROR,
    details={"key": "value"},  ***REMOVED*** Optional context
    retry_after=30,  ***REMOVED*** Optional retry delay in seconds
)

***REMOVED*** Convert to structured response
error_dict = error.to_dict()
***REMOVED*** {
***REMOVED***     "error": True,
***REMOVED***     "error_code": "INTERNAL_ERROR",
***REMOVED***     "message": "User-friendly error message",
***REMOVED***     "correlation_id": "uuid-here",
***REMOVED***     "timestamp": "2025-01-15T10:30:00",
***REMOVED***     "details": {"key": "value"},
***REMOVED***     "retry_after": 30
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** MCPValidationError

For input validation failures.

```python
from scheduler_mcp.error_handling import MCPValidationError

raise MCPValidationError(
    message="Invalid date format",
    field="end_date",  ***REMOVED*** Optional field name
    details={"expected": "YYYY-MM-DD"},
)
```

***REMOVED******REMOVED******REMOVED*** MCPServiceUnavailable

For backend service unavailability.

```python
from scheduler_mcp.error_handling import MCPServiceUnavailable

raise MCPServiceUnavailable(
    message="Database connection failed",
    service_name="database",
    retry_after=30,
    details={"host": "db.example.com"},
)
```

***REMOVED******REMOVED******REMOVED*** MCPRateLimitError

For rate limit violations.

```python
from scheduler_mcp.error_handling import MCPRateLimitError

raise MCPRateLimitError(
    message="Rate limit exceeded",
    limit=100,  ***REMOVED*** Requests per window
    window=60,  ***REMOVED*** Window in seconds
    retry_after=45,  ***REMOVED*** Seconds until reset
)
```

***REMOVED******REMOVED******REMOVED*** MCPAuthenticationError

For authentication failures.

```python
from scheduler_mcp.error_handling import MCPAuthenticationError

raise MCPAuthenticationError(
    message="Invalid credentials",
    details={"method": "jwt"},
)
```

***REMOVED******REMOVED******REMOVED*** MCPTimeoutError

For operation timeouts.

```python
from scheduler_mcp.error_handling import MCPTimeoutError

raise MCPTimeoutError(
    message="Schedule validation timed out",
    timeout_seconds=30.0,
    operation="acgme_validation",
    retry_after=10,
)
```

***REMOVED******REMOVED******REMOVED*** MCPCircuitOpenError

Raised when circuit breaker is open.

```python
from scheduler_mcp.error_handling import MCPCircuitOpenError

***REMOVED*** Usually raised automatically by circuit breaker
raise MCPCircuitOpenError(
    service_name="api",
    retry_after=60,
)
```

---

***REMOVED******REMOVED*** Error Handler Decorator

The `@mcp_error_handler` decorator provides automatic error handling, logging, and transformation.

***REMOVED******REMOVED******REMOVED*** Features

- Automatically catches and transforms exceptions
- Logs errors with correlation IDs
- Converts Python exceptions to structured MCP errors
- Optional retry logic integration
- Optional circuit breaker integration

***REMOVED******REMOVED******REMOVED*** Basic Usage

```python
@mcp_error_handler
async def my_tool():
    ***REMOVED*** ValueError is automatically converted to MCPValidationError
    raise ValueError("Invalid input")
```

***REMOVED******REMOVED******REMOVED*** With Parameters

```python
@mcp_error_handler(
    retry_config=RetryConfig(max_attempts=3),
    circuit_breaker_name="my_service",
    log_errors=True,  ***REMOVED*** Default: True
)
async def my_tool():
    pass
```

***REMOVED******REMOVED******REMOVED*** Exception Conversion

The decorator automatically converts standard Python exceptions to MCP exceptions:

| Python Exception | MCP Exception |
|-----------------|---------------|
| `ValueError` | `MCPValidationError` |
| `asyncio.TimeoutError` | `MCPTimeoutError` |
| `ConnectionError` | `MCPServiceUnavailable` |
| Other exceptions | `MCPToolError` (INTERNAL_ERROR) |

---

***REMOVED******REMOVED*** Retry Logic

Automatic retry with exponential backoff and jitter.

***REMOVED******REMOVED******REMOVED*** RetryConfig

```python
from scheduler_mcp.error_handling import RetryConfig

config = RetryConfig(
    max_attempts=3,           ***REMOVED*** Maximum retry attempts
    base_delay=1.0,           ***REMOVED*** Base delay in seconds
    max_delay=60.0,           ***REMOVED*** Maximum delay cap
    exponential_base=2.0,     ***REMOVED*** Exponential multiplier
    jitter=True,              ***REMOVED*** Add randomness (0-25% of delay)
    retryable_exceptions=(    ***REMOVED*** Exceptions to retry
        MCPServiceUnavailable,
        MCPTimeoutError,
        asyncio.TimeoutError,
        ConnectionError,
    ),
)
```

***REMOVED******REMOVED******REMOVED*** How It Works

1. **First attempt**: Immediate execution
2. **Retry 1**: Wait `base_delay * (exponential_base ^ 0)` = 1.0s
3. **Retry 2**: Wait `base_delay * (exponential_base ^ 1)` = 2.0s
4. **Retry 3**: Wait `base_delay * (exponential_base ^ 2)` = 4.0s
5. Jitter adds 0-25% randomness to prevent thundering herd

***REMOVED******REMOVED******REMOVED*** Standalone Usage

```python
from scheduler_mcp.error_handling import retry_with_backoff, RetryConfig

@retry_with_backoff(RetryConfig(max_attempts=5))
async def my_function():
    ***REMOVED*** Function with retry logic
    pass
```

***REMOVED******REMOVED******REMOVED*** With Error Handler

```python
@mcp_error_handler(
    retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
)
async def my_tool():
    ***REMOVED*** Combines error handling + retry
    pass
```

---

***REMOVED******REMOVED*** Circuit Breaker

Prevents cascading failures by opening circuit after threshold failures.

***REMOVED******REMOVED******REMOVED*** Circuit States

1. **CLOSED** (normal): All requests pass through
2. **OPEN** (failing): Requests rejected immediately
3. **HALF_OPEN** (testing): Limited requests allowed to test recovery

***REMOVED******REMOVED******REMOVED*** State Transitions

```
CLOSED --[threshold failures]--> OPEN
OPEN --[timeout elapsed]--> HALF_OPEN
HALF_OPEN --[success threshold]--> CLOSED
HALF_OPEN --[any failure]--> OPEN
```

***REMOVED******REMOVED******REMOVED*** CircuitBreakerConfig

```python
from scheduler_mcp.error_handling import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,      ***REMOVED*** Failures before opening
    success_threshold=2,      ***REMOVED*** Successes to close from half-open
    timeout=60.0,             ***REMOVED*** Seconds before half-open test
    half_open_max_calls=3,    ***REMOVED*** Max concurrent calls in half-open
    monitored_exceptions=(    ***REMOVED*** Exceptions that trigger circuit
        MCPServiceUnavailable,
        MCPTimeoutError,
        ConnectionError,
    ),
)
```

***REMOVED******REMOVED******REMOVED*** Usage with Decorator

```python
@mcp_error_handler(
    circuit_breaker_name="database",
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=5,
        timeout=60.0,
    ),
)
async def query_db():
    pass
```

***REMOVED******REMOVED******REMOVED*** Direct Usage

```python
from scheduler_mcp.error_handling import get_circuit_breaker

cb = get_circuit_breaker("my_service")

async def my_operation():
    return "result"

try:
    result = await cb.call(my_operation)
except MCPCircuitOpenError:
    ***REMOVED*** Circuit is open, service degraded
    pass

***REMOVED*** Check circuit state
state = cb.get_state()
print(f"State: {state['state']}")
print(f"Failures: {state['failure_count']}")
```

***REMOVED******REMOVED******REMOVED*** Global Registry

Circuit breakers are stored in a global registry by name.

```python
from scheduler_mcp.error_handling import get_all_circuit_breakers

***REMOVED*** Get all circuit breaker states
states = get_all_circuit_breakers()
***REMOVED*** {
***REMOVED***     "database": {"state": "closed", "failure_count": 0, ...},
***REMOVED***     "api": {"state": "open", "failure_count": 5, ...},
***REMOVED*** }
```

---

***REMOVED******REMOVED*** Error Metrics

Track error rates and patterns for monitoring and alerting.

***REMOVED******REMOVED******REMOVED*** Recording Errors

```python
from scheduler_mcp.error_handling import record_error, MCPErrorCode

record_error(
    error_code=MCPErrorCode.VALIDATION_ERROR,
    tool_name="validate_schedule",
)
```

***REMOVED******REMOVED******REMOVED*** Getting Metrics

```python
from scheduler_mcp.error_handling import get_error_metrics

metrics = get_error_metrics()
***REMOVED*** {
***REMOVED***     "total_errors": 42,
***REMOVED***     "errors_by_code": {
***REMOVED***         "VALIDATION_ERROR": 20,
***REMOVED***         "TIMEOUT": 10,
***REMOVED***         "SERVICE_UNAVAILABLE": 12,
***REMOVED***     },
***REMOVED***     "errors_by_tool": {
***REMOVED***         "validate_schedule": 15,
***REMOVED***         "analyze_swap": 10,
***REMOVED***     },
***REMOVED***     "last_error_time": 1642254123.456,
***REMOVED***     "circuit_breakers": {...},
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Resetting Metrics

```python
from scheduler_mcp.error_handling import reset_error_metrics

reset_error_metrics()  ***REMOVED*** Useful for testing
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Use Appropriate Exception Types

```python
***REMOVED*** ✓ Good: Specific exception with context
raise MCPValidationError(
    message="End date must be after start date",
    field="end_date",
    details={"start_date": "2025-01-01", "end_date": "2024-12-31"},
)

***REMOVED*** ✗ Bad: Generic exception
raise Exception("Invalid dates")
```

***REMOVED******REMOVED******REMOVED*** 2. Don't Leak Sensitive Information

```python
***REMOVED*** ✓ Good: Generic user-facing message
raise MCPServiceUnavailable(
    message="Database connection failed",
    service_name="database",
)
***REMOVED*** Detailed error logged server-side only

***REMOVED*** ✗ Bad: Exposes internal details
raise Exception(f"Connection failed: {db_password}@{db_host}")
```

***REMOVED******REMOVED******REMOVED*** 3. Use Circuit Breakers for External Services

```python
***REMOVED*** ✓ Good: Protect external service calls
@mcp_error_handler(circuit_breaker_name="external_api")
async def call_external_api():
    pass

***REMOVED*** ✗ Bad: No protection, can cascade failures
async def call_external_api():
    pass
```

***REMOVED******REMOVED******REMOVED*** 4. Configure Appropriate Retry Strategies

```python
***REMOVED*** ✓ Good: Fast retries for transient failures
@mcp_error_handler(
    retry_config=RetryConfig(
        max_attempts=3,
        base_delay=0.5,  ***REMOVED*** Start with 0.5s
    )
)
async def fetch_cached_data():
    pass

***REMOVED*** ✓ Good: Slower retries for heavy operations
@mcp_error_handler(
    retry_config=RetryConfig(
        max_attempts=2,
        base_delay=5.0,  ***REMOVED*** Start with 5s
    )
)
async def run_heavy_computation():
    pass
```

***REMOVED******REMOVED******REMOVED*** 5. Provide Helpful Error Messages

```python
***REMOVED*** ✓ Good: Actionable message
raise MCPValidationError(
    message="Assignment conflicts with existing schedule",
    field="assignment_id",
    details={
        "conflicting_assignment": "assign-123",
        "date": "2025-01-15",
        "suggested_action": "Choose a different date or cancel conflicting assignment",
    },
)

***REMOVED*** ✗ Bad: Vague message
raise MCPValidationError("Conflict")
```

***REMOVED******REMOVED******REMOVED*** 6. Use Correlation IDs for Tracing

```python
***REMOVED*** Correlation IDs are automatically generated and logged
@mcp_error_handler
async def my_tool():
    ***REMOVED*** Errors will have correlation_id in logs and responses
    raise MCPServiceUnavailable("Service down")

***REMOVED*** Use correlation ID to trace error across services
***REMOVED*** Logs will show: "correlation_id": "abc-123-def-456"
```

---

***REMOVED******REMOVED*** Examples

See `/home/user/Autonomous-Assignment-Program-Manager/mcp-server/examples/error_handling_example.py` for comprehensive examples including:

1. Basic error handler usage
2. Retry logic with exponential backoff
3. Circuit breaker pattern
4. Combining retry and circuit breaker
5. Manual error handling
6. Direct circuit breaker usage
7. Error metrics monitoring
8. Structured error responses

Run examples:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/mcp-server
python examples/error_handling_example.py
```

---

***REMOVED******REMOVED*** Testing

Comprehensive test suite available at `/home/user/Autonomous-Assignment-Program-Manager/mcp-server/tests/test_error_handling.py`

Run tests:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/mcp-server
pytest tests/test_error_handling.py -v
```

Test coverage includes:
- Exception creation and serialization
- Retry logic with exponential backoff
- Circuit breaker state transitions
- Error handler decorator transformations
- Metrics tracking
- Integration scenarios

---

***REMOVED******REMOVED*** Integration with MCP Tools

***REMOVED******REMOVED******REMOVED*** Updating Existing Tools

Update your MCP tools to use the error handling middleware:

```python
***REMOVED*** Before
async def validate_schedule(request):
    try:
        ***REMOVED*** validation logic
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

***REMOVED*** After
from scheduler_mcp.error_handling import mcp_error_handler, RetryConfig

@mcp_error_handler(
    retry_config=RetryConfig(max_attempts=3),
    circuit_breaker_name="validation_service",
)
async def validate_schedule(request):
    ***REMOVED*** validation logic
    return result
    ***REMOVED*** Errors automatically handled, logged, and structured
```

***REMOVED******REMOVED******REMOVED*** Tool Registration

```python
from scheduler_mcp.error_handling import mcp_error_handler

@mcp.tool()
@mcp_error_handler
async def my_mcp_tool(param: str) -> dict:
    """MCP tool with error handling."""
    ***REMOVED*** Tool implementation
    pass
```

---

***REMOVED******REMOVED*** Error Response Format

All MCP errors follow this standardized format:

```json
{
  "error": true,
  "error_code": "VALIDATION_ERROR",
  "message": "User-friendly error message",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "details": {
    "field": "end_date",
    "reason": "end_date must be after start_date"
  },
  "retry_after": 30
}
```

Fields:
- `error`: Always `true` for error responses
- `error_code`: Standardized error code (see `MCPErrorCode` enum)
- `message`: Human-readable error message
- `correlation_id`: Unique ID for tracing
- `timestamp`: ISO 8601 timestamp
- `details`: Optional error-specific context
- `retry_after`: Optional suggested retry delay (seconds)

---

***REMOVED******REMOVED*** Monitoring and Observability

***REMOVED******REMOVED******REMOVED*** Metrics Dashboard

Use `get_error_metrics()` to build monitoring dashboards:

```python
from scheduler_mcp.error_handling import get_error_metrics

***REMOVED*** Periodic metrics collection
metrics = get_error_metrics()

***REMOVED*** Alert on high error rates
if metrics["total_errors"] > threshold:
    send_alert("High error rate detected")

***REMOVED*** Monitor circuit breaker states
for name, state in metrics["circuit_breakers"].items():
    if state["state"] == "open":
        send_alert(f"Circuit breaker {name} is OPEN")
```

***REMOVED******REMOVED******REMOVED*** Log Correlation

All errors are logged with correlation IDs:

```
ERROR scheduler_mcp.error_handling:error_handling.py:854 validate_schedule timed out
    correlation_id: 550e8400-e29b-41d4-a716-446655440000
```

Use correlation IDs to:
- Trace errors across services
- Debug distributed systems
- Correlate errors with user actions

---

***REMOVED******REMOVED*** Performance Considerations

***REMOVED******REMOVED******REMOVED*** Retry Strategy Impact

- **Fast retries** (< 1s): Suitable for cache misses, network blips
- **Medium retries** (1-5s): Suitable for database connection issues
- **Slow retries** (> 5s): Suitable for external API rate limits

***REMOVED******REMOVED******REMOVED*** Circuit Breaker Overhead

- **Minimal overhead** in CLOSED state (~microseconds)
- **Zero request overhead** in OPEN state (immediate rejection)
- **Limited concurrency** in HALF_OPEN state (prevents overload)

***REMOVED******REMOVED******REMOVED*** Memory Usage

- Circuit breakers: ~1KB per instance
- Metrics: ~100 bytes per error code/tool combination
- Correlation tracking: ~36 bytes per active request (UUID)

---

***REMOVED******REMOVED*** FAQ

***REMOVED******REMOVED******REMOVED*** Q: When should I use retry vs circuit breaker?

**A:** Use both together:
- **Retry**: For transient failures (network blips, temporary unavailability)
- **Circuit breaker**: For sustained failures (service down, database unreachable)

Retries handle short-term issues, circuit breakers prevent cascade during prolonged outages.

***REMOVED******REMOVED******REMOVED*** Q: What exceptions are retried automatically?

**A:** By default:
- `MCPServiceUnavailable`
- `MCPTimeoutError`
- `asyncio.TimeoutError`
- `ConnectionError`

Validation errors are NOT retried (they won't succeed on retry).

***REMOVED******REMOVED******REMOVED*** Q: How do I create a custom error type?

**A:** Inherit from `MCPToolError`:

```python
class MCPCustomError(MCPToolError):
    def __init__(self, message: str, custom_field: str):
        super().__init__(
            message=message,
            error_code=MCPErrorCode.INTERNAL_ERROR,  ***REMOVED*** or create new code
            details={"custom_field": custom_field},
        )
```

***REMOVED******REMOVED******REMOVED*** Q: Can I disable error logging?

**A:** Yes:

```python
@mcp_error_handler(log_errors=False)
async def my_tool():
    pass
```

***REMOVED******REMOVED******REMOVED*** Q: How do I test circuit breaker behavior?

**A:** See test examples in `tests/test_error_handling.py`:

```python
async def test_circuit_breaker():
    cb = get_circuit_breaker("test", CircuitBreakerConfig(failure_threshold=2))

    ***REMOVED*** Trigger failures
    for _ in range(2):
        with pytest.raises(MCPServiceUnavailable):
            await cb.call(failing_function)

    ***REMOVED*** Circuit should be open
    assert cb.state.state == CircuitState.OPEN
```

---

***REMOVED******REMOVED*** Support

For questions or issues:
1. Check examples: `/mcp-server/examples/error_handling_example.py`
2. Review tests: `/mcp-server/tests/test_error_handling.py`
3. Read source: `/mcp-server/src/scheduler_mcp/error_handling.py`
4. File issue on GitHub

---

***REMOVED******REMOVED*** License

MIT License - See project LICENSE file for details.
