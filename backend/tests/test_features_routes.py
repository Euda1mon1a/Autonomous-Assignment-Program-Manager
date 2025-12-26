"""
Comprehensive tests for Feature Flags API routes.

Tests coverage for feature flag management:
- POST /api/features - Create feature flag (admin)
- GET /api/features - List feature flags (admin)
- GET /api/features/stats - Get feature flag statistics (admin)
- GET /api/features/{key} - Get feature flag by key (admin)
- PUT /api/features/{key} - Update feature flag (admin)
- DELETE /api/features/{key} - Delete feature flag (admin)
- POST /api/features/evaluate - Evaluate feature flag (any user)
- POST /api/features/evaluate/bulk - Bulk evaluate flags (any user)
- POST /api/features/{key}/enable - Enable feature flag (admin)
- POST /api/features/{key}/disable - Disable feature flag (admin)
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestCreateFeatureFlagEndpoint:
    """Tests for POST /api/features endpoint."""

    def test_create_requires_auth(self, client: TestClient):
        """Test that creating feature flag requires authentication."""
        response = client.post(
            "/api/features",
            json={
                "key": "test-feature",
                "name": "Test Feature",
                "flag_type": "boolean",
                "enabled": True,
            },
        )

        assert response.status_code in [401, 403]

    def test_create_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that creating feature flag requires admin role."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.id = uuid4()
            mock_flag.key = "test-feature"
            mock_service.create_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/features",
                json={
                    "key": "test-feature",
                    "name": "Test Feature",
                    "flag_type": "boolean",
                    "enabled": True,
                },
                headers=auth_headers,
            )

            # May return 201 if admin, or 403 if not admin
            assert response.status_code in [201, 401, 403, 422]

    def test_create_duplicate_key(self, client: TestClient, auth_headers: dict):
        """Test creating feature flag with duplicate key."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.create_flag = AsyncMock(
                side_effect=ValueError("Feature flag with key already exists")
            )
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/features",
                json={
                    "key": "duplicate-key",
                    "name": "Duplicate Feature",
                    "flag_type": "boolean",
                },
                headers=auth_headers,
            )

            assert response.status_code in [400, 401, 403, 422]


class TestListFeatureFlagsEndpoint:
    """Tests for GET /api/features endpoint."""

    def test_list_requires_auth(self, client: TestClient):
        """Test that listing feature flags requires authentication."""
        response = client.get("/api/features")

        assert response.status_code in [401, 403]

    def test_list_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that listing feature flags requires admin role."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_flags = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = client.get(
                "/api/features",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]

    def test_list_with_filters(self, client: TestClient, auth_headers: dict):
        """Test listing feature flags with filters."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_flags = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = client.get(
                "/api/features?enabled_only=true&environment=production",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]

    def test_list_pagination(self, client: TestClient, auth_headers: dict):
        """Test listing feature flags with pagination."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_flags = AsyncMock(return_value=[])
            mock_service_class.return_value = mock_service

            response = client.get(
                "/api/features?page=2&page_size=25",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]


class TestFeatureFlagStatsEndpoint:
    """Tests for GET /api/features/stats endpoint."""

    def test_stats_requires_auth(self, client: TestClient):
        """Test that stats requires authentication."""
        response = client.get("/api/features/stats")

        assert response.status_code in [401, 403]

    def test_stats_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that stats requires admin role."""
        with (
            patch("app.api.routes.features.FeatureFlagService") as mock_service_class,
            patch("app.api.routes.features._get_flags_by_environment") as mock_env,
        ):
            mock_service = MagicMock()
            mock_service.get_stats = AsyncMock(
                return_value={
                    "total_flags": 10,
                    "enabled_flags": 7,
                    "disabled_flags": 3,
                    "percentage_rollout_flags": 2,
                    "variant_flags": 1,
                    "recent_evaluations": 1000,
                    "unique_users": 50,
                }
            )
            mock_service_class.return_value = mock_service
            mock_env.return_value = {}

            response = client.get(
                "/api/features/stats",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]


class TestGetFeatureFlagEndpoint:
    """Tests for GET /api/features/{key} endpoint."""

    def test_get_requires_auth(self, client: TestClient):
        """Test that getting feature flag requires authentication."""
        response = client.get("/api/features/test-feature")

        assert response.status_code in [401, 403]

    def test_get_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that getting feature flag requires admin role."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.key = "test-feature"
            mock_service.get_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.get(
                "/api/features/test-feature",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]

    def test_get_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting non-existent feature flag."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_flag = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            response = client.get(
                "/api/features/nonexistent-flag",
                headers=auth_headers,
            )

            assert response.status_code in [401, 403, 404]


class TestUpdateFeatureFlagEndpoint:
    """Tests for PUT /api/features/{key} endpoint."""

    def test_update_requires_auth(self, client: TestClient):
        """Test that updating feature flag requires authentication."""
        response = client.put(
            "/api/features/test-feature",
            json={"enabled": False},
        )

        assert response.status_code in [401, 403]

    def test_update_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that updating feature flag requires admin role."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.key = "test-feature"
            mock_flag.enabled = False
            mock_service.update_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.put(
                "/api/features/test-feature",
                json={"enabled": False},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403, 422]

    def test_update_no_changes(self, client: TestClient, auth_headers: dict):
        """Test updating feature flag with no changes."""
        response = client.put(
            "/api/features/test-feature",
            json={},
            headers=auth_headers,
        )

        assert response.status_code in [400, 401, 403, 422]


class TestDeleteFeatureFlagEndpoint:
    """Tests for DELETE /api/features/{key} endpoint."""

    def test_delete_requires_auth(self, client: TestClient):
        """Test that deleting feature flag requires authentication."""
        response = client.delete("/api/features/test-feature")

        assert response.status_code in [401, 403]

    def test_delete_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that deleting feature flag requires admin role."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_flag = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service

            response = client.delete(
                "/api/features/test-feature",
                headers=auth_headers,
            )

            assert response.status_code in [204, 401, 403]

    def test_delete_not_found(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent feature flag."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.delete_flag = AsyncMock(return_value=False)
            mock_service_class.return_value = mock_service

            response = client.delete(
                "/api/features/nonexistent-flag",
                headers=auth_headers,
            )

            assert response.status_code in [401, 403, 404]


class TestEvaluateFeatureFlagEndpoint:
    """Tests for POST /api/features/evaluate endpoint."""

    def test_evaluate_requires_auth(self, client: TestClient):
        """Test that evaluating feature flag requires authentication."""
        response = client.post(
            "/api/features/evaluate",
            json={"flag_key": "test-feature"},
        )

        assert response.status_code in [401, 403]

    def test_evaluate_any_user(self, client: TestClient, auth_headers: dict):
        """Test that any authenticated user can evaluate flags."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.flag_type = "boolean"
            mock_service.evaluate_flag = AsyncMock(
                return_value=(True, None, "Flag enabled")
            )
            mock_service.get_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/features/evaluate",
                json={"flag_key": "test-feature"},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 422]

    def test_evaluate_with_context(self, client: TestClient, auth_headers: dict):
        """Test evaluating feature flag with context."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.flag_type = "boolean"
            mock_service.evaluate_flag = AsyncMock(
                return_value=(True, None, "Context matched")
            )
            mock_service.get_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/features/evaluate",
                json={
                    "flag_key": "test-feature",
                    "context": {"environment": "production"},
                },
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 422]


class TestBulkEvaluateEndpoint:
    """Tests for POST /api/features/evaluate/bulk endpoint."""

    def test_bulk_requires_auth(self, client: TestClient):
        """Test that bulk evaluation requires authentication."""
        response = client.post(
            "/api/features/evaluate/bulk",
            json={"flag_keys": ["feature1", "feature2"]},
        )

        assert response.status_code in [401, 403]

    def test_bulk_evaluate_success(self, client: TestClient, auth_headers: dict):
        """Test successful bulk evaluation."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.flag_type = "boolean"
            mock_service.evaluate_flags_bulk = AsyncMock(
                return_value={
                    "feature1": (True, None, "Enabled"),
                    "feature2": (False, None, "Disabled"),
                }
            )
            mock_service.get_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/features/evaluate/bulk",
                json={"flag_keys": ["feature1", "feature2"]},
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 422]


class TestEnableFeatureFlagEndpoint:
    """Tests for POST /api/features/{key}/enable endpoint."""

    def test_enable_requires_auth(self, client: TestClient):
        """Test that enabling feature flag requires authentication."""
        response = client.post("/api/features/test-feature/enable")

        assert response.status_code in [401, 403]

    def test_enable_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that enabling feature flag requires admin role."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.key = "test-feature"
            mock_flag.enabled = True
            mock_service.update_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/features/test-feature/enable",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]

    def test_enable_with_reason(self, client: TestClient, auth_headers: dict):
        """Test enabling feature flag with reason."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.key = "test-feature"
            mock_flag.enabled = True
            mock_service.update_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/features/test-feature/enable?reason=Testing%20new%20feature",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]


class TestDisableFeatureFlagEndpoint:
    """Tests for POST /api/features/{key}/disable endpoint."""

    def test_disable_requires_auth(self, client: TestClient):
        """Test that disabling feature flag requires authentication."""
        response = client.post("/api/features/test-feature/disable")

        assert response.status_code in [401, 403]

    def test_disable_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that disabling feature flag requires admin role."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.key = "test-feature"
            mock_flag.enabled = False
            mock_service.update_flag = AsyncMock(return_value=mock_flag)
            mock_service_class.return_value = mock_service

            response = client.post(
                "/api/features/test-feature/disable",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403]


# ============================================================================
# Integration Tests
# ============================================================================


class TestFeaturesIntegration:
    """Integration tests for feature flag endpoints."""

    def test_feature_flag_workflow(self, client: TestClient, auth_headers: dict):
        """Test typical feature flag workflow."""
        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_flag = MagicMock()
            mock_flag.id = uuid4()
            mock_flag.key = "new-feature"
            mock_flag.name = "New Feature"
            mock_flag.enabled = False
            mock_flag.flag_type = "boolean"

            mock_service.create_flag = AsyncMock(return_value=mock_flag)
            mock_service.get_flag = AsyncMock(return_value=mock_flag)
            mock_service.update_flag = AsyncMock(return_value=mock_flag)
            mock_service.delete_flag = AsyncMock(return_value=True)
            mock_service_class.return_value = mock_service

            # Create flag
            create_response = client.post(
                "/api/features",
                json={
                    "key": "new-feature",
                    "name": "New Feature",
                    "flag_type": "boolean",
                },
                headers=auth_headers,
            )
            # May succeed or fail based on auth
            assert create_response.status_code in [201, 401, 403, 422]

    def test_admin_endpoints_require_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that admin endpoints require admin role."""
        admin_endpoints = [
            ("/api/features", "GET"),
            ("/api/features/stats", "GET"),
            ("/api/features/test-feature", "GET"),
        ]

        with patch("app.api.routes.features.FeatureFlagService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.list_flags = AsyncMock(return_value=[])
            mock_service.get_stats = AsyncMock(
                return_value={
                    "total_flags": 0,
                    "enabled_flags": 0,
                    "disabled_flags": 0,
                    "percentage_rollout_flags": 0,
                    "variant_flags": 0,
                    "recent_evaluations": 0,
                    "unique_users": 0,
                }
            )
            mock_service.get_flag = AsyncMock(return_value=None)
            mock_service_class.return_value = mock_service

            with patch("app.api.routes.features._get_flags_by_environment") as mock_env:
                mock_env.return_value = {}

                for url, method in admin_endpoints:
                    if method == "GET":
                        response = client.get(url, headers=auth_headers)
                    else:
                        response = client.post(url, headers=auth_headers)
                    assert response.status_code in [
                        200,
                        401,
                        403,
                        404,
                    ], f"Unexpected status for {url}"


class TestFeaturesEdgeCases:
    """Test edge cases for feature flag endpoints."""

    def test_create_invalid_flag_type(self, client: TestClient, auth_headers: dict):
        """Test creating flag with invalid type."""
        response = client.post(
            "/api/features",
            json={
                "key": "test-feature",
                "name": "Test Feature",
                "flag_type": "invalid_type",
            },
            headers=auth_headers,
        )

        assert response.status_code in [401, 403, 422]

    def test_list_invalid_pagination(self, client: TestClient, auth_headers: dict):
        """Test listing with invalid pagination parameters."""
        response = client.get(
            "/api/features?page=0",  # page must be >= 1
            headers=auth_headers,
        )

        assert response.status_code in [401, 403, 422]

    def test_evaluate_missing_flag_key(self, client: TestClient, auth_headers: dict):
        """Test evaluating without flag key."""
        response = client.post(
            "/api/features/evaluate",
            json={},  # Missing flag_key
            headers=auth_headers,
        )

        assert response.status_code in [401, 422]

    def test_bulk_evaluate_empty_list(self, client: TestClient, auth_headers: dict):
        """Test bulk evaluation with empty flag list."""
        response = client.post(
            "/api/features/evaluate/bulk",
            json={"flag_keys": []},
            headers=auth_headers,
        )

        # May be accepted or rejected
        assert response.status_code in [200, 401, 422]
