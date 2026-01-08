"""Absence controller for request/response handling."""

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.person import PersonRepository
from app.schemas.absence import (
    AbsenceCreate,
    AbsenceBulkApply,
    AbsenceBulkCreate,
    AbsenceBulkPreview,
    AbsenceResponse,
    AbsenceUpdate,
    AllResidentsAwayStatus,
    AwayAbsenceDetail,
    AwayFromProgramCheck,
    AwayFromProgramSummary,
    ThresholdStatus,
)
from app.services.absence_service import AbsenceService


class AbsenceController:
    """Controller for absence endpoints."""

    def __init__(self, db: Session):
        self.db = db
        self.service = AbsenceService(db)
        self.person_repo = PersonRepository(db)

    def list_absences(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        absence_type: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict:
        """List absences with optional filters and pagination.

        Args:
            start_date: Filter absences starting from this date
            end_date: Filter absences ending by this date
            person_id: Filter by specific person
            absence_type: Filter by absence type
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dict with items, total count, page, and page_size
        """
        # TODO: Update service layer to support pagination (page, page_size)
        # For now, fetch all and apply pagination at controller level
        result = self.service.list_absences(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
            absence_type=absence_type,
        )

        # Handle both list and dict returns from service
        if isinstance(result, dict):
            items = result.get("items", result.get("absences", []))
        else:
            items = result if result else []

        total = len(items)
        offset = (page - 1) * page_size
        paginated_items = items[offset : offset + page_size]

        return {
            "items": paginated_items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_absence(self, absence_id: UUID) -> AbsenceResponse:
        """Get a single absence by ID."""
        absence = self.service.get_absence(absence_id)
        if not absence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Absence not found",
            )
        return absence

    def create_absence(self, absence_in: AbsenceCreate) -> AbsenceResponse:
        """Create a new absence."""
        result = self.service.create_absence(
            person_id=absence_in.person_id,
            start_date=absence_in.start_date,
            end_date=absence_in.end_date,
            absence_type=absence_in.absence_type,
            replacement_activity=getattr(absence_in, "replacement_activity", None),
            deployment_orders=getattr(absence_in, "deployment_orders", False),
            tdy_location=getattr(absence_in, "tdy_location", None),
            notes=getattr(absence_in, "notes", None),
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"],
            )

        return result["absence"]

    def update_absence(
        self,
        absence_id: UUID,
        absence_in: AbsenceUpdate,
    ) -> AbsenceResponse:
        """Update an absence."""
        update_data = absence_in.model_dump(exclude_unset=True)

        result = self.service.update_absence(
            absence_id=absence_id,
            update_data=update_data,
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

        return result["absence"]

    def delete_absence(self, absence_id: UUID) -> None:
        """Delete an absence."""
        result = self.service.delete_absence(absence_id)
        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"],
            )

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    def preview_bulk_absences(self, bulk_data: AbsenceBulkCreate) -> AbsenceBulkPreview:
        """Preview bulk absences before applying.

        Validates all absences and returns a preview with valid entries,
        validation errors, and summary statistics.

        Args:
            bulk_data: AbsenceBulkCreate with list of absences.

        Returns:
            AbsenceBulkPreview with validation results and summary.
        """
        return self.service.preview_bulk_absences(bulk_data)

    def apply_bulk_absences(self, bulk_data: AbsenceBulkCreate) -> AbsenceBulkApply:
        """Apply bulk absences after validation.

        Creates all valid absences, skipping those with conflicts.

        Args:
            bulk_data: AbsenceBulkCreate with list of absences.

        Returns:
            AbsenceBulkApply with created count, skipped count, and errors.
        """
        return self.service.apply_bulk_absences(bulk_data)

    # =========================================================================
    # Away-From-Program Tracking
    # =========================================================================

    def get_away_from_program_summary(
        self,
        person_id: UUID,
        academic_year: int | None = None,
    ) -> AwayFromProgramSummary:
        """Get away-from-program summary for a specific resident.

        Args:
            person_id: UUID of the resident.
            academic_year: Academic year start (e.g., 2025). Defaults to current.

        Returns:
            AwayFromProgramSummary with days used, remaining, status, and absences.

        Raises:
            HTTPException: If person not found.
        """
        # Verify person exists
        person = self.person_repo.get_by_id(person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found",
            )

        # Get academic year start date
        academic_year_start = None
        if academic_year:
            academic_year_start = date(academic_year, 7, 1)

        # Get summary from service
        summary = self.service.get_away_from_program_summary(
            person_id=person_id,
            academic_year_start=academic_year_start,
        )

        # Convert to Pydantic model
        return AwayFromProgramSummary(
            person_id=summary["person_id"],
            academic_year=summary["academic_year"],
            days_used=summary["days_used"],
            days_remaining=summary["days_remaining"],
            threshold_status=ThresholdStatus(summary["threshold_status"]),
            max_days=summary["max_days"],
            warning_days=summary["warning_days"],
            absences=[
                AwayAbsenceDetail(
                    id=a["id"],
                    start_date=a["start_date"],
                    end_date=a["end_date"],
                    absence_type=a["absence_type"],
                    days=a["days"],
                )
                for a in summary["absences"]
            ],
        )

    def check_away_threshold(
        self,
        person_id: UUID,
        additional_days: int = 0,
        academic_year: int | None = None,
    ) -> AwayFromProgramCheck:
        """Check away-from-program threshold for a person.

        Args:
            person_id: UUID of the person.
            additional_days: Days to add (for preview before creating absence).
            academic_year: Academic year start. Defaults to current.

        Returns:
            AwayFromProgramCheck with current/projected days and status.
        """
        # Verify person exists
        person = self.person_repo.get_by_id(person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Person not found",
            )

        academic_year_start = None
        if academic_year:
            academic_year_start = date(academic_year, 7, 1)

        result = self.service.check_away_threshold(
            person_id=person_id,
            additional_days=additional_days,
            academic_year_start=academic_year_start,
        )

        return AwayFromProgramCheck(
            current_days=result["current_days"],
            projected_days=result["projected_days"],
            threshold_status=ThresholdStatus(result["threshold_status"]),
            days_remaining=result["days_remaining"],
            max_days=result["max_days"],
            warning_days=result["warning_days"],
        )

    def get_all_residents_away_status(
        self,
        academic_year: int | None = None,
    ) -> AllResidentsAwayStatus:
        """Get away-from-program status for all residents (compliance dashboard).

        Args:
            academic_year: Academic year start. Defaults to current.

        Returns:
            AllResidentsAwayStatus with all residents' summaries.
        """
        academic_year_start = None
        if academic_year:
            academic_year_start = date(academic_year, 7, 1)
        else:
            academic_year_start, _ = self.service.get_academic_year_bounds()

        # Get all residents
        residents = self.person_repo.list_residents()

        summaries = []
        status_counts = {"ok": 0, "warning": 0, "critical": 0, "exceeded": 0}

        for resident in residents:
            summary = self.service.get_away_from_program_summary(
                person_id=resident.id,
                academic_year_start=academic_year_start,
            )

            summaries.append(
                AwayFromProgramSummary(
                    person_id=summary["person_id"],
                    academic_year=summary["academic_year"],
                    days_used=summary["days_used"],
                    days_remaining=summary["days_remaining"],
                    threshold_status=ThresholdStatus(summary["threshold_status"]),
                    max_days=summary["max_days"],
                    warning_days=summary["warning_days"],
                    absences=[
                        AwayAbsenceDetail(
                            id=a["id"],
                            start_date=a["start_date"],
                            end_date=a["end_date"],
                            absence_type=a["absence_type"],
                            days=a["days"],
                        )
                        for a in summary["absences"]
                    ],
                )
            )

            status_counts[summary["threshold_status"]] += 1

        return AllResidentsAwayStatus(
            academic_year=self.service.get_academic_year_label(academic_year_start),
            residents=summaries,
            summary={
                "total_residents": len(residents),
                "by_status": status_counts,
            },
        )
