# N-1/N-2 Contingency Analysis: Resilience Engineering Deep Dive

**Status**: Complete Reconnaissance + Analysis
**Session**: 7 (OVERNIGHT_BURN)
**G2 Agent**: RECON (Search Party)
**Generated**: 2025-12-30

---

## Table of Contents

1. [Concept Explanation](#concept-explanation)
2. [Power Grid Analogy](#power-grid-analogy)
3. [Calculation Methodology](#calculation-methodology)
4. [Response Procedures](#response-procedures)
5. [Implementation Architecture](#implementation-architecture)
6. [Integration with Resilience Framework](#integration-with-resilience-framework)

---

## Concept Explanation

### What Is N-1/N-2 Contingency Analysis?

**N-1 Contingency Analysis** answers: _"Can the system survive the loss of any single component?"_

**N-2 Contingency Analysis** answers: _"Can the system survive the loss of any two components simultaneously?"_

These concepts originate from electrical grid reliability engineering, where "N" represents the total number of components (power plants, transmission lines, substations). The North American Electric Reliability Corporation (NERC) mandates that transmission systems maintain:

- **N-1 Contingency**: Any single component can fail without cascading blackouts
- **N-2 Contingency**: Some critical transmission corridors must survive loss of two simultaneous components (e.g., double-circuit transmission towers during severe storms)

### Application to Medical Residency Scheduling

In medical residency scheduling, we replace electrical components with **faculty members** and apply the same reliability logic:

- **Component = Faculty Member**: Each faculty member is a "resource" in the scheduling network
- **Failure = Absence**: Illness, departure, emergency leave, family crisis
- **Cascade = Burnout Contagion**: One faculty member's absence increases workload on others, potentially triggering additional absences

### Core Vulnerability Types

#### 1. **Single Points of Failure (N-1 Vulnerabilities)**

```
Vulnerability Type          | Impact
----------------------------+------------------------------------
Sole Provider               | Only person qualified for critical duty
High Workload              | Loss causes immediate undercoverage
Unique Credential          | Special qualification/certification
Irreplaceable Relationship | Critical team dynamic (e.g., senior PGY)
```

**Example**: Dr. Smith is the only faculty qualified to supervise Level 2 procedures in a rural clinic. Her absence creates immediate risk.

#### 2. **Dangerous Pairs (N-2 Vulnerabilities)**

Two faculty members whose **simultaneous loss** creates undercoverage or regulatory violation.

```
Dangerous Pair Type        | Scenario
---------------------------+----------------------------------------
Overlapping Coverage       | Both cover same rare specialty
Skill Dependency           | Second person depends on first's backup
Zone Concentration         | Both assigned to critical geographic zone
Backup Loss               | Loss of faculty who was covering for primary
```

**Example**: Dr. A covers Trauma + General Surgery; Dr. B covers Emergency Medicine + Trauma. If both absent, Trauma has zero coverage.

#### 3. **Cascade Vulnerabilities**

Primary failure triggers secondary failures through:

- **Load Redistribution**: Remaining faculty overloaded (burnout/departure)
- **Skill Gaps**: Remaining faculty lack qualifications for uncovered duties
- **Morale Impact**: Team loses key mentor/leader
- **System Instability**: Multiple failures occur within short time window

---

## Power Grid Analogy

### Electrical Grid N-1/N-2 Concept

#### The 2003 Northeast Blackout (Classic Case Study)

On August 14, 2003, a cascading blackout affected 55 million people across northeastern North America. Root cause analysis revealed:

```
1. Initial Failure: Single transmission line in Ohio trips due to vegetation contact
2. Load Redistribution: Power diverts to nearby lines, overloading them
3. Cascade: Three more lines trip from overload
4. Uncontrolled Shutdown: Protection systems overwhelm grid operators
5. Result: 55 MW of generation off-line, 21,000 MW of demand lost

Timeline: Initial failure to total collapse = ~15 minutes
```

**NERC Response**: Mandate N-1 contingency analysis. Every transmission pathway must handle loss of any single element without cascading outages.

### Why This Applies to Medical Scheduling

```
ELECTRICAL GRID              |  MEDICAL SCHEDULING
------------------------------------+------------------------------------
Power Plant Failure          |  Faculty Absence (illness, departure)
Transmission Line Overload   |  Faculty Workload Exceeds Burnout Point
Cascading Outages            |  Contagion: Team members also leave
Blackout (Total Collapse)    |  Schedule Collapse (unsafe staffing)
Recovery Time: Hours to Days |  Recovery Time: Days to Months
Cost: Billions in damages    |  Cost: Patient safety, resident wellbeing
```

### The Cascade Failure Anatomy (from Power Grid):

```
Stage 1: Initial Failure
├─ Component exceeds capacity or fails
├─ Load redistributes to neighbors
└─ Stress level increases

Stage 2: Secondary Failures
├─ Neighboring components overload
├─ Protection systems trip components offline
├─ More load redistributes
└─ Stress increases further

Stage 3: Accelerating Collapse
├─ Each failure triggers more failures
├─ Cascades across geographic zones
├─ Protection systems can't keep pace
└─ Collapse becomes inevitable

Stage 4: Total System Collapse
├─ Blackout (electrical grid)
├─ Schedule collapse (medical scheduling)
├─ System requires hours/days to stabilize
└─ Recovery measured in economic/patient harm
```

### Key Insight: The Overload Threshold

Electrical grids and medical teams have similar properties:

```
Utilization (%) | Status           | Safety Margin | Years to Failure
                |                  |               |
< 70%          | Normal           | 30%           | Indefinite
70-80%         | Optimal          | 20%           | Decades
80-85%         | Approaching Limit | 15%           | Years
85-90%         | Dangerous        | 10%           | Months
90-95%         | Critical         | 5%            | Weeks
> 95%          | Phase Transition | -5%           | Days/Hours
```

**Phase Transition**: At 85-95% utilization, small additional load causes disproportionate impact. Like a phase change in materials (water → steam), the system shifts to a new, unstable mode.

---

## Calculation Methodology

### N-1 Analysis Algorithm

**Input**: Faculty list, blocks, current assignments, coverage requirements

**Output**: Vulnerability list (sorted by severity)

```python
Algorithm: Analyze N-1 Vulnerabilities

For each faculty member F:
    1. Create assignment state without F
    2. For each block B where F has assignment:
        a. Count remaining coverage (other faculty assigned to B)
        b. Compare against coverage_requirement[B]
        c. If remaining < required:
            - Mark B as "affected"
            - If remaining == 0:
              - Mark as "uncovered" (CRITICAL)

    3. Categorize by severity:
        CRITICAL:  F is sole provider for ≥1 block OR
                   ≥20% of blocks become undercovered
        HIGH:      ≥10% of blocks OR >5 blocks affected
        MEDIUM:    5-10% of blocks affected
        LOW:       <5% of blocks affected

    4. Add Vulnerability(F, severity, affected_blocks)

Output: Vulnerabilities sorted by (severity, affected_blocks DESC)
```

### N-2 Analysis Algorithm

**Input**: Faculty list, current assignments, N-1 vulnerabilities

**Optimization**: Only test pairs involving "critical" or "high" faculty from N-1 (reduces O(n²) to O(n·k) where k ≈ 5-10)

```python
Algorithm: Analyze N-2 Fatal Pairs

1. Extract critical_faculty from N-1 analysis:
   critical_ids = {f.id for f in vulnerabilities if severity in (CRITICAL, HIGH)}

2. If |critical_ids| < 2:
   Use top-5 faculty by workload as proxy

3. For each pair (F1, F2) in critical_faculty:
    a. Create assignment state without F1 and F2
    b. Collect blocks where at least one of (F1, F2) was assigned
    c. For each such block:
        - Count remaining coverage
        - If remaining < required:
          - Mark as "uncoverable"

    d. If uncoverable blocks > 0:
        Add FatalPair(F1, F2, uncovered_count, affected_services)

4. Sort by uncoverable_blocks DESC

Output: Fatal pairs list
```

### Centrality Scoring

Measures how "important" each faculty member is to overall system resilience.

```python
Algorithm: Calculate Centrality Score

For each faculty member F:
    services_covered = count of services F can provide
    unique_coverage = count of services where F is sole provider
    replacement_difficulty = 1 / (1 + avg_alternatives)
    workload_share = F's assignments / total assignments

    # Weighted combination
    score = (
        0.30 * (services_covered / total_services) +
        0.30 * (unique_coverage / total_services) +
        0.20 * replacement_difficulty +
        0.20 * workload_share
    )

Output: Centrality scores sorted DESC (higher = more critical)
```

**NetworkX Enhancement** (if available):

```python
Additional Metrics (via NetworkX graph analysis):
- Betweenness Centrality:  How often faculty is on "shortest path" between others
- Degree Centrality:        Direct connection count
- Eigenvector Centrality:   Importance from connections to important people
- PageRank:                 Google's algorithm applied to scheduling network
```

### Cascade Simulation

Models how initial failure propagates through system.

```python
Algorithm: Simulate Cascade Failure

Input: initial_failures (list of faculty IDs), max_utilization=0.80

state = {
    active_faculty: all faculty except initial_failures,
    failed_ids: initial_failures,
    total_load: sum(workload[f] for f in initial_failures),
    step: 0
}

While remaining_capacity > 0 and step < MAX_STEPS:
    step += 1

    1. Redistribute load:
       avg_load = total_load / len(active_faculty)

    2. Find newly overloaded faculty:
       new_failures = [
           f for f in active_faculty
           if (base_load[f] + avg_load) > (base_load[f] / max_utilization) * 1.2
       ]
       # 1.2 = overload threshold (120% of capacity)

    3. Remove newly failed faculty:
       for f in new_failures:
           failed_ids.add(f)
           total_load += base_load[f]
           active_faculty.remove(f)

    4. Record cascade_step:
       {step, failed_faculty: new_failures, remaining: len(active_faculty)}

Output: CascadeSimulation(
    initial_failures,
    cascade_steps,
    total_failures,
    final_coverage,
    is_catastrophic
)
```

### Phase Transition Detection

Identifies when system is at risk of sudden shift to chaotic/unstable state.

```python
Algorithm: Detect Phase Transition Risk

indicators = []

1. Check utilization thresholds:
   if utilization > 95%: indicators.add("Utilization > 95% (CRITICAL zone)")
   elif utilization > 90%: indicators.add("Utilization > 90% (approaching critical)")
   elif utilization > 85%: indicators.add("Utilization > 85% (elevated risk)")

2. Check vulnerability count:
   critical_count = count(v for v in vulnerabilities if v.severity == CRITICAL)
   if critical_count >= 3: indicators.add("Multiple critical dependencies")

3. Check fatal pairs:
   if len(fatal_pairs) >= 5: indicators.add("System fragility (many fatal pairs)")

4. Determine risk level:
   if len(indicators) >= 3: risk = CRITICAL
   elif len(indicators) >= 2: risk = HIGH
   elif len(indicators) >= 1: risk = MEDIUM
   else: risk = LOW

Output: (risk_level, indicators_list)
```

---

## Response Procedures

### Red Light / Green Light Decision Framework

```
UTILIZATION          STATUS              REQUIRED ACTIONS
─────────────────────────────────────────────────────────────
< 75%               GREEN               ✓ Routine operations
                                        ✓ Standard scheduling

75-85%              YELLOW              ⚠ Enhanced monitoring
                                        ⚠ Cross-training initiatives
                                        ⚠ Contingency review

85-90%              ORANGE              🔴 Active intervention
                                        🔴 Reduce new commitments
                                        🔴 Activate backup plans
                                        🔴 Increase oversight

90-95%              RED                 🚨 Emergency procedures
                                        🚨 Halt discretionary assignments
                                        🚨 Activate backup faculty
                                        🚨 Daily reporting

> 95%               BLACK               ⛔ Phase transition imminent
                                        ⛔ Deploy fallback schedule
                                        ⛔ Restrict to essential duties
                                        ⛔ Intensive monitoring
```

### N-1 Vulnerability Response

**When N-1 Analysis shows Critical or High Vulnerabilities:**

#### Step 1: Immediate Assessment (Same Day)

```
1. Confirm the finding:
   - Validate coverage calculations
   - Check for recently added assignments
   - Verify absence patterns

2. Identify vulnerable faculty:
   - Who is sole provider?
   - What duties are at risk?
   - What's the timeline?

3. Assess backup availability:
   - Who can cover? (credentialing?)
   - Capacity available?
   - Travel/logistics feasible?
```

#### Step 2: Tactical Response (Days 1-5)

```
Priority 1 - Sole Provider Backup:
  □ Cross-train designated backup for critical duties
  □ Create contingency assignment plan
  □ Brief backup on protocols
  □ Test backup's readiness with simulation

Priority 2 - Load Reduction:
  □ Redistribute workload to underutilized faculty
  □ Defer non-critical assignments
  □ Extend rotation lengths to reduce churn

Priority 3 - Coverage Augmentation:
  □ Recruit external coverage (locum, retired faculty)
  □ Adjust block assignments to increase redundancy
  □ Implement "buddy" coverage model
```

#### Step 3: Strategic Response (Weeks 1-4)

```
Long-term Mitigation:
  □ Hire additional faculty (if budget permits)
  □ Formal cross-training program
  □ Credential development for underqualified staff
  □ Schedule design optimization

Policy Changes:
  □ Require ≥2 qualified faculty per critical duty
  □ Stagger leave to prevent simultaneous absences
  □ Establish coverage baselines
  □ Regular contingency drills
```

### N-2 Fatal Pair Response

**When N-2 Analysis shows Fatal Pairs (system fails with loss of pair):**

#### Step 1: Pair Identification

```
For each fatal pair (F1, F2):
  - What duties are uncovered?
  - What's the probability of simultaneous loss?
  - Can this be mitigated?

Risk = Severity × Probability
  CRITICAL: Both are sole providers for same duty
  HIGH:     Simultaneous loss > 20% coverage loss
  MEDIUM:   Simultaneous loss breaks 1-2 regulations
  LOW:      Impact recoverable within 48 hours
```

#### Step 2: Separation Strategy

**Goal**: Prevent simultaneous loss of critical pairs

```
Method 1 - Schedule Separation:
  □ Ensure F1 and F2 never off on same day
  □ Stagger vacation/conference schedules
  □ Cross-check when approving leave requests

Method 2 - Skill Redundancy:
  □ Train third faculty member on F1's unique skills
  □ Train backup on F2's responsibilities
  □ Reduce dependency on the pair

Method 3 - Duty Decoupling:
  □ If F1+F2 cover overlapping services:
     - Add third provider for overlap service
     - Redistribute duties to other faculty
     - Create separate coverage paths
```

#### Step 3: Monitoring

```
Weekly Checks:
  □ Verify leave schedules prevent fatal pair absence
  □ Check cross-training progress
  □ Monitor utilization of pair members

Incident Response:
  □ If pair members unexpectedly both unavailable:
     - Activate emergency schedule
     - Call in backup faculty
     - Escalate to leadership
     - Brief all stakeholders
```

### Cascade Failure Response

**When Cascade Simulation shows Catastrophic Collapse Probability:**

#### Step 1: Immediate Action (Hours)

```
IF cascade_simulation.is_catastrophic:
    □ Deploy emergency schedule (pre-computed)
    □ Activate 24/7 command center
    □ Call in all available backup faculty
    □ Restrict to essential duties only
    □ Hourly status updates to leadership
```

#### Step 2: Stabilization (Days 1-3)

```
1. Reduce utilization immediately:
   - Cancel non-urgent clinic sessions
   - Defer elective procedures
   - Reduce call frequency where possible

2. Augment capacity:
   - Hire emergency locum tenens
   - Activate retired faculty recall
   - Request external institutional support

3. Support affected faculty:
   - Offer counseling/mental health services
   - Reduce non-clinical duties
   - Provide extra breaks/time off

4. Communication:
   - Daily briefings to faculty
   - Transparent reporting to hospital leadership
   - Update patient communication if needed
```

#### Step 3: Recovery (Weeks 1-4)

```
Post-Crisis Analysis:
  □ Root cause analysis (what triggered initial failure?)
  □ Lessons learned documentation
  □ Identify vulnerabilities exposed

System Hardening:
  □ Update contingency plans based on real incident
  □ Increase baseline staffing if needed
  □ Implement identified process improvements

Resilience Enhancement:
  □ Cross-training accelerated
  □ Backup faculty expanded
  □ Schedule redesigned for better robustness
```

---

## Implementation Architecture

### Code Location Map

```
backend/app/
├── resilience/
│   ├── contingency.py              # N-1/N-2 analyzer (core algorithm)
│   ├── simulation/
│   │   └── n2_scenario.py          # N-2 scenario testing
│   ├── cascade_detector.py         # Cascade failure simulator
│   ├── metrics.py                  # Centrality scoring
│   └── unified_critical_index.py   # Aggregated health score
│
├── services/resilience/
│   ├── contingency.py              # ContingencyService (production wrapper)
│   └── homeostasis.py              # Health monitoring service
│
└── api/routes/
    └── resilience.py               # API endpoints for contingency analysis

backend/tests/
├── services/
│   └── test_contingency_service.py # 40+ test cases
├── resilience/
│   └── test_resilience_components.py
└── scenarios/
    └── resilience_scenarios.py     # End-to-end test scenarios
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Database (Faculty, Blocks, Assignments)                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ ContingencyService._load_data()                              │
│ - Fetch faculty members                                      │
│ - Fetch schedule blocks                                      │
│ - Fetch assignments with eager loading                       │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Build Lookup Tables (O(n) pass)                              │
│ - assignments_by_faculty: faculty_id → [assignments]         │
│ - assignments_by_block: block_id → [assignments]             │
│ - faculty_assignment_count: faculty_id → count               │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
    N-1 Analysis      N-2 Analysis     Centrality
    ┌──────────┐      ┌──────────┐     ┌──────────┐
    │Simulate  │      │Test all  │     │Calculate │
    │each      │      │critical  │     │network   │
    │faculty   │      │pairs     │     │importance│
    │loss      │      │loss      │     │          │
    └──────────┘      └──────────┘     └──────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase Transition Detection                                   │
│ - Utilization check                                          │
│ - Vulnerability count analysis                               │
│ - Fatal pair assessment                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ ContingencyAnalysisResult                                    │
│ - n1_vulnerabilities: list[VulnerabilityInfo]                │
│ - n2_fatal_pairs: list[FatalPairInfo]                        │
│ - centrality_scores: list[CentralityInfo]                    │
│ - phase_transition_risk: str                                 │
│ - recommended_actions: list[str]                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ API Response / Celery Task Notification                      │
│ - HTTP endpoint: /api/resilience/contingency                 │
│ - Background task: celery beat (every 24 hours)              │
│ - Alerts if critical vulnerabilities detected                │
└─────────────────────────────────────────────────────────────┘
```

### Performance Optimization

**N-1 Analysis**: O(f × b) where f = faculty, b = blocks
- With lookups: O(f × a) where a = avg assignments per faculty
- Typical: 50 faculty × 5 assignments = 250 operations

**N-2 Analysis**: O(p²) pairs, but optimized:
- Only analyzes pairs involving critical/high faculty (~5-10)
- Reduces to O(5-10 choose 2) = 10-45 pairs analyzed
- Each pair: O(b) block checks = ~45 × 365 = ~16,000 operations

**Total Typical Runtime**: 50-200ms for full analysis on moderate schedules

### Caching Strategy

```
_lookup_cache: {
    "faculty:2025-01": {
        "assignments_by_faculty": {...},
        "block_assignments_count": {...}
    }
}

_analysis_cache: {
    "contingency:2025-01-to-02": <ContingencyAnalysisResult>
}

Cache invalidation: On assignment changes, clear relevant cache keys
```

---

## Integration with Resilience Framework

### Position in Resilience Tier 1

The resilience framework has 5 tiers of concepts:

```
TIER 1 - CORE CONCEPTS (Foundational - Used Everywhere)
├─ 80% Utilization Threshold        ← Works with N-1/N-2
├─ N-1/N-2 Contingency             ← THIS MODULE
├─ Defense in Depth                ← Uses N-1/N-2 results
├─ Static Stability                ← Creates backups from N-1/N-2 insights
└─ Sacrifice Hierarchy             ← Prioritizes by centrality scores

TIER 2 - STRATEGIC CONCEPTS (Advanced)
├─ Homeostasis (biological feedback)
├─ Blast Radius Isolation (AWS zones)
└─ Le Chatelier's Principle (equilibrium shifts)

TIER 3+ - CROSS-DISCIPLINARY (Specialized)
├─ SPC Monitoring
├─ Process Capability
├─ Burnout Epidemiology
├─ Erlang Coverage
├─ Seismic Detection
├─ Burnout Fire Index
├─ Creep/Fatigue
└─ Recovery Distance
```

### How N-1/N-2 Feeds Other Modules

#### 1. Defense in Depth (Layers 1-5)

```
Layer 1: Prevent (Detection & Monitoring)
  └─ N-1 analysis identifies vulnerabilities before they fail

Layer 2: Detect (Real-time Monitoring)
  └─ Cascade simulation detects when system crosses thresholds

Layer 3: Isolate (Blast Radius)
  └─ Fatal pairs indicate which failures would propagate

Layer 4: Respond (Emergency Procedures)
  └─ Recommendations guide immediate actions

Layer 5: Recover (Fallback Plans)
  └─ Pre-computed schedules from N-1 analysis
```

#### 2. Static Stability (Fallback Schedules)

N-1 analysis identifies what "could fail". Static stability creates backup schedules:

```
Primary Schedule Analysis:
  ├─ Run N-1: Identify vulnerabilities
  ├─ For each vulnerability:
  │   └─ Create modified schedule without that faculty
  └─ Store these as fallback schedules

Deployment:
  If faculty suddenly unavailable:
  └─ Use pre-computed fallback schedule (instant activation)
```

#### 3. Homeostasis (Feedback Loops)

N-1/N-2 results feed into feedback control:

```
Feedback Loop:
  1. Contingency analysis → vulnerabilities detected
  2. System adjusts → increases redundancy/training
  3. Next iteration → vulnerabilities reduce
  4. System stabilizes → homeostasis achieved
```

#### 4. Erlang Coverage (Optimal Staffing)

N-1/N-2 identifies coverage requirements; Erlang-C calculates staffing:

```
Input from N-1/N-2:
  ├─ How many faculty needed per specialty?
  └─ What's the failure rate if understaffed?

Erlang-C Calculation:
  ├─ Target service level (e.g., 95%)
  ├─ Call arrival rate
  └─ Output: Exact staffing needed
```

#### 5. Burnout Epidemiology (Contagion Modeling)

Cascade failure simulations predict burnout spread:

```
Epidemic Model (SIR):
  ├─ S (Susceptible): Faculty with normal stress levels
  ├─ I (Infected): Faculty experiencing burnout
  └─ R (Recovered): Faculty who recovered or left

Connection to N-1/N-2:
  ├─ Loss of one faculty (N-1) increases load on others
  ├─ Load increase pushes susceptible → infected
  ├─ Infected faculty may leave (failure)
  └─ Cascade simulation models this spread
```

### Health Check Integration

**Scheduled Task** (Celery Beat):

```python
@celery_app.task(name="resilience.contingency_analysis")
def run_contingency_analysis():
    """Run N-1/N-2 analysis every 24 hours"""

    service = ContingencyService(db)
    result = service.analyze_contingency(
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30)
    )

    # Generate alerts if critical
    if not result.n1_pass:
        alert_leadership(f"N-1 FAILED: {len(result.n1_vulnerabilities)} critical dependencies")

    if not result.n2_pass:
        alert_leadership(f"N-2 FAILED: {len(result.n2_fatal_pairs)} fatal pairs identified")

    if result.phase_transition_risk in ("high", "critical"):
        alert_leadership(f"PHASE TRANSITION RISK: {result.phase_transition_risk}")

    # Store results in database
    store_analysis(result)
```

### API Endpoints

```
GET /api/resilience/contingency?start_date=2025-01-01&end_date=2025-01-31
  └─ Returns full ContingencyAnalysisResult

GET /api/resilience/contingency/faculty/{faculty_id}
  └─ Simulate loss of specific faculty

GET /api/resilience/vulnerabilities
  └─ List all current N-1 vulnerabilities

GET /api/resilience/fatal-pairs
  └─ List all identified N-2 fatal pairs

GET /api/resilience/health
  └─ Quick health check (without full N-2)
```

---

## Key Findings from Codebase

### Strengths

1. **Comprehensive N-1 Analysis**: Tests removal of each faculty, calculates affected blocks, identifies severity levels
2. **Optimized N-2 Analysis**: Only analyzes critical faculty pairs, reduces O(n²) to manageable size
3. **Centrality Metrics**: Uses NetworkX for sophisticated importance scoring (betweenness, pagerank, eigenvector)
4. **Cascade Simulation**: Models how initial failure propagates through load redistribution
5. **Phase Transition Detection**: Identifies when system at risk of sudden collapse
6. **Service Integration**: Proper separation of concerns (controller → service → repository)
7. **Test Coverage**: 40+ test cases covering all scenarios

### Integration Points with Resilience Framework

| Module | Uses N-1/N-2 Output | How |
|--------|-------------------|-----|
| Defense in Depth | YES | Creates layer 1 (detect) via N-1 findings |
| Static Stability | YES | Pre-computes fallback schedules from N-1 results |
| Cascade Detection | YES | Uses cascade_failure simulation directly |
| Unified Critical Index | YES | Incorporates N-1/N-2 status as health metric |
| Circuit Breaker | YES | Trips breaker if N-1 pass = False |
| Homeostasis | YES | Feedback loop adjusts based on contingency results |

### Recommended Daily Workflow

```
Morning (6am):
  ├─ Run N-1/N-2 contingency analysis (batch job)
  ├─ Check for new critical vulnerabilities
  ├─ Review fatal pairs (prevent simultaneous leave)
  └─ Verify fallback schedules are current

Mid-day (12pm):
  ├─ Alert if new vulnerabilities detected
  ├─ Brief leadership on phase transition risk
  └─ Adjust day's assignments if needed

Evening (6pm):
  ├─ Monitor faculty availability
  ├─ Verify backup plans are ready
  └─ Store results for next analysis cycle
```

---

## References

### Source Files (Codebase Location)

- **Core Algorithm**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/resilience/contingency.py` (1008 lines)
- **Service Wrapper**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/services/resilience/contingency.py` (1209 lines)
- **Scenario Testing**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/resilience/simulation/n2_scenario.py` (531 lines)
- **Tests**: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/tests/services/test_contingency_service.py` (835 lines)

### External References

- **NERC Reliability Standards**: [NERC TOP-001-3](https://www.nerc.net/files/standards/pdfs/nerc_top_001-3.pdf) - Transmission Operations Planning
- **2003 Blackout Analysis**: US-Canada Power System Outage Task Force Report
- **Cascade Failures**: "Cascade Control and Defense" by Pourbeik et al. (2006)
- **Power Grid Resilience**: Buldyrev et al., "Catastrophic cascade of failures in interdependent networks" (Nature, 2010)

---

## Glossary

| Term | Definition |
|------|-----------|
| **N-1** | System survives loss of any single component |
| **N-2** | System survives loss of any two components |
| **Contingency** | Unexpected loss of component (failure/absence) |
| **Vulnerability** | Dependency that creates risk if lost |
| **Fatal Pair** | Two components whose simultaneous loss causes system failure |
| **Centrality** | Measure of how critical a component is to system |
| **Cascade** | Failure that triggers additional failures (uncontrolled spread) |
| **Phase Transition** | Sudden shift from stable to unstable system behavior |
| **Utilization** | Percentage of available capacity being used (0-100%) |
| **Overload Threshold** | Utilization level where additional failures become likely |

---

**End of Report**

Generated by G2_RECON (Search Party Operation)
Session 7: OVERNIGHT_BURN - Resilience Engineering Deep Dive
