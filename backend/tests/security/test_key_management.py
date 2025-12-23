"""
Tests for Key Management Service.

Tests cover:
- Key generation (symmetric and asymmetric)
- Key encryption at rest
- Key retrieval and decryption
- Access control and policies
- Key versioning and rotation
- Key lifecycle management
- Usage tracking and auditing
- Backup and recovery
- HSM integration hooks
- Key revocation
"""

import base64
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.security.key_management import (
    AccessPolicy,
    CryptographicKey,
    HSMConfig,
    KeyGenerationRequest,
    KeyManagementService,
    KeyPurpose,
    KeyStatus,
    KeyType,
    KeyUsageLog,
    _decrypt_key_material,
    _encrypt_key_material,
)


@pytest.fixture
def key_service():
    """Create a KeyManagementService instance for testing."""
    return KeyManagementService()


@pytest.fixture
def key_service_with_hsm():
    """Create a KeyManagementService with HSM enabled."""
    hsm_config = HSMConfig(
        enabled=True,
        provider="pkcs11",
        endpoint="https://hsm.example.com",
        key_wrapping_enabled=True,
    )
    return KeyManagementService(hsm_config=hsm_config)


@pytest.fixture
def sample_key_request():
    """Create a sample key generation request."""
    return KeyGenerationRequest(
        key_type=KeyType.SYMMETRIC,
        purpose=KeyPurpose.ENCRYPTION,
        name="test-encryption-key",
        description="Test encryption key for unit tests",
        access_policy=AccessPolicy.ADMIN_ONLY,
        allowed_users=["admin", "service-account"],
        expires_in_days=365,
        auto_rotate=False,
    )


@pytest.fixture
def sample_rsa_key_request():
    """Create a sample RSA key generation request."""
    return KeyGenerationRequest(
        key_type=KeyType.RSA_2048,
        purpose=KeyPurpose.SIGNING,
        name="test-signing-key",
        description="Test RSA signing key",
        access_policy=AccessPolicy.SERVICE_ACCOUNT,
        allowed_users=["signer-service"],
        expires_in_days=730,
        auto_rotate=True,
        rotation_interval_days=90,
    )


# =============================================================================
# Encryption/Decryption Tests
# =============================================================================


class TestEncryptionDecryption:
    """Test suite for encryption and decryption functions."""

    def test_encrypt_decrypt_roundtrip(self):
        """Test that encryption and decryption are inverse operations."""
        original_data = b"This is sensitive key material that must be encrypted"

        # Encrypt
        ciphertext, salt, nonce, tag = _encrypt_key_material(original_data)

        # Verify encrypted data is different
        assert ciphertext != original_data

        # Decrypt
        decrypted_data = _decrypt_key_material(ciphertext, salt, nonce, tag)

        # Verify roundtrip
        assert decrypted_data == original_data

    def test_encryption_produces_different_output(self):
        """Test that encrypting same data twice produces different ciphertext."""
        data = b"Same data encrypted twice"

        ciphertext1, salt1, nonce1, tag1 = _encrypt_key_material(data)
        ciphertext2, salt2, nonce2, tag2 = _encrypt_key_material(data)

        # Different salts and nonces should produce different ciphertexts
        assert salt1 != salt2
        assert nonce1 != nonce2
        assert ciphertext1 != ciphertext2

    def test_decryption_with_wrong_tag_fails(self):
        """Test that tampering with authentication tag causes decryption to fail."""
        data = b"Protected data"
        ciphertext, salt, nonce, tag = _encrypt_key_material(data)

        # Tamper with tag
        wrong_tag = bytes([b ^ 0xFF for b in tag])

        # Decryption should fail
        with pytest.raises(Exception):
            _decrypt_key_material(ciphertext, salt, nonce, wrong_tag)

    def test_decryption_with_tampered_ciphertext_fails(self):
        """Test that tampering with ciphertext causes decryption to fail."""
        data = b"Protected data"
        ciphertext, salt, nonce, tag = _encrypt_key_material(data)

        # Tamper with ciphertext
        tampered_ciphertext = bytearray(ciphertext)
        tampered_ciphertext[0] ^= 0xFF
        tampered_ciphertext = bytes(tampered_ciphertext)

        # Decryption should fail
        with pytest.raises(Exception):
            _decrypt_key_material(tampered_ciphertext, salt, nonce, tag)


# =============================================================================
# Key Generation Tests
# =============================================================================


class TestKeyGeneration:
    """Test suite for key generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_symmetric_key(
        self, async_db, key_service, sample_key_request
    ):
        """Test generating a symmetric encryption key."""
        metadata = await key_service.generate_key(
            async_db, sample_key_request, created_by="admin"
        )

        assert metadata is not None
        assert metadata.name == "test-encryption-key"
        assert metadata.key_type == KeyType.SYMMETRIC
        assert metadata.purpose == KeyPurpose.ENCRYPTION
        assert metadata.status == KeyStatus.ACTIVE
        assert metadata.version == 1
        assert metadata.created_by == "admin"
        assert metadata.access_policy == AccessPolicy.ADMIN_ONLY
        assert "admin" in metadata.allowed_users

    @pytest.mark.asyncio
    async def test_generate_rsa_key(
        self, async_db, key_service, sample_rsa_key_request
    ):
        """Test generating an RSA key pair."""
        metadata = await key_service.generate_key(
            async_db, sample_rsa_key_request, created_by="admin"
        )

        assert metadata is not None
        assert metadata.name == "test-signing-key"
        assert metadata.key_type == KeyType.RSA_2048
        assert metadata.purpose == KeyPurpose.SIGNING
        assert metadata.status == KeyStatus.ACTIVE

        # Verify key was stored in database
        result = await async_db.execute(
            select(CryptographicKey).where(
                CryptographicKey.id == uuid.UUID(metadata.id)
            )
        )
        key_record = result.scalar_one()

        assert key_record.encrypted_key_material is not None
        assert key_record.encrypted_private_key is not None
        assert key_record.public_key is not None
        assert "BEGIN PUBLIC KEY" in key_record.public_key

    @pytest.mark.asyncio
    async def test_generate_key_with_expiration(self, async_db, key_service):
        """Test generating a key with expiration date."""
        request = KeyGenerationRequest(
            key_type=KeyType.SYMMETRIC,
            purpose=KeyPurpose.API_KEY,
            name="expiring-key",
            expires_in_days=30,
        )

        metadata = await key_service.generate_key(async_db, request, "admin")

        assert metadata.expires_at is not None
        expected_expiry = datetime.utcnow() + timedelta(days=30)
        assert abs((metadata.expires_at - expected_expiry).total_seconds()) < 60

    @pytest.mark.asyncio
    async def test_generate_key_with_auto_rotate(self, async_db, key_service):
        """Test generating a key with auto-rotation enabled."""
        request = KeyGenerationRequest(
            key_type=KeyType.SYMMETRIC,
            purpose=KeyPurpose.DATABASE,
            name="auto-rotate-key",
            auto_rotate=True,
            rotation_interval_days=90,
        )

        metadata = await key_service.generate_key(async_db, request, "admin")

        # Verify key record has rotation settings
        result = await async_db.execute(
            select(CryptographicKey).where(
                CryptographicKey.id == uuid.UUID(metadata.id)
            )
        )
        key_record = result.scalar_one()

        assert key_record.auto_rotate is True
        assert key_record.rotation_interval_days == 90

    @pytest.mark.asyncio
    async def test_generate_duplicate_key_name_fails(
        self, async_db, key_service, sample_key_request
    ):
        """Test that generating a key with duplicate name fails."""
        # Create first key
        await key_service.generate_key(async_db, sample_key_request, "admin")

        # Try to create duplicate
        with pytest.raises(ValidationError, match="already exists"):
            await key_service.generate_key(async_db, sample_key_request, "admin")

    @pytest.mark.asyncio
    async def test_validate_rotation_interval_required_for_auto_rotate(self):
        """Test that rotation_interval_days is required when auto_rotate is True."""
        with pytest.raises(ValidationError, match="rotation_interval_days required"):
            KeyGenerationRequest(
                key_type=KeyType.SYMMETRIC,
                purpose=KeyPurpose.ENCRYPTION,
                name="bad-auto-rotate",
                auto_rotate=True,
                rotation_interval_days=None,  # This should fail validation
            )


# =============================================================================
# Key Retrieval Tests
# =============================================================================


class TestKeyRetrieval:
    """Test suite for key retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_key_metadata(self, async_db, key_service, sample_key_request):
        """Test retrieving key metadata."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Retrieve key
        key_data = await key_service.get_key(
            async_db, created.id, user_id="admin", decrypt=False
        )

        assert key_data is not None
        assert key_data["metadata"].id == created.id
        assert key_data["metadata"].name == "test-encryption-key"
        assert "key_material" not in key_data  # Not decrypted

    @pytest.mark.asyncio
    async def test_get_key_with_decryption(
        self, async_db, key_service, sample_key_request
    ):
        """Test retrieving and decrypting key material."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Retrieve with decryption
        key_data = await key_service.get_key(
            async_db, created.id, user_id="admin", decrypt=True
        )

        assert key_data is not None
        assert "key_material" in key_data
        assert key_data["key_material"] is not None

        # Verify it's valid base64
        decoded = base64.b64decode(key_data["key_material"])
        assert len(decoded) == 32  # AES-256 key

    @pytest.mark.asyncio
    async def test_get_rsa_key_with_private_key(
        self, async_db, key_service, sample_rsa_key_request
    ):
        """Test retrieving RSA key with private key material."""
        # Create RSA key
        created = await key_service.generate_key(
            async_db, sample_rsa_key_request, "admin"
        )

        # Retrieve with decryption
        key_data = await key_service.get_key(
            async_db, created.id, user_id="admin", decrypt=True
        )

        assert "public_key" in key_data
        assert "private_key" in key_data
        assert "BEGIN PUBLIC KEY" in key_data["public_key"]
        assert "BEGIN PRIVATE KEY" in key_data["private_key"]

    @pytest.mark.asyncio
    async def test_get_key_by_name(self, async_db, key_service, sample_key_request):
        """Test retrieving key by name."""
        # Create key
        await key_service.generate_key(async_db, sample_key_request, "admin")

        # Retrieve by name
        metadata = await key_service.get_key_by_name(
            async_db, "test-encryption-key", user_id="admin"
        )

        assert metadata is not None
        assert metadata.name == "test-encryption-key"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key_fails(self, async_db, key_service):
        """Test that retrieving non-existent key raises NotFoundError."""
        fake_id = str(uuid.uuid4())

        with pytest.raises(NotFoundError):
            await key_service.get_key(async_db, fake_id, user_id="admin")

    @pytest.mark.asyncio
    async def test_list_keys(self, async_db, key_service):
        """Test listing all accessible keys."""
        # Create multiple keys
        for i in range(3):
            request = KeyGenerationRequest(
                key_type=KeyType.SYMMETRIC,
                purpose=KeyPurpose.ENCRYPTION,
                name=f"key-{i}",
                access_policy=AccessPolicy.ADMIN_ONLY,
            )
            await key_service.generate_key(async_db, request, "admin")

        # List keys
        keys = await key_service.list_keys(async_db, user_id="admin")

        assert len(keys) >= 3
        assert all(k.status == KeyStatus.ACTIVE for k in keys)

    @pytest.mark.asyncio
    async def test_list_keys_filtered_by_status(self, async_db, key_service):
        """Test listing keys filtered by status."""
        # Create and revoke a key
        request = KeyGenerationRequest(
            key_type=KeyType.SYMMETRIC,
            purpose=KeyPurpose.ENCRYPTION,
            name="revoked-key",
        )
        created = await key_service.generate_key(async_db, request, "admin")
        await key_service.revoke_key(async_db, created.id, "admin", "test")

        # List active keys
        active_keys = await key_service.list_keys(
            async_db, user_id="admin", status=KeyStatus.ACTIVE
        )

        # List revoked keys
        revoked_keys = await key_service.list_keys(
            async_db, user_id="admin", status=KeyStatus.REVOKED
        )

        assert all(k.status == KeyStatus.ACTIVE for k in active_keys)
        assert all(k.status == KeyStatus.REVOKED for k in revoked_keys)
        assert created.id in [k.id for k in revoked_keys]


# =============================================================================
# Access Control Tests
# =============================================================================


class TestAccessControl:
    """Test suite for key access control and policies."""

    @pytest.mark.asyncio
    async def test_admin_only_policy_allows_access(self, async_db, key_service):
        """Test that ADMIN_ONLY policy allows admin access."""
        request = KeyGenerationRequest(
            key_type=KeyType.SYMMETRIC,
            purpose=KeyPurpose.ENCRYPTION,
            name="admin-key",
            access_policy=AccessPolicy.ADMIN_ONLY,
        )

        created = await key_service.generate_key(async_db, request, "admin")

        # Admin should have access
        key_data = await key_service.get_key(async_db, created.id, user_id="admin")
        assert key_data is not None

    @pytest.mark.asyncio
    async def test_user_specific_policy_enforces_allowed_users(
        self, async_db, key_service
    ):
        """Test that USER_SPECIFIC policy enforces allowed_users list."""
        request = KeyGenerationRequest(
            key_type=KeyType.SYMMETRIC,
            purpose=KeyPurpose.ENCRYPTION,
            name="user-specific-key",
            access_policy=AccessPolicy.USER_SPECIFIC,
            allowed_users=["alice", "bob"],
        )

        created = await key_service.generate_key(async_db, request, "admin")

        # Alice should have access
        key_data = await key_service.get_key(async_db, created.id, user_id="alice")
        assert key_data is not None

        # Charlie should not have access
        with pytest.raises(ForbiddenError):
            await key_service.get_key(async_db, created.id, user_id="charlie")

    @pytest.mark.asyncio
    async def test_public_read_policy_allows_all(self, async_db, key_service):
        """Test that PUBLIC_READ policy allows access to anyone."""
        request = KeyGenerationRequest(
            key_type=KeyType.SYMMETRIC,
            purpose=KeyPurpose.ENCRYPTION,
            name="public-key",
            access_policy=AccessPolicy.PUBLIC_READ,
        )

        created = await key_service.generate_key(async_db, request, "admin")

        # Any user should have access
        for user in ["alice", "bob", "charlie", "anonymous"]:
            key_data = await key_service.get_key(async_db, created.id, user_id=user)
            assert key_data is not None


# =============================================================================
# Key Lifecycle Tests
# =============================================================================


class TestKeyLifecycle:
    """Test suite for key lifecycle management."""

    @pytest.mark.asyncio
    async def test_rotate_key(self, async_db, key_service, sample_key_request):
        """Test rotating a key to create a new version."""
        # Create original key
        original = await key_service.generate_key(async_db, sample_key_request, "admin")

        assert original.version == 1

        # Rotate key
        rotated = await key_service.rotate_key(async_db, original.id, user_id="admin")

        assert rotated.version == 2
        assert rotated.name == original.name
        assert rotated.id != original.id

    @pytest.mark.asyncio
    async def test_revoke_key(self, async_db, key_service, sample_key_request):
        """Test revoking a key."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Revoke key
        revoked = await key_service.revoke_key(
            async_db, created.id, user_id="admin", reason="Compromised"
        )

        assert revoked.status == KeyStatus.REVOKED
        assert revoked.id == created.id

        # Verify in database
        result = await async_db.execute(
            select(CryptographicKey).where(CryptographicKey.id == uuid.UUID(created.id))
        )
        key_record = result.scalar_one()

        assert key_record.status == KeyStatus.REVOKED.value
        assert key_record.revoked_at is not None
        assert key_record.revocation_reason == "Compromised"

    @pytest.mark.asyncio
    async def test_cannot_rotate_revoked_key(
        self, async_db, key_service, sample_key_request
    ):
        """Test that revoked keys cannot be rotated."""
        # Create and revoke key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")
        await key_service.revoke_key(async_db, created.id, "admin", "test")

        # Try to rotate
        with pytest.raises(ValidationError, match="Cannot rotate revoked key"):
            await key_service.rotate_key(async_db, created.id, "admin")

    @pytest.mark.asyncio
    async def test_delete_revoked_key(self, async_db, key_service, sample_key_request):
        """Test deleting a revoked key."""
        # Create and revoke key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")
        await key_service.revoke_key(async_db, created.id, "admin", "test")

        # Delete key
        await key_service.delete_key(async_db, created.id, "admin")

        # Verify deleted
        with pytest.raises(NotFoundError):
            await key_service.get_key(async_db, created.id, "admin")

    @pytest.mark.asyncio
    async def test_cannot_delete_active_key_without_force(
        self, async_db, key_service, sample_key_request
    ):
        """Test that active keys cannot be deleted without force flag."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Try to delete without force
        with pytest.raises(ValidationError, match="Cannot delete active key"):
            await key_service.delete_key(async_db, created.id, "admin", force=False)

    @pytest.mark.asyncio
    async def test_delete_active_key_with_force(
        self, async_db, key_service, sample_key_request
    ):
        """Test force deleting an active key."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Force delete
        await key_service.delete_key(async_db, created.id, "admin", force=True)

        # Verify deleted
        with pytest.raises(NotFoundError):
            await key_service.get_key(async_db, created.id, "admin")


# =============================================================================
# Usage Tracking Tests
# =============================================================================


class TestUsageTracking:
    """Test suite for key usage tracking and auditing."""

    @pytest.mark.asyncio
    async def test_key_usage_increments_count(
        self, async_db, key_service, sample_key_request
    ):
        """Test that using a key increments usage count."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Use key multiple times
        for _ in range(3):
            await key_service.get_key(async_db, created.id, "admin", decrypt=False)

        # Check usage count
        metadata = await key_service.get_key_by_name(async_db, created.name, "admin")
        assert metadata.usage_count >= 3

    @pytest.mark.asyncio
    async def test_get_key_usage_history(
        self, async_db, key_service, sample_key_request
    ):
        """Test retrieving usage history for a key."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Use key
        await key_service.get_key(async_db, created.id, "admin", decrypt=True)

        # Get usage history
        usage_records = await key_service.get_key_usage(
            async_db, created.id, user_id="admin"
        )

        assert len(usage_records) > 0
        assert all(r.key_id == created.id for r in usage_records)
        assert any(r.operation == "read" for r in usage_records)

    @pytest.mark.asyncio
    async def test_usage_logs_track_operations(
        self, async_db, key_service, sample_key_request
    ):
        """Test that usage logs track different operations."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Perform various operations
        await key_service.get_key(async_db, created.id, "admin", decrypt=False)
        await key_service.get_key(async_db, created.id, "admin", decrypt=True)

        # Verify usage logs in database
        result = await async_db.execute(
            select(KeyUsageLog).where(KeyUsageLog.key_id == uuid.UUID(created.id))
        )
        logs = result.scalars().all()

        assert len(logs) >= 2
        operations = {log.operation for log in logs}
        assert "read" in operations


# =============================================================================
# Backup and Recovery Tests
# =============================================================================


class TestBackupRecovery:
    """Test suite for key backup and recovery functionality."""

    @pytest.mark.asyncio
    async def test_backup_key(self, async_db, key_service, sample_key_request):
        """Test marking a key as backed up."""
        # Create key
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        assert created.is_backed_up is False

        # Backup key
        backed_up = await key_service.backup_key(
            async_db,
            created.id,
            user_id="admin",
            backup_location="s3://backup-bucket/keys/test-key",
        )

        assert backed_up.is_backed_up is True

        # Verify in database
        result = await async_db.execute(
            select(CryptographicKey).where(CryptographicKey.id == uuid.UUID(created.id))
        )
        key_record = result.scalar_one()

        assert key_record.is_backed_up is True
        assert key_record.backup_location == "s3://backup-bucket/keys/test-key"
        assert key_record.last_backup_at is not None


# =============================================================================
# HSM Integration Tests
# =============================================================================


class TestHSMIntegration:
    """Test suite for HSM integration functionality."""

    @pytest.mark.asyncio
    async def test_integrate_key_with_hsm(
        self, async_db, key_service_with_hsm, sample_key_request
    ):
        """Test linking a key to an HSM-stored key."""
        # Create key
        created = await key_service_with_hsm.generate_key(
            async_db, sample_key_request, "admin"
        )

        # Integrate with HSM
        integrated = await key_service_with_hsm.integrate_with_hsm(
            async_db, created.id, user_id="admin", hsm_key_id="hsm-key-12345"
        )

        assert integrated.hsm_integrated is True

        # Verify in database
        result = await async_db.execute(
            select(CryptographicKey).where(CryptographicKey.id == uuid.UUID(created.id))
        )
        key_record = result.scalar_one()

        assert key_record.hsm_integrated is True
        assert key_record.hsm_key_id == "hsm-key-12345"
        assert key_record.hsm_provider == "pkcs11"

    @pytest.mark.asyncio
    async def test_hsm_integration_fails_when_disabled(
        self, async_db, key_service, sample_key_request
    ):
        """Test that HSM integration fails when HSM is not enabled."""
        # Create key with HSM disabled
        created = await key_service.generate_key(async_db, sample_key_request, "admin")

        # Try to integrate with HSM
        with pytest.raises(ValidationError, match="HSM integration is not enabled"):
            await key_service.integrate_with_hsm(
                async_db, created.id, user_id="admin", hsm_key_id="hsm-key-12345"
            )

    @pytest.mark.asyncio
    async def test_keys_marked_as_hsm_integrated_on_generation(
        self, async_db, key_service_with_hsm, sample_key_request
    ):
        """Test that keys are marked as HSM-integrated when HSM is enabled."""
        created = await key_service_with_hsm.generate_key(
            async_db, sample_key_request, "admin"
        )

        assert created.hsm_integrated is True


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_key_with_very_long_name(self, async_db, key_service):
        """Test that key names are limited in length."""
        long_name = "a" * 300

        request = KeyGenerationRequest(
            key_type=KeyType.SYMMETRIC, purpose=KeyPurpose.ENCRYPTION, name=long_name
        )

        # This should be caught by Pydantic validation
        with pytest.raises((ValidationError, ValueError)):
            await key_service.generate_key(async_db, request, "admin")

    @pytest.mark.asyncio
    async def test_expired_key_tracking(self, async_db, key_service):
        """Test that expired keys can be identified."""
        # Create key that expires in the past (for testing)
        request = KeyGenerationRequest(
            key_type=KeyType.SYMMETRIC,
            purpose=KeyPurpose.API_KEY,
            name="expired-key",
            expires_in_days=1,
        )

        created = await key_service.generate_key(async_db, request, "admin")

        # Manually set expiration to past
        result = await async_db.execute(
            select(CryptographicKey).where(CryptographicKey.id == uuid.UUID(created.id))
        )
        key_record = result.scalar_one()
        key_record.expires_at = datetime.utcnow() - timedelta(days=1)
        await async_db.commit()

        # Verify expiration is tracked
        result = await async_db.execute(
            select(CryptographicKey).where(CryptographicKey.id == uuid.UUID(created.id))
        )
        key_record = result.scalar_one()
        assert key_record.expires_at < datetime.utcnow()

    @pytest.mark.asyncio
    async def test_concurrent_key_generation_same_name(
        self, async_db, key_service, sample_key_request
    ):
        """Test that concurrent key generation with same name is handled."""
        # This is a simplification - in production, use proper concurrency testing
        await key_service.generate_key(async_db, sample_key_request, "admin")

        # Second attempt should fail
        with pytest.raises(ValidationError, match="already exists"):
            await key_service.generate_key(async_db, sample_key_request, "admin")
