"""Tests for SSO (Single Sign-On) API routes.

Tests the SSO authentication flows including:
- SAML metadata and login
- OAuth2/OIDC login and callback
- Provider listing
- SSO status
- User provisioning
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


class TestSSORoutes:
    """Test suite for SSO API endpoints."""

    # ========================================================================
    # SAML Tests
    # ========================================================================

    @patch("app.api.routes.sso.sso_config")
    @patch("app.api.routes.sso.SAMLProvider")
    def test_saml_metadata_success(
        self,
        mock_saml_provider: MagicMock,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test getting SAML SP metadata."""
        mock_config.saml.enabled = True

        mock_provider = MagicMock()
        mock_provider.generate_sp_metadata.return_value = """<?xml version="1.0"?>
        <EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata">
        </EntityDescriptor>"""
        mock_saml_provider.return_value = mock_provider

        response = client.get("/api/sso/saml/metadata")
        assert response.status_code == 200
        assert "xml" in response.headers.get("content-type", "")

    @patch("app.api.routes.sso.sso_config")
    def test_saml_metadata_not_enabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SAML metadata when SAML disabled."""
        mock_config.saml.enabled = False

        response = client.get("/api/sso/saml/metadata")
        assert response.status_code == 404
        assert "not enabled" in response.json()["detail"]

    @patch("app.api.routes.sso.sso_config")
    @patch("app.api.routes.sso.SAMLProvider")
    def test_saml_login_redirect(
        self,
        mock_saml_provider: MagicMock,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SAML login initiates redirect."""
        mock_config.saml.enabled = True

        mock_provider = MagicMock()
        mock_provider.generate_authn_request.return_value = (
            "request-id-123",
            "https://idp.example.com/sso?SAMLRequest=...",
        )
        mock_saml_provider.return_value = mock_provider

        response = client.get(
            "/api/sso/saml/login",
            follow_redirects=False,
        )
        assert response.status_code == 307  # Redirect

    @patch("app.api.routes.sso.sso_config")
    def test_saml_login_not_enabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SAML login when disabled."""
        mock_config.saml.enabled = False

        response = client.get("/api/sso/saml/login")
        assert response.status_code == 404

    @patch("app.api.routes.sso.sso_config")
    def test_saml_acs_not_enabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SAML ACS when disabled."""
        mock_config.saml.enabled = False

        response = client.post(
            "/api/sso/saml/acs",
            data={"SAMLResponse": "base64encoded"},
        )
        assert response.status_code == 404

    @patch("app.api.routes.sso.sso_config")
    def test_saml_acs_missing_response(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SAML ACS without SAMLResponse."""
        mock_config.saml.enabled = True

        response = client.post("/api/sso/saml/acs", data={})
        assert response.status_code == 400
        assert "Missing SAMLResponse" in response.json()["detail"]

    @patch("app.api.routes.sso.sso_config")
    def test_saml_logout_not_enabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SAML logout when disabled."""
        mock_config.saml.enabled = False

        response = client.get("/api/sso/saml/logout?name_id=user@example.com")
        assert response.status_code == 404

    @patch("app.api.routes.sso.sso_config")
    @patch("app.api.routes.sso.SAMLProvider")
    def test_saml_logout_redirect(
        self,
        mock_saml_provider: MagicMock,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SAML logout initiates redirect."""
        mock_config.saml.enabled = True

        mock_provider = MagicMock()
        mock_provider.generate_logout_request.return_value = (
            "request-id-456",
            "https://idp.example.com/logout?SAMLRequest=...",
        )
        mock_saml_provider.return_value = mock_provider

        response = client.get(
            "/api/sso/saml/logout?name_id=user@example.com",
            follow_redirects=False,
        )
        assert response.status_code == 307

    # ========================================================================
    # OAuth2/OIDC Tests
    # ========================================================================

    @patch("app.api.routes.sso.sso_config")
    @patch("app.api.routes.sso.OAuth2Provider")
    def test_oauth2_login_redirect(
        self,
        mock_oauth_provider: MagicMock,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test OAuth2 login initiates redirect."""
        mock_config.oauth2.enabled = True

        mock_provider = MagicMock()
        mock_provider.generate_authorization_url.return_value = {
            "authorization_url": "https://oauth.example.com/authorize?client_id=...",
            "state": "random-state-123",
            "code_verifier": "pkce-verifier",
        }
        mock_oauth_provider.return_value = mock_provider

        response = client.get(
            "/api/sso/oauth2/login",
            follow_redirects=False,
        )
        assert response.status_code == 307

    @patch("app.api.routes.sso.sso_config")
    def test_oauth2_login_not_enabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test OAuth2 login when disabled."""
        mock_config.oauth2.enabled = False

        response = client.get("/api/sso/oauth2/login")
        assert response.status_code == 404

    @patch("app.api.routes.sso.sso_config")
    def test_oauth2_callback_not_enabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test OAuth2 callback when disabled."""
        mock_config.oauth2.enabled = False

        response = client.get("/api/sso/oauth2/callback?code=abc&state=xyz")
        assert response.status_code == 404

    @patch("app.api.routes.sso._sso_sessions", {})
    @patch("app.api.routes.sso.sso_config")
    def test_oauth2_callback_invalid_state(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test OAuth2 callback with invalid state."""
        mock_config.oauth2.enabled = True

        response = client.get("/api/sso/oauth2/callback?code=abc&state=invalid")
        assert response.status_code == 400
        assert "Invalid state" in response.json()["detail"]

    # ========================================================================
    # Provider Listing Tests
    # ========================================================================

    @patch("app.api.routes.sso.sso_config")
    def test_list_providers_both_enabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test listing providers when both enabled."""
        mock_config.saml.enabled = True
        mock_config.oauth2.enabled = True
        mock_config.oauth2.provider_name = "Okta"
        mock_config.enabled = True
        mock_config.allow_local_fallback = True

        response = client.get("/api/sso/providers")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert data["sso_enabled"] is True
        assert len(data["providers"]) == 2

    @patch("app.api.routes.sso.sso_config")
    def test_list_providers_saml_only(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test listing providers with SAML only."""
        mock_config.saml.enabled = True
        mock_config.oauth2.enabled = False
        mock_config.enabled = True
        mock_config.allow_local_fallback = True

        response = client.get("/api/sso/providers")
        assert response.status_code == 200

        data = response.json()
        assert len(data["providers"]) == 1
        assert data["providers"][0]["type"] == "saml"

    @patch("app.api.routes.sso.sso_config")
    def test_list_providers_oauth2_only(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test listing providers with OAuth2 only."""
        mock_config.saml.enabled = False
        mock_config.oauth2.enabled = True
        mock_config.oauth2.provider_name = "Azure AD"
        mock_config.enabled = True
        mock_config.allow_local_fallback = True

        response = client.get("/api/sso/providers")
        assert response.status_code == 200

        data = response.json()
        assert len(data["providers"]) == 1
        assert data["providers"][0]["type"] == "oauth2"

    @patch("app.api.routes.sso.sso_config")
    def test_list_providers_none_enabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test listing providers when none enabled."""
        mock_config.saml.enabled = False
        mock_config.oauth2.enabled = False
        mock_config.enabled = False
        mock_config.allow_local_fallback = True

        response = client.get("/api/sso/providers")
        assert response.status_code == 200

        data = response.json()
        assert data["providers"] == []
        assert data["sso_enabled"] is False

    # ========================================================================
    # Status Tests
    # ========================================================================

    @patch("app.api.routes.sso.sso_config")
    def test_sso_status_full_config(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SSO status with full configuration."""
        mock_config.enabled = True
        mock_config.get_active_providers.return_value = ["saml", "oauth2"]
        mock_config.auto_provision_users = True
        mock_config.allow_local_fallback = True
        mock_config.default_role = "resident"
        mock_config.saml.enabled = True
        mock_config.oauth2.enabled = True

        response = client.get("/api/sso/status")
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is True
        assert data["saml_enabled"] is True
        assert data["oauth2_enabled"] is True
        assert data["auto_provision_users"] is True
        assert data["default_role"] == "resident"

    @patch("app.api.routes.sso.sso_config")
    def test_sso_status_disabled(
        self,
        mock_config: MagicMock,
        client: TestClient,
    ):
        """Test SSO status when disabled."""
        mock_config.enabled = False
        mock_config.get_active_providers.return_value = []
        mock_config.auto_provision_users = False
        mock_config.allow_local_fallback = True
        mock_config.default_role = "resident"
        mock_config.saml.enabled = False
        mock_config.oauth2.enabled = False

        response = client.get("/api/sso/status")
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is False

    # ========================================================================
    # User Provisioning Tests
    # ========================================================================

    @patch("app.api.routes.sso.sso_config")
    def test_get_or_create_user_existing(
        self,
        mock_config: MagicMock,
        db_session: MagicMock,
    ):
        """Test get_or_create_user with existing user."""
        from app.api.routes.sso import get_or_create_user

        mock_user = MagicMock()
        mock_user.email = "existing@example.com"
        db_session.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_or_create_user(
            db_session,
            {"email": "existing@example.com", "username": "existing"},
            "saml",
        )
        assert result == mock_user

    @patch("app.api.routes.sso.sso_config")
    def test_get_or_create_user_missing_email(
        self,
        mock_config: MagicMock,
        db_session: MagicMock,
    ):
        """Test get_or_create_user without email raises error."""
        from fastapi import HTTPException

        from app.api.routes.sso import get_or_create_user

        with pytest.raises(HTTPException) as exc_info:
            get_or_create_user(
                db_session,
                {"username": "nomail"},
                "saml",
            )
        assert exc_info.value.status_code == 400
        assert "Email is required" in str(exc_info.value.detail)

    @patch("app.api.routes.sso.sso_config")
    def test_get_or_create_user_auto_provision_disabled(
        self,
        mock_config: MagicMock,
        db_session: MagicMock,
    ):
        """Test user creation when auto-provision disabled."""
        from fastapi import HTTPException

        from app.api.routes.sso import get_or_create_user

        mock_config.auto_provision_users = False
        db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_create_user(
                db_session,
                {"email": "new@example.com"},
                "oauth2",
            )
        assert exc_info.value.status_code == 403
        assert "auto-provisioning is disabled" in str(exc_info.value.detail)
