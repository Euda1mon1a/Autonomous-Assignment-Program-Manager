"""
Performance Optimizer for Scheduling Engine.

Provides utilities to reduce solver complexity through:
- Context pre-processing
- Infeasible assignment pruning
- Block clustering for batch processing
- Complexity estimation for solver selection
"""
import logging
from collections import defaultdict
from functools import lru_cache
from uuid import UUID

from app.scheduling.constraints import SchedulingContext

logger = logging.getLogger(__name__)


class SchedulingOptimizer:
    """
    Optimizes scheduling context to reduce solver complexity.

    Features:
    - Pre-process context to remove infeasible assignments
    - Cluster similar blocks for batch processing
    - Estimate problem complexity for solver selection
    - Lazy loading patterns for large datasets
    """

    def __init__(self, enable_caching: bool = True):
        """
        Initialize optimizer.

        Args:
            enable_caching: Enable LRU caching for expensive operations
        """
        self.enable_caching = enable_caching
        self._availability_cache: dict = {}

    def optimize_context(self, context: SchedulingContext) -> SchedulingContext:
        """
        Pre-process context to reduce solver complexity.

        Optimizations:
        - Remove unavailable resident-block pairs
        - Filter out templates with impossible capacity
        - Build efficient lookup structures

        Args:
            context: Original scheduling context

        Returns:
            Optimized scheduling context
        """
        logger.info("Optimizing scheduling context...")

        # Count optimizations
        original_resident_count = len(context.residents)
        original_block_count = len(context.blocks)

        # Filter residents with no availability
        active_residents = self._filter_active_residents(context)

        # Filter blocks that have available residents
        assignable_blocks = self._filter_assignable_blocks(context, active_residents)

        # Update context with filtered data
        context.residents = active_residents
        context.blocks = assignable_blocks

        # Rebuild indices
        context.resident_idx = {r.id: i for i, r in enumerate(context.residents)}
        context.block_idx = {b.id: i for i, b in enumerate(context.blocks)}

        logger.info(
            f"Optimization complete: {original_resident_count} -> {len(active_residents)} residents, "
            f"{original_block_count} -> {len(assignable_blocks)} blocks"
        )

        return context

    def prune_infeasible_assignments(
        self,
        context: SchedulingContext,
        availability: dict[UUID, dict[UUID, dict]],
    ) -> set[tuple[UUID, UUID]]:
        """
        Remove impossible assignments early based on availability.

        Args:
            context: Scheduling context
            availability: Availability matrix

        Returns:
            Set of feasible (resident_id, block_id) pairs
        """
        feasible = set()

        for resident in context.residents:
            for block in context.blocks:
                # Skip weekends for primary assignments
                if block.is_weekend:
                    continue

                # Check availability
                if resident.id in availability:
                    if block.id in availability[resident.id]:
                        if availability[resident.id][block.id].get("available", True):
                            feasible.add((resident.id, block.id))
                    else:
                        feasible.add((resident.id, block.id))
                else:
                    feasible.add((resident.id, block.id))

        logger.debug(f"Pruned to {len(feasible)} feasible assignments")
        return feasible

    def cluster_similar_blocks(
        self,
        blocks: list,
        cluster_by: str = "week",
    ) -> dict[str, list]:
        """
        Group blocks for batch processing.

        Clustering strategies:
        - week: Group by calendar week
        - month: Group by month
        - consecutive: Group consecutive days

        Args:
            blocks: List of Block objects
            cluster_by: Clustering strategy

        Returns:
            Dictionary mapping cluster key to block list
        """
        clusters = defaultdict(list)

        for block in blocks:
            if cluster_by == "week":
                # ISO week number
                week_key = f"{block.date.year}-W{block.date.isocalendar()[1]:02d}"
                clusters[week_key].append(block)
            elif cluster_by == "month":
                month_key = f"{block.date.year}-{block.date.month:02d}"
                clusters[month_key].append(block)
            elif cluster_by == "consecutive":
                # Group by block_number (28-day rotations)
                clusters[f"block_{block.block_number}"].append(block)
            else:
                # Default: one cluster per day
                clusters[block.date.isoformat()].append(block)

        logger.debug(f"Created {len(clusters)} block clusters using '{cluster_by}' strategy")
        return dict(clusters)

    @lru_cache(maxsize=128)
    def estimate_complexity(self, context: SchedulingContext) -> dict[str, float]:
        """
        Estimate problem complexity to recommend appropriate solver.

        Analyzes the scheduling problem to estimate computational complexity
        and recommend the most suitable solver algorithm. This helps avoid
        timeouts and ensures good performance.

        Complexity Factors:
            1. **Variable Count**: residents × blocks × templates
               - Determines search space size
               - More variables = harder problem

            2. **Constraint Density**: constraints / variables
               - Higher density = more restricted search space
               - Can make problem easier (pruning) or harder (conflicts)

            3. **Availability Sparsity**: unavailable_slots / total_slots
               - More unavailability = smaller search space (easier)
               - Sparsity > 0.3 significantly reduces complexity

        Complexity Score (0-100):
            - **0-20**: Simple problem
              - Recommended: "greedy" solver
              - Expected runtime: <1 second

            - **20-50**: Moderate complexity
              - Recommended: "pulp" solver
              - Expected runtime: 1-10 seconds

            - **50-75**: Complex problem
              - Recommended: "cp_sat" solver
              - Expected runtime: 10-60 seconds

            - **75-100**: Very complex problem
              - Recommended: "hybrid" solver
              - Expected runtime: 60-300 seconds

        Args:
            context: SchedulingContext with residents, blocks, templates, availability
                    (Note: LRU cache requires hashable inputs - in practice,
                    pass summary statistics instead of full context)

        Returns:
            dict: Complexity analysis with:
                - score (float): Complexity score (0-100)
                - variables (int): Estimated decision variable count
                - constraints (int): Estimated constraint count
                - sparsity (float): Availability sparsity (0.0-1.0)
                - recommended_solver (str): Suggested algorithm name

        Example:
            >>> optimizer = SchedulingOptimizer()
            >>> complexity = optimizer.estimate_complexity(context)
            >>> print(f"Complexity: {complexity['score']:.1f}")
            >>> print(f"Recommended: {complexity['recommended_solver']}")
            >>> # Output:
            >>> # Complexity: 35.2
            >>> # Recommended: pulp

        Note:
            This is a heuristic estimate. Actual solving difficulty may vary
            based on constraint interactions and problem structure.
        """
        # Note: This requires context to be hashable, which it's not by default
        # In practice, we'd pass summary stats instead
        num_residents = len(context.residents)
        num_blocks = len(context.blocks)
        num_templates = len(context.templates)

        # Estimate variable count (3D: resident × block × template)
        variables = num_residents * num_blocks * num_templates

        # Estimate constraints
        # - Availability: residents × blocks
        # - One per block: blocks
        # - 80-hour rule: residents × date_windows
        # - 1-in-7 rule: residents × date_windows
        date_range = (context.end_date - context.start_date).days if context.end_date and context.start_date else 28
        date_windows = max(1, date_range // 7)

        constraints = (
            num_residents * num_blocks +  # Availability
            num_blocks +  # One per block
            num_residents * date_windows * 2  # 80-hour + 1-in-7
        )

        # Calculate sparsity (unavailable slots)
        total_slots = num_residents * num_blocks
        unavailable = 0
        for resident in context.residents:
            if resident.id in context.availability:
                for block in context.blocks:
                    if block.id in context.availability[resident.id]:
                        if not context.availability[resident.id][block.id].get("available", True):
                            unavailable += 1

        sparsity = unavailable / total_slots if total_slots > 0 else 0

        # Calculate complexity score (0-100)
        # Higher score = more complex problem
        base_score = min(100, (variables / 10000) * 50)
        constraint_factor = min(50, (constraints / variables) * 100) if variables > 0 else 0
        sparsity_penalty = sparsity * 20

        score = base_score + constraint_factor - sparsity_penalty

        # Recommend solver based on complexity
        if score < 20:
            recommended = "greedy"
        elif score < 50:
            recommended = "pulp"
        elif score < 75:
            recommended = "cp_sat"
        else:
            recommended = "hybrid"

        # Check if quantum-inspired solver might be beneficial
        # Quantum-inspired approaches excel at:
        # - Large problems with many local minima
        # - Problems where approximate solutions are acceptable
        # - High-complexity problems that timeout classical solvers
        quantum_recommended = score >= 60 or variables > 50000

        return {
            "score": round(score, 2),
            "variables": variables,
            "constraints": constraints,
            "sparsity": round(sparsity, 3),
            "recommended_solver": recommended,
            "quantum_recommended": quantum_recommended,
            "available_solvers": self._get_available_solvers(),
        }

    def _get_available_solvers(self) -> list[str]:
        """Get list of available solver algorithms."""
        solvers = ["greedy", "pulp", "cp_sat", "hybrid"]

        # Check for quantum-inspired solvers
        try:
            from app.scheduling.quantum import get_quantum_library_status
            status = get_quantum_library_status()
            if status.get("dwave_samplers") or status.get("pyqubo"):
                solvers.append("quantum_inspired")
            if status.get("dwave_system"):
                solvers.append("quantum_hardware")
        except ImportError:
            pass

        return solvers

    def _filter_active_residents(self, context: SchedulingContext) -> list:
        """Filter residents who have at least one available block."""
        active = []

        for resident in context.residents:
            has_availability = False

            # Check if resident has any available blocks
            for block in context.blocks:
                if block.is_weekend:
                    continue

                if resident.id in context.availability:
                    if block.id in context.availability[resident.id]:
                        if context.availability[resident.id][block.id].get("available", True):
                            has_availability = True
                            break
                    else:
                        has_availability = True
                        break
                else:
                    has_availability = True
                    break

            if has_availability:
                active.append(resident)

        return active

    def _filter_assignable_blocks(self, context: SchedulingContext, residents: list) -> list:
        """Filter blocks that have at least one available resident."""
        assignable = []

        for block in context.blocks:
            has_eligible = False

            # Check if any resident is available
            for resident in residents:
                if resident.id in context.availability:
                    if block.id in context.availability[resident.id]:
                        if context.availability[resident.id][block.id].get("available", True):
                            has_eligible = True
                            break
                    else:
                        has_eligible = True
                        break
                else:
                    has_eligible = True
                    break

            if has_eligible:
                assignable.append(block)

        return assignable
