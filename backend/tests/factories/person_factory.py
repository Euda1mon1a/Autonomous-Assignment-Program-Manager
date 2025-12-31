"""Factory for creating test Person instances (residents and faculty)."""

from typing import Optional
from uuid import uuid4

from faker import Faker
from sqlalchemy.orm import Session

from app.models.person import FacultyRole, Person, ScreenerRole

fake = Faker()


class PersonFactory:
    """Factory for creating Person instances with random data."""

    SPECIALTIES = [
        "Sports Medicine",
        "Primary Care",
        "Dermatology",
        "Musculoskeletal",
        "Pediatrics",
        "Women's Health",
        "Geriatrics",
        "Preventive Medicine",
    ]

    @staticmethod
    def create_resident(
        db: Session,
        name: Optional[str] = None,
        pgy_level: Optional[int] = None,
        email: Optional[str] = None,
        target_clinical_blocks: Optional[int] = None,
    ) -> Person:
        """
        Create a single resident.

        Args:
            db: Database session
            name: Resident name (random if not provided)
            pgy_level: PGY level 1-3 (random if not provided)
            email: Email address (generated from name if not provided)
            target_clinical_blocks: Expected clinical blocks (default based on PGY)

        Returns:
            Person: Created resident instance
        """
        if name is None:
            name = f"Dr. {fake.first_name()} {fake.last_name()}"

        if pgy_level is None:
            pgy_level = fake.random_int(min=1, max=3)

        if email is None:
            email = name.lower().replace("dr. ", "").replace(" ", ".") + "@resident.mil"

        if target_clinical_blocks is None:
            # Regular resident: ~48-56 blocks (12-14 weeks * 4 blocks/week)
            target_clinical_blocks = fake.random_int(min=48, max=56)

        resident = Person(
            id=uuid4(),
            name=name,
            type="resident",
            email=email,
            pgy_level=pgy_level,
            target_clinical_blocks=target_clinical_blocks,
        )
        db.add(resident)
        db.commit()
        db.refresh(resident)
        return resident

    @staticmethod
    def create_faculty(
        db: Session,
        name: Optional[str] = None,
        faculty_role: Optional[str] = None,
        performs_procedures: bool = False,
        specialties: Optional[list[str]] = None,
        email: Optional[str] = None,
    ) -> Person:
        """
        Create a single faculty member.

        Args:
            db: Database session
            name: Faculty name (random if not provided)
            faculty_role: FacultyRole enum value (random if not provided)
            performs_procedures: Whether faculty performs procedures
            specialties: List of specialties (random if not provided)
            email: Email address (generated from name if not provided)

        Returns:
            Person: Created faculty instance
        """
        if name is None:
            name = f"Dr. {fake.first_name()} {fake.last_name()}"

        if faculty_role is None:
            faculty_role = fake.random_element(
                [
                    FacultyRole.CORE.value,
                    FacultyRole.APD.value,
                    FacultyRole.OIC.value,
                    FacultyRole.SPORTS_MED.value,
                ]
            )

        if specialties is None:
            num_specialties = fake.random_int(min=1, max=3)
            specialties = fake.random_choices(
                PersonFactory.SPECIALTIES, length=num_specialties
            )

        if email is None:
            email = name.lower().replace("dr. ", "").replace(" ", ".") + "@faculty.mil"

        faculty = Person(
            id=uuid4(),
            name=name,
            type="faculty",
            email=email,
            performs_procedures=performs_procedures,
            specialties=specialties,
            faculty_role=faculty_role,
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return faculty

    @staticmethod
    def create_screener(
        db: Session,
        name: Optional[str] = None,
        screener_role: Optional[str] = None,
        screening_efficiency: Optional[int] = None,
    ) -> Person:
        """
        Create a screener (can be resident or dedicated staff).

        Args:
            db: Database session
            name: Screener name (random if not provided)
            screener_role: ScreenerRole enum value (random if not provided)
            screening_efficiency: Efficiency percentage 70-100 (role-based if not provided)

        Returns:
            Person: Created person with screener capabilities
        """
        if name is None:
            name = f"{fake.first_name()} {fake.last_name()}"

        if screener_role is None:
            screener_role = fake.random_element(
                [
                    ScreenerRole.DEDICATED.value,
                    ScreenerRole.RN.value,
                    ScreenerRole.EMT.value,
                ]
            )

        if screening_efficiency is None:
            # Role-based efficiency
            efficiency_map = {
                ScreenerRole.DEDICATED.value: 100,
                ScreenerRole.RN.value: 90,
                ScreenerRole.EMT.value: 80,
                ScreenerRole.RESIDENT.value: 70,
            }
            screening_efficiency = efficiency_map.get(screener_role, 100)

        person_type = (
            "resident" if screener_role == ScreenerRole.RESIDENT.value else "faculty"
        )
        email = name.lower().replace(" ", ".") + "@screener.mil"

        screener = Person(
            id=uuid4(),
            name=name,
            type=person_type,
            email=email,
            can_screen=True,
            screener_role=screener_role,
            screening_efficiency=screening_efficiency,
            pgy_level=2 if person_type == "resident" else None,
        )
        db.add(screener)
        db.commit()
        db.refresh(screener)
        return screener

    @staticmethod
    def create_program_director(db: Session, name: Optional[str] = None) -> Person:
        """Create a Program Director."""
        if name is None:
            name = f"Dr. {fake.first_name()} {fake.last_name()}"

        pd = Person(
            id=uuid4(),
            name=name,
            type="faculty",
            email=name.lower().replace("dr. ", "").replace(" ", ".") + "@pd.mil",
            faculty_role=FacultyRole.PD.value,
            specialties=["Program Leadership"],
        )
        db.add(pd)
        db.commit()
        db.refresh(pd)
        return pd

    @staticmethod
    def create_sports_medicine_faculty(
        db: Session, name: Optional[str] = None
    ) -> Person:
        """Create a Sports Medicine faculty member."""
        if name is None:
            name = f"Dr. {fake.first_name()} {fake.last_name()}"

        sm_faculty = Person(
            id=uuid4(),
            name=name,
            type="faculty",
            email=name.lower().replace("dr. ", "").replace(" ", ".") + "@sm.mil",
            faculty_role=FacultyRole.SPORTS_MED.value,
            specialties=["Sports Medicine"],
            performs_procedures=True,
        )
        db.add(sm_faculty)
        db.commit()
        db.refresh(sm_faculty)
        return sm_faculty

    @staticmethod
    def create_batch_residents(
        db: Session,
        count: int = 10,
        pgy_distribution: Optional[dict[int, int]] = None,
    ) -> list[Person]:
        """
        Create multiple residents with controlled PGY distribution.

        Args:
            db: Database session
            count: Total number of residents to create
            pgy_distribution: Dict mapping PGY level to count
                             Example: {1: 4, 2: 3, 3: 3} creates 4 PGY-1, 3 PGY-2, 3 PGY-3

        Returns:
            list[Person]: List of created residents
        """
        residents = []

        if pgy_distribution:
            for pgy_level, pgy_count in pgy_distribution.items():
                for _ in range(pgy_count):
                    resident = PersonFactory.create_resident(
                        db, pgy_level=pgy_level
                    )
                    residents.append(resident)
        else:
            # Even distribution across PGY levels
            for i in range(count):
                pgy_level = (i % 3) + 1  # Cycles 1, 2, 3, 1, 2, 3...
                resident = PersonFactory.create_resident(db, pgy_level=pgy_level)
                residents.append(resident)

        return residents

    @staticmethod
    def create_batch_faculty(
        db: Session,
        count: int = 5,
        include_leadership: bool = True,
    ) -> list[Person]:
        """
        Create multiple faculty members.

        Args:
            db: Database session
            count: Number of faculty to create
            include_leadership: If True, include PD, APD, OIC in the mix

        Returns:
            list[Person]: List of created faculty
        """
        faculty = []

        if include_leadership and count >= 3:
            # Create leadership first
            faculty.append(PersonFactory.create_program_director(db))
            faculty.append(
                PersonFactory.create_faculty(db, faculty_role=FacultyRole.APD.value)
            )
            faculty.append(
                PersonFactory.create_faculty(db, faculty_role=FacultyRole.OIC.value)
            )
            remaining = count - 3
        else:
            remaining = count

        # Create remaining faculty (mix of core and sports med)
        for i in range(remaining):
            if i % 4 == 0:
                # Every 4th is sports medicine
                faculty.append(PersonFactory.create_sports_medicine_faculty(db))
            else:
                faculty.append(
                    PersonFactory.create_faculty(
                        db,
                        faculty_role=FacultyRole.CORE.value,
                        performs_procedures=fake.boolean(chance_of_getting_true=30),
                    )
                )

        return faculty

    @staticmethod
    def create_chief_resident(
        db: Session, name: Optional[str] = None, pgy_level: int = 3
    ) -> Person:
        """
        Create a chief resident with reduced clinical load.

        Args:
            db: Database session
            name: Name (random if not provided)
            pgy_level: PGY level (default 3)

        Returns:
            Person: Chief resident instance
        """
        if name is None:
            name = f"Dr. {fake.first_name()} {fake.last_name()} (Chief)"

        chief = Person(
            id=uuid4(),
            name=name,
            type="resident",
            email=name.lower()
            .replace("dr. ", "")
            .replace(" (chief)", "")
            .replace(" ", ".")
            + "@chief.mil",
            pgy_level=pgy_level,
            target_clinical_blocks=24,  # 6 clinical + 6 admin weeks
        )
        db.add(chief)
        db.commit()
        db.refresh(chief)
        return chief

    @staticmethod
    def create_research_resident(
        db: Session, name: Optional[str] = None, pgy_level: int = 2
    ) -> Person:
        """
        Create a research track resident with minimal clinical load.

        Args:
            db: Database session
            name: Name (random if not provided)
            pgy_level: PGY level (default 2)

        Returns:
            Person: Research resident instance
        """
        if name is None:
            name = f"Dr. {fake.first_name()} {fake.last_name()} (Research)"

        research = Person(
            id=uuid4(),
            name=name,
            type="resident",
            email=name.lower()
            .replace("dr. ", "")
            .replace(" (research)", "")
            .replace(" ", ".")
            + "@research.mil",
            pgy_level=pgy_level,
            target_clinical_blocks=8,  # 2 clinical weeks only
        )
        db.add(research)
        db.commit()
        db.refresh(research)
        return research
