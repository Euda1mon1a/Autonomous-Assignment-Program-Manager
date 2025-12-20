# Request Timeout Handling

Comprehensive timeout handling for FastAPI with support for global request timeouts, per-endpoint timeouts, database query timeouts, and graceful cancellation.

## Features

- **Global Request Timeout**: Middleware-based timeout for all requests
- **Per-Endpoint Timeouts**: Decorator-based timeout control
- **Database Query Timeout**: Prevent slow queries from blocking
- **Timeout Headers**: Response headers showing timeout status
- **Graceful Cancellation**: Proper cleanup on timeout
- **Nested Timeout Support**: Automatic minimum timeout selection
- **Prometheus Metrics**: Track timeout events

## Installation

Add the timeout middleware to your FastAPI application:

```python
from fastapi import FastAPI
from app.timeout.middleware import TimeoutMiddleware

app = FastAPI()

# Add timeout middleware with 30s default timeout
app.add_middleware(
    TimeoutMiddleware,
    default_timeout=30.0,
    timeout_header=True,
    exclude_paths=["/health", "/metrics"]
)
```

## Usage Examples

### 1. Global Request Timeout (Middleware)

All requests will timeout after the default duration (30s in example above):

```python
@app.get("/api/data")
async def get_data():
    # This endpoint inherits the 30s global timeout
    data = await fetch_data()
    return data
```

### 2. Per-Endpoint Timeout (Decorator)

Override the global timeout for specific endpoints:

```python
from app.timeout.decorators import with_timeout

@app.get("/api/long-report")
@with_timeout(120.0)  # 2 minute timeout for this endpoint
async def generate_report():
    report = await generate_complex_report()
    return report

@app.get("/api/quick-check")
@with_timeout(5.0, error_message="Health check timed out")
async def quick_check():
    status = await check_status()
    return status
```

### 3. Database Query Timeout

Prevent slow database queries from blocking:

```python
from app.timeout.decorators import db_timeout
from sqlalchemy.orm import Session

@app.get("/api/complex-query")
@db_timeout(10.0)  # 10s timeout for database queries
async def complex_query(db: Session):
    # All database queries in this function have 10s timeout
    result = db.query(Model).filter(...).all()
    return result
```

### 4. Manual Timeout Handling

Use the timeout handler directly for fine-grained control:

```python
from app.timeout.handler import TimeoutHandler

@app.get("/api/multi-step")
async def multi_step_operation():
    async with TimeoutHandler(60.0) as handler:
        # Step 1
        result1 = await step1()

        # Check remaining time
        remaining = handler.get_remaining_time()
        if remaining < 10:
            # Not enough time for step 2
            return {"partial": result1}

        # Step 2
        result2 = await step2()

        return {"result1": result1, "result2": result2}
```

### 5. Check Remaining Time

Access timeout information from context:

```python
from app.timeout.handler import get_timeout_remaining, get_timeout_elapsed

@app.get("/api/adaptive")
async def adaptive_operation():
    remaining = get_timeout_remaining()

    if remaining and remaining < 5:
        # Use fast algorithm
        return await quick_algorithm()
    else:
        # Use thorough algorithm
        return await thorough_algorithm()
```

### 6. Timeout Remaining Guard

Prevent execution if timeout already exceeded:

```python
from app.timeout.decorators import timeout_remaining

@timeout_remaining
async def expensive_operation():
    # Only executes if there's time remaining
    return await do_expensive_work()
```

## Configuration

### Middleware Options

```python
app.add_middleware(
    TimeoutMiddleware,
    default_timeout=30.0,        # Default timeout in seconds
    timeout_header=True,          # Include timeout headers in response
    exclude_paths=["/health"]     # Paths to exclude from timeout
)
```

### Environment Variables

Add to `.env` for application-wide timeout configuration:

```bash
# Default request timeout (seconds)
REQUEST_TIMEOUT=30

# Database query timeout (seconds)
DB_QUERY_TIMEOUT=10
```

## Response Headers

When `timeout_header=True`, responses include:

- `X-Timeout-Limit`: Total timeout duration (seconds)
- `X-Timeout-Elapsed`: Time spent processing request (seconds)
- `X-Timeout-Remaining`: Time remaining before timeout (seconds)

Example:
```
X-Timeout-Limit: 30.0
X-Timeout-Elapsed: 2.456
X-Timeout-Remaining: 27.544
```

## Error Responses

Timeout errors return HTTP 504 Gateway Timeout:

```json
{
  "detail": "Request exceeded timeout of 30s",
  "timeout": 30.0,
  "elapsed": 31.234
}
```

## Metrics

When Prometheus is available, timeout metrics are recorded:

- `http_request_timeouts_total`: Count of timed out requests (by method, path, type)
- `http_request_timeout_duration_seconds`: Duration histogram of timeouts (by method, path)

## Best Practices

### 1. Choose Appropriate Timeouts

- **Quick APIs** (data retrieval): 5-10s
- **Standard operations**: 30s (default)
- **Complex operations** (reports, analytics): 60-120s
- **Background jobs**: Use Celery instead of long HTTP timeouts

### 2. Use Database Timeouts

Always use `@db_timeout` for endpoints with complex queries:

```python
@app.get("/api/analytics")
@db_timeout(15.0)  # Prevent slow queries
async def analytics(db: Session):
    return await complex_query(db)
```

### 3. Nested Timeout Handling

Timeouts automatically use the minimum value:

```python
# Global: 30s
@with_timeout(10.0)  # Endpoint: 10s
async def operation():
    async with TimeoutHandler(5.0):  # Function: 5s
        # Effective timeout: 5s (minimum)
        pass
```

### 4. Graceful Degradation

Check remaining time and adapt:

```python
@app.get("/api/search")
async def search(query: str):
    remaining = get_timeout_remaining()

    if remaining and remaining < 10:
        # Quick search
        return await quick_search(query)
    else:
        # Thorough search
        return await deep_search(query)
```

### 5. Exclude Health Checks

Always exclude monitoring endpoints:

```python
app.add_middleware(
    TimeoutMiddleware,
    exclude_paths=["/health", "/metrics", "/readiness"]
)
```

## Testing

```python
import pytest
from app.timeout.handler import TimeoutHandler, TimeoutError

async def test_timeout():
    """Test operation timeout."""
    with pytest.raises(TimeoutError):
        async with TimeoutHandler(0.1):
            await asyncio.sleep(1.0)

async def test_success():
    """Test operation within timeout."""
    async with TimeoutHandler(1.0) as handler:
        await asyncio.sleep(0.1)
        assert handler.get_remaining_time() > 0
```

## Advanced Usage

### Custom Timeout Logic

```python
from app.timeout.handler import TimeoutHandler, TimeoutError

@app.post("/api/batch-process")
async def batch_process(items: list):
    async with TimeoutHandler(60.0) as handler:
        results = []

        for item in items:
            # Check if we have time
            if handler.get_remaining_time() < 5:
                # Save partial results
                await save_partial(results)
                raise TimeoutError(
                    f"Processed {len(results)}/{len(items)} items before timeout"
                )

            result = await process_item(item)
            results.append(result)

        return {"results": results, "completed": True}
```

### Adaptive Algorithms

```python
@app.get("/api/optimization")
async def optimize(problem: dict):
    remaining = get_timeout_remaining() or 30.0

    if remaining > 60:
        # Use optimal but slow algorithm
        return await optimal_solve(problem)
    elif remaining > 10:
        # Use good heuristic
        return await heuristic_solve(problem)
    else:
        # Use fast approximation
        return await quick_solve(problem)
```

## Troubleshooting

### Timeout Not Applied

- Verify middleware is added: `app.middleware_stack` should include `TimeoutMiddleware`
- Check if path is in `exclude_paths`
- Ensure decorator is applied in correct order (after route decorator)

### Timeout Too Short/Long

- Check nested timeouts - minimum is used
- Review global timeout setting in middleware
- Verify decorator timeout value

### Database Timeout Not Working

- Ensure PostgreSQL is being used (uses `statement_timeout`)
- Check that `Session` is passed to decorated function
- Verify timeout is set before queries execute

## See Also

- [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/advanced/middleware/)
- [asyncio Timeouts](https://docs.python.org/3/library/asyncio-task.html#timeouts)
- [SQLAlchemy Query Timeout](https://docs.sqlalchemy.org/en/14/core/connections.html#setting-alternate-search-paths-on-connect)
