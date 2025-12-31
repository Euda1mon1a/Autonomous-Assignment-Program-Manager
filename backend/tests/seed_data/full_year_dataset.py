"""Full academic year seed dataset for integration testing."""

from datetime import date

from sqlalchemy.orm import Session

from tests.factories.credential_factory import CredentialFactory
from tests.factories.leave_factory import LeaveFactory
from tests.factories.schedule_factory import ScheduleFactory
from tests.factories.swap_factory import SwapFactory


class FullYearDataset:
    """
    Full academic year dataset for comprehensive integration tests.

    Includes:
    - 10 residents (mixed PGY levels)
    - 5 faculty (including leadership)
    - Full academic year of blocks (730 blocks)
    - 8 rotation templates
    - Certifications
    - Absences throughout the year
    - Swap requests
    """

    @staticmethod
    def seed(db: Session, year: int | None = None) -> dict:
        """
        Seed database with full academic year dataset.

        Args:
            db: Database session
            year: Academic year starting year (current year if None)

        Returns:
            dict: Dictionary with all seeded entities
        """
        if year is None:
            year = date.today().year

        ***REMOVED*** Create academic year skeleton (people, blocks, templates)
        skeleton = ScheduleFactory.create_academic_year_skeleton(
            db, year=year, num_residents=10, num_faculty=5
        )

        ***REMOVED*** Add certifications for all residents
        cert_types = CredentialFactory.create_standard_certification_types(db)
        all_certifications = []

        for resident in skeleton["residents"]:
            ***REMOVED*** Some residents have all current certs, some have mixed status
            if skeleton["residents"].index(resident) % 2 == 0:
                certs = CredentialFactory.certify_person_all_standard(
                    db, person=resident, certification_types=cert_types
                )
            else:
                certs = CredentialFactory.create_mixed_status_certifications(
                    db, person=resident, certification_types=cert_types
                )
            all_certifications.extend(
                list(certs.values()) if isinstance(certs, dict) else certs
            )

        ***REMOVED*** Add absences throughout the year
        absences = LeaveFactory.create_batch_absences(
            db, persons=skeleton["residents"], count_per_person=2
        )

        ***REMOVED*** Add faculty swaps
        swaps = SwapFactory.create_batch_swaps(
            db, faculty=skeleton["faculty"], num_swaps=10
        )

        return {
            "residents": skeleton["residents"],
            "faculty": skeleton["faculty"],
            "blocks": skeleton["blocks"],
            "templates": skeleton["templates"],
            "year": skeleton["year"],
            "certification_types": cert_types,
            "certifications": all_certifications,
            "absences": absences,
            "swaps": swaps,
            "dataset_type": "full_year",
            "total_blocks": len(skeleton["blocks"]),
            "total_residents": len(skeleton["residents"]),
            "total_faculty": len(skeleton["faculty"]),
        }

    @staticmethod
    def seed_with_assignments(
        db: Session, year: int | None = None, num_days: int = 28
    ) -> dict:
        """
        Seed database with full year data PLUS assignments for first block.

        Full year assignments would be too large for typical tests,
        so this creates assignments only for the first 28 days.

        Args:
            db: Database session
            year: Academic year starting year
            num_days: Number of days to create assignments for (default 28)

        Returns:
            dict: Dictionary with all seeded entities
        """
        ***REMOVED*** Get full year skeleton
        data = FullYearDataset.seed(db, year=year)

        ***REMOVED*** Create assignments for first N days only
        from tests.factories.assignment_factory import AssignmentFactory

        first_blocks = data["blocks"][: num_days * 2]  ***REMOVED*** 2 blocks per day
        clinic_template = data["templates"]["pgy1_clinic"]

        assignments = []
        for resident in data["residents"]:
            ***REMOVED*** Assign each resident to 1 week of the first 28 days
            week_index = data["residents"].index(resident) % (num_days // 7)
            week_start = week_index * 14  ***REMOVED*** 14 blocks per week
            week_blocks = first_blocks[week_start : week_start + 14]

            week_assignments = AssignmentFactory.create_week_assignments(
                db,
                person=resident,
                blocks=week_blocks,
                rotation_template=clinic_template,
            )
            assignments.extend(week_assignments)

        data["assignments"] = assignments
        data["assigned_blocks"] = first_blocks
        return data

    @staticmethod
    def seed_realistic_program(db: Session, year: int | None = None) -> dict:
        """
        Seed realistic residency program with proper PGY distribution.

        Creates:
        - 12 residents (4 per PGY level)
        - 6 faculty (PD, APD, OIC, 2 core, 1 sports med)
        - Full year blocks
        - Standard rotation templates
        - Realistic certification statuses
        - Realistic absence patterns

        Args:
            db: Database session
            year: Academic year starting year

        Returns:
            dict: Dictionary with all seeded entities
        """
        from tests.factories.person_factory import PersonFactory
        from tests.factories.block_factory import BlockFactory
        from tests.factories.rotation_factory import RotationFactory

        if year is None:
            year = date.today().year

        ***REMOVED*** Create residents with proper PGY distribution
        residents = PersonFactory.create_batch_residents(
            db, count=12, pgy_distribution={1: 4, 2: 4, 3: 4}
        )

        ***REMOVED*** Create realistic faculty mix
        faculty = []
        faculty.append(PersonFactory.create_program_director(db))  ***REMOVED*** PD
        faculty.append(PersonFactory.create_faculty(db, faculty_role="apd"))  ***REMOVED*** APD
        faculty.append(PersonFactory.create_faculty(db, faculty_role="oic"))  ***REMOVED*** OIC
        faculty.append(PersonFactory.create_sports_medicine_faculty(db))  ***REMOVED*** SM
        faculty.append(PersonFactory.create_faculty(db, faculty_role="core"))  ***REMOVED*** Core 1
        faculty.append(PersonFactory.create_faculty(db, faculty_role="core"))  ***REMOVED*** Core 2

        ***REMOVED*** Create full year blocks
        blocks = BlockFactory.create_academic_year_blocks(db, year=year)

        ***REMOVED*** Create rotation templates
        templates = RotationFactory.create_standard_template_set(db)

        ***REMOVED*** Create certifications with realistic mix
        cert_types = CredentialFactory.create_standard_certification_types(db)
        all_certifications = []

        for resident in residents:
            ***REMOVED*** 60% current, 30% expiring soon, 10% expired
            certs = CredentialFactory.create_batch_certifications(
                db,
                persons=[resident],
                certification_type=cert_types["BLS"],
                status_distribution={
                    "current": 0.6,
                    "expiring_soon": 0.3,
                    "expired": 0.1,
                },
            )
            all_certifications.extend(certs)

        ***REMOVED*** Create realistic absences (vacation, conference, occasional emergency)
        absences = []
        for resident in residents:
            ***REMOVED*** 1-2 vacations per year
            vacation = LeaveFactory.create_vacation(db, person=resident)
            absences.append(vacation)

            ***REMOVED*** Some attend conferences
            if residents.index(resident) % 3 == 0:
                conference = LeaveFactory.create_conference(db, person=resident)
                absences.append(conference)

        ***REMOVED*** Faculty swaps
        swaps = SwapFactory.create_batch_swaps(
            db, faculty=faculty, num_swaps=15, swap_type=None
        )

        return {
            "residents": residents,
            "faculty": faculty,
            "blocks": blocks,
            "templates": templates,
            "year": year,
            "certification_types": cert_types,
            "certifications": all_certifications,
            "absences": absences,
            "swaps": swaps,
            "dataset_type": "realistic_program",
            "program_size": "small",  ***REMOVED*** 12 residents = small program
        }
