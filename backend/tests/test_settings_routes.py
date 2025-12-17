"""Comprehensive tests for settings API routes."""
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.settings import ApplicationSettings


class TestGetSettingsEndpoint:
    """Tests for GET /api/settings endpoint."""

    def test_get_settings_creates_defaults_when_none_exist(
        self, client: TestClient, db: Session
    ):
        """Test that getting settings creates defaults when none exist."""
        # Verify no settings exist
        assert db.query(ApplicationSettings).first() is None

        response = client.get("/api/settings")

        assert response.status_code == 200
        data = response.json()

        # Verify default values
        assert data["scheduling_algorithm"] == "greedy"
        assert data["work_hours_per_week"] == 80
        assert data["max_consecutive_days"] == 6
        assert data["min_days_off_per_week"] == 1
        assert data["pgy1_supervision_ratio"] == "1:2"
        assert data["pgy2_supervision_ratio"] == "1:4"
        assert data["pgy3_supervision_ratio"] == "1:4"
        assert data["enable_weekend_scheduling"] is True
        assert data["enable_holiday_scheduling"] is False
        assert data["default_block_duration_hours"] == 4

        # Verify settings were created in database
        settings = db.query(ApplicationSettings).first()
        assert settings is not None

    def test_get_settings_returns_existing_settings(
        self, client: TestClient, db: Session
    ):
        """Test getting existing settings from database."""
        # Create custom settings
        settings = ApplicationSettings(
            scheduling_algorithm="cp_sat",
            work_hours_per_week=70,
            max_consecutive_days=5,
            min_days_off_per_week=2,
            enable_weekend_scheduling=False,
        )
        db.add(settings)
        db.commit()

        response = client.get("/api/settings")

        assert response.status_code == 200
        data = response.json()

        assert data["scheduling_algorithm"] == "cp_sat"
        assert data["work_hours_per_week"] == 70
        assert data["max_consecutive_days"] == 5
        assert data["min_days_off_per_week"] == 2
        assert data["enable_weekend_scheduling"] is False

    def test_get_settings_response_structure(self, client: TestClient, db: Session):
        """Test that response contains all required fields."""
        response = client.get("/api/settings")

        assert response.status_code == 200
        data = response.json()

        # Verify all fields are present
        required_fields = [
            "scheduling_algorithm",
            "work_hours_per_week",
            "max_consecutive_days",
            "min_days_off_per_week",
            "pgy1_supervision_ratio",
            "pgy2_supervision_ratio",
            "pgy3_supervision_ratio",
            "enable_weekend_scheduling",
            "enable_holiday_scheduling",
            "default_block_duration_hours",
        ]

        for field in required_fields:
            assert field in data, f"Field {field} missing from response"


class TestUpdateSettingsEndpoint:
    """Tests for POST /api/settings endpoint (full update)."""

    def test_update_all_settings_success(self, client: TestClient, db: Session):
        """Test successfully updating all settings."""
        update_data = {
            "scheduling_algorithm": "min_conflicts",
            "work_hours_per_week": 75,
            "max_consecutive_days": 5,
            "min_days_off_per_week": 2,
            "pgy1_supervision_ratio": "1:1",
            "pgy2_supervision_ratio": "1:3",
            "pgy3_supervision_ratio": "1:5",
            "enable_weekend_scheduling": False,
            "enable_holiday_scheduling": True,
            "default_block_duration_hours": 6,
        }

        response = client.post("/api/settings", json=update_data)

        assert response.status_code == 200
        data = response.json()

        # Verify all fields were updated
        for key, value in update_data.items():
            assert data[key] == value

        # Verify in database
        settings = db.query(ApplicationSettings).first()
        assert settings.scheduling_algorithm == "min_conflicts"
        assert settings.work_hours_per_week == 75

    def test_update_settings_invalid_algorithm(self, client: TestClient, db: Session):
        """Test validation for invalid scheduling algorithm."""
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "invalid_algorithm",
                "work_hours_per_week": 80,
                "max_consecutive_days": 6,
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )

        # Should fail at database constraint level (500) or validation level (422)
        assert response.status_code in [422, 500]

    def test_update_settings_work_hours_below_minimum(
        self, client: TestClient, db: Session
    ):
        """Test validation for work_hours_per_week below minimum (40)."""
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 30,  # Below minimum
                "max_consecutive_days": 6,
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )

        assert response.status_code == 422

    def test_update_settings_work_hours_above_maximum(
        self, client: TestClient, db: Session
    ):
        """Test validation for work_hours_per_week above maximum (100)."""
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 120,  # Above maximum
                "max_consecutive_days": 6,
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )

        assert response.status_code == 422

    def test_update_settings_work_hours_at_boundaries(
        self, client: TestClient, db: Session
    ):
        """Test work_hours_per_week at boundary values (40 and 100)."""
        # Test minimum boundary (40)
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 40,
                "max_consecutive_days": 6,
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )
        assert response.status_code == 200
        assert response.json()["work_hours_per_week"] == 40

        # Test maximum boundary (100)
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 100,
                "max_consecutive_days": 6,
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )
        assert response.status_code == 200
        assert response.json()["work_hours_per_week"] == 100

    def test_update_settings_max_consecutive_days_invalid(
        self, client: TestClient, db: Session
    ):
        """Test validation for max_consecutive_days outside valid range (1-7)."""
        # Test below minimum
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 80,
                "max_consecutive_days": 0,  # Below minimum
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )
        assert response.status_code == 422

        # Test above maximum
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 80,
                "max_consecutive_days": 8,  # Above maximum
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )
        assert response.status_code == 422

    def test_update_settings_min_days_off_invalid(
        self, client: TestClient, db: Session
    ):
        """Test validation for min_days_off_per_week outside valid range (1-3)."""
        # Test below minimum
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 80,
                "max_consecutive_days": 6,
                "min_days_off_per_week": 0,  # Below minimum
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )
        assert response.status_code == 422

        # Test above maximum
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 80,
                "max_consecutive_days": 6,
                "min_days_off_per_week": 4,  # Above maximum
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )
        assert response.status_code == 422

    def test_update_settings_block_duration_invalid(
        self, client: TestClient, db: Session
    ):
        """Test validation for default_block_duration_hours outside valid range (1-12)."""
        # Test below minimum
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 80,
                "max_consecutive_days": 6,
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 0,  # Below minimum
            },
        )
        assert response.status_code == 422

        # Test above maximum
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 80,
                "max_consecutive_days": 6,
                "min_days_off_per_week": 1,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 13,  # Above maximum
            },
        )
        assert response.status_code == 422

    def test_update_settings_updates_timestamp(self, client: TestClient, db: Session):
        """Test that updated_at timestamp is updated on settings change."""
        # Create initial settings
        client.get("/api/settings")
        initial_settings = db.query(ApplicationSettings).first()
        initial_updated_at = initial_settings.updated_at

        # Wait a moment and update
        import time
        time.sleep(0.1)

        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "cp_sat",
                "work_hours_per_week": 75,
                "max_consecutive_days": 5,
                "min_days_off_per_week": 2,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )

        assert response.status_code == 200

        # Verify timestamp was updated
        updated_settings = db.query(ApplicationSettings).first()
        assert updated_settings.updated_at > initial_updated_at


class TestPatchSettingsEndpoint:
    """Tests for PATCH /api/settings endpoint (partial update)."""

    def test_patch_single_field(self, client: TestClient, db: Session):
        """Test patching a single field."""
        # Create initial settings
        client.get("/api/settings")

        response = client.patch(
            "/api/settings",
            json={"scheduling_algorithm": "cp_sat"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["scheduling_algorithm"] == "cp_sat"
        # Other fields should remain at defaults
        assert data["work_hours_per_week"] == 80
        assert data["max_consecutive_days"] == 6

    def test_patch_multiple_fields(self, client: TestClient, db: Session):
        """Test patching multiple fields at once."""
        # Create initial settings
        client.get("/api/settings")

        response = client.patch(
            "/api/settings",
            json={
                "work_hours_per_week": 70,
                "max_consecutive_days": 5,
                "enable_weekend_scheduling": False,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["work_hours_per_week"] == 70
        assert data["max_consecutive_days"] == 5
        assert data["enable_weekend_scheduling"] is False
        # Unchanged fields
        assert data["scheduling_algorithm"] == "greedy"
        assert data["min_days_off_per_week"] == 1

    def test_patch_empty_data_returns_unchanged(self, client: TestClient, db: Session):
        """Test that patching with empty data returns settings unchanged."""
        # Create initial settings
        response = client.get("/api/settings")
        initial_data = response.json()

        # Patch with empty object
        response = client.patch("/api/settings", json={})

        assert response.status_code == 200
        data = response.json()

        # Should be identical to initial
        assert data == initial_data

    def test_patch_boolean_fields(self, client: TestClient, db: Session):
        """Test patching boolean fields."""
        # Create initial settings
        client.get("/api/settings")

        response = client.patch(
            "/api/settings",
            json={
                "enable_weekend_scheduling": False,
                "enable_holiday_scheduling": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["enable_weekend_scheduling"] is False
        assert data["enable_holiday_scheduling"] is True

    def test_patch_supervision_ratios(self, client: TestClient, db: Session):
        """Test patching supervision ratio fields."""
        response = client.patch(
            "/api/settings",
            json={
                "pgy1_supervision_ratio": "1:1",
                "pgy2_supervision_ratio": "1:3",
                "pgy3_supervision_ratio": "1:6",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["pgy1_supervision_ratio"] == "1:1"
        assert data["pgy2_supervision_ratio"] == "1:3"
        assert data["pgy3_supervision_ratio"] == "1:6"

    def test_patch_with_invalid_value(self, client: TestClient, db: Session):
        """Test that patching with invalid value fails validation."""
        response = client.patch(
            "/api/settings",
            json={"work_hours_per_week": 150},  # Above maximum
        )

        assert response.status_code == 422

    def test_patch_preserves_other_fields(self, client: TestClient, db: Session):
        """Test that patching preserves all non-specified fields."""
        # Create settings with specific values
        client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "min_conflicts",
                "work_hours_per_week": 85,
                "max_consecutive_days": 5,
                "min_days_off_per_week": 2,
                "pgy1_supervision_ratio": "1:1",
                "pgy2_supervision_ratio": "1:3",
                "pgy3_supervision_ratio": "1:5",
                "enable_weekend_scheduling": False,
                "enable_holiday_scheduling": True,
                "default_block_duration_hours": 6,
            },
        )

        # Patch only one field
        response = client.patch(
            "/api/settings",
            json={"work_hours_per_week": 75},
        )

        assert response.status_code == 200
        data = response.json()

        # Updated field
        assert data["work_hours_per_week"] == 75

        # All other fields should be preserved
        assert data["scheduling_algorithm"] == "min_conflicts"
        assert data["max_consecutive_days"] == 5
        assert data["min_days_off_per_week"] == 2
        assert data["pgy1_supervision_ratio"] == "1:1"
        assert data["pgy2_supervision_ratio"] == "1:3"
        assert data["pgy3_supervision_ratio"] == "1:5"
        assert data["enable_weekend_scheduling"] is False
        assert data["enable_holiday_scheduling"] is True
        assert data["default_block_duration_hours"] == 6

    def test_patch_updates_timestamp(self, client: TestClient, db: Session):
        """Test that patching updates the updated_at timestamp."""
        # Create initial settings
        client.get("/api/settings")
        initial_settings = db.query(ApplicationSettings).first()
        initial_updated_at = initial_settings.updated_at

        # Wait a moment
        import time
        time.sleep(0.1)

        # Patch a field
        response = client.patch(
            "/api/settings",
            json={"work_hours_per_week": 75},
        )

        assert response.status_code == 200

        # Verify timestamp was updated
        updated_settings = db.query(ApplicationSettings).first()
        assert updated_settings.updated_at > initial_updated_at


class TestResetSettingsEndpoint:
    """Tests for DELETE /api/settings endpoint (reset to defaults)."""

    def test_reset_settings_to_defaults(self, client: TestClient, db: Session):
        """Test resetting settings to default values."""
        # Create custom settings
        client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "cp_sat",
                "work_hours_per_week": 70,
                "max_consecutive_days": 5,
                "min_days_off_per_week": 2,
                "pgy1_supervision_ratio": "1:1",
                "pgy2_supervision_ratio": "1:3",
                "pgy3_supervision_ratio": "1:5",
                "enable_weekend_scheduling": False,
                "enable_holiday_scheduling": True,
                "default_block_duration_hours": 8,
            },
        )

        # Reset to defaults
        response = client.delete("/api/settings")

        assert response.status_code == 204

        # Verify settings were reset
        response = client.get("/api/settings")
        data = response.json()

        assert data["scheduling_algorithm"] == "greedy"
        assert data["work_hours_per_week"] == 80
        assert data["max_consecutive_days"] == 6
        assert data["min_days_off_per_week"] == 1
        assert data["pgy1_supervision_ratio"] == "1:2"
        assert data["pgy2_supervision_ratio"] == "1:4"
        assert data["pgy3_supervision_ratio"] == "1:4"
        assert data["enable_weekend_scheduling"] is True
        assert data["enable_holiday_scheduling"] is False
        assert data["default_block_duration_hours"] == 4

    def test_reset_settings_preserves_record(self, client: TestClient, db: Session):
        """Test that reset updates the existing record rather than deleting it."""
        # Create settings
        client.get("/api/settings")

        # Get the settings ID
        settings_before = db.query(ApplicationSettings).first()
        settings_id = settings_before.id

        # Reset
        response = client.delete("/api/settings")
        assert response.status_code == 204

        # Verify the same record still exists
        settings_after = db.query(ApplicationSettings).first()
        assert settings_after is not None
        assert settings_after.id == settings_id

    def test_reset_updates_timestamp(self, client: TestClient, db: Session):
        """Test that reset updates the updated_at timestamp."""
        # Create settings
        client.get("/api/settings")
        initial_settings = db.query(ApplicationSettings).first()
        initial_updated_at = initial_settings.updated_at

        # Wait a moment
        import time
        time.sleep(0.1)

        # Reset
        response = client.delete("/api/settings")
        assert response.status_code == 204

        # Verify timestamp was updated
        updated_settings = db.query(ApplicationSettings).first()
        assert updated_settings.updated_at > initial_updated_at


class TestSettingsValidation:
    """Tests for settings validation and edge cases."""

    def test_all_valid_scheduling_algorithms(self, client: TestClient, db: Session):
        """Test all valid scheduling algorithm values."""
        valid_algorithms = ["greedy", "min_conflicts", "cp_sat", "pulp", "hybrid"]

        for algorithm in valid_algorithms:
            response = client.patch(
                "/api/settings",
                json={"scheduling_algorithm": algorithm},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["scheduling_algorithm"] == algorithm

    def test_settings_boundary_values(self, client: TestClient, db: Session):
        """Test all boundary values for integer constraints."""
        # Test minimum boundary values
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 40,  # Minimum
                "max_consecutive_days": 1,  # Minimum
                "min_days_off_per_week": 1,  # Minimum
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 1,  # Minimum
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["work_hours_per_week"] == 40
        assert data["max_consecutive_days"] == 1
        assert data["min_days_off_per_week"] == 1
        assert data["default_block_duration_hours"] == 1

        # Test maximum boundary values
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 100,  # Maximum
                "max_consecutive_days": 7,  # Maximum
                "min_days_off_per_week": 3,  # Maximum
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 12,  # Maximum
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["work_hours_per_week"] == 100
        assert data["max_consecutive_days"] == 7
        assert data["min_days_off_per_week"] == 3
        assert data["default_block_duration_hours"] == 12

    def test_settings_missing_required_field(self, client: TestClient, db: Session):
        """Test that POST with missing required field fails."""
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "greedy",
                "work_hours_per_week": 80,
                # Missing other required fields
            },
        )

        assert response.status_code == 422

    def test_settings_extra_fields_ignored(self, client: TestClient, db: Session):
        """Test that extra fields in request are ignored."""
        response = client.patch(
            "/api/settings",
            json={
                "work_hours_per_week": 75,
                "extra_field": "should be ignored",
                "another_extra": 123,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["work_hours_per_week"] == 75
        assert "extra_field" not in data
        assert "another_extra" not in data


class TestSettingsIntegration:
    """Integration tests for settings workflow."""

    def test_full_settings_lifecycle(self, client: TestClient, db: Session):
        """Test complete settings lifecycle: create, update, patch, reset."""
        # 1. Get initial defaults (creates settings)
        response = client.get("/api/settings")
        assert response.status_code == 200
        initial_data = response.json()
        assert initial_data["scheduling_algorithm"] == "greedy"

        # 2. Full update
        response = client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "cp_sat",
                "work_hours_per_week": 75,
                "max_consecutive_days": 5,
                "min_days_off_per_week": 2,
                "pgy1_supervision_ratio": "1:1",
                "pgy2_supervision_ratio": "1:3",
                "pgy3_supervision_ratio": "1:5",
                "enable_weekend_scheduling": False,
                "enable_holiday_scheduling": True,
                "default_block_duration_hours": 6,
            },
        )
        assert response.status_code == 200
        assert response.json()["scheduling_algorithm"] == "cp_sat"

        # 3. Partial update
        response = client.patch(
            "/api/settings",
            json={"work_hours_per_week": 80},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["work_hours_per_week"] == 80
        assert data["scheduling_algorithm"] == "cp_sat"  # Unchanged

        # 4. Reset to defaults
        response = client.delete("/api/settings")
        assert response.status_code == 204

        # 5. Verify reset worked
        response = client.get("/api/settings")
        assert response.status_code == 200
        reset_data = response.json()
        assert reset_data["scheduling_algorithm"] == "greedy"
        assert reset_data["work_hours_per_week"] == 80

    def test_multiple_updates_same_field(self, client: TestClient, db: Session):
        """Test updating the same field multiple times."""
        # Initial value
        client.get("/api/settings")

        # Update 1
        response = client.patch("/api/settings", json={"work_hours_per_week": 70})
        assert response.status_code == 200
        assert response.json()["work_hours_per_week"] == 70

        # Update 2
        response = client.patch("/api/settings", json={"work_hours_per_week": 85})
        assert response.status_code == 200
        assert response.json()["work_hours_per_week"] == 85

        # Update 3
        response = client.patch("/api/settings", json={"work_hours_per_week": 60})
        assert response.status_code == 200
        assert response.json()["work_hours_per_week"] == 60

        # Verify final value persists
        response = client.get("/api/settings")
        assert response.json()["work_hours_per_week"] == 60

    def test_settings_singleton_behavior(self, client: TestClient, db: Session):
        """Test that only one settings record exists in database."""
        # Create settings multiple times
        client.get("/api/settings")
        client.post(
            "/api/settings",
            json={
                "scheduling_algorithm": "cp_sat",
                "work_hours_per_week": 75,
                "max_consecutive_days": 5,
                "min_days_off_per_week": 2,
                "pgy1_supervision_ratio": "1:2",
                "pgy2_supervision_ratio": "1:4",
                "pgy3_supervision_ratio": "1:4",
                "enable_weekend_scheduling": True,
                "enable_holiday_scheduling": False,
                "default_block_duration_hours": 4,
            },
        )
        client.patch("/api/settings", json={"work_hours_per_week": 80})

        # Verify only one record exists
        settings_count = db.query(ApplicationSettings).count()
        assert settings_count == 1
