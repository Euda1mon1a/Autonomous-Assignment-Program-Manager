"""Tests for BlockController."""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.block_controller import BlockController
from app.models.block import Block
from app.schemas.block import BlockCreate


class TestBlockController:
    """Test suite for BlockController."""

    # ========================================================================
    # List Blocks Tests
    # ========================================================================

    def test_list_blocks_no_filters(self, db, sample_blocks):
        """Test listing all blocks without filters."""
        controller = BlockController(db)
        result = controller.list_blocks()

        assert result.total >= len(sample_blocks)
        assert len(result.items) >= len(sample_blocks)

    def test_list_blocks_with_date_filter(self, db):
        """Test listing blocks with date range filter."""
        # Create blocks for specific dates
        start = date(2025, 1, 1)
        for i in range(5):
            block_date = start + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=block_date,
                time_of_day="AM",
                block_number=1,
                is_weekend=(block_date.weekday() >= 5),
            )
            db.add(block)
        db.commit()

        controller = BlockController(db)
        result = controller.list_blocks(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
        )

        # Should return blocks for Jan 1-3 (3 days, AM and PM = 6 blocks potentially)
        assert result.total >= 3

    def test_list_blocks_with_block_number_filter(self, db):
        """Test filtering blocks by block number."""
        # Create blocks with different block numbers
        block1 = Block(
            id=uuid4(),
            date=date.today(),
            time_of_day="AM",
            block_number=1,
        )
        block2 = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=30),
            time_of_day="AM",
            block_number=2,
        )
        db.add_all([block1, block2])
        db.commit()

        controller = BlockController(db)
        result = controller.list_blocks(block_number=1)

        assert result.total >= 1
        assert all(item.block_number == 1 for item in result.items)

    # ========================================================================
    # Get Block Tests
    # ========================================================================

    def test_get_block_success(self, db, sample_block):
        """Test getting a single block by ID."""
        controller = BlockController(db)
        block = controller.get_block(sample_block.id)

        assert block is not None
        assert block.id == sample_block.id
        assert block.date == sample_block.date
        assert block.time_of_day == sample_block.time_of_day

    def test_get_block_not_found(self, db):
        """Test getting a non-existent block raises 404."""
        controller = BlockController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_block(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    # ========================================================================
    # Create Block Tests
    # ========================================================================

    def test_create_block_success(self, db):
        """Test creating a block successfully."""
        controller = BlockController(db)

        block_data = BlockCreate(
            date=date.today() + timedelta(days=30),
            time_of_day="PM",
            block_number=1,
            is_weekend=False,
            is_holiday=False,
        )

        block = controller.create_block(block_data)

        assert block is not None
        assert block.date == block_data.date
        assert block.time_of_day == "PM"
        assert block.block_number == 1

    def test_create_block_minimal_data(self, db):
        """Test creating a block with minimal required fields."""
        controller = BlockController(db)

        block_data = BlockCreate(
            date=date.today() + timedelta(days=45),
            time_of_day="AM",
        )

        block = controller.create_block(block_data)

        assert block is not None
        assert block.date == block_data.date
        assert block.time_of_day == "AM"

    # ========================================================================
    # Generate Blocks Tests
    # ========================================================================

    def test_generate_blocks_single_day(self, db):
        """Test generating blocks for a single day."""
        controller = BlockController(db)

        start = date(2025, 6, 1)
        end = date(2025, 6, 1)

        result = controller.generate_blocks(
            start_date=start,
            end_date=end,
            base_block_number=1,
        )

        # Should create 2 blocks (AM and PM)
        assert result.total == 2
        assert len(result.items) == 2

    def test_generate_blocks_week(self, db):
        """Test generating blocks for one week."""
        controller = BlockController(db)

        start = date(2025, 7, 1)
        end = date(2025, 7, 7)

        result = controller.generate_blocks(
            start_date=start,
            end_date=end,
            base_block_number=1,
        )

        # 7 days * 2 blocks per day = 14 blocks
        assert result.total == 14
        assert len(result.items) == 14

    def test_generate_blocks_custom_block_number(self, db):
        """Test generating blocks with custom base block number."""
        controller = BlockController(db)

        start = date(2025, 8, 1)
        end = date(2025, 8, 1)

        result = controller.generate_blocks(
            start_date=start,
            end_date=end,
            base_block_number=5,
        )

        assert result.total == 2
        # All generated blocks should have block_number 5
        assert all(item.block_number == 5 for item in result.items)

    def test_generate_blocks_identifies_weekends(self, db):
        """Test that generated blocks correctly identify weekends."""
        controller = BlockController(db)

        # Generate blocks including a weekend
        # June 7, 2025 is a Saturday
        start = date(2025, 6, 6)  # Friday
        end = date(2025, 6, 8)  # Sunday

        result = controller.generate_blocks(
            start_date=start,
            end_date=end,
            base_block_number=1,
        )

        # Find weekend blocks
        weekend_blocks = [item for item in result.items if item.is_weekend]
        weekday_blocks = [item for item in result.items if not item.is_weekend]

        # Should have some weekend blocks (Sat, Sun = 4 blocks)
        assert len(weekend_blocks) == 4
        # And some weekday blocks (Fri = 2 blocks)
        assert len(weekday_blocks) == 2

    # ========================================================================
    # Delete Block Tests
    # ========================================================================

    def test_delete_block_success(self, db, sample_block):
        """Test deleting a block successfully."""
        controller = BlockController(db)

        block_id = sample_block.id
        controller.delete_block(block_id)

        # Verify deletion
        deleted = db.query(Block).filter(Block.id == block_id).first()
        assert deleted is None

    def test_delete_block_not_found(self, db):
        """Test deleting a non-existent block raises 404."""
        controller = BlockController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_block(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_create_get_delete_workflow(self, db):
        """Test complete create-get-delete workflow."""
        controller = BlockController(db)

        # Create
        block_data = BlockCreate(
            date=date(2025, 9, 15),
            time_of_day="AM",
            block_number=3,
        )
        created = controller.create_block(block_data)
        block_id = created.id

        # Get
        retrieved = controller.get_block(block_id)
        assert retrieved.id == block_id
        assert retrieved.date == date(2025, 9, 15)

        # Delete
        controller.delete_block(block_id)

        # Verify deletion
        with pytest.raises(HTTPException):
            controller.get_block(block_id)

    def test_generate_and_list_blocks(self, db):
        """Test generating blocks and then listing them."""
        controller = BlockController(db)

        # Generate blocks for 3 days
        start = date(2025, 10, 1)
        end = date(2025, 10, 3)

        gen_result = controller.generate_blocks(
            start_date=start,
            end_date=end,
            base_block_number=7,
        )

        assert gen_result.total == 6  # 3 days * 2 blocks

        # List blocks for that date range
        list_result = controller.list_blocks(
            start_date=start,
            end_date=end,
        )

        assert list_result.total >= 6
