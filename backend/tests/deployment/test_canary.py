"""Tests for canary release system (pure logic, no DB)."""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.deployment.canary import (
    CanaryConfig,
    CanaryMetrics,
    CanaryOutcome,
    CanaryRelease,
    CanaryReleaseManager,
    CanaryState,
    MetricComparison,
    RollbackReason,
    TrafficSplit,
    UserSegment,
)


# -- Enums -------------------------------------------------------------------


class TestCanaryState:
    def test_all_states(self):
        states = [s.value for s in CanaryState]
        assert "preparing" in states
        assert "ramping" in states
        assert "monitoring" in states
        assert "rolling_back" in states
        assert "rolled_back" in states
        assert "complete" in states
        assert "paused" in states

    def test_state_values(self):
        assert CanaryState.PREPARING == "preparing"
        assert CanaryState.COMPLETE == "complete"


class TestCanaryOutcome:
    def test_all_outcomes(self):
        outcomes = [o.value for o in CanaryOutcome]
        assert "success" in outcomes
        assert "automatic_rollback" in outcomes
        assert "manual_rollback" in outcomes
        assert "in_progress" in outcomes


class TestRollbackReason:
    def test_all_reasons(self):
        reasons = [r.value for r in RollbackReason]
        assert "error_rate_spike" in reasons
        assert "latency_degradation" in reasons
        assert "manual" in reasons
        assert "timeout" in reasons


# -- UserSegment -------------------------------------------------------------


class TestUserSegment:
    def test_defaults(self):
        seg = UserSegment()
        assert seg.name == ""
        assert seg.is_active is True
        assert seg.percentage == 0.0

    def test_inactive_never_matches(self):
        seg = UserSegment(is_active=False, user_ids=[uuid4()])
        uid = seg.user_ids[0]
        assert seg.matches(uid) is False

    def test_matches_user_id(self):
        uid = uuid4()
        seg = UserSegment(user_ids=[uid])
        assert seg.matches(uid) is True

    def test_no_match_user_id(self):
        seg = UserSegment(user_ids=[uuid4()])
        assert seg.matches(uuid4()) is False

    def test_matches_role(self):
        seg = UserSegment(user_roles=["admin"])
        assert seg.matches(uuid4(), user_role="admin") is True

    def test_no_match_role(self):
        seg = UserSegment(user_roles=["admin"])
        assert seg.matches(uuid4(), user_role="resident") is False

    def test_matches_organization(self):
        org_id = uuid4()
        seg = UserSegment(organizations=[org_id])
        assert seg.matches(uuid4(), organization_id=org_id) is True

    def test_no_match_organization(self):
        seg = UserSegment(organizations=[uuid4()])
        assert seg.matches(uuid4(), organization_id=uuid4()) is False

    def test_percentage_match(self):
        seg = UserSegment(percentage=1.0)  # 100%
        # user_hash % 100 < 100 always true
        assert seg.matches(uuid4(), user_hash=50) is True

    def test_percentage_no_match(self):
        seg = UserSegment(percentage=0.01)  # 1%
        assert seg.matches(uuid4(), user_hash=99) is False

    def test_percentage_needs_hash(self):
        seg = UserSegment(percentage=0.5)
        # No user_hash → no percentage match
        assert seg.matches(uuid4()) is False

    def test_no_criteria_no_match(self):
        seg = UserSegment()
        assert seg.matches(uuid4()) is False


# -- TrafficSplit ------------------------------------------------------------


class TestTrafficSplit:
    def test_default_values(self):
        ts = TrafficSplit()
        assert ts.canary_percentage == 0.0
        assert ts.baseline_percentage == 100.0

    def test_custom_split(self):
        ts = TrafficSplit(canary_percentage=10.0, baseline_percentage=90.0)
        assert ts.canary_percentage == 10.0
        assert ts.baseline_percentage == 90.0

    def test_invalid_sum_raises(self):
        with pytest.raises(ValueError, match="sum to 100"):
            TrafficSplit(canary_percentage=60.0, baseline_percentage=60.0)

    def test_can_ramp_up_true(self):
        ts = TrafficSplit(canary_percentage=10.0, baseline_percentage=90.0)
        assert ts.can_ramp_up() is True

    def test_can_ramp_up_at_target(self):
        ts = TrafficSplit(
            canary_percentage=100.0,
            baseline_percentage=0.0,
            target_percentage=100.0,
        )
        assert ts.can_ramp_up() is False

    def test_can_ramp_up_at_max(self):
        ts = TrafficSplit(
            canary_percentage=50.0,
            baseline_percentage=50.0,
            max_ramp_percentage=50.0,
        )
        assert ts.can_ramp_up() is False

    def test_ramp_up(self):
        ts = TrafficSplit(
            canary_percentage=10.0,
            baseline_percentage=90.0,
            ramp_increment=10.0,
        )
        new_ts = ts.ramp_up()
        assert new_ts.canary_percentage == 20.0
        assert new_ts.baseline_percentage == 80.0

    def test_ramp_up_respects_max(self):
        ts = TrafficSplit(
            canary_percentage=45.0,
            baseline_percentage=55.0,
            ramp_increment=10.0,
            max_ramp_percentage=50.0,
        )
        new_ts = ts.ramp_up()
        assert new_ts.canary_percentage == 50.0

    def test_ramp_up_respects_target(self):
        ts = TrafficSplit(
            canary_percentage=95.0,
            baseline_percentage=5.0,
            ramp_increment=10.0,
            target_percentage=100.0,
            max_ramp_percentage=100.0,
        )
        new_ts = ts.ramp_up()
        assert new_ts.canary_percentage == 100.0


# -- CanaryMetrics -----------------------------------------------------------


class TestCanaryMetrics:
    def test_defaults(self):
        m = CanaryMetrics()
        assert m.canary_request_count == 0
        assert m.canary_error_rate == 0.0
        assert m.canary_availability == 100.0

    def test_calculate_error_rates(self):
        m = CanaryMetrics(
            canary_request_count=100,
            canary_error_count=5,
            baseline_request_count=200,
            baseline_error_count=4,
        )
        m.calculate_error_rates()
        assert m.canary_error_rate == pytest.approx(5.0)
        assert m.baseline_error_rate == pytest.approx(2.0)

    def test_calculate_error_rates_zero_requests(self):
        m = CanaryMetrics(canary_request_count=0, baseline_request_count=0)
        m.calculate_error_rates()
        assert m.canary_error_rate == 0.0
        assert m.baseline_error_rate == 0.0


# -- MetricComparison -------------------------------------------------------


class TestMetricComparison:
    def test_acceptable(self):
        mc = MetricComparison(
            metric_name="error_rate",
            canary_value=2.0,
            baseline_value=2.0,
            threshold=5.0,
        )
        assert mc.is_acceptable is True
        assert mc.difference == 0.0

    def test_unacceptable(self):
        mc = MetricComparison(
            metric_name="error_rate",
            canary_value=10.0,
            baseline_value=2.0,
            threshold=5.0,
        )
        assert mc.is_acceptable is False

    def test_difference_calculated(self):
        mc = MetricComparison(
            metric_name="latency",
            canary_value=150.0,
            baseline_value=100.0,
            threshold=100.0,
        )
        assert mc.difference == 50.0
        assert mc.difference_percentage == pytest.approx(50.0)

    def test_baseline_zero(self):
        mc = MetricComparison(
            metric_name="errors",
            canary_value=5.0,
            baseline_value=0.0,
            threshold=10.0,
        )
        assert mc.difference_percentage == float("inf")
        assert mc.is_acceptable is False

    def test_both_zero(self):
        mc = MetricComparison(
            metric_name="errors",
            canary_value=0.0,
            baseline_value=0.0,
            threshold=10.0,
        )
        assert mc.difference_percentage == 0.0
        assert mc.is_acceptable is True


# -- CanaryConfig ------------------------------------------------------------


class TestCanaryConfig:
    def test_defaults(self):
        cfg = CanaryConfig()
        assert cfg.initial_traffic_percentage == 5.0
        assert cfg.target_traffic_percentage == 100.0
        assert cfg.auto_rollback_enabled is True

    def test_custom(self):
        cfg = CanaryConfig(
            release_name="api-v2",
            canary_version="v2.0",
            baseline_version="v1.0",
            max_error_rate_increase=1.0,
        )
        assert cfg.release_name == "api-v2"
        assert cfg.max_error_rate_increase == 1.0


# -- CanaryRelease -----------------------------------------------------------


class TestCanaryRelease:
    def test_defaults(self):
        r = CanaryRelease()
        assert r.state == CanaryState.PREPARING
        assert r.outcome == CanaryOutcome.IN_PROGRESS
        assert isinstance(r.id, UUID)

    def test_log_event(self):
        r = CanaryRelease()
        r.log_event("test", "Test event", {"key": "value"})
        assert len(r.events) == 1
        assert r.events[0]["type"] == "test"
        assert r.events[0]["message"] == "Test event"
        assert r.events[0]["metadata"] == {"key": "value"}

    def test_is_expired_not_started(self):
        r = CanaryRelease()
        assert r.is_expired() is False

    def test_is_expired_within_time(self):
        r = CanaryRelease()
        r.started_at = datetime.utcnow()
        assert r.is_expired() is False

    def test_is_expired_past_time(self):
        r = CanaryRelease()
        r.config.maximum_release_duration_hours = 1
        r.started_at = datetime.utcnow() - timedelta(hours=2)
        assert r.is_expired() is True

    def test_can_ramp_up_wrong_state(self):
        r = CanaryRelease()
        r.state = CanaryState.MONITORING
        assert r.can_ramp_up() is False

    def test_can_ramp_up_correct_state(self):
        r = CanaryRelease()
        r.state = CanaryState.RAMPING
        r.current_traffic = TrafficSplit(
            canary_percentage=10.0, baseline_percentage=90.0
        )
        assert r.can_ramp_up() is True


# -- CanaryReleaseManager ----------------------------------------------------


def _make_manager_with_release():
    """Create a manager with a started release."""
    manager = CanaryReleaseManager()
    config = CanaryConfig(
        release_name="test-release",
        canary_version="v2.0",
        baseline_version="v1.0",
        initial_traffic_percentage=5.0,
        ramp_increment=10.0,
    )
    release = manager.create_release(config)
    manager.start_release(release.id)
    return manager, release


class TestManagerInit:
    def test_empty(self):
        m = CanaryReleaseManager()
        assert m.releases == {}
        assert m.get_active_releases() == []


class TestManagerCreateRelease:
    def test_creates(self):
        m = CanaryReleaseManager()
        cfg = CanaryConfig(release_name="test")
        r = m.create_release(cfg)
        assert r.state == CanaryState.PREPARING
        assert r.id in m.releases

    def test_traffic_from_config(self):
        m = CanaryReleaseManager()
        cfg = CanaryConfig(initial_traffic_percentage=10.0)
        r = m.create_release(cfg)
        assert r.current_traffic.canary_percentage == 10.0
        assert r.current_traffic.baseline_percentage == 90.0

    def test_logs_event(self):
        m = CanaryReleaseManager()
        r = m.create_release(CanaryConfig(release_name="logged"))
        assert len(r.events) >= 1
        assert r.events[0]["type"] == "created"


class TestManagerStartRelease:
    def test_start(self):
        m = CanaryReleaseManager()
        r = m.create_release(CanaryConfig())
        result = m.start_release(r.id)
        assert result is True
        assert r.state == CanaryState.RAMPING
        assert r.started_at is not None

    def test_start_nonexistent(self):
        m = CanaryReleaseManager()
        assert m.start_release(uuid4()) is False

    def test_start_already_started(self):
        m = CanaryReleaseManager()
        r = m.create_release(CanaryConfig())
        m.start_release(r.id)
        assert m.start_release(r.id) is False


class TestManagerRecordRequest:
    def test_record_canary(self):
        manager, release = _make_manager_with_release()
        manager.record_request(release.id, is_canary=True, latency_ms=50.0)
        assert release.current_metrics.canary_request_count == 1

    def test_record_baseline(self):
        manager, release = _make_manager_with_release()
        manager.record_request(release.id, is_canary=False)
        assert release.current_metrics.baseline_request_count == 1

    def test_record_error(self):
        manager, release = _make_manager_with_release()
        manager.record_request(release.id, is_canary=True, error=True)
        assert release.current_metrics.canary_error_count == 1

    def test_record_exception(self):
        manager, release = _make_manager_with_release()
        manager.record_request(release.id, is_canary=True, exception=True)
        assert release.current_metrics.canary_exception_count == 1

    def test_record_nonexistent(self):
        m = CanaryReleaseManager()
        m.record_request(uuid4(), is_canary=True)  # Should not raise

    def test_error_rates_updated(self):
        manager, release = _make_manager_with_release()
        for _ in range(10):
            manager.record_request(release.id, is_canary=True)
        manager.record_request(release.id, is_canary=True, error=True)
        assert release.current_metrics.canary_error_rate > 0


class TestManagerCollectMetrics:
    def test_collects(self):
        manager, release = _make_manager_with_release()
        manager.record_request(release.id, is_canary=True)
        snapshot = manager.collect_metrics(release.id)
        assert snapshot.canary_request_count == 1
        assert len(release.metrics_history) == 1

    def test_nonexistent_raises(self):
        m = CanaryReleaseManager()
        with pytest.raises(ValueError, match="not found"):
            m.collect_metrics(uuid4())


class TestManagerCompareMetrics:
    def test_comparisons(self):
        manager, release = _make_manager_with_release()
        for _ in range(20):
            manager.record_request(release.id, is_canary=True, latency_ms=50)
            manager.record_request(release.id, is_canary=False, latency_ms=45)
        comps = manager.compare_metrics(release.id)
        assert len(comps) >= 2  # error_rate + latency + availability
        names = [c.metric_name for c in comps]
        assert "error_rate" in names

    def test_nonexistent_raises(self):
        m = CanaryReleaseManager()
        with pytest.raises(ValueError, match="not found"):
            m.compare_metrics(uuid4())


class TestManagerCheckRollback:
    def test_no_rollback_healthy(self):
        manager, release = _make_manager_with_release()
        for _ in range(20):
            manager.record_request(release.id, is_canary=True)
            manager.record_request(release.id, is_canary=False)
        should_rb, reason = manager.check_rollback_conditions(release.id)
        assert should_rb is False
        assert reason is None

    def test_rollback_error_spike(self):
        manager, release = _make_manager_with_release()
        for _ in range(10):
            manager.record_request(release.id, is_canary=True, error=True)
        for _ in range(20):
            manager.record_request(release.id, is_canary=False)
        should_rb, reason = manager.check_rollback_conditions(release.id)
        assert should_rb is True
        assert reason == RollbackReason.ERROR_RATE_SPIKE

    def test_rollback_exception_rate(self):
        manager, release = _make_manager_with_release()
        for _ in range(10):
            manager.record_request(release.id, is_canary=True, exception=True)
        should_rb, reason = manager.check_rollback_conditions(release.id)
        assert should_rb is True
        assert reason == RollbackReason.EXCEPTION_RATE

    def test_no_rollback_insufficient_data(self):
        manager, release = _make_manager_with_release()
        manager.record_request(release.id, is_canary=True, error=True)
        should_rb, _ = manager.check_rollback_conditions(release.id)
        assert should_rb is False

    def test_no_rollback_disabled(self):
        m = CanaryReleaseManager()
        cfg = CanaryConfig(auto_rollback_enabled=False)
        r = m.create_release(cfg)
        m.start_release(r.id)
        for _ in range(20):
            m.record_request(r.id, is_canary=True, error=True)
        should_rb, _ = m.check_rollback_conditions(r.id)
        assert should_rb is False

    def test_nonexistent_no_rollback(self):
        m = CanaryReleaseManager()
        should_rb, reason = m.check_rollback_conditions(uuid4())
        assert should_rb is False


class TestManagerRollback:
    def test_rollback(self):
        manager, release = _make_manager_with_release()
        result = manager.rollback(
            release.id, RollbackReason.ERROR_RATE_SPIKE, "Too many errors"
        )
        assert result is True
        assert release.state == CanaryState.ROLLED_BACK
        assert release.outcome == CanaryOutcome.AUTOMATIC_ROLLBACK
        assert release.current_traffic.canary_percentage == 0.0
        assert release.completed_at is not None

    def test_manual_rollback(self):
        manager, release = _make_manager_with_release()
        manager.rollback(release.id, RollbackReason.MANUAL, "Manual stop")
        assert release.outcome == CanaryOutcome.MANUAL_ROLLBACK

    def test_rollback_nonexistent(self):
        m = CanaryReleaseManager()
        assert m.rollback(uuid4(), RollbackReason.MANUAL) is False


class TestManagerRampUp:
    def test_ramp_up(self):
        manager, release = _make_manager_with_release()
        # Ensure can_ramp_up passes by clearing last_ramp_at timing
        release.last_ramp_at = None
        result = manager.ramp_up(release.id)
        assert result is True
        assert release.current_traffic.canary_percentage > 5.0

    def test_ramp_up_nonexistent(self):
        m = CanaryReleaseManager()
        assert m.ramp_up(uuid4()) is False


class TestManagerCompleteRelease:
    def test_complete(self):
        manager, release = _make_manager_with_release()
        result = manager.complete_release(release.id)
        assert result is True
        assert release.state == CanaryState.COMPLETE
        assert release.outcome == CanaryOutcome.SUCCESS
        assert release.completed_at is not None

    def test_complete_nonexistent(self):
        m = CanaryReleaseManager()
        assert m.complete_release(uuid4()) is False


class TestManagerPauseResume:
    def test_pause(self):
        manager, release = _make_manager_with_release()
        result = manager.pause_release(release.id, "Investigating")
        assert result is True
        assert release.state == CanaryState.PAUSED

    def test_resume(self):
        manager, release = _make_manager_with_release()
        manager.pause_release(release.id)
        result = manager.resume_release(release.id)
        assert result is True
        assert release.state == CanaryState.RAMPING

    def test_resume_not_paused(self):
        manager, release = _make_manager_with_release()
        assert manager.resume_release(release.id) is False

    def test_pause_nonexistent(self):
        m = CanaryReleaseManager()
        assert m.pause_release(uuid4()) is False


class TestManagerGetStatus:
    def test_status(self):
        manager, release = _make_manager_with_release()
        status = manager.get_release_status(release.id)
        assert status["state"] == "ramping"
        assert "traffic" in status
        assert "metrics" in status
        assert "timing" in status
        assert "health" in status

    def test_status_nonexistent(self):
        m = CanaryReleaseManager()
        status = m.get_release_status(uuid4())
        assert "error" in status


class TestManagerActiveReleases:
    def test_active(self):
        manager, release = _make_manager_with_release()
        active = manager.get_active_releases()
        assert len(active) == 1

    def test_completed_not_active(self):
        manager, release = _make_manager_with_release()
        manager.complete_release(release.id)
        assert manager.get_active_releases() == []


class TestManagerEventHandlers:
    def test_register_and_emit(self):
        events_received = []
        m = CanaryReleaseManager()
        m.register_event_handler("release_created", lambda r: events_received.append(r))
        m.create_release(CanaryConfig())
        assert len(events_received) == 1

    def test_handler_error_suppressed(self):
        m = CanaryReleaseManager()
        m.register_event_handler(
            "release_created", lambda r: (_ for _ in ()).throw(RuntimeError("fail"))
        )
        # Should not raise
        m.create_release(CanaryConfig())


class TestManagerMetricCollectors:
    def test_register_collector(self):
        calls = []
        m = CanaryReleaseManager()
        m.register_metric_collector(lambda r: calls.append(r))
        r = m.create_release(CanaryConfig())
        m.start_release(r.id)
        m.collect_metrics(r.id)
        assert len(calls) == 1


class TestManagerRouteRequest:
    def test_baseline_for_nonexistent(self):
        m = CanaryReleaseManager()
        assert m.route_request(uuid4(), uuid4()) == "baseline"

    def test_baseline_for_completed(self):
        manager, release = _make_manager_with_release()
        manager.complete_release(release.id)
        assert manager.route_request(release.id, uuid4()) == "baseline"

    def test_canary_by_segment(self):
        uid = uuid4()
        seg = UserSegment(user_ids=[uid])
        m = CanaryReleaseManager()
        cfg = CanaryConfig(target_segments=[seg])
        r = m.create_release(cfg)
        m.start_release(r.id)
        assert m.route_request(r.id, uid) == "canary"


class TestManagerCleanup:
    def test_cleanup_old(self):
        manager, release = _make_manager_with_release()
        manager.complete_release(release.id)
        release.completed_at = datetime.utcnow() - timedelta(days=10)
        removed = manager.cleanup_old_releases(days=7)
        assert removed == 1
        assert release.id not in manager.releases

    def test_cleanup_keeps_recent(self):
        manager, release = _make_manager_with_release()
        manager.complete_release(release.id)
        removed = manager.cleanup_old_releases(days=7)
        assert removed == 0
