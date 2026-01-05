"""Comprehensive tests for resident weekly requirements.

Tests cover:
- Model creation and validation
- API routes CRUD operations
- Constraint validation and enforcement
- Schema validation
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.resident_weekly_requirement import ResidentWeeklyRequirement
from app.models.rotation_template import RotationTemplate
from app.schemas.resident_weekly_requirement import (
    ResidentWeeklyRequirementBase,
    ResidentWeeklyRequirementCreate,
    ResidentWeeklyRequirementUpdate,
)
from app.scheduling.constraints.resident_weekly_clinic import (
    ResidentAcademicTimeConstraint,
    ResidentClinicDayPreferenceConstraint,
    ResidentWeeklyClinicConstraint,
)
from app.scheduling.constraints.base import SchedulingContext


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def outpatient_template(db: Session) -> RotationTemplate:
    """Create an outpatient rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="Family Medicine Outpatient",
        activity_type="outpatient",
        abbreviation="FMO",
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def clinic_template(db: Session) -> RotationTemplate:
    """Create a clinic rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="Primary Care Clinic",
        activity_type="clinic",
        abbreviation="PCC",
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def sample_weekly_requirement(
    db: Session, outpatient_template: RotationTemplate
) -> ResidentWeeklyRequirement:
    """Create a sample weekly requirement."""
    requirement = ResidentWeeklyRequirement(
        id=uuid4(),
        rotation_template_id=outpatient_template.id,
        fm_clinic_min_per_week=2,
        fm_clinic_max_per_week=3,
        specialty_min_per_week=2,
        specialty_max_per_week=5,
        academics_required=True,
        protected_slots={"wed_am": "conference"},
        allowed_clinic_days=[0, 1, 2, 3, 4],  # Mon-Fri
        specialty_name="Family Medicine",
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


# =============================================================================
# Model Tests
# =============================================================================


class TestResidentWeeklyRequirementModel:
    """Tests for ResidentWeeklyRequirement SQLAlchemy model."""

    def test_create_requirement(
        self, db: Session, outpatient_template: RotationTemplate
    ):
        """Test creating a basic weekly requirement."""
        requirement = ResidentWeeklyRequirement(
            id=uuid4(),
            rotation_template_id=outpatient_template.id,
            fm_clinic_min_per_week=2,
            fm_clinic_max_per_week=4,
        )
        db.add(requirement)
        db.commit()

        assert requirement.id is not None
        assert requirement.rotation_template_id == outpatient_template.id
        assert requirement.fm_clinic_min_per_week == 2
        assert requirement.fm_clinic_max_per_week == 4
        assert requirement.academics_required is True  # Default

    def test_total_halfdays_properties(
        self, sample_weekly_requirement: ResidentWeeklyRequirement
    ):
        """Test computed total_min_halfdays and total_max_halfdays."""
        # With academics_required=True, adds 1 to totals
        # min: 2 (fm) + 2 (specialty) + 1 (academics) = 5
        # max: 3 (fm) + 5 (specialty) + 1 (academics) = 9
        assert sample_weekly_requirement.total_min_halfdays == 5
        assert sample_weekly_requirement.total_max_halfdays == 9

    def test_is_valid_range_valid(
        self, sample_weekly_requirement: ResidentWeeklyRequirement
    ):
        """Test is_valid_range returns True for valid ranges."""
        assert sample_weekly_requirement.is_valid_range is True

    def test_is_valid_range_invalid(
        self, db: Session, outpatient_template: RotationTemplate
    ):
        """Test is_valid_range returns False for invalid ranges."""
        requirement = ResidentWeeklyRequirement(
            id=uuid4(),
            rotation_template_id=outpatient_template.id,
            fm_clinic_min_per_week=5,  # min > max
            fm_clinic_max_per_week=2,
        )
        db.add(requirement)
        db.commit()

        assert requirement.is_valid_range is False

    def test_get_allowed_days_set_with_days(
        self, sample_weekly_requirement: ResidentWeeklyRequirement
    ):
        """Test get_allowed_days_set returns configured days."""
        days = sample_weekly_requirement.get_allowed_days_set()
        assert days == {0, 1, 2, 3, 4}

    def test_get_allowed_days_set_empty(
        self, db: Session, outpatient_template: RotationTemplate
    ):
        """Test get_allowed_days_set returns all weekdays when empty."""
        requirement = ResidentWeeklyRequirement(
            id=uuid4(),
            rotation_template_id=outpatient_template.id,
            allowed_clinic_days=[],
        )
        db.add(requirement)
        db.commit()

        days = requirement.get_allowed_days_set()
        assert days == {0, 1, 2, 3, 4}

    def test_is_slot_protected_true(
        self, sample_weekly_requirement: ResidentWeeklyRequirement
    ):
        """Test is_slot_protected returns True for protected slot."""
        # Wed AM is protected
        assert sample_weekly_requirement.is_slot_protected(2, "AM") is True

    def test_is_slot_protected_false(
        self, sample_weekly_requirement: ResidentWeeklyRequirement
    ):
        """Test is_slot_protected returns False for unprotected slot."""
        # Monday AM is not protected
        assert sample_weekly_requirement.is_slot_protected(0, "AM") is False

    def test_rotation_template_relationship(
        self, sample_weekly_requirement: ResidentWeeklyRequirement,
        outpatient_template: RotationTemplate
    ):
        """Test relationship to rotation template."""
        assert sample_weekly_requirement.rotation_template is not None
        assert sample_weekly_requirement.rotation_template.id == outpatient_template.id


# =============================================================================
# Schema Tests
# =============================================================================


class TestResidentWeeklyRequirementSchemas:
    """Tests for Pydantic schemas."""

    def test_base_schema_defaults(self):
        """Test base schema has correct defaults."""
        schema = ResidentWeeklyRequirementBase()
        assert schema.fm_clinic_min_per_week == 2
        assert schema.fm_clinic_max_per_week == 3
        assert schema.specialty_min_per_week == 0
        assert schema.specialty_max_per_week == 10
        assert schema.academics_required is True
        assert schema.protected_slots == {}
        assert schema.allowed_clinic_days == []

    def test_create_schema_requires_template_id(self):
        """Test create schema requires rotation_template_id."""
        with pytest.raises(Exception):  # ValidationError
            ResidentWeeklyRequirementCreate()  # Missing required field

    def test_create_schema_valid(self):
        """Test create schema with valid data."""
        schema = ResidentWeeklyRequirementCreate(
            rotation_template_id=uuid4(),
            fm_clinic_min_per_week=2,
            fm_clinic_max_per_week=4,
        )
        assert schema.fm_clinic_min_per_week == 2
        assert schema.fm_clinic_max_per_week == 4

    def test_protected_slots_validation_valid(self):
        """Test protected_slots validation with valid keys."""
        schema = ResidentWeeklyRequirementBase(
            protected_slots={"wed_am": "conference", "fri_pm": "didactics"}
        )
        assert "wed_am" in schema.protected_slots
        assert "fri_pm" in schema.protected_slots

    def test_protected_slots_validation_invalid_format(self):
        """Test protected_slots validation rejects invalid format."""
        with pytest.raises(Exception):  # ValidationError
            ResidentWeeklyRequirementBase(
                protected_slots={"wednesday_morning": "conference"}  # Invalid format
            )

    def test_protected_slots_validation_invalid_day(self):
        """Test protected_slots validation rejects invalid day."""
        with pytest.raises(Exception):  # ValidationError
            ResidentWeeklyRequirementBase(
                protected_slots={"sat_am": "conference"}  # Saturday invalid
            )

    def test_allowed_clinic_days_validation_valid(self):
        """Test allowed_clinic_days validation with valid days."""
        schema = ResidentWeeklyRequirementBase(
            allowed_clinic_days=[0, 1, 2, 3, 4]
        )
        assert schema.allowed_clinic_days == [0, 1, 2, 3, 4]

    def test_allowed_clinic_days_validation_invalid(self):
        """Test allowed_clinic_days validation rejects invalid days."""
        with pytest.raises(Exception):  # ValidationError
            ResidentWeeklyRequirementBase(
                allowed_clinic_days=[0, 5, 6]  # 5 and 6 are invalid (Sat, Sun)
            )

    def test_range_validation_min_exceeds_max(self):
        """Test validation rejects min > max for clinic."""
        with pytest.raises(Exception):  # ValidationError
            ResidentWeeklyRequirementBase(
                fm_clinic_min_per_week=5,
                fm_clinic_max_per_week=2,
            )

    def test_update_schema_all_optional(self):
        """Test update schema has all optional fields."""
        schema = ResidentWeeklyRequirementUpdate()  # Should not raise
        assert schema.fm_clinic_min_per_week is None
        assert schema.fm_clinic_max_per_week is None


# =============================================================================
# API Route Tests
# =============================================================================


class TestListResidentWeeklyRequirements:
    """Tests for GET /api/resident-weekly-requirements endpoint."""

    def test_list_requirements_empty(self, client: TestClient, db: Session):
        """Test listing requirements when database is empty."""
        response = client.get("/api/resident-weekly-requirements")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0

    def test_list_requirements_with_data(
        self, client: TestClient, sample_weekly_requirement: ResidentWeeklyRequirement
    ):
        """Test listing requirements with data."""
        response = client.get("/api/resident-weekly-requirements")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["fm_clinic_min_per_week"] == 2

    def test_list_requirements_filter_by_activity_type(
        self,
        client: TestClient,
        db: Session,
        outpatient_template: RotationTemplate,
        clinic_template: RotationTemplate,
    ):
        """Test filtering requirements by activity type."""
        # Create requirements for both templates
        req1 = ResidentWeeklyRequirement(
            id=uuid4(),
            rotation_template_id=outpatient_template.id,
            fm_clinic_min_per_week=2,
        )
        req2 = ResidentWeeklyRequirement(
            id=uuid4(),
            rotation_template_id=clinic_template.id,
            fm_clinic_min_per_week=3,
        )
        db.add_all([req1, req2])
        db.commit()

        response = client.get(
            "/api/resident-weekly-requirements?activity_type=outpatient"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


class TestCreateResidentWeeklyRequirement:
    """Tests for POST /api/resident-weekly-requirements endpoint."""

    def test_create_requirement(
        self, client: TestClient, outpatient_template: RotationTemplate
    ):
        """Test creating a new requirement."""
        response = client.post(
            "/api/resident-weekly-requirements",
            json={
                "rotation_template_id": str(outpatient_template.id),
                "fm_clinic_min_per_week": 2,
                "fm_clinic_max_per_week": 4,
                "academics_required": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["fm_clinic_min_per_week"] == 2
        assert data["fm_clinic_max_per_week"] == 4

    def test_create_requirement_template_not_found(self, client: TestClient):
        """Test creating requirement with non-existent template."""
        response = client.post(
            "/api/resident-weekly-requirements",
            json={
                "rotation_template_id": str(uuid4()),
                "fm_clinic_min_per_week": 2,
            },
        )

        assert response.status_code == 404

    def test_create_requirement_duplicate(
        self,
        client: TestClient,
        sample_weekly_requirement: ResidentWeeklyRequirement,
        outpatient_template: RotationTemplate,
    ):
        """Test creating duplicate requirement for same template."""
        response = client.post(
            "/api/resident-weekly-requirements",
            json={
                "rotation_template_id": str(outpatient_template.id),
                "fm_clinic_min_per_week": 3,
            },
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


class TestGetRequirementByTemplate:
    """Tests for GET /api/resident-weekly-requirements/by-template/{template_id}."""

    def test_get_requirement_by_template(
        self,
        client: TestClient,
        sample_weekly_requirement: ResidentWeeklyRequirement,
        outpatient_template: RotationTemplate,
    ):
        """Test getting requirement by template ID."""
        response = client.get(
            f"/api/resident-weekly-requirements/by-template/{outpatient_template.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template_name"] == outpatient_template.name
        assert data["fm_clinic_min_per_week"] == 2

    def test_get_requirement_template_not_found(self, client: TestClient):
        """Test getting requirement for non-existent template."""
        response = client.get(
            f"/api/resident-weekly-requirements/by-template/{uuid4()}"
        )

        assert response.status_code == 404

    def test_get_requirement_not_configured(
        self, client: TestClient, outpatient_template: RotationTemplate
    ):
        """Test getting requirement when none configured."""
        response = client.get(
            f"/api/resident-weekly-requirements/by-template/{outpatient_template.id}"
        )

        assert response.status_code == 404
        assert "not configured" in response.json()["detail"]


class TestUpsertRequirementByTemplate:
    """Tests for PUT /api/resident-weekly-requirements/by-template/{template_id}."""

    def test_create_via_upsert(
        self, client: TestClient, outpatient_template: RotationTemplate
    ):
        """Test creating requirement via upsert endpoint."""
        response = client.put(
            f"/api/resident-weekly-requirements/by-template/{outpatient_template.id}",
            json={"fm_clinic_min_per_week": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["fm_clinic_min_per_week"] == 3
        assert data["template_name"] == outpatient_template.name

    def test_update_via_upsert(
        self,
        client: TestClient,
        sample_weekly_requirement: ResidentWeeklyRequirement,
        outpatient_template: RotationTemplate,
    ):
        """Test updating existing requirement via upsert."""
        response = client.put(
            f"/api/resident-weekly-requirements/by-template/{outpatient_template.id}",
            json={"fm_clinic_min_per_week": 4},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["fm_clinic_min_per_week"] == 4


class TestDeleteRequirementByTemplate:
    """Tests for DELETE /api/resident-weekly-requirements/by-template/{template_id}."""

    def test_delete_requirement(
        self,
        client: TestClient,
        sample_weekly_requirement: ResidentWeeklyRequirement,
        outpatient_template: RotationTemplate,
    ):
        """Test deleting requirement by template."""
        response = client.delete(
            f"/api/resident-weekly-requirements/by-template/{outpatient_template.id}"
        )

        assert response.status_code == 204

        # Verify deleted
        response = client.get(
            f"/api/resident-weekly-requirements/by-template/{outpatient_template.id}"
        )
        assert response.status_code == 404


class TestBulkOutpatientDefaults:
    """Tests for POST /api/resident-weekly-requirements/bulk/outpatient-defaults."""

    def test_apply_outpatient_defaults(
        self, client: TestClient, outpatient_template: RotationTemplate
    ):
        """Test applying ACGME-compliant defaults to outpatient templates."""
        response = client.post(
            "/api/resident-weekly-requirements/bulk/outpatient-defaults"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 1
        assert str(outpatient_template.id) in data["created_ids"]

    def test_apply_outpatient_defaults_dry_run(
        self, client: TestClient, outpatient_template: RotationTemplate
    ):
        """Test dry run doesn't create requirements."""
        response = client.post(
            "/api/resident-weekly-requirements/bulk/outpatient-defaults?dry_run=true"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["created"] == 1

        # Verify not actually created
        response = client.get(
            f"/api/resident-weekly-requirements/by-template/{outpatient_template.id}"
        )
        assert response.status_code == 404


# =============================================================================
# Constraint Tests
# =============================================================================


class TestResidentWeeklyClinicConstraint:
    """Tests for ResidentWeeklyClinicConstraint."""

    def test_constraint_initialization(self):
        """Test constraint initializes correctly."""
        constraint = ResidentWeeklyClinicConstraint()
        assert constraint.name == "ResidentWeeklyClinic"
        assert constraint.enabled is True

    def test_constraint_with_requirements(self):
        """Test constraint with pre-loaded requirements."""
        template_id = uuid4()
        requirements = {
            template_id: {
                "fm_clinic_min_per_week": 2,
                "fm_clinic_max_per_week": 4,
            }
        }
        constraint = ResidentWeeklyClinicConstraint(
            weekly_requirements=requirements
        )

        req = constraint.get_requirement(template_id)
        assert req is not None
        assert req["fm_clinic_min_per_week"] == 2

    def test_constraint_requirement_not_found(self):
        """Test get_requirement returns None for unknown template."""
        constraint = ResidentWeeklyClinicConstraint()
        req = constraint.get_requirement(uuid4())
        assert req is None


class TestResidentAcademicTimeConstraint:
    """Tests for ResidentAcademicTimeConstraint."""

    def test_academic_constraint_initialization(self):
        """Test academic time constraint initializes correctly."""
        constraint = ResidentAcademicTimeConstraint()
        assert constraint.name == "ResidentAcademicTime"
        assert constraint.priority.name == "CRITICAL"


class TestResidentClinicDayPreferenceConstraint:
    """Tests for ResidentClinicDayPreferenceConstraint."""

    def test_preference_constraint_initialization(self):
        """Test clinic day preference constraint initializes correctly."""
        constraint = ResidentClinicDayPreferenceConstraint(weight=15.0)
        assert constraint.name == "ResidentClinicDayPreference"
        assert constraint.weight == 15.0
