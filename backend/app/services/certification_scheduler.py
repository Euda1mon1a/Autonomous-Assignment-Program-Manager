"""Background scheduler for certification expiration checks and reminders.

This module provides:
- Daily certification status updates
- Automatic expiration reminder emails at configured intervals
- Compliance summary reports

Usage:
    from app.services.certification_scheduler import CertificationScheduler

    # Start scheduler on app startup
    scheduler = CertificationScheduler()
    scheduler.start()

    # Stop on shutdown
    scheduler.stop()

Configuration via environment variables:
- CERT_CHECK_ENABLED: Enable/disable scheduler (default: true)
- CERT_CHECK_HOUR: Hour to run daily check (default: 6 = 6 AM)
- CERT_ADMIN_EMAIL: Email for compliance summaries
"""

import os

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.certification_service import CertificationService
from app.services.email_service import EmailService

logger = get_logger(__name__)

# Reminder thresholds in days
REMINDER_THRESHOLDS = [180, 90, 30, 14, 7]


class CertificationScheduler:
    """Background scheduler for certification management tasks."""

    def __init__(self):
        self.scheduler = None
        self.enabled = os.getenv("CERT_CHECK_ENABLED", "true").lower() == "true"
        self.check_hour = int(os.getenv("CERT_CHECK_HOUR", "6"))
        self.admin_email = os.getenv("CERT_ADMIN_EMAIL")

    def start(self):
        """Start the background scheduler."""
        if not self.enabled:
            logger.info("Certification scheduler is disabled")
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger

            self.scheduler = BackgroundScheduler()

            # Daily certification check at configured hour
            self.scheduler.add_job(
                self.run_daily_check,
                CronTrigger(hour=self.check_hour, minute=0),
                id="daily_certification_check",
                name="Daily Certification Check",
                replace_existing=True,
            )

            self.scheduler.start()
            logger.info(
                f"Certification scheduler started. Daily check at {self.check_hour}:00"
            )

        except ImportError:
            logger.warning(
                "APScheduler not installed. Install with: pip install apscheduler. "
                "Certification reminders will not be sent automatically."
            )
        except Exception as e:
            logger.error(f"Failed to start certification scheduler: {e}")

    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            logger.info("Certification scheduler stopped")

    def run_daily_check(self):
        """
        Run the daily certification check.

        This:
        1. Updates all certification statuses
        2. Sends reminder emails for each threshold
        3. Sends compliance summary to admin
        """
        logger.info("Starting daily certification check")
        db: Session = SessionLocal()

        try:
            cert_service = CertificationService(db)
            email_service = EmailService()

            # 1. Update all certification statuses
            updated_count = cert_service.update_all_statuses()
            logger.info(f"Updated {updated_count} certification statuses")

            # 2. Send reminder emails for each threshold
            total_reminders_sent = 0
            for days in REMINDER_THRESHOLDS:
                sent = self._send_reminders_for_threshold(
                    db, cert_service, email_service, days
                )
                total_reminders_sent += sent

            logger.info(f"Sent {total_reminders_sent} reminder emails")

            # 3. Send compliance summary to admin
            if self.admin_email:
                self._send_admin_summary(db, cert_service, email_service)

            logger.info("Daily certification check completed")

        except Exception as e:
            logger.error(f"Error in daily certification check: {e}")
        finally:
            db.close()

    def _send_reminders_for_threshold(
        self,
        db: Session,
        cert_service: CertificationService,
        email_service: EmailService,
        days: int,
    ) -> int:
        """Send reminders for a specific day threshold."""
        certs_needing_reminder = cert_service.get_certifications_needing_reminder(days)
        sent_count = 0

        for cert in certs_needing_reminder:
            # Check if this cert type has this reminder enabled
            reminder_field = f"reminder_days_{days}"
            if not getattr(cert.certification_type, reminder_field, True):
                continue

            # Send email
            success = email_service.send_certification_reminder(
                person=cert.person,
                certification=cert,
                days_until_expiration=cert.days_until_expiration,
            )

            if success:
                # Mark reminder as sent
                cert_service.mark_reminder_sent(cert.id, days)
                sent_count += 1

        if sent_count > 0:
            logger.info(f"Sent {sent_count} {days}-day reminders")

        return sent_count

    def _send_admin_summary(
        self,
        db: Session,
        cert_service: CertificationService,
        email_service: EmailService,
    ):
        """Send compliance summary to administrator."""
        try:
            expiring = cert_service.get_expiring_certifications(days=180)
            expired = cert_service.get_expired_certifications()

            email_service.send_compliance_summary(
                to_email=self.admin_email,
                expiring_certs=expiring["items"],
                expired_certs=expired["items"],
            )
            logger.info(f"Sent compliance summary to {self.admin_email}")
        except Exception as e:
            logger.error(f"Failed to send admin summary: {e}")

    def run_now(self, db: Session | None = None):
        """
        Run the certification check immediately (for testing/manual trigger).

        Can be called via API or CLI.
        """
        if db is None:
            db = SessionLocal()
            close_db = True
        else:
            close_db = False

        try:
            self.run_daily_check()
        finally:
            if close_db:
                db.close()


# Global scheduler instance
_scheduler: CertificationScheduler | None = None


def get_scheduler() -> CertificationScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = CertificationScheduler()
    return _scheduler


def start_scheduler():
    """Start the certification scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the certification scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
