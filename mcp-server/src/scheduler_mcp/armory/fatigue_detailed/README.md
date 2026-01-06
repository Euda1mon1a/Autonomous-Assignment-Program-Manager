# Fatigue Detailed Domain

> **Low-Level FRMS Components and Batch Analysis Tools**

This domain contains granular fatigue analysis tools for detailed FRMS (Fatigue Risk Management System) calculations. Most users should use the high-level `run_frms_assessment_tool` from the core toolkit.

---

## Tool Inventory (6 tools)

### Core Fatigue Components (3 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `get_fatigue_score_tool` | Real-time fatigue calculation | Samn-Perelli scale (1-7) |
| `analyze_sleep_debt_tool` | Cumulative sleep deficit | BAC equivalence mapping |
| `evaluate_fatigue_hazard_tool` | 5-level hazard assessment | Aviation FRMS (GREEN to BLACK) |

**When to use:** Building custom fatigue models; debugging FRMS calculations; integrating with external systems.

### Fire Danger Index (2 tools)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `calculate_fire_danger_index_tool` | Multi-temporal burnout danger | Canadian CFFDRS adaptation |
| `calculate_batch_fire_danger_tool` | Program-wide screening | Identify highest-risk residents |

**When to use:** Large-scale burnout screening; comparative risk analysis; trend monitoring across cohorts.

### Advanced Detection (1 tool)

| Tool | Purpose | Core Concept |
|------|---------|--------------|
| `detect_burnout_precursors_tool` | Seismic early warning | STA/LTA algorithm (Short-Term/Long-Term Average) |

**When to use:** Detecting P-wave equivalents before burnout events; time-series analysis of workload patterns.

---

## Relationship to Core FRMS Tool

The core `run_frms_assessment_tool` aggregates these components:

```
run_frms_assessment_tool
├── get_fatigue_score_tool        (Samn-Perelli level)
├── analyze_sleep_debt_tool       (Sleep debt hours)
├── evaluate_fatigue_hazard_tool  (Hazard level)
└── (internal alertness model)    (Circadian predictions)
```

**Use the core tool** for standard assessments. **Use armory tools** when:
- Building custom fatigue models
- Debugging unexpected FRMS results
- Integrating with research systems
- Performing batch analysis

---

## Samn-Perelli Scale

| Level | Description | Duty Status |
|-------|-------------|-------------|
| 1 | Fully alert, wide awake | Safe |
| 2 | Very lively, responsive | Safe |
| 3 | Okay, somewhat fresh | Safe |
| 4 | A little tired, less than fresh | Caution |
| 5 | Moderately tired, let down | Warning |
| 6 | Extremely tired, very difficult to concentrate | Unsafe |
| 7 | Completely exhausted, unable to function | Incapacitated |

---

## Fire Danger Index Levels

Adapted from Canadian Forest Fire Danger Rating System:

| Level | Color | Restrictions |
|-------|-------|--------------|
| LOW | Green | Normal operations |
| MODERATE | Blue | Standard monitoring |
| HIGH | Yellow | Increased vigilance |
| VERY HIGH | Orange | Workload restrictions |
| EXTREME | Red | Immediate intervention |

---

## Sleep Debt BAC Equivalence

Based on Van Dongen et al. (2003):

| Hours Awake | BAC Equivalent | Impairment |
|-------------|----------------|------------|
| 17 | 0.05% | Mild |
| 20 | 0.08% | Legal limit (driving) |
| 24 | 0.10% | Significant |
| 28 | 0.15% | Severe |

---

## STA/LTA Algorithm

Seismological precursor detection adapted for workload:

```
STA = mean(signal[t-short_window:t])
LTA = mean(signal[t-long_window:t])
ratio = STA / LTA

if ratio > threshold:
    alert("Precursor detected")
```

**Typical parameters:**
- short_window: 5 days (acute changes)
- long_window: 30 days (baseline)
- threshold: 2.5 (significant deviation)

---

## Scientific References

- Samn, S.W. & Perelli, L.P. (1982). "Estimating aircrew fatigue"
- Van Dongen, H.P. et al. (2003). "The cumulative cost of additional wakefulness"
- Allen, R.V. (1978). "Automatic earthquake recognition and timing from single traces"
- FAA AC 120-103A. "Fatigue Risk Management Systems for Aviation Safety"

---

## Activation

```bash
export ARMORY_DOMAINS="fatigue_detailed"
# or
/armory fatigue_detailed
```
