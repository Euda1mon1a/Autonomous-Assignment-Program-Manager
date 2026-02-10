"""Tests for API deprecation management (no DB)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.middleware.versioning.deprecation import (
    DeprecationManager,
    DeprecationWarning,
    VersionStatus,
    get_deprecation_manager,
)


# ---------------------------------------------------------------------------
# VersionStatus enum
# ---------------------------------------------------------------------------


class TestVersionStatus:
    def test_values(self):
        assert VersionStatus.DEVELOPMENT == "development"
        assert VersionStatus.BETA == "beta"
        assert VersionStatus.STABLE == "stable"
        assert VersionStatus.DEPRECATED == "deprecated"
        assert VersionStatus.SUNSET == "sunset"
        assert VersionStatus.RETIRED == "retired"

    def test_count(self):
        assert len(VersionStatus) == 6

    def test_is_string_enum(self):
        assert isinstance(VersionStatus.STABLE, str)


# ---------------------------------------------------------------------------
# DeprecationWarning dataclass
# ---------------------------------------------------------------------------


class TestDeprecationWarning:
    def test_minimal(self):
        w = DeprecationWarning(
            endpoint="/api/v1/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
        )
        assert w.endpoint == "/api/v1/test"
        assert w.version == "v1"
        assert w.sunset_date is None
        assert w.replacement is None
        assert w.message is None
        assert w.documentation_url is None

    def test_full(self):
        sunset = datetime(2025, 6, 1)
        w = DeprecationWarning(
            endpoint="/api/v1/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=sunset,
            replacement="/api/v2/test",
            message="Use v2",
            documentation_url="https://docs.example.com/migrate",
        )
        assert w.sunset_date == sunset
        assert w.replacement == "/api/v2/test"
        assert w.message == "Use v2"
        assert w.documentation_url == "https://docs.example.com/migrate"

    # --- to_header_value ---

    def test_header_value_minimal(self):
        w = DeprecationWarning(
            endpoint="/api/v1/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
        )
        header = w.to_header_value()
        assert 'version="v1"' in header
        assert "sunset" not in header
        assert "replacement" not in header

    def test_header_value_with_sunset(self):
        sunset = datetime(2025, 6, 1, 0, 0, 0)
        w = DeprecationWarning(
            endpoint="/api/v1/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=sunset,
        )
        header = w.to_header_value()
        assert "sunset=" in header
        assert "2025-06-01" in header

    def test_header_value_with_replacement(self):
        w = DeprecationWarning(
            endpoint="/api/v1/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            replacement="/api/v2/test",
        )
        header = w.to_header_value()
        assert 'replacement="/api/v2/test"' in header

    def test_header_value_semicolon_separated(self):
        w = DeprecationWarning(
            endpoint="/api/v1/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=datetime(2025, 6, 1),
            replacement="/api/v2/test",
        )
        header = w.to_header_value()
        assert "; " in header

    # --- days_until_sunset ---

    def test_days_until_sunset_no_date(self):
        w = DeprecationWarning(
            endpoint="/test", version="v1", status=VersionStatus.DEPRECATED
        )
        assert w.days_until_sunset() is None

    def test_days_until_sunset_future(self):
        future = datetime.now() + timedelta(days=30)
        w = DeprecationWarning(
            endpoint="/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=future,
        )
        days = w.days_until_sunset()
        assert days is not None
        assert 29 <= days <= 30

    def test_days_until_sunset_past(self):
        past = datetime.now() - timedelta(days=10)
        w = DeprecationWarning(
            endpoint="/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=past,
        )
        assert w.days_until_sunset() == 0

    # --- is_past_sunset ---

    def test_is_past_sunset_no_date(self):
        w = DeprecationWarning(
            endpoint="/test", version="v1", status=VersionStatus.DEPRECATED
        )
        assert w.is_past_sunset() is False

    def test_is_past_sunset_future(self):
        future = datetime.now() + timedelta(days=30)
        w = DeprecationWarning(
            endpoint="/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=future,
        )
        assert w.is_past_sunset() is False

    def test_is_past_sunset_past(self):
        past = datetime.now() - timedelta(days=10)
        w = DeprecationWarning(
            endpoint="/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=past,
        )
        assert w.is_past_sunset() is True


# ---------------------------------------------------------------------------
# DeprecationManager — initialization
# ---------------------------------------------------------------------------


class TestDeprecationManagerInit:
    def test_has_default_deprecations(self):
        mgr = DeprecationManager()
        assert mgr.is_deprecated("/api/v1/swaps/legacy")
        assert mgr.is_deprecated("/api/v1/assignments/bulk")

    def test_default_version_status(self):
        mgr = DeprecationManager()
        assert mgr.get_version_status("v1") == VersionStatus.STABLE
        assert mgr.get_version_status("v2") == VersionStatus.STABLE
        assert mgr.get_version_status("v3") == VersionStatus.BETA

    def test_unknown_version_defaults_stable(self):
        mgr = DeprecationManager()
        assert mgr.get_version_status("v99") == VersionStatus.STABLE


# ---------------------------------------------------------------------------
# DeprecationManager — register / get / is_deprecated
# ---------------------------------------------------------------------------


class TestDeprecationManagerOps:
    def test_register_and_get(self):
        mgr = DeprecationManager()
        mgr.register_deprecation(
            endpoint="/api/v1/custom",
            version="v1",
            status=VersionStatus.DEPRECATED,
            message="Custom deprecation",
        )
        warning = mgr.get_deprecation("/api/v1/custom")
        assert warning is not None
        assert warning.message == "Custom deprecation"

    def test_get_nonexistent(self):
        mgr = DeprecationManager()
        assert mgr.get_deprecation("/api/v99/nothing") is None

    def test_is_deprecated_true(self):
        mgr = DeprecationManager()
        mgr.register_deprecation(
            endpoint="/test", version="v1", status=VersionStatus.DEPRECATED
        )
        assert mgr.is_deprecated("/test") is True

    def test_is_deprecated_false(self):
        mgr = DeprecationManager()
        assert mgr.is_deprecated("/nonexistent") is False

    def test_register_overwrite(self):
        mgr = DeprecationManager()
        mgr.register_deprecation(
            endpoint="/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            message="first",
        )
        mgr.register_deprecation(
            endpoint="/test",
            version="v2",
            status=VersionStatus.SUNSET,
            message="second",
        )
        warning = mgr.get_deprecation("/test")
        assert warning.version == "v2"
        assert warning.message == "second"


# ---------------------------------------------------------------------------
# DeprecationManager — version status
# ---------------------------------------------------------------------------


class TestVersionStatusManagement:
    def test_set_version_status(self):
        mgr = DeprecationManager()
        mgr.set_version_status("v1", VersionStatus.DEPRECATED)
        assert mgr.get_version_status("v1") == VersionStatus.DEPRECATED

    def test_set_new_version(self):
        mgr = DeprecationManager()
        mgr.set_version_status("v4", VersionStatus.DEVELOPMENT)
        assert mgr.get_version_status("v4") == VersionStatus.DEVELOPMENT


# ---------------------------------------------------------------------------
# DeprecationManager — get_all_deprecations
# ---------------------------------------------------------------------------


class TestGetAllDeprecations:
    def test_returns_list(self):
        mgr = DeprecationManager()
        result = mgr.get_all_deprecations()
        assert isinstance(result, list)
        assert len(result) >= 2  # Defaults

    def test_entries_have_required_keys(self):
        mgr = DeprecationManager()
        for entry in mgr.get_all_deprecations():
            assert "endpoint" in entry
            assert "version" in entry
            assert "status" in entry
            assert "sunset_date" in entry
            assert "replacement" in entry

    def test_sorted_by_sunset_date(self):
        mgr = DeprecationManager()
        result = mgr.get_all_deprecations()
        sunset_dates = [r["sunset_date"] for r in result if r["sunset_date"]]
        assert sunset_dates == sorted(sunset_dates)

    def test_custom_deprecation_included(self):
        mgr = DeprecationManager()
        mgr.register_deprecation(
            endpoint="/api/v1/custom",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=datetime(2099, 1, 1),
        )
        endpoints = [d["endpoint"] for d in mgr.get_all_deprecations()]
        assert "/api/v1/custom" in endpoints


# ---------------------------------------------------------------------------
# DeprecationManager — get_version_lifecycle
# ---------------------------------------------------------------------------


class TestGetVersionLifecycle:
    def test_returns_dict(self):
        mgr = DeprecationManager()
        result = mgr.get_version_lifecycle()
        assert isinstance(result, dict)

    def test_contains_default_versions(self):
        mgr = DeprecationManager()
        lifecycle = mgr.get_version_lifecycle()
        assert "v1" in lifecycle
        assert "v2" in lifecycle
        assert "v3" in lifecycle

    def test_entries_have_status_and_description(self):
        mgr = DeprecationManager()
        for version, info in mgr.get_version_lifecycle().items():
            assert "status" in info
            assert "description" in info
            assert isinstance(info["description"], str)
            assert len(info["description"]) > 0

    def test_stable_description(self):
        mgr = DeprecationManager()
        lifecycle = mgr.get_version_lifecycle()
        assert "production" in lifecycle["v1"]["description"].lower()

    def test_beta_description(self):
        mgr = DeprecationManager()
        lifecycle = mgr.get_version_lifecycle()
        assert "testing" in lifecycle["v3"]["description"].lower()


# ---------------------------------------------------------------------------
# _get_status_description
# ---------------------------------------------------------------------------


class TestStatusDescription:
    def test_all_statuses_have_descriptions(self):
        mgr = DeprecationManager()
        for status in VersionStatus:
            desc = mgr._get_status_description(status)
            assert isinstance(desc, str)
            assert len(desc) > 0
            assert desc != "Unknown status"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_returns_manager(self):
        mgr = get_deprecation_manager()
        assert isinstance(mgr, DeprecationManager)

    def test_returns_same_instance(self):
        mgr1 = get_deprecation_manager()
        mgr2 = get_deprecation_manager()
        assert mgr1 is mgr2
