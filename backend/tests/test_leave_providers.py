"""Tests for leave provider package."""
import pytest
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from app.services.leave_providers import (
    LeaveProvider,
    LeaveRecord,
    DatabaseLeaveProvider,
    CSVLeaveProvider,
    LeaveProviderFactory,
)
from app.models.absence import Absence


class TestLeaveRecord:
    """Tests for LeaveRecord dataclass."""

    def test_create_record(self):
        """Test creating a leave record."""
        record = LeaveRecord(
            faculty_name="Dr. Smith",
            faculty_id="123",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            leave_type="vacation",
        )

        assert record.faculty_name == "Dr. Smith"
        assert record.faculty_id == "123"
        assert record.leave_type == "vacation"
        assert record.is_blocking is True  # Default

    def test_record_defaults(self):
        """Test record default values."""
        record = LeaveRecord(
            faculty_name="Dr. Smith",
            faculty_id=None,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            leave_type="conference",
        )

        assert record.faculty_id is None
        assert record.description is None
        assert record.is_blocking is True

    def test_non_blocking_record(self):
        """Test non-blocking leave record."""
        record = LeaveRecord(
            faculty_name="Dr. Smith",
            faculty_id=None,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            leave_type="conference",
            is_blocking=False,
        )

        assert record.is_blocking is False


class TestDatabaseLeaveProvider:
    """Tests for DatabaseLeaveProvider."""

    def test_init(self, db):
        """Test provider initialization."""
        provider = DatabaseLeaveProvider(db)
        assert provider.db == db
        assert provider.cache_ttl == 300  # Default

    def test_init_custom_ttl(self, db):
        """Test provider with custom cache TTL."""
        provider = DatabaseLeaveProvider(db, cache_ttl_seconds=600)
        assert provider.cache_ttl == 600

    def test_get_all_leave_empty(self, db):
        """Test getting leave when none exists."""
        provider = DatabaseLeaveProvider(db)
        records = provider.get_all_leave()
        assert records == []

    def test_get_all_leave_with_data(self, db, sample_faculty):
        """Test getting leave records."""
        # Create absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=14),
            absence_type="vacation",
            notes="Annual leave",
        )
        db.add(absence)
        db.commit()

        provider = DatabaseLeaveProvider(db)
        records = provider.get_all_leave()

        assert len(records) >= 1
        record = next(r for r in records if r.faculty_name == sample_faculty.name)
        assert record.leave_type == "vacation"

    def test_get_conflicts_blocking_only(self, db, sample_faculty):
        """Test get_conflicts returns only blocking records."""
        # Create non-blocking absence
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=14),
            absence_type="conference",
            is_blocking=False,
        )
        db.add(absence)
        db.commit()

        provider = DatabaseLeaveProvider(db)
        conflicts = provider.get_conflicts()

        # Non-blocking should not appear in conflicts
        non_blocking = [c for c in conflicts if c.faculty_name == sample_faculty.name]
        assert len(non_blocking) == 0

    def test_get_conflicts_date_range(self, db, sample_faculty):
        """Test filtering conflicts by date range."""
        # Create absence in next month
        absence = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=45),
            end_date=date.today() + timedelta(days=52),
            absence_type="vacation",
            is_blocking=True,
        )
        db.add(absence)
        db.commit()

        provider = DatabaseLeaveProvider(db)

        # Query for this week only
        conflicts = provider.get_conflicts(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
        )

        # Absence should not appear
        assert all(c.faculty_name != sample_faculty.name for c in conflicts)

    def test_sync_clears_cache(self, db):
        """Test sync method clears cache."""
        provider = DatabaseLeaveProvider(db)
        provider._cache = [LeaveRecord("Test", None, date.today(), date.today(), "vacation")]

        count = provider.sync()

        assert provider._cache is None
        assert count == 0  # No records in empty db


class TestLeaveProviderFactory:
    """Tests for LeaveProviderFactory."""

    def test_create_database_provider(self, db):
        """Test creating database provider."""
        provider = LeaveProviderFactory.create("database", db=db)
        assert isinstance(provider, DatabaseLeaveProvider)

    def test_create_csv_provider(self):
        """Test creating CSV provider."""
        provider = LeaveProviderFactory.create("csv", file_path=Path("/tmp/test.csv"))
        assert isinstance(provider, CSVLeaveProvider)

    def test_unknown_provider_type(self):
        """Test unknown provider type raises error."""
        with pytest.raises(ValueError, match="Unknown provider type"):
            LeaveProviderFactory.create("unknown")


class TestCSVLeaveProvider:
    """Tests for CSVLeaveProvider."""

    def test_init(self):
        """Test CSV provider initialization."""
        provider = CSVLeaveProvider(Path("/tmp/test.csv"))
        assert provider.file_path == Path("/tmp/test.csv")

    def test_get_all_leave_file_not_found(self):
        """Test graceful handling of missing file."""
        provider = CSVLeaveProvider(Path("/nonexistent/path.csv"))
        records = provider.get_all_leave()
        assert records == []
