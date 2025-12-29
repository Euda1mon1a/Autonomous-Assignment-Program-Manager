# Schedule Resilience Framework

## Overview

The resilience framework applies cross-disciplinary concepts from power grids, epidemiology, manufacturing, and other industries to medical residency scheduling. The goal is to create schedules that are robust, sustainable, and resistant to unexpected disruptions while preventing resident burnout and maintaining patient care quality.

## Core Resilience Concepts

### 80% Utilization Threshold

**Origin:** Queuing theory from telecommunications and operations research

**Principle:**
Systems operating above **80% capacity** experience non-linear degradation in performance. Beyond this threshold, small increases in demand cause exponential increases in wait times, errors, and system failures.

**Application to Residency Scheduling:**
- **Individual resident utilization:** Clinical work hours should average ≤80% of ACGME maximum
- **Team capacity:** Coverage should maintain 20% buffer above minimum requirements
- **Clinical service load:** Patient volume should not exceed 80% of theoretical maximum

**Why 80%?**
- **Below 80%:** System absorbs variations smoothly
- **80-90%:** Performance degradation becomes noticeable
- **90-95%:** Minor disruptions cause major delays
- **Above 95%:** System operates in constant crisis mode

**Monitoring:**
The system tracks utilization metrics:
- **Individual:** Average weekly hours / 80 hours maximum
- **Service:** Current residents / minimum required residents
- **Clinical load:** Patient census / target census

**Example:**
- Resident working 64 hours/week = 80% utilization → Healthy
- Resident working 72 hours/week = 90% utilization → Warning
- Resident working 76+ hours/week = 95%+ utilization → High risk for burnout

### N-1 and N-2 Contingency Analysis

**Origin:** Power grid reliability engineering

**Principle:**
Critical systems must remain functional even when one (N-1) or two (N-2) components fail. This ensures resilience to unexpected outages.

**Application to Residency Scheduling:**

**N-1 Analysis (Single Resident Absence):**
- Can each critical service maintain coverage if one resident is unavailable?
- Simulates: illness, family emergency, short-notice TDY
- **Pass criteria:** All shifts covered, no ACGME violations for remaining residents
- **Fail criteria:** Coverage gaps or remaining residents exceed duty hour limits

**N-2 Analysis (Two Resident Absences):**
- Can critical services survive two simultaneous absences?
- Simulates: multiple illnesses, deployment + sick leave, couple of residents with shared emergency
- **Pass criteria:** Emergency coverage maintained (may require faculty augmentation)
- **Partial pass:** Coverage maintained with temporary policy flexibilities
- **Fail criteria:** Patient care compromised, service must be suspended

**System Implementation:**
1. **Daily analysis:** Check if current schedule passes N-1 for all services
2. **Weekly analysis:** Check if schedule passes N-2 for critical services (ICU, ED)
3. **Alerts:** Notify program director when schedule fails N-1 or N-2
4. **Auto-suggestions:** System proposes schedule adjustments to restore resilience

**Example:**
- **ICU rotation:** Requires 2 residents minimum
- **Current staffing:** 4 residents assigned
- **N-1 test:** Remove 1 resident → 3 remain (>2 minimum) → PASS
- **N-2 test:** Remove 2 residents → 2 remain (=2 minimum) → MARGINAL PASS
- **Action:** Consider adding 5th resident to create better N-2 buffer

### Defense in Depth (Tiered Alert Levels)

**Origin:** Cybersecurity and nuclear power plant safety

**Principle:**
Multiple independent safety layers prevent catastrophic failures. As conditions worsen, each layer activates additional protections.

**Application to Residency Scheduling:**

The system uses five defense levels based on multiple resilience metrics:

**GREEN - Optimal Conditions:**
- All residents <75% utilization
- Schedule passes N-2 for all services
- No ACGME compliance concerns
- Adequate vacation and educational time scheduled
- **Action:** Normal operations, proactive planning

**YELLOW - Early Warning:**
- Some residents at 75-85% utilization
- Schedule passes N-1 but fails N-2 for some services
- Minor ACGME compliance margins (e.g., one resident at 78 hours/week)
- Vacation requests accumulating
- **Action:** Increase monitoring, prepare contingencies, address warning signs

**ORANGE - Elevated Risk:**
- Multiple residents at 85-95% utilization
- Schedule fails N-1 for non-critical services
- ACGME compliance approaching limits (multiple residents >75 hours/week)
- Coverage gaps emerging
- Burnout indicators present
- **Action:** Implement mitigations (redistribute workload, add faculty support), mandatory program director review

**RED - Critical Stress:**
- Residents consistently at 90%+ utilization
- Schedule fails N-1 for critical services (ICU, ED)
- ACGME violations occurring or imminent
- Multiple residents requesting stress-related leave
- Burnout epidemic spreading
- **Action:** Emergency interventions (reduce census, cancel electives, bring in locums), daily leadership huddles

**BLACK - System Failure:**
- ACGME violations systematic and unresolvable with current staffing
- Patient safety compromised
- Residents unable to provide adequate care due to exhaustion
- Mass resignations or medical leaves
- **Action:** Crisis management (close services, request external assistance, ACGME notification), survival mode

**Automated Defense Activation:**
The system automatically escalates defense levels and suggests interventions:
- **YELLOW → GREEN:** Reduce elective scheduling, redistribute call
- **ORANGE → YELLOW:** Add faculty coverage, reduce clinic volume, fast-track vacation requests
- **RED → ORANGE:** Cancel non-essential activities, activate moonlighting pool, request additional residents
- **BLACK → RED:** Emergency staffing, service line closures, ACGME reporting

### Static Stability (Fallback Schedules)

**Origin:** Power grid frequency regulation

**Principle:**
Pre-computed fallback states allow systems to quickly stabilize after disruptions without needing complex real-time calculations.

**Application to Residency Scheduling:**

**Pre-Computed Fallback Schedules:**
The system maintains pre-generated "emergency schedules" for common scenarios:

**Scenario 1: N-1 Fallback (One Resident Out)**
- Pre-computed schedules showing how to redistribute workload
- One fallback per critical service
- Updated monthly as resident skills/rotations change
- Can be activated instantly when resident calls in sick

**Scenario 2: N-2 Fallback (Two Residents Out)**
- More austere coverage patterns
- May include faculty step-up or reduced clinic schedules
- Used for deployment, extended illness, multiple emergencies

**Scenario 3: Holiday Minimum Coverage**
- Pre-planned minimal staffing for major holidays
- Balances resident time off with adequate patient care
- Rotates fairly across years

**Scenario 4: Deployment Surge**
- For military programs: pre-planned coverage during deployment waves
- Accounts for 1-3 residents deployed simultaneously
- May extend over 6-12 months

**Benefits:**
- **Speed:** Instantly deploy backup schedule when needed
- **Compliance:** Fallbacks are pre-validated for ACGME compliance
- **Predictability:** Residents know what happens in emergencies
- **Reduced stress:** No scrambling to create new schedule during crisis

### Sacrifice Hierarchy (Triage-Based Load Shedding)

**Origin:** Emergency medicine triage and electrical grid load shedding

**Principle:**
When capacity is insufficient, systematically reduce non-essential activities in a predefined priority order to protect critical functions.

**Application to Residency Scheduling:**

**Priority Tiers for Load Shedding:**

**Tier 1 - Protected (Never Sacrifice):**
- Emergency department coverage
- ICU coverage
- Inpatient ward coverage
- ACGME-required educational conferences
- Resident safety (duty hour limits)

**Tier 2 - High Priority (Sacrifice Only if Necessary):**
- Subspecialty inpatient consultations
- Procedure services (endoscopy, cath lab)
- Urgent outpatient care
- Required didactics

**Tier 3 - Medium Priority (Sacrifice Before Higher Tiers):**
- Elective procedures
- Non-urgent subspecialty clinics
- Elective rotations
- Administrative duties

**Tier 4 - Low Priority (Sacrifice First):**
- Research time
- Professional development activities
- Non-essential conferences
- Committee participation

**Implementation During Crisis:**
When the system enters RED or BLACK defense levels:
1. **Tier 4 activities suspended first**
2. **Tier 3 activities reduced next** (e.g., elective procedures rescheduled)
3. **Tier 2 activities modified** (e.g., some subspecialty clinics consolidated)
4. **Tier 1 activities protected at all costs** (may require external resources)

**Example Crisis Response:**
- **Scenario:** Three residents simultaneously ill with flu
- **Defense level:** RED (schedule fails N-1 for critical services)
- **Sacrifice hierarchy activation:**
  - Cancel research time (Tier 4) → Redeploy residents to clinical coverage
  - Postpone elective procedures (Tier 3) → Reduce procedure service needs
  - Consolidate subspecialty clinics (Tier 3) → Free up subspecialty attendings to cover general wards
  - Maintain ED and ICU coverage (Tier 1) → Non-negotiable

## Strategic Resilience Concepts

### Homeostasis (Biological Feedback Loops)

**Origin:** Physiology and systems biology

**Principle:**
Living systems maintain stability through continuous feedback and self-correction. Deviations from optimal states trigger compensatory responses.

**Application to Residency Scheduling:**

**Feedback Loops:**
- **Utilization too high → Automatic schedule lightening:** System suggests adding residents or reducing clinical load
- **Coverage gaps emerging → Preemptive scheduling:** Fill gaps before they become critical
- **Burnout indicators rising → Wellness interventions:** Trigger counseling, mental health resources, schedule relief

**Homeostatic Targets:**
- **Utilization:** Maintain 70-80% (self-adjusts if drifting higher or lower)
- **Call frequency:** Equitable distribution across residents (balances automatically)
- **Vacation:** Ensure regular time off (system prompts residents to schedule vacation)

**Example:**
- Resident's 4-week average hours: 68, 70, 72, 74 (trending upward)
- System detects trend before hitting 80-hour limit
- **Homeostatic response:** Suggest lighter rotations or additional days off in next block
- Returns resident to 70-hour average (homeostasis restored)

### Blast Radius Isolation (Failure Containment)

**Origin:** Amazon Web Services (AWS) availability zones

**Principle:**
Design systems so that failures are contained to small zones and don't cascade across the entire system.

**Application to Residency Scheduling:**

**Service-Based Isolation:**
- **Rotate residents across services:** Don't concentrate all senior residents on one service
- **Cross-train residents:** Multiple residents capable of covering each service
- **Avoid single points of failure:** No single resident is irreplaceable for any service

**Example:**
- **Bad design (large blast radius):** All three senior residents assigned to ICU simultaneously
  - If one deploys, ICU loses 33% of senior coverage
  - ICU becomes vulnerable (fails N-1)

- **Good design (small blast radius):** Senior residents distributed: 1 ICU, 1 wards, 1 ED
  - If ICU senior deploys, can temporarily rotate ED senior to ICU
  - Other services unaffected (failure contained)

**Time-Based Isolation:**
- **Stagger start dates for new rotations:** Not all residents change rotations the same day
- **Spread vacation across the year:** Avoid entire program taking vacation same month
- **Distribute call across the week:** Don't cluster all call on weekends

### Le Chatelier's Principle (Equilibrium Shifts)

**Origin:** Chemistry (equilibrium thermodynamics)

**Principle:**
When a system at equilibrium is disturbed, it shifts to counteract the disturbance and restore equilibrium.

**Application to Residency Scheduling:**

**Schedule Equilibrium:**
When disruptions occur (resident illness, deployment, emergency), the system automatically suggests compensatory shifts:
- **Resident out → Increase other residents' hours** (within ACGME limits)
- **High clinical demand → Reduce educational time temporarily** (make up later)
- **Faculty shortage → Increase senior resident autonomy** (with appropriate oversight)

**Restoration to Equilibrium:**
After the disruption passes, the system automatically "rebalances":
- Residents who covered extra shifts get lighter assignments later
- Educational time is restored with catch-up sessions
- Vacation requests prioritized for those who deferred time off

**Example:**
- **Disturbance:** Resident deployed for 6 months
- **Initial shift:** Remaining residents absorb clinical duties (increase hours)
- **Equilibrium restoration:** When deployed resident returns, others get lighter rotations and extra vacation
- **Final state:** All residents return to equitable workload distribution

## Advanced Resilience Analytics

### Statistical Process Control (SPC) Monitoring

**Origin:** Semiconductor manufacturing quality control

**Principle:**
Continuously monitor process metrics and detect when the system is drifting out of control before defects occur.

**Application to Residency Scheduling:**

**Control Charts:**
The system tracks key metrics over time and applies Western Electric rules to detect anomalies:

**Metrics Monitored:**
- **Individual resident hours per week** (target: 65-70, upper limit: 80)
- **Service coverage ratios** (target: 1.2× minimum, lower limit: 1.0×)
- **Burnout survey scores** (target: <3/10, alert: >5/10)
- **Swap request frequency** (target: 1-2/month, alert: >5/month)

**Western Electric Rules (Automated Alerts):**
- **Rule 1:** Any point outside control limits (e.g., resident exceeds 80 hours) → Immediate alert
- **Rule 2:** 2 of 3 consecutive points more than 2 standard deviations from mean → Trend alert
- **Rule 3:** 4 of 5 consecutive points more than 1 standard deviation from mean → Drift alert
- **Rule 4:** 8 consecutive points on one side of the mean → Systematic shift alert

**Example:**
- Resident's weekly hours: 68, 70, 72, 74, 76, 78, 80, 82
- **Rule 4 violated:** 8 consecutive weeks trending upward
- **System alert:** "Resident X showing systematic increase in work hours, approaching ACGME limit. Recommend schedule intervention."

### Burnout Epidemiology (SIR Models)

**Origin:** Public health and network epidemiology

**Principle:**
Burnout spreads through social networks like an infectious disease. The reproduction number (Rt) indicates whether burnout is spreading or declining.

**Application to Residency Scheduling:**

**Burnout States:**
- **Susceptible (S):** Residents at risk but not yet burned out
- **Infected (I):** Residents experiencing burnout symptoms
- **Recovered (R):** Residents who recovered through interventions

**Reproduction Number (Rt):**
- **Rt > 1:** Burnout is spreading (epidemic)
- **Rt = 1:** Burnout is stable (endemic)
- **Rt < 1:** Burnout is declining (containment)

**Transmission Mechanisms:**
- **Workload contagion:** Burned out residents work slower, increasing load on others
- **Morale contagion:** Negativity spreads through team dynamics
- **Swap cascades:** One resident's absence creates strain that spreads

**System Response:**
- **Rt approaching 1.0:** Yellow defense level, increase wellness resources
- **Rt > 1.0:** Orange/red defense level, implement load shedding, mandatory interventions
- **Goal:** Keep Rt < 0.8 through proactive schedule management

### Erlang Coverage (Queuing Optimization)

**Origin:** Telecommunications queuing theory

**Principle:**
Calculate optimal staffing levels to maintain service quality given variable demand and stochastic arrivals.

**Application to Residency Scheduling:**

**Erlang C Formula:**
Calculates probability that incoming patient/consult must wait given:
- **Arrival rate (λ):** Patients per hour
- **Service rate (μ):** Patients each resident can see per hour
- **Number of servers (N):** Residents on duty

**Specialist Staffing Optimization:**
- Determine minimum residents needed to maintain <10% wait probability
- Accounts for variability in patient arrivals
- Ensures adequate coverage during peak times

**Example:**
- **Emergency consults:** Average 3 per hour (λ=3), each takes 30 min (μ=2 per resident)
- **Erlang C calculation:** Need 2 residents to maintain <5% wait probability
- **Schedule:** Always assign ≥2 residents to consult service

## Practical Applications

### Dashboard Integration

The scheduling system integrates all resilience metrics into a unified dashboard:

**Resilience Score (0-100):**
Composite score based on:
- Utilization levels (30% weight)
- N-1/N-2 contingency (25% weight)
- Defense level (20% weight)
- Burnout indicators (15% weight)
- ACGME compliance margins (10% weight)

**Traffic Light Indicators:**
- **Green:** Resilience score 75-100
- **Yellow:** Resilience score 50-74
- **Orange:** Resilience score 25-49
- **Red:** Resilience score 0-24

**Early Warning System:**
- Predictive alerts when resilience metrics are trending toward thresholds
- Suggested interventions before problems become critical
- Automated scenario modeling ("What if resident X deploys next month?")

### Program Director Actions

Based on resilience framework insights, program directors can:

1. **Proactive scheduling:** Design schedules that pass N-1/N-2 from the start
2. **Early intervention:** Address Yellow/Orange defense levels before reaching Red
3. **Data-driven decisions:** Use utilization, SPC, and Erlang metrics to justify staffing requests
4. **Resident wellness:** Demonstrate to ACGME that burnout prevention is systematic, not reactive
5. **Accreditation readiness:** Document resilience monitoring for site visits

## Conclusion

The resilience framework transforms residency scheduling from reactive crisis management to proactive system design. By applying proven concepts from engineering, epidemiology, and operations research, programs can create schedules that are:

- **Robust:** Survive unexpected disruptions (N-1/N-2)
- **Sustainable:** Operate below stress thresholds (80% utilization)
- **Self-correcting:** Homeostatic feedback loops maintain equilibrium
- **Monitored:** SPC and analytics provide early warning
- **Optimized:** Erlang queuing ensures adequate coverage with minimal excess

This systematic approach protects resident well-being, ensures patient safety, and maintains ACGME compliance even in challenging circumstances.
