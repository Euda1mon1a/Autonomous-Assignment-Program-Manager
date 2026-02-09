"""Tests for wellness schemas (Field bounds, field_validators, enums, defaults)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.wellness import (
    SurveyTypeEnum,
    SurveyFrequencyEnum,
    TransactionTypeEnum,
    QuestionOption,
    SurveyQuestion,
    SurveyBase,
    SurveyCreate,
    SurveyUpdate,
    SurveyResponse,
    SurveyListItem,
    SurveyResponseCreate,
    SurveySubmissionResult,
    SurveyResponseSummary,
    SurveyHistoryResponse,
    AchievementInfo,
    WellnessAccountResponse,
    WellnessAccountUpdate,
    LeaderboardOptInRequest,
    ConsentRequest,
    LeaderboardEntry,
    LeaderboardResponse,
    PointTransactionResponse,
    PointHistoryResponse,
    HopfieldPositionCreate,
    HopfieldPositionResult,
    HopfieldLandscapeData,
    HopfieldAggregatesResponse,
    QuickPulseSubmit,
    QuickPulseResult,
    WellnessAnalyticsSummary,
    CorrelationDataPoint,
    CorrelationAnalysis,
    WellnessExportRequest,
    WellnessExportResponse,
    QuickPulseWidgetData,
)


# ── Enums ──────────────────────────────────────────────────────────────


class TestSurveyTypeEnum:
    def test_values(self):
        assert SurveyTypeEnum.BURNOUT == "burnout"
        assert SurveyTypeEnum.STRESS == "stress"
        assert SurveyTypeEnum.SLEEP == "sleep"
        assert SurveyTypeEnum.EFFICACY == "efficacy"
        assert SurveyTypeEnum.PULSE == "pulse"
        assert SurveyTypeEnum.HOPFIELD == "hopfield"
        assert SurveyTypeEnum.CUSTOM == "custom"

    def test_count(self):
        assert len(SurveyTypeEnum) == 7


class TestSurveyFrequencyEnum:
    def test_values(self):
        assert SurveyFrequencyEnum.DAILY == "daily"
        assert SurveyFrequencyEnum.WEEKLY == "weekly"
        assert SurveyFrequencyEnum.BIWEEKLY == "biweekly"
        assert SurveyFrequencyEnum.BLOCK == "block"
        assert SurveyFrequencyEnum.ANNUAL == "annual"

    def test_count(self):
        assert len(SurveyFrequencyEnum) == 5


class TestTransactionTypeEnum:
    def test_values(self):
        assert TransactionTypeEnum.SURVEY == "survey"
        assert TransactionTypeEnum.STREAK == "streak"
        assert TransactionTypeEnum.ACHIEVEMENT == "achievement"
        assert TransactionTypeEnum.BLOCK_BONUS == "block_bonus"
        assert TransactionTypeEnum.ADMIN == "admin"
        assert TransactionTypeEnum.REDEMPTION == "redemption"

    def test_count(self):
        assert len(TransactionTypeEnum) == 6


# ── SurveyBase ─────────────────────────────────────────────────────────


class TestSurveyBase:
    def test_defaults(self):
        r = SurveyBase(
            name="MBI-2",
            display_name="Maslach Burnout Inventory",
            survey_type=SurveyTypeEnum.BURNOUT,
        )
        assert r.description is None
        assert r.instructions is None
        assert r.points_value == 50
        assert r.estimated_seconds == 60
        assert r.frequency == SurveyFrequencyEnum.WEEKLY

    # --- name (min_length=1, max_length=50) ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            SurveyBase(
                name="",
                display_name="Test",
                survey_type=SurveyTypeEnum.BURNOUT,
            )

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            SurveyBase(
                name="x" * 51,
                display_name="Test",
                survey_type=SurveyTypeEnum.BURNOUT,
            )

    # --- display_name (min_length=1, max_length=200) ---

    def test_display_name_empty(self):
        with pytest.raises(ValidationError):
            SurveyBase(
                name="MBI",
                display_name="",
                survey_type=SurveyTypeEnum.BURNOUT,
            )

    def test_display_name_too_long(self):
        with pytest.raises(ValidationError):
            SurveyBase(
                name="MBI",
                display_name="x" * 201,
                survey_type=SurveyTypeEnum.BURNOUT,
            )

    # --- points_value (ge=0) ---

    def test_points_value_below_min(self):
        with pytest.raises(ValidationError):
            SurveyBase(
                name="MBI",
                display_name="Test",
                survey_type=SurveyTypeEnum.BURNOUT,
                points_value=-1,
            )

    # --- estimated_seconds (ge=1) ---

    def test_estimated_seconds_below_min(self):
        with pytest.raises(ValidationError):
            SurveyBase(
                name="MBI",
                display_name="Test",
                survey_type=SurveyTypeEnum.BURNOUT,
                estimated_seconds=0,
            )


# ── SurveyCreate ───────────────────────────────────────────────────────


class TestSurveyCreate:
    def test_defaults(self):
        q = SurveyQuestion(id="q1", text="How are you?")
        r = SurveyCreate(
            name="Test",
            display_name="Test Survey",
            survey_type=SurveyTypeEnum.PULSE,
            questions=[q],
        )
        assert r.scoring_algorithm is None
        assert r.target_roles == []


# ── SurveyUpdate ───────────────────────────────────────────────────────


class TestSurveyUpdate:
    def test_all_none(self):
        r = SurveyUpdate()
        assert r.display_name is None
        assert r.description is None
        assert r.instructions is None
        assert r.points_value is None
        assert r.is_active is None
        assert r.target_roles is None

    def test_points_value_below_min(self):
        with pytest.raises(ValidationError):
            SurveyUpdate(points_value=-1)


# ── SurveyResponseCreate ──────────────────────────────────────────────


class TestSurveyResponseCreate:
    def test_defaults(self):
        r = SurveyResponseCreate(responses={"q1": 3})
        assert r.block_number is None
        assert r.academic_year is None

    # --- block_number (ge=0, le=13) ---

    def test_block_number_below_min(self):
        with pytest.raises(ValidationError):
            SurveyResponseCreate(responses={"q1": 3}, block_number=-1)

    def test_block_number_above_max(self):
        with pytest.raises(ValidationError):
            SurveyResponseCreate(responses={"q1": 3}, block_number=14)

    # --- academic_year (ge=2000, le=2100) ---

    def test_academic_year_below_min(self):
        with pytest.raises(ValidationError):
            SurveyResponseCreate(responses={"q1": 3}, academic_year=1999)

    def test_academic_year_above_max(self):
        with pytest.raises(ValidationError):
            SurveyResponseCreate(responses={"q1": 3}, academic_year=2101)

    # --- responses validator (not empty) ---

    def test_responses_empty(self):
        with pytest.raises(ValidationError, match="At least one response"):
            SurveyResponseCreate(responses={})


# ── SurveySubmissionResult ───────────────────────────────────────────


class TestSurveySubmissionResult:
    def test_defaults(self):
        r = SurveySubmissionResult(success=True)
        assert r.response_id is None
        assert r.score is None
        assert r.score_interpretation is None
        assert r.points_earned == 0
        assert r.new_achievements == []
        assert r.streak_updated is False
        assert r.current_streak == 0
        assert r.message == ""


# ── WellnessAccountUpdate ───────────────────────────────────────────


class TestWellnessAccountUpdate:
    def test_all_none(self):
        r = WellnessAccountUpdate()
        assert r.leaderboard_opt_in is None
        assert r.display_name is None
        assert r.research_consent is None

    # --- display_name (min_length=3, max_length=50) ---

    def test_display_name_too_short(self):
        with pytest.raises(ValidationError):
            WellnessAccountUpdate(display_name="ab")

    def test_display_name_too_long(self):
        with pytest.raises(ValidationError):
            WellnessAccountUpdate(display_name="x" * 51)

    def test_display_name_valid(self):
        r = WellnessAccountUpdate(display_name="DrSmith")
        assert r.display_name == "DrSmith"


# ── LeaderboardOptInRequest ──────────────────────────────────────────


class TestLeaderboardOptInRequest:
    def test_display_name_too_short(self):
        with pytest.raises(ValidationError):
            LeaderboardOptInRequest(opt_in=True, display_name="ab")

    def test_display_name_too_long(self):
        with pytest.raises(ValidationError):
            LeaderboardOptInRequest(opt_in=True, display_name="x" * 51)

    def test_display_name_none_ok(self):
        r = LeaderboardOptInRequest(opt_in=True)
        assert r.display_name is None


# ── ConsentRequest ───────────────────────────────────────────────────


class TestConsentRequest:
    def test_defaults(self):
        r = ConsentRequest(consent=True)
        assert r.consent_version == "1.0"


# ── LeaderboardEntry ─────────────────────────────────────────────────


class TestLeaderboardEntry:
    def test_defaults(self):
        r = LeaderboardEntry(rank=1, display_name="DrA", points=500, streak=5)
        assert r.is_you is False


# ── LeaderboardResponse ──────────────────────────────────────────────


class TestLeaderboardResponse:
    def test_defaults(self):
        r = LeaderboardResponse(entries=[], total_participants=10)
        assert r.your_rank is None
        assert r.your_points is None
        assert r.snapshot_date is None


# ── HopfieldPositionCreate ───────────────────────────────────────────


class TestHopfieldPositionCreate:
    def test_valid(self):
        r = HopfieldPositionCreate(x_position=0.5, y_position=0.5)
        assert r.z_position is None
        assert r.confidence is None
        assert r.notes is None
        assert r.block_number is None
        assert r.academic_year is None

    # --- x_position/y_position (ge=0, le=1) ---

    def test_x_below_min(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=-0.1, y_position=0.5)

    def test_x_above_max(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=1.1, y_position=0.5)

    def test_y_below_min(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=-0.1)

    def test_y_above_max(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=1.1)

    # --- z_position (ge=0, le=1) ---

    def test_z_below_min(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=0.5, z_position=-0.1)

    def test_z_above_max(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=0.5, z_position=1.1)

    # --- confidence (ge=1, le=5) ---

    def test_confidence_below_min(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=0.5, confidence=0)

    def test_confidence_above_max(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=0.5, confidence=6)

    # --- notes (max_length=500) ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=0.5, notes="x" * 501)

    # --- block_number (ge=0, le=13) ---

    def test_block_number_below_min(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=0.5, block_number=-1)

    def test_block_number_above_max(self):
        with pytest.raises(ValidationError):
            HopfieldPositionCreate(x_position=0.5, y_position=0.5, block_number=14)


# ── HopfieldPositionResult ───────────────────────────────────────────


class TestHopfieldPositionResult:
    def test_defaults(self):
        r = HopfieldPositionResult(success=True)
        assert r.position_id is None
        assert r.basin_depth is None
        assert r.energy_value is None
        assert r.stability_score is None
        assert r.nearest_attractor_type is None
        assert r.points_earned == 0
        assert r.message == ""


# ── HopfieldAggregatesResponse ───────────────────────────────────────


class TestHopfieldAggregatesResponse:
    def test_defaults(self):
        r = HopfieldAggregatesResponse(total_positions=50)
        assert r.average_x is None
        assert r.average_y is None
        assert r.average_basin_depth is None
        assert r.average_energy is None
        assert r.computed_basin_depth is None
        assert r.agreement_score is None
        assert r.block_number is None
        assert r.academic_year is None


# ── QuickPulseSubmit ─────────────────────────────────────────────────


class TestQuickPulseSubmit:
    def test_valid(self):
        r = QuickPulseSubmit(mood=3)
        assert r.energy is None
        assert r.notes is None

    # --- mood (ge=1, le=5) ---

    def test_mood_below_min(self):
        with pytest.raises(ValidationError):
            QuickPulseSubmit(mood=0)

    def test_mood_above_max(self):
        with pytest.raises(ValidationError):
            QuickPulseSubmit(mood=6)

    # --- energy (ge=1, le=5) ---

    def test_energy_below_min(self):
        with pytest.raises(ValidationError):
            QuickPulseSubmit(mood=3, energy=0)

    def test_energy_above_max(self):
        with pytest.raises(ValidationError):
            QuickPulseSubmit(mood=3, energy=6)

    # --- notes (max_length=200) ---

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            QuickPulseSubmit(mood=3, notes="x" * 201)


# ── QuickPulseResult ─────────────────────────────────────────────────


class TestQuickPulseResult:
    def test_defaults(self):
        r = QuickPulseResult(success=True)
        assert r.points_earned == 0
        assert r.current_streak == 0
        assert r.message == ""


# ── WellnessExportRequest ───────────────────────────────────────────


class TestWellnessExportRequest:
    def test_defaults(self):
        r = WellnessExportRequest()
        assert r.start_date is None
        assert r.end_date is None
        assert r.survey_types is None
        assert r.include_hopfield is True
        assert r.include_algorithm_snapshots is True
        assert r.format == "csv"


# ── WellnessExportResponse ──────────────────────────────────────────


class TestWellnessExportResponse:
    def test_defaults(self):
        r = WellnessExportResponse(
            export_id=uuid4(),
            status="pending",
            created_at=datetime(2026, 1, 15),
        )
        assert r.download_url is None
        assert r.record_count is None


# ── QuickPulseWidgetData ─────────────────────────────────────────────


class TestQuickPulseWidgetData:
    def test_defaults(self):
        r = QuickPulseWidgetData()
        assert r.can_submit is True
        assert r.last_submitted_at is None
        assert r.current_streak == 0
        assert r.points_balance == 0
        assert r.available_surveys == []
        assert r.recent_achievements == []
