"""SSO response schemas."""

from pydantic import BaseModel


class SSOProvider(BaseModel):
    """SSO provider configuration."""

    type: str
    name: str
    login_url: str
    metadata_url: str | None = None


class ProvidersResponse(BaseModel):
    """Response for list of available SSO providers."""

    providers: list[SSOProvider]
    sso_enabled: bool
    local_auth_enabled: bool


class SSOStatusResponse(BaseModel):
    """Response for SSO configuration status."""

    enabled: bool
    active_providers: list[str]
    auto_provision_users: bool
    allow_local_fallback: bool
    default_role: str
    saml_enabled: bool
    oauth2_enabled: bool
