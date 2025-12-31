"""
Schedule Generator Profiler

Profiles the schedule generation engine to identify performance bottlenecks
in constraint evaluation, solver operations, and assignment logic.

Usage:
    python -m profiling.profile_scheduler
    python -m profiling.profile_scheduler --residents 100 --weeks 4
    python -m profiling.profile_scheduler --sort time
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.scheduling.engine import ScheduleGenerator
from profiling import ProfilerContext


def setup_test_data(db, num_residents: int = 50, num_weeks: int = 4):
    """Create test data for profiling."""
    template = RotationTemplate(
        id=uuid4(),
        name="Profile Template",
        activity_type="clinic",
        abbreviation="PT",
        max_residents=10,
        supervision_required=True,
    )
    db.add(template)

    residents = []
    for pgy in [1, 2, 3]:
        count = num_residents // 3
        for i in range(count):
            resident = Person(
                id=uuid4(),
                name=f"Profile Resident PGY{pgy}-{i + 1}",
                type="resident",
                email=f"prof.pgy{pgy}.r{i + 1}@test.org",
                pgy_level=pgy,
                target_clinical_blocks=48,
            )
            db.add(resident)
            residents.append(resident)

    blocks = []
    start_date = date.today()
    for day_offset in range(num_weeks * 7):
        current_date = start_date + timedelta(days=day_offset)
        for tod in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=tod,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
            )
            db.add(block)
            blocks.append(block)

    db.commit()

    return {
        "residents": residents,
        "blocks": blocks,
        "template": template,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=num_weeks * 7 - 1),
    }


def profile_schedule_generation(
    num_residents: int = 50,
    num_weeks: int = 4,
    sort_by: str = "cumulative",
):
    """Profile schedule generation."""
    print(f"\n{'=' * 80}")
    print("PROFILING SCHEDULE GENERATION")
    print(f"Residents: {num_residents}, Weeks: {num_weeks}")
    print(f"{'=' * 80}\n")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Setup
        test_data = setup_test_data(db, num_residents, num_weeks)

        # Profile
        profiler = ProfilerContext("schedule_generation")

        print("Starting profiler...")
        with profiler:
            generator = ScheduleGenerator(db)
            result = generator.generate_schedule(
                start_date=test_data["start_date"],
                end_date=test_data["end_date"],
                residents=test_data["residents"],
                blocks=test_data["blocks"],
            )

        print(f"Generation complete: {len(result.get('assignments', []))} assignments")

        # Print stats
        profiler.print_stats(sort_by=sort_by, limit=50)

        # Save stats
        output_dir = Path(__file__).parent.parent.parent / "profiling_results"
        profiler.save_stats(output_dir)

        # Highlight key functions
        print(f"\n{'=' * 80}")
        print("KEY FUNCTION ANALYSIS")
        print(f"{'=' * 80}\n")

        key_functions = [
            "generate_schedule",
            "evaluate_constraints",
            "solve",
            "assign_resident",
        ]

        for func_name in key_functions:
            stats = profiler.get_function_stats(func_name)
            if stats.get("output"):
                print(f"\n{func_name}:")
                print(stats["output"][:500])  # First 500 chars

    finally:
        # Cleanup
        db.query(Assignment).delete()
        db.query(Block).delete()
        db.query(Person).delete()
        db.query(RotationTemplate).delete()
        db.commit()
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Profile schedule generation")
    parser.add_argument("--residents", type=int, default=50, help="Number of residents")
    parser.add_argument("--weeks", type=int, default=4, help="Number of weeks")
    parser.add_argument(
        "--sort",
        type=str,
        default="cumulative",
        choices=["cumulative", "time", "calls"],
        help="Sort method",
    )

    args = parser.parse_args()

    profile_schedule_generation(
        num_residents=args.residents,
        num_weeks=args.weeks,
        sort_by=args.sort,
    )


if __name__ == "__main__":
    main()
