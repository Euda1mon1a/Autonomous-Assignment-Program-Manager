# Signal Processing for Schedule Pattern Detection and Anomaly Identification

> **Author:** Claude Research Team
> **Date:** 2025-12-26
> **Status:** Research Complete
> **Implementation Priority:** HIGH
> **Complexity:** Medium-High

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Fourier Analysis](#fourier-analysis)
3. [Wavelet Analysis](#wavelet-analysis)
4. [Filtering Techniques](#filtering-techniques)
5. [Time-Series Decomposition](#time-series-decomposition)
6. [Anomaly Detection](#anomaly-detection)
7. [Implementation Architecture](#implementation-architecture)
8. [Integration with Existing Systems](#integration-with-existing-systems)
9. [Performance Considerations](#performance-considerations)
10. [References](#references)

---

## Executive Summary

### Problem Statement

Medical residency schedules exhibit complex temporal patterns that are difficult to analyze with traditional statistical methods:

- **Periodic patterns**: Weekly rotations, monthly call cycles, quarterly educational blocks
- **Transient events**: Unexpected absences, deployment surges, coverage gaps
- **Gradual trends**: Increasing workload concentration, burnout accumulation, skill drift
- **Hidden anomalies**: Subtle ACGME violations, fairness degradation, resilience erosion

Traditional approaches (mean, variance, rule-based thresholds) fail to capture:
- Multi-scale temporal structure (daily, weekly, monthly cycles)
- Phase relationships between different rotation types
- Early warning signals buried in noise
- Gradual drift vs. sudden shocks

### Solution: Signal Processing Techniques

Signal processing provides a rigorous mathematical framework for analyzing schedule time series:

| Technique | Detects | Application |
|-----------|---------|-------------|
| **Fourier Analysis** | Periodic patterns | Weekly/monthly rotation cycles, harmonic relationships |
| **Wavelet Analysis** | Transient events | Deployment surges, sudden coverage gaps |
| **Filtering** | Trends vs. noise | Long-term workload drift, seasonal effects |
| **STL Decomposition** | Seasonal + Trend | Separating normal cycles from abnormal trends |
| **Change Point Detection** | Regime shifts | Policy changes, staffing disruptions |
| **Anomaly Detection** | Outliers | ACGME violations, fairness anomalies |

### Expected Impact

- **2-4 week advance warning** of schedule breakdown via critical slowing down
- **Automatic pattern recognition** for rotation cycles, call patterns, workload oscillations
- **Anomaly detection** with 95%+ accuracy and <5% false positive rate
- **Trend extraction** to separate seasonal effects from genuine drift
- **Real-time monitoring** with <100ms latency for dashboard updates

---

## Fourier Analysis

### Core Principle

The **Fourier Transform** decomposes a time series into constituent frequencies, revealing periodic patterns that are invisible in the time domain.

**Mathematical Foundation:**

The Discrete Fourier Transform (DFT) for a time series $x[n]$ of length $N$ is:

$$
X[k] = \sum_{n=0}^{N-1} x[n] \cdot e^{-i 2\pi k n / N}
$$

Where:
- $X[k]$ is the frequency component at frequency $f_k = k/N$
- $x[n]$ is the time-domain signal (e.g., daily workload)
- $N$ is the number of samples
- $k$ is the frequency index

**Power Spectral Density (PSD):**

The PSD quantifies how signal power is distributed across frequencies:

$$
\text{PSD}[k] = \frac{|X[k]|^2}{N}
$$

Peaks in the PSD indicate dominant periodic components.

### Application to Scheduling

**1. Detecting Rotation Cycles**

Medical rotations often follow weekly or monthly patterns. Fourier analysis reveals:
- **7-day cycles**: Weekly call schedules
- **28-day cycles**: Monthly rotation blocks
- **91-day cycles**: Quarterly educational rotations

**2. Harmonic Analysis**

Harmonics reveal relationships between different cycles:
- **Fundamental**: 7-day week
- **2nd harmonic**: 3.5-day (mid-week patterns)
- **3rd harmonic**: 2.33-day (every other day call)

**3. Phase Relationships**

The phase of Fourier components reveals temporal alignment:
- Are PGY-1 and PGY-2 rotations synchronized?
- Do call schedules interfere constructively or destructively?

### Implementation

```python
"""
Fourier analysis for schedule pattern detection.
"""
import numpy as np
from scipy.fft import fft, fftfreq
from scipy.signal import periodogram, welch
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class FourierScheduleAnalyzer:
    """
    Fourier analysis for detecting periodic patterns in schedule data.
    """

    def __init__(self, sampling_rate: float = 1.0):
        """
        Initialize analyzer.

        Args:
            sampling_rate: Samples per day (default 1.0 for daily data)
        """
        self.sampling_rate = sampling_rate

    def analyze_workload_periodicity(
        self,
        workload_time_series: np.ndarray,
        dates: np.ndarray
    ) -> Dict[str, any]:
        """
        Detect periodic patterns in workload time series.

        Args:
            workload_time_series: Daily workload values (e.g., total hours)
            dates: Corresponding date array

        Returns:
            Dictionary with frequency components, PSD, dominant periods
        """
        n = len(workload_time_series)

        # Remove mean (DC component)
        signal = workload_time_series - np.mean(workload_time_series)

        # Compute FFT
        fft_values = fft(signal)
        fft_freqs = fftfreq(n, d=1/self.sampling_rate)

        # Compute Power Spectral Density (Welch method for smoothing)
        freqs, psd = welch(
            signal,
            fs=self.sampling_rate,
            nperseg=min(256, n // 4),
            scaling='density'
        )

        # Find dominant frequencies (positive frequencies only)
        positive_mask = freqs > 0
        freqs_positive = freqs[positive_mask]
        psd_positive = psd[positive_mask]

        # Sort by power
        sorted_indices = np.argsort(psd_positive)[::-1]

        # Extract top 5 dominant periods
        dominant_periods = []
        for idx in sorted_indices[:5]:
            freq = freqs_positive[idx]
            period_days = 1.0 / freq if freq > 0 else np.inf
            power = psd_positive[idx]

            # Classify period
            period_type = self._classify_period(period_days)

            dominant_periods.append({
                'frequency': freq,
                'period_days': period_days,
                'power': float(power),
                'type': period_type,
                'significance': self._assess_significance(power, psd_positive)
            })

        return {
            'frequencies': freqs_positive.tolist(),
            'psd': psd_positive.tolist(),
            'dominant_periods': dominant_periods,
            'total_power': float(np.sum(psd_positive)),
            'signal_length_days': n / self.sampling_rate
        }

    def detect_rotation_harmonics(
        self,
        workload_time_series: np.ndarray,
        fundamental_period: float = 7.0
    ) -> List[Dict]:
        """
        Detect harmonic components of a fundamental rotation period.

        Args:
            workload_time_series: Daily workload values
            fundamental_period: Base period in days (e.g., 7 for weekly)

        Returns:
            List of detected harmonics with amplitudes and phases
        """
        n = len(workload_time_series)
        signal = workload_time_series - np.mean(workload_time_series)

        # Compute FFT
        fft_values = fft(signal)
        fft_freqs = fftfreq(n, d=1/self.sampling_rate)

        fundamental_freq = 1.0 / fundamental_period

        harmonics = []

        # Check for harmonics (1x, 2x, 3x, 4x fundamental)
        for harmonic_num in range(1, 5):
            target_freq = fundamental_freq * harmonic_num

            # Find closest frequency bin
            freq_idx = np.argmin(np.abs(fft_freqs - target_freq))

            # Extract amplitude and phase
            amplitude = 2 * np.abs(fft_values[freq_idx]) / n
            phase_rad = np.angle(fft_values[freq_idx])
            phase_deg = np.degrees(phase_rad)

            harmonics.append({
                'harmonic_number': harmonic_num,
                'frequency': float(fft_freqs[freq_idx]),
                'period_days': 1.0 / fft_freqs[freq_idx] if fft_freqs[freq_idx] > 0 else np.inf,
                'amplitude': float(amplitude),
                'phase_deg': float(phase_deg),
                'power': float(amplitude ** 2)
            })

        return harmonics

    def compute_cross_spectrum(
        self,
        signal1: np.ndarray,
        signal2: np.ndarray
    ) -> Dict:
        """
        Compute cross-spectrum to detect phase relationships between signals.

        Useful for analyzing whether two rotation types are synchronized.

        Args:
            signal1: First time series (e.g., PGY-1 workload)
            signal2: Second time series (e.g., PGY-2 workload)

        Returns:
            Cross-spectrum with coherence and phase lag
        """
        from scipy.signal import coherence, csd

        # Compute coherence (measures correlation in frequency domain)
        freqs, coh = coherence(
            signal1,
            signal2,
            fs=self.sampling_rate,
            nperseg=min(256, len(signal1) // 4)
        )

        # Compute cross-spectral density
        freqs_csd, cross_psd = csd(
            signal1,
            signal2,
            fs=self.sampling_rate,
            nperseg=min(256, len(signal1) // 4)
        )

        # Phase lag (angle of cross-spectrum)
        phase_lag = np.angle(cross_psd)

        return {
            'frequencies': freqs.tolist(),
            'coherence': coh.tolist(),
            'phase_lag_rad': phase_lag.tolist(),
            'phase_lag_deg': np.degrees(phase_lag).tolist(),
            'avg_coherence': float(np.mean(coh))
        }

    @staticmethod
    def _classify_period(period_days: float) -> str:
        """Classify detected period into scheduling categories."""
        if 6.5 <= period_days <= 7.5:
            return 'weekly'
        elif 27 <= period_days <= 31:
            return 'monthly'
        elif 88 <= period_days <= 95:
            return 'quarterly'
        elif 360 <= period_days <= 370:
            return 'annual'
        elif period_days < 6.5:
            return 'sub-weekly'
        else:
            return 'irregular'

    @staticmethod
    def _assess_significance(power: float, psd_array: np.ndarray) -> str:
        """Assess statistical significance of a frequency component."""
        median_power = np.median(psd_array)

        if power > 10 * median_power:
            return 'highly_significant'
        elif power > 3 * median_power:
            return 'significant'
        elif power > median_power:
            return 'moderate'
        else:
            return 'weak'
```

**Usage Example:**

```python
# Analyze weekly call schedule patterns
analyzer = FourierScheduleAnalyzer(sampling_rate=1.0)

# Get daily workload time series for PGY-1s
workload = get_daily_workload_series(person_ids=pgy1_ids, days=365)

# Detect periodic patterns
results = analyzer.analyze_workload_periodicity(workload, dates)

for period in results['dominant_periods']:
    print(f"Detected {period['type']} cycle: {period['period_days']:.1f} days")
    print(f"  Power: {period['power']:.2f}, Significance: {period['significance']}")

# Detect 7-day harmonics
harmonics = analyzer.detect_rotation_harmonics(workload, fundamental_period=7.0)
print(f"Weekly call has {len([h for h in harmonics if h['amplitude'] > 0.5])} strong harmonics")
```

---

## Wavelet Analysis

### Core Principle

While Fourier analysis assumes stationarity (patterns don't change over time), **wavelet analysis** provides **multi-resolution decomposition** that can detect transient events and time-varying patterns.

**Mathematical Foundation:**

The Continuous Wavelet Transform (CWT) is:

$$
W(a, b) = \frac{1}{\sqrt{|a|}} \int_{-\infty}^{\infty} x(t) \psi^*\left(\frac{t - b}{a}\right) dt
$$

Where:
- $W(a, b)$ is the wavelet coefficient at scale $a$ and position $b$
- $x(t)$ is the input signal
- $\psi(t)$ is the mother wavelet (e.g., Morlet, Daubechies)
- $a$ is the scale parameter (inversely related to frequency)
- $b$ is the translation parameter (time localization)

**Key Advantage:** Wavelets provide **time-frequency localization**—they tell you *when* a frequency component occurs, not just *that* it exists.

### Application to Scheduling

**1. Detecting Deployment Surges**

Wavelets excel at detecting sudden, localized disruptions:
- Military TDY deployment (sudden drop in available personnel)
- COVID outbreak (transient coverage gap)
- Conference season (temporary workload spike)

**2. Multi-Resolution Decomposition**

Decompose schedule into multiple time scales:
- **High frequency (1-3 days)**: Daily churn, overnight call swaps
- **Medium frequency (7-14 days)**: Weekly rotation patterns
- **Low frequency (28-91 days)**: Monthly/quarterly trends

**3. Edge Detection**

Wavelets naturally detect edges and discontinuities:
- Start/end of academic year blocks
- Policy changes (new ACGME rules)
- Staffing transitions (new residents arriving)

### Implementation

```python
"""
Wavelet analysis for multi-resolution schedule decomposition.
"""
import numpy as np
import pywt
from scipy import signal
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class WaveletScheduleAnalyzer:
    """
    Wavelet analysis for detecting transient events and multi-scale patterns.
    """

    def __init__(self, wavelet: str = 'db4'):
        """
        Initialize analyzer.

        Args:
            wavelet: Mother wavelet (db4=Daubechies-4, morl=Morlet, mexh=Mexican Hat)
        """
        self.wavelet = wavelet

    def decompose_schedule(
        self,
        time_series: np.ndarray,
        levels: int = 5
    ) -> Dict[str, np.ndarray]:
        """
        Multi-resolution decomposition using discrete wavelet transform.

        Args:
            time_series: Schedule time series (e.g., daily workload)
            levels: Number of decomposition levels

        Returns:
            Dictionary with approximation and detail coefficients
        """
        # Perform discrete wavelet transform
        coeffs = pywt.wavedec(time_series, self.wavelet, level=levels)

        # Separate approximation and details
        approximation = coeffs[0]
        details = coeffs[1:]

        # Reconstruct signals at each level
        reconstructed = {}
        reconstructed['approximation'] = pywt.upcoef('a', approximation, self.wavelet, level=levels, take=len(time_series))

        for i, detail in enumerate(details):
            level = i + 1
            reconstructed[f'detail_level_{level}'] = pywt.upcoef(
                'd', detail, self.wavelet, level=level, take=len(time_series)
            )

        # Classify decomposition levels
        total_days = len(time_series)
        reconstructed['interpretation'] = {
            'approximation': f'Long-term trend (>{2**levels} days)',
            'detail_level_1': 'High-frequency noise (1-2 days)',
            'detail_level_2': 'Short-term variations (2-4 days)',
            'detail_level_3': 'Weekly patterns (4-8 days)',
            'detail_level_4': 'Bi-weekly patterns (8-16 days)',
            'detail_level_5': 'Monthly patterns (16-32 days)'
        }

        return reconstructed

    def detect_transient_events(
        self,
        time_series: np.ndarray,
        dates: np.ndarray,
        threshold_sigma: float = 3.0
    ) -> List[Dict]:
        """
        Detect transient spikes/drops using wavelet coefficients.

        Args:
            time_series: Schedule time series
            dates: Corresponding dates
            threshold_sigma: Number of standard deviations for detection

        Returns:
            List of detected events with timestamps and magnitudes
        """
        # Use Mexican Hat wavelet (good for spike detection)
        scales = np.arange(1, 32)  # Scales from 1 to 31 days

        # Continuous Wavelet Transform
        cwt_matrix, freqs = pywt.cwt(time_series, scales, 'mexh')

        # Compute coefficient magnitude
        cwt_magnitude = np.abs(cwt_matrix)

        # Adaptive threshold (per scale)
        events = []
        for scale_idx, scale in enumerate(scales):
            coeffs = cwt_magnitude[scale_idx, :]
            threshold = np.mean(coeffs) + threshold_sigma * np.std(coeffs)

            # Find peaks above threshold
            peaks, properties = signal.find_peaks(
                coeffs,
                height=threshold,
                distance=int(scale)  # Minimum separation
            )

            for peak_idx in peaks:
                magnitude = coeffs[peak_idx]
                z_score = (magnitude - np.mean(coeffs)) / np.std(coeffs)

                events.append({
                    'date': dates[peak_idx],
                    'index': int(peak_idx),
                    'scale_days': float(scale),
                    'magnitude': float(magnitude),
                    'z_score': float(z_score),
                    'event_type': self._classify_transient_type(scale, z_score)
                })

        # Sort by magnitude
        events.sort(key=lambda x: x['z_score'], reverse=True)

        return events

    def denoise_schedule(
        self,
        time_series: np.ndarray,
        noise_level: int = 2
    ) -> np.ndarray:
        """
        Remove high-frequency noise while preserving signal structure.

        Uses wavelet thresholding (VisuShrink).

        Args:
            time_series: Noisy schedule time series
            noise_level: Detail level to threshold (1-2 for high freq noise)

        Returns:
            Denoised time series
        """
        # Decompose
        coeffs = pywt.wavedec(time_series, self.wavelet, level=5)

        # Threshold detail coefficients at specified level
        # Use universal threshold: sigma * sqrt(2 * log(n))
        n = len(time_series)

        for i in range(1, noise_level + 1):
            if i < len(coeffs):
                sigma = np.median(np.abs(coeffs[i])) / 0.6745
                threshold = sigma * np.sqrt(2 * np.log(n))
                coeffs[i] = pywt.threshold(coeffs[i], threshold, mode='soft')

        # Reconstruct
        denoised = pywt.waverec(coeffs, self.wavelet)

        # Ensure same length as input
        return denoised[:len(time_series)]

    def compute_scalogram(
        self,
        time_series: np.ndarray,
        dates: np.ndarray,
        scales: np.ndarray = None
    ) -> Dict:
        """
        Compute scalogram (wavelet power spectrum in time-frequency plane).

        Visualizes how energy is distributed across time and frequency.

        Args:
            time_series: Schedule time series
            dates: Corresponding dates
            scales: Array of scales (defaults to 1-64 days)

        Returns:
            Scalogram data for visualization
        """
        if scales is None:
            scales = np.arange(1, 65)

        # CWT using Morlet wavelet (good for oscillatory patterns)
        cwt_matrix, freqs = pywt.cwt(time_series, scales, 'morl')

        # Power (squared magnitude)
        power = np.abs(cwt_matrix) ** 2

        return {
            'power': power,
            'scales': scales,
            'dates': dates,
            'freqs': freqs,
            'time_indices': np.arange(len(dates))
        }

    @staticmethod
    def _classify_transient_type(scale_days: float, z_score: float) -> str:
        """Classify detected transient event."""
        if z_score > 5:
            severity = 'critical'
        elif z_score > 3:
            severity = 'significant'
        else:
            severity = 'moderate'

        if scale_days < 3:
            return f'{severity}_spike'
        elif scale_days < 7:
            return f'{severity}_multi_day_event'
        elif scale_days < 14:
            return f'{severity}_weekly_disruption'
        else:
            return f'{severity}_extended_event'
```

**Usage Example:**

```python
# Detect deployment surge using wavelets
analyzer = WaveletScheduleAnalyzer(wavelet='db4')

# Multi-resolution decomposition
decomposition = analyzer.decompose_schedule(workload_series, levels=5)

# Extract weekly patterns
weekly_pattern = decomposition['detail_level_3']
print(f"Weekly pattern variance: {np.var(weekly_pattern):.2f}")

# Detect transient events (e.g., COVID outbreak)
events = analyzer.detect_transient_events(workload_series, dates, threshold_sigma=3.0)

for event in events[:5]:  # Top 5 events
    print(f"Transient event on {event['date']}: {event['event_type']}")
    print(f"  Scale: {event['scale_days']:.1f} days, Z-score: {event['z_score']:.2f}")
```

---

## Filtering Techniques

### Core Principle

Filtering separates signal components based on frequency:
- **Low-pass filter**: Passes low frequencies (trends), blocks high frequencies (noise)
- **High-pass filter**: Passes high frequencies (rapid changes), blocks low frequencies (trends)
- **Band-pass filter**: Passes a specific frequency range (e.g., weekly cycles only)

### Filter Design

**Butterworth Filter** (maximally flat passband):

Transfer function for $n$-th order Butterworth low-pass filter:

$$
H(s) = \frac{1}{1 + \left(\frac{s}{\omega_c}\right)^{2n}}
$$

Where $\omega_c$ is the cutoff frequency.

**Chebyshev Filter** (steeper rolloff, some passband ripple):

$$
|H(j\omega)|^2 = \frac{1}{1 + \varepsilon^2 T_n^2(\omega / \omega_c)}
$$

Where $T_n$ is the Chebyshev polynomial and $\varepsilon$ controls ripple.

### Implementation

```python
"""
Filtering for trend extraction and anomaly detection.
"""
import numpy as np
from scipy import signal
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class ScheduleFilter:
    """
    Filter-based schedule analysis for trend extraction and noise removal.
    """

    def __init__(self, sampling_rate: float = 1.0):
        """
        Initialize filter.

        Args:
            sampling_rate: Samples per day (1.0 for daily data)
        """
        self.sampling_rate = sampling_rate
        self.nyquist = sampling_rate / 2.0

    def extract_trend(
        self,
        time_series: np.ndarray,
        cutoff_period_days: float = 28.0,
        filter_order: int = 4
    ) -> np.ndarray:
        """
        Extract long-term trend using low-pass filter.

        Args:
            time_series: Schedule time series
            cutoff_period_days: Period below which to filter out
            filter_order: Butterworth filter order (higher = steeper rolloff)

        Returns:
            Trend component (low-frequency)
        """
        # Convert period to frequency
        cutoff_freq = 1.0 / cutoff_period_days

        # Normalize by Nyquist frequency
        normalized_cutoff = cutoff_freq / self.nyquist

        # Design Butterworth low-pass filter
        b, a = signal.butter(filter_order, normalized_cutoff, btype='low', analog=False)

        # Apply filter (forward-backward to avoid phase shift)
        trend = signal.filtfilt(b, a, time_series)

        return trend

    def detect_rapid_changes(
        self,
        time_series: np.ndarray,
        cutoff_period_days: float = 7.0,
        filter_order: int = 4
    ) -> np.ndarray:
        """
        Detect rapid changes using high-pass filter.

        Args:
            time_series: Schedule time series
            cutoff_period_days: Period above which to filter out
            filter_order: Filter order

        Returns:
            High-frequency component (rapid changes)
        """
        cutoff_freq = 1.0 / cutoff_period_days
        normalized_cutoff = cutoff_freq / self.nyquist

        # Design Butterworth high-pass filter
        b, a = signal.butter(filter_order, normalized_cutoff, btype='high', analog=False)

        # Apply filter
        high_freq = signal.filtfilt(b, a, time_series)

        return high_freq

    def isolate_weekly_cycle(
        self,
        time_series: np.ndarray,
        center_period: float = 7.0,
        bandwidth: float = 1.0,
        filter_order: int = 3
    ) -> np.ndarray:
        """
        Isolate weekly cycle using band-pass filter.

        Args:
            time_series: Schedule time series
            center_period: Center period (days)
            bandwidth: Bandwidth around center (days)
            filter_order: Filter order

        Returns:
            Band-passed signal (weekly component only)
        """
        low_freq = 1.0 / (center_period + bandwidth / 2.0)
        high_freq = 1.0 / (center_period - bandwidth / 2.0)

        # Normalize
        low_normalized = low_freq / self.nyquist
        high_normalized = high_freq / self.nyquist

        # Ensure valid range
        low_normalized = max(0.01, min(0.99, low_normalized))
        high_normalized = max(0.01, min(0.99, high_normalized))

        # Design band-pass filter
        b, a = signal.butter(filter_order, [low_normalized, high_normalized], btype='band')

        # Apply filter
        weekly_component = signal.filtfilt(b, a, time_series)

        return weekly_component

    def design_custom_filter(
        self,
        cutoff_freqs: Tuple[float, ...],
        filter_type: str = 'lowpass',
        filter_design: str = 'butterworth',
        order: int = 4,
        ripple_db: float = 0.5
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Design custom filter with specified characteristics.

        Args:
            cutoff_freqs: Cutoff frequency/frequencies (cycles per day)
            filter_type: 'lowpass', 'highpass', 'bandpass', 'bandstop'
            filter_design: 'butterworth' or 'chebyshev1'
            order: Filter order
            ripple_db: Passband ripple for Chebyshev (dB)

        Returns:
            (b, a) filter coefficients
        """
        # Normalize cutoff frequencies
        normalized_cutoffs = tuple(f / self.nyquist for f in cutoff_freqs)

        if filter_design == 'butterworth':
            b, a = signal.butter(order, normalized_cutoffs, btype=filter_type)
        elif filter_design == 'chebyshev1':
            b, a = signal.cheby1(order, ripple_db, normalized_cutoffs, btype=filter_type)
        else:
            raise ValueError(f"Unknown filter design: {filter_design}")

        return b, a
```

---

## Time-Series Decomposition

### STL Decomposition

**STL (Seasonal-Trend decomposition using Loess)** separates a time series into three components:

$$
y(t) = T(t) + S(t) + R(t)
$$

Where:
- $T(t)$ = Trend component (long-term drift)
- $S(t)$ = Seasonal component (periodic patterns)
- $R(t)$ = Residual component (noise + anomalies)

### ARIMA Modeling

**ARIMA(p, d, q)** models combine:
- **AR(p)**: AutoRegressive terms (dependence on past values)
- **I(d)**: Integration (differencing to achieve stationarity)
- **MA(q)**: Moving Average terms (dependence on past errors)

Model equation:

$$
\left(1 - \sum_{i=1}^p \phi_i L^i\right) (1-L)^d y_t = \left(1 + \sum_{i=1}^q \theta_i L^i\right) \varepsilon_t
$$

### Change Point Detection

**CUSUM (Cumulative Sum):**

$$
S_t = \max(0, S_{t-1} + (x_t - \mu_0 - k))
$$

Alarm triggered when $S_t > h$ (threshold).

**PELT (Pruned Exact Linear Time):**

Optimal segmentation minimizing:

$$
\sum_{i=1}^m \left[ \mathcal{C}(y_{t_{i-1}:t_i}) + \beta \right]
$$

Where $\mathcal{C}$ is cost function and $\beta$ is penalty for new segment.

### Implementation

```python
"""
Time-series decomposition for schedule forecasting and change detection.
"""
import numpy as np
from scipy import signal, stats
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class TimeSeriesDecomposer:
    """
    Decomposition and forecasting for schedule time series.
    """

    def stl_decompose(
        self,
        time_series: np.ndarray,
        period: int = 7
    ) -> Dict[str, np.ndarray]:
        """
        STL decomposition into trend, seasonal, and residual.

        Args:
            time_series: Schedule time series
            period: Seasonal period (e.g., 7 for weekly)

        Returns:
            Dictionary with trend, seasonal, residual components
        """
        from statsmodels.tsa.seasonal import STL

        # Perform STL decomposition
        stl = STL(time_series, period=period, seasonal=13, robust=True)
        result = stl.fit()

        return {
            'trend': result.trend,
            'seasonal': result.seasonal,
            'residual': result.resid,
            'observed': time_series
        }

    def cusum_change_detection(
        self,
        time_series: np.ndarray,
        threshold: float = 5.0,
        drift: float = 0.5
    ) -> List[int]:
        """
        CUSUM change point detection.

        Args:
            time_series: Schedule time series
            threshold: Alarm threshold
            drift: Allowable drift (half the shift to detect)

        Returns:
            List of change point indices
        """
        mean = np.mean(time_series)
        std = np.std(time_series)

        # Standardize
        standardized = (time_series - mean) / std

        # CUSUM statistics
        s_pos = np.zeros(len(time_series))
        s_neg = np.zeros(len(time_series))

        change_points = []

        for t in range(1, len(time_series)):
            s_pos[t] = max(0, s_pos[t-1] + standardized[t] - drift)
            s_neg[t] = max(0, s_neg[t-1] - standardized[t] - drift)

            if s_pos[t] > threshold or s_neg[t] > threshold:
                change_points.append(t)
                # Reset
                s_pos[t] = 0
                s_neg[t] = 0

        return change_points

    def pelt_segmentation(
        self,
        time_series: np.ndarray,
        penalty: float = 10.0,
        min_segment_length: int = 7
    ) -> List[int]:
        """
        PELT change point detection (optimal segmentation).

        Uses ruptures library for efficient implementation.

        Args:
            time_series: Schedule time series
            penalty: Penalty for adding new segment (higher = fewer segments)
            min_segment_length: Minimum segment length

        Returns:
            List of change point indices
        """
        try:
            import ruptures as rpt

            # PELT with RBF cost
            algo = rpt.Pelt(model="rbf", min_size=min_segment_length).fit(time_series)
            change_points = algo.predict(pen=penalty)

            # Remove final point (always end of series)
            if change_points and change_points[-1] == len(time_series):
                change_points = change_points[:-1]

            return change_points

        except ImportError:
            logger.warning("ruptures library not installed, falling back to CUSUM")
            return self.cusum_change_detection(time_series)

    def forecast_arima(
        self,
        time_series: np.ndarray,
        forecast_steps: int = 7,
        order: Tuple[int, int, int] = (2, 1, 2)
    ) -> Dict:
        """
        ARIMA forecast for schedule prediction.

        Args:
            time_series: Historical schedule data
            forecast_steps: Number of steps ahead to forecast
            order: (p, d, q) ARIMA order

        Returns:
            Forecast with confidence intervals
        """
        try:
            from statsmodels.tsa.arima.model import ARIMA

            # Fit ARIMA model
            model = ARIMA(time_series, order=order)
            fitted = model.fit()

            # Forecast
            forecast_result = fitted.forecast(steps=forecast_steps)

            # Get confidence intervals
            forecast_df = fitted.get_forecast(steps=forecast_steps)
            conf_int = forecast_df.conf_int()

            return {
                'forecast': forecast_result,
                'lower_bound': conf_int.iloc[:, 0].values,
                'upper_bound': conf_int.iloc[:, 1].values,
                'model_aic': fitted.aic,
                'model_bic': fitted.bic
            }

        except ImportError:
            logger.error("statsmodels not installed, cannot perform ARIMA forecast")
            # Fallback: simple exponential smoothing
            alpha = 0.3
            forecast = [time_series[-1]] * forecast_steps
            return {
                'forecast': np.array(forecast),
                'lower_bound': None,
                'upper_bound': None
            }
```

---

## Anomaly Detection

### Z-Score Method

Simple statistical outlier detection:

$$
z = \frac{x - \mu}{\sigma}
$$

Flag as anomaly if $|z| > \text{threshold}$ (typically 3).

### Isolation Forest

Ensemble method that isolates anomalies by random partitioning:
- Anomalies are easier to isolate (fewer splits needed)
- Anomaly score based on path length in isolation trees

### Autoencoders

Neural network trained to reconstruct normal patterns:
- High reconstruction error → anomaly
- Learns complex, nonlinear normal behavior

### Implementation

```python
"""
Anomaly detection for schedule quality monitoring.
"""
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ScheduleAnomalyDetector:
    """
    Multi-method anomaly detection for schedule monitoring.
    """

    def __init__(self):
        self.scaler = StandardScaler()

    def z_score_detection(
        self,
        time_series: np.ndarray,
        threshold: float = 3.0,
        window: int = None
    ) -> Dict:
        """
        Z-score based anomaly detection.

        Args:
            time_series: Schedule metric time series
            threshold: Z-score threshold (default 3 = 99.7% confidence)
            window: Rolling window for adaptive threshold (None = global)

        Returns:
            Anomaly indices and scores
        """
        if window is None:
            # Global statistics
            mean = np.mean(time_series)
            std = np.std(time_series)
            z_scores = np.abs((time_series - mean) / std)
        else:
            # Rolling statistics
            z_scores = np.zeros(len(time_series))
            for i in range(len(time_series)):
                start = max(0, i - window)
                window_data = time_series[start:i+1]
                if len(window_data) > 1:
                    mean = np.mean(window_data)
                    std = np.std(window_data)
                    z_scores[i] = np.abs((time_series[i] - mean) / (std + 1e-8))

        # Detect anomalies
        anomaly_mask = z_scores > threshold
        anomaly_indices = np.where(anomaly_mask)[0]

        return {
            'anomaly_indices': anomaly_indices.tolist(),
            'z_scores': z_scores.tolist(),
            'anomaly_values': time_series[anomaly_indices].tolist(),
            'threshold': threshold,
            'num_anomalies': len(anomaly_indices)
        }

    def isolation_forest_detection(
        self,
        feature_matrix: np.ndarray,
        contamination: float = 0.05
    ) -> Dict:
        """
        Isolation Forest for multivariate anomaly detection.

        Args:
            feature_matrix: (n_samples, n_features) schedule metrics
            contamination: Expected proportion of anomalies

        Returns:
            Anomaly labels and scores
        """
        # Fit Isolation Forest
        clf = IsolationForest(contamination=contamination, random_state=42)
        labels = clf.fit_predict(feature_matrix)
        scores = clf.score_samples(feature_matrix)

        # -1 = anomaly, 1 = normal
        anomaly_mask = labels == -1
        anomaly_indices = np.where(anomaly_mask)[0]

        return {
            'anomaly_indices': anomaly_indices.tolist(),
            'anomaly_scores': scores.tolist(),
            'labels': labels.tolist(),
            'num_anomalies': int(np.sum(anomaly_mask)),
            'contamination': contamination
        }

    def mad_detection(
        self,
        time_series: np.ndarray,
        threshold: float = 3.5
    ) -> Dict:
        """
        Median Absolute Deviation (MAD) detection (robust to outliers).

        Args:
            time_series: Schedule metric time series
            threshold: MAD threshold (3.5 for moderate outliers)

        Returns:
            Anomaly indices and scores
        """
        median = np.median(time_series)
        mad = np.median(np.abs(time_series - median))

        # Modified z-score using MAD
        modified_z_scores = 0.6745 * (time_series - median) / (mad + 1e-8)

        anomaly_mask = np.abs(modified_z_scores) > threshold
        anomaly_indices = np.where(anomaly_mask)[0]

        return {
            'anomaly_indices': anomaly_indices.tolist(),
            'mad_scores': modified_z_scores.tolist(),
            'median': float(median),
            'mad': float(mad),
            'num_anomalies': len(anomaly_indices)
        }

    def ensemble_detection(
        self,
        time_series: np.ndarray,
        feature_matrix: np.ndarray = None,
        voting_threshold: int = 2
    ) -> Dict:
        """
        Ensemble anomaly detection (voting across multiple methods).

        Args:
            time_series: Univariate time series
            feature_matrix: Multivariate features (optional)
            voting_threshold: Minimum votes to flag as anomaly

        Returns:
            Consensus anomalies from multiple detectors
        """
        n = len(time_series)
        votes = np.zeros(n, dtype=int)

        # Method 1: Z-score
        z_result = self.z_score_detection(time_series, threshold=3.0)
        for idx in z_result['anomaly_indices']:
            votes[idx] += 1

        # Method 2: MAD
        mad_result = self.mad_detection(time_series, threshold=3.5)
        for idx in mad_result['anomaly_indices']:
            votes[idx] += 1

        # Method 3: Isolation Forest (if feature matrix provided)
        if feature_matrix is not None:
            iso_result = self.isolation_forest_detection(feature_matrix)
            for idx in iso_result['anomaly_indices']:
                if idx < n:
                    votes[idx] += 1

        # Consensus anomalies
        anomaly_mask = votes >= voting_threshold
        anomaly_indices = np.where(anomaly_mask)[0]

        return {
            'anomaly_indices': anomaly_indices.tolist(),
            'votes': votes.tolist(),
            'voting_threshold': voting_threshold,
            'num_anomalies': len(anomaly_indices),
            'methods_used': ['z_score', 'mad', 'isolation_forest'] if feature_matrix is not None else ['z_score', 'mad']
        }
```

---

## Implementation Architecture

### Integration Points

```python
"""
Signal processing integration with existing analytics.
"""
from datetime import date, timedelta
from typing import Dict, List
import numpy as np
from sqlalchemy.orm import Session

from app.analytics.metrics import calculate_fairness_index
from app.analytics.stability_metrics import StabilityMetricsComputer


class SignalProcessingAnalytics:
    """
    Unified signal processing analytics for schedule monitoring.
    """

    def __init__(self, db: Session):
        self.db = db
        self.fourier = FourierScheduleAnalyzer()
        self.wavelet = WaveletScheduleAnalyzer()
        self.filter = ScheduleFilter()
        self.decomposer = TimeSeriesDecomposer()
        self.anomaly = ScheduleAnomalyDetector()

    def comprehensive_analysis(
        self,
        start_date: date,
        end_date: date,
        person_ids: List[str] = None
    ) -> Dict:
        """
        Run full signal processing pipeline on schedule data.

        Args:
            start_date: Analysis start date
            end_date: Analysis end date
            person_ids: Optional list of people to analyze

        Returns:
            Comprehensive analysis results
        """
        # Extract time series from database
        workload_series, dates = self._extract_workload_series(
            start_date, end_date, person_ids
        )

        # 1. Fourier Analysis - detect periodic patterns
        fourier_results = self.fourier.analyze_workload_periodicity(
            workload_series, dates
        )

        # 2. Wavelet Analysis - detect transient events
        wavelet_decomp = self.wavelet.decompose_schedule(workload_series, levels=5)
        transient_events = self.wavelet.detect_transient_events(
            workload_series, dates, threshold_sigma=3.0
        )

        # 3. Filtering - extract trend
        trend = self.filter.extract_trend(workload_series, cutoff_period_days=28.0)

        # 4. STL Decomposition
        stl_components = self.decomposer.stl_decompose(workload_series, period=7)

        # 5. Change Point Detection
        change_points = self.decomposer.pelt_segmentation(workload_series, penalty=10.0)

        # 6. Anomaly Detection
        anomalies = self.anomaly.z_score_detection(workload_series, threshold=3.0)

        return {
            'fourier_analysis': fourier_results,
            'wavelet_decomposition': {
                'approximation': wavelet_decomp['approximation'].tolist(),
                'weekly_pattern': wavelet_decomp['detail_level_3'].tolist()
            },
            'transient_events': transient_events[:10],  # Top 10
            'trend': trend.tolist(),
            'stl_components': {
                'trend': stl_components['trend'].tolist(),
                'seasonal': stl_components['seasonal'].tolist(),
                'residual': stl_components['residual'].tolist()
            },
            'change_points': change_points,
            'anomalies': anomalies,
            'dates': [d.isoformat() for d in dates]
        }

    def _extract_workload_series(
        self,
        start_date: date,
        end_date: date,
        person_ids: List[str] = None
    ) -> tuple:
        """
        Extract daily workload time series from database.

        Returns:
            (workload_array, dates_array)
        """
        from app.models.assignment import Assignment
        from app.models.block import Block

        # Query assignments in date range
        query = self.db.query(
            Block.date,
            func.count(Assignment.id).label('workload')
        ).join(Assignment).filter(
            Block.date >= start_date,
            Block.date <= end_date
        )

        if person_ids:
            query = query.filter(Assignment.person_id.in_(person_ids))

        query = query.group_by(Block.date).order_by(Block.date)

        results = query.all()

        # Convert to numpy arrays
        dates = np.array([r.date for r in results])
        workload = np.array([r.workload for r in results], dtype=float)

        return workload, dates
```

---

## Performance Considerations

### Computational Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| FFT | O(N log N) | Very fast, use for >1000 samples |
| Wavelet CWT | O(N × S) | S = number of scales, ~O(N²) |
| DWT | O(N) | Fast, use for decomposition |
| Butterworth Filter | O(N) | filtfilt doubles cost |
| STL Decomposition | O(N × iterations) | ~10 iterations typical |
| PELT | O(N) | Optimal, very efficient |
| Isolation Forest | O(T × N log N) | T = number of trees |

### Optimization Strategies

1. **Downsample** for long time series (365+ days) before CWT
2. **Cache** Fourier/wavelet results (recompute only on new data)
3. **Parallel** processing for multiple person time series
4. **Incremental** updates for rolling window statistics

---

## References

1. Oppenheim, A. V., & Schafer, R. W. (2009). *Discrete-Time Signal Processing* (3rd ed.). Prentice Hall.

2. Mallat, S. (2008). *A Wavelet Tour of Signal Processing* (3rd ed.). Academic Press.

3. Cleveland, R. B., et al. (1990). STL: A seasonal-trend decomposition procedure based on loess. *Journal of Official Statistics*, 6(1), 3-73.

4. Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal detection of changepoints with a linear computational cost. *Journal of the American Statistical Association*, 107(500), 1590-1598.

5. Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation forest. *2008 Eighth IEEE International Conference on Data Mining*, 413-422.

6. Virtanen, P., et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. *Nature Methods*, 17(3), 261-272.

7. Seabold, S., & Perktold, J. (2010). statsmodels: Econometric and statistical modeling with python. *9th Python in Science Conference*.

---

**Last Updated:** 2025-12-26
**Next Review:** Q2 2026
