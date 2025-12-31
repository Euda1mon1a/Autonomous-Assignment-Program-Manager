"""
Integration tests for notification service delivery.

Tests notification delivery through various channels.
"""

import pytest
from sqlalchemy.orm import Session

from app.models.person import Person


class TestNotificationIntegration:
    """Test notification service integration."""

    def test_email_notification_delivery_integration(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test email notification delivery."""
        ***REMOVED*** notification_service = NotificationService(db)
        ***REMOVED*** result = notification_service.send_email(
        ***REMOVED***     recipient_id=sample_resident.id,
        ***REMOVED***     subject="Test Email",
        ***REMOVED***     body="This is a test email",
        ***REMOVED*** )
        ***REMOVED*** assert result.sent

    def test_notification_queue_integration(
        self,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test notification queuing and processing."""
        ***REMOVED*** Queue multiple notifications
        ***REMOVED*** notification_service = NotificationService(db)
        ***REMOVED*** for resident in sample_residents:
        ***REMOVED***     notification_service.queue_notification(
        ***REMOVED***         recipient_id=resident.id,
        ***REMOVED***         type="test",
        ***REMOVED***         message="Test notification",
        ***REMOVED***     )

        ***REMOVED*** Process queue
        ***REMOVED*** result = notification_service.process_queue()
        ***REMOVED*** assert result.processed > 0

    def test_notification_template_integration(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test notification with templates."""
        ***REMOVED*** notification_service = NotificationService(db)
        ***REMOVED*** result = notification_service.send_from_template(
        ***REMOVED***     template_name="schedule_change",
        ***REMOVED***     recipient_id=sample_resident.id,
        ***REMOVED***     context={"date": "2024-01-01", "rotation": "Clinic"},
        ***REMOVED*** )
        ***REMOVED*** assert result.sent

    def test_bulk_notification_integration(
        self,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test bulk notification delivery."""
        ***REMOVED*** notification_service = NotificationService(db)
        ***REMOVED*** result = notification_service.send_bulk(
        ***REMOVED***     recipient_ids=[r.id for r in sample_residents],
        ***REMOVED***     type="announcement",
        ***REMOVED***     message="System maintenance",
        ***REMOVED*** )
        ***REMOVED*** assert result.sent == len(sample_residents)

    def test_notification_preferences_integration(
        self,
        db: Session,
        sample_resident: Person,
    ):
        """Test notification preferences filtering."""
        ***REMOVED*** Set preferences
        ***REMOVED*** prefs_service = NotificationPreferencesService(db)
        ***REMOVED*** prefs_service.update_preferences(
        ***REMOVED***     person_id=sample_resident.id,
        ***REMOVED***     email_enabled=False,
        ***REMOVED***     sms_enabled=True,
        ***REMOVED*** )

        ***REMOVED*** Send notification - should respect preferences
        ***REMOVED*** notification_service = NotificationService(db)
        ***REMOVED*** result = notification_service.send_notification(
        ***REMOVED***     recipient_id=sample_resident.id,
        ***REMOVED***     message="Test",
        ***REMOVED*** )
        ***REMOVED*** assert result.via == "sms"
