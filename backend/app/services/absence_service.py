"""Absence service for business logic."""

from collections import defaultdict
from datetime import date
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.repositories.absence import AbsenceRepository
from app.schemas.absence import (
    AbsenceBulkApply,
    AbsenceBulkCreate,
    AbsenceBulkPreview,
    AbsenceCreate,
    AbsenceValidationError,
)


class AbsenceService:
    """Service for absence business logic."""

    def __init__(self, db: Session) -> None:
        """Initialize absence service.

        Args:
            db: Database session for absence operations.
        """
        self.db = db
        self.absence_repo = AbsenceRepository(db)

    def get_absence(self, absence_id: UUID) -> Absence | None:
        """Get a single absence by ID.

        Args:
            absence_id: UUID of the absence record.

        Returns:
            Absence object if found, None otherwise.
        """
        return self.absence_repo.get_by_id(absence_id)

    def list_absences(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        absence_type: str | None = None,
    ) -> dict:
        """List absences with optional filters.

        Args:
            start_date: Filter absences starting on or after this date.
            end_date: Filter absences ending on or before this date.
            person_id: Filter absences for a specific person.
            absence_type: Filter by absence type (e.g., 'TDY', 'Leave', 'Deployment').

        Returns:
            Dictionary with 'items' (list of Absence objects) and 'total' (count).
        """
        absences = self.absence_repo.list_with_filters(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            absence_type=absence_type,
        )
        return {"items": absences, "total": len(absences)}

    def create_absence(
        self,
        person_id: UUID,
        start_date: date,
        end_date: date,
        absence_type: str,
        replacement_activity: str | None = None,
        deployment_orders: bool = False,
        tdy_location: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Create a new absence record for leave, TDY, or deployment.

        Args:
            person_id: UUID of the person with the absence.
            start_date: First date of the absence.
            end_date: Last date of the absence (inclusive).
            absence_type: Type of absence ('Leave', 'TDY', 'Deployment', etc.).
            replacement_activity: Activity scheduled during absence (optional).
            deployment_orders: Whether this is a deployment with official orders.
            tdy_location: Location for TDY assignments (optional).
            notes: Additional notes about the absence.

        Returns:
            Dictionary with 'absence' (created Absence object) and 'error' (None if successful).
        """
        absence_data = {
            "person_id": person_id,
            "start_date": start_date,
            "end_date": end_date,
            "absence_type": absence_type,
        }
        if replacement_activity:
            absence_data["replacement_activity"] = replacement_activity
        if deployment_orders:
            absence_data["deployment_orders"] = deployment_orders
        if tdy_location:
            absence_data["tdy_location"] = tdy_location
        if notes:
            absence_data["notes"] = notes

        absence = self.absence_repo.create(absence_data)
        self.absence_repo.commit()
        self.absence_repo.refresh(absence)

        return {"absence": absence, "error": None}

    def update_absence(self, absence_id: UUID, update_data: dict) -> dict:
        """Update an existing absence record.

        Args:
            absence_id: UUID of the absence to update.
            update_data: Dictionary of fields to update.

        Returns:
            Dictionary with 'absence' (updated Absence object) and 'error' (None if successful,
            error message if absence not found).
        """
        absence = self.absence_repo.get_by_id(absence_id)
        if not absence:
            return {"absence": None, "error": "Absence not found"}

        absence = self.absence_repo.update(absence, update_data)
        self.absence_repo.commit()
        self.absence_repo.refresh(absence)

        return {"absence": absence, "error": None}

    def delete_absence(self, absence_id: UUID) -> dict:
        """Delete an absence record.

        Args:
            absence_id: UUID of the absence to delete.

        Returns:
            Dictionary with 'success' (bool) and 'error' (None if successful,
            error message if absence not found).
        """
        absence = self.absence_repo.get_by_id(absence_id)
        if not absence:
            return {"success": False, "error": "Absence not found"}

        self.absence_repo.delete(absence)
        self.absence_repo.commit()
        return {"success": True, "error": None}

    def is_person_absent(self, person_id: UUID, on_date: date) -> bool:
        """Check if a person has a blocking absence on a specific date.

        Args:
            person_id: UUID of the person to check.
            on_date: Date to check for absences.

        Returns:
            True if person has an absence covering this date, False otherwise.
        """
        return self.absence_repo.has_absence_on_date(person_id, on_date)

        # =========================================================================
        # Bulk Operations
        # =========================================================================

    def preview_bulk_absences(self, bulk_data: AbsenceBulkCreate) -> AbsenceBulkPreview:
        """Validate bulk absences and return a preview.

        Validates each absence in the list, checking for:
        - Schema validation errors
        - Duplicate absences (same person + overlapping dates)
        - Conflicts with existing absences

        Args:
            bulk_data: AbsenceBulkCreate containing list of absences.

        Returns:
            AbsenceBulkPreview with valid absences, errors, and summary.
        """
        valid_absences: list[AbsenceCreate] = []
        errors: list[AbsenceValidationError] = []

        # Track seen absences to detect duplicates within the batch
        seen_absences: dict[tuple, list[tuple[date, date]]] = defaultdict(list)

        for idx, absence in enumerate(bulk_data.absences):
            try:
                # Check for duplicates within the batch
                person_key = (str(absence.person_id), absence.absence_type)
                is_batch_duplicate = False

                for existing_start, existing_end in seen_absences[person_key]:
                    # Check for overlap
                    if (
                        absence.start_date <= existing_end
                        and absence.end_date >= existing_start
                    ):
                        errors.append(
                            AbsenceValidationError(
                                index=idx,
                                field="dates",
                                message=(
                                    f"Duplicate/overlapping absence in batch for person "
                                    f"{absence.person_id} ({absence.start_date} - {absence.end_date})"
                                ),
                                absence_data=absence.model_dump(mode="json"),
                            )
                        )
                        is_batch_duplicate = True
                        break

                if is_batch_duplicate:
                    continue

                    # Check for conflicts with existing absences in DB
                existing = self.absence_repo.get_by_person_and_date_range(
                    person_id=absence.person_id,
                    start_date=absence.start_date,
                    end_date=absence.end_date,
                )

                if existing:
                    errors.append(
                        AbsenceValidationError(
                            index=idx,
                            field="dates",
                            message=(
                                f"Conflict with existing absence(s) for person "
                                f"{absence.person_id}: dates overlap with {len(existing)} "
                                f"existing record(s)"
                            ),
                            absence_data=absence.model_dump(mode="json"),
                        )
                    )
                    continue

                    # Mark as seen
                seen_absences[person_key].append((absence.start_date, absence.end_date))
                valid_absences.append(absence)

            except ValidationError as e:
                # Pydantic validation error
                for error in e.errors():
                    errors.append(
                        AbsenceValidationError(
                            index=idx,
                            field=".".join(str(loc) for loc in error.get("loc", [])),
                            message=error.get("msg", "Validation error"),
                            absence_data=None,
                        )
                    )
            except Exception as e:
                errors.append(
                    AbsenceValidationError(
                        index=idx,
                        field=None,
                        message=str(e),
                        absence_data=None,
                    )
                )

                # Build summary
        summary = self._build_bulk_summary(valid_absences)

        return AbsenceBulkPreview(
            valid=valid_absences,
            errors=errors,
            summary=summary,
        )

    def apply_bulk_absences(self, bulk_data: AbsenceBulkCreate) -> AbsenceBulkApply:
        """Apply validated bulk absences.

        Creates absences for all valid entries, skipping those with conflicts.

        Args:
            bulk_data: AbsenceBulkCreate containing list of absences.

        Returns:
            AbsenceBulkApply with created count, skipped count, and errors.
        """
        created = 0
        skipped = 0
        errors: list[AbsenceValidationError] = []

        # First, run preview to get validation
        preview = self.preview_bulk_absences(bulk_data)

        # Record errors from preview
        errors.extend(preview.errors)
        skipped += len(preview.errors)

        # Create valid absences
        for idx, absence_create in enumerate(preview.valid):
            try:
                absence_data = {
                    "person_id": absence_create.person_id,
                    "start_date": absence_create.start_date,
                    "end_date": absence_create.end_date,
                    "absence_type": absence_create.absence_type,
                    "is_blocking": absence_create.is_blocking,
                    "return_date_tentative": absence_create.return_date_tentative,
                    "created_by_id": absence_create.created_by_id,
                    "deployment_orders": absence_create.deployment_orders,
                    "tdy_location": absence_create.tdy_location,
                    "replacement_activity": absence_create.replacement_activity,
                    "notes": absence_create.notes,
                }

                # Remove None values to use DB defaults
                absence_data = {k: v for k, v in absence_data.items() if v is not None}

                absence = self.absence_repo.create(absence_data)
                created += 1

            except Exception as e:
                # Find original index from bulk_data
                original_idx = self._find_original_index(
                    bulk_data.absences, absence_create
                )
                errors.append(
                    AbsenceValidationError(
                        index=original_idx if original_idx is not None else idx,
                        field=None,
                        message=f"Failed to create: {str(e)}",
                        absence_data=absence_create.model_dump(mode="json"),
                    )
                )
                skipped += 1

                # Commit all changes
        if created > 0:
            self.absence_repo.commit()

        return AbsenceBulkApply(
            created=created,
            skipped=skipped,
            errors=errors,
        )

    def _build_bulk_summary(self, absences: list[AbsenceCreate]) -> dict:
        """Build summary statistics for bulk absences.

        Args:
            absences: List of valid AbsenceCreate objects.

        Returns:
            Dictionary with summary statistics.
        """
        if not absences:
            return {
                "total_count": 0,
                "by_type": {},
                "unique_persons": 0,
                "date_range": None,
            }

        by_type: dict[str, int] = defaultdict(int)
        unique_persons: set[str] = set()
        min_date: date | None = None
        max_date: date | None = None

        for absence in absences:
            by_type[absence.absence_type] += 1
            unique_persons.add(str(absence.person_id))

            if min_date is None or absence.start_date < min_date:
                min_date = absence.start_date
            if max_date is None or absence.end_date > max_date:
                max_date = absence.end_date

        return {
            "total_count": len(absences),
            "by_type": dict(by_type),
            "unique_persons": len(unique_persons),
            "date_range": {
                "start": min_date.isoformat() if min_date else None,
                "end": max_date.isoformat() if max_date else None,
            },
        }

    def _find_original_index(
        self, original_list: list[AbsenceCreate], target: AbsenceCreate
    ) -> int | None:
        """Find the original index of an absence in the input list.

        Args:
            original_list: Original list of AbsenceCreate objects.
            target: Target AbsenceCreate to find.

        Returns:
            Index if found, None otherwise.
        """
        for idx, absence in enumerate(original_list):
            if (
                absence.person_id == target.person_id
                and absence.start_date == target.start_date
                and absence.end_date == target.end_date
                and absence.absence_type == target.absence_type
            ):
                return idx
        return None

        # =========================================================================
        # Away-From-Program Tracking
        # =========================================================================

        # Constants for away-from-program threshold

    AWAY_FROM_PROGRAM_MAX_DAYS = 28  # Days per academic year before training extension
    AWAY_FROM_PROGRAM_WARNING_DAYS = 21  # 75% threshold for warning

    def get_academic_year_bounds(
        self, target_date: date | None = None
    ) -> tuple[date, date]:
        """Get the academic year start and end dates.

        Academic year runs July 1 - June 30.

        Args:
            target_date: Date to determine academic year for. Defaults to today.

        Returns:
            Tuple of (start_date, end_date) for the academic year.
        """
        if target_date is None:
            target_date = date.today()

            # Academic year starts July 1
        if target_date.month >= 7:
            # We're in the second half of calendar year, so academic year started this July
            start = date(target_date.year, 7, 1)
            end = date(target_date.year + 1, 6, 30)
        else:
            # We're in the first half of calendar year, so academic year started last July
            start = date(target_date.year - 1, 7, 1)
            end = date(target_date.year, 6, 30)

        return start, end

    def get_academic_year_label(self, target_date: date | None = None) -> str:
        """Get the academic year label (e.g., '2025-2026').

        Args:
            target_date: Date to determine academic year for. Defaults to today.

        Returns:
            Academic year label string.
        """
        start, end = self.get_academic_year_bounds(target_date)
        return f"{start.year}-{end.year}"

    def get_away_from_program_days(
        self,
        person_id: UUID,
        academic_year_start: date | None = None,
        exclude_absence_id: UUID | None = None,
    ) -> int:
        """Calculate total away-from-program days for a person in an academic year.

        Only counts absences where is_away_from_program=True.
        Handles partial overlaps with academic year boundaries.

        Args:
            person_id: UUID of the person.
            academic_year_start: Start of academic year. Defaults to current year.
            exclude_absence_id: Optional absence ID to exclude (for edit scenarios).

        Returns:
            Total days away from program in the academic year.
        """
        if academic_year_start is None:
            academic_year_start, _ = self.get_academic_year_bounds()

            # Get academic year end
        academic_year_end = date(academic_year_start.year + 1, 6, 30)

        # Get all absences for this person that overlap with the academic year
        absences = self.absence_repo.list_with_filters(
            person_id=person_id,
            start_date=academic_year_start,
            end_date=academic_year_end,
        )

        total_days = 0
        for absence in absences:
            # Skip if not marked as away-from-program
            if not absence.is_away_from_program:
                continue

                # Skip if this is the excluded absence (for edit scenarios)
            if exclude_absence_id and absence.id == exclude_absence_id:
                continue

                # Calculate days within academic year bounds
            effective_start = max(absence.start_date, academic_year_start)
            effective_end = min(absence.end_date, academic_year_end)

            # Add 1 because both dates are inclusive
            days = (effective_end - effective_start).days + 1
            if days > 0:
                total_days += days

        return total_days

    def check_away_threshold(
        self,
        person_id: UUID,
        additional_days: int = 0,
        academic_year_start: date | None = None,
    ) -> dict:
        """Check away-from-program threshold status.

        Args:
            person_id: UUID of the person.
            additional_days: Days to add (for checking before creating new absence).
            academic_year_start: Start of academic year. Defaults to current year.

        Returns:
            Dictionary with:
            - current_days: Current away-from-program days
            - projected_days: Days after adding additional_days
            - threshold_status: 'ok', 'warning', 'critical', or 'exceeded'
            - days_remaining: Days remaining before limit
            - max_days: Maximum allowed days (28)
            - warning_days: Warning threshold (21)
        """
        current_days = self.get_away_from_program_days(
            person_id=person_id,
            academic_year_start=academic_year_start,
        )

        projected_days = current_days + additional_days

        # Determine status
        if projected_days > self.AWAY_FROM_PROGRAM_MAX_DAYS:
            status = "exceeded"
        elif projected_days >= self.AWAY_FROM_PROGRAM_MAX_DAYS:
            status = "critical"
        elif projected_days >= self.AWAY_FROM_PROGRAM_WARNING_DAYS:
            status = "warning"
        else:
            status = "ok"

        return {
            "current_days": current_days,
            "projected_days": projected_days,
            "threshold_status": status,
            "days_remaining": max(0, self.AWAY_FROM_PROGRAM_MAX_DAYS - current_days),
            "max_days": self.AWAY_FROM_PROGRAM_MAX_DAYS,
            "warning_days": self.AWAY_FROM_PROGRAM_WARNING_DAYS,
        }

    def get_away_from_program_summary(
        self,
        person_id: UUID,
        academic_year_start: date | None = None,
    ) -> dict:
        """Get full away-from-program summary for a person.

        Args:
            person_id: UUID of the person.
            academic_year_start: Start of academic year. Defaults to current year.

        Returns:
            Dictionary with full summary including absences.
        """
        if academic_year_start is None:
            academic_year_start, _ = self.get_academic_year_bounds()

        academic_year_end = date(academic_year_start.year + 1, 6, 30)

        # Get threshold info
        threshold_info = self.check_away_threshold(
            person_id=person_id,
            academic_year_start=academic_year_start,
        )

        # Get absences that contribute to away-from-program
        absences = self.absence_repo.list_with_filters(
            person_id=person_id,
            start_date=academic_year_start,
            end_date=academic_year_end,
        )

        contributing_absences = [
            {
                "id": str(a.id),
                "start_date": a.start_date.isoformat(),
                "end_date": a.end_date.isoformat(),
                "absence_type": a.absence_type,
                "days": (
                    min(a.end_date, academic_year_end)
                    - max(a.start_date, academic_year_start)
                ).days
                + 1,
            }
            for a in absences
            if a.is_away_from_program
        ]

        return {
            "person_id": str(person_id),
            "academic_year": self.get_academic_year_label(academic_year_start),
            "days_used": threshold_info["current_days"],
            "days_remaining": threshold_info["days_remaining"],
            "threshold_status": threshold_info["threshold_status"],
            "max_days": threshold_info["max_days"],
            "warning_days": threshold_info["warning_days"],
            "absences": contributing_absences,
        }
