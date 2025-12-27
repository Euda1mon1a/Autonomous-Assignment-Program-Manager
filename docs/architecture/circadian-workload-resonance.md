# Circadian-Workload Resonance Patterns

> **Document Status:** Technical Reference
> **Last Updated:** 2025-12-27
> **Module:** `backend/app/frms/`
> **Related:** Aviation FRMS Integration, Three-Process Model

---

## Executive Summary

**Circadian-Workload Resonance** describes the phenomenon where work scheduling patterns interact with human biological rhythms to either amplify or dampen fatigue effects. When work schedules "resonate" negatively with circadian rhythms, the combined effect is greater than either factor alone—leading to disproportionately elevated fatigue and error risk.

This document catalogs known resonance patterns in medical residency scheduling and provides detection/mitigation strategies implemented in the FRMS module.

---

## Table of Contents

1. [Biological Background](#biological-background)
2. [Resonance Patterns Catalog](#resonance-patterns-catalog)
3. [Detection Algorithms](#detection-algorithms)
4. [Mitigation Strategies](#mitigation-strategies)
5. [Integration with FRMS](#integration-with-frms)
6. [Validation Evidence](#validation-evidence)

---

## Biological Background

### The Circadian System

The human circadian system is a ~24-hour internal clock that regulates:

- **Core body temperature** (nadir at ~4:00 AM)
- **Cortisol secretion** (peak at ~8:00 AM, nadir at midnight)
- **Melatonin secretion** (rises at dusk, peaks at ~2:00 AM)
- **Alertness/performance** (peak at 9-11 AM and 7-9 PM)
- **Sleep propensity** (maximum at 2-6 AM)

### Window of Circadian Low (WOCL)

The **Window of Circadian Low** (2:00-6:00 AM) represents the period of:
- Minimum core body temperature
- Maximum melatonin levels
- Minimum cortisol levels
- Maximum sleep propensity
- 20-30% slower reaction times
- 2-3x higher error rates

### Resonance Effect

When work patterns align with circadian vulnerabilities, the effects compound:

```
Total Fatigue Risk = Base Fatigue × Circadian Modifier × Resonance Amplifier
```

Where resonance amplifiers can range from 1.0 (no resonance) to 3.0+ (severe resonance).

---

## Resonance Patterns Catalog

### Pattern 1: WOCL Procedure Scheduling

**Description:** High-risk procedures scheduled during 2:00-6:00 AM window.

**Resonance Mechanism:**
- Circadian alertness at minimum
- Sleep inertia if awakened for procedure
- Reduced fine motor precision
- Impaired decision-making

**Risk Amplifier:** 2.0-3.0x

**Clinical Examples:**
- Central line placement at 3:00 AM
- Emergency intubation at 4:00 AM
- Conscious sedation during overnight call

**Detection:**
```python
def detect_wocl_procedure(assignment):
    """Detect high-risk procedures in WOCL window."""
    if assignment.start_hour in range(2, 6):
        if assignment.has_procedure:
            return {
                "pattern": "wocl_procedure",
                "severity": "high",
                "amplifier": 2.5,
            }
    return None
```

**Mitigation:**
1. Defer non-emergent procedures to 6:00+ AM
2. Require attending presence for WOCL procedures
3. Implement procedure checklists for WOCL periods
4. Limit junior resident procedures during WOCL

---

### Pattern 2: Rotating Shift Desynchronization

**Description:** Rapid rotation between day and night shifts that prevents circadian adaptation.

**Resonance Mechanism:**
- Internal clock never synchronizes with work schedule
- Chronic partial sleep deprivation compounds
- Gastrointestinal and cardiovascular stress
- "Perpetual jet lag" effect

**Risk Amplifier:** 1.5-2.5x

**Problematic Patterns:**
- Day → Night → Day within same week
- Irregular start times (7 AM, then 11 PM, then 6 AM)
- "Split" rotations with mid-week day/night switches

**Detection:**
```python
def detect_rotation_desync(schedule_history, days=14):
    """Detect destabilizing rotation patterns."""
    day_shifts = count_shifts_by_type(schedule_history, "day")
    night_shifts = count_shifts_by_type(schedule_history, "night")
    transitions = count_day_night_transitions(schedule_history)

    if transitions >= 3 and days <= 14:
        return {
            "pattern": "rotation_desync",
            "severity": "high",
            "transitions_per_week": transitions / 2,
            "amplifier": 1.5 + (transitions * 0.2),
        }
    return None
```

**Mitigation:**
1. Cluster night shifts (3-4 consecutive nights)
2. Allow 48-72 hours for circadian transition
3. Use "forward rotation" (days → evenings → nights)
4. Avoid more than 2 day/night transitions per month

---

### Pattern 3: Early Morning Start Syndrome

**Description:** Shifts starting 5:00-7:00 AM causing chronic sleep curtailment.

**Resonance Mechanism:**
- Requires wake time during high sleep propensity
- Biological clock still releasing melatonin
- Cumulative sleep debt over weeks
- Morning commute adds to pre-shift fatigue

**Risk Amplifier:** 1.3-1.8x

**Contributing Factors:**
- Long commute times
- Evening obligations preventing early bedtime
- Social/family pressures on sleep timing

**Detection:**
```python
def detect_early_start_syndrome(schedule, typical_bedtime=23.0):
    """Detect chronic early morning start patterns."""
    early_starts = sum(1 for s in schedule if 5.0 <= s.start_hour < 7.0)

    # Calculate implied sleep duration
    required_wake_time = min(s.start_hour for s in schedule if s.start_hour < 7.0) - 1.0
    implied_sleep = required_wake_time - typical_bedtime
    if implied_sleep < 0:
        implied_sleep += 24

    if early_starts >= 3 and implied_sleep < 6.0:
        return {
            "pattern": "early_start_syndrome",
            "severity": "moderate",
            "implied_sleep_hours": implied_sleep,
            "amplifier": 1.5,
        }
    return None
```

**Mitigation:**
1. Shift OR start times to 7:30-8:00 AM when possible
2. Educate on sleep timing discipline
3. Consider proximity for early-start assignments
4. Limit consecutive early starts to 5 days

---

### Pattern 4: Post-Night Recovery Failure

**Description:** Insufficient recovery time after night shift series before returning to day shifts.

**Resonance Mechanism:**
- Circadian system still adapted to night schedule
- Day sleep less restorative than night sleep
- 3-7 days needed for full re-adaptation
- "Social jet lag" from weekend activities

**Risk Amplifier:** 1.4-2.0x

**Detection:**
```python
def detect_recovery_failure(schedule):
    """Detect insufficient post-night recovery."""
    night_series = find_consecutive_nights(schedule)

    for series in night_series:
        last_night = series[-1].date
        next_day_shift = find_next_day_shift(schedule, last_night)

        if next_day_shift:
            recovery_hours = (next_day_shift.start - series[-1].end).total_hours()

            if recovery_hours < 48:
                return {
                    "pattern": "recovery_failure",
                    "severity": "high",
                    "nights_worked": len(series),
                    "recovery_hours": recovery_hours,
                    "amplifier": 2.0 - (recovery_hours / 48) * 0.6,
                }
    return None
```

**Mitigation:**
1. Require 48-hour minimum before day shift return
2. Use "recovery day" concept (no clinical duties)
3. Schedule light clinic after night series
4. Avoid early morning starts immediately after nights

---

### Pattern 5: Cumulative Debt Cascade

**Description:** Progressive sleep debt accumulation across a block/rotation without adequate recovery.

**Resonance Mechanism:**
- Each day adds to sleep debt
- Recovery sleep only partially restores
- Debt compounds with interest (fatigue begets poor sleep)
- Eventual "crash" or performance collapse

**Risk Amplifier:** Variable (starts 1.0, can reach 4.0+)

**Trajectory:**
```
Day 1: Debt = 1 hour, Amplifier = 1.0
Day 3: Debt = 4 hours, Amplifier = 1.2
Day 5: Debt = 8 hours, Amplifier = 1.5
Day 7: Debt = 12+ hours, Amplifier = 2.0+
Day 10+: Debt = 20+ hours, Amplifier = 3.0+
```

**Detection:**
```python
def detect_debt_cascade(person_state, days=7):
    """Detect cumulative sleep debt cascade."""
    debt = person_state.cumulative_debt
    days_since_recovery = person_state.days_since_full_day_off

    if debt > 8.0 or days_since_recovery > 6:
        amplifier = 1.0 + (debt / 10.0) + (days_since_recovery / 14.0)
        return {
            "pattern": "debt_cascade",
            "severity": "critical" if amplifier > 2.0 else "high",
            "cumulative_debt_hours": debt,
            "days_without_recovery": days_since_recovery,
            "amplifier": min(amplifier, 4.0),
        }
    return None
```

**Mitigation:**
1. ACGME 1-in-7 rule enforcement (but biological need is often more)
2. Strategic "recovery days" within block
3. Monitor fatigue scores for cascade detection
4. Automatic workload reduction triggers

---

### Pattern 6: Post-Call Circadian Disruption

**Description:** Attempting normal activities after 24+ hour call shift when circadian system expects sleep.

**Resonance Mechanism:**
- Extended wakefulness compounds circadian low
- "Second wind" effect masks true fatigue
- Post-call sleep often fragmented
- Driving hazard period 6:00-10:00 AM post-call

**Risk Amplifier:** 2.0-3.5x (peaks 6:00-9:00 AM post-call)

**Detection:**
```python
def detect_post_call_disruption(call_end_time, next_activity_time):
    """Detect post-call circadian danger zone."""
    hours_since_call = (next_activity_time - call_end_time).total_hours()

    # Danger zone: 0-4 hours after call ending in early morning
    if call_end_time.hour in range(6, 10):
        if hours_since_call < 4:
            return {
                "pattern": "post_call_disruption",
                "severity": "critical",
                "danger_activity": "driving" if next_activity_time.is_commute else "clinical",
                "amplifier": 3.0,
            }
    return None
```

**Mitigation:**
1. Mandatory 10-hour rest post-call (ACGME)
2. Offer taxi/ride-share for post-call commute
3. No patient care activities until minimum rest
4. Caffeine nap strategy before commute

---

### Pattern 7: Weekend Call Circadian Shift

**Description:** Weekend call disrupting established weekday circadian rhythm.

**Resonance Mechanism:**
- "Social jet lag" from weekend sleep timing
- Abrupt transition from late weekend sleep to Sunday night call
- Pre-call anxiety affecting sleep
- Monday re-adaptation required

**Risk Amplifier:** 1.3-1.7x

**Detection:**
```python
def detect_weekend_call_shift(schedule):
    """Detect circadian disruption from weekend call patterns."""
    weekend_calls = [s for s in schedule if s.is_weekend and s.is_call]

    for call in weekend_calls:
        friday_activity = get_friday_end_time(schedule)

        if friday_activity and friday_activity.hour > 20:
            # Late Friday -> early weekend call
            return {
                "pattern": "weekend_call_shift",
                "severity": "moderate",
                "transition_hours": 24 - friday_activity.hour + call.start_hour,
                "amplifier": 1.5,
            }
    return None
```

**Mitigation:**
1. Consistent weekend wake times even when not on call
2. Pre-call "phase advance" sleep strategy
3. Light weekend schedules before weekend call
4. Minimize Friday night social activities before weekend call

---

## Detection Algorithms

### Composite Resonance Score

The FRMS module calculates a composite resonance score by evaluating all patterns:

```python
def calculate_composite_resonance(person_id, schedule, current_time):
    """
    Calculate composite circadian-workload resonance score.

    Returns:
        float: Resonance amplifier (1.0 = no resonance, higher = worse)
    """
    detections = []

    # Check all patterns
    patterns = [
        detect_wocl_procedure,
        detect_rotation_desync,
        detect_early_start_syndrome,
        detect_recovery_failure,
        detect_debt_cascade,
        detect_post_call_disruption,
        detect_weekend_call_shift,
    ]

    for detect_fn in patterns:
        result = detect_fn(schedule)
        if result:
            detections.append(result)

    if not detections:
        return 1.0

    # Combine amplifiers (multiplicative with diminishing returns)
    composite = 1.0
    for detection in sorted(detections, key=lambda d: d["amplifier"], reverse=True):
        # Each additional pattern adds diminishing amplification
        marginal = (detection["amplifier"] - 1.0) * 0.7
        composite += marginal

    return min(composite, 5.0)  # Cap at 5x amplification
```

### Real-Time Detection

The monitoring module continuously evaluates resonance patterns:

```python
class ResonanceMonitor:
    """Real-time circadian-workload resonance detection."""

    def __init__(self, fatigue_monitor):
        self.fatigue_monitor = fatigue_monitor
        self.pattern_history = defaultdict(list)

    def evaluate(self, person_id, current_schedule, current_time):
        """Evaluate resonance risk for a person."""
        resonance = calculate_composite_resonance(
            person_id, current_schedule, current_time
        )

        # Adjust effectiveness by resonance
        base_effectiveness = self.fatigue_monitor.get_effectiveness(person_id)
        adjusted = base_effectiveness / resonance

        # Generate alerts if resonance is high
        if resonance > 2.0:
            self._generate_resonance_alert(person_id, resonance)

        return {
            "base_effectiveness": base_effectiveness,
            "resonance_amplifier": resonance,
            "adjusted_effectiveness": adjusted,
            "active_patterns": self._get_active_patterns(person_id),
        }
```

---

## Mitigation Strategies

### Scheduler Integration

The FRMS constraint generator uses resonance patterns to influence scheduling:

```python
class ResonanceAwareConstraint(SoftConstraint):
    """Constraint that penalizes resonance-inducing schedules."""

    def calculate_penalty(self, proposed_assignment, current_schedule):
        # Project schedule with proposed assignment
        test_schedule = current_schedule + [proposed_assignment]

        # Calculate resonance
        resonance = calculate_composite_resonance(
            proposed_assignment.person_id,
            test_schedule,
            proposed_assignment.start_time,
        )

        # Penalty proportional to resonance above 1.0
        if resonance > 1.0:
            return self.weight * (resonance - 1.0) * 100
        return 0
```

### Intervention Recommendations

Based on detected patterns, the system generates specific interventions:

| Pattern | Intervention Level | Recommended Actions |
|---------|-------------------|---------------------|
| WOCL Procedure | Immediate | Delay procedure or add supervision |
| Rotation Desync | Schedule Change | Cluster shifts, add transition days |
| Early Start | Education | Sleep timing counseling |
| Recovery Failure | Mandatory | Block schedule modification |
| Debt Cascade | Urgent | Mandatory rest day |
| Post-Call Disruption | Immediate | Transportation assistance |
| Weekend Shift | Proactive | Sleep strategy coaching |

---

## Integration with FRMS

### Three-Process Model Extension

Resonance effects are integrated into the Three-Process Model:

```python
class ThreeProcessModel:
    """Extended with resonance awareness."""

    def calculate_effectiveness(self, state, time_of_day, schedule=None):
        # Base three-process calculation
        base_score = self._calculate_base_effectiveness(state, time_of_day)

        # Apply resonance modification if schedule provided
        if schedule:
            resonance = calculate_composite_resonance(
                state.person_id, schedule, state.timestamp
            )
            return EffectivenessScore(
                overall=base_score.overall / resonance,
                resonance_amplifier=resonance,
                resonance_patterns=self._get_patterns(schedule),
                ...
            )

        return base_score
```

### QUBO Penalty Terms

Resonance patterns add penalty terms to the QUBO optimization:

```python
def add_resonance_penalties(Q, formulation, context):
    """Add resonance-aware penalties to QUBO matrix."""

    for resident in context.residents:
        for block in context.blocks:
            # Project resonance if this assignment is made
            projected_resonance = estimate_resonance(
                resident.id, block, context.existing_assignments
            )

            if projected_resonance > 1.2:
                penalty = RESONANCE_PENALTY_BASE * (projected_resonance - 1.0)
                # Add to diagonal (linear term)
                idx = get_variable_index(resident, block)
                Q[(idx, idx)] += penalty
```

---

## Validation Evidence

### Aviation Studies

| Study | Finding | Relevance |
|-------|---------|-----------|
| FAA CAMI 2009-2010 | WOCL errors 2.8x higher | Pattern 1 validation |
| NASA Ames 2006 | Rotation desync increases lapses 1.9x | Pattern 2 validation |
| NTSB Fatigue Reviews | Post-call driving accidents peak 6-9 AM | Pattern 6 validation |

### Medical Studies

| Study | Finding | Relevance |
|-------|---------|-----------|
| Barger 2006 (NEJM) | Night residents 61% higher serious error rate | WOCL/Night validation |
| Landrigan 2004 | Extended shifts 36% more serious errors | Debt cascade validation |
| Lockley 2004 | Call-related attentional failures 2.0x | Post-call validation |

### Implementation Metrics

Target validation metrics for FRMS resonance detection:

| Metric | Target | Method |
|--------|--------|--------|
| Pattern Detection Sensitivity | >80% | vs. self-reported resonance |
| Specificity | >70% | Avoid false alarms |
| Correlation with Errors | r > 0.3 | Error report correlation |
| Intervention Effectiveness | 30% reduction | Pre/post comparison |

---

## References

1. Borbély, A.A. (1982). A two process model of sleep regulation. Human Neurobiology.
2. Hursh, S.R. et al. (2004). Fatigue models for applied research in warfighting. Aviation, Space, and Environmental Medicine.
3. Folkard, S. & Tucker, P. (2003). Shift work, safety and productivity. Occupational Medicine.
4. Barger, L.K. et al. (2006). Extended work shifts and neurobehavioral errors. NEJM.
5. FAA (2012). 14 CFR Part 117 - Flight Crew Member Duty and Rest Requirements.
6. ICAO (2016). Doc 9966 - Manual for the Oversight of Fatigue Management Approaches.

---

*This document is part of the FRMS module documentation. For implementation details, see `backend/app/frms/` source code.*
