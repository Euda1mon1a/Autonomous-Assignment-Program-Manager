"""Swap validation service."""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models.person import Person


@dataclass
class ValidationError:
    code: str
    message: str
    severity: str = "error"


@dataclass
class SwapValidationResult:
    valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]
    back_to_back_conflict: bool = False
    external_conflict: str | None = None
    call_cascade_affected: bool = False


class SwapValidationService:
    """Service for validating FMIT swap requests."""

    def __init__(self, db: Session):
        self.db = db

    def validate_swap(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
        target_week: date | None = None,
    ) -> SwapValidationResult:
        """Validate a proposed swap."""
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        back_to_back = False
        external_conflict = None

        source_faculty = self._get_faculty(source_faculty_id)
        target_faculty = self._get_faculty(target_faculty_id)

        if not source_faculty:
            errors.append(ValidationError("SOURCE_NOT_FOUND", "Source faculty not found"))
        if not target_faculty:
            errors.append(ValidationError("TARGET_NOT_FOUND", "Target faculty not found"))

        if errors:
            return SwapValidationResult(valid=False, errors=errors, warnings=warnings)

        # Check back-to-back conflicts
        target_weeks = self._get_faculty_fmit_weeks(target_faculty_id)
        if self._creates_back_to_back(target_weeks, source_week):
            back_to_back = True
            errors.append(ValidationError(
                "BACK_TO_BACK",
                f"Taking week {source_week} would create back-to-back FMIT for {target_faculty.name}"
            ))

        # Check external conflicts
        conflict = self._check_external_conflicts(target_faculty_id, source_week)
        if conflict:
            external_conflict = conflict
            errors.append(ValidationError(
                "EXTERNAL_CONFLICT",
                f"{target_faculty.name} has {conflict} conflict during week {source_week}"
            ))

        # Past date check
        if source_week < date.today():
            errors.append(ValidationError("PAST_DATE", f"Cannot swap past week {source_week}"))

        # Warning for imminent swaps
        if source_week < date.today() + timedelta(days=14):
            warnings.append(ValidationError(
                "IMMINENT_SWAP",
                f"Week {source_week} is within 2 weeks",
                severity="warning"
            ))

        return SwapValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            back_to_back_conflict=back_to_back,
            external_conflict=external_conflict,
            call_cascade_affected=True,
        )

    def _get_faculty(self, faculty_id: UUID) -> Optional["Person"]:
        from app.models.person import Person
        return self.db.query(Person).filter(Person.id == faculty_id, Person.type == "faculty").first()

    def _get_faculty_fmit_weeks(self, faculty_id: UUID) -> list[date]:
        return []  # Placeholder - needs schedule data source

    def _creates_back_to_back(self, existing_weeks: list[date], new_week: date) -> bool:
        from app.services.xlsx_import import has_back_to_back_conflict
        return has_back_to_back_conflict(sorted(existing_weeks + [new_week]))

    def _check_external_conflicts(self, faculty_id: UUID, week: date) -> str | None:
        from app.models.absence import Absence
        week_end = week + timedelta(days=6)
        conflict = self.db.query(Absence).filter(
            Absence.person_id == faculty_id,
            Absence.start_date <= week_end,
            Absence.end_date >= week,
            Absence.is_blocking,
        ).first()
        return conflict.absence_type if conflict else None
