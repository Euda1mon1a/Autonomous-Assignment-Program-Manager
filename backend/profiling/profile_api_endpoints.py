"""
API Endpoint Profiler

Profiles FastAPI endpoint handlers to identify bottlenecks in request processing,
middleware overhead, and response generation.

Usage:
    python -m profiling.profile_api_endpoints
    python -m profiling.profile_api_endpoints --endpoint /api/schedule/generate
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from profiling import ProfilerContext, profile_function


@profile_function(sort_by="cumulative", limit=40)
def profile_schedule_endpoint():
    """Profile schedule generation endpoint logic."""
    from datetime import date, timedelta
    from uuid import uuid4

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.models.rotation_template import RotationTemplate
    from app.scheduling.engine import ScheduleGenerator

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Simulate endpoint logic
        template = RotationTemplate(
            id=uuid4(),
            name="API Profile",
            activity_type="clinic",
            abbreviation="AP",
        )
        db.add(template)

        residents = []
        for i in range(25):
            resident = Person(
                id=uuid4(),
                name=f"API Resident {i + 1}",
                type="resident",
                email=f"api.res{i + 1}@test.org",
                pgy_level=(i % 3) + 1,
            )
            db.add(resident)
            residents.append(resident)

        blocks = []
        start_date = date.today()
        for day in range(14):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=day),
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=False,
                )
                db.add(block)
                blocks.append(block)

        db.commit()

        # Profile schedule generation (main endpoint work)
        generator = ScheduleGenerator(db)
        result = generator.generate_schedule(
            start_date=start_date,
            end_date=start_date + timedelta(days=13),
            residents=residents,
            blocks=blocks,
        )

        return result

    finally:
        db.query(Assignment).delete()
        db.query(Block).delete()
        db.query(Person).delete()
        db.query(RotationTemplate).delete()
        db.commit()
        db.close()


@profile_function(sort_by="cumulative", limit=40)
def profile_validation_endpoint():
    """Profile ACGME validation endpoint logic."""
    from datetime import date, timedelta
    from uuid import uuid4

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.models.rotation_template import RotationTemplate
    from app.scheduling.validator import ACGMEValidator

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        template = RotationTemplate(
            id=uuid4(),
            name="Val API Profile",
            activity_type="clinic",
            abbreviation="VAP",
        )
        db.add(template)

        residents = []
        for i in range(50):
            resident = Person(
                id=uuid4(),
                name=f"Val API Resident {i + 1}",
                type="resident",
                email=f"val.api.res{i + 1}@test.org",
                pgy_level=(i % 3) + 1,
            )
            db.add(resident)
            residents.append(resident)

        blocks = []
        start_date = date.today()
        for day in range(28):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=day),
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=(start_date + timedelta(days=day)).weekday() >= 5,
                )
                db.add(block)
                blocks.append(block)

        db.commit()

        # Create assignments
        for resident in residents:
            for block in blocks:
                if block.date.weekday() != 6:
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=resident.id,
                        rotation_template_id=template.id,
                        role="primary",
                    )
                    db.add(assignment)
        db.commit()

        # Profile validation
        validator = ACGMEValidator(db)
        result = validator.validate_all(start_date, start_date + timedelta(days=27))

        return result

    finally:
        db.query(Assignment).delete()
        db.query(Block).delete()
        db.query(Person).delete()
        db.query(RotationTemplate).delete()
        db.commit()
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Profile API endpoints")
    parser.add_argument(
        "--endpoint",
        type=str,
        default="all",
        choices=["schedule", "validation", "all"],
        help="Endpoint to profile",
    )

    args = parser.parse_args()

    print(f"\n{'=' * 80}")
    print("API ENDPOINT PROFILING")
    print(f"{'=' * 80}\n")

    if args.endpoint in ["schedule", "all"]:
        print("\nProfiling Schedule Generation Endpoint...")
        profile_schedule_endpoint()
        print()

    if args.endpoint in ["validation", "all"]:
        print("\nProfiling ACGME Validation Endpoint...")
        profile_validation_endpoint()
        print()


if __name__ == "__main__":
    main()
