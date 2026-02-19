from uuid import uuid4

import pytest

from app.core.exceptions import ActivityNotFoundError
from app.models.activity import Activity, ActivityCategory
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.preload import ActivityCache, TemplateCache


def _create_activity(db, code: str, display: str) -> Activity:
    activity = Activity(
        id=uuid4(),
        name=code,
        code=code,
        display_abbreviation=display,
        activity_category=ActivityCategory.CLINICAL.value,
        is_protected=False,
        counts_toward_physical_capacity=False,
    )
    db.add(activity)
    return activity


def _create_template(db, abbreviation: str, name: str) -> RotationTemplate:
    template = RotationTemplate(
        id=uuid4(),
        name=name,
        rotation_type="inpatient",
        abbreviation=abbreviation,
        display_abbreviation=abbreviation,
    )
    db.add(template)
    return template


def test_activity_cache_uses_fallbacks_and_optional(db):
    exact = _create_activity(db, "CALL", "CALL")
    display = _create_activity(db, "FM", "FMC")
    db.commit()

    cache = ActivityCache(db)

    assert cache.get("CALL") == exact.id
    assert cache.get("call") == exact.id
    assert cache.get("FMC") == display.id
    assert cache.get("UNKNOWN", required=False) is None

    with pytest.raises(ActivityNotFoundError):
        cache.get("MISSING")


def test_template_cache_prefers_pgy_specific_then_alias(db):
    resident = Person(
        id=uuid4(),
        name="Resident Two",
        type="resident",
        pgy_level=2,
    )
    db.add(resident)

    _create_template(db, "FMIT", "FMIT")
    pgy_template = _create_template(db, "FMIT-PGY2", "FMIT PGY2")
    alias_template = _create_template(db, "PNF", "PEDNF alias")
    db.commit()

    cache = TemplateCache(db)

    assert cache.get("FMIT", person=resident) == pgy_template
    assert cache.get("PEDNF", person=resident) == alias_template
