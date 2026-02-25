"""Service for generating academic blocks and daily half-day blocks."""

import logging
from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.academic_block import AcademicBlock
from app.models.block import Block
from app.models.day_type import (
    DayType,
    OperationalIntent,
    get_default_operational_intent,
)
from app.utils.academic_blocks import get_all_block_dates
from app.utils.holidays import get_federal_holidays, is_federal_holiday

logger = logging.getLogger(__name__)


class BlockGenerationService:
    """Service to manage creation of academic and daily blocks."""

    def __init__(self, db: Session):
        self.db = db

    def ensure_academic_blocks_exist(self, academic_year: int) -> list[AcademicBlock]:
        """Ensure all 14 AcademicBlock records exist for the given year."""
        existing = (
            self.db.query(AcademicBlock)
            .filter(AcademicBlock.academic_year == academic_year)
            .order_by(AcademicBlock.block_number)
            .all()
        )

        if len(existing) == 14:
            return existing

        existing_nums = {b.block_number for b in existing}
        created = []

        block_ranges = get_all_block_dates(academic_year)
        for br in block_ranges:
            if br.block_number not in existing_nums:
                # Orientation block (0) can be 0 days
                if br.block_number == 0 and br.duration_days <= 0:
                    continue

                ab = AcademicBlock(
                    id=uuid4(),
                    block_number=br.block_number,
                    academic_year=academic_year,
                    start_date=br.start_date,
                    end_date=br.end_date,
                    is_orientation=(br.block_number == 0),
                    is_variable_length=(br.block_number in (0, 13)),
                    name=f"Block {br.block_number}"
                    if br.block_number > 0
                    else "Orientation",
                )
                self.db.add(ab)
                created.append(ab)

        if created:
            self.db.flush()
            logger.info(
                f"Created {len(created)} academic blocks for AY {academic_year}"
            )

        return (
            self.db.query(AcademicBlock)
            .filter(AcademicBlock.academic_year == academic_year)
            .order_by(AcademicBlock.block_number)
            .all()
        )

    def generate_daily_blocks(
        self, start_date: date, end_date: date, block_number: int
    ) -> tuple[int, int]:
        """Generate AM/PM half-day blocks for a date range."""
        created = 0
        skipped = 0

        # Holiday lookup
        holiday_lookup = {}
        for year in {start_date.year, end_date.year}:
            for holiday in get_federal_holidays(year):
                holiday_lookup[holiday.date] = (holiday.name, holiday.actual_date)

        current = start_date
        while current <= end_date:
            is_weekend = current.weekday() >= 5
            is_holiday, holiday_name = is_federal_holiday(current)
            actual_date = (
                holiday_lookup.get(current, (None, None))[1] if is_holiday else None
            )

            for tod in ["AM", "PM"]:
                existing = (
                    self.db.query(Block)
                    .filter(Block.date == current, Block.time_of_day == tod)
                    .first()
                )

                if existing:
                    skipped += 1
                    continue

                day_type = DayType.FEDERAL_HOLIDAY if is_holiday else DayType.NORMAL
                operational_intent = (
                    get_default_operational_intent(day_type)
                    if is_holiday
                    else OperationalIntent.NORMAL
                )

                block = Block(
                    date=current,
                    time_of_day=tod,
                    block_number=block_number,
                    is_weekend=is_weekend,
                    is_holiday=is_holiday,
                    holiday_name=holiday_name,
                    day_type=day_type,
                    operational_intent=operational_intent,
                    actual_date=actual_date,
                )
                self.db.add(block)
                created += 1

            current += timedelta(days=1)

        if created:
            self.db.flush()

        return created, skipped
