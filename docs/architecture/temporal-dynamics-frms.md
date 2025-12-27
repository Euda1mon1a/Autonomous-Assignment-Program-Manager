# Temporal Dynamics: Fatigue Risk Management System (FRMS)

> **The Chronobiology Lens for Medical Residency Scheduling**

## Overview

The Fatigue Risk Management System (FRMS) brings aviation safety science to medical residency scheduling. This document describes how temporal dynamics—circadian rhythms, sleep homeostasis, and fatigue accumulation—constrain and optimize scheduling decisions.

## The Temporal Constraint Challenge

Medical residency scheduling has always had a temporal dimension (duty hours, blocks, rotations), but traditional approaches treat time as a simple counter. FRMS adds **chronobiology awareness**—understanding that human performance varies predictably with:

1. **Time of day** (circadian rhythm)
2. **Time since sleep** (sleep homeostasis)
3. **Accumulated sleep debt** (cumulative fatigue)
4. **Shift pattern history** (workload recovery)

## Theoretical Foundations

### The Three-Process Model

FRMS adapts the Three-Process Model from aviation fatigue science:

```
Alertness = f(Process_S, Process_C, Process_W)

Where:
- Process_S (Sleep Homeostasis): Sleep pressure builds during waking
- Process_C (Circadian): 24-hour biological clock
- Process_W (Sleep Inertia): Post-wake grogginess
```

**Aviation Origin**: FAA Advisory Circular AC 120-103A, ICAO Annex 6

### Samn-Perelli Fatigue Scale

A 7-level subjective fatigue scale developed for USAF aircrew (1982):

| Level | Description | Clinical Safety |
|-------|-------------|-----------------|
| 1 | Fully alert, wide awake | Safe for all duties |
| 2 | Very lively, responsive | Safe for all duties |
| 3 | Okay, somewhat fresh | Safe for all duties |
| 4 | A little tired | Safe for most duties |
| 5 | Moderately tired | Restrict procedures/ICU |
| 6 | Extremely tired | Advisory duties only |
| 7 | Completely exhausted | No clinical duties |

**Duty Thresholds** (adapted for medical residency):
- **Critical Care/ICU**: Maximum SP-4
- **Procedures**: Maximum SP-3
- **Inpatient Wards**: Maximum SP-5
- **Outpatient Clinic**: Maximum SP-5
- **Education/Conference**: Maximum SP-6

### Circadian Rhythm Phases

The 24-hour biological clock creates predictable performance windows:

```
        Alertness
           ↑
      1.0  ┌─────────────────────────────────────────┐
           │           ╭───╮                         │
           │          ╱     ╲       ╭──╮             │
      0.9  │         ╱       ╲     ╱    ╲            │
           │        ╱         ╲   ╱      ╲           │
      0.8  │       ╱           ╲ ╱        ╲          │
           │      ╱             ╳          ╲         │
      0.7  │     ╱                          ╲        │
           │    ╱                            ╲       │
      0.6  │   ╱        NADIR                 ╲      │
           │──╱──────────────────────────────────────│
           0  2  4  6  8  10 12 14 16 18 20 22 24
                         Hour of Day →
```

| Phase | Time Range | Multiplier | Scheduling Impact |
|-------|-----------|------------|-------------------|
| Nadir | 02:00-06:00 | 0.60 | Avoid high-risk procedures |
| Early Morning | 06:00-09:00 | 0.85 | Good for routine tasks |
| Morning Peak | 09:00-12:00 | 1.00 | Optimal for complex work |
| Post-Lunch | 12:00-15:00 | 0.90 | Schedule lighter duties |
| Afternoon | 15:00-18:00 | 0.95 | Good for sustained attention |
| Evening | 18:00-21:00 | 0.90 | Routine duties, handoffs |
| Night | 21:00-02:00 | 0.75 | Enhanced monitoring |

### Sleep Debt Accumulation

Sleep debt is the cumulative deficit between sleep need and actual sleep:

```python
Daily_Debt = Baseline_Need - Effective_Sleep
Cumulative_Debt = Σ(Daily_Debt) over time

Where:
  Baseline_Need ≈ 7.5 hours (individual variation: 6-9 hours)
  Effective_Sleep = Actual_Duration × Quality_Factor × Circadian_Alignment
```

**Recovery Ratio**: Approximately 1.5 hours of extra sleep needed per hour of accumulated debt.

**Cognitive Impairment Equivalence**:
| Sleep Debt | Approx. BAC Equivalent |
|------------|------------------------|
| 5 hours | 0.025% |
| 10 hours | 0.05% |
| 17-19 hours awake | 0.05% |
| 20 hours | 0.10% |
| 24 hours awake | 0.10% |

## FRMS Architecture

### Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     FRMS Service Layer                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Fatigue      │ │ Alertness    │ │ Hazard               │ │
│  │ Profiles     │ │ Predictions  │ │ Detection            │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Core Models                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Samn-Perelli │ │ Sleep Debt   │ │ Alertness            │ │
│  │ Scale        │ │ Model        │ │ Engine               │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Temporal Constraints                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Circadian Phases → Sleep Homeostasis → Hazard Levels│   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                     Integration Points                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐ │
│  │ Scheduling   │ │ ACGME        │ │ Resilience           │ │
│  │ Engine       │ │ Validator    │ │ Framework            │ │
│  └──────────────┘ └──────────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Input: Shift patterns, sleep history, work hours
                    ↓
2. Calculate: Hours awake, circadian phase, sleep debt
                    ↓
3. Predict: Alertness score using Three-Process Model
                    ↓
4. Assess: Hazard level (GREEN → BLACK)
                    ↓
5. Output: Safety status, mitigations, schedule recommendations
```

## Hazard Threshold System

Adapted from aviation FRMS with medical-specific thresholds:

### Level Definitions

| Level | Alertness | Sleep Debt | Hours Awake | Response |
|-------|-----------|------------|-------------|----------|
| GREEN | ≥0.70 | <5h | <14h | Normal operations |
| YELLOW | ≥0.55 | <10h | <18h | Enhanced monitoring |
| ORANGE | ≥0.45 | <15h | <22h | Schedule review |
| RED | ≥0.35 | <20h | <26h | Schedule modification |
| BLACK | <0.35 | ≥20h | ≥26h | Immediate intervention |

### Mitigation Escalation

```
GREEN  → No action required
         ↓
YELLOW → [Monitoring]
         ↓
ORANGE → [Monitoring] + [Buddy System] + [Duty Restriction]
         ↓
RED    → [Duty Restriction] + [Shift Swap] + [Schedule Modification]
         ↓
BLACK  → [Mandatory Rest] + [Immediate Relief]
```

## ACGME Integration

FRMS extends ACGME compliance by adding **fatigue-based validation**:

### Traditional ACGME Rules
- 80 hours/week (averaged over 4 weeks)
- 24-hour maximum shift (+4 hours for handoff)
- 1 day off per 7 days

### FRMS Enhancement
FRMS proves that fatigue risks precede ACGME violations. By monitoring:
- Alertness decline before hour limits
- Sleep debt accumulation patterns
- Circadian disruption from night shifts

We can **prevent** ACGME violations rather than just **detect** them.

```
Traditional: Did you exceed 80 hours? → Violation
FRMS:        Is fatigue building?    → Early warning → Intervention
```

## Scheduling Constraints

### Hard Constraints (Must Satisfy)

1. **Circadian Nadir Avoidance**
   - Do not schedule high-risk procedures during 02:00-06:00
   - Applies to: procedures, critical care

2. **Maximum Consecutive Nights**
   - Maximum 4 consecutive night shifts
   - Mandatory recovery period after 4th night

3. **Post-Call Restriction**
   - No new duties after 24-hour call until rest period
   - Minimum 8 hours off before next shift

### Soft Constraints (Optimization Goals)

1. **Circadian Alignment** (weight: 0.3)
   - Prefer shifts aligned with natural circadian rhythm
   - Minimize circadian disruption

2. **Sleep Debt Prevention** (weight: 0.4)
   - Avoid schedules that accumulate sleep debt
   - Ensure adequate recovery between duty periods

3. **Recovery Opportunity** (weight: 0.3)
   - Sufficient off-time for sleep debt recovery
   - Strategic placement of days off

## API Endpoints

### Real-Time Fatigue Scoring
```
POST /api/v1/fatigue-risk/score
{
  "hours_awake": 14.0,
  "hours_worked_24h": 10.0,
  "consecutive_night_shifts": 2,
  "time_of_day_hour": 4,
  "prior_sleep_hours": 6.0
}
→ Returns: SP level, alertness score, recommendations
```

### Resident Fatigue Profile
```
GET /api/v1/fatigue-risk/resident/{id}/profile
→ Returns: Complete fatigue state, hazard level, ACGME status
```

### Schedule Fatigue Assessment
```
POST /api/v1/fatigue-risk/resident/{id}/schedule-assessment
{
  "proposed_shifts": [...]
}
→ Returns: Trajectory predictions, high-risk windows, recommendations
```

### Temporal Constraints Export
```
GET /api/v1/fatigue-risk/temporal-constraints
→ Returns: JSON specification for holographic hub integration
```

## Holographic Hub Integration

The FRMS exports temporal constraint data as JSON for visualization:

```json
{
  "version": "1.0",
  "framework": "Aviation FRMS adapted for Medical Residency",
  "circadian_rhythm": {
    "phases": [...],
    "alertness_curve": [...]
  },
  "sleep_homeostasis": {
    "baseline_need": 7.5,
    "recovery_ratio": 1.5,
    "debt_severity_thresholds": {...}
  },
  "hazard_thresholds": {
    "levels": [...]
  },
  "scheduling_constraints": {
    "hard_constraints": [...],
    "soft_constraints": [...]
  }
}
```

## Validation Evidence

### Tests Proving FRMS Prevents ACGME Violations

1. **test_fatigue_predicts_acgme_risk**: High fatigue correlates with ACGME risk before limits reached
2. **test_frms_catches_violations_early**: FRMS flags concerning patterns before thresholds
3. **test_circadian_constraint_validates_acgme**: Circadian constraints complement hour rules

### Metrics for Evaluation

- **Early Warning Rate**: % of near-violations caught by FRMS before occurrence
- **Intervention Effectiveness**: Alertness improvement after mitigation
- **Schedule Optimization**: Reduction in high-risk windows after FRMS integration

## References

1. FAA Advisory Circular AC 120-103A: Fatigue Risk Management Systems for Aviation Safety
2. ICAO Doc 9966: Manual for the Oversight of Fatigue Management Approaches
3. ACGME Common Program Requirements: Duty Hours
4. Samn, S.W. & Perelli, L.P. (1982). Estimating aircrew fatigue. USAF SAM Report No. 82-21
5. Borbély, A.A. (1982). A two process model of sleep regulation
6. Åkerstedt, T. & Folkard, S. (1997). The three-process model of alertness
7. Van Dongen, H.P. et al. (2003). The cumulative cost of additional wakefulness

## Summary

The FRMS module transforms scheduling from a rule-following exercise into a **safety management system**. By understanding temporal dynamics—circadian rhythms, sleep debt, and fatigue accumulation—we can:

1. **Predict** fatigue before it becomes dangerous
2. **Prevent** ACGME violations rather than just detect them
3. **Optimize** schedules for both compliance and human performance
4. **Protect** residents and patients through proactive intervention

This is the **temporal dynamics lens**: seeing scheduling not just as who-does-what-when, but as an optimization problem constrained by the biological realities of human chronobiology.
