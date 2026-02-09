"""Tests for alert rule definitions for monitoring systems."""

from app.core.metrics.alerts import (
    AlertCondition,
    AlertRule,
    AlertRuleBuilder,
    AlertSeverity,
    get_all_alert_rules,
    to_prometheus_rules,
)


# ==================== AlertSeverity enum ====================


class TestAlertSeverity:
    def test_is_str_enum(self):
        assert isinstance(AlertSeverity.INFO, str)

    def test_values(self):
        assert AlertSeverity.INFO == "info"
        assert AlertSeverity.WARNING == "warning"
        assert AlertSeverity.CRITICAL == "critical"

    def test_count(self):
        assert len(AlertSeverity) == 3


# ==================== AlertCondition enum ====================


class TestAlertCondition:
    def test_is_str_enum(self):
        assert isinstance(AlertCondition.THRESHOLD, str)

    def test_values(self):
        assert AlertCondition.THRESHOLD == "threshold"
        assert AlertCondition.ANOMALY == "anomaly"
        assert AlertCondition.RATE_OF_CHANGE == "rate_of_change"
        assert AlertCondition.ABSENCE == "absence"

    def test_count(self):
        assert len(AlertCondition) == 4


# ==================== AlertRule dataclass ====================


class TestAlertRule:
    def test_required_fields(self):
        rule = AlertRule(
            name="TestAlert",
            description="Test",
            severity=AlertSeverity.WARNING,
            condition=AlertCondition.THRESHOLD,
            query="rate(errors[5m]) > 0.1",
        )
        assert rule.name == "TestAlert"
        assert rule.severity == AlertSeverity.WARNING
        assert rule.condition == AlertCondition.THRESHOLD
        assert rule.query == "rate(errors[5m]) > 0.1"

    def test_defaults(self):
        rule = AlertRule(
            name="Test",
            description="Test",
            severity=AlertSeverity.INFO,
            condition=AlertCondition.THRESHOLD,
            query="test",
        )
        assert rule.threshold is None
        assert rule.duration == "5m"
        assert rule.labels == {}
        assert rule.annotations == {}
        assert rule.notification_channels == []

    def test_custom_fields(self):
        rule = AlertRule(
            name="Custom",
            description="Custom alert",
            severity=AlertSeverity.CRITICAL,
            condition=AlertCondition.RATE_OF_CHANGE,
            query="test_query",
            threshold=0.5,
            duration="10m",
            labels={"team": "backend"},
            annotations={"summary": "Alert fired"},
            notification_channels=["slack", "pagerduty"],
        )
        assert rule.threshold == 0.5
        assert rule.duration == "10m"
        assert rule.labels["team"] == "backend"
        assert rule.annotations["summary"] == "Alert fired"
        assert len(rule.notification_channels) == 2


# ==================== AlertRuleBuilder ====================


class TestAlertRuleBuilder:
    def test_init(self):
        builder = AlertRuleBuilder()
        assert builder.rules == []

    def test_build_system_alerts(self):
        builder = AlertRuleBuilder()
        rules = builder.build_system_alerts()
        assert len(rules) == 5
        names = {r.name for r in rules}
        assert "HighErrorRate" in names
        assert "SlowResponseTime" in names
        assert "HighCPUUsage" in names
        assert "LowMemory" in names
        assert "DatabaseConnectionPoolExhaustion" in names

    def test_system_alerts_have_queries(self):
        builder = AlertRuleBuilder()
        for rule in builder.build_system_alerts():
            assert rule.query, f"{rule.name} missing query"

    def test_system_alerts_severities(self):
        builder = AlertRuleBuilder()
        rules = builder.build_system_alerts()
        critical = [r for r in rules if r.severity == AlertSeverity.CRITICAL]
        warning = [r for r in rules if r.severity == AlertSeverity.WARNING]
        assert len(critical) >= 2
        assert len(warning) >= 2

    def test_build_compliance_alerts(self):
        builder = AlertRuleBuilder()
        rules = builder.build_compliance_alerts()
        assert len(rules) == 3
        names = {r.name for r in rules}
        assert "ACGMEViolationDetected" in names
        assert "RepeatedACGMEViolations" in names
        assert "WorkHourThresholdApproaching" in names

    def test_compliance_alerts_all_critical_or_warning(self):
        builder = AlertRuleBuilder()
        for rule in builder.build_compliance_alerts():
            assert rule.severity in (AlertSeverity.CRITICAL, AlertSeverity.WARNING)

    def test_build_security_alerts(self):
        builder = AlertRuleBuilder()
        rules = builder.build_security_alerts()
        assert len(rules) == 4
        names = {r.name for r in rules}
        assert "FailedAuthenticationSpike" in names
        assert "SuspiciousActivityDetected" in names
        assert "RateLimitViolations" in names
        assert "LargeDataExport" in names

    def test_build_performance_alerts(self):
        builder = AlertRuleBuilder()
        rules = builder.build_performance_alerts()
        assert len(rules) == 2
        names = {r.name for r in rules}
        assert "SlowDatabaseQueries" in names
        assert "LowCacheHitRate" in names

    def test_all_rules_have_notification_channels(self):
        builder = AlertRuleBuilder()
        all_rules = (
            builder.build_system_alerts()
            + builder.build_compliance_alerts()
            + builder.build_security_alerts()
            + builder.build_performance_alerts()
        )
        for rule in all_rules:
            assert len(rule.notification_channels) > 0, f"{rule.name} has no channels"

    def test_all_rules_have_labels(self):
        builder = AlertRuleBuilder()
        all_rules = (
            builder.build_system_alerts()
            + builder.build_compliance_alerts()
            + builder.build_security_alerts()
            + builder.build_performance_alerts()
        )
        for rule in all_rules:
            assert "team" in rule.labels, f"{rule.name} missing team label"

    def test_all_rules_have_annotations(self):
        builder = AlertRuleBuilder()
        all_rules = (
            builder.build_system_alerts()
            + builder.build_compliance_alerts()
            + builder.build_security_alerts()
            + builder.build_performance_alerts()
        )
        for rule in all_rules:
            assert "summary" in rule.annotations, f"{rule.name} missing summary"


# ==================== to_prometheus_rules ====================


class TestToPrometheusRules:
    def test_basic_structure(self):
        rules = [
            AlertRule(
                name="Test",
                description="Test",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query="test_query",
            )
        ]
        result = to_prometheus_rules(rules)
        assert "groups" in result
        assert len(result["groups"]) == 1

    def test_groups_by_severity(self):
        rules = [
            AlertRule(
                name="A",
                description="A",
                severity=AlertSeverity.WARNING,
                condition=AlertCondition.THRESHOLD,
                query="a",
            ),
            AlertRule(
                name="B",
                description="B",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.THRESHOLD,
                query="b",
            ),
        ]
        result = to_prometheus_rules(rules)
        assert len(result["groups"]) == 2
        group_names = {g["name"] for g in result["groups"]}
        assert "warning_alerts" in group_names
        assert "critical_alerts" in group_names

    def test_rule_format(self):
        rules = [
            AlertRule(
                name="TestAlert",
                description="Test",
                severity=AlertSeverity.CRITICAL,
                condition=AlertCondition.THRESHOLD,
                query="rate(errors[5m]) > 0.1",
                duration="10m",
                labels={"team": "backend"},
                annotations={"summary": "Error rate high"},
            )
        ]
        result = to_prometheus_rules(rules)
        prom_rule = result["groups"][0]["rules"][0]
        assert prom_rule["alert"] == "TestAlert"
        assert prom_rule["expr"] == "rate(errors[5m]) > 0.1"
        assert prom_rule["for"] == "10m"
        assert prom_rule["labels"]["severity"] == "critical"
        assert prom_rule["labels"]["team"] == "backend"
        assert prom_rule["annotations"]["summary"] == "Error rate high"

    def test_empty_rules(self):
        result = to_prometheus_rules([])
        assert result["groups"] == []


# ==================== get_all_alert_rules ====================


class TestGetAllAlertRules:
    def test_returns_list(self):
        rules = get_all_alert_rules()
        assert isinstance(rules, list)

    def test_returns_all_rules(self):
        rules = get_all_alert_rules()
        # 5 system + 3 compliance + 4 security + 2 performance = 14
        assert len(rules) == 14

    def test_all_are_alert_rules(self):
        for rule in get_all_alert_rules():
            assert isinstance(rule, AlertRule)

    def test_all_unique_names(self):
        rules = get_all_alert_rules()
        names = [r.name for r in rules]
        assert len(names) == len(set(names))
