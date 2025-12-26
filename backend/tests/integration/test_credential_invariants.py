"""
Integration tests for credential invariant system.

Tests cover:
- Hard credential requirement enforcement (Frame 7.1)
- Soft credential penalties for expiring credentials (Frame 7.2)
- Credential renewal during active assignments (Frame 7.3)
- Dashboard hard failure prediction (Frame 7.4)

Based on slot-type invariants from CLAUDE.md and test frames from
docs/testing/TEST_SCENARIO_FRAMES.md sections 7.1-7.4.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.certification import CertificationType, PersonCertification
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


# ============================================================================
# Slot-Type Invariant Catalog (Mock)
# ============================================================================

INVARIANT_CATALOG = {
    "inpatient_call": {
        "hard": ["HIPAA", "Cyber_Training", "AUP", "Chaperone", "N95_Fit"],
        "soft": [{"name": "expiring_soon", "window_days": 14, "penalty": 3}],
    },
    "peds_clinic": {
        "hard": ["BLS", "HIPAA"],
        "soft": [{"name": "expiring_soon", "window_days": 14, "penalty": 3}],
    },
    "procedures_half_day": {
        "hard": ["BLS", "BBP_Module", "Sharps_Safety"],
        "soft": [{"name": "expiring_soon", "window_days": 30, "penalty": 5}],
    },
    "general_clinic": {
        "hard": ["HIPAA", "BLS"],
        "soft": [{"name": "expiring_soon", "window_days": 14, "penalty": 2}],
    },
}


# ============================================================================
# Helper Functions
# ============================================================================


def is_eligible(
    person: Person, slot_type: str, assignment_date: date, db: Session
) -> tuple[bool, int, list[str]]:
    """
    Check if person meets slot requirements.

    Args:
        person: Person to check
        slot_type: Type of slot (e.g., "inpatient_call")
        assignment_date: Date of assignment
        db: Database session

    Returns:
        tuple: (eligible: bool, penalty: int, missing_credentials: list[str])
    """
    reqs = INVARIANT_CATALOG.get(slot_type, {})
    missing_credentials = []
    penalty = 0

    # Hard constraints - must pass all
    for req_cert_name in reqs.get("hard", []):
        # Find certification type
        cert_type = (
            db.query(CertificationType)
            .filter(CertificationType.name == req_cert_name)
            .first()
        )
        if not cert_type:
            missing_credentials.append(req_cert_name)
            continue

        # Check if person has this certification
        person_cert = (
            db.query(PersonCertification)
            .filter(
                PersonCertification.person_id == person.id,
                PersonCertification.certification_type_id == cert_type.id,
            )
            .first()
        )

        if not person_cert:
            missing_credentials.append(req_cert_name)
        elif person_cert.expiration_date < assignment_date:
            missing_credentials.append(f"{req_cert_name} (expired)")

    # If any hard constraint fails, not eligible
    if missing_credentials:
        return False, 0, missing_credentials

    # Soft constraints - accumulate penalties
    for soft in reqs.get("soft", []):
        if soft["name"] == "expiring_soon":
            window_days = soft["window_days"]
            window_end = assignment_date + timedelta(days=window_days)

            # Check all required hard credentials for expiration
            for req_cert_name in reqs.get("hard", []):
                cert_type = (
                    db.query(CertificationType)
                    .filter(CertificationType.name == req_cert_name)
                    .first()
                )
                if not cert_type:
                    continue

                person_cert = (
                    db.query(PersonCertification)
                    .filter(
                        PersonCertification.person_id == person.id,
                        PersonCertification.certification_type_id == cert_type.id,
                    )
                    .first()
                )

                if person_cert and person_cert.expiration_date <= window_end:
                    penalty += soft["penalty"]
                    break  # Only apply penalty once per slot

    return True, penalty, []


def predict_next_block_failures(db: Session, current_block_number: int) -> list[dict]:
    """
    Predict which faculty will have hard credential failures in next block.

    Args:
        db: Database session
        current_block_number: Current block number

    Returns:
        list: Predictions with person_id, failing_credentials, affected_assignments
    """
    predictions = []
    next_block_number = current_block_number + 1

    # Get all assignments in next block
    next_block_assignments = (
        db.query(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .filter(Block.block_number == next_block_number)
        .all()
    )

    for assignment in next_block_assignments:
        person = db.query(Person).filter(Person.id == assignment.person_id).first()
        if not person:
            continue

        # Get slot type from rotation template
        rotation = (
            db.query(RotationTemplate)
            .filter(RotationTemplate.id == assignment.rotation_template_id)
            .first()
        )
        if not rotation:
            continue

        # Use activity_type as slot_type (simplified)
        slot_type = rotation.activity_type

        # Check eligibility for block start date
        block = db.query(Block).filter(Block.id == assignment.block_id).first()
        if not block:
            continue

        eligible, _, missing = is_eligible(person, slot_type, block.date, db)

        if not eligible:
            # Check if already in predictions
            existing = next(
                (p for p in predictions if p["person_id"] == person.id), None
            )
            if existing:
                existing["failing_credentials"].extend(missing)
                existing["affected_assignments"].append(assignment.id)
            else:
                predictions.append(
                    {
                        "person_id": person.id,
                        "person_name": person.name,
                        "failing_credentials": missing,
                        "affected_assignments": [assignment.id],
                    }
                )

    return predictions


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def cert_types(db: Session) -> dict[str, CertificationType]:
    """Create standard certification types."""
    certs_data = {
        "BLS": {
            "full_name": "Basic Life Support",
            "renewal_period_months": 24,
        },
        "N95_Fit": {
            "full_name": "N95 Respirator Fit Test",
            "renewal_period_months": 12,
        },
        "HIPAA": {
            "full_name": "HIPAA Privacy Training",
            "renewal_period_months": 12,
        },
        "Cyber_Training": {
            "full_name": "Cybersecurity Awareness Training",
            "renewal_period_months": 12,
        },
        "AUP": {
            "full_name": "Acceptable Use Policy Acknowledgment",
            "renewal_period_months": 12,
        },
        "Chaperone": {
            "full_name": "Chaperone Training",
            "renewal_period_months": 24,
        },
        "BBP_Module": {
            "full_name": "Bloodborne Pathogens Training",
            "renewal_period_months": 12,
        },
        "Sharps_Safety": {
            "full_name": "Sharps Safety Training",
            "renewal_period_months": 12,
        },
    }

    cert_types_dict = {}
    for name, data in certs_data.items():
        cert_type = CertificationType(
            id=uuid4(),
            name=name,
            full_name=data["full_name"],
            renewal_period_months=data["renewal_period_months"],
            is_active=True,
        )
        db.add(cert_type)
        cert_types_dict[name] = cert_type

    db.commit()
    for cert_type in cert_types_dict.values():
        db.refresh(cert_type)

    return cert_types_dict


@pytest.fixture
def faculty_no_n95(db: Session, cert_types: dict) -> Person:
    """Create faculty with BLS and HIPAA but no N95."""
    faculty = Person(
        id=uuid4(),
        name="Dr. No N95",
        type="faculty",
        email="no.n95@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)

    # Add BLS and HIPAA certifications
    for cert_name in ["BLS", "HIPAA", "Cyber_Training", "AUP", "Chaperone"]:
        cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types[cert_name].id,
            issued_date=date.today() - timedelta(days=365),
            expiration_date=date.today() + timedelta(days=365),
            status="current",
        )
        db.add(cert)

    db.commit()
    return faculty


@pytest.fixture
def faculty_with_expiring_bls(db: Session, cert_types: dict) -> Person:
    """Create faculty with BLS expiring in 10 days."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Expiring BLS",
        type="faculty",
        email="expiring.bls@hospital.org",
        performs_procedures=True,
    )
    db.add(faculty)
    db.commit()
    db.refresh(faculty)

    # Add BLS expiring in 10 days
    bls_cert = PersonCertification(
        id=uuid4(),
        person_id=faculty.id,
        certification_type_id=cert_types["BLS"].id,
        issued_date=date.today() - timedelta(days=720),
        expiration_date=date.today() + timedelta(days=10),
        status="expiring_soon",
    )
    db.add(bls_cert)

    # Add HIPAA (not expiring)
    hipaa_cert = PersonCertification(
        id=uuid4(),
        person_id=faculty.id,
        certification_type_id=cert_types["HIPAA"].id,
        issued_date=date.today() - timedelta(days=180),
        expiration_date=date.today() + timedelta(days=185),
        status="current",
    )
    db.add(hipaa_cert)

    db.commit()
    return faculty


@pytest.fixture
def inpatient_call_rotation(db: Session) -> RotationTemplate:
    """Create inpatient call rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Inpatient Call",
        activity_type="inpatient_call",
        abbreviation="Call",
        max_residents=4,
        supervision_required=True,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


@pytest.fixture
def peds_clinic_rotation(db: Session) -> RotationTemplate:
    """Create pediatric clinic rotation template."""
    rotation = RotationTemplate(
        id=uuid4(),
        name="Pediatric Clinic",
        activity_type="peds_clinic",
        abbreviation="Peds",
        max_residents=4,
        supervision_required=True,
    )
    db.add(rotation)
    db.commit()
    db.refresh(rotation)
    return rotation


# ============================================================================
# Frame 7.1: Hard Credential Requirement Enforcement
# ============================================================================


class TestHardCredentialEnforcement:
    """Test hard credential requirements block ineligible assignments."""

    def test_hard_credential_requirement_n95_missing(
        self,
        db: Session,
        faculty_no_n95: Person,
        inpatient_call_rotation: RotationTemplate,
    ):
        """
        Test hard credential requirement blocks assignment.

        Frame 7.1: Inpatient call requires N95, faculty lacks it.
        """
        # SETUP
        assignment_date = date.today() + timedelta(days=7)

        # ACTION
        eligible, penalty, missing = is_eligible(
            faculty_no_n95, "inpatient_call", assignment_date, db
        )

        # ASSERT
        assert eligible is False, "Faculty without N95 should not be eligible"
        assert penalty == 0, "Hard constraint should have penalty=0 (blocking)"
        assert "N95_Fit" in missing, "N95_Fit should be in missing credentials"

    def test_hard_credential_requirement_all_present(
        self, db: Session, cert_types: dict, inpatient_call_rotation: RotationTemplate
    ):
        """Test faculty with all required credentials is eligible."""
        # SETUP
        faculty = Person(
            id=uuid4(),
            name="Dr. Fully Credentialed",
            type="faculty",
            email="fully.credentialed@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

        # Add all required certifications for inpatient call
        for cert_name in ["HIPAA", "Cyber_Training", "AUP", "Chaperone", "N95_Fit"]:
            cert = PersonCertification(
                id=uuid4(),
                person_id=faculty.id,
                certification_type_id=cert_types[cert_name].id,
                issued_date=date.today() - timedelta(days=180),
                expiration_date=date.today() + timedelta(days=185),
                status="current",
            )
            db.add(cert)
        db.commit()

        assignment_date = date.today() + timedelta(days=7)

        # ACTION
        eligible, penalty, missing = is_eligible(
            faculty, "inpatient_call", assignment_date, db
        )

        # ASSERT
        assert eligible is True, "Faculty with all credentials should be eligible"
        assert len(missing) == 0, "Should have no missing credentials"

    def test_hard_credential_expired_blocks_assignment(
        self, db: Session, cert_types: dict, inpatient_call_rotation: RotationTemplate
    ):
        """Test expired credential blocks assignment."""
        # SETUP
        faculty = Person(
            id=uuid4(),
            name="Dr. Expired N95",
            type="faculty",
            email="expired.n95@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

        # Add all certifications, but N95 is expired
        for cert_name in ["HIPAA", "Cyber_Training", "AUP", "Chaperone"]:
            cert = PersonCertification(
                id=uuid4(),
                person_id=faculty.id,
                certification_type_id=cert_types[cert_name].id,
                issued_date=date.today() - timedelta(days=180),
                expiration_date=date.today() + timedelta(days=185),
                status="current",
            )
            db.add(cert)

        # N95 expired yesterday
        n95_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types["N95_Fit"].id,
            issued_date=date.today() - timedelta(days=365),
            expiration_date=date.today() - timedelta(days=1),
            status="expired",
        )
        db.add(n95_cert)
        db.commit()

        assignment_date = date.today() + timedelta(days=7)

        # ACTION
        eligible, penalty, missing = is_eligible(
            faculty, "inpatient_call", assignment_date, db
        )

        # ASSERT
        assert eligible is False, "Expired credential should block assignment"
        assert any("N95_Fit" in m for m in missing), "Expired N95 should be in missing"


# ============================================================================
# Frame 7.2: Soft Credential Penalties
# ============================================================================


class TestSoftCredentialPenalties:
    """Test soft credential penalties accumulate correctly."""

    def test_soft_credential_penalty_expiring_soon(
        self,
        db: Session,
        faculty_with_expiring_bls: Person,
        peds_clinic_rotation: RotationTemplate,
    ):
        """
        Test soft credential penalty for expiring credentials.

        Frame 7.2: Faculty with BLS expiring in 10 days assigned to peds clinic
        with 14-day warning window should receive penalty=3.
        """
        # SETUP
        assignment_date = date.today() + timedelta(days=5)

        # ACTION
        eligible, penalty, missing = is_eligible(
            faculty_with_expiring_bls, "peds_clinic", assignment_date, db
        )

        # ASSERT
        assert eligible is True, "Should still be eligible (soft constraint)"
        assert penalty == 3, "Should have penalty=3 for expiring soon"
        assert len(missing) == 0, "Should have no hard missing credentials"

    def test_soft_credential_no_penalty_outside_window(
        self, db: Session, cert_types: dict, peds_clinic_rotation: RotationTemplate
    ):
        """Test no penalty when credential expires outside warning window."""
        # SETUP
        faculty = Person(
            id=uuid4(),
            name="Dr. BLS Expires Later",
            type="faculty",
            email="bls.later@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

        # BLS expires in 30 days (outside 14-day window)
        bls_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types["BLS"].id,
            issued_date=date.today() - timedelta(days=700),
            expiration_date=date.today() + timedelta(days=30),
            status="current",
        )
        db.add(bls_cert)

        # HIPAA (not expiring)
        hipaa_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types["HIPAA"].id,
            issued_date=date.today() - timedelta(days=180),
            expiration_date=date.today() + timedelta(days=185),
            status="current",
        )
        db.add(hipaa_cert)
        db.commit()

        assignment_date = date.today() + timedelta(days=5)

        # ACTION
        eligible, penalty, missing = is_eligible(
            faculty, "peds_clinic", assignment_date, db
        )

        # ASSERT
        assert eligible is True, "Should be eligible"
        assert penalty == 0, "Should have no penalty (expires outside 14-day window)"

    def test_soft_credential_penalty_multiple_slots(
        self, db: Session, cert_types: dict
    ):
        """Test penalties for procedures with larger warning window."""
        # SETUP
        faculty = Person(
            id=uuid4(),
            name="Dr. Procedure Faculty",
            type="faculty",
            email="procedure.fac@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

        # BLS expires in 20 days
        # Should trigger penalty for procedures_half_day (30-day window, penalty=5)
        bls_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types["BLS"].id,
            issued_date=date.today() - timedelta(days=710),
            expiration_date=date.today() + timedelta(days=20),
            status="expiring_soon",
        )
        db.add(bls_cert)

        # Add other required certs
        for cert_name in ["BBP_Module", "Sharps_Safety"]:
            cert = PersonCertification(
                id=uuid4(),
                person_id=faculty.id,
                certification_type_id=cert_types[cert_name].id,
                issued_date=date.today() - timedelta(days=180),
                expiration_date=date.today() + timedelta(days=185),
                status="current",
            )
            db.add(cert)
        db.commit()

        assignment_date = date.today() + timedelta(days=5)

        # ACTION
        eligible, penalty, missing = is_eligible(
            faculty, "procedures_half_day", assignment_date, db
        )

        # ASSERT
        assert eligible is True, "Should be eligible"
        assert penalty == 5, "Should have penalty=5 for procedures (30-day window)"


# ============================================================================
# Frame 7.3: Credential Renewal During Assignment
# ============================================================================


class TestCredentialRenewalDuringAssignment:
    """Test handling of credential renewal during active assignment."""

    def test_credential_renewal_removes_penalty(
        self,
        db: Session,
        faculty_with_expiring_bls: Person,
        peds_clinic_rotation: RotationTemplate,
        cert_types: dict,
    ):
        """
        Test credential renewal removes soft penalties.

        Frame 7.3: Faculty renews BLS mid-block, penalty should be removed.
        """
        # SETUP
        assignment_date = date.today() + timedelta(days=5)

        # Verify initial penalty
        eligible_before, penalty_before, _ = is_eligible(
            faculty_with_expiring_bls, "peds_clinic", assignment_date, db
        )
        assert penalty_before == 3, "Should have penalty before renewal"

        # ACTION: Faculty completes BLS renewal
        old_bls = (
            db.query(PersonCertification)
            .filter(
                PersonCertification.person_id == faculty_with_expiring_bls.id,
                PersonCertification.certification_type_id == cert_types["BLS"].id,
            )
            .first()
        )

        # Update expiration date to 2 years in future
        old_bls.expiration_date = date.today() + timedelta(days=730)
        old_bls.status = "current"
        db.commit()

        # ASSERT: Verify penalty removed
        eligible_after, penalty_after, missing_after = is_eligible(
            faculty_with_expiring_bls, "peds_clinic", assignment_date, db
        )

        assert eligible_after is True, "Should still be eligible"
        assert penalty_after == 0, "Penalty should be removed after renewal"
        assert len(missing_after) == 0, "Should have no missing credentials"

    def test_renewal_before_expiration_proactive(
        self, db: Session, cert_types: dict, peds_clinic_rotation: RotationTemplate
    ):
        """Test proactive renewal well before expiration."""
        # SETUP
        faculty = Person(
            id=uuid4(),
            name="Dr. Proactive Renewer",
            type="faculty",
            email="proactive@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

        # BLS expires in 60 days (proactively renewing)
        bls_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types["BLS"].id,
            issued_date=date.today() - timedelta(days=670),
            expiration_date=date.today() + timedelta(days=60),
            status="current",
        )
        db.add(bls_cert)

        hipaa_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types["HIPAA"].id,
            issued_date=date.today() - timedelta(days=180),
            expiration_date=date.today() + timedelta(days=185),
            status="current",
        )
        db.add(hipaa_cert)
        db.commit()

        # Renew BLS proactively
        bls_cert.expiration_date = date.today() + timedelta(days=730)
        db.commit()

        assignment_date = date.today() + timedelta(days=5)

        # ACTION
        eligible, penalty, missing = is_eligible(
            faculty, "peds_clinic", assignment_date, db
        )

        # ASSERT
        assert eligible is True
        assert penalty == 0, "Proactively renewed cert should have no penalty"


# ============================================================================
# Frame 7.4: Dashboard Hard Failure Prediction
# ============================================================================


class TestDashboardHardFailurePrediction:
    """Test dashboard prediction of hard credential failures."""

    def test_dashboard_hard_failure_prediction_next_block(
        self, db: Session, cert_types: dict
    ):
        """
        Test prediction of hard credential failures in next block.

        Frame 7.4: Identify faculty who will fail hard constraints in next block.
        """
        # SETUP
        # Create faculty with BLS expiring between blocks
        faculty = Person(
            id=uuid4(),
            name="Dr. BLS Expires Soon",
            type="faculty",
            email="bls.expires@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

        # Current block ends Jan 15, next block starts Jan 22
        # BLS expires Jan 20 (between blocks)
        current_block_end = date(2025, 1, 15)
        next_block_start = date(2025, 1, 22)
        bls_expiration = date(2025, 1, 20)

        bls_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types["BLS"].id,
            issued_date=date(2023, 1, 20),
            expiration_date=bls_expiration,
            status="current",
        )
        db.add(bls_cert)

        hipaa_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty.id,
            certification_type_id=cert_types["HIPAA"].id,
            issued_date=date(2024, 1, 1),
            expiration_date=date(2025, 6, 1),
            status="current",
        )
        db.add(hipaa_cert)
        db.commit()

        # Create blocks for next period
        block_11 = Block(
            id=uuid4(),
            date=next_block_start,
            time_of_day="AM",
            block_number=11,
            is_weekend=False,
        )
        db.add(block_11)
        db.commit()
        db.refresh(block_11)

        # Create peds clinic rotation requiring BLS
        peds_rotation = RotationTemplate(
            id=uuid4(),
            name="Pediatric Clinic",
            activity_type="peds_clinic",
            abbreviation="Peds",
            max_residents=4,
        )
        db.add(peds_rotation)
        db.commit()
        db.refresh(peds_rotation)

        # Create assignment in block 11 requiring BLS
        assignment = Assignment(
            id=uuid4(),
            block_id=block_11.id,
            person_id=faculty.id,
            rotation_template_id=peds_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

        # ACTION
        predictions = predict_next_block_failures(db, current_block_number=10)

        # ASSERT
        assert len(predictions) > 0, "Should have at least one prediction"

        faculty_prediction = next(
            (p for p in predictions if p["person_id"] == faculty.id), None
        )
        assert faculty_prediction is not None, "Faculty should be in predictions"
        assert any(
            "BLS" in cred for cred in faculty_prediction["failing_credentials"]
        ), "BLS should be in failing credentials"
        assert assignment.id in faculty_prediction["affected_assignments"], (
            "Assignment should be affected"
        )

    def test_dashboard_no_failures_when_all_valid(self, db: Session, cert_types: dict):
        """Test dashboard shows no failures when all credentials valid."""
        # SETUP
        faculty = Person(
            id=uuid4(),
            name="Dr. All Valid",
            type="faculty",
            email="all.valid@hospital.org",
            performs_procedures=True,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)

        # All certifications valid for next block
        next_block_start = date(2025, 1, 22)

        for cert_name in ["BLS", "HIPAA"]:
            cert = PersonCertification(
                id=uuid4(),
                person_id=faculty.id,
                certification_type_id=cert_types[cert_name].id,
                issued_date=date(2024, 1, 1),
                expiration_date=date(2025, 12, 31),  # Valid all year
                status="current",
            )
            db.add(cert)
        db.commit()

        # Create block and assignment
        block_11 = Block(
            id=uuid4(),
            date=next_block_start,
            time_of_day="AM",
            block_number=11,
            is_weekend=False,
        )
        db.add(block_11)
        db.commit()
        db.refresh(block_11)

        peds_rotation = RotationTemplate(
            id=uuid4(),
            name="Pediatric Clinic",
            activity_type="peds_clinic",
            abbreviation="Peds",
            max_residents=4,
        )
        db.add(peds_rotation)
        db.commit()
        db.refresh(peds_rotation)

        assignment = Assignment(
            id=uuid4(),
            block_id=block_11.id,
            person_id=faculty.id,
            rotation_template_id=peds_rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        # ACTION
        predictions = predict_next_block_failures(db, current_block_number=10)

        # ASSERT
        faculty_prediction = next(
            (p for p in predictions if p["person_id"] == faculty.id), None
        )
        assert faculty_prediction is None, (
            "Faculty with valid credentials should not be in predictions"
        )

    def test_dashboard_multiple_faculty_predictions(
        self, db: Session, cert_types: dict
    ):
        """Test dashboard handles multiple faculty with failures."""
        # SETUP
        next_block_start = date(2025, 1, 22)

        # Create multiple faculty with expiring credentials
        faculty_list = []
        for i in range(3):
            faculty = Person(
                id=uuid4(),
                name=f"Dr. Faculty {i}",
                type="faculty",
                email=f"faculty{i}@hospital.org",
                performs_procedures=True,
            )
            db.add(faculty)
            faculty_list.append(faculty)

        db.commit()
        for f in faculty_list:
            db.refresh(f)

        # Faculty 0: BLS expires before next block
        bls_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty_list[0].id,
            certification_type_id=cert_types["BLS"].id,
            issued_date=date(2023, 1, 20),
            expiration_date=date(2025, 1, 20),
            status="current",
        )
        db.add(bls_cert)

        # Faculty 1: HIPAA expires before next block
        hipaa_cert = PersonCertification(
            id=uuid4(),
            person_id=faculty_list[1].id,
            certification_type_id=cert_types["HIPAA"].id,
            issued_date=date(2024, 1, 18),
            expiration_date=date(2025, 1, 18),
            status="current",
        )
        db.add(hipaa_cert)

        # Faculty 2: All valid (control)
        for cert_name in ["BLS", "HIPAA"]:
            cert = PersonCertification(
                id=uuid4(),
                person_id=faculty_list[2].id,
                certification_type_id=cert_types[cert_name].id,
                issued_date=date(2024, 1, 1),
                expiration_date=date(2025, 12, 31),
                status="current",
            )
            db.add(cert)

        db.commit()

        # Create block
        block_11 = Block(
            id=uuid4(),
            date=next_block_start,
            time_of_day="AM",
            block_number=11,
            is_weekend=False,
        )
        db.add(block_11)
        db.commit()
        db.refresh(block_11)

        # Create rotation
        peds_rotation = RotationTemplate(
            id=uuid4(),
            name="Pediatric Clinic",
            activity_type="peds_clinic",
            abbreviation="Peds",
            max_residents=4,
        )
        db.add(peds_rotation)
        db.commit()
        db.refresh(peds_rotation)

        # Create assignments for all faculty
        for faculty in faculty_list:
            assignment = Assignment(
                id=uuid4(),
                block_id=block_11.id,
                person_id=faculty.id,
                rotation_template_id=peds_rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # ACTION
        predictions = predict_next_block_failures(db, current_block_number=10)

        # ASSERT
        assert len(predictions) == 2, "Should predict failures for 2 faculty"

        # Faculty 0 should have BLS failure
        fac0_pred = next(
            (p for p in predictions if p["person_id"] == faculty_list[0].id), None
        )
        assert fac0_pred is not None
        assert any("BLS" in c for c in fac0_pred["failing_credentials"])

        # Faculty 1 should have HIPAA failure
        fac1_pred = next(
            (p for p in predictions if p["person_id"] == faculty_list[1].id), None
        )
        assert fac1_pred is not None
        assert any("HIPAA" in c for c in fac1_pred["failing_credentials"])

        # Faculty 2 should not be in predictions
        fac2_pred = next(
            (p for p in predictions if p["person_id"] == faculty_list[2].id), None
        )
        assert fac2_pred is None, "Faculty with valid certs should not be predicted"
