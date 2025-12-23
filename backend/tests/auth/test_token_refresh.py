"""
Tests for token refresh service.

Tests cover:
- Token creation and storage
- Token validation and rotation
- Token revocation (individual, family, user)
- Reuse detection
- Device binding
- Concurrent session limits
- Metrics collection
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.auth.token_refresh import (
    DeviceFingerprint,
    RefreshTokenCreate,
    RefreshTokenService,
    RefreshTokenStatus,
    TokenRotationStrategy,
)


@pytest.fixture
def token_service():
    """Create a fresh token service for each test."""
    return RefreshTokenService(
        db=None,
        max_tokens_per_user=3,
        default_expiry_days=30,
        rotation_strategy=TokenRotationStrategy.ALWAYS,
        enable_device_binding=True,
        enable_reuse_detection=True,
    )


@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "user_id": str(uuid4()),
        "username": "testuser",
    }


@pytest.fixture
def device_fingerprint():
    """Sample device fingerprint."""
    return DeviceFingerprint(
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        device_id="device-123",
    )


class TestRefreshTokenCreation:
    """Test refresh token creation."""

    @pytest.mark.asyncio
    async def test_create_refresh_token(self, token_service, sample_user):
        """Test creating a basic refresh token."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
            expires_in_days=30,
        )

        token_data, token_string = await token_service.create_refresh_token(request)

        assert token_data is not None
        assert token_string is not None
        assert len(token_string) > 50  # Secure random string
        assert token_data.user_id == sample_user["user_id"]
        assert token_data.username == sample_user["username"]
        assert token_data.status == RefreshTokenStatus.ACTIVE
        assert token_data.family_id is not None
        assert token_data.token_id is not None
        assert token_data.refresh_count == 0

    @pytest.mark.asyncio
    async def test_create_with_device_binding(
        self, token_service, sample_user, device_fingerprint
    ):
        """Test creating token with device binding."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
        )

        token_data, _ = await token_service.create_refresh_token(
            request, device_fingerprint
        )

        assert token_data.device_fingerprint is not None
        assert len(token_data.device_fingerprint) == 64  # SHA-256 hex
        assert token_data.device_info["ip_address"] == device_fingerprint.ip_address
        assert token_data.device_info["user_agent"] == device_fingerprint.user_agent

    @pytest.mark.asyncio
    async def test_concurrent_token_limit(self, token_service, sample_user):
        """Test that max tokens per user is enforced."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
        )

        # Create max tokens
        tokens = []
        for _ in range(token_service.max_tokens_per_user):
            token_data, token_string = await token_service.create_refresh_token(request)
            tokens.append((token_data, token_string))

        # Verify all tokens are active
        user_tokens = token_service.get_user_tokens(sample_user["user_id"])
        active_tokens = [
            t for t in user_tokens if t.status == RefreshTokenStatus.ACTIVE
        ]
        assert len(active_tokens) == token_service.max_tokens_per_user

        # Create one more - should revoke oldest
        new_token_data, _ = await token_service.create_refresh_token(request)

        # Verify still at max
        user_tokens = token_service.get_user_tokens(sample_user["user_id"])
        active_tokens = [
            t for t in user_tokens if t.status == RefreshTokenStatus.ACTIVE
        ]
        assert len(active_tokens) == token_service.max_tokens_per_user

        # Verify new token is active
        assert new_token_data.status == RefreshTokenStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_token_family_creation(self, token_service, sample_user):
        """Test that tokens with same family_id are linked."""
        family_id = token_service._generate_family_id()

        request1 = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
            family_id=family_id,
        )

        token1_data, _ = await token_service.create_refresh_token(request1)
        assert token1_data.family_id == family_id

        request2 = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
            family_id=family_id,
            parent_token_id=token1_data.token_id,
        )

        token2_data, _ = await token_service.create_refresh_token(request2)
        assert token2_data.family_id == family_id
        assert token2_data.parent_token_id == token1_data.token_id

        # Verify family contains both tokens
        family_tokens = token_service.get_token_family(family_id)
        assert len(family_tokens) == 2


class TestTokenValidationAndRotation:
    """Test token validation and rotation."""

    @pytest.mark.asyncio
    async def test_validate_and_rotate_always(
        self, token_service, sample_user, device_fingerprint
    ):
        """Test token rotation with ALWAYS strategy."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
        )

        token_data, token_string = await token_service.create_refresh_token(
            request, device_fingerprint
        )

        # Validate and rotate
        (
            new_token_data,
            new_token_string,
            status,
        ) = await token_service.validate_and_rotate_token(
            token_string, device_fingerprint
        )

        assert status == "rotated"
        assert new_token_data is not None
        assert new_token_string is not None
        assert new_token_data.token_id != token_data.token_id
        assert new_token_data.family_id == token_data.family_id
        assert new_token_data.parent_token_id == token_data.token_id

        # Original token should be marked USED
        assert token_data.status == RefreshTokenStatus.USED

    @pytest.mark.asyncio
    async def test_validate_without_rotation(self, token_service, sample_user):
        """Test token validation without rotation (NEVER strategy)."""
        service = RefreshTokenService(
            rotation_strategy=TokenRotationStrategy.NEVER,
        )

        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
        )

        token_data, token_string = await service.create_refresh_token(request)

        # Validate without rotation
        result_data, result_string, status = await service.validate_and_rotate_token(
            token_string
        )

        assert status == "valid"
        assert result_data is not None
        assert result_string is None  # No new token
        assert result_data.token_id == token_data.token_id

    @pytest.mark.asyncio
    async def test_device_mismatch_rejection(
        self, token_service, sample_user, device_fingerprint
    ):
        """Test that device mismatch is rejected."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
        )

        token_data, token_string = await token_service.create_refresh_token(
            request, device_fingerprint
        )

        # Try to use from different device
        different_device = DeviceFingerprint(
            ip_address="10.0.0.1",  # Different IP
            user_agent="Different Browser",
            device_id="different-device",
        )

        (
            result_data,
            result_string,
            status,
        ) = await token_service.validate_and_rotate_token(
            token_string, different_device
        )

        assert result_data is None
        assert result_string is None
        assert "Device fingerprint mismatch" in status

    @pytest.mark.asyncio
    async def test_expired_token_rejection(self, token_service, sample_user):
        """Test that expired tokens are rejected."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
            expires_in_days=1,
        )

        token_data, token_string = await token_service.create_refresh_token(request)

        # Manually expire token
        token_data.expires_at = datetime.utcnow() - timedelta(hours=1)

        (
            result_data,
            result_string,
            status,
        ) = await token_service.validate_and_rotate_token(token_string)

        assert result_data is None
        assert result_string is None
        assert "expired" in status.lower()

    @pytest.mark.asyncio
    async def test_invalid_token_rejection(self, token_service):
        """Test that invalid tokens are rejected."""
        (
            result_data,
            result_string,
            status,
        ) = await token_service.validate_and_rotate_token("invalid-token")

        assert result_data is None
        assert result_string is None
        assert "not found" in status.lower()


class TestTokenReuseDetection:
    """Test token reuse detection and family revocation."""

    @pytest.mark.asyncio
    async def test_reuse_detection(self, token_service, sample_user):
        """Test that token reuse is detected and family is revoked."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
        )

        token_data, token_string = await token_service.create_refresh_token(request)
        family_id = token_data.family_id

        # First use - should rotate
        (
            new_token_data,
            new_token_string,
            status,
        ) = await token_service.validate_and_rotate_token(token_string)

        assert status == "rotated"
        assert token_data.status == RefreshTokenStatus.USED

        # Try to reuse old token - should detect and revoke family
        (
            reuse_data,
            reuse_string,
            reuse_status,
        ) = await token_service.validate_and_rotate_token(token_string)

        assert reuse_data is None
        assert reuse_string is None
        assert "reuse detected" in reuse_status.lower()

        # Verify entire family was revoked
        family_tokens = token_service.get_token_family(family_id)
        for token in family_tokens:
            assert token.status in [
                RefreshTokenStatus.FAMILY_REVOKED,
                RefreshTokenStatus.REVOKED,
            ]

    @pytest.mark.asyncio
    async def test_multi_generation_reuse(self, token_service, sample_user):
        """Test reuse detection across multiple token generations."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
        )

        # Create initial token
        token1_data, token1_string = await token_service.create_refresh_token(request)
        family_id = token1_data.family_id

        # Rotate to token2
        token2_data, token2_string, _ = await token_service.validate_and_rotate_token(
            token1_string
        )

        # Rotate to token3
        token3_data, token3_string, _ = await token_service.validate_and_rotate_token(
            token2_string
        )

        # Try to reuse token1 (already used twice ago)
        (
            reuse_data,
            reuse_string,
            reuse_status,
        ) = await token_service.validate_and_rotate_token(token1_string)

        assert reuse_data is None
        assert "reuse detected" in reuse_status.lower()

        # Verify entire family was revoked (3 tokens)
        family_tokens = token_service.get_token_family(family_id)
        assert len(family_tokens) >= 3


class TestTokenRevocation:
    """Test token revocation operations."""

    @pytest.mark.asyncio
    async def test_revoke_single_token(self, token_service, sample_user):
        """Test revoking a single token."""
        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
        )

        token_data, token_string = await token_service.create_refresh_token(request)

        # Revoke token
        success = await token_service.revoke_token(
            token_data.token_id, reason="test_revoke"
        )

        assert success is True
        assert token_data.status == RefreshTokenStatus.REVOKED
        assert token_data.metadata["revoke_reason"] == "test_revoke"

        # Try to use revoked token
        (
            result_data,
            result_string,
            status,
        ) = await token_service.validate_and_rotate_token(token_string)

        assert result_data is None
        assert "not found" in status.lower()  # Token removed from storage

    @pytest.mark.asyncio
    async def test_revoke_token_family(self, token_service, sample_user):
        """Test revoking entire token family."""
        family_id = token_service._generate_family_id()

        # Create multiple tokens in same family
        for i in range(3):
            request = RefreshTokenCreate(
                user_id=sample_user["user_id"],
                username=sample_user["username"],
                family_id=family_id,
            )
            await token_service.create_refresh_token(request)

        # Revoke family
        revoked_count = await token_service.revoke_token_family(
            family_id, reason="family_test"
        )

        assert revoked_count == 3

        # Verify all tokens revoked
        family_tokens = token_service.get_token_family(family_id)
        assert len(family_tokens) == 0  # All removed from storage

    @pytest.mark.asyncio
    async def test_revoke_user_tokens(self, token_service, sample_user):
        """Test revoking all tokens for a user."""
        # Create multiple tokens
        for i in range(3):
            request = RefreshTokenCreate(
                user_id=sample_user["user_id"],
                username=sample_user["username"],
            )
            await token_service.create_refresh_token(request)

        # Revoke all user tokens
        revoked_count = await token_service.revoke_user_tokens(sample_user["user_id"])

        assert revoked_count == 3

        # Verify no active tokens
        user_tokens = token_service.get_user_tokens(sample_user["user_id"])
        assert len(user_tokens) == 0

    @pytest.mark.asyncio
    async def test_revoke_user_tokens_except_one(self, token_service, sample_user):
        """Test revoking all user tokens except one (logout other devices)."""
        # Create 3 tokens
        tokens = []
        for i in range(3):
            request = RefreshTokenCreate(
                user_id=sample_user["user_id"],
                username=sample_user["username"],
            )
            token_data, _ = await token_service.create_refresh_token(request)
            tokens.append(token_data)

        # Keep first token, revoke others
        keep_token_id = tokens[0].token_id
        revoked_count = await token_service.revoke_user_tokens(
            sample_user["user_id"], except_token_id=keep_token_id
        )

        assert revoked_count == 2

        # Verify kept token is still active
        user_tokens = token_service.get_user_tokens(sample_user["user_id"])
        active_tokens = [
            t for t in user_tokens if t.status == RefreshTokenStatus.ACTIVE
        ]
        assert len(active_tokens) == 1
        assert active_tokens[0].token_id == keep_token_id


class TestTokenCleanup:
    """Test token cleanup operations."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_tokens(self, token_service, sample_user):
        """Test cleanup of expired tokens."""
        # Create tokens with different expiration times
        for days in [1, 2, 3]:
            request = RefreshTokenCreate(
                user_id=sample_user["user_id"],
                username=sample_user["username"],
                expires_in_days=days,
            )
            await token_service.create_refresh_token(request)

        # Manually expire first two tokens
        all_tokens = list(token_service._token_storage.values())
        all_tokens[0].expires_at = datetime.utcnow() - timedelta(hours=1)
        all_tokens[1].expires_at = datetime.utcnow() - timedelta(minutes=1)

        # Cleanup
        cleaned = await token_service.cleanup_expired_tokens()

        assert cleaned == 2

        # Verify only 1 token remains
        remaining_tokens = token_service.get_user_tokens(sample_user["user_id"])
        assert len(remaining_tokens) == 1


class TestTokenMetrics:
    """Test token metrics collection."""

    @pytest.mark.asyncio
    async def test_get_metrics(self, token_service, sample_user):
        """Test getting token metrics."""
        # Create some tokens
        for i in range(3):
            request = RefreshTokenCreate(
                user_id=sample_user["user_id"],
                username=sample_user["username"],
            )
            await token_service.create_refresh_token(request)

        metrics = token_service.get_metrics()

        assert metrics.total_active_tokens == 3
        assert metrics.tokens_created_24h == 3
        assert metrics.average_token_age_hours >= 0


class TestDeviceFingerprint:
    """Test device fingerprint generation."""

    def test_fingerprint_hash_consistency(self):
        """Test that same device generates same hash."""
        fp1 = DeviceFingerprint(
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_id="device-1",
        )
        fp2 = DeviceFingerprint(
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_id="device-1",
        )

        assert fp1.generate_hash() == fp2.generate_hash()

    def test_fingerprint_hash_difference(self):
        """Test that different devices generate different hashes."""
        fp1 = DeviceFingerprint(ip_address="192.168.1.1", user_agent="Mozilla/5.0")
        fp2 = DeviceFingerprint(ip_address="192.168.1.2", user_agent="Mozilla/5.0")

        assert fp1.generate_hash() != fp2.generate_hash()

    def test_fingerprint_hash_length(self):
        """Test that hash is SHA-256 (64 hex characters)."""
        fp = DeviceFingerprint(ip_address="192.168.1.1")
        hash_value = fp.generate_hash()

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)


class TestTokenRotationStrategies:
    """Test different token rotation strategies."""

    @pytest.mark.asyncio
    async def test_threshold_rotation(self, sample_user):
        """Test THRESHOLD rotation strategy."""
        service = RefreshTokenService(
            rotation_strategy=TokenRotationStrategy.THRESHOLD,
            rotation_threshold=0.5,  # Rotate if >50% lifetime used
            default_expiry_days=1,  # 1 day for easier testing
        )

        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
            expires_in_days=1,
        )

        token_data, token_string = await service.create_refresh_token(request)

        # Simulate time passing (>50% of lifetime)
        token_data.created_at = datetime.utcnow() - timedelta(hours=13)

        # Should rotate
        result_data, result_string, status = await service.validate_and_rotate_token(
            token_string
        )

        assert status == "rotated"
        assert result_data.token_id != token_data.token_id

    @pytest.mark.asyncio
    async def test_threshold_no_rotation(self, sample_user):
        """Test THRESHOLD strategy when threshold not met."""
        service = RefreshTokenService(
            rotation_strategy=TokenRotationStrategy.THRESHOLD,
            rotation_threshold=0.5,
            default_expiry_days=1,
        )

        request = RefreshTokenCreate(
            user_id=sample_user["user_id"],
            username=sample_user["username"],
            expires_in_days=1,
        )

        token_data, token_string = await service.create_refresh_token(request)

        # Token is fresh (<50% lifetime used)
        result_data, result_string, status = await service.validate_and_rotate_token(
            token_string
        )

        assert status == "valid"
        assert result_string is None  # No rotation
        assert result_data.token_id == token_data.token_id
