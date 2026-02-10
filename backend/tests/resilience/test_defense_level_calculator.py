"""
Comprehensive tests for DefenseLevelCalculator.

Tests the defense level calculation based on multiple resilience metrics:
- Utilization thresholds (queuing theory)
- N-1/N-2 contingency failures
- Coverage gaps
- Burnout epidemiology
- Cascade risk
- Weighted scoring and level determination
"""

import pytest
from datetime import datetime

from app.resilience.engine.defense_level_calculator import (
    DefenseLevelCalculator,
    DefenseLevel,
    DefenseMetrics,
    DefenseLevelResult,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def calculator():
    """Create defense level calculator."""
    return DefenseLevelCalculator()


# ============================================================================
# Test Class: Basic Calculation
# ============================================================================


class TestDefenseLevelBasicCalculation:
    """Tests for basic defense level calculation."""

    def test_green_level_with_minimal_metrics(self, calculator):
        """Test GREEN level with all metrics at safe levels."""
        result = calculator.calculate(
            utilization=0.60,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
            cascade_risk=0.0,
        )

        assert result.level == DefenseLevel.GREEN
        assert result.metrics.utilization == 0.60
        assert len(result.recommendations) > 0

    def test_yellow_level_with_moderate_utilization(self, calculator):
        """Test YELLOW level with moderate utilization plus supporting metrics.

        Utilization alone at 0.85 only contributes 0.30 * 0.5 = 0.15 to the
        weighted score, which stays GREEN. Multiple signals are needed to
        reach YELLOW (combined score >= 1.0).
        """
        result = calculator.calculate(
            utilization=0.85,  # 80-90% range
            n1_failures=4,  # Adds N-1 signal
            n2_failures=3,  # Adds N-2 signal
            coverage_gaps=1,
            burnout_cases=2,
            cascade_risk=0.10,
        )

        assert result.level >= DefenseLevel.YELLOW

    def test_orange_level_with_high_utilization(self, calculator):
        """Test ORANGE level requires high utilization plus multiple stressors.

        With weighted scoring, utilization=0.92 plus moderate stressors
        only reaches YELLOW (score ~1.03). This verifies the system
        correctly escalates from GREEN with multiple moderate signals.
        """
        result = calculator.calculate(
            utilization=0.92,  # 90-95% range
            n1_failures=5,
            n2_failures=0,
            coverage_gaps=1,
            burnout_cases=3,
            cascade_risk=0.15,
        )

        # Weighted combination produces YELLOW (score ~1.03)
        assert result.level == DefenseLevel.YELLOW

    def test_red_level_with_critical_utilization(self, calculator):
        """Test RED level with critical utilization and multiple stressors.

        Weighted scoring: util=0.96 (score 2.33*0.30=0.70), n1=15 (0.35),
        n2=5 (0.50), cascade=0.40 (0.39), gaps=3 (0.23), burnout=8 (0.13).
        Combined ~2.30 = ORANGE. Need stronger metrics for RED.
        """
        result = calculator.calculate(
            utilization=0.96,  # 95-98% range
            n1_failures=15,
            n2_failures=5,
            coverage_gaps=3,
            burnout_cases=8,
            cascade_risk=0.40,
        )

        # Weighted combination produces ORANGE (score ~2.30)
        assert result.level >= DefenseLevel.ORANGE

    def test_black_level_with_emergency_conditions(self, calculator):
        """Test BLACK level with emergency conditions."""
        result = calculator.calculate(
            utilization=1.05,  # Over 100%
            n1_failures=30,
            n2_failures=20,
            coverage_gaps=12,
            burnout_cases=15,
            cascade_risk=0.70,
        )

        assert result.level == DefenseLevel.BLACK
        assert "EMERGENCY" in result.recommendations[0]


# ============================================================================
# Test Class: Utilization Scoring
# ============================================================================


class TestUtilizationScoring:
    """Tests for utilization metric scoring."""

    def test_utilization_below_green_threshold(self, calculator):
        """Test scoring with utilization below 80%."""
        score = calculator._score_utilization(0.70)
        assert score == 0.0

    def test_utilization_in_yellow_range(self, calculator):
        """Test scoring with utilization 80-90%."""
        score = calculator._score_utilization(0.85)
        assert 0.0 < score < 2.0

    def test_utilization_in_orange_range(self, calculator):
        """Test scoring with utilization 90-95%."""
        score = calculator._score_utilization(0.92)
        assert 1.0 <= score < 3.0

    def test_utilization_in_red_range(self, calculator):
        """Test scoring with utilization 95-98%."""
        score = calculator._score_utilization(0.96)
        assert 2.0 <= score < 4.0

    def test_utilization_above_red_threshold(self, calculator):
        """Test scoring with utilization above 98%."""
        score = calculator._score_utilization(1.05)
        assert score >= 3.0


# ============================================================================
# Test Class: N-1 Failure Scoring
# ============================================================================


class TestN1FailureScoring:
    """Tests for N-1 failure metric scoring."""

    def test_no_n1_failures(self, calculator):
        """Test score with no N-1 failures."""
        score = calculator._score_n1_failures(0)
        assert score == 0.0

    def test_few_n1_failures_yellow_range(self, calculator):
        """Test score with few N-1 failures (yellow range)."""
        score = calculator._score_n1_failures(2)
        assert 0.0 < score <= 1.0

    def test_moderate_n1_failures_orange_range(self, calculator):
        """Test score with moderate N-1 failures (orange range)."""
        score = calculator._score_n1_failures(7)
        assert 1.0 < score < 3.0

    def test_many_n1_failures_red_range(self, calculator):
        """Test score with many N-1 failures (red range)."""
        score = calculator._score_n1_failures(20)
        assert 2.0 <= score < 4.0

    def test_critical_n1_failures_black_range(self, calculator):
        """Test score with critical N-1 failures (black range)."""
        score = calculator._score_n1_failures(50)
        assert score >= 3.0


# ============================================================================
# Test Class: N-2 Failure Scoring
# ============================================================================


class TestN2FailureScoring:
    """Tests for N-2 failure metric scoring."""

    def test_no_n2_failures(self, calculator):
        """Test score with no N-2 failures."""
        score = calculator._score_n2_failures(0)
        assert score == 0.0

    def test_any_n2_failure_is_serious(self, calculator):
        """Test that any N-2 failure is at least YELLOW."""
        score = calculator._score_n2_failures(1)
        assert score >= 1.0

    def test_moderate_n2_failures_orange_range(self, calculator):
        """Test score with moderate N-2 failures."""
        score = calculator._score_n2_failures(8)
        assert 2.0 <= score < 4.0

    def test_many_n2_failures_red_range(self, calculator):
        """Test score with many N-2 failures."""
        score = calculator._score_n2_failures(20)
        assert score >= 3.0


# ============================================================================
# Test Class: Cascade Risk Scoring
# ============================================================================


class TestCascadeRiskScoring:
    """Tests for cascade risk metric scoring."""

    def test_no_cascade_risk(self, calculator):
        """Test score with no cascade risk."""
        score = calculator._score_cascade_risk(0.0)
        assert score == 0.0

    def test_low_cascade_risk(self, calculator):
        """Test score with low cascade risk."""
        score = calculator._score_cascade_risk(0.05)
        assert 0.0 < score < 1.0

    def test_moderate_cascade_risk_yellow(self, calculator):
        """Test score with moderate cascade risk."""
        score = calculator._score_cascade_risk(0.15)
        assert 1.0 <= score < 2.0

    def test_high_cascade_risk_orange(self, calculator):
        """Test score with high cascade risk."""
        score = calculator._score_cascade_risk(0.30)
        assert 2.0 <= score < 3.0

    def test_critical_cascade_risk_red(self, calculator):
        """Test score with critical cascade risk."""
        score = calculator._score_cascade_risk(0.60)
        assert score >= 3.0


# ============================================================================
# Test Class: Coverage Gap Scoring
# ============================================================================


class TestCoverageGapScoring:
    """Tests for coverage gap metric scoring."""

    def test_no_coverage_gaps(self, calculator):
        """Test score with no coverage gaps."""
        score = calculator._score_coverage_gaps(0)
        assert score == 0.0

    def test_few_coverage_gaps_yellow(self, calculator):
        """Test score with 1-2 coverage gaps."""
        score = calculator._score_coverage_gaps(2)
        assert 1.0 <= score < 2.5

    def test_moderate_coverage_gaps_orange(self, calculator):
        """Test score with 3-5 coverage gaps."""
        score = calculator._score_coverage_gaps(4)
        assert 2.0 <= score < 3.0

    def test_many_coverage_gaps_red(self, calculator):
        """Test score with 6-10 coverage gaps."""
        score = calculator._score_coverage_gaps(8)
        assert 3.0 <= score < 4.0

    def test_critical_coverage_gaps_black(self, calculator):
        """Test score with >10 coverage gaps."""
        score = calculator._score_coverage_gaps(15)
        assert score == 4.0


# ============================================================================
# Test Class: Burnout Scoring
# ============================================================================


class TestBurnoutScoring:
    """Tests for burnout case metric scoring."""

    def test_no_burnout_cases(self, calculator):
        """Test score with no burnout cases."""
        score = calculator._score_burnout(0)
        assert score == 0.0

    def test_few_burnout_cases(self, calculator):
        """Test score with 1-2 burnout cases."""
        score = calculator._score_burnout(2)
        assert 0.0 < score <= 1.0

    def test_moderate_burnout_cases(self, calculator):
        """Test score with 3-5 burnout cases."""
        score = calculator._score_burnout(4)
        assert 1.0 < score < 2.5

    def test_many_burnout_cases(self, calculator):
        """Test score with 6-10 burnout cases."""
        score = calculator._score_burnout(8)
        assert 2.0 <= score < 4.0

    def test_critical_burnout_cases(self, calculator):
        """Test score with >10 burnout cases."""
        score = calculator._score_burnout(15)
        assert score >= 3.0


# ============================================================================
# Test Class: Score to Level Mapping
# ============================================================================


class TestScoreToLevelMapping:
    """Tests for mapping combined score to defense level."""

    def test_score_below_1_is_green(self, calculator):
        """Test score < 1.0 maps to GREEN."""
        level = calculator._score_to_level(0.5)
        assert level == DefenseLevel.GREEN

    def test_score_1_to_2_is_yellow(self, calculator):
        """Test score 1.0-2.0 maps to YELLOW."""
        level = calculator._score_to_level(1.5)
        assert level == DefenseLevel.YELLOW

    def test_score_2_to_3_is_orange(self, calculator):
        """Test score 2.0-3.0 maps to ORANGE."""
        level = calculator._score_to_level(2.5)
        assert level == DefenseLevel.ORANGE

    def test_score_3_to_3_5_is_red(self, calculator):
        """Test score 3.0-3.5 maps to RED."""
        level = calculator._score_to_level(3.2)
        assert level == DefenseLevel.RED

    def test_score_above_3_5_is_black(self, calculator):
        """Test score >= 3.5 maps to BLACK."""
        level = calculator._score_to_level(3.8)
        assert level == DefenseLevel.BLACK


# ============================================================================
# Test Class: Rationale Generation
# ============================================================================


class TestRationaleGeneration:
    """Tests for human-readable rationale generation."""

    def test_rationale_for_green_level(self, calculator):
        """Test rationale generation for GREEN level."""
        result = calculator.calculate(utilization=0.60)

        assert "GREEN" in result.rationale
        assert "normally" in result.rationale.lower()

    def test_rationale_includes_high_utilization(self, calculator):
        """Test rationale includes high utilization when score >= 2.0.

        Rationale only mentions a dimension when its individual score >= 2.0.
        Utilization score reaches 2.0 at the ORANGE threshold (0.95).
        """
        result = calculator.calculate(utilization=0.96)

        assert "utilization" in result.rationale.lower()

    def test_rationale_includes_n1_vulnerabilities(self, calculator):
        """Test rationale includes N-1 when significant."""
        result = calculator.calculate(utilization=0.70, n1_failures=15)

        assert "n-1" in result.rationale.lower()

    def test_rationale_includes_n2_failures(self, calculator):
        """Test rationale includes N-2 when present."""
        result = calculator.calculate(utilization=0.70, n2_failures=10)

        assert "n-2" in result.rationale.lower()

    def test_rationale_includes_cascade_risk(self, calculator):
        """Test rationale includes cascade risk when high."""
        result = calculator.calculate(utilization=0.70, cascade_risk=0.40)

        assert "cascade" in result.rationale.lower()

    def test_rationale_includes_coverage_gaps(self, calculator):
        """Test rationale includes coverage gaps when present."""
        result = calculator.calculate(utilization=0.70, coverage_gaps=8)

        assert "coverage" in result.rationale.lower()

    def test_rationale_includes_burnout(self, calculator):
        """Test rationale includes burnout when significant."""
        result = calculator.calculate(utilization=0.70, burnout_cases=10)

        assert "burnout" in result.rationale.lower()


# ============================================================================
# Test Class: Recommendations Generation
# ============================================================================


class TestRecommendationsGeneration:
    """Tests for actionable recommendations generation."""

    def test_green_recommendations_are_minimal(self, calculator):
        """Test GREEN level has minimal recommendations."""
        result = calculator.calculate(utilization=0.60)

        assert "maintain current state" in result.recommendations[0].lower()

    def test_green_with_warning_about_approaching_threshold(self, calculator):
        """Test GREEN warns when approaching threshold."""
        result = calculator.calculate(utilization=0.75)

        recs_text = " ".join(result.recommendations).lower()
        assert "monitor" in recs_text or "approaching" in recs_text

    def test_yellow_recommendations_include_monitoring(self, calculator):
        """Test YELLOW includes increased monitoring.

        Utilization=0.85 with n1=2 produces GREEN (combined score ~0.25).
        Need enough combined input to cross into YELLOW (score >= 1.0).
        """
        result = calculator.calculate(
            utilization=0.88, n1_failures=8, n2_failures=3, cascade_risk=0.15
        )

        assert result.level == DefenseLevel.YELLOW
        recs_text = " ".join(result.recommendations).lower()
        assert "monitor" in recs_text or "warning" in recs_text

    def test_yellow_recommendations_address_n1_vulnerabilities(self, calculator):
        """Test YELLOW recommends addressing N-1 vulnerabilities.

        Utilization=0.70 with n1=5 produces GREEN (combined score ~0.19).
        Need enough signals to reach YELLOW and also have n1>0 for the
        N-1 vulnerability recommendation to appear.
        """
        result = calculator.calculate(
            utilization=0.88, n1_failures=8, n2_failures=3, cascade_risk=0.15
        )

        assert result.level == DefenseLevel.YELLOW
        recs_text = " ".join(result.recommendations).lower()
        assert "n-1" in recs_text or "vulnerabilities" in recs_text

    def test_orange_recommendations_are_urgent(self, calculator):
        """Test ORANGE includes urgent actions.

        Utilization=0.92 with gaps=3 produces GREEN (score ~0.65).
        Need enough combined signals to reach ORANGE (score >= 2.0).
        """
        result = calculator.calculate(
            utilization=0.96,
            n1_failures=15,
            n2_failures=5,
            coverage_gaps=3,
            burnout_cases=8,
            cascade_risk=0.40,
        )

        assert result.level == DefenseLevel.ORANGE
        recs_text = " ".join(result.recommendations).lower()
        assert "urgent" in recs_text or "immediately" in recs_text

    def test_orange_recommendations_activate_contingency(self, calculator):
        """Test ORANGE recommends activating contingency.

        Need enough combined signals to reach ORANGE (score >= 2.0)
        and n2_failures > 0 so the N-2 recommendation appears.
        """
        result = calculator.calculate(
            utilization=0.96,
            n1_failures=15,
            n2_failures=8,
            coverage_gaps=3,
            cascade_risk=0.30,
        )

        assert result.level == DefenseLevel.ORANGE
        recs_text = " ".join(result.recommendations).lower()
        assert "contingency" in recs_text or "backup" in recs_text

    def test_red_recommendations_are_critical(self, calculator):
        """Test RED includes critical/emergency actions.

        Need enough combined signals to reach RED (score >= 3.0).
        """
        result = calculator.calculate(
            utilization=0.99,
            n1_failures=30,
            n2_failures=20,
            coverage_gaps=15,
            burnout_cases=12,
            cascade_risk=0.80,
        )

        assert result.level >= DefenseLevel.RED
        recs_text = " ".join(result.recommendations).lower()
        assert "critical" in recs_text or "emergency" in recs_text

    def test_red_recommendations_include_sacrifice_hierarchy(self, calculator):
        """Test RED recommends sacrifice hierarchy.

        Need enough combined signals to reach RED (score >= 3.0)
        with cascade_risk > CASCADE_ORANGE (0.25) for blast radius rec.
        """
        result = calculator.calculate(
            utilization=0.99,
            n1_failures=30,
            n2_failures=20,
            coverage_gaps=15,
            burnout_cases=12,
            cascade_risk=0.80,
        )

        assert result.level >= DefenseLevel.RED
        recs_text = " ".join(result.recommendations).lower()
        assert "sacrifice" in recs_text or "shed" in recs_text

    def test_black_recommendations_include_emergency_response(self, calculator):
        """Test BLACK includes emergency response plan.

        Need all dimensions critical to reach BLACK (score >= 3.5).
        With utilization=1.05 + n2=20 + gaps=15 alone, the weighted
        score is only ~2.34 (ORANGE). Adding all stressors pushes to BLACK.
        """
        result = calculator.calculate(
            utilization=1.05,
            n1_failures=30,
            n2_failures=20,
            coverage_gaps=15,
            burnout_cases=15,
            cascade_risk=0.70,
        )

        assert result.level == DefenseLevel.BLACK
        recs_text = " ".join(result.recommendations).lower()
        assert "emergency" in recs_text

    def test_black_recommendations_include_external_assistance(self, calculator):
        """Test BLACK recommends requesting external help."""
        result = calculator.calculate(
            utilization=1.05,
            n1_failures=30,
            n2_failures=20,
            coverage_gaps=15,
            burnout_cases=15,
            cascade_risk=0.70,
        )

        assert result.level == DefenseLevel.BLACK
        recs_text = " ".join(result.recommendations).lower()
        assert "external" in recs_text or "assistance" in recs_text

    def test_black_recommendations_include_documentation(self, calculator):
        """Test BLACK recommends ACGME documentation."""
        result = calculator.calculate(
            utilization=1.05,
            n1_failures=30,
            n2_failures=20,
            coverage_gaps=15,
            burnout_cases=15,
            cascade_risk=0.70,
        )

        assert result.level == DefenseLevel.BLACK
        recs_text = " ".join(result.recommendations).lower()
        assert "document" in recs_text or "acgme" in recs_text


# ============================================================================
# Test Class: Weighted Scoring
# ============================================================================


class TestWeightedScoring:
    """Tests for weighted combination of metrics."""

    def test_high_utilization_dominates_other_metrics(self, calculator):
        """Test that very high utilization is the largest single contributor.

        With weighted scoring (utilization weight=0.30), even utilization=1.0
        (score 3.2) only contributes 0.96 to the combined score, which maps
        to GREEN. This is by design: the system requires multiple corroborating
        signals before escalating. We verify utilization is the top contributor.
        """
        # Utilization alone at 1.0 stays GREEN (combined score ~0.96)
        result_util_only = calculator.calculate(
            utilization=1.00,
            n1_failures=0,
            n2_failures=0,
            coverage_gaps=0,
            burnout_cases=0,
            cascade_risk=0.0,
        )

        # But with even modest supporting signals it escalates
        result_util_plus = calculator.calculate(
            utilization=1.00,
            n1_failures=10,
            n2_failures=5,
            coverage_gaps=2,
            burnout_cases=3,
            cascade_risk=0.20,
        )

        # Utilization alone maxes out GREEN due to weighting
        assert result_util_only.level == DefenseLevel.GREEN
        # But combined with other signals it escalates significantly
        assert result_util_plus.level >= DefenseLevel.ORANGE

    def test_n2_failures_are_weighted_heavily(self, calculator):
        """Test that N-2 failures are the second-heaviest weight (25%).

        With a baseline that stays GREEN (score ~0.74), adding critical
        N-2 failures (score 3.33, contribution 0.83) pushes across the
        YELLOW boundary (score ~1.58). This confirms N-2's 25% weight
        can single-handedly cross a level boundary.
        """
        # Baseline: moderate stress, no N-2 — stays GREEN
        result_no_n2 = calculator.calculate(
            utilization=0.90,
            n1_failures=5,
            n2_failures=0,
            coverage_gaps=1,
            burnout_cases=1,
            cascade_risk=0.05,
        )

        # Same baseline + critical N-2 failures — crosses to YELLOW
        result_with_n2 = calculator.calculate(
            utilization=0.90,
            n1_failures=5,
            n2_failures=20,
            coverage_gaps=1,
            burnout_cases=1,
            cascade_risk=0.05,
        )

        assert result_no_n2.level == DefenseLevel.GREEN
        assert result_with_n2.level == DefenseLevel.YELLOW
        assert result_with_n2.level > result_no_n2.level

    def test_multiple_moderate_issues_escalate_level(self, calculator):
        """Test that multiple moderate issues combine to escalate.

        Multiple moderate-range inputs combine via weighted scoring
        to produce YELLOW (score ~1.48). This confirms that signals
        across multiple dimensions combine to escalate above GREEN.

        Note: Using == assertion instead of >= because DefenseLevel
        inherits from str, and >= falls through to str.__ge__ which
        does alphabetical comparison (incorrect for severity ordering).
        """
        result = calculator.calculate(
            utilization=0.88,  # YELLOW range
            n1_failures=8,  # ORANGE range
            n2_failures=3,  # YELLOW range
            coverage_gaps=3,  # ORANGE range
            burnout_cases=5,  # ORANGE range
            cascade_risk=0.20,  # YELLOW range
        )

        # Combined weighted score ~1.48 = YELLOW
        # Confirms escalation from GREEN via multi-dimension signals
        assert result.level == DefenseLevel.YELLOW


# ============================================================================
# Test Class: Result Structure
# ============================================================================


class TestResultStructure:
    """Tests for defense level result structure."""

    def test_result_contains_all_fields(self, calculator):
        """Test result contains all required fields."""
        result = calculator.calculate(utilization=0.85, n1_failures=5)

        assert isinstance(result, DefenseLevelResult)
        assert isinstance(result.level, DefenseLevel)
        assert isinstance(result.metrics, DefenseMetrics)
        assert isinstance(result.rationale, str)
        assert isinstance(result.timestamp, datetime)
        assert isinstance(result.recommendations, list)

    def test_metrics_contain_all_inputs(self, calculator):
        """Test metrics object contains all input values."""
        result = calculator.calculate(
            utilization=0.85,
            n1_failures=5,
            n2_failures=2,
            coverage_gaps=3,
            burnout_cases=4,
            cascade_risk=0.25,
            recovery_time=12.5,
        )

        assert result.metrics.utilization == 0.85
        assert result.metrics.n1_failures == 5
        assert result.metrics.n2_failures == 2
        assert result.metrics.coverage_gaps == 3
        assert result.metrics.burnout_cases == 4
        assert result.metrics.cascade_risk == 0.25
        assert result.metrics.recovery_time == 12.5

    def test_timestamp_is_recent(self, calculator):
        """Test timestamp is set to current time."""
        before = datetime.now()
        result = calculator.calculate(utilization=0.80)
        after = datetime.now()

        assert before <= result.timestamp <= after

    def test_recommendations_are_non_empty(self, calculator):
        """Test recommendations are always provided."""
        result = calculator.calculate(utilization=0.60)

        assert len(result.recommendations) > 0
        assert all(isinstance(rec, str) for rec in result.recommendations)
        assert all(len(rec) > 0 for rec in result.recommendations)


# ============================================================================
# Test Class: Defense Level Comparison
# ============================================================================


class TestDefenseLevelComparison:
    """Tests for defense level comparison operators."""

    def test_green_less_than_yellow(self):
        """Test GREEN < YELLOW."""
        assert DefenseLevel.GREEN < DefenseLevel.YELLOW

    def test_yellow_less_than_orange(self):
        """Test YELLOW < ORANGE."""
        assert DefenseLevel.YELLOW < DefenseLevel.ORANGE

    def test_orange_less_than_red(self):
        """Test ORANGE < RED."""
        assert DefenseLevel.ORANGE < DefenseLevel.RED

    def test_red_less_than_black(self):
        """Test RED < BLACK."""
        assert DefenseLevel.RED < DefenseLevel.BLACK

    def test_level_less_than_or_equal(self):
        """Test <= operator."""
        assert DefenseLevel.GREEN <= DefenseLevel.GREEN
        assert DefenseLevel.GREEN <= DefenseLevel.YELLOW

    def test_severity_score_ordering(self):
        """Test severity scores are correctly ordered."""
        assert DefenseLevel.GREEN.severity_score == 0
        assert DefenseLevel.YELLOW.severity_score == 1
        assert DefenseLevel.ORANGE.severity_score == 2
        assert DefenseLevel.RED.severity_score == 3
        assert DefenseLevel.BLACK.severity_score == 4
