"""
Scheduling Engine for Residency Program.

Implements the core scheduling algorithms:
- Phase 0: Absence loading -> Availability matrix
- Phase 1: Smart pairing -> Greedy initialization
- Phase 2: Resident association -> Constraint-based assignment
- Phase 3: Faculty assignment -> Supervision ratio enforcement
- Phase 7: Validation -> ACGME compliance checking
"""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID
import time

from sqlalchemy.orm import Session

from app.models.person import Person
from app.models.block import Block
from app.models.assignment import Assignment
from app.models.absence import Absence
from app.models.rotation_template import RotationTemplate
from app.models.schedule_run import ScheduleRun
from app.scheduling.validator import ACGMEValidator


class SchedulingEngine:
    """
    Clean, maintainable scheduling engine for residency programs.

    Algorithm: Greedy initialization + constraint repair
    Constraints: ACGME duty hours, supervision ratios, clinic capacity
    """

    def __init__(self, db: Session, start_date: date, end_date: date):
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.availability_matrix: dict = {}
        self.assignments: list[Assignment] = []
        self.validator = ACGMEValidator(db)

    def generate(
        self,
        pgy_levels: Optional[list[int]] = None,
        rotation_template_ids: Optional[list[UUID]] = None,
        algorithm: str = "greedy",
    ) -> dict:
        """
        Generate a complete schedule.

        Steps:
        1. Ensure blocks exist for date range
        2. Load absences and build availability matrix
        3. Assign residents using selected algorithm
        4. Assign supervising faculty
        5. Validate ACGME compliance
        6. Save results
        """
        start_time = time.time()

        # Step 1: Ensure blocks exist
        blocks = self._ensure_blocks_exist()

        # Step 2: Load absences and build availability matrix
        self._build_availability_matrix()

        # Step 3: Get residents and templates
        residents = self._get_residents(pgy_levels)
        templates = self._get_rotation_templates(rotation_template_ids)

        if not residents:
            return {
                "status": "failed",
                "message": "No residents found matching criteria",
                "total_assigned": 0,
                "total_blocks": len(blocks),
                "validation": self._empty_validation(),
            }

        # Step 4: Assign residents
        if algorithm == "greedy":
            self._assign_residents_greedy(residents, templates, blocks)
        else:
            # Default to greedy for now
            self._assign_residents_greedy(residents, templates, blocks)

        # Step 5: Assign faculty supervision
        faculty = self._get_faculty()
        self._assign_faculty(faculty, blocks)

        # Step 6: Save assignments
        self._save_assignments()

        # Step 7: Validate
        validation = self.validator.validate_all(self.start_date, self.end_date)

        # Step 8: Record run
        runtime = time.time() - start_time
        run = self._record_run(algorithm, validation, runtime)

        return {
            "status": "success" if validation.valid else "partial",
            "message": f"Generated {len(self.assignments)} assignments",
            "total_assigned": len(self.assignments),
            "total_blocks": len(blocks),
            "validation": validation,
            "run_id": run.id,
        }

    def _ensure_blocks_exist(self) -> list[Block]:
        """Ensure half-day blocks exist for the date range."""
        blocks = []
        current_date = self.start_date
        block_number = 1

        while current_date <= self.end_date:
            for time_of_day in ["AM", "PM"]:
                existing = self.db.query(Block).filter(
                    Block.date == current_date,
                    Block.time_of_day == time_of_day,
                ).first()

                if existing:
                    blocks.append(existing)
                else:
                    block = Block(
                        date=current_date,
                        time_of_day=time_of_day,
                        block_number=block_number,
                        is_weekend=(current_date.weekday() >= 5),
                    )
                    self.db.add(block)
                    blocks.append(block)

            # Update block number every 28 days
            days_from_start = (current_date - self.start_date).days
            block_number = 1 + (days_from_start // 28)
            current_date += timedelta(days=1)

        self.db.commit()
        return blocks

    def _build_availability_matrix(self):
        """
        Build availability matrix from absences.

        Matrix structure:
        {
            person_id: {
                block_id: {
                    'available': bool,
                    'replacement': str (activity shown when absent)
                }
            }
        }
        """
        # Get all people
        people = self.db.query(Person).all()

        # Get all blocks in range
        blocks = self.db.query(Block).filter(
            Block.date >= self.start_date,
            Block.date <= self.end_date,
        ).all()

        # Get absences in range
        absences = self.db.query(Absence).filter(
            Absence.start_date <= self.end_date,
            Absence.end_date >= self.start_date,
        ).all()

        # Build matrix
        for person in people:
            self.availability_matrix[person.id] = {}

            for block in blocks:
                # Default: available
                is_available = True
                replacement_activity = None

                # Check absences
                for absence in absences:
                    if (
                        absence.person_id == person.id
                        and absence.start_date <= block.date <= absence.end_date
                    ):
                        is_available = False
                        replacement_activity = absence.replacement_activity
                        break

                self.availability_matrix[person.id][block.id] = {
                    "available": is_available,
                    "replacement": replacement_activity,
                }

    def _get_residents(self, pgy_levels: Optional[list[int]] = None) -> list[Person]:
        """Get residents, optionally filtered by PGY level."""
        query = self.db.query(Person).filter(Person.type == "resident")

        if pgy_levels:
            query = query.filter(Person.pgy_level.in_(pgy_levels))

        return query.order_by(Person.pgy_level, Person.name).all()

    def _get_faculty(self) -> list[Person]:
        """Get all faculty members."""
        return self.db.query(Person).filter(Person.type == "faculty").all()

    def _get_rotation_templates(
        self, template_ids: Optional[list[UUID]] = None
    ) -> list[RotationTemplate]:
        """Get rotation templates, optionally filtered by ID."""
        query = self.db.query(RotationTemplate)

        if template_ids:
            query = query.filter(RotationTemplate.id.in_(template_ids))

        return query.all()

    def _assign_residents_greedy(
        self,
        residents: list[Person],
        templates: list[RotationTemplate],
        blocks: list[Block],
    ):
        """
        Greedy assignment algorithm.

        Strategy:
        1. Sort blocks by constraint scarcity (hardest first)
        2. For each block, assign most eligible resident
        3. Track assignments for equity
        """
        # Filter to workday blocks only (exclude weekends for clinic)
        workday_blocks = [b for b in blocks if not b.is_weekend]

        # Sort blocks by difficulty (fewest eligible residents = harder)
        sorted_blocks = sorted(
            workday_blocks,
            key=lambda b: self._count_eligible_residents(b, residents),
        )

        # Track assignment counts for equity
        assignment_counts = {r.id: 0 for r in residents}

        for block in sorted_blocks:
            eligible = [
                r
                for r in residents
                if self._is_available(r.id, block.id)
            ]

            if not eligible:
                continue  # No one available for this block

            # Select resident with fewest assignments (equity)
            selected = min(eligible, key=lambda r: assignment_counts[r.id])

            # Find appropriate template
            template = self._select_template_for_resident(selected, templates)

            # Create assignment
            assignment = Assignment(
                block_id=block.id,
                person_id=selected.id,
                rotation_template_id=template.id if template else None,
                role="primary",
            )
            self.assignments.append(assignment)
            assignment_counts[selected.id] += 1

    def _assign_faculty(self, faculty: list[Person], blocks: list[Block]):
        """
        Assign faculty supervision based on ACGME ratios.

        Rules:
        - PGY-1: 1 faculty : 2 residents
        - PGY-2/3: 1 faculty : 4 residents
        """
        # Group assignments by block
        assignments_by_block = {}
        for assignment in self.assignments:
            if assignment.block_id not in assignments_by_block:
                assignments_by_block[assignment.block_id] = []
            assignments_by_block[assignment.block_id].append(assignment)

        # Assign faculty to each block
        faculty_assignments = {f.id: 0 for f in faculty}

        for block_id, block_assignments in assignments_by_block.items():
            # Get resident details for this block
            resident_ids = [a.person_id for a in block_assignments]
            residents_in_block = self.db.query(Person).filter(
                Person.id.in_(resident_ids)
            ).all()

            # Calculate required faculty
            pgy1_count = sum(1 for r in residents_in_block if r.pgy_level == 1)
            other_count = len(residents_in_block) - pgy1_count

            # 1:2 for PGY-1, 1:4 for others
            required = (pgy1_count + 1) // 2 + (other_count + 3) // 4
            required = max(1, required) if residents_in_block else 0

            # Find available faculty
            available = [
                f for f in faculty
                if self._is_available(f.id, block_id)
            ]

            # Assign faculty (balance load)
            selected = sorted(available, key=lambda f: faculty_assignments[f.id])[:required]

            for fac in selected:
                assignment = Assignment(
                    block_id=block_id,
                    person_id=fac.id,
                    role="supervising",
                )
                self.assignments.append(assignment)
                faculty_assignments[fac.id] += 1

    def _count_eligible_residents(self, block: Block, residents: list[Person]) -> int:
        """Count how many residents can fill this block."""
        return sum(
            1
            for r in residents
            if self._is_available(r.id, block.id)
        )

    def _is_available(self, person_id: UUID, block_id: UUID) -> bool:
        """Check if person is available for block."""
        if person_id not in self.availability_matrix:
            return True
        if block_id not in self.availability_matrix[person_id]:
            return True
        return self.availability_matrix[person_id][block_id]["available"]

    def _select_template_for_resident(
        self, resident: Person, templates: list[RotationTemplate]
    ) -> Optional[RotationTemplate]:
        """Select appropriate rotation template for resident."""
        # Filter templates by PGY level suitability
        suitable = []
        for template in templates:
            # Check procedure credentials
            if template.requires_procedure_credential:
                continue  # Residents don't do procedures by default

            suitable.append(template)

        # Return first suitable template (can be enhanced with smarter selection)
        return suitable[0] if suitable else None

    def _save_assignments(self):
        """Save all assignments to database."""
        for assignment in self.assignments:
            self.db.add(assignment)
        self.db.commit()

    def _record_run(
        self, algorithm: str, validation, runtime: float
    ) -> ScheduleRun:
        """Record the schedule run for audit."""
        run = ScheduleRun(
            start_date=self.start_date,
            end_date=self.end_date,
            algorithm=algorithm,
            status="success" if validation.valid else "partial",
            total_blocks_assigned=len(self.assignments),
            acgme_violations=validation.total_violations,
            runtime_seconds=runtime,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _empty_validation(self):
        """Return empty validation result."""
        from app.schemas.schedule import ValidationResult
        return ValidationResult(
            valid=True,
            total_violations=0,
            violations=[],
            coverage_rate=0.0,
        )
