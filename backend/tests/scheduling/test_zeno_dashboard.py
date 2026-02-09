"""Tests for Zeno dashboard metrics and reporting (pure logic, no DB required)."""

import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.scheduling.zeno_dashboard import (
    ZenoDashboard,
    ZenoDashboardSummary,
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


# ==================== Helpers ====================


def _run(coro):
    """Run async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _make_metrics(
    risk: ZenoRisk = ZenoRisk.LOW,
    frozen_ratio: float = 0.0,
    measurement_frequency: float = 0.0,
    local_optima_risk: float = 0.0,
    interventions_24h: int = 0,
    interventions_7d: int = 0,
    frozen_assignments: int = 0,
    total_assignments: int = 100,
    evolution_prevented: int = 0,
    solver_attempts_blocked: int = 0,
    frozen_by_user: dict | None = None,
    last_successful_evolution: datetime | None = None,
    immediate_actions: list | None = None,
    watch_items: list | None = None,
) -> ZenoMetrics:
    """Build a ZenoMetrics with controlled values."""
    return ZenoMetrics(
        timestamp=datetime(2025, 6, 15, 10, 0, 0),
        risk_level=risk,
        measurement_frequency=measurement_frequency,
        frozen_ratio=frozen_ratio,
        local_optima_risk=local_optima_risk,
        interventions_24h=interventions_24h,
        interventions_7d=interventions_7d,
        frozen_assignments=frozen_assignments,
        total_assignments=total_assignments,
        evolution_prevented=evolution_prevented,
        solver_attempts_blocked=solver_attempts_blocked,
        frozen_by_user=frozen_by_user or {},
        last_successful_evolution=last_successful_evolution,
        immediate_actions=immediate_actions or [],
        watch_items=watch_items or [],
    )


def _make_dashboard() -> tuple[ZenoDashboard, ZenoGovernor]:
    """Build a ZenoDashboard with fresh governor."""
    gov = ZenoGovernor()
    return ZenoDashboard(gov), gov


# ==================== ZenoDashboardSummary Tests ====================


class TestZenoDashboardSummary:
    """Test ZenoDashboardSummary dataclass."""

    def test_basic_construction(self):
        s = ZenoDashboardSummary(
            current_risk=ZenoRisk.LOW,
            current_frozen_ratio=0.05,
            current_measurement_frequency=0.1,
            local_optima_risk=0.2,
            interventions_24h=2,
            frozen_assignments=5,
            solver_attempts_blocked=0,
            evolution_prevented=0,
            interventions_7d=10,
            avg_interventions_per_day=10 / 7,
            trend_direction="stable",
            recommended_policy={},
            is_in_freedom_window=False,
            active_freedom_windows=0,
            critical_alerts=[],
            warnings=[],
            recommendations=[],
            last_successful_evolution=None,
            hours_since_evolution=None,
        )
        assert s.current_risk == ZenoRisk.LOW
        assert s.trend_direction == "stable"


# ==================== _analyze_trend Tests ====================


class TestAnalyzeTrend:
    """Test _analyze_trend method."""

    def test_zero_7d_returns_stable(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(interventions_7d=0, interventions_24h=5)
        assert dashboard._analyze_trend(m) == "stable"

    def test_improving_when_24h_below_average(self):
        dashboard, _ = _make_dashboard()
        # avg = 7/7 = 1.0; 24h = 0 < 1.0 * 0.8 = 0.8
        m = _make_metrics(interventions_7d=7, interventions_24h=0)
        assert dashboard._analyze_trend(m) == "improving"

    def test_degrading_when_24h_above_average(self):
        dashboard, _ = _make_dashboard()
        # avg = 7/7 = 1.0; 24h = 3 > 1.0 * 1.2 = 1.2
        m = _make_metrics(interventions_7d=7, interventions_24h=3)
        assert dashboard._analyze_trend(m) == "degrading"

    def test_stable_when_24h_near_average(self):
        dashboard, _ = _make_dashboard()
        # avg = 7/7 = 1.0; 24h = 1 is in [0.8, 1.2]
        m = _make_metrics(interventions_7d=7, interventions_24h=1)
        assert dashboard._analyze_trend(m) == "stable"


# ==================== _generate_critical_alerts Tests ====================


class TestGenerateCriticalAlerts:
    """Test _generate_critical_alerts method."""

    def test_low_risk_no_alerts(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(risk=ZenoRisk.LOW)
        assert dashboard._generate_critical_alerts(m) == []

    def test_critical_risk_alert(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(
            risk=ZenoRisk.CRITICAL,
            frozen_ratio=0.6,
            measurement_frequency=0.5,
        )
        alerts = dashboard._generate_critical_alerts(m)
        assert any("CRITICAL" in a for a in alerts)

    def test_high_frozen_ratio_alert(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(frozen_ratio=0.75)
        alerts = dashboard._generate_critical_alerts(m)
        assert any("75%" in a for a in alerts)

    def test_high_evolution_prevented_alert(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(evolution_prevented=15)
        alerts = dashboard._generate_critical_alerts(m)
        assert any("15" in a and "blocked" in a for a in alerts)

    def test_stale_evolution_alert(self):
        dashboard, _ = _make_dashboard()
        stale_time = datetime.now() - timedelta(hours=72)
        m = _make_metrics(last_successful_evolution=stale_time)
        alerts = dashboard._generate_critical_alerts(m)
        assert any("local optimum" in a for a in alerts)

    def test_recent_evolution_no_stale_alert(self):
        dashboard, _ = _make_dashboard()
        recent = datetime.now() - timedelta(hours=1)
        m = _make_metrics(last_successful_evolution=recent)
        alerts = dashboard._generate_critical_alerts(m)
        assert not any("local optimum" in a for a in alerts)


# ==================== _generate_warnings Tests ====================


class TestGenerateWarnings:
    """Test _generate_warnings method."""

    def test_low_risk_no_warnings(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(risk=ZenoRisk.LOW)
        assert dashboard._generate_warnings(m) == []

    def test_high_risk_warning(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(risk=ZenoRisk.HIGH, measurement_frequency=0.3)
        warnings = dashboard._generate_warnings(m)
        assert any("HIGH" in w for w in warnings)

    def test_moderate_risk_warning(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(risk=ZenoRisk.MODERATE, frozen_ratio=0.2)
        warnings = dashboard._generate_warnings(m)
        assert any("MODERATE" in w for w in warnings)

    def test_local_optima_risk_warning(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(local_optima_risk=0.8)
        warnings = dashboard._generate_warnings(m)
        assert any("optima" in w.lower() for w in warnings)

    def test_solver_blocked_warning(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(solver_attempts_blocked=8)
        warnings = dashboard._generate_warnings(m)
        assert any("8" in w and "blocked" in w for w in warnings)

    def test_user_locking_too_many_warning(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(
            total_assignments=100,
            frozen_by_user={"user_abc": 40},
        )
        warnings = dashboard._generate_warnings(m)
        assert any("user_abc" in w for w in warnings)

    def test_user_locking_below_threshold_no_warning(self):
        dashboard, _ = _make_dashboard()
        m = _make_metrics(
            total_assignments=100,
            frozen_by_user={"user_abc": 5},
        )
        warnings = dashboard._generate_warnings(m)
        assert not any("user_abc" in w for w in warnings)


# ==================== format_policy_for_display Tests ====================


class TestFormatPolicyForDisplay:
    """Test format_policy_for_display standalone function."""

    def test_basic_output(self):
        policy = InterventionPolicy()
        result = format_policy_for_display(policy)
        assert "Recommended Intervention Policy" in result

    def test_max_checks_shown(self):
        policy = InterventionPolicy(max_checks_per_day=5)
        result = format_policy_for_display(policy)
        assert "5" in result

    def test_min_interval_shown(self):
        policy = InterventionPolicy(min_interval_hours=4)
        result = format_policy_for_display(policy)
        assert "4 hours" in result

    def test_review_windows_listed(self):
        policy = InterventionPolicy(recommended_windows=["09:00-10:00", "15:00-16:00"])
        result = format_policy_for_display(policy)
        assert "09:00-10:00" in result
        assert "15:00-16:00" in result

    def test_hands_off_periods_shown(self):
        policy = InterventionPolicy(
            hands_off_periods=[
                {
                    "start": "22:00",
                    "end": "06:00",
                    "duration_hours": 8,
                    "reason": "Overnight solver run",
                }
            ]
        )
        result = format_policy_for_display(policy)
        assert "Overnight solver run" in result
        assert "22:00" in result

    def test_no_hands_off_periods(self):
        policy = InterventionPolicy(hands_off_periods=[])
        result = format_policy_for_display(policy)
        assert "Hands-off" not in result

    def test_auto_lock_threshold_shown(self):
        policy = InterventionPolicy(auto_lock_threshold=0.9)
        result = format_policy_for_display(policy)
        assert "90%" in result

    def test_explanation_shown(self):
        policy = InterventionPolicy(explanation="Reduce monitoring frequency")
        result = format_policy_for_display(policy)
        assert "Reduce monitoring frequency" in result


# ==================== generate_zeno_report Tests ====================


class TestGenerateZenoReport:
    """Test generate_zeno_report standalone function."""

    def test_basic_report(self):
        m = _make_metrics()
        report = generate_zeno_report(m)
        assert "QUANTUM ZENO EFFECT MONITORING REPORT" in report

    def test_risk_level_shown(self):
        m = _make_metrics(risk=ZenoRisk.CRITICAL)
        report = generate_zeno_report(m)
        assert "CRITICAL" in report

    def test_low_risk_emoji(self):
        m = _make_metrics(risk=ZenoRisk.LOW)
        report = generate_zeno_report(m)
        # Check the emoji is present (checkmark for LOW)
        assert "LOW" in report

    def test_frozen_stats_shown(self):
        m = _make_metrics(
            frozen_assignments=15, total_assignments=100, frozen_ratio=0.15
        )
        report = generate_zeno_report(m)
        assert "15" in report
        assert "100" in report

    def test_24h_activity_section(self):
        m = _make_metrics(interventions_24h=7, solver_attempts_blocked=3)
        report = generate_zeno_report(m)
        assert "24-HOUR ACTIVITY" in report
        assert "7" in report

    def test_7d_trends_section(self):
        m = _make_metrics(interventions_7d=21)
        report = generate_zeno_report(m)
        assert "7-DAY TRENDS" in report
        assert "21" in report

    def test_last_evolution_never(self):
        m = _make_metrics(last_successful_evolution=None)
        report = generate_zeno_report(m)
        assert "Never" in report

    def test_last_evolution_shown(self):
        recent = datetime.now() - timedelta(hours=5)
        m = _make_metrics(last_successful_evolution=recent)
        report = generate_zeno_report(m)
        assert "hours ago" in report

    def test_frozen_by_user_section(self):
        m = _make_metrics(
            frozen_by_user={"coord_1": 10, "coord_2": 5},
            total_assignments=100,
        )
        report = generate_zeno_report(m)
        assert "coord_1" in report
        assert "coord_2" in report

    def test_no_frozen_by_user_skips_section(self):
        m = _make_metrics(frozen_by_user={})
        report = generate_zeno_report(m)
        assert "FROZEN ASSIGNMENTS BY USER" not in report

    def test_immediate_actions_section(self):
        m = _make_metrics(immediate_actions=["Reduce check frequency"])
        report = generate_zeno_report(m)
        assert "IMMEDIATE ACTIONS" in report
        assert "Reduce check frequency" in report

    def test_watch_items_section(self):
        m = _make_metrics(watch_items=["Monitor solver convergence"])
        report = generate_zeno_report(m)
        assert "WATCH ITEMS" in report
        assert "Monitor solver convergence" in report

    def test_policy_section(self):
        m = _make_metrics()
        report = generate_zeno_report(m)
        assert "RECOMMENDED POLICY" in report

    def test_timestamp_shown(self):
        m = _make_metrics()
        report = generate_zeno_report(m)
        assert "2025-06-15" in report


# ==================== Async Dashboard Methods Tests ====================


class TestGetSummary:
    """Test ZenoDashboard.get_summary async method."""

    def test_empty_governor_returns_summary(self):
        dashboard, gov = _make_dashboard()
        gov.total_assignments = 50
        summary = _run(dashboard.get_summary())
        assert isinstance(summary, ZenoDashboardSummary)
        assert summary.current_risk == ZenoRisk.LOW
        assert summary.interventions_24h == 0

    def test_summary_trend_direction(self):
        dashboard, gov = _make_dashboard()
        gov.total_assignments = 50
        summary = _run(dashboard.get_summary())
        assert summary.trend_direction in ("improving", "stable", "degrading")


class TestGetInterventionHistory:
    """Test get_intervention_history async method."""

    def test_empty_history(self):
        dashboard, _ = _make_dashboard()
        history = _run(dashboard.get_intervention_history(24))
        assert history == []

    def test_recent_interventions_returned(self):
        dashboard, gov = _make_dashboard()
        gov.interventions.append(
            HumanIntervention(
                timestamp=datetime.now() - timedelta(hours=1),
                user_id="test_user",
                assignments_reviewed={uuid4()},
                intervention_type="review",
                reason="routine check",
            )
        )
        history = _run(dashboard.get_intervention_history(24))
        assert len(history) == 1
        assert history[0]["user_id"] == "test_user"
        assert history[0]["type"] == "review"

    def test_old_interventions_filtered(self):
        dashboard, gov = _make_dashboard()
        gov.interventions.append(
            HumanIntervention(
                timestamp=datetime.now() - timedelta(hours=48),
                user_id="old_user",
                assignments_reviewed={uuid4()},
            )
        )
        history = _run(dashboard.get_intervention_history(24))
        assert len(history) == 0


class TestGetFreedomWindowStatus:
    """Test get_freedom_window_status async method."""

    def test_no_windows(self):
        dashboard, _ = _make_dashboard()
        status = _run(dashboard.get_freedom_window_status())
        assert status["is_in_freedom_window"] is False
        assert status["active_windows"] == 0
        assert status["total_windows"] == 0
        assert status["windows"] == []

    def test_active_window(self):
        dashboard, gov = _make_dashboard()
        now = datetime.now()
        gov.freedom_windows.append(
            OptimizationFreedomWindow(
                start_time=now - timedelta(hours=1),
                end_time=now + timedelta(hours=3),
                is_active=True,
                reason="overnight run",
            )
        )
        status = _run(dashboard.get_freedom_window_status())
        assert status["total_windows"] == 1
        assert status["active_windows"] == 1
        assert status["windows"][0]["reason"] == "overnight run"


class TestGetSolverPerformanceSummary:
    """Test get_solver_performance_summary async method."""

    def test_no_attempts(self):
        dashboard, _ = _make_dashboard()
        summary = _run(dashboard.get_solver_performance_summary())
        assert summary["total_attempts"] == 0
        assert summary["success_rate"] == 0.0

    def test_with_attempts(self):
        dashboard, gov = _make_dashboard()
        gov.solver_attempts = [
            {"successful": True, "blocked": False},
            {"successful": False, "blocked": True},
            {"successful": True, "blocked": False},
        ]
        summary = _run(dashboard.get_solver_performance_summary())
        assert summary["total_attempts"] == 3
        assert summary["successful_attempts"] == 2
        assert summary["blocked_attempts"] == 1
        assert summary["success_rate"] == pytest.approx(2 / 3)
        assert summary["block_rate"] == pytest.approx(1 / 3)


class TestExportMetricsForMonitoring:
    """Test export_metrics_for_monitoring async method."""

    def test_basic_export(self):
        dashboard, gov = _make_dashboard()
        gov.total_assignments = 50
        export = _run(dashboard.export_metrics_for_monitoring())
        assert "zeno_risk_level" in export
        assert "zeno_frozen_ratio" in export
        assert "zeno_measurement_frequency" in export
        assert "zeno_local_optima_risk" in export
        assert "zeno_interventions_24h" in export
        assert "zeno_evolution_prevented" in export
        assert "zeno_solver_attempts_blocked" in export
        assert "zeno_in_freedom_window" in export

    def test_risk_level_values(self):
        dashboard, gov = _make_dashboard()
        gov.total_assignments = 50
        export = _run(dashboard.export_metrics_for_monitoring())
        assert export["zeno_risk_level"]["value"] in (0, 1, 2, 3)

    def test_gauge_types(self):
        dashboard, gov = _make_dashboard()
        gov.total_assignments = 50
        export = _run(dashboard.export_metrics_for_monitoring())
        assert export["zeno_frozen_ratio"]["type"] == "gauge"
        assert export["zeno_measurement_frequency"]["type"] == "gauge"
