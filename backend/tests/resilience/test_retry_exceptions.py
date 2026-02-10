"""Tests for retry exception classes (pure logic, no DB)."""

import pytest

from app.resilience.retry.exceptions import (
    InvalidRetryConfigError,
    MaxRetriesExceeded,
    NonRetryableError,
    RetryError,
    RetryTimeoutError,
)


# ── RetryError ─────────────────────────────────────────────────────────


class TestRetryError:
    def test_basic_creation(self):
        err = RetryError("something failed")
        assert str(err) == "something failed"
        assert err.attempts == 0
        assert err.last_exception is None

    def test_with_attempts_and_last_exception(self):
        original = ValueError("original")
        err = RetryError("failed", attempts=3, last_exception=original)
        assert err.attempts == 3
        assert err.last_exception is original

    def test_is_exception(self):
        assert issubclass(RetryError, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(RetryError, match="test error"):
            raise RetryError("test error")


# ── MaxRetriesExceeded ─────────────────────────────────────────────────


class TestMaxRetriesExceeded:
    def test_default_message(self):
        err = MaxRetriesExceeded(attempts=5)
        assert "5" in str(err)
        assert "operation" in str(err)

    def test_custom_operation(self):
        err = MaxRetriesExceeded(attempts=3, operation="db_connect")
        assert "db_connect" in str(err)
        assert "3" in str(err)

    def test_with_last_exception(self):
        original = ConnectionError("refused")
        err = MaxRetriesExceeded(attempts=3, last_exception=original)
        assert err.last_exception is original
        assert err.attempts == 3

    def test_is_retry_error(self):
        assert issubclass(MaxRetriesExceeded, RetryError)

    def test_operation_stored(self):
        err = MaxRetriesExceeded(attempts=3, operation="my_op")
        assert err.operation == "my_op"

    def test_can_be_caught_as_retry_error(self):
        with pytest.raises(RetryError):
            raise MaxRetriesExceeded(attempts=5)


# ── NonRetryableError ──────────────────────────────────────────────────


class TestNonRetryableError:
    def test_basic_creation(self):
        err = NonRetryableError("cannot retry")
        assert str(err) == "cannot retry"
        assert err.original_exception is None

    def test_with_original_exception(self):
        original = PermissionError("access denied")
        err = NonRetryableError("cannot retry", original_exception=original)
        assert err.original_exception is original
        assert err.last_exception is original

    def test_is_retry_error(self):
        assert issubclass(NonRetryableError, RetryError)

    def test_attempts_always_zero(self):
        err = NonRetryableError("no retry")
        assert err.attempts == 0


# ── RetryTimeoutError ──────────────────────────────────────────────────


class TestRetryTimeoutError:
    def test_basic_creation(self):
        err = RetryTimeoutError(timeout_seconds=30.0)
        assert "30.0" in str(err) or "30" in str(err)
        assert err.timeout_seconds == 30.0
        assert err.attempts == 0

    def test_with_attempts(self):
        err = RetryTimeoutError(timeout_seconds=60.0, attempts=5)
        assert err.attempts == 5
        assert "5" in str(err)

    def test_with_last_exception(self):
        original = TimeoutError("connection timed out")
        err = RetryTimeoutError(timeout_seconds=10.0, last_exception=original)
        assert err.last_exception is original

    def test_is_retry_error(self):
        assert issubclass(RetryTimeoutError, RetryError)


# ── InvalidRetryConfigError ───────────────────────────────────────────


class TestInvalidRetryConfigError:
    def test_basic_creation(self):
        err = InvalidRetryConfigError("bad config")
        assert str(err) == "bad config"
        assert err.config_field is None

    def test_with_config_field(self):
        err = InvalidRetryConfigError("invalid value", config_field="max_retries")
        assert err.config_field == "max_retries"

    def test_is_retry_error(self):
        assert issubclass(InvalidRetryConfigError, RetryError)

    def test_can_be_caught_as_retry_error(self):
        with pytest.raises(RetryError):
            raise InvalidRetryConfigError("invalid")


# ── Exception hierarchy ───────────────────────────────────────────────


class TestExceptionHierarchy:
    def test_all_subclass_retry_error(self):
        assert issubclass(MaxRetriesExceeded, RetryError)
        assert issubclass(NonRetryableError, RetryError)
        assert issubclass(RetryTimeoutError, RetryError)
        assert issubclass(InvalidRetryConfigError, RetryError)

    def test_all_subclass_exception(self):
        for cls in [
            RetryError,
            MaxRetriesExceeded,
            NonRetryableError,
            RetryTimeoutError,
            InvalidRetryConfigError,
        ]:
            assert issubclass(cls, Exception)

    def test_catch_all_with_retry_error(self):
        """All retry exceptions caught by catching RetryError."""
        for cls, args in [
            (MaxRetriesExceeded, (3,)),
            (NonRetryableError, ("no",)),
            (RetryTimeoutError, (10.0,)),
            (InvalidRetryConfigError, ("bad",)),
        ]:
            with pytest.raises(RetryError):
                raise cls(*args)
