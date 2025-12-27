# Frequency Lens: Spectral Analysis for Schedule Optimization

> **Cross-Disciplinary Origins**: Signal Processing, Seismology, Telecommunications
> **Module**: `backend/app/analytics/signal_processing.py`
> **Integration**: Holographic Hub visualization (Sessions 9-10)

---

## Table of Contents

1. [Overview](#overview)
2. [Why Frequency Domain Analysis?](#why-frequency-domain-analysis)
3. [Core Techniques](#core-techniques)
4. [STA/LTA Anomaly Detection](#stalta-anomaly-detection)
5. [Wavelet Analysis](#wavelet-analysis)
6. [Harmonic Analysis](#harmonic-analysis)
7. [Constraint Validation](#frequency-based-constraint-validation)
8. [Usage Examples](#usage-examples)
9. [Visualization Export](#visualization-export)
10. [Performance Considerations](#performance-considerations)

---

## Overview

The **Frequency Lens** provides a fundamentally different view of residency schedules by transforming time-domain workload data into the frequency domain. This reveals hidden patterns that are invisible in traditional time-series analysis:

- **Periodic Patterns**: Weekly, biweekly, and monthly rhythms
- **Anomalies**: Sudden changes using seismic detection algorithms
- **Constraint Violations**: Patterns too rapid for human endurance
- **Harmonic Resonances**: Interfering schedule patterns

### The "Lens" Metaphor

Just as different optical lenses reveal different aspects of light (UV, IR, polarization), the frequency lens reveals schedule structure that exists in the frequency domain:

| Domain | Reveals | Example |
|--------|---------|---------|
| **Time** | What happened when | "Dr. Smith worked 12 hours on Tuesday" |
| **Frequency** | What patterns exist | "Dr. Smith has a strong 7-day periodicity" |
| **Wavelet** | When patterns changed | "Weekly pattern broke down in Block 7" |

---

## Why Frequency Domain Analysis?

### Problem with Time-Domain Only

Traditional schedule analytics look at:
- Total hours per week
- Average daily workload
- Consecutive duty days

These miss **structural patterns**:

```
Time Domain View:
Day 1: 8h, Day 2: 12h, Day 3: 8h, Day 4: 12h, Day 5: 8h, Day 6: 12h, Day 7: 8h

What you see: Average 9.7h/day, max 12h
What you miss: Alternating pattern at 0.5 cycles/day
```

### Frequency Domain Reveals

The same data in frequency domain shows:
- **Strong 2-day period** (0.5 cycles/day) - Alternating heavy/light pattern
- **Missing 7-day period** - No weekly rest rhythm
- **No low-frequency trend** - Workload is stable overall

### Clinical Significance

Frequency patterns correlate with:

| Pattern | Frequency | Clinical Impact |
|---------|-----------|-----------------|
| Daily alternation | 0.5 cycles/day | Sleep disruption, circadian issues |
| Weekly rhythm | 1/7 cycles/day | Recovery time, ACGME compliance |
| Monthly cycles | 1/30 cycles/day | Block rotation effects |
| Missing rest period | High-frequency only | Burnout risk, fatigue accumulation |

---

## Core Techniques

### 1. Fast Fourier Transform (FFT)

The FFT decomposes a schedule into its constituent frequencies:

```
Workload(t) = A₀ + A₁·sin(2πf₁t + φ₁) + A₂·sin(2πf₂t + φ₂) + ...
```

Where:
- `A₀` = Average workload (DC component)
- `A₁, A₂, ...` = Amplitude of each frequency component
- `f₁, f₂, ...` = Frequencies (cycles per day)
- `φ₁, φ₂, ...` = Phase (when the pattern peaks)

**Key Outputs**:
- Dominant frequencies (strongest patterns)
- Periodicity detection (does a regular pattern exist?)
- Phase information (when patterns align)

### 2. Wavelet Transform

Wavelets provide **multi-resolution analysis** - different levels of detail at different scales:

| Level | Scale | Captures |
|-------|-------|----------|
| 1 | 2 days | Daily fluctuations |
| 2 | 4 days | Short-term patterns |
| 3 | 8 days | Weekly patterns |
| 4 | 16 days | Biweekly patterns |
| 5 | 32 days | Monthly patterns |

**Advantage over FFT**: Wavelets preserve time information. You can see **when** a pattern changed, not just **that** it exists.

### 3. Spectral Decomposition (STL)

Separates workload into:

```
Workload(t) = Trend(t) + Seasonal(t) + Residual(t)
```

- **Trend**: Long-term direction (increasing/decreasing workload)
- **Seasonal**: Regular repeating pattern (weekly cycle)
- **Residual**: Unexplained variation (emergencies, irregular events)

**Use Cases**:
- Identify if workload is trending up over time
- Quantify how strong the weekly pattern is
- Detect irregular days that don't fit the pattern

---

## STA/LTA Anomaly Detection

### Origin: Seismology

The **Short-Term Average / Long-Term Average** algorithm was developed for automatic earthquake detection in seismograms. It detects sudden changes in signal characteristics.

### How It Works

```
          LTA window (20 days)
    ←─────────────────────────────────→

    ┌─────────────────┬───────────────┐
    │ Long-term trend │  STA window   │
    │                 │   (5 days)    │
    └─────────────────┴───────────────┘
                              ↑
                         Current position

Ratio = STA / LTA

If Ratio > Threshold (e.g., 3.0):
    → ANOMALY DETECTED
```

### Interpretation for Schedules

| Ratio | Meaning | Action |
|-------|---------|--------|
| < 1.5 | Normal variation | None |
| 1.5-3.0 | Elevated but expected | Monitor |
| 3.0-5.0 | Significant change | Investigate |
| > 5.0 | Major event | Immediate review |

### Types of Detected Anomalies

1. **Workload Spike**: Sudden increase (e.g., covering for absent colleague)
2. **Workload Drop**: Sudden decrease (e.g., illness, cancelled procedures)
3. **Pattern Change**: Shift in regular pattern (e.g., rotation change)
4. **Rapid Alternation**: Too-frequent on/off switching

### Configuration

```python
processor = WorkloadSignalProcessor(
    sta_window=5,      # 5-day short-term average
    lta_window=20,     # 20-day long-term average
    sta_lta_threshold=3.0  # Trigger at 3x ratio
)
```

**Tuning Guidelines**:
- Shorter STA → More sensitive to brief spikes
- Longer LTA → More stable baseline, fewer false positives
- Lower threshold → More detections (including noise)
- Higher threshold → Only major events

---

## Wavelet Analysis

### Discrete Wavelet Transform (DWT)

Decomposes the signal into **approximation** (low-frequency trend) and **details** (high-frequency variations) at multiple scales.

```
Original Signal
     │
     ▼
┌────────────┐
│   Level 1  │ ──→ Detail 1 (daily fluctuations)
│   Decomp   │
└────────────┘
     │
     ▼
┌────────────┐
│   Level 2  │ ──→ Detail 2 (2-4 day patterns)
│   Decomp   │
└────────────┘
     │
     ▼
┌────────────┐
│   Level 3  │ ──→ Detail 3 (weekly patterns)
│   Decomp   │
└────────────┘
     │
     ▼
  Approximation (trend)
```

### Wavelet Selection

| Wavelet | Use Case | Properties |
|---------|----------|------------|
| **Haar** | Simple, step-like patterns | Fastest, least smooth |
| **Daubechies 4** | General purpose | Good balance of smoothness and localization |
| **Symlet 4** | Symmetric patterns | Better phase characteristics |
| **Coiflet** | Trend analysis | More vanishing moments |

**Recommended**: Daubechies 4 (`db4`) for most scheduling applications.

### Continuous Wavelet Transform (CWT)

Provides time-frequency representation (spectrogram-like):

```
Frequency ▲
          │  ░░░░░        ░░░░░░░░░      High-frequency activity
          │    ░░░░░░░░░░░░░░
          │      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     7-day pattern
          │        ▓▓▓▓▓▓▓▓▓▓▓▓
          │    ████████████████████████  Trend
          └────────────────────────────→ Time
             Week 1    Week 2    Week 3
```

**Interpretation**:
- Bright bands at specific frequencies = Strong periodic pattern
- Bands that fade = Pattern weakening
- Sudden bright spots = Transient events

---

## Harmonic Analysis

### What Are Harmonics?

If a schedule has a fundamental 7-day period, harmonics are patterns at:
- 7 days (fundamental)
- 3.5 days (2nd harmonic)
- 2.33 days (3rd harmonic)
- etc.

### Why Harmonics Matter

**Constructive Resonance**: When harmonics align in-phase, they reinforce:
```
7-day pattern peaks Monday
3.5-day pattern also peaks Monday
→ Extreme workload on Mondays
```

**Destructive Resonance**: When harmonics are anti-phase:
```
7-day pattern peaks Monday
3.5-day pattern troughs Monday
→ Erratic, unpredictable workload
```

### Total Harmonic Distortion (THD)

Measures how much harmonic content exists beyond the fundamental:

```
THD = sqrt(P₂ + P₃ + P₄ + ...) / P₁

Where Pₙ = power of nth harmonic
```

| THD | Interpretation |
|-----|----------------|
| < 0.1 | Very clean pattern |
| 0.1-0.3 | Normal variation |
| 0.3-0.5 | Significant harmonics |
| > 0.5 | Complex, multi-periodic pattern |

---

## Frequency-Based Constraint Validation

### Built-in Constraints

The system validates schedules against physiologically-based frequency limits:

| Constraint | Max Frequency | Min Period | Severity |
|------------|---------------|------------|----------|
| Minimum Rest | 1.0 cycle/day | 1 day | Error |
| Recovery Period | 0.5 cycle/day | 2 days | Warning |
| Weekly Rest (ACGME) | 1/7 cycle/day | 7 days | Error |

### Violation Detection

The algorithm:
1. Computes FFT of workload signal
2. Identifies frequency components above constraint limits
3. Checks if high-frequency components have significant power
4. Reports violations with location and severity

### Example Violation

```
CRITICAL: minimum_rest_period violation
  Detected frequency 0.85 cycles/day (period: 1.2 days)
  exceeds max 1.0 cycles/day
  Location: Days 14-21
  Description: Cannot alternate on/off faster than once per day
```

### Custom Constraints

```python
custom_constraint = FrequencyConstraint(
    name="post_call_recovery",
    max_frequency=0.33,  # Max 1 cycle per 3 days
    min_period_days=3.0,
    description="Minimum 2 days off after heavy call",
    severity="warning"
)

processor = WorkloadSignalProcessor(constraints=[custom_constraint])
```

---

## Usage Examples

### Basic Analysis

```python
from app.analytics.signal_processing import (
    WorkloadSignalProcessor,
    WorkloadTimeSeries,
)
from datetime import date, timedelta
import numpy as np

# Create sample data (90 days of daily hours)
dates = [date(2025, 1, 1) + timedelta(days=i) for i in range(90)]
hours = np.random.normal(8, 2, 90)  # Simulated workload

# Add weekly pattern
for i in range(90):
    if dates[i].weekday() in [5, 6]:  # Weekend
        hours[i] *= 0.5  # Reduced weekend work

# Create time series
ts = WorkloadTimeSeries(
    values=hours,
    dates=dates,
    person_id=uuid4(),
    units="hours"
)

# Initialize processor and analyze
processor = WorkloadSignalProcessor()
result = processor.analyze_workload_patterns(ts)

# Check for issues
for violation in result["constraint_violations"]:
    print(f"[{violation['severity']}] {violation['description']}")

for rec in result["recommendations"]:
    print(f"Recommendation: {rec}")
```

### Quick Anomaly Detection

```python
from app.analytics.signal_processing import detect_schedule_anomalies

# Detect anomalies with custom threshold
anomalies = detect_schedule_anomalies(
    daily_hours=[8, 8, 14, 8, 8, 16, 8, 8],  # Spike on days 3, 6
    dates=dates[:8],
    threshold=2.5  # More sensitive
)

for a in anomalies:
    print(f"{a['date']}: {a['type']} (severity: {a['severity']:.2f})")
```

### Extracting Specific Patterns

```python
# Get only the weekly pattern
dwt_result = processor.discrete_wavelet_transform(ts, level=4)

# Reconstruct with only weekly component (level 3)
weekly_pattern = processor.wavelet_reconstruct(
    dwt_result,
    keep_levels=[2]  # Level 3 ≈ 7-8 days
)

# Compare original vs weekly pattern
print(f"Weekly pattern strength: {np.std(weekly_pattern) / np.std(ts.values):.2%}")
```

### Filtering Noise

```python
# Apply adaptive filtering
filtered = processor.adaptive_filter(ts, method="savgol", window_size=7)

print(f"Noise reduction: {filtered['quality_metrics']['noise_reduction']:.2%}")
print(f"Correlation: {filtered['quality_metrics']['correlation_with_original']:.3f}")
```

---

## Visualization Export

### Holographic Format

The system exports data in a structured format for 3D visualization:

```json
{
  "version": "1.0",
  "export_type": "holographic_signal_analysis",
  "time_domain": {
    "dates": ["2025-01-01", "2025-01-02", ...],
    "values": [8.0, 9.5, 12.0, ...],
    "trend": [8.2, 8.3, 8.4, ...],
    "seasonal": [-0.2, 0.5, 1.0, ...],
    "residual": [0.0, 0.7, 2.6, ...]
  },
  "frequency_domain": {
    "frequencies": [0.01, 0.02, 0.03, ...],
    "magnitudes": [100, 50, 30, ...],
    "dominant_peaks": [
      {"frequency": 0.143, "period_days": 7.0, "magnitude": 100}
    ],
    "harmonics": [...],
    "resonances": [...]
  },
  "wavelet_domain": {
    "cwt": {
      "coefficients": [[...], [...], ...],
      "scales": [1, 2, 4, 8, ...],
      "power": [[...], [...], ...]
    }
  },
  "anomalies": [
    {"type": "workload_spike", "date": "2025-02-15", "severity": 0.8}
  ]
}
```

### Export Code

```python
from app.analytics.signal_processing import export_for_visualization

# Generate JSON for visualization
json_data = export_for_visualization(result, hours, dates)

# Save for holographic hub
with open("schedule_spectral_data.json", "w") as f:
    f.write(json_data)
```

---

## Performance Considerations

### Computational Complexity

| Operation | Complexity | Typical Time (90 days) |
|-----------|------------|------------------------|
| FFT | O(n log n) | < 1 ms |
| DWT | O(n) | < 1 ms |
| CWT | O(n × scales) | ~10 ms |
| STA/LTA | O(n) | < 1 ms |
| STL | O(n × iterations) | ~50 ms |
| Full Analysis | All above | ~100 ms |

### Memory Usage

| Data | Size (365 days) |
|------|-----------------|
| Time series | ~3 KB |
| FFT result | ~6 KB |
| CWT coefficients | ~100 KB |
| Full analysis result | ~200 KB |

### Optimization Tips

1. **Batch Processing**: Analyze multiple residents in parallel
2. **Caching**: Cache FFT/wavelet results for unchanging historical data
3. **Selective Analysis**: Run only needed analyses:
   ```python
   result = processor.analyze_workload_patterns(
       ts,
       analysis_types=["fft", "sta_lta"]  # Skip expensive CWT
   )
   ```
4. **Downsampling**: For long time series, consider weekly aggregation first

---

## Integration with Other Modules

### Burnout Fire Index

Feed frequency metrics to the Burnout Fire Index:

```python
from app.resilience.burnout_fire_index import BurnoutDangerRating

# Use spectral decomposition trend for velocity
spectral = result["spectral_decomposition"]
trend = spectral["trend"]
velocity = (trend[-7] - trend[-14]) / 7  # Trend slope over last week

rating = BurnoutDangerRating()
danger = rating.calculate_burnout_danger(
    resident_id=uuid,
    recent_hours=sum(hours[-14:]),
    monthly_load=sum(hours[-90:]) / 3,
    yearly_satisfaction=0.7,
    workload_velocity=velocity  # From frequency analysis
)
```

### Resilience Framework

Signal processing integrates with:
- **Homeostasis**: Detect oscillations around setpoint
- **SPC Monitoring**: Western Electric rules on residuals
- **Early Warning**: Seismic precursors in wavelet coefficients

---

## References

1. Mallat, S. (2009). *A Wavelet Tour of Signal Processing*, 3rd ed. Academic Press.
2. Allen, R.V. (1978). "Automatic earthquake recognition and timing from single traces." *Bulletin of the Seismological Society of America*.
3. Cleveland, R.B. et al. (1990). "STL: A Seasonal-Trend Decomposition Procedure Based on Loess." *Journal of Official Statistics*.
4. Oppenheim, A.V. & Schafer, R.W. (2010). *Discrete-Time Signal Processing*, 3rd ed. Pearson.
5. Van Wagner, C.E. (1987). "Development and Structure of the Canadian Forest Fire Weather Index System." *Forestry Technical Report 35*.

---

*Part of the Cross-Disciplinary Resilience Framework. See also: [Cross-Disciplinary Resilience](cross-disciplinary-resilience.md), [Burnout Fire Index](../resilience/burnout-fire-index.md)*
