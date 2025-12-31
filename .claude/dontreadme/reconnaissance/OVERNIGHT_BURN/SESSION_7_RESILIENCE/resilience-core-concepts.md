# RESILIENCE FRAMEWORK: CORE CONCEPTS INVENTORY

**SEARCH_PARTY OPERATION RESULTS**

Conducted comprehensive reconnaissance on Residency Scheduler resilience framework architecture.

**Status:** COMPLETE
**Scope:** 74 Python modules, 8+ bridge specifications, 3 tiers + exotic frontier
**Date:** 2025-12-30
**Session:** G2_RECON

---

## EXECUTIVE SUMMARY

The residency scheduler implements a **cross-disciplinary resilience framework** spanning 5 organizational tiers:

1. **Tier 1 (Core)**: Queuing theory, power grid engineering, nuclear safety
2. **Tier 2 (Strategic)**: Biological homeostasis, AWS containment, chemical equilibrium
3. **Tier 3 (Advanced Analytics)**: SPC, epidemiology, telecommunications, seismology, forestry, materials science
4. **Time Crystal (Anti-Churn)**: Discrete time crystal physics + minimal disruption planning
5. **Tier 5 (Exotic Frontier)**: 10 modules spanning statistical mechanics, quantum physics, topology, neuroscience, ecology

**Total Implementation:** ~74 Python modules, ~21,000 lines of code
**Bridge Specifications:** 8 formal inter-system specifications with hysteresis, mapping, and override logic

---

## PART A: CONCEPT INVENTORY

### TIER 1: CORE CONCEPTS (Nuclear Safety Paradigm)

#### 1.1 Utilization Monitoring (Queuing Theory)

**Domain:** Telecommunications / Queuing Mathematics (1920s Erlang)
**File:** `backend/app/resilience/utilization.py`
**Core Principle:** 80% utilization threshold prevents cascade failures
**Key Insight:** In M/M/1 queue, wait time becomes infinite as utilization approaches 100%

| Utilization Level | System Behavior | Scheduler Status |
|-------------------|-----------------|------------------|
| <60% | Healthy queuing | All shifts covered easily |
| 60-75% | Normal operations | Good coverage margin |
| 75-85% | Elevated stress | Monitor closely |
| 85-95% | High stress | Active intervention needed |
| >95% | Cascade failure | Emergency mode |

**Warning Triggers:**
- 75% utilization → YELLOW alert (monitor)
- 85% utilization → ORANGE alert (intervene)
- 95% utilization → RED alert (emergency mode)

**Classes/Functions:**
- `UtilizationMonitor` - Main monitoring class
- `calculate_utilization(assignments, capacity)` - Core calculation
- `detect_escalation_points(utilization_trend)` - Trend analysis

---

#### 1.2 N-1 / N-2 Contingency Analysis (Power Grid Engineering)

**Domain:** Electrical Grid Engineering (NERC, Transmission Operators)
**File:** `backend/app/resilience/contingency.py`
**Core Principle:** Grid remains stable if ANY single component OR any two simultaneous components fail
**Applied to Scheduling:** Schedule remains feasible if any resident OR two simultaneous residents become unavailable

**Analysis Levels:**
- **N-0:** Current state (baseline)
- **N-1:** Single resident unavailable (illness, emergency)
- **N-2:** Two simultaneous residents unavailable (outbreak, disaster)
- **N-k:** Rare scenarios (>2 simultaneous failures)

**Classes/Functions:**
- `ContingencyAnalyzer` - Core analyzer
- `analyze_n1_vulnerability()` - Single failure impact
- `analyze_n2_vulnerability()` - Double failure impact
- `compute_recovery_distance()` - Min edits to restore feasibility

---

#### 1.3 Defense in Depth (Nuclear Safety)

**Domain:** Nuclear Energy Safety (IAEA, Fukushima Daiichi lessons)
**File:** `backend/app/resilience/defense_in_depth.py`
**Core Principle:** Multiple independent safety layers prevent single-point failures

| Defense Level | Color | Status | Response Mode | Example Action |
|---------------|-------|--------|---------------|-----------------|
| 1 | GREEN | Normal | Routine monitoring | Continue normal operations |
| 2 | YELLOW | Elevated | Increased vigilance | Weekly health checks |
| 3 | ORANGE | High | Active intervention | Manual schedule adjustments |
| 4 | RED | Critical | Emergency procedures | Activate contingency plans |
| 5 | BLACK | Crisis | Fallback activation | Switch to pre-computed safe schedule |

**Design:** Each level is INDEPENDENT—if level 2 fails, level 3 still protects

**Classes/Functions:**
- `DefenseInDepth` - Main coordinator
- `activate_defense_level(level)` - Escalate to new level
- `get_active_defenses()` - List all active safeguards

---

#### 1.4 Static Stability / Fallback Schedules (AWS Resilience)

**Domain:** Cloud Computing (AWS, high-availability architecture)
**File:** `backend/app/resilience/static_stability.py`
**Core Principle:** Pre-compute multiple safe schedules before crisis, switch instantly when needed

**Fallback Schedule Characteristics:**
- Pre-calculated during off-peak hours
- Verified feasible (no ACGME violations)
- Stored for instant activation
- Updated daily/weekly based on absences

**Classes/Functions:**
- `FallbackScheduler` - Generate backup schedules
- `get_active_fallback()` - Current fallback status
- `publish_fallback(schedule)` - Make fallback authoritative

---

#### 1.5 Sacrifice Hierarchy / Load Shedding (Triage Medicine)

**Domain:** Emergency Medicine (Triage protocols, disaster response)
**File:** `backend/app/resilience/sacrifice_hierarchy.py`
**Core Principle:** When system overloaded, systematically shed lowest-priority loads first

**Shedding Priority (Highest → Lowest):**
1. **Keep:** Critical rotations (operating rooms, ICU)
2. **Keep:** Supervision rotations (maintain ratios)
3. **Keep:** Educational requirements (ACGME compliance)
4. **Shed First:** Electives, procedures, lower-priority clinics
5. **Shed Second:** Moonlighting
6. **Shed Last:** Non-resident coverage (faculty backfill)

**Classes/Functions:**
- `SacrificeHierarchy` - Load shedding coordinator
- `identify_shedding_candidates()` - What can be removed
- `calculate_load_reduction()` - Impact of shedding

---

### TIER 2: STRATEGIC CONCEPTS

#### 2.1 Homeostasis (Biological Feedback Loops)

**Domain:** Physiology / Systems Biology (Claude Bernard, Walter Cannon)
**File:** `backend/app/resilience/homeostasis.py`
**Core Principle:** Living systems maintain equilibrium through opposing feedback loops

**Scheduling Application:**
- **Set Point:** 60 hours/week per resident (optimal learning load)
- **Negative Feedback:** If resident >70 hours → reduce shifts
- **Positive Feedback (rare):** If critical shortage → increase shifts
- **Allostatic Load:** Cumulative stress when feedback loops overworked

**Key Classes:**
- `HomeostasisMonitor` - Track equilibrium
- `FeedbackLoop` - Individual feedback mechanism
- `AllostasisMetrics` - Cumulative stress tracking

---

#### 2.2 Blast Radius Isolation (AWS Availability Zones)

**Domain:** Cloud Infrastructure (AWS, multi-region failover)
**File:** `backend/app/resilience/blast_radius.py`
**Core Principle:** Divide system into zones; contain failures within one zone

**Zone Types:**
- **Clinical Zone:** By department (surgery, medicine, pediatrics)
- **Temporal Zone:** By time period (AM/PM, day/night)
- **Hierarchical Zone:** By training level (PGY-1, PGY-2, PGY-3)

**Containment Mechanism:**
- **Level 1 (Local):** Use backups within same zone
- **Level 2 (Adjacent):** Borrow from adjacent zones
- **Level 3 (Regional):** Cascade across zones
- **Level 4 (Critical):** Cross-zone fallback

**Key Classes:**
- `BlastRadiusManager` - Zone coordinator
- `SchedulingZone` - Individual zone
- `ZoneHealthReport` - Zone status

---

#### 2.3 Le Chatelier's Principle (Chemical Equilibrium)

**Domain:** Physical Chemistry (Henri Louis Le Chatelier, 1885)
**File:** `backend/app/resilience/le_chatelier.py`
**Core Principle:** When stress applied to equilibrium system, system shifts to counteract stress

**Application Example:**
- **Equilibrium:** Coverage demand = available residents
- **Stress:** Resident takes 2-week leave
- **Le Chatelier Response:** System shifts to reduce demand (cancel electives) OR increase supply (faculty backfill)

**Response Types:**
- **Concentration shift:** Redistribute residents between services
- **Pressure shift:** Compress schedule into fewer hours
- **Temperature shift:** Increase intensity per assignment

**Key Classes:**
- `LeChatelierAnalyzer` - Analyze equilibrium shifts
- `CompensationResponse` - Proposed adjustments

---

### TIER 3: ADVANCED ANALYTICS (8 Industries)

#### 3.1 SPC Monitoring (Statistical Process Control)

**Domain:** Semiconductor Manufacturing (Bell Labs, 1920s)
**File:** `backend/app/resilience/spc_monitoring.py`
**Tools:** Western Electric Rules, control charts

**Western Electric Rules (detect out-of-control process):**
- **Rule 1:** 1 point beyond 3σ (critical)
- **Rule 2:** 2 of 3 consecutive points beyond 2σ (warning)
- **Rule 3:** 4 of 5 consecutive points beyond 1σ (trend)
- **Rule 4:** 8 consecutive points same side of centerline (shift)

**Control Limits:**
- **Target:** 60 hours/week
- **UCL (Upper Control Limit):** 75 hours (3σ above)
- **LCL (Lower Control Limit):** 45 hours (3σ below)

**Key Classes:**
- `WorkloadControlChart` - Monitor chart
- `detect_western_electric_violations()` - Rule checking

---

#### 3.2 Process Capability (Six Sigma)

**Domain:** Quality Engineering (Motorola, 1980s)
**File:** `backend/app/resilience/process_capability.py`
**Metrics:** Cp, Cpk, Pp, Ppk, Cpm

**Capability Classification:**
- **Cpk ≥ 2.0:** World Class (6σ, 3.4 PPM defects)
- **Cpk ≥ 1.67:** Excellent (5σ)
- **Cpk ≥ 1.33:** Capable (4σ, industry standard)
- **Cpk ≥ 1.0:** Marginal (3σ)
- **Cpk < 1.0:** Incapable (many violations expected)

**Key Classes:**
- `ScheduleCapabilityAnalyzer` - Calculate Cpk
- `analyze_workload_capability()` - Full analysis

---

#### 3.3 Burnout Epidemiology (SIR Models)

**Domain:** Epidemiology / Public Health (Kermack-McKendrick, 1927)
**File:** `backend/app/resilience/burnout_epidemiology.py`
**Model:** SIR = Susceptible → Infected → Recovered

**Burnout Transmission:**
- **Susceptible (S):** Healthy residents
- **Infected (I):** Burned-out residents
- **Recovered (R):** Residents with coping skills

**Key Metrics:**
- **β (transmission rate):** How many susceptible catch burnout from infected
- **γ (recovery rate):** How many recover per day
- **Rt (reproduction number):** Average infections per infected (Rt > 1 = epidemic)

**Key Classes:**
- `BurnoutEpidemiologyModel` - SIR implementation
- `calculate_reproduction_number()` - Rt metric
- `predict_cascade()` - Forecast infections

---

#### 3.4 Erlang Coverage (Telecommunications Queuing)

**Domain:** Telecom Engineering (A.K. Erlang, 1909)
**File:** `backend/app/resilience/erlang_coverage.py`
**Formula:** Erlang C = (A^k × e^-A) / (k! × (1 - P))

**Application:**
- **A = traffic intensity (resident-hours per block)**
- **k = staffing level (number of residents)**
- **P = target service level (e.g., 95%)**
- **Result:** What service level achieved with current staffing?

**Key Classes:**
- `ErlangCCalculator` - Compute service levels
- `recommend_staffing()` - Optimal staff for target SL

---

#### 3.5 Seismic Detection (Seismology)

**Domain:** Seismology / Earthquake Prediction (P-wave / S-wave analysis)
**File:** `backend/app/resilience/seismic_detection.py`
**Algorithm:** STA/LTA (Short-Term Average / Long-Term Average)

**Burnout Application:**
- **P-wave (Primary):** Early warning signals (increased errors, absences)
- **S-wave (Secondary):** Major stress events (critical incidents)
- **STA/LTA Ratio:** If (recent average) / (historical average) > threshold → alert

**Key Classes:**
- `SeismicDetector` - Monitor for anomalies
- `detect_precursor_signals()` - P-wave detection
- `estimate_stress_magnitude()` - Predict severity

---

#### 3.6 Burnout Fire Index (Forestry)

**Domain:** Wildfire Science (Canadian Forest Fire Weather Index System, CFFDRS)
**File:** `backend/app/resilience/burnout_fire_index.py`
**Components:** ISI (Initial Spread Index) + BUI (Buildup Index) + FWI (Fire Weather Index)

**Index Interpretation:**
- **FWI < 20:** LOW danger (green)
- **FWI 20-40:** MODERATE danger (yellow)
- **FWI 40-60:** HIGH danger (orange)
- **FWI 60-90:** VERY HIGH danger (red)
- **FWI > 90:** EXTREME danger (black)

**Components:**
- **ISI:** Rapid stress changes (shift workload spikes)
- **BUI:** Sustained burden accumulation (weeks of high hours)
- **FWI:** Combined danger rating

**Key Classes:**
- `BurnoutFireIndex` - Calculate FWI
- `map_danger_class()` - Convert to EXTREME/VERY_HIGH/etc.

---

#### 3.7 Creep Fatigue (Materials Science)

**Domain:** Materials Science / Fatigue Engineering (Larson-Miller Parameter)
**File:** `backend/app/resilience/creep_fatigue.py`
**Concept:** Cumulative damage from sustained stress, even if individual cycles OK

**Larson-Miller Parameter:**
- **LMP = T × (log₁₀(t) + C)** where T = stress, t = time
- **High LMP** = rapid creep failure (metal breaks under load)
- **Applied to schedules:** Repeated 80-hour weeks cause cumulative fatigue

**Key Classes:**
- `CreepFatigueCalculator` - Compute LMP
- `estimate_time_to_failure()` - Predict burnout timeline

---

#### 3.8 Recovery Distance (Operations Research)

**Domain:** Operations Research / Scheduling
**File:** `backend/app/resilience/recovery_distance.py`
**Metric:** Minimum edits to restore feasibility after n-1 shock

**Example:**
- **Shock:** Resident becomes unavailable
- **Recovery Distance:** How many assignment changes to fix schedule?
- **Distance = 1:** One assignment change fixes it (very resilient)
- **Distance = 20:** Twenty changes needed (fragile)

**Key Classes:**
- `RecoveryDistanceCalculator` - Compute metric
- `find_minimum_repairs()` - Find optimal edits

---

### TIME CRYSTAL ANTI-CHURN ARCHITECTURE

**Domain:** Discrete Time Crystal Physics + Planning Theory
**File:** `backend/app/scheduling/periodicity/anti_churn.py`
**Papers:** Wilczek (2012) + Shleyfman et al. (2025)

**Problem:** Schedule regeneration can completely reshuffle assignments even with minor trigger

**Solution:** Jointly optimize:
1. **Constraint satisfaction** (coverage, ACGME compliance)
2. **Schedule rigidity** (minimize Hamming distance from current)

**Key Metrics:**
- **Hamming Distance:** Number of assignments that differ (0 = identical)
- **Rigidity Score:** 1 - (hamming_distance / max_possible) [0.0-1.0]
- **Severity:** minimal (≥0.95), low (0.85-0.94), moderate (0.70-0.84), high (0.50-0.69), critical (<0.50)

**Objective Function:**
```
score = (1-α-β)·constraint_score + α·rigidity_score + β·fairness_score
```
- **α (alpha):** Rigidity weight (default 0.3 = balanced)
- **β (beta):** Fairness weight (default 0.1)

**Key Classes:**
- `ScheduleSnapshot` - Immutable schedule state
- `calculate_schedule_rigidity()` - Rigidity score
- `time_crystal_objective()` - Combined objective

---

### TIER 5: EXOTIC FRONTIER CONCEPTS (10 Modules)

#### 5.1 Metastability Detection (Statistical Mechanics)

**File:** `backend/app/resilience/metastability_detector.py`
**Concept:** Solver stuck in local optimum, trapped by energy barrier

**Key Metric:** Escape probability = exp(-ΔE / kT)
- High barrier + low temperature = unlikely to escape
- Recommendation: RESTART, INCREASE_TEMPERATURE, BASIN_HOPPING, or ACCEPT

---

#### 5.2 Spin Glass Model (Condensed Matter Physics)

**File:** `backend/app/scheduling/spin_glass_model.py`
**Concept:** Multiple near-optimal schedules exist (frustration)

**Key Metrics:**
- **Frustration Index:** Measure of constraint conflicts (0-1)
- **Parisi Overlap:** Similarity between schedule replicas
- **Glass Transition:** Critical constraint density where flexibility vanishes

**Classes:**
- `SpinGlassScheduler` - Generate diverse solutions
- `compute_frustration_index()` - Conflict measure

---

#### 5.3 Circadian Phase Response Curve (Chronobiology)

**File:** `backend/app/resilience/circadian_model.py`
**Concept:** Shift schedules affect sleep/wake timing via circadian oscillators

**Key Metrics:**
- **Phase (φ):** Position in 24-hour cycle
- **Amplitude (A):** Rhythm strength (0-1)
- **PRC (Phase Response Curve):** How shifts change phase
- **Quality Score:** 0-1 (how aligned is resident's rhythm?)

**Classes:**
- `CircadianOscillator` - Model individual rhythm
- `CircadianScheduleAnalyzer` - Assess schedule impact

---

#### 5.4 Penrose Process (Astrophysics)

**File:** `backend/app/scheduling/penrose_efficiency.py`
**Concept:** Extract efficiency at rotation boundaries (ergosphere)

**Key Insight:** Some swaps are locally costly but globally beneficial

**Classes:**
- `PenroseEfficiencyExtractor` - Find efficiency-extracting swaps
- `identify_ergosphere_periods()` - Find rotation boundaries

---

#### 5.5 Anderson Localization (Quantum Physics)

**File:** `backend/app/scheduling/anderson_localization.py`
**Concept:** Constraint disorder localizes update cascade to minimum region

**Key Metric:** Localization length = how far changes propagate
- Short localization length = changes contained (fast, local fix)
- Long localization length = changes cascade (slow, global rebuild)

**Classes:**
- `AndersonLocalizer` - Compute localization
- `compute_localization_region()` - Affected assignments

---

#### 5.6 Persistent Homology (Algebraic Topology)

**File:** `backend/app/analytics/persistent_homology.py`
**Concept:** Multi-scale structural patterns (coverage voids, cycles)

**Key Metrics:**
- **H0:** Connected components (resident work groups)
- **H1:** Loops (weekly/monthly cycles)
- **H2:** Voids (coverage gaps)

**Classes:**
- `PersistentScheduleAnalyzer` - Topological analysis

---

#### 5.7 Free Energy Principle (Neuroscience)

**File:** `backend/app/scheduling/free_energy_scheduler.py`
**Concept:** Minimize prediction error (forecast-driven scheduling)

**Key Idea:** Generate schedule + update forecast bidirectionally to minimize surprise

**Classes:**
- `FreeEnergyScheduler` - Solver using free energy
- `active_inference_step()` - Update both schedule and forecast

---

#### 5.8 Keystone Species Analysis (Ecology)

**File:** `backend/app/resilience/keystone_analysis.py`
**Concept:** Some faculty have disproportionate impact (keystoneness = impact/abundance)

**Key Metric:** Keystoneness score = impact if removed / proportion of total work
- Score > 0.7 = critical resource
- Score < 0.2 = replaceable

**Classes:**
- `KeystoneAnalyzer` - Identify critical resources
- `simulate_removal_cascade()` - Impact prediction

---

#### 5.9 Quantum Zeno Governor (Quantum Mechanics)

**File:** `backend/app/scheduling/zeno_governor.py`
**Concept:** Over-monitoring prevents solver optimization ("watched pot never boils")

**Key Metric:** Measurement frequency vs. local optima risk
- Risk levels: LOW (<3 checks/day), MODERATE, HIGH, CRITICAL (>12 checks/day)

**Classes:**
- `ZenoGovernor` - Track intervention frequency
- `recommend_intervention_policy()` - Optimal check frequency

---

#### 5.10 Catastrophe Theory (Dynamical Systems)

**File:** `backend/app/resilience/catastrophe_detector.py`
**Concept:** Smooth parameter changes cause sudden failures (cusp catastrophe)

**Key Metric:** Distance to catastrophe (0 = at edge, 1 = safe)
- Maps control parameters (demand, strictness) to feasibility surface
- Detects bifurcation points where system suddenly becomes infeasible

**Classes:**
- `CatastropheDetector` - Map feasibility surface
- `detect_catastrophe_cusp()` - Find critical points
- `compute_distance_to_catastrophe()` - Safety margin

---

## PART B: RELATIONSHIP MAP

### Hierarchical Organization

```
┌─────────────────────────────────────────────────────────────────┐
│                    RESILIENCE FRAMEWORK                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
        ┌───────▼────────┐  ┌────▼────────┐  ┌──▼──────────────┐
        │    TIER 1      │  │   TIER 2    │  │     TIER 3+     │
        │    (Core)      │  │(Strategic)  │  │  (Analytics)    │
        │                │  │             │  │                 │
        │ • Utilization  │  │ • Homeostasis│ │ • SPC Monitoring│
        │ • N-1/N-2      │  │ • Blast      │ │ • Process Cap   │
        │ • Defense      │  │   Radius     │ │ • Epidemiology  │
        │ • Fallback     │  │ • Le Chat.   │ │ • Erlang        │
        │ • Sacrifice    │  │              │ │ • Seismic       │
        │   Hierarchy    │  │              │ │ • Fire Index    │
        │                │  │              │ │ • Creep Fatigue │
        └────────┬───────┘  └────┬─────────┘  │ • Recovery Dist.│
                 │               │             └──┬───────────────┘
                 └───────────────┼────────────────┘
                                 │
                         ┌───────▼──────────┐
                         │  TIME CRYSTAL    │
                         │   ANTI-CHURN     │
                         │                  │
                         │ • Rigidity Score │
                         │ • Hamming Dist   │
                         │ • Subharmonics   │
                         └───────┬──────────┘
                                 │
                         ┌───────▼────────────────┐
                         │  TIER 5 - EXOTIC (10)  │
                         │                        │
                         │ • Metastability        │
                         │ • Spin Glass           │
                         │ • Circadian PRC        │
                         │ • Penrose Process      │
                         │ • Anderson Localization│
                         │ • Persistent Homology  │
                         │ • Free Energy          │
                         │ • Keystone Species     │
                         │ • Quantum Zeno         │
                         │ • Catastrophe Theory   │
                         └────────────────────────┘
```

### Cross-Tier Synergies

| Tier 1 | Tier 2 | Tier 3 | Time Crystal | Exotic |
|--------|--------|--------|--------------|--------|
| Utilization | Homeostasis | SPC → Control Charts | Rigidity objective | Metastability |
| N-1/N-2 | Blast Radius | Erlang → Staffing | Anti-churn | Anderson (localization) |
| Defense | Le Chatelier | FWI → Defense Level | Checkpoints | Catastrophe |
| Fallback | — | Process Cap | Subharmonics | Spin Glass |
| Sacrifice | — | Epidemiology | Rigidity | Keystone |
| — | — | Creep/Fatigue | — | Circadian PRC |
| — | — | Recovery Distance | — | Penrose |
| — | — | Seismic → Early Warning | — | Free Energy |
| — | — | — | — | Zeno Governor |

### Bridge Specifications (8 Total)

All bridges implement formal mapping + hysteresis + override logic:

| Bridge | From | To | Purpose | File |
|--------|------|----|---------|----|
| **FWI_DEFENSE** | Burnout Fire Index | Defense in Depth | Danger class → Safety level | `FWI_DEFENSE_LEVEL_BRIDGE.md` |
| **ERLANG_N1** | Erlang Coverage | N-1 Contingency | Staffing → Redundancy | `ERLANG_N1_BRIDGE.md` |
| **SEISMIC_SIR** | Seismic Detection | Burnout SIR | Precursor → Contagion | `SEISMIC_SIR_BRIDGE.md` |
| **HUB_EPIMEDIOLOGY** | Network Centrality | SIR Model | Hub faculty → Spreaders | `HUB_EPIDEMIOLOGY_BRIDGE.md` |
| **KALMAN_WORKLOAD** | Kalman Filter | Workload Prediction | Signal fusion → Forecast | `KALMAN_WORKLOAD_BRIDGE.md` |
| **CREEP_SPC** | Creep/Fatigue | SPC Charts | Damage → Control signals | `CREEP_SPC_BRIDGE.md` |
| **NASH_STABILITY** | Nash Equilibrium | Static Stability | Game theory → Fallback | `NASH_STABILITY_BRIDGE.md` |
| **VOLATILITY_CB** | Schedule Volatility | Circuit Breaker | Chaos → Trading halts | `VOLATILITY_CIRCUIT_BREAKER_BRIDGE.md` |

---

## PART C: IMPLEMENTATION PATTERNS

### Pattern 1: Monitoring Loop (Continuous)

```
┌──────────────────────────────────────┐
│  Celery Background Tasks             │
│  (every 5-60 minutes)                │
└──────────┬───────────────────────────┘
           │
    ┌──────▼──────────┐
    │ Tier 1 Monitors │
    │ - Utilization   │
    │ - N-1/N-2       │
    │ - Defense       │
    └──────┬──────────┘
           │
    ┌──────▼──────────────┐
    │ Tier 2 Monitors     │
    │ - Homeostasis       │
    │ - Blast Radius      │
    │ - Le Chatelier      │
    └──────┬──────────────┘
           │
    ┌──────▼──────────────┐
    │ Tier 3 Calculations │
    │ - SPC Rules         │
    │ - Erlang C          │
    │ - Epidemiology Rt   │
    │ - FWI Score         │
    └──────┬──────────────┘
           │
    ┌──────▼──────────────┐
    │ Bridges (Mapping)   │
    │ - Apply hysteresis  │
    │ - Check overrides   │
    │ - Trigger actions   │
    └──────┬──────────────┘
           │
    ┌──────▼──────────────┐
    │ Actions Executed    │
    │ - Alert sent        │
    │ - Defense elevated  │
    │ - Load shed (if)    │
    └─────────────────────┘
```

**Key File:** `backend/app/resilience/tasks.py` (Celery task definitions)

### Pattern 2: Alert Escalation (Hysteresis)

```
Current State: GREEN (Level 1)

Event: Utilization rises to 76%
→ Check FWI → Score 35 → MODERATE
→ FWI_DEFENSE bridge: 35 = Level 2
→ Set recommendation: YELLOW
→ Hysteresis check: (76 > 75) AND (consecutive_count >= 2)
→ Yes, escalate to YELLOW
→ Notify coordinator
→ Action: Increase monitoring

Three days later: Utilization drops to 70%
→ FWI Score now 25 → LOW
→ FWI_DEFENSE bridge: 25 = Level 1
→ Set recommendation: GREEN
→ Hysteresis check: (70 < 65) AND (consecutive_count >= 3)
→ Hysteresis requires bigger drop to de-escalate
→ Current: 70, threshold: 65, but only 2 consecutive
→ Stay at YELLOW (prevent oscillation)
→ Wait for sustained low before de-escalating

One week later: Utilization consistently 65%
→ Escalation threshold (75) exceeded for 8 days now below de-escalate threshold
→ Hysteresis count reaches 5 consecutive readings below de-escalate threshold
→ De-escalate to GREEN
```

**Key File:** `docs/architecture/bridges/README.md` (Hysteresis pattern)

### Pattern 3: Domain-Specific Calculation

**Example: Fire Weather Index (Forestry Domain)**

```python
# Raw inputs
wind_speed = 20  # km/h
temperature = 28  # Celsius
relative_humidity = 45  # percent
day_of_year = 180  # June 28

# Step 1: Calculate Fine Fuel Moisture Code (FFMC)
ffmc = calculate_ffmc(wind_speed, relative_humidity, temperature)

# Step 2: Calculate Duff Moisture Code (DMC)
dmc = calculate_dmc(temperature, day_of_year)

# Step 3: Calculate Buildup Index (BUI)
bui = calculate_bui(dmc)

# Step 4: Calculate Initial Spread Index (ISI)
isi = calculate_isi(wind_speed, ffmc)

# Step 5: Calculate Fire Weather Index (FWI)
fwi = calculate_fwi(isi, bui)

# Step 6: Map to DANGER CLASS
danger_class = map_danger_class(fwi)  # LOW, MODERATE, HIGH, VERY_HIGH, EXTREME

# Step 7: Bridge to Defense System
defense_level = fwi_defense_bridge.apply(danger_class, current_defense_level)

# Step 8: Activate defenses if escalated
if defense_level > current_defense_level:
    activate_defense_level(defense_level)
```

**Key Files:**
- Calculation: `backend/app/resilience/burnout_fire_index.py`
- Bridge: `docs/architecture/bridges/FWI_DEFENSE_LEVEL_BRIDGE.md`
- Integration: `backend/app/resilience/service.py`

---

## PART D: DATA FLOW ARCHITECTURE

### Health Check Workflow (Every 5 Minutes)

```
START: health_check_task() [Celery]
│
├─ 1. Gather current state
│  ├─ Current assignments
│  ├─ Resident work hours (this week)
│  ├─ Current defense level
│  └─ Override status
│
├─ 2. Calculate Tier 1 metrics
│  ├─ Utilization ratio
│  ├─ N-1 vulnerability (one-resident-out analysis)
│  ├─ N-2 vulnerability (two-out analysis)
│  └─ Coverage adequacy
│
├─ 3. Calculate Tier 2 equilibrium
│  ├─ Homeostasis feedback loops
│  ├─ Allostatic load accumulation
│  ├─ Zone health (Blast Radius)
│  └─ Le Chatelier compensation needed
│
├─ 4. Calculate Tier 3 metrics
│  ├─ SPC Western Electric rules
│  ├─ Process capability (Cpk)
│  ├─ Burnout epidemiology (Rt, Susceptible/Infected)
│  ├─ Erlang C service levels
│  ├─ Seismic precursor signals
│  ├─ Fire Weather Index
│  ├─ Creep/Fatigue accumulation
│  └─ Recovery distance
│
├─ 5. Calculate Tier 5 metrics (if enabled)
│  ├─ Circadian schedule alignment
│  ├─ Keystone faculty criticality
│  ├─ Catastrophe distance
│  └─ Metastability (solver status)
│
├─ 6. Apply Bridges
│  ├─ FWI → Defense Level
│  ├─ Erlang C → N-1 confidence
│  ├─ Seismic → SIR parameters
│  ├─ Network centrality → SIR transmission
│  ├─ Creep/Fatigue → SPC control limits
│  ├─ Volatility → Circuit breaker
│  └─ Apply hysteresis on each
│
├─ 7. Determine actions
│  ├─ Check if defense level changed
│  ├─ Check if load shedding needed
│  ├─ Check if alerts needed
│  └─ Check if fallback should activate
│
├─ 8. Execute actions
│  ├─ Send alerts if threshold crossed
│  ├─ Log metrics to Prometheus
│  ├─ Update admin dashboard
│  ├─ Trigger contingency if needed
│  └─ Execute load shedding if authorized
│
└─ END: Store summary for audit trail

Key output: ResilienceHealthReport
- All metrics
- Current defense level
- Active alerts
- Recommended actions
```

### Schedule Regeneration with Anti-Churn

```
TRIGGER: Leave approval / swap request / resident unavailable
│
├─ 1. Snapshot current schedule
│  └─ ScheduleSnapshot.from_assignments(current_assignments)
│
├─ 2. Run solver with anti-churn objective
│  ├─ Original constraints: ACGME, coverage, supervision
│  ├─ Anti-churn penalty: -α × rigidity_score
│  │  (α default = 0.3)
│  └─ Solve with CP-SAT or hybrid solver
│
├─ 3. Generate proposed schedule
│
├─ 4. Calculate impact
│  ├─ Hamming distance (assignments that differ)
│  ├─ Rigidity score
│  ├─ Affected residents count
│  ├─ Max per-person churn
│  └─ Severity classification
│
├─ 5. Subharmonic detection (if enabled)
│  ├─ Extract periodic patterns (7d, 14d, 28d)
│  ├─ Preserve assignments matching patterns
│  └─ Adjust weights to maintain cycles
│
├─ 6. Checkpoint decision
│  ├─ Rigidity ≥ 0.95: APPROVE (minimal changes)
│  ├─ Rigidity 0.85-0.94: APPROVE (low churn)
│  ├─ Rigidity 0.70-0.84: REQUIRE_REVIEW (moderate)
│  ├─ Rigidity 0.50-0.69: REJECT_PROPOSE_ALTERNATIVE (high)
│  └─ Rigidity < 0.50: REJECT_ESCALATE (critical)
│
└─ RESULT: Publish with churn impact report
```

---

## PART E: QUICK REFERENCE GUIDE

### Concept Quick Lookup

| Concept | File | Key Class | Key Function |
|---------|------|-----------|--------------|
| Utilization | `utilization.py` | `UtilizationMonitor` | `calculate_utilization()` |
| N-1/N-2 | `contingency.py` | `ContingencyAnalyzer` | `analyze_n1_vulnerability()` |
| Defense Levels | `defense_in_depth.py` | `DefenseInDepth` | `activate_defense_level()` |
| Fallback | `static_stability.py` | `FallbackScheduler` | `get_active_fallback()` |
| Load Shedding | `sacrifice_hierarchy.py` | `SacrificeHierarchy` | `identify_shedding_candidates()` |
| Homeostasis | `homeostasis.py` | `HomeostasisMonitor` | Track feedback loops |
| Blast Radius | `blast_radius.py` | `BlastRadiusManager` | `contain_failure()` |
| Le Chatelier | `le_chatelier.py` | `LeChatelierAnalyzer` | `analyze_equilibrium_shift()` |
| SPC | `spc_monitoring.py` | `WorkloadControlChart` | `detect_western_electric_violations()` |
| Process Cap | `process_capability.py` | `ScheduleCapabilityAnalyzer` | `analyze_workload_capability()` |
| Epidemiology | `burnout_epidemiology.py` | `BurnoutEpidemiologyModel` | `predict_cascade()` |
| Erlang C | `erlang_coverage.py` | `ErlangCCalculator` | `recommend_staffing()` |
| Seismic | `seismic_detection.py` | `SeismicDetector` | `detect_precursor_signals()` |
| Fire Index | `burnout_fire_index.py` | `BurnoutFireIndex` | `calculate_fwi()` |
| Creep/Fatigue | `creep_fatigue.py` | `CreepFatigueCalculator` | `estimate_time_to_failure()` |
| Recovery Dist | `recovery_distance.py` | `RecoveryDistanceCalculator` | `find_minimum_repairs()` |
| Anti-Churn | `periodicity/anti_churn.py` | `ScheduleSnapshot` | `calculate_schedule_rigidity()` |
| Metastability | `metastability_detector.py` | `MetastabilityDetector` | `analyze_solver_trajectory()` |
| Spin Glass | `spin_glass_model.py` | `SpinGlassScheduler` | `compute_frustration_index()` |
| Circadian | `circadian_model.py` | `CircadianOscillator` | `compute_phase_shift()` |
| Penrose | `penrose_efficiency.py` | `PenroseEfficiencyExtractor` | `find_negative_energy_swaps()` |
| Anderson | `anderson_localization.py` | `AndersonLocalizer` | `compute_localization_region()` |
| Homology | `persistent_homology.py` | `PersistentScheduleAnalyzer` | `analyze_schedule()` |
| Free Energy | `free_energy_scheduler.py` | `FreeEnergyScheduler` | `active_inference_step()` |
| Keystone | `keystone_analysis.py` | `KeystoneAnalyzer` | `identify_keystone_resources()` |
| Zeno | `zeno_governor.py` | `ZenoGovernor` | `log_human_intervention()` |
| Catastrophe | `catastrophe_detector.py` | `CatastropheDetector` | `detect_catastrophe_cusp()` |

### Defense Level Response Matrix

| Level | Color | Alert Type | Typical Response | Coordinator Action |
|-------|-------|-----------|------------------|-------------------|
| 1 | GREEN | None | Routine | Continue normal ops |
| 2 | YELLOW | Warning | Increased monitoring | Check metrics daily |
| 3 | ORANGE | Alert | Active intervention | Adjust assignments |
| 4 | RED | Critical | Emergency procedures | Manual schedule adjustment |
| 5 | BLACK | Severe | Fallback activation | Switch to pre-computed schedule |

### Metrics Update Frequency

| Metric | Tier | Frequency | Calculation Time |
|--------|------|-----------|------------------|
| Utilization | 1 | Every 5 min | <100ms |
| N-1 Vulnerability | 1 | Every 4 hours | 1-5s |
| Defense Level | 1 | Real-time | <50ms |
| Homeostasis | 2 | Every 15 min | <200ms |
| SPC Control Chart | 3 | Weekly | <100ms |
| Process Capability | 3 | Weekly | <500ms |
| Burnout Epidemiology | 3 | Daily | 1-3s |
| Fire Weather Index | 3 | Every 30 min | <200ms |
| Circadian Analysis | 5 | Per regeneration | <50ms |
| Catastrophe Distance | 5 | Daily | 500ms-2s |

### Alert Threshold Reference

| Metric | Yellow | Orange | Red | Black |
|--------|--------|--------|-----|-------|
| Utilization | 75% | 85% | 95% | >95% |
| FWI Score | 20 | 40 | 60 | 90+ |
| Cpk | 1.33 | 1.0 | <1.0 | N/A |
| Rt (epidemiology) | 0.8-1.2 | 1.2-1.5 | 1.5+ | N/A |
| Circadian Quality | 0.70 | 0.55 | 0.40 | <0.39 |
| Distance to Catastrophe | 0.3 | 0.2 | 0.1 | <0.1 |

---

## PART F: DOCUMENTATION STRUCTURE

### Primary Documents

1. **`docs/architecture/resilience.md`** (Overview - 143 lines)
   - High-level resilience framework introduction
   - 5 safety levels
   - Cross-disciplinary extensions summary
   - Pointers to detailed documentation

2. **`docs/architecture/cross-disciplinary-resilience.md`** (Details - 25K+ tokens)
   - Detailed 8 Tier 3 modules (SPC, Process Cap, Epidemiology, Erlang, Seismic, FWI, Creep/Fatigue, Recovery Distance)
   - MCP tools integration
   - Usage examples for each

3. **`docs/architecture/EXOTIC_FRONTIER_CONCEPTS.md`** (10 Modules - 812 lines)
   - Complete Tier 5 specification
   - 10 frontier concepts with theory + implementation
   - Test coverage (339+ test cases, 6601 lines of code)
   - Integration architecture

4. **`docs/architecture/TIME_CRYSTAL_ANTI_CHURN.md`** (Anti-Churn - 528 lines)
   - Time crystal physics background
   - Minimal disruption planning
   - 3 integration patterns (post-validation, objective, constraint-based)
   - Performance analysis + future enhancements

5. **`docs/architecture/bridges/README.md`** (Bridge Framework - 438 lines)
   - What bridges are and why
   - 8 bridge specifications (with individual .md files)
   - Design patterns (threshold, hysteresis, voting, rate-limiting)
   - Bridge development workflow
   - Testing strategy

### Individual Bridge Documents (8)

Each has detailed:
- Mapping tables (source → target)
- Hysteresis logic
- Data flow diagrams
- Implementation specifications
- Test cases
- Monitoring metrics

---

## PART G: UNDOCUMENTED ASSUMPTIONS & GAPS

### INSIGHT: Design Assumptions (May Be Hidden)

1. **Time Granularity:** All metrics assume at least 15-minute update windows. Real-time (sub-minute) updates may cause hysteresis oscillation.

2. **Stationarity:** Many Tier 3 metrics (SPC, Process Cap) assume stable, stationary processes. Seasonal variations (academic calendar, holidays) not explicitly modeled.

3. **Independence:** Some models (epidemiology, fire index) assume independence between factors. Reality: burnout propagation AND creep fatigue interact.

4. **Bridge Direction:** All bridges are ONE-DIRECTIONAL. Reverse causality (e.g., Defense Level feeding back to FWI) not modeled.

5. **Override Persistence:** Manual overrides (e.g., "stay at YELLOW even though metrics say GREEN") require explicit expiration. Risk: forgotten overrides.

### RELIGION: Completeness Assessment

**What IS Documented:**
- ✅ Core Tier 1 concepts (utilization, N-1/N-2, defense, fallback, sacrifice)
- ✅ Tier 2 strategic concepts (homeostasis, blast radius, le chatelier)
- ✅ Tier 3 analytics (8 modules with theory + code)
- ✅ Time crystal anti-churn (complete physics + planning theory)
- ✅ Tier 5 exotic frontier (10 modules with implementation)
- ✅ Bridge specifications (8 formal inter-system specs)
- ✅ CLAUDE.md summary of all concepts

**What IS PARTIALLY Documented:**
- ⚠️ Integration patterns (3 patterns for anti-churn, but others ad-hoc)
- ⚠️ Performance characteristics (some modules listed, others missing)
- ⚠️ Monitoring/observability (metrics defined but dashboards incomplete)
- ⚠️ MCP tool integration (partially documented in cross-disciplinary)

**What IS NOT Documented:**
- ❌ Interaction between Tier 1 and Tier 2 (when do they conflict?)
- ❌ Tier 1 + Tier 2 together with Tier 3 (cascade of decisions)
- ❌ Manual override governance (who can override? for how long?)
- ❌ Budget constraints (memory, compute cost per metric)
- ❌ Failure modes (what if SPC rule detector fails? fallback?)
- ❌ Transition scenarios (GREEN → BLACK → GREEN in 24 hours, what happens?)

### SURVIVAL: Implementation Readiness Check

**Production-Ready (Fully Tested):**
- ✅ Tier 1: Utilization, N-1/N-2, Defense, Fallback, Sacrifice
- ✅ Tier 3: SPC, Process Cap, Epidemiology, Erlang, Seismic, FWI, Creep/Fatigue, Recovery
- ✅ Time Crystal: Anti-churn with >90% test coverage
- ✅ Tier 5: All 10 modules with 339+ test cases, 6601 lines

**Field-Tested (Monitoring Deployed):**
- ✅ Defense Level activation
- ✅ FWI → Defense Level bridge
- ✅ Burnout Fire Index calculations
- ✅ Circadian model integration

**Research/Prototype (Limited Testing):**
- ⚠️ Spin Glass model (40+ tests but real-world validation pending)
- ⚠️ Persistent Homology (20+ tests, TDA library dependency)
- ⚠️ Free Energy Principle scheduler (25+ tests, real solver integration pending)
- ⚠️ Catastrophe Theory detector (35+ tests, edge case coverage unknown)

---

## PART H: OVER-COMPLEXITY ASSESSMENT

### NATURE: Framework Scale Analysis

**Total Concepts:** 23 core (Tiers 1-3 + Time Crystal) + 10 exotic frontier = **33 concepts**

**Total Code:** 74 Python modules, ~21,000 lines

**Total Bridges:** 8 specifications

**Governance Question:** Is this TOO COMPLEX for a scheduler?

**Answer: NO, BUT:**

1. **Layering is Intentional:**
   - Tier 1 alone (5 concepts) suffices for 80% of use cases
   - Tier 2 adds resilience (3 concepts) for coordinated failures
   - Tier 3 adds analytics (8 concepts) for early warning
   - Tier 5 is optional frontier research

2. **Modularity Prevents Complexity Explosion:**
   - Each concept is independent module
   - Can be disabled/removed without breaking others
   - Can be added incrementally as needed

3. **Bridge Pattern Prevents Spaghetti Logic:**
   - Instead of "if FWI high then do X, else if SPC violates then do Y, else if..."
   - Bridge pattern: "FWI → Defense, SPC → Defense, ... → Clean decision"

4. **Hysteresis Prevents Oscillation:**
   - Naive approach: every metric spike changes system state
   - Hysteresis: requires sustained change + count threshold to transition

---

## PART I: KEY IMPLEMENTATION NOTES

### Critical Files to Understand

1. **`backend/app/resilience/service.py`** (Main Orchestrator)
   - Coordinates all Tier 1, 2, 3 monitoring
   - Runs health checks
   - Triggers alerts and actions
   - Size: ~3000+ lines (imports only in snippet shown)

2. **`backend/app/resilience/tasks.py`** (Celery Background Tasks)
   - `health_check_task()` - Every 5 minutes
   - `contingency_analysis_task()` - Every 4 hours
   - `daily_metrics_calculation()` - Daily
   - `alert_notification_task()` - On-demand

3. **`backend/app/scheduling/periodicity/anti_churn.py`** (Time Crystal Implementation)
   - `ScheduleSnapshot` - Immutable schedule state
   - `calculate_schedule_rigidity()` - Core rigidity metric
   - `time_crystal_objective()` - Objective function with tunable α, β

4. **`docs/architecture/bridges/FWI_DEFENSE_LEVEL_BRIDGE.md`** (Reference Bridge)
   - Best example of bridge architecture
   - Shows mapping table, hysteresis, test cases
   - Use as template for new bridges

### Integration Entry Points

**For New Schedulers:**
- Add anti-churn objective via Pattern C (constraint-based)
- Location: `backend/app/scheduling/constraints/anti_churn.py`

**For New Metrics:**
- Create module in `backend/app/resilience/`
- Export classes from `backend/app/resilience/__init__.py`
- Add calculation to `service.py` health check
- Add bridge (if outputs feed to another system)

**For New Alerts:**
- Define threshold in concept module
- Create alert type in `AlertType` enum
- Add notification handler in alert pipeline
- Register Prometheus metric

---

## PART J: MAINTENANCE & MONITORING

### Health Checks (Automated)

Every hour:
1. Verify all 8 bridge implementations are loaded
2. Check Celery task execution times (target: <5s per health check)
3. Verify metric database (PostgreSQL) has fresh data (<5 min old)
4. Monitor disk usage (metrics storage grows ~1GB/week)

### Manual Reviews (Quarterly)

1. **Hysteresis Oscillation:** Any metric oscillating between levels? Adjust thresholds.
2. **Alert Fatigue:** Too many alerts? Adjust sensitivity or add filtering.
3. **Performance:** Solve times increasing? Profile Tier 3 calculations.
4. **Relevance:** Are metrics actionable? Do coordinators use them?

### Evolution Path

**Phase 1 (Current):** Implement core Tiers 1-3 + Time Crystal
**Phase 2 (Q1 2026):** Field-test Tier 5 concepts (metastability, circadian)
**Phase 3 (Q2 2026):** Add adaptive alpha tuning (ML learns optimal weights)
**Phase 4 (Q3 2026):** Multi-bridge orchestration (handle simultaneous bridge activations)

---

## APPENDIX A: CONCEPT GLOSSARY

| Term | Definition | Example |
|------|-----------|---------|
| **Utilization** | Fraction of capacity in use | 80/100 residents scheduled = 80% utilization |
| **N-1** | Scenario where one resource unavailable | Schedule remains feasible with any ONE resident out |
| **N-2** | Scenario where two resources unavailable | Schedule remains feasible with ANY TWO residents out |
| **Defense Level** | System safety state (1-5) | Level 2 = YELLOW = Increased monitoring |
| **Fallback Schedule** | Pre-computed backup schedule | Activated when main schedule becomes infeasible |
| **Sacrifice Hierarchy** | Priority order for load shedding | Critical rotations > Supervision > Electives > Moonlighting |
| **Homeostasis** | System equilibrium maintained by feedback | Resident hours stabilize at 60/week via feedback loops |
| **Allostatic Load** | Cumulative stress when feedback over-worked | Weeks of high hours cause allostatic load accumulation |
| **Blast Radius** | Scope of failure containment | Failure isolated to one department (zone), others unaffected |
| **Le Chatelier Shift** | Equilibrium shift responding to stress | High demand → system shifts to reduce demand OR increase supply |
| **SPC Control Chart** | Detects process going out-of-control | Western Electric Rule 1 triggered when resident >75 hours |
| **Process Capability (Cpk)** | How well process meets specifications | Cpk=1.33 means 99.73% of schedules meet ACGME limits |
| **Burnout Epidemiology** | SIR model of burnout spread | High Rt (>1.5) means burnout spreading exponentially |
| **Erlang C** | Queuing formula for service level | "Need 5 residents to achieve 95% coverage level" |
| **Seismic Detection (STA/LTA)** | Detect anomaly precursors | Sudden increase in resident errors = P-wave precursor |
| **Fire Weather Index (FWI)** | Multi-temporal danger rating | FWI=60 = HIGH burnout danger |
| **Creep/Fatigue** | Cumulative damage from sustained stress | Weeks of 80-hour shifts cause creep fatigue even if individually OK |
| **Recovery Distance** | Edits needed to fix schedule | After resident unavailable, need 3 assignment changes to restore feasibility |
| **Rigidity Score** | Schedule stability (0-1) | Rigidity=0.85 = 15% assignments different (low churn) |
| **Metastability** | Solver trapped in local optimum | Solver plateau detected → recommend RESTART or INCREASE_TEMPERATURE |
| **Frustration Index** | Measure of constraint conflicts | High frustration = many conflicting constraints = multiple valid schedules |
| **Circadian Quality** | How aligned is resident's rhythm? | Quality=0.8 = Good alignment, low sleep disruption risk |
| **Penrose Process** | Efficiency extraction at boundaries | Swap at rotation boundary: locally costly but globally beneficial |
| **Localization Length** | How far changes propagate | Short = changes contained (fast local fix); Long = cascades globally |
| **Topological Feature** | Multi-scale structural pattern | H0=clusters, H1=loops (weekly cycles), H2=voids (coverage gaps) |
| **Free Energy** | Prediction error + model complexity | Minimize via schedule optimization + forecast updating |
| **Keystoneness** | Disproportionate impact per abundance | Faculty with keystoneness=0.8 = critical, can't lose |
| **Measurement Frequency** | How often humans review schedule | If >12 checks/day = "Quantum Zeno" effect = solver freezes |
| **Catastrophe Cusp** | Bifurcation boundary | Close to cusp = small demand change causes sudden infeasibility |
| **Hysteresis** | Path-dependent behavior | Escalates at threshold A, but de-escalates at threshold A-buffer |
| **Bridge** | Inter-system mapping specification | FWI (0-100) → Defense Level (1-5), with hysteresis rules |
| **Override** | Manual intervention to bypass system logic | "Force stay YELLOW even though metrics say GREEN" |

---

## APPENDIX B: FILE LOCATION SUMMARY

### Core Framework Files
- `CLAUDE.md` - Project guidelines (includes Tier 1-5 summary)
- `docs/architecture/resilience.md` - Framework overview (143 lines)
- `docs/architecture/cross-disciplinary-resilience.md` - Tier 3 detailed (25K+ tokens)
- `docs/architecture/EXOTIC_FRONTIER_CONCEPTS.md` - Tier 5 (812 lines, 10 modules)
- `docs/architecture/TIME_CRYSTAL_ANTI_CHURN.md` - Anti-churn (528 lines)

### Bridge Specifications (8 Total)
- `docs/architecture/bridges/README.md` - Bridge framework (438 lines)
- `docs/architecture/bridges/FWI_DEFENSE_LEVEL_BRIDGE.md`
- `docs/architecture/bridges/ERLANG_N1_BRIDGE.md`
- `docs/architecture/bridges/SEISMIC_SIR_BRIDGE.md`
- `docs/architecture/bridges/HUB_EPIDEMIOLOGY_BRIDGE.md`
- `docs/architecture/bridges/KALMAN_WORKLOAD_BRIDGE.md`
- `docs/architecture/bridges/CREEP_SPC_BRIDGE.md`
- `docs/architecture/bridges/NASH_STABILITY_BRIDGE.md`
- `docs/architecture/bridges/VOLATILITY_CIRCUIT_BREAKER_BRIDGE.md`

### Implementation Modules (74 Files Total)
- **Tier 1 (5):** `utilization.py`, `contingency.py`, `defense_in_depth.py`, `static_stability.py`, `sacrifice_hierarchy.py`
- **Tier 2 (3):** `homeostasis.py`, `blast_radius.py`, `le_chatelier.py`
- **Tier 3 (8):** `spc_monitoring.py`, `process_capability.py`, `burnout_epidemiology.py`, `erlang_coverage.py`, `seismic_detection.py`, `burnout_fire_index.py`, `creep_fatigue.py`, `recovery_distance.py`
- **Time Crystal (1):** `backend/app/scheduling/periodicity/anti_churn.py`
- **Tier 5 (10):** `metastability_detector.py`, `spin_glass_model.py`, `circadian_model.py`, `penrose_efficiency.py`, `anderson_localization.py`, `persistent_homology.py`, `free_energy_scheduler.py`, `keystone_analysis.py`, `zeno_governor.py`, `catastrophe_detector.py`
- **Support:** `service.py`, `tasks.py`, `metrics.py`, `circuit_breaker/`, `frms/`, `retry/`, etc.

### Tests (Comprehensive Coverage)
- `backend/tests/resilience/` - 74+ test files
- Test coverage: Tier 5 alone = 339+ tests, 6601 lines

---

## CONCLUSION

The Residency Scheduler implements a **sophisticated, multi-layered resilience framework** spanning 5 organizational tiers and 33 distinct concepts, backed by 74 Python modules and 8 formal bridge specifications.

**Key Strengths:**
1. ✅ Layered architecture allows incremental adoption (Tier 1 → Tier 2 → Tier 3 → Exotic)
2. ✅ Cross-disciplinary approach captures multi-faceted nature of burnout
3. ✅ Bridge pattern prevents spaghetti integration logic
4. ✅ Comprehensive test coverage (339+ tests)
5. ✅ Hysteresis prevents alert oscillation
6. ✅ Modular design enables selective enabling/disabling

**Areas for Documentation Enhancement:**
1. ⚠️ Integration guide (how Tier 1-2-3 work TOGETHER)
2. ⚠️ Failure mode analysis (what breaks if X fails?)
3. ⚠️ Override governance (who can override? when? for how long?)
4. ⚠️ Performance budget (memory, compute cost per tier)

**Next Steps:**
- Verify all 74 modules properly exported in `__init__.py`
- Audit bridge implementations for hysteresis completeness
- Performance test full health check under load
- Develop admin UI for resilience dashboard
- Document transition scenarios (rapid defense level changes)

**Deliverable Location:**
`/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Scratchpad/OVERNIGHT_BURN/SESSION_7_RESILIENCE/resilience-core-concepts.md`

