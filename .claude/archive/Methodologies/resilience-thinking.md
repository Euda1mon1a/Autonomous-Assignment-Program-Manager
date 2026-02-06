# Resilience Thinking Methodology

**Purpose:** Design systems to anticipate, withstand, and recover from failures

---

## When to Use This Methodology

Apply when:
- Designing new schedule features
- Analyzing system vulnerabilities
- Planning for absences or disruptions
- Evaluating schedule quality
- Responding to failures

---

## Core Philosophy

> "Hope is not a strategy. Design for failure, not just success."

### Resilience vs Robustness

| Aspect | Robustness | Resilience |
|--------|-----------|-----------|
| **Goal** | Prevent failure | Recover from failure |
| **Approach** | Strengthen components | Enable graceful degradation |
| **Cost** | High (over-engineer) | Moderate (smart redundancy) |
| **Failure Mode** | Brittle (catastrophic) | Graceful (degraded service) |

**Example:**
- **Robustness:** Ensure no faculty ever absent → Impossible
- **Resilience:** Plan for absences, have backup coverage → Practical

---

## Failure Mode Identification

### FMEA (Failure Modes and Effects Analysis)

#### Step 1: Identify Components

```
System: Residency Scheduler
Components:
├── People (residents, faculty)
├── Rotations (clinic types)
├── Assignments (who-what-when)
├── Constraints (rules)
└── Data (database, backups)
```

#### Step 2: List Failure Modes

| Component | Failure Mode | Likelihood | Severity | RPN |
|-----------|-------------|------------|----------|-----|
| Faculty | Unexpected absence | High | High | 16 |
| Faculty | Loss of credentials | Medium | High | 12 |
| Resident | Medical leave | Medium | Medium | 9 |
| Resident | Deployment (military) | Low | High | 8 |
| Database | Corruption | Low | Critical | 12 |
| Solver | Infeasible result | Medium | Medium | 9 |
| API | Downtime | Low | High | 8 |

**RPN = Risk Priority Number** (Likelihood × Severity × Detectability)

#### Step 3: Rank by Risk

**Priority:**
1. Faculty unexpected absence (RPN 16)
2. Database corruption (RPN 12)
3. Faculty credential loss (RPN 12)

#### Step 4: Design Mitigations

| Failure | Mitigation | Type |
|---------|-----------|------|
| Faculty absence | N-1 contingency planning | Preventive |
| Database corruption | Automated backups | Detective |
| Credential loss | 30-day expiry alerts | Preventive |
| Solver infeasible | Constraint relaxation fallback | Corrective |

---

## Redundancy Planning

### Types of Redundancy

#### 1. Hot Standby (Active)

**Example:** Multiple faculty qualified for same rotation

```python
rotation_coverage = {
    "procedures_full_day": {
        "required": 1,
        "qualified": ["FAC-PD", "FAC-002", "FAC-005"],
        "redundancy_factor": 3.0,  # 3 qualified for 1 slot
        "status": "resilient"
    },
    "peds_clinic": {
        "required": 2,
        "qualified": ["FAC-001", "FAC-003"],
        "redundancy_factor": 1.0,  # 2 qualified for 2 slots
        "status": "vulnerable"
    }
}
```

**Goal:** Redundancy factor ≥ 1.5 (N-1 compliance)

#### 2. Warm Standby (Trainable)

**Example:** Faculty who could be cross-trained

```python
cross_training_candidates = {
    "procedures_full_day": {
        "current": ["FAC-PD"],
        "trainable": ["FAC-002", "FAC-005"],
        "training_time": "3-6 months",
        "priority": "P0"  # Only 1 qualified, critical SPOF
    }
}
```

#### 3. Cold Standby (Emergency)

**Example:** Retired faculty who could be recalled

```python
emergency_reserves = {
    "faculty": [
        {
            "id": "FAC-RETIRED-01",
            "status": "inactive",
            "can_cover": ["inpatient", "peds_clinic"],
            "activation_time": "7 days",
            "cost": "high"
        }
    ]
}
```

### N-1 and N-2 Analysis

#### N-1 Contingency

**Definition:** System remains functional with any single component failure

```python
def check_n1_compliance(schedule):
    """
    Test each person removal individually.

    For each person:
    1. Remove from schedule
    2. Check if remaining coverage meets minimums
    3. Verify no ACGME violations introduced
    4. Estimate recovery effort (hours)
    """
    failures = []

    for person in people:
        temp_schedule = schedule.remove_person(person)

        if not meets_minimum_coverage(temp_schedule):
            failures.append({
                "person": person,
                "impact": "critical",
                "affected_rotations": get_uncovered_rotations(temp_schedule),
                "recovery_impossible": True
            })
        elif creates_acgme_violations(temp_schedule):
            failures.append({
                "person": person,
                "impact": "moderate",
                "recovery_possible": True,
                "recovery_hours": estimate_recovery_time(temp_schedule)
            })

    return {
        "compliant": len(failures) == 0,
        "failures": failures
    }
```

**Compliance Target:** Zero critical failures

#### N-2 Contingency

**Definition:** System degrades gracefully with any two component failures

```python
def check_n2_compliance(schedule):
    """
    Test all pairs of people removals.

    Computationally expensive: O(n²) combinations.
    Focus on critical pairs.
    """
    critical_pairs = []

    for person1, person2 in combinations(people, 2):
        temp_schedule = schedule.remove_people([person1, person2])

        impact = assess_impact(temp_schedule)

        if impact == "catastrophic":
            critical_pairs.append({
                "people": [person1, person2],
                "impact": impact,
                "recovery_impossible": True,
                "reason": "No backup coverage available"
            })

    return {
        "compliant": len(critical_pairs) == 0,
        "critical_pairs": critical_pairs
    }
```

**Compliance Target:** Zero catastrophic pairs (acceptable to have degraded service)

---

## Recovery Time Objectives (RTO)

### Define RTO Targets

| Failure Scenario | RTO Target | Recovery Method |
|------------------|------------|----------------|
| Single faculty absence | 4 hours | Automatic swap matching |
| Critical faculty absence | 24 hours | Manual reassignment |
| Dual faculty absence | 48 hours | Schedule regeneration |
| Database corruption | 1 hour | Restore from backup |
| Solver failure | 2 hours | Fallback algorithm |
| Mass absence (pandemic) | 7 days | Activate static fallback |

### Recovery Time Estimation

```python
def estimate_recovery_time(failure_scenario):
    """
    Estimate time to restore service after failure.

    Factors:
    - Availability of backup resources
    - Complexity of reassignment
    - Need for approvals
    - Constraint satisfaction difficulty
    """
    if failure_scenario.has_automatic_backup:
        base_time = 1  # hours
    elif failure_scenario.has_warm_backup:
        base_time = 4  # hours
    else:
        base_time = 24  # hours (manual intervention)

    # Adjust for complexity
    complexity_multiplier = 1.0

    if failure_scenario.affects_multiple_rotations:
        complexity_multiplier *= 1.5

    if failure_scenario.creates_acgme_violations:
        complexity_multiplier *= 2.0

    if failure_scenario.requires_policy_exception:
        complexity_multiplier *= 3.0

    return base_time * complexity_multiplier
```

---

## Defense in Depth

### Five-Layer Defense Model

#### Layer 1: GREEN (Normal Operations)

**Status:** All systems nominal

**Criteria:**
- Utilization < 80%
- N-1 compliant
- Coverage rate > 90%
- Zero ACGME violations

**Response:** Proactive optimization

```python
def green_zone_actions():
    return [
        "Optimize for preferences and fairness",
        "Build additional slack capacity",
        "Cross-train personnel",
        "Update static fallback schedules"
    ]
```

#### Layer 2: YELLOW (Early Warning)

**Status:** Approaching capacity limits

**Criteria:**
- Utilization 80-85%
- N-1 violations in 1-2 areas
- Coverage rate 85-90%
- ACGME warnings (not violations)

**Response:** Preventive action

```python
def yellow_zone_actions():
    return [
        "Reduce assignments for high-utilization personnel",
        "Activate warm standby resources",
        "Defer non-essential rotations",
        "Increase monitoring frequency",
        "Alert leadership"
    ]
```

#### Layer 3: ORANGE (Degraded)

**Status:** Significant capacity constraints

**Criteria:**
- Utilization 85-90%
- N-2 non-compliant
- Coverage rate 80-85%
- Minor ACGME violations

**Response:** Load shedding

```python
def orange_zone_actions():
    return [
        "Activate sacrifice hierarchy (defer lowest priority rotations)",
        "Request policy exceptions for constraints",
        "Activate cold standby resources",
        "Daily senior leadership briefings",
        "Prepare contingency plans"
    ]
```

#### Layer 4: RED (Critical)

**Status:** Minimal viable service

**Criteria:**
- Utilization > 90%
- N-1 non-compliant
- Coverage rate 70-80%
- Multiple ACGME violations

**Response:** Crisis management

```python
def red_zone_actions():
    return [
        "Activate incident command",
        "Implement static fallback schedule",
        "Request external support (other programs)",
        "Suspend non-critical services",
        "Hourly status updates",
        "Document all exceptions"
    ]
```

#### Layer 5: BLACK (Failure)

**Status:** Cannot maintain safe operations

**Criteria:**
- Utilization > 100%
- Coverage rate < 70%
- Critical ACGME violations
- Patient safety concerns

**Response:** Shutdown/escalation

```python
def black_zone_actions():
    return [
        "Escalate to ACGME and hospital leadership",
        "Request program suspension if needed",
        "Activate disaster recovery plan",
        "Protect residents from unsafe conditions",
        "Document for regulatory review"
    ]
```

### Escalation Triggers

```python
def check_defense_level(metrics):
    """
    Determine current defense level and check for escalation.
    """
    if metrics.utilization > 1.0 or metrics.coverage < 0.7:
        return "BLACK", escalate_to_leadership()

    elif metrics.utilization > 0.9 or metrics.acgme_violations > 3:
        return "RED", activate_incident_response()

    elif metrics.utilization > 0.85 or metrics.n2_compliant is False:
        return "ORANGE", implement_load_shedding()

    elif metrics.utilization > 0.80 or len(metrics.n1_failures) > 0:
        return "YELLOW", preventive_actions()

    else:
        return "GREEN", continue_optimization()
```

---

## Homeostasis and Feedback Loops

### Self-Regulating Systems

#### Negative Feedback (Stabilizing)

**Example:** Workload balancing

```python
class WorkloadBalancingLoop:
    """
    Negative feedback loop to maintain fairness.

    When workload imbalance increases:
    1. Detect: Gini coefficient rises
    2. React: Assign fewer shifts to overloaded people
    3. Stabilize: Gini coefficient falls back to target
    """

    def __init__(self, target_gini=0.15):
        self.target_gini = target_gini

    def feedback(self, current_gini):
        error = current_gini - self.target_gini

        if error > 0.05:  # Significant imbalance
            return "reduce_assignments_for_overloaded"
        elif error < -0.05:  # Too balanced (may sacrifice coverage)
            return "allow_more_variance"
        else:
            return "maintain"
```

#### Positive Feedback (Alert for Runaway)

**Example:** Burnout cascade

```python
class BurnoutCascadeDetector:
    """
    Positive feedback loop detection (bad).

    When one person burns out:
    1. They take leave
    2. Workload redistributed to others
    3. Others become overloaded
    4. More burnout → Cascade failure

    Detection: Break the loop before cascade.
    """

    def detect_cascade(self, utilization_history):
        for person in people:
            recent_utilization = utilization_history[person][-4:]  # Last 4 weeks

            if all(u > 0.85 for u in recent_utilization):
                # Sustained high utilization → High burnout risk
                return {
                    "person": person,
                    "risk": "critical",
                    "action": "immediate_load_reduction",
                    "cascade_potential": True
                }
```

### Equilibrium Seeking (Le Chatelier's Principle)

**From chemistry:** System responds to disturbances by shifting to counteract them

**Application:** Schedule self-correction

```python
def apply_le_chatelier(schedule, disturbance):
    """
    When external change disrupts schedule balance,
    system shifts to restore equilibrium.

    Example:
    - Disturbance: Faculty absence
    - Response: Increase resident assignments slightly
    - New equilibrium: Coverage maintained, utilization rises slightly
    """
    if disturbance.type == "person_absence":
        affected_rotations = schedule.get_rotations_for(disturbance.person)

        # Find people with spare capacity (below utilization threshold)
        available = [p for p in people if p.utilization < 0.75]

        # Redistribute assignments to restore coverage
        for rotation in affected_rotations:
            schedule.reassign(rotation, from_person=disturbance.person,
                             to_person=select_best_match(available, rotation))

        return schedule  # New equilibrium reached
```

---

## Blast Radius Isolation

### Containment Zones

**From AWS:** Limit failure propagation

```python
class RotationZones:
    """
    Isolate rotations into independent zones.

    If one zone fails, others continue normally.
    """

    zones = {
        "zone_1_inpatient": {
            "rotations": ["inpatient"],
            "people": ["PGY1-01", "PGY1-02", "FAC-001"],
            "isolated": True
        },
        "zone_2_clinic": {
            "rotations": ["peds_clinic", "adult_clinic"],
            "people": ["PGY2-01", "FAC-002", "FAC-003"],
            "isolated": True
        },
        "zone_3_procedures": {
            "rotations": ["procedures_full_day", "procedures_half_day"],
            "people": ["PGY3-01", "FAC-PD"],
            "isolated": True
        }
    }

    def assess_blast_radius(self, failure):
        """
        If failure occurs in zone_1, only zone_1 affected.
        Zones 2 and 3 continue normally.
        """
        affected_zone = self.find_zone(failure.person)

        return {
            "affected_zone": affected_zone,
            "affected_rotations": affected_zone["rotations"],
            "isolated": affected_zone["isolated"],
            "blast_radius": len(affected_zone["rotations"]),
            "total_rotations": sum(len(z["rotations"]) for z in self.zones.values()),
            "containment_percentage": 100 * (1 - blast_radius / total_rotations)
        }
```

---

## Static Stability

### Pre-Computed Fallback Schedules

**From power grids:** Have backup plans ready before failure

```python
class StaticFallbackSchedules:
    """
    Maintain library of pre-computed backup schedules.

    Scenarios:
    - Pandemic (multiple absences)
    - Deployment surge
    - Residency program size reduction
    """

    fallbacks = {
        "pandemic_20_percent_out": {
            "description": "20% of personnel unavailable",
            "schedule": "precomputed_pandemic_schedule.json",
            "coverage_rate": 85.0,
            "acgme_compliant": True,
            "activation_criteria": ">=5 people absent",
            "last_updated": "2025-12-01"
        },
        "deployment_surge": {
            "description": "Multiple military deployments",
            "schedule": "precomputed_deployment_schedule.json",
            "coverage_rate": 80.0,
            "acgme_compliant": True,
            "activation_criteria": ">=3 faculty deployed",
            "last_updated": "2025-12-01"
        }
    }

    def activate_fallback(self, scenario):
        """
        Load pre-computed fallback schedule.

        Advantage: Instant recovery (no solver runtime).
        Disadvantage: May not be optimal for current situation.
        """
        fallback = self.fallbacks[scenario]

        # Verify fallback is still valid
        if not self.verify_fallback(fallback):
            return {
                "status": "failed",
                "reason": "Fallback schedule no longer valid (personnel changes)",
                "action": "Generate new fallback or solve in real-time"
            }

        # Load and activate
        return {
            "status": "activated",
            "schedule": load_schedule(fallback["schedule"]),
            "coverage_rate": fallback["coverage_rate"],
            "recovery_time": "immediate"
        }
```

---

## Sacrifice Hierarchy

### Prioritized Load Shedding

**From emergency medicine:** Triage when resources insufficient

```python
class SacrificeHierarchy:
    """
    When capacity is insufficient, defer lowest priority items first.

    Priority levels (highest to lowest):
    1. ACGME compliance (never sacrifice)
    2. Patient care rotations (critical)
    3. Teaching rotations (important)
    4. Research time (deferrable)
    5. Elective rotations (nice to have)
    """

    priority_levels = [
        {
            "level": 1,
            "name": "ACGME Compliance",
            "rotations": [],  # Not a rotation, a constraint
            "sacrificable": False
        },
        {
            "level": 2,
            "name": "Critical Patient Care",
            "rotations": ["inpatient", "ER"],
            "min_coverage": 3,
            "sacrificable": False
        },
        {
            "level": 3,
            "name": "Outpatient Clinics",
            "rotations": ["peds_clinic", "adult_clinic"],
            "min_coverage": 2,
            "sacrificable": "partial"  # Can reduce but not eliminate
        },
        {
            "level": 4,
            "name": "Teaching",
            "rotations": ["conference", "simulation"],
            "min_coverage": 1,
            "sacrificable": True
        },
        {
            "level": 5,
            "name": "Research/Elective",
            "rotations": ["research", "elective"],
            "min_coverage": 0,
            "sacrificable": True
        }
    ]

    def apply_sacrifice(self, capacity_deficit):
        """
        Shed load starting from lowest priority.

        Example:
        - Need to reduce 5 assignments
        - Defer 2 research, 2 elective, 1 teaching
        - Maintain all patient care
        """
        sacrificed = []

        for level in reversed(self.priority_levels):
            if capacity_deficit <= 0:
                break

            if level["sacrificable"]:
                for rotation in level["rotations"]:
                    assignments = schedule.get_assignments(rotation)
                    to_defer = min(capacity_deficit, len(assignments) - level["min_coverage"])

                    if to_defer > 0:
                        sacrificed.extend(assignments[-to_defer:])
                        capacity_deficit -= to_defer

        return {
            "sacrificed_assignments": sacrificed,
            "remaining_deficit": capacity_deficit,
            "critical_rotations_maintained": True
        }
```

---

## Monitoring and Detection

### Early Warning Indicators

```python
class ResilienceMonitoring:
    """
    Continuous monitoring for resilience degradation.
    """

    def check_early_warnings(self, schedule):
        warnings = []

        # Utilization approaching threshold
        for person in people:
            if 0.75 < person.utilization < 0.80:
                warnings.append({
                    "type": "utilization_warning",
                    "person": person,
                    "current": person.utilization,
                    "threshold": 0.80,
                    "margin": 0.80 - person.utilization,
                    "trend": "approaching"
                })

        # N-1 compliance degrading
        n1_result = check_n1_compliance(schedule)
        if len(n1_result["failures"]) > 0:
            for failure in n1_result["failures"]:
                if failure["impact"] == "moderate":  # Not critical yet
                    warnings.append({
                        "type": "n1_warning",
                        "person": failure["person"],
                        "status": "degraded",
                        "action": "Add backup coverage"
                    })

        # Coverage trending down
        coverage_trend = calculate_coverage_trend(schedule, days=7)
        if coverage_trend < -2.0:  # Declining by >2% per week
            warnings.append({
                "type": "coverage_trend",
                "current": schedule.coverage_rate,
                "trend": coverage_trend,
                "projection": "Will fall below 90% in 2 weeks",
                "action": "Review absence patterns"
            })

        return warnings
```

---

## Quick Reference

### Resilience Design Checklist

When designing a feature:

- [ ] What can fail? (FMEA)
- [ ] What is the impact of each failure? (Severity × Likelihood)
- [ ] Is there redundancy? (N-1, N-2)
- [ ] What is the recovery time? (RTO)
- [ ] Which defense layer does it affect? (GREEN → BLACK)
- [ ] Are there feedback loops? (Negative = good, Positive = bad)
- [ ] Is the blast radius contained? (Zone isolation)
- [ ] Is there a static fallback? (Pre-computed backup)
- [ ] What gets sacrificed first? (Priority hierarchy)
- [ ] How do we detect degradation? (Monitoring)

---

## Related Documentation

- `.claude/Hooks/post-resilience-test.md` - Capture resilience test results
- `docs/architecture/cross-disciplinary-resilience.md` - Framework concepts
- `backend/app/resilience/` - Resilience implementation
- `.claude/skills/production-incident-responder/SKILL.md` - Incident response
