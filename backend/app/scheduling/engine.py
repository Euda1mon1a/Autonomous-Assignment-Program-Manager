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
- pulp: Linear programming solver using PuLP for large-scale optimization
- hybrid: Combines CP-SAT and PuLP for best results

The engine uses a modular constraint system (constraints.py) and pluggable solvers (solvers.py)
for flexible, maintainable scheduling.
"""
import time
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import get_logger

logger = get_logger(__name__)

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.schedule_run import ScheduleRun
from app.resilience.service import ResilienceConfig, ResilienceService
from app.scheduling.constraints import (
    ConstraintManager,
    SchedulingContext,
)
from app.scheduling.solvers import (
    SolverFactory,
    SolverResult,
)
from app.scheduling.validator import ACGMEValidator


class SchedulingEngine:
    """
    Clean, maintainable scheduling engine for residency programs.

    Features:
    - Multiple solver backends (greedy, CP-SAT, PuLP, hybrid)
    - Modular constraint system
    - ACGME compliance validation
    - Faculty supervision assignment

    Algorithm Flow:
    1. Ensure blocks exist for date range
    2. Build availability matrix from absences
    3. Create scheduling context with all data
    4. Run selected solver with constraints
    5. Assign faculty supervision
    6. Validate and save results
    """

    # Available algorithms
    ALGORITHMS = ["greedy", "cp_sat", "pulp", "hybrid"]

    def __init__(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        constraint_manager: ConstraintManager | None = None,
        resilience_config: ResilienceConfig | None = None,
    ):
        self.db = db
        self.start_date = start_date
        self.end_date = end_date
        self.availability_matrix: dict = {}
        self.assignments: list[Assignment] = []
        self.validator = ACGMEValidator(db)
        self.constraint_manager = constraint_manager or ConstraintManager.create_default()

        # Initialize resilience service for health monitoring
        self.resilience = ResilienceService(
            db=db,
            config=resilience_config or ResilienceConfig(),
        )

    def generate(
        self,
        pgy_levels: list[int] | None = None,
        rotation_template_ids: list[UUID] | None = None,
        algorithm: str = "greedy",
        timeout_seconds: float = 60.0,
        check_resilience: bool = True,
        preserve_fmit: bool = True,
    ) -> dict:
        """
        Generate a complete schedule.

        Args:
            pgy_levels: Filter residents by PGY level (None = all)
            rotation_template_ids: Filter templates by ID (None = all)
            algorithm: Solver algorithm ('greedy', 'cp_sat', 'pulp', 'hybrid')
            timeout_seconds: Maximum solver runtime
            check_resilience: Run resilience health check before/after generation
            preserve_fmit: Preserve existing FMIT faculty assignments (default True)

        Returns:
            Dictionary with status, assignments, validation results, and resilience info
        """
        start_time = time.time()

        # Validate algorithm
        if algorithm not in self.ALGORITHMS:
            logger.warning(f"Unknown algorithm '{algorithm}', using 'greedy'")
            algorithm = "greedy"

        # Issue #3: Transaction boundaries - wrap everything in a single transaction
        # Create an "in_progress" run record first
        run = self._create_initial_run(algorithm)

        # Pre-generation resilience check
        # Store as instance attribute for _populate_resilience_data to access
        self._pre_health_report = None
        if check_resilience:
            self._pre_health_report = self._check_pre_generation_resilience()

        try:
            # Step 1: Ensure blocks exist (but don't commit yet)
            blocks = self._ensure_blocks_exist(commit=False)

            # Step 1.5: Load FMIT assignments if preserving them
            fmit_assignments = []
            preserve_ids: set[UUID] = set()
            if preserve_fmit:
                fmit_assignments = self._load_fmit_assignments()
                preserve_ids = {a.id for a in fmit_assignments}
                if fmit_assignments:
                    logger.info(
                        f"Preserving {len(fmit_assignments)} FMIT faculty assignments"
                    )

            # Issue #2: Delete existing assignments for this date range to avoid duplicates
            self._delete_existing_assignments(preserve_ids=preserve_ids)

            # Step 2: Load absences and build availability matrix
            self._build_availability_matrix()

            # Step 3: Get residents, faculty, and templates
            residents = self._get_residents(pgy_levels)
            templates = self._get_rotation_templates(rotation_template_ids)
            faculty = self._get_faculty()

            if not residents:
                self._update_run_status(run, "failed", 0, 0, time.time() - start_time)
                self.db.commit()
                return {
                    "status": "failed",
                    "message": "No residents found matching criteria",
                    "total_assigned": 0,
                    "total_blocks": len(blocks),
                    "validation": self._empty_validation(),
                    "run_id": run.id,
                }

            # Step 4: Create scheduling context (with resilience data if available)
            context = self._build_context(
                residents, faculty, blocks, templates,
                include_resilience=check_resilience,
            )

            # Step 5: Run solver
            solver_result = self._run_solver(algorithm, context, timeout_seconds)

            if not solver_result.success:
                logger.warning(f"Solver failed: {solver_result.solver_status}")
                # Fallback to greedy if advanced solver fails
                if algorithm != "greedy":
                    logger.info("Falling back to greedy solver")
                    solver_result = self._run_solver("greedy", context, timeout_seconds)

            # Step 6: Convert solver results to assignments
            self._create_assignments_from_result(solver_result, residents, templates)

            # Step 7: Assign faculty supervision
            self._assign_faculty(faculty, blocks)

            # Step 8: Add assignments to session (but don't commit yet)
            for assignment in self.assignments:
                self.db.add(assignment)

            # Step 9: Validate
            validation = self.validator.validate_all(self.start_date, self.end_date)

            # Step 10: Update run record with results
            runtime = time.time() - start_time
            self._update_run_with_results(run, algorithm, validation, runtime, solver_result)

            # Issue #3: Single atomic commit - all or nothing
            self.db.commit()
            self.db.refresh(run)

            # Post-generation resilience check
            post_health_report = None
            resilience_warnings = []
            if check_resilience:
                post_health_report = self._check_post_generation_resilience(
                    faculty, blocks, self.assignments
                )
                resilience_warnings = self._get_resilience_warnings(post_health_report)

            return {
                "status": "success" if validation.valid else "partial",
                "message": f"Generated {len(self.assignments)} assignments using {algorithm}",
                "total_assigned": len(self.assignments),
                "total_blocks": len(blocks),
                "validation": validation,
                "run_id": run.id,
                "solver_stats": solver_result.statistics,
                "resilience": {
                    "pre_generation_status": self._pre_health_report.overall_status if self._pre_health_report else None,
                    "post_generation_status": post_health_report.overall_status if post_health_report else None,
                    "utilization_rate": post_health_report.utilization.utilization_rate if post_health_report else None,
                    "n1_compliant": post_health_report.n1_pass if post_health_report else None,
                    "n2_compliant": post_health_report.n2_pass if post_health_report else None,
                    "warnings": resilience_warnings,
                    "immediate_actions": post_health_report.immediate_actions if post_health_report else [],
                    # New: Include resilience constraint activity
                    "resilience_constraints_active": context.has_resilience_data() if context else False,
                    "hub_faculty_count": len(context.hub_scores) if context else 0,
                },
            }

        except Exception as e:
            # Issue #3: Rollback on any failure to prevent partial persistence
            logger.error(f"Schedule generation failed: {e}")
            self.db.rollback()

            # Try to update run status to failed (in a new transaction)
            try:
                self.db.refresh(run)
                self._update_run_status(run, "failed", 0, 0, time.time() - start_time)
                self.db.commit()
            except Exception:
                self.db.rollback()

            raise

    def _build_context(
        self,
        residents: list[Person],
        faculty: list[Person],
        blocks: list[Block],
        templates: list[RotationTemplate],
        include_resilience: bool = True,
    ) -> SchedulingContext:
        """
        Build scheduling context from database objects.

        Args:
            residents: List of resident Person objects
            faculty: List of faculty Person objects
            blocks: List of Block objects for the schedule period
            templates: List of RotationTemplate objects
            include_resilience: Whether to populate resilience data

        Returns:
            SchedulingContext with all data needed for constraint evaluation
        """
        # Build base context
        context = SchedulingContext(
            residents=residents,
            faculty=faculty,
            blocks=blocks,
            templates=templates,
            availability=self.availability_matrix,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        # Populate resilience data if available and requested
        if include_resilience and self.resilience:
            self._populate_resilience_data(context, faculty, blocks)

        return context

    def _populate_resilience_data(
        self,
        context: SchedulingContext,
        faculty: list[Person],
        blocks: list[Block],
    ):
        """
        Populate resilience data in the scheduling context.

        Tier 1 (Critical):
        - Hub scores from hub analysis
        - Current utilization from resilience service

        Tier 2 (Strategic):
        - N-1 vulnerable faculty from contingency analysis
        - Preference trails from stigmergy
        - Zone assignments from blast radius isolation

        The data enables resilience-aware constraints to function.
        Constraints are auto-enabled when their data is available.
        """
        try:
            # =================================================================
            # TIER 1: Critical resilience data
            # =================================================================

            # Get hub scores
            hub_scores = self._get_hub_scores(faculty)
            if hub_scores:
                context.hub_scores = hub_scores
                logger.debug(f"Loaded hub scores for {len(hub_scores)} faculty")

                # Enable hub protection constraint if we have data
                if self.constraint_manager:
                    self.constraint_manager.enable("HubProtection")

            # Get current utilization from pre-generation check
            if hasattr(self, '_pre_health_report') and self._pre_health_report:
                context.current_utilization = self._pre_health_report.utilization.utilization_rate
                context.target_utilization = self.resilience.config.max_utilization

                # Enable utilization buffer constraint
                if self.constraint_manager:
                    self.constraint_manager.enable("UtilizationBuffer")

            # =================================================================
            # TIER 2: Strategic resilience data
            # =================================================================

            # Get N-1 vulnerable faculty from contingency analysis
            n1_vulnerable = self._get_n1_vulnerable_faculty(faculty, blocks)
            if n1_vulnerable:
                context.n1_vulnerable_faculty = n1_vulnerable
                logger.debug(f"Identified {len(n1_vulnerable)} N-1 vulnerable faculty")

            # Always enable N1 constraint - it can work without pre-identified faculty
            # by analyzing the solution for single points of failure
            if self.constraint_manager:
                self.constraint_manager.enable("N1Vulnerability")

            # Get preference trails from stigmergy
            preference_trails = self._get_preference_trails(faculty)
            if preference_trails:
                context.preference_trails = preference_trails
                logger.debug(f"Loaded preference trails for {len(preference_trails)} faculty")

                # Enable preference trail constraint
                if self.constraint_manager:
                    self.constraint_manager.enable("PreferenceTrail")

            # Get zone assignments from blast radius isolation
            zone_data = self._get_zone_assignments(faculty, blocks)
            if zone_data:
                context.zone_assignments = zone_data.get("faculty_zones", {})
                context.block_zones = zone_data.get("block_zones", {})
                logger.debug(
                    f"Loaded zone data: {len(context.zone_assignments)} faculty, "
                    f"{len(context.block_zones)} blocks"
                )

                # Enable zone boundary constraint
                if self.constraint_manager:
                    self.constraint_manager.enable("ZoneBoundary")

        except Exception as e:
            logger.warning(f"Failed to populate resilience data: {e}")
            # Continue without resilience data - constraints will be no-ops

    def _get_hub_scores(self, faculty: list[Person]) -> dict[UUID, float]:
        """
        Get hub vulnerability scores for faculty from network analysis.

        Hub scores are computed by the ResilienceService using network centrality
        metrics (degree, betweenness, closeness) to identify critical "hub"
        faculty whose loss would significantly impact the system.

        Network Theory Context:
            Scale-free networks (common in organizations) are:
            - Robust to random failures
            - Extremely vulnerable to targeted hub removal
            - Hub faculty cover unique services or specialties
            - Over-assigning hubs increases systemic risk

        Args:
            faculty: List of faculty Person objects

        Returns:
            dict[UUID, float]: Mapping of faculty_id to hub score (0.0-1.0)
                - 0.0-0.4: Low hub score, not critical
                - 0.4-0.6: Moderate hub, should be somewhat protected
                - 0.6-1.0: Critical hub, strongly protect from over-assignment
                Returns empty dict if hub analysis data unavailable

        Example:
            >>> hub_scores = self._get_hub_scores(faculty)
            >>> critical_hubs = {fid: score for fid, score in hub_scores.items() if score > 0.6}
            >>> print(f"Found {len(critical_hubs)} critical hub faculty")

        Note:
            Called during context building if resilience integration is enabled.
            Scores are cached in the scheduling context for constraint evaluation.
        """
        hub_scores = {}

        try:
            # Check if we have cached hub analysis results
            if hasattr(self.resilience, 'hub_analyzer'):
                # Get latest centrality data
                for fac in faculty:
                    centrality = self.resilience.hub_analyzer.get_faculty_centrality(fac.id)
                    if centrality:
                        hub_scores[fac.id] = centrality.composite_score
        except Exception as e:
            logger.debug(f"Could not get hub scores: {e}")

        return hub_scores

    def _get_n1_vulnerable_faculty(
        self,
        faculty: list[Person],
        blocks: list[Block],
    ) -> set[UUID]:
        """
        Identify faculty whose loss would cause N-1 failure.

        These are single points of failure - the schedule cannot
        survive if they become unavailable.
        """
        n1_vulnerable = set()

        try:
            # Use contingency analyzer if available
            if hasattr(self.resilience, 'contingency'):
                # This would need existing assignments to analyze
                # For now, return empty - will be populated after solving
                pass
        except Exception as e:
            logger.debug(f"Could not get N-1 vulnerable faculty: {e}")

        return n1_vulnerable

    def _get_preference_trails(self, faculty: list[Person]) -> dict[UUID, dict[str, float]]:
        """
        Get preference trail data from stigmergy system.

        Returns dict of faculty_id -> {slot_type -> strength}.
        Used for soft preference optimization.
        """
        preference_trails = {}

        try:
            if hasattr(self.resilience, 'stigmergy'):
                for fac in faculty:
                    prefs = self.resilience.get_faculty_preferences(fac.id, min_strength=0.3)
                    if prefs:
                        faculty_prefs = {}
                        for trail in prefs:
                            if trail.slot_type:
                                faculty_prefs[trail.slot_type] = trail.strength
                        if faculty_prefs:
                            preference_trails[fac.id] = faculty_prefs
        except Exception as e:
            logger.debug(f"Could not get preference trails: {e}")

        return preference_trails

    def _get_zone_assignments(
        self,
        faculty: list[Person],
        blocks: list[Block],
    ) -> dict:
        """
        Get zone assignment data from blast radius isolation system.

        Returns dict with:
        - faculty_zones: {faculty_id -> zone_id}
        - block_zones: {block_id -> zone_id}

        Used to enforce zone boundaries and contain failures.
        """
        zone_data = {
            "faculty_zones": {},
            "block_zones": {},
        }

        try:
            if hasattr(self.resilience, 'blast_radius'):
                blast_radius = self.resilience.blast_radius

                # Get faculty zone assignments
                for fac in faculty:
                    zone = blast_radius.get_faculty_zone(fac.id)
                    if zone:
                        zone_data["faculty_zones"][fac.id] = zone.id

                # Get block zone assignments (from rotation template or service type)
                for block in blocks:
                    # Blocks may be associated with zones through their rotation template
                    # or through explicit zone assignment
                    zone = blast_radius.get_block_zone(block.id)
                    if zone:
                        zone_data["block_zones"][block.id] = zone.id

        except Exception as e:
            logger.debug(f"Could not get zone assignments: {e}")

        # Only return if we have meaningful data
        if zone_data["faculty_zones"] or zone_data["block_zones"]:
            return zone_data
        return None

    def _run_solver(
        self,
        algorithm: str,
        context: SchedulingContext,
        timeout_seconds: float,
    ) -> SolverResult:
        """Run the selected solver algorithm."""
        try:
            solver = SolverFactory.create(
                algorithm,
                constraint_manager=self.constraint_manager,
                timeout_seconds=timeout_seconds,
            )
            return solver.solve(context)
        except Exception as e:
            logger.error(f"Solver error: {e}")
            return SolverResult(
                success=False,
                assignments=[],
                status="error",
                solver_status=str(e),
            )

    def _create_assignments_from_result(
        self,
        result: SolverResult,
        residents: list[Person],
        templates: list[RotationTemplate],
    ):
        """Convert solver results to Assignment objects."""
        for person_id, block_id, template_id in result.assignments:
            assignment = Assignment(
                block_id=block_id,
                person_id=person_id,
                rotation_template_id=template_id,
                role="primary",
            )
            self.assignments.append(assignment)

    def _ensure_blocks_exist(self, commit: bool = True) -> list[Block]:
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

        if commit:
            self.db.commit()
        else:
            self.db.flush()  # Make blocks available in the session without committing

        return blocks

    def _build_availability_matrix(self):
        """
        Build availability matrix from absences in the database.

        This method queries all absences that overlap with the scheduling period
        and constructs a matrix indicating whether each person is available for
        each block. This is a critical preprocessing step that enables fast
        constraint evaluation during solving.

        Matrix structure:
            {
                person_id (UUID): {
                    block_id (UUID): {
                        'available' (bool): True if person can be assigned,
                        'replacement' (str): Activity displayed in calendar (e.g., "TDY"),
                        'partial_absence' (bool): True if person has non-blocking absence
                    }
                }
            }

        Absence Classification Logic:
            - **Blocking absences** (deployment, TDY, extended medical):
              - available = False
              - Person CANNOT be assigned to this block
              - Enforced by AvailabilityConstraint (hard constraint)

            - **Partial absences** (vacation day, conference, appointment):
              - available = True
              - Person CAN be assigned (they can work partial day)
              - partial_absence = True (tracked for informational purposes)
              - Calendar shows replacement activity but assignment is allowed

        Performance:
            - Pre-computes all availability checks: O(people × blocks × absences)
            - Enables O(1) lookup during constraint evaluation
            - Reduces solver time by avoiding database queries during solving

        Example:
            >>> # After building availability matrix:
            >>> is_available = self.availability_matrix[resident_id][block_id]["available"]
            >>> if is_available:
            ...     # Can assign resident to this block
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
                has_partial_absence = False

                # Check absences
                for absence in absences:
                    if (
                        absence.person_id == person.id
                        and absence.start_date <= block.date <= absence.end_date
                    ):
                        # Use the should_block_assignment property to determine
                        if absence.should_block_assignment:
                            # Blocking absence - person cannot be assigned
                            is_available = False
                            replacement_activity = absence.replacement_activity
                            break
                        else:
                            # Partial absence - person can be assigned but we track it
                            has_partial_absence = True
                            replacement_activity = absence.replacement_activity
                            # Don't break - keep checking for blocking absences

                self.availability_matrix[person.id][block.id] = {
                    "available": is_available,
                    "replacement": replacement_activity,
                    "partial_absence": has_partial_absence,
                }

    def _get_residents(self, pgy_levels: list[int] | None = None) -> list[Person]:
        """Get residents, optionally filtered by PGY level."""
        query = self.db.query(Person).filter(Person.type == "resident")

        if pgy_levels:
            query = query.filter(Person.pgy_level.in_(pgy_levels))

        return query.order_by(Person.pgy_level, Person.name).all()

    def _get_faculty(self) -> list[Person]:
        """Get all faculty members."""
        return self.db.query(Person).filter(Person.type == "faculty").all()

    def _load_fmit_assignments(self) -> list[Assignment]:
        """
        Load FMIT assignments (faculty on inpatient) for the date range.

        FMIT (Faculty Managing Inpatient Teaching) assignments are pre-selected
        by faculty at the beginning of the academic year. These assignments
        should be preserved during schedule generation rather than deleted
        and regenerated.

        Detection logic:
            - person.type == 'faculty'
            - template.activity_type == 'inpatient'

        Returns:
            List of Assignment objects for faculty on FMIT rotations
        """
        return (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .join(Person, Assignment.person_id == Person.id)
            .join(RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id)
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
                Person.type == "faculty",
                RotationTemplate.activity_type == "inpatient",
            )
            .all()
        )

    def _get_rotation_templates(
        self, template_ids: list[UUID] | None = None
    ) -> list[RotationTemplate]:
        """Get rotation templates, optionally filtered by ID."""
        query = self.db.query(RotationTemplate)

        if template_ids:
            query = query.filter(RotationTemplate.id.in_(template_ids))

        return query.all()

    def _assign_faculty(self, faculty: list[Person], blocks: list[Block]):
        """
        Assign faculty supervision based on ACGME supervision ratios.

        This method implements the second phase of scheduling: after residents
        are assigned to blocks, faculty are assigned to provide supervision
        according to ACGME requirements.

        ACGME Supervision Ratios:
            - PGY-1 residents: 1 faculty : 2 residents (intensive supervision)
            - PGY-2/3 residents: 1 faculty : 4 residents (greater autonomy)

        Algorithm:
            1. Group existing resident assignments by block
            2. For each block with residents:
               a. Count PGY-1 vs. PGY-2/3 residents
               b. Calculate required faculty: ⌈PGY1/2⌉ + ⌈Others/4⌉
               c. Find available faculty (check availability matrix)
               d. Select least-loaded faculty to balance workload
               e. Create "supervising" role assignments

        Load Balancing:
            Faculty are sorted by current assignment count and selected in order
            to distribute supervision burden equitably across all faculty.

        Args:
            faculty: List of Person objects with type="faculty"
            blocks: List of Block objects in the scheduling period

        Side Effects:
            Appends faculty Assignment objects to self.assignments with role="supervising"

        Example:
            Block with 2 PGY-1 and 4 PGY-2/3 residents:
            - PGY-1 faculty needed: ⌈2/2⌉ = 1
            - PGY-2/3 faculty needed: ⌈4/4⌉ = 1
            - Total: 2 faculty assigned to supervise this block

        Note:
            This method is separate from the main constraint solver because
            faculty assignment is a post-processing step that depends on
            resident assignments being finalized first.
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

    def _is_available(self, person_id: UUID, block_id: UUID) -> bool:
        """Check if person is available for block."""
        if person_id not in self.availability_matrix:
            return True
        if block_id not in self.availability_matrix[person_id]:
            return True
        return self.availability_matrix[person_id][block_id]["available"]

    def _create_initial_run(self, algorithm: str) -> ScheduleRun:
        """Create initial run record with 'in_progress' status."""
        run = ScheduleRun(
            start_date=self.start_date,
            end_date=self.end_date,
            algorithm=algorithm,
            status="in_progress",
            total_blocks_assigned=0,
            acgme_violations=0,
            runtime_seconds=0.0,
            config_json={},
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _delete_existing_assignments(self, preserve_ids: set[UUID] | None = None):
        """
        Delete existing assignments for the date range to avoid duplicates.

        Uses row-level locking (SELECT FOR UPDATE) to prevent concurrent
        schedule generations from racing. This ensures that only one
        generation can modify assignments for a given date range at a time.

        Args:
            preserve_ids: Set of assignment IDs to preserve (e.g., FMIT assignments)
        """
        preserve_ids = preserve_ids or set()

        # Get all block IDs in the date range with row-level lock
        # The FOR UPDATE lock ensures exclusive access to these blocks
        # during the transaction, preventing concurrent generations from
        # creating conflicting assignments
        blocks = (
            self.db.query(Block)
            .filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
            )
            .with_for_update(nowait=False)  # Wait for lock rather than fail immediately
            .all()
        )
        block_ids = [block.id for block in blocks]

        if block_ids:
            # Lock and delete existing assignments for these blocks
            # We select first to acquire locks, then delete
            existing_assignments = (
                self.db.query(Assignment)
                .filter(Assignment.block_id.in_(block_ids))
                .with_for_update(nowait=False)
                .all()
            )

            deleted_count = 0
            preserved_count = 0
            for assignment in existing_assignments:
                if assignment.id in preserve_ids:
                    preserved_count += 1
                    continue  # Skip preserved assignments (e.g., FMIT)
                self.db.delete(assignment)
                deleted_count += 1

            logger.info(
                f"Deleted {deleted_count} existing assignments for date range "
                f"({self.start_date} to {self.end_date}), preserved {preserved_count}"
            )

    def _update_run_status(self, run: ScheduleRun, status: str, total_assigned: int, violations: int, runtime: float):
        """Update run record with final status."""
        run.status = status
        run.total_blocks_assigned = total_assigned
        run.acgme_violations = violations
        run.runtime_seconds = runtime
        self.db.add(run)

    def _update_run_with_results(
        self,
        run: ScheduleRun,
        algorithm: str,
        validation,
        runtime: float,
        solver_result: SolverResult | None = None,
    ):
        """Update run record with generation results."""
        config = {}
        if solver_result:
            config = {
                "solver_status": solver_result.solver_status,
                "objective_value": solver_result.objective_value,
                "solver_runtime": solver_result.runtime_seconds,
                "statistics": solver_result.statistics,
            }

        run.algorithm = algorithm
        run.status = "success" if validation.valid else "partial"
        run.total_blocks_assigned = len(self.assignments)
        run.acgme_violations = validation.total_violations
        run.runtime_seconds = runtime
        run.config_json = config
        self.db.add(run)

    def _empty_validation(self):
        """Return empty validation result."""
        from app.schemas.schedule import ValidationResult
        return ValidationResult(
            valid=True,
            total_violations=0,
            violations=[],
            coverage_rate=0.0,
        )

    def _check_pre_generation_resilience(self):
        """
        Run resilience health check before schedule generation.

        This provides early warning if system is already stressed.
        """
        try:
            faculty = self._get_faculty()
            blocks = self.db.query(Block).filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
            ).all()
            existing_assignments = self.db.query(Assignment).join(Block).filter(
                Block.date >= self.start_date,
                Block.date <= self.end_date,
            ).all()

            report = self.resilience.check_health(
                faculty=faculty,
                blocks=blocks,
                assignments=existing_assignments,
            )

            # Log warning if system is stressed
            if report.overall_status in ("critical", "emergency"):
                logger.warning(
                    f"Pre-generation resilience check: {report.overall_status.upper()}. "
                    f"Utilization: {report.utilization.utilization_rate:.0%}. "
                    f"Actions: {report.immediate_actions}"
                )
            elif report.overall_status == "degraded":
                logger.info(
                    f"Pre-generation resilience check: degraded. "
                    f"Utilization: {report.utilization.utilization_rate:.0%}"
                )

            return report

        except Exception as e:
            logger.warning(f"Pre-generation resilience check failed: {e}")
            return None

    def _check_post_generation_resilience(
        self,
        faculty: list[Person],
        blocks: list[Block],
        assignments: list[Assignment],
    ):
        """
        Run resilience health check after schedule generation.

        This validates the generated schedule doesn't create stress conditions.
        """
        try:
            report = self.resilience.check_health(
                faculty=faculty,
                blocks=blocks,
                assignments=assignments,
            )

            # Log if schedule creates concerning conditions
            if report.overall_status in ("critical", "emergency"):
                logger.warning(
                    f"Post-generation resilience check: {report.overall_status.upper()}. "
                    f"Generated schedule may create stress conditions. "
                    f"Utilization: {report.utilization.utilization_rate:.0%}"
                )
            elif not report.n1_pass:
                logger.warning(
                    "Post-generation resilience check: N-1 FAIL. "
                    "Schedule is vulnerable to single faculty loss."
                )

            return report

        except Exception as e:
            logger.warning(f"Post-generation resilience check failed: {e}")
            return None

    def _get_resilience_warnings(self, health_report) -> list[str]:
        """Extract actionable warnings from health report."""
        warnings = []

        if health_report is None:
            return warnings

        # Utilization warnings
        if health_report.utilization.level.value in ("ORANGE", "RED", "BLACK"):
            warnings.append(
                f"High utilization ({health_report.utilization.utilization_rate:.0%}) - "
                f"approaching cascade failure risk"
            )

        # Contingency warnings
        if not health_report.n1_pass:
            warnings.append(
                "N-1 vulnerability: Schedule cannot survive loss of one key faculty member"
            )
        if not health_report.n2_pass:
            warnings.append(
                "N-2 vulnerability: Schedule cannot survive loss of two faculty members"
            )

        # Phase transition warning
        if health_report.phase_transition_risk in ("high", "critical"):
            warnings.append(
                f"Phase transition risk is {health_report.phase_transition_risk} - "
                f"system may experience sudden degradation"
            )

        # Buffer warning
        if health_report.utilization.buffer_remaining < 0.10:
            warnings.append(
                f"Buffer critically low ({health_report.utilization.buffer_remaining:.0%}) - "
                f"no capacity for unexpected absences"
            )

        return warnings
