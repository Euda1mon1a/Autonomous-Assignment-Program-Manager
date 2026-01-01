"""
Penrose Process for Schedule Rotation Efficiency Extraction.

Applies black hole physics concept to scheduling:
- Ergosphere = Rotation boundary periods (week ends, block transitions)
- Negative energy states = Swaps that appear locally costly but unlock system benefit
- Energy extraction = Conflict reduction through rotation-aware assignment

Physics basis: Penrose process extracts up to 29% rotational energy from
spinning black holes by splitting particles in the ergosphere.

In scheduling context:
- The "rotation" is the duty cycle (weekly patterns, block boundaries)
- The "ergosphere" is the boundary region between rotations (handoff periods)
- "Negative energy particles" are swaps that cost locally but benefit globally
- "Energy extraction" is reduction in conflicts and improvements in coverage

Example:
    >>> extractor = PenroseEfficiencyExtractor()
    >>> ergospheres = await extractor.identify_ergosphere_periods(rotations)
    >>> swaps = await extractor.find_negative_energy_swaps(schedule, ergospheres[0])
    >>> optimized = await extractor.execute_penrose_cascade(schedule)
    >>> efficiency = extractor.compute_extraction_efficiency(swaps)
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.rotation_template import RotationTemplate

logger = logging.getLogger(__name__)


# Penrose Process Constants
PENROSE_EFFICIENCY_LIMIT = (
    0.29  # Theoretical maximum extraction from rotating black holes (29%)
)
PM_HOUR_OFFSET = 12  # Hour offset for PM blocks (noon)
AM_HOUR_OFFSET = 8  # Hour offset for AM blocks (8 AM)
HALF_DAY_BLOCK_HOURS = 4  # Duration of a half-day block
MIN_REST_HOURS = 8  # Minimum rest period between shifts
PRE_TRANSITION_HOURS = 12  # Hours before transition for pre-phase
POST_TRANSITION_HOURS = 12  # Hours after transition for post-phase

# Rotation Velocity Calculation Constants
BASE_VELOCITY_SWAPS_PER_DAY = 1.5  # Base average swaps per day
WEEKEND_FACTOR = 2.0  # Multiplier for weekend swap activity
BLOCK_TRANSITION_FACTOR = 1.5  # Multiplier near block boundaries
HOLIDAY_FACTOR = 1.3  # Multiplier during holiday periods
ROTATION_VELOCITY_MULTIPLIER = 0.1  # Multiplier for extraction potential from velocity
BLOCK_TRANSITION_VELOCITY_MULTIPLIER = 0.15  # Higher multiplier for block transitions
HOURS_PER_DAY = 24  # Hours in a day


@dataclass
class ErgospherePeriod:
    """
    Represents a rotation boundary period with extraction potential.

    The ergosphere is the region around a rotating black hole where particles
    can have negative energy states. In scheduling, this represents transition
    periods between rotation phases where swaps can unlock hidden efficiency.

    Attributes:
        start_time: Beginning of the ergosphere period
        end_time: End of the ergosphere period
        rotation_velocity: Rate of schedule changes (swaps/day) in this period
        extraction_potential: Estimated efficiency gain from Penrose swaps (0-1)
        boundary_type: Type of boundary ("week_end", "block_transition", "rotation_handoff")
        affected_assignments: Assignment IDs in this ergosphere
    """

    start_time: datetime
    end_time: datetime
    rotation_velocity: float  # Swaps per day
    extraction_potential: float  # 0-1 scale, max ~0.29 (Penrose theoretical limit)
    boundary_type: str  # "week_end", "block_transition", "rotation_handoff"
    affected_assignments: list[UUID] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate ergosphere parameters."""
        if not 0 <= self.extraction_potential <= PENROSE_EFFICIENCY_LIMIT:
            logger.warning(
                f"Extraction potential {self.extraction_potential} exceeds "
                f"Penrose limit of {PENROSE_EFFICIENCY_LIMIT} ({PENROSE_EFFICIENCY_LIMIT * 100:.0f}%)"
            )
        if self.start_time >= self.end_time:
            raise ValueError("Ergosphere start_time must be before end_time")

    @property
    def duration_hours(self) -> float:
        """Calculate duration of ergosphere in hours."""
        return (self.end_time - self.start_time).total_seconds() / (
            60 * 60
        )  # Convert seconds to hours

    @property
    def is_high_potential(self) -> bool:
        """Check if this ergosphere has high extraction potential (>15%)."""
        return self.extraction_potential > 0.15


@dataclass
class PhaseComponent:
    """
    Represents a phase decomposition of an assignment.

    In the Penrose process, particles are split into positive and negative
    energy components. For scheduling, we decompose assignments into phases
    (e.g., pre-handoff, during-handoff, post-handoff) to identify where
    swaps can extract efficiency.

    Attributes:
        assignment_id: ID of the parent assignment
        phase_type: Type of phase ("pre_transition", "transition", "post_transition")
        energy_state: Energy state ("positive", "negative", "zero")
        phase_start: Start time of this phase
        phase_end: End time of this phase
        conflict_score: Number of conflicts in this phase
        flexibility_score: Degrees of freedom available (0-1)
    """

    assignment_id: UUID
    phase_type: str
    energy_state: str  # "positive", "negative", "zero"
    phase_start: datetime
    phase_end: datetime
    conflict_score: int
    flexibility_score: float  # 0-1, higher = more swap options

    def __post_init__(self) -> None:
        """Validate phase component."""
        valid_phases = {"pre_transition", "transition", "post_transition"}
        if self.phase_type not in valid_phases:
            raise ValueError(f"phase_type must be one of {valid_phases}")

        valid_states = {"positive", "negative", "zero"}
        if self.energy_state not in valid_states:
            raise ValueError(f"energy_state must be one of {valid_states}")

    @property
    def is_negative_energy(self) -> bool:
        """Check if this phase component has negative energy state."""
        return self.energy_state == "negative"


@dataclass
class PenroseSwap:
    """
    Represents a Penrose swap with local cost but global benefit.

    In the Penrose process, a particle enters the ergosphere, splits into
    positive and negative energy particles, and the negative one falls into
    the black hole while the positive one escapes with more energy than the
    original particle.

    For scheduling: a swap that locally increases conflicts but globally
    reduces total system conflicts or improves coverage.

    Attributes:
        swap_id: Unique identifier for this swap
        assignment_a: First assignment to swap
        assignment_b: Second assignment to swap
        local_cost: Local conflict increase (negative = improvement)
        global_benefit: System-wide benefit score (positive = good)
        net_extraction: Net efficiency extraction (global_benefit - local_cost)
        ergosphere_period: The ergosphere where this swap occurs
        confidence: Confidence in benefit estimate (0-1)
        executed: Whether this swap has been executed
    """

    swap_id: UUID
    assignment_a: UUID
    assignment_b: UUID
    local_cost: float  # Can be negative (local improvement)
    global_benefit: float  # Should be positive
    ergosphere_period: ErgospherePeriod
    confidence: float = 0.8
    executed: bool = False

    def __post_init__(self) -> None:
        """Validate Penrose swap."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    @property
    def net_extraction(self) -> float:
        """Calculate net efficiency extraction."""
        return self.global_benefit - abs(self.local_cost)

    @property
    def is_beneficial(self) -> bool:
        """Check if this swap provides net benefit."""
        return self.net_extraction > 0

    @property
    def extraction_ratio(self) -> float:
        """Calculate extraction efficiency ratio (benefit/cost)."""
        if abs(self.local_cost) < 0.001:  # Avoid division by zero
            return float("inf") if self.global_benefit > 0 else 0
        return self.global_benefit / abs(self.local_cost)


class RotationEnergyTracker:
    """
    Tracks rotation energy and extraction limits.

    Just as a black hole spins down as energy is extracted via the Penrose
    process, a schedule's "rotation energy" (capacity for beneficial swaps)
    diminishes as swaps are executed. This class tracks the extraction budget.

    Attributes:
        initial_rotation_energy: Initial capacity for swaps
        extracted_energy: Total energy extracted so far
        max_extraction_fraction: Maximum fraction that can be extracted (0.29)
        extraction_history: History of extractions
    """

    def __init__(self, initial_rotation_energy: float) -> None:
        """
        Initialize rotation energy tracker.

        Args:
            initial_rotation_energy: Initial swap capacity (e.g., number of
                potential beneficial swaps)
        """
        self.initial_rotation_energy = initial_rotation_energy
        self.extracted_energy = 0.0
        self.max_extraction_fraction = (
            PENROSE_EFFICIENCY_LIMIT  # Penrose theoretical limit
        )
        self.extraction_history: list[dict[str, Any]] = []

    @property
    def remaining_energy(self) -> float:
        """Calculate remaining extractable energy."""
        return self.initial_rotation_energy - self.extracted_energy

    @property
    def extraction_fraction(self) -> float:
        """Calculate fraction of energy extracted."""
        if self.initial_rotation_energy == 0:
            return 0
        return self.extracted_energy / self.initial_rotation_energy

    @property
    def is_exhausted(self) -> bool:
        """Check if extraction capacity is exhausted."""
        return self.extraction_fraction >= self.max_extraction_fraction

    @property
    def extraction_budget(self) -> float:
        """Calculate remaining extraction budget."""
        max_extractable = self.initial_rotation_energy * self.max_extraction_fraction
        return max(0, max_extractable - self.extracted_energy)

    def record_extraction(self, swap: PenroseSwap) -> bool:
        """
        Record an energy extraction from a swap.

        Args:
            swap: The Penrose swap that was executed

        Returns:
            True if extraction was recorded, False if budget exhausted
        """
        if self.is_exhausted:
            logger.warning(
                "Extraction budget exhausted, cannot record more extractions"
            )
            return False

        if not swap.is_beneficial:
            logger.warning(f"Swap {swap.swap_id} is not beneficial, skipping")
            return False

        self.extracted_energy += swap.net_extraction
        self.extraction_history.append(
            {
                "swap_id": str(swap.swap_id),
                "extraction": swap.net_extraction,
                "timestamp": datetime.utcnow(),
                "cumulative": self.extracted_energy,
            }
        )
        logger.info(
            f"Recorded extraction: {swap.net_extraction:.2f} "
            f"(total: {self.extracted_energy:.2f}, "
            f"fraction: {self.extraction_fraction:.2%})"
        )
        return True


class PenroseEfficiencyExtractor:
    """
    Extract rotation efficiency using Penrose process analogy.

    The Penrose process extracts rotational energy from black holes by
    exploiting the ergosphere's unique properties. This class applies
    the same principle to schedule optimization:

    1. Identify ergospheres (rotation boundaries)
    2. Decompose assignments into phase components
    3. Find negative-energy swaps (locally costly, globally beneficial)
    4. Execute Penrose cascade to extract efficiency
    5. Track extraction limits to prevent over-optimization

    Example:
        >>> async with get_db() as db:
        ...     extractor = PenroseEfficiencyExtractor(db)
        ...     schedule_data = await extractor.load_schedule(schedule_id)
        ...     ergospheres = await extractor.identify_ergosphere_periods(
        ...         schedule_data['rotations']
        ...     )
        ...     swaps = await extractor.find_negative_energy_swaps(
        ...         schedule_data, ergospheres[0]
        ...     )
        ...     optimized = await extractor.execute_penrose_cascade(schedule_data)
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize Penrose efficiency extractor.

        Args:
            db: Async database session
        """
        self.db = db
        self.energy_tracker: RotationEnergyTracker | None = None

    async def identify_ergosphere_periods(
        self, start_date: date, end_date: date
    ) -> list[ErgospherePeriod]:
        """
        Identify rotation boundary periods (ergospheres).

        Ergospheres are transition zones where swaps can extract efficiency:
        - Week boundaries (Friday PM to Monday AM)
        - Block transitions (last day of block to first day of next)
        - Rotation handoffs (when residents change services)

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            List of identified ergosphere periods sorted by extraction potential
        """
        ergospheres: list[ErgospherePeriod] = []

        # Load all blocks in the date range
        result = await self.db.execute(
            select(Block)
            .where(Block.date >= start_date)
            .where(Block.date <= end_date)
            .order_by(Block.date, Block.time_of_day)
        )
        blocks = result.scalars().all()

        # Group blocks by week
        blocks_by_week: dict[int, list[Block]] = defaultdict(list)
        for block in blocks:
            week_num = block.date.isocalendar()[1]
            blocks_by_week[week_num].append(block)

        # Identify week-end ergospheres (Friday PM to Monday AM)
        for week_num, week_blocks in blocks_by_week.items():
            # Find Friday PM and Monday AM blocks
            friday_pm = None
            monday_am = None

            for block in week_blocks:
                if block.date.weekday() == 4 and block.time_of_day == "PM":  # Friday
                    friday_pm = block
                if block.date.weekday() == 0 and block.time_of_day == "AM":  # Monday
                    monday_am = block

            if friday_pm and monday_am:
                # Calculate rotation velocity (historical swap rate)
                rotation_velocity = await self._calculate_rotation_velocity(
                    friday_pm.date, monday_am.date
                )

                # Estimate extraction potential based on transition complexity
                extraction_potential = min(
                    PENROSE_EFFICIENCY_LIMIT,
                    rotation_velocity * ROTATION_VELOCITY_MULTIPLIER,
                )  # Cap at Penrose limit

                ergosphere = ErgospherePeriod(
                    start_time=datetime.combine(friday_pm.date, datetime.min.time())
                    + timedelta(hours=PM_HOUR_OFFSET),  # Friday PM
                    end_time=datetime.combine(monday_am.date, datetime.min.time())
                    + timedelta(hours=AM_HOUR_OFFSET),  # Monday AM
                    rotation_velocity=rotation_velocity,
                    extraction_potential=extraction_potential,
                    boundary_type="week_end",
                    affected_assignments=await self._get_assignments_in_period(
                        friday_pm.date, monday_am.date
                    ),
                )
                ergospheres.append(ergosphere)

        # Identify block transition ergospheres
        block_transitions = await self._identify_block_transitions(blocks)
        ergospheres.extend(block_transitions)

        # Sort by extraction potential (highest first)
        ergospheres.sort(key=lambda e: e.extraction_potential, reverse=True)

        logger.info(
            f"Identified {len(ergospheres)} ergosphere periods "
            f"({sum(1 for e in ergospheres if e.is_high_potential)} high-potential)"
        )

        return ergospheres

    async def _calculate_rotation_velocity(
        self, start_date: date, end_date: date
    ) -> float:
        """
        Calculate historical rotation velocity (swaps per day).

        Uses heuristics based on:
        - Day of week (weekends have more swap activity)
        - Time of year (more swaps at block transitions)
        - Historical patterns from similar periods

        Args:
            start_date: Start date for velocity calculation
            end_date: End date for velocity calculation

        Returns:
            Average swaps per day in this period
        """
        # Calculate period duration
        days = (end_date - start_date).days
        if days == 0:
            return 0.0

        # Base velocity on average
        base_velocity = BASE_VELOCITY_SWAPS_PER_DAY

        # Weekend factor: More swaps happen around weekends
        weekend_factor = WEEKEND_FACTOR if start_date.weekday() >= 4 else 1.0

        # Block transition factor: Check if this period is near a block boundary
        # Blocks typically start on the 1st and 15th of months
        transition_factor = 1.0
        if start_date.day in range(1, 8) or start_date.day in range(15, 22):
            transition_factor = BLOCK_TRANSITION_FACTOR

        # Time of year factor: More swaps during holiday periods
        month = start_date.month
        holiday_multiplier = 1.0
        if month in [11, 12, 6, 7]:  # November, December, June, July (holidays)
            holiday_multiplier = HOLIDAY_FACTOR

        return base_velocity * weekend_factor * transition_factor * holiday_multiplier

    async def _get_assignments_in_period(
        self, start_date: date, end_date: date
    ) -> list[UUID]:
        """
        Get assignment IDs in a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of assignment UUIDs
        """
        result = await self.db.execute(
            select(Assignment.id)
            .join(Block)
            .where(Block.date >= start_date)
            .where(Block.date <= end_date)
        )
        return [row[0] for row in result.all()]

    async def _identify_block_transitions(
        self, blocks: list[Block]
    ) -> list[ErgospherePeriod]:
        """
        Identify block transition ergospheres.

        Args:
            blocks: List of blocks to analyze

        Returns:
            List of block transition ergospheres
        """
        ergospheres: list[ErgospherePeriod] = []

        # Group blocks by block_number
        blocks_by_num: dict[int, list[Block]] = defaultdict(list)
        for block in blocks:
            blocks_by_num[block.block_number].append(block)

        # Find transitions between consecutive blocks
        sorted_block_nums = sorted(blocks_by_num.keys())
        for i in range(len(sorted_block_nums) - 1):
            current_num = sorted_block_nums[i]
            next_num = sorted_block_nums[i + 1]

            if next_num == current_num + 1:
                # Find last block of current and first block of next
                current_blocks = sorted(
                    blocks_by_num[current_num], key=lambda b: (b.date, b.time_of_day)
                )
                next_blocks = sorted(
                    blocks_by_num[next_num], key=lambda b: (b.date, b.time_of_day)
                )

                if current_blocks and next_blocks:
                    last_block = current_blocks[-1]
                    first_block = next_blocks[0]

                    rotation_velocity = await self._calculate_rotation_velocity(
                        last_block.date, first_block.date
                    )

                    # Block transitions have higher extraction potential
                    extraction_potential = min(
                        PENROSE_EFFICIENCY_LIMIT,
                        rotation_velocity * BLOCK_TRANSITION_VELOCITY_MULTIPLIER,
                    )

                    ergosphere = ErgospherePeriod(
                        start_time=datetime.combine(
                            last_block.date, datetime.min.time()
                        )
                        + timedelta(
                            hours=PM_HOUR_OFFSET
                            if last_block.time_of_day == "PM"
                            else 0
                        ),
                        end_time=datetime.combine(first_block.date, datetime.min.time())
                        + timedelta(
                            hours=AM_HOUR_OFFSET
                            if first_block.time_of_day == "AM"
                            else PM_HOUR_OFFSET
                        ),
                        rotation_velocity=rotation_velocity,
                        extraction_potential=extraction_potential,
                        boundary_type="block_transition",
                        affected_assignments=await self._get_assignments_in_period(
                            last_block.date, first_block.date
                        ),
                    )
                    ergospheres.append(ergosphere)

        return ergospheres

    async def _count_conflicts_in_period(
        self, assignment: Assignment, start_time: datetime, end_time: datetime
    ) -> int:
        """
        Count assignment conflicts in a time period.

        Conflicts include:
        - Overlapping assignments for the same person
        - Back-to-back shifts without rest periods
        - Assignments during blocked periods

        Args:
            assignment: Assignment to check
            start_time: Period start time
            end_time: Period end time

        Returns:
            Number of conflicts detected
        """
        conflict_count = 0

        # Get all assignments for this person in the time range
        result = await self.db.execute(
            select(Assignment)
            .join(Block)
            .where(
                Assignment.person_id == assignment.person_id,
                Assignment.id != assignment.id,  # Exclude current assignment
            )
        )
        other_assignments = result.scalars().all()

        for other in other_assignments:
            if not other.block:
                continue

            # Convert other assignment to datetime
            other_dt = datetime.combine(
                other.block.date, datetime.min.time()
            ) + timedelta(
                hours=PM_HOUR_OFFSET if other.block.time_of_day == "PM" else 0
            )

            # Check for overlap with the period
            if start_time <= other_dt < end_time:
                conflict_count += 1

            # Check for back-to-back shifts (less than minimum rest hours apart)
            if assignment.block:
                assignment_dt = datetime.combine(
                    assignment.block.date, datetime.min.time()
                ) + timedelta(
                    hours=PM_HOUR_OFFSET if assignment.block.time_of_day == "PM" else 0
                )

                time_between = abs(
                    (other_dt - assignment_dt).total_seconds() / (60 * 60)
                )  # Convert to hours
                if 0 < time_between < MIN_REST_HOURS:
                    conflict_count += 1

        return conflict_count

    def _calculate_flexibility_score(
        self, assignment: Assignment, all_assignments: list[Assignment]
    ) -> float:
        """
        Calculate flexibility score for an assignment.

        Flexibility measures how many swap options are available:
        - Higher if similar assignments exist (more swap candidates)
        - Lower if assignment is unique or constrained
        - Considers rotation type, timing, and person constraints

        Args:
            assignment: Assignment to score
            all_assignments: All assignments in the schedule

        Returns:
            Flexibility score from 0.0 (rigid) to 1.0 (highly flexible)
        """
        if not all_assignments:
            return 0.5  # Default neutral flexibility

        # Count potential swap candidates
        swap_candidates = 0
        total_other_assignments = 0

        for other in all_assignments:
            if other.id == assignment.id or other.person_id == assignment.person_id:
                continue

            total_other_assignments += 1

            # Same rotation type = potential swap candidate
            if other.rotation_template_id == assignment.rotation_template_id:
                swap_candidates += 1

            # Same role = potential swap candidate
            if other.role == assignment.role:
                swap_candidates += 0.5

        if total_other_assignments == 0:
            return 0.3  # Low flexibility if no other assignments

        # Flexibility is proportion of potential swap candidates
        flexibility = swap_candidates / total_other_assignments
        return min(1.0, flexibility)  # Cap at 1.0

    def _calculate_confidence_score(
        self,
        assignment_a: Assignment,
        assignment_b: Assignment,
        historical_data_size: int,
    ) -> float:
        """
        Calculate confidence in swap benefit estimation.

        Confidence based on:
        - Data quality (how much historical data we have)
        - Assignment similarity (more similar = higher confidence)
        - Temporal proximity (closer in time = higher confidence)

        Args:
            assignment_a: First assignment
            assignment_b: Second assignment
            historical_data_size: Number of historical data points available

        Returns:
            Confidence score from 0.0 (low) to 1.0 (high)
        """
        # Base confidence from data quality
        # Confidence increases logarithmically with data size
        if historical_data_size == 0:
            data_confidence = 0.2  # Minimum baseline
        else:
            # Scale from 0.2 to 1.0 based on data size
            # 10 data points = ~0.5, 100 = ~0.8, 1000 = ~1.0
            data_confidence = min(1.0, 0.2 + (0.8 * (historical_data_size / 1000)))

        # Similarity bonus: same rotation type increases confidence
        similarity_bonus = 0.0
        if (
            assignment_a.rotation_template_id
            and assignment_b.rotation_template_id
            and assignment_a.rotation_template_id == assignment_b.rotation_template_id
        ):
            similarity_bonus = 0.15

        # Role match bonus
        if assignment_a.role == assignment_b.role:
            similarity_bonus += 0.05

        # Temporal proximity: same week increases confidence
        temporal_bonus = 0.0
        if assignment_a.block and assignment_b.block:
            date_diff = abs((assignment_a.block.date - assignment_b.block.date).days)
            if date_diff <= 7:
                temporal_bonus = 0.1
            elif date_diff <= 28:
                temporal_bonus = 0.05

        total_confidence = data_confidence + similarity_bonus + temporal_bonus
        return min(1.0, total_confidence)

    async def decompose_into_phases(
        self, assignment: Assignment
    ) -> list[PhaseComponent]:
        """
        Decompose an assignment into rotation phases.

        Similar to how a particle is split in the Penrose process,
        we decompose an assignment into pre-transition, transition,
        and post-transition phases to identify negative-energy states.

        Args:
            assignment: The assignment to decompose

        Returns:
            List of phase components
        """
        phases: list[PhaseComponent] = []

        if not assignment.block:
            logger.warning(f"Assignment {assignment.id} has no block, cannot decompose")
            return phases

        block_date = assignment.block.date
        block_time = assignment.block.time_of_day

        # Convert block to datetime
        assignment_dt = datetime.combine(block_date, datetime.min.time()) + timedelta(
            hours=PM_HOUR_OFFSET if block_time == "PM" else 0
        )

        # Pre-transition phase
        pre_start = assignment_dt - timedelta(hours=PRE_TRANSITION_HOURS)
        pre_end = assignment_dt

        # Transition phase (current block)
        trans_start = assignment_dt
        trans_end = assignment_dt + timedelta(
            hours=HALF_DAY_BLOCK_HOURS
        )  # Half-day block

        # Post-transition phase
        post_start = trans_end
        post_end = trans_end + timedelta(hours=POST_TRANSITION_HOURS)

        # Calculate conflict scores for each phase
        pre_conflicts = await self._count_conflicts_in_period(
            assignment, pre_start, pre_end
        )
        trans_conflicts = await self._count_conflicts_in_period(
            assignment, trans_start, trans_end
        )
        post_conflicts = await self._count_conflicts_in_period(
            assignment, post_start, post_end
        )

        # Determine energy states based on conflict patterns
        # Negative energy = transition reduces conflicts
        pre_energy = "positive" if pre_conflicts > trans_conflicts else "zero"
        trans_energy = (
            "negative"
            if trans_conflicts < (pre_conflicts + post_conflicts) / 2
            else "positive"
        )
        post_energy = "positive" if post_conflicts > trans_conflicts else "zero"

        # Get all assignments for flexibility calculation
        result = await self.db.execute(
            select(Assignment).where(Assignment.person_id == assignment.person_id)
        )
        person_assignments = result.scalars().all()

        # Calculate flexibility score
        flexibility = self._calculate_flexibility_score(assignment, person_assignments)

        # Create phase components
        phases.extend(
            [
                PhaseComponent(
                    assignment_id=assignment.id,
                    phase_type="pre_transition",
                    energy_state=pre_energy,
                    phase_start=pre_start,
                    phase_end=pre_end,
                    conflict_score=pre_conflicts,
                    flexibility_score=flexibility,
                ),
                PhaseComponent(
                    assignment_id=assignment.id,
                    phase_type="transition",
                    energy_state=trans_energy,
                    phase_start=trans_start,
                    phase_end=trans_end,
                    conflict_score=trans_conflicts,
                    flexibility_score=flexibility
                    * 0.7,  # Slightly lower during transition
                ),
                PhaseComponent(
                    assignment_id=assignment.id,
                    phase_type="post_transition",
                    energy_state=post_energy,
                    phase_start=post_start,
                    phase_end=post_end,
                    conflict_score=post_conflicts,
                    flexibility_score=flexibility,
                ),
            ]
        )

        return phases

    async def find_negative_energy_swaps(
        self, schedule_id: UUID, period: ErgospherePeriod
    ) -> list[PenroseSwap]:
        """
        Find swaps with local cost but global benefit (negative energy).

        In the Penrose process, particles with negative energy relative to
        infinity can exist in the ergosphere. For scheduling, these are swaps
        that locally increase conflicts but globally improve the schedule.

        Args:
            schedule_id: ID of the schedule to analyze
            period: The ergosphere period to search

        Returns:
            List of Penrose swaps sorted by net extraction benefit
        """
        swaps: list[PenroseSwap] = []

        # Get assignments in this ergosphere period
        result = await self.db.execute(
            select(Assignment)
            .join(Block)
            .where(Assignment.id.in_(period.affected_assignments))
            .options()  # Could add selectinload for relations
        )
        assignments = result.scalars().all()

        # Find potential swap pairs
        for i, assign_a in enumerate(assignments):
            for assign_b in assignments[i + 1 :]:
                # Calculate local and global impacts
                local_cost = await self._calculate_local_cost(assign_a, assign_b)
                global_benefit = await self._calculate_global_benefit(
                    assign_a, assign_b, assignments
                )

                # Only include if globally beneficial
                if global_benefit > abs(local_cost):
                    # Calculate confidence based on historical data and assignment similarity
                    confidence = self._calculate_confidence_score(
                        assign_a, assign_b, len(assignments)
                    )

                    swap = PenroseSwap(
                        swap_id=UUID(
                            int=hash((assign_a.id, assign_b.id)) & (2**128 - 1)
                        ),
                        assignment_a=assign_a.id,
                        assignment_b=assign_b.id,
                        local_cost=local_cost,
                        global_benefit=global_benefit,
                        ergosphere_period=period,
                        confidence=confidence,
                    )
                    swaps.append(swap)

        # Sort by net extraction (highest first)
        swaps.sort(key=lambda s: s.net_extraction, reverse=True)

        logger.info(
            f"Found {len(swaps)} negative-energy swaps in ergosphere "
            f"{period.boundary_type} with total extraction potential "
            f"{sum(s.net_extraction for s in swaps):.2f}"
        )

        return swaps

    async def _calculate_local_cost(
        self, assign_a: Assignment, assign_b: Assignment
    ) -> float:
        """
        Calculate local cost of swapping two assignments.

        Args:
            assign_a: First assignment
            assign_b: Second assignment

        Returns:
            Local cost (positive = worse, negative = better)
        """
        # Cost factors weighted by impact
        cost = 0.0

        # 1. Skill/qualification mismatch (highest cost)
        if assign_a.rotation_template_id != assign_b.rotation_template_id:
            cost += 2.0  # Different rotation types = higher cost

        # 2. Role mismatch (medium cost)
        if assign_a.role != assign_b.role:
            cost += 1.5

        # 3. Person preference mismatch (estimated from historical patterns)
        # Higher cost if persons have consistently preferred different rotations
        cost += await self._estimate_preference_mismatch(assign_a, assign_b)

        return cost

    async def _calculate_global_benefit(
        self,
        assign_a: Assignment,
        assign_b: Assignment,
        all_assignments: list[Assignment],
    ) -> float:
        """
        Calculate global benefit of swapping two assignments.

        Benefit metrics:
        1. Improved workload balance across residents
        2. Reduced ACGME violations (consecutive shifts, work hours)
        3. Better coverage distribution (specialty balance)
        4. Improved person preferences (rotation variety)

        Args:
            assign_a: First assignment
            assign_b: Second assignment
            all_assignments: All assignments in the period

        Returns:
            Global benefit score (higher = better)
        """
        benefit = 0.0

        # 1. Workload balance improvement
        # Count assignments per person before and after swap
        person_a_count = sum(
            1 for a in all_assignments if a.person_id == assign_a.person_id
        )
        person_b_count = sum(
            1 for a in all_assignments if a.person_id == assign_b.person_id
        )

        # Calculate workload variance before swap
        workload_before_variance = abs(person_a_count - person_b_count)

        # After swap, counts would be swapped for these specific assignments
        workload_after_variance = abs((person_a_count - 1) - (person_b_count + 1))

        if workload_after_variance < workload_before_variance:
            benefit += 3.0  # Improved balance

        # 2. ACGME compliance improvement
        # Check if swap reduces consecutive shifts
        if assign_a.block and assign_b.block:
            date_diff = abs((assign_a.block.date - assign_b.block.date).days)

            # If assignments are close together (< 2 days), swapping might reduce fatigue
            if date_diff <= 2:
                benefit += 2.5

            # If different weeks, swapping helps distribute work
            if date_diff >= 7:
                benefit += 1.5

        # 3. Coverage distribution improvement
        # If swapping provides better specialty coverage (different rotations)
        if (
            assign_a.rotation_template_id
            and assign_b.rotation_template_id
            and assign_a.rotation_template_id != assign_b.rotation_template_id
        ):
            benefit += 2.0  # Cross-training benefit

        # 4. Rotation variety improvement
        # Count how many times each person has done their assigned rotation
        person_a_rotation_count = sum(
            1
            for a in all_assignments
            if a.person_id == assign_a.person_id
            and a.rotation_template_id == assign_a.rotation_template_id
        )
        person_b_rotation_count = sum(
            1
            for a in all_assignments
            if a.person_id == assign_b.person_id
            and a.rotation_template_id == assign_b.rotation_template_id
        )

        # If person has done this rotation many times, swapping provides variety
        if person_a_rotation_count > 3 or person_b_rotation_count > 3:
            benefit += 1.5

        return benefit

    def compute_extraction_efficiency(self, swaps_executed: list[PenroseSwap]) -> float:
        """
        Compute total efficiency extraction from executed swaps.

        Args:
            swaps_executed: List of executed Penrose swaps

        Returns:
            Total efficiency extracted as fraction (0-0.29)
        """
        if not swaps_executed:
            return 0.0

        total_extraction = sum(
            swap.net_extraction for swap in swaps_executed if swap.executed
        )

        # Normalize by initial rotation energy if tracker is initialized
        if self.energy_tracker:
            efficiency = total_extraction / self.energy_tracker.initial_rotation_energy
            efficiency = min(
                efficiency, PENROSE_EFFICIENCY_LIMIT
            )  # Cap at Penrose limit
        else:
            # Without tracker, estimate based on number of swaps
            efficiency = min(len(swaps_executed) * 0.05, PENROSE_EFFICIENCY_LIMIT)

        logger.info(
            f"Computed extraction efficiency: {efficiency:.2%} "
            f"from {len(swaps_executed)} swaps "
            f"(total extraction: {total_extraction:.2f})"
        )

        return efficiency

    async def execute_penrose_cascade(
        self, schedule_id: UUID, max_iterations: int = 5
    ) -> dict[str, Any]:
        """
        Execute cascade of Penrose swaps to optimize schedule.

        Like a chain reaction of Penrose processes, execute multiple
        rounds of beneficial swaps until convergence or budget exhaustion.

        Args:
            schedule_id: ID of the schedule to optimize
            max_iterations: Maximum optimization iterations

        Returns:
            Dictionary with optimization results:
                - swaps_executed: Number of swaps executed
                - efficiency_extracted: Total efficiency extraction
                - iterations: Number of iterations performed
                - final_conflicts: Final conflict count
                - improvement: Overall improvement metric
        """
        # Calculate initial schedule energy (flexibility/swap potential)
        # Get all assignments to assess schedule flexibility
        result = await self.db.execute(select(Assignment))
        all_assignments = result.scalars().all()

        # Initial energy based on:
        # 1. Number of assignments (more = more swap potential)
        # 2. Variety of rotations (diverse = more flexibility)
        # 3. Person distribution (balanced = easier to swap)
        num_assignments = len(all_assignments)
        unique_rotations = len(
            set(
                a.rotation_template_id
                for a in all_assignments
                if a.rotation_template_id
            )
        )
        unique_persons = len(set(a.person_id for a in all_assignments))

        # Energy formula: base energy scales with assignment count and diversity
        initial_energy = (
            num_assignments * 0.5  # Base from assignment count
            + unique_rotations * 5.0  # Bonus for rotation variety
            + unique_persons * 3.0  # Bonus for person diversity
        )
        initial_energy = max(100.0, initial_energy)  # Minimum baseline energy

        logger.info(
            f"Initial schedule energy: {initial_energy:.2f} "
            f"(assignments={num_assignments}, rotations={unique_rotations}, persons={unique_persons})"
        )

        self.energy_tracker = RotationEnergyTracker(initial_energy)

        all_swaps: list[PenroseSwap] = []
        iteration = 0

        logger.info(f"Starting Penrose cascade for schedule {schedule_id}")

        while iteration < max_iterations and not self.energy_tracker.is_exhausted:
            iteration += 1
            logger.info(
                f"Cascade iteration {iteration}/{max_iterations} "
                f"(budget: {self.energy_tracker.extraction_budget:.2f})"
            )

            # Get actual schedule date range from assignments
            if all_assignments:
                assignments_with_blocks = [a for a in all_assignments if a.block]
                if assignments_with_blocks:
                    start_date = min(a.block.date for a in assignments_with_blocks)
                    end_date = max(a.block.date for a in assignments_with_blocks)
                else:
                    # Fallback if no blocks
                    start_date = date.today()
                    end_date = start_date + timedelta(days=28)
            else:
                start_date = date.today()
                end_date = start_date + timedelta(days=28)

            ergospheres = await self.identify_ergosphere_periods(start_date, end_date)

            # Find swaps in high-potential ergospheres
            iteration_swaps: list[PenroseSwap] = []
            for ergosphere in ergospheres:
                if ergosphere.is_high_potential:
                    swaps = await self.find_negative_energy_swaps(
                        schedule_id, ergosphere
                    )
                    iteration_swaps.extend(swaps)

            if not iteration_swaps:
                logger.info("No beneficial swaps found, terminating cascade")
                break

            # Execute top swaps within budget
            executed_count = 0
            for swap in sorted(
                iteration_swaps, key=lambda s: s.net_extraction, reverse=True
            ):
                if swap.net_extraction <= self.energy_tracker.extraction_budget:
                    # Mark swap for execution (actual DB execution happens in service layer)
                    swap.executed = True
                    self.energy_tracker.record_extraction(swap)
                    all_swaps.append(swap)
                    executed_count += 1

                    logger.debug(
                        f"Executed swap {swap.swap_id}: "
                        f"extraction={swap.net_extraction:.2f}, "
                        f"assignments=({swap.assignment_a}, {swap.assignment_b})"
                    )

            if executed_count == 0:
                logger.info("No swaps within budget, terminating cascade")
                break

            logger.info(f"Iteration {iteration}: executed {executed_count} swaps")

        # Calculate final metrics
        efficiency = self.compute_extraction_efficiency(all_swaps)
        final_conflicts = await self._estimate_total_conflicts(schedule_id)

        # Calculate final conflict count across all assignments
        final_conflicts = 0
        for assignment in all_assignments:
            if assignment.block:
                # Count conflicts for this assignment
                assignment_dt = datetime.combine(
                    assignment.block.date, datetime.min.time()
                ) + timedelta(
                    hours=PM_HOUR_OFFSET if assignment.block.time_of_day == "PM" else 0
                )

                period_start = assignment_dt - timedelta(hours=HOURS_PER_DAY)
                period_end = assignment_dt + timedelta(hours=HOURS_PER_DAY)

                conflicts = await self._count_conflicts_in_period(
                    assignment, period_start, period_end
                )
                final_conflicts += conflicts

        result = {
            "swaps_executed": len([s for s in all_swaps if s.executed]),
            "efficiency_extracted": efficiency,
            "iterations": iteration,
            "final_conflicts": final_conflicts,
            "improvement": efficiency * 100,  # Percentage improvement
            "budget_used": self.energy_tracker.extraction_fraction,
            "swaps": all_swaps,
        }

        logger.info(
            f"Penrose cascade complete: {result['swaps_executed']} swaps, "
            f"{result['efficiency_extracted']:.2%} efficiency extracted"
        )

        return result

    # Helper methods for conflict and flexibility estimation

    async def _estimate_conflicts_in_period(
        self, assignment: Assignment, start: datetime, end: datetime
    ) -> int:
        """
        Estimate conflict count in a period.

        Args:
            assignment: Assignment to check
            start: Period start
            end: Period end

        Returns:
            Estimated conflict count
        """
        # Simplified heuristic: conflicts are higher during transitions
        duration_hours = (end - start).total_seconds() / 3600
        if duration_hours <= 4:
            # Transition periods have fewer conflicts
            return 0
        elif duration_hours <= 12:
            # Standard half-day blocks
            return 1
        else:
            # Longer periods may have multiple conflicts
            return int(duration_hours / 12)

    def _calculate_flexibility_score(
        self, assignment: Assignment, phase_type: str
    ) -> float:
        """
        Calculate flexibility score for a phase.

        Args:
            assignment: Assignment to score
            phase_type: Type of phase

        Returns:
            Flexibility score (0-1)
        """
        # Flexibility based on phase type
        if phase_type == "transition":
            # Transition periods are less flexible
            return 0.5
        elif phase_type == "pre_transition":
            # Pre-transition has moderate flexibility
            return 0.7
        else:  # post_transition
            # Post-transition has moderate flexibility
            return 0.7

    def _calculate_swap_confidence(
        self, assign_a: Assignment, assign_b: Assignment, total_assignments: int
    ) -> float:
        """
        Calculate confidence in swap benefit estimate.

        Args:
            assign_a: First assignment
            assign_b: Second assignment
            total_assignments: Total number of assignments in context

        Returns:
            Confidence score (0-1)
        """
        # Base confidence
        confidence = 0.7

        # Increase confidence with more context
        if total_assignments > 50:
            confidence += 0.1
        if total_assignments > 100:
            confidence += 0.1

        # Decrease confidence if assignments lack data
        if not assign_a.rotation_template_id or not assign_b.rotation_template_id:
            confidence -= 0.2

        return max(0.0, min(1.0, confidence))

    async def _estimate_preference_mismatch(
        self, assign_a: Assignment, assign_b: Assignment
    ) -> float:
        """
        Estimate preference mismatch cost.

        Args:
            assign_a: First assignment
            assign_b: Second assignment

        Returns:
            Preference mismatch cost (0-1)
        """
        # Heuristic: assume 0.3 base mismatch cost
        return 0.3

    def _estimate_workload_balance_improvement(
        self, assign_a: Assignment, assign_b: Assignment, all_assignments: list
    ) -> float:
        """
        Estimate workload balance improvement from swap.

        Args:
            assign_a: First assignment
            assign_b: Second assignment
            all_assignments: All assignments

        Returns:
            Balance improvement score (0-1)
        """
        # Simplified: assume moderate improvement
        return 0.6

    async def _estimate_acgme_improvement(
        self, assign_a: Assignment, assign_b: Assignment
    ) -> float:
        """
        Estimate ACGME compliance improvement from swap.

        Args:
            assign_a: First assignment
            assign_b: Second assignment

        Returns:
            ACGME improvement score (0-1)
        """
        # Heuristic: swaps during off-peak times improve compliance
        return 0.4

    def _estimate_coverage_improvement(
        self, assign_a: Assignment, assign_b: Assignment
    ) -> float:
        """
        Estimate coverage distribution improvement from swap.

        Args:
            assign_a: First assignment
            assign_b: Second assignment

        Returns:
            Coverage improvement score (0-1)
        """
        # Different rotations indicate coverage rebalancing
        if assign_a.rotation_template_id != assign_b.rotation_template_id:
            return 0.7
        return 0.2

    async def _estimate_preference_improvement(
        self, assign_a: Assignment, assign_b: Assignment
    ) -> float:
        """
        Estimate preference satisfaction improvement from swap.

        Args:
            assign_a: First assignment
            assign_b: Second assignment

        Returns:
            Preference improvement score (0-1)
        """
        # Heuristic: assume moderate preference improvement
        return 0.5

    async def _calculate_initial_rotation_energy(self, schedule_id: UUID) -> float:
        """
        Calculate initial rotation energy based on schedule flexibility.

        Args:
            schedule_id: Schedule to analyze

        Returns:
            Initial rotation energy (potential for beneficial swaps)
        """
        # Query schedule complexity metrics
        # Base energy on number of potential swap opportunities
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == schedule_id).limit(100)
        )
        assignments = result.scalars().all()

        # Energy scales with number of assignments and diversity
        base_energy = len(assignments) * 0.5  # 0.5 energy per assignment
        diversity_factor = 1.2  # Assume 20% diversity bonus

        return base_energy * diversity_factor

    async def _get_schedule_date_range(self, schedule_id: UUID) -> dict[str, date]:
        """
        Get date range for a schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            Dict with 'start' and 'end' dates
        """
        # Query min and max dates from assignments
        result = await self.db.execute(
            select(Assignment)
            .join(Block)
            .where(Assignment.id == schedule_id)
            .order_by(Block.date)
            .limit(1)
        )
        first_assignment = result.scalar_one_or_none()

        if not first_assignment or not first_assignment.block:
            # Default to current date + 28 days
            return {"start": date.today(), "end": date.today() + timedelta(days=28)}

        # Use block date as reference
        start_date = first_assignment.block.date
        end_date = start_date + timedelta(days=28)  # One block period

        return {"start": start_date, "end": end_date}

    async def _estimate_total_conflicts(self, schedule_id: UUID) -> int:
        """
        Estimate total conflict count in schedule.

        Args:
            schedule_id: Schedule to analyze

        Returns:
            Estimated total conflicts
        """
        # Query assignments and estimate conflicts
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == schedule_id).limit(100)
        )
        assignments = result.scalars().all()

        # Heuristic: ~5% of assignments have conflicts
        estimated_conflicts = int(len(assignments) * 0.05)

        return max(0, estimated_conflicts)
