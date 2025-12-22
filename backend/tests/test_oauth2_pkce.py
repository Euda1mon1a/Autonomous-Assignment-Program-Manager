"""Tests for OAuth2 PKCE implementation."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException

from app.auth.oauth2_pkce import (
    create_authorization_code,
    exchange_code_for_token,
    generate_code_challenge,
    generate_code_verifier,
    introspect_token,
    register_client,
    revoke_token,
    validate_client,
    validate_redirect_uri,
    validate_state_parameter,
    verify_code_challenge,
)
from app.models.oauth2_authorization_code import OAuth2AuthorizationCode
from app.models.oauth2_client import PKCEClient
from app.models.user import User
from app.schemas.oauth2 import AuthorizationRequest, TokenRequest


class TestPKCECodeGeneration:
    """Test PKCE code verifier and challenge generation."""

    def test_generate_code_verifier(self):
        """Test code verifier generation."""
        verifier = generate_code_verifier()

        assert isinstance(verifier, str)
        assert len(verifier) >= 43
        assert len(verifier) <= 128
        # Base64url characters only
        assert all(c.isalnum() or c in "-_" for c in verifier)

    def test_generate_code_challenge_s256(self):
        """Test S256 code challenge generation."""
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier, "S256")

        assert isinstance(challenge, str)
        assert len(challenge) >= 43  # SHA256 base64url is 43 chars
        assert challenge != verifier  # Challenge is hashed

    def test_generate_code_challenge_plain(self):
        """Test plain code challenge generation."""
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier, "plain")

        assert challenge == verifier  # Plain method returns verifier

    def test_generate_code_challenge_invalid_method(self):
        """Test invalid code challenge method."""
        verifier = generate_code_verifier()

        with pytest.raises(ValueError, match="Unsupported code challenge method"):
            generate_code_challenge(verifier, "invalid")

    def test_verify_code_challenge_s256_success(self):
        """Test successful S256 code challenge verification."""
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier, "S256")

        assert verify_code_challenge(verifier, challenge, "S256") is True

    def test_verify_code_challenge_s256_failure(self):
        """Test failed S256 code challenge verification."""
        verifier1 = generate_code_verifier()
        verifier2 = generate_code_verifier()
        challenge = generate_code_challenge(verifier1, "S256")

        assert verify_code_challenge(verifier2, challenge, "S256") is False

    def test_verify_code_challenge_plain_success(self):
        """Test successful plain code challenge verification."""
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier, "plain")

        assert verify_code_challenge(verifier, challenge, "plain") is True


class TestClientManagement:
    """Test OAuth2 PKCE client management."""

    @pytest.mark.asyncio
    async def test_register_client(self, db):
        """Test client registration."""
        client = await register_client(
            db,
            client_name="Test App",
            redirect_uris=["https://example.com/callback"],
            client_uri="https://example.com",
            scope="read write",
        )

        assert isinstance(client, PKCEClient)
        assert client.client_name == "Test App"
        assert client.is_public is True
        assert client.is_active is True
        assert "https://example.com/callback" in client.redirect_uris

    @pytest.mark.asyncio
    async def test_validate_client_success(self, db, pkce_client):
        """Test successful client validation."""
        validated_client = await validate_client(db, pkce_client.client_id)

        assert validated_client.id == pkce_client.id

    @pytest.mark.asyncio
    async def test_validate_client_not_found(self, db):
        """Test client validation with non-existent client."""
        with pytest.raises(HTTPException) as exc_info:
            await validate_client(db, "non-existent-client-id")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_client_inactive(self, db, pkce_client):
        """Test client validation with inactive client."""
        pkce_client.is_active = False
        db.commit()

        with pytest.raises(HTTPException) as exc_info:
            await validate_client(db, pkce_client.client_id)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_redirect_uri_success(self, pkce_client):
        """Test successful redirect URI validation."""
        # Should not raise exception
        await validate_redirect_uri(pkce_client, pkce_client.redirect_uris[0])

    @pytest.mark.asyncio
    async def test_validate_redirect_uri_failure(self, pkce_client):
        """Test failed redirect URI validation."""
        with pytest.raises(HTTPException) as exc_info:
            await validate_redirect_uri(pkce_client, "https://evil.com/callback")

        assert exc_info.value.status_code == 400


class TestAuthorizationFlow:
    """Test OAuth2 authorization code flow with PKCE."""

    @pytest.mark.asyncio
    async def test_create_authorization_code(self, db, pkce_client, test_user):
        """Test authorization code creation."""
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier, "S256")

        request = AuthorizationRequest(
            client_id=pkce_client.client_id,
            redirect_uri=pkce_client.redirect_uris[0],
            scope="read",
            state="random_state",
            code_challenge=code_challenge,
            code_challenge_method="S256",
        )

        response = await create_authorization_code(db, request, test_user)

        assert response.code is not None
        assert response.state == "random_state"

        # Verify code is stored in database
        auth_code = db.query(OAuth2AuthorizationCode).filter_by(code=response.code).first()
        assert auth_code is not None
        assert auth_code.user_id == test_user.id
        assert auth_code.code_challenge == code_challenge

    @pytest.mark.asyncio
    async def test_create_authorization_code_invalid_client(self, db, test_user):
        """Test authorization code creation with invalid client."""
        request = AuthorizationRequest(
            client_id="invalid-client",
            redirect_uri="https://example.com/callback",
            code_challenge=generate_code_challenge(generate_code_verifier(), "S256"),
            code_challenge_method="S256",
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_authorization_code(db, request, test_user)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_create_authorization_code_invalid_redirect_uri(self, db, pkce_client, test_user):
        """Test authorization code creation with invalid redirect URI."""
        request = AuthorizationRequest(
            client_id=pkce_client.client_id,
            redirect_uri="https://evil.com/callback",
            code_challenge=generate_code_challenge(generate_code_verifier(), "S256"),
            code_challenge_method="S256",
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_authorization_code(db, request, test_user)

        assert exc_info.value.status_code == 400


class TestTokenExchange:
    """Test token exchange with PKCE validation."""

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, db, auth_code_with_pkce, pkce_client):
        """Test successful token exchange."""
        request = TokenRequest(
            code=auth_code_with_pkce["code"],
            redirect_uri=pkce_client.redirect_uris[0],
            client_id=pkce_client.client_id,
            code_verifier=auth_code_with_pkce["verifier"],
        )

        response = await exchange_code_for_token(db, request)

        assert response.access_token is not None
        assert response.token_type == "Bearer"
        assert response.expires_in > 0

        # Verify code is marked as used
        auth_code = db.query(OAuth2AuthorizationCode).filter_by(
            code=auth_code_with_pkce["code"]
        ).first()
        assert auth_code.is_used == "true"

    @pytest.mark.asyncio
    async def test_exchange_code_invalid_verifier(self, db, auth_code_with_pkce, pkce_client):
        """Test token exchange with invalid code verifier."""
        request = TokenRequest(
            code=auth_code_with_pkce["code"],
            redirect_uri=pkce_client.redirect_uris[0],
            client_id=pkce_client.client_id,
            code_verifier=generate_code_verifier(),  # Wrong verifier
        )

        with pytest.raises(HTTPException) as exc_info:
            await exchange_code_for_token(db, request)

        assert exc_info.value.status_code == 400
        assert "Invalid code verifier" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_exchange_code_already_used(self, db, auth_code_with_pkce, pkce_client):
        """Test token exchange with already used code."""
        # Use the code first time
        request = TokenRequest(
            code=auth_code_with_pkce["code"],
            redirect_uri=pkce_client.redirect_uris[0],
            client_id=pkce_client.client_id,
            code_verifier=auth_code_with_pkce["verifier"],
        )
        await exchange_code_for_token(db, request)

        # Try to use it again
        with pytest.raises(HTTPException) as exc_info:
            await exchange_code_for_token(db, request)

        assert exc_info.value.status_code == 400
        assert "already been used" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_exchange_code_expired(self, db, pkce_client, test_user):
        """Test token exchange with expired code."""
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier, "S256")

        # Create expired authorization code
        auth_code = OAuth2AuthorizationCode(
            code="expired_code",
            client_id=pkce_client.client_id,
            user_id=test_user.id,
            redirect_uri=pkce_client.redirect_uris[0],
            code_challenge=code_challenge,
            code_challenge_method="S256",
            is_used="false",
            expires_at=datetime.utcnow() - timedelta(minutes=5),  # Expired
        )
        db.add(auth_code)
        db.commit()

        request = TokenRequest(
            code="expired_code",
            redirect_uri=pkce_client.redirect_uris[0],
            client_id=pkce_client.client_id,
            code_verifier=code_verifier,
        )

        with pytest.raises(HTTPException) as exc_info:
            await exchange_code_for_token(db, request)

        assert exc_info.value.status_code == 400
        assert "expired" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_exchange_code_redirect_uri_mismatch(self, db, auth_code_with_pkce, pkce_client):
        """Test token exchange with mismatched redirect URI."""
        # Add another redirect URI to the client
        pkce_client.redirect_uris.append("https://other.com/callback")
        db.commit()

        request = TokenRequest(
            code=auth_code_with_pkce["code"],
            redirect_uri="https://other.com/callback",  # Different from auth request
            client_id=pkce_client.client_id,
            code_verifier=auth_code_with_pkce["verifier"],
        )

        with pytest.raises(HTTPException) as exc_info:
            await exchange_code_for_token(db, request)

        assert exc_info.value.status_code == 400
        assert "Redirect URI mismatch" in exc_info.value.detail


class TestTokenIntrospection:
    """Test token introspection."""

    @pytest.mark.asyncio
    async def test_introspect_valid_token(self, db, valid_access_token, test_user):
        """Test introspection of valid token."""
        response = await introspect_token(db, valid_access_token)

        assert response.active is True
        assert response.username == test_user.username
        assert response.sub == str(test_user.id)

    @pytest.mark.asyncio
    async def test_introspect_invalid_token(self, db):
        """Test introspection of invalid token."""
        response = await introspect_token(db, "invalid.token.here")

        assert response.active is False

    @pytest.mark.asyncio
    async def test_revoke_token(self, db, valid_access_token, test_user):
        """Test token revocation."""
        # Revoke the token
        await revoke_token(db, valid_access_token, test_user.id)

        # Verify it's blacklisted
        response = await introspect_token(db, valid_access_token)
        assert response.active is False


class TestStateValidation:
    """Test state parameter validation for CSRF protection."""

    @pytest.mark.asyncio
    async def test_validate_state_parameter_match(self):
        """Test successful state validation."""
        # Should not raise exception
        await validate_state_parameter("random_state", "random_state")

    @pytest.mark.asyncio
    async def test_validate_state_parameter_mismatch(self):
        """Test failed state validation."""
        with pytest.raises(HTTPException) as exc_info:
            await validate_state_parameter("state1", "state2")

        assert exc_info.value.status_code == 400
        assert "CSRF" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_validate_state_parameter_both_none(self):
        """Test state validation when both are None."""
        # Should not raise exception (acceptable but not recommended)
        await validate_state_parameter(None, None)


# Pytest fixtures

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        role="coordinator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def pkce_client(db):
    """Create a test PKCE client."""
    client = PKCEClient(
        client_id="test_client_id",
        client_name="Test PKCE Client",
        redirect_uris=["https://example.com/callback"],
        is_public=True,
        is_active=True,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@pytest.fixture
def auth_code_with_pkce(db, pkce_client, test_user):
    """Create an authorization code with PKCE challenge."""
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier, "S256")

    auth_code = OAuth2AuthorizationCode(
        code="test_auth_code",
        client_id=pkce_client.client_id,
        user_id=test_user.id,
        redirect_uri=pkce_client.redirect_uris[0],
        code_challenge=code_challenge,
        code_challenge_method="S256",
        is_used="false",
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(auth_code)
    db.commit()

    return {
        "code": auth_code.code,
        "verifier": code_verifier,
        "challenge": code_challenge,
    }


@pytest.fixture
def valid_access_token(test_user):
    """Create a valid access token for testing."""
    from app.core.security import create_access_token

    token_data = {
        "sub": str(test_user.id),
        "username": test_user.username,
        "role": test_user.role,
    }
    access_token, jti, expires_at = create_access_token(token_data)
    return access_token
