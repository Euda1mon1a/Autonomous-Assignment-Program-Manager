# Change Point Detection Usage Guide

This guide covers the change point detection capabilities in the residency scheduler, which identify regime shifts, policy changes, and structural breaks in schedule patterns.

## Overview

Change point detection uses signal processing algorithms to answer:
- **When did the schedule fundamentally change?**
- **Was there a policy update that affected workload?**
- **Did staffing levels shift significantly?**

Two algorithms are available:
1. **CUSUM** (Cumulative Sum) - Detects mean shifts
2. **PELT** (Pruned Exact Linear Time) - Optimal segmentation for multiple change points

---

## Quick Start

### MCP Tool (Simplest)

```python
# Via MCP tool
result = await detect_schedule_changepoints_tool(
    daily_values=[8, 8, 8, 10, 12, 12, 12, 12, 12, 12],
    dates=["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04",
           "2025-01-05", "2025-01-06", "2025-01-07", "2025-01-08",
           "2025-01-09", "2025-01-10"],
    methods=["cusum", "pelt"]
)

if result["total_changepoints"] > 0:
    print(f"Found {result['total_changepoints']} change points!")
    for method, data in result["results"].items():
        for cp in data["change_points"]:
            print(f"  [{method}] {cp['timestamp']}: {cp['description']}")
```

### Python Backend (Direct)

```python
from datetime import date, timedelta
from app.analytics.signal_processing import detect_schedule_changepoints

# Create sample data with a regime shift
daily_hours = [8.0] * 30 + [12.0] * 30  # Shift at day 30
dates = [date(2025, 1, 1) + timedelta(days=i) for i in range(60)]

# Detect change points
results = detect_schedule_changepoints(daily_hours, dates)

# Process results
for method, result in results.items():
    print(f"\n{method.upper()}:")
    print(f"  Found {result['num_changepoints']} change points")
    for cp in result['change_points']:
        print(f"  - {cp['timestamp']}: {cp['description']}")
        print(f"    Confidence: {cp['confidence']:.1%}")
```

---

## Understanding the Algorithms

### CUSUM (Cumulative Sum)

CUSUM tracks cumulative deviations from the mean and triggers an alarm when the cumulative sum exceeds a threshold.

**How it works:**
```
S_high[t] = max(0, S_high[t-1] + (x[t] - mean - drift))
S_low[t] = min(0, S_low[t-1] + (x[t] - mean + drift))

Alarm when |S| > threshold
```

**Best for:**
- Detecting sudden mean shifts (upward or downward)
- Online/streaming detection
- Clear before/after transitions

**Parameters:**
- `threshold` (default: 5.0) - Higher = fewer false alarms, lower sensitivity
- `drift` (default: 0.0) - Allowable drift before triggering

### PELT (Pruned Exact Linear Time)

PELT finds the optimal segmentation that minimizes:
```
Total Cost = Σ(segment variance × segment length) + penalty × num_changepoints
```

**Best for:**
- Finding multiple change points simultaneously
- Detecting variance changes (not just mean)
- Offline analysis of historical data

**Parameters:**
- `penalty` (default: 1.0) - Higher = fewer segments, more conservative
- `min_segment_length` (default: 5) - Minimum days between change points

---

## Common Use Cases

### 1. Detecting Policy Changes

```python
# Analyze a year of workload data
daily_hours = fetch_daily_workload(year=2024)
dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(365)]

results = detect_schedule_changepoints(daily_hours, dates)

# Find high-confidence changes
policy_changes = [
    cp for method_result in results.values()
    for cp in method_result['change_points']
    if cp['confidence'] > 0.7
]

print("Likely policy changes detected:")
for cp in sorted(policy_changes, key=lambda x: x['index']):
    print(f"  {cp['timestamp']}: {cp['change_type']} ({cp['magnitude']:+.1f} hours)")
```

### 2. Staffing Level Transitions

```python
# Look for upward shifts indicating reduced staffing
results = detect_schedule_changepoints(daily_hours, dates, methods=["cusum"])

staffing_reductions = [
    cp for cp in results['cusum']['change_points']
    if cp['change_type'] == 'mean_shift_upward'  # More work = fewer staff
    and cp['magnitude'] > 2.0  # Significant increase
]

if staffing_reductions:
    print("Warning: Detected potential staffing reductions:")
    for cp in staffing_reductions:
        print(f"  {cp['timestamp']}: Workload increased by {cp['magnitude']:.1f} hours")
```

### 3. Compliance Audit Trail

```python
# Generate audit report of all detected changes
results = detect_schedule_changepoints(daily_hours, dates)

audit_report = {
    "analysis_date": date.today().isoformat(),
    "data_range": {"start": dates[0].isoformat(), "end": dates[-1].isoformat()},
    "changes_detected": []
}

for method, result in results.items():
    for cp in result['change_points']:
        audit_report['changes_detected'].append({
            "date": cp['timestamp'],
            "detection_method": method,
            "type": cp['change_type'],
            "magnitude": cp['magnitude'],
            "confidence": cp['confidence'],
            "requires_review": cp['confidence'] > 0.7 and abs(cp['magnitude']) > 3.0
        })

# Flag changes requiring human review
needs_review = [c for c in audit_report['changes_detected'] if c['requires_review']]
print(f"Changes requiring review: {len(needs_review)}")
```

### 4. Integration with Signal Processing Pipeline

```python
from app.analytics.signal_processing import WorkloadSignalProcessor, WorkloadTimeSeries

# Full signal analysis including change points
ts = WorkloadTimeSeries(
    values=np.array(daily_hours),
    dates=dates,
)

processor = WorkloadSignalProcessor()
result = processor.analyze_workload_patterns(
    ts,
    analysis_types=["changepoint", "fft", "sta_lta"]
)

# Change points in context with other anomalies
print("Change Points:", result['changepoint_analysis'])
print("Spectral Analysis:", result['fft_analysis'])
print("Recommendations:", result['recommendations'])
```

---

## Output Interpretation

### Change Point Structure

```python
{
    "index": 30,                    # Position in time series
    "timestamp": "2025-01-31",      # Date of change
    "change_type": "mean_shift_upward",  # Type of change detected
    "magnitude": 4.2,               # Size of change (hours)
    "confidence": 0.85,             # How confident (0-1)
    "description": "Upward shift: 8.0 → 12.2"
}
```

### Change Types

| Type | Meaning |
|------|---------|
| `mean_shift_upward` | Average workload increased |
| `mean_shift_downward` | Average workload decreased |
| `variance_change` | Workload variability changed |
| `trend_change` | Both mean and variance shifted |
| `segment_boundary` | PELT-detected segment break |

### Confidence Interpretation

| Confidence | Interpretation | Action |
|------------|----------------|--------|
| > 0.8 | High confidence | Investigate cause |
| 0.5 - 0.8 | Moderate | Monitor for confirmation |
| < 0.5 | Low | Likely noise, ignore |

---

## Best Practices

### 1. Data Quality

```python
# Ensure sufficient data points
if len(daily_values) < 30:
    print("Warning: Less than 30 days of data may produce unreliable results")

# Check for missing values
if any(np.isnan(daily_values)):
    print("Warning: Missing values should be interpolated first")
```

### 2. Parameter Tuning

```python
# For noisy data, increase threshold
results = processor.detect_change_points_cusum(series, threshold=6.0)

# For smooth data, decrease threshold
results = processor.detect_change_points_cusum(series, threshold=4.0)

# For fewer segments, increase penalty
results = processor.detect_change_points_pelt(series, penalty=2.0)
```

### 3. Combining Methods

```python
# Use both methods and compare
results = detect_schedule_changepoints(daily_hours, dates, methods=["cusum", "pelt"])

# Find changes detected by both methods (higher confidence)
cusum_indices = {cp['index'] for cp in results['cusum']['change_points']}
pelt_indices = {cp['index'] for cp in results['pelt']['change_points']}

confirmed_changes = cusum_indices & pelt_indices
print(f"Changes confirmed by both methods: {len(confirmed_changes)}")
```

---

## Performance Characteristics

| Metric | CUSUM | PELT |
|--------|-------|------|
| Time Complexity | O(n) | O(n) with ruptures, O(n²) fallback |
| Memory | O(n) | O(n) |
| 365 days | < 10ms | < 50ms |
| 3 years | < 30ms | < 200ms |
| Streaming | Yes | No |

---

## Troubleshooting

### No Change Points Detected

1. **Threshold too high:** Lower `threshold` parameter
2. **Data too smooth:** Check if data is already aggregated/smoothed
3. **Insufficient data:** Need at least 10 points

### Too Many Change Points

1. **Threshold too low:** Increase `threshold` or `penalty`
2. **Noisy data:** Pre-filter with moving average
3. **Min segment too small:** Increase `min_segment_length`

### PELT Fallback Warning

```
WARNING: ruptures library not available, using simplified PELT implementation
```

Install the ruptures library for optimal PELT performance:
```bash
pip install ruptures
```

---

## API Reference

### MCP Tool

```python
detect_schedule_changepoints_tool(
    daily_values: list[float],  # Required: workload values
    dates: list[str],           # Required: YYYY-MM-DD dates
    methods: list[str] | None   # Optional: ["cusum", "pelt"]
) -> dict
```

### Python Function

```python
detect_schedule_changepoints(
    daily_hours: Sequence[float],
    dates: Sequence[date],
    methods: list[str] | None = None
) -> dict[str, ChangePointAnalysisResult]
```

### WorkloadSignalProcessor Methods

```python
processor.detect_change_points_cusum(
    series: np.ndarray,
    threshold: float = 5.0,
    drift: float = 0.0
) -> list[ChangePoint]

processor.detect_change_points_pelt(
    series: np.ndarray,
    penalty: float = 1.0,
    min_segment_length: int = 5
) -> list[ChangePoint]

processor.analyze_schedule_changepoints(
    ts: WorkloadTimeSeries,
    methods: list[str] | None = None
) -> dict[str, ChangePointAnalysisResult]
```

---

## Related Documentation

- [Signal Processing Research](../../research/SIGNAL_PROCESSING_SCHEDULE_ANALYSIS.md)
- [SOC Predictor (Early Warning)](../implementation/SOC_PREDICTOR_IMPLEMENTATION.md)
- [Shapley Values (Fair Workload)](./shapley_value_usage.md)
