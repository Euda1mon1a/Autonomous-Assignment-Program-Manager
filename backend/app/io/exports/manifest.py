"""Export manifest generation and verification for data integrity.

This module provides cryptographic integrity verification for schedule exports
(Excel, Markdown, JSON). Each export is accompanied by a manifest containing
row count, SHA256 hash, and metadata for tamper detection.

Security Note:
    - Uses SHA256 for collision resistance
    - Canonical JSON serialization prevents hash variation
    - Manifest validation fails fast with descriptive error messages
    - No sensitive data (names, schedules) included in manifest
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


# Supported export types
ExportType = Literal["excel", "markdown", "json"]


class ExportManifest(BaseModel):
    """
    Cryptographic manifest for exported schedule data.

    Attributes:
        schema_version: Manifest format version (semver)
        row_count: Number of data rows in export
        sha256_rows: SHA256 hash of canonicalized row data
        generated_at: UTC timestamp (ISO8601 format)
        export_type: Type of export (excel/markdown/json)

    Example:
        >>> manifest = ExportManifest(
        ...     schema_version="1.0.0",
        ...     row_count=100,
        ...     sha256_rows="abc123...",
        ...     generated_at="2025-12-29T10:30:00Z",
        ...     export_type="excel"
        ... )
    """

    schema_version: str = Field(
        ...,
        description="Manifest schema version (semver)",
        pattern=r"^\d+\.\d+\.\d+$"
    )
    row_count: int = Field(
        ...,
        ge=0,
        description="Number of rows in export"
    )
    sha256_rows: str = Field(
        ...,
        description="SHA256 hash of canonicalized rows",
        min_length=64,
        max_length=64
    )
    generated_at: str = Field(
        ...,
        description="UTC timestamp in ISO8601 format"
    )
    export_type: ExportType = Field(
        ...,
        description="Type of export file"
    )

    @field_validator("generated_at")
    @classmethod
    def validate_iso8601(cls, v: str) -> str:
        """Validate ISO8601 timestamp format."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Invalid ISO8601 timestamp: {v}") from e
        return v

    @field_validator("sha256_rows")
    @classmethod
    def validate_hex_hash(cls, v: str) -> str:
        """Validate SHA256 hash is valid hexadecimal."""
        try:
            int(v, 16)
        except ValueError as e:
            raise ValueError(f"Invalid SHA256 hash (not hex): {v}") from e
        return v.lower()


def canonicalize_row(row: dict) -> str:
    """
    Convert a row dict to a deterministic canonical string representation.

    Uses JSON serialization with sorted keys and no whitespace to ensure
    the same row data always produces the same string, regardless of
    dict key ordering or insertion order.

    Args:
        row: Dictionary representing a single data row

    Returns:
        Canonical JSON string representation

    Example:
        >>> canonicalize_row({"name": "John", "id": 123})
        '{"id":123,"name":"John"}'
        >>> canonicalize_row({"id": 123, "name": "John"})
        '{"id":123,"name":"John"}'  # Same output despite different order
    """
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _compute_rows_hash(rows: list[dict]) -> str:
    """
    Compute SHA256 hash of canonicalized row data.

    Args:
        rows: List of row dictionaries

    Returns:
        Hexadecimal SHA256 hash string (lowercase)

    Raises:
        TypeError: If rows contain non-serializable data
    """
    hasher = hashlib.sha256()

    for row in rows:
        canonical = canonicalize_row(row)
        hasher.update(canonical.encode("utf-8"))

    return hasher.hexdigest()


def generate_manifest(
    rows: list[dict],
    schema_version: str,
    export_type: ExportType
) -> dict:
    """
    Generate export manifest with integrity metadata.

    Creates a cryptographic manifest containing row count, SHA256 hash,
    and metadata for the provided export data. The manifest can be used
    to verify data integrity after export/import.

    Args:
        rows: List of data rows (each row is a dict)
        schema_version: Manifest schema version (e.g., "1.0.0")
        export_type: Type of export ("excel", "markdown", "json")

    Returns:
        Manifest dictionary (can be serialized to JSON)

    Raises:
        ValueError: If schema_version is invalid or rows contain bad data
        TypeError: If rows contain non-JSON-serializable objects

    Example:
        >>> rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        >>> manifest = generate_manifest(rows, "1.0.0", "excel")
        >>> manifest["row_count"]
        2
        >>> len(manifest["sha256_rows"])
        64
    """
    logger.info(
        f"Generating manifest for {len(rows)} rows "
        f"(type={export_type}, schema={schema_version})"
    )

    # Compute hash
    sha256_rows = _compute_rows_hash(rows)

    # Generate UTC timestamp
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Create and validate manifest
    manifest = ExportManifest(
        schema_version=schema_version,
        row_count=len(rows),
        sha256_rows=sha256_rows,
        generated_at=generated_at,
        export_type=export_type
    )

    logger.debug(f"Generated manifest hash: {sha256_rows[:16]}...")
    return manifest.model_dump()


def write_manifest(manifest: dict, path: Path) -> None:
    """
    Write manifest to JSON file.

    Args:
        manifest: Manifest dictionary (from generate_manifest)
        path: Output file path (e.g., schedule.xlsx.manifest.json)

    Raises:
        IOError: If file cannot be written
        PermissionError: If insufficient permissions
        ValueError: If manifest is invalid

    Example:
        >>> manifest = generate_manifest(rows, "1.0.0", "excel")
        >>> write_manifest(manifest, Path("/tmp/export.xlsx.manifest.json"))
    """
    # Validate manifest structure
    ExportManifest(**manifest)

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote manifest to {path}")


def verify_manifest(rows: list[dict], manifest_path: Path) -> tuple[bool, str]:
    """
    Verify export data against stored manifest.

    Recomputes the SHA256 hash of the provided rows and compares it
    against the hash stored in the manifest file. Validates row count
    and manifest schema.

    Args:
        rows: Current row data to verify
        manifest_path: Path to manifest JSON file

    Returns:
        Tuple of (is_valid: bool, reason: str)
            - (True, "OK") if verification succeeds
            - (False, "reason") if verification fails

    Example:
        >>> rows = [{"id": 1, "name": "Alice"}]
        >>> valid, reason = verify_manifest(rows, Path("export.manifest.json"))
        >>> if not valid:
        ...     print(f"Verification failed: {reason}")

    Note:
        Does NOT raise exceptions - returns (False, reason) on failure
        for graceful error handling in export workflows.
    """
    # Check manifest file exists
    if not manifest_path.exists():
        return False, f"Manifest file not found: {manifest_path}"

    # Load and validate manifest
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        manifest = ExportManifest(**manifest_data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Invalid manifest file {manifest_path}: {e}")
        return False, f"Invalid manifest format: {e}"
    except IOError as e:
        logger.error(f"Cannot read manifest {manifest_path}: {e}")
        return False, f"Cannot read manifest: {e}"

    # Verify row count
    if len(rows) != manifest.row_count:
        return False, (
            f"Row count mismatch: expected {manifest.row_count}, "
            f"got {len(rows)}"
        )

    # Recompute hash
    try:
        computed_hash = _compute_rows_hash(rows)
    except (TypeError, ValueError) as e:
        logger.error(f"Cannot hash rows: {e}")
        return False, f"Cannot compute hash: {e}"

    # Verify hash
    if computed_hash != manifest.sha256_rows:
        logger.warning(
            f"Hash mismatch for {manifest_path}: "
            f"expected {manifest.sha256_rows[:16]}..., "
            f"got {computed_hash[:16]}..."
        )
        return False, "SHA256 hash mismatch - data has been modified"

    logger.info(f"Manifest verification passed for {manifest_path}")
    return True, "OK"
