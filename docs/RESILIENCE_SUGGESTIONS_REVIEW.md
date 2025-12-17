# Resilience Framework Suggestions Review

**Date:** December 2024
**Context:** External review of the Resilience Framework implementation suggested several libraries and improvements.

---

## Summary Table

| Suggestion | Library | Assessment | Action |
|------------|---------|------------|--------|
| A. State Machine | `transitions` | Low value | **Discard** |
| B. Signal/Events | `blinker`/`PyDispatcher` | Marginal value | **Discard** |
| C. Simulation | `SimPy` | High value | **Explore for Tier 4** |
| D. Dashboard | `Streamlit` | Valid but out-of-scope | **Skip** (frontend) |
| E. Skill Checks | N/A (code change) | High value | **Implement** |

---

## Detailed Analysis

### A. `transitions` Library for State Machine - DISCARDED

**Original Suggestion:**
> Your `blast_radius.py` manages transitions (Green → Yellow → Red) with manual `if/elif` logic. Use `transitions` to define states and valid transitions declaratively.

**Analysis:**
The current `ZoneStatus` implementation is **not a true state machine**. It's a **status calculation** based on capacity:

```python
# blast_radius.py:209-222
def calculate_status(self) -> ZoneStatus:
    """Calculate current zone status."""
    available = self.get_total_available()

    if available < self.minimum_coverage * 0.5:
        return ZoneStatus.BLACK
    elif available < self.minimum_coverage:
        return ZoneStatus.RED
    # ... etc
```

**Why `transitions` doesn't fit:**
1. **No guarded transitions** - Status is purely derived from capacity, not transition rules
2. **No transition callbacks needed** - The `_update_zone_status` method handles changes simply via list-based observer
3. **Deterministic output** - Given the same capacity, you always get the same status
4. **No state persistence** - Status is recalculated on every check

**When `transitions` would help:**
- If transitions had prerequisites (e.g., "can only move to GREEN after 24h in YELLOW")
- If certain transitions were forbidden (e.g., "cannot jump from BLACK to GREEN")
- If transitions triggered complex side effects needing rollback

**Verdict:** The current implementation is appropriate. Adding `transitions` would introduce:
- New dependency
- Learning curve for contributors
- Abstraction layer for simple logic

---

### B. `blinker`/`PyDispatcher` for Event Signals - DISCARDED

**Original Suggestion:**
> The code uses `self._on_zone_status_change.append(handler)`. This is a basic Observer pattern that scales poorly.

**Analysis:**
The current implementation in `BlastRadiusManager`:

```python
# blast_radius.py:297-299
self._on_zone_status_change: list[Callable] = []
self._on_containment_change: list[Callable] = []
```

**Current Scale:**
- ~2-3 event types per component
- ~5-10 handlers expected per type
- Synchronous execution (no async needs)
- Single process (no cross-service messaging)

**What `blinker` provides:**
- Named signals: `zone_changed = blinker.signal('zone-changed')`
- Weak references to handlers (prevents memory leaks)
- Sender filtering
- Thread-safe dispatch

**Why not needed now:**
1. Current handler count is manageable
2. No memory leak risk (handlers are service-level, not request-level)
3. No need for sender filtering
4. No threading requirements

**When to reconsider:**
- If moving to microservices (use proper message queue instead)
- If handler count exceeds ~50 per signal
- If async event processing becomes necessary

**Verdict:** Premature optimization. Keep simple list-based approach.

---

### C. `SimPy` for Monte Carlo Simulations - EXPLORE FURTHER

**Original Suggestion:**
> Use SimPy for discrete-event simulation. You can model "1 year of scheduling" in 1 second, injecting random failures to see if the "Blast Radius" logic actually holds up.

**Analysis:**
This suggestion has **high value** for the documented Tier 4 research goals:

From `RESILIENCE_FRAMEWORK.md`:
> **Tier 4: Research & Future Consideration**
> **4.1 Ecology: Minimum Viable Population and Extinction Vortex**
> - What's the minimum faculty count to maintain a viable training program?
> - At what point do losses become self-reinforcing?

**SimPy Capabilities:**
1. **Discrete-event simulation** - Model individual events (sick calls, PCS moves) over time
2. **Resource modeling** - Faculty as constrained resources
3. **Process-based** - Easy to model "a faculty member's career lifecycle"
4. **Fast execution** - Simulate years in seconds

**Proposed Use Cases:**

#### Use Case 1: N-2 Contingency Validation
```python
# Pseudocode for SimPy simulation
def simulate_n2_scenario(env, faculty_pool, schedule):
    """Simulate random loss of 2 faculty members and measure recovery."""
    # Remove 2 random faculty
    lost = random.sample(faculty_pool, 2)

    # Run blast radius containment
    for zone in zones:
        if not zone.is_self_sufficient():
            # Attempt borrowing
            yield env.timeout(BORROWING_DELAY)
            attempt_borrowing(zone)

    # Measure outcomes
    return {
        'coverage_maintained': calculate_coverage(),
        'zones_failed': count_failed_zones(),
        'time_to_stabilize': env.now
    }
```

#### Use Case 2: Extinction Vortex Detection
```python
def simulate_burnout_cascade(env, faculty_pool, burnout_threshold):
    """Model positive feedback loop: overwork → departures → more overwork"""
    while len(faculty_pool) > 0:
        # Calculate workload per faculty
        workload_per_person = TOTAL_DEMAND / len(faculty_pool)

        # Burnout probability increases with workload
        burnout_prob = min(1.0, (workload_per_person / burnout_threshold) ** 2)

        # Check each faculty for departure
        for faculty in faculty_pool[:]:
            if random.random() < burnout_prob:
                faculty_pool.remove(faculty)
                yield env.process(replacement_delay())

        yield env.timeout(1)  # One time unit
```

**Implementation Approach:**
1. Create `app/resilience/simulation/` module
2. Define simulation scenarios matching Tier 4 research questions
3. Integrate with existing resilience components for validation
4. Output statistical reports on failure probabilities

**Recommended Next Steps:**
1. Add `simpy` to optional dependencies: `pip install simpy`
2. Create proof-of-concept simulation for N-2 validation
3. Validate that current blast radius logic prevents cascade failures
4. Document findings for program leadership

---

### D. `Streamlit` Dashboard - SKIP (Frontend Concern)

**Original Suggestion:**
> Build a "Resilience Cockpit" in 50 lines of Python to visualize ZoneHealthReport data.

**Analysis:**
Valid suggestion, but **outside the scope of current backend work**. The backend already provides comprehensive APIs:

- `ResilienceService.get_comprehensive_report()`
- `ResilienceService.get_tier2_status()`
- `ResilienceService.get_tier3_status()`

These return structured data suitable for any frontend visualization.

**If pursued later:**
Streamlit would be appropriate for internal admin dashboards during development/testing but would not replace the production Next.js frontend.

---

### E. Skill Check for Zone Self-Sufficiency - IMPLEMENT

**Original Suggestion:**
> The current `blast_radius.py` treats faculty largely as "counts". Ensure your zone includes a check for *critical skills* (e.g., `minimum_ob_supervisors >= 1`), not just total bodies.

**Analysis:**
This is a **valid and important gap** in the current implementation.

**Current Code (blast_radius.py:201-203):**
```python
def is_self_sufficient(self) -> bool:
    """Check if zone can operate without borrowing."""
    return self.get_total_available() >= self.minimum_coverage
```

**The "Warm Body Fallacy":**
If a zone has 3 available faculty but none can perform a critical service (e.g., OB supervision, ICU procedures), the zone is effectively RED even though the count is GREEN.

**Existing Related Code:**
The `hub_analysis.py` module already tracks this:
```python
# hub_analysis.py:92
unique_services: int = 0  # Services only this person can cover
```

But this information is **not integrated** into zone self-sufficiency checks.

**Proposed Solution:**

#### Step 1: Add Critical Skills to Zone Definition
```python
@dataclass
class SchedulingZone:
    # ... existing fields ...

    # NEW: Critical skills that must be covered
    critical_skills: dict[str, int] = field(default_factory=dict)
    # Example: {"ob_supervision": 1, "icu_procedures": 2}
```

#### Step 2: Add Skills to Faculty Assignment
```python
@dataclass
class ZoneFacultyAssignment:
    # ... existing fields ...

    # NEW: Skills this faculty member provides
    skills: list[str] = field(default_factory=list)
```

#### Step 3: Enhance Self-Sufficiency Check
```python
def is_self_sufficient(self) -> bool:
    """Check if zone can operate without borrowing."""
    # Check total count
    if self.get_total_available() < self.minimum_coverage:
        return False

    # Check critical skills coverage
    for skill, min_required in self.critical_skills.items():
        available_with_skill = sum(
            1 for f in self._get_all_available_faculty()
            if skill in f.skills
        )
        if available_with_skill < min_required:
            return False

    return True
```

#### Step 4: Integrate with Hub Analysis
The `HubAnalyzer.generate_cross_training_recommendations()` output should inform which skills need distribution across zones.

**Implementation Priority:** HIGH
This addresses a real safety gap where the system could report "GREEN" status while lacking critical coverage capabilities.

---

## Implementation Recommendations

### Immediate (Next Sprint)
1. **Implement skill checks in zone self-sufficiency** (Section E)
   - Add `critical_skills` to `SchedulingZone`
   - Add `skills` to `ZoneFacultyAssignment`
   - Enhance `is_self_sufficient()` logic
   - Add tests for skill-based status calculation

### Short-term (1-2 Months)
2. **Prototype SimPy simulation** (Section C)
   - Add `simpy` as optional dependency
   - Create `app/resilience/simulation/` module
   - Implement N-2 contingency validation scenario
   - Document simulation methodology

### Deferred
3. **Libraries (Sections A, B):** No action needed
4. **Dashboard (Section D):** Defer to frontend team if needed

---

## References

- [SimPy Documentation](https://simpy.readthedocs.io/)
- [RESILIENCE_FRAMEWORK.md](./RESILIENCE_FRAMEWORK.md) - Original framework documentation
- [blast_radius.py](../backend/app/resilience/blast_radius.py) - Current implementation
- [hub_analysis.py](../backend/app/resilience/hub_analysis.py) - Hub vulnerability analysis
