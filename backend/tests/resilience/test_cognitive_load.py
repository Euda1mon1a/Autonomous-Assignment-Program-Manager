"""Tests for Cognitive Load Management (psychology/human factors pattern)."""

from datetime import datetime, timedelta
from uuid import uuid4

from app.resilience.cognitive_load import (
    CognitiveLoadManager,
    CognitiveLoadReport,
    CognitiveSession,
    CognitiveState,
    Decision,
    DecisionCategory,
    DecisionComplexity,
    DecisionOutcome,
    DecisionQueueStatus,
)


# ==================== Enums ====================


class TestDecisionComplexity:
    def test_is_str_enum(self):
        assert isinstance(DecisionComplexity.TRIVIAL, str)

    def test_values(self):
        assert DecisionComplexity.TRIVIAL == "trivial"
        assert DecisionComplexity.SIMPLE == "simple"
        assert DecisionComplexity.MODERATE == "moderate"
        assert DecisionComplexity.COMPLEX == "complex"
        assert DecisionComplexity.STRATEGIC == "strategic"

    def test_count(self):
        assert len(DecisionComplexity) == 5


class TestDecisionCategory:
    def test_values(self):
        assert DecisionCategory.ASSIGNMENT == "assignment"
        assert DecisionCategory.SWAP == "swap"
        assert DecisionCategory.COVERAGE == "coverage"
        assert DecisionCategory.LEAVE == "leave"
        assert DecisionCategory.CONFLICT == "conflict"
        assert DecisionCategory.OVERRIDE == "override"
        assert DecisionCategory.POLICY == "policy"
        assert DecisionCategory.EMERGENCY == "emergency"

    def test_count(self):
        assert len(DecisionCategory) == 8


class TestCognitiveState:
    def test_values(self):
        assert CognitiveState.FRESH == "fresh"
        assert CognitiveState.ENGAGED == "engaged"
        assert CognitiveState.LOADED == "loaded"
        assert CognitiveState.FATIGUED == "fatigued"
        assert CognitiveState.DEPLETED == "depleted"

    def test_count(self):
        assert len(CognitiveState) == 5


class TestDecisionOutcome:
    def test_values(self):
        assert DecisionOutcome.DECIDED == "decided"
        assert DecisionOutcome.DEFERRED == "deferred"
        assert DecisionOutcome.AUTO_DEFAULT == "auto_default"
        assert DecisionOutcome.DELEGATED == "delegated"
        assert DecisionOutcome.CANCELLED == "cancelled"

    def test_count(self):
        assert len(DecisionOutcome) == 5


# ==================== Decision dataclass ====================


class TestDecision:
    def _make_decision(self, **overrides):
        defaults = {
            "id": uuid4(),
            "category": DecisionCategory.ASSIGNMENT,
            "complexity": DecisionComplexity.MODERATE,
            "description": "Assign coverage",
            "created_at": datetime.now(),
        }
        defaults.update(overrides)
        return Decision(**defaults)

    def test_required_fields(self):
        d = self._make_decision()
        assert d.category == DecisionCategory.ASSIGNMENT
        assert d.complexity == DecisionComplexity.MODERATE
        assert d.description == "Assign coverage"

    def test_defaults(self):
        d = self._make_decision()
        assert d.options == []
        assert d.recommended_option is None
        assert d.has_safe_default is False
        assert d.safe_default is None
        assert d.context == {}
        assert d.related_decisions == []
        assert d.deadline is None
        assert d.is_urgent is False
        assert d.can_defer is True
        assert d.outcome is None
        assert d.chosen_option is None
        assert d.decided_at is None
        assert d.decided_by is None
        assert d.estimated_cognitive_cost == 1.0
        assert d.actual_time_seconds is None

    def test_cognitive_cost_trivial(self):
        d = self._make_decision(complexity=DecisionComplexity.TRIVIAL)
        assert d.get_cognitive_cost() == 0.25

    def test_cognitive_cost_simple(self):
        d = self._make_decision(complexity=DecisionComplexity.SIMPLE)
        assert d.get_cognitive_cost() == 0.5

    def test_cognitive_cost_moderate(self):
        d = self._make_decision(complexity=DecisionComplexity.MODERATE)
        assert d.get_cognitive_cost() == 1.0

    def test_cognitive_cost_complex(self):
        d = self._make_decision(complexity=DecisionComplexity.COMPLEX)
        assert d.get_cognitive_cost() == 2.0

    def test_cognitive_cost_strategic(self):
        d = self._make_decision(complexity=DecisionComplexity.STRATEGIC)
        assert d.get_cognitive_cost() == 3.0

    def test_cognitive_cost_with_many_options(self):
        d = self._make_decision(
            complexity=DecisionComplexity.MODERATE,
            options=["A", "B", "C", "D", "E"],
        )
        # base=1.0, option_multiplier = 1.0 + (5-2)*0.1 = 1.3
        assert d.get_cognitive_cost() == 1.0 * 1.3

    def test_cognitive_cost_with_two_options(self):
        d = self._make_decision(
            complexity=DecisionComplexity.SIMPLE,
            options=["A", "B"],
        )
        # 2 options = multiplier 1.0
        assert d.get_cognitive_cost() == 0.5

    def test_cognitive_cost_with_recommendation(self):
        d = self._make_decision(
            complexity=DecisionComplexity.MODERATE,
            recommended_option="A",
        )
        # base=1.0, recommend_discount=0.8
        assert d.get_cognitive_cost() == 0.8

    def test_cognitive_cost_options_and_recommendation(self):
        d = self._make_decision(
            complexity=DecisionComplexity.COMPLEX,
            options=["A", "B", "C", "D"],
            recommended_option="A",
        )
        # base=2.0, option_multiplier=1.0+(4-2)*0.1=1.2, recommend_discount=0.8
        expected = 2.0 * 1.2 * 0.8
        assert abs(d.get_cognitive_cost() - expected) < 0.001


# ==================== CognitiveSession dataclass ====================


class TestCognitiveSession:
    def _make_session(self, **overrides):
        defaults = {
            "id": uuid4(),
            "user_id": uuid4(),
            "started_at": datetime.now(),
        }
        defaults.update(overrides)
        return CognitiveSession(**defaults)

    def _make_decision(self, complexity=DecisionComplexity.MODERATE):
        return Decision(
            id=uuid4(),
            category=DecisionCategory.ASSIGNMENT,
            complexity=complexity,
            description="Test",
            created_at=datetime.now(),
        )

    def test_defaults(self):
        s = self._make_session()
        assert s.max_decisions_before_break == 7
        assert s.break_duration_minutes == 15
        assert s.session_duration_minutes == 120
        assert s.decisions_made == []
        assert s.total_cognitive_cost == 0.0
        assert s.breaks_taken == 0
        assert s.last_break_at is None
        assert s.current_state == CognitiveState.FRESH
        assert s.ended_at is None

    def test_add_decision_updates_cost(self):
        s = self._make_session()
        d = self._make_decision(DecisionComplexity.MODERATE)
        s.add_decision(d)
        assert s.total_cognitive_cost == 1.0
        assert len(s.decisions_made) == 1

    def test_state_fresh_under_2(self):
        s = self._make_session()
        d = self._make_decision(DecisionComplexity.SIMPLE)  # cost 0.5
        s.add_decision(d)
        assert s.current_state == CognitiveState.FRESH

    def test_state_engaged_at_2(self):
        s = self._make_session()
        for _ in range(2):
            s.add_decision(self._make_decision(DecisionComplexity.MODERATE))
        # cost = 2.0 → ENGAGED (2 <= cost < 4)
        assert s.current_state == CognitiveState.ENGAGED

    def test_state_loaded_at_4(self):
        s = self._make_session()
        for _ in range(4):
            s.add_decision(self._make_decision(DecisionComplexity.MODERATE))
        # cost = 4.0 → LOADED
        assert s.current_state == CognitiveState.LOADED

    def test_state_fatigued_at_6(self):
        s = self._make_session()
        for _ in range(3):
            s.add_decision(self._make_decision(DecisionComplexity.COMPLEX))
        # cost = 6.0 → FATIGUED
        assert s.current_state == CognitiveState.FATIGUED

    def test_state_depleted_at_8(self):
        s = self._make_session()
        for _ in range(4):
            s.add_decision(self._make_decision(DecisionComplexity.COMPLEX))
        # cost = 8.0 → DEPLETED
        assert s.current_state == CognitiveState.DEPLETED

    def test_take_break_reduces_cost(self):
        s = self._make_session()
        for _ in range(4):
            s.add_decision(self._make_decision(DecisionComplexity.MODERATE))
        assert s.total_cognitive_cost == 4.0
        s.take_break()
        assert s.total_cognitive_cost == 1.0  # 4 - 3
        assert s.breaks_taken == 1
        assert s.last_break_at is not None

    def test_take_break_cost_floor_zero(self):
        s = self._make_session()
        s.add_decision(self._make_decision(DecisionComplexity.TRIVIAL))
        s.take_break()
        assert s.total_cognitive_cost == 0.0

    def test_decisions_until_break(self):
        s = self._make_session()
        assert s.decisions_until_break == 7
        s.add_decision(self._make_decision())
        assert s.decisions_until_break == 6

    def test_decisions_until_break_floor_zero(self):
        s = self._make_session()
        for _ in range(10):
            s.add_decision(self._make_decision())
        assert s.decisions_until_break == 0

    def test_should_take_break_when_fatigued(self):
        s = self._make_session()
        for _ in range(3):
            s.add_decision(self._make_decision(DecisionComplexity.COMPLEX))
        assert s.current_state == CognitiveState.FATIGUED
        assert s.should_take_break is True

    def test_should_take_break_when_max_reached(self):
        s = self._make_session(max_decisions_before_break=3)
        for _ in range(3):
            s.add_decision(self._make_decision(DecisionComplexity.TRIVIAL))
        assert s.should_take_break is True

    def test_should_not_take_break_when_fresh(self):
        s = self._make_session()
        assert s.should_take_break is False


# ==================== CognitiveLoadReport dataclass ====================


class TestCognitiveLoadReport:
    def test_fields(self):
        uid = uuid4()
        sid = uuid4()
        report = CognitiveLoadReport(
            user_id=uid,
            generated_at=datetime.now(),
            session_id=sid,
            current_state=CognitiveState.ENGAGED,
            decisions_this_session=3,
            cognitive_cost_this_session=2.5,
            remaining_capacity=0.75,
            decisions_until_break=4,
            should_take_break=False,
            decisions_today=5,
            total_sessions_today=2,
            average_decision_time=12.5,
            recommendations=["Keep going"],
        )
        assert report.user_id == uid
        assert report.session_id == sid
        assert report.current_state == CognitiveState.ENGAGED
        assert report.remaining_capacity == 0.75
        assert len(report.recommendations) == 1


class TestDecisionQueueStatus:
    def test_fields(self):
        status = DecisionQueueStatus(
            total_pending=5,
            by_complexity={"simple": 3, "complex": 2},
            by_category={"assignment": 5},
            urgent_count=1,
            can_auto_decide=2,
            oldest_pending=datetime.now(),
            estimated_cognitive_cost=6.0,
            recommendations=["Schedule focused time"],
        )
        assert status.total_pending == 5
        assert status.urgent_count == 1
        assert status.can_auto_decide == 2


# ==================== CognitiveLoadManager ====================


class TestCognitiveLoadManagerInit:
    def test_defaults(self):
        mgr = CognitiveLoadManager()
        assert mgr.max_decisions_per_session == 7
        assert mgr.auto_decide_when_fatigued is True
        assert mgr.batch_similar_decisions is True
        assert mgr.sessions == {}
        assert mgr.pending_decisions == []
        assert mgr.decision_history == []

    def test_custom(self):
        mgr = CognitiveLoadManager(
            max_decisions_per_session=5,
            auto_decide_when_fatigued=False,
            batch_similar_decisions=False,
        )
        assert mgr.max_decisions_per_session == 5
        assert mgr.auto_decide_when_fatigued is False


class TestStartEndSession:
    def test_start_session(self):
        mgr = CognitiveLoadManager()
        uid = uuid4()
        session = mgr.start_session(uid)
        assert isinstance(session, CognitiveSession)
        assert session.user_id == uid
        assert session.id in mgr.sessions

    def test_start_session_custom_max(self):
        mgr = CognitiveLoadManager()
        session = mgr.start_session(uuid4(), max_decisions=3)
        assert session.max_decisions_before_break == 3

    def test_end_session(self):
        mgr = CognitiveLoadManager()
        session = mgr.start_session(uuid4())
        assert session.ended_at is None
        mgr.end_session(session.id)
        assert session.ended_at is not None

    def test_end_nonexistent_session(self):
        mgr = CognitiveLoadManager()
        mgr.end_session(uuid4())  # Should not raise


class TestCreateDecision:
    def test_creates_decision(self):
        mgr = CognitiveLoadManager()
        d = mgr.create_decision(
            category=DecisionCategory.ASSIGNMENT,
            complexity=DecisionComplexity.SIMPLE,
            description="Who covers surgery?",
            options=["Dr. A", "Dr. B"],
        )
        assert isinstance(d, Decision)
        assert d.category == DecisionCategory.ASSIGNMENT
        assert d.description == "Who covers surgery?"
        assert len(d.options) == 2
        assert d in mgr.pending_decisions

    def test_with_safe_default(self):
        mgr = CognitiveLoadManager()
        d = mgr.create_decision(
            category=DecisionCategory.SWAP,
            complexity=DecisionComplexity.SIMPLE,
            description="Approve swap",
            options=["approve", "deny"],
            safe_default="approve",
            recommended_option="approve",
        )
        assert d.has_safe_default is True
        assert d.safe_default == "approve"
        assert d.recommended_option == "approve"

    def test_urgent_decision(self):
        mgr = CognitiveLoadManager()
        d = mgr.create_decision(
            category=DecisionCategory.EMERGENCY,
            complexity=DecisionComplexity.COMPLEX,
            description="Emergency coverage",
            options=["option1"],
            is_urgent=True,
        )
        assert d.is_urgent is True
        assert d.can_defer is False


class TestRequestDecision:
    def _setup_mgr_session(self):
        mgr = CognitiveLoadManager()
        session = mgr.start_session(uuid4())
        return mgr, session

    def test_normal_decision(self):
        mgr, session = self._setup_mgr_session()
        d = mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.SIMPLE,
            "Test",
            ["A", "B"],
        )
        choice, outcome = mgr.request_decision(session.id, d)
        assert outcome == DecisionOutcome.DECIDED

    def test_auto_decide_when_depleted(self):
        mgr, session = self._setup_mgr_session()
        # Deplete the session
        for _ in range(4):
            d = Decision(
                id=uuid4(),
                category=DecisionCategory.ASSIGNMENT,
                complexity=DecisionComplexity.COMPLEX,
                description="Heavy",
                created_at=datetime.now(),
            )
            session.add_decision(d)
        assert session.current_state == CognitiveState.DEPLETED

        decision = mgr.create_decision(
            DecisionCategory.SWAP,
            DecisionComplexity.SIMPLE,
            "Approve swap",
            ["approve", "deny"],
            safe_default="approve",
        )
        choice, outcome = mgr.request_decision(session.id, decision)
        assert outcome == DecisionOutcome.AUTO_DEFAULT
        assert choice == "approve"

    def test_defer_when_break_recommended(self):
        mgr, session = self._setup_mgr_session()
        # Make session fatigued
        for _ in range(3):
            d = Decision(
                id=uuid4(),
                category=DecisionCategory.ASSIGNMENT,
                complexity=DecisionComplexity.COMPLEX,
                description="Heavy",
                created_at=datetime.now(),
            )
            session.add_decision(d)
        assert session.should_take_break is True

        decision = mgr.create_decision(
            DecisionCategory.LEAVE,
            DecisionComplexity.SIMPLE,
            "Approve leave",
            ["approve", "defer"],
        )
        choice, outcome = mgr.request_decision(session.id, decision)
        assert outcome == DecisionOutcome.DEFERRED
        assert choice is None

    def test_invalid_session_raises(self):
        mgr = CognitiveLoadManager()
        d = mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.SIMPLE,
            "Test",
            ["A"],
        )
        try:
            mgr.request_decision(uuid4(), d)
            raise AssertionError("Should have raised ValueError")
        except ValueError:
            pass


class TestRecordDecision:
    def test_records_decision(self):
        mgr = CognitiveLoadManager()
        session = mgr.start_session(uuid4())
        d = mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.SIMPLE,
            "Test",
            ["A", "B"],
        )
        mgr.record_decision(session.id, d.id, "A", "user-1", actual_time_seconds=5.0)
        assert d.outcome == DecisionOutcome.DECIDED
        assert d.chosen_option == "A"
        assert d.decided_by == "user-1"
        assert d.actual_time_seconds == 5.0
        assert d not in mgr.pending_decisions
        assert d in mgr.decision_history
        assert len(session.decisions_made) == 1

    def test_records_without_session(self):
        mgr = CognitiveLoadManager()
        d = mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.SIMPLE,
            "Test",
            ["A"],
        )
        # Pass invalid session_id — should still record
        mgr.record_decision(uuid4(), d.id, "A", "user-1")
        assert d.outcome == DecisionOutcome.DECIDED
        assert d in mgr.decision_history


class TestGetSessionStatus:
    def test_returns_report(self):
        mgr = CognitiveLoadManager()
        session = mgr.start_session(uuid4())
        report = mgr.get_session_status(session.id)
        assert isinstance(report, CognitiveLoadReport)
        assert report.session_id == session.id
        assert report.current_state == CognitiveState.FRESH
        assert report.decisions_this_session == 0

    def test_returns_none_for_unknown(self):
        mgr = CognitiveLoadManager()
        assert mgr.get_session_status(uuid4()) is None

    def test_recommendations_when_fresh(self):
        mgr = CognitiveLoadManager()
        session = mgr.start_session(uuid4())
        report = mgr.get_session_status(session.id)
        assert any("good" in r.lower() for r in report.recommendations)

    def test_recommendations_when_depleted(self):
        mgr = CognitiveLoadManager()
        session = mgr.start_session(uuid4())
        for _ in range(4):
            d = Decision(
                id=uuid4(),
                category=DecisionCategory.ASSIGNMENT,
                complexity=DecisionComplexity.COMPLEX,
                description="Heavy",
                created_at=datetime.now(),
            )
            session.add_decision(d)
        report = mgr.get_session_status(session.id)
        assert any("break" in r.lower() for r in report.recommendations)

    def test_remaining_capacity(self):
        mgr = CognitiveLoadManager()
        session = mgr.start_session(uuid4())
        report = mgr.get_session_status(session.id)
        assert report.remaining_capacity > 0


class TestGetQueueStatus:
    def test_empty_queue(self):
        mgr = CognitiveLoadManager()
        status = mgr.get_queue_status()
        assert isinstance(status, DecisionQueueStatus)
        assert status.total_pending == 0
        assert status.urgent_count == 0
        assert status.can_auto_decide == 0
        assert status.oldest_pending is None

    def test_populated_queue(self):
        mgr = CognitiveLoadManager()
        mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.SIMPLE,
            "Test1",
            ["A"],
            is_urgent=True,
        )
        mgr.create_decision(
            DecisionCategory.SWAP,
            DecisionComplexity.MODERATE,
            "Test2",
            ["A", "B"],
            safe_default="A",
        )
        status = mgr.get_queue_status()
        assert status.total_pending == 2
        assert status.urgent_count == 1
        assert status.can_auto_decide == 1
        assert status.oldest_pending is not None
        assert "simple" in status.by_complexity
        assert "moderate" in status.by_complexity

    def test_recommendations_for_large_queue(self):
        mgr = CognitiveLoadManager()
        for i in range(12):
            mgr.create_decision(
                DecisionCategory.ASSIGNMENT,
                DecisionComplexity.SIMPLE,
                f"Decision {i}",
                ["A"],
            )
        status = mgr.get_queue_status()
        assert any("backlog" in r.lower() for r in status.recommendations)


class TestBatchSimilarDecisions:
    def test_groups_by_category(self):
        mgr = CognitiveLoadManager()
        mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.SIMPLE,
            "A1",
            ["x"],
        )
        mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.MODERATE,
            "A2",
            ["y"],
        )
        mgr.create_decision(
            DecisionCategory.SWAP,
            DecisionComplexity.SIMPLE,
            "S1",
            ["z"],
        )
        # Note: __init__ sets self.batch_similar_decisions = True (bool),
        # shadowing the method. Call via unbound method.
        batches = CognitiveLoadManager.batch_similar_decisions(mgr)
        assert DecisionCategory.ASSIGNMENT in batches
        assert len(batches[DecisionCategory.ASSIGNMENT]) == 2
        assert DecisionCategory.SWAP in batches
        assert len(batches[DecisionCategory.SWAP]) == 1

    def test_empty_queue(self):
        mgr = CognitiveLoadManager()
        assert CognitiveLoadManager.batch_similar_decisions(mgr) == {}


class TestPrioritizeDecisions:
    def test_urgent_first(self):
        mgr = CognitiveLoadManager()
        d1 = mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.MODERATE,
            "Normal",
            ["A"],
        )
        d2 = mgr.create_decision(
            DecisionCategory.EMERGENCY,
            DecisionComplexity.COMPLEX,
            "Urgent",
            ["B"],
            is_urgent=True,
        )
        prioritized = mgr.prioritize_decisions()
        assert prioritized[0].id == d2.id

    def test_simpler_before_complex(self):
        mgr = CognitiveLoadManager()
        d1 = mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.STRATEGIC,
            "Hard",
            ["A"],
        )
        d2 = mgr.create_decision(
            DecisionCategory.ASSIGNMENT,
            DecisionComplexity.TRIVIAL,
            "Easy",
            ["B"],
        )
        prioritized = mgr.prioritize_decisions()
        assert prioritized[0].id == d2.id

    def test_empty_queue(self):
        mgr = CognitiveLoadManager()
        assert mgr.prioritize_decisions() == []


class TestScheduleCognitiveLoad:
    def test_empty_changes(self):
        mgr = CognitiveLoadManager()
        result = mgr.calculate_schedule_cognitive_load([])
        assert result["total_score"] == 0.0
        assert result["grade"] == "A"

    def test_low_load(self):
        mgr = CognitiveLoadManager()
        changes = [{"type": "assignment"}] * 5
        result = mgr.calculate_schedule_cognitive_load(changes)
        assert result["grade"] in ("A", "B")

    def test_high_load_with_conflicts(self):
        mgr = CognitiveLoadManager()
        changes = [{"type": "conflict"}] * 10
        result = mgr.calculate_schedule_cognitive_load(changes)
        # base = 10 * 0.5 = 5, conflicts = 10 * 2.0 = 20, total = 25
        assert result["grade"] == "D"
        assert result["factors"]["conflicts"] == 10

    def test_excessive_load(self):
        mgr = CognitiveLoadManager()
        changes = [{"type": "conflict"}] * 20
        result = mgr.calculate_schedule_cognitive_load(changes)
        assert result["grade"] == "F"

    def test_mixed_changes(self):
        mgr = CognitiveLoadManager()
        changes = [
            {"type": "exception_added"},
            {"type": "override_rule"},
            {"type": "cross_coverage_needed"},
            {"type": "normal_change"},
        ]
        result = mgr.calculate_schedule_cognitive_load(changes)
        assert result["factors"]["exceptions"] == 1
        assert result["factors"]["overrides"] == 1
        assert result["factors"]["cross_coverage"] == 1

    def test_recommendations_many_exceptions(self):
        mgr = CognitiveLoadManager()
        changes = [{"type": "exception"}] * 7
        result = mgr.calculate_schedule_cognitive_load(changes)
        assert any("exception" in r.lower() for r in result["recommendations"])


class TestRegisterHandlers:
    def test_register_default_handler(self):
        mgr = CognitiveLoadManager()

        def handler(d):
            return "approve"

        mgr.register_default_handler(DecisionCategory.SWAP, handler)
        assert DecisionCategory.SWAP in mgr._default_handlers

    def test_register_state_handler(self):
        mgr = CognitiveLoadManager()

        def handler(s):
            return None

        mgr.register_state_handler(handler)
        assert len(mgr._on_state_change) == 1


class TestDecisionTemplates:
    def test_returns_templates(self):
        mgr = CognitiveLoadManager()
        templates = mgr.get_decision_templates()
        assert DecisionCategory.SWAP in templates
        assert DecisionCategory.LEAVE in templates
        assert DecisionCategory.COVERAGE in templates
        assert DecisionCategory.CONFLICT in templates
        assert DecisionCategory.OVERRIDE in templates
        assert DecisionCategory.EMERGENCY in templates

    def test_swap_template_has_safe_default(self):
        mgr = CognitiveLoadManager()
        templates = mgr.get_decision_templates()
        swap = templates[DecisionCategory.SWAP]
        assert swap["safe_default"] == "approve"
        assert swap["recommended_option"] == "approve"

    def test_emergency_has_no_safe_default(self):
        mgr = CognitiveLoadManager()
        templates = mgr.get_decision_templates()
        emergency = templates[DecisionCategory.EMERGENCY]
        assert emergency["safe_default"] is None
