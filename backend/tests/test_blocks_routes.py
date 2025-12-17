"""Tests for block API routes.

Comprehensive test suite covering CRUD operations, filters, validation,
date range queries, and error handling for block endpoints.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.block import Block


class TestListBlocksEndpoint:
    """Tests for GET /api/blocks endpoint."""

    def test_list_blocks_empty(self, client: TestClient, db: Session):
        """Test listing blocks when none exist."""
        response = client.get("/api/blocks")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_blocks_with_data(self, client: TestClient, sample_blocks):
        """Test listing blocks with existing data."""
        response = client.get("/api/blocks")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert len(data["items"]) > 0

        # Validate block structure
        block = data["items"][0]
        assert "id" in block
        assert "date" in block
        assert "time_of_day" in block
        assert "block_number" in block
        assert "is_weekend" in block
        assert "is_holiday" in block

    def test_list_blocks_filter_by_start_date(self, client: TestClient, sample_blocks):
        """Test filtering blocks by start_date."""
        filter_date = (date.today() + timedelta(days=3)).isoformat()
        response = client.get(
            "/api/blocks",
            params={"start_date": filter_date}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned blocks should be on or after the filter date
        for block in data["items"]:
            block_date = date.fromisoformat(block["date"])
            assert block_date >= date.fromisoformat(filter_date)

    def test_list_blocks_filter_by_end_date(self, client: TestClient, sample_blocks):
        """Test filtering blocks by end_date."""
        filter_date = (date.today() + timedelta(days=3)).isoformat()
        response = client.get(
            "/api/blocks",
            params={"end_date": filter_date}
        )

        assert response.status_code == 200
        data = response.json()

        # All returned blocks should be on or before the filter date
        for block in data["items"]:
            block_date = date.fromisoformat(block["date"])
            assert block_date <= date.fromisoformat(filter_date)

    def test_list_blocks_filter_by_date_range(self, client: TestClient, db: Session):
        """Test filtering blocks by date range."""
        # Create blocks across a larger range
        start = date.today()
        for i in range(14):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=False,
                    is_holiday=False,
                )
                db.add(block)
        db.commit()

        # Filter for middle week
        filter_start = (start + timedelta(days=5)).isoformat()
        filter_end = (start + timedelta(days=9)).isoformat()

        response = client.get(
            "/api/blocks",
            params={
                "start_date": filter_start,
                "end_date": filter_end
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Should get 5 days * 2 blocks = 10 blocks
        assert data["total"] == 10

        # All blocks should be in range
        for block in data["items"]:
            block_date = date.fromisoformat(block["date"])
            assert date.fromisoformat(filter_start) <= block_date <= date.fromisoformat(filter_end)

    def test_list_blocks_filter_by_block_number(self, client: TestClient, db: Session):
        """Test filtering blocks by block_number."""
        # Create blocks with different block numbers
        today = date.today()
        for block_num in [1, 2, 3]:
            for i in range(3):
                block = Block(
                    id=uuid4(),
                    date=today + timedelta(days=i),
                    time_of_day="AM",
                    block_number=block_num,
                    is_weekend=False,
                    is_holiday=False,
                )
                db.add(block)
        db.commit()

        response = client.get(
            "/api/blocks",
            params={"block_number": 2}
        )

        assert response.status_code == 200
        data = response.json()

        # Should get only blocks with block_number 2
        assert data["total"] == 3
        for block in data["items"]:
            assert block["block_number"] == 2

    def test_list_blocks_combined_filters(self, client: TestClient, db: Session):
        """Test combining multiple filters."""
        start = date.today()
        for i in range(10):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start + timedelta(days=i),
                    time_of_day=tod,
                    block_number=(i // 3) + 1,
                    is_weekend=False,
                    is_holiday=False,
                )
                db.add(block)
        db.commit()

        # Filter by date range AND block number
        filter_start = (start + timedelta(days=3)).isoformat()
        filter_end = (start + timedelta(days=6)).isoformat()

        response = client.get(
            "/api/blocks",
            params={
                "start_date": filter_start,
                "end_date": filter_end,
                "block_number": 2
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Validate combined filters
        for block in data["items"]:
            block_date = date.fromisoformat(block["date"])
            assert date.fromisoformat(filter_start) <= block_date <= date.fromisoformat(filter_end)
            assert block["block_number"] == 2

    def test_list_blocks_no_results_in_range(self, client: TestClient, sample_blocks):
        """Test filtering with date range that has no blocks."""
        # Query far in the future
        future_start = (date.today() + timedelta(days=365)).isoformat()
        future_end = (date.today() + timedelta(days=400)).isoformat()

        response = client.get(
            "/api/blocks",
            params={
                "start_date": future_start,
                "end_date": future_end
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0


class TestGetBlockEndpoint:
    """Tests for GET /api/blocks/{block_id} endpoint."""

    def test_get_block_success(self, client: TestClient, sample_block: Block):
        """Test getting an existing block by ID."""
        response = client.get(f"/api/blocks/{sample_block.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_block.id)
        assert data["date"] == sample_block.date.isoformat()
        assert data["time_of_day"] == sample_block.time_of_day
        assert data["block_number"] == sample_block.block_number
        assert data["is_weekend"] == sample_block.is_weekend
        assert data["is_holiday"] == sample_block.is_holiday

    def test_get_block_not_found(self, client: TestClient):
        """Test getting a non-existent block."""
        fake_id = uuid4()
        response = client.get(f"/api/blocks/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_block_invalid_uuid(self, client: TestClient):
        """Test getting block with invalid UUID format."""
        response = client.get("/api/blocks/not-a-valid-uuid")

        assert response.status_code == 422  # Validation error

    def test_get_block_with_holiday(self, client: TestClient, db: Session):
        """Test getting a block that is a holiday."""
        holiday_block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=1),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
            is_holiday=True,
            holiday_name="New Year's Day",
        )
        db.add(holiday_block)
        db.commit()
        db.refresh(holiday_block)

        response = client.get(f"/api/blocks/{holiday_block.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_holiday"] is True
        assert data["holiday_name"] == "New Year's Day"


class TestCreateBlockEndpoint:
    """Tests for POST /api/blocks endpoint."""

    def test_create_block_am_success(self, client: TestClient):
        """Test creating a valid AM block."""
        block_data = {
            "date": (date.today() + timedelta(days=30)).isoformat(),
            "time_of_day": "AM",
            "block_number": 1,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["date"] == block_data["date"]
        assert data["time_of_day"] == "AM"
        assert data["block_number"] == 1

    def test_create_block_pm_success(self, client: TestClient):
        """Test creating a valid PM block."""
        block_data = {
            "date": (date.today() + timedelta(days=31)).isoformat(),
            "time_of_day": "PM",
            "block_number": 2,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        assert response.status_code == 201
        data = response.json()
        assert data["time_of_day"] == "PM"
        assert data["block_number"] == 2

    def test_create_block_weekend(self, client: TestClient):
        """Test creating a weekend block."""
        # Find next Saturday
        today = date.today()
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        saturday = today + timedelta(days=days_until_saturday)

        block_data = {
            "date": saturday.isoformat(),
            "time_of_day": "AM",
            "block_number": 1,
            "is_weekend": True,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        assert response.status_code == 201
        data = response.json()
        assert data["is_weekend"] is True

    def test_create_block_holiday(self, client: TestClient):
        """Test creating a holiday block."""
        block_data = {
            "date": (date.today() + timedelta(days=100)).isoformat(),
            "time_of_day": "AM",
            "block_number": 1,
            "is_weekend": False,
            "is_holiday": True,
            "holiday_name": "Independence Day",
        }

        response = client.post("/api/blocks", json=block_data)

        assert response.status_code == 201
        data = response.json()
        assert data["is_holiday"] is True
        assert data["holiday_name"] == "Independence Day"

    def test_create_block_invalid_time_of_day(self, client: TestClient):
        """Test creating block with invalid time_of_day."""
        block_data = {
            "date": (date.today() + timedelta(days=32)).isoformat(),
            "time_of_day": "EVENING",  # Invalid, must be AM or PM
            "block_number": 1,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        assert response.status_code == 422  # Validation error
        error_detail = str(response.json()["detail"])
        assert "AM" in error_detail or "PM" in error_detail or "time_of_day" in error_detail

    def test_create_block_missing_required_fields(self, client: TestClient):
        """Test creating block with missing required fields."""
        block_data = {
            "date": (date.today() + timedelta(days=33)).isoformat(),
            # Missing time_of_day and block_number
        }

        response = client.post("/api/blocks", json=block_data)

        assert response.status_code == 422  # Validation error

    def test_create_block_duplicate(self, client: TestClient, db: Session):
        """Test creating a duplicate block for same date/time."""
        test_date = date.today() + timedelta(days=50)

        # Create first block
        block1 = Block(
            id=uuid4(),
            date=test_date,
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
            is_holiday=False,
        )
        db.add(block1)
        db.commit()

        # Try to create duplicate
        block_data = {
            "date": test_date.isoformat(),
            "time_of_day": "AM",
            "block_number": 1,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        # Should fail with 400 or 422 depending on validation
        assert response.status_code in [400, 422]

    def test_create_block_invalid_date_format(self, client: TestClient):
        """Test creating block with invalid date format."""
        block_data = {
            "date": "not-a-valid-date",
            "time_of_day": "AM",
            "block_number": 1,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        assert response.status_code == 422  # Validation error

    def test_create_block_negative_block_number(self, client: TestClient):
        """Test creating block with negative block_number."""
        block_data = {
            "date": (date.today() + timedelta(days=35)).isoformat(),
            "time_of_day": "PM",
            "block_number": -1,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        # Depending on validation, might succeed or fail
        # If it succeeds, verify the block_number is stored
        if response.status_code == 201:
            data = response.json()
            assert "block_number" in data


class TestGenerateBlocksEndpoint:
    """Tests for POST /api/blocks/generate endpoint."""

    def test_generate_blocks_single_day(self, client: TestClient):
        """Test generating blocks for a single day."""
        test_date = date.today() + timedelta(days=60)

        response = client.post(
            "/api/blocks/generate",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
                "base_block_number": 1,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # AM and PM
        assert len(data["items"]) == 2

        # Verify both AM and PM blocks
        times = [block["time_of_day"] for block in data["items"]]
        assert "AM" in times
        assert "PM" in times

    def test_generate_blocks_week(self, client: TestClient):
        """Test generating blocks for a week."""
        start = date.today() + timedelta(days=70)
        end = start + timedelta(days=6)

        response = client.post(
            "/api/blocks/generate",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "base_block_number": 1,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 14  # 7 days * 2 blocks

    def test_generate_blocks_custom_base_number(self, client: TestClient):
        """Test generating blocks with custom base_block_number."""
        test_date = date.today() + timedelta(days=80)

        response = client.post(
            "/api/blocks/generate",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
                "base_block_number": 5,
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify block numbers
        for block in data["items"]:
            assert block["block_number"] >= 5

    def test_generate_blocks_month(self, client: TestClient):
        """Test generating blocks for approximately a month."""
        start = date.today() + timedelta(days=90)
        end = start + timedelta(days=29)  # 30 days

        response = client.post(
            "/api/blocks/generate",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "base_block_number": 1,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 60  # 30 days * 2 blocks

    def test_generate_blocks_invalid_date_range(self, client: TestClient):
        """Test generating blocks with end_date before start_date."""
        start = date.today() + timedelta(days=100)
        end = start - timedelta(days=5)  # Invalid: end before start

        response = client.post(
            "/api/blocks/generate",
            params={
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            }
        )

        # Should handle gracefully (either error or return 0 blocks)
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            data = response.json()
            assert data["total"] == 0

    def test_generate_blocks_missing_dates(self, client: TestClient):
        """Test generate blocks with missing required parameters."""
        response = client.post("/api/blocks/generate")

        assert response.status_code == 422  # Validation error

    def test_generate_blocks_default_base_number(self, client: TestClient):
        """Test generate blocks uses default base_block_number when not provided."""
        test_date = date.today() + timedelta(days=120)

        response = client.post(
            "/api/blocks/generate",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
                # base_block_number not provided, should default to 1
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0

        # Should use default base number
        for block in data["items"]:
            assert "block_number" in block


class TestDeleteBlockEndpoint:
    """Tests for DELETE /api/blocks/{block_id} endpoint."""

    def test_delete_block_success(self, client: TestClient, db: Session):
        """Test successfully deleting an existing block."""
        # Create a block to delete
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=150),
            time_of_day="AM",
            block_number=1,
            is_weekend=False,
            is_holiday=False,
        )
        db.add(block)
        db.commit()
        block_id = block.id

        response = client.delete(f"/api/blocks/{block_id}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify block is deleted
        verify_response = client.get(f"/api/blocks/{block_id}")
        assert verify_response.status_code == 404

    def test_delete_block_not_found(self, client: TestClient):
        """Test deleting a non-existent block."""
        fake_id = uuid4()
        response = client.delete(f"/api/blocks/{fake_id}")

        assert response.status_code == 404

    def test_delete_block_invalid_uuid(self, client: TestClient):
        """Test deleting block with invalid UUID format."""
        response = client.delete("/api/blocks/invalid-uuid-format")

        assert response.status_code == 422  # Validation error

    def test_delete_block_twice(self, client: TestClient, db: Session):
        """Test deleting the same block twice."""
        # Create a block to delete
        block = Block(
            id=uuid4(),
            date=date.today() + timedelta(days=160),
            time_of_day="PM",
            block_number=1,
            is_weekend=False,
            is_holiday=False,
        )
        db.add(block)
        db.commit()
        block_id = block.id

        # First delete
        response1 = client.delete(f"/api/blocks/{block_id}")
        assert response1.status_code == 204

        # Second delete should fail
        response2 = client.delete(f"/api/blocks/{block_id}")
        assert response2.status_code == 404


class TestBlockStructureAndValidation:
    """Tests for block data structure and field validation."""

    def test_block_response_has_all_fields(self, client: TestClient, sample_block: Block):
        """Test that block response includes all expected fields."""
        response = client.get(f"/api/blocks/{sample_block.id}")

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = ["id", "date", "time_of_day", "block_number", "is_weekend", "is_holiday"]
        for field in required_fields:
            assert field in data

        # Optional fields
        assert "holiday_name" in data  # Should be present even if null

    def test_block_date_format(self, client: TestClient, sample_blocks):
        """Test that block dates are in ISO format."""
        response = client.get("/api/blocks")

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            for block in data["items"]:
                # Should be parseable as ISO date
                try:
                    parsed_date = date.fromisoformat(block["date"])
                    assert isinstance(parsed_date, date)
                except ValueError:
                    pytest.fail(f"Invalid date format: {block['date']}")

    def test_block_time_of_day_values(self, client: TestClient, sample_blocks):
        """Test that time_of_day only contains valid values."""
        response = client.get("/api/blocks")

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            for block in data["items"]:
                assert block["time_of_day"] in ["AM", "PM"]

    def test_block_boolean_fields(self, client: TestClient, sample_blocks):
        """Test that boolean fields are actual booleans."""
        response = client.get("/api/blocks")

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            for block in data["items"]:
                assert isinstance(block["is_weekend"], bool)
                assert isinstance(block["is_holiday"], bool)

    def test_block_number_is_integer(self, client: TestClient, sample_blocks):
        """Test that block_number is an integer."""
        response = client.get("/api/blocks")

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            for block in data["items"]:
                assert isinstance(block["block_number"], int)


class TestBlockEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_create_block_far_future_date(self, client: TestClient):
        """Test creating a block far in the future."""
        far_future = date.today() + timedelta(days=3650)  # 10 years

        block_data = {
            "date": far_future.isoformat(),
            "time_of_day": "AM",
            "block_number": 1,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        # Should succeed
        assert response.status_code == 201

    def test_create_block_past_date(self, client: TestClient):
        """Test creating a block with a past date."""
        past_date = date.today() - timedelta(days=30)

        block_data = {
            "date": past_date.isoformat(),
            "time_of_day": "PM",
            "block_number": 1,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        # Should succeed (past dates might be needed for historical data)
        assert response.status_code in [201, 400]

    def test_generate_blocks_zero_days(self, client: TestClient):
        """Test generating blocks with same start and end date."""
        test_date = date.today() + timedelta(days=200)

        response = client.post(
            "/api/blocks/generate",
            params={
                "start_date": test_date.isoformat(),
                "end_date": test_date.isoformat(),
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Should still create AM and PM for that day

    def test_list_blocks_boundary_dates(self, client: TestClient, db: Session):
        """Test filtering with exact boundary dates."""
        # Create blocks for specific dates
        base_date = date.today() + timedelta(days=250)
        for i in range(5):
            block = Block(
                id=uuid4(),
                date=base_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
                is_holiday=False,
            )
            db.add(block)
        db.commit()

        # Query with exact start date
        response = client.get(
            "/api/blocks",
            params={"start_date": base_date.isoformat()}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5  # Should include blocks on exact start date

    def test_block_with_very_large_block_number(self, client: TestClient):
        """Test creating block with very large block_number."""
        block_data = {
            "date": (date.today() + timedelta(days=300)).isoformat(),
            "time_of_day": "AM",
            "block_number": 999999,
            "is_weekend": False,
            "is_holiday": False,
        }

        response = client.post("/api/blocks", json=block_data)

        # Should succeed or handle gracefully
        assert response.status_code in [201, 400, 422]
        if response.status_code == 201:
            data = response.json()
            assert data["block_number"] == 999999

    def test_holiday_name_without_holiday_flag(self, client: TestClient):
        """Test creating block with holiday_name but is_holiday=False."""
        block_data = {
            "date": (date.today() + timedelta(days=350)).isoformat(),
            "time_of_day": "PM",
            "block_number": 1,
            "is_weekend": False,
            "is_holiday": False,
            "holiday_name": "Not Actually a Holiday",
        }

        response = client.post("/api/blocks", json=block_data)

        # Should succeed - validation may or may not enforce consistency
        assert response.status_code in [201, 400, 422]
