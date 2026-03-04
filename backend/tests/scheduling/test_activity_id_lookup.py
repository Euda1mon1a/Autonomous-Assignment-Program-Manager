"""Tests for _get_activity_id_by_code disambiguation.

ARCH-006 (Basilisk's Gaze): When multiple activities share a
display_abbreviation (e.g., code='C' and code='fm_clinic' both have
display='C'), the lookup must prefer the exact code match.
"""

from uuid import uuid4

from app.models.activity import Activity, ActivityCategory
from app.scheduling.engine import SchedulingEngine


def _seed_activities(db):
    """Create the two activities that trigger the ambiguity."""
    generic_c = Activity(
        id=uuid4(),
        name="Clinic",
        code="C",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    fm_clinic = Activity(
        id=uuid4(),
        name="FM Clinic",
        code="fm_clinic",
        display_abbreviation="C",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add_all([generic_c, fm_clinic])
    db.commit()
    return generic_c, fm_clinic


def test_code_preferred_over_display_abbreviation(db):
    """_get_activity_id_by_code('C') must return code='C', not fm_clinic."""
    generic_c, fm_clinic = _seed_activities(db)

    from datetime import date

    engine = SchedulingEngine(db, date(2026, 1, 1), date(2026, 1, 28))

    result = engine._get_activity_id_by_code("C")
    assert result == generic_c.id, (
        f"Expected generic Clinic (code='C'), got {result}. fm_clinic.id={fm_clinic.id}"
    )


def test_display_abbreviation_fallback(db):
    """If no code match exists, display_abbreviation fallback still works."""
    # Create an activity with a unique display abbreviation
    act = Activity(
        id=uuid4(),
        name="Custom Activity",
        code="CUSTOM_INTERNAL",
        display_abbreviation="CX",
        activity_category=ActivityCategory.CLINICAL.value,
    )
    db.add(act)
    db.commit()

    from datetime import date

    engine = SchedulingEngine(db, date(2026, 1, 1), date(2026, 1, 28))

    # Lookup by display abbreviation (no activity has code='CX')
    result = engine._get_activity_id_by_code("CX")
    assert result == act.id


def test_case_insensitive_code_match(db):
    """Lookup is case-insensitive for both code and display abbreviation."""
    generic_c, fm_clinic = _seed_activities(db)

    from datetime import date

    engine = SchedulingEngine(db, date(2026, 1, 1), date(2026, 1, 28))

    # Uppercase input
    assert engine._get_activity_id_by_code("C") == generic_c.id
    # Lowercase input
    engine._activity_id_cache.clear()
    assert engine._get_activity_id_by_code("c") == generic_c.id
    # fm_clinic by name
    engine._activity_id_cache.clear()
    assert engine._get_activity_id_by_code("FM_CLINIC") == fm_clinic.id


def test_cache_stores_correct_id(db):
    """Cache must store the code-match, not a stale display-match."""
    generic_c, fm_clinic = _seed_activities(db)

    from datetime import date

    engine = SchedulingEngine(db, date(2026, 1, 1), date(2026, 1, 28))

    # First call populates cache
    first = engine._get_activity_id_by_code("C")
    # Second call hits cache
    second = engine._get_activity_id_by_code("C")

    assert first == second == generic_c.id


def test_activity_not_found_raises(db):
    """Missing activity code raises ActivityNotFoundError."""
    from datetime import date

    engine = SchedulingEngine(db, date(2026, 1, 1), date(2026, 1, 28))

    import pytest
    from app.scheduling.engine import ActivityNotFoundError

    with pytest.raises(ActivityNotFoundError):
        engine._get_activity_id_by_code("NONEXISTENT_CODE_XYZ")
