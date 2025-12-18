"""
Resilience-Aware Constraints.

This module contains constraints that improve schedule resilience and
robustness to disruptions.

Based on systems resilience theory, these constraints:
- Protect critical "hub" faculty from over-assignment
- Maintain capacity buffers for unexpected demand
- Isolate failures through zone boundaries
- Learn from historical preferences
- Identify and address N-1 vulnerabilities

Classes:
    - HubProtectionConstraint: Protect hub faculty from overload (soft, Tier 1)
    - UtilizationBufferConstraint: Maintain capacity buffer (soft, Tier 1)
    - ZoneBoundaryConstraint: Isolate blast radius (soft, Tier 2)
    - PreferenceTrailConstraint: Learn from history (soft, Tier 2)
    - N1VulnerabilityConstraint: Address single points of failure (soft, Tier 2)
"""
import logging
from collections import defaultdict
from uuid import UUID

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class HubProtectionConstraint(SoftConstraint):
    """
    Protects hub faculty from over-assignment.

    Network theory shows that scale-free networks (common in organizations)
    are robust to random failure but extremely vulnerable to hub removal.
    This constraint distributes load away from critical "hub" faculty.

    Rationale:
    - Hub faculty cover unique services or are hard to replace
    - Over-assigning hubs increases systemic risk
    - If a hub becomes unavailable, the system may fail N-1 analysis

    Implementation:
    - Penalizes assignments to faculty with high hub scores
    - Penalty scales with hub_score * assignment_count
    - Critical hubs (score > 0.6) get 2x penalty multiplier
    """

    # Hub score thresholds
    HIGH_HUB_THRESHOLD = 0.4      # Above this = significant hub
    CRITICAL_HUB_THRESHOLD = 0.6  # Above this = critical hub (2x penalty)

    def __init__(self, weight: float = 15.0):
        super().__init__(
            name="HubProtection",
            constraint_type=ConstraintType.HUB_PROTECTION,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add hub protection penalty to CP-SAT model objective function.

        For each faculty with hub_score > HIGH_HUB_THRESHOLD (0.4), adds a penalty
        to the objective function that scales with:
        - Hub score (0.4-1.0)
        - Assignment count
        - Criticality multiplier (2x for scores > 0.6)

        This creates economic pressure in the optimization to distribute work
        away from critical hub faculty, improving system resilience.

        Args:
            model: OR-Tools CP-SAT model
            variables: Dictionary with "assignments" decision variables
            context: SchedulingContext with hub_scores populated

        Implementation:
            - For each hub faculty (score > 0.4):
              - Sum their assignments across all blocks
              - Multiply by (hub_score × multiplier × 100) as integer factor
              - Add to penalty variable in objective function
            - Critical hubs (score > 0.6) get 2× multiplier

        Example:
            Faculty with hub_score=0.7 assigned to 10 blocks:
            penalty = 10 × (0.7 × 2.0 × 100) = 1400 penalty units

        Note:
            Only active when context.hub_scores is populated by ResilienceService
        """
        x = variables.get("assignments", {})

        if not x or not context.hub_scores:
            return  # No resilience data available

        total_hub_penalty = 0

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            hub_score = context.get_hub_score(faculty.id)
            if hub_score < self.HIGH_HUB_THRESHOLD:
                continue  # Not a hub, no penalty

            # Count assignments to this faculty
            faculty_vars = [
                x[f_i, context.block_idx[b.id]]
                for b in context.blocks
                if (f_i, context.block_idx[b.id]) in x
            ]

            if not faculty_vars:
                continue

            # Penalty multiplier based on hub criticality
            multiplier = 2.0 if hub_score >= self.CRITICAL_HUB_THRESHOLD else 1.0

            # Create penalty variable
            faculty_total = sum(faculty_vars)
            # Scale penalty by hub_score and multiplier
            penalty_factor = int(hub_score * multiplier * 100)
            total_hub_penalty += faculty_total * penalty_factor

        if total_hub_penalty:
            variables["hub_penalty"] = total_hub_penalty

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add hub protection penalty to PuLP model."""
        import pulp
        x = variables.get("assignments", {})

        if not x or not context.hub_scores:
            return

        penalty_terms = []

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            hub_score = context.get_hub_score(faculty.id)
            if hub_score < self.HIGH_HUB_THRESHOLD:
                continue

            faculty_vars = [
                x[f_i, context.block_idx[b.id]]
                for b in context.blocks
                if (f_i, context.block_idx[b.id]) in x
            ]

            if faculty_vars:
                multiplier = 2.0 if hub_score >= self.CRITICAL_HUB_THRESHOLD else 1.0
                penalty_factor = hub_score * multiplier
                penalty_terms.append(pulp.lpSum(faculty_vars) * penalty_factor)

        if penalty_terms:
            variables["hub_penalty"] = pulp.lpSum(penalty_terms)

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Validate hub protection and calculate penalty.

        Reports:
        - Which hubs are over-assigned
        - Total hub concentration risk
        """
        violations = []
        total_penalty = 0.0

        if not context.hub_scores:
            return ConstraintResult(satisfied=True, penalty=0.0)

        # Count assignments per faculty
        faculty_counts = defaultdict(int)
        for a in assignments:
            faculty_counts[a.person_id] += 1

        # Calculate average assignments
        if faculty_counts:
            avg_assignments = sum(faculty_counts.values()) / len(faculty_counts)
        else:
            avg_assignments = 0

        for faculty in context.faculty:
            hub_score = context.get_hub_score(faculty.id)
            if hub_score < self.HIGH_HUB_THRESHOLD:
                continue

            count = faculty_counts.get(faculty.id, 0)
            multiplier = 2.0 if hub_score >= self.CRITICAL_HUB_THRESHOLD else 1.0

            # Calculate penalty
            penalty = count * hub_score * multiplier * self.weight
            total_penalty += penalty

            # Report if hub is over-assigned (> average)
            if count > avg_assignments * 1.2:  # 20% above average
                severity = "HIGH" if hub_score >= self.CRITICAL_HUB_THRESHOLD else "MEDIUM"
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity=severity,
                    message=f"Hub faculty {faculty.name} (score={hub_score:.2f}) has {count} assignments (avg={avg_assignments:.1f})",
                    person_id=faculty.id,
                    details={
                        "hub_score": hub_score,
                        "assignment_count": count,
                        "average_assignments": avg_assignments,
                        "is_critical_hub": hub_score >= self.CRITICAL_HUB_THRESHOLD,
                    },
                ))

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )


class UtilizationBufferConstraint(SoftConstraint):
    """
    Maintains capacity buffer to absorb unexpected demand.

    Based on queuing theory (Erlang-C): wait times increase exponentially
    as utilization approaches 100%. The 80% threshold provides buffer for:
    - Unexpected absences
    - Emergency coverage needs
    - Surge demand

    Rationale:
    - At 80% utilization, wait times are manageable
    - At 90%+, small disturbances cause cascade failures
    - 20% buffer = "defense in depth" against surprises

    Implementation:
    - Calculates effective utilization from assignment count
    - Penalizes schedules that exceed target utilization
    - Penalty increases sharply above threshold (quadratic)
    """

    def __init__(self, weight: float = 20.0, target_utilization: float = 0.80):
        super().__init__(
            name="UtilizationBuffer",
            constraint_type=ConstraintType.UTILIZATION_BUFFER,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )
        self.target_utilization = target_utilization

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add utilization buffer constraint to CP-SAT model.

        Implements queuing theory-based capacity management: penalizes schedules
        that exceed the target utilization threshold (default 80%). Based on
        Erlang-C formula which shows that wait times increase exponentially
        as utilization approaches 100%.

        The 80% threshold provides a 20% buffer for:
        - Unexpected absences (illness, family emergencies)
        - Surge demand (patient volume spikes, special events)
        - Emergency coverage needs

        Args:
            model: OR-Tools CP-SAT model
            variables: Dictionary with "assignments" decision variables
            context: SchedulingContext with target_utilization setting

        Implementation:
            1. Calculate safe capacity: max_capacity × target_utilization
            2. Sum all assignments across faculty and blocks
            3. Create over_utilization variable: max(0, total - safe_capacity)
            4. Add to objective function as penalty

        Example:
            System with 10 faculty, 100 blocks, 80% target:
            - Max capacity: 10 × 100 = 1000 assignment-blocks
            - Safe capacity: 1000 × 0.80 = 800 assignment-blocks
            - If schedule has 850 assignments: penalty = 50 units
            - If schedule has 900 assignments: penalty = 100 units

        Queuing Theory Rationale:
            At 80% utilization: average wait times are acceptable
            At 90% utilization: wait times increase 3-5x
            At 95%+ utilization: system experiences cascade failures

        Note:
            Uses linear penalty in CP-SAT (quadratic is too complex).
            Validation step uses quadratic penalty for more accurate assessment.
        """
        x = variables.get("assignments", {})

        if not x:
            return

        # Calculate maximum safe assignments
        # Max capacity = faculty * blocks_per_faculty
        # Safe capacity = max_capacity * target_utilization
        max_blocks_per_faculty = len(context.blocks)
        max_capacity = len(context.faculty) * max_blocks_per_faculty
        safe_capacity = int(max_capacity * context.target_utilization)

        # Sum all assignments
        total_assignments = sum(x.values())

        # Create over-utilization variable
        over_util = model.NewIntVar(0, max_capacity, "over_utilization")
        model.Add(over_util >= total_assignments - safe_capacity)
        model.Add(over_util >= 0)

        # Quadratic-ish penalty: over_util * over_util is complex in CP-SAT
        # Use linear approximation with higher weight for large overages
        variables["utilization_penalty"] = over_util

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add utilization buffer constraint to PuLP model."""
        import pulp
        x = variables.get("assignments", {})

        if not x:
            return

        max_blocks_per_faculty = len(context.blocks)
        max_capacity = len(context.faculty) * max_blocks_per_faculty
        safe_capacity = int(max_capacity * context.target_utilization)

        total_assignments = pulp.lpSum(x.values())

        # Over-utilization slack variable
        over_util = pulp.LpVariable("over_utilization", lowBound=0, cat="Integer")
        model += over_util >= total_assignments - safe_capacity, "utilization_slack"

        variables["utilization_penalty"] = over_util

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Validate utilization buffer and calculate penalty.

        Reports:
        - Current utilization rate
        - Buffer remaining
        - Whether in danger zone
        """
        violations = []

        # Calculate utilization
        # This is a simplified calculation - actual would consider
        # faculty-specific availability
        total_assignments = len([a for a in assignments if a.role == "primary"])
        workday_blocks = len([b for b in context.blocks if not b.is_weekend])

        # Capacity = faculty who can work * average available blocks
        available_faculty = len([
            f for f in context.faculty
            if any(
                context.availability.get(f.id, {}).get(b.id, {}).get("available", True)
                for b in context.blocks
            )
        ])

        if available_faculty == 0 or workday_blocks == 0:
            return ConstraintResult(satisfied=True, penalty=0.0)

        # Simplified: each faculty can cover 1 block per day on average
        max_capacity = available_faculty * workday_blocks
        utilization = total_assignments / max_capacity if max_capacity > 0 else 0

        # Calculate penalty
        target = context.target_utilization if context.target_utilization else self.target_utilization

        if utilization <= target:
            penalty = 0.0
            buffer_remaining = target - utilization
        else:
            # Quadratic penalty above threshold
            over_threshold = utilization - target
            penalty = (over_threshold ** 2) * self.weight * 100
            buffer_remaining = 0.0

            # Determine severity based on how far over
            if utilization >= 0.95:
                severity = "CRITICAL"
            elif utilization >= 0.90:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            violations.append(ConstraintViolation(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                severity=severity,
                message=f"Utilization {utilization:.0%} exceeds target {target:.0%} (buffer exhausted)",
                details={
                    "utilization_rate": utilization,
                    "target_utilization": target,
                    "buffer_remaining": buffer_remaining,
                    "total_assignments": total_assignments,
                    "max_capacity": max_capacity,
                    "danger_zone": utilization >= 0.90,
                },
            ))

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=penalty,
        )


# =============================================================================
# TIER 2: STRATEGIC RESILIENCE CONSTRAINTS
# =============================================================================

class ZoneBoundaryConstraint(SoftConstraint):
    """
    Respects blast radius zone boundaries in scheduling.

    AWS Architecture Pattern: Failures should be contained within defined
    boundaries ("cells" or "availability zones"). A problem in one area
    cannot propagate to affect others.

    Rationale:
    - Each zone has dedicated faculty as primary coverage
    - Cross-zone assignments weaken isolation
    - When Zone A fails, Zones B and C should continue unaffected

    Implementation:
    - Penalizes assignments where faculty zone != block zone
    - Severity increases with containment level (soft → lockdown)
    - Critical zones (e.g., inpatient) have higher penalties
    """

    # Zone type priority multipliers
    ZONE_PRIORITY = {
        "inpatient": 2.0,      # Critical - highest isolation
        "outpatient": 1.5,     # Important
        "on_call": 1.5,        # Important
        "education": 1.0,      # Standard
        "research": 0.8,       # Flexible
        "admin": 0.5,          # Most flexible
    }

    def __init__(self, weight: float = 12.0):
        super().__init__(
            name="ZoneBoundary",
            constraint_type=ConstraintType.ZONE_BOUNDARY,
            weight=weight,
            priority=ConstraintPriority.MEDIUM,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add zone boundary penalty to CP-SAT model.

        For each assignment where faculty_zone != block_zone, add penalty.
        """
        x = variables.get("assignments", {})

        if not x or not context.zone_assignments or not context.block_zones:
            return  # No zone data available

        total_zone_penalty = 0

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_zone = context.zone_assignments.get(faculty.id)
            if not faculty_zone:
                continue  # Faculty not assigned to a zone

            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i) not in x:
                    continue

                block_zone = context.block_zones.get(block.id)
                if not block_zone:
                    continue  # Block not in a zone

                # Penalty if zones don't match
                if faculty_zone != block_zone:
                    penalty_factor = 10  # Base penalty for cross-zone
                    total_zone_penalty += x[f_i, b_i] * penalty_factor

        if total_zone_penalty:
            variables["zone_penalty"] = total_zone_penalty

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add zone boundary penalty to PuLP model."""
        import pulp
        x = variables.get("assignments", {})

        if not x or not context.zone_assignments or not context.block_zones:
            return

        penalty_terms = []

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_zone = context.zone_assignments.get(faculty.id)
            if not faculty_zone:
                continue

            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i) not in x:
                    continue

                block_zone = context.block_zones.get(block.id)
                if block_zone and faculty_zone != block_zone:
                    penalty_factor = 10
                    penalty_terms.append(x[f_i, b_i] * penalty_factor)

        if penalty_terms:
            variables["zone_penalty"] = pulp.lpSum(penalty_terms)

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Validate zone boundary compliance.

        Reports:
        - Cross-zone assignment count
        - Which zones are being violated
        - Total isolation breach penalty
        """
        violations = []
        total_penalty = 0.0

        if not context.zone_assignments or not context.block_zones:
            return ConstraintResult(satisfied=True, penalty=0.0)

        cross_zone_count = 0
        zone_violation_details = defaultdict(int)

        for assignment in assignments:
            faculty_zone = context.zone_assignments.get(assignment.person_id)
            block_zone = context.block_zones.get(assignment.block_id)

            if faculty_zone and block_zone and faculty_zone != block_zone:
                cross_zone_count += 1
                zone_violation_details[(str(faculty_zone), str(block_zone))] += 1
                total_penalty += self.weight

        if cross_zone_count > 0:
            # Determine severity based on percentage
            total_assignments = len(assignments)
            cross_zone_pct = cross_zone_count / total_assignments if total_assignments > 0 else 0

            if cross_zone_pct >= 0.20:
                severity = "HIGH"
            elif cross_zone_pct >= 0.10:
                severity = "MEDIUM"
            else:
                severity = "LOW"

            violations.append(ConstraintViolation(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                severity=severity,
                message=f"{cross_zone_count} cross-zone assignments ({cross_zone_pct:.0%} of total) - blast radius isolation weakened",
                details={
                    "cross_zone_count": cross_zone_count,
                    "total_assignments": total_assignments,
                    "cross_zone_percentage": cross_zone_pct,
                    "zone_violations": dict(zone_violation_details),
                },
            ))

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )


class PreferenceTrailConstraint(SoftConstraint):
    """
    Uses stigmergy preference trails for assignment optimization.

    Swarm Intelligence Pattern (Biology/AI): Individual agents following
    simple rules can collectively solve complex problems through indirect
    coordination. Ants find shortest paths without central planning by
    depositing and following pheromone trails.

    Rationale:
    - Preference trails encode learned faculty preferences
    - Strong trails indicate consistent preference/avoidance
    - Following trails improves satisfaction without explicit rules

    Implementation:
    - Rewards assignments matching strong preference trails
    - Penalizes assignments matching strong avoidance trails
    - Trail strength (0-1) modulates reward/penalty
    """

    # Trail strength thresholds
    STRONG_TRAIL_THRESHOLD = 0.6   # Above this = strong signal
    WEAK_TRAIL_THRESHOLD = 0.3     # Below this = ignore

    def __init__(self, weight: float = 8.0):
        super().__init__(
            name="PreferenceTrail",
            constraint_type=ConstraintType.PREFERENCE_TRAIL,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add preference trail bonus/penalty to CP-SAT model.

        For each (faculty, block), check if matching preference trail exists.
        """
        x = variables.get("assignments", {})

        if not x or not context.preference_trails:
            return  # No preference data available

        total_trail_score = 0

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_prefs = context.preference_trails.get(faculty.id, {})
            if not faculty_prefs:
                continue

            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i) not in x:
                    continue

                # Determine slot type from block
                slot_type = f"{block.date.strftime('%A').lower()}_{block.time_of_day.lower()}"

                # Check if we have a preference for this slot type
                trail_strength = faculty_prefs.get(slot_type, 0.5)

                if trail_strength >= self.STRONG_TRAIL_THRESHOLD:
                    # Bonus for matching strong preference
                    bonus = int((trail_strength - 0.5) * 20)
                    total_trail_score += x[f_i, b_i] * bonus
                elif trail_strength <= (1.0 - self.STRONG_TRAIL_THRESHOLD):
                    # Penalty for matching strong avoidance (low trail = avoidance)
                    penalty = int((0.5 - trail_strength) * 20)
                    total_trail_score -= x[f_i, b_i] * penalty

        if total_trail_score:
            variables["trail_bonus"] = total_trail_score

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add preference trail bonus/penalty to PuLP model."""
        import pulp
        x = variables.get("assignments", {})

        if not x or not context.preference_trails:
            return

        bonus_terms = []
        penalty_terms = []

        for faculty in context.faculty:
            f_i = context.resident_idx.get(faculty.id)
            if f_i is None:
                continue

            faculty_prefs = context.preference_trails.get(faculty.id, {})
            if not faculty_prefs:
                continue

            for block in context.blocks:
                b_i = context.block_idx[block.id]
                if (f_i, b_i) not in x:
                    continue

                slot_type = f"{block.date.strftime('%A').lower()}_{block.time_of_day.lower()}"
                trail_strength = faculty_prefs.get(slot_type, 0.5)

                if trail_strength >= self.STRONG_TRAIL_THRESHOLD:
                    bonus = (trail_strength - 0.5) * 2
                    bonus_terms.append(x[f_i, b_i] * bonus)
                elif trail_strength <= (1.0 - self.STRONG_TRAIL_THRESHOLD):
                    penalty = (0.5 - trail_strength) * 2
                    penalty_terms.append(x[f_i, b_i] * penalty)

        if bonus_terms:
            variables["trail_bonus"] = pulp.lpSum(bonus_terms)
        if penalty_terms:
            variables["trail_penalty"] = pulp.lpSum(penalty_terms)

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Validate preference trail alignment.

        Reports:
        - How well assignments align with preference trails
        - Assignments against strong avoidance trails
        """
        violations = []
        total_penalty = 0.0

        if not context.preference_trails:
            return ConstraintResult(satisfied=True, penalty=0.0)

        aligned_count = 0
        misaligned_count = 0
        total_checked = 0

        for assignment in assignments:
            faculty_prefs = context.preference_trails.get(assignment.person_id, {})
            if not faculty_prefs:
                continue

            # Get block for slot type
            block = None
            for b in context.blocks:
                if b.id == assignment.block_id:
                    block = b
                    break

            if not block:
                continue

            slot_type = f"{block.date.strftime('%A').lower()}_{block.time_of_day.lower()}"
            trail_strength = faculty_prefs.get(slot_type, 0.5)
            total_checked += 1

            if trail_strength >= self.STRONG_TRAIL_THRESHOLD:
                aligned_count += 1
            elif trail_strength <= (1.0 - self.STRONG_TRAIL_THRESHOLD):
                misaligned_count += 1
                total_penalty += (0.5 - trail_strength) * self.weight

        if total_checked > 0:
            alignment_rate = aligned_count / total_checked
            misalignment_rate = misaligned_count / total_checked

            # Report if significant misalignment
            if misaligned_count > 0 and misalignment_rate >= 0.10:
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="MEDIUM" if misalignment_rate >= 0.20 else "LOW",
                    message=f"{misaligned_count} assignments against preference trails ({misalignment_rate:.0%})",
                    details={
                        "aligned_count": aligned_count,
                        "misaligned_count": misaligned_count,
                        "total_checked": total_checked,
                        "alignment_rate": alignment_rate,
                        "misalignment_rate": misalignment_rate,
                    },
                ))

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )


class N1VulnerabilityConstraint(SoftConstraint):
    """
    Prevents schedules that create single points of failure.

    Power Grid N-1 Pattern: The system must survive the loss of any single
    component. Applied to scheduling: no service should depend on exactly
    one faculty member being available.

    Rationale:
    - N-1 compliance = schedule survives any single faculty absence
    - Single points of failure cause cascade risks
    - Cross-training and redundancy improve resilience

    Implementation:
    - Penalizes assignments that create N-1 vulnerabilities
    - Higher penalty for critical services/time slots
    - Identifies faculty who are sole coverage providers
    """

    def __init__(self, weight: float = 25.0):
        super().__init__(
            name="N1Vulnerability",
            constraint_type=ConstraintType.N1_VULNERABILITY,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(self, model, variables: dict, context: SchedulingContext):
        """
        Add N-1 vulnerability penalty to CP-SAT model.

        For blocks where only one faculty could be assigned, add penalty.
        This encourages solutions with redundancy.
        """
        x = variables.get("assignments", {})

        if not x:
            return

        # For each block, count how many faculty could cover it
        # If only 1 faculty assigned and no alternatives, that's N-1 vulnerable
        total_n1_penalty = 0

        for block in context.blocks:
            b_i = context.block_idx[block.id]

            # Count available faculty for this block
            available_for_block = []
            for faculty in context.faculty:
                f_i = context.resident_idx.get(faculty.id)
                if f_i is None:
                    continue

                # Check availability
                is_available = context.availability.get(
                    faculty.id, {}
                ).get(block.id, {}).get("available", True)

                if is_available and (f_i, b_i) in x:
                    available_for_block.append((f_i, faculty.id))

            # If only 1-2 faculty available, add penalty for assignments
            if len(available_for_block) <= 2:
                for f_i, _ in available_for_block:
                    # Penalty scaled by scarcity: 1 available = high, 2 = medium
                    scarcity_factor = 3 - len(available_for_block)  # 2 or 1
                    total_n1_penalty += x[f_i, b_i] * scarcity_factor * 10

        if total_n1_penalty:
            variables["n1_penalty"] = total_n1_penalty

    def add_to_pulp(self, model, variables: dict, context: SchedulingContext):
        """Add N-1 vulnerability penalty to PuLP model."""
        import pulp
        x = variables.get("assignments", {})

        if not x:
            return

        penalty_terms = []

        for block in context.blocks:
            b_i = context.block_idx[block.id]

            available_for_block = []
            for faculty in context.faculty:
                f_i = context.resident_idx.get(faculty.id)
                if f_i is None:
                    continue

                is_available = context.availability.get(
                    faculty.id, {}
                ).get(block.id, {}).get("available", True)

                if is_available and (f_i, b_i) in x:
                    available_for_block.append(f_i)

            if len(available_for_block) <= 2:
                scarcity_factor = 3 - len(available_for_block)
                for f_i in available_for_block:
                    penalty_terms.append(x[f_i, b_i] * scarcity_factor)

        if penalty_terms:
            variables["n1_penalty"] = pulp.lpSum(penalty_terms)

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Validate N-1 compliance of the schedule.

        Reports:
        - Blocks that are N-1 vulnerable (single coverage)
        - Faculty who are single points of failure
        - Overall N-1 compliance rate
        """
        violations = []
        total_penalty = 0.0

        # Analyze each block for redundancy
        block_coverage = defaultdict(list)
        for assignment in assignments:
            block_coverage[assignment.block_id].append(assignment.person_id)

        n1_vulnerable_blocks = []
        sole_providers = defaultdict(int)

        for block in context.blocks:
            providers = block_coverage.get(block.id, [])

            if len(providers) == 1:
                n1_vulnerable_blocks.append(block.id)
                sole_providers[providers[0]] += 1
                total_penalty += self.weight

        # Also check faculty in n1_vulnerable_faculty set
        for faculty_id in context.n1_vulnerable_faculty:
            if faculty_id in sole_providers:
                # Already counted in sole_providers
                continue
            # Check how many assignments this faculty has
            faculty_assignments = [a for a in assignments if a.person_id == faculty_id]
            if faculty_assignments:
                # Add extra penalty for known N-1 vulnerable faculty
                total_penalty += len(faculty_assignments) * self.weight * 0.5

        # Report violations
        if n1_vulnerable_blocks:
            vulnerability_rate = len(n1_vulnerable_blocks) / len(context.blocks) if context.blocks else 0

            if vulnerability_rate >= 0.20:
                severity = "CRITICAL"
            elif vulnerability_rate >= 0.10:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            violations.append(ConstraintViolation(
                constraint_name=self.name,
                constraint_type=self.constraint_type,
                severity=severity,
                message=f"{len(n1_vulnerable_blocks)} blocks have single-point-of-failure coverage ({vulnerability_rate:.0%})",
                details={
                    "n1_vulnerable_blocks": len(n1_vulnerable_blocks),
                    "total_blocks": len(context.blocks),
                    "vulnerability_rate": vulnerability_rate,
                    "sole_provider_counts": dict(sole_providers),
                    "n1_pass": len(n1_vulnerable_blocks) == 0,
                },
            ))

        # Report sole providers
        for faculty_id, sole_count in sole_providers.items():
            faculty_name = "Unknown"
            for f in context.faculty:
                if f.id == faculty_id:
                    faculty_name = f.name
                    break

            if sole_count >= 3:  # Report faculty who are sole provider for 3+ blocks
                violations.append(ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="HIGH" if sole_count >= 5 else "MEDIUM",
                    message=f"Faculty {faculty_name} is sole provider for {sole_count} blocks - single point of failure risk",
                    person_id=faculty_id,
                    details={
                        "sole_coverage_blocks": sole_count,
                        "recommendation": "Cross-train backup faculty",
                    },
                ))

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=total_penalty,
        )

