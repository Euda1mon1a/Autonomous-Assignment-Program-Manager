"""
Background Task Profiler

Profiles Celery background tasks to identify bottlenecks in asynchronous processing.

Usage:
    python -m profiling.profile_background_tasks
    python -m profiling.profile_background_tasks --task resilience_check
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from profiling import ProfilerContext, profile_function


@profile_function(sort_by="cumulative", limit=40)
def profile_resilience_task():
    """Profile resilience health check task."""
    from datetime import date, timedelta
    from uuid import uuid4

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.models.rotation_template import RotationTemplate
    from app.resilience.contingency import N1ContingencyAnalyzer

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Simulate background task setup
        template = RotationTemplate(
            id=uuid4(),
            name="Resilience Task Profile",
            activity_type="clinic",
            abbreviation="RTP",
        )
        db.add(template)

        people = []
        for i in range(30):
            person = Person(
                id=uuid4(),
                name=f"Res Task Person {i + 1}",
                type="resident" if i % 2 == 0 else "faculty",
                email=f"res.task{i + 1}@test.org",
                pgy_level=(i % 3) + 1 if i % 2 == 0 else None,
            )
            db.add(person)
            people.append(person)

        blocks = []
        start_date = date.today()
        for day in range(28):
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

        # Create assignments
        for block in blocks:
            assigned = int(len(people) * 0.7)
            for i in range(assigned):
                person = people[i % len(people)]
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=person.id,
                    rotation_template_id=template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Profile N-1 analysis (typical background task)
        analyzer = N1ContingencyAnalyzer(db)
        result = analyzer.analyze(
            start_date=start_date,
            end_date=start_date + timedelta(days=27),
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
def profile_notification_task():
    """Profile notification sending task."""
    # Simulated notification task
    print("Profiling notification task logic...")

    import time

    # Simulate email template rendering
    def render_template(template_name: str, context: dict) -> str:
        """Simulate template rendering."""
        time.sleep(0.001)  # Simulate I/O
        return f"{template_name}: {context}"

    # Simulate batch notifications
    notifications = []
    for i in range(100):
        context = {
            "user_name": f"User {i + 1}",
            "message": f"Notification message {i + 1}",
            "timestamp": time.time(),
        }
        rendered = render_template("notification.html", context)
        notifications.append(rendered)

    return notifications


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Profile background tasks")
    parser.add_argument(
        "--task",
        type=str,
        default="all",
        choices=["resilience", "notification", "all"],
        help="Task type to profile",
    )

    args = parser.parse_args()

    print(f"\n{'=' * 80}")
    print("BACKGROUND TASK PROFILING")
    print(f"{'=' * 80}\n")

    if args.task in ["resilience", "all"]:
        print("\nProfiling Resilience Check Task...")
        profile_resilience_task()
        print()

    if args.task in ["notification", "all"]:
        print("\nProfiling Notification Task...")
        profile_notification_task()
        print()


if __name__ == "__main__":
    main()
