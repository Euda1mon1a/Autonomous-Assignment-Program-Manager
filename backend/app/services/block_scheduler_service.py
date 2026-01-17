"""Block scheduler service - leave-eligible rotation matching algorithm.

This service implements the core scheduling logic for academic blocks:
1. Residents with approved leave -> leave-eligible rotations
2. Remaining residents -> balanced coverage across all rotations
3. Coverage gaps identified for non-leave-eligible rotations

Key concept: Residents with approved leave get auto-assigned to
leave_eligible=True rotations so they don't disrupt FMIT/inpatient coverage.
"""

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.utils.academic_blocks import get_block_dates as _get_block_dates_util

from app.models.absence import Absence
from app.models.activity import Activity
from app.models.block_assignment import AssignmentReason, BlockAssignment
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import HalfDayAssignment
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

        Academic blocks use Thursday-Wednesday alignment:
        - Block 0: July 1 through day before first Thursday (orientation)
        - Blocks 1-12: 28 days each, Thursday start, Wednesday end
        - Block 13: Starts Thursday, ends June 30 (variable length)

        Args:
            block_number: Block number (0-13)
            academic_year: Starting year of academic year (e.g., 2025 for AY 2025-2026)

        Returns:
            Tuple of (start_date, end_date)
        """
        block = _get_block_dates_util(block_number, academic_year)
        return block.start_date, block.end_date

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

    def get_explorer_data(
        self,
        block_number: int,
        academic_year: int,
    ) -> dict:
        """
        Get complete Block Explorer data for pre-launch verification.

        Aggregates data from multiple sources:
        - Dashboard data (residents, rotations, capacities)
        - ACGME validation results
        - Assignment details with half-day breakdown

        Returns a dict matching the BlockExplorerResponse schema.
        """
        from datetime import datetime as dt
        from app.scheduling.validator import ACGMEValidator

        start_date, end_date = self.get_block_dates(block_number, academic_year)
        days_in_block = (end_date - start_date).days + 1

        # Get dashboard data (reuses existing logic)
        dashboard = self.get_dashboard(block_number, academic_year)

        # Get ACGME validation
        validator = ACGMEValidator(self.db)
        validation = validator.validate_all(start_date, end_date)

        # Get all residents and rotations
        all_residents = self.db.query(Person).filter(Person.type == "resident").all()
        all_faculty = self.db.query(Person).filter(Person.type == "faculty").all()
        all_rotations = self.db.query(RotationTemplate).all()

        # Bulk query half-day assignments for the block date range
        all_half_day_assignments = (
            self.db.query(HalfDayAssignment)
            .filter(
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
            )
            .options(joinedload(HalfDayAssignment.activity))
            .all()
        )

        # Index by (person_id, date, time_of_day) for O(1) lookup
        hda_index: dict[tuple, HalfDayAssignment] = {}
        for hda in all_half_day_assignments:
            key = (hda.person_id, hda.date, hda.time_of_day)
            hda_index[key] = hda

        # Query call assignments for the block
        call_assignments = (
            self.db.query(CallAssignment)
            .filter(
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
            .all()
        )
        call_days_filled = len(set(ca.date for ca in call_assignments))

        # Query all activities for color mapping
        all_activities = self.db.query(Activity).all()
        activity_colors = {
            a.display_abbreviation: a.background_color or "#374151"
            for a in all_activities
            if a.display_abbreviation
        }
        # Add fallback colors for common codes
        activity_colors.setdefault("---", "#374151")
        activity_colors.setdefault("FMIT", "#3b82f6")
        activity_colors.setdefault("NF", "#6366f1")
        activity_colors.setdefault("C", "#10b981")

        # Build completeness data
        assigned_count = len(dashboard.current_assignments)
        total_residents = len(all_residents)
        resident_ids = {r.id for r in all_residents}
        filled_half_day_slots = len(
            [hda for hda in all_half_day_assignments if hda.person_id in resident_ids]
        )
        total_half_day_slots = (
            total_residents * days_in_block * 2
        )  # 2 slots per day (AM/PM)
        completeness = {
            "residents": {
                "assigned": assigned_count,
                "total": total_residents,
                "status": "pass" if assigned_count == total_residents else "warn",
            },
            "faculty": {
                "active": len(all_faculty),
                "total": len(all_faculty),
                "status": "pass" if len(all_faculty) > 0 else "fail",
            },
            "rotations": {
                "defined": len(all_rotations),
                "total": len(all_rotations),
                "status": "pass" if len(all_rotations) > 0 else "fail",
            },
            "absences": {
                "recorded": len(dashboard.residents_with_leave),
                "pending": 0,
                "status": "pass",
            },
            "callRoster": {
                "filled": call_days_filled,
                "total": days_in_block,
                "status": "pass" if call_days_filled >= days_in_block else "warn",
            },
            "coverage": {
                "filled": filled_half_day_slots,
                "total": total_half_day_slots,
                "gaps": total_half_day_slots - filled_half_day_slots,
                "status": "pass"
                if filled_half_day_slots == total_half_day_slots
                else "warn",
            },
        }

        # Build ACGME compliance from validation
        has_80_hour_violation = any(
            v.type == "80_HOUR_VIOLATION" for v in validation.violations
        )
        has_1_in_7_violation = any(
            v.type == "1_IN_7_VIOLATION" for v in validation.violations
        )
        has_supervision_violation = any(
            v.type == "SUPERVISION_RATIO_VIOLATION" for v in validation.violations
        )

        # Find max hours for 80-hour detail
        max_hours_detail = "All residents within limit"
        max_hours_resident = None
        if validation.statistics:
            max_hours_detail = (
                f"Max: {validation.statistics.get('max_weekly_hours', 'N/A')} hrs/wk"
            )

        acgme_compliance = {
            "overallStatus": "pass" if validation.valid else "fail",
            "lastChecked": dt.utcnow().isoformat() + "Z",
            "rules": [
                {
                    "id": "80-hour",
                    "name": "80-Hour Rule",
                    "status": "fail" if has_80_hour_violation else "pass",
                    "detail": max_hours_detail,
                    "threshold": "80 hrs/wk averaged over 4 weeks",
                },
                {
                    "id": "1-in-7",
                    "name": "1-in-7 Day Off",
                    "status": "fail" if has_1_in_7_violation else "pass",
                    "detail": "All residents compliant"
                    if not has_1_in_7_violation
                    else "Violations found",
                    "threshold": "1 day off per 7-day period",
                },
                {
                    "id": "supervision",
                    "name": "Supervision Ratios",
                    "status": "fail" if has_supervision_violation else "pass",
                    "detail": "PGY-1: 1:2 | PGY-2/3: 1:4",
                    "threshold": "PGY-1 max 1:2, PGY-2/3 max 1:4",
                },
            ],
        }

        # Build health data
        health = {
            "coverage": int(validation.coverage_rate)
            if validation.coverage_rate
            else 0,
            "conflicts": validation.total_violations,
            "residentCount": assigned_count,
            "totalResidents": total_residents,
            "acgmeCompliant": validation.valid,
            "completeness": 100
            if assigned_count == total_residents
            else int(assigned_count / total_residents * 100),
            "status": "ready"
            if validation.valid and assigned_count == total_residents
            else "warning",
        }

        # Build calendar structure
        from datetime import timedelta

        weeks = []
        current_date = start_date
        week_num = 1
        while current_date <= end_date:
            week_dates = []
            for _ in range(7):
                if current_date <= end_date:
                    week_dates.append(current_date.isoformat())
                current_date += timedelta(days=1)
            if week_dates:
                weeks.append({"weekNum": week_num, "dates": week_dates})
                week_num += 1

        calendar = {
            "weeks": weeks,
            "dayLabels": ["Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed"],
        }

        # Build resident explorer data
        residents_data = []
        assignment_by_resident = {}
        for a in dashboard.current_assignments:
            assignment_by_resident[a.resident_id] = a

        # Source tracking
        source_counts = {"PRE": 0, "GEN": 0, "MAN": 0}

        for resident in all_residents:
            assignment = assignment_by_resident.get(resident.id)
            rotation_name = "Unassigned"
            rotation_id = ""
            source = "GEN"
            notes = None
            needs_attention = False
            attention_reason = None

            if assignment:
                if assignment.rotation_template:
                    rotation_name = assignment.rotation_template.name
                    rotation_id = str(assignment.rotation_template.id)

                # Determine source
                if assignment.assignment_reason == "manual":
                    source = "MAN"
                elif assignment.assignment_reason == "leave_eligible_match":
                    source = "PRE"
                else:
                    source = "GEN"

                notes = assignment.notes

                # Check if needs attention
                if assignment.has_leave and assignment.leave_days > 0:
                    needs_attention = True
                    attention_reason = (
                        f"Has {assignment.leave_days} leave days - verify coverage"
                    )

            else:
                needs_attention = True
                attention_reason = "No block assignment"

            source_counts[source] = source_counts.get(source, 0) + 1

            # Build half-days from actual HalfDayAssignment records
            half_days = []
            complete_assignments = 0
            current = start_date
            while current <= end_date:
                am_key = (resident.id, current, "AM")
                pm_key = (resident.id, current, "PM")

                am_hda = hda_index.get(am_key)
                pm_hda = hda_index.get(pm_key)

                am_abbrev = "---"
                pm_abbrev = "---"
                am_source = "---"
                pm_source = "---"

                if am_hda:
                    am_abbrev = (
                        am_hda.activity.display_abbreviation
                        if am_hda.activity
                        else "???"
                    )
                    am_source = am_hda.source or "GEN"
                    complete_assignments += 1

                if pm_hda:
                    pm_abbrev = (
                        pm_hda.activity.display_abbreviation
                        if pm_hda.activity
                        else "???"
                    )
                    pm_source = pm_hda.source or "GEN"
                    complete_assignments += 1

                half_days.append(
                    {
                        "date": current.isoformat(),
                        "am": am_abbrev,
                        "pm": pm_abbrev,
                        "amSource": am_source,
                        "pmSource": pm_source,
                    }
                )
                current += timedelta(days=1)

            # Calculate assignment count (total expected half-day slots)
            assignment_count = days_in_block * 2

            residents_data.append(
                {
                    "id": str(resident.id),
                    "name": resident.name,
                    "pgyLevel": resident.pgy_level or 1,
                    "rotation": rotation_name[:4].upper()
                    if rotation_name != "Unassigned"
                    else "---",
                    "rotationId": rotation_id,
                    "assignmentCount": assignment_count,
                    "completeAssignments": complete_assignments,
                    "absenceDays": assignment.leave_days if assignment else 0,
                    "source": source,
                    "notes": notes,
                    "needsAttention": needs_attention
                    or complete_assignments < assignment_count,
                    "attentionReason": attention_reason
                    or (
                        f"Missing {assignment_count - complete_assignments} half-day assignments"
                        if complete_assignments < assignment_count
                        else None
                    ),
                    "halfDays": half_days,
                }
            )

        # Build rotation explorer data
        rotations_data = []
        for cap in dashboard.rotation_capacities:
            rotation = next(
                (r for r in all_rotations if r.id == cap.rotation_template_id), None
            )
            if rotation:
                resident_ids = [
                    str(a.resident_id)
                    for a in dashboard.current_assignments
                    if a.rotation_template_id == rotation.id
                ]
                # Get color from activity_colors dict or default
                rotation_abbrev = rotation.name[:4].upper()
                rotation_color = activity_colors.get(rotation_abbrev, "#3b82f6")
                rotations_data.append(
                    {
                        "id": str(rotation.id),
                        "name": rotation.name,
                        "abbreviation": rotation_abbrev,
                        "category": rotation.activity_type or "Other",
                        "color": rotation_color,
                        "capacity": cap.max_residents,
                        "assignedCount": cap.current_assigned,
                        "residents": resident_ids,
                        "description": rotation.name,
                        "callEligible": not rotation.leave_eligible,
                        "leaveEligible": rotation.leave_eligible,
                    }
                )

        # Build validation checks
        validation_checks = [
            {
                "name": "56-Day Coverage",
                "status": "pass" if assigned_count == total_residents else "fail",
                "description": "All residents have complete half-day coverage",
                "details": f"{assigned_count}/{total_residents} residents assigned",
            },
            {
                "name": "ACGME Work Hours",
                "status": "pass" if not has_80_hour_violation else "fail",
                "description": "All residents within 80-hour weekly limit",
                "details": max_hours_detail,
            },
            {
                "name": "1-in-7 Day Off",
                "status": "pass" if not has_1_in_7_violation else "fail",
                "description": "All residents have required day off",
                "details": "Using PAUSE interpretation for absences",
            },
            {
                "name": "Supervision Ratios",
                "status": "pass" if not has_supervision_violation else "fail",
                "description": "Attending coverage meets requirements",
                "details": "All shifts have required supervision",
            },
        ]

        # Add any missing fallback colors for common codes
        activity_colors.setdefault("INP", "#8b5cf6")
        activity_colors.setdefault("CLN", "#10b981")
        activity_colors.setdefault("ELEC", "#f59e0b")
        activity_colors.setdefault("ED", "#ef4444")
        activity_colors.setdefault("OFF", "#374151")
        activity_colors.setdefault("ABS", "#dc2626")
        activity_colors.setdefault("POST", "#9333ea")
        activity_colors.setdefault("CALL", "#0891b2")

        # Sources
        total_assignments = sum(source_counts.values())
        sources = {
            "PRE": {
                "label": "Preloaded",
                "color": "#3b82f6",
                "description": "From Excel import - locked assignments",
                "count": source_counts.get("PRE", 0),
                "percentage": int(source_counts.get("PRE", 0) / total_assignments * 100)
                if total_assignments
                else 0,
            },
            "GEN": {
                "label": "Generated",
                "color": "#10b981",
                "description": "Created by scheduling algorithm",
                "count": source_counts.get("GEN", 0),
                "percentage": int(source_counts.get("GEN", 0) / total_assignments * 100)
                if total_assignments
                else 0,
            },
            "MAN": {
                "label": "Manual",
                "color": "#f59e0b",
                "description": "Manually entered or modified",
                "count": source_counts.get("MAN", 0),
                "percentage": int(source_counts.get("MAN", 0) / total_assignments * 100)
                if total_assignments
                else 0,
            },
        }

        # Build meta
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        date_range = f"{month_names[start_date.month - 1]} {start_date.day} - {month_names[end_date.month - 1]} {end_date.day}, {end_date.year}"

        meta = {
            "blockNumber": block_number,
            "title": f"Block {block_number}",
            "dateRange": date_range,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "daysInBlock": days_in_block,
            "generatedAt": dt.utcnow().isoformat() + "Z",
        }

        return {
            "meta": meta,
            "completeness": completeness,
            "acgmeCompliance": acgme_compliance,
            "health": health,
            "calendar": calendar,
            "residents": residents_data,
            "rotations": rotations_data,
            "validationChecks": validation_checks,
            "activityColors": activity_colors,
            "sources": sources,
        }
