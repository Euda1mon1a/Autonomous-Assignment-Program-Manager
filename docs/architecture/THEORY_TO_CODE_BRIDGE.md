# Theory-to-Code Bridge
## Mapping 28,000+ Lines of Research to Production Implementation

**Purpose:** This document bridges extensive cross-disciplinary research to concrete implementation in the Residency Scheduler codebase.

**Last Updated:** 2025-12-26
**Status:** Implementation Roadmap
**Estimated Total Effort:** 640-840 hours (4-5 months, 1 developer)

---

## Table of Contents

1. [Game Theory → Code](#1-game-theory--code)
2. [Control Theory → Code](#2-control-theory--code)
3. [Complex Systems → Code](#3-complex-systems--code)
4. [Quantum Computing → Code](#4-quantum-computing--code)
5. [Integration Architecture](#5-integration-architecture)
6. [Implementation Priorities](#6-implementation-priorities)
7. [Testing & Validation Strategy](#7-testing--validation-strategy)

---

## 1. Game Theory → Code

### 1.1 VCG Mechanism → `FacultyPreferenceService`

**Research Source:**
- `/docs/research/GAME_THEORY_SCHEDULING_RESEARCH.md` (Lines 234-456)
- `/docs/research/GAME_THEORY_EXECUTIVE_SUMMARY.md` (Lines 47-59)
- `/docs/research/GAME_THEORY_QUICK_REFERENCE.md` (Section: "Strategyproof Mechanisms")

**Target Code File:**
- **Primary:** `/backend/app/services/faculty_preference_service.py`
- **New Module:** `/backend/app/services/game_theory/vcg_mechanism.py`

**Current State:**
The `FacultyPreferenceService` (886 lines) currently implements:
- ✅ Preference collection (`get_or_create_preferences()`)
- ✅ Compatibility scoring (`calculate_compatibility_score()`)
- ❌ **Missing:** Strategyproof mechanism (VCG payments)
- ❌ **Missing:** Truthfulness guarantees

**Proposed Implementation:**

```python
# backend/app/services/game_theory/vcg_mechanism.py

from typing import Dict, List, Tuple
from uuid import UUID
from datetime import date

class VCGMechanism:
    """
    Vickrey-Clarke-Groves mechanism for strategyproof shift allocation.

    Guarantees:
    - Truthfulness: Faculty gain nothing by misreporting preferences
    - Efficiency: Maximizes total value (social welfare)
    - Individual rationality: No one worse off than without participating

    Theory Source: docs/research/GAME_THEORY_SCHEDULING_RESEARCH.md (Lines 234-298)
    """

    def __init__(self, db: Session):
        self.db = db

    def allocate_shifts_vcg(
        self,
        faculty_preferences: Dict[UUID, List[Tuple[date, float]]],
        available_shifts: List[date],
        constraints: Dict[str, Any],
    ) -> Tuple[Dict[UUID, date], Dict[UUID, float]]:
        """
        Allocate shifts using VCG mechanism.

        Args:
            faculty_preferences: Mapping of faculty_id -> [(shift_date, value)]
                where value is declared preference strength (0-100)
            available_shifts: List of shifts to allocate
            constraints: ACGME and workload constraints

        Returns:
            Tuple of:
            - allocation: Mapping of faculty_id -> assigned_shift
            - payments: Mapping of faculty_id -> VCG payment (priority points)

        Algorithm:
            1. Find allocation maximizing sum of declared values
            2. For each faculty i, calculate VCG payment:
               payment_i = social_welfare_without_i - social_welfare_of_others_with_i
            3. Verify truthfulness: lying never reduces payment or improves allocation

        Time Complexity: O(n! * m) where n=faculty, m=shifts
        Optimization: Use Hungarian algorithm for O(n³)
        """
        # Step 1: Solve assignment problem (maximize total value)
        allocation = self._maximize_social_welfare(
            faculty_preferences, available_shifts, constraints
        )

        # Step 2: Calculate VCG payments
        payments = {}
        for faculty_id in faculty_preferences:
            # Calculate what total value would be WITHOUT this faculty
            other_allocation = self._maximize_social_welfare(
                {k: v for k, v in faculty_preferences.items() if k != faculty_id},
                available_shifts,
                constraints
            )

            # VCG payment = harm caused to others
            social_welfare_with = sum(
                faculty_preferences[fid][shift]
                for fid, shift in allocation.items()
                if fid != faculty_id
            )
            social_welfare_without = sum(
                faculty_preferences[fid][shift]
                for fid, shift in other_allocation.items()
            )

            payments[faculty_id] = social_welfare_without - social_welfare_with

        return allocation, payments

    def _maximize_social_welfare(
        self,
        preferences: Dict[UUID, List[Tuple[date, float]]],
        shifts: List[date],
        constraints: Dict[str, Any],
    ) -> Dict[UUID, date]:
        """
        Solve assignment problem using Hungarian algorithm.

        Integration Point: Use existing CP-SAT solver from scheduling engine
        with modified objective function.
        """
        from ortools.linear_solver import pywraplp

        # Create cost matrix from preferences
        cost_matrix = self._build_cost_matrix(preferences, shifts)

        # Solve using Hungarian algorithm
        solver = pywraplp.Solver.CreateSolver('SCIP')

        # ... constraint programming logic ...

        return allocation

    def verify_strategyproofness(
        self,
        faculty_id: UUID,
        true_preferences: List[Tuple[date, float]],
        declared_preferences: List[Tuple[date, float]],
    ) -> bool:
        """
        Verify that misreporting doesn't benefit the faculty member.

        Returns:
            True if mechanism is strategyproof for this case
        """
        # Run VCG with true preferences
        true_allocation, true_payment = self.allocate_shifts_vcg(
            {faculty_id: true_preferences, ...}, ...
        )

        # Run VCG with declared preferences
        declared_allocation, declared_payment = self.allocate_shifts_vcg(
            {faculty_id: declared_preferences, ...}, ...
        )

        # Calculate utility with lying
        utility_with_lying = (
            true_preferences[declared_allocation[faculty_id]] - declared_payment
        )

        # Calculate utility with truth
        utility_with_truth = (
            true_preferences[true_allocation[faculty_id]] - true_payment
        )

        # Verify lying doesn't help
        return utility_with_truth >= utility_with_lying
```

**Integration with Existing Code:**

```python
# backend/app/services/faculty_preference_service.py

from app.services.game_theory.vcg_mechanism import VCGMechanism

class FacultyPreferenceService:
    def __init__(self, db: Session):
        self.db = db
        self._cache = None
        self.vcg = VCGMechanism(db)  # NEW

    def collect_preferences_strategyproof(
        self,
        faculty_id: UUID,
        shift_dates: List[date],
        preference_values: List[float],
    ) -> FacultyPreference:
        """
        Collect preferences with VCG truthfulness guarantee.

        This method guarantees faculty cannot benefit by lying about
        preferences, making strategic misreporting pointless.
        """
        # Store preferences with VCG flag
        preferences = self.update_preferences(
            faculty_id=faculty_id,
            preferred_weeks=[str(d) for d, v in zip(shift_dates, preference_values) if v > 0.5],
            preference_mechanism="VCG",  # NEW FIELD
            preference_values=dict(zip(shift_dates, preference_values)),  # NEW FIELD
        )

        return preferences
```

**Data Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Faculty Submit Preferences                               │
│    POST /api/preferences/submit                             │
│    {faculty_id, shift_preferences: [(date, value)]}         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. VCGMechanism.allocate_shifts_vcg()                       │
│    • Build cost matrix from all preferences                 │
│    • Solve assignment problem (Hungarian/CP-SAT)            │
│    • Calculate VCG payments for each faculty                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Generate Schedule with Truthful Allocation              │
│    • assignments: {faculty_id -> shift_date}                │
│    • payments: {faculty_id -> priority_points}              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Store Results & Award Priority Points                   │
│    • Create Assignment records                              │
│    • Update FacultyPreference.priority_points (NEW)         │
│    • Log VCG payments for transparency                      │
└─────────────────────────────────────────────────────────────┘
```

**Database Schema Changes:**

```sql
-- Add VCG mechanism fields to faculty_preference table
ALTER TABLE faculty_preference
ADD COLUMN preference_mechanism VARCHAR(20) DEFAULT 'manual',
ADD COLUMN preference_values JSONB,  -- {date: value} mapping
ADD COLUMN priority_points INTEGER DEFAULT 0,
ADD COLUMN vcg_payment_history JSONB DEFAULT '[]';  -- Audit trail

-- Create index for priority point queries
CREATE INDEX idx_faculty_preference_priority_points
ON faculty_preference(priority_points DESC);
```

**Estimated Effort:**
- Core VCG implementation: **40 hours**
- Integration with existing services: **20 hours**
- Database migrations: **8 hours**
- Unit tests (90% coverage): **24 hours**
- Integration tests: **16 hours**
- **Total: 108 hours (~3 weeks)**

---

### 1.2 Shapley Values → `WorkloadService`

**Research Source:**
- `/docs/research/GAME_THEORY_SCHEDULING_RESEARCH.md` (Lines 567-723)
- `/docs/research/GAME_THEORY_EXECUTIVE_SUMMARY.md` (Lines 65-85)

**Target Code File:**
- **New Module:** `/backend/app/services/game_theory/shapley_fairness.py`
- **Integration:** `/backend/app/ml/models/workload_optimizer.py`

**Current State:**
- ❌ No existing Shapley value implementation
- ✅ Basic workload tracking exists in `workload_optimizer.py`
- ❌ No fair contribution measurement

**Proposed Implementation:**

```python
# backend/app/services/game_theory/shapley_fairness.py

from itertools import combinations
from typing import Dict, Set, List
from uuid import UUID

class ShapleyFairnessCalculator:
    """
    Calculate fair workload distribution using Shapley values.

    Shapley value = average marginal contribution across all possible coalitions

    Properties:
    - Efficiency: Total value distributed exactly equals total created
    - Symmetry: Identical contributors get identical shares
    - Dummy: Zero contributors get zero value
    - Additivity: Values combine linearly

    Theory Source: docs/research/GAME_THEORY_SCHEDULING_RESEARCH.md (Lines 567-723)
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_shapley_workload(
        self,
        faculty_pool: Set[UUID],
        coverage_requirements: Dict[str, int],  # {rotation_type: needed_faculty}
    ) -> Dict[UUID, float]:
        """
        Calculate fair workload targets using Shapley values.

        Args:
            faculty_pool: Set of available faculty IDs
            coverage_requirements: Minimum faculty needed per rotation type

        Returns:
            Mapping of faculty_id -> fair_workload_fraction (0-1)

        Example:
            Dr. Smith can cover {clinic, inpatient, procedures}
            Dr. Jones can cover {clinic, inpatient}
            Dr. Lee can cover {clinic}

            Shapley values:
            - Smith: 0.50 (high value, covers all types)
            - Jones: 0.33 (medium value, covers most)
            - Lee: 0.17 (low value, covers only clinic)

            Fair workload targets:
            - Smith: 0.50 * total_weeks = higher load BUT gets first choice
            - Jones: 0.33 * total_weeks
            - Lee: 0.17 * total_weeks = lighter load but less choice
        """
        shapley_values = {}
        n = len(faculty_pool)

        for faculty_id in faculty_pool:
            # Calculate marginal contribution across all coalitions
            value = 0.0

            # Iterate over all possible coalition sizes
            for k in range(n):
                # Number of coalitions of size k not containing faculty_id
                coalitions_without = list(combinations(
                    faculty_pool - {faculty_id}, k
                ))

                for coalition in coalitions_without:
                    # Coalition value without this faculty
                    v_without = self._coalition_coverage_value(
                        set(coalition), coverage_requirements
                    )

                    # Coalition value with this faculty
                    v_with = self._coalition_coverage_value(
                        set(coalition) | {faculty_id}, coverage_requirements
                    )

                    # Marginal contribution
                    marginal = v_with - v_without

                    # Weight by probability of this coalition forming
                    weight = 1.0 / (n * comb(n - 1, k))

                    value += weight * marginal

            shapley_values[faculty_id] = value

        # Normalize to sum to 1.0
        total = sum(shapley_values.values())
        if total > 0:
            shapley_values = {k: v / total for k, v in shapley_values.items()}

        return shapley_values

    def _coalition_coverage_value(
        self,
        coalition: Set[UUID],
        requirements: Dict[str, int],
    ) -> float:
        """
        Calculate how much coverage value a coalition provides.

        Value = sum over rotation types of min(available_faculty, required_faculty)

        This measures the coalition's ability to fulfill coverage needs.
        """
        value = 0.0

        for rotation_type, required_count in requirements.items():
            # Count faculty in coalition who can cover this rotation
            capable_faculty = self._get_capable_faculty(coalition, rotation_type)

            # Value is capped at requirement (extra faculty doesn't add value)
            value += min(len(capable_faculty), required_count)

        return value

    def _get_capable_faculty(
        self,
        faculty_ids: Set[UUID],
        rotation_type: str,
    ) -> Set[UUID]:
        """Get faculty from set who can cover a rotation type."""
        # Query faculty credentials/qualifications
        capable = set()
        for fid in faculty_ids:
            # Check if faculty has required credentials
            # Integration point: Use existing credential system
            if self._can_cover_rotation(fid, rotation_type):
                capable.add(fid)
        return capable

    def apply_shapley_workload_targets(
        self,
        shapley_values: Dict[UUID, float],
        total_weeks: int,
    ) -> Dict[UUID, int]:
        """
        Convert Shapley values to concrete workload targets.

        Args:
            shapley_values: Fair contribution fractions
            total_weeks: Total FMIT weeks to distribute

        Returns:
            Mapping of faculty_id -> target_weeks_per_year
        """
        targets = {}

        for faculty_id, fraction in shapley_values.items():
            target_weeks = round(fraction * total_weeks)
            targets[faculty_id] = target_weeks

        # Adjust for rounding errors to ensure sum equals total_weeks
        difference = total_weeks - sum(targets.values())
        if difference != 0:
            # Distribute difference to highest Shapley value faculty
            sorted_faculty = sorted(
                shapley_values.items(), key=lambda x: x[1], reverse=True
            )
            targets[sorted_faculty[0][0]] += difference

        return targets
```

**Integration with Scheduling Engine:**

```python
# backend/app/scheduling/constraints/workload.py

from app.services.game_theory.shapley_fairness import ShapleyFairnessCalculator

class ShapleyWorkloadConstraint:
    """
    Enforce fair workload distribution based on Shapley values.

    Integration: Add to SchedulingEngine as soft constraint
    """

    def __init__(self, weight: float = 10.0):
        self.weight = weight
        self.calculator = ShapleyFairnessCalculator(db)

    def add_constraints(
        self,
        model,
        faculty: List[Person],
        coverage_requirements: Dict[str, int],
    ):
        """Add Shapley fairness constraints to CP-SAT model."""

        # Calculate fair targets
        shapley_values = self.calculator.calculate_shapley_workload(
            faculty_pool={f.id for f in faculty},
            coverage_requirements=coverage_requirements,
        )

        targets = self.calculator.apply_shapley_workload_targets(
            shapley_values, total_weeks=52  # Annual target
        )

        # Add soft constraints to minimize deviation from Shapley targets
        for faculty_id, target in targets.items():
            actual = model.NewIntVar(0, 52, f"actual_weeks_{faculty_id}")

            # Penalty for deviation from Shapley target
            deviation = model.NewIntVar(-52, 52, f"deviation_{faculty_id}")
            model.Add(deviation == actual - target)

            abs_deviation = model.NewIntVar(0, 52, f"abs_dev_{faculty_id}")
            model.AddAbsEquality(abs_deviation, deviation)

            # Minimize weighted deviation
            model.Minimize(self.weight * abs_deviation)
```

**Data Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Annual Schedule Planning Triggered                      │
│    (e.g., July 1 for academic year)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. ShapleyFairnessCalculator.calculate_shapley_workload()  │
│    Inputs:                                                  │
│    • All faculty in program                                 │
│    • Coverage requirements per rotation type                │
│    • Faculty qualifications/credentials                     │
│    Output:                                                  │
│    • {faculty_id: fair_contribution_fraction}               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Convert to Workload Targets                             │
│    shapley_value * total_weeks = target_weeks_per_year      │
│    Example:                                                 │
│    • Dr. Smith (0.50) → 26 weeks/year                       │
│    • Dr. Jones (0.33) → 17 weeks/year                       │
│    • Dr. Lee (0.17) → 9 weeks/year                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Integrate into Scheduling Engine                        │
│    • Add ShapleyWorkloadConstraint to solver                │
│    • Soft constraint: minimize deviation from targets       │
│    • Generates schedule respecting fair contribution        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Dashboard Display                                        │
│    • Show Shapley values per faculty                        │
│    • Visualize contribution vs. workload                    │
│    • Justify workload targets objectively                   │
└─────────────────────────────────────────────────────────────┘
```

**Database Schema Changes:**

```sql
-- Add Shapley value tracking
CREATE TABLE shapley_workload_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    academic_year INTEGER NOT NULL,
    faculty_id UUID REFERENCES persons(id),

    -- Calculated values
    shapley_value FLOAT NOT NULL,  -- Fair contribution (0-1)
    target_weeks INTEGER NOT NULL,  -- Annual workload target
    actual_weeks INTEGER,           -- Actual assigned (updated quarterly)

    -- Justification data
    rotation_coverage JSONB,  -- {rotation_type: can_cover (bool)}
    marginal_contributions JSONB,  -- Detailed calculation audit trail

    -- Metadata
    calculated_at TIMESTAMP DEFAULT NOW(),
    calculation_version VARCHAR(20),

    UNIQUE(academic_year, faculty_id)
);

CREATE INDEX idx_shapley_academic_year ON shapley_workload_analysis(academic_year);
CREATE INDEX idx_shapley_faculty ON shapley_workload_analysis(faculty_id);
```

**Estimated Effort:**
- Core Shapley implementation: **32 hours**
- Integration with scheduling constraints: **24 hours**
- Database schema & migrations: **8 hours**
- Dashboard visualization: **16 hours**
- Unit tests: **20 hours**
- Integration tests: **12 hours**
- **Total: 112 hours (~3 weeks)**

---

### 1.3 Nash Equilibrium Check → `SwapAutoMatcher`

**Research Source:**
- `/docs/research/GAME_THEORY_SCHEDULING_RESEARCH.md` (Lines 789-921)
- `/docs/architecture/game-theory-framework.md` (Section: "Stability Analysis")

**Target Code File:**
- **Primary:** `/backend/app/services/swap_auto_matcher.py` (existing, 886 lines)
- **Enhancement:** Add Nash equilibrium detection

**Current State:**
The `SwapAutoMatcher` already has sophisticated matching logic:
- ✅ Compatibility scoring (lines 92-136)
- ✅ Preference alignment (lines 548-559)
- ✅ Historical analysis (lines 572-650)
- ❌ **Missing:** Nash equilibrium stability check
- ❌ **Missing:** Proactive instability detection

**Proposed Enhancement:**

```python
# backend/app/services/swap_auto_matcher.py

class SwapAutoMatcher:
    # ... existing code ...

    def check_nash_equilibrium(
        self,
        current_schedule: List[Assignment],
    ) -> NashEquilibriumReport:
        """
        Check if current schedule is a Nash equilibrium.

        Nash Equilibrium: No faculty can improve their situation by
        unilaterally requesting a swap.

        Theory Source: docs/research/GAME_THEORY_SCHEDULING_RESEARCH.md (Lines 789-921)

        Returns:
            Report containing:
            - is_equilibrium: bool (True if stable)
            - unstable_assignments: List of assignments where faculty would swap
            - swap_incentives: List of beneficial swaps for each faculty
            - stability_score: float (0-1, where 1 = perfectly stable)
        """
        unstable_assignments = []
        swap_incentives = []

        for assignment in current_schedule:
            faculty_id = assignment.person_id
            current_week = assignment.block.start_date

            # Find all other assignments this faculty could swap with
            potential_swaps = self._find_beneficial_swaps(
                faculty_id, current_week, current_schedule
            )

            if potential_swaps:
                # Faculty has incentive to deviate from current schedule
                unstable_assignments.append(assignment)
                swap_incentives.extend(potential_swaps)

        # Calculate stability score
        total_assignments = len(current_schedule)
        stable_assignments = total_assignments - len(unstable_assignments)
        stability_score = stable_assignments / total_assignments if total_assignments > 0 else 1.0

        is_equilibrium = len(unstable_assignments) == 0

        return NashEquilibriumReport(
            is_equilibrium=is_equilibrium,
            stability_score=stability_score,
            unstable_assignments=unstable_assignments,
            swap_incentives=swap_incentives,
            total_assignments=total_assignments,
            stable_assignments=stable_assignments,
        )

    def _find_beneficial_swaps(
        self,
        faculty_id: UUID,
        current_week: date,
        all_assignments: List[Assignment],
    ) -> List[Dict]:
        """
        Find swaps that would make this faculty better off.

        A swap is beneficial if:
        - Faculty prefers target week over current week
        - Swap partner is willing (or can be incentivized)
        - No ACGME violations result
        """
        beneficial_swaps = []

        # Get faculty preferences
        current_utility = self._calculate_utility(faculty_id, current_week)

        for other_assignment in all_assignments:
            if other_assignment.person_id == faculty_id:
                continue  # Skip own assignments

            other_week = other_assignment.block.start_date

            # Would this faculty prefer the other week?
            swap_utility = self._calculate_utility(faculty_id, other_week)

            if swap_utility > current_utility:
                # Faculty would benefit from this swap
                beneficial_swaps.append({
                    "target_faculty_id": other_assignment.person_id,
                    "target_week": other_week,
                    "utility_gain": swap_utility - current_utility,
                })

        return beneficial_swaps

    def _calculate_utility(
        self,
        faculty_id: UUID,
        week: date,
    ) -> float:
        """
        Calculate faculty's utility for a given week.

        Utility components:
        - Preference alignment: +1.0 if preferred, -1.0 if blocked, 0 otherwise
        - Workload proximity to target: penalize deviation from Shapley target
        - Personal constraints: penalize violations of personal rules
        """
        utility = 0.0

        # Preference component
        if self.preference_service.is_week_preferred(faculty_id, week):
            utility += 1.0
        elif self.preference_service.is_week_blocked(faculty_id, week):
            utility -= 1.0

        # Workload component
        preferences = self.preference_service.get_or_create_preferences(faculty_id)
        current_count = self.db.query(Assignment).filter(
            Assignment.person_id == faculty_id
        ).count()

        target = preferences.target_weeks_per_year or 6
        deviation = abs(current_count - target)
        utility -= 0.1 * deviation  # Penalty for being off target

        # Personal constraints
        # Check consecutive weeks, max per month, etc.
        # ... constraint checking logic ...

        return utility

    def predict_swap_requests_before_publish(
        self,
        draft_schedule: List[Assignment],
    ) -> SwapPredictionReport:
        """
        Predict which assignments will generate swap requests.

        Use BEFORE publishing schedule to identify problems early.

        Returns:
            Report with:
            - high_risk_assignments: Likely to generate swap requests
            - recommended_adjustments: Suggested changes to improve stability
            - predicted_swap_count: Estimated number of swap requests
        """
        nash_report = self.check_nash_equilibrium(draft_schedule)

        high_risk = []
        for assignment in nash_report.unstable_assignments:
            # Assignments where faculty has strong incentive to swap
            incentives = [
                inc for inc in nash_report.swap_incentives
                if inc["source_assignment_id"] == assignment.id
            ]

            if incentives:
                max_gain = max(inc["utility_gain"] for inc in incentives)
                if max_gain > 0.5:  # Strong incentive threshold
                    high_risk.append({
                        "assignment": assignment,
                        "utility_gain": max_gain,
                        "likely_swap_requests": incentives,
                    })

        # Generate recommendations
        recommendations = self._generate_stability_recommendations(
            high_risk, draft_schedule
        )

        return SwapPredictionReport(
            stability_score=nash_report.stability_score,
            high_risk_assignments=high_risk,
            recommended_adjustments=recommendations,
            predicted_swap_count=len(high_risk),
        )
```

**Integration with Schedule Generation:**

```python
# backend/app/scheduling/engine.py

class SchedulingEngine:
    def __init__(self, db: Session):
        self.db = db
        self.matcher = SwapAutoMatcher(db)  # Existing

    def generate_schedule_with_stability_check(
        self,
        ...
    ) -> Schedule:
        """Generate schedule with Nash equilibrium validation."""

        # Generate initial schedule
        draft_schedule = self._solve_constraints(...)

        # NEW: Check stability before publishing
        prediction = self.matcher.predict_swap_requests_before_publish(
            draft_schedule
        )

        if prediction.stability_score < 0.85:  # Threshold
            logger.warning(
                f"Schedule stability low ({prediction.stability_score:.1%}). "
                f"Predicted {prediction.predicted_swap_count} swap requests."
            )

            # Option 1: Auto-adjust based on recommendations
            if auto_adjust:
                draft_schedule = self._apply_stability_recommendations(
                    draft_schedule, prediction.recommended_adjustments
                )

            # Option 2: Alert coordinator for manual review
            else:
                await send_alert(
                    severity="WARNING",
                    title="Schedule Stability Warning",
                    message=f"Draft schedule has {len(prediction.high_risk_assignments)} "
                            f"high-risk assignments. Review recommended.",
                    data=prediction.dict(),
                )

        return draft_schedule
```

**Data Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Schedule Generation Completes                           │
│    • Draft schedule created by SchedulingEngine             │
│    • All hard constraints satisfied                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Nash Equilibrium Check (BEFORE publishing)              │
│    SwapAutoMatcher.check_nash_equilibrium()                 │
│    • For each faculty, find beneficial swaps                │
│    • Calculate utility gain from deviating                  │
│    • Identify unstable assignments                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Stability Score Calculation                             │
│    stability = 1 - (unstable_count / total_assignments)     │
│    Example: 47/50 stable → 94% stability score              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
                     [Decision]
                    /          \
                   /            \
              [< 85%]          [≥ 85%]
                 /                \
                ▼                  ▼
┌───────────────────────┐  ┌─────────────────┐
│ 4a. Low Stability     │  │ 4b. Good        │
│ • Alert coordinator   │  │     Stability   │
│ • Show high-risk      │  │ • Publish       │
│   assignments         │  │   schedule      │
│ • Suggest adjustments │  │                 │
└───────────────────────┘  └─────────────────┘
```

**API Endpoints:**

```python
# backend/app/api/routes/scheduling.py

@router.post("/schedules/{schedule_id}/stability-check")
async def check_schedule_stability(
    schedule_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Check Nash equilibrium stability of a schedule.

    Returns:
        - stability_score: float (0-1)
        - is_nash_equilibrium: bool
        - unstable_assignments: list
        - recommended_adjustments: list
    """
    schedule = get_schedule_or_404(db, schedule_id)
    matcher = SwapAutoMatcher(db)

    report = matcher.check_nash_equilibrium(schedule.assignments)

    return {
        "stability_score": report.stability_score,
        "is_nash_equilibrium": report.is_equilibrium,
        "unstable_assignments": [
            {
                "faculty_id": a.person_id,
                "week": a.block.start_date.isoformat(),
                "incentive": "strong" if ... else "moderate",
            }
            for a in report.unstable_assignments
        ],
        "summary": (
            f"{report.stable_assignments}/{report.total_assignments} "
            f"assignments are stable ({report.stability_score:.1%})"
        ),
    }
```

**Database Schema Changes:**

```sql
-- Track Nash equilibrium checks
CREATE TABLE nash_equilibrium_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID REFERENCES schedules(id),
    checked_at TIMESTAMP DEFAULT NOW(),

    -- Results
    is_equilibrium BOOLEAN NOT NULL,
    stability_score FLOAT NOT NULL,  -- 0-1
    unstable_count INTEGER NOT NULL,
    total_assignments INTEGER NOT NULL,

    -- Details
    unstable_assignments JSONB,  -- [{assignment_id, utility_gain, ...}]
    swap_incentives JSONB,       -- Detailed incentive analysis

    -- Actions
    recommendations JSONB,
    adjustments_applied BOOLEAN DEFAULT FALSE,
    coordinator_notified BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_nash_schedule ON nash_equilibrium_checks(schedule_id);
CREATE INDEX idx_nash_stability ON nash_equilibrium_checks(stability_score);
```

**Estimated Effort:**
- Nash equilibrium implementation: **24 hours**
- Utility calculation logic: **16 hours**
- Integration with scheduling engine: **12 hours**
- API endpoints: **8 hours**
- Database schema: **4 hours**
- Unit tests: **16 hours**
- Integration tests: **12 hours**
- **Total: 92 hours (~2.5 weeks)**

---

## 2. Control Theory → Code

### 2.1 PID Controller → `HomeostasisService`

**Research Source:**
- `/docs/research/control-theory-architecture.md` (Lines 123-345)
- `/docs/research/control-theory-quick-reference.md` (Lines 20-31)
- `/docs/research/exotic-control-theory-for-scheduling.md` (Section: "Classical Control")

**Target Code File:**
- **Primary:** `/backend/app/services/resilience/homeostasis.py` (existing, 100+ lines shown)
- **Enhancement:** Add PID feedback loops

**Current State:**
The `HomeostasisService` already has feedback loop monitoring:
- ✅ Volatility metrics tracking
- ✅ Allostatic load calculation
- ❌ **Missing:** Automatic correction via PID control
- ❌ **Missing:** Setpoint tracking

**Proposed Enhancement:**

```python
# backend/app/services/resilience/control/pid_controller.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

@dataclass
class PIDGains:
    """PID controller tuning parameters."""
    Kp: float  # Proportional gain
    Ki: float  # Integral gain
    Kd: float  # Derivative gain

    # Anti-windup
    max_integral: float = 100.0
    min_integral: float = -100.0

class PIDController:
    """
    PID controller for automatic setpoint tracking.

    Theory Source: docs/research/control-theory-quick-reference.md (Lines 20-31)

    Classic PID equation:
        u(t) = Kp·e(t) + Ki·∫e(τ)dτ + Kd·de(t)/dt

    Where:
        e(t) = setpoint - measurement  (error)
        u(t) = control output

    Applications in Scheduling:
    - Maintain utilization at 75% target
    - Keep coverage rate at 95%
    - Balance workload distribution
    """

    def __init__(
        self,
        gains: PIDGains,
        setpoint: float,
        output_limits: tuple[float, float] = (-100, 100),
    ):
        self.gains = gains
        self.setpoint = setpoint
        self.output_limits = output_limits

        # State variables
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time: Optional[datetime] = None

    def update(
        self,
        measurement: float,
        current_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate control output for current measurement.

        Args:
            measurement: Current process value
            current_time: Timestamp (defaults to now)

        Returns:
            Control output (within output_limits)
        """
        if current_time is None:
            current_time = datetime.utcnow()

        # Calculate error
        error = self.setpoint - measurement

        # Calculate time delta
        if self._last_time is not None:
            dt = (current_time - self._last_time).total_seconds() / 3600.0  # hours
        else:
            dt = 1.0  # Default 1 hour for first iteration

        # Proportional term
        P = self.gains.Kp * error

        # Integral term (with anti-windup)
        self._integral += error * dt
        self._integral = max(
            self.gains.min_integral,
            min(self._integral, self.gains.max_integral)
        )
        I = self.gains.Ki * self._integral

        # Derivative term
        if dt > 0:
            derivative = (error - self._last_error) / dt
        else:
            derivative = 0.0
        D = self.gains.Kd * derivative

        # Total control output
        output = P + I + D

        # Apply output limits
        output = max(self.output_limits[0], min(output, self.output_limits[1]))

        # Update state
        self._last_error = error
        self._last_time = current_time

        return output

    def reset(self):
        """Reset controller state (e.g., when setpoint changes)."""
        self._integral = 0.0
        self._last_error = 0.0
        self._last_time = None

# Integration with HomeostasisService
class HomeostasisService:
    def __init__(self, db: Session, config: ResilienceConfig | None = None):
        self.db = db
        self._config = config
        self._resilience_service: ResilienceService | None = None

        # NEW: PID controllers for key metrics
        self.utilization_pid = PIDController(
            gains=PIDGains(Kp=2.0, Ki=0.5, Kd=0.1),
            setpoint=0.75,  # Target 75% utilization
            output_limits=(-10, 10),  # ±10% adjustment
        )

        self.coverage_pid = PIDController(
            gains=PIDGains(Kp=3.0, Ki=0.8, Kd=0.2),
            setpoint=0.95,  # Target 95% coverage
            output_limits=(-5, 5),  # ±5% adjustment
        )

    def auto_correct_utilization(
        self,
        current_utilization: float,
    ) -> Dict[str, Any]:
        """
        Automatically correct utilization drift using PID control.

        Returns:
            Correction actions:
            - adjustment_needed: float (e.g., +2.5% more assignments)
            - recommended_actions: list of concrete steps
            - control_breakdown: {P, I, D components}
        """
        # Calculate control output
        correction = self.utilization_pid.update(current_utilization)

        # Interpret control output as % adjustment needed
        adjustment_pct = correction / 100.0

        # Generate recommended actions
        if abs(correction) < 1.0:
            actions = ["No adjustment needed - within tolerance"]
        elif correction > 0:
            # Need to increase utilization
            actions = [
                f"Add {abs(correction):.1f}% more assignments",
                "Consider assigning additional faculty to coverage",
                "Review blocked weeks and encourage flexibility",
            ]
        else:
            # Need to decrease utilization
            actions = [
                f"Reduce utilization by {abs(correction):.1f}%",
                "Redistribute assignments more evenly",
                "Consider hiring additional faculty",
            ]

        return {
            "current_utilization": current_utilization,
            "target": self.utilization_pid.setpoint,
            "error": self.utilization_pid.setpoint - current_utilization,
            "adjustment_needed_pct": adjustment_pct,
            "correction_signal": correction,
            "recommended_actions": actions,
            "control_breakdown": {
                "proportional": self.utilization_pid.gains.Kp * (self.utilization_pid.setpoint - current_utilization),
                "integral": self.utilization_pid.gains.Ki * self.utilization_pid._integral,
                "derivative": self.utilization_pid.gains.Kd * (
                    (self.utilization_pid.setpoint - current_utilization) - self.utilization_pid._last_error
                ),
            },
        }
```

**Integration with Celery Tasks:**

```python
# backend/app/resilience/tasks.py

@celery_app.task
def pid_utilization_control():
    """
    Background task: PID control for utilization.
    Runs every 6 hours.
    """
    db = get_db()
    homeostasis = HomeostasisService(db)

    # Get current utilization
    current_util = calculate_current_utilization(db)

    # Apply PID control
    correction = homeostasis.auto_correct_utilization(current_util)

    # Store in metrics
    await store_control_action(db, "utilization_pid", correction)

    # Alert if significant adjustment needed
    if abs(correction["adjustment_needed_pct"]) > 0.05:  # >5% adjustment
        await send_alert(
            severity="MEDIUM",
            title="Utilization Drift Detected",
            message=f"Current utilization {current_util:.1%} deviating from "
                    f"target {homeostasis.utilization_pid.setpoint:.1%}. "
                    f"Recommended actions: {', '.join(correction['recommended_actions'])}",
            data=correction,
        )

    db.close()

# Schedule PID tasks
celery_app.conf.beat_schedule.update({
    'pid-utilization-control': {
        'task': 'app.resilience.tasks.pid_utilization_control',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
})
```

**Data Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Metrics Collection (Every 6 hours via Celery)           │
│    • Query current utilization from assignments             │
│    • Query coverage rate from schedules                     │
│    • Calculate workload balance metrics                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PIDController.update()                                   │
│    Input: current_utilization = 0.82 (82%)                  │
│    Setpoint: 0.75 (75%)                                     │
│    Error: -0.07 (7% too high)                               │
│                                                             │
│    Control Calculation:                                     │
│    P = 2.0 × (-0.07) = -0.14                                │
│    I = 0.5 × (∫error) = -0.03                               │
│    D = 0.1 × (de/dt) = -0.01                                │
│    Output = -0.18 → -18% adjustment needed                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Generate Correction Actions                             │
│    Interpretation: Utilization 7% too high                  │
│    Recommended actions:                                     │
│    • Reduce utilization by 18%                              │
│    • Redistribute 9-10 assignments                          │
│    • Consider hiring 0.2 FTE additional faculty             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Alert & Dashboard                                        │
│    • Send alert to coordinator (if >5% adjustment)          │
│    • Display PID trend chart on dashboard                   │
│    • Show P/I/D component breakdown                         │
└─────────────────────────────────────────────────────────────┘
```

**Tuning Parameters:**

```python
# Configuration for different scenarios
PID_TUNING_PROFILES = {
    "aggressive": PIDGains(Kp=3.0, Ki=1.0, Kd=0.3),  # Fast response, risk of overshoot
    "conservative": PIDGains(Kp=1.0, Ki=0.3, Kd=0.05),  # Slow, stable
    "default": PIDGains(Kp=2.0, Ki=0.5, Kd=0.1),  # Balanced
}

# Ziegler-Nichols tuning method (empirical)
def tune_pid_ziegler_nichols(
    ultimate_gain: float,  # Gain at which system oscillates
    ultimate_period: float,  # Oscillation period
) -> PIDGains:
    """
    Auto-tune PID gains using Ziegler-Nichols method.

    Theory Source: docs/research/control-theory-architecture.md (Lines 234-267)
    """
    Kp = 0.6 * ultimate_gain
    Ki = 2.0 * Kp / ultimate_period
    Kd = Kp * ultimate_period / 8.0

    return PIDGains(Kp=Kp, Ki=Ki, Kd=Kd)
```

**Estimated Effort:**
- Core PID implementation: **16 hours**
- Integration with homeostasis service: **12 hours**
- Celery task setup: **8 hours**
- Tuning & calibration: **16 hours**
- Dashboard visualization: **12 hours**
- Unit tests: **12 hours**
- **Total: 76 hours (~2 weeks)**

---

### 2.2 Kalman Filter → `ResilienceService` (Workload Estimation)

**Research Source:**
- `/docs/research/control-theory-architecture.md` (Lines 456-621)
- `/docs/research/control-theory-quick-reference.md` (Lines 33-45)

**Target Code File:**
- **New Module:** `/backend/app/services/resilience/control/kalman_filter.py`
- **Integration:** `/backend/app/resilience/service.py`

**Use Case:**
Faculty self-report work hours, but data is noisy and incomplete. Kalman filter optimally combines:
- Noisy measurements (self-reported hours)
- Process model (expected hours based on assignments)
- Historical trends

**Proposed Implementation:**

```python
# backend/app/services/resilience/control/kalman_filter.py

import numpy as np
from typing import Tuple

class KalmanFilter:
    """
    Kalman filter for optimal state estimation under uncertainty.

    Theory Source: docs/research/control-theory-quick-reference.md (Lines 33-45)

    State Equations:
        x[k+1] = A·x[k] + B·u[k] + w[k]  (process model)
        z[k] = H·x[k] + v[k]             (measurement model)

    Where:
        x = state vector (e.g., [true_hours, hours_trend])
        z = measurement (e.g., self-reported hours)
        w ~ N(0, Q)  (process noise)
        v ~ N(0, R)  (measurement noise)

    Application: Estimate true work hours from noisy self-reports
    """

    def __init__(
        self,
        state_dim: int = 2,  # [hours, trend]
        measurement_dim: int = 1,  # reported hours
        process_noise: float = 1.0,
        measurement_noise: float = 5.0,
    ):
        # State transition matrix
        self.A = np.array([
            [1.0, 1.0],  # hours[k+1] = hours[k] + trend[k]
            [0.0, 0.98],  # trend[k+1] = 0.98·trend[k] (decay)
        ])

        # Control input matrix
        self.B = np.array([[1.0], [0.0]])  # Expected hours from schedule

        # Measurement matrix
        self.H = np.array([[1.0, 0.0]])  # Observe hours only

        # Process noise covariance
        self.Q = np.eye(state_dim) * process_noise

        # Measurement noise covariance
        self.R = np.array([[measurement_noise ** 2]])

        # State estimate and covariance
        self.x = np.zeros((state_dim, 1))  # [hours, trend]
        self.P = np.eye(state_dim) * 100.0  # High initial uncertainty

    def predict(
        self,
        control_input: float,  # Expected hours from schedule
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prediction step: estimate next state based on process model.

        Args:
            control_input: Expected hours from scheduled assignments

        Returns:
            (predicted_state, predicted_covariance)
        """
        u = np.array([[control_input]])

        # Predict state
        self.x = self.A @ self.x + self.B @ u

        # Predict covariance
        self.P = self.A @ self.P @ self.A.T + self.Q

        return self.x, self.P

    def update(
        self,
        measurement: float,  # Reported hours
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Update step: correct prediction with measurement.

        Args:
            measurement: Self-reported work hours

        Returns:
            (corrected_state, corrected_covariance)
        """
        z = np.array([[measurement]])

        # Innovation (measurement residual)
        y = z - self.H @ self.x

        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R

        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Update state
        self.x = self.x + K @ y

        # Update covariance
        I = np.eye(self.x.shape[0])
        self.P = (I - K @ self.H) @ self.P

        return self.x, self.P

    def get_estimate(self) -> Dict[str, float]:
        """Get current best estimate."""
        return {
            "estimated_hours": float(self.x[0, 0]),
            "trend": float(self.x[1, 0]),
            "uncertainty": float(np.sqrt(self.P[0, 0])),
        }

# Integration with workload tracking
class WorkloadEstimator:
    """
    Estimate true faculty workload using Kalman filtering.

    Combines:
    - Scheduled hours (from assignments)
    - Self-reported hours (noisy measurements)
    - Historical trends
    """

    def __init__(self, db: Session):
        self.db = db
        self.filters: Dict[UUID, KalmanFilter] = {}

    def get_or_create_filter(self, faculty_id: UUID) -> KalmanFilter:
        """Get Kalman filter for a faculty member."""
        if faculty_id not in self.filters:
            self.filters[faculty_id] = KalmanFilter(
                process_noise=1.0,  # ±1 hour process uncertainty
                measurement_noise=5.0,  # ±5 hour measurement uncertainty
            )
        return self.filters[faculty_id]

    def update_workload_estimate(
        self,
        faculty_id: UUID,
        reported_hours: float,
        scheduled_hours: float,
        week: date,
    ) -> Dict[str, float]:
        """
        Update workload estimate with new measurement.

        Args:
            faculty_id: Faculty member
            reported_hours: Self-reported hours (noisy)
            scheduled_hours: Expected hours from schedule
            week: Week of measurement

        Returns:
            {
                estimated_hours: float,  # Best estimate
                uncertainty: float,      # ±uncertainty
                trend: float,            # Hours/week trend
            }
        """
        kf = self.get_or_create_filter(faculty_id)

        # Prediction step (using scheduled hours as expected)
        kf.predict(scheduled_hours)

        # Update step (correct with reported hours)
        kf.update(reported_hours)

        # Get estimate
        estimate = kf.get_estimate()

        # Store in database
        self._store_estimate(faculty_id, week, estimate)

        return estimate

    def _store_estimate(
        self,
        faculty_id: UUID,
        week: date,
        estimate: Dict[str, float],
    ):
        """Store Kalman-filtered estimate in database."""
        # Integration point: Store in workload_metrics table
        pass
```

**Integration Example:**

```python
# Usage in hour reporting
from app.services.resilience.control.kalman_filter import WorkloadEstimator

estimator = WorkloadEstimator(db)

# Faculty reports hours
reported_hours = 65.0  # Noisy self-report
scheduled_hours = 60.0  # From assignments

estimate = estimator.update_workload_estimate(
    faculty_id=faculty.id,
    reported_hours=reported_hours,
    scheduled_hours=scheduled_hours,
    week=current_week,
)

print(f"Estimated true hours: {estimate['estimated_hours']:.1f} "
      f"±{estimate['uncertainty']:.1f}")
# Output: "Estimated true hours: 62.3 ±2.1"
```

**Data Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Weekly Hour Reporting                                    │
│    • Faculty submits self-report: 65 hours                  │
│    • System knows scheduled hours: 60 hours                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Kalman Filter Prediction                                │
│    Prior estimate: 58 hours ±3                              │
│    Expected (from schedule): 60 hours                       │
│    Predicted: 59 hours ±3.5                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Kalman Filter Update                                     │
│    Measurement: 65 hours (noisy)                            │
│    Predicted: 59 hours                                      │
│    Innovation: +6 hours                                     │
│    Kalman Gain: 0.35 (trust 35% measurement, 65% model)     │
│    Corrected estimate: 59 + 0.35×6 = 61.1 hours ±2.1        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ACGME Compliance Check                                  │
│    Use filtered estimate (61.1 hours) instead of            │
│    noisy report (65 hours) for violation checks             │
│    Result: More accurate compliance monitoring              │
└─────────────────────────────────────────────────────────────┘
```

**Estimated Effort:**
- Core Kalman filter: **20 hours**
- Integration with workload tracking: **16 hours**
- Database schema: **4 hours**
- Unit tests: **12 hours**
- **Total: 52 hours (~1.5 weeks)**

---

### 2.3 Model Predictive Control (MPC) → `SchedulingEngine`

**Research Source:**
- `/docs/research/control-theory-architecture.md` (Lines 722-945)
- `/docs/research/exotic-control-theory-for-scheduling.md` (Section: "MPC for Scheduling")

**Target Code File:**
- **New Module:** `/backend/app/scheduling/control/mpc_scheduler.py`
- **Integration:** `/backend/app/scheduling/engine.py`

**Current State:**
- ✅ Existing CP-SAT solver for constraint satisfaction
- ❌ **Missing:** Multi-week horizon optimization
- ❌ **Missing:** Receding horizon strategy

**Proposed Implementation:**

```python
# backend/app/scheduling/control/mpc_scheduler.py

from typing import List, Dict
from datetime import date, timedelta
from ortools.sat.python import cp_model

class MPCScheduler:
    """
    Model Predictive Control for multi-week scheduling.

    Theory Source: docs/research/control-theory-architecture.md (Lines 722-945)

    MPC Strategy:
    1. Optimize schedule for next N weeks (prediction horizon)
    2. Execute only first M weeks (control horizon)
    3. Re-optimize with updated information

    Benefits:
    - Looks ahead to avoid future problems
    - Handles constraints naturally (via CP-SAT)
    - Adapts to changing conditions
    """

    def __init__(
        self,
        db: Session,
        prediction_horizon: int = 4,  # weeks
        control_horizon: int = 2,  # weeks
    ):
        self.db = db
        self.prediction_horizon = prediction_horizon
        self.control_horizon = control_horizon

    def generate_schedule_mpc(
        self,
        start_week: date,
        faculty: List[Person],
        constraints: Dict[str, Any],
        weights: Dict[str, float],
    ) -> Schedule:
        """
        Generate schedule using MPC strategy.

        Args:
            start_week: First week to schedule
            faculty: Available faculty
            constraints: ACGME + personal constraints
            weights: Objective function weights

        Returns:
            Schedule for control_horizon weeks (only execute these)
        """
        # Step 1: Plan for full prediction horizon
        horizon_end = start_week + timedelta(weeks=self.prediction_horizon)

        full_plan = self._optimize_horizon(
            start_week,
            horizon_end,
            faculty,
            constraints,
            weights,
        )

        # Step 2: Extract only control horizon (first M weeks)
        execute_end = start_week + timedelta(weeks=self.control_horizon)
        executed_plan = [
            a for a in full_plan
            if a.block.start_date < execute_end
        ]

        # Step 3: Store plan and prepare for next iteration
        self._store_mpc_plan(
            executed=executed_plan,
            planned_ahead=full_plan,
            iteration_time=datetime.utcnow(),
        )

        return Schedule(assignments=executed_plan)

    def _optimize_horizon(
        self,
        start: date,
        end: date,
        faculty: List[Person],
        constraints: Dict[str, Any],
        weights: Dict[str, float],
    ) -> List[Assignment]:
        """
        Optimize schedule over prediction horizon.

        Integration: Use existing CP-SAT solver with extended horizon
        """
        model = cp_model.CpModel()

        # Decision variables: x[faculty_id, week, rotation]
        weeks = self._get_weeks_in_range(start, end)
        assignments = {}

        for faculty_member in faculty:
            for week in weeks:
                for rotation in self._get_available_rotations(week):
                    var = model.NewBoolVar(
                        f"assign_{faculty_member.id}_{week}_{rotation.id}"
                    )
                    assignments[(faculty_member.id, week, rotation.id)] = var

        # Add constraints (existing logic from scheduling engine)
        self._add_acgme_constraints(model, assignments, weeks, faculty)
        self._add_coverage_constraints(model, assignments, weeks)
        self._add_preference_constraints(model, assignments, faculty, weights)

        # NEW: Add look-ahead constraints
        # E.g., ensure Week 3-4 don't create problems for Week 5-6
        self._add_lookahead_constraints(model, assignments, weeks)

        # Objective: Maximize satisfaction over full horizon
        objective = self._build_mpc_objective(
            model, assignments, weeks, faculty, weights
        )
        model.Maximize(objective)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            return self._extract_assignments(solver, assignments, faculty)
        else:
            raise ValueError("MPC optimization failed to find feasible solution")

    def _add_lookahead_constraints(
        self,
        model,
        assignments: Dict,
        weeks: List[date],
    ):
        """
        Add constraints that prevent future problems.

        Examples:
        - Don't schedule consecutive weeks if it would violate gap constraint
        - Don't over-utilize faculty early if it causes coverage gaps later
        - Balance workload across horizon
        """
        # Constraint: Avoid consecutive week violations across horizon
        for faculty_id in self._get_faculty_ids():
            preferences = self._get_preferences(faculty_id)
            min_gap = preferences.min_gap_between_weeks or 2

            for i, week1 in enumerate(weeks[:-min_gap]):
                for j in range(i + 1, min(i + min_gap + 1, len(weeks))):
                    week2 = weeks[j]

                    # If assigned in week1, can't be assigned in week2
                    # (if within min_gap)
                    for rotation1 in self._get_available_rotations(week1):
                        for rotation2 in self._get_available_rotations(week2):
                            model.Add(
                                assignments.get((faculty_id, week1, rotation1.id), 0)
                                + assignments.get((faculty_id, week2, rotation2.id), 0)
                                <= 1
                            )

    def _build_mpc_objective(
        self,
        model,
        assignments: Dict,
        weeks: List[date],
        faculty: List[Person],
        weights: Dict[str, float],
    ):
        """
        Build objective function with time-discounting.

        Objective = ∑[t=0 to N] γ^t · cost(t)

        Where γ < 1 discounts future costs (near-term more important)
        """
        gamma = 0.95  # Discount factor

        total_cost = 0

        for t, week in enumerate(weeks):
            week_cost = 0

            # Preference satisfaction
            for faculty_member in faculty:
                for rotation in self._get_available_rotations(week):
                    var = assignments.get(
                        (faculty_member.id, week, rotation.id)
                    )
                    if var:
                        pref_score = self._get_preference_score(
                            faculty_member.id, week
                        )
                        week_cost += pref_score * var

            # Apply time discount
            total_cost += (gamma ** t) * week_cost

        return total_cost
```

**Integration with Existing Engine:**

```python
# backend/app/scheduling/engine.py

from app.scheduling.control.mpc_scheduler import MPCScheduler

class SchedulingEngine:
    def __init__(self, db: Session):
        self.db = db
        self.mpc = MPCScheduler(
            db,
            prediction_horizon=4,  # Plan 4 weeks ahead
            control_horizon=2,     # Execute 2 weeks
        )

    def generate_schedule_iterative(
        self,
        start_date: date,
        total_weeks: int,
        faculty: List[Person],
    ) -> Schedule:
        """
        Generate schedule using MPC receding horizon strategy.

        Instead of scheduling all 52 weeks at once:
        1. Schedule weeks 1-4, execute weeks 1-2
        2. Schedule weeks 3-6, execute weeks 3-4
        3. Repeat...

        Benefits:
        - Adapts to new information (leave requests, emergencies)
        - Avoids early decisions that cause later problems
        - Maintains computational feasibility
        """
        full_schedule = []
        current_week = start_date

        while len(full_schedule) < total_weeks:
            # Run MPC iteration
            iteration_schedule = self.mpc.generate_schedule_mpc(
                start_week=current_week,
                faculty=faculty,
                constraints=self._get_constraints(),
                weights=self._get_objective_weights(),
            )

            # Append executed portion
            full_schedule.extend(iteration_schedule.assignments)

            # Advance to next iteration
            current_week += timedelta(weeks=self.mpc.control_horizon)

        return Schedule(assignments=full_schedule[:total_weeks])
```

**Estimated Effort:**
- Core MPC implementation: **40 hours**
- Integration with CP-SAT: **24 hours**
- Horizon constraint logic: **20 hours**
- Testing & validation: **24 hours**
- **Total: 108 hours (~3 weeks)**

---

## 3. Complex Systems → Code

### 3.1 Phase Transition Detection → `HealthMonitor`

**Research Source:**
- `/docs/research/complex-systems-scheduling-research.md` (Lines 234-567)
- `/docs/research/thermodynamic_resilience_foundations.md` (Section: "Phase Transitions")
- `/docs/research/INTEGRATION_GUIDE.md` (Lines 51-114)

**Target Code File:**
- **Primary:** `/backend/app/resilience/thermodynamics/phase_transitions.py` (already exists!)
- **Integration:** `/backend/app/resilience/service.py`

**Current State:**
- ✅ Phase transition detection module already implemented!
- ✅ Critical slowing down detection
- ❌ **Missing:** Integration with health monitoring
- ❌ **Missing:** Alert triggering

**Integration Enhancement:**

```python
# backend/app/resilience/service.py

from app.resilience.thermodynamics import (
    PhaseTransitionDetector,
    CriticalPhenomenaMonitor,
    TransitionSeverity,
)

class ResilienceService:
    def __init__(self, db: Session, config: ResilienceConfig):
        self.db = db
        self.config = config

        # Existing components
        self.utilization = UtilizationMonitor()
        self.defense = DefenseInDepth()

        # NEW: Thermodynamic monitoring
        self.phase_detector = PhaseTransitionDetector(
            window_size=50,  # Track last 50 measurements
            variance_threshold=2.0,
            autocorr_threshold=0.7,
        )
        self.critical_monitor = CriticalPhenomenaMonitor()

    async def health_check(self) -> ResilienceHealth:
        """Enhanced health check with phase transition detection."""

        # Standard metrics
        util = await self.utilization.get_current()
        coverage = await self._get_coverage_rate()

        # NEW: Check for phase transitions
        phase_risk = await self._detect_phase_transitions({
            "utilization": util,
            "coverage": coverage,
            "violations": await self._count_violations(),
            "workload_variance": await self._calculate_workload_variance(),
        })

        # Escalate defense level if phase transition imminent
        if phase_risk.overall_severity == TransitionSeverity.IMMINENT:
            logger.critical("Phase transition imminent - escalating defense")
            self.defense.escalate_to_emergency()

        return ResilienceHealth(
            utilization=util,
            coverage=coverage,
            phase_transition_risk=phase_risk,  # NEW
            defense_level=self.defense.current_level,
        )

    async def _detect_phase_transitions(
        self,
        metrics: Dict[str, float],
    ) -> PhaseTransitionRisk:
        """
        Detect early warning signals of phase transitions.

        Theory: docs/research/complex-systems-scheduling-research.md (Lines 234-567)

        Early Warning Signals:
        1. Increased variance (system becoming unstable)
        2. Increased autocorrelation (critical slowing down)
        3. Flickering (rapid state changes)
        4. Skewness (asymmetric distribution)
        """
        # Update detector with new metrics
        await self.phase_detector.update(metrics)

        # Check for early warning signals
        risk = await self.critical_monitor.assess_risk(
            self.phase_detector.get_history()
        )

        # Store in database
        await self._store_phase_transition_risk(risk)

        return risk
```

**Alert Thresholds:**

```python
# backend/app/resilience/alerts.py

PHASE_TRANSITION_ALERT_RULES = {
    TransitionSeverity.NORMAL: {
        "alert": False,
    },
    TransitionSeverity.ELEVATED: {
        "alert": True,
        "severity": "LOW",
        "message": "Early warning signals detected - monitor closely",
    },
    TransitionSeverity.HIGH: {
        "alert": True,
        "severity": "MEDIUM",
        "message": "Multiple early warning signals - phase transition possible",
    },
    TransitionSeverity.CRITICAL: {
        "alert": True,
        "severity": "HIGH",
        "message": "Phase transition likely - prepare contingency plans",
    },
    TransitionSeverity.IMMINENT: {
        "alert": True,
        "severity": "CRITICAL",
        "message": "Phase transition imminent - activate emergency protocols",
    },
}
```

**Estimated Effort:**
- Integration with existing module: **12 hours**
- Alert rule configuration: **8 hours**
- Dashboard visualization: **16 hours**
- Testing: **12 hours**
- **Total: 48 hours (~1.5 weeks)**

---

### 3.2 Power Law Analysis → `HubAnalysisService`

**Research Source:**
- `/docs/research/complex-systems-scheduling-research.md` (Lines 678-892)

**Target Code File:**
- **Primary:** `/backend/app/resilience/hub_analysis.py` (already exists!)
- **Enhancement:** Add power law fitting

**Current State:**
- ✅ Hub analysis module exists
- ❌ **Missing:** Power law distribution fitting
- ❌ **Missing:** Heavy-tail detection

**Proposed Enhancement:**

```python
# backend/app/resilience/hub_analysis.py

import numpy as np
from scipy import stats
import powerlaw  # pip install powerlaw

class HubAnalysisService:
    # ... existing code ...

    def analyze_degree_distribution(
        self,
        schedule: Schedule,
    ) -> PowerLawAnalysis:
        """
        Analyze if workload distribution follows a power law.

        Theory: docs/research/complex-systems-scheduling-research.md (Lines 678-892)

        Power law: P(k) ~ k^(-α)

        Where k = workload (assignments), α = power law exponent

        Implications:
        - α ≈ 2-3: Scale-free network, few "superhubs"
        - α > 3: More even distribution
        - α < 2: Extreme inequality (unsustainable)
        """
        # Get workload distribution
        workloads = [
            len(self._get_assignments(faculty_id, schedule))
            for faculty_id in self._get_all_faculty()
        ]

        # Fit power law
        fit = powerlaw.Fit(workloads, discrete=True)

        # Compare to alternative distributions
        R_pl_exp = fit.distribution_compare('power_law', 'exponential')
        R_pl_lognormal = fit.distribution_compare('power_law', 'lognormal')

        # Determine if power law is good fit
        is_power_law = (
            fit.alpha > 1.5 and
            R_pl_exp[0] > 0 and  # Power law better than exponential
            R_pl_lognormal[1] > 0.1  # Not significantly worse than lognormal
        )

        return PowerLawAnalysis(
            alpha=fit.alpha,
            xmin=fit.xmin,
            is_power_law=is_power_law,
            comparison_to_exponential=R_pl_exp,
            comparison_to_lognormal=R_pl_lognormal,
            interpretation=self._interpret_power_law(fit.alpha, is_power_law),
        )

    def _interpret_power_law(
        self,
        alpha: float,
        is_power_law: bool,
    ) -> str:
        """Generate human-readable interpretation."""
        if not is_power_law:
            return "Workload distribution is NOT scale-free (good - more balanced)"

        if alpha < 2.0:
            return (
                f"Extreme inequality detected (α={alpha:.2f} < 2). "
                "Few faculty carry disproportionate load - UNSUSTAINABLE."
            )
        elif alpha < 3.0:
            return (
                f"Scale-free distribution (α={alpha:.2f}). "
                "Some 'hub' faculty carry heavier load - MONITOR for burnout."
            )
        else:
            return (
                f"Near-even distribution (α={alpha:.2f} > 3). "
                "Workload well-balanced across faculty."
            )
```

**Estimated Effort:**
- Power law implementation: **16 hours**
- Integration with hub analysis: **8 hours**
- Visualization: **12 hours**
- Testing: **8 hours**
- **Total: 44 hours (~1 week)**

---

### 3.3 Edge-of-Chaos Metrics → Constraint Weight Tuning

**Research Source:**
- `/docs/research/complex-systems-scheduling-research.md` (Lines 1123-1345)

**Target Code File:**
- **New Module:** `/backend/app/scheduling/adaptation/edge_of_chaos.py`

**Proposed Implementation:**

```python
# backend/app/scheduling/adaptation/edge_of_chaos.py

class EdgeOfChaosOptimizer:
    """
    Tune constraint weights to operate at "edge of chaos".

    Theory Source: docs/research/complex-systems-scheduling-research.md (Lines 1123-1345)

    Edge of chaos = sweet spot between:
    - Too rigid (frozen, inflexible)
    - Too chaotic (unstable, unpredictable)

    Measured by:
    - Lyapunov exponent (λ)
    - Entropy production rate
    - Correlation length

    Target: λ ≈ 0 (edge of chaos)
    """

    def calculate_lyapunov_exponent(
        self,
        schedules: List[Schedule],
    ) -> float:
        """
        Calculate Lyapunov exponent for schedule stability.

        λ > 0: Chaotic (small changes amplify)
        λ = 0: Edge of chaos (optimal)
        λ < 0: Frozen (stable but inflexible)
        """
        # Compare similar initial conditions
        divergences = []

        for i in range(len(schedules) - 1):
            initial_diff = self._schedule_distance(
                schedules[i], schedules[i+1]
            )

            # Evolve both schedules (e.g., add new constraints)
            evolved1 = self._perturb_schedule(schedules[i])
            evolved2 = self._perturb_schedule(schedules[i+1])

            final_diff = self._schedule_distance(evolved1, evolved2)

            if initial_diff > 0:
                divergence = np.log(final_diff / initial_diff)
                divergences.append(divergence)

        # Average divergence rate
        lyapunov = np.mean(divergences) if divergences else 0.0

        return lyapunov

    def tune_weights_to_edge_of_chaos(
        self,
        initial_weights: Dict[str, float],
        test_scenarios: List[Dict],
    ) -> Dict[str, float]:
        """
        Adaptively tune constraint weights to achieve λ ≈ 0.

        Args:
            initial_weights: Starting constraint weights
            test_scenarios: Different constraint scenarios to test

        Returns:
            Optimized weights that operate at edge of chaos
        """
        current_weights = initial_weights.copy()

        for iteration in range(20):  # Max 20 iterations
            # Generate schedules with current weights
            schedules = [
                self._generate_with_weights(scenario, current_weights)
                for scenario in test_scenarios
            ]

            # Calculate Lyapunov exponent
            lyapunov = self.calculate_lyapunov_exponent(schedules)

            # Check if at edge of chaos
            if abs(lyapunov) < 0.05:  # Close enough to 0
                logger.info(f"Found edge of chaos at iteration {iteration}")
                break

            # Adjust weights
            if lyapunov > 0:
                # Too chaotic - increase constraint weights (more rigid)
                current_weights = {
                    k: v * 1.1 for k, v in current_weights.items()
                }
            else:
                # Too frozen - decrease constraint weights (more flexible)
                current_weights = {
                    k: v * 0.9 for k, v in current_weights.items()
                }

        return current_weights
```

**Estimated Effort:**
- Core implementation: **32 hours**
- Integration with scheduling: **16 hours**
- Testing & calibration: **20 hours**
- **Total: 68 hours (~2 weeks)**

---

## 4. Quantum Computing → Code

### 4.1 QUBO Solver Integration

**Research Source:**
- `/docs/research/quantum-physics-scheduler-exploration.md`

**Target Code File:**
- **Primary:** `/backend/app/scheduling/quantum/qubo_solver.py` (already exists!)
- **Enhancement:** Add shadow mode validation vs CP-SAT

**Current State:**
- ✅ QUBO solver module already exists
- ❌ **Missing:** Production integration
- ❌ **Missing:** Benchmark framework

**Proposed Enhancement:**

```python
# backend/app/scheduling/quantum/qubo_solver.py

class QUBOScheduler:
    # ... existing code ...

    def shadow_mode_comparison(
        self,
        constraints: Dict,
        use_quantum: bool = False,
    ) -> BenchmarkResult:
        """
        Run both CP-SAT and QUBO solver in parallel, compare results.

        Shadow Mode: QUBO runs alongside CP-SAT but doesn't affect production.
        Collects data for validation.

        Args:
            constraints: Scheduling constraints
            use_quantum: If True, use actual quantum hardware (D-Wave)

        Returns:
            Comparison metrics:
            - solve_time_cpsat: float
            - solve_time_qubo: float
            - objective_value_cpsat: float
            - objective_value_qubo: float
            - solution_quality_ratio: float
        """
        import time

        # Run CP-SAT (production method)
        start_cpsat = time.time()
        solution_cpsat = self._solve_with_cpsat(constraints)
        time_cpsat = time.time() - start_cpsat

        # Run QUBO (experimental)
        start_qubo = time.time()
        solution_qubo = self._solve_with_qubo(constraints, use_quantum=use_quantum)
        time_qubo = time.time() - start_qubo

        # Compare solutions
        obj_cpsat = self._evaluate_objective(solution_cpsat)
        obj_qubo = self._evaluate_objective(solution_qubo)

        quality_ratio = obj_qubo / obj_cpsat if obj_cpsat > 0 else 0.0

        # Store benchmark results
        result = BenchmarkResult(
            timestamp=datetime.utcnow(),
            solve_time_cpsat=time_cpsat,
            solve_time_qubo=time_qubo,
            objective_cpsat=obj_cpsat,
            objective_qubo=obj_qubo,
            quality_ratio=quality_ratio,
            speedup=time_cpsat / time_qubo if time_qubo > 0 else 0.0,
            constraints_count=len(constraints),
            variables_count=self._count_variables(constraints),
        )

        await self._store_benchmark(result)

        return result
```

**Integration Point:**

```python
# backend/app/scheduling/engine.py

class SchedulingEngine:
    def __init__(self, db: Session, enable_qubo_shadow: bool = False):
        self.db = db
        self.enable_qubo_shadow = enable_qubo_shadow

        if enable_qubo_shadow:
            self.qubo = QUBOScheduler(db)

    def generate_schedule(self, ...):
        # Generate with CP-SAT (production)
        schedule = self._solve_with_cpsat(...)

        # Shadow mode: Also run QUBO for comparison
        if self.enable_qubo_shadow:
            asyncio.create_task(
                self.qubo.shadow_mode_comparison(constraints)
            )  # Run in background, don't block

        return schedule
```

**Estimated Effort:**
- Shadow mode framework: **20 hours**
- Benchmark collection: **12 hours**
- Analysis dashboard: **16 hours**
- Testing: **8 hours**
- **Total: 56 hours (~1.5 weeks)**

---

## 5. Integration Architecture

### 5.1 Service Layer Integration

```
┌─────────────────────────────────────────────────────────────┐
│ API Layer (FastAPI Routes)                                 │
│ /api/scheduling, /api/resilience, /api/swaps               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Service Layer                                               │
│ ┌─────────────────┐  ┌──────────────────┐                  │
│ │SchedulingEngine │  │ ResilienceService│                  │
│ │  + MPC          │  │  + PID           │                  │
│ │  + QUBO shadow  │  │  + Phase detect  │                  │
│ └─────────────────┘  └──────────────────┘                  │
│                                                             │
│ ┌──────────────────────┐  ┌────────────────────┐           │
│ │ SwapAutoMatcher      │  │ FacultyPrefService │           │
│ │  + Nash equilibrium  │  │  + VCG mechanism   │           │
│ │  + Game theory       │  │  + Shapley values  │           │
│ └──────────────────────┘  └────────────────────┘           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Theory Modules (New)                                        │
│ ┌───────────────────┐  ┌────────────────────┐              │
│ │ game_theory/      │  │ resilience/control/│              │
│ │  - vcg_mechanism  │  │  - pid_controller  │              │
│ │  - shapley        │  │  - kalman_filter   │              │
│ │  - nash_check     │  │  - mpc_scheduler   │              │
│ └───────────────────┘  └────────────────────┘              │
│                                                             │
│ ┌──────────────────────┐  ┌───────────────────┐            │
│ │ thermodynamics/      │  │ quantum/          │            │
│ │  - phase_transitions │  │  - qubo_solver    │            │
│ │  - entropy           │  │  - benchmark      │            │
│ └──────────────────────┘  └───────────────────┘            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ Database Layer (PostgreSQL)                                │
│ - Assignments, Preferences, Swaps                          │
│ - NEW: shapley_workload_analysis                           │
│ - NEW: nash_equilibrium_checks                             │
│ - NEW: qubo_benchmarks                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Implementation Priorities

### Phase 1: High-Priority Foundations (Weeks 1-6)
**Estimated: 280 hours**

1. **VCG Mechanism** (108 hours)
   - Immediate impact on preference honesty
   - Builds foundation for game theory

2. **Nash Equilibrium Check** (92 hours)
   - Prevents swap request flood
   - Low complexity, high value

3. **PID Controller** (76 hours)
   - Auto-corrects utilization drift
   - Quick wins in stability

### Phase 2: Fairness & Optimization (Weeks 7-12)
**Estimated: 288 hours**

4. **Shapley Values** (112 hours)
   - Objective workload targets
   - Reduces fairness complaints

5. **MPC Scheduler** (108 hours)
   - Better long-term planning
   - Handles constraints naturally

6. **Edge-of-Chaos Tuning** (68 hours)
   - Optimizes flexibility vs stability

### Phase 3: Advanced Monitoring (Weeks 13-16)
**Estimated: 200 hours**

7. **Kalman Filter** (52 hours)
   - Better workload estimates
   - Improves compliance accuracy

8. **Phase Transition Integration** (48 hours)
   - Early warning system
   - Leverages existing module

9. **Power Law Analysis** (44 hours)
   - Detects unsustainable inequality
   - Dashboard enhancement

10. **QUBO Shadow Mode** (56 hours)
    - Future-proofs for quantum
    - No production risk

**Total Estimated Effort: 768 hours (~5 months, 1 developer)**

---

## 7. Testing & Validation Strategy

### 7.1 Unit Testing

Each module requires ≥90% code coverage:

```python
# Example: test_vcg_mechanism.py

class TestVCGMechanism:
    def test_strategyproofness(self):
        """Verify lying never helps."""
        vcg = VCGMechanism(db)

        # True preferences
        true_prefs = {faculty.id: [(date1, 100), (date2, 50)]}

        # Lying preferences
        lie_prefs = {faculty.id: [(date1, 50), (date2, 100)]}

        # Run VCG with both
        true_alloc, true_payment = vcg.allocate_shifts_vcg(true_prefs, ...)
        lie_alloc, lie_payment = vcg.allocate_shifts_vcg(lie_prefs, ...)

        # Calculate utilities
        true_utility = true_prefs[faculty.id][true_alloc[faculty.id]] - true_payment
        lie_utility = true_prefs[faculty.id][lie_alloc[faculty.id]] - lie_payment

        # Lying should not help
        assert true_utility >= lie_utility
```

### 7.2 Integration Testing

Test interactions between modules:

```python
# test_game_theory_integration.py

async def test_vcg_shapley_nash_pipeline():
    """Test full game theory pipeline."""

    # 1. Collect preferences with VCG
    vcg = VCGMechanism(db)
    allocation, payments = vcg.allocate_shifts_vcg(preferences, ...)

    # 2. Calculate Shapley-fair workload
    shapley = ShapleyFairnessCalculator(db)
    targets = shapley.calculate_shapley_workload(faculty, ...)

    # 3. Check Nash equilibrium
    matcher = SwapAutoMatcher(db)
    nash_report = matcher.check_nash_equilibrium(allocation)

    # Verify no incentive to swap with Shapley-fair allocation
    assert nash_report.stability_score > 0.9
```

### 7.3 Validation Against Theory

```python
# test_theoretical_guarantees.py

def test_shapley_axioms():
    """Verify Shapley value satisfies theoretical axioms."""
    calc = ShapleyFairnessCalculator(db)

    faculty = create_test_faculty()
    values = calc.calculate_shapley_workload(faculty, requirements)

    # Axiom 1: Efficiency (sum equals total value)
    assert abs(sum(values.values()) - 1.0) < 0.001

    # Axiom 2: Symmetry (identical faculty get identical values)
    identical_faculty = [f for f in faculty if f.qualifications == QUAL_A]
    identical_values = [values[f.id] for f in identical_faculty]
    assert len(set(identical_values)) == 1  # All same

    # Axiom 3: Dummy (zero contributor gets zero value)
    dummy = next(f for f in faculty if len(f.qualifications) == 0)
    assert values[dummy.id] == 0.0
```

---

## Conclusion

This Theory-to-Code Bridge provides concrete implementation paths for:

1. **Game Theory** → Strategyproof preferences, fair workload, stable swaps
2. **Control Theory** → Auto-correct utilization, filter noise, plan ahead
3. **Complex Systems** → Detect instabilities, tune to edge-of-chaos
4. **Quantum Computing** → Shadow mode validation for future hardware

**Total Effort:** 768 hours (~5 months, 1 developer)

**Next Steps:**
1. Review priorities with stakeholders
2. Begin Phase 1 implementation (VCG, Nash, PID)
3. Set up continuous benchmarking infrastructure
4. Validate theoretical guarantees with tests

---

**Document Maintenance:**
- Update implementation status as modules are completed
- Add lessons learned and calibration data
- Revise effort estimates based on actual implementation time

**Author:** Claude (Anthropic)
**Date:** 2025-12-26
**Version:** 1.0
