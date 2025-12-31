"""
Database Query Profiler

Profiles database query performance to identify N+1 queries, slow queries,
and inefficient ORM usage.

Usage:
    python -m profiling.profile_queries
    python -m profiling.profile_queries --query-type joins
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import joinedload, sessionmaker

from app.core.config import settings
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from profiling import ProfilerContext


class QueryProfiler:
    """Track and profile database queries."""

    def __init__(self):
        self.queries = []

    def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Called before query execution."""
        import time

        context._query_start_time = time.perf_counter()

    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Called after query execution."""
        import time

        total_time = time.perf_counter() - context._query_start_time
        self.queries.append(
            {
                "statement": statement,
                "parameters": parameters,
                "duration": total_time,
            }
        )

    def attach_to_engine(self, engine):
        """Attach query profiler to SQLAlchemy engine."""
        event.listen(engine, "before_cursor_execute", self.before_cursor_execute)
        event.listen(engine, "after_cursor_execute", self.after_cursor_execute)

    def print_summary(self):
        """Print query summary statistics."""
        if not self.queries:
            print("No queries recorded")
            return

        total_time = sum(q["duration"] for q in self.queries)
        avg_time = total_time / len(self.queries)

        sorted_queries = sorted(self.queries, key=lambda x: x["duration"], reverse=True)

        print(f"\n{'=' * 80}")
        print("QUERY PROFILE SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total Queries: {len(self.queries)}")
        print(f"Total Time: {total_time:.3f}s")
        print(f"Average Time: {avg_time:.6f}s")
        print(f"\nSlowest Queries:")
        print(f"{'-' * 80}")

        for i, query in enumerate(sorted_queries[:10], 1):
            print(f"\n{i}. Duration: {query['duration']:.6f}s")
            print(f"   SQL: {query['statement'][:200]}")


def profile_simple_queries():
    """Profile simple SELECT queries."""
    print("Profiling simple SELECT queries...")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    query_profiler = QueryProfiler()
    query_profiler.attach_to_engine(engine)

    db = SessionLocal()

    try:
        # Create test data
        people = []
        for i in range(100):
            person = Person(
                id=uuid4(),
                name=f"Query Person {i + 1}",
                type="resident",
                email=f"qprof{i + 1}@test.org",
                pgy_level=1,
            )
            db.add(person)
            people.append(person)
        db.commit()

        person_ids = [p.id for p in people]

        # Profile queries
        profiler = ProfilerContext("simple_queries")

        with profiler:
            for person_id in person_ids[:50]:
                result = db.execute(select(Person).where(Person.id == person_id)).scalar_one_or_none()

        profiler.print_stats(limit=30)
        query_profiler.print_summary()

        output_dir = Path(__file__).parent.parent.parent / "profiling_results"
        profiler.save_stats(output_dir)

    finally:
        db.query(Person).delete()
        db.commit()
        db.close()


def profile_join_queries():
    """Profile JOIN queries with relationships."""
    print("Profiling JOIN queries...")

    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)

    query_profiler = QueryProfiler()
    query_profiler.attach_to_engine(engine)

    db = SessionLocal()

    try:
        # Create complex test data
        template = RotationTemplate(
            id=uuid4(),
            name="Join Profile",
            activity_type="clinic",
            abbreviation="JP",
        )
        db.add(template)

        people = []
        for i in range(50):
            person = Person(
                id=uuid4(),
                name=f"Join Person {i + 1}",
                type="resident",
                email=f"join{i + 1}@test.org",
                pgy_level=1,
            )
            db.add(person)
            people.append(person)

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

        # Create assignments
        for person in people:
            for block in blocks[:5]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=person.id,
                    rotation_template_id=template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Profile with eager loading
        profiler = ProfilerContext("join_queries_eager")

        with profiler:
            result = db.execute(
                select(Assignment)
                .options(
                    joinedload(Assignment.person),
                    joinedload(Assignment.block),
                    joinedload(Assignment.rotation_template),
                )
                .limit(100)
            ).scalars().all()

        profiler.print_stats(limit=30)
        query_profiler.print_summary()

        output_dir = Path(__file__).parent.parent.parent / "profiling_results"
        profiler.save_stats(output_dir)

    finally:
        db.query(Assignment).delete()
        db.query(Block).delete()
        db.query(Person).delete()
        db.query(RotationTemplate).delete()
        db.commit()
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Profile database queries")
    parser.add_argument(
        "--query-type",
        type=str,
        default="simple",
        choices=["simple", "joins", "all"],
        help="Query type to profile",
    )

    args = parser.parse_args()

    if args.query_type in ["simple", "all"]:
        profile_simple_queries()
        print()

    if args.query_type in ["joins", "all"]:
        profile_join_queries()
        print()


if __name__ == "__main__":
    main()
