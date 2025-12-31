"""Tests for CertificationService."""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from app.models.certification import CertificationType, PersonCertification
from app.services.certification_service import CertificationService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_cert_type(db) -> CertificationType:
    """Create a sample certification type (BLS)."""
    cert_type = CertificationType(
        id=uuid4(),
        name="BLS",
        full_name="Basic Life Support",
        description="Basic Life Support certification",
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
def sample_acls_cert_type(db) -> CertificationType:
    """Create a sample ACLS certification type."""
    cert_type = CertificationType(
        id=uuid4(),
        name="ACLS",
        full_name="Advanced Cardiovascular Life Support",
        description="ACLS certification",
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
def inactive_cert_type(db) -> CertificationType:
    """Create an inactive certification type."""
    cert_type = CertificationType(
        id=uuid4(),
        name="OLD_CERT",
        full_name="Old Certification",
        description="Deprecated certification",
        renewal_period_months=12,
        required_for_residents=False,
        required_for_faculty=False,
        is_active=False,
    )
    db.add(cert_type)
    db.commit()
    db.refresh(cert_type)
    return cert_type


@pytest.fixture
def current_certification(db, sample_resident, sample_cert_type) -> PersonCertification:
    """Create a current certification (expires in 1 year)."""
    cert = PersonCertification(
        id=uuid4(),
        person_id=sample_resident.id,
        certification_type_id=sample_cert_type.id,
        issued_date=date.today() - timedelta(days=365),
        expiration_date=date.today() + timedelta(days=365),
        status="current",
        certification_number="BLS123456",
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


@pytest.fixture
def expiring_soon_certification(
    db, sample_resident, sample_acls_cert_type
) -> PersonCertification:
    """Create a certification expiring soon (in 60 days)."""
    cert = PersonCertification(
        id=uuid4(),
        person_id=sample_resident.id,
        certification_type_id=sample_acls_cert_type.id,
        issued_date=date.today() - timedelta(days=670),
        expiration_date=date.today() + timedelta(days=60),
        status="expiring_soon",
        certification_number="ACLS789",
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


@pytest.fixture
def expired_certification(db, sample_faculty) -> PersonCertification:
    """Create an expired certification."""
    # Need a cert type
    cert_type = CertificationType(
        id=uuid4(),
        name="PALS",
        full_name="Pediatric Advanced Life Support",
        renewal_period_months=24,
        required_for_residents=True,
        required_for_faculty=True,
        is_active=True,
    )
    db.add(cert_type)
    db.flush()

    cert = PersonCertification(
        id=uuid4(),
        person_id=sample_faculty.id,
        certification_type_id=cert_type.id,
        issued_date=date.today() - timedelta(days=800),
        expiration_date=date.today() - timedelta(days=30),
        status="expired",
        certification_number="PALS999",
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


# ============================================================================
# Certification Type Operations Tests
# ============================================================================


class TestCertificationTypeOperations:
    """Test suite for certification type CRUD operations."""

    def test_get_certification_type_success(self, db, sample_cert_type):
        """Test getting a certification type by ID successfully."""
        service = CertificationService(db)
        result = service.get_certification_type(sample_cert_type.id)

        assert result is not None
        assert result.id == sample_cert_type.id
        assert result.name == "BLS"
        assert result.full_name == "Basic Life Support"

    def test_get_certification_type_not_found(self, db):
        """Test getting a non-existent certification type returns None."""
        service = CertificationService(db)
        result = service.get_certification_type(uuid4())

        assert result is None

    def test_get_certification_type_by_name_success(self, db, sample_cert_type):
        """Test getting a certification type by name successfully."""
        service = CertificationService(db)
        result = service.get_certification_type_by_name("BLS")

        assert result is not None
        assert result.id == sample_cert_type.id
        assert result.name == "BLS"

    def test_get_certification_type_by_name_not_found(self, db):
        """Test getting a certification type by non-existent name returns None."""
        service = CertificationService(db)
        result = service.get_certification_type_by_name("NONEXISTENT")

        assert result is None

    def test_list_certification_types_active_only(
        self, db, sample_cert_type, sample_acls_cert_type, inactive_cert_type
    ):
        """Test listing only active certification types."""
        service = CertificationService(db)
        result = service.list_certification_types(active_only=True)

        assert result["total"] == 2
        assert len(result["items"]) == 2
        cert_names = {cert.name for cert in result["items"]}
        assert "BLS" in cert_names
        assert "ACLS" in cert_names
        assert "OLD_CERT" not in cert_names

    def test_list_certification_types_include_inactive(
        self, db, sample_cert_type, sample_acls_cert_type, inactive_cert_type
    ):
        """Test listing all certification types including inactive."""
        service = CertificationService(db)
        result = service.list_certification_types(active_only=False)

        assert result["total"] == 3
        assert len(result["items"]) == 3
        cert_names = {cert.name for cert in result["items"]}
        assert "BLS" in cert_names
        assert "ACLS" in cert_names
        assert "OLD_CERT" in cert_names

    def test_list_certification_types_empty(self, db):
        """Test listing certification types when none exist."""
        service = CertificationService(db)
        result = service.list_certification_types()

        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_create_certification_type_success(self, db):
        """Test creating a new certification type successfully."""
        service = CertificationService(db)
        result = service.create_certification_type(
            name="NRP",
            full_name="Neonatal Resuscitation Program",
            description="NRP certification",
            renewal_period_months=24,
            required_for_residents=True,
            required_for_faculty=False,
        )

        assert result["error"] is None
        assert result["certification_type"] is not None
        cert_type = result["certification_type"]
        assert cert_type.name == "NRP"
        assert cert_type.full_name == "Neonatal Resuscitation Program"
        assert cert_type.renewal_period_months == 24
        assert cert_type.required_for_residents is True
        assert cert_type.required_for_faculty is False
        assert cert_type.is_active is True

    def test_create_certification_type_duplicate_name(self, db, sample_cert_type):
        """Test creating a certification type with duplicate name fails."""
        service = CertificationService(db)
        result = service.create_certification_type(
            name="BLS",
            full_name="Another BLS",
        )

        assert result["error"] is not None
        assert "already exists" in result["error"]
        assert result["certification_type"] is None

    def test_create_certification_type_with_defaults(self, db):
        """Test creating certification type uses default values."""
        service = CertificationService(db)
        result = service.create_certification_type(name="TEST_CERT")

        assert result["error"] is None
        cert_type = result["certification_type"]
        assert cert_type.renewal_period_months == 24  # Default
        assert cert_type.required_for_residents is True  # Default
        assert cert_type.required_for_faculty is True  # Default

    def test_update_certification_type_success(self, db, sample_cert_type):
        """Test updating a certification type successfully."""
        service = CertificationService(db)
        result = service.update_certification_type(
            sample_cert_type.id,
            {
                "full_name": "Updated BLS Name",
                "description": "Updated description",
                "renewal_period_months": 12,
            },
        )

        assert result["error"] is None
        assert result["certification_type"] is not None
        cert_type = result["certification_type"]
        assert cert_type.full_name == "Updated BLS Name"
        assert cert_type.description == "Updated description"
        assert cert_type.renewal_period_months == 12

    def test_update_certification_type_not_found(self, db):
        """Test updating a non-existent certification type returns error."""
        service = CertificationService(db)
        result = service.update_certification_type(
            uuid4(),
            {"description": "New description"},
        )

        assert result["error"] is not None
        assert "not found" in result["error"]
        assert result["certification_type"] is None


# ============================================================================
# Person Certification Operations Tests
# ============================================================================


class TestPersonCertificationOperations:
    """Test suite for person certification CRUD operations."""

    def test_get_person_certification_success(self, db, current_certification):
        """Test getting a person certification by ID successfully."""
        service = CertificationService(db)
        result = service.get_person_certification(current_certification.id)

        assert result is not None
        assert result.id == current_certification.id
        assert result.certification_number == "BLS123456"

    def test_get_person_certification_not_found(self, db):
        """Test getting a non-existent person certification returns None."""
        service = CertificationService(db)
        result = service.get_person_certification(uuid4())

        assert result is None

    def test_list_certifications_for_person_include_expired(
        self, db, sample_resident, current_certification, expiring_soon_certification
    ):
        """Test listing all certifications for a person including expired."""
        service = CertificationService(db)
        result = service.list_certifications_for_person(
            sample_resident.id, include_expired=True
        )

        assert result["total"] == 2
        assert len(result["items"]) == 2

    def test_list_certifications_for_person_exclude_expired(
        self, db, sample_resident, current_certification, expiring_soon_certification
    ):
        """Test listing only current certifications for a person."""
        service = CertificationService(db)
        result = service.list_certifications_for_person(
            sample_resident.id, include_expired=False
        )

        assert result["total"] == 2  # Both are current (not expired)
        assert len(result["items"]) == 2

    def test_list_certifications_for_person_empty(self, db, sample_resident):
        """Test listing certifications when person has none."""
        service = CertificationService(db)
        result = service.list_certifications_for_person(sample_resident.id)

        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_create_person_certification_success(
        self, db, sample_resident, sample_cert_type
    ):
        """Test creating a certification for a person successfully."""
        service = CertificationService(db)
        issued = date.today() - timedelta(days=30)
        expires = date.today() + timedelta(days=700)

        result = service.create_person_certification(
            person_id=sample_resident.id,
            certification_type_id=sample_cert_type.id,
            issued_date=issued,
            expiration_date=expires,
            certification_number="BLS999",
            verified_by="Test Admin",
            notes="Test certification",
        )

        assert result["error"] is None
        assert result["certification"] is not None
        cert = result["certification"]
        assert cert.person_id == sample_resident.id
        assert cert.certification_type_id == sample_cert_type.id
        assert cert.certification_number == "BLS999"
        assert cert.verified_by == "Test Admin"
        assert cert.verified_date == date.today()
        assert cert.status == "current"  # Far future expiration

    def test_create_person_certification_expiring_soon_status(
        self, db, sample_resident, sample_cert_type
    ):
        """Test creating a certification expiring soon gets correct status."""
        service = CertificationService(db)
        issued = date.today() - timedelta(days=600)
        expires = date.today() + timedelta(days=60)  # Within 180 days

        result = service.create_person_certification(
            person_id=sample_resident.id,
            certification_type_id=sample_cert_type.id,
            issued_date=issued,
            expiration_date=expires,
        )

        assert result["error"] is None
        cert = result["certification"]
        assert cert.status == "expiring_soon"

    def test_create_person_certification_expired_status(
        self, db, sample_resident, sample_cert_type
    ):
        """Test creating an already expired certification gets correct status."""
        service = CertificationService(db)
        issued = date.today() - timedelta(days=800)
        expires = date.today() - timedelta(days=50)  # Already expired

        result = service.create_person_certification(
            person_id=sample_resident.id,
            certification_type_id=sample_cert_type.id,
            issued_date=issued,
            expiration_date=expires,
        )

        assert result["error"] is None
        cert = result["certification"]
        assert cert.status == "expired"

    def test_create_person_certification_person_not_found(self, db, sample_cert_type):
        """Test creating certification for non-existent person fails."""
        service = CertificationService(db)
        result = service.create_person_certification(
            person_id=uuid4(),
            certification_type_id=sample_cert_type.id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
        )

        assert result["error"] is not None
        assert "Person not found" in result["error"]
        assert result["certification"] is None

    def test_create_person_certification_type_not_found(self, db, sample_resident):
        """Test creating certification with non-existent type fails."""
        service = CertificationService(db)
        result = service.create_person_certification(
            person_id=sample_resident.id,
            certification_type_id=uuid4(),
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
        )

        assert result["error"] is not None
        assert "Certification type not found" in result["error"]
        assert result["certification"] is None

    def test_create_person_certification_duplicate(
        self, db, sample_resident, sample_cert_type, current_certification
    ):
        """Test creating duplicate certification fails."""
        service = CertificationService(db)
        result = service.create_person_certification(
            person_id=sample_resident.id,
            certification_type_id=sample_cert_type.id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
        )

        assert result["error"] is not None
        assert "already has" in result["error"]
        assert "Update it instead" in result["error"]
        assert result["certification"] is None

    def test_update_person_certification_success(self, db, current_certification):
        """Test updating a person certification successfully."""
        service = CertificationService(db)
        result = service.update_person_certification(
            current_certification.id,
            {
                "certification_number": "BLS-NEW-123",
                "notes": "Updated notes",
            },
        )

        assert result["error"] is None
        cert = result["certification"]
        assert cert.certification_number == "BLS-NEW-123"
        assert cert.notes == "Updated notes"

    def test_update_person_certification_expiration_recalculates_status(
        self, db, current_certification
    ):
        """Test updating expiration date recalculates status."""
        service = CertificationService(db)
        # Update to expire soon
        new_expiration = date.today() + timedelta(days=30)
        result = service.update_person_certification(
            current_certification.id,
            {"expiration_date": new_expiration},
        )

        assert result["error"] is None
        cert = result["certification"]
        assert cert.expiration_date == new_expiration
        assert cert.status == "expiring_soon"

    def test_update_person_certification_to_expired(self, db, current_certification):
        """Test updating to expired date sets status to expired."""
        service = CertificationService(db)
        new_expiration = date.today() - timedelta(days=10)
        result = service.update_person_certification(
            current_certification.id,
            {"expiration_date": new_expiration},
        )

        assert result["error"] is None
        cert = result["certification"]
        assert cert.status == "expired"

    def test_update_person_certification_not_found(self, db):
        """Test updating non-existent certification returns error."""
        service = CertificationService(db)
        result = service.update_person_certification(
            uuid4(),
            {"notes": "Test"},
        )

        assert result["error"] is not None
        assert "not found" in result["error"]
        assert result["certification"] is None

    def test_renew_certification_success(self, db, expiring_soon_certification):
        """Test renewing a certification successfully."""
        service = CertificationService(db)
        new_issued = date.today()
        new_expires = date.today() + timedelta(days=730)

        result = service.renew_certification(
            expiring_soon_certification.id,
            new_issued_date=new_issued,
            new_expiration_date=new_expires,
            new_certification_number="ACLS-RENEWED",
        )

        assert result["error"] is None
        cert = result["certification"]
        assert cert.issued_date == new_issued
        assert cert.expiration_date == new_expires
        assert cert.certification_number == "ACLS-RENEWED"
        assert cert.status == "current"
        # Reminder flags should be reset
        assert cert.reminder_180_sent is None
        assert cert.reminder_90_sent is None
        assert cert.reminder_30_sent is None

    def test_renew_certification_without_new_number(
        self, db, expiring_soon_certification
    ):
        """Test renewing certification keeps old number if not provided."""
        service = CertificationService(db)
        old_number = expiring_soon_certification.certification_number
        new_issued = date.today()
        new_expires = date.today() + timedelta(days=730)

        result = service.renew_certification(
            expiring_soon_certification.id,
            new_issued_date=new_issued,
            new_expiration_date=new_expires,
        )

        assert result["error"] is None
        cert = result["certification"]
        assert cert.certification_number == old_number

    def test_renew_certification_not_found(self, db):
        """Test renewing non-existent certification returns error."""
        service = CertificationService(db)
        result = service.renew_certification(
            uuid4(),
            new_issued_date=date.today(),
            new_expiration_date=date.today() + timedelta(days=730),
        )

        assert result["error"] is not None
        assert "not found" in result["error"]
        assert result["certification"] is None

    def test_delete_person_certification_success(self, db, current_certification):
        """Test deleting a person certification successfully."""
        service = CertificationService(db)
        cert_id = current_certification.id

        result = service.delete_person_certification(cert_id)

        assert result["error"] is None
        assert result["success"] is True

        # Verify it's deleted
        deleted_cert = service.get_person_certification(cert_id)
        assert deleted_cert is None

    def test_delete_person_certification_not_found(self, db):
        """Test deleting non-existent certification returns error."""
        service = CertificationService(db)
        result = service.delete_person_certification(uuid4())

        assert result["error"] is not None
        assert "not found" in result["error"]
        assert result["success"] is False


# ============================================================================
# Expiration & Compliance Tests
# ============================================================================


class TestExpirationAndCompliance:
    """Test suite for expiration tracking and compliance checks."""

    def test_get_expiring_certifications_default_180_days(
        self,
        db,
        current_certification,
        expiring_soon_certification,
        expired_certification,
    ):
        """Test getting certifications expiring within 180 days."""
        service = CertificationService(db)
        result = service.get_expiring_certifications(days=180)

        assert result["days_threshold"] == 180
        # expiring_soon_certification expires in 60 days, should be included
        # current_certification expires in 365 days, should NOT be included
        # expired_certification already expired, should NOT be included
        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].id == expiring_soon_certification.id

    def test_get_expiring_certifications_custom_days(
        self, db, current_certification, expiring_soon_certification
    ):
        """Test getting certifications expiring within custom days."""
        service = CertificationService(db)
        result = service.get_expiring_certifications(days=30)

        # Only certifications expiring within 30 days
        # expiring_soon_certification expires in 60 days, should NOT be included
        assert result["total"] == 0

        # Test with 90 days
        result = service.get_expiring_certifications(days=90)
        assert result["total"] == 1

    def test_get_expired_certifications(
        self, db, current_certification, expired_certification
    ):
        """Test getting all expired certifications."""
        service = CertificationService(db)
        result = service.get_expired_certifications()

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0].id == expired_certification.id

    def test_get_compliance_summary(
        self,
        db,
        current_certification,
        expiring_soon_certification,
        expired_certification,
    ):
        """Test getting overall compliance summary."""
        service = CertificationService(db)
        result = service.get_compliance_summary()

        assert result["total"] == 3
        assert result["current"] == 2  # current and expiring_soon
        assert result["expired"] == 1
        assert result["expiring_soon"] == 1
        # Compliance rate should be (2/3) * 100 = 66.67
        assert 66 <= result["compliance_rate"] <= 67

    def test_get_compliance_summary_empty(self, db):
        """Test compliance summary with no certifications."""
        service = CertificationService(db)
        result = service.get_compliance_summary()

        assert result["total"] == 0
        assert result["current"] == 0
        assert result["expired"] == 0
        assert result["compliance_rate"] == 100  # Default when none exist

    def test_get_person_compliance_success(
        self, db, sample_resident, sample_cert_type, current_certification
    ):
        """Test getting compliance status for a person."""
        service = CertificationService(db)
        result = service.get_person_compliance(sample_resident.id)

        assert result["error"] is None
        assert result["person"].id == sample_resident.id
        assert result["total_required"] >= 0
        assert result["total_current"] == 1
        assert result["expired"] == 0
        assert result["expiring_soon"] == 0

    def test_get_person_compliance_with_missing_certs(
        self, db, sample_resident, sample_cert_type, sample_acls_cert_type
    ):
        """Test getting compliance with missing required certifications."""
        service = CertificationService(db)
        result = service.get_person_compliance(sample_resident.id)

        assert result["error"] is None
        # Person has no certifications but 2 are required
        assert result["total_required"] == 2
        assert result["total_current"] == 0
        assert len(result["missing"]) == 2
        assert result["is_compliant"] is False

    def test_get_person_compliance_person_not_found(self, db):
        """Test getting compliance for non-existent person."""
        service = CertificationService(db)
        result = service.get_person_compliance(uuid4())

        assert result["error"] is not None
        assert "Person not found" in result["error"]

    def test_get_certifications_needing_reminder(self, db, expiring_soon_certification):
        """Test getting certifications that need reminders."""
        service = CertificationService(db)
        # expiring_soon_certification expires in 60 days
        result = service.get_certifications_needing_reminder(days=90)

        assert len(result) == 1
        assert result[0].id == expiring_soon_certification.id

    def test_get_certifications_needing_reminder_already_sent(
        self, db, expiring_soon_certification
    ):
        """Test certifications with reminders already sent are excluded."""
        # Mark reminder as sent
        expiring_soon_certification.reminder_90_sent = datetime.utcnow()
        db.commit()

        service = CertificationService(db)
        result = service.get_certifications_needing_reminder(days=90)

        assert len(result) == 0

    def test_mark_reminder_sent_success(self, db, expiring_soon_certification):
        """Test marking a reminder as sent successfully."""
        service = CertificationService(db)
        result = service.mark_reminder_sent(expiring_soon_certification.id, days=90)

        assert result["error"] is None
        assert result["success"] is True

        # Verify reminder was marked
        db.refresh(expiring_soon_certification)
        assert expiring_soon_certification.reminder_90_sent is not None

    def test_mark_reminder_sent_not_found(self, db):
        """Test marking reminder for non-existent certification."""
        service = CertificationService(db)
        result = service.mark_reminder_sent(uuid4(), days=90)

        assert result["error"] is not None
        assert "not found" in result["error"]
        assert result["success"] is False

    def test_update_all_statuses(
        self, db, current_certification, expiring_soon_certification
    ):
        """Test updating all certification statuses."""
        # Manually set wrong statuses
        current_certification.status = "expired"  # Wrong
        expiring_soon_certification.status = "current"  # Wrong
        db.commit()

        service = CertificationService(db)
        count = service.update_all_statuses()

        # Should have updated 2 certifications
        assert count == 2

        # Verify statuses are corrected
        db.refresh(current_certification)
        db.refresh(expiring_soon_certification)
        assert current_certification.status == "current"
        assert expiring_soon_certification.status == "expiring_soon"


# ============================================================================
# Bulk Operations Tests
# ============================================================================


class TestBulkOperations:
    """Test suite for bulk certification operations."""

    def test_bulk_add_certifications_for_person_success(
        self, db, sample_resident, sample_cert_type, sample_acls_cert_type
    ):
        """Test bulk adding certifications for a person successfully."""
        service = CertificationService(db)
        cert_data = [
            {
                "certification_type_id": sample_cert_type.id,
                "issued_date": date.today() - timedelta(days=365),
                "expiration_date": date.today() + timedelta(days=365),
                "certification_number": "BLS123",
            },
            {
                "certification_type_id": sample_acls_cert_type.id,
                "issued_date": date.today() - timedelta(days=200),
                "expiration_date": date.today() + timedelta(days=530),
                "certification_number": "ACLS456",
                "verified_by": "Admin",
                "notes": "Test note",
            },
        ]

        result = service.bulk_add_certifications_for_person(
            sample_resident.id, cert_data
        )

        assert result["total_created"] == 2
        assert result["total_errors"] == 0
        assert len(result["created"]) == 2
        assert len(result["errors"]) == 0

    def test_bulk_add_certifications_partial_failure(
        self, db, sample_resident, sample_cert_type, sample_acls_cert_type
    ):
        """Test bulk adding with some failures."""
        service = CertificationService(db)
        cert_data = [
            {
                "certification_type_id": sample_cert_type.id,
                "issued_date": date.today(),
                "expiration_date": date.today() + timedelta(days=365),
            },
            {
                # Invalid cert type ID
                "certification_type_id": uuid4(),
                "issued_date": date.today(),
                "expiration_date": date.today() + timedelta(days=365),
            },
            {
                "certification_type_id": sample_acls_cert_type.id,
                "issued_date": date.today(),
                "expiration_date": date.today() + timedelta(days=365),
            },
        ]

        result = service.bulk_add_certifications_for_person(
            sample_resident.id, cert_data
        )

        assert result["total_created"] == 2
        assert result["total_errors"] == 1
        assert len(result["created"]) == 2
        assert len(result["errors"]) == 1
        assert "Certification type not found" in result["errors"][0]["error"]

    def test_bulk_add_certifications_all_failures(self, db, sample_resident):
        """Test bulk adding where all fail."""
        service = CertificationService(db)
        cert_data = [
            {
                "certification_type_id": uuid4(),
                "issued_date": date.today(),
                "expiration_date": date.today() + timedelta(days=365),
            },
            {
                "certification_type_id": uuid4(),
                "issued_date": date.today(),
                "expiration_date": date.today() + timedelta(days=365),
            },
        ]

        result = service.bulk_add_certifications_for_person(
            sample_resident.id, cert_data
        )

        assert result["total_created"] == 0
        assert result["total_errors"] == 2
        assert len(result["created"]) == 0
        assert len(result["errors"]) == 2

    def test_bulk_add_certifications_empty_list(self, db, sample_resident):
        """Test bulk adding with empty list."""
        service = CertificationService(db)
        result = service.bulk_add_certifications_for_person(sample_resident.id, [])

        assert result["total_created"] == 0
        assert result["total_errors"] == 0
        assert len(result["created"]) == 0
        assert len(result["errors"]) == 0
