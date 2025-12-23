"""Tests for webhook API routes.

Tests the webhook management functionality including:
- Webhook CRUD operations
- Event triggering
- Delivery monitoring
- Dead letter queue management
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.routes.webhooks import get_webhook_service
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_webhook_service():
    """Create a mock webhook service."""
    service = AsyncMock()
    return service


@pytest.fixture
def client_with_mock_service(db, mock_webhook_service):
    """Create test client with mocked webhook service."""
    from app.db.session import get_db

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_webhook_service] = lambda: mock_webhook_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestWebhookRoutes:
    """Test suite for webhook API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_create_webhook_requires_auth(self, client: TestClient):
        """Test that webhook creation requires authentication."""
        response = client.post(
            "/api/webhooks",
            json={
                "url": "https://example.com/webhook",
                "name": "Test Webhook",
                "event_types": ["schedule.updated"],
            },
        )
        assert response.status_code == 401

    def test_list_webhooks_requires_auth(self, client: TestClient):
        """Test that listing webhooks requires authentication."""
        response = client.get("/api/webhooks")
        assert response.status_code == 401

    def test_get_webhook_requires_auth(self, client: TestClient):
        """Test that getting webhook requires authentication."""
        response = client.get(f"/api/webhooks/{uuid4()}")
        assert response.status_code == 401

    def test_delete_webhook_requires_auth(self, client: TestClient):
        """Test that deleting webhook requires authentication."""
        response = client.delete(f"/api/webhooks/{uuid4()}")
        assert response.status_code == 401

    # ========================================================================
    # Webhook CRUD Tests
    # ========================================================================

    def test_create_webhook_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test successful webhook creation."""
        webhook_id = uuid4()
        mock_webhook_service.create_webhook.return_value = {
            "id": str(webhook_id),
            "url": "https://example.com/webhook",
            "name": "Test Webhook",
            "event_types": ["schedule.updated"],
            "status": "active",
        }

        response = client_with_mock_service.post(
            "/api/webhooks",
            headers=auth_headers,
            json={
                "url": "https://example.com/webhook",
                "name": "Test Webhook",
                "event_types": ["schedule.updated"],
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Test Webhook"

    def test_create_webhook_with_options(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test webhook creation with all options."""
        webhook_id = uuid4()
        mock_webhook_service.create_webhook.return_value = {
            "id": str(webhook_id),
            "url": "https://example.com/webhook",
            "name": "Full Webhook",
            "event_types": ["schedule.updated", "assignment.created"],
            "status": "active",
            "description": "Test description",
            "timeout_seconds": 30,
            "max_retries": 5,
        }

        response = client_with_mock_service.post(
            "/api/webhooks",
            headers=auth_headers,
            json={
                "url": "https://example.com/webhook",
                "name": "Full Webhook",
                "event_types": ["schedule.updated", "assignment.created"],
                "description": "Test description",
                "secret": "webhook-secret-key",
                "timeout_seconds": 30,
                "max_retries": 5,
                "custom_headers": {"X-Custom": "value"},
            },
        )
        assert response.status_code == 201

    def test_list_webhooks_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test listing webhooks."""
        mock_webhook_service.list_webhooks.return_value = [
            {
                "id": str(uuid4()),
                "url": "https://example.com/webhook1",
                "name": "Webhook 1",
                "status": "active",
            },
            {
                "id": str(uuid4()),
                "url": "https://example.com/webhook2",
                "name": "Webhook 2",
                "status": "paused",
            },
        ]

        response = client_with_mock_service.get("/api/webhooks", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "webhooks" in data
        assert len(data["webhooks"]) == 2

    def test_list_webhooks_with_filter(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test listing webhooks with status filter."""
        mock_webhook_service.list_webhooks.return_value = []

        response = client_with_mock_service.get(
            "/api/webhooks?status=active&skip=0&limit=50",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_webhook_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test getting a specific webhook."""
        webhook_id = uuid4()
        mock_webhook_service.get_webhook.return_value = {
            "id": str(webhook_id),
            "url": "https://example.com/webhook",
            "name": "Test Webhook",
            "status": "active",
        }

        response = client_with_mock_service.get(
            f"/api/webhooks/{webhook_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_get_webhook_not_found(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test getting non-existent webhook."""
        mock_webhook_service.get_webhook.return_value = None

        response = client_with_mock_service.get(
            f"/api/webhooks/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_webhook_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test updating a webhook."""
        webhook_id = uuid4()
        mock_webhook_service.update_webhook.return_value = {
            "id": str(webhook_id),
            "url": "https://example.com/webhook-updated",
            "name": "Updated Webhook",
            "status": "active",
        }

        response = client_with_mock_service.put(
            f"/api/webhooks/{webhook_id}",
            headers=auth_headers,
            json={
                "name": "Updated Webhook",
                "url": "https://example.com/webhook-updated",
            },
        )
        assert response.status_code == 200

    def test_delete_webhook_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test deleting a webhook."""
        webhook_id = uuid4()
        mock_webhook_service.delete_webhook.return_value = True

        response = client_with_mock_service.delete(
            f"/api/webhooks/{webhook_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_delete_webhook_not_found(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test deleting non-existent webhook."""
        mock_webhook_service.delete_webhook.return_value = False

        response = client_with_mock_service.delete(
            f"/api/webhooks/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ========================================================================
    # Pause/Resume Tests
    # ========================================================================

    def test_pause_webhook_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test pausing a webhook."""
        webhook_id = uuid4()
        mock_webhook_service.pause_webhook.return_value = {
            "id": str(webhook_id),
            "status": "paused",
        }

        response = client_with_mock_service.post(
            f"/api/webhooks/{webhook_id}/pause",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_resume_webhook_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test resuming a webhook."""
        webhook_id = uuid4()
        mock_webhook_service.resume_webhook.return_value = {
            "id": str(webhook_id),
            "status": "active",
        }

        response = client_with_mock_service.post(
            f"/api/webhooks/{webhook_id}/resume",
            headers=auth_headers,
        )
        assert response.status_code == 200

    # ========================================================================
    # Event Trigger Tests
    # ========================================================================

    def test_trigger_event_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test triggering a webhook event."""
        mock_webhook_service.trigger_event.return_value = 3  # 3 webhooks triggered

        response = client_with_mock_service.post(
            "/api/webhooks/events/trigger",
            headers=auth_headers,
            json={
                "event_type": "schedule.updated",
                "payload": {"schedule_id": str(uuid4())},
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["webhooks_triggered"] == 3

    # ========================================================================
    # Delivery Monitoring Tests
    # ========================================================================

    def test_list_deliveries_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test listing webhook deliveries."""
        mock_webhook_service.list_deliveries.return_value = [
            {
                "id": str(uuid4()),
                "webhook_id": str(uuid4()),
                "status": "delivered",
                "response_code": 200,
            }
        ]

        response = client_with_mock_service.get(
            "/api/webhooks/deliveries", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "deliveries" in data

    def test_get_delivery_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test getting a specific delivery."""
        delivery_id = uuid4()
        mock_webhook_service.get_delivery_status.return_value = {
            "id": str(delivery_id),
            "status": "delivered",
        }

        response = client_with_mock_service.get(
            f"/api/webhooks/deliveries/{delivery_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_retry_delivery_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test retrying a failed delivery."""
        delivery_id = uuid4()
        mock_webhook_service.retry_delivery.return_value = True
        mock_webhook_service.get_delivery_status.return_value = {
            "id": str(delivery_id),
            "status": "pending",
        }

        response = client_with_mock_service.post(
            "/api/webhooks/deliveries/retry",
            headers=auth_headers,
            json={"delivery_id": str(delivery_id)},
        )
        assert response.status_code == 200

    # ========================================================================
    # Dead Letter Queue Tests
    # ========================================================================

    def test_list_dead_letters_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test listing dead letter queue."""
        mock_webhook_service.list_dead_letters.return_value = [
            {
                "id": str(uuid4()),
                "delivery_id": str(uuid4()),
                "resolved": False,
            }
        ]

        response = client_with_mock_service.get(
            "/api/webhooks/dead-letters", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "dead_letters" in data

    def test_resolve_dead_letter_success(
        self,
        client_with_mock_service: TestClient,
        mock_webhook_service: AsyncMock,
        auth_headers: dict,
    ):
        """Test resolving a dead letter."""
        dead_letter_id = uuid4()
        mock_webhook_service.resolve_dead_letter.return_value = True
        mock_webhook_service.list_dead_letters.return_value = [
            {
                "id": str(dead_letter_id),
                "resolved": True,
            }
        ]

        response = client_with_mock_service.post(
            f"/api/webhooks/dead-letters/{dead_letter_id}/resolve",
            headers=auth_headers,
            json={"notes": "Resolved manually", "retry": False},
        )
        assert response.status_code == 200
