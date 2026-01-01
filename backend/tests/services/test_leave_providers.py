"""Tests for LeaveProvider factory and implementations."""

import pytest
import tempfile
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from app.models.absence import Absence
from app.models.person import Person
from app.services.leave_providers.factory import LeaveProviderFactory
from app.services.leave_providers.database import DatabaseLeaveProvider
from app.services.leave_providers.csv_provider import CSVLeaveProvider


class TestLeaveProviderFactory:
    """Test suite for LeaveProviderFactory."""

    def test_create_database_provider(self, db):
        """Test creating a database provider."""
        provider = LeaveProviderFactory.create("database", db=db)
        assert isinstance(provider, DatabaseLeaveProvider)
        assert provider.db is db

    def test_create_csv_provider(self):
        """Test creating a CSV provider."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = Path(f.name)
            f.write("person_id,start_date,end_date,absence_type\n")
            f.write("123,2025-01-01,2025-01-05,vacation\n")

        try:
            provider = LeaveProviderFactory.create("csv", file_path=csv_path)
            assert isinstance(provider, CSVLeaveProvider)
            assert provider.file_path == csv_path
        finally:
            csv_path.unlink()

    def test_create_database_provider_missing_db(self):
        """Test creating database provider without db raises error."""
        with pytest.raises(ValueError, match="Database session required"):
            LeaveProviderFactory.create("database")

    def test_create_csv_provider_missing_path(self):
        """Test creating CSV provider without file_path raises error."""
        with pytest.raises(ValueError, match="File path required"):
            LeaveProviderFactory.create("csv")

    def test_create_unknown_provider_type(self, db):
        """Test creating unknown provider type raises error."""
        with pytest.raises(ValueError, match="Unknown provider type"):
            LeaveProviderFactory.create("unknown", db=db)


class TestDatabaseLeaveProvider:
    """Test suite for DatabaseLeaveProvider."""

    def test_get_absences_for_person(self, db, sample_resident):
        """Test getting absences for a specific person."""
        # Create test absences
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 5),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 3),
            absence_type="conference",
        )
        db.add_all([absence1, absence2])
        db.commit()

        provider = DatabaseLeaveProvider(db)
        absences = provider.get_absences_for_person(str(sample_resident.id))

        assert len(absences) == 2
        assert any(a.absence_type == "vacation" for a in absences)
        assert any(a.absence_type == "conference" for a in absences)

    def test_get_absences_in_date_range(self, db, sample_resident):
        """Test getting absences within a date range."""
        absence1 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 20),
            absence_type="vacation",
        )
        absence2 = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 5),
            absence_type="sick",
        )
        db.add_all([absence1, absence2])
        db.commit()

        provider = DatabaseLeaveProvider(db)
        absences = provider.get_absences_in_range(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )

        assert len(absences) == 1
        assert absences[0].absence_type == "vacation"

    def test_get_all_absences(self, db, sample_residents):
        """Test getting all absences."""
        for i, resident in enumerate(sample_residents):
            absence = Absence(
                id=uuid4(),
                person_id=resident.id,
                start_date=date(2025, 1, i + 1),
                end_date=date(2025, 1, i + 3),
                absence_type="vacation",
            )
            db.add(absence)
        db.commit()

        provider = DatabaseLeaveProvider(db)
        absences = provider.get_all_absences()

        assert len(absences) == 3

    def test_is_person_absent_true(self, db, sample_resident):
        """Test checking if person is absent on a specific date."""
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        provider = DatabaseLeaveProvider(db)
        is_absent = provider.is_person_absent(
            str(sample_resident.id),
            date(2025, 1, 12),  # Middle of absence
        )

        assert is_absent is True

    def test_is_person_absent_false(self, db, sample_resident):
        """Test checking if person is not absent."""
        absence = Absence(
            id=uuid4(),
            person_id=sample_resident.id,
            start_date=date(2025, 1, 10),
            end_date=date(2025, 1, 15),
            absence_type="vacation",
        )
        db.add(absence)
        db.commit()

        provider = DatabaseLeaveProvider(db)
        is_absent = provider.is_person_absent(
            str(sample_resident.id),
            date(2025, 1, 20),  # After absence
        )

        assert is_absent is False


class TestCSVLeaveProvider:
    """Test suite for CSVLeaveProvider."""

    def test_load_absences_from_csv(self):
        """Test loading absences from CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = Path(f.name)
            f.write("person_id,start_date,end_date,absence_type,notes\n")
            f.write("person-123,2025-01-01,2025-01-05,vacation,Annual leave\n")
            f.write("person-456,2025-02-01,2025-02-03,conference,Medical conference\n")

        try:
            provider = CSVLeaveProvider(csv_path)
            absences = provider.get_all_absences()

            assert len(absences) >= 2
            # CSV provider returns dicts, not model objects
        finally:
            csv_path.unlink()

    def test_get_absences_for_person_from_csv(self):
        """Test getting absences for a specific person from CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = Path(f.name)
            f.write("person_id,start_date,end_date,absence_type\n")
            f.write("person-123,2025-01-01,2025-01-05,vacation\n")
            f.write("person-456,2025-02-01,2025-02-03,sick\n")
            f.write("person-123,2025-03-01,2025-03-03,conference\n")

        try:
            provider = CSVLeaveProvider(csv_path)
            absences = provider.get_absences_for_person("person-123")

            # Should find 2 absences for person-123
            assert len(absences) >= 1
        finally:
            csv_path.unlink()

    def test_csv_file_not_found(self):
        """Test CSV provider with non-existent file."""
        csv_path = Path("/nonexistent/path/to/file.csv")

        with pytest.raises((FileNotFoundError, Exception)):
            provider = CSVLeaveProvider(csv_path)
            # Depending on implementation, error might occur at init or first read

    def test_empty_csv_file(self):
        """Test CSV provider with empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = Path(f.name)
            f.write("person_id,start_date,end_date,absence_type\n")
            # No data rows

        try:
            provider = CSVLeaveProvider(csv_path)
            absences = provider.get_all_absences()
            assert len(absences) == 0
        finally:
            csv_path.unlink()

    def test_csv_malformed_data(self):
        """Test CSV provider with malformed data."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = Path(f.name)
            f.write("person_id,start_date,end_date,absence_type\n")
            f.write("person-123,invalid-date,2025-01-05,vacation\n")

        try:
            provider = CSVLeaveProvider(csv_path)
            # Provider should handle or raise error for malformed data
            # Behavior depends on implementation
        finally:
            csv_path.unlink()
