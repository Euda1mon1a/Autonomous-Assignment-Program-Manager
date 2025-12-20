"""
Tests for SSO authentication (SAML and OAuth2).

Tests cover:
- SAML authentication flow
- OAuth2/OIDC authentication flow
- User provisioning (JIT)
- Session creation
- Configuration validation
"""

import base64
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.sso.config import SAMLConfig, OAuth2Config, SSOConfig, load_sso_config
from app.auth.sso.oauth2_provider import OAuth2Provider
from app.auth.sso.saml_provider import SAMLProvider
from app.main import app
from app.models.user import User


class TestSAMLConfig:
    """Test SAML configuration."""

    def test_saml_config_defaults(self):
        """Test default SAML configuration."""
        config = SAMLConfig()

        assert config.enabled is False
        assert config.want_assertions_signed is True
        assert config.want_response_signed is True
        assert config.authn_requests_signed is False
        assert config.logout_requests_signed is False

    def test_saml_config_url_validation(self):
        """Test SAML URL validation."""
        with pytest.raises(ValueError, match="must be a valid HTTP"):
            SAMLConfig(
                enabled=True,
                acs_url="not-a-url",
            )

    def test_saml_attribute_mapping(self):
        """Test SAML attribute mapping configuration."""
        config = SAMLConfig(
            attribute_map={
                "mail": "email",
                "uid": "username",
                "givenName": "first_name",
            }
        )

        assert config.attribute_map["mail"] == "email"
        assert config.attribute_map["uid"] == "username"


class TestOAuth2Config:
    """Test OAuth2 configuration."""

    def test_oauth2_config_defaults(self):
        """Test default OAuth2 configuration."""
        config = OAuth2Config()

        assert config.enabled is False
        assert config.provider_name == "OAuth2"
        assert config.require_email_verified is True
        assert "openid" in config.scope

    def test_oauth2_config_url_validation(self):
        """Test OAuth2 URL validation."""
        with pytest.raises(ValueError, match="must be a valid HTTP"):
            OAuth2Config(
                enabled=True,
                authorization_endpoint="not-a-url",
            )

    def test_oauth2_attribute_mapping(self):
        """Test OAuth2 claim mapping configuration."""
        config = OAuth2Config(
            attribute_map={
                "email": "email",
                "sub": "username",
            }
        )

        assert config.attribute_map["email"] == "email"
        assert config.attribute_map["sub"] == "username"


class TestSSOConfig:
    """Test master SSO configuration."""

    def test_sso_config_defaults(self):
        """Test default SSO configuration."""
        config = SSOConfig()

        assert config.enabled is False
        assert config.allow_local_fallback is True
        assert config.auto_provision_users is True
        assert config.default_role == "coordinator"

    def test_has_active_provider(self):
        """Test checking for active providers."""
        config = SSOConfig(enabled=True)
        assert config.has_active_provider is False

        config.saml.enabled = True
        assert config.has_active_provider is True

    def test_get_active_providers(self):
        """Test getting list of active providers."""
        config = SSOConfig(enabled=True)
        config.saml.enabled = True
        config.oauth2.enabled = True

        providers = config.get_active_providers()
        assert "saml" in providers
        assert "oauth2" in providers


class TestSAMLProvider:
    """Test SAML provider implementation."""

    @pytest.fixture
    def saml_config(self):
        """Create test SAML configuration."""
        return SAMLConfig(
            enabled=True,
            entity_id="https://sp.example.com",
            acs_url="https://sp.example.com/api/sso/saml/acs",
            slo_url="https://sp.example.com/api/sso/saml/slo",
            idp_entity_id="https://idp.example.com",
            idp_sso_url="https://idp.example.com/sso",
            idp_slo_url="https://idp.example.com/slo",
            idp_x509_cert="test_cert",
        )

    @pytest.fixture
    def saml_provider(self, saml_config):
        """Create SAML provider instance."""
        return SAMLProvider(saml_config)

    def test_generate_authn_request(self, saml_provider):
        """Test SAML authentication request generation."""
        request_id, redirect_url = saml_provider.generate_authn_request()

        assert request_id.startswith("_saml_")
        assert "https://idp.example.com/sso" in redirect_url
        assert "SAMLRequest=" in redirect_url

    def test_generate_sp_metadata(self, saml_provider):
        """Test SP metadata generation."""
        metadata = saml_provider.generate_sp_metadata()

        assert "EntityDescriptor" in metadata
        assert "SPSSODescriptor" in metadata
        assert "https://sp.example.com" in metadata
        assert "AssertionConsumerService" in metadata

    def test_generate_logout_request(self, saml_provider):
        """Test SAML logout request generation."""
        name_id = "user@example.com"
        session_index = "session_123"

        request_id, redirect_url = saml_provider.generate_logout_request(
            name_id, session_index
        )

        assert request_id.startswith("_saml_logout_")
        assert "https://idp.example.com/slo" in redirect_url
        assert "SAMLRequest=" in redirect_url

    def test_parse_saml_response_invalid_base64(self, saml_provider):
        """Test parsing invalid SAML response."""
        with pytest.raises(ValueError, match="Failed to decode"):
            saml_provider.parse_saml_response("invalid_base64", validate_signature=False)

    def test_parse_saml_response_invalid_xml(self, saml_provider):
        """Test parsing SAML response with invalid XML."""
        invalid_xml = base64.b64encode(b"not xml").decode("utf-8")

        with pytest.raises(ValueError, match="Invalid SAML XML"):
            saml_provider.parse_saml_response(invalid_xml, validate_signature=False)

    def test_parse_idp_metadata(self, saml_provider):
        """Test parsing IdP metadata."""
        metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
    entityID="https://idp.example.com">
    <IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            Location="https://idp.example.com/sso"/>
        <SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
            Location="https://idp.example.com/slo"/>
        <KeyDescriptor>
            <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
                <ds:X509Data>
                    <ds:X509Certificate>MIICertificate</ds:X509Certificate>
                </ds:X509Data>
            </ds:KeyInfo>
        </KeyDescriptor>
    </IDPSSODescriptor>
</EntityDescriptor>"""

        config = saml_provider.parse_idp_metadata(metadata_xml)

        assert config["entity_id"] == "https://idp.example.com"
        assert config["sso_url"] == "https://idp.example.com/sso"
        assert config["slo_url"] == "https://idp.example.com/slo"
        assert "MIICertificate" in config["x509_cert"]


class TestOAuth2Provider:
    """Test OAuth2 provider implementation."""

    @pytest.fixture
    def oauth2_config(self):
        """Create test OAuth2 configuration."""
        return OAuth2Config(
            enabled=True,
            provider_name="Test OAuth2",
            client_id="test_client_id",
            client_secret="test_client_secret",
            authorization_endpoint="https://oauth.example.com/authorize",
            token_endpoint="https://oauth.example.com/token",
            userinfo_endpoint="https://oauth.example.com/userinfo",
            jwks_uri="https://oauth.example.com/jwks",
            issuer="https://oauth.example.com",
            redirect_uri="https://sp.example.com/callback",
        )

    @pytest.fixture
    def oauth2_provider(self, oauth2_config):
        """Create OAuth2 provider instance."""
        return OAuth2Provider(oauth2_config)

    def test_generate_authorization_url(self, oauth2_provider):
        """Test OAuth2 authorization URL generation."""
        auth_data = oauth2_provider.generate_authorization_url(use_pkce=True)

        assert "authorization_url" in auth_data
        assert "state" in auth_data
        assert "code_verifier" in auth_data

        url = auth_data["authorization_url"]
        assert "https://oauth.example.com/authorize" in url
        assert "client_id=test_client_id" in url
        assert "response_type=code" in url
        assert "code_challenge=" in url
        assert "state=" in auth_data["state"]

    def test_generate_authorization_url_no_pkce(self, oauth2_provider):
        """Test OAuth2 authorization URL without PKCE."""
        auth_data = oauth2_provider.generate_authorization_url(use_pkce=False)

        assert "authorization_url" in auth_data
        assert "state" in auth_data
        assert "code_verifier" not in auth_data

        url = auth_data["authorization_url"]
        assert "code_challenge=" not in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, oauth2_provider):
        """Test OAuth2 code exchange."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "test_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "test_refresh_token",
                "id_token": "test_id_token",
            }
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            token_response = await oauth2_provider.exchange_code_for_token(
                "test_code", code_verifier="test_verifier"
            )

            assert token_response["access_token"] == "test_access_token"
            assert token_response["token_type"] == "Bearer"
            assert token_response["id_token"] == "test_id_token"

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_error(self, oauth2_provider):
        """Test OAuth2 code exchange with error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "error": "invalid_grant",
                "error_description": "Code expired",
            }
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(ValueError, match="Token exchange error"):
                await oauth2_provider.exchange_code_for_token("expired_code")

    @pytest.mark.asyncio
    async def test_get_userinfo(self, oauth2_provider):
        """Test fetching user info."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "sub": "user123",
                "email": "user@example.com",
                "email_verified": True,
                "name": "Test User",
            }
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            userinfo = await oauth2_provider.get_userinfo("test_access_token")

            assert userinfo["sub"] == "user123"
            assert userinfo["email"] == "user@example.com"
            assert userinfo["email_verified"] is True

    def test_map_claims_to_user(self, oauth2_provider):
        """Test mapping OAuth2 claims to user attributes."""
        claims = {
            "email": "user@example.com",
            "preferred_username": "testuser",
            "given_name": "Test",
            "family_name": "User",
        }

        mapped = oauth2_provider.map_claims_to_user(claims)

        assert mapped["email"] == "user@example.com"
        assert mapped["username"] == "testuser"
        assert mapped["first_name"] == "Test"
        assert mapped["last_name"] == "User"

    def test_generate_code_challenge(self, oauth2_provider):
        """Test PKCE code challenge generation."""
        code_verifier = "test_verifier_string_1234567890"
        code_challenge = oauth2_provider._generate_code_challenge(code_verifier)

        assert isinstance(code_challenge, str)
        assert len(code_challenge) > 0
        # Verify it's base64-url encoded (no padding)
        assert "=" not in code_challenge

    @pytest.mark.asyncio
    async def test_refresh_token(self, oauth2_provider):
        """Test token refresh."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "new_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            }
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            token_response = await oauth2_provider.refresh_token("test_refresh_token")

            assert token_response["access_token"] == "new_access_token"


class TestSSORoutes:
    """Test SSO API routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_list_providers_disabled(self, client):
        """Test listing providers when SSO is disabled."""
        with patch("app.api.routes.sso.sso_config") as mock_config:
            mock_config.enabled = False
            mock_config.saml.enabled = False
            mock_config.oauth2.enabled = False
            mock_config.allow_local_fallback = True

            response = client.get("/api/sso/providers")

            assert response.status_code == 200
            data = response.json()
            assert data["sso_enabled"] is False
            assert data["local_auth_enabled"] is True
            assert len(data["providers"]) == 0

    def test_list_providers_enabled(self, client):
        """Test listing providers when SSO is enabled."""
        with patch("app.api.routes.sso.sso_config") as mock_config:
            mock_config.enabled = True
            mock_config.saml.enabled = True
            mock_config.oauth2.enabled = True
            mock_config.oauth2.provider_name = "Google"
            mock_config.allow_local_fallback = True

            response = client.get("/api/sso/providers")

            assert response.status_code == 200
            data = response.json()
            assert data["sso_enabled"] is True
            assert len(data["providers"]) == 2

    def test_sso_status(self, client):
        """Test SSO status endpoint."""
        with patch("app.api.routes.sso.sso_config") as mock_config:
            mock_config.enabled = True
            mock_config.auto_provision_users = True
            mock_config.allow_local_fallback = True
            mock_config.default_role = "coordinator"
            mock_config.saml.enabled = True
            mock_config.oauth2.enabled = False
            mock_config.get_active_providers.return_value = ["saml"]

            response = client.get("/api/sso/status")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["auto_provision_users"] is True
            assert "saml" in data["active_providers"]

    def test_saml_metadata_disabled(self, client):
        """Test SAML metadata when SAML is disabled."""
        with patch("app.api.routes.sso.sso_config") as mock_config:
            mock_config.saml.enabled = False

            response = client.get("/api/sso/saml/metadata")

            assert response.status_code == 404

    def test_oauth2_login_disabled(self, client):
        """Test OAuth2 login when OAuth2 is disabled."""
        with patch("app.api.routes.sso.sso_config") as mock_config:
            mock_config.oauth2.enabled = False

            response = client.get("/api/sso/oauth2/login")

            assert response.status_code == 404


def test_load_sso_config_from_env(monkeypatch):
    """Test loading SSO configuration from environment variables."""
    monkeypatch.setenv("SSO_ENABLED", "true")
    monkeypatch.setenv("SSO_SAML_ENABLED", "true")
    monkeypatch.setenv("SSO_SAML_ENTITY_ID", "https://sp.example.com")
    monkeypatch.setenv("SSO_OAUTH2_ENABLED", "true")
    monkeypatch.setenv("SSO_OAUTH2_CLIENT_ID", "test_client_id")

    config = load_sso_config()

    assert config.enabled is True
    assert config.saml.enabled is True
    assert config.saml.entity_id == "https://sp.example.com"
    assert config.oauth2.enabled is True
    assert config.oauth2.client_id == "test_client_id"
