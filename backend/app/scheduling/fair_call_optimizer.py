"""
Fair call scheduling optimizer using OR-Tools CP-SAT solver.

This module implements max-min fairness for distributing call shifts among faculty,
minimizing the maximum deviation from target call counts while respecting eligibility
constraints and individual unavailability.

Algorithm:
    1. Primary objective: Minimize maximum deviation from target calls (max-min fairness)
    2. Secondary objective: Minimize sum of deviations (lexicographic optimization)

The solver uses a two-phase approach:
    - Phase 1: Find minimum possible max_deviation
    - Phase 2: Fix max_deviation and minimize sum of absolute deviations

Example:
    >>> input_data = CallScheduleInput(
    ...     days=[date(2025, 1, 1), date(2025, 1, 2)],
    ...     faculty=["FAC-001", "FAC-002"],
    ...     target_calls={"FAC-001": 1, "FAC-002": 1},
    ...     eligibility={
    ...         date(2025, 1, 1): {"FAC-001", "FAC-002"},
    ...         date(2025, 1, 2): {"FAC-001", "FAC-002"}
    ...     }
    ... )
    >>> result = optimize_call_schedule(input_data)
    >>> assert result.status == "optimal"
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from time import time
from typing import Optional

from ortools.sat.python import cp_model


logger = logging.getLogger(__name__)


@dataclass
class CallScheduleInput:
    """
    Input data for call schedule optimization.

    Attributes:
        days: List of dates to schedule call shifts for (e.g., all Fridays/Saturdays)
        faculty: List of faculty IDs eligible for call
        target_calls: Target number of call shifts per faculty member (faculty_id -> count)
        eligibility: Which faculty are eligible for each day (date -> set of faculty_ids)
        max_calls: Optional hard caps on calls per faculty (faculty_id -> max_count)
    """

    days: list[date]
    faculty: list[str]
    target_calls: dict[str, int]
    eligibility: dict[date, set[str]]
    max_calls: dict[str, int] | None = None


@dataclass
class CallScheduleResult:
    """
    Result of call schedule optimization.

    Attributes:
        schedule: Assignment of faculty to call days (date -> faculty_id)
        deviations: Actual deviation from target for each faculty (faculty_id -> actual - target)
        max_deviation: Maximum absolute deviation across all faculty
        solve_time_seconds: Time taken to solve the optimization problem
        status: Solver status ("optimal", "feasible", "infeasible", "unknown")
        objective_value: Final objective value (sum of absolute deviations in phase 2)
    """

    schedule: dict[date, str]
    deviations: dict[str, int]
    max_deviation: int
    solve_time_seconds: float
    status: str
    objective_value: int = 0


class CallScheduleModel:
    """
    OR-Tools CP-SAT model for fair call scheduling.

    This class encapsulates the constraint programming model, including:
    - Binary assignment variables (is_assigned[day][faculty])
    - Call count variables per faculty
    - Deviation variables (positive/negative/absolute)
    - Max deviation variable for min-max fairness
    """

    def __init__(self, input_data: CallScheduleInput):
        """
        Initialize the call schedule model.

        Args:
            input_data: Input parameters for the scheduling problem
        """
        self.input = input_data
        self.model = cp_model.CpModel()

        # Decision variables
        self.is_assigned: dict[date, dict[str, cp_model.IntVar]] = {}
        self.calls_assigned: dict[str, cp_model.IntVar] = {}
        self.deviation: dict[str, cp_model.IntVar] = {}
        self.abs_deviation: dict[str, cp_model.IntVar] = {}
        self.max_deviation: cp_model.IntVar = None

        self._build_model()

    def _build_model(self) -> None:
        """Build the constraint programming model with all variables and constraints."""
        self._create_variables()
        self._add_coverage_constraints()
        self._add_eligibility_constraints()
        self._add_call_count_constraints()
        self._add_deviation_constraints()
        self._add_max_calls_constraints()

    def _create_variables(self) -> None:
        """Create decision variables for the optimization problem."""
        # Binary assignment variables: is_assigned[day][faculty] = 1 if faculty on call that day
        for day in self.input.days:
            self.is_assigned[day] = {}
            for fac in self.input.faculty:
                var_name = f"assign_{day.isoformat()}_{fac}"
                self.is_assigned[day][fac] = self.model.NewBoolVar(var_name)

        # Total calls assigned to each faculty member
        max_possible_calls = len(self.input.days)
        for fac in self.input.faculty:
            var_name = f"calls_{fac}"
            self.calls_assigned[fac] = self.model.NewIntVar(
                0, max_possible_calls, var_name
            )

        # Deviation from target (can be positive or negative)
        for fac in self.input.faculty:
            target = self.input.target_calls.get(fac, 0)
            # Allow deviations from -target to +max_possible_calls
            var_name = f"deviation_{fac}"
            self.deviation[fac] = self.model.NewIntVar(
                -target, max_possible_calls, var_name
            )

        # Absolute deviation (always non-negative)
        for fac in self.input.faculty:
            var_name = f"abs_dev_{fac}"
            self.abs_deviation[fac] = self.model.NewIntVar(
                0, max_possible_calls, var_name
            )

        # Maximum deviation across all faculty (for min-max fairness)
        self.max_deviation = self.model.NewIntVar(
            0, max_possible_calls, "max_deviation"
        )

    def _add_coverage_constraints(self) -> None:
        """Ensure exactly one faculty member is assigned to each call day."""
        for day in self.input.days:
            # Exactly one faculty member per day
            self.model.Add(
                sum(self.is_assigned[day][fac] for fac in self.input.faculty) == 1
            )

    def _add_eligibility_constraints(self) -> None:
        """Enforce faculty eligibility constraints (e.g., only inpatient faculty on Fri/Sat)."""
        for day in self.input.days:
            eligible_faculty = self.input.eligibility.get(day, set())

            for fac in self.input.faculty:
                if fac not in eligible_faculty:
                    # Faculty not eligible for this day - force assignment to 0
                    self.model.Add(self.is_assigned[day][fac] == 0)

    def _add_call_count_constraints(self) -> None:
        """Link binary assignment variables to total call counts per faculty."""
        for fac in self.input.faculty:
            # Sum of assignments across all days equals total calls for this faculty
            total_calls = sum(self.is_assigned[day][fac] for day in self.input.days)
            self.model.Add(self.calls_assigned[fac] == total_calls)

    def _add_deviation_constraints(self) -> None:
        """
        Calculate deviations from target and their absolute values.

        Uses linearization technique for absolute value:
            abs_deviation >= deviation
            abs_deviation >= -deviation
        """
        for fac in self.input.faculty:
            target = self.input.target_calls.get(fac, 0)

            # deviation = actual - target
            self.model.Add(self.deviation[fac] == self.calls_assigned[fac] - target)

            # Absolute value linearization:
            # abs_deviation >= deviation
            self.model.Add(self.abs_deviation[fac] >= self.deviation[fac])
            # abs_deviation >= -deviation
            self.model.Add(self.abs_deviation[fac] >= -self.deviation[fac])

            # Max deviation tracking
            self.model.Add(self.max_deviation >= self.abs_deviation[fac])

    def _add_max_calls_constraints(self) -> None:
        """Add optional hard caps on maximum calls per faculty member."""
        if self.input.max_calls:
            for fac, max_cap in self.input.max_calls.items():
                if fac in self.input.faculty:
                    self.model.Add(self.calls_assigned[fac] <= max_cap)

    def minimize_max_deviation(
        self, time_limit_seconds: float
    ) -> cp_model.CpSolverStatus:
        """
        Phase 1: Minimize the maximum deviation (max-min fairness).

        Args:
            time_limit_seconds: Solver time limit

        Returns:
            Solver status after optimization
        """
        self.model.Minimize(self.max_deviation)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.log_search_progress = False

        status = solver.Solve(self.model)

        logger.info(
            f"Phase 1 (min max_dev): status={solver.StatusName(status)}, "
            f"max_dev={solver.Value(self.max_deviation) if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else 'N/A'}, "
            f"time={solver.WallTime():.2f}s"
        )

        return status

    def minimize_sum_deviations(
        self, fixed_max_dev: int, time_limit_seconds: float
    ) -> tuple[cp_model.CpSolverStatus, cp_model.CpSolver]:
        """
        Phase 2: Minimize sum of absolute deviations with max_deviation fixed.

        Args:
            fixed_max_dev: The maximum deviation value from phase 1
            time_limit_seconds: Solver time limit

        Returns:
            Tuple of (solver status, solver instance for extracting solution)
        """
        # Fix max_deviation to the value found in phase 1
        self.model.Add(self.max_deviation == fixed_max_dev)

        # New objective: minimize sum of absolute deviations
        sum_abs_dev = sum(self.abs_deviation[fac] for fac in self.input.faculty)
        self.model.Minimize(sum_abs_dev)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.log_search_progress = False

        status = solver.Solve(self.model)

        logger.info(
            f"Phase 2 (min sum_dev): status={solver.StatusName(status)}, "
            f"sum_dev={solver.ObjectiveValue() if status in [cp_model.OPTIMAL, cp_model.FEASIBLE] else 'N/A'}, "
            f"time={solver.WallTime():.2f}s"
        )

        return status, solver

    def extract_solution(self, solver: cp_model.CpSolver) -> dict[date, str]:
        """
        Extract the schedule assignment from the solved model.

        Args:
            solver: Solved CP-SAT solver instance

        Returns:
            Dictionary mapping each call day to the assigned faculty member
        """
        schedule = {}
        for day in self.input.days:
            for fac in self.input.faculty:
                if solver.Value(self.is_assigned[day][fac]) == 1:
                    schedule[day] = fac
                    break
        return schedule

    def extract_deviations(self, solver: cp_model.CpSolver) -> dict[str, int]:
        """
        Extract actual deviations from target for each faculty member.

        Args:
            solver: Solved CP-SAT solver instance

        Returns:
            Dictionary mapping faculty_id to (actual - target) deviation
        """
        return {fac: solver.Value(self.deviation[fac]) for fac in self.input.faculty}


def optimize_call_schedule(
    input_data: CallScheduleInput, time_limit_seconds: float = 30.0
) -> CallScheduleResult:
    """
    Optimize call schedule using max-min fairness with two-phase approach.

    Phase 1: Minimize maximum deviation from target calls (ensures fairness)
    Phase 2: Minimize sum of deviations while maintaining optimal max_deviation

    This lexicographic optimization ensures:
    1. No faculty member is excessively over/under-assigned relative to others
    2. Among all solutions with minimal max_deviation, choose the most balanced overall

    Args:
        input_data: Call schedule input parameters (days, faculty, targets, eligibility)
        time_limit_seconds: Maximum solver time per phase (default: 30s each phase)

    Returns:
        CallScheduleResult containing the optimized schedule and statistics

    Raises:
        ValueError: If input data is invalid (e.g., no days, no faculty, mismatched targets)

    Example:
        >>> input_data = CallScheduleInput(
        ...     days=[date(2025, 1, 3), date(2025, 1, 10)],  # Fridays
        ...     faculty=["FAC-001", "FAC-002", "FAC-003"],
        ...     target_calls={"FAC-001": 3, "FAC-002": 3, "FAC-003": 2},
        ...     eligibility={
        ...         date(2025, 1, 3): {"FAC-001", "FAC-002"},
        ...         date(2025, 1, 10): {"FAC-001", "FAC-003"}
        ...     }
        ... )
        >>> result = optimize_call_schedule(input_data, time_limit_seconds=10.0)
        >>> print(f"Status: {result.status}, Max deviation: {result.max_deviation}")
    """
    start_time = time()

    # Validate input
    _validate_input(input_data)

    logger.info(
        f"Starting call schedule optimization: {len(input_data.days)} days, "
        f"{len(input_data.faculty)} faculty"
    )

    # Build the constraint programming model
    model = CallScheduleModel(input_data)

    # Phase 1: Minimize maximum deviation
    phase1_status = model.minimize_max_deviation(time_limit_seconds)

    if phase1_status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Infeasible or error - return early
        total_time = time() - start_time
        status_name = _status_to_string(phase1_status)
        logger.warning(f"Phase 1 failed with status: {status_name}")

        return CallScheduleResult(
            schedule={},
            deviations={},
            max_deviation=0,
            solve_time_seconds=total_time,
            status=status_name,
        )

    # Extract the optimal max_deviation value from phase 1
    # Need to solve again to get solver instance with solution
    temp_solver = cp_model.CpSolver()
    temp_solver.parameters.max_time_in_seconds = time_limit_seconds
    temp_solver.Solve(model.model)
    fixed_max_dev = temp_solver.Value(model.max_deviation)

    # Phase 2: Minimize sum of deviations with max_deviation fixed
    phase2_status, final_solver = model.minimize_sum_deviations(
        fixed_max_dev, time_limit_seconds
    )

    if phase2_status not in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Phase 2 failed - return phase 1 solution
        logger.warning("Phase 2 failed, returning phase 1 solution")
        schedule = model.extract_solution(temp_solver)
        deviations = model.extract_deviations(temp_solver)
        max_dev = temp_solver.Value(model.max_deviation)
        total_time = time() - start_time

        return CallScheduleResult(
            schedule=schedule,
            deviations=deviations,
            max_deviation=max_dev,
            solve_time_seconds=total_time,
            status=_status_to_string(phase1_status),
            objective_value=sum(abs(d) for d in deviations.values()),
        )

    # Extract final solution from phase 2
    schedule = model.extract_solution(final_solver)
    deviations = model.extract_deviations(final_solver)
    max_dev = final_solver.Value(model.max_deviation)
    total_time = time() - start_time

    # Determine overall status (optimal only if both phases optimal)
    if phase1_status == cp_model.OPTIMAL and phase2_status == cp_model.OPTIMAL:
        final_status = "optimal"
    else:
        final_status = "feasible"

    logger.info(
        f"Optimization complete: status={final_status}, max_dev={max_dev}, "
        f"sum_abs_dev={final_solver.ObjectiveValue()}, time={total_time:.2f}s"
    )

    return CallScheduleResult(
        schedule=schedule,
        deviations=deviations,
        max_deviation=max_dev,
        solve_time_seconds=total_time,
        status=final_status,
        objective_value=int(final_solver.ObjectiveValue()),
    )


def _validate_input(input_data: CallScheduleInput) -> None:
    """
    Validate call schedule input data.

    Args:
        input_data: Input to validate

    Raises:
        ValueError: If input is invalid
    """
    if not input_data.days:
        raise ValueError("No call days provided")

    if not input_data.faculty:
        raise ValueError("No faculty members provided")

    # Check that all faculty have target_calls defined
    for fac in input_data.faculty:
        if fac not in input_data.target_calls:
            raise ValueError(f"Faculty {fac} missing target_calls entry")

    # Check that all days have eligibility defined
    for day in input_data.days:
        if day not in input_data.eligibility:
            raise ValueError(f"Day {day} missing eligibility entry")

        if not input_data.eligibility[day]:
            raise ValueError(f"Day {day} has no eligible faculty")

    # Check that eligibility only references valid faculty
    all_faculty_set = set(input_data.faculty)
    for day, eligible in input_data.eligibility.items():
        invalid = eligible - all_faculty_set
        if invalid:
            raise ValueError(f"Day {day} references unknown faculty: {invalid}")


def _status_to_string(status: cp_model.CpSolverStatus) -> str:
    """
    Convert CP-SAT solver status to human-readable string.

    Args:
        status: OR-Tools solver status code

    Returns:
        Status string ("optimal", "feasible", "infeasible", "unknown")
    """
    if status == cp_model.OPTIMAL:
        return "optimal"
    elif status == cp_model.FEASIBLE:
        return "feasible"
    elif status == cp_model.INFEASIBLE:
        return "infeasible"
    else:
        return "unknown"
