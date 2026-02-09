"""Tests for changelog schemas (defaults, nested models)."""

from app.schemas.changelog import (
    ChangelogRequest,
    ChangelogSchemaRequest,
    VersionSaveRequest,
    VersionInfo,
    VersionListResponse,
    VersionSaveResponse,
    ChangelogResponse,
    APIChangeDetail,
    APIDiffSummary,
    APIDiffResponse,
    MigrationGuideRequest,
    MigrationGuideResponse,
    VersionSuggestionRequest,
    VersionSuggestionResponse,
)


class TestChangelogRequest:
    def test_valid_defaults(self):
        r = ChangelogRequest(old_version="1.0.0", new_version="1.1.0")
        assert r.output_format == "markdown"
        assert r.include_migration_guide is True

    def test_custom_format(self):
        r = ChangelogRequest(
            old_version="1.0.0", new_version="1.1.0", output_format="json"
        )
        assert r.output_format == "json"


class TestChangelogSchemaRequest:
    def test_valid_defaults(self):
        r = ChangelogSchemaRequest(
            old_schema={"openapi": "3.0.0"},
            new_schema={"openapi": "3.1.0"},
        )
        assert r.output_format == "markdown"
        assert r.include_migration_guide is True


class TestVersionSaveRequest:
    def test_valid_minimal(self):
        r = VersionSaveRequest(schema={"openapi": "3.0.0"})
        assert r.version is None
        assert r.metadata is None

    def test_full(self):
        r = VersionSaveRequest(
            version="2.0.0",
            schema={"openapi": "3.0.0"},
            metadata={"commit": "abc123"},
        )
        assert r.version == "2.0.0"
        assert r.metadata["commit"] == "abc123"


class TestVersionInfo:
    def test_valid(self):
        r = VersionInfo(version="1.0.0", saved_at="2026-03-01T00:00:00Z")
        assert r.metadata == {}

    def test_with_metadata(self):
        r = VersionInfo(
            version="1.0.0",
            saved_at="2026-03-01T00:00:00Z",
            metadata={"tag": "release"},
        )
        assert r.metadata["tag"] == "release"


class TestVersionListResponse:
    def test_valid(self):
        info = VersionInfo(version="1.0.0", saved_at="2026-03-01T00:00:00Z")
        r = VersionListResponse(versions=[info], count=1)
        assert r.count == 1

    def test_empty(self):
        r = VersionListResponse(versions=[], count=0)
        assert r.versions == []


class TestVersionSaveResponse:
    def test_valid(self):
        r = VersionSaveResponse(
            version="1.0.0",
            message="Saved successfully",
            saved_at="2026-03-01T00:00:00Z",
        )
        assert r.message == "Saved successfully"


class TestChangelogResponse:
    def test_valid(self):
        r = ChangelogResponse(
            changelog="## Changes\n- Added feature X",
            format="markdown",
            old_version="1.0.0",
            new_version="1.1.0",
            generated_at="2026-03-01T00:00:00Z",
        )
        assert r.format == "markdown"


class TestAPIChangeDetail:
    def test_valid_minimal(self):
        r = APIChangeDetail(
            type="added",
            path="/api/v1/schedules",
            description="New endpoint for schedule generation",
            breaking=False,
        )
        assert r.method is None
        assert r.old_value is None
        assert r.new_value is None
        assert r.migration_guide is None

    def test_breaking_change(self):
        r = APIChangeDetail(
            type="removed",
            path="/api/v1/legacy",
            method="DELETE",
            description="Removed legacy endpoint",
            breaking=True,
            old_value={"responses": {"200": {}}},
            migration_guide="Use /api/v2/modern instead",
        )
        assert r.breaking is True
        assert r.migration_guide is not None


class TestAPIDiffSummary:
    def test_valid(self):
        r = APIDiffSummary(
            total_changes=10,
            breaking_changes=2,
            non_breaking_changes=8,
            has_breaking_changes=True,
        )
        assert r.has_breaking_changes is True

    def test_no_breaking(self):
        r = APIDiffSummary(
            total_changes=5,
            breaking_changes=0,
            non_breaking_changes=5,
            has_breaking_changes=False,
        )
        assert r.has_breaking_changes is False


class TestAPIDiffResponse:
    def test_valid(self):
        summary = APIDiffSummary(
            total_changes=1,
            breaking_changes=0,
            non_breaking_changes=1,
            has_breaking_changes=False,
        )
        change = APIChangeDetail(
            type="added",
            path="/api/v1/new",
            description="New endpoint",
            breaking=False,
        )
        r = APIDiffResponse(
            old_version="1.0.0",
            new_version="1.1.0",
            suggested_version="1.1.0",
            generated_at="2026-03-01T00:00:00Z",
            summary=summary,
            changes=[change],
        )
        assert len(r.changes) == 1


class TestMigrationGuideRequest:
    def test_valid(self):
        r = MigrationGuideRequest(old_version="1.0.0", new_version="2.0.0")
        assert r.old_version == "1.0.0"


class TestMigrationGuideResponse:
    def test_valid(self):
        r = MigrationGuideResponse(
            migration_guide="## Migration from 1.0 to 2.0\n...",
            old_version="1.0.0",
            new_version="2.0.0",
            breaking_changes_count=3,
            generated_at="2026-03-01T00:00:00Z",
        )
        assert r.breaking_changes_count == 3


class TestVersionSuggestionRequest:
    def test_valid(self):
        r = VersionSuggestionRequest(old_version="1.0.0", new_version="1.1.0")
        assert r.old_version == "1.0.0"


class TestVersionSuggestionResponse:
    def test_valid(self):
        r = VersionSuggestionResponse(
            current_version="1.0.0",
            suggested_version="2.0.0",
            reason="Breaking changes detected",
            breaking_changes=2,
            new_features=3,
            patch_changes=5,
        )
        assert r.suggested_version == "2.0.0"
        assert r.breaking_changes == 2
