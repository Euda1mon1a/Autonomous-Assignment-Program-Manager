***REMOVED*** Game Theory Quick Reference for Scheduling
***REMOVED******REMOVED*** Implementation Cheat Sheet

**Last Updated:** 2025-12-20

This is a quick reference companion to the full [Game Theory Scheduling Research Report](./GAME_THEORY_SCHEDULING_RESEARCH.md).

---

***REMOVED******REMOVED*** 🎯 Core Concepts at a Glance

| Concept | When to Use | Key Benefit | Implementation Complexity |
|---------|-------------|-------------|---------------------------|
| **Nash Equilibrium** | Check schedule stability | Know when faculty are satisfied | ⭐⭐ Medium |
| **VCG Mechanism** | Elicit truthful preferences | Strategyproof preference collection | ⭐⭐⭐ High |
| **Vickrey Auction** | Allocate contested shifts | Fair, strategyproof allocation | ⭐⭐ Medium |
| **Shapley Value** | Fair workload distribution | Equitable burden sharing | ⭐⭐⭐ High |
| **Random Serial Dictatorship** | Initial schedule generation | Strategyproof, efficient, simple | ⭐ Easy |
| **Replicator Dynamics** | Learn successful strategies | Adaptive system evolution | ⭐⭐ Medium |
| **Double Auction** | Decentralized swap market | Market-driven price discovery | ⭐⭐⭐ High |
| **Schelling Model** | Detect preference clustering | Identify faculty groups | ⭐⭐ Medium |

---

***REMOVED******REMOVED*** 💡 Quick Decision Tree

***REMOVED******REMOVED******REMOVED*** "How do I choose which mechanism to use?"

```
START: What problem are you solving?
│
├─ "I need to collect faculty preferences"
│  ├─ Trust faculty to be honest? → Use simple ranking
│  └─ Worried about strategic lying? → Use **VCG Mechanism** or **RSD**
│
├─ "I need to allocate a contested shift (e.g., Christmas)"
│  ├─ Want fairness + strategyproofness? → **Vickrey Auction**
│  └─ Want to consider seniority/points? → **Priority Point Auction**
│
├─ "I need to check if schedule is stable"
│  └─ **Nash Equilibrium Analysis** - check if anyone wants to swap
│
├─ "I need to ensure fair workload distribution"
│  └─ **Shapley Value** - allocate based on marginal contributions
│
├─ "I want the system to learn over time"
│  └─ **Evolutionary Game Theory** - use replicator dynamics
│
└─ "I want to detect faculty preference groups"
   └─ **Schelling Segregation Model** - clustering analysis
```

---

***REMOVED******REMOVED*** 🚀 Implementation Snippets

***REMOVED******REMOVED******REMOVED*** 1. Check Nash Stability (Simple Version)

```python
def is_schedule_stable_simple(schedule: Schedule) -> tuple[bool, list[str]]:
    """Quick check if anyone wants to swap."""
    improvements = []

    for faculty in schedule.faculty:
        ***REMOVED*** Check all possible single swaps
        for my_assignment in faculty.assignments:
            for other_faculty in schedule.faculty:
                for their_assignment in other_faculty.assignments:
                    ***REMOVED*** Would both be happier after swap?
                    if (self.would_prefer_swap(faculty, my_assignment, their_assignment) and
                        self.would_prefer_swap(other_faculty, their_assignment, my_assignment)):
                        improvements.append(
                            f"{faculty.name} ↔ {other_faculty.name}: "
                            f"{my_assignment.week} ↔ {their_assignment.week}"
                        )

    return (len(improvements) == 0, improvements)
```

***REMOVED******REMOVED******REMOVED*** 2. Random Serial Dictatorship (Strategyproof Allocation)

```python
def allocate_shifts_rsd(
    faculty: list[UUID],
    shifts: list[Shift],
    preferences: dict[UUID, list[Shift]]  ***REMOVED*** Ordered by preference
) -> dict[UUID, Shift]:
    """Strategyproof allocation using RSD."""

    ***REMOVED*** Randomize faculty order
    random_order = random.sample(faculty, len(faculty))

    allocation = {}
    available = shifts.copy()

    for fid in random_order:
        ***REMOVED*** Pick most preferred available shift
        for shift in preferences[fid]:
            if shift in available:
                allocation[fid] = shift
                available.remove(shift)
                break

    return allocation
```

***REMOVED******REMOVED******REMOVED*** 3. Vickrey Auction (Second-Price)

```python
def run_vickrey_auction(
    shift: Shift,
    bids: dict[UUID, float]  ***REMOVED*** faculty_id → bid amount
) -> tuple[UUID, float]:
    """
    Allocate shift using Vickrey (second-price) auction.

    Returns: (winner_id, payment_amount)

    Key property: Bidding true value is optimal (strategyproof).
    """
    sorted_bids = sorted(bids.items(), key=lambda x: -x[1])

    winner = sorted_bids[0][0]
    payment = sorted_bids[1][1] if len(sorted_bids) > 1 else 0.0

    return (winner, payment)
```

***REMOVED******REMOVED******REMOVED*** 4. Shapley Value (Monte Carlo Approximation)

```python
def calculate_shapley_monte_carlo(
    faculty: list[UUID],
    value_function: Callable[[set[UUID]], float],
    num_samples: int = 1000
) -> dict[UUID, float]:
    """
    Approximate Shapley values using sampling.

    Args:
        value_function: Maps coalition → total value
        num_samples: More samples = better accuracy

    Returns:
        Shapley value for each faculty member
    """
    shapley = {fid: 0.0 for fid in faculty}

    for _ in range(num_samples):
        ***REMOVED*** Random permutation
        order = random.sample(faculty, len(faculty))

        coalition = set()
        for fid in order:
            ***REMOVED*** Marginal contribution
            before = value_function(coalition)
            coalition.add(fid)
            after = value_function(coalition)

            shapley[fid] += (after - before)

    ***REMOVED*** Average over samples
    for fid in shapley:
        shapley[fid] /= num_samples

    return shapley
```

***REMOVED******REMOVED******REMOVED*** 5. Replicator Dynamics (Strategy Evolution)

```python
def update_strategies_replicator(
    current_frequencies: dict[str, float],
    fitness: dict[str, float],
    dt: float = 0.1
) -> dict[str, float]:
    """
    Update strategy frequencies using replicator dynamics.

    dx/dt = x * (fitness(x) - avg_fitness)

    Args:
        current_frequencies: Current strategy proportions
        fitness: Success rate for each strategy
        dt: Time step

    Returns:
        New strategy frequencies
    """
    avg_fitness = sum(
        current_frequencies[s] * fitness[s]
        for s in current_frequencies
    )

    new_frequencies = {}
    for strategy in current_frequencies:
        x = current_frequencies[strategy]
        f = fitness[strategy]

        ***REMOVED*** dx/dt = x(f - avg_f)
        new_x = x + x * (f - avg_fitness) * dt
        new_frequencies[strategy] = max(0.0, new_x)

    ***REMOVED*** Normalize to sum to 1
    total = sum(new_frequencies.values())
    if total > 0:
        for s in new_frequencies:
            new_frequencies[s] /= total

    return new_frequencies
```

---

***REMOVED******REMOVED*** 📊 When to Use Each Mechanism

***REMOVED******REMOVED******REMOVED*** Strategyproof Preference Collection

**Use when:** Faculty might lie about preferences to game the system

**Mechanisms:**
1. **Random Serial Dictatorship** - Easiest, works for simple allocation
2. **VCG Mechanism** - Most general, handles complex scenarios
3. **Top Trading Cycles** - Good for indivisible items (shifts)

**Implementation Priority:** ⭐⭐⭐ HIGH

**Existing Integration Point:** `FacultyPreferenceService.collect_preferences()`

---

***REMOVED******REMOVED******REMOVED*** Fair Workload Distribution

**Use when:** You want to ensure no one is overloaded or underutilized

**Mechanisms:**
1. **Shapley Value** - Fair based on marginal contribution
2. **Core Stability** - Ensure no coalition wants to defect
3. **Envy-Free Allocation** - No one prefers another's bundle

**Implementation Priority:** ⭐⭐⭐ HIGH

**Existing Integration Point:** `ResilienceService.calculate_utilization()`

---

***REMOVED******REMOVED******REMOVED*** Contested Resource Allocation

**Use when:** Multiple faculty want the same desirable shift

**Mechanisms:**
1. **Vickrey Auction** - Strategyproof, efficient
2. **Combinatorial Auction** - For bundles (e.g., consecutive shifts)
3. **Priority Points** - Seniority-based allocation

**Implementation Priority:** ⭐⭐ MEDIUM

**Existing Integration Point:** `SwapAutoMatcher.suggest_optimal_matches()`

---

***REMOVED******REMOVED******REMOVED*** Stability Analysis

**Use when:** You want to know if schedule will need many swaps

**Mechanisms:**
1. **Nash Equilibrium** - Check if anyone wants to deviate
2. **Core** - Check if coalitions want to defect
3. **Price of Stability** - How much efficiency loss for stability

**Implementation Priority:** ⭐⭐ MEDIUM

**Existing Integration Point:** `ResilienceService.get_tier3_metrics()`

---

***REMOVED******REMOVED******REMOVED*** Adaptive Learning

**Use when:** System should improve over time based on outcomes

**Mechanisms:**
1. **Replicator Dynamics** - Successful strategies spread
2. **Reinforcement Learning** - Learn optimal policies
3. **Bayesian Updating** - Update beliefs from data

**Implementation Priority:** ⭐ LOW (Nice to have)

**Existing Integration Point:** `StigmergicScheduler` (already has trail evolution)

---

***REMOVED******REMOVED*** 🔧 Integration Points with Existing System

***REMOVED******REMOVED******REMOVED*** Stigmergy ↔ Game Theory

| Stigmergy Feature | Game Theory Enhancement |
|-------------------|------------------------|
| Preference trails | → Use as utility functions for Nash analysis |
| Trail strength | → Input for Shapley value calculation |
| Evaporation | → Combine with replicator dynamics |
| Swap affinity trails | → Input for double auction pricing |
| Collective preferences | → Detect via Schelling clustering |

***REMOVED******REMOVED******REMOVED*** Swap Auto-Matcher ↔ Mechanism Design

| Current Feature | Game Theory Enhancement |
|----------------|------------------------|
| Compatibility scoring | → Add Nash stability check |
| Match ranking | → Use VCG payments for priority |
| Historical success | → Replicator dynamics for strategy evolution |
| Workload balance | → Enforce Shapley fairness constraints |
| Priority levels | → Auction-based prioritization |

***REMOVED******REMOVED******REMOVED*** Resilience ↔ Cooperative Game Theory

| Resilience Metric | Game Theory Enhancement |
|-------------------|------------------------|
| Utilization (80% rule) | → Shapley-fair workload targets |
| N-1/N-2 contingency | → Coalition stability (core) |
| Coverage capacity | → Value function for Shapley calculation |
| Tier health | → Nash distance metric |

---

***REMOVED******REMOVED*** 📈 Performance Considerations

***REMOVED******REMOVED******REMOVED*** Computational Complexity

| Algorithm | Exact Complexity | Approximation | When to Approximate |
|-----------|------------------|---------------|---------------------|
| **Shapley Value** | O(n! · 2^n) | Monte Carlo: O(k·n) | n > 10 faculty |
| **Nash Equilibrium** | PPAD-complete | Best-response: O(n³) | Always use approx |
| **VCG Allocation** | NP-hard (general) | Greedy: O(n²) | n > 20 items |
| **Combinatorial Auction** | NP-hard | ILP solver | n < 50 items |
| **Core Stability** | NP-hard | Check subset: O(2^k) | Check only k=2,3 |

***REMOVED******REMOVED******REMOVED*** Caching Strategies

```python
***REMOVED*** Cache Shapley values (expensive to compute)
@lru_cache(maxsize=128)
def get_shapley_values(schedule_id: UUID) -> dict[UUID, float]:
    ***REMOVED*** Recompute only if schedule changed
    pass

***REMOVED*** Cache Nash stability (changes infrequently)
@lru_cache(maxsize=64)
def get_nash_distance(schedule_id: UUID) -> float:
    ***REMOVED*** Invalidate on swap
    pass

***REMOVED*** Don't cache auction results (real-time)
def run_auction(shift_id: UUID, bids: dict) -> AuctionResult:
    ***REMOVED*** Always compute fresh
    pass
```

---

***REMOVED******REMOVED*** 🎓 Key Theorems to Remember

***REMOVED******REMOVED******REMOVED*** Revelation Principle
> Any outcome achievable by a complex mechanism can be achieved by a truthful direct-revelation mechanism.

**Practical Meaning:** Design systems where telling the truth is optimal.

***REMOVED******REMOVED******REMOVED*** Gibbard-Satterthwaite Theorem
> For 3+ alternatives, only dictatorships are strategyproof and deterministic.

**Practical Meaning:** Need randomization (RSD) or restricted domains for strategyproofness.

***REMOVED******REMOVED******REMOVED*** Myerson-Satterthwaite Theorem
> In bilateral trade, you cannot have efficiency + budget balance + individual rationality + incentive compatibility all at once.

**Practical Meaning:** Swap markets need trade-offs (e.g., sacrifice efficiency for incentives).

***REMOVED******REMOVED******REMOVED*** Shapley Uniqueness
> The Shapley value is the unique payoff division satisfying efficiency, symmetry, linearity, and null player property.

**Practical Meaning:** Shapley is the "natural" fair division method.

---

***REMOVED******REMOVED*** 🐛 Common Pitfalls

***REMOVED******REMOVED******REMOVED*** Pitfall 1: Assuming Truthful Reporting
**Problem:** Faculty strategically misreport preferences
**Solution:** Use strategyproof mechanisms (VCG, RSD, Vickrey)

***REMOVED******REMOVED******REMOVED*** Pitfall 2: Ignoring Strategic Behavior
**Problem:** Sophisticated faculty game the system
**Solution:** Principal-agent analysis, monitoring, screening

***REMOVED******REMOVED******REMOVED*** Pitfall 3: Computational Intractability
**Problem:** Exact Shapley/Nash calculation takes too long
**Solution:** Use approximations (Monte Carlo, best-response)

***REMOVED******REMOVED******REMOVED*** Pitfall 4: Fairness ≠ Efficiency
**Problem:** Fair allocation may not maximize total utility
**Solution:** Choose explicit trade-off (e.g., "Shapley-fair within 5% of optimal")

***REMOVED******REMOVED******REMOVED*** Pitfall 5: Stability ≠ Optimality
**Problem:** Nash equilibrium may be suboptimal
**Solution:** Use price of stability/anarchy metrics, guide toward better equilibria

---

***REMOVED******REMOVED*** 📚 Further Reading

***REMOVED******REMOVED******REMOVED*** Beginner-Friendly
- [Game Theory 101 (YouTube)](https://www.youtube.com/user/gametheory101)
- [Algorithmic Game Theory (Nisan et al.)](http://www.cambridge.org/us/academic/subjects/computer-science/algorithmics-complexity-computer-algebra-and-computational-g/algorithmic-game-theory)

***REMOVED******REMOVED******REMOVED*** Advanced
- [Mechanism Design and Approximation (Jason Hartline)](http://jasonhartline.com/MDnA/)
- [Twenty Lectures on Algorithmic Game Theory (Tim Roughgarden)](https://theory.stanford.edu/~tim/papers/cacm.pdf)

***REMOVED******REMOVED******REMOVED*** Applied
- [Kidney Exchange Literature](https://pubsonline.informs.org/doi/abs/10.1287/mnsc.2020.3954)
- [Residency Matching (NRMP)](https://www.nrmp.org/)
- [School Choice Mechanism Design](https://economics.mit.edu/sites/default/files/publications/The%20Design%20of%20School%20Choice%20Systems%20in%20NYC.pdf)

---

***REMOVED******REMOVED*** 🤝 Contributing

Found a better algorithm? Have implementation experience? Please contribute!

**Contact:** See main [GAME_THEORY_SCHEDULING_RESEARCH.md](./GAME_THEORY_SCHEDULING_RESEARCH.md)

**Implementation Status:** Track progress in [TODO_TRACKER.md](../planning/TODO_TRACKER.md)

---

*Last Updated: 2025-12-20*
