"""Absence Overlap Detection Service.

Detects overlaps between staged absences and existing absences in the database.
Supports various overlap types for import staging workflow:
- EXACT: Identical person and date range
- PARTIAL: Date ranges overlap but are not identical
- CONTAINED: Staged absence is fully within an existing absence
- CONTAINS: Staged absence fully contains an existing absence

Used by:
- Import staging workflow for absence uploads
- Manual absence entry validation
- Bulk absence management
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.import_staging import ImportStagedAbsence, OverlapType

logger = get_logger(__name__)


class OverlapSeverity(str, Enum):
    """Severity level of an overlap."""

    INFO = "info"  # Minor overlap, informational
    WARNING = "warning"  # Overlap that may need attention
    CRITICAL = "critical"  # Significant overlap requiring resolution


@dataclass
class OverlapDetail:
    """Detailed information about a single overlap."""

    existing_absence_id: UUID
    overlap_type: OverlapType
    severity: OverlapSeverity
    existing_start_date: date
    existing_end_date: date
    existing_absence_type: str
    overlap_start_date: date  # Start of overlapping period
    overlap_end_date: date  # End of overlapping period
    overlap_days: int
    description: str
    person_name: str | None = None
    resolution_options: list[str] = field(default_factory=list)


@dataclass
class OverlapDetectionResult:
    """Result of overlap detection for a staged absence."""

    staged_absence_id: UUID | None
    person_id: UUID
    person_name: str
    staged_start_date: date
    staged_end_date: date
    staged_absence_type: str
    has_overlap: bool
    primary_overlap_type: OverlapType
    overlapping_absence_ids: list[UUID]
    overlap_details: list[OverlapDetail]
    total_overlap_days: int
    validation_errors: list[str]
    validation_warnings: list[str]
    can_auto_merge: bool = False  # Whether absences can be auto-merged
    suggested_action: str = "create"  # create, merge, skip, or extend


class AbsenceOverlapService:
    """
    Service for detecting overlaps between staged and existing absences.

    Provides comprehensive overlap detection with:
    - Multiple overlap type classification
    - Severity assessment
    - Resolution suggestions
    - Audit-friendly detailed results
    """

    def __init__(self, db: AsyncSession):
        """Initialize the service with database session."""
        self.db = db

    async def detect_overlaps(
        self,
        person_id: UUID,
        start_date: date,
        end_date: date,
        absence_type: str,
        person_name: str = "",
        staged_absence_id: UUID | None = None,
        exclude_absence_id: UUID | None = None,
    ) -> OverlapDetectionResult:
        """
        Detect overlaps with existing absences for a person and date range.

        Args:
            person_id: UUID of the person
            start_date: Start date of the absence to check
            end_date: End date of the absence to check
            absence_type: Type of absence being checked
            person_name: Name of person (for reporting)
            staged_absence_id: ID of staged absence (if applicable)
            exclude_absence_id: Exclude this absence from overlap check (for updates)

        Returns:
            OverlapDetectionResult with full overlap analysis
        """
        # Query existing absences that could overlap
        query = select(Absence).where(
            and_(
                Absence.person_id == person_id,
                # Date overlap condition: existing.start <= new.end AND existing.end >= new.start
                Absence.start_date <= end_date,
                Absence.end_date >= start_date,
            )
        )

        if exclude_absence_id:
            query = query.where(Absence.id != exclude_absence_id)

        result = await self.db.execute(query)
        existing_absences = result.scalars().all()

        # Analyze overlaps
        overlap_details = []
        overlapping_ids = []
        total_overlap_days = 0
        validation_errors = []
        validation_warnings = []

        for existing in existing_absences:
            overlap_type = self._classify_overlap(
                start_date, end_date, existing.start_date, existing.end_date
            )

            if overlap_type == OverlapType.NONE:
                continue

            # Calculate overlap period
            overlap_start = max(start_date, existing.start_date)
            overlap_end = min(end_date, existing.end_date)
            overlap_days = (overlap_end - overlap_start).days + 1
            total_overlap_days += overlap_days

            # Determine severity
            severity = self._assess_severity(
                overlap_type, absence_type, existing.absence_type
            )

            # Generate description
            description = self._generate_description(
                overlap_type, existing, overlap_start, overlap_end, overlap_days
            )

            # Generate resolution options
            resolution_options = self._get_resolution_options(
                overlap_type, absence_type, existing.absence_type
            )

            detail = OverlapDetail(
                existing_absence_id=existing.id,
                overlap_type=overlap_type,
                severity=severity,
                existing_start_date=existing.start_date,
                existing_end_date=existing.end_date,
                existing_absence_type=existing.absence_type,
                overlap_start_date=overlap_start,
                overlap_end_date=overlap_end,
                overlap_days=overlap_days,
                description=description,
                person_name=person_name,
                resolution_options=resolution_options,
            )

            overlap_details.append(detail)
            overlapping_ids.append(existing.id)

            # Add validation messages based on severity
            if severity == OverlapSeverity.CRITICAL:
                validation_errors.append(description)
            elif severity == OverlapSeverity.WARNING:
                validation_warnings.append(description)

        # Determine primary overlap type (most significant)
        primary_overlap_type = self._get_primary_overlap_type(overlap_details)

        # Determine if auto-merge is possible
        can_auto_merge = self._can_auto_merge(overlap_details, absence_type)

        # Suggest action
        suggested_action = self._suggest_action(
            primary_overlap_type, overlap_details, absence_type
        )

        return OverlapDetectionResult(
            staged_absence_id=staged_absence_id,
            person_id=person_id,
            person_name=person_name,
            staged_start_date=start_date,
            staged_end_date=end_date,
            staged_absence_type=absence_type,
            has_overlap=len(overlapping_ids) > 0,
            primary_overlap_type=primary_overlap_type,
            overlapping_absence_ids=overlapping_ids,
            overlap_details=overlap_details,
            total_overlap_days=total_overlap_days,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            can_auto_merge=can_auto_merge,
            suggested_action=suggested_action,
        )

    async def detect_overlaps_for_staged_absence(
        self,
        staged_absence: ImportStagedAbsence,
    ) -> OverlapDetectionResult:
        """
        Detect overlaps for a staged absence record.

        Convenience method that extracts data from ImportStagedAbsence model.

        Args:
            staged_absence: The staged absence to check

        Returns:
            OverlapDetectionResult with full overlap analysis
        """
        if not staged_absence.matched_person_id:
            # Cannot check overlaps without matched person
            return OverlapDetectionResult(
                staged_absence_id=staged_absence.id,
                person_id=UUID("00000000-0000-0000-0000-000000000000"),
                person_name=staged_absence.person_name,
                staged_start_date=staged_absence.start_date,
                staged_end_date=staged_absence.end_date,
                staged_absence_type=staged_absence.absence_type,
                has_overlap=False,
                primary_overlap_type=OverlapType.NONE,
                overlapping_absence_ids=[],
                overlap_details=[],
                total_overlap_days=0,
                validation_errors=["Cannot check overlaps: person not matched"],
                validation_warnings=[],
                can_auto_merge=False,
                suggested_action="create",
            )

        return await self.detect_overlaps(
            person_id=staged_absence.matched_person_id,
            start_date=staged_absence.start_date,
            end_date=staged_absence.end_date,
            absence_type=staged_absence.absence_type,
            person_name=staged_absence.person_name,
            staged_absence_id=staged_absence.id,
        )

    async def batch_detect_overlaps(
        self,
        staged_absences: list[ImportStagedAbsence],
    ) -> list[OverlapDetectionResult]:
        """
        Detect overlaps for multiple staged absences efficiently.

        Args:
            staged_absences: List of staged absences to check

        Returns:
            List of OverlapDetectionResult for each staged absence
        """
        results = []
        for staged in staged_absences:
            result = await self.detect_overlaps_for_staged_absence(staged)
            results.append(result)
        return results

    def _classify_overlap(
        self,
        new_start: date,
        new_end: date,
        existing_start: date,
        existing_end: date,
    ) -> OverlapType:
        """
        Classify the type of overlap between two date ranges.

        Args:
            new_start: Start of new/staged absence
            new_end: End of new/staged absence
            existing_start: Start of existing absence
            existing_end: End of existing absence

        Returns:
            OverlapType classification
        """
        # Check for exact match
        if new_start == existing_start and new_end == existing_end:
            return OverlapType.EXACT

        # Check if new is fully contained within existing
        if new_start >= existing_start and new_end <= existing_end:
            return OverlapType.CONTAINED

        # Check if new fully contains existing
        if new_start <= existing_start and new_end >= existing_end:
            return OverlapType.CONTAINS

        # Check for any overlap (partial)
        if new_start <= existing_end and new_end >= existing_start:
            return OverlapType.PARTIAL

        return OverlapType.NONE

    def _assess_severity(
        self,
        overlap_type: OverlapType,
        new_type: str,
        existing_type: str,
    ) -> OverlapSeverity:
        """
        Assess the severity of an overlap based on type and absence types.

        Args:
            overlap_type: Type of date overlap
            new_type: Absence type of new/staged absence
            existing_type: Absence type of existing absence

        Returns:
            OverlapSeverity level
        """
        # Exact duplicates are critical
        if overlap_type == OverlapType.EXACT:
            return OverlapSeverity.CRITICAL

        # Same absence type with significant overlap is critical
        if new_type == existing_type and overlap_type in (
            OverlapType.CONTAINED,
            OverlapType.CONTAINS,
        ):
            return OverlapSeverity.CRITICAL

        # Different types with overlap is a warning
        if overlap_type in (OverlapType.PARTIAL, OverlapType.CONTAINS):
            return OverlapSeverity.WARNING

        return OverlapSeverity.INFO

    def _generate_description(
        self,
        overlap_type: OverlapType,
        existing: Absence,
        overlap_start: date,
        overlap_end: date,
        overlap_days: int,
    ) -> str:
        """Generate human-readable description of the overlap."""
        descriptions = {
            OverlapType.EXACT: (
                f"Exact duplicate: existing {existing.absence_type} "
                f"from {existing.start_date} to {existing.end_date}"
            ),
            OverlapType.CONTAINED: (
                f"Fully within existing {existing.absence_type} "
                f"({existing.start_date} to {existing.end_date})"
            ),
            OverlapType.CONTAINS: (
                f"Fully contains existing {existing.absence_type} "
                f"({existing.start_date} to {existing.end_date})"
            ),
            OverlapType.PARTIAL: (
                f"Partial overlap with {existing.absence_type} "
                f"({overlap_days} days from {overlap_start} to {overlap_end})"
            ),
        }
        return descriptions.get(overlap_type, "Unknown overlap")

    def _get_resolution_options(
        self,
        overlap_type: OverlapType,
        new_type: str,
        existing_type: str,
    ) -> list[str]:
        """Get available resolution options for the overlap."""
        options = []

        if overlap_type == OverlapType.EXACT:
            options = ["skip", "replace"]
        elif overlap_type == OverlapType.CONTAINED:
            options = ["skip"]  # New is within existing, no need to add
        elif overlap_type == OverlapType.CONTAINS:
            if new_type == existing_type:
                options = ["replace", "extend_existing", "skip"]
            else:
                options = ["create_separate", "skip"]
        elif overlap_type == OverlapType.PARTIAL:
            if new_type == existing_type:
                options = ["merge", "create_separate", "skip"]
            else:
                options = ["create_separate", "skip"]

        return options

    def _get_primary_overlap_type(
        self,
        overlap_details: list[OverlapDetail],
    ) -> OverlapType:
        """Determine the most significant overlap type."""
        if not overlap_details:
            return OverlapType.NONE

        # Priority order: EXACT > CONTAINED > CONTAINS > PARTIAL
        priority = {
            OverlapType.EXACT: 4,
            OverlapType.CONTAINED: 3,
            OverlapType.CONTAINS: 2,
            OverlapType.PARTIAL: 1,
            OverlapType.NONE: 0,
        }

        return max(
            (d.overlap_type for d in overlap_details),
            key=lambda x: priority.get(x, 0),
        )

    def _can_auto_merge(
        self,
        overlap_details: list[OverlapDetail],
        new_type: str,
    ) -> bool:
        """Determine if absences can be automatically merged."""
        if not overlap_details:
            return False

        # Can only auto-merge if single overlap with same type and partial/contains
        if len(overlap_details) != 1:
            return False

        detail = overlap_details[0]
        if detail.existing_absence_type != new_type:
            return False

        if detail.overlap_type in (OverlapType.PARTIAL, OverlapType.CONTAINS):
            return True

        return False

    def _suggest_action(
        self,
        primary_overlap_type: OverlapType,
        overlap_details: list[OverlapDetail],
        new_type: str,
    ) -> str:
        """Suggest the best action based on overlap analysis."""
        if primary_overlap_type == OverlapType.NONE:
            return "create"

        if primary_overlap_type == OverlapType.EXACT:
            return "skip"

        if primary_overlap_type == OverlapType.CONTAINED:
            return "skip"

        if len(overlap_details) == 1:
            detail = overlap_details[0]
            if detail.existing_absence_type == new_type:
                if primary_overlap_type == OverlapType.CONTAINS:
                    return "extend"
                if primary_overlap_type == OverlapType.PARTIAL:
                    return "merge"

        return "create"  # Default to creating with manual review


async def check_absence_overlaps(
    db: AsyncSession,
    person_id: UUID,
    start_date: date,
    end_date: date,
    absence_type: str,
    person_name: str = "",
    exclude_absence_id: UUID | None = None,
) -> OverlapDetectionResult:
    """
    Convenience function to check absence overlaps.

    Args:
        db: Database session
        person_id: UUID of the person
        start_date: Start date of the absence
        end_date: End date of the absence
        absence_type: Type of absence
        person_name: Name of person (for reporting)
        exclude_absence_id: Exclude this absence from check (for updates)

    Returns:
        OverlapDetectionResult with full overlap analysis
    """
    service = AbsenceOverlapService(db)
    return await service.detect_overlaps(
        person_id=person_id,
        start_date=start_date,
        end_date=end_date,
        absence_type=absence_type,
        person_name=person_name,
        exclude_absence_id=exclude_absence_id,
    )
