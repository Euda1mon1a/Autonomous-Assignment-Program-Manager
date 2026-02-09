"""Tests for absence overlap detection service."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.absence import Absence
from app.models.person import Person
from app.models.import_staging import ImportStagedAbsence
from app.services.absence_overlap_service import (
    AbsenceOverlapService,
    OverlapDetectionResult,
    OverlapType,
    OverlapSeverity,
    check_absence_overlaps,
)


@pytest.fixture
def absence_overlap_service(db: Session) -> AbsenceOverlapService:
    """Create absence overlap service fixture."""
    return AbsenceOverlapService(db)


@pytest_asyncio.fixture
async def async_absence_overlap_service(async_db: AsyncSession) -> AbsenceOverlapService:
    """Create async absence overlap service fixture."""
    return AbsenceOverlapService(async_db)


@pytest.fixture
def test_person(db: Session) -> Person:
    """Create a test person."""
    person = Person(
        id=uuid4(),
        name="John Doe",
        email="john.doe@example.com",
        type="resident",
        pgy_level=1,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@pytest.fixture
def test_person2(db: Session) -> Person:
    """Create a second test person."""
    person = Person(
        id=uuid4(),
        name="Jane Smith",
        email="jane.smith@example.com",
        type="resident",
        pgy_level=2,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


class TestAbsenceOverlapService:
    """Test cases for AbsenceOverlapService."""

    def test_no_overlap_when_different_persons(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person, test_person2: Person
    ) -> None:
        """Test that absences for different people don't overlap."""
        # Create absence for person1
        absence1 = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence1)
        db.commit()

        # Check for person2 - should have no overlap
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person2.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )

        assert result.has_overlap is False
        assert len(result.overlapping_absence_ids) == 0

    def test_exact_overlap_detection(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test detection of exact duplicate absences."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check exact same date range
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        assert len(result.overlapping_absence_ids) == 1
        assert result.primary_overlap_type == OverlapType.EXACT
        assert result.suggested_action == "skip"

    def test_partial_overlap_detection(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test detection of partial date range overlap."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check partial overlap (starts before, ends during)
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.PARTIAL
        assert result.total_overlap_days > 0

    def test_contained_overlap_detection(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test detection when new absence is fully within existing."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 20),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check new absence fully contained within existing
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.CONTAINED
        assert result.suggested_action == "skip"

    def test_contains_overlap_detection(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test detection when new absence fully contains existing."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check new absence fully contains existing
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 20),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.CONTAINS

    def test_no_overlap_when_no_dates_overlap(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test that non-overlapping date ranges are correctly identified."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check non-overlapping date range (after)
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 15),
            end_date=date(2025, 3, 20),
            absence_type="vacation",
        )

        assert result.has_overlap is False
        assert len(result.overlapping_absence_ids) == 0

    def test_severity_assessment_exact_duplicate(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test severity assessment for exact duplicates."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check exact same date range
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        # Should have at least one critical severity for exact match
        critical_found = any(
            d.severity == OverlapSeverity.CRITICAL for d in result.overlap_details
        )
        assert critical_found is True

    def test_severity_assessment_different_types(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test severity assessment for different absence types."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check partial overlap with different type
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 10),
            end_date=date(2025, 3, 20),
            absence_type="tdy",
        )

        assert result.has_overlap is True
        # Different types with partial overlap should be warning, not critical
        warning_found = any(
            d.severity == OverlapSeverity.WARNING for d in result.overlap_details
        )
        assert warning_found is True

    def test_resolution_options_for_exact_duplicate(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test resolution options for exact duplicates."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        assert "skip" in result.overlap_details[0].resolution_options
        assert "replace" in result.overlap_details[0].resolution_options

    def test_can_auto_merge_same_type_partial_overlap(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test auto-merge capability for same type partial overlap."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check partial overlap with same type
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        # Should be able to merge partial overlap of same type
        assert result.can_auto_merge is True

    def test_cannot_auto_merge_different_types(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test that different absence types cannot auto-merge."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check partial overlap with different type
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="tdy",
        )

        assert result.has_overlap is True
        # Different types cannot auto-merge
        assert result.can_auto_merge is False

    def test_exclude_absence_id_for_updates(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test excluding an absence when checking for overlaps (for updates)."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check for overlaps excluding the existing absence
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
            exclude_absence_id=absence.id,
        )

        assert result.has_overlap is False

    def test_detect_overlaps_for_staged_absence(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test detecting overlaps for a staged absence."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Create staged absence with matching person
        staged_absence = ImportStagedAbsence(
            id=uuid4(),
            person_name=test_person.name,
            matched_person_id=test_person.id,
            start_date=date(2025, 3, 10),
            end_date=date(2025, 3, 20),
            absence_type="vacation",
        )

        result = absence_overlap_service.detect_overlaps_for_staged_absence(staged_absence)

        assert result.has_overlap is True
        assert len(result.overlapping_absence_ids) == 1

    def test_detect_overlaps_for_staged_absence_no_person_match(
        self, absence_overlap_service: AbsenceOverlapService
    ) -> None:
        """Test detecting overlaps when person is not matched."""
        staged_absence = ImportStagedAbsence(
            id=uuid4(),
            person_name="Unknown Person",
            matched_person_id=None,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )

        result = absence_overlap_service.detect_overlaps_for_staged_absence(staged_absence)

        assert result.has_overlap is False
        assert len(result.validation_errors) > 0
        assert "Cannot check overlaps" in result.validation_errors[0]


class TestAbsenceOverlapServiceAsync:
    """Test cases for async AbsenceOverlapService methods."""

    @pytest.mark.asyncio
    async def test_async_detect_overlaps(
        self, async_absence_overlap_service: AbsenceOverlapService, db: Session
    ) -> None:
        """Test async detect_overlaps method."""
        # Create test person in async db
        from uuid import uuid4
        person = Person(
            id=uuid4(),
            name="Async Test Person",
            email="async@test.example.com",
            type="resident",
            pgy_level=1,
        )
        async_db = async_absence_overlap_service.db
        async_db.add(person)
        await async_db.commit()

        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        async_db.add(absence)
        await async_db.commit()

        # Check for overlaps
        result = await async_absence_overlap_service.detect_overlaps(
            person_id=person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        assert len(result.overlapping_absence_ids) == 1

    @pytest.mark.asyncio
    async def test_async_batch_detect_overlaps(
        self, async_absence_overlap_service: AbsenceOverlapService, db: Session
    ) -> None:
        """Test async batch_detect_overlaps method."""
        # Create test persons in async db
        person1 = Person(
            id=uuid4(),
            name="Person 1",
            email="person1@test.example.com",
            type="resident",
            pgy_level=1,
        )
        person2 = Person(
            id=uuid4(),
            name="Person 2",
            email="person2@test.example.com",
            type="resident",
            pgy_level=2,
        )
        async_db = async_absence_overlap_service.db
        async_db.add(person1)
        async_db.add(person2)
        await async_db.commit()

        # Create existing absences
        absence1 = Absence(
            id=uuid4(),
            person_id=person1.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        async_db.add(absence1)

        # Create staged absences
        staged1 = ImportStagedAbsence(
            id=uuid4(),
            person_name=person1.name,
            matched_person_id=person1.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )
        staged2 = ImportStagedAbsence(
            id=uuid4(),
            person_name=person2.name,
            matched_person_id=person2.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 5),
            absence_type="tdy",
        )

        # Batch detect overlaps
        results = await async_absence_overlap_service.batch_detect_overlaps([staged1, staged2])

        assert len(results) == 2
        assert results[0].has_overlap is True  # staged1 overlaps with absence1
        assert results[1].has_overlap is False  # staged2 doesn't overlap


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_check_absence_overlaps_function(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test the check_absence_overlaps convenience function."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        result = check_absence_overlaps(
            db=db,
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        assert len(result.overlapping_absence_ids) == 1

    def test_check_absence_overlaps_exclude(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test check_absence_overlaps with exclude parameter."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        result = check_absence_overlaps(
            db=db,
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
            exclude_absence_id=absence.id,
        )

        assert result.has_overlap is False


class TestOverlapTypeClassifications:
    """Test overlap type classification logic."""

    def test_overlap_type_classification_same_range(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test exact overlap classification."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check exact same range
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )

        assert result.primary_overlap_type == OverlapType.EXACT

    def test_overlap_type_classification_contained(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test contained overlap classification."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 20),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check new absence fully contained
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )

        assert result.primary_overlap_type == OverlapType.CONTAINED

    def test_overlap_type_classification_contains(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test contains overlap classification."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check new absence fully contains existing
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 20),
            absence_type="vacation",
        )

        assert result.primary_overlap_type == OverlapType.CONTAINS

    def test_overlap_type_classification_partial(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test partial overlap classification."""
        # Create existing absence
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        # Check partial overlap (start before, end after)
        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )

        assert result.primary_overlap_type == OverlapType.PARTIAL


class TestOverlapDetectionResult:
    """Test OverlapDetectionResult data structure."""

    def test_result_has_overlap_true(self, absence_overlap_service: AbsenceOverlapService, test_person: Person) -> None:
        """Test result structure when overlap exists."""
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 5),
            end_date=date(2025, 3, 15),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        assert len(result.overlapping_absence_ids) > 0
        assert len(result.overlap_details) > 0
        assert result.total_overlap_days > 0
        assert result.suggested_action in ["create", "skip", "merge", "extend", "replace"]

    def test_result_has_overlap_false(self, absence_overlap_service: AbsenceOverlapService, test_person: Person) -> None:
        """Test result structure when no overlap exists."""
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 15),
            end_date=date(2025, 3, 25),
            absence_type="vacation",
        )

        assert result.has_overlap is False
        assert len(result.overlapping_absence_ids) == 0
        assert len(result.overlap_details) == 0
        assert result.total_overlap_days == 0
        assert result.suggested_action == "create"

    def test_result_validation_errors_and_warnings(
        self, absence_overlap_service: AbsenceOverlapService, test_person: Person
    ) -> None:
        """Test validation errors and warnings in result."""
        absence = Absence(
            id=uuid4(),
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )
        db = absence_overlap_service.db
        db.add(absence)
        db.commit()

        result = absence_overlap_service.detect_overlaps(
            person_id=test_person.id,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 10),
            absence_type="vacation",
        )

        assert result.has_overlap is True
        # Critical overlaps should generate validation errors
        assert len(result.validation_errors) > 0
        assert len(result.validation_warnings) >= 0