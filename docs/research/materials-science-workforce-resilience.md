# Materials Science Metaphors for Workforce Resilience
## Research Report: Exotic Materials Concepts Applied to Medical Residency Scheduling

**Date:** 2025-12-20
**Status:** Research & Implementation Recommendations
**Integration:** Builds on existing `FatigueTracker`, `HomeostasisMonitor`, and `CognitiveLoadManager`

---

## Executive Summary

This report explores seven materials science and mechanical engineering concepts and their applications to workforce fatigue, recovery, and stress accumulation in medical residency scheduling. Each concept provides a metaphorical framework for understanding human performance limits, predicting failure modes, and designing recovery protocols.

**Key Finding:** Just as materials fail through predictable mechanisms (fatigue, creep, fracture), medical staff experience analogous degradation patterns that can be quantified, monitored, and mitigated through materials-inspired resilience frameworks.

---

## 1. Stress-Strain Curves: Elastic, Plastic, and Failure Regions

### Core Materials Science Principle

The [stress-strain curve](https://en.wikipedia.org/wiki/Stress–strain_curve) characterizes material behavior under loading:

- **Elastic Region (Hooke's Law):** Stress ∝ Strain, fully recoverable deformation
  - Slope = Young's Modulus (material stiffness)
  - Atomic bonds stretch but don't break

- **Yield Point:** Transition from elastic to plastic deformation
  - Typically defined as 0.2% permanent strain offset
  - Marks onset of irreversible damage

- **Plastic Region:** Permanent deformation after load removal
  - Strain hardening occurs (discussed in Section 5)
  - Dislocations multiply and tangle

- **Ultimate Tensile Strength (UTS):** Maximum stress before failure
  - Peak of stress-strain curve

- **Fracture Point:** Complete material failure
  - Brittle materials: sudden failure at UTS
  - Ductile materials: necking, then rupture

**Key Insight:** Materials have *safe operating zones* (elastic region) and *damage accumulation zones* (plastic region) before catastrophic failure.

### Application to Workforce Fatigue

Medical residents exhibit analogous response regions:

1. **Elastic Workload Zone (0-60 hours/week):**
   - Full recovery with normal sleep/rest
   - Performance returns to baseline after time off
   - No cumulative damage
   - Corresponds to ACGME's 80-hour rule providing safety margin

2. **Yield Point (~70-75 hours/week):**
   - Onset of incomplete recovery
   - Sleep debt begins accumulating
   - Cognitive performance degrades measurably
   - Mood changes, irritability emerge
   - *First "micro-cracks" appear*

3. **Plastic Deformation Zone (75-90 hours/week):**
   - Permanent effects even after rest
   - Chronic stress biomarkers elevate
   - Decision quality degrades
   - Increased error rates
   - Requires extended recovery (not just weekend off)

4. **Ultimate Strength (~95+ hours/week):**
   - Maximum sustainable load (temporarily)
   - High risk of acute failure events
   - Medical errors spike
   - Mental health crises

5. **Fracture (Burnout/Breakdown):**
   - Complete inability to continue
   - Medical leave required
   - PTSD, depression, substance abuse
   - Career-ending in severe cases

### Detection Methods (Early Warning of "Yield Point" Crossing)

**Physiological Markers:**
- HRV (Heart Rate Variability) reduction
- Cortisol dysregulation (flattened diurnal curve)
- Sleep efficiency below 85%
- Persistent fatigue despite rest

**Behavioral Markers:**
- Decision time increases (cognitive slowing)
- Increased sick calls/shift cancellations
- Social withdrawal
- Emotional volatility

**Performance Markers:**
- Error rate increases >20% above baseline
- Documentation delays
- Procedure time increases
- Patient complaints

**System Metrics (Already Tracked):**
```python
# From fatigue_tracker.py
fatigue_score = (
    consecutive_days * 10 +
    night_shifts * 15 +
    weekend_days * 12 +
    days_since_off * 8 +
    total_hours * 1.5
)

# PROPOSED: Add "Yield Detection"
if fatigue_score > ELASTIC_LIMIT and recovery_incomplete:
    alert_yield_point_exceeded()
```

### Implementation Ideas

**1. Elastic Limit Enforcement:**
```python
# backend/app/resilience/stress_strain.py (NEW)

from dataclasses import dataclass
from enum import Enum

class DeformationRegion(str, Enum):
    ELASTIC = "elastic"           # Fully recoverable
    YIELD = "yield"               # Transition zone
    PLASTIC = "plastic"           # Permanent damage accumulating
    NECKING = "necking"           # Approaching failure
    FRACTURE = "fracture"         # Complete breakdown

@dataclass
class StressStrainMetrics:
    """Track faculty position on stress-strain curve."""

    person_id: str
    current_load: float           # Current hours/week
    elastic_limit: float = 60.0   # Person-specific safe zone
    yield_point: float = 70.0     # Onset of damage
    ultimate_strength: float = 85.0  # Maximum sustainable

    # Recovery tracking
    time_in_plastic_region: int = 0  # Days in plastic zone
    recovery_debt: float = 0.0       # Hours of recovery needed

    def get_deformation_region(self) -> DeformationRegion:
        """Determine current region on stress-strain curve."""
        if self.current_load <= self.elastic_limit:
            return DeformationRegion.ELASTIC
        elif self.current_load <= self.yield_point:
            return DeformationRegion.YIELD
        elif self.current_load <= self.ultimate_strength:
            return DeformationRegion.PLASTIC
        elif self.current_load <= self.ultimate_strength * 1.1:
            return DeformationRegion.NECKING
        else:
            return DeformationRegion.FRACTURE

    def calculate_recovery_debt(self) -> float:
        """
        Calculate recovery time needed based on plastic deformation.

        Plastic deformation requires exponentially more recovery time.
        """
        if self.current_load <= self.elastic_limit:
            return 0.0  # Full recovery with normal rest

        excess_load = self.current_load - self.elastic_limit

        # Exponential recovery debt in plastic region
        recovery_multiplier = 1 + (excess_load / self.elastic_limit) ** 2
        return excess_load * recovery_multiplier * self.time_in_plastic_region
```

**2. Integration with Existing FatigueTracker:**
```python
# Enhance backend/app/validators/fatigue_tracker.py

def calculate_stress_strain_position(self, person_id: str, target_date: date):
    """
    Map fatigue score to stress-strain curve position.

    Returns deformation region and recovery recommendations.
    """
    fatigue_data = self.calculate_fatigue_score(person_id, target_date)
    fatigue_score = fatigue_data.get("fatigue_score", 0)

    # Map fatigue score to stress-strain regions
    # FATIGUE_THRESHOLD_MODERATE = 50 (existing)
    # FATIGUE_THRESHOLD_HIGH = 70 (existing)

    if fatigue_score < 50:
        region = "ELASTIC"
        recovery = "Normal rest sufficient"
    elif fatigue_score < 70:
        region = "YIELD"
        recovery = "Extended rest recommended (48h minimum)"
    elif fatigue_score < 90:
        region = "PLASTIC"
        recovery = "Mandatory recovery period (72h+), damage accumulating"
    else:
        region = "CRITICAL"
        recovery = "IMMEDIATE INTERVENTION - risk of burnout/breakdown"

    return {
        "deformation_region": region,
        "recovery_recommendation": recovery,
        "is_safe_zone": region == "ELASTIC",
        "permanent_damage_risk": region in ("PLASTIC", "CRITICAL"),
    }
```

**3. Scheduling Constraint:**
```python
# Prevent scheduling in plastic region for >3 consecutive days
MAX_DAYS_IN_PLASTIC_REGION = 3

if person.days_in_plastic_region >= MAX_DAYS_IN_PLASTIC_REGION:
    # Force into elastic region (light duty or time off)
    schedule_recovery_block(person)
```

---

## 2. Fatigue Failure: Repeated Cyclic Loading

### Core Materials Science Principle

[Fatigue failure](https://sdcverifier.com/structural-engineering-101/fatigue-strength-and-limit-understanding-materials-specific-data/) occurs from repeated cyclic loading well below the material's yield strength:

- **S-N Curves (Wöhler Curves):** Stress amplitude vs. cycles to failure
  - High stress, low cycles: Low Cycle Fatigue (LCF)
  - Low stress, high cycles: High Cycle Fatigue (HCF)

- **Endurance Limit (Fatigue Limit):**
  - Stress level below which infinite cycles can be sustained
  - Ferrous metals (steel, titanium): true endurance limit exists
  - Non-ferrous metals (aluminum): no true limit, eventual failure

- **Mechanisms:**
  - Persistent slip bands form along crystal planes
  - Surface intrusions/extrusions create stress concentrators
  - Microcracks nucleate and grow
  - Sudden catastrophic failure when crack reaches critical size

**Key Insight:** Repeated moderate stress causes failure even when each individual stress cycle is "safe." Cumulative damage from cycles, not just peak stress.

### Application to Workforce Fatigue

**Call Cycles as Fatigue Loading:**

Weekend call every 4 weeks: 13 cycles/year
- Resident stress: 85% yield strength each cycle
- Material analogy: 13 cycles at 85% UTS
- S-N curve predicts failure in 10^4-10^5 cycles (years of service)

Weekend call every 2 weeks: 26 cycles/year
- Same stress amplitude (85%)
- Doubling cycle frequency halves fatigue life
- Predicts burnout in half the time

**Holiday Coverage Cycles:**
- Holidays are high-stress events (95% of UTS)
- Each holiday cycle consumes more "fatigue budget"
- 3 consecutive holidays may exceed fatigue limit

**Night Float Rotations:**
- Circadian disruption = cyclic stress
- Each night shift = 1 fatigue cycle
- Recovery incomplete between cycles → cumulative damage

### Detection Methods

**1. Cycle Counting:**
```python
# Track high-stress cycles (analogous to rainflow counting in materials)
high_stress_cycles = {
    "weekend_calls": count,
    "night_shifts": count,
    "holidays_worked": count,
    "double_shifts": count,
    "cross_coverage_events": count,
}

# Each type has different "damage per cycle"
damage_per_weekend_call = 5.0
damage_per_night_shift = 2.0
damage_per_holiday = 8.0

cumulative_fatigue_damage = sum(
    cycles * damage_factor
    for cycles, damage_factor in high_stress_cycles.items()
)
```

**2. Palmgren-Miner Rule (Linear Damage Accumulation):**
```
D = Σ(n_i / N_i)

Where:
- n_i = actual cycles at stress level i
- N_i = cycles to failure at stress level i (from S-N curve)
- D = 1.0 → failure predicted

If D > 0.8, approaching fatigue failure
```

**3. Micro-Crack Detection (Behavioral Changes):**
- First missed documentation deadline (crack initiation)
- First emotional outburst (crack propagation begins)
- First sick call from stress (crack becoming visible)
- Errors in familiar tasks (critical crack length approaching)

### Implementation Ideas

**1. Fatigue Life Tracker:**
```python
# backend/app/resilience/fatigue_life.py (NEW)

@dataclass
class FatigueLifeMetrics:
    """Track cumulative fatigue damage using materials science approach."""

    person_id: str
    academic_year_start: date

    # Cycle counts by stress amplitude
    high_stress_cycles: dict[str, int] = field(default_factory=dict)
    # Examples: "weekend_call", "holiday", "night_shift", "double_shift"

    # S-N curve parameters (calibrated to burnout data)
    endurance_limit: float = 50.0  # Below this, no fatigue damage
    fatigue_strength_coefficient: float = 100.0
    fatigue_strength_exponent: float = -0.12  # Material-specific

    # Cumulative damage
    miner_sum: float = 0.0  # Palmgren-Miner damage accumulation

    def cycles_to_failure(self, stress_amplitude: float) -> float:
        """
        Calculate cycles to failure for given stress amplitude (S-N curve).

        N = (S / σ_f')^(1/b)

        Where:
        - N = cycles to failure
        - S = stress amplitude
        - σ_f' = fatigue strength coefficient
        - b = fatigue strength exponent
        """
        if stress_amplitude <= self.endurance_limit:
            return float('inf')  # Below endurance limit

        N = (stress_amplitude / self.fatigue_strength_coefficient) ** (1 / self.fatigue_strength_exponent)
        return N

    def add_stress_cycle(self, cycle_type: str, stress_amplitude: float):
        """
        Record a stress cycle and update cumulative damage.

        Args:
            cycle_type: "weekend_call", "night_shift", etc.
            stress_amplitude: Equivalent stress (0-100 scale)
        """
        # Update cycle count
        self.high_stress_cycles[cycle_type] = self.high_stress_cycles.get(cycle_type, 0) + 1

        # Calculate damage contribution (Palmgren-Miner)
        N_f = self.cycles_to_failure(stress_amplitude)
        if N_f != float('inf'):
            damage_increment = 1.0 / N_f
            self.miner_sum += damage_increment

    def get_remaining_life_fraction(self) -> float:
        """
        Get remaining fatigue life as fraction (0.0 = failed, 1.0 = pristine).

        Returns:
            Remaining life fraction
        """
        return max(0.0, 1.0 - self.miner_sum)

    def get_fatigue_status(self) -> dict:
        """Get comprehensive fatigue life status."""
        remaining_life = self.get_remaining_life_fraction()

        if self.miner_sum >= 1.0:
            status = "FAILURE_PREDICTED"
            recommendation = "IMMEDIATE: Remove from schedule, mandatory recovery/counseling"
        elif self.miner_sum >= 0.8:
            status = "CRITICAL"
            recommendation = "Urgent: Reduce high-stress cycles, increase recovery time"
        elif self.miner_sum >= 0.6:
            status = "WARNING"
            recommendation = "Monitor closely, limit weekend/holiday coverage"
        elif self.miner_sum >= 0.4:
            status = "MODERATE"
            recommendation = "Normal monitoring, maintain rotation balance"
        else:
            status = "HEALTHY"
            recommendation = "Continue current schedule"

        return {
            "person_id": self.person_id,
            "miner_damage_sum": self.miner_sum,
            "remaining_life_fraction": remaining_life,
            "status": status,
            "recommendation": recommendation,
            "high_stress_cycle_counts": self.high_stress_cycles,
            "estimated_cycles_to_burnout": 1.0 / (self.miner_sum / len(self.high_stress_cycles)) if self.miner_sum > 0 else float('inf'),
        }
```

**2. Integration with Existing System:**
```python
# Enhance backend/app/resilience/homeostasis.py

def calculate_allostatic_load(self, entity_id: UUID, ...):
    """Existing method - enhance with fatigue life tracking."""

    # Existing allostatic load calculation
    metrics = AllostasisMetrics(...)
    metrics.calculate()

    # NEW: Add fatigue life analysis
    fatigue_life = self.fatigue_life_tracker.get_status(entity_id)

    if fatigue_life["miner_damage_sum"] >= 0.8:
        # Critical fatigue damage - escalate alert
        self.trigger_fatigue_failure_alert(entity_id, fatigue_life)

    return metrics
```

**3. Scheduling Constraint - Cycle Spacing:**
```python
# Enforce minimum recovery between high-stress cycles

MIN_RECOVERY_DAYS_BETWEEN_WEEKEND_CALLS = 21  # 3 weeks minimum
MIN_RECOVERY_DAYS_BETWEEN_HOLIDAYS = 60       # 2 months minimum

def validate_stress_cycle_spacing(assignments: list[Assignment]) -> bool:
    """
    Ensure adequate recovery between high-stress cycles.

    Analogous to ensuring sufficient time between load cycles
    for crack healing/arrest.
    """
    weekend_calls = [a for a in assignments if a.is_weekend_call]

    for i in range(len(weekend_calls) - 1):
        days_between = (weekend_calls[i+1].date - weekend_calls[i].date).days
        if days_between < MIN_RECOVERY_DAYS_BETWEEN_WEEKEND_CALLS:
            return False  # Cycles too closely spaced

    return True
```

---

## 3. Creep: Slow Deformation Under Sustained Load

### Core Materials Science Principle

[Creep](https://tactun.com/creep-testing-predicting-long-term-material-behavior/) is time-dependent deformation under constant stress, particularly at elevated temperatures:

**Three Stages of Creep:**

1. **Primary Creep (Transient):**
   - Initial rapid deformation rate
   - Deformation rate decreases with time
   - Strain hardening dominates

2. **Secondary Creep (Steady-State):**
   - Constant, minimum deformation rate
   - Balance between strain hardening and recovery
   - Longest phase (can be years)
   - Most predictable for engineering design

3. **Tertiary Creep (Accelerating):**
   - Rapid increase in deformation rate
   - Necking, void formation, microcrack coalescence
   - Leads to rupture failure
   - Often sudden and catastrophic

**Key Characteristics:**
- Occurs at stresses well below yield strength
- Time-dependent (weeks, months, years)
- Temperature-accelerated (Arrhenius relationship)
- Irreversible deformation

### Application to Workforce Fatigue

**Sustained Moderate Workload as Creep Loading:**

Unlike acute overload (yield/plastic deformation), sustained moderate overwork causes slow degradation:

**Primary Creep Phase (Months 1-3):**
- Initial adaptation to workload
- Resident feels they're "toughening up"
- Minor sleep debt accumulates
- Performance remains acceptable
- *Deceptive period - damage not apparent*

**Secondary Creep Phase (Months 4-18):**
- Steady degradation rate
- Chronic fatigue becomes normalized
- Cognitive performance subtly degrades
- Error rate slowly increases
- May continue for years if undetected
- *Silent damage accumulation*

**Tertiary Creep Phase (Final weeks/months):**
- Sudden acceleration of decline
- Cascading failures
- Inability to compensate
- Medical errors cluster
- Emotional breakdown
- *Catastrophic failure imminent*

**Real-World Example:**
```
Resident assigned 72 hours/week (just below 80-hour limit)
- Stress = 90% of yield strength
- Safe for short term (1-2 weeks)
- But sustained for 6 months → creep failure
- Burnout occurs despite "compliance" with hour limits
```

### Detection Methods

**1. Creep Rate Monitoring:**

Track performance degradation over time (slope of decline):

```python
# Performance metrics over time
performance_over_time = [
    (week_1, 95%),  # Baseline
    (week_4, 93%),  # Primary creep
    (week_8, 91%),  # Entering secondary creep
    (week_16, 88%), # Secondary creep
    (week_20, 82%), # Accelerating tertiary creep
    (week_22, 68%), # Imminent failure
]

# Calculate creep rate (slope)
creep_rate = Δ_performance / Δ_time

if creep_rate < -0.5% per week:
    alert_secondary_creep()  # Steady degradation

if creep_rate < -2.0% per week:
    alert_tertiary_creep()  # Accelerating failure
```

**2. Time-to-Rupture Prediction:**

Materials science uses Larson-Miller parameter for creep rupture:
```
LMP = T(C + log t_r)

Where:
- T = temperature (analogy: chronic stress level)
- t_r = time to rupture
- C = material constant (~20 for steels)
```

Workforce analogy:
```python
def predict_time_to_burnout(
    chronic_stress_level: float,  # 0-100
    person_resilience: float,      # Material constant
    time_under_stress: int,        # days
) -> int:
    """
    Predict time to burnout using creep rupture model.

    Returns: estimated days until burnout
    """
    # Higher stress → exponentially shorter time to failure
    # Larson-Miller-inspired equation

    C = person_resilience  # Person-specific constant (varies 15-25)
    T = chronic_stress_level  # Equivalent to temperature

    # Solve for time to rupture
    log_t_r = (LMP_critical / T) - C
    t_r = 10 ** log_t_r

    return int(t_r - time_under_stress)  # Days remaining
```

**3. Micro-Structural Inspection (Longitudinal Assessment):**

Periodic "creep testing" via:
- Monthly cognitive assessments (reaction time, working memory)
- Mood tracking (PHQ-9, GAD-7 scores trending)
- Sleep quality metrics (quantitative)
- Procedural skill assessment (simulator performance)

### Implementation Ideas

**1. Creep Damage Accumulator:**

```python
# backend/app/resilience/creep.py (NEW)

from dataclasses import dataclass
from datetime import date, timedelta
import numpy as np

@dataclass
class CreepMetrics:
    """Track time-dependent degradation under sustained load."""

    person_id: str
    load_start_date: date
    sustained_load_level: float  # 0-100 (% of capacity)

    # Creep phases
    primary_creep_duration: int = 90   # days (adaptive phase)
    secondary_creep_rate: float = 0.0  # %/week degradation
    tertiary_creep_threshold: float = 0.15  # When acceleration begins

    # Performance tracking
    baseline_performance: float = 100.0
    current_performance: float = 100.0
    performance_history: list[tuple[date, float]] = field(default_factory=list)

    # Rupture prediction
    time_to_rupture: int = None  # days (None = not in tertiary)

    def record_performance(self, test_date: date, performance: float):
        """Record performance measurement for creep rate calculation."""
        self.performance_history.append((test_date, performance))
        self.current_performance = performance

        # Calculate creep rate if we have enough data
        if len(self.performance_history) >= 4:
            self._calculate_creep_rate()
            self._detect_tertiary_creep()

    def _calculate_creep_rate(self):
        """
        Calculate creep rate (performance degradation per week).

        Uses linear regression on recent performance history.
        """
        if len(self.performance_history) < 4:
            return

        # Last 8 weeks of data
        recent = self.performance_history[-8:]

        dates = [(d - self.load_start_date).days for d, _ in recent]
        perfs = [p for _, p in recent]

        # Linear regression
        slope, intercept = np.polyfit(dates, perfs, 1)

        # Convert to %/week
        self.secondary_creep_rate = slope * 7  # days to weeks

    def _detect_tertiary_creep(self):
        """Detect transition to tertiary (accelerating) creep."""
        if len(self.performance_history) < 6:
            return

        # Compare recent rate vs. earlier rate
        mid_point = len(self.performance_history) // 2

        early_data = self.performance_history[:mid_point]
        recent_data = self.performance_history[mid_point:]

        # Calculate slopes
        early_slope = self._calc_slope(early_data)
        recent_slope = self._calc_slope(recent_data)

        # Tertiary creep if recent slope is significantly worse
        acceleration = abs(recent_slope - early_slope)

        if acceleration > self.tertiary_creep_threshold:
            # Entering tertiary creep - predict rupture
            self._predict_rupture()

    def _calc_slope(self, data: list[tuple[date, float]]) -> float:
        """Calculate slope of performance data."""
        dates = [(d - self.load_start_date).days for d, _ in data]
        perfs = [p for _, p in data]
        slope, _ = np.polyfit(dates, perfs, 1)
        return slope * 7  # Convert to weekly rate

    def _predict_rupture(self):
        """Predict time to burnout (creep rupture)."""
        if self.secondary_creep_rate >= 0:
            return  # No degradation, no rupture

        # Current performance degradation rate
        # Predict when performance hits critical threshold (60%)
        CRITICAL_PERFORMANCE = 60.0

        performance_deficit = self.current_performance - CRITICAL_PERFORMANCE
        weeks_to_rupture = performance_deficit / abs(self.secondary_creep_rate)

        self.time_to_rupture = int(weeks_to_rupture * 7)  # Convert to days

    def get_creep_phase(self) -> str:
        """Determine current creep phase."""
        days_under_load = (date.today() - self.load_start_date).days

        if days_under_load < self.primary_creep_duration:
            return "PRIMARY"  # Initial adaptation

        if self.time_to_rupture is not None:
            if self.time_to_rupture < 30:
                return "TERTIARY_CRITICAL"
            return "TERTIARY"  # Accelerating failure

        return "SECONDARY"  # Steady-state creep

    def get_creep_status(self) -> dict:
        """Get comprehensive creep status."""
        phase = self.get_creep_phase()

        recommendations = {
            "PRIMARY": "Monitor closely - adaptation period",
            "SECONDARY": "Stable degradation - maintain monitoring, consider load reduction",
            "TERTIARY": "WARNING: Accelerating degradation detected - reduce load immediately",
            "TERTIARY_CRITICAL": "CRITICAL: Burnout imminent - remove from schedule",
        }

        return {
            "person_id": self.person_id,
            "creep_phase": phase,
            "days_under_sustained_load": (date.today() - self.load_start_date).days,
            "sustained_load_level": self.sustained_load_level,
            "current_performance": self.current_performance,
            "creep_rate_percent_per_week": self.secondary_creep_rate,
            "time_to_rupture_days": self.time_to_rupture,
            "recommendation": recommendations[phase],
            "requires_immediate_intervention": phase in ("TERTIARY", "TERTIARY_CRITICAL"),
        }
```

**2. Integration with Scheduling:**

```python
# backend/app/scheduling/validator.py

def validate_sustained_load(person: Person, assignments: list[Assignment]) -> bool:
    """
    Validate that sustained load doesn't cause creep failure.

    Prevents multi-month overloading even if within weekly limits.
    """
    # Calculate average load over past 12 weeks
    weeks_12_avg = calculate_rolling_average(person, assignments, weeks=12)

    # Check for sustained overload
    CREEP_THRESHOLD = 70.0  # % of capacity
    SUSTAINED_DURATION_LIMIT = 16  # weeks

    if weeks_12_avg > CREEP_THRESHOLD:
        weeks_overloaded = count_consecutive_weeks_above(weeks_12_avg, CREEP_THRESHOLD)

        if weeks_overloaded >= SUSTAINED_DURATION_LIMIT:
            # Creep failure risk - reject schedule
            return False

    return True
```

**3. Creep Recovery Protocol:**

```python
# When creep detected, prescribe recovery based on phase

def prescribe_creep_recovery(creep_status: dict) -> dict:
    """
    Determine recovery protocol based on creep phase.

    Returns: recovery plan with duration and load limits
    """
    phase = creep_status["creep_phase"]

    if phase == "PRIMARY":
        return {
            "action": "MONITOR",
            "load_reduction": "0%",
            "duration_weeks": 0,
        }

    elif phase == "SECONDARY":
        return {
            "action": "REDUCE_LOAD",
            "load_reduction": "20%",
            "duration_weeks": 4,
            "note": "Reduce to elastic zone, allow partial recovery",
        }

    elif phase == "TERTIARY":
        return {
            "action": "MAJOR_REDUCTION",
            "load_reduction": "40%",
            "duration_weeks": 8,
            "note": "Significant creep damage accumulated, extended recovery needed",
        }

    else:  # TERTIARY_CRITICAL
        return {
            "action": "IMMEDIATE_REMOVAL",
            "load_reduction": "100%",
            "duration_weeks": 12,
            "note": "CRITICAL: Medical leave recommended, burnout imminent",
            "requires_counseling": True,
            "requires_medical_evaluation": True,
        }
```

---

## 4. Crystal Lattice Defects: Dislocations, Vacancies, and Their Effects

### Core Materials Science Principle

[Crystal lattice defects](https://www.numberanalytics.com/blog/ultimate-guide-crystal-defects-materials-science) are imperfections in crystalline structure that profoundly affect material properties:

**Point Defects (Vacancies):**
- Missing atoms in lattice positions
- Created by thermal fluctuations, irradiation, or quenching
- Facilitate diffusion (atoms can "hop" through vacancies)
- Increase electrical resistivity
- Density: ~10^-4 to 10^-3 vacancies per atom at high temperature

**Line Defects (Dislocations):**
- Extra half-plane of atoms (edge dislocation)
- Helical atomic arrangement (screw dislocation)
- Enable plastic deformation through slip
- Dislocation density:
  - Annealed crystal: 10^8 dislocations/m²
  - Cold worked: 10^14-10^16 dislocations/m²
  - Destroyed material: >10^17 dislocations/m²

**Key Properties:**
- Dislocations interact and tangle → strengthening (work hardening)
- Dislocations pile up at barriers → stress concentration
- High dislocation density → brittle behavior
- Vacancies enable diffusion and phase transformations

### Application to Workforce Fatigue

**Organizational "Crystal Structure":**

Ideal organization = perfect crystal:
- Every role filled (no vacancies)
- Clear reporting structure
- Smooth operational flow
- Predictable stress distribution

**Vacancies (Staffing Gaps):**
- Unfilled positions
- Faculty on leave/deployment
- Open positions due to resignations
- *Each vacancy increases strain on remaining staff*

**Dislocations (Workflow Disruptions):**
- Schedule swaps
- Last-minute coverage changes
- Procedure cancellations/rescheduling
- Emergency cross-coverage
- Communication breakdowns
- *Dislocations allow system to absorb stress but accumulate damage*

**Dislocation Density → Brittleness Analogy:**

Low dislocation density (stable schedule):
- Few swaps, minimal changes
- High ductility (can absorb disruptions)
- Staff can adapt to minor changes

High dislocation density (chaotic schedule):
- Constant swaps, daily changes
- System becomes brittle
- Single additional disruption causes cascade failure
- *"Dislocation hardening" → schedule is rigid, can't absorb more*

### Detection Methods

**1. Vacancy Tracking:**
```python
# Count staffing vacancies
vacancies = {
    "unfilled_positions": count_open_positions(),
    "faculty_on_leave": count_leave_of_absence(),
    "temporary_unavailability": count_sick_calls(),
    "pending_departures": count_resignation_notices(),
}

vacancy_density = sum(vacancies.values()) / total_positions

# Critical vacancy density threshold
if vacancy_density > 0.15:  # >15% vacancy rate
    alert_critical_vacancy_density()
```

**2. Dislocation Density (Schedule Changes):**
```python
# Count schedule disruptions (dislocations)
dislocations = {
    "swaps_this_month": count_approved_swaps(),
    "emergency_coverage": count_emergency_calls(),
    "last_minute_changes": count_changes_within_48h(),
    "cross_coverage_events": count_cross_service_coverage(),
}

dislocation_density = sum(dislocations.values()) / total_scheduled_blocks

# Dislocation density thresholds
if dislocation_density > 0.10:  # 10% of blocks affected
    status = "WORK_HARDENED"  # Schedule brittle, can't absorb more
elif dislocation_density > 0.05:
    status = "MODERATE"
else:
    status = "STABLE"
```

**3. Dislocation Pile-Up Detection:**

When dislocations concentrate at a single person/service:
```python
# Detect localized stress concentration
person_dislocation_counts = {
    person: count_swaps_and_changes(person)
    for person in faculty
}

# Identify pile-ups
threshold = mean(person_dislocation_counts) + 2*std_dev
pile_ups = [
    person for person, count in person_dislocation_counts.items()
    if count > threshold
]

# Pile-ups indicate stress concentration → crack initiation risk
```

### Implementation Ideas

**1. Defect Density Monitor:**

```python
# backend/app/resilience/lattice_defects.py (NEW)

from dataclasses import dataclass
from datetime import date, timedelta

@dataclass
class LatticeDefectMetrics:
    """Track organizational 'crystal defects' affecting resilience."""

    service_id: str
    calculation_date: date

    # Vacancies (missing atoms)
    total_positions: int
    filled_positions: int
    unfilled_positions: int
    on_leave: int
    unavailable_temporarily: int

    # Dislocations (schedule disruptions)
    total_scheduled_blocks: int
    swaps_count: int
    emergency_coverage_count: int
    last_minute_changes: int
    cross_coverage_count: int

    # Derived metrics
    vacancy_density: float = 0.0        # Fraction of positions vacant
    dislocation_density: float = 0.0    # Fraction of blocks disrupted

    def calculate_defect_densities(self):
        """Calculate vacancy and dislocation densities."""
        # Vacancy density
        total_vacancies = (
            self.unfilled_positions +
            self.on_leave +
            self.unavailable_temporarily
        )
        self.vacancy_density = total_vacancies / self.total_positions if self.total_positions > 0 else 0.0

        # Dislocation density
        total_dislocations = (
            self.swaps_count +
            self.emergency_coverage_count +
            self.last_minute_changes +
            self.cross_coverage_count
        )
        self.dislocation_density = total_dislocations / self.total_scheduled_blocks if self.total_scheduled_blocks > 0 else 0.0

    def get_material_state(self) -> str:
        """
        Classify organizational state using materials science analogy.

        Returns: material state classification
        """
        # Annealed (pristine): Low defects, ductile
        if self.vacancy_density < 0.05 and self.dislocation_density < 0.03:
            return "ANNEALED"  # Ideal state

        # Cold worked (moderate): Moderate defects, work-hardened
        if self.vacancy_density < 0.15 and self.dislocation_density < 0.10:
            return "COLD_WORKED"  # Functional but stressed

        # Heavily cold worked: High dislocations, brittle
        if self.dislocation_density >= 0.10:
            return "HEAVILY_COLD_WORKED"  # Brittle, can't absorb more

        # High vacancy: Structurally compromised
        if self.vacancy_density >= 0.15:
            return "STRUCTURALLY_DEFECTIVE"  # Critical staffing shortage

        return "DAMAGED"  # Both metrics elevated

    def predict_fracture_risk(self) -> dict:
        """
        Predict risk of catastrophic failure using defect density.

        High vacancy + high dislocation = crack propagation risk
        """
        state = self.get_material_state()

        # Combined risk score (multiplicative interaction)
        risk_score = self.vacancy_density * self.dislocation_density * 100

        risk_levels = {
            "ANNEALED": ("LOW", "Stable organization, can absorb disruptions"),
            "COLD_WORKED": ("MODERATE", "Work-hardened, limit additional changes"),
            "HEAVILY_COLD_WORKED": ("HIGH", "Brittle schedule, single disruption may cascade"),
            "STRUCTURALLY_DEFECTIVE": ("CRITICAL", "Critical understaffing, system vulnerable"),
            "DAMAGED": ("CRITICAL", "Multiple failure modes, immediate intervention needed"),
        }

        risk_level, description = risk_levels.get(state, ("UNKNOWN", ""))

        return {
            "service_id": self.service_id,
            "material_state": state,
            "vacancy_density": round(self.vacancy_density, 3),
            "dislocation_density": round(self.dislocation_density, 3),
            "fracture_risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "description": description,
            "recommendations": self._get_recommendations(state),
        }

    def _get_recommendations(self, state: str) -> list[str]:
        """Get recommendations based on material state."""
        recs = []

        if state in ("HEAVILY_COLD_WORKED", "DAMAGED"):
            recs.append("URGENT: Freeze non-essential schedule changes")
            recs.append("Implement strict change control (emergency only)")

        if state in ("STRUCTURALLY_DEFECTIVE", "DAMAGED"):
            recs.append("CRITICAL: Recruit temporary coverage immediately")
            recs.append("Consider service reduction until staffing restored")

        if self.vacancy_density > 0.10:
            recs.append(f"Fill {int(self.vacancy_density * 100)}% staffing gap priority")

        if self.dislocation_density > 0.08:
            recs.append("High schedule chaos - review swap policies, reduce emergency coverage")

        if not recs:
            recs.append("Continue monitoring defect densities")

        return recs
```

**2. Dislocation Pile-Up Detector:**

```python
def detect_dislocation_pileups(
    faculty: list[Person],
    assignments: list[Assignment],
    lookback_days: int = 30
) -> list[dict]:
    """
    Detect faculty with concentrated schedule disruptions (dislocation pile-ups).

    Pile-ups indicate stress concentration → micro-crack initiation sites.
    """
    cutoff_date = date.today() - timedelta(days=lookback_days)

    # Count disruptions per person
    person_disruptions = {}

    for person in faculty:
        disruptions = count_schedule_disruptions(person, cutoff_date)
        person_disruptions[person.id] = {
            "person": person,
            "disruption_count": disruptions,
        }

    # Statistical outlier detection (pile-ups)
    counts = [d["disruption_count"] for d in person_disruptions.values()]
    mean_disruptions = statistics.mean(counts)
    std_disruptions = statistics.stdev(counts) if len(counts) > 1 else 0

    threshold = mean_disruptions + 2 * std_disruptions  # 2σ outlier

    # Identify pile-ups
    pile_ups = []
    for person_id, data in person_disruptions.items():
        if data["disruption_count"] > threshold:
            pile_ups.append({
                "person_id": person_id,
                "person_name": data["person"].name,
                "disruption_count": data["disruption_count"],
                "excess_over_mean": data["disruption_count"] - mean_disruptions,
                "severity": "CRITICAL" if data["disruption_count"] > mean_disruptions + 3*std_disruptions else "HIGH",
                "recommendation": "Dislocation pile-up detected - protect from further changes, prioritize for recovery",
            })

    return pile_ups
```

**3. Annealing Protocol (Restore Crystal Structure):**

When defect density is high, "anneal" the organization:

```python
def anneal_organization(service_id: str) -> dict:
    """
    Restore organizational structure through 'annealing'.

    Materials science annealing:
    - Heat to recrystallization temperature
    - Hold for time
    - Slow cool
    - Result: dislocations eliminated, vacancies reduced

    Organizational annealing:
    - Freeze schedule changes (2-4 weeks)
    - Fill critical vacancies
    - Cancel non-essential activities
    - Stabilize before resuming normal operations
    """
    defect_metrics = calculate_lattice_defects(service_id)

    if defect_metrics["material_state"] in ("HEAVILY_COLD_WORKED", "DAMAGED"):
        return {
            "action": "ANNEAL",
            "duration_weeks": 4,
            "protocol": [
                "FREEZE: No schedule changes except emergencies (2 weeks)",
                "RECRUIT: Fill all vacant positions or get temp coverage",
                "CANCEL: Defer non-essential activities",
                "STABILIZE: Lock schedule for final 2 weeks",
                "VERIFY: Re-measure defect densities before releasing freeze",
            ],
            "expected_outcome": "Reduce dislocation density to <0.05, vacancy density to <0.10",
        }

    return {"action": "NO_ANNEALING_NEEDED"}
```

---

## 5. Work Hardening / Strain Hardening: Strengthening Through Deformation

### Core Materials Science Principle

[Work hardening](https://metalzenith.com/blogs/steel-mechanical-physical-properties-terms/work-hardening-strengthening-steel-through-deformation-mechanics) (strain hardening) strengthens metals through plastic deformation:

**Mechanism:**
- Plastic deformation generates new dislocations
- Dislocation density increases from 10^8 to 10^16 m^-2
- Dislocations tangle and impede each other's motion
- Yield strength increases: Δσ = αGb√ρ
  - α = constant (0.3-0.5)
  - G = shear modulus
  - b = Burgers vector
  - ρ = dislocation density

**Effects:**
- **Strength increases:** Higher yield and ultimate strength
- **Ductility decreases:** Material becomes brittle
- **Hardness increases:** Resistance to indentation
- **Formability decreases:** Harder to continue deforming

**Trade-off:** Strength vs. ductility - you gain one at the expense of the other.

**Reversibility:** Annealing (heat treatment) reverses work hardening by reducing dislocation density.

### Application to Workforce Fatigue

**Psychological Work Hardening (Positive):**

Short-term stress exposure can strengthen resilience:

**Beneficial Work Hardening:**
- Controlled stress exposure (e.g., intern year challenges)
- "What doesn't kill me makes me stronger"
- Develops coping mechanisms
- Builds confidence from overcoming challenges
- Stress inoculation effect

**Optimal Work Hardening:**
- Brief overload periods (1-2 weeks)
- Followed by recovery
- Gradually increasing difficulty
- Supportive environment
- Skill-building focus

**Detrimental Over-Hardening:**

Excessive or prolonged work hardening becomes pathological:

- **Emotional Brittleness:** Reduced empathy, compassion fatigue
- **Cognitive Rigidity:** "By-the-book" thinking, loss of creativity
- **Defensive Hardening:** Cynicism, detachment, depersonalization
- **Reduced Adaptability:** Can't handle novelty or ambiguity
- **Burnout Precursor:** Hardened exterior, damaged interior

**Trade-Off (Parallel to Materials):**
- Strength ↑, Ductility ↓
- Resilience to routine stress ↑, Adaptability to novel stress ↓
- Short-term performance ↑, Long-term sustainability ↓

### Detection Methods

**1. Work Hardening vs. Over-Hardening:**

Beneficial work hardening indicators:
- Increased confidence after challenges
- Improved efficiency (faster task completion)
- Better stress coping (lower reactivity)
- Maintained empathy and engagement
- Positive self-talk ("I can handle this")

Detrimental over-hardening indicators:
- Emotional flattening (reduced affect)
- Cynicism, sarcasm increase
- Depersonalization of patients
- Rule-rigidity (can't adapt)
- Loss of professional ideals ("just a job")
- Defensive medicine practices

**2. Ductility Loss Detection:**

Psychological ductility = ability to adapt to changing conditions

Tests:
- Response to unexpected changes (flexibility)
- Novel problem-solving ability
- Empathy assessments (decreases with over-hardening)
- Burnout inventory (MBI depersonalization subscale)

**3. Dislocation Density Proxy:**

Materials: High dislocation density = work hardened
Psychology: High chronic stressor exposure = work hardened

Track cumulative stressor exposure:
```python
cumulative_stressors = (
    high_acuity_patients_count * 2.0 +
    difficult_conversations_count * 3.0 +
    adverse_events_involved * 5.0 +
    ethical_dilemmas_count * 4.0 +
    interpersonal_conflicts * 3.0
)

# High cumulative stressors → work hardening
if cumulative_stressors > threshold:
    assess_for_overhardening()
```

### Implementation Ideas

**1. Work Hardening Tracker:**

```python
# backend/app/resilience/work_hardening.py (NEW)

from dataclasses import dataclass
from datetime import date
from enum import Enum

class HardeningState(str, Enum):
    UNHARDENED = "unhardened"           # Baseline, untested
    OPTIMALLY_HARDENED = "optimal"      # Strengthened, ductile retained
    OVER_HARDENED = "over_hardened"     # Brittle, damaged
    ANNEALED = "annealed"               # Recovered from over-hardening

@dataclass
class WorkHardeningMetrics:
    """Track psychological work hardening (resilience vs. brittleness)."""

    person_id: str
    baseline_date: date

    # Stressor exposure (analogous to dislocation density)
    cumulative_stress_exposure: float = 0.0
    acute_stressors_30d: int = 0
    chronic_stressor_duration_days: int = 0

    # Strength indicators (positive work hardening)
    stress_coping_score: float = 50.0    # 0-100, baseline 50
    task_efficiency: float = 1.0         # Relative to baseline
    confidence_score: float = 50.0       # Self-efficacy

    # Ductility indicators (negative when over-hardened)
    empathy_score: float = 80.0          # 0-100, baseline 80
    adaptability_score: float = 70.0     # Novel problem-solving
    emotional_range: float = 100.0       # % of baseline affect range

    # Burnout markers (MBI)
    depersonalization_score: float = 0.0  # 0-30, higher = worse
    cynicism_score: float = 0.0          # 0-100

    def calculate_hardening_state(self) -> HardeningState:
        """
        Determine if work hardening is beneficial or detrimental.

        Optimal hardening:
        - Increased strength (coping, efficiency)
        - Maintained ductility (empathy, adaptability)

        Over-hardening:
        - Increased strength BUT
        - Lost ductility (brittle, cynical, rigid)
        """
        # Check for strength gains
        strength_increased = (
            self.stress_coping_score > 60 or
            self.task_efficiency > 1.1 or
            self.confidence_score > 60
        )

        # Check for ductility loss
        ductility_lost = (
            self.empathy_score < 60 or
            self.adaptability_score < 50 or
            self.emotional_range < 70 or
            self.depersonalization_score > 10 or
            self.cynicism_score > 40
        )

        if strength_increased and not ductility_lost:
            return HardeningState.OPTIMALLY_HARDENED

        if ductility_lost:
            return HardeningState.OVER_HARDENED

        if self.cumulative_stress_exposure < 10:
            return HardeningState.UNHARDENED

        return HardeningState.ANNEALED  # Recovered state

    def get_work_hardening_status(self) -> dict:
        """Get comprehensive work hardening assessment."""
        state = self.calculate_hardening_state()

        recommendations = {
            HardeningState.UNHARDENED: "Continue gradual stress exposure for skill building",
            HardeningState.OPTIMALLY_HARDENED: "Excellent resilience, maintain current trajectory",
            HardeningState.OVER_HARDENED: "WARNING: Over-hardening detected - initiate annealing protocol",
            HardeningState.ANNEALED: "Recovery successful, monitor for re-hardening",
        }

        # Calculate strength/ductility balance
        strength = (self.stress_coping_score + self.task_efficiency*50 + self.confidence_score) / 3
        ductility = (self.empathy_score + self.adaptability_score + self.emotional_range) / 3

        return {
            "person_id": self.person_id,
            "hardening_state": state.value,
            "cumulative_stress_exposure": self.cumulative_stress_exposure,
            "strength_index": round(strength, 1),
            "ductility_index": round(ductility, 1),
            "depersonalization_score": self.depersonalization_score,
            "cynicism_score": self.cynicism_score,
            "recommendation": recommendations[state],
            "requires_intervention": state == HardeningState.OVER_HARDENED,
        }

    def prescribe_annealing(self) -> dict:
        """
        Prescribe 'annealing' protocol to reverse over-hardening.

        Materials annealing: Heat + hold + cool = reduced dislocation density
        Psychological annealing: Low stress + reflection + support = restored ductility
        """
        if self.calculate_hardening_state() != HardeningState.OVER_HARDENED:
            return {"annealing_needed": False}

        return {
            "annealing_needed": True,
            "protocol": "PSYCHOLOGICAL_ANNEALING",
            "duration_weeks": 6,
            "components": [
                "REDUCE_LOAD: 30% reduction in clinical duties (4 weeks)",
                "REFLECTION: Weekly supervision/therapy sessions",
                "RECONNECTION: Engagement with professional ideals (why medicine?)",
                "SUPPORT: Peer support groups, mentorship",
                "SKILL_REFRESH: Non-clinical learning (restore curiosity)",
                "GRADUAL_RETURN: Phased return to full duties",
            ],
            "target_outcomes": {
                "empathy_score": ">75",
                "adaptability_score": ">65",
                "depersonalization_score": "<8",
                "cynicism_score": "<30",
            },
            "monitoring_frequency": "Bi-weekly assessments",
        }
```

**2. Optimal Hardening Schedule Design:**

```python
# Design rotations to provide beneficial hardening without over-hardening

def design_optimal_hardening_rotation(pgy_level: int) -> dict:
    """
    Design rotation schedule for optimal work hardening.

    Gradual stress exposure with recovery periods.
    """
    if pgy_level == 1:  # Interns
        return {
            "phase": "INITIAL_HARDENING",
            "max_consecutive_high_stress_weeks": 2,
            "recovery_after_hard_rotation": 1,  # weeks
            "hard_rotations_per_year": 4,
            "principle": "Brief stress exposure, ample recovery, skill focus",
        }

    elif pgy_level == 2:  # PGY-2
        return {
            "phase": "PROGRESSIVE_HARDENING",
            "max_consecutive_high_stress_weeks": 3,
            "recovery_after_hard_rotation": 1,
            "hard_rotations_per_year": 6,
            "principle": "Increased stress tolerance, maintained recovery",
        }

    else:  # PGY-3+
        return {
            "phase": "MAINTENANCE",
            "max_consecutive_high_stress_weeks": 4,
            "recovery_after_hard_rotation": 1,
            "hard_rotations_per_year": 8,
            "principle": "Sustained performance, over-hardening prevention",
        }
```

**3. Over-Hardening Prevention:**

```python
# Detect early signs of over-hardening

def monitor_for_over_hardening(person: Person) -> dict:
    """
    Monthly assessment for over-hardening (brittleness).

    Returns: assessment with intervention triggers
    """
    # Administer assessments
    mbi_scores = administer_maslach_burnout_inventory(person)
    empathy_score = administer_empathy_assessment(person)
    adaptability_score = assess_cognitive_flexibility(person)

    # Check for over-hardening markers
    over_hardening_detected = (
        mbi_scores["depersonalization"] > 10 or
        empathy_score < 60 or
        adaptability_score < 50
    )

    if over_hardening_detected:
        return {
            "person_id": person.id,
            "alert": "OVER_HARDENING_DETECTED",
            "severity": "HIGH" if mbi_scores["depersonalization"] > 15 else "MODERATE",
            "recommendation": "Initiate annealing protocol - reduce stress exposure 30%",
            "metrics": {
                "depersonalization": mbi_scores["depersonalization"],
                "empathy": empathy_score,
                "adaptability": adaptability_score,
            },
            "action": "IMMEDIATE",
        }

    return {"status": "OPTIMAL_HARDENING"}
```

---

## 6. Fracture Mechanics: Crack Propagation and Critical Stress Intensity

### Core Materials Science Principle

[Fracture mechanics](https://mechanicalc.com/reference/fracture-mechanics) predicts catastrophic failure from crack growth:

**Stress Intensity Factor (K):**
```
K = σ√(πa)f(geometry)

Where:
- σ = applied stress
- a = crack length
- f = geometric correction factor
```

**Critical Stress Intensity (K_IC):**
- Material property (fracture toughness)
- When K ≥ K_IC → unstable crack growth → fracture
- Units: MPa√m or ksi√in

**Crack Growth Stages:**

1. **Crack Initiation:**
   - Micro-cracks form at stress concentrators
   - Inclusions, surface defects, dislocation pile-ups

2. **Stable Crack Growth:**
   - Slow, controlled growth
   - K < K_IC
   - Predictable from Paris Law: da/dN = C(ΔK)^m

3. **Critical Crack Length:**
   - K reaches K_IC
   - Transition to unstable growth

4. **Catastrophic Failure:**
   - Rapid crack propagation
   - Material fractures
   - Sudden, often without warning

**Key Insight:** Small cracks are benign until they reach critical size. Non-destructive testing can detect cracks before failure.

### Application to Workforce Fatigue

**Psychological "Cracks" (Burnout Precursors):**

Micro-cracks (initiation):
- First medical error
- First patient complaint
- First interpersonal conflict
- First documentation lapse
- *Often dismissed as isolated incidents*

Stable crack growth (propagation):
- Increasing error frequency
- Recurring conflicts
- Progressive withdrawal
- Mounting complaints
- Sleep problems worsening
- *Visible to close observers, not yet critical*

Critical crack length (K → K_IC):
- Multiple concurrent stressors
- Loss of coping mechanisms
- Social support network fails
- Suicidal ideation emerges
- *On verge of catastrophic failure*

Catastrophic failure (fracture):
- Complete burnout
- Suicide attempt
- Job abandonment
- Medical leave
- Malpractice event
- *System failure, sudden and severe*

**Stress Intensity Factor Analogy:**

```
K_psychological = (External Stress) × √(Vulnerability Magnitude) × f(Support)

Where:
- External Stress = workload, life events, etc.
- Vulnerability = existing "crack" (depression, burnout symptoms)
- f(Support) = social support reduces stress intensity
```

### Detection Methods

**1. Crack Detection (NDT Analogy):**

Non-destructive testing for psychological cracks:

**Weekly "Ultrasonic Inspection":**
- Brief check-ins: "How are you doing, really?"
- Emotional temperature checks
- Sleep quality questions
- Substance use screening

**Monthly "Radiographic Inspection":**
- PHQ-9 (depression screening)
- GAD-7 (anxiety screening)
- Single-item burnout measure
- *Detects internal cracks not visible externally*

**Quarterly "Dye Penetrant Testing":**
- Comprehensive wellness assessment
- MBI (Maslach Burnout Inventory)
- Work-life balance evaluation
- Career satisfaction
- *Reveals crack networks*

**2. Crack Size Measurement:**

Track crack propagation over time:

```python
# Severity scoring (crack length proxy)
burnout_crack_length = (
    phq9_score * 2.0 +           # Depression severity
    gad7_score * 1.5 +           # Anxiety
    mbi_emotional_exhaustion +   # Burnout
    sleep_debt_hours * 0.5 +     # Physiological
    error_count_30d * 3.0        # Performance
)

# Critical crack length threshold
CRITICAL_CRACK_LENGTH = 60  # Empirically derived

if burnout_crack_length >= CRITICAL_CRACK_LENGTH:
    alert_imminent_fracture()  # K ≥ K_IC
```

**3. Stress Intensity Monitoring:**

```python
def calculate_stress_intensity_factor(
    external_stress: float,       # 0-100
    vulnerability_magnitude: float,  # Crack length proxy
    social_support: float,        # 0-100
) -> float:
    """
    Calculate psychological stress intensity factor.

    K = σ√(πa) / support_factor
    """
    import math

    # Geometry factor (simplified)
    support_factor = 1.0 + (social_support / 100.0)  # Support reduces K

    K = (external_stress * math.sqrt(math.pi * vulnerability_magnitude)) / support_factor

    return K

# Critical stress intensity (person-specific)
K_IC_baseline = 150  # Average fracture toughness

if K > K_IC_baseline:
    status = "CRITICAL_CRACK_PROPAGATION"
else:
    status = "STABLE"
```

**4. Paris Law (Crack Growth Rate):**

```
da/dN = C(ΔK)^m

Psychological analogy:
d(burnout)/d(week) = C(stress_variation)^m
```

Track burnout progression rate:
```python
burnout_growth_rate = (burnout_this_week - burnout_last_week) / 1_week

if burnout_growth_rate > 2.0:  # Accelerating growth
    warn_critical_crack_growth()
```

### Implementation Ideas

**1. Fracture Mechanics Module:**

```python
# backend/app/resilience/fracture_mechanics.py (NEW)

from dataclasses import dataclass, field
from datetime import date
import math

@dataclass
class PsychologicalCrack:
    """Represent a psychological 'crack' (burnout precursor)."""

    person_id: str
    crack_id: str
    initiated_date: date

    # Crack characteristics
    crack_type: str  # "depression", "burnout", "anxiety", "trauma"
    initial_severity: float  # Crack length at detection
    current_severity: float

    # Growth tracking
    severity_history: list[tuple[date, float]] = field(default_factory=list)
    growth_rate: float = 0.0  # da/dN (severity increase per week)

    # Stress factors
    external_stress_level: float = 50.0  # 0-100
    social_support_level: float = 70.0   # 0-100

    # Critical thresholds
    critical_severity: float = 60.0  # K_IC equivalent

    def record_severity(self, measurement_date: date, severity: float):
        """Record crack severity measurement."""
        self.severity_history.append((measurement_date, severity))
        self.current_severity = severity

        # Calculate growth rate if we have enough data
        if len(self.severity_history) >= 2:
            self._calculate_growth_rate()

    def _calculate_growth_rate(self):
        """Calculate crack growth rate (Paris Law analogy)."""
        if len(self.severity_history) < 2:
            return

        # Last 4 weeks of data
        recent = self.severity_history[-4:]

        # Linear regression to get slope
        dates_numeric = [(d - self.initiated_date).days for d, _ in recent]
        severities = [s for _, s in recent]

        if len(dates_numeric) >= 2:
            # Simple slope calculation
            time_span = dates_numeric[-1] - dates_numeric[0]
            severity_change = severities[-1] - severities[0]

            if time_span > 0:
                self.growth_rate = (severity_change / time_span) * 7  # per week

    def calculate_stress_intensity_factor(self) -> float:
        """
        Calculate stress intensity factor K.

        K = σ√(πa) / support_factor
        """
        support_factor = 1.0 + (self.social_support_level / 100.0)

        K = (self.external_stress_level * math.sqrt(math.pi * self.current_severity)) / support_factor

        return K

    def predict_time_to_critical(self) -> int:
        """
        Predict days until crack reaches critical size.

        Returns: days until K ≥ K_IC (fracture)
        """
        if self.growth_rate <= 0:
            return -1  # Not growing or shrinking

        severity_deficit = self.critical_severity - self.current_severity

        if severity_deficit <= 0:
            return 0  # Already critical

        weeks_to_critical = severity_deficit / self.growth_rate
        return int(weeks_to_critical * 7)  # Convert to days

    def get_fracture_risk(self) -> dict:
        """Assess risk of catastrophic failure."""
        K = self.calculate_stress_intensity_factor()
        K_IC = self.critical_severity  # Simplified

        # Normalized stress intensity (0-1, >1 = critical)
        normalized_K = K / K_IC

        days_to_critical = self.predict_time_to_critical()

        if normalized_K >= 1.0:
            risk_level = "CRITICAL_FRACTURE_IMMINENT"
            recommendation = "IMMEDIATE INTERVENTION: Remove from clinical duties, psychiatric evaluation"
        elif normalized_K >= 0.8:
            risk_level = "HIGH"
            recommendation = "Urgent: Reduce stress, increase support, weekly monitoring"
        elif normalized_K >= 0.6:
            risk_level = "MODERATE"
            recommendation = "Monitor closely, consider workload reduction"
        else:
            risk_level = "LOW"
            recommendation = "Continue routine monitoring"

        return {
            "person_id": self.person_id,
            "crack_type": self.crack_type,
            "current_severity": self.current_severity,
            "stress_intensity_K": round(K, 2),
            "critical_K_IC": K_IC,
            "normalized_K": round(normalized_K, 2),
            "growth_rate_per_week": round(self.growth_rate, 2),
            "days_to_critical": days_to_critical,
            "risk_level": risk_level,
            "recommendation": recommendation,
        }

@dataclass
class FractureMechanicsMonitor:
    """Monitor psychological cracks across workforce."""

    cracks: dict[str, list[PsychologicalCrack]] = field(default_factory=dict)

    def detect_new_cracks(self, person_id: str, assessment_data: dict) -> list[PsychologicalCrack]:
        """
        Detect new psychological cracks from assessment data.

        Args:
            person_id: Person being assessed
            assessment_data: PHQ-9, GAD-7, MBI scores

        Returns:
            List of newly detected cracks
        """
        new_cracks = []

        # Depression crack
        phq9 = assessment_data.get("phq9_score", 0)
        if phq9 >= 10:  # Moderate depression threshold
            crack = PsychologicalCrack(
                person_id=person_id,
                crack_id=f"{person_id}_depression_{date.today()}",
                initiated_date=date.today(),
                crack_type="depression",
                initial_severity=phq9,
                current_severity=phq9,
            )
            new_cracks.append(crack)

        # Burnout crack
        mbi_ee = assessment_data.get("mbi_emotional_exhaustion", 0)
        if mbi_ee >= 27:  # High emotional exhaustion
            crack = PsychologicalCrack(
                person_id=person_id,
                crack_id=f"{person_id}_burnout_{date.today()}",
                initiated_date=date.today(),
                crack_type="burnout",
                initial_severity=mbi_ee,
                current_severity=mbi_ee,
            )
            new_cracks.append(crack)

        # Anxiety crack
        gad7 = assessment_data.get("gad7_score", 0)
        if gad7 >= 10:
            crack = PsychologicalCrack(
                person_id=person_id,
                crack_id=f"{person_id}_anxiety_{date.today()}",
                initiated_date=date.today(),
                crack_type="anxiety",
                initial_severity=gad7,
                current_severity=gad7,
            )
            new_cracks.append(crack)

        # Register cracks
        if person_id not in self.cracks:
            self.cracks[person_id] = []

        self.cracks[person_id].extend(new_cracks)

        return new_cracks

    def get_critical_cracks(self) -> list[dict]:
        """Get all cracks approaching critical stress intensity."""
        critical = []

        for person_id, person_cracks in self.cracks.items():
            for crack in person_cracks:
                risk = crack.get_fracture_risk()

                if risk["risk_level"] in ("CRITICAL_FRACTURE_IMMINENT", "HIGH"):
                    critical.append(risk)

        return sorted(critical, key=lambda x: x["normalized_K"], reverse=True)
```

**2. Non-Destructive Testing Schedule:**

```python
# Implement routine "crack inspection" schedule

INSPECTION_SCHEDULE = {
    "daily": ["brief_emotional_check"],  # Supervisor touch-base
    "weekly": ["sleep_quality", "stress_level_1_10"],
    "monthly": ["PHQ-9", "GAD-7", "single_item_burnout"],
    "quarterly": ["MBI_full", "work_life_balance", "career_satisfaction"],
    "annually": ["comprehensive_wellness_exam"],
}

def conduct_ndt_inspection(person: Person, frequency: str):
    """Conduct non-destructive testing for psychological cracks."""
    assessments = INSPECTION_SCHEDULE[frequency]

    results = {}
    for assessment in assessments:
        results[assessment] = administer_assessment(person, assessment)

    # Analyze for new cracks
    monitor = FractureMechanicsMonitor()
    new_cracks = monitor.detect_new_cracks(person.id, results)

    if new_cracks:
        alert_new_cracks_detected(person, new_cracks)

    return results
```

**3. Crack Arrest (Intervention):**

```python
def arrest_crack_propagation(crack: PsychologicalCrack) -> dict:
    """
    Prevent crack from reaching critical size (fracture prevention).

    Materials science crack arrest:
    - Drill hole at crack tip (stop propagation)
    - Apply compressive stress (close crack)
    - Change material properties (annealing)

    Psychological crack arrest:
    - Remove stress (workload reduction)
    - Add support (therapy, mentorship)
    - Restore resilience (recovery activities)
    """
    risk = crack.get_fracture_risk()

    if risk["risk_level"] == "CRITICAL_FRACTURE_IMMINENT":
        return {
            "intervention": "EMERGENCY_CRACK_ARREST",
            "actions": [
                "IMMEDIATE: Remove from clinical duties (complete stress removal)",
                "PSYCHIATRIC EVALUATION: Within 24 hours",
                "CRISIS SUPPORT: Activate crisis intervention team",
                "HOSPITALIZATION: Consider if suicidal ideation present",
            ],
            "duration": "Until cleared by psychiatry",
            "goal": "Prevent catastrophic failure (suicide, complete breakdown)",
        }

    elif risk["risk_level"] == "HIGH":
        return {
            "intervention": "AGGRESSIVE_CRACK_ARREST",
            "actions": [
                "WORKLOAD REDUCTION: 50% reduction for 4 weeks",
                "THERAPY: Weekly sessions (CBT/DBT)",
                "MEDICATION EVALUATION: Consult psychiatry",
                "PEER SUPPORT: Assign mentor for weekly check-ins",
                "RE-ASSESS: Weekly crack size measurements",
            ],
            "duration": "4-8 weeks",
            "goal": "Stop crack growth, reduce K below 0.6*K_IC",
        }

    else:  # MODERATE
        return {
            "intervention": "PREVENTIVE_CRACK_ARREST",
            "actions": [
                "WORKLOAD ADJUSTMENT: 20% reduction",
                "COUNSELING: Bi-weekly sessions",
                "WELLNESS ACTIVITIES: Dedicated time for recovery",
                "MONITOR: Bi-weekly assessments",
            ],
            "duration": "4 weeks",
            "goal": "Prevent crack growth, maintain stable state",
        }
```

---

## 7. Annealing: Relieving Internal Stresses Through Controlled Recovery

### Core Materials Science Principle

[Annealing](https://virgamet.com/blog/recrystallization-annealing) is a heat treatment that reverses work hardening and relieves residual stresses:

**Three Stages:**

1. **Recovery (550-650°C):**
   - Dislocation density reduction
   - Internal stresses relax
   - Minimal microstructure change
   - Slight softening

2. **Recrystallization (650-750°C):**
   - New strain-free grains nucleate
   - Old deformed grains consumed
   - Dramatic softening
   - Ductility restored
   - Strength reduced to annealed state

3. **Grain Growth (>750°C, extended time):**
   - Coarsening of grain structure
   - May reduce strength excessively
   - Controlled to prevent over-softening

**Process:**
- Heat to recrystallization temperature
- Hold for time (hours)
- Slow cool to room temperature

**Effects:**
- Reverses work hardening
- Restores ductility
- Eliminates residual stresses
- Returns to "pristine" state (mostly)

**Applications:**
- Between cold working operations
- Stress relief after welding
- Dimensional stability
- Improved machinability

### Application to Workforce Fatigue

**Psychological Annealing (Recovery & Restoration):**

Recovery phase (light stress reduction):
- Weekend off (48h recovery)
- Short vacation (3-5 days)
- Light duty week
- *Reduces acute stress, minimal restoration*

Recrystallization phase (significant recovery):
- Extended vacation (2-3 weeks)
- Sabbatical (3-6 months)
- Recovery from burnout
- Therapy + stress-free environment
- *Dramatic restoration, "like new"*

Grain growth phase (over-recovery):
- Extended leave (>6 months)
- Career break
- Risk: skill atrophy, disconnection
- *May require re-orientation/training*

**Annealing Requirements:**

Temperature (stress removal):
- Must reduce stress below recrystallization threshold
- Partial stress reduction → recovery only (incomplete)
- Full stress removal → recrystallization (complete reset)

Time (duration):
- Insufficient time → incomplete recrystallization
- Adequate time → full restoration
- Excessive time → skill loss (grain growth)

Cooling (return to work):
- Rapid return → re-hardening shock
- Gradual return → sustainable restoration
- *Phased return to full duties critical*

### Detection Methods

**1. Need for Annealing Assessment:**

Indicators that annealing is needed:
- High work hardening (over-hardened)
- Excessive dislocation density (schedule chaos)
- Brittle behavior (emotional rigidity)
- High residual stress (chronic tension)

```python
def assess_annealing_need(person: Person) -> dict:
    """Determine if psychological annealing is needed."""

    metrics = {
        "work_hardening_state": get_work_hardening_state(person),
        "dislocation_density": get_schedule_disruption_density(person),
        "brittleness_index": get_emotional_rigidity_score(person),
        "residual_stress": get_chronic_stress_level(person),
    }

    # Decision matrix
    needs_annealing = (
        metrics["work_hardening_state"] == "OVER_HARDENED" or
        metrics["brittleness_index"] > 70 or
        metrics["residual_stress"] > 80
    )

    if needs_annealing:
        # Determine annealing depth
        if metrics["brittleness_index"] > 85:
            anneal_type = "FULL_RECRYSTALLIZATION"
            duration_weeks = 12
        elif metrics["residual_stress"] > 70:
            anneal_type = "STRESS_RELIEF_ANNEAL"
            duration_weeks = 4
        else:
            anneal_type = "RECOVERY_ANNEAL"
            duration_weeks = 2

        return {
            "annealing_needed": True,
            "anneal_type": anneal_type,
            "duration_weeks": duration_weeks,
            "metrics": metrics,
        }

    return {"annealing_needed": False}
```

**2. Annealing Progress Monitoring:**

Track restoration during annealing:

```python
def monitor_annealing_progress(
    person: Person,
    anneal_start_date: date,
    target_state: str
) -> dict:
    """
    Monitor progress during annealing (recovery) period.

    Analogous to monitoring temperature during heat treatment.
    """
    weeks_in_anneal = (date.today() - anneal_start_date).days // 7

    # Measure restoration markers
    stress_level_current = measure_stress_biomarkers(person)
    ductility_current = measure_emotional_flexibility(person)
    hardness_current = measure_cognitive_rigidity(person)

    # Expected values for complete annealing
    target_values = {
        "stress_level": 30,    # Low
        "ductility": 85,       # High flexibility
        "hardness": 40,        # Soft (adaptable)
    }

    # Calculate completion %
    stress_progress = (100 - stress_level_current) / (100 - target_values["stress_level"])
    ductility_progress = ductility_current / target_values["ductility"]
    hardness_progress = (100 - hardness_current) / (100 - target_values["hardness"])

    overall_progress = (stress_progress + ductility_progress + hardness_progress) / 3

    return {
        "person_id": person.id,
        "weeks_in_anneal": weeks_in_anneal,
        "overall_progress": round(overall_progress * 100, 1),
        "current_state": {
            "stress_level": stress_level_current,
            "ductility": ductility_current,
            "hardness": hardness_current,
        },
        "target_state": target_values,
        "complete": overall_progress >= 0.9,
    }
```

### Implementation Ideas

**1. Annealing Protocol Module:**

```python
# backend/app/resilience/annealing.py (NEW)

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

class AnnealingType(str, Enum):
    """Type of annealing treatment."""
    STRESS_RELIEF = "stress_relief"           # Recovery only (no recrystallization)
    RECRYSTALLIZATION = "recrystallization"   # Full reset
    FULL_ANNEAL = "full_anneal"               # Complete restoration + grain refinement

@dataclass
class AnnealingProtocol:
    """Psychological annealing (recovery) protocol."""

    person_id: str
    anneal_type: AnnealingType
    start_date: date
    duration_weeks: int

    # Temperature (stress level) requirements
    target_stress_level: float = 20.0  # Must achieve this or below

    # Phases
    heating_phase_weeks: int = 1       # Ramp down stress gradually
    holding_phase_weeks: int = None    # Main recovery period
    cooling_phase_weeks: int = 2       # Phased return to work

    # Monitoring
    check_in_frequency_days: int = 7

    # Outcomes
    target_outcomes: dict = None

    def __post_init__(self):
        """Initialize calculated fields."""
        # Calculate holding phase
        self.holding_phase_weeks = self.duration_weeks - self.heating_phase_weeks - self.cooling_phase_weeks

        # Set target outcomes based on type
        if self.anneal_type == AnnealingType.STRESS_RELIEF:
            self.target_outcomes = {
                "stress_biomarkers": "<40",
                "sleep_quality": ">80%",
                "mood_score": ">70",
            }
        elif self.anneal_type == AnnealingType.RECRYSTALLIZATION:
            self.target_outcomes = {
                "burnout_score": "<25",
                "empathy_restored": ">75",
                "adaptability": ">70",
                "depersonalization": "<8",
            }
        else:  # FULL_ANNEAL
            self.target_outcomes = {
                "complete_restoration": "baseline",
                "professional_identity": "restored",
                "career_satisfaction": ">80",
            }

    def get_current_phase(self, current_date: date) -> str:
        """Determine current phase of annealing."""
        weeks_elapsed = (current_date - self.start_date).days // 7

        if weeks_elapsed < self.heating_phase_weeks:
            return "HEATING"  # Ramping down stress
        elif weeks_elapsed < self.heating_phase_weeks + self.holding_phase_weeks:
            return "HOLDING"  # Main recovery
        elif weeks_elapsed < self.duration_weeks:
            return "COOLING"  # Phased return
        else:
            return "COMPLETE"

    def get_phase_instructions(self, phase: str) -> list[str]:
        """Get instructions for current phase."""

        instructions = {
            "HEATING": [
                "Week 1: Gradual reduction of clinical duties",
                "Transfer active patients to colleagues",
                "Cancel non-essential commitments",
                "Begin daily wellness activities (exercise, meditation)",
                "Establish therapy/counseling schedule",
            ],
            "HOLDING": [
                f"Weeks 2-{self.holding_phase_weeks + 1}: Complete stress removal",
                "NO clinical work (essential for recrystallization)",
                "Focus on restoration activities:",
                "  - Physical health (sleep, exercise, nutrition)",
                "  - Mental health (therapy, mindfulness)",
                "  - Social connection (family, friends)",
                "  - Professional identity (reflection on values, goals)",
                "Weekly monitoring of recovery markers",
                "Adjust duration if progress slower than expected",
            ],
            "COOLING": [
                f"Weeks {self.duration_weeks - self.cooling_phase_weeks}-{self.duration_weeks}: Phased return",
                "Week 1 of return: 25% clinical load",
                "Week 2 of return: 50% clinical load",
                "Full return only if restoration complete",
                "Maintain wellness activities permanently",
            ],
            "COMPLETE": [
                "Annealing complete - verify outcomes achieved",
                "Transition to maintenance mode",
                "Implement work-hardening prevention strategies",
            ],
        }

        return instructions.get(phase, [])

    def assess_readiness_for_next_phase(
        self,
        current_phase: str,
        assessment_data: dict
    ) -> dict:
        """
        Assess if person is ready to progress to next phase.

        Critical: Don't rush cooling phase (return to work).
        Like materials: premature cooling causes re-hardening.
        """
        if current_phase == "HEATING":
            # Check stress level reduction
            stress_level = assessment_data.get("stress_level", 100)
            ready = stress_level < 50

            return {
                "ready_for_next_phase": ready,
                "current_phase": "HEATING",
                "next_phase": "HOLDING",
                "gate_criteria": "Stress level < 50",
                "current_value": stress_level,
            }

        elif current_phase == "HOLDING":
            # Check for recrystallization completion
            restoration_markers = {
                "stress_level": assessment_data.get("stress_level", 100) < 30,
                "sleep_quality": assessment_data.get("sleep_quality", 0) > 85,
                "mood_stability": assessment_data.get("mood_score", 0) > 75,
                "burnout_reduction": assessment_data.get("burnout_score", 100) < 30,
            }

            markers_met = sum(restoration_markers.values())
            ready = markers_met >= 3  # At least 3 of 4 markers

            return {
                "ready_for_next_phase": ready,
                "current_phase": "HOLDING",
                "next_phase": "COOLING",
                "gate_criteria": "3 of 4 restoration markers met",
                "markers_met": markers_met,
                "markers_detail": restoration_markers,
                "recommendation": "Continue holding phase if not ready" if not ready else "Begin phased return",
            }

        elif current_phase == "COOLING":
            # Check tolerance of gradual work return
            current_load = assessment_data.get("current_workload_percent", 0)
            stress_response = assessment_data.get("stress_level", 100)

            # Should tolerate increased load without stress spike
            ready = (current_load >= 75) and (stress_response < 40)

            return {
                "ready_for_next_phase": ready,
                "current_phase": "COOLING",
                "next_phase": "COMPLETE",
                "gate_criteria": "Tolerating 75%+ workload with stress <40",
                "current_workload": current_load,
                "stress_response": stress_response,
            }

        return {"ready_for_next_phase": True}

# Prescribe annealing based on assessment
def prescribe_annealing(person: Person, assessment: dict) -> AnnealingProtocol:
    """
    Prescribe appropriate annealing protocol.

    Matches severity to annealing type and duration.
    """
    severity_score = calculate_severity(assessment)

    if severity_score >= 80:  # Severe
        return AnnealingProtocol(
            person_id=person.id,
            anneal_type=AnnealingType.FULL_ANNEAL,
            start_date=date.today(),
            duration_weeks=12,
        )
    elif severity_score >= 60:  # Moderate
        return AnnealingProtocol(
            person_id=person.id,
            anneal_type=AnnealingType.RECRYSTALLIZATION,
            start_date=date.today(),
            duration_weeks=6,
        )
    else:  # Mild
        return AnnealingProtocol(
            person_id=person.id,
            anneal_type=AnnealingType.STRESS_RELIEF,
            start_date=date.today(),
            duration_weeks=2,
        )
```

**2. Preventive Annealing Schedule:**

Just as materials are annealed between cold working operations, schedule regular recovery:

```python
# Implement periodic annealing to prevent over-hardening

PREVENTIVE_ANNEALING_SCHEDULE = {
    "PGY1": {
        "frequency_weeks": 8,  # Every 8 weeks
        "duration_weeks": 1,   # 1 week stress relief
        "type": AnnealingType.STRESS_RELIEF,
        "rationale": "Prevent accumulation of work hardening during intern year",
    },
    "PGY2": {
        "frequency_weeks": 12,
        "duration_weeks": 1,
        "type": AnnealingType.STRESS_RELIEF,
    },
    "PGY3+": {
        "frequency_weeks": 16,
        "duration_weeks": 2,
        "type": AnnealingType.RECRYSTALLIZATION,  # Deeper restoration needed
    },
}

def schedule_preventive_annealing(person: Person, academic_year: int) -> list[date]:
    """
    Schedule preventive annealing periods throughout the year.

    Prevents over-hardening by regular stress relief.
    """
    config = PREVENTIVE_ANNEALING_SCHEDULE[f"PGY{person.pgy_level}"]

    anneal_dates = []
    current_date = datetime(academic_year, 7, 1)  # July 1st start

    while current_date < datetime(academic_year + 1, 6, 30):
        anneal_dates.append(current_date)
        current_date += timedelta(weeks=config["frequency_weeks"])

    return anneal_dates
```

**3. Integration with Scheduling System:**

```python
# backend/app/scheduling/validator.py

def validate_annealing_compliance(assignments: list[Assignment]) -> bool:
    """
    Ensure schedule includes adequate annealing (recovery) periods.

    Rejects schedules that don't allow for recrystallization.
    """
    for person in get_all_residents():
        # Check for preventive annealing periods
        annealing_weeks = count_annealing_weeks(person, assignments)
        required_annealing = PREVENTIVE_ANNEALING_SCHEDULE[f"PGY{person.pgy_level}"]

        expected_anneals = 52 // required_annealing["frequency_weeks"]

        if annealing_weeks < expected_anneals:
            logger.warning(
                f"Insufficient annealing for {person.name}: "
                f"{annealing_weeks} vs {expected_anneals} required"
            )
            return False

    return True
```

---

## Summary Matrix: Materials Science Concepts Applied to Workforce Resilience

| Concept | Material Behavior | Workforce Analog | Detection Method | Implementation |
|---------|------------------|------------------|------------------|----------------|
| **Stress-Strain Curve** | Elastic → Yield → Plastic → Fracture | Safe hours → Fatigue onset → Damage accumulation → Burnout | Fatigue score mapping to regions | Enforce elastic limit, prevent plastic zone work |
| **Fatigue Failure** | Repeated cyclic loading → crack nucleation → failure | Weekend calls, night shifts → cumulative damage → burnout | Cycle counting, Palmgren-Miner sum | Limit high-stress cycles, enforce recovery spacing |
| **Creep** | Time-dependent deformation under sustained load | Chronic overwork → slow degradation → sudden collapse | Performance decline rate, time-to-rupture prediction | Limit sustained load duration, creep rate monitoring |
| **Lattice Defects** | Vacancies & dislocations affect properties | Staffing gaps & schedule chaos → system brittleness | Vacancy density, dislocation density | Fill vacancies, freeze changes when brittle |
| **Work Hardening** | Deformation increases strength but reduces ductility | Stress exposure builds resilience but risks brittleness | Empathy loss, cynicism, rigidity | Controlled hardening, prevent over-hardening |
| **Fracture Mechanics** | Crack propagation → critical size → catastrophic failure | Burnout symptoms → severity increase → breakdown | Crack size, stress intensity K, growth rate | Non-destructive testing, crack arrest interventions |
| **Annealing** | Heat treatment restores ductility, relieves stress | Recovery periods restore resilience | Brittleness, residual stress assessment | Scheduled annealing, phased return protocols |

---

## Implementation Roadmap

### Phase 1: Core Metrics (4 weeks)
1. Implement `StressStrainMetrics` class
2. Enhance `FatigueTracker` with stress-strain regions
3. Add `FatigueLifeMetrics` (S-N curve tracking)
4. Deploy `LatticeDefectMetrics` for organizational health

### Phase 2: Advanced Monitoring (6 weeks)
5. Build `CreepMetrics` for sustained load tracking
6. Implement `WorkHardeningMetrics` and over-hardening detection
7. Deploy `FractureMechanicsMonitor` for psychological crack tracking
8. Create `AnnealingProtocol` module

### Phase 3: Integration & Validation (8 weeks)
9. Integrate all metrics into `HomeostasisMonitor`
10. Add scheduling constraints based on materials science rules
11. Build alert system for critical thresholds
12. Validate against historical burnout data

### Phase 4: Operational Deployment (4 weeks)
13. Train coordinators on materials science framework
14. Implement dashboard with all metrics
15. Establish intervention protocols
16. Monitor and refine thresholds

---

## Validation Strategy

**Retrospective Analysis:**
- Apply framework to historical burnout cases
- Check if early warning signals present
- Calibrate thresholds for prediction accuracy

**Prospective Monitoring:**
- Track metrics for 12 months
- Correlate with actual outcomes (burnout, errors, resignations)
- Refine models based on observed data

**A/B Testing:**
- Implement in pilot service
- Compare outcomes to control service
- Measure reduction in burnout, errors, turnover

---

## Expected Outcomes

**Early Warning:**
- Detect burnout risk 4-8 weeks before clinical manifestation
- Identify "micro-cracks" for preventive intervention

**Optimized Scheduling:**
- Balance workload to stay in elastic region
- Limit cyclic fatigue through spacing constraints
- Prevent creep failure from sustained overload

**Targeted Interventions:**
- Prescribe annealing based on work hardening state
- Arrest crack propagation before catastrophic failure
- Restore system when defect density critical

**Cultural Shift:**
- Normalize recovery as essential maintenance
- Reframe burnout as predictable materials failure
- Enable data-driven wellness interventions

---

## Sources

1. [Stress-Strain Curve - Wikipedia](https://en.wikipedia.org/wiki/Stress–strain_curve)
2. [Fatigue Strength & Limit - SDC Verifier](https://sdcverifier.com/structural-engineering-101/fatigue-strength-and-limit-understanding-materials-specific-data/)
3. [Creep Testing - TACTUN](https://tactun.com/creep-testing-predicting-long-term-material-behavior/)
4. [Crystal Defects - Number Analytics](https://www.numberanalytics.com/blog/ultimate-guide-crystal-defects-materials-science)
5. [Work Hardening - Metal Zenith](https://metalzenith.com/blogs/steel-mechanical-physical-properties-terms/work-hardening-strengthening-steel-through-deformation-mechanics)
6. [Fracture Mechanics - MechaniCalc](https://mechanicalc.com/reference/fracture-mechanics)
7. [Recrystallization Annealing - Virgamet](https://virgamet.com/blog/recrystallization-annealing)
8. [Fatigue Life Prediction - MIT](https://web.mit.edu/course/3/3.11/www/modules/fatigue.pdf)
9. [Dislocation Theory - Wikipedia](https://en.wikipedia.org/wiki/Dislocation)
10. [Annealing Process - Bodycote](https://www.bodycote.com/services/heat-treatment/annealingnormalising/recrystallisation/)

---

**Document Status:** Ready for technical review and pilot implementation

**Next Steps:**
1. Review with resilience framework team
2. Prioritize implementation phases
3. Identify pilot service for deployment
4. Establish baseline metrics collection
