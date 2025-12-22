"""
Tests for API versioning middleware.

Tests version detection, deprecation warnings, response transformation,
and version-aware routing.
"""
import pytest
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from app.middleware.versioning import (
    APIVersion,
    VersioningMiddleware,
    VersionedAPIRouter,
    DeprecationManager,
    VersionStatus,
    get_api_version,
    get_deprecation_manager,
    ResponseTransformer,
    TransformRegistry,
    transform_response,
)


class TestAPIVersion:
    """Test APIVersion enum and parsing."""

    def test_version_from_string_with_v_prefix(self):
        """Test parsing version with 'v' prefix."""
        assert APIVersion.from_string("v1") == APIVersion.V1
        assert APIVersion.from_string("v2") == APIVersion.V2
        assert APIVersion.from_string("v3") == APIVersion.V3

    def test_version_from_string_without_prefix(self):
        """Test parsing version without 'v' prefix."""
        assert APIVersion.from_string("1") == APIVersion.V1
        assert APIVersion.from_string("2") == APIVersion.V2
        assert APIVersion.from_string("3") == APIVersion.V3

    def test_version_from_string_with_minor_version(self):
        """Test parsing version with minor version number."""
        assert APIVersion.from_string("1.0") == APIVersion.V1
        assert APIVersion.from_string("2.1") == APIVersion.V2
        assert APIVersion.from_string("v3.2") == APIVersion.V3

    def test_version_from_string_invalid(self):
        """Test parsing invalid version strings."""
        assert APIVersion.from_string("invalid") is None
        assert APIVersion.from_string("") is None
        assert APIVersion.from_string("v99") is None

    def test_version_numeric_property(self):
        """Test numeric version property."""
        assert APIVersion.V1.numeric == 1
        assert APIVersion.V2.numeric == 2
        assert APIVersion.V3.numeric == 3

    def test_version_comparison(self):
        """Test version comparison operators."""
        assert APIVersion.V1 < APIVersion.V2
        assert APIVersion.V2 < APIVersion.V3
        assert APIVersion.V1 <= APIVersion.V1
        assert APIVersion.V2 <= APIVersion.V3


class TestVersioningMiddleware:
    """Test VersioningMiddleware functionality."""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app with versioning middleware."""
        test_app = FastAPI()

        # Add versioning middleware
        test_app.add_middleware(VersioningMiddleware)

        # Test endpoint
        @test_app.get("/api/v1/test")
        async def test_v1():
            version = get_api_version()
            return {"version": version.value, "data": "v1"}

        @test_app.get("/api/v2/test")
        async def test_v2():
            version = get_api_version()
            return {"version": version.value, "data": "v2"}

        @test_app.get("/api/v1/unversioned")
        async def test_unversioned():
            version = get_api_version()
            return {"version": version.value}

        return test_app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_version_detection_from_url(self, client):
        """Test version detection from URL path."""
        response = client.get("/api/v1/test")
        assert response.status_code == 200
        assert response.json()["version"] == "v1"

        response = client.get("/api/v2/test")
        assert response.status_code == 200
        assert response.json()["version"] == "v2"

    def test_version_detection_from_header(self, client):
        """Test version detection from Accept-Version header."""
        response = client.get(
            "/api/v1/unversioned",
            headers={"Accept-Version": "v2"}
        )
        # Header should override URL
        assert response.json()["version"] == "v2"

    def test_version_detection_from_query_param(self, client):
        """Test version detection from query parameter."""
        response = client.get("/api/v1/unversioned?version=2")
        # Query param should be used when no header
        assert response.json()["version"] == "v2"

        response = client.get("/api/v1/unversioned?api_version=v3")
        assert response.json()["version"] == "v3"

    def test_version_priority_order(self, client):
        """Test version detection priority: URL > Header > Query > Default."""
        # URL takes precedence over header
        response = client.get(
            "/api/v2/test",
            headers={"Accept-Version": "v1"}
        )
        assert response.json()["version"] == "v2"

    def test_default_version(self, client):
        """Test default version when none specified."""
        response = client.get("/api/v1/unversioned")
        assert response.json()["version"] == "v1"

    def test_version_headers_added_to_response(self, client):
        """Test that version headers are added to response."""
        response = client.get("/api/v2/test")
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v2"
        assert "X-API-Latest-Version" in response.headers


class TestDeprecationManager:
    """Test deprecation management functionality."""

    @pytest.fixture
    def deprecation_mgr(self):
        """Create fresh deprecation manager."""
        return DeprecationManager()

    def test_register_deprecation(self, deprecation_mgr):
        """Test registering a deprecated endpoint."""
        deprecation_mgr.register_deprecation(
            endpoint="/api/v1/old",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=datetime(2025, 12, 31),
            replacement="/api/v2/new",
            message="Use v2 endpoint",
        )

        assert deprecation_mgr.is_deprecated("/api/v1/old")
        warning = deprecation_mgr.get_deprecation("/api/v1/old")
        assert warning is not None
        assert warning.replacement == "/api/v2/new"

    def test_is_deprecated(self, deprecation_mgr):
        """Test checking if endpoint is deprecated."""
        assert not deprecation_mgr.is_deprecated("/api/v2/new")

        deprecation_mgr.register_deprecation(
            endpoint="/api/v1/old",
            version="v1",
            status=VersionStatus.DEPRECATED,
        )

        assert deprecation_mgr.is_deprecated("/api/v1/old")

    def test_sunset_date_calculation(self, deprecation_mgr):
        """Test sunset date calculations."""
        future_date = datetime.now() + timedelta(days=30)

        deprecation_mgr.register_deprecation(
            endpoint="/api/v1/test",
            version="v1",
            status=VersionStatus.SUNSET,
            sunset_date=future_date,
        )

        warning = deprecation_mgr.get_deprecation("/api/v1/test")
        days_remaining = warning.days_until_sunset()

        assert days_remaining is not None
        assert days_remaining >= 29  # Allow for test execution time
        assert not warning.is_past_sunset()

    def test_past_sunset(self, deprecation_mgr):
        """Test detection of past sunset dates."""
        past_date = datetime.now() - timedelta(days=30)

        deprecation_mgr.register_deprecation(
            endpoint="/api/v1/retired",
            version="v1",
            status=VersionStatus.RETIRED,
            sunset_date=past_date,
        )

        warning = deprecation_mgr.get_deprecation("/api/v1/retired")
        assert warning.is_past_sunset()

    def test_deprecation_header_value(self, deprecation_mgr):
        """Test deprecation header formatting."""
        deprecation_mgr.register_deprecation(
            endpoint="/api/v1/test",
            version="v1",
            status=VersionStatus.DEPRECATED,
            sunset_date=datetime(2025, 12, 31),
            replacement="/api/v2/test",
        )

        warning = deprecation_mgr.get_deprecation("/api/v1/test")
        header_value = warning.to_header_value()

        assert 'version="v1"' in header_value
        assert 'sunset="2025-12-31' in header_value
        assert 'replacement="/api/v2/test"' in header_value

    def test_version_status(self, deprecation_mgr):
        """Test version status management."""
        assert deprecation_mgr.get_version_status("v1") == VersionStatus.STABLE
        assert deprecation_mgr.get_version_status("v3") == VersionStatus.BETA

        deprecation_mgr.set_version_status("v1", VersionStatus.DEPRECATED)
        assert deprecation_mgr.get_version_status("v1") == VersionStatus.DEPRECATED

    def test_get_all_deprecations(self, deprecation_mgr):
        """Test retrieving all deprecations."""
        all_deprecations = deprecation_mgr.get_all_deprecations()
        assert isinstance(all_deprecations, list)

        # Should include default deprecations
        assert len(all_deprecations) > 0

        # Check structure
        for dep in all_deprecations:
            assert "endpoint" in dep
            assert "version" in dep
            assert "status" in dep


class TestVersionedAPIRouter:
    """Test version-aware routing."""

    @pytest.fixture
    def app(self):
        """Create test app with versioned router."""
        test_app = FastAPI()
        test_app.add_middleware(VersioningMiddleware)

        # Create versioned routers
        v1_router = VersionedAPIRouter(
            prefix="/api/v1",
            min_version=APIVersion.V1,
            max_version=APIVersion.V1,
        )

        v2_router = VersionedAPIRouter(
            prefix="/api/v2",
            min_version=APIVersion.V2,
        )

        @v1_router.get("/users")
        async def get_users_v1():
            return {"users": [], "format": "v1"}

        @v2_router.get("/users")
        async def get_users_v2():
            return {
                "data": {"users": []},
                "metadata": {"count": 0},
                "format": "v2"
            }

        test_app.include_router(v1_router)
        test_app.include_router(v2_router)

        return test_app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_version_specific_endpoints(self, client):
        """Test that different versions have different implementations."""
        v1_response = client.get("/api/v1/users")
        assert v1_response.status_code == 200
        assert v1_response.json()["format"] == "v1"

        v2_response = client.get("/api/v2/users")
        assert v2_response.status_code == 200
        assert v2_response.json()["format"] == "v2"

    def test_version_enforcement(self, client):
        """Test that version requirements are enforced."""
        # Try to access v2 endpoint with v3 version
        # This should work since no max_version set
        response = client.get(
            "/api/v2/users",
            headers={"Accept-Version": "v3"}
        )
        assert response.status_code == 200


class TestResponseTransformers:
    """Test response transformation functionality."""

    def test_date_format_transformer(self):
        """Test date format transformation."""
        from app.middleware.versioning.transformers import DateFormatTransformer

        transformer = DateFormatTransformer()

        # Test datetime transformation
        dt = datetime(2024, 1, 15, 10, 30, 0)

        v1_result = transformer.transform(dt, APIVersion.V1)
        assert v1_result == "2024-01-15"

        v2_result = transformer.transform(dt, APIVersion.V2)
        assert "2024-01-15" in v2_result
        assert "T" in v2_result  # ISO 8601 format

    def test_pagination_transformer(self):
        """Test pagination format transformation."""
        from app.middleware.versioning.transformers import PaginationTransformer

        transformer = PaginationTransformer()

        data = [{"id": 1}, {"id": 2}, {"id": 3}]

        # V1: flat list
        v1_result = transformer.transform(data, APIVersion.V1)
        assert isinstance(v1_result, list)
        assert len(v1_result) == 3

        # V2: wrapped with metadata
        v2_result = transformer.transform(data, APIVersion.V2)
        assert isinstance(v2_result, dict)
        assert "data" in v2_result
        assert "metadata" in v2_result
        assert v2_result["metadata"]["total"] == 3

    def test_field_rename_transformer(self):
        """Test field renaming transformation."""
        from app.middleware.versioning.transformers import FieldRenameTransformer

        mappings = {
            APIVersion.V1: {"person_id": "personId"},
            APIVersion.V2: {"person_id": "person_id"},
        }

        transformer = FieldRenameTransformer(mappings)

        data = {"person_id": "123", "name": "Test"}

        # V1: camelCase
        v1_result = transformer.transform(data, APIVersion.V1)
        assert "personId" in v1_result
        assert v1_result["personId"] == "123"

        # V2: snake_case
        v2_result = transformer.transform(data, APIVersion.V2)
        assert "person_id" in v2_result
        assert v2_result["person_id"] == "123"

    def test_transform_registry(self):
        """Test transform registry."""
        from app.middleware.versioning.transformers import (
            TransformRegistry,
            DateFormatTransformer,
        )

        registry = TransformRegistry()

        # Register custom transformer
        registry.register("test", DateFormatTransformer())

        # Verify registration
        transformer = registry.get("test")
        assert transformer is not None

    def test_transform_response_helper(self):
        """Test transform_response convenience function."""
        data = {
            "date": datetime(2024, 1, 15),
            "items": [1, 2, 3],
        }

        # Transform to v1
        result = transform_response(data, version=APIVersion.V1)
        assert isinstance(result, dict)


class TestVersionChangelog:
    """Test version changelog functionality."""

    def test_version_changelog_structure(self):
        """Test that version changelog has correct structure."""
        from app.middleware.versioning.middleware import version_changelog

        changelog = version_changelog()

        assert "v1" in changelog
        assert "v2" in changelog
        assert "v3" in changelog

        # Check v1 structure
        v1 = changelog["v1"]
        assert "version" in v1
        assert "released" in v1
        assert "status" in v1
        assert "features" in v1
        assert isinstance(v1["features"], list)

        # Check v2 has breaking changes
        v2 = changelog["v2"]
        assert "breaking_changes" in v2
        assert isinstance(v2["breaking_changes"], list)

    def test_changelog_contains_deprecations(self):
        """Test that changelog includes deprecation info."""
        from app.middleware.versioning.middleware import version_changelog

        changelog = version_changelog()
        v2 = changelog["v2"]

        assert "deprecations" in v2
        assert isinstance(v2["deprecations"], list)


class TestVersionIntegration:
    """Integration tests for versioning system."""

    @pytest.fixture
    def app(self):
        """Create full test app with versioning."""
        test_app = FastAPI()
        test_app.add_middleware(VersioningMiddleware)

        # Get deprecation manager
        dep_mgr = get_deprecation_manager()

        router = VersionedAPIRouter()

        @router.get("/current-version")
        async def get_current_version():
            version = get_api_version()
            return {"version": version.value}

        @router.get("/changelog")
        async def get_changelog():
            from app.middleware.versioning.middleware import version_changelog
            return version_changelog()

        @router.get("/deprecations")
        async def get_deprecations():
            return dep_mgr.get_all_deprecations()

        test_app.include_router(router)

        return test_app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_version_detection_integration(self, client):
        """Test end-to-end version detection."""
        # Test URL path detection
        response = client.get("/current-version?version=2")
        assert response.status_code == 200
        assert response.json()["version"] == "v2"

        # Test header detection
        response = client.get(
            "/current-version",
            headers={"Accept-Version": "v3"}
        )
        assert response.json()["version"] == "v3"

    def test_changelog_endpoint(self, client):
        """Test changelog endpoint."""
        response = client.get("/changelog")
        assert response.status_code == 200

        changelog = response.json()
        assert "v1" in changelog
        assert "v2" in changelog

    def test_deprecations_endpoint(self, client):
        """Test deprecations endpoint."""
        response = client.get("/deprecations")
        assert response.status_code == 200

        deprecations = response.json()
        assert isinstance(deprecations, list)
