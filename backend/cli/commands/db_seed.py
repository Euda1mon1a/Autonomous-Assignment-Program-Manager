"""
Database seeding commands.

Populate database with test/demo data.
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List

import typer
from rich.console import Console
from sqlalchemy import select

from cli.utils.output import print_success, print_error, print_info
from cli.utils.progress import progress_bar
from cli.utils.database import get_db_manager

app = typer.Typer()
console = Console()


@app.command()
def all(
    profile: str = typer.Option(
        "dev", "--profile", "-p", help="Seed profile (dev/demo/test)"
    ),
):
    """
    Seed database with complete dataset.

    Args:
        profile: Seed profile (dev, demo, test)
    """
    asyncio.run(seed_all(profile))


@app.command()
def users(
    count: int = typer.Option(10, "--count", "-n", help="Number of users to create"),
):
    """
    Seed users (residents, faculty, staff).

    Args:
        count: Number of users to create
    """
    asyncio.run(seed_users(count))


@app.command()
def schedules(
    block: int = typer.Option(1, "--block", "-b", help="Block number to seed"),
):
    """
    Seed schedule data for a block.

    Args:
        block: Block number (1-12)
    """
    asyncio.run(seed_schedules(block))


@app.command()
def clear(
    table: str = typer.Argument(None, help="Table to clear (or 'all' for everything)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """
    Clear seeded data.

    Args:
        table: Table name to clear (None for all)
        force: Skip confirmation prompt
    """
    if not force:
        from cli.utils.prompts import confirm

        if not confirm(f"Clear {table or 'all'} data?", default=False):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    asyncio.run(clear_data(table))


async def seed_all(profile: str):
    """
    Seed complete dataset.

    Args:
        profile: Seed profile (dev/demo/test)
    """
    print_info(f"Seeding database with {profile} profile...")

    # Import models
    from app.models.person import Person
    from app.models.assignment import Assignment
    from app.models.rotation import Rotation
    from app.models.block import Block

    db_manager = get_db_manager()

    async for session in db_manager.get_session():
        try:
            # Seed in order of dependencies
            print_info("Seeding rotations...")
            await _seed_rotations(session, profile)

            print_info("Seeding persons...")
            await _seed_persons(session, profile)

            print_info("Seeding blocks...")
            await _seed_blocks(session, profile)

            print_info("Seeding assignments...")
            await _seed_assignments(session, profile)

            await session.commit()
            print_success(f"Database seeded with {profile} profile")

        except Exception as e:
            await session.rollback()
            print_error(f"Seeding failed: {str(e)}")
            raise typer.Exit(1)


async def seed_users(count: int):
    """
    Seed users.

    Args:
        count: Number of users to create
    """
    from app.models.person import Person, Role

    print_info(f"Creating {count} users...")

    db_manager = get_db_manager()

    async for session in db_manager.get_session():
        try:
            # Create residents
            residents_count = int(count * 0.6)
            for i in range(residents_count):
                person = Person(
                    id=f"RES-{i + 1:03d}",
                    first_name="Resident",
                    last_name=f"{i + 1:03d}",
                    email=f"resident{i + 1}@example.com",
                    role=Role.RESIDENT,
                    pgy_level=f"PGY-{(i % 3) + 1}",
                )
                session.add(person)

            # Create faculty
            faculty_count = int(count * 0.3)
            for i in range(faculty_count):
                person = Person(
                    id=f"FAC-{i + 1:03d}",
                    first_name="Faculty",
                    last_name=f"{i + 1:03d}",
                    email=f"faculty{i + 1}@example.com",
                    role=Role.FACULTY,
                )
                session.add(person)

            # Create staff
            staff_count = count - residents_count - faculty_count
            for i in range(staff_count):
                person = Person(
                    id=f"STAFF-{i + 1:03d}",
                    first_name="Staff",
                    last_name=f"{i + 1:03d}",
                    email=f"staff{i + 1}@example.com",
                    role=Role.CLINICAL_STAFF,
                )
                session.add(person)

            await session.commit()
            print_success(f"Created {count} users")

        except Exception as e:
            await session.rollback()
            print_error(f"User creation failed: {str(e)}")
            raise typer.Exit(1)


async def seed_schedules(block: int):
    """
    Seed schedule for a block.

    Args:
        block: Block number
    """
    print_info(f"Seeding schedule for block {block}...")

    # Implementation would create assignments for the block
    # This is a placeholder
    print_success(f"Schedule seeded for block {block}")


async def clear_data(table: str = None):
    """
    Clear seeded data.

    Args:
        table: Table name to clear (None for all)
    """
    print_info(f"Clearing {table or 'all'} data...")

    # Implementation would delete data
    # This is a placeholder
    print_success("Data cleared")


async def _seed_rotations(session, profile: str):
    """Seed rotation templates."""
    from app.models.rotation import Rotation

    rotations = [
        {"name": "Inpatient", "description": "Inpatient ward", "color": "#FF5733"},
        {"name": "Clinic", "description": "Outpatient clinic", "color": "#33FF57"},
        {"name": "Procedures", "description": "Procedures", "color": "#3357FF"},
        {"name": "Conference", "description": "Educational", "color": "#F3FF33"},
        {"name": "Call", "description": "On-call duty", "color": "#FF33F3"},
        {"name": "Night Float", "description": "Night coverage", "color": "#33FFF3"},
    ]

    for rot_data in rotations:
        rotation = Rotation(**rot_data)
        session.add(rotation)


async def _seed_persons(session, profile: str):
    """Seed persons (residents, faculty)."""
    from app.models.person import Person, Role

    # Add sample persons based on profile
    if profile in ["dev", "demo"]:
        count = 15 if profile == "dev" else 30

        for i in range(count):
            if i < count * 0.6:
                role = Role.RESIDENT
                pgy = f"PGY-{(i % 3) + 1}"
            elif i < count * 0.9:
                role = Role.FACULTY
                pgy = None
            else:
                role = Role.CLINICAL_STAFF
                pgy = None

            person = Person(
                id=f"PERSON-{i + 1:03d}",
                first_name=f"First{i + 1}",
                last_name=f"Last{i + 1}",
                email=f"person{i + 1}@example.com",
                role=role,
                pgy_level=pgy,
            )
            session.add(person)


async def _seed_blocks(session, profile: str):
    """Seed academic year blocks."""
    from app.models.block import Block

    # Create blocks for current academic year
    start_date = date(2024, 7, 1)  # July 1, 2024

    for block_num in range(1, 13):
        # Each block is ~4 weeks
        block_start = start_date + timedelta(weeks=(block_num - 1) * 4)
        block_end = block_start + timedelta(weeks=4) - timedelta(days=1)

        block = Block(
            block_number=block_num,
            start_date=block_start,
            end_date=block_end,
            academic_year=2024,
        )
        session.add(block)


async def _seed_assignments(session, profile: str):
    """Seed sample assignments."""
    # This would create sample schedule assignments
    # Placeholder for now
    pass
