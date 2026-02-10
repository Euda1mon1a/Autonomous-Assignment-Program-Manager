"""Tests for FRMS monitoring and alerting (no DB)."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.frms.monitoring import (
    AlertSeverity,
    DashboardMetrics,
    FatigueAlert,
    FatigueMonitor,
)


# ---------------------------------------------------------------------------
# AlertSeverity enum
# ---------------------------------------------------------------------------


class TestAlertSeverity:
    def test_values(self):
        assert AlertSeverity.INFO == "info"
        assert AlertSeverity.WARNING == "warning"
        assert AlertSeverity.CRITICAL == "critical"
        assert AlertSeverity.EMERGENCY == "emergency"

    def test_count(self):
        assert len(AlertSeverity) == 4

    def test_is_string_enum(self):
        assert isinstance(AlertSeverity.INFO, str)


# ---------------------------------------------------------------------------
# FatigueAlert dataclass
# ---------------------------------------------------------------------------


class TestFatigueAlert:
    def _make(self, **overrides):
        defaults = {
            "alert_id": "alert_001",
            "person_id": uuid4(),
            "person_name": "Test Resident",
            "severity": AlertSeverity.WARNING,
            "created_at": datetime(2026, 1, 15, 8, 0),
            "effectiveness_score": 75.0,
            "threshold_violated": 77.0,
            "message": "WARNING: test",
        }
        defaults.update(overrides)
        return FatigueAlert(**defaults)

    def test_defaults(self):
        alert = self._make()
        assert alert.contributing_factors == {}
        assert alert.recommended_actions == []
        assert alert.acknowledged is False
        assert alert.acknowledged_at is None
        assert alert.acknowledged_by is None

    def test_to_dict_keys(self):
        d = self._make().to_dict()
        expected = {
            "alert_id",
            "person_id",
            "person_name",
            "severity",
            "created_at",
            "effectiveness_score",
            "threshold_violated",
            "message",
            "contributing_factors",
            "recommended_actions",
            "acknowledged",
            "acknowledged_at",
            "acknowledged_by",
        }
        assert set(d.keys()) == expected

    def test_to_dict_person_id_string(self):
        pid = uuid4()
        d = self._make(person_id=pid).to_dict()
        assert d["person_id"] == str(pid)

    def test_to_dict_severity_value(self):
        d = self._make(severity=AlertSeverity.CRITICAL).to_dict()
        assert d["severity"] == "critical"

    def test_to_dict_created_at_iso(self):
        t = datetime(2026, 1, 15, 8, 30)
        d = self._make(created_at=t).to_dict()
        assert d["created_at"] == t.isoformat()

    def test_to_dict_rounds_effectiveness(self):
        d = self._make(effectiveness_score=75.456).to_dict()
        assert d["effectiveness_score"] == 75.46

    def test_to_dict_rounds_threshold(self):
        d = self._make(threshold_violated=77.789).to_dict()
        assert d["threshold_violated"] == 77.79

    def test_to_dict_acknowledged_at_none(self):
        d = self._make().to_dict()
        assert d["acknowledged_at"] is None

    def test_to_dict_acknowledged_at_iso(self):
        t = datetime(2026, 1, 15, 9, 0)
        d = self._make(acknowledged_at=t).to_dict()
        assert d["acknowledged_at"] == t.isoformat()


# ---------------------------------------------------------------------------
# DashboardMetrics dataclass
# ---------------------------------------------------------------------------


class TestDashboardMetrics:
    def _make(self, **overrides):
        defaults = {
            "timestamp": datetime(2026, 1, 15, 8, 0),
            "total_residents": 30,
            "active_alerts": 2,
            "at_optimal": 10,
            "at_acceptable": 12,
            "at_caution": 5,
            "at_high_risk": 2,
            "at_critical": 1,
            "improving": 8,
            "stable": 18,
            "degrading": 4,
        }
        defaults.update(overrides)
        return DashboardMetrics(**defaults)

    def test_defaults(self):
        dm = self._make()
        assert dm.highest_risk_residents == []
        assert dm.upcoming_risk_shifts == []
        assert dm.alerts_last_24h == 0
        assert dm.avg_effectiveness_24h == 85.0
        assert dm.min_effectiveness_24h == 70.0

    def test_to_dict_top_level_keys(self):
        d = self._make().to_dict()
        expected = {
            "timestamp",
            "total_residents",
            "active_alerts",
            "distribution",
            "trends",
            "highest_risk_residents",
            "upcoming_risk_shifts",
            "last_24h",
        }
        assert set(d.keys()) == expected

    def test_to_dict_distribution(self):
        d = self._make().to_dict()
        dist = d["distribution"]
        assert dist["optimal"] == 10
        assert dist["acceptable"] == 12
        assert dist["caution"] == 5
        assert dist["high_risk"] == 2
        assert dist["critical"] == 1

    def test_to_dict_trends(self):
        d = self._make().to_dict()
        trends = d["trends"]
        assert trends["improving"] == 8
        assert trends["stable"] == 18
        assert trends["degrading"] == 4

    def test_to_dict_last_24h(self):
        d = self._make(
            alerts_last_24h=5,
            avg_effectiveness_24h=82.456,
            min_effectiveness_24h=65.789,
        ).to_dict()
        last = d["last_24h"]
        assert last["alerts"] == 5
        assert last["avg_effectiveness"] == 82.46
        assert last["min_effectiveness"] == 65.79

    def test_to_dict_timestamp_iso(self):
        t = datetime(2026, 1, 15, 8, 0)
        d = self._make(timestamp=t).to_dict()
        assert d["timestamp"] == t.isoformat()


# ---------------------------------------------------------------------------
# FatigueMonitor — init
# ---------------------------------------------------------------------------


class TestFatigueMonitorInit:
    def test_creates_instance(self):
        monitor = FatigueMonitor()
        assert monitor is not None

    def test_default_notifications(self):
        monitor = FatigueMonitor()
        assert monitor.enable_notifications is True

    def test_disabled_notifications(self):
        monitor = FatigueMonitor(enable_notifications=False)
        assert monitor.enable_notifications is False

    def test_default_no_callback(self):
        monitor = FatigueMonitor()
        assert monitor.alert_callback is None

    def test_custom_callback(self):
        cb = lambda x: None  # noqa: E731
        monitor = FatigueMonitor(alert_callback=cb)
        assert monitor.alert_callback is cb

    def test_empty_state(self):
        monitor = FatigueMonitor()
        assert len(monitor._resident_states) == 0
        assert len(monitor._active_alerts) == 0
        assert len(monitor._alert_history) == 0


# ---------------------------------------------------------------------------
# FatigueMonitor._get_recommendations
# ---------------------------------------------------------------------------


def _mock_effectiveness(overall=85.0, factors=None):
    """Create a mock EffectivenessScore with just the attributes we need."""
    return SimpleNamespace(
        overall=overall,
        factors=factors or {},
    )


class TestGetRecommendations:
    def test_emergency_includes_remove(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(55.0)
        recs = monitor._get_recommendations(AlertSeverity.EMERGENCY, eff)
        assert any("remove" in r.lower() for r in recs)

    def test_emergency_includes_mandatory_rest(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(55.0)
        recs = monitor._get_recommendations(AlertSeverity.EMERGENCY, eff)
        assert any("mandatory rest" in r.lower() for r in recs)

    def test_critical_includes_supervision(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(68.0)
        recs = monitor._get_recommendations(AlertSeverity.CRITICAL, eff)
        assert any("supervision" in r.lower() for r in recs)

    def test_critical_avoids_high_risk(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(68.0)
        recs = monitor._get_recommendations(AlertSeverity.CRITICAL, eff)
        assert any("high-risk" in r.lower() for r in recs)

    def test_warning_includes_monitor(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(75.0)
        recs = monitor._get_recommendations(AlertSeverity.WARNING, eff)
        assert any("monitor" in r.lower() for r in recs)

    def test_info_includes_track(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(82.0)
        recs = monitor._get_recommendations(AlertSeverity.INFO, eff)
        assert any("track" in r.lower() for r in recs)

    def test_wocl_factor_adds_recommendation(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(75.0, factors={"in_wocl": True})
        recs = monitor._get_recommendations(AlertSeverity.WARNING, eff)
        assert any("WOCL" in r for r in recs)

    def test_extended_wakefulness_factor(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(75.0, factors={"hours_awake": 20})
        recs = monitor._get_recommendations(AlertSeverity.WARNING, eff)
        assert any("wakefulness" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# FatigueMonitor._check_and_generate_alert
# ---------------------------------------------------------------------------


class TestCheckAndGenerateAlert:
    def test_no_alert_above_acceptable(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(90.0, factors={})
        result = monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert result is None

    def test_info_alert_below_acceptable(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(82.0, factors={})
        result = monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert result is not None
        assert result.severity == AlertSeverity.INFO

    def test_warning_alert_below_faa(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(74.0, factors={})
        result = monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert result is not None
        assert result.severity == AlertSeverity.WARNING

    def test_critical_alert_below_fra(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(65.0, factors={})
        result = monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert result is not None
        assert result.severity == AlertSeverity.CRITICAL

    def test_emergency_alert_below_critical(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(55.0, factors={})
        result = monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert result is not None
        assert result.severity == AlertSeverity.EMERGENCY

    def test_alert_stored_in_active(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(74.0, factors={})
        alert = monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert alert.alert_id in monitor._active_alerts

    def test_alert_stored_in_history(self):
        monitor = FatigueMonitor()
        eff = _mock_effectiveness(74.0, factors={})
        monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert len(monitor._alert_history) == 1

    def test_deduplication_within_hour(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        eff = _mock_effectiveness(74.0, factors={})
        alert1 = monitor._check_and_generate_alert(
            pid, "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        alert2 = monitor._check_and_generate_alert(
            pid, "Test", eff, datetime(2026, 1, 15, 8, 30)
        )
        assert alert1 is not None
        assert alert2 is None

    def test_callback_triggered(self):
        received = []
        monitor = FatigueMonitor(alert_callback=lambda a: received.append(a))
        eff = _mock_effectiveness(74.0, factors={})
        monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert len(received) == 1

    def test_callback_not_triggered_when_disabled(self):
        received = []
        monitor = FatigueMonitor(
            alert_callback=lambda a: received.append(a),
            enable_notifications=False,
        )
        eff = _mock_effectiveness(74.0, factors={})
        monitor._check_and_generate_alert(
            uuid4(), "Test", eff, datetime(2026, 1, 15, 8, 0)
        )
        assert len(received) == 0


# ---------------------------------------------------------------------------
# FatigueMonitor._cleanup_old_alert_keys
# ---------------------------------------------------------------------------


class TestCleanupOldAlertKeys:
    def test_removes_old_keys(self):
        monitor = FatigueMonitor()
        now = datetime(2026, 1, 15, 10, 0)
        old = now - timedelta(hours=2)
        monitor._recent_alert_keys["old_key"] = old
        monitor._cleanup_old_alert_keys(now)
        assert "old_key" not in monitor._recent_alert_keys

    def test_keeps_recent_keys(self):
        monitor = FatigueMonitor()
        now = datetime(2026, 1, 15, 10, 0)
        recent = now - timedelta(minutes=30)
        monitor._recent_alert_keys["recent_key"] = recent
        monitor._cleanup_old_alert_keys(now)
        assert "recent_key" in monitor._recent_alert_keys


# ---------------------------------------------------------------------------
# FatigueMonitor.check_alerts / acknowledge_alert
# ---------------------------------------------------------------------------


class TestCheckAndAcknowledgeAlerts:
    def _add_alert(self, monitor, alert_id="alert_1", acknowledged=False):
        alert = FatigueAlert(
            alert_id=alert_id,
            person_id=uuid4(),
            person_name="Test",
            severity=AlertSeverity.WARNING,
            created_at=datetime(2026, 1, 15, 8, 0),
            effectiveness_score=75.0,
            threshold_violated=77.0,
            message="test",
            acknowledged=acknowledged,
        )
        monitor._active_alerts[alert_id] = alert
        return alert

    def test_check_returns_unacknowledged(self):
        monitor = FatigueMonitor()
        self._add_alert(monitor, "a1")
        self._add_alert(monitor, "a2", acknowledged=True)
        alerts = monitor.check_alerts()
        assert len(alerts) == 1
        assert alerts[0].alert_id == "a1"

    def test_check_empty(self):
        monitor = FatigueMonitor()
        assert monitor.check_alerts() == []

    def test_acknowledge_returns_true(self):
        monitor = FatigueMonitor()
        self._add_alert(monitor, "a1")
        assert monitor.acknowledge_alert("a1", "Dr. Smith") is True

    def test_acknowledge_sets_fields(self):
        monitor = FatigueMonitor()
        self._add_alert(monitor, "a1")
        monitor.acknowledge_alert("a1", "Dr. Smith")
        alert = monitor._active_alerts["a1"]
        assert alert.acknowledged is True
        assert alert.acknowledged_by == "Dr. Smith"
        assert alert.acknowledged_at is not None

    def test_acknowledge_nonexistent_returns_false(self):
        monitor = FatigueMonitor()
        assert monitor.acknowledge_alert("nonexistent", "Dr. Smith") is False


# ---------------------------------------------------------------------------
# FatigueMonitor._calculate_trend
# ---------------------------------------------------------------------------


class TestCalculateTrend:
    def test_no_history_returns_zero(self):
        monitor = FatigueMonitor()
        assert monitor._calculate_trend(uuid4()) == 0.0

    def test_single_entry_returns_zero(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        now = datetime.now()
        monitor._effectiveness_history[pid] = [(now, 85.0)]
        assert monitor._calculate_trend(pid) == 0.0

    def test_improving_trend_positive(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        now = datetime.now()
        monitor._effectiveness_history[pid] = [
            (now - timedelta(hours=1), 70.0),
            (now, 85.0),
        ]
        assert monitor._calculate_trend(pid) > 0

    def test_degrading_trend_negative(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        now = datetime.now()
        monitor._effectiveness_history[pid] = [
            (now - timedelta(hours=1), 90.0),
            (now, 70.0),
        ]
        assert monitor._calculate_trend(pid) < 0


# ---------------------------------------------------------------------------
# FatigueMonitor.get_resident_history
# ---------------------------------------------------------------------------


class TestGetResidentHistory:
    def test_no_history_returns_empty(self):
        monitor = FatigueMonitor()
        result = monitor.get_resident_history(uuid4())
        assert result == []

    def test_returns_recent_entries(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        now = datetime.now()
        monitor._effectiveness_history[pid] = [
            (now - timedelta(hours=2), 85.0),
            (now - timedelta(hours=1), 80.0),
            (now, 75.0),
        ]
        result = monitor.get_resident_history(pid, hours=24)
        assert len(result) == 3

    def test_filters_old_entries(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        now = datetime.now()
        monitor._effectiveness_history[pid] = [
            (now - timedelta(hours=48), 90.0),
            (now, 75.0),
        ]
        result = monitor.get_resident_history(pid, hours=24)
        assert len(result) == 1

    def test_entry_format(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        now = datetime.now()
        monitor._effectiveness_history[pid] = [(now, 82.456)]
        result = monitor.get_resident_history(pid, hours=24)
        assert "timestamp" in result[0]
        assert "effectiveness" in result[0]
        assert result[0]["effectiveness"] == 82.46


# ---------------------------------------------------------------------------
# FatigueMonitor.export_alert_report
# ---------------------------------------------------------------------------


class TestExportAlertReport:
    def _make_alert(self, person_id, person_name, severity, created_at, ack=False):
        return FatigueAlert(
            alert_id=f"alert_{created_at.timestamp():.0f}",
            person_id=person_id,
            person_name=person_name,
            severity=severity,
            created_at=created_at,
            effectiveness_score=70.0,
            threshold_violated=77.0,
            message="test",
            acknowledged=ack,
        )

    def test_empty_report(self):
        monitor = FatigueMonitor()
        report = monitor.export_alert_report(
            datetime(2026, 1, 1), datetime(2026, 1, 31)
        )
        assert report["total_alerts"] == 0

    def test_report_structure(self):
        monitor = FatigueMonitor()
        report = monitor.export_alert_report(
            datetime(2026, 1, 1), datetime(2026, 1, 31)
        )
        expected = {
            "start_date",
            "end_date",
            "total_alerts",
            "by_severity",
            "by_person",
            "acknowledged_count",
            "unacknowledged_count",
        }
        assert set(report.keys()) == expected

    def test_filters_by_date_range(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        monitor._alert_history = [
            self._make_alert(pid, "A", AlertSeverity.WARNING, datetime(2026, 1, 10)),
            self._make_alert(pid, "A", AlertSeverity.WARNING, datetime(2026, 2, 10)),
        ]
        report = monitor.export_alert_report(
            datetime(2026, 1, 1), datetime(2026, 1, 31)
        )
        assert report["total_alerts"] == 1

    def test_by_severity(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        monitor._alert_history = [
            self._make_alert(pid, "A", AlertSeverity.WARNING, datetime(2026, 1, 10)),
            self._make_alert(pid, "A", AlertSeverity.CRITICAL, datetime(2026, 1, 11)),
            self._make_alert(pid, "A", AlertSeverity.WARNING, datetime(2026, 1, 12)),
        ]
        report = monitor.export_alert_report(
            datetime(2026, 1, 1), datetime(2026, 1, 31)
        )
        assert report["by_severity"]["warning"] == 2
        assert report["by_severity"]["critical"] == 1

    def test_by_person(self):
        monitor = FatigueMonitor()
        pid1 = uuid4()
        pid2 = uuid4()
        monitor._alert_history = [
            self._make_alert(
                pid1, "Alice", AlertSeverity.WARNING, datetime(2026, 1, 10)
            ),
            self._make_alert(pid2, "Bob", AlertSeverity.WARNING, datetime(2026, 1, 11)),
            self._make_alert(
                pid1, "Alice", AlertSeverity.CRITICAL, datetime(2026, 1, 12)
            ),
        ]
        report = monitor.export_alert_report(
            datetime(2026, 1, 1), datetime(2026, 1, 31)
        )
        assert report["by_person"][str(pid1)]["count"] == 2
        assert report["by_person"][str(pid2)]["count"] == 1

    def test_acknowledged_count(self):
        monitor = FatigueMonitor()
        pid = uuid4()
        monitor._alert_history = [
            self._make_alert(
                pid, "A", AlertSeverity.WARNING, datetime(2026, 1, 10), ack=True
            ),
            self._make_alert(
                pid, "A", AlertSeverity.WARNING, datetime(2026, 1, 11), ack=False
            ),
        ]
        report = monitor.export_alert_report(
            datetime(2026, 1, 1), datetime(2026, 1, 31)
        )
        assert report["acknowledged_count"] == 1
        assert report["unacknowledged_count"] == 1

    def test_dates_in_iso_format(self):
        monitor = FatigueMonitor()
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)
        report = monitor.export_alert_report(start, end)
        assert report["start_date"] == start.isoformat()
        assert report["end_date"] == end.isoformat()
