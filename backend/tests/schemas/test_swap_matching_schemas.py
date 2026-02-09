"""Tests for swap matching schemas (Pydantic validation and enum coverage)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.swap_matching import (
    MatchPriority,
    MatchType,
    SwapMatch,
    ScoringBreakdown,
    RankedMatch,
    AutoMatchResult,
    BatchAutoMatchResult,
    MatchingCriteria,
    MatchingSuggestion,
    MatchingAnalytics,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestMatchPriority:
    def test_values(self):
        assert MatchPriority.CRITICAL.value == "critical"
        assert MatchPriority.HIGH.value == "high"
        assert MatchPriority.MEDIUM.value == "medium"
        assert MatchPriority.LOW.value == "low"

    def test_count(self):
        assert len(MatchPriority) == 4

    def test_is_str(self):
        assert isinstance(MatchPriority.CRITICAL, str)


class TestMatchType:
    def test_values(self):
        assert MatchType.MUTUAL.value == "mutual"
        assert MatchType.ONE_WAY.value == "one_way"
        assert MatchType.ABSORB.value == "absorb"

    def test_count(self):
        assert len(MatchType) == 3


# ===========================================================================
# SwapMatch Tests
# ===========================================================================


class TestSwapMatch:
    def _valid_kwargs(self):
        return {
            "match_id": uuid4(),
            "request_a_id": uuid4(),
            "request_b_id": uuid4(),
            "faculty_a_id": uuid4(),
            "faculty_a_name": "Dr. Alpha",
            "faculty_b_id": uuid4(),
            "faculty_b_name": "Dr. Beta",
            "week_a": date(2026, 3, 2),
            "week_b": date(2026, 3, 9),
            "match_type": MatchType.MUTUAL,
            "is_mutual": True,
        }

    def test_valid(self):
        m = SwapMatch(**self._valid_kwargs())
        assert m.is_mutual is True
        assert m.created_at is not None

    def test_all_fields_populated(self):
        m = SwapMatch(**self._valid_kwargs())
        assert m.faculty_a_name == "Dr. Alpha"
        assert m.match_type == MatchType.MUTUAL


# ===========================================================================
# ScoringBreakdown Tests
# ===========================================================================


class TestScoringBreakdown:
    def _valid_kwargs(self):
        return {
            "date_proximity_score": 0.8,
            "preference_alignment_score": 0.9,
            "workload_balance_score": 0.7,
            "history_score": 0.6,
            "availability_score": 1.0,
            "blocking_penalty": 1.0,
            "total_score": 0.85,
        }

    def test_valid(self):
        s = ScoringBreakdown(**self._valid_kwargs())
        assert s.total_score == 0.85

    def test_all_scores_bounded_zero(self):
        kw = self._valid_kwargs()
        for field in [
            "date_proximity_score",
            "preference_alignment_score",
            "workload_balance_score",
            "history_score",
            "availability_score",
            "blocking_penalty",
            "total_score",
        ]:
            kw_bad = {**kw, field: -0.1}
            with pytest.raises(ValidationError):
                ScoringBreakdown(**kw_bad)

    def test_all_scores_bounded_one(self):
        kw = self._valid_kwargs()
        for field in [
            "date_proximity_score",
            "preference_alignment_score",
            "workload_balance_score",
            "history_score",
            "availability_score",
            "blocking_penalty",
            "total_score",
        ]:
            kw_bad = {**kw, field: 1.1}
            with pytest.raises(ValidationError):
                ScoringBreakdown(**kw_bad)

    def test_boundary_zero(self):
        kw = dict.fromkeys(self._valid_kwargs(), 0.0)
        s = ScoringBreakdown(**kw)
        assert s.total_score == 0.0

    def test_boundary_one(self):
        kw = dict.fromkeys(self._valid_kwargs(), 1.0)
        s = ScoringBreakdown(**kw)
        assert s.total_score == 1.0


# ===========================================================================
# RankedMatch Tests
# ===========================================================================


class TestRankedMatch:
    def _make_scoring(self):
        return ScoringBreakdown(
            date_proximity_score=0.8,
            preference_alignment_score=0.9,
            workload_balance_score=0.7,
            history_score=0.6,
            availability_score=1.0,
            blocking_penalty=1.0,
            total_score=0.85,
        )

    def _make_swap_match(self):
        return SwapMatch(
            match_id=uuid4(),
            request_a_id=uuid4(),
            request_b_id=uuid4(),
            faculty_a_id=uuid4(),
            faculty_a_name="Dr. A",
            faculty_b_id=uuid4(),
            faculty_b_name="Dr. B",
            week_a=date(2026, 3, 2),
            week_b=date(2026, 3, 9),
            match_type=MatchType.MUTUAL,
            is_mutual=True,
        )

    def test_valid(self):
        r = RankedMatch(
            match=self._make_swap_match(),
            compatibility_score=0.85,
            priority=MatchPriority.HIGH,
            scoring_breakdown=self._make_scoring(),
            explanation="Strong mutual preference alignment",
            estimated_acceptance_probability=0.9,
            recommended_action="Notify both parties",
        )
        assert r.warnings == []
        assert r.compatibility_score == 0.85

    def test_compatibility_score_above_one(self):
        with pytest.raises(ValidationError):
            RankedMatch(
                match=self._make_swap_match(),
                compatibility_score=1.5,
                priority=MatchPriority.HIGH,
                scoring_breakdown=self._make_scoring(),
                explanation="Test",
                estimated_acceptance_probability=0.9,
                recommended_action="Test",
            )

    def test_acceptance_probability_below_zero(self):
        with pytest.raises(ValidationError):
            RankedMatch(
                match=self._make_swap_match(),
                compatibility_score=0.5,
                priority=MatchPriority.LOW,
                scoring_breakdown=self._make_scoring(),
                explanation="Test",
                estimated_acceptance_probability=-0.1,
                recommended_action="Test",
            )


# ===========================================================================
# AutoMatchResult Tests
# ===========================================================================


class TestAutoMatchResult:
    def test_valid(self):
        r = AutoMatchResult(
            request_id=uuid4(),
            faculty_id=uuid4(),
            source_week=date(2026, 3, 2),
            matches_found=0,
            success=False,
            message="No compatible matches found",
        )
        assert r.target_week is None
        assert r.best_match is None
        assert r.all_matches == []

    def test_matches_found_negative(self):
        with pytest.raises(ValidationError):
            AutoMatchResult(
                request_id=uuid4(),
                faculty_id=uuid4(),
                source_week=date(2026, 3, 2),
                matches_found=-1,
                success=False,
                message="Test",
            )


# ===========================================================================
# BatchAutoMatchResult Tests
# ===========================================================================


class TestBatchAutoMatchResult:
    def test_valid(self):
        r = BatchAutoMatchResult(
            total_requests_processed=10,
            total_matches_found=7,
            execution_time_seconds=1.5,
        )
        assert r.successful_matches == []
        assert r.no_matches == []
        assert r.high_priority_matches == []

    def test_counts_negative(self):
        with pytest.raises(ValidationError):
            BatchAutoMatchResult(
                total_requests_processed=-1,
                total_matches_found=0,
                execution_time_seconds=0.0,
            )

    def test_execution_time_negative(self):
        with pytest.raises(ValidationError):
            BatchAutoMatchResult(
                total_requests_processed=0,
                total_matches_found=0,
                execution_time_seconds=-1.0,
            )


# ===========================================================================
# MatchingCriteria Tests
# ===========================================================================


class TestMatchingCriteria:
    def test_defaults(self):
        c = MatchingCriteria()
        assert c.date_proximity_weight == 0.20
        assert c.preference_alignment_weight == 0.35
        assert c.workload_balance_weight == 0.15
        assert c.history_weight == 0.15
        assert c.availability_weight == 0.15
        assert c.minimum_score_threshold == 0.4
        assert c.high_priority_threshold == 0.75
        assert c.max_matches_per_request == 5
        assert c.max_date_separation_days == 90
        assert c.require_mutual_availability is True
        assert c.exclude_blocked_weeks is True
        assert c.consider_past_rejections is True
        assert c.history_lookback_days == 365

    def test_total_weight_property(self):
        c = MatchingCriteria()
        assert abs(c.total_weight - 1.0) < 0.01

    def test_weight_above_one(self):
        with pytest.raises(ValidationError):
            MatchingCriteria(date_proximity_weight=1.5)

    def test_weight_negative(self):
        with pytest.raises(ValidationError):
            MatchingCriteria(preference_alignment_weight=-0.1)

    def test_threshold_boundaries(self):
        c = MatchingCriteria(minimum_score_threshold=0.0)
        assert c.minimum_score_threshold == 0.0
        c = MatchingCriteria(minimum_score_threshold=1.0)
        assert c.minimum_score_threshold == 1.0

    def test_threshold_above_one(self):
        with pytest.raises(ValidationError):
            MatchingCriteria(minimum_score_threshold=1.1)

    def test_max_matches_boundaries(self):
        c = MatchingCriteria(max_matches_per_request=1)
        assert c.max_matches_per_request == 1
        c = MatchingCriteria(max_matches_per_request=20)
        assert c.max_matches_per_request == 20

    def test_max_matches_zero(self):
        with pytest.raises(ValidationError):
            MatchingCriteria(max_matches_per_request=0)

    def test_max_matches_above_max(self):
        with pytest.raises(ValidationError):
            MatchingCriteria(max_matches_per_request=21)

    def test_max_date_separation_boundaries(self):
        c = MatchingCriteria(max_date_separation_days=1)
        assert c.max_date_separation_days == 1
        c = MatchingCriteria(max_date_separation_days=365)
        assert c.max_date_separation_days == 365

    def test_max_date_separation_zero(self):
        with pytest.raises(ValidationError):
            MatchingCriteria(max_date_separation_days=0)

    def test_history_lookback_boundaries(self):
        c = MatchingCriteria(history_lookback_days=1)
        assert c.history_lookback_days == 1
        c = MatchingCriteria(history_lookback_days=1825)
        assert c.history_lookback_days == 1825

    def test_history_lookback_above_max(self):
        with pytest.raises(ValidationError):
            MatchingCriteria(history_lookback_days=1826)

    def test_custom_weights(self):
        c = MatchingCriteria(
            date_proximity_weight=0.5,
            preference_alignment_weight=0.2,
            workload_balance_weight=0.1,
            history_weight=0.1,
            availability_weight=0.1,
        )
        assert abs(c.total_weight - 1.0) < 0.01


# ===========================================================================
# MatchingSuggestion Tests
# ===========================================================================


class TestMatchingSuggestion:
    def test_valid(self):
        s = MatchingSuggestion(
            faculty_id=uuid4(),
            faculty_name="Dr. Alpha",
            current_week=date(2026, 3, 2),
            suggested_partner_id=uuid4(),
            suggested_partner_name="Dr. Beta",
            partner_week=date(2026, 3, 9),
            benefit_score=0.85,
            reason="Both prefer the other's week",
            action_text="Consider swapping weeks with Dr. Beta",
        )
        assert s.benefit_score == 0.85

    def test_benefit_score_above_one(self):
        with pytest.raises(ValidationError):
            MatchingSuggestion(
                faculty_id=uuid4(),
                faculty_name="Dr. A",
                current_week=date(2026, 3, 2),
                suggested_partner_id=uuid4(),
                suggested_partner_name="Dr. B",
                partner_week=date(2026, 3, 9),
                benefit_score=1.5,
                reason="Test",
                action_text="Test",
            )

    def test_benefit_score_negative(self):
        with pytest.raises(ValidationError):
            MatchingSuggestion(
                faculty_id=uuid4(),
                faculty_name="Dr. A",
                current_week=date(2026, 3, 2),
                suggested_partner_id=uuid4(),
                suggested_partner_name="Dr. B",
                partner_week=date(2026, 3, 9),
                benefit_score=-0.1,
                reason="Test",
                action_text="Test",
            )


# ===========================================================================
# MatchingAnalytics Tests
# ===========================================================================


class TestMatchingAnalytics:
    def test_valid(self):
        a = MatchingAnalytics(
            date_range_start=date(2026, 1, 1),
            date_range_end=date(2026, 3, 31),
            total_requests=50,
            successful_matches=35,
            failed_matches=15,
            average_match_score=0.75,
            average_time_to_match_days=3.5,
        )
        assert a.top_scoring_factors == {}
        assert a.common_blocking_reasons == []

    def test_counts_negative(self):
        with pytest.raises(ValidationError):
            MatchingAnalytics(
                date_range_start=date(2026, 1, 1),
                date_range_end=date(2026, 3, 31),
                total_requests=-1,
                successful_matches=0,
                failed_matches=0,
                average_match_score=0.0,
                average_time_to_match_days=0.0,
            )

    def test_average_score_above_one(self):
        with pytest.raises(ValidationError):
            MatchingAnalytics(
                date_range_start=date(2026, 1, 1),
                date_range_end=date(2026, 3, 31),
                total_requests=10,
                successful_matches=5,
                failed_matches=5,
                average_match_score=1.1,
                average_time_to_match_days=2.0,
            )

    def test_time_to_match_negative(self):
        with pytest.raises(ValidationError):
            MatchingAnalytics(
                date_range_start=date(2026, 1, 1),
                date_range_end=date(2026, 3, 31),
                total_requests=10,
                successful_matches=5,
                failed_matches=5,
                average_match_score=0.5,
                average_time_to_match_days=-1.0,
            )
