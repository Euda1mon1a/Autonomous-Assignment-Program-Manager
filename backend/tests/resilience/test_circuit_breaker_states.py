"""Tests for circuit breaker state machine (pure logic, no DB)."""

from datetime import datetime, timedelta

import pytest

from app.resilience.circuit_breaker.states import (
    CircuitMetrics,
    CircuitState,
    StateMachine,
    StateTransition,
)


# -- CircuitState enum -------------------------------------------------------


class TestCircuitState:
    def test_values(self):
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_member_count(self):
        assert len(CircuitState) == 3


# -- StateTransition dataclass -----------------------------------------------


class TestStateTransition:
    def test_creation(self):
        t = StateTransition(
            from_state=CircuitState.CLOSED,
            to_state=CircuitState.OPEN,
            timestamp=datetime(2026, 1, 1),
            reason="test",
            failure_count=5,
        )
        assert t.from_state == CircuitState.CLOSED
        assert t.to_state == CircuitState.OPEN
        assert t.reason == "test"
        assert t.failure_count == 5
        assert t.success_count == 0


# -- CircuitMetrics dataclass ------------------------------------------------


class TestCircuitMetrics:
    def test_default_values(self):
        m = CircuitMetrics()
        assert m.total_requests == 0
        assert m.successful_requests == 0
        assert m.failed_requests == 0
        assert m.rejected_requests == 0
        assert m.consecutive_failures == 0
        assert m.consecutive_successes == 0
        assert m.last_failure_time is None
        assert m.last_success_time is None
        assert m.state_transitions == []

    def test_failure_rate_zero_requests(self):
        m = CircuitMetrics()
        assert m.failure_rate == 0.0

    def test_failure_rate_calculated(self):
        m = CircuitMetrics(total_requests=10, failed_requests=3)
        assert m.failure_rate == pytest.approx(0.3)

    def test_success_rate_zero_requests(self):
        m = CircuitMetrics()
        assert m.success_rate == 0.0

    def test_success_rate_calculated(self):
        m = CircuitMetrics(total_requests=10, successful_requests=7)
        assert m.success_rate == pytest.approx(0.7)

    def test_reset_consecutive_counters(self):
        m = CircuitMetrics(consecutive_failures=5, consecutive_successes=3)
        m.reset_consecutive_counters()
        assert m.consecutive_failures == 0
        assert m.consecutive_successes == 0


# -- StateMachine init -------------------------------------------------------


class TestStateMachineInit:
    def test_default_init(self):
        sm = StateMachine()
        assert sm.current_state == CircuitState.CLOSED
        assert sm.failure_threshold == 5
        assert sm.success_threshold == 2
        assert sm.half_open_max_calls == 3
        assert sm.opened_at is None

    def test_custom_init(self):
        sm = StateMachine(
            failure_threshold=3,
            success_threshold=1,
            timeout_seconds=30.0,
            half_open_max_calls=5,
        )
        assert sm.failure_threshold == 3
        assert sm.success_threshold == 1
        assert sm.half_open_max_calls == 5


# -- record_success ----------------------------------------------------------


class TestRecordSuccess:
    def test_increments_counters(self):
        sm = StateMachine()
        sm.record_success()
        assert sm.metrics.total_requests == 1
        assert sm.metrics.successful_requests == 1
        assert sm.metrics.consecutive_successes == 1
        assert sm.metrics.consecutive_failures == 0

    def test_resets_consecutive_failures(self):
        sm = StateMachine()
        sm.metrics.consecutive_failures = 3
        sm.record_success()
        assert sm.metrics.consecutive_failures == 0

    def test_stays_closed_in_closed_state(self):
        sm = StateMachine()
        state = sm.record_success()
        assert state == CircuitState.CLOSED

    def test_sets_last_success_time(self):
        sm = StateMachine()
        sm.record_success()
        assert sm.metrics.last_success_time is not None


# -- record_failure ----------------------------------------------------------


class TestRecordFailure:
    def test_increments_counters(self):
        sm = StateMachine()
        sm.record_failure()
        assert sm.metrics.total_requests == 1
        assert sm.metrics.failed_requests == 1
        assert sm.metrics.consecutive_failures == 1
        assert sm.metrics.consecutive_successes == 0

    def test_resets_consecutive_successes(self):
        sm = StateMachine()
        sm.metrics.consecutive_successes = 3
        sm.record_failure()
        assert sm.metrics.consecutive_successes == 0

    def test_stays_closed_below_threshold(self):
        sm = StateMachine(failure_threshold=5)
        for _ in range(4):
            state = sm.record_failure()
        assert state == CircuitState.CLOSED

    def test_opens_at_threshold(self):
        sm = StateMachine(failure_threshold=3)
        for _ in range(3):
            state = sm.record_failure()
        assert state == CircuitState.OPEN
        assert sm.opened_at is not None

    def test_sets_last_failure_time(self):
        sm = StateMachine()
        sm.record_failure()
        assert sm.metrics.last_failure_time is not None


# -- State transitions -------------------------------------------------------


class TestStateTransitions:
    def test_closed_to_open(self):
        sm = StateMachine(failure_threshold=2)
        sm.record_failure()
        sm.record_failure()
        assert sm.current_state == CircuitState.OPEN
        assert len(sm.metrics.state_transitions) == 1
        assert sm.metrics.state_transitions[0].from_state == CircuitState.CLOSED
        assert sm.metrics.state_transitions[0].to_state == CircuitState.OPEN

    def test_half_open_to_open_on_failure(self):
        sm = StateMachine(failure_threshold=2)
        sm.record_failure()
        sm.record_failure()
        # Manually set to half-open for testing
        sm.current_state = CircuitState.HALF_OPEN
        sm.metrics.reset_consecutive_counters()
        state = sm.record_failure()
        assert state == CircuitState.OPEN

    def test_half_open_to_closed_on_success(self):
        sm = StateMachine(failure_threshold=2, success_threshold=2)
        sm.record_failure()
        sm.record_failure()
        # Manually set to half-open for testing
        sm.current_state = CircuitState.HALF_OPEN
        sm.metrics.reset_consecutive_counters()
        sm.record_success()
        assert sm.current_state == CircuitState.HALF_OPEN  # Not yet
        sm.record_success()
        assert sm.current_state == CircuitState.CLOSED  # Now closed

    def test_transition_records_reason(self):
        sm = StateMachine(failure_threshold=1)
        sm.record_failure()
        assert "threshold" in sm.metrics.state_transitions[0].reason.lower()


# -- should_allow_request ----------------------------------------------------


class TestShouldAllowRequest:
    def test_closed_always_allows(self):
        sm = StateMachine()
        assert sm.should_allow_request() is True

    def test_open_rejects(self):
        sm = StateMachine(failure_threshold=1)
        sm.record_failure()
        assert sm.current_state == CircuitState.OPEN
        assert sm.should_allow_request() is False

    def test_open_allows_after_timeout(self):
        sm = StateMachine(failure_threshold=1, timeout_seconds=1.0)
        sm.record_failure()
        # Set opened_at to the past
        sm.opened_at = datetime.utcnow() - timedelta(seconds=10)
        assert sm.should_allow_request() is True
        assert sm.current_state == CircuitState.HALF_OPEN

    def test_half_open_allows_limited_calls(self):
        sm = StateMachine(half_open_max_calls=2)
        sm.current_state = CircuitState.HALF_OPEN
        sm.half_open_calls_in_flight = 0
        assert sm.should_allow_request() is True
        sm.half_open_calls_in_flight = 2
        assert sm.should_allow_request() is False


# -- record_rejection --------------------------------------------------------


class TestRecordRejection:
    def test_increments_rejected(self):
        sm = StateMachine()
        sm.record_rejection()
        assert sm.metrics.rejected_requests == 1


# -- force_open / force_closed -----------------------------------------------


class TestForceOverrides:
    def test_force_open(self):
        sm = StateMachine()
        assert sm.current_state == CircuitState.CLOSED
        sm.force_open("Manual test")
        assert sm.current_state == CircuitState.OPEN

    def test_force_open_when_already_open(self):
        sm = StateMachine(failure_threshold=1)
        sm.record_failure()
        transitions_before = len(sm.metrics.state_transitions)
        sm.force_open("Redundant")
        # Should not add another transition
        assert len(sm.metrics.state_transitions) == transitions_before

    def test_force_closed(self):
        sm = StateMachine(failure_threshold=1)
        sm.record_failure()
        assert sm.current_state == CircuitState.OPEN
        sm.force_closed("Manual recovery")
        assert sm.current_state == CircuitState.CLOSED

    def test_force_closed_when_already_closed(self):
        sm = StateMachine()
        transitions_before = len(sm.metrics.state_transitions)
        sm.force_closed("Redundant")
        assert len(sm.metrics.state_transitions) == transitions_before


# -- reset -------------------------------------------------------------------


class TestReset:
    def test_reset_to_initial(self):
        sm = StateMachine(failure_threshold=1)
        sm.record_failure()
        sm.record_failure()
        sm.reset()
        assert sm.current_state == CircuitState.CLOSED
        assert sm.metrics.total_requests == 0
        assert sm.metrics.failed_requests == 0
        assert sm.opened_at is None
        assert sm.half_open_calls_in_flight == 0


# -- get_status --------------------------------------------------------------


class TestGetStatus:
    def test_has_expected_keys(self):
        sm = StateMachine()
        status = sm.get_status()
        expected_keys = {
            "state",
            "failure_rate",
            "success_rate",
            "total_requests",
            "successful_requests",
            "failed_requests",
            "rejected_requests",
            "consecutive_failures",
            "consecutive_successes",
            "opened_at",
            "last_failure_time",
            "last_success_time",
            "recent_transitions",
        }
        assert set(status.keys()) == expected_keys

    def test_initial_status(self):
        sm = StateMachine()
        status = sm.get_status()
        assert status["state"] == "closed"
        assert status["total_requests"] == 0
        assert status["opened_at"] is None

    def test_after_failures(self):
        sm = StateMachine(failure_threshold=2)
        sm.record_failure()
        sm.record_failure()
        status = sm.get_status()
        assert status["state"] == "open"
        assert status["failed_requests"] == 2
        assert status["opened_at"] is not None
        assert len(status["recent_transitions"]) == 1
