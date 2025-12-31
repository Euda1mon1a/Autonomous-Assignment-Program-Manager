# Military Medical Resilience Calibration

**Status:** Comprehensive Implementation Guide
**Date:** 2025-12-31
**Purpose:** Apply military medical context to resilience framework (burnout epidemiology, defense levels, contingency)
**Audience:** Military Medical Residency Program Directors, Chief Medical Officers, Human Resources

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Military Medical Context](#military-medical-context)
3. [TDY/Deployment Fatigue Weighting](#tdydeployment-fatigue-weighting)
4. [Post-Deployment Recovery Periods](#post-deployment-recovery-periods)
5. [Rank/Hierarchy Stress Factors](#rankhierarchy-stress-factors)
6. [Military-Specific Rt Calculation Adjustments](#military-specific-rt-calculation-adjustments)
7. [Implementation Procedures](#implementation-procedures)
8. [Monitoring Dashboard](#monitoring-dashboard)
9. [Case Studies](#case-studies)

---

## Executive Summary

The residency scheduler's resilience framework operates in a unique military medical context where:

- **TDY (Temporary Duty) assignments** create variable, unpredictable workload spikes
- **Deployment cycles** create long periods of extreme stress followed by integration challenges
- **Rank-based hierarchy** affects both workload and social transmission of burnout
- **PERSEC/OPSEC constraints** limit external staffing augmentation (cannot easily hire civilian replacements)
- **Geographically distributed operations** create isolation and limit peer support networks

**Key Adjustment:** Standard civilian resilience metrics must be weighted 20-40% heavier for military medical programs due to these unique stressors.

---

## Military Medical Context

### Operational Environment Characteristics

#### 1. **TDY/Temporary Duty Assignments**

**Definition:** Unplanned temporary duty at different location (field exercise, humanitarian mission, support operation).

**Characteristics:**
- Duration: 2 weeks to 6 months (unpredictable)
- Frequency: 0-4 TDYs per year depending on rank/specialty
- Composition: Mix of clinical (patient care) and non-clinical (logistics, training) duties
- Integration: Residents return to home unit with scheduling disruption

**Burnout Impact:**
- Creates 2-3x normal workload during TDY period
- Breaks sleep/recovery routines
- Separates from peer support networks
- Reintegration requires 1-2 weeks schedule adjustment

#### 2. **Deployment Cycles**

**Definition:** Extended operational deployment (months to years at forward location).

**Cycle Phases:**

```
Pre-Deployment (Month -3 to 0):
├─ Heavy workload (preparing to depart)
├─ Family stress (separation preparations)
└─ Sleep disruption (pre-deployment anxiety)

Deployment (Month 0 to 6-24):
├─ Extreme workload (frontline operations)
├─ Limited recovery (few days off monthly)
├─ Isolation (limited peer support)
├─ Ethical/moral stress (combat/casualty exposure)
└─ Sleep disruption (operational requirements)

Post-Deployment (Month +1 to +6):
├─ Reintegration challenges
├─ Sleep problems (PTSD-related)
├─ Relationship rebuilding
├─ Schedule restructuring at home unit
└─ Psychological readjustment
```

**Burnout Vulnerability:**
- Pre-deployment: Allostatic load +15-20 points
- During deployment: Allostatic load +30-50 points
- Post-deployment: Allostatic load +10-20 points for 3-6 months

#### 3. **Rank-Based Hierarchy Impact**

**Hierarchy Levels:**
- **Junior Officers (O-1 to O-2)**: Residents, early attendings
- **Senior Officers (O-3 to O-4)**: Chiefs, program directors
- **Senior Leadership (O-5+)**: Hospital commanders, division heads

**Stress Distribution by Rank:**

```
Workload Allocation:
- O-1/O-2 (Junior): Direct clinical care (60%), admin (20%), command (20%)
- O-3/O-4 (Senior): Clinical (40%), admin (35%), command (25%)
- O-5+ (Leadership): Clinical (20%), admin (30%), command (50%)

Social Transmission Risk (Burnout Contagion):
- Junior → Peer: 0.08 transmission probability per contact
- Junior → Senior: 0.02 transmission probability (hierarchy barrier)
- Senior → Junior: 0.15 transmission probability (authority amplification)
- Senior → Peer: 0.12 transmission probability (role modeling effect)
```

**Key Implication:** Senior officers (O-3+) are "super-spreaders" due to high authority and visibility. One burned-out chief affects 15-20% of team within 4 weeks.

#### 4. **OPSEC/PERSEC Constraints**

**Security Restrictions on Staffing:**
- Cannot hire civilian contractors without security clearance
- Civilian locums may not have TS/SCI clearance
- Cannot cross-deploy from incompatible commands easily
- Geographic isolation limits temporary staffing options

**Practical Impact:**
- When faculty absent, cannot "just hire someone quickly"
- Remaining staff must absorb workload internally
- High utilization (>85%) is practically unavoidable
- N-1 vulnerabilities more common in military than civilian settings

### Operational Tempo Categories

**Category A (Low Tempo):** Peacetime training
- TDY frequency: <1 per year
- Deployment rotations: Minimal
- Workload: Normal (60-70 hours/week)

**Category B (Moderate Tempo):** Elevated training/operations
- TDY frequency: 2-3 per year
- Deployment rotations: 6-12 month cycles
- Workload: Elevated (70-80 hours/week)

**Category C (High Tempo):** Active operations
- TDY frequency: 3-4 per year
- Deployment rotations: Continuous (always some deployed)
- Workload: Critical (80-90+ hours/week)

---

## TDY/Deployment Fatigue Weighting

### Allostatic Load Adjustment Algorithm

**Standard Civilian Model:**
```
allostatic_load = base_load + schedule_overwork + psychosocial_stress
                = 0.3*work_hours + 0.4*schedule_variance + 0.3*psychosocial
```

**Military Medical Model (Weighting Adjustment):**
```
allostatic_load_military = (
    0.35*work_hours +                    # Base workload (5% increase)
    0.40*schedule_variance +              # Schedule unpredictability
    0.25*psychosocial_stress +            # Reduced slightly (amplified by TDY)
    0.10*tdy_fatigue_factor +             # NEW: TDY-specific component
    0.05*deployment_reintegration         # NEW: Post-deployment stress
)

Where:
  tdy_fatigue_factor = (
      0.50 * active_tdy_indicator +       # Currently on TDY (0 or 1)
      0.30 * tdy_frequency_last_6mo +     # How many TDYs in past 6 months
      0.20 * avg_tdy_duration             # Average length of TDYs (normalized 0-1)
  )

  deployment_reintegration = (
      1.0 if deployed_recently (0-3 months ago) else 0.5 if 3-6 months ago else 0
  ) * deployment_duration_months / 12
```

**Practical Calculation Example:**

```
Resident A (Peacetime):
  work_hours = 65h/week → 0.65 normalized
  schedule_variance = 0.2 (low)
  psychosocial = 0.4 (normal)
  tdy_fatigue = 0 (not on TDY)
  deployment_reint = 0 (not post-deploy)

  load = 0.35*0.65 + 0.40*0.2 + 0.25*0.4 + 0.10*0 + 0.05*0
       = 0.228 + 0.08 + 0.1 + 0 + 0
       = 0.408 → 41 points (NORMAL)

Resident B (Active TDY):
  work_hours = 80h/week → 0.8 normalized
  schedule_variance = 0.8 (high - unpredictable TDY location)
  psychosocial = 0.6 (elevated - away from family)
  tdy_fatigue = 1.0 (currently on TDY)
  deployment_reint = 0 (not post-deploy)

  load = 0.35*0.8 + 0.40*0.8 + 0.25*0.6 + 0.10*1.0 + 0.05*0
       = 0.28 + 0.32 + 0.15 + 0.10 + 0
       = 0.85 → 85 points (CRITICAL BURNOUT RISK)

Resident C (Post-Deployment, 1 Month):
  work_hours = 70h/week → 0.7 normalized
  schedule_variance = 0.4 (moderate - reintegrating)
  psychosocial = 0.7 (elevated - PTSD, relationship issues)
  tdy_fatigue = 0 (not on TDY)
  deployment_reint = 1.0 * 12/12 = 1.0 (12-month deployment, just returned)

  load = 0.35*0.7 + 0.40*0.4 + 0.25*0.7 + 0.10*0 + 0.05*1.0
       = 0.245 + 0.16 + 0.175 + 0 + 0.05
       = 0.630 → 63 points (HIGH BURNOUT RISK)
```

### TDY Fatigue Factor Breakdown

| Condition | Factor Value | Rationale |
|-----------|------------|-----------|
| Not on TDY, no TDYs in 6mo | 0 | Baseline, no TDY stress |
| 1-2 TDYs in past 6 months | 0.25 | Occasional disruption |
| 3-4 TDYs in past 6 months | 0.50 | Frequent disruption |
| Currently on TDY (week 1-2) | 0.75 | High acute stress |
| Currently on TDY (week 3+) | 1.0 | Maximum TDY fatigue |
| Between TDYs (2-week reintegration) | 0.60 | Lingering fatigue |

### Deployment Reintegration Weighting

**Timeline Post-Deployment:**

```
Weeks Post-Return    Reintegration Factor    Rationale
────────────────────────────────────────────────────────
0-4 (Month 1)        1.0 × (deploy_months/12) [MAXIMUM]
5-8 (Month 2)        0.8 × (deploy_months/12)
9-12 (Month 3)       0.6 × (deploy_months/12)
13-16 (Month 4)      0.4 × (deploy_months/12)
17-24 (Month 5-6)    0.2 × (deploy_months/12)
25+ (Month 7+)       0 (full reintegration)
```

**Deployment Duration Impact:**

```
Deployment Length    Reintegration Duration    Peak Load Adjustment
─────────────────────────────────────────────────────────────────
3-6 months          1-2 months                 +15-20 points
6-12 months         2-3 months                 +20-30 points
12-18 months        3-4 months                 +25-35 points
18+ months          4-6 months                 +30-40 points
```

---

## Post-Deployment Recovery Periods

### Mandatory Recovery Schedule

**U.S. Military Guidance (adopted):**

For every month of deployment, plan minimum recovery period:

```
Deployment Length    Minimum Recovery Period    Recommended
──────────────────────────────────────────────────────────
3 months            1 month non-TDY            2 months recommended
6 months            2 months non-TDY            3 months recommended
9 months            3 months non-TDY            4 months recommended
12+ months          4 months non-TDY            6 months recommended
```

### Recovery Schedule Implementation

**Phase 1: Immediate Return (Week 1-2)**
- **Assignment:** Light clinic duty only (no call, no procedures)
- **Hours:** 40-45 hours/week
- **Support:** Assign senior mentor for daily check-ins
- **Restrictions:** No on-call, no high-stress rotations
- **Monitoring:** Daily brief psychosocial check-in

**Phase 2: Gradual Reintegration (Week 3-6)**
- **Assignment:** Clinic + limited call (no weekends)
- **Hours:** 45-55 hours/week
- **Support:** Weekly psychosocial check-in
- **Restrictions:** Call capped at 1-2 per month
- **Monitoring:** Weekly resilience metrics

**Phase 3: Standard Operations (Week 7-12, Month 2-3)**
- **Assignment:** Normal schedule resumption
- **Hours:** 60-70 hours/week (gradually increase)
- **Support:** Monthly check-ins
- **Restrictions:** None (full duty)
- **Monitoring:** Bi-weekly resilience metrics

### Psychosocial Recovery Support

**Mandatory (All returning deployed personnel):**
1. **Post-Deployment Brief** (Day 1-3)
   - Confidential decompression session with chaplain or mental health officer
   - No record kept in personnel file
   - Structured to identify acute mental health needs

2. **Sleep Hygiene Program** (Week 1-4)
   - Sleep coach assignment
   - Melatonin/sleep aid authorization if needed
   - Sleep tracking with wearable device
   - Goal: Restore normal sleep within 2-3 weeks

3. **Relationship Reconnection** (Week 1-8)
   - Family counseling offered (up to 6 sessions)
   - Spouse/partner education on post-deployment adjustment
   - Child reintegration support if applicable

4. **Mental Health Screening** (Month 1, Month 3, Month 6)
   - Formal PTSD/depression screening
   - Confidential (not in medical record)
   - Early intervention if needed

**Optional (As indicated):**
- Combat trauma counseling
- Moral injury support
- Substance use assessment
- Sleep disorder treatment

### Return-to-Duty Clearance

**Medical Clearance Required Before Normal Duties:**

Resident must be cleared by:
1. Occupational health physician (physical readiness)
2. Mental health officer (psychological readiness)
3. Program director (operational readiness)

**Clearance Withholding Criteria:**
- Active PTSD with hypervigilance
- Sleep deprivation (>2 weeks of inadequate sleep)
- Active substance abuse/misuse
- Suicidal ideation or self-harm
- Severe marital/family crisis

**Graduated Return-to-Duty Protocol:**

```
Medical Clearance → Occupational Health OK?
    ├─ YES → Mental Health Eval
    │         ├─ OK → Program Director Review
    │         │       ├─ OK → CLEARED (Phase 1 assignment)
    │         │       └─ NO → Require specific accommodations
    │         └─ CONCERN → Extended recovery period required
    └─ NO → Physical therapy/conditioning → Retry
```

---

## Rank/Hierarchy Stress Factors

### Rank-Based Workload Distribution

**Standard Allocation Model:**

```
Rank        Position          Clinical    Admin    Command    Total Hours
─────────────────────────────────────────────────────────────────────
O-1         Junior Resident   70%         15%      15%        65-75h
O-2         Senior Resident   60%         25%      15%        70-80h
O-3         Chief Resident    50%         30%      20%        75-85h
O-4         Department Attending 40%      35%      25%        75-85h
O-5+        Division Chief    20%         35%      45%        75-85h
```

### Rank-Based Burnout Contagion Model

**Transmission Matrix** (probability of transmitting burnout per contact):

```
                Transmits To:
From Rank       O-1/O-2      O-3      O-4/O-5
─────────────────────────────────────────────
O-1/O-2 (Junior) 0.10         0.03     0.01
O-3 (Chief)      0.20         0.12     0.08
O-4 (Attending)  0.15         0.10     0.10
O-5+ (Leader)    0.18         0.15     0.12
```

**Interpretation:**
- **Downward transmission** (senior → junior): High (0.15-0.20)
  - Authority amplification effect
  - Juniors perceive senior stress as organizational signal
  - Modeling of burnout-coping strategies

- **Lateral transmission** (peer → peer): Medium (0.10-0.12)
  - Normal social contagion
  - Shared commiserating

- **Upward transmission** (junior → senior): Low (0.01-0.08)
  - Senior buffer against contagion
  - Power difference limits empathy resonance

### Hierarchy-Based Role Stress

**Command Responsibilities by Rank:**

| Rank | Responsibility | Stress Factor |
|------|----------------|---------------|
| O-1 | None (trainee) | 0.1x |
| O-2 | Mentor junior residents | 0.4x |
| O-3 | Chief resident (direct supervision) | 0.8x |
| O-4 | Department clinical leadership | 1.2x |
| O-5+ | Command authority (strategic) | 1.5x |

**Combined Load Calculation:**

```
total_load[rank] = base_clinical_load + rank_admin_burden + command_stress

Example:
  O-1 Total: 65h base + 10h admin + (65 × 0.1) = 65 + 10 + 6.5 = 81.5h
  O-3 Total: 50h base + 30h admin + (50 × 0.8) = 50 + 30 + 40 = 120h [!]
  O-5 Total: 20h base + 35h admin + (20 × 1.5) = 20 + 35 + 30 = 85h
```

**Key Finding:** O-3 chiefs often work 120+ hours/week due to command overhead. This creates severe burnout risk and high super-spreader status.

### Hierarchy-Based Support Structures

**Mentoring Networks (Resilience Building):**

- **O-1 ← O-2 mentoring**: Established peer (same rank +1 year)
- **O-2 ← O-3 mentoring**: Chief resident supervision
- **O-3 ← O-4 mentoring**: Department attending guidance
- **O-4 ← O-5 mentoring**: Division chief leadership

**Mentoring Effectiveness on Burnout Reduction:**
- Active mentoring: Rt reduced 30-40%
- No mentoring: Rt elevated 10-20%
- Mentor burned out: Transmission amplified 50%

---

## Military-Specific Rt Calculation Adjustments

### Modified Rt Formula for Military Context

**Standard Civilian Rt:**
```
Rt = β × S/N × contacts × duration
   = transmission_rate × susceptible_fraction × network_intensity × infection_window
```

**Military Adjusted Rt:**
```
Rt_military = β × S/N × contacts × duration × military_multiplier

Where:
military_multiplier = (
    0.4 * TDY_contagion_amplifier +
    0.3 * deployment_cycle_amplifier +
    0.2 * rank_hierarchy_amplifier +
    0.1 * isolation_amplifier
)
```

### Military Multiplier Components

#### 1. TDY Contagion Amplifier

```
TDY Contagion = (
    0.6 * tdy_return_clustering +        # Multiple returns same week
    0.4 * psychosocial_sharing_intensity  # Return decompression
)

tdy_return_clustering:
  ├─ 1 return per month:  0.3
  ├─ 2-3 returns per month: 0.6
  ├─ 4+ returns per month: 1.0

psychosocial_sharing_intensity:
  ├─ No post-TDY debrief: 0.1
  ├─ Informal discussions: 0.4
  ├─ Structured decompression: 0.6
  └─ Mandatory group debrief: 1.0
```

**Interpretation:** When multiple personnel return from TDY simultaneously AND there's structured debriefing (where stress is discussed), burnout contagion amplifies 1.4-1.8x normal rates.

#### 2. Deployment Cycle Amplifier

```
Deployment_Cycle = (
    0.5 * simultaneous_deployment_fraction +
    0.3 * post_deployment_return_clustering +
    0.2 * pre_deployment_anxiety_elevation
)

simultaneous_deployment_fraction:
  ├─ <10% of program deployed: 0.2
  ├─ 10-30% deployed: 0.5
  ├─ 30-50% deployed: 0.8
  └─ >50% deployed: 1.0

post_deployment_return_clustering:
  ├─ Staggered returns (spread over months): 0.1
  ├─ Groups return (1-2 week windows): 0.4
  ├─ Synchronized returns (all same week): 0.8
  └─ Rapid rotation (new cohort deploys as others return): 1.0

pre_deployment_anxiety_elevation:
  ├─ 3 months pre-deploy: 0.1
  ├─ 1-3 months pre-deploy: 0.3
  ├─ 2-4 weeks pre-deploy: 0.6
  └─ <2 weeks pre-deploy: 1.0
```

**Key Insight:** Synchronized returns amplify contagion dramatically. If 30% of program returns same week, they collectively brief others on deployment stress, amplifying transmission 1.4x for those 2-3 weeks.

#### 3. Rank Hierarchy Amplifier

```
Rank_Hierarchy = (
    0.7 * super_spreader_rank_ratio +
    0.3 * authority_distance_effect
)

super_spreader_rank_ratio:
  ├─ No O-3+ burned out: 0
  ├─ 1 O-3+ burned out: 0.3
  ├─ 2+ O-3+ burned out: 0.8
  ├─ Chief resident burned out: 1.0

authority_distance_effect:
  ├─ Flat hierarchy (minimal rank structure): 0.1
  ├─ Standard military (clear but navigable): 0.4
  ├─ Rigid hierarchy (strict rank-based): 0.7
  └─ Authoritarian structure (power distance 80+): 1.0
```

**Practical Example:**
```
Program A (Flexible Hierarchy):
  - No chiefs/seniors burned out
  - Collaborative culture
  - Rank_Hierarchy = 0.7 * 0 + 0.3 * 0.1 = 0.03
  - Minimal amplification

Program B (Standard Military + 1 Chief Burned Out):
  - Chief resident (O-3) burned out (load 85)
  - Clear rank structure
  - Rank_Hierarchy = 0.7 * 0.3 + 0.3 * 0.4 = 0.21 + 0.12 = 0.33
  - 33% amplification to Rt

Program C (Authoritarian + Chief + Dept Head Burned Out):
  - Chief (O-3) + attending (O-4) both burned out
  - Strict hierarchy
  - Rank_Hierarchy = 0.7 * 0.8 + 0.3 * 0.7 = 0.56 + 0.21 = 0.77
  - 77% amplification to Rt (!!)
```

#### 4. Isolation Amplifier

```
Isolation = (
    0.6 * geographic_isolation_factor +
    0.4 * peer_network_fragmentation
)

geographic_isolation_factor:
  ├─ Urban teaching hospital (connected): 0.1
  ├─ Regional military hospital: 0.3
  ├─ Remote forward location: 0.6
  ├─ Very remote/deployed: 1.0

peer_network_fragmentation:
  ├─ Cohesive team (strong peer bonds): 0.1
  ├─ Some team fragmentation: 0.4
  ├─ High fragmentation (cliques): 0.7
  └─ Isolated individuals (no peer support): 1.0
```

### Complete Example: Military Rt Calculation

**Scenario: Naval Medical Center, 20-person faculty, 1 chief on TDY, post-deployment period**

```
Base Parameters:
  β (transmission rate) = 0.06 (slightly higher than civilian 0.05 due to military culture)
  S (susceptible) = 18 out of 20 = 0.9
  N (total) = 20
  contacts_per_week = 25 (high due to military briefings, tight team)
  infection_window = 4 weeks

  Civilian Rt = 0.06 × 0.9 × 25 × 4 / 20 = 1.08

Military Adjustments:
  TDY_amplifier = 0.6 * 0.6 + 0.4 * 0.4 = 0.36 + 0.16 = 0.52
  Deployment_amplifier = 0.5 * 0.3 + 0.3 * 0.4 + 0.2 * 0.2 = 0.15 + 0.12 + 0.04 = 0.31
  Rank_amplifier = 0.7 * 0.3 + 0.3 * 0.4 = 0.21 + 0.12 = 0.33
  Isolation_amplifier = 0.6 * 0.3 + 0.4 * 0.4 = 0.18 + 0.16 = 0.34

  military_multiplier = 0.4 * 0.52 + 0.3 * 0.31 + 0.2 * 0.33 + 0.1 * 0.34
                       = 0.208 + 0.093 + 0.066 + 0.034
                       = 0.401

Rt_military = 1.08 × (1 + 0.401) = 1.08 × 1.401 = 1.51

Status: RAPID SPREAD (threshold = 1.5)
Recommendation: ORANGE → RED escalation
```

### Quarterly Rt Review Protocol

**Every 3 months, calculate:**
1. **Baseline Rt** (from epidemiological data)
2. **Military Multiplier** (recalculate 4 components)
3. **Adjusted Rt** (baseline × multiplier)
4. **Trend Analysis** (Rt improving or worsening?)
5. **Action Triggers** (escalation/de-escalation points)

---

## Implementation Procedures

### Configuration Setup

**In System Configuration:**

```python
# backend/app/core/config.py (add military adjustments)

MILITARY_MEDICAL_ADJUSTMENTS = {
    "enabled": True,
    "program_type": "military",  # or "civilian"

    "allostatic_load_weights": {
        "work_hours": 0.35,
        "schedule_variance": 0.40,
        "psychosocial": 0.25,
        "tdy_fatigue": 0.10,
        "deployment_reintegration": 0.05,
    },

    "tdy_factors": {
        "not_on_tdy": 0.0,
        "1_2_tdy_6mo": 0.25,
        "3_4_tdy_6mo": 0.50,
        "current_tdy_week_1_2": 0.75,
        "current_tdy_week_3_plus": 1.0,
        "between_tdy_reintegration": 0.60,
    },

    "rt_multiplier_weights": {
        "tdy_contagion": 0.4,
        "deployment_cycle": 0.3,
        "rank_hierarchy": 0.2,
        "isolation": 0.1,
    },

    "mandatory_recovery": {
        "3_months_deployment": 1,   # months
        "6_months_deployment": 2,
        "9_months_deployment": 3,
        "12_plus_deployment": 4,
    },

    "recovery_phases": {
        "phase_1_duration": 14,  # days
        "phase_1_max_hours": 45,
        "phase_2_duration": 28,
        "phase_2_max_hours": 55,
    },
}
```

### Monitoring Implementation

**Weekly Monitoring Job (Celery task):**

```python
@celery_app.task(bind=True)
def calculate_military_adjusted_metrics(self, program_id: str):
    """
    Weekly: Calculate military-adjusted burnout metrics.
    """
    program = get_program(program_id)

    if not program.military_medical_mode:
        return  # Skip if not military

    # 1. Calculate TDY status for each resident
    residents = get_active_residents(program_id)
    for resident in residents:
        tdy_status = calculate_tdy_status(resident)
        deploy_status = calculate_deployment_status(resident)

        # 2. Adjust allostatic load
        adjusted_load = calculate_military_adjusted_load(
            resident,
            tdy_status=tdy_status,
            deploy_status=deploy_status,
            config=MILITARY_MEDICAL_ADJUSTMENTS
        )

        # 3. Store adjusted metrics
        store_military_metrics(resident, adjusted_load)

    # 4. Calculate Rt with military multiplier
    burned_out = {r for r in residents if r.adjusted_load > 60}
    rt_baseline = calculate_rt(burned_out, residents)
    rt_military = apply_military_multiplier(rt_baseline, program)

    # 5. Store and alert
    store_military_rt(program, rt_military)
    if rt_military > 1.5:
        alert_leadership("RAPID BURNOUT SPREAD", rt=rt_military)
```

### Training and Documentation

**For Program Directors:**

1. **Monthly Briefing Template**
   - TDY frequency and reintegration status
   - Military-adjusted burnout Rt
   - Defense level (with military weighting)
   - Rank-based risk assessment
   - Recovery periods for returned personnel

2. **Decision Support Documentation**
   - When to escalate defense level (military thresholds)
   - Mandatory recovery schedule implementation
   - Rank hierarchy risk factors
   - Communication templates for sensitive conversations

3. **Data Privacy**
   - TDY/deployment data is OPSEC sensitive
   - Burnout metrics cannot be exported
   - Dashboard access limited to commander-level
   - No external sharing without approval

---

## Monitoring Dashboard

### Key Military-Specific Metrics

**Panel 1: TDY Impact Analysis**

```
Current TDY Status:
  On TDY Right Now:        3/20 faculty (15%)
  Returning This Week:     2 faculty
  Scheduled Next Month:    4 faculty
  TDY Frequency (6mo):     2.1 average TDYs per person

TDY Burnout Risk:
  High Risk (on TDY):      Load 85 average (+18 vs non-TDY)
  Reintegrating (2wk):     Load 72 average (+10 vs normal)
  Post-Return (2-4wk):     Load 68 average (+5 vs normal)
```

**Panel 2: Deployment Cycle Status**

```
Current Deployment Status:
  Currently Deployed:      6/20 faculty (30%)
  Returning Next Month:    0
  Pre-Deploy (3mo out):    4 faculty (elevated stress)
  Post-Deploy (<3mo):      2 faculty (reintegrating)

Deployment Stress Index:
  Simultaneous % Deployed: 30%
  Return Clustering Risk:  MODERATE (returns staggered)
  Pre-Deploy Anxiety:      16% of program in prep phase

Estimated Reintegration Load (next 30 days):
  None expected
```

**Panel 3: Rank-Based Burnout Contagion**

```
Super-Spreader Status:
  [!!!] Chief Resident (O-3): Load 82 (CRITICAL)
  [!!] Attending (O-4): Load 71 (HIGH)
  [!] Senior Resident (O-2): Load 68 (MODERATE)

Contagion Risk by Rank:
  From Chief → to Junior Residents:  0.20 prob/contact
  From Chief → to Peers:              0.12 prob/contact
  Junior-to-Junior:                   0.10 prob/contact

Recommended Actions:
  URGENT: Chief resident intervention needed
  Address: Command responsibilities reducing
  Support: Peer mentoring intensification
```

**Panel 4: Military-Adjusted Rt**

```
Burnout Reproduction Number (Rt):
  Baseline Civilian Rt:    0.92 (CONTROLLED)
  TDY Amplifier:           ×0.52 (+52%)
  Deployment Amplifier:    ×0.31 (+31%)
  Rank Hierarchy:          ×0.33 (+33%)
  Isolation Amplifier:     ×0.34 (+34%)

  MILITARY RT:             1.38 (APPROACHING THRESHOLD)

Status: YELLOW → ORANGE ESCALATION PREDICTED (within 1-2 weeks)
Recommendation: Activate ORANGE level protocols now
  - Chief resident workload reduction
  - Reintegration support for returning deployed
  - Enhanced monitoring (3x weekly)
```

**Panel 5: Recovery Schedule Compliance**

```
Post-Deployment Recovery Status:

Resident Name    Deploy Len    Days Back    Phase    Status
─────────────────────────────────────────────────────────────
Smith, J         12 months     18 days     Phase 2  ✓ ON TRACK
Jones, M         6 months      42 days     Phase 3  ✓ PROGRESSING
Lee, K           9 months      7 days      Phase 1  ✓ COMPLIANT

Alert Flags:
  [!] Smith, J: Scheduled for call next week (still in Phase 2)
      → Recommend postponing to Phase 3
```

---

## Case Studies

### Case 1: Successful TDY Management

**Scenario:**
- 20-person faculty program
- 4 simultaneous TDY returns (humanitarian mission)
- Chief resident (O-3) remained home to manage schedule

**Timeline:**
```
Week 0 (Pre-Return):
  - Status: CONTROL (FWI 35, Rt 0.75)
  - Chief: Allostatic load 68
  - Prep: Organized mandatory decompression briefing

Week 1-2 (Post-Return):
  - 4 residents returned (load 75-82 each)
  - Structured 2-hour decompression session
  - Limited assignments (45h/week) for returns
  - Status: YELLOW (FWI 42, Rt 1.08 → adjusted to 1.42)
  - Chief: Allostatic load 78 (temporary increase)

Week 3-4 (Reintegration):
  - Returned residents ramping to normal (55-65h/week)
  - Decompression effects wearing off
  - Status: Still YELLOW, but trending down

Week 5-6 (Stabilization):
  - All residents back to normal load
  - Status: CONTROL (FWI 38, Rt 0.82)
```

**Outcome:** Smooth reintegration, no burnout cascade, Rt peaked at 1.42 but didn't cross 1.5 escalation threshold.

**Key Success Factors:**
1. Chief stayed home to manage surge
2. Structured decompression (vs. informal)
3. Mandatory light duty for returnees
4. Regular check-ins during reintegration

---

### Case 2: Post-Deployment Reintegration Failure

**Scenario:**
- 20-person program
- 6 residents returned from 9-month deployment
- Aggressive schedule restart (attempting to "normalize" immediately)
- Chief resident also recently returned (12-month deployment)

**Timeline:**
```
Week 0 (Returns):
  - 6 residents + 1 chief returned same day
  - Status: YELLOW (FWI 48, Rt 0.98)
  - Allostatic loads: 70-85 (elevated by deployment)

Week 1 (Error: Aggressive Ramp-Up):
  - Assigned to normal schedule immediately
  - No structured decompression
  - Chief took full command responsibilities
  - Chief's load jumped to 92 (CRITICAL)
  - Status: ORANGE (FWI 52, Rt 1.32 → 1.83 with military adj)

Week 2-3 (Cascade Begins):
  - Returned residents struggling (70-80h/week)
  - Chief burned out, not managing well
  - One O-2 senior resident calls in sick
  - Second resident departures from program
  - Status: RED (FWI 65, Rt 1.95 → 2.74 with military adj)

Week 4 (Crisis):
  - 3 additional unexpected absences
  - Chief on emergency leave
  - Schedule collapses
  - Status: BLACK (FWI 78, Rt > 3.0)
```

**Outcome:** Catastrophic cascade failure, 2-year recovery needed.

**Key Failure Points:**
1. No mandatory recovery periods implemented
2. Chief returned and immediately took full load
3. No structured decompression (informal only)
4. Aggressive "normalization" ignored psychological recovery needs
5. No military-adjusted Rt monitoring (would have caught escalation)

**Lesson:** Post-deployment reintegration is NOT just about schedule adjustment; psychological recovery is critical infrastructure.

---

## Appendix: Quick Reference

### Stress Factor Checklist

- [ ] **TDY Status**: On TDY? When returning? Frequency in past 6 months?
- [ ] **Deployment Status**: Recently returned? Still deployed? Pre-deployment?
- [ ] **Rank**: O-1/O-2 (junior), O-3 (chief), O-4+ (senior)?
- [ ] **Recovery Phase**: If post-deploy, which phase (1/2/3)?
- [ ] **Hierarchy Impact**: Is this person a super-spreader (O-3+)?
- [ ] **Isolation**: Remote location? Peer support available?

### Escalation Decision Tree (Military Context)

```
Is military-adjusted Rt > 1.5?
  ├─ NO → GREEN/YELLOW (maintain prevention)
  └─ YES → Is chief/senior burned out?
      ├─ YES → RED (rapid escalation likely)
      └─ NO → ORANGE (monitor closely)

Is resident returning from deployment in Phase 1-2?
  ├─ YES (Week 1-8) → Mandatory light duty
  └─ NO → Standard assignment

Is TDY causing current surge?
  ├─ YES → Limited reintegration (45h/week for returnees)
  └─ NO → Standard assignment
```

---

**Document Classification:** MILITARY MEDICAL OPERATIONS
**Approved for:** Program Directors, Chief Medical Officers, Human Resources
**Date Effective:** 2025-12-31
**Next Review:** 2026-03-31

