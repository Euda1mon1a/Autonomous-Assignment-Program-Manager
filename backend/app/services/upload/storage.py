"""Storage backends for file uploads.

Provides abstraction layer for file storage with support for:
- Local filesystem storage
- AWS S3 storage
- Storage metadata tracking
"""

import logging
import shutil
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Exception raised for storage operation failures."""

    pass


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save(
        self,
        file_content: bytes | BinaryIO,
        filename: str,
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Save file to storage.

        Args:
            file_content: File content as bytes or file-like object
            filename: Target filename
            content_type: MIME type
            metadata: Additional metadata to store

        Returns:
            dict: Storage result with file_id, url, size, etc.
        """
        pass

    @abstractmethod
    def get(self, file_id: str) -> bytes:
        """
        Retrieve file from storage.

        Args:
            file_id: Unique file identifier

        Returns:
            bytes: File content

        Raises:
            StorageError: If file not found or retrieval fails
        """
        pass

    @abstractmethod
    def delete(self, file_id: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_id: Unique file identifier

        Returns:
            bool: True if deleted successfully
        """
        pass

    @abstractmethod
    def exists(self, file_id: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            file_id: Unique file identifier

        Returns:
            bool: True if file exists
        """
        pass

    @abstractmethod
    def get_url(self, file_id: str, expires_in: int = 3600) -> str:
        """
        Get URL to access file.

        Args:
            file_id: Unique file identifier
            expires_in: URL expiration time in seconds

        Returns:
            str: URL to access file
        """
        pass


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage backend.

    Stores files in a local directory with organized folder structure.
    """

    def __init__(self, base_path: str | Path = "/tmp/uploads"):
        """
        Initialize local storage backend.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage initialized at {self.base_path}")

    def save(
        self,
        file_content: bytes | BinaryIO,
        filename: str,
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Save file to local filesystem.

        Files are organized in subdirectories by date: YYYY/MM/DD/
        Each file gets a unique ID (UUID).

        Args:
            file_content: File content
            filename: Original filename
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            dict: Storage result
        """
        try:
            # Generate unique file ID
            file_id = str(uuid4())

            # Create date-based subdirectory structure
            now = datetime.utcnow()
            date_path = (
                self.base_path / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
            )
            date_path.mkdir(parents=True, exist_ok=True)

            # Determine file extension
            ext = Path(filename).suffix
            storage_filename = f"{file_id}{ext}"
            file_path = date_path / storage_filename

            # Write file
            if isinstance(file_content, bytes):
                file_path.write_bytes(file_content)
                size_bytes = len(file_content)
            else:
                # File-like object
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file_content, f)
                size_bytes = file_path.stat().st_size

            logger.info(f"Saved file {file_id} to {file_path} ({size_bytes} bytes)")

            return {
                "file_id": file_id,
                "filename": filename,
                "storage_path": str(file_path),
                "size_bytes": size_bytes,
                "content_type": content_type,
                "backend": "local",
                "created_at": now.isoformat(),
                "metadata": metadata or {},
            }

        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise StorageError(f"Failed to save file: {e}")

    def get(self, file_id: str) -> bytes:
        """
        Retrieve file from local filesystem.

        Args:
            file_id: Unique file identifier

        Returns:
            bytes: File content
        """
        file_path = self._find_file_path(file_id)
        if not file_path:
            raise StorageError(f"File not found: {file_id}")

        try:
            return file_path.read_bytes()
        except Exception as e:
            logger.error(f"Failed to read file {file_id}: {e}")
            raise StorageError(f"Failed to read file: {e}")

    def delete(self, file_id: str) -> bool:
        """
        Delete file from local filesystem.

        Args:
            file_id: Unique file identifier

        Returns:
            bool: True if deleted
        """
        file_path = self._find_file_path(file_id)
        if not file_path:
            return False

        try:
            file_path.unlink()
            logger.info(f"Deleted file {file_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_id}: {e}")
            raise StorageError(f"Failed to delete file: {e}")

    def exists(self, file_id: str) -> bool:
        """Check if file exists."""
        file_path = self._find_file_path(file_id)
        return file_path is not None and file_path.exists()

    def get_url(self, file_id: str, expires_in: int = 3600) -> str:
        """
        Get URL to access file.

        For local storage, returns a path-based URL.
        In production, this would be served through a web server.

        Args:
            file_id: File identifier
            expires_in: Not used for local storage

        Returns:
            str: File URL
        """
        if not self.exists(file_id):
            raise StorageError(f"File not found: {file_id}")

        # In production, this would be a proper URL served by nginx/apache
        return f"/api/v1/uploads/{file_id}"

    def _find_file_path(self, file_id: str) -> Path | None:
        """
        Find file path by searching date-based subdirectories.

        Args:
            file_id: File identifier

        Returns:
            Path: File path if found, None otherwise
        """
        # Search through date directories
        for file_path in self.base_path.rglob(f"{file_id}.*"):
            if file_path.is_file():
                return file_path
        return None


class S3StorageBackend(StorageBackend):
    """
    AWS S3 storage backend.

    Stores files in S3 with support for:
    - Multipart uploads
    - Pre-signed URLs
    - Server-side encryption
    - Metadata storage
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        access_key: str | None = None,
        secret_key: str | None = None,
        endpoint_url: str | None = None,
    ):
        """
        Initialize S3 storage backend.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key: AWS access key (optional, uses boto3 default chain)
            secret_key: AWS secret key (optional)
            endpoint_url: Custom S3 endpoint (for S3-compatible services)
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

        logger.info(f"S3 storage initialized for bucket {bucket_name} in {region}")

    def save(
        self,
        file_content: bytes | BinaryIO,
        filename: str,
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Save file to S3.

        Args:
            file_content: File content
            filename: Original filename
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            dict: Storage result
        """
        try:
            # Generate unique file ID
            file_id = str(uuid4())

            # Create S3 key with date-based prefix
            now = datetime.utcnow()
            ext = Path(filename).suffix
            s3_key = f"{now.year}/{now.month:02d}/{now.day:02d}/{file_id}{ext}"

            # Prepare metadata
            s3_metadata = metadata or {}
            s3_metadata["original_filename"] = filename
            s3_metadata["upload_timestamp"] = now.isoformat()

            # Upload to S3
            upload_args = {
                "Bucket": self.bucket_name,
                "Key": s3_key,
                "ContentType": content_type,
                "Metadata": {k: str(v) for k, v in s3_metadata.items()},
                "ServerSideEncryption": "AES256",
            }

            if isinstance(file_content, bytes):
                upload_args["Body"] = file_content
                size_bytes = len(file_content)
            else:
                upload_args["Body"] = file_content
                # Get size from file object
                file_content.seek(0, 2)  # Seek to end
                size_bytes = file_content.tell()
                file_content.seek(0)  # Reset to beginning

            self.s3_client.put_object(**upload_args)

            logger.info(f"Uploaded file {file_id} to S3: {s3_key} ({size_bytes} bytes)")

            return {
                "file_id": file_id,
                "filename": filename,
                "storage_path": s3_key,
                "size_bytes": size_bytes,
                "content_type": content_type,
                "backend": "s3",
                "bucket": self.bucket_name,
                "region": self.region,
                "created_at": now.isoformat(),
                "metadata": metadata or {},
            }

        except self.ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise StorageError(f"S3 upload failed: {e}")
        except Exception as e:
            logger.error(f"Failed to save file to S3: {e}")
            raise StorageError(f"Failed to save file: {e}")

    def get(self, file_id: str) -> bytes:
        """
        Retrieve file from S3.

        Args:
            file_id: File identifier

        Returns:
            bytes: File content
        """
        s3_key = self._find_s3_key(file_id)
        if not s3_key:
            raise StorageError(f"File not found: {file_id}")

        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response["Body"].read()
        except self.ClientError as e:
            logger.error(f"Failed to get file from S3: {e}")
            raise StorageError(f"Failed to get file: {e}")

    def delete(self, file_id: str) -> bool:
        """
        Delete file from S3.

        Args:
            file_id: File identifier

        Returns:
            bool: True if deleted
        """
        s3_key = self._find_s3_key(file_id)
        if not s3_key:
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted file {file_id} from S3")
            return True
        except self.ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            raise StorageError(f"Failed to delete file: {e}")

    def exists(self, file_id: str) -> bool:
        """Check if file exists in S3."""
        s3_key = self._find_s3_key(file_id)
        if not s3_key:
            return False

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except self.ClientError:
            return False

    def get_url(self, file_id: str, expires_in: int = 3600) -> str:
        """
        Generate pre-signed URL for S3 file.

        Args:
            file_id: File identifier
            expires_in: URL expiration time in seconds

        Returns:
            str: Pre-signed URL
        """
        s3_key = self._find_s3_key(file_id)
        if not s3_key:
            raise StorageError(f"File not found: {file_id}")

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expires_in,
            )
            return url
        except self.ClientError as e:
            logger.error(f"Failed to generate pre-signed URL: {e}")
            raise StorageError(f"Failed to generate URL: {e}")

    def _find_s3_key(self, file_id: str) -> str | None:
        """
        Find S3 key for file ID.

        Args:
            file_id: File identifier

        Returns:
            str: S3 key if found, None otherwise
        """
        try:
            # List objects with file_id prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix="", Delimiter="/"
            )

            # Search through years
            for year_prefix in response.get("CommonPrefixes", []):
                year = year_prefix["Prefix"]
                # Search through months
                month_response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name, Prefix=year, Delimiter="/"
                )
                for month_prefix in month_response.get("CommonPrefixes", []):
                    month = month_prefix["Prefix"]
                    # Search through days
                    day_response = self.s3_client.list_objects_v2(
                        Bucket=self.bucket_name, Prefix=month, Delimiter="/"
                    )
                    for day_prefix in day_response.get("CommonPrefixes", []):
                        day = day_prefix["Prefix"]
                        # Search files in day
                        files_response = self.s3_client.list_objects_v2(
                            Bucket=self.bucket_name, Prefix=day
                        )
                        for obj in files_response.get("Contents", []):
                            if file_id in obj["Key"]:
                                return obj["Key"]

            return None
        except self.ClientError as e:
            logger.error(f"Failed to find S3 key for {file_id}: {e}")
            return None
