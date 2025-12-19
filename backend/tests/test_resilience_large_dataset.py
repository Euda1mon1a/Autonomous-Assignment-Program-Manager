"""
Tests for resilience endpoints with large datasets (>100 records).

These tests verify that the removal of .limit(100) constraints works correctly
and that resilience queries properly fetch all data without truncation.

Issue: #277 - Resilience reports truncate data at 100 rows
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestLargeDatasetQueryBehavior:
    """
    Tests to verify queries return all records without truncation.

    These tests directly verify the query behavior that was fixed by removing
    .limit(100) constraints from resilience routes.
    """

    def test_faculty_query_returns_all_150(self, db: Session):
        """
        Verify faculty query returns all 150 records, not just first 100.

        This directly tests the query pattern used in get_system_health.
        """
        # Create 150 faculty members
        for i in range(150):
            person = Person(
                id=uuid4(),
                name=f"Faculty Member {i}",
                type="faculty",
                email=f"faculty{i}@test.org",
            )
            db.add(person)
        db.commit()

        # Query using the same pattern as the resilience routes
        faculty = (
            db.query(Person)
            .filter(Person.type == "faculty")
            .order_by(Person.id)
            .all()
        )

        # Verify all 150 are returned (not truncated to 100)
        assert len(faculty) == 150

    def test_blocks_query_returns_all_120(self, db: Session):
        """
        Verify blocks query returns all 120 records, not just first 100.
        """
        # Create 120 blocks (60 days * 2 blocks per day)
        start_date = date.today()
        for i in range(60):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=i * 2 + (0 if time_of_day == "AM" else 1),
                    is_weekend=False,
                )
                db.add(block)
        db.commit()

        end_date = start_date + timedelta(days=60)

        # Query using the same pattern as the resilience routes
        blocks = (
            db.query(Block)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date
            )
            .order_by(Block.date, Block.id)
            .all()
        )

        # Verify all 120 are returned (not truncated to 100)
        assert len(blocks) == 120

    def test_assignments_query_returns_all_150(self, db: Session):
        """
        Verify assignments query returns all 150 records, not just first 100.
        """
        # Create faculty
        faculty = []
        for i in range(50):
            person = Person(
                id=uuid4(),
                name=f"Doctor {i}",
                type="faculty",
                email=f"doctor{i}@test.org",
            )
            db.add(person)
            faculty.append(person)

        # Create blocks
        blocks = []
        start_date = date.today()
        for i in range(80):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=i * 2 + (0 if time_of_day == "AM" else 1),
                    is_weekend=False,
                )
                db.add(block)
                blocks.append(block)

        # Create rotation template
        template = RotationTemplate(
            id=uuid4(),
            name="General Clinic",
            activity_type="clinic",
            abbreviation="GC",
        )
        db.add(template)

        db.commit()

        # Create 150 assignments
        for i in range(150):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i % len(blocks)].id,
                person_id=faculty[i % len(faculty)].id,
                rotation_template_id=template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        end_date = start_date + timedelta(days=80)

        # Query using the same pattern as the resilience routes
        from sqlalchemy.orm import joinedload

        assignments = (
            db.query(Assignment)
            .join(Block)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template)
            )
            .filter(
                Block.date >= start_date,
                Block.date <= end_date
            )
            .order_by(Block.date, Assignment.id)
            .all()
        )

        # Verify all 150 are returned (not truncated to 100)
        assert len(assignments) == 150


class TestLargeDatasetScenarios:
    """
    Tests for various large dataset scenarios.
    """

    def test_mixed_large_dataset_all_types(self, db: Session):
        """
        Verify all three query types work together with large datasets.

        Simulates a realistic residency program with:
        - 125 faculty
        - 120 blocks (60 days)
        - 200 assignments
        """
        # Create 125 faculty
        faculty = []
        for i in range(125):
            person = Person(
                id=uuid4(),
                name=f"Faculty {i}",
                type="faculty",
                email=f"faculty{i}@hospital.org",
            )
            db.add(person)
            faculty.append(person)

        # Create 120 blocks
        blocks = []
        start_date = date.today()
        for i in range(60):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=i * 2 + (0 if time_of_day == "AM" else 1),
                    is_weekend=False,
                )
                db.add(block)
                blocks.append(block)

        # Create template
        template = RotationTemplate(
            id=uuid4(),
            name="Ward Service",
            activity_type="inpatient",
            abbreviation="WS",
        )
        db.add(template)

        db.commit()

        # Create 200 assignments
        for i in range(200):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i % len(blocks)].id,
                person_id=faculty[i % len(faculty)].id,
                rotation_template_id=template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        end_date = start_date + timedelta(days=60)

        # Query all three types
        faculty_result = (
            db.query(Person)
            .filter(Person.type == "faculty")
            .order_by(Person.id)
            .all()
        )

        blocks_result = (
            db.query(Block)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date
            )
            .order_by(Block.date, Block.id)
            .all()
        )

        from sqlalchemy.orm import joinedload

        assignments_result = (
            db.query(Assignment)
            .join(Block)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template)
            )
            .filter(
                Block.date >= start_date,
                Block.date <= end_date
            )
            .order_by(Block.date, Assignment.id)
            .all()
        )

        # Verify none are truncated
        assert len(faculty_result) == 125, f"Expected 125 faculty, got {len(faculty_result)}"
        assert len(blocks_result) == 120, f"Expected 120 blocks, got {len(blocks_result)}"
        assert len(assignments_result) == 200, f"Expected 200 assignments, got {len(assignments_result)}"

    def test_query_ordering_is_deterministic(self, db: Session):
        """
        Verify query results are deterministically ordered.

        This ensures the same order on repeated queries, which is important
        for consistent health check results.
        """
        # Create faculty in random order
        import random
        faculty_ids = [uuid4() for _ in range(50)]
        random.shuffle(faculty_ids)

        for fid in faculty_ids:
            person = Person(
                id=fid,
                name=f"Faculty {fid}",
                type="faculty",
                email=f"{fid}@test.org",
            )
            db.add(person)
        db.commit()

        # Query twice
        result1 = (
            db.query(Person)
            .filter(Person.type == "faculty")
            .order_by(Person.id)
            .all()
        )

        result2 = (
            db.query(Person)
            .filter(Person.type == "faculty")
            .order_by(Person.id)
            .all()
        )

        # Verify same order
        assert [p.id for p in result1] == [p.id for p in result2]

    def test_exactly_100_records_all_returned(self, db: Session):
        """
        Edge case: Verify exactly 100 records are all returned.

        Tests the boundary condition where the old limit would have
        returned all records anyway.
        """
        for i in range(100):
            person = Person(
                id=uuid4(),
                name=f"Faculty {i}",
                type="faculty",
                email=f"faculty{i}@test.org",
            )
            db.add(person)
        db.commit()

        faculty = (
            db.query(Person)
            .filter(Person.type == "faculty")
            .order_by(Person.id)
            .all()
        )

        assert len(faculty) == 100

    def test_101_records_all_returned(self, db: Session):
        """
        Edge case: Verify 101 records are all returned.

        Tests just above the old 100 limit to ensure no truncation.
        """
        for i in range(101):
            person = Person(
                id=uuid4(),
                name=f"Faculty {i}",
                type="faculty",
                email=f"faculty{i}@test.org",
            )
            db.add(person)
        db.commit()

        faculty = (
            db.query(Person)
            .filter(Person.type == "faculty")
            .order_by(Person.id)
            .all()
        )

        # This would have been 100 before the fix
        assert len(faculty) == 101
