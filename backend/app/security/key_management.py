"""
Key Management Service for the Residency Scheduler backend.

This service provides enterprise-grade cryptographic key management including:
- Key generation (symmetric and asymmetric)
- Secure key storage with encryption at rest
- Key versioning and lifecycle management
- Key usage tracking and auditing
- Key access policies and RBAC
- Hardware Security Module (HSM) integration hooks
- Key backup and recovery mechanisms
- Key revocation and rotation handling

Security: All keys are encrypted at rest using a master key derived from settings.
Audit: All key operations are logged for compliance and security auditing.
"""
import base64
import json
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.db.base import Base
from app.db.types import GUID, JSONType

logger = logging.getLogger(__name__)
settings = get_settings()


# =============================================================================
# Enums and Constants
# =============================================================================

class KeyType(str, Enum):
    """Types of cryptographic keys."""
    SYMMETRIC = "symmetric"
    RSA_2048 = "rsa_2048"
    RSA_4096 = "rsa_4096"
    EC_P256 = "ec_p256"
    EC_P384 = "ec_p384"


class KeyPurpose(str, Enum):
    """Purpose/usage of cryptographic keys."""
    ENCRYPTION = "encryption"
    SIGNING = "signing"
    JWT = "jwt"
    API_KEY = "api_key"
    DATABASE = "database"
    BACKUP = "backup"
    HSM_WRAPPING = "hsm_wrapping"


class KeyStatus(str, Enum):
    """Lifecycle status of keys."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ROTATING = "rotating"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING_DELETION = "pending_deletion"


class AccessPolicy(str, Enum):
    """Access control policies for keys."""
    ADMIN_ONLY = "admin_only"
    SERVICE_ACCOUNT = "service_account"
    APPLICATION = "application"
    USER_SPECIFIC = "user_specific"
    PUBLIC_READ = "public_read"


# =============================================================================
# Pydantic Schemas
# =============================================================================

class KeyGenerationRequest(BaseModel):
    """Request schema for generating a new key."""
    key_type: KeyType
    purpose: KeyPurpose
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    access_policy: AccessPolicy = AccessPolicy.ADMIN_ONLY
    allowed_users: list[str] = Field(default_factory=list)
    expires_in_days: Optional[int] = Field(None, ge=1, le=3650)
    auto_rotate: bool = False
    rotation_interval_days: Optional[int] = Field(None, ge=30, le=365)

    @field_validator('rotation_interval_days')
    @classmethod
    def validate_rotation_interval(cls, v: Optional[int], info) -> Optional[int]:
        """Validate rotation interval is set if auto_rotate is enabled."""
        if info.data.get('auto_rotate') and v is None:
            raise ValueError('rotation_interval_days required when auto_rotate is True')
        return v


class KeyMetadata(BaseModel):
    """Metadata about a cryptographic key."""
    id: str
    name: str
    key_type: KeyType
    purpose: KeyPurpose
    status: KeyStatus
    version: int
    created_at: datetime
    created_by: str
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    access_policy: AccessPolicy
    allowed_users: list[str]
    is_backed_up: bool
    hsm_integrated: bool


class KeyUsageRecord(BaseModel):
    """Record of key usage for auditing."""
    key_id: str
    used_at: datetime
    used_by: str
    operation: str
    success: bool
    metadata: dict[str, Any] = Field(default_factory=dict)


class HSMConfig(BaseModel):
    """Configuration for Hardware Security Module integration."""
    enabled: bool = False
    provider: str = "pkcs11"  # pkcs11, aws_kms, azure_keyvault, google_kms
    endpoint: Optional[str] = None
    credentials: Optional[dict[str, str]] = None
    key_wrapping_enabled: bool = True
    auto_backup_to_hsm: bool = False


# =============================================================================
# Database Models
# =============================================================================

class CryptographicKey(Base):
    """
    Database model for storing encrypted cryptographic keys.

    Security:
    - All key material is encrypted at rest using AES-256-GCM
    - Encryption key is derived from master secret using PBKDF2
    - Each key has a unique salt and nonce for encryption
    - Private keys are stored separately from public keys
    """
    __tablename__ = "cryptographic_keys"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    key_type = Column(String(50), nullable=False)
    purpose = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default=KeyStatus.ACTIVE.value)
    version = Column(Integer, nullable=False, default=1)

    # Encrypted key material (base64 encoded)
    encrypted_key_material = Column(Text, nullable=False)
    encrypted_private_key = Column(Text, nullable=True)  # For asymmetric keys
    public_key = Column(Text, nullable=True)  # For asymmetric keys (can be unencrypted)

    # Encryption metadata
    encryption_salt = Column(String(64), nullable=False)  # Salt for key derivation
    encryption_nonce = Column(String(32), nullable=False)  # Nonce for AES-GCM
    encryption_tag = Column(String(32), nullable=False)  # Authentication tag

    # Access control
    access_policy = Column(String(50), nullable=False, default=AccessPolicy.ADMIN_ONLY.value)
    allowed_users = Column(JSONType, nullable=False, default=list)  # List of user IDs

    # Lifecycle management
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(500), nullable=True)

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)

    # Rotation and versioning
    auto_rotate = Column(Boolean, nullable=False, default=False)
    rotation_interval_days = Column(Integer, nullable=True)
    last_rotated_at = Column(DateTime, nullable=True)
    previous_version_id = Column(GUID(), nullable=True)  # Link to previous version
    next_version_id = Column(GUID(), nullable=True)  # Link to next version

    # Backup and recovery
    is_backed_up = Column(Boolean, nullable=False, default=False)
    backup_location = Column(String(500), nullable=True)
    last_backup_at = Column(DateTime, nullable=True)

    # HSM integration
    hsm_integrated = Column(Boolean, nullable=False, default=False)
    hsm_key_id = Column(String(255), nullable=True)
    hsm_provider = Column(String(50), nullable=True)

    # Metadata
    description = Column(String(1000), nullable=True)
    key_metadata = Column(JSONType, nullable=False, default=dict)

    def __repr__(self):
        return f"<CryptographicKey(name='{self.name}', type='{self.key_type}', status='{self.status}')>"


class KeyUsageLog(Base):
    """
    Audit log for key usage tracking.

    Records every use of a cryptographic key for security auditing and compliance.
    """
    __tablename__ = "key_usage_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    key_id = Column(GUID(), nullable=False, index=True)
    key_name = Column(String(255), nullable=False)

    # Usage details
    used_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    used_by = Column(String(255), nullable=False, index=True)
    operation = Column(String(100), nullable=False)  # encrypt, decrypt, sign, verify
    success = Column(Boolean, nullable=False)

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)

    # Additional metadata
    usage_metadata = Column(JSONType, nullable=False, default=dict)
    error_message = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<KeyUsageLog(key='{self.key_name}', operation='{self.operation}', success={self.success})>"


# =============================================================================
# Key Encryption/Decryption Functions
# =============================================================================

def _derive_encryption_key(salt: bytes) -> bytes:
    """
    Derive an encryption key from the master secret using PBKDF2.

    Args:
        salt: Random salt for key derivation

    Returns:
        32-byte encryption key for AES-256
    """
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(settings.SECRET_KEY.encode())


def _encrypt_key_material(key_material: bytes) -> tuple[bytes, bytes, bytes, bytes]:
    """
    Encrypt key material using AES-256-GCM.

    Args:
        key_material: Raw key bytes to encrypt

    Returns:
        Tuple of (encrypted_data, salt, nonce, tag)
    """
    # Generate random salt and nonce
    salt = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)  # 96 bits for GCM

    # Derive encryption key from master secret
    encryption_key = _derive_encryption_key(salt)

    # Encrypt using AES-256-GCM
    cipher = Cipher(
        algorithms.AES(encryption_key),
        modes.GCM(nonce),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(key_material) + encryptor.finalize()

    return ciphertext, salt, nonce, encryptor.tag


def _decrypt_key_material(
    encrypted_data: bytes,
    salt: bytes,
    nonce: bytes,
    tag: bytes
) -> bytes:
    """
    Decrypt key material using AES-256-GCM.

    Args:
        encrypted_data: Encrypted key material
        salt: Salt used for key derivation
        nonce: Nonce used for encryption
        tag: Authentication tag from GCM

    Returns:
        Decrypted key material

    Raises:
        ValueError: If decryption fails (tampered data)
    """
    # Derive encryption key from master secret
    encryption_key = _derive_encryption_key(salt)

    # Decrypt using AES-256-GCM
    cipher = Cipher(
        algorithms.AES(encryption_key),
        modes.GCM(nonce, tag),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_data) + decryptor.finalize()


# =============================================================================
# Key Management Service
# =============================================================================

class KeyManagementService:
    """
    Enterprise-grade cryptographic key management service.

    Features:
    - Symmetric and asymmetric key generation
    - Secure storage with encryption at rest
    - Key versioning and rotation
    - Usage tracking and auditing
    - Access control and policies
    - HSM integration support
    - Backup and recovery
    - Key revocation
    """

    def __init__(self, hsm_config: Optional[HSMConfig] = None):
        """
        Initialize key management service.

        Args:
            hsm_config: Optional HSM configuration for hardware-backed keys
        """
        self.hsm_config = hsm_config or HSMConfig()

    # =========================================================================
    # Key Generation
    # =========================================================================

    async def generate_key(
        self,
        db: AsyncSession,
        request: KeyGenerationRequest,
        created_by: str
    ) -> KeyMetadata:
        """
        Generate a new cryptographic key.

        Args:
            db: Database session
            request: Key generation request
            created_by: Username/ID of requesting user

        Returns:
            Metadata of the generated key

        Raises:
            ValidationError: If key with same name already exists
        """
        # Check if key with same name exists
        existing = await self._get_key_by_name(db, request.name)
        if existing:
            raise ValidationError(f"Key with name '{request.name}' already exists")

        # Generate key material based on type
        if request.key_type == KeyType.SYMMETRIC:
            key_material = self._generate_symmetric_key()
            private_key_material = None
            public_key_pem = None
        else:
            key_material, private_key_material, public_key_pem = self._generate_asymmetric_key(
                request.key_type
            )

        # Encrypt key material
        encrypted_key, salt, nonce, tag = _encrypt_key_material(key_material)

        # Encrypt private key if asymmetric
        encrypted_private_key = None
        private_salt = None
        private_nonce = None
        private_tag = None
        if private_key_material:
            encrypted_private_key, private_salt, private_nonce, private_tag = \
                _encrypt_key_material(private_key_material)

        # Calculate expiration date
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

        # Create database record
        key_record = CryptographicKey(
            id=uuid.uuid4(),
            name=request.name,
            key_type=request.key_type.value,
            purpose=request.purpose.value,
            status=KeyStatus.ACTIVE.value,
            version=1,
            encrypted_key_material=base64.b64encode(encrypted_key).decode(),
            encrypted_private_key=base64.b64encode(encrypted_private_key).decode() if encrypted_private_key else None,
            public_key=public_key_pem,
            encryption_salt=base64.b64encode(salt).decode(),
            encryption_nonce=base64.b64encode(nonce).decode(),
            encryption_tag=base64.b64encode(tag).decode(),
            access_policy=request.access_policy.value,
            allowed_users=request.allowed_users,
            created_by=created_by,
            expires_at=expires_at,
            auto_rotate=request.auto_rotate,
            rotation_interval_days=request.rotation_interval_days,
            description=request.description,
            hsm_integrated=self.hsm_config.enabled,
            metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "algorithm": request.key_type.value,
            }
        )

        # Store encrypted private key metadata if asymmetric
        if private_key_material:
            key_record.metadata.update({
                "private_key_salt": base64.b64encode(private_salt).decode(),
                "private_key_nonce": base64.b64encode(private_nonce).decode(),
                "private_key_tag": base64.b64encode(private_tag).decode(),
            })

        db.add(key_record)
        await db.commit()
        await db.refresh(key_record)

        logger.info(f"Generated new {request.key_type.value} key: {request.name}")

        return self._key_to_metadata(key_record)

    def _generate_symmetric_key(self, key_size: int = 32) -> bytes:
        """
        Generate a symmetric key (AES-256).

        Args:
            key_size: Key size in bytes (default 32 for AES-256)

        Returns:
            Random key bytes
        """
        return secrets.token_bytes(key_size)

    def _generate_asymmetric_key(
        self,
        key_type: KeyType
    ) -> tuple[bytes, bytes, str]:
        """
        Generate an asymmetric key pair.

        Args:
            key_type: Type of asymmetric key to generate

        Returns:
            Tuple of (public_key_bytes, private_key_bytes, public_key_pem)

        Raises:
            ValidationError: If key type is not supported
        """
        if key_type == KeyType.RSA_2048:
            key_size = 2048
        elif key_type == KeyType.RSA_4096:
            key_size = 4096
        else:
            raise ValidationError(f"Asymmetric key type {key_type} not yet implemented")

        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        # Serialize private key
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Serialize public key
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        public_key_pem = public_key_bytes.decode()

        return public_key_bytes, private_key_bytes, public_key_pem

    # =========================================================================
    # Key Retrieval
    # =========================================================================

    async def get_key(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str,
        decrypt: bool = False
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve a cryptographic key by ID.

        Args:
            db: Database session
            key_id: UUID of the key
            user_id: ID of requesting user
            decrypt: Whether to decrypt and return key material

        Returns:
            Key data including material if decrypt=True, None if not found

        Raises:
            ForbiddenError: If user doesn't have access to the key
            NotFoundError: If key doesn't exist
        """
        key_uuid = uuid.UUID(key_id)
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.id == key_uuid)
        )
        key_record = result.scalar_one_or_none()

        if not key_record:
            raise NotFoundError(f"Key with ID {key_id} not found")

        # Check access policy
        if not self._check_access(key_record, user_id):
            raise ForbiddenError(f"Access denied to key {key_record.name}")

        # Update usage tracking
        await self._record_usage(
            db, key_record, user_id, "read", True
        )

        # Prepare response
        response = {
            "metadata": self._key_to_metadata(key_record),
            "public_key": key_record.public_key,
        }

        # Decrypt key material if requested
        if decrypt:
            try:
                key_material = self._decrypt_key(key_record)
                response["key_material"] = base64.b64encode(key_material).decode()

                # Decrypt private key if asymmetric
                if key_record.encrypted_private_key:
                    private_key = self._decrypt_private_key(key_record)
                    response["private_key"] = private_key.decode()

            except Exception as e:
                logger.error(f"Failed to decrypt key {key_id}: {e}")
                await self._record_usage(
                    db, key_record, user_id, "decrypt", False,
                    error=str(e)
                )
                raise ValidationError("Failed to decrypt key material")

        return response

    async def get_key_by_name(
        self,
        db: AsyncSession,
        name: str,
        user_id: str
    ) -> Optional[KeyMetadata]:
        """
        Retrieve key metadata by name.

        Args:
            db: Database session
            name: Key name
            user_id: ID of requesting user

        Returns:
            Key metadata or None if not found

        Raises:
            ForbiddenError: If user doesn't have access
        """
        key_record = await self._get_key_by_name(db, name)
        if not key_record:
            return None

        if not self._check_access(key_record, user_id):
            raise ForbiddenError(f"Access denied to key {name}")

        return self._key_to_metadata(key_record)

    async def list_keys(
        self,
        db: AsyncSession,
        user_id: str,
        status: Optional[KeyStatus] = None,
        purpose: Optional[KeyPurpose] = None
    ) -> list[KeyMetadata]:
        """
        List all keys accessible to the user.

        Args:
            db: Database session
            user_id: ID of requesting user
            status: Optional filter by status
            purpose: Optional filter by purpose

        Returns:
            List of key metadata
        """
        query = select(CryptographicKey)

        if status:
            query = query.where(CryptographicKey.status == status.value)
        if purpose:
            query = query.where(CryptographicKey.purpose == purpose.value)

        result = await db.execute(query.order_by(CryptographicKey.created_at.desc()))
        all_keys = result.scalars().all()

        # Filter by access policy
        accessible_keys = [
            self._key_to_metadata(key)
            for key in all_keys
            if self._check_access(key, user_id)
        ]

        return accessible_keys

    # =========================================================================
    # Key Lifecycle Management
    # =========================================================================

    async def rotate_key(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str
    ) -> KeyMetadata:
        """
        Rotate a key by generating a new version.

        Args:
            db: Database session
            key_id: UUID of key to rotate
            user_id: ID of requesting user

        Returns:
            Metadata of new key version

        Raises:
            ForbiddenError: If user doesn't have access
            ValidationError: If key cannot be rotated
        """
        key_uuid = uuid.UUID(key_id)
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.id == key_uuid)
        )
        old_key = result.scalar_one_or_none()

        if not old_key:
            raise NotFoundError(f"Key with ID {key_id} not found")

        if not self._check_access(old_key, user_id):
            raise ForbiddenError(f"Access denied to key {old_key.name}")

        if old_key.status == KeyStatus.REVOKED.value:
            raise ValidationError("Cannot rotate revoked key")

        # Mark old key as rotating
        old_key.status = KeyStatus.ROTATING.value
        await db.commit()

        # Generate new key version
        new_request = KeyGenerationRequest(
            key_type=KeyType(old_key.key_type),
            purpose=KeyPurpose(old_key.purpose),
            name=f"{old_key.name}",  # Keep same name
            description=f"Rotated version of {old_key.name}",
            access_policy=AccessPolicy(old_key.access_policy),
            allowed_users=old_key.allowed_users,
            expires_in_days=None,
            auto_rotate=old_key.auto_rotate,
            rotation_interval_days=old_key.rotation_interval_days
        )

        # Delete old key to avoid name conflict
        await db.delete(old_key)
        await db.commit()

        new_key_metadata = await self.generate_key(db, new_request, user_id)

        # Re-fetch new key and update version info
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.id == uuid.UUID(new_key_metadata.id))
        )
        new_key = result.scalar_one()

        new_key.version = old_key.version + 1
        new_key.previous_version_id = old_key.id
        new_key.last_rotated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(new_key)

        logger.info(f"Rotated key {old_key.name} from v{old_key.version} to v{new_key.version}")

        return self._key_to_metadata(new_key)

    async def revoke_key(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str,
        reason: str
    ) -> KeyMetadata:
        """
        Revoke a key, preventing further use.

        Args:
            db: Database session
            key_id: UUID of key to revoke
            user_id: ID of requesting user
            reason: Reason for revocation

        Returns:
            Updated key metadata

        Raises:
            ForbiddenError: If user doesn't have access
        """
        key_uuid = uuid.UUID(key_id)
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.id == key_uuid)
        )
        key_record = result.scalar_one_or_none()

        if not key_record:
            raise NotFoundError(f"Key with ID {key_id} not found")

        if not self._check_access(key_record, user_id):
            raise ForbiddenError(f"Access denied to key {key_record.name}")

        key_record.status = KeyStatus.REVOKED.value
        key_record.revoked_at = datetime.utcnow()
        key_record.revocation_reason = reason

        await db.commit()
        await db.refresh(key_record)

        logger.warning(f"Revoked key {key_record.name}: {reason}")

        return self._key_to_metadata(key_record)

    async def delete_key(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str,
        force: bool = False
    ) -> None:
        """
        Delete a key permanently.

        Args:
            db: Database session
            key_id: UUID of key to delete
            user_id: ID of requesting user
            force: Skip safety checks if True

        Raises:
            ForbiddenError: If user doesn't have access
            ValidationError: If key is active and force=False
        """
        key_uuid = uuid.UUID(key_id)
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.id == key_uuid)
        )
        key_record = result.scalar_one_or_none()

        if not key_record:
            raise NotFoundError(f"Key with ID {key_id} not found")

        if not self._check_access(key_record, user_id):
            raise ForbiddenError(f"Access denied to key {key_record.name}")

        if not force and key_record.status == KeyStatus.ACTIVE.value:
            raise ValidationError(
                "Cannot delete active key. Revoke first or use force=True"
            )

        await db.delete(key_record)
        await db.commit()

        logger.warning(f"Deleted key {key_record.name} (force={force})")

    # =========================================================================
    # Key Usage Tracking
    # =========================================================================

    async def get_key_usage(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str,
        limit: int = 100
    ) -> list[KeyUsageRecord]:
        """
        Get usage history for a key.

        Args:
            db: Database session
            key_id: UUID of key
            user_id: ID of requesting user
            limit: Maximum number of records to return

        Returns:
            List of usage records

        Raises:
            ForbiddenError: If user doesn't have access
        """
        # Check access to key
        key_uuid = uuid.UUID(key_id)
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.id == key_uuid)
        )
        key_record = result.scalar_one_or_none()

        if not key_record:
            raise NotFoundError(f"Key with ID {key_id} not found")

        if not self._check_access(key_record, user_id):
            raise ForbiddenError(f"Access denied to key {key_record.name}")

        # Fetch usage logs
        result = await db.execute(
            select(KeyUsageLog)
            .where(KeyUsageLog.key_id == key_uuid)
            .order_by(KeyUsageLog.used_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        return [
            KeyUsageRecord(
                key_id=str(log.key_id),
                used_at=log.used_at,
                used_by=log.used_by,
                operation=log.operation,
                success=log.success,
                metadata=log.metadata or {}
            )
            for log in logs
        ]

    # =========================================================================
    # Backup and Recovery
    # =========================================================================

    async def backup_key(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str,
        backup_location: str
    ) -> KeyMetadata:
        """
        Mark a key as backed up to external storage.

        Args:
            db: Database session
            key_id: UUID of key to backup
            user_id: ID of requesting user
            backup_location: Location identifier for backup

        Returns:
            Updated key metadata

        Raises:
            ForbiddenError: If user doesn't have access
        """
        key_uuid = uuid.UUID(key_id)
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.id == key_uuid)
        )
        key_record = result.scalar_one_or_none()

        if not key_record:
            raise NotFoundError(f"Key with ID {key_id} not found")

        if not self._check_access(key_record, user_id):
            raise ForbiddenError(f"Access denied to key {key_record.name}")

        key_record.is_backed_up = True
        key_record.backup_location = backup_location
        key_record.last_backup_at = datetime.utcnow()

        await db.commit()
        await db.refresh(key_record)

        logger.info(f"Backed up key {key_record.name} to {backup_location}")

        return self._key_to_metadata(key_record)

    # =========================================================================
    # HSM Integration Hooks
    # =========================================================================

    async def integrate_with_hsm(
        self,
        db: AsyncSession,
        key_id: str,
        user_id: str,
        hsm_key_id: str
    ) -> KeyMetadata:
        """
        Link a key to an HSM-stored key.

        Args:
            db: Database session
            key_id: UUID of key
            user_id: ID of requesting user
            hsm_key_id: Identifier of key in HSM

        Returns:
            Updated key metadata

        Raises:
            ForbiddenError: If user doesn't have access
            ValidationError: If HSM not configured
        """
        if not self.hsm_config.enabled:
            raise ValidationError("HSM integration is not enabled")

        key_uuid = uuid.UUID(key_id)
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.id == key_uuid)
        )
        key_record = result.scalar_one_or_none()

        if not key_record:
            raise NotFoundError(f"Key with ID {key_id} not found")

        if not self._check_access(key_record, user_id):
            raise ForbiddenError(f"Access denied to key {key_record.name}")

        key_record.hsm_integrated = True
        key_record.hsm_key_id = hsm_key_id
        key_record.hsm_provider = self.hsm_config.provider

        await db.commit()
        await db.refresh(key_record)

        logger.info(f"Integrated key {key_record.name} with HSM: {hsm_key_id}")

        return self._key_to_metadata(key_record)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_key_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[CryptographicKey]:
        """Get key record by name."""
        result = await db.execute(
            select(CryptographicKey).where(CryptographicKey.name == name)
        )
        return result.scalar_one_or_none()

    def _check_access(self, key: CryptographicKey, user_id: str) -> bool:
        """
        Check if user has access to a key based on access policy.

        Args:
            key: Key record
            user_id: User ID to check

        Returns:
            True if user has access, False otherwise
        """
        policy = AccessPolicy(key.access_policy)

        if policy == AccessPolicy.PUBLIC_READ:
            return True
        elif policy == AccessPolicy.USER_SPECIFIC:
            return user_id in key.allowed_users
        elif policy == AccessPolicy.ADMIN_ONLY:
            # In production, check if user_id is an admin
            # For now, allow access
            return True
        elif policy in (AccessPolicy.SERVICE_ACCOUNT, AccessPolicy.APPLICATION):
            # In production, check service account credentials
            return True

        return False

    async def _record_usage(
        self,
        db: AsyncSession,
        key: CryptographicKey,
        user_id: str,
        operation: str,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Record key usage in audit log.

        Args:
            db: Database session
            key: Key record
            user_id: User who used the key
            operation: Operation performed
            success: Whether operation succeeded
            error: Optional error message
        """
        # Update key usage statistics
        key.usage_count += 1
        if success:
            key.last_used_at = datetime.utcnow()

        # Create usage log
        log = KeyUsageLog(
            key_id=key.id,
            key_name=key.name,
            used_by=user_id,
            operation=operation,
            success=success,
            error_message=error,
            metadata={
                "key_version": key.version,
                "key_type": key.key_type,
            }
        )

        db.add(log)
        await db.commit()

    def _key_to_metadata(self, key: CryptographicKey) -> KeyMetadata:
        """Convert database record to metadata schema."""
        return KeyMetadata(
            id=str(key.id),
            name=key.name,
            key_type=KeyType(key.key_type),
            purpose=KeyPurpose(key.purpose),
            status=KeyStatus(key.status),
            version=key.version,
            created_at=key.created_at,
            created_by=key.created_by,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            access_policy=AccessPolicy(key.access_policy),
            allowed_users=key.allowed_users or [],
            is_backed_up=key.is_backed_up,
            hsm_integrated=key.hsm_integrated
        )

    def _decrypt_key(self, key: CryptographicKey) -> bytes:
        """Decrypt symmetric key or public key material."""
        encrypted_data = base64.b64decode(key.encrypted_key_material)
        salt = base64.b64decode(key.encryption_salt)
        nonce = base64.b64decode(key.encryption_nonce)
        tag = base64.b64decode(key.encryption_tag)

        return _decrypt_key_material(encrypted_data, salt, nonce, tag)

    def _decrypt_private_key(self, key: CryptographicKey) -> bytes:
        """Decrypt private key material for asymmetric keys."""
        if not key.encrypted_private_key:
            raise ValidationError("Key does not have private key material")

        encrypted_data = base64.b64decode(key.encrypted_private_key)
        salt = base64.b64decode(key.metadata["private_key_salt"])
        nonce = base64.b64decode(key.metadata["private_key_nonce"])
        tag = base64.b64decode(key.metadata["private_key_tag"])

        return _decrypt_key_material(encrypted_data, salt, nonce, tag)


# =============================================================================
# Synchronous Wrapper for Backward Compatibility
# =============================================================================

class SyncKeyManagementService:
    """
    Synchronous wrapper for KeyManagementService.

    Provides sync methods for use with non-async codebases.
    """

    def __init__(self, hsm_config: Optional[HSMConfig] = None):
        """Initialize with optional HSM configuration."""
        self.async_service = KeyManagementService(hsm_config)

    def generate_key_sync(
        self,
        db: Session,
        request: KeyGenerationRequest,
        created_by: str
    ) -> KeyMetadata:
        """Synchronous version of generate_key."""
        # In production, use asyncio.run() or sync session
        raise NotImplementedError("Sync version requires async-to-sync adapter")

    def get_key_sync(
        self,
        db: Session,
        key_id: str,
        user_id: str,
        decrypt: bool = False
    ) -> Optional[dict[str, Any]]:
        """Synchronous version of get_key."""
        raise NotImplementedError("Sync version requires async-to-sync adapter")
