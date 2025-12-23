"""
Gateway authentication layer for API key, JWT, OAuth2, and request signature validation.

This module provides comprehensive authentication mechanisms for the API gateway:
- API key validation for external services
- JWT token validation at gateway level
- OAuth2 client credentials flow
- Rate limiting per API key/client
- IP whitelist/blacklist support
- Request signing verification (HMAC)
- API key rotation support
"""

import hashlib
import hmac
import ipaddress
import logging
import secrets
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, Request, status
from jose import jwt
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.core.security import get_password_hash, verify_password, verify_token
from app.models.gateway_auth import (
    APIKey,
    IPBlacklist,
    IPWhitelist,
    OAuth2Client,
    RequestSignature,
)
from app.models.user import User
from app.schemas.gateway_auth import (
    APIKeyCreate,
    APIKeyResponse,
    GatewayAuthValidationResponse,
    OAuth2TokenResponse,
    RequestSignatureVerifyRequest,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Constants
API_KEY_PREFIX = "sk_live_"
API_KEY_LENGTH = 64  # Characters in the random part
SIGNATURE_TOLERANCE_SECONDS = 300  # 5 minutes for replay attack prevention
HMAC_ALGORITHM = "sha256"


class GatewayAuthenticationError(Exception):
    """Base exception for gateway authentication errors."""

    pass


class APIKeyManager:
    """
    Manager for API key lifecycle operations.

    Handles creation, validation, rotation, and revocation of API keys.
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_api_key(self) -> tuple[str, str, str]:
        """
        Generate a new API key.

        Returns:
            Tuple of (full_key, key_hash, key_prefix)
                - full_key: The complete API key to show to user (only once)
                - key_hash: SHA-256 hash to store in database
                - key_prefix: First 8 characters for identification
        """
        # Generate random key
        random_part = secrets.token_urlsafe(API_KEY_LENGTH)
        full_key = f"{API_KEY_PREFIX}{random_part}"

        # Hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        # Extract prefix for display
        key_prefix = full_key[:16]  # "sk_live_" + first 8 chars

        return full_key, key_hash, key_prefix

    async def create_api_key(
        self, key_data: APIKeyCreate, owner_id: UUID | None = None
    ) -> APIKeyResponse:
        """
        Create a new API key.

        Args:
            key_data: API key creation data
            owner_id: Optional owner user ID

        Returns:
            APIKeyResponse with the full API key (only shown once)
        """
        # Generate key
        full_key, key_hash, key_prefix = self.generate_api_key()

        # Create database record
        api_key = APIKey(
            name=key_data.name,
            key_hash=key_hash,
            key_prefix=key_prefix,
            owner_id=owner_id,
            scopes=key_data.scopes,
            allowed_ips=key_data.allowed_ips,
            rate_limit_per_minute=key_data.rate_limit_per_minute,
            rate_limit_per_hour=key_data.rate_limit_per_hour,
            expires_at=key_data.expires_at,
            is_active=True,
        )

        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)

        logger.info(f"Created API key: {api_key.name} (prefix: {key_prefix})")

        # Return response with full key (only time we show it)
        response = APIKeyResponse.model_validate(api_key)
        response.api_key = full_key
        return response

    async def validate_api_key(self, api_key: str) -> APIKey | None:
        """
        Validate an API key.

        Args:
            api_key: The API key to validate

        Returns:
            APIKey object if valid, None otherwise
        """
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Query database
        result = self.db.execute(
            select(APIKey).where(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active == True,
                    APIKey.revoked_at.is_(None),
                )
            )
        )
        db_key = result.scalar_one_or_none()

        if not db_key:
            logger.warning(f"Invalid API key attempt with prefix: {api_key[:16]}")
            return None

        # Check expiration
        if db_key.is_expired:
            logger.warning(f"Expired API key used: {db_key.name}")
            return None

        return db_key

    async def rotate_api_key(
        self, key_id: UUID, grace_period_hours: int = 24, new_name: str | None = None
    ) -> tuple[APIKeyResponse, APIKey]:
        """
        Rotate an API key by creating a new one and linking to the old one.

        Args:
            key_id: ID of the key to rotate
            grace_period_hours: Hours to keep old key valid
            new_name: Optional new name for rotated key

        Returns:
            Tuple of (new_key_response, old_key)

        Raises:
            ValueError: If key not found or already rotated
        """
        # Get existing key
        old_key = self.db.get(APIKey, key_id)
        if not old_key:
            raise ValueError("API key not found")

        if old_key.rotated_to_id:
            raise ValueError("API key has already been rotated")

        # Create new key with same settings
        new_key_data = APIKeyCreate(
            name=new_name or f"{old_key.name} (rotated)",
            scopes=old_key.scopes,
            allowed_ips=old_key.allowed_ips,
            rate_limit_per_minute=old_key.rate_limit_per_minute,
            rate_limit_per_hour=old_key.rate_limit_per_hour,
        )

        new_key_response = await self.create_api_key(new_key_data, old_key.owner_id)
        new_key = self.db.get(APIKey, new_key_response.id)

        # Link keys
        old_key.rotated_to_id = new_key.id
        new_key.rotated_from_id = old_key.id

        # Schedule old key expiration
        if grace_period_hours > 0:
            old_key.expires_at = datetime.utcnow() + timedelta(hours=grace_period_hours)
        else:
            old_key.is_active = False

        self.db.commit()

        logger.info(
            f"Rotated API key: {old_key.name} -> {new_key.name}, "
            f"grace period: {grace_period_hours}h"
        )

        return new_key_response, old_key

    async def revoke_api_key(
        self, key_id: UUID, reason: str, revoked_by_id: UUID | None = None
    ) -> APIKey:
        """
        Revoke an API key immediately.

        Args:
            key_id: ID of the key to revoke
            reason: Reason for revocation
            revoked_by_id: ID of user who revoked the key

        Returns:
            Revoked APIKey object

        Raises:
            ValueError: If key not found
        """
        api_key = self.db.get(APIKey, key_id)
        if not api_key:
            raise ValueError("API key not found")

        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by_id = revoked_by_id
        api_key.revoked_reason = reason

        self.db.commit()
        logger.warning(f"Revoked API key: {api_key.name}, reason: {reason}")

        return api_key

    async def update_key_usage(self, api_key: APIKey, client_ip: str) -> None:
        """
        Update API key usage statistics.

        Args:
            api_key: The API key object
            client_ip: Client IP address
        """
        api_key.last_used_at = datetime.utcnow()
        api_key.last_used_ip = client_ip
        api_key.total_requests += 1
        self.db.commit()


class OAuth2Manager:
    """
    Manager for OAuth2 client credentials flow.

    Handles client creation, token issuance, and validation.
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_client_credentials(self) -> tuple[str, str, str]:
        """
        Generate OAuth2 client ID and secret.

        Returns:
            Tuple of (client_id, client_secret, client_secret_hash)
        """
        client_id = f"client_{secrets.token_urlsafe(32)}"
        client_secret = secrets.token_urlsafe(48)
        client_secret_hash = get_password_hash(client_secret)

        return client_id, client_secret, client_secret_hash

    async def create_client(
        self, name: str, scopes: str, owner_id: UUID | None = None, **kwargs
    ) -> tuple[OAuth2Client, str]:
        """
        Create a new OAuth2 client.

        Args:
            name: Client name
            scopes: Allowed scopes
            owner_id: Optional owner user ID
            **kwargs: Additional client parameters

        Returns:
            Tuple of (OAuth2Client, client_secret)
        """
        client_id, client_secret, client_secret_hash = (
            self.generate_client_credentials()
        )

        client = OAuth2Client(
            client_id=client_id,
            client_secret_hash=client_secret_hash,
            name=name,
            scopes=scopes,
            owner_id=owner_id,
            **kwargs,
        )

        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)

        logger.info(f"Created OAuth2 client: {name} (client_id: {client_id})")

        return client, client_secret

    async def authenticate_client(
        self, client_id: str, client_secret: str
    ) -> OAuth2Client | None:
        """
        Authenticate an OAuth2 client.

        Args:
            client_id: Client ID
            client_secret: Client secret

        Returns:
            OAuth2Client if valid, None otherwise
        """
        result = self.db.execute(
            select(OAuth2Client).where(
                and_(
                    OAuth2Client.client_id == client_id, OAuth2Client.is_active == True
                )
            )
        )
        client = result.scalar_one_or_none()

        if not client:
            logger.warning(f"Invalid OAuth2 client_id: {client_id}")
            return None

        # Verify client secret
        if not verify_password(client_secret, client.client_secret_hash):
            logger.warning(f"Invalid OAuth2 client_secret for client: {client_id}")
            return None

        return client

    async def issue_access_token(
        self, client: OAuth2Client, requested_scopes: str | None = None
    ) -> OAuth2TokenResponse:
        """
        Issue an access token for OAuth2 client credentials flow.

        Args:
            client: Authenticated OAuth2 client
            requested_scopes: Optional requested scopes (must be subset of client scopes)

        Returns:
            OAuth2TokenResponse with access token

        Raises:
            ValueError: If requested scopes exceed client's allowed scopes
        """
        # Validate scopes
        client_scopes = set(client.get_scopes())
        if requested_scopes:
            requested = set(s.strip() for s in requested_scopes.split())
            if not requested.issubset(client_scopes):
                raise ValueError("Requested scopes exceed client's allowed scopes")
            granted_scopes = requested
        else:
            granted_scopes = client_scopes

        # Create JWT token
        expires_delta = timedelta(seconds=client.access_token_lifetime_seconds)
        expires_at = datetime.utcnow() + expires_delta

        token_data = {
            "sub": str(client.id),
            "client_id": client.client_id,
            "scopes": list(granted_scopes),
            "type": "client_credentials",
            "exp": expires_at,
            "iat": datetime.utcnow(),
        }

        access_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm="HS256")

        # Update usage statistics
        client.last_used_at = datetime.utcnow()
        client.total_tokens_issued += 1
        self.db.commit()

        logger.info(
            f"Issued OAuth2 token for client: {client.name}, "
            f"scopes: {', '.join(granted_scopes)}"
        )

        return OAuth2TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=client.access_token_lifetime_seconds,
            scope=" ".join(granted_scopes) if granted_scopes else None,
        )


class IPFilterManager:
    """
    Manager for IP whitelist and blacklist operations.

    Handles IP-based access control with support for CIDR ranges.
    """

    def __init__(self, db: Session):
        self.db = db

    def _ip_in_range(self, ip: str, range_spec: str) -> bool:
        """
        Check if an IP address is in a given range.

        Args:
            ip: IP address to check
            range_spec: IP address or CIDR range

        Returns:
            True if IP is in range, False otherwise
        """
        try:
            ip_obj = ipaddress.ip_address(ip)

            # Check if range_spec is a CIDR range
            if "/" in range_spec:
                network = ipaddress.ip_network(range_spec, strict=False)
                return ip_obj in network
            else:
                # Single IP comparison
                return ip == range_spec
        except ValueError as e:
            logger.error(f"Invalid IP address or range: {e}")
            return False

    async def is_ip_blacklisted(
        self, ip_address: str
    ) -> tuple[bool, IPBlacklist | None]:
        """
        Check if an IP address is blacklisted.

        Args:
            ip_address: IP address to check

        Returns:
            Tuple of (is_blacklisted, blacklist_entry)
        """
        # Get all active blacklist entries
        result = self.db.execute(
            select(IPBlacklist).where(
                and_(
                    IPBlacklist.is_active == True,
                    IPBlacklist.expires_at.is_(None)
                    | (IPBlacklist.expires_at > datetime.utcnow()),
                )
            )
        )
        blacklists = result.scalars().all()

        for entry in blacklists:
            if self._ip_in_range(ip_address, entry.ip_address):
                # Update last hit time
                entry.last_hit_at = datetime.utcnow()
                self.db.commit()

                logger.warning(
                    f"Blocked IP: {ip_address}, reason: {entry.reason}, "
                    f"method: {entry.detection_method}"
                )
                return True, entry

        return False, None

    async def is_ip_whitelisted(
        self, ip_address: str, applies_to: str = "all"
    ) -> tuple[bool, IPWhitelist | None]:
        """
        Check if an IP address is whitelisted.

        Args:
            ip_address: IP address to check
            applies_to: Context to check (e.g., 'all', 'api_keys', 'oauth2')

        Returns:
            Tuple of (is_whitelisted, whitelist_entry)
        """
        # Get all active whitelist entries
        result = self.db.execute(
            select(IPWhitelist).where(
                and_(
                    IPWhitelist.is_active == True,
                    IPWhitelist.expires_at.is_(None)
                    | (IPWhitelist.expires_at > datetime.utcnow()),
                    (IPWhitelist.applies_to == applies_to)
                    | (IPWhitelist.applies_to == "all"),
                )
            )
        )
        whitelists = result.scalars().all()

        for entry in whitelists:
            if self._ip_in_range(ip_address, entry.ip_address):
                logger.info(f"Whitelisted IP: {ip_address}, applies_to: {applies_to}")
                return True, entry

        return False, None

    async def check_ip_allowed(
        self,
        ip_address: str,
        applies_to: str = "all",
        allowed_ips: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Comprehensive IP check: blacklist, whitelist, and optional allowed IPs.

        Args:
            ip_address: IP address to check
            applies_to: Context for whitelist check
            allowed_ips: Optional list of allowed IP ranges (for API keys)

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check blacklist first (takes precedence)
        is_blacklisted, blacklist_entry = await self.is_ip_blacklisted(ip_address)
        if is_blacklisted:
            return False, f"IP blacklisted: {blacklist_entry.reason}"

        # Check allowed IPs list (for API key restrictions)
        if allowed_ips:
            ip_allowed = any(
                self._ip_in_range(ip_address, allowed_ip) for allowed_ip in allowed_ips
            )
            if not ip_allowed:
                return False, "IP not in allowed list for this API key"

        # Check whitelist (informational, doesn't block)
        await self.is_ip_whitelisted(ip_address, applies_to)

        return True, None


class RequestSignatureValidator:
    """
    Validator for HMAC request signatures.

    Prevents replay attacks and ensures request integrity.
    """

    def __init__(self, db: Session):
        self.db = db

    def _generate_signature(
        self,
        secret: str,
        method: str,
        path: str,
        timestamp: str,
        body: str | None = None,
    ) -> str:
        """
        Generate HMAC signature for a request.

        Args:
            secret: Secret key (API key or client secret)
            method: HTTP method
            path: Request path
            timestamp: Request timestamp (ISO format)
            body: Optional request body

        Returns:
            HMAC signature (hex)
        """
        # Build signing string: METHOD\nPATH\nTIMESTAMP\nBODY
        parts = [method.upper(), path, timestamp]
        if body:
            parts.append(body)

        signing_string = "\n".join(parts)

        # Generate HMAC
        signature = hmac.new(
            secret.encode(), signing_string.encode(), hashlib.sha256
        ).hexdigest()

        return signature

    async def verify_signature(
        self,
        api_key: APIKey,
        request_data: RequestSignatureVerifyRequest,
        client_ip: str,
    ) -> tuple[bool, str | None]:
        """
        Verify HMAC signature for a request.

        Args:
            api_key: API key for signature verification
            request_data: Request signature data
            client_ip: Client IP address

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse timestamp
            request_time = datetime.fromisoformat(request_data.timestamp)

            # Check timestamp tolerance (prevent replay attacks)
            time_diff = abs((datetime.utcnow() - request_time).total_seconds())
            if time_diff > SIGNATURE_TOLERANCE_SECONDS:
                return (
                    False,
                    f"Request timestamp outside tolerance window ({SIGNATURE_TOLERANCE_SECONDS}s)",
                )

            # Check for signature replay
            signature_hash = hashlib.sha256(request_data.signature.encode()).hexdigest()
            existing = self.db.execute(
                select(RequestSignature).where(
                    RequestSignature.signature_hash == signature_hash
                )
            ).scalar_one_or_none()

            if existing:
                # Log failed verification
                self._log_verification(
                    api_key.id,
                    request_data,
                    client_ip,
                    is_valid=False,
                    failure_reason="Signature replay detected",
                )
                return False, "Signature has already been used (replay attack)"

            # Generate expected signature
            # Note: In production, you'd use the actual API key value, not the hash
            # This is a simplified example - actual implementation would need
            # to store a signing secret separately or derive it from the key
            expected_signature = self._generate_signature(
                secret=api_key.key_hash,  # In reality, use actual key or separate signing secret
                method=request_data.method,
                path=request_data.path,
                timestamp=request_data.timestamp,
                body=request_data.body,
            )

            is_valid = hmac.compare_digest(request_data.signature, expected_signature)

            # Log verification attempt
            failure_reason = None if is_valid else "Invalid signature"
            self._log_verification(
                api_key.id, request_data, client_ip, is_valid, failure_reason
            )

            return is_valid, failure_reason

        except ValueError as e:
            return False, f"Invalid timestamp format: {e}"
        except Exception as e:
            logger.error(f"Signature verification error: {e}", exc_info=True)
            return False, "Signature verification failed"

    def _log_verification(
        self,
        api_key_id: UUID,
        request_data: RequestSignatureVerifyRequest,
        client_ip: str,
        is_valid: bool,
        failure_reason: str | None = None,
    ) -> None:
        """Log signature verification attempt."""
        signature_hash = hashlib.sha256(request_data.signature.encode()).hexdigest()
        request_time = datetime.fromisoformat(request_data.timestamp)

        log_entry = RequestSignature(
            signature_hash=signature_hash,
            api_key_id=api_key_id,
            request_method=request_data.method,
            request_path=request_data.path,
            request_timestamp=request_time,
            is_valid=is_valid,
            failure_reason=failure_reason,
            client_ip=client_ip,
        )

        self.db.add(log_entry)
        self.db.commit()


class GatewayAuthenticator:
    """
    Main gateway authentication orchestrator.

    Coordinates all authentication mechanisms and provides unified validation.
    """

    def __init__(self, db: Session):
        self.db = db
        self.api_key_manager = APIKeyManager(db)
        self.oauth2_manager = OAuth2Manager(db)
        self.ip_filter_manager = IPFilterManager(db)
        self.signature_validator = RequestSignatureValidator(db)
        self.rate_limiter = RateLimiter()

    async def validate_request(
        self,
        request: Request,
        api_key: str | None = None,
        jwt_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        signature_data: RequestSignatureVerifyRequest | None = None,
    ) -> GatewayAuthValidationResponse:
        """
        Validate a request using available authentication methods.

        Priority:
        1. IP blacklist (immediate rejection)
        2. API key authentication
        3. JWT token authentication
        4. OAuth2 client credentials
        5. Request signature verification (if provided)
        6. Rate limiting

        Args:
            request: FastAPI request object
            api_key: Optional API key
            jwt_token: Optional JWT token
            client_id: Optional OAuth2 client ID
            client_secret: Optional OAuth2 client secret
            signature_data: Optional request signature data

        Returns:
            GatewayAuthValidationResponse with validation results
        """
        # Get client IP
        client_ip = self._get_client_ip(request)

        # Check IP blacklist first
        (
            is_blacklisted,
            blacklist_entry,
        ) = await self.ip_filter_manager.is_ip_blacklisted(client_ip)
        if is_blacklisted:
            logger.warning(f"Blocked blacklisted IP: {client_ip}")
            return GatewayAuthValidationResponse(
                is_valid=False, error_message=f"Access denied: {blacklist_entry.reason}"
            )

        # Try API key authentication
        if api_key:
            return await self._validate_api_key(api_key, client_ip, signature_data)

        # Try JWT token authentication
        if jwt_token:
            return await self._validate_jwt(jwt_token, client_ip)

        # Try OAuth2 client credentials
        if client_id and client_secret:
            return await self._validate_oauth2_client(
                client_id, client_secret, client_ip
            )

        # No valid authentication method provided
        return GatewayAuthValidationResponse(
            is_valid=False, error_message="No valid authentication credentials provided"
        )

    async def _validate_api_key(
        self,
        api_key: str,
        client_ip: str,
        signature_data: RequestSignatureVerifyRequest | None = None,
    ) -> GatewayAuthValidationResponse:
        """Validate API key authentication."""
        # Validate API key
        db_key = await self.api_key_manager.validate_api_key(api_key)
        if not db_key:
            return GatewayAuthValidationResponse(
                is_valid=False, auth_type="api_key", error_message="Invalid API key"
            )

        # Check IP restrictions
        allowed_ips = db_key.get_allowed_ips()
        is_allowed, reason = await self.ip_filter_manager.check_ip_allowed(
            client_ip,
            applies_to="api_keys",
            allowed_ips=allowed_ips if allowed_ips else None,
        )
        if not is_allowed:
            return GatewayAuthValidationResponse(
                is_valid=False, auth_type="api_key", error_message=reason
            )

        # Verify signature if provided
        if signature_data:
            is_valid, error = await self.signature_validator.verify_signature(
                db_key, signature_data, client_ip
            )
            if not is_valid:
                return GatewayAuthValidationResponse(
                    is_valid=False,
                    auth_type="api_key",
                    error_message=f"Signature verification failed: {error}",
                )

        # Check rate limits
        rate_limit_key = f"api_key:{db_key.id}"
        rate_limit_info = await self._check_rate_limit(
            rate_limit_key, db_key.rate_limit_per_minute, 60
        )

        if not rate_limit_info["allowed"]:
            return GatewayAuthValidationResponse(
                is_valid=False,
                auth_type="api_key",
                rate_limit_remaining=0,
                rate_limit_reset_at=rate_limit_info["reset_at"],
                error_message="Rate limit exceeded",
            )

        # Update usage statistics
        await self.api_key_manager.update_key_usage(db_key, client_ip)

        return GatewayAuthValidationResponse(
            is_valid=True,
            auth_type="api_key",
            user_id=db_key.owner_id,
            scopes=db_key.get_scopes(),
            rate_limit_remaining=rate_limit_info["remaining"],
            rate_limit_reset_at=rate_limit_info["reset_at"],
        )

    async def _validate_jwt(
        self, jwt_token: str, client_ip: str
    ) -> GatewayAuthValidationResponse:
        """Validate JWT token authentication."""
        token_data = verify_token(jwt_token, self.db)
        if not token_data or not token_data.user_id:
            return GatewayAuthValidationResponse(
                is_valid=False,
                auth_type="jwt",
                error_message="Invalid or expired JWT token",
            )

        # Check IP whitelist/blacklist
        is_allowed, reason = await self.ip_filter_manager.check_ip_allowed(
            client_ip, applies_to="all"
        )
        if not is_allowed:
            return GatewayAuthValidationResponse(
                is_valid=False, auth_type="jwt", error_message=reason
            )

        # Get user
        user = self.db.get(User, UUID(token_data.user_id))
        if not user or not user.is_active:
            return GatewayAuthValidationResponse(
                is_valid=False,
                auth_type="jwt",
                error_message="User not found or inactive",
            )

        return GatewayAuthValidationResponse(
            is_valid=True,
            auth_type="jwt",
            user_id=user.id,
            scopes=["user"],  # Could be expanded based on user roles
        )

    async def _validate_oauth2_client(
        self, client_id: str, client_secret: str, client_ip: str
    ) -> GatewayAuthValidationResponse:
        """Validate OAuth2 client credentials."""
        client = await self.oauth2_manager.authenticate_client(client_id, client_secret)
        if not client:
            return GatewayAuthValidationResponse(
                is_valid=False,
                auth_type="oauth2",
                error_message="Invalid client credentials",
            )

        # Check IP whitelist/blacklist
        is_allowed, reason = await self.ip_filter_manager.check_ip_allowed(
            client_ip, applies_to="oauth2"
        )
        if not is_allowed:
            return GatewayAuthValidationResponse(
                is_valid=False, auth_type="oauth2", error_message=reason
            )

        # Check rate limits
        rate_limit_key = f"oauth2_client:{client.id}"
        rate_limit_info = await self._check_rate_limit(
            rate_limit_key, client.rate_limit_per_minute, 60
        )

        if not rate_limit_info["allowed"]:
            return GatewayAuthValidationResponse(
                is_valid=False,
                auth_type="oauth2",
                rate_limit_remaining=0,
                rate_limit_reset_at=rate_limit_info["reset_at"],
                error_message="Rate limit exceeded",
            )

        return GatewayAuthValidationResponse(
            is_valid=True,
            auth_type="oauth2",
            user_id=client.owner_id,
            scopes=client.get_scopes(),
            rate_limit_remaining=rate_limit_info["remaining"],
            rate_limit_reset_at=rate_limit_info["reset_at"],
        )

    async def _check_rate_limit(
        self, key: str, max_requests: int | None, window_seconds: int
    ) -> dict:
        """Check rate limit for a key."""
        if max_requests is None:
            return {"allowed": True, "remaining": 999999, "reset_at": None}

        is_limited, info = self.rate_limiter.is_rate_limited(
            key=key, max_requests=max_requests, window_seconds=window_seconds
        )

        return {
            "allowed": not is_limited,
            "remaining": info.get("remaining", 0),
            "reset_at": datetime.fromtimestamp(info["reset_at"])
            if "reset_at" in info
            else None,
        }

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"


# Utility functions for FastAPI dependencies


async def get_gateway_authenticator(db: Session) -> GatewayAuthenticator:
    """Dependency to get GatewayAuthenticator instance."""
    return GatewayAuthenticator(db)


async def require_api_key(request: Request, db: Session) -> APIKey:
    """
    FastAPI dependency to require valid API key authentication.

    Usage:
        @router.get("/protected")
        async def protected_route(api_key: APIKey = Depends(require_api_key)):
            return {"message": "Authenticated with API key"}
    """
    # Extract API key from header
    api_key_header = request.headers.get("X-API-Key")
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate
    authenticator = GatewayAuthenticator(db)
    validation = await authenticator._validate_api_key(
        api_key_header, authenticator._get_client_ip(request)
    )

    if not validation.is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=validation.error_message,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Get and return the API key object
    key_hash = hashlib.sha256(api_key_header.encode()).hexdigest()
    result = db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    return result.scalar_one()
