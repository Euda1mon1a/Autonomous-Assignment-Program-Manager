"""Tests for wellness_service.py pure functions.

Covers _interpret_score, _calculate_score, and get_achievement_info
without requiring a database.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.models.wellness import AchievementType
from app.services.wellness_service import (
    ACHIEVEMENT_DEFINITIONS,
    WellnessService,
)


def _make_service() -> WellnessService:
    """Create a WellnessService with a mock db session."""
    return WellnessService(db=MagicMock())


def _make_survey(
    survey_type: str = "burnout",
    questions_json: list | None = None,
    scoring_json: dict | None = None,
) -> SimpleNamespace:
    """Create a minimal Survey-like object for testing."""
    return SimpleNamespace(
        survey_type=survey_type,
        questions_json=questions_json,
        scoring_json=scoring_json,
    )


def _make_account(
    achievements: list[str] | None = None,
    earned_at: dict | None = None,
) -> SimpleNamespace:
    """Create a minimal WellnessAccount-like object for testing."""
    return SimpleNamespace(
        achievements_json=achievements or [],
        achievements_earned_at_json=earned_at or {},
    )


# ── _interpret_score ─────────────────────────────────────────────────────


class TestInterpretScore:
    """Test score interpretation thresholds."""

    svc = _make_service()

    # Burnout: <=6 low, <=9 moderate, >9 high
    def test_burnout_low(self):
        assert self.svc._interpret_score("burnout", 3) == "low"

    def test_burnout_low_boundary(self):
        assert self.svc._interpret_score("burnout", 6) == "low"

    def test_burnout_moderate(self):
        assert self.svc._interpret_score("burnout", 7) == "moderate"

    def test_burnout_moderate_boundary(self):
        assert self.svc._interpret_score("burnout", 9) == "moderate"

    def test_burnout_high(self):
        assert self.svc._interpret_score("burnout", 10) == "high"

    def test_burnout_high_extreme(self):
        assert self.svc._interpret_score("burnout", 100) == "high"

    # Stress: <=4 low, <=8 moderate, <=12 high, >12 very_high
    def test_stress_low(self):
        assert self.svc._interpret_score("stress", 2) == "low"

    def test_stress_moderate(self):
        assert self.svc._interpret_score("stress", 6) == "moderate"

    def test_stress_high(self):
        assert self.svc._interpret_score("stress", 10) == "high"

    def test_stress_very_high(self):
        assert self.svc._interpret_score("stress", 15) == "very_high"

    # Sleep: <=1 good, <=2 fair, >2 poor
    def test_sleep_good(self):
        assert self.svc._interpret_score("sleep", 0.5) == "good"

    def test_sleep_fair(self):
        assert self.svc._interpret_score("sleep", 1.5) == "fair"

    def test_sleep_poor(self):
        assert self.svc._interpret_score("sleep", 5) == "poor"

    # Efficacy: <=8 low, <=12 moderate, >12 high
    def test_efficacy_low(self):
        assert self.svc._interpret_score("efficacy", 5) == "low"

    def test_efficacy_moderate(self):
        assert self.svc._interpret_score("efficacy", 10) == "moderate"

    def test_efficacy_high(self):
        assert self.svc._interpret_score("efficacy", 15) == "high"

    # Unknown survey type
    def test_unknown_type(self):
        assert self.svc._interpret_score("unknown_type", 5) is None

    # Zero score
    def test_zero_score(self):
        assert self.svc._interpret_score("burnout", 0) == "low"

    # Negative score
    def test_negative_score(self):
        assert self.svc._interpret_score("stress", -1) == "low"


# ── _calculate_score ────────────────────────────────────────────────────


class TestCalculateScore:
    """Test score calculation from survey responses."""

    svc = _make_service()

    def test_simple_sum_scoring(self):
        """No scoring_json: sum scores from options matching responses."""
        survey = _make_survey(
            survey_type="burnout",
            questions_json=[
                {
                    "id": "q1",
                    "options": [
                        {"value": "a", "score": 1},
                        {"value": "b", "score": 2},
                        {"value": "c", "score": 3},
                    ],
                },
                {
                    "id": "q2",
                    "options": [
                        {"value": "a", "score": 0},
                        {"value": "b", "score": 1},
                    ],
                },
            ],
        )
        responses = {"q1": "c", "q2": "b"}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 4  # 3 + 1
        assert interp == "low"  # burnout <=6 is low

    def test_simple_sum_burnout_high(self):
        """Sum scoring resulting in high burnout."""
        survey = _make_survey(
            survey_type="burnout",
            questions_json=[
                {"id": "q1", "options": [{"value": "a", "score": 5}]},
                {"id": "q2", "options": [{"value": "a", "score": 5}]},
            ],
        )
        responses = {"q1": "a", "q2": "a"}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 10
        assert interp == "high"

    def test_missing_response_skipped(self):
        """Questions without responses contribute 0 to score."""
        survey = _make_survey(
            survey_type="burnout",
            questions_json=[
                {"id": "q1", "options": [{"value": "a", "score": 3}]},
                {"id": "q2", "options": [{"value": "a", "score": 3}]},
            ],
        )
        responses = {"q1": "a"}  # q2 not answered
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 3

    def test_no_matching_option(self):
        """Response value doesn't match any option -- 0 score for that question."""
        survey = _make_survey(
            survey_type="burnout",
            questions_json=[
                {"id": "q1", "options": [{"value": "a", "score": 3}]},
            ],
        )
        responses = {"q1": "z"}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 0

    def test_custom_sum_scoring(self):
        """scoring_json with method='sum' sums response values directly."""
        survey = _make_survey(
            survey_type="stress",
            scoring_json={"method": "sum"},
        )
        responses = {"q1": 3, "q2": 5, "q3": 2}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 10
        assert interp == "high"  # stress 10 <=12 is high

    def test_custom_average_scoring(self):
        """scoring_json with method='average' averages response values."""
        survey = _make_survey(
            survey_type="efficacy",
            scoring_json={"method": "average"},
        )
        responses = {"q1": 10, "q2": 14, "q3": 12}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 12.0
        assert interp == "moderate"  # efficacy <=12 is moderate

    def test_custom_average_empty_responses(self):
        """Average of empty responses is 0."""
        survey = _make_survey(
            survey_type="efficacy",
            scoring_json={"method": "average"},
        )
        responses = {}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 0

    def test_unknown_scoring_method(self):
        """Unknown scoring method returns None."""
        survey = _make_survey(
            survey_type="burnout",
            scoring_json={"method": "weighted_percentile"},
        )
        responses = {"q1": 5}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score is None
        assert interp is None

    def test_empty_questions(self):
        """Survey with no questions scores 0."""
        survey = _make_survey(
            survey_type="burnout",
            questions_json=[],
        )
        responses = {}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 0

    def test_none_questions(self):
        """Survey with None questions_json scores 0."""
        survey = _make_survey(
            survey_type="burnout",
            questions_json=None,
        )
        responses = {}
        score, interp = self.svc._calculate_score(survey, responses)
        assert score == 0


# ── get_achievement_info ────────────────────────────────────────────────


class TestGetAchievementInfo:
    """Test achievement info display generation."""

    svc = _make_service()

    def test_no_account(self):
        """None account returns all achievements as unearned."""
        result = self.svc.get_achievement_info(None)
        assert len(result) == len(AchievementType)
        assert all(not a["earned"] for a in result)

    def test_empty_account(self):
        """Account with no achievements shows all unearned."""
        account = _make_account()
        result = self.svc.get_achievement_info(account)
        assert len(result) == len(AchievementType)
        assert all(not a["earned"] for a in result)

    def test_some_earned(self):
        """Account with some achievements shows correct earned status."""
        account = _make_account(
            achievements=["first_checkin", "points_100"],
            earned_at={"first_checkin": "2026-01-01", "points_100": "2026-01-15"},
        )
        result = self.svc.get_achievement_info(account)

        first_checkin = next(a for a in result if a["code"] == "first_checkin")
        assert first_checkin["earned"] is True
        assert first_checkin["earned_at"] == "2026-01-01"

        points_100 = next(a for a in result if a["code"] == "points_100")
        assert points_100["earned"] is True

        weekly_warrior = next(a for a in result if a["code"] == "weekly_warrior")
        assert weekly_warrior["earned"] is False
        assert weekly_warrior["earned_at"] is None

    def test_all_achievements_have_definition(self):
        """Every AchievementType has an entry in ACHIEVEMENT_DEFINITIONS."""
        for at in AchievementType:
            if at in ACHIEVEMENT_DEFINITIONS:
                defn = ACHIEVEMENT_DEFINITIONS[at]
                assert "name" in defn
                assert "description" in defn
                assert "icon" in defn

    def test_result_has_required_fields(self):
        """Each achievement dict has all required display fields."""
        account = _make_account()
        result = self.svc.get_achievement_info(account)
        for a in result:
            assert "code" in a
            assert "name" in a
            assert "description" in a
            assert "icon" in a
            assert "earned" in a
            assert "criteria" in a
