"""OAuth2 PKCE schemas for request/response validation."""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


class OAuth2ClientCreate(BaseModel):
    """Request to create a new OAuth2 client."""
    client_name: str = Field(..., min_length=1, max_length=255)
    client_uri: HttpUrl | None = None
    redirect_uris: list[str] = Field(..., min_items=1)
    scope: str | None = None

    @field_validator("redirect_uris")
    @classmethod
    def validate_redirect_uris(cls, v: list[str]) -> list[str]:
        """Validate that all redirect URIs are valid."""
        if not v:
            raise ValueError("At least one redirect URI is required")
        for uri in v:
            if not uri.startswith(("http://", "https://", "app://")):
                raise ValueError(f"Invalid redirect URI: {uri}")
        return v


class OAuth2ClientResponse(BaseModel):
    """OAuth2 client response."""
    id: UUID
    client_id: str
    client_name: str
    client_uri: str | None
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    scope: str | None
    is_public: bool
    is_active: bool

    class Config:
        from_attributes = True


class PKCECodeChallenge(BaseModel):
    """PKCE code challenge for authorization request."""
    code_challenge: str = Field(..., min_length=43, max_length=128)
    code_challenge_method: Literal["S256", "plain"] = "S256"

    @field_validator("code_challenge")
    @classmethod
    def validate_code_challenge(cls, v: str) -> str:
        """Validate code challenge format."""
        # Base64url encoded SHA256 hash is 43 characters
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Code challenge must be base64url encoded")
        return v


class AuthorizationRequest(BaseModel):
    """OAuth2 authorization request with PKCE."""
    response_type: Literal["code"] = "code"
    client_id: str = Field(..., min_length=1, max_length=255)
    redirect_uri: str = Field(..., min_length=1, max_length=512)
    scope: str | None = None
    state: str | None = Field(None, max_length=255)
    nonce: str | None = Field(None, max_length=255)
    code_challenge: str = Field(..., min_length=43, max_length=128)
    code_challenge_method: Literal["S256", "plain"] = "S256"


class AuthorizationResponse(BaseModel):
    """OAuth2 authorization response."""
    code: str
    state: str | None = None


class TokenRequest(BaseModel):
    """OAuth2 token exchange request with PKCE."""
    grant_type: Literal["authorization_code"] = "authorization_code"
    code: str = Field(..., min_length=1, max_length=255)
    redirect_uri: str = Field(..., min_length=1, max_length=512)
    client_id: str = Field(..., min_length=1, max_length=255)
    code_verifier: str = Field(..., min_length=43, max_length=128)

    @field_validator("code_verifier")
    @classmethod
    def validate_code_verifier(cls, v: str) -> str:
        """Validate code verifier format."""
        # RFC 7636: code verifier is 43-128 characters, unreserved chars only
        if not v.replace("-", "").replace("_", "").replace(".", "").replace("~", "").isalnum():
            raise ValueError("Code verifier must contain only unreserved characters")
        return v


class TokenResponse(BaseModel):
    """OAuth2 token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str | None = None
    refresh_token: str | None = None


class TokenIntrospectionRequest(BaseModel):
    """Token introspection request."""
    token: str = Field(..., min_length=1)
    token_type_hint: Literal["access_token", "refresh_token"] | None = None


class TokenIntrospectionResponse(BaseModel):
    """Token introspection response (RFC 7662)."""
    active: bool
    scope: str | None = None
    client_id: str | None = None
    username: str | None = None
    token_type: str | None = None
    exp: int | None = None
    iat: int | None = None
    sub: str | None = None
    aud: str | None = None
    iss: str | None = None
    jti: str | None = None


class OAuth2Error(BaseModel):
    """OAuth2 error response."""
    error: str
    error_description: str | None = None
    error_uri: str | None = None
    state: str | None = None
