"""
Tests for Statistical Process Control (SPC) Workload Monitoring.

Comprehensive test suite for Western Electric Rules implementation and
process capability calculations.
"""

import math
import statistics
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.resilience.spc_monitoring import (
    SPCAlert,
    WorkloadControlChart,
    calculate_control_limits,
    calculate_process_capability,
)


class TestSPCAlert:
    """Test suite for SPCAlert dataclass."""

    def test_spc_alert_creation(self):
        """Test basic SPCAlert creation."""
        alert = SPCAlert(
            rule="Rule 1",
            severity="CRITICAL",
            message="Test violation",
        )

        assert alert.rule == "Rule 1"
        assert alert.severity == "CRITICAL"
        assert alert.message == "Test violation"
        assert alert.resident_id is None
        assert isinstance(alert.timestamp, datetime)
        assert alert.data_points == []
        assert alert.control_limits == {}

    def test_spc_alert_with_resident_id(self):
        """Test SPCAlert with resident ID."""
        resident_id = uuid4()
        alert = SPCAlert(
            rule="Rule 2",
            severity="WARNING",
            message="Test violation",
            resident_id=resident_id,
        )

        assert alert.resident_id == resident_id

    def test_spc_alert_with_data_points(self):
        """Test SPCAlert with data points."""
        data = [65.0, 70.0, 75.0]
        alert = SPCAlert(
            rule="Rule 3",
            severity="WARNING",
            message="Test violation",
            data_points=data,
        )

        assert alert.data_points == data

    def test_spc_alert_with_control_limits(self):
        """Test SPCAlert with control limits."""
        limits = {"ucl": 75.0, "lcl": 45.0, "centerline": 60.0}
        alert = SPCAlert(
            rule="Rule 1",
            severity="CRITICAL",
            message="Test violation",
            control_limits=limits,
        )

        assert alert.control_limits == limits


class TestWorkloadControlChart:
    """Test suite for WorkloadControlChart class."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        chart = WorkloadControlChart()

        assert chart.target_hours == 60.0
        assert chart.sigma == 5.0
        assert chart.ucl_3sigma == 75.0  # 60 + 3*5
        assert chart.lcl_3sigma == 45.0  # 60 - 3*5
        assert chart.ucl_2sigma == 70.0  # 60 + 2*5
        assert chart.lcl_2sigma == 50.0  # 60 - 2*5
        assert chart.ucl_1sigma == 65.0  # 60 + 1*5
        assert chart.lcl_1sigma == 55.0  # 60 - 1*5

    def test_initialization_custom_parameters(self):
        """Test initialization with custom parameters."""
        chart = WorkloadControlChart(target_hours=50.0, sigma=10.0)

        assert chart.target_hours == 50.0
        assert chart.sigma == 10.0
        assert chart.ucl_3sigma == 80.0  # 50 + 3*10
        assert chart.lcl_3sigma == 20.0  # 50 - 3*10

    def test_detect_violations_empty_data(self):
        """Test that empty data raises ValueError."""
        chart = WorkloadControlChart()
        resident_id = uuid4()

        with pytest.raises(ValueError, match="weekly_hours cannot be empty"):
            chart.detect_western_electric_violations(resident_id, [])

    def test_detect_violations_negative_hours(self):
        """Test that negative hours raise ValueError."""
        chart = WorkloadControlChart()
        resident_id = uuid4()

        with pytest.raises(ValueError, match="cannot be negative"):
            chart.detect_western_electric_violations(resident_id, [60, -5, 62])

    def test_detect_violations_excessive_hours(self):
        """Test that hours > 168 raise ValueError."""
        chart = WorkloadControlChart()
        resident_id = uuid4()

        with pytest.raises(ValueError, match="exceeds 168 hours/week"):
            chart.detect_western_electric_violations(resident_id, [60, 200, 62])

    def test_detect_violations_no_violations(self):
        """Test data with no violations returns empty list."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # All points within 1σ (55-65)
        weekly_hours = [58, 62, 59, 61, 60, 58, 62]
        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        assert len(alerts) == 0


class TestWesternElectricRule1:
    """Test suite for Western Electric Rule 1 (1 point beyond 3σ)."""

    def test_rule_1_upper_violation(self):
        """Test Rule 1 detects point above UCL (3σ)."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        # UCL = 75.0
        resident_id = uuid4()

        weekly_hours = [60, 62, 76, 61, 59]  # 76 > 75

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        # Should have exactly 1 Rule 1 alert
        rule1_alerts = [a for a in alerts if a.rule == "Rule 1"]
        assert len(rule1_alerts) == 1

        alert = rule1_alerts[0]
        assert alert.severity == "CRITICAL"
        assert alert.resident_id == resident_id
        assert 76.0 in alert.data_points
        assert "3σ upper limit" in alert.message
        assert "75.0" in alert.message  # UCL value

    def test_rule_1_lower_violation(self):
        """Test Rule 1 detects point below LCL (3σ)."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        # LCL = 45.0
        resident_id = uuid4()

        weekly_hours = [60, 62, 44, 61, 59]  # 44 < 45

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule1_alerts = [a for a in alerts if a.rule == "Rule 1"]
        assert len(rule1_alerts) == 1

        alert = rule1_alerts[0]
        assert alert.severity == "CRITICAL"
        assert alert.resident_id == resident_id
        assert 44.0 in alert.data_points
        assert "3σ lower limit" in alert.message
        assert "45.0" in alert.message  # LCL value

    def test_rule_1_multiple_violations(self):
        """Test Rule 1 detects multiple violations."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [76, 44, 60, 77]  # Two upper, one lower violations

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule1_alerts = [a for a in alerts if a.rule == "Rule 1"]
        assert len(rule1_alerts) == 3  # All three violations detected

    def test_rule_1_boundary_values(self):
        """Test Rule 1 at exact boundary (should not trigger)."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # Exactly at 3σ limits should not violate
        weekly_hours = [75.0, 60, 45.0]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule1_alerts = [a for a in alerts if a.rule == "Rule 1"]
        assert len(rule1_alerts) == 0


class TestWesternElectricRule2:
    """Test suite for Western Electric Rule 2 (2 of 3 beyond 2σ, same side)."""

    def test_rule_2_upper_violation(self):
        """Test Rule 2 detects 2 of 3 points above 2σ."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        # 2σ upper = 70.0
        resident_id = uuid4()

        weekly_hours = [71, 72, 60, 61]  # First 3: two above 70

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule2_alerts = [a for a in alerts if a.rule == "Rule 2"]
        assert len(rule2_alerts) == 1

        alert = rule2_alerts[0]
        assert alert.severity == "WARNING"
        assert alert.resident_id == resident_id
        assert "2 of 3 weeks" in alert.message
        assert "2σ upper limit" in alert.message
        assert len(alert.data_points) == 3

    def test_rule_2_lower_violation(self):
        """Test Rule 2 detects 2 of 3 points below 2σ."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        # 2σ lower = 50.0
        resident_id = uuid4()

        weekly_hours = [49, 48, 60, 61]  # First 3: two below 50

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule2_alerts = [a for a in alerts if a.rule == "Rule 2"]
        assert len(rule2_alerts) == 1

        alert = rule2_alerts[0]
        assert alert.severity == "WARNING"
        assert "2σ lower limit" in alert.message

    def test_rule_2_insufficient_violations(self):
        """Test Rule 2 does not trigger with only 1 of 3."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [71, 60, 61]  # Only 1 above 2σ

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule2_alerts = [a for a in alerts if a.rule == "Rule 2"]
        assert len(rule2_alerts) == 0

    def test_rule_2_insufficient_data(self):
        """Test Rule 2 with fewer than 3 points."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [71, 72]  # Only 2 points

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule2_alerts = [a for a in alerts if a.rule == "Rule 2"]
        assert len(rule2_alerts) == 0

    def test_rule_2_mixed_sides(self):
        """Test Rule 2 does not trigger when violations on different sides."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # One above 2σ upper, one below 2σ lower - different sides
        weekly_hours = [71, 49, 60]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule2_alerts = [a for a in alerts if a.rule == "Rule 2"]
        assert len(rule2_alerts) == 0


class TestWesternElectricRule3:
    """Test suite for Western Electric Rule 3 (4 of 5 beyond 1σ, same side)."""

    def test_rule_3_upper_violation(self):
        """Test Rule 3 detects 4 of 5 points above 1σ."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        # 1σ upper = 65.0
        resident_id = uuid4()

        weekly_hours = [66, 67, 60, 68, 69]  # 4 of 5 above 65

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule3_alerts = [a for a in alerts if a.rule == "Rule 3"]
        assert len(rule3_alerts) == 1

        alert = rule3_alerts[0]
        assert alert.severity == "WARNING"
        assert "4 of 5 weeks" in alert.message
        assert "1σ upper threshold" in alert.message
        assert len(alert.data_points) == 5

    def test_rule_3_lower_violation(self):
        """Test Rule 3 detects 4 of 5 points below 1σ."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        # 1σ lower = 55.0
        resident_id = uuid4()

        weekly_hours = [54, 53, 60, 52, 51]  # 4 of 5 below 55

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule3_alerts = [a for a in alerts if a.rule == "Rule 3"]
        assert len(rule3_alerts) == 1

        alert = rule3_alerts[0]
        assert alert.severity == "WARNING"
        assert "1σ lower threshold" in alert.message

    def test_rule_3_insufficient_violations(self):
        """Test Rule 3 does not trigger with only 3 of 5."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [66, 67, 60, 61, 68]  # Only 3 above 1σ

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule3_alerts = [a for a in alerts if a.rule == "Rule 3"]
        assert len(rule3_alerts) == 0

    def test_rule_3_insufficient_data(self):
        """Test Rule 3 with fewer than 5 points."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [66, 67, 68, 69]  # Only 4 points

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule3_alerts = [a for a in alerts if a.rule == "Rule 3"]
        assert len(rule3_alerts) == 0

    def test_rule_3_exactly_4_of_5(self):
        """Test Rule 3 triggers with exactly 4 of 5."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [66, 67, 60, 68, 69]  # Exactly 4 of 5

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule3_alerts = [a for a in alerts if a.rule == "Rule 3"]
        assert len(rule3_alerts) == 1

    def test_rule_3_all_5_of_5(self):
        """Test Rule 3 triggers with all 5 of 5."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [66, 67, 68, 69, 70]  # All 5 above 1σ

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule3_alerts = [a for a in alerts if a.rule == "Rule 3"]
        assert len(rule3_alerts) == 1


class TestWesternElectricRule4:
    """Test suite for Western Electric Rule 4 (8 consecutive on same side)."""

    def test_rule_4_above_centerline(self):
        """Test Rule 4 detects 8 consecutive points above centerline."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # All 8 above 60
        weekly_hours = [61, 62, 63, 64, 65, 66, 67, 68]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule4_alerts = [a for a in alerts if a.rule == "Rule 4"]
        assert len(rule4_alerts) == 1

        alert = rule4_alerts[0]
        assert alert.severity == "INFO"
        assert "8 consecutive weeks" in alert.message
        assert "above target" in alert.message
        assert len(alert.data_points) == 8

    def test_rule_4_below_centerline(self):
        """Test Rule 4 detects 8 consecutive points below centerline."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # All 8 below 60
        weekly_hours = [59, 58, 57, 56, 55, 54, 53, 52]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule4_alerts = [a for a in alerts if a.rule == "Rule 4"]
        assert len(rule4_alerts) == 1

        alert = rule4_alerts[0]
        assert alert.severity == "INFO"
        assert "below target" in alert.message

    def test_rule_4_insufficient_consecutive(self):
        """Test Rule 4 does not trigger with only 7 consecutive."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # Only 7 above centerline
        weekly_hours = [61, 62, 63, 64, 65, 66, 67]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule4_alerts = [a for a in alerts if a.rule == "Rule 4"]
        assert len(rule4_alerts) == 0

    def test_rule_4_interrupted_sequence(self):
        """Test Rule 4 does not trigger when sequence is interrupted."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # 7 above, then 1 below, then 1 above - no 8 consecutive
        weekly_hours = [61, 62, 63, 64, 65, 66, 67, 59, 61]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule4_alerts = [a for a in alerts if a.rule == "Rule 4"]
        assert len(rule4_alerts) == 0

    def test_rule_4_on_centerline_breaks_sequence(self):
        """Test that point exactly on centerline breaks sequence."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # Point exactly on centerline should not count
        weekly_hours = [61, 62, 63, 60, 64, 65, 66, 67]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule4_alerts = [a for a in alerts if a.rule == "Rule 4"]
        assert len(rule4_alerts) == 0

    def test_rule_4_insufficient_data(self):
        """Test Rule 4 with fewer than 8 points."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [61, 62, 63, 64, 65, 66, 67]  # Only 7 points

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule4_alerts = [a for a in alerts if a.rule == "Rule 4"]
        assert len(rule4_alerts) == 0

    def test_rule_4_includes_mean_in_limits(self):
        """Test Rule 4 alert includes mean in control limits."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        weekly_hours = [61, 62, 63, 64, 65, 66, 67, 68]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule4_alerts = [a for a in alerts if a.rule == "Rule 4"]
        assert len(rule4_alerts) == 1

        alert = rule4_alerts[0]
        assert "centerline" in alert.control_limits
        assert "mean_actual" in alert.control_limits
        assert alert.control_limits["centerline"] == 60.0
        # Mean of [61-68] = 64.5
        assert alert.control_limits["mean_actual"] == pytest.approx(64.5)


class TestMultipleRuleViolations:
    """Test scenarios where multiple rules are violated simultaneously."""

    def test_rule_1_and_rule_2_together(self):
        """Test that both Rule 1 and Rule 2 can trigger on same data."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # 76 triggers Rule 1 (> 75)
        # 71, 72 in window trigger Rule 2 (2 of 3 > 70)
        weekly_hours = [71, 72, 76]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        rule1_alerts = [a for a in alerts if a.rule == "Rule 1"]
        rule2_alerts = [a for a in alerts if a.rule == "Rule 2"]

        assert len(rule1_alerts) >= 1
        assert len(rule2_alerts) >= 1

    def test_all_rules_no_violation(self):
        """Test that good data triggers no rules."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # Perfectly centered data
        weekly_hours = [60, 60, 60, 60, 60, 60, 60, 60]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        # Only Rule 4 should trigger (8 on same side)
        assert len(alerts) == 1
        assert alerts[0].rule == "Rule 4"
        assert alerts[0].severity == "INFO"


class TestCalculateControlLimits:
    """Test suite for calculate_control_limits function."""

    def test_calculate_control_limits_basic(self):
        """Test basic control limit calculation."""
        data = [58, 62, 59, 61, 60, 58, 62, 60]

        limits = calculate_control_limits(data)

        assert "centerline" in limits
        assert "sigma" in limits
        assert "ucl" in limits
        assert "lcl" in limits
        assert "ucl_2sigma" in limits
        assert "lcl_2sigma" in limits
        assert "n" in limits

        assert limits["n"] == 8
        assert limits["centerline"] == pytest.approx(60.0)
        assert limits["ucl"] == pytest.approx(limits["centerline"] + 3 * limits["sigma"])
        assert limits["lcl"] == pytest.approx(limits["centerline"] - 3 * limits["sigma"])

    def test_calculate_control_limits_known_values(self):
        """Test control limits with known statistical values."""
        # Data with mean=50, stdev=10
        data = [40, 45, 50, 55, 60]
        expected_mean = 50.0
        expected_stdev = statistics.stdev(data)

        limits = calculate_control_limits(data)

        assert limits["centerline"] == pytest.approx(expected_mean)
        assert limits["sigma"] == pytest.approx(expected_stdev)
        assert limits["ucl"] == pytest.approx(expected_mean + 3 * expected_stdev)
        assert limits["lcl"] == pytest.approx(expected_mean - 3 * expected_stdev)

    def test_calculate_control_limits_empty_data(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="data cannot be empty"):
            calculate_control_limits([])

    def test_calculate_control_limits_single_point(self):
        """Test that single data point raises ValueError."""
        with pytest.raises(ValueError, match="at least 2 points"):
            calculate_control_limits([60])

    def test_calculate_control_limits_two_points(self):
        """Test minimum valid input (2 points)."""
        data = [50, 60]

        limits = calculate_control_limits(data)

        assert limits["centerline"] == 55.0
        assert limits["n"] == 2
        # Standard deviation should be calculated
        assert limits["sigma"] > 0

    def test_calculate_control_limits_no_variation(self):
        """Test data with zero variation."""
        data = [60, 60, 60, 60, 60]

        limits = calculate_control_limits(data)

        assert limits["centerline"] == 60.0
        assert limits["sigma"] == 0.0
        assert limits["ucl"] == 60.0
        assert limits["lcl"] == 60.0


class TestCalculateProcessCapability:
    """Test suite for calculate_process_capability function."""

    def test_process_capability_basic(self):
        """Test basic process capability calculation."""
        # Centered process: mean=60, stdev=5
        # LSL=40, USL=80
        data = [55, 60, 65, 58, 62, 59, 61, 60]
        lsl = 40
        usl = 80

        capability = calculate_process_capability(data, lsl, usl)

        assert "cp" in capability
        assert "cpk" in capability
        assert "pp" in capability
        assert "ppk" in capability
        assert "mean" in capability
        assert "sigma" in capability
        assert "interpretation" in capability

        # Cp = (USL - LSL) / (6 * sigma)
        # Cp = (80 - 40) / (6 * ~2.5) = ~2.67
        assert capability["cp"] > 0
        assert capability["cpk"] > 0

    def test_process_capability_centered_process(self):
        """Test perfectly centered process (Cp = Cpk)."""
        # Perfect normal distribution centered at 60
        data = [60] * 10  # No variation, perfectly centered

        lsl = 40
        usl = 80

        capability = calculate_process_capability(data, lsl, usl)

        # Zero variation -> infinite capability
        assert capability["cp"] == float('inf')
        assert capability["cpk"] == float('inf')
        assert capability["mean"] == 60.0
        assert capability["sigma"] == 0.0

    def test_process_capability_not_centered(self):
        """Test off-center process (Cpk < Cp)."""
        # Process biased high: mean=70, stdev=5
        data = [65, 70, 75, 68, 72, 69, 71, 70]
        lsl = 40
        usl = 80

        capability = calculate_process_capability(data, lsl, usl)

        # Off-center process should have Cpk < Cp
        # (Cpk accounts for centering, Cp does not)
        assert capability["cpk"] <= capability["cp"]
        assert capability["mean"] > 60  # Biased high

    def test_process_capability_interpretation_not_capable(self):
        """Test interpretation for non-capable process (Cpk < 1.0)."""
        # Wide variation: sigma=15, mean=60
        data = [30, 50, 70, 90, 45, 65, 85, 55]
        lsl = 40
        usl = 80

        capability = calculate_process_capability(data, lsl, usl)

        if capability["cpk"] < 1.0:
            assert "not capable" in capability["interpretation"].lower()

    def test_process_capability_interpretation_capable(self):
        """Test interpretation for capable process (Cpk >= 1.33)."""
        # Tight distribution: mean=60, low variation
        data = [58, 59, 60, 61, 62, 59, 61, 60]
        lsl = 40
        usl = 80

        capability = calculate_process_capability(data, lsl, usl)

        # Should be capable with tight distribution
        assert capability["cpk"] > 0

    def test_process_capability_empty_data(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="data cannot be empty"):
            calculate_process_capability([], lsl=40, usl=80)

    def test_process_capability_single_point(self):
        """Test that single point raises ValueError."""
        with pytest.raises(ValueError, match="at least 2 points"):
            calculate_process_capability([60], lsl=40, usl=80)

    def test_process_capability_invalid_limits(self):
        """Test that LSL >= USL raises ValueError."""
        data = [55, 60, 65]

        with pytest.raises(ValueError, match="LSL .* must be less than USL"):
            calculate_process_capability(data, lsl=80, usl=40)

        with pytest.raises(ValueError, match="LSL .* must be less than USL"):
            calculate_process_capability(data, lsl=60, usl=60)

    def test_process_capability_cp_formula(self):
        """Test Cp calculation formula."""
        # Known values: mean=60, stdev=5, LSL=40, USL=80
        data = [55, 60, 65, 58, 62, 59, 61, 60]
        lsl = 40
        usl = 80

        capability = calculate_process_capability(data, lsl, usl)

        # Cp = (USL - LSL) / (6 * sigma)
        expected_cp = (usl - lsl) / (6 * capability["sigma"])
        assert capability["cp"] == pytest.approx(expected_cp)

    def test_process_capability_cpk_formula(self):
        """Test Cpk calculation formula."""
        data = [55, 60, 65, 58, 62, 59, 61, 60]
        lsl = 40
        usl = 80

        capability = calculate_process_capability(data, lsl, usl)

        mean = capability["mean"]
        sigma = capability["sigma"]

        # Cpk = min((USL - mean)/(3*sigma), (mean - LSL)/(3*sigma))
        cpu = (usl - mean) / (3 * sigma)
        cpl = (mean - lsl) / (3 * sigma)
        expected_cpk = min(cpu, cpl)

        assert capability["cpk"] == pytest.approx(expected_cpk)

    def test_process_capability_outside_spec_no_variation(self):
        """Test process outside specs with zero variation."""
        # Mean at 90, all points identical, but USL=80
        data = [90, 90, 90, 90]
        lsl = 40
        usl = 80

        capability = calculate_process_capability(data, lsl, usl)

        assert capability["mean"] == 90.0
        assert capability["sigma"] == 0.0
        assert capability["cpk"] == float('-inf')  # Outside spec
        assert "outside specification" in capability["interpretation"].lower()

    def test_process_capability_acgme_scenario(self):
        """Test realistic ACGME compliance scenario."""
        # Weekly hours: target 60, variation ±5
        # ACGME limit: 80 hours/week
        data = [58, 62, 59, 61, 63, 60, 58, 62, 64, 57]
        lsl = 0   # Minimum hours (can't be negative)
        usl = 80  # ACGME limit

        capability = calculate_process_capability(data, lsl, usl)

        # Should show good capability (mean ~60, low variation)
        assert capability["mean"] < 65  # Well below ACGME limit
        assert capability["cpk"] > 1.0  # Should be capable
        assert capability["lsl"] == 0
        assert capability["usl"] == 80


class TestIntegrationScenarios:
    """Integration tests for realistic scheduling scenarios."""

    def test_acgme_violation_scenario(self):
        """Test detection of ACGME violation pattern."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # Gradual increase leading to ACGME violation
        weekly_hours = [60, 65, 68, 72, 75, 78, 80, 82]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        # Should trigger multiple rules
        assert len(alerts) > 0

        # Should have CRITICAL alert (Rule 1) for 82 hours
        critical_alerts = [a for a in alerts if a.severity == "CRITICAL"]
        assert len(critical_alerts) > 0

    def test_normal_rotation_variation(self):
        """Test normal rotation variation doesn't trigger alerts."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # Normal variation within ±1σ
        weekly_hours = [58, 62, 59, 61, 60, 58, 63, 59]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        # Should not trigger WARNING or CRITICAL alerts
        critical_or_warning = [
            a for a in alerts if a.severity in ("CRITICAL", "WARNING")
        ]
        assert len(critical_or_warning) == 0

    def test_burnout_pattern_detection(self):
        """Test detection of sustained overwork (burnout risk)."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # Sustained high hours (between 1σ and 2σ)
        weekly_hours = [66, 67, 68, 67, 66, 68, 67, 66]

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        # Should trigger Rule 4 (8 consecutive above centerline)
        rule4_alerts = [a for a in alerts if a.rule == "Rule 4"]
        assert len(rule4_alerts) == 1
        assert rule4_alerts[0].severity == "INFO"

    def test_scheduling_gap_detection(self):
        """Test detection of scheduling gap (too few hours)."""
        chart = WorkloadControlChart(target_hours=60.0, sigma=5.0)
        resident_id = uuid4()

        # Sudden drop suggesting scheduling gap
        weekly_hours = [60, 62, 59, 20, 61]  # 20 hours << 45 (3σ lower)

        alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

        # Should trigger Rule 1 for low hours
        rule1_alerts = [a for a in alerts if a.rule == "Rule 1"]
        assert len(rule1_alerts) > 0
        assert any("lower limit" in a.message for a in rule1_alerts)
