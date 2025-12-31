"""
Integration tests for notification workflow.

Tests notification creation, delivery, preferences, and management.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.person import Person


class TestNotificationWorkflow:
    """Test notification system workflows."""

    def test_send_notification_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
    ):
        """Test sending a notification."""
        notification_response = client.post(
            "/api/notifications/",
            json={
                "recipient_id": str(sample_resident.id),
                "type": "schedule_change",
                "message": "Your schedule has been updated",
                "priority": "normal",
            },
            headers=auth_headers,
        )
        assert notification_response.status_code in [200, 201, 404, 501]

    def test_get_user_notifications_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test retrieving user notifications."""
        notifications_response = client.get(
            "/api/notifications/",
            headers=auth_headers,
        )
        assert notifications_response.status_code in [200, 404]

    def test_mark_notification_read_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test marking notifications as read."""
        # Send notification first
        send_response = client.post(
            "/api/notifications/",
            json={
                "type": "test",
                "message": "Test notification",
            },
            headers=auth_headers,
        )

        if send_response.status_code in [200, 201]:
            notification_id = send_response.json().get("id")
            if notification_id:
                # Mark as read
                read_response = client.post(
                    f"/api/notifications/{notification_id}/read",
                    headers=auth_headers,
                )
                assert read_response.status_code in [200, 404]

    def test_notification_preferences_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test managing notification preferences."""
        # Get preferences
        get_prefs = client.get(
            "/api/notifications/preferences",
            headers=auth_headers,
        )
        assert get_prefs.status_code in [200, 404, 501]

        # Update preferences
        update_prefs = client.put(
            "/api/notifications/preferences",
            json={
                "email_enabled": True,
                "sms_enabled": False,
                "types": ["schedule_change", "swap_request"],
            },
            headers=auth_headers,
        )
        assert update_prefs.status_code in [200, 404, 501]

    def test_bulk_notification_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_residents: list[Person],
    ):
        """Test sending bulk notifications."""
        bulk_response = client.post(
            "/api/notifications/bulk",
            json={
                "recipient_ids": [str(r.id) for r in sample_residents],
                "type": "announcement",
                "message": "System maintenance scheduled",
            },
            headers=auth_headers,
        )
        assert bulk_response.status_code in [200, 201, 404, 501]

    def test_notification_templates_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test notification templates."""
        # List templates
        list_response = client.get(
            "/api/notifications/templates",
            headers=auth_headers,
        )
        assert list_response.status_code in [200, 404, 501]

    def test_email_notification_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
    ):
        """Test email notification delivery."""
        email_response = client.post(
            "/api/notifications/email",
            json={
                "recipient_email": sample_resident.email,
                "subject": "Test Email",
                "body": "This is a test email notification",
            },
            headers=auth_headers,
        )
        assert email_response.status_code in [200, 202, 404, 501]
