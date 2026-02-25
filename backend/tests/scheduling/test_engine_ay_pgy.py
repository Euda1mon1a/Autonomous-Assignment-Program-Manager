"""Tests for AY-scoped PGY level wiring in the scheduling engine.

Verifies that the engine uses PersonAcademicYear records for PGY levels
instead of the legacy Person.pgy_level column.
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.scheduling.engine import SchedulingEngine


class TestGetPgyLevel:
    """Tests for SchedulingEngine._get_pgy_level()."""

    def _make_engine(self, start_date=None, pgy_by_person=None):
        """Create an engine with mocked DB, bypassing full init."""
        mock_db = MagicMock()
        # Mock PersonAcademicYear query to return empty by default
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(SchedulingEngine, "__init__", lambda self, *a, **kw: None):
            engine = SchedulingEngine.__new__(SchedulingEngine)
            engine.db = mock_db
            engine.start_date = start_date or date(2025, 9, 1)
            engine.end_date = date(2025, 9, 28)
            engine._pgy_by_person = pgy_by_person or {}
        return engine

    def test_uses_ay_record_when_present(self):
        """Should prefer AY-scoped PGY over Person.pgy_level."""
        person_id = uuid4()
        person = MagicMock()
        person.id = person_id
        person.pgy_level = 1  # Legacy says PGY-1

        # AY record says PGY-2 (advanced after rollover)
        engine = self._make_engine(pgy_by_person={person_id: 2})

        assert engine._get_pgy_level(person) == 2

    def test_falls_back_to_person_pgy_level(self):
        """Should fall back to Person.pgy_level when no AY record."""
        person = MagicMock()
        person.id = uuid4()
        person.pgy_level = 3

        engine = self._make_engine(pgy_by_person={})

        assert engine._get_pgy_level(person) == 3

    def test_falls_back_to_zero_when_no_pgy(self):
        """Should return 0 when person has no pgy_level attribute."""
        person = MagicMock(spec=[])  # No attributes
        person.id = uuid4()

        engine = self._make_engine(pgy_by_person={})

        assert engine._get_pgy_level(person) == 0

    def test_ay_none_pgy_falls_back_to_person(self):
        """When AY record exists but pgy_level is None, fall back to Person."""
        person_id = uuid4()
        person = MagicMock()
        person.id = person_id
        person.pgy_level = 2

        # AY record exists but with None pgy
        engine = self._make_engine(pgy_by_person={person_id: None})

        # None is in dict, so get() returns None -> falls through to Person
        assert engine._get_pgy_level(person) == 2


class TestEngineAYInit:
    """Tests for AY PGY lookup initialization in __init__."""

    @patch("app.scheduling.engine.SyncPreloadService")
    @patch("app.scheduling.engine.ACGMEValidator")
    @patch("app.scheduling.engine.ResilienceService")
    @patch("app.scheduling.engine.ConstraintManager")
    def test_init_builds_pgy_lookup(self, mock_cm, mock_rs, mock_av, mock_sps):
        """Engine init should query PersonAcademicYear for the block's AY."""
        mock_db = MagicMock()

        person_id = uuid4()
        mock_ay = MagicMock()
        mock_ay.person_id = person_id
        mock_ay.pgy_level = 2

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ay]
        mock_cm.create_default.return_value = MagicMock()

        engine = SchedulingEngine(
            db=mock_db,
            start_date=date(2025, 9, 1),  # AY 2025
            end_date=date(2025, 9, 28),
        )

        assert engine._pgy_by_person.get(person_id) == 2

    @patch("app.scheduling.engine.SyncPreloadService")
    @patch("app.scheduling.engine.ACGMEValidator")
    @patch("app.scheduling.engine.ResilienceService")
    @patch("app.scheduling.engine.ConstraintManager")
    def test_init_survives_missing_table(self, mock_cm, mock_rs, mock_av, mock_sps):
        """Engine init should not crash if person_academic_years table missing."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("relation does not exist")
        mock_cm.create_default.return_value = MagicMock()

        engine = SchedulingEngine(
            db=mock_db,
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 28),
        )

        assert engine._pgy_by_person == {}


class TestAcademicYearForDate:
    """Tests for get_academic_year_for_date utility."""

    def test_july_returns_same_year(self):
        from app.utils.academic_blocks import get_academic_year_for_date

        assert get_academic_year_for_date(date(2025, 7, 1)) == 2025

    def test_december_returns_same_year(self):
        from app.utils.academic_blocks import get_academic_year_for_date

        assert get_academic_year_for_date(date(2025, 12, 31)) == 2025

    def test_january_returns_previous_year(self):
        from app.utils.academic_blocks import get_academic_year_for_date

        assert get_academic_year_for_date(date(2026, 1, 15)) == 2025

    def test_june_returns_previous_year(self):
        from app.utils.academic_blocks import get_academic_year_for_date

        assert get_academic_year_for_date(date(2026, 6, 30)) == 2025
