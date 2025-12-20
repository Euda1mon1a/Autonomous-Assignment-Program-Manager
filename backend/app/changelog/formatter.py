"""
Changelog output formatters.

Supports multiple output formats:
- Markdown (for documentation)
- JSON (for programmatic access)
- HTML (for web display)
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any

from app.changelog.differ import APIChange, APIDiff, ChangeType


class OutputFormat(str, Enum):
    """Supported output formats for changelog."""

    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class ChangelogFormatter:
    """
    Formats API changes into various output formats.

    Supports:
    - Markdown for documentation
    - JSON for API responses
    - HTML for web display
    """

    def format(
        self,
        diff: APIDiff,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        include_migration_guide: bool = True,
    ) -> str:
        """
        Format API diff into specified output format.

        Args:
            diff: APIDiff to format
            output_format: Desired output format
            include_migration_guide: Include migration guides

        Returns:
            Formatted changelog string
        """
        if output_format == OutputFormat.MARKDOWN:
            return self._format_markdown(diff, include_migration_guide)
        elif output_format == OutputFormat.JSON:
            return self._format_json(diff, include_migration_guide)
        elif output_format == OutputFormat.HTML:
            return self._format_html(diff, include_migration_guide)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _format_markdown(self, diff: APIDiff, include_migration: bool) -> str:
        """Format as Markdown."""
        lines = []

        # Header
        lines.append(f"# API Changelog: {diff.old_version} → {diff.new_version}")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")

        # Summary
        suggested_version = diff.suggest_version_bump(diff.old_version)
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Old Version:** {diff.old_version}")
        lines.append(f"- **New Version:** {diff.new_version}")
        lines.append(f"- **Suggested Version:** {suggested_version}")
        lines.append(f"- **Total Changes:** {len(diff.changes)}")
        lines.append(f"- **Breaking Changes:** {len(diff.breaking_changes)}")
        lines.append(f"- **Non-Breaking Changes:** {len(diff.non_breaking_changes)}")
        lines.append("")

        # Breaking changes section
        if diff.breaking_changes:
            lines.append("## ⚠️ Breaking Changes")
            lines.append("")
            lines.append(
                "**WARNING:** These changes may break existing integrations. "
                "Review carefully and update your code accordingly."
            )
            lines.append("")

            for change in diff.breaking_changes:
                lines.extend(self._format_change_markdown(change, include_migration))
                lines.append("")

        # Non-breaking changes section
        if diff.non_breaking_changes:
            lines.append("## ✨ New Features & Improvements")
            lines.append("")

            for change in diff.non_breaking_changes:
                lines.extend(self._format_change_markdown(change, include_migration))
                lines.append("")

        # Migration guide
        if include_migration and diff.breaking_changes:
            lines.append("## 📖 Migration Guide")
            lines.append("")
            lines.append("Follow these steps to migrate to the new version:")
            lines.append("")

            for i, change in enumerate(diff.breaking_changes, 1):
                if change.migration_guide:
                    lines.append(f"### {i}. {change.description}")
                    lines.append("")
                    lines.append(change.migration_guide)
                    lines.append("")

        return "\n".join(lines)

    def _format_change_markdown(
        self,
        change: APIChange,
        include_migration: bool,
    ) -> list[str]:
        """Format a single change as Markdown."""
        lines = []

        # Icon based on change type
        icon = self._get_change_icon(change.change_type)
        prefix = f"### {icon} {change.description}"

        lines.append(prefix)
        lines.append("")

        # Details
        details = []
        if change.path:
            details.append(f"- **Endpoint:** `{change.method or ''} {change.path}`")
        if change.change_type:
            details.append(f"- **Type:** {change.change_type.value}")
        if change.breaking:
            details.append("- **Breaking:** Yes ⚠️")

        if change.old_value is not None:
            old_str = self._format_value(change.old_value)
            details.append(f"- **Old Value:** {old_str}")

        if change.new_value is not None:
            new_str = self._format_value(change.new_value)
            details.append(f"- **New Value:** {new_str}")

        lines.extend(details)

        # Migration guide (inline)
        if include_migration and change.migration_guide and not change.breaking:
            lines.append("")
            lines.append(f"**Note:** {change.migration_guide}")

        return lines

    def _format_json(self, diff: APIDiff, include_migration: bool) -> str:
        """Format as JSON."""
        data = {
            "old_version": diff.old_version,
            "new_version": diff.new_version,
            "suggested_version": diff.suggest_version_bump(diff.old_version),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_changes": len(diff.changes),
                "breaking_changes": len(diff.breaking_changes),
                "non_breaking_changes": len(diff.non_breaking_changes),
                "has_breaking_changes": diff.has_breaking_changes,
            },
            "changes": [
                self._change_to_dict(change, include_migration)
                for change in diff.changes
            ],
        }

        return json.dumps(data, indent=2, default=str)

    def _format_html(self, diff: APIDiff, include_migration: bool) -> str:
        """Format as HTML."""
        lines = []

        # Header
        lines.append("<!DOCTYPE html>")
        lines.append("<html>")
        lines.append("<head>")
        lines.append("<meta charset='utf-8'>")
        lines.append(f"<title>API Changelog: {diff.old_version} → {diff.new_version}</title>")
        lines.append("<style>")
        lines.append(self._get_html_styles())
        lines.append("</style>")
        lines.append("</head>")
        lines.append("<body>")

        # Title
        lines.append("<div class='container'>")
        lines.append(f"<h1>API Changelog: {diff.old_version} → {diff.new_version}</h1>")
        lines.append(f"<p class='meta'>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>")

        # Summary
        suggested_version = diff.suggest_version_bump(diff.old_version)
        lines.append("<div class='summary'>")
        lines.append("<h2>Summary</h2>")
        lines.append("<ul>")
        lines.append(f"<li><strong>Old Version:</strong> {diff.old_version}</li>")
        lines.append(f"<li><strong>New Version:</strong> {diff.new_version}</li>")
        lines.append(f"<li><strong>Suggested Version:</strong> {suggested_version}</li>")
        lines.append(f"<li><strong>Total Changes:</strong> {len(diff.changes)}</li>")
        lines.append(f"<li><strong>Breaking Changes:</strong> {len(diff.breaking_changes)}</li>")
        lines.append(f"<li><strong>Non-Breaking Changes:</strong> {len(diff.non_breaking_changes)}</li>")
        lines.append("</ul>")
        lines.append("</div>")

        # Breaking changes
        if diff.breaking_changes:
            lines.append("<div class='section breaking'>")
            lines.append("<h2>⚠️ Breaking Changes</h2>")
            lines.append(
                "<p class='warning'>These changes may break existing integrations. "
                "Review carefully and update your code accordingly.</p>"
            )
            for change in diff.breaking_changes:
                lines.extend(self._format_change_html(change, include_migration))
            lines.append("</div>")

        # Non-breaking changes
        if diff.non_breaking_changes:
            lines.append("<div class='section'>")
            lines.append("<h2>✨ New Features & Improvements</h2>")
            for change in diff.non_breaking_changes:
                lines.extend(self._format_change_html(change, include_migration))
            lines.append("</div>")

        # Migration guide
        if include_migration and diff.breaking_changes:
            lines.append("<div class='section migration'>")
            lines.append("<h2>📖 Migration Guide</h2>")
            for i, change in enumerate(diff.breaking_changes, 1):
                if change.migration_guide:
                    lines.append(f"<h3>{i}. {change.description}</h3>")
                    lines.append(f"<p>{change.migration_guide}</p>")
            lines.append("</div>")

        lines.append("</div>")
        lines.append("</body>")
        lines.append("</html>")

        return "\n".join(lines)

    def _format_change_html(
        self,
        change: APIChange,
        include_migration: bool,
    ) -> list[str]:
        """Format a single change as HTML."""
        lines = []

        css_class = "breaking" if change.breaking else "non-breaking"
        lines.append(f"<div class='change {css_class}'>")

        # Title
        icon = self._get_change_icon(change.change_type)
        lines.append(f"<h3>{icon} {change.description}</h3>")

        # Details
        lines.append("<ul>")
        if change.path:
            lines.append(f"<li><strong>Endpoint:</strong> <code>{change.method or ''} {change.path}</code></li>")
        if change.change_type:
            lines.append(f"<li><strong>Type:</strong> {change.change_type.value}</li>")
        if change.breaking:
            lines.append("<li><strong>Breaking:</strong> Yes ⚠️</li>")
        if change.old_value is not None:
            old_str = self._format_value(change.old_value)
            lines.append(f"<li><strong>Old Value:</strong> {old_str}</li>")
        if change.new_value is not None:
            new_str = self._format_value(change.new_value)
            lines.append(f"<li><strong>New Value:</strong> {new_str}</li>")
        lines.append("</ul>")

        # Migration guide
        if include_migration and change.migration_guide:
            lines.append(f"<p class='migration-note'><strong>Migration:</strong> {change.migration_guide}</p>")

        lines.append("</div>")

        return lines

    def _change_to_dict(self, change: APIChange, include_migration: bool) -> dict[str, Any]:
        """Convert APIChange to dictionary."""
        data = {
            "type": change.change_type.value,
            "path": change.path,
            "method": change.method,
            "description": change.description,
            "breaking": change.breaking,
        }

        if change.old_value is not None:
            data["old_value"] = change.old_value

        if change.new_value is not None:
            data["new_value"] = change.new_value

        if include_migration and change.migration_guide:
            data["migration_guide"] = change.migration_guide

        return data

    def _get_change_icon(self, change_type: ChangeType) -> str:
        """Get emoji icon for change type."""
        icons = {
            ChangeType.ENDPOINT_REMOVED: "🗑️",
            ChangeType.ENDPOINT_METHOD_REMOVED: "🗑️",
            ChangeType.REQUIRED_PARAM_ADDED: "⚠️",
            ChangeType.PARAM_REMOVED: "🗑️",
            ChangeType.PARAM_TYPE_CHANGED: "🔄",
            ChangeType.RESPONSE_SCHEMA_CHANGED: "🔄",
            ChangeType.RESPONSE_STATUS_REMOVED: "🗑️",
            ChangeType.ENDPOINT_ADDED: "✨",
            ChangeType.ENDPOINT_METHOD_ADDED: "✨",
            ChangeType.OPTIONAL_PARAM_ADDED: "➕",
            ChangeType.RESPONSE_STATUS_ADDED: "➕",
            ChangeType.RESPONSE_FIELD_ADDED: "➕",
            ChangeType.DESCRIPTION_CHANGED: "📝",
            ChangeType.EXAMPLE_CHANGED: "📝",
            ChangeType.DEPRECATED_ADDED: "⚠️",
            ChangeType.TAG_CHANGED: "🏷️",
            ChangeType.INTERNAL_CHANGE: "🔧",
        }
        return icons.get(change_type, "📌")

    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if isinstance(value, (list, dict)):
            return f"`{json.dumps(value)}`"
        return f"`{value}`"

    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML output."""
        return """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: #f5f5f5;
}

.container {
    background: white;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h1 {
    color: #1a1a1a;
    border-bottom: 3px solid #007bff;
    padding-bottom: 10px;
}

h2 {
    color: #2c3e50;
    margin-top: 30px;
}

h3 {
    color: #34495e;
    margin-top: 15px;
}

.meta {
    color: #666;
    font-size: 0.9em;
}

.summary {
    background: #f8f9fa;
    border-left: 4px solid #007bff;
    padding: 15px;
    margin: 20px 0;
}

.section {
    margin: 30px 0;
}

.section.breaking {
    border-left: 4px solid #dc3545;
    padding-left: 15px;
}

.section.migration {
    background: #fff3cd;
    border-left: 4px solid #ffc107;
    padding: 15px;
}

.change {
    background: #f8f9fa;
    border-radius: 4px;
    padding: 15px;
    margin: 15px 0;
    border-left: 4px solid #28a745;
}

.change.breaking {
    background: #fff5f5;
    border-left-color: #dc3545;
}

.warning {
    background: #fff3cd;
    border: 1px solid #ffc107;
    padding: 10px;
    border-radius: 4px;
    color: #856404;
}

.migration-note {
    background: #e7f3ff;
    border-left: 3px solid #007bff;
    padding: 10px;
    margin-top: 10px;
    font-size: 0.95em;
}

code {
    background: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
}

ul {
    list-style-type: none;
    padding-left: 0;
}

ul li {
    padding: 5px 0;
}
"""
