"""Tests for fatigue risk schemas (Field bounds, defaults, nested models)."""

from datetime import date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.fatigue_risk import (
    SamnPerelliAssessmentRequest,
    SamnPerelliAssessmentResponse,
    FatigueScoreRequest,
    FatigueScoreResponse,
    AlertnessPredictionResponse,
    ShiftPatternInput,
    ScheduleFatigueAssessmentRequest,
    ScheduleFatigueAssessmentResponse,
    HazardAlertResponse,
    HazardScanResponse,
    FatigueProfileResponse,
    SleepDebtStateResponse,
    SleepDebtTrajectoryRequest,
    SleepDebtTrajectoryResponse,
    TeamHeatmapRequest,
    TeamHeatmapResponse,
    CircadianPhaseInfo,
    HazardLevelInfo,
    MitigationTypeInfo,
    TemporalConstraintsExport,
    InterventionCreateRequest,
    InterventionUpdateRequest,
    InterventionResponse,
    ACGMEFatigueValidationRequest,
    ACGMEFatigueValidationResponse,
)


# ── SamnPerelliAssessmentRequest ────────────────────────────────────────


class TestSamnPerelliAssessmentRequest:
    def test_valid(self):
        r = SamnPerelliAssessmentRequest(level=3)
        assert r.notes is None

    # --- level ge=1, le=7 ---

    def test_level_below_min(self):
        with pytest.raises(ValidationError):
            SamnPerelliAssessmentRequest(level=0)

    def test_level_above_max(self):
        with pytest.raises(ValidationError):
            SamnPerelliAssessmentRequest(level=8)

    # --- notes min_length=1, max_length=1000 ---

    def test_notes_empty(self):
        with pytest.raises(ValidationError):
            SamnPerelliAssessmentRequest(level=3, notes="")

    def test_notes_too_long(self):
        with pytest.raises(ValidationError):
            SamnPerelliAssessmentRequest(level=3, notes="x" * 1001)


# ── SamnPerelliAssessmentResponse ───────────────────────────────────────


class TestSamnPerelliAssessmentResponse:
    def test_defaults(self):
        r = SamnPerelliAssessmentResponse(
            resident_id="res-1",
            level=3,
            level_name="Okay",
            description="Acceptable alertness",
            assessed_at=datetime(2026, 1, 15),
            is_self_reported=True,
            safe_for_duty=True,
        )
        assert r.duty_restrictions is None
        assert r.recommended_rest_hours is None
        assert r.notes is None


# ── FatigueScoreRequest ─────────────────────────────────────────────────


class TestFatigueScoreRequest:
    def test_defaults(self):
        r = FatigueScoreRequest(hours_awake=12, hours_worked_24h=8)
        assert r.consecutive_night_shifts == 0
        assert r.time_of_day_hour == 12
        assert r.prior_sleep_hours == 7.0

    # --- hours_awake ge=0, le=72 ---

    def test_hours_awake_below_min(self):
        with pytest.raises(ValidationError):
            FatigueScoreRequest(hours_awake=-1, hours_worked_24h=8)

    def test_hours_awake_above_max(self):
        with pytest.raises(ValidationError):
            FatigueScoreRequest(hours_awake=73, hours_worked_24h=8)

    # --- hours_worked_24h ge=0, le=24 ---

    def test_hours_worked_below_min(self):
        with pytest.raises(ValidationError):
            FatigueScoreRequest(hours_awake=12, hours_worked_24h=-1)

    def test_hours_worked_above_max(self):
        with pytest.raises(ValidationError):
            FatigueScoreRequest(hours_awake=12, hours_worked_24h=25)

    # --- consecutive_night_shifts ge=0, le=30 ---

    def test_night_shifts_above_max(self):
        with pytest.raises(ValidationError):
            FatigueScoreRequest(
                hours_awake=12, hours_worked_24h=8, consecutive_night_shifts=31
            )

    # --- time_of_day_hour ge=0, le=23 ---

    def test_time_of_day_above_max(self):
        with pytest.raises(ValidationError):
            FatigueScoreRequest(hours_awake=12, hours_worked_24h=8, time_of_day_hour=24)

    # --- prior_sleep_hours ge=0, le=24 ---

    def test_prior_sleep_above_max(self):
        with pytest.raises(ValidationError):
            FatigueScoreRequest(
                hours_awake=12, hours_worked_24h=8, prior_sleep_hours=25
            )


# ── FatigueScoreResponse ────────────────────────────────────────────────


class TestFatigueScoreResponse:
    def test_valid(self):
        r = FatigueScoreResponse(
            samn_perelli_level=3,
            samn_perelli_name="Okay",
            alertness_score=0.7,
            circadian_phase="afternoon_dip",
            factors={"sleep": 0.8},
        )
        assert r.alertness_score == 0.7


# ── ShiftPatternInput ───────────────────────────────────────────────────


class TestShiftPatternInput:
    def test_defaults(self):
        r = ShiftPatternInput(
            type="day",
            start="2026-01-15T08:00:00",
            end="2026-01-15T17:00:00",
        )
        assert r.prior_sleep == 7.0

    # --- prior_sleep ge=0 ---

    def test_prior_sleep_negative(self):
        with pytest.raises(ValidationError):
            ShiftPatternInput(
                type="day",
                start="2026-01-15T08:00:00",
                end="2026-01-15T17:00:00",
                prior_sleep=-1,
            )


# ── ScheduleFatigueAssessmentRequest/Response ───────────────────────────


class TestScheduleFatigueAssessmentRequest:
    def test_valid(self):
        shift = ShiftPatternInput(
            type="day", start="2026-01-15T08:00:00", end="2026-01-15T17:00:00"
        )
        r = ScheduleFatigueAssessmentRequest(proposed_shifts=[shift])
        assert len(r.proposed_shifts) == 1


class TestScheduleFatigueAssessmentResponse:
    def test_valid(self):
        r = ScheduleFatigueAssessmentResponse(
            resident_id="res-1",
            shifts_evaluated=5,
            overall_risk="moderate",
            metrics={},
            hazard_distribution={},
            high_risk_windows=[],
            trajectory=[],
            recommendations=[],
        )
        assert r.overall_risk == "moderate"


# ── HazardAlertResponse ─────────────────────────────────────────────────


class TestHazardAlertResponse:
    def test_defaults(self):
        r = HazardAlertResponse(
            resident_id="res-1",
            hazard_level="yellow",
            hazard_level_name="Moderate",
            detected_at=datetime(2026, 1, 15),
            triggers=["sleep_debt"],
            required_mitigations=["rest_break"],
            recommended_mitigations=["caffeine"],
            acgme_risk=False,
        )
        assert r.alertness_score is None
        assert r.sleep_debt is None
        assert r.hours_awake is None
        assert r.samn_perelli is None
        assert r.escalation_time is None
        assert r.notes is None


# ── HazardScanResponse ──────────────────────────────────────────────────


class TestHazardScanResponse:
    def test_valid(self):
        r = HazardScanResponse(
            scanned_at=datetime(2026, 1, 15),
            total_residents=12,
            hazards_found=3,
            by_level={"green": 9, "yellow": 2, "red": 1},
            critical_count=1,
            acgme_risk_count=0,
            residents=[],
        )
        assert r.hazards_found == 3


# ── FatigueProfileResponse ──────────────────────────────────────────────


class TestFatigueProfileResponse:
    def test_valid(self):
        r = FatigueProfileResponse(
            resident_id="res-1",
            resident_name="Dr. Smith",
            pgy_level=1,
            generated_at=datetime(2026, 1, 15),
            current_state={},
            hazard={},
            work_history={},
            predictions={},
            acgme={},
        )
        assert r.pgy_level == 1


# ── SleepDebtStateResponse ──────────────────────────────────────────────


class TestSleepDebtStateResponse:
    def test_valid(self):
        r = SleepDebtStateResponse(
            resident_id="res-1",
            current_debt_hours=4.5,
            last_updated=datetime(2026, 1, 15),
            consecutive_deficit_days=3,
            recovery_sleep_needed=6.0,
            chronic_debt=False,
            debt_severity="moderate",
            impairment_equivalent_bac=0.03,
        )
        assert r.impairment_equivalent_bac == 0.03


# ── SleepDebtTrajectoryRequest ──────────────────────────────────────────


class TestSleepDebtTrajectoryRequest:
    def test_valid(self):
        r = SleepDebtTrajectoryRequest(planned_sleep_hours=[7.0, 8.0, 6.5])
        assert r.start_debt is None

    # --- planned_sleep_hours min_length=1, max_length=30 ---

    def test_empty(self):
        with pytest.raises(ValidationError):
            SleepDebtTrajectoryRequest(planned_sleep_hours=[])

    # --- start_debt ge=0 ---

    def test_start_debt_negative(self):
        with pytest.raises(ValidationError):
            SleepDebtTrajectoryRequest(planned_sleep_hours=[7.0], start_debt=-1)


# ── SleepDebtTrajectoryResponse ─────────────────────────────────────────


class TestSleepDebtTrajectoryResponse:
    def test_valid(self):
        r = SleepDebtTrajectoryResponse(
            resident_id="res-1",
            days_predicted=3,
            trajectory=[],
            recovery_estimate_nights=2,
        )
        assert r.recovery_estimate_nights == 2


# ── Dashboard schemas ───────────────────────────────────────────────────


class TestTeamHeatmapRequest:
    def test_defaults(self):
        r = TeamHeatmapRequest(target_date=date(2026, 1, 15))
        assert r.include_predictions is True


class TestTeamHeatmapResponse:
    def test_valid(self):
        r = TeamHeatmapResponse(
            date="2026-01-15",
            generated_at=datetime(2026, 1, 15),
            residents=[],
            hours=list(range(24)),
        )
        assert len(r.hours) == 24


class TestCircadianPhaseInfo:
    def test_valid(self):
        r = CircadianPhaseInfo(
            phase="morning_peak",
            name="Morning Peak",
            time_range="09:00-12:00",
            alertness_multiplier=1.2,
            description="Peak alertness",
        )
        assert r.alertness_multiplier == 1.2


class TestHazardLevelInfo:
    def test_valid(self):
        r = HazardLevelInfo(
            level="yellow",
            name="Moderate",
            description="Moderate risk",
            thresholds={"alertness": 0.5},
            required_mitigations=["rest_break"],
        )
        assert r.level == "yellow"


class TestMitigationTypeInfo:
    def test_valid(self):
        r = MitigationTypeInfo(
            type="rest_break", name="Rest Break", description="15-min break"
        )
        assert r.type == "rest_break"


# ── TemporalConstraintsExport ───────────────────────────────────────────


class TestTemporalConstraintsExport:
    def test_valid(self):
        r = TemporalConstraintsExport(
            version="1.0",
            generated_at=datetime(2026, 1, 15),
            framework="FRMS",
            references=["ICAO"],
            circadian_rhythm={},
            sleep_homeostasis={},
            samn_perelli_scale={},
            hazard_thresholds={},
            acgme_integration={},
            scheduling_constraints={},
        )
        assert r.version == "1.0"


# ── Intervention schemas ────────────────────────────────────────────────


class TestInterventionCreateRequest:
    def test_defaults(self):
        r = InterventionCreateRequest(intervention_type="rest_break")
        assert r.alert_id is None
        assert r.description is None
        assert r.authorized_by is None
        assert r.authorization_method == "manual"


class TestInterventionUpdateRequest:
    def test_valid(self):
        r = InterventionUpdateRequest(outcome="effective")
        assert r.outcome_notes is None
        assert r.post_alertness is None


class TestInterventionResponse:
    def test_valid(self):
        r = InterventionResponse(
            id="int-1",
            person_id="res-1",
            intervention_type="rest_break",
            authorization_method="manual",
            created_at=datetime(2026, 1, 15),
        )
        assert r.alert_id is None
        assert r.description is None
        assert r.started_at is None
        assert r.completed_at is None
        assert r.outcome is None
        assert r.pre_alertness is None
        assert r.post_alertness is None
        assert r.alertness_improvement is None


# ── ACGME validation schemas ────────────────────────────────────────────


class TestACGMEFatigueValidationRequest:
    def test_valid(self):
        r = ACGMEFatigueValidationRequest(
            resident_id=uuid4(),
            schedule_start=date(2026, 1, 1),
            schedule_end=date(2026, 3, 31),
        )
        assert r.schedule_start == date(2026, 1, 1)


class TestACGMEFatigueValidationResponse:
    def test_valid(self):
        r = ACGMEFatigueValidationResponse(
            resident_id="res-1",
            schedule_period={"start": "2026-01-01", "end": "2026-03-31"},
            acgme_compliant=True,
            fatigue_compliant=True,
            hours_summary={},
            fatigue_risk_periods=[],
            recommendations=[],
            validation_details={},
        )
        assert r.acgme_compliant is True
        assert r.fatigue_compliant is True
