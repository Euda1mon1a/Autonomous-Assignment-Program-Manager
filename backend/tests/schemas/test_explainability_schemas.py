"""Tests for explainability schemas (enums, defaults, nested models)."""

from datetime import datetime
from uuid import uuid4

from app.schemas.explainability import (
    ConfidenceLevel,
    ConstraintType,
    ConstraintStatus,
    ConstraintEvaluation,
    AlternativeCandidate,
    DecisionInputs,
    DecisionExplanation,
    AssignmentWithExplanation,
    ExplainabilityReport,
)


class TestConfidenceLevel:
    def test_values(self):
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"

    def test_count(self):
        assert len(ConfidenceLevel) == 3


class TestConstraintType:
    def test_values(self):
        assert ConstraintType.HARD.value == "hard"
        assert ConstraintType.SOFT.value == "soft"

    def test_count(self):
        assert len(ConstraintType) == 2


class TestConstraintStatus:
    def test_values(self):
        assert ConstraintStatus.SATISFIED.value == "satisfied"
        assert ConstraintStatus.VIOLATED.value == "violated"
        assert ConstraintStatus.NOT_APPLICABLE.value == "not_applicable"

    def test_count(self):
        assert len(ConstraintStatus) == 3


class TestConstraintEvaluation:
    def test_valid_minimal(self):
        r = ConstraintEvaluation(
            constraint_name="80-hour rule",
            constraint_type=ConstraintType.HARD,
            status=ConstraintStatus.SATISFIED,
        )
        assert r.weight == 1.0
        assert r.penalty == 0.0
        assert r.details is None

    def test_violated(self):
        r = ConstraintEvaluation(
            constraint_name="equity",
            constraint_type=ConstraintType.SOFT,
            status=ConstraintStatus.VIOLATED,
            weight=2.0,
            penalty=50.0,
            details="Assignment count above mean + 2 stdev",
        )
        assert r.penalty == 50.0


class TestAlternativeCandidate:
    def test_valid_minimal(self):
        r = AlternativeCandidate(
            person_id=uuid4(), person_name="Dr. Smith", score=850.0
        )
        assert r.rejection_reasons == []
        assert r.constraint_violations == []

    def test_with_reasons(self):
        r = AlternativeCandidate(
            person_id=uuid4(),
            person_name="Dr. Jones",
            score=700.0,
            rejection_reasons=["Lower score"],
            constraint_violations=["1-in-7 violation"],
        )
        assert len(r.rejection_reasons) == 1
        assert len(r.constraint_violations) == 1


class TestDecisionInputs:
    def test_valid_minimal(self):
        r = DecisionInputs(
            block_id=uuid4(),
            block_date=datetime(2026, 3, 1),
            block_time_of_day="AM",
            eligible_residents=10,
        )
        assert r.rotation_template_id is None
        assert r.rotation_name is None
        assert r.active_constraints == []
        assert r.overrides_in_effect == []

    def test_full(self):
        r = DecisionInputs(
            block_id=uuid4(),
            block_date=datetime(2026, 3, 1),
            block_time_of_day="PM",
            rotation_template_id=uuid4(),
            rotation_name="FM Clinic",
            eligible_residents=8,
            active_constraints=["80-hour", "1-in-7"],
            overrides_in_effect=["leave-override"],
        )
        assert len(r.active_constraints) == 2


class TestDecisionExplanation:
    def _make_inputs(self):
        return DecisionInputs(
            block_id=uuid4(),
            block_date=datetime(2026, 3, 1),
            block_time_of_day="AM",
            eligible_residents=10,
        )

    def test_valid_minimal(self):
        r = DecisionExplanation(
            person_id=uuid4(),
            person_name="Dr. Smith",
            inputs=self._make_inputs(),
        )
        assert r.assignment_id is None
        assert r.score == 0.0
        assert r.score_breakdown == {}
        assert r.constraints_evaluated == []
        assert r.hard_constraints_satisfied is True
        assert r.soft_constraint_penalties == 0.0
        assert r.alternatives == []
        assert r.margin_vs_next_best == 0.0
        assert r.confidence == ConfidenceLevel.MEDIUM
        assert r.confidence_score == 0.5
        assert r.confidence_factors == []
        assert r.trade_off_summary == ""
        assert r.algorithm == ""
        assert r.solver_version == "1.0.0"
        assert r.random_seed is None

    def test_full(self):
        alt = AlternativeCandidate(
            person_id=uuid4(), person_name="Dr. Jones", score=800.0
        )
        constraint = ConstraintEvaluation(
            constraint_name="80-hour",
            constraint_type=ConstraintType.HARD,
            status=ConstraintStatus.SATISFIED,
        )
        r = DecisionExplanation(
            assignment_id=uuid4(),
            person_id=uuid4(),
            person_name="Dr. Smith",
            inputs=self._make_inputs(),
            score=950.0,
            score_breakdown={"coverage": 1000, "equity_penalty": -50},
            constraints_evaluated=[constraint],
            alternatives=[alt],
            margin_vs_next_best=150.0,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.95,
            trade_off_summary="Clear winner",
        )
        assert r.score == 950.0
        assert len(r.alternatives) == 1


class TestAssignmentWithExplanation:
    def test_valid_minimal(self):
        r = AssignmentWithExplanation(
            id=uuid4(),
            block_id=uuid4(),
            person_id=uuid4(),
            rotation_template_id=None,
            role="primary",
            notes=None,
            override_reason=None,
            created_at=datetime(2026, 3, 1),
            updated_at=datetime(2026, 3, 1),
        )
        assert r.explanation is None
        assert r.confidence is None
        assert r.confidence_score is None


class TestExplainabilityReport:
    def test_defaults(self):
        r = ExplainabilityReport(
            start_date=datetime(2026, 3, 1),
            end_date=datetime(2026, 3, 28),
            total_assignments=100,
        )
        assert r.high_confidence_count == 0
        assert r.medium_confidence_count == 0
        assert r.low_confidence_count == 0
        assert r.average_confidence_score == 0.0
        assert r.hard_constraint_violations == 0
        assert r.soft_constraint_penalties_total == 0.0
        assert r.most_common_violations == []
        assert r.overrides_used == 0
        assert r.override_reasons == []
        assert r.fairness_score == 0.0
        assert r.workload_variance == 0.0
        assert r.max_assignment_delta == 0
        assert r.algorithm_used == ""
        assert r.solver_runtime_seconds == 0.0
        assert r.random_seed is None

    def test_populated(self):
        r = ExplainabilityReport(
            start_date=datetime(2026, 3, 1),
            end_date=datetime(2026, 3, 28),
            total_assignments=100,
            high_confidence_count=70,
            medium_confidence_count=25,
            low_confidence_count=5,
            average_confidence_score=0.82,
            fairness_score=0.91,
            algorithm_used="CP-SAT v2",
        )
        assert r.high_confidence_count == 70
        assert r.fairness_score == 0.91
