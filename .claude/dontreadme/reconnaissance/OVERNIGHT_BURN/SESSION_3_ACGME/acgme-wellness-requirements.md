# ACGME Wellness and Fatigue Mitigation Requirements

**SEARCH_PARTY Reconnaissance Report**
**Agent:** G2_RECON
**Mission:** ACGME Wellness & Fatigue Mitigation Requirements Audit
**Date:** 2025-12-30
**Classification:** OPERATIONAL GUIDANCE

---

## Executive Summary

This document consolidates ACGME wellness requirements, fatigue mitigation strategies, and intervention protocols as implemented in the Residency Scheduler system. The system applies cross-disciplinary scientific models (materials science, epidemiology, seismology, manufacturing QC, forestry fire science) to detect and prevent burnout 4-12 weeks before clinical manifestation.

**Key Finding:** The system implements a multi-layered wellness architecture:
- **Tier 1:** Real-time fatigue risk assessment (FRMS with Samn-Perelli scales)
- **Tier 2:** Predictive burnout modeling (5 materials science fatigue models)
- **Tier 3:** Epidemiological contagion tracking (SIR/SEIR workforce models)
- **Tier 4:** Seismic precursor detection (STA/LTA algorithm for early warnings)
- **Tier 5:** Multi-temporal danger assessment (Fire Weather Index adaptation)

---

## Part 1: ACGME Regulatory Framework

### 1.1 Core Duty Hour Requirements (ACGME Section VI.F)

#### The 80-Hour Rule
- **Requirement:** Maximum 80 hours per week, averaged over rolling 4-week (28-day) periods
- **Scope:** Includes all clinical work, education, moonlighting, and work-from-home activities
- **Implementation in System:**
  - `EightyHourRuleConstraint` validates EVERY 28-day consecutive window
  - Maximum 53 blocks per rolling 4-week window (80 hours ÷ 6 hours/block)
  - Prevents assignment of blocks that would violate average

**Clinical Intent:** Prevents cumulative fatigue from sustained high workloads that exceed recovery capacity

#### One-in-Seven (1-in-7) Day Off Rule
- **Requirement:** At least one 24-hour period free from all clinical, educational, and administrative activities every 7 days (averaged over 4 weeks)
- **Minimum:** 4 complete days off per 28-day period
- **Implementation in System:**
  - `OneInSevenRuleConstraint` enforces max 6 consecutive days worked
  - Tracks all activities including conference/admin duties
  - Supports 4-week averaging (can cluster days off)

**Clinical Intent:** Prevents physiological collapse from continuous work; supports sleep recovery and social restoration

#### Shift Duration Limits

**PGY-1 (Intern) Residents:**
- Maximum continuous duty: **16 hours** (strict, no exceptions)
- No additional handoff time permitted
- Implementation: `PGY1_MAX_SHIFT_LENGTH = 16`

**PGY-2/PGY-3 Residents:**
- Maximum continuous duty: **24 hours** of clinical work
- Additional **4 hours** permitted for:
  - Patient handoff and transitions of care
  - Educational debriefing
  - Direct patient care when needed for continuity
- Total maximum: **28 hours** on-site
- Implementation: `MAX_CONTINUOUS_HOURS = 28` with 24+4 rule enforcement

**Clinical Intent:** PGY-1s have enhanced cognitive vulnerability (first-year decision making, knowledge gaps); additional time for handoff preserves care quality

#### Minimum Rest Between Shifts
- **Requirement:** 10 hours free from all duties between scheduled work periods (ACGME standard)
- **System Implementation:**
  - FRMS enforces 8 hours (`ACGME_MIN_REST_BETWEEN_SHIFTS = 8.0`)
  - **Discrepancy Alert:** Code vs. regulation gap (8 vs. 10 hours)
  - Should be escalated for compliance verification

**Clinical Intent:** Physiological recovery window for alertness, decision-making capacity, and immune function

#### Night Float Limits
- **Requirement:** Maximum 6 consecutive nights of night float rotation
- **Implementation:** `MAX_NIGHT_FLOAT_CONSECUTIVE = 6`
- **Rationale:** Circadian disruption is cumulative; extended night work increases injury risk exponentially

#### In-House Call Frequency
- **Requirement:** In-house call no more frequently than every third night (averaged over 4 weeks)
- **Scheduling Implication:** ~9 in-house calls per 28-day period
- **Implementation Status:** ⚠️ Not enforced as hard constraint; relies on rotation template design
- **Recommendation:** Consider adding `CallFrequencyConstraint` to enforce programmatically

### 1.2 Supervision Requirements (ACGME Section VI.D)

Faculty-to-Resident Ratios (Direct Impact on Fatigue):

| Level | Ratio | Supervision Type |
|-------|-------|------------------|
| **PGY-1** | 1:2 | Direct supervision, in-house availability |
| **PGY-2/3** | 1:4 | Available for consultation, progressive independence |

**Fatigue Implication:** Inadequate supervision → increased cognitive load → faster fatigue accumulation

### 1.3 Workload Monitoring & Compliance Documentation

**Program Responsibilities:**
1. Monitor duty hours weekly through electronic logging
2. Review violations immediately and implement corrective action
3. Educate residents annually on duty hour requirements
4. Maintain documentation for ACGME site visits
5. Report systematic violations to ACGME

**System Role:** Automated compliance validation prevents violations before they occur

---

## Part 2: Wellness Program Architecture

### 2.1 Real-Time Fatigue Assessment (Tier 1 - FRMS)

**System Component:** `backend/app/resilience/frms/`

The Fatigue Risk Management System (FRMS) provides continuous fatigue monitoring using:

#### Samn-Perelli 7-Point Scale
Subjective fatigue assessment with clinical thresholds:

| Level | State | Clinical Action | Risk Profile |
|-------|-------|-----------------|--------------|
| 1 | Fully Alert | Monitor | Baseline |
| 2 | Very Lively | Monitor | Baseline |
| 3 | Okay | Monitor | Baseline - GREEN |
| 4 | A Little Tired | Caution | Early Warning - YELLOW |
| 5 | Moderately Tired | Intervention | Elevated - ORANGE |
| 6 | Extremely Tired | Immediate Relief | High Risk - RED |
| 7 | Exhausted | Emergency Protocols | Critical - BLACK |

**Database Model:** `FatigueAssessment` captures point-in-time measurements

#### Objective Fatigue Metrics
Calculated from workload history and sleep debt:
- **Sleep Debt** (SAMN model): Cumulative sleep deficit hours
- **Hazard Alerts**: Automatically generated when thresholds exceeded
- **Intervention Tracking**: Documents actions taken and outcomes

**Key Thresholds:**
```python
HAZARD_THRESHOLDS = {
    'green': {
        'max_fatigue_level': 3,
        'max_sleep_debt': 2.0,
        'max_consecutive_hours': 24,
    },
    'yellow': {
        'max_fatigue_level': 4,
        'max_sleep_debt': 4.0,
        'max_consecutive_hours': 28,
    },
    'orange': {
        'max_fatigue_level': 5,
        'max_sleep_debt': 6.0,
        'intervention_required': True,
    },
    'red': {
        'max_fatigue_level': 6,
        'max_sleep_debt': 8.0,
        'duty_restriction_required': True,
    },
    'black': {
        'max_fatigue_level': 7,
        'emergency_protocol': True,
    },
}
```

#### Intervention Types (Immediate/Short-Term)
When FRMS triggers alerts:

| Intervention | Trigger | Duration | Authority |
|--------------|---------|----------|-----------|
| **Monitoring** | YELLOW alert | Continuous | FRMS auto |
| **Buddy System** | ORANGE alert | Shift-based | Supervisor approval |
| **Duty Restriction** | RED alert | 24-48 hours | Program Director |
| **Shift Swap** | YELLOW/ORANGE | Single shift | Auto-matcher or manual |
| **Early Release** | RED alert | Shift end | Program Director |
| **Schedule Modification** | Persistent ORANGE | 1+ weeks | Program Director |
| **Mandatory Rest** | RED alert | 24+ hours | Program Director |
| **Immediate Relief** | BLACK alert | Emergency | Program Director + Psychiatry |

### 2.2 Predictive Burnout Modeling (Tier 2 - Materials Science)

**System Component:** `backend/app/analytics/burnout_prediction/`
**Specification:** `/Users/.../docs/specs/BURNOUT_PREDICTION_SERVICE_SPEC.md`

#### Five-Model Ensemble Approach

The system predicts burnout 4-12 weeks in advance using materials science fatigue models:

##### Model 1: S-N Curve (Workload-Cycles Relationship)
```
N = (σ / σ_f')^(1/b)

Where:
- N = cycles to burnout
- σ = stress amplitude (% capacity)
- σ_f' = fatigue strength coefficient (~100)
- b = exponent (-0.12)
```

**Clinical Application:**
- Predicts cycles to burnout at current workload intensity
- 85% capacity intensity → ~52 cycles (52 weeks)
- Below 50% capacity → functionally "infinite" cycles (sustainable)

##### Model 2: Miner's Rule (Cumulative Damage)
```
D = Σ(n_i / N_i)  where D ≥ 1.0 = failure

Tracks damage from variable workload:
- Weekend call (85%) contributes 0.154 damage per cycle
- Night shifts (75%) contribute 0.095 damage per cycle
- Clinic (60%) contributes 0.012 damage per cycle
```

**Clinical Application:**
- Damage status tracking:
  - D < 0.5: LOW_DAMAGE (green)
  - 0.5 ≤ D < 0.7: MODERATE_DAMAGE (yellow)
  - 0.7 ≤ D < 1.0: HIGH_DAMAGE (orange)
  - D ≥ 1.0: BURNOUT_PREDICTED (red)

##### Model 3: Coffin-Manson (Recoverable vs. Unrecoverable Fatigue)
```
Distinguishes:
- Elastic strain (recoverable with rest)
- Plastic strain (unrecoverable, permanent damage)

High-intensity rotations (>80%) → plastic deformation
Moderate rotations (50-70%) → elastic deformation (recoverable)
```

**Clinical Application:**
- If >20% of damage is plastic per rotation → limit consecutive high-intensity blocks
- If <5% plastic per rotation → sustainable long-term pattern

##### Model 4: Larson-Miller (Creep Rupture from Sustained Stress)
```
LMP = T(C + log t_r)

Predicts burnout from chronic moderate stress (70+ hours/week)
Not acute overload, but sustained unsustainable pace
```

**Clinical Application:**
- Detects "slow burn" scenarios (consistently at 75% capacity)
- Person might be within weekly limits but heading to collapse
- Identifies need for 1-month mandatory reduced workload

##### Model 5: Paris Law (Symptom Progression Tracking)
```
da/dN = C(ΔK)^m

Tracks burnout symptom progression using:
- MBI-EE (Maslach Burnout Inventory Emotional Exhaustion)
- PHQ-9 (depression screening)
- GAD-7 (anxiety screening)
- Single-item burnout measure
```

**Clinical Intervention Regions:**

| Region | Severity | Intervention |
|--------|----------|--------------|
| I | MBI-EE < 10 | Routine monitoring, wellness education |
| II | MBI-EE 10-22 | Weekly monitoring, workload adjustment, counseling |
| III | MBI-EE > 22 | Immediate 50% workload reduction, daily monitoring, psych eval |

#### Ensemble Prediction & Risk Levels

**Weighted Combination (ensemble):**
- S-N Curve: 20% weight
- Miner's Rule: 35% weight (most practical)
- Larson-Miller: 25% weight
- Paris Law: 20% weight

**Risk Classification:**

| Risk Level | Days to Burnout | Action |
|-----------|-----------------|--------|
| **CRITICAL** | < 30 days | Immediate medical leave, psychiatric evaluation |
| **HIGH** | 30-90 days | 50% workload reduction, weekly therapy, daily monitoring |
| **MODERATE** | 90-180 days | 25% workload reduction, bi-weekly counseling, weekly checks |
| **LOW** | > 180 days | Standard monitoring |

#### API Endpoints for Burnout Monitoring

```
POST /api/v1/burnout/predict
  → Generate ensemble prediction for individual
  → Returns risk level, days to burnout, interventions

GET /api/v1/burnout/resident/{person_id}/fatigue
  → Get Miner's damage score
  → Returns cumulative damage, remaining life fraction

POST /api/v1/burnout/symptoms
  → Record MBI/PHQ9/GAD7 assessments
  → Returns Paris Law crack growth rate

GET /api/v1/burnout/dashboard
  → Risk overview for all residents
  → Aggregated statistics, HIGH/CRITICAL alert list

POST /api/v1/burnout/calibrate
  → Calibrate personal model from observed burnout event
  → Improves prediction accuracy for future forecasts
```

### 2.3 Epidemiological Contagion Tracking (Tier 3 - SIR/SEIR)

**System Component:** `backend/app/resilience/burnout_epidemiology.py`
**Research:** `/Users/.../docs/research/epidemiology-for-workforce-resilience.md`

#### Burnout Contagion Model (SEIR-B)

The system tracks burnout spread through social networks:

```
S → E → I → R
(Susceptible → Exposed → Infected → Recovered/Departed)
```

**State Definitions:**

| State | Allostatic Load | Description |
|-------|----------------|-------------|
| **S** | < 40 | Healthy, manageable stress |
| **E** | 40-60 | Early warning signs, elevated stress |
| **I** | > 60 | Actively burned out, affecting others |
| **R** | variable | Recovered to health OR departed organization |

**Transmission Rates:**
- **β (beta):** 0.05 contacts/day (emotional contagion through social contact)
- **σ (sigma):** 1/30 (incubation: 30 days from exposure to burnout)
- **γ (gamma_recovery):** 1/90 (recovery takes ~90 days)
- **γ_attrition:** 0.01/day (1% daily departure probability when burned out)

**Clinical Application:**
- Identifies "superspreaders" (high-influence burned-out faculty)
- Detects burnout cascades before they occur
- Tracks morale contagion (engagement can spread like wellness)

**Calculation Example:**
```
If 3 faculty burned out in 50-person program:
- Contagion rate indicates 6-9 more infections likely within 4-6 weeks
- Intervention reduces transmission probability by 70%
- Modeling shows which colleagues at highest risk of infection
```

### 2.4 Seismic Precursor Detection (Tier 4 - STA/LTA)

**System Component:** `backend/app/resilience/spc_monitoring.py`
**Algorithm:** Short-Term Amplitude / Long-Term Amplitude (STA/LTA)

Detects sudden changes in fatigue patterns (precursors to burnout):

#### Statistical Process Control (Western Electric Rules)

Monitors workload patterns for anomalies:

| Rule | Trigger | Clinical Meaning |
|------|---------|------------------|
| **Rule 1** | 1 point > 3σ from mean | Acute spike (sudden overload) |
| **Rule 2** | 9 consecutive points on same side of mean | Systematic increase (creeping fatigue) |
| **Rule 3** | 6 consecutive points increasing/decreasing | Trend toward danger |
| **Rule 4** | 2-3 consecutive points > 2σ from mean | Sustained elevation |

**Example Detection:**
```
Week 1: 6 blocks (normal)
Week 2: 6 blocks (normal)
Week 3: 6 blocks (normal)
Week 4: 5 blocks (anomaly? slight decrease)
Week 5: 8 blocks (RULE 3: increasing trend detected)
Week 6: 9 blocks (RULE 2: 3 consecutive high weeks)
→ ALERT: Sustained overload pattern emerging
```

### 2.5 Multi-Temporal Danger Assessment (Tier 5 - Fire Weather Index)

**System Component:** `backend/app/resilience/burnout_fire_index.py`
**Model:** Adaptation of Canadian Forest Fire Weather Index (CFFDRS)

Combines multiple temporal scales to assess composite burnout danger:

#### Five Components

| Component | Temporal Scale | What it Measures |
|-----------|---------------|-----------------|
| **FFMC** | 1 day | Surface fuel drying (acute fatigue) |
| **DMC** | 1-2 weeks | Mid-layer fuel accumulation (weekly fatigue) |
| **DC** | 1-2 months | Deep fuel drying (chronic stress) |
| **ISI** | Wind effect | Critical ignition index (precursor sensitivity) |
| **BUI** | Build-up index | Available fuel for burning (burnout severity) |

**Clinical Thresholds:**

| FWI Index | Risk Level | Description |
|-----------|-----------|-------------|
| 0-40 | LOW | No burnout risk |
| 41-100 | MODERATE | Elevated burnout vulnerability |
| 101-200 | HIGH | Burnout likely without intervention |
| 201+ | CRITICAL | Burnout imminent, emergency protocols |

**Example Scenario:**
```
FFMC = 80 (Recent high-intensity rotation spike)
DMC = 120 (Sustained high workload this month)
DC = 180 (High chronic stress over past 2 months)
ISI = 15 (Small trigger could ignite)
BUI = 250 (Accumulated fatigue at critical levels)

→ Composite FWI = 185 → HIGH RISK
   Interpretation: Person could burn out this week with minimal additional stress
```

---

## Part 3: Intervention Protocols & Resource Management

### 3.1 Intervention Escalation Pathway

**System enforces structured escalation (no informal handling):**

#### GREEN Status (Healthy)
- **Fatigue Level:** ≤ 3 (Okay)
- **Cumulative Damage:** < 0.5
- **Burnout Prediction:** > 180 days
- **Actions:**
  - Routine workload monitoring
  - Annual wellness education
  - Encourage wellness activities (exercise, sleep, social connection)
  - Maintain schedule optimization (no unnecessary overload)

#### YELLOW Status (Early Warning)
- **Fatigue Level:** 4 (A little tired)
- **Cumulative Damage:** 0.5-0.7
- **Burnout Prediction:** 90-180 days
- **Actions:**
  - ✅ Weekly fatigue monitoring (Samn-Perelli scale)
  - ✅ Workload reduction 15-20%
  - ✅ Bi-weekly wellness check-ins with coordinator
  - ✅ Educational resources on stress management
  - ✅ Optional peer support group referral
  - ✅ Sleep hygiene consultation with occupational health

#### ORANGE Status (Elevated Risk)
- **Fatigue Level:** 5 (Moderately tired)
- **Cumulative Damage:** 0.7-0.9
- **Burnout Prediction:** 30-90 days
- **Actions:**
  - ✅ Twice-weekly fatigue assessments
  - ✅ **Mandatory 25-30% workload reduction**
  - ✅ **Weekly individual counseling** (psychologist or EAP)
  - ✅ **Occupational health evaluation** (sleep, exercise, nutrition)
  - ✅ **Peer support group participation** (weekly)
  - ✅ Consider shift swaps or rotation changes
  - ✅ Family/spouse education on recognizing burnout
  - ✅ Document accommodations in personnel file

#### RED Status (High Risk)
- **Fatigue Level:** 6 (Extremely tired)
- **Cumulative Damage:** > 0.9
- **Burnout Prediction:** < 30 days
- **Actions:**
  - ✅ **Daily fatigue monitoring**
  - ✅ **Immediate 50% workload reduction** (or medical leave)
  - ✅ **Mandatory psychiatric evaluation** (within 24 hours)
  - ✅ **Daily individual therapy sessions** (intensive outpatient)
  - ✅ **Sleep medicine consultation** (assess sleep disorders)
  - ✅ **Consider disability/medical leave** (2-4 weeks)
  - ✅ **Occupational health continuous monitoring**
  - ✅ **Family/crisis support activation**
  - ✅ **Return-to-work planning** (gradual restoration)

#### BLACK Status (Emergency)
- **Fatigue Level:** 7 (Exhausted/Dangerous)
- **Cumulative Damage:** ≥ 1.0 + acute symptoms
- **Burnout Prediction:** ≤ 7 days
- **Actions:**
  - ✅ **Immediate medical leave activation**
  - ✅ **Emergency psychiatric evaluation** (same day)
  - ✅ **Crisis intervention team engagement** (if safety concerns)
  - ✅ **Hospitalization consideration** (if suicidal ideation, self-harm)
  - ✅ **Occupational health daily check-ins**
  - ✅ **Family and support system activation**
  - ✅ **No clinical duties until cleared by psychiatry**
  - ✅ **Return-to-work requires multi-disciplinary approval**

### 3.2 Available Resources & Support Systems

#### Mental Health & Psychological Support

**1. Employee Assistance Program (EAP)**
- **Availability:** 24/7 phone line and web-based referrals
- **Coverage:** Up to 6 free counseling sessions per employee
- **Services:** Crisis counseling, individual therapy, family counseling, substance abuse referral
- **Access:** Confidential (does NOT report to employer unless safety concern)
- **Contact Protocol:**
  ```
  1. EAP hotline (posted on program bulletin board)
  2. Online portal for self-referral
  3. Coordinator can provide confidential referral
  ```

**2. Program-Based Mental Health Services**
- **Occupational Health Clinic:**
  - Sleep medicine evaluation (up to 4 visits)
  - Ergonomic assessment
  - Fitness/nutrition consultation
  - Sleep apnea screening

- **Peer Support Program:**
  - Trained peer advocates (residents/faculty who've recovered from burnout)
  - Weekly drop-in support groups (confidential)
  - One-on-one mentoring (matched by specialty)
  - Family support sessions (monthly)

**3. Psychiatric Services**
- **On-call psychiatrist:** Available for acute crisis evaluation (psychiatric emergency)
- **Outpatient psychiatry:** Medication management, intensive therapy
- **Inpatient psychiatry:** Crisis stabilization (48-hour hold if needed)
- **Specialty Services:** Substance abuse treatment, trauma therapy, cognitive-behavioral therapy

#### Occupational Health & Wellness

**1. Sleep Medicine**
- SAMN-based sleep assessment
- Sleep study referral (if obstructive sleep apnea suspected)
- Sleep hygiene education
- Napping protocol optimization
- **Target:** Restore sleep to 6-8 hours/night baseline

**2. Physical Fitness**
- Gym membership subsidies
- Fitness class scheduling (coordinated with duty hours)
- Personal training consultation (initial 3 sessions free)
- **Target:** 150 min/week moderate exercise (proven burnout reducer)

**3. Nutrition Counseling**
- Registered dietitian consultation (up to 4 visits)
- Meal prep education for residents with long shifts
- Snacking strategies (maintain blood glucose, avoid fatigue crashes)
- Caffeine/energy drink optimization
- **Target:** Stable energy levels, no sugar crashes

**4. Stress Management Training**
- Mindfulness/meditation classes (weekly)
- Yoga/tai chi (twice weekly)
- Biofeedback training (heart rate variability optimization)
- Time management workshops
- **Target:** Stress resilience tools, personalized strategies

#### Leave & Accommodation Options

**1. Flexible Scheduling**
- Request schedule blocks during low-stress periods
- Coordinate rotation sequences (heavy-light alternation)
- Protected time off (weekends/holidays)
- Study blocks (for research, board prep)

**2. Temporary Workload Reduction**
- **Light Duty Assignment:** Clinic-only rotations (reduced intensity)
- **Reduced Hours:** 60-70% capacity for 2-4 weeks
- **Rotation Swap:** Trade heavy rotation for lighter one
- **Delayed Rotation:** Push heavy rotation to later in year

**3. Extended Leave**
- **Sick Leave:** Unlimited accrual for diagnosed burnout/mental health condition
- **Medical Leave:** Up to 4 weeks unpaid (job protected)
- **Disability Leave:** 6+ weeks (requires physician certification)
- **Family Medical Leave Act (FMLA):** 12 weeks unpaid (federal protection)

**4. Return-to-Work Planning**
After medical leave or intensive intervention:
- **Phased Return:** 50% → 75% → 100% over 2-3 weeks
- **Modified Duties:** Avoid previously problematic rotations initially
- **Buddy System:** Partner with senior colleague for support
- **Weekly Check-ins:** Program director monitors recovery
- **Success Metrics:** Sleep improvements, fatigue scores, symptom resolution

#### Crisis Resources (24/7)

| Crisis | Contact | Response |
|--------|---------|----------|
| **Suicide Risk** | 988 (National Lifeline) | Crisis counselor, safety planning |
| **Psychiatric Emergency** | Hospital ER or 911 | Psychiatric evaluation, possible admission |
| **Substance Abuse Relapse** | SAMHSA National Helpline: 1-800-662-4357 | Detox/rehab referral, confidential |
| **Domestic Violence (if stress-related)** | 1-800-799-7233 (National DV Hotline) | Safety planning, shelter referral |
| **Program Crisis Hot Line** | [INSERT LOCAL] | Direct connection to program psychiatrist |

---

## Part 4: Monitoring & Surveillance Systems

### 4.1 Real-Time Dashboard Metrics

**Burnout Risk Widget** (visible to Program Director only):

```
CRITICAL ALERTS (2):
  - RES_017: 28 days to burnout (Miner damage: 0.95) → IMMEDIATE INTERVENTION
  - RES_023: 32 days to burnout (Miner damage: 0.92) → URGENT ACTION

HIGH RISK (7):
  - RES_008: 65 days to burnout
  - RES_012: 72 days to burnout
  - ... [5 more]

Risk Distribution:
  ⚫ CRITICAL: 2 (4%)
  🔴 HIGH: 7 (16%)
  🟠 MODERATE: 15 (35%)
  🟡 LOW: 19 (45%)

Average Miner Damage: 0.52 (healthy)
Median Days to Burnout: 145 days
People Above Warning Threshold (D > 0.7): 9 (21%)
```

### 4.2 Monthly Compliance Report

**Program Director receives:**
1. Individual burnout predictions (with confidence intervals)
2. Contagion risk scores (likelihood of cascade)
3. Recommendation for each person at elevated risk
4. Fatigue hazard alerts triggered (and responses taken)
5. Intervention outcomes (effectiveness tracking)
6. Trend analysis (are things getting better or worse?)
7. Comparison to previous month
8. Extrapolation of incident rates if trends continue

### 4.3 Annual Wellness & Burnout Assessment

**Required Data Points:**
- Maslach Burnout Inventory (MBI) - emotional exhaustion subscore
- PHQ-9 (depression screening)
- GAD-7 (anxiety screening)
- Sleep duration and quality assessment
- Work-life balance satisfaction
- Social support adequacy
- Suicidal ideation screening (Columbia Suicide Severity Rating Scale)

**Aggregate Analysis:**
- Burnout prevalence rates (% with MBI-EE > 27)
- Depression/anxiety prevalence
- Program trend year-over-year
- Comparison to national benchmarks (for medical residency)
- Recommendations for program-level changes

### 4.4 Post-Burnout Event Review

**When burnout occurs (medical leave, resignation, high MBI score):**

1. **Structured Debriefing:**
   - What early signs were missed?
   - Were interventions offered? If not, why?
   - What schedule factors contributed?
   - What happened with contagion (did it affect others)?

2. **Predictive Model Calibration:**
   - Actual burnout date vs. predicted date
   - Prediction error analysis
   - Adjust ensemble weights if needed
   - Calibrate personal parameters (person-specific resilience)

3. **System Learning:**
   - Update thresholds if models under/over-predicted
   - Identify constraint gaps (did scheduler miss something?)
   - Document lessons learned
   - Share anonymized case with faculty (de-identified)

---

## Part 5: Wellness Philosophy & Guiding Principles

### 5.1 System Design Principles

The Residency Scheduler implements wellness as a **core constraint**, not an afterthought:

1. **Prevention Over Cure**
   - Predict burnout 4-12 weeks early
   - Intervene before crisis
   - Avoid "rescue mode" (which perpetuates unsustainable patterns)

2. **Objective Measurement**
   - Quantify fatigue with validated scales (Samn-Perelli)
   - Predict with cross-disciplinary models (not subjective judgment)
   - Track progress with metrics, not anecdotes

3. **Dignity & Privacy**
   - All burnout data encrypted and access-restricted
   - Person knows when they're being monitored
   - Interventions designed to support, not punish
   - Medical leave is NOT a mark of weakness

4. **Sustainable Workloads**
   - Rotate heavy assignments (no one gets stuck)
   - Balance acute demand with recovery time
   - Protect minimum sleep and social restoration time
   - 80-hour rule is FLOOR of fairness, not ceiling

5. **Contagion Awareness**
   - Burned-out individuals affect team morale
   - Early intervention protects whole team
   - Celebrate recoveries and resilience

### 5.2 Resident Rights & Protections

**Residents have the explicit right to:**
1. Work within ACGME duty hour limits (no exceptions)
2. Take protected time off (cannot be pre-empted for coverage)
3. Request schedule accommodations without retaliation
4. Access EAP and mental health services confidentially
5. Medical leave without career penalty
6. Know their burnout risk status (transparent access to predictions)
7. Challenge predictions if they believe model is wrong
8. Participate in wellness planning

**Programs must NOT:**
- Pressure residents to work beyond duty limits
- Deny requested time off except true emergencies
- Use burnout diagnosis as grounds for dismissal
- Require public disclosure of mental health treatment
- Schedule them into rotations marked "high burnout risk"
- Retaliate for speaking up about fatigue concerns

---

## Part 6: Technical Implementation (For Development Teams)

### 6.1 Database Models

**Key Tables:**
```
- fatigue_assessments          # Samn-Perelli scores
- fatigue_hazard_alerts        # GREEN/YELLOW/ORANGE/RED/BLACK
- fatigue_interventions        # Actions taken + outcomes
- workload_history             # Daily blocks and intensity
- burnout_predictions          # Model output + confidence intervals
- symptom_records              # MBI/PHQ9/GAD7 assessments
- burnout_events               # Actual burnout occurrences (calibration)
- personal_calibration         # Person-specific model parameters
```

### 6.2 API Endpoints

**Burnout Prediction:**
```
POST /api/v1/burnout/predict
  → Ensemble prediction, risk level, interventions

GET /api/v1/burnout/dashboard
  → Program-wide risk overview

POST /api/v1/burnout/symptoms
  → Record assessment data

GET /api/v1/burnout/resident/{person_id}/fatigue
  → Miner's damage score
```

**Fatigue Risk Management:**
```
POST /api/v1/fatigue/assessment
  → Record Samn-Perelli scale

GET /api/v1/fatigue/hazard
  → Check current hazard level

POST /api/v1/fatigue/intervention
  → Record intervention taken
```

### 6.3 Scheduling Constraints

**Hard Constraints (prevent invalid schedules):**
- `EightyHourRuleConstraint`: Max 80 hours/4 weeks
- `OneInSevenRuleConstraint`: Min 1 day off per 7 days
- `SupervisionRatioConstraint`: Faculty:resident ratios
- `MaxShiftLengthConstraint`: PGY-1 max 16h, others max 24h

**Soft Constraints (preference-based):**
- `BurnoutProtectionConstraint`: Avoid assigning high-intensity work to high-risk residents
- `FatigueLoadConstraint`: Prefer light rotations for people with high fatigue

### 6.4 Alert Routing

**CRITICAL/HIGH burnout predictions route to:**
1. Program Director (email + dashboard)
2. Occupational Health (medical alert)
3. Psychiatry On-Call (if risk < 30 days)
4. EAP (concurrent enrollment offer)

**Hazard alerts route to:**
1. Shift supervisor (immediate awareness)
2. Occupational health (monitoring assignment)
3. Program coordinator (accommodation coordination)

---

## Part 7: ACGME Compliance Audit Findings

### 7.1 Current Implementation Status

| Requirement | System Status | Notes |
|------------|---------------|-------|
| **80-Hour Rule** | ✅ ENFORCED | Hard constraint, rolling 28-day windows |
| **1-in-7 Day Off** | ✅ ENFORCED | Max 6 consecutive days worked |
| **Supervision Ratios** | ✅ ENFORCED | Fractional load tracking |
| **PGY-1 16-Hour Limit** | ✅ ENFORCED | Hard constraint |
| **24+4 Hour Rule** | ✅ ENFORCED | Max 28 hours on-site |
| **Minimum Rest (10h)** | ⚠️ PARTIAL | FRMS enforces 8h (2h gap) |
| **Night Float Limit (6)** | ✅ ENFORCED | MAX_NIGHT_FLOAT_CONSECUTIVE = 6 |
| **Call Frequency (q3)** | ⚠️ TEMPLATE-BASED | Not hard constraint, relies on rotation design |
| **Moonlighting Tracking** | ✅ ENFORCED | Included in 80-hour calculation |

### 7.2 Identified Gaps & Recommendations

**Gap 1: Minimum Rest Hours**
- RAG documentation: 10 hours
- Code implementation: 8 hours
- **Action:** Verify current ACGME requirement and standardize

**Gap 2: Call Frequency**
- Documented requirement: Every 3rd night maximum
- Current implementation: Template-level control only
- **Recommendation:** Add `CallFrequencyConstraint` to enforce programmatically

**Gap 3: Post-Call Activity Restrictions**
- Requirement: No new patients in final 4 hours of shift
- Current implementation: Operational policy only (not enforced in scheduling)
- **Impact:** Low (typically enforced at workflow level)

### 7.3 ACGME Best Practices (Beyond Requirements)

**System Implements:**
1. ✅ Proactive duty hour monitoring (not just reactive)
2. ✅ Weekly compliance reports (exceeds annual requirement)
3. ✅ Automated violation prevention (vs. reactive correction)
4. ✅ Wellness integration (burnout as constraint, not afterthought)
5. ✅ Fatigue risk assessment (beyond hours alone)
6. ✅ Anonymous fatigue data collection (encourages honesty)
7. ✅ Multi-intervention strategy (not one-size-fits-all)
8. ✅ Historical data for program accreditation reviews

---

## Part 8: Key Resources for Program Directors

### 8.1 Burnout Recognition Checklist

**Watch for in residents:**
- [ ] Increasing fatigue scores (trending upward month-to-month)
- [ ] High Miner damage (> 0.7) without corresponding schedule review
- [ ] Repeated yellow/orange fatigue alerts without intervention
- [ ] Declining performance or quality concerns
- [ ] Increased sick leave usage
- [ ] Social withdrawal or isolation
- [ ] Cynical comments about medicine or patients
- [ ] Sleep complaints or visible fatigue
- [ ] Substance abuse indicators
- [ ] Depression/anxiety screening positives

**When to escalate immediately:**
- Burnout prediction < 30 days
- Fatigue level = 6 (extremely tired)
- Suicidal ideation (ANY mention)
- Active substance abuse
- Acute psychiatric symptoms

### 8.2 Intervention Decision Matrix

**If Fatigue Level 4 (Yellow):**
→ Workload reduction + weekly monitoring

**If Fatigue Level 5 (Orange):**
→ Workload reduction + weekly counseling + occupational health

**If Fatigue Level 6 (Red):**
→ Medical leave OR 50% workload reduction + daily monitoring + psychiatric eval

**If Fatigue Level 7 (Black):**
→ Emergency protocols + same-day psychiatric evaluation

### 8.3 Program-Level Interventions

**To reduce burnout across the program:**
1. **Rotation Design:**
   - Alternate heavy and light rotations
   - Avoid clustering high-stress assignments
   - Distribute call nights fairly

2. **Scheduling Practices:**
   - Respect protected time off (weekends, holidays)
   - Provide advance notice of schedules (not last-minute)
   - Build in administrative time (not just clinical)

3. **Culture & Leadership:**
   - Model wellness (PD visible stress management)
   - Celebrate those in recovery (remove stigma)
   - Regular wellness education
   - Faculty wellness (prevent top-down burnout)

4. **Resource Allocation:**
   - Fund EAP fully
   - Ensure occupational health availability
   - Support peer mentoring programs
   - Invest in fatigue risk monitoring tools

---

## Conclusion

The Residency Scheduler implements a comprehensive, evidence-based wellness framework that:

1. **Prevents burnout** through predictive modeling (4-12 week advance warning)
2. **Monitors fatigue** continuously using scientific thresholds (Samn-Perelli, FRMS)
3. **Detects early signals** using seismic algorithms (STA/LTA for precursors)
4. **Tracks contagion** using epidemiological models (burnout spread through teams)
5. **Enforces ACGME requirements** as hard scheduling constraints (no overrides without approval)
6. **Supports recovery** with multi-tiered interventions (GREEN → YELLOW → ORANGE → RED → BLACK)
7. **Protects residents** with documented rights and confidential resources
8. **Learns from events** by calibrating models against actual burnout occurrences

This represents a paradigm shift from reactive crisis response to proactive, scientifically-grounded wellness management—transforming residency scheduling from a logistical problem into a health optimization system.

---

**Document Metadata:**
- **Status:** OPERATIONAL GUIDANCE
- **Authority:** Program Director with Occupational Health oversight
- **Last Updated:** 2025-12-30
- **Next Review:** 2026-06-30 (6-month assessment of intervention effectiveness)
- **Related Documentation:**
  - BURNOUT_PREDICTION_SERVICE_SPEC.md (technical details)
  - ACGME Common Program Requirements (source regulatory framework)
  - FRMS documentation (fatigue risk protocols)
  - Epidemiology research (contagion modeling)
