# MCP Error Handling Documentation

## Overview

The MCP error handling middleware provides a comprehensive suite of tools for managing errors, retries, and service resilience in the Scheduler MCP server. It includes:

- **Custom exception hierarchy** for structured error responses
- **Automatic retry logic** with exponential backoff and jitter
- **Circuit breaker pattern** for service resilience
- **Error handler decorator** for automatic error transformation
- **Metrics tracking** for monitoring and observability
- **Correlation IDs** for distributed tracing

## Table of Contents

1. [Quick Start](#quick-start)
2. [Exception Classes](#exception-classes)
3. [Error Handler Decorator](#error-handler-decorator)
4. [Retry Logic](#retry-logic)
5. [Circuit Breaker](#circuit-breaker)
6. [Error Metrics](#error-metrics)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## Quick Start

### Basic Usage

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

### With Retry Logic

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
    # API call implementation
    pass
```

### With Circuit Breaker

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
    # Database query implementation
    pass
```

---

## Exception Classes

### Exception Hierarchy

```
MCPToolError (base)
├── MCPValidationError (input validation)
├── MCPServiceUnavailable (backend service down)
├── MCPRateLimitError (rate limit exceeded)
├── MCPAuthenticationError (auth failed)
├── MCPTimeoutError (operation timeout)
└── MCPCircuitOpenError (circuit breaker open)
```

### MCPToolError (Base Class)

All MCP exceptions inherit from this base class.

```python
from scheduler_mcp.error_handling import MCPToolError, MCPErrorCode

error = MCPToolError(
    message="User-friendly error message",
    error_code=MCPErrorCode.INTERNAL_ERROR,
    details={"key": "value"},  # Optional context
    retry_after=30,  # Optional retry delay in seconds
)

# Convert to structured response
error_dict = error.to_dict()
# {
#     "error": True,
#     "error_code": "INTERNAL_ERROR",
#     "message": "User-friendly error message",
#     "correlation_id": "uuid-here",
#     "timestamp": "2025-01-15T10:30:00",
#     "details": {"key": "value"},
#     "retry_after": 30
# }
```

### MCPValidationError

For input validation failures.

```python
from scheduler_mcp.error_handling import MCPValidationError

raise MCPValidationError(
    message="Invalid date format",
    field="end_date",  # Optional field name
    details={"expected": "YYYY-MM-DD"},
)
```

### MCPServiceUnavailable

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

### MCPRateLimitError

For rate limit violations.

```python
from scheduler_mcp.error_handling import MCPRateLimitError

raise MCPRateLimitError(
    message="Rate limit exceeded",
    limit=100,  # Requests per window
    window=60,  # Window in seconds
    retry_after=45,  # Seconds until reset
)
```

### MCPAuthenticationError

For authentication failures.

```python
from scheduler_mcp.error_handling import MCPAuthenticationError

raise MCPAuthenticationError(
    message="Invalid credentials",
    details={"method": "jwt"},
)
```

### MCPTimeoutError

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

### MCPCircuitOpenError

Raised when circuit breaker is open.

```python
from scheduler_mcp.error_handling import MCPCircuitOpenError

# Usually raised automatically by circuit breaker
raise MCPCircuitOpenError(
    service_name="api",
    retry_after=60,
)
```

---

## Error Handler Decorator

The `@mcp_error_handler` decorator provides automatic error handling, logging, and transformation.

### Features

- Automatically catches and transforms exceptions
- Logs errors with correlation IDs
- Converts Python exceptions to structured MCP errors
- Optional retry logic integration
- Optional circuit breaker integration

### Basic Usage

```python
@mcp_error_handler
async def my_tool():
    # ValueError is automatically converted to MCPValidationError
    raise ValueError("Invalid input")
```

### With Parameters

```python
@mcp_error_handler(
    retry_config=RetryConfig(max_attempts=3),
    circuit_breaker_name="my_service",
    log_errors=True,  # Default: True
)
async def my_tool():
    pass
```

### Exception Conversion

The decorator automatically converts standard Python exceptions to MCP exceptions:

| Python Exception | MCP Exception |
|-----------------|---------------|
| `ValueError` | `MCPValidationError` |
| `asyncio.TimeoutError` | `MCPTimeoutError` |
| `ConnectionError` | `MCPServiceUnavailable` |
| Other exceptions | `MCPToolError` (INTERNAL_ERROR) |

---

## Retry Logic

Automatic retry with exponential backoff and jitter.

### RetryConfig

```python
from scheduler_mcp.error_handling import RetryConfig

config = RetryConfig(
    max_attempts=3,           # Maximum retry attempts
    base_delay=1.0,           # Base delay in seconds
    max_delay=60.0,           # Maximum delay cap
    exponential_base=2.0,     # Exponential multiplier
    jitter=True,              # Add randomness (0-25% of delay)
    retryable_exceptions=(    # Exceptions to retry
        MCPServiceUnavailable,
        MCPTimeoutError,
        asyncio.TimeoutError,
        ConnectionError,
    ),
)
```

### How It Works

1. **First attempt**: Immediate execution
2. **Retry 1**: Wait `base_delay * (exponential_base ^ 0)` = 1.0s
3. **Retry 2**: Wait `base_delay * (exponential_base ^ 1)` = 2.0s
4. **Retry 3**: Wait `base_delay * (exponential_base ^ 2)` = 4.0s
5. Jitter adds 0-25% randomness to prevent thundering herd

### Standalone Usage

```python
from scheduler_mcp.error_handling import retry_with_backoff, RetryConfig

@retry_with_backoff(RetryConfig(max_attempts=5))
async def my_function():
    # Function with retry logic
    pass
```

### With Error Handler

```python
@mcp_error_handler(
    retry_config=RetryConfig(max_attempts=3, base_delay=0.5)
)
async def my_tool():
    # Combines error handling + retry
    pass
```

---

## Circuit Breaker

Prevents cascading failures by opening circuit after threshold failures.

### Circuit States

1. **CLOSED** (normal): All requests pass through
2. **OPEN** (failing): Requests rejected immediately
3. **HALF_OPEN** (testing): Limited requests allowed to test recovery

### State Transitions

```
CLOSED --[threshold failures]--> OPEN
OPEN --[timeout elapsed]--> HALF_OPEN
HALF_OPEN --[success threshold]--> CLOSED
HALF_OPEN --[any failure]--> OPEN
```

### CircuitBreakerConfig

```python
from scheduler_mcp.error_handling import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=5,      # Failures before opening
    success_threshold=2,      # Successes to close from half-open
    timeout=60.0,             # Seconds before half-open test
    half_open_max_calls=3,    # Max concurrent calls in half-open
    monitored_exceptions=(    # Exceptions that trigger circuit
        MCPServiceUnavailable,
        MCPTimeoutError,
        ConnectionError,
    ),
)
```

### Usage with Decorator

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

### Direct Usage

```python
from scheduler_mcp.error_handling import get_circuit_breaker

cb = get_circuit_breaker("my_service")

async def my_operation():
    return "result"

try:
    result = await cb.call(my_operation)
except MCPCircuitOpenError:
    # Circuit is open, service degraded
    pass

# Check circuit state
state = cb.get_state()
print(f"State: {state['state']}")
print(f"Failures: {state['failure_count']}")
```

### Global Registry

Circuit breakers are stored in a global registry by name.

```python
from scheduler_mcp.error_handling import get_all_circuit_breakers

# Get all circuit breaker states
states = get_all_circuit_breakers()
# {
#     "database": {"state": "closed", "failure_count": 0, ...},
#     "api": {"state": "open", "failure_count": 5, ...},
# }
```

---

## Error Metrics

Track error rates and patterns for monitoring and alerting.

### Recording Errors

```python
from scheduler_mcp.error_handling import record_error, MCPErrorCode

record_error(
    error_code=MCPErrorCode.VALIDATION_ERROR,
    tool_name="validate_schedule",
)
```

### Getting Metrics

```python
from scheduler_mcp.error_handling import get_error_metrics

metrics = get_error_metrics()
# {
#     "total_errors": 42,
#     "errors_by_code": {
#         "VALIDATION_ERROR": 20,
#         "TIMEOUT": 10,
#         "SERVICE_UNAVAILABLE": 12,
#     },
#     "errors_by_tool": {
#         "validate_schedule": 15,
#         "analyze_swap": 10,
#     },
#     "last_error_time": 1642254123.456,
#     "circuit_breakers": {...},
# }
```

### Resetting Metrics

```python
from scheduler_mcp.error_handling import reset_error_metrics

reset_error_metrics()  # Useful for testing
```

---

## Best Practices

### 1. Use Appropriate Exception Types

```python
# ✓ Good: Specific exception with context
raise MCPValidationError(
    message="End date must be after start date",
    field="end_date",
    details={"start_date": "2025-01-01", "end_date": "2024-12-31"},
)

# ✗ Bad: Generic exception
raise Exception("Invalid dates")
```

### 2. Don't Leak Sensitive Information

```python
# ✓ Good: Generic user-facing message
raise MCPServiceUnavailable(
    message="Database connection failed",
    service_name="database",
)
# Detailed error logged server-side only

# ✗ Bad: Exposes internal details
raise Exception(f"Connection failed: {db_password}@{db_host}")
```

### 3. Use Circuit Breakers for External Services

```python
# ✓ Good: Protect external service calls
@mcp_error_handler(circuit_breaker_name="external_api")
async def call_external_api():
    pass

# ✗ Bad: No protection, can cascade failures
async def call_external_api():
    pass
```

### 4. Configure Appropriate Retry Strategies

```python
# ✓ Good: Fast retries for transient failures
@mcp_error_handler(
    retry_config=RetryConfig(
        max_attempts=3,
        base_delay=0.5,  # Start with 0.5s
    )
)
async def fetch_cached_data():
    pass

# ✓ Good: Slower retries for heavy operations
@mcp_error_handler(
    retry_config=RetryConfig(
        max_attempts=2,
        base_delay=5.0,  # Start with 5s
    )
)
async def run_heavy_computation():
    pass
```

### 5. Provide Helpful Error Messages

```python
# ✓ Good: Actionable message
raise MCPValidationError(
    message="Assignment conflicts with existing schedule",
    field="assignment_id",
    details={
        "conflicting_assignment": "assign-123",
        "date": "2025-01-15",
        "suggested_action": "Choose a different date or cancel conflicting assignment",
    },
)

# ✗ Bad: Vague message
raise MCPValidationError("Conflict")
```

### 6. Use Correlation IDs for Tracing

```python
# Correlation IDs are automatically generated and logged
@mcp_error_handler
async def my_tool():
    # Errors will have correlation_id in logs and responses
    raise MCPServiceUnavailable("Service down")

# Use correlation ID to trace error across services
# Logs will show: "correlation_id": "abc-123-def-456"
```

---

## Examples

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

## Testing

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

## Integration with MCP Tools

### Updating Existing Tools

Update your MCP tools to use the error handling middleware:

```python
# Before
async def validate_schedule(request):
    try:
        # validation logic
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

# After
from scheduler_mcp.error_handling import mcp_error_handler, RetryConfig

@mcp_error_handler(
    retry_config=RetryConfig(max_attempts=3),
    circuit_breaker_name="validation_service",
)
async def validate_schedule(request):
    # validation logic
    return result
    # Errors automatically handled, logged, and structured
```

### Tool Registration

```python
from scheduler_mcp.error_handling import mcp_error_handler

@mcp.tool()
@mcp_error_handler
async def my_mcp_tool(param: str) -> dict:
    """MCP tool with error handling."""
    # Tool implementation
    pass
```

---

## Error Response Format

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

## Monitoring and Observability

### Metrics Dashboard

Use `get_error_metrics()` to build monitoring dashboards:

```python
from scheduler_mcp.error_handling import get_error_metrics

# Periodic metrics collection
metrics = get_error_metrics()

# Alert on high error rates
if metrics["total_errors"] > threshold:
    send_alert("High error rate detected")

# Monitor circuit breaker states
for name, state in metrics["circuit_breakers"].items():
    if state["state"] == "open":
        send_alert(f"Circuit breaker {name} is OPEN")
```

### Log Correlation

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

## Performance Considerations

### Retry Strategy Impact

- **Fast retries** (< 1s): Suitable for cache misses, network blips
- **Medium retries** (1-5s): Suitable for database connection issues
- **Slow retries** (> 5s): Suitable for external API rate limits

### Circuit Breaker Overhead

- **Minimal overhead** in CLOSED state (~microseconds)
- **Zero request overhead** in OPEN state (immediate rejection)
- **Limited concurrency** in HALF_OPEN state (prevents overload)

### Memory Usage

- Circuit breakers: ~1KB per instance
- Metrics: ~100 bytes per error code/tool combination
- Correlation tracking: ~36 bytes per active request (UUID)

---

## FAQ

### Q: When should I use retry vs circuit breaker?

**A:** Use both together:
- **Retry**: For transient failures (network blips, temporary unavailability)
- **Circuit breaker**: For sustained failures (service down, database unreachable)

Retries handle short-term issues, circuit breakers prevent cascade during prolonged outages.

### Q: What exceptions are retried automatically?

**A:** By default:
- `MCPServiceUnavailable`
- `MCPTimeoutError`
- `asyncio.TimeoutError`
- `ConnectionError`

Validation errors are NOT retried (they won't succeed on retry).

### Q: How do I create a custom error type?

**A:** Inherit from `MCPToolError`:

```python
class MCPCustomError(MCPToolError):
    def __init__(self, message: str, custom_field: str):
        super().__init__(
            message=message,
            error_code=MCPErrorCode.INTERNAL_ERROR,  # or create new code
            details={"custom_field": custom_field},
        )
```

### Q: Can I disable error logging?

**A:** Yes:

```python
@mcp_error_handler(log_errors=False)
async def my_tool():
    pass
```

### Q: How do I test circuit breaker behavior?

**A:** See test examples in `tests/test_error_handling.py`:

```python
async def test_circuit_breaker():
    cb = get_circuit_breaker("test", CircuitBreakerConfig(failure_threshold=2))

    # Trigger failures
    for _ in range(2):
        with pytest.raises(MCPServiceUnavailable):
            await cb.call(failing_function)

    # Circuit should be open
    assert cb.state.state == CircuitState.OPEN
```

---

## Support

For questions or issues:
1. Check examples: `/mcp-server/examples/error_handling_example.py`
2. Review tests: `/mcp-server/tests/test_error_handling.py`
3. Read source: `/mcp-server/src/scheduler_mcp/error_handling.py`
4. File issue on GitHub

---

## License

MIT License - See project LICENSE file for details.
