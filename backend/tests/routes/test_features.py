"""Tests for feature flag management API routes.

Tests the feature flag functionality including:
- CRUD operations for feature flags
- Flag evaluation (single and bulk)
- Statistics and audit logs
- Enable/disable toggles
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.models.user import User


class TestFeatureRoutes:
    """Test suite for feature flag API endpoints."""

    # ========================================================================
    # Authentication Tests
    # ========================================================================

    def test_create_flag_requires_auth(self, client: TestClient):
        """Test that creating flag requires authentication."""
        response = client.post(
            "/api/features/",
            json={
                "key": "test-flag",
                "name": "Test Flag",
                "flag_type": "boolean",
            },
        )
        assert response.status_code == 401

    def test_list_flags_requires_auth(self, client: TestClient):
        """Test that listing flags requires authentication."""
        response = client.get("/api/features/")
        assert response.status_code == 401

    def test_get_flag_requires_auth(self, client: TestClient):
        """Test that getting flag requires authentication."""
        response = client.get("/api/features/test-flag")
        assert response.status_code == 401

    def test_update_flag_requires_auth(self, client: TestClient):
        """Test that updating flag requires authentication."""
        response = client.put(
            "/api/features/test-flag",
            json={"enabled": True},
        )
        assert response.status_code == 401

    def test_delete_flag_requires_auth(self, client: TestClient):
        """Test that deleting flag requires authentication."""
        response = client.delete("/api/features/test-flag")
        assert response.status_code == 401

    def test_evaluate_flag_requires_auth(self, client: TestClient):
        """Test that evaluating flag requires authentication."""
        response = client.post(
            "/api/features/evaluate",
            json={"flag_key": "test-flag"},
        )
        assert response.status_code == 401

    def test_stats_requires_auth(self, client: TestClient):
        """Test that getting stats requires authentication."""
        response = client.get("/api/features/stats")
        assert response.status_code == 401

    # ========================================================================
    # Create Feature Flag Tests
    # ========================================================================

    @patch("app.api.routes.features.FeatureFlagService")
    def test_create_flag_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
        admin_user: User,
    ):
        """Test successful feature flag creation."""
        mock_service = MagicMock()
        mock_service.create_flag = AsyncMock(
            return_value=MagicMock(
                id=uuid4(),
                key="new-feature",
                name="New Feature",
                description="A new feature",
                flag_type="boolean",
                enabled=True,
                rollout_percentage=None,
                environments=["production"],
                target_user_ids=None,
                target_roles=None,
                variants=None,
                dependencies=None,
                custom_attributes=None,
                created_at="2025-01-15T10:00:00",
                updated_at="2025-01-15T10:00:00",
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/",
            headers=auth_headers,
            json={
                "key": "new-feature",
                "name": "New Feature",
                "description": "A new feature",
                "flag_type": "boolean",
                "enabled": True,
                "environments": ["production"],
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["key"] == "new-feature"
        assert data["enabled"] is True

    @patch("app.api.routes.features.FeatureFlagService")
    def test_create_flag_with_rollout(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test creating flag with percentage rollout."""
        mock_service = MagicMock()
        mock_service.create_flag = AsyncMock(
            return_value=MagicMock(
                id=uuid4(),
                key="rollout-flag",
                name="Rollout Flag",
                flag_type="percentage",
                enabled=True,
                rollout_percentage=0.5,
                environments=None,
                target_user_ids=None,
                target_roles=None,
                variants=None,
                dependencies=None,
                custom_attributes=None,
                created_at="2025-01-15T10:00:00",
                updated_at="2025-01-15T10:00:00",
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/",
            headers=auth_headers,
            json={
                "key": "rollout-flag",
                "name": "Rollout Flag",
                "flag_type": "percentage",
                "enabled": True,
                "rollout_percentage": 0.5,
            },
        )
        assert response.status_code == 201

    @patch("app.api.routes.features.FeatureFlagService")
    def test_create_flag_with_variants(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test creating flag with variant options."""
        variants = [
            {"key": "control", "weight": 50},
            {"key": "treatment", "weight": 50},
        ]
        mock_service = MagicMock()
        mock_service.create_flag = AsyncMock(
            return_value=MagicMock(
                id=uuid4(),
                key="ab-test-flag",
                name="A/B Test Flag",
                flag_type="variant",
                enabled=True,
                rollout_percentage=None,
                environments=None,
                target_user_ids=None,
                target_roles=None,
                variants=variants,
                dependencies=None,
                custom_attributes=None,
                created_at="2025-01-15T10:00:00",
                updated_at="2025-01-15T10:00:00",
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/",
            headers=auth_headers,
            json={
                "key": "ab-test-flag",
                "name": "A/B Test Flag",
                "flag_type": "variant",
                "enabled": True,
                "variants": variants,
            },
        )
        assert response.status_code == 201

    @patch("app.api.routes.features.FeatureFlagService")
    def test_create_flag_duplicate_key(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test creating flag with duplicate key fails."""
        mock_service = MagicMock()
        mock_service.create_flag = AsyncMock(
            side_effect=ValueError("Flag with key 'existing-flag' already exists")
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/",
            headers=auth_headers,
            json={
                "key": "existing-flag",
                "name": "Existing Flag",
                "flag_type": "boolean",
            },
        )
        assert response.status_code == 400

    # ========================================================================
    # List Feature Flags Tests
    # ========================================================================

    @patch("app.api.routes.features.FeatureFlagService")
    def test_list_flags_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test listing feature flags."""
        mock_flags = [
            MagicMock(key="flag-1", name="Flag 1", enabled=True),
            MagicMock(key="flag-2", name="Flag 2", enabled=False),
        ]
        mock_service = MagicMock()
        mock_service.list_flags = AsyncMock(return_value=mock_flags)
        mock_service_class.return_value = mock_service

        response = client.get("/api/features/", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "flags" in data
        assert "total" in data
        assert data["total"] == 2

    @patch("app.api.routes.features.FeatureFlagService")
    def test_list_flags_enabled_only(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test listing only enabled flags."""
        mock_flags = [MagicMock(key="flag-1", name="Flag 1", enabled=True)]
        mock_service = MagicMock()
        mock_service.list_flags = AsyncMock(return_value=mock_flags)
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/features/?enabled_only=true",
            headers=auth_headers,
        )
        assert response.status_code == 200

        mock_service.list_flags.assert_called_once_with(
            enabled_only=True, environment=None
        )

    @patch("app.api.routes.features.FeatureFlagService")
    def test_list_flags_by_environment(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test listing flags filtered by environment."""
        mock_service = MagicMock()
        mock_service.list_flags = AsyncMock(return_value=[])
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/features/?environment=production",
            headers=auth_headers,
        )
        assert response.status_code == 200

        mock_service.list_flags.assert_called_once_with(
            enabled_only=False, environment="production"
        )

    @patch("app.api.routes.features.FeatureFlagService")
    def test_list_flags_pagination(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test listing flags with pagination."""
        mock_flags = [MagicMock(key=f"flag-{i}") for i in range(100)]
        mock_service = MagicMock()
        mock_service.list_flags = AsyncMock(return_value=mock_flags)
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/features/?page=2&page_size=25",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 25
        assert data["total"] == 100
        assert data["total_pages"] == 4

    # ========================================================================
    # Get Feature Flag Tests
    # ========================================================================

    @patch("app.api.routes.features.FeatureFlagService")
    def test_get_flag_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting a specific feature flag."""
        mock_service = MagicMock()
        mock_service.get_flag = AsyncMock(
            return_value=MagicMock(
                id=uuid4(),
                key="test-flag",
                name="Test Flag",
                description="A test flag",
                flag_type="boolean",
                enabled=True,
                rollout_percentage=None,
                environments=["development", "staging"],
                target_user_ids=None,
                target_roles=None,
                variants=None,
                dependencies=None,
                custom_attributes=None,
                created_at="2025-01-15T10:00:00",
                updated_at="2025-01-15T10:00:00",
            )
        )
        mock_service_class.return_value = mock_service

        response = client.get("/api/features/test-flag", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["key"] == "test-flag"

    @patch("app.api.routes.features.FeatureFlagService")
    def test_get_flag_not_found(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting non-existent flag."""
        mock_service = MagicMock()
        mock_service.get_flag = AsyncMock(return_value=None)
        mock_service_class.return_value = mock_service

        response = client.get("/api/features/nonexistent", headers=auth_headers)
        assert response.status_code == 404

    # ========================================================================
    # Update Feature Flag Tests
    # ========================================================================

    @patch("app.api.routes.features.FeatureFlagService")
    def test_update_flag_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test updating a feature flag."""
        mock_service = MagicMock()
        mock_service.update_flag = AsyncMock(
            return_value=MagicMock(
                id=uuid4(),
                key="test-flag",
                name="Updated Flag Name",
                enabled=False,
                rollout_percentage=0.25,
                created_at="2025-01-15T10:00:00",
                updated_at="2025-01-15T11:00:00",
            )
        )
        mock_service_class.return_value = mock_service

        response = client.put(
            "/api/features/test-flag?reason=testing",
            headers=auth_headers,
            json={
                "name": "Updated Flag Name",
                "enabled": False,
                "rollout_percentage": 0.25,
            },
        )
        assert response.status_code == 200

    @patch("app.api.routes.features.FeatureFlagService")
    def test_update_flag_not_found(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test updating non-existent flag."""
        mock_service = MagicMock()
        mock_service.update_flag = AsyncMock(side_effect=ValueError("Flag not found"))
        mock_service_class.return_value = mock_service

        response = client.put(
            "/api/features/nonexistent",
            headers=auth_headers,
            json={"enabled": True},
        )
        assert response.status_code == 404

    @patch("app.api.routes.features.FeatureFlagService")
    def test_update_flag_no_updates(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test updating flag with empty update body."""
        response = client.put(
            "/api/features/test-flag",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 400

    # ========================================================================
    # Delete Feature Flag Tests
    # ========================================================================

    @patch("app.api.routes.features.FeatureFlagService")
    def test_delete_flag_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test deleting a feature flag."""
        mock_service = MagicMock()
        mock_service.delete_flag = AsyncMock(return_value=True)
        mock_service_class.return_value = mock_service

        response = client.delete(
            "/api/features/test-flag?reason=cleanup",
            headers=auth_headers,
        )
        assert response.status_code == 204

    @patch("app.api.routes.features.FeatureFlagService")
    def test_delete_flag_not_found(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test deleting non-existent flag."""
        mock_service = MagicMock()
        mock_service.delete_flag = AsyncMock(return_value=False)
        mock_service_class.return_value = mock_service

        response = client.delete("/api/features/nonexistent", headers=auth_headers)
        assert response.status_code == 404

    # ========================================================================
    # Evaluate Feature Flag Tests
    # ========================================================================

    @patch("app.api.routes.features.FeatureFlagService")
    def test_evaluate_flag_enabled(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test evaluating an enabled flag."""
        mock_service = MagicMock()
        mock_service.evaluate_flag = AsyncMock(
            return_value=(True, None, "flag enabled")
        )
        mock_service.get_flag = AsyncMock(return_value=MagicMock(flag_type="boolean"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/evaluate",
            headers=auth_headers,
            json={"flag_key": "test-flag"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is True
        assert data["flag_type"] == "boolean"

    @patch("app.api.routes.features.FeatureFlagService")
    def test_evaluate_flag_disabled(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test evaluating a disabled flag."""
        mock_service = MagicMock()
        mock_service.evaluate_flag = AsyncMock(
            return_value=(False, None, "flag disabled")
        )
        mock_service.get_flag = AsyncMock(return_value=MagicMock(flag_type="boolean"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/evaluate",
            headers=auth_headers,
            json={"flag_key": "disabled-flag"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is False

    @patch("app.api.routes.features.FeatureFlagService")
    def test_evaluate_flag_with_variant(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test evaluating a variant flag."""
        mock_service = MagicMock()
        mock_service.evaluate_flag = AsyncMock(
            return_value=(True, "treatment", "variant selected")
        )
        mock_service.get_flag = AsyncMock(return_value=MagicMock(flag_type="variant"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/evaluate",
            headers=auth_headers,
            json={"flag_key": "ab-test-flag"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is True
        assert data["variant"] == "treatment"
        assert data["flag_type"] == "variant"

    @patch("app.api.routes.features.FeatureFlagService")
    def test_evaluate_flag_with_context(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test evaluating flag with custom context."""
        mock_service = MagicMock()
        mock_service.evaluate_flag = AsyncMock(
            return_value=(True, None, "context matched")
        )
        mock_service.get_flag = AsyncMock(return_value=MagicMock(flag_type="boolean"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/evaluate",
            headers=auth_headers,
            json={
                "flag_key": "context-flag",
                "context": {"department": "cardiology", "shift": "night"},
            },
        )
        assert response.status_code == 200

    # ========================================================================
    # Bulk Evaluate Feature Flags Tests
    # ========================================================================

    @patch("app.api.routes.features.FeatureFlagService")
    def test_evaluate_flags_bulk_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test bulk evaluation of feature flags."""
        mock_service = MagicMock()
        mock_service.evaluate_flags_bulk = AsyncMock(
            return_value={
                "flag-1": (True, None, "enabled"),
                "flag-2": (False, None, "disabled"),
                "flag-3": (True, "treatment", "variant selected"),
            }
        )
        mock_service.get_flag = AsyncMock(
            side_effect=[
                MagicMock(flag_type="boolean"),
                MagicMock(flag_type="boolean"),
                MagicMock(flag_type="variant"),
            ]
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/evaluate/bulk",
            headers=auth_headers,
            json={"flag_keys": ["flag-1", "flag-2", "flag-3"]},
        )
        assert response.status_code == 200

        data = response.json()
        assert "flags" in data
        assert len(data["flags"]) == 3
        assert data["flags"]["flag-1"]["enabled"] is True
        assert data["flags"]["flag-2"]["enabled"] is False
        assert data["flags"]["flag-3"]["variant"] == "treatment"

    @patch("app.api.routes.features.FeatureFlagService")
    def test_evaluate_flags_bulk_empty(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test bulk evaluation with no flags."""
        mock_service = MagicMock()
        mock_service.evaluate_flags_bulk = AsyncMock(return_value={})
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/evaluate/bulk",
            headers=auth_headers,
            json={"flag_keys": []},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["flags"] == {}

    # ========================================================================
    # Enable/Disable Toggle Tests
    # ========================================================================

    @patch("app.api.routes.features.FeatureFlagService")
    def test_enable_flag_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test enabling a feature flag."""
        mock_service = MagicMock()
        mock_service.update_flag = AsyncMock(
            return_value=MagicMock(
                key="test-flag",
                enabled=True,
                created_at="2025-01-15T10:00:00",
                updated_at="2025-01-15T11:00:00",
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/test-flag/enable",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is True

    @patch("app.api.routes.features.FeatureFlagService")
    def test_enable_flag_not_found(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test enabling non-existent flag."""
        mock_service = MagicMock()
        mock_service.update_flag = AsyncMock(side_effect=ValueError("Flag not found"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/nonexistent/enable",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @patch("app.api.routes.features.FeatureFlagService")
    def test_disable_flag_success(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test disabling a feature flag."""
        mock_service = MagicMock()
        mock_service.update_flag = AsyncMock(
            return_value=MagicMock(
                key="test-flag",
                enabled=False,
                created_at="2025-01-15T10:00:00",
                updated_at="2025-01-15T11:00:00",
            )
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/test-flag/disable?reason=maintenance",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is False

    @patch("app.api.routes.features.FeatureFlagService")
    def test_disable_flag_not_found(
        self,
        mock_service_class: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test disabling non-existent flag."""
        mock_service = MagicMock()
        mock_service.update_flag = AsyncMock(side_effect=ValueError("Flag not found"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/features/nonexistent/disable",
            headers=auth_headers,
        )
        assert response.status_code == 404

    # ========================================================================
    # Statistics Tests
    # ========================================================================

    @patch("app.api.routes.features._get_flags_by_environment")
    @patch("app.api.routes.features.FeatureFlagService")
    def test_get_stats_success(
        self,
        mock_service_class: MagicMock,
        mock_get_flags_by_env: MagicMock,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test getting feature flag statistics."""
        mock_service = MagicMock()
        mock_service.get_stats = AsyncMock(
            return_value={
                "total_flags": 10,
                "enabled_flags": 7,
                "disabled_flags": 3,
                "percentage_rollout_flags": 2,
                "variant_flags": 1,
                "recent_evaluations": 1500,
                "unique_users": 250,
            }
        )
        mock_service_class.return_value = mock_service

        mock_get_flags_by_env.return_value = {
            "development": {"total": 10, "enabled": [], "disabled": []},
            "staging": {"total": 8, "enabled": [], "disabled": []},
            "production": {"total": 5, "enabled": [], "disabled": []},
        }

        response = client.get("/api/features/stats", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["total_flags"] == 10
        assert data["enabled_flags"] == 7
        assert data["disabled_flags"] == 3
        assert "flags_by_environment" in data
