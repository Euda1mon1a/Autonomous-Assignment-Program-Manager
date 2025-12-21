"""
Compound Stress Scenario: Everything Happens At Once.

"Objective: Survive" - Halo Reach

This simulation models the reality of PCS season where multiple
stressors compound simultaneously:

1. Faculty PCS (departures AND delayed arrivals)
2. Screener turnover (40%+ annual, higher than faculty)
3. July Effect (new interns at minimum competency)
4. Call compression (fewer people = more frequent call)
5. Burnout contagion (stress spreads through team)
6. FMIT requirements (MUST be staffed - non-negotiable)

The goal is not to avoid stress - it's to SURVIVE.
FMIT must continue. The mission is non-negotiable.

This answers: "What if everything happens all at once?"
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StaffType(Enum):
    """Types of staff in the simulation."""
    FACULTY = "faculty"
    SCREENER_DEDICATED = "screener_dedicated"  ***REMOVED*** MA, LVN
    SCREENER_RN = "screener_rn"                ***REMOVED*** RN fallback
    SCREENER_EMT = "screener_emt"              ***REMOVED*** Active duty medic
    INTERN = "intern"                          ***REMOVED*** PGY-1
    SENIOR_RESIDENT = "senior_resident"        ***REMOVED*** PGY-2/3


class DefenseLevel(Enum):
    """System defense levels."""
    GREEN = 0   ***REMOVED*** Normal
    YELLOW = 1  ***REMOVED*** Warning
    ORANGE = 2  ***REMOVED*** Degraded - OB turf acceptable
    RED = 3     ***REMOVED*** Crisis - OB turf preferred
    BLACK = 4   ***REMOVED*** Survival mode - OB turf mandatory


@dataclass
class CompoundStressConfig:
    """
    Configuration for compound stress simulation.

    Models everything happening at once during PCS season.
    """
    ***REMOVED*** === FACULTY ===
    initial_faculty: int = 4          ***REMOVED*** Your PCS arrival reality
    expected_faculty: int = 10        ***REMOVED*** Normal staffing
    minimum_faculty_for_fmit: int = 5 ***REMOVED*** Below this, FMIT is at risk
    faculty_pcs_departures: int = 3   ***REMOVED*** How many leave during PCS
    faculty_arrival_lag_days: int = 45
    faculty_onboarding_days: int = 21 ***REMOVED*** 50% productivity during onboarding

    ***REMOVED*** === SCREENERS ===
    initial_screeners_dedicated: int = 2
    initial_screeners_rn: int = 3     ***REMOVED*** Available for fallback
    initial_screeners_emt: int = 2    ***REMOVED*** Active duty medics
    screener_turnover_rate: float = 0.40  ***REMOVED*** 40% annual (higher than faculty)
    optimal_screener_ratio: float = 2.5   ***REMOVED*** Per physician
    minimum_screener_ratio: float = 1.0

    ***REMOVED*** === RESIDENTS ===
    initial_interns: int = 4          ***REMOVED*** PGY-1
    initial_seniors: int = 4          ***REMOVED*** PGY-2/3
    july_intern_competency: float = 0.5   ***REMOVED*** 50% effective in July
    intern_competency_gain_per_month: float = 0.08  ***REMOVED*** Ramp up

    ***REMOVED*** === FMIT (NON-NEGOTIABLE) ===
    fmit_weeks_per_year: int = 52     ***REMOVED*** Every week needs coverage
    fmit_faculty_required: int = 1     ***REMOVED*** Per week minimum
    fmit_can_turf_to_ob: bool = True  ***REMOVED*** Only at ORANGE+ defense
    fmit_turf_penalty: float = 10.0   ***REMOVED*** Score penalty for OB turf

    ***REMOVED*** === CALL ===
    call_nights_per_week: int = 7
    minimum_call_interval_days: int = 3  ***REMOVED*** q3 absolute minimum
    sustainable_call_interval_days: int = 5  ***REMOVED*** q5 sustainable
    call_burnout_multiplier: float = 1.5  ***REMOVED*** Extra burnout from frequent call

    ***REMOVED*** === CLINIC ===
    clinic_sessions_per_week: int = 40  ***REMOVED*** Total demand
    sessions_per_faculty_sustainable: int = 8  ***REMOVED*** Per week max

    ***REMOVED*** === BURNOUT DYNAMICS ===
    ***REMOVED*** Reduced rates to model long grind, not immediate collapse
    base_burnout_rate: float = 0.0003     ***REMOVED*** Daily base rate (~10%/year baseline)
    workload_burnout_multiplier: float = 3.0  ***REMOVED*** Less aggressive
    burnout_contagion_rate: float = 0.01  ***REMOVED*** Spreads to teammates
    burnout_threshold: float = 1.5        ***REMOVED*** Workload multiplier
    critical_threshold: float = 2.0

    ***REMOVED*** === ACGME CONTINUITY (FM-specific) ===
    ***REMOVED*** Residents must have minimum continuity weeks per year
    min_continuity_weeks_per_resident: int = 40  ***REMOVED*** ACGME FM requirement
    continuity_patients_per_resident: int = 120   ***REMOVED*** Panel size target

    ***REMOVED*** === SIMULATION ===
    duration_days: int = 365
    seed: int = 42


@dataclass
class DailyState:
    """Complete system state for a single day."""
    day: int

    ***REMOVED*** Staffing counts
    faculty_count: int
    faculty_onboarding: int  ***REMOVED*** Still ramping up
    screener_dedicated: int
    screener_rn_active: int  ***REMOVED*** Currently screening
    screener_emt_active: int
    intern_count: int
    senior_count: int

    ***REMOVED*** Derived metrics
    effective_faculty: float  ***REMOVED*** Adjusted for onboarding
    effective_physicians: float  ***REMOVED*** Faculty + seniors + partial interns
    screener_ratio: float
    workload_per_physician: float
    call_interval_days: float
    intern_competency: float

    ***REMOVED*** Status
    defense_level: DefenseLevel
    fmit_covered: bool
    fmit_turfed_to_ob: bool
    clinic_sessions_covered: int
    clinic_sessions_dropped: int

    ***REMOVED*** Events
    departures: dict = field(default_factory=dict)
    arrivals: dict = field(default_factory=dict)
    burnout_events: int = 0

    ***REMOVED*** Scores
    burnout_score: float = 0.0  ***REMOVED*** Accumulated team burnout
    survival_score: float = 100.0  ***REMOVED*** Starts at 100, degrades


@dataclass
class CompoundStressResult:
    """Results from compound stress simulation."""
    config: CompoundStressConfig

    ***REMOVED*** Survival
    survived: bool
    fmit_survived: bool  ***REMOVED*** The mission
    days_survived: int

    ***REMOVED*** Final state
    final_faculty: int
    final_screeners: int
    final_defense_level: DefenseLevel

    ***REMOVED*** FMIT metrics (the mission)
    fmit_weeks_covered: int
    fmit_weeks_turfed: int
    fmit_weeks_failed: int  ***REMOVED*** Unacceptable

    ***REMOVED*** Stress metrics
    peak_workload: float
    peak_call_frequency: float  ***REMOVED*** Worst q-value
    days_in_crisis: int  ***REMOVED*** RED or BLACK
    total_burnout_departures: int

    ***REMOVED*** Screener metrics
    days_below_min_screener_ratio: int
    rn_fallback_days: int
    emt_fallback_days: int

    ***REMOVED*** Timeline
    states: list[DailyState]

    ***REMOVED*** Recommendations
    recommendations: list[str]


class CompoundStressScenario:
    """
    Simulates compound stress during PCS season.

    Everything happens at once. The goal is to survive.
    FMIT must continue.
    """

    def __init__(self, config: CompoundStressConfig):
        self.config = config
        self._rng = random.Random(config.seed)
        self._reset()

    def _reset(self):
        """Reset simulation state."""
        self._day = 0
        self._states: list[DailyState] = []

        ***REMOVED*** Staff counts
        self._faculty = self.config.initial_faculty
        self._faculty_onboarding = 0
        self._screener_dedicated = self.config.initial_screeners_dedicated
        self._screener_rn_available = self.config.initial_screeners_rn
        self._screener_emt_available = self.config.initial_screeners_emt
        self._interns = self.config.initial_interns
        self._seniors = self.config.initial_seniors

        ***REMOVED*** Hiring queues
        self._faculty_arriving: list[tuple[int, bool]] = []  ***REMOVED*** (day, is_onboarding)
        self._screener_arriving: list[int] = []

        ***REMOVED*** Burnout tracking
        self._team_burnout = 0.0
        self._burnout_departures = 0

        ***REMOVED*** FMIT tracking
        self._fmit_covered = 0
        self._fmit_turfed = 0
        self._fmit_failed = 0

    def _calculate_intern_competency(self) -> float:
        """Calculate intern competency based on time since July."""
        ***REMOVED*** Assume simulation starts July 1 (day 0)
        months_elapsed = self._day / 30.0
        competency = self.config.july_intern_competency + \
                     (months_elapsed * self.config.intern_competency_gain_per_month)
        return min(1.0, competency)

    def _calculate_effective_physicians(self) -> float:
        """Calculate effective physician count."""
        ***REMOVED*** Faculty (adjusted for onboarding)
        effective_faculty = self._faculty - (self._faculty_onboarding * 0.5)

        ***REMOVED*** Seniors count as full physicians
        effective_seniors = self._seniors

        ***REMOVED*** Interns count based on competency
        intern_competency = self._calculate_intern_competency()
        effective_interns = self._interns * intern_competency * 0.7  ***REMOVED*** Never fully independent

        return effective_faculty + effective_seniors + effective_interns

    def _calculate_screener_ratio(self) -> float:
        """Calculate current screener:physician ratio."""
        physicians = self._calculate_effective_physicians()
        if physicians <= 0:
            return 0.0

        ***REMOVED*** Total available screeners (dedicated + activated fallback)
        total_screeners = self._screener_dedicated

        ***REMOVED*** Activate RN fallback if below minimum
        rn_needed = 0
        emt_needed = 0

        current_ratio = total_screeners / physicians
        if current_ratio < self.config.minimum_screener_ratio:
            ***REMOVED*** Need fallback
            deficit = (self.config.minimum_screener_ratio * physicians) - total_screeners
            rn_needed = min(int(deficit), self._screener_rn_available)
            total_screeners += rn_needed

            current_ratio = total_screeners / physicians
            if current_ratio < self.config.minimum_screener_ratio:
                emt_needed = min(
                    int((self.config.minimum_screener_ratio * physicians) - total_screeners),
                    self._screener_emt_available
                )
                total_screeners += emt_needed

        self._rn_active = rn_needed
        self._emt_active = emt_needed

        return total_screeners / physicians if physicians > 0 else 0

    def _calculate_workload(self) -> float:
        """Calculate workload per physician."""
        physicians = self._calculate_effective_physicians()
        if physicians <= 0:
            return float('inf')

        ***REMOVED*** Base clinic workload
        clinic_workload = self.config.clinic_sessions_per_week / 5  ***REMOVED*** Daily

        ***REMOVED*** Normalize to expected staffing
        expected_physicians = self.config.expected_faculty + self._seniors + \
                             (self._interns * 0.7)

        return clinic_workload / physicians * (expected_physicians / 10)

    def _calculate_call_interval(self) -> float:
        """Calculate average days between call for each physician."""
        call_eligible = self._faculty + self._seniors  ***REMOVED*** Interns don't take independent call
        if call_eligible <= 0:
            return 0.0
        return call_eligible / self.config.call_nights_per_week

    def _determine_defense_level(self) -> DefenseLevel:
        """Determine current defense level based on system state."""
        workload = self._calculate_workload()
        faculty = self._faculty

        if faculty < 3 or workload > 3.0:
            return DefenseLevel.BLACK
        elif faculty < 4 or workload > self.config.critical_threshold:
            return DefenseLevel.RED
        elif faculty < 5 or workload > self.config.burnout_threshold:
            return DefenseLevel.ORANGE
        elif workload > self.config.burnout_threshold * 0.8:
            return DefenseLevel.YELLOW
        else:
            return DefenseLevel.GREEN

    def _process_fmit_week(self, defense_level: DefenseLevel) -> tuple[bool, bool]:
        """
        Process FMIT for this week.

        FMIT Structure (RIGID - NO ADAPTATION):
        - Friday AM → Sunday 1200: One attending (60+ hours straight)
        - Different faculty covers overnight calls until cycle repeats
        - Cannot be downregulated or adapted

        Returns: (covered, turfed_to_ob)

        FMIT MUST SURVIVE.
        """
        ***REMOVED*** Check if we're at a week boundary (every 7 days)
        if self._day % 7 != 0:
            return True, False  ***REMOVED*** Not a week boundary

        ***REMOVED*** FMIT requires:
        ***REMOVED*** 1. One faculty for the weekend block (Fri AM - Sun noon)
        ***REMOVED*** 2. Faculty available for overnight calls rest of week
        ***REMOVED*** 3. The FMIT attending is BLOCKED from clinic that week

        available_for_fmit = self._faculty - self._faculty_onboarding

        ***REMOVED*** Need at least 2: one for FMIT, one for call backup
        ***REMOVED*** Below minimum, we're in trouble
        if available_for_fmit >= 2:
            ***REMOVED*** Can cover with FM faculty
            ***REMOVED*** But check if this leaves anyone for clinic
            remaining_for_clinic = available_for_fmit - 1  ***REMOVED*** One on FMIT

            if remaining_for_clinic >= 1:
                return True, False
            else:
                ***REMOVED*** Everyone is either on FMIT or can't work
                ***REMOVED*** Risky but technically covered
                return True, False

        elif available_for_fmit == 1:
            ***REMOVED*** Only one faculty - they're on FMIT, no one for backup
            ***REMOVED*** Must turf to OB at ORANGE+
            if self.config.fmit_can_turf_to_ob and defense_level.value >= DefenseLevel.ORANGE.value:
                return True, True
            else:
                ***REMOVED*** Can't turf yet but only one faculty
                ***REMOVED*** They'll cover FMIT but clinic is devastated
                return True, False

        else:  ***REMOVED*** available_for_fmit == 0
            ***REMOVED*** No faculty available
            if self.config.fmit_can_turf_to_ob:
                return True, True  ***REMOVED*** OB must cover
            else:
                return False, False  ***REMOVED*** FMIT FAILED

    def _process_burnout_contagion(self, workload: float):
        """Process burnout spreading through team."""
        if workload <= self.config.burnout_threshold:
            ***REMOVED*** Recovery when workload is sustainable
            self._team_burnout = max(0, self._team_burnout - 0.5)
            return

        ***REMOVED*** Burnout accumulates
        burnout_increase = (workload - self.config.burnout_threshold) * 2.0

        ***REMOVED*** Contagion effect - burnout spreads
        contagion = self._team_burnout * self.config.burnout_contagion_rate

        self._team_burnout += burnout_increase + contagion

    def _process_departures(self, workload: float, call_interval: float) -> dict:
        """Process all staff departures for the day."""
        departures = {
            "faculty": 0,
            "screener_dedicated": 0,
            "screener_rn": 0,
            "screener_emt": 0,
        }

        ***REMOVED*** Faculty departures (burnout-driven)
        if self._faculty > 0:
            ***REMOVED*** Base rate
            departure_prob = self.config.base_burnout_rate

            ***REMOVED*** Workload multiplier
            if workload > self.config.burnout_threshold:
                ratio = workload / self.config.burnout_threshold
                departure_prob *= self.config.workload_burnout_multiplier * ratio

            ***REMOVED*** Call frequency multiplier
            if call_interval < self.config.sustainable_call_interval_days:
                call_stress = self.config.sustainable_call_interval_days / max(1, call_interval)
                departure_prob *= self.config.call_burnout_multiplier * call_stress

            ***REMOVED*** Team burnout contagion
            departure_prob += self._team_burnout * 0.001

            for _ in range(self._faculty):
                if self._rng.random() < departure_prob:
                    departures["faculty"] += 1
                    self._burnout_departures += 1

            self._faculty -= departures["faculty"]

        ***REMOVED*** Screener departures (higher base turnover)
        screener_base_rate = self.config.screener_turnover_rate / 365

        for _ in range(self._screener_dedicated):
            if self._rng.random() < screener_base_rate * 1.5:  ***REMOVED*** Higher during stress
                departures["screener_dedicated"] += 1
        self._screener_dedicated -= departures["screener_dedicated"]

        return departures

    def _process_arrivals(self) -> dict:
        """Process staff arrivals."""
        arrivals = {"faculty": 0, "screener": 0}

        ***REMOVED*** Faculty arrivals
        new_queue = []
        for arrival_day, is_onboarding in self._faculty_arriving:
            if arrival_day == self._day:
                self._faculty += 1
                if is_onboarding:
                    self._faculty_onboarding += 1
                arrivals["faculty"] += 1
            elif arrival_day > self._day:
                new_queue.append((arrival_day, is_onboarding))
        self._faculty_arriving = new_queue

        ***REMOVED*** Screener arrivals
        new_screener_queue = []
        for arrival_day in self._screener_arriving:
            if arrival_day == self._day:
                self._screener_dedicated += 1
                arrivals["screener"] += 1
            elif arrival_day > self._day:
                new_screener_queue.append(arrival_day)
        self._screener_arriving = new_screener_queue

        ***REMOVED*** Reduce onboarding count after onboarding period
        if self._faculty_onboarding > 0 and self._day % self.config.faculty_onboarding_days == 0:
            self._faculty_onboarding = max(0, self._faculty_onboarding - 1)

        ***REMOVED*** Try to hire replacements
        self._attempt_hiring()

        return arrivals

    def _attempt_hiring(self):
        """Attempt to hire replacements."""
        ***REMOVED*** Faculty hiring
        faculty_deficit = self.config.expected_faculty - self._faculty - len(self._faculty_arriving)
        if faculty_deficit > 0 and len(self._faculty_arriving) < 3:
            if self._rng.random() < 0.03:  ***REMOVED*** 3% daily chance to initiate hire
                arrival_day = self._day + self.config.faculty_arrival_lag_days
                self._faculty_arriving.append((arrival_day, True))  ***REMOVED*** With onboarding

        ***REMOVED*** Screener hiring (faster)
        screener_deficit = 4 - self._screener_dedicated - len(self._screener_arriving)
        if screener_deficit > 0 and len(self._screener_arriving) < 2:
            if self._rng.random() < 0.05:  ***REMOVED*** 5% daily
                arrival_day = self._day + 30  ***REMOVED*** 30 day hiring
                self._screener_arriving.append(arrival_day)

    def _calculate_clinic_coverage(self, screener_ratio: float) -> tuple[int, int]:
        """Calculate clinic sessions covered vs dropped."""
        physicians = self._calculate_effective_physicians()

        ***REMOVED*** Each physician can cover X sessions, modified by screener support
        sessions_per_physician = self.config.sessions_per_faculty_sustainable

        ***REMOVED*** Screener penalty
        if screener_ratio < self.config.minimum_screener_ratio:
            ***REMOVED*** Significant slowdown without screeners
            sessions_per_physician *= 0.6
        elif screener_ratio < self.config.optimal_screener_ratio:
            ***REMOVED*** Moderate slowdown
            efficiency = 0.6 + (0.4 * screener_ratio / self.config.optimal_screener_ratio)
            sessions_per_physician *= efficiency

        covered = int(physicians * sessions_per_physician / 5)  ***REMOVED*** Daily
        target = self.config.clinic_sessions_per_week // 5
        dropped = max(0, target - covered)

        return covered, dropped

    def _calculate_survival_score(self, state: DailyState) -> float:
        """Calculate survival score for the day."""
        score = 100.0

        ***REMOVED*** FMIT failure is catastrophic
        if not state.fmit_covered and not state.fmit_turfed_to_ob:
            score -= 50.0
        elif state.fmit_turfed_to_ob:
            score -= 10.0  ***REMOVED*** Penalty but surviving

        ***REMOVED*** Defense level penalties
        level_penalties = {
            DefenseLevel.GREEN: 0,
            DefenseLevel.YELLOW: 5,
            DefenseLevel.ORANGE: 15,
            DefenseLevel.RED: 30,
            DefenseLevel.BLACK: 50,
        }
        score -= level_penalties[state.defense_level]

        ***REMOVED*** Workload penalty
        if state.workload_per_physician > self.config.critical_threshold:
            score -= 20
        elif state.workload_per_physician > self.config.burnout_threshold:
            score -= 10

        ***REMOVED*** Screener ratio penalty
        if state.screener_ratio < self.config.minimum_screener_ratio:
            score -= 10

        return max(0, score)

    def _simulate_day(self) -> DailyState:
        """Simulate a single day."""
        ***REMOVED*** Calculate metrics
        effective_physicians = self._calculate_effective_physicians()
        screener_ratio = self._calculate_screener_ratio()
        workload = self._calculate_workload()
        call_interval = self._calculate_call_interval()
        intern_competency = self._calculate_intern_competency()
        defense_level = self._determine_defense_level()

        ***REMOVED*** Process FMIT
        fmit_covered, fmit_turfed = self._process_fmit_week(defense_level)
        if self._day % 7 == 0:
            if fmit_covered and not fmit_turfed:
                self._fmit_covered += 1
            elif fmit_turfed:
                self._fmit_turfed += 1
            else:
                self._fmit_failed += 1

        ***REMOVED*** Process burnout contagion
        self._process_burnout_contagion(workload)

        ***REMOVED*** Process departures and arrivals
        departures = self._process_departures(workload, call_interval)
        arrivals = self._process_arrivals()

        ***REMOVED*** Calculate clinic coverage
        covered, dropped = self._calculate_clinic_coverage(screener_ratio)

        ***REMOVED*** Build state
        state = DailyState(
            day=self._day,
            faculty_count=self._faculty,
            faculty_onboarding=self._faculty_onboarding,
            screener_dedicated=self._screener_dedicated,
            screener_rn_active=getattr(self, '_rn_active', 0),
            screener_emt_active=getattr(self, '_emt_active', 0),
            intern_count=self._interns,
            senior_count=self._seniors,
            effective_faculty=self._faculty - (self._faculty_onboarding * 0.5),
            effective_physicians=effective_physicians,
            screener_ratio=screener_ratio,
            workload_per_physician=workload,
            call_interval_days=call_interval,
            intern_competency=intern_competency,
            defense_level=defense_level,
            fmit_covered=fmit_covered,
            fmit_turfed_to_ob=fmit_turfed,
            clinic_sessions_covered=covered,
            clinic_sessions_dropped=dropped,
            departures=departures,
            arrivals=arrivals,
            burnout_score=self._team_burnout,
        )

        state.survival_score = self._calculate_survival_score(state)

        self._states.append(state)
        self._day += 1

        return state

    def _generate_recommendations(self) -> list[str]:
        """Generate survival recommendations."""
        recs = []

        if self._fmit_failed > 0:
            recs.append(
                f"🔴 FMIT FAILED {self._fmit_failed} weeks. "
                "Unacceptable. Need immediate faculty or permanent OB agreement."
            )

        if self._fmit_turfed > 0:
            recs.append(
                f"🟠 FMIT turfed to OB {self._fmit_turfed} weeks. "
                "Survival mode - but mission continues."
            )

        if self._faculty < self.config.minimum_faculty_for_fmit:
            recs.append(
                f"🔴 Faculty ({self._faculty}) below FMIT minimum ({self.config.minimum_faculty_for_fmit}). "
                "Request emergency locums immediately."
            )

        if self._burnout_departures > 0:
            recs.append(
                f"⚠️ {self._burnout_departures} burnout-driven departures. "
                "Workload reduction critical to retain remaining staff."
            )

        ***REMOVED*** Screener recommendations
        if self._screener_dedicated < 2:
            recs.append(
                "🟠 Screener shortage. Activate RN/EMT fallback. "
                "Enable intern stagger to maximize coverage."
            )

        return recs

    def run(self) -> CompoundStressResult:
        """
        Run the compound stress simulation.

        Objective: SURVIVE
        FMIT must continue.
        """
        self._reset()

        ***REMOVED*** Run simulation
        while self._day < self.config.duration_days:
            state = self._simulate_day()

            ***REMOVED*** Check for total collapse
            if self._faculty < self.config.minimum_faculty_for_fmit - 2:
                break  ***REMOVED*** Below minimum viable

        ***REMOVED*** Calculate summary metrics
        states = self._states

        days_in_crisis = sum(
            1 for s in states
            if s.defense_level in (DefenseLevel.RED, DefenseLevel.BLACK)
        )

        days_below_min_ratio = sum(
            1 for s in states
            if s.screener_ratio < self.config.minimum_screener_ratio
        )

        rn_fallback_days = sum(1 for s in states if s.screener_rn_active > 0)
        emt_fallback_days = sum(1 for s in states if s.screener_emt_active > 0)

        peak_workload = max(s.workload_per_physician for s in states)
        peak_call = min(s.call_interval_days for s in states if s.call_interval_days > 0)

        ***REMOVED*** FMIT survival is THE metric
        fmit_survived = self._fmit_failed == 0

        return CompoundStressResult(
            config=self.config,
            survived=self._faculty >= self.config.minimum_faculty_for_fmit - 2,
            fmit_survived=fmit_survived,
            days_survived=self._day,
            final_faculty=self._faculty,
            final_screeners=self._screener_dedicated,
            final_defense_level=states[-1].defense_level if states else DefenseLevel.BLACK,
            fmit_weeks_covered=self._fmit_covered,
            fmit_weeks_turfed=self._fmit_turfed,
            fmit_weeks_failed=self._fmit_failed,
            peak_workload=peak_workload,
            peak_call_frequency=peak_call,
            days_in_crisis=days_in_crisis,
            total_burnout_departures=self._burnout_departures,
            days_below_min_screener_ratio=days_below_min_ratio,
            rn_fallback_days=rn_fallback_days,
            emt_fallback_days=emt_fallback_days,
            states=states,
            recommendations=self._generate_recommendations(),
        )


def run_compound_monte_carlo(config: CompoundStressConfig, n_runs: int = 100) -> dict:
    """Run Monte Carlo for compound stress scenario."""
    results = []

    for seed in range(n_runs):
        cfg = CompoundStressConfig(
            initial_faculty=config.initial_faculty,
            expected_faculty=config.expected_faculty,
            initial_screeners_dedicated=config.initial_screeners_dedicated,
            initial_screeners_rn=config.initial_screeners_rn,
            initial_screeners_emt=config.initial_screeners_emt,
            initial_interns=config.initial_interns,
            initial_seniors=config.initial_seniors,
            seed=seed,
        )
        scenario = CompoundStressScenario(cfg)
        results.append(scenario.run())

    ***REMOVED*** Aggregate
    survived_count = sum(1 for r in results if r.survived)
    fmit_survived_count = sum(1 for r in results if r.fmit_survived)

    return {
        "n_runs": n_runs,
        "survival_rate": survived_count / n_runs,
        "fmit_survival_rate": fmit_survived_count / n_runs,  ***REMOVED*** THE METRIC
        "avg_days_survived": sum(r.days_survived for r in results) / n_runs,
        "avg_fmit_turfed": sum(r.fmit_weeks_turfed for r in results) / n_runs,
        "avg_fmit_failed": sum(r.fmit_weeks_failed for r in results) / n_runs,
        "avg_burnout_departures": sum(r.total_burnout_departures for r in results) / n_runs,
        "avg_days_crisis": sum(r.days_in_crisis for r in results) / n_runs,
    }
