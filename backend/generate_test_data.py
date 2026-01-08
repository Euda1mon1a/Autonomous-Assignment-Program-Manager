#!/usr/bin/env python3
"""
Test data generation script.

Generates realistic test data for development and testing:
- People (residents, faculty, staff)
- Rotation templates
- Assignments
- Absences
- Swap requests

Usage:
    python scripts/dev/generate_test_data.py --preset small
    python scripts/dev/generate_test_data.py --residents 18 --faculty 10
    python scripts/dev/generate_test_data.py --academic-year 2025 --with-assignments
"""

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.block import Block, Session
from app.models.person import FacultyRole, Person
from app.models.rotation import RotationTemplate


FIRST_NAMES = [
    "John", "Jane", "Michael", "Emily", "David", "Sarah",
    "Robert", "Jennifer", "William", "Jessica", "James", "Ashley",
    "Christopher", "Amanda", "Daniel", "Melissa", "Matthew", "Stephanie",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson",
]


def generate_people(
    db,
    num_residents: int = 18,
    num_faculty: int = 10,
) -> tuple[List[Person], List[Person]]:
    """Generate test people."""
    print(f"\nGenerating {num_residents} residents and {num_faculty} faculty...")

    residents = []
    faculty = []

    # Generate residents (6 per PGY level)
    for pgy in [1, 2, 3]:
        for i in range(num_residents // 3):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            person = Person(
                email=f"pgy{pgy}_{i+1:02d}@residency.test",
                first_name=first_name,
                last_name=last_name,
                role="RESIDENT",
                pgy_level=pgy,
                is_active=True,
            )
            db.add(person)
            residents.append(person)

    # Generate faculty with various roles
    faculty_roles = [
        FacultyRole.PD,
        FacultyRole.APD,
        FacultyRole.OIC,
        FacultyRole.DEPT_CHIEF,
    ] + [FacultyRole.CORE] * (num_faculty - 4)

    for i, role in enumerate(faculty_roles[:num_faculty]):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        person = Person(
            email=f"faculty_{role.value}_{i+1:02d}@residency.test",
            first_name=first_name,
            last_name=last_name,
            role="FACULTY",
            faculty_role=role.value,
            is_active=True,
        )
        db.add(person)
        faculty.append(person)

    db.commit()

    print(f"  ✓ Created {len(residents)} residents")
    print(f"  ✓ Created {len(faculty)} faculty")

    return residents, faculty


def generate_rotations(db) -> List[RotationTemplate]:
    """Generate rotation templates."""
    print("\nGenerating rotation templates...")

    rotations_data = [
        {"name": "Clinic", "duration_blocks": 1, "description": "Outpatient clinic"},
        {"name": "Inpatient", "duration_blocks": 1, "description": "Inpatient ward"},
        {"name": "Procedures", "duration_blocks": 1, "description": "Procedures clinic"},
        {"name": "Conference", "duration_blocks": 1, "description": "Educational conference"},
        {"name": "Night Float", "duration_blocks": 4, "description": "Night shift coverage"},
        {"name": "FMIT", "duration_blocks": 1, "description": "Faculty member in training"},
        {"name": "Call", "duration_blocks": 1, "description": "On-call duty"},
        {"name": "Vacation", "duration_blocks": 4, "description": "Scheduled time off"},
    ]

    rotations = []

    for data in rotations_data:
        rotation = RotationTemplate(**data)
        db.add(rotation)
        rotations.append(rotation)

    db.commit()

    print(f"  ✓ Created {len(rotations)} rotation templates")

    return rotations


def generate_blocks(db, academic_year: int) -> List[Block]:
    """Generate blocks for academic year."""
    from app.models.block import Session

    print(f"\nGenerating blocks for academic year {academic_year}-{academic_year + 1}...")

    start_date = date(academic_year, 7, 1)
    end_date = date(academic_year + 1, 6, 30)

    blocks = []
    current_date = start_date
    block_number = 1

    while current_date <= end_date:
        # Create AM and PM blocks
        for session in [Session.AM, Session.PM]:
            block = Block(
                date=current_date,
                session=session,
                block_number=block_number,
                is_weekend=current_date.weekday() >= 5,
            )
            db.add(block)
            blocks.append(block)

        current_date += timedelta(days=1)

        # Increment block number every 28 days
        if (current_date - start_date).days % 28 == 0:
            block_number += 1

    db.commit()

    print(f"  ✓ Created {len(blocks)} blocks")

    return blocks


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test data generation script"
    )
    parser.add_argument(
        "--preset",
        choices=["small", "medium", "large"],
        help="Use preset configuration (small=18/10, medium=30/15, large=50/20)",
    )
    parser.add_argument(
        "--residents",
        type=int,
        default=18,
        help="Number of residents (default: 18)",
    )
    parser.add_argument(
        "--faculty",
        type=int,
        default=10,
        help="Number of faculty (default: 10)",
    )
    parser.add_argument(
        "--academic-year",
        type=int,
        default=2025,
        help="Academic year (default: 2025 for 2025-2026)",
    )
    parser.add_argument(
        "--with-assignments",
        action="store_true",
        help="Generate sample assignments (experimental)",
    )
    parser.add_argument(
        "--clear-first",
        action="store_true",
        help="Clear existing test data first",
    )

    args = parser.parse_args()

    try:
        # Apply preset
        if args.preset == "small":
            args.residents = 18
            args.faculty = 10
        elif args.preset == "medium":
            args.residents = 30
            args.faculty = 15
        elif args.preset == "large":
            args.residents = 50
            args.faculty = 20

        print("=" * 60)
        print("Test Data Generation")
        print("=" * 60)
        print(f"\nConfiguration:")
        print(f"  Residents: {args.residents}")
        print(f"  Faculty: {args.faculty}")
        print(f"  Academic Year: {args.academic_year}-{args.academic_year + 1}")

        db = SessionLocal()

        try:
            # Clear existing data if requested
            if args.clear_first:
                print("\nClearing existing test data...")
                # This would need proper implementation to avoid foreign key issues
                print("  ⚠ Clear functionality not yet implemented")

            # Generate data
            residents, faculty = generate_people(db, args.residents, args.faculty)
            rotations = generate_rotations(db)
            blocks = generate_blocks(db, args.academic_year)

            if args.with_assignments:
                print("\n⚠ Assignment generation not yet implemented")

            print("\n" + "=" * 60)
            print("✓ Test data generation complete!")
            print("\nSummary:")
            print(f"  Residents: {len(residents)}")
            print(f"  Faculty: {len(faculty)}")
            print(f"  Rotations: {len(rotations)}")
            print(f"  Blocks: {len(blocks)}")
            print("=" * 60)

            return 0

        finally:
            db.close()

    except KeyboardInterrupt:
        print("\nAborted by user")
        return 130

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
