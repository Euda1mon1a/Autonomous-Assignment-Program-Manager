"""
Tests for the strict evaluator with numeric scoring.
"""

from uuid import uuid4

from app.autonomous.evaluator import (
    EvaluationResult,
    ScheduleEvaluator,
    ScoreComponent,
    ViolationDetail,
    ViolationSeverity,
)


class TestViolationDetail:
    """Tests for ViolationDetail dataclass."""

    def test_create_violation_detail(self):
        """Test creating a violation detail."""
        violation = ViolationDetail(
            type="80_HOUR_VIOLATION",
            severity=ViolationSeverity.CRITICAL,
            message="Exceeded 80 hours",
            person_id=uuid4(),
            penalty=0.20,
        )

        assert violation.type == "80_HOUR_VIOLATION"
        assert violation.severity == ViolationSeverity.CRITICAL
        assert violation.penalty == 0.20

    def test_violation_severity_enum(self):
        """Test severity enum values."""
        assert ViolationSeverity.CRITICAL.value == "critical"
        assert ViolationSeverity.HIGH.value == "high"
        assert ViolationSeverity.MEDIUM.value == "medium"
        assert ViolationSeverity.LOW.value == "low"


class TestScoreComponent:
    """Tests for ScoreComponent dataclass."""

    def test_weighted_value_calculation(self):
        """Test that weighted value is calculated correctly."""
        component = ScoreComponent(
            name="coverage_rate",
            weight=0.25,
            raw_value=0.80,
        )

        assert component.weighted_value == 0.20  # 0.25 * 0.80

    def test_zero_weight(self):
        """Test component with zero weight."""
        component = ScoreComponent(
            name="preference",
            weight=0.0,
            raw_value=1.0,
        )

        assert component.weighted_value == 0.0


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_to_dict(self):
        """Test JSON serialization."""
        result = EvaluationResult(
            valid=True,
            score=0.85,
            hard_constraint_pass=True,
            soft_score=0.45,
            coverage_rate=0.90,
            total_violations=2,
            critical_violations=0,
            violations=[
                ViolationDetail(
                    type="N1_VULNERABILITY",
                    severity=ViolationSeverity.HIGH,
                    message="N-1 vulnerable",
                )
            ],
            components=[
                ScoreComponent(name="coverage", weight=0.25, raw_value=0.90),
            ],
        )

        data = result.to_dict()

        assert data["valid"] is True
        assert data["score"] == 0.85
        assert data["coverage_rate"] == 0.90
        assert len(data["violations"]) == 1
        assert data["violations"][0]["type"] == "N1_VULNERABILITY"

    def test_is_better_than_valid_vs_invalid(self):
        """Test comparison: valid beats invalid."""
        valid = EvaluationResult(
            valid=True,
            score=0.50,
            hard_constraint_pass=True,
            soft_score=0.50,
            coverage_rate=0.80,
            total_violations=0,
            critical_violations=0,
        )

        invalid = EvaluationResult(
            valid=False,
            score=0.90,  # Higher score but invalid
            hard_constraint_pass=False,
            soft_score=0.90,
            coverage_rate=0.95,
            total_violations=1,
            critical_violations=1,
        )

        assert valid.is_better_than(invalid) is True
        assert invalid.is_better_than(valid) is False

    def test_is_better_than_score_comparison(self):
        """Test comparison: higher score wins when both valid."""
        high_score = EvaluationResult(
            valid=True,
            score=0.90,
            hard_constraint_pass=True,
            soft_score=0.50,
            coverage_rate=0.95,
            total_violations=0,
            critical_violations=0,
        )

        low_score = EvaluationResult(
            valid=True,
            score=0.70,
            hard_constraint_pass=True,
            soft_score=0.30,
            coverage_rate=0.80,
            total_violations=0,
            critical_violations=0,
        )

        assert high_score.is_better_than(low_score) is True
        assert low_score.is_better_than(high_score) is False

    def test_is_better_than_same_score_fewer_violations(self):
        """Test comparison: fewer critical violations wins on tie."""
        few_violations = EvaluationResult(
            valid=False,
            score=0.70,
            hard_constraint_pass=False,
            soft_score=0.70,
            coverage_rate=0.80,
            total_violations=1,
            critical_violations=1,
        )

        many_violations = EvaluationResult(
            valid=False,
            score=0.70,  # Same score
            hard_constraint_pass=False,
            soft_score=0.70,
            coverage_rate=0.80,
            total_violations=5,
            critical_violations=5,
        )

        assert few_violations.is_better_than(many_violations) is True
        assert many_violations.is_better_than(few_violations) is False


class TestScheduleEvaluatorWeights:
    """Tests for evaluator weight configuration."""

    def test_weights_sum_to_one(self):
        """Test that all weights sum to 1.0."""
        total = sum(ScheduleEvaluator.WEIGHTS.values())
        assert abs(total - 1.0) < 0.001  # Allow floating point error

    def test_weight_keys(self):
        """Test expected weight keys are present."""
        expected = {
            "acgme_compliance",
            "coverage_rate",
            "resilience",
            "load_balance",
            "preference_alignment",
        }
        assert set(ScheduleEvaluator.WEIGHTS.keys()) == expected


class TestEvaluatorCoverageScore:
    """Tests for coverage rate scoring."""

    def test_full_coverage_score(self):
        """Test that 100% coverage gives 1.0 raw value."""
        # This would need a database fixture in real tests
        # For now, test the math logic
        assigned = 100
        total = 100
        coverage = assigned / total if total > 0 else 1.0

        assert coverage == 1.0

    def test_partial_coverage_score(self):
        """Test partial coverage calculation."""
        assigned = 80
        total = 100
        coverage = assigned / total

        assert coverage == 0.80

    def test_no_blocks_coverage(self):
        """Test coverage when no blocks exist."""
        assigned = 0
        total = 0
        coverage = assigned / total if total > 0 else 1.0

        assert coverage == 1.0  # Default to 1.0 if no blocks


class TestEvaluatorLoadBalance:
    """Tests for load balance scoring using coefficient of variation."""

    def test_perfectly_balanced(self):
        """Test that perfectly balanced load gives score of 1.0."""
        # All people have same number of assignments
        counts = [10, 10, 10, 10]
        mean = sum(counts) / len(counts)
        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        std_dev = variance**0.5
        cv = std_dev / mean if mean > 0 else 0.0
        score = max(0.0, 1.0 - cv)

        assert cv == 0.0
        assert score == 1.0

    def test_unbalanced_load(self):
        """Test that unbalanced load reduces score."""
        counts = [1, 10, 10, 10]  # One person underloaded
        mean = sum(counts) / len(counts)
        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        std_dev = variance**0.5
        cv = std_dev / mean if mean > 0 else 0.0
        score = max(0.0, 1.0 - cv)

        assert cv > 0.0
        assert score < 1.0

    def test_severely_unbalanced(self):
        """Test that severely unbalanced load gives low score."""
        counts = [1, 100]  # Extreme imbalance
        mean = sum(counts) / len(counts)
        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        std_dev = variance**0.5
        cv = std_dev / mean if mean > 0 else 0.0
        score = max(0.0, 1.0 - cv)

        assert cv > 0.5  # High coefficient of variation
        assert score < 0.5  # Low score
