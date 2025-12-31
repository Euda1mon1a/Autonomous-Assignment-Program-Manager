"""
Comprehensive tests for AlertGenerator.

Tests the alert generation system including:
- Alert generation based on metrics
- Alert deduplication
- Alert prioritization
- Escalation logic
- Fatigue prevention
"""

import pytest
from datetime import datetime, timedelta

from app.resilience.engine.alert_generator import (
    AlertGenerator,
    Alert,
    AlertSeverity,
    AlertCategory,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def alert_generator():
    """Create alert generator."""
    return AlertGenerator()


# ============================================================================
# Test Class: Utilization Alerts
# ============================================================================


class TestUtilizationAlerts:
    """Tests for utilization-based alerts."""

    def test_no_alert_below_threshold(self, alert_generator):
        """Test no alert generated when below threshold."""
        alert = alert_generator.generate_utilization_alert(
            utilization=0.75, threshold=0.90
        )

        assert alert is None

    def test_info_alert_at_90_percent(self, alert_generator):
        """Test INFO alert at 90% utilization."""
        alert = alert_generator.generate_utilization_alert(
            utilization=0.90, threshold=0.90
        )

        assert alert is not None
        assert alert.severity == AlertSeverity.INFO
        assert alert.category == AlertCategory.UTILIZATION

    def test_warning_alert_at_92_percent(self, alert_generator):
        """Test WARNING alert at 92% utilization."""
        alert = alert_generator.generate_utilization_alert(utilization=0.92)

        assert alert.severity == AlertSeverity.WARNING
        assert "90%" in alert.title or "92%" in alert.title

    def test_critical_alert_at_96_percent(self, alert_generator):
        """Test CRITICAL alert at 96% utilization."""
        alert = alert_generator.generate_utilization_alert(utilization=0.96)

        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.requires_ack is True
        assert alert.escalation_time_minutes == 15

    def test_emergency_alert_at_98_percent(self, alert_generator):
        """Test EMERGENCY alert at 98%+ utilization."""
        alert = alert_generator.generate_utilization_alert(utilization=0.99)

        assert alert.severity == AlertSeverity.EMERGENCY
        assert alert.requires_ack is True
        assert alert.escalation_time_minutes == 5

    def test_utilization_alert_includes_metrics(self, alert_generator):
        """Test utilization alert includes metrics."""
        alert = alert_generator.generate_utilization_alert(utilization=0.95)

        assert "utilization" in alert.metrics
        assert "threshold" in alert.metrics
        assert alert.metrics["utilization"] == 0.95

    def test_utilization_alert_includes_recommendations(self, alert_generator):
        """Test utilization alert includes recommendations."""
        alert = alert_generator.generate_utilization_alert(utilization=0.95)

        assert len(alert.recommendations) > 0
        recs_text = " ".join(alert.recommendations).lower()
        assert "reduce" in recs_text or "backup" in recs_text


# ============================================================================
# Test Class: Burnout Alerts
# ============================================================================


class TestBurnoutAlerts:
    """Tests for burnout epidemic alerts."""

    def test_no_alert_when_under_control(self, alert_generator):
        """Test no alert when burnout under control."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=1, total_population=20, rt=0.8
        )

        assert alert is None

    def test_info_alert_with_low_prevalence_high_rt(self, alert_generator):
        """Test INFO alert with low prevalence but Rt > 1."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=1, total_population=20, rt=1.1  # 5% prevalence
        )

        assert alert is not None
        assert alert.severity == AlertSeverity.INFO

    def test_warning_alert_with_moderate_prevalence(self, alert_generator):
        """Test WARNING alert with 6-10% prevalence."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=2, total_population=20, rt=1.2  # 10% prevalence
        )

        assert alert.severity == AlertSeverity.WARNING
        assert alert.category == AlertCategory.BURNOUT

    def test_critical_alert_with_high_prevalence(self, alert_generator):
        """Test CRITICAL alert with >10% prevalence."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=3, total_population=20, rt=1.6  # 15% prevalence
        )

        assert alert.severity == AlertSeverity.CRITICAL

    def test_critical_alert_with_high_rt(self, alert_generator):
        """Test CRITICAL alert with Rt > 1.5."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=1, total_population=20, rt=1.8
        )

        assert alert.severity == AlertSeverity.CRITICAL

    def test_emergency_alert_with_epidemic(self, alert_generator):
        """Test EMERGENCY alert with epidemic conditions."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=4, total_population=20, rt=2.5  # 20% prevalence, Rt > 2
        )

        assert alert.severity == AlertSeverity.EMERGENCY

    def test_burnout_alert_includes_metrics(self, alert_generator):
        """Test burnout alert includes epidemic metrics."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=3, total_population=20, rt=1.5
        )

        assert "infected" in alert.metrics
        assert "prevalence" in alert.metrics
        assert "rt" in alert.metrics
        assert alert.metrics["infected"] == 3
        assert alert.metrics["rt"] == 1.5

    def test_burnout_alert_indicates_growth_or_decline(self, alert_generator):
        """Test burnout alert indicates if epidemic is growing."""
        alert_growing = alert_generator.generate_burnout_alert(
            infected_count=2, total_population=20, rt=1.5
        )
        alert_declining = alert_generator.generate_burnout_alert(
            infected_count=2, total_population=20, rt=0.7
        )

        assert "growing" in alert_growing.message.lower()
        assert "declining" in alert_declining.message.lower()

    def test_burnout_alert_requires_acknowledgment(self, alert_generator):
        """Test burnout alerts require acknowledgment."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=2, total_population=20, rt=1.2
        )

        assert alert.requires_ack is True

    def test_burnout_alert_includes_intervention_recommendations(
        self, alert_generator
    ):
        """Test burnout alert includes intervention recommendations."""
        alert = alert_generator.generate_burnout_alert(
            infected_count=3, total_population=20, rt=1.5
        )

        recs_text = " ".join(alert.recommendations).lower()
        assert "workload" in recs_text or "wellness" in recs_text or "time off" in recs_text


# ============================================================================
# Test Class: N-1 Contingency Alerts
# ============================================================================


class TestN1ContingencyAlerts:
    """Tests for N-1 contingency failure alerts."""

    def test_no_alert_with_no_spofs(self, alert_generator):
        """Test no alert when no single points of failure."""
        alert = alert_generator.generate_n1_alert(spof_count=0, critical_scenarios=[])

        assert alert is None

    def test_info_alert_with_few_spofs(self, alert_generator):
        """Test INFO alert with 1-2 SPOFs."""
        alert = alert_generator.generate_n1_alert(spof_count=2, critical_scenarios=[])

        assert alert is not None
        assert alert.severity == AlertSeverity.INFO

    def test_warning_alert_with_moderate_spofs(self, alert_generator):
        """Test WARNING alert with 3-4 SPOFs."""
        alert = alert_generator.generate_n1_alert(spof_count=4, critical_scenarios=[])

        assert alert.severity == AlertSeverity.WARNING
        assert alert.category == AlertCategory.CONTINGENCY

    def test_critical_alert_with_many_spofs(self, alert_generator):
        """Test CRITICAL alert with >=5 SPOFs."""
        alert = alert_generator.generate_n1_alert(spof_count=7, critical_scenarios=[])

        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.requires_ack is True

    def test_n1_alert_includes_spof_count(self, alert_generator):
        """Test N-1 alert includes SPOF count."""
        alert = alert_generator.generate_n1_alert(spof_count=5, critical_scenarios=[])

        assert "5" in alert.title
        assert "spof" in alert.title.lower()

    def test_n1_alert_includes_cross_training_recommendation(self, alert_generator):
        """Test N-1 alert recommends cross-training."""
        alert = alert_generator.generate_n1_alert(spof_count=3, critical_scenarios=[])

        recs_text = " ".join(alert.recommendations).lower()
        assert "cross-train" in recs_text or "backup" in recs_text


# ============================================================================
# Test Class: Alert Deduplication
# ============================================================================


class TestAlertDeduplication:
    """Tests for alert deduplication logic."""

    def test_deduplicate_identical_alerts(self, alert_generator):
        """Test that identical alerts are deduplicated."""
        alert1 = alert_generator.generate_utilization_alert(utilization=0.95)
        alert_generator.active_alerts.append(alert1)

        alert2 = alert_generator.generate_utilization_alert(utilization=0.95)

        is_duplicate = alert_generator.deduplicate_alerts(alert2)
        assert is_duplicate is True

    def test_dont_deduplicate_different_categories(self, alert_generator):
        """Test alerts of different categories aren't deduplicated."""
        alert1 = alert_generator.generate_utilization_alert(utilization=0.95)
        alert_generator.active_alerts.append(alert1)

        alert2 = alert_generator.generate_n1_alert(spof_count=5, critical_scenarios=[])

        is_duplicate = alert_generator.deduplicate_alerts(alert2)
        assert is_duplicate is False

    def test_dont_deduplicate_different_severities(self, alert_generator):
        """Test alerts of different severities aren't deduplicated."""
        alert1 = alert_generator.generate_utilization_alert(utilization=0.92)  # WARNING
        alert_generator.active_alerts.append(alert1)

        alert2 = alert_generator.generate_utilization_alert(utilization=0.98)  # EMERGENCY

        is_duplicate = alert_generator.deduplicate_alerts(alert2)
        # Different severities, should not be considered duplicate
        assert is_duplicate is False

    def test_deduplicate_only_recent_alerts(self, alert_generator):
        """Test deduplication only considers recent alerts (last hour)."""
        # Create old alert
        old_alert = alert_generator.generate_utilization_alert(utilization=0.95)
        old_alert.timestamp = datetime.now() - timedelta(hours=2)
        alert_generator.active_alerts.append(old_alert)

        # New alert should not be considered duplicate
        new_alert = alert_generator.generate_utilization_alert(utilization=0.95)
        is_duplicate = alert_generator.deduplicate_alerts(new_alert)

        assert is_duplicate is False


# ============================================================================
# Test Class: Alert Prioritization
# ============================================================================


class TestAlertPrioritization:
    """Tests for alert prioritization logic."""

    def test_prioritize_by_severity(self, alert_generator):
        """Test alerts are prioritized by severity."""
        info_alert = Alert(
            id="1",
            timestamp=datetime.now(),
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            title="Info",
            message="Info message",
            metrics={},
            recommendations=[],
        )
        critical_alert = Alert(
            id="2",
            timestamp=datetime.now(),
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SYSTEM,
            title="Critical",
            message="Critical message",
            metrics={},
            recommendations=[],
        )
        warning_alert = Alert(
            id="3",
            timestamp=datetime.now(),
            severity=AlertSeverity.WARNING,
            category=AlertCategory.SYSTEM,
            title="Warning",
            message="Warning message",
            metrics={},
            recommendations=[],
        )

        prioritized = alert_generator.prioritize_alerts(
            [info_alert, critical_alert, warning_alert]
        )

        assert prioritized[0].severity == AlertSeverity.CRITICAL
        assert prioritized[1].severity == AlertSeverity.WARNING
        assert prioritized[2].severity == AlertSeverity.INFO

    def test_prioritize_emergency_over_critical(self, alert_generator):
        """Test EMERGENCY alerts prioritized over CRITICAL."""
        critical_alert = Alert(
            id="1",
            timestamp=datetime.now(),
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SYSTEM,
            title="Critical",
            message="Critical",
            metrics={},
            recommendations=[],
        )
        emergency_alert = Alert(
            id="2",
            timestamp=datetime.now(),
            severity=AlertSeverity.EMERGENCY,
            category=AlertCategory.SYSTEM,
            title="Emergency",
            message="Emergency",
            metrics={},
            recommendations=[],
        )

        prioritized = alert_generator.prioritize_alerts(
            [critical_alert, emergency_alert]
        )

        assert prioritized[0].severity == AlertSeverity.EMERGENCY

    def test_prioritize_by_timestamp_when_same_severity(self, alert_generator):
        """Test newer alerts prioritized when same severity."""
        old_alert = Alert(
            id="1",
            timestamp=datetime.now() - timedelta(minutes=10),
            severity=AlertSeverity.WARNING,
            category=AlertCategory.SYSTEM,
            title="Old",
            message="Old",
            metrics={},
            recommendations=[],
        )
        new_alert = Alert(
            id="2",
            timestamp=datetime.now(),
            severity=AlertSeverity.WARNING,
            category=AlertCategory.SYSTEM,
            title="New",
            message="New",
            metrics={},
            recommendations=[],
        )

        prioritized = alert_generator.prioritize_alerts([old_alert, new_alert])

        assert prioritized[0].id == "2"  # Newer alert first


# ============================================================================
# Test Class: Alert Escalation
# ============================================================================


class TestAlertEscalation:
    """Tests for alert escalation logic."""

    def test_should_not_escalate_without_escalation_time(self, alert_generator):
        """Test alerts without escalation time don't escalate."""
        alert = Alert(
            id="1",
            timestamp=datetime.now() - timedelta(minutes=30),
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Test",
            metrics={},
            recommendations=[],
            escalation_time_minutes=None,
        )

        should_escalate = alert_generator.should_escalate(alert)
        assert should_escalate is False

    def test_should_not_escalate_before_time(self, alert_generator):
        """Test alert doesn't escalate before escalation time."""
        alert = Alert(
            id="1",
            timestamp=datetime.now() - timedelta(minutes=10),
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Test",
            metrics={},
            recommendations=[],
            escalation_time_minutes=15,
        )

        should_escalate = alert_generator.should_escalate(alert)
        assert should_escalate is False

    def test_should_escalate_after_time(self, alert_generator):
        """Test alert escalates after escalation time passes."""
        alert = Alert(
            id="1",
            timestamp=datetime.now() - timedelta(minutes=20),
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SYSTEM,
            title="Test",
            message="Test",
            metrics={},
            recommendations=[],
            escalation_time_minutes=15,
        )

        should_escalate = alert_generator.should_escalate(alert)
        assert should_escalate is True

    def test_emergency_alerts_escalate_quickly(self, alert_generator):
        """Test EMERGENCY alerts have short escalation time."""
        alert = alert_generator.generate_utilization_alert(utilization=0.99)

        assert alert.escalation_time_minutes == 5

    def test_critical_alerts_escalate_moderately(self, alert_generator):
        """Test CRITICAL alerts have moderate escalation time."""
        alert = alert_generator.generate_utilization_alert(utilization=0.96)

        assert alert.escalation_time_minutes == 15

    def test_warning_alerts_escalate_slowly(self, alert_generator):
        """Test WARNING alerts have longer escalation time."""
        alert = alert_generator.generate_utilization_alert(utilization=0.92)

        assert alert.escalation_time_minutes == 60


# ============================================================================
# Test Class: Alert Structure
# ============================================================================


class TestAlertStructure:
    """Tests for alert data structure."""

    def test_alert_has_unique_id(self, alert_generator):
        """Test each alert has a unique ID."""
        alert1 = alert_generator.generate_utilization_alert(utilization=0.95)
        alert2 = alert_generator.generate_utilization_alert(utilization=0.95)

        assert alert1.id != alert2.id

    def test_alert_has_timestamp(self, alert_generator):
        """Test alert has timestamp."""
        before = datetime.now()
        alert = alert_generator.generate_utilization_alert(utilization=0.95)
        after = datetime.now()

        assert before <= alert.timestamp <= after

    def test_alert_has_severity_and_category(self, alert_generator):
        """Test alert has severity and category."""
        alert = alert_generator.generate_utilization_alert(utilization=0.95)

        assert isinstance(alert.severity, AlertSeverity)
        assert isinstance(alert.category, AlertCategory)

    def test_alert_has_title_and_message(self, alert_generator):
        """Test alert has title and message."""
        alert = alert_generator.generate_utilization_alert(utilization=0.95)

        assert len(alert.title) > 0
        assert len(alert.message) > 0

    def test_alert_has_metrics_dict(self, alert_generator):
        """Test alert has metrics dictionary."""
        alert = alert_generator.generate_utilization_alert(utilization=0.95)

        assert isinstance(alert.metrics, dict)
        assert len(alert.metrics) > 0

    def test_alert_has_recommendations_list(self, alert_generator):
        """Test alert has recommendations list."""
        alert = alert_generator.generate_utilization_alert(utilization=0.95)

        assert isinstance(alert.recommendations, list)
        assert len(alert.recommendations) > 0


# ============================================================================
# Test Class: Alert History
# ============================================================================


class TestAlertHistory:
    """Tests for alert history tracking."""

    def test_alert_history_starts_empty(self, alert_generator):
        """Test alert history starts empty."""
        assert len(alert_generator.alert_history) == 0

    def test_active_alerts_starts_empty(self, alert_generator):
        """Test active alerts list starts empty."""
        assert len(alert_generator.active_alerts) == 0

    def test_suppressed_alerts_starts_empty(self, alert_generator):
        """Test suppressed alerts set starts empty."""
        assert len(alert_generator.suppressed_alerts) == 0
