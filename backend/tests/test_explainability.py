"""
Tests for scheduler explainability features.

Tests cover:
- ExplainabilityService
- DecisionExplanation generation
- Confidence calculation
- Alternative candidate tracking
- Audit hash computation
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.scheduling.constraints import (
    ConstraintManager,
    SchedulingContext,
)
from app.scheduling.explainability import (
    ExplainabilityService,
    compute_audit_hash,
)
from app.scheduling.solvers import GreedySolver
from app.schemas.explainability import (
    ConfidenceLevel,
    ConstraintStatus,
    DecisionExplanation,
)

# ============================================================================
# Test Fixtures
# ============================================================================


class MockPerson:
    """Mock person for testing."""

    def __init__(
        self, id=None, name="Test Person", person_type="resident", pgy_level=1
    ):
        self.id = id or uuid4()
        self.name = name
        self.type = person_type
        self.pgy_level = pgy_level


class MockBlock:
    """Mock block for testing."""

    def __init__(self, id=None, block_date=None, time_of_day="AM", is_weekend=False):
        self.id = id or uuid4()
        self.date = block_date or date.today()
        self.time_of_day = time_of_day
        self.is_weekend = is_weekend


class MockTemplate:
    """Mock rotation template for testing."""

    def __init__(
        self,
        id=None,
        name="Test Rotation",
        max_residents=None,
        requires_procedure_credential=False,
    ):
        self.id = id or uuid4()
        self.name = name
        self.max_residents = max_residents
        self.requires_procedure_credential = requires_procedure_credential


@pytest.fixture
def explainability_context():
    """Create a context for explainability tests."""
    residents = [
        MockPerson(name=f"Resident {i}", pgy_level=(i % 3) + 1) for i in range(5)
    ]
    faculty = [MockPerson(name="Faculty 1", person_type="faculty", pgy_level=None)]

    start_date = date(2024, 1, 1)
    blocks = []
    for day_offset in range(5):
        block_date = start_date + timedelta(days=day_offset)
        for tod in ["AM", "PM"]:
            blocks.append(
                MockBlock(
                    block_date=block_date,
                    time_of_day=tod,
                    is_weekend=False,
                )
            )

    templates = [MockTemplate(name="Clinic")]

    context = SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=blocks,
        templates=templates,
        start_date=start_date,
        end_date=start_date + timedelta(days=4),
    )

    # Set all as available
    for r in residents:
        context.availability[r.id] = {}
        for b in blocks:
            context.availability[r.id][b.id] = {"available": True, "replacement": None}

    return context


@pytest.fixture
def constraint_manager():
    """Create a constraint manager for tests."""
    return ConstraintManager.create_default()


# ============================================================================
# ExplainabilityService Tests
# ============================================================================


class TestExplainabilityService:
    """Tests for ExplainabilityService."""

    def test_service_initialization(self, explainability_context, constraint_manager):
        """Test service initialization."""
        service = ExplainabilityService(
            context=explainability_context,
            constraint_manager=constraint_manager,
            algorithm="greedy",
        )

        assert service.algorithm == "greedy"
        assert service.context is explainability_context
        assert len(service._person_names) == 6  # 5 residents + 1 faculty

    def test_explain_assignment_returns_explanation(
        self, explainability_context, constraint_manager
    ):
        """Test that explain_assignment returns a valid explanation."""
        service = ExplainabilityService(
            context=explainability_context,
            constraint_manager=constraint_manager,
            algorithm="greedy",
        )

        selected = explainability_context.residents[0]
        block = explainability_context.blocks[0]
        template = explainability_context.templates[0]
        all_candidates = explainability_context.residents
        candidate_scores = {r.id: 100 - i * 10 for i, r in enumerate(all_candidates)}
        assignment_counts = {r.id: 0 for r in all_candidates}

        explanation = service.explain_assignment(
            selected_person=selected,
            block=block,
            template=template,
            all_candidates=all_candidates,
            candidate_scores=candidate_scores,
            assignment_counts=assignment_counts,
        )

        assert explanation.person_id == selected.id
        assert explanation.person_name == selected.name
        assert explanation.inputs.block_id == block.id
        assert explanation.inputs.rotation_name == template.name
        assert explanation.confidence in [
            ConfidenceLevel.HIGH,
            ConfidenceLevel.MEDIUM,
            ConfidenceLevel.LOW,
        ]

    def test_explain_assignment_includes_alternatives(
        self, explainability_context, constraint_manager
    ):
        """Test that explanation includes alternative candidates."""
        service = ExplainabilityService(
            context=explainability_context,
            constraint_manager=constraint_manager,
            algorithm="greedy",
        )

        selected = explainability_context.residents[0]
        block = explainability_context.blocks[0]
        template = explainability_context.templates[0]
        all_candidates = explainability_context.residents
        candidate_scores = {r.id: 100 - i * 10 for i, r in enumerate(all_candidates)}
        assignment_counts = {r.id: 0 for r in all_candidates}

        explanation = service.explain_assignment(
            selected_person=selected,
            block=block,
            template=template,
            all_candidates=all_candidates,
            candidate_scores=candidate_scores,
            assignment_counts=assignment_counts,
        )

        # Should include up to 3 alternatives
        assert len(explanation.alternatives) <= 3
        # Alternatives should not include the selected person
        for alt in explanation.alternatives:
            assert alt.person_id != selected.id

    def test_explain_assignment_evaluates_constraints(
        self, explainability_context, constraint_manager
    ):
        """Test that explanation includes constraint evaluations."""
        service = ExplainabilityService(
            context=explainability_context,
            constraint_manager=constraint_manager,
            algorithm="greedy",
        )

        selected = explainability_context.residents[0]
        block = explainability_context.blocks[0]
        template = explainability_context.templates[0]
        all_candidates = [selected]
        candidate_scores = {selected.id: 100}
        assignment_counts = {selected.id: 0}

        explanation = service.explain_assignment(
            selected_person=selected,
            block=block,
            template=template,
            all_candidates=all_candidates,
            candidate_scores=candidate_scores,
            assignment_counts=assignment_counts,
        )

        # Should have constraint evaluations
        assert len(explanation.constraints_evaluated) > 0

        # Should have at least availability constraint
        constraint_names = [
            c.constraint_name for c in explanation.constraints_evaluated
        ]
        assert "Availability" in constraint_names

    def test_explain_assignment_unavailable_resident(
        self, explainability_context, constraint_manager
    ):
        """Test explanation for unavailable resident shows violation."""
        # Mark first resident as unavailable
        resident = explainability_context.residents[0]
        block = explainability_context.blocks[0]
        explainability_context.availability[resident.id][block.id] = {
            "available": False,
            "replacement": "Leave",
        }

        service = ExplainabilityService(
            context=explainability_context,
            constraint_manager=constraint_manager,
            algorithm="greedy",
        )

        template = explainability_context.templates[0]
        all_candidates = [resident]
        candidate_scores = {resident.id: 100}
        assignment_counts = {resident.id: 0}

        explanation = service.explain_assignment(
            selected_person=resident,
            block=block,
            template=template,
            all_candidates=all_candidates,
            candidate_scores=candidate_scores,
            assignment_counts=assignment_counts,
        )

        # Should show availability violation
        availability_constraint = next(
            (
                c
                for c in explanation.constraints_evaluated
                if c.constraint_name == "Availability"
            ),
            None,
        )
        assert availability_constraint is not None
        assert availability_constraint.status == ConstraintStatus.VIOLATED
        assert explanation.hard_constraints_satisfied is False

    def test_explain_assignment_generates_trade_off_summary(
        self, explainability_context, constraint_manager
    ):
        """Test that explanation includes trade-off summary."""
        service = ExplainabilityService(
            context=explainability_context,
            constraint_manager=constraint_manager,
            algorithm="greedy",
        )

        selected = explainability_context.residents[0]
        block = explainability_context.blocks[0]
        template = explainability_context.templates[0]
        all_candidates = explainability_context.residents
        candidate_scores = {r.id: 100 - i * 10 for i, r in enumerate(all_candidates)}
        assignment_counts = {r.id: i for i, r in enumerate(all_candidates)}

        explanation = service.explain_assignment(
            selected_person=selected,
            block=block,
            template=template,
            all_candidates=all_candidates,
            candidate_scores=candidate_scores,
            assignment_counts=assignment_counts,
        )

        # Should have a non-empty trade-off summary
        assert explanation.trade_off_summary
        assert selected.name in explanation.trade_off_summary
        assert template.name in explanation.trade_off_summary


# ============================================================================
# Confidence Calculation Tests
# ============================================================================


class TestConfidenceCalculation:
    """Tests for confidence calculation."""

    def test_high_confidence_with_large_margin(
        self, explainability_context, constraint_manager
    ):
        """Test that large margin produces high confidence."""
        service = ExplainabilityService(
            context=explainability_context,
            constraint_manager=constraint_manager,
            algorithm="greedy",
        )

        selected = explainability_context.residents[0]
        block = explainability_context.blocks[0]
        template = explainability_context.templates[0]
        all_candidates = explainability_context.residents

        # Give selected a much higher score
        candidate_scores = {r.id: 10 for r in all_candidates}
        candidate_scores[selected.id] = 500  # Large margin
        assignment_counts = {r.id: 0 for r in all_candidates}

        explanation = service.explain_assignment(
            selected_person=selected,
            block=block,
            template=template,
            all_candidates=all_candidates,
            candidate_scores=candidate_scores,
            assignment_counts=assignment_counts,
        )

        assert explanation.confidence == ConfidenceLevel.HIGH
        assert explanation.confidence_score >= 0.7

    def test_single_candidate_increases_confidence(
        self, explainability_context, constraint_manager
    ):
        """Test that single candidate increases confidence."""
        service = ExplainabilityService(
            context=explainability_context,
            constraint_manager=constraint_manager,
            algorithm="greedy",
        )

        selected = explainability_context.residents[0]
        block = explainability_context.blocks[0]
        template = explainability_context.templates[0]
        all_candidates = [selected]  # Only one candidate
        candidate_scores = {selected.id: 100}
        assignment_counts = {selected.id: 0}

        explanation = service.explain_assignment(
            selected_person=selected,
            block=block,
            template=template,
            all_candidates=all_candidates,
            candidate_scores=candidate_scores,
            assignment_counts=assignment_counts,
        )

        # Single candidate should boost confidence
        assert explanation.confidence_score >= 0.6


# ============================================================================
# Greedy Solver Explainability Tests
# ============================================================================


class TestGreedySolverExplainability:
    """Tests for greedy solver explainability integration."""

    def test_greedy_solver_generates_explanations(self, explainability_context):
        """Test that greedy solver generates explanations for assignments."""
        solver = GreedySolver(generate_explanations=True)
        result = solver.solve(explainability_context)

        assert result.success is True
        assert len(result.assignments) > 0

        # Should have explanations for each assignment
        assert len(result.explanations) == len(result.assignments)

    def test_greedy_solver_explanations_contain_required_fields(
        self, explainability_context
    ):
        """Test that explanations contain all required fields."""
        solver = GreedySolver(generate_explanations=True)
        result = solver.solve(explainability_context)

        for key, explanation in result.explanations.items():
            person_id, block_id = key

            # Check required fields
            assert "person_id" in explanation
            assert "person_name" in explanation
            assert "inputs" in explanation
            assert "confidence" in explanation
            assert "confidence_score" in explanation
            assert "trade_off_summary" in explanation
            assert "alternatives" in explanation

    def test_greedy_solver_can_disable_explanations(self, explainability_context):
        """Test that explanations can be disabled."""
        solver = GreedySolver(generate_explanations=False)
        result = solver.solve(explainability_context)

        assert result.success is True
        assert len(result.explanations) == 0

    def test_greedy_solver_statistics_include_confidence_distribution(
        self, explainability_context
    ):
        """Test that solver statistics include confidence distribution."""
        solver = GreedySolver(generate_explanations=True)
        result = solver.solve(explainability_context)

        # Check statistics include confidence counts
        assert "high_confidence_assignments" in result.statistics
        assert "medium_confidence_assignments" in result.statistics
        assert "low_confidence_assignments" in result.statistics

        # Total should match assignments
        total_conf = (
            result.statistics["high_confidence_assignments"]
            + result.statistics["medium_confidence_assignments"]
            + result.statistics["low_confidence_assignments"]
        )
        assert total_conf == len(result.assignments)


# ============================================================================
# Audit Hash Tests
# ============================================================================


class TestAuditHash:
    """Tests for audit hash computation."""

    def test_compute_audit_hash_returns_valid_hash(self):
        """Test that compute_audit_hash returns a valid SHA-256 hash."""
        hash_value = compute_audit_hash(
            person_id=uuid4(),
            block_id=uuid4(),
            template_id=uuid4(),
            score=100.0,
            algorithm="greedy",
            timestamp=datetime.utcnow(),
        )

        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_audit_hash_is_deterministic(self):
        """Test that same inputs produce same hash."""
        person_id = uuid4()
        block_id = uuid4()
        template_id = uuid4()
        timestamp = datetime(2024, 1, 1, 12, 0, 0)

        hash1 = compute_audit_hash(
            person_id=person_id,
            block_id=block_id,
            template_id=template_id,
            score=100.0,
            algorithm="greedy",
            timestamp=timestamp,
        )

        hash2 = compute_audit_hash(
            person_id=person_id,
            block_id=block_id,
            template_id=template_id,
            score=100.0,
            algorithm="greedy",
            timestamp=timestamp,
        )

        assert hash1 == hash2

    def test_audit_hash_differs_with_different_inputs(self):
        """Test that different inputs produce different hashes."""
        person_id = uuid4()
        block_id = uuid4()
        template_id = uuid4()
        timestamp = datetime.utcnow()

        hash1 = compute_audit_hash(
            person_id=person_id,
            block_id=block_id,
            template_id=template_id,
            score=100.0,
            algorithm="greedy",
            timestamp=timestamp,
        )

        hash2 = compute_audit_hash(
            person_id=person_id,
            block_id=block_id,
            template_id=template_id,
            score=200.0,  # Different score
            algorithm="greedy",
            timestamp=timestamp,
        )

        assert hash1 != hash2

    def test_audit_hash_handles_none_template(self):
        """Test that hash works with None template_id."""
        hash_value = compute_audit_hash(
            person_id=uuid4(),
            block_id=uuid4(),
            template_id=None,
            score=100.0,
            algorithm="greedy",
            timestamp=datetime.utcnow(),
        )

        assert hash_value is not None
        assert len(hash_value) == 64


# ============================================================================
# Schema Tests
# ============================================================================


class TestExplainabilitySchemas:
    """Tests for explainability Pydantic schemas."""

    def test_decision_explanation_serialization(self):
        """Test that DecisionExplanation can be serialized."""
        from app.schemas.explainability import DecisionInputs

        explanation = DecisionExplanation(
            person_id=uuid4(),
            person_name="Test Person",
            inputs=DecisionInputs(
                block_id=uuid4(),
                block_date=datetime.utcnow(),
                block_time_of_day="AM",
                eligible_residents=5,
            ),
            score=100.0,
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.85,
            trade_off_summary="Test summary",
        )

        # Should serialize to dict
        data = explanation.model_dump()
        assert data["person_name"] == "Test Person"
        assert data["confidence"] == "high"
        assert data["confidence_score"] == 0.85

    def test_alternative_candidate_serialization(self):
        """Test that AlternativeCandidate can be serialized."""
        from app.schemas.explainability import AlternativeCandidate

        alt = AlternativeCandidate(
            person_id=uuid4(),
            person_name="Alternative Person",
            score=80.0,
            rejection_reasons=["Lower score", "Higher workload"],
            constraint_violations=[],
        )

        data = alt.model_dump()
        assert data["person_name"] == "Alternative Person"
        assert len(data["rejection_reasons"]) == 2
