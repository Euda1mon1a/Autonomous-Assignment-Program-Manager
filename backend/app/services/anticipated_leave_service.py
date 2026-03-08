"""Service for generating anticipated leave for incoming interns."""

import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.absence import Absence
from app.schemas.absence import AbsenceType
from app.models.person import Person
from app.models.settings import ApplicationSettings
from app.utils.academic_blocks import get_all_block_dates as get_academic_block_dates

logger = logging.getLogger(__name__)


class AnticipatedLeaveService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_anticipated_leave(
        self,
        academic_year: int,
        weeks_per_intern: int = 4,
        created_by_id: UUID | None = None,
    ) -> dict[str, int]:
        """
        Generate placeholder 'anticipated' leave for all PGY-1 interns.
        This provides a balanced structure for the solver before actual
        leave requests arrive.
        """
        if weeks_per_intern < 1:
            raise ValueError("weeks_per_intern must be at least 1")

        # Find all PGY-1s for the current cohort.
        # NOTE: Uses current pgy_level, not year-scoped. Once PersonAcademicYear
        # table ships (Track A), scope by academic_year to handle past/future AYs.
        interns = (
            self.db.query(Person)
            .filter(Person.pgy_level == 1, Person.is_active == True)  # noqa: E712
            .all()
        )

        if not interns:
            return {
                "interns_processed": 0,
                "absences_created": 0,
                "absences_deleted": 0,
            }

        # Clear existing anticipated leave for these interns in this AY
        # This allows safely re-running the generator
        existing_stmt = select(Absence).where(
            Absence.person_id.in_([i.id for i in interns]),
            Absence.status == "anticipated",
        )
        existing = self.db.execute(existing_stmt).scalars().all()

        deleted_count = 0
        for absence in existing:
            # Simple check if it falls in the academic year
            start_block, ay1 = get_academic_block_dates(absence.start_date)
            end_block, ay2 = get_academic_block_dates(absence.end_date)
            if ay1 == academic_year or ay2 == academic_year:
                self.db.delete(absence)
                deleted_count += 1

        self.db.flush()

        absences_created = 0

        # We will distribute the leave across blocks 2-12 (avoiding 1 and 13 usually)
        # But for simplicity in the generator, we'll assign 1 week to 4 random blocks
        # using a simple round-robin or modulo to distribute evenly.
        # This avoids all interns taking leave in Block 12.

        available_blocks = list(range(2, 13))  # Blocks 2 through 12
        num_blocks = len(available_blocks)
        # Cap to avoid zero-spacing when weeks_per_intern > num_blocks
        effective_weeks = min(weeks_per_intern, num_blocks)
        block_spacing = max(num_blocks // effective_weeks, 1)

        for i, intern in enumerate(interns):
            # Pick 'effective_weeks' distinct blocks for this intern, distributed smoothly
            for w in range(effective_weeks):
                block_idx = (i + w * block_spacing) % num_blocks
                block_num = available_blocks[block_idx]

                # We need the start and end date of that block to put the leave in
                # We'll just put it in the first week of the chosen block.
                # In a real system, you might look up the actual Block model.
                from app.models.block import Block

                block_record = (
                    self.db.query(Block)
                    .filter(
                        Block.block_number == block_num,
                        Block.academic_year == academic_year,
                    )
                    .first()
                )

                if block_record:
                    start = block_record.start_date
                    end = start + timedelta(days=6)  # 1 week
                else:
                    # Fallback to rough calculation if Block records aren't generated yet
                    from app.utils.academic_blocks import get_block_dates

                    start, _ = get_block_dates(block_num, academic_year)  # type: ignore[misc]
                    end = start + timedelta(days=6)

                absence = Absence(
                    person_id=intern.id,
                    start_date=start,
                    end_date=end,
                    absence_type=AbsenceType.VACATION.value,
                    is_blocking=False,  # Vacation is nominally non-blocking, though solver blocks it
                    is_away_from_program=True,
                    status="anticipated",
                    created_by_id=created_by_id,
                    notes="Auto-generated anticipated leave placeholder.",
                )
                self.db.add(absence)
                absences_created += 1

        self.db.commit()

        logger.info(
            f"Generated {absences_created} anticipated leave blocks for {len(interns)} interns (AY {academic_year})"
        )

        return {
            "interns_processed": len(interns),
            "absences_created": absences_created,
            "absences_deleted": deleted_count,
        }
