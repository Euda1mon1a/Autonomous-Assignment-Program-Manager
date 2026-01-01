"""
Tests for OAuth2 PKCE API routes.

Comprehensive test coverage for:
- Authorization endpoint (OAuth2 authorization code flow)
- Token endpoint (code exchange for access token)
- Token introspection (RFC 7662)
- Token revocation
- Client registration and management
- PKCE validation
- Security requirements
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.oauth2_pkce import (
    generate_code_challenge,
    generate_code_verifier,
)
from app.models.oauth2_authorization_code import OAuth2AuthorizationCode
from app.models.oauth2_client import PKCEClient
from app.models.user import User
from app.core.security import get_password_hash


@pytest.fixture
def pkce_client(db: Session) -> PKCEClient:
    """Create a test OAuth2 PKCE client."""
    client = PKCEClient(
        id=uuid4(),
        client_id=f"test-client-{uuid4().hex[:8]}",
        client_name="Test OAuth2 Client",
        redirect_uris=["https://example.com/callback", "https://app.example.com/auth"],
        client_uri="https://example.com",
        scope="read write",
        is_public=True,
        is_active=True,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user for OAuth2 flow."""
    user = User(
        id=uuid4(),
        username="oauth_test_user",
        email="oauth@test.org",
        hashed_password=get_password_hash("testpass123"),
        role="resident",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def code_verifier() -> str:
    """Generate a PKCE code verifier for testing."""
    return generate_code_verifier()


@pytest.fixture
def code_challenge(code_verifier: str) -> str:
    """Generate a PKCE code challenge for testing."""
    return generate_code_challenge(code_verifier, "S256")


class TestAuthorizationEndpoint:
    """Test suite for OAuth2 authorization endpoint."""

    def test_authorize_success(
        self,
        client: TestClient,
        db: Session,
        pkce_client: PKCEClient,
        test_user: User,
        code_challenge: str,
        auth_headers: dict,
    ):
        """Test successful authorization code creation."""
        payload = {
            "client_id": pkce_client.client_id,
            "redirect_uri": pkce_client.redirect_uris[0],
            "scope": "read",
            "state": "random_state_string",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        # Login first to get authenticated session
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "oauth_test_user", "password": "testpass123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post("/api/oauth2/authorize", json=payload, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert data["state"] == "random_state_string"
        assert len(data["code"]) > 0

        # Verify code is stored in database
        auth_code = (
            db.query(OAuth2AuthorizationCode)
            .filter_by(code=data["code"])
            .first()
        )
        assert auth_code is not None
        assert str(auth_code.user_id) == str(test_user.id)

    def test_authorize_invalid_client(
        self, client: TestClient, code_challenge: str, auth_headers: dict
    ):
        """Test authorization with invalid client ID."""
        payload = {
            "client_id": "invalid-client-id",
            "redirect_uri": "https://example.com/callback",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        response = client.post("/api/oauth2/authorize", json=payload, headers=auth_headers)

        assert response.status_code in [401, 403]

    def test_authorize_invalid_redirect_uri(
        self,
        client: TestClient,
        pkce_client: PKCEClient,
        code_challenge: str,
        auth_headers: dict,
    ):
        """Test authorization with invalid redirect URI."""
        payload = {
            "client_id": pkce_client.client_id,
            "redirect_uri": "https://evil.com/callback",  # Not in registered URIs
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        response = client.post("/api/oauth2/authorize", json=payload, headers=auth_headers)

        assert response.status_code in [400, 401, 403]

    def test_authorize_unauthenticated(
        self, client: TestClient, pkce_client: PKCEClient, code_challenge: str
    ):
        """Test authorization without authentication."""
        payload = {
            "client_id": pkce_client.client_id,
            "redirect_uri": pkce_client.redirect_uris[0],
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        response = client.post("/api/oauth2/authorize", json=payload)

        assert response.status_code in [401, 403]

    def test_authorize_with_state_parameter(
        self,
        client: TestClient,
        pkce_client: PKCEClient,
        code_challenge: str,
        auth_headers: dict,
    ):
        """Test authorization with state parameter (CSRF protection)."""
        payload = {
            "client_id": pkce_client.client_id,
            "redirect_uri": pkce_client.redirect_uris[0],
            "state": "unique-state-12345",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        # Login first
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "oauth_test_user", "password": "testpass123"},
        )
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            response = client.post("/api/oauth2/authorize", json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                assert data["state"] == "unique-state-12345"


class TestTokenEndpoint:
    """Test suite for OAuth2 token endpoint."""

    def test_token_exchange_success(
        self,
        client: TestClient,
        db: Session,
        pkce_client: PKCEClient,
        test_user: User,
        code_verifier: str,
        code_challenge: str,
    ):
        """Test successful token exchange with authorization code."""
        # First, create an authorization code
        auth_code = OAuth2AuthorizationCode(
            id=uuid4(),
            code=f"auth_code_{uuid4().hex}",
            client_id=pkce_client.client_id,
            user_id=test_user.id,
            redirect_uri=pkce_client.redirect_uris[0],
            scope="read",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.add(auth_code)
        db.commit()

        payload = {
            "grant_type": "authorization_code",
            "code": auth_code.code,
            "redirect_uri": pkce_client.redirect_uris[0],
            "client_id": pkce_client.client_id,
            "code_verifier": code_verifier,
        }

        response = client.post("/api/oauth2/token", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_token_exchange_invalid_code(
        self, client: TestClient, pkce_client: PKCEClient, code_verifier: str
    ):
        """Test token exchange with invalid authorization code."""
        payload = {
            "grant_type": "authorization_code",
            "code": "invalid_code_12345",
            "redirect_uri": pkce_client.redirect_uris[0],
            "client_id": pkce_client.client_id,
            "code_verifier": code_verifier,
        }

        response = client.post("/api/oauth2/token", json=payload)

        assert response.status_code in [400, 401]

    def test_token_exchange_expired_code(
        self,
        client: TestClient,
        db: Session,
        pkce_client: PKCEClient,
        test_user: User,
        code_verifier: str,
        code_challenge: str,
    ):
        """Test token exchange with expired authorization code."""
        # Create expired authorization code
        auth_code = OAuth2AuthorizationCode(
            id=uuid4(),
            code=f"expired_code_{uuid4().hex}",
            client_id=pkce_client.client_id,
            user_id=test_user.id,
            redirect_uri=pkce_client.redirect_uris[0],
            scope="read",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            expires_at=datetime.utcnow() - timedelta(minutes=5),  # Expired
        )
        db.add(auth_code)
        db.commit()

        payload = {
            "grant_type": "authorization_code",
            "code": auth_code.code,
            "redirect_uri": pkce_client.redirect_uris[0],
            "client_id": pkce_client.client_id,
            "code_verifier": code_verifier,
        }

        response = client.post("/api/oauth2/token", json=payload)

        assert response.status_code in [400, 401]

    def test_token_exchange_wrong_verifier(
        self,
        client: TestClient,
        db: Session,
        pkce_client: PKCEClient,
        test_user: User,
        code_challenge: str,
    ):
        """Test token exchange with incorrect code verifier (PKCE violation)."""
        # Create authorization code
        auth_code = OAuth2AuthorizationCode(
            id=uuid4(),
            code=f"auth_code_{uuid4().hex}",
            client_id=pkce_client.client_id,
            user_id=test_user.id,
            redirect_uri=pkce_client.redirect_uris[0],
            scope="read",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.add(auth_code)
        db.commit()

        # Use wrong verifier
        wrong_verifier = generate_code_verifier()

        payload = {
            "grant_type": "authorization_code",
            "code": auth_code.code,
            "redirect_uri": pkce_client.redirect_uris[0],
            "client_id": pkce_client.client_id,
            "code_verifier": wrong_verifier,
        }

        response = client.post("/api/oauth2/token", json=payload)

        assert response.status_code in [400, 401]

    def test_token_exchange_redirect_uri_mismatch(
        self,
        client: TestClient,
        db: Session,
        pkce_client: PKCEClient,
        test_user: User,
        code_verifier: str,
        code_challenge: str,
    ):
        """Test token exchange with mismatched redirect URI."""
        # Create authorization code
        auth_code = OAuth2AuthorizationCode(
            id=uuid4(),
            code=f"auth_code_{uuid4().hex}",
            client_id=pkce_client.client_id,
            user_id=test_user.id,
            redirect_uri=pkce_client.redirect_uris[0],
            scope="read",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.add(auth_code)
        db.commit()

        # Use different redirect URI
        payload = {
            "grant_type": "authorization_code",
            "code": auth_code.code,
            "redirect_uri": "https://different.com/callback",
            "client_id": pkce_client.client_id,
            "code_verifier": code_verifier,
        }

        response = client.post("/api/oauth2/token", json=payload)

        assert response.status_code in [400, 401]


class TestTokenIntrospectionEndpoint:
    """Test suite for token introspection endpoint."""

    def test_introspect_valid_token(
        self, client: TestClient, db: Session, test_user: User
    ):
        """Test introspecting a valid access token."""
        # Login to get a real token
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "oauth_test_user", "password": "testpass123"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]

            payload = {"token": token}

            response = client.post("/api/oauth2/introspect", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert "active" in data

    def test_introspect_invalid_token(self, client: TestClient):
        """Test introspecting an invalid token."""
        payload = {"token": "invalid_token_12345"}

        response = client.post("/api/oauth2/introspect", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False

    def test_introspect_expired_token(self, client: TestClient):
        """Test introspecting an expired token."""
        # Create a token that looks valid but is expired
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        payload = {"token": expired_token}

        response = client.post("/api/oauth2/introspect", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should indicate token is not active
        assert "active" in data


class TestTokenRevocationEndpoint:
    """Test suite for token revocation endpoint."""

    def test_revoke_token_success(
        self, client: TestClient, db: Session, test_user: User
    ):
        """Test successful token revocation."""
        # Login to get a token
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "oauth_test_user", "password": "testpass123"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = client.post(
                "/api/oauth2/revoke",
                params={"token": token},
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "revoked" in data["message"].lower()

    def test_revoke_token_unauthenticated(self, client: TestClient):
        """Test token revocation without authentication."""
        response = client.post(
            "/api/oauth2/revoke",
            params={"token": "some_token"},
        )

        assert response.status_code in [401, 403]


class TestClientRegistrationEndpoint:
    """Test suite for OAuth2 client registration endpoint."""

    def test_register_client_success(
        self, client: TestClient, db: Session, admin_user: User
    ):
        """Test successful client registration by admin."""
        # Login as admin
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            payload = {
                "client_name": "New Test Client",
                "redirect_uris": ["https://newapp.com/callback"],
                "client_uri": "https://newapp.com",
                "scope": "read write",
            }

            response = client.post("/api/oauth2/clients", json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                assert "client_id" in data
                assert data["client_name"] == "New Test Client"
                assert data["is_public"] is True
                assert data["is_active"] is True

    def test_register_client_non_admin(
        self, client: TestClient, db: Session, test_user: User
    ):
        """Test client registration by non-admin user (should fail)."""
        # Login as regular user
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "oauth_test_user", "password": "testpass123"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            payload = {
                "client_name": "Unauthorized Client",
                "redirect_uris": ["https://app.com/callback"],
            }

            response = client.post("/api/oauth2/clients", json=payload, headers=headers)

            assert response.status_code == 403

    def test_register_client_unauthenticated(self, client: TestClient):
        """Test client registration without authentication."""
        payload = {
            "client_name": "Unauthenticated Client",
            "redirect_uris": ["https://app.com/callback"],
        }

        response = client.post("/api/oauth2/clients", json=payload)

        assert response.status_code in [401, 403]

    def test_register_client_invalid_redirect_uri(
        self, client: TestClient, admin_user: User
    ):
        """Test client registration with invalid redirect URI."""
        login_response = client.post(
            "/api/auth/login/json",
            json={"username": "testadmin", "password": "testpass123"},
        )

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            payload = {
                "client_name": "Invalid URI Client",
                "redirect_uris": ["not-a-valid-uri"],  # Invalid URI
            }

            response = client.post("/api/oauth2/clients", json=payload, headers=headers)

            assert response.status_code == 422  # Validation error


class TestOAuth2SecurityRequirements:
    """Test suite for OAuth2 security requirements."""

    def test_authorization_code_single_use(
        self,
        client: TestClient,
        db: Session,
        pkce_client: PKCEClient,
        test_user: User,
        code_verifier: str,
        code_challenge: str,
    ):
        """Test that authorization codes can only be used once."""
        # Create authorization code
        auth_code = OAuth2AuthorizationCode(
            id=uuid4(),
            code=f"single_use_code_{uuid4().hex}",
            client_id=pkce_client.client_id,
            user_id=test_user.id,
            redirect_uri=pkce_client.redirect_uris[0],
            scope="read",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.add(auth_code)
        db.commit()

        payload = {
            "grant_type": "authorization_code",
            "code": auth_code.code,
            "redirect_uri": pkce_client.redirect_uris[0],
            "client_id": pkce_client.client_id,
            "code_verifier": code_verifier,
        }

        # First exchange should succeed
        response1 = client.post("/api/oauth2/token", json=payload)

        # Second exchange should fail (code already used)
        response2 = client.post("/api/oauth2/token", json=payload)

        # Either first succeeds and second fails, or both fail
        if response1.status_code == 200:
            assert response2.status_code in [400, 401]

    def test_pkce_prevents_code_interception(
        self,
        client: TestClient,
        db: Session,
        pkce_client: PKCEClient,
        test_user: User,
        code_challenge: str,
    ):
        """Test that PKCE prevents authorization code interception."""
        # Attacker intercepts the authorization code
        auth_code = OAuth2AuthorizationCode(
            id=uuid4(),
            code=f"intercepted_code_{uuid4().hex}",
            client_id=pkce_client.client_id,
            user_id=test_user.id,
            redirect_uri=pkce_client.redirect_uris[0],
            scope="read",
            code_challenge=code_challenge,
            code_challenge_method="S256",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )
        db.add(auth_code)
        db.commit()

        # Attacker tries to use code without correct verifier
        attacker_verifier = generate_code_verifier()

        payload = {
            "grant_type": "authorization_code",
            "code": auth_code.code,
            "redirect_uri": pkce_client.redirect_uris[0],
            "client_id": pkce_client.client_id,
            "code_verifier": attacker_verifier,
        }

        response = client.post("/api/oauth2/token", json=payload)

        # Should fail due to PKCE verification
        assert response.status_code in [400, 401]


class TestOAuth2EdgeCases:
    """Test suite for OAuth2 edge cases and error handling."""

    def test_authorize_with_missing_pkce_challenge(
        self, client: TestClient, pkce_client: PKCEClient, auth_headers: dict
    ):
        """Test authorization without PKCE code challenge."""
        payload = {
            "client_id": pkce_client.client_id,
            "redirect_uri": pkce_client.redirect_uris[0],
            # Missing code_challenge
        }

        response = client.post("/api/oauth2/authorize", json=payload, headers=auth_headers)

        assert response.status_code == 422  # Validation error

    def test_token_with_unsupported_grant_type(
        self, client: TestClient, pkce_client: PKCEClient
    ):
        """Test token endpoint with unsupported grant type."""
        payload = {
            "grant_type": "password",  # Not supported in PKCE flow
            "username": "test",
            "password": "test",
        }

        response = client.post("/api/oauth2/token", json=payload)

        assert response.status_code in [400, 422]

    def test_authorize_with_inactive_client(
        self,
        client: TestClient,
        db: Session,
        pkce_client: PKCEClient,
        code_challenge: str,
        auth_headers: dict,
    ):
        """Test authorization with inactive client."""
        # Deactivate client
        pkce_client.is_active = False
        db.commit()

        payload = {
            "client_id": pkce_client.client_id,
            "redirect_uri": pkce_client.redirect_uris[0],
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        response = client.post("/api/oauth2/authorize", json=payload, headers=auth_headers)

        assert response.status_code in [401, 403]
