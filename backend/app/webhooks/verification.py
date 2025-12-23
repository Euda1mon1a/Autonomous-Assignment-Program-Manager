"""Webhook verification service for incoming webhooks.

Provides comprehensive verification for incoming webhook requests including:
- HMAC signature verification with multiple algorithms
- Timestamp validation to prevent replay attacks
- IP whitelist validation
- Retry detection
- Payload integrity verification
- Comprehensive failure logging

This service is designed for verifying webhooks RECEIVED by the application
from external services (e.g., payment processors, third-party integrations).
"""

import hashlib
import hmac
import ipaddress
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.webhooks.models import Webhook, WebhookDelivery

logger = logging.getLogger(__name__)
settings = get_settings()


class SignatureAlgorithm(str, Enum):
    """Supported signature algorithms for webhook verification."""

    SHA256 = "sha256"
    SHA512 = "sha512"
    SHA1 = "sha1"  # Legacy support only, not recommended


class VerificationResult:
    """Result of webhook verification with detailed failure information."""

    def __init__(
        self,
        valid: bool,
        failure_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize verification result.

        Args:
            valid: Whether verification succeeded
            failure_reason: Detailed reason for failure (if any)
            metadata: Additional verification metadata
        """
        self.valid = valid
        self.failure_reason = failure_reason
        self.metadata = metadata or {}
        self.verified_at = datetime.utcnow()

    def __bool__(self) -> bool:
        """Allow boolean evaluation of verification result."""
        return self.valid

    def __repr__(self) -> str:
        """String representation of verification result."""
        if self.valid:
            return "<VerificationResult: VALID>"
        return f"<VerificationResult: INVALID - {self.failure_reason}>"


class WebhookVerificationService:
    """
    Comprehensive webhook verification service for incoming webhooks.

    Provides multi-layered security verification including signature validation,
    timestamp checking, IP whitelisting, and retry detection.
    """

    def __init__(
        self,
        timestamp_tolerance_seconds: int | None = None,
        enable_ip_whitelist: bool = True,
        enable_retry_detection: bool = True,
        max_payload_size_bytes: int = 1048576,  # 1MB default
    ):
        """
        Initialize webhook verification service.

        Args:
            timestamp_tolerance_seconds: Maximum age for webhook requests.
                Defaults to WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS from config.
            enable_ip_whitelist: Enable IP whitelist validation
            enable_retry_detection: Enable duplicate delivery detection
            max_payload_size_bytes: Maximum allowed payload size
        """
        self.timestamp_tolerance = (
            timestamp_tolerance_seconds or settings.WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS
        )
        self.enable_ip_whitelist = enable_ip_whitelist
        self.enable_retry_detection = enable_retry_detection
        self.max_payload_size = max_payload_size_bytes

    # =========================================================================
    # Main Verification Methods
    # =========================================================================

    async def verify_webhook(
        self,
        request: Request,
        db: AsyncSession,
        webhook_id: UUID | None = None,
        secret: str | None = None,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.SHA256,
        ip_whitelist: list[str] | None = None,
        required_headers: list[str] | None = None,
    ) -> VerificationResult:
        """
        Perform comprehensive webhook verification.

        Args:
            request: FastAPI request object
            db: Database session for retry detection
            webhook_id: Optional webhook ID for database lookup
            secret: Shared secret for verification (required if webhook_id not provided)
            algorithm: Signature algorithm to use
            ip_whitelist: List of allowed IP addresses/CIDR ranges
            required_headers: List of required header names

        Returns:
            VerificationResult with validation status and details

        Example:
            >>> service = WebhookVerificationService()
            >>> result = await service.verify_webhook(
            ...     request,
            ...     db,
            ...     secret="my-webhook-secret"
            ... )
            >>> if result:
            ...     # Process webhook
            ...     pass
            >>> else:
            ...     logger.warning(f"Verification failed: {result.failure_reason}")
        """
        # Step 1: Validate IP address if whitelist enabled
        if self.enable_ip_whitelist and ip_whitelist:
            ip_result = self._verify_ip_address(request, ip_whitelist)
            if not ip_result:
                logger.warning(
                    f"Webhook IP verification failed from {request.client.host}: "
                    f"{ip_result.failure_reason}"
                )
                return ip_result

        # Step 2: Validate required headers
        if required_headers:
            headers_result = self._verify_required_headers(request, required_headers)
            if not headers_result:
                logger.warning(
                    f"Webhook missing required headers: {headers_result.failure_reason}"
                )
                return headers_result

        # Step 3: Extract and parse payload
        try:
            body = await request.body()
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError as e:
            logger.warning(f"Webhook payload JSON decode error: {e}")
            return VerificationResult(False, f"Invalid JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error reading webhook payload: {e}", exc_info=True)
            return VerificationResult(False, f"Error reading payload: {e}")

        # Step 4: Validate payload size
        payload_size = len(body) if body else 0
        if payload_size > self.max_payload_size:
            logger.warning(
                f"Webhook payload too large: {payload_size} bytes > "
                f"{self.max_payload_size} bytes"
            )
            return VerificationResult(
                False,
                f"Payload too large: {payload_size} bytes exceeds maximum {self.max_payload_size}",
            )

        # Step 5: Load webhook secret if webhook_id provided
        if webhook_id and not secret:
            webhook = await self._get_webhook(db, webhook_id)
            if not webhook:
                logger.warning(f"Webhook {webhook_id} not found")
                return VerificationResult(False, f"Webhook {webhook_id} not found")
            secret = webhook.secret

        if not secret:
            logger.error("No secret provided for webhook verification")
            return VerificationResult(False, "No secret available for verification")

        # Step 6: Extract signature and timestamp from headers
        signature = request.headers.get("X-Webhook-Signature") or request.headers.get(
            "X-Hub-Signature-256"
        )
        timestamp_str = request.headers.get("X-Webhook-Timestamp")

        if not signature:
            logger.warning("Webhook request missing signature header")
            return VerificationResult(False, "Missing signature header")

        if not timestamp_str:
            logger.warning("Webhook request missing timestamp header")
            return VerificationResult(False, "Missing timestamp header")

        # Step 7: Parse timestamp
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp_str}")
            return VerificationResult(
                False, f"Invalid timestamp format: {timestamp_str}"
            )

        # Step 8: Verify timestamp freshness
        timestamp_result = self._verify_timestamp(timestamp)
        if not timestamp_result:
            logger.warning(
                f"Webhook timestamp verification failed: {timestamp_result.failure_reason}"
            )
            return timestamp_result

        # Step 9: Verify signature
        signature_result = self._verify_signature(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            secret=secret,
            algorithm=algorithm,
        )

        if not signature_result:
            logger.warning(
                f"Webhook signature verification failed: {signature_result.failure_reason}"
            )
            return signature_result

        # Step 10: Detect retries/duplicates if enabled
        if self.enable_retry_detection:
            delivery_id = request.headers.get("X-Webhook-Delivery")
            if delivery_id:
                retry_result = await self._detect_retry(db, delivery_id)
                if not retry_result:
                    logger.info(f"Duplicate webhook delivery detected: {delivery_id}")
                    # Note: We don't fail on duplicate, just log it
                    signature_result.metadata["is_retry"] = True
                    signature_result.metadata["retry_info"] = retry_result.metadata

        # Step 11: All checks passed
        logger.info(
            f"Webhook verification successful from {request.client.host} "
            f"(payload_size={payload_size} bytes)"
        )

        return VerificationResult(
            True,
            metadata={
                "timestamp": timestamp,
                "algorithm": algorithm.value,
                "payload_size": payload_size,
                "client_ip": request.client.host if request.client else None,
            },
        )

    async def verify_and_raise(
        self, request: Request, db: AsyncSession, **kwargs
    ) -> dict[str, Any]:
        """
        Verify webhook and raise HTTPException on failure.

        Convenience method for use in FastAPI route handlers.

        Args:
            request: FastAPI request object
            db: Database session
            **kwargs: Additional arguments passed to verify_webhook

        Returns:
            Parsed payload dictionary if verification succeeds

        Raises:
            HTTPException: If verification fails

        Example:
            >>> @app.post("/webhooks/stripe")
            >>> async def stripe_webhook(
            ...     request: Request,
            ...     db: AsyncSession = Depends(get_db)
            ... ):
            ...     service = WebhookVerificationService()
            ...     payload = await service.verify_and_raise(
            ...         request, db, secret=settings.STRIPE_WEBHOOK_SECRET
            ...     )
            ...     # Process verified webhook
            ...     return {"status": "ok"}
        """
        result = await self.verify_webhook(request, db, **kwargs)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Webhook verification failed: {result.failure_reason}",
            )

        # Extract payload from request
        body = await request.body()
        return json.loads(body) if body else {}

    # =========================================================================
    # Individual Verification Methods
    # =========================================================================

    def _verify_signature(
        self,
        payload: dict[str, Any],
        signature: str,
        timestamp: int,
        secret: str,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.SHA256,
    ) -> VerificationResult:
        """
        Verify HMAC signature for webhook payload.

        Args:
            payload: Webhook payload dictionary
            signature: Signature from header (format: "sha256=<hex>" or just "<hex>")
            timestamp: Unix timestamp
            secret: Shared secret
            algorithm: Signature algorithm

        Returns:
            VerificationResult indicating success or failure
        """
        try:
            # Generate expected signature
            expected_sig = self._generate_signature(
                payload, timestamp, secret, algorithm
            )

            # Normalize signature format (remove algorithm prefix if present)
            signature_value = signature
            if "=" in signature:
                sig_algo, signature_value = signature.split("=", 1)
                # Validate algorithm matches
                if sig_algo != algorithm.value:
                    return VerificationResult(
                        False,
                        f"Algorithm mismatch: expected {algorithm.value}, got {sig_algo}",
                    )

            # Constant-time comparison to prevent timing attacks
            if not hmac.compare_digest(signature_value, expected_sig):
                return VerificationResult(
                    False, "Signature mismatch - invalid secret or tampered payload"
                )

            return VerificationResult(True, metadata={"algorithm": algorithm.value})

        except Exception as e:
            logger.error(f"Error verifying signature: {e}", exc_info=True)
            return VerificationResult(False, f"Signature verification error: {e}")

    def _verify_timestamp(self, timestamp: int) -> VerificationResult:
        """
        Verify timestamp is within acceptable tolerance window.

        Prevents replay attacks by rejecting old webhook requests.

        Args:
            timestamp: Unix timestamp from webhook

        Returns:
            VerificationResult indicating if timestamp is fresh
        """
        try:
            current_time = int(datetime.utcnow().timestamp())
            time_diff = abs(current_time - timestamp)

            if time_diff > self.timestamp_tolerance:
                return VerificationResult(
                    False,
                    f"Timestamp outside tolerance: {time_diff}s > {self.timestamp_tolerance}s "
                    f"(potential replay attack)",
                )

            # Calculate when the webhook was sent
            webhook_time = datetime.fromtimestamp(timestamp)

            return VerificationResult(
                True,
                metadata={
                    "timestamp": timestamp,
                    "age_seconds": time_diff,
                    "webhook_time": webhook_time.isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Error verifying timestamp: {e}", exc_info=True)
            return VerificationResult(False, f"Timestamp verification error: {e}")

    def _verify_ip_address(
        self, request: Request, ip_whitelist: list[str]
    ) -> VerificationResult:
        """
        Verify request originates from whitelisted IP address.

        Supports both individual IPs and CIDR notation.

        Args:
            request: FastAPI request object
            ip_whitelist: List of allowed IPs or CIDR ranges

        Returns:
            VerificationResult indicating if IP is whitelisted

        Example:
            >>> ip_whitelist = ["192.168.1.100", "10.0.0.0/8", "172.16.0.0/12"]
        """
        if not request.client:
            return VerificationResult(False, "Unable to determine client IP address")

        client_ip = request.client.host

        try:
            client_addr = ipaddress.ip_address(client_ip)

            for allowed in ip_whitelist:
                try:
                    # Check if CIDR notation
                    if "/" in allowed:
                        network = ipaddress.ip_network(allowed, strict=False)
                        if client_addr in network:
                            return VerificationResult(
                                True,
                                metadata={
                                    "client_ip": client_ip,
                                    "matched_network": allowed,
                                },
                            )
                    else:
                        # Individual IP comparison
                        allowed_addr = ipaddress.ip_address(allowed)
                        if client_addr == allowed_addr:
                            return VerificationResult(
                                True,
                                metadata={
                                    "client_ip": client_ip,
                                    "matched_ip": allowed,
                                },
                            )
                except ValueError as e:
                    logger.warning(f"Invalid IP in whitelist: {allowed} - {e}")
                    continue

            return VerificationResult(False, f"IP address {client_ip} not in whitelist")

        except ValueError as e:
            logger.warning(f"Invalid client IP address: {client_ip} - {e}")
            return VerificationResult(False, f"Invalid client IP: {client_ip}")

    def _verify_required_headers(
        self, request: Request, required_headers: list[str]
    ) -> VerificationResult:
        """
        Verify all required headers are present in request.

        Args:
            request: FastAPI request object
            required_headers: List of required header names (case-insensitive)

        Returns:
            VerificationResult indicating if all headers present
        """
        missing_headers = []

        # Convert to lowercase for case-insensitive comparison
        request_headers = {k.lower(): v for k, v in request.headers.items()}

        for required in required_headers:
            if required.lower() not in request_headers:
                missing_headers.append(required)

        if missing_headers:
            return VerificationResult(
                False, f"Missing required headers: {', '.join(missing_headers)}"
            )

        return VerificationResult(True)

    async def _detect_retry(
        self, db: AsyncSession, delivery_id: str
    ) -> VerificationResult:
        """
        Detect if webhook delivery is a retry (duplicate).

        Args:
            db: Database session
            delivery_id: Unique delivery identifier from X-Webhook-Delivery header

        Returns:
            VerificationResult indicating if this is first delivery
        """
        try:
            # Check if we've seen this delivery ID before
            result = await db.execute(
                select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
            )
            existing_delivery = result.scalar_one_or_none()

            if existing_delivery:
                return VerificationResult(
                    False,
                    "Duplicate delivery detected (retry)",
                    metadata={
                        "delivery_id": delivery_id,
                        "original_attempt_at": existing_delivery.first_attempted_at.isoformat()
                        if existing_delivery.first_attempted_at
                        else None,
                        "attempt_count": existing_delivery.attempt_count,
                    },
                )

            return VerificationResult(True, metadata={"delivery_id": delivery_id})

        except Exception as e:
            logger.error(f"Error detecting retry for {delivery_id}: {e}", exc_info=True)
            # Don't fail verification on retry detection errors
            return VerificationResult(True, metadata={"retry_detection_error": str(e)})

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _generate_signature(
        self,
        payload: dict[str, Any],
        timestamp: int,
        secret: str,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.SHA256,
    ) -> str:
        """
        Generate HMAC signature for comparison.

        Args:
            payload: Webhook payload dictionary
            timestamp: Unix timestamp
            secret: Shared secret
            algorithm: Hash algorithm to use

        Returns:
            Hex-encoded HMAC signature (without algorithm prefix)
        """
        # Create signing string: timestamp.payload_json
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signing_string = f"{timestamp}.{payload_json}"

        # Select hash algorithm
        hash_func = {
            SignatureAlgorithm.SHA256: hashlib.sha256,
            SignatureAlgorithm.SHA512: hashlib.sha512,
            SignatureAlgorithm.SHA1: hashlib.sha1,
        }.get(algorithm, hashlib.sha256)

        # Generate HMAC
        signature = hmac.new(
            secret.encode("utf-8"), signing_string.encode("utf-8"), hash_func
        ).hexdigest()

        return signature

    async def _get_webhook(self, db: AsyncSession, webhook_id: UUID) -> Webhook | None:
        """
        Retrieve webhook configuration from database.

        Args:
            db: Database session
            webhook_id: Webhook UUID

        Returns:
            Webhook model or None if not found
        """
        try:
            result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching webhook {webhook_id}: {e}", exc_info=True)
            return None

    # =========================================================================
    # Secret Management
    # =========================================================================

    @staticmethod
    def generate_webhook_secret(length: int = 32) -> str:
        """
        Generate a cryptographically secure webhook secret.

        Args:
            length: Length of secret in bytes (default: 32)

        Returns:
            URL-safe base64-encoded secret string

        Example:
            >>> secret = WebhookVerificationService.generate_webhook_secret()
            >>> len(secret) >= 32
            True
        """
        import secrets

        return secrets.token_urlsafe(length)

    @staticmethod
    def rotate_webhook_secret(
        old_secret: str, verify_with_both: bool = True, grace_period_hours: int = 24
    ) -> tuple[str, dict[str, Any]]:
        """
        Generate new webhook secret and return rotation metadata.

        During secret rotation, you can verify webhooks with both old and new
        secrets for a grace period.

        Args:
            old_secret: Current webhook secret
            verify_with_both: Allow both old and new secrets during transition
            grace_period_hours: Hours to allow old secret (if verify_with_both=True)

        Returns:
            Tuple of (new_secret, rotation_metadata)

        Example:
            >>> new_secret, metadata = WebhookVerificationService.rotate_webhook_secret(
            ...     "old-secret",
            ...     verify_with_both=True,
            ...     grace_period_hours=24
            ... )
            >>> metadata["old_secret_valid_until"]  # datetime when old secret expires
        """
        import secrets

        new_secret = secrets.token_urlsafe(32)

        metadata = {
            "rotated_at": datetime.utcnow().isoformat(),
            "old_secret_hash": hashlib.sha256(old_secret.encode()).hexdigest()[:16],
            "verify_with_both": verify_with_both,
        }

        if verify_with_both:
            valid_until = datetime.utcnow() + timedelta(hours=grace_period_hours)
            metadata["old_secret_valid_until"] = valid_until.isoformat()
            metadata["grace_period_hours"] = grace_period_hours

        return new_secret, metadata

    # =========================================================================
    # Logging and Monitoring
    # =========================================================================

    def log_verification_failure(
        self,
        request: Request,
        result: VerificationResult,
        additional_context: dict[str, Any] | None = None,
    ) -> None:
        """
        Log detailed information about verification failure.

        Args:
            request: FastAPI request object
            result: Failed verification result
            additional_context: Additional context to include in log
        """
        context = additional_context or {}

        log_data = {
            "reason": result.failure_reason,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "path": request.url.path,
            "method": request.method,
            "timestamp": datetime.utcnow().isoformat(),
            **context,
            **result.metadata,
        }

        logger.warning(
            f"Webhook verification failed: {result.failure_reason}",
            extra={"webhook_verification": log_data},
        )

        # Optional: Send to monitoring/alerting system
        # This could trigger alerts for potential security issues
        if "replay attack" in result.failure_reason.lower():
            logger.critical(
                f"Potential replay attack detected from {log_data['client_ip']}",
                extra={"security_alert": log_data},
            )
