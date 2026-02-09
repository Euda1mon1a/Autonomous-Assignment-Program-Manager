"""Tests for OAuth2 PKCE schemas (field_validators, Field bounds, Literals)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.oauth2 import (
    OAuth2ClientCreate,
    OAuth2ClientResponse,
    PKCECodeChallenge,
    AuthorizationRequest,
    AuthorizationResponse,
    TokenRequest,
    TokenResponse,
    TokenIntrospectionRequest,
    TokenIntrospectionResponse,
    OAuth2Error,
)


class TestOAuth2ClientCreate:
    def test_valid(self):
        r = OAuth2ClientCreate(
            client_name="My App",
            redirect_uris=["https://example.com/callback"],
        )
        assert r.client_name == "My App"
        assert r.client_uri is None
        assert r.scope is None

    # --- client_name min_length=1, max_length=255 ---

    def test_client_name_empty(self):
        with pytest.raises(ValidationError):
            OAuth2ClientCreate(client_name="", redirect_uris=["https://example.com/cb"])

    def test_client_name_too_long(self):
        with pytest.raises(ValidationError):
            OAuth2ClientCreate(
                client_name="x" * 256, redirect_uris=["https://example.com/cb"]
            )

    # --- redirect_uris field_validator ---

    def test_redirect_uris_invalid_scheme(self):
        with pytest.raises(ValidationError, match="Invalid redirect URI"):
            OAuth2ClientCreate(
                client_name="App", redirect_uris=["ftp://example.com/cb"]
            )

    def test_redirect_uris_app_scheme(self):
        r = OAuth2ClientCreate(
            client_name="App", redirect_uris=["app://my-app/callback"]
        )
        assert r.redirect_uris == ["app://my-app/callback"]

    def test_redirect_uris_multiple(self):
        r = OAuth2ClientCreate(
            client_name="App",
            redirect_uris=["https://a.com/cb", "http://localhost/cb"],
        )
        assert len(r.redirect_uris) == 2


class TestOAuth2ClientResponse:
    def test_valid(self):
        r = OAuth2ClientResponse(
            id=uuid4(),
            client_id="client-abc",
            client_name="My App",
            client_uri=None,
            redirect_uris=["https://example.com/cb"],
            grant_types=["authorization_code"],
            response_types=["code"],
            scope="read",
            is_public=True,
            is_active=True,
        )
        assert r.is_public is True


class TestPKCECodeChallenge:
    def _valid_challenge(self):
        # Base64url encoded SHA256 is 43 chars
        return "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"

    def test_valid(self):
        r = PKCECodeChallenge(code_challenge=self._valid_challenge())
        assert r.code_challenge_method == "S256"

    def test_plain_method(self):
        r = PKCECodeChallenge(
            code_challenge=self._valid_challenge(), code_challenge_method="plain"
        )
        assert r.code_challenge_method == "plain"

    # --- code_challenge min_length=43, max_length=128 ---

    def test_code_challenge_too_short(self):
        with pytest.raises(ValidationError):
            PKCECodeChallenge(code_challenge="short")

    def test_code_challenge_too_long(self):
        with pytest.raises(ValidationError):
            PKCECodeChallenge(code_challenge="A" * 129)

    # --- code_challenge field_validator ---

    def test_code_challenge_invalid_chars(self):
        # 43+ chars but with invalid characters
        with pytest.raises(ValidationError, match="base64url"):
            PKCECodeChallenge(code_challenge="!" * 43)


class TestAuthorizationRequest:
    def _valid_kwargs(self):
        return {
            "client_id": "client-abc",
            "redirect_uri": "https://example.com/callback",
            "code_challenge": "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
        }

    def test_valid(self):
        r = AuthorizationRequest(**self._valid_kwargs())
        assert r.response_type == "code"
        assert r.code_challenge_method == "S256"
        assert r.scope is None
        assert r.state is None
        assert r.nonce is None

    def test_with_state(self):
        kw = self._valid_kwargs()
        kw["state"] = "random-state"
        r = AuthorizationRequest(**kw)
        assert r.state == "random-state"

    # --- state max_length=255, nonce max_length=255 ---

    def test_state_too_long(self):
        kw = self._valid_kwargs()
        kw["state"] = "x" * 256
        with pytest.raises(ValidationError):
            AuthorizationRequest(**kw)

    def test_nonce_too_long(self):
        kw = self._valid_kwargs()
        kw["nonce"] = "x" * 256
        with pytest.raises(ValidationError):
            AuthorizationRequest(**kw)


class TestAuthorizationResponse:
    def test_valid(self):
        r = AuthorizationResponse(code="auth-code-123")
        assert r.state is None

    def test_with_state(self):
        r = AuthorizationResponse(code="auth-code-123", state="my-state")
        assert r.state == "my-state"


class TestTokenRequest:
    def _valid_kwargs(self):
        return {
            "code": "auth-code-123",
            "redirect_uri": "https://example.com/callback",
            "client_id": "client-abc",
            "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk",
        }

    def test_valid(self):
        r = TokenRequest(**self._valid_kwargs())
        assert r.grant_type == "authorization_code"

    # --- code_verifier min_length=43, max_length=128, field_validator ---

    def test_code_verifier_too_short(self):
        kw = self._valid_kwargs()
        kw["code_verifier"] = "short"
        with pytest.raises(ValidationError):
            TokenRequest(**kw)

    def test_code_verifier_invalid_chars(self):
        kw = self._valid_kwargs()
        kw["code_verifier"] = "!" * 43
        with pytest.raises(ValidationError, match="unreserved"):
            TokenRequest(**kw)


class TestTokenResponse:
    def test_valid(self):
        r = TokenResponse(access_token="eyJ...", expires_in=3600)
        assert r.token_type == "Bearer"
        assert r.scope is None
        assert r.refresh_token is None


class TestTokenIntrospectionRequest:
    def test_valid(self):
        r = TokenIntrospectionRequest(token="eyJ...")
        assert r.token_type_hint is None

    def test_with_hint(self):
        r = TokenIntrospectionRequest(token="eyJ...", token_type_hint="access_token")
        assert r.token_type_hint == "access_token"

    def test_token_empty(self):
        with pytest.raises(ValidationError):
            TokenIntrospectionRequest(token="")


class TestTokenIntrospectionResponse:
    def test_active(self):
        r = TokenIntrospectionResponse(active=True)
        assert r.scope is None
        assert r.client_id is None
        assert r.username is None
        assert r.exp is None
        assert r.iat is None
        assert r.sub is None
        assert r.aud is None
        assert r.iss is None
        assert r.jti is None

    def test_inactive(self):
        r = TokenIntrospectionResponse(active=False)
        assert r.active is False


class TestOAuth2Error:
    def test_valid(self):
        r = OAuth2Error(error="invalid_request")
        assert r.error_description is None
        assert r.error_uri is None
        assert r.state is None

    def test_full(self):
        r = OAuth2Error(
            error="access_denied",
            error_description="User denied access",
            state="my-state",
        )
        assert r.error_description == "User denied access"
