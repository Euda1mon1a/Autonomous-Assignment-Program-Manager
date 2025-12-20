"""Tests for API changelog generation."""

import json
import pytest
from datetime import datetime

from app.changelog.differ import APIDiffer, ChangeType
from app.changelog.formatter import ChangelogFormatter, OutputFormat
from app.changelog.generator import ChangelogGenerator


# Sample OpenAPI schemas for testing
SAMPLE_SCHEMA_V1 = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.0.0",
    },
    "paths": {
        "/users": {
            "get": {
                "summary": "List users",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer"},
                        "required": False,
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Success",
                    }
                },
            },
            "post": {
                "summary": "Create user",
                "responses": {
                    "201": {
                        "description": "Created",
                    }
                },
            },
        },
    },
}

SAMPLE_SCHEMA_V2_BREAKING = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "2.0.0",
    },
    "paths": {
        "/users": {
            "get": {
                "summary": "List users (updated)",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "string"},  # Type changed (breaking)
                        "required": False,
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer"},
                        "required": True,  # New required param (breaking)
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Success",
                    }
                },
            },
            # POST removed (breaking)
        },
        "/users/{id}": {  # New endpoint (non-breaking)
            "get": {
                "summary": "Get user by ID",
                "responses": {
                    "200": {
                        "description": "Success",
                    }
                },
            },
        },
    },
}

SAMPLE_SCHEMA_V1_1_NON_BREAKING = {
    "openapi": "3.0.0",
    "info": {
        "title": "Test API",
        "version": "1.1.0",
    },
    "paths": {
        "/users": {
            "get": {
                "summary": "List users",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer"},
                        "required": False,
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer"},
                        "required": False,  # New optional param (non-breaking)
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Success",
                    }
                },
            },
            "post": {
                "summary": "Create user",
                "responses": {
                    "201": {
                        "description": "Created",
                    }
                },
            },
        },
        "/users/{id}": {  # New endpoint (non-breaking)
            "get": {
                "summary": "Get user by ID",
                "responses": {
                    "200": {
                        "description": "Success",
                    }
                },
            },
        },
    },
}


class TestAPIDiffer:
    """Test API diff detection."""

    def test_detect_endpoint_removed(self):
        """Test detection of removed endpoint method."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        # Check that POST /users removal is detected
        removed_methods = [
            c for c in diff.changes
            if c.change_type == ChangeType.ENDPOINT_METHOD_REMOVED
        ]
        assert len(removed_methods) > 0
        assert any(c.path == "/users" and c.method == "POST" for c in removed_methods)

    def test_detect_endpoint_added(self):
        """Test detection of new endpoint."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        # Check that /users/{id} is detected as new
        added_endpoints = [
            c for c in diff.changes
            if c.change_type == ChangeType.ENDPOINT_ADDED
        ]
        assert any(c.path == "/users/{id}" for c in added_endpoints)

    def test_detect_required_param_added(self):
        """Test detection of new required parameter."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        # Check that required 'limit' param is detected
        required_params = [
            c for c in diff.changes
            if c.change_type == ChangeType.REQUIRED_PARAM_ADDED
        ]
        assert len(required_params) > 0
        assert any("limit" in c.description for c in required_params)

    def test_detect_param_type_changed(self):
        """Test detection of parameter type change."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        # Check that 'page' type change is detected
        type_changes = [
            c for c in diff.changes
            if c.change_type == ChangeType.PARAM_TYPE_CHANGED
        ]
        assert len(type_changes) > 0
        assert any("page" in c.description for c in type_changes)

    def test_detect_optional_param_added(self):
        """Test detection of optional parameter (non-breaking)."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V1_1_NON_BREAKING)

        # Check that optional 'limit' param is detected
        optional_params = [
            c for c in diff.changes
            if c.change_type == ChangeType.OPTIONAL_PARAM_ADDED
        ]
        assert len(optional_params) > 0
        assert any("limit" in c.description for c in optional_params)

    def test_breaking_changes_identified(self):
        """Test that breaking changes are correctly identified."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        # Should have breaking changes
        assert diff.has_breaking_changes
        assert len(diff.breaking_changes) > 0

        # All breaking changes should be marked as breaking
        for change in diff.breaking_changes:
            assert change.breaking

    def test_non_breaking_changes(self):
        """Test non-breaking changes detection."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V1_1_NON_BREAKING)

        # Should not have breaking changes
        assert not diff.has_breaking_changes

        # Should have non-breaking changes
        assert len(diff.non_breaking_changes) > 0

    def test_version_bump_suggestion_major(self):
        """Test major version bump suggestion for breaking changes."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        # Should suggest major version bump
        suggested = diff.suggest_version_bump("1.0.0")
        assert suggested == "2.0.0"

    def test_version_bump_suggestion_minor(self):
        """Test minor version bump suggestion for new features."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V1_1_NON_BREAKING)

        # Should suggest minor version bump
        suggested = diff.suggest_version_bump("1.0.0")
        assert suggested == "1.1.0"


class TestChangelogFormatter:
    """Test changelog formatting."""

    def test_format_markdown(self):
        """Test Markdown output format."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        formatter = ChangelogFormatter()
        markdown = formatter.format(diff, OutputFormat.MARKDOWN)

        # Check for key sections
        assert "# API Changelog" in markdown
        assert "## Summary" in markdown
        assert "## ⚠️ Breaking Changes" in markdown
        assert diff.old_version in markdown
        assert diff.new_version in markdown

    def test_format_json(self):
        """Test JSON output format."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        formatter = ChangelogFormatter()
        json_output = formatter.format(diff, OutputFormat.JSON)

        # Should be valid JSON
        data = json.loads(json_output)

        # Check structure
        assert "old_version" in data
        assert "new_version" in data
        assert "summary" in data
        assert "changes" in data

        # Check summary
        assert data["summary"]["breaking_changes"] > 0
        assert data["summary"]["total_changes"] > 0

    def test_format_html(self):
        """Test HTML output format."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        formatter = ChangelogFormatter()
        html = formatter.format(diff, OutputFormat.HTML)

        # Check for HTML structure
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "API Changelog" in html

    def test_migration_guide_included(self):
        """Test that migration guide is included when requested."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        formatter = ChangelogFormatter()
        markdown = formatter.format(
            diff,
            OutputFormat.MARKDOWN,
            include_migration_guide=True,
        )

        # Should include migration guide section
        assert "## 📖 Migration Guide" in markdown

    def test_migration_guide_excluded(self):
        """Test that migration guide can be excluded."""
        differ = APIDiffer()
        diff = differ.compare_schemas(SAMPLE_SCHEMA_V1, SAMPLE_SCHEMA_V2_BREAKING)

        formatter = ChangelogFormatter()
        markdown = formatter.format(
            diff,
            OutputFormat.MARKDOWN,
            include_migration_guide=False,
        )

        # Migration guide section should not be present
        assert "## 📖 Migration Guide" not in markdown


class TestChangelogGenerator:
    """Test changelog generator."""

    def test_generate_changelog(self, tmp_path):
        """Test basic changelog generation."""
        generator = ChangelogGenerator(storage_path=str(tmp_path))

        changelog = generator.generate_changelog(
            SAMPLE_SCHEMA_V1,
            SAMPLE_SCHEMA_V2_BREAKING,
            output_format=OutputFormat.MARKDOWN,
        )

        # Should be a non-empty string
        assert isinstance(changelog, str)
        assert len(changelog) > 0
        assert "API Changelog" in changelog

    def test_save_and_load_version(self, tmp_path):
        """Test saving and loading version snapshots."""
        generator = ChangelogGenerator(storage_path=str(tmp_path))

        # Save version
        version = generator.save_current_version(SAMPLE_SCHEMA_V1)
        assert version == "1.0.0"

        # Load version
        loaded = generator.version_history.load_version("1.0.0")
        assert loaded is not None
        assert loaded["version"] == "1.0.0"
        assert loaded["schema"] == SAMPLE_SCHEMA_V1

    def test_list_versions(self, tmp_path):
        """Test listing stored versions."""
        generator = ChangelogGenerator(storage_path=str(tmp_path))

        # Save multiple versions
        generator.save_current_version(SAMPLE_SCHEMA_V1)
        generator.save_current_version(SAMPLE_SCHEMA_V1_1_NON_BREAKING)

        # List versions
        versions = generator.list_versions()
        assert len(versions) >= 2

        # Check version info
        version_ids = [v["version"] for v in versions]
        assert "1.0.0" in version_ids
        assert "1.1.0" in version_ids

    def test_generate_from_versions(self, tmp_path):
        """Test generating changelog from stored versions."""
        generator = ChangelogGenerator(storage_path=str(tmp_path))

        # Save versions
        generator.save_current_version(SAMPLE_SCHEMA_V1)
        generator.save_current_version(SAMPLE_SCHEMA_V2_BREAKING)

        # Generate changelog
        changelog = generator.generate_from_versions(
            "1.0.0",
            "2.0.0",
            output_format=OutputFormat.MARKDOWN,
        )

        assert changelog is not None
        assert "1.0.0" in changelog
        assert "2.0.0" in changelog

    def test_generate_migration_guide(self, tmp_path):
        """Test migration guide generation."""
        generator = ChangelogGenerator(storage_path=str(tmp_path))

        guide = generator.generate_migration_guide(
            SAMPLE_SCHEMA_V1,
            SAMPLE_SCHEMA_V2_BREAKING,
        )

        # Should be a non-empty string
        assert isinstance(guide, str)
        assert len(guide) > 0
        assert "# Migration Guide" in guide
        assert "Table of Contents" in guide

    def test_suggest_version(self, tmp_path):
        """Test version suggestion."""
        generator = ChangelogGenerator(storage_path=str(tmp_path))

        # Breaking changes -> major bump
        suggested = generator.suggest_version(
            SAMPLE_SCHEMA_V1,
            SAMPLE_SCHEMA_V2_BREAKING,
        )
        assert suggested == "2.0.0"

        # Non-breaking changes -> minor bump
        suggested = generator.suggest_version(
            SAMPLE_SCHEMA_V1,
            SAMPLE_SCHEMA_V1_1_NON_BREAKING,
        )
        assert suggested == "1.1.0"

    def test_delete_version(self, tmp_path):
        """Test version deletion."""
        generator = ChangelogGenerator(storage_path=str(tmp_path))

        # Save version
        generator.save_current_version(SAMPLE_SCHEMA_V1)

        # Verify it exists
        loaded = generator.version_history.load_version("1.0.0")
        assert loaded is not None

        # Delete it
        deleted = generator.version_history.delete_version("1.0.0")
        assert deleted

        # Verify it's gone
        loaded = generator.version_history.load_version("1.0.0")
        assert loaded is None

    def test_version_not_found(self, tmp_path):
        """Test handling of non-existent versions."""
        generator = ChangelogGenerator(storage_path=str(tmp_path))

        # Try to generate changelog for non-existent versions
        changelog = generator.generate_from_versions(
            "1.0.0",
            "2.0.0",
            output_format=OutputFormat.MARKDOWN,
        )

        # Should return None
        assert changelog is None
