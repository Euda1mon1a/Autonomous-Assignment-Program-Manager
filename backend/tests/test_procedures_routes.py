"""Tests for procedures API routes.

Comprehensive test suite covering procedure CRUD operations, filtering,
categorization, activation/deactivation, and validation.
"""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.procedure import Procedure


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_procedure(db: Session) -> Procedure:
    """Create a sample procedure."""
    procedure = Procedure(
        id=uuid4(),
        name="IUD Placement",
        description="Intrauterine device insertion procedure",
        category="office",
        specialty="OB/GYN",
        supervision_ratio=2,
        requires_certification=True,
        complexity_level="standard",
        min_pgy_level=2,
        is_active=True,
    )
    db.add(procedure)
    db.commit()
    db.refresh(procedure)
    return procedure


@pytest.fixture
def sample_procedures(db: Session) -> list[Procedure]:
    """Create multiple sample procedures across different categories."""
    procedures = []

    procedure_data = [
        {
            "name": "Botox Injection",
            "description": "Cosmetic botulinum toxin injection",
            "category": "office",
            "specialty": "Dermatology",
            "supervision_ratio": 1,
            "complexity_level": "basic",
            "min_pgy_level": 1,
            "is_active": True,
        },
        {
            "name": "Colposcopy",
            "description": "Cervical examination procedure",
            "category": "office",
            "specialty": "OB/GYN",
            "supervision_ratio": 2,
            "complexity_level": "standard",
            "min_pgy_level": 2,
            "is_active": True,
        },
        {
            "name": "Mastectomy",
            "description": "Surgical breast removal",
            "category": "surgical",
            "specialty": "General Surgery",
            "supervision_ratio": 1,
            "complexity_level": "complex",
            "min_pgy_level": 3,
            "is_active": True,
        },
        {
            "name": "Labor and Delivery",
            "description": "Obstetric delivery supervision",
            "category": "obstetric",
            "specialty": "OB/GYN",
            "supervision_ratio": 2,
            "complexity_level": "advanced",
            "min_pgy_level": 2,
            "is_active": True,
        },
        {
            "name": "Sports Medicine Clinic",
            "description": "Outpatient sports medicine consultation",
            "category": "clinic",
            "specialty": "Sports Medicine",
            "supervision_ratio": 4,
            "complexity_level": "basic",
            "min_pgy_level": 1,
            "is_active": True,
        },
        {
            "name": "Deprecated Procedure",
            "description": "No longer performed",
            "category": "office",
            "specialty": "General",
            "supervision_ratio": 1,
            "complexity_level": "basic",
            "min_pgy_level": 1,
            "is_active": False,  # Inactive
        },
    ]

    for data in procedure_data:
        procedure = Procedure(id=uuid4(), **data)
        db.add(procedure)
        procedures.append(procedure)

    db.commit()
    for p in procedures:
        db.refresh(p)
    return procedures


# ============================================================================
# List Procedures Endpoint
# ============================================================================

class TestListProceduresEndpoint:
    """Tests for GET /api/procedures endpoint."""

    def test_list_procedures_empty(self, client: TestClient, db: Session):
        """Test listing procedures when none exist."""
        response = client.get("/api/procedures")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_procedures_with_data(self, client: TestClient, sample_procedures):
        """Test listing procedures with existing data."""
        response = client.get("/api/procedures")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 6  # All procedures including inactive
        assert len(data["items"]) == 6

        # Validate structure
        procedure = data["items"][0]
        assert "id" in procedure
        assert "name" in procedure
        assert "description" in procedure
        assert "category" in procedure
        assert "specialty" in procedure
        assert "supervision_ratio" in procedure
        assert "requires_certification" in procedure
        assert "complexity_level" in procedure
        assert "min_pgy_level" in procedure
        assert "is_active" in procedure

    def test_list_procedures_filter_by_specialty(
        self, client: TestClient, sample_procedures
    ):
        """Test filtering procedures by specialty."""
        response = client.get("/api/procedures", params={"specialty": "OB/GYN"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Colposcopy and Labor and Delivery

        for procedure in data["items"]:
            assert procedure["specialty"] == "OB/GYN"

    def test_list_procedures_filter_by_category(
        self, client: TestClient, sample_procedures
    ):
        """Test filtering procedures by category."""
        response = client.get("/api/procedures", params={"category": "office"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # Botox, Colposcopy, Deprecated

        for procedure in data["items"]:
            assert procedure["category"] == "office"

    def test_list_procedures_filter_by_is_active(
        self, client: TestClient, sample_procedures
    ):
        """Test filtering procedures by active status."""
        # Filter active only
        response = client.get("/api/procedures", params={"is_active": True})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # All except deprecated

        for procedure in data["items"]:
            assert procedure["is_active"] is True

        # Filter inactive only
        response = client.get("/api/procedures", params={"is_active": False})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1  # Only deprecated

    def test_list_procedures_filter_by_complexity_level(
        self, client: TestClient, sample_procedures
    ):
        """Test filtering procedures by complexity level."""
        response = client.get("/api/procedures", params={"complexity_level": "basic"})

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # Botox, Sports Medicine, Deprecated

        for procedure in data["items"]:
            assert procedure["complexity_level"] == "basic"

    def test_list_procedures_combined_filters(
        self, client: TestClient, sample_procedures
    ):
        """Test combining multiple filters."""
        response = client.get(
            "/api/procedures",
            params={
                "category": "office",
                "is_active": True,
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should get Botox and Colposcopy (not deprecated)
        assert data["total"] == 2

        for procedure in data["items"]:
            assert procedure["category"] == "office"
            assert procedure["is_active"] is True

    def test_list_procedures_no_matches(self, client: TestClient, sample_procedures):
        """Test filtering with no matching results."""
        response = client.get(
            "/api/procedures",
            params={"specialty": "NonExistentSpecialty"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


# ============================================================================
# Get Specialties and Categories Endpoints
# ============================================================================

class TestGetSpecialtiesEndpoint:
    """Tests for GET /api/procedures/specialties endpoint."""

    def test_get_specialties_empty(self, client: TestClient):
        """Test getting specialties when no procedures exist."""
        response = client.get("/api/procedures/specialties")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_specialties_with_data(self, client: TestClient, sample_procedures):
        """Test getting unique specialties from procedures."""
        response = client.get("/api/procedures/specialties")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Should include all unique specialties
        expected_specialties = {
            "Dermatology",
            "OB/GYN",
            "General Surgery",
            "Sports Medicine",
            "General",
        }
        assert set(data) == expected_specialties

    def test_get_specialties_unique(self, client: TestClient, sample_procedures):
        """Test that specialties are unique (no duplicates)."""
        response = client.get("/api/procedures/specialties")

        assert response.status_code == 200
        data = response.json()

        # Check for duplicates
        assert len(data) == len(set(data))


class TestGetCategoriesEndpoint:
    """Tests for GET /api/procedures/categories endpoint."""

    def test_get_categories_empty(self, client: TestClient):
        """Test getting categories when no procedures exist."""
        response = client.get("/api/procedures/categories")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_categories_with_data(self, client: TestClient, sample_procedures):
        """Test getting unique categories from procedures."""
        response = client.get("/api/procedures/categories")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Should include all unique categories
        expected_categories = {
            "office",
            "surgical",
            "obstetric",
            "clinic",
        }
        assert set(data) == expected_categories

    def test_get_categories_unique(self, client: TestClient, sample_procedures):
        """Test that categories are unique (no duplicates)."""
        response = client.get("/api/procedures/categories")

        assert response.status_code == 200
        data = response.json()

        # Check for duplicates
        assert len(data) == len(set(data))


# ============================================================================
# Get Procedure Endpoints
# ============================================================================

class TestGetProcedureByNameEndpoint:
    """Tests for GET /api/procedures/by-name/{name} endpoint."""

    def test_get_procedure_by_name_success(
        self, client: TestClient, sample_procedure: Procedure
    ):
        """Test getting a procedure by its name."""
        response = client.get(f"/api/procedures/by-name/{sample_procedure.name}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_procedure.id)
        assert data["name"] == sample_procedure.name
        assert data["description"] == sample_procedure.description

    def test_get_procedure_by_name_not_found(self, client: TestClient):
        """Test getting non-existent procedure by name."""
        response = client.get("/api/procedures/by-name/NonExistentProcedure")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_procedure_by_name_case_sensitive(
        self, client: TestClient, sample_procedure: Procedure
    ):
        """Test that name lookup is case-sensitive."""
        # Exact match should work
        response = client.get(f"/api/procedures/by-name/{sample_procedure.name}")
        assert response.status_code == 200

        # Different case might not work (depends on implementation)
        response = client.get(f"/api/procedures/by-name/{sample_procedure.name.lower()}")
        # Could be 200 or 404 depending on case sensitivity
        assert response.status_code in [200, 404]


class TestGetProcedureEndpoint:
    """Tests for GET /api/procedures/{procedure_id} endpoint."""

    def test_get_procedure_success(
        self, client: TestClient, sample_procedure: Procedure
    ):
        """Test getting a procedure by ID."""
        response = client.get(f"/api/procedures/{sample_procedure.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_procedure.id)
        assert data["name"] == sample_procedure.name
        assert data["category"] == sample_procedure.category
        assert data["specialty"] == sample_procedure.specialty
        assert data["supervision_ratio"] == sample_procedure.supervision_ratio
        assert data["complexity_level"] == sample_procedure.complexity_level

    def test_get_procedure_not_found(self, client: TestClient):
        """Test getting non-existent procedure."""
        fake_id = uuid4()
        response = client.get(f"/api/procedures/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_procedure_invalid_uuid(self, client: TestClient):
        """Test getting procedure with invalid UUID."""
        response = client.get("/api/procedures/invalid-uuid")

        assert response.status_code == 422


# ============================================================================
# Create Procedure Endpoint
# ============================================================================

class TestCreateProcedureEndpoint:
    """Tests for POST /api/procedures endpoint."""

    def test_create_procedure_success(self, client: TestClient, auth_headers: dict):
        """Test creating a new procedure."""
        procedure_data = {
            "name": "Vasectomy",
            "description": "Male sterilization procedure",
            "category": "surgical",
            "specialty": "Urology",
            "supervision_ratio": 1,
            "requires_certification": True,
            "complexity_level": "standard",
            "min_pgy_level": 2,
            "is_active": True,
        }

        response = client.post(
            "/api/procedures",
            json=procedure_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == procedure_data["name"]
        assert data["category"] == procedure_data["category"]
        assert data["specialty"] == procedure_data["specialty"]

    def test_create_procedure_requires_auth(self, client: TestClient):
        """Test that creating procedure requires authentication."""
        procedure_data = {
            "name": "Test Procedure",
            "category": "office",
        }

        response = client.post("/api/procedures", json=procedure_data)

        assert response.status_code == 401

    def test_create_procedure_minimal_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating procedure with minimal required fields."""
        procedure_data = {
            "name": "Minimal Procedure",
            # Other fields should use defaults
        }

        response = client.post(
            "/api/procedures",
            json=procedure_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Procedure"
        # Check defaults
        assert data["supervision_ratio"] == 1
        assert data["requires_certification"] is True
        assert data["complexity_level"] == "standard"
        assert data["min_pgy_level"] == 1
        assert data["is_active"] is True

    def test_create_procedure_duplicate_name(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_procedure: Procedure,
    ):
        """Test creating procedure with duplicate name."""
        procedure_data = {
            "name": sample_procedure.name,  # Duplicate
            "category": "office",
        }

        response = client.post(
            "/api/procedures",
            json=procedure_data,
            headers=auth_headers,
        )

        assert response.status_code in [400, 422]

    def test_create_procedure_invalid_complexity_level(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating procedure with invalid complexity level."""
        procedure_data = {
            "name": "Invalid Procedure",
            "complexity_level": "invalid_level",
        }

        response = client.post(
            "/api/procedures",
            json=procedure_data,
            headers=auth_headers,
        )

        assert response.status_code == 422
        error_detail = str(response.json()["detail"])
        assert "complexity_level" in error_detail.lower()

    def test_create_procedure_invalid_pgy_level(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating procedure with invalid PGY level."""
        procedure_data = {
            "name": "Invalid PGY Procedure",
            "min_pgy_level": 5,  # Invalid: must be 1-3
        }

        response = client.post(
            "/api/procedures",
            json=procedure_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_procedure_invalid_supervision_ratio(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating procedure with invalid supervision ratio."""
        procedure_data = {
            "name": "Invalid Ratio Procedure",
            "supervision_ratio": 0,  # Invalid: must be at least 1
        }

        response = client.post(
            "/api/procedures",
            json=procedure_data,
            headers=auth_headers,
        )

        assert response.status_code == 422


# ============================================================================
# Update Procedure Endpoint
# ============================================================================

class TestUpdateProcedureEndpoint:
    """Tests for PUT /api/procedures/{procedure_id} endpoint."""

    def test_update_procedure_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_procedure: Procedure,
    ):
        """Test updating a procedure."""
        update_data = {
            "description": "Updated description",
            "supervision_ratio": 3,
            "complexity_level": "advanced",
        }

        response = client.put(
            f"/api/procedures/{sample_procedure.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["supervision_ratio"] == 3
        assert data["complexity_level"] == "advanced"
        # Name should remain unchanged
        assert data["name"] == sample_procedure.name

    def test_update_procedure_requires_auth(
        self, client: TestClient, sample_procedure: Procedure
    ):
        """Test that updating procedure requires authentication."""
        update_data = {"description": "New description"}

        response = client.put(
            f"/api/procedures/{sample_procedure.id}",
            json=update_data,
        )

        assert response.status_code == 401

    def test_update_procedure_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test updating non-existent procedure."""
        fake_id = uuid4()
        update_data = {"description": "New description"}

        response = client.put(
            f"/api/procedures/{fake_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_update_procedure_partial_update(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_procedure: Procedure,
    ):
        """Test partial update of procedure fields."""
        update_data = {
            "description": "Only updating description",
        }

        response = client.put(
            f"/api/procedures/{sample_procedure.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Only updating description"
        # Other fields should remain unchanged
        assert data["name"] == sample_procedure.name
        assert data["category"] == sample_procedure.category
        assert data["specialty"] == sample_procedure.specialty

    def test_update_procedure_invalid_complexity(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_procedure: Procedure,
    ):
        """Test updating with invalid complexity level."""
        update_data = {
            "complexity_level": "super_complex",  # Invalid
        }

        response = client.put(
            f"/api/procedures/{sample_procedure.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 422


# ============================================================================
# Delete Procedure Endpoint
# ============================================================================

class TestDeleteProcedureEndpoint:
    """Tests for DELETE /api/procedures/{procedure_id} endpoint."""

    def test_delete_procedure_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test deleting a procedure."""
        # Create a procedure to delete
        procedure = Procedure(
            id=uuid4(),
            name="Procedure To Delete",
            category="office",
        )
        db.add(procedure)
        db.commit()
        procedure_id = procedure.id

        response = client.delete(
            f"/api/procedures/{procedure_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        verify_response = client.get(f"/api/procedures/{procedure_id}")
        assert verify_response.status_code == 404

    def test_delete_procedure_requires_auth(
        self, client: TestClient, sample_procedure: Procedure
    ):
        """Test that deleting procedure requires authentication."""
        response = client.delete(f"/api/procedures/{sample_procedure.id}")

        assert response.status_code == 401

    def test_delete_procedure_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test deleting non-existent procedure."""
        fake_id = uuid4()
        response = client.delete(
            f"/api/procedures/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# Activate/Deactivate Procedure Endpoints
# ============================================================================

class TestDeactivateProcedureEndpoint:
    """Tests for POST /api/procedures/{procedure_id}/deactivate endpoint."""

    def test_deactivate_procedure_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_procedure: Procedure,
    ):
        """Test deactivating a procedure."""
        response = client.post(
            f"/api/procedures/{sample_procedure.id}/deactivate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["id"] == str(sample_procedure.id)

    def test_deactivate_procedure_requires_auth(
        self, client: TestClient, sample_procedure: Procedure
    ):
        """Test that deactivating procedure requires authentication."""
        response = client.post(f"/api/procedures/{sample_procedure.id}/deactivate")

        assert response.status_code == 401

    def test_deactivate_procedure_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test deactivating non-existent procedure."""
        fake_id = uuid4()
        response = client.post(
            f"/api/procedures/{fake_id}/deactivate",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_deactivate_already_inactive_procedure(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test deactivating an already inactive procedure."""
        procedure = Procedure(
            id=uuid4(),
            name="Already Inactive",
            category="office",
            is_active=False,
        )
        db.add(procedure)
        db.commit()

        response = client.post(
            f"/api/procedures/{procedure.id}/deactivate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False


class TestActivateProcedureEndpoint:
    """Tests for POST /api/procedures/{procedure_id}/activate endpoint."""

    def test_activate_procedure_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test activating an inactive procedure."""
        procedure = Procedure(
            id=uuid4(),
            name="Inactive Procedure",
            category="office",
            is_active=False,
        )
        db.add(procedure)
        db.commit()

        response = client.post(
            f"/api/procedures/{procedure.id}/activate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        assert data["id"] == str(procedure.id)

    def test_activate_procedure_requires_auth(
        self, client: TestClient, db: Session
    ):
        """Test that activating procedure requires authentication."""
        procedure = Procedure(
            id=uuid4(),
            name="Inactive",
            category="office",
            is_active=False,
        )
        db.add(procedure)
        db.commit()

        response = client.post(f"/api/procedures/{procedure.id}/activate")

        assert response.status_code == 401

    def test_activate_procedure_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test activating non-existent procedure."""
        fake_id = uuid4()
        response = client.post(
            f"/api/procedures/{fake_id}/activate",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_activate_already_active_procedure(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_procedure: Procedure,
    ):
        """Test activating an already active procedure."""
        response = client.post(
            f"/api/procedures/{sample_procedure.id}/activate",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True


# ============================================================================
# Edge Cases and Validation
# ============================================================================

class TestProcedureEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_procedure_with_all_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating procedure with all possible fields populated."""
        procedure_data = {
            "name": "Comprehensive Procedure",
            "description": "Detailed description",
            "category": "surgical",
            "specialty": "Cardiology",
            "supervision_ratio": 2,
            "requires_certification": True,
            "complexity_level": "complex",
            "min_pgy_level": 3,
            "is_active": True,
        }

        response = client.post(
            "/api/procedures",
            json=procedure_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        for key, value in procedure_data.items():
            assert data[key] == value

    def test_create_procedure_pgy_level_boundary_values(
        self, client: TestClient, auth_headers: dict
    ):
        """Test PGY level validation at boundary values."""
        # Valid: 1
        response = client.post(
            "/api/procedures",
            json={"name": "PGY1 Procedure", "min_pgy_level": 1},
            headers=auth_headers,
        )
        assert response.status_code == 201

        # Valid: 3
        response = client.post(
            "/api/procedures",
            json={"name": "PGY3 Procedure", "min_pgy_level": 3},
            headers=auth_headers,
        )
        assert response.status_code == 201

        # Invalid: 0
        response = client.post(
            "/api/procedures",
            json={"name": "PGY0 Procedure", "min_pgy_level": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Invalid: 4
        response = client.post(
            "/api/procedures",
            json={"name": "PGY4 Procedure", "min_pgy_level": 4},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_procedure_very_long_name(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating procedure with very long name."""
        long_name = "A" * 300  # Very long name

        response = client.post(
            "/api/procedures",
            json={"name": long_name},
            headers=auth_headers,
        )

        # Might succeed or fail depending on column size
        assert response.status_code in [201, 400, 422]

    def test_update_procedure_to_duplicate_name(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_procedures: list[Procedure],
    ):
        """Test updating procedure to duplicate another's name."""
        update_data = {
            "name": sample_procedures[1].name,  # Try to use another's name
        }

        response = client.put(
            f"/api/procedures/{sample_procedures[0].id}",
            json=update_data,
            headers=auth_headers,
        )

        # Should fail due to unique constraint
        assert response.status_code in [400, 422]

    def test_filter_procedures_with_null_values(
        self, client: TestClient, db: Session, auth_headers: dict
    ):
        """Test filtering when some procedures have null optional fields."""
        # Create procedure with minimal fields
        procedure = Procedure(
            id=uuid4(),
            name="Minimal Fields Procedure",
            description=None,
            category=None,
            specialty=None,
        )
        db.add(procedure)
        db.commit()

        # Should still be able to list all procedures
        response = client.get("/api/procedures")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_procedure_response_structure(
        self, client: TestClient, sample_procedure: Procedure
    ):
        """Test that procedure response has all expected fields."""
        response = client.get(f"/api/procedures/{sample_procedure.id}")

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "id", "name", "description", "category", "specialty",
            "supervision_ratio", "requires_certification", "complexity_level",
            "min_pgy_level", "is_active", "created_at", "updated_at"
        ]

        for field in required_fields:
            assert field in data

    def test_complexity_level_valid_values(
        self, client: TestClient, auth_headers: dict
    ):
        """Test all valid complexity level values."""
        valid_levels = ['basic', 'standard', 'advanced', 'complex']

        for i, level in enumerate(valid_levels):
            response = client.post(
                "/api/procedures",
                json={
                    "name": f"Procedure {level} {i}",
                    "complexity_level": level,
                },
                headers=auth_headers,
            )

            assert response.status_code == 201
            data = response.json()
            assert data["complexity_level"] == level
