"""
Single Sign-On (SSO) API routes.

Provides endpoints for SAML and OAuth2/OIDC authentication flows.
Includes user provisioning (JIT) and session creation.
"""

import logging
import urllib.parse
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.sso.config import load_sso_config
from app.auth.sso.oauth2_provider import OAuth2Provider
from app.auth.sso.saml_provider import SAMLProvider
from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter()

# Load SSO configuration
sso_config = load_sso_config()

# Security: Allowed redirect hosts to prevent open redirect attacks
# Add production domain(s) to this list in production
ALLOWED_REDIRECT_HOSTS = ["localhost", "127.0.0.1"]


def validate_redirect_url(url: str | None) -> str:
    """
    Validate redirect URL is safe, preventing open redirect attacks.

    Open redirect vulnerabilities allow attackers to redirect users to arbitrary
    external sites after successful authentication, enabling phishing attacks.

    Args:
        url: User-supplied redirect URL (from relay_state or redirect_uri)

    Returns:
        Validated redirect URL (safe) or default /dashboard if validation fails

    Security:
        - Only allows relative URLs (starting with / but not //)
        - Validates absolute URLs against ALLOWED_REDIRECT_HOSTS whitelist
        - Logs blocked redirect attempts for security monitoring
    """
    if not url:
        return "/dashboard"

    # Allow relative URLs (safe - same-origin)
    # Block protocol-relative URLs (//) which could redirect to external sites
    if url.startswith("/") and not url.startswith("//"):
        return url

    # Validate absolute URLs against whitelist
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc:
            # Has a hostname - must be in whitelist
            if parsed.netloc not in ALLOWED_REDIRECT_HOSTS:
                logger.warning(
                    f"SECURITY: Blocked open redirect attempt to: {parsed.netloc}"
                )
                return "/dashboard"
        # No netloc but has scheme (e.g., javascript:) - block
        elif parsed.scheme:
            logger.warning(f"SECURITY: Blocked redirect with scheme: {parsed.scheme}")
            return "/dashboard"
    except Exception as e:
        logger.warning(f"SECURITY: Invalid redirect URL: {e}")
        return "/dashboard"

    return url


class SSOSessionState(BaseModel):
    """Temporary SSO session state stored in cache/session."""

    provider: str
    state: str | None = None
    relay_state: str | None = None
    code_verifier: str | None = None
    request_id: str | None = None


# In-memory session store (use Redis in production)
_sso_sessions: dict[str, SSOSessionState] = {}


def get_or_create_user(db: Session, attributes: dict[str, str], provider: str) -> User:
    """
    Get existing user or create new user (JIT provisioning).

    Args:
        db: Database session
        attributes: User attributes from SSO provider
        provider: SSO provider name (saml, oauth2)

    Returns:
        User object

    Raises:
        HTTPException: If user creation fails
    """
    email = attributes.get("email", "").strip()
    username = attributes.get("username", "").strip()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required from SSO provider",
        )

    # Use email as username if username not provided
    if not username:
        username = email.split("@")[0]

    # Check if user exists by email
    user = db.query(User).filter(User.email == email).first()

    if user:
        # Update last login
        from datetime import datetime

        user.last_login = datetime.utcnow()
        db.commit()
        return user

    # Auto-provision user if enabled
    if not sso_config.auto_provision_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not exist and auto-provisioning is disabled",
        )

    # Check if username is already taken
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        # Append random suffix to username
        import uuid

        username = f"{username}_{uuid.uuid4().hex[:8]}"

    # Extract role from attributes or use default
    role = attributes.get("role", sso_config.default_role)

    # Validate role
    valid_roles = {
        "admin",
        "coordinator",
        "faculty",
        "clinical_staff",
        "rn",
        "lpn",
        "msa",
        "resident",
    }
    if role not in valid_roles:
        role = sso_config.default_role

    # Create new user
    try:
        new_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(f"sso_{provider}_{uuid.uuid4().hex}"),
            role=role,
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


def create_session(response: Response, user: User) -> dict:
    """
    Create authenticated session for user.

    Sets httpOnly cookie and returns token response.

    Args:
        response: FastAPI response object
        user: Authenticated user

    Returns:
        Dict with access_token and user info
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, jti, expires_at = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires,
    )

    # Set httpOnly cookie for XSS protection
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
    }


# SAML Routes


@router.get("/saml/metadata")
async def saml_metadata():
    """
    Get SAML Service Provider metadata.

    Returns SP metadata XML for IdP configuration.
    """
    if not sso_config.saml.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAML authentication not enabled",
        )

    provider = SAMLProvider(sso_config.saml)
    metadata_xml = provider.generate_sp_metadata()

    return Response(content=metadata_xml, media_type="application/xml")


@router.get("/saml/login")
async def saml_login(relay_state: str | None = None):
    """
    Initiate SAML login flow.

    Redirects user to IdP for authentication.

    Args:
        relay_state: Optional URL to redirect after successful authentication
    """
    if not sso_config.saml.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAML authentication not enabled",
        )

    provider = SAMLProvider(sso_config.saml)
    request_id, redirect_url = provider.generate_authn_request()

    # Store session state
    _sso_sessions[request_id] = SSOSessionState(
        provider="saml",
        request_id=request_id,
        relay_state=relay_state,
    )

    return RedirectResponse(url=redirect_url)


@router.post("/saml/acs")
async def saml_acs(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    SAML Assertion Consumer Service (ACS).

    Receives SAML response from IdP, validates it, and creates user session.
    """
    if not sso_config.saml.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAML authentication not enabled",
        )

    # Get SAML response from form data
    form_data = await request.form()
    saml_response = form_data.get("SAMLResponse")
    relay_state = form_data.get("RelayState")

    if not saml_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing SAMLResponse",
        )

    # Parse and validate SAML response
    provider = SAMLProvider(sso_config.saml)

    try:
        saml_data = provider.parse_saml_response(
            saml_response, validate_signature=sso_config.saml.want_assertions_signed
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SAML response validation failed: {str(e)}",
        )

    # Extract user attributes
    attributes = saml_data["attributes"]

    # Get or create user
    user = get_or_create_user(db, attributes, "saml")

    # Create session
    session_data = create_session(response, user)

    # Redirect to relay state or default dashboard
    # Security: Validate redirect URL to prevent open redirect attacks
    redirect_url = validate_redirect_url(relay_state)

    # Return HTML that redirects (since this is a POST response)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url={redirect_url}">
    </head>
    <body>
        <p>Authentication successful. Redirecting...</p>
        <script>window.location.href = '{redirect_url}';</script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@router.get("/saml/logout")
async def saml_logout(name_id: str, session_index: str | None = None):
    """
    Initiate SAML logout flow.

    Redirects user to IdP for logout.
    """
    if not sso_config.saml.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SAML authentication not enabled",
        )

    provider = SAMLProvider(sso_config.saml)
    request_id, redirect_url = provider.generate_logout_request(name_id, session_index)

    return RedirectResponse(url=redirect_url)


# OAuth2/OIDC Routes


@router.get("/oauth2/login")
async def oauth2_login(redirect_uri: str | None = None):
    """
    Initiate OAuth2/OIDC login flow.

    Redirects user to OAuth2 provider for authentication.

    Args:
        redirect_uri: Optional URL to redirect after successful authentication
    """
    if not sso_config.oauth2.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth2 authentication not enabled",
        )

    provider = OAuth2Provider(sso_config.oauth2)
    auth_data = provider.generate_authorization_url(use_pkce=True)

    # Store session state
    state = auth_data["state"]
    _sso_sessions[state] = SSOSessionState(
        provider="oauth2",
        state=state,
        relay_state=redirect_uri,
        code_verifier=auth_data.get("code_verifier"),
    )

    return RedirectResponse(url=auth_data["authorization_url"])


@router.get("/oauth2/callback")
async def oauth2_callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    OAuth2/OIDC callback endpoint.

    Receives authorization code, exchanges it for tokens, and creates user session.
    """
    if not sso_config.oauth2.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth2 authentication not enabled",
        )

    # Validate state parameter (CSRF protection)
    session_state = _sso_sessions.get(state)
    if not session_state or session_state.state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    provider = OAuth2Provider(sso_config.oauth2)

    # Exchange code for tokens
    try:
        token_response = await provider.exchange_code_for_token(
            code, code_verifier=session_state.code_verifier
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token exchange failed: {str(e)}",
        )

    # Validate ID token if present (OIDC)
    id_token = token_response.get("id_token")
    if id_token:
        try:
            id_token_claims = await provider.validate_id_token(id_token)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID token validation failed: {str(e)}",
            )
    else:
        id_token_claims = {}

    # Get user info from UserInfo endpoint or ID token
    access_token = token_response.get("access_token")
    if access_token and sso_config.oauth2.userinfo_endpoint:
        try:
            userinfo = await provider.get_userinfo(access_token)
        except ValueError:
            # Fall back to ID token claims
            userinfo = id_token_claims
    else:
        userinfo = id_token_claims

    # Map claims to user attributes
    attributes = provider.map_claims_to_user(userinfo)

    # Get or create user
    user = get_or_create_user(db, attributes, "oauth2")

    # Create session
    session_data = create_session(response, user)

    # Clean up session state
    del _sso_sessions[state]

    # Redirect to relay state or default dashboard
    # Security: Validate redirect URL to prevent open redirect attacks
    redirect_url = validate_redirect_url(session_state.relay_state)

    return RedirectResponse(url=redirect_url)


@router.get("/providers")
async def list_providers():
    """
    List available SSO providers.

    Returns configuration info for active SSO providers.
    """
    providers = []

    if sso_config.saml.enabled:
        providers.append(
            {
                "type": "saml",
                "name": "SAML 2.0",
                "login_url": "/api/sso/saml/login",
                "metadata_url": "/api/sso/saml/metadata",
            }
        )

    if sso_config.oauth2.enabled:
        providers.append(
            {
                "type": "oauth2",
                "name": sso_config.oauth2.provider_name,
                "login_url": "/api/sso/oauth2/login",
            }
        )

    return {
        "providers": providers,
        "sso_enabled": sso_config.enabled,
        "local_auth_enabled": sso_config.allow_local_fallback,
    }


@router.get("/status")
async def sso_status():
    """
    Get SSO configuration status.

    Returns current SSO configuration (admin info).
    """
    return {
        "enabled": sso_config.enabled,
        "active_providers": sso_config.get_active_providers(),
        "auto_provision_users": sso_config.auto_provision_users,
        "allow_local_fallback": sso_config.allow_local_fallback,
        "default_role": sso_config.default_role,
        "saml_enabled": sso_config.saml.enabled,
        "oauth2_enabled": sso_config.oauth2.enabled,
    }
