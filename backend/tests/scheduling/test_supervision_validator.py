"""Tests for supervision ratio compliance validator (pure logic, no DB required)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.scheduling.validators.supervision_validator import (
    OTHER_RATIO,
    PGY1_RATIO,
    SupervisionValidator,
    SupervisionViolation,
)


# ==================== Helpers ====================

BLOCK_ID = uuid4()
FACULTY_ID = uuid4()
BASE_DATE = date(2025, 3, 3)


def _uuids(n: int) -> list:
    """Generate n UUIDs."""
    return [uuid4() for _ in range(n)]


def _block(
    pgy1: int = 0,
    other: int = 0,
    faculty: int = 0,
    block_date: date = BASE_DATE,
    block_id=None,
) -> dict:
    """Build a period block dict."""
    return {
        "block_id": block_id or BLOCK_ID,
        "block_date": block_date,
        "pgy1_residents": _uuids(pgy1),
        "other_residents": _uuids(other),
        "faculty_assigned": _uuids(faculty),
    }


def _violation(
    deficit: int = 1,
    block_date: date = BASE_DATE,
    pgy1: int = 2,
    other: int = 0,
) -> SupervisionViolation:
    """Build a SupervisionViolation for report tests."""
    required = (pgy1 * 2 + other + 3) // 4
    actual = max(0, required - deficit)
    return SupervisionViolation(
        block_id=BLOCK_ID,
        block_date=block_date,
        residents=pgy1 + other,
        pgy1_count=pgy1,
        pgy2_3_count=other,
        required_faculty=required,
        actual_faculty=actual,
        deficit=deficit,
        severity="CRITICAL" if deficit >= 2 else "HIGH",
        message=f"Block {block_date} deficit {deficit}",
    )


# ==================== Constants Tests ====================


class TestConstants:
    """Verify supervision ratio constants."""

    def test_pgy1_ratio(self):
        assert PGY1_RATIO == 2

    def test_other_ratio(self):
        assert OTHER_RATIO == 4


# ==================== Dataclass Tests ====================


class TestSupervisionViolation:
    """Test SupervisionViolation dataclass."""

    def test_construction(self):
        v = SupervisionViolation(
            block_id=BLOCK_ID,
            block_date=BASE_DATE,
            residents=4,
            pgy1_count=2,
            pgy2_3_count=2,
            required_faculty=2,
            actual_faculty=1,
            deficit=1,
            severity="HIGH",
            message="Test violation",
        )
        assert v.residents == 4
        assert v.deficit == 1
        assert v.severity == "HIGH"

    def test_none_block_id(self):
        v = SupervisionViolation(
            block_id=None,
            block_date=BASE_DATE,
            residents=2,
            pgy1_count=2,
            pgy2_3_count=0,
            required_faculty=1,
            actual_faculty=0,
            deficit=1,
            severity="HIGH",
            message="Test",
        )
        assert v.block_id is None


# ==================== SupervisionValidator Init ====================


class TestSupervisionValidatorInit:
    """Test SupervisionValidator initialization."""

    def test_defaults(self):
        v = SupervisionValidator()
        assert v.pgy1_ratio == 2
        assert v.other_ratio == 4


# ==================== calculate_required_faculty Tests ====================


class TestCalculateRequiredFaculty:
    """Test calculate_required_faculty method."""

    def test_zero_residents(self):
        """No residents -> 0 faculty needed."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(0, 0) == 0

    def test_one_pgy1(self):
        """1 PGY-1 = 2 units -> ceil(2/4) = 1."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(1, 0) == 1

    def test_two_pgy1(self):
        """2 PGY-1 = 4 units -> ceil(4/4) = 1."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(2, 0) == 1

    def test_three_pgy1(self):
        """3 PGY-1 = 6 units -> ceil(6/4) = 2."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(3, 0) == 2

    def test_four_pgy1(self):
        """4 PGY-1 = 8 units -> ceil(8/4) = 2."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(4, 0) == 2

    def test_one_other(self):
        """1 PGY-2/3 = 1 unit -> ceil(1/4) = 1."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(0, 1) == 1

    def test_four_other(self):
        """4 PGY-2/3 = 4 units -> ceil(4/4) = 1."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(0, 4) == 1

    def test_five_other(self):
        """5 PGY-2/3 = 5 units -> ceil(5/4) = 2."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(0, 5) == 2

    def test_mixed_scenario(self):
        """2 PGY-1 + 2 PGY-2/3 = 4+2 = 6 units -> ceil(6/4) = 2."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(2, 2) == 2

    def test_large_mixed_scenario(self):
        """5 PGY-1 + 8 PGY-2/3 = 10+8 = 18 units -> ceil(18/4) = 5."""
        v = SupervisionValidator()
        assert v.calculate_required_faculty(5, 8) == 5


# ==================== validate_block_supervision Tests ====================


class TestValidateBlockSupervision:
    """Test validate_block_supervision method."""

    def test_compliant_no_violation(self):
        """Adequate faculty -> None."""
        v = SupervisionValidator()
        result = v.validate_block_supervision(
            BLOCK_ID, BASE_DATE, _uuids(2), _uuids(2), _uuids(2)
        )
        assert result is None

    def test_no_residents_no_violation(self):
        """Zero residents -> None (0 faculty needed)."""
        v = SupervisionValidator()
        result = v.validate_block_supervision(BLOCK_ID, BASE_DATE, [], [], [])
        assert result is None

    def test_deficit_1_high_severity(self):
        """Deficit of 1 -> HIGH severity."""
        v = SupervisionValidator()
        # 3 PGY-1 = 6 units, need ceil(6/4) = 2, have 1
        result = v.validate_block_supervision(
            BLOCK_ID, BASE_DATE, _uuids(3), [], _uuids(1)
        )
        assert result is not None
        assert result.deficit == 1
        assert result.severity == "HIGH"

    def test_deficit_2_critical_severity(self):
        """Deficit >= 2 -> CRITICAL severity."""
        v = SupervisionValidator()
        # 5 PGY-1 = 10 units, need ceil(10/4) = 3, have 1
        result = v.validate_block_supervision(
            BLOCK_ID, BASE_DATE, _uuids(5), [], _uuids(1)
        )
        assert result is not None
        assert result.deficit == 2
        assert result.severity == "CRITICAL"

    def test_none_lists_handled(self):
        """None resident/faculty lists treated as empty."""
        v = SupervisionValidator()
        result = v.validate_block_supervision(BLOCK_ID, BASE_DATE, None, None, None)
        assert result is None

    def test_violation_fields(self):
        """Violation includes correct field values."""
        v = SupervisionValidator()
        pgy1 = _uuids(2)
        other = _uuids(3)
        faculty = _uuids(1)
        # 2*2 + 3 = 7 units, ceil(7/4) = ceil(1.75) = 2, have 1
        result = v.validate_block_supervision(BLOCK_ID, BASE_DATE, pgy1, other, faculty)
        assert result is not None
        assert result.block_id == BLOCK_ID
        assert result.block_date == BASE_DATE
        assert result.pgy1_count == 2
        assert result.pgy2_3_count == 3
        assert result.residents == 5
        assert result.required_faculty == 2
        assert result.actual_faculty == 1
        assert result.deficit == 1

    def test_date_in_message(self):
        """Block date appears in violation message."""
        v = SupervisionValidator()
        result = v.validate_block_supervision(
            BLOCK_ID, date(2025, 6, 15), _uuids(3), [], _uuids(1)
        )
        assert result is not None
        assert "2025-06-15" in result.message

    def test_exact_faculty_compliant(self):
        """Exactly required faculty count -> compliant."""
        v = SupervisionValidator()
        # 4 PGY-1 = 8 units, need 2
        result = v.validate_block_supervision(
            BLOCK_ID, BASE_DATE, _uuids(4), [], _uuids(2)
        )
        assert result is None

    def test_excess_faculty_compliant(self):
        """More than required -> compliant."""
        v = SupervisionValidator()
        result = v.validate_block_supervision(
            BLOCK_ID, BASE_DATE, _uuids(1), [], _uuids(5)
        )
        assert result is None


# ==================== validate_period_supervision Tests ====================


class TestValidatePeriodSupervision:
    """Test validate_period_supervision method."""

    def test_empty_period(self):
        """No blocks -> empty violations, 100% compliance."""
        v = SupervisionValidator()
        violations, metrics = v.validate_period_supervision([])
        assert len(violations) == 0
        assert metrics["total_blocks"] == 0
        assert metrics["compliance_rate"] == 100.0

    def test_all_compliant(self):
        """All blocks compliant -> 100% compliance."""
        v = SupervisionValidator()
        blocks = [
            _block(pgy1=2, faculty=1, block_date=BASE_DATE),
            _block(pgy1=2, faculty=1, block_date=BASE_DATE + timedelta(days=1)),
        ]
        violations, metrics = v.validate_period_supervision(blocks)
        assert len(violations) == 0
        assert metrics["compliance_rate"] == 100.0
        assert metrics["supervision_load_factors"]["all_compliant"] == 2

    def test_one_violation(self):
        """One non-compliant block -> 50% compliance (2 blocks)."""
        v = SupervisionValidator()
        blocks = [
            _block(pgy1=2, faculty=1, block_date=BASE_DATE),
            _block(pgy1=4, faculty=1, block_date=BASE_DATE + timedelta(days=1)),
        ]
        violations, metrics = v.validate_period_supervision(blocks)
        assert len(violations) == 1
        assert metrics["blocks_with_violations"] == 1
        assert metrics["compliance_rate"] == pytest.approx(50.0)

    def test_no_residents_block(self):
        """Block with no residents -> categorized as no_residents."""
        v = SupervisionValidator()
        blocks = [_block(pgy1=0, other=0, faculty=2)]
        violations, metrics = v.validate_period_supervision(blocks)
        assert len(violations) == 0
        assert metrics["supervision_load_factors"]["no_residents"] == 1

    def test_multi_deficit_tracking(self):
        """Deficit >= 2 tracked as multi_deficit."""
        v = SupervisionValidator()
        blocks = [_block(pgy1=5, faculty=1)]  # need 3, have 1, deficit 2
        violations, metrics = v.validate_period_supervision(blocks)
        assert len(violations) == 1
        assert metrics["supervision_load_factors"]["multi_deficit"] == 1

    def test_single_deficit_tracking(self):
        """Deficit == 1 tracked as single_deficit."""
        v = SupervisionValidator()
        blocks = [_block(pgy1=3, faculty=1)]  # need 2, have 1, deficit 1
        violations, metrics = v.validate_period_supervision(blocks)
        assert len(violations) == 1
        assert metrics["supervision_load_factors"]["single_deficit"] == 1

    def test_mixed_period(self):
        """Mix of compliant, violation, and no-resident blocks."""
        v = SupervisionValidator()
        blocks = [
            _block(pgy1=2, faculty=1, block_date=BASE_DATE),  # compliant
            _block(
                pgy1=4, faculty=1, block_date=BASE_DATE + timedelta(days=1)
            ),  # violation
            _block(
                pgy1=0, other=0, faculty=0, block_date=BASE_DATE + timedelta(days=2)
            ),  # no res
        ]
        violations, metrics = v.validate_period_supervision(blocks)
        assert len(violations) == 1
        assert metrics["total_blocks"] == 3
        lf = metrics["supervision_load_factors"]
        assert lf["all_compliant"] == 1
        assert lf["no_residents"] == 1
        assert lf["single_deficit"] + lf["multi_deficit"] == 1


# ==================== validate_attending_availability Tests ====================


class TestValidateAttendingAvailability:
    """Test validate_attending_availability method."""

    def test_all_available_no_message(self):
        v = SupervisionValidator()
        availability = {BASE_DATE: True, BASE_DATE + timedelta(days=1): True}
        result = v.validate_attending_availability(
            FACULTY_ID, availability, [BASE_DATE, BASE_DATE + timedelta(days=1)]
        )
        assert result is None

    def test_one_unavailable_returns_message(self):
        v = SupervisionValidator()
        availability = {BASE_DATE: True, BASE_DATE + timedelta(days=1): False}
        result = v.validate_attending_availability(
            FACULTY_ID, availability, [BASE_DATE, BASE_DATE + timedelta(days=1)]
        )
        assert result is not None
        assert "1 required supervision dates" in result

    def test_missing_date_defaults_unavailable(self):
        """Date not in availability dict defaults to False."""
        v = SupervisionValidator()
        result = v.validate_attending_availability(FACULTY_ID, {}, [BASE_DATE])
        assert result is not None

    def test_empty_required_dates(self):
        v = SupervisionValidator()
        result = v.validate_attending_availability(FACULTY_ID, {}, [])
        assert result is None

    def test_faculty_id_in_message(self):
        v = SupervisionValidator()
        result = v.validate_attending_availability(FACULTY_ID, {}, [BASE_DATE])
        assert result is not None
        assert str(FACULTY_ID) in result


# ==================== validate_specialty_supervision Tests ====================


class TestValidateSpecialtySupervision:
    """Test validate_specialty_supervision method."""

    def test_matching_specialty_valid(self):
        v = SupervisionValidator()
        faculty = [
            {"id": uuid4(), "specialties": ["Sports Medicine", "Family Medicine"]}
        ]
        is_valid, msg = v.validate_specialty_supervision("Sports Medicine", faculty)
        assert is_valid is True
        assert msg is None

    def test_no_matching_specialty_invalid(self):
        v = SupervisionValidator()
        faculty = [{"id": uuid4(), "specialties": ["Family Medicine"]}]
        is_valid, msg = v.validate_specialty_supervision("Dermatology", faculty)
        assert is_valid is False
        assert "Dermatology" in msg

    def test_empty_faculty_list(self):
        v = SupervisionValidator()
        is_valid, msg = v.validate_specialty_supervision("Sports Medicine", [])
        assert is_valid is False

    def test_faculty_without_specialties_key(self):
        """Faculty dict missing 'specialties' key -> treated as empty."""
        v = SupervisionValidator()
        faculty = [{"id": uuid4()}]
        is_valid, msg = v.validate_specialty_supervision("Any", faculty)
        assert is_valid is False

    def test_multiple_faculty_one_match(self):
        """Second faculty has the specialty -> valid."""
        v = SupervisionValidator()
        faculty = [
            {"id": uuid4(), "specialties": ["Pediatrics"]},
            {"id": uuid4(), "specialties": ["Dermatology"]},
        ]
        is_valid, msg = v.validate_specialty_supervision("Dermatology", faculty)
        assert is_valid is True


# ==================== validate_procedure_supervision Tests ====================


class TestValidateProcedureSupervision:
    """Test validate_procedure_supervision method."""

    def test_certified_faculty_valid(self):
        v = SupervisionValidator()
        faculty = [
            {
                "id": uuid4(),
                "procedure_certifications": ["Minor Procedures", "Joint Injection"],
            }
        ]
        is_valid, msg = v.validate_procedure_supervision("Minor Procedures", faculty)
        assert is_valid is True
        assert msg is None

    def test_no_certified_faculty_invalid(self):
        v = SupervisionValidator()
        faculty = [{"id": uuid4(), "procedure_certifications": ["Joint Injection"]}]
        is_valid, msg = v.validate_procedure_supervision("Colposcopy", faculty)
        assert is_valid is False
        assert "Colposcopy" in msg

    def test_empty_faculty_list(self):
        v = SupervisionValidator()
        is_valid, msg = v.validate_procedure_supervision("Minor Procedures", [])
        assert is_valid is False

    def test_faculty_without_certifications_key(self):
        v = SupervisionValidator()
        faculty = [{"id": uuid4()}]
        is_valid, msg = v.validate_procedure_supervision("Any", faculty)
        assert is_valid is False

    def test_multiple_faculty_one_certified(self):
        v = SupervisionValidator()
        faculty = [
            {"id": uuid4(), "procedure_certifications": []},
            {"id": uuid4(), "procedure_certifications": ["Colposcopy"]},
        ]
        is_valid, msg = v.validate_procedure_supervision("Colposcopy", faculty)
        assert is_valid is True


# ==================== get_supervision_deficit_report Tests ====================


class TestGetSupervisionDeficitReport:
    """Test get_supervision_deficit_report method."""

    def test_empty_violations(self):
        v = SupervisionValidator()
        report = v.get_supervision_deficit_report([])
        assert report["total_violations"] == 0
        assert report["critical_count"] == 0
        assert report["high_count"] == 0
        assert report["total_deficit"] == 0
        assert report["worst_case"] is None
        assert report["by_date"] == {}

    def test_single_high_violation(self):
        v = SupervisionValidator()
        violations = [_violation(deficit=1)]
        report = v.get_supervision_deficit_report(violations)
        assert report["total_violations"] == 1
        assert report["high_count"] == 1
        assert report["critical_count"] == 0
        assert report["total_deficit"] == 1

    def test_single_critical_violation(self):
        v = SupervisionValidator()
        violations = [_violation(deficit=3)]
        report = v.get_supervision_deficit_report(violations)
        assert report["critical_count"] == 1
        assert report["high_count"] == 0
        assert report["total_deficit"] == 3

    def test_worst_case_identified(self):
        v = SupervisionValidator()
        violations = [
            _violation(deficit=1, block_date=BASE_DATE),
            _violation(deficit=3, block_date=BASE_DATE + timedelta(days=1)),
            _violation(deficit=2, block_date=BASE_DATE + timedelta(days=2)),
        ]
        report = v.get_supervision_deficit_report(violations)
        assert report["worst_case"]["deficit"] == 3
        assert report["worst_case"]["date"] == BASE_DATE + timedelta(days=1)

    def test_by_date_grouping(self):
        v = SupervisionValidator()
        violations = [
            _violation(deficit=1, block_date=BASE_DATE),
            _violation(deficit=2, block_date=BASE_DATE),
            _violation(deficit=1, block_date=BASE_DATE + timedelta(days=1)),
        ]
        report = v.get_supervision_deficit_report(violations)
        assert len(report["by_date"][str(BASE_DATE)]) == 2
        assert len(report["by_date"][str(BASE_DATE + timedelta(days=1))]) == 1

    def test_total_deficit_sum(self):
        v = SupervisionValidator()
        violations = [
            _violation(deficit=1),
            _violation(deficit=2),
            _violation(deficit=3),
        ]
        report = v.get_supervision_deficit_report(violations)
        assert report["total_deficit"] == 6

    def test_mixed_severity_counts(self):
        v = SupervisionValidator()
        violations = [
            _violation(deficit=1),  # HIGH
            _violation(deficit=1),  # HIGH
            _violation(deficit=2),  # CRITICAL
            _violation(deficit=3),  # CRITICAL
        ]
        report = v.get_supervision_deficit_report(violations)
        assert report["high_count"] == 2
        assert report["critical_count"] == 2
        assert report["total_violations"] == 4
