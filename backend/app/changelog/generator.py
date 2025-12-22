"""
API changelog generator.

Orchestrates the changelog generation process:
- Fetches current and historical OpenAPI schemas
- Detects changes using APIDiffer
- Formats output using ChangelogFormatter
- Stores version history
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.changelog.differ import APIDiff, APIDiffer
from app.changelog.formatter import ChangelogFormatter, OutputFormat

logger = logging.getLogger(__name__)


class VersionHistory:
    """Manages version history storage and retrieval."""

    def __init__(self, storage_path: str = "/tmp/api_versions"):
        """
        Initialize version history manager.

        Args:
            storage_path: Directory to store version snapshots
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_version(
        self,
        version: str,
        schema: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Save an API version snapshot.

        Args:
            version: Version identifier (e.g., "1.0.0")
            schema: OpenAPI schema
            metadata: Additional metadata
        """
        version_file = self.storage_path / f"{version}.json"

        data = {
            "version": version,
            "schema": schema,
            "saved_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        with open(version_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved API version {version} to {version_file}")

    def load_version(self, version: str) -> dict[str, Any] | None:
        """
        Load an API version snapshot.

        Args:
            version: Version identifier

        Returns:
            Version data or None if not found
        """
        version_file = self.storage_path / f"{version}.json"

        if not version_file.exists():
            logger.warning(f"Version {version} not found at {version_file}")
            return None

        with open(version_file, "r") as f:
            data = json.load(f)

        return data

    def list_versions(self) -> list[dict[str, Any]]:
        """
        List all stored versions.

        Returns:
            List of version metadata (sorted by date, newest first)
        """
        versions = []

        for version_file in self.storage_path.glob("*.json"):
            try:
                with open(version_file, "r") as f:
                    data = json.load(f)
                    versions.append({
                        "version": data.get("version"),
                        "saved_at": data.get("saved_at"),
                        "metadata": data.get("metadata", {}),
                    })
            except Exception as e:
                logger.error(f"Error reading {version_file}: {e}")

        # Sort by saved_at timestamp (newest first)
        versions.sort(key=lambda v: v.get("saved_at", ""), reverse=True)

        return versions

    def delete_version(self, version: str) -> bool:
        """
        Delete a version snapshot.

        Args:
            version: Version identifier

        Returns:
            True if deleted, False if not found
        """
        version_file = self.storage_path / f"{version}.json"

        if version_file.exists():
            version_file.unlink()
            logger.info(f"Deleted version {version}")
            return True

        return False


class ChangelogGenerator:
    """
    Generates API changelogs by comparing OpenAPI schemas.

    Features:
    - Compare any two API versions
    - Detect breaking changes
    - Generate migration guides
    - Multiple output formats (Markdown, JSON, HTML)
    - Version history tracking
    """

    def __init__(self, storage_path: str = "/tmp/api_versions"):
        """
        Initialize changelog generator.

        Args:
            storage_path: Directory to store version history
        """
        self.differ = APIDiffer()
        self.formatter = ChangelogFormatter()
        self.version_history = VersionHistory(storage_path)

    def generate_changelog(
        self,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        include_migration_guide: bool = True,
    ) -> str:
        """
        Generate changelog from two OpenAPI schemas.

        Args:
            old_schema: Previous OpenAPI schema
            new_schema: New OpenAPI schema
            output_format: Output format (markdown, json, html)
            include_migration_guide: Include migration instructions

        Returns:
            Formatted changelog string
        """
        # Compare schemas
        diff = self.differ.compare_schemas(old_schema, new_schema)

        # Format output
        changelog = self.formatter.format(
            diff,
            output_format=output_format,
            include_migration_guide=include_migration_guide,
        )

        return changelog

    def generate_from_versions(
        self,
        old_version: str,
        new_version: str,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        include_migration_guide: bool = True,
    ) -> str | None:
        """
        Generate changelog from stored version snapshots.

        Args:
            old_version: Previous version identifier
            new_version: New version identifier
            output_format: Output format
            include_migration_guide: Include migration instructions

        Returns:
            Formatted changelog or None if versions not found
        """
        # Load versions
        old_data = self.version_history.load_version(old_version)
        new_data = self.version_history.load_version(new_version)

        if not old_data:
            logger.error(f"Old version {old_version} not found")
            return None

        if not new_data:
            logger.error(f"New version {new_version} not found")
            return None

        # Generate changelog
        return self.generate_changelog(
            old_data["schema"],
            new_data["schema"],
            output_format=output_format,
            include_migration_guide=include_migration_guide,
        )

    def save_current_version(
        self,
        current_schema: dict[str, Any],
        version: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Save current API schema as a version snapshot.

        Args:
            current_schema: Current OpenAPI schema
            version: Version identifier (auto-detected if None)
            metadata: Additional metadata to store

        Returns:
            Version identifier that was saved
        """
        # Auto-detect version from schema
        if version is None:
            version = current_schema.get("info", {}).get("version", "unknown")

        # Save version
        self.version_history.save_version(version, current_schema, metadata)

        return version

    def get_diff(
        self,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
    ) -> APIDiff:
        """
        Get structured diff between two schemas.

        Args:
            old_schema: Previous OpenAPI schema
            new_schema: New OpenAPI schema

        Returns:
            APIDiff object with all changes
        """
        return self.differ.compare_schemas(old_schema, new_schema)

    def list_versions(self) -> list[dict[str, Any]]:
        """
        List all stored API versions.

        Returns:
            List of version metadata
        """
        return self.version_history.list_versions()

    def generate_migration_guide(
        self,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
    ) -> str:
        """
        Generate detailed migration guide for breaking changes.

        Args:
            old_schema: Previous OpenAPI schema
            new_schema: New OpenAPI schema

        Returns:
            Markdown-formatted migration guide
        """
        diff = self.differ.compare_schemas(old_schema, new_schema)

        if not diff.breaking_changes:
            return "# Migration Guide\n\nNo breaking changes detected. Migration is not required."

        lines = []
        lines.append("# Migration Guide")
        lines.append("")
        lines.append(f"## Migrating from {diff.old_version} to {diff.new_version}")
        lines.append("")
        lines.append(
            f"This guide helps you migrate your application from version {diff.old_version} "
            f"to version {diff.new_version}. There are **{len(diff.breaking_changes)} breaking changes** "
            "that require your attention."
        )
        lines.append("")

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")
        for i, change in enumerate(diff.breaking_changes, 1):
            lines.append(f"{i}. {change.description}")
        lines.append("")

        # Detailed migration steps
        lines.append("## Detailed Migration Steps")
        lines.append("")

        for i, change in enumerate(diff.breaking_changes, 1):
            lines.append(f"### {i}. {change.description}")
            lines.append("")

            # Details
            if change.path:
                lines.append(f"**Affected Endpoint:** `{change.method or ''} {change.path}`")
                lines.append("")

            # Migration guide
            if change.migration_guide:
                lines.append("**Action Required:**")
                lines.append("")
                lines.append(change.migration_guide)
                lines.append("")

            # Technical details
            if change.old_value is not None or change.new_value is not None:
                lines.append("<details>")
                lines.append("<summary>Technical Details</summary>")
                lines.append("")
                if change.old_value is not None:
                    lines.append(f"**Before:** `{change.old_value}`")
                    lines.append("")
                if change.new_value is not None:
                    lines.append(f"**After:** `{change.new_value}`")
                    lines.append("")
                lines.append("</details>")
                lines.append("")

        # Testing recommendations
        lines.append("## Testing Recommendations")
        lines.append("")
        lines.append("After completing the migration, ensure you:")
        lines.append("")
        lines.append("1. Run your test suite to verify functionality")
        lines.append("2. Test all affected endpoints in a staging environment")
        lines.append("3. Monitor error logs for any integration issues")
        lines.append("4. Update your API documentation and client libraries")
        lines.append("")

        # Support
        lines.append("## Need Help?")
        lines.append("")
        lines.append("If you encounter issues during migration:")
        lines.append("")
        lines.append("- Review the API documentation")
        lines.append("- Check the example requests/responses")
        lines.append("- Contact the API support team")
        lines.append("")

        return "\n".join(lines)

    def suggest_version(
        self,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
    ) -> str:
        """
        Suggest next version number based on semantic versioning.

        Args:
            old_schema: Previous OpenAPI schema
            new_schema: New OpenAPI schema

        Returns:
            Suggested version string (e.g., "2.0.0")
        """
        diff = self.differ.compare_schemas(old_schema, new_schema)
        current_version = old_schema.get("info", {}).get("version", "1.0.0")
        return diff.suggest_version_bump(current_version)
