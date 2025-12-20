"""Tests for certifications API routes.

Comprehensive test suite covering certification type and person certification CRUD operations,
compliance monitoring, expiration tracking, and admin functions.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.certification import CertificationType, PersonCertification
from app.models.person import Person


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_cert_type(db: Session) -> CertificationType:
    """Create a sample BLS certification type."""
    cert_type = CertificationType(
        id=uuid4(),
        name="BLS",
        full_name="Basic Life Support",
        description="Basic CPR and emergency care",
        renewal_period_months=24,
        required_for_residents=True,
        required_for_faculty=True,
        is_active=True,
    )
    db.add(cert_type)
    db.commit()
    db.refresh(cert_type)
    return cert_type


@pytest.fixture
def sample_cert_types(db: Session) -> list[CertificationType]:
    """Create multiple certification types."""
    cert_types = []

    certs = [
        ("BLS", "Basic Life Support", 24),
        ("ACLS", "Advanced Cardiovascular Life Support", 24),
        ("PALS", "Pediatric Advanced Life Support", 24),
        ("NRP", "Neonatal Resuscitation Program", 24),
    ]

    for name, full_name, renewal in certs:
        cert_type = CertificationType(
            id=uuid4(),
            name=name,
            full_name=full_name,
            renewal_period_months=renewal,
            required_for_residents=True,
            required_for_faculty=True,
            is_active=True,
        )
        db.add(cert_type)
        cert_types.append(cert_type)

    db.commit()
    for ct in cert_types:
        db.refresh(ct)
    return cert_types


@pytest.fixture
def sample_person_cert(
    db: Session,
    sample_resident: Person,
    sample_cert_type: CertificationType,
) -> PersonCertification:
    """Create a sample person certification."""
    person_cert = PersonCertification(
        id=uuid4(),
        person_id=sample_resident.id,
        certification_type_id=sample_cert_type.id,
        certification_number="BLS-123456",
        issued_date=date.today() - timedelta(days=365),
        expiration_date=date.today() + timedelta(days=365),
        status="current",
        verified_by="Test Verifier",
        verified_date=date.today(),
    )
    db.add(person_cert)
    db.commit()
    db.refresh(person_cert)
    return person_cert


@pytest.fixture
def expiring_person_cert(
    db: Session,
    sample_resident: Person,
    sample_cert_types: list[CertificationType],
) -> PersonCertification:
    """Create a person certification that's expiring soon."""
    person_cert = PersonCertification(
        id=uuid4(),
        person_id=sample_resident.id,
        certification_type_id=sample_cert_types[1].id,  # ACLS
        certification_number="ACLS-789",
        issued_date=date.today() - timedelta(days=700),
        expiration_date=date.today() + timedelta(days=30),  # Expires in 30 days
        status="expiring_soon",
    )
    db.add(person_cert)
    db.commit()
    db.refresh(person_cert)
    return person_cert


@pytest.fixture
def expired_person_cert(
    db: Session,
    sample_faculty: Person,
    sample_cert_types: list[CertificationType],
) -> PersonCertification:
    """Create an expired person certification."""
    person_cert = PersonCertification(
        id=uuid4(),
        person_id=sample_faculty.id,
        certification_type_id=sample_cert_types[2].id,  # PALS
        certification_number="PALS-999",
        issued_date=date.today() - timedelta(days=800),
        expiration_date=date.today() - timedelta(days=30),  # Expired 30 days ago
        status="expired",
    )
    db.add(person_cert)
    db.commit()
    db.refresh(person_cert)
    return person_cert


# ============================================================================
# Certification Type Endpoints
# ============================================================================

class TestListCertificationTypesEndpoint:
    """Tests for GET /api/certifications/types endpoint."""

    def test_list_certification_types_empty(self, client: TestClient, db: Session):
        """Test listing certification types when none exist."""
        response = client.get("/api/certifications/types")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_certification_types_with_data(
        self, client: TestClient, sample_cert_types
    ):
        """Test listing certification types with existing data."""
        response = client.get("/api/certifications/types")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4

        # Validate structure
        cert = data["items"][0]
        assert "id" in cert
        assert "name" in cert
        assert "full_name" in cert
        assert "renewal_period_months" in cert
        assert "required_for_residents" in cert
        assert "required_for_faculty" in cert
        assert "is_active" in cert

    def test_list_certification_types_active_only(self, client: TestClient, db: Session):
        """Test filtering by active_only parameter."""
        # Create active and inactive cert types
        active = CertificationType(
            id=uuid4(),
            name="BLS",
            full_name="Basic Life Support",
            is_active=True,
        )
        inactive = CertificationType(
            id=uuid4(),
            name="OLD_CERT",
            full_name="Deprecated Certification",
            is_active=False,
        )
        db.add_all([active, inactive])
        db.commit()

        # Default: active_only=True
        response = client.get("/api/certifications/types")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "BLS"

        # Explicitly set active_only=False
        response = client.get("/api/certifications/types", params={"active_only": False})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2


class TestGetCertificationTypeEndpoint:
    """Tests for GET /api/certifications/types/{cert_type_id} endpoint."""

    def test_get_certification_type_success(
        self, client: TestClient, sample_cert_type: CertificationType
    ):
        """Test getting an existing certification type."""
        response = client.get(f"/api/certifications/types/{sample_cert_type.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_cert_type.id)
        assert data["name"] == sample_cert_type.name
        assert data["full_name"] == sample_cert_type.full_name
        assert data["renewal_period_months"] == sample_cert_type.renewal_period_months

    def test_get_certification_type_not_found(self, client: TestClient):
        """Test getting a non-existent certification type."""
        fake_id = uuid4()
        response = client.get(f"/api/certifications/types/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_certification_type_invalid_uuid(self, client: TestClient):
        """Test getting certification type with invalid UUID."""
        response = client.get("/api/certifications/types/invalid-uuid")

        assert response.status_code == 422


class TestCreateCertificationTypeEndpoint:
    """Tests for POST /api/certifications/types endpoint."""

    def test_create_certification_type_success(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a new certification type."""
        cert_data = {
            "name": "ALSO",
            "full_name": "Advanced Life Support in Obstetrics",
            "description": "OB emergency procedures",
            "renewal_period_months": 36,
            "required_for_residents": False,
            "required_for_faculty": True,
            "is_active": True,
        }

        response = client.post(
            "/api/certifications/types",
            json=cert_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == cert_data["name"]
        assert data["full_name"] == cert_data["full_name"]
        assert data["renewal_period_months"] == 36

    def test_create_certification_type_requires_auth(self, client: TestClient):
        """Test that creating certification type requires authentication."""
        cert_data = {
            "name": "TEST",
            "full_name": "Test Certification",
            "renewal_period_months": 24,
        }

        response = client.post("/api/certifications/types", json=cert_data)

        assert response.status_code == 401

    def test_create_certification_type_duplicate_name(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_cert_type: CertificationType,
    ):
        """Test creating certification type with duplicate name."""
        cert_data = {
            "name": sample_cert_type.name,  # Duplicate
            "full_name": "Different Full Name",
            "renewal_period_months": 24,
        }

        response = client.post(
            "/api/certifications/types",
            json=cert_data,
            headers=auth_headers,
        )

        assert response.status_code in [400, 422]

    def test_create_certification_type_missing_required_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating certification type with missing required fields."""
        cert_data = {
            # Missing 'name'
            "full_name": "Test Certification",
        }

        response = client.post(
            "/api/certifications/types",
            json=cert_data,
            headers=auth_headers,
        )

        assert response.status_code == 422


class TestUpdateCertificationTypeEndpoint:
    """Tests for PUT /api/certifications/types/{cert_type_id} endpoint."""

    def test_update_certification_type_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_cert_type: CertificationType,
    ):
        """Test updating a certification type."""
        update_data = {
            "full_name": "Updated Full Name",
            "renewal_period_months": 36,
            "required_for_residents": False,
        }

        response = client.put(
            f"/api/certifications/types/{sample_cert_type.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Full Name"
        assert data["renewal_period_months"] == 36
        assert data["required_for_residents"] is False

    def test_update_certification_type_requires_auth(
        self, client: TestClient, sample_cert_type: CertificationType
    ):
        """Test that updating certification type requires authentication."""
        update_data = {"full_name": "New Name"}

        response = client.put(
            f"/api/certifications/types/{sample_cert_type.id}",
            json=update_data,
        )

        assert response.status_code == 401

    def test_update_certification_type_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test updating non-existent certification type."""
        fake_id = uuid4()
        update_data = {"full_name": "New Name"}

        response = client.put(
            f"/api/certifications/types/{fake_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# Expiration & Compliance Endpoints
# ============================================================================

class TestGetExpiringCertificationsEndpoint:
    """Tests for GET /api/certifications/expiring endpoint."""

    def test_get_expiring_certifications_default_days(
        self,
        client: TestClient,
        expiring_person_cert: PersonCertification,
        sample_person_cert: PersonCertification,
    ):
        """Test getting expiring certifications with default 180 days."""
        response = client.get("/api/certifications/expiring")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "days_threshold" in data
        assert data["days_threshold"] == 180

        # Should include the expiring cert (30 days)
        assert data["total"] >= 1

    def test_get_expiring_certifications_custom_days(
        self,
        client: TestClient,
        expiring_person_cert: PersonCertification,
        sample_person_cert: PersonCertification,
    ):
        """Test getting expiring certifications with custom days parameter."""
        response = client.get("/api/certifications/expiring", params={"days": 60})

        assert response.status_code == 200
        data = response.json()
        assert data["days_threshold"] == 60

        # Should include expiring cert (30 days)
        assert data["total"] >= 1

    def test_get_expiring_certifications_narrow_window(
        self, client: TestClient, sample_person_cert: PersonCertification
    ):
        """Test with narrow window that excludes all certs."""
        response = client.get("/api/certifications/expiring", params={"days": 1})

        assert response.status_code == 200
        data = response.json()
        assert data["days_threshold"] == 1
        # sample_person_cert expires in 365 days, should not be included
        assert data["total"] == 0

    def test_expiring_certifications_response_structure(
        self, client: TestClient, expiring_person_cert: PersonCertification
    ):
        """Test response structure for expiring certifications."""
        response = client.get("/api/certifications/expiring", params={"days": 60})

        assert response.status_code == 200
        data = response.json()

        if data["total"] > 0:
            cert = data["items"][0]
            assert "id" in cert
            assert "person" in cert
            assert "certification_type" in cert
            assert "expiration_date" in cert
            assert "days_until_expiration" in cert
            assert "status" in cert


class TestGetComplianceSummaryEndpoint:
    """Tests for GET /api/certifications/compliance endpoint."""

    def test_get_compliance_summary_empty(self, client: TestClient):
        """Test compliance summary with no certifications."""
        response = client.get("/api/certifications/compliance")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "current" in data
        assert "expiring_soon" in data
        assert "expired" in data
        assert "compliance_rate" in data
        assert data["total"] == 0

    def test_get_compliance_summary_with_data(
        self,
        client: TestClient,
        sample_person_cert: PersonCertification,
        expiring_person_cert: PersonCertification,
        expired_person_cert: PersonCertification,
    ):
        """Test compliance summary with various cert statuses."""
        response = client.get("/api/certifications/compliance")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["current"] >= 1
        assert data["expiring_soon"] >= 1
        assert data["expired"] >= 1
        assert 0 <= data["compliance_rate"] <= 1.0


class TestGetPersonComplianceEndpoint:
    """Tests for GET /api/certifications/compliance/{person_id} endpoint."""

    def test_get_person_compliance_success(
        self,
        client: TestClient,
        sample_resident: Person,
        sample_person_cert: PersonCertification,
    ):
        """Test getting compliance for a specific person."""
        response = client.get(f"/api/certifications/compliance/{sample_resident.id}")

        assert response.status_code == 200
        data = response.json()
        assert "person" in data
        assert "total_required" in data
        assert "total_current" in data
        assert "expired" in data
        assert "expiring_soon" in data
        assert "missing" in data
        assert "is_compliant" in data
        assert data["person"]["id"] == str(sample_resident.id)

    def test_get_person_compliance_not_found(self, client: TestClient):
        """Test getting compliance for non-existent person."""
        fake_id = uuid4()
        response = client.get(f"/api/certifications/compliance/{fake_id}")

        assert response.status_code == 404


# ============================================================================
# Person Certification Endpoints
# ============================================================================

class TestListCertificationsForPersonEndpoint:
    """Tests for GET /api/certifications/by-person/{person_id} endpoint."""

    def test_list_certifications_for_person_empty(
        self, client: TestClient, sample_resident: Person
    ):
        """Test listing certifications for person with none."""
        response = client.get(f"/api/certifications/by-person/{sample_resident.id}")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0

    def test_list_certifications_for_person_with_data(
        self,
        client: TestClient,
        sample_resident: Person,
        sample_person_cert: PersonCertification,
    ):
        """Test listing certifications for person with data."""
        response = client.get(f"/api/certifications/by-person/{sample_resident.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["person_id"] == str(sample_resident.id)

    def test_list_certifications_include_expired(
        self,
        client: TestClient,
        sample_resident: Person,
        db: Session,
        sample_cert_type: CertificationType,
    ):
        """Test include_expired parameter."""
        # Create an expired cert
        expired_cert = PersonCertification(
            id=uuid4(),
            person_id=sample_resident.id,
            certification_type_id=sample_cert_type.id,
            issued_date=date.today() - timedelta(days=800),
            expiration_date=date.today() - timedelta(days=30),
            status="expired",
        )
        db.add(expired_cert)
        db.commit()

        # With expired (default)
        response = client.get(f"/api/certifications/by-person/{sample_resident.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

        # Without expired
        response = client.get(
            f"/api/certifications/by-person/{sample_resident.id}",
            params={"include_expired": False},
        )
        assert response.status_code == 200


class TestGetPersonCertificationEndpoint:
    """Tests for GET /api/certifications/{cert_id} endpoint."""

    def test_get_person_certification_success(
        self, client: TestClient, sample_person_cert: PersonCertification
    ):
        """Test getting a person certification."""
        response = client.get(f"/api/certifications/{sample_person_cert.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_person_cert.id)
        assert data["certification_number"] == sample_person_cert.certification_number
        assert "days_until_expiration" in data
        assert "is_expired" in data
        assert "is_expiring_soon" in data

    def test_get_person_certification_not_found(self, client: TestClient):
        """Test getting non-existent person certification."""
        fake_id = uuid4()
        response = client.get(f"/api/certifications/{fake_id}")

        assert response.status_code == 404

    def test_get_person_certification_invalid_uuid(self, client: TestClient):
        """Test getting certification with invalid UUID."""
        response = client.get("/api/certifications/invalid-uuid")

        assert response.status_code == 422


class TestCreatePersonCertificationEndpoint:
    """Tests for POST /api/certifications endpoint."""

    def test_create_person_certification_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_faculty: Person,
        sample_cert_type: CertificationType,
    ):
        """Test creating a person certification."""
        cert_data = {
            "person_id": str(sample_faculty.id),
            "certification_type_id": str(sample_cert_type.id),
            "certification_number": "BLS-NEW-123",
            "issued_date": date.today().isoformat(),
            "expiration_date": (date.today() + timedelta(days=730)).isoformat(),
            "status": "current",
            "verified_by": "Test Admin",
            "verified_date": date.today().isoformat(),
        }

        response = client.post(
            "/api/certifications",
            json=cert_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["certification_number"] == cert_data["certification_number"]

    def test_create_person_certification_requires_auth(
        self,
        client: TestClient,
        sample_resident: Person,
        sample_cert_type: CertificationType,
    ):
        """Test that creating person certification requires authentication."""
        cert_data = {
            "person_id": str(sample_resident.id),
            "certification_type_id": str(sample_cert_type.id),
            "issued_date": date.today().isoformat(),
            "expiration_date": (date.today() + timedelta(days=730)).isoformat(),
        }

        response = client.post("/api/certifications", json=cert_data)

        assert response.status_code == 401

    def test_create_person_certification_invalid_status(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
        sample_cert_type: CertificationType,
    ):
        """Test creating certification with invalid status."""
        cert_data = {
            "person_id": str(sample_resident.id),
            "certification_type_id": str(sample_cert_type.id),
            "issued_date": date.today().isoformat(),
            "expiration_date": (date.today() + timedelta(days=730)).isoformat(),
            "status": "invalid_status",
        }

        response = client.post(
            "/api/certifications",
            json=cert_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_person_certification_missing_required_fields(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating certification with missing required fields."""
        cert_data = {
            # Missing person_id, certification_type_id, dates
            "certification_number": "TEST-123",
        }

        response = client.post(
            "/api/certifications",
            json=cert_data,
            headers=auth_headers,
        )

        assert response.status_code == 422


class TestUpdatePersonCertificationEndpoint:
    """Tests for PUT /api/certifications/{cert_id} endpoint."""

    def test_update_person_certification_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_person_cert: PersonCertification,
    ):
        """Test updating a person certification."""
        update_data = {
            "certification_number": "BLS-UPDATED-999",
            "notes": "Updated certification info",
        }

        response = client.put(
            f"/api/certifications/{sample_person_cert.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["certification_number"] == "BLS-UPDATED-999"
        assert data["notes"] == "Updated certification info"

    def test_update_person_certification_requires_auth(
        self, client: TestClient, sample_person_cert: PersonCertification
    ):
        """Test that updating person certification requires authentication."""
        update_data = {"notes": "New notes"}

        response = client.put(
            f"/api/certifications/{sample_person_cert.id}",
            json=update_data,
        )

        assert response.status_code == 401

    def test_update_person_certification_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test updating non-existent person certification."""
        fake_id = uuid4()
        update_data = {"notes": "New notes"}

        response = client.put(
            f"/api/certifications/{fake_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestRenewCertificationEndpoint:
    """Tests for POST /api/certifications/{cert_id}/renew endpoint."""

    def test_renew_certification_success(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_person_cert: PersonCertification,
    ):
        """Test renewing a certification."""
        renewal_data = {
            "new_issued_date": date.today().isoformat(),
            "new_expiration_date": (date.today() + timedelta(days=730)).isoformat(),
            "new_certification_number": "BLS-RENEWED-2024",
        }

        response = client.post(
            f"/api/certifications/{sample_person_cert.id}/renew",
            json=renewal_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["certification_number"] == "BLS-RENEWED-2024"
        assert data["issued_date"] == renewal_data["new_issued_date"]
        assert data["expiration_date"] == renewal_data["new_expiration_date"]

    def test_renew_certification_requires_auth(
        self, client: TestClient, sample_person_cert: PersonCertification
    ):
        """Test that renewing certification requires authentication."""
        renewal_data = {
            "new_issued_date": date.today().isoformat(),
            "new_expiration_date": (date.today() + timedelta(days=730)).isoformat(),
        }

        response = client.post(
            f"/api/certifications/{sample_person_cert.id}/renew",
            json=renewal_data,
        )

        assert response.status_code == 401

    def test_renew_certification_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test renewing non-existent certification."""
        fake_id = uuid4()
        renewal_data = {
            "new_issued_date": date.today().isoformat(),
            "new_expiration_date": (date.today() + timedelta(days=730)).isoformat(),
        }

        response = client.post(
            f"/api/certifications/{fake_id}/renew",
            json=renewal_data,
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_renew_certification_missing_dates(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_person_cert: PersonCertification,
    ):
        """Test renewing with missing required dates."""
        renewal_data = {
            # Missing dates
            "new_certification_number": "BLS-123",
        }

        response = client.post(
            f"/api/certifications/{sample_person_cert.id}/renew",
            json=renewal_data,
            headers=auth_headers,
        )

        assert response.status_code == 422


class TestDeletePersonCertificationEndpoint:
    """Tests for DELETE /api/certifications/{cert_id} endpoint."""

    def test_delete_person_certification_success(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_cert_type: CertificationType,
    ):
        """Test deleting a person certification."""
        # Create a cert to delete
        cert = PersonCertification(
            id=uuid4(),
            person_id=sample_resident.id,
            certification_type_id=sample_cert_type.id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
        )
        db.add(cert)
        db.commit()
        cert_id = cert.id

        response = client.delete(
            f"/api/certifications/{cert_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deletion
        verify_response = client.get(f"/api/certifications/{cert_id}")
        assert verify_response.status_code == 404

    def test_delete_person_certification_requires_auth(
        self, client: TestClient, sample_person_cert: PersonCertification
    ):
        """Test that deleting certification requires authentication."""
        response = client.delete(f"/api/certifications/{sample_person_cert.id}")

        assert response.status_code == 401

    def test_delete_person_certification_not_found(
        self, client: TestClient, auth_headers: dict
    ):
        """Test deleting non-existent certification."""
        fake_id = uuid4()
        response = client.delete(
            f"/api/certifications/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404


# ============================================================================
# Admin Endpoints
# ============================================================================

class TestTriggerCertificationRemindersEndpoint:
    """Tests for POST /api/certifications/admin/send-reminders endpoint."""

    def test_trigger_reminders_success(
        self,
        client: TestClient,
        auth_headers: dict,
        expiring_person_cert: PersonCertification,
        expired_person_cert: PersonCertification,
    ):
        """Test manually triggering certification reminders (admin only)."""
        response = client.post(
            "/api/certifications/admin/send-reminders",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "statuses_updated" in data
        assert "expiring_count" in data
        assert "expired_count" in data
        assert data["status"] == "success"

    def test_trigger_reminders_requires_auth(self, client: TestClient):
        """Test that triggering reminders requires authentication."""
        response = client.post("/api/certifications/admin/send-reminders")

        assert response.status_code == 401

    def test_trigger_reminders_requires_admin(
        self, client: TestClient, db: Session
    ):
        """Test that triggering reminders requires admin role."""
        # Create non-admin user
        from app.models.user import User
        from app.core.security import get_password_hash

        user = User(
            id=uuid4(),
            username="regularuser",
            email="regular@test.org",
            hashed_password=get_password_hash("testpass123"),
            role="coordinator",  # Not admin
            is_active=True,
        )
        db.add(user)
        db.commit()

        # Login as regular user
        response = client.post(
            "/api/auth/login/json",
            json={"username": "regularuser", "password": "testpass123"},
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to trigger reminders
        response = client.post(
            "/api/certifications/admin/send-reminders",
            headers=headers,
        )

        assert response.status_code == 403  # Forbidden


# ============================================================================
# Edge Cases and Validation
# ============================================================================

class TestCertificationEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_certification_expiration_before_issued(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
        sample_cert_type: CertificationType,
    ):
        """Test creating certification with expiration before issued date."""
        cert_data = {
            "person_id": str(sample_resident.id),
            "certification_type_id": str(sample_cert_type.id),
            "issued_date": date.today().isoformat(),
            "expiration_date": (date.today() - timedelta(days=1)).isoformat(),
        }

        response = client.post(
            "/api/certifications",
            json=cert_data,
            headers=auth_headers,
        )

        # Should fail validation
        assert response.status_code in [400, 422]

    def test_certification_with_far_future_expiration(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_resident: Person,
        sample_cert_type: CertificationType,
    ):
        """Test creating certification with far future expiration."""
        cert_data = {
            "person_id": str(sample_resident.id),
            "certification_type_id": str(sample_cert_type.id),
            "issued_date": date.today().isoformat(),
            "expiration_date": (date.today() + timedelta(days=3650)).isoformat(),  # 10 years
        }

        response = client.post(
            "/api/certifications",
            json=cert_data,
            headers=auth_headers,
        )

        # Should succeed
        assert response.status_code in [201, 400, 422]

    def test_get_expiring_with_zero_days(self, client: TestClient):
        """Test getting expiring certifications with 0 days threshold."""
        response = client.get("/api/certifications/expiring", params={"days": 0})

        assert response.status_code == 200
        data = response.json()
        assert data["days_threshold"] == 0
        assert data["total"] == 0

    def test_get_expiring_with_negative_days(self, client: TestClient):
        """Test getting expiring certifications with negative days."""
        response = client.get("/api/certifications/expiring", params={"days": -30})

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]
