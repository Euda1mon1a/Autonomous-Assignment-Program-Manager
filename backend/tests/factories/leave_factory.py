"""Factory for creating test Absence (leave) instances."""

from datetime import date, timedelta
from typing import Optional
from uuid import uuid4

from faker import Faker
from sqlalchemy.orm import Session

from app.models.absence import ABSENCE_TYPES, Absence
from app.models.person import Person

fake = Faker()


class LeaveFactory:
    """Factory for creating Absence instances with random data."""

    @staticmethod
    def create_absence(
        db: Session,
        person: Person,
        start_date: date | None = None,
        end_date: date | None = None,
        absence_type: str = "vacation",
        is_blocking: bool | None = None,
        deployment_orders: bool = False,
        tdy_location: str | None = None,
        replacement_activity: str | None = None,
        notes: str | None = None,
        return_date_tentative: bool = False,
    ) -> Absence:
        """
        Create an absence record.

        Args:
            db: Database session
            person: Person who is absent
            start_date: Absence start date (7 days from now if not provided)
            end_date: Absence end date (calculated if not provided)
            absence_type: Type of absence (see ABSENCE_TYPES)
            is_blocking: Whether absence blocks assignment (auto-determined if None)
            deployment_orders: Military deployment flag
            tdy_location: TDY location (for military TDY)
            replacement_activity: Activity shown in schedule during absence
            notes: Additional notes
            return_date_tentative: Whether return date is uncertain

        Returns:
            Absence: Created absence instance
        """
        if start_date is None:
            start_date = date.today() + timedelta(days=7)

        if end_date is None:
            # Default duration based on type
            duration_days = {
                "vacation": 7,
                "deployment": 90,
                "tdy": 14,
                "medical": 3,
                "family_emergency": 5,
                "conference": 3,
                "bereavement": 5,
                "emergency_leave": 7,
                "sick": 2,
                "convalescent": 14,
                "maternity_paternity": 84,  # 12 weeks
            }
            days = duration_days.get(absence_type, 7)
            end_date = start_date + timedelta(days=days - 1)

        if absence_type not in ABSENCE_TYPES:
            raise ValueError(
                f"Invalid absence_type: {absence_type}. Must be one of {list(ABSENCE_TYPES.keys())}"
            )

        absence = Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=start_date,
            end_date=end_date,
            absence_type=absence_type,
            is_blocking=is_blocking,
            deployment_orders=deployment_orders,
            tdy_location=tdy_location,
            replacement_activity=replacement_activity,
            notes=notes,
            return_date_tentative=return_date_tentative,
        )
        db.add(absence)
        db.commit()
        db.refresh(absence)
        return absence

    @staticmethod
    def create_vacation(
        db: Session,
        person: Person,
        start_date: date | None = None,
        days: int = 7,
    ) -> Absence:
        """
        Create a vacation absence.

        Args:
            db: Database session
            person: Person taking vacation
            start_date: Start date (7 days from now if not provided)
            days: Duration in days (default 7)

        Returns:
            Absence: Vacation absence
        """
        if start_date is None:
            start_date = date.today() + timedelta(days=7)

        end_date = start_date + timedelta(days=days - 1)

        return LeaveFactory.create_absence(
            db,
            person=person,
            start_date=start_date,
            end_date=end_date,
            absence_type="vacation",
            is_blocking=False,
            notes="Scheduled vacation leave",
        )

    @staticmethod
    def create_deployment(
        db: Session,
        person: Person,
        start_date: date | None = None,
        days: int = 180,
        deployment_location: str = "Undisclosed",
    ) -> Absence:
        """
        Create a military deployment absence.

        Args:
            db: Database session
            person: Person being deployed
            start_date: Deployment start date
            days: Deployment duration (default 180 days / 6 months)
            deployment_location: Deployment location

        Returns:
            Absence: Deployment absence
        """
        if start_date is None:
            start_date = date.today() + timedelta(days=14)

        end_date = start_date + timedelta(days=days - 1)

        return LeaveFactory.create_absence(
            db,
            person=person,
            start_date=start_date,
            end_date=end_date,
            absence_type="deployment",
            is_blocking=True,
            deployment_orders=True,
            replacement_activity=f"DEPLOYMENT - {deployment_location}",
            notes=f"Military deployment to {deployment_location}",
        )

    @staticmethod
    def create_tdy(
        db: Session,
        person: Person,
        start_date: date | None = None,
        days: int = 14,
        location: str = "CONUS",
    ) -> Absence:
        """
        Create a TDY (Temporary Duty) absence.

        Args:
            db: Database session
            person: Person on TDY
            start_date: TDY start date
            days: TDY duration (default 14 days / 2 weeks)
            location: TDY location

        Returns:
            Absence: TDY absence
        """
        if start_date is None:
            start_date = date.today() + timedelta(days=21)

        end_date = start_date + timedelta(days=days - 1)

        return LeaveFactory.create_absence(
            db,
            person=person,
            start_date=start_date,
            end_date=end_date,
            absence_type="tdy",
            is_blocking=True,
            tdy_location=location,
            replacement_activity=f"TDY - {location}",
            notes=f"Temporary duty assignment to {location}",
        )

    @staticmethod
    def create_medical_leave(
        db: Session,
        person: Person,
        start_date: date | None = None,
        days: int = 10,
    ) -> Absence:
        """
        Create a medical leave absence.

        Args:
            db: Database session
            person: Person on medical leave
            start_date: Leave start date
            days: Duration (default 10 days, triggers blocking)

        Returns:
            Absence: Medical leave absence
        """
        if start_date is None:
            start_date = date.today() + timedelta(days=1)

        end_date = start_date + timedelta(days=days - 1)

        # Medical leave >7 days is blocking
        is_blocking = days > 7

        return LeaveFactory.create_absence(
            db,
            person=person,
            start_date=start_date,
            end_date=end_date,
            absence_type="medical",
            is_blocking=is_blocking,
            notes="Medical leave - recovery period",
        )

    @staticmethod
    def create_family_emergency(
        db: Session,
        person: Person,
        start_date: date | None = None,
        return_date_known: bool = False,
    ) -> Absence:
        """
        Create a family emergency absence.

        Args:
            db: Database session
            person: Person with family emergency
            start_date: Emergency start date (today if not provided)
            return_date_known: Whether return date is confirmed

        Returns:
            Absence: Family emergency absence
        """
        if start_date is None:
            start_date = date.today()

        # Default to 7 days but mark as tentative if return unknown
        end_date = start_date + timedelta(days=6)

        return LeaveFactory.create_absence(
            db,
            person=person,
            start_date=start_date,
            end_date=end_date,
            absence_type="family_emergency",
            is_blocking=True,
            return_date_tentative=not return_date_known,
            notes="Family emergency - travel required",
        )

    @staticmethod
    def create_conference(
        db: Session,
        person: Person,
        start_date: date | None = None,
        days: int = 3,
        conference_name: str | None = None,
    ) -> Absence:
        """
        Create a conference absence.

        Args:
            db: Database session
            person: Person attending conference
            start_date: Conference start date
            days: Conference duration (default 3 days)
            conference_name: Name of conference

        Returns:
            Absence: Conference absence
        """
        if start_date is None:
            start_date = date.today() + timedelta(days=30)

        end_date = start_date + timedelta(days=days - 1)

        if conference_name is None:
            conference_name = fake.catch_phrase() + " Conference"

        return LeaveFactory.create_absence(
            db,
            person=person,
            start_date=start_date,
            end_date=end_date,
            absence_type="conference",
            is_blocking=False,
            replacement_activity=f"CONF - {conference_name[:20]}",
            notes=f"Attending {conference_name}",
        )

    @staticmethod
    def create_maternity_paternity_leave(
        db: Session,
        person: Person,
        start_date: date | None = None,
        days: int = 84,
    ) -> Absence:
        """
        Create maternity/paternity leave (12 weeks standard).

        Args:
            db: Database session
            person: Person taking parental leave
            start_date: Leave start date
            days: Duration (default 84 days / 12 weeks)

        Returns:
            Absence: Maternity/paternity leave
        """
        if start_date is None:
            start_date = date.today() + timedelta(days=30)

        end_date = start_date + timedelta(days=days - 1)

        return LeaveFactory.create_absence(
            db,
            person=person,
            start_date=start_date,
            end_date=end_date,
            absence_type="maternity_paternity",
            is_blocking=True,
            notes="Parental leave (12 weeks)",
        )

    @staticmethod
    def create_overlapping_absences(
        db: Session,
        persons: list[Person],
        start_date: date | None = None,
        days: int = 7,
    ) -> list[Absence]:
        """
        Create overlapping absences for multiple people (coverage gap scenario).

        Args:
            db: Database session
            persons: List of persons to mark absent
            start_date: Start date for all absences
            days: Duration for all absences

        Returns:
            list[Absence]: List of overlapping absences
        """
        if start_date is None:
            start_date = date.today() + timedelta(days=14)

        absences = []
        for person in persons:
            absence = LeaveFactory.create_vacation(
                db, person=person, start_date=start_date, days=days
            )
            absences.append(absence)

        return absences

    @staticmethod
    def create_batch_absences(
        db: Session,
        persons: list[Person],
        absence_type: str | None = None,
        count_per_person: int = 1,
    ) -> list[Absence]:
        """
        Create multiple absences for multiple people.

        Args:
            db: Database session
            persons: List of persons
            absence_type: Type of absence (random if None)
            count_per_person: Number of absences per person

        Returns:
            list[Absence]: List of created absences
        """
        absences = []

        for person in persons:
            for i in range(count_per_person):
                selected_type = (
                    absence_type
                    if absence_type
                    else fake.random_element(list(ABSENCE_TYPES.keys()))
                )

                # Stagger start dates
                days_offset = 7 + (i * 14)
                start = date.today() + timedelta(days=days_offset)

                absence = LeaveFactory.create_absence(
                    db, person=person, start_date=start, absence_type=selected_type
                )
                absences.append(absence)

        return absences
