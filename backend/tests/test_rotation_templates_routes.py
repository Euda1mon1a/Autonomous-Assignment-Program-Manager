"""Comprehensive tests for rotation template API routes."""

from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.rotation_template import RotationTemplate


class TestListRotationTemplates:
    """Tests for GET /api/rotation-templates endpoint."""

    def test_list_templates_empty(self, client: TestClient, db: Session):
        """Test listing templates when database is empty."""
        response = client.get("/api/rotation-templates")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_templates_single(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test listing templates with one template in database."""
        response = client.get("/api/rotation-templates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == sample_rotation_template.name
        assert (
            data["items"][0]["activity_type"] == sample_rotation_template.activity_type
        )

    def test_list_templates_multiple(self, client: TestClient, db: Session):
        """Test listing multiple templates."""
        templates_data = [
            {"name": "Clinic A", "activity_type": "clinic", "abbreviation": "CA"},
            {"name": "Inpatient B", "activity_type": "inpatient", "abbreviation": "IB"},
            {"name": "Procedure C", "activity_type": "procedure", "abbreviation": "PC"},
        ]

        for template_data in templates_data:
            template = RotationTemplate(id=uuid4(), **template_data)
            db.add(template)
        db.commit()

        response = client.get("/api/rotation-templates")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_templates_sorted_by_name(self, client: TestClient, db: Session):
        """Test that templates are sorted by name."""
        templates_data = [
            {"name": "Zebra Clinic", "activity_type": "clinic"},
            {"name": "Alpha Clinic", "activity_type": "clinic"},
            {"name": "Beta Clinic", "activity_type": "clinic"},
        ]

        for template_data in templates_data:
            template = RotationTemplate(id=uuid4(), **template_data)
            db.add(template)
        db.commit()

        response = client.get("/api/rotation-templates")

        assert response.status_code == 200
        data = response.json()
        names = [item["name"] for item in data["items"]]
        assert names == ["Alpha Clinic", "Beta Clinic", "Zebra Clinic"]

    def test_list_templates_filter_by_activity_type_clinic(
        self, client: TestClient, db: Session
    ):
        """Test filtering templates by activity_type='clinic'."""
        templates_data = [
            {"name": "Clinic A", "activity_type": "clinic"},
            {"name": "Inpatient B", "activity_type": "inpatient"},
            {"name": "Clinic C", "activity_type": "clinic"},
            {"name": "Procedure D", "activity_type": "procedure"},
        ]

        for template_data in templates_data:
            template = RotationTemplate(id=uuid4(), **template_data)
            db.add(template)
        db.commit()

        response = client.get("/api/rotation-templates?activity_type=clinic")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["activity_type"] == "clinic" for item in data["items"])

    def test_list_templates_filter_by_activity_type_inpatient(
        self, client: TestClient, db: Session
    ):
        """Test filtering templates by activity_type='inpatient'."""
        templates_data = [
            {"name": "Clinic A", "activity_type": "clinic"},
            {"name": "Inpatient B", "activity_type": "inpatient"},
            {"name": "Inpatient C", "activity_type": "inpatient"},
        ]

        for template_data in templates_data:
            template = RotationTemplate(id=uuid4(), **template_data)
            db.add(template)
        db.commit()

        response = client.get("/api/rotation-templates?activity_type=inpatient")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["activity_type"] == "inpatient" for item in data["items"])

    def test_list_templates_filter_by_activity_type_no_results(
        self, client: TestClient, db: Session
    ):
        """Test filtering by activity_type with no matching results."""
        template = RotationTemplate(
            id=uuid4(),
            name="Clinic A",
            activity_type="clinic",
        )
        db.add(template)
        db.commit()

        response = client.get("/api/rotation-templates?activity_type=conference")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_templates_filter_case_sensitive(
        self, client: TestClient, db: Session
    ):
        """Test that activity_type filter is case-sensitive."""
        template = RotationTemplate(
            id=uuid4(),
            name="Clinic A",
            activity_type="clinic",
        )
        db.add(template)
        db.commit()

        response = client.get("/api/rotation-templates?activity_type=CLINIC")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_templates_includes_all_fields(self, client: TestClient, db: Session):
        """Test that response includes all template fields."""
        template = RotationTemplate(
            id=uuid4(),
            name="Sports Medicine Clinic",
            activity_type="clinic",
            abbreviation="SM",
            clinic_location="Building A",
            max_residents=4,
            requires_specialty="Sports Medicine",
            requires_procedure_credential=True,
            supervision_required=True,
            max_supervision_ratio=3,
        )
        db.add(template)
        db.commit()

        response = client.get("/api/rotation-templates")

        assert response.status_code == 200
        data = response.json()
        item = data["items"][0]
        assert item["name"] == "Sports Medicine Clinic"
        assert item["activity_type"] == "clinic"
        assert item["abbreviation"] == "SM"
        assert item["clinic_location"] == "Building A"
        assert item["max_residents"] == 4
        assert item["requires_specialty"] == "Sports Medicine"
        assert item["requires_procedure_credential"] is True
        assert item["supervision_required"] is True
        assert item["max_supervision_ratio"] == 3
        assert "id" in item
        assert "created_at" in item


class TestGetRotationTemplate:
    """Tests for GET /api/rotation-templates/{template_id} endpoint."""

    def test_get_template_success(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test successfully retrieving a template by ID."""
        response = client.get(f"/api/rotation-templates/{sample_rotation_template.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_rotation_template.id)
        assert data["name"] == sample_rotation_template.name
        assert data["activity_type"] == sample_rotation_template.activity_type

    def test_get_template_not_found(self, client: TestClient):
        """Test getting a non-existent template returns 404."""
        non_existent_id = uuid4()
        response = client.get(f"/api/rotation-templates/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Rotation template not found"

    def test_get_template_invalid_uuid(self, client: TestClient):
        """Test getting template with invalid UUID format."""
        response = client.get("/api/rotation-templates/not-a-uuid")

        assert response.status_code == 422  # Validation error

    def test_get_template_includes_all_fields(self, client: TestClient, db: Session):
        """Test that get returns all template fields."""
        template = RotationTemplate(
            id=uuid4(),
            name="Complete Template",
            activity_type="procedure",
            abbreviation="CT",
            clinic_location="Room 101",
            max_residents=2,
            requires_specialty="Cardiology",
            requires_procedure_credential=True,
            supervision_required=False,
            max_supervision_ratio=5,
        )
        db.add(template)
        db.commit()

        response = client.get(f"/api/rotation-templates/{template.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Complete Template"
        assert data["activity_type"] == "procedure"
        assert data["abbreviation"] == "CT"
        assert data["clinic_location"] == "Room 101"
        assert data["max_residents"] == 2
        assert data["requires_specialty"] == "Cardiology"
        assert data["requires_procedure_credential"] is True
        assert data["supervision_required"] is False
        assert data["max_supervision_ratio"] == 5

    def test_get_template_with_minimal_fields(self, client: TestClient, db: Session):
        """Test getting template with only required fields."""
        template = RotationTemplate(
            id=uuid4(),
            name="Minimal Template",
            activity_type="conference",
        )
        db.add(template)
        db.commit()

        response = client.get(f"/api/rotation-templates/{template.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Template"
        assert data["activity_type"] == "conference"
        assert data["abbreviation"] is None
        assert data["clinic_location"] is None


class TestCreateRotationTemplate:
    """Tests for POST /api/rotation-templates endpoint."""

    def test_create_template_minimal_fields(self, client: TestClient, db: Session):
        """Test creating template with only required fields."""
        template_data = {
            "name": "New Clinic",
            "activity_type": "clinic",
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "New Clinic"
        assert data["activity_type"] == "clinic"
        assert "created_at" in data

        # Verify it was saved to database
        template_id = UUID(data["id"])
        db_template = (
            db.query(RotationTemplate)
            .filter(RotationTemplate.id == template_id)
            .first()
        )
        assert db_template is not None
        assert db_template.name == "New Clinic"

    def test_create_template_all_fields(self, client: TestClient, db: Session):
        """Test creating template with all fields populated."""
        template_data = {
            "name": "Complete Sports Medicine",
            "activity_type": "clinic",
            "abbreviation": "CSM",
            "clinic_location": "Sports Med Center",
            "max_residents": 6,
            "requires_specialty": "Sports Medicine",
            "requires_procedure_credential": True,
            "supervision_required": True,
            "max_supervision_ratio": 2,
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Complete Sports Medicine"
        assert data["activity_type"] == "clinic"
        assert data["abbreviation"] == "CSM"
        assert data["clinic_location"] == "Sports Med Center"
        assert data["max_residents"] == 6
        assert data["requires_specialty"] == "Sports Medicine"
        assert data["requires_procedure_credential"] is True
        assert data["supervision_required"] is True
        assert data["max_supervision_ratio"] == 2

    def test_create_template_missing_required_name(self, client: TestClient):
        """Test creating template without required 'name' field."""
        template_data = {
            "activity_type": "clinic",
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 422  # Validation error

    def test_create_template_missing_required_activity_type(self, client: TestClient):
        """Test creating template without required 'activity_type' field."""
        template_data = {
            "name": "Test Clinic",
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 422  # Validation error

    def test_create_template_with_null_optional_fields(self, client: TestClient):
        """Test creating template with null optional fields."""
        template_data = {
            "name": "Null Fields Template",
            "activity_type": "inpatient",
            "abbreviation": None,
            "clinic_location": None,
            "max_residents": None,
            "requires_specialty": None,
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["abbreviation"] is None
        assert data["clinic_location"] is None

    def test_create_template_inpatient_type(self, client: TestClient):
        """Test creating inpatient activity type template."""
        template_data = {
            "name": "FMIT Inpatient",
            "activity_type": "inpatient",
            "abbreviation": "FMIT",
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["activity_type"] == "inpatient"

    def test_create_template_procedure_type(self, client: TestClient):
        """Test creating procedure activity type template."""
        template_data = {
            "name": "Joint Injection Procedure",
            "activity_type": "procedure",
            "requires_procedure_credential": True,
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["activity_type"] == "procedure"
        assert data["requires_procedure_credential"] is True

    def test_create_template_conference_type(self, client: TestClient):
        """Test creating conference activity type template."""
        template_data = {
            "name": "Weekly Grand Rounds",
            "activity_type": "conference",
            "supervision_required": False,
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["activity_type"] == "conference"

    def test_create_template_with_zero_max_residents(self, client: TestClient):
        """Test creating template with max_residents=0."""
        template_data = {
            "name": "No Resident Clinic",
            "activity_type": "clinic",
            "max_residents": 0,
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["max_residents"] == 0

    def test_create_template_boolean_defaults(self, client: TestClient):
        """Test that boolean fields have correct defaults."""
        template_data = {
            "name": "Default Boolean Template",
            "activity_type": "clinic",
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["requires_procedure_credential"] is False
        assert data["supervision_required"] is True

    def test_create_template_default_supervision_ratio(self, client: TestClient):
        """Test default max_supervision_ratio value."""
        template_data = {
            "name": "Default Ratio Template",
            "activity_type": "clinic",
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert data["max_supervision_ratio"] == 4

    def test_create_template_created_at_timestamp(self, client: TestClient):
        """Test that created_at timestamp is set correctly."""
        template_data = {
            "name": "Timestamp Test",
            "activity_type": "clinic",
        }

        response = client.post("/api/rotation-templates", json=template_data)

        assert response.status_code == 201
        data = response.json()
        assert "created_at" in data
        # Verify it's a valid ISO timestamp
        created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        assert isinstance(created_at, datetime)


class TestUpdateRotationTemplate:
    """Tests for PUT /api/rotation-templates/{template_id} endpoint."""

    def test_update_template_single_field(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test updating a single field."""
        update_data = {
            "name": "Updated Clinic Name",
        }

        response = client.put(
            f"/api/rotation-templates/{sample_rotation_template.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Clinic Name"
        assert data["activity_type"] == sample_rotation_template.activity_type

    def test_update_template_multiple_fields(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test updating multiple fields at once."""
        update_data = {
            "name": "New Name",
            "abbreviation": "NN",
            "max_residents": 10,
        }

        response = client.put(
            f"/api/rotation-templates/{sample_rotation_template.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["abbreviation"] == "NN"
        assert data["max_residents"] == 10

    def test_update_template_all_fields(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test updating all fields."""
        update_data = {
            "name": "Completely Updated",
            "activity_type": "inpatient",
            "abbreviation": "CU",
            "clinic_location": "New Location",
            "max_residents": 8,
            "requires_specialty": "Emergency Medicine",
            "requires_procedure_credential": True,
            "supervision_required": False,
            "max_supervision_ratio": 6,
        }

        response = client.put(
            f"/api/rotation-templates/{sample_rotation_template.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Completely Updated"
        assert data["activity_type"] == "inpatient"
        assert data["abbreviation"] == "CU"
        assert data["clinic_location"] == "New Location"
        assert data["max_residents"] == 8

    def test_update_template_not_found(self, client: TestClient):
        """Test updating non-existent template returns 404."""
        non_existent_id = uuid4()
        update_data = {"name": "Updated Name"}

        response = client.put(
            f"/api/rotation-templates/{non_existent_id}",
            json=update_data,
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Rotation template not found"

    def test_update_template_invalid_uuid(self, client: TestClient):
        """Test updating with invalid UUID format."""
        update_data = {"name": "Updated Name"}

        response = client.put(
            "/api/rotation-templates/invalid-uuid",
            json=update_data,
        )

        assert response.status_code == 422

    def test_update_template_empty_body(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test updating with empty body (no changes)."""
        response = client.put(
            f"/api/rotation-templates/{sample_rotation_template.id}",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        # Original values should remain
        assert data["name"] == sample_rotation_template.name

    def test_update_template_set_field_to_null(self, client: TestClient, db: Session):
        """Test setting optional field to null."""
        template = RotationTemplate(
            id=uuid4(),
            name="Template with Data",
            activity_type="clinic",
            abbreviation="TWD",
            clinic_location="Building B",
        )
        db.add(template)
        db.commit()

        update_data = {
            "abbreviation": None,
            "clinic_location": None,
        }

        response = client.put(
            f"/api/rotation-templates/{template.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["abbreviation"] is None
        assert data["clinic_location"] is None

    def test_update_template_change_activity_type(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test changing activity_type."""
        update_data = {
            "activity_type": "procedure",
        }

        response = client.put(
            f"/api/rotation-templates/{sample_rotation_template.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["activity_type"] == "procedure"

    def test_update_template_toggle_boolean_fields(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test toggling boolean fields."""
        update_data = {
            "requires_procedure_credential": True,
            "supervision_required": False,
        }

        response = client.put(
            f"/api/rotation-templates/{sample_rotation_template.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requires_procedure_credential"] is True
        assert data["supervision_required"] is False

    def test_update_template_preserves_id_and_created_at(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test that update preserves id and created_at."""
        original_id = str(sample_rotation_template.id)
        original_created_at = sample_rotation_template.created_at

        update_data = {
            "name": "Updated Name",
        }

        response = client.put(
            f"/api/rotation-templates/{sample_rotation_template.id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == original_id
        # created_at should not change
        assert data["created_at"] == original_created_at.isoformat()


class TestDeleteRotationTemplate:
    """Tests for DELETE /api/rotation-templates/{template_id} endpoint."""

    def test_delete_template_success(
        self,
        client: TestClient,
        db: Session,
        sample_rotation_template: RotationTemplate,
    ):
        """Test successfully deleting a template."""
        template_id = sample_rotation_template.id

        response = client.delete(f"/api/rotation-templates/{template_id}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify template was deleted from database
        db_template = (
            db.query(RotationTemplate)
            .filter(RotationTemplate.id == template_id)
            .first()
        )
        assert db_template is None

    def test_delete_template_not_found(self, client: TestClient):
        """Test deleting non-existent template returns 404."""
        non_existent_id = uuid4()

        response = client.delete(f"/api/rotation-templates/{non_existent_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Rotation template not found"

    def test_delete_template_invalid_uuid(self, client: TestClient):
        """Test deleting with invalid UUID format."""
        response = client.delete("/api/rotation-templates/invalid-uuid")

        assert response.status_code == 422

    def test_delete_template_twice(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test deleting same template twice returns 404 on second attempt."""
        template_id = sample_rotation_template.id

        # First delete
        response = client.delete(f"/api/rotation-templates/{template_id}")
        assert response.status_code == 204

        # Second delete
        response = client.delete(f"/api/rotation-templates/{template_id}")
        assert response.status_code == 404

    def test_delete_template_verify_list_updated(self, client: TestClient, db: Session):
        """Test that deleted template no longer appears in list."""
        template = RotationTemplate(
            id=uuid4(),
            name="To Be Deleted",
            activity_type="clinic",
        )
        db.add(template)
        db.commit()

        # Verify it's in the list
        response = client.get("/api/rotation-templates")
        assert response.status_code == 200
        assert response.json()["total"] == 1

        # Delete it
        response = client.delete(f"/api/rotation-templates/{template.id}")
        assert response.status_code == 204

        # Verify it's gone from list
        response = client.get("/api/rotation-templates")
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_delete_template_verify_get_fails(
        self, client: TestClient, sample_rotation_template: RotationTemplate
    ):
        """Test that GET fails after template is deleted."""
        template_id = sample_rotation_template.id

        # Verify we can get it initially
        response = client.get(f"/api/rotation-templates/{template_id}")
        assert response.status_code == 200

        # Delete it
        response = client.delete(f"/api/rotation-templates/{template_id}")
        assert response.status_code == 204

        # Verify GET now fails
        response = client.get(f"/api/rotation-templates/{template_id}")
        assert response.status_code == 404


class TestRotationTemplateIntegration:
    """Integration tests covering multiple operations."""

    def test_full_crud_lifecycle(self, client: TestClient, db: Session):
        """Test complete CRUD lifecycle: create, read, update, delete."""
        # Create
        create_data = {
            "name": "Lifecycle Test",
            "activity_type": "clinic",
            "abbreviation": "LT",
        }
        response = client.post("/api/rotation-templates", json=create_data)
        assert response.status_code == 201
        template_id = response.json()["id"]

        # Read
        response = client.get(f"/api/rotation-templates/{template_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Lifecycle Test"

        # Update
        update_data = {"name": "Updated Lifecycle"}
        response = client.put(
            f"/api/rotation-templates/{template_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Lifecycle"

        # Delete
        response = client.delete(f"/api/rotation-templates/{template_id}")
        assert response.status_code == 204

        # Verify deletion
        response = client.get(f"/api/rotation-templates/{template_id}")
        assert response.status_code == 404

    def test_create_multiple_and_filter(self, client: TestClient, db: Session):
        """Test creating multiple templates and filtering by type."""
        templates = [
            {"name": "Clinic 1", "activity_type": "clinic"},
            {"name": "Clinic 2", "activity_type": "clinic"},
            {"name": "Inpatient 1", "activity_type": "inpatient"},
            {"name": "Procedure 1", "activity_type": "procedure"},
        ]

        for template in templates:
            response = client.post("/api/rotation-templates", json=template)
            assert response.status_code == 201

        # Filter by clinic
        response = client.get("/api/rotation-templates?activity_type=clinic")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["activity_type"] == "clinic" for item in data["items"])

        # Filter by inpatient
        response = client.get("/api/rotation-templates?activity_type=inpatient")
        assert response.status_code == 200
        assert response.json()["total"] == 1

        # No filter (all)
        response = client.get("/api/rotation-templates")
        assert response.status_code == 200
        assert response.json()["total"] == 4

    def test_update_after_create(self, client: TestClient):
        """Test that newly created template can be immediately updated."""
        create_data = {
            "name": "Initial Name",
            "activity_type": "clinic",
        }
        response = client.post("/api/rotation-templates", json=create_data)
        assert response.status_code == 201
        template_id = response.json()["id"]

        update_data = {
            "name": "Updated Name",
            "abbreviation": "UN",
        }
        response = client.put(
            f"/api/rotation-templates/{template_id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["abbreviation"] == "UN"

    def test_template_with_specialty_requirements(self, client: TestClient):
        """Test creating and managing template with specialty requirements."""
        create_data = {
            "name": "Sports Medicine Clinic",
            "activity_type": "clinic",
            "requires_specialty": "Sports Medicine",
            "requires_procedure_credential": True,
            "max_supervision_ratio": 2,
        }

        response = client.post("/api/rotation-templates", json=create_data)
        assert response.status_code == 201
        data = response.json()
        assert data["requires_specialty"] == "Sports Medicine"
        assert data["requires_procedure_credential"] is True
        assert data["max_supervision_ratio"] == 2

    def test_template_capacity_management(self, client: TestClient):
        """Test template with capacity constraints."""
        create_data = {
            "name": "Limited Capacity Clinic",
            "activity_type": "clinic",
            "max_residents": 3,
            "clinic_location": "Small Room A",
        }

        response = client.post("/api/rotation-templates", json=create_data)
        assert response.status_code == 201
        template_id = response.json()["id"]

        # Update capacity
        update_data = {"max_residents": 5}
        response = client.put(
            f"/api/rotation-templates/{template_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["max_residents"] == 5

    def test_different_activity_types_coexist(self, client: TestClient, db: Session):
        """Test that different activity types can coexist."""
        activity_types = ["clinic", "inpatient", "procedure", "conference"]

        for activity_type in activity_types:
            template = RotationTemplate(
                id=uuid4(),
                name=f"Test {activity_type.title()}",
                activity_type=activity_type,
            )
            db.add(template)
        db.commit()

        response = client.get("/api/rotation-templates")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4

        returned_types = {item["activity_type"] for item in data["items"]}
        assert returned_types == set(activity_types)
