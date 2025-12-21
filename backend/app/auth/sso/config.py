"""
SSO configuration for SAML and OAuth2 providers.

Configuration settings for enterprise SSO integration including
SAML 2.0 Service Provider settings and OAuth2/OIDC provider settings.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator


class SAMLConfig(BaseModel):
    """
    SAML 2.0 Service Provider configuration.

    Attributes:
        enabled: Whether SAML authentication is enabled
        entity_id: Service Provider (SP) entity ID
        acs_url: Assertion Consumer Service URL (callback URL)
        slo_url: Single Logout Service URL
        idp_entity_id: Identity Provider (IdP) entity ID
        idp_sso_url: IdP Single Sign-On URL
        idp_slo_url: IdP Single Logout URL
        idp_x509_cert: IdP X.509 certificate for signature verification
        sp_x509_cert: SP X.509 certificate (optional)
        sp_private_key: SP private key for signing requests (optional)
        name_id_format: SAML NameID format
        attribute_map: Mapping of SAML attributes to user fields
        want_assertions_signed: Require signed assertions
        want_response_signed: Require signed responses
        authn_requests_signed: Sign authentication requests
        logout_requests_signed: Sign logout requests
    """

    enabled: bool = False
    entity_id: str = Field(default="", description="SP entity ID")
    acs_url: str = Field(default="", description="Assertion Consumer Service URL")
    slo_url: str = Field(default="", description="Single Logout Service URL")

    # Identity Provider settings
    idp_entity_id: str = Field(default="", description="IdP entity ID")
    idp_sso_url: str = Field(default="", description="IdP SSO URL")
    idp_slo_url: str = Field(default="", description="IdP SLO URL")
    idp_x509_cert: str = Field(default="", description="IdP certificate")

    # Service Provider certificates (optional, for signing)
    sp_x509_cert: Optional[str] = Field(default=None, description="SP certificate")
    sp_private_key: Optional[str] = Field(default=None, description="SP private key")

    # SAML settings
    name_id_format: str = Field(
        default="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        description="NameID format",
    )

    # Attribute mapping (SAML attribute -> user field)
    attribute_map: Dict[str, str] = Field(
        default={
            "email": "email",
            "username": "username",
            "firstName": "first_name",
            "lastName": "last_name",
            "role": "role",
        },
        description="SAML attribute to user field mapping",
    )

    # Security settings
    want_assertions_signed: bool = Field(
        default=True, description="Require signed assertions"
    )
    want_response_signed: bool = Field(
        default=True, description="Require signed responses"
    )
    authn_requests_signed: bool = Field(
        default=False, description="Sign authentication requests"
    )
    logout_requests_signed: bool = Field(
        default=False, description="Sign logout requests"
    )

    @field_validator("acs_url", "slo_url", "idp_sso_url", "idp_slo_url")
    @classmethod
    def validate_url(cls, v: str, info) -> str:
        """Validate URL fields when SAML is enabled."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError(f"{info.field_name} must be a valid HTTP(S) URL")
        return v


class OAuth2Config(BaseModel):
    """
    OAuth2/OpenID Connect provider configuration.

    Attributes:
        enabled: Whether OAuth2 authentication is enabled
        provider_name: Provider display name (e.g., "Google", "Azure AD")
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        authorization_endpoint: Authorization endpoint URL
        token_endpoint: Token endpoint URL
        userinfo_endpoint: UserInfo endpoint URL
        jwks_uri: JSON Web Key Set URI for token validation
        issuer: Expected issuer claim in ID tokens
        scope: OAuth2 scopes to request
        redirect_uri: OAuth2 callback/redirect URI
        attribute_map: Mapping of OAuth2 claims to user fields
        require_email_verified: Require verified email claim
    """

    enabled: bool = False
    provider_name: str = Field(default="OAuth2", description="Provider display name")

    # OAuth2 client credentials
    client_id: str = Field(default="", description="OAuth2 client ID")
    client_secret: str = Field(default="", description="OAuth2 client secret")

    # OAuth2/OIDC endpoints
    authorization_endpoint: str = Field(
        default="", description="Authorization endpoint"
    )
    token_endpoint: str = Field(default="", description="Token endpoint")
    userinfo_endpoint: str = Field(default="", description="UserInfo endpoint")
    jwks_uri: str = Field(default="", description="JWKS URI for token validation")
    issuer: str = Field(default="", description="Expected token issuer")

    # OAuth2 settings
    scope: str = Field(
        default="openid profile email", description="OAuth2 scopes"
    )
    redirect_uri: str = Field(default="", description="OAuth2 redirect URI")

    # Attribute mapping (OAuth2 claim -> user field)
    attribute_map: Dict[str, str] = Field(
        default={
            "email": "email",
            "preferred_username": "username",
            "name": "full_name",
            "given_name": "first_name",
            "family_name": "last_name",
            "role": "role",
        },
        description="OAuth2 claim to user field mapping",
    )

    # Security settings
    require_email_verified: bool = Field(
        default=True, description="Require verified email"
    )

    @field_validator(
        "authorization_endpoint",
        "token_endpoint",
        "userinfo_endpoint",
        "jwks_uri",
        "redirect_uri",
    )
    @classmethod
    def validate_url(cls, v: str, info) -> str:
        """Validate URL fields when OAuth2 is enabled."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError(f"{info.field_name} must be a valid HTTP(S) URL")
        return v


class SSOConfig(BaseModel):
    """
    Master SSO configuration container.

    Attributes:
        enabled: Whether SSO is enabled globally
        allow_local_fallback: Allow local username/password auth as fallback
        auto_provision_users: Enable Just-in-Time (JIT) user provisioning
        default_role: Default role for auto-provisioned users
        saml: SAML configuration
        oauth2: OAuth2 configuration
    """

    enabled: bool = Field(
        default=False, description="Enable SSO authentication globally"
    )
    allow_local_fallback: bool = Field(
        default=True, description="Allow local auth as fallback"
    )
    auto_provision_users: bool = Field(
        default=True, description="Enable JIT user provisioning"
    )
    default_role: str = Field(
        default="coordinator", description="Default role for new users"
    )

    # Provider configurations
    saml: SAMLConfig = Field(default_factory=SAMLConfig)
    oauth2: OAuth2Config = Field(default_factory=OAuth2Config)

    @property
    def has_active_provider(self) -> bool:
        """Check if any SSO provider is enabled."""
        return self.enabled and (self.saml.enabled or self.oauth2.enabled)

    def get_active_providers(self) -> list[str]:
        """Get list of active provider names."""
        providers = []
        if self.enabled:
            if self.saml.enabled:
                providers.append("saml")
            if self.oauth2.enabled:
                providers.append("oauth2")
        return providers


def load_sso_config() -> SSOConfig:
    """
    Load SSO configuration from environment variables.

    Environment variables should follow this pattern:
    - SSO_ENABLED=true/false
    - SSO_SAML_ENABLED=true/false
    - SSO_SAML_ENTITY_ID=...
    - SSO_OAUTH2_ENABLED=true/false
    - SSO_OAUTH2_CLIENT_ID=...
    etc.

    Returns:
        SSOConfig: Configured SSO settings
    """
    import os

    def get_bool(key: str, default: bool = False) -> bool:
        """Get boolean from environment."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def get_dict(key: str, default: Dict[str, str]) -> Dict[str, str]:
        """Get dictionary from environment (JSON format)."""
        import json

        value = os.getenv(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return default

    # Load main SSO config
    sso_config = SSOConfig(
        enabled=get_bool("SSO_ENABLED", False),
        allow_local_fallback=get_bool("SSO_ALLOW_LOCAL_FALLBACK", True),
        auto_provision_users=get_bool("SSO_AUTO_PROVISION_USERS", True),
        default_role=os.getenv("SSO_DEFAULT_ROLE", "coordinator"),
    )

    # Load SAML config
    sso_config.saml = SAMLConfig(
        enabled=get_bool("SSO_SAML_ENABLED", False),
        entity_id=os.getenv("SSO_SAML_ENTITY_ID", ""),
        acs_url=os.getenv("SSO_SAML_ACS_URL", ""),
        slo_url=os.getenv("SSO_SAML_SLO_URL", ""),
        idp_entity_id=os.getenv("SSO_SAML_IDP_ENTITY_ID", ""),
        idp_sso_url=os.getenv("SSO_SAML_IDP_SSO_URL", ""),
        idp_slo_url=os.getenv("SSO_SAML_IDP_SLO_URL", ""),
        idp_x509_cert=os.getenv("SSO_SAML_IDP_X509_CERT", ""),
        sp_x509_cert=os.getenv("SSO_SAML_SP_X509_CERT"),
        sp_private_key=os.getenv("SSO_SAML_SP_PRIVATE_KEY"),
        name_id_format=os.getenv(
            "SSO_SAML_NAME_ID_FORMAT",
            "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
        ),
        attribute_map=get_dict(
            "SSO_SAML_ATTRIBUTE_MAP",
            {
                "email": "email",
                "username": "username",
                "firstName": "first_name",
                "lastName": "last_name",
                "role": "role",
            },
        ),
        want_assertions_signed=get_bool("SSO_SAML_WANT_ASSERTIONS_SIGNED", True),
        want_response_signed=get_bool("SSO_SAML_WANT_RESPONSE_SIGNED", True),
        authn_requests_signed=get_bool("SSO_SAML_AUTHN_REQUESTS_SIGNED", False),
        logout_requests_signed=get_bool("SSO_SAML_LOGOUT_REQUESTS_SIGNED", False),
    )

    # Load OAuth2 config
    sso_config.oauth2 = OAuth2Config(
        enabled=get_bool("SSO_OAUTH2_ENABLED", False),
        provider_name=os.getenv("SSO_OAUTH2_PROVIDER_NAME", "OAuth2"),
        client_id=os.getenv("SSO_OAUTH2_CLIENT_ID", ""),
        client_secret=os.getenv("SSO_OAUTH2_CLIENT_SECRET", ""),
        authorization_endpoint=os.getenv("SSO_OAUTH2_AUTHORIZATION_ENDPOINT", ""),
        token_endpoint=os.getenv("SSO_OAUTH2_TOKEN_ENDPOINT", ""),
        userinfo_endpoint=os.getenv("SSO_OAUTH2_USERINFO_ENDPOINT", ""),
        jwks_uri=os.getenv("SSO_OAUTH2_JWKS_URI", ""),
        issuer=os.getenv("SSO_OAUTH2_ISSUER", ""),
        scope=os.getenv("SSO_OAUTH2_SCOPE", "openid profile email"),
        redirect_uri=os.getenv("SSO_OAUTH2_REDIRECT_URI", ""),
        attribute_map=get_dict(
            "SSO_OAUTH2_ATTRIBUTE_MAP",
            {
                "email": "email",
                "preferred_username": "username",
                "name": "full_name",
                "given_name": "first_name",
                "family_name": "last_name",
                "role": "role",
            },
        ),
        require_email_verified=get_bool("SSO_OAUTH2_REQUIRE_EMAIL_VERIFIED", True),
    )

    return sso_config
