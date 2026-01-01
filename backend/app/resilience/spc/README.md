***REMOVED*** Statistical Process Control (SPC) Module

***REMOVED******REMOVED*** Overview

This module implements Statistical Process Control (SPC) techniques from semiconductor manufacturing and Six Sigma quality control, adapted for monitoring resilience metrics in medical residency scheduling.

**Origin**: Walter Shewhart (Bell Labs, 1920s), refined by Western Electric (1956)

**Purpose**: Detect when a monitored process goes "out of control" - distinguishing normal variation from special cause variation requiring intervention.

---

***REMOVED******REMOVED*** Module Structure

```
backend/app/resilience/spc/
|-- __init__.py              ***REMOVED*** Public exports
|-- control_chart.py         ***REMOVED*** Shewhart, CUSUM, and EWMA charts
|-- western_electric.py      ***REMOVED*** Western Electric 8-rule detection
```

---

***REMOVED******REMOVED*** Control Charts (`control_chart.py`)

***REMOVED******REMOVED******REMOVED*** ControlChart (Shewhart X-bar Chart)

The basic control chart monitors individual measurements against statistical control limits.

***REMOVED******REMOVED******REMOVED******REMOVED*** Control Limits

```
UCL = center_line + 3 * sigma    Upper Control Limit
UWL = center_line + 2 * sigma    Upper Warning Limit
CL  = center_line                Center Line (mean or target)
LWL = center_line - 2 * sigma    Lower Warning Limit
LCL = center_line - 3 * sigma    Lower Control Limit
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Zone Classification

Points are classified into zones based on distance from center line:

| Zone | Distance from CL | Probability (Normal) |
|------|------------------|---------------------|
| A    | Within 1 sigma   | 68.27%              |
| B    | 1-2 sigma        | 27.18%              |
| C    | 2-3 sigma        | 4.28%               |
| Out  | Beyond 3 sigma   | 0.27%               |

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
from app.resilience.spc import ControlChart, ControlChartType

***REMOVED*** Create chart
chart = ControlChart(
    chart_type=ControlChartType.XBAR,
    sigma_multiplier=3.0  ***REMOVED*** Standard 3-sigma limits
)

***REMOVED*** Calculate limits from baseline data (minimum 5 points)
baseline_data = [60, 62, 58, 61, 59, 63, 60, 58, 62, 61]
limits = chart.calculate_limits(baseline_data)

print(f"Center Line: {limits.center_line:.2f}")
print(f"UCL: {limits.ucl:.2f}")
print(f"LCL: {limits.lcl:.2f}")
print(f"Sigma: {limits.sigma:.2f}")

***REMOVED*** Add new data points and check control status
point = chart.add_point(65.0)
print(f"Value: {point.value}")
print(f"In Control: {point.is_in_control}")
print(f"Zone: {point.zone}")
print(f"Violated Rule: {point.violated_rule}")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Key Classes

```python
@dataclass
class ControlLimits:
    center_line: float  ***REMOVED*** Mean or target
    ucl: float          ***REMOVED*** Upper control limit (mean + 3 sigma)
    lcl: float          ***REMOVED*** Lower control limit (mean - 3 sigma)
    uwl: float          ***REMOVED*** Upper warning limit (mean + 2 sigma)
    lwl: float          ***REMOVED*** Lower warning limit (mean - 2 sigma)
    sigma: float        ***REMOVED*** Process standard deviation

@dataclass
class ControlChartPoint:
    timestamp: datetime
    value: float
    is_in_control: bool
    violated_rule: str | None  ***REMOVED*** Rule name if violated
    zone: str                  ***REMOVED*** "A", "B", "C", or "Out"
```

---

***REMOVED******REMOVED******REMOVED*** Process Capability Indices (Cp/Cpk)

Process capability indices measure how well a process fits within specification limits.

***REMOVED******REMOVED******REMOVED******REMOVED*** Formulas

```
Cp  = (UCL - LCL) / (6 * sigma)           Process Capability
Cpu = (UCL - process_mean) / (3 * sigma)  Upper Capability
Cpl = (process_mean - LCL) / (3 * sigma)  Lower Capability
Cpk = min(Cpu, Cpl)                        Centered Capability
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Interpretation

| Cpk Value | Interpretation | Defect Rate (ppm) |
|-----------|----------------|-------------------|
| >= 2.00   | Excellent (Six Sigma) | 3.4       |
| >= 1.33   | Good (Four Sigma)     | 63        |
| >= 1.00   | Adequate              | 2,700     |
| < 1.00    | Poor                  | > 66,807  |

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
***REMOVED*** After adding data points to the chart
capability = chart.get_capability_indices()

print(f"Cp:  {capability['cp']}")
print(f"Cpk: {capability['cpk']}")
print(f"Cpu: {capability['cpu']}")
print(f"Cpl: {capability['cpl']}")
print(f"Interpretation: {capability['interpretation']}")
print(f"Process Mean: {capability['process_mean']}")
```

---

***REMOVED******REMOVED******REMOVED*** Trend Detection

Detect increasing, decreasing, or stable trends in recent data.

```python
trends = chart.detect_trends(window_size=7)

print(f"Trend: {trends['trend']}")        ***REMOVED*** "increasing", "decreasing", "stable"
print(f"Slope: {trends['slope']}")        ***REMOVED*** Rate of change
print(f"Recent Mean: {trends['recent_mean']}")
print(f"Recent Std: {trends['recent_std']}")
```

---

***REMOVED******REMOVED******REMOVED*** CUSUMChart (Cumulative Sum)

CUSUM charts are more sensitive to small, persistent shifts in the process mean than Shewhart charts.

***REMOVED******REMOVED******REMOVED******REMOVED*** Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| target    | Process target/mean | From baseline |
| sigma     | Process std deviation | From baseline |
| k         | Allowable slack (in sigma units) | 0.5 |
| h         | Decision interval (in sigma units) | 4.0-5.0 |

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
from app.resilience.spc.control_chart import CUSUMChart

***REMOVED*** Initialize with target and sigma from baseline
cusum = CUSUMChart(
    target=60.0,
    sigma=3.0,
    k=0.5,    ***REMOVED*** Allowable slack (0.5 sigma typical)
    h=4.0     ***REMOVED*** Decision interval (4-5 sigma typical)
)

***REMOVED*** Add points - CUSUM accumulates deviations
for value in [61, 62, 61, 63, 62, 64, 63, 65]:
    point = cusum.add_point(value)
    print(f"Value: {value}, CUSUM+: {point.cusum_high:.2f}, "
          f"CUSUM-: {point.cusum_low:.2f}, In Control: {point.is_in_control}")

***REMOVED*** Reset CUSUM after intervention
cusum.reset()
```

***REMOVED******REMOVED******REMOVED******REMOVED*** How CUSUM Works

- Maintains two cumulative sums: one for upward drift, one for downward drift
- Accumulates deviations from target, minus allowable slack (k)
- Signals when cumulative sum exceeds decision interval (h)
- More sensitive to small persistent shifts than Shewhart charts

---

***REMOVED******REMOVED******REMOVED*** EWMAChart (Exponentially Weighted Moving Average)

EWMA charts smooth data and are effective for autocorrelated data and detecting gradual shifts.

***REMOVED******REMOVED******REMOVED******REMOVED*** Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| target    | Process target | From baseline |
| sigma     | Process std deviation | From baseline |
| lambda_   | Weighting factor (0 < lambda <= 1) | 0.2-0.3 |
| L         | Control limit multiplier | 3.0 |

***REMOVED******REMOVED******REMOVED******REMOVED*** Usage

```python
from app.resilience.spc.control_chart import EWMAChart

ewma = EWMAChart(
    target=60.0,
    sigma=3.0,
    lambda_=0.2,  ***REMOVED*** Weighting factor (smaller = more smoothing)
    L=3.0         ***REMOVED*** Control limit width
)

***REMOVED*** Add points - EWMA smooths the data
for value in [62, 58, 61, 59, 63, 60, 62, 61]:
    point = ewma.add_point(value)
    print(f"Value: {value}, EWMA: {point.ewma:.2f}, "
          f"UCL: {point.ucl:.2f}, LCL: {point.lcl:.2f}")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** EWMA Formula

```
z_t = lambda * x_t + (1 - lambda) * z_{t-1}

where:
  z_t     = EWMA at time t
  x_t     = observation at time t
  lambda  = weighting factor (0 < lambda <= 1)
  z_0     = target (initial value)
```

---

***REMOVED******REMOVED*** Western Electric Rules (`western_electric.py`)

Classic rules from AT&T/Western Electric (1956) for detecting out-of-control conditions.

***REMOVED******REMOVED******REMOVED*** The Eight Rules

| Rule | Condition | Severity | Interpretation |
|------|-----------|----------|----------------|
| 1 | One point beyond 3 sigma | CRITICAL | Immediate investigation required |
| 2 | 2 of 3 consecutive beyond 2 sigma (same side) | WARNING | Shift detected |
| 3 | 4 of 5 consecutive beyond 1 sigma (same side) | WARNING | Trend detected |
| 4 | 8 consecutive on same side of center line | WARNING | Sustained shift |
| 5 | 6 consecutive trending up or down | WARNING | Monotonic trend |
| 6 | 15 consecutive within 1 sigma | INFO | Suspiciously stable (possible data manipulation) |
| 7 | 14 consecutive alternating up/down | INFO | Systematic variation |
| 8 | 8 consecutive beyond 1 sigma (both sides) | WARNING | Excessive variation |

***REMOVED******REMOVED******REMOVED*** Usage

```python
from app.resilience.spc import WesternElectricRules

***REMOVED*** Initialize with center line and sigma
rules = WesternElectricRules(
    center_line=60.0,
    sigma=3.0
)

***REMOVED*** Check all rules against data
data = [60, 61, 59, 62, 58, 71, 60, 59]  ***REMOVED*** Note: 71 is beyond 3 sigma
violations = rules.check_all_rules(data)

for v in violations:
    print(f"Rule {v.rule_number}: {v.rule_name}")
    print(f"  Severity: {v.severity}")
    print(f"  Description: {v.description}")
    print(f"  Points: {v.points_involved}")

***REMOVED*** Get summary statistics
summary = rules.get_rule_summary(violations)
print(f"\nSummary:")
print(f"  Total Violations: {summary['total_violations']}")
print(f"  Critical: {summary['critical']}")
print(f"  Warning: {summary['warning']}")
print(f"  Info: {summary['info']}")
print(f"  Status: {summary['status']}")
print(f"  Rules Violated: {summary['rules_violated']}")
```

***REMOVED******REMOVED******REMOVED*** RuleViolation Dataclass

```python
@dataclass
class RuleViolation:
    rule_number: int        ***REMOVED*** 1-8
    rule_name: str          ***REMOVED*** e.g., "Beyond 3 Sigma"
    description: str        ***REMOVED*** Human-readable description
    severity: str           ***REMOVED*** "critical", "warning", "info"
    points_involved: list[int]  ***REMOVED*** Indices of points in violation
```

***REMOVED******REMOVED******REMOVED*** Status Interpretation

| Status | Meaning |
|--------|---------|
| in_control | No violations detected |
| stable | Only INFO-level violations |
| warning | WARNING-level violations (no critical) |
| out_of_control | CRITICAL violations present |

---

***REMOVED******REMOVED*** Medical Scheduling Application

***REMOVED******REMOVED******REMOVED*** Monitoring Resident Work Hours

```python
from app.resilience.spc import ControlChart, WesternElectricRules

***REMOVED*** Target: 60 hours/week (safe operating point)
***REMOVED*** ACGME limit: 80 hours/week
chart = ControlChart()

***REMOVED*** Baseline from historical in-control data
baseline_hours = [58, 62, 60, 59, 61, 63, 58, 60, 62, 61]
limits = chart.calculate_limits(baseline_hours)

***REMOVED*** Monitor weekly hours
weekly_hours = [60, 62, 64, 66, 68, 70, 72, 74]  ***REMOVED*** Increasing trend

for hours in weekly_hours:
    point = chart.add_point(hours)
    if not point.is_in_control:
        print(f"ALERT: {hours} hours is OUT OF CONTROL!")

***REMOVED*** Check Western Electric rules
rules = WesternElectricRules(limits.center_line, limits.sigma)
violations = rules.check_all_rules(chart.data_points)

if violations:
    print("\nWestern Electric Rule Violations Detected:")
    for v in violations:
        print(f"  - Rule {v.rule_number} ({v.severity}): {v.description}")
```

***REMOVED******REMOVED******REMOVED*** Monitoring Coverage Gaps

```python
***REMOVED*** Track daily coverage gap counts
gap_baseline = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0]  ***REMOVED*** Baseline: ~0.4 gaps/day

chart = ControlChart()
limits = chart.calculate_limits(gap_baseline)

***REMOVED*** Today's data
today_gaps = 3
point = chart.add_point(today_gaps)

if point.zone in ["C", "Out"]:
    print(f"WARNING: {today_gaps} coverage gaps is in zone {point.zone}")
```

***REMOVED******REMOVED******REMOVED*** Integration with Resilience Engine

The SPC module integrates with the broader resilience framework:

```python
from app.resilience.spc import ControlChart, WesternElectricRules

***REMOVED*** Called by resilience engine for periodic monitoring
def monitor_burnout_rate(burnout_counts: list[float]) -> dict:
    """Monitor burnout rate using SPC."""
    if len(burnout_counts) < 5:
        return {"status": "insufficient_data"}

    chart = ControlChart()
    limits = chart.calculate_limits(burnout_counts[:10])  ***REMOVED*** Baseline

    for count in burnout_counts[10:]:
        chart.add_point(count)

    rules = WesternElectricRules(limits.center_line, limits.sigma)
    violations = rules.check_all_rules(chart.data_points)

    return {
        "limits": {
            "ucl": limits.ucl,
            "lcl": limits.lcl,
            "center_line": limits.center_line,
        },
        "capability": chart.get_capability_indices(),
        "violations": rules.get_rule_summary(violations),
        "trends": chart.detect_trends(),
    }
```

---

***REMOVED******REMOVED*** Testing

```bash
***REMOVED*** Run SPC tests
pytest backend/tests/resilience/test_spc.py -v

***REMOVED*** Run with coverage
pytest backend/tests/resilience/test_spc.py --cov=app.resilience.spc
```

***REMOVED******REMOVED******REMOVED*** Test Coverage

- `TestControlChart`: Limit calculation, zone classification, in/out of control detection
- `TestCUSUMChart`: Drift detection, reset functionality
- `TestEWMAChart`: Smoothing, shift detection
- `TestWesternElectricRules`: All 8 rules, summary generation

---

***REMOVED******REMOVED*** Scientific References

1. **Shewhart, W.A.** (1931). *Economic Control of Quality of Manufactured Product*. Van Nostrand.

2. **Western Electric Company** (1956). *Statistical Quality Control Handbook*. AT&T.

3. **Montgomery, D.C.** (2012). *Introduction to Statistical Quality Control* (7th ed.). Wiley.

4. **Page, E.S.** (1954). "Continuous Inspection Schemes". *Biometrika*, 41(1/2), 100-115. (CUSUM)

5. **Roberts, S.W.** (1959). "Control Chart Tests Based on Geometric Moving Averages". *Technometrics*, 1(3), 239-250. (EWMA)

---

***REMOVED******REMOVED*** Dependencies

- `numpy`: Statistical calculations
- Python 3.11+ (for type hints)

---

***REMOVED******REMOVED*** Changelog

- **2024-12-31**: Initial implementation (Session 26)
- **Documentation**: Control charts, Western Electric rules, process capability

---

***REMOVED******REMOVED*** See Also

- `/backend/app/resilience/README.md` - Resilience framework overview
- `/docs/architecture/cross-disciplinary-resilience.md` - Full cross-domain framework
- `/backend/tests/resilience/test_spc.py` - Test suite
