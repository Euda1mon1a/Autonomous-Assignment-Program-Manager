#!/usr/bin/env python
"""Antigravity GUI Testing Seed Data.

Seeds a complete Academic Year with all user types, residents, faculty,
blocks, rotation templates, assignments, and absences for comprehensive
GUI testing.

Usage:
    python -m scripts.seed_antigravity [--clear] [--year YEAR]

Options:
    --clear     Clear existing data before seeding
    --year      Academic year start year (default: 2025, creates AY 2025-2026)

Academic Year: July 1 - June 30 (730 blocks: 365 days x AM/PM)
"""

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

# Add backend to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from faker import Faker
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.import_staging import (
    ImportBatch,
    ImportBatchStatus,
    ImportStagedAssignment,
    StagedAssignmentStatus,
)
from app.models.person import FacultyRole, Person
from app.models.rotation_template import RotationTemplate
from app.models.user import User
from app.utils.academic_blocks import get_block_number_for_date

fake = Faker()
Faker.seed(42)  # Reproducible fake data
random.seed(42)


class AntigravitySeed:
    """Complete Academic Year seed for GUI testing."""

    # Default password for all test users
    DEFAULT_PASSWORD = "admin123"

    # User definitions: (username, email, role, full_name)
    USER_DEFINITIONS = [
        ("admin", "admin@test.mil", "admin", "System Administrator"),
        (
            "coordinator",
            "coordinator@test.mil",
            "coordinator",
            "Scheduling Coordinator",
        ),
        ("faculty_pd", "pd@test.mil", "faculty", "Program Director"),
        ("faculty_apd", "apd@test.mil", "faculty", "Associate Program Director"),
        ("faculty_core", "core@test.mil", "faculty", "Core Faculty Member"),
        ("resident_pgy1", "pgy1@test.mil", "resident", "PGY-1 Resident"),
        ("resident_pgy2", "pgy2@test.mil", "resident", "PGY-2 Resident"),
        ("resident_pgy3", "pgy3@test.mil", "resident", "PGY-3 Resident"),
        ("clinical_staff", "clinical@test.mil", "clinical_staff", "Clinical Staff"),
        ("rn_user", "rn@test.mil", "rn", "Registered Nurse"),
        ("lpn_user", "lpn@test.mil", "lpn", "Licensed Practical Nurse"),
        ("msa_user", "msa@test.mil", "msa", "Medical Support Assistant"),
    ]

    # Rotation template definitions
    ROTATION_TEMPLATES = [
        # (name, activity_type, abbrev, display_abbrev, max_residents, supervision_req, leave_eligible, font_color, bg_color)
        (
            "Inpatient",
            "inpatient",
            "INP",
            "INP",
            None,
            True,
            False,
            "text-white",
            "bg-red-600",
        ),
        (
            "Outpatient Clinic",
            "outpatient",
            "OPC",
            "C",
            4,
            True,
            True,
            "text-white",
            "bg-blue-600",
        ),
        (
            "Night Float",
            "inpatient",
            "NF",
            "NF",
            2,
            True,
            False,
            "text-white",
            "bg-purple-700",
        ),
        (
            "Call",
            "inpatient",
            "CALL",
            "CALL",
            1,
            True,
            False,
            "text-white",
            "bg-orange-600",
        ),
        (
            "FMIT",
            "inpatient",
            "FMIT",
            "FMIT",
            None,
            True,
            False,
            "text-white",
            "bg-red-700",
        ),
        (
            "Sports Medicine",
            "outpatient",
            "SM",
            "SM",
            3,
            True,
            True,
            "text-white",
            "bg-green-600",
        ),
        (
            "Procedures",
            "procedure",
            "PROC",
            "PROC",
            2,
            True,
            True,
            "text-white",
            "bg-teal-600",
        ),
        (
            "Conference",
            "conference",
            "CONF",
            "CONF",
            None,
            False,
            False,
            "text-gray-800",
            "bg-yellow-300",
        ),
        (
            "Annual Leave",
            "absence",
            "AL",
            "AL",
            None,
            False,
            True,
            "text-gray-600",
            "bg-gray-200",
        ),
        (
            "Sick Leave",
            "absence",
            "SL",
            "SL",
            None,
            False,
            True,
            "text-gray-600",
            "bg-gray-300",
        ),
        (
            "TDY",
            "absence",
            "TDY",
            "TDY",
            None,
            False,
            True,
            "text-white",
            "bg-gray-700",
        ),
        (
            "Deployment",
            "absence",
            "DEP",
            "DEP",
            None,
            False,
            True,
            "text-white",
            "bg-gray-800",
        ),
        (
            "Recovery",
            "recovery",
            "REC",
            "REC",
            None,
            False,
            True,
            "text-gray-600",
            "bg-blue-100",
        ),
        ("Off", "off", "OFF", "OFF", None, False, True, "text-gray-500", "bg-white"),
        # Post-call templates for faculty
        (
            "Post-Call AM",
            "recovery",
            "PCAT",
            "PCAT",
            None,
            False,
            True,
            "text-gray-800",
            "bg-yellow-200",
        ),
        (
            "Day Off",
            "off",
            "DO",
            "DO",
            None,
            False,
            True,
            "text-gray-600",
            "bg-gray-200",
        ),
    ]

    # Federal holidays (month, day, name)
    FEDERAL_HOLIDAYS = [
        (1, 1, "New Year's Day"),
        (7, 4, "Independence Day"),
        (11, 11, "Veterans Day"),
        (12, 25, "Christmas Day"),
    ]

    def __init__(self, db: Session, year: int = 2025):
        """Initialize seeder.

        Args:
            db: Database session
            year: Academic year start year (e.g., 2025 for AY 2025-2026)
        """
        self.db = db
        self.year = year
        self.ay_start = date(year, 7, 1)  # July 1
        self.ay_end = date(year + 1, 6, 30)  # June 30 next year

        # Track created entities count
        self.created = {
            "users": 0,
            "residents": 0,
            "faculty": 0,
            "blocks": 0,
            "templates": {},  # name -> RotationTemplate (used during run)
            "assignments": 0,
            "absences": 0,
            "call_assignments": 0,
            "import_batches": 0,
        }

        # Temporary lists for referencing during the run
        self._users_list = []
        self._residents_list = []
        self._faculty_list = []
        self._blocks_list = []
        self._import_batches_list = []

        # Track assigned (block_id, person_id) pairs to prevent duplicates
        self._assigned_pairs: set[tuple] = set()

    def seed_all(self) -> dict:
        """Seed complete academic year.

        Returns:
            dict: Summary of created entities
        """
        print(f"Seeding Academic Year {self.year}-{self.year + 1}...")
        print(f"  Date range: {self.ay_start} to {self.ay_end}")
        print()

        self._seed_users()
        self._seed_people()
        self._seed_rotation_templates()
        self._seed_blocks()
        self._seed_assignments()
        self._seed_absences()
        self._seed_call_assignments()  # Resident call (kept for reference)
        self._seed_faculty_call_assignments()  # Faculty call
        self._seed_import_history()

        self.db.commit()

        return self._summary()

    def clear_existing(self) -> int:
        """Clear existing seeded data.

        Returns:
            int: Number of records deleted
        """
        count = 0
        print("Clearing existing data...")

        # Delete in order to respect foreign key constraints
        # Import staging first (references people/rotations)
        count += self.db.query(ImportStagedAssignment).delete()
        print("  Deleted import staged assignments")

        count += self.db.query(ImportBatch).delete()
        print("  Deleted import batches")

        count += self.db.query(CallAssignment).delete()
        print("  Deleted call assignments")

        count += self.db.query(Assignment).delete()
        print(f"  Deleted {self.db.query(Assignment).count()} assignments")

        count += self.db.query(Absence).delete()
        print(f"  Deleted {self.db.query(Absence).count()} absences")

        count += self.db.query(Block).delete()
        print(f"  Deleted {self.db.query(Block).count()} blocks")

        count += (
            self.db.query(RotationTemplate)
            .filter(RotationTemplate.is_archived == False)  # noqa: E712
            .delete(synchronize_session="fetch")
        )
        print("  Deleted rotation templates")

        count += self.db.query(Person).delete()
        print(f"  Deleted {self.db.query(Person).count()} people")

        count += self.db.query(User).delete()
        print(f"  Deleted {self.db.query(User).count()} users")

        self.db.commit()
        print(f"  Total deleted: {count}")
        print()
        return count

    def _seed_users(self) -> None:
        """Create all 12 test users with 8 RBAC roles."""
        print("Creating users...")

        hashed_password = get_password_hash(self.DEFAULT_PASSWORD)

        for username, email, role, full_name in self.USER_DEFINITIONS:
            # Check if user already exists
            existing = self.db.query(User).filter(User.username == username).first()
            if existing:
                print(f"  User '{username}' already exists, skipping...")
                self.created["users"].append(existing)
                continue

            user = User(
                id=uuid4(),
                username=username,
                email=email,
                hashed_password=hashed_password,
                role=role,
                is_active=True,
            )
            self.db.add(user)
            self._users_list.append(user)
            self.created["users"] += 1
            print(f"  Created: {username} ({role})")

        self.db.flush()
        print(f"  Total users: {self.created['users']}")
        print()

    def _seed_people(self) -> None:
        """Create 45 residents (15 per PGY) and 10 faculty."""
        print("Creating people...")

        # Create residents: 15 per PGY level
        for pgy_level in [1, 2, 3]:
            for i in range(15):
                first_name = fake.first_name()
                last_name = fake.last_name()
                name = f"Dr. {first_name} {last_name}"
                email = f"{first_name.lower()}.{last_name.lower()}.pgy{pgy_level}@resident.mil"

                # Vary clinical block targets
                target_blocks = random.randint(48, 56)

                resident = Person(
                    id=uuid4(),
                    name=name,
                    type="resident",
                    email=email,
                    pgy_level=pgy_level,
                    target_clinical_blocks=target_blocks,
                )
                self.db.add(resident)
                self._residents_list.append(resident)
                self.created["residents"] += 1

            print(f"  Created 15 PGY-{pgy_level} residents")

        # Create faculty with specific roles
        faculty_configs = [
            (FacultyRole.PD.value, "Program Director", ["Program Leadership"]),
            (
                FacultyRole.APD.value,
                "Associate Program Director",
                ["Education", "Curriculum"],
            ),
            (FacultyRole.OIC.value, "Officer in Charge", ["Operations"]),
            (
                FacultyRole.DEPT_CHIEF.value,
                "Department Chief",
                ["Leadership", "Administration"],
            ),
            (
                FacultyRole.SPORTS_MED.value,
                "Sports Medicine Faculty",
                ["Sports Medicine"],
            ),
            (
                FacultyRole.SPORTS_MED.value,
                "Sports Medicine Faculty 2",
                ["Sports Medicine"],
            ),
            (
                FacultyRole.CORE.value,
                "Core Faculty 1",
                ["Primary Care", "Preventive Medicine"],
            ),
            (
                FacultyRole.CORE.value,
                "Core Faculty 2",
                ["Women's Health", "Pediatrics"],
            ),
            (FacultyRole.CORE.value, "Core Faculty 3", ["Geriatrics", "Primary Care"]),
            (
                FacultyRole.CORE.value,
                "Core Faculty 4",
                ["Musculoskeletal", "Dermatology"],
            ),
        ]

        for faculty_role, title, specialties in faculty_configs:
            first_name = fake.first_name()
            last_name = fake.last_name()
            name = f"Dr. {first_name} {last_name}"
            email = f"{first_name.lower()}.{last_name.lower()}@faculty.mil"

            performs_procedures = faculty_role in [
                FacultyRole.SPORTS_MED.value,
                FacultyRole.CORE.value,
            ]

            faculty = Person(
                id=uuid4(),
                name=name,
                type="faculty",
                email=email,
                faculty_role=faculty_role,
                specialties=specialties,
                performs_procedures=performs_procedures,
                primary_duty=title,
            )
            self.db.add(faculty)
            self._faculty_list.append(faculty)
            self.created["faculty"] += 1

        print(f"  Created {self.created['faculty']} faculty members")
        self.db.flush()
        print(f"  Total people: {self.created['residents'] + self.created['faculty']}")
        print()

    def _seed_rotation_templates(self) -> None:
        """Create rotation templates."""
        print("Creating rotation templates...")

        for config in self.ROTATION_TEMPLATES:
            (
                name,
                activity_type,
                abbreviation,
                display_abbrev,
                max_residents,
                supervision_req,
                leave_eligible,
                font_color,
                bg_color,
            ) = config

            # Check if template already exists
            existing = (
                self.db.query(RotationTemplate)
                .filter(RotationTemplate.name == name)
                .first()
            )
            if existing:
                self.created["templates"][name] = existing
                continue

            template = RotationTemplate(
                id=uuid4(),
                name=name,
                activity_type=activity_type,
                abbreviation=abbreviation,
                display_abbreviation=display_abbrev,
                max_residents=max_residents,
                supervision_required=supervision_req,
                leave_eligible=leave_eligible,
                font_color=font_color,
                background_color=bg_color,
                is_archived=False,
            )
            self.db.add(template)
            self.created["templates"][name] = template
            print(f"  Created: {name} ({activity_type})")

        self.db.flush()
        print(f"  Total templates: {len(self.created['templates'])}")
        print()

    def _seed_blocks(self) -> None:
        """Create 730 blocks for full academic year."""
        print("Creating blocks for academic year...")

        current_date = self.ay_start
        block_count = 0

        # Pre-compute holidays for both years
        holidays = set()
        for month, day, _ in self.FEDERAL_HOLIDAYS:
            holidays.add((self.year, month, day))
            holidays.add((self.year + 1, month, day))

        while current_date <= self.ay_end:
            block_number = self._calculate_block_number(current_date)
            is_weekend = current_date.weekday() >= 5
            is_holiday = (
                current_date.year,
                current_date.month,
                current_date.day,
            ) in holidays
            holiday_name = None

            if is_holiday:
                for month, day, name in self.FEDERAL_HOLIDAYS:
                    if current_date.month == month and current_date.day == day:
                        holiday_name = name
                        break

            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=block_number,
                    is_weekend=is_weekend,
                    is_holiday=is_holiday,
                    holiday_name=holiday_name,
                )
                self.db.add(block)
                self._blocks_list.append(block)
                self.created["blocks"] += 1
                block_count += 1

            current_date += timedelta(days=1)

        self.db.flush()
        print(f"  Created {block_count} blocks ({block_count // 2} days)")
        print()

    def _seed_assignments(self) -> None:
        """Generate realistic assignments for the academic year."""
        print("Creating assignments...")

        # Group blocks by week for assignment patterns
        blocks_by_week = {}
        for block in self._blocks_list:
            week_num = (block.date - self.ay_start).days // 7
            if week_num not in blocks_by_week:
                blocks_by_week[week_num] = []
            blocks_by_week[week_num].append(block)

        # Get templates
        clinic_template = self.created["templates"].get("Outpatient Clinic")
        fmit_template = self.created["templates"].get("FMIT")
        nf_template = self.created["templates"].get("Night Float")
        conf_template = self.created["templates"].get("Conference")
        sm_template = self.created["templates"].get("Sports Medicine")
        proc_template = self.created["templates"].get("Procedures")

        residents = self._residents_list
        faculty = self._faculty_list

        # Assign each resident to rotations across the year
        assignment_count = 0
        week_count = len(blocks_by_week)

        for week_num, blocks in blocks_by_week.items():
            # Get weekday blocks only
            weekday_blocks = [
                b for b in blocks if not b.is_weekend and not b.is_holiday
            ]

            # Assign residents based on rotation pattern
            for i, resident in enumerate(residents):
                # Rotate through different activities based on week and resident index
                activity_cycle = (week_num + i) % 13  # 13-block academic year

                if activity_cycle < 2:  # FMIT weeks
                    template = fmit_template
                elif activity_cycle == 2:  # Night Float week
                    template = nf_template
                elif activity_cycle in [3, 4, 5, 6]:  # Clinic weeks
                    template = clinic_template
                elif activity_cycle == 7:  # Procedures
                    template = proc_template
                elif activity_cycle == 8:  # Sports Med (if PGY-2/3)
                    template = (
                        sm_template if resident.pgy_level >= 2 else clinic_template
                    )
                else:  # More clinic
                    template = clinic_template

                # Assign to weekday blocks (AM sessions for clinic, both for inpatient)
                for block in weekday_blocks:
                    if template and template.activity_type == "outpatient":
                        # Clinic only AM
                        if block.time_of_day == "AM":
                            self._create_assignment(
                                resident, block, template, "primary"
                            )
                            assignment_count += 1
                    elif template:
                        # Inpatient rotations - both AM and PM
                        self._create_assignment(resident, block, template, "primary")
                        assignment_count += 1

            # Assign supervising faculty
            if clinic_template and weekday_blocks:
                supervising_faculty = random.choice(faculty)
                for block in weekday_blocks[:2]:  # Sample supervision
                    if block.time_of_day == "AM":
                        self._create_assignment(
                            supervising_faculty, block, clinic_template, "supervising"
                        )
                        assignment_count += 1

            # Progress indicator
            if week_num % 10 == 0:
                print(f"  Week {week_num}/{week_count} processed...")

        # Add conference assignments (Friday AM for all)
        if conf_template:
            friday_am_blocks = [
                b
                for b in self._blocks_list
                if b.date.weekday() == 4 and b.time_of_day == "AM" and not b.is_holiday
            ]
            for block in friday_am_blocks[:20]:  # First 20 Fridays
                for resident in residents[:10]:  # Sample residents
                    self._create_assignment(resident, block, conf_template, "primary")
                    assignment_count += 1

        self.db.flush()
        self.created["assignments"] = assignment_count
        print(f"  Created {assignment_count} assignments")
        print()

    def _create_assignment(
        self,
        person: Person,
        block: Block,
        template: RotationTemplate,
        role: str,
    ) -> Assignment | None:
        """Create a single assignment, checking for duplicates.

        Args:
            person: Person to assign
            block: Block to assign to
            template: Rotation template
            role: Assignment role

        Returns:
            Assignment or None if duplicate
        """
        # Check in-memory tracking first (faster than DB query)
        pair_key = (block.id, person.id)
        if pair_key in self._assigned_pairs:
            return None

        # Mark as assigned
        self._assigned_pairs.add(pair_key)

        assignment = Assignment(
            id=uuid4(),
            person_id=person.id,
            block_id=block.id,
            rotation_template_id=template.id,
            role=role,
            created_by="antigravity_seed",
            confidence=random.uniform(0.8, 1.0),
            score=random.uniform(0.7, 1.0),
        )
        self.db.add(assignment)
        return assignment

    def _seed_absences(self) -> None:
        """Create realistic absences (5-10% of residents)."""
        print("Creating absences...")

        residents = self._residents_list
        num_with_absences = int(len(residents) * 0.08)  # ~8%

        absence_types_weights = [
            ("vacation", 40),
            ("tdy", 20),
            ("conference", 15),
            ("medical", 10),
            ("sick", 10),
            ("deployment", 3),
            ("family_emergency", 2),
        ]

        selected_residents = random.sample(residents, num_with_absences)
        absence_count = 0

        for resident in selected_residents:
            # Each selected resident gets 1-3 absences
            num_absences = random.randint(1, 3)

            for _ in range(num_absences):
                # Select absence type weighted
                absence_type = random.choices(
                    [t[0] for t in absence_types_weights],
                    weights=[t[1] for t in absence_types_weights],
                )[0]

                # Random start within AY
                days_offset = random.randint(0, 300)
                start_date = self.ay_start + timedelta(days=days_offset)

                # Duration based on type
                duration_map = {
                    "vacation": random.randint(3, 14),
                    "tdy": random.randint(7, 21),
                    "conference": random.randint(2, 5),
                    "medical": random.randint(1, 10),
                    "sick": random.randint(1, 5),
                    "deployment": random.randint(30, 180),
                    "family_emergency": random.randint(3, 10),
                }
                duration = duration_map.get(absence_type, 7)
                end_date = start_date + timedelta(days=duration - 1)

                # Ensure end date is within AY
                if end_date > self.ay_end:
                    end_date = self.ay_end

                is_blocking = absence_type in ["deployment", "tdy", "family_emergency"]

                absence = Absence(
                    id=uuid4(),
                    person_id=resident.id,
                    start_date=start_date,
                    end_date=end_date,
                    absence_type=absence_type,
                    is_blocking=is_blocking,
                    deployment_orders=absence_type == "deployment",
                    tdy_location="CONUS" if absence_type == "tdy" else None,
                    notes=f"Seeded {absence_type} absence",
                )
                self.db.add(absence)
                absence_count += 1

        self.db.flush()
        self.created["absences"] = absence_count
        print(f"  Created {absence_count} absences for {num_with_absences} residents")
        print()

    def _seed_call_assignments(self) -> None:
        """Create call assignments for residents.

        NOTE: Resident call is separate from faculty call and uses Night Float
        rotation assignments rather than call_assignments table. Skipping for now
        to focus on faculty call workflow.
        """
        print("Skipping resident call assignments (using Night Float rotation instead)")
        print()

    def _seed_faculty_call_assignments(self) -> None:
        """Create faculty call assignments (sunday, weekday, holiday, backup)."""
        print("Creating faculty call assignments...")

        faculty = self._faculty_list
        if not faculty:
            print("  No faculty found, skipping...")
            return

        call_count = 0

        # Generate faculty call schedule for 6 months of the AY
        current_date = self.ay_start
        end_call_date = self.ay_start + timedelta(days=180)  # First 6 months

        # Pre-compute holidays
        holidays = set()
        for month, day, _ in self.FEDERAL_HOLIDAYS:
            holidays.add((self.year, month, day))
            holidays.add((self.year + 1, month, day))

        while current_date < end_call_date:
            day_of_week = current_date.weekday()  # 0=Mon, 6=Sun
            is_holiday = (
                current_date.year,
                current_date.month,
                current_date.day,
            ) in holidays

            day_index = (current_date - self.ay_start).days

            # Sunday call (day_of_week == 6)
            if day_of_week == 6:
                assigned = faculty[day_index % len(faculty)]
                call = CallAssignment(
                    id=uuid4(),
                    date=current_date,
                    person_id=assigned.id,
                    call_type="sunday",
                    is_weekend=True,
                    is_holiday=is_holiday,
                )
                self.db.add(call)
                call_count += 1

            # Weekday call (Mon-Thu, day_of_week 0-3)
            elif day_of_week in (0, 1, 2, 3) and not is_holiday:
                assigned = faculty[day_index % len(faculty)]
                call = CallAssignment(
                    id=uuid4(),
                    date=current_date,
                    person_id=assigned.id,
                    call_type="weekday",
                    is_weekend=False,
                    is_holiday=False,
                )
                self.db.add(call)
                call_count += 1

            # Holiday call
            if is_holiday:
                assigned = faculty[(day_index + 1) % len(faculty)]
                call = CallAssignment(
                    id=uuid4(),
                    date=current_date,
                    person_id=assigned.id,
                    call_type="holiday",
                    is_weekend=day_of_week >= 5,
                    is_holiday=True,
                )
                self.db.add(call)
                call_count += 1

            # Backup call (Fridays and Saturdays)
            if day_of_week in (4, 5):  # Friday, Saturday
                assigned = faculty[(day_index + 2) % len(faculty)]
                call = CallAssignment(
                    id=uuid4(),
                    date=current_date,
                    person_id=assigned.id,
                    call_type="backup",
                    is_weekend=day_of_week == 5,
                    is_holiday=is_holiday,
                )
                self.db.add(call)
                call_count += 1

            current_date += timedelta(days=1)

        self.db.flush()
        self.created["call_assignments"] = call_count
        print(f"  Created {call_count} faculty call assignments")
        print()

    def _seed_import_history(self) -> None:
        """Create import batch history with various statuses for GUI testing."""
        print("Creating import history...")

        # Get a user for created_by
        admin_user = next((u for u in self._users_list if u.role == "admin"), None)
        coord_user = next(
            (u for u in self._users_list if u.role == "coordinator"), None
        )

        batch_configs = [
            # (filename, status, days_ago, row_count, error_count, notes)
            (
                "Block_10_Schedule_2025.xlsx",
                "applied",
                30,
                245,
                0,
                "Block 10 initial schedule import",
            ),
            (
                "Block_11_Draft_v1.xlsx",
                "applied",
                21,
                238,
                2,
                "Block 11 first draft - 2 conflicts resolved",
            ),
            (
                "Block_11_Final.xlsx",
                "applied",
                14,
                240,
                0,
                "Block 11 final schedule",
            ),
            (
                "Block_12_Preliminary.xlsx",
                "staged",
                3,
                242,
                5,
                "Block 12 preliminary - needs review",
            ),
            (
                "Vacation_Requests_Jan.xlsx",
                "applied",
                7,
                15,
                0,
                "January vacation requests",
            ),
            (
                "TDY_Updates.xlsx",
                "rejected",
                5,
                8,
                3,
                "Rejected - duplicate entries",
            ),
            (
                "Block_12_Revised.xlsx",
                "staged",
                1,
                244,
                1,
                "Block 12 revised draft",
            ),
        ]

        for filename, status_str, days_ago, rows, errors, notes in batch_configs:
            created_at = date.today() - timedelta(days=days_ago)
            created_by = admin_user if days_ago > 20 else coord_user

            batch_id = uuid4()
            # Use raw SQL to bypass SQLAlchemy enum name/value mismatch
            from sqlalchemy import text

            self.db.execute(
                text(
                    """
                    INSERT INTO import_batches
                    (id, created_at, filename, status, created_by_id, row_count, error_count,
                     warning_count, notes, target_block, conflict_resolution, rollback_available)
                    VALUES
                    (:id, :created_at, :filename, CAST(:status AS importbatchstatus), :created_by_id, :row_count,
                     :error_count, :warning_count, :notes, :target_block, 'upsert', true)
                """
                ),
                {
                    "id": str(batch_id),
                    "created_at": created_at,
                    "filename": filename,
                    "status": status_str,
                    "created_by_id": str(created_by.id) if created_by else None,
                    "row_count": rows,
                    "error_count": errors,
                    "warning_count": random.randint(0, 3),
                    "notes": notes,
                    "target_block": (10 + (30 - days_ago) // 14),
                },
            )
            self.created["import_batches"] += 1

            # Add staged assignments for STAGED batches
            if status_str == "staged":
                residents_sample = random.sample(
                    self._residents_list, min(10, len(self._residents_list))
                )
                templates_list = list(self.created["templates"].values())

                for i, resident in enumerate(residents_sample):
                    template = random.choice(templates_list) if templates_list else None
                    # Use raw SQL to bypass enum issues
                    self.db.execute(
                        text(
                            """
                            INSERT INTO import_staged_assignments
                            (id, batch_id, row_number, sheet_name, person_name,
                             assignment_date, slot, rotation_name, matched_person_id,
                             person_match_confidence, matched_rotation_id,
                             rotation_match_confidence, status)
                            VALUES
                            (:id, :batch_id, :row_number, :sheet_name, :person_name,
                             :assignment_date, :slot, :rotation_name, :matched_person_id,
                             :person_match_confidence, :matched_rotation_id,
                             :rotation_match_confidence, CAST(:status AS stagedassignmentstatus))
                        """
                        ),
                        {
                            "id": str(uuid4()),
                            "batch_id": str(batch_id),
                            "row_number": i + 2,
                            "sheet_name": "Schedule",
                            "person_name": resident.name,
                            "assignment_date": date.today() + timedelta(days=i),
                            "slot": "AM" if i % 2 == 0 else "PM",
                            "rotation_name": template.name if template else "Clinic",
                            "matched_person_id": str(resident.id),
                            "person_match_confidence": 95,
                            "matched_rotation_id": (
                                str(template.id) if template else None
                            ),
                            "rotation_match_confidence": 90 if template else 0,
                            "status": "pending",
                        },
                    )

        self.db.flush()
        print(f"  Created {self.created['import_batches']} import batches")
        print()

    def _calculate_block_number(self, block_date: date) -> int:
        """Calculate academic year block number (0-13) for a given date.

        Uses Thursday-Wednesday aligned blocks:
        - Block 0: July 1 through day before first Thursday (orientation)
        - Blocks 1-12: 28 days each, Thursday start, Wednesday end
        - Block 13: Starts Thursday, ends June 30 (variable length)

        Args:
            block_date: Date to calculate block number for

        Returns:
            Block number (0-13)
        """
        block_number, _ = get_block_number_for_date(block_date)
        return block_number

    def _summary(self) -> dict:
        """Generate summary of created entities.

        Returns:
            dict: Summary statistics
        """
        summary = {
            "users": self.created["users"],
            "residents": self.created["residents"],
            "faculty": self.created["faculty"],
            "blocks": self.created["blocks"],
            "rotation_templates": len(self.created["templates"]),
            "assignments": self.created["assignments"],
            "absences": self.created["absences"],
            "call_assignments": self.created["call_assignments"],
            "import_batches": self.created["import_batches"],
            "academic_year": f"{self.year}-{self.year + 1}",
            "date_range": f"{self.ay_start} to {self.ay_end}",
        }

        print("=" * 60)
        print("SEED SUMMARY")
        print("=" * 60)
        print(f"  Academic Year: {summary['academic_year']}")
        print(f"  Date Range: {summary['date_range']}")
        print()
        print(f"  Users Created: {summary['users']}")
        print(f"  Residents Created: {summary['residents']}")
        print(f"  Faculty Created: {summary['faculty']}")
        print(f"  Blocks Created: {summary['blocks']}")
        print(f"  Rotation Templates: {summary['rotation_templates']}")
        print(f"  Assignments Created: {summary['assignments']}")
        print(f"  Absences Created: {summary['absences']}")
        print(f"  Call Assignments Created: {summary['call_assignments']}")
        print(f"  Import Batches Created: {summary['import_batches']}")
        print("=" * 60)
        print()
        print("Test Credentials:")
        print(f"  Password for all users: {self.DEFAULT_PASSWORD}")
        print()
        print("User Accounts:")
        for username, email, role, _ in self.USER_DEFINITIONS:
            print(f"  - {username} ({role}): {email}")
        print()

        return summary


def main():
    """CLI interface for Antigravity seed."""
    parser = argparse.ArgumentParser(
        description="Seed complete Academic Year for Antigravity GUI testing"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before seeding",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=2025,
        help="Academic year start year (default: 2025 for AY 2025-2026)",
    )

    args = parser.parse_args()

    print()
    print("=" * 60)
    print("ANTIGRAVITY GUI TESTING SEED")
    print("=" * 60)
    print()

    db = SessionLocal()

    try:
        seeder = AntigravitySeed(db, year=args.year)

        if args.clear:
            seeder.clear_existing()

        result = seeder.seed_all()

        print("Seed completed successfully!")
        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
