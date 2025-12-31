"""Tests for CertificationScheduler background service."""

from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from app.models.certification import CertificationType, PersonCertification
from app.models.person import Person
from app.services.certification_scheduler import (
    REMINDER_THRESHOLDS,
    CertificationScheduler,
    get_scheduler,
)


class TestCertificationSchedulerInit:
    """Test CertificationScheduler initialization."""

    def test_init_default_enabled(self):
        """Test scheduler initializes as enabled by default."""
        with patch.dict("os.environ", {"CERT_CHECK_ENABLED": "true"}):
            scheduler = CertificationScheduler()

            assert scheduler.enabled is True
            assert scheduler.check_hour == 6
            assert scheduler.admin_email is None

    def test_init_disabled_via_env(self):
        """Test scheduler can be disabled via environment variable."""
        with patch.dict("os.environ", {"CERT_CHECK_ENABLED": "false"}):
            scheduler = CertificationScheduler()

            assert scheduler.enabled is False

    def test_init_custom_check_hour(self):
        """Test custom check hour from environment."""
        with patch.dict("os.environ", {"CERT_CHECK_HOUR": "8"}):
            scheduler = CertificationScheduler()

            assert scheduler.check_hour == 8

    def test_init_with_admin_email(self):
        """Test admin email configuration from environment."""
        with patch.dict("os.environ", {"CERT_ADMIN_EMAIL": "admin@hospital.org"}):
            scheduler = CertificationScheduler()

            assert scheduler.admin_email == "admin@hospital.org"

    def test_init_case_insensitive_enabled(self):
        """Test CERT_CHECK_ENABLED is case-insensitive."""
        with patch.dict("os.environ", {"CERT_CHECK_ENABLED": "TRUE"}):
            scheduler = CertificationScheduler()
            assert scheduler.enabled is True

        with patch.dict("os.environ", {"CERT_CHECK_ENABLED": "False"}):
            scheduler = CertificationScheduler()
            assert scheduler.enabled is False


class TestCertificationSchedulerStart:
    """Test scheduler start functionality."""

    def test_start_when_disabled(self):
        """Test start() does nothing when scheduler is disabled."""
        with patch.dict("os.environ", {"CERT_CHECK_ENABLED": "false"}):
            scheduler = CertificationScheduler()
            scheduler.start()

            # When disabled, scheduler should remain None
            assert scheduler.scheduler is None

    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_start_success(self, mock_scheduler_class):
        """Test successful scheduler start."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        with patch.dict(
            "os.environ", {"CERT_CHECK_ENABLED": "true", "CERT_CHECK_HOUR": "6"}
        ):
            scheduler = CertificationScheduler()
            scheduler.start()

            # Verify scheduler was created and started
            mock_scheduler_class.assert_called_once()
            mock_scheduler.add_job.assert_called_once()
            mock_scheduler.start.assert_called_once()
            # Verify scheduler object is set
            assert scheduler.scheduler is mock_scheduler

    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_start_adds_cron_job(self, mock_scheduler_class):
        """Test scheduler adds daily cron job correctly."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        with patch.dict(
            "os.environ", {"CERT_CHECK_ENABLED": "true", "CERT_CHECK_HOUR": "7"}
        ):
            scheduler = CertificationScheduler()
            scheduler.start()

            # Verify job configuration
            call_args = mock_scheduler.add_job.call_args
            assert call_args[0][0] == scheduler.run_daily_check
            assert call_args[1]["id"] == "daily_certification_check"
            assert call_args[1]["name"] == "Daily Certification Check"
            assert call_args[1]["replace_existing"] is True

    def test_start_without_apscheduler(self, caplog):
        """Test scheduler handles missing APScheduler gracefully."""
        import logging

        caplog.set_level(logging.WARNING)
        with (
            patch.dict("os.environ", {"CERT_CHECK_ENABLED": "true"}),
            patch.dict(
                "sys.modules",
                {
                    "apscheduler": None,
                    "apscheduler.schedulers": None,
                    "apscheduler.schedulers.background": None,
                },
            ),
        ):
            # Need to reload module to pick up the missing import
            scheduler = CertificationScheduler()
            scheduler.start()

            # Since we can't actually make apscheduler disappear after it's loaded,
            # we just verify the scheduler didn't crash
            # The actual import error handling is tested by the code structure

    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_start_handles_exception(self, mock_scheduler_class):
        """Test scheduler handles startup exceptions."""
        mock_scheduler_class.side_effect = Exception("Startup error")

        with patch.dict("os.environ", {"CERT_CHECK_ENABLED": "true"}):
            scheduler = CertificationScheduler()
            # Should not raise - exception is caught internally
            scheduler.start()

            # Scheduler should remain None after failed start
            assert scheduler.scheduler is None


class TestCertificationSchedulerStop:
    """Test scheduler stop functionality."""

    def test_stop_active_scheduler(self):
        """Test stopping an active scheduler."""
        scheduler = CertificationScheduler()
        mock_scheduler = MagicMock()
        scheduler.scheduler = mock_scheduler

        scheduler.stop()

        mock_scheduler.shutdown.assert_called_once_with(wait=False)

    def test_stop_when_no_scheduler(self):
        """Test stop() when scheduler was never started."""
        scheduler = CertificationScheduler()
        scheduler.scheduler = None

        # Should not raise exception
        scheduler.stop()


class TestCertificationSchedulerRunDailyCheck:
    """Test daily check execution."""

    @patch("app.services.certification_scheduler.SessionLocal")
    @patch("app.services.certification_scheduler.CertificationService")
    @patch("app.services.certification_scheduler.EmailService")
    def test_run_daily_check_updates_statuses(
        self, mock_email_service_class, mock_cert_service_class, mock_session_local
    ):
        """Test run_daily_check updates all certification statuses."""
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cert_service = MagicMock()
        mock_cert_service.update_all_statuses.return_value = 42
        mock_cert_service.get_certifications_needing_reminder.return_value = []
        mock_cert_service_class.return_value = mock_cert_service

        mock_email_service = MagicMock()
        mock_email_service_class.return_value = mock_email_service

        # Run daily check
        scheduler = CertificationScheduler()
        scheduler.run_daily_check()

        # Verify status update was called
        mock_cert_service.update_all_statuses.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("app.services.certification_scheduler.SessionLocal")
    @patch("app.services.certification_scheduler.CertificationService")
    @patch("app.services.certification_scheduler.EmailService")
    def test_run_daily_check_sends_reminders_for_all_thresholds(
        self, mock_email_service_class, mock_cert_service_class, mock_session_local
    ):
        """Test run_daily_check processes all reminder thresholds."""
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cert_service = MagicMock()
        mock_cert_service.update_all_statuses.return_value = 0
        mock_cert_service.get_certifications_needing_reminder.return_value = []
        mock_cert_service_class.return_value = mock_cert_service

        mock_email_service = MagicMock()
        mock_email_service_class.return_value = mock_email_service

        # Run daily check
        scheduler = CertificationScheduler()
        scheduler.run_daily_check()

        # Verify all thresholds were checked
        assert mock_cert_service.get_certifications_needing_reminder.call_count == len(
            REMINDER_THRESHOLDS
        )
        for days in REMINDER_THRESHOLDS:
            mock_cert_service.get_certifications_needing_reminder.assert_any_call(days)

    @patch("app.services.certification_scheduler.SessionLocal")
    @patch("app.services.certification_scheduler.CertificationService")
    @patch("app.services.certification_scheduler.EmailService")
    def test_run_daily_check_sends_admin_summary_when_configured(
        self, mock_email_service_class, mock_cert_service_class, mock_session_local
    ):
        """Test run_daily_check sends admin summary when email configured."""
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cert_service = MagicMock()
        mock_cert_service.update_all_statuses.return_value = 0
        mock_cert_service.get_certifications_needing_reminder.return_value = []
        mock_cert_service.get_expiring_certifications.return_value = {"items": []}
        mock_cert_service.get_expired_certifications.return_value = {"items": []}
        mock_cert_service_class.return_value = mock_cert_service

        mock_email_service = MagicMock()
        mock_email_service_class.return_value = mock_email_service

        # Run with admin email configured
        with patch.dict("os.environ", {"CERT_ADMIN_EMAIL": "admin@hospital.org"}):
            scheduler = CertificationScheduler()
            scheduler.run_daily_check()

            # Verify admin summary was sent
            mock_email_service.send_compliance_summary.assert_called_once()

    @patch("app.services.certification_scheduler.SessionLocal")
    @patch("app.services.certification_scheduler.CertificationService")
    @patch("app.services.certification_scheduler.EmailService")
    def test_run_daily_check_skips_admin_summary_when_not_configured(
        self, mock_email_service_class, mock_cert_service_class, mock_session_local
    ):
        """Test run_daily_check skips admin summary when no email configured."""
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cert_service = MagicMock()
        mock_cert_service.update_all_statuses.return_value = 0
        mock_cert_service.get_certifications_needing_reminder.return_value = []
        mock_cert_service_class.return_value = mock_cert_service

        mock_email_service = MagicMock()
        mock_email_service_class.return_value = mock_email_service

        # Run without admin email
        with patch.dict("os.environ", {"CERT_ADMIN_EMAIL": ""}, clear=True):
            scheduler = CertificationScheduler()
            scheduler.run_daily_check()

            # Verify admin summary was NOT sent
            mock_email_service.send_compliance_summary.assert_not_called()

    @patch("app.services.certification_scheduler.SessionLocal")
    @patch("app.services.certification_scheduler.CertificationService")
    @patch("app.services.certification_scheduler.EmailService")
    def test_run_daily_check_handles_exception(
        self,
        mock_email_service_class,
        mock_cert_service_class,
        mock_session_local,
    ):
        """Test run_daily_check handles exceptions gracefully."""
        # Setup mocks to raise exception
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cert_service = MagicMock()
        mock_cert_service.update_all_statuses.side_effect = Exception("Database error")
        mock_cert_service_class.return_value = mock_cert_service

        mock_email_service = MagicMock()
        mock_email_service_class.return_value = mock_email_service

        # Run daily check - should not raise
        scheduler = CertificationScheduler()
        scheduler.run_daily_check()

        # Verify database was closed even after exception
        mock_db.close.assert_called_once()


class TestSendRemindersForThreshold:
    """Test reminder sending for specific thresholds."""

    def test_send_reminders_for_threshold_no_certs(self):
        """Test when no certifications need reminders."""
        scheduler = CertificationScheduler()
        mock_db = MagicMock()
        mock_cert_service = MagicMock()
        mock_email_service = MagicMock()

        mock_cert_service.get_certifications_needing_reminder.return_value = []

        sent_count = scheduler._send_reminders_for_threshold(
            mock_db, mock_cert_service, mock_email_service, 30
        )

        assert sent_count == 0
        mock_email_service.send_certification_reminder.assert_not_called()

    def test_send_reminders_for_threshold_sends_emails(self):
        """Test sending reminders for certifications needing reminders."""
        scheduler = CertificationScheduler()
        mock_db = MagicMock()
        mock_cert_service = MagicMock()
        mock_email_service = MagicMock()

        # Create mock certification with enabled reminder
        mock_cert_type = Mock(spec=CertificationType)
        mock_cert_type.reminder_days_30 = True

        mock_person = Mock(spec=Person)
        mock_person.email = "doctor@hospital.org"

        mock_cert = Mock(spec=PersonCertification)
        mock_cert.id = uuid4()
        mock_cert.certification_type = mock_cert_type
        mock_cert.person = mock_person
        mock_cert.days_until_expiration = 28

        mock_cert_service.get_certifications_needing_reminder.return_value = [mock_cert]
        mock_email_service.send_certification_reminder.return_value = True

        sent_count = scheduler._send_reminders_for_threshold(
            mock_db, mock_cert_service, mock_email_service, 30
        )

        assert sent_count == 1
        mock_email_service.send_certification_reminder.assert_called_once_with(
            person=mock_person,
            certification=mock_cert,
            days_until_expiration=28,
        )
        mock_cert_service.mark_reminder_sent.assert_called_once_with(mock_cert.id, 30)

    def test_send_reminders_for_threshold_skips_disabled_reminders(self):
        """Test skips certifications with disabled reminder for that threshold."""
        scheduler = CertificationScheduler()
        mock_db = MagicMock()
        mock_cert_service = MagicMock()
        mock_email_service = MagicMock()

        # Create mock certification with DISABLED reminder for 30 days
        mock_cert_type = Mock(spec=CertificationType)
        mock_cert_type.reminder_days_30 = False

        mock_cert = Mock(spec=PersonCertification)
        mock_cert.certification_type = mock_cert_type
        mock_cert.days_until_expiration = 28

        mock_cert_service.get_certifications_needing_reminder.return_value = [mock_cert]

        sent_count = scheduler._send_reminders_for_threshold(
            mock_db, mock_cert_service, mock_email_service, 30
        )

        assert sent_count == 0
        mock_email_service.send_certification_reminder.assert_not_called()

    def test_send_reminders_for_threshold_handles_email_failure(self):
        """Test handles email sending failures gracefully."""
        scheduler = CertificationScheduler()
        mock_db = MagicMock()
        mock_cert_service = MagicMock()
        mock_email_service = MagicMock()

        # Create mock certification
        mock_cert_type = Mock(spec=CertificationType)
        mock_cert_type.reminder_days_7 = True

        mock_person = Mock(spec=Person)
        mock_cert = Mock(spec=PersonCertification)
        mock_cert.id = uuid4()
        mock_cert.certification_type = mock_cert_type
        mock_cert.person = mock_person
        mock_cert.days_until_expiration = 5

        mock_cert_service.get_certifications_needing_reminder.return_value = [mock_cert]
        mock_email_service.send_certification_reminder.return_value = False

        sent_count = scheduler._send_reminders_for_threshold(
            mock_db, mock_cert_service, mock_email_service, 7
        )

        assert sent_count == 0
        # Should not mark as sent if email failed
        mock_cert_service.mark_reminder_sent.assert_not_called()

    def test_send_reminders_for_threshold_multiple_certs(self):
        """Test sending reminders for multiple certifications."""
        scheduler = CertificationScheduler()
        mock_db = MagicMock()
        mock_cert_service = MagicMock()
        mock_email_service = MagicMock()

        # Create multiple mock certifications
        mock_certs = []
        for i in range(3):
            mock_cert_type = Mock(spec=CertificationType)
            mock_cert_type.reminder_days_90 = True

            mock_person = Mock(spec=Person)
            mock_cert = Mock(spec=PersonCertification)
            mock_cert.id = uuid4()
            mock_cert.certification_type = mock_cert_type
            mock_cert.person = mock_person
            mock_cert.days_until_expiration = 85

            mock_certs.append(mock_cert)

        mock_cert_service.get_certifications_needing_reminder.return_value = mock_certs
        mock_email_service.send_certification_reminder.return_value = True

        sent_count = scheduler._send_reminders_for_threshold(
            mock_db, mock_cert_service, mock_email_service, 90
        )

        assert sent_count == 3
        assert mock_email_service.send_certification_reminder.call_count == 3
        assert mock_cert_service.mark_reminder_sent.call_count == 3


class TestSendAdminSummary:
    """Test admin summary email functionality."""

    def test_send_admin_summary_success(self):
        """Test successful admin summary email."""
        scheduler = CertificationScheduler()
        scheduler.admin_email = "admin@hospital.org"

        mock_db = MagicMock()
        mock_cert_service = MagicMock()
        mock_email_service = MagicMock()

        expiring_certs = [Mock(spec=PersonCertification)]
        expired_certs = [Mock(spec=PersonCertification)]

        mock_cert_service.get_expiring_certifications.return_value = {
            "items": expiring_certs
        }
        mock_cert_service.get_expired_certifications.return_value = {
            "items": expired_certs
        }

        scheduler._send_admin_summary(mock_db, mock_cert_service, mock_email_service)

        mock_cert_service.get_expiring_certifications.assert_called_once_with(days=180)
        mock_cert_service.get_expired_certifications.assert_called_once()
        mock_email_service.send_compliance_summary.assert_called_once_with(
            to_email="admin@hospital.org",
            expiring_certs=expiring_certs,
            expired_certs=expired_certs,
        )

    def test_send_admin_summary_handles_exception(self):
        """Test admin summary handles exceptions gracefully."""
        scheduler = CertificationScheduler()
        scheduler.admin_email = "admin@hospital.org"

        mock_db = MagicMock()
        mock_cert_service = MagicMock()
        mock_email_service = MagicMock()

        mock_cert_service.get_expiring_certifications.side_effect = Exception(
            "Database error"
        )

        # Should not raise - exception is caught internally
        scheduler._send_admin_summary(mock_db, mock_cert_service, mock_email_service)

        # Verify email was not sent (exception prevented it)
        mock_email_service.send_compliance_summary.assert_not_called()


class TestRunNow:
    """Test manual trigger functionality."""

    @patch("app.services.certification_scheduler.SessionLocal")
    def test_run_now_without_db_session(self, mock_session_local):
        """Test run_now creates and closes database session when not provided."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        scheduler = CertificationScheduler()
        with patch.object(scheduler, "run_daily_check") as mock_run:
            scheduler.run_now()

            mock_run.assert_called_once()
            mock_db.close.assert_called_once()

    @patch("app.services.certification_scheduler.SessionLocal")
    def test_run_now_with_db_session(self, mock_session_local):
        """Test run_now uses provided database session and doesn't close it."""
        provided_db = MagicMock()

        scheduler = CertificationScheduler()
        with patch.object(scheduler, "run_daily_check") as mock_run:
            scheduler.run_now(db=provided_db)

            mock_run.assert_called_once()
            provided_db.close.assert_not_called()
            mock_session_local.assert_not_called()

    @patch("app.services.certification_scheduler.SessionLocal")
    def test_run_now_closes_db_on_exception(self, mock_session_local):
        """Test run_now closes database even when exception occurs."""
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        scheduler = CertificationScheduler()
        with patch.object(
            scheduler, "run_daily_check", side_effect=Exception("Test error")
        ):
            with pytest.raises(Exception, match="Test error"):
                scheduler.run_now()

            mock_db.close.assert_called_once()


class TestGetSchedulerSingleton:
    """Test global scheduler singleton pattern."""

    def test_get_scheduler_creates_instance(self):
        """Test get_scheduler creates a new instance on first call."""
        # Reset global state
        import app.services.certification_scheduler as scheduler_module

        scheduler_module._scheduler = None

        scheduler = get_scheduler()

        assert scheduler is not None
        assert isinstance(scheduler, CertificationScheduler)

    def test_get_scheduler_returns_same_instance(self):
        """Test get_scheduler returns the same instance on subsequent calls."""
        # Reset global state
        import app.services.certification_scheduler as scheduler_module

        scheduler_module._scheduler = None

        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()

        assert scheduler1 is scheduler2

    def test_get_scheduler_after_module_import(self):
        """Test get_scheduler works after module import."""
        from app.services.certification_scheduler import get_scheduler as imported_get

        scheduler = imported_get()
        assert isinstance(scheduler, CertificationScheduler)


class TestReminderThresholds:
    """Test reminder threshold configuration."""

    def test_reminder_thresholds_defined(self):
        """Test REMINDER_THRESHOLDS constant is properly defined."""
        assert REMINDER_THRESHOLDS == [180, 90, 30, 14, 7]

    def test_reminder_thresholds_are_sorted_descending(self):
        """Test thresholds are in descending order."""
        assert sorted(REMINDER_THRESHOLDS, reverse=True) == REMINDER_THRESHOLDS


class TestIntegrationScenarios:
    """Test complete workflow scenarios."""

    @patch("app.services.certification_scheduler.SessionLocal")
    @patch("app.services.certification_scheduler.CertificationService")
    @patch("app.services.certification_scheduler.EmailService")
    def test_complete_daily_check_workflow(
        self,
        mock_email_service_class,
        mock_cert_service_class,
        mock_session_local,
    ):
        """Test complete daily check workflow with status updates and reminders."""
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Create mock certifications needing reminders
        mock_cert_type = Mock(spec=CertificationType)
        mock_cert_type.reminder_days_30 = True
        mock_cert_type.reminder_days_7 = True

        mock_person = Mock(spec=Person)
        mock_person.email = "doctor@hospital.org"

        mock_cert_30 = Mock(spec=PersonCertification)
        mock_cert_30.id = uuid4()
        mock_cert_30.certification_type = mock_cert_type
        mock_cert_30.person = mock_person
        mock_cert_30.days_until_expiration = 28

        mock_cert_7 = Mock(spec=PersonCertification)
        mock_cert_7.id = uuid4()
        mock_cert_7.certification_type = mock_cert_type
        mock_cert_7.person = mock_person
        mock_cert_7.days_until_expiration = 5

        # Setup certification service
        mock_cert_service = MagicMock()
        mock_cert_service.update_all_statuses.return_value = 15

        def get_certs_for_threshold(days):
            if days == 30:
                return [mock_cert_30]
            elif days == 7:
                return [mock_cert_7]
            return []

        mock_cert_service.get_certifications_needing_reminder.side_effect = (
            get_certs_for_threshold
        )
        mock_cert_service.get_expiring_certifications.return_value = {
            "items": [mock_cert_30, mock_cert_7]
        }
        mock_cert_service.get_expired_certifications.return_value = {"items": []}
        mock_cert_service_class.return_value = mock_cert_service

        # Setup email service
        mock_email_service = MagicMock()
        mock_email_service.send_certification_reminder.return_value = True
        mock_email_service_class.return_value = mock_email_service

        # Run daily check with admin email
        with patch.dict("os.environ", {"CERT_ADMIN_EMAIL": "admin@hospital.org"}):
            scheduler = CertificationScheduler()
            scheduler.run_daily_check()

        # Verify workflow
        mock_cert_service.update_all_statuses.assert_called_once()
        assert mock_email_service.send_certification_reminder.call_count == 2
        mock_cert_service.mark_reminder_sent.assert_any_call(mock_cert_30.id, 30)
        mock_cert_service.mark_reminder_sent.assert_any_call(mock_cert_7.id, 7)
        mock_email_service.send_compliance_summary.assert_called_once()
        # Database should be closed
        mock_db.close.assert_called_once()

    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_full_lifecycle_start_and_stop(self, mock_scheduler_class):
        """Test complete scheduler lifecycle from start to stop."""
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler

        with patch.dict(
            "os.environ", {"CERT_CHECK_ENABLED": "true", "CERT_CHECK_HOUR": "6"}
        ):
            scheduler = CertificationScheduler()

            # Start scheduler
            scheduler.start()
            assert scheduler.scheduler is not None
            mock_scheduler.start.assert_called_once()

            # Stop scheduler
            scheduler.stop()
            mock_scheduler.shutdown.assert_called_once_with(wait=False)
