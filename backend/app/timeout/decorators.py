"""
Timeout decorators for endpoint and database operations.

Provides:
- @with_timeout: Per-endpoint timeout decorator
- @db_timeout: Database query timeout decorator
"""

import asyncio
import logging
from collections.abc import Callable
from functools import wraps

from sqlalchemy.orm import Session

from app.timeout.handler import (
    TimeoutError,
    get_timeout_remaining,
    with_timeout_wrapper,
)

logger = logging.getLogger(__name__)


def with_timeout(timeout: float, error_message: str | None = None):
    """
    Decorator to apply timeout to an async endpoint or function.

    Usage:
        @app.get("/slow-endpoint")
        @with_timeout(60.0)
        async def slow_endpoint():
            # This endpoint has a 60 second timeout
            await some_long_operation()

        # With custom error message
        @with_timeout(30.0, "Report generation timed out")
        async def generate_report():
            pass

    Args:
        timeout: Timeout in seconds
        error_message: Custom error message for timeout

    Returns:
        Decorator function
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if there's already a timeout from middleware
            existing_timeout = get_timeout_remaining()
            if existing_timeout is not None:
                # Use the minimum of existing and decorator timeout
                effective_timeout = min(timeout, existing_timeout)
                logger.debug(
                    f"Using minimum timeout: {effective_timeout}s "
                    f"(decorator: {timeout}s, existing: {existing_timeout}s)"
                )
            else:
                effective_timeout = timeout

            # Execute with timeout
            msg = (
                error_message
                or f"{func.__name__} exceeded timeout of {effective_timeout}s"
            )
            return await with_timeout_wrapper(
                func(*args, **kwargs), timeout=effective_timeout, error_message=msg
            )

        return wrapper

    return decorator


def db_timeout(timeout: float):
    """
    Decorator to apply timeout to database operations.

    Sets SQLAlchemy execution timeout for all queries within the function.
    This prevents slow queries from blocking the application.

    Usage:
        @db_timeout(5.0)
        async def get_complex_data(db: Session):
            # All queries here have a 5 second timeout
            result = db.query(Model).filter(...).all()
            return result

    Args:
        timeout: Database query timeout in seconds

    Returns:
        Decorator function

    Note:
        This uses PostgreSQL's statement_timeout. For other databases,
        you may need to adjust the implementation.
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Find the Session argument
            db_session = None
            for arg in args:
                if isinstance(arg, Session):
                    db_session = arg
                    break

            if db_session is None:
                # Check kwargs
                db_session = kwargs.get("db")

            if db_session is None:
                logger.warning(
                    f"@db_timeout applied to {func.__name__} but no Session found. "
                    "Timeout will not be applied to database queries."
                )
                return await func(*args, **kwargs)

            # Set statement timeout (PostgreSQL)
            timeout_ms = int(timeout * 1000)
            try:
                # Execute SET statement_timeout
                db_session.execute(f"SET statement_timeout = {timeout_ms}")
                logger.debug(f"Set database timeout to {timeout}s for {func.__name__}")

                # Execute the function
                result = await func(*args, **kwargs)

                # Reset timeout
                db_session.execute("RESET statement_timeout")
                return result

            except Exception as e:
                # Reset timeout on error
                try:
                    db_session.execute("RESET statement_timeout")
                except Exception:
                    pass  # Ignore errors during cleanup

                # Check if it's a timeout error
                error_str = str(e).lower()
                if "timeout" in error_str or "canceling statement" in error_str:
                    logger.warning(f"Database query timeout in {func.__name__}: {e}")
                    raise TimeoutError(
                        f"Database query exceeded timeout of {timeout}s",
                        timeout=timeout,
                    ) from e
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Find the Session argument
            db_session = None
            for arg in args:
                if isinstance(arg, Session):
                    db_session = arg
                    break

            if db_session is None:
                # Check kwargs
                db_session = kwargs.get("db")

            if db_session is None:
                logger.warning(
                    f"@db_timeout applied to {func.__name__} but no Session found. "
                    "Timeout will not be applied to database queries."
                )
                return func(*args, **kwargs)

            # Set statement timeout (PostgreSQL)
            timeout_ms = int(timeout * 1000)
            try:
                # Execute SET statement_timeout
                db_session.execute(f"SET statement_timeout = {timeout_ms}")
                logger.debug(f"Set database timeout to {timeout}s for {func.__name__}")

                # Execute the function
                result = func(*args, **kwargs)

                # Reset timeout
                db_session.execute("RESET statement_timeout")
                return result

            except Exception as e:
                # Reset timeout on error
                try:
                    db_session.execute("RESET statement_timeout")
                except Exception:
                    pass  # Ignore errors during cleanup

                # Check if it's a timeout error
                error_str = str(e).lower()
                if "timeout" in error_str or "canceling statement" in error_str:
                    logger.warning(f"Database query timeout in {func.__name__}: {e}")
                    raise TimeoutError(
                        f"Database query exceeded timeout of {timeout}s",
                        timeout=timeout,
                    ) from e
                raise

        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def timeout_remaining(func: Callable):
    """
    Decorator to check remaining timeout before executing function.

    Raises TimeoutError if there's no time remaining from parent timeout.
    Useful for preventing execution of operations that would immediately timeout.

    Usage:
        @timeout_remaining
        async def expensive_operation():
            # Only executes if there's time remaining
            pass

    Args:
        func: Function to wrap

    Returns:
        Wrapped function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        remaining = get_timeout_remaining()
        if remaining is not None and remaining <= 0:
            raise TimeoutError(
                f"{func.__name__} not executed: timeout already exceeded", timeout=0
            )

        return await func(*args, **kwargs)

    return wrapper
