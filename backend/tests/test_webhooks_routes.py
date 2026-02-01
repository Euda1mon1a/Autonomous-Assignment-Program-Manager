"""Route tests for webhook API endpoints."""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.webhooks.service import WebhookService


def _webhook_dict(webhook_id: UUID) -> dict:
    now = datetime.utcnow()
    return {
        "id": webhook_id,
        "url": "https://example.com/webhook",
        "name": "Test Webhook",
        "description": None,
        "event_types": ["test.event"],
        "status": "active",
        "retry_enabled": True,
        "max_retries": 3,
        "timeout_seconds": 30,
        "custom_headers": {},
        "metadata": {},
        "owner_id": None,
        "created_at": now,
        "updated_at": now,
        "last_triggered_at": None,
    }


def _delivery_dict(delivery_id: UUID, webhook_id: UUID) -> dict:
    now = datetime.utcnow()
    return {
        "id": delivery_id,
        "webhook_id": webhook_id,
        "event_type": "test.event",
        "event_id": "evt-123",
        "payload": {"foo": "bar"},
        "status": "pending",
        "attempt_count": 0,
        "max_attempts": 3,
        "next_retry_at": None,
        "http_status_code": None,
        "response_body": None,
        "response_time_ms": None,
        "error_message": None,
        "created_at": now,
        "first_attempted_at": None,
        "last_attempted_at": None,
        "completed_at": None,
    }


def _dead_letter_dict(
    dead_letter_id: UUID, delivery_id: UUID, webhook_id: UUID
) -> dict:
    now = datetime.utcnow()
    return {
        "id": dead_letter_id,
        "delivery_id": delivery_id,
        "webhook_id": webhook_id,
        "event_type": "test.event",
        "payload": {"foo": "bar"},
        "total_attempts": 3,
        "last_error_message": "timeout",
        "last_http_status": 504,
        "resolved": False,
        "resolved_at": None,
        "resolved_by": None,
        "resolution_notes": None,
        "created_at": now,
    }


class TestWebhookRoutes:
    """Smoke tests for webhook API routes."""

    def test_create_webhook(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()

        async def fake_create_webhook(self, **_kwargs):
            return _webhook_dict(webhook_id)

        monkeypatch.setattr(WebhookService, "create_webhook", fake_create_webhook)

        payload = {
            "url": "https://example.com/webhook",
            "name": "Test Webhook",
            "event_types": ["test.event"],
            "secret": "s" * 32,
            "timeout_seconds": 30,
            "max_retries": 3,
        }

        response = client.post(
            "/api/v1/webhooks",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(webhook_id)
        assert data["name"] == "Test Webhook"

    def test_list_webhooks(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()

        async def fake_list_webhooks(self, **_kwargs):
            return [_webhook_dict(webhook_id)]

        monkeypatch.setattr(WebhookService, "list_webhooks", fake_list_webhooks)

        response = client.get("/api/v1/webhooks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["webhooks"][0]["id"] == str(webhook_id)

    def test_get_webhook(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()

        async def fake_get_webhook(self, _db, _webhook_id):
            return _webhook_dict(webhook_id)

        monkeypatch.setattr(WebhookService, "get_webhook", fake_get_webhook)

        response = client.get(f"/api/v1/webhooks/{webhook_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(webhook_id)

    def test_pause_resume_webhook(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()

        async def fake_pause(self, _db, _webhook_id):
            return _webhook_dict(webhook_id)

        async def fake_resume(self, _db, _webhook_id):
            return _webhook_dict(webhook_id)

        monkeypatch.setattr(WebhookService, "pause_webhook", fake_pause)
        monkeypatch.setattr(WebhookService, "resume_webhook", fake_resume)

        response = client.post(
            f"/api/v1/webhooks/{webhook_id}/pause", headers=auth_headers
        )
        assert response.status_code == 200

        response = client.post(
            f"/api/v1/webhooks/{webhook_id}/resume", headers=auth_headers
        )
        assert response.status_code == 200

    def test_update_webhook(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()

        async def fake_update_webhook(self, _db, _webhook_id, **_kwargs):
            return _webhook_dict(webhook_id)

        monkeypatch.setattr(WebhookService, "update_webhook", fake_update_webhook)

        payload = {"name": "Updated Webhook"}
        response = client.put(
            f"/api/v1/webhooks/{webhook_id}", json=payload, headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(webhook_id)

    def test_delete_webhook(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()

        async def fake_delete_webhook(self, _db, _webhook_id):
            return True

        monkeypatch.setattr(WebhookService, "delete_webhook", fake_delete_webhook)

        response = client.delete(f"/api/v1/webhooks/{webhook_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_trigger_event(self, client: TestClient, auth_headers, monkeypatch):
        async def fake_trigger_event(self, **_kwargs):
            return 2

        monkeypatch.setattr(WebhookService, "trigger_event", fake_trigger_event)

        payload = {"event_type": "test.event", "payload": {"foo": "bar"}}
        response = client.post(
            "/api/v1/webhooks/events/trigger",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["webhooks_triggered"] == 2

    def test_list_deliveries(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()
        delivery_id = uuid4()

        async def fake_list_deliveries(self, **_kwargs):
            return [_delivery_dict(delivery_id, webhook_id)]

        monkeypatch.setattr(WebhookService, "list_deliveries", fake_list_deliveries)

        response = client.get("/api/v1/webhooks/deliveries", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["deliveries"][0]["id"] == str(delivery_id)

    def test_retry_delivery(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()
        delivery_id = uuid4()

        async def fake_retry(self, _db, _delivery_id):
            return True

        async def fake_get_delivery(self, _db, _delivery_id):
            return _delivery_dict(delivery_id, webhook_id)

        monkeypatch.setattr(WebhookService, "retry_delivery", fake_retry)
        monkeypatch.setattr(WebhookService, "get_delivery_status", fake_get_delivery)

        payload = {"delivery_id": str(delivery_id)}
        response = client.post(
            "/api/v1/webhooks/deliveries/retry",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(delivery_id)

    def test_list_dead_letters(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()
        delivery_id = uuid4()
        dead_letter_id = uuid4()

        async def fake_list_dead_letters(self, **_kwargs):
            return [_dead_letter_dict(dead_letter_id, delivery_id, webhook_id)]

        monkeypatch.setattr(WebhookService, "list_dead_letters", fake_list_dead_letters)

        response = client.get("/api/v1/webhooks/dead-letters", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_resolve_dead_letter(self, client: TestClient, auth_headers, monkeypatch):
        webhook_id = uuid4()
        delivery_id = uuid4()
        dead_letter_id = uuid4()

        async def fake_resolve_dead_letter(self, **_kwargs):
            return True

        async def fake_list_dead_letters(self, **_kwargs):
            return [_dead_letter_dict(dead_letter_id, delivery_id, webhook_id)]

        monkeypatch.setattr(
            WebhookService, "resolve_dead_letter", fake_resolve_dead_letter
        )
        monkeypatch.setattr(WebhookService, "list_dead_letters", fake_list_dead_letters)

        payload = {"notes": "resolved", "retry": False}
        response = client.post(
            f"/api/v1/webhooks/dead-letters/{dead_letter_id}/resolve",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(dead_letter_id)
