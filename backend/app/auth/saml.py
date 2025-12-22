"""
SAML-based SSO Integration Service.

Provides comprehensive SAML 2.0 Single Sign-On integration including:
- SAML service provider configuration
- Identity provider metadata parsing
- SAML assertion validation
- Attribute mapping to user model
- Single logout (SLO) support
- SAML response signature verification
- Session management integration
- Multi-IdP support

This module serves as the high-level integration layer for SAML authentication,
coordinating between SAML protocol handling, user provisioning, and session management.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.auth.sso.config import SAMLConfig, load_sso_config
from app.auth.sso.saml_provider import SAMLProvider
from app.core.security import create_access_token, get_password_hash
from app.models.user import User

logger = logging.getLogger(__name__)


# ============================================================================
# Multi-IdP Configuration
# ============================================================================


class SAMLIdentityProvider:
    """
    Configuration for a single SAML Identity Provider.

    Supports multiple IdPs for enterprise SSO scenarios (e.g., different
    organizations or departments using different identity providers).
    """

    def __init__(
        self,
        idp_id: str,
        name: str,
        config: SAMLConfig,
        enabled: bool = True,
        priority: int = 0,
        domains: Optional[List[str]] = None,
    ):
        """
        Initialize SAML Identity Provider configuration.

        Args:
            idp_id: Unique identifier for this IdP
            name: Display name for this IdP
            config: SAML configuration for this IdP
            enabled: Whether this IdP is currently enabled
            priority: Priority for IdP selection (higher = higher priority)
            domains: Email domains associated with this IdP (for auto-selection)
        """
        self.idp_id = idp_id
        self.name = name
        self.config = config
        self.enabled = enabled
        self.priority = priority
        self.domains = domains or []
        self.provider = SAMLProvider(config)

    def matches_domain(self, email: str) -> bool:
        """
        Check if an email address matches this IdP's domains.

        Args:
            email: Email address to check

        Returns:
            True if email domain matches this IdP's configured domains
        """
        if not self.domains:
            return False

        email_domain = email.split("@")[-1].lower()
        return email_domain in [d.lower() for d in self.domains]


class SAMLIdentityProviderRegistry:
    """
    Registry for managing multiple SAML Identity Providers.

    Supports multi-IdP scenarios with domain-based routing and priority-based
    selection.
    """

    def __init__(self):
        """Initialize empty IdP registry."""
        self._idps: Dict[str, SAMLIdentityProvider] = {}

    def register(
        self,
        idp_id: str,
        name: str,
        config: SAMLConfig,
        enabled: bool = True,
        priority: int = 0,
        domains: Optional[List[str]] = None,
    ) -> SAMLIdentityProvider:
        """
        Register a new Identity Provider.

        Args:
            idp_id: Unique identifier for this IdP
            name: Display name for this IdP
            config: SAML configuration for this IdP
            enabled: Whether this IdP is currently enabled
            priority: Priority for IdP selection
            domains: Email domains associated with this IdP

        Returns:
            Registered SAMLIdentityProvider instance

        Raises:
            ValueError: If IdP with same ID already exists
        """
        if idp_id in self._idps:
            raise ValueError(f"IdP with ID '{idp_id}' already registered")

        idp = SAMLIdentityProvider(
            idp_id=idp_id,
            name=name,
            config=config,
            enabled=enabled,
            priority=priority,
            domains=domains,
        )
        self._idps[idp_id] = idp

        logger.info(
            f"Registered SAML IdP: {name} (ID: {idp_id}, "
            f"domains: {domains}, priority: {priority})"
        )

        return idp

    def get(self, idp_id: str) -> Optional[SAMLIdentityProvider]:
        """
        Get Identity Provider by ID.

        Args:
            idp_id: IdP identifier

        Returns:
            SAMLIdentityProvider or None if not found
        """
        return self._idps.get(idp_id)

    def get_all_enabled(self) -> List[SAMLIdentityProvider]:
        """
        Get all enabled Identity Providers.

        Returns:
            List of enabled IdPs sorted by priority (descending)
        """
        enabled = [idp for idp in self._idps.values() if idp.enabled]
        return sorted(enabled, key=lambda x: x.priority, reverse=True)

    def get_by_email(self, email: str) -> Optional[SAMLIdentityProvider]:
        """
        Get Identity Provider for an email address based on domain matching.

        Args:
            email: Email address

        Returns:
            Matching SAMLIdentityProvider or None if no match found
        """
        for idp in self.get_all_enabled():
            if idp.matches_domain(email):
                return idp
        return None

    def get_default(self) -> Optional[SAMLIdentityProvider]:
        """
        Get default Identity Provider (highest priority enabled IdP).

        Returns:
            Default SAMLIdentityProvider or None if no IdPs registered
        """
        enabled = self.get_all_enabled()
        return enabled[0] if enabled else None

    def unregister(self, idp_id: str) -> bool:
        """
        Unregister an Identity Provider.

        Args:
            idp_id: IdP identifier

        Returns:
            True if IdP was unregistered, False if not found
        """
        if idp_id in self._idps:
            del self._idps[idp_id]
            logger.info(f"Unregistered SAML IdP: {idp_id}")
            return True
        return False


# Global IdP registry
_idp_registry = SAMLIdentityProviderRegistry()


def get_idp_registry() -> SAMLIdentityProviderRegistry:
    """Get global IdP registry instance."""
    return _idp_registry


# ============================================================================
# SAML Session Management
# ============================================================================


class SAMLSession:
    """
    SAML session information.

    Stores SAML-specific session data for managing SSO sessions and
    enabling Single Logout (SLO).
    """

    def __init__(
        self,
        session_id: str,
        user_id: UUID,
        idp_id: str,
        name_id: str,
        session_index: Optional[str] = None,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        attributes: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize SAML session.

        Args:
            session_id: Unique session identifier
            user_id: Associated user ID
            idp_id: Identity Provider ID
            name_id: SAML NameID (for logout)
            session_index: SAML SessionIndex (for logout)
            created_at: Session creation timestamp
            expires_at: Session expiration timestamp
            attributes: SAML attributes from assertion
        """
        self.session_id = session_id
        self.user_id = user_id
        self.idp_id = idp_id
        self.name_id = name_id
        self.session_index = session_index
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(hours=8))
        self.attributes = attributes or {}

    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() >= self.expires_at

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": str(self.user_id),
            "idp_id": self.idp_id,
            "name_id": self.name_id,
            "session_index": self.session_index,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "attributes": self.attributes,
        }


class SAMLSessionManager:
    """
    In-memory SAML session manager.

    Manages SAML session lifecycle for Single Logout support.
    In production, consider using Redis or database for distributed deployments.
    """

    def __init__(self):
        """Initialize session manager."""
        self._sessions: Dict[str, SAMLSession] = {}
        self._user_sessions: Dict[UUID, List[str]] = {}

    def create_session(
        self,
        user_id: UUID,
        idp_id: str,
        name_id: str,
        session_index: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
        session_duration_hours: int = 8,
    ) -> SAMLSession:
        """
        Create new SAML session.

        Args:
            user_id: User ID
            idp_id: Identity Provider ID
            name_id: SAML NameID
            session_index: SAML SessionIndex
            attributes: SAML attributes
            session_duration_hours: Session duration in hours

        Returns:
            Created SAMLSession
        """
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=session_duration_hours)

        session = SAMLSession(
            session_id=session_id,
            user_id=user_id,
            idp_id=idp_id,
            name_id=name_id,
            session_index=session_index,
            expires_at=expires_at,
            attributes=attributes,
        )

        self._sessions[session_id] = session

        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)

        logger.info(
            f"Created SAML session {session_id} for user {user_id} via IdP {idp_id}"
        )

        return session

    def get_session(self, session_id: str) -> Optional[SAMLSession]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SAMLSession or None if not found or expired
        """
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            self.destroy_session(session_id)
            return None
        return session

    def get_user_sessions(self, user_id: UUID) -> List[SAMLSession]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of active SAMLSessions
        """
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []
        for session_id in session_ids[:]:  # Copy to avoid modification during iteration
            session = self.get_session(session_id)
            if session:
                sessions.append(session)
            else:
                # Remove expired/invalid session
                session_ids.remove(session_id)
        return sessions

    def destroy_session(self, session_id: str) -> bool:
        """
        Destroy a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was destroyed, False if not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        del self._sessions[session_id]

        if session.user_id in self._user_sessions:
            try:
                self._user_sessions[session.user_id].remove(session_id)
            except ValueError:
                pass

        logger.info(f"Destroyed SAML session {session_id}")
        return True

    def destroy_user_sessions(self, user_id: UUID) -> int:
        """
        Destroy all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            Number of sessions destroyed
        """
        session_ids = self._user_sessions.get(user_id, [])
        count = 0
        for session_id in session_ids[:]:
            if self.destroy_session(session_id):
                count += 1
        return count

    def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_ids = [
            sid for sid, sess in self._sessions.items() if sess.is_expired()
        ]
        for session_id in expired_ids:
            self.destroy_session(session_id)
        return len(expired_ids)


# Global session manager
_session_manager = SAMLSessionManager()


def get_session_manager() -> SAMLSessionManager:
    """Get global session manager instance."""
    return _session_manager


# ============================================================================
# SAML Authentication Service
# ============================================================================


class SAMLAuthenticationService:
    """
    High-level SAML authentication service.

    Orchestrates SAML authentication flow including user provisioning,
    session management, and integration with application authentication.
    """

    def __init__(
        self,
        idp_registry: Optional[SAMLIdentityProviderRegistry] = None,
        session_manager: Optional[SAMLSessionManager] = None,
    ):
        """
        Initialize SAML authentication service.

        Args:
            idp_registry: IdP registry (uses global if not provided)
            session_manager: Session manager (uses global if not provided)
        """
        self.idp_registry = idp_registry or get_idp_registry()
        self.session_manager = session_manager or get_session_manager()
        self.sso_config = load_sso_config()

    async def initiate_login(
        self,
        idp_id: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """
        Initiate SAML login flow.

        Args:
            idp_id: Specific IdP to use (optional)
            email: User email for IdP selection (optional)

        Returns:
            Tuple of (request_id, redirect_url, idp_id)

        Raises:
            HTTPException: If no suitable IdP found or IdP not enabled
        """
        # Select IdP
        if idp_id:
            idp = self.idp_registry.get(idp_id)
            if not idp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Identity Provider '{idp_id}' not found",
                )
        elif email:
            idp = self.idp_registry.get_by_email(email)
            if not idp:
                idp = self.idp_registry.get_default()
        else:
            idp = self.idp_registry.get_default()

        if not idp:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No SAML Identity Provider configured",
            )

        if not idp.enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Identity Provider '{idp.name}' is currently disabled",
            )

        # Generate authentication request
        request_id, redirect_url = idp.provider.generate_authn_request()

        logger.info(
            f"Initiated SAML login for IdP '{idp.name}' (ID: {idp.idp_id}), "
            f"request_id: {request_id}"
        )

        return request_id, redirect_url, idp.idp_id

    async def handle_login_response(
        self,
        saml_response: str,
        idp_id: str,
        db: AsyncSession,
    ) -> Tuple[User, str, str]:
        """
        Handle SAML login response.

        Validates SAML response, provisions user if needed, creates session,
        and generates access token.

        Args:
            saml_response: Base64-encoded SAML response
            idp_id: Identity Provider ID
            db: Database session

        Returns:
            Tuple of (user, access_token, saml_session_id)

        Raises:
            HTTPException: If validation fails or user provisioning fails
        """
        # Get IdP
        idp = self.idp_registry.get(idp_id)
        if not idp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Identity Provider",
            )

        # Parse and validate SAML response
        try:
            saml_data = idp.provider.parse_saml_response(
                saml_response,
                validate_signature=idp.config.want_response_signed
                or idp.config.want_assertions_signed,
            )
        except ValueError as e:
            logger.error(f"SAML response validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid SAML response",
            )

        name_id = saml_data["name_id"]
        session_index = saml_data.get("session_index")
        attributes = saml_data["attributes"]

        logger.info(
            f"Validated SAML response from IdP '{idp.name}', "
            f"NameID: {name_id}, attributes: {list(attributes.keys())}"
        )

        # Get or create user
        user = await self._get_or_create_user(db, attributes, idp_id)

        # Create SAML session
        saml_session = self.session_manager.create_session(
            user_id=user.id,
            idp_id=idp_id,
            name_id=name_id,
            session_index=session_index,
            attributes=attributes,
        )

        # Update last login
        await self._update_last_login(db, user.id)

        # Generate access token
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "saml_session_id": saml_session.session_id,
        }
        access_token, jti, expires_at = create_access_token(token_data)

        logger.info(
            f"SAML login successful for user {user.username} (ID: {user.id}) "
            f"via IdP '{idp.name}'"
        )

        return user, access_token, saml_session.session_id

    async def initiate_logout(
        self,
        user_id: UUID,
        saml_session_id: Optional[str] = None,
    ) -> Optional[Tuple[str, str]]:
        """
        Initiate SAML Single Logout (SLO).

        Args:
            user_id: User ID
            saml_session_id: Specific SAML session to logout (optional)

        Returns:
            Tuple of (request_id, redirect_url) or None if local logout only

        Raises:
            HTTPException: If session not found or IdP not configured
        """
        # Get SAML session
        if saml_session_id:
            session = self.session_manager.get_session(saml_session_id)
            if not session or session.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="SAML session not found",
                )
            sessions = [session]
        else:
            sessions = self.session_manager.get_user_sessions(user_id)

        if not sessions:
            # No SAML sessions, local logout only
            return None

        # Use first session for SLO
        session = sessions[0]

        # Get IdP
        idp = self.idp_registry.get(session.idp_id)
        if not idp:
            # IdP no longer configured, destroy sessions locally
            self.session_manager.destroy_user_sessions(user_id)
            return None

        # Generate logout request
        request_id, redirect_url = idp.provider.generate_logout_request(
            name_id=session.name_id,
            session_index=session.session_index,
        )

        # Destroy local sessions
        self.session_manager.destroy_user_sessions(user_id)

        logger.info(
            f"Initiated SAML logout for user {user_id}, "
            f"request_id: {request_id}, IdP: {idp.name}"
        )

        return request_id, redirect_url

    async def _get_or_create_user(
        self,
        db: AsyncSession,
        attributes: Dict[str, str],
        idp_id: str,
    ) -> User:
        """
        Get existing user or create new one (JIT provisioning).

        Args:
            db: Database session
            attributes: SAML attributes
            idp_id: Identity Provider ID

        Returns:
            User instance

        Raises:
            HTTPException: If user provisioning fails
        """
        # Extract required attributes
        email = attributes.get("email")
        username = attributes.get("username") or email

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email attribute required in SAML response",
            )

        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email required in SAML response",
            )

        # Check if user exists
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update user attributes from SAML
            if self.sso_config.auto_provision_users:
                await self._update_user_attributes(db, user, attributes)
            return user

        # Create new user (JIT provisioning)
        if not self.sso_config.auto_provision_users:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not exist and auto-provisioning is disabled",
            )

        role = attributes.get("role") or self.sso_config.default_role

        # Generate random password (won't be used for SSO users)
        random_password = get_password_hash(str(uuid.uuid4()))

        user = User(
            username=username,
            email=email,
            hashed_password=random_password,
            role=role,
            is_active=True,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(
            f"Created new user via SAML JIT provisioning: {username} "
            f"(email: {email}, role: {role}, IdP: {idp_id})"
        )

        return user

    async def _update_user_attributes(
        self,
        db: AsyncSession,
        user: User,
        attributes: Dict[str, str],
    ) -> None:
        """
        Update user attributes from SAML assertion.

        Args:
            db: Database session
            user: User to update
            attributes: SAML attributes
        """
        updates = {}

        # Update email if changed
        if "email" in attributes and attributes["email"] != user.email:
            updates["email"] = attributes["email"]

        # Update username if changed
        if "username" in attributes and attributes["username"] != user.username:
            updates["username"] = attributes["username"]

        # Update role if provided
        if "role" in attributes and attributes["role"] != user.role:
            updates["role"] = attributes["role"]

        if updates:
            await db.execute(
                update(User).where(User.id == user.id).values(**updates)
            )
            await db.commit()
            await db.refresh(user)

            logger.info(f"Updated user {user.id} attributes from SAML: {updates}")

    async def _update_last_login(self, db: AsyncSession, user_id: UUID) -> None:
        """
        Update user's last login timestamp.

        Args:
            db: Database session
            user_id: User ID
        """
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login=datetime.utcnow())
        )
        await db.commit()


# ============================================================================
# Utility Functions
# ============================================================================


async def initialize_default_idp() -> Optional[SAMLIdentityProvider]:
    """
    Initialize default SAML Identity Provider from configuration.

    Loads SSO configuration and registers default IdP if SAML is enabled.

    Returns:
        Registered SAMLIdentityProvider or None if SAML not enabled
    """
    sso_config = load_sso_config()

    if not sso_config.enabled or not sso_config.saml.enabled:
        logger.info("SAML SSO is not enabled")
        return None

    # Validate required configuration
    if not sso_config.saml.entity_id:
        logger.error("SAML entity_id not configured")
        return None

    if not sso_config.saml.acs_url:
        logger.error("SAML acs_url not configured")
        return None

    if not sso_config.saml.idp_sso_url:
        logger.error("SAML idp_sso_url not configured")
        return None

    # Register default IdP
    registry = get_idp_registry()
    idp = registry.register(
        idp_id="default",
        name="Default SAML Provider",
        config=sso_config.saml,
        enabled=True,
        priority=100,
    )

    logger.info(
        f"Initialized default SAML IdP: entity_id={sso_config.saml.entity_id}, "
        f"acs_url={sso_config.saml.acs_url}"
    )

    return idp


def get_saml_service() -> SAMLAuthenticationService:
    """
    Get SAML authentication service instance.

    Returns:
        SAMLAuthenticationService
    """
    return SAMLAuthenticationService()
