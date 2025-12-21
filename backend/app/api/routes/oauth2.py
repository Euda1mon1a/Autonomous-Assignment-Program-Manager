"""OAuth2 PKCE API routes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.oauth2_pkce import (
    create_authorization_code,
    exchange_code_for_token,
    introspect_token,
    register_client,
    revoke_token,
)
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.oauth2 import (
    AuthorizationRequest,
    AuthorizationResponse,
    OAuth2ClientCreate,
    OAuth2ClientResponse,
    TokenIntrospectionRequest,
    TokenIntrospectionResponse,
    TokenRequest,
    TokenResponse,
)

router = APIRouter()


@router.post("/authorize", response_model=AuthorizationResponse)
async def authorize(
    request: AuthorizationRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    """
    OAuth2 authorization endpoint with PKCE.

    Requires user to be authenticated. Creates an authorization code that
    can be exchanged for an access token.

    Flow:
    1. User authenticates (session or login)
    2. User authorizes the client application
    3. Server creates authorization code with PKCE challenge
    4. Client receives code and can exchange it for access token

    Args:
        request: Authorization request with PKCE code challenge
        current_user: Authenticated user (from session/JWT)
        db: Database session

    Returns:
        AuthorizationResponse with authorization code and state

    Raises:
        HTTPException: If validation fails
    """
    return await create_authorization_code(db, request, current_user)


@router.post("/token", response_model=TokenResponse)
async def token(
    request: TokenRequest,
    db: Session = Depends(get_db),
):
    """
    OAuth2 token endpoint - exchange authorization code for access token.

    This endpoint validates the authorization code and PKCE code verifier,
    then issues an access token.

    Security:
    - Validates code verifier matches code challenge (PKCE)
    - Single-use authorization codes (prevent replay)
    - Time-limited codes (10 minutes)
    - Redirect URI validation

    Args:
        request: Token request with authorization code and code verifier
        db: Database session

    Returns:
        TokenResponse with access token

    Raises:
        HTTPException: If validation fails
    """
    return await exchange_code_for_token(db, request)


@router.post("/introspect", response_model=TokenIntrospectionResponse)
async def token_introspection(
    request: TokenIntrospectionRequest,
    db: Session = Depends(get_db),
):
    """
    Token introspection endpoint (RFC 7662).

    Allows clients to check if an access token is valid and retrieve
    metadata about the token.

    Args:
        request: Introspection request with token
        db: Database session

    Returns:
        TokenIntrospectionResponse with token metadata
    """
    return await introspect_token(db, request.token)


@router.post("/revoke")
async def revoke(
    token: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    """
    Token revocation endpoint.

    Allows users to revoke their own access tokens by adding them
    to the blacklist.

    Args:
        token: The access token to revoke
        current_user: Authenticated user
        db: Database session

    Returns:
        Success message
    """
    await revoke_token(db, token, current_user.id)
    return {"message": "Token revoked successfully"}


@router.post("/clients", response_model=OAuth2ClientResponse)
async def create_client(
    request: OAuth2ClientCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
):
    """
    Register a new OAuth2 public client.

    Only admin users can register new clients.

    Args:
        request: Client registration request
        current_user: Authenticated admin user
        db: Database session

    Returns:
        OAuth2ClientResponse with client details including client_id

    Raises:
        HTTPException: If user is not admin
    """
    # Only admins can register clients
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    client = await register_client(
        db,
        client_name=request.client_name,
        redirect_uris=request.redirect_uris,
        client_uri=str(request.client_uri) if request.client_uri else None,
        scope=request.scope,
    )

    return OAuth2ClientResponse.model_validate(client)
