"""Transaction management utilities.

Provides robust transaction management with:
- Automatic commit on success
- Automatic rollback on failure
- Savepoint support for nested transactions
- Transaction timeout handling
- Transaction retry logic with exponential backoff
- Transaction metrics and logging
"""

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, TypeVar

from sqlalchemy import exc as sa_exc
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Type variable for decorator
F = TypeVar("F", bound=Callable[..., Any])


class TransactionError(Exception):
    """Base exception for transaction errors."""

    pass


class TransactionTimeout(TransactionError):
    """Transaction exceeded timeout limit."""

    pass


class TransactionRetryExhausted(TransactionError):
    """All transaction retry attempts failed."""

    pass


@contextmanager
def transactional(
    session: Session,
    use_savepoint: bool = False,
    timeout_seconds: float | None = None,
    readonly: bool = False,
):
    """
    Context manager for safe transactional operations.

    Ensures:
    - Automatic commit on success
    - Automatic rollback on exception
    - Optional savepoint support for nested transactions
    - Optional timeout enforcement
    - Optional read-only mode

    Args:
        session: SQLAlchemy session
        use_savepoint: Use SAVEPOINT for nested transactions
        timeout_seconds: Optional timeout for transaction
        readonly: Mark transaction as read-only (no commit)

    Usage:
        with transactional(session) as txn:
            # Do work
            session.add(obj)
            # Auto-commit on success, rollback on exception

        # Nested transaction with savepoint:
        with transactional(session) as outer:
            session.add(obj1)
            try:
                with transactional(session, use_savepoint=True) as inner:
                    session.add(obj2)
                    raise ValueError()  # Inner rollback only
            except ValueError:
                pass
            # obj1 still committed, obj2 rolled back

    Raises:
        TransactionTimeout: If transaction exceeds timeout
    """
    start_time = time.time()
    savepoint = None

    try:
        if use_savepoint:
            # Create savepoint for nested transaction
            savepoint = session.begin_nested()
            logger.debug("Started nested transaction with savepoint")
        else:
            # Check if we're already in a transaction
            if not session.in_transaction():
                session.begin()
                logger.debug("Started new transaction")

        yield session

        # Check timeout before commit
        if timeout_seconds:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise TransactionTimeout(
                    f"Transaction exceeded timeout of {timeout_seconds}s (took {elapsed:.2f}s)"
                )

        # Commit transaction
        if not readonly:
            if savepoint:
                savepoint.commit()
                logger.debug("Committed savepoint")
            else:
                session.commit()
                elapsed = time.time() - start_time
                logger.debug(f"Committed transaction in {elapsed:.3f}s")

    except Exception as e:
        # Rollback on any exception
        if savepoint:
            savepoint.rollback()
            logger.warning(f"Rolled back savepoint: {e}")
        else:
            session.rollback()
            logger.warning(f"Rolled back transaction: {e}")
        raise


@contextmanager
def transactional_with_retry(
    session: Session,
    max_retries: int = 3,
    initial_backoff: float = 0.1,
    max_backoff: float = 2.0,
    timeout_seconds: float | None = None,
):
    """
    Context manager for transactional operations with automatic retry.

    Retries on deadlock detection and serialization failures.

    Args:
        session: SQLAlchemy session
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        timeout_seconds: Optional timeout per attempt

    Usage:
        with transactional_with_retry(session, max_retries=3) as txn:
            # Operations that might deadlock
            session.query(Model).with_for_update().filter(...)

    Raises:
        TransactionRetryExhausted: If all retries fail
    """
    retries = 0
    backoff = initial_backoff

    while retries <= max_retries:
        try:
            with transactional(session, timeout_seconds=timeout_seconds):
                yield session
                return  # Success, exit retry loop

        except (sa_exc.OperationalError, sa_exc.DBAPIError) as e:
            # Check if it's a retryable error (deadlock, serialization failure)
            error_msg = str(e).lower()
            is_retryable = any(
                keyword in error_msg
                for keyword in ["deadlock", "serialization", "lock timeout"]
            )

            if not is_retryable or retries >= max_retries:
                if retries >= max_retries:
                    logger.error(
                        f"Transaction retry exhausted after {retries} attempts: {e}"
                    )
                    raise TransactionRetryExhausted(
                        f"Failed after {max_retries} retries: {e}"
                    ) from e
                raise

            # Retry with exponential backoff
            retries += 1
            logger.warning(
                f"Transaction retry {retries}/{max_retries} after error: {e}. "
                f"Backing off {backoff:.2f}s"
            )
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)


def transactional_decorator(
    use_savepoint: bool = False,
    timeout_seconds: float | None = None,
    readonly: bool = False,
    max_retries: int = 0,
):
    """
    Decorator for transactional functions.

    The decorated function must accept a `session` parameter.

    Args:
        use_savepoint: Use SAVEPOINT for nested transactions
        timeout_seconds: Optional timeout for transaction
        readonly: Mark transaction as read-only
        max_retries: Number of retry attempts (0 = no retry)

    Usage:
        @transactional_decorator(timeout_seconds=5.0)
        def my_service_method(session: Session, arg1, arg2):
            # Do work
            session.add(obj)
            # Auto-commit on success

        # With retry:
        @transactional_decorator(max_retries=3)
        def update_with_locking(session: Session, id: str):
            obj = session.query(Model).with_for_update().filter_by(id=id).one()
            obj.value += 1
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract session from args or kwargs
            session = None
            if "session" in kwargs:
                session = kwargs["session"]
            elif len(args) > 0 and isinstance(args[0], Session):
                session = args[0]
            else:
                # Try to find session in args
                for arg in args:
                    if isinstance(arg, Session):
                        session = arg
                        break

            if not session:
                raise ValueError(
                    f"Function {func.__name__} requires a Session parameter"
                )

            # Execute with appropriate transaction wrapper
            if max_retries > 0:
                with transactional_with_retry(
                    session,
                    max_retries=max_retries,
                    timeout_seconds=timeout_seconds,
                ):
                    return func(*args, **kwargs)
            else:
                with transactional(
                    session,
                    use_savepoint=use_savepoint,
                    timeout_seconds=timeout_seconds,
                    readonly=readonly,
                ):
                    return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


@contextmanager
def optimistic_lock_retry(
    session: Session,
    max_retries: int = 5,
    initial_backoff: float = 0.05,
):
    """
    Context manager for optimistic locking with version column.

    Automatically retries on StaleDataError (optimistic lock failure).

    Args:
        session: SQLAlchemy session
        max_retries: Maximum retry attempts
        initial_backoff: Initial backoff time

    Usage:
        with optimistic_lock_retry(session) as txn:
            obj = session.query(Model).filter_by(id=id).one()
            obj.value += 1  # Increments version_id automatically
            session.flush()
    """
    retries = 0
    backoff = initial_backoff

    while retries <= max_retries:
        try:
            with transactional(session):
                yield session
                return

        except sa_exc.StaleDataError as e:
            if retries >= max_retries:
                logger.error(
                    f"Optimistic lock retry exhausted after {retries} attempts"
                )
                raise TransactionRetryExhausted(
                    f"Optimistic lock failed after {max_retries} retries"
                ) from e

            retries += 1
            logger.debug(
                f"Optimistic lock conflict, retry {retries}/{max_retries}. "
                f"Backing off {backoff:.3f}s"
            )
            time.sleep(backoff)
            backoff *= 1.5


def lock_ordering_key(model_class: type, entity_id: Any) -> tuple[str, Any]:
    """
    Generate a consistent lock ordering key to prevent deadlocks.

    Deadlocks occur when transactions acquire locks in different orders.
    This function generates a consistent key for sorting lock acquisitions.

    Args:
        model_class: SQLAlchemy model class
        entity_id: Entity ID

    Returns:
        Tuple of (table_name, entity_id) for sorting

    Usage:
        # Acquire locks in consistent order
        locks_needed = [
            (Assignment, id1),
            (SwapRecord, id2),
            (Assignment, id3),
        ]

        # Sort by lock ordering key
        locks_sorted = sorted(locks_needed, key=lambda x: lock_ordering_key(*x))

        # Acquire in order
        for model, id in locks_sorted:
            obj = session.query(model).with_for_update().filter_by(id=id).one()
    """
    table_name = model_class.__tablename__
    return (table_name, entity_id)


class TransactionMetrics:
    """Track transaction performance metrics."""

    def __init__(self):
        self.total_transactions = 0
        self.successful_transactions = 0
        self.failed_transactions = 0
        self.total_duration = 0.0
        self.max_duration = 0.0
        self.min_duration = float("inf")

    def record_success(self, duration: float):
        """Record a successful transaction."""
        self.total_transactions += 1
        self.successful_transactions += 1
        self.total_duration += duration
        self.max_duration = max(self.max_duration, duration)
        self.min_duration = min(self.min_duration, duration)

    def record_failure(self, duration: float):
        """Record a failed transaction."""
        self.total_transactions += 1
        self.failed_transactions += 1
        self.total_duration += duration

    def get_stats(self) -> dict[str, Any]:
        """Get transaction statistics."""
        avg_duration = (
            self.total_duration / self.total_transactions
            if self.total_transactions > 0
            else 0.0
        )
        success_rate = (
            self.successful_transactions / self.total_transactions
            if self.total_transactions > 0
            else 0.0
        )

        return {
            "total_transactions": self.total_transactions,
            "successful_transactions": self.successful_transactions,
            "failed_transactions": self.failed_transactions,
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration,
            "max_duration_seconds": self.max_duration,
            "min_duration_seconds": (
                self.min_duration if self.min_duration != float("inf") else 0.0
            ),
        }


# Global metrics instance
transaction_metrics = TransactionMetrics()


@contextmanager
def tracked_transaction(session: Session, **kwargs):
    """
    Context manager that tracks transaction metrics.

    Args:
        session: SQLAlchemy session
        **kwargs: Additional args passed to transactional()

    Usage:
        with tracked_transaction(session) as txn:
            # Do work
            pass

        # Later, get metrics:
        stats = transaction_metrics.get_stats()
    """
    start_time = time.time()
    success = False

    try:
        with transactional(session, **kwargs):
            yield session
            success = True

    finally:
        duration = time.time() - start_time
        if success:
            transaction_metrics.record_success(duration)
        else:
            transaction_metrics.record_failure(duration)
