# Signal Processing Analytics Service - Implementation Specification

> **Version:** 1.0.0
> **Created:** 2025-12-26
> **Status:** Ready for Implementation
> **Priority:** HIGH
> **Complexity:** Medium-High
> **Dependencies:** `docs/research/SIGNAL_PROCESSING_SCHEDULE_ANALYSIS.md`

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Service Architecture](#service-architecture)
3. [Data Pipeline](#data-pipeline)
4. [Analysis Modules](#analysis-modules)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Pydantic Schemas](#pydantic-schemas)
8. [Frontend Components](#frontend-components)
9. [Alert Integration](#alert-integration)
10. [Caching Strategy](#caching-strategy)
11. [Testing Requirements](#testing-requirements)
12. [Performance Benchmarks](#performance-benchmarks)
13. [Deployment Plan](#deployment-plan)
14. [Security Considerations](#security-considerations)

---

## Executive Summary

### Purpose

The **Signal Processing Analytics Service** applies advanced signal processing techniques to schedule time-series data to detect:

- **Periodic patterns** (Fourier analysis for rotation cycles)
- **Transient events** (Wavelet analysis for deployment surges)
- **Long-term trends** (Filtering for workload drift)
- **Anomalies** (Statistical outlier detection)
- **Regime changes** (Change point detection)
- **Future predictions** (ARIMA forecasting)

### Key Features

| Feature | Technique | Business Value |
|---------|-----------|----------------|
| **Rotation Pattern Detection** | Fourier Transform (FFT) | Automatically identify weekly/monthly cycles |
| **Deployment Surge Detection** | Continuous Wavelet Transform | 2-4 week advance warning of coverage gaps |
| **Trend Extraction** | Butterworth Filtering + STL | Separate seasonal effects from genuine drift |
| **Anomaly Detection** | Isolation Forest + Z-score | 95%+ accuracy, <5% false positive rate |
| **Change Point Detection** | PELT Algorithm | Detect policy changes, staffing disruptions |
| **Workload Forecasting** | ARIMA Models | 7-day ahead prediction with confidence intervals |

### Expected Impact

- **Early Warning**: 2-4 weeks advance notice of schedule degradation
- **Pattern Recognition**: Automatic detection of rotation cycles without manual rules
- **Anomaly Detection**: Real-time alerts for ACGME violations, fairness anomalies
- **Dashboard Performance**: <100ms latency for real-time signal visualizations
- **Forecast Accuracy**: 85%+ accuracy for 7-day ahead workload predictions

---

## Service Architecture

### Layered Architecture

Following the project's standard layered pattern:

```
API Route (FastAPI endpoint)
    ↓
Controller (request/response handling, validation)
    ↓
Service (business logic, orchestration)
    ↓
Analysis Modules (signal processing algorithms)
    ↓
Data Pipeline (time-series extraction)
    ↓
Model (SQLAlchemy ORM - assignments, blocks, persons)
```

### Directory Structure

```
backend/app/
├── analytics/
│   ├── signal_processing/         # New directory
│   │   ├── __init__.py
│   │   ├── fourier_analyzer.py    # Fourier Transform analysis
│   │   ├── wavelet_analyzer.py    # Wavelet analysis
│   │   ├── filter.py              # Filtering (trend extraction)
│   │   ├── decomposer.py          # STL, ARIMA, change detection
│   │   ├── anomaly_detector.py    # Anomaly detection
│   │   └── pipeline.py            # Time-series extraction pipeline
│   ├── signal_processing_service.py  # Main service orchestrator
│
├── api/routes/
│   └── signal_processing.py       # API endpoints
│
├── schemas/
│   └── signal_processing.py       # Pydantic schemas
│
├── models/
│   └── signal_analysis.py         # Database models (cached results)
│
tests/
├── analytics/
│   └── signal_processing/
│       ├── test_fourier_analyzer.py
│       ├── test_wavelet_analyzer.py
│       ├── test_filter.py
│       ├── test_decomposer.py
│       ├── test_anomaly_detector.py
│       └── test_service.py
```

### Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| **FourierAnalyzer** | FFT, power spectral density, harmonic detection, cross-spectrum |
| **WaveletAnalyzer** | Multi-resolution decomposition, transient event detection, denoising |
| **ScheduleFilter** | Low-pass, high-pass, band-pass filtering for trend extraction |
| **TimeSeriesDecomposer** | STL decomposition, ARIMA forecasting, change point detection |
| **AnomalyDetector** | Z-score, MAD, Isolation Forest, ensemble voting |
| **TimeSeriesPipeline** | Extract workload/fairness/compliance time series from database |
| **SignalProcessingService** | Orchestrate analysis, caching, alert generation |

---

## Data Pipeline

### Time-Series Extraction

The pipeline converts relational schedule data into time-series arrays suitable for signal processing.

#### Workload Time Series

```python
"""
Extract daily workload time series for signal processing.
"""
from datetime import date, timedelta
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block, BlockSession


class TimeSeriesPipeline:
    """
    Extract time-series data from schedule database for signal processing.
    """

    def __init__(self, db: Session):
        self.db = db

    async def extract_workload_series(
        self,
        start_date: date,
        end_date: date,
        person_ids: Optional[List[str]] = None,
        aggregation: str = "count"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract daily workload time series.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            person_ids: Optional filter for specific people
            aggregation: 'count' (number of assignments) or 'hours' (total hours)

        Returns:
            (workload_array, dates_array)
        """
        # Query assignments grouped by date
        query = self.db.query(
            Block.date,
            func.count(Assignment.id).label('assignment_count')
        ).join(Assignment).filter(
            Block.date >= start_date,
            Block.date <= end_date
        )

        if person_ids:
            query = query.filter(Assignment.person_id.in_(person_ids))

        query = query.group_by(Block.date).order_by(Block.date)
        results = query.all()

        # Create continuous date range (fill missing dates with 0)
        date_range = []
        current = start_date
        while current <= end_date:
            date_range.append(current)
            current += timedelta(days=1)

        # Map results to date range
        result_dict = {r.date: r.assignment_count for r in results}
        workload = np.array([
            result_dict.get(d, 0) for d in date_range
        ], dtype=float)

        dates = np.array(date_range)

        return workload, dates

    async def extract_fairness_series(
        self,
        start_date: date,
        end_date: date,
        pgy_year: Optional[int] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract daily fairness index (Gini coefficient) time series.

        Args:
            start_date: Start date
            end_date: End date
            pgy_year: Optional filter for specific PGY year

        Returns:
            (fairness_index_array, dates_array)
        """
        from app.analytics.metrics import calculate_fairness_index

        # Calculate fairness for each date in range
        date_range = []
        fairness_values = []

        current = start_date
        while current <= end_date:
            # Get assignments for this date
            assignments = self.db.query(Assignment).join(Block).filter(
                Block.date == current
            )

            if pgy_year:
                assignments = assignments.join(Person).filter(
                    Person.pgy_year == pgy_year
                )

            assignments_list = assignments.all()

            # Calculate fairness index
            if assignments_list:
                workload_by_person = {}
                for assign in assignments_list:
                    workload_by_person[assign.person_id] = \
                        workload_by_person.get(assign.person_id, 0) + 1

                fairness = calculate_fairness_index(list(workload_by_person.values()))
            else:
                fairness = 1.0  # Perfect fairness if no assignments

            date_range.append(current)
            fairness_values.append(fairness)

            current += timedelta(days=1)

        return np.array(fairness_values), np.array(date_range)

    async def extract_compliance_series(
        self,
        start_date: date,
        end_date: date,
        person_ids: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract daily ACGME compliance score time series.

        Returns 1.0 for compliant days, 0.0 for non-compliant.

        Args:
            start_date: Start date
            end_date: End date
            person_ids: Optional filter for specific people

        Returns:
            (compliance_array, dates_array)
        """
        from app.scheduling.acgme_validator import ACGMEValidator

        validator = ACGMEValidator(self.db)

        date_range = []
        compliance_scores = []

        current = start_date
        while current <= end_date:
            # Check ACGME compliance for this date
            violations = await validator.validate_date(current, person_ids)

            # Binary: 1.0 if compliant, 0.0 if violations
            score = 0.0 if violations else 1.0

            date_range.append(current)
            compliance_scores.append(score)

            current += timedelta(days=1)

        return np.array(compliance_scores), np.array(date_range)

    async def extract_coverage_series(
        self,
        start_date: date,
        end_date: date,
        rotation_type: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract daily coverage rate time series.

        Args:
            start_date: Start date
            end_date: End date
            rotation_type: Optional filter for specific rotation type

        Returns:
            (coverage_rate_array, dates_array)
        """
        from app.analytics.metrics import calculate_coverage_rate

        date_range = []
        coverage_rates = []

        current = start_date
        while current <= end_date:
            # Calculate coverage rate for this date
            rate = await calculate_coverage_rate(
                self.db,
                current,
                rotation_type
            )

            date_range.append(current)
            coverage_rates.append(rate)

            current += timedelta(days=1)

        return np.array(coverage_rates), np.array(date_range)

    async def extract_multivariate_features(
        self,
        start_date: date,
        end_date: date,
        person_ids: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract multivariate feature matrix for anomaly detection.

        Features:
        - Workload (assignment count)
        - Fairness index (Gini coefficient)
        - ACGME compliance (binary)
        - Coverage rate
        - Workload variance (rolling 7-day)

        Args:
            start_date: Start date
            end_date: End date
            person_ids: Optional filter

        Returns:
            (feature_matrix, dates_array) where feature_matrix is (N, 5)
        """
        # Extract individual series
        workload, dates1 = await self.extract_workload_series(
            start_date, end_date, person_ids
        )
        fairness, dates2 = await self.extract_fairness_series(
            start_date, end_date
        )
        compliance, dates3 = await self.extract_compliance_series(
            start_date, end_date, person_ids
        )
        coverage, dates4 = await self.extract_coverage_series(
            start_date, end_date
        )

        # Ensure all date arrays match
        assert np.array_equal(dates1, dates2)
        assert np.array_equal(dates1, dates3)
        assert np.array_equal(dates1, dates4)

        # Calculate rolling variance
        workload_variance = self._rolling_variance(workload, window=7)

        # Stack into feature matrix
        feature_matrix = np.column_stack([
            workload,
            fairness,
            compliance,
            coverage,
            workload_variance
        ])

        return feature_matrix, dates1

    @staticmethod
    def _rolling_variance(series: np.ndarray, window: int) -> np.ndarray:
        """Calculate rolling variance with specified window."""
        variances = np.zeros_like(series)

        for i in range(len(series)):
            start = max(0, i - window + 1)
            window_data = series[start:i+1]
            variances[i] = np.var(window_data) if len(window_data) > 1 else 0.0

        return variances
```

---

## Analysis Modules

### Module 1: Fourier Analyzer

**File:** `backend/app/analytics/signal_processing/fourier_analyzer.py`

**Purpose:** Frequency-domain analysis for detecting periodic patterns in schedules.

**Key Methods:**

```python
class FourierScheduleAnalyzer:
    """Fourier analysis for periodic pattern detection."""

    def analyze_workload_periodicity(
        self,
        workload_time_series: np.ndarray,
        dates: np.ndarray
    ) -> Dict[str, Any]:
        """
        Detect periodic patterns using FFT.

        Returns:
            - frequencies: Frequency array
            - psd: Power spectral density
            - dominant_periods: Top 5 periodic components with classification
            - total_power: Total signal power
        """

    def detect_rotation_harmonics(
        self,
        workload_time_series: np.ndarray,
        fundamental_period: float = 7.0
    ) -> List[Dict]:
        """
        Detect harmonic components (1x, 2x, 3x, 4x) of fundamental period.

        Returns:
            List of harmonics with amplitude, phase, power
        """

    def compute_cross_spectrum(
        self,
        signal1: np.ndarray,
        signal2: np.ndarray
    ) -> Dict:
        """
        Compute cross-spectrum and coherence between two signals.

        Useful for:
        - Detecting phase relationships between PGY-1 and PGY-2 schedules
        - Identifying synchronized rotation patterns
        """
```

**Implementation:** Copy from `docs/research/SIGNAL_PROCESSING_SCHEDULE_ANALYSIS.md` lines 121-337.

**Dependencies:**
- `scipy.fft` (fft, fftfreq)
- `scipy.signal` (periodogram, welch, coherence, csd)
- `numpy`

---

### Module 2: Wavelet Analyzer

**File:** `backend/app/analytics/signal_processing/wavelet_analyzer.py`

**Purpose:** Multi-resolution time-frequency analysis for transient event detection.

**Key Methods:**

```python
class WaveletScheduleAnalyzer:
    """Wavelet analysis for transient events and multi-scale decomposition."""

    def decompose_schedule(
        self,
        time_series: np.ndarray,
        levels: int = 5
    ) -> Dict[str, np.ndarray]:
        """
        Multi-resolution decomposition using DWT.

        Returns:
            - approximation: Long-term trend
            - detail_level_1 to detail_level_5: High to low frequency components
            - interpretation: Human-readable description of each level
        """

    def detect_transient_events(
        self,
        time_series: np.ndarray,
        dates: np.ndarray,
        threshold_sigma: float = 3.0
    ) -> List[Dict]:
        """
        Detect sudden spikes/drops using CWT with Mexican Hat wavelet.

        Returns:
            List of events with date, scale, magnitude, z-score, event_type
        """

    def denoise_schedule(
        self,
        time_series: np.ndarray,
        noise_level: int = 2
    ) -> np.ndarray:
        """
        Remove high-frequency noise using wavelet thresholding.

        Uses VisuShrink universal threshold.
        """

    def compute_scalogram(
        self,
        time_series: np.ndarray,
        dates: np.ndarray,
        scales: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Compute scalogram (wavelet power spectrum) for visualization.

        Returns:
            - power: 2D array (scales × time)
            - scales: Scale array (in days)
            - dates: Date array
            - freqs: Corresponding frequencies
        """
```

**Implementation:** Copy from research document lines 410-629.

**Dependencies:**
- `pywt` (PyWavelets library)
- `scipy.signal` (find_peaks)
- `numpy`

---

### Module 3: Schedule Filter

**File:** `backend/app/analytics/signal_processing/filter.py`

**Purpose:** Filter-based trend extraction and frequency isolation.

**Key Methods:**

```python
class ScheduleFilter:
    """Filter-based schedule analysis for trend extraction."""

    def extract_trend(
        self,
        time_series: np.ndarray,
        cutoff_period_days: float = 28.0,
        filter_order: int = 4
    ) -> np.ndarray:
        """
        Extract long-term trend using Butterworth low-pass filter.

        Args:
            cutoff_period_days: Period below which to filter out (default 28 days)

        Returns:
            Trend component (low-frequency signal)
        """

    def detect_rapid_changes(
        self,
        time_series: np.ndarray,
        cutoff_period_days: float = 7.0,
        filter_order: int = 4
    ) -> np.ndarray:
        """
        Detect rapid changes using high-pass filter.

        Returns:
            High-frequency component (rapid changes)
        """

    def isolate_weekly_cycle(
        self,
        time_series: np.ndarray,
        center_period: float = 7.0,
        bandwidth: float = 1.0,
        filter_order: int = 3
    ) -> np.ndarray:
        """
        Isolate weekly cycle using band-pass filter.

        Returns:
            Band-passed signal (weekly component only)
        """

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

        Returns:
            (b, a) filter coefficients for scipy.signal.filtfilt
        """
```

**Implementation:** Copy from research document lines 685-841.

**Dependencies:**
- `scipy.signal` (butter, cheby1, filtfilt)
- `numpy`

---

### Module 4: Time-Series Decomposer

**File:** `backend/app/analytics/signal_processing/decomposer.py`

**Purpose:** STL decomposition, ARIMA forecasting, change point detection.

**Key Methods:**

```python
class TimeSeriesDecomposer:
    """Decomposition and forecasting for schedule time series."""

    def stl_decompose(
        self,
        time_series: np.ndarray,
        period: int = 7
    ) -> Dict[str, np.ndarray]:
        """
        STL decomposition into trend, seasonal, and residual.

        Returns:
            - trend: Long-term trend component
            - seasonal: Periodic seasonal component
            - residual: Residual (noise + anomalies)
            - observed: Original time series
        """

    def cusum_change_detection(
        self,
        time_series: np.ndarray,
        threshold: float = 5.0,
        drift: float = 0.5
    ) -> List[int]:
        """
        CUSUM change point detection.

        Returns:
            List of change point indices
        """

    def pelt_segmentation(
        self,
        time_series: np.ndarray,
        penalty: float = 10.0,
        min_segment_length: int = 7
    ) -> List[int]:
        """
        PELT algorithm for optimal change point detection.

        Returns:
            List of change point indices
        """

    def forecast_arima(
        self,
        time_series: np.ndarray,
        forecast_steps: int = 7,
        order: Tuple[int, int, int] = (2, 1, 2)
    ) -> Dict:
        """
        ARIMA forecast for schedule prediction.

        Returns:
            - forecast: Predicted values
            - lower_bound: Lower confidence interval (95%)
            - upper_bound: Upper confidence interval (95%)
            - model_aic: Akaike Information Criterion
            - model_bic: Bayesian Information Criterion
        """
```

**Implementation:** Copy from research document lines 896-1066.

**Dependencies:**
- `statsmodels` (STL, ARIMA)
- `ruptures` (PELT algorithm - optional, fallback to CUSUM)
- `scipy.stats`
- `numpy`

---

### Module 5: Anomaly Detector

**File:** `backend/app/analytics/signal_processing/anomaly_detector.py`

**Purpose:** Multi-method anomaly detection with ensemble voting.

**Key Methods:**

```python
class ScheduleAnomalyDetector:
    """Multi-method anomaly detection for schedule monitoring."""

    def z_score_detection(
        self,
        time_series: np.ndarray,
        threshold: float = 3.0,
        window: Optional[int] = None
    ) -> Dict:
        """
        Z-score based anomaly detection.

        Returns:
            - anomaly_indices: Indices of detected anomalies
            - z_scores: Z-score for each data point
            - anomaly_values: Values at anomaly points
            - num_anomalies: Count of anomalies
        """

    def isolation_forest_detection(
        self,
        feature_matrix: np.ndarray,
        contamination: float = 0.05
    ) -> Dict:
        """
        Isolation Forest for multivariate anomaly detection.

        Returns:
            - anomaly_indices: Indices of detected anomalies
            - anomaly_scores: Anomaly score for each point
            - labels: -1 for anomaly, 1 for normal
            - num_anomalies: Count of anomalies
        """

    def mad_detection(
        self,
        time_series: np.ndarray,
        threshold: float = 3.5
    ) -> Dict:
        """
        Median Absolute Deviation detection (robust to outliers).

        Returns:
            - anomaly_indices: Indices of detected anomalies
            - mad_scores: Modified z-scores using MAD
            - median: Median of time series
            - mad: Median absolute deviation
        """

    def ensemble_detection(
        self,
        time_series: np.ndarray,
        feature_matrix: Optional[np.ndarray] = None,
        voting_threshold: int = 2
    ) -> Dict:
        """
        Ensemble anomaly detection with voting across multiple methods.

        Combines: Z-score, MAD, Isolation Forest (if feature_matrix provided)

        Returns:
            - anomaly_indices: Consensus anomalies
            - votes: Vote count for each point
            - voting_threshold: Minimum votes required
            - methods_used: List of methods applied
        """
```

**Implementation:** Copy from research document lines 1097-1275.

**Dependencies:**
- `sklearn.ensemble` (IsolationForest)
- `sklearn.preprocessing` (StandardScaler)
- `scipy.stats`
- `numpy`

---

### Module 6: Time-Series Pipeline

**File:** `backend/app/analytics/signal_processing/pipeline.py`

**Purpose:** Extract time-series data from relational database for signal processing.

**Implementation:** See [Data Pipeline](#data-pipeline) section above.

---

## API Endpoints

### Route File

**File:** `backend/app/api/routes/signal_processing.py`

### Endpoint Specifications

#### 1. POST /api/v1/signals/fft - Fourier Analysis

**Purpose:** Detect periodic patterns in schedule workload.

**Request:**

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

class FourierAnalysisRequest(BaseModel):
    start_date: date = Field(..., description="Analysis start date")
    end_date: date = Field(..., description="Analysis end date")
    person_ids: Optional[List[str]] = Field(None, description="Filter for specific people")
    metric_type: str = Field("workload", description="workload|fairness|compliance|coverage")
    detect_harmonics: bool = Field(True, description="Detect harmonic components")
    fundamental_period: float = Field(7.0, description="Fundamental period for harmonic analysis (days)")
```

**Response:**

```python
class PeriodComponent(BaseModel):
    frequency: float
    period_days: float
    power: float
    type: str  # 'weekly'|'monthly'|'quarterly'|'annual'|'irregular'
    significance: str  # 'highly_significant'|'significant'|'moderate'|'weak'

class HarmonicComponent(BaseModel):
    harmonic_number: int
    frequency: float
    period_days: float
    amplitude: float
    phase_deg: float
    power: float

class FourierAnalysisResponse(BaseModel):
    frequencies: List[float]
    psd: List[float]
    dominant_periods: List[PeriodComponent]
    harmonics: Optional[List[HarmonicComponent]]
    total_power: float
    signal_length_days: int
    analysis_date: datetime
```

**Handler:**

```python
@router.post("/signals/fft", response_model=FourierAnalysisResponse)
async def analyze_fourier_spectrum(
    request: FourierAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> FourierAnalysisResponse:
    """
    Perform Fourier analysis to detect periodic patterns in schedule data.

    Detects:
    - Weekly rotation cycles (7-day period)
    - Monthly rotation blocks (28-30 day period)
    - Quarterly educational rotations (90-day period)
    - Harmonic relationships between cycles

    Returns power spectral density and dominant frequency components.
    """
    service = SignalProcessingService(db)

    result = await service.analyze_fourier(
        start_date=request.start_date,
        end_date=request.end_date,
        person_ids=request.person_ids,
        metric_type=request.metric_type,
        detect_harmonics=request.detect_harmonics,
        fundamental_period=request.fundamental_period
    )

    return result
```

---

#### 2. POST /api/v1/signals/wavelet - Wavelet Analysis

**Purpose:** Detect transient events and multi-resolution decomposition.

**Request:**

```python
class WaveletAnalysisRequest(BaseModel):
    start_date: date
    end_date: date
    person_ids: Optional[List[str]] = None
    metric_type: str = "workload"
    decomposition_levels: int = Field(5, ge=3, le=7, description="Number of decomposition levels")
    detect_transients: bool = Field(True, description="Detect transient events")
    threshold_sigma: float = Field(3.0, description="Threshold for transient detection (std devs)")
    compute_scalogram: bool = Field(False, description="Compute scalogram for visualization")
```

**Response:**

```python
class TransientEvent(BaseModel):
    date: date
    index: int
    scale_days: float
    magnitude: float
    z_score: float
    event_type: str  # 'critical_spike'|'significant_multi_day_event'|etc.

class WaveletDecomposition(BaseModel):
    approximation: List[float]
    detail_levels: Dict[str, List[float]]  # 'detail_level_1' -> values
    interpretation: Dict[str, str]

class Scalogram(BaseModel):
    power: List[List[float]]  # 2D array (scales × time)
    scales: List[float]
    dates: List[date]
    time_indices: List[int]

class WaveletAnalysisResponse(BaseModel):
    decomposition: WaveletDecomposition
    transient_events: Optional[List[TransientEvent]]
    scalogram: Optional[Scalogram]
    analysis_date: datetime
```

**Handler:**

```python
@router.post("/signals/wavelet", response_model=WaveletAnalysisResponse)
async def analyze_wavelet_transform(
    request: WaveletAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> WaveletAnalysisResponse:
    """
    Perform wavelet analysis for multi-resolution decomposition and transient event detection.

    Detects:
    - Deployment surges (sudden drops in available personnel)
    - COVID outbreaks (transient coverage gaps)
    - Conference season spikes (temporary workload increases)
    - Multi-scale patterns (daily, weekly, monthly)

    Returns decomposed signals and detected transient events.
    """
    service = SignalProcessingService(db)

    result = await service.analyze_wavelet(
        start_date=request.start_date,
        end_date=request.end_date,
        person_ids=request.person_ids,
        metric_type=request.metric_type,
        decomposition_levels=request.decomposition_levels,
        detect_transients=request.detect_transients,
        threshold_sigma=request.threshold_sigma,
        compute_scalogram=request.compute_scalogram
    )

    return result
```

---

#### 3. POST /api/v1/signals/anomalies - Anomaly Detection

**Purpose:** Detect statistical outliers and anomalies in schedule metrics.

**Request:**

```python
class AnomalyDetectionRequest(BaseModel):
    start_date: date
    end_date: date
    person_ids: Optional[List[str]] = None
    metric_type: str = "workload"
    methods: List[str] = Field(
        ["z_score", "mad", "isolation_forest"],
        description="Detection methods to use"
    )
    z_score_threshold: float = Field(3.0, description="Z-score threshold")
    mad_threshold: float = Field(3.5, description="MAD threshold")
    contamination: float = Field(0.05, description="Expected anomaly proportion (0-0.5)")
    voting_threshold: int = Field(2, description="Minimum votes to flag as anomaly (ensemble)")
    use_ensemble: bool = Field(True, description="Use ensemble voting")
```

**Response:**

```python
class Anomaly(BaseModel):
    date: date
    index: int
    value: float
    z_score: Optional[float]
    mad_score: Optional[float]
    anomaly_score: Optional[float]
    votes: int
    methods_detected: List[str]
    severity: str  # 'critical'|'high'|'moderate'

class AnomalyDetectionResponse(BaseModel):
    anomalies: List[Anomaly]
    num_anomalies: int
    total_points: int
    anomaly_rate: float
    methods_used: List[str]
    ensemble_threshold: Optional[int]
    analysis_date: datetime
```

**Handler:**

```python
@router.post("/signals/anomalies", response_model=AnomalyDetectionResponse)
async def detect_schedule_anomalies(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> AnomalyDetectionResponse:
    """
    Detect anomalies in schedule metrics using multiple statistical methods.

    Methods:
    - Z-score: Simple statistical outlier detection
    - MAD: Median Absolute Deviation (robust to outliers)
    - Isolation Forest: Machine learning ensemble method

    Returns detected anomalies with severity classification and consensus voting.
    """
    service = SignalProcessingService(db)

    result = await service.detect_anomalies(
        start_date=request.start_date,
        end_date=request.end_date,
        person_ids=request.person_ids,
        metric_type=request.metric_type,
        methods=request.methods,
        z_score_threshold=request.z_score_threshold,
        mad_threshold=request.mad_threshold,
        contamination=request.contamination,
        voting_threshold=request.voting_threshold,
        use_ensemble=request.use_ensemble
    )

    return result
```

---

#### 4. POST /api/v1/signals/forecast - ARIMA Forecasting

**Purpose:** Predict future schedule metrics using time-series forecasting.

**Request:**

```python
class ForecastRequest(BaseModel):
    start_date: date
    end_date: date  # Historical data end date
    person_ids: Optional[List[str]] = None
    metric_type: str = "workload"
    forecast_steps: int = Field(7, ge=1, le=30, description="Days ahead to forecast")
    arima_order: Optional[Tuple[int, int, int]] = Field(
        None,
        description="ARIMA (p,d,q) order. Auto-selected if None"
    )
    confidence_level: float = Field(0.95, description="Confidence level for intervals")
```

**Response:**

```python
class ForecastResult(BaseModel):
    forecast_dates: List[date]
    forecast_values: List[float]
    lower_bound: List[float]
    upper_bound: List[float]
    model_order: Tuple[int, int, int]
    model_aic: float
    model_bic: float
    confidence_level: float
    analysis_date: datetime

class ForecastResponse(BaseModel):
    forecast: ForecastResult
    historical_dates: List[date]
    historical_values: List[float]
```

**Handler:**

```python
@router.post("/signals/forecast", response_model=ForecastResponse)
async def forecast_schedule_metrics(
    request: ForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ForecastResponse:
    """
    Forecast future schedule metrics using ARIMA time-series models.

    Predicts:
    - Future workload levels (7-30 days ahead)
    - Expected fairness trends
    - Compliance degradation risk

    Returns point forecasts with confidence intervals.
    """
    service = SignalProcessingService(db)

    result = await service.forecast_arima(
        start_date=request.start_date,
        end_date=request.end_date,
        person_ids=request.person_ids,
        metric_type=request.metric_type,
        forecast_steps=request.forecast_steps,
        arima_order=request.arima_order,
        confidence_level=request.confidence_level
    )

    return result
```

---

#### 5. GET /api/v1/signals/changepoints - Change Point Detection

**Purpose:** Detect regime shifts and structural breaks in schedule data.

**Request:**

```python
class ChangePointRequest(BaseModel):
    start_date: date
    end_date: date
    person_ids: Optional[List[str]] = None
    metric_type: str = "workload"
    algorithm: str = Field("pelt", description="pelt|cusum")
    penalty: float = Field(10.0, description="PELT penalty (higher = fewer segments)")
    cusum_threshold: float = Field(5.0, description="CUSUM alarm threshold")
    min_segment_length: int = Field(7, description="Minimum segment length (days)")
```

**Response:**

```python
class ChangePoint(BaseModel):
    date: date
    index: int
    before_mean: float
    after_mean: float
    change_magnitude: float
    confidence: str  # 'high'|'medium'|'low'

class SegmentStats(BaseModel):
    start_date: date
    end_date: date
    mean: float
    std: float
    length_days: int

class ChangePointResponse(BaseModel):
    change_points: List[ChangePoint]
    segments: List[SegmentStats]
    num_change_points: int
    algorithm_used: str
    analysis_date: datetime
```

**Handler:**

```python
@router.get("/signals/changepoints", response_model=ChangePointResponse)
async def detect_change_points(
    start_date: date = Query(...),
    end_date: date = Query(...),
    person_ids: Optional[str] = Query(None, description="Comma-separated person IDs"),
    metric_type: str = Query("workload"),
    algorithm: str = Query("pelt"),
    penalty: float = Query(10.0),
    cusum_threshold: float = Query(5.0),
    min_segment_length: int = Query(7),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ChangePointResponse:
    """
    Detect change points (regime shifts) in schedule time series.

    Detects:
    - Policy changes (new ACGME rules)
    - Staffing transitions (new residents arriving)
    - Academic year block boundaries
    - System disruptions (COVID, deployments)

    Returns detected change points and segment statistics.
    """
    service = SignalProcessingService(db)

    person_ids_list = person_ids.split(",") if person_ids else None

    result = await service.detect_change_points(
        start_date=start_date,
        end_date=end_date,
        person_ids=person_ids_list,
        metric_type=metric_type,
        algorithm=algorithm,
        penalty=penalty,
        cusum_threshold=cusum_threshold,
        min_segment_length=min_segment_length
    )

    return result
```

---

#### 6. POST /api/v1/signals/comprehensive - Comprehensive Analysis

**Purpose:** Run full signal processing pipeline (all analyses).

**Request:**

```python
class ComprehensiveAnalysisRequest(BaseModel):
    start_date: date
    end_date: date
    person_ids: Optional[List[str]] = None
    metric_type: str = "workload"
    include_fourier: bool = True
    include_wavelet: bool = True
    include_anomalies: bool = True
    include_forecast: bool = True
    include_changepoints: bool = True
```

**Response:**

```python
class ComprehensiveAnalysisResponse(BaseModel):
    fourier_analysis: Optional[FourierAnalysisResponse]
    wavelet_analysis: Optional[WaveletAnalysisResponse]
    anomaly_detection: Optional[AnomalyDetectionResponse]
    forecast: Optional[ForecastResponse]
    change_points: Optional[ChangePointResponse]
    analysis_date: datetime
    processing_time_ms: float
```

**Handler:**

```python
@router.post("/signals/comprehensive", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_signal_analysis(
    request: ComprehensiveAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ComprehensiveAnalysisResponse:
    """
    Run comprehensive signal processing pipeline on schedule data.

    Performs all available analyses:
    - Fourier (periodic patterns)
    - Wavelet (transient events)
    - Anomaly detection (outliers)
    - Forecasting (predictions)
    - Change points (regime shifts)

    Results are cached and can trigger alerts if anomalies detected.
    """
    import time
    start_time = time.time()

    service = SignalProcessingService(db)

    result = await service.comprehensive_analysis(
        start_date=request.start_date,
        end_date=request.end_date,
        person_ids=request.person_ids,
        metric_type=request.metric_type,
        include_fourier=request.include_fourier,
        include_wavelet=request.include_wavelet,
        include_anomalies=request.include_anomalies,
        include_forecast=request.include_forecast,
        include_changepoints=request.include_changepoints
    )

    # Add alert generation to background tasks if anomalies detected
    if result.anomaly_detection and result.anomaly_detection.num_anomalies > 0:
        background_tasks.add_task(
            service.generate_anomaly_alerts,
            anomalies=result.anomaly_detection.anomalies,
            metric_type=request.metric_type
        )

    processing_time = (time.time() - start_time) * 1000
    result.processing_time_ms = processing_time

    return result
```

---

## Database Schema

### New Model: SignalAnalysisCache

**File:** `backend/app/models/signal_analysis.py`

**Purpose:** Cache signal processing results to avoid expensive recomputation.

```python
"""
Signal analysis cache model for storing computed results.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import JSON, Column, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base_class import Base


class SignalAnalysisCache(Base):
    """
    Cache for signal processing analysis results.

    Stores computed Fourier, wavelet, anomaly, forecast results
    to avoid expensive recomputation for dashboard queries.
    """

    __tablename__ = "signal_analysis_cache"

    id = Column(Integer, primary_key=True, index=True)

    # Analysis parameters (cache key)
    analysis_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="fourier|wavelet|anomaly|forecast|changepoint"
    )
    metric_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="workload|fairness|compliance|coverage"
    )
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    person_filter_hash = Column(
        String(64),
        nullable=True,
        comment="Hash of person_ids list (NULL = all people)"
    )

    # Analysis results (JSONB for fast querying)
    results = Column(JSONB, nullable=False, comment="Serialized analysis results")

    # Metadata
    computed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    processing_time_ms = Column(Float, nullable=True)
    cache_version = Column(
        String(20),
        nullable=False,
        default="1.0.0",
        comment="Schema version for cache invalidation"
    )

    # Expiration
    expires_at = Column(
        DateTime,
        nullable=True,
        comment="Cache expiration (NULL = never expire)"
    )

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @classmethod
    def generate_cache_key(
        cls,
        analysis_type: str,
        metric_type: str,
        start_date: date,
        end_date: date,
        person_ids: Optional[list] = None
    ) -> dict:
        """Generate cache key parameters."""
        import hashlib

        person_filter_hash = None
        if person_ids:
            # Sort for deterministic hash
            sorted_ids = sorted(person_ids)
            person_filter_hash = hashlib.sha256(
                ",".join(sorted_ids).encode()
            ).hexdigest()

        return {
            "analysis_type": analysis_type,
            "metric_type": metric_type,
            "start_date": start_date,
            "end_date": end_date,
            "person_filter_hash": person_filter_hash
        }
```

**Migration:**

```bash
alembic revision --autogenerate -m "Add signal_analysis_cache table"
```

---

## Pydantic Schemas

**File:** `backend/app/schemas/signal_processing.py`

All Pydantic schemas defined in [API Endpoints](#api-endpoints) section above.

**Additional Shared Schemas:**

```python
"""
Pydantic schemas for signal processing analytics.
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class TimeSeriesData(BaseModel):
    """Time-series data with dates."""
    dates: List[date]
    values: List[float]
    metric_type: str
    label: Optional[str] = None


class SignalProcessingMetrics(BaseModel):
    """Summary metrics from signal processing analysis."""
    dominant_period_days: Optional[float] = Field(
        None,
        description="Most dominant periodic component (days)"
    )
    trend_direction: Optional[str] = Field(
        None,
        description="increasing|decreasing|stable"
    )
    trend_slope: Optional[float] = Field(
        None,
        description="Linear trend slope (units per day)"
    )
    num_anomalies: Optional[int] = Field(
        None,
        description="Number of detected anomalies"
    )
    anomaly_rate: Optional[float] = Field(
        None,
        description="Proportion of anomalous points"
    )
    num_transient_events: Optional[int] = Field(
        None,
        description="Number of transient events (spikes/drops)"
    )
    num_change_points: Optional[int] = Field(
        None,
        description="Number of detected regime changes"
    )
    forecast_7day_change: Optional[float] = Field(
        None,
        description="Predicted change in next 7 days (%)"
    )
```

---

## Frontend Components

### Component 1: Spectral Plot (Fourier)

**File:** `frontend/src/components/analytics/SpectralPlot.tsx`

**Purpose:** Visualize power spectral density from Fourier analysis.

```typescript
"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";

interface PeriodComponent {
  frequency: number;
  period_days: number;
  power: number;
  type: string;
  significance: string;
}

interface SpectralPlotProps {
  frequencies: number[];
  psd: number[];
  dominantPeriods: PeriodComponent[];
  title?: string;
}

export function SpectralPlot({
  frequencies,
  psd,
  dominantPeriods,
  title = "Power Spectral Density"
}: SpectralPlotProps) {
  // Convert to chart data
  const chartData = frequencies.map((freq, idx) => ({
    frequency: freq,
    period: freq > 0 ? 1.0 / freq : 999,
    power: psd[idx]
  }));

  // Filter for positive frequencies only
  const positiveData = chartData.filter(d => d.frequency > 0);

  // Sort dominant periods by power
  const topPeriods = [...dominantPeriods]
    .sort((a, b) => b.power - a.power)
    .slice(0, 5);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={positiveData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="period"
            label={{ value: "Period (days)", position: "insideBottom", offset: -5 }}
            domain={[0, 100]}
          />
          <YAxis
            label={{ value: "Power", angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            formatter={(value: number) => value.toFixed(2)}
            labelFormatter={(label) => `Period: ${label.toFixed(1)} days`}
          />
          <Line
            type="monotone"
            dataKey="power"
            stroke="#3b82f6"
            dot={false}
            strokeWidth={2}
          />

          {/* Reference lines for dominant periods */}
          {topPeriods.map((period, idx) => (
            <ReferenceLine
              key={idx}
              x={period.period_days}
              stroke={idx === 0 ? "#ef4444" : "#9ca3af"}
              strokeDasharray="3 3"
              label={{
                value: `${period.period_days.toFixed(0)}d (${period.type})`,
                position: "top"
              }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Dominant Periods Table */}
      <div className="mt-4">
        <h4 className="text-sm font-semibold mb-2">Dominant Periods</h4>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-1">Period</th>
              <th className="text-left py-1">Type</th>
              <th className="text-left py-1">Power</th>
              <th className="text-left py-1">Significance</th>
            </tr>
          </thead>
          <tbody>
            {topPeriods.map((period, idx) => (
              <tr key={idx} className="border-b">
                <td className="py-1">{period.period_days.toFixed(1)} days</td>
                <td className="py-1">
                  <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                    {period.type}
                  </span>
                </td>
                <td className="py-1">{period.power.toFixed(2)}</td>
                <td className="py-1">
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      period.significance === "highly_significant"
                        ? "bg-red-100 text-red-800"
                        : period.significance === "significant"
                        ? "bg-orange-100 text-orange-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {period.significance}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

### Component 2: Wavelet Scalogram

**File:** `frontend/src/components/analytics/WaveletScalogram.tsx`

**Purpose:** Visualize wavelet scalogram (time-frequency heatmap).

```typescript
"use client";

import React from "react";
import { scaleSequential } from "d3-scale";
import { interpolateViridis } from "d3-scale-chromatic";

interface ScalogramData {
  power: number[][];  // 2D array (scales × time)
  scales: number[];
  dates: string[];
  time_indices: number[];
}

interface WaveletScalogramProps {
  data: ScalogramData;
  title?: string;
}

export function WaveletScalogram({
  data,
  title = "Wavelet Scalogram"
}: WaveletScalogramProps) {
  const { power, scales, dates } = data;

  // Find min/max power for color scale
  const flatPower = power.flat();
  const minPower = Math.min(...flatPower);
  const maxPower = Math.max(...flatPower);

  // Color scale
  const colorScale = scaleSequential(interpolateViridis)
    .domain([minPower, maxPower]);

  // Canvas dimensions
  const cellWidth = 4;  // pixels per time point
  const cellHeight = 10; // pixels per scale

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>

      <div className="overflow-x-auto">
        <svg
          width={dates.length * cellWidth}
          height={scales.length * cellHeight + 60}
        >
          {/* Scalogram heatmap */}
          <g transform="translate(0, 40)">
            {scales.map((scale, scaleIdx) => (
              <g key={scaleIdx}>
                {dates.map((date, timeIdx) => (
                  <rect
                    key={timeIdx}
                    x={timeIdx * cellWidth}
                    y={scaleIdx * cellHeight}
                    width={cellWidth}
                    height={cellHeight}
                    fill={colorScale(power[scaleIdx][timeIdx])}
                  />
                ))}
              </g>
            ))}
          </g>

          {/* Y-axis (scales) */}
          <text x={-20} y={20} fontSize={12} textAnchor="middle">
            Scale (days)
          </text>
          {[0, Math.floor(scales.length / 2), scales.length - 1].map(idx => (
            <text
              key={idx}
              x={-5}
              y={40 + idx * cellHeight + cellHeight / 2}
              fontSize={10}
              textAnchor="end"
            >
              {scales[idx].toFixed(0)}
            </text>
          ))}

          {/* X-axis (time) - show first and last date */}
          <text
            x={0}
            y={40 + scales.length * cellHeight + 20}
            fontSize={10}
          >
            {dates[0]}
          </text>
          <text
            x={dates.length * cellWidth - 60}
            y={40 + scales.length * cellHeight + 20}
            fontSize={10}
          >
            {dates[dates.length - 1]}
          </text>
        </svg>
      </div>

      {/* Color scale legend */}
      <div className="mt-4 flex items-center">
        <span className="text-sm mr-2">Power:</span>
        <div className="flex items-center">
          <span className="text-xs mr-1">{minPower.toFixed(1)}</span>
          <div
            className="h-4 w-32"
            style={{
              background: `linear-gradient(to right, ${colorScale(minPower)}, ${colorScale(maxPower)})`
            }}
          />
          <span className="text-xs ml-1">{maxPower.toFixed(1)}</span>
        </div>
      </div>
    </div>
  );
}
```

---

### Component 3: Anomaly Timeline

**File:** `frontend/src/components/analytics/AnomalyTimeline.tsx`

**Purpose:** Visualize detected anomalies on timeline with severity.

```typescript
"use client";

import React from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from "recharts";

interface Anomaly {
  date: string;
  index: number;
  value: number;
  z_score?: number;
  severity: string;
}

interface AnomalyTimelineProps {
  anomalies: Anomaly[];
  historicalDates: string[];
  historicalValues: number[];
  title?: string;
}

export function AnomalyTimeline({
  anomalies,
  historicalDates,
  historicalValues,
  title = "Detected Anomalies"
}: AnomalyTimelineProps) {
  // Combine historical data
  const historicalData = historicalDates.map((date, idx) => ({
    date,
    value: historicalValues[idx],
    isAnomaly: false
  }));

  // Mark anomalies
  const anomalyDateSet = new Set(anomalies.map(a => a.date));
  const anomalyMap = new Map(anomalies.map(a => [a.date, a]));

  const chartData = historicalData.map(d => {
    const isAnomaly = anomalyDateSet.has(d.date);
    const anomaly = isAnomaly ? anomalyMap.get(d.date) : null;

    return {
      ...d,
      isAnomaly,
      severity: anomaly?.severity || "none"
    };
  });

  // Color by severity
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical": return "#ef4444";  // red-500
      case "high": return "#f97316";      // orange-500
      case "moderate": return "#eab308";  // yellow-500
      default: return "#3b82f6";          // blue-500
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            name="Date"
            tickFormatter={(tick) => new Date(tick).toLocaleDateString()}
          />
          <YAxis dataKey="value" name="Value" />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-2 border rounded shadow">
                    <p className="text-sm font-semibold">
                      {new Date(data.date).toLocaleDateString()}
                    </p>
                    <p className="text-sm">Value: {data.value.toFixed(2)}</p>
                    {data.isAnomaly && (
                      <p className="text-sm font-semibold text-red-600">
                        Anomaly Detected ({data.severity})
                      </p>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter name="Schedule Metric" data={chartData} fill="#3b82f6">
            {chartData.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.isAnomaly ? getSeverityColor(entry.severity) : "#3b82f6"}
                r={entry.isAnomaly ? 6 : 3}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>

      {/* Anomaly Summary */}
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="text-2xl font-bold text-red-600">
            {anomalies.filter(a => a.severity === "critical").length}
          </p>
          <p className="text-sm text-gray-600">Critical</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-orange-600">
            {anomalies.filter(a => a.severity === "high").length}
          </p>
          <p className="text-sm text-gray-600">High</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-yellow-600">
            {anomalies.filter(a => a.severity === "moderate").length}
          </p>
          <p className="text-sm text-gray-600">Moderate</p>
        </div>
      </div>
    </div>
  );
}
```

---

### Component 4: Forecast Chart

**File:** `frontend/src/components/analytics/ForecastChart.tsx`

**Purpose:** Visualize ARIMA forecast with confidence intervals.

```typescript
"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart
} from "recharts";

interface ForecastChartProps {
  historicalDates: string[];
  historicalValues: number[];
  forecastDates: string[];
  forecastValues: number[];
  lowerBound: number[];
  upperBound: number[];
  title?: string;
}

export function ForecastChart({
  historicalDates,
  historicalValues,
  forecastDates,
  forecastValues,
  lowerBound,
  upperBound,
  title = "Workload Forecast"
}: ForecastChartProps) {
  // Combine historical and forecast data
  const historicalData = historicalDates.map((date, idx) => ({
    date,
    historical: historicalValues[idx],
    forecast: null,
    lower: null,
    upper: null
  }));

  const forecastData = forecastDates.map((date, idx) => ({
    date,
    historical: null,
    forecast: forecastValues[idx],
    lower: lowerBound[idx],
    upper: upperBound[idx]
  }));

  const chartData = [...historicalData, ...forecastData];

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tickFormatter={(tick) => new Date(tick).toLocaleDateString()}
          />
          <YAxis />
          <Tooltip
            labelFormatter={(label) => new Date(label).toLocaleDateString()}
          />
          <Legend />

          {/* Confidence interval */}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="#93c5fd"
            fillOpacity={0.3}
            name="95% Confidence"
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#ffffff"
            fillOpacity={1}
          />

          {/* Historical data */}
          <Line
            type="monotone"
            dataKey="historical"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Historical"
          />

          {/* Forecast */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#ef4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ r: 4 }}
            name="Forecast"
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Forecast summary */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">7-Day Forecast Range</p>
          <p className="text-lg font-semibold">
            {Math.min(...lowerBound).toFixed(1)} - {Math.max(...upperBound).toFixed(1)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Expected Change</p>
          <p className="text-lg font-semibold">
            {((forecastValues[forecastValues.length - 1] - historicalValues[historicalValues.length - 1]) / historicalValues[historicalValues.length - 1] * 100).toFixed(1)}%
          </p>
        </div>
      </div>
    </div>
  );
}
```

---

## Alert Integration

### Alert Service Integration

**File:** `backend/app/analytics/signal_processing_service.py`

```python
async def generate_anomaly_alerts(
    self,
    anomalies: List[Anomaly],
    metric_type: str
) -> None:
    """
    Generate alerts for detected anomalies.

    Integrates with existing notification system to alert coordinators
    when critical anomalies are detected.

    Args:
        anomalies: List of detected anomalies
        metric_type: Type of metric analyzed
    """
    from app.services.email_service import EmailService
    from app.models.user import User

    email_service = EmailService()

    # Filter critical and high severity anomalies
    critical_anomalies = [
        a for a in anomalies
        if a.severity in ["critical", "high"]
    ]

    if not critical_anomalies:
        return

    # Get coordinators and admins
    coordinators = self.db.query(User).filter(
        User.role.in_(["ADMIN", "COORDINATOR"]),
        User.is_active == True
    ).all()

    # Format alert message
    alert_message = f"""
Signal Processing Alert: {len(critical_anomalies)} anomalies detected in {metric_type}

Detected Anomalies:
"""

    for anomaly in critical_anomalies[:10]:  # Top 10
        alert_message += f"- {anomaly.date}: {anomaly.severity} (z-score: {anomaly.z_score:.2f})\n"

    # Send email alerts
    for coordinator in coordinators:
        await email_service.send_email(
            to=coordinator.email,
            subject=f"Schedule Anomaly Alert - {metric_type}",
            body=alert_message
        )

    logger.info(
        f"Sent {len(coordinators)} anomaly alerts for {len(critical_anomalies)} anomalies"
    )
```

### Alert Configuration

**File:** `backend/app/core/config.py`

Add configuration settings:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Signal Processing Alerts
    SIGNAL_PROCESSING_ALERTS_ENABLED: bool = True
    ANOMALY_DETECTION_THRESHOLD_CRITICAL: float = 4.0  # Z-score
    ANOMALY_DETECTION_THRESHOLD_HIGH: float = 3.0
    TRANSIENT_EVENT_ALERT_THRESHOLD: float = 3.5
    CHANGE_POINT_ALERT_ENABLED: bool = True
```

---

## Caching Strategy

### Cache Implementation

**Service Method:**

```python
async def _get_or_compute_cached(
    self,
    analysis_type: str,
    metric_type: str,
    start_date: date,
    end_date: date,
    person_ids: Optional[List[str]],
    compute_func: Callable,
    ttl_hours: int = 24
) -> Dict:
    """
    Get cached result or compute and cache.

    Args:
        analysis_type: Type of analysis
        metric_type: Metric being analyzed
        start_date: Analysis start date
        end_date: Analysis end date
        person_ids: Optional person filter
        compute_func: Function to compute result if cache miss
        ttl_hours: Cache TTL in hours

    Returns:
        Analysis results (from cache or freshly computed)
    """
    from app.models.signal_analysis import SignalAnalysisCache

    # Generate cache key
    cache_key = SignalAnalysisCache.generate_cache_key(
        analysis_type=analysis_type,
        metric_type=metric_type,
        start_date=start_date,
        end_date=end_date,
        person_ids=person_ids
    )

    # Check cache
    cached = self.db.query(SignalAnalysisCache).filter_by(**cache_key).first()

    if cached and not cached.is_expired():
        logger.info(f"Cache hit for {analysis_type}/{metric_type}")
        return cached.results

    # Cache miss - compute
    logger.info(f"Cache miss for {analysis_type}/{metric_type}, computing...")
    import time
    start_time = time.time()

    results = await compute_func()

    processing_time = (time.time() - start_time) * 1000

    # Store in cache
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

    if cached:
        # Update existing cache entry
        cached.results = results
        cached.computed_at = datetime.utcnow()
        cached.processing_time_ms = processing_time
        cached.expires_at = expires_at
    else:
        # Create new cache entry
        cached = SignalAnalysisCache(
            **cache_key,
            results=results,
            processing_time_ms=processing_time,
            expires_at=expires_at
        )
        self.db.add(cached)

    self.db.commit()

    logger.info(f"Cached {analysis_type} results (computed in {processing_time:.1f}ms)")

    return results
```

### Cache Invalidation

**Trigger:** Invalidate cache when schedule changes.

```python
# In assignment_service.py or similar

async def create_assignment(self, ...):
    """Create assignment and invalidate signal processing cache."""

    # ... create assignment ...

    # Invalidate cache for affected date range
    await self._invalidate_signal_cache(assignment.block.date)

async def _invalidate_signal_cache(self, changed_date: date):
    """Invalidate cached signal processing results affected by schedule change."""
    from app.models.signal_analysis import SignalAnalysisCache

    # Delete cache entries that overlap with changed date
    self.db.query(SignalAnalysisCache).filter(
        SignalAnalysisCache.start_date <= changed_date,
        SignalAnalysisCache.end_date >= changed_date
    ).delete()

    self.db.commit()
    logger.info(f"Invalidated signal cache for date {changed_date}")
```

---

## Testing Requirements

### Unit Tests

**File:** `backend/tests/analytics/signal_processing/test_fourier_analyzer.py`

```python
"""
Unit tests for Fourier analysis.
"""
import numpy as np
import pytest

from app.analytics.signal_processing.fourier_analyzer import FourierScheduleAnalyzer


class TestFourierScheduleAnalyzer:
    """Test suite for Fourier analysis."""

    def test_detect_weekly_pattern(self):
        """Test detection of weekly (7-day) pattern."""
        analyzer = FourierScheduleAnalyzer(sampling_rate=1.0)

        # Generate synthetic weekly pattern
        n = 365
        t = np.arange(n)
        signal = 10 + 5 * np.sin(2 * np.pi * t / 7.0)  # 7-day period

        dates = np.arange(n)

        # Analyze
        result = analyzer.analyze_workload_periodicity(signal, dates)

        # Assert weekly period detected
        dominant = result['dominant_periods'][0]
        assert 6.5 <= dominant['period_days'] <= 7.5
        assert dominant['type'] == 'weekly'
        assert dominant['significance'] in ['highly_significant', 'significant']

    def test_detect_harmonics(self):
        """Test harmonic detection for fundamental period."""
        analyzer = FourierScheduleAnalyzer(sampling_rate=1.0)

        # Generate signal with fundamental + 2nd harmonic
        n = 365
        t = np.arange(n)
        signal = (
            10 +
            5 * np.sin(2 * np.pi * t / 7.0) +      # Fundamental
            2 * np.sin(2 * np.pi * t / 3.5)        # 2nd harmonic
        )

        # Detect harmonics
        harmonics = analyzer.detect_rotation_harmonics(signal, fundamental_period=7.0)

        # Assert both harmonics detected
        assert harmonics[0]['harmonic_number'] == 1
        assert harmonics[0]['amplitude'] > 4.5  # Close to 5

        assert harmonics[1]['harmonic_number'] == 2
        assert harmonics[1]['amplitude'] > 1.5  # Close to 2

    def test_cross_spectrum_coherence(self):
        """Test cross-spectrum computation for correlated signals."""
        analyzer = FourierScheduleAnalyzer(sampling_rate=1.0)

        # Generate two correlated signals
        n = 365
        t = np.arange(n)
        signal1 = 10 + 5 * np.sin(2 * np.pi * t / 7.0)
        signal2 = 12 + 5 * np.sin(2 * np.pi * t / 7.0 + np.pi / 4)  # Phase shift

        # Compute cross-spectrum
        result = analyzer.compute_cross_spectrum(signal1, signal2)

        # Assert high coherence at weekly frequency
        weekly_freq_idx = np.argmin(np.abs(np.array(result['frequencies']) - 1/7.0))
        coherence_at_weekly = result['coherence'][weekly_freq_idx]

        assert coherence_at_weekly > 0.9  # High coherence
```

**Similar test files for:**
- `test_wavelet_analyzer.py`
- `test_filter.py`
- `test_decomposer.py`
- `test_anomaly_detector.py`
- `test_pipeline.py`

### Integration Tests

**File:** `backend/tests/analytics/signal_processing/test_service.py`

```python
"""
Integration tests for signal processing service.
"""
import pytest
from datetime import date, timedelta

from app.analytics.signal_processing_service import SignalProcessingService


@pytest.mark.asyncio
class TestSignalProcessingService:
    """Integration tests for signal processing service."""

    async def test_end_to_end_fourier_analysis(self, db, sample_schedule_data):
        """Test end-to-end Fourier analysis with real database."""
        service = SignalProcessingService(db)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        # Run Fourier analysis
        result = await service.analyze_fourier(
            start_date=start_date,
            end_date=end_date,
            person_ids=None,
            metric_type="workload",
            detect_harmonics=True,
            fundamental_period=7.0
        )

        # Assert result structure
        assert 'dominant_periods' in result
        assert len(result['dominant_periods']) > 0
        assert result['total_power'] > 0

    async def test_cache_hit_performance(self, db, sample_schedule_data):
        """Test that cache improves performance on repeated queries."""
        service = SignalProcessingService(db)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        # First call (cache miss)
        import time
        start = time.time()
        result1 = await service.analyze_fourier(
            start_date=start_date,
            end_date=end_date,
            metric_type="workload"
        )
        time_uncached = time.time() - start

        # Second call (cache hit)
        start = time.time()
        result2 = await service.analyze_fourier(
            start_date=start_date,
            end_date=end_date,
            metric_type="workload"
        )
        time_cached = time.time() - start

        # Assert cache hit is faster
        assert time_cached < time_uncached * 0.5  # At least 2x faster

        # Assert results identical
        assert result1 == result2
```

### Load/Performance Tests

**File:** `backend/tests/performance/test_signal_processing_load.py`

```python
"""
Performance tests for signal processing under load.
"""
import pytest
from datetime import date


@pytest.mark.performance
class TestSignalProcessingPerformance:
    """Performance benchmarks for signal processing."""

    async def test_fourier_analysis_latency(self, db, large_schedule_dataset):
        """Test Fourier analysis latency for large dataset (1 year)."""
        from app.analytics.signal_processing_service import SignalProcessingService

        service = SignalProcessingService(db)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        import time
        start = time.time()

        result = await service.analyze_fourier(
            start_date=start_date,
            end_date=end_date,
            metric_type="workload"
        )

        elapsed_ms = (time.time() - start) * 1000

        # Assert meets SLA (<100ms for dashboard)
        assert elapsed_ms < 100, f"Fourier analysis took {elapsed_ms:.1f}ms (target <100ms)"

    async def test_comprehensive_analysis_throughput(self, db, large_schedule_dataset):
        """Test comprehensive analysis can handle concurrent requests."""
        from app.analytics.signal_processing_service import SignalProcessingService
        import asyncio

        service = SignalProcessingService(db)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        # Run 10 concurrent comprehensive analyses
        tasks = [
            service.comprehensive_analysis(
                start_date=start_date,
                end_date=end_date,
                metric_type="workload"
            )
            for _ in range(10)
        ]

        import time
        start = time.time()

        results = await asyncio.gather(*tasks)

        elapsed_s = time.time() - start

        # Assert reasonable throughput
        assert elapsed_s < 5.0, f"10 concurrent analyses took {elapsed_s:.1f}s (target <5s)"
        assert len(results) == 10
```

---

## Performance Benchmarks

### Target Latencies

| Operation | Target | Optimization |
|-----------|--------|--------------|
| **Fourier Analysis (1 year)** | <100ms | Cache results, use scipy FFT |
| **Wavelet CWT (1 year)** | <500ms | Downsample to 365 points, use pywt |
| **Anomaly Detection** | <50ms | Use Isolation Forest (sklearn), cache |
| **STL Decomposition** | <200ms | Statsmodels optimized implementation |
| **ARIMA Forecast** | <300ms | Cache fitted models, reuse for similar data |
| **Comprehensive Analysis** | <1000ms | Parallel execution, cache all components |

### Optimization Strategies

1. **Data Pipeline Optimization**
   - Use database indexes on `block.date`, `assignment.person_id`
   - Batch queries for multiple metrics
   - Use `numpy` arrays (avoid Python loops)

2. **Computation Optimization**
   - Use `scipy.fft.fft` (fastest FFT implementation)
   - Downsample long time series before CWT (>365 days → resample to daily)
   - Cache sklearn models (Isolation Forest) between requests

3. **Caching Strategy**
   - Cache Fourier/wavelet results for 24 hours
   - Invalidate cache on schedule changes (only affected date ranges)
   - Use PostgreSQL JSONB for fast cache queries

4. **Parallel Processing**
   - Use `asyncio.gather()` for independent analyses
   - Run Fourier + Wavelet + Anomaly in parallel for comprehensive analysis

---

## Deployment Plan

### Phase 1: Core Infrastructure (Week 1)

- [ ] Create database migration for `signal_analysis_cache` table
- [ ] Implement `TimeSeriesPipeline` for data extraction
- [ ] Set up directory structure and module scaffolding

### Phase 2: Analysis Modules (Week 2-3)

- [ ] Implement `FourierScheduleAnalyzer`
- [ ] Implement `WaveletScheduleAnalyzer`
- [ ] Implement `ScheduleFilter`
- [ ] Implement `TimeSeriesDecomposer`
- [ ] Implement `ScheduleAnomalyDetector`
- [ ] Write unit tests for all modules (>90% coverage)

### Phase 3: Service Layer (Week 4)

- [ ] Implement `SignalProcessingService` orchestrator
- [ ] Implement caching logic with `signal_analysis_cache`
- [ ] Implement alert generation integration
- [ ] Write integration tests

### Phase 4: API Endpoints (Week 5)

- [ ] Create Pydantic schemas (`signal_processing.py`)
- [ ] Implement API routes (`/api/v1/signals/*`)
- [ ] Add authentication and authorization checks
- [ ] Write API integration tests

### Phase 5: Frontend Components (Week 6)

- [ ] Implement `SpectralPlot` component
- [ ] Implement `WaveletScalogram` component
- [ ] Implement `AnomalyTimeline` component
- [ ] Implement `ForecastChart` component
- [ ] Create dashboard page for signal processing analytics

### Phase 6: Testing & Optimization (Week 7)

- [ ] Run performance benchmarks
- [ ] Optimize slow queries and computations
- [ ] Load testing with k6
- [ ] Fix any bugs discovered in testing

### Phase 7: Documentation & Deployment (Week 8)

- [ ] Update API documentation
- [ ] Create user guide for signal processing features
- [ ] Deploy to staging environment
- [ ] User acceptance testing
- [ ] Deploy to production

---

## Security Considerations

### Data Privacy

- **No PII in Signal Data**: Signal processing operates on aggregated metrics only
- **Access Control**: All API endpoints require authentication
- **Role-Based Access**: Only ADMIN and COORDINATOR roles can access signal analytics
- **Audit Logging**: Log all signal processing API calls with user ID and parameters

### Input Validation

```python
# Example validation in API route
@router.post("/signals/fft")
async def analyze_fourier_spectrum(
    request: FourierAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Validate date range
    if request.end_date < request.start_date:
        raise HTTPException(400, "end_date must be after start_date")

    # Validate date range not too large (prevent DoS)
    date_range_days = (request.end_date - request.start_date).days
    if date_range_days > 730:  # Max 2 years
        raise HTTPException(400, "Date range cannot exceed 2 years")

    # Validate person_ids (prevent injection)
    if request.person_ids:
        for person_id in request.person_ids:
            if not person_id.isalnum():
                raise HTTPException(400, "Invalid person_id format")

    # ... proceed with analysis ...
```

### Rate Limiting

- Apply rate limits to prevent abuse:
  - Fourier/Wavelet: 60 requests/hour per user
  - Comprehensive Analysis: 10 requests/hour per user (expensive)

### Error Handling

- Never leak sensitive information in error messages
- Use generic error messages for 4xx/5xx responses
- Log detailed errors server-side only

---

## Dependencies

### Python Packages (Add to `backend/requirements.txt`)

```txt
# Signal Processing
scipy>=1.11.0                # FFT, filtering, signal processing
pywavelets>=1.4.1           # Wavelet transforms
statsmodels>=0.14.0         # STL decomposition, ARIMA
ruptures>=1.1.8             # Change point detection (PELT)
scikit-learn>=1.3.0         # Isolation Forest, preprocessing
```

### Installation

```bash
cd backend
pip install scipy pywavelets statsmodels ruptures scikit-learn
pip freeze > requirements.txt
```

---

## Success Metrics

### Technical Metrics

- **API Latency**: P95 < 100ms for cached queries, P95 < 500ms for uncached
- **Test Coverage**: >90% for all signal processing modules
- **Cache Hit Rate**: >80% for repeated queries
- **False Positive Rate (Anomalies)**: <5%
- **Forecast Accuracy (7-day)**: >85% (MAPE)

### Business Metrics

- **Early Warning Lead Time**: 2-4 weeks advance notice of schedule degradation
- **Pattern Detection Accuracy**: 95%+ for known rotation cycles
- **User Adoption**: 50%+ of coordinators use signal analytics within 3 months
- **Alert Actionability**: 70%+ of anomaly alerts result in corrective action

---

## Future Enhancements

### Phase 2 (Q2 2026)

- **Real-time Streaming**: WebSocket-based real-time signal monitoring
- **Machine Learning**: Train custom anomaly detection models on historical data
- **Multi-variate Forecasting**: VARIMA models for forecasting multiple metrics simultaneously
- **Automated Interventions**: Auto-generate schedule adjustments when critical anomalies detected

### Phase 3 (Q3 2026)

- **Explainable AI**: SHAP values for anomaly explanations
- **Causal Analysis**: Granger causality tests for identifying root causes
- **Burnout Prediction**: Integrate with SIR epidemiology models from resilience framework
- **Mobile App**: Push notifications for critical signal processing alerts

---

## Appendix

### Mathematical Foundations

Refer to `docs/research/SIGNAL_PROCESSING_SCHEDULE_ANALYSIS.md` for:
- Fourier Transform equations
- Wavelet Transform mathematics
- Filter design theory
- STL decomposition algorithm
- ARIMA model equations
- Anomaly detection statistics

### References

1. Oppenheim, A. V., & Schafer, R. W. (2009). *Discrete-Time Signal Processing*
2. Mallat, S. (2008). *A Wavelet Tour of Signal Processing*
3. Cleveland, R. B., et al. (1990). STL: A seasonal-trend decomposition procedure
4. Killick, R., et al. (2012). Optimal detection of changepoints (PELT)
5. Liu, F. T., et al. (2008). Isolation forest
6. SciPy Documentation: https://docs.scipy.org/doc/scipy/reference/signal.html
7. PyWavelets Documentation: https://pywavelets.readthedocs.io/
8. Statsmodels Documentation: https://www.statsmodels.org/

---

**Implementation Start Date:** 2026-01-06
**Target Completion:** 2026-02-28 (8 weeks)
**Status:** READY FOR IMPLEMENTATION

**Questions/Clarifications:** Contact development team or refer to research document.
