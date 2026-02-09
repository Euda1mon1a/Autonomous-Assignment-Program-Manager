"""Tests for MTF Types (strongly-typed dataclasses for MTF compliance system)."""

from datetime import date

import pytest

from app.resilience.mtf_types import (
    CascadePrediction,
    CoverageGap,
    MTFComplianceResult,
    MTFViolation,
    PositiveFeedbackRisk,
    ProjectionWithoutSupport,
    StaffingLevel,
    SupportingMetrics,
    SystemHealthState,
    ViolationSeverity,
)


# ==================== ViolationSeverity ====================


class TestViolationSeverity:
    def test_values(self):
        assert ViolationSeverity.CRITICAL.value == "critical"
        assert ViolationSeverity.HIGH.value == "high"
        assert ViolationSeverity.MEDIUM.value == "medium"
        assert ViolationSeverity.LOW.value == "low"

    def test_count(self):
        assert len(ViolationSeverity) == 4


# ==================== MTFViolation ====================


class TestMTFViolation:
    def test_basic(self):
        v = MTFViolation(
            rule_id="ACGME-80HR",
            severity=ViolationSeverity.CRITICAL,
            description="Weekly hours exceed 80",
        )
        assert v.rule_id == "ACGME-80HR"
        assert v.severity == ViolationSeverity.CRITICAL
        assert v.affected_items == []
        assert v.recommendation is None

    def test_with_optional_fields(self):
        v = MTFViolation(
            rule_id="R01",
            severity=ViolationSeverity.LOW,
            description="Minor issue",
            affected_items=["Block 5", "Block 6"],
            recommendation="Adjust schedule",
        )
        assert len(v.affected_items) == 2
        assert v.recommendation == "Adjust schedule"


# ==================== MTFComplianceResult ====================


class TestMTFComplianceResult:
    def test_defaults(self):
        r = MTFComplianceResult(is_compliant=True)
        assert r.is_compliant is True
        assert r.violations == []
        assert r.score == 100.0
        assert r.checked_at is None
        assert r.recommendations == []

    def test_non_compliant(self):
        v = MTFViolation(
            rule_id="R01",
            severity=ViolationSeverity.HIGH,
            description="Test violation",
        )
        r = MTFComplianceResult(
            is_compliant=False,
            violations=[v],
            score=75.0,
            checked_at=date(2026, 1, 15),
        )
        assert r.is_compliant is False
        assert len(r.violations) == 1
        assert r.score == 75.0


# ==================== StaffingLevel ====================


class TestStaffingLevel:
    def test_deficit_calculated(self):
        s = StaffingLevel(role="attending", required=5, available=3)
        assert s.deficit == 2

    def test_no_deficit(self):
        s = StaffingLevel(role="resident", required=4, available=6)
        assert s.deficit == 0

    def test_exact_staffing(self):
        s = StaffingLevel(role="nurse", required=3, available=3)
        assert s.deficit == 0

    def test_zero_available(self):
        s = StaffingLevel(role="attending", required=5, available=0)
        assert s.deficit == 5

    def test_deficit_overridden_by_post_init(self):
        # Even if deficit is passed, post_init recalculates
        s = StaffingLevel(role="attending", required=5, available=3, deficit=99)
        assert s.deficit == 2


# ==================== CoverageGap ====================


class TestCoverageGap:
    def test_gap_calculated(self):
        g = CoverageGap(
            date=date(2026, 1, 15),
            time_of_day="AM",
            rotation="ICU",
            required_staff=3,
            assigned_staff=1,
        )
        assert g.gap_size == 2

    def test_no_gap(self):
        g = CoverageGap(
            date=date(2026, 1, 15),
            time_of_day="PM",
            rotation="Clinic",
            required_staff=2,
            assigned_staff=3,
        )
        assert g.gap_size == 0

    def test_exact_coverage(self):
        g = CoverageGap(
            date=date(2026, 1, 15),
            time_of_day="AM",
            rotation="OR",
            required_staff=2,
            assigned_staff=2,
        )
        assert g.gap_size == 0

    def test_gap_overridden_by_post_init(self):
        g = CoverageGap(
            date=date(2026, 1, 15),
            time_of_day="AM",
            rotation="ICU",
            required_staff=5,
            assigned_staff=2,
            gap_size=99,
        )
        assert g.gap_size == 3


# ==================== SystemHealthState ====================


class TestSystemHealthState:
    def test_basic(self):
        s = SystemHealthState(
            n1_pass=True,
            n2_pass=False,
            coverage_rate=0.95,
            average_allostatic_load=3.5,
            load_shedding_level="NORMAL",
            equilibrium_state="stable",
        )
        assert s.n1_pass is True
        assert s.n2_pass is False
        assert s.overloaded_faculty_count == 0
        assert s.compensation_debt == 0.0
        assert s.volatility_level == "normal"
        assert s.phase_transition_risk == "low"

    def test_to_dict(self):
        s = SystemHealthState(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.98,
            average_allostatic_load=2.0,
            load_shedding_level="NORMAL",
            equilibrium_state="stable",
            overloaded_faculty_count=2,
        )
        d = s.to_dict()
        assert d["n1_pass"] is True
        assert d["coverage_rate"] == 0.98
        assert d["overloaded_faculty_count"] == 2
        assert len(d) == 10

    def test_to_dict_keys(self):
        s = SystemHealthState(
            n1_pass=True,
            n2_pass=True,
            coverage_rate=0.90,
            average_allostatic_load=1.0,
            load_shedding_level="NORMAL",
            equilibrium_state="stable",
        )
        expected_keys = {
            "n1_pass",
            "n2_pass",
            "coverage_rate",
            "average_allostatic_load",
            "overloaded_faculty_count",
            "load_shedding_level",
            "equilibrium_state",
            "compensation_debt",
            "volatility_level",
            "phase_transition_risk",
        }
        assert set(s.to_dict().keys()) == expected_keys


# ==================== CascadePrediction ====================


class TestCascadePrediction:
    def test_defaults(self):
        c = CascadePrediction(days_until_exhaustion=30)
        assert c.cascade_probability == 0.0
        assert c.critical_faculty == []
        assert c.projected_load_increase == 0.0

    def test_to_dict(self):
        c = CascadePrediction(
            days_until_exhaustion=14,
            cascade_probability=0.75,
            critical_faculty=[101, 202],
            projected_load_increase=0.3,
        )
        d = c.to_dict()
        assert d["days_until_exhaustion"] == 14
        assert d["cascade_probability"] == 0.75
        assert len(d["critical_faculty"]) == 2


# ==================== PositiveFeedbackRisk ====================


class TestPositiveFeedbackRisk:
    def test_defaults(self):
        p = PositiveFeedbackRisk(
            risk_type="burnout_cascade",
            confidence=0.85,
            description="Faculty burnout spreading",
        )
        assert p.affected_entities == []
        assert p.mitigation_required is False

    def test_to_dict(self):
        p = PositiveFeedbackRisk(
            risk_type="overwork_spiral",
            confidence=0.9,
            description="Overwork spreading",
            affected_entities=["Dr. A", "Dr. B"],
            mitigation_required=True,
        )
        d = p.to_dict()
        assert d["risk_type"] == "overwork_spiral"
        assert d["mitigation_required"] is True
        assert len(d["affected_entities"]) == 2


# ==================== SupportingMetrics ====================


class TestSupportingMetrics:
    def test_frozen(self):
        sm = SupportingMetrics(
            coverage_rate=0.95,
            n1_pass=True,
            n2_pass=False,
            load_shedding_level="NORMAL",
            average_allostatic_load=2.5,
            equilibrium_state="stable",
            compensation_debt=100.0,
            snapshot_timestamp="2026-01-15T12:00:00",
        )
        with pytest.raises(AttributeError):
            sm.coverage_rate = 0.99  # frozen

    def test_to_dict(self):
        sm = SupportingMetrics(
            coverage_rate=0.90,
            n1_pass=True,
            n2_pass=True,
            load_shedding_level="ELEVATED",
            average_allostatic_load=3.0,
            equilibrium_state="stressed",
            compensation_debt=50.0,
            snapshot_timestamp="2026-02-01T08:00:00",
        )
        d = sm.to_dict()
        assert d["coverage_rate"] == 0.90
        assert d["snapshot_timestamp"] == "2026-02-01T08:00:00"
        assert len(d) == 8

    def test_nullable_fields(self):
        sm = SupportingMetrics(
            coverage_rate=None,
            n1_pass=None,
            n2_pass=None,
            load_shedding_level="UNKNOWN",
            average_allostatic_load=None,
            equilibrium_state="unknown",
            compensation_debt=None,
            snapshot_timestamp="2026-01-01T00:00:00",
        )
        d = sm.to_dict()
        assert d["coverage_rate"] is None
        assert d["n1_pass"] is None


# ==================== ProjectionWithoutSupport ====================


class TestProjectionWithoutSupport:
    def test_defaults(self):
        p = ProjectionWithoutSupport(timeline_days=30)
        assert p.outcomes == []
        assert p.mission_failure_likely is False

    def test_to_dict(self):
        p = ProjectionWithoutSupport(
            timeline_days=14,
            outcomes=["Coverage gaps increase", "Burnout risk rises"],
            mission_failure_likely=True,
        )
        d = p.to_dict()
        assert d["timeline_days"] == 14
        assert len(d["outcomes"]) == 2
        assert d["mission_failure_likely"] is True

    def test_empty_outcomes(self):
        p = ProjectionWithoutSupport(timeline_days=90)
        d = p.to_dict()
        assert d["outcomes"] == []
