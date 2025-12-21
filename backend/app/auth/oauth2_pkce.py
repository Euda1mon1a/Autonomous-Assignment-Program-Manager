"""
OAuth2 PKCE (Proof Key for Code Exchange) implementation.

This module implements the OAuth2 Authorization Code Flow with PKCE extension
(RFC 7636) for public clients (mobile apps, SPAs). PKCE prevents authorization
code interception attacks without requiring a client secret.

Flow:
1. Client generates code_verifier (random string)
2. Client computes code_challenge = BASE64URL(SHA256(code_verifier))
3. Client requests authorization with code_challenge
4. Server returns authorization code
5. Client exchanges code + code_verifier for access token
6. Server validates code_verifier matches code_challenge
"""
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_token
from app.models.oauth2_authorization_code import OAuth2AuthorizationCode
from app.models.oauth2_client import PKCEClient
from app.models.user import User
from app.schemas.oauth2 import (
    AuthorizationRequest,
    AuthorizationResponse,
    OAuth2Error,
    TokenIntrospectionResponse,
    TokenRequest,
    TokenResponse,
)

settings = get_settings()

# Import observability metrics (optional - graceful degradation)
try:
    from app.core.observability import metrics as obs_metrics
except ImportError:
    obs_metrics = None


# PKCE Constants (RFC 7636)
CODE_VERIFIER_MIN_LENGTH = 43
CODE_VERIFIER_MAX_LENGTH = 128
CODE_CHALLENGE_METHOD_S256 = "S256"
CODE_CHALLENGE_METHOD_PLAIN = "plain"
AUTHORIZATION_CODE_EXPIRE_MINUTES = 10


def generate_code_verifier() -> str:
    """
    Generate a cryptographically random code verifier for PKCE.

    The code verifier is a random string of 43-128 characters using
    unreserved characters [A-Z], [a-z], [0-9], "-", ".", "_", "~".

    Returns:
        str: Base64url-encoded random string (43 characters)
    """
    # Generate 32 random bytes, encode as base64url (43 chars)
    random_bytes = secrets.token_bytes(32)
    code_verifier = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
    return code_verifier


def generate_code_challenge(code_verifier: str, method: str = CODE_CHALLENGE_METHOD_S256) -> str:
    """
    Generate a code challenge from a code verifier.

    Args:
        code_verifier: The code verifier string
        method: Challenge method - "S256" (SHA256) or "plain"

    Returns:
        str: Code challenge (base64url-encoded SHA256 hash for S256, or verifier for plain)

    Raises:
        ValueError: If method is not supported
    """
    if method == CODE_CHALLENGE_METHOD_S256:
        # SHA256 hash of the verifier, then base64url encode
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        return challenge
    elif method == CODE_CHALLENGE_METHOD_PLAIN:
        # Plain method: challenge = verifier (not recommended)
        return code_verifier
    else:
        raise ValueError(f"Unsupported code challenge method: {method}")


def verify_code_challenge(code_verifier: str, code_challenge: str, method: str) -> bool:
    """
    Verify that a code verifier matches a code challenge.

    Args:
        code_verifier: The code verifier to check
        code_challenge: The expected code challenge
        method: Challenge method used (S256 or plain)

    Returns:
        bool: True if verification succeeds, False otherwise
    """
    try:
        computed_challenge = generate_code_challenge(code_verifier, method)
        return secrets.compare_digest(computed_challenge, code_challenge)
    except Exception:
        return False


def generate_authorization_code() -> str:
    """
    Generate a cryptographically random authorization code.

    Returns:
        str: Base64url-encoded random string (32 characters)
    """
    # Generate 24 random bytes, encode as base64url (32 chars)
    random_bytes = secrets.token_bytes(24)
    auth_code = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
    return auth_code


def generate_state() -> str:
    """
    Generate a cryptographically random state parameter for CSRF protection.

    Returns:
        str: Base64url-encoded random string
    """
    return secrets.token_urlsafe(32)


async def validate_client(db: Session, client_id: str) -> PKCEClient:
    """
    Validate that a client exists and is active.

    Args:
        db: Database session
        client_id: Client identifier

    Returns:
        PKCEClient: The validated client

    Raises:
        HTTPException: If client is invalid or inactive
    """
    client = db.query(PKCEClient).filter(
        PKCEClient.client_id == client_id,
        PKCEClient.is_active == True  # noqa: E712
    ).first()

    if not client:
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_client")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return client


async def validate_redirect_uri(client: PKCEClient, redirect_uri: str) -> None:
    """
    Validate that a redirect URI is registered for the client.

    Args:
        client: The PKCE client
        redirect_uri: The redirect URI to validate

    Raises:
        HTTPException: If redirect URI is not registered
    """
    if not client.is_redirect_uri_allowed(redirect_uri):
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_redirect_uri")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect URI",
        )


async def create_authorization_code(
    db: Session,
    request: AuthorizationRequest,
    user: User,
) -> AuthorizationResponse:
    """
    Create an authorization code for the PKCE flow.

    Args:
        db: Database session
        request: Authorization request with PKCE parameters
        user: Authenticated user granting authorization

    Returns:
        AuthorizationResponse: Contains the authorization code

    Raises:
        HTTPException: If validation fails
    """
    # Validate client
    client = await validate_client(db, request.client_id)

    # Validate redirect URI
    await validate_redirect_uri(client, request.redirect_uri)

    # Validate code challenge method
    if request.code_challenge_method not in [CODE_CHALLENGE_METHOD_S256, CODE_CHALLENGE_METHOD_PLAIN]:
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported code challenge method. Use S256.",
        )

    # Generate authorization code
    code = generate_authorization_code()
    expires_at = datetime.utcnow() + timedelta(minutes=AUTHORIZATION_CODE_EXPIRE_MINUTES)

    # Store authorization code in database
    auth_code = OAuth2AuthorizationCode(
        code=code,
        client_id=request.client_id,
        user_id=user.id,
        redirect_uri=request.redirect_uri,
        scope=request.scope,
        code_challenge=request.code_challenge,
        code_challenge_method=request.code_challenge_method,
        state=request.state,
        nonce=request.nonce,
        is_used="false",
        expires_at=expires_at,
    )

    db.add(auth_code)
    db.commit()
    db.refresh(auth_code)

    if obs_metrics:
        obs_metrics.record_oauth2_authorization_granted(request.client_id)

    return AuthorizationResponse(
        code=code,
        state=request.state,
    )


async def exchange_code_for_token(
    db: Session,
    request: TokenRequest,
) -> TokenResponse:
    """
    Exchange an authorization code for an access token (with PKCE validation).

    Args:
        db: Database session
        request: Token request with authorization code and code verifier

    Returns:
        TokenResponse: Contains the access token

    Raises:
        HTTPException: If validation fails
    """
    # Validate client
    client = await validate_client(db, request.client_id)

    # Retrieve authorization code
    auth_code = db.query(OAuth2AuthorizationCode).filter(
        OAuth2AuthorizationCode.code == request.code,
        OAuth2AuthorizationCode.client_id == request.client_id,
    ).first()

    if not auth_code:
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_grant")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code",
        )

    # Check if code has already been used (prevent replay attacks)
    if auth_code.is_used == "true":
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_grant")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code has already been used",
        )

    # Check if code has expired
    if auth_code.is_expired():
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_grant")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code has expired",
        )

    # Validate redirect URI matches
    if auth_code.redirect_uri != request.redirect_uri:
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_grant")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Redirect URI mismatch",
        )

    # Verify PKCE code challenge
    if not verify_code_challenge(
        request.code_verifier,
        auth_code.code_challenge,
        auth_code.code_challenge_method
    ):
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_grant")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code verifier",
        )

    # Mark authorization code as used
    auth_code.mark_as_used()
    db.commit()

    # Retrieve user
    user = db.query(User).filter(User.id == auth_code.user_id).first()
    if not user or not user.is_active:
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_grant")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or inactive",
        )

    # Create access token
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "client_id": request.client_id,
        "scope": auth_code.scope,
    }
    access_token, jti, expires_at = create_access_token(token_data)

    if obs_metrics:
        obs_metrics.record_oauth2_token_issued(request.client_id, "access_token")

    return TokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        scope=auth_code.scope,
    )


async def introspect_token(
    db: Session,
    token: str,
) -> TokenIntrospectionResponse:
    """
    Introspect an access token to check its validity and metadata.

    This implements RFC 7662 (OAuth 2.0 Token Introspection).

    Args:
        db: Database session
        token: The access token to introspect

    Returns:
        TokenIntrospectionResponse: Token metadata
    """
    # Verify and decode token
    token_data = verify_token(token, db)

    if token_data is None or token_data.user_id is None:
        # Token is invalid or expired
        return TokenIntrospectionResponse(active=False)

    # Retrieve user to get additional metadata
    user = db.query(User).filter(User.id == UUID(token_data.user_id)).first()

    if not user or not user.is_active:
        return TokenIntrospectionResponse(active=False)

    # Decode token to get claims (already verified above)
    from jose import jwt
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        return TokenIntrospectionResponse(
            active=True,
            scope=payload.get("scope"),
            client_id=payload.get("client_id"),
            username=user.username,
            token_type="Bearer",
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            sub=payload.get("sub"),
            jti=payload.get("jti"),
        )
    except Exception:
        return TokenIntrospectionResponse(active=False)


async def revoke_token(db: Session, token: str, user_id: UUID) -> None:
    """
    Revoke an access token by adding it to the blacklist.

    Args:
        db: Database session
        token: The access token to revoke
        user_id: ID of user revoking the token

    Raises:
        HTTPException: If token is invalid
    """
    from app.core.security import blacklist_token
    from jose import jwt

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        jti = payload.get("jti")
        expires_at = datetime.fromtimestamp(payload.get("exp"))

        if jti:
            blacklist_token(db, jti, expires_at, user_id, reason="revoked")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token does not have a JTI claim",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )


async def validate_state_parameter(
    expected_state: Optional[str],
    received_state: Optional[str]
) -> None:
    """
    Validate the state parameter to prevent CSRF attacks.

    Args:
        expected_state: State value sent in authorization request
        received_state: State value received in callback

    Raises:
        HTTPException: If state validation fails
    """
    if expected_state is None and received_state is None:
        # Both are None, which is acceptable but not recommended
        return

    if expected_state != received_state:
        if obs_metrics:
            obs_metrics.record_oauth2_error("invalid_request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State parameter mismatch - possible CSRF attack",
        )


async def register_client(
    db: Session,
    client_name: str,
    redirect_uris: list[str],
    client_uri: Optional[str] = None,
    scope: Optional[str] = None,
) -> PKCEClient:
    """
    Register a new OAuth2 PKCE public client.

    Args:
        db: Database session
        client_name: Human-readable client name
        redirect_uris: List of allowed redirect URIs
        client_uri: Optional client homepage URI
        scope: Optional default scope

    Returns:
        PKCEClient: The registered client

    Raises:
        HTTPException: If registration fails
    """
    # Generate unique client_id
    client_id = secrets.token_urlsafe(32)

    client = PKCEClient(
        client_id=client_id,
        client_name=client_name,
        client_uri=client_uri,
        redirect_uris=redirect_uris,
        scope=scope,
        is_public=True,
        is_active=True,
    )

    db.add(client)
    db.commit()
    db.refresh(client)

    if obs_metrics:
        obs_metrics.record_oauth2_client_registered(client_id)

    return client
