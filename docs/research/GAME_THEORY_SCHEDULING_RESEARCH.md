# Game Theory and Mechanism Design for Scheduling Systems
## Research Report and Implementation Recommendations

**Author:** Claude Research Team
**Date:** 2025-12-20
**Purpose:** Explore exotic game theory concepts for enhancing the residency scheduler's swap matching and fair workload distribution mechanisms

---

## Executive Summary

This report investigates advanced game-theoretic and mechanism design concepts applicable to medical residency scheduling systems, with a focus on:

1. **Incentive-compatible preference elicitation** - Getting truthful preferences from faculty
2. **Fair swap matching algorithms** - Optimal allocation of shift swaps
3. **Workload distribution fairness** - Ensuring equitable duty assignment
4. **Strategic behavior prevention** - Designing mechanisms resistant to gaming

The system already implements **stigmergy-based preference tracking** (biological swarm intelligence). We propose complementary game-theoretic mechanisms that leverage existing infrastructure while adding strategyproof matching, fair division algorithms, and Nash equilibrium analysis.

---

## Table of Contents

1. [Nash Equilibrium in Scheduling](#1-nash-equilibrium-in-scheduling)
2. [Mechanism Design Fundamentals](#2-mechanism-design-fundamentals)
3. [Auction Theory for Shift Allocation](#3-auction-theory-for-shift-allocation)
4. [Cooperative Game Theory](#4-cooperative-game-theory)
5. [Evolutionary Game Theory](#5-evolutionary-game-theory)
6. [Schelling's Segregation Model](#6-schellings-segregation-model)
7. [Principal-Agent Problem](#7-principal-agent-problem)
8. [Practical Implementation Roadmap](#8-practical-implementation-roadmap)
9. [Integration with Existing Systems](#9-integration-with-existing-systems)
10. [References](#10-references)

---

## 1. Nash Equilibrium in Scheduling

### Core Principle

A **Nash Equilibrium** is a state where no player can improve their outcome by unilaterally changing their strategy, given other players' strategies remain fixed. In scheduling, this represents stable assignments where no single faculty member would benefit from requesting a swap.

**Mathematical Definition:**
A strategy profile (s₁*, s₂*, ..., sₙ*) is a Nash equilibrium if for each player i:

```
u_i(s_i*, s_{-i}*) ≥ u_i(s_i, s_{-i}*) for all strategies s_i
```

Where u_i is player i's utility and s_{-i}* represents all other players' equilibrium strategies.

### Application to Shift Scheduling

#### 1.1 Stable Schedule States

**Problem:** Determine when a schedule has reached a stable state where faculty are satisfied.

**Implementation:**
```python
class NashEquilibriumAnalyzer:
    """
    Analyzes schedules for Nash equilibrium properties.

    A schedule is in Nash equilibrium if no single faculty member
    can improve their utility by requesting a swap that would be accepted.
    """

    def is_schedule_stable(
        self,
        schedule: Schedule,
        utility_function: Callable[[UUID, Assignment], float]
    ) -> tuple[bool, list[str]]:
        """
        Check if schedule is in Nash equilibrium.

        Returns:
            (is_stable, list_of_improvement_opportunities)
        """
        improvements = []

        for faculty in schedule.faculty:
            current_utility = self._calculate_total_utility(
                faculty, schedule, utility_function
            )

            # Check all possible single-swap improvements
            for other_faculty in schedule.faculty:
                if other_faculty == faculty:
                    continue

                for my_slot in faculty.assignments:
                    for their_slot in other_faculty.assignments:
                        # Simulate swap
                        new_utility = self._utility_after_swap(
                            faculty, my_slot, their_slot,
                            schedule, utility_function
                        )

                        if new_utility > current_utility:
                            improvements.append(
                                f"{faculty.name} could improve by swapping "
                                f"{my_slot.week} with {other_faculty.name}'s "
                                f"{their_slot.week}"
                            )

        return (len(improvements) == 0, improvements)

    def calculate_nash_distance(self, schedule: Schedule) -> float:
        """
        Calculate how far the schedule is from Nash equilibrium.

        Returns a score 0-1 where 0 = at equilibrium, 1 = very unstable.
        """
        total_potential_improvement = 0.0
        total_possible_swaps = 0

        for faculty in schedule.faculty:
            current_util = self._calculate_total_utility(faculty, schedule)

            for swap in self._enumerate_possible_swaps(faculty, schedule):
                total_possible_swaps += 1
                potential_util = self._utility_after_swap(faculty, swap)
                improvement = max(0, potential_util - current_util)
                total_potential_improvement += improvement

        if total_possible_swaps == 0:
            return 0.0

        # Normalize by number of possible swaps
        avg_improvement = total_potential_improvement / total_possible_swaps

        # Convert to 0-1 scale (assuming max utility difference is 1.0)
        return min(avg_improvement, 1.0)
```

#### 1.2 Mixed Strategy Nash Equilibrium for Scheduling Games

Recent research ([TST 2024](https://www.sciopen.com/article/10.26599/TST.2024.9010056)) shows that scheduling can be modeled as a game where faculty use **mixed strategies** - probabilistic preferences over shifts.

**Application:** Use historical preference data from stigmergy trails to infer faculty mixed strategies:

```python
def infer_mixed_strategy_from_trails(
    self,
    faculty_id: UUID,
    slot_type: str
) -> float:
    """
    Infer probability faculty prefers this slot type based on trail history.

    Uses stigmergy trail strength as Bayesian prior for mixed strategy.
    """
    trails = self.stigmergy.get_faculty_preferences(
        faculty_id,
        trail_type=TrailType.PREFERENCE,
        min_strength=0.1
    )

    # Filter to relevant slot type
    relevant_trails = [t for t in trails if t.slot_type == slot_type]

    if not relevant_trails:
        return 0.0  # No preference data = uniform distribution

    # Aggregate trail strengths with recency weighting
    total_strength = 0.0
    total_weight = 0.0

    for trail in relevant_trails:
        # Weight by recency (exponential decay)
        age_days = trail.days_since_reinforced
        recency_weight = math.exp(-0.1 * age_days)

        total_strength += trail.strength * recency_weight
        total_weight += recency_weight

    if total_weight == 0:
        return 0.0

    # Normalize to probability
    return min(total_strength / total_weight, 1.0)
```

### Integration with Existing System

**Stigmergy → Nash Equilibrium:**
- Use stigmergy trails to define utility functions
- Trail strength = preference intensity
- Collective preference = Nash equilibrium attractor

```python
# In SwapAutoMatcher, add Nash stability check
def suggest_optimal_matches_with_stability(
    self,
    request_id: UUID,
    top_k: int = 5
) -> list[RankedMatch]:
    """
    Suggest matches that move schedule toward Nash equilibrium.
    """
    matches = self.suggest_optimal_matches(request_id, top_k)

    # Enhance with stability analysis
    analyzer = NashEquilibriumAnalyzer()

    for match in matches:
        # Calculate if this swap improves Nash distance
        stability_improvement = analyzer.calculate_stability_improvement(
            current_schedule=self._get_current_schedule(),
            proposed_swap=match
        )

        # Boost score for stability-improving swaps
        match.compatibility_score *= (1.0 + 0.2 * stability_improvement)

        if stability_improvement > 0.3:
            match.explanation += "; Significantly improves schedule stability"

    return sorted(matches, key=lambda m: m.compatibility_score, reverse=True)
```

---

## 2. Mechanism Design Fundamentals

### Core Principle

**Mechanism design** is "reverse game theory" - designing rules/incentives to achieve desired outcomes when participants act strategically. Key properties:

1. **Incentive Compatibility (IC):** Truth-telling is optimal
2. **Individual Rationality (IR):** Participation is beneficial
3. **Budget Balance:** No external subsidies needed
4. **Efficiency:** Maximizes social welfare

**Revelation Principle:** Any outcome achievable with a complex mechanism can be achieved by a truthful direct-revelation mechanism.

### Application to Preference Elicitation

#### 2.1 Strategyproof Preference Collection

**Problem:** Faculty may lie about preferences to game the scheduling system.

**Solution:** Design mechanisms where truth-telling is dominant-strategy incentive-compatible (DSIC).

```python
class StrategyproofPreferenceElicitor:
    """
    Collects faculty preferences in a strategyproof manner.

    Implements the Revelation Principle: design mechanism where
    truthful reporting is the dominant strategy.
    """

    def collect_preferences_vcg(
        self,
        faculty_id: UUID,
        available_slots: list[Slot]
    ) -> list[tuple[Slot, float]]:
        """
        Collect preferences using Vickrey-Clarke-Groves (VCG) mechanism.

        VCG is strategyproof: faculty cannot benefit by lying.

        Returns:
            List of (slot, true_valuation) pairs
        """
        # Ask faculty to rank all slots (reports)
        reported_ranking = self._ask_for_ranking(faculty_id, available_slots)

        # VCG payment rule ensures truthfulness
<<<<<<< HEAD
        # Faculty pays the "externality" they impose on others
=======
        ***REMOVED*** pays the "externality" they impose on others
>>>>>>> origin/docs/session-14-summary
        allocation = self._vcg_allocate(reported_ranking, available_slots)

        # Calculate VCG payment (difference in others' welfare)
        payment = self._calculate_vcg_payment(faculty_id, allocation)

        # In our context, "payment" is constraint satisfaction cost
        # (e.g., working less preferred shifts, ACGME burden)

        return allocation

    def _vcg_allocate(
        self,
        rankings: dict[UUID, list[tuple[Slot, float]]],
        slots: list[Slot]
    ) -> dict[UUID, list[Slot]]:
        """
        Allocate slots to maximize total reported utility.

        This is the standard VCG allocation rule.
        """
        # This is a maximum weight matching problem
        # Use Hungarian algorithm or linear programming
        allocation = self._maximum_weight_matching(rankings, slots)

        return allocation

    def _calculate_vcg_payment(
        self,
        faculty_id: UUID,
        allocation: dict[UUID, list[Slot]]
    ) -> float:
        """
        Calculate VCG payment = externality imposed on others.

        Payment = (welfare of others without you) -
                  (welfare of others with you)
        """
        # Total welfare with this faculty
        total_with = self._calculate_social_welfare(allocation)

        # Remove this faculty and re-optimize
        allocation_without = self._reallocate_without(faculty_id, allocation)
        total_without = self._calculate_social_welfare(allocation_without)

        # Externality = reduction in others' welfare due to your presence
        externality = total_without - (total_with - allocation[faculty_id].utility)

        return max(0, externality)
```

#### 2.2 Preventing Preference Manipulation

**Gibbard-Satterthwaite Theorem:** For 3+ alternatives, the only strategyproof voting rule that isn't dictatorial is a random dictatorship.

**Implication:** Pure deterministic voting over schedules cannot be fully strategyproof. Solutions:

1. **Random Serial Dictatorship (RSD):** Random order, each picks best available
2. **Probabilistic Assignment:** Each faculty gets lottery over shifts
3. **Restricted Domains:** Limit to single-peaked preferences

```python
class RandomSerialDictatorship:
    """
    Implements Random Serial Dictatorship for shift allocation.

    Properties:
    - Strategyproof (truthful reporting is dominant strategy)
    - Ex-post efficient (resulting allocation is Pareto optimal)
    - Anonymous (all faculty treated equally)
    """

    def allocate_shifts(
        self,
        faculty: list[UUID],
        shifts: list[Shift],
        preferences: dict[UUID, list[Shift]]  # Ordered by preference
    ) -> dict[UUID, Shift]:
        """
        Allocate shifts using RSD.

        Returns:
            Allocation mapping faculty → shift
        """
        allocation = {}
        available_shifts = shifts.copy()

        # Randomize faculty order (uniformly)
        random_order = random.sample(faculty, len(faculty))

        for faculty_id in random_order:
<<<<<<< HEAD
            # Faculty picks their most preferred available shift
=======
            ***REMOVED*** picks their most preferred available shift
>>>>>>> origin/docs/session-14-summary
            pref_list = preferences[faculty_id]

            for shift in pref_list:
                if shift in available_shifts:
                    allocation[faculty_id] = shift
                    available_shifts.remove(shift)
                    break

        return allocation

    def calculate_rsd_probabilities(
        self,
        faculty_id: UUID,
        shift: Shift,
        all_preferences: dict[UUID, list[Shift]]
    ) -> float:
        """
        Calculate probability faculty gets shift under RSD.

        This is #P-complete in general, but can use Monte Carlo estimation
        or exact calculation for small instances.
        """
        # Monte Carlo estimation
        num_samples = 10000
        successes = 0

        for _ in range(num_samples):
            allocation = self.allocate_shifts(
                list(all_preferences.keys()),
                list(all_preferences.values())[0],  # All shifts
                all_preferences
            )

            if allocation.get(faculty_id) == shift:
                successes += 1

        return successes / num_samples
```

### Integration with Existing System

```python
# In FacultyPreferenceService
def collect_preferences_strategyproof(
    self,
    faculty_id: UUID,
    available_weeks: list[date]
) -> FacultyPreference:
    """
    Collect preferences using strategyproof mechanism.

    Integrates with existing preference system but adds game-theoretic guarantees.
    """
    # Option 1: Use RSD for actual allocation
    rsd = RandomSerialDictatorship()

    # Get reported preferences (faculty has no incentive to lie)
    reported_prefs = self._ask_for_preference_ranking(faculty_id, available_weeks)

    # Store in existing FacultyPreference model
    preferences = self.get_or_create_preferences(faculty_id)

    # Convert ranking to preferred/blocked weeks
    top_k = int(len(reported_prefs) * 0.3)  # Top 30% = preferred
    bottom_k = int(len(reported_prefs) * 0.2)  # Bottom 20% = blocked

    preferences.preferred_weeks = [w.isoformat() for w in reported_prefs[:top_k]]
    preferences.blocked_weeks = [w.isoformat() for w in reported_prefs[-bottom_k:]]

    # Record in stigmergy system for learning
    for i, week in enumerate(reported_prefs):
        strength = 1.0 - (i / len(reported_prefs))  # Linear decay

        if strength > 0.7:
            trail_type = TrailType.PREFERENCE
        elif strength < 0.3:
            trail_type = TrailType.AVOIDANCE
        else:
            continue  # Neutral

        self.stigmergy.record_preference(
            faculty_id=faculty_id,
            trail_type=trail_type,
            slot_type=f"week_{week.isocalendar()[1]}",
            strength=strength
        )

    return preferences
```

---

## 3. Auction Theory for Shift Allocation

### Core Principle

**Auction theory** studies optimal allocation through competitive bidding. Key mechanisms:

1. **Vickrey (Second-Price) Auction:** Truthful, efficient, simple
2. **Combinatorial Auctions:** Bid on bundles (e.g., consecutive shifts)
3. **Double Auctions:** Both buyers and sellers submit bids

### Application to Swap Markets

#### 3.1 Vickrey Auction for Priority Swaps

**Problem:** Multiple faculty want the same desirable shift. How to allocate fairly?

**Solution:** Use **priority points** as "currency" in a Vickrey auction.

```python
class ShiftAuctionMechanism:
    """
    Implements auction-based shift allocation using priority points.

    Faculty earn priority points through:
    - Taking undesirable shifts
    - Working holidays
    - Coverage during emergencies
    - Seniority

    They spend points to bid for desirable shifts.
    """

    def __init__(self, db: Session):
        self.db = db
        self.point_ledger = PriorityPointLedger(db)

    def run_vickrey_auction(
        self,
        shift: Shift,
        bidders: list[UUID],
        bids: dict[UUID, float]  # faculty_id → bid in points
    ) -> tuple[UUID, float]:
        """
        Run Vickrey (second-price) auction for a shift.

        Returns:
            (winner_id, payment) where payment = second-highest bid

        Properties:
        - Strategyproof: bidding true value is dominant strategy
        - Efficient: shift goes to faculty who values it most
        - Revenue equivalent: same expected revenue as first-price
        """
        if not bidders or not bids:
            raise ValueError("Need at least one bidder")

        # Sort bids descending
        sorted_bids = sorted(
            [(fid, bids[fid]) for fid in bidders],
            key=lambda x: -x[1]
        )

        winner_id = sorted_bids[0][0]

        # Payment = second highest bid (Vickrey rule)
        if len(sorted_bids) > 1:
            payment = sorted_bids[1][1]
        else:
            payment = 0.0  # No competition, pay reserve price

        # Deduct points from winner
        self.point_ledger.deduct_points(winner_id, payment)

        return (winner_id, payment)

    def run_combinatorial_auction(
        self,
        shifts: list[Shift],
        bundle_bids: dict[UUID, list[tuple[frozenset[Shift], float]]]
    ) -> dict[UUID, set[Shift]]:
        """
        Run combinatorial auction for shift bundles.

        Faculty can bid on bundles (e.g., "consecutive weekend shifts").

        This is the Winner Determination Problem (WDP), which is NP-hard.
        Use ILP solver or approximation algorithm.
        """
        # Formulate as Integer Linear Program
        # Variables: x[faculty, bundle] ∈ {0, 1}
        # Objective: maximize Σ bid[faculty, bundle] * x[faculty, bundle]
        # Constraints: each shift appears in at most one winning bundle

        winner_allocation = self._solve_wdp_ilp(shifts, bundle_bids)

        return winner_allocation

    def _solve_wdp_ilp(
        self,
        shifts: list[Shift],
        bundle_bids: dict[UUID, list[tuple[frozenset[Shift], float]]]
    ) -> dict[UUID, set[Shift]]:
        """
        Solve Winner Determination Problem using ILP.

        Uses OR-Tools or similar ILP solver.
        """
        from ortools.linear_solver import pywraplp

        solver = pywraplp.Solver.CreateSolver('SCIP')

        # Create variables for each (faculty, bundle) pair
        variables = {}
        for faculty_id, bundles in bundle_bids.items():
            for bundle, bid in bundles:
                var = solver.BoolVar(f'x_{faculty_id}_{id(bundle)}')
                variables[(faculty_id, bundle)] = (var, bid)

        # Objective: maximize total value
        objective = solver.Objective()
        for (fid, bundle), (var, bid) in variables.items():
            objective.SetCoefficient(var, bid)
        objective.SetMaximization()

        # Constraints: each shift in at most one bundle
        for shift in shifts:
            constraint = solver.Constraint(0, 1)
            for (fid, bundle), (var, bid) in variables.items():
                if shift in bundle:
                    constraint.SetCoefficient(var, 1)

        # Solve
        status = solver.Solve()

        if status != pywraplp.Solver.OPTIMAL:
            return {}  # No feasible solution

        # Extract winning allocations
        allocation = {}
        for (fid, bundle), (var, bid) in variables.items():
            if var.solution_value() > 0.5:  # Binary variable is 1
                allocation[fid] = set(bundle)

        return allocation
```

#### 3.2 Double Auction for Swap Matching

**Problem:** Decentralized swap market where faculty can both offer and request swaps.

**Solution:** **Double auction** where faculty submit ask/bid prices in priority points.

```python
class SwapDoubleAuction:
    """
    Double auction for shift swaps.

    Faculty who want to give away a shift = sellers (ask price)
    Faculty who want to take a shift = buyers (bid price)

    Mechanism clears market at equilibrium price.
    """

    def run_double_auction(
        self,
        asks: dict[UUID, tuple[Shift, float]],  # seller → (shift, ask_price)
        bids: dict[UUID, tuple[Shift, float]]   # buyer → (shift, bid_price)
    ) -> list[tuple[UUID, UUID, Shift, float]]:
        """
        Run double auction and return matched swaps.

        Uses k-Double Auction mechanism (strategyproof).

        Returns:
            List of (seller, buyer, shift, price) trades
        """
        trades = []

        # Group by shift type
        shifts_offered = {}
        for seller_id, (shift, ask) in asks.items():
            key = (shift.week, shift.rotation)
            if key not in shifts_offered:
                shifts_offered[key] = []
            shifts_offered[key].append((seller_id, ask))

        shifts_wanted = {}
        for buyer_id, (shift, bid) in bids.items():
            key = (shift.week, shift.rotation)
            if key not in shifts_wanted:
                shifts_wanted[key] = []
            shifts_wanted[key].append((buyer_id, bid))

        # Match for each shift type
        for shift_key in set(shifts_offered.keys()) & set(shifts_wanted.keys()):
            sellers = sorted(shifts_offered[shift_key], key=lambda x: x[1])  # Asc ask
            buyers = sorted(shifts_wanted[shift_key], key=lambda x: -x[1])   # Desc bid

            # Find equilibrium: where supply meets demand
            for i, (seller_id, ask) in enumerate(sellers):
                if i >= len(buyers):
                    break

                buyer_id, bid = buyers[i]

                if bid >= ask:  # Trade possible
                    # k-Double Auction price rule (k=0.5 = median)
                    price = 0.5 * (ask + bid)

                    trades.append((seller_id, buyer_id, shift_key, price))

        return trades
```

### Integration with Existing System

```python
# Add to SwapAutoMatcher
class AuctionEnhancedMatcher(SwapAutoMatcher):
    """
    Extends swap matcher with auction-based prioritization.
    """

    def __init__(self, db: Session, criteria: MatchingCriteria | None = None):
        super().__init__(db, criteria)
        self.auction = ShiftAuctionMechanism(db)

    def suggest_with_priority_auction(
        self,
        request_id: UUID,
        top_k: int = 5
    ) -> list[RankedMatch]:
        """
        Suggest matches using priority point system.

        High-value swaps (blocked weeks, emergencies) get priority through
        implicit auction mechanism.
        """
        matches = self.suggest_optimal_matches(request_id, top_k)

        request = self.db.query(SwapRecord).get(request_id)

        # Calculate "willingness to pay" from preference intensity
        source_prefs = self.preference_service.get_or_create_preferences(
            request.source_faculty_id
        )

        # If source week is blocked → high willingness to swap (high bid)
        if self.preference_service.is_week_blocked(
            request.source_faculty_id,
            request.source_week
        ):
            urgency_points = 100.0  # High priority points
        else:
            urgency_points = 10.0  # Normal priority

        # Enhance matches with auction priority
        for match in matches:
            # Calculate counter-party's ask price
            partner_prefs = self.preference_service.get_or_create_preferences(
                match.match.faculty_b_id
            )

            if self.preference_service.is_week_preferred(
                match.match.faculty_b_id,
                request.source_week
            ):
                ask_price = 5.0  # Low ask (they want it)
            else:
                ask_price = 50.0  # High ask (reluctant)

            # Match if bid > ask
            if urgency_points >= ask_price:
                match.priority = MatchPriority.HIGH
                match.explanation += f"; Auction priority (bid={urgency_points:.0f} > ask={ask_price:.0f})"

        return matches
```

---

## 4. Cooperative Game Theory

### Core Principle

**Cooperative game theory** studies how coalitions form and how payoffs are distributed. The **Shapley value** provides a fair division based on marginal contributions.

**Shapley Value Formula:**
```
φᵢ(v) = Σ [ |S|!(n-|S|-1)! / n! ] * [v(S∪{i}) - v(S)]
      S⊆N\{i}
```

Where:
- φᵢ(v) = Shapley value for player i
- S = subset of players (coalition)
- v(S) = value function for coalition S
- n = total number of players

### Application to Workload Distribution

#### 4.1 Shapley-Fair Workload Allocation

**Problem:** How to fairly distribute the burden of undesirable shifts?

**Solution:** Use Shapley value to allocate based on each faculty's contribution to coverage capacity.

```python
class ShapleyWorkloadAllocator:
    """
    Allocates workload using Shapley value for fairness.

    The Shapley value ensures each faculty member's workload reflects
    their marginal contribution to the program's coverage capability.

    Based on: "Non-Monetary Fair Scheduling — a Cooperative Game Theory Approach"
    https://duch.mimuw.edu.pl/~ps219737/wp-content/uploads/2023/03/shapleyScheduling-spaa.pdf
    """

    def calculate_shapley_values(
        self,
        faculty: list[UUID],
        capability_function: Callable[[set[UUID]], float]
    ) -> dict[UUID, float]:
        """
        Calculate Shapley value for each faculty member.

        Args:
            faculty: List of faculty IDs
            capability_function: Maps subset of faculty → coverage capability
                                 (e.g., number of shifts they can collectively cover)

        Returns:
            Shapley value for each faculty (their "fair share" of work)
        """
        n = len(faculty)
        shapley_values = {fid: 0.0 for fid in faculty}

        # Enumerate all possible orderings (permutations)
        # For each ordering, add marginal contribution
        for perm in itertools.permutations(faculty):
            coalition = set()

            for i, faculty_id in enumerate(perm):
                # Value before adding this faculty
                value_before = capability_function(coalition)

                # Value after adding this faculty
                coalition.add(faculty_id)
                value_after = capability_function(coalition)

                # Marginal contribution
                marginal = value_after - value_before

                shapley_values[faculty_id] += marginal

        # Average over all permutations
        num_perms = math.factorial(n)
        for fid in shapley_values:
            shapley_values[fid] /= num_perms

        return shapley_values

    def approximate_shapley_monte_carlo(
        self,
        faculty: list[UUID],
        capability_function: Callable[[set[UUID]], float],
        num_samples: int = 1000
    ) -> dict[UUID, float]:
        """
        Approximate Shapley values using Monte Carlo sampling.

        Exact computation is O(n! * 2^n), which is intractable for large n.
        Monte Carlo gives good approximation in polynomial time.
        """
        shapley_values = {fid: 0.0 for fid in faculty}

        for _ in range(num_samples):
            # Random permutation
            perm = random.sample(faculty, len(faculty))

            coalition = set()
            for faculty_id in perm:
                value_before = capability_function(coalition)
                coalition.add(faculty_id)
                value_after = capability_function(coalition)

                marginal = value_after - value_before
                shapley_values[faculty_id] += marginal

        # Average over samples
        for fid in shapley_values:
            shapley_values[fid] /= num_samples

        return shapley_values

    def allocate_shifts_shapley_fair(
        self,
        faculty: list[Person],
        shifts: list[Shift],
        qualifications: dict[UUID, set[str]]  # faculty → set of rotation types
    ) -> dict[UUID, list[Shift]]:
        """
        Allocate shifts proportional to Shapley values.

        Faculty with higher Shapley values (more critical to coverage)
        get more choice in shift selection.
        """
        # Define capability function
        def coverage_capability(coalition: set[UUID]) -> float:
            """
            How many shifts can this coalition cover?
            """
            covered = 0
            for shift in shifts:
                # Check if any member can cover this shift
                can_cover = any(
                    shift.rotation_type in qualifications.get(fid, set())
                    for fid in coalition
                )
                if can_cover:
                    covered += 1
            return float(covered)

        # Calculate Shapley values
        faculty_ids = [f.id for f in faculty]
        shapley = self.approximate_shapley_monte_carlo(
            faculty_ids,
            coverage_capability,
            num_samples=5000
        )

        # Allocate shifts in proportion to Shapley values
        total_shapley = sum(shapley.values())

        allocation = {fid: [] for fid in faculty_ids}
        available_shifts = shifts.copy()

        # Sort faculty by Shapley value (descending)
        sorted_faculty = sorted(
            faculty_ids,
            key=lambda fid: -shapley[fid]
        )

        # Allocate using weighted random selection
        for shift in shifts:
            # Who can cover this shift?
            eligible = [
                fid for fid in sorted_faculty
                if shift.rotation_type in qualifications.get(fid, set())
                and len(allocation[fid]) < (len(shifts) / len(faculty)) * 1.5  # Load balance
            ]

            if not eligible:
                continue  # No one available

            # Select proportional to Shapley value (those who contribute more get more choice)
            weights = [shapley[fid] for fid in eligible]
            selected = random.choices(eligible, weights=weights, k=1)[0]

            allocation[selected].append(shift)

        return allocation
```

#### 4.2 Core Stability for Schedule Assignments

The **core** of a cooperative game is the set of allocations where no coalition can improve by defecting.

```python
def is_allocation_in_core(
    allocation: dict[UUID, list[Shift]],
    faculty: list[UUID],
    utility_function: Callable[[UUID, list[Shift]], float]
) -> bool:
    """
    Check if allocation is in the core (no coalition wants to defect).

    Returns True if stable, False if some coalition can improve by defecting.
    """
    n = len(faculty)

    # Check all possible coalitions
    for r in range(1, n + 1):
        for coalition in itertools.combinations(faculty, r):
            coalition_set = set(coalition)

            # Current utility for coalition members
            current_utility = sum(
                utility_function(fid, allocation[fid])
                for fid in coalition_set
            )

            # Can they improve by reallocating among themselves?
            coalition_shifts = []
            for fid in coalition_set:
                coalition_shifts.extend(allocation[fid])

            # Find best reallocation within coalition
            best_realloc = optimize_allocation_within_coalition(
                coalition_set,
                coalition_shifts,
                utility_function
            )

            best_utility = sum(
                utility_function(fid, best_realloc[fid])
                for fid in coalition_set
            )

            if best_utility > current_utility:
                return False  # Coalition can improve → not in core

    return True  # No coalition can improve → in core
```

### Integration with Existing System

```python
# Add Shapley-based workload fairness check to resilience monitoring
class ShapleyResilienceMetric:
    """
    Integrates Shapley value analysis into resilience framework.
    """

    def calculate_workload_fairness(
        self,
        schedule: Schedule
    ) -> dict[str, Any]:
        """
        Calculate how fair the workload distribution is using Shapley values.

        Returns:
            Metrics including Shapley values, fairness score, and recommendations
        """
        allocator = ShapleyWorkloadAllocator()

        # Get all faculty and their qualifications
        faculty = schedule.get_all_faculty()
        qualifications = {
            f.id: set(f.credentialing_records.keys())
            for f in faculty
        }

        # Calculate Shapley values
        faculty_ids = [f.id for f in faculty]

        def coverage_capability(coalition: set[UUID]) -> float:
            # From resilience.py - use existing coverage metrics
            return calculate_coverage_capacity(coalition, schedule)

        shapley_values = allocator.approximate_shapley_monte_carlo(
            faculty_ids,
            coverage_capability
        )

        # Calculate actual workload
        actual_workload = {
            f.id: len([a for a in schedule.assignments if a.person_id == f.id])
            for f in faculty
        }

        # Compare Shapley-fair allocation vs actual
        total_shifts = sum(actual_workload.values())
        expected_workload = {
            fid: (shapley_values[fid] / sum(shapley_values.values())) * total_shifts
            for fid in faculty_ids
        }

        # Calculate fairness deviation
        deviations = {
            fid: abs(actual_workload[fid] - expected_workload[fid])
            for fid in faculty_ids
        }

        max_deviation = max(deviations.values())
        avg_deviation = statistics.mean(deviations.values())

        # Fairness score (0 = perfectly fair, 1 = very unfair)
        fairness_score = min(avg_deviation / (total_shifts / len(faculty)), 1.0)

        return {
            "shapley_values": shapley_values,
            "expected_workload": expected_workload,
            "actual_workload": actual_workload,
            "deviations": deviations,
            "fairness_score": 1.0 - fairness_score,  # Convert to 0-1 where 1=fair
            "max_deviation": max_deviation,
            "recommendations": self._generate_fairness_recommendations(
                deviations, expected_workload, actual_workload
            )
        }
```

---

## 5. Evolutionary Game Theory

### Core Principle

**Evolutionary game theory** models how strategies evolve over time through natural selection. The **replicator dynamics** equation describes strategy evolution:

```
dx_i/dt = x_i * (u_i(x) - ū(x))
```

Where:
- x_i = frequency of strategy i
- u_i(x) = fitness/payoff of strategy i
- ū(x) = average population fitness

**Evolutionarily Stable Strategy (ESS):** A strategy that, if adopted by a population, cannot be invaded by rare mutants.

### Application to Preference Evolution

#### 5.1 Learning Optimal Swap Strategies

**Problem:** Faculty learn over time which swap strategies work best.

**Solution:** Model as replicator dynamics where successful strategies spread.

```python
class EvolutionarySwapLearner:
    """
    Models evolution of swap request strategies using replicator dynamics.

    Faculty observe which strategies succeed (accepted swaps) and
    adjust their behavior over time.
    """

    def __init__(self, db: Session):
        self.db = db
        self.strategy_frequencies = {}  # strategy_type → frequency

    def update_strategy_frequencies(
        self,
        time_window_days: int = 30
    ):
        """
        Update strategy frequencies based on recent swap outcomes.

        Successful strategies increase in frequency (replicator dynamics).
        """
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)

        # Get recent swaps
        swaps = self.db.query(SwapRecord).filter(
            SwapRecord.requested_at >= cutoff
        ).all()

        # Categorize swap strategies
        strategies = {
            "early_request": 0,      # Request >2 weeks in advance
            "late_request": 0,        # Request <1 week in advance
            "mutual_preference": 0,   # Both parties prefer swap
            "one_way": 0,            # Only one party benefits
            "emergency": 0,          # Blocked week (urgent)
            "opportunistic": 0,      # Not urgent, but preferred
        }

        success_count = {k: 0 for k in strategies.keys()}

        for swap in swaps:
            # Categorize this swap's strategy
            strategy = self._categorize_swap_strategy(swap)
            strategies[strategy] += 1

            if swap.status == SwapStatus.EXECUTED:
                success_count[strategy] += 1

        # Calculate fitness (success rate) for each strategy
        fitness = {}
        for strategy in strategies:
            if strategies[strategy] > 0:
                fitness[strategy] = success_count[strategy] / strategies[strategy]
            else:
                fitness[strategy] = 0.0

        # Average fitness
        avg_fitness = statistics.mean(fitness.values()) if fitness else 0.5

        # Apply replicator dynamics
        # dx/dt = x * (fitness - avg_fitness)
        dt = time_window_days / 365.0  # Normalize to years

        for strategy in strategies:
            current_freq = self.strategy_frequencies.get(strategy, 1.0 / len(strategies))

            # Discrete-time replicator equation
            growth_rate = current_freq * (fitness[strategy] - avg_fitness)
            new_freq = current_freq + growth_rate * dt

            # Normalize to ensure sum = 1
            self.strategy_frequencies[strategy] = max(0.0, new_freq)

        # Renormalize
        total = sum(self.strategy_frequencies.values())
        if total > 0:
            for strategy in self.strategy_frequencies:
                self.strategy_frequencies[strategy] /= total

    def suggest_optimal_strategy(
        self,
        faculty_id: UUID,
        current_situation: dict[str, Any]
    ) -> str:
        """
        Suggest which swap strategy to use based on evolved frequencies.

        Higher-fitness strategies are recommended more often.
        """
        if not self.strategy_frequencies:
            self.update_strategy_frequencies()

        # Filter strategies applicable to current situation
        applicable = self._filter_applicable_strategies(
            self.strategy_frequencies,
            current_situation
        )

        if not applicable:
            return "one_way"  # Default

        # Select strategy proportional to frequency (evolutionary success)
        strategies = list(applicable.keys())
        weights = list(applicable.values())

        return random.choices(strategies, weights=weights, k=1)[0]

    def _categorize_swap_strategy(self, swap: SwapRecord) -> str:
        """Categorize a swap request into strategy type."""
        days_until = (swap.source_week - swap.requested_at.date()).days

        # Check if it's mutual preference
        source_prefs = self.db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == swap.source_faculty_id
        ).first()

        target_prefs = self.db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == swap.target_faculty_id
        ).first()

        is_mutual = (
            source_prefs and target_prefs and
            swap.target_week and
            swap.source_week.isoformat() in (target_prefs.preferred_weeks or []) and
            swap.target_week.isoformat() in (source_prefs.preferred_weeks or [])
        )

        is_emergency = (
            source_prefs and
            swap.source_week.isoformat() in (source_prefs.blocked_weeks or [])
        )

        if is_emergency:
            return "emergency"
        elif is_mutual:
            return "mutual_preference"
        elif days_until > 14:
            return "early_request"
        elif days_until < 7:
            return "late_request"
        elif source_prefs and swap.target_week and swap.target_week.isoformat() in (source_prefs.preferred_weeks or []):
            return "opportunistic"
        else:
            return "one_way"
```

#### 5.2 Evolutionarily Stable Scheduling Strategies

```python
def find_evolutionarily_stable_strategy(
    population: list[UUID],
    strategy_payoffs: Callable[[str, str], float],
    strategies: list[str]
) -> str:
    """
    Find ESS - strategy that cannot be invaded by mutants.

    A strategy s* is ESS if for all s ≠ s*:
    - u(s*, s*) > u(s, s*), OR
    - u(s*, s*) = u(s, s*) AND u(s*, s) > u(s, s)

    Where u(s1, s2) = payoff for playing s1 against s2.
    """
    for candidate in strategies:
        is_ess = True

        for alternative in strategies:
            if alternative == candidate:
                continue

            # Payoff for candidate vs candidate
            u_cc = strategy_payoffs(candidate, candidate)
            # Payoff for alternative vs candidate
            u_ac = strategy_payoffs(alternative, candidate)

            # First condition: candidate must do better vs itself
            if u_ac > u_cc:
                is_ess = False
                break

            # Second condition: if tied, candidate must beat alternative
            if u_ac == u_cc:
                u_ca = strategy_payoffs(candidate, alternative)
                u_aa = strategy_payoffs(alternative, alternative)

                if u_ca <= u_aa:
                    is_ess = False
                    break

        if is_ess:
            return candidate

    return None  # No ESS found
```

### Integration with Existing System

```python
# Enhance stigmergy with evolutionary dynamics
class EvolutionaryStigmergy(StigmergicScheduler):
    """
    Extends stigmergy with evolutionary game theory.

    Trail strengths evolve according to replicator dynamics based on
    swap success rates.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evolutionary_learner = EvolutionarySwapLearner(db=None)  # Set db later

    def evolve_trail_strengths(self, time_delta_days: float = 1.0):
        """
        Apply replicator dynamics to trail strengths.

        Trails associated with successful swaps increase in strength.
        """
        # Calculate fitness for each trail based on swap outcomes
        for trail in self.trails.values():
            if trail.trail_type != TrailType.SWAP_AFFINITY:
                continue

            # Count successful swaps using this trail
            successful_swaps = sum(
                1 for _, signal, _ in trail.signal_history
                if signal == SignalType.COMPLETED_SWAP
            )

            total_swaps = sum(
                1 for _, signal, _ in trail.signal_history
                if signal in (SignalType.COMPLETED_SWAP, SignalType.REQUESTED_SWAP)
            )

            if total_swaps == 0:
                continue

            # Fitness = success rate
            fitness = successful_swaps / total_swaps

            # Average fitness across all trails
            all_fitnesses = [
                sum(1 for _, s, _ in t.signal_history if s == SignalType.COMPLETED_SWAP) /
                max(1, sum(1 for _, s, _ in t.signal_history
                          if s in (SignalType.COMPLETED_SWAP, SignalType.REQUESTED_SWAP)))
                for t in self.trails.values()
                if t.trail_type == TrailType.SWAP_AFFINITY
            ]

            avg_fitness = statistics.mean(all_fitnesses) if all_fitnesses else 0.5

            # Replicator dynamics: dx/dt = x(fitness - avg_fitness)
            growth_rate = trail.strength * (fitness - avg_fitness)
            new_strength = trail.strength + growth_rate * (time_delta_days / 365.0)

            # Update trail strength
            trail.strength = max(trail.min_strength, min(trail.max_strength, new_strength))
```

---

## 6. Schelling's Segregation Model

### Core Principle

**Schelling's segregation model** shows how individual preferences for similar neighbors can lead to macro-level segregation, even when individuals have weak preferences.

**Key Insight:** Local preferences → global clustering patterns (emergent behavior).

### Application to Shift Preference Clustering

#### 6.1 Detecting Preference Homophily

**Problem:** Do faculty cluster into groups with similar scheduling preferences?

**Solution:** Apply Schelling dynamics to detect preference-based clustering.

```python
class PreferenceClusteringAnalyzer:
    """
    Analyzes whether faculty cluster into preference groups.

    Uses Schelling model to detect emergent segregation patterns
    in shift preferences.
    """

    def __init__(self, db: Session):
        self.db = db

    def detect_preference_clusters(
        self,
        faculty: list[Person],
        tolerance: float = 0.3
    ) -> dict[str, list[UUID]]:
        """
        Detect faculty clusters based on preference similarity.

        Args:
            faculty: List of faculty members
            tolerance: Minimum similarity to be "satisfied" with neighbors
                      (0 = must be identical, 1 = any neighbor ok)

        Returns:
            Clusters of faculty with similar preferences
        """
        # Build preference similarity matrix
        similarity = {}
        for f1 in faculty:
            for f2 in faculty:
                if f1.id == f2.id:
                    continue
                similarity[(f1.id, f2.id)] = self._calculate_preference_similarity(
                    f1.id, f2.id
                )

        # Simulate Schelling dynamics
        # Start with random "neighborhood" assignments
        num_neighborhoods = max(3, len(faculty) // 5)
        assignments = {
            f.id: random.randint(0, num_neighborhoods - 1)
            for f in faculty
        }

        max_iterations = 100
        for iteration in range(max_iterations):
            moved = False

            for faculty_member in random.sample(faculty, len(faculty)):
                fid = faculty_member.id
                current_neighborhood = assignments[fid]

                # Calculate satisfaction with current neighborhood
                neighbors = [
                    f.id for f in faculty
                    if f.id != fid and assignments[f.id] == current_neighborhood
                ]

                if not neighbors:
                    satisfaction = 0.0
                else:
                    avg_similarity = statistics.mean([
                        similarity.get((fid, nid), 0.0)
                        for nid in neighbors
                    ])
                    satisfaction = avg_similarity

                # If unsatisfied, try to move
                if satisfaction < tolerance:
                    # Find better neighborhood
                    best_neighborhood = current_neighborhood
                    best_satisfaction = satisfaction

                    for target_neighborhood in range(num_neighborhoods):
                        if target_neighborhood == current_neighborhood:
                            continue

                        # Calculate potential satisfaction there
                        potential_neighbors = [
                            f.id for f in faculty
                            if f.id != fid and assignments[f.id] == target_neighborhood
                        ]

                        if not potential_neighbors:
                            potential_satisfaction = 1.0  # Empty = no dissimilarity
                        else:
                            potential_satisfaction = statistics.mean([
                                similarity.get((fid, nid), 0.0)
                                for nid in potential_neighbors
                            ])

                        if potential_satisfaction > best_satisfaction:
                            best_neighborhood = target_neighborhood
                            best_satisfaction = potential_satisfaction

                    # Move if better neighborhood found
                    if best_neighborhood != current_neighborhood:
                        assignments[fid] = best_neighborhood
                        moved = True

            # Stop if no one moved (stable state)
            if not moved:
                break

        # Extract clusters
        clusters = {}
        for neighborhood_id in range(num_neighborhoods):
            cluster_members = [
                fid for fid, assigned in assignments.items()
                if assigned == neighborhood_id
            ]
            if cluster_members:
                clusters[f"cluster_{neighborhood_id}"] = cluster_members

        return clusters

    def _calculate_preference_similarity(
        self,
        faculty_a: UUID,
        faculty_b: UUID
    ) -> float:
        """
        Calculate preference similarity between two faculty.

        Returns value 0-1 where 1 = identical preferences.
        """
        prefs_a = self.db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == faculty_a
        ).first()

        prefs_b = self.db.query(FacultyPreference).filter(
            FacultyPreference.faculty_id == faculty_b
        ).first()

        if not prefs_a or not prefs_b:
            return 0.5  # No data = neutral

        # Calculate overlap in preferred/blocked weeks
        preferred_a = set(prefs_a.preferred_weeks or [])
        preferred_b = set(prefs_b.preferred_weeks or [])

        blocked_a = set(prefs_a.blocked_weeks or [])
        blocked_b = set(prefs_b.blocked_weeks or [])

        # Jaccard similarity
        preferred_overlap = len(preferred_a & preferred_b)
        preferred_union = len(preferred_a | preferred_b)

        blocked_overlap = len(blocked_a & blocked_b)
        blocked_union = len(blocked_a | blocked_b)

        pref_similarity = preferred_overlap / max(1, preferred_union)
        block_similarity = blocked_overlap / max(1, blocked_union)

        # Average
        return 0.5 * (pref_similarity + block_similarity)

    def measure_segregation_level(
        self,
        clusters: dict[str, list[UUID]]
    ) -> float:
        """
        Measure degree of preference segregation (0 = mixed, 1 = highly segregated).

        Uses dissimilarity index from urban segregation research.
        """
        # Calculate within-cluster similarity vs between-cluster similarity
        within_similarity = []
        between_similarity = []

        for cluster_id, members in clusters.items():
            # Within-cluster
            for i, fid_a in enumerate(members):
                for fid_b in members[i+1:]:
                    sim = self._calculate_preference_similarity(fid_a, fid_b)
                    within_similarity.append(sim)

            # Between-cluster
            other_members = [
                fid for cid, members2 in clusters.items()
                if cid != cluster_id
                for fid in members2
            ]

            for fid_a in members:
                for fid_b in random.sample(other_members, min(10, len(other_members))):
                    sim = self._calculate_preference_similarity(fid_a, fid_b)
                    between_similarity.append(sim)

        if not within_similarity or not between_similarity:
            return 0.0

        avg_within = statistics.mean(within_similarity)
        avg_between = statistics.mean(between_similarity)

        # Segregation index
        if avg_within + avg_between == 0:
            return 0.0

        return (avg_within - avg_between) / (avg_within + avg_between + 1e-6)
```

### Integration with Existing System

```python
# Add clustering analysis to resilience monitoring
def analyze_preference_clustering(schedule: Schedule) -> dict[str, Any]:
    """
    Analyze whether faculty self-organize into preference clusters.

    High clustering might indicate:
    - Need for specialized schedules for different preference groups
    - Opportunity for preference-based pods/teams
    - Risk of workload imbalance if clusters have different sizes
    """
    analyzer = PreferenceClusteringAnalyzer(schedule.db)

    clusters = analyzer.detect_preference_clusters(
        schedule.get_all_faculty(),
        tolerance=0.3
    )

    segregation_level = analyzer.measure_segregation_level(clusters)

    # Generate recommendations
    recommendations = []

    if segregation_level > 0.6:
        recommendations.append(
            "High preference clustering detected. Consider creating "
            "specialized scheduling tracks for different preference groups."
        )

    if len(clusters) < 2:
        recommendations.append(
            "Faculty preferences are homogeneous. Standard scheduling should work well."
        )

    # Check cluster size balance
    cluster_sizes = [len(members) for members in clusters.values()]
    if max(cluster_sizes) > 2 * min(cluster_sizes):
        recommendations.append(
            "Unbalanced cluster sizes. Largest group may dominate scheduling decisions."
        )

    return {
        "clusters": clusters,
        "segregation_level": segregation_level,
        "num_clusters": len(clusters),
        "cluster_sizes": {cid: len(members) for cid, members in clusters.items()},
        "recommendations": recommendations
    }
```

---

## 7. Principal-Agent Problem

### Core Principle

The **principal-agent problem** arises when one party (principal) delegates work to another (agent) whose interests may not align. Classic solutions:

1. **Incentive alignment** - Design payments/rewards to align interests
2. **Monitoring** - Observe agent behavior (costly)
3. **Screening** - Separate high/low types before contracting

### Application to Schedule Compliance

#### 7.1 Incentive-Compatible Schedule Acceptance

**Problem:** Faculty (agents) may report false availability to game the system. Administration (principal) wants truthful reporting.

**Solution:** Design mechanism where truth-telling maximizes faculty utility.

```python
class IncentiveAlignmentMechanism:
    """
    Aligns faculty incentives with program goals.

    Implements principal-agent solutions:
    1. Revelation Principle: make truth-telling optimal
    2. Incentive constraints: penalize gaming
    3. Participation constraints: ensure voluntary participation
    """

    def __init__(self, db: Session):
        self.db = db

    def design_incentive_compatible_allocation(
        self,
        faculty: list[UUID],
        shifts: list[Shift],
        reported_preferences: dict[UUID, list[tuple[Shift, float]]]
    ) -> dict[UUID, list[Shift]]:
        """
        Allocate shifts such that truthful preference reporting is optimal.

        Uses VCG-like mechanism:
        - Faculty report valuations for shifts
        - Allocation maximizes total value (efficient)
        - Payments ensure truth-telling is dominant strategy
        """
        # Step 1: Allocate to maximize reported social welfare
        allocation = self._maximize_social_welfare(
            faculty,
            shifts,
            reported_preferences
        )

        # Step 2: Calculate VCG "payments" (opportunity costs)
<<<<<<< HEAD
        # Faculty "pays" by accepting less preferred shifts
=======
        ***REMOVED*** "pays" by accepting less preferred shifts
>>>>>>> origin/docs/session-14-summary
        payments = {}
        for fid in faculty:
            # Welfare of others with this faculty
            total_with = self._social_welfare(allocation, reported_preferences)

            # Welfare of others if this faculty wasn't there
            others_allocation = self._reallocate_without(fid, allocation)
            others_welfare_without = self._social_welfare(
                others_allocation,
                {k: v for k, v in reported_preferences.items() if k != fid}
            )

            # This faculty's own welfare
            own_welfare = sum(
                value for shift, value in reported_preferences[fid]
                if shift in allocation[fid]
            )

            # VCG payment = externality imposed on others
            externality = others_welfare_without - (total_with - own_welfare)
            payments[fid] = max(0, externality)

        # Step 3: Verify incentive compatibility
        # For each faculty, check that lying doesn't help
        for fid in faculty:
            # Try alternative (lying) strategies
            for lie_factor in [0.5, 1.5]:  # Under/over-report values
                lying_prefs = {
                    fid: [(s, v * lie_factor) for s, v in reported_preferences[fid]]
                }
                lying_prefs.update({
                    k: v for k, v in reported_preferences.items() if k != fid
                })

                lying_allocation = self._maximize_social_welfare(
                    faculty, shifts, lying_prefs
                )

                # Utility from lying
                lying_utility = sum(
                    true_value for shift, true_value in reported_preferences[fid]
                    if shift in lying_allocation[fid]
                ) - self._calculate_payment(fid, lying_allocation, lying_prefs)

                # Utility from truth-telling
                truthful_utility = sum(
                    value for shift, value in reported_preferences[fid]
                    if shift in allocation[fid]
                ) - payments[fid]

                # Verify truth-telling is better
                if lying_utility > truthful_utility + 0.01:  # Small epsilon for numerical stability
                    logger.warning(
                        f"Mechanism not fully incentive compatible for {fid}: "
                        f"lying utility {lying_utility} > truthful {truthful_utility}"
                    )

        return allocation

    def implement_monitoring_mechanism(
        self,
        faculty_id: UUID,
        reported_availability: list[date],
        monitoring_cost: float = 0.1
    ) -> tuple[bool, float]:
        """
        Implement costly monitoring to verify reported availability.

        Trade-off: Monitoring cost vs. value of catching misreporting.

        Returns:
            (should_monitor, expected_value_of_monitoring)
        """
        # Estimate probability faculty is misreporting
        historical_accuracy = self._estimate_reporting_accuracy(faculty_id)

        # Expected value of monitoring = prob(lying) * benefit(catching) - cost
        prob_lying = 1.0 - historical_accuracy

        # Benefit of catching = improved allocation efficiency
        benefit_if_lying = self._estimate_misallocation_cost(
            faculty_id,
            reported_availability
        )

        expected_value = prob_lying * benefit_if_lying - monitoring_cost

        should_monitor = expected_value > 0

        return (should_monitor, expected_value)

    def implement_screening_mechanism(
        self,
        applicant_faculty: list[UUID]
    ) -> dict[UUID, str]:
        """
        Screen faculty into types before assignment.

        Separate faculty into:
        - "High reliability" - rarely request swaps, accept most schedules
        - "Standard" - normal swap behavior
        - "High maintenance" - frequent swaps, many constraints

        Offer different contracts/scheduling rules to each type.
        """
        faculty_types = {}

        for fid in applicant_faculty:
            # Analyze historical behavior
            swap_history = self.db.query(SwapRecord).filter(
                or_(
                    SwapRecord.source_faculty_id == fid,
                    SwapRecord.target_faculty_id == fid
                )
            ).all()

            swap_rate = len(swap_history) / 365.0  # Swaps per year

            preferences = self.db.query(FacultyPreference).filter(
                FacultyPreference.faculty_id == fid
            ).first()

            constraint_count = 0
            if preferences:
                constraint_count += len(preferences.blocked_weeks or [])
                constraint_count += len(preferences.preferred_weeks or [])

            # Classify
            if swap_rate < 2 and constraint_count < 10:
                faculty_types[fid] = "high_reliability"
            elif swap_rate > 6 or constraint_count > 30:
                faculty_types[fid] = "high_maintenance"
            else:
                faculty_types[fid] = "standard"

        return faculty_types
```

### Integration with Existing System

```python
# Add incentive analysis to swap auto-matcher
class IncentiveAwareSwapMatcher(SwapAutoMatcher):
    """
    Extends swap matcher with principal-agent analysis.
    """

    def detect_strategic_behavior(
        self,
        faculty_id: UUID,
        time_window_days: int = 90
    ) -> dict[str, Any]:
        """
        Detect if faculty is strategically gaming the swap system.

        Signs of strategic behavior:
        - Requesting swaps immediately after receiving schedule
        - Consistent pattern of swapping same week types
        - High rate of "absorb" swaps that reduce workload
        """
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)

        swaps = self.db.query(SwapRecord).filter(
            SwapRecord.source_faculty_id == faculty_id,
            SwapRecord.requested_at >= cutoff
        ).all()

        if not swaps:
            return {"strategic_behavior_detected": False}

        # Analyze patterns
        immediate_requests = sum(
            1 for s in swaps
            if (s.requested_at.date() - s.source_week).days > 30
        )

        absorb_swaps = sum(
            1 for s in swaps
            if s.swap_type == SwapType.ABSORB
        )

        # Check if always swapping same week type
        week_numbers = [s.source_week.isocalendar()[1] for s in swaps]
        if week_numbers:
            most_common_week = statistics.mode(week_numbers)
            concentration = week_numbers.count(most_common_week) / len(week_numbers)
        else:
            concentration = 0.0

        # Scoring
        strategic_score = 0.0

        if immediate_requests / len(swaps) > 0.5:
            strategic_score += 0.3  # Often requests swaps right away

        if absorb_swaps / len(swaps) > 0.4:
            strategic_score += 0.3  # Many absorb swaps (reducing workload)

        if concentration > 0.7:
            strategic_score += 0.4  # Always swapping same week type

        detected = strategic_score > 0.5

        return {
            "strategic_behavior_detected": detected,
            "strategic_score": strategic_score,
            "immediate_request_rate": immediate_requests / len(swaps),
            "absorb_swap_rate": absorb_swaps / len(swaps),
            "week_concentration": concentration,
            "recommendation": (
                "Consider requiring advance notice for swap requests"
                if detected else "Behavior appears normal"
            )
        }
```

---

## 8. Practical Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

**Goal:** Implement core strategyproof mechanisms

1. **Random Serial Dictatorship for Initial Allocation**
   - File: `/backend/app/scheduling/rsd_allocator.py`
   - Integrates with existing `engine.py`
   - Use for yearly schedule initialization

2. **VCG-based Preference Elicitation**
   - Extend `FacultyPreferenceService`
   - Add `collect_preferences_vcg()` method
   - Store valuations in stigmergy trails

3. **Nash Equilibrium Analyzer**
   - File: `/backend/app/scheduling/nash_analyzer.py`
   - Add to resilience health checks
   - Monitor schedule stability

**Deliverables:**
- Strategyproof preference collection
- Nash stability metrics in Grafana
- Updated API routes for preference submission

### Phase 2: Auction Mechanisms (Weeks 5-8)

**Goal:** Implement priority-based allocation

1. **Priority Point System**
   - New model: `PriorityPointLedger`
   - Earn points: undesirable shifts, holidays, emergency coverage
   - Spend points: bid for preferred shifts

2. **Vickrey Auction for High-Demand Shifts**
   - Integrate with `SwapAutoMatcher`
   - Auction off contentious weeks (holidays, summer)
   - Logging and audit trail for fairness

3. **Double Auction for Swap Marketplace**
   - New service: `SwapDoubleAuction`
   - Continuous double auction (CDA) for live swap market
   - Real-time price discovery

**Deliverables:**
- Priority point UI in faculty portal
- Auction results dashboard
- Automated market clearing

### Phase 3: Cooperative Mechanisms (Weeks 9-12)

**Goal:** Fair workload distribution using Shapley values

1. **Shapley Value Calculator**
   - File: `/backend/app/scheduling/shapley.py`
   - Monte Carlo approximation for large faculty groups
   - Cache results for performance

2. **Workload Fairness Monitor**
   - Extend `ResilienceService`
   - Weekly fairness reports
   - Alert when Shapley deviation > threshold

3. **Coalition-Based Schedule Optimization**
   - Allow faculty to form "pods" for coordinated scheduling
   - Use Shapley value for pod workload allocation
   - Core stability verification

**Deliverables:**
- Fairness dashboard
- Shapley-based workload recommendations
- Pod scheduling feature

### Phase 4: Learning and Evolution (Weeks 13-16)

**Goal:** Adaptive strategies through evolutionary dynamics

1. **Evolutionary Strategy Learner**
   - Extend `StigmergicScheduler`
   - Add replicator dynamics to trail evolution
   - Learn which swap strategies succeed

2. **Preference Clustering Analysis**
   - Schelling-based cluster detection
   - Identify preference-based faculty groups
   - Recommend specialized schedules

3. **Strategic Behavior Detection**
   - Principal-agent analysis in `SwapAutoMatcher`
   - Flag suspicious patterns
   - Automated monitoring decisions

**Deliverables:**
- Adaptive recommendation engine
- Strategic behavior alerts
- Clustering visualization

### Phase 5: Integration and Testing (Weeks 17-20)

**Goal:** Full system integration and validation

1. **Comprehensive Testing**
   - Unit tests for all game-theoretic modules
   - Integration tests with existing swap system
   - Load tests for auction scaling

2. **Documentation and Training**
   - API documentation updates
   - Admin manual for game theory features
   - Faculty user guide

3. **Performance Optimization**
   - Profile Shapley calculation
   - Optimize auction algorithms
   - Cache equilibrium analyses

**Deliverables:**
- 95%+ test coverage for new modules
- Complete documentation
- Performance benchmarks

---

## 9. Integration with Existing Systems

### 9.1 Stigmergy + Game Theory Synergy

**Current System (Stigmergy):**
- Tracks preferences as pheromone trails
- Collective intelligence through emergent patterns
- Evaporation ensures recency

**Enhancement (Game Theory):**
- Use trail strengths as utility functions for Nash analysis
- Apply replicator dynamics to trail evolution
- Strategyproof mechanisms ensure trail honesty

```python
class UnifiedSchedulingEngine:
    """
    Combines stigmergy with game-theoretic mechanisms.
    """

    def __init__(self, db: Session):
        self.db = db
        self.stigmergy = StigmergicScheduler()
        self.nash_analyzer = NashEquilibriumAnalyzer()
        self.shapley_allocator = ShapleyWorkloadAllocator()
        self.evolutionary_learner = EvolutionarySwapLearner(db)

    def generate_schedule_with_guarantees(
        self,
        faculty: list[Person],
        shifts: list[Shift],
        year: int
    ) -> Schedule:
        """
        Generate schedule with game-theoretic guarantees:
        - Strategyproof preference elicitation
        - Nash equilibrium stability
        - Shapley-fair workload distribution
        - Evolutionary learning
        """
        # Step 1: Collect preferences (strategyproof)
        preferences = self._collect_strategyproof_preferences(faculty)

        # Step 2: Initial allocation using RSD
        initial_allocation = self._rsd_allocate(faculty, shifts, preferences)

        # Step 3: Refine toward Nash equilibrium
        schedule = self._refine_to_nash(initial_allocation, preferences)

        # Step 4: Verify Shapley fairness
        fairness = self.shapley_allocator.calculate_workload_fairness(schedule)

        if fairness["fairness_score"] < 0.7:
            # Adjust to improve fairness
            schedule = self._rebalance_for_fairness(schedule, fairness)

        # Step 5: Record in stigmergy for learning
        self._record_schedule_in_stigmergy(schedule)

        # Step 6: Update evolutionary strategies
        self.evolutionary_learner.update_strategy_frequencies()

        return schedule
```

### 9.2 Database Schema Extensions

```python
# New models needed

class PriorityPoint(Base):
    """Priority points for auction system."""
    __tablename__ = "priority_points"

    id = Column(UUID, primary_key=True, default=uuid4)
    faculty_id = Column(UUID, ForeignKey("persons.id"))
    balance = Column(Float, default=0.0)
    earned_total = Column(Float, default=0.0)
    spent_total = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

class PriorityPointTransaction(Base):
    """Audit trail for point transactions."""
    __tablename__ = "priority_point_transactions"

    id = Column(UUID, primary_key=True, default=uuid4)
    faculty_id = Column(UUID, ForeignKey("persons.id"))
    amount = Column(Float)  # Positive = earned, negative = spent
    reason = Column(String)
    shift_id = Column(UUID, ForeignKey("shifts.id"), nullable=True)
    auction_id = Column(UUID, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ShapleyValue(Base):
    """Cached Shapley values for faculty."""
    __tablename__ = "shapley_values"

    id = Column(UUID, primary_key=True, default=uuid4)
    faculty_id = Column(UUID, ForeignKey("persons.id"))
    schedule_id = Column(UUID, ForeignKey("schedules.id"))
    shapley_value = Column(Float)
    expected_workload = Column(Float)
    actual_workload = Column(Float)
    calculated_at = Column(DateTime, default=datetime.utcnow)

class StrategyPerformance(Base):
    """Track performance of swap strategies."""
    __tablename__ = "strategy_performance"

    id = Column(UUID, primary_key=True, default=uuid4)
    strategy_type = Column(String)  # e.g., "early_request", "mutual_preference"
    success_count = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    population_frequency = Column(Float, default=0.0)  # For replicator dynamics
    last_updated = Column(DateTime, default=datetime.utcnow)
```

### 9.3 API Routes

```python
# New routes in /backend/app/api/routes/game_theory.py

@router.post("/preferences/strategyproof")
async def collect_strategyproof_preferences(
    faculty_id: UUID,
    preferences: list[PreferenceRanking],
    db: AsyncSession = Depends(get_db)
) -> StrategyproofPreferenceResponse:
    """
    Collect faculty preferences using strategyproof mechanism.

    Guarantees: Truth-telling is dominant strategy.
    """
    pass

@router.post("/auctions/vickrey")
async def run_vickrey_auction(
    shift_id: UUID,
    bids: dict[UUID, float],
    db: AsyncSession = Depends(get_db)
) -> AuctionResult:
    """
    Run Vickrey auction for a contested shift.

    Returns: Winner and second-price payment.
    """
    pass

@router.get("/fairness/shapley/{schedule_id}")
async def get_shapley_fairness(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ShapleyFairnessReport:
    """
    Calculate Shapley-fair workload distribution.

    Returns: Shapley values and fairness metrics.
    """
    pass

@router.get("/stability/nash/{schedule_id}")
async def analyze_nash_stability(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> NashStabilityReport:
    """
    Analyze schedule for Nash equilibrium.

    Returns: Stability score and improvement opportunities.
    """
    pass

@router.get("/evolution/strategies")
async def get_evolutionary_strategies(
    db: AsyncSession = Depends(get_db)
) -> EvolutionaryStrategyReport:
    """
    Get current strategy frequencies from replicator dynamics.

    Returns: Which swap strategies are succeeding.
    """
    pass
```

---

## 10. References

### Academic Papers

1. **Nash Equilibrium in Scheduling**
   - [Mixed Strategy Nash Equilibrium for Scheduling Games on Batching-Machines](https://www.sciopen.com/article/10.26599/TST.2024.9010056) - Tsinghua Science and Technology, 2025
   - [Reinforcement Nash Equilibrium Solver](https://www.ijcai.org/proceedings/2024/30) - IJCAI 2024

2. **Mechanism Design**
   - [Theory of Mechanism Design](https://www.isid.ac.in/~dmishra/gmdoc/mdnotes.pdf) - Debasis Mishra, 2024
   - [Mechanism Design Game Theory](https://staff.science.uva.nl/u.endriss/teaching/game-theory/slides/gt10.pdf) - Ulle Endriss, 2025
   - Stanford: [Mechanism Theory](https://web.stanford.edu/~jacksonm/mechtheo.pdf) - Matthew O. Jackson

3. **Auction Theory**
   - [Combinatorial Diffusion Auction Design](https://arxiv.org/html/2410.22765) - arXiv 2024
   - [Vickrey-Clarke-Groves Mechanisms](https://web.stanford.edu/~jdlevin/Econ%20285/Vickrey%20Auction.pdf) - Jonathan Levin, Stanford
   - [Shake it up baby: scheduling with package auctions](https://www.researchgate.net/publication/221445065_Shake_it_up_baby_scheduling_with_package_auctions)

4. **Cooperative Game Theory**
   - [Non-Monetary Fair Scheduling — a Cooperative Game Theory Approach](https://duch.mimuw.edu.pl/~ps219737/wp-content/uploads/2023/03/shapleyScheduling-spaa.pdf) - Piotr Skowron
   - [Fair Share Is Not Enough: Measuring Fairness in Scheduling with Cooperative Game Theory](https://link.springer.com/chapter/10.1007/978-3-642-55195-6_4)
   - [Low-carbon collaborative scheduling method using cooperative game theory](https://www.sciencedirect.com/science/article/abs/pii/S0378779625006340) - ScienceDirect 2025

5. **Evolutionary Game Theory**
   - [The replicator equation and other game dynamics](https://www.pnas.org/doi/10.1073/pnas.1400823111) - PNAS
   - [Evolutionary Game Theory (Stanford Encyclopedia)](https://plato.stanford.edu/entries/game-evolutionary/)
   - [Replicator equation - Wikipedia](https://en.wikipedia.org/wiki/Replicator_equation)

6. **Matching Markets**
   - [Capacity Planning in Stable Matching with Truthful Preference Uncertainty](https://arxiv.org/abs/2506.22560) - arXiv 2025
   - [Stable Schedule Matching under Revealed Preference](https://link.springer.com/chapter/10.1007/978-3-662-05219-8_1)
   - [A Primer on Game Theory Behind NRMP](https://pmc.ncbi.nlm.nih.gov/articles/PMC8368266/)
   - [NRMP 2025 Main Residency Match Results](https://www.nrmp.org/about/news/2025/05/nrmp-releases-2025-main-residency-match-results-and-data-report-providing-in-depth-insight-into-the-largest-residency-match-in-history/)

7. **Fair Division**
   - [Strategy-Proofness, Envy-Freeness and Pareto Efficiency](https://link.springer.com/chapter/10.1007/978-3-030-29908-8_42)
   - [Recent Advances in Fair Resource Allocation](https://www.cs.toronto.edu/~nisarg/papers/Fair-Division-Tutorial.pdf) - Rupert Freeman & Nisarg Shah
   - [Obviously Strategyproof Mechanisms for Machine Scheduling](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESA.2019.46)

8. **Top Trading Cycles**
   - [Fast TTC Computation](https://arxiv.org/html/2403.15111v1) - arXiv March 2024
   - [Top Trading Cycles - Wikipedia](https://en.wikipedia.org/wiki/Top_trading_cycle)
   - [GitHub: Top-Trading-Cycle Implementation](https://github.com/MohammadYasinKarbasian/Top-Trading-Cycle)

9. **Kidney Exchange (Applied Mechanism Design)**
   - [New Algorithms for Hierarchical Optimization in Kidney Exchange](https://ideas.repec.org/a/inm/oropre/v72y2024i4p1654-1673.html) - Operations Research 2024
   - [Designing a kidney exchange program in Germany](https://link.springer.com/article/10.1007/s10100-024-00933-0) - CEJOR 2024
   - [Kidney Exchange: An Operations Perspective](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.2020.3954)

10. **Schelling Segregation Model**
    - [Understanding the social context of Schelling model](https://www.pnas.org/doi/10.1073/pnas.0708155105) - PNAS
    - [Aging effects in Schelling segregation model](https://www.nature.com/articles/s41598-022-23224-7) - Scientific Reports
    - [Schelling's Model - Wikipedia](https://en.wikipedia.org/wiki/Schelling's_model_of_segregation)

### Implementation Resources

- [Gale-Shapley Algorithm Implementations](https://github.com/lwcarani/matching-algorithms)
- [OR-Tools for Combinatorial Optimization](https://developers.google.com/optimization)
- [NetworkX for Graph Algorithms](https://networkx.org/)
- [SciPy for Optimization](https://scipy.org/)

---

## Conclusion

Game theory and mechanism design provide powerful tools for building fair, efficient, and strategyproof scheduling systems. By integrating these concepts with the existing stigmergy-based preference tracking, the residency scheduler can achieve:

1. **Incentive Compatibility** - Faculty truthfully report preferences
2. **Stability** - Schedules reach Nash equilibrium with minimal swapping
3. **Fairness** - Shapley values ensure equitable workload distribution
4. **Adaptability** - Evolutionary dynamics learn optimal strategies
5. **Efficiency** - Auctions allocate contested resources optimally

The proposed implementation roadmap provides a structured path to integrate these advanced concepts while maintaining compatibility with existing systems.

**Next Steps:**
1. Review and approve Phase 1 implementation plan
2. Create database migrations for new models
3. Begin development of strategyproof preference collection
4. Establish testing framework for game-theoretic properties

---

*End of Report*
