# Production Fork Implementation Plan

> **Created:** 2025-12-21
> **Purpose:** Battle-ready scheduling with screener ratios, FMIT flexibility, and crisis-mode turf rules
> **Target:** Private repository fork for [Your Program]
> **Context:** PCS season reality - arrived to 4 faculty, need system that survives

---

## Executive Summary

This plan creates a production-ready fork that handles:
1. **Screener:Physician ratios** (ideal 1:2-3, minimum 1:1, suboptimal 2:1)
2. **RN-as-screener fallback** when screener pool is depleted
3. **FMIT continuity turf to OB** when staffing is critical
4. **Intern stagger patterns** for screener sharing
5. **Overnight call reasonableness** given faculty constraints
6. **Simulation-validated** against real scenarios (4-faculty PCS)

---

## Table of Contents

1. [New Data Models](#1-new-data-models)
2. [Screener Constraint System](#2-screener-constraint-system)
3. [FMIT Crisis Mode (OB Turf)](#3-fmit-crisis-mode-ob-turf)
4. [Intern Stagger Patterns](#4-intern-stagger-patterns)
5. [Overnight Call Reasonableness](#5-overnight-call-reasonableness)
6. [Simulation Scenarios](#6-simulation-scenarios)
7. [Fork Strategy](#7-fork-strategy)
8. [Parallel Implementation Tracks](#8-parallel-implementation-tracks)
9. [Sequential Dependencies](#9-sequential-dependencies)

---

## 1. New Data Models

### 1.1 Screener Role Type

**File:** `backend/app/models/person.py`

```python
class ScreenerRole(str, Enum):
    """
    Screener types with different scheduling constraints.

    Screeners handle patient intake, vitals, chief complaint documentation
    before physician sees patient. Critical for clinic efficiency.
    """
    DEDICATED = "dedicated"     # Full-time clinic screener (MA, LVN)
    RN = "rn"                   # RN who can screen when needed
    RESIDENT = "resident"       # PGY-1 can screen in staggered model

class Person(Base):
    # ... existing fields ...

    # Screener-specific fields
    screener_role = Column(String(50))  # ScreenerRole enum
    can_screen = Column(Boolean, default=False)  # Quick check for RN fallback
    screening_efficiency = Column(Float, default=1.0)  # 1.0 = average, 1.5 = fast
```

### 1.2 Clinic Session Model

**File:** `backend/app/models/clinic_session.py` (NEW)

```python
class ClinicSession(Base):
    """
    Represents a clinic half-day session with staffing requirements.

    A session needs:
    - 1+ physicians (faculty or senior resident)
    - Screeners at target ratio (1:2-3 ideal, 1:1 minimum)
    """
    __tablename__ = "clinic_sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False)
    session_type = Column(String(20))  # 'AM' or 'PM'
    clinic_type = Column(String(50))   # 'FM', 'peds', 'OB', 'sports_med'

    # Staffing
    physician_count = Column(Integer, default=1)
    screener_count = Column(Integer, default=0)

    # Calculated metrics
    screener_ratio = Column(Float)  # screeners per physician

    # Status
    staffing_status = Column(String(20))  # 'optimal', 'adequate', 'suboptimal', 'critical'
    rn_fallback_used = Column(Boolean, default=False)

    @property
    def ratio_quality(self) -> str:
        """Evaluate screener:physician ratio quality."""
        if self.screener_ratio >= 2.0:
            return "optimal"      # 2-3 screeners per physician
        elif self.screener_ratio >= 1.0:
            return "adequate"     # 1:1
        elif self.screener_ratio >= 0.5:
            return "suboptimal"   # 2 physicians sharing 1 screener
        else:
            return "critical"     # No screener coverage
```

### 1.3 Intern Stagger Model

**File:** `backend/app/models/intern_stagger.py` (NEW)

```python
class InternStaggerPattern(Base):
    """
    Defines how PGY-1s share screeners through staggered start times.

    Example: Intern A starts 0730, Intern B starts 0900
    - 0730-0900: Screener works with Intern A exclusively
    - 0900-1130: Screener splits between A and B
    - 1130-1200: Screener wraps up with Intern B

    This allows 1 screener to support 2 interns effectively.
    """
    __tablename__ = "intern_stagger_patterns"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100))  # "Standard 90min Stagger"

    # Timing
    intern_a_start = Column(Time)  # 07:30
    intern_b_start = Column(Time)  # 09:00
    overlap_duration_minutes = Column(Integer)  # 150 min overlap

    # Screener efficiency during overlap (typically 0.6-0.8)
    overlap_efficiency = Column(Float, default=0.7)

    # Which intern pairs this pattern works for
    min_intern_a_experience_weeks = Column(Integer, default=4)  # A needs some ramp-up
```

---

## 2. Screener Constraint System

### 2.1 Screener Ratio Constraint

**File:** `backend/app/scheduling/constraints/screener.py` (NEW)

```python
"""
Screener:Physician Ratio Constraints.

Staffing model based on clinic efficiency data:
- Optimal: 1 physician : 2-3 screeners (physician never waits)
- Adequate: 1 physician : 1 screener (some delays)
- Suboptimal: 2 physicians : 1 screener (significant delays)
- Critical: No screener (physician does own intake - 50% productivity loss)

An efficient faculty can easily use 2-3 screeners.
Interns with staggered schedules can share screeners effectively.
"""

class ScreenerRatioConstraint(SoftConstraint):
    """
    Soft constraint penalizing suboptimal screener ratios.

    Penalties:
    - Optimal (2-3:1): 0 penalty
    - Adequate (1:1): -5 penalty per session
    - Suboptimal (0.5:1): -20 penalty per session
    - Critical (0:1): -50 penalty per session
    """

    OPTIMAL_MIN_RATIO = 2.0
    ADEQUATE_MIN_RATIO = 1.0
    SUBOPTIMAL_MIN_RATIO = 0.5

    PENALTY_ADEQUATE = 5
    PENALTY_SUBOPTIMAL = 20
    PENALTY_CRITICAL = 50

    weight = 15.0  # High weight - screener ratio affects patient throughput

    def evaluate(self, context: SchedulingContext) -> ConstraintResult:
        """Evaluate screener ratio penalties across all clinic sessions."""
        violations = []
        total_penalty = 0

        for session in context.clinic_sessions:
            ratio = session.screener_ratio

            if ratio >= self.OPTIMAL_MIN_RATIO:
                continue  # No penalty
            elif ratio >= self.ADEQUATE_MIN_RATIO:
                penalty = self.PENALTY_ADEQUATE
                severity = "info"
            elif ratio >= self.SUBOPTIMAL_MIN_RATIO:
                penalty = self.PENALTY_SUBOPTIMAL
                severity = "warning"
            else:
                penalty = self.PENALTY_CRITICAL
                severity = "error"

            violations.append(ConstraintViolation(
                severity=severity,
                message=f"Clinic {session.date} {session.session_type}: "
                        f"screener ratio {ratio:.1f}:1 ({session.ratio_quality})",
                block_id=None,
                person_id=None,
            ))
            total_penalty += penalty

        return ConstraintResult(
            violations=violations,
            score=-total_penalty,
        )


class RNScreenerFallbackConstraint(SoftConstraint):
    """
    Allows RNs to serve as screeners when dedicated pool is exhausted.

    RN-as-screener has trade-offs:
    - Pro: Maintains clinic throughput
    - Con: RN pulled from other duties (triage, procedures, patient calls)

    This constraint tracks when fallback is used and penalizes lightly
    to prefer dedicated screeners when available.
    """

    FALLBACK_PENALTY = 3  # Small penalty per RN-as-screener session
    weight = 5.0

    def evaluate(self, context: SchedulingContext) -> ConstraintResult:
        """Track RN fallback usage."""
        violations = []
        fallback_count = 0

        for session in context.clinic_sessions:
            if session.rn_fallback_used:
                fallback_count += 1
                violations.append(ConstraintViolation(
                    severity="info",
                    message=f"RN screener fallback: {session.date} {session.session_type}",
                ))

        return ConstraintResult(
            violations=violations,
            score=-fallback_count * self.FALLBACK_PENALTY,
        )
```

### 2.2 Screener Assignment Service

**File:** `backend/app/services/screener_assignment_service.py` (NEW)

```python
"""
Screener Assignment Service.

Assigns screeners to clinic sessions based on:
1. Dedicated screener availability
2. Physician count and efficiency
3. RN fallback pool
4. Intern stagger opportunities
"""

class ScreenerAssignmentService:
    """Manages screener-to-session assignments."""

    def assign_screeners_to_session(
        self,
        session: ClinicSession,
        available_screeners: list[Person],
        available_rns: list[Person],
        intern_stagger_active: bool = False,
    ) -> ScreenerAssignment:
        """
        Assign screeners to a clinic session.

        Priority order:
        1. Dedicated screeners (1:2-3 ratio if available)
        2. RN fallback (if dedicated pool exhausted)
        3. Mark critical if neither available

        Args:
            session: The clinic session to staff
            available_screeners: Pool of dedicated screeners
            available_rns: Pool of RNs who can screen
            intern_stagger_active: If True, 1 screener can cover 2 interns
        """
        target_ratio = 2.0  # Ideal: 2 screeners per physician
        min_ratio = 1.0     # Minimum: 1:1

        physicians = session.physician_count

        if intern_stagger_active and self._all_physicians_are_interns(session):
            # Staggered interns can share: 1 screener per 2 interns
            needed = max(1, physicians // 2)
        else:
            needed = int(physicians * target_ratio)

        # Try dedicated screeners first
        assigned_dedicated = min(len(available_screeners), needed)
        remaining_need = needed - assigned_dedicated

        # Fall back to RNs
        assigned_rns = 0
        if remaining_need > 0 and available_rns:
            assigned_rns = min(len(available_rns), remaining_need)

        total_screeners = assigned_dedicated + assigned_rns
        actual_ratio = total_screeners / physicians if physicians > 0 else 0

        return ScreenerAssignment(
            session=session,
            dedicated_count=assigned_dedicated,
            rn_count=assigned_rns,
            actual_ratio=actual_ratio,
            rn_fallback_used=assigned_rns > 0,
            status=self._determine_status(actual_ratio),
        )
```

---

## 3. FMIT Crisis Mode (OB Turf)

### 3.1 FMIT Continuity Turf Rules

**File:** `backend/app/scheduling/constraints/fmit.py` (UPDATE)

```python
class FMITContinuityTurfConstraint(HardConstraint):
    """
    FMIT continuity delivery turf rules.

    FM faculty attend continuity deliveries (patients they've followed in clinic).
    When staffing is critical, continuity deliveries can be turfed to OB.

    Defense levels:
    - GREEN/YELLOW: FM attends all continuity deliveries
    - ORANGE: FM attends if available, otherwise OB covers
    - RED/BLACK: OB covers all, FM focuses on clinic/call

    This constraint reads the current defense level from ResilienceService
    and adjusts FMIT requirements accordingly.
    """

    name = "fmit_continuity_turf"
    constraint_type = ConstraintType.AVAILABILITY
    priority = ConstraintPriority.REQUIRED

    def evaluate(self, context: SchedulingContext) -> ConstraintResult:
        """Evaluate FMIT continuity requirements based on defense level."""
        violations = []

        defense_level = context.resilience_status.defense_level

        for delivery in context.continuity_deliveries:
            fm_faculty = delivery.continuity_provider

            if defense_level in ("GREEN", "YELLOW"):
                # Normal: FM must attend
                if not self._is_fm_available(fm_faculty, delivery.date, context):
                    violations.append(ConstraintViolation(
                        severity="error",
                        message=f"FM continuity required: {fm_faculty.name} unavailable "
                                f"for delivery on {delivery.date}",
                        block_id=None,
                        person_id=fm_faculty.id,
                    ))

            elif defense_level == "ORANGE":
                # Degraded: FM preferred, OB acceptable
                if not self._is_fm_available(fm_faculty, delivery.date, context):
                    # Log but don't fail - OB will cover
                    violations.append(ConstraintViolation(
                        severity="warning",
                        message=f"FM continuity turfed to OB: {delivery.date} "
                                f"({fm_faculty.name} unavailable, defense={defense_level})",
                    ))

            else:  # RED or BLACK
                # Crisis: All continuity turfed to OB
                violations.append(ConstraintViolation(
                    severity="info",
                    message=f"Crisis mode: All continuity turfed to OB "
                            f"(defense={defense_level})",
                ))
                break  # One message covers all

        return ConstraintResult(violations=violations, score=0)


class FMITStaffingFloorConstraint(HardConstraint):
    """
    Ensures minimum faculty available before FMIT assignments.

    FMIT weeks consume faculty completely (blocked from clinic/call).
    This constraint prevents FMIT assignment when it would drop
    available faculty below safe thresholds.

    Thresholds:
    - minimum_faculty_for_fmit: 5 (below this, no FMIT assignments)
    - fmit_utilization_cap: 0.20 (max 20% of faculty on FMIT at once)
    """

    MINIMUM_FACULTY_FOR_FMIT = 5
    FMIT_UTILIZATION_CAP = 0.20  # Max 20% on FMIT simultaneously

    def evaluate(self, context: SchedulingContext) -> ConstraintResult:
        """Check if FMIT assignments are safe given current staffing."""
        violations = []

        total_faculty = len(context.active_faculty)

        if total_faculty < self.MINIMUM_FACULTY_FOR_FMIT:
            # Block ALL FMIT assignments
            for fmit_week in context.proposed_fmit_weeks:
                violations.append(ConstraintViolation(
                    severity="error",
                    message=f"Cannot assign FMIT: only {total_faculty} faculty available "
                            f"(minimum {self.MINIMUM_FACULTY_FOR_FMIT} required)",
                    person_id=fmit_week.faculty_id,
                ))
        else:
            # Check utilization cap
            max_concurrent_fmit = int(total_faculty * self.FMIT_UTILIZATION_CAP)
            max_concurrent_fmit = max(1, max_concurrent_fmit)  # At least 1 allowed

            fmit_by_week = self._group_fmit_by_week(context.proposed_fmit_weeks)
            for week, assignments in fmit_by_week.items():
                if len(assignments) > max_concurrent_fmit:
                    violations.append(ConstraintViolation(
                        severity="error",
                        message=f"Week {week}: {len(assignments)} FMIT exceeds cap "
                                f"({max_concurrent_fmit} max for {total_faculty} faculty)",
                    ))

        return ConstraintResult(violations=violations, score=0)
```

---

## 4. Intern Stagger Patterns

### 4.1 Stagger Pattern Service

**File:** `backend/app/services/intern_stagger_service.py` (NEW)

```python
"""
Intern Stagger Service.

Manages staggered intern schedules to allow screener sharing.

Model:
- Intern A starts 0730, sees patients with screener support
- Intern B starts 0900, 90 min after A
- During overlap (0900-1130), screener alternates between both
- Net effect: 1 screener supports 2 interns with ~70% efficiency each

This is acceptable for PGY-1s who:
- Are still learning (slower pace acceptable)
- Benefit from brief waits (time to think/document)
- Need less complex patients initially
"""

class InternStaggerService:
    """Manages intern stagger scheduling."""

    DEFAULT_STAGGER_MINUTES = 90
    OVERLAP_EFFICIENCY = 0.7  # Each intern gets 70% screener time during overlap

    def create_stagger_pair(
        self,
        intern_a: Person,
        intern_b: Person,
        session_date: date,
        session_type: str,
    ) -> InternStaggerAssignment:
        """
        Create a staggered intern pair for a clinic session.

        Requirements:
        - Both must be PGY-1
        - Intern A should have 4+ weeks clinic experience (leads)
        - Session must have at least 1 dedicated screener
        """
        if intern_a.pgy_level != 1 or intern_b.pgy_level != 1:
            raise ValueError("Stagger patterns only for PGY-1 interns")

        return InternStaggerAssignment(
            intern_a_id=intern_a.id,
            intern_b_id=intern_b.id,
            date=session_date,
            session_type=session_type,
            intern_a_start=time(7, 30),
            intern_b_start=time(9, 0),
            stagger_minutes=self.DEFAULT_STAGGER_MINUTES,
            screener_efficiency=self.OVERLAP_EFFICIENCY,
        )

    def calculate_effective_screener_coverage(
        self,
        stagger: InternStaggerAssignment,
        screener_count: int,
    ) -> float:
        """
        Calculate effective screener coverage for staggered interns.

        With stagger, 1 screener provides ~1.4 effective screener-hours
        (0.7 efficiency * 2 interns = 1.4 effective)
        """
        # Non-overlap periods: full efficiency
        non_overlap_hours = 1.5  # 0730-0900 for A only

        # Overlap period: reduced efficiency per intern
        overlap_hours = 2.5  # 0900-1130 shared

        effective_coverage = (
            (non_overlap_hours * 1.0) +  # Full for A
            (overlap_hours * self.OVERLAP_EFFICIENCY * 2)  # Split for both
        )

        return effective_coverage * screener_count
```

### 4.2 Stagger-Aware Screener Constraint

**File:** `backend/app/scheduling/constraints/screener.py` (UPDATE)

```python
class StaggeredInternScreenerConstraint(SoftConstraint):
    """
    Adjusts screener requirements when intern stagger is active.

    When PGY-1s are staggered:
    - 1 screener can effectively cover 2 interns
    - Minimum ratio drops from 1:1 to 0.5:1
    - This enables clinic to run with fewer screeners

    Bonus: Encourages stagger scheduling when screener pool is limited.
    """

    STAGGER_BONUS = 10  # Bonus for using stagger pattern
    weight = 8.0

    def evaluate(self, context: SchedulingContext) -> ConstraintResult:
        """Reward stagger patterns when they help screener coverage."""
        violations = []
        bonus = 0

        for session in context.clinic_sessions:
            if session.has_intern_stagger:
                # Check if stagger was necessary (low screener count)
                if session.screener_count < session.physician_count:
                    bonus += self.STAGGER_BONUS
                    violations.append(ConstraintViolation(
                        severity="info",
                        message=f"Intern stagger enabled: {session.date} "
                                f"(1 screener covering 2 interns)",
                    ))

        return ConstraintResult(violations=violations, score=bonus)
```

---

## 5. Overnight Call Reasonableness

### 5.1 Call Reasonableness Constraint

**File:** `backend/app/scheduling/constraints/call_equity.py` (UPDATE)

```python
class CallReasonablenessConstraint(SoftConstraint):
    """
    Ensures overnight call schedule is reasonable given faculty count.

    "Reasonable" depends on available faculty:
    - 10+ faculty: Standard rotation (q7-10 call)
    - 6-9 faculty: Slightly increased (q5-7 call)
    - 4-5 faculty: Heavy but manageable (q4-5 call)
    - <4 faculty: CRITICAL - may need external coverage

    This constraint works with ResilienceService to:
    1. Calculate sustainable call frequency
    2. Alert when frequency exceeds sustainability
    3. Trigger defense level escalation if needed
    """

    # Days between calls for sustainability (by faculty count)
    SUSTAINABILITY_THRESHOLDS = {
        10: 7,   # 10+ faculty: q7 sustainable
        8: 6,    # 8-9 faculty: q6 sustainable
        6: 5,    # 6-7 faculty: q5 sustainable
        4: 4,    # 4-5 faculty: q4 minimum
        2: 3,    # 2-3 faculty: q3 CRITICAL (not sustainable long-term)
    }

    UNSUSTAINABLE_PENALTY = 30
    weight = 20.0

    def evaluate(self, context: SchedulingContext) -> ConstraintResult:
        """Check if call frequency is sustainable."""
        violations = []
        total_penalty = 0

        faculty_count = len(context.call_eligible_faculty)

        # Find sustainability threshold
        sustainable_interval = 7  # Default
        for count, interval in sorted(self.SUSTAINABILITY_THRESHOLDS.items(), reverse=True):
            if faculty_count >= count:
                sustainable_interval = interval
                break

        # Calculate actual average interval per faculty
        for faculty in context.call_eligible_faculty:
            actual_interval = self._calculate_average_call_interval(
                faculty, context.call_assignments
            )

            if actual_interval < sustainable_interval:
                penalty = self.UNSUSTAINABLE_PENALTY * (sustainable_interval - actual_interval)
                total_penalty += penalty

                violations.append(ConstraintViolation(
                    severity="warning" if actual_interval >= sustainable_interval - 1 else "error",
                    message=f"{faculty.name}: q{actual_interval:.1f} call "
                            f"(sustainable: q{sustainable_interval}+)",
                    person_id=faculty.id,
                ))

        # Check for critical staffing
        if faculty_count < 4:
            violations.append(ConstraintViolation(
                severity="error",
                message=f"CRITICAL: Only {faculty_count} call-eligible faculty. "
                        f"Consider external moonlighters or locums.",
            ))
            total_penalty += 100  # Heavy penalty

        return ConstraintResult(violations=violations, score=-total_penalty)
```

---

## 6. Simulation Scenarios

### 6.1 PCS Season Scenario

**File:** `backend/app/resilience/simulation/pcs_scenario.py` (NEW)

```python
"""
PCS (Permanent Change of Station) Season Simulation.

Models the military-specific staffing crisis that occurs during summer
PCS season when multiple faculty may leave/arrive simultaneously.

Real-world scenario: Arriving to 4 faculty when normal staffing is 10.
"""

from dataclasses import dataclass
from .base import SimulationConfig, SimulationResult
from .cascade_scenario import BurnoutCascadeScenario, CascadeConfig


@dataclass
class PCSSeasonConfig:
    """
    Configuration for PCS season simulation.

    Based on real military medicine patterns:
    - PCS season: June-August peak
    - Average 30% turnover annually
    - New arrivals have 2-4 week onboarding (reduced productivity)
    - Departures often front-loaded (people leave before replacements arrive)
    """

    # Starting conditions
    initial_faculty: int = 4  # Your PCS arrival reality
    expected_faculty: int = 10  # Normal staffing level

    # Timing
    simulation_days: int = 365
    pcs_season_start_day: int = 150  # ~June 1
    pcs_season_end_day: int = 240    # ~August 31

    # Departure/arrival patterns
    departures_during_pcs: int = 3   ***REMOVED*** leaving
    arrivals_during_pcs: int = 5     ***REMOVED*** arriving (eventually)
    arrival_lag_days: int = 45       # Average gap between departure and replacement
    onboarding_days: int = 21        # New faculty at 50% productivity

    # Screener dynamics
    initial_screeners: int = 2
    screener_turnover_rate: float = 0.4  # 40% annual (higher than faculty)

    # Workload
    total_clinic_sessions_per_week: int = 40  # Full schedule demand

    # Seed
    seed: int = 42


class PCSSeasonScenario:
    """
    Simulates a year starting from PCS-depleted staffing.

    Key metrics tracked:
    - Days until staffing recovers to target
    - Screener ratio degradation periods
    - FMIT coverage gaps
    - Call frequency per faculty
    - Defense level escalations
    """

    def __init__(self, config: PCSSeasonConfig):
        self.config = config

    def run(self) -> PCSSeasonResult:
        """Run the PCS season simulation."""
        # Convert to cascade config for burnout modeling
        cascade_config = CascadeConfig(
            initial_faculty=self.config.initial_faculty,
            minimum_viable=3,
            max_simulation_days=self.config.simulation_days,
            total_workload_units=self.config.total_clinic_sessions_per_week / 4,
            sustainable_workload=1.2,
            burnout_threshold=1.5,
            critical_threshold=2.0,
            hiring_delay_days=self.config.arrival_lag_days,
            seed=self.config.seed,
        )

        # Run burnout cascade
        cascade_result = BurnoutCascadeScenario(cascade_config).run()

        # Overlay screener dynamics
        screener_result = self._simulate_screener_dynamics()

        # Calculate metrics
        return PCSSeasonResult(
            config=self.config,
            collapsed=cascade_result.collapsed,
            days_to_collapse=cascade_result.days_to_collapse,
            days_to_recovery=self._calculate_recovery_day(cascade_result),
            peak_call_frequency=self._calculate_peak_call_frequency(),
            screener_ratio_nadir=screener_result.nadir_ratio,
            fmit_gaps=self._count_fmit_gaps(),
            defense_escalations=cascade_result.defense_escalations,
            recommendations=self._generate_recommendations(cascade_result),
        )

    def _generate_recommendations(self, cascade_result) -> list[str]:
        """Generate actionable recommendations based on simulation."""
        recs = []

        if self.config.initial_faculty < 5:
            recs.append(
                "CRITICAL: <5 faculty. Request locum coverage or moonlighters immediately."
            )

        if cascade_result.peak_workload > 2.0:
            recs.append(
                "Workload exceeded 2.0x sustainable. Activate OB turf for continuity deliveries."
            )

        if self.config.initial_screeners < self.config.initial_faculty:
            recs.append(
                "Screener shortage. Enable RN fallback and intern stagger patterns."
            )

        recs.append(
            f"Target recovery: Day {self._calculate_recovery_day(cascade_result)}. "
            f"Plan aggressive hiring to beat this."
        )

        return recs


@dataclass
class PCSSeasonResult:
    """Results from PCS season simulation."""
    config: PCSSeasonConfig
    collapsed: bool
    days_to_collapse: int | None
    days_to_recovery: int
    peak_call_frequency: float  # Worst-case days between calls
    screener_ratio_nadir: float  # Lowest screener:physician ratio
    fmit_gaps: int  # Number of weeks FMIT couldn't be staffed
    defense_escalations: list[tuple[int, str]]  # (day, level)
    recommendations: list[str]
```

### 6.2 Monte Carlo Test Suite

**File:** `backend/app/resilience/simulation/monte_carlo.py` (NEW)

```python
"""
Monte Carlo Simulation Suite for Battle Testing.

Runs thousands of simulations with varying parameters to:
1. Identify failure probability for different staffing levels
2. Find optimal screener ratios
3. Test FMIT turf thresholds
4. Validate call frequency limits
"""

from dataclasses import dataclass
from typing import Callable
import numpy as np
from concurrent.futures import ProcessPoolExecutor

from .pcs_scenario import PCSSeasonConfig, PCSSeasonScenario


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo simulation suite."""
    n_simulations: int = 1000
    parallel_workers: int = 4

    # Parameter ranges to test
    faculty_range: tuple[int, int] = (3, 12)
    screener_range: tuple[int, int] = (1, 8)

    # Fixed parameters
    simulation_days: int = 365


class MonteCarloRunner:
    """Runs Monte Carlo simulations and aggregates results."""

    def __init__(self, config: MonteCarloConfig):
        self.config = config

    def run_faculty_survival_analysis(self) -> dict:
        """
        Determine survival probability for each faculty count.

        Returns:
            Dict mapping faculty_count -> survival_probability
        """
        results = {}

        for faculty_count in range(
            self.config.faculty_range[0],
            self.config.faculty_range[1] + 1
        ):
            survival_count = 0

            for seed in range(self.config.n_simulations):
                pcs_config = PCSSeasonConfig(
                    initial_faculty=faculty_count,
                    seed=seed,
                )
                result = PCSSeasonScenario(pcs_config).run()

                if not result.collapsed:
                    survival_count += 1

            results[faculty_count] = survival_count / self.config.n_simulations

        return results

    def find_critical_thresholds(self) -> dict:
        """
        Find critical thresholds for various parameters.

        Returns:
            Dict with:
            - min_faculty_for_survival: Minimum faculty with >95% survival
            - optimal_screener_ratio: Ratio with best outcomes
            - max_call_frequency: Sustainable call frequency
        """
        survival = self.run_faculty_survival_analysis()

        # Find minimum faculty for 95% survival
        min_faculty = None
        for count in sorted(survival.keys()):
            if survival[count] >= 0.95:
                min_faculty = count
                break

        return {
            "min_faculty_for_survival": min_faculty,
            "survival_by_count": survival,
            "recommendations": self._generate_threshold_recommendations(survival),
        }

    def _generate_threshold_recommendations(self, survival: dict) -> list[str]:
        """Generate recommendations from Monte Carlo results."""
        recs = []

        # Find 50%, 80%, 95% survival thresholds
        for target, label in [(0.50, "coin-flip"), (0.80, "likely"), (0.95, "safe")]:
            for count in sorted(survival.keys()):
                if survival[count] >= target:
                    recs.append(f"{count} faculty: {target*100:.0f}% survival ({label})")
                    break

        return recs
```

---

## 7. Fork Strategy

### 7.1 Repository Structure

```
your-org/residency-scheduler-[site-name]/    # Private fork
├── .github/
│   └── workflows/
│       └── deploy.yml                        # Site-specific CI/CD
├── config/
│   └── site_config.py                        # Site-specific parameters
├── data/
│   └── faculty_roster.json                   # Real faculty data (gitignored)
├── docs/
│   └── SITE_SPECIFIC.md                      # Your program's documentation
└── (all other files from upstream)
```

### 7.2 Site Configuration

**File:** `config/site_config.py` (NEW - in private fork only)

```python
"""
Site-specific configuration for [Your Program].

This file contains parameters specific to your residency program.
It is NOT committed to the public upstream repository.
"""

# Staffing
EXPECTED_FACULTY_COUNT = 10
CURRENT_FACULTY_COUNT = 4  # PCS season reality
EXPECTED_SCREENER_COUNT = 6
CURRENT_SCREENER_COUNT = 2

# Screener ratios
OPTIMAL_SCREENER_RATIO = 2.5  # Your efficient faculty can use 2-3
MINIMUM_SCREENER_RATIO = 1.0
SUBOPTIMAL_SCREENER_RATIO = 0.5

# FMIT
FMIT_WEEKS_PER_FACULTY_PER_YEAR = 6
MINIMUM_FACULTY_FOR_FMIT = 5
OB_TURF_DEFENSE_LEVEL = "ORANGE"  # Turf continuity at this level

# Intern stagger
ENABLE_INTERN_STAGGER = True
STAGGER_MINUTES = 90
MIN_INTERN_EXPERIENCE_WEEKS = 4

# Call
SUNDAY_CALL_EQUITY_WEIGHT = 2.0  # Sunday counts double for equity
CALL_ELIGIBLE_ROLES = ["core", "apd", "oic"]
CALL_EXEMPT_ROLES = ["pd", "dept_chief", "sports_med"]

# PCS season
PCS_SEASON_START = "06-01"
PCS_SEASON_END = "08-31"
PCS_HIRING_LAG_DAYS = 45
```

### 7.3 Fork Commands

```bash
# 1. Create private fork (GitHub CLI)
gh repo fork Euda1mon1a/Autonomous-Assignment-Program-Manager \
    --clone \
    --private \
    --remote-name upstream

# 2. Rename for your site
mv Autonomous-Assignment-Program-Manager residency-scheduler-[site]
cd residency-scheduler-[site]

# 3. Create site config
mkdir -p config
touch config/site_config.py
echo "config/site_config.py" >> .gitignore
echo "data/" >> .gitignore

# 4. Set up upstream tracking
git remote add upstream https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
git fetch upstream

# 5. Create site-specific branch
git checkout -b site-specific
```

---

## 8. Parallel Implementation Tracks

These can be worked on **simultaneously** by different sessions/agents:

### Track A: Data Models (Foundation)
**Files to create/modify:**
- `backend/app/models/clinic_session.py` (NEW)
- `backend/app/models/intern_stagger.py` (NEW)
- `backend/app/models/person.py` (add screener fields)
- `backend/alembic/versions/XXX_add_screener_models.py`

**No dependencies on other tracks.**

### Track B: Screener Constraints
**Files to create:**
- `backend/app/scheduling/constraints/screener.py` (NEW)
- `backend/app/services/screener_assignment_service.py` (NEW)
- `backend/tests/constraints/test_screener_constraints.py`

**Depends on:** Track A (models must exist)

### Track C: FMIT Crisis Mode
**Files to modify:**
- `backend/app/scheduling/constraints/fmit.py` (add turf rules)
- `backend/app/services/fmit_scheduler_service.py` (add defense awareness)

**Depends on:** Existing resilience service (already integrated)

### Track D: Intern Stagger System
**Files to create:**
- `backend/app/services/intern_stagger_service.py` (NEW)
- `backend/tests/services/test_intern_stagger.py`

**Depends on:** Track A (models)

### Track E: Simulation Scenarios
**Files to create:**
- `backend/app/resilience/simulation/pcs_scenario.py` (NEW)
- `backend/app/resilience/simulation/monte_carlo.py` (NEW)
- `backend/tests/simulation/test_pcs_scenario.py`

**Depends on:** Existing cascade_scenario.py (already exists)

### Track F: Site Fork Setup
**Actions:**
- Create private repo
- Set up CI/CD
- Configure site_config.py
- Document site-specific procedures

**No code dependencies - can run in parallel with all tracks.**

---

## 9. Sequential Dependencies

These must be done **in order**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEQUENTIAL DEPENDENCY CHAIN                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Track A: Data Models                                        │
│     └── Creates ClinicSession, InternStagger, screener fields  │
│         │                                                       │
│         ▼                                                       │
│  2. Database Migration                                          │
│     └── alembic revision --autogenerate                        │
│     └── alembic upgrade head                                   │
│         │                                                       │
│         ▼                                                       │
│  3. Tracks B, C, D (can be parallel after step 2)              │
│     ├── B: Screener Constraints                                │
│     ├── C: FMIT Crisis Mode                                    │
│     └── D: Intern Stagger                                      │
│         │                                                       │
│         ▼                                                       │
│  4. Integration Testing                                         │
│     └── Test all constraints together                          │
│     └── Verify no conflicts                                    │
│         │                                                       │
│         ▼                                                       │
│  5. Track E: Simulation Validation                             │
│     └── Run PCS scenario with new constraints                  │
│     └── Monte Carlo for threshold calibration                  │
│         │                                                       │
│         ▼                                                       │
│  6. Production Deployment (Track F fork)                        │
│     └── Load real faculty data                                 │
│     └── Configure site_config.py                               │
│     └── Run simulations with real parameters                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Implementation Priority Matrix

| Priority | Track | Effort | Impact | Can Parallelize? |
|----------|-------|--------|--------|------------------|
| **P0** | A: Data Models | 2 hours | Foundation | Yes (first) |
| **P0** | F: Fork Setup | 1 hour | Unblocks production | Yes |
| **P1** | B: Screener Constraints | 4 hours | Critical for clinic | After A |
| **P1** | C: FMIT Crisis Mode | 2 hours | Enables turf rules | Yes |
| **P1** | E: PCS Simulation | 3 hours | Validates system | Yes |
| **P2** | D: Intern Stagger | 3 hours | Optimization | After A |
| **P2** | Monte Carlo | 2 hours | Threshold calibration | After E |

---

## 11. Immediate Next Steps

### Session 1 (Now): Foundation
1. Create data models (Track A)
2. Run migration
3. Set up fork (Track F)

### Session 2: Core Constraints
1. Screener constraints (Track B)
2. FMIT crisis mode (Track C)

### Session 3: Simulation
1. PCS scenario (Track E)
2. Run with your parameters (4 faculty, 2 screeners)
3. Generate survival curves

### Session 4: Optimization
1. Intern stagger (Track D)
2. Monte Carlo calibration
3. Production deployment

---

## 12. Documentation Backlog (For Future Sessions)

These items need documentation but can wait:

1. **Screener Training SOP** - How to onboard RNs as backup screeners
2. **FMIT Turf Protocol** - When/how to communicate OB turf to patients
3. **Intern Stagger Checklist** - Daily operations for staggered schedules
4. **PCS Season Playbook** - Pre-PCS, during-PCS, post-PCS actions
5. **Call Moonlighter Integration** - How to add external coverage to system

---

**Document Status:** Ready for parallel implementation
**Last Updated:** 2025-12-21
