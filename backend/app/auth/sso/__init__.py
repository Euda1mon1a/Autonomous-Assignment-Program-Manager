"""
Single Sign-On (SSO) authentication package.

Provides enterprise SSO authentication via:
- SAML 2.0 Service Provider (SP)
- OAuth2/OpenID Connect (OIDC)
"""

from app.auth.sso.config import SSOConfig, SAMLConfig, OAuth2Config
from app.auth.sso.saml_provider import SAMLProvider
from app.auth.sso.oauth2_provider import OAuth2Provider

__all__ = [
    "SSOConfig",
    "SAMLConfig",
    "OAuth2Config",
    "SAMLProvider",
    "OAuth2Provider",
]
