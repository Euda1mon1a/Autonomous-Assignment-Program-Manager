# Six Sigma Process Capability Analysis - Usage Guide

## Overview

The `process_capability` module provides Six Sigma quality metrics for measuring schedule quality and process control. It implements industry-standard capability indices (Cp, Cpk, Pp, Ppk, Cpm) to quantify how consistently the scheduling system meets ACGME compliance and operational constraints.

## Quick Start

```python
from app.resilience.process_capability import ScheduleCapabilityAnalyzer

# Create analyzer instance
analyzer = ScheduleCapabilityAnalyzer(min_sample_size=30)

# Analyze weekly resident hours
weekly_hours = [65, 72, 58, 75, 68, 70, 62, 77, 64, 69, 71, 66]

report = analyzer.analyze_workload_capability(
    weekly_hours,
    min_hours=40.0,      # Lower spec limit
    max_hours=80.0,      # Upper spec limit (ACGME)
    target_hours=60.0    # Ideal target
)

# Check results
print(f"Capability: {report.capability_status}")  # EXCELLENT, CAPABLE, MARGINAL, or INCAPABLE
print(f"Cpk: {report.cpk:.3f}")                    # Process capability index
print(f"Sigma Level: {report.sigma_level:.2f}σ")  # Quality level
```

## Understanding the Metrics

### Cp (Process Capability)
- **Formula**: `Cp = (USL - LSL) / (6σ)`
- **Meaning**: Potential capability if process were perfectly centered
- **Interpretation**:
  - Cp >= 2.0: Excellent
  - Cp >= 1.33: Capable
  - Cp >= 1.0: Marginal
  - Cp < 1.0: Incapable

### Cpk (Centered Process Capability)
- **Formula**: `Cpk = min((USL - μ) / 3σ, (μ - LSL) / 3σ)`
- **Meaning**: Actual capability accounting for process centering
- **Key Points**:
  - Cpk <= Cp (always)
  - Cpk < Cp indicates off-center process
  - **Use this metric for decisions**

### Cpm (Taguchi Capability)
- **Formula**: `Cpm = Cp / √(1 + ((μ - T) / σ)²)`
- **Meaning**: Capability with penalty for being off-target
- **Key Points**:
  - More stringent than Cpk
  - Encourages hitting target, not just staying within specs

### Sigma Level
- **Formula**: `σ_level ≈ 3 × Cpk`
- **Meaning**: Process quality in sigma (σ) units
- **Interpretation**:
  - 6σ (Cpk=2.0): 0.002 defects per million (world-class)
  - 5σ (Cpk=1.67): 0.6 defects per million
  - 4σ (Cpk=1.33): 66 defects per million (industry standard)
  - 3σ (Cpk=1.0): 2,700 defects per million (minimum acceptable)

## Common Use Cases

### 1. ACGME Compliance Monitoring

Monitor resident weekly hours to ensure consistent compliance:

```python
from app.resilience.process_capability import ScheduleCapabilityAnalyzer

analyzer = ScheduleCapabilityAnalyzer()

# Collect 12 weeks of data
weekly_hours = [65, 72, 58, 75, 68, 70, 62, 77, 64, 69, 71, 66]

report = analyzer.analyze_workload_capability(
    weekly_hours,
    min_hours=40.0,
    max_hours=80.0,  # ACGME limit
    target_hours=60.0
)

if report.capability_status == "INCAPABLE":
    print("WARNING: High risk of ACGME violations")
    print(f"Cpk: {report.cpk:.3f} - Process cannot consistently meet 80-hour limit")
elif report.capability_status == "MARGINAL":
    print("CAUTION: Process barely meets requirements")
    print("Recommendation: Reduce variation in weekly assignments")
elif report.capability_status in ["CAPABLE", "EXCELLENT"]:
    print(f"✓ Process is {report.capability_status.lower()}")
    print(f"Estimated violation rate: <0.01%")
```

### 2. Schedule Generator Comparison

Compare different scheduling algorithms:

```python
# Test Algorithm A
algo_a_hours = generate_schedule_with_algorithm_a()
report_a = analyzer.analyze_workload_capability(algo_a_hours, 40, 80)

# Test Algorithm B
algo_b_hours = generate_schedule_with_algorithm_b()
report_b = analyzer.analyze_workload_capability(algo_b_hours, 40, 80)

# Compare
if report_b.cpk > report_a.cpk:
    print(f"Algorithm B is superior: Cpk={report_b.cpk:.3f} vs {report_a.cpk:.3f}")
    print(f"Algorithm B is {report_b.cpk / report_a.cpk:.1f}x more capable")
```

### 3. Process Improvement Tracking

Track capability over time to measure improvement:

```python
from datetime import date

# Baseline (before improvement)
baseline_hours = [...]  # Old scheduling system
baseline_report = analyzer.analyze_workload_capability(baseline_hours, 40, 80)

# After improvement
improved_hours = [...]  # New scheduling system
improved_report = analyzer.analyze_workload_capability(improved_hours, 40, 80)

improvement = {
    "cpk_change": improved_report.cpk - baseline_report.cpk,
    "sigma_change": improved_report.sigma_level - baseline_report.sigma_level,
    "variation_reduction": (1 - improved_report.std_dev / baseline_report.std_dev) * 100
}

print(f"Cpk improved from {baseline_report.cpk:.3f} to {improved_report.cpk:.3f}")
print(f"Variation reduced by {improvement['variation_reduction']:.1f}%")
```

### 4. Integration with Resilience Monitoring

Combine with existing resilience framework:

```python
from app.resilience.utilization import UtilizationMonitor
from app.resilience.process_capability import ScheduleCapabilityAnalyzer

# Monitor both utilization and capability
utilization_monitor = UtilizationMonitor()
capability_analyzer = ScheduleCapabilityAnalyzer()

# Get current schedule data
weekly_hours = get_recent_weekly_hours(weeks=12)

# Check utilization
utilization_metrics = utilization_monitor.calculate_utilization(
    available_faculty=get_available_faculty(),
    required_blocks=get_required_blocks()
)

# Check capability
capability_report = capability_analyzer.analyze_workload_capability(
    weekly_hours,
    min_hours=40,
    max_hours=80
)

# Combined assessment
if utilization_metrics.level.value in ["red", "black"] and \
   capability_report.capability_status == "INCAPABLE":
    print("CRITICAL: Both high utilization AND poor capability")
    print("Recommendation: Activate load shedding AND review scheduling process")
```

## Interpreting Results

### ProcessCapabilityReport Fields

```python
report = analyzer.analyze_workload_capability(data, 40, 80)

# Core indices
report.cp       # Process potential (assumes centered)
report.cpk      # Process capability (actual) ⭐ Use this for decisions
report.pp       # Process performance (long-term Cp)
report.ppk      # Process performance (long-term Cpk)
report.cpm      # Taguchi index (penalizes off-target)

# Classification
report.capability_status  # "EXCELLENT", "CAPABLE", "MARGINAL", "INCAPABLE"
report.sigma_level       # Quality level (e.g., 4.5σ)

# Statistics
report.sample_size       # Number of data points
report.mean              # Average value
report.std_dev          # Standard deviation
report.lsl              # Lower specification limit
report.usl              # Upper specification limit
report.target           # Target value (optional)
```

### Getting a Human-Readable Summary

```python
summary = analyzer.get_capability_summary(report)

print(f"Status: {summary['status']}")
print(f"Sigma Level: {summary['sigma_level']}")
print(f"Centering: {summary['centering']}")
print(f"Estimated Defect Rate: {summary['estimated_defect_rate']['ppm']} PPM")

print("\nRecommendations:")
for rec in summary['recommendations']:
    print(f"  • {rec}")
```

## Decision Guidelines

### When to Deploy a Schedule Generator

| Cpk      | Sigma | Classification | Decision                           |
|----------|-------|----------------|-------------------------------------|
| >= 2.0   | 6σ    | EXCELLENT      | Deploy - World-class quality        |
| >= 1.67  | 5σ    | EXCELLENT      | Deploy - Excellent quality          |
| >= 1.33  | 4σ    | CAPABLE        | Deploy - Industry standard          |
| >= 1.0   | 3σ    | MARGINAL       | Improve before deploying            |
| < 1.0    | <3σ   | INCAPABLE      | Do NOT deploy - defects expected    |

### When to Investigate a Process

- **Cpk dropping over time**: Process degradation
- **Cpk < Cp significantly**: Process off-center, adjust mean
- **Cpm << Cp**: Process hitting specs but not target
- **High std_dev**: Too much variation, need tighter controls

## Advanced Usage

### Custom Specification Limits

```python
# Coverage rate analysis (0-100%)
coverage_rates = [0.98, 0.97, 0.99, 0.96, 0.98, 0.97]
report = analyzer.analyze_workload_capability(
    coverage_rates,
    min_hours=0.95,  # 95% minimum coverage
    max_hours=1.0,   # 100% maximum
    target_hours=1.0 # Aim for 100%
)
```

### Individual Index Calculations

```python
# Calculate just Cp
cp = analyzer.calculate_cp(data, lsl=40, usl=80)

# Calculate just Cpk
cpk = analyzer.calculate_cpk(data, lsl=40, usl=80)

# Calculate Cpm with specific target
cpm = analyzer.calculate_cpm(data, lsl=40, usl=80, target=60)

# Convert Cpk to sigma level
sigma = analyzer.get_sigma_level(cpk)

# Classify capability
status = analyzer.classify_capability(cpk)  # Returns str
```

## Best Practices

1. **Sample Size**: Use at least 30 data points for reliable analysis
2. **Time Window**: Analyze rolling windows (e.g., last 12 weeks)
3. **Consistent Measurement**: Always use same specification limits
4. **Regular Monitoring**: Track Cpk weekly or monthly
5. **Document Baseline**: Record initial Cpk when deploying new systems
6. **Set Targets**: Aim for Cpk >= 1.33 (4σ quality)
7. **Investigate Changes**: Any Cpk drop >0.2 should trigger investigation

## Files Created

1. **Main Module**: `/backend/app/resilience/process_capability.py` (564 lines)
   - ProcessCapabilityReport dataclass
   - ScheduleCapabilityAnalyzer class
   - All Six Sigma calculation methods

2. **Test Suite**: `/backend/tests/resilience/test_process_capability.py` (840 lines)
   - Comprehensive pytest test coverage
   - Tests for all calculation methods
   - Edge case testing
   - Integration tests

3. **Demo Script**: `/backend/demo_process_capability.py` (318 lines)
   - Interactive demonstrations
   - Manual calculation examples
   - Practical use cases

## Running Tests

```bash
# Run all process capability tests
cd backend
pytest tests/resilience/test_process_capability.py -v

# Run specific test class
pytest tests/resilience/test_process_capability.py::TestCpkCalculation -v

# Run with coverage
pytest tests/resilience/test_process_capability.py --cov=app.resilience.process_capability
```

## Running Demo

```bash
cd backend
python demo_process_capability.py
```

## Integration Checklist

- [x] Module created at `app/resilience/process_capability.py`
- [x] Tests created at `tests/resilience/test_process_capability.py`
- [x] Follows project code style (type hints, Google docstrings)
- [x] Uses dataclasses for data structures
- [x] Compatible with existing resilience modules
- [x] Comprehensive test coverage
- [x] Documentation and examples provided

## Next Steps

1. **Import into resilience service**: Add capability analysis to `ResilienceService`
2. **Create Prometheus metrics**: Track Cpk over time
3. **Add to health checks**: Include capability status in resilience reports
4. **Dashboard integration**: Display capability trends in Grafana
5. **Alert thresholds**: Set alerts for Cpk < 1.33

## References

- Six Sigma methodology: Process capability indices
- ACGME work hour requirements
- Statistical process control (SPC)
- Taguchi loss function and robust quality engineering
