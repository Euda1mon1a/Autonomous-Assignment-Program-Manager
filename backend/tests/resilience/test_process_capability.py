"""
Tests for Six Sigma process capability metrics.

Tests the ScheduleCapabilityAnalyzer class and related functionality
for measuring schedule quality using Cp, Cpk, Pp, Ppk, and Cpm indices.
"""

import math
import statistics

import pytest

from app.resilience.process_capability import (
    ProcessCapabilityReport,
    ScheduleCapabilityAnalyzer,
)


class TestProcessCapabilityReport:
    """Test ProcessCapabilityReport dataclass."""

    def test_report_creation(self):
        """Test creating a capability report."""
        report = ProcessCapabilityReport(
            cp=1.5,
            cpk=1.4,
            pp=1.5,
            ppk=1.4,
            cpm=1.3,
            capability_status="CAPABLE",
            sigma_level=4.2,
            sample_size=50,
            mean=65.0,
            std_dev=5.0,
            lsl=40.0,
            usl=80.0,
            target=60.0,
        )

        assert report.cp == 1.5
        assert report.cpk == 1.4
        assert report.capability_status == "CAPABLE"
        assert report.sigma_level == 4.2
        assert report.target == 60.0

    def test_report_without_target(self):
        """Test creating a report without target value."""
        report = ProcessCapabilityReport(
            cp=1.5,
            cpk=1.4,
            pp=1.5,
            ppk=1.4,
            cpm=1.3,
            capability_status="CAPABLE",
            sigma_level=4.2,
            sample_size=50,
            mean=65.0,
            std_dev=5.0,
            lsl=40.0,
            usl=80.0,
        )

        assert report.target is None


class TestScheduleCapabilityAnalyzer:
    """Test ScheduleCapabilityAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a capability analyzer instance."""
        return ScheduleCapabilityAnalyzer(min_sample_size=30)

    @pytest.fixture
    def centered_data(self):
        """Well-centered data (mean=60, σ≈5, within 40-80)."""
        return [
            62,
            58,
            65,
            55,
            68,
            57,
            63,
            61,
            59,
            64,
            60,
            62,
            58,
            66,
            54,
            67,
            59,
            61,
            63,
            58,
            64,
            60,
            57,
            65,
            62,
            59,
            61,
            63,
            58,
            66,
            60,
            62,
            64,
            58,
            61,
            59,
            63,
            65,
            57,
            60,
        ]

    @pytest.fixture
    def off_center_data(self):
        """Off-center data (mean≈70, closer to USL)."""
        return [
            72,
            68,
            75,
            65,
            78,
            67,
            73,
            71,
            69,
            74,
            70,
            72,
            68,
            76,
            64,
            77,
            69,
            71,
            73,
            68,
            74,
            70,
            67,
            75,
            72,
            69,
            71,
            73,
            68,
            76,
        ]

    @pytest.fixture
    def high_variation_data(self):
        """High variation data (wide spread)."""
        return [
            45,
            75,
            50,
            70,
            48,
            72,
            52,
            68,
            55,
            65,
            47,
            73,
            51,
            69,
            49,
            71,
            53,
            67,
            54,
            66,
            46,
            74,
            50,
            70,
            48,
            72,
            52,
            68,
            56,
            64,
        ]


class TestCpCalculation:
    """Test Cp (process capability) calculation."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer()

    def test_cp_perfect_process(self, analyzer):
        """Test Cp with perfectly controlled process (σ=1, range=40)."""
        # If σ=1 and range=40, then Cp = 40/(6*1) = 6.67
        data = [60.0] * 10  # Will have σ close to 0, but need variation
        data = [59, 60, 61, 60, 60, 59, 60, 61, 60, 60]  # Small variation

        cp = analyzer.calculate_cp(data, lsl=40.0, usl=80.0)

        # With small variation, Cp should be very high
        assert cp > 2.0

    def test_cp_normal_process(self, analyzer, centered_data):
        """Test Cp with normal process variation."""
        cp = analyzer.calculate_cp(centered_data, lsl=40.0, usl=80.0)

        # For well-controlled process, expect Cp > 1.0
        assert cp > 1.0
        assert cp < 5.0  # Reasonable upper bound

    def test_cp_high_variation(self, analyzer, high_variation_data):
        """Test Cp with high variation process."""
        cp = analyzer.calculate_cp(high_variation_data, lsl=40.0, usl=80.0)

        # High variation means lower Cp
        assert cp < 2.0

    def test_cp_formula_validation(self, analyzer):
        """Test Cp formula with known values."""
        # Data with known statistics
        # mean=60, σ=5, LSL=40, USL=80
        # Cp = (80-40)/(6*5) = 40/30 = 1.333
        data = [60 + x for x in [-5, -3, -1, 0, 1, 3, 5]]
        data.extend([60 + x for x in [-5, -3, -1, 0, 1, 3, 5]])  # Double it

        std_dev = statistics.stdev(data)
        expected_cp = 40 / (6 * std_dev)

        cp = analyzer.calculate_cp(data, lsl=40.0, usl=80.0)

        assert abs(cp - expected_cp) < 0.01

    def test_cp_empty_data(self, analyzer):
        """Test Cp raises error with empty data."""
        with pytest.raises(ValueError, match="empty data"):
            analyzer.calculate_cp([], lsl=40.0, usl=80.0)

    def test_cp_single_sample(self, analyzer):
        """Test Cp raises error with single sample."""
        with pytest.raises(ValueError, match="at least 2 samples"):
            analyzer.calculate_cp([60.0], lsl=40.0, usl=80.0)

    def test_cp_zero_variance(self, analyzer):
        """Test Cp with zero variance (constant data)."""
        data = [60.0] * 10

        cp = analyzer.calculate_cp(data, lsl=40.0, usl=80.0)

        # Zero variance → infinite capability (theoretically)
        assert math.isinf(cp)


class TestCpkCalculation:
    """Test Cpk (centered process capability) calculation."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer()

    def test_cpk_centered_process(self, analyzer, centered_data):
        """Test Cpk with well-centered process."""
        cpk = analyzer.calculate_cpk(centered_data, lsl=40.0, usl=80.0)

        # Well-centered process should have Cpk close to Cp
        cp = analyzer.calculate_cp(centered_data, lsl=40.0, usl=80.0)

        assert cpk > 0.9 * cp  # Cpk should be close to Cp
        assert cpk <= cp  # Cpk can never exceed Cp

    def test_cpk_off_center_high(self, analyzer, off_center_data):
        """Test Cpk with process shifted toward USL."""
        cpk = analyzer.calculate_cpk(off_center_data, lsl=40.0, usl=80.0)
        cp = analyzer.calculate_cp(off_center_data, lsl=40.0, usl=80.0)

        # Off-center process: Cpk should be noticeably less than Cp
        assert cpk < 0.85 * cp

    def test_cpk_off_center_low(self, analyzer):
        """Test Cpk with process shifted toward LSL."""
        # Mean around 50 (closer to LSL=40)
        data = [50, 48, 52, 49, 51, 47, 53, 50, 49, 51] * 3

        cpk = analyzer.calculate_cpk(data, lsl=40.0, usl=80.0)
        cp = analyzer.calculate_cp(data, lsl=40.0, usl=80.0)

        # Off-center toward LSL
        assert cpk < cp

    def test_cpk_formula_validation(self, analyzer):
        """Test Cpk formula with known values."""
        # Create data: mean=65, σ=5
        # LSL=40, USL=80
        # CPU = (80-65)/(3*5) = 15/15 = 1.0
        # CPL = (65-40)/(3*5) = 25/15 = 1.667
        # Cpk = min(1.0, 1.667) = 1.0
        data = [65 + x for x in [-5, -3, -1, 0, 1, 3, 5]]
        data.extend([65 + x for x in [-5, -3, -1, 0, 1, 3, 5]])

        cpk = analyzer.calculate_cpk(data, lsl=40.0, usl=80.0)

        # Should be approximately 1.0 (limited by upper bound)
        assert 0.8 < cpk < 1.2

    def test_cpk_outside_specs(self, analyzer):
        """Test Cpk when mean is outside specifications."""
        # Mean at 85 (above USL=80)
        data = [85, 84, 86, 83, 87, 85, 84, 86, 85, 84]

        cpk = analyzer.calculate_cpk(data, lsl=40.0, usl=80.0)

        # Process outside specs → negative or very low Cpk
        assert cpk < 0.5

    def test_cpk_empty_data(self, analyzer):
        """Test Cpk raises error with empty data."""
        with pytest.raises(ValueError, match="empty data"):
            analyzer.calculate_cpk([], lsl=40.0, usl=80.0)

    def test_cpk_zero_variance_inside_specs(self, analyzer):
        """Test Cpk with zero variance, mean inside specs."""
        data = [60.0] * 10

        cpk = analyzer.calculate_cpk(data, lsl=40.0, usl=80.0)

        # Perfect centering, no variation
        assert math.isinf(cpk)

    def test_cpk_zero_variance_outside_specs(self, analyzer):
        """Test Cpk with zero variance, mean outside specs."""
        data = [85.0] * 10  # Above USL

        cpk = analyzer.calculate_cpk(data, lsl=40.0, usl=80.0)

        # Outside specs with no variation → completely incapable
        assert cpk == 0.0


class TestPpAndPpkCalculation:
    """Test Pp and Ppk (process performance) calculation."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer()

    def test_pp_equals_cp(self, analyzer, centered_data):
        """Test that Pp equals Cp for single time series."""
        pp = analyzer.calculate_pp(centered_data, lsl=40.0, usl=80.0)
        cp = analyzer.calculate_cp(centered_data, lsl=40.0, usl=80.0)

        # For our implementation, Pp = Cp
        assert pp == cp

    def test_ppk_equals_cpk(self, analyzer, centered_data):
        """Test that Ppk equals Cpk for single time series."""
        ppk = analyzer.calculate_ppk(centered_data, lsl=40.0, usl=80.0)
        cpk = analyzer.calculate_cpk(centered_data, lsl=40.0, usl=80.0)

        # For our implementation, Ppk = Cpk
        assert ppk == cpk


class TestCpmCalculation:
    """Test Cpm (Taguchi capability) calculation."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer()

    def test_cpm_on_target(self, analyzer):
        """Test Cpm when process is centered on target."""
        # Data centered at 60 (the target)
        data = [60, 58, 62, 59, 61, 60, 59, 61, 60, 58]

        cpm = analyzer.calculate_cpm(data, lsl=40.0, usl=80.0, target=60.0)
        cp = analyzer.calculate_cp(data, lsl=40.0, usl=80.0)

        # When centered on target, Cpm ≈ Cp
        assert abs(cpm - cp) < 0.1

    def test_cpm_off_target(self, analyzer):
        """Test Cpm when process is off target."""
        # Data centered at 70, but target is 60
        data = [70, 68, 72, 69, 71, 70, 69, 71, 70, 68]

        cpm = analyzer.calculate_cpm(data, lsl=40.0, usl=80.0, target=60.0)
        cp = analyzer.calculate_cp(data, lsl=40.0, usl=80.0)

        # Off-target: Cpm should be less than Cp
        assert cpm < cp

    def test_cpm_formula_validation(self, analyzer):
        """Test Cpm formula with known values."""
        # mean=70, σ=5, target=60, LSL=40, USL=80
        # Deviation from target = 70-60 = 10
        # Adjusted σ = √(5² + 10²) = √(25 + 100) = √125 = 11.18
        # Cpm = 40 / (6 * 11.18) = 40/67.08 = 0.596
        data = [70 + x for x in [-5, -3, -1, 0, 1, 3, 5]]
        data.extend([70 + x for x in [-5, -3, -1, 0, 1, 3, 5]])

        cpm = analyzer.calculate_cpm(data, lsl=40.0, usl=80.0, target=60.0)

        # Should be around 0.6
        assert 0.4 < cpm < 0.8

    def test_cpm_always_less_than_cp(self, analyzer):
        """Test that Cpm <= Cp (unless exactly on target)."""
        data = [65, 63, 67, 64, 66, 65, 64, 66, 65, 63]

        cp = analyzer.calculate_cp(data, lsl=40.0, usl=80.0)
        cpm = analyzer.calculate_cpm(data, lsl=40.0, usl=80.0, target=60.0)

        # Cpm penalizes off-target
        assert cpm <= cp

    def test_cpm_empty_data(self, analyzer):
        """Test Cpm raises error with empty data."""
        with pytest.raises(ValueError, match="empty data"):
            analyzer.calculate_cpm([], lsl=40.0, usl=80.0, target=60.0)

    def test_cpm_zero_variance_on_target(self, analyzer):
        """Test Cpm with zero variance on target."""
        data = [60.0] * 10

        cpm = analyzer.calculate_cpm(data, lsl=40.0, usl=80.0, target=60.0)

        # Perfect on target, no variation
        assert math.isinf(cpm)


class TestSigmaLevelConversion:
    """Test sigma level conversion from Cpk."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer()

    def test_sigma_level_from_cpk(self, analyzer):
        """Test sigma level calculation from Cpk."""
        # Standard conversions
        assert analyzer.get_sigma_level(1.0) == pytest.approx(3.0, abs=0.1)
        assert analyzer.get_sigma_level(1.33) == pytest.approx(4.0, abs=0.1)
        assert analyzer.get_sigma_level(1.67) == pytest.approx(5.0, abs=0.1)
        assert analyzer.get_sigma_level(2.0) == pytest.approx(6.0, abs=0.1)

    def test_sigma_level_zero_cpk(self, analyzer):
        """Test sigma level with zero Cpk."""
        assert analyzer.get_sigma_level(0.0) == 0.0

    def test_sigma_level_negative_cpk(self, analyzer):
        """Test sigma level with negative Cpk."""
        assert analyzer.get_sigma_level(-0.5) == 0.0

    def test_sigma_level_fractional(self, analyzer):
        """Test sigma level with fractional Cpk."""
        sigma = analyzer.get_sigma_level(1.5)
        assert sigma == pytest.approx(4.5, abs=0.01)


class TestCapabilityClassification:
    """Test capability classification."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer()

    def test_excellent_classification(self, analyzer):
        """Test EXCELLENT classification."""
        assert analyzer.classify_capability(2.0) == "EXCELLENT"
        assert analyzer.classify_capability(1.67) == "EXCELLENT"
        assert analyzer.classify_capability(3.0) == "EXCELLENT"

    def test_capable_classification(self, analyzer):
        """Test CAPABLE classification."""
        assert analyzer.classify_capability(1.33) == "CAPABLE"
        assert analyzer.classify_capability(1.5) == "CAPABLE"
        assert analyzer.classify_capability(1.66) == "CAPABLE"

    def test_marginal_classification(self, analyzer):
        """Test MARGINAL classification."""
        assert analyzer.classify_capability(1.0) == "MARGINAL"
        assert analyzer.classify_capability(1.2) == "MARGINAL"
        assert analyzer.classify_capability(1.32) == "MARGINAL"

    def test_incapable_classification(self, analyzer):
        """Test INCAPABLE classification."""
        assert analyzer.classify_capability(0.99) == "INCAPABLE"
        assert analyzer.classify_capability(0.5) == "INCAPABLE"
        assert analyzer.classify_capability(0.0) == "INCAPABLE"
        assert analyzer.classify_capability(-0.5) == "INCAPABLE"


class TestWorkloadCapabilityAnalysis:
    """Test workload capability analysis (main method)."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer(min_sample_size=30)

    def test_analyze_centered_workload(self, analyzer, centered_data):
        """Test analysis of well-centered workload data."""
        report = analyzer.analyze_workload_capability(
            centered_data,
            min_hours=40.0,
            max_hours=80.0,
            target_hours=60.0,
        )

        assert isinstance(report, ProcessCapabilityReport)
        assert report.sample_size == len(centered_data)
        assert report.lsl == 40.0
        assert report.usl == 80.0
        assert report.target == 60.0
        assert report.capability_status in ["EXCELLENT", "CAPABLE", "MARGINAL"]
        assert report.sigma_level > 0

    def test_analyze_default_target(self, analyzer, centered_data):
        """Test analysis with default target (midpoint)."""
        report = analyzer.analyze_workload_capability(
            centered_data,
            min_hours=40.0,
            max_hours=80.0,
        )

        # Target should default to midpoint
        assert report.target == 60.0

    def test_analyze_off_center_workload(self, analyzer, off_center_data):
        """Test analysis of off-center workload data."""
        report = analyzer.analyze_workload_capability(
            off_center_data,
            min_hours=40.0,
            max_hours=80.0,
            target_hours=60.0,
        )

        # Off-center: Cpk should be less than Cp
        assert report.cpk < report.cp

    def test_analyze_high_variation_workload(self, analyzer, high_variation_data):
        """Test analysis of high-variation workload data."""
        report = analyzer.analyze_workload_capability(
            high_variation_data,
            min_hours=40.0,
            max_hours=80.0,
        )

        # High variation → lower capability
        assert report.capability_status in ["MARGINAL", "INCAPABLE", "CAPABLE"]

    def test_analyze_excellent_workload(self, analyzer):
        """Test analysis of excellent (6σ) workload."""
        # Tightly controlled data
        data = [60 + x for x in range(-2, 3)] * 10  # 58-62 range

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=40.0,
            max_hours=80.0,
        )

        assert report.capability_status == "EXCELLENT"
        assert report.sigma_level > 5.0

    def test_analyze_incapable_workload(self, analyzer):
        """Test analysis of incapable workload."""
        # Wide, erratic data
        data = [40, 80, 42, 78, 45, 75, 43, 79] * 5

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=40.0,
            max_hours=80.0,
        )

        assert report.capability_status in ["INCAPABLE", "MARGINAL"]
        assert report.cpk < 1.33

    def test_analyze_empty_data_raises_error(self, analyzer):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="empty data"):
            analyzer.analyze_workload_capability(
                [],
                min_hours=40.0,
                max_hours=80.0,
            )

    def test_analyze_small_sample_warning(self, analyzer, caplog):
        """Test warning with small sample size."""
        small_data = [60, 65, 58, 62, 61]  # Only 5 samples

        report = analyzer.analyze_workload_capability(
            small_data,
            min_hours=40.0,
            max_hours=80.0,
        )

        # Should still produce report
        assert isinstance(report, ProcessCapabilityReport)

        # Should log warning about sample size
        assert "below recommended minimum" in caplog.text.lower()

    def test_analyze_invalid_spec_limits(self, analyzer):
        """Test error with invalid specification limits."""
        data = [60, 65, 58, 62, 61]

        with pytest.raises(ValueError, match="Invalid specification limits"):
            analyzer.analyze_workload_capability(
                data,
                min_hours=80.0,  # LSL > USL
                max_hours=40.0,
            )

    def test_analyze_all_indices_present(self, analyzer, centered_data):
        """Test that all capability indices are calculated."""
        report = analyzer.analyze_workload_capability(
            centered_data,
            min_hours=40.0,
            max_hours=80.0,
        )

        assert report.cp > 0
        assert report.cpk > 0
        assert report.pp > 0
        assert report.ppk > 0
        assert report.cpm > 0

    def test_analyze_statistics_accurate(self, analyzer):
        """Test that calculated statistics match input data."""
        data = [60, 65, 55, 70, 50, 75, 58, 62, 68, 52]

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=40.0,
            max_hours=80.0,
        )

        expected_mean = statistics.mean(data)
        expected_std = statistics.stdev(data)

        assert abs(report.mean - expected_mean) < 0.01
        assert abs(report.std_dev - expected_std) < 0.01


class TestCapabilitySummary:
    """Test capability summary generation."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer()

    @pytest.fixture
    def sample_report(self):
        """Create a sample capability report."""
        return ProcessCapabilityReport(
            cp=1.5,
            cpk=1.4,
            pp=1.5,
            ppk=1.4,
            cpm=1.3,
            capability_status="CAPABLE",
            sigma_level=4.2,
            sample_size=50,
            mean=65.0,
            std_dev=5.0,
            lsl=40.0,
            usl=80.0,
            target=60.0,
        )

    def test_summary_structure(self, analyzer, sample_report):
        """Test summary dictionary structure."""
        summary = analyzer.get_capability_summary(sample_report)

        assert "status" in summary
        assert "sigma_level" in summary
        assert "indices" in summary
        assert "centering" in summary
        assert "statistics" in summary
        assert "estimated_defect_rate" in summary
        assert "recommendations" in summary

    def test_summary_indices_formatted(self, analyzer, sample_report):
        """Test that indices are properly formatted."""
        summary = analyzer.get_capability_summary(sample_report)

        indices = summary["indices"]
        assert "Cpk" in indices
        assert "Cp" in indices
        assert "Ppk" in indices
        assert "Pp" in indices
        assert "Cpm" in indices

        # Check formatting (3 decimal places)
        assert indices["Cpk"] == "1.400"
        assert indices["Cp"] == "1.500"

    def test_summary_centering_assessment(self, analyzer, sample_report):
        """Test centering assessment in summary."""
        summary = analyzer.get_capability_summary(sample_report)

        centering = summary["centering"]
        assert isinstance(centering, str)
        assert any(word in centering for word in ["EXCELLENT", "GOOD", "FAIR", "POOR"])

    def test_summary_recommendations_present(self, analyzer, sample_report):
        """Test that recommendations are generated."""
        summary = analyzer.get_capability_summary(sample_report)

        recommendations = summary["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_summary_defect_rate_calculated(self, analyzer, sample_report):
        """Test defect rate estimation."""
        summary = analyzer.get_capability_summary(sample_report)

        defect_rate = summary["estimated_defect_rate"]
        assert "ppm" in defect_rate
        assert "percentage" in defect_rate

    def test_summary_statistics_match_report(self, analyzer, sample_report):
        """Test that summary statistics match report."""
        summary = analyzer.get_capability_summary(sample_report)

        stats = summary["statistics"]
        assert stats["mean"] == "65.00"
        assert stats["std_dev"] == "5.00"
        assert stats["target"] == "60.00"
        assert stats["sample_size"] == 50

    def test_centering_excellent(self, analyzer):
        """Test excellent centering assessment."""
        report = ProcessCapabilityReport(
            cp=1.5,
            cpk=1.48,  # 98.7% of Cp
            pp=1.5,
            ppk=1.48,
            cpm=1.45,
            capability_status="CAPABLE",
            sigma_level=4.44,
            sample_size=50,
            mean=60.0,
            std_dev=5.0,
            lsl=40.0,
            usl=80.0,
            target=60.0,
        )

        summary = analyzer.get_capability_summary(report)
        assert "EXCELLENT" in summary["centering"]

    def test_centering_poor(self, analyzer):
        """Test poor centering assessment."""
        report = ProcessCapabilityReport(
            cp=1.5,
            cpk=0.9,  # 60% of Cp
            pp=1.5,
            ppk=0.9,
            cpm=0.8,
            capability_status="INCAPABLE",
            sigma_level=2.7,
            sample_size=50,
            mean=70.0,
            std_dev=5.0,
            lsl=40.0,
            usl=80.0,
            target=60.0,
        )

        summary = analyzer.get_capability_summary(report)
        assert "POOR" in summary["centering"]

    def test_recommendations_incapable(self, analyzer):
        """Test recommendations for incapable process."""
        report = ProcessCapabilityReport(
            cp=0.8,
            cpk=0.7,
            pp=0.8,
            ppk=0.7,
            cpm=0.6,
            capability_status="INCAPABLE",
            sigma_level=2.1,
            sample_size=50,
            mean=65.0,
            std_dev=8.0,
            lsl=40.0,
            usl=80.0,
            target=60.0,
        )

        summary = analyzer.get_capability_summary(report)
        recommendations = summary["recommendations"]

        assert any("URGENT" in rec for rec in recommendations)

    def test_recommendations_excellent(self, analyzer):
        """Test recommendations for excellent process."""
        report = ProcessCapabilityReport(
            cp=2.0,
            cpk=1.95,
            pp=2.0,
            ppk=1.95,
            cpm=1.9,
            capability_status="EXCELLENT",
            sigma_level=5.85,
            sample_size=50,
            mean=60.0,
            std_dev=3.33,
            lsl=40.0,
            usl=80.0,
            target=60.0,
        )

        summary = analyzer.get_capability_summary(report)
        recommendations = summary["recommendations"]

        assert any("World-class" in rec for rec in recommendations)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def analyzer(self):
        return ScheduleCapabilityAnalyzer()

    def test_all_data_at_lsl(self, analyzer):
        """Test when all data points are at LSL."""
        data = [40.0] * 10

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=40.0,
            max_hours=80.0,
        )

        # At spec limit, should still be technically capable
        assert report.mean == 40.0

    def test_all_data_at_usl(self, analyzer):
        """Test when all data points are at USL."""
        data = [80.0] * 10

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=40.0,
            max_hours=80.0,
        )

        # At spec limit
        assert report.mean == 80.0

    def test_all_data_outside_usl(self, analyzer):
        """Test when all data exceeds USL."""
        data = [85.0] * 10

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=40.0,
            max_hours=80.0,
        )

        # Should be incapable
        assert report.capability_status == "INCAPABLE"
        assert report.cpk == 0.0  # Zero variance outside spec

    def test_bimodal_distribution(self, analyzer):
        """Test with bimodal data distribution."""
        # Two clusters: one at 50, one at 70
        data = [50] * 15 + [70] * 15

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=40.0,
            max_hours=80.0,
        )

        # Bimodal should have high variation
        assert report.std_dev > 5.0

    def test_very_large_sample(self, analyzer):
        """Test with very large sample size."""
        # Generate 1000 samples
        import random

        random.seed(42)
        data = [random.gauss(60, 5) for _ in range(1000)]

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=40.0,
            max_hours=80.0,
        )

        assert report.sample_size == 1000
        assert report.capability_status in ["EXCELLENT", "CAPABLE"]

    def test_negative_values(self, analyzer):
        """Test with negative values (invalid but should handle)."""
        data = [-10, 0, 10, 20, 30]

        # Should not crash, even if data is unusual
        report = analyzer.analyze_workload_capability(
            data,
            min_hours=0.0,
            max_hours=40.0,
        )

        assert isinstance(report, ProcessCapabilityReport)

    def test_very_narrow_spec_limits(self, analyzer):
        """Test with very narrow specification limits."""
        data = [60, 61, 59, 60, 61, 59, 60]

        report = analyzer.analyze_workload_capability(
            data,
            min_hours=59.0,
            max_hours=61.0,
        )

        # Narrow specs with typical variation → low capability
        assert report.cpk < 2.0
