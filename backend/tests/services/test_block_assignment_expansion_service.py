"""Tests for BlockAssignmentExpansionService scheduling helpers."""

from datetime import date

from app.models.rotation_template import RotationTemplate
from app.services.block_assignment_expansion_service import (
    BlockAssignmentExpansionService,
    LEC_EXEMPT_ROTATIONS,
    NIGHT_FLOAT_PATTERNS,
)


def test_is_last_wednesday_of_block() -> None:
    service = BlockAssignmentExpansionService(db=None)  # type: ignore[arg-type]

    # Wednesday with end date Thursday -> last Wednesday
    current = date(2026, 1, 28)  # Wednesday
    end_date = date(2026, 1, 29)
    assert service._is_last_wednesday_of_block(current, end_date) is True

    # Wednesday with another Wednesday ahead -> not last
    end_date = date(2026, 2, 10)
    assert service._is_last_wednesday_of_block(current, end_date) is False


def test_should_have_continuity_clinic() -> None:
    service = BlockAssignmentExpansionService(db=None)  # type: ignore[arg-type]

    wed = date(2026, 1, 28)  # Wednesday
    tue = date(2026, 1, 27)  # Tuesday
    mon = date(2026, 1, 26)  # Monday

    assert service._should_have_continuity_clinic(wed, "AM", 1) is True
    assert service._should_have_continuity_clinic(tue, "PM", 2) is True
    assert service._should_have_continuity_clinic(mon, "PM", 3) is True

    assert service._should_have_continuity_clinic(wed, "PM", 1) is False
    assert service._should_have_continuity_clinic(tue, "AM", 2) is False
    assert service._should_have_continuity_clinic(mon, "AM", 3) is False


def test_ldnf_assignment_patterns() -> None:
    service = BlockAssignmentExpansionService(db=None)  # type: ignore[arg-type]

    friday = date(2026, 1, 30)  # Friday
    monday = date(2026, 1, 26)  # Monday
    saturday = date(2026, 1, 31)  # Saturday
    last_wed = date(2026, 1, 28)  # Wednesday

    assert service._get_ldnf_assignment(friday, "AM", False) == "C"
    assert service._get_ldnf_assignment(friday, "PM", False) == "OFF"
    assert service._get_ldnf_assignment(monday, "AM", False) == "OFF"
    assert service._get_ldnf_assignment(monday, "PM", False) == "LDNF"
    assert service._get_ldnf_assignment(saturday, "AM", False) == "W"
    assert service._get_ldnf_assignment(saturday, "PM", False) == "W"

    assert service._get_ldnf_assignment(last_wed, "AM", True) == "LEC"
    assert service._get_ldnf_assignment(last_wed, "PM", True) == "ADV"


def test_night_float_template_abbrev() -> None:
    service = BlockAssignmentExpansionService(db=None)  # type: ignore[arg-type]

    rotation = RotationTemplate(abbreviation="NF")
    assert (
        service._get_night_float_template_abbrev(rotation, "AM")
        == (NIGHT_FLOAT_PATTERNS["NF"][0])
    )
    assert (
        service._get_night_float_template_abbrev(rotation, "PM")
        == (NIGHT_FLOAT_PATTERNS["NF"][1])
    )


def test_should_use_lec_respects_exempt_rotations() -> None:
    service = BlockAssignmentExpansionService(db=None)  # type: ignore[arg-type]

    wed = date(2026, 1, 28)  # Wednesday
    rotation = RotationTemplate(abbreviation="IM")
    assert service._should_use_lec(rotation, wed) is True

    exempt_rotation = RotationTemplate(abbreviation=next(iter(LEC_EXEMPT_ROTATIONS)))
    assert service._should_use_lec(exempt_rotation, wed) is False


def test_weekly_patterns_default_activity_uses_rotation_type() -> None:
    service = BlockAssignmentExpansionService(db=None)  # type: ignore[arg-type]

    rotation = RotationTemplate(rotation_type="inpatient", includes_weekend_work=False)
    rotation.weekly_patterns = []

    patterns = service._get_weekly_patterns(rotation)

    assert patterns[(1, "AM", None)].activity_type == "inpatient"
