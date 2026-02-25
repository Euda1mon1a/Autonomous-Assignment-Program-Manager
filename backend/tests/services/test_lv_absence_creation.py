"""Tests for LV code → Absence record creation (WP-6 Track C).

Verifies that importing LV activity codes auto-creates Absence records
to close the import audit gap.
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.half_day_import_service import HalfDayImportService


class TestDatesToRanges:
    """Tests for the _dates_to_ranges static method."""

    def test_empty(self):
        assert HalfDayImportService._dates_to_ranges([]) == []

    def test_single_date(self):
        d = date(2026, 1, 5)
        assert HalfDayImportService._dates_to_ranges([d]) == [(d, d)]

    def test_consecutive_dates(self):
        dates = [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7)]
        result = HalfDayImportService._dates_to_ranges(dates)
        assert result == [(date(2026, 1, 5), date(2026, 1, 7))]

    def test_gap_splits_ranges(self):
        dates = [
            date(2026, 1, 5),
            date(2026, 1, 6),
            # gap
            date(2026, 1, 10),
            date(2026, 1, 11),
        ]
        result = HalfDayImportService._dates_to_ranges(dates)
        assert result == [
            (date(2026, 1, 5), date(2026, 1, 6)),
            (date(2026, 1, 10), date(2026, 1, 11)),
        ]

    def test_three_isolated_dates(self):
        dates = [date(2026, 1, 5), date(2026, 1, 8), date(2026, 1, 12)]
        result = HalfDayImportService._dates_to_ranges(dates)
        assert len(result) == 3
        assert all(s == e for s, e in result)


class TestCreateAbsencesFromLV:
    """Tests for create_absences_from_lv_assignments."""

    def _make_service(self):
        mock_db = MagicMock()
        # Default: no existing absences
        mock_db.query.return_value.filter.return_value.first.return_value = None
        return HalfDayImportService(mock_db), mock_db

    def _make_staged(self, person_id, assignment_date, rotation_name):
        sa = MagicMock()
        sa.matched_person_id = person_id
        sa.assignment_date = assignment_date
        sa.rotation_name = rotation_name
        return sa

    def test_creates_absence_from_lv_codes(self):
        """LV-AM/LV-PM codes should create an Absence record."""
        service, mock_db = self._make_service()
        pid = uuid4()
        batch_id = uuid4()

        staged = [
            self._make_staged(pid, date(2026, 3, 10), "LV-AM"),
            self._make_staged(pid, date(2026, 3, 10), "LV-PM"),
            self._make_staged(pid, date(2026, 3, 11), "LV-AM"),
            self._make_staged(pid, date(2026, 3, 11), "LV-PM"),
        ]

        count = service.create_absences_from_lv_assignments(staged, batch_id)

        assert count == 1
        mock_db.add.assert_called_once()
        absence = mock_db.add.call_args[0][0]
        assert absence.start_date == date(2026, 3, 10)
        assert absence.end_date == date(2026, 3, 11)
        assert absence.absence_type == "vacation"
        assert absence.person_id == pid

    def test_contiguous_dates_become_one_range(self):
        """3 consecutive LV days → 1 Absence (not 3)."""
        service, mock_db = self._make_service()
        pid = uuid4()
        batch_id = uuid4()

        staged = [
            self._make_staged(pid, date(2026, 3, 10), "LV-AM"),
            self._make_staged(pid, date(2026, 3, 11), "LV-AM"),
            self._make_staged(pid, date(2026, 3, 12), "LV-AM"),
        ]

        count = service.create_absences_from_lv_assignments(staged, batch_id)

        assert count == 1

    def test_gap_creates_two_absences(self):
        """Non-contiguous LV days → separate Absence records."""
        service, mock_db = self._make_service()
        pid = uuid4()
        batch_id = uuid4()

        staged = [
            self._make_staged(pid, date(2026, 3, 10), "LV-AM"),
            # gap
            self._make_staged(pid, date(2026, 3, 14), "LV-AM"),
        ]

        count = service.create_absences_from_lv_assignments(staged, batch_id)

        assert count == 2

    def test_skips_existing_overlapping_absence(self):
        """Should not create duplicate Absence if one already overlaps."""
        service, mock_db = self._make_service()
        # Simulate existing absence found
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

        pid = uuid4()
        batch_id = uuid4()

        staged = [
            self._make_staged(pid, date(2026, 3, 10), "LV-AM"),
        ]

        count = service.create_absences_from_lv_assignments(staged, batch_id)

        assert count == 0
        mock_db.add.assert_not_called()

    def test_ignores_non_lv_codes(self):
        """Non-LV activity codes should not create absences."""
        service, mock_db = self._make_service()
        pid = uuid4()
        batch_id = uuid4()

        staged = [
            self._make_staged(pid, date(2026, 3, 10), "CLI"),
            self._make_staged(pid, date(2026, 3, 10), "OR"),
            self._make_staged(pid, date(2026, 3, 10), "OFF"),
        ]

        count = service.create_absences_from_lv_assignments(staged, batch_id)

        assert count == 0

    def test_ignores_unmatched_persons(self):
        """Staged rows without matched_person_id should be skipped."""
        service, mock_db = self._make_service()
        batch_id = uuid4()

        sa = MagicMock()
        sa.matched_person_id = None
        sa.rotation_name = "LV-AM"
        sa.assignment_date = date(2026, 3, 10)

        count = service.create_absences_from_lv_assignments([sa], batch_id)

        assert count == 0

    def test_multiple_people(self):
        """LV codes for different people create separate absences."""
        service, mock_db = self._make_service()
        pid1 = uuid4()
        pid2 = uuid4()
        batch_id = uuid4()

        staged = [
            self._make_staged(pid1, date(2026, 3, 10), "LV-AM"),
            self._make_staged(pid2, date(2026, 3, 10), "LV-AM"),
        ]

        count = service.create_absences_from_lv_assignments(staged, batch_id)

        assert count == 2
