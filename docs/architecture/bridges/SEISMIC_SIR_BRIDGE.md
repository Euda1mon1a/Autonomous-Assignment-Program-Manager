# Seismic-SIR Bridge Specification

> **Cross-Disciplinary Integration**: Earthquake Precursor Detection → Epidemic Transmission Dynamics
>
> **Last Updated**: 2025-12-26
> **Status**: Implementation Ready
> **Estimated Effort**: 6-8 hours
> **Files Modified**: 3 (2 new, 1 updated)
> **Lines of Code**: ~250 lines

---

## Executive Summary

The **Seismic-SIR Bridge** connects two cross-disciplinary resilience systems:

1. **Seismic Detection** (from seismology): Detects behavioral precursors using STA/LTA algorithm
2. **Burnout Epidemiology** (from epidemiology): Models burnout spread using SIR epidemic model

**The Bridge Concept**: Individual behavioral precursors (P-waves) detected by seismic analysis should modulate the transmission rate (β) in the SIR model. When residents show early warning signs (increased swap requests, sick calls, etc.), the "contagiousness" of burnout increases—stressed individuals amplify stress in their close contacts.

**Why This Matters**:
- Seismic detection identifies **who** is at risk (individual level)
- SIR modeling predicts **spread** through the network (population level)
- Bridging them creates **dynamic feedback**: individual precursors → population transmission → escalating interventions

---

## Table of Contents

1. [Mathematical Foundation](#1-mathematical-foundation)
2. [Data Flow Diagram](#2-data-flow-diagram)
3. [Implementation Specification](#3-implementation-specification)
4. [Configuration](#4-configuration)
5. [Test Cases](#5-test-cases)
6. [Integration Points](#6-integration-points)
7. [Implementation Estimate](#7-implementation-estimate)
8. [References](#8-references)

---

## 1. Mathematical Foundation

### 1.1 STA/LTA to Beta Mapping

The bridge transforms seismic precursor signals into dynamic adjustments to the SIR transmission rate.

**Base Formula**:

```
β_adjusted = β_base × (1 + α × f(STA/LTA))
```

Where:
- `β_base`: Baseline transmission rate (default: 0.05 = 5% per week)
- `α`: Sensitivity parameter (default: 0.3 = 30% amplification per unit)
- `f(STA/LTA)`: Normalized transformation function

### 1.2 Transformation Function

The transformation function `f(STA/LTA)` normalizes the seismic ratio to a beta multiplier:

**Piecewise Function**:

```
f(r) = {
    0                           if r < 2.5    (no trigger)
    log₂(r / 2.5)              if 2.5 ≤ r < 10.0  (moderate)
    log₂(4) + 0.5×(r - 10)     if r ≥ 10.0   (critical)
}
```

Where `r` is the STA/LTA ratio.

**Rationale**:
- **No adjustment** below trigger threshold (2.5)
- **Logarithmic scaling** in moderate range (matches seismic magnitude scaling)
- **Linear continuation** in critical range (prevents β from exceeding 1.0)

**Example Values**:

| STA/LTA Ratio | f(r)   | β_adjusted (α=0.3, β_base=0.05) |
|---------------|--------|----------------------------------|
| 1.0           | 0.00   | 0.050 (no change)                |
| 2.5           | 0.00   | 0.050 (trigger threshold)        |
| 5.0           | 1.00   | 0.065 (+30%)                     |
| 10.0          | 2.00   | 0.080 (+60%)                     |
| 15.0          | 4.50   | 0.118 (+136%)                    |
| 20.0          | 7.00   | 0.155 (+210%)                    |

### 1.3 Aggregation Across Multiple Residents

When multiple residents show precursors simultaneously, aggregate using weighted average:

```
β_total = β_base × (1 + α × Σᵢ wᵢ × f(rᵢ))
```

Where:
- `i`: Index over residents with detected precursors
- `wᵢ`: Weight for resident `i` (default: `degree(i) / Σ degree`)
- `rᵢ`: STA/LTA ratio for resident `i`

**Weight Formula** (degree-weighted):

```
wᵢ = degree(resident_i) / Σⱼ degree(resident_j)
```

Higher-connectivity residents (potential super-spreaders) get higher weights.

### 1.4 Temporal Smoothing

To prevent β from oscillating wildly, apply exponential moving average:

```
β_smoothed(t) = γ × β_current(t) + (1 - γ) × β_smoothed(t-1)
```

Where:
- `γ`: Smoothing factor (default: 0.2 = 20% weight on new value)
- Higher γ = faster response to new data
- Lower γ = more stable, slower response

### 1.5 Clamping

Always ensure β stays within valid bounds:

```
β_final = clamp(β_smoothed, min=0.01, max=0.95)
```

- **Min (0.01)**: Prevent β from going to zero (unrealistic)
- **Max (0.95)**: Prevent β from reaching 1.0 (SIR model instability)

---

## 2. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SEISMIC DETECTION LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [Time Series Data]                                                 │
│   - Swap requests                                                   │
│   - Sick calls                     ┌──────────────────────┐        │
│   - Response delays        ───────>│ BurnoutEarlyWarning  │        │
│   - Preference declines            │  .detect_precursors()│        │
│   - Coverage declines              └──────────┬───────────┘        │
│                                               │                     │
│                                               v                     │
│                                      [SeismicAlert]                 │
│                                       - sta_lta_ratio               │
│                                       - severity                    │
│                                       - resident_id                 │
└───────────────────────────────────────────┬─────────────────────────┘
                                            │
                                            v
┌─────────────────────────────────────────────────────────────────────┐
│                      SEISMIC-SIR BRIDGE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────┐           │
│  │         SeismicSIRBridge                            │           │
│  ├─────────────────────────────────────────────────────┤           │
│  │                                                     │           │
│  │  1. collect_precursor_signals()                    │           │
│  │     └─> Gather all active SeismicAlerts            │           │
│  │                                                     │           │
│  │  2. transform_sta_lta_to_beta_delta()              │           │
│  │     └─> Apply f(r) transformation                  │           │
│  │     └─> Weight by network degree                   │           │
│  │     └─> Aggregate across residents                 │           │
│  │                                                     │           │
│  │  3. smooth_beta_adjustment()                       │           │
│  │     └─> Apply exponential moving average           │           │
│  │                                                     │           │
│  │  4. clamp_beta()                                   │           │
│  │     └─> Ensure β ∈ [0.01, 0.95]                    │           │
│  │                                                     │           │
│  │  5. update_sir_model()                             │           │
│  │     └─> Send β_adjusted to epidemiology service    │           │
│  │                                                     │           │
│  └─────────────────────────────────────────────────────┘           │
│                                                                     │
└───────────────────────────────────────────┬─────────────────────────┘
                                            │
                                            v
┌─────────────────────────────────────────────────────────────────────┐
│                   BURNOUT EPIDEMIOLOGY LAYER                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────┐                   │
│  │  BurnoutEpidemiology                        │                   │
│  ├─────────────────────────────────────────────┤                   │
│  │                                             │                   │
│  │  update_transmission_rate(β_new)           │                   │
│  │    └─> Updates β in BurnoutSIRModel        │                   │
│  │                                             │                   │
│  │  simulate_sir_spread(beta=β_new)           │                   │
│  │    └─> Run SIR simulation with new β       │                   │
│  │                                             │                   │
│  │  calculate_reproduction_number()           │                   │
│  │    └─> Recompute Rt with updated β         │                   │
│  │                                             │                   │
│  └─────────────────────────────────────────────┘                   │
│                                                                     │
│  [Output]                                                           │
│   - Updated Rt (reproduction number)                                │
│   - Revised intervention recommendations                            │
│   - Projected epidemic trajectory                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Specification

### 3.1 New Class: `SeismicSIRBridge`

**File**: `backend/app/resilience/seismic_sir_bridge.py`

```python
"""
Seismic-SIR Bridge: Connects earthquake precursor detection to epidemic modeling.

Transforms individual behavioral precursors (detected via STA/LTA seismic analysis)
into dynamic adjustments to the SIR epidemic transmission rate (β).
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import numpy as np

from app.resilience.seismic_detection import BurnoutEarlyWarning, SeismicAlert
from app.resilience.burnout_epidemiology import BurnoutEpidemiology

logger = logging.getLogger(__name__)


@dataclass
class BetaAdjustment:
    """
    Record of a beta adjustment event.

    Tracks how seismic precursors modified the SIR transmission rate.
    """

    timestamp: datetime
    beta_base: float
    beta_adjusted: float
    sta_lta_max: float
    num_active_alerts: int
    affected_residents: list[UUID]
    adjustment_magnitude: float  # Percentage change

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "beta_base": self.beta_base,
            "beta_adjusted": self.beta_adjusted,
            "sta_lta_max": self.sta_lta_max,
            "num_active_alerts": self.num_active_alerts,
            "affected_residents": [str(r) for r in self.affected_residents],
            "adjustment_magnitude": self.adjustment_magnitude,
        }


class SeismicSIRBridge:
    """
    Bridge between seismic precursor detection and SIR epidemic modeling.

    Transforms individual-level behavioral signals (STA/LTA ratios) into
    population-level transmission dynamics (β adjustments).

    Example:
        bridge = SeismicSIRBridge(
            seismic_detector=detector,
            epidemiology_model=epi_model,
            sensitivity=0.3,
            smoothing_factor=0.2
        )

        # Process new seismic alerts
        alerts = detector.detect_precursors(...)
        bridge.update_from_alerts(alerts)

        # SIR model now uses updated β
        epi_model.simulate_sir_spread()
    """

    def __init__(
        self,
        seismic_detector: BurnoutEarlyWarning,
        epidemiology_model: BurnoutEpidemiology,
        sensitivity: float = 0.3,
        smoothing_factor: float = 0.2,
        beta_base: float = 0.05,
    ):
        """
        Initialize the seismic-SIR bridge.

        Args:
            seismic_detector: Seismic precursor detection system
            epidemiology_model: SIR epidemic model
            sensitivity: Sensitivity parameter α (0.0-1.0)
            smoothing_factor: Exponential moving average factor γ (0.0-1.0)
            beta_base: Baseline transmission rate (default: 0.05 = 5% per week)

        Raises:
            ValueError: If parameters are out of valid ranges
        """
        if not 0 <= sensitivity <= 1:
            raise ValueError(f"sensitivity must be in [0, 1], got {sensitivity}")
        if not 0 <= smoothing_factor <= 1:
            raise ValueError(f"smoothing_factor must be in [0, 1], got {smoothing_factor}")
        if not 0.01 <= beta_base <= 0.95:
            raise ValueError(f"beta_base must be in [0.01, 0.95], got {beta_base}")

        self.seismic_detector = seismic_detector
        self.epidemiology_model = epidemiology_model
        self.sensitivity = sensitivity
        self.smoothing_factor = smoothing_factor
        self.beta_base = beta_base

        # State tracking
        self._beta_smoothed: float = beta_base
        self._adjustment_history: list[BetaAdjustment] = []
        self._active_alerts: dict[UUID, SeismicAlert] = {}

        logger.info(
            f"SeismicSIRBridge initialized: α={sensitivity}, γ={smoothing_factor}, "
            f"β_base={beta_base}"
        )

    def update_from_alerts(self, alerts: list[SeismicAlert]) -> BetaAdjustment:
        """
        Update SIR transmission rate based on new seismic alerts.

        Args:
            alerts: List of newly detected seismic alerts

        Returns:
            BetaAdjustment record documenting the change
        """
        # Update active alerts
        for alert in alerts:
            if alert.resident_id:
                self._active_alerts[alert.resident_id] = alert

        # Prune old alerts (>7 days)
        self._prune_old_alerts(max_age=timedelta(days=7))

        # Calculate beta adjustment
        beta_delta = self._calculate_beta_delta()
        beta_current = self.beta_base * (1 + self.sensitivity * beta_delta)

        # Apply smoothing
        self._beta_smoothed = (
            self.smoothing_factor * beta_current
            + (1 - self.smoothing_factor) * self._beta_smoothed
        )

        # Clamp to valid range
        beta_final = np.clip(self._beta_smoothed, 0.01, 0.95)

        # Update epidemiology model
        self.epidemiology_model.update_transmission_rate(beta_final)

        # Record adjustment
        sta_lta_max = max(
            (a.sta_lta_ratio for a in self._active_alerts.values()),
            default=0.0
        )

        adjustment = BetaAdjustment(
            timestamp=datetime.now(),
            beta_base=self.beta_base,
            beta_adjusted=beta_final,
            sta_lta_max=sta_lta_max,
            num_active_alerts=len(self._active_alerts),
            affected_residents=list(self._active_alerts.keys()),
            adjustment_magnitude=(beta_final - self.beta_base) / self.beta_base * 100,
        )

        self._adjustment_history.append(adjustment)

        logger.info(
            f"Beta adjusted: {self.beta_base:.4f} → {beta_final:.4f} "
            f"({adjustment.adjustment_magnitude:+.1f}%) from {len(alerts)} new alerts"
        )

        return adjustment

    def _calculate_beta_delta(self) -> float:
        """
        Calculate aggregate beta delta from all active alerts.

        Returns:
            Aggregate f(r) value across all residents
        """
        if not self._active_alerts:
            return 0.0

        # Get network degrees for weighting
        network = self.epidemiology_model.network
        total_delta = 0.0
        total_weight = 0.0

        for resident_id, alert in self._active_alerts.items():
            # Transform STA/LTA to beta delta
            f_r = self._transform_sta_lta(alert.sta_lta_ratio)

            # Weight by network connectivity (super-spreaders matter more)
            if resident_id in network:
                weight = network.degree(resident_id)
            else:
                weight = 1.0

            total_delta += weight * f_r
            total_weight += weight

        # Weighted average
        if total_weight > 0:
            return total_delta / total_weight
        return 0.0

    @staticmethod
    def _transform_sta_lta(ratio: float) -> float:
        """
        Transform STA/LTA ratio to beta delta using f(r) function.

        Args:
            ratio: STA/LTA ratio from seismic detection

        Returns:
            Normalized beta adjustment value
        """
        if ratio < 2.5:
            # Below trigger threshold - no adjustment
            return 0.0

        elif ratio < 10.0:
            # Moderate range - logarithmic scaling
            return np.log2(ratio / 2.5)

        else:
            # Critical range - linear continuation
            return np.log2(4.0) + 0.5 * (ratio - 10.0)

    def _prune_old_alerts(self, max_age: timedelta):
        """
        Remove alerts older than max_age.

        Args:
            max_age: Maximum age to keep alerts
        """
        cutoff = datetime.now() - max_age
        to_remove = [
            resident_id
            for resident_id, alert in self._active_alerts.items()
            if alert.trigger_time < cutoff
        ]

        for resident_id in to_remove:
            del self._active_alerts[resident_id]

        if to_remove:
            logger.debug(f"Pruned {len(to_remove)} old alerts (>{max_age.days} days)")

    def get_current_beta(self) -> float:
        """Get current smoothed beta value."""
        return self._beta_smoothed

    def get_adjustment_history(
        self, limit: Optional[int] = None
    ) -> list[BetaAdjustment]:
        """
        Get history of beta adjustments.

        Args:
            limit: Maximum number of records to return (most recent first)

        Returns:
            List of BetaAdjustment records
        """
        history = sorted(
            self._adjustment_history,
            key=lambda a: a.timestamp,
            reverse=True
        )

        if limit:
            return history[:limit]
        return history

    def reset_beta(self):
        """Reset beta to baseline (remove all adjustments)."""
        self._beta_smoothed = self.beta_base
        self._active_alerts.clear()
        self.epidemiology_model.update_transmission_rate(self.beta_base)
        logger.info(f"Beta reset to baseline: {self.beta_base}")
```

### 3.2 New Method: `BurnoutEpidemiology.update_transmission_rate()`

**File**: `backend/app/resilience/burnout_epidemiology.py`

Add this method to the existing `BurnoutEpidemiology` class:

```python
def update_transmission_rate(self, new_beta: float):
    """
    Update the transmission rate for future SIR simulations.

    This method is called by the SeismicSIRBridge to dynamically
    adjust β based on seismic precursor signals.

    Args:
        new_beta: New transmission rate (0.01-0.95)

    Raises:
        ValueError: If new_beta is outside valid range
    """
    if not 0.01 <= new_beta <= 0.95:
        raise ValueError(f"new_beta must be in [0.01, 0.95], got {new_beta}")

    # Store as instance variable for use in simulations
    self._current_beta = new_beta

    logger.info(f"Transmission rate updated: β={new_beta:.4f}")
```

Also add initialization in `__init__`:

```python
def __init__(self, social_network: nx.Graph):
    # ... existing code ...

    # Default beta (can be overridden by bridge)
    self._current_beta: float = 0.05  # 5% per week default
```

And update `simulate_sir_spread()` to use `self._current_beta` if `beta` parameter is not provided:

```python
def simulate_sir_spread(
    self,
    initial_infected: set[UUID],
    beta: float | None = None,  # Make optional
    gamma: float = 0.02,
    steps: int = 52,
) -> list[dict]:
    """
    Simulate SIR epidemic spread over time.

    Args:
        initial_infected: Initial set of burned out residents
        beta: Transmission rate (if None, uses current value from bridge)
        gamma: Recovery rate per time step (default 0.02)
        steps: Number of time steps to simulate (default 52 = 1 year)

    Returns:
        List of dicts with S, I, R counts at each time step
    """
    # Use current beta if not explicitly provided
    if beta is None:
        beta = self._current_beta

    # ... rest of existing code ...
```

### 3.3 Integration Service

**File**: `backend/app/services/seismic_sir_integration_service.py`

```python
"""
Service for integrating seismic detection with SIR epidemic modeling.

Orchestrates the seismic-SIR bridge and provides high-level API for
the resilience monitoring system.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.resilience.burnout_epidemiology import BurnoutEpidemiology
from app.resilience.seismic_detection import BurnoutEarlyWarning, PrecursorSignal
from app.resilience.seismic_sir_bridge import SeismicSIRBridge, BetaAdjustment

logger = logging.getLogger(__name__)


class SeismicSIRIntegrationService:
    """
    High-level service for seismic-SIR integration.

    Provides API for:
    - Analyzing resident behavioral data
    - Detecting precursor signals
    - Updating SIR transmission rates
    - Generating integrated reports
    """

    def __init__(
        self,
        seismic_detector: BurnoutEarlyWarning,
        epidemiology_model: BurnoutEpidemiology,
        sensitivity: float = 0.3,
    ):
        """Initialize integration service."""
        self.bridge = SeismicSIRBridge(
            seismic_detector=seismic_detector,
            epidemiology_model=epidemiology_model,
            sensitivity=sensitivity,
        )

        self.seismic_detector = seismic_detector
        self.epidemiology_model = epidemiology_model

        logger.info("SeismicSIRIntegrationService initialized")

    async def analyze_resident_behavioral_data(
        self,
        resident_id: UUID,
        time_series_data: dict[PrecursorSignal, list[float]],
    ) -> list[SeismicAlert]:
        """
        Analyze time series data for a resident and update SIR model.

        Args:
            resident_id: Resident to analyze
            time_series_data: Dict mapping signal types to time series

        Returns:
            List of detected seismic alerts
        """
        all_alerts = []

        # Detect precursors for each signal type
        for signal_type, time_series in time_series_data.items():
            alerts = self.seismic_detector.detect_precursors(
                resident_id=resident_id,
                signal_type=signal_type,
                time_series=time_series,
            )
            all_alerts.extend(alerts)

        # Update SIR model with new alerts
        if all_alerts:
            adjustment = self.bridge.update_from_alerts(all_alerts)
            logger.info(
                f"Analyzed resident {resident_id}: {len(all_alerts)} alerts detected, "
                f"β adjusted by {adjustment.adjustment_magnitude:+.1f}%"
            )

        return all_alerts

    async def get_integrated_risk_report(self) -> dict:
        """
        Generate integrated risk report combining seismic and epidemic data.

        Returns:
            Dict with seismic alerts, current β, Rt, and recommendations
        """
        # Get current beta
        current_beta = self.bridge.get_current_beta()

        # Get active seismic alerts
        active_alerts = len(self.bridge._active_alerts)

        # Calculate current Rt with updated beta
        burned_out = set(self.epidemiology_model.burnout_history.keys())  # Simplified
        epi_report = self.epidemiology_model.calculate_reproduction_number(
            burned_out_residents=burned_out
        )

        # Get recent beta adjustments
        recent_adjustments = self.bridge.get_adjustment_history(limit=10)

        return {
            "timestamp": datetime.now().isoformat(),
            "seismic_status": {
                "active_alerts": active_alerts,
                "affected_residents": len(self.bridge._active_alerts),
            },
            "epidemic_status": {
                "current_beta": current_beta,
                "beta_base": self.bridge.beta_base,
                "beta_adjustment_pct": (
                    (current_beta - self.bridge.beta_base) / self.bridge.beta_base * 100
                ),
                "reproduction_number": epi_report.reproduction_number,
                "status": epi_report.status,
                "intervention_level": epi_report.intervention_level,
            },
            "recent_adjustments": [a.to_dict() for a in recent_adjustments],
            "recommended_interventions": epi_report.recommended_interventions,
        }
```

---

## 4. Configuration

### 4.1 Configuration Parameters

**File**: `backend/app/core/config.py`

Add to `Settings` class:

```python
# Seismic-SIR Bridge Configuration
SEISMIC_SIR_SENSITIVITY: float = Field(
    default=0.3,
    ge=0.0,
    le=1.0,
    description="Sensitivity parameter α for seismic-SIR bridge (0.0-1.0)"
)

SEISMIC_SIR_SMOOTHING: float = Field(
    default=0.2,
    ge=0.0,
    le=1.0,
    description="Exponential smoothing factor γ for beta adjustments (0.0-1.0)"
)

SEISMIC_SIR_BETA_BASE: float = Field(
    default=0.05,
    ge=0.01,
    le=0.95,
    description="Baseline SIR transmission rate β_base"
)

SEISMIC_SIR_UPDATE_INTERVAL_HOURS: int = Field(
    default=6,
    ge=1,
    le=168,
    description="How often to update beta from seismic signals (hours)"
)
```

### 4.2 Environment Variables

**.env.example**:

```bash
# Seismic-SIR Bridge
SEISMIC_SIR_SENSITIVITY=0.3          # Sensitivity (0.0-1.0)
SEISMIC_SIR_SMOOTHING=0.2            # Smoothing factor (0.0-1.0)
SEISMIC_SIR_BETA_BASE=0.05           # Baseline beta
SEISMIC_SIR_UPDATE_INTERVAL_HOURS=6  # Update frequency
```

### 4.3 Parameter Tuning Guide

| Parameter | Low | Medium (Default) | High | Effect |
|-----------|-----|------------------|------|--------|
| **Sensitivity (α)** | 0.1 | 0.3 | 0.6 | Higher → larger β adjustments |
| **Smoothing (γ)** | 0.1 | 0.2 | 0.5 | Higher → faster response, more volatile |
| **Beta Base** | 0.03 | 0.05 | 0.08 | Higher → faster baseline spread |
| **Update Interval** | 1h | 6h | 24h | Lower → more frequent updates |

**Recommended Settings by Program Size**:

| Program Size | Sensitivity | Smoothing | Beta Base | Update Interval |
|--------------|-------------|-----------|-----------|-----------------|
| Small (<10) | 0.4 | 0.3 | 0.06 | 3h |
| Medium (10-30) | 0.3 | 0.2 | 0.05 | 6h |
| Large (>30) | 0.2 | 0.15 | 0.04 | 12h |

---

## 5. Test Cases

### 5.1 Unit Tests

**File**: `backend/tests/resilience/test_seismic_sir_bridge.py`

```python
"""Tests for seismic-SIR bridge."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

import networkx as nx

from app.resilience.burnout_epidemiology import BurnoutEpidemiology, BurnoutState
from app.resilience.seismic_detection import (
    BurnoutEarlyWarning,
    SeismicAlert,
    PrecursorSignal,
)
from app.resilience.seismic_sir_bridge import SeismicSIRBridge


@pytest.fixture
def network():
    """Create test social network."""
    G = nx.Graph()
    residents = [uuid4() for _ in range(10)]
    G.add_nodes_from(residents)

    # Add edges (social connections)
    for i in range(len(residents) - 1):
        G.add_edge(residents[i], residents[i + 1])

    return G


@pytest.fixture
def seismic_detector():
    """Create seismic detector."""
    return BurnoutEarlyWarning(short_window=5, long_window=30)


@pytest.fixture
def epi_model(network):
    """Create epidemiology model."""
    return BurnoutEpidemiology(social_network=network)


@pytest.fixture
def bridge(seismic_detector, epi_model):
    """Create seismic-SIR bridge."""
    return SeismicSIRBridge(
        seismic_detector=seismic_detector,
        epidemiology_model=epi_model,
        sensitivity=0.3,
        smoothing_factor=0.2,
        beta_base=0.05,
    )


class TestSeismicSIRBridge:
    """Test seismic-SIR bridge functionality."""

    def test_initialization(self, bridge):
        """Test bridge initialization."""
        assert bridge.sensitivity == 0.3
        assert bridge.smoothing_factor == 0.2
        assert bridge.beta_base == 0.05
        assert bridge.get_current_beta() == 0.05

    def test_no_adjustment_below_threshold(self, bridge):
        """Test that beta is not adjusted for low STA/LTA ratios."""
        # Create alert with ratio below threshold
        alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=2.0,  # Below 2.5 threshold
            trigger_time=datetime.now(),
            severity="low",
            predicted_magnitude=2.0,
            resident_id=uuid4(),
        )

        adjustment = bridge.update_from_alerts([alert])

        # Beta should remain at baseline
        assert adjustment.beta_adjusted == pytest.approx(0.05, rel=0.01)
        assert adjustment.adjustment_magnitude == pytest.approx(0.0, abs=1.0)

    def test_moderate_adjustment(self, bridge):
        """Test moderate beta adjustment for elevated STA/LTA."""
        alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=5.0,  # Moderate elevation
            trigger_time=datetime.now(),
            severity="medium",
            predicted_magnitude=4.0,
            resident_id=uuid4(),
        )

        adjustment = bridge.update_from_alerts([alert])

        # Beta should increase
        assert adjustment.beta_adjusted > 0.05
        assert adjustment.beta_adjusted < 0.10  # Not too high
        assert adjustment.adjustment_magnitude > 0

    def test_critical_adjustment(self, bridge):
        """Test large beta adjustment for critical STA/LTA."""
        alert = SeismicAlert(
            signal_type=PrecursorSignal.SICK_CALLS,
            sta_lta_ratio=15.0,  # Critical elevation
            trigger_time=datetime.now(),
            severity="critical",
            predicted_magnitude=8.0,
            resident_id=uuid4(),
        )

        adjustment = bridge.update_from_alerts([alert])

        # Beta should increase significantly
        assert adjustment.beta_adjusted > 0.10
        assert adjustment.adjustment_magnitude > 50  # >50% increase

    def test_multiple_alerts_aggregation(self, bridge, network):
        """Test aggregation of multiple simultaneous alerts."""
        residents = list(network.nodes())

        alerts = [
            SeismicAlert(
                signal_type=PrecursorSignal.SWAP_REQUESTS,
                sta_lta_ratio=5.0,
                trigger_time=datetime.now(),
                severity="medium",
                predicted_magnitude=4.0,
                resident_id=residents[0],
            ),
            SeismicAlert(
                signal_type=PrecursorSignal.SICK_CALLS,
                sta_lta_ratio=7.0,
                trigger_time=datetime.now(),
                severity="high",
                predicted_magnitude=5.0,
                resident_id=residents[1],
            ),
            SeismicAlert(
                signal_type=PrecursorSignal.RESPONSE_DELAYS,
                sta_lta_ratio=4.0,
                trigger_time=datetime.now(),
                severity="medium",
                predicted_magnitude=3.5,
                resident_id=residents[2],
            ),
        ]

        adjustment = bridge.update_from_alerts(alerts)

        # Beta should reflect combined signals
        assert adjustment.num_active_alerts == 3
        assert len(adjustment.affected_residents) == 3
        assert adjustment.beta_adjusted > 0.05

    def test_smoothing_reduces_volatility(self, bridge):
        """Test that smoothing prevents rapid beta changes."""
        # First alert
        alert1 = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=5.0,
            trigger_time=datetime.now(),
            severity="medium",
            predicted_magnitude=4.0,
            resident_id=uuid4(),
        )

        adj1 = bridge.update_from_alerts([alert1])
        beta_after_first = adj1.beta_adjusted

        # Second alert (higher)
        alert2 = SeismicAlert(
            signal_type=PrecursorSignal.SICK_CALLS,
            sta_lta_ratio=10.0,
            trigger_time=datetime.now(),
            severity="high",
            predicted_magnitude=6.0,
            resident_id=uuid4(),
        )

        adj2 = bridge.update_from_alerts([alert2])
        beta_after_second = adj2.beta_adjusted

        # Beta should increase but smoothed (not jump immediately to max)
        assert beta_after_second > beta_after_first
        # With smoothing_factor=0.2, change should be gradual
        beta_change = beta_after_second - beta_after_first
        assert beta_change < 0.05  # Not a huge jump

    def test_clamping_prevents_invalid_beta(self, bridge):
        """Test that beta is clamped to valid range [0.01, 0.95]."""
        # Create extreme alert
        alert = SeismicAlert(
            signal_type=PrecursorSignal.SICK_CALLS,
            sta_lta_ratio=100.0,  # Extremely high
            trigger_time=datetime.now(),
            severity="critical",
            predicted_magnitude=10.0,
            resident_id=uuid4(),
        )

        adjustment = bridge.update_from_alerts([alert])

        # Beta should be clamped to max (0.95)
        assert adjustment.beta_adjusted <= 0.95
        assert adjustment.beta_adjusted >= 0.01

    def test_old_alerts_pruned(self, bridge):
        """Test that old alerts are removed."""
        # Create old alert (8 days ago)
        old_alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=5.0,
            trigger_time=datetime.now() - timedelta(days=8),
            severity="medium",
            predicted_magnitude=4.0,
            resident_id=uuid4(),
        )

        # Add to active alerts manually
        bridge._active_alerts[old_alert.resident_id] = old_alert

        # Create new alert
        new_alert = SeismicAlert(
            signal_type=PrecursorSignal.SICK_CALLS,
            sta_lta_ratio=6.0,
            trigger_time=datetime.now(),
            severity="medium",
            predicted_magnitude=4.5,
            resident_id=uuid4(),
        )

        bridge.update_from_alerts([new_alert])

        # Old alert should be pruned (>7 days)
        assert old_alert.resident_id not in bridge._active_alerts
        assert new_alert.resident_id in bridge._active_alerts

    def test_transform_sta_lta_function(self, bridge):
        """Test f(r) transformation function."""
        # Below threshold
        assert bridge._transform_sta_lta(2.0) == 0.0
        assert bridge._transform_sta_lta(2.5) == 0.0

        # Moderate range (logarithmic)
        f_5 = bridge._transform_sta_lta(5.0)
        f_10 = bridge._transform_sta_lta(10.0)
        assert f_5 > 0
        assert f_10 > f_5
        assert f_10 == pytest.approx(2.0, rel=0.01)  # log2(10/2.5) = log2(4) = 2

        # Critical range (linear continuation)
        f_15 = bridge._transform_sta_lta(15.0)
        f_20 = bridge._transform_sta_lta(20.0)
        assert f_15 > f_10
        assert f_20 > f_15
        # Linear increment: 0.5 per unit above 10
        assert f_15 == pytest.approx(f_10 + 0.5 * 5, rel=0.01)

    def test_reset_beta(self, bridge):
        """Test beta reset functionality."""
        # Create alert to adjust beta
        alert = SeismicAlert(
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            sta_lta_ratio=8.0,
            trigger_time=datetime.now(),
            severity="high",
            predicted_magnitude=5.0,
            resident_id=uuid4(),
        )

        bridge.update_from_alerts([alert])
        assert bridge.get_current_beta() > 0.05

        # Reset
        bridge.reset_beta()
        assert bridge.get_current_beta() == 0.05
        assert len(bridge._active_alerts) == 0

    def test_adjustment_history_tracking(self, bridge):
        """Test that adjustment history is tracked."""
        # Create multiple alerts over time
        for i in range(5):
            alert = SeismicAlert(
                signal_type=PrecursorSignal.SWAP_REQUESTS,
                sta_lta_ratio=3.0 + i,
                trigger_time=datetime.now(),
                severity="medium",
                predicted_magnitude=3.0 + i,
                resident_id=uuid4(),
            )
            bridge.update_from_alerts([alert])

        # Check history
        history = bridge.get_adjustment_history()
        assert len(history) == 5

        # Most recent first
        assert history[0].timestamp > history[-1].timestamp

        # Limited history
        limited = bridge.get_adjustment_history(limit=3)
        assert len(limited) == 3
```

### 5.2 Integration Tests

```python
class TestSeismicSIRIntegration:
    """Integration tests for full seismic-SIR pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, network):
        """Test full pipeline: data → seismic → SIR."""
        # Setup
        seismic_detector = BurnoutEarlyWarning(short_window=5, long_window=30)
        epi_model = BurnoutEpidemiology(social_network=network)
        bridge = SeismicSIRBridge(
            seismic_detector=seismic_detector,
            epidemiology_model=epi_model,
            sensitivity=0.3,
        )

        # Create time series data showing increasing stress
        resident_id = list(network.nodes())[0]
        time_series = [0, 1, 0, 1, 0, 1, 2, 3, 5, 7, 8, 10, 12, 15] * 3  # 42 points

        # Detect precursors
        alerts = seismic_detector.detect_precursors(
            resident_id=resident_id,
            signal_type=PrecursorSignal.SWAP_REQUESTS,
            time_series=time_series,
        )

        assert len(alerts) > 0, "Should detect precursor signals"

        # Update bridge
        adjustment = bridge.update_from_alerts(alerts)

        # Verify beta increased
        assert adjustment.beta_adjusted > 0.05

        # Run SIR simulation with new beta
        initial_infected = {resident_id}
        epi_model.record_burnout_state(resident_id, BurnoutState.BURNED_OUT)

        time_series_results = epi_model.simulate_sir_spread(
            initial_infected=initial_infected,
            steps=20,
        )

        # Verify epidemic spreads faster with elevated beta
        assert len(time_series_results) > 0
        assert time_series_results[-1]["infected"] > 0 or time_series_results[-1]["recovered"] > 0
```

---

## 6. Integration Points

### 6.1 Celery Task for Periodic Updates

**File**: `backend/app/tasks/seismic_sir_update.py`

```python
"""Celery task for periodic seismic-SIR updates."""
from celery import shared_task
from app.services.seismic_sir_integration_service import SeismicSIRIntegrationService

@shared_task(name="seismic_sir.update_beta")
def update_beta_from_seismic_signals():
    """
    Periodic task to update SIR transmission rate from seismic precursors.

    Runs every N hours (configured in SEISMIC_SIR_UPDATE_INTERVAL_HOURS).
    """
    # Implementation would fetch latest behavioral data and update
    pass
```

### 6.2 API Endpoint

**File**: `backend/app/api/routes/resilience.py`

```python
@router.get("/seismic-sir/status")
async def get_seismic_sir_status(
    service: SeismicSIRIntegrationService = Depends(get_seismic_sir_service),
):
    """
    Get current seismic-SIR bridge status.

    Returns current beta, active alerts, and Rt.
    """
    report = await service.get_integrated_risk_report()
    return report
```

### 6.3 Dashboard Widget

**Frontend Component**: `frontend/components/resilience/SeismicSIRWidget.tsx`

```typescript
interface SeismicSIRStatus {
  seismicStatus: {
    activeAlerts: number;
    affectedResidents: number;
  };
  epidemicStatus: {
    currentBeta: number;
    betaAdjustmentPct: number;
    reproductionNumber: number;
    status: string;
  };
}

export function SeismicSIRWidget() {
  const { data } = useQuery<SeismicSIRStatus>({
    queryKey: ['resilience', 'seismic-sir'],
    queryFn: () => fetch('/api/resilience/seismic-sir/status').then(r => r.json()),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Seismic-SIR Integration</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <Metric
            label="Active Precursor Alerts"
            value={data?.seismicStatus.activeAlerts}
          />
          <Metric
            label="Current β"
            value={data?.epidemicStatus.currentBeta.toFixed(4)}
            delta={`${data?.epidemicStatus.betaAdjustmentPct:+.1f}%`}
          />
          <Metric
            label="Reproduction Number (Rt)"
            value={data?.epidemicStatus.reproductionNumber.toFixed(2)}
          />
          <Badge variant={getBadgeVariant(data?.epidemicStatus.status)}>
            {data?.epidemicStatus.status}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## 7. Implementation Estimate

### 7.1 Effort Breakdown

| Task | Estimated Hours | Complexity |
|------|-----------------|------------|
| **Core Bridge Implementation** | 3-4 hours | Medium |
| - `SeismicSIRBridge` class | 2 hours | Medium |
| - `BurnoutEpidemiology` updates | 0.5 hours | Low |
| - Integration service | 0.5-1 hour | Low |
| **Configuration** | 0.5 hours | Low |
| - Add to `config.py` | 0.25 hours | Low |
| - Update `.env.example` | 0.25 hours | Low |
| **Tests** | 2-3 hours | Medium |
| - Unit tests | 1.5 hours | Medium |
| - Integration tests | 1 hour | Medium |
| - Test fixtures | 0.5 hours | Low |
| **API Integration** | 1 hour | Low |
| - Celery task | 0.5 hours | Low |
| - API endpoint | 0.5 hours | Low |
| **Documentation** | 0.5 hours | Low |
| - Docstrings | 0.25 hours | Low |
| - Update architecture docs | 0.25 hours | Low |

**Total**: 6-8 hours

### 7.2 Files Modified

| File | Type | Lines Added |
|------|------|-------------|
| `backend/app/resilience/seismic_sir_bridge.py` | New | ~250 |
| `backend/app/resilience/burnout_epidemiology.py` | Modified | ~20 |
| `backend/app/services/seismic_sir_integration_service.py` | New | ~100 |
| `backend/app/core/config.py` | Modified | ~15 |
| `backend/tests/resilience/test_seismic_sir_bridge.py` | New | ~300 |
| `.env.example` | Modified | ~5 |

**Total**: ~690 lines of code

### 7.3 Dependencies

No new dependencies required. Uses existing:
- `numpy` (already installed)
- `networkx` (already installed)

---

## 8. References

### 8.1 Seismology

- Withers, M., et al. (1998). "A comparison of select trigger algorithms for automated global seismic phase and event detection." *Bulletin of the Seismological Society of America*, 88(1), 95-106.
- Allen, R. V. (1978). "Automatic earthquake recognition and timing from single traces." *Bulletin of the Seismological Society of America*, 68(5), 1521-1532.

### 8.2 Epidemiology

- Kermack, W. O., & McKendrick, A. G. (1927). "A contribution to the mathematical theory of epidemics." *Proceedings of the Royal Society A*, 115(772), 700-721.
- Anderson, R. M., & May, R. M. (1991). *Infectious Diseases of Humans: Dynamics and Control*. Oxford University Press.

### 8.3 Burnout Contagion

- Bakker, A. B., et al. (2009). "Burnout contagion among intensive care nurses." *Journal of Advanced Nursing*, 51(3), 276-287.
- Christakis, N. A., & Fowler, J. H. (2008). "Dynamic spread of happiness in a large social network." *BMJ*, 337, a2338.

### 8.4 Related Documentation

- **Seismic Detection**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/seismic_detection.py`
- **Burnout Epidemiology**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/burnout_epidemiology.py`
- **Cross-Disciplinary Resilience**: `/home/user/Autonomous-Assignment-Program-Manager/docs/architecture/cross-disciplinary-resilience.md`

---

## Appendix: Example Usage

```python
import networkx as nx
from uuid import uuid4

from app.resilience.seismic_detection import BurnoutEarlyWarning, PrecursorSignal
from app.resilience.burnout_epidemiology import BurnoutEpidemiology
from app.resilience.seismic_sir_bridge import SeismicSIRBridge

# Setup
network = nx.karate_club_graph()  # Example social network
seismic_detector = BurnoutEarlyWarning(short_window=5, long_window=30)
epi_model = BurnoutEpidemiology(social_network=network)

bridge = SeismicSIRBridge(
    seismic_detector=seismic_detector,
    epidemiology_model=epi_model,
    sensitivity=0.3,
    smoothing_factor=0.2,
    beta_base=0.05,
)

# Collect behavioral data
resident_id = list(network.nodes())[0]
swap_request_data = [0, 1, 0, 1, 2, 3, 5, 7, 8, 10, 12, 15, 18, 20, 22, 25]

# Detect precursors
alerts = seismic_detector.detect_precursors(
    resident_id=resident_id,
    signal_type=PrecursorSignal.SWAP_REQUESTS,
    time_series=swap_request_data,
)

print(f"Detected {len(alerts)} seismic alerts")

# Update SIR model
adjustment = bridge.update_from_alerts(alerts)

print(f"Beta adjusted: {adjustment.beta_base:.4f} → {adjustment.beta_adjusted:.4f}")
print(f"Adjustment magnitude: {adjustment.adjustment_magnitude:+.1f}%")

# Run epidemic simulation with updated beta
initial_infected = {resident_id}
time_series = epi_model.simulate_sir_spread(initial_infected=initial_infected)

print(f"Simulated {len(time_series)} time steps")
print(f"Final state: I={time_series[-1]['infected']}, R={time_series[-1]['recovered']}")
```

---

**Document Version**: 1.0
**Author**: Autonomous Assignment Program Manager Development Team
**Review Status**: Ready for Implementation
