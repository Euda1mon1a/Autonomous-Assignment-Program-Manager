"""
Tests for Quantum Zeno Effect Optimization Governor.

Tests the logic that prevents over-monitoring from freezing optimization.
"""

import uuid
from datetime import datetime, timedelta

import pytest

from app.scheduling.zeno_dashboard import (
    ZenoDashboard,
    format_policy_for_display,
    generate_zeno_report,
)
from app.scheduling.zeno_governor import (
    HumanIntervention,
    InterventionPolicy,
    OptimizationFreedomWindow,
    ZenoGovernor,
    ZenoMetrics,
    ZenoRisk,
)


class TestZenoRisk:
    """Tests for ZenoRisk enum."""

    def test_risk_levels_defined(self):
        """Test that all risk levels are defined."""
        assert ZenoRisk.LOW == "low"
        assert ZenoRisk.MODERATE == "moderate"
        assert ZenoRisk.HIGH == "high"
        assert ZenoRisk.CRITICAL == "critical"


class TestInterventionPolicy:
    """Tests for InterventionPolicy dataclass."""

    def test_default_initialization(self):
        """Test default policy values."""
        policy = InterventionPolicy()

        assert policy.max_checks_per_day == 3
        assert policy.min_interval_hours == 8
        assert len(policy.recommended_windows) == 3
        assert policy.auto_lock_threshold == 0.95

    def test_custom_initialization(self):
        """Test custom policy values."""
        policy = InterventionPolicy(
            max_checks_per_day=1,
            min_interval_hours=24,
            recommended_windows=["09:00-10:00"],
            auto_lock_threshold=0.99,
            explanation="Critical risk policy",
        )

        assert policy.max_checks_per_day == 1
        assert policy.min_interval_hours == 24
        assert len(policy.recommended_windows) == 1
        assert policy.auto_lock_threshold == 0.99
        assert "Critical" in policy.explanation


class TestOptimizationFreedomWindow:
    """Tests for OptimizationFreedomWindow dataclass."""

    def test_default_initialization(self):
        """Test default window initialization."""
        window = OptimizationFreedomWindow()

        assert window.is_active is True
        assert window.interventions_blocked == 0
        assert window.solver_improvements == 0
        assert window.final_score_improvement == 0.0

    def test_window_duration(self):
        """Test window duration calculation."""
        start = datetime(2024, 1, 15, 8, 0)
        end = datetime(2024, 1, 15, 12, 0)

        window = OptimizationFreedomWindow(start_time=start, end_time=end)

        duration = (window.end_time - window.start_time).total_seconds() / 3600
        assert duration == 4.0


class TestZenoMetrics:
    """Tests for ZenoMetrics dataclass."""

    def test_default_initialization(self):
        """Test default metrics initialization."""
        metrics = ZenoMetrics()

        assert metrics.risk_level == ZenoRisk.LOW
        assert metrics.interventions_24h == 0
        assert metrics.frozen_ratio == 0.0
        assert metrics.evolution_prevented == 0

    def test_custom_metrics(self):
        """Test metrics with custom values."""
        policy = InterventionPolicy()
        metrics = ZenoMetrics(
            risk_level=ZenoRisk.HIGH,
            interventions_24h=10,
            frozen_ratio=0.4,
            evolution_prevented=5,
            recommended_policy=policy,
        )

        assert metrics.risk_level == ZenoRisk.HIGH
        assert metrics.interventions_24h == 10
        assert metrics.frozen_ratio == 0.4
        assert metrics.evolution_prevented == 5


class TestHumanIntervention:
    """Tests for HumanIntervention dataclass."""

    def test_intervention_creation(self):
        """Test creating intervention record."""
        assignment_ids = {uuid.uuid4(), uuid.uuid4()}

        intervention = HumanIntervention(
            user_id="test_user",
            assignments_reviewed=assignment_ids,
            assignments_locked={list(assignment_ids)[0]},
            intervention_type="lock",
            reason="Testing",
        )

        assert intervention.user_id == "test_user"
        assert len(intervention.assignments_reviewed) == 2
        assert len(intervention.assignments_locked) == 1
        assert intervention.intervention_type == "lock"
        assert intervention.reason == "Testing"


class TestZenoGovernor:
    """Tests for ZenoGovernor main class."""

    @pytest.fixture
    def governor(self):
        """Create a fresh governor instance."""
        return ZenoGovernor()

    @pytest.fixture
    def sample_assignments(self):
        """Create sample assignment IDs."""
        return {uuid.uuid4() for _ in range(10)}

    def test_initialization(self, governor):
        """Test governor initialization."""
        assert len(governor.interventions) == 0
        assert len(governor.frozen_assignments) == 0
        assert governor.total_assignments == 0

    @pytest.mark.asyncio
    async def test_log_intervention_low_risk(self, governor, sample_assignments):
        """Test logging intervention with low risk."""
        governor.total_assignments = 100

        risk = await governor.log_human_intervention(
            checkpoint_time=datetime.now(),
            assignments_reviewed=sample_assignments,
            user_id="test_user",
        )

        assert risk == ZenoRisk.LOW
        assert len(governor.interventions) == 1

    @pytest.mark.asyncio
    async def test_log_intervention_with_locks(self, governor, sample_assignments):
        """Test logging intervention that locks assignments."""
        governor.total_assignments = 100
        locked = {list(sample_assignments)[0], list(sample_assignments)[1]}

        risk = await governor.log_human_intervention(
            checkpoint_time=datetime.now(),
            assignments_reviewed=sample_assignments,
            assignments_locked=locked,
            user_id="test_user",
        )

        assert len(governor.frozen_assignments) == 2
        assert locked.issubset(governor.frozen_assignments)

    @pytest.mark.asyncio
    async def test_multiple_interventions_increase_risk(self, governor):
        """Test that multiple interventions increase risk."""
        governor.total_assignments = 100

        # Log many interventions in short time
        for i in range(15):
            timestamp = datetime.now() - timedelta(minutes=i * 30)
            assignments = {uuid.uuid4() for _ in range(5)}

            await governor.log_human_intervention(
                checkpoint_time=timestamp,
                assignments_reviewed=assignments,
                user_id=f"user_{i}",
            )

        risk = governor._assess_current_risk()
        assert risk in [ZenoRisk.HIGH, ZenoRisk.CRITICAL]

    def test_compute_measurement_frequency_empty(self, governor):
        """Test measurement frequency with no interventions."""
        freq = governor.compute_measurement_frequency()
        assert freq == 0.0

    def test_compute_measurement_frequency_single(self, governor):
        """Test measurement frequency with single intervention."""
        governor.interventions.append(
            HumanIntervention(
                timestamp=datetime.now(),
                user_id="test",
                assignments_reviewed={uuid.uuid4()},
            )
        )

        freq = governor.compute_measurement_frequency()
        assert freq > 0.0

    def test_compute_measurement_frequency_multiple(self, governor):
        """Test measurement frequency with multiple interventions."""
        # Add 6 interventions in past 12 hours
        for i in range(6):
            timestamp = datetime.now() - timedelta(hours=i * 2)
            governor.interventions.append(
                HumanIntervention(
                    timestamp=timestamp,
                    user_id="test",
                    assignments_reviewed={uuid.uuid4()},
                )
            )

        freq = governor.compute_measurement_frequency(timedelta(hours=12))
        expected = 6 / 12  # 0.5 interventions per hour
        assert abs(freq - expected) < 0.1

    def test_compute_frozen_ratio_zero(self, governor):
        """Test frozen ratio with no assignments."""
        ratio = governor.compute_frozen_assignments_ratio()
        assert ratio == 0.0

    def test_compute_frozen_ratio_none_frozen(self, governor):
        """Test frozen ratio with assignments but none frozen."""
        governor.total_assignments = 100
        ratio = governor.compute_frozen_assignments_ratio()
        assert ratio == 0.0

    def test_compute_frozen_ratio_half_frozen(self, governor):
        """Test frozen ratio with 50% frozen."""
        governor.total_assignments = 100
        governor.frozen_assignments = {uuid.uuid4() for _ in range(50)}

        ratio = governor.compute_frozen_assignments_ratio()
        assert ratio == 0.5

    def test_compute_local_optima_risk_low(self, governor):
        """Test local optima risk with healthy state."""
        governor.total_assignments = 100
        governor.frozen_assignments = {uuid.uuid4() for _ in range(5)}  # 5% frozen

        risk = governor.compute_local_optima_risk()
        assert risk < 0.3  # Low risk

    def test_compute_local_optima_risk_high(self, governor):
        """Test local optima risk with problematic state."""
        governor.total_assignments = 100
        governor.frozen_assignments = {uuid.uuid4() for _ in range(80)}  # 80% frozen

        # Add many interventions
        for i in range(20):
            timestamp = datetime.now() - timedelta(minutes=i * 10)
            governor.interventions.append(
                HumanIntervention(
                    timestamp=timestamp,
                    user_id="test",
                    assignments_reviewed={uuid.uuid4()},
                )
            )

        risk = governor.compute_local_optima_risk()
        assert risk > 0.6  # High risk

    def test_recommend_policy_low_risk(self, governor):
        """Test policy recommendation for low risk."""
        governor.total_assignments = 100

        policy = governor.recommend_intervention_policy()

        assert policy.max_checks_per_day == 6
        assert policy.min_interval_hours == 4
        assert len(policy.hands_off_periods) == 0

    def test_recommend_policy_critical_risk(self, governor):
        """Test policy recommendation for critical risk."""
        governor.total_assignments = 100
        governor.frozen_assignments = {uuid.uuid4() for _ in range(60)}  # 60% frozen

        policy = governor.recommend_intervention_policy()

        assert policy.max_checks_per_day == 1
        assert policy.min_interval_hours == 24
        assert len(policy.hands_off_periods) > 0
        assert policy.auto_lock_threshold >= 0.99

    def test_compute_evolution_prevented_zero(self, governor):
        """Test evolution prevention with no blocked attempts."""
        prevented = governor.compute_evolution_prevented()
        assert prevented == 0

    def test_compute_evolution_prevented_with_blocks(self, governor):
        """Test evolution prevention with blocked attempts."""
        frozen_id = uuid.uuid4()
        governor.frozen_assignments.add(frozen_id)

        # Log blocked solver attempts
        for _ in range(5):
            governor.log_solver_attempt(
                proposed_changes={frozen_id, uuid.uuid4()},
                successful=False,
                blocked=True,
                reason="Frozen assignment conflict",
            )

        prevented = governor.compute_evolution_prevented()
        assert prevented == 5

    @pytest.mark.asyncio
    async def test_create_freedom_window(self, governor):
        """Test creating optimization freedom window."""
        window = await governor.create_freedom_window(
            duration_hours=8, reason="Overnight optimization"
        )

        assert window.is_active is True
        assert window.reason == "Overnight optimization"
        assert len(governor.freedom_windows) == 1

        duration = (window.end_time - window.start_time).total_seconds() / 3600
        assert abs(duration - 8.0) < 0.1

    def test_is_in_freedom_window_false(self, governor):
        """Test freedom window check when no windows active."""
        assert governor.is_in_freedom_window() is False

    @pytest.mark.asyncio
    async def test_is_in_freedom_window_true(self, governor):
        """Test freedom window check when window is active."""
        # Create window that includes current time
        await governor.create_freedom_window(duration_hours=2)

        assert governor.is_in_freedom_window() is True

    def test_is_in_freedom_window_expired(self, governor):
        """Test freedom window check with expired window."""
        # Create window in the past
        past_window = OptimizationFreedomWindow(
            start_time=datetime.now() - timedelta(hours=4),
            end_time=datetime.now() - timedelta(hours=2),
            is_active=True,
        )
        governor.freedom_windows.append(past_window)

        assert governor.is_in_freedom_window() is False

    def test_get_current_metrics(self, governor):
        """Test getting current metrics."""
        governor.total_assignments = 100

        metrics = governor.get_current_metrics()

        assert isinstance(metrics, ZenoMetrics)
        assert metrics.total_assignments == 100
        assert metrics.risk_level == ZenoRisk.LOW

    @pytest.mark.asyncio
    async def test_get_current_metrics_with_data(self, governor):
        """Test metrics with intervention data."""
        governor.total_assignments = 100
        frozen_ids = {uuid.uuid4() for _ in range(20)}

        # Log intervention
        await governor.log_human_intervention(
            checkpoint_time=datetime.now(),
            assignments_reviewed={uuid.uuid4() for _ in range(30)},
            assignments_locked=frozen_ids,
            user_id="test_user",
        )

        metrics = governor.get_current_metrics()

        assert metrics.interventions_24h == 1
        assert metrics.frozen_assignments == 20
        assert metrics.frozen_ratio == 0.2
        assert "test_user" in metrics.frozen_by_user
        assert metrics.frozen_by_user["test_user"] == 20

    def test_log_solver_attempt_successful(self, governor):
        """Test logging successful solver attempt."""
        changes = {uuid.uuid4(), uuid.uuid4()}

        governor.log_solver_attempt(
            proposed_changes=changes,
            successful=True,
            blocked=False,
            reason="Improved solution",
        )

        assert len(governor.solver_attempts) == 1
        assert governor.solver_attempts[0]["successful"] is True
        assert governor.solver_attempts[0]["blocked"] is False

    def test_log_solver_attempt_blocked(self, governor):
        """Test logging blocked solver attempt."""
        frozen_id = uuid.uuid4()
        governor.frozen_assignments.add(frozen_id)

        governor.log_solver_attempt(
            proposed_changes={frozen_id, uuid.uuid4()},
            successful=False,
            blocked=True,
            reason="Conflicts with frozen assignment",
        )

        assert len(governor.solver_attempts) == 1
        assert governor.solver_attempts[0]["blocked"] is True
        assert frozen_id in governor.solver_attempts[0]["frozen_conflicts"]

    def test_unlock_assignment_success(self, governor):
        """Test unlocking a frozen assignment."""
        assignment_id = uuid.uuid4()
        governor.frozen_assignments.add(assignment_id)

        result = governor.unlock_assignment(assignment_id, user_id="test_user")

        assert result is True
        assert assignment_id not in governor.frozen_assignments
        assert len(governor.interventions) == 1
        assert governor.interventions[0].intervention_type == "unlock"

    def test_unlock_assignment_not_locked(self, governor):
        """Test unlocking assignment that wasn't locked."""
        assignment_id = uuid.uuid4()

        result = governor.unlock_assignment(assignment_id, user_id="test_user")

        assert result is False


class TestZenoDashboard:
    """Tests for ZenoDashboard class."""

    @pytest.fixture
    def governor(self):
        """Create governor instance."""
        gov = ZenoGovernor()
        gov.total_assignments = 100
        return gov

    @pytest.fixture
    def dashboard(self, governor):
        """Create dashboard instance."""
        return ZenoDashboard(governor)

    @pytest.mark.asyncio
    async def test_get_summary_empty(self, dashboard):
        """Test dashboard summary with no data."""
        summary = await dashboard.get_summary()

        assert summary.current_risk == ZenoRisk.LOW
        assert summary.interventions_24h == 0
        assert summary.frozen_assignments == 0

    @pytest.mark.asyncio
    async def test_get_summary_with_data(self, dashboard, governor):
        """Test dashboard summary with intervention data."""
        # Add interventions
        for i in range(5):
            timestamp = datetime.now() - timedelta(hours=i * 3)
            assignments = {uuid.uuid4() for _ in range(10)}

            await governor.log_human_intervention(
                checkpoint_time=timestamp,
                assignments_reviewed=assignments,
                user_id=f"user_{i}",
            )

        summary = await dashboard.get_summary()

        assert summary.interventions_24h > 0
        assert summary.trend_direction in ["improving", "stable", "degrading"]

    @pytest.mark.asyncio
    async def test_get_intervention_history(self, dashboard, governor):
        """Test getting intervention history."""
        # Add interventions
        for i in range(3):
            timestamp = datetime.now() - timedelta(hours=i)
            await governor.log_human_intervention(
                checkpoint_time=timestamp,
                assignments_reviewed={uuid.uuid4()},
                user_id=f"user_{i}",
            )

        history = await dashboard.get_intervention_history(hours=24)

        assert len(history) == 3
        assert all("intervention_id" in item for item in history)
        assert all("user_id" in item for item in history)

    @pytest.mark.asyncio
    async def test_get_freedom_window_status(self, dashboard, governor):
        """Test getting freedom window status."""
        # Create freedom window
        await governor.create_freedom_window(duration_hours=4, reason="Testing")

        status = await dashboard.get_freedom_window_status()

        assert status["total_windows"] == 1
        assert status["active_windows"] == 1
        assert len(status["windows"]) == 1
        assert status["windows"][0]["reason"] == "Testing"

    @pytest.mark.asyncio
    async def test_get_solver_performance_summary_empty(self, dashboard):
        """Test solver performance with no attempts."""
        summary = await dashboard.get_solver_performance_summary()

        assert summary["total_attempts"] == 0
        assert summary["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_solver_performance_summary_with_data(self, dashboard, governor):
        """Test solver performance with attempts."""
        # Log solver attempts
        for i in range(10):
            governor.log_solver_attempt(
                proposed_changes={uuid.uuid4()},
                successful=(i % 3 == 0),  # 3/10 successful
                blocked=(i % 5 == 0),  # 2/10 blocked
            )

        summary = await dashboard.get_solver_performance_summary()

        assert summary["total_attempts"] == 10
        assert summary["successful_attempts"] == 4  # indices 0, 3, 6, 9
        assert summary["blocked_attempts"] == 2  # indices 0, 5
        assert 0.0 <= summary["success_rate"] <= 1.0

    @pytest.mark.asyncio
    async def test_export_metrics_for_monitoring(self, dashboard, governor):
        """Test exporting metrics for Prometheus."""
        # Add some data
        await governor.log_human_intervention(
            checkpoint_time=datetime.now(),
            assignments_reviewed={uuid.uuid4() for _ in range(5)},
        )

        metrics = await dashboard.export_metrics_for_monitoring()

        assert "zeno_risk_level" in metrics
        assert "zeno_frozen_ratio" in metrics
        assert "zeno_measurement_frequency" in metrics
        assert "zeno_local_optima_risk" in metrics

        # Check metric structure
        assert "value" in metrics["zeno_risk_level"]
        assert isinstance(metrics["zeno_frozen_ratio"]["value"], float)


class TestDashboardFormatters:
    """Tests for dashboard formatting functions."""

    def test_format_policy_for_display(self):
        """Test policy formatting."""
        policy = InterventionPolicy(
            max_checks_per_day=2,
            min_interval_hours=12,
            recommended_windows=["09:00-10:00", "17:00-18:00"],
            explanation="Test policy",
        )

        text = format_policy_for_display(policy)

        assert "Max checks per day: 2" in text
        assert "Min interval: 12 hours" in text
        assert "09:00-10:00" in text
        assert "Test policy" in text

    def test_generate_zeno_report(self):
        """Test report generation."""
        metrics = ZenoMetrics(
            risk_level=ZenoRisk.MODERATE,
            interventions_24h=5,
            frozen_ratio=0.25,
            total_assignments=100,
            frozen_assignments=25,
        )

        report = generate_zeno_report(metrics)

        assert "QUANTUM ZENO EFFECT MONITORING REPORT" in report
        assert "MODERATE" in report
        assert "25 / 100" in report
        assert "Interventions: 5" in report


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @pytest.mark.asyncio
    async def test_normal_operations_scenario(self):
        """Test normal operations with reasonable intervention cadence."""
        governor = ZenoGovernor()
        governor.total_assignments = 100

        # 3 reviews per day, spaced 8 hours apart - should stay LOW risk
        for day in range(3):
            for review in range(3):
                timestamp = datetime.now() - timedelta(
                    days=2 - day, hours=8 * (2 - review)
                )
                assignments = {uuid.uuid4() for _ in range(10)}

                risk = await governor.log_human_intervention(
                    checkpoint_time=timestamp,
                    assignments_reviewed=assignments,
                    user_id="coordinator",
                )

        # Should still be low risk
        assert risk == ZenoRisk.LOW

        metrics = governor.get_current_metrics()
        assert metrics.risk_level == ZenoRisk.LOW

    @pytest.mark.asyncio
    async def test_over_monitoring_scenario(self):
        """Test scenario where coordinator checks too frequently."""
        governor = ZenoGovernor()
        governor.total_assignments = 100

        # Check every hour for a day - should escalate to HIGH/CRITICAL
        for hour in range(24):
            timestamp = datetime.now() - timedelta(hours=23 - hour)
            assignments = {uuid.uuid4() for _ in range(5)}
            locked = {list(assignments)[0]}  # Lock one assignment each time

            risk = await governor.log_human_intervention(
                checkpoint_time=timestamp,
                assignments_reviewed=assignments,
                assignments_locked=locked,
                user_id="anxious_coordinator",
            )

        # Should be high or critical risk
        assert risk in [ZenoRisk.HIGH, ZenoRisk.CRITICAL]

        metrics = governor.get_current_metrics()
        assert metrics.interventions_24h >= 20
        assert len(metrics.immediate_actions) > 0

    @pytest.mark.asyncio
    async def test_solver_frozen_scenario(self):
        """Test scenario where solver is blocked by frozen assignments."""
        governor = ZenoGovernor()
        governor.total_assignments = 100

        # Lock 60% of assignments
        frozen_ids = {uuid.uuid4() for _ in range(60)}
        await governor.log_human_intervention(
            checkpoint_time=datetime.now(),
            assignments_reviewed=frozen_ids,
            assignments_locked=frozen_ids,
            user_id="cautious_coordinator",
        )

        # Try solver improvements that conflict with frozen assignments
        for _ in range(10):
            # Mix of frozen and unfrozen in proposed changes
            proposed = set(list(frozen_ids)[:3]) | {uuid.uuid4(), uuid.uuid4()}

            governor.log_solver_attempt(
                proposed_changes=proposed,
                successful=False,
                blocked=True,
                reason="Frozen assignment conflicts",
            )

        metrics = governor.get_current_metrics()

        # Should detect high frozen ratio and blocked evolution
        assert metrics.frozen_ratio >= 0.6
        assert metrics.evolution_prevented > 0
        assert metrics.local_optima_risk > 0.6

        # Should recommend strict policy
        policy = governor.recommend_intervention_policy()
        assert policy.max_checks_per_day <= 2
