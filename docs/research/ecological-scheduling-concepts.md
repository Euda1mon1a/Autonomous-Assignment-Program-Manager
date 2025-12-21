# Ecological Concepts for Scheduling and Resilience Systems

> **Research Report**
> **Date:** 2025-12-20
> **Purpose:** Map exotic ecology and ecosystem concepts to workforce scheduling and resilience
> **Context:** Residency scheduling system already using homeostasis, Le Chatelier equilibrium, and stigmergy

---

## Executive Summary

This report translates seven core ecological principles into actionable workforce scheduling mechanisms. Each concept provides a unique lens for understanding and optimizing how medical personnel ("species") interact with scheduling demands ("resources") in a complex adaptive system.

**Key Insight:** Ecosystems and medical scheduling systems share fundamental dynamics:
- Limited resources (shifts/food)
- Competition and cooperation
- Cascade failures
- Resilience through diversity
- Succession toward stable states

---

## Table of Contents

1. [Ecological Succession](#1-ecological-succession)
2. [Niche Partitioning](#2-niche-partitioning)
3. [Carrying Capacity](#3-carrying-capacity)
4. [Predator-Prey Dynamics (Lotka-Volterra)](#4-predator-prey-dynamics-lotka-volterra)
5. [Keystone Species](#5-keystone-species)
6. [Trophic Cascades](#6-trophic-cascades)
7. [Ecological Resilience](#7-ecological-resilience)
8. [Integration Architecture](#8-integration-architecture)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Ecological Succession

### Core Ecological Principle

**Ecological succession** is the process by which ecosystem structure changes over time, progressing through predictable stages toward a stable "climax community":

- **Primary succession**: Colonization of barren environments (bare rock → lichens → mosses → grasses → shrubs → forest)
- **Secondary succession**: Recovery after disturbance (cleared forest → pioneer species → intermediate → climax)
- **Climax community**: Stable equilibrium state where species composition remains constant

**Key Properties:**
- Predictable progression through stages
- Early stages: Fast-growing, opportunistic "pioneer species"
- Late stages: Slow-growing, specialized species optimized for stability
- Disturbances reset succession to earlier stages

### Mapping to Workforce/Scheduling

**Faculty = Species, Shift Coverage = Ecosystem Function**

In scheduling, succession maps to **schedule maturation** and **team evolution**:

| Succession Stage | Scheduling Equivalent | Characteristics |
|------------------|----------------------|-----------------|
| **Bare substrate** | New residency program / Empty schedule | No established patterns |
| **Pioneer stage** | Initial staffing with generalists | High turnover, flexible roles, low specialization |
| **Intermediate stage** | Mixed generalist/specialist team | Emerging preferences, some niche specialization |
| **Climax community** | Mature, stable team | Deep specialization, established preferences, low turnover |

**Real-World Example:**
A new residency program starts with all faculty covering all rotations (pioneer stage). Over 2-3 years, faculty gravitate toward specialties (intermediate). After 5 years, each faculty "owns" specific rotations and rare substitutions occur (climax).

### Specific Implementation Ideas

#### 1.1 Succession Stage Detector

**Location:** `backend/app/resilience/succession_analysis.py`

Track schedule maturity based on assignment pattern stability:

```python
@dataclass
class SuccessionStage:
    stage: str  # "pioneer", "intermediate", "climax"
    stability_index: float  # 0.0-1.0 (higher = more stable)
    specialization_ratio: float  # Specialists / Generalists
    turnover_rate: float  # Faculty changes per month
    time_to_climax_estimate: int  # Months until stable

    # Stage thresholds
    PIONEER_THRESHOLD = 0.3  # Stability < 0.3
    INTERMEDIATE_THRESHOLD = 0.7  # 0.3 ≤ stability < 0.7
    # CLIMAX = stability ≥ 0.7

def calculate_stability_index(
    current_schedule: list[Assignment],
    historical_schedules: list[list[Assignment]],
    lookback_months: int = 12
) -> float:
    """
    Measure how stable assignment patterns are over time.

    Stability indicators:
    - Same faculty assigned to same rotation types
    - Consistent block preferences (Monday AM, Friday PM, etc.)
    - Low swap frequency
    - Few emergency reassignments
    """
    pass
```

**Metrics to Track:**
- **Assignment stability**: % of blocks assigned to same faculty as last period
- **Specialization coefficient**: Herfindahl index of rotation concentration per faculty
- **Swap frequency**: Swaps per faculty per month (high = low stability)
- **Emergency coverage events**: Unplanned coverage requests (disturbance indicator)

#### 1.2 Disturbance Detection and Recovery

Track events that "reset" succession:

```python
class SuccessionDisturbance:
    """Events that reset schedule maturity."""

    DISTURBANCE_TYPES = {
        "faculty_departure": 0.8,  # High impact (faculty leaves)
        "new_hires": 0.5,          # Medium (adds capacity but disrupts patterns)
        "acgme_violation": 0.7,    # High (forces major restructure)
        "covid_surge": 0.9,        # Critical (emergency protocols)
        "new_rotation": 0.4,       # Medium (new service line)
    }

    def estimate_recovery_time(
        disturbance_type: str,
        current_stage: SuccessionStage,
        team_size: int
    ) -> int:
        """
        Estimate months to return to pre-disturbance stability.

        Recovery factors:
        - Larger teams recover faster (redundancy)
        - Climax communities take longer to recover (lost specialization)
        - Multiple disturbances compound recovery time
        """
        base_impact = DISTURBANCE_TYPES[disturbance_type]

        # Larger teams = faster recovery
        team_factor = max(0.5, 1.0 - (team_size - 10) * 0.05)

        # Climax communities lose more and take longer
        stage_factor = {
            "pioneer": 0.5,      # Already unstable, quick to adapt
            "intermediate": 1.0,  # Moderate recovery
            "climax": 1.5,       # Lost specialization is costly
        }[current_stage.stage]

        # Months to recovery
        return int(base_impact * team_factor * stage_factor * 6)
```

#### 1.3 Succession-Aware Scheduling

**Optimization Strategy:** Adjust scheduling algorithm based on succession stage:

| Stage | Strategy | Rationale |
|-------|----------|-----------|
| **Pioneer** | Maximize flexibility, rotate all faculty through all services | Build experience base, discover preferences |
| **Intermediate** | Balance specialization with cross-training | Develop niches while maintaining resilience |
| **Climax** | Respect established patterns, minimize disruption | Preserve stability, only swap when necessary |

```python
class SuccessionAwareConstraint(SoftConstraint):
    """
    Adjusts scheduling penalties based on succession stage.

    Pioneer stage: Low penalty for novel assignments (encourage exploration)
    Climax stage: High penalty for deviating from established patterns
    """

    def calculate_novelty_penalty(
        self,
        faculty: Person,
        rotation: str,
        succession_stage: SuccessionStage
    ) -> float:
        # Check historical assignment frequency
        historical_freq = self._get_historical_frequency(faculty.id, rotation)

        if succession_stage.stage == "pioneer":
            # Encourage novelty in pioneer stage
            return 0.0 if historical_freq < 0.1 else 5.0

        elif succession_stage.stage == "climax":
            # Penalize novelty in climax stage
            if historical_freq < 0.1:
                return 20.0  # High penalty for new assignment
            else:
                return 0.0   # No penalty for established pattern

        else:  # intermediate
            # Moderate penalty
            return 10.0 if historical_freq < 0.05 else 0.0
```

### Warning Signs and Metrics

| Warning Sign | Metric | Threshold | Action |
|--------------|--------|-----------|--------|
| **Regression from climax** | Stability index dropping | Δ > 0.15 in 3 months | Investigate disturbances, reduce changes |
| **Stuck in pioneer stage** | Stability < 0.3 | > 18 months | Force specialization, reduce rotation frequency |
| **Over-specialized climax** | Specialization ratio > 3.0 | Any | Cross-train to prevent brittleness |
| **Chronic instability** | High swap rate | > 0.5 swaps/faculty/month | Review workload balance, preferences |

**Dashboard Metrics:**
```python
@dataclass
class SuccessionHealthReport:
    current_stage: str
    stability_index: float
    months_at_current_stage: int

    # Trend indicators
    stability_trend: str  # "improving", "stable", "degrading"
    recent_disturbances: list[SuccessionDisturbance]

    # Recommendations
    schedule_strategy: str  # "explore", "balance", "preserve"
    cross_training_needed: bool
    predicted_next_stage: str
    estimated_months_to_next: int
```

---

## 2. Niche Partitioning

### Core Ecological Principle

**Niche partitioning** (resource partitioning) is how species divide limited resources to coexist and reduce competition:

- **Resource axis differentiation**: Species specialize on different resources
- **Competitive exclusion principle**: Two species cannot occupy the same niche indefinitely
- **Niche breadth**: Generalists (wide niche) vs specialists (narrow niche)

**Classic Example:** Darwin's finches on Galápagos Islands evolved different beak sizes to eat different seed sizes, reducing competition.

**Resource Axes:**
- Food type (seeds, insects, nectar)
- Feeding height (ground, shrubs, canopy)
- Time of day (diurnal, nocturnal, crepuscular)

### Mapping to Workforce/Scheduling

**Faculty = Species, Shifts/Rotations = Resources**

Medical scheduling has multiple resource axes that can be partitioned:

| Resource Axis | Partitioning Strategy | Example |
|---------------|----------------------|---------|
| **Time of day** | AM specialists vs PM specialists | Dr. Smith prefers 7am-3pm, Dr. Jones 3pm-11pm |
| **Day of week** | Weekend warriors vs weekday-only | Dr. Lee covers weekends, gets weekdays off |
| **Rotation type** | Inpatient vs outpatient vs procedures | Dr. Chen (clinic), Dr. Park (wards) |
| **Patient population** | Pediatrics vs adults vs geriatrics | Age-based specialization |
| **Acuity level** | ICU vs floor vs discharge planning | Intensity-based partitioning |
| **Geographic zone** | North campus vs South campus | Spatial partitioning |

**Competitive Exclusion in Scheduling:**
Two faculty with identical preferences cannot both get their ideal schedule. One must shift to a different niche or accept suboptimal assignments.

### Specific Implementation Ideas

#### 2.1 Multi-Dimensional Niche Space

**Location:** `backend/app/resilience/niche_analysis.py`

Model each faculty member's "niche" as a point in multi-dimensional preference space:

```python
@dataclass
class SchedulingNiche:
    """Faculty member's scheduling niche in N-dimensional space."""

    faculty_id: UUID

    # Temporal axes (0.0 = avoid, 1.0 = strongly prefer)
    time_of_day_prefs: dict[str, float]  # {"morning": 0.8, "afternoon": 0.5, "evening": 0.2}
    day_of_week_prefs: dict[str, float]  # {"monday": 0.7, "friday": 0.3, ...}

    # Functional axes
    rotation_type_prefs: dict[str, float]  # {"clinic": 0.9, "inpatient": 0.3, ...}
    patient_pop_prefs: dict[str, float]   # {"pediatric": 0.8, "adult": 0.6, ...}

    # Spatial axes
    location_prefs: dict[str, float]  # {"north_campus": 0.9, "south_campus": 0.4}

    # Derived properties
    niche_breadth: float  # Variance across all preferences (high = generalist)
    niche_center: dict[str, float]  # Mean preference vector

    @property
    def is_generalist(self) -> bool:
        """Generalist = low variance in preferences."""
        return self.niche_breadth > 0.6

    @property
    def is_specialist(self) -> bool:
        """Specialist = high variance (strong preferences)."""
        return self.niche_breadth < 0.3

def calculate_niche_overlap(
    niche_a: SchedulingNiche,
    niche_b: SchedulingNiche
) -> float:
    """
    Calculate overlap between two faculty niches (0.0-1.0).

    High overlap = high competition for same assignments.
    Low overlap = complementary, can coexist peacefully.

    Uses Pianka's index from ecology:
    Overlap = Σ(p_i_a * p_i_b) / sqrt(Σ(p_i_a²) * Σ(p_i_b²))
    """
    all_axes = set(niche_a.time_of_day_prefs.keys()) | set(niche_b.time_of_day_prefs.keys())

    numerator = sum(
        niche_a.time_of_day_prefs.get(axis, 0.5) *
        niche_b.time_of_day_prefs.get(axis, 0.5)
        for axis in all_axes
    )

    denom_a = sum(niche_a.time_of_day_prefs.get(axis, 0.5) ** 2 for axis in all_axes)
    denom_b = sum(niche_b.time_of_day_prefs.get(axis, 0.5) ** 2 for axis in all_axes)

    if denom_a == 0 or denom_b == 0:
        return 0.0

    return numerator / (denom_a * denom_b) ** 0.5
```

#### 2.2 Niche Partitioning Optimizer

**Goal:** Maximize team coverage while minimizing competition (niche overlap).

```python
class NichePartitioningService:
    """Optimize faculty assignments to reduce niche competition."""

    def recommend_partitioning(
        self,
        faculty: list[Person],
        available_shifts: list[Block]
    ) -> dict[UUID, list[str]]:
        """
        Recommend which faculty should specialize in which shift types.

        Algorithm:
        1. Calculate all pairwise niche overlaps
        2. Identify high-competition pairs (overlap > 0.7)
        3. For each pair, recommend divergence along axis with most flexibility
        4. Assign faculty to non-overlapping shift types
        """
        niches = [self._build_niche(f) for f in faculty]

        # Find high-competition pairs
        high_overlap_pairs = []
        for i, niche_a in enumerate(niches):
            for j, niche_b in enumerate(niches[i+1:], start=i+1):
                overlap = calculate_niche_overlap(niche_a, niche_b)
                if overlap > 0.7:
                    high_overlap_pairs.append((i, j, overlap))

        # Recommend partitioning
        recommendations = {}
        for i, j, overlap in high_overlap_pairs:
            faculty_a = faculty[i]
            faculty_b = faculty[j]

            # Find axis with most divergence potential
            divergence_axis = self._find_divergence_axis(niches[i], niches[j])

            recommendations[faculty_a.id] = {
                "message": f"High niche overlap ({overlap:.0%}) with {faculty_b.name}",
                "suggestion": f"Consider specializing in {divergence_axis['high_value']} shifts",
                "alternative": f"Or shift to {divergence_axis['low_competition']} rotation",
            }

        return recommendations

    def _find_divergence_axis(
        self,
        niche_a: SchedulingNiche,
        niche_b: SchedulingNiche
    ) -> dict:
        """
        Identify which resource axis has potential for partitioning.

        Strategy: Find axis where preferences are similar but resources are abundant,
        so one faculty can shift without loss of satisfaction.
        """
        # Example: Both prefer mornings, but afternoons are understaffed
        # Recommend one shift to afternoons
        pass
```

#### 2.3 Niche Expansion During Crisis

**Ecological analogy:** During resource scarcity, specialists become generalists to survive.

```python
class CrisisNicheExpansion:
    """
    During emergencies, temporarily expand faculty niches.

    Ecological principle: "Realized niche" (actual) vs "fundamental niche" (potential).
    Under stress, species expand into less-preferred niches to survive.
    """

    def expand_niches_for_crisis(
        self,
        faculty: list[Person],
        crisis_severity: float  # 0.0-1.0
    ) -> dict[UUID, SchedulingNiche]:
        """
        Temporarily expand niches based on crisis severity.

        Severity 0.3: Ask specialists to cover adjacent niches (clinic → inpatient)
        Severity 0.7: All faculty expand to generalist mode
        Severity 1.0: Ignore all preferences (emergency override)
        """
        expanded_niches = {}

        for f in faculty:
            original_niche = self._get_niche(f.id)

            # Calculate expansion factor
            expansion = min(1.0, crisis_severity * 1.5)

            # Flatten preference variance (specialist → generalist)
            expanded = SchedulingNiche(
                faculty_id=f.id,
                time_of_day_prefs={
                    k: self._flatten_toward_neutral(v, expansion)
                    for k, v in original_niche.time_of_day_prefs.items()
                },
                # ... same for other axes
            )

            expanded_niches[f.id] = expanded

        return expanded_niches

    def _flatten_toward_neutral(self, preference: float, factor: float) -> float:
        """
        Move preference toward 0.5 (neutral) based on factor.

        Examples:
        - preference=0.9, factor=0.5 → 0.7 (still prefer, but less strong)
        - preference=0.2, factor=1.0 → 0.5 (forced to neutral)
        """
        neutral = 0.5
        return preference + (neutral - preference) * factor
```

### Warning Signs and Metrics

| Warning Sign | Metric | Threshold | Action |
|--------------|--------|-----------|--------|
| **High niche overlap** | Mean pairwise overlap | > 0.6 | Recommend specialization, hire complementary skills |
| **Abandoned niches** | Shift types with no specialists | Any rotation < 0.3 avg preference | Recruit specialist or incentivize niche shift |
| **Over-specialization** | Team mean niche breadth | < 0.25 | Cross-train generalists for resilience |
| **Niche compression** | Realized niche << fundamental niche | Faculty consistently working outside preferences | Investigate workload imbalance, burnout risk |

**Dashboard Metrics:**
```python
@dataclass
class NichePartitioningReport:
    team_niche_diversity: float  # Higher = better coverage
    high_overlap_pairs: list[tuple[str, str, float]]  # Faculty pairs competing
    underserved_niches: list[str]  # Shift types no one wants
    overserved_niches: list[str]  # Shift types everyone wants

    # Recommendations
    hiring_needs: dict[str, str]  # Niche → job description
    cross_training_suggestions: list[tuple[str, str]]  # (Faculty, target niche)

    # Health indicator
    partitioning_health: str  # "healthy", "competitive", "critical_gaps"
```

---

## 3. Carrying Capacity

### Core Ecological Principle

**Carrying capacity (K)** is the maximum population size an environment can sustain indefinitely given available resources:

- **Logistic growth**: Population grows exponentially until approaching K, then levels off
- **Density dependence**: Birth rates decline and death rates increase as population approaches K
- **Overshoot and collapse**: Exceeding K temporarily leads to resource depletion and population crash

**Limiting factors** that determine K:
- Food availability
- Water
- Shelter
- Disease
- Predation

**Formula:** `dN/dt = rN(1 - N/K)` where N = population, r = growth rate, K = carrying capacity

### Mapping to Workforce/Scheduling

**Faculty = Population, Shifts = Resources, Patient Demand = Environment**

Carrying capacity maps directly to **maximum sustainable staffing levels** before quality degrades:

| Ecological Concept | Scheduling Equivalent |
|-------------------|----------------------|
| **Population (N)** | Active faculty count |
| **Carrying capacity (K)** | Maximum sustainable faculty given resources (budget, space, preceptors) |
| **Resources** | Clinical sites, patient volume, supervision capacity, budget |
| **Overshoot** | Over-hiring faculty without adequate patient volume or supervision |
| **Collapse** | Faculty leave due to insufficient clinical material or poor mentorship |

**Key Insight:** Carrying capacity is NOT just patient volume—it's multi-factorial:
- **Clinical volume**: Need enough patients for faculty to stay proficient
- **Physical space**: Clinic rooms, OR time, desk space
- **Administrative capacity**: Coordinators, IT support
- **Supervisory capacity**: Senior faculty to train junior faculty
- **Budget constraints**: Salary pool, benefits

### Specific Implementation Ideas

#### 3.1 Multi-Factor Carrying Capacity Model

**Location:** `backend/app/resilience/carrying_capacity.py`

```python
@dataclass
class CarryingCapacityFactors:
    """Factors that limit maximum sustainable faculty count."""

    # Resource constraints
    patient_volume_annual: int  # Total patient encounters available
    clinic_rooms: int
    OR_time_hours_weekly: float
    inpatient_beds: int

    # Support infrastructure
    coordinator_capacity: int  # Faculty per coordinator (1:10 ratio typical)
    IT_support_capacity: int   # Faculty per IT staff
    admin_staff_count: int

    # Financial
    salary_budget_annual: float
    benefits_budget_annual: float

    # Training capacity (for academic programs)
    senior_faculty_count: int  # Needed to supervise junior faculty
    preceptor_ratio: float     # Junior faculty per senior (e.g., 2:1)

    # Physical space
    office_space_sqft: int
    shared_workspace_seats: int

def calculate_carrying_capacity(
    factors: CarryingCapacityFactors
) -> dict[str, int]:
    """
    Calculate maximum sustainable faculty across multiple limiting factors.

    Returns the MINIMUM across all constraints (Liebig's Law of the Minimum).
    """
    constraints = {}

    # Patient volume constraint
    # Assume 1 faculty needs 1200 patient encounters/year to stay proficient
    constraints["patient_volume"] = factors.patient_volume_annual // 1200

    # Clinic room constraint
    # Assume 1 room supports 4 faculty (shared scheduling)
    constraints["clinic_rooms"] = factors.clinic_rooms * 4

    # Coordinator constraint
    # 1 coordinator can manage 10 faculty
    constraints["coordinator_capacity"] = factors.coordinator_capacity * 10

    # Budget constraint
    # Assume average faculty costs $250k total compensation
    avg_faculty_cost = 250000
    constraints["budget"] = int(
        (factors.salary_budget_annual + factors.benefits_budget_annual) / avg_faculty_cost
    )

    # Supervision constraint (academic programs)
    # 1 senior faculty can supervise 2 junior faculty
    # Total faculty = senior + junior, where junior = 2 * senior
    # So total = senior + 2*senior = 3*senior
    constraints["supervision"] = int(factors.senior_faculty_count * (1 + factors.preceptor_ratio))

    # Return limiting factor
    limiting_factor = min(constraints, key=constraints.get)
    carrying_capacity = constraints[limiting_factor]

    return {
        "carrying_capacity_K": carrying_capacity,
        "limiting_factor": limiting_factor,
        "all_constraints": constraints,
        "headroom": carrying_capacity - factors.get("current_faculty_count", 0),
        "utilization_of_K": factors.get("current_faculty_count", 0) / carrying_capacity,
    }
```

#### 3.2 Overshoot Detection and Warning System

**Ecological principle:** Populations that exceed K experience boom-bust cycles.

```python
class CarryingCapacityMonitor:
    """Monitor for carrying capacity overshoot."""

    # Utilization thresholds (as % of K)
    HEALTHY_RANGE = (0.6, 0.85)      # 60-85% of K
    WARNING_THRESHOLD = 0.90          # 90% of K
    OVERSHOOT_THRESHOLD = 1.0         # Exceeded K
    CRITICAL_OVERSHOOT = 1.15         # 15% over K

    def check_overshoot_status(
        self,
        current_faculty: int,
        carrying_capacity_K: int,
        limiting_factor: str
    ) -> dict:
        """
        Detect if system is in overshoot.

        Returns status and recommended actions.
        """
        utilization = current_faculty / carrying_capacity_K

        if utilization < self.HEALTHY_RANGE[0]:
            status = "UNDERUTILIZED"
            severity = "low"
            actions = [
                f"Operating at {utilization:.0%} of carrying capacity",
                "Consider recruiting additional faculty",
                f"Could sustainably add {int(carrying_capacity_K * 0.75 - current_faculty)} faculty",
            ]

        elif utilization <= self.HEALTHY_RANGE[1]:
            status = "HEALTHY"
            severity = "none"
            actions = ["Operating within sustainable range"]

        elif utilization <= self.WARNING_THRESHOLD:
            status = "WARNING"
            severity = "medium"
            actions = [
                f"Approaching carrying capacity ({utilization:.0%} of K)",
                f"Limiting factor: {limiting_factor}",
                "Review resource expansion before next hire",
            ]

        elif utilization <= self.OVERSHOOT_THRESHOLD:
            status = "AT_CAPACITY"
            severity = "high"
            actions = [
                "At carrying capacity limit",
                f"MUST expand {limiting_factor} before hiring",
                "Risk of quality degradation if exceeded",
            ]

        else:  # Overshoot
            status = "OVERSHOOT"
            severity = "critical" if utilization >= self.CRITICAL_OVERSHOOT else "high"
            overshoot_pct = (utilization - 1.0) * 100

            actions = [
                f"OVERSHOOT: {overshoot_pct:.0f}% over carrying capacity",
                f"Limiting factor '{limiting_factor}' exhausted",
                "Expect resource conflicts, quality degradation, faculty dissatisfaction",
                "URGENT: Expand resources or reduce faculty count",
            ]

            # Predict collapse if not addressed
            if utilization >= self.CRITICAL_OVERSHOOT:
                actions.append(
                    "CRITICAL: Risk of faculty attrition cascade (collapse)"
                )

        return {
            "status": status,
            "severity": severity,
            "utilization_of_K": utilization,
            "overshoot_amount": max(0, current_faculty - carrying_capacity_K),
            "actions": actions,
            "limiting_factor": limiting_factor,
        }
```

#### 3.3 Dynamic Carrying Capacity (Seasonal Variation)

**Ecological principle:** Carrying capacity fluctuates with seasons and environmental conditions.

```python
class DynamicCarryingCapacity:
    """
    Model time-varying carrying capacity.

    Factors that change K:
    - Academic calendar (resident rotations change patient volume)
    - Seasonal patient demand (flu season, summer trauma season)
    - Budget cycles (fiscal year constraints)
    - Temporary facility changes (renovations reduce clinic rooms)
    """

    def calculate_time_varying_K(
        self,
        base_factors: CarryingCapacityFactors,
        date: datetime
    ) -> int:
        """
        Calculate carrying capacity for a specific time period.
        """
        # Start with base calculation
        base_K = calculate_carrying_capacity(base_factors)["carrying_capacity_K"]

        # Apply seasonal modifiers
        month = date.month

        # Example: Patient volume varies
        patient_volume_modifier = {
            12: 1.2, 1: 1.2, 2: 1.1,  # Winter (flu season)
            3: 1.0, 4: 1.0, 5: 1.0,   # Spring (normal)
            6: 0.85, 7: 0.85, 8: 0.85,  # Summer (lower volume)
            9: 1.0, 10: 1.1, 11: 1.15,  # Fall (increasing)
        }[month]

        # Academic year modifiers (if residency program)
        # June-July: New residents arrive, need more supervision
        if month in [6, 7]:
            supervision_modifier = 0.8  # Need more senior coverage
        else:
            supervision_modifier = 1.0

        # Combine modifiers
        adjusted_K = int(base_K * patient_volume_modifier * supervision_modifier)

        return adjusted_K
```

#### 3.4 Carrying Capacity Expansion Planner

```python
class CapacityExpansionPlanner:
    """Plan resource expansions to increase carrying capacity."""

    def recommend_expansion_strategy(
        self,
        current_factors: CarryingCapacityFactors,
        target_faculty_count: int
    ) -> dict:
        """
        Determine what resources to expand to support target faculty count.

        Returns ROI-optimized expansion plan.
        """
        current_K = calculate_carrying_capacity(current_factors)
        current_capacity = current_K["carrying_capacity_K"]

        if target_faculty_count <= current_capacity:
            return {"message": "No expansion needed", "current_headroom": current_capacity - target_faculty_count}

        # Calculate shortfall
        shortfall = target_faculty_count - current_capacity
        limiting_factor = current_K["limiting_factor"]

        # Expansion costs (example values)
        expansion_costs = {
            "patient_volume": {
                "cost_per_unit": 50000,  # Marketing, outreach per 1200 encounters
                "units_needed": shortfall,
                "description": "Increase patient volume through marketing and access expansion",
            },
            "clinic_rooms": {
                "cost_per_unit": 150000,  # Construction/lease cost per room
                "units_needed": int(shortfall / 4) + 1,  # 1 room supports 4 faculty
                "description": "Add clinic examination rooms",
            },
            "coordinator_capacity": {
                "cost_per_unit": 75000,  # Salary + benefits for coordinator
                "units_needed": int(shortfall / 10) + 1,  # 1 coordinator per 10 faculty
                "description": "Hire additional program coordinators",
            },
            "budget": {
                "cost_per_unit": 250000,  # Average faculty total compensation
                "units_needed": shortfall,
                "description": "Increase salary budget",
            },
        }

        # Recommend addressing limiting factor first
        limiting_expansion = expansion_costs[limiting_factor]
        total_cost = limiting_expansion["cost_per_unit"] * limiting_expansion["units_needed"]

        return {
            "target_faculty": target_faculty_count,
            "current_capacity": current_capacity,
            "shortfall": shortfall,
            "limiting_factor": limiting_factor,
            "expansion_plan": {
                "primary_investment": limiting_factor,
                "units_needed": limiting_expansion["units_needed"],
                "total_cost": total_cost,
                "cost_per_faculty_enabled": total_cost / shortfall,
                "description": limiting_expansion["description"],
            },
            "timeline_estimate_months": limiting_expansion["units_needed"] * 3,  # 3 months per unit
        }
```

### Warning Signs and Metrics

| Warning Sign | Metric | Threshold | Action |
|--------------|--------|-----------|--------|
| **Approaching capacity** | Faculty / K | > 0.85 | Pause hiring, plan expansion |
| **Overshoot** | Faculty / K | > 1.0 | Urgent: Expand resources or freeze hiring |
| **Critical overshoot** | Faculty / K | > 1.15 | Emergency: Expect attrition, quality degradation |
| **Underutilization** | Faculty / K | < 0.6 | Inefficient, consider recruiting or reducing resources |
| **Constraint imbalance** | Max constraint / Min constraint | > 2.0 | Resources misallocated, rebalance investments |

**Dashboard Metrics:**
```python
@dataclass
class CarryingCapacityReport:
    carrying_capacity_K: int
    current_faculty_N: int
    utilization_of_K: float

    limiting_factor: str  # Which resource is constraining K
    headroom: int  # Faculty slots available before hitting K

    # All constraint limits
    constraint_breakdown: dict[str, int]

    # Status
    overshoot_status: str  # "healthy", "warning", "at_capacity", "overshoot"
    severity: str

    # Trends
    K_6_months_ago: int
    K_trend: str  # "increasing", "stable", "decreasing"

    # Recommendations
    recommended_actions: list[str]
    expansion_plan: Optional[dict]

    # Predictive
    months_until_K_exhausted: Optional[int]  # Based on hiring rate
```

---

## 4. Predator-Prey Dynamics (Lotka-Volterra)

### Core Ecological Principle

**Lotka-Volterra equations** model oscillating population dynamics between predators and prey:

**Prey equation:** `dx/dt = αx - βxy`
- Prey (x) grow exponentially (αx) when alone
- Prey decrease when consumed by predators (βxy)

**Predator equation:** `dy/dt = δxy - γy`
- Predators (y) starve without prey (−γy)
- Predators increase when eating prey (δxy)

**Key Dynamics:**
- **Oscillating cycles**: Prey increase → Predators increase → Prey decrease → Predators decrease → Cycle repeats
- **Phase lag**: Predator peaks lag behind prey peaks
- **Equilibrium**: Stable point exists but rarely achieved
- **Amplitude**: Depends on parameters (α, β, γ, δ)

**Real example:** Lynx and snowshoe hare populations in Canada oscillate with ~10-year cycles.

### Mapping to Workforce/Scheduling

This is the most abstract mapping, but powerful for modeling **demand oscillations**:

| Ecological | Scheduling Equivalent |
|-----------|----------------------|
| **Prey** | Open shift slots (demand) |
| **Predators** | Available faculty (supply) |
| **Consumption** | Faculty filling shifts (supply meeting demand) |

**Alternative Mapping (More Intuitive):**

| Ecological | Scheduling Equivalent |
|-----------|----------------------|
| **Prey** | Faculty availability (supply) |
| **Predators** | Shift demand / patient volume |
| **Consumption** | Demand "consuming" faculty time |

**Real-World Oscillations in Scheduling:**
1. **Resident rotations** create demand waves (every 4 weeks, new rotation = new coverage needs)
2. **Seasonal patient volume** (flu season → high demand → burnout → resignations → understaffing)
3. **Faculty burnout-recovery cycles** (high workload → burnout → time off → return → repeat)
4. **Hiring lag effects** (shortage → hire → overstaffing → hiring freeze → shortage)

### Specific Implementation Ideas

#### 4.1 Demand-Supply Oscillation Detector

**Location:** `backend/app/resilience/lotka_volterra.py`

Model the feedback loop between shift demand and faculty supply:

```python
@dataclass
class LotkaVolterraParams:
    """Parameters for predator-prey scheduling dynamics."""

    # Prey (shift demand) parameters
    alpha: float  # Intrinsic demand growth rate (patient volume increase)
    beta: float   # Rate at which faculty "consume" (fill) shifts

    # Predator (faculty supply) parameters
    gamma: float  # Faculty attrition rate (burnout, resignation)
    delta: float  # Faculty recruitment rate (response to demand)

    # Typical values (estimated)
    # alpha = 0.05 (demand grows 5%/month if unmet)
    # beta = 0.8 (faculty can fill 80% of encountered shifts)
    # gamma = 0.02 (2% monthly attrition baseline)
    # delta = 0.1 (recruitment responsive to demand)

def simulate_demand_supply_dynamics(
    initial_shifts: int,
    initial_faculty: int,
    params: LotkaVolterraParams,
    time_steps: int = 36  # Months
) -> list[dict]:
    """
    Simulate Lotka-Volterra dynamics for scheduling.

    Returns time series of (shifts, faculty) over time.
    Useful for predicting oscillations and planning hiring.
    """
    results = []

    shifts = initial_shifts  # x (prey)
    faculty = initial_faculty  # y (predator)

    for month in range(time_steps):
        # Record state
        results.append({
            "month": month,
            "open_shifts": shifts,
            "available_faculty": faculty,
            "coverage_ratio": faculty / shifts if shifts > 0 else float('inf'),
            "stress_level": max(0, (shifts - faculty * 40) / shifts) if shifts > 0 else 0,
        })

        # Lotka-Volterra updates (discrete time approximation)
        dt = 1  # 1 month timestep

        # Shift demand dynamics
        # dx/dt = α*x - β*x*y
        # Demand grows naturally but is reduced when filled by faculty
        d_shifts = (params.alpha * shifts - params.beta * shifts * faculty) * dt

        # Faculty supply dynamics
        # dy/dt = δ*x*y - γ*y
        # Faculty grow when demand is high, decline due to attrition
        d_faculty = (params.delta * shifts * faculty - params.gamma * faculty) * dt

        # Update populations
        shifts = max(0, shifts + d_shifts)
        faculty = max(0, faculty + d_faculty)

    return results

def detect_oscillation_pattern(
    time_series: list[dict]
) -> dict:
    """
    Analyze time series for oscillation characteristics.

    Returns:
    - Oscillation period (months between peaks)
    - Amplitude (peak-to-trough variation)
    - Phase relationship (lag between demand and supply peaks)
    - Stability (damped, stable, or growing oscillations)
    """
    shifts_series = [t["open_shifts"] for t in time_series]
    faculty_series = [t["available_faculty"] for t in time_series]

    # Find peaks
    shift_peaks = find_peaks(shifts_series)
    faculty_peaks = find_peaks(faculty_series)

    # Calculate period
    if len(shift_peaks) >= 2:
        periods = [shift_peaks[i+1] - shift_peaks[i] for i in range(len(shift_peaks)-1)]
        avg_period = sum(periods) / len(periods)
    else:
        avg_period = None

    # Calculate amplitude
    shift_amplitude = (max(shifts_series) - min(shifts_series)) / max(shifts_series)
    faculty_amplitude = (max(faculty_series) - min(faculty_series)) / max(faculty_series)

    # Detect stability
    # Compare first-half vs second-half amplitude
    mid = len(time_series) // 2
    early_amp = max(shifts_series[:mid]) - min(shifts_series[:mid])
    late_amp = max(shifts_series[mid:]) - min(shifts_series[mid:])

    if late_amp < early_amp * 0.8:
        stability = "damped"  # Oscillations decreasing (approaching equilibrium)
    elif late_amp > early_amp * 1.2:
        stability = "growing"  # Oscillations increasing (unstable)
    else:
        stability = "stable"  # Constant amplitude

    return {
        "oscillation_detected": avg_period is not None,
        "period_months": avg_period,
        "shift_amplitude": shift_amplitude,
        "faculty_amplitude": faculty_amplitude,
        "stability": stability,
        "equilibrium_reached": stability == "damped" and late_amp < 0.1,
    }
```

#### 4.2 Oscillation Damping Strategies

**Goal:** Reduce boom-bust cycles through strategic interventions.

```python
class OscillationDampingService:
    """
    Strategies to dampen predator-prey oscillations in scheduling.

    Ecological interventions that stabilize populations:
    1. Buffer prey population (maintain shift buffer)
    2. Smooth predator response (gradual hiring, not panic hiring)
    3. Introduce storage (vacation banks, flex pools)
    """

    def recommend_damping_strategy(
        self,
        oscillation_analysis: dict,
        current_state: dict
    ) -> dict:
        """
        Recommend interventions to reduce oscillation amplitude.
        """
        strategies = []

        # Strategy 1: Maintain demand buffer
        if oscillation_analysis["shift_amplitude"] > 0.3:
            strategies.append({
                "intervention": "Demand Buffer",
                "description": "Maintain 15-20% buffer of unfilled shifts to absorb demand spikes",
                "implementation": "Don't schedule 100% of capacity; keep 15% open for flex",
                "ecological_analog": "Carrying capacity headroom prevents overshoot",
            })

        # Strategy 2: Smooth hiring response
        if oscillation_analysis["faculty_amplitude"] > 0.25:
            strategies.append({
                "intervention": "Smoothed Hiring",
                "description": "Avoid panic hiring during peaks; use predictive hiring based on trends",
                "implementation": "Moving average of 6-month demand, hire proactively not reactively",
                "ecological_analog": "Reduce predator numerical response to prey fluctuations",
            })

        # Strategy 3: Introduce storage mechanisms
        strategies.append({
            "intervention": "Temporal Buffering",
            "description": "Build vacation banks and flex pools to smooth supply over time",
            "implementation": "Faculty can bank overtime during low-demand periods, use during peaks",
            "ecological_analog": "Food caching by predators smooths consumption",
        })

        # Strategy 4: External stabilization (locum tenens)
        if oscillation_analysis["stability"] == "growing":
            strategies.append({
                "intervention": "External Supply",
                "description": "Use locum tenens / per-diem pool to absorb demand spikes without permanent hiring",
                "implementation": "Maintain contract with locum agency for 10-15% flex capacity",
                "ecological_analog": "Immigration from external populations stabilizes local dynamics",
            })

        return {
            "oscillation_risk": oscillation_analysis["stability"],
            "damping_strategies": strategies,
            "priority": "high" if oscillation_analysis["stability"] == "growing" else "medium",
        }
```

#### 4.3 Phase-Lag Prediction

**Ecological insight:** Predator peaks lag behind prey peaks by a predictable amount.

```python
class PhaseLagPredictor:
    """
    Predict when faculty shortages will occur based on demand phase.

    If demand peaked 3 months ago, faculty burnout/attrition peak is imminent.
    Use this to proactively schedule relief.
    """

    def predict_burnout_peak(
        self,
        recent_demand_history: list[dict],
        typical_lag_months: int = 2
    ) -> dict:
        """
        Predict when faculty stress will peak based on demand cycles.

        Args:
            recent_demand_history: Last 12 months of shift demand data
            typical_lag_months: Typical lag between demand peak and burnout peak

        Returns:
            Prediction of burnout timing and severity
        """
        # Find most recent demand peak
        demand_values = [h["shift_count"] for h in recent_demand_history]
        peak_idx = demand_values.index(max(demand_values))
        peak_month = recent_demand_history[peak_idx]["month"]

        # Current month
        current_month = recent_demand_history[-1]["month"]
        months_since_peak = (current_month.year - peak_month.year) * 12 + \
                           (current_month.month - peak_month.month)

        # Predict burnout peak
        burnout_peak_month = peak_month + timedelta(days=30 * typical_lag_months)
        months_until_burnout_peak = typical_lag_months - months_since_peak

        if months_until_burnout_peak <= 0:
            status = "CURRENT" if months_until_burnout_peak >= -1 else "PAST"
        else:
            status = "UPCOMING"

        return {
            "demand_peak_month": peak_month,
            "predicted_burnout_peak": burnout_peak_month,
            "months_until_burnout_peak": months_until_burnout_peak,
            "status": status,
            "recommended_action": self._get_phase_action(status, months_until_burnout_peak),
        }

    def _get_phase_action(self, status: str, months_until: int) -> str:
        if status == "UPCOMING":
            if months_until == 1:
                return "URGENT: Schedule relief shifts, activate backup pool NOW"
            elif months_until == 2:
                return "Prepare relief coverage, contact locum agency, plan vacation coverage"
            else:
                return "Monitor closely, prepare contingency plans"
        elif status == "CURRENT":
            return "CRITICAL: Implement all relief measures, expect increased sick calls"
        else:
            return "Recovery phase: Monitor for attrition, conduct retention interviews"
```

### Warning Signs and Metrics

| Warning Sign | Metric | Threshold | Action |
|--------------|--------|-----------|--------|
| **Growing oscillations** | Amplitude ratio (late/early) | > 1.2 | Implement damping strategies urgently |
| **High-amplitude cycles** | Peak-to-trough variation | > 30% | Add flex capacity, smooth hiring |
| **Short cycle period** | Months between peaks | < 4 months | System too reactive, increase response time |
| **Phase-lag exhaustion** | Months since demand peak | 2-3 months | Predict burnout wave, activate relief |

**Dashboard Metrics:**
```python
@dataclass
class LotkaVolterraReport:
    oscillation_detected: bool
    cycle_period_months: Optional[float]

    # Current phase
    current_phase: str  # "demand_rising", "demand_peak", "demand_falling", "equilibrium"
    predicted_next_peak: datetime
    predicted_burnout_peak: datetime

    # Oscillation characteristics
    demand_amplitude: float
    supply_amplitude: float
    stability_trend: str  # "damped", "stable", "growing"

    # Interventions
    damping_strategies: list[dict]
    immediate_actions: list[str]

    # Simulation results
    forecasted_next_12_months: list[dict]  # Month-by-month predictions
```

---

## 5. Keystone Species

### Core Ecological Principle

**Keystone species** are organisms whose impact on ecosystem structure and function is disproportionately large relative to their abundance:

- **Definition**: Species whose removal causes dramatic ecosystem changes
- **Distinguishing feature**: Effect >> biomass (10x-100x impact)
- **Classic examples**:
  - Sea otters: Control sea urchin populations → Protect kelp forests
  - Wolves in Yellowstone: Control elk → Prevent overgrazing → Riparian recovery
  - Fig trees: Provide fruit year-round → Support entire frugivore community

**Keystone vs Dominant Species:**
- **Dominant**: High abundance, large biomass (e.g., oak trees in forest)
- **Keystone**: Low abundance, critical function (e.g., beavers creating wetlands)

**Mechanisms:**
- **Predation**: Control prey populations
- **Engineering**: Modify habitat (beavers, elephants)
- **Mutualism**: Enable other species (pollinators, mycorrhizae)
- **Resource provision**: Unique resources (fig trees, cavity-nesting trees)

### Mapping to Workforce/Scheduling

**Keystone Faculty = Faculty whose removal disproportionately disrupts operations**

This is closely related to "hub faculty" but distinct:
- **Hub faculty**: High connectivity (network centrality)
- **Keystone faculty**: Critical function enabler (unique capabilities)

| Keystone Characteristic | Faculty Equivalent |
|------------------------|-------------------|
| **Unique function** | Only faculty credentialed for specific procedures |
| **Enables others** | Training director who credentials other faculty |
| **Structural role** | Department chair who approves all schedule changes |
| **Rare resource provider** | Only faculty fluent in rare language (ASL, Mandarin) |
| **System engineer** | IT-savvy faculty who maintains scheduling software |

**Real-World Examples:**
1. **Only cardiac anesthesiologist** → Removal stops all cardiac surgeries (not just their shifts)
2. **Training director** → Removal halts all new procedure credentialing (blocks others' advancement)
3. **Ultrasound expert** → Removal means no one can teach ultrasound-guided procedures
4. **Spanish-fluent faculty** → Removal leaves Spanish-speaking patients underserved

### Specific Implementation Ideas

#### 5.1 Keystone Faculty Identification

**Location:** `backend/app/resilience/keystone_analysis.py`

```python
@dataclass
class KeystoneMetrics:
    """Metrics that identify keystone faculty."""

    faculty_id: UUID
    faculty_name: str

    # Unique capability metrics
    unique_credentials_count: int  # Procedures only they can perform
    unique_language_skills: list[str]  # Languages only they speak
    unique_patient_populations: list[str]  # Populations only they serve

    # Enablement metrics (help others work)
    faculty_trained_count: int  # How many faculty they've credentialed
    procedures_taught_count: int  # Procedures they teach
    is_training_director: bool
    is_quality_officer: bool

    # Structural role metrics
    approval_authority: list[str]  # ["schedules", "leave", "swaps"]
    committee_memberships: list[str]
    is_department_chair: bool

    # Dependency metrics (how many people depend on them)
    dependent_faculty_count: int  # Faculty who need their teaching/approval
    dependent_procedures_count: int  # Procedures that require them
    dependent_services_count: int  # Services that can't run without them

    # Calculated keystone score
    @property
    def keystone_score(self) -> float:
        """
        Calculate keystone score (0.0-1.0).

        High score = high impact if removed.
        """
        score = 0.0

        # Unique capabilities (max 0.4 points)
        uniqueness = min(0.4, (
            self.unique_credentials_count * 0.1 +
            len(self.unique_language_skills) * 0.05 +
            len(self.unique_patient_populations) * 0.05
        ))
        score += uniqueness

        # Enablement of others (max 0.3 points)
        enablement = min(0.3, (
            self.faculty_trained_count * 0.02 +
            self.procedures_taught_count * 0.01 +
            (0.1 if self.is_training_director else 0)
        ))
        score += enablement

        # Structural role (max 0.3 points)
        structural = min(0.3, (
            len(self.approval_authority) * 0.1 +
            (0.15 if self.is_department_chair else 0)
        ))
        score += structural

        return min(1.0, score)

    @property
    def keystone_type(self) -> str:
        """Classify type of keystone role."""
        if self.unique_credentials_count >= 2:
            return "UNIQUE_CAPABILITY"
        elif self.is_training_director or self.faculty_trained_count > 5:
            return "ENABLER"
        elif self.is_department_chair or len(self.approval_authority) >= 2:
            return "STRUCTURAL"
        elif len(self.unique_language_skills) > 0 or len(self.unique_patient_populations) > 0:
            return "ACCESS_PROVIDER"
        else:
            return "NONE"

def identify_keystone_faculty(
    faculty: list[Person],
    credentials: list[ProcedureCredential],
    training_records: list[dict]
) -> list[KeystoneMetrics]:
    """
    Identify all keystone faculty in the system.

    Returns ranked list by keystone score.
    """
    keystone_list = []

    for f in faculty:
        # Calculate unique credentials
        unique_creds = count_unique_credentials(f.id, credentials, faculty)

        # Calculate training impact
        faculty_trained = count_faculty_trained(f.id, training_records)

        # Check structural roles
        is_chair = check_department_chair(f.id)
        approval_auth = get_approval_authority(f.id)

        metrics = KeystoneMetrics(
            faculty_id=f.id,
            faculty_name=f.name,
            unique_credentials_count=unique_creds,
            # ... populate all fields
        )

        if metrics.keystone_score >= 0.3:  # Threshold for keystone status
            keystone_list.append(metrics)

    # Sort by score descending
    keystone_list.sort(key=lambda x: x.keystone_score, reverse=True)

    return keystone_list
```

#### 5.2 Keystone Protection Constraint

**Goal:** Prevent over-reliance on keystone faculty and maintain backup capacity.

```python
class KeystoneProtectionConstraint(SoftConstraint):
    """
    Protect keystone faculty from overload and ensure redundancy.

    Similar to HubProtectionConstraint but focused on unique capabilities.
    """

    KEYSTONE_THRESHOLD = 0.3  # Score above which protection activates

    def __init__(self, weight: float = 30.0):
        super().__init__(
            name="KeystoneProtection",
            constraint_type=ConstraintType.KEYSTONE_PROTECTION,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def validate(self, assignments: list, context: SchedulingContext) -> ConstraintResult:
        """
        Check if keystone faculty are over-assigned or lack backup.
        """
        violations = []

        keystone_faculty = context.get("keystone_faculty", [])

        for kf in keystone_faculty:
            if kf.keystone_score < self.KEYSTONE_THRESHOLD:
                continue

            # Count assignments
            faculty_assignments = [a for a in assignments if a.person_id == kf.faculty_id]
            assignment_count = len(faculty_assignments)

            # Check if unique capabilities have backup
            if kf.unique_credentials_count > 0:
                backup_exists = self._check_backup_exists(kf, context)

                if not backup_exists:
                    violations.append(ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"Keystone faculty {kf.faculty_name} has {kf.unique_credentials_count} unique credentials with NO backup",
                        person_id=kf.faculty_id,
                        details={
                            "keystone_score": kf.keystone_score,
                            "keystone_type": kf.keystone_type,
                            "unique_credentials": kf.unique_credentials_count,
                            "recommendation": "Cross-train backup faculty immediately",
                            "risk": "Single point of failure - service closure if unavailable",
                        },
                    ))

        return ConstraintResult(
            satisfied=True,  # Soft constraint
            violations=violations,
            penalty=len(violations) * self.weight * 10,
        )
```

#### 5.3 Keystone Succession Planning

**Ecological analogy:** Ecosystems collapse when keystone species are removed without replacement.

```python
class KeystoneSuccessionPlanner:
    """
    Plan for keystone faculty departure or unavailability.

    Ensures critical functions have trained backups.
    """

    def assess_keystone_risk(
        self,
        keystone_faculty: list[KeystoneMetrics]
    ) -> dict:
        """
        Assess organizational risk from keystone dependencies.
        """
        high_risk = []
        medium_risk = []

        for kf in keystone_faculty:
            # Calculate backup coverage
            backup_score = self._calculate_backup_coverage(kf)

            # Risk = keystone score × (1 - backup coverage)
            risk = kf.keystone_score * (1 - backup_score)

            risk_assessment = {
                "faculty_id": kf.faculty_id,
                "faculty_name": kf.faculty_name,
                "keystone_score": kf.keystone_score,
                "backup_coverage": backup_score,
                "risk_score": risk,
                "keystone_type": kf.keystone_type,
            }

            if risk >= 0.5:
                high_risk.append(risk_assessment)
            elif risk >= 0.3:
                medium_risk.append(risk_assessment)

        return {
            "high_risk_keystones": high_risk,
            "medium_risk_keystones": medium_risk,
            "total_risk_score": sum(r["risk_score"] for r in high_risk + medium_risk),
            "recommendations": self._generate_succession_plan(high_risk),
        }

    def _generate_succession_plan(
        self,
        high_risk_keystones: list[dict]
    ) -> list[dict]:
        """
        Generate action plan to reduce keystone dependency risk.
        """
        plans = []

        for kf in high_risk_keystones:
            if kf["keystone_type"] == "UNIQUE_CAPABILITY":
                plans.append({
                    "faculty": kf["faculty_name"],
                    "action": "Cross-train backup for unique procedures",
                    "timeline": "3-6 months",
                    "priority": "CRITICAL",
                    "steps": [
                        "Identify 2 faculty candidates for cross-training",
                        "Schedule 20 supervised procedure sessions",
                        "Complete competency assessment",
                        "Grant credential to backup faculty",
                    ],
                })

            elif kf["keystone_type"] == "ENABLER":
                plans.append({
                    "faculty": kf["faculty_name"],
                    "action": "Develop co-training director",
                    "timeline": "6-12 months",
                    "priority": "HIGH",
                    "steps": [
                        "Identify successor candidate",
                        "Shadow current training director",
                        "Co-manage credentialing process",
                        "Transfer institutional knowledge",
                    ],
                })

            elif kf["keystone_type"] == "STRUCTURAL":
                plans.append({
                    "faculty": kf["faculty_name"],
                    "action": "Distribute approval authority",
                    "timeline": "1-3 months",
                    "priority": "HIGH",
                    "steps": [
                        "Delegate routine approvals to senior faculty",
                        "Create approval workflows with backup authorization",
                        "Document decision criteria for successors",
                    ],
                })

        return plans
```

#### 5.4 Keystone Impact Simulation

**What happens if keystone faculty leaves?**

```python
class KeystoneRemovalSimulator:
    """
    Simulate ecosystem effects of removing a keystone faculty member.

    Ecological analog: Removing wolves from Yellowstone caused elk overpopulation,
    overgrazing, riparian collapse, loss of songbirds, etc. (trophic cascade)
    """

    def simulate_keystone_removal(
        self,
        keystone_faculty_id: UUID,
        current_schedule: list[Assignment],
        faculty_pool: list[Person]
    ) -> dict:
        """
        Predict cascading effects of keystone faculty departure.
        """
        kf = self._get_keystone_metrics(keystone_faculty_id)

        effects = {
            "direct_effects": [],
            "cascade_effects": [],
            "services_at_risk": [],
            "faculty_blocked": [],
            "mitigation_required": [],
        }

        # Direct effect: Their shifts need coverage
        their_assignments = [a for a in current_schedule if a.person_id == keystone_faculty_id]
        effects["direct_effects"].append({
            "type": "coverage_gap",
            "shifts_affected": len(their_assignments),
            "severity": "high",
        })

        # Cascade effect: Unique credentials
        if kf.unique_credentials_count > 0:
            procedures_lost = self._get_unique_procedures(kf.faculty_id)
            effects["services_at_risk"].extend(procedures_lost)
            effects["cascade_effects"].append({
                "type": "service_closure",
                "procedures": procedures_lost,
                "severity": "critical",
                "description": f"Loss of {len(procedures_lost)} procedure types - no backup trained",
            })

        # Cascade effect: Training/credentialing
        if kf.is_training_director:
            effects["cascade_effects"].append({
                "type": "credentialing_halt",
                "severity": "critical",
                "description": "New procedure credentialing will stop",
                "faculty_blocked": kf.faculty_trained_count,
            })

        # Cascade effect: Approval bottleneck
        if kf.is_department_chair or "schedules" in kf.approval_authority:
            effects["cascade_effects"].append({
                "type": "administrative_bottleneck",
                "severity": "high",
                "description": "Schedule approvals will require interim delegation",
            })

        # Mitigation requirements
        total_severity = self._calculate_total_severity(effects)
        effects["total_severity_score"] = total_severity

        if total_severity >= 0.7:
            effects["mitigation_required"].append("Emergency succession plan - activate immediately")
            effects["mitigation_required"].append("Do not accept resignation without 6-month transition")

        return effects
```

### Warning Signs and Metrics

| Warning Sign | Metric | Threshold | Action |
|--------------|--------|-----------|--------|
| **Critical keystone dependency** | Keystone score with no backup | > 0.5 | URGENT: Cross-train backup |
| **Keystone overload** | Keystone faculty utilization | > 85% | Reduce workload, protect from burnout |
| **Succession gap** | Keystones with no succession plan | Any | Create training/transition plan |
| **Concentrated keystones** | Keystone functions in <3 people | Any | Distribute critical functions |

**Dashboard Metrics:**
```python
@dataclass
class KeystoneReport:
    keystone_faculty: list[KeystoneMetrics]  # Sorted by score

    # Risk assessment
    total_keystone_risk_score: float
    high_risk_keystones: int  # Count with risk > 0.5

    # Coverage
    unique_capabilities_without_backup: int
    critical_functions_without_succession: int

    # Recommendations
    urgent_cross_training_needed: list[dict]
    succession_plans_required: list[dict]

    # Simulation results
    worst_case_removal_impact: dict  # Impact if top keystone leaves
```

---

## 6. Trophic Cascades

### Core Ecological Principle

**Trophic cascades** occur when effects propagate through multiple levels of a food web, typically initiated by changes at the top (apex predators):

**Food Web Levels:**
1. **Apex predators** (wolves, lions)
2. **Herbivores** (elk, deer)
3. **Plants** (grass, trees)
4. **Soil/decomposers**

**Classic Cascade Example - Yellowstone Wolves:**
- **1926**: Wolves extirpated → Elk population explodes
- **Effect on vegetation**: Overgrazing → Riparian zones destroyed
- **Effect on other species**: Beaver decline (no willows), songbird decline (no shrubs)
- **Effect on rivers**: Bank erosion, channel widening (no vegetation)
- **1995**: Wolves reintroduced → Elk population controlled
- **Restoration**: Riparian recovery, beaver return, biodiversity increase

**Key Properties:**
- **Top-down control**: Predators control ecosystem structure
- **Multi-level effects**: Changes propagate 3-4 levels down
- **Non-linear**: Small change at top → Large change at bottom
- **Indirect effects**: Species affected without direct interaction

### Mapping to Workforce/Scheduling

**Trophic Levels in Medical Scheduling:**

| Trophic Level | Scheduling Equivalent | Control Mechanism |
|--------------|----------------------|-------------------|
| **Apex predators** | Administration / Department chairs | Policy, budget, hiring |
| **Herbivores** | Faculty schedulers / Coordinators | Assignment decisions |
| **Plants** | Individual faculty | Accept/decline assignments |
| **Soil** | Residents, support staff | Affected by faculty availability |

**Real-World Cascade Examples:**

**Cascade 1: Budget Cut → Service Closure**
1. Administration cuts budget 10%
2. → Hiring freeze, lose 2 faculty to attrition
3. → Coordinators forced to reduce clinic sessions
4. → Individual faculty overworked, request fewer shifts
5. → Residents lose training opportunities, program quality declines

**Cascade 2: ACGME Policy Change → Workflow Collapse**
1. ACGME enforces stricter 80-hour rule
2. → Coordinators must reduce resident hours
3. → Faculty must cover shifts previously handled by residents
4. → Faculty burnout increases, request more time off
5. → Nurse practitioners hired to fill gaps (different care model)
6. → Patient satisfaction declines (continuity of care disrupted)

**Cascade 3: Senior Faculty Retirement → Training Breakdown**
1. Senior faculty retires (keystone species removal)
2. → Junior faculty lose mentorship and procedure supervision
3. → Procedure credentialing slows (fewer qualified supervisors)
4. → New faculty remain uncredentialed longer
5. → Service capacity constrained (credentialed faculty overworked)
6. → Residents receive less procedural training

### Specific Implementation Ideas

#### 6.1 Cascade Propagation Detector

**Location:** `backend/app/resilience/trophic_cascade.py`

```python
@dataclass
class CascadeLevel:
    """One level in a trophic cascade."""

    level: int  # 0 = initiating event, 1 = first effect, 2 = second effect, etc.
    affected_entity_type: str  # "policy", "faculty", "coordinator", "resident", "patient"
    affected_entities: list[UUID]  # Specific entities affected

    effect_type: str  # "workload_increase", "availability_decrease", "service_closure", etc.
    magnitude: float  # 0.0-1.0 severity

    description: str
    timestamp: datetime

    # Causal link to previous level
    caused_by: Optional[str]  # Reference to parent effect

@dataclass
class TrophicCascade:
    """Complete cascade from initiating event through all effects."""

    cascade_id: UUID
    initiating_event: str  # "budget_cut", "faculty_departure", "policy_change", etc.
    start_date: datetime

    levels: list[CascadeLevel]

    @property
    def cascade_depth(self) -> int:
        """How many levels deep the cascade propagated."""
        return max(level.level for level in self.levels) + 1

    @property
    def total_impact(self) -> float:
        """Cumulative impact across all levels."""
        return sum(level.magnitude for level in self.levels)

    @property
    def is_amplifying(self) -> bool:
        """Check if effects are amplifying (getting worse) through levels."""
        if len(self.levels) < 2:
            return False

        # Compare magnitude of level N vs level N-1
        for i in range(1, len(self.levels)):
            current_level_effects = [l for l in self.levels if l.level == i]
            prev_level_effects = [l for l in self.levels if l.level == i-1]

            current_magnitude = sum(e.magnitude for e in current_level_effects)
            prev_magnitude = sum(e.magnitude for e in prev_level_effects)

            if current_magnitude > prev_magnitude * 1.5:  # 50% amplification
                return True

        return False

class CascadeDetector:
    """Detect and track trophic cascades in scheduling system."""

    def detect_cascade(
        self,
        initiating_event: dict,
        time_window_days: int = 90
    ) -> TrophicCascade:
        """
        Trace effects of an initiating event through the system.

        Args:
            initiating_event: Event that started the cascade (policy change, departure, etc.)
            time_window_days: How long to look for downstream effects

        Returns:
            Complete cascade with all detected levels
        """
        cascade = TrophicCascade(
            cascade_id=uuid.uuid4(),
            initiating_event=initiating_event["type"],
            start_date=initiating_event["timestamp"],
            levels=[],
        )

        # Level 0: Initiating event
        level_0 = CascadeLevel(
            level=0,
            affected_entity_type=initiating_event["entity_type"],
            affected_entities=initiating_event["entities"],
            effect_type=initiating_event["type"],
            magnitude=initiating_event["magnitude"],
            description=initiating_event["description"],
            timestamp=initiating_event["timestamp"],
            caused_by=None,
        )
        cascade.levels.append(level_0)

        # Trace downstream effects
        current_level = 0
        max_depth = 5  # Prevent infinite loops

        while current_level < max_depth:
            next_level_effects = self._find_effects_from_level(
                cascade.levels,
                current_level,
                time_window_days
            )

            if not next_level_effects:
                break  # Cascade terminated

            cascade.levels.extend(next_level_effects)
            current_level += 1

        return cascade

    def _find_effects_from_level(
        self,
        existing_levels: list[CascadeLevel],
        parent_level: int,
        time_window_days: int
    ) -> list[CascadeLevel]:
        """
        Find next-level effects caused by parent level.

        Causal inference rules:
        - Temporal sequence (effect after cause)
        - Spatial/logical connection (affected entities related to causing entities)
        - Magnitude plausibility (effect size reasonable given cause)
        """
        parent_effects = [l for l in existing_levels if l.level == parent_level]
        if not parent_effects:
            return []

        next_effects = []

        for parent in parent_effects:
            # Look for events that occurred after parent, within time window
            if parent.effect_type == "faculty_departure":
                # Expect: increased workload for remaining faculty
                next_effects.extend(self._detect_workload_increase(parent, time_window_days))
                # Expect: service reductions
                next_effects.extend(self._detect_service_reductions(parent, time_window_days))

            elif parent.effect_type == "workload_increase":
                # Expect: burnout, time-off requests, quality decline
                next_effects.extend(self._detect_burnout_signals(parent, time_window_days))

            elif parent.effect_type == "service_reduction":
                # Expect: patient access issues, resident training gaps
                next_effects.extend(self._detect_training_gaps(parent, time_window_days))

        # Set level number for all next effects
        for effect in next_effects:
            effect.level = parent_level + 1

        return next_effects
```

#### 6.2 Cascade Prevention Interventions

**Goal:** Interrupt cascade propagation before it reaches critical levels.

```python
class CascadeInterventionPlanner:
    """
    Design interventions to stop cascades at each level.

    Ecological analog: Reintroducing wolves stopped elk overgr azing cascade.
    """

    INTERVENTION_STRATEGIES = {
        # Level 0: Policy/admin changes
        "budget_cut": {
            "level_0_intervention": "Negotiate budget restoration or phased implementation",
            "level_1_intervention": "Hire temporary/part-time faculty to bridge gap",
            "level_2_intervention": "Implement workload redistribution before burnout",
        },

        # Keystone faculty departure
        "keystone_departure": {
            "level_0_intervention": "Retain faculty with counter-offer, flexible schedule",
            "level_1_intervention": "Activate succession plan, cross-trained backup",
            "level_2_intervention": "Bring in locum tenens for unique procedures",
        },

        # ACGME policy change
        "acgme_policy_change": {
            "level_0_intervention": "Proactive compliance planning before enforcement",
            "level_1_intervention": "Adjust rotation structure to maintain coverage",
            "level_2_intervention": "Hire mid-level providers to offset resident hour reduction",
        },
    }

    def recommend_intervention(
        self,
        cascade: TrophicCascade,
        current_level: int
    ) -> dict:
        """
        Recommend intervention to stop cascade at current level.

        Earlier interventions are more effective (less damage to undo).
        """
        event_type = cascade.initiating_event

        if event_type not in self.INTERVENTION_STRATEGIES:
            return {"message": "No predefined intervention strategy"}

        strategies = self.INTERVENTION_STRATEGIES[event_type]
        intervention_key = f"level_{current_level}_intervention"

        if intervention_key not in strategies:
            intervention_key = f"level_{min(current_level, 2)}_intervention"  # Use closest level

        return {
            "cascade_id": cascade.cascade_id,
            "current_depth": cascade.cascade_depth,
            "current_level": current_level,
            "intervention": strategies[intervention_key],
            "urgency": "CRITICAL" if current_level >= 2 else "HIGH" if current_level >= 1 else "MEDIUM",
            "cost_estimate": self._estimate_intervention_cost(event_type, current_level),
            "effectiveness_probability": max(0.2, 0.9 - (current_level * 0.2)),  # Harder to stop deeper cascades
        }

    def _estimate_intervention_cost(self, event_type: str, level: int) -> str:
        """
        Estimate relative cost of intervention at this level.

        Ecological principle: Prevention cheaper than restoration.
        """
        base_costs = {
            "budget_cut": 100000,
            "keystone_departure": 150000,
            "acgme_policy_change": 200000,
        }

        base = base_costs.get(event_type, 100000)

        # Cost multiplier increases exponentially with depth
        multiplier = 1.5 ** level

        total = int(base * multiplier)

        if total < 100000:
            return f"${total:,} (Low)"
        elif total < 500000:
            return f"${total:,} (Medium)"
        else:
            return f"${total:,} (High)"
```

#### 6.3 Cascade Early Warning System

**Ecological principle:** Detect early indicators before cascade fully develops.

```python
class CascadeEarlyWarning:
    """
    Monitor for early warning signs of trophic cascades.

    Leading indicators that precede full cascade:
    - Faculty retention interviews showing dissatisfaction
    - Budget discussions mentioning cuts
    - Regulatory agencies announcing policy reviews
    - Sudden increase in time-off requests
    """

    def scan_for_cascade_triggers(
        self,
        recent_events: list[dict],
        time_window_days: int = 30
    ) -> list[dict]:
        """
        Scan recent events for cascade trigger patterns.
        """
        warnings = []

        # Pattern 1: Multiple faculty expressing dissatisfaction
        dissatisfaction_events = [
            e for e in recent_events
            if e["type"] in ["retention_interview_negative", "complaint_filed", "exit_survey_poor"]
        ]

        if len(dissatisfaction_events) >= 3:
            warnings.append({
                "warning_type": "FACULTY_DISSATISFACTION_CLUSTER",
                "severity": "HIGH",
                "description": f"{len(dissatisfaction_events)} faculty expressing dissatisfaction in {time_window_days} days",
                "potential_cascade": "keystone_departure",
                "recommended_action": "Conduct retention focus groups, address systemic issues",
                "time_to_cascade": "60-90 days",
            })

        # Pattern 2: Budget discussions
        budget_events = [e for e in recent_events if e["type"] == "budget_discussion"]
        negative_budget_mentions = sum(
            1 for e in budget_events
            if any(word in e["description"].lower() for word in ["cut", "reduce", "freeze"])
        )

        if negative_budget_mentions >= 2:
            warnings.append({
                "warning_type": "BUDGET_PRESSURE",
                "severity": "MEDIUM",
                "description": f"Budget cuts mentioned in {negative_budget_mentions} recent discussions",
                "potential_cascade": "budget_cut",
                "recommended_action": "Develop contingency staffing plan, identify efficiencies",
                "time_to_cascade": "90-180 days",
            })

        # Pattern 3: Workload spike
        workload_events = [
            e for e in recent_events
            if e["type"] == "utilization_report" and e["metrics"]["utilization"] > 0.90
        ]

        if len(workload_events) >= 2:
            warnings.append({
                "warning_type": "SUSTAINED_HIGH_UTILIZATION",
                "severity": "CRITICAL",
                "description": "Utilization > 90% for sustained period",
                "potential_cascade": "burnout_cascade",
                "recommended_action": "Activate relief coverage immediately, reduce elective workload",
                "time_to_cascade": "30-60 days",
            })

        return warnings
```

### Warning Signs and Metrics

| Warning Sign | Metric | Threshold | Action |
|--------------|--------|-----------|--------|
| **Cascade depth** | Number of levels propagated | ≥ 3 levels | URGENT: Intervene immediately |
| **Amplifying cascade** | Level N magnitude / Level N-1 | > 1.5× | Effects accelerating, emergency response |
| **Multiple concurrent cascades** | Active cascades count | ≥ 2 | System instability, crisis mode |
| **Cascade trigger cluster** | Warning signals in 30 days | ≥ 3 | Preventive action required |

**Dashboard Metrics:**
```python
@dataclass
class CascadeMonitoringReport:
    active_cascades: list[TrophicCascade]
    cascade_warnings: list[dict]  # Early warning signals

    # Summary statistics
    total_active_cascades: int
    deepest_cascade_depth: int
    highest_impact_cascade: TrophicCascade

    # Health indicators
    cascade_risk_level: str  # "low", "moderate", "high", "critical"
    amplifying_cascades_count: int

    # Interventions
    recommended_interventions: list[dict]
    urgent_actions: list[str]

    # Historical
    cascades_last_90_days: int
    average_cascade_depth: float
```

---

## 7. Ecological Resilience

### Core Ecological Principle

**Ecological resilience** is the capacity of an ecosystem to absorb disturbance while maintaining its fundamental structure, function, and feedbacks:

**Key Concepts:**

1. **Resilience vs Resistance**
   - **Resistance**: Ability to resist change (stay same during disturbance)
   - **Resilience**: Ability to recover after change (return to baseline)

2. **Domain of Attraction**
   - **Stable state**: Ecosystem configuration (e.g., grassland, forest)
   - **Basin of attraction**: Range of conditions where system stays in stable state
   - **Regime shift**: System crosses threshold into different stable state

3. **Adaptive Capacity**
   - **Diversity**: Multiple species performing similar functions (functional redundancy)
   - **Modularity**: Semi-independent sub-systems (failures contained)
   - **Learning**: System adapts based on past disturbances

**Classic Example - Coral Reef Regime Shift:**
- **Healthy state**: Coral-dominated reef
- **Disturbance**: Overfishing removes herbivorous fish
- **Regime shift**: Algae overgrows coral → Algae-dominated reef
- **Irreversibility**: Difficult to restore coral without removing algae and restoring fish

**Resilience Mechanisms:**
- **Functional redundancy**: Multiple species do same job (if one fails, others compensate)
- **Response diversity**: Species respond differently to same disturbance (not all affected equally)
- **Modularity**: System organized into semi-independent modules (local failure doesn't cascade)

### Mapping to Workforce/Scheduling

**System State = Schedule Configuration**

Scheduling systems have multiple stable states (regimes):

| Regime | Characteristics | Trigger Events |
|--------|----------------|----------------|
| **Normal operations** | 70-85% utilization, all services running, low swap rate | Default state |
| **Stressed but functional** | 85-95% utilization, some services reduced, high swap rate | Temporary understaffing |
| **Crisis mode** | >95% utilization, essential services only, emergency protocols | Major disruption (pandemic, mass departure) |
| **Collapsed** | Cannot maintain essential services, patient care compromised | Unrecovered crisis |

**Regime Shift Example:**
- **Normal → Stressed**: Flu season increases patient volume 20%
- **Stressed → Crisis**: 3 faculty simultaneously take medical leave
- **Crisis → Collapsed**: Unable to recruit replacements, services shut down

**Resilience in Scheduling:**

| Resilience Mechanism | Scheduling Implementation |
|---------------------|-------------------------|
| **Functional redundancy** | Multiple faculty credentialed for same procedures |
| **Response diversity** | Faculty with different availability patterns (some weekday, some weekend) |
| **Modularity** | Zone-based scheduling (failure in one zone doesn't spread) |
| **Adaptive capacity** | Learning from past disruptions, updating protocols |

### Specific Implementation Ideas

#### 7.1 System Regime Detection

**Location:** `backend/app/resilience/regime_detection.py`

```python
@dataclass
class SystemRegime:
    """Stable operating state of the scheduling system."""

    regime_name: str  # "normal", "stressed", "crisis", "collapsed"

    # Defining characteristics
    utilization_range: tuple[float, float]  # Min, max utilization for this regime
    service_coverage: float  # % of services operational (0.0-1.0)
    response_protocols: list[str]  # Active protocols

    # Resilience properties
    basin_of_attraction: float  # How much disturbance regime can absorb (0.0-1.0)
    recovery_time_days: int  # Typical time to return to this regime

    # Regime-specific constraints
    active_constraints: list[str]  # Which constraints are enforced
    suspended_constraints: list[str]  # Which constraints are relaxed

# Define regimes
NORMAL_REGIME = SystemRegime(
    regime_name="normal",
    utilization_range=(0.60, 0.85),
    service_coverage=1.0,
    response_protocols=["standard_scheduling"],
    basin_of_attraction=0.6,  # Can absorb moderate disturbances
    recovery_time_days=7,
    active_constraints=["acgme", "preferences", "equity", "hub_protection"],
    suspended_constraints=[],
)

STRESSED_REGIME = SystemRegime(
    regime_name="stressed",
    utilization_range=(0.85, 0.95),
    service_coverage=0.90,
    response_protocols=["increased_monitoring", "backup_pool_activation"],
    basin_of_attraction=0.3,  # Less stable
    recovery_time_days=14,
    active_constraints=["acgme", "equity"],
    suspended_constraints=["preferences"],  # Preferences relaxed
)

CRISIS_REGIME = SystemRegime(
    regime_name="crisis",
    utilization_range=(0.95, 1.10),
    service_coverage=0.60,  # Only essential services
    response_protocols=["emergency_scheduling", "load_shedding", "external_support"],
    basin_of_attraction=0.1,  # Very unstable
    recovery_time_days=30,
    active_constraints=["acgme"],  # Only regulatory requirements
    suspended_constraints=["preferences", "equity", "hub_protection"],
)

COLLAPSED_REGIME = SystemRegime(
    regime_name="collapsed",
    utilization_range=(1.10, float('inf')),
    service_coverage=0.40,  # Minimal services
    response_protocols=["service_closure", "emergency_transfer"],
    basin_of_attraction=0.0,  # No resilience, seeking to escape
    recovery_time_days=90,
    active_constraints=[],
    suspended_constraints=["acgme", "preferences", "equity"],  # Emergency override
)

class RegimeDetector:
    """Detect current system regime and predict regime shifts."""

    REGIMES = [NORMAL_REGIME, STRESSED_REGIME, CRISIS_REGIME, COLLAPSED_REGIME]

    def identify_current_regime(
        self,
        current_metrics: dict
    ) -> SystemRegime:
        """
        Determine which regime the system is currently in.
        """
        utilization = current_metrics["utilization"]
        service_coverage = current_metrics["service_coverage"]

        # Match to regime based on utilization (primary indicator)
        for regime in self.REGIMES:
            if regime.utilization_range[0] <= utilization < regime.utilization_range[1]:
                return regime

        # Default to collapsed if no match
        return COLLAPSED_REGIME

    def calculate_regime_stability(
        self,
        current_regime: SystemRegime,
        current_metrics: dict,
        recent_disturbances: list[dict]
    ) -> dict:
        """
        Calculate how stable the current regime is.

        Returns distance from regime boundary and risk of regime shift.
        """
        utilization = current_metrics["utilization"]

        # Distance from upper boundary
        distance_to_threshold = current_regime.utilization_range[1] - utilization
        normalized_distance = distance_to_threshold / (
            current_regime.utilization_range[1] - current_regime.utilization_range[0]
        )

        # Calculate disturbance pressure
        disturbance_magnitude = sum(d["magnitude"] for d in recent_disturbances)

        # Stability = basin of attraction - disturbance pressure
        stability = current_regime.basin_of_attraction - (disturbance_magnitude * 0.5)

        # Risk of regime shift
        if stability < 0.1:
            shift_risk = "CRITICAL"
        elif stability < 0.3:
            shift_risk = "HIGH"
        elif stability < 0.5:
            shift_risk = "MODERATE"
        else:
            shift_risk = "LOW"

        return {
            "current_regime": current_regime.regime_name,
            "distance_to_threshold": normalized_distance,
            "basin_of_attraction": current_regime.basin_of_attraction,
            "disturbance_pressure": disturbance_magnitude,
            "stability_index": stability,
            "regime_shift_risk": shift_risk,
            "next_regime_if_crossed": self._get_next_regime(current_regime),
        }

    def _get_next_regime(self, current: SystemRegime) -> str:
        """Determine next regime if threshold crossed."""
        current_idx = self.REGIMES.index(current)
        if current_idx < len(self.REGIMES) - 1:
            return self.REGIMES[current_idx + 1].regime_name
        else:
            return "collapsed"  # Already at worst state
```

#### 7.2 Resilience Diversity Metrics

**Ecological principle:** Diversity provides resilience through redundancy and response variation.

```python
class ResilienceDiversityAnalyzer:
    """
    Measure diversity metrics that confer resilience.

    Three types of diversity:
    1. Functional redundancy: How many faculty can do the same job
    2. Response diversity: How varied are faculty responses to stress
    3. Temporal diversity: Coverage across different time periods
    """

    def calculate_functional_redundancy(
        self,
        faculty: list[Person],
        credentials: list[ProcedureCredential]
    ) -> dict:
        """
        For each procedure/service, count how many faculty can perform it.

        High redundancy = high resilience (losing one faculty doesn't close service).
        """
        procedure_coverage = defaultdict(list)

        for cred in credentials:
            if cred.status == "active":
                procedure_coverage[cred.procedure_type].append(cred.person_id)

        redundancy_scores = {}
        for procedure, faculty_list in procedure_coverage.items():
            count = len(faculty_list)

            if count == 1:
                score = 0.0  # No redundancy
                risk = "CRITICAL"
            elif count == 2:
                score = 0.5  # Minimal redundancy
                risk = "HIGH"
            elif count <= 4:
                score = 0.75  # Moderate redundancy
                risk = "MEDIUM"
            else:
                score = 1.0  # High redundancy
                risk = "LOW"

            redundancy_scores[procedure] = {
                "faculty_count": count,
                "redundancy_score": score,
                "risk_level": risk,
            }

        # Calculate overall redundancy
        avg_redundancy = sum(s["redundancy_score"] for s in redundancy_scores.values()) / len(redundancy_scores)

        critical_procedures = [
            proc for proc, data in redundancy_scores.items()
            if data["risk_level"] == "CRITICAL"
        ]

        return {
            "average_redundancy": avg_redundancy,
            "procedure_redundancy": redundancy_scores,
            "critical_single_points": critical_procedures,
            "resilience_index": avg_redundancy,
        }

    def calculate_response_diversity(
        self,
        faculty: list[Person],
        stress_responses: list[dict]
    ) -> dict:
        """
        Measure diversity in how faculty respond to stress.

        High response diversity means not all faculty react the same way to a disturbance.

        Example:
        - Flu season hits
        - Some faculty volunteer extra shifts (help)
        - Some maintain normal schedule (neutral)
        - Some request time off (stress response)

        Diverse responses = some faculty compensate for others = resilience.
        """
        response_types = defaultdict(int)

        for response in stress_responses:
            response_types[response["response_type"]] += 1

        total = len(stress_responses)
        if total == 0:
            return {"diversity_index": 0.0}

        # Shannon diversity index
        # H = -Σ(p_i * log(p_i))
        # Higher H = more diverse responses
        import math

        h_index = 0.0
        for count in response_types.values():
            p_i = count / total
            if p_i > 0:
                h_index -= p_i * math.log(p_i)

        # Normalize to 0-1 (max H for 3 response types = log(3) ≈ 1.1)
        max_h = math.log(3)
        normalized_h = min(1.0, h_index / max_h)

        return {
            "response_diversity_index": normalized_h,
            "response_breakdown": dict(response_types),
            "resilience_interpretation": "High" if normalized_h > 0.7 else "Moderate" if normalized_h > 0.4 else "Low",
        }
```

#### 7.3 Adaptive Capacity Tracker

**Ecological principle:** Systems that learn from disturbances become more resilient.

```python
class AdaptiveCapacityTracker:
    """
    Track how system adapts and learns from past disturbances.

    Measures:
    - Are protocols updated after incidents?
    - Is cross-training increased after vulnerabilities exposed?
    - Are early warning thresholds adjusted?
    """

    def assess_adaptive_capacity(
        self,
        past_disturbances: list[dict],
        post_disturbance_actions: list[dict]
    ) -> dict:
        """
        Measure how well the system learns from past events.
        """
        learning_indicators = {
            "protocols_updated": 0,
            "cross_training_initiated": 0,
            "resource_capacity_increased": 0,
            "early_warning_thresholds_adjusted": 0,
            "no_action_taken": 0,
        }

        for disturbance in past_disturbances:
            disturbance_id = disturbance["id"]

            # Find actions taken in response
            related_actions = [
                a for a in post_disturbance_actions
                if a["triggered_by"] == disturbance_id
            ]

            if not related_actions:
                learning_indicators["no_action_taken"] += 1
                continue

            # Categorize actions
            for action in related_actions:
                if action["action_type"] == "protocol_update":
                    learning_indicators["protocols_updated"] += 1
                elif action["action_type"] == "cross_training":
                    learning_indicators["cross_training_initiated"] += 1
                elif action["action_type"] == "capacity_expansion":
                    learning_indicators["resource_capacity_increased"] += 1
                elif action["action_type"] == "threshold_adjustment":
                    learning_indicators["early_warning_thresholds_adjusted"] += 1

        # Calculate adaptive capacity score
        total_disturbances = len(past_disturbances)
        if total_disturbances == 0:
            return {"adaptive_capacity_score": 1.0, "note": "No disturbances to learn from"}

        learning_rate = (total_disturbances - learning_indicators["no_action_taken"]) / total_disturbances

        # Quality of learning (weighted by action type)
        action_weights = {
            "protocols_updated": 0.3,
            "cross_training_initiated": 0.4,  # Highest weight (prevents future issues)
            "resource_capacity_increased": 0.35,
            "early_warning_thresholds_adjusted": 0.25,
        }

        weighted_learning_score = sum(
            learning_indicators[action] * action_weights[action]
            for action in action_weights.keys()
        ) / total_disturbances

        adaptive_capacity_score = (learning_rate + weighted_learning_score) / 2

        return {
            "adaptive_capacity_score": adaptive_capacity_score,
            "learning_rate": learning_rate,
            "learning_indicators": learning_indicators,
            "resilience_trend": "Improving" if adaptive_capacity_score > 0.7 else "Stagnant" if adaptive_capacity_score > 0.4 else "Declining",
        }
```

#### 7.4 Regime Shift Prevention

**Ecological principle:** Prevent regime shifts before crossing irreversible thresholds.

```python
class RegimeShiftPrevention:
    """
    Monitor for signs of impending regime shift and intervene.

    Early warning signals (Scheffer et al. 2009):
    - Critical slowing down: System takes longer to recover from small disturbances
    - Increased variance: System becomes more variable/erratic
    - Flickering: Brief excursions to alternative state
    """

    def detect_early_warning_signals(
        self,
        time_series: list[dict],
        window_size: int = 30  # days
    ) -> dict:
        """
        Detect statistical early warning signals of regime shift.
        """
        # Extract metrics time series
        utilization_series = [t["utilization"] for t in time_series]

        warnings = {}

        # Signal 1: Critical slowing down
        # Measured as autocorrelation (current value predicts next value)
        autocorr = self._calculate_autocorrelation(utilization_series, lag=1)

        if autocorr > 0.7:
            warnings["critical_slowing_down"] = {
                "detected": True,
                "autocorrelation": autocorr,
                "interpretation": "System recovering more slowly from disturbances",
                "risk": "HIGH",
            }

        # Signal 2: Increased variance
        # Compare recent variance to historical baseline
        recent_variance = self._variance(utilization_series[-window_size:])
        historical_variance = self._variance(utilization_series[:-window_size])

        if recent_variance > historical_variance * 1.5:
            warnings["increased_variance"] = {
                "detected": True,
                "recent_variance": recent_variance,
                "historical_variance": historical_variance,
                "ratio": recent_variance / historical_variance,
                "interpretation": "System becoming more erratic and unpredictable",
                "risk": "MEDIUM",
            }

        # Signal 3: Flickering (brief excursions across threshold)
        threshold = 0.95  # Crisis threshold
        flicker_count = self._count_threshold_crossings(utilization_series[-window_size:], threshold)

        if flicker_count >= 3:
            warnings["flickering"] = {
                "detected": True,
                "threshold_crossings": flicker_count,
                "interpretation": f"System briefly crossed crisis threshold {flicker_count} times",
                "risk": "CRITICAL",
            }

        # Overall risk assessment
        if len(warnings) == 0:
            overall_risk = "LOW"
        elif len(warnings) == 1:
            overall_risk = "MODERATE"
        elif len(warnings) == 2:
            overall_risk = "HIGH"
        else:
            overall_risk = "CRITICAL"

        return {
            "early_warning_signals": warnings,
            "overall_regime_shift_risk": overall_risk,
            "recommended_action": self._get_prevention_actions(overall_risk),
        }

    def _get_prevention_actions(self, risk_level: str) -> list[str]:
        """Recommend actions based on risk level."""
        if risk_level == "CRITICAL":
            return [
                "URGENT: Activate crisis prevention protocols",
                "Reduce utilization target to 75% immediately",
                "Activate all backup capacity (locum tenens, per-diem pool)",
                "Suspend non-essential services",
                "Emergency meeting with leadership",
            ]
        elif risk_level == "HIGH":
            return [
                "Increase monitoring frequency (daily checks)",
                "Proactively reduce workload (postpone elective activities)",
                "Contact backup resources (put on standby)",
                "Review and update emergency protocols",
            ]
        elif risk_level == "MODERATE":
            return [
                "Enhanced monitoring (weekly reviews)",
                "Assess faculty stress levels",
                "Prepare contingency plans",
            ]
        else:
            return ["Continue routine monitoring"]
```

### Warning Signs and Metrics

| Warning Sign | Metric | Threshold | Action |
|--------------|--------|-----------|--------|
| **Regime boundary proximity** | Distance to next regime | < 0.15 | Reduce utilization, activate buffers |
| **Critical slowing down** | Autocorrelation | > 0.7 | System losing resilience, preventive action |
| **Increased variance** | Recent variance / Historical | > 1.5× | System destabilizing, increase monitoring |
| **Flickering** | Threshold crossings in 30 days | ≥ 3 | Imminent regime shift, emergency protocols |
| **Low functional redundancy** | Average redundancy score | < 0.5 | Cross-train urgently |
| **Low adaptive capacity** | Learning score | < 0.4 | Improve incident response processes |

**Dashboard Metrics:**
```python
@dataclass
class EcologicalResilienceReport:
    # Current state
    current_regime: str
    regime_stability: float  # 0.0-1.0
    distance_to_threshold: float
    regime_shift_risk: str  # "low", "moderate", "high", "critical"

    # Diversity metrics
    functional_redundancy: float
    response_diversity: float
    critical_single_points: list[str]

    # Adaptive capacity
    adaptive_capacity_score: float
    learning_rate: float

    # Early warnings
    early_warning_signals: dict
    flickering_detected: bool

    # Interventions
    recommended_regime_shift_prevention: list[str]
    estimated_time_to_regime_shift: Optional[int]  # Days if current trajectory continues
```

---

## 8. Integration Architecture

### How These Concepts Fit Together

The seven ecological concepts form a layered resilience framework:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 7: ECOLOGICAL RESILIENCE (Meta-Framework)                  │
│ • Regime detection, early warning signals, adaptive capacity     │
│ • Monitors all other layers for system-level health             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 6: TROPHIC CASCADES (Propagation Analysis)                 │
│ • Detects how disruptions propagate through organizational levels│
│ • Intervenes to stop cascades before they reach critical systems │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: KEYSTONE SPECIES (Critical Dependencies)                │
│ • Identifies faculty with disproportionate impact                │
│ • Protects and plans succession for critical roles              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: PREDATOR-PREY DYNAMICS (Oscillation Management)         │
│ • Models demand-supply feedback loops                           │
│ • Dampens boom-bust cycles, predicts stress peaks               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: CARRYING CAPACITY (Resource Limits)                     │
│ • Enforces sustainable staffing levels                          │
│ • Prevents overshoot and collapse                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: NICHE PARTITIONING (Resource Division)                  │
│ • Optimizes faculty specialization vs generalization            │
│ • Reduces competition, maximizes coverage diversity             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: ECOLOGICAL SUCCESSION (Maturity Progression)            │
│ • Tracks schedule maturation from pioneer to climax             │
│ • Adjusts strategies based on team development stage            │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema Extensions

**Location:** `backend/alembic/versions/007_add_ecological_tables.py`

```python
def upgrade():
    # Succession tracking
    op.create_table(
        'succession_states',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('measured_at', sa.DateTime, nullable=False),
        sa.Column('stage', sa.String(20)),  # pioneer, intermediate, climax
        sa.Column('stability_index', sa.Float),
        sa.Column('specialization_ratio', sa.Float),
        sa.Column('turnover_rate', sa.Float),
        sa.Column('metrics_snapshot', JSONType()),
    )

    # Niche assignments
    op.create_table(
        'faculty_niches',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('faculty_id', GUID(), sa.ForeignKey('persons.id')),
        sa.Column('calculated_at', sa.DateTime, nullable=False),
        sa.Column('niche_breadth', sa.Float),
        sa.Column('time_of_day_prefs', JSONType()),
        sa.Column('rotation_type_prefs', JSONType()),
        sa.Column('is_generalist', sa.Boolean),
        sa.Column('is_specialist', sa.Boolean),
    )

    # Carrying capacity snapshots
    op.create_table(
        'carrying_capacity_snapshots',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('snapshot_date', sa.DateTime, nullable=False),
        sa.Column('carrying_capacity_K', sa.Integer),
        sa.Column('current_faculty_N', sa.Integer),
        sa.Column('limiting_factor', sa.String(50)),
        sa.Column('utilization_of_K', sa.Float),
        sa.Column('constraint_breakdown', JSONType()),
    )

    # Keystone faculty metrics
    op.create_table(
        'keystone_faculty_metrics',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('faculty_id', GUID(), sa.ForeignKey('persons.id')),
        sa.Column('calculated_at', sa.DateTime, nullable=False),
        sa.Column('keystone_score', sa.Float),
        sa.Column('keystone_type', sa.String(30)),
        sa.Column('unique_credentials_count', sa.Integer),
        sa.Column('faculty_trained_count', sa.Integer),
        sa.Column('backup_coverage_score', sa.Float),
    )

    # Trophic cascades
    op.create_table(
        'trophic_cascades',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('initiating_event', sa.String(100)),
        sa.Column('start_date', sa.DateTime, nullable=False),
        sa.Column('cascade_depth', sa.Integer),
        sa.Column('total_impact_score', sa.Float),
        sa.Column('is_amplifying', sa.Boolean),
        sa.Column('cascade_data', JSONType()),  # Full cascade levels
    )

    # Regime states
    op.create_table(
        'system_regime_states',
        sa.Column('id', GUID(), primary_key=True),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('regime_name', sa.String(20)),  # normal, stressed, crisis, collapsed
        sa.Column('utilization', sa.Float),
        sa.Column('service_coverage', sa.Float),
        sa.Column('regime_stability', sa.Float),
        sa.Column('early_warning_signals', JSONType()),
    )
```

### API Endpoints

**Location:** `backend/app/api/routes/ecological_resilience.py`

```python
# Succession
@router.get("/ecology/succession/status")
async def get_succession_status() -> dict:
    """Get current succession stage and stability."""
    pass

# Niche
@router.get("/ecology/niche/analysis")
async def analyze_niche_partitioning() -> dict:
    """Analyze faculty niche overlaps and recommendations."""
    pass

# Carrying capacity
@router.get("/ecology/carrying-capacity")
async def get_carrying_capacity() -> dict:
    """Get current carrying capacity and utilization."""
    pass

# Keystone
@router.get("/ecology/keystone/faculty")
async def get_keystone_faculty() -> list[KeystoneMetrics]:
    """Identify keystone faculty."""
    pass

# Cascades
@router.get("/ecology/cascades/active")
async def get_active_cascades() -> list[TrophicCascade]:
    """Get currently propagating cascades."""
    pass

# Regime
@router.get("/ecology/regime/current")
async def get_current_regime() -> dict:
    """Get current system regime and stability."""
    pass

# Unified dashboard
@router.get("/ecology/resilience-dashboard")
async def get_ecological_resilience_dashboard() -> dict:
    """
    Comprehensive ecological resilience overview.

    Combines all 7 ecological concepts into unified view.
    """
    return {
        "succession": await get_succession_status(),
        "niche_partitioning": await analyze_niche_partitioning(),
        "carrying_capacity": await get_carrying_capacity(),
        "keystone_analysis": await get_keystone_faculty(),
        "active_cascades": await get_active_cascades(),
        "current_regime": await get_current_regime(),
        "overall_resilience_score": calculate_overall_resilience(),
    }
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Implement core data collection and basic metrics.

1. **Database migrations** (007_add_ecological_tables.py)
   - Create all ecological tracking tables
   - Add indexes for time-series queries

2. **Basic metric calculation**
   - Succession stability index
   - Carrying capacity calculation
   - Keystone faculty identification

3. **Data collection pipeline**
   - Celery tasks to calculate metrics daily
   - Store results in database

### Phase 2: Analysis Engines (Weeks 3-5)

**Goal:** Implement core analysis algorithms.

1. **Succession analysis** (`succession_analysis.py`)
   - Stage detector
   - Disturbance tracker
   - Succession-aware constraint

2. **Niche analysis** (`niche_analysis.py`)
   - Niche space calculator
   - Overlap detection
   - Partitioning recommendations

3. **Carrying capacity** (`carrying_capacity.py`)
   - Multi-factor K calculation
   - Overshoot detector
   - Expansion planner

4. **Keystone analysis** (`keystone_analysis.py`)
   - Keystone identification
   - Protection constraint
   - Succession planning

### Phase 3: Dynamic Systems (Weeks 6-8)

**Goal:** Implement feedback loop and cascade detection.

1. **Lotka-Volterra simulator** (`lotka_volterra.py`)
   - Demand-supply oscillation model
   - Phase-lag predictor
   - Damping strategies

2. **Cascade detector** (`trophic_cascade.py`)
   - Cascade propagation tracker
   - Intervention planner
   - Early warning scanner

3. **Regime detection** (`regime_detection.py`)
   - Regime identifier
   - Early warning signal detector
   - Regime shift prevention

### Phase 4: Integration and UI (Weeks 9-10)

**Goal:** Unified dashboard and operational integration.

1. **API endpoints** (`ecological_resilience.py`)
   - All 7 concept endpoints
   - Unified dashboard endpoint

2. **Frontend dashboard** (`frontend/app/resilience/ecology`)
   - Succession timeline
   - Niche visualization (force-directed graph)
   - Carrying capacity gauge
   - Keystone faculty cards
   - Cascade flow diagram
   - Regime state indicator

3. **Integration with scheduling engine**
   - Succession-aware constraint in scheduler
   - Niche-based assignment preferences
   - Carrying capacity hard limit
   - Keystone protection constraint

### Phase 5: Validation and Tuning (Weeks 11-12)

**Goal:** Validate against historical data and tune parameters.

1. **Historical backtesting**
   - Run succession detector on past 2 years
   - Validate cascade detection against known incidents
   - Calibrate carrying capacity formula

2. **Parameter tuning**
   - Adjust thresholds based on empirical data
   - Optimize constraint weights

3. **Documentation**
   - User guide for ecological resilience dashboard
   - Admin manual for interpreting metrics
   - API documentation

---

## Summary: Ecological Metaphor Value Proposition

### Why Ecology Adds Value to Existing Resilience Framework

Your system already has:
- ✅ Homeostasis (biology - feedback loops)
- ✅ Le Chatelier equilibrium (chemistry - stress compensation)
- ✅ Stigmergy (swarm intelligence - learned preferences)
- ✅ Hub analysis (network theory - critical nodes)
- ✅ N-1/N-2 contingency (power grid - redundancy)

**What ecology uniquely adds:**

1. **Temporal dynamics** (Succession, Lotka-Volterra)
   - Existing: Snapshot-in-time analysis
   - Ecology adds: How systems evolve over time, predictable patterns

2. **Resource competition** (Niche partitioning, Carrying capacity)
   - Existing: Individual constraints (ACGME, preferences)
   - Ecology adds: How faculty compete for preferred shifts, sustainable limits

3. **Multi-level propagation** (Trophic cascades)
   - Existing: Direct effects (faculty leaves → gap)
   - Ecology adds: Indirect effects (faculty leaves → others overloaded → burnout cascade)

4. **Critical dependencies** (Keystone species)
   - Existing: Hub analysis (network centrality)
   - Ecology adds: Unique functional roles (not just connectivity)

5. **Regime shifts** (Ecological resilience)
   - Existing: Discrete states (GREEN → YELLOW → RED)
   - Ecology adds: Basin of attraction, early warning signals, irreversible thresholds

### Quick Reference: When to Use Each Concept

| Use This Concept | When You Need To |
|-----------------|------------------|
| **Succession** | Understand schedule maturity, adjust strategies for team development stage |
| **Niche Partitioning** | Optimize faculty specialization, reduce preference conflicts |
| **Carrying Capacity** | Determine maximum sustainable staffing, prevent overhiring |
| **Lotka-Volterra** | Predict demand-supply oscillations, dampen boom-bust cycles |
| **Keystone Species** | Identify critical faculty, ensure backup for unique capabilities |
| **Trophic Cascades** | Trace disruption propagation, intervene before effects cascade |
| **Ecological Resilience** | Detect regime shift risk, maintain system in healthy state |

---

**End of Report**

*For questions or implementation assistance, contact the resilience engineering team.*
