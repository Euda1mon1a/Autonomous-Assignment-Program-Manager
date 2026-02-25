"""Tests for absence → preload refresh wiring (WP-7 Track C).

Verifies that creating/updating/deleting absences triggers
leave preload refresh in sync_preload_service.
"""

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


class TestAbsenceServicePreloadRefresh:
    """Tests for AbsenceService._refresh_leave_preloads wiring."""

    def _make_service(self):
        from app.services.absence_service import AbsenceService

        mock_db = MagicMock()
        service = AbsenceService(mock_db)
        service.absence_repo = MagicMock()
        return service, mock_db

    @patch("app.services.absence_service.AbsenceService._refresh_leave_preloads")
    def test_create_absence_triggers_refresh(self, mock_refresh):
        """Creating an absence should refresh leave preloads."""
        service, mock_db = self._make_service()
        pid = uuid4()

        # Mock repo
        mock_absence = MagicMock()
        mock_absence.person_id = pid
        mock_absence.start_date = date(2026, 3, 10)
        mock_absence.end_date = date(2026, 3, 14)
        service.absence_repo.create.return_value = mock_absence

        service.create_absence(
            person_id=pid,
            start_date=date(2026, 3, 10),
            end_date=date(2026, 3, 14),
            absence_type="vacation",
        )

        mock_refresh.assert_called_once_with(pid, date(2026, 3, 10), date(2026, 3, 14))

    @patch("app.services.absence_service.AbsenceService._refresh_leave_preloads")
    def test_delete_absence_triggers_refresh(self, mock_refresh):
        """Deleting an absence should refresh leave preloads."""
        service, mock_db = self._make_service()
        pid = uuid4()
        absence_id = uuid4()

        mock_absence = MagicMock()
        mock_absence.person_id = pid
        mock_absence.start_date = date(2026, 3, 10)
        mock_absence.end_date = date(2026, 3, 14)
        service.absence_repo.get_by_id.return_value = mock_absence

        service.delete_absence(absence_id)

        mock_refresh.assert_called_once_with(pid, date(2026, 3, 10), date(2026, 3, 14))

    @patch("app.services.absence_service.AbsenceService._refresh_leave_preloads")
    def test_update_absence_triggers_refresh_with_union(self, mock_refresh):
        """Updating absence dates should refresh the union of old + new ranges."""
        service, mock_db = self._make_service()
        pid = uuid4()
        absence_id = uuid4()

        mock_absence = MagicMock()
        mock_absence.person_id = pid
        mock_absence.start_date = date(2026, 3, 10)
        mock_absence.end_date = date(2026, 3, 14)
        service.absence_repo.get_by_id.return_value = mock_absence

        # After update: dates shift later
        updated_absence = MagicMock()
        updated_absence.person_id = pid
        updated_absence.start_date = date(2026, 3, 12)
        updated_absence.end_date = date(2026, 3, 18)
        service.absence_repo.update.return_value = updated_absence
        service.absence_repo.refresh = MagicMock()

        service.update_absence(
            absence_id, {"start_date": date(2026, 3, 12), "end_date": date(2026, 3, 18)}
        )

        # Should refresh the union: min(old_start, new_start) to max(old_end, new_end)
        mock_refresh.assert_called_once_with(pid, date(2026, 3, 10), date(2026, 3, 18))

    @patch("app.services.absence_service.AbsenceService._refresh_leave_preloads")
    def test_delete_nonexistent_does_not_refresh(self, mock_refresh):
        """Deleting a missing absence should not trigger refresh."""
        service, mock_db = self._make_service()
        service.absence_repo.get_by_id.return_value = None

        result = service.delete_absence(uuid4())

        assert result["success"] is False
        mock_refresh.assert_not_called()


class TestRefreshLeavePreloadsMethod:
    """Tests for the _refresh_leave_preloads helper method."""

    def test_calls_sync_preload_service(self):
        """Should call SyncPreloadService.refresh_leave_preloads."""
        from app.services.absence_service import AbsenceService

        mock_db = MagicMock()
        service = AbsenceService(mock_db)
        pid = uuid4()

        with patch(
            "app.services.sync_preload_service.SyncPreloadService"
        ) as mock_sps_class:
            mock_sps = MagicMock()
            mock_sps_class.return_value = mock_sps

            service._refresh_leave_preloads(pid, date(2026, 3, 10), date(2026, 3, 14))

            mock_sps_class.assert_called_once_with(mock_db)
            mock_sps.refresh_leave_preloads.assert_called_once_with(
                pid, date(2026, 3, 10), date(2026, 3, 14)
            )

    def test_swallows_exception(self):
        """Should not raise if preload refresh fails."""
        from app.services.absence_service import AbsenceService

        mock_db = MagicMock()
        service = AbsenceService(mock_db)

        with patch(
            "app.services.sync_preload_service.SyncPreloadService",
            side_effect=Exception("DB error"),
        ):
            # Should not raise
            service._refresh_leave_preloads(
                uuid4(), date(2026, 3, 10), date(2026, 3, 14)
            )
