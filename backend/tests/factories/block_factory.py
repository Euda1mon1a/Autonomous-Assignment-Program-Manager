"""Factory for creating test Block instances."""

from datetime import date, timedelta
from typing import Optional
from uuid import uuid4

from faker import Faker
from sqlalchemy.orm import Session

from app.models.block import Block
from app.utils.academic_blocks import get_block_number_for_date

fake = Faker()


class BlockFactory:
    """Factory for creating Block instances with random data."""

    US_FEDERAL_HOLIDAYS = {
        "New Year's Day": (1, 1),
        "Martin Luther King Jr. Day": None,  # 3rd Monday in January
        "Presidents' Day": None,  # 3rd Monday in February
        "Memorial Day": None,  # Last Monday in May
        "Independence Day": (7, 4),
        "Labor Day": None,  # 1st Monday in September
        "Columbus Day": None,  # 2nd Monday in October
        "Veterans Day": (11, 11),
        "Thanksgiving": None,  # 4th Thursday in November
        "Christmas": (12, 25),
    }

    @staticmethod
    def create_block(
        db: Session,
        block_date: date | None = None,
        time_of_day: str = "AM",
        block_number: int | None = None,
        is_weekend: bool | None = None,
        is_holiday: bool | None = None,
        holiday_name: str | None = None,
    ) -> Block:
        """
        Create a single block.

        Args:
            db: Database session
            block_date: Date for block (today if not provided)
            time_of_day: "AM" or "PM"
            block_number: Academic year block number (calculated if not provided)
            is_weekend: Weekend flag (calculated from date if not provided)
            is_holiday: Holiday flag (False if not provided)
            holiday_name: Name of holiday if is_holiday=True

        Returns:
            Block: Created block instance
        """
        if block_date is None:
            block_date = date.today()

        if is_weekend is None:
            is_weekend = block_date.weekday() >= 5

        if is_holiday is None:
            is_holiday = False

        if block_number is None:
            block_number = BlockFactory._calculate_block_number(block_date)

        block = Block(
            id=uuid4(),
            date=block_date,
            time_of_day=time_of_day,
            block_number=block_number,
            is_weekend=is_weekend,
            is_holiday=is_holiday,
            holiday_name=holiday_name,
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        return block

    @staticmethod
    def create_day_blocks(
        db: Session,
        block_date: date | None = None,
    ) -> tuple[Block, Block]:
        """
        Create AM and PM blocks for a single day.

        Args:
            db: Database session
            block_date: Date for blocks (today if not provided)

        Returns:
            tuple[Block, Block]: (AM block, PM block)
        """
        if block_date is None:
            block_date = date.today()

        am_block = BlockFactory.create_block(
            db, block_date=block_date, time_of_day="AM"
        )
        pm_block = BlockFactory.create_block(
            db, block_date=block_date, time_of_day="PM"
        )

        return am_block, pm_block

    @staticmethod
    def create_week_blocks(
        db: Session,
        start_date: date | None = None,
    ) -> list[Block]:
        """
        Create blocks for a full week (7 days × 2 blocks = 14 blocks).

        Args:
            db: Database session
            start_date: Starting date (today if not provided)

        Returns:
            list[Block]: List of 14 blocks (7 days, AM + PM each)
        """
        if start_date is None:
            start_date = date.today()

        blocks = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                block = BlockFactory.create_block(
                    db, block_date=current_date, time_of_day=time_of_day
                )
                blocks.append(block)

        return blocks

    @staticmethod
    def create_block_period(
        db: Session,
        start_date: date | None = None,
        days: int = 28,
    ) -> list[Block]:
        """
        Create blocks for a 4-week block period (28 days × 2 blocks = 56 blocks).

        Args:
            db: Database session
            start_date: Starting date (today if not provided)
            days: Number of days (default 28 for standard block)

        Returns:
            list[Block]: List of blocks for the period
        """
        if start_date is None:
            start_date = date.today()

        blocks = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                block = BlockFactory.create_block(
                    db, block_date=current_date, time_of_day=time_of_day
                )
                blocks.append(block)

        return blocks

    @staticmethod
    def create_academic_year_blocks(
        db: Session,
        year: int | None = None,
    ) -> list[Block]:
        """
        Create blocks for a full academic year (365 days × 2 blocks = 730 blocks).

        Academic year runs July 1 - June 30.

        Args:
            db: Database session
            year: Starting year (current year if not provided)

        Returns:
            list[Block]: List of 730 blocks for academic year
        """
        if year is None:
            year = date.today().year

        start_date = date(year, 7, 1)  # July 1
        end_date = date(year + 1, 6, 30)  # June 30 next year

        blocks = []
        current_date = start_date

        while current_date <= end_date:
            block_number = BlockFactory._calculate_block_number(current_date)
            is_weekend = current_date.weekday() >= 5
            is_holiday, holiday_name = BlockFactory._check_holiday(current_date)

            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=block_number,
                    is_weekend=is_weekend,
                    is_holiday=is_holiday,
                    holiday_name=holiday_name,
                )
                db.add(block)
                blocks.append(block)

            current_date += timedelta(days=1)

        db.commit()
        return blocks

    @staticmethod
    def create_weekend_blocks(
        db: Session,
        start_date: date | None = None,
        num_weekends: int = 4,
    ) -> list[Block]:
        """
        Create blocks for weekends only.

        Args:
            db: Database session
            start_date: Starting date (today if not provided)
            num_weekends: Number of weekends to create

        Returns:
            list[Block]: List of weekend blocks
        """
        if start_date is None:
            start_date = date.today()

        # Move to next Saturday
        days_until_saturday = (5 - start_date.weekday()) % 7
        if days_until_saturday == 0 and start_date.weekday() != 5:
            days_until_saturday = 6
        current_date = start_date + timedelta(days=days_until_saturday)

        blocks = []
        for _ in range(num_weekends):
            # Saturday and Sunday
            for day_offset in [0, 1]:
                weekend_date = current_date + timedelta(days=day_offset)
                for time_of_day in ["AM", "PM"]:
                    block = BlockFactory.create_block(
                        db,
                        block_date=weekend_date,
                        time_of_day=time_of_day,
                        is_weekend=True,
                    )
                    blocks.append(block)
            # Move to next Saturday
            current_date += timedelta(days=7)

        return blocks

    @staticmethod
    def create_holiday_blocks(
        db: Session,
        year: int | None = None,
    ) -> list[Block]:
        """
        Create blocks for federal holidays.

        Args:
            db: Database session
            year: Year for holidays (current year if not provided)

        Returns:
            list[Block]: List of holiday blocks
        """
        if year is None:
            year = date.today().year

        blocks = []

        # Fixed holidays
        for holiday_name, month_day in BlockFactory.US_FEDERAL_HOLIDAYS.items():
            if month_day:
                month, day = month_day
                holiday_date = date(year, month, day)

                for time_of_day in ["AM", "PM"]:
                    block = BlockFactory.create_block(
                        db,
                        block_date=holiday_date,
                        time_of_day=time_of_day,
                        is_holiday=True,
                        holiday_name=holiday_name,
                    )
                    blocks.append(block)

        return blocks

    @staticmethod
    def _calculate_block_number(block_date: date) -> int:
        """
        Calculate academic year block number (0-13) for a given date.

        Uses Thursday-Wednesday aligned blocks:
        - Block 0: July 1 through day before first Thursday (orientation)
        - Blocks 1-12: 28 days each, Thursday start, Wednesday end
        - Block 13: Starts Thursday, ends June 30 (variable length)

        Args:
            block_date: Date to calculate block number for

        Returns:
            int: Block number (0-13)
        """
        block_number, _ = get_block_number_for_date(block_date)
        return block_number

    @staticmethod
    def _check_holiday(check_date: date) -> tuple[bool, str | None]:
        """
        Check if a date is a federal holiday.

        Args:
            check_date: Date to check

        Returns:
            tuple[bool, Optional[str]]: (is_holiday, holiday_name)
        """
        # Fixed holidays
        for holiday_name, month_day in BlockFactory.US_FEDERAL_HOLIDAYS.items():
            if month_day:
                month, day = month_day
                if check_date.month == month and check_date.day == day:
                    return True, holiday_name

        # TODO: Implement floating holidays (MLK Day, Presidents' Day, etc.)
        # For now, return False for these

        return False, None
