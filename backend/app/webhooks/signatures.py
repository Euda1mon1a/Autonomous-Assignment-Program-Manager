"""Webhook signature generation and verification.

Implements HMAC-SHA256 signing for webhook payloads to ensure
authenticity and prevent tampering.

Signature format follows GitHub/Stripe webhook standards:
    X-Webhook-Signature: sha256=<hex-encoded-hmac>
    X-Webhook-Timestamp: <unix-timestamp>
"""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any


class WebhookSignatureGenerator:
    """
    Generates and verifies HMAC-SHA256 signatures for webhook payloads.

    Uses a shared secret to sign payloads, preventing replay attacks
    and ensuring payload integrity.
    """

    SIGNATURE_HEADER = "X-Webhook-Signature"
    TIMESTAMP_HEADER = "X-Webhook-Timestamp"
    EVENT_TYPE_HEADER = "X-Webhook-Event"
    DELIVERY_ID_HEADER = "X-Webhook-Delivery"

    def __init__(self, timestamp_tolerance_seconds: int = 300):
        """
        Initialize the signature generator.

        Args:
            timestamp_tolerance_seconds: Maximum age of webhook requests to accept.
                Defaults to 300 seconds (5 minutes) to prevent replay attacks.
        """
        self.timestamp_tolerance_seconds = timestamp_tolerance_seconds

    def generate_signature(
        self, payload: dict[str, Any], secret: str, timestamp: int | None = None
    ) -> tuple[str, int]:
        """
        Generate HMAC-SHA256 signature for a webhook payload.

        Args:
            payload: Webhook payload dictionary
            secret: Shared secret for signing
            timestamp: Unix timestamp (defaults to current time)

        Returns:
            Tuple of (signature, timestamp)

        Example:
            >>> generator = WebhookSignatureGenerator()
            >>> payload = {"event": "schedule.created", "data": {"id": "123"}}
            >>> signature, timestamp = generator.generate_signature(payload, "my-secret")
            >>> signature.startswith("sha256=")
            True
        """
        if timestamp is None:
            timestamp = int(datetime.utcnow().timestamp())

        # Create signing string: timestamp.payload_json
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        signing_string = f"{timestamp}.{payload_json}"

        # Generate HMAC-SHA256 signature
        signature_bytes = hmac.new(
            secret.encode("utf-8"), signing_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return f"sha256={signature_bytes}", timestamp

    def verify_signature(
        self, payload: dict[str, Any], signature: str, timestamp: int, secret: str
    ) -> bool:
        """
        Verify HMAC-SHA256 signature for a webhook payload.

        Args:
            payload: Webhook payload dictionary
            signature: Signature to verify (format: "sha256=<hex>")
            timestamp: Unix timestamp from request
            secret: Shared secret for verification

        Returns:
            True if signature is valid and timestamp is fresh, False otherwise

        Raises:
            ValueError: If timestamp is outside tolerance window
        """
        # Check timestamp freshness (prevent replay attacks)
        current_timestamp = int(datetime.utcnow().timestamp())
        timestamp_diff = abs(current_timestamp - timestamp)

        if timestamp_diff > self.timestamp_tolerance_seconds:
            raise ValueError(
                f"Timestamp outside tolerance window: "
                f"{timestamp_diff}s > {self.timestamp_tolerance_seconds}s"
            )

        # Generate expected signature
        expected_signature, _ = self.generate_signature(payload, secret, timestamp)

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)

    def generate_headers(
        self, payload: dict[str, Any], secret: str, event_type: str, delivery_id: str
    ) -> dict[str, str]:
        """
        Generate all webhook headers including signature.

        Args:
            payload: Webhook payload dictionary
            secret: Shared secret for signing
            event_type: Event type (e.g., "schedule.created")
            delivery_id: Unique delivery identifier

        Returns:
            Dictionary of headers to include in webhook request

        Example:
            >>> generator = WebhookSignatureGenerator()
            >>> headers = generator.generate_headers(
            ...     {"data": "test"},
            ...     "secret",
            ...     "test.event",
            ...     "delivery-123"
            ... )
            >>> "X-Webhook-Signature" in headers
            True
        """
        signature, timestamp = self.generate_signature(payload, secret)

        return {
            self.SIGNATURE_HEADER: signature,
            self.TIMESTAMP_HEADER: str(timestamp),
            self.EVENT_TYPE_HEADER: event_type,
            self.DELIVERY_ID_HEADER: delivery_id,
            "Content-Type": "application/json",
            "User-Agent": "Residency-Scheduler-Webhook/1.0",
        }

    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """
        Compare two strings in constant time to prevent timing attacks.

        This is a wrapper around hmac.compare_digest for backwards compatibility.

        Args:
            a: First string
            b: Second string

        Returns:
            True if strings are equal, False otherwise
        """
        return hmac.compare_digest(a, b)
