"""Tests for gateway authentication schemas (Pydantic validation)."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.gateway_auth import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyUpdate,
    APIKeyRotateRequest,
    APIKeyRevokeRequest,
    OAuth2ClientCreate,
    OAuth2ClientResponse,
    OAuth2ClientUpdate,
    OAuth2TokenRequest,
    OAuth2TokenResponse,
    IPWhitelistCreate,
    IPWhitelistResponse,
    IPBlacklistCreate,
    IPBlacklistResponse,
    RequestSignatureVerifyRequest,
    GatewayAuthValidationRequest,
    GatewayAuthValidationResponse,
    APIKeyListResponse,
    OAuth2ClientListResponse,
    IPWhitelistListResponse,
    IPBlacklistListResponse,
)


# ===========================================================================
# APIKeyCreate Tests
# ===========================================================================


class TestAPIKeyCreate:
    def test_valid_minimal(self):
        r = APIKeyCreate(name="test-key")
        assert r.scopes is None
        assert r.allowed_ips is None
        assert r.rate_limit_per_minute == 100
        assert r.rate_limit_per_hour == 5000
        assert r.expires_at is None

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="x" * 256)

    def test_name_max_length(self):
        r = APIKeyCreate(name="x" * 255)
        assert len(r.name) == 255

    def test_rate_limit_per_minute_boundaries(self):
        r = APIKeyCreate(name="test", rate_limit_per_minute=1)
        assert r.rate_limit_per_minute == 1
        r = APIKeyCreate(name="test", rate_limit_per_minute=10000)
        assert r.rate_limit_per_minute == 10000

    def test_rate_limit_per_minute_zero(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="test", rate_limit_per_minute=0)

    def test_rate_limit_per_minute_above_max(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="test", rate_limit_per_minute=10001)

    def test_rate_limit_per_hour_boundaries(self):
        r = APIKeyCreate(name="test", rate_limit_per_hour=1)
        assert r.rate_limit_per_hour == 1
        r = APIKeyCreate(name="test", rate_limit_per_hour=100000)
        assert r.rate_limit_per_hour == 100000

    def test_rate_limit_per_hour_above_max(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="test", rate_limit_per_hour=100001)

    def test_valid_scopes(self):
        r = APIKeyCreate(name="test", scopes="read,write,admin")
        assert r.scopes == "read,write,admin"

    def test_scopes_empty_values(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="test", scopes="read,,write")

    def test_valid_ips(self):
        r = APIKeyCreate(name="test", allowed_ips="192.168.1.1,10.0.0.0/8")
        assert r.allowed_ips == "192.168.1.1,10.0.0.0/8"

    def test_ips_empty_values(self):
        with pytest.raises(ValidationError):
            APIKeyCreate(name="test", allowed_ips="192.168.1.1,,10.0.0.1")


# ===========================================================================
# APIKeyUpdate Tests
# ===========================================================================


class TestAPIKeyUpdate:
    def test_all_none(self):
        r = APIKeyUpdate()
        assert r.name is None
        assert r.scopes is None
        assert r.is_active is None

    def test_name_min_length(self):
        r = APIKeyUpdate(name="a")
        assert r.name == "a"

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            APIKeyUpdate(name="")

    def test_rate_limit_boundaries(self):
        r = APIKeyUpdate(rate_limit_per_minute=1, rate_limit_per_hour=1)
        assert r.rate_limit_per_minute == 1

        with pytest.raises(ValidationError):
            APIKeyUpdate(rate_limit_per_minute=0)


# ===========================================================================
# APIKeyRotateRequest Tests
# ===========================================================================


class TestAPIKeyRotateRequest:
    def test_defaults(self):
        r = APIKeyRotateRequest()
        assert r.name is None
        assert r.grace_period_hours == 24

    def test_grace_period_boundaries(self):
        r = APIKeyRotateRequest(grace_period_hours=0)
        assert r.grace_period_hours == 0
        r = APIKeyRotateRequest(grace_period_hours=168)
        assert r.grace_period_hours == 168

    def test_grace_period_negative(self):
        with pytest.raises(ValidationError):
            APIKeyRotateRequest(grace_period_hours=-1)

    def test_grace_period_above_max(self):
        with pytest.raises(ValidationError):
            APIKeyRotateRequest(grace_period_hours=169)


# ===========================================================================
# APIKeyRevokeRequest Tests
# ===========================================================================


class TestAPIKeyRevokeRequest:
    def test_valid(self):
        r = APIKeyRevokeRequest(reason="Key compromised")
        assert r.reason == "Key compromised"

    def test_reason_empty(self):
        with pytest.raises(ValidationError):
            APIKeyRevokeRequest(reason="")

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            APIKeyRevokeRequest(reason="x" * 501)


# ===========================================================================
# OAuth2ClientCreate Tests
# ===========================================================================


class TestOAuth2ClientCreate:
    def test_valid(self):
        r = OAuth2ClientCreate(name="Test Client")
        assert r.scopes == "read"
        assert r.grant_types == "client_credentials"
        assert r.is_confidential is True
        assert r.rate_limit_per_minute == 100
        assert r.rate_limit_per_hour == 5000
        assert r.access_token_lifetime_seconds == 3600

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            OAuth2ClientCreate(name="")

    def test_access_token_lifetime_boundaries(self):
        r = OAuth2ClientCreate(name="test", access_token_lifetime_seconds=300)
        assert r.access_token_lifetime_seconds == 300
        r = OAuth2ClientCreate(name="test", access_token_lifetime_seconds=86400)
        assert r.access_token_lifetime_seconds == 86400

    def test_access_token_lifetime_below_min(self):
        with pytest.raises(ValidationError):
            OAuth2ClientCreate(name="test", access_token_lifetime_seconds=299)

    def test_access_token_lifetime_above_max(self):
        with pytest.raises(ValidationError):
            OAuth2ClientCreate(name="test", access_token_lifetime_seconds=86401)


# ===========================================================================
# OAuth2TokenRequest Tests
# ===========================================================================


class TestOAuth2TokenRequest:
    def test_valid(self):
        r = OAuth2TokenRequest(
            grant_type="client_credentials",
            client_id="test_client",
            client_secret="test_secret",
        )
        assert r.scope is None

    def test_grant_type_invalid(self):
        with pytest.raises(ValidationError):
            OAuth2TokenRequest(
                grant_type="authorization_code",
                client_id="test",
                client_secret="test",
            )

    def test_client_id_empty(self):
        with pytest.raises(ValidationError):
            OAuth2TokenRequest(
                grant_type="client_credentials",
                client_id="",
                client_secret="test",
            )

    def test_client_secret_empty(self):
        with pytest.raises(ValidationError):
            OAuth2TokenRequest(
                grant_type="client_credentials",
                client_id="test",
                client_secret="",
            )


# ===========================================================================
# OAuth2TokenResponse Tests
# ===========================================================================


class TestOAuth2TokenResponse:
    def test_defaults(self):
        r = OAuth2TokenResponse(access_token="abc123", expires_in=3600)
        assert r.token_type == "Bearer"
        assert r.scope is None


# ===========================================================================
# IPWhitelistCreate Tests
# ===========================================================================


class TestIPWhitelistCreate:
    def test_valid(self):
        r = IPWhitelistCreate(ip_address="192.168.1.1")
        assert r.description is None
        assert r.applies_to == "all"
        assert r.expires_at is None

    def test_ip_too_short(self):
        with pytest.raises(ValidationError):
            IPWhitelistCreate(ip_address="1.1.1")

    def test_ip_too_long(self):
        with pytest.raises(ValidationError):
            IPWhitelistCreate(ip_address="x" * 46)

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            IPWhitelistCreate(ip_address="192.168.1.1", description="x" * 501)

    def test_valid_applies_to_values(self):
        for val in ["all", "api_keys", "oauth2", "gateway"]:
            r = IPWhitelistCreate(ip_address="192.168.1.1", applies_to=val)
            assert r.applies_to == val

    def test_invalid_applies_to(self):
        with pytest.raises(ValidationError):
            IPWhitelistCreate(ip_address="192.168.1.1", applies_to="invalid")


# ===========================================================================
# IPBlacklistCreate Tests
# ===========================================================================


class TestIPBlacklistCreate:
    def test_valid(self):
        r = IPBlacklistCreate(
            ip_address="10.0.0.1",
            reason="Brute force attack detected",
        )
        assert r.detection_method == "manual"
        assert r.expires_at is None

    def test_ip_too_short(self):
        with pytest.raises(ValidationError):
            IPBlacklistCreate(ip_address="1.1", reason="test")

    def test_reason_empty(self):
        with pytest.raises(ValidationError):
            IPBlacklistCreate(ip_address="10.0.0.1", reason="")

    def test_reason_too_long(self):
        with pytest.raises(ValidationError):
            IPBlacklistCreate(ip_address="10.0.0.1", reason="x" * 501)

    def test_valid_detection_methods(self):
        for method in [
            "manual",
            "rate_limit",
            "brute_force",
            "suspicious_activity",
            "automated",
        ]:
            r = IPBlacklistCreate(
                ip_address="10.0.0.1",
                reason="Test reason",
                detection_method=method,
            )
            assert r.detection_method == method

    def test_invalid_detection_method(self):
        with pytest.raises(ValidationError):
            IPBlacklistCreate(
                ip_address="10.0.0.1",
                reason="Test reason",
                detection_method="magic",
            )

    def test_detection_method_none(self):
        r = IPBlacklistCreate(
            ip_address="10.0.0.1",
            reason="Test reason",
            detection_method=None,
        )
        assert r.detection_method is None


# ===========================================================================
# RequestSignatureVerifyRequest Tests
# ===========================================================================


class TestRequestSignatureVerifyRequest:
    def test_valid(self):
        r = RequestSignatureVerifyRequest(
            signature="sha256=abc123",
            timestamp="2026-01-15T10:30:00",
            method="POST",
            path="/api/v1/schedules",
        )
        assert r.body is None

    def test_valid_methods(self):
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]:
            r = RequestSignatureVerifyRequest(
                signature="test",
                timestamp="2026-01-01",
                method=method,
                path="/test",
            )
            assert r.method == method

    def test_invalid_method(self):
        with pytest.raises(ValidationError):
            RequestSignatureVerifyRequest(
                signature="test",
                timestamp="2026-01-01",
                method="TRACE",
                path="/test",
            )

    def test_path_empty(self):
        with pytest.raises(ValidationError):
            RequestSignatureVerifyRequest(
                signature="test",
                timestamp="2026-01-01",
                method="GET",
                path="",
            )

    def test_path_too_long(self):
        with pytest.raises(ValidationError):
            RequestSignatureVerifyRequest(
                signature="test",
                timestamp="2026-01-01",
                method="GET",
                path="/" + "x" * 2000,
            )


# ===========================================================================
# GatewayAuthValidationRequest Tests
# ===========================================================================


class TestGatewayAuthValidationRequest:
    def test_minimal(self):
        r = GatewayAuthValidationRequest(ip_address="192.168.1.1")
        assert r.api_key is None
        assert r.jwt_token is None
        assert r.client_id is None


# ===========================================================================
# GatewayAuthValidationResponse Tests
# ===========================================================================


class TestGatewayAuthValidationResponse:
    def test_valid_success(self):
        r = GatewayAuthValidationResponse(
            is_valid=True,
            auth_type="api_key",
            user_id=uuid4(),
            scopes=["read", "write"],
            rate_limit_remaining=99,
        )
        assert r.is_valid is True

    def test_valid_failure(self):
        r = GatewayAuthValidationResponse(
            is_valid=False,
            error_message="Invalid API key",
        )
        assert r.scopes == []


# ===========================================================================
# List Response Tests
# ===========================================================================


class TestListResponses:
    def test_api_key_list(self):
        r = APIKeyListResponse(total=0, items=[])
        assert r.total == 0

    def test_oauth2_client_list(self):
        r = OAuth2ClientListResponse(total=0, items=[])
        assert r.total == 0

    def test_ip_whitelist_list(self):
        r = IPWhitelistListResponse(total=0, items=[])
        assert r.total == 0

    def test_ip_blacklist_list(self):
        r = IPBlacklistListResponse(total=0, items=[])
        assert r.total == 0


# ===========================================================================
# Response Schema Tests
# ===========================================================================


class TestAPIKeyResponse:
    def test_valid(self):
        r = APIKeyResponse(
            id=uuid4(),
            name="prod-key",
            key_prefix="sk_live_",
            scopes="read,write",
            allowed_ips=None,
            rate_limit_per_minute=100,
            rate_limit_per_hour=5000,
            is_active=True,
            expires_at=None,
            last_used_at=None,
            last_used_ip=None,
            total_requests=42,
            created_at=datetime.now(),
        )
        assert r.api_key is None  # default


class TestOAuth2ClientResponse:
    def test_valid(self):
        r = OAuth2ClientResponse(
            id=uuid4(),
            client_id="client_abc",
            name="Test Client",
            description="A test client",
            scopes="read",
            grant_types="client_credentials",
            is_active=True,
            is_confidential=True,
            rate_limit_per_minute=100,
            rate_limit_per_hour=5000,
            access_token_lifetime_seconds=3600,
            last_used_at=None,
            total_tokens_issued=0,
            created_at=datetime.now(),
        )
        assert r.client_secret is None  # default


class TestIPWhitelistResponse:
    def test_valid(self):
        r = IPWhitelistResponse(
            id=uuid4(),
            ip_address="192.168.1.0/24",
            description="Office network",
            applies_to="all",
            is_active=True,
            expires_at=None,
            created_at=datetime.now(),
        )
        assert r.is_active is True


class TestIPBlacklistResponse:
    def test_valid(self):
        r = IPBlacklistResponse(
            id=uuid4(),
            ip_address="10.0.0.1",
            reason="Brute force",
            detection_method="brute_force",
            incident_count=50,
            is_active=True,
            expires_at=None,
            last_hit_at=None,
            created_at=datetime.now(),
        )
        assert r.incident_count == 50
