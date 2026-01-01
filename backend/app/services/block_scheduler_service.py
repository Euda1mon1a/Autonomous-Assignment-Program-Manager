"""Block scheduler service - leave-eligible rotation matching algorithm.

This service implements the core scheduling logic for academic blocks:
1. Residents with approved leave -> leave-eligible rotations
2. Remaining residents -> balanced coverage across all rotations
3. Coverage gaps identified for non-leave-eligible rotations

Key concept: Residents with approved leave get auto-assigned to
leave_eligible=True rotations so they don't disrupt FMIT/inpatient coverage.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.block_assignment import AssignmentReason, BlockAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.repositories.absence import AbsenceRepository
from app.repositories.block_assignment import BlockAssignmentRepository
from app.schemas.block_assignment import (
    AssignmentPreview,
    BlockAssignmentResponse,
    BlockScheduleResponse,
    BlockSchedulerDashboard,
    CoverageGap,
    LeaveConflict,
    ResidentInfo,
    ResidentLeaveInfo,
    RotationCapacity,
    RotationTemplateInfo,
)


@dataclass
class ResidentLeaveData:
    """Internal data structure for resident leave information."""

    resident: Person
    leave_days: int
    leave_types: list[str] = field(default_factory=list)
    absences: list[Absence] = field(default_factory=list)


@dataclass
class RotationSlot:
    """Internal data structure for rotation capacity tracking."""

    template: RotationTemplate
    max_capacity: int | None
    current_count: int = 0

    @property
    def available(self) -> int | None:
        """Get available slots (None if unlimited)."""
        if self.max_capacity is None:
            return None
        return max(0, self.max_capacity - self.current_count)

    @property
    def is_full(self) -> bool:
        """Check if rotation is at capacity."""
        if self.max_capacity is None:
            return False
        return self.current_count >= self.max_capacity


class BlockSchedulerService:
    """
    Service for scheduling residents to rotations per academic block.

    Priority order:
    1. Residents with approved leave -> leave-eligible rotations
    2. Remaining residents -> coverage needs first, then balanced distribution
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.assignment_repo = BlockAssignmentRepository(db)
        self.absence_repo = AbsenceRepository(db)

    def get_block_dates(
        self, block_number: int, academic_year: int
    ) -> tuple[date, date]:
        """
        Calculate the start and end dates for an academic block.

        Academic year starts July 1. Each block is 28 days.
        Block 0 is orientation (late June/early July).
        """
        # Academic year starts July 1
        year_start = date(academic_year, 7, 1)

        if block_number == 0:
            # Block 0 is orientation, typically last week of June
            start = year_start - timedelta(days=7)
            end = year_start - timedelta(days=1)
        else:
            # Regular blocks are 28 days each
            start = year_start + timedelta(days=(block_number - 1) * 28)
            end = start + timedelta(days=27)

        return start, end

    def get_residents_with_leave_in_block(
        self,
        block_number: int,
        academic_year: int,
    ) -> list[ResidentLeaveData]:
        """
        Get all residents who have approved leave during a block.

        Returns list of ResidentLeaveData with leave details.
        """
        start_date, end_date = self.get_block_dates(block_number, academic_year)

        # Get all residents
        residents = self.db.query(Person).filter(Person.type == "resident").all()

        residents_with_leave: list[ResidentLeaveData] = []

        for resident in residents:
            # Get absences that overlap with the block
            absences = self.absence_repo.get_by_person_and_date_range(
                resident.id, start_date, end_date
            )

            if absences:
                # Calculate total leave days in block
                leave_days = 0
                leave_types = set()

                for absence in absences:
                    # Calculate overlap with block
                    overlap_start = max(absence.start_date, start_date)
                    overlap_end = min(absence.end_date, end_date)
                    days = (overlap_end - overlap_start).days + 1
                    leave_days += days
                    leave_types.add(absence.absence_type)

                residents_with_leave.append(
                    ResidentLeaveData(
                        resident=resident,
                        leave_days=leave_days,
                        leave_types=list(leave_types),
                        absences=absences,
                    )
                )

        return residents_with_leave

    def get_rotation_capacities(
        self,
        block_number: int,
        academic_year: int,
    ) -> dict[UUID, RotationSlot]:
        """
        Get current capacity status for all rotations.

        Returns dict mapping rotation_template_id -> RotationSlot
        """
        # Get all rotation templates
        templates = self.db.query(RotationTemplate).all()

        capacities: dict[UUID, RotationSlot] = {}

        for template in templates:
            # Count current assignments
            current = self.assignment_repo.count_by_rotation(
                template.id, block_number, academic_year
            )

            capacities[template.id] = RotationSlot(
                template=template,
                max_capacity=template.max_residents,
                current_count=current,
            )

        return capacities

    def find_best_leave_eligible_rotation(
        self,
        resident: Person,
        capacities: dict[UUID, RotationSlot],
        already_assigned: set[UUID],
    ) -> RotationTemplate | None:
        """
        Find the best leave-eligible rotation for a resident with leave.

        Priority:
        1. Specialty match (if resident has specialty preferences)
        2. PGY level appropriateness
        3. Available capacity
        """
        candidates: list[tuple[RotationTemplate, int]] = []  # (template, score)

        for rotation_id, slot in capacities.items():
            # Skip if already assigned to this rotation
            if rotation_id in already_assigned:
                continue

            # Skip non-leave-eligible rotations
            if not slot.template.leave_eligible:
                continue

            # Skip if at capacity
            if slot.is_full:
                continue

            # Calculate match score
            score = 0

            # Prefer rotations with available capacity (not overcrowded)
            if slot.available is not None:
                score += slot.available * 10

            # Specialty match bonus
            if resident.specialties and slot.template.requires_specialty:
                if slot.template.requires_specialty in resident.specialties:
                    score += 50

            # PGY level consideration (some rotations may be better for certain levels)
            # For now, all PGY levels are treated equally

            candidates.append((slot.template, score))

        if not candidates:
            return None

        # Sort by score descending, return best match
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def find_best_coverage_rotation(
        self,
        resident: Person,
        capacities: dict[UUID, RotationSlot],
        already_assigned: set[UUID],
    ) -> RotationTemplate | None:
        """
        Find the best rotation for coverage needs.

        Priority:
        1. Non-leave-eligible rotations needing coverage (FMIT, inpatient)
        2. Rotations with fewer assignments (balance)
        3. Specialty match
        """
        candidates: list[tuple[RotationTemplate, int]] = []

        for rotation_id, slot in capacities.items():
            if rotation_id in already_assigned:
                continue

            if slot.is_full:
                continue

            score = 0

            # High priority for non-leave-eligible (coverage critical)
            if not slot.template.leave_eligible:
                score += 100

            # Prefer under-staffed rotations
            if slot.max_capacity and slot.current_count < slot.max_capacity:
                unfilled = slot.max_capacity - slot.current_count
                score += unfilled * 20

            # Specialty match bonus
            if resident.specialties and slot.template.requires_specialty:
                if slot.template.requires_specialty in resident.specialties:
                    score += 30

            candidates.append((slot.template, score))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def schedule_block(
        self,
        block_number: int,
        academic_year: int,
        dry_run: bool = True,
        include_all_residents: bool = True,
        created_by: str | None = None,
    ) -> BlockScheduleResponse:
        """
        Schedule all residents for a block.

        Algorithm:
        1. Get residents with leave in this block
        2. Assign residents with leave to leave-eligible rotations
        3. Assign remaining residents to balance coverage
        4. Validate and report gaps/conflicts
        """
        start_date, end_date = self.get_block_dates(block_number, academic_year)

        # Get all residents
        all_residents = self.db.query(Person).filter(Person.type == "resident").all()

        # Get leave data
        residents_with_leave = self.get_residents_with_leave_in_block(
            block_number, academic_year
        )
        leave_resident_ids = {r.resident.id for r in residents_with_leave}

        # Get capacity status
        capacities = self.get_rotation_capacities(block_number, academic_year)

        # Track assignments
        assignments: list[AssignmentPreview] = []
        assigned_rotations: set[UUID] = set()
        coverage_gaps: list[CoverageGap] = []
        leave_conflicts: list[LeaveConflict] = []
        assignment_records: list[dict] = []

        # Step 1: Assign residents with leave to leave-eligible rotations
        for leave_data in residents_with_leave:
            resident = leave_data.resident

            rotation = self.find_best_leave_eligible_rotation(
                resident, capacities, assigned_rotations
            )

            if rotation:
                # Track assignment
                if rotation.id in capacities:
                    capacities[rotation.id].current_count += 1

                preview = AssignmentPreview(
                    resident_id=resident.id,
                    resident_name=resident.name,
                    pgy_level=resident.pgy_level,
                    rotation_template_id=rotation.id,
                    rotation_name=rotation.name,
                    has_leave=True,
                    leave_days=leave_data.leave_days,
                    assignment_reason=AssignmentReason.LEAVE_ELIGIBLE_MATCH.value,
                    is_leave_eligible_rotation=rotation.leave_eligible,
                )
                assignments.append(preview)

                assignment_records.append(
                    {
                        "block_number": block_number,
                        "academic_year": academic_year,
                        "resident_id": resident.id,
                        "rotation_template_id": rotation.id,
                        "has_leave": True,
                        "leave_days": leave_data.leave_days,
                        "assignment_reason": AssignmentReason.LEAVE_ELIGIBLE_MATCH.value,
                        "created_by": created_by,
                    }
                )
            else:
                # No leave-eligible rotation available - conflict
                leave_conflicts.append(
                    LeaveConflict(
                        resident_id=resident.id,
                        resident_name=resident.name,
                        rotation_name="None available",
                        leave_days=leave_data.leave_days,
                        conflict_reason="No leave-eligible rotation with capacity",
                    )
                )

        # Step 2: Assign remaining residents (if requested)
        if include_all_residents:
            remaining_residents = [
                r for r in all_residents if r.id not in leave_resident_ids
            ]

            for resident in remaining_residents:
                rotation = self.find_best_coverage_rotation(
                    resident, capacities, assigned_rotations
                )

                if rotation:
                    if rotation.id in capacities:
                        capacities[rotation.id].current_count += 1

                    reason = (
                        AssignmentReason.COVERAGE_PRIORITY.value
                        if not rotation.leave_eligible
                        else AssignmentReason.BALANCED.value
                    )

                    preview = AssignmentPreview(
                        resident_id=resident.id,
                        resident_name=resident.name,
                        pgy_level=resident.pgy_level,
                        rotation_template_id=rotation.id,
                        rotation_name=rotation.name,
                        has_leave=False,
                        leave_days=0,
                        assignment_reason=reason,
                        is_leave_eligible_rotation=rotation.leave_eligible,
                    )
                    assignments.append(preview)

                    assignment_records.append(
                        {
                            "block_number": block_number,
                            "academic_year": academic_year,
                            "resident_id": resident.id,
                            "rotation_template_id": rotation.id,
                            "has_leave": False,
                            "leave_days": 0,
                            "assignment_reason": reason,
                            "created_by": created_by,
                        }
                    )

        # Step 3: Identify coverage gaps
        for rotation_id, slot in capacities.items():
            if slot.max_capacity and slot.current_count < slot.max_capacity:
                gap = slot.max_capacity - slot.current_count

                # Determine severity
                if not slot.template.leave_eligible:
                    severity = "critical" if gap > 1 else "warning"
                else:
                    severity = "info"

                coverage_gaps.append(
                    CoverageGap(
                        rotation_template_id=rotation_id,
                        rotation_name=slot.template.name,
                        required_coverage=slot.max_capacity,
                        assigned_coverage=slot.current_count,
                        gap=gap,
                        severity=severity,
                    )
                )

        # Step 4: Save if not dry run
        if not dry_run:
            # Clear existing assignments for this block
            self.assignment_repo.delete_block_assignments(block_number, academic_year)
            self.db.flush()

            # Create new assignments
            self.assignment_repo.bulk_create(assignment_records)
            self.db.commit()

        # Build rotation capacity response
        rotation_capacities = [
            RotationCapacity(
                rotation_template_id=slot.template.id,
                rotation_name=slot.template.name,
                leave_eligible=slot.template.leave_eligible,
                max_residents=slot.max_capacity,
                current_assigned=slot.current_count,
                available_slots=slot.available,
            )
            for slot in capacities.values()
        ]

        return BlockScheduleResponse(
            block_number=block_number,
            academic_year=academic_year,
            dry_run=dry_run,
            success=len(leave_conflicts) == 0,
            message=(
                "Preview generated"
                if dry_run
                else "Assignments saved successfully"
                if len(leave_conflicts) == 0
                else f"Completed with {len(leave_conflicts)} conflicts"
            ),
            assignments=assignments,
            total_residents=len(all_residents)
            if include_all_residents
            else len(residents_with_leave),
            residents_with_leave=len(residents_with_leave),
            coverage_gaps=[g for g in coverage_gaps if g.gap > 0],
            leave_conflicts=leave_conflicts,
            rotation_capacities=rotation_capacities,
        )

    def get_dashboard(
        self,
        block_number: int,
        academic_year: int,
    ) -> BlockSchedulerDashboard:
        """Get dashboard view for block scheduler UI."""
        start_date, end_date = self.get_block_dates(block_number, academic_year)

        # Get all residents
        all_residents = self.db.query(Person).filter(Person.type == "resident").all()

        # Get leave data
        residents_with_leave = self.get_residents_with_leave_in_block(
            block_number, academic_year
        )

        # Get capacities
        capacities = self.get_rotation_capacities(block_number, academic_year)

        # Get current assignments
        current_assignments = self.assignment_repo.list_by_block(
            block_number, academic_year, include_relations=True
        )

        assigned_resident_ids = {a.resident_id for a in current_assignments}

        # Build response
        leave_info = [
            ResidentLeaveInfo(
                resident_id=ld.resident.id,
                resident_name=ld.resident.name,
                pgy_level=ld.resident.pgy_level,
                leave_days=ld.leave_days,
                leave_types=ld.leave_types,
            )
            for ld in residents_with_leave
        ]

        rotation_capacities = [
            RotationCapacity(
                rotation_template_id=slot.template.id,
                rotation_name=slot.template.name,
                leave_eligible=slot.template.leave_eligible,
                max_residents=slot.max_capacity,
                current_assigned=slot.current_count,
                available_slots=slot.available,
            )
            for slot in capacities.values()
        ]

        leave_eligible_count = sum(
            1 for slot in capacities.values() if slot.template.leave_eligible
        )

        assignment_responses = []
        for assignment in current_assignments:
            resident_info = None
            rotation_info = None

            if assignment.resident:
                resident_info = ResidentInfo(
                    id=assignment.resident.id,
                    name=assignment.resident.name,
                    pgy_level=assignment.resident.pgy_level,
                )

            if assignment.rotation_template:
                rotation_info = RotationTemplateInfo(
                    id=assignment.rotation_template.id,
                    name=assignment.rotation_template.name,
                    activity_type=assignment.rotation_template.activity_type,
                    leave_eligible=assignment.rotation_template.leave_eligible,
                )

            assignment_responses.append(
                BlockAssignmentResponse(
                    id=assignment.id,
                    block_number=assignment.block_number,
                    academic_year=assignment.academic_year,
                    resident_id=assignment.resident_id,
                    rotation_template_id=assignment.rotation_template_id,
                    has_leave=assignment.has_leave,
                    leave_days=assignment.leave_days,
                    assignment_reason=assignment.assignment_reason,
                    notes=assignment.notes,
                    created_by=assignment.created_by,
                    created_at=assignment.created_at,
                    updated_at=assignment.updated_at,
                    resident=resident_info,
                    rotation_template=rotation_info,
                )
            )

        return BlockSchedulerDashboard(
            block_number=block_number,
            academic_year=academic_year,
            block_start_date=start_date.isoformat(),
            block_end_date=end_date.isoformat(),
            total_residents=len(all_residents),
            residents_with_leave=leave_info,
            rotation_capacities=rotation_capacities,
            leave_eligible_rotations=leave_eligible_count,
            non_leave_eligible_rotations=len(capacities) - leave_eligible_count,
            current_assignments=assignment_responses,
            unassigned_residents=len(all_residents) - len(assigned_resident_ids),
        )

    def get_assignment(self, assignment_id: UUID) -> BlockAssignment | None:
        """Get a single assignment by ID."""
        return self.assignment_repo.get_by_id_with_relations(assignment_id)

    def update_assignment(
        self,
        assignment_id: UUID,
        update_data: dict,
    ) -> BlockAssignment | None:
        """Update a block assignment."""
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            return None

        # Mark as manual if rotation is changed
        if "rotation_template_id" in update_data:
            update_data["assignment_reason"] = AssignmentReason.MANUAL.value

        assignment = self.assignment_repo.update(assignment, update_data)
        self.assignment_repo.commit()
        self.assignment_repo.refresh(assignment)
        return assignment

    def delete_assignment(self, assignment_id: UUID) -> bool:
        """Delete a block assignment."""
        assignment = self.assignment_repo.get_by_id(assignment_id)
        if not assignment:
            return False

        self.assignment_repo.delete(assignment)
        self.assignment_repo.commit()
        return True

    def create_manual_assignment(
        self,
        block_number: int,
        academic_year: int,
        resident_id: UUID,
        rotation_template_id: UUID | None,
        created_by: str | None = None,
        notes: str | None = None,
    ) -> BlockAssignment:
        """Create a manual block assignment."""
        # Check for leave
        residents_with_leave = self.get_residents_with_leave_in_block(
            block_number, academic_year
        )
        leave_data = next(
            (r for r in residents_with_leave if r.resident.id == resident_id),
            None,
        )

        assignment_data = {
            "block_number": block_number,
            "academic_year": academic_year,
            "resident_id": resident_id,
            "rotation_template_id": rotation_template_id,
            "has_leave": leave_data is not None,
            "leave_days": leave_data.leave_days if leave_data else 0,
            "assignment_reason": AssignmentReason.MANUAL.value,
            "created_by": created_by,
            "notes": notes,
        }

        assignment = self.assignment_repo.create(assignment_data)
        self.assignment_repo.commit()
        self.assignment_repo.refresh(assignment)
        return assignment
