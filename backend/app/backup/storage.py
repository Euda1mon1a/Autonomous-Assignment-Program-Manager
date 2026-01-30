"""
Backup Storage Backends.

This module provides abstraction for different storage backends:
- Local filesystem storage
- AWS S3 storage
- S3-compatible storage (MinIO, etc.)

All storage backends implement the BackupStorage interface for consistency.

Usage:
    # Local storage
    storage = LocalStorage("/backups")
    storage.save_backup(backup_id, backup_data)

    # S3 storage
    storage = S3Storage(bucket="my-backups", region="us-east-1")
    storage.save_backup(backup_id, backup_data)

    # Get storage from settings
    storage = get_storage_backend()
"""

import gzip
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BackupStorage(ABC):
    """
    Abstract base class for backup storage backends.

    Defines the interface that all storage backends must implement.
    """

    @abstractmethod
    def save_backup(self, backup_id: str, backup_data: dict[str, Any]) -> bool:
        """
        Save a backup to storage.

        Args:
            backup_id: Unique identifier for the backup
            backup_data: Backup data dictionary

        Returns:
            bool: True if successful

        Raises:
            ValueError: If save fails
        """
        pass

    @abstractmethod
    def get_backup(self, backup_id: str) -> dict[str, Any]:
        """
        Retrieve a backup from storage.

        Args:
            backup_id: Unique identifier for the backup

        Returns:
            dict: Backup data

        Raises:
            ValueError: If backup not found or retrieval fails
        """
        pass

    @abstractmethod
    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup from storage.

        Args:
            backup_id: Unique identifier for the backup

        Returns:
            bool: True if successful

        Raises:
            ValueError: If deletion fails
        """
        pass

    @abstractmethod
    def list_backups(
        self,
        backup_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List available backups.

        Args:
            backup_type: Filter by backup type (full, incremental, differential)
            limit: Maximum number of backups to return

        Returns:
            list: List of backup metadata dictionaries
        """
        pass

    @abstractmethod
    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity.

        Args:
            backup_id: Unique identifier for the backup

        Returns:
            bool: True if backup is valid

        Raises:
            ValueError: If verification fails
        """
        pass

    @abstractmethod
    def get_backup_size(self, backup_id: str) -> int:
        """
        Get size of a backup in bytes.

        Args:
            backup_id: Unique identifier for the backup

        Returns:
            int: Size in bytes

        Raises:
            ValueError: If backup not found
        """
        pass

    def _calculate_checksum(self, data: bytes) -> str:
        """
        Calculate SHA-256 checksum.

        Args:
            data: Data bytes

        Returns:
            str: Hex digest of SHA-256 hash
        """
        return hashlib.sha256(data).hexdigest()

    def _compress_backup(self, backup_data: dict[str, Any]) -> bytes:
        """
        Compress backup data using gzip.

        Args:
            backup_data: Backup data dictionary

        Returns:
            bytes: Compressed data
        """
        json_str = json.dumps(backup_data, indent=2, default=str)
        return gzip.compress(json_str.encode("utf-8"))

    def _decompress_backup(self, compressed_data: bytes) -> dict[str, Any]:
        """
        Decompress backup data.

        Args:
            compressed_data: Compressed bytes

        Returns:
            dict: Decompressed backup data

        Raises:
            ValueError: If decompression fails
        """
        try:
            json_str = gzip.decompress(compressed_data).decode("utf-8")
            return json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Failed to decompress backup: {e}")


class LocalStorage(BackupStorage):
    """
    Local filesystem storage backend.

    Stores backups in the local filesystem with gzip compression.
    Suitable for development, testing, and small deployments.

    Directory structure:
        backup_dir/
            full/
                backup_<id>.json.gz
                backup_<id>.meta.json
            incremental/
                backup_<id>.json.gz
                backup_<id>.meta.json
            differential/
                backup_<id>.json.gz
                backup_<id>.meta.json
    """

    def __init__(self, backup_dir: str = "/tmp/backups") -> None:
        """
        Initialize local storage.

        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self._ensure_directories()

        logger.info(f"Initialized LocalStorage at {self.backup_dir}")

    def _ensure_directories(self) -> None:
        """Create backup directories if they don't exist."""
        for subdir in ["full", "incremental", "differential"]:
            (self.backup_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _get_backup_path(self, backup_id: str, backup_type: str = "full") -> Path:
        """
        Get filesystem path for a backup.

        Args:
            backup_id: Backup identifier
            backup_type: Type of backup (full, incremental, differential)

        Returns:
            Path: Path to backup file
        """
        return self.backup_dir / backup_type / f"backup_{backup_id}.json.gz"

    def _get_metadata_path(self, backup_id: str, backup_type: str = "full") -> Path:
        """
        Get filesystem path for backup metadata.

        Args:
            backup_id: Backup identifier
            backup_type: Type of backup

        Returns:
            Path: Path to metadata file
        """
        return self.backup_dir / backup_type / f"backup_{backup_id}.meta.json"

    def save_backup(self, backup_id: str, backup_data: dict[str, Any]) -> bool:
        """
        Save backup to local filesystem.

        Args:
            backup_id: Unique backup identifier
            backup_data: Backup data dictionary

        Returns:
            bool: True if successful

        Raises:
            ValueError: If save fails
        """
        try:
            backup_type = backup_data.get("backup_type", "full")

            # Compress backup data
            compressed_data = self._compress_backup(backup_data)

            # Calculate checksum
            checksum = self._calculate_checksum(compressed_data)

            # Save backup file
            backup_path = self._get_backup_path(backup_id, backup_type)
            backup_path.write_bytes(compressed_data)

            # Save metadata
            metadata = {
                "backup_id": backup_id,
                "backup_type": backup_type,
                "created_at": backup_data.get(
                    "created_at", datetime.utcnow().isoformat()
                ),
                "size_bytes": len(compressed_data),
                "checksum": checksum,
                "strategy": backup_data.get("strategy", backup_type),
                "table_count": backup_data.get("metadata", {}).get("table_count", 0),
                "total_rows": backup_data.get("metadata", {}).get("total_rows", 0),
            }

            metadata_path = self._get_metadata_path(backup_id, backup_type)
            metadata_path.write_text(json.dumps(metadata, indent=2))

            logger.info(
                f"Saved backup {backup_id} to {backup_path} "
                f"({len(compressed_data) / 1024 / 1024:.2f} MB)"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to save backup {backup_id}: {e}", exc_info=True)
            raise ValueError(f"Failed to save backup: {e}")

    def get_backup(self, backup_id: str) -> dict[str, Any]:
        """
        Retrieve backup from local filesystem.

        Args:
            backup_id: Unique backup identifier

        Returns:
            dict: Backup data

        Raises:
            ValueError: If backup not found or retrieval fails
        """
        try:
            # Try each backup type directory
            for backup_type in ["full", "incremental", "differential"]:
                backup_path = self._get_backup_path(backup_id, backup_type)

                if backup_path.exists():
                    # Read compressed data
                    compressed_data = backup_path.read_bytes()

                    # Decompress
                    backup_data = self._decompress_backup(compressed_data)

                    logger.info(f"Retrieved backup {backup_id} from {backup_path}")
                    return backup_data

            raise ValueError(f"Backup {backup_id} not found")

        except Exception as e:
            logger.error(f"Failed to retrieve backup {backup_id}: {e}")
            raise ValueError(f"Failed to retrieve backup: {e}")

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete backup from local filesystem.

        Args:
            backup_id: Unique backup identifier

        Returns:
            bool: True if successful

        Raises:
            ValueError: If deletion fails
        """
        try:
            deleted = False

            # Try each backup type directory
            for backup_type in ["full", "incremental", "differential"]:
                backup_path = self._get_backup_path(backup_id, backup_type)
                metadata_path = self._get_metadata_path(backup_id, backup_type)

                if backup_path.exists():
                    backup_path.unlink()
                    deleted = True

                if metadata_path.exists():
                    metadata_path.unlink()

            if not deleted:
                raise ValueError(f"Backup {backup_id} not found")

            logger.info(f"Deleted backup {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            raise ValueError(f"Failed to delete backup: {e}")

    def list_backups(
        self,
        backup_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List available backups in local filesystem.

        Args:
            backup_type: Filter by backup type
            limit: Maximum number of backups to return

        Returns:
            list: List of backup metadata dictionaries
        """
        backups = []

        # Search in specified type or all types
        types_to_search = (
            [backup_type] if backup_type else ["full", "incremental", "differential"]
        )

        for btype in types_to_search:
            type_dir = self.backup_dir / btype

            if not type_dir.exists():
                continue

                # Find all metadata files
            for meta_file in type_dir.glob("*.meta.json"):
                try:
                    metadata = json.loads(meta_file.read_text())
                    backups.append(metadata)
                except Exception as e:
                    logger.warning(f"Error reading metadata {meta_file}: {e}")
                    continue

                    # Sort by created_at descending
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return backups[:limit]

    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity using checksum.

        Args:
            backup_id: Unique backup identifier

        Returns:
            bool: True if backup is valid

        Raises:
            ValueError: If verification fails
        """
        try:
            # Find backup and metadata
            for backup_type in ["full", "incremental", "differential"]:
                backup_path = self._get_backup_path(backup_id, backup_type)
                metadata_path = self._get_metadata_path(backup_id, backup_type)

                if backup_path.exists() and metadata_path.exists():
                    # Read metadata
                    metadata = json.loads(metadata_path.read_text())
                    expected_checksum = metadata.get("checksum")

                    if not expected_checksum:
                        logger.warning(f"No checksum in metadata for {backup_id}")
                        return False

                        # Calculate actual checksum
                    compressed_data = backup_path.read_bytes()
                    actual_checksum = self._calculate_checksum(compressed_data)

                    # Compare checksums
                    if actual_checksum == expected_checksum:
                        logger.info(f"Backup {backup_id} verified successfully")
                        return True
                    else:
                        logger.error(
                            f"Checksum mismatch for {backup_id}: "
                            f"expected {expected_checksum}, got {actual_checksum}"
                        )
                        return False

            raise ValueError(f"Backup {backup_id} not found")

        except Exception as e:
            logger.error(f"Failed to verify backup {backup_id}: {e}")
            raise ValueError(f"Failed to verify backup: {e}")

    def get_backup_size(self, backup_id: str) -> int:
        """
        Get size of backup in bytes.

        Args:
            backup_id: Unique backup identifier

        Returns:
            int: Size in bytes

        Raises:
            ValueError: If backup not found
        """
        for backup_type in ["full", "incremental", "differential"]:
            backup_path = self._get_backup_path(backup_id, backup_type)

            if backup_path.exists():
                return backup_path.stat().st_size

        raise ValueError(f"Backup {backup_id} not found")


class S3Storage(BackupStorage):
    """
    AWS S3 storage backend.

    Stores backups in AWS S3 or S3-compatible storage (MinIO, DigitalOcean Spaces, etc.).
    Suitable for production deployments with redundancy and scalability.

    Requires boto3: pip install boto3
    """

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        """
        Initialize S3 storage.

        Args:
            bucket: S3 bucket name
            region: AWS region
            access_key: AWS access key (uses env if None)
            secret_key: AWS secret key (uses env if None)
            endpoint_url: Custom endpoint URL for S3-compatible services
        """
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )

        self.bucket = bucket
        self.region = region

        # Create S3 client
        session_kwargs = {}
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key

        client_kwargs = {"region_name": region}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        session = boto3.Session(**session_kwargs)
        self.s3_client = session.client("s3", **client_kwargs)

        logger.info(f"Initialized S3Storage for bucket {bucket} in region {region}")

    def _get_s3_key(self, backup_id: str, backup_type: str = "full") -> str:
        """
        Get S3 object key for a backup.

        Args:
            backup_id: Backup identifier
            backup_type: Type of backup

        Returns:
            str: S3 object key
        """
        return f"backups/{backup_type}/backup_{backup_id}.json.gz"

    def _get_metadata_key(self, backup_id: str, backup_type: str = "full") -> str:
        """
        Get S3 object key for backup metadata.

        Args:
            backup_id: Backup identifier
            backup_type: Type of backup

        Returns:
            str: S3 object key for metadata
        """
        return f"backups/{backup_type}/backup_{backup_id}.meta.json"

    def save_backup(self, backup_id: str, backup_data: dict[str, Any]) -> bool:
        """
        Save backup to S3.

        Args:
            backup_id: Unique backup identifier
            backup_data: Backup data dictionary

        Returns:
            bool: True if successful

        Raises:
            ValueError: If save fails
        """
        try:
            backup_type = backup_data.get("backup_type", "full")

            # Compress backup data
            compressed_data = self._compress_backup(backup_data)

            # Calculate checksum
            checksum = self._calculate_checksum(compressed_data)

            # Upload backup to S3
            s3_key = self._get_s3_key(backup_id, backup_type)
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=compressed_data,
                ContentType="application/gzip",
                Metadata={
                    "backup-id": backup_id,
                    "backup-type": backup_type,
                    "checksum": checksum,
                },
            )

            # Upload metadata
            metadata = {
                "backup_id": backup_id,
                "backup_type": backup_type,
                "created_at": backup_data.get(
                    "created_at", datetime.utcnow().isoformat()
                ),
                "size_bytes": len(compressed_data),
                "checksum": checksum,
                "strategy": backup_data.get("strategy", backup_type),
                "table_count": backup_data.get("metadata", {}).get("table_count", 0),
                "total_rows": backup_data.get("metadata", {}).get("total_rows", 0),
                "storage_class": "STANDARD",
            }

            metadata_key = self._get_metadata_key(backup_id, backup_type)
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2),
                ContentType="application/json",
            )

            logger.info(
                f"Saved backup {backup_id} to S3 {self.bucket}/{s3_key} "
                f"({len(compressed_data) / 1024 / 1024:.2f} MB)"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to save backup {backup_id} to S3: {e}", exc_info=True)
            raise ValueError(f"Failed to save backup to S3: {e}")

    def get_backup(self, backup_id: str) -> dict[str, Any]:
        """
        Retrieve backup from S3.

        Args:
            backup_id: Unique backup identifier

        Returns:
            dict: Backup data

        Raises:
            ValueError: If backup not found or retrieval fails
        """
        try:
            # Try each backup type
            for backup_type in ["full", "incremental", "differential"]:
                s3_key = self._get_s3_key(backup_id, backup_type)

                try:
                    # Get object from S3
                    response = self.s3_client.get_object(
                        Bucket=self.bucket,
                        Key=s3_key,
                    )

                    # Read compressed data
                    compressed_data = response["Body"].read()

                    # Decompress
                    backup_data = self._decompress_backup(compressed_data)

                    logger.info(
                        f"Retrieved backup {backup_id} from S3 {self.bucket}/{s3_key}"
                    )
                    return backup_data

                except self.s3_client.exceptions.NoSuchKey:
                    continue

            raise ValueError(f"Backup {backup_id} not found in S3")

        except Exception as e:
            logger.error(f"Failed to retrieve backup {backup_id} from S3: {e}")
            raise ValueError(f"Failed to retrieve backup from S3: {e}")

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete backup from S3.

        Args:
            backup_id: Unique backup identifier

        Returns:
            bool: True if successful

        Raises:
            ValueError: If deletion fails
        """
        try:
            deleted = False

            # Try each backup type
            for backup_type in ["full", "incremental", "differential"]:
                s3_key = self._get_s3_key(backup_id, backup_type)
                metadata_key = self._get_metadata_key(backup_id, backup_type)

                # Delete backup
                try:
                    self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
                    deleted = True
                except Exception:
                    pass

                    # Delete metadata
                try:
                    self.s3_client.delete_object(Bucket=self.bucket, Key=metadata_key)
                except Exception:
                    pass

            if not deleted:
                raise ValueError(f"Backup {backup_id} not found in S3")

            logger.info(f"Deleted backup {backup_id} from S3")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id} from S3: {e}")
            raise ValueError(f"Failed to delete backup from S3: {e}")

    def list_backups(
        self,
        backup_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List available backups in S3.

        Args:
            backup_type: Filter by backup type
            limit: Maximum number of backups to return

        Returns:
            list: List of backup metadata dictionaries
        """
        backups = []

        # Search in specified type or all types
        types_to_search = (
            [backup_type] if backup_type else ["full", "incremental", "differential"]
        )

        for btype in types_to_search:
            prefix = f"backups/{btype}/"

            # List objects with metadata prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=limit,
            )

            if "Contents" not in response:
                continue

                # Get metadata files
            for obj in response["Contents"]:
                key = obj["Key"]

                if not key.endswith(".meta.json"):
                    continue

                try:
                    # Get metadata
                    meta_response = self.s3_client.get_object(
                        Bucket=self.bucket,
                        Key=key,
                    )

                    metadata = json.loads(meta_response["Body"].read())
                    backups.append(metadata)

                except Exception as e:
                    logger.warning(f"Error reading S3 metadata {key}: {e}")
                    continue

                    # Sort by created_at descending
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return backups[:limit]

    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity using checksum.

        Args:
            backup_id: Unique backup identifier

        Returns:
            bool: True if backup is valid

        Raises:
            ValueError: If verification fails
        """
        try:
            # Find backup and metadata in S3
            for backup_type in ["full", "incremental", "differential"]:
                s3_key = self._get_s3_key(backup_id, backup_type)
                metadata_key = self._get_metadata_key(backup_id, backup_type)

                try:
                    # Get metadata
                    meta_response = self.s3_client.get_object(
                        Bucket=self.bucket,
                        Key=metadata_key,
                    )

                    metadata = json.loads(meta_response["Body"].read())
                    expected_checksum = metadata.get("checksum")

                    if not expected_checksum:
                        logger.warning(f"No checksum in metadata for {backup_id}")
                        return False

                        # Get backup data
                    backup_response = self.s3_client.get_object(
                        Bucket=self.bucket,
                        Key=s3_key,
                    )

                    compressed_data = backup_response["Body"].read()

                    # Calculate actual checksum
                    actual_checksum = self._calculate_checksum(compressed_data)

                    # Compare checksums
                    if actual_checksum == expected_checksum:
                        logger.info(f"Backup {backup_id} verified successfully in S3")
                        return True
                    else:
                        logger.error(
                            f"S3 checksum mismatch for {backup_id}: "
                            f"expected {expected_checksum}, got {actual_checksum}"
                        )
                        return False

                except self.s3_client.exceptions.NoSuchKey:
                    continue

            raise ValueError(f"Backup {backup_id} not found in S3")

        except Exception as e:
            logger.error(f"Failed to verify backup {backup_id} in S3: {e}")
            raise ValueError(f"Failed to verify backup in S3: {e}")

    def get_backup_size(self, backup_id: str) -> int:
        """
        Get size of backup in bytes from S3.

        Args:
            backup_id: Unique backup identifier

        Returns:
            int: Size in bytes

        Raises:
            ValueError: If backup not found
        """
        for backup_type in ["full", "incremental", "differential"]:
            s3_key = self._get_s3_key(backup_id, backup_type)

            try:
                response = self.s3_client.head_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                )

                return response["ContentLength"]

            except self.s3_client.exceptions.NoSuchKey:
                continue

        raise ValueError(f"Backup {backup_id} not found in S3")


def get_storage_backend() -> BackupStorage:
    """
    Get storage backend from application settings.

    Returns:
        BackupStorage: Configured storage backend

    Raises:
        ValueError: If storage backend is not configured or invalid
    """
    from app.core.config import get_settings

    settings = get_settings()

    # Get storage backend from settings
    storage_backend = getattr(settings, "BACKUP_STORAGE_BACKEND", "local")

    if storage_backend == "local":
        backup_dir = getattr(settings, "BACKUP_LOCAL_DIR", "/tmp/backups")
        return LocalStorage(backup_dir=backup_dir)

    elif storage_backend == "s3":
        bucket = getattr(settings, "BACKUP_S3_BUCKET", "")
        region = getattr(settings, "BACKUP_S3_REGION", "us-east-1")
        access_key = getattr(settings, "BACKUP_S3_ACCESS_KEY", "")
        secret_key = getattr(settings, "BACKUP_S3_SECRET_KEY", "")
        endpoint_url = getattr(settings, "BACKUP_S3_ENDPOINT_URL", None)

        if not bucket:
            raise ValueError("BACKUP_S3_BUCKET must be set for S3 storage backend")

        return S3Storage(
            bucket=bucket,
            region=region,
            access_key=access_key or None,
            secret_key=secret_key or None,
            endpoint_url=endpoint_url or None,
        )

    else:
        raise ValueError(
            f"Invalid storage backend: {storage_backend}. Must be 'local' or 's3'"
        )
