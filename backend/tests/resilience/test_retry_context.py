"""Tests for retry context tracking (pure logic, no DB)."""

from datetime import datetime, timedelta

import pytest

from app.resilience.retry.context import RetryAttempt, RetryContext


# ── RetryAttempt dataclass ─────────────────────────────────────────────


class TestRetryAttempt:
    def test_creation(self):
        ts = datetime(2026, 1, 15, 10, 0, 0)
        attempt = RetryAttempt(
            attempt_number=1,
            timestamp=ts,
            delay_before=2.0,
        )
        assert attempt.attempt_number == 1
        assert attempt.timestamp == ts
        assert attempt.delay_before == 2.0
        assert attempt.exception is None
        assert attempt.success is False
        assert attempt.duration == 0.0

    def test_with_exception(self):
        exc = ValueError("test error")
        attempt = RetryAttempt(
            attempt_number=2,
            timestamp=datetime(2026, 1, 15),
            delay_before=1.0,
            exception=exc,
        )
        assert attempt.exception is exc

    def test_successful(self):
        attempt = RetryAttempt(
            attempt_number=3,
            timestamp=datetime(2026, 1, 15),
            delay_before=0.0,
            success=True,
            duration=0.5,
        )
        assert attempt.success is True
        assert attempt.duration == 0.5


# ── RetryContext init & properties ─────────────────────────────────────


class TestRetryContextInit:
    def test_basic_init(self):
        ctx = RetryContext(operation_name="test_op", max_attempts=3)
        assert ctx.operation_name == "test_op"
        assert ctx.max_attempts == 3
        assert ctx.attempts == []
        assert ctx.last_delay == 0.0

    def test_attempt_count_empty(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        assert ctx.attempt_count == 0

    def test_callbacks_default_none(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        assert ctx.on_retry is None
        assert ctx.on_success is None
        assert ctx.on_failure is None

    def test_elapsed_time(self):
        ctx = RetryContext(
            operation_name="test",
            max_attempts=3,
            start_time=datetime.utcnow() - timedelta(seconds=5),
        )
        assert ctx.elapsed_seconds >= 4.0  # At least 4s elapsed

    def test_total_delay_empty(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        assert ctx.total_delay == 0.0


# ── RetryContext.last_exception ─────────────────────────────────────────


class TestLastException:
    def test_no_attempts(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        assert ctx.last_exception is None

    def test_no_exception_in_attempts(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt(success=True)
        assert ctx.last_exception is None

    def test_returns_last_exception(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        exc1 = ValueError("first")
        exc2 = RuntimeError("second")
        ctx.record_attempt(exception=exc1)
        ctx.record_attempt(exception=exc2)
        assert ctx.last_exception is exc2

    def test_skips_successful_attempts(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        exc = ValueError("error")
        ctx.record_attempt(exception=exc)
        ctx.record_attempt(success=True)
        # Last attempt has no exception, so we get the earlier one
        assert ctx.last_exception is exc


# ── RetryContext.record_attempt ────────────────────────────────────────


class TestRecordAttempt:
    def test_increments_count(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt(success=True)
        assert ctx.attempt_count == 1
        ctx.record_attempt(exception=ValueError("e"))
        assert ctx.attempt_count == 2

    def test_attempt_number_sequential(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt()
        ctx.record_attempt()
        ctx.record_attempt()
        assert ctx.attempts[0].attempt_number == 1
        assert ctx.attempts[1].attempt_number == 2
        assert ctx.attempts[2].attempt_number == 3

    def test_updates_last_delay(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt(delay_before=5.0)
        assert ctx.last_delay == 5.0

    def test_total_delay_accumulated(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt(delay_before=1.0)
        ctx.record_attempt(delay_before=2.0)
        ctx.record_attempt(delay_before=3.0)
        assert ctx.total_delay == 6.0

    def test_records_duration(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt(duration=1.5)
        assert ctx.attempts[0].duration == 1.5


# ── RetryContext callbacks ─────────────────────────────────────────────


class TestCallbacks:
    def test_trigger_retry_callback(self):
        called = []
        ctx = RetryContext(
            operation_name="test",
            max_attempts=3,
            on_retry=lambda ctx, exc, delay: called.append(
                ("retry", type(exc).__name__, delay)
            ),
        )
        ctx.trigger_retry_callback(ValueError("err"), 2.0)
        assert len(called) == 1
        assert called[0] == ("retry", "ValueError", 2)

    def test_retry_callback_none_no_error(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        # Should not raise
        ctx.trigger_retry_callback(ValueError("err"), 1.0)

    def test_retry_callback_exception_swallowed(self):
        """Callback errors are logged, not re-raised."""

        def bad_callback(ctx, exc, delay):
            raise RuntimeError("callback error")

        ctx = RetryContext(operation_name="test", max_attempts=3, on_retry=bad_callback)
        # Should not raise
        ctx.trigger_retry_callback(ValueError("err"), 1.0)

    def test_trigger_success_callback(self):
        called = []
        ctx = RetryContext(
            operation_name="test",
            max_attempts=3,
            on_success=lambda ctx, result: called.append(result),
        )
        ctx.trigger_success_callback("ok")
        assert called == ["ok"]

    def test_success_callback_none_no_error(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.trigger_success_callback("result")

    def test_success_callback_exception_swallowed(self):
        def bad_callback(ctx, result):
            raise RuntimeError("callback error")

        ctx = RetryContext(
            operation_name="test", max_attempts=3, on_success=bad_callback
        )
        ctx.trigger_success_callback("result")

    def test_trigger_failure_callback(self):
        called = []
        ctx = RetryContext(
            operation_name="test",
            max_attempts=3,
            on_failure=lambda ctx, exc: called.append(type(exc).__name__),
        )
        ctx.trigger_failure_callback(ValueError("final error"))
        assert called == ["ValueError"]

    def test_failure_callback_none_no_error(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.trigger_failure_callback(ValueError("err"))

    def test_failure_callback_exception_swallowed(self):
        def bad_callback(ctx, exc):
            raise RuntimeError("callback error")

        ctx = RetryContext(
            operation_name="test", max_attempts=3, on_failure=bad_callback
        )
        ctx.trigger_failure_callback(ValueError("err"))


# ── RetryContext.get_summary ───────────────────────────────────────────


class TestGetSummary:
    def test_empty_summary(self):
        ctx = RetryContext(operation_name="test_op", max_attempts=5)
        summary = ctx.get_summary()
        assert summary["operation"] == "test_op"
        assert summary["total_attempts"] == 0
        assert summary["max_attempts"] == 5
        assert summary["successful"] is False
        assert summary["last_exception"] is None
        assert summary["attempts"] == []

    def test_summary_with_attempts(self):
        ctx = RetryContext(operation_name="test_op", max_attempts=3)
        ctx.record_attempt(exception=ValueError("e1"), delay_before=1.0, duration=0.5)
        ctx.record_attempt(success=True, delay_before=2.0, duration=0.3)
        summary = ctx.get_summary()
        assert summary["total_attempts"] == 2
        assert summary["successful"] is True
        assert summary["total_delay_seconds"] == 3.0
        assert len(summary["attempts"]) == 2

    def test_summary_attempt_details(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt(exception=ValueError("e"), delay_before=1.0, duration=0.2)
        attempt_detail = ctx.get_summary()["attempts"][0]
        assert attempt_detail["attempt"] == 1
        assert attempt_detail["delay_before"] == 1.0
        assert attempt_detail["success"] is False
        assert attempt_detail["exception"] == "ValueError"
        assert attempt_detail["duration"] == 0.2

    def test_summary_last_exception_type(self):
        ctx = RetryContext(operation_name="test", max_attempts=3)
        ctx.record_attempt(exception=RuntimeError("fail"))
        summary = ctx.get_summary()
        assert summary["last_exception"] == "RuntimeError"


# ── RetryContext.__repr__ ──────────────────────────────────────────────


class TestRepr:
    def test_repr_format(self):
        ctx = RetryContext(operation_name="test_op", max_attempts=5)
        r = repr(ctx)
        assert "test_op" in r
        assert "0/5" in r
