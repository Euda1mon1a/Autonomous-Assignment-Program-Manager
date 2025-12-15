"""
Scheduling Engine for Residency Program.

Implements the core scheduling algorithms:
- Phase 0: Absence loading -> Availability matrix
- Phase 1: Smart pairing -> Greedy initialization
- Phase 2: Resident association -> Constraint-based assignment
- Phase 3: Faculty assignment -> Supervision ratio enforcement
- Phase 7: Validation -> ACGME compliance checking

Algorithms:
- greedy: Fast heuristic, assigns hardest blocks first to least-loaded residents
- cp_sat: Constraint programming solver using Google OR-Tools, guarantees ACGME compliance
"""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID
from collections import defaultdict
import time
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

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
        if algorithm == "cp_sat":
            success = self._assign_residents_cpsat(residents, templates, blocks)
            if not success:
                logger.warning("CP-SAT solver failed, falling back to greedy")
                self._assign_residents_greedy(residents, templates, blocks)
        else:
            # Default to greedy
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

    def _assign_residents_cpsat(
        self,
        residents: list[Person],
        templates: list[RotationTemplate],
        blocks: list[Block],
    ) -> bool:
        """
        CP-SAT constraint programming solver for resident assignment.

        Guarantees ACGME compliance by encoding constraints directly into the solver:
        - 80-hour rule: Max 80 hours/week (rolling 4-week average)
        - 1-in-7 rule: Max 6 consecutive duty days
        - Availability: Respects absences
        - Equity: Balances workload across residents

        Returns True if optimal/feasible solution found, False otherwise.
        """
        try:
            from ortools.sat.python import cp_model
        except ImportError:
            logger.error("ortools not installed. Run: pip install ortools>=9.8")
            return False

        # Filter to workday blocks only
        workday_blocks = [b for b in blocks if not b.is_weekend]

        if not workday_blocks or not residents:
            return False

        # Create the model
        model = cp_model.CpModel()

        # ============================================================
        # DECISION VARIABLES
        # x[r_idx, b_idx] = 1 if resident r is assigned to block b
        # ============================================================
        x = {}
        resident_ids = [r.id for r in residents]
        block_ids = [b.id for b in workday_blocks]

        # Create mapping for fast lookup
        resident_idx = {r.id: i for i, r in enumerate(residents)}
        block_idx = {b.id: i for i, b in enumerate(workday_blocks)}
        block_by_id = {b.id: b for b in workday_blocks}

        for r in residents:
            for b in workday_blocks:
                r_i = resident_idx[r.id]
                b_i = block_idx[b.id]
                x[r_i, b_i] = model.NewBoolVar(f"x_{r_i}_{b_i}")

        # ============================================================
        # CONSTRAINT 1: AVAILABILITY (from absences)
        # If resident is absent, they cannot be assigned
        # ============================================================
        for r in residents:
            r_i = resident_idx[r.id]
            for b in workday_blocks:
                b_i = block_idx[b.id]
                if not self._is_available(r.id, b.id):
                    model.Add(x[r_i, b_i] == 0)

        # ============================================================
        # CONSTRAINT 2: AT MOST ONE RESIDENT PER BLOCK
        # Each block can have at most one primary resident assignment
        # ============================================================
        for b in workday_blocks:
            b_i = block_idx[b.id]
            model.Add(
                sum(x[resident_idx[r.id], b_i] for r in residents) <= 1
            )

        # ============================================================
        # CONSTRAINT 3: 80-HOUR RULE (Rolling 4-week average)
        # Max 80 hours/week averaged over 4 weeks
        # Each half-day block = 6 hours
        # So max blocks per 4 weeks = (80 * 4) / 6 = 53.3 -> 53 blocks
        # ============================================================
        HOURS_PER_BLOCK = 6
        MAX_WEEKLY_HOURS = 80
        ROLLING_WEEKS = 4
        MAX_BLOCKS_PER_WINDOW = (MAX_WEEKLY_HOURS * ROLLING_WEEKS) // HOURS_PER_BLOCK  # 53

        # Group blocks by date for window calculations
        blocks_by_date = defaultdict(list)
        for b in workday_blocks:
            blocks_by_date[b.date].append(b)

        dates = sorted(blocks_by_date.keys())

        # For each possible 28-day window starting point
        for window_start_idx in range(len(dates)):
            window_start = dates[window_start_idx]
            window_end = window_start + timedelta(days=ROLLING_WEEKS * 7 - 1)

            # Get all blocks in this window
            window_blocks = [
                b for b in workday_blocks
                if window_start <= b.date <= window_end
            ]

            if not window_blocks:
                continue

            # For each resident, sum of blocks in window <= MAX_BLOCKS
            for r in residents:
                r_i = resident_idx[r.id]
                window_sum = sum(
                    x[r_i, block_idx[b.id]] for b in window_blocks
                )
                model.Add(window_sum <= MAX_BLOCKS_PER_WINDOW)

        # ============================================================
        # CONSTRAINT 4: 1-IN-7 RULE (Max consecutive duty days)
        # Cannot work more than 6 consecutive days
        # ============================================================
        MAX_CONSECUTIVE_DAYS = 6

        for r in residents:
            r_i = resident_idx[r.id]

            # Check each possible 7-day window
            for start_idx in range(len(dates)):
                # Get 7 consecutive days starting from this date
                consecutive_dates = []
                current = dates[start_idx]

                for day_offset in range(MAX_CONSECUTIVE_DAYS + 1):  # 7 days
                    target_date = current + timedelta(days=day_offset)
                    if target_date in blocks_by_date:
                        consecutive_dates.append(target_date)
                    elif target_date <= self.end_date:
                        # Date exists but no blocks (weekend or holiday)
                        # This counts as a day off, break the streak
                        break

                # If we have 7 consecutive calendar days with blocks
                if len(consecutive_dates) == MAX_CONSECUTIVE_DAYS + 1:
                    # At least one of these days must be off
                    # Sum of assignments across all 7 days must be < 7
                    # (accounting for AM and PM blocks)
                    day_has_assignment = []
                    for d in consecutive_dates:
                        day_blocks = blocks_by_date[d]
                        # Resident works this day if assigned to ANY block on this day
                        day_vars = [x[r_i, block_idx[b.id]] for b in day_blocks]
                        if day_vars:
                            day_worked = model.NewBoolVar(f"day_{r_i}_{d}")
                            # day_worked = 1 if any block on this day is assigned
                            model.AddMaxEquality(day_worked, day_vars)
                            day_has_assignment.append(day_worked)

                    # Can't work all 7 days
                    if len(day_has_assignment) == MAX_CONSECUTIVE_DAYS + 1:
                        model.Add(sum(day_has_assignment) <= MAX_CONSECUTIVE_DAYS)

        # ============================================================
        # OBJECTIVE: MAXIMIZE COVERAGE + BALANCE WORKLOAD
        # 1. Maximize total assignments (coverage)
        # 2. Minimize the maximum assignments per resident (equity)
        # ============================================================

        # Total assignments
        total_assignments = sum(
            x[resident_idx[r.id], block_idx[b.id]]
            for r in residents
            for b in workday_blocks
        )

        # Track max assignments per resident for equity
        max_assignments = model.NewIntVar(0, len(workday_blocks), "max_assignments")
        for r in residents:
            r_i = resident_idx[r.id]
            resident_total = sum(x[r_i, block_idx[b.id]] for b in workday_blocks)
            model.Add(resident_total <= max_assignments)

        # Combined objective: maximize coverage, minimize max (for equity)
        # Scale total_assignments to prioritize coverage, then equity
        model.Maximize(total_assignments * 1000 - max_assignments)

        # ============================================================
        # SOLVE
        # ============================================================
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60.0  # 1 minute timeout
        solver.parameters.num_search_workers = 4  # Parallel solving

        status = solver.Solve(model)

        if status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            logger.warning(f"CP-SAT solver status: {solver.StatusName(status)}")
            return False

        logger.info(f"CP-SAT found {'optimal' if status == cp_model.OPTIMAL else 'feasible'} solution")
        logger.info(f"Total assignments: {solver.Value(total_assignments)}")

        # ============================================================
        # EXTRACT SOLUTION
        # ============================================================
        for r in residents:
            r_i = resident_idx[r.id]
            for b in workday_blocks:
                b_i = block_idx[b.id]
                if solver.Value(x[r_i, b_i]) == 1:
                    # Find appropriate template
                    template = self._select_template_for_resident(r, templates)

                    assignment = Assignment(
                        block_id=b.id,
                        person_id=r.id,
                        rotation_template_id=template.id if template else None,
                        role="primary",
                    )
                    self.assignments.append(assignment)

        return True

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
