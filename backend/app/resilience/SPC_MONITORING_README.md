# Statistical Process Control (SPC) Workload Monitoring

## Overview

The SPC Monitoring module implements **Western Electric Rules** for detecting workload drift and anomalies in medical resident scheduling. It provides real-time detection of unusual patterns that may indicate scheduling problems, ACGME violations, or burnout risk.

## Purpose

This module complements the existing `process_capability.py` module:

- **`process_capability.py`**: Measures overall process quality using Six Sigma capability indices (Cp, Cpk, Pp, Ppk, Cpm)
  - **Question it answers**: "How good is our overall scheduling process?"
  - **Use case**: Retrospective analysis of schedule quality over long periods
  - **Output**: Quality metrics and capability classifications

- **`spc_monitoring.py`**: Detects real-time workload anomalies using Western Electric Rules
  - **Question it answers**: "Are we seeing unusual patterns right now that need investigation?"
  - **Use case**: Real-time monitoring and early warning system
  - **Output**: Alerts when workload patterns deviate from expected norms

**Both modules are valuable and serve different purposes in a comprehensive quality monitoring system.**

## Western Electric Rules

Four rules detect different types of process variation:

### Rule 1: One Point Beyond 3σ (CRITICAL)
- **Indicates**: Special cause variation - process out of control
- **Severity**: CRITICAL
- **Action**: Immediate investigation required
- **Example**: Resident working 82 hours in one week (when UCL = 75 hours)

### Rule 2: Two of Three Consecutive Points Beyond 2σ (WARNING)
- **Indicates**: Process shift - sustained change in mean
- **Severity**: WARNING
- **Action**: Investigate cause of shift
- **Example**: 2 of 3 weeks with 70+ hours (when 2σ limit = 70 hours)

### Rule 3: Four of Five Consecutive Points Beyond 1σ (WARNING)
- **Indicates**: Process trend - gradual shift in level
- **Severity**: WARNING
- **Action**: Monitor and investigate trend
- **Example**: 4 of 5 weeks with 65+ hours (when 1σ limit = 65 hours)

### Rule 4: Eight Consecutive Points on Same Side of Centerline (INFO)
- **Indicates**: Sustained shift in process mean
- **Severity**: INFO
- **Action**: Identify and address root cause of shift
- **Example**: 8 consecutive weeks above 60-hour target

## Usage

### Basic Example

```python
from app.resilience.spc_monitoring import WorkloadControlChart
from uuid import uuid4

# Create control chart with target=60h, sigma=5h
chart = WorkloadControlChart(target_hours=60, sigma=5)

# Weekly hours for a resident over 8 weeks
weekly_hours = [58, 62, 59, 67, 71, 75, 78, 80]

# Detect violations
resident_id = uuid4()
alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

# Process alerts
for alert in alerts:
    if alert.severity == "CRITICAL":
        notify_program_director(alert)
    elif alert.severity == "WARNING":
        log_warning(alert)
    else:
        log_info(alert)
```

### Calculate Control Limits from Historical Data

```python
from app.resilience.spc_monitoring import calculate_control_limits

# Historical weekly hours data
historical_data = [58, 62, 59, 61, 63, 60, 58, 62, 64, 57]

# Calculate empirical control limits
limits = calculate_control_limits(historical_data)

print(f"Centerline: {limits['centerline']:.1f}h")
print(f"UCL (3σ): {limits['ucl']:.1f}h")
print(f"LCL (3σ): {limits['lcl']:.1f}h")

# Use empirical limits for monitoring
chart = WorkloadControlChart(
    target_hours=limits['centerline'],
    sigma=limits['sigma']
)
```

### Calculate Process Capability

```python
from app.resilience.spc_monitoring import calculate_process_capability

# Weekly hours data
data = [58, 62, 59, 61, 63, 60, 58, 62]

# ACGME limits: 0-80 hours/week
capability = calculate_process_capability(
    data=data,
    lsl=0,   # Lower spec limit
    usl=80,  # Upper spec limit (ACGME)
)

print(f"Cpk: {capability['cpk']:.2f}")
print(f"Interpretation: {capability['interpretation']}")

# Cpk >= 1.33 indicates capable process (4-sigma quality)
if capability['cpk'] < 1.0:
    print("WARNING: Process not capable - violations likely")
```

## Integration with Existing Process Capability Module

For comprehensive workload monitoring, use both modules together:

```python
from app.resilience.spc_monitoring import WorkloadControlChart
from app.resilience.process_capability import ScheduleCapabilityAnalyzer

# Real-time monitoring with Western Electric Rules
spc_chart = WorkloadControlChart(target_hours=60, sigma=5)
alerts = spc_chart.detect_western_electric_violations(resident_id, weekly_hours)

# Overall process quality assessment with Six Sigma
capability_analyzer = ScheduleCapabilityAnalyzer()
report = capability_analyzer.analyze_workload_capability(
    weekly_hours,
    min_hours=40,
    max_hours=80
)

# Act on results
if alerts:
    print(f"⚠️  {len(alerts)} SPC violations detected - immediate attention needed")
    for alert in alerts:
        print(f"  - {alert.rule}: {alert.message}")

if report.capability_status == "INCAPABLE":
    print(f"❌ Process incapable: Cpk={report.cpk:.2f} - systemic improvements required")
elif report.capability_status == "CAPABLE":
    print(f"✅ Process capable: Cpk={report.cpk:.2f} ({report.sigma_level:.1f}σ quality)")
```

## Alert Structure

All alerts include:

```python
@dataclass
class SPCAlert:
    rule: str                      # "Rule 1", "Rule 2", etc.
    severity: str                  # "CRITICAL", "WARNING", or "INFO"
    message: str                   # Human-readable description
    resident_id: Optional[UUID]    # Affected resident (or None for system-wide)
    timestamp: datetime            # When alert was generated
    data_points: list[float]       # Data that triggered the alert
    control_limits: dict           # Relevant control limits
```

## Control Chart Parameters

### Default Parameters (Recommended)

```python
WorkloadControlChart(
    target_hours=60.0,  # Target weekly hours
    sigma=5.0           # Process standard deviation
)
```

**Rationale**:
- **Target = 60h**: Provides 20-hour buffer below ACGME limit (80h)
- **Sigma = 5h**: Normal variation; 99.7% of weeks should be 45-75 hours (3σ)
- **UCL (3σ) = 75h**: 5-hour buffer before ACGME violation
- **LCL (3σ) = 45h**: Detects potential scheduling gaps

### Custom Parameters

Adjust based on your program's specific characteristics:

```python
# More aggressive monitoring (tighter tolerances)
strict_chart = WorkloadControlChart(target_hours=55, sigma=4)

# More lenient (wider tolerances)
lenient_chart = WorkloadControlChart(target_hours=65, sigma=6)

# Empirical (learn from historical data)
limits = calculate_control_limits(historical_weekly_hours)
empirical_chart = WorkloadControlChart(
    target_hours=limits['centerline'],
    sigma=limits['sigma']
)
```

## Typical Scenarios

### Scenario 1: Normal Rotation Variation

```python
# Normal variation within ±1σ
weekly_hours = [58, 62, 59, 61, 60, 58, 63, 59]
alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

# Expected: No CRITICAL or WARNING alerts (may have INFO if trending)
```

### Scenario 2: ACGME Violation Pattern

```python
# Gradual increase leading to violation
weekly_hours = [60, 65, 68, 72, 75, 78, 80, 82]
alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

# Expected:
# - Multiple Rule 1 CRITICAL alerts (78, 80, 82 > 75)
# - Rule 2 WARNING alert (shift detected)
# - Rule 3 WARNING alert (trend detected)
```

### Scenario 3: Burnout Risk Pattern

```python
# Sustained high hours (not violating, but concerning)
weekly_hours = [66, 67, 68, 67, 66, 68, 67, 66]
alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

# Expected:
# - Rule 4 INFO alert (8 consecutive above centerline)
# - Action: Investigate why consistently high, consider rotation adjustment
```

### Scenario 4: Scheduling Gap

```python
# Sudden drop suggesting gap in coverage
weekly_hours = [60, 62, 59, 20, 61]
alerts = chart.detect_western_electric_violations(resident_id, weekly_hours)

# Expected:
# - Rule 1 CRITICAL alert (20 < 45 LCL)
# - Action: Investigate scheduling gap or data error
```

## Statistical Background

### Control Chart Theory

Control charts distinguish between:

1. **Common Cause Variation**: Natural, inherent variation in the process
   - Expected and acceptable
   - Example: Normal week-to-week workload fluctuations

2. **Special Cause Variation**: Unusual, non-random variation requiring investigation
   - Detected by Western Electric Rules
   - Example: Unexpected surge in clinical demands

### Process Capability Indices

Brief comparison with `process_capability.py`:

- **Cp**: Potential capability (assumes centered) = (USL - LSL) / (6σ)
- **Cpk**: Actual capability (accounts for centering) = min((USL - μ)/3σ, (μ - LSL)/3σ)
- **Interpretation**:
  - Cpk < 1.0: Process not capable (defects expected)
  - Cpk = 1.33: Process capable (4σ quality, industry standard)
  - Cpk = 1.67: Process highly capable (5σ quality)
  - Cpk = 2.0: World-class (6σ quality)

## Testing

Comprehensive test suite at: `tests/resilience/test_spc_monitoring.py`

Run tests:

```bash
cd backend
pytest tests/resilience/test_spc_monitoring.py -v
```

Test coverage includes:
- All four Western Electric Rules
- Edge cases (empty data, boundary conditions, invalid inputs)
- Integration scenarios (ACGME violations, normal patterns, burnout risk)
- Control limit calculations
- Process capability calculations

## Performance Considerations

- **Time Complexity**: O(n) for each rule check, where n = number of weeks
- **Space Complexity**: O(n) for storing weekly hours
- **Recommended**: Monitor weekly (not daily) to reduce noise
- **Data Requirements**:
  - Minimum 1 week for any detection
  - Minimum 3 weeks for Rule 2
  - Minimum 5 weeks for Rule 3
  - Minimum 8 weeks for Rule 4

## References

- **Western Electric Rules**: Statistical Quality Control Handbook (1956)
- **Control Charts**: Walter Shewhart, "Economic Control of Quality" (1931)
- **Process Capability**: Six Sigma methodology
- **ACGME Work Hours**: [ACGME Common Program Requirements](https://www.acgme.org/what-we-do/accreditation/common-program-requirements/)

## Related Modules

- **`process_capability.py`**: Six Sigma capability indices for overall quality assessment
- **`utilization.py`**: Queuing theory-based utilization monitoring (80% threshold)
- **`homeostasis.py`**: Feedback loop detection and setpoint management
- **`metrics.py`**: Prometheus metrics for resilience monitoring

## Author Notes

This module was created to provide early warning of workload anomalies before they escalate to ACGME violations or resident burnout. It implements proven industrial quality control techniques adapted for medical scheduling.

**Key insight**: Control charts were originally developed for manufacturing quality control, but the same statistical principles apply to workload monitoring. A resident working excessive hours is analogous to a manufacturing process producing defective parts - both indicate the process is "out of control" and requires investigation.
