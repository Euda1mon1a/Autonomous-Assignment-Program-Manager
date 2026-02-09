"""Tests for audience token schemas (Field bounds, field_validator, defaults)."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.audience_token import (
    AudienceTokenRequest,
    AudienceTokenResponse,
    AudienceListResponse,
    RevokeTokenRequest,
    RevokeTokenResponse,
)


class TestAudienceTokenRequest:
    def test_defaults(self):
        # Use a valid audience from the system
        r = AudienceTokenRequest(audience="jobs.abort")
        assert r.ttl_seconds == 120

    # --- ttl_seconds ge=30, le=600 ---

    def test_ttl_boundaries(self):
        r = AudienceTokenRequest(audience="jobs.abort", ttl_seconds=30)
        assert r.ttl_seconds == 30
        r = AudienceTokenRequest(audience="jobs.abort", ttl_seconds=600)
        assert r.ttl_seconds == 600

    def test_ttl_below_min(self):
        with pytest.raises(ValidationError):
            AudienceTokenRequest(audience="jobs.abort", ttl_seconds=29)

    def test_ttl_above_max(self):
        with pytest.raises(ValidationError):
            AudienceTokenRequest(audience="jobs.abort", ttl_seconds=601)

    # --- audience field_validator ---

    def test_invalid_audience(self):
        with pytest.raises(ValidationError, match="Invalid audience"):
            AudienceTokenRequest(audience="nonexistent.operation")


class TestAudienceTokenResponse:
    def test_valid(self):
        r = AudienceTokenResponse(
            token="eyJhbGciOiJIUzI1NiJ9.test",
            audience="jobs.abort",
            expires_at=datetime(2026, 3, 1, 12, 0),
            ttl_seconds=120,
        )
        assert r.audience == "jobs.abort"
        assert r.ttl_seconds == 120


class TestAudienceListResponse:
    def test_valid(self):
        r = AudienceListResponse(
            audiences={
                "jobs.abort": "Abort running background jobs",
                "schedule.generate": "Generate new schedules",
            }
        )
        assert len(r.audiences) == 2
        assert "jobs.abort" in r.audiences

    def test_empty(self):
        r = AudienceListResponse(audiences={})
        assert r.audiences == {}


class TestRevokeTokenRequest:
    def test_valid_minimal(self):
        r = RevokeTokenRequest(jti="a" * 32)
        assert r.token is None
        assert r.reason == "manual_revocation"

    def test_full(self):
        r = RevokeTokenRequest(
            jti="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            token="eyJhbGciOiJIUzI1NiJ9.test",
            reason="Suspicious activity detected",
        )
        assert r.token is not None
        assert r.reason == "Suspicious activity detected"

    # --- jti min_length=32 ---

    def test_jti_too_short(self):
        with pytest.raises(ValidationError):
            RevokeTokenRequest(jti="a" * 31)

    def test_jti_min_length(self):
        r = RevokeTokenRequest(jti="a" * 32)
        assert len(r.jti) == 32

    # --- reason max_length=255 ---

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            RevokeTokenRequest(jti="a" * 32, reason="x" * 256)

    def test_reason_max_length(self):
        r = RevokeTokenRequest(jti="a" * 32, reason="x" * 255)
        assert len(r.reason) == 255


class TestRevokeTokenResponse:
    def test_valid(self):
        r = RevokeTokenResponse(
            success=True,
            jti="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            message="Token successfully revoked",
        )
        assert r.success is True
        assert r.message == "Token successfully revoked"
