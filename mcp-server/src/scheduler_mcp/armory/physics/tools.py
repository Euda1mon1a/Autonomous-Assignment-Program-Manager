"""
Physics Domain MCP Tools - Thermodynamics, Hopfield Networks, Time Crystals.

This module registers physics-inspired analysis tools when the physics
armory domain is activated.

Activation: ARMORY_DOMAINS="physics" or ARMORY_DOMAINS="all"

Tools (12):
- Thermodynamics: entropy, phase transitions, free energy (4)
- Hopfield: energy, attractors, basins, spurious patterns (5)
- Time Crystal: periodicity, rigidity, checkpoints (3)
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def register_physics_tools(mcp: "FastMCP") -> int:
    """
    Register all physics domain tools with the MCP server.

    Args:
        mcp: FastMCP server instance

    Returns:
        Number of tools registered
    """
    # Import response types and helper functions (... goes up two levels to scheduler_mcp)
    from ...thermodynamics_tools import (
        ScheduleEntropyResponse,
        EntropyMonitorStateResponse,
        PhaseTransitionRiskResponse,
        FreeEnergyOptimizationResponse,
        calculate_schedule_entropy,
        get_entropy_monitor_state,
        analyze_phase_transitions,
        optimize_free_energy,
    )
    from ...hopfield_attractor_tools import (
        HopfieldEnergyResponse,
        NearbyAttractorsResponse,
        BasinDepthResponse,
        SpuriousAttractorsResponse,
        EnergyLandscapeResponse,
        calculate_hopfield_energy,
        find_nearby_attractors,
        measure_basin_depth,
        detect_spurious_attractors,
        analyze_energy_landscape,
    )
    from ...time_crystal_tools import (
        SchedulePeriodicityResponse,
        TimeCrystalObjectiveResponse,
        CheckpointStatusResponse,
        TimeCrystalHealthResponse,
        analyze_schedule_periodicity,
        calculate_time_crystal_objective,
        get_checkpoint_status,
        get_time_crystal_health,
    )

    tools_registered = 0

    # =========================================================================
    # Thermodynamics Tools
    # =========================================================================

    @mcp.tool()
    async def calculate_schedule_entropy_tool(
        start_date: str | None = None,
        end_date: str | None = None,
        include_mutual_information: bool = True,
    ) -> ScheduleEntropyResponse:
        """
        Calculate comprehensive entropy metrics for the schedule.

        Entropy measures the disorder/randomness in schedule assignment distribution.
        This tool applies Shannon entropy analysis across multiple dimensions.

        **Entropy Dimensions Analyzed:**
        - Person Entropy: Distribution of assignments across faculty
        - Rotation Entropy: Distribution across rotation types
        - Time Entropy: Distribution across time blocks
        - Joint Entropy: Combined person-rotation distribution
        - Mutual Information: How much knowing the person tells about the rotation

        Args:
            start_date: Start date for analysis (YYYY-MM-DD), defaults to today
            end_date: End date for analysis (YYYY-MM-DD), defaults to 30 days
            include_mutual_information: Calculate mutual information between dimensions

        Returns:
            ScheduleEntropyResponse with entropy metrics and interpretation
        """
        return await calculate_schedule_entropy(
            start_date=start_date,
            end_date=end_date,
            include_mutual_information=include_mutual_information,
        )

    tools_registered += 1

    @mcp.tool()
    async def get_entropy_monitor_state_tool(
        history_window: int = 100,
    ) -> EntropyMonitorStateResponse:
        """
        Get current state of the entropy monitor for early warning detection.

        The entropy monitor tracks entropy dynamics over time to detect:
        - Critical slowing down (entropy changes slow near phase transitions)
        - Rapid entropy changes (system instability)
        - Entropy production rate (energy dissipation)

        Args:
            history_window: Number of entropy measurements to analyze (10-1000)

        Returns:
            EntropyMonitorStateResponse with current monitor state
        """
        return await get_entropy_monitor_state(history_window=history_window)

    tools_registered += 1

    @mcp.tool()
    async def analyze_phase_transitions_tool(
        metrics: dict[str, list[float]] | None = None,
        window_size: int = 50,
    ) -> PhaseTransitionRiskResponse:
        """
        Detect approaching phase transitions using critical phenomena theory.

        Applies physics-based early warning signal detection to identify when
        the scheduling system is approaching a phase transition (failure).

        **Universal Early Warning Signals:**
        1. Increasing Variance - Fluctuations diverge before transitions
        2. Critical Slowing Down - Response time increases near critical point
        3. Flickering - Rapid state switching near bistable points
        4. Skewness Changes - Distribution becomes asymmetric

        Args:
            metrics: Dictionary of metric_name -> time series values
            window_size: Analysis window size for signal detection (10-200)

        Returns:
            PhaseTransitionRiskResponse with detected signals and recommendations
        """
        return await analyze_phase_transitions(
            metrics=metrics,
            window_size=window_size,
        )

    tools_registered += 1

    @mcp.tool()
    async def optimize_free_energy_tool(
        schedule_id: str | None = None,
        target_temperature: float = 1.0,
        max_iterations: int = 100,
    ) -> FreeEnergyOptimizationResponse:
        """
        Optimize schedule using free energy minimization.

        **NOTE: This module is planned but not yet implemented.**

        Applies thermodynamic principles to find optimal schedule configurations
        by balancing Internal Energy (U) and Entropy (S).

        Helmholtz Free Energy: F = U - TS

        Args:
            schedule_id: Schedule to optimize (or use current)
            target_temperature: Temperature parameter (higher = more exploration)
            max_iterations: Maximum optimization iterations

        Returns:
            FreeEnergyOptimizationResponse (placeholder until implemented)
        """
        return await optimize_free_energy(
            schedule_id=schedule_id,
            target_temperature=target_temperature,
            max_iterations=max_iterations,
        )

    tools_registered += 1

    # =========================================================================
    # Hopfield Network Tools
    # =========================================================================

    @mcp.tool()
    async def calculate_hopfield_energy_tool(
        start_date: str | None = None,
        end_date: str | None = None,
        schedule_id: str | None = None,
    ) -> HopfieldEnergyResponse:
        """
        Calculate Hopfield energy of the current schedule state.

        **Hopfield Energy Function:**
        E = -0.5 * sum_ij(w_ij * s_i * s_j)

        Lower energy = more stable configuration matching learned patterns.

        Args:
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)
            schedule_id: Optional specific schedule ID to analyze

        Returns:
            HopfieldEnergyResponse with energy metrics and stability assessment
        """
        return await calculate_hopfield_energy(
            start_date=start_date,
            end_date=end_date,
            schedule_id=schedule_id,
        )

    tools_registered += 1

    @mcp.tool()
    async def find_nearby_attractors_tool(
        max_distance: int = 10,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> NearbyAttractorsResponse:
        """
        Identify stable attractors near the current schedule state.

        Attractors are stable states (energy minima) that the system naturally
        evolves toward. Finding nearby attractors shows alternative stable
        configurations.

        Args:
            max_distance: Maximum Hamming distance to search (1-50)
            start_date: Start date for analysis (YYYY-MM-DD)
            end_date: End date for analysis (YYYY-MM-DD)

        Returns:
            NearbyAttractorsResponse with identified attractors and recommendations
        """
        return await find_nearby_attractors(
            max_distance=max_distance,
            start_date=start_date,
            end_date=end_date,
        )

    tools_registered += 1

    @mcp.tool()
    async def measure_basin_depth_tool(
        attractor_id: str | None = None,
        num_perturbations: int = 100,
    ) -> BasinDepthResponse:
        """
        Measure the depth of the basin of attraction for current or specified attractor.

        Basin depth is the energy barrier that must be overcome to escape.
        Deeper basins = more robust schedules.

        Args:
            attractor_id: Specific attractor to analyze (defaults to nearest)
            num_perturbations: Number of random perturbations to test (10-1000)

        Returns:
            BasinDepthResponse with stability metrics and robustness assessment
        """
        return await measure_basin_depth(
            attractor_id=attractor_id,
            num_perturbations=num_perturbations,
        )

    tools_registered += 1

    @mcp.tool()
    async def detect_spurious_attractors_tool(
        search_radius: int = 20,
        min_basin_size: int = 10,
    ) -> SpuriousAttractorsResponse:
        """
        Detect spurious attractors (unintended stable patterns / scheduling anti-patterns).

        Spurious attractors are stable states that were NOT part of training patterns.
        In scheduling, these are anti-patterns like concentrated overload.

        Args:
            search_radius: Hamming distance to search for spurious attractors (5-50)
            min_basin_size: Minimum basin size to report (avoid noise)

        Returns:
            SpuriousAttractorsResponse with anti-patterns and mitigation strategies
        """
        return await detect_spurious_attractors(
            search_radius=search_radius,
            min_basin_size=min_basin_size,
        )

    tools_registered += 1

    @mcp.tool()
    async def analyze_energy_landscape_tool(
        schedule_id: str | None = None,
    ) -> EnergyLandscapeResponse:
        """
        Analyze the energy landscape around current schedule.

        **NOTE: This module is planned but not yet implemented.**

        Maps stability of current schedule and nearby alternatives.

        Args:
            schedule_id: Schedule to analyze (or use current)

        Returns:
            EnergyLandscapeResponse with stability analysis (placeholder)
        """
        return await analyze_energy_landscape(schedule_id=schedule_id)

    tools_registered += 1

    # =========================================================================
    # Time Crystal Tools
    # =========================================================================

    @mcp.tool()
    async def analyze_schedule_periodicity_tool(
        assignments: list[dict] | None = None,
        schedule_id: str | None = None,
        base_period_days: int = 7,
    ) -> SchedulePeriodicityResponse:
        """
        Analyze natural periodicities in a schedule.

        Time crystal insight: Medical schedules have natural "drive periods"
        (7 days, 28 days) and emergent "subharmonic responses" (alternating
        weekends, Q4 call patterns).

        Args:
            assignments: Schedule as list of dicts with {person_id, block_id, date}
            schedule_id: Alternative: ID of schedule in database
            base_period_days: Base period to look for (default: 7 for weekly)

        Returns:
            SchedulePeriodicityResponse with detected patterns and recommendations
        """
        return await analyze_schedule_periodicity(
            assignments=assignments,
            schedule_id=schedule_id,
            base_period_days=base_period_days,
        )

    tools_registered += 1

    @mcp.tool()
    async def calculate_time_crystal_objective_tool(
        current_assignments: list[dict],
        proposed_assignments: list[dict],
        constraint_results: list[dict] | None = None,
        alpha: float = 0.3,
        beta: float = 0.1,
    ) -> TimeCrystalObjectiveResponse:
        """
        Calculate time-crystal-inspired optimization objective.

        Combines constraint satisfaction with anti-churn (rigidity) to create
        schedules that are BOTH compliant AND stable.

        Objective: score = (1-α-β) * constraints + α * rigidity + β * fairness

        Args:
            current_assignments: Current schedule assignments
            proposed_assignments: Proposed schedule assignments
            constraint_results: Optional constraint evaluation results
            alpha: Weight for rigidity (0.0-1.0, default 0.3)
            beta: Weight for fairness (0.0-1.0, default 0.1)

        Returns:
            TimeCrystalObjectiveResponse with component breakdown
        """
        return await calculate_time_crystal_objective(
            current_assignments=current_assignments,
            proposed_assignments=proposed_assignments,
            constraint_results=constraint_results,
            alpha=alpha,
            beta=beta,
        )

    tools_registered += 1

    @mcp.tool()
    async def get_checkpoint_status_tool(
        schedule_id: str | None = None,
    ) -> CheckpointStatusResponse:
        """
        Get current stroboscopic checkpoint status.

        Time crystal insight: Schedule state advances only at discrete checkpoints
        (week boundaries, block transitions) - not continuously.

        Args:
            schedule_id: Optional specific schedule to check

        Returns:
            CheckpointStatusResponse with checkpoint state
        """
        return await get_checkpoint_status(schedule_id=schedule_id)

    tools_registered += 1

    logger.info(f"Physics domain: registered {tools_registered} tools")
    return tools_registered
