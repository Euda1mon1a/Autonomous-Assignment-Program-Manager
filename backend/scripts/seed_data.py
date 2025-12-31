"""
Database seeding utilities for development and testing.

Provides:
- Development seed data (sanitized)
- Test fixture seed data
- Demo environment seed data
- Seed data validation
- Incremental seeding
- Seed data cleanup
"""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.block import Block
from app.models.rotation_template import RotationTemplate
from app.models.assignment import Assignment
from app.models.user import User
from app.core.security import get_password_hash


class SeedData:
    """Base seed data generator."""

    def __init__(self, db: Session, start_date: date | None = None):
        """
        Initialize seed data generator.

        Args:
            db: Database session
            start_date: Starting date for blocks (defaults to today)
        """
        self.db = db
        self.start_date = start_date or date.today()

    def validate(self) -> bool:
        """
        Validate seed data can be applied.

        Returns:
            True if valid, False otherwise
        """
        # Check for existing data
        person_count = self.db.query(Person).count()
        user_count = self.db.query(User).count()

        return person_count == 0 and user_count == 0

    def clear(self) -> int:
        """
        Clear seeded data (opposite of seed).

        Returns:
            Number of records deleted
        """
        count = 0

        # Delete in correct order to avoid foreign key issues
        count += self.db.query(Assignment).delete()
        count += self.db.query(Block).delete()
        count += self.db.query(RotationTemplate).delete()
        count += self.db.query(Person).delete()
        count += self.db.query(User).delete()

        self.db.commit()
        return count


class DevelopmentSeed(SeedData):
    """Development environment seed data (sanitized)."""

    def seed(self) -> dict[str, Any]:
        """
        Seed development database.

        Returns:
            Dictionary of created resources
        """
        if not self.validate():
            raise ValueError("Database already contains data")

        resources = {
            "users": self._create_users(),
            "persons": self._create_persons(),
            "rotation_templates": self._create_rotation_templates(),
            "blocks": self._create_blocks(),
            "assignments": self._create_assignments(),
        }

        self.db.commit()
        return resources

    def _create_users(self) -> list[User]:
        """Create development users."""
        users = [
            User(
                id=str(uuid4()),
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator",
                is_active=True,
                role="ADMIN",
            ),
            User(
                id=str(uuid4()),
                username="coordinator",
                email="coordinator@example.com",
                hashed_password=get_password_hash("coord123"),
                full_name="Scheduling Coordinator",
                is_active=True,
                role="COORDINATOR",
            ),
            User(
                id=str(uuid4()),
                username="faculty",
                email="faculty@example.com",
                hashed_password=get_password_hash("fac123"),
                full_name="Faculty Member",
                is_active=True,
                role="FACULTY",
            ),
        ]

        for user in users:
            self.db.add(user)

        return users

    def _create_persons(self) -> list[Person]:
        """Create development persons."""
        persons = []

        # Residents
        for i in range(1, 4):
            for j in range(1, 4):
                person = Person(
                    id=str(uuid4()),
                    name=f"PGY{i}-{j:02d}",
                    role="RESIDENT",
                    specialization="Internal Medicine",
                    start_date=self.start_date - timedelta(days=365 * i),
                    is_active=True,
                )
                persons.append(person)
                self.db.add(person)

        # Faculty
        for i in range(1, 4):
            person = Person(
                id=str(uuid4()),
                name=f"FAC-{i:02d}",
                role="FACULTY",
                specialization="Internal Medicine",
                start_date=self.start_date - timedelta(days=365 * 5),
                is_active=True,
            )
            persons.append(person)
            self.db.add(person)

        return persons

    def _create_rotation_templates(self) -> list[RotationTemplate]:
        """Create rotation templates."""
        templates = [
            RotationTemplate(
                id=str(uuid4()),
                name="Inpatient",
                description="Inpatient rounds and consultation",
                is_active=True,
            ),
            RotationTemplate(
                id=str(uuid4()),
                name="Clinic",
                description="Outpatient clinic",
                is_active=True,
            ),
            RotationTemplate(
                id=str(uuid4()),
                name="Night Float",
                description="Overnight patient coverage",
                is_active=True,
            ),
            RotationTemplate(
                id=str(uuid4()),
                name="Conference",
                description="Educational conference",
                is_active=True,
            ),
        ]

        for template in templates:
            self.db.add(template)

        return templates

    def _create_blocks(self) -> list[Block]:
        """Create block schedule."""
        blocks = []
        current_date = self.start_date

        for i in range(260):  # Half year of blocks
            for session in ["AM", "PM"]:
                block = Block(
                    id=str(uuid4()),
                    date=current_date,
                    session=session,
                    is_active=True,
                )
                blocks.append(block)
                self.db.add(block)

            current_date += timedelta(days=1)

        return blocks

    def _create_assignments(self) -> list[Assignment]:
        """Create sample assignments."""
        assignments = []

        persons = self.db.query(Person).limit(5).all()
        templates = self.db.query(RotationTemplate).all()
        blocks = self.db.query(Block).limit(20).all()

        for i, person in enumerate(persons):
            for j, block in enumerate(blocks):
                template = templates[j % len(templates)]
                assignment = Assignment(
                    id=str(uuid4()),
                    person_id=person.id,
                    block_id=block.id,
                    rotation_template_id=template.id,
                    status="ACTIVE",
                )
                assignments.append(assignment)
                self.db.add(assignment)

        return assignments


class TestFixtureSeed(SeedData):
    """Test fixture seed data with minimal required data."""

    def seed(self) -> dict[str, Any]:
        """
        Seed minimal test data.

        Returns:
            Dictionary of created resources
        """
        resources = {
            "users": self._create_test_users(),
            "persons": self._create_test_persons(),
            "rotation_templates": self._create_test_templates(),
            "blocks": self._create_test_blocks(),
        }

        self.db.commit()
        return resources

    def _create_test_users(self) -> list[User]:
        """Create test users."""
        user = User(
            id="test-user-1",
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            role="COORDINATOR",
        )
        self.db.add(user)
        return [user]

    def _create_test_persons(self) -> list[Person]:
        """Create test persons."""
        persons = [
            Person(
                id="test-resident-1",
                name="Test Resident",
                role="RESIDENT",
                start_date=self.start_date,
                is_active=True,
            ),
            Person(
                id="test-faculty-1",
                name="Test Faculty",
                role="FACULTY",
                start_date=self.start_date,
                is_active=True,
            ),
        ]

        for person in persons:
            self.db.add(person)

        return persons

    def _create_test_templates(self) -> list[RotationTemplate]:
        """Create test rotation templates."""
        templates = [
            RotationTemplate(
                id="test-template-1",
                name="Test Rotation",
                is_active=True,
            ),
        ]

        for template in templates:
            self.db.add(template)

        return templates

    def _create_test_blocks(self) -> list[Block]:
        """Create test blocks."""
        blocks = [
            Block(
                id="test-block-1",
                date=self.start_date,
                session="AM",
                is_active=True,
            ),
            Block(
                id="test-block-2",
                date=self.start_date,
                session="PM",
                is_active=True,
            ),
        ]

        for block in blocks:
            self.db.add(block)

        return blocks


class DemoSeed(SeedData):
    """Demo environment seed data."""

    def seed(self) -> dict[str, Any]:
        """
        Seed demo database.

        Returns:
            Dictionary of created resources
        """
        return DevelopmentSeed(self.db, self.start_date).seed()


class SeedDataManager:
    """Manager for all seeding operations."""

    @staticmethod
    def seed_development(db: Session, start_date: date | None = None) -> dict[str, Any]:
        """Seed development data."""
        seeder = DevelopmentSeed(db, start_date)
        return seeder.seed()

    @staticmethod
    def seed_test_fixtures(
        db: Session, start_date: date | None = None
    ) -> dict[str, Any]:
        """Seed test fixtures."""
        seeder = TestFixtureSeed(db, start_date)
        return seeder.seed()

    @staticmethod
    def seed_demo(db: Session, start_date: date | None = None) -> dict[str, Any]:
        """Seed demo data."""
        seeder = DemoSeed(db, start_date)
        return seeder.seed()

    @staticmethod
    def clear_all_seeds(db: Session) -> int:
        """Clear all seeded data."""
        seeder = SeedData(db)
        return seeder.clear()

    @staticmethod
    def validate_environment(db: Session) -> bool:
        """Check if environment can accept seed data."""
        seeder = SeedData(db)
        return seeder.validate()


# CLI Interface
def main():
    """CLI interface for seeding."""
    import argparse
    from app.db.session import SessionLocal

    parser = argparse.ArgumentParser(description="Database seeding")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("dev", help="Seed development data")
    subparsers.add_parser("test", help="Seed test fixtures")
    subparsers.add_parser("demo", help="Seed demo data")
    subparsers.add_parser("validate", help="Validate seeding compatibility")
    subparsers.add_parser("clear", help="Clear all seeded data")

    args = parser.parse_args()

    db = SessionLocal()

    try:
        if args.command == "dev":
            print("Seeding development data...")
            result = SeedDataManager.seed_development(db)
            print(
                f"Created: {json.dumps({k: len(v) for k, v in result.items()}, indent=2)}"
            )

        elif args.command == "test":
            print("Seeding test fixtures...")
            result = SeedDataManager.seed_test_fixtures(db)
            print(
                f"Created: {json.dumps({k: len(v) for k, v in result.items()}, indent=2)}"
            )

        elif args.command == "demo":
            print("Seeding demo data...")
            result = SeedDataManager.seed_demo(db)
            print(
                f"Created: {json.dumps({k: len(v) for k, v in result.items()}, indent=2)}"
            )

        elif args.command == "validate":
            is_valid = SeedDataManager.validate_environment(db)
            print(f"Seeding compatible: {is_valid}")

        elif args.command == "clear":
            print("Clearing seeded data...")
            count = SeedDataManager.clear_all_seeds(db)
            print(f"Deleted {count} records")

    finally:
        db.close()


if __name__ == "__main__":
    main()
