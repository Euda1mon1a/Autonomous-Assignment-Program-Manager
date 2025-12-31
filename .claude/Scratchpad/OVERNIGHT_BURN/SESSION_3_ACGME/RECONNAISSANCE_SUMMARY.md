# SEARCH_PARTY Reconnaissance Summary
## ACGME Wellness & Fatigue Mitigation Requirements

**Agent:** G2_RECON
**Mission:** Complete Wellness & Fatigue Mitigation Audit
**Date:** 2025-12-30
**Status:** COMPLETE

---

## Deliverable

**Primary Document:** `acgme-wellness-requirements.md` (943 lines)
**Location:** `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Scratchpad/OVERNIGHT_BURN/SESSION_3_ACGME/`

---

## Search Perimeter Coverage

### PERCEPTION - Current Wellness Programs Identified

The Residency Scheduler implements a **5-Tier Wellness Architecture**:

1. **Tier 1 - Real-Time Fatigue Management (FRMS)**
   - Location: `backend/app/resilience/frms/`
   - Samn-Perelli 7-level fatigue scale (real-time assessment)
   - Automated hazard alerts (GREEN/YELLOW/ORANGE/RED/BLACK)
   - Sleep debt tracking
   - Immediate intervention protocols

2. **Tier 2 - Predictive Burnout Modeling (Materials Science)**
   - Location: `backend/app/analytics/burnout_prediction/`
   - 5-model ensemble approach:
     - S-N Curve (workload-cycles relationship)
     - Miner's Rule (cumulative damage)
     - Coffin-Manson (recoverable vs. unrecoverable fatigue)
     - Larson-Miller (creep rupture from sustained stress)
     - Paris Law (symptom progression tracking)
   - Predicts burnout 4-12 weeks in advance
   - Confidence interval generation

3. **Tier 3 - Epidemiological Contagion (SIR/SEIR)**
   - Location: `backend/app/resilience/burnout_epidemiology.py`
   - Models burnout spread through social networks
   - Tracks transmission rates (β, σ, γ parameters)
   - Identifies superspreaders
   - Detects cascade risk

4. **Tier 4 - Seismic Precursor Detection (STA/LTA)**
   - Location: `backend/app/resilience/spc_monitoring.py`
   - Statistical Process Control (Western Electric rules)
   - Detects sudden changes in fatigue patterns
   - Triggers early warning before acute crisis

5. **Tier 5 - Multi-Temporal Danger Assessment (Fire Weather Index)**
   - Location: `backend/app/resilience/burnout_fire_index.py`
   - Composite danger scoring across temporal scales
   - FWI Index 0-40 (LOW) to 201+ (CRITICAL)
   - Combines acute, weekly, and chronic stress signals

### INVESTIGATION - Fatigue Mitigation Strategies Found

**Real-Time Interventions:**
- Duty restrictions (shift swaps, early release, schedule modification)
- Buddy system pairing with senior colleagues
- Mandatory rest periods
- Shift duration limits (enforce hard caps)
- Recovery time between shifts (10-hour minimum)

**Short-Term Interventions:**
- Workload reduction (15-50% depending on risk level)
- Weekly/daily fatigue monitoring
- Peer support group participation
- Individual counseling (weekly to daily)
- Sleep medicine consultation

**Long-Term Interventions:**
- Schedule redesign (rotating heavy/light assignments)
- Extended leave options (sick, medical, FMLA)
- Phased return-to-work protocols
- Personal model calibration (resilience assessment)
- Rotation sequence optimization

**Program-Level Interventions:**
- Rotation template design (balance intensity)
- Fair distribution of call nights
- Protected time off enforcement
- Faculty wellness modeling
- Culture change (destigmatize treatment)

### ARCANA - ACGME Wellness Requirements Documented

**Core Duty Hour Rules (ACGME Section VI.F):**
1. **80-Hour Rule** ✅
   - Maximum 80 hours/week averaged over rolling 4-week periods
   - Implemented as hard constraint with rolling window validation
   - Includes all clinical work, education, moonlighting

2. **One-in-Seven Rule** ✅
   - At least one 24-hour day off per 7 days (averaged over 4 weeks)
   - Minimum 4 full days off per 28-day period
   - Maximum 6 consecutive days worked

3. **Shift Duration Limits** ✅
   - PGY-1: Maximum 16 hours (strict, no exceptions)
   - PGY-2/3: Maximum 24 hours + 4 hours for handoff = 28 hours total

4. **Minimum Rest Between Shifts** ⚠️
   - ACGME Requirement: 10 hours
   - System Implementation: 8 hours (DISCREPANCY)
   - Gap identified, needs regulatory verification

5. **Night Float Limits** ✅
   - Maximum 6 consecutive nights
   - Enforced as hard constraint

6. **Call Frequency** ⚠️
   - Maximum every 3rd night (in-house call)
   - Documented requirement, template-based control only
   - Not enforced as hard constraint

7. **Supervision Ratios** ✅
   - PGY-1: 1 faculty : 2 residents
   - PGY-2/3: 1 faculty : 4 residents
   - Enforced through fractional load tracking

8. **Moonlighting Tracking** ✅
   - All moonlighting included in 80-hour calculation
   - Both internal and external tracked

### HISTORY - Wellness Evolution in System

**Evidence of Progressive Enhancement:**

1. **Phase 1 - Basic Compliance (Initial Implementation)**
   - Hard constraints for ACGME rules
   - 80-hour rule, 1-in-7, shift lengths

2. **Phase 2 - Fatigue Risk Management (Tier 1 Added)**
   - FRMS system with Samn-Perelli scale
   - Real-time hazard alerts
   - Intervention tracking

3. **Phase 3 - Predictive Analytics (Tier 2 Added)**
   - Burnout prediction service (specification: BURNOUT_PREDICTION_SERVICE_SPEC.md)
   - Materials science fatigue models
   - 4-12 week advance warning capability

4. **Phase 4 - Network Analysis (Tier 3 Added)**
   - Epidemiological contagion modeling
   - Burnout spread detection
   - Superspreader identification

5. **Phase 5 - Early Warning Systems (Tier 4-5 Added)**
   - Seismic precursor detection (STA/LTA)
   - Fire Weather Index adaptation
   - Multi-temporal danger assessment

### INSIGHT - Burnout Prevention Philosophy

**System Design Demonstrates:**
1. **Prevention Over Reaction** - Predict 4-12 weeks early, intervene proactively
2. **Scientific Rigor** - Cross-disciplinary models (not subjective judgment)
3. **Objective Measurement** - Validated scales (Samn-Perelli, MBI, PHQ-9, GAD-7)
4. **Privacy & Dignity** - Encrypted data, person knows status, confidential resources
5. **Sustainable Pace** - 80-hour rule as minimum fairness floor, not ceiling
6. **Contagion Awareness** - Burned-out person affects entire team
7. **Resident Rights** - Explicit protections against retaliation, confidential access to resources
8. **Continuous Learning** - Calibrate models from actual burnout events for improvement

### RELIGION - Is Wellness Tracked Systemically?

**YES - Comprehensive System Integration:**

1. **Database Models:**
   - `fatigue_assessments` (Samn-Perelli scores)
   - `fatigue_hazard_alerts` (risk levels)
   - `fatigue_interventions` (actions taken + outcomes)
   - `workload_history` (daily block intensity)
   - `burnout_predictions` (model outputs)
   - `symptom_records` (MBI/PHQ9/GAD7)
   - `burnout_events` (calibration data)
   - `personal_calibration` (person-specific parameters)

2. **Scheduling Constraints:**
   - Hard constraints (prevent invalid schedules)
   - Soft constraints (prefer better outcomes)
   - `BurnoutProtectionConstraint` (avoid overloading high-risk residents)

3. **Monitoring & Reporting:**
   - Real-time dashboard (program director view)
   - Weekly compliance reports
   - Monthly risk assessments
   - Annual burnout prevalence audits
   - Post-event review and learning

4. **Alert Routing:**
   - CRITICAL predictions → PD + Occupational Health + Psychiatry
   - HIGH predictions → PD + Occupational Health
   - Hazard alerts → Shift supervisor + program coordinator

5. **Measurement & Metrics:**
   - Miner's cumulative damage (0.0-1.0+ scale)
   - Burnout prediction days (ensemble output)
   - Confidence intervals (uncertainty quantification)
   - Risk levels (CRITICAL, HIGH, MODERATE, LOW)
   - Primary failure modes (S-N, Miner, Larson-Miller, Paris)

### NATURE - Is Wellness Performative or Real?

**REAL - NOT PERFORMATIVE:**

**Evidence of Genuine Implementation:**
1. **Hard Constraints** - Violations prevented at scheduling layer, not just monitored
2. **Automation** - No manual workarounds; system enforces rules
3. **Prediction** - 4-12 week advance warning (allows prevention, not crisis response)
4. **Multi-Intervention** - Not one-size-fits-all; graduated response based on severity
5. **Resource Commitment** - EAP, occupational health, psychiatry, peer support budgeted
6. **Privacy Protection** - Burnout data encrypted, not accessible to general admin
7. **Calibration Loop** - Models improve from actual burnout events (learning system)
8. **Resident Rights** - Documented protections against retaliation
9. **Leave Options** - Medical leave available without career penalty
10. **Escalation Protocols** - Emergency protocols for BLACK status (psychiatric eval within 24h)

**Not Performative Because:**
- Wellness is enforced BEFORE crisis (prevention)
- System prevents someone from being scheduled into burnout (not rescue afterward)
- Interventions are graduated (not binary on/off)
- Person's risk status is transparent (they can see predictions)
- Recovery supported (phased return, modified duties)
- Program learns from failures (model calibration)

### MEDICINE - Mental Health Resources Available

**Documented Resources in System:**

1. **Employee Assistance Program (EAP)**
   - 24/7 phone line + web portal
   - Up to 6 free counseling sessions
   - Crisis counseling available
   - Confidential (doesn't report to employer unless safety concern)

2. **On-Site Occupational Health**
   - Sleep medicine consultation (up to 4 visits)
   - Sleep apnea screening
   - Sleep hygiene education
   - Fitness/nutrition consultation
   - Ergonomic assessment

3. **Psychiatric Services**
   - On-call psychiatrist (acute crisis evaluation)
   - Outpatient psychiatry (medication management)
   - Inpatient psychiatry (crisis stabilization)
   - Specialty services (substance abuse, trauma, CBT)

4. **Peer Support Program**
   - Trained peer advocates (residents/faculty in recovery)
   - Weekly drop-in support groups (confidential)
   - One-on-one mentoring (specialty-matched)
   - Family support sessions (monthly)

5. **Crisis Resources (24/7)**
   - 988 Suicide & Crisis Lifeline
   - Hospital emergency services
   - SAMHSA substance abuse helpline (1-800-662-4357)
   - National Domestic Violence Hotline
   - Program crisis hot line (local)

6. **Wellness Programs**
   - Mindfulness/meditation classes (weekly)
   - Yoga/tai chi (twice weekly)
   - Gym membership subsidies
   - Stress management workshops
   - Time management training

### SURVIVAL - Crisis Intervention Protocols

**Escalation Pathway:**

| Status | Fatigue Level | Miner Damage | Days to Burnout | Protocol |
|--------|---------------|--------------|-----------------|----------|
| **GREEN** | ≤ 3 | < 0.5 | > 180 | Monitoring + education |
| **YELLOW** | 4 | 0.5-0.7 | 90-180 | 15-20% workload reduction + weekly check-ins |
| **ORANGE** | 5 | 0.7-0.9 | 30-90 | 25-30% reduction + weekly counseling |
| **RED** | 6 | > 0.9 | < 30 | 50% reduction/medical leave + daily monitoring |
| **BLACK** | 7 | ≥ 1.0 + acute symptoms | ≤ 7 | Emergency protocols + same-day psychiatry |

**BLACK Status Triggers:**
- Immediate medical leave activation
- Emergency psychiatric evaluation (same day)
- Crisis intervention team (if safety concerns)
- Hospitalization consideration (if suicidal ideation)
- Family and support system activation
- No clinical duties until cleared by psychiatry

**Recovery Support:**
- Phased return-to-work (50% → 75% → 100%)
- Modified duty assignments (avoid previously problematic rotations)
- Buddy system pairing
- Weekly check-ins with program director

### STEALTH - Hidden Burnout Indicators Detected

**System Detects Multiple Precursor Signals:**

1. **Fatigue Signal Precursors:**
   - Trending fatigue scores (direction matters)
   - Increasing Samn-Perelli levels week-to-week
   - Sleep debt accumulation
   - Circadian disruption (night float clustering)

2. **Workload Anomalies (SPC Rules):**
   - Sudden spikes (Rule 1: 3σ from mean)
   - Sustained elevation (Rule 2: 9 consecutive high weeks)
   - Upward trends (Rule 3: 6 consecutive increasing weeks)
   - Oscillating high values (Rule 4: 2-3 consecutive >2σ)

3. **Symptom Progression (Paris Law):**
   - MBI Emotional Exhaustion trending upward
   - PHQ-9 depression scores increasing
   - GAD-7 anxiety scores increasing
   - Single-item burnout scale deterioration

4. **Contagion Spread (Epidemiology):**
   - Multiple residents in same rotation burning out simultaneously
   - Burnout after one person departs (redistribution of work)
   - Demoralization spreading through team

5. **Damage Accumulation (Miner's Rule):**
   - High-intensity cycles clustering
   - Insufficient recovery time between heavy rotations
   - No low-intensity weeks for healing

6. **Creep Damage (Larson-Miller):**
   - Sustained 70+ hour weeks (not acute spikes, but chronic)
   - Persistent moderate-high workload over 8+ weeks
   - No planned restoration weeks

---

## Key Findings Summary

### What Works Well
✅ **Hard constraints prevent violations** - 80-hour rule, 1-in-7, shift limits enforced at scheduling layer
✅ **Predictive capability** - 4-12 week advance warning with 80%+ sensitivity (target)
✅ **Multi-layered detection** - Detects via fatigue, workload patterns, symptoms, contagion, precursors
✅ **Graduated interventions** - Response scales with severity (not binary)
✅ **Resident rights protection** - Documented, explicit protections against retaliation
✅ **Privacy-first design** - Burnout data encrypted, restricted access
✅ **Learning loop** - Models calibrate from actual burnout events
✅ **Resource availability** - EAP, occupational health, psychiatry, peer support budgeted

### Compliance Gaps Identified
⚠️ **Minimum Rest Hours** - Code enforces 8 hours, ACGME specifies 10 hours (2-hour gap)
⚠️ **Call Frequency Constraint** - Documented (q3) but not enforced as hard constraint, template-based only
⚠️ **Night Float Documentation** - Code enforces 6-night limit but not documented in RAG knowledge base

### Operational Strengths
🎯 **Proactive Prevention** - Burnout detected/prevented BEFORE crisis (not reactive rescue)
🎯 **System Learning** - Burnout event post-review calibrates models for improvement
🎯 **Program-Level Insight** - Dashboard gives PD visibility into team risk, not just individuals
🎯 **Contagion Awareness** - Recognizes burned-out person affects entire team morale

---

## Conclusion

The Residency Scheduler implements **comprehensive, evidence-based wellness as a core system feature**, not an add-on:

1. ✅ ACGME duty hour rules enforced as hard constraints
2. ✅ Real-time fatigue monitoring with automated alerts
3. ✅ Predictive burnout modeling 4-12 weeks in advance
4. ✅ Multi-disciplinary scientific approaches (materials science, epidemiology, seismology)
5. ✅ Graduated intervention protocols (GREEN → RED → BLACK)
6. ✅ Robust mental health resources and crisis support
7. ✅ Resident privacy protections and right to treatment
8. ✅ System learning loop (calibrate from actual outcomes)

**This represents a paradigm shift from reactive crisis response to proactive, scientifically-grounded wellness management.**

---

**Documentation Complete**
**Deliverable:** `acgme-wellness-requirements.md` (943 lines, comprehensive)
**Classification:** OPERATIONAL GUIDANCE
**Authority:** Program Director with Occupational Health oversight
