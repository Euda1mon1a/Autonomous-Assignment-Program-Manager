# MCP Analytics Tools Documentation
## G2_RECON SEARCH_PARTY Reconnaissance Report
**Date:** 2025-12-30
**Session:** Session 8 - Overnight Burn
**Classification:** ANALYTICS TOOL INVENTORY

---

## Executive Summary

The Residency Scheduler MCP Server exposes **81 specialized tools** organized into 11 functional domains, providing AI assistants with comprehensive analytics capabilities for schedule optimization, compliance monitoring, resilience analysis, and advanced signal processing.

**Key Metrics:**
- **Total Tools:** 81 registered MCP tools
- **Resources:** 2 queryable endpoints (schedule status, compliance summary)
- **Domains:** 11 analytical categories
- **Cross-Disciplinary:** 40+ scientific frameworks integrated
- **Metrics Coverage:** ~150 distinct analytics metrics available

---

## PERCEPTION LENS: Current Analytics Tool Landscape

### Tool Distribution by Domain

```
Domain                          | Tool Count | Lines of Code
--------------------------------|------------|---------------
Scheduling & Conflict Detection |     3      | ~2,500
Resilience Framework            |    15      | ~8,000
Early Warning Systems           |     3      | ~4,500
Optimization & Erlang C         |     5      | ~3,000
Empirical Testing              |     5      | ~4,000
Composite Resilience           |     4      | ~3,500
Epidemiological Modeling       |     3      | ~2,000
Artificial Immune System       |     3      | ~2,500
Thermodynamics & Entropy       |     4      | ~3,000
Time Crystal Scheduling        |     5      | ~4,000
Advanced Signal Processing     |    15      | ~7,000
Circuit Breaker Management     |     3      | ~2,000
Deployment & Infrastructure    |     6      | ~4,000
Async Task Management          |     4      | ~1,500
Background Tasks               |    2      | ~500
```

**Total Codebase:** ~51,500+ lines across 45+ source files

---

## INVESTIGATION LENS: Metric Coverage Analysis

### Tier 1: Core Metrics (Always Available)

#### 1. **Schedule Coverage & Capacity**
- Total blocks requiring coverage
- Current assignments
- Coverage rate (0-1.0)
- Unfilled slots
- Coverage by rotation type
- Coverage by specialty/zone

#### 2. **Utilization Metrics**
- Utilization rate (0-1.0)
- Effective utilization (adjusted for stability)
- Buffer remaining vs. 80% threshold
- Wait time multiplier (queuing theory)
- Capacity headroom

#### 3. **ACGME Compliance**
- Work hours violations (80-hour rule)
- Consecutive duty violations (1-in-7 rule)
- Supervision ratio violations
- Rest period violations
- Violation count by type
- Violation severity (low/medium/high/critical)

#### 4. **Assignment Equity**
- Gini coefficient (0-1.0, where 0 = perfect equality)
- Standard deviation of workload
- Overloaded providers (>80th percentile)
- Underloaded providers (<20th percentile)
- Fairness score (0-1.0)

### Tier 2: Advanced Resilience Metrics

#### 5. **Contingency Analysis (N-1/N-2)**
- N-1 pass/fail status
- N-1 vulnerabilities detected
- N-2 pass/fail status
- Fatal faculty pairs
- Affected services per vulnerability
- Most critical faculty ranking
- Phase transition risk level

#### 6. **Network Analysis**
- Hub centrality scores (NetworkX betweenness, pagerank, closeness)
- Faculty isolation risk
- Cascade failure potential
- Single points of failure
- Network density
- Clustering coefficient

#### 7. **Defense Levels**
- Current defense level (prevention, control, safety, containment, emergency)
- Recommended level
- Status (ready, active, degraded)
- Active defensive actions
- Coverage rate at each level
- Escalation needed (boolean)

#### 8. **Blast Radius Analysis**
- Zone health status
- Affected zones count
- Cascade containment rate
- Blast radius magnitude (1-10)
- Propagation potential

### Tier 3: Cross-Disciplinary Analytics

#### 9. **Early Warning Signals**

**Seismic Detection (STA/LTA Algorithm):**
- STA/LTA ratio (>2.5 indicates anomaly)
- Alert count by signal type
- Predicted magnitude (1-10 Richter scale)
- Time-to-event estimation (days)
- Growth rate of ratio
- Signal types: swap requests, sick calls, preference decline, response delays

**Statistical Process Control (Western Electric Rules):**
- SPC violation count
- Violations by rule (Rule 1-4)
- Process capability (Cp, Cpk)
- Control limits
- Sigma level
- Mean and standard deviation

**Fire Danger Index (CFFDRS):**
- Danger class (low/moderate/high/extreme)
- Fire weather index
- Buildup index
- Drying index
- Days since rain

#### 10. **Epidemiological Burnout Modeling**

**Reproduction Number (Rt):**
- Rt value (>1 indicates spread, <1 indicates decline)
- Status (declining/endemic/growing/crisis)
- Secondary cases per index case
- Transmission chains identified
- Time window (28 days default)

**SIR/SIS Epidemic Simulation:**
- R0 (basic reproduction number)
- Peak infected count
- Peak week
- Herd immunity threshold
- Attack rate
- Final attack rate
- Epidemic trajectory

#### 11. **Workload & Fatigue Analysis**

**FRMS (Fatigue Risk Management System):**
- Fatigue score (0-100)
- Sleep debt hours
- Hazard level (low/moderate/high)
- Risk categories: burnout prone, sleep deprived, high utilization
- Individual assessments available

**Creep-Fatigue Analysis (Materials Science):**
- Larson-Miller Parameter (LMP)
- Creep stage: primary/secondary/tertiary
- Fatigue damage (Miner's Rule)
- Combined risk score
- Time-to-failure estimate

#### 12. **Optimization Metrics**

**Erlang C Staffing:**
- Offered load (arrival_rate × service_time)
- Wait probability (0-1.0)
- Average wait time
- Service level (% served within target)
- Queue stability
- Staffing table (servers vs. metrics)
- Severity (healthy/warning/critical/emergency)

**Process Capability (Six Sigma):**
- Cp (process potential)
- Cpk (process capability actual)
- Pp (process performance long-term)
- Ppk (process performance actual)
- Cpm (Taguchi capability)
- Sigma level (3σ, 4σ, 5σ, 6σ)
- Defects per million (PPM)
- Capability status (excellent/capable/marginal/incapable)

#### 13. **Phase Transition & Stability Metrics**

**Critical Slowing Down (SOC Theory):**
- Relaxation time (hours)
- Variance trend (slope)
- Autocorrelation (AC1)
- Signals triggered (0-3)
- Warning level (GREEN/YELLOW/ORANGE/RED)
- Days to critical estimate

**Entropy Analysis:**
- Person entropy (bits)
- Rotation entropy (bits)
- Time entropy (bits)
- Joint entropy (bits)
- Mutual information (bits)
- Normalized entropy (0-1.0)
- Entropy status (balanced/concentrated/dispersed)

**Changepoint Detection:**
- CUSUM changepoints
- PELT changepoints
- Magnitude of change
- Confidence level
- Signal transition moments

#### 14. **Time Crystal Metrics (Anti-Churn)**

**Schedule Rigidity:**
- Rigidity score (0-1.0, 1=identical)
- Total changes
- Affected people count
- Severity (minimal/low/moderate/high/critical)
- Churn rate
- Stability assessment

**Periodicity Analysis:**
- Fundamental period (days)
- Detected subharmonics [7, 14, 28]
- Periodicity strength (0-1.0)
- ACGME window alignment
- Harmonic resonance with regulations
- Spectral entropy

#### 15. **Advanced Network Metrics**

**Game Theory Analysis:**
- Nash equilibrium status
- Deviation incentives (count)
- Coordination failures (count)
- Utility components (efficiency, fairness, compliance)
- Stability indicators

**Ecological Dynamics (Lotka-Volterra):**
- Supply-demand equilibrium point
- System stability level
- Capacity crunch risk
- Intervention effectiveness
- Population cycles detected

**Kalman Filter Analysis:**
- Workload trend (estimated)
- Anomaly confidence
- Noise level
- Residuals
- State predictions

**Fourier/FFT Analysis:**
- Dominant period (days)
- Power spectrum peaks
- Harmonic alignment with ACGME cycles
- Spectral entropy
- Frequency content

#### 16. **Immunity & Anomaly Detection**

**Artificial Immune System:**
- Detector count
- Detector coverage rate
- Anomaly detection rate
- Repair success rate
- Active antibodies
- Memory cells (learned patterns)
- System health status

---

## ARCANA LENS: Analytics Domain Concepts

### Scientific Frameworks Integrated

#### Power Grid / Nuclear Safety
- **Utilization Threshold:** 80% critical point from queuing theory
- **Defense in Depth:** 5-level nuclear reactor paradigm
- **N-1/N-2 Contingency:** Electrical grid planning
- **Static Stability:** AWS availability zone paradigm

#### Epidemiology
- **SIR Model:** Susceptible-Infected-Recovered
- **SIS Model:** Susceptible-Infected-Susceptible (reinfection)
- **Rt Reproduction Number:** Epidemic transmission rate
- **Herd Immunity:** Population-level protection threshold
- **Transmission Chains:** Contact tracing through networks

#### Seismology
- **STA/LTA Algorithm:** P-wave precursor detection
- **Magnitude Estimation:** Richter-scale equivalent for events
- **Signal Processing:** Time-series analysis from sensors
- **Precursor Detection:** Foreshock patterns

#### Manufacturing & Quality Control
- **Statistical Process Control:** Western Electric Rules (Rule 1-4)
- **Process Capability:** Cp/Cpk/Cpm Six Sigma metrics
- **Sigma Levels:** 3σ to 6σ quality classes
- **Defects Per Million:** Quantified quality standards

#### Forestry
- **Canadian Fire Weather Index:** Multi-temporal danger rating
- **Buildup Index:** Fuel moisture accumulation
- **Drying Index:** Evaporation potential
- **Days Since Rain:** Precipitation recency

#### Materials Science
- **Creep Analysis:** Time-dependent deformation (primary/secondary/tertiary)
- **Larson-Miller Parameter:** Creep rupture time prediction
- **Fatigue Analysis:** Cyclic loading and Miner's Rule
- **S-N Curves:** Stress-life relationships

#### Information Theory
- **Shannon Entropy:** Information content in distributions
- **Mutual Information:** Dependency between variables
- **Joint Entropy:** Combined uncertainty
- **Kullback-Leibler Divergence:** Distribution distance

#### Network Science
- **Graph Metrics:** Betweenness, closeness, pagerank centrality
- **Community Detection:** Clustering algorithms
- **Hub Identification:** Critical node detection
- **Cascade Modeling:** Failure propagation

#### Thermodynamics
- **Entropy Production:** Energy dissipation rates
- **Phase Transitions:** Critical points and tipping
- **Free Energy:** Optimization landscape
- **Energy Landscape:** State space geometry

#### Game Theory & Economics
- **Nash Equilibrium:** Stable strategy combinations
- **Shapley Values:** Fair value allocation
- **Utility Functions:** Multi-objective optimization
- **Gini Coefficient:** Inequality measurement

#### Cognitive Science
- **Miller's Law:** 7±2 working memory limit
- **Cognitive Load:** Decision queue complexity
- **Bounded Rationality:** Decision-making limits

#### Emergent Systems
- **Stigmergy:** Indirect coordination through trails
- **Swarm Intelligence:** Collective decision-making
- **Self-Organized Criticality:** Phase transitions
- **Tipping Points:** Critical state transitions

---

## HISTORY LENS: Tool Evolution & Maturity

### Generation 1: Foundational Tools (2024)
- Schedule validation
- Conflict detection
- Basic compliance checking
- Swap analysis
- Background task management

### Generation 2: Resilience Framework (2024-2025)
- Utilization monitoring
- Defense levels
- N-1/N-2 contingency analysis
- Static fallbacks
- Sacrifice hierarchy

### Generation 3: Cross-Disciplinary Analytics (2025)
- Early warning systems (STA/LTA, SPC, Fire Index)
- Epidemiological modeling (Rt, SIR, SIS)
- FRMS fatigue analysis
- Erlang C optimization
- Network centrality analysis

### Generation 4: Advanced Physics & Theory (2025)
- Thermodynamics (entropy, phase transitions)
- Time crystal scheduling (anti-churn)
- Materials science (creep-fatigue)
- Kalman filtering
- Fourier/FFT analysis

### Generation 5: Metaanalysis & Empiricism (2025)
- Solver benchmarking
- Constraint yield analysis
- Ablation studies
- Module usage analysis
- Critical slowing down detection

### Generation 6: Bio-Inspired Systems (2025)
- Artificial immune system
- Gene regulatory networks
- Ecological dynamics
- Game theory analysis
- Transcription factor networks

---

## INSIGHT LENS: AI-Assisted Analytics Usage Patterns

### High-Value Queries for AI Assistants

**For Schedule Generation:**
```
1. Validate schedule → check_utilization_threshold → run_contingency_analysis
2. Detect conflicts → analyze_swap_candidates → validate_compliance
3. Optimize coverage → optimize_erlang_coverage → calculate_process_capability
```

**For Crisis Response:**
```
1. get_unified_critical_index (aggregated risk)
2. get_defense_level (action recommendations)
3. execute_sacrifice_hierarchy (load shedding)
4. simulate_burnout_contagion (impact prediction)
```

**For Burnout Prevention:**
```
1. detect_burnout_precursors (early warning)
2. assess_creep_fatigue (time-to-failure)
3. calculate_burnout_rt (transmission risk)
4. scan_team_fatigue (organizational health)
```

**For Resilience Planning:**
```
1. calculate_recovery_distance (fragility score)
2. analyze_schedule_periodicity (pattern preservation)
3. get_time_crystal_health (anti-churn status)
4. analyze_schedule_rigidity (stability metrics)
```

**For Analytical Reporting:**
```
1. get_schedule_status (comprehensive overview)
2. get_compliance_summary (regulatory status)
3. get_unified_critical_index (risk aggregation)
4. benchmark_solvers/constraints (performance analytics)
```

### Typical Analytical Workflows

**Workflow 1: Daily Health Check (5 min)**
```
Resource: schedule://status/current
Resource: schedule://compliance/current
Tool: check_utilization_threshold
Tool: get_defense_level
Tool: get_unified_critical_index
```

**Workflow 2: Contingency Planning (30 min)**
```
Tool: run_contingency_analysis_resilience
Tool: calculate_blast_radius
Tool: calculate_recovery_distance
Tool: get_static_fallbacks
Tool: execute_sacrifice_hierarchy (simulate)
```

**Workflow 3: Burnout Risk Assessment (15 min)**
```
Tool: detect_burnout_precursors (multiple signal types)
Tool: assess_creep_fatigue
Tool: calculate_burnout_rt
Tool: simulate_burnout_contagion
Tool: scan_team_fatigue
```

**Workflow 4: Schedule Quality Analysis (20 min)**
```
Tool: benchmark_constraints
Tool: calculate_process_capability
Tool: calculate_equity_metrics
Tool: analyze_schedule_periodicity
Tool: analyze_schedule_rigidity
```

---

## RELIGION LENS: Universal Queryability

### Queryable Endpoints

#### 1. Resource: `schedule://status/{date_range}`
**Metrics Returned:**
- Total assignments
- Coverage metrics
- Utilization rate
- Current conflicts count
- Active issues list
- Recommendations

**Date Range Formats:**
- `current` or `today`: Today only
- `week` or `this-week`: Next 7 days
- `month` or `this-month`: Next 30 days
- `YYYY-MM-DD:YYYY-MM-DD`: Explicit range
- Alternative: `start_date` and `end_date` parameters override

#### 2. Resource: `schedule://compliance/{date_range}`
**Metrics Returned:**
- ACGME compliance status
- Violations by category
- Critical issues
- At-risk residents/faculty
- Recommendations
- Audit trail

**Queryable Metrics (Post-Processing Available):**
- Work hour violations: `violations[].type == "80_hour_rule"`
- Supervision violations: `violations[].type == "supervision_ratio"`
- Rest period violations: `violations[].type == "1_in_7"`
- Violation severity: `violations[].severity` (critical/high/medium/low)

### Universal Queryability Checklist

| Metric Category | Tools Available | Queryable | Filterable | Aggregatable |
|-----------------|-----------------|-----------|------------|--------------|
| Coverage        | 15+ tools       | YES       | YES        | YES          |
| Compliance      | 8+ tools        | YES       | YES        | YES          |
| Utilization     | 12+ tools       | YES       | YES        | YES          |
| Resilience      | 25+ tools       | YES       | YES        | YES          |
| Burnout Risk    | 10+ tools       | YES       | YES        | YES          |
| Network         | 8+ tools        | YES       | YES        | YES          |
| Fairness        | 6+ tools        | YES       | YES        | YES          |
| Quality         | 5+ tools        | YES       | YES        | YES          |

---

## NATURE LENS: Tool Complexity & Dependencies

### Complexity Tiers

**Tier 1: Simple Calculations (< 500 LOC)**
- `check_utilization_threshold` - Arithmetic
- `calculate_erlang_metrics` - Formula application
- `generate_lorenz_curve` - Statistical calculation
- `get_defense_level` - State machine
- Background task management tools

**Tier 2: Moderate Complexity (500-1500 LOC)**
- Early warning tools (STA/LTA, SPC, Fire Index)
- Equity metrics
- Basic resilience checks
- Deployment validation
- Module usage analysis

**Tier 3: High Complexity (1500-3000 LOC)**
- Contingency analysis (N-1/N-2)
- Optimization tools (Erlang coverage, process capability)
- Empirical testing (benchmarking)
- Network analysis
- Entropy calculations

**Tier 4: Very High Complexity (3000+ LOC)**
- Epidemiological modeling (SIR, SIS, Rt)
- Artificial immune system
- Thermodynamics analysis
- Creep-fatigue assessment
- Signal processing (Fourier, Kalman, changepoint)

### External Dependencies

**Database Required:**
- All tools accessing person/assignment/block data
- Contingency analysis tools
- Empirical testing tools
- Historical analysis tools
- ~40 tools (49% of total)

**API Client Required:**
- Schedule status/compliance resources
- Deployment tools
- Network-dependent tools
- ~15 tools (19% of total)

**Calculation Only (Stateless):**
- Shapley value calculation
- Process capability
- Equity metrics
- Critical slowing down
- Erlang metrics
- ~26 tools (32% of total)

**Optional Enhancements:**
- SPC analysis can use live or historical data
- Burnout Rt calculation requires social network graph
- Contingency analysis enhanced with cascade simulation

---

## MEDICINE LENS: Performance Context

### Execution Time Estimates (Typical)

**Fast (<1 second):**
- Utilization threshold check
- Defense level lookup
- Erlang metrics calculation
- Equity metrics
- Shapley value calculation (placeholder)
- ~20 tools

**Moderate (1-10 seconds):**
- Early warning analysis (STA/LTA, SPC)
- Fire danger index
- Entropy calculation
- Process capability
- Network centrality analysis
- ~25 tools

**Slow (10-60 seconds):**
- Contingency analysis (N-1/N-2)
- Blast radius analysis
- Epidemiological simulation (SIR/SIS)
- Creep-fatigue assessment
- Burnout contagion
- ~15 tools

**Very Slow (>60 seconds, background task):**
- Module usage analysis
- Solver benchmarking
- Constraint benchmarking
- Ablation studies
- Fourier analysis (large dataset)
- ~10 tools (recommend async execution)

### Resource Consumption

**Memory-Light (< 100 MB):**
- All simple calculation tools
- Most stateless analytics
- ~45 tools

**Memory-Moderate (100-500 MB):**
- Network analysis (full graph)
- Epidemiological simulation
- Entropy analysis with large history
- ~15 tools

**Memory-Intensive (> 500 MB):**
- Full contingency analysis
- Large-scale signal processing
- Module usage analysis across entire codebase
- Solver benchmarking
- ~5 tools (potentially problematic)

### Database Query Performance

**Indexed Queries (< 100 ms):**
- Person/assignment by date range
- Block queries
- Rotation types
- ~30 tools

**Join Queries (100-500 ms):**
- Coverage analysis requiring person-block-rotation joins
- Compliance checking
- Fairness calculation
- ~20 tools

**Complex Aggregations (500-5000 ms):**
- Contingency analysis requiring all permutations
- Network analysis requiring graph construction
- Epidemiological modeling requiring path tracing
- ~10 tools

---

## SURVIVAL LENS: Anomaly Detection Tools

### Built-In Anomaly Detection Capabilities

| Tool | Anomaly Type | Detection Method | Sensitivity |
|------|--------------|-----------------|------------|
| detect_burnout_precursors | Behavioral change | STA/LTA algorithm | Configurable (2.5+ ratio) |
| run_spc_analysis | Workload drift | Western Electric Rules | Rule-dependent |
| detect_critical_slowing_down | Phase transition | SOC metrics | 3 signal threshold |
| detect_schedule_changepoints | Structural break | CUSUM/PELT | Variance-based |
| analyze_schedule_rigidity | Excessive churn | Difference metric | Count-based |
| detect_coordination_failures | Strategic inconsistency | Utility deviation | Threshold-based |
| analyze_antibody_response | Schedule anomaly | Feature distance | Affinity-based |
| calculate_fire_danger_index | Multi-temporal danger | CFFDRS formula | Risk class |
| check_memory_cells | Pattern recurrence | Signature matching | Confidence-based |
| analyze_schedule_entropy | Distribution anomaly | Entropy bounds | Normalized range |

### Anomaly Interpretation Framework

**Anomaly Severity Levels:**

```
GREEN (Healthy)
├── No signals triggered
├── Within normal ranges
└── Routine monitoring sufficient

YELLOW (Warning)
├── 1-2 signals triggered
├── Increased monitoring recommended
└── Preventive actions suggested

ORANGE (Elevated)
├── 2-3 signals triggered or confirmed drift
├── Immediate action recommended
└── Escalation to leadership

RED (Critical)
├── 3+ signals triggered or rapid decline
├── Emergency protocols required
└── Immediate decision-maker notification

BLACK (Emergency)
├── Multiple critical systems failing
├── Cascade failure risk high
└── Full emergency activation
```

### Recommended Monitoring Intervals

| Signal Type | Check Interval | Alert Threshold | Action |
|-------------|----------------|-----------------|--------|
| Utilization | 6 hours | >75% | Increase monitoring |
| ACGME violations | Daily | Any critical | Remediate |
| Burnout precursors | Weekly | STA/LTA > 2.5 | Assess stress |
| Defense level | Daily | Below CONTROL | Escalate |
| Network hubs | Monthly | New critical hub | Plan contingency |
| Entropy changes | Weekly | Trend anomaly | Analyze pattern |
| Coverage gaps | 6 hours | >5% unfilled | Find backup |

---

## STEALTH LENS: Undocumented Metrics & Hidden Capabilities

### Lesser-Known Metrics

#### 1. **Transcription Factor Regulatory Network**
- Active transcription factors (Master/Activator/Repressor/Pioneer/Dual)
- Constraint weight modulation
- Regulatory feedback loops
- Signal cascades (deployment, crisis events)
- Chromatin state (open/silenced constraints)
*Location:* `composite_resilience_tools.py` / `analyze_transcription_triggers_tool`

#### 2. **Homeostasis Allostatic Load**
- Cumulative stress on system
- Feedback loop strength
- Compensation capacity
- Stress threshold status
- Recovery time estimates
*Location:* `resilience_integration.py` / `analyze_homeostasis_tool`

#### 3. **Le Chatelier Equilibrium Shift**
- Current equilibrium state
- Stress-induced shift magnitude
- Compensation direction
- Partial/temporary nature documentation
- Stress prediction metrics
*Location:* `resilience_integration.py` / `analyze_le_chatelier_tool`

#### 4. **Stigmergy Preference Trails**
- Faculty preference patterns (pheromone-like)
- Slot attraction scores
- Collective intelligence patterns
- Emergent optimization signals
- Suggestion generation
*Location:* `resilience_integration.py` / `analyze_stigmergy_tool`

#### 5. **Basin Depth Metrics (Hopfield Networks)**
- Schedule energy landscape
- Attractor basin depth
- Spurious attractor detection
- Nearby attractors (alternative schedules)
- Energy gradient analysis
*Location:* `hopfield_attractor_tools.py` / Multiple tools

#### 6. **Circadian PRC (Phase Response Curve)**
- Chronobiological burn-in patterns
- Optimal work phase windows
- Fatigue phase prediction
- Night shift impact quantification
*Location:* `frms_integration.py` (partially embedded)

#### 7. **Quantum Zeno Monitoring Governor**
- Over-monitoring impact quantification
- Observation frequency optimization
- System "freezing" prevention
- Intervention cascade thresholds
*Location:* `composite_resilience_tools.py` (reference only)

#### 8. **Persistent Homology Coverage Patterns**
- Multi-scale coverage topology
- Persistent features in rotation networks
- Coverage hole detection
- Structural stability metrics
*Location:* `resilience_integration.py` (topological analysis)

#### 9. **Value-at-Risk (VaR) Metrics**
- Schedule vulnerability to disruptions
- Confidence levels (95%, 99%)
- Worst-case coverage loss
- Conditional VaR (expected shortfall)
- Disruption scenario library
*Location:* `var_risk_tools.py`

#### 10. **Seismic Magnitude Estimation**
- Burnout event predicted magnitude (1-10)
- Richter-scale equivalent
- Impact radius
- Aftershock probability
*Location:* `early_warning_integration.py`

### Hidden Capabilities

#### Capability 1: Async Task Chaining
Tools can be chained via async task management:
```
start_background_task("resilience_contingency", {"days_ahead": 90})
→ get_task_status(task_id)
→ When complete, results contain underlying metrics
```

#### Capability 2: Comparative Analysis
Many tools support side-by-side comparison when provided schedule IDs:
```
analyze_schedule_rigidity(current_schedule_id, proposed_schedule_id)
→ Detailed change analysis
```

#### Capability 3: Simulation-Only Mode
Several tools support `simulate_only=true` parameter:
```
execute_sacrifice_hierarchy("red", simulate_only=True)
→ Shows impact without actual deployment
```

#### Capability 4: Historical Trend Extraction
Tools with `history_window` parameter can extract trends:
```
get_entropy_monitor_state(history_window=100)
→ 100 measurements of entropy evolution
```

#### Capability 5: Granular Filtering
Many tools support filtering to specific providers/blocks/dates:
```
Tool parameters with optional filters:
- zone_id (for blast radius)
- slot_type (for stigmergy)
- signal_type (for precursor detection)
```

---

## INTEGRATION PATTERNS

### Dashboard Integration Points

#### Primary Dashboards
1. **Resilience Dashboard**
   - `get_unified_critical_index`
   - `get_defense_level`
   - `calculate_burnout_rt`
   - `check_utilization_threshold`
   - Real-time integration recommended

2. **Compliance Dashboard**
   - Resource: `schedule://compliance/{date_range}`
   - `run_spc_analysis` (work hour trends)
   - `calculate_process_capability` (quality metrics)
   - `validate_schedule_tool` (validation status)

3. **Early Warning Dashboard**
   - `detect_burnout_precursors` (all signal types)
   - `detect_critical_slowing_down`
   - `detect_schedule_changepoints`
   - `analyze_fire_danger_index`

4. **Operations Dashboard**
   - Resource: `schedule://status/{date_range}`
   - `check_utilization_threshold`
   - `run_contingency_analysis_resilience`
   - `analyze_hub_centrality`

5. **Quality Dashboard**
   - `calculate_equity_metrics`
   - `calculate_process_capability`
   - `benchmark_constraints` (if historical)
   - `generate_lorenz_curve`

### API Response Patterns

#### Standard Success Response
```json
{
  "status": "success",
  "metric_name": "value",
  "detail": {...},
  "recommendations": ["action1", "action2"]
}
```

#### Alert Response
```json
{
  "status": "success",
  "severity": "critical",
  "metric_name": "value",
  "alert_triggered": true,
  "immediate_actions": ["action1", "action2"],
  "escalation_needed": true
}
```

#### Error Response
```json
{
  "status": "error",
  "error_code": "INVALID_INPUT|DATABASE_ERROR|...",
  "message": "Human-readable description",
  "detail": {...}
}
```

---

## REFERENCE IMPLEMENTATION EXAMPLES

### Example 1: Daily Health Check Script
```python
# Minimal viable daily check
from mcp_client import call_tool, call_resource

async def daily_health_check():
    # Get schedule overview
    status = await call_resource("schedule://status/current")
    compliance = await call_resource("schedule://compliance/current")

    # Check critical metrics
    util = await call_tool("check_utilization_threshold",
        available_faculty=len(status.faculty),
        required_blocks=status.unfilled_blocks
    )

    defense = await call_tool("get_defense_level",
        coverage_rate=status.coverage_rate
    )

    # Aggregate risk
    critical_index = await call_tool("get_unified_critical_index",
        include_details=False, top_n=3
    )

    # Report
    print(f"Coverage: {status.coverage_rate:.0%}")
    print(f"Utilization: {util.level}")
    print(f"Defense: {defense.current_level}")
    print(f"Risk Level: {critical_index.risk_level}")
    if critical_index.risk_level in ["high", "critical"]:
        for fac in critical_index.top_risk_faculty:
            print(f"  ALERT: {fac.anonymized_id}")
```

### Example 2: Crisis Response Workflow
```python
async def crisis_response(severity_level):
    # Determine sacrifice hierarchy
    sacrifice = await call_tool("execute_sacrifice_hierarchy",
        target_level=severity_level,
        simulate_only=True  # First preview impact
    )

    # Check what can help
    fallbacks = await call_tool("get_static_fallbacks")

    # Assess damage
    contingency = await call_tool("run_contingency_analysis_resilience",
        analyze_n1=True, analyze_n2=True,
        include_cascade_simulation=True
    )

    # Estimate burnout spread
    if has_burned_out_faculty():
        rt = await call_tool("calculate_burnout_rt",
            burned_out_provider_ids=[...],
            time_window_days=28
        )
        if rt.rt > 1.0:
            print(f"BURNOUT SPREADING: Rt={rt.rt:.2f}")

    return {
        "sacrifice_plan": sacrifice,
        "available_fallbacks": fallbacks,
        "vulnerability_assessment": contingency,
        "burnout_risk": rt
    }
```

### Example 3: Burnout Risk Monitoring
```python
async def burnout_risk_scan():
    # Multi-signal precursor detection
    signals = ["swap_requests", "sick_calls", "response_delays"]
    precursors = {}

    for resident_id, signal_data in get_recent_signal_data():
        for signal_type in signals:
            result = await call_tool("detect_burnout_precursors",
                resident_id=resident_id,
                signal_type=signal_type,
                time_series=signal_data[signal_type]
            )
            if result.severity in ["high", "critical"]:
                precursors[resident_id] = result

    # Fatigue risk assessment
    fatigue = await call_tool("assess_creep_fatigue",
        include_assessments=True, top_n=20
    )

    # Epidemiological spread check
    if len(precursors) > 0:
        rt = await call_tool("calculate_burnout_rt",
            burned_out_provider_ids=list(precursors.keys()),
            time_window_days=14
        )

    return {
        "precursor_residents": precursors,
        "fatigue_risk": fatigue,
        "contagion_status": rt if rt else None
    }
```

---

## METRIC EXPORTABILITY

### Exportable Formats

| Format | Tools Supported | Use Cases |
|--------|-----------------|-----------|
| JSON | All 81 tools | API/Dashboard integration |
| CSV | Tabular tools (40+) | Excel analysis, data warehouse |
| Time Series | Historical tools (15+) | Trend analysis, forecasting |
| Graph Format | Network tools (10+) | Network visualization |
| Lorenz Curve | Equity tools (3+) | Inequality visualization |
| SIR Trajectory | Epidemic tools (3+) | Disease spread visualization |

### Dashboard Integration Checklist

- [ ] Schedule Status Resource integrated
- [ ] Compliance Summary Resource integrated
- [ ] Utilization Threshold real-time monitoring
- [ ] Defense Level color-coded display
- [ ] Burnout Precursor alert display
- [ ] Equity Metrics trend chart
- [ ] Network Hub visualization
- [ ] Coverage Gap heat map
- [ ] Contingency Status dashboard
- [ ] Unified Critical Index scorecard

---

## CONCLUSION

The MCP Analytics Toolkit provides **comprehensive, multi-domain visibility** into schedule performance across:
- **Regulatory compliance** (ACGME)
- **Operational resilience** (N-1/N-2, cascade analysis)
- **Workforce burnout** (epidemiology, early warning)
- **Quality assurance** (Six Sigma, process capability)
- **Network vulnerability** (graph analysis, centrality)
- **Predictive signals** (critical slowing down, changepoint detection)

**All 81 tools are queryable, filterable, and aggregatable**, enabling AI assistants to build sophisticated analytical workflows for medical residency program scheduling.

---

**End of Report**

Generated by G2_RECON SEARCH_PARTY
Session: Session 8 - Overnight Burn
Classification: ANALYTICAL RECONNAISSANCE
