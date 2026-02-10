"""Tests for person-specific validation functions (no DB)."""

from __future__ import annotations

import pytest

from app.validators.common import ValidationError
from app.validators.person_validators import (
    COMMON_SPECIALTIES,
    MAX_PGY_LEVEL,
    MIN_PGY_LEVEL,
    VALID_FACULTY_ROLES,
    VALID_PERSON_TYPES,
    validate_call_counts,
    validate_faculty_role,
    validate_person_email,
    validate_person_name,
    validate_person_phone,
    validate_person_type,
    validate_pgy_level,
    validate_primary_duty,
    validate_specialties,
    validate_supervision_requirements,
    validate_target_clinical_blocks,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_valid_person_types(self):
        assert "resident" in VALID_PERSON_TYPES
        assert "faculty" in VALID_PERSON_TYPES
        assert len(VALID_PERSON_TYPES) == 2

    def test_valid_faculty_roles(self):
        expected = {"pd", "apd", "oic", "dept_chief", "sports_med", "core"}
        assert set(VALID_FACULTY_ROLES) == expected

    def test_pgy_range(self):
        assert MIN_PGY_LEVEL == 1
        assert MAX_PGY_LEVEL == 3

    def test_common_specialties_count(self):
        assert len(COMMON_SPECIALTIES) >= 10

    def test_family_medicine_in_specialties(self):
        assert "Family Medicine" in COMMON_SPECIALTIES


# ---------------------------------------------------------------------------
# validate_person_type
# ---------------------------------------------------------------------------


class TestValidatePersonType:
    def test_resident(self):
        assert validate_person_type("resident") == "resident"

    def test_faculty(self):
        assert validate_person_type("faculty") == "faculty"

    def test_uppercase_normalized(self):
        assert validate_person_type("RESIDENT") == "resident"
        assert validate_person_type("Faculty") == "faculty"

    def test_whitespace_stripped(self):
        assert validate_person_type("  resident  ") == "resident"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_person_type("")

    def test_invalid_type(self):
        with pytest.raises(ValidationError, match="must be one of"):
            validate_person_type("student")


# ---------------------------------------------------------------------------
# validate_pgy_level
# ---------------------------------------------------------------------------


class TestValidatePgyLevel:
    def test_resident_pgy1(self):
        assert validate_pgy_level(1, "resident") == 1

    def test_resident_pgy2(self):
        assert validate_pgy_level(2, "resident") == 2

    def test_resident_pgy3(self):
        assert validate_pgy_level(3, "resident") == 3

    def test_resident_none_raises(self):
        with pytest.raises(ValidationError, match="must have a PGY level"):
            validate_pgy_level(None, "resident")

    def test_resident_below_min(self):
        with pytest.raises(ValidationError):
            validate_pgy_level(0, "resident")

    def test_resident_above_max(self):
        with pytest.raises(ValidationError):
            validate_pgy_level(4, "resident")

    def test_faculty_none_ok(self):
        assert validate_pgy_level(None, "faculty") is None

    def test_faculty_with_pgy_raises(self):
        with pytest.raises(ValidationError, match="Faculty cannot have"):
            validate_pgy_level(2, "faculty")

    def test_unknown_type_returns_value(self):
        # Unknown person type just passes through
        assert validate_pgy_level(5, "unknown") == 5


# ---------------------------------------------------------------------------
# validate_faculty_role
# ---------------------------------------------------------------------------


class TestValidateFacultyRole:
    @pytest.mark.parametrize("role", VALID_FACULTY_ROLES)
    def test_valid_roles(self, role):
        assert validate_faculty_role(role, "faculty") == role

    def test_uppercase_normalized(self):
        assert validate_faculty_role("PD", "faculty") == "pd"

    def test_whitespace_stripped(self):
        assert validate_faculty_role("  apd  ", "faculty") == "apd"

    def test_faculty_none_ok(self):
        assert validate_faculty_role(None, "faculty") is None

    def test_invalid_role(self):
        with pytest.raises(ValidationError, match="must be one of"):
            validate_faculty_role("chief_of_staff", "faculty")

    def test_resident_none_ok(self):
        assert validate_faculty_role(None, "resident") is None

    def test_resident_with_role_raises(self):
        with pytest.raises(ValidationError, match="Residents cannot"):
            validate_faculty_role("pd", "resident")


# ---------------------------------------------------------------------------
# validate_specialties
# ---------------------------------------------------------------------------


class TestValidateSpecialties:
    def test_none_returns_none(self):
        assert validate_specialties(None) is None

    def test_empty_list_returns_none(self):
        assert validate_specialties([]) is None

    def test_valid_single(self):
        result = validate_specialties(["Family Medicine"])
        assert result == ["Family Medicine"]

    def test_valid_multiple(self):
        result = validate_specialties(["Family Medicine", "Sports Medicine"])
        assert result == ["Family Medicine", "Sports Medicine"]

    def test_strips_whitespace(self):
        result = validate_specialties(["  Family Medicine  "])
        assert result == ["Family Medicine"]

    def test_duplicate_raises(self):
        with pytest.raises(ValidationError, match="Duplicate"):
            validate_specialties(["Family Medicine", "family medicine"])

    def test_non_string_item_raises(self):
        with pytest.raises(ValidationError, match="must be a string"):
            validate_specialties([123])

    def test_empty_string_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_specialties([""])

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_specialties(["   "])

    def test_not_a_list_raises(self):
        with pytest.raises(ValidationError, match="must be a list"):
            validate_specialties("Family Medicine")  # type: ignore[arg-type]

    def test_too_short_specialty(self):
        with pytest.raises(ValidationError):
            validate_specialties(["A"])


# ---------------------------------------------------------------------------
# validate_person_name
# ---------------------------------------------------------------------------


class TestValidatePersonName:
    def test_valid_name(self):
        assert validate_person_name("John Smith") == "John Smith"

    def test_hyphenated(self):
        assert validate_person_name("Jean-Pierre") == "Jean-Pierre"

    def test_apostrophe(self):
        assert validate_person_name("O'Brien") == "O'Brien"

    def test_single_char_raises(self):
        with pytest.raises(ValidationError, match="too short"):
            validate_person_name("J")

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            validate_person_name("")


# ---------------------------------------------------------------------------
# validate_person_email
# ---------------------------------------------------------------------------


class TestValidatePersonEmail:
    def test_none_returns_none(self):
        assert validate_person_email(None) is None

    def test_empty_returns_none(self):
        assert validate_person_email("") is None

    def test_whitespace_returns_none(self):
        assert validate_person_email("   ") is None

    def test_valid_email(self):
        result = validate_person_email("test@example.com")
        assert result == "test@example.com"

    def test_uppercase_lowered(self):
        result = validate_person_email("Test@EXAMPLE.COM")
        assert result == "test@example.com"

    def test_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid email"):
            validate_person_email("not-an-email")


# ---------------------------------------------------------------------------
# validate_person_phone
# ---------------------------------------------------------------------------


class TestValidatePersonPhone:
    def test_none_returns_none(self):
        assert validate_person_phone(None) is None

    def test_empty_returns_none(self):
        assert validate_person_phone("") is None

    def test_whitespace_returns_none(self):
        assert validate_person_phone("   ") is None

    def test_us_format(self):
        result = validate_person_phone("(555) 123-4567")
        assert result == "5551234567"

    def test_us_with_country_code(self):
        result = validate_person_phone("+1-555-123-4567")
        assert result == "15551234567"

    def test_too_short(self):
        with pytest.raises(ValidationError):
            validate_person_phone("12345")


# ---------------------------------------------------------------------------
# validate_target_clinical_blocks
# ---------------------------------------------------------------------------


class TestValidateTargetClinicalBlocks:
    def test_none_returns_none(self):
        assert validate_target_clinical_blocks(None, "resident") is None

    def test_valid_resident_blocks(self):
        assert validate_target_clinical_blocks(48, "resident", pgy_level=2) == 48

    def test_valid_faculty_blocks(self):
        assert validate_target_clinical_blocks(10, "faculty") == 10

    def test_resident_too_low(self):
        with pytest.raises(ValidationError, match="too low"):
            validate_target_clinical_blocks(2, "resident", pgy_level=1)

    def test_resident_too_high(self):
        with pytest.raises(ValidationError, match="too high"):
            validate_target_clinical_blocks(250, "resident", pgy_level=3)

    def test_zero_ok_for_faculty(self):
        assert validate_target_clinical_blocks(0, "faculty") == 0

    def test_negative_raises(self):
        with pytest.raises(ValidationError):
            validate_target_clinical_blocks(-1, "resident", pgy_level=1)

    def test_boundary_resident_min(self):
        # 4 blocks is the minimum allowed for residents
        assert validate_target_clinical_blocks(4, "resident", pgy_level=1) == 4

    def test_boundary_resident_max(self):
        # 200 blocks is the maximum allowed for residents
        assert validate_target_clinical_blocks(200, "resident", pgy_level=1) == 200


# ---------------------------------------------------------------------------
# validate_supervision_requirements
# ---------------------------------------------------------------------------


class TestValidateSupervisionRequirements:
    def test_faculty(self):
        result = validate_supervision_requirements("faculty", None)
        assert result["needs_supervision"] is False
        assert result["supervision_ratio"] == 0
        assert result["requires_procedure_supervision"] is False

    def test_pgy1_ratio(self):
        result = validate_supervision_requirements("resident", 1)
        assert result["needs_supervision"] is True
        assert result["supervision_ratio"] == 2

    def test_pgy2_ratio(self):
        result = validate_supervision_requirements("resident", 2)
        assert result["needs_supervision"] is True
        assert result["supervision_ratio"] == 4

    def test_pgy3_ratio(self):
        result = validate_supervision_requirements("resident", 3)
        assert result["supervision_ratio"] == 4

    def test_procedures_flag(self):
        result = validate_supervision_requirements(
            "resident", 1, performs_procedures=True
        )
        assert result["requires_procedure_supervision"] is True

    def test_no_procedures_flag(self):
        result = validate_supervision_requirements(
            "resident", 1, performs_procedures=False
        )
        assert result["requires_procedure_supervision"] is False

    def test_resident_no_pgy_raises(self):
        with pytest.raises(ValidationError, match="without PGY level"):
            validate_supervision_requirements("resident", None)

    def test_unknown_type_raises(self):
        with pytest.raises(ValidationError, match="Unknown person type"):
            validate_supervision_requirements("student", None)


# ---------------------------------------------------------------------------
# validate_call_counts
# ---------------------------------------------------------------------------


class TestValidateCallCounts:
    def test_defaults_all_zero(self):
        assert validate_call_counts() == (0, 0, 0)

    def test_explicit_values(self):
        assert validate_call_counts(5, 10, 3) == (5, 10, 3)

    def test_none_defaults_to_zero(self):
        assert validate_call_counts(None, None, None) == (0, 0, 0)

    def test_negative_sunday_raises(self):
        with pytest.raises(ValidationError):
            validate_call_counts(sunday_call_count=-1)

    def test_negative_weekday_raises(self):
        with pytest.raises(ValidationError):
            validate_call_counts(weekday_call_count=-1)

    def test_negative_fmit_raises(self):
        with pytest.raises(ValidationError):
            validate_call_counts(fmit_weeks_count=-1)

    def test_fmit_too_high(self):
        with pytest.raises(ValidationError, match="too high"):
            validate_call_counts(fmit_weeks_count=13)

    def test_fmit_boundary_12_ok(self):
        # 12 is the max for the secondary check
        assert validate_call_counts(fmit_weeks_count=12) == (0, 0, 12)

    def test_sunday_max_52(self):
        assert validate_call_counts(sunday_call_count=52) == (52, 0, 0)

    def test_sunday_above_52_raises(self):
        with pytest.raises(ValidationError):
            validate_call_counts(sunday_call_count=53)


# ---------------------------------------------------------------------------
# validate_primary_duty
# ---------------------------------------------------------------------------


class TestValidatePrimaryDuty:
    def test_none_returns_none(self):
        assert validate_primary_duty(None, "faculty") is None

    def test_empty_returns_none(self):
        assert validate_primary_duty("", "faculty") is None

    def test_whitespace_returns_none(self):
        assert validate_primary_duty("   ", "faculty") is None

    def test_valid_duty(self):
        result = validate_primary_duty("Faculty Alpha", "faculty")
        assert result == "Faculty Alpha"

    def test_strips_whitespace(self):
        result = validate_primary_duty("  Faculty Alpha  ", "faculty")
        assert result == "Faculty Alpha"

    def test_too_short(self):
        with pytest.raises(ValidationError):
            validate_primary_duty("A", "faculty")

    def test_resident_also_works(self):
        # Primary duty validation doesn't restrict by person type
        result = validate_primary_duty("Resident Duty", "resident")
        assert result == "Resident Duty"
