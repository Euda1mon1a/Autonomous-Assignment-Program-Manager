"""Factory for creating test certification instances."""

from datetime import date, timedelta
from typing import Optional
from uuid import uuid4

from faker import Faker
from sqlalchemy.orm import Session

from app.models.certification import CertificationType, PersonCertification
from app.models.person import Person

fake = Faker()


class CredentialFactory:
    """Factory for creating certification instances with random data."""

    STANDARD_CERTIFICATIONS = {
        "BLS": ("Basic Life Support", 24),
        "ACLS": ("Advanced Cardiovascular Life Support", 24),
        "PALS": ("Pediatric Advanced Life Support", 24),
        "NRP": ("Neonatal Resuscitation Program", 24),
        "ATLS": ("Advanced Trauma Life Support", 48),
        "ALSO": ("Advanced Life Support in Obstetrics", 60),
    }

    @staticmethod
    def create_certification_type(
        db: Session,
        name: str,
        full_name: str | None = None,
        renewal_period_months: int = 24,
        required_for_residents: bool = True,
        required_for_faculty: bool = True,
    ) -> CertificationType:
        """
        Create a certification type.

        Args:
            db: Database session
            name: Short name (e.g., "BLS")
            full_name: Full name (e.g., "Basic Life Support")
            renewal_period_months: Months until renewal (default 24)
            required_for_residents: Required for residents
            required_for_faculty: Required for faculty

        Returns:
            CertificationType: Created certification type
        """
        cert_type = CertificationType(
            id=uuid4(),
            name=name,
            full_name=full_name or name,
            renewal_period_months=renewal_period_months,
            required_for_residents=required_for_residents,
            required_for_faculty=required_for_faculty,
        )
        db.add(cert_type)
        db.commit()
        db.refresh(cert_type)
        return cert_type

    @staticmethod
    def create_person_certification(
        db: Session,
        person: Person,
        certification_type: CertificationType,
        issued_date: date | None = None,
        expiration_date: date | None = None,
        status: str = "current",
        certification_number: str | None = None,
    ) -> PersonCertification:
        """
        Create a person certification.

        Args:
            db: Database session
            person: Person who has the certification
            certification_type: Type of certification
            issued_date: Date issued (90 days ago if not provided)
            expiration_date: Expiration date (calculated from issued_date if not provided)
            status: Certification status ("current", "expiring_soon", "expired", "pending")
            certification_number: Certificate number

        Returns:
            PersonCertification: Created person certification
        """
        if issued_date is None:
            issued_date = date.today() - timedelta(days=90)

        if expiration_date is None:
            expiration_date = issued_date + timedelta(
                days=certification_type.renewal_period_months * 30
            )

        if certification_number is None:
            certification_number = fake.bothify(
                text="???-######", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            )

        person_cert = PersonCertification(
            id=uuid4(),
            person_id=person.id,
            certification_type_id=certification_type.id,
            issued_date=issued_date,
            expiration_date=expiration_date,
            status=status,
            certification_number=certification_number,
        )
        db.add(person_cert)
        db.commit()
        db.refresh(person_cert)
        return person_cert

    @staticmethod
    def create_current_certification(
        db: Session,
        person: Person,
        certification_type: CertificationType,
    ) -> PersonCertification:
        """
        Create a current (valid, not expiring soon) certification.

        Args:
            db: Database session
            person: Person who has the certification
            certification_type: Type of certification

        Returns:
            PersonCertification: Current certification (expires in ~18 months)
        """
        issued_date = date.today() - timedelta(days=180)  # 6 months ago
        expiration_date = issued_date + timedelta(
            days=certification_type.renewal_period_months * 30
        )

        return CredentialFactory.create_person_certification(
            db,
            person=person,
            certification_type=certification_type,
            issued_date=issued_date,
            expiration_date=expiration_date,
            status="current",
        )

    @staticmethod
    def create_expiring_soon_certification(
        db: Session,
        person: Person,
        certification_type: CertificationType,
        days_until_expiration: int = 30,
    ) -> PersonCertification:
        """
        Create an expiring soon certification.

        Args:
            db: Database session
            person: Person who has the certification
            certification_type: Type of certification
            days_until_expiration: Days until expiration (default 30)

        Returns:
            PersonCertification: Expiring soon certification
        """
        expiration_date = date.today() + timedelta(days=days_until_expiration)
        issued_date = expiration_date - timedelta(
            days=certification_type.renewal_period_months * 30
        )

        return CredentialFactory.create_person_certification(
            db,
            person=person,
            certification_type=certification_type,
            issued_date=issued_date,
            expiration_date=expiration_date,
            status="expiring_soon",
        )

    @staticmethod
    def create_expired_certification(
        db: Session,
        person: Person,
        certification_type: CertificationType,
        days_expired: int = 7,
    ) -> PersonCertification:
        """
        Create an expired certification.

        Args:
            db: Database session
            person: Person who has the certification
            certification_type: Type of certification
            days_expired: Days since expiration (default 7)

        Returns:
            PersonCertification: Expired certification
        """
        expiration_date = date.today() - timedelta(days=days_expired)
        issued_date = expiration_date - timedelta(
            days=certification_type.renewal_period_months * 30
        )

        return CredentialFactory.create_person_certification(
            db,
            person=person,
            certification_type=certification_type,
            issued_date=issued_date,
            expiration_date=expiration_date,
            status="expired",
        )

    @staticmethod
    def create_standard_certification_types(
        db: Session,
    ) -> dict[str, CertificationType]:
        """
        Create all standard certification types (BLS, ACLS, PALS, etc.).

        Args:
            db: Database session

        Returns:
            dict[str, CertificationType]: Dictionary of name -> certification type
        """
        cert_types = {}

        for name, (
            full_name,
            renewal_months,
        ) in CredentialFactory.STANDARD_CERTIFICATIONS.items():
            cert_type = CredentialFactory.create_certification_type(
                db,
                name=name,
                full_name=full_name,
                renewal_period_months=renewal_months,
            )
            cert_types[name] = cert_type

        return cert_types

    @staticmethod
    def certify_person_all_standard(
        db: Session,
        person: Person,
        certification_types: dict[str, CertificationType] | None = None,
    ) -> list[PersonCertification]:
        """
        Certify a person in all standard certifications (BLS, ACLS, PALS, NRP).

        Args:
            db: Database session
            person: Person to certify
            certification_types: Pre-created certification types (creates if None)

        Returns:
            list[PersonCertification]: List of person certifications
        """
        if certification_types is None:
            certification_types = CredentialFactory.create_standard_certification_types(
                db
            )

        certifications = []
        for cert_type in certification_types.values():
            cert = CredentialFactory.create_current_certification(
                db, person=person, certification_type=cert_type
            )
            certifications.append(cert)

        return certifications

    @staticmethod
    def create_mixed_status_certifications(
        db: Session,
        person: Person,
        certification_types: dict[str, CertificationType] | None = None,
    ) -> dict[str, PersonCertification]:
        """
        Create certifications with mixed statuses for testing.

        Creates:
        - BLS: current
        - ACLS: expiring in 30 days
        - PALS: expiring in 7 days
        - NRP: expired 5 days ago

        Args:
            db: Database session
            person: Person to certify
            certification_types: Pre-created certification types (creates if None)

        Returns:
            dict[str, PersonCertification]: Dictionary of certification name -> person cert
        """
        if certification_types is None:
            certification_types = CredentialFactory.create_standard_certification_types(
                db
            )

        certifications = {}

        # BLS: current
        certifications["BLS"] = CredentialFactory.create_current_certification(
            db, person=person, certification_type=certification_types["BLS"]
        )

        # ACLS: expiring in 30 days
        certifications["ACLS"] = CredentialFactory.create_expiring_soon_certification(
            db,
            person=person,
            certification_type=certification_types["ACLS"],
            days_until_expiration=30,
        )

        # PALS: expiring in 7 days
        certifications["PALS"] = CredentialFactory.create_expiring_soon_certification(
            db,
            person=person,
            certification_type=certification_types["PALS"],
            days_until_expiration=7,
        )

        # NRP: expired 5 days ago
        certifications["NRP"] = CredentialFactory.create_expired_certification(
            db,
            person=person,
            certification_type=certification_types["NRP"],
            days_expired=5,
        )

        return certifications

    @staticmethod
    def create_batch_certifications(
        db: Session,
        persons: list[Person],
        certification_type: CertificationType,
        status_distribution: dict[str, float] | None = None,
    ) -> list[PersonCertification]:
        """
        Create certifications for multiple people with status distribution.

        Args:
            db: Database session
            persons: List of persons to certify
            certification_type: Type of certification
            status_distribution: Distribution of statuses (default: 70% current, 20% expiring, 10% expired)

        Returns:
            list[PersonCertification]: List of created certifications
        """
        if status_distribution is None:
            status_distribution = {
                "current": 0.7,
                "expiring_soon": 0.2,
                "expired": 0.1,
            }

        certifications = []
        for person in persons:
            status_choice = fake.random.choices(
                list(status_distribution.keys()),
                weights=list(status_distribution.values()),
                k=1,
            )[0]

            if status_choice == "current":
                cert = CredentialFactory.create_current_certification(
                    db, person=person, certification_type=certification_type
                )
            elif status_choice == "expiring_soon":
                cert = CredentialFactory.create_expiring_soon_certification(
                    db, person=person, certification_type=certification_type
                )
            else:  # expired
                cert = CredentialFactory.create_expired_certification(
                    db, person=person, certification_type=certification_type
                )

            certifications.append(cert)

        return certifications
