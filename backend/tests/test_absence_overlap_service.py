"""Tests for Absence Overlap Detection Service.

Comprehensive test suite covering:
- Overlap type classification (exact, partial, contained, contains)
- Severity assessment
- Resolution options
- Batch detection
- Edge cases and boundary conditions
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.import_staging import ImportStagedAbsence, OverlapType
from app.models.person import Person
from app.services.absence_overlap_service import (
    AbsenceOverlapService,
    OverlapSeverity,
    check_absence_overlaps,
)


@pytest.fixture
def sample_faculty(db: Session) -> Person:
    """Create a sample faculty member."""
    faculty = Person(
        id=uuid4(),
        name="Dr. Test Faculty",
        type="faculty",
        email="faculty@hospital.org",
    )
    db.add(faculty)
    db.commit()
    return faculty


@pytest.fixture
def existing_vacation(db: Session, sample_faculty: Person) -> Absence:
    """Create an existing vacation absence."""
    absence = Absence(
        id=uuid4(),
        person_id=sample_faculty.id,
        start_date=date.today() + timedelta(days=10),
        end_date=date.today() + timedelta(days=17),
        absence_type="vacation",
        is_blocking=False,
    )
    db.add(absence)
    db.commit()
    return absence


@pytest.fixture
def existing_deployment(db: Session, sample_faculty: Person) -> Absence:
    """Create an existing deployment absence."""
    absence = Absence(
        id=uuid4(),
        person_id=sample_faculty.id,
        start_date=date.today() + timedelta(days=30),
        end_date=date.today() + timedelta(days=60),
        absence_type="deployment",
        is_blocking=True,
    )
    db.add(absence)
    db.commit()
    return absence


class TestOverlapTypeClassification:
    """Tests for overlap type classification logic."""

    def test_no_overlap_before(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test no overlap when new absence is before existing."""
        # Wrap sync session for async compatibility
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # New absence ends before existing starts
        new_start = date.today()
        new_end = date.today() + timedelta(days=5)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is False
        assert result.primary_overlap_type == OverlapType.NONE
        assert len(result.overlapping_absence_ids) == 0

    def test_no_overlap_after(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test no overlap when new absence is after existing."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # New absence starts after existing ends
        new_start = date.today() + timedelta(days=20)
        new_end = date.today() + timedelta(days=25)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is False
        assert result.primary_overlap_type == OverlapType.NONE

    def test_exact_overlap(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test exact overlap detection (identical dates)."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=existing_vacation.start_date,
                end_date=existing_vacation.end_date,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.EXACT
        assert len(result.overlap_details) == 1
        assert result.overlap_details[0].severity == OverlapSeverity.CRITICAL

    def test_contained_overlap(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test contained overlap (new is within existing)."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # New absence is fully within existing
        new_start = existing_vacation.start_date + timedelta(days=2)
        new_end = existing_vacation.end_date - timedelta(days=2)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.CONTAINED
        assert result.suggested_action == "skip"

    def test_contains_overlap(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test contains overlap (new contains existing)."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # New absence fully contains existing
        new_start = existing_vacation.start_date - timedelta(days=5)
        new_end = existing_vacation.end_date + timedelta(days=5)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.CONTAINS

    def test_partial_overlap_start(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test partial overlap at start of existing."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # New absence overlaps start of existing
        new_start = existing_vacation.start_date - timedelta(days=3)
        new_end = existing_vacation.start_date + timedelta(days=3)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.PARTIAL
        assert result.overlap_details[0].overlap_days == 4  # Day 0, 1, 2, 3

    def test_partial_overlap_end(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test partial overlap at end of existing."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # New absence overlaps end of existing
        new_start = existing_vacation.end_date - timedelta(days=2)
        new_end = existing_vacation.end_date + timedelta(days=5)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.PARTIAL
        assert result.overlap_details[0].overlap_days == 3  # Last 3 days of existing


class TestSeverityAssessment:
    """Tests for overlap severity assessment."""

    def test_exact_duplicate_is_critical(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test that exact duplicates are marked as critical."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=existing_vacation.start_date,
                end_date=existing_vacation.end_date,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.overlap_details[0].severity == OverlapSeverity.CRITICAL
        assert len(result.validation_errors) > 0

    def test_different_types_is_warning(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test that overlaps with different types are warnings."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # Same dates but different type
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=existing_vacation.start_date,
                end_date=existing_vacation.end_date,
                absence_type="conference",  # Different type
                person_name=sample_faculty.name,
            )
        )

        # Exact match with different type should still be critical
        assert result.overlap_details[0].severity == OverlapSeverity.CRITICAL


class TestResolutionOptions:
    """Tests for resolution option generation."""

    def test_exact_match_options(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test resolution options for exact match."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=existing_vacation.start_date,
                end_date=existing_vacation.end_date,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        options = result.overlap_details[0].resolution_options
        assert "skip" in options
        assert "replace" in options

    def test_partial_same_type_can_merge(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test that partial overlap of same type suggests merge."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # Partial overlap with same type
        new_start = existing_vacation.end_date - timedelta(days=2)
        new_end = existing_vacation.end_date + timedelta(days=5)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",  # Same type
                person_name=sample_faculty.name,
            )
        )

        assert result.can_auto_merge is True
        assert result.suggested_action == "merge"
        options = result.overlap_details[0].resolution_options
        assert "merge" in options


class TestMultipleOverlaps:
    """Tests for handling multiple overlapping absences."""

    def test_multiple_overlaps_detected(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
        existing_deployment: Absence,
    ):
        """Test detection of multiple overlaps."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # Create absence that spans both existing absences
        new_start = existing_vacation.start_date
        new_end = existing_deployment.end_date

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is True
        assert len(result.overlapping_absence_ids) == 2
        assert len(result.overlap_details) == 2


class TestExcludeAbsence:
    """Tests for excluding absences from overlap check."""

    def test_exclude_self_in_update(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test excluding self when updating an absence."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # When updating, exclude the absence being updated
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=existing_vacation.start_date,
                end_date=existing_vacation.end_date,
                absence_type="vacation",
                person_name=sample_faculty.name,
                exclude_absence_id=existing_vacation.id,  # Exclude self
            )
        )

        # Should not detect overlap with self
        assert result.has_overlap is False


class TestConvenienceFunction:
    """Tests for the convenience function."""

    def test_check_absence_overlaps_function(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test the convenience function for overlap checking."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            check_absence_overlaps(
                db=async_db,
                person_id=sample_faculty.id,
                start_date=existing_vacation.start_date,
                end_date=existing_vacation.end_date,
                absence_type="vacation",
            )
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.EXACT


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_day_overlap(
        self,
        client,
        db: Session,
        sample_faculty: Person,
        existing_vacation: Absence,
    ):
        """Test single day overlap at boundary."""
        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        # New absence ends on same day existing starts
        new_start = existing_vacation.start_date - timedelta(days=5)
        new_end = existing_vacation.start_date

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=new_start,
                end_date=new_end,
                absence_type="vacation",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is True
        assert result.overlap_details[0].overlap_days == 1

    def test_same_day_absence(
        self,
        client,
        db: Session,
        sample_faculty: Person,
    ):
        """Test single-day absence overlap detection."""
        # Create existing single-day absence
        single_day = Absence(
            id=uuid4(),
            person_id=sample_faculty.id,
            start_date=date.today() + timedelta(days=50),
            end_date=date.today() + timedelta(days=50),  # Same day
            absence_type="conference",
            is_blocking=False,
        )
        db.add(single_day)
        db.commit()

        from tests.conftest import AsyncSessionWrapper
        async_db = AsyncSessionWrapper(db)

        service = AbsenceOverlapService(async_db)

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            service.detect_overlaps(
                person_id=sample_faculty.id,
                start_date=single_day.start_date,
                end_date=single_day.end_date,
                absence_type="conference",
                person_name=sample_faculty.name,
            )
        )

        assert result.has_overlap is True
        assert result.primary_overlap_type == OverlapType.EXACT
        assert result.overlap_details[0].overlap_days == 1
