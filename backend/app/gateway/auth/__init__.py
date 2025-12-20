"""
Gateway authentication module.

Provides comprehensive authentication mechanisms for the API gateway including:
- API key validation and management
- OAuth2 client credentials flow
- JWT token validation
- Request signature verification (HMAC)
- IP whitelist/blacklist filtering
- Rate limiting per API key/client
- API key rotation support

Usage:
    from app.gateway.auth import (
        GatewayAuthenticator,
        APIKeyManager,
        OAuth2Manager,
        IPFilterManager,
        RequestSignatureValidator,
        require_api_key,
    )

    # In a FastAPI route
    @router.get("/protected")
    async def protected_route(
        api_key: APIKey = Depends(require_api_key),
        db: Session = Depends(get_db)
    ):
        # Route logic here
        pass

    # Or use the main authenticator
    authenticator = GatewayAuthenticator(db)
    validation = await authenticator.validate_request(
        request=request,
        api_key=api_key_from_header
    )
"""

from app.gateway.auth.gateway_auth import (
    APIKeyManager,
    GatewayAuthenticationError,
    GatewayAuthenticator,
    IPFilterManager,
    OAuth2Manager,
    RequestSignatureValidator,
    get_gateway_authenticator,
    require_api_key,
)

__all__ = [
    # Main classes
    "GatewayAuthenticator",
    "APIKeyManager",
    "OAuth2Manager",
    "IPFilterManager",
    "RequestSignatureValidator",
    # Dependencies
    "get_gateway_authenticator",
    "require_api_key",
    # Exceptions
    "GatewayAuthenticationError",
]
