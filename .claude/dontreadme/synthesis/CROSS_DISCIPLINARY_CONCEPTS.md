# Cross-Disciplinary Resilience Concepts - Quick Reference

**Purpose:** Map cross-industry concepts to medical residency scheduling for LLM context loading.

**Audience:** AI agents integrating resilience framework

**Last Updated:** 2025-12-31 (Session 37)

---

## Concept Hierarchy

**Tier 1 - Core:** Foundational concepts (must implement)
**Tier 2 - Strategic:** High-leverage patterns (recommended)
**Tier 3 - Analytics:** Advanced monitoring (operational excellence)
**Tier 4 - Observability:** Infrastructure hardening (production-ready)
**Tier 5 - Exotic Frontier:** Research-grade innovations (bleeding edge)

---

## Tier 1: Core Concepts (Foundational)

### 80% Utilization Threshold (Queuing Theory)

**Source:** Telecommunications, data center capacity planning

**Concept:** Systems above 80% utilization experience exponential queue growth (M/M/c queuing model)

**Application to Scheduling:**
- Monitor resident utilization: `hours_worked / max_hours_available`
- Alert when utilization > 80% (yellow zone)
- Critical alert when > 90% (red zone)

**Metrics:**
- Individual utilization: `sum(shift_hours) / (7 days × 24 hours)`
- Team utilization: `avg(individual_utilization)`

**Implementation:** `backend/app/resilience/utilization_monitor.py`

**MCP Tool:** `mcp__resilience_calculate_utilization`

---

### N-1/N-2 Contingency (Power Grid)

**Source:** Electrical grid reliability engineering

**Concept:** System must survive loss of any 1 component (N-1) or any 2 (N-2)

**Application to Scheduling:**
- N-1: Can schedule survive if any 1 resident is unavailable?
- N-2: Can schedule survive if any 2 residents are unavailable?

**Checks:**
- Coverage: All critical shifts still covered?
- ACGME compliance: Work hour limits still satisfied?
- Specialization: Credentialed staff available for procedures?

**Implementation:** `backend/app/resilience/contingency_analyzer.py`

**MCP Tool:** `mcp__resilience_analyze_contingency`

---

### Defense in Depth (5 Safety Levels)

**Source:** Cybersecurity, nuclear safety (Swiss cheese model)

**Concept:** Multiple independent safety layers (failure of one doesn't cause catastrophe)

**Application to Scheduling:**
1. **GREEN (Safe):** Utilization < 70%, no conflicts, full coverage
2. **YELLOW (Caution):** Utilization 70-80%, minor gaps, N-1 passes
3. **ORANGE (Warning):** Utilization 80-90%, coverage gaps, N-1 fails
4. **RED (Critical):** Utilization > 90%, ACGME violations imminent
5. **BLACK (Emergency):** Active ACGME violations, immediate intervention required

**Implementation:** `backend/app/resilience/defense_levels.py`

**MCP Tool:** `mcp__resilience_get_defense_level`

---

## Tier 3: Analytics (Advanced Monitoring)

### SPC - Statistical Process Control (Manufacturing)

**Source:** Semiconductor manufacturing, Six Sigma quality control

**Concept:** Control charts detect when process deviates from expected variation

**Western Electric Rules:**
1. Any point beyond 3σ (rare, investigate)
2. 2 of 3 consecutive points beyond 2σ (trend)
3. 4 of 5 consecutive points beyond 1σ (shift)
4. 8 consecutive points on same side of mean (bias)

**Application to Scheduling:**
- Chart: Weekly work hours over time
- Control limits: ±3σ from mean
- Alerts: When Western Electric rules violated

**Implementation:** `backend/app/resilience/spc_monitor.py`

**MCP Tool:** `mcp__resilience_spc_check_violations`

---

### Burnout Epidemiology (SIR Model)

**Source:** Public health, disease modeling

**Concept:** Burnout spreads like a contagion (susceptible → infected → recovered)

**SIR Model:**
- **S (Susceptible):** Residents at risk (high utilization, low recovery)
- **I (Infected):** Actively burned out
- **R (Recovered):** Post-burnout, may relapse

**Metrics:**
- **Rt (Reproduction number):** How many residents does 1 burned-out resident "infect"?
- Rt < 1: Burnout declining
- Rt = 1: Endemic burnout
- Rt > 1: Epidemic burnout

**Implementation:** `backend/app/resilience/burnout_sir.py`

**MCP Tool:** `mcp__resilience_calculate_burnout_rt`

---

### Erlang C Coverage (Telecommunications)

**Source:** Call center staffing, telecom queuing

**Concept:** Minimum staff to maintain service level (e.g., 80% of calls answered within 20 seconds)

**Application to Scheduling:**
- Calculate minimum residents needed for target wait time
- Accounts for stochastic arrivals (patients, procedures)

**Formula:**
```
Erlang C = P(wait > 0) given λ (arrival rate), μ (service rate), c (servers)
```

**Implementation:** `backend/app/resilience/erlang_coverage.py`

**MCP Tool:** `mcp__resilience_erlang_min_staff`

---

### Burnout Fire Index (Forestry)

**Source:** Canadian Forest Fire Danger Rating System (CFFDRS)

**Concept:** Multi-temporal danger rating (current conditions + long-term dryness)

**Indices:**
1. **FFMC (Fine Fuel Moisture Code):** Short-term stress (daily)
2. **DMC (Duff Moisture Code):** Medium-term stress (weekly)
3. **DC (Drought Code):** Long-term stress (seasonal)
4. **FWI (Fire Weather Index):** Combined danger rating

**Application to Scheduling:**
- FFMC → Daily stress (today's shift load)
- DMC → Weekly stress (rolling 7-day hours)
- DC → Seasonal stress (cumulative fatigue over rotation)
- FWI → Composite burnout risk score

**Implementation:** `backend/app/resilience/burnout_fire_index.py`

**MCP Tool:** `mcp__resilience_fire_index_calculate`

---

### STA/LTA Seismic Detection (Geophysics)

**Source:** Earthquake precursor detection

**Concept:** Short-Term Average / Long-Term Average ratio detects anomalies

**Formula:**
```
STA = avg(signal, last 5 days)
LTA = avg(signal, last 30 days)
Trigger = STA / LTA > 3.0
```

**Application to Scheduling:**
- Signal: Daily stress score
- Trigger: When recent stress >> baseline stress

**Implementation:** `backend/app/resilience/sta_lta_detector.py`

**MCP Tool:** `mcp__resilience_sta_lta_detect_anomaly`

---

## Tier 5: Exotic Frontier (Research-Grade)

### Metastability Detection (Statistical Mechanics)

**Source:** Phase transitions in physics

**Concept:** System trapped in local minimum (solver stuck in suboptimal solution)

**Escape Strategies:**
- Simulated annealing (temperature-based jumps)
- Tunneling (quantum-inspired barrier crossing)
- Basin hopping (restart from random state)

**Application to Scheduling:**
- Detect when solver iterates without improvement (stuck)
- Apply escape strategy to find better solution

**Implementation:** `backend/app/resilience/exotic/metastability.py`

**Status:** Experimental

---

### Spin Glass Model (Condensed Matter Physics)

**Source:** Frustrated magnetic systems

**Concept:** Conflicting constraints create multiple valid solutions

**Application to Scheduling:**
- Generate diverse schedule replicas (not just one optimal)
- Useful for contingency planning (fallback schedules)

**Implementation:** `backend/app/resilience/exotic/spin_glass.py`

**Status:** Experimental

---

### Circadian PRC (Chronobiology)

**Source:** Circadian rhythm research, jet lag

**Concept:** Phase Response Curve - how timing of stimulus affects circadian shift

**Application to Scheduling:**
- Model burnout based on shift timing (night shifts disrupt circadian rhythm)
- Mechanistic model (not just correlational)

**Implementation:** `backend/app/resilience/exotic/circadian_prc.py`

**Status:** Experimental

---

### Penrose Process (Astrophysics)

**Source:** Black hole energy extraction

**Concept:** Extract energy from rotation boundaries

**Application to Scheduling:**
- Efficiency gains from rotation transitions (handoffs, knowledge transfer)

**Implementation:** `backend/app/resilience/exotic/penrose_process.py`

**Status:** Experimental

---

## Quick Reference Table

| Concept | Source Field | Metric | Alert Threshold | MCP Tool |
|---------|--------------|--------|-----------------|----------|
| **Utilization** | Queuing Theory | % time working | > 80% | `mcp__resilience_calculate_utilization` |
| **N-1 Contingency** | Power Grid | Coverage with 1 loss | Fails | `mcp__resilience_analyze_contingency` |
| **Defense Level** | Cybersecurity | Safety tier | ORANGE+ | `mcp__resilience_get_defense_level` |
| **SPC Violation** | Manufacturing | Western Electric | Any rule | `mcp__resilience_spc_check_violations` |
| **Burnout Rt** | Epidemiology | Reproduction # | > 1.0 | `mcp__resilience_calculate_burnout_rt` |
| **Erlang C** | Telecom | Service level | < 80% | `mcp__resilience_erlang_min_staff` |
| **Fire Index** | Forestry | FWI score | > 30 (High) | `mcp__resilience_fire_index_calculate` |
| **STA/LTA** | Seismology | Ratio | > 3.0 | `mcp__resilience_sta_lta_detect_anomaly` |

---

## Integration with MCP Tools

All Tier 1-3 concepts have corresponding MCP tools. Use them via:

```python
# Example: Check defense level
result = await mcp_client.call_tool(
    "mcp__resilience_get_defense_level",
    {"schedule_id": "block_10"}
)

# Example: Calculate burnout Rt
rt = await mcp_client.call_tool(
    "mcp__resilience_calculate_burnout_rt",
    {"start_date": "2025-01-01", "end_date": "2025-01-31"}
)
```

**See:** `mcp-server/src/scheduler_mcp/tools/resilience/`

---

## Human-Readable Summaries

For human-facing dashboards, translate metrics:

- **Utilization 85%** → "Approaching capacity, watch for overload"
- **N-1 Fails** → "Vulnerable to single resident absence"
- **Defense Level ORANGE** → "Schedule under stress, intervention recommended"
- **Burnout Rt = 1.3** → "Burnout spreading, expect 30% increase"
- **FWI = 35** → "High burnout risk (like 'High' fire danger)"
- **STA/LTA = 4.2** → "Recent stress 4x baseline (anomaly detected)"

---

## Further Reading

- **Full Documentation:** `docs/architecture/cross-disciplinary-resilience.md`
- **Exotic Concepts:** `docs/architecture/EXOTIC_FRONTIER_CONCEPTS.md`
- **Time Crystal Scheduling:** `docs/architecture/TIME_CRYSTAL_ANTI_CHURN.md`
- **MCP Tools:** `mcp-server/README.md`

---

**Maintained by:** Sessions 15-20, 37 (resilience framework development)
