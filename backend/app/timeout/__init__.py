"""
Request timeout handling package.

Provides:
- Global request timeout via middleware
- Per-endpoint timeout decorators
- Database query timeout support
- Graceful cancellation handling
- Timeout metrics and headers

Usage:
    # Add middleware to app
    from app.timeout.middleware import TimeoutMiddleware
    app.add_middleware(TimeoutMiddleware, default_timeout=30.0)

    # Use decorator for specific endpoints
    from app.timeout.decorators import with_timeout

    @app.get("/long-operation")
    @with_timeout(60.0)
    async def long_operation():
        # This endpoint has a 60s timeout
        pass

    # Use timeout handler directly
    from app.timeout.handler import TimeoutHandler

    async def my_function():
        async with TimeoutHandler(10.0) as handler:
            result = await some_operation()
"""

from app.timeout.decorators import db_timeout, with_timeout
from app.timeout.handler import TimeoutError, TimeoutHandler
from app.timeout.middleware import TimeoutMiddleware

__all__ = [
    "TimeoutHandler",
    "TimeoutError",
    "TimeoutMiddleware",
    "with_timeout",
    "db_timeout",
]
