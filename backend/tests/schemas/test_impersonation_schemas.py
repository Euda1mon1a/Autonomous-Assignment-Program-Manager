"""Tests for impersonation schemas (defaults, nested models)."""

from datetime import datetime
from uuid import uuid4

from app.schemas.auth import UserResponse
from app.schemas.impersonation import (
    ImpersonateRequest,
    ImpersonateResponse,
    ImpersonationStatus,
    EndImpersonationResponse,
)


def _make_user(**overrides):
    defaults = {
        "id": uuid4(),
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
    }
    defaults.update(overrides)
    return UserResponse(**defaults)


class TestImpersonateRequest:
    def test_valid(self):
        uid = uuid4()
        r = ImpersonateRequest(target_user_id=uid)
        assert r.target_user_id == uid


class TestImpersonateResponse:
    def test_valid(self):
        user = _make_user(username="resident1", role="resident")
        r = ImpersonateResponse(
            impersonation_token="eyJhbGciOiJIUzI1N...",
            target_user=user,
            expires_at=datetime(2026, 3, 1, 12, 30),
        )
        assert r.impersonation_token.startswith("eyJ")
        assert r.target_user.username == "resident1"
        assert r.expires_at is not None


class TestImpersonationStatus:
    def test_defaults(self):
        r = ImpersonationStatus()
        assert r.is_impersonating is False
        assert r.target_user is None
        assert r.original_user is None
        assert r.expires_at is None

    def test_active(self):
        target = _make_user(username="resident1", role="resident")
        original = _make_user(username="admin", role="admin")
        r = ImpersonationStatus(
            is_impersonating=True,
            target_user=target,
            original_user=original,
            expires_at=datetime(2026, 3, 1, 13, 0),
        )
        assert r.is_impersonating is True
        assert r.target_user.username == "resident1"
        assert r.original_user.username == "admin"


class TestEndImpersonationResponse:
    def test_valid(self):
        r = EndImpersonationResponse(success=True)
        assert r.success is True
        assert r.message == "Impersonation ended successfully"

    def test_custom_message(self):
        r = EndImpersonationResponse(success=False, message="Session expired")
        assert r.success is False
        assert r.message == "Session expired"
