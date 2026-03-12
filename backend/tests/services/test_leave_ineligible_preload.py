"""Tests for leave-ineligible absence preload logic.

When a resident is on a rotation with leave_eligible=False, their absences
should NOT be converted to LV-AM/LV-PM preloads during that block.

Tests cover:
1. Sync _load_absences skips leave-ineligible residents
2. Sync _load_absences allows leave-eligible residents
3. Block scoping: leave-ineligible in Block N does not affect Block N+1
4. refresh_leave_preloads returns 0 for leave-ineligible residents
5. Async _load_absences skips leave-ineligible residents
6. Async _load_absences allows leave-eligible residents
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.models.absence import Absence
from app.models.activity import Activity, ActivityCategory
from app.models.block_assignment import BlockAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.services.sync_preload_service import SyncPreloadService
from app.utils.academic_blocks import get_block_dates, get_block_number_for_date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_activity(db, code: str, display: str, category: str) -> Activity:
    """Create an Activity row for testing."""
    activity = Activity(
        id=uuid4(),
        name=code,
        code=code,
        display_abbreviation=display,
        activity_category=category,
        is_protected=False,
        counts_toward_physical_capacity=False,
    )
    db.add(activity)
    return activity


def _seed_leave_activities(db) -> tuple[Activity, Activity]:
    """Create LV-AM and LV-PM activities required by the preload service."""
    lv_am = _create_activity(db, "LV-AM", "LV-AM", ActivityCategory.TIME_OFF.value)
    lv_pm = _create_activity(db, "LV-PM", "LV-PM", ActivityCategory.TIME_OFF.value)
    db.flush()
    return lv_am, lv_pm


def _make_resident(db, name: str = "Test Resident", pgy: int = 2) -> Person:
    """Create a resident Person."""
    person = Person(
        id=uuid4(),
        name=name,
        type="resident",
        pgy_level=pgy,
    )
    db.add(person)
    return person


def _make_template(
    db,
    name: str,
    abbreviation: str,
    leave_eligible: bool = True,
) -> RotationTemplate:
    """Create a RotationTemplate with explicit leave_eligible flag."""
    template = RotationTemplate(
        id=uuid4(),
        name=name,
        rotation_type="inpatient" if not leave_eligible else "outpatient",
        abbreviation=abbreviation,
        leave_eligible=leave_eligible,
    )
    db.add(template)
    return template


def _make_block_assignment(
    db,
    resident: Person,
    template: RotationTemplate,
    block_number: int,
    academic_year: int,
) -> BlockAssignment:
    """Create a BlockAssignment linking resident to rotation for a block."""
    ba = BlockAssignment(
        id=uuid4(),
        block_number=block_number,
        academic_year=academic_year,
        resident_id=resident.id,
        rotation_template_id=template.id,
    )
    db.add(ba)
    return ba


def _make_absence(
    db,
    person: Person,
    start_date: date,
    end_date: date,
    absence_type: str = "vacation",
) -> Absence:
    """Create a blocking absence for a person."""
    absence = Absence(
        id=uuid4(),
        person_id=person.id,
        start_date=start_date,
        end_date=end_date,
        absence_type=absence_type,
    )
    db.add(absence)
    return absence


def _count_leave_preloads(db, person_id) -> int:
    """Count HalfDayAssignment rows with LV-AM or LV-PM for a person."""
    return (
        db.query(HalfDayAssignment)
        .join(Activity, HalfDayAssignment.activity_id == Activity.id)
        .filter(
            HalfDayAssignment.person_id == person_id,
            Activity.code.in_(["LV-AM", "LV-PM"]),
        )
        .count()
    )


# ===========================================================================
# Sync SyncPreloadService._load_absences
# ===========================================================================


class TestSyncLoadAbsencesLeaveIneligible:
    """Tests for SyncPreloadService._load_absences leave-ineligible filtering."""

    def test_absences_skipped_when_on_leave_ineligible_rotation(self, db):
        """Absences should NOT produce LV preloads when resident is on a
        leave_eligible=False rotation in the current block."""
        _seed_leave_activities(db)

        resident = _make_resident(db, "FMIT Resident")
        fmit_template = _make_template(
            db, "FMIT Inpatient", "FMIT", leave_eligible=False
        )

        block_number = 10
        academic_year = 2025
        _make_block_assignment(db, resident, fmit_template, block_number, academic_year)

        block_dates = get_block_dates(block_number, academic_year)
        # Absence in the middle of the block
        _make_absence(
            db,
            resident,
            block_dates.start_date + timedelta(days=3),
            block_dates.start_date + timedelta(days=5),
        )
        db.commit()

        service = SyncPreloadService(db)
        count = service._load_absences(
            block_dates.start_date,
            block_dates.end_date,
            block_number,
            academic_year,
        )

        assert count == 0, "No preloads should be created for leave-ineligible resident"
        assert _count_leave_preloads(db, resident.id) == 0

    def test_absences_loaded_when_on_leave_eligible_rotation(self, db):
        """Absences SHOULD produce LV preloads when resident is on a
        leave_eligible=True rotation."""
        _seed_leave_activities(db)

        resident = _make_resident(db, "Elective Resident")
        elective_template = _make_template(
            db, "Sports Medicine", "SM", leave_eligible=True
        )

        block_number = 10
        academic_year = 2025
        _make_block_assignment(
            db, resident, elective_template, block_number, academic_year
        )

        block_dates = get_block_dates(block_number, academic_year)
        absence_start = block_dates.start_date + timedelta(days=3)
        absence_end = block_dates.start_date + timedelta(days=5)
        _make_absence(db, resident, absence_start, absence_end)
        db.commit()

        service = SyncPreloadService(db)
        count = service._load_absences(
            block_dates.start_date,
            block_dates.end_date,
            block_number,
            academic_year,
        )

        # 3 days * 2 slots (AM+PM) = 6 preloads
        expected_days = (absence_end - absence_start).days + 1
        assert count == expected_days * 2
        assert _count_leave_preloads(db, resident.id) == expected_days * 2

    def test_block_scoping_ineligible_in_block_n_eligible_in_block_n_plus_1(self, db):
        """A resident on FMIT in Block 12 should still get absences loaded
        in Block 13 if Block 13 rotation is leave-eligible."""
        _seed_leave_activities(db)

        resident = _make_resident(db, "Block Scoped Resident")
        fmit_template = _make_template(db, "FMIT", "FMIT", leave_eligible=False)
        elective_template = _make_template(
            db, "Dermatology", "DERM", leave_eligible=True
        )

        academic_year = 2025
        # Block 12: leave-ineligible
        _make_block_assignment(db, resident, fmit_template, 12, academic_year)
        # Block 13: leave-eligible
        _make_block_assignment(db, resident, elective_template, 13, academic_year)

        block_13_dates = get_block_dates(13, academic_year)
        # Absence in Block 13
        absence_start = block_13_dates.start_date + timedelta(days=1)
        absence_end = block_13_dates.start_date + timedelta(days=3)
        _make_absence(db, resident, absence_start, absence_end)
        db.commit()

        service = SyncPreloadService(db)

        # Block 12 should produce 0 (resident is leave-ineligible there)
        block_12_dates = get_block_dates(12, academic_year)
        count_12 = service._load_absences(
            block_12_dates.start_date,
            block_12_dates.end_date,
            12,
            academic_year,
        )
        assert count_12 == 0

        # Block 13 should produce preloads (resident IS leave-eligible there)
        count_13 = service._load_absences(
            block_13_dates.start_date,
            block_13_dates.end_date,
            13,
            academic_year,
        )
        expected_days = (absence_end - absence_start).days + 1
        assert count_13 == expected_days * 2
        assert _count_leave_preloads(db, resident.id) == expected_days * 2

    def test_no_block_assignment_still_loads_absences(self, db):
        """If a resident has no BlockAssignment (edge case), they are NOT in
        the leave-ineligible set, so absences should still load."""
        _seed_leave_activities(db)

        resident = _make_resident(db, "Unassigned Resident")

        block_number = 10
        academic_year = 2025
        block_dates = get_block_dates(block_number, academic_year)

        absence_start = block_dates.start_date + timedelta(days=1)
        absence_end = block_dates.start_date + timedelta(days=2)
        _make_absence(db, resident, absence_start, absence_end)
        db.commit()

        service = SyncPreloadService(db)
        count = service._load_absences(
            block_dates.start_date,
            block_dates.end_date,
            block_number,
            academic_year,
        )

        expected_days = (absence_end - absence_start).days + 1
        assert count == expected_days * 2

    def test_mixed_residents_only_eligible_get_preloads(self, db):
        """When two residents have absences but one is leave-ineligible,
        only the eligible resident should get preloads."""
        _seed_leave_activities(db)

        resident_fmit = _make_resident(db, "FMIT Resident")
        resident_sm = _make_resident(db, "SM Resident")
        fmit_template = _make_template(db, "FMIT", "FMIT", leave_eligible=False)
        sm_template = _make_template(db, "SM", "SM", leave_eligible=True)

        block_number = 10
        academic_year = 2025
        _make_block_assignment(
            db, resident_fmit, fmit_template, block_number, academic_year
        )
        _make_block_assignment(
            db, resident_sm, sm_template, block_number, academic_year
        )

        block_dates = get_block_dates(block_number, academic_year)
        absence_start = block_dates.start_date + timedelta(days=2)
        absence_end = block_dates.start_date + timedelta(days=4)
        _make_absence(db, resident_fmit, absence_start, absence_end)
        _make_absence(db, resident_sm, absence_start, absence_end)
        db.commit()

        service = SyncPreloadService(db)
        count = service._load_absences(
            block_dates.start_date,
            block_dates.end_date,
            block_number,
            academic_year,
        )

        expected_days = (absence_end - absence_start).days + 1
        # Only SM resident's absences
        assert count == expected_days * 2
        assert _count_leave_preloads(db, resident_fmit.id) == 0
        assert _count_leave_preloads(db, resident_sm.id) == expected_days * 2


# ===========================================================================
# Sync SyncPreloadService.refresh_leave_preloads
# ===========================================================================


class TestRefreshLeavePreloadsLeaveIneligible:
    """Tests for refresh_leave_preloads returning 0 for leave-ineligible."""

    def test_refresh_returns_zero_for_leave_ineligible(self, db):
        """refresh_leave_preloads should return 0 and create no preloads
        when the person is on a leave-ineligible rotation."""
        _seed_leave_activities(db)

        resident = _make_resident(db, "FMIT Resident")
        fmit_template = _make_template(db, "FMIT", "FMIT", leave_eligible=False)

        block_number = 10
        academic_year = 2025
        _make_block_assignment(db, resident, fmit_template, block_number, academic_year)

        block_dates = get_block_dates(block_number, academic_year)
        absence_start = block_dates.start_date + timedelta(days=2)
        absence_end = block_dates.start_date + timedelta(days=4)
        _make_absence(db, resident, absence_start, absence_end)
        db.commit()

        service = SyncPreloadService(db)
        count = service.refresh_leave_preloads(resident.id, absence_start, absence_end)

        assert count == 0
        assert _count_leave_preloads(db, resident.id) == 0

    def test_refresh_creates_preloads_for_leave_eligible(self, db):
        """refresh_leave_preloads should create preloads for leave-eligible."""
        _seed_leave_activities(db)

        resident = _make_resident(db, "SM Resident")
        sm_template = _make_template(db, "SM", "SM", leave_eligible=True)

        block_number = 10
        academic_year = 2025
        _make_block_assignment(db, resident, sm_template, block_number, academic_year)

        block_dates = get_block_dates(block_number, academic_year)
        absence_start = block_dates.start_date + timedelta(days=2)
        absence_end = block_dates.start_date + timedelta(days=4)
        _make_absence(db, resident, absence_start, absence_end)
        db.commit()

        service = SyncPreloadService(db)
        count = service.refresh_leave_preloads(resident.id, absence_start, absence_end)

        expected_days = (absence_end - absence_start).days + 1
        assert count == expected_days * 2
        assert _count_leave_preloads(db, resident.id) == expected_days * 2

    def test_refresh_derives_block_from_date(self, db):
        """refresh_leave_preloads uses get_block_number_for_date to scope the
        leave-ineligible check, so the block is derived from start_date."""
        _seed_leave_activities(db)

        resident = _make_resident(db, "Scoped Resident")
        fmit_template = _make_template(db, "FMIT", "FMIT", leave_eligible=False)
        sm_template = _make_template(db, "SM", "SM", leave_eligible=True)

        academic_year = 2025
        # Resident on FMIT in Block 12, SM in Block 13
        _make_block_assignment(db, resident, fmit_template, 12, academic_year)
        _make_block_assignment(db, resident, sm_template, 13, academic_year)

        block_13_dates = get_block_dates(13, academic_year)
        absence_start = block_13_dates.start_date + timedelta(days=1)
        absence_end = block_13_dates.start_date + timedelta(days=2)
        _make_absence(db, resident, absence_start, absence_end)
        db.commit()

        service = SyncPreloadService(db)

        # Refresh for dates in Block 13 — should create preloads
        # because Block 13 rotation is leave-eligible
        count = service.refresh_leave_preloads(resident.id, absence_start, absence_end)

        expected_days = (absence_end - absence_start).days + 1
        assert count == expected_days * 2


# ===========================================================================
# Async PreloadService._load_absences
# ===========================================================================


@pytest.mark.asyncio
class TestAsyncLoadAbsencesLeaveIneligible:
    """Tests for async PreloadService._load_absences leave-ineligible filtering.

    Uses the AsyncSessionWrapper from the root conftest to wrap the sync
    db fixture for async compatibility.
    """

    async def test_absences_skipped_when_on_leave_ineligible_rotation(
        self, db, async_db_session
    ):
        """Async path: absences should NOT produce LV preloads when resident
        is on a leave_eligible=False rotation."""
        from app.services.preload_service import PreloadService

        _seed_leave_activities(db)

        resident = _make_resident(db, "Async FMIT Resident")
        fmit_template = _make_template(db, "FMIT Async", "FMIT", leave_eligible=False)

        block_number = 10
        academic_year = 2025
        _make_block_assignment(db, resident, fmit_template, block_number, academic_year)

        block_dates = get_block_dates(block_number, academic_year)
        _make_absence(
            db,
            resident,
            block_dates.start_date + timedelta(days=3),
            block_dates.start_date + timedelta(days=5),
        )
        db.commit()

        service = PreloadService(async_db_session)
        count = await service._load_absences(
            block_dates.start_date,
            block_dates.end_date,
            block_number,
            academic_year,
        )

        assert count == 0
        assert _count_leave_preloads(db, resident.id) == 0

    async def test_absences_loaded_when_on_leave_eligible_rotation(
        self, db, async_db_session
    ):
        """Async path: absences SHOULD produce LV preloads when resident
        is on a leave_eligible=True rotation."""
        from app.services.preload_service import PreloadService

        _seed_leave_activities(db)

        resident = _make_resident(db, "Async SM Resident")
        sm_template = _make_template(db, "SM Async", "SM", leave_eligible=True)

        block_number = 10
        academic_year = 2025
        _make_block_assignment(db, resident, sm_template, block_number, academic_year)

        block_dates = get_block_dates(block_number, academic_year)
        absence_start = block_dates.start_date + timedelta(days=3)
        absence_end = block_dates.start_date + timedelta(days=5)
        _make_absence(db, resident, absence_start, absence_end)
        db.commit()

        service = PreloadService(async_db_session)
        count = await service._load_absences(
            block_dates.start_date,
            block_dates.end_date,
            block_number,
            academic_year,
        )

        expected_days = (absence_end - absence_start).days + 1
        assert count == expected_days * 2
        assert _count_leave_preloads(db, resident.id) == expected_days * 2
