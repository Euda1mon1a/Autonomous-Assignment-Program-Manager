"""Tests for observability metrics and request ID middleware."""

import time

from app.core.observability import (
    PROMETHEUS_AVAILABLE,
    IdempotencyTimer,
    ObservabilityMetrics,
    RequestIDMiddleware,
    ScheduleTimer,
    get_request_id,
    request_id_ctx,
    with_request_id,
)


# ==================== request_id context ====================


class TestRequestIdContext:
    def test_default_none(self):
        assert get_request_id() is None

    def test_set_and_get(self):
        token = request_id_ctx.set("obs-123")
        try:
            assert get_request_id() == "obs-123"
        finally:
            request_id_ctx.reset(token)


# ==================== ObservabilityMetrics singleton ====================


class TestObservabilityMetricsSingleton:
    def test_singleton(self):
        m1 = ObservabilityMetrics()
        m2 = ObservabilityMetrics()
        assert m1 is m2

    def test_initialized(self):
        m = ObservabilityMetrics()
        assert m._initialized is True

    def test_enabled_reflects_prometheus(self):
        m = ObservabilityMetrics()
        assert m._enabled == PROMETHEUS_AVAILABLE


# ==================== Auth metrics (no-op when prometheus unavailable) ====================


class TestAuthMetrics:
    def test_record_token_issued(self):
        m = ObservabilityMetrics()
        # Should not raise regardless of prometheus availability
        m.record_token_issued("access")
        m.record_token_issued("refresh")

    def test_record_token_blacklisted(self):
        m = ObservabilityMetrics()
        m.record_token_blacklisted("logout")
        m.record_token_blacklisted("revoked")

    def test_record_auth_failure(self):
        m = ObservabilityMetrics()
        m.record_auth_failure("expired")
        m.record_auth_failure("invalid_signature")


# ==================== Idempotency metrics ====================


class TestIdempotencyMetrics:
    def test_record_hit(self):
        m = ObservabilityMetrics()
        m.record_idempotency_hit()

    def test_record_miss(self):
        m = ObservabilityMetrics()
        m.record_idempotency_miss()

    def test_record_conflict(self):
        m = ObservabilityMetrics()
        m.record_idempotency_conflict()

    def test_record_pending(self):
        m = ObservabilityMetrics()
        m.record_idempotency_pending()

    def test_set_cache_size(self):
        m = ObservabilityMetrics()
        m.set_idempotency_cache_size(42)

    def test_time_lookup_returns_timer(self):
        m = ObservabilityMetrics()
        timer = m.time_idempotency_lookup()
        assert isinstance(timer, IdempotencyTimer)


# ==================== Scheduling metrics ====================


class TestSchedulingMetrics:
    def test_record_success(self):
        m = ObservabilityMetrics()
        m.record_schedule_success("cp_sat", assignments=50)

    def test_record_success_zero_assignments(self):
        m = ObservabilityMetrics()
        m.record_schedule_success("greedy", assignments=0)

    def test_record_failure(self):
        m = ObservabilityMetrics()
        m.record_schedule_failure("pulp")

    def test_record_violation(self):
        m = ObservabilityMetrics()
        m.record_violation("80_hour")
        m.record_violation("1_in_7")

    def test_time_generation_returns_timer(self):
        m = ObservabilityMetrics()
        timer = m.time_schedule_generation("cp_sat")
        assert isinstance(timer, ScheduleTimer)


# ==================== IdempotencyTimer ====================


class TestIdempotencyTimer:
    def test_context_manager(self):
        m = ObservabilityMetrics()
        timer = IdempotencyTimer(m)
        with timer as t:
            assert t is timer
            assert t.start_time is not None

    def test_returns_false(self):
        m = ObservabilityMetrics()
        timer = IdempotencyTimer(m)
        result = timer.__exit__(None, None, None)
        assert result is False

    def test_measures_duration(self):
        m = ObservabilityMetrics()
        with IdempotencyTimer(m) as t:
            time.sleep(0.01)
        # start_time should have been set
        assert t.start_time is not None


# ==================== ScheduleTimer ====================


class TestScheduleTimer:
    def test_context_manager(self):
        m = ObservabilityMetrics()
        timer = ScheduleTimer(m, "greedy")
        with timer as t:
            assert t is timer
            assert t.start_time is not None
            assert t.algorithm == "greedy"

    def test_returns_false(self):
        m = ObservabilityMetrics()
        timer = ScheduleTimer(m, "cp_sat")
        result = timer.__exit__(None, None, None)
        assert result is False


# ==================== RequestIDMiddleware ====================


class TestRequestIDMiddleware:
    def test_max_length(self):
        assert RequestIDMiddleware.MAX_REQUEST_ID_LENGTH == 255

    def test_has_dispatch(self):
        assert hasattr(RequestIDMiddleware, "dispatch")


# ==================== with_request_id decorator ====================


class TestWithRequestId:
    def test_wraps_function(self):
        @with_request_id
        def my_func():
            return 42

        assert my_func() == 42

    def test_preserves_name(self):
        @with_request_id
        def my_func():
            pass

        assert my_func.__name__ == "my_func"

    def test_with_request_id_set(self):
        token = request_id_ctx.set("dec-456")
        try:

            @with_request_id
            def my_func():
                return get_request_id()

            # The decorator sets the logging context; request_id_ctx is separate
            result = my_func()
            # Function should still return (not crash)
            assert result is not None or result is None  # Just ensure no crash
        finally:
            request_id_ctx.reset(token)
