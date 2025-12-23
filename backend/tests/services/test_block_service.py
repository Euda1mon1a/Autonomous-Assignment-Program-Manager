"""Tests for BlockService."""

from datetime import date, timedelta
from uuid import uuid4

from app.models.block import Block
from app.services.block_service import BlockService


class TestBlockService:
    """Test suite for BlockService."""

    # ========================================================================
    # Get Block Tests
    # ========================================================================

    def test_get_block_success(self, db, sample_block):
        """Test getting a block by ID successfully."""
        service = BlockService(db)
        result = service.get_block(sample_block.id)

        assert result is not None
        assert result.id == sample_block.id
        assert result.date == sample_block.date
        assert result.time_of_day == sample_block.time_of_day

    def test_get_block_not_found(self, db):
        """Test getting a non-existent block returns None."""
        service = BlockService(db)
        result = service.get_block(uuid4())

        assert result is None

    # ========================================================================
    # List Blocks Tests
    # ========================================================================

    def test_list_blocks_no_filters(self, db, sample_blocks):
        """Test listing all blocks without filters."""
        service = BlockService(db)
        result = service.list_blocks()

        # sample_blocks creates 14 blocks (7 days * 2 times per day)
        assert result["total"] == 14
        assert len(result["items"]) == 14

    def test_list_blocks_filter_by_start_date(self, db):
        """Test filtering blocks by start_date."""
        # Create blocks on specific dates
        block1 = Block(
            id=uuid4(),
            date=date(2025, 1, 5),
            time_of_day="AM",
            block_number=1,
        )
        block2 = Block(
            id=uuid4(),
            date=date(2025, 1, 10),
            time_of_day="AM",
            block_number=1,
        )
        block3 = Block(
            id=uuid4(),
            date=date(2025, 1, 15),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([block1, block2, block3])
        db.commit()

        service = BlockService(db)
        result = service.list_blocks(start_date=date(2025, 1, 10))

        assert result["total"] == 2  # block2 and block3

    def test_list_blocks_filter_by_end_date(self, db):
        """Test filtering blocks by end_date."""
        # Create blocks on specific dates
        block1 = Block(
            id=uuid4(),
            date=date(2025, 1, 5),
            time_of_day="AM",
            block_number=1,
        )
        block2 = Block(
            id=uuid4(),
            date=date(2025, 1, 10),
            time_of_day="AM",
            block_number=1,
        )
        block3 = Block(
            id=uuid4(),
            date=date(2025, 1, 15),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([block1, block2, block3])
        db.commit()

        service = BlockService(db)
        result = service.list_blocks(end_date=date(2025, 1, 10))

        assert result["total"] == 2  # block1 and block2

    def test_list_blocks_filter_by_date_range(self, db):
        """Test filtering blocks by date range (start and end)."""
        blocks = []
        for i in range(10):
            block = Block(
                id=uuid4(),
                date=date(2025, 1, 1) + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        service = BlockService(db)
        result = service.list_blocks(
            start_date=date(2025, 1, 3),
            end_date=date(2025, 1, 7),
        )

        # Should return blocks for days 3, 4, 5, 6, 7 (5 blocks)
        assert result["total"] == 5

    def test_list_blocks_filter_by_block_number(self, db):
        """Test filtering blocks by block_number."""
        block1 = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
        )
        block2 = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=1),
            time_of_day="AM",
            block_number=2,
        )
        block3 = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=2),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([block1, block2, block3])
        db.commit()

        service = BlockService(db)
        result = service.list_blocks(block_number=1)

        assert result["total"] == 2
        assert all(block.block_number == 1 for block in result["items"])

    def test_list_blocks_multiple_filters(self, db):
        """Test combining multiple filters."""
        blocks = []
        for i in range(10):
            block = Block(
                id=uuid4(),
                date=date(2025, 1, 1) + timedelta(days=i),
                time_of_day="AM",
                block_number=1 if i < 5 else 2,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        service = BlockService(db)
        result = service.list_blocks(
            start_date=date(2025, 1, 3),
            end_date=date(2025, 1, 8),
            block_number=1,
        )

        # Days 3-5 have block_number=1 (3 blocks)
        assert result["total"] == 3

    def test_list_blocks_empty_result(self, db):
        """Test listing blocks when none exist."""
        service = BlockService(db)
        result = service.list_blocks()

        assert result["total"] == 0
        assert len(result["items"]) == 0

    # ========================================================================
    # Create Block Tests
    # ========================================================================

    def test_create_block_success_minimal_data(self, db):
        """Test creating a block with minimal required fields."""
        service = BlockService(db)
        block_date = date(2025, 2, 15)

        result = service.create_block(
            block_date=block_date,
            time_of_day="AM",
        )

        assert result["error"] is None
        block = result["block"]
        assert block is not None
        assert block.date == block_date
        assert block.time_of_day == "AM"
        assert block.id is not None

    def test_create_block_auto_calculates_is_weekend(self, db):
        """Test that is_weekend is automatically calculated if not provided."""
        service = BlockService(db)

        # Create block on a weekday (Monday = 0)
        weekday = date(2025, 1, 6)  # Monday
        result = service.create_block(
            block_date=weekday,
            time_of_day="AM",
        )
        assert result["block"].is_weekend is False

        # Create block on a weekend (Saturday = 5)
        weekend = date(2025, 1, 11)  # Saturday
        result = service.create_block(
            block_date=weekend,
            time_of_day="PM",
        )
        assert result["block"].is_weekend is True

        # Sunday (6)
        sunday = date(2025, 1, 12)  # Sunday
        result = service.create_block(
            block_date=sunday,
            time_of_day="AM",
        )
        assert result["block"].is_weekend is True

    def test_create_block_with_all_fields(self, db):
        """Test creating a block with all optional fields."""
        service = BlockService(db)
        block_date = date(2025, 7, 4)  # Independence Day

        result = service.create_block(
            block_date=block_date,
            time_of_day="PM",
            block_number=5,
            is_weekend=False,
            is_holiday=True,
        )

        block = result["block"]
        assert block.date == block_date
        assert block.time_of_day == "PM"
        assert block.block_number == 5
        assert block.is_weekend is False
        assert block.is_holiday is True

    def test_create_block_duplicate_error(self, db):
        """Test creating a duplicate block returns error."""
        service = BlockService(db)
        block_date = date(2025, 3, 15)

        # Create first block
        result1 = service.create_block(
            block_date=block_date,
            time_of_day="AM",
        )
        assert result1["error"] is None

        # Try to create duplicate
        result2 = service.create_block(
            block_date=block_date,
            time_of_day="AM",
        )

        assert result2["error"] == "Block already exists for this date and time"
        assert result2["block"] is None

    def test_create_block_different_times_same_day(self, db):
        """Test creating AM and PM blocks for the same day."""
        service = BlockService(db)
        block_date = date(2025, 4, 1)

        # Create AM block
        result_am = service.create_block(
            block_date=block_date,
            time_of_day="AM",
        )
        assert result_am["error"] is None

        # Create PM block (should succeed)
        result_pm = service.create_block(
            block_date=block_date,
            time_of_day="PM",
        )
        assert result_pm["error"] is None
        assert result_pm["block"].time_of_day == "PM"

    def test_create_block_persists_to_database(self, db):
        """Test that created block is persisted to database."""
        service = BlockService(db)
        block_date = date(2025, 5, 20)

        result = service.create_block(
            block_date=block_date,
            time_of_day="AM",
        )

        block_id = result["block"].id

        # Query directly from database
        db_block = db.query(Block).filter(Block.id == block_id).first()
        assert db_block is not None
        assert db_block.date == block_date

    # ========================================================================
    # Generate Blocks Tests
    # ========================================================================

    def test_generate_blocks_single_day(self, db):
        """Test generating blocks for a single day."""
        service = BlockService(db)
        start = date(2025, 6, 1)
        end = date(2025, 6, 1)

        result = service.generate_blocks(start, end)

        # Should create 2 blocks (AM and PM)
        assert result["total"] == 2
        assert len(result["items"]) == 2

        times = {block.time_of_day for block in result["items"]}
        assert times == {"AM", "PM"}

    def test_generate_blocks_one_week(self, db):
        """Test generating blocks for one week."""
        service = BlockService(db)
        start = date(2025, 6, 1)
        end = date(2025, 6, 7)

        result = service.generate_blocks(start, end)

        # 7 days * 2 times per day = 14 blocks
        assert result["total"] == 14

    def test_generate_blocks_calculates_block_numbers(self, db):
        """Test that generate_blocks calculates block numbers correctly."""
        service = BlockService(db)
        start = date(2025, 1, 1)
        end = date(2025, 1, 30)  # 30 days (slightly over 1 block period)

        result = service.generate_blocks(start, end, base_block_number=10)

        # Blocks on days 0-27 should be block_number 10
        # Blocks on days 28-29 should be block_number 11
        block_numbers = {block.block_number for block in result["items"]}
        assert 10 in block_numbers
        assert 11 in block_numbers

    def test_generate_blocks_sets_is_weekend_correctly(self, db):
        """Test that generate_blocks sets is_weekend correctly."""
        service = BlockService(db)
        # Start on Monday Jan 6, 2025
        start = date(2025, 1, 6)  # Monday
        end = date(2025, 1, 12)  # Sunday

        result = service.generate_blocks(start, end)

        # Check weekend flags
        for block in result["items"]:
            weekday = block.date.weekday()
            if weekday >= 5:  # Saturday or Sunday
                assert block.is_weekend is True
            else:
                assert block.is_weekend is False

    def test_generate_blocks_skips_existing(self, db):
        """Test that generate_blocks skips already existing blocks."""
        service = BlockService(db)
        start = date(2025, 7, 1)
        end = date(2025, 7, 3)

        # Pre-create a block
        existing_block = Block(
            id=uuid4(),
            date=date(2025, 7, 2),
            time_of_day="AM",
            block_number=1,
        )
        db.add(existing_block)
        db.commit()

        result = service.generate_blocks(start, end)

        # Should create 5 blocks (3 days * 2 - 1 existing)
        assert result["total"] == 5

        # Verify the existing block is still there
        db_block = db.query(Block).filter(Block.id == existing_block.id).first()
        assert db_block is not None

    def test_generate_blocks_sets_holiday_false(self, db):
        """Test that generate_blocks sets is_holiday to False."""
        service = BlockService(db)
        start = date(2025, 8, 1)
        end = date(2025, 8, 2)

        result = service.generate_blocks(start, end)

        assert all(block.is_holiday is False for block in result["items"])

    def test_generate_blocks_large_range(self, db):
        """Test generating blocks for a large date range (full year)."""
        service = BlockService(db)
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)

        result = service.generate_blocks(start, end)

        # 365 days * 2 times per day = 730 blocks
        assert result["total"] == 730

    def test_generate_blocks_custom_base_block_number(self, db):
        """Test generating blocks with custom base block number."""
        service = BlockService(db)
        start = date(2025, 9, 1)
        end = date(2025, 9, 3)

        result = service.generate_blocks(start, end, base_block_number=100)

        assert all(block.block_number == 100 for block in result["items"])

    def test_generate_blocks_block_number_increments_every_28_days(self, db):
        """Test that block number increments every 28 days (4 weeks)."""
        service = BlockService(db)
        start = date(2025, 1, 1)
        end = date(2025, 2, 10)  # More than 28 days

        result = service.generate_blocks(start, end, base_block_number=1)

        # Get blocks from days 1-27 (should be block 1)
        early_blocks = [
            b for b in result["items"] if b.date < start + timedelta(days=28)
        ]
        assert all(b.block_number == 1 for b in early_blocks)

        # Get blocks from day 28+ (should be block 2)
        later_blocks = [
            b for b in result["items"] if b.date >= start + timedelta(days=28)
        ]
        assert all(b.block_number == 2 for b in later_blocks)

    # ========================================================================
    # Delete Block Tests
    # ========================================================================

    def test_delete_block_success(self, db, sample_block):
        """Test deleting a block successfully."""
        block_id = sample_block.id

        service = BlockService(db)
        result = service.delete_block(block_id)

        assert result["success"] is True
        assert result["error"] is None

        # Verify deletion
        db_block = db.query(Block).filter(Block.id == block_id).first()
        assert db_block is None

    def test_delete_block_not_found(self, db):
        """Test deleting a non-existent block returns error."""
        service = BlockService(db)
        result = service.delete_block(uuid4())

        assert result["success"] is False
        assert result["error"] == "Block not found"

    def test_delete_block_am_leaves_pm(self, db):
        """Test deleting AM block doesn't affect PM block on same day."""
        block_date = date(2025, 10, 15)
        block_am = Block(
            id=uuid4(),
            date=block_date,
            time_of_day="AM",
            block_number=1,
        )
        block_pm = Block(
            id=uuid4(),
            date=block_date,
            time_of_day="PM",
            block_number=1,
        )
        db.add_all([block_am, block_pm])
        db.commit()

        service = BlockService(db)
        service.delete_block(block_am.id)

        # Verify AM is deleted
        db_am = db.query(Block).filter(Block.id == block_am.id).first()
        assert db_am is None

        # Verify PM still exists
        db_pm = db.query(Block).filter(Block.id == block_pm.id).first()
        assert db_pm is not None

    # ========================================================================
    # Edge Cases and Business Logic Tests
    # ========================================================================

    def test_create_block_weekend_edge_case_friday(self, db):
        """Test creating block on Friday (weekday 4) is not weekend."""
        service = BlockService(db)
        friday = date(2025, 1, 10)  # Friday
        assert friday.weekday() == 4

        result = service.create_block(
            block_date=friday,
            time_of_day="AM",
        )

        assert result["block"].is_weekend is False

    def test_create_block_weekend_edge_case_saturday(self, db):
        """Test creating block on Saturday (weekday 5) is weekend."""
        service = BlockService(db)
        saturday = date(2025, 1, 11)  # Saturday
        assert saturday.weekday() == 5

        result = service.create_block(
            block_date=saturday,
            time_of_day="AM",
        )

        assert result["block"].is_weekend is True

    def test_generate_blocks_empty_range(self, db):
        """Test generate_blocks with end date before start date."""
        service = BlockService(db)
        start = date(2025, 11, 15)
        end = date(2025, 11, 10)  # Before start

        result = service.generate_blocks(start, end)

        # Should create no blocks
        assert result["total"] == 0
        assert len(result["items"]) == 0

    def test_list_blocks_date_boundary_inclusive(self, db):
        """Test that date range filters are inclusive on both ends."""
        service = BlockService(db)

        # Create blocks on specific dates
        block1 = Block(
            id=uuid4(),
            date=date(2025, 12, 1),
            time_of_day="AM",
            block_number=1,
        )
        block2 = Block(
            id=uuid4(),
            date=date(2025, 12, 15),
            time_of_day="AM",
            block_number=1,
        )
        block3 = Block(
            id=uuid4(),
            date=date(2025, 12, 31),
            time_of_day="AM",
            block_number=1,
        )
        db.add_all([block1, block2, block3])
        db.commit()

        result = service.list_blocks(
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31),
        )

        # Should include all three (boundaries are inclusive)
        assert result["total"] == 3
