"""Tests for rotation requirements compliance validator (pure logic, no DB required)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.validators.rotation_validator import (
    MIN_CONFERENCE_ATTENDANCE,
    MIN_CONTINUITY_CLINIC_FREQUENCY,
    MIN_PROCEDURE_BLOCKS,
    MIN_PROCEDURES_PER_YEAR,
    MIN_PROCEDURES_PGY1,
    MIN_PROCEDURES_PGY2,
    MIN_ROTATION_DAYS,
    MIN_SPECIALTY_BLOCKS,
    PGY1_MIN_CLINIC_BLOCKS,
    PGY2_MIN_CLINIC_BLOCKS,
    PGY3_MIN_CLINIC_BLOCKS,
    RotationValidator,
    RotationViolation,
    RotationWarning,
)


# ==================== Helpers ====================

PERSON = uuid4()
BASE_DATE = date(2025, 7, 1)  # Start of academic year


def _rotation(name: str, idx: int = 0, rot_type: str = "Other", blocks: int = 1):
    """Build a rotation dict for sequence/summary tests."""
    return {
        "rotation_name": name,
        "start_date": BASE_DATE + timedelta(days=28 * idx),
        "end_date": BASE_DATE + timedelta(days=28 * idx + 27),
        "rotation_type": rot_type,
        "blocks": blocks,
    }


# ==================== Constants Tests ====================


class TestConstants:
    """Verify rotation constants are correct."""

    def test_min_rotation_days(self):
        assert MIN_ROTATION_DAYS == 7

    def test_pgy1_min_clinic_blocks(self):
        assert PGY1_MIN_CLINIC_BLOCKS == 8

    def test_pgy2_min_clinic_blocks(self):
        assert PGY2_MIN_CLINIC_BLOCKS == 8

    def test_pgy3_min_clinic_blocks(self):
        assert PGY3_MIN_CLINIC_BLOCKS == 6

    def test_min_specialty_blocks(self):
        assert MIN_SPECIALTY_BLOCKS == 6

    def test_min_procedure_blocks(self):
        assert MIN_PROCEDURE_BLOCKS == 2

    def test_min_continuity_clinic_frequency(self):
        assert MIN_CONTINUITY_CLINIC_FREQUENCY == 2

    def test_min_procedures_per_year(self):
        assert MIN_PROCEDURES_PER_YEAR == 50

    def test_min_procedures_pgy1(self):
        assert MIN_PROCEDURES_PGY1 == 20

    def test_min_procedures_pgy2(self):
        assert MIN_PROCEDURES_PGY2 == 30

    def test_min_conference_attendance(self):
        assert pytest.approx(0.95) == MIN_CONFERENCE_ATTENDANCE


# ==================== Dataclass Tests ====================


class TestRotationViolation:
    """Test RotationViolation dataclass."""

    def test_construction(self):
        v = RotationViolation(
            person_id=PERSON,
            violation_type="minimum_length",
            severity="MEDIUM",
            message="Rotation too short",
            rotation_name="Inpatient",
            actual_value=5,
            required_value=7,
        )
        assert v.person_id == PERSON
        assert v.violation_type == "minimum_length"
        assert v.actual_value == 5
        assert v.required_value == 7

    def test_float_values(self):
        v = RotationViolation(
            person_id=PERSON,
            violation_type="volume_shortfall",
            severity="HIGH",
            message="Low volume",
            rotation_name="Procedures",
            actual_value=10.5,
            required_value=50.0,
        )
        assert v.actual_value == 10.5


class TestRotationWarning:
    """Test RotationWarning dataclass."""

    def test_construction(self):
        w = RotationWarning(
            person_id=PERSON,
            warning_type="low_volume",
            message="Volume below target",
            rotation_name="Procedures",
            current_value=35,
            target_value=50,
        )
        assert w.warning_type == "low_volume"
        assert w.current_value == 35


# ==================== RotationValidator Init ====================


class TestRotationValidatorInit:
    """Test RotationValidator initialization."""

    def test_defaults(self):
        v = RotationValidator()
        assert v.min_rotation_days == 7
        assert v.pgy1_min_clinic == 8
        assert v.pgy2_min_clinic == 8
        assert v.pgy3_min_clinic == 6
        assert v.min_specialty == 6
        assert v.min_procedures == 2


# ==================== validate_minimum_rotation_length Tests ====================


class TestValidateMinimumRotationLength:
    """Test validate_minimum_rotation_length method."""

    def test_adequate_length_no_violation(self):
        """7+ days -> no violation."""
        v = RotationValidator()
        result = v.validate_minimum_rotation_length(
            PERSON, "Inpatient", BASE_DATE, BASE_DATE + timedelta(days=6)
        )
        assert result is None

    def test_exactly_7_days_no_violation(self):
        """Exactly 7 days (inclusive) -> no violation."""
        v = RotationValidator()
        result = v.validate_minimum_rotation_length(
            PERSON, "Inpatient", BASE_DATE, BASE_DATE + timedelta(days=6)
        )
        # duration = 6 - 0 + 1 = 7
        assert result is None

    def test_6_days_violation(self):
        """6 days (< 7) -> MEDIUM violation."""
        v = RotationValidator()
        result = v.validate_minimum_rotation_length(
            PERSON, "Inpatient", BASE_DATE, BASE_DATE + timedelta(days=4)
        )
        # duration = 4 - 0 + 1 = 5
        assert result is not None
        assert result.violation_type == "minimum_length"
        assert result.severity == "MEDIUM"
        assert result.actual_value == 5
        assert result.required_value == 7

    def test_single_day_violation(self):
        """1-day rotation -> violation."""
        v = RotationValidator()
        result = v.validate_minimum_rotation_length(
            PERSON, "Inpatient", BASE_DATE, BASE_DATE
        )
        assert result is not None
        assert result.actual_value == 1

    def test_long_rotation_no_violation(self):
        """28 days -> no violation."""
        v = RotationValidator()
        result = v.validate_minimum_rotation_length(
            PERSON, "Inpatient", BASE_DATE, BASE_DATE + timedelta(days=27)
        )
        assert result is None

    def test_rotation_name_in_message(self):
        """Rotation name appears in violation message."""
        v = RotationValidator()
        result = v.validate_minimum_rotation_length(
            PERSON, "Emergency Medicine", BASE_DATE, BASE_DATE + timedelta(days=2)
        )
        assert result is not None
        assert "Emergency Medicine" in result.message
        assert result.rotation_name == "Emergency Medicine"


# ==================== validate_pgy_level_clinic_requirements Tests ====================


class TestValidatePgyLevelClinicRequirements:
    """Test validate_pgy_level_clinic_requirements method."""

    def test_pgy1_adequate_no_violation(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(PERSON, 1, 8)
        assert result is None

    def test_pgy1_insufficient_violation(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(PERSON, 1, 5)
        assert result is not None
        assert result.severity == "HIGH"
        assert result.actual_value == 5
        assert result.required_value == 8

    def test_pgy2_adequate_no_violation(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(PERSON, 2, 10)
        assert result is None

    def test_pgy2_insufficient_violation(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(PERSON, 2, 6)
        assert result is not None
        assert result.required_value == 8

    def test_pgy3_adequate_no_violation(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(PERSON, 3, 6)
        assert result is None

    def test_pgy3_insufficient_violation(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(PERSON, 3, 4)
        assert result is not None
        assert result.required_value == 6

    def test_unknown_pgy_level_returns_none(self):
        """PGY > 3 returns None (no rule defined)."""
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(PERSON, 4, 0)
        assert result is None

    def test_year_to_date_flag_in_message(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(
            PERSON, 1, 3, year_to_date=True
        )
        assert result is not None
        assert "year-to-date" in result.message

    def test_annual_flag_in_message(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(
            PERSON, 1, 3, year_to_date=False
        )
        assert result is not None
        assert "annual" in result.message

    def test_rotation_name_includes_pgy_level(self):
        v = RotationValidator()
        result = v.validate_pgy_level_clinic_requirements(PERSON, 2, 3)
        assert result is not None
        assert result.rotation_name == "PGY-2 Clinic"


# ==================== validate_specialty_rotation_completion Tests ====================


class TestValidateSpecialtyRotationCompletion:
    """Test validate_specialty_rotation_completion method."""

    def test_pgy1_skipped(self):
        """PGY-1 does not require specialty -> always None."""
        v = RotationValidator()
        result = v.validate_specialty_rotation_completion(PERSON, 1, 0)
        assert result is None

    def test_pgy2_adequate_no_violation(self):
        v = RotationValidator()
        result = v.validate_specialty_rotation_completion(PERSON, 2, 6)
        assert result is None

    def test_pgy2_insufficient_violation(self):
        v = RotationValidator()
        result = v.validate_specialty_rotation_completion(PERSON, 2, 3)
        assert result is not None
        assert result.severity == "HIGH"
        assert result.actual_value == 3
        assert result.required_value == 6

    def test_pgy3_adequate_no_violation(self):
        v = RotationValidator()
        result = v.validate_specialty_rotation_completion(PERSON, 3, 8)
        assert result is None

    def test_pgy3_insufficient_violation(self):
        v = RotationValidator()
        result = v.validate_specialty_rotation_completion(PERSON, 3, 5)
        assert result is not None
        assert "deficit" in result.message

    def test_exactly_at_minimum(self):
        v = RotationValidator()
        result = v.validate_specialty_rotation_completion(PERSON, 2, 6)
        assert result is None


# ==================== validate_procedure_volume Tests ====================


class TestValidateProcedureVolume:
    """Test validate_procedure_volume method."""

    def test_pgy1_adequate_no_issues(self):
        """PGY-1 at 20 procedures (target 20) -> no issue."""
        v = RotationValidator()
        violation, warning = v.validate_procedure_volume(PERSON, 1, 20)
        assert violation is None
        assert warning is None

    def test_pgy1_critical_shortfall(self):
        """PGY-1 with < 60% of target -> violation."""
        v = RotationValidator()
        # target_volume for PGY-1 = 20, 60% = 12
        violation, warning = v.validate_procedure_volume(PERSON, 1, 10)
        assert violation is not None
        assert violation.severity == "HIGH"
        assert violation.violation_type == "volume_shortfall"
        assert warning is None

    def test_pgy1_warning_zone(self):
        """PGY-1 between 60-85% of target -> warning only."""
        v = RotationValidator()
        # target_volume for PGY-1 = 20, 60% = 12, 85% = 17
        violation, warning = v.validate_procedure_volume(PERSON, 1, 14)
        assert violation is None
        assert warning is not None
        assert warning.warning_type == "low_volume"

    def test_pgy2_critical_shortfall(self):
        """PGY-2 target is 30, < 18 (60%) -> violation."""
        v = RotationValidator()
        violation, warning = v.validate_procedure_volume(PERSON, 2, 15)
        assert violation is not None
        assert warning is None

    def test_pgy3_target_50(self):
        """PGY-3+ uses MIN_PROCEDURES_PER_YEAR = 50."""
        v = RotationValidator()
        # 50 * 0.6 = 30, so 28 triggers violation
        violation, warning = v.validate_procedure_volume(PERSON, 3, 28)
        assert violation is not None
        assert violation.required_value == 50

    def test_custom_target_volume(self):
        """Custom target overrides PGY defaults."""
        v = RotationValidator()
        # Custom target 100, 60% = 60
        violation, warning = v.validate_procedure_volume(
            PERSON, 1, 55, target_volume=100
        )
        assert violation is not None
        assert violation.required_value == 100

    def test_custom_target_warning_zone(self):
        """Custom target 100, between 60-85 -> warning."""
        v = RotationValidator()
        violation, warning = v.validate_procedure_volume(
            PERSON, 1, 70, target_volume=100
        )
        assert violation is None
        assert warning is not None
        assert warning.target_value == 100

    def test_above_target_no_issues(self):
        """Above target -> no violation or warning."""
        v = RotationValidator()
        violation, warning = v.validate_procedure_volume(PERSON, 3, 60)
        assert violation is None
        assert warning is None

    def test_exactly_at_60_percent(self):
        """At exactly 60% -> no violation (uses <, not <=)."""
        v = RotationValidator()
        # PGY-1 target 20, 60% = 12.0 exactly
        violation, warning = v.validate_procedure_volume(PERSON, 1, 12)
        assert violation is None
        # 12 < 17 (85% of 20) -> should be warning
        assert warning is not None

    def test_exactly_at_85_percent(self):
        """At exactly 85% -> no warning (uses <, not <=)."""
        v = RotationValidator()
        # PGY-1 target 20, 85% = 17.0 exactly
        violation, warning = v.validate_procedure_volume(PERSON, 1, 17)
        assert violation is None
        assert warning is None


# ==================== validate_rotation_sequence Tests ====================


class TestValidateRotationSequence:
    """Test validate_rotation_sequence method."""

    def test_pgy1_fmit_early_no_violation(self):
        """FMIT in position 1-5 -> no violation."""
        v = RotationValidator()
        rotations = [
            _rotation("FMIT", idx=0),
            _rotation("Inpatient", idx=1),
            _rotation("Clinic", idx=2),
        ]
        violations = v.validate_rotation_sequence(PERSON, 1, rotations)
        assert len(violations) == 0

    def test_pgy1_fmit_late_violation(self):
        """FMIT after 5 other rotations -> MEDIUM violation."""
        v = RotationValidator()
        rotations = [_rotation(f"Rotation-{i}", idx=i) for i in range(6)]
        rotations.append(_rotation("FMIT", idx=6))  # Position 6 (index > 5)
        violations = v.validate_rotation_sequence(PERSON, 1, rotations)
        assert len(violations) == 1
        assert violations[0].rotation_name == "FMIT"
        assert violations[0].severity == "MEDIUM"

    def test_pgy1_no_fmit_no_violation(self):
        """PGY-1 without FMIT in list -> no violation (just not scheduled yet)."""
        v = RotationValidator()
        rotations = [_rotation(f"Rotation-{i}", idx=i) for i in range(4)]
        violations = v.validate_rotation_sequence(PERSON, 1, rotations)
        assert len(violations) == 0

    def test_pgy2_specialty_distributed_no_violation(self):
        """PGY-2 with distributed specialty rotations -> no violation."""
        v = RotationValidator()
        rotations = [
            _rotation("Specialty-A", idx=0),
            _rotation("Clinic", idx=1),
            _rotation("Specialty-B", idx=2),
            _rotation("Inpatient", idx=3),
            _rotation("Specialty-C", idx=4),
        ]
        violations = v.validate_rotation_sequence(PERSON, 2, rotations)
        assert len(violations) == 0

    def test_pgy2_three_consecutive_specialty_violation(self):
        """PGY-2 with 3 consecutive specialty rotations -> violation."""
        v = RotationValidator()
        rotations = [
            _rotation("Specialty-A", idx=0),
            _rotation("Specialty-B", idx=1),
            _rotation("Specialty-C", idx=2),
        ]
        violations = v.validate_rotation_sequence(PERSON, 2, rotations)
        assert len(violations) == 1
        assert "consecutive specialty" in violations[0].message

    def test_pgy2_derm_neuro_count_as_specialty(self):
        """DERM and NEURO are specialty rotations."""
        v = RotationValidator()
        rotations = [
            _rotation("DERM", idx=0),
            _rotation("NEURO", idx=1),
            _rotation("Elective", idx=2),
        ]
        violations = v.validate_rotation_sequence(PERSON, 2, rotations)
        # All 3 are consecutive specialties
        assert len(violations) == 1

    def test_pgy1_no_specialty_check(self):
        """PGY-1 skips specialty clustering check (pgy_level < 2)."""
        v = RotationValidator()
        rotations = [
            _rotation("Specialty-A", idx=0),
            _rotation("Specialty-B", idx=1),
            _rotation("Specialty-C", idx=2),
        ]
        violations = v.validate_rotation_sequence(PERSON, 1, rotations)
        assert len(violations) == 0

    def test_empty_rotations_no_violation(self):
        v = RotationValidator()
        violations = v.validate_rotation_sequence(PERSON, 1, [])
        assert len(violations) == 0

    def test_case_insensitive_fmit(self):
        """FMIT detection is case-insensitive (uppercased)."""
        v = RotationValidator()
        rotations = [_rotation(f"Rot-{i}", idx=i) for i in range(6)]
        rotations.append(_rotation("fmit", idx=6))
        violations = v.validate_rotation_sequence(PERSON, 1, rotations)
        assert len(violations) == 1  # fmit -> FMIT detected late

    def test_four_consecutive_specialty_multiple_violations(self):
        """4 consecutive specialties trigger violation at count 3 and 4."""
        v = RotationValidator()
        rotations = [
            _rotation("Specialty-A", idx=0),
            _rotation("Specialty-B", idx=1),
            _rotation("Specialty-C", idx=2),
            _rotation("Specialty-D", idx=3),
        ]
        violations = v.validate_rotation_sequence(PERSON, 2, rotations)
        # First violation at count=3, second at count=4
        assert len(violations) == 2


# ==================== validate_continuity_clinic_frequency Tests ====================


class TestValidateContinuityClinicFrequency:
    """Test validate_continuity_clinic_frequency method."""

    def test_adequate_frequency_no_warning(self):
        """≥2 blocks/month -> no warning."""
        v = RotationValidator()
        result = v.validate_continuity_clinic_frequency(PERSON, 1, 2.5)
        assert result is None

    def test_exactly_at_minimum_no_warning(self):
        """Exactly 2 blocks/month -> no warning."""
        v = RotationValidator()
        result = v.validate_continuity_clinic_frequency(PERSON, 1, 2.0)
        assert result is None

    def test_low_frequency_warning(self):
        """< 2 blocks/month -> warning."""
        v = RotationValidator()
        result = v.validate_continuity_clinic_frequency(PERSON, 1, 1.5)
        assert result is not None
        assert result.warning_type == "low_volume"
        assert result.current_value == 1.5
        assert result.target_value == 2

    def test_zero_frequency_warning(self):
        v = RotationValidator()
        result = v.validate_continuity_clinic_frequency(PERSON, 2, 0.0)
        assert result is not None

    def test_rotation_name_continuity(self):
        v = RotationValidator()
        result = v.validate_continuity_clinic_frequency(PERSON, 1, 1.0)
        assert result is not None
        assert result.rotation_name == "Continuity Clinic"


# ==================== validate_educational_milestone_completion Tests ====================


class TestValidateEducationalMilestoneCompletion:
    """Test validate_educational_milestone_completion method."""

    def test_all_complete_no_violations(self):
        v = RotationValidator()
        milestones = {"Patient Care": True, "Knowledge": True, "Communication": True}
        violations = v.validate_educational_milestone_completion(
            PERSON, "Inpatient", milestones
        )
        assert len(violations) == 0

    def test_one_incomplete_one_violation(self):
        v = RotationValidator()
        milestones = {"Patient Care": True, "Knowledge": False}
        violations = v.validate_educational_milestone_completion(
            PERSON, "Inpatient", milestones
        )
        assert len(violations) == 1
        assert "Knowledge" in violations[0].message
        assert violations[0].severity == "MEDIUM"

    def test_all_incomplete_multiple_violations(self):
        v = RotationValidator()
        milestones = {"A": False, "B": False, "C": False}
        violations = v.validate_educational_milestone_completion(
            PERSON, "Clinic", milestones
        )
        assert len(violations) == 3

    def test_empty_milestones_no_violations(self):
        v = RotationValidator()
        violations = v.validate_educational_milestone_completion(PERSON, "Clinic", {})
        assert len(violations) == 0

    def test_rotation_name_in_message(self):
        v = RotationValidator()
        milestones = {"Patient Care": False}
        violations = v.validate_educational_milestone_completion(
            PERSON, "Emergency Medicine", milestones
        )
        assert len(violations) == 1
        assert "Emergency Medicine" in violations[0].message
        assert violations[0].rotation_name == "Emergency Medicine"

    def test_actual_and_required_values(self):
        v = RotationValidator()
        milestones = {"Milestone-X": False}
        violations = v.validate_educational_milestone_completion(
            PERSON, "Clinic", milestones
        )
        assert violations[0].actual_value == 0
        assert violations[0].required_value == 1


# ==================== get_annual_rotation_summary Tests ====================


class TestGetAnnualRotationSummary:
    """Test get_annual_rotation_summary method."""

    def test_empty_rotations(self):
        v = RotationValidator()
        result = v.get_annual_rotation_summary(PERSON, 1, [])
        assert result["total_blocks_completed"] == 0
        assert result["utilization_rate"] == 0
        assert result["clinic_blocks"] == 0
        assert result["specialty_blocks"] == 0
        assert result["inpatient_blocks"] == 0
        assert result["diversity_score"] == 0

    def test_single_rotation(self):
        v = RotationValidator()
        rotations = [_rotation("Clinic", rot_type="Clinic", blocks=2)]
        result = v.get_annual_rotation_summary(PERSON, 1, rotations)
        assert result["total_blocks_completed"] == 2
        assert result["clinic_blocks"] == 2
        assert result["diversity_score"] == 1

    def test_mixed_rotation_types(self):
        v = RotationValidator()
        rotations = [
            _rotation("FM Clinic", rot_type="Clinic", blocks=3),
            _rotation("Inpatient Med", rot_type="Inpatient", blocks=4),
            _rotation("Derm Elective", rot_type="Specialty", blocks=2),
            _rotation("Continuity", rot_type="Continuity Clinic", blocks=2),
        ]
        result = v.get_annual_rotation_summary(PERSON, 2, rotations)
        assert result["total_blocks_completed"] == 11
        assert result["clinic_blocks"] == 5  # Clinic(3) + Continuity Clinic(2)
        assert result["specialty_blocks"] == 2
        assert result["inpatient_blocks"] == 4
        assert result["diversity_score"] == 4

    def test_utilization_rate(self):
        v = RotationValidator()
        rotations = [_rotation("Clinic", rot_type="Clinic", blocks=13)]
        result = v.get_annual_rotation_summary(
            PERSON, 1, rotations, total_blocks_available=26
        )
        assert result["utilization_rate"] == pytest.approx(0.5)

    def test_full_utilization(self):
        v = RotationValidator()
        rotations = [_rotation("All", rot_type="Other", blocks=26)]
        result = v.get_annual_rotation_summary(
            PERSON, 1, rotations, total_blocks_available=26
        )
        assert result["utilization_rate"] == pytest.approx(1.0)

    def test_zero_blocks_available(self):
        """Edge case: 0 blocks available -> utilization 0."""
        v = RotationValidator()
        result = v.get_annual_rotation_summary(PERSON, 1, [], total_blocks_available=0)
        assert result["utilization_rate"] == 0

    def test_person_id_as_string(self):
        v = RotationValidator()
        result = v.get_annual_rotation_summary(PERSON, 1, [])
        assert result["person_id"] == str(PERSON)

    def test_pgy_level_in_result(self):
        v = RotationValidator()
        result = v.get_annual_rotation_summary(PERSON, 2, [])
        assert result["pgy_level"] == 2

    def test_default_blocks_is_one(self):
        """Rotation without 'blocks' key defaults to 1."""
        v = RotationValidator()
        rotations = [{"rotation_name": "X", "rotation_type": "Other"}]
        result = v.get_annual_rotation_summary(PERSON, 1, rotations)
        assert result["total_blocks_completed"] == 1

    def test_rotation_breakdown_dict(self):
        v = RotationValidator()
        rotations = [
            _rotation("A", rot_type="Clinic", blocks=2),
            _rotation("B", rot_type="Clinic", blocks=3),
            _rotation("C", rot_type="Inpatient", blocks=1),
        ]
        result = v.get_annual_rotation_summary(PERSON, 1, rotations)
        assert result["rotation_breakdown"]["Clinic"] == 5
        assert result["rotation_breakdown"]["Inpatient"] == 1
