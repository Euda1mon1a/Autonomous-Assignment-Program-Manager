"""Tests for CertificationController."""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.certification_controller import CertificationController
from app.models.person import Person
from app.models.certification import CertificationType, PersonCertification
from app.schemas.certification import (
    CertificationTypeCreate,
    CertificationTypeUpdate,
    PersonCertificationCreate,
    PersonCertificationUpdate,
)


class TestCertificationController:
    """Test suite for CertificationController."""

    @pytest.fixture
    def setup_data(self, db):
        """Create common test data."""
        # Create residents and faculty
        resident = Person(
            id=uuid4(),
            name="Dr. Resident",
            type="resident",
            email="resident@hospital.org",
            pgy_level=2,
        )
        faculty = Person(
            id=uuid4(),
            name="Dr. Faculty",
            type="faculty",
            email="faculty@hospital.org",
        )
        db.add_all([resident, faculty])

        # Create certification types
        bls = CertificationType(
            id=uuid4(),
            name="BLS",
            full_name="Basic Life Support",
            description="Basic cardiac life support certification",
            renewal_period_months=24,
            required_for_residents=True,
            required_for_faculty=True,
            is_active=True,
        )
        acls = CertificationType(
            id=uuid4(),
            name="ACLS",
            full_name="Advanced Cardiovascular Life Support",
            description="Advanced cardiac life support certification",
            renewal_period_months=24,
            required_for_residents=True,
            required_for_faculty=True,
            is_active=True,
        )
        pals = CertificationType(
            id=uuid4(),
            name="PALS",
            full_name="Pediatric Advanced Life Support",
            description="Pediatric life support certification",
            renewal_period_months=24,
            required_for_residents=True,
            required_for_faculty=False,  # Not required for faculty
            is_active=True,
        )
        db.add_all([bls, acls, pals])
        db.commit()

        return {
            "resident": resident,
            "faculty": faculty,
            "bls": bls,
            "acls": acls,
            "pals": pals,
        }

    # ========================================================================
    # Certification Type Tests
    # ========================================================================

    def test_list_certification_types(self, db, setup_data):
        """Test listing certification types."""
        controller = CertificationController(db)
        result = controller.list_certification_types()

        assert result.total >= 3
        assert len(result.items) >= 3

    def test_list_certification_types_active_only(self, db, setup_data):
        """Test filtering to active types only."""
        # Create inactive type
        inactive = CertificationType(
            id=uuid4(),
            name="INACTIVE",
            full_name="Inactive Certification",
            is_active=False,
        )
        db.add(inactive)
        db.commit()

        controller = CertificationController(db)
        result = controller.list_certification_types(active_only=True)

        assert all(c.is_active for c in result.items)

    def test_get_certification_type_success(self, db, setup_data):
        """Test getting a certification type by ID."""
        controller = CertificationController(db)
        result = controller.get_certification_type(setup_data["bls"].id)

        assert result is not None
        assert result.name == "BLS"
        assert result.full_name == "Basic Life Support"

    def test_get_certification_type_not_found(self, db):
        """Test getting non-existent certification type raises 404."""
        controller = CertificationController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_certification_type(uuid4())

        assert exc_info.value.status_code == 404

    def test_create_certification_type(self, db):
        """Test creating a new certification type."""
        controller = CertificationController(db)

        cert_type_data = CertificationTypeCreate(
            name="NRP",
            full_name="Neonatal Resuscitation Program",
            description="Neonatal resuscitation certification",
            renewal_period_months=24,
            required_for_residents=True,
            required_for_faculty=False,
        )

        result = controller.create_certification_type(cert_type_data)

        assert result is not None
        assert result.name == "NRP"
        assert result.renewal_period_months == 24

    def test_create_certification_type_duplicate_name(self, db, setup_data):
        """Test creating certification type with duplicate name fails."""
        controller = CertificationController(db)

        cert_type_data = CertificationTypeCreate(
            name="BLS",  # Already exists
            full_name="Basic Life Support",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_certification_type(cert_type_data)

        assert exc_info.value.status_code == 400

    def test_update_certification_type(self, db, setup_data):
        """Test updating a certification type."""
        controller = CertificationController(db)

        update_data = CertificationTypeUpdate(
            description="Updated description",
            renewal_period_months=36,
        )

        result = controller.update_certification_type(setup_data["bls"].id, update_data)

        assert result.description == "Updated description"
        assert result.renewal_period_months == 36

    def test_update_certification_type_not_found(self, db):
        """Test updating non-existent certification type raises 404."""
        controller = CertificationController(db)

        update_data = CertificationTypeUpdate(description="New description")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_certification_type(uuid4(), update_data)

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Person Certification Tests
    # ========================================================================

    def test_list_certifications_for_person(self, db, setup_data):
        """Test listing certifications for a person."""
        # Create certifications for resident
        cert1 = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today() - timedelta(days=365),
            expiration_date=date.today() + timedelta(days=365),
            status="current",
        )
        cert2 = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["acls"].id,
            issued_date=date.today() - timedelta(days=365),
            expiration_date=date.today() + timedelta(days=365),
            status="current",
        )
        db.add_all([cert1, cert2])
        db.commit()

        controller = CertificationController(db)
        result = controller.list_certifications_for_person(setup_data["resident"].id)

        assert result.total >= 2

    def test_list_certifications_exclude_expired(self, db, setup_data):
        """Test excluding expired certifications from list."""
        # Create current and expired certifications
        current = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today() - timedelta(days=365),
            expiration_date=date.today() + timedelta(days=365),
            status="current",
        )
        # Note: For expired certs we need a separate cert type to avoid unique constraint
        expired = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["acls"].id,
            issued_date=date.today() - timedelta(days=730),
            expiration_date=date.today() - timedelta(days=1),
            status="expired",
        )
        db.add_all([current, expired])
        db.commit()

        controller = CertificationController(db)
        result = controller.list_certifications_for_person(
            setup_data["resident"].id, include_expired=False
        )

        # Should only include non-expired
        assert all(c.status != "expired" for c in result.items)

    def test_get_person_certification_success(self, db, setup_data):
        """Test getting a person certification by ID."""
        cert = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
            certification_number="BLS12345",
        )
        db.add(cert)
        db.commit()

        controller = CertificationController(db)
        result = controller.get_person_certification(cert.id)

        assert result is not None
        assert result.id == cert.id

    def test_get_person_certification_not_found(self, db):
        """Test getting non-existent person certification raises 404."""
        controller = CertificationController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_person_certification(uuid4())

        assert exc_info.value.status_code == 404

    def test_create_person_certification(self, db, setup_data):
        """Test creating a person certification."""
        controller = CertificationController(db)

        cert_data = PersonCertificationCreate(
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
            certification_number="BLS12345",
        )

        result = controller.create_person_certification(cert_data)

        assert result is not None
        assert result.certification_number == "BLS12345"

    def test_create_person_certification_duplicate(self, db, setup_data):
        """Test creating duplicate certification fails."""
        # Create initial certification
        existing = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
        )
        db.add(existing)
        db.commit()

        controller = CertificationController(db)

        cert_data = PersonCertificationCreate(
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,  # Same person and type
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_person_certification(cert_data)

        assert exc_info.value.status_code == 400

    def test_update_person_certification(self, db, setup_data):
        """Test updating a person certification."""
        cert = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
            notes="Original notes",
        )
        db.add(cert)
        db.commit()

        controller = CertificationController(db)

        update_data = PersonCertificationUpdate(notes="Updated notes")
        result = controller.update_person_certification(cert.id, update_data)

        assert result.notes == "Updated notes"

    def test_renew_certification(self, db, setup_data):
        """Test renewing a certification."""
        cert = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today() - timedelta(days=700),
            expiration_date=date.today() + timedelta(days=30),  # Expiring soon
            certification_number="BLS12345",
        )
        db.add(cert)
        db.commit()

        controller = CertificationController(db)

        new_issued = date.today()
        new_expiration = date.today() + timedelta(days=730)

        result = controller.renew_certification(
            cert.id,
            new_issued_date=new_issued,
            new_expiration_date=new_expiration,
            new_certification_number="BLS67890",
        )

        assert result.issued_date == new_issued
        assert result.expiration_date == new_expiration
        assert result.certification_number == "BLS67890"

    def test_delete_person_certification(self, db, setup_data):
        """Test deleting a person certification."""
        cert = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
        )
        db.add(cert)
        db.commit()
        cert_id = cert.id

        controller = CertificationController(db)
        controller.delete_person_certification(cert_id)

        # Verify deletion
        deleted = (
            db.query(PersonCertification)
            .filter(PersonCertification.id == cert_id)
            .first()
        )
        assert deleted is None

    # ========================================================================
    # Expiration & Compliance Tests
    # ========================================================================

    def test_get_expiring_certifications(self, db, setup_data):
        """Test getting certifications expiring soon."""
        # Create certifications with different expiration dates
        expiring_soon = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today() - timedelta(days=700),
            expiration_date=date.today() + timedelta(days=30),  # 30 days
        )
        not_expiring = PersonCertification(
            id=uuid4(),
            person_id=setup_data["faculty"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),  # 1 year
        )
        db.add_all([expiring_soon, not_expiring])
        db.commit()

        controller = CertificationController(db)
        result = controller.get_expiring_certifications(days=90)

        # Should include the one expiring in 30 days
        assert any(c.days_until_expiration <= 90 for c in result.items)

    def test_get_compliance_summary(self, db, setup_data):
        """Test getting overall compliance summary."""
        # Create some certifications
        cert = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
        )
        db.add(cert)
        db.commit()

        controller = CertificationController(db)
        result = controller.get_compliance_summary()

        assert result is not None
        assert hasattr(result, "total_personnel")

    def test_get_person_compliance(self, db, setup_data):
        """Test getting compliance for a specific person."""
        # Create some certifications for resident
        cert = PersonCertification(
            id=uuid4(),
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
        )
        db.add(cert)
        db.commit()

        controller = CertificationController(db)
        result = controller.get_person_compliance(setup_data["resident"].id)

        assert result.person.id == setup_data["resident"].id
        assert hasattr(result, "total_required")
        assert hasattr(result, "total_current")

    def test_get_person_compliance_not_found(self, db):
        """Test getting compliance for non-existent person raises 404."""
        controller = CertificationController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_person_compliance(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_create_and_renew_workflow(self, db, setup_data):
        """Test complete certification creation and renewal workflow."""
        controller = CertificationController(db)

        # Create initial certification
        cert_data = PersonCertificationCreate(
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today() - timedelta(days=700),
            expiration_date=date.today() + timedelta(days=30),
            certification_number="BLS001",
        )
        created = controller.create_person_certification(cert_data)
        cert_id = created.id

        # Verify it shows as expiring
        expiring = controller.get_expiring_certifications(days=60)
        assert any(c.id == cert_id for c in expiring.items)

        # Renew the certification
        renewed = controller.renew_certification(
            cert_id,
            new_issued_date=date.today(),
            new_expiration_date=date.today() + timedelta(days=730),
            new_certification_number="BLS002",
        )

        assert renewed.certification_number == "BLS002"
        assert renewed.expiration_date == date.today() + timedelta(days=730)

    def test_compliance_tracking(self, db, setup_data):
        """Test compliance tracking for a person."""
        controller = CertificationController(db)

        # Check initial compliance (no certifications)
        initial = controller.get_person_compliance(setup_data["resident"].id)
        initial_current = initial.total_current

        # Add a certification
        cert_data = PersonCertificationCreate(
            person_id=setup_data["resident"].id,
            certification_type_id=setup_data["bls"].id,
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=730),
        )
        controller.create_person_certification(cert_data)

        # Check compliance again
        after = controller.get_person_compliance(setup_data["resident"].id)
        assert after.total_current >= initial_current
