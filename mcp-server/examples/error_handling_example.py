"""
Example usage of MCP error handling middleware.

This module demonstrates how to use the error handling features
in MCP tools including decorators, retry logic, and circuit breakers.
"""

import asyncio
from datetime import date
from typing import Any

from scheduler_mcp.error_handling import (
    # Exceptions
    MCPValidationError,
    MCPServiceUnavailable,
    MCPTimeoutError,
    MCPErrorCode,
    # Decorators
    mcp_error_handler,
    RetryConfig,
    CircuitBreakerConfig,
    # Utilities
    get_circuit_breaker,
    get_error_metrics,
)


# ============================================================================
# Example 1: Basic Error Handler
# ============================================================================


@mcp_error_handler
async def validate_schedule_dates(start_date: str, end_date: str) -> dict[str, Any]:
    """
    Validate schedule date range.

    The @mcp_error_handler decorator automatically:
    - Catches exceptions and converts them to structured errors
    - Logs errors with correlation IDs
    - Returns proper error responses

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Validation result

    Raises:
        MCPValidationError: If dates are invalid
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as e:
        # ValueError is automatically converted to MCPValidationError
        raise ValueError(f"Invalid date format: {e}")

    if end < start:
        # Explicit validation error with field information
        raise MCPValidationError(
            message="End date must be after start date",
            field="end_date",
            details={
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    return {
        "valid": True,
        "start_date": start_date,
        "end_date": end_date,
        "days": (end - start).days,
    }


# ============================================================================
# Example 2: Error Handler with Retry Logic
# ============================================================================


@mcp_error_handler(
    retry_config=RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        exponential_base=2.0,
        jitter=True,
    )
)
async def fetch_schedule_from_api(schedule_id: str) -> dict[str, Any]:
    """
    Fetch schedule from backend API with automatic retry.

    If the API is temporarily unavailable or times out, the decorator
    will automatically retry with exponential backoff.

    Args:
        schedule_id: Schedule identifier

    Returns:
        Schedule data

    Raises:
        MCPServiceUnavailable: If API is unavailable after all retries
        MCPTimeoutError: If request times out after all retries
    """
    # Simulate API call
    # In real implementation, this would use httpx or similar
    import random

    if random.random() < 0.3:  # 30% chance of transient failure
        raise MCPServiceUnavailable(
            "Backend API temporarily unavailable",
            service_name="schedule_api",
            retry_after=5,
        )

    # Successful response
    return {
        "schedule_id": schedule_id,
        "assignments": [],
        "status": "active",
    }


# ============================================================================
# Example 3: Error Handler with Circuit Breaker
# ============================================================================


@mcp_error_handler(
    circuit_breaker_name="database",
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=5,  # Open after 5 failures
        success_threshold=2,  # Close after 2 successes in half-open
        timeout=60.0,  # Try half-open after 60 seconds
    ),
)
async def query_database(query: str) -> dict[str, Any]:
    """
    Query database with circuit breaker protection.

    If the database is experiencing issues, the circuit breaker will
    open and reject requests immediately, preventing cascading failures.
    It will periodically test recovery.

    Args:
        query: Database query

    Returns:
        Query results

    Raises:
        MCPCircuitOpenError: If circuit breaker is open
        MCPServiceUnavailable: If database is unavailable
    """
    # Simulate database query
    # In real implementation, this would use SQLAlchemy
    try:
        # Simulate potential database issues
        await asyncio.sleep(0.1)
        return {"results": [], "count": 0}
    except Exception as e:
        raise MCPServiceUnavailable(
            "Database connection failed",
            service_name="database",
            retry_after=30,
        )


# ============================================================================
# Example 4: Combining Retry and Circuit Breaker
# ============================================================================


@mcp_error_handler(
    retry_config=RetryConfig(max_attempts=3, base_delay=0.5),
    circuit_breaker_name="resilience_api",
    circuit_breaker_config=CircuitBreakerConfig(failure_threshold=10),
)
async def run_resilience_check() -> dict[str, Any]:
    """
    Run resilience health check with both retry and circuit breaker.

    This combines:
    1. Retry logic for transient failures
    2. Circuit breaker for persistent failures
    3. Automatic error handling and logging

    Returns:
        Resilience check results

    Raises:
        MCPCircuitOpenError: If circuit is open
        MCPServiceUnavailable: If service is unavailable
    """
    # Simulate resilience API call
    return {
        "status": "healthy",
        "safety_level": "GREEN",
        "checks_passed": 8,
        "checks_failed": 0,
    }


# ============================================================================
# Example 5: Manual Error Handling
# ============================================================================


async def manual_error_handling_example() -> dict[str, Any]:
    """
    Example of manual error handling without decorator.

    Use this approach when you need more control over error handling
    or want to handle different errors differently.

    Returns:
        Operation result or error response
    """
    try:
        # Your operation here
        result = await some_risky_operation()
        return {"success": True, "result": result}

    except MCPValidationError as e:
        # Handle validation errors
        print(f"Validation failed: {e.message}")
        return e.to_dict()

    except MCPServiceUnavailable as e:
        # Handle service unavailable
        print(f"Service unavailable: {e.message}, retry after {e.retry_after}s")
        return e.to_dict()

    except Exception as e:
        # Catch-all for unexpected errors
        error = MCPValidationError(
            message="An unexpected error occurred",
            details={"error_type": type(e).__name__},
        )
        return error.to_dict()


async def some_risky_operation() -> str:
    """Placeholder for demonstration."""
    return "success"


# ============================================================================
# Example 6: Using Circuit Breaker Directly
# ============================================================================


async def direct_circuit_breaker_usage() -> None:
    """
    Example of using circuit breaker directly without decorator.

    This gives you more control over circuit breaker behavior.
    """
    # Get or create circuit breaker
    cb = get_circuit_breaker(
        "my_service",
        CircuitBreakerConfig(
            failure_threshold=3,
            timeout=30.0,
        ),
    )

    # Use circuit breaker
    try:
        async def my_operation():
            # Your operation here
            return "success"

        result = await cb.call(my_operation)
        print(f"Operation succeeded: {result}")

    except MCPServiceUnavailable as e:
        print(f"Service unavailable: {e.message}")

    # Check circuit breaker state
    state = cb.get_state()
    print(f"Circuit breaker state: {state['state']}")
    print(f"Failure count: {state['failure_count']}")


# ============================================================================
# Example 7: Monitoring Error Metrics
# ============================================================================


async def monitor_errors() -> dict[str, Any]:
    """
    Example of monitoring error metrics.

    Use this to track error rates and circuit breaker states
    for observability and alerting.

    Returns:
        Error metrics
    """
    metrics = get_error_metrics()

    print(f"Total errors: {metrics['total_errors']}")
    print(f"Errors by code: {metrics['errors_by_code']}")
    print(f"Errors by tool: {metrics['errors_by_tool']}")
    print(f"Circuit breakers: {metrics['circuit_breakers']}")

    return metrics


# ============================================================================
# Example 8: Structured Error Response
# ============================================================================


async def structured_error_example() -> dict[str, Any]:
    """
    Example of creating structured error responses.

    All MCP errors can be converted to dictionaries with
    consistent structure for API responses.

    Returns:
        Error response dictionary
    """
    try:
        # Operation that might fail
        raise MCPTimeoutError(
            message="Schedule validation timed out",
            timeout_seconds=30.0,
            operation="acgme_validation",
            retry_after=10,
        )

    except MCPTimeoutError as e:
        # Convert to structured response
        error_response = e.to_dict()

        """
        error_response will be:
        {
            "error": true,
            "error_code": "TIMEOUT",
            "message": "Schedule validation timed out",
            "correlation_id": "unique-uuid",
            "timestamp": "2025-01-15T10:30:00",
            "details": {
                "timeout_seconds": 30.0,
                "operation": "acgme_validation"
            },
            "retry_after": 10
        }
        """

        return error_response


# ============================================================================
# Main Example Runner
# ============================================================================


async def main():
    """Run all examples."""
    print("=" * 70)
    print("MCP Error Handling Examples")
    print("=" * 70)

    # Example 1: Basic validation
    print("\n1. Basic Error Handler:")
    try:
        result = await validate_schedule_dates("2025-01-01", "2025-01-31")
        print(f"   ✓ Valid dates: {result['days']} days")
    except MCPValidationError as e:
        print(f"   ✗ Validation error: {e.message}")

    try:
        await validate_schedule_dates("2025-01-31", "2025-01-01")
    except MCPValidationError as e:
        print(f"   ✗ Expected error: {e.message}")

    # Example 2: Retry logic
    print("\n2. Retry Logic:")
    try:
        result = await fetch_schedule_from_api("schedule-123")
        print(f"   ✓ Fetched schedule: {result['schedule_id']}")
    except MCPServiceUnavailable as e:
        print(f"   ✗ Service unavailable: {e.message}")

    # Example 3: Circuit breaker
    print("\n3. Circuit Breaker:")
    try:
        result = await query_database("SELECT * FROM schedules")
        print(f"   ✓ Query returned {result['count']} results")
    except Exception as e:
        print(f"   ✗ Error: {type(e).__name__}: {e}")

    # Example 4: Monitoring
    print("\n4. Error Metrics:")
    metrics = await monitor_errors()
    print(f"   Total errors tracked: {metrics['total_errors']}")

    # Example 5: Structured error
    print("\n5. Structured Error Response:")
    error_response = await structured_error_example()
    print(f"   Error code: {error_response['error_code']}")
    print(f"   Retry after: {error_response['retry_after']}s")

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
