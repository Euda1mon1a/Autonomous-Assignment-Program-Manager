"""Tests for audience-scoped JWT authentication."""

import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from jose import jwt

from app.core.audience_auth import (
    ALGORITHM,
    VALID_AUDIENCES,
    AudienceTokenPayload,
    create_audience_token,
    get_audience_token,
    require_audience,
    revoke_audience_token,
    validate_audience,
    verify_audience_token,
)
from app.core.config import get_settings
from app.models.token_blacklist import TokenBlacklist

settings = get_settings()


class TestAudienceValidation:
    """Tests for audience validation."""

    def test_validate_valid_audience(self):
        """Test validation accepts valid audiences."""
        for audience in VALID_AUDIENCES:
            validate_audience(audience)  # Should not raise

    def test_validate_invalid_audience(self):
        """Test validation rejects invalid audiences."""
        with pytest.raises(ValueError, match="Invalid audience"):
            validate_audience("invalid.audience")

    def test_validate_empty_audience(self):
        """Test validation rejects empty audience."""
        with pytest.raises(ValueError, match="Invalid audience"):
            validate_audience("")


class TestCreateAudienceToken:
    """Tests for audience token creation."""

    def test_create_token_success(self):
        """Test successful token creation."""
        user_id = str(uuid4())
        audience = "jobs.abort"
        ttl_seconds = 120

        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=ttl_seconds,
        )

        # Verify response structure
        assert response.audience == audience
        assert response.ttl_seconds == ttl_seconds
        assert isinstance(response.token, str)
        assert isinstance(response.expires_at, datetime)

        # Verify token can be decoded
        payload = jwt.decode(
            response.token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        assert payload["sub"] == user_id
        assert payload["aud"] == audience
        assert payload["type"] == "audience"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_create_token_invalid_audience(self):
        """Test token creation fails with invalid audience."""
        with pytest.raises(ValueError, match="Invalid audience"):
            create_audience_token(
                user_id=str(uuid4()),
                audience="invalid.operation",
                ttl_seconds=120,
            )

    def test_create_token_ttl_too_long(self):
        """Test token creation fails with TTL > 10 minutes."""
        with pytest.raises(ValueError, match="TTL cannot exceed 600 seconds"):
            create_audience_token(
                user_id=str(uuid4()),
                audience="jobs.abort",
                ttl_seconds=601,
            )

    def test_create_token_ttl_too_short(self):
        """Test token creation fails with TTL < 30 seconds."""
        with pytest.raises(ValueError, match="TTL must be at least 30 seconds"):
            create_audience_token(
                user_id=str(uuid4()),
                audience="jobs.abort",
                ttl_seconds=29,
            )

    def test_create_token_default_ttl(self):
        """Test token creation uses default TTL of 120 seconds."""
        response = create_audience_token(
            user_id=str(uuid4()),
            audience="jobs.abort",
        )

        assert response.ttl_seconds == 120

        # Verify expiration is approximately 120 seconds from now
        now = datetime.utcnow()
        expected_expiry = now + timedelta(seconds=120)
        time_diff = abs((response.expires_at - expected_expiry).total_seconds())
        assert time_diff < 5  # Allow 5 second tolerance

    def test_create_token_unique_jti(self):
        """Test each token gets a unique JTI."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        token1 = create_audience_token(user_id=user_id, audience=audience)
        token2 = create_audience_token(user_id=user_id, audience=audience)

        payload1 = jwt.decode(token1.token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        payload2 = jwt.decode(token2.token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        assert payload1["jti"] != payload2["jti"]


class TestVerifyAudienceToken:
    """Tests for audience token verification."""

    def test_verify_valid_token(self, db):
        """Test verification succeeds for valid token."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=120,
        )

        # Verify token
        payload = verify_audience_token(response.token, audience, db)

        assert payload.sub == user_id
        assert payload.aud == audience
        assert isinstance(payload.jti, str)
        assert isinstance(payload.exp, datetime)
        assert isinstance(payload.iat, datetime)

    def test_verify_wrong_audience(self, db):
        """Test verification fails when audience doesn't match."""
        user_id = str(uuid4())

        # Create token for jobs.abort
        response = create_audience_token(
            user_id=user_id,
            audience="jobs.abort",
            ttl_seconds=120,
        )

        # Try to verify with different audience
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(response.token, "schedule.generate", db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "not valid for this operation" in exc_info.value.detail

    def test_verify_expired_token(self, db):
        """Test verification fails for expired token."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token with very short TTL
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=30,  # 30 seconds
        )

        # Wait for expiration (with clock skew tolerance)
        time.sleep(31)

        # Verify token fails
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(response.token, audience, db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "expired" in exc_info.value.detail.lower()

    def test_verify_blacklisted_token(self, db):
        """Test verification fails for blacklisted token."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=120,
        )

        # Decode to get jti
        payload = jwt.decode(
            response.token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        jti = payload["jti"]

        # Blacklist the token
        revoke_audience_token(
            db=db,
            jti=jti,
            expires_at=response.expires_at,
            user_id=user_id,
            reason="test_revocation",
        )

        # Verify token fails
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(response.token, audience, db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "revoked" in exc_info.value.detail.lower()

    def test_verify_wrong_token_type(self, db):
        """Test verification fails for non-audience tokens."""
        # Create a regular access token (no type field)
        payload = {
            "sub": str(uuid4()),
            "aud": "jobs.abort",
            "exp": datetime.utcnow() + timedelta(minutes=5),
            "iat": datetime.utcnow(),
            "jti": str(uuid4()),
            # No "type": "audience" field
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

        # Verify token fails
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(token, "jobs.abort", db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid token type" in exc_info.value.detail

    def test_verify_missing_claims(self, db):
        """Test verification fails when required claims are missing."""
        # Create token missing required claims
        payload = {
            "sub": str(uuid4()),
            # Missing aud, exp, iat, jti
            "type": "audience",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

        # Verify token fails
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(token, "jobs.abort", db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid token structure" in exc_info.value.detail

    def test_verify_future_dated_token(self, db):
        """Test verification fails for future-dated tokens."""
        # Create token with future iat
        future_time = datetime.utcnow() + timedelta(minutes=10)
        payload = {
            "sub": str(uuid4()),
            "aud": "jobs.abort",
            "exp": future_time + timedelta(minutes=5),
            "iat": future_time,  # Future timestamp
            "jti": str(uuid4()),
            "type": "audience",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

        # Verify token fails
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(token, "jobs.abort", db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid token timestamp" in exc_info.value.detail

    def test_verify_invalid_signature(self, db):
        """Test verification fails for tampered tokens."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create valid token
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=120,
        )

        # Tamper with token (change last character)
        tampered_token = response.token[:-1] + "X"

        # Verify token fails
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(tampered_token, audience, db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid token" in exc_info.value.detail


class TestRevokeAudienceToken:
    """Tests for audience token revocation."""

    def test_revoke_token(self, db):
        """Test token revocation adds to blacklist."""
        user_id = str(uuid4())
        jti = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        # Revoke token
        record = revoke_audience_token(
            db=db,
            jti=jti,
            expires_at=expires_at,
            user_id=user_id,
            reason="test_revocation",
        )

        # Verify record created
        assert record.jti == jti
        assert str(record.user_id) == user_id
        assert record.reason == "test_revocation"

        # Verify token is blacklisted
        assert TokenBlacklist.is_blacklisted(db, jti)

    def test_revoke_token_prevents_use(self, db):
        """Test revoked token cannot be used."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=120,
        )

        # Decode to get jti
        payload = jwt.decode(
            response.token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )

        # Revoke immediately
        revoke_audience_token(
            db=db,
            jti=payload["jti"],
            expires_at=response.expires_at,
            user_id=user_id,
            reason="immediate_revocation",
        )

        # Verify token fails
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(response.token, audience, db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequireAudience:
    """Tests for require_audience dependency."""

    @pytest.mark.asyncio
    async def test_require_audience_success(self, db):
        """Test dependency succeeds with valid token."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=120,
        )

        # Create dependency
        dependency = require_audience(audience)

        # Call dependency with valid authorization header
        authorization = f"Bearer {response.token}"
        payload = await dependency(authorization=authorization, db=db)

        assert payload.sub == user_id
        assert payload.aud == audience

    @pytest.mark.asyncio
    async def test_require_audience_missing_header(self, db):
        """Test dependency fails without Authorization header."""
        dependency = require_audience("jobs.abort")

        with pytest.raises(HTTPException) as exc_info:
            await dependency(authorization=None, db=db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Authorization header required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_audience_invalid_format(self, db):
        """Test dependency fails with invalid header format."""
        dependency = require_audience("jobs.abort")

        # Missing "Bearer " prefix
        with pytest.raises(HTTPException) as exc_info:
            await dependency(authorization="invalid-token", db=db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid authorization format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_audience_wrong_audience(self, db):
        """Test dependency fails with wrong audience token."""
        user_id = str(uuid4())

        # Create token for different audience
        response = create_audience_token(
            user_id=user_id,
            audience="jobs.abort",
            ttl_seconds=120,
        )

        # Try to use for different audience
        dependency = require_audience("schedule.generate")
        authorization = f"Bearer {response.token}"

        with pytest.raises(HTTPException) as exc_info:
            await dependency(authorization=authorization, db=db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "not valid for this operation" in exc_info.value.detail


class TestGetAudienceToken:
    """Tests for get_audience_token function."""

    def test_get_audience_token_success(self, db):
        """Test manual token extraction succeeds."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=120,
        )

        # Extract token
        authorization = f"Bearer {response.token}"
        payload = get_audience_token(authorization, audience, db)

        assert payload.sub == user_id
        assert payload.aud == audience

    def test_get_audience_token_missing_header(self, db):
        """Test extraction fails without header."""
        with pytest.raises(ValueError, match="Authorization header is required"):
            get_audience_token(None, "jobs.abort", db)

    def test_get_audience_token_invalid_format(self, db):
        """Test extraction fails with invalid format."""
        with pytest.raises(ValueError, match="Invalid authorization format"):
            get_audience_token("invalid-token", "jobs.abort", db)

    def test_get_audience_token_without_db(self):
        """Test extraction works without db (no blacklist check)."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=120,
        )

        # Extract without db
        authorization = f"Bearer {response.token}"
        payload = get_audience_token(authorization, audience, db=None)

        assert payload.sub == user_id
        assert payload.aud == audience


class TestClockSkewTolerance:
    """Tests for clock skew tolerance."""

    def test_verify_near_expiration_within_tolerance(self, db):
        """Test token near expiration (within tolerance) succeeds."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token that expires in 35 seconds
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=35,
        )

        # Wait until just before expiration (within 30s tolerance)
        time.sleep(32)

        # Should still succeed (within clock skew tolerance)
        payload = verify_audience_token(response.token, audience, db)
        assert payload.sub == user_id

    def test_verify_past_tolerance_fails(self, db):
        """Test token past tolerance window fails."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Create token with minimum TTL
        response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=30,
        )

        # Wait past expiration + tolerance
        time.sleep(61)  # 30s TTL + 30s tolerance + 1s buffer

        # Should fail
        with pytest.raises(HTTPException) as exc_info:
            verify_audience_token(response.token, audience, db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    @pytest.mark.asyncio
    async def test_abort_job_workflow(self, db):
        """Test complete workflow: create token, use for operation, revoke."""
        user_id = str(uuid4())
        audience = "jobs.abort"

        # Step 1: User requests elevated permission token
        token_response = create_audience_token(
            user_id=user_id,
            audience=audience,
            ttl_seconds=120,
        )

        # Step 2: User performs operation with token
        dependency = require_audience(audience)
        authorization = f"Bearer {token_response.token}"
        payload = await dependency(authorization=authorization, db=db)

        assert payload.sub == user_id

        # Step 3: Token is revoked after use (good practice)
        token_payload = jwt.decode(
            token_response.token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        revoke_audience_token(
            db=db,
            jti=token_payload["jti"],
            expires_at=token_response.expires_at,
            user_id=user_id,
            reason="operation_completed",
        )

        # Step 4: Token cannot be reused
        with pytest.raises(HTTPException):
            await dependency(authorization=authorization, db=db)

    def test_multiple_audiences_same_user(self, db):
        """Test user can have tokens for different audiences simultaneously."""
        user_id = str(uuid4())

        # Create tokens for different operations
        token1 = create_audience_token(user_id, "jobs.abort", ttl_seconds=120)
        token2 = create_audience_token(user_id, "schedule.generate", ttl_seconds=120)
        token3 = create_audience_token(user_id, "swap.execute", ttl_seconds=120)

        # Verify each token works for its audience
        payload1 = verify_audience_token(token1.token, "jobs.abort", db)
        payload2 = verify_audience_token(token2.token, "schedule.generate", db)
        payload3 = verify_audience_token(token3.token, "swap.execute", db)

        assert payload1.sub == user_id
        assert payload2.sub == user_id
        assert payload3.sub == user_id

        # Verify tokens don't work for wrong audiences
        with pytest.raises(HTTPException):
            verify_audience_token(token1.token, "schedule.generate", db)

        with pytest.raises(HTTPException):
            verify_audience_token(token2.token, "swap.execute", db)


# Fixtures


@pytest.fixture
def db():
    """Mock database session for testing."""
    from unittest.mock import MagicMock

    db_mock = MagicMock()

    # Mock TokenBlacklist.is_blacklisted to track blacklisted tokens
    blacklisted_tokens = set()

    def is_blacklisted(jti):
        return jti in blacklisted_tokens

    def add_to_blacklist(record):
        blacklisted_tokens.add(record.jti)

    db_mock.add.side_effect = add_to_blacklist
    db_mock.commit.return_value = None

    # Patch TokenBlacklist.is_blacklisted
    with patch.object(TokenBlacklist, "is_blacklisted", side_effect=is_blacklisted):
        yield db_mock
