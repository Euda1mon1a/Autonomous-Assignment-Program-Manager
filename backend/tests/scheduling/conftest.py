"""
Pytest fixtures for scheduling tests - includes ROSETTA ground truth fixtures.

ROSETTA is the "answer key" - the correct Block 10 schedule.
These fixtures load ROSETTA and provide structured access for TDD testing.
"""

from datetime import date
from pathlib import Path

import pytest

from app.utils.rosetta_parser import (
    RosettaAssignment,
    get_last_wednesday_assignments,
    get_rosetta_by_date,
    get_rosetta_by_resident,
    get_wednesday_am_assignments,
    parse_rosetta,
)

# Path to ROSETTA ground truth file
# Works in both host (backend/tests/...) and container (/app/tests/...)
_tests_dir = Path(__file__).parent.parent  # backend/tests or /app/tests
_backend_dir = _tests_dir.parent  # backend or /app

# Try container path first, then host path
_container_path = _backend_dir / "docs" / "scheduling" / "Block10_ROSETTA_CORRECT.xlsx"
_host_path = (
    _backend_dir.parent / "docs" / "scheduling" / "Block10_ROSETTA_CORRECT.xlsx"
)

ROSETTA_PATH = _container_path if _container_path.exists() else _host_path


# ============================================================================
# ROSETTA Ground Truth Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def rosetta_assignments() -> list[RosettaAssignment]:
    """
    Load ALL ground truth assignments from ROSETTA.

    This is the source of truth - 9 residents × 56 half-day slots = ~504 assignments.
    Scope is "module" to avoid re-parsing the xlsx for every test.
    """
    if not ROSETTA_PATH.exists():
        pytest.skip(f"ROSETTA file not found: {ROSETTA_PATH}")
    return parse_rosetta(ROSETTA_PATH)


@pytest.fixture(scope="module")
def rosetta_by_resident(
    rosetta_assignments: list[RosettaAssignment],
) -> dict[str, list[RosettaAssignment]]:
    """Group ROSETTA assignments by resident name."""
    return get_rosetta_by_resident(rosetta_assignments)


@pytest.fixture(scope="module")
def rosetta_by_date(
    rosetta_assignments: list[RosettaAssignment],
) -> dict[date, list[RosettaAssignment]]:
    """Group ROSETTA assignments by date."""
    return get_rosetta_by_date(rosetta_assignments)


# ============================================================================
# Pattern-Specific Fixtures (for targeted testing)
# ============================================================================


@pytest.fixture
def expected_travis_kap(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    Travis (KAP) pattern - tests Kapiolani L&D rules.

    Key patterns to verify:
    - Mon PM = OFF
    - Tue = OFF/OFF
    - Wed AM = C (continuity clinic)
    - Wed PM = LEC
    - Thu-Sun = KAP/KAP
    """
    return rosetta_by_resident.get("Travis, Colin", [])


@pytest.fixture
def expected_headid_ldnf(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    Headid (LDNF) pattern - tests L&D Night Float rules.

    Key patterns to verify:
    - Mon-Thu = OFF/LDNF
    - Fri AM = C (FRIDAY morning clinic, not Wed!)
    - Fri PM = OFF
    - Sat-Sun = W/W
    """
    return rosetta_by_resident.get("Headid, Ronald", [])


@pytest.fixture
def expected_sloss_proc(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    Sloss (PROC) pattern - tests intern continuity rule.

    Key patterns to verify:
    - Wed AM = C (intern continuity, not PR!)
    - Other days = PR/C
    """
    return rosetta_by_resident.get("Sloss, Meleighe", [])


@pytest.fixture
def expected_monsivais_im(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    Monsivais (IM) pattern - tests intern continuity with IM rotation.

    Key patterns to verify:
    - Wed AM = C (intern continuity, not IM!)
    - Other days = IM/IM (IM works weekends)
    """
    return rosetta_by_resident.get("Monsivais, Joshua", [])


@pytest.fixture
def expected_you_neuro_nf(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    You (NEURO→NF) pattern - tests mid-block transition.

    Key patterns to verify:
    - First half (before Mar 23): NEURO/C
    - Second half (Mar 23+): OFF/NF
    - Last Wednesday = LEC/ADV
    """
    return rosetta_by_resident.get("You, Jae", [])


@pytest.fixture
def expected_wilhelm_pedw_pednf(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    Wilhelm (PedW→PedNF) pattern - tests mid-block + intern continuity.

    Key patterns to verify:
    - First half: PedW, Wed AM = C (intern continuity)
    - Second half: OFF/PedNF, Wed AM still = C
    """
    return rosetta_by_resident.get("Wilhelm, Clara", [])


@pytest.fixture
def expected_byrnes_pednf_pedw(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    Byrnes (PedNF→PedW) pattern - tests reverse mid-block.

    Key patterns to verify:
    - First half: OFF/PedNF
    - Second half: PedW, Wed AM = C (intern continuity)
    """
    return rosetta_by_resident.get("Byrnes, Katherine", [])


@pytest.fixture
def expected_sawyer_fmc(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    Sawyer (FMC) pattern - tests FMC clinic rotation.

    Key patterns to verify:
    - High clinic load (C throughout)
    - Wed AM = C (intern continuity)
    - Wed PM = LEC
    """
    return rosetta_by_resident.get("Sawyer, Tessa", [])


@pytest.fixture
def expected_chen_fmc(
    rosetta_by_resident: dict[str, list[RosettaAssignment]],
) -> list[RosettaAssignment]:
    """
    Chen (FMC) pattern - PGY-2, no intern continuity rule.

    Key patterns to verify:
    - High clinic load (C throughout)
    - No special Wed AM rule (not an intern)
    - Wed PM = LEC
    """
    return rosetta_by_resident.get("Chen, Michael", [])


# ============================================================================
# Rule-Specific Fixtures
# ============================================================================


@pytest.fixture
def rosetta_intern_wed_am(
    rosetta_assignments: list[RosettaAssignment],
) -> list[RosettaAssignment]:
    """
    All Wednesday AM slots for PGY-1 interns.

    Used to test intern continuity rule: all PGY-1 should have C on Wed AM
    (except exempt rotations like NF, LDNF, TDY).
    """
    return get_wednesday_am_assignments(rosetta_assignments, pgy_filter=1)


@pytest.fixture
def rosetta_last_wednesday(
    rosetta_assignments: list[RosettaAssignment],
) -> list[RosettaAssignment]:
    """
    All assignments for last Wednesday (Apr 8, 2026).

    Used to test last Wednesday rule: AM = LEC, PM = ADV for everyone.
    """
    return get_last_wednesday_assignments(rosetta_assignments)


@pytest.fixture
def rosetta_wednesday_pm_all(
    rosetta_assignments: list[RosettaAssignment],
) -> list[RosettaAssignment]:
    """
    All Wednesday PM slots.

    Used to test Wednesday PM LEC rule (should be LEC for most, except NF/LDNF/TDY).
    """
    return [
        a
        for a in rosetta_assignments
        if a.date.weekday() == 2 and a.time_of_day == "PM"
    ]


# ============================================================================
# Helper Constants
# ============================================================================

# Block 10 dates
BLOCK_10_START = date(2026, 3, 12)  # Thursday
BLOCK_10_END = date(2026, 4, 8)  # Wednesday
MID_BLOCK_DATE = date(2026, 3, 23)  # Monday (start of second half)
LAST_WEDNESDAY = date(2026, 4, 8)

# Resident to rotation mapping (from ROSETTA)
ROSETTA_RESIDENTS = {
    "Travis, Colin": {"pgy": 1, "rotation1": "KAP", "rotation2": None},
    "Headid, Ronald": {"pgy": 2, "rotation1": "LDNF", "rotation2": None},
    "Sloss, Meleighe": {"pgy": 1, "rotation1": "PROC", "rotation2": None},
    "Monsivais, Joshua": {"pgy": 1, "rotation1": "IM", "rotation2": None},
    "You, Jae": {"pgy": 3, "rotation1": "NEURO", "rotation2": "NF"},
    "Wilhelm, Clara": {"pgy": 1, "rotation1": "Peds Ward", "rotation2": "Peds NF"},
    "Byrnes, Katherine": {"pgy": 1, "rotation1": "Peds NF", "rotation2": "Peds Ward"},
    "Sawyer, Tessa": {"pgy": 1, "rotation1": "FMC", "rotation2": None},
    "Chen, Michael": {"pgy": 2, "rotation1": "FMC", "rotation2": None},
}
