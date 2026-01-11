"""Tests for FacultyAssignmentExpansionService.

Tests the 56-slot expansion rule for faculty:
- All faculty get exactly 56 assignments per block
- Existing assignments (FMIT, clinic, supervision) are preserved
- Empty weekday slots get GME-AM/GME-PM
- Weekend slots get W-AM/W-PM
- Absence slots get LV-AM/LV-PM
"""

import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.faculty_assignment_expansion_service import (
    FacultyAssignmentExpansionService,
)


class TestFacultyAssignmentExpansionService:
    """Test suite for FacultyAssignmentExpansionService."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock DB."""
        return FacultyAssignmentExpansionService(mock_db)

    @pytest.fixture
    def mock_faculty(self):
        """Create mock faculty member."""
        faculty = MagicMock()
        faculty.id = uuid.uuid4()
        faculty.type = "faculty"
        faculty.is_active = True
        faculty.name = "Test Faculty"
        return faculty

    @pytest.fixture
    def mock_block(self):
        """Create mock block."""
        block = MagicMock()
        block.id = uuid.uuid4()
        block.date = date(2026, 1, 5)  # Monday
        block.time_of_day = "AM"
        return block

    @pytest.fixture
    def mock_gme_template(self):
        """Create mock GME rotation template."""
        template = MagicMock()
        template.id = uuid.uuid4()
        template.abbreviation = "GME-AM"
        template.template_category = "absence"
        return template

    @pytest.fixture
    def mock_w_template(self):
        """Create mock Weekend rotation template."""
        template = MagicMock()
        template.id = uuid.uuid4()
        template.abbreviation = "W-AM"
        template.template_category = "absence"
        return template

    @pytest.fixture
    def mock_lv_template(self):
        """Create mock Leave rotation template."""
        template = MagicMock()
        template.id = uuid.uuid4()
        template.abbreviation = "LV-AM"
        template.template_category = "absence"
        return template


class TestFillSlot:
    """Test _fill_slot method."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FacultyAssignmentExpansionService(mock_db)

    def test_returns_none_if_slot_already_assigned(self, service):
        """Existing assignment should not be overwritten."""
        person = MagicMock()
        person.id = uuid.uuid4()

        block = MagicMock()
        block.id = uuid.uuid4()

        # Pre-populate existing assignment
        service._block_cache[(date(2026, 1, 5), "AM")] = block
        service._existing_assignments[(person.id, block.id)] = MagicMock()

        result = service._fill_slot(
            person=person,
            slot_date=date(2026, 1, 5),
            time_of_day="AM",
            is_weekend=False,
            is_absent=False,
            schedule_run_id=None,
            created_by="test",
        )

        assert result is None

    def test_creates_weekend_assignment(self, service):
        """Weekend slots should use W-AM/W-PM templates."""
        person = MagicMock()
        person.id = uuid.uuid4()

        block = MagicMock()
        block.id = uuid.uuid4()

        w_template = MagicMock()
        w_template.id = uuid.uuid4()

        service._block_cache[(date(2026, 1, 4), "AM")] = block  # Saturday
        service._placeholder_templates["W-AM"] = w_template

        result = service._fill_slot(
            person=person,
            slot_date=date(2026, 1, 4),
            time_of_day="AM",
            is_weekend=True,
            is_absent=False,
            schedule_run_id=None,
            created_by="test",
        )

        assert result is not None
        assert result.rotation_template_id == w_template.id

    def test_creates_absence_assignment(self, service):
        """Absence slots should use LV-AM/LV-PM templates."""
        person = MagicMock()
        person.id = uuid.uuid4()

        block = MagicMock()
        block.id = uuid.uuid4()

        lv_template = MagicMock()
        lv_template.id = uuid.uuid4()

        service._block_cache[(date(2026, 1, 5), "AM")] = block
        service._placeholder_templates["LV-AM"] = lv_template

        result = service._fill_slot(
            person=person,
            slot_date=date(2026, 1, 5),
            time_of_day="AM",
            is_weekend=False,
            is_absent=True,
            schedule_run_id=None,
            created_by="test",
        )

        assert result is not None
        assert result.rotation_template_id == lv_template.id

    def test_creates_gme_assignment_for_empty_weekday(self, service):
        """Empty weekday slots should use GME-AM/GME-PM templates."""
        person = MagicMock()
        person.id = uuid.uuid4()

        block = MagicMock()
        block.id = uuid.uuid4()
        block.is_holiday = False  # Explicitly set for test

        gme_template = MagicMock()
        gme_template.id = uuid.uuid4()

        service._block_cache[(date(2026, 1, 5), "AM")] = block  # Monday
        service._placeholder_templates["GME-AM"] = gme_template

        result = service._fill_slot(
            person=person,
            slot_date=date(2026, 1, 5),
            time_of_day="AM",
            is_weekend=False,
            is_absent=False,
            schedule_run_id=None,
            created_by="test",
        )

        assert result is not None
        assert result.rotation_template_id == gme_template.id

    def test_creates_holiday_assignment(self, service):
        """Holiday slots should use HOL-AM/HOL-PM templates."""
        person = MagicMock()
        person.id = uuid.uuid4()

        block = MagicMock()
        block.id = uuid.uuid4()
        block.is_holiday = True  # Federal holiday

        hol_template = MagicMock()
        hol_template.id = uuid.uuid4()

        service._block_cache[(date(2026, 1, 1), "AM")] = block  # New Year's Day
        service._placeholder_templates["HOL-AM"] = hol_template

        result = service._fill_slot(
            person=person,
            slot_date=date(2026, 1, 1),
            time_of_day="AM",
            is_weekend=False,
            is_absent=False,
            schedule_run_id=None,
            created_by="test",
        )

        assert result is not None
        assert result.rotation_template_id == hol_template.id


class TestFiftySixSlotRule:
    """Test that faculty get exactly 56 assignments per block."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FacultyAssignmentExpansionService(mock_db)

    def test_fill_single_faculty_creates_56_slots(self, service):
        """Faculty member should get 56 assignments for a 28-day block."""
        person = MagicMock()
        person.id = uuid.uuid4()

        # Create 56 blocks (28 days × 2 slots)
        start_date = date(2026, 1, 5)  # Monday
        for day_offset in range(28):
            current_date = start_date + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = MagicMock()
                block.id = uuid.uuid4()
                service._block_cache[(current_date, time_of_day)] = block

        # Create placeholder templates
        for abbrev in ["W-AM", "W-PM", "LV-AM", "LV-PM", "GME-AM", "GME-PM"]:
            template = MagicMock()
            template.id = uuid.uuid4()
            service._placeholder_templates[abbrev] = template

        # No existing assignments
        service._existing_assignments = {}
        service._absence_cache = {}

        result = service._fill_single_faculty(
            person=person,
            start_date=start_date,
            end_date=start_date + timedelta(days=27),
            schedule_run_id=None,
            created_by="test",
        )

        # Should create 56 assignments
        assert len(result) == 56

    def test_preserves_existing_assignments(self, service):
        """Existing assignments should not be overwritten."""
        person = MagicMock()
        person.id = uuid.uuid4()

        # Create blocks for 2 days (4 slots)
        start_date = date(2026, 1, 5)
        blocks = {}
        for day_offset in range(2):
            current_date = start_date + timedelta(days=day_offset)
            for time_of_day in ["AM", "PM"]:
                block = MagicMock()
                block.id = uuid.uuid4()
                blocks[(current_date, time_of_day)] = block
                service._block_cache[(current_date, time_of_day)] = block

        # Pre-populate 2 existing assignments
        existing_key1 = (person.id, blocks[(start_date, "AM")].id)
        existing_key2 = (person.id, blocks[(start_date, "PM")].id)
        service._existing_assignments[existing_key1] = MagicMock()
        service._existing_assignments[existing_key2] = MagicMock()

        # Create placeholder templates
        for abbrev in ["GME-AM", "GME-PM"]:
            template = MagicMock()
            template.id = uuid.uuid4()
            service._placeholder_templates[abbrev] = template

        service._absence_cache = {}

        result = service._fill_single_faculty(
            person=person,
            start_date=start_date,
            end_date=start_date + timedelta(days=1),
            schedule_run_id=None,
            created_by="test",
        )

        # Should only create 2 new assignments (day 2 slots)
        # Day 1 slots already have assignments
        assert len(result) == 2


class TestAbsenceHandling:
    """Test absence handling for faculty."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return FacultyAssignmentExpansionService(mock_db)

    def test_blocking_absence_creates_lv_assignment(self, service):
        """Blocking absence should create LV assignment."""
        person_id = uuid.uuid4()

        # Create mock absence
        absence = MagicMock()
        absence.start_date = date(2026, 1, 5)
        absence.end_date = date(2026, 1, 7)
        absence.should_block_assignment = True
        service._absence_cache[person_id] = [absence]

        assert service._is_person_absent(person_id, date(2026, 1, 6)) is True
        assert service._is_person_absent(person_id, date(2026, 1, 8)) is False

    def test_non_blocking_absence_does_not_block(self, service):
        """Non-blocking absence should not create LV assignment."""
        person_id = uuid.uuid4()

        absence = MagicMock()
        absence.start_date = date(2026, 1, 5)
        absence.end_date = date(2026, 1, 7)
        absence.should_block_assignment = False
        service._absence_cache[person_id] = [absence]

        assert service._is_person_absent(person_id, date(2026, 1, 6)) is False
