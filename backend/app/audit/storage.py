"""
Archive Storage Backends for Audit Logs.

This module provides storage backends for compressed audit log archives,
supporting both local filesystem and AWS S3 storage.

Storage Organization:
-------------------
Archives are organized by:
- Year/Month (e.g., 2025/01/)
- Archive ID (e.g., archive-2025-01-daily.json.gz)

Archive Format:
-------------
Archives are JSON files containing:
- Archive metadata (created_at, record_count, date_range)
- Compressed audit log records
- Retention policy information
- Checksum for integrity verification

Compression:
----------
All archives are gzip-compressed by default to minimize storage costs.
Compression typically achieves 70-90% size reduction.
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


class ArchiveStorageError(Exception):
    """Exception raised for archive storage operation failures."""

    pass


class ArchiveStorageBackend(ABC):
    """Abstract base class for archive storage backends."""

    @abstractmethod
    def save_archive(
        self,
        archive_id: str,
        archive_data: dict[str, Any],
        compress: bool = True,
    ) -> dict[str, Any]:
        """
        Save archive to storage.

        Args:
            archive_id: Unique archive identifier
            archive_data: Archive data dictionary
            compress: Whether to compress the archive

        Returns:
            dict: Storage result with archive_id, size, checksum, etc.
        """
        pass

    @abstractmethod
    def get_archive(self, archive_id: str) -> dict[str, Any]:
        """
        Retrieve archive from storage.

        Args:
            archive_id: Archive identifier

        Returns:
            dict: Archive data

        Raises:
            ArchiveStorageError: If archive not found or retrieval fails
        """
        pass

    @abstractmethod
    def delete_archive(self, archive_id: str) -> bool:
        """
        Delete archive from storage.

        Args:
            archive_id: Archive identifier

        Returns:
            bool: True if deleted successfully
        """
        pass

    @abstractmethod
    def list_archives(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        List available archives.

        Args:
            start_date: Filter archives created after this date
            end_date: Filter archives created before this date

        Returns:
            list: Archive metadata list
        """
        pass

    @abstractmethod
    def exists(self, archive_id: str) -> bool:
        """
        Check if archive exists.

        Args:
            archive_id: Archive identifier

        Returns:
            bool: True if archive exists
        """
        pass

    def _compress_data(self, data: dict[str, Any]) -> bytes:
        """
        Compress archive data with gzip.

        Args:
            data: Archive data dictionary

        Returns:
            bytes: Compressed data
        """
        json_bytes = json.dumps(data, default=str).encode("utf-8")
        return gzip.compress(json_bytes)

    def _decompress_data(self, compressed_data: bytes) -> dict[str, Any]:
        """
        Decompress archive data.

        Args:
            compressed_data: Gzip-compressed data

        Returns:
            dict: Decompressed archive data
        """
        json_bytes = gzip.decompress(compressed_data)
        return json.loads(json_bytes)

    def _calculate_checksum(self, data: bytes) -> str:
        """
        Calculate SHA256 checksum for data integrity.

        Args:
            data: Data bytes

        Returns:
            str: Hex-encoded checksum
        """
        return hashlib.sha256(data).hexdigest()


class LocalArchiveStorage(ArchiveStorageBackend):
    """
    Local filesystem storage for audit log archives.

    Stores archives in organized directory structure:
    base_path/
        2025/
            01/
                archive-2025-01-01.json.gz
                archive-2025-01-02.json.gz
        2024/
            12/
                archive-2024-12-31.json.gz
    """

    def __init__(self, base_path: str | Path = "/var/audit/archives") -> None:
        """
        Initialize local archive storage.

        Args:
            base_path: Base directory for archive storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local archive storage initialized at {self.base_path}")

    def save_archive(
        self,
        archive_id: str,
        archive_data: dict[str, Any],
        compress: bool = True,
    ) -> dict[str, Any]:
        """
        Save archive to local filesystem.

        Args:
            archive_id: Archive identifier (e.g., "archive-2025-01-15")
            archive_data: Archive data
            compress: Whether to compress

        Returns:
            dict: Storage result
        """
        try:
            # Extract date from archive_id or use current date
            created_at = archive_data.get("created_at", datetime.utcnow())
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", ""))

                # Create date-based directory structure
            year_path = self.base_path / str(created_at.year)
            month_path = year_path / f"{created_at.month:02d}"
            month_path.mkdir(parents=True, exist_ok=True)

            # Determine filename
            filename = f"{archive_id}.json"
            if compress:
                filename += ".gz"
            archive_path = month_path / filename

            # Prepare data
            if compress:
                data_bytes = self._compress_data(archive_data)
            else:
                data_bytes = json.dumps(archive_data, default=str).encode("utf-8")

                # Calculate checksum
            checksum = self._calculate_checksum(data_bytes)

            # Write file
            archive_path.write_bytes(data_bytes)

            size_bytes = len(data_bytes)
            logger.info(
                f"Saved archive {archive_id} to {archive_path} "
                f"({size_bytes} bytes, compressed={compress})"
            )

            return {
                "archive_id": archive_id,
                "storage_path": str(archive_path),
                "size_bytes": size_bytes,
                "compressed": compress,
                "checksum": checksum,
                "backend": "local",
                "created_at": created_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to save archive {archive_id}: {e}")
            raise ArchiveStorageError(f"Failed to save archive: {e}")

    def get_archive(self, archive_id: str) -> dict[str, Any]:
        """
        Retrieve archive from local filesystem.

        Args:
            archive_id: Archive identifier

        Returns:
            dict: Archive data
        """
        archive_path = self._find_archive_path(archive_id)
        if not archive_path:
            raise ArchiveStorageError(f"Archive not found: {archive_id}")

        try:
            data_bytes = archive_path.read_bytes()

            # Detect if compressed
            if archive_path.suffix == ".gz":
                archive_data = self._decompress_data(data_bytes)
            else:
                archive_data = json.loads(data_bytes)

            logger.info(f"Retrieved archive {archive_id} from {archive_path}")
            return archive_data

        except Exception as e:
            logger.error(f"Failed to read archive {archive_id}: {e}")
            raise ArchiveStorageError(f"Failed to read archive: {e}")

    def delete_archive(self, archive_id: str) -> bool:
        """
        Delete archive from local filesystem.

        Args:
            archive_id: Archive identifier

        Returns:
            bool: True if deleted
        """
        archive_path = self._find_archive_path(archive_id)
        if not archive_path:
            return False

        try:
            archive_path.unlink()
            logger.info(f"Deleted archive {archive_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete archive {archive_id}: {e}")
            raise ArchiveStorageError(f"Failed to delete archive: {e}")

    def exists(self, archive_id: str) -> bool:
        """Check if archive exists."""
        archive_path = self._find_archive_path(archive_id)
        return archive_path is not None and archive_path.exists()

    def list_archives(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        List available archives.

        Args:
            start_date: Filter archives after this date
            end_date: Filter archives before this date

        Returns:
            list: Archive metadata
        """
        archives = []

        try:
            # Search all archive files
            for archive_path in self.base_path.rglob("archive-*.json*"):
                if not archive_path.is_file():
                    continue

                    # Extract metadata
                stat = archive_path.stat()
                created_at = datetime.fromtimestamp(stat.st_mtime)

                # Apply date filters
                if start_date and created_at < start_date:
                    continue
                if end_date and created_at > end_date:
                    continue

                archive_id = archive_path.stem
                if archive_id.endswith(".json"):
                    archive_id = archive_id[:-5]

                archives.append(
                    {
                        "archive_id": archive_id,
                        "storage_path": str(archive_path),
                        "size_bytes": stat.st_size,
                        "compressed": archive_path.suffix == ".gz",
                        "created_at": created_at.isoformat(),
                    }
                )

                # Sort by created_at descending
            archives.sort(key=lambda x: x["created_at"], reverse=True)
            return archives

        except Exception as e:
            logger.error(f"Failed to list archives: {e}")
            return []

    def _find_archive_path(self, archive_id: str) -> Path | None:
        """
        Find archive path by searching directory structure.

        Args:
            archive_id: Archive identifier

        Returns:
            Path: Archive path if found, None otherwise
        """
        # Search for both compressed and uncompressed versions
        for pattern in [f"{archive_id}.json.gz", f"{archive_id}.json"]:
            for archive_path in self.base_path.rglob(pattern):
                if archive_path.is_file():
                    return archive_path
        return None


class S3ArchiveStorage(ArchiveStorageBackend):
    """
    AWS S3 storage for audit log archives.

    Stores archives in S3 with:
    - Server-side encryption
    - Metadata tagging
    - Lifecycle policies support
    - Pre-signed URLs for retrieval
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_url: str | None = None,
        prefix: str = "audit-archives",
    ) -> None:
        """
        Initialize S3 archive storage.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key: AWS access key (optional)
            secret_key: AWS secret key (optional)
            endpoint_url: Custom S3 endpoint
            prefix: S3 key prefix for archives
        """
        try:
            import boto3
            from botocore.exceptions import ClientError

            self.ClientError = ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )

        self.bucket_name = bucket_name
        self.region = region
        self.prefix = prefix

        # Initialize S3 client
        session_kwargs = {}
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key

        client_kwargs = {"region_name": region}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        session = boto3.Session(**session_kwargs)
        self.s3_client = session.client("s3", **client_kwargs)

        logger.info(
            f"S3 archive storage initialized for bucket {bucket_name} "
            f"in {region} with prefix {prefix}"
        )

    def save_archive(
        self,
        archive_id: str,
        archive_data: dict[str, Any],
        compress: bool = True,
    ) -> dict[str, Any]:
        """
        Save archive to S3.

        Args:
            archive_id: Archive identifier
            archive_data: Archive data
            compress: Whether to compress

        Returns:
            dict: Storage result
        """
        try:
            # Extract date
            created_at = archive_data.get("created_at", datetime.utcnow())
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", ""))

                # Create S3 key with date-based prefix
            filename = f"{archive_id}.json"
            if compress:
                filename += ".gz"
            s3_key = (
                f"{self.prefix}/{created_at.year}/{created_at.month:02d}/{filename}"
            )

            # Prepare data
            if compress:
                data_bytes = self._compress_data(archive_data)
            else:
                data_bytes = json.dumps(archive_data, default=str).encode("utf-8")

                # Calculate checksum
            checksum = self._calculate_checksum(data_bytes)

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=data_bytes,
                ContentType="application/json" if not compress else "application/gzip",
                ServerSideEncryption="AES256",
                Metadata={
                    "archive_id": archive_id,
                    "created_at": created_at.isoformat(),
                    "compressed": str(compress),
                    "checksum": checksum,
                },
                Tagging=f"Type=AuditArchive&Year={created_at.year}",
            )

            size_bytes = len(data_bytes)
            logger.info(
                f"Uploaded archive {archive_id} to S3: {s3_key} "
                f"({size_bytes} bytes, compressed={compress})"
            )

            return {
                "archive_id": archive_id,
                "storage_path": s3_key,
                "size_bytes": size_bytes,
                "compressed": compress,
                "checksum": checksum,
                "backend": "s3",
                "bucket": self.bucket_name,
                "region": self.region,
                "created_at": created_at.isoformat(),
            }

        except self.ClientError as e:
            logger.error(f"S3 upload failed for {archive_id}: {e}")
            raise ArchiveStorageError(f"S3 upload failed: {e}")
        except Exception as e:
            logger.error(f"Failed to save archive to S3: {e}")
            raise ArchiveStorageError(f"Failed to save archive: {e}")

    def get_archive(self, archive_id: str) -> dict[str, Any]:
        """
        Retrieve archive from S3.

        Args:
            archive_id: Archive identifier

        Returns:
            dict: Archive data
        """
        s3_key = self._find_s3_key(archive_id)
        if not s3_key:
            raise ArchiveStorageError(f"Archive not found: {archive_id}")

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            data_bytes = response["Body"].read()

            # Check if compressed
            if s3_key.endswith(".gz"):
                archive_data = self._decompress_data(data_bytes)
            else:
                archive_data = json.loads(data_bytes)

            logger.info(f"Retrieved archive {archive_id} from S3: {s3_key}")
            return archive_data

        except self.ClientError as e:
            logger.error(f"Failed to get archive from S3: {e}")
            raise ArchiveStorageError(f"Failed to get archive: {e}")

    def delete_archive(self, archive_id: str) -> bool:
        """
        Delete archive from S3.

        Args:
            archive_id: Archive identifier

        Returns:
            bool: True if deleted
        """
        s3_key = self._find_s3_key(archive_id)
        if not s3_key:
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted archive {archive_id} from S3")
            return True
        except self.ClientError as e:
            logger.error(f"Failed to delete archive from S3: {e}")
            raise ArchiveStorageError(f"Failed to delete archive: {e}")

    def exists(self, archive_id: str) -> bool:
        """Check if archive exists in S3."""
        s3_key = self._find_s3_key(archive_id)
        if not s3_key:
            return False

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except self.ClientError:
            return False

    def list_archives(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        List available archives in S3.

        Args:
            start_date: Filter archives after this date
            end_date: Filter archives before this date

        Returns:
            list: Archive metadata
        """
        archives = []

        try:
            # List all objects with prefix
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

            for page in pages:
                for obj in page.get("Contents", []):
                    s3_key = obj["Key"]

                    # Extract archive_id from key
                    filename = Path(s3_key).name
                    archive_id = filename.replace(".json.gz", "").replace(".json", "")

                    # Get object metadata
                    created_at = obj["LastModified"]

                    # Apply date filters
                    if start_date and created_at < start_date.replace(
                        tzinfo=created_at.tzinfo
                    ):
                        continue
                    if end_date and created_at > end_date.replace(
                        tzinfo=created_at.tzinfo
                    ):
                        continue

                    archives.append(
                        {
                            "archive_id": archive_id,
                            "storage_path": s3_key,
                            "size_bytes": obj["Size"],
                            "compressed": s3_key.endswith(".gz"),
                            "created_at": created_at.isoformat(),
                        }
                    )

                    # Sort by created_at descending
            archives.sort(key=lambda x: x["created_at"], reverse=True)
            return archives

        except self.ClientError as e:
            logger.error(f"Failed to list S3 archives: {e}")
            return []

    def _find_s3_key(self, archive_id: str) -> str | None:
        """
        Find S3 key for archive ID.

        Args:
            archive_id: Archive identifier

        Returns:
            str: S3 key if found, None otherwise
        """
        try:
            # List objects with prefix
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)

            for page in pages:
                for obj in page.get("Contents", []):
                    if archive_id in obj["Key"]:
                        return obj["Key"]

            return None

        except self.ClientError as e:
            logger.error(f"Failed to find S3 key for {archive_id}: {e}")
            return None


def get_storage_backend(
    backend_type: str = "local",
    **kwargs: Any,
) -> ArchiveStorageBackend:
    """
    Get storage backend instance.

    Args:
        backend_type: 'local' or 's3'
        **kwargs: Backend-specific configuration

    Returns:
        ArchiveStorageBackend: Storage backend instance

    Raises:
        ValueError: If backend_type is not supported
    """
    if backend_type == "local":
        base_path = kwargs.get("base_path", "/var/audit/archives")
        return LocalArchiveStorage(base_path=base_path)

    elif backend_type == "s3":
        bucket_name = kwargs.get("bucket_name")
        if not bucket_name:
            raise ValueError("bucket_name is required for S3 storage")

        return S3ArchiveStorage(
            bucket_name=bucket_name,
            region=kwargs.get("region", "us-east-1"),
            access_key=kwargs.get("access_key"),
            secret_key=kwargs.get("secret_key"),
            endpoint_url=kwargs.get("endpoint_url"),
            prefix=kwargs.get("prefix", "audit-archives"),
        )

    else:
        raise ValueError(f"Unsupported storage backend: {backend_type}")
