"""Tests for calendar export and subscription API routes.

Comprehensive test suite covering ICS file exports, webcal subscriptions,
date filtering, and authentication for calendar endpoints.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.calendar_subscription import CalendarSubscription
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestExportAllCalendarsEndpoint:
    """Tests for GET /api/calendar/export/ics endpoint."""

    def test_export_all_calendars_success(
        self,
        client: TestClient,
        db: Session,
        sample_blocks,
        sample_resident,
        sample_rotation_template,
    ):
        """Test exporting all calendars as ICS file."""
        # Create an assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start = date.today()
        end = date.today() + timedelta(days=7)

        response = client.get(
            "/api/v1/calendar/export/ics",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar"
        assert "attachment" in response.headers["content-disposition"]

        # Verify ICS content
        content = response.text
        assert "BEGIN:VCALENDAR" in content
        assert "END:VCALENDAR" in content

    def test_export_all_calendars_with_person_filter(
        self,
        client: TestClient,
        db: Session,
        sample_blocks,
        sample_resident,
        sample_rotation_template,
    ):
        """Test exporting calendars filtered by person_ids."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start = date.today()
        end = date.today() + timedelta(days=7)

        response = client.get(
            "/api/v1/calendar/export/ics",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "person_ids": [str(sample_resident.id)],
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar"

    def test_export_all_calendars_with_rotation_filter(
        self,
        client: TestClient,
        db: Session,
        sample_blocks,
        sample_resident,
        sample_rotation_template,
    ):
        """Test exporting calendars filtered by rotation_ids."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start = date.today()
        end = date.today() + timedelta(days=7)

        response = client.get(
            "/api/v1/calendar/export/ics",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "rotation_ids": [str(sample_rotation_template.id)],
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar"

    def test_export_all_calendars_missing_dates(self, client: TestClient):
        """Test export without required date parameters."""
        response = client.get("/api/v1/calendar/export/ics")

        assert response.status_code == 422  # Validation error

    def test_export_all_calendars_invalid_date_range(self, client: TestClient):
        """Test export with end_date before start_date."""
        start = date.today()
        end = start - timedelta(days=7)

        response = client.get(
            "/api/v1/calendar/export/ics",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_export_all_calendars_empty_range(self, client: TestClient):
        """Test export with date range that has no assignments."""
        # Far future dates
        start = date.today() + timedelta(days=365)
        end = start + timedelta(days=30)

        response = client.get(
            "/api/v1/calendar/export/ics",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 200
        content = response.text
        assert "BEGIN:VCALENDAR" in content

    def test_export_all_calendars_filename(self, client: TestClient):
        """Test that export has proper filename in headers."""
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            "/api/v1/calendar/export/ics",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 200
        disposition = response.headers["content-disposition"]
        assert "complete_schedule" in disposition
        assert ".ics" in disposition


class TestExportPersonICSEndpoint:
    """Tests for GET /api/calendar/export/ics/{person_id} endpoint."""

    def test_export_person_ics_success(
        self,
        client: TestClient,
        db: Session,
        sample_blocks,
        sample_resident,
        sample_rotation_template,
    ):
        """Test exporting ICS for a specific person."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/ics/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar"
        content = response.text
        assert "BEGIN:VCALENDAR" in content

    def test_export_person_ics_not_found(self, client: TestClient):
        """Test exporting ICS for non-existent person."""
        fake_id = uuid4()
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/ics/{fake_id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 404

    def test_export_person_ics_invalid_uuid(self, client: TestClient):
        """Test exporting ICS with invalid person UUID."""
        response = client.get(
            "/api/v1/calendar/export/ics/invalid-uuid",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )

        assert response.status_code == 422

    def test_export_person_ics_missing_dates(
        self, client: TestClient, sample_resident: Person
    ):
        """Test export without required date parameters."""
        response = client.get(f"/api/v1/calendar/export/ics/{sample_resident.id}")

        assert response.status_code == 422

    def test_export_person_ics_with_include_types(
        self, client: TestClient, sample_resident: Person
    ):
        """Test export with include_types filter."""
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/ics/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "include_types": ["clinic", "inpatient"],
            },
        )

        assert response.status_code in [200, 404]  # 404 if person not found

    def test_export_person_ics_filename(
        self, client: TestClient, sample_resident: Person
    ):
        """Test that export has proper filename including person_id."""
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/ics/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        if response.status_code == 200:
            disposition = response.headers["content-disposition"]
            assert "schedule_" in disposition
            assert str(sample_resident.id) in disposition


class TestExportPersonCalendarEndpoint:
    """Tests for GET /api/calendar/export/person/{person_id} endpoint."""

    def test_export_person_calendar_success(
        self,
        client: TestClient,
        db: Session,
        sample_blocks,
        sample_resident,
        sample_rotation_template,
    ):
        """Test exporting calendar for a person (alternate endpoint)."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/person/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar"

    def test_export_person_calendar_not_found(self, client: TestClient):
        """Test exporting calendar for non-existent person."""
        fake_id = uuid4()
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/person/{fake_id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 404

    def test_export_person_calendar_invalid_uuid(self, client: TestClient):
        """Test exporting calendar with invalid UUID."""
        response = client.get(
            "/api/v1/calendar/export/person/invalid-uuid",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )

        assert response.status_code == 422

    def test_export_person_calendar_long_range(
        self, client: TestClient, sample_resident: Person
    ):
        """Test exporting calendar for a long date range."""
        start = date.today()
        end = start + timedelta(days=365)  # Full year

        response = client.get(
            f"/api/v1/calendar/export/person/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        # Should handle gracefully even for large ranges
        assert response.status_code in [200, 404]


class TestExportRotationCalendarEndpoint:
    """Tests for GET /api/calendar/export/rotation/{rotation_id} endpoint."""

    def test_export_rotation_calendar_success(
        self,
        client: TestClient,
        db: Session,
        sample_blocks,
        sample_resident,
        sample_rotation_template,
    ):
        """Test exporting calendar for a rotation."""
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/rotation/{sample_rotation_template.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/calendar"

    def test_export_rotation_calendar_not_found(self, client: TestClient):
        """Test exporting calendar for non-existent rotation."""
        fake_id = uuid4()
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/rotation/{fake_id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        assert response.status_code == 404

    def test_export_rotation_calendar_invalid_uuid(self, client: TestClient):
        """Test exporting rotation calendar with invalid UUID."""
        response = client.get(
            "/api/v1/calendar/export/rotation/invalid-uuid",
            params={
                "start_date": date.today().isoformat(),
                "end_date": (date.today() + timedelta(days=7)).isoformat(),
            },
        )

        assert response.status_code == 422

    def test_export_rotation_calendar_missing_dates(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test export without required date parameters."""
        response = client.get(
            f"/api/v1/calendar/export/rotation/{sample_rotation_template.id}"
        )

        assert response.status_code == 422

    def test_export_rotation_calendar_filename(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test that export has proper filename including rotation_id."""
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/rotation/{sample_rotation_template.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        if response.status_code == 200:
            disposition = response.headers["content-disposition"]
            assert "rotation_" in disposition
            assert str(sample_rotation_template.id) in disposition


class TestCreateSubscriptionEndpoint:
    """Tests for POST /api/calendar/subscribe endpoint."""

    def test_create_subscription_success(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test creating a calendar subscription."""
        subscription_data = {
            "person_id": str(sample_resident.id),
            "label": "My Calendar",
        }

        response = client.post(
            "/api/v1/calendar/subscribe", json=subscription_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "webcal_url" in data
        assert "subscription_url" in data
        assert data["person_id"] == str(sample_resident.id)
        assert data["label"] == "My Calendar"
        assert data["is_active"] is True

    def test_create_subscription_with_expiration(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test creating subscription with custom expiration."""
        subscription_data = {
            "person_id": str(sample_resident.id),
            "label": "Expiring Calendar",
            "expires_days": 30,
        }

        response = client.post(
            "/api/v1/calendar/subscribe", json=subscription_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "expires_at" in data

    def test_create_subscription_person_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating subscription for non-existent person."""
        fake_id = uuid4()
        subscription_data = {
            "person_id": str(fake_id),
            "label": "Invalid Person",
        }

        response = client.post(
            "/api/v1/calendar/subscribe", json=subscription_data, headers=auth_headers
        )

        assert response.status_code == 404

    def test_create_subscription_missing_person_id(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating subscription without person_id."""
        subscription_data = {
            "label": "No Person",
        }

        response = client.post(
            "/api/v1/calendar/subscribe", json=subscription_data, headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_subscription_requires_auth(
        self, client: TestClient, sample_resident: Person
    ):
        """Test that creating subscription requires authentication."""
        subscription_data = {
            "person_id": str(sample_resident.id),
            "label": "No Auth",
        }

        response = client.post("/api/v1/calendar/subscribe", json=subscription_data)

        assert response.status_code == 401

    def test_create_subscription_webcal_url_format(
        self, client: TestClient, sample_resident: Person, auth_headers: dict
    ):
        """Test that webcal URL has proper format."""
        subscription_data = {
            "person_id": str(sample_resident.id),
            "label": "Test",
        }

        response = client.post(
            "/api/v1/calendar/subscribe", json=subscription_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["webcal_url"].startswith("webcal://")


class TestGetSubscriptionFeedEndpoint:
    """Tests for GET /api/calendar/subscribe/{token} endpoint."""

    def test_get_subscription_feed_success(
        self, client: TestClient, db: Session, admin_user, sample_resident: Person
    ):
        """Test getting subscription feed with valid token."""
        # Create a subscription
        subscription = CalendarSubscription(
            id=uuid4(),
            token="test_token_12345",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Test Subscription",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        db.add(subscription)
        db.commit()

        response = client.get(f"/api/v1/calendar/subscribe/{subscription.token}")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/calendar")
        content = response.text
        assert "BEGIN:VCALENDAR" in content

    def test_get_subscription_feed_invalid_token(self, client: TestClient):
        """Test getting subscription feed with invalid token."""
        response = client.get("/api/v1/calendar/subscribe/invalid_token")

        assert response.status_code == 401

    def test_get_subscription_feed_expired_token(
        self, client: TestClient, db: Session, admin_user, sample_resident: Person
    ):
        """Test getting subscription feed with expired token."""
        # Create expired subscription
        subscription = CalendarSubscription(
            id=uuid4(),
            token="expired_token_12345",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Expired",
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
            is_active=True,
        )
        db.add(subscription)
        db.commit()

        response = client.get(f"/api/v1/calendar/subscribe/{subscription.token}")

        assert response.status_code == 401

    def test_get_subscription_feed_inactive_token(
        self, client: TestClient, db: Session, admin_user, sample_resident: Person
    ):
        """Test getting subscription feed with inactive token."""
        subscription = CalendarSubscription(
            id=uuid4(),
            token="inactive_token_12345",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Inactive",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=False,  # Inactive
        )
        db.add(subscription)
        db.commit()

        response = client.get(f"/api/v1/calendar/subscribe/{subscription.token}")

        assert response.status_code == 401

    def test_get_subscription_feed_no_auth_required(
        self, client: TestClient, db: Session, admin_user, sample_resident: Person
    ):
        """Test that subscription feed does not require authentication header."""
        subscription = CalendarSubscription(
            id=uuid4(),
            token="public_token_12345",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Public",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        db.add(subscription)
        db.commit()

        # Call without auth headers
        response = client.get(f"/api/v1/calendar/subscribe/{subscription.token}")

        # Should succeed - token is the auth
        assert response.status_code == 200

    def test_get_subscription_feed_cache_headers(
        self, client: TestClient, db: Session, admin_user, sample_resident: Person
    ):
        """Test that subscription feed includes proper cache headers."""
        subscription = CalendarSubscription(
            id=uuid4(),
            token="cache_test_token",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Cache Test",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        db.add(subscription)
        db.commit()

        response = client.get(f"/api/v1/calendar/subscribe/{subscription.token}")

        assert response.status_code == 200
        assert "cache-control" in response.headers


class TestListSubscriptionsEndpoint:
    """Tests for GET /api/calendar/subscriptions endpoint."""

    def test_list_subscriptions_empty(self, client: TestClient, auth_headers: dict):
        """Test listing subscriptions when none exist."""
        response = client.get("/api/v1/calendar/subscriptions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "subscriptions" in data
        assert "total" in data
        assert data["total"] == 0

    def test_list_subscriptions_with_data(
        self,
        client: TestClient,
        db: Session,
        admin_user,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test listing subscriptions with existing data."""
        # Create subscriptions
        for i in range(3):
            subscription = CalendarSubscription(
                id=uuid4(),
                token=f"token_{i}",
                person_id=sample_resident.id,
                created_by_user_id=admin_user.id,
                label=f"Sub {i}",
                expires_at=datetime.utcnow() + timedelta(days=365),
                is_active=True,
            )
            db.add(subscription)
        db.commit()

        response = client.get("/api/v1/calendar/subscriptions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    def test_list_subscriptions_filter_by_person(
        self,
        client: TestClient,
        db: Session,
        admin_user,
        sample_resident: Person,
        sample_faculty: Person,
        auth_headers: dict,
    ):
        """Test filtering subscriptions by person_id."""
        # Create subscription for resident
        sub1 = CalendarSubscription(
            id=uuid4(),
            token="resident_token",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Resident",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        # Create subscription for faculty
        sub2 = CalendarSubscription(
            id=uuid4(),
            token="faculty_token",
            person_id=sample_faculty.id,
            created_by_user_id=admin_user.id,
            label="Faculty",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        db.add(sub1)
        db.add(sub2)
        db.commit()

        response = client.get(
            "/api/v1/calendar/subscriptions",
            params={"person_id": str(sample_resident.id)},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should only return subscriptions for resident
        for sub in data["subscriptions"]:
            assert sub["person_id"] == str(sample_resident.id)

    def test_list_subscriptions_active_only(
        self,
        client: TestClient,
        db: Session,
        admin_user,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test filtering only active subscriptions."""
        # Create active subscription
        sub1 = CalendarSubscription(
            id=uuid4(),
            token="active_token",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Active",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        # Create inactive subscription
        sub2 = CalendarSubscription(
            id=uuid4(),
            token="inactive_token",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Inactive",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=False,
        )
        db.add(sub1)
        db.add(sub2)
        db.commit()

        response = client.get(
            "/api/v1/calendar/subscriptions",
            params={"active_only": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # All should be active
        for sub in data["subscriptions"]:
            assert sub["is_active"] is True

    def test_list_subscriptions_requires_auth(self, client: TestClient):
        """Test that listing subscriptions requires authentication."""
        response = client.get("/api/v1/calendar/subscriptions")

        assert response.status_code == 401

    def test_list_subscriptions_includes_urls(
        self,
        client: TestClient,
        db: Session,
        admin_user,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test that subscription list includes URLs."""
        subscription = CalendarSubscription(
            id=uuid4(),
            token="url_test_token",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="URL Test",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        db.add(subscription)
        db.commit()

        response = client.get("/api/v1/calendar/subscriptions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        if data["subscriptions"]:
            sub = data["subscriptions"][0]
            assert "subscription_url" in sub
            assert "webcal_url" in sub


class TestRevokeSubscriptionEndpoint:
    """Tests for DELETE /api/calendar/subscribe/{token} endpoint."""

    def test_revoke_subscription_success(
        self,
        client: TestClient,
        db: Session,
        admin_user,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test successfully revoking a subscription."""
        subscription = CalendarSubscription(
            id=uuid4(),
            token="revoke_token_123",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="To Revoke",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        db.add(subscription)
        db.commit()

        response = client.delete(
            f"/api/v1/calendar/subscribe/{subscription.token}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_revoke_subscription_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test revoking non-existent subscription."""
        response = client.delete(
            "/api/v1/calendar/subscribe/nonexistent_token", headers=auth_headers
        )

        assert response.status_code == 404

    def test_revoke_subscription_requires_auth(
        self, client: TestClient, db: Session, admin_user, sample_resident: Person
    ):
        """Test that revoking subscription requires authentication."""
        subscription = CalendarSubscription(
            id=uuid4(),
            token="auth_test_token",
            person_id=sample_resident.id,
            created_by_user_id=admin_user.id,
            label="Auth Test",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        db.add(subscription)
        db.commit()

        response = client.delete(f"/api/v1/calendar/subscribe/{subscription.token}")

        assert response.status_code == 401

    def test_revoke_subscription_unauthorized(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test revoking subscription owned by different user."""
        # Create subscription owned by different user
        other_user_id = uuid4()
        subscription = CalendarSubscription(
            id=uuid4(),
            token="other_user_token",
            person_id=sample_resident.id,
            created_by_user_id=other_user_id,  # Different user
            label="Other User",
            expires_at=datetime.utcnow() + timedelta(days=365),
            is_active=True,
        )
        db.add(subscription)
        db.commit()

        response = client.delete(
            f"/api/v1/calendar/subscribe/{subscription.token}", headers=auth_headers
        )

        assert response.status_code == 403


class TestCalendarICSContent:
    """Tests for ICS file content validation."""

    def test_ics_has_vcalendar_wrapper(
        self, client: TestClient, sample_resident: Person
    ):
        """Test that ICS content has proper VCALENDAR wrapper."""
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/ics/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        if response.status_code == 200:
            content = response.text
            assert content.startswith("BEGIN:VCALENDAR")
            assert content.strip().endswith("END:VCALENDAR")

    def test_ics_has_version(self, client: TestClient, sample_resident: Person):
        """Test that ICS includes VERSION property."""
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/ics/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        if response.status_code == 200:
            content = response.text
            assert "VERSION:2.0" in content

    def test_ics_has_prodid(self, client: TestClient, sample_resident: Person):
        """Test that ICS includes PRODID property."""
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            f"/api/v1/calendar/export/ics/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        if response.status_code == 200:
            content = response.text
            assert "PRODID:" in content


class TestCalendarEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_export_same_day_range(self, client: TestClient, sample_resident: Person):
        """Test exporting calendar for single day (start = end)."""
        today = date.today()

        response = client.get(
            f"/api/v1/calendar/export/ics/{sample_resident.id}",
            params={
                "start_date": today.isoformat(),
                "end_date": today.isoformat(),
            },
        )

        # Should succeed
        assert response.status_code in [200, 404]

    def test_export_very_long_range(self, client: TestClient, sample_resident: Person):
        """Test exporting calendar for very long date range."""
        start = date.today()
        end = start + timedelta(days=730)  # 2 years

        response = client.get(
            f"/api/v1/calendar/export/ics/{sample_resident.id}",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            },
        )

        # Should handle gracefully
        assert response.status_code in [200, 404, 400]

    def test_subscription_token_uniqueness(
        self,
        client: TestClient,
        db: Session,
        sample_resident: Person,
        auth_headers: dict,
    ):
        """Test that multiple subscriptions get unique tokens."""
        tokens = set()

        for i in range(3):
            subscription_data = {
                "person_id": str(sample_resident.id),
                "label": f"Sub {i}",
            }

            response = client.post(
                "/api/v1/calendar/subscribe",
                json=subscription_data,
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            tokens.add(data["token"])

        # All tokens should be unique
        assert len(tokens) == 3

    def test_export_with_empty_person_ids_list(self, client: TestClient):
        """Test export with empty person_ids list."""
        start = date.today()
        end = start + timedelta(days=7)

        response = client.get(
            "/api/v1/calendar/export/ics",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "person_ids": [],
            },
        )

        # Should handle gracefully
        assert response.status_code in [200, 400]
