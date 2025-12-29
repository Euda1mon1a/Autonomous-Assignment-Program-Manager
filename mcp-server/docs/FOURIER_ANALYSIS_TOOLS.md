# Fourier Analysis Tools for Schedule Periodicity Detection

## Overview

The Fourier Analysis MCP tools provide spectral analysis capabilities for detecting and analyzing periodic patterns in medical residency scheduling data. These tools use Fast Fourier Transform (FFT) to identify natural cycles in workload, swap patterns, absences, and other time-series metrics.

**Key Value Proposition**: Complements time crystal periodicity detection with frequency domain analysis, enabling data-driven schedule optimization that preserves natural cycles and aligns with ACGME regulatory windows.

## Scientific Background

### Fast Fourier Transform (FFT)

FFT decomposes a time-series signal into its constituent frequencies, revealing hidden periodic patterns that may not be obvious in the time domain.

**Applications in Scheduling:**
- Detect dominant work cycles (weekly, biweekly, monthly)
- Identify schedule complexity and predictability
- Verify alignment with ACGME compliance windows (7d, 14d, 28d)
- Measure schedule regularity for resident planning

### Shannon Entropy

Spectral entropy quantifies how "spread out" the frequency content is:
- **Low entropy**: Few dominant frequencies → Simple, predictable schedule
- **High entropy**: Many frequencies → Complex, chaotic schedule

## Available Tools

### 1. `detect_schedule_cycles_tool`

**Purpose**: Identify dominant periodic patterns in schedule metrics using FFT.

**Inputs**:
- `signal`: Time series data (e.g., daily workload hours, swap counts)
- `sampling_period_days`: Sampling interval in days (default: 1.0)
- `num_peaks`: Number of top frequencies to return (default: 5)

**Outputs**:
- `dominant_period_days`: Strongest detected cycle length
- `all_periods`: List of detected periods with power and interpretation
- `periodicity_detected`: Boolean flag for clear periodicity
- `recommendations`: Actionable guidance

**Example Use Cases**:

```python
# Detect workload cycles
daily_hours = [40, 45, 50, 48, 40, 0, 0, 42, 46, 50, 48, 38, 5, 0, ...]
result = await detect_schedule_cycles_tool(daily_hours)

if result.dominant_period_days:
    print(f"Strongest cycle: {result.dominant_period_days} days")
    # Output: "Strongest cycle: 7.2 days"

# Analyze swap frequency (weekly aggregates)
weekly_swaps = [2, 3, 1, 2, 5, 2, 1, 3, 2, 1, 4, 2, ...]
result = await detect_schedule_cycles_tool(
    weekly_swaps,
    sampling_period_days=7.0
)
```

**Interpretation Guide**:

| Detected Period | Interpretation |
|----------------|----------------|
| ~3.5 days | Half-week pattern (mid-week shifts) |
| ~7 days | Weekly cycle (aligns with ACGME 1-in-7 rule) |
| ~14 days | Biweekly pattern (alternating weekends) |
| ~21 days | Three-week rotation cycle |
| ~28 days | ACGME 4-week rolling average window |

### 2. `analyze_harmonic_resonance_tool`

**Purpose**: Check if natural schedule cycles align with ACGME regulatory windows.

**Inputs**:
- `signal`: Time series data
- `sampling_period_days`: Sampling interval (default: 1.0)

**Outputs**:
- `acgme_7d_alignment`: Weekly cycle alignment (0.0-1.0)
- `acgme_14d_alignment`: Biweekly cycle alignment (0.0-1.0)
- `acgme_28d_alignment`: 4-week window alignment (0.0-1.0)
- `overall_resonance`: Weighted average alignment
- `resonant_harmonics`: Frequencies aligned with ACGME
- `dissonant_frequencies`: Strong frequencies that conflict
- `health_status`: healthy/degraded/critical

**Example Use Cases**:

```python
# Check ACGME alignment of workload pattern
result = await analyze_harmonic_resonance_tool(daily_workload)

if result.overall_resonance > 0.7:
    print("✓ Schedule naturally aligns with ACGME cycles")
else:
    print("✗ ACGME alignment issues detected:")
    for rec in result.recommendations:
        print(f"  - {rec}")

# Inspect specific alignments
print(f"Weekly (7d) alignment: {result.acgme_7d_alignment:.2f}")
print(f"28-day window alignment: {result.acgme_28d_alignment:.2f}")
```

**Health Status Thresholds**:

| Overall Resonance | Health Status | Interpretation |
|-------------------|---------------|----------------|
| ≥ 0.7 | Healthy | Strong ACGME alignment |
| 0.4 - 0.7 | Degraded | Partial alignment, some conflicts |
| < 0.4 | Critical | Poor alignment, high compliance risk |

### 3. `calculate_spectral_entropy_tool`

**Purpose**: Measure schedule complexity and predictability via spectral entropy.

**Inputs**:
- `signal`: Time series data
- `sampling_period_days`: Sampling interval (default: 1.0)

**Outputs**:
- `spectral_entropy`: Shannon entropy 0.0-1.0 (normalized)
- `entropy_interpretation`: Human-readable explanation
- `signal_complexity`: simple/moderate/complex/chaotic
- `dominant_frequencies_count`: Number of significant components
- `frequency_concentration`: Inverse of entropy
- `predictability`: high/moderate/low/very low

**Example Use Cases**:

```python
# Assess schedule predictability
result = await calculate_spectral_entropy_tool(assignment_changes_daily)

if result.spectral_entropy > 0.8:
    print("⚠ Schedule is highly complex/chaotic")
    print("   Residents may find schedule unpredictable")
elif result.spectral_entropy < 0.3:
    print("✓ Schedule is highly regular/predictable")
    print("   Good for resident planning")

print(f"Complexity: {result.signal_complexity}")
print(f"Predictability: {result.predictability}")
```

**Entropy Interpretation**:

| Entropy Range | Complexity | Predictability | Typical Cause |
|--------------|------------|----------------|---------------|
| 0.0 - 0.3 | Simple | High | Single dominant frequency (e.g., pure weekly cycle) |
| 0.3 - 0.6 | Moderate | Moderate | Few periodic components (e.g., weekly + biweekly) |
| 0.6 - 0.8 | Complex | Low | Many frequency components (multiple overlapping rotations) |
| 0.8 - 1.0 | Chaotic | Very Low | Approaching white noise (irregular ad-hoc scheduling) |

## Integration with Time Crystal Framework

These Fourier tools complement the existing time crystal scheduling framework:

| Time Crystal Concept | Fourier Analysis Tool | Synergy |
|---------------------|----------------------|---------|
| **Subharmonic Detection** | `detect_schedule_cycles_tool` | FFT precisely identifies natural periods for anti-churn optimization |
| **ACGME Compliance** | `analyze_harmonic_resonance_tool` | Verifies schedule aligns with regulatory 7d/28d windows |
| **Rigidity Scoring** | `calculate_spectral_entropy_tool` | Low entropy → high rigidity (predictable, stable) |

**Workflow Example**:

```python
# 1. Detect natural cycles in current schedule
cycles = await detect_schedule_cycles_tool(current_workload)
print(f"Dominant period: {cycles.dominant_period_days} days")

# 2. Check ACGME alignment
resonance = await analyze_harmonic_resonance_tool(current_workload)
print(f"ACGME alignment: {resonance.overall_resonance:.2f}")

# 3. Assess complexity
entropy = await calculate_spectral_entropy_tool(current_workload)
print(f"Schedule complexity: {entropy.signal_complexity}")

# 4. Use insights for schedule regeneration
if cycles.dominant_period_days and cycles.dominant_period_days > 6.5:
    # Preserve weekly cycle in time crystal objective
    alpha = 0.4  # Higher rigidity weight
else:
    # Less rigid - allow more optimization
    alpha = 0.2
```

## Signal Preparation Best Practices

### 1. Sampling Rate Selection

- **Daily data** (most common): `sampling_period_days=1.0`
- **AM/PM blocks**: `sampling_period_days=0.5`
- **Weekly aggregates**: `sampling_period_days=7.0`

### 2. Minimum Signal Length

- **Absolute minimum**: 7 samples
- **Recommended**: ≥ 3× longest expected period
  - For weekly detection: ≥ 21 days
  - For monthly detection: ≥ 90 days

### 3. Data Quality

- **Avoid all-zero signals**: Tools return placeholder results
- **Handle missing data**: Interpolate or use median imputation
- **Remove outliers**: Extreme values can obscure patterns

### 4. Metric Selection

| Metric | Use Case | Sampling |
|--------|----------|----------|
| `total_hours_per_day` | Workload cycles | Daily |
| `swap_count_per_week` | Swap patterns | Weekly |
| `absence_rate_per_day` | Leave patterns | Daily |
| `assignment_changes_per_day` | Schedule churn | Daily |
| `night_shifts_per_week` | Call distribution | Weekly |

## Performance Considerations

- **FFT complexity**: O(n log n) where n = signal length
- **Typical runtime**: < 50ms for signals up to 365 samples
- **Memory**: Minimal (< 1 MB for typical schedule data)

## Limitations

1. **Edge Effects**: Short signals may have unreliable FFT results
2. **Non-stationary Signals**: FFT assumes stationarity (patterns don't change over time)
3. **Leap Seconds/DST**: Time zone transitions can introduce artifacts
4. **Synthetic Signals**: Randomly generated schedules may show false periodicities

## Troubleshooting

### "Signal too short" Error

**Cause**: Signal has < 7 samples
**Fix**: Aggregate data or use longer time window

### "Signal is all zeros" Error

**Cause**: Metric has no variation (e.g., all residents off)
**Fix**: Choose different metric or time period

### "No strong periodic patterns detected"

**Possible Causes**:
- Schedule is truly irregular
- Multiple overlapping periods cancel out
- Sampling rate too coarse

**Diagnostic Steps**:
1. Check spectral entropy - high entropy confirms irregularity
2. Try different sampling rates (daily vs weekly)
3. Inspect power spectrum manually for weak peaks

### Detected Period Doesn't Match Intuition

**Possible Causes**:
- Aliasing from coarse sampling
- Harmonics of true period (e.g., 14d detected instead of 7d)
- Multiple competing periods

**Diagnostic Steps**:
1. Check `all_periods` list for secondary peaks
2. Increase `num_peaks` to see more candidates
3. Cross-validate with time crystal autocorrelation tools

## API Reference

### Request Formats

All tools accept time-series data as `list[float]`:

```json
{
  "signal": [40.0, 45.0, 50.0, 48.0, 40.0, 0.0, 0.0],
  "sampling_period_days": 1.0,
  "num_peaks": 5
}
```

### Response Format Examples

**ScheduleCyclesResponse**:
```json
{
  "dominant_period_days": 7.1,
  "all_periods": [
    {
      "period_days": 7.1,
      "frequency_hz": 0.141,
      "power": 145.3,
      "relative_power": 1.0,
      "interpretation": "Weekly cycle (7-day ACGME 1-in-7 rule)"
    }
  ],
  "signal_length_days": 28,
  "mean_value": 38.5,
  "signal_std": 12.3,
  "periodicity_detected": true,
  "recommendations": [
    "Detected strong 7.1-day cycle - consider preserving in schedule regeneration"
  ]
}
```

## Future Enhancements

Potential additions to the Fourier analysis toolkit:

1. **Wavelet Analysis**: Multi-resolution decomposition for non-stationary signals
2. **Cross-Spectrum**: Compare periodicity between two metrics (workload vs swaps)
3. **Phase Analysis**: Detect time shifts between related cycles
4. **Confidence Intervals**: Bootstrap estimates for period detection uncertainty
5. **Anomaly Detection**: Flag periods with unexpected frequency content

## References

- **TIME_CRYSTAL_ANTI_CHURN.md**: Time crystal scheduling framework
- **cross-disciplinary-resilience.md**: Subharmonic detection patterns
- **CLAUDE.md Section 11**: Key concepts - Time Crystal Scheduling

## Support

For questions or issues with Fourier analysis tools:
- Check troubleshooting section above
- Review test cases in `tests/test_fourier_analysis_tools.py`
- Consult MCP tool docstrings for detailed parameter descriptions
