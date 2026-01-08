#!/usr/bin/env python3
"""
Block Assignments Import Script

Imports resident rotation assignments from CSV into block_assignments table.

Usage:
    python -m scripts.import_block_assignments --csv data.csv --year 2026
    python -m scripts.import_block_assignments --csv data.csv --year 2026 --dry-run

CSV Format:
    block_number,rotation_abbrev,resident_name
    10,HILO,Smith
    10,FMC,Jones
    11,FMIT,Williams

Or with full names:
    block_number,rotation_abbrev,resident_name
    10,HILO,"Smith, Jane"
    10,FMC,"Jones, John"
"""
import argparse
import csv
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.block_assignment import BlockAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class BlockAssignmentImporter:
    """Import block assignments from CSV."""

    def __init__(self, session: AsyncSession, academic_year: int, dry_run: bool = False):
        self.session = session
        self.academic_year = academic_year
        self.dry_run = dry_run
        self._rotation_cache: dict[str, UUID] = {}
        self._resident_cache: dict[str, tuple[UUID, str]] = {}

    async def load_caches(self) -> None:
        """Pre-load rotation templates and residents for fast lookup."""
        # Load rotation templates
        result = await self.session.execute(
            select(RotationTemplate).where(RotationTemplate.is_archived == False)
        )
        templates = result.scalars().all()

        for t in templates:
            # Index by abbreviation and display_abbreviation
            if t.abbreviation:
                self._rotation_cache[t.abbreviation.upper()] = t.id
            if t.display_abbreviation:
                self._rotation_cache[t.display_abbreviation.upper()] = t.id
            # Also index by name for fallback
            self._rotation_cache[t.name.upper()] = t.id

        print(f"Loaded {len(templates)} rotation templates")

        # Load residents
        result = await self.session.execute(
            select(Person).where(Person.type == "resident")
        )
        residents = result.scalars().all()

        for r in residents:
            # Extract last name for fuzzy matching
            name_parts = r.name.replace(",", " ").split()
            for part in name_parts:
                # Skip common prefixes
                if part.lower() in ("dr", "dr.", "md"):
                    continue
                # Index by each name part (case-insensitive)
                key = part.upper()
                if key not in self._resident_cache:
                    self._resident_cache[key] = (r.id, r.name)

        print(f"Loaded {len(residents)} residents")

    def match_rotation(self, abbrev: str) -> UUID | None:
        """Match rotation abbreviation to template ID."""
        # Direct match
        key = abbrev.upper().strip()
        if key in self._rotation_cache:
            return self._rotation_cache[key]

        # Try common variations
        variations = [
            key.replace(" ", "-"),
            key.replace("-", " "),
            key.replace("/", "-"),
            key.replace("_", "-"),
        ]
        for var in variations:
            if var in self._rotation_cache:
                return self._rotation_cache[var]

        return None

    def match_resident(self, name: str) -> tuple[UUID, str] | None:
        """Match resident name to person ID."""
        # Clean and split name
        name = name.strip().replace(",", " ")
        parts = name.split()

        # Try each part (usually last name is most unique)
        for part in parts:
            key = part.upper()
            if key in self._resident_cache:
                return self._resident_cache[key]

        return None

    async def check_duplicate(self, block_number: int, resident_id: UUID) -> bool:
        """Check if assignment already exists."""
        result = await self.session.execute(
            select(BlockAssignment).where(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == self.academic_year,
                BlockAssignment.resident_id == resident_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def import_csv(self, csv_path: str) -> dict[str, Any]:
        """Import assignments from CSV file."""
        await self.load_caches()

        results = {
            "total_rows": 0,
            "imported": 0,
            "skipped_duplicate": 0,
            "errors": [],
        }

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)

            # Normalize header names
            if reader.fieldnames:
                reader.fieldnames = [h.lower().strip() for h in reader.fieldnames]

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                results["total_rows"] += 1

                # Extract fields (handle various column name variations)
                block_number = int(row.get("block_number") or row.get("block") or row.get("blk"))
                rotation_abbrev = row.get("rotation_abbrev") or row.get("rotation") or row.get("rot")
                resident_name = row.get("resident_name") or row.get("resident") or row.get("name")

                if not all([block_number, rotation_abbrev, resident_name]):
                    results["errors"].append(f"Row {row_num}: Missing required field")
                    continue

                # Validate block number
                if not (0 <= block_number <= 13):
                    results["errors"].append(f"Row {row_num}: Invalid block_number {block_number}")
                    continue

                # Match rotation
                rotation_id = self.match_rotation(rotation_abbrev)
                if not rotation_id:
                    results["errors"].append(
                        f"Row {row_num}: Unknown rotation '{rotation_abbrev}'"
                    )
                    continue

                # Match resident
                resident_match = self.match_resident(resident_name)
                if not resident_match:
                    results["errors"].append(
                        f"Row {row_num}: Unknown resident '{resident_name}'"
                    )
                    continue

                resident_id, matched_name = resident_match

                # Check for duplicate
                if await self.check_duplicate(block_number, resident_id):
                    results["skipped_duplicate"] += 1
                    print(f"  Skip duplicate: Block {block_number}, {matched_name}")
                    continue

                # Create assignment
                if not self.dry_run:
                    assignment = BlockAssignment(
                        block_number=block_number,
                        academic_year=self.academic_year,
                        resident_id=resident_id,
                        rotation_template_id=rotation_id,
                        assignment_reason="manual",
                        created_by="import_script",
                    )
                    self.session.add(assignment)

                results["imported"] += 1
                print(f"  Import: Block {block_number}, {matched_name} -> {rotation_abbrev}")

        if not self.dry_run:
            await self.session.commit()

        return results


async def main():
    parser = argparse.ArgumentParser(description="Import block assignments from CSV")
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--year", type=int, required=True, help="Academic year (e.g., 2026)")
    parser.add_argument("--dry-run", action="store_true", help="Validate without inserting")
    args = parser.parse_args()

    # Check file exists
    if not Path(args.csv).exists():
        print(f"Error: File not found: {args.csv}")
        sys.exit(1)

    # Get database URL
    settings = get_settings()
    database_url = str(settings.SQLALCHEMY_DATABASE_URI)

    # Create async engine
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        importer = BlockAssignmentImporter(
            session=session,
            academic_year=args.year,
            dry_run=args.dry_run,
        )

        print(f"\n{'DRY RUN - ' if args.dry_run else ''}Importing block assignments")
        print(f"File: {args.csv}")
        print(f"Academic Year: {args.year}")
        print("-" * 50)

        results = await importer.import_csv(args.csv)

        print("-" * 50)
        print(f"Total rows: {results['total_rows']}")
        print(f"Imported: {results['imported']}")
        print(f"Skipped (duplicate): {results['skipped_duplicate']}")
        print(f"Errors: {len(results['errors'])}")

        if results["errors"]:
            print("\nErrors:")
            for err in results["errors"][:20]:  # Limit to first 20
                print(f"  - {err}")
            if len(results["errors"]) > 20:
                print(f"  ... and {len(results['errors']) - 20} more")

        if args.dry_run:
            print("\n[DRY RUN] No changes made to database")


if __name__ == "__main__":
    asyncio.run(main())
