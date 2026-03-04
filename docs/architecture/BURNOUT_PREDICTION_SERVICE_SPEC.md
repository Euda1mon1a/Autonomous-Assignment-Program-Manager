# Burnout Prediction Service Specification

**Document Version:** 1.0
**Date:** 2025-12-26
**Status:** Implementation Ready
**Target:** Production-ready burnout prediction engine using materials science fatigue models

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Service Architecture](#service-architecture)
3. [API Endpoints](#api-endpoints)
4. [Prediction Models](#prediction-models)
5. [Database Schema](#database-schema)
6. [Ensemble Logic](#ensemble-logic)
7. [Integration Points](#integration-points)
8. [Implementation Plan](#implementation-plan)
9. [Testing Strategy](#testing-strategy)
10. [Performance Requirements](#performance-requirements)

---

## 1. Executive Summary

### 1.1 Purpose

This specification defines a production-ready burnout prediction service that applies materials science fatigue and creep models to predict personnel burnout risk 4-12 weeks before clinical manifestation.

### 1.2 Key Innovation

**Objective, data-driven prediction** based on workload history and symptom progression, analogous to how aerospace engineers predict structural failure in aircraft components.

### 1.3 Success Metrics

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| **Sensitivity** | ≥80% at 12-week horizon | ≥70% |
| **Specificity** | ≥85% | ≥75% |
| **MAE (Mean Absolute Error)** | ≤14 days (2 weeks) | ≤21 days |
| **Positive Predictive Value** | ≥70% | ≥60% |
| **Early Warning Window** | 4-12 weeks before burnout | ≥4 weeks |

### 1.4 Core Models

1. **S-N Curve**: Workload intensity → cycles to burnout
2. **Miner's Rule**: Cumulative damage from variable workload
3. **Coffin-Manson**: Recoverable vs. unrecoverable fatigue
4. **Larson-Miller**: Sustained workload creep rupture
5. **Paris Law**: Symptom severity progression (crack growth)

---

## 2. Service Architecture

### 2.1 Module Structure

```
backend/app/analytics/burnout_prediction/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── sn_curve.py              # S-N curve model
│   ├── miners_rule.py           # Cumulative damage calculator
│   ├── coffin_manson.py         # Low-cycle fatigue model
│   ├── larson_miller.py         # Creep rupture predictor
│   └── paris_law.py             # Crack growth tracker
├── ensemble.py                   # Multi-model ensemble predictor
├── calibration.py               # Parameter calibration from data
├── service.py                   # Main service class
└── persistence.py               # Database operations

backend/app/schemas/burnout_prediction.py  # Pydantic schemas
backend/app/models/burnout.py             # SQLAlchemy models
backend/app/api/routes/burnout.py         # API endpoints
```

### 2.2 Service Class Design

```python
"""Main burnout prediction service."""
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.analytics.burnout_prediction.ensemble import EnsembleBurnoutPredictor
from app.analytics.burnout_prediction.calibration import ModelCalibrator
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BurnoutPredictionConfig:
    """Configuration for burnout prediction service."""

    # Model parameters
    sn_sigma_f_prime: float = 100.0      # S-N curve fatigue strength coefficient
    sn_b: float = -0.12                  # S-N curve exponent
    sn_endurance_limit: float = 50.0     # Stress below which infinite cycles tolerated

    # Miner's Rule
    miner_critical_damage: float = 1.0   # Failure threshold
    miner_warning_threshold: float = 0.7 # Early warning at 70%

    # Larson-Miller
    lm_C: float = 20.0                   # Material constant
    lm_reference_LMP: float = 30000      # Reference parameter value

    # Paris Law
    paris_C: float = 1e-5                # Crack growth coefficient
    paris_m: float = 3.0                 # Crack growth exponent
    paris_critical_severity: float = 27.0 # MBI-EE burnout threshold

    # Ensemble weights (must sum to 1.0)
    weight_sn_curve: float = 0.20
    weight_miner: float = 0.35           # Highest weight - most practical
    weight_larson_miller: float = 0.25
    weight_paris_law: float = 0.20

    # Calibration settings
    enable_adaptive_calibration: bool = True
    calibration_learning_rate: float = 0.1
    min_calibration_samples: int = 20

    # Alert thresholds (days to burnout)
    critical_threshold: int = 30         # < 30 days = CRITICAL
    high_threshold: int = 90             # < 90 days = HIGH
    moderate_threshold: int = 180        # < 180 days = MODERATE


class BurnoutPredictionService:
    """
    Burnout prediction service using materials science fatigue models.

    Provides:
    - Multi-model ensemble predictions
    - Personal calibration
    - Risk scoring and classification
    - Intervention recommendations

    Usage:
        service = BurnoutPredictionService(db)
        prediction = await service.predict_burnout(
            person_id=faculty_id,
            current_date=date.today()
        )

        if prediction.risk_level == "CRITICAL":
            await service.trigger_intervention(prediction)
    """

    def __init__(
        self,
        db: Session,
        config: BurnoutPredictionConfig | None = None,
    ):
        self.db = db
        self.config = config or BurnoutPredictionConfig()

        # Initialize ensemble predictor
        self.ensemble = EnsembleBurnoutPredictor(config=self.config)

        # Initialize calibrator
        self.calibrator = ModelCalibrator(db=db, config=self.config)

        # Load calibrated parameters if available
        self._load_calibrated_parameters()

    async def predict_burnout(
        self,
        person_id: UUID,
        current_date: date | None = None,
    ) -> BurnoutPrediction:
        """
        Generate comprehensive burnout prediction for a person.

        Args:
            person_id: Person to predict for
            current_date: Prediction date (defaults to today)

        Returns:
            BurnoutPrediction with ensemble forecast and recommendations
        """
        # Implementation details below...

    async def calculate_fatigue_score(
        self,
        person_id: UUID,
        period_days: int = 90,
    ) -> FatigueScore:
        """Calculate cumulative fatigue score (Miner's damage)."""
        # Implementation details below...

    async def calibrate_personal_model(
        self,
        person_id: UUID,
        observed_burnout_date: date,
        workload_at_burnout: float,
    ):
        """Calibrate model parameters from observed burnout event."""
        # Implementation details below...
```

### 2.3 Ensemble Predictor

```python
"""Multi-model ensemble burnout predictor."""
from dataclasses import dataclass
from typing import List

from app.analytics.burnout_prediction.models.sn_curve import SNCurveModel
from app.analytics.burnout_prediction.models.miners_rule import MinerDamageCalculator
from app.analytics.burnout_prediction.models.coffin_manson import CoffinMansonModel
from app.analytics.burnout_prediction.models.larson_miller import LarsonMillerModel
from app.analytics.burnout_prediction.models.paris_law import ParisLawModel


@dataclass
class BurnoutPrediction:
    """Unified burnout prediction from all models."""

    person_id: UUID
    prediction_date: date

    # Model-specific predictions (days to burnout)
    sn_curve_prediction: float | None
    miner_damage: float
    miner_cycles_remaining: float | None
    coffin_manson_regime: str              # LOW_CYCLE_FATIGUE, HIGH_CYCLE_FATIGUE, TRANSITION
    larson_miller_days: float | None
    paris_law_weeks: float | None

    # Unified prediction (weighted ensemble)
    ensemble_prediction_days: float
    confidence_interval_lower: float       # 95% CI lower bound
    confidence_interval_upper: float       # 95% CI upper bound

    # Risk classification
    risk_level: str                        # LOW, MODERATE, HIGH, CRITICAL
    primary_failure_mode: str              # Dominant mechanism

    # Recommendations
    interventions: List[str]
    workload_adjustment_recommended: float # Percentage reduction suggested

    # Metadata
    models_used: int                       # How many models contributed
    prediction_quality: str                # EXCELLENT, GOOD, FAIR, POOR


class EnsembleBurnoutPredictor:
    """Combine all materials science models for robust prediction."""

    def __init__(self, config: BurnoutPredictionConfig):
        self.config = config

        # Initialize all models
        self.sn_model = SNCurveModel(config)
        self.cm_model = CoffinMansonModel(config)
        self.lm_model = LarsonMillerModel(config)
        self.paris_model = ParisLawModel(config)

    def predict(
        self,
        person_id: UUID,
        workload_history: List[WorkloadRecord],
        symptom_history: List[SymptomRecord],
        current_stress: float,
    ) -> BurnoutPrediction:
        """Generate ensemble prediction from all models."""
        # Implementation combines all 5 models with weighted averaging
        # Details in section 6.1
```

---

## 3. API Endpoints

### 3.1 Prediction Endpoints

#### POST /api/v1/burnout/predict

**Description**: Predict burnout risk for a person

**Request Body**:
```json
{
  "person_id": "uuid",
  "prediction_date": "2025-12-26",  // Optional, defaults to today
  "include_recommendations": true
}
```

**Response** (200 OK):
```json
{
  "person_id": "uuid",
  "prediction_date": "2025-12-26",
  "ensemble_prediction_days": 45.3,
  "confidence_interval": {
    "lower": 31.7,
    "upper": 58.9
  },
  "risk_level": "HIGH",
  "primary_failure_mode": "CUMULATIVE_DAMAGE",
  "model_predictions": {
    "sn_curve_days": 52.0,
    "miner_damage": 0.82,
    "miner_cycles_remaining": 9.0,
    "coffin_manson_regime": "LOW_CYCLE_FATIGUE",
    "larson_miller_days": 61.0,
    "paris_law_weeks": 6.0
  },
  "interventions": [
    "URGENT: Reduce workload 50% for 4 weeks minimum",
    "Weekly therapy sessions (CBT/supportive)",
    "Limit high-intensity cycles (weekend call, night shifts)"
  ],
  "workload_adjustment_recommended": -0.50,
  "prediction_quality": "GOOD",
  "models_used": 5
}
```

**Error Responses**:
- `400 Bad Request`: Invalid person_id or date
- `404 Not Found`: Person not found
- `422 Unprocessable Entity`: Insufficient data for prediction

---

#### GET /api/v1/burnout/resident/{person_id}/fatigue

**Description**: Get cumulative fatigue score (Miner's damage)

**Query Parameters**:
- `period_days` (int, default=90): Historical period to analyze

**Response** (200 OK):
```json
{
  "person_id": "uuid",
  "calculated_at": "2025-12-26T10:30:00Z",
  "period_days": 90,
  "cumulative_damage": 0.82,
  "remaining_life_fraction": 0.18,
  "status": "HIGH_DAMAGE",
  "severity": "WARNING",
  "recommendation": "Urgent: Reduce workload intensity and frequency",
  "damage_breakdown": [
    {
      "cycle_type": "weekend_call",
      "stress_amplitude": 85.0,
      "cycles_completed": 8,
      "damage_fraction": 0.154,
      "cumulative_damage": 0.82
    }
  ],
  "cycles_to_critical": 2.3,
  "warning_threshold_exceeded": true
}
```

---

#### POST /api/v1/burnout/calibrate

**Description**: Calibrate personal model from observed burnout event

**Request Body**:
```json
{
  "person_id": "uuid",
  "burnout_date": "2025-11-15",
  "average_workload_percent": 78.0,
  "sustained_stress_level": 80.0,
  "cycles_to_burnout": 24,
  "burnout_type": "medical_leave"  // or "resignation", "mbi_high"
}
```

**Response** (200 OK):
```json
{
  "person_id": "uuid",
  "calibration_successful": true,
  "personal_parameters": {
    "sigma_f_prime": 95.3,
    "larson_miller_parameter": 28500,
    "resilience_classification": "Low"  // High, Average, Low
  },
  "prediction_improvement": {
    "mae_before": 21.3,
    "mae_after": 12.7,
    "improvement_percent": 40.4
  }
}
```

---

#### GET /api/v1/burnout/dashboard

**Description**: Risk overview for all residents/faculty

**Query Parameters**:
- `role` (string, optional): Filter by role (resident, faculty)
- `risk_level` (string, optional): Filter by risk level
- `pgy_level` (int, optional): Filter residents by PGY level

**Response** (200 OK):
```json
{
  "generated_at": "2025-12-26T10:30:00Z",
  "total_people": 45,
  "risk_distribution": {
    "CRITICAL": 2,
    "HIGH": 7,
    "MODERATE": 15,
    "LOW": 21
  },
  "predictions": [
    {
      "person_id": "uuid",
      "person_name": "RES_001",  // Sanitized for PERSEC
      "role": "resident",
      "pgy_level": 2,
      "risk_level": "CRITICAL",
      "days_to_burnout": 28.5,
      "miner_damage": 0.95,
      "primary_failure_mode": "CRACK_PROPAGATION",
      "urgent_intervention_needed": true
    }
  ],
  "summary_statistics": {
    "average_miner_damage": 0.52,
    "median_days_to_burnout": 145.0,
    "people_above_warning_threshold": 9
  }
}
```

---

### 3.2 Symptom Tracking Endpoints

#### POST /api/v1/burnout/symptoms

**Description**: Record symptom assessment

**Request Body**:
```json
{
  "person_id": "uuid",
  "assessment_date": "2025-12-26",
  "mbi_emotional_exhaustion": 18,  // 0-54 scale
  "phq9_score": 8,                  // 0-27 scale (depression)
  "gad7_score": 6,                  // 0-21 scale (anxiety)
  "single_item_burnout": 3          // 1-5 scale
}
```

**Response** (201 Created):
```json
{
  "symptom_id": "uuid",
  "person_id": "uuid",
  "assessment_date": "2025-12-26",
  "crack_length": 18.0,             // Current severity for Paris Law
  "stress_intensity_delta_K": 23.8,
  "growth_rate_per_week": 0.45,
  "weeks_to_critical": 20,
  "risk_level": "MODERATE"
}
```

---

### 3.3 Workload Recording Endpoints

#### POST /api/v1/burnout/workload

**Description**: Record workload intensity

**Request Body**:
```json
{
  "person_id": "uuid",
  "date": "2025-12-26",
  "cycle_type": "weekend_call",     // Categorized work type
  "duration_hours": 28,
  "intensity_percent": 85,          // % of capacity
  "unrecoverable_fatigue": 0.3      // For Coffin-Manson (0-1)
}
```

**Response** (201 Created):
```json
{
  "workload_id": "uuid",
  "person_id": "uuid",
  "date": "2025-12-26",
  "damage_increment": 0.019,        // Contribution to Miner damage
  "cumulative_damage": 0.82,
  "cycles_to_failure": 52.3         // S-N curve prediction at this intensity
}
```

---

## 4. Prediction Models

### 4.1 S-N Curve Model

**File**: `backend/app/analytics/burnout_prediction/models/sn_curve.py`

**Purpose**: Relate workload intensity to cycles until burnout

**Equation**:
```
N = (σ / σ_f')^(1/b)

Where:
- N = cycles to burnout
- σ = stress amplitude (% capacity)
- σ_f' = fatigue strength coefficient (material constant, ~100)
- b = fatigue strength exponent (-0.08 to -0.15, typically -0.12)
```

**Implementation**:
```python
"""S-N Curve model for burnout prediction."""
import numpy as np
from dataclasses import dataclass


@dataclass
class SNCurveParameters:
    """S-N curve parameters."""
    sigma_f_prime: float = 100.0
    b: float = -0.12
    endurance_limit: float = 50.0
    transition_life: float = 10000


class SNCurveModel:
    """S-N curve model for predicting cycles to burnout."""

    def __init__(self, config: BurnoutPredictionConfig):
        self.params = SNCurveParameters(
            sigma_f_prime=config.sn_sigma_f_prime,
            b=config.sn_b,
            endurance_limit=config.sn_endurance_limit,
        )

    def cycles_to_failure(self, stress_amplitude: float) -> float:
        """
        Calculate cycles to failure for given stress amplitude.

        Args:
            stress_amplitude: Workload intensity (0-100% capacity)

        Returns:
            Number of cycles to burnout (failure)
        """
        if stress_amplitude <= self.params.endurance_limit:
            return 1e6  # Essentially infinite

        N = (stress_amplitude / self.params.sigma_f_prime) ** (1 / self.params.b)
        return N

    def stress_for_target_life(self, target_cycles: float) -> float:
        """Calculate allowable stress for target fatigue life."""
        sigma = self.params.sigma_f_prime * (target_cycles ** self.params.b)
        return max(sigma, self.params.endurance_limit)
```

**Usage**:
```python
model = SNCurveModel(config)

# Predict cycles to burnout for weekend call (85% intensity)
cycles = model.cycles_to_failure(85)  # ~52 cycles
days = cycles * 7  # Convert to days (assuming weekly cycles)

# Find safe workload for 3-year residency
safe_stress = model.stress_for_target_life(156)  # 3 years = 156 weeks
```

---

### 4.2 Miner's Rule Model

**File**: `backend/app/analytics/burnout_prediction/models/miners_rule.py`

**Purpose**: Calculate cumulative damage from variable workload

**Equation**:
```
D = Σ(n_i / N_i)

Where:
- D = cumulative damage (failure when D ≥ 1.0)
- n_i = actual cycles at stress level i
- N_i = cycles to failure at stress level i (from S-N curve)
```

**Implementation**:
```python
"""Miner's Rule for cumulative damage calculation."""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class LoadingCycle:
    """Represent a loading cycle."""
    cycle_type: str
    stress_amplitude: float
    cycle_count: int


@dataclass
class MinerDamageCalculator:
    """Calculate cumulative fatigue damage using Miner's Rule."""

    sn_model: SNCurveModel
    damage_sum: float = 0.0
    damage_history: List[Dict] = field(default_factory=list)

    critical_damage: float = 1.0
    warning_threshold: float = 0.7

    def add_loading_cycles(self, cycles: LoadingCycle) -> float:
        """Add loading cycles and update cumulative damage."""
        N_i = self.sn_model.cycles_to_failure(cycles.stress_amplitude)
        damage_increment = cycles.cycle_count / N_i

        self.damage_sum += damage_increment

        self.damage_history.append({
            'cycle_type': cycles.cycle_type,
            'stress_amplitude': cycles.stress_amplitude,
            'cycles_completed': cycles.cycle_count,
            'cycles_to_failure': N_i,
            'damage_fraction': damage_increment,
            'cumulative_damage': self.damage_sum
        })

        return damage_increment

    def predict_failure_in_cycles(
        self,
        future_stress: float,
    ) -> float:
        """Predict how many more cycles until burnout."""
        remaining_damage = self.critical_damage - self.damage_sum

        if remaining_damage <= 0:
            return 0

        N_future = self.sn_model.cycles_to_failure(future_stress)
        damage_per_cycle = 1.0 / N_future
        cycles_remaining = remaining_damage / damage_per_cycle

        return cycles_remaining

    def get_damage_status(self) -> Dict:
        """Get comprehensive damage status."""
        remaining_life = max(0.0, 1.0 - self.damage_sum)

        if self.damage_sum >= self.critical_damage:
            status = "BURNOUT_PREDICTED"
            severity = "CRITICAL"
        elif self.damage_sum >= self.warning_threshold:
            status = "HIGH_DAMAGE"
            severity = "WARNING"
        elif self.damage_sum >= 0.5:
            status = "MODERATE_DAMAGE"
            severity = "CAUTION"
        else:
            status = "LOW_DAMAGE"
            severity = "NORMAL"

        return {
            'cumulative_damage': round(self.damage_sum, 3),
            'remaining_life_fraction': round(remaining_life, 3),
            'status': status,
            'severity': severity,
        }
```

---

### 4.3 Coffin-Manson Model

**File**: `backend/app/analytics/burnout_prediction/models/coffin_manson.py`

**Purpose**: Distinguish recoverable vs. unrecoverable fatigue

**Equation**:
```
Δε_total / 2 = (σ_f' / E) * (2N_f)^b + ε_f' * (2N_f)^c
                ↑ elastic (recoverable)    ↑ plastic (unrecoverable)
```

**Key Insight**:
- **High-intensity rotations** (>80% capacity) → plastic deformation → permanent damage
- **Moderate rotations** (50-70% capacity) → elastic deformation → recoverable with rest

**Implementation**:
```python
"""Coffin-Manson low-cycle fatigue model."""
from dataclasses import dataclass


@dataclass
class CoffinMansonParameters:
    """Coffin-Manson model parameters."""
    sigma_f_prime: float = 100.0
    b: float = -0.12
    E: float = 100.0
    epsilon_f_prime: float = 1.0
    c: float = -0.6


class CoffinMansonModel:
    """Low-cycle fatigue model for high-intensity workload."""

    def __init__(self, config: BurnoutPredictionConfig):
        self.params = CoffinMansonParameters()

    def elastic_strain(self, cycles: float) -> float:
        """Calculate elastic strain component (recoverable)."""
        return (self.params.sigma_f_prime / self.params.E) * (cycles ** self.params.b)

    def plastic_strain(self, cycles: float) -> float:
        """Calculate plastic strain component (unrecoverable)."""
        return self.params.epsilon_f_prime * (cycles ** self.params.c)

    def total_strain(self, cycles: float) -> float:
        """Calculate total strain."""
        return self.elastic_strain(cycles) + self.plastic_strain(cycles)

    def classify_fatigue_regime(self, cycles: float) -> str:
        """Classify fatigue regime based on dominant strain."""
        elastic = self.elastic_strain(cycles)
        plastic = self.plastic_strain(cycles)

        ratio = plastic / elastic if elastic > 0 else float('inf')

        if ratio > 2:
            return "LOW_CYCLE_FATIGUE"  # Plastic dominates
        elif ratio < 0.5:
            return "HIGH_CYCLE_FATIGUE"  # Elastic dominates
        else:
            return "TRANSITION"

    def unrecoverable_damage_fraction(self, total_strain: float, cycles: float) -> float:
        """Calculate fraction of damage that is unrecoverable."""
        plastic = self.plastic_strain(cycles)
        return plastic / total_strain if total_strain > 0 else 0
```

**Clinical Decision**:
- If plastic strain > 20% per rotation → limit consecutive high-intensity rotations
- If plastic strain < 5% per rotation → sustainable long-term

---

### 4.4 Larson-Miller Model

**File**: `backend/app/analytics/burnout_prediction/models/larson_miller.py`

**Purpose**: Predict burnout under sustained moderate workload

**Equation**:
```
LMP = T(C + log t_r)

Where:
- T = "temperature" (chronic stress level, %)
- t_r = time to rupture (days)
- C = material constant (typically 20)
- LMP = Larson-Miller Parameter (person-specific)
```

**Use Case**: Detect creep failure from sustained 70+ hour weeks (not violating 80-hour rule acutely, but unsustainable over months)

**Implementation**:
```python
"""Larson-Miller parameter for creep rupture prediction."""
from dataclasses import dataclass
import numpy as np


@dataclass
class LarsonMillerParameters:
    """Larson-Miller model parameters."""
    C: float = 20.0
    LMP_reference: float = 30000
    stress_reference: float = 70.0


class LarsonMillerModel:
    """Creep rupture model for sustained workload."""

    def __init__(self, config: BurnoutPredictionConfig):
        self.params = LarsonMillerParameters(
            C=config.lm_C,
            LMP_reference=config.lm_reference_LMP,
        )

    def calculate_LMP(self, temperature: float, time_to_rupture: float) -> float:
        """Calculate Larson-Miller Parameter."""
        time_hours = time_to_rupture * 24
        LMP = temperature * (self.params.C + np.log10(time_hours))
        return LMP

    def predict_time_to_rupture(
        self,
        chronic_stress_level: float,
        LMP: float = None,
    ) -> float:
        """Predict time to burnout for given chronic stress."""
        if LMP is None:
            LMP = self.params.LMP_reference

        log_t_r = (LMP / chronic_stress_level) - self.params.C
        t_r_hours = 10 ** log_t_r
        t_r_days = t_r_hours / 24

        return t_r_days

    def predict_safe_stress_level(
        self,
        target_duration_days: float,
        LMP: float = None,
    ) -> float:
        """Predict safe chronic stress level for target duration."""
        if LMP is None:
            LMP = self.params.LMP_reference

        t_r_hours = target_duration_days * 24
        T = LMP / (self.params.C + np.log10(t_r_hours))

        return T

    def calibrate_personal_LMP(
        self,
        observed_stress: float,
        observed_time_to_burnout: float,
    ) -> float:
        """Calibrate person-specific LMP from observed burnout."""
        return self.calculate_LMP(observed_stress, observed_time_to_burnout)
```

---

### 4.5 Paris Law Model

**File**: `backend/app/analytics/burnout_prediction/models/paris_law.py`

**Purpose**: Track burnout symptom progression (crack growth)

**Equation**:
```
da/dN = C(ΔK)^m

Where:
- da/dN = crack growth rate (severity increase per cycle/week)
- ΔK = stress intensity factor = Δσ * sqrt(π * a)
- C = crack growth coefficient
- m = crack growth exponent (2-4)
- a = crack length (current symptom severity)
```

**Implementation**:
```python
"""Paris Law for burnout symptom progression."""
from dataclasses import dataclass, field
from typing import List, Tuple
import numpy as np


@dataclass
class ParisLawParameters:
    """Paris Law parameters."""
    C: float = 1e-5
    m: float = 3.0
    delta_K_th: float = 5.0
    K_IC: float = 50.0
    a_critical: float = 27.0  # MBI-EE ≥ 27 = high burnout


@dataclass
class BurnoutCrack:
    """Represent a burnout 'crack' (symptom severity)."""
    person_id: UUID
    crack_type: str
    current_severity: float
    current_date: date
    severity_history: List[Tuple[date, float]] = field(default_factory=list)
    stress_range: float = 20.0


class ParisLawModel:
    """Paris Law model for burnout symptom progression."""

    def __init__(self, config: BurnoutPredictionConfig):
        self.params = ParisLawParameters(
            C=config.paris_C,
            m=config.paris_m,
            a_critical=config.paris_critical_severity,
        )

    def stress_intensity_range(self, crack_length: float, stress_range: float) -> float:
        """Calculate stress intensity factor range ΔK."""
        Y = 1.0  # Geometry factor (simplified)
        delta_K = stress_range * Y * np.sqrt(np.pi * crack_length)
        return delta_K

    def crack_growth_rate(self, crack_length: float, stress_range: float) -> float:
        """Calculate crack growth rate da/dN using Paris Law."""
        delta_K = self.stress_intensity_range(crack_length, stress_range)

        # Region I: Below threshold, no growth
        if delta_K < self.params.delta_K_th:
            return 0.0

        # Region III: Approaching critical, rapid growth
        if delta_K > 0.8 * self.params.K_IC:
            acceleration = np.exp((delta_K - 0.8 * self.params.K_IC) / 5.0)
            return self.params.C * (delta_K ** self.params.m) * acceleration

        # Region II: Paris Law (stable growth)
        da_dN = self.params.C * (delta_K ** self.params.m)
        return da_dN

    def predict_cycles_to_critical(
        self,
        initial_crack: float,
        stress_range: float,
    ) -> Tuple[int, List[float]]:
        """Predict cycles until crack reaches critical size."""
        a = initial_crack
        cycles = 0
        progression = [a]

        max_cycles = 1000

        while a < self.params.a_critical and cycles < max_cycles:
            da_dN = self.crack_growth_rate(a, stress_range)
            a += da_dN
            cycles += 1
            progression.append(a)

            delta_K = self.stress_intensity_range(a, stress_range)
            if delta_K >= self.params.K_IC:
                break

        return cycles, progression
```

**Clinical Intervention**:
| Region | Severity | Growth Rate | Intervention |
|--------|----------|-------------|--------------|
| I | < 10 | Slow | Routine monitoring, wellness maintenance |
| II | 10-22 | Predictable | Workload adjustment, weekly monitoring, counseling |
| III | > 22 | Rapid | Immediate 50% workload reduction, daily monitoring, psych eval |

---

## 5. Database Schema

### 5.1 Core Tables

#### `burnout_predictions`

```sql
CREATE TABLE burnout_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES people(id),
    prediction_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Model predictions (days to burnout)
    sn_curve_prediction FLOAT,
    miner_damage FLOAT NOT NULL,
    miner_cycles_remaining FLOAT,
    coffin_manson_regime VARCHAR(30),
    larson_miller_days FLOAT,
    paris_law_weeks FLOAT,

    -- Ensemble results
    ensemble_prediction_days FLOAT NOT NULL,
    confidence_interval_lower FLOAT NOT NULL,
    confidence_interval_upper FLOAT NOT NULL,

    -- Risk classification
    risk_level VARCHAR(20) NOT NULL,  -- LOW, MODERATE, HIGH, CRITICAL
    primary_failure_mode VARCHAR(50) NOT NULL,

    -- Recommendations
    interventions TEXT[],
    workload_adjustment_recommended FLOAT,

    -- Metadata
    models_used INTEGER NOT NULL,
    prediction_quality VARCHAR(20) NOT NULL,

    CONSTRAINT check_risk_level CHECK (risk_level IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')),
    CONSTRAINT check_miner_damage CHECK (miner_damage >= 0.0 AND miner_damage <= 2.0),
    INDEX idx_person_date (person_id, prediction_date DESC),
    INDEX idx_risk_level (risk_level),
    INDEX idx_prediction_date (prediction_date DESC)
);
```

---

#### `workload_history`

```sql
CREATE TABLE workload_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES people(id),
    date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Workload details
    cycle_type VARCHAR(100) NOT NULL,  -- weekend_call, night_shift, clinic, etc.
    duration_hours FLOAT NOT NULL,
    intensity_percent FLOAT NOT NULL CHECK (intensity_percent >= 0 AND intensity_percent <= 100),
    unrecoverable_fatigue FLOAT CHECK (unrecoverable_fatigue >= 0 AND unrecoverable_fatigue <= 1),

    -- Calculated metrics
    damage_increment FLOAT,
    cumulative_damage FLOAT,
    cycles_to_failure FLOAT,

    -- Context
    notes TEXT,

    UNIQUE (person_id, date, cycle_type),
    INDEX idx_person_date (person_id, date DESC),
    INDEX idx_cycle_type (cycle_type)
);
```

---

#### `symptom_records`

```sql
CREATE TABLE symptom_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES people(id),
    assessment_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Symptom assessments
    mbi_emotional_exhaustion INTEGER CHECK (mbi_emotional_exhaustion >= 0 AND mbi_emotional_exhaustion <= 54),
    mbi_depersonalization INTEGER CHECK (mbi_depersonalization >= 0 AND mbi_depersonalization <= 30),
    mbi_personal_accomplishment INTEGER CHECK (mbi_personal_accomplishment >= 0 AND mbi_personal_accomplishment <= 48),
    phq9_score INTEGER CHECK (phq9_score >= 0 AND phq9_score <= 27),
    gad7_score INTEGER CHECK (gad7_score >= 0 AND gad7_score <= 21),
    single_item_burnout INTEGER CHECK (single_item_burnout >= 1 AND single_item_burnout <= 5),

    -- Paris Law calculations
    crack_length FLOAT,  -- Current severity for Paris Law
    stress_intensity_delta_K FLOAT,
    growth_rate_per_week FLOAT,
    weeks_to_critical INTEGER,
    crack_risk_level VARCHAR(20),

    -- Context
    notes TEXT,
    administered_by VARCHAR(255),

    UNIQUE (person_id, assessment_date),
    INDEX idx_person_date (person_id, assessment_date DESC),
    INDEX idx_mbi_ee (mbi_emotional_exhaustion),
    CONSTRAINT check_crack_risk CHECK (crack_risk_level IN ('LOW', 'MODERATE', 'HIGH', 'IMMINENT_FAILURE', 'CRITICAL_BURNOUT'))
);
```

---

#### `burnout_events`

```sql
CREATE TABLE burnout_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES people(id),
    burnout_date DATE NOT NULL,
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Event classification
    event_type VARCHAR(50) NOT NULL,  -- medical_leave, resignation, mbi_high, etc.
    severity VARCHAR(20) NOT NULL,

    -- Workload at burnout
    average_workload_percent FLOAT,
    sustained_stress_level FLOAT,
    cycles_to_burnout INTEGER,
    days_to_burnout INTEGER,

    -- Prediction accuracy (if predicted)
    was_predicted BOOLEAN DEFAULT FALSE,
    predicted_date DATE,
    prediction_error_days INTEGER,

    -- Outcome
    return_to_work_date DATE,
    intervention_provided TEXT[],
    notes TEXT,

    INDEX idx_person (person_id),
    INDEX idx_event_date (burnout_date),
    INDEX idx_was_predicted (was_predicted),
    CONSTRAINT check_event_type CHECK (event_type IN ('medical_leave', 'resignation', 'mbi_high', 'self_reported', 'other'))
);
```

---

#### `personal_calibration`

```sql
CREATE TABLE personal_calibration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES people(id) UNIQUE,
    calibrated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW(),

    -- S-N Curve parameters
    sigma_f_prime FLOAT NOT NULL DEFAULT 100.0,
    b FLOAT NOT NULL DEFAULT -0.12,
    endurance_limit FLOAT NOT NULL DEFAULT 50.0,

    -- Larson-Miller parameters
    personal_LMP FLOAT NOT NULL DEFAULT 30000,
    resilience_classification VARCHAR(20),  -- High, Average, Low

    -- Paris Law parameters
    paris_C FLOAT NOT NULL DEFAULT 1e-5,
    paris_m FLOAT NOT NULL DEFAULT 3.0,

    -- Calibration quality
    calibration_samples INTEGER NOT NULL DEFAULT 0,
    mae_error_days FLOAT,
    r_squared FLOAT,

    -- Metadata
    notes TEXT,

    CONSTRAINT check_resilience CHECK (resilience_classification IN ('High', 'Average', 'Low'))
);
```

---

### 5.2 Alembic Migration Example

```python
"""Add burnout prediction tables

Revision ID: add_burnout_prediction
Revises: previous_revision
Create Date: 2025-12-26 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_burnout_prediction'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade():
    # Create burnout_predictions table
    op.create_table(
        'burnout_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('person_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),

        sa.Column('sn_curve_prediction', sa.Float()),
        sa.Column('miner_damage', sa.Float(), nullable=False),
        sa.Column('miner_cycles_remaining', sa.Float()),
        sa.Column('coffin_manson_regime', sa.String(30)),
        sa.Column('larson_miller_days', sa.Float()),
        sa.Column('paris_law_weeks', sa.Float()),

        sa.Column('ensemble_prediction_days', sa.Float(), nullable=False),
        sa.Column('confidence_interval_lower', sa.Float(), nullable=False),
        sa.Column('confidence_interval_upper', sa.Float(), nullable=False),

        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('primary_failure_mode', sa.String(50), nullable=False),

        sa.Column('interventions', postgresql.ARRAY(sa.Text())),
        sa.Column('workload_adjustment_recommended', sa.Float()),

        sa.Column('models_used', sa.Integer(), nullable=False),
        sa.Column('prediction_quality', sa.String(20), nullable=False),

        sa.ForeignKeyConstraint(['person_id'], ['people.id']),
        sa.CheckConstraint("risk_level IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL')"),
    )

    op.create_index('idx_burnout_person_date', 'burnout_predictions', ['person_id', 'prediction_date'])
    op.create_index('idx_burnout_risk_level', 'burnout_predictions', ['risk_level'])

    # Create other tables (workload_history, symptom_records, etc.)
    # ... similar pattern


def downgrade():
    op.drop_table('burnout_predictions')
    # Drop other tables
```

---

## 6. Ensemble Logic

### 6.1 Weighted Ensemble Algorithm

```python
"""Ensemble prediction algorithm."""
from typing import List, Tuple


class EnsembleBurnoutPredictor:
    """Multi-model ensemble predictor."""

    def predict(
        self,
        person_id: UUID,
        workload_history: List[WorkloadRecord],
        symptom_history: List[SymptomRecord],
        current_stress: float,
    ) -> BurnoutPrediction:
        """Generate ensemble prediction."""

        # 1. S-N Curve: Predict based on current workload intensity
        sn_days = self._predict_sn_curve(workload_history)

        # 2. Miner's Rule: Calculate cumulative damage
        miner_calc, miner_days = self._predict_miner_damage(workload_history, current_stress)

        # 3. Coffin-Manson: Classify fatigue regime
        cm_regime = self._classify_fatigue_regime(workload_history)

        # 4. Larson-Miller: Predict based on sustained stress
        lm_days = self._predict_larson_miller(current_stress)

        # 5. Paris Law: Predict based on symptom progression
        paris_weeks = self._predict_paris_law(symptom_history)
        paris_days = paris_weeks * 7 if paris_weeks else None

        # 6. Combine predictions with weighted average
        ensemble_days, ci_lower, ci_upper, models_used = self._ensemble_combine(
            sn_days, miner_days, lm_days, paris_days
        )

        # 7. Classify risk level
        risk_level = self._classify_risk(ensemble_days)

        # 8. Determine primary failure mode
        primary_mode = self._determine_failure_mode(
            sn_days, miner_days, lm_days, paris_days
        )

        # 9. Generate interventions
        interventions = self._generate_interventions(
            risk_level, primary_mode, miner_calc.damage_sum, ensemble_days
        )

        # 10. Calculate workload adjustment
        workload_adjustment = self._calculate_workload_adjustment(risk_level)

        # 11. Assess prediction quality
        quality = self._assess_quality(models_used, workload_history, symptom_history)

        return BurnoutPrediction(
            person_id=person_id,
            prediction_date=date.today(),
            sn_curve_prediction=sn_days,
            miner_damage=miner_calc.damage_sum,
            miner_cycles_remaining=miner_calc.predict_failure_in_cycles(current_stress) if miner_days else None,
            coffin_manson_regime=cm_regime,
            larson_miller_days=lm_days,
            paris_law_weeks=paris_weeks,
            ensemble_prediction_days=ensemble_days,
            confidence_interval_lower=ci_lower,
            confidence_interval_upper=ci_upper,
            risk_level=risk_level,
            primary_failure_mode=primary_mode,
            interventions=interventions,
            workload_adjustment_recommended=workload_adjustment,
            models_used=models_used,
            prediction_quality=quality,
        )

    def _ensemble_combine(
        self,
        sn_days: float | None,
        miner_days: float | None,
        lm_days: float | None,
        paris_days: float | None,
    ) -> Tuple[float, float, float, int]:
        """
        Combine model predictions using weighted average.

        Returns:
            (ensemble_days, ci_lower, ci_upper, models_used)
        """
        predictions = []
        weights = []

        if sn_days and sn_days != float('inf'):
            predictions.append(sn_days)
            weights.append(self.config.weight_sn_curve)

        if miner_days and miner_days != float('inf'):
            predictions.append(miner_days)
            weights.append(self.config.weight_miner)

        if lm_days and lm_days != float('inf'):
            predictions.append(lm_days)
            weights.append(self.config.weight_larson_miller)

        if paris_days and paris_days != float('inf'):
            predictions.append(paris_days)
            weights.append(self.config.weight_paris_law)

        if not predictions:
            return float('inf'), float('inf'), float('inf'), 0

        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]

        # Weighted average
        ensemble_days = sum(p * w for p, w in zip(predictions, normalized_weights))

        # Confidence interval (±30% empirically calibrated)
        ci_lower = ensemble_days * 0.7
        ci_upper = ensemble_days * 1.3

        return ensemble_days, ci_lower, ci_upper, len(predictions)

    def _classify_risk(self, days_to_burnout: float) -> str:
        """Classify risk level based on days to burnout."""
        if days_to_burnout < self.config.critical_threshold:
            return "CRITICAL"
        elif days_to_burnout < self.config.high_threshold:
            return "HIGH"
        elif days_to_burnout < self.config.moderate_threshold:
            return "MODERATE"
        else:
            return "LOW"

    def _determine_failure_mode(
        self,
        sn_days: float | None,
        miner_days: float | None,
        lm_days: float | None,
        paris_days: float | None,
    ) -> str:
        """Determine which model predicts earliest failure."""
        predictions = {
            "CYCLIC_FATIGUE": sn_days or float('inf'),
            "CUMULATIVE_DAMAGE": miner_days or float('inf'),
            "CREEP_RUPTURE": lm_days or float('inf'),
            "CRACK_PROPAGATION": paris_days or float('inf'),
        }

        return min(predictions.items(), key=lambda x: x[1])[0]

    def _generate_interventions(
        self,
        risk_level: str,
        failure_mode: str,
        miner_damage: float,
        days_to_burnout: float,
    ) -> List[str]:
        """Generate intervention recommendations."""
        interventions = []

        # Risk-based interventions
        if risk_level == "CRITICAL":
            interventions.append("IMMEDIATE: Remove from clinical duties (medical leave)")
            interventions.append("Psychiatric evaluation within 24 hours")
            interventions.append("Crisis intervention team activation")
        elif risk_level == "HIGH":
            interventions.append("URGENT: Reduce workload 50% for 4 weeks minimum")
            interventions.append("Weekly therapy sessions (CBT/supportive)")
            interventions.append("Daily symptom monitoring")
        elif risk_level == "MODERATE":
            interventions.append("Reduce workload 20-30%")
            interventions.append("Bi-weekly counseling sessions")
            interventions.append("Weekly symptom checks")

        # Mode-specific interventions
        if failure_mode == "CUMULATIVE_DAMAGE":
            interventions.append("Limit high-intensity cycles (weekend call, night shifts)")
            interventions.append("Increase recovery time between demanding rotations")
        elif failure_mode == "CREEP_RUPTURE":
            interventions.append("Reduce sustained workload (<70% capacity)")
            interventions.append("Implement mandatory rest weeks every 8 weeks")
        elif failure_mode == "CRACK_PROPAGATION":
            interventions.append("Stabilize workload (reduce stress fluctuations)")
            interventions.append("Increase social support and mentorship")

        # Miner damage-specific
        if miner_damage > 0.8:
            interventions.append("Critical cumulative damage - extended recovery protocol needed")

        return interventions

    def _calculate_workload_adjustment(self, risk_level: str) -> float:
        """Calculate recommended workload reduction."""
        adjustments = {
            "CRITICAL": -0.75,    # 75% reduction
            "HIGH": -0.50,        # 50% reduction
            "MODERATE": -0.25,    # 25% reduction
            "LOW": 0.0,           # No change
        }
        return adjustments.get(risk_level, 0.0)

    def _assess_quality(
        self,
        models_used: int,
        workload_history: List,
        symptom_history: List,
    ) -> str:
        """Assess prediction quality based on data availability."""
        if models_used >= 4 and len(workload_history) >= 12 and len(symptom_history) >= 3:
            return "EXCELLENT"
        elif models_used >= 3 and len(workload_history) >= 8:
            return "GOOD"
        elif models_used >= 2 and len(workload_history) >= 4:
            return "FAIR"
        else:
            return "POOR"
```

---

### 6.2 Confidence Interval Calculation

**Method**: Bootstrap confidence intervals

```python
def calculate_bootstrap_ci(
    predictions: List[float],
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for ensemble prediction.

    Args:
        predictions: Individual model predictions
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level (0.95 = 95%)

    Returns:
        (lower_bound, upper_bound)
    """
    bootstrap_means = []

    for _ in range(n_bootstrap):
        # Resample with replacement
        sample = np.random.choice(predictions, size=len(predictions), replace=True)
        bootstrap_means.append(np.mean(sample))

    # Calculate percentiles
    alpha = 1 - confidence
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    ci_lower = np.percentile(bootstrap_means, lower_percentile)
    ci_upper = np.percentile(bootstrap_means, upper_percentile)

    return ci_lower, ci_upper
```

---

## 7. Integration Points

### 7.1 Resilience Framework Integration

**Connect to existing resilience service:**

```python
# In app/resilience/service.py

class ResilienceService:
    """Enhanced with burnout prediction."""

    def __init__(self, db: Session, config: ResilienceConfig = None):
        # ... existing initialization

        # Add burnout predictor
        from app.analytics.burnout_prediction.service import BurnoutPredictionService
        self.burnout_predictor = BurnoutPredictionService(db)

    async def check_health(
        self,
        faculty: list,
        blocks: list,
        assignments: list,
        coverage_requirements: dict[UUID, int] | None = None,
    ) -> SystemHealthReport:
        """Enhanced health check with burnout predictions."""

        # ... existing health check logic

        # Add burnout risk assessment for all faculty
        burnout_risks = []
        for person in faculty:
            try:
                prediction = await self.burnout_predictor.predict_burnout(person.id)
                if prediction.risk_level in ("HIGH", "CRITICAL"):
                    burnout_risks.append({
                        'person_id': person.id,
                        'risk_level': prediction.risk_level,
                        'days_to_burnout': prediction.ensemble_prediction_days,
                    })
            except Exception as e:
                logger.warning(f"Burnout prediction failed for {person.id}: {e}")

        # Add to report
        report.burnout_risks = burnout_risks

        # Generate additional recommendations
        if burnout_risks:
            report.immediate_actions.insert(
                0,
                f"BURNOUT ALERT: {len(burnout_risks)} faculty at HIGH/CRITICAL risk"
            )

        return report
```

---

### 7.2 Scheduling Constraints Integration

**Use predictions as soft constraints in scheduler:**

```python
# In app/scheduling/constraints/burnout_protection.py

from app.analytics.burnout_prediction.service import BurnoutPredictionService


class BurnoutProtectionConstraint:
    """Constraint to protect high-risk faculty from overload."""

    def __init__(self, db: Session):
        self.burnout_service = BurnoutPredictionService(db)
        self.weight = 100  # High priority

    async def evaluate(
        self,
        assignment: Assignment,
        schedule_state: ScheduleState,
    ) -> float:
        """
        Evaluate constraint violation.

        Returns:
            Penalty score (0 = no violation, higher = worse)
        """
        # Get burnout prediction for this person
        prediction = await self.burnout_service.predict_burnout(assignment.person_id)

        # High penalty if assigning high-intensity work to high-risk person
        if prediction.risk_level == "CRITICAL":
            return 1000.0  # Strong penalty
        elif prediction.risk_level == "HIGH":
            # Scale penalty by workload intensity
            workload_intensity = self._estimate_workload_intensity(assignment)
            if workload_intensity > 75:
                return 500.0
            elif workload_intensity > 60:
                return 200.0
        elif prediction.risk_level == "MODERATE":
            workload_intensity = self._estimate_workload_intensity(assignment)
            if workload_intensity > 85:
                return 100.0

        return 0.0  # No penalty for low-risk or low-intensity assignments
```

---

### 7.3 Alert Integration

**Emit events for high-risk predictions:**

```python
# In app/analytics/burnout_prediction/service.py

class BurnoutPredictionService:

    async def predict_burnout(
        self,
        person_id: UUID,
        current_date: date | None = None,
    ) -> BurnoutPrediction:
        """Generate prediction and emit alerts."""

        # ... prediction logic

        # Emit alert events
        if prediction.risk_level == "CRITICAL":
            await self._emit_critical_alert(prediction)
        elif prediction.risk_level == "HIGH":
            await self._emit_high_risk_alert(prediction)

        return prediction

    async def _emit_critical_alert(self, prediction: BurnoutPrediction):
        """Send critical burnout alert."""
        from app.services.email_service import EmailService
        from app.models.notification import NotificationType

        email_service = EmailService(self.db)

        # Get person details
        person = await self.db.get(Person, prediction.person_id)

        # Send email to program leadership
        await email_service.send_notification(
            recipient_emails=["program_director@example.com", "coordinator@example.com"],
            subject=f"CRITICAL Burnout Alert: {person.name}",
            template="burnout_critical_alert",
            context={
                "person_name": person.name,
                "days_to_burnout": prediction.ensemble_prediction_days,
                "primary_mode": prediction.primary_failure_mode,
                "interventions": prediction.interventions,
            },
            notification_type=NotificationType.CRITICAL_ALERT,
        )
```

---

### 7.4 Dashboard Visualization

**Add burnout risk widget to main dashboard:**

```typescript
// frontend/src/components/dashboard/BurnoutRiskWidget.tsx

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

interface BurnoutRisk {
  person_id: string;
  person_name: string;
  role: string;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  days_to_burnout: number;
  miner_damage: number;
}

export function BurnoutRiskWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ['burnout-dashboard'],
    queryFn: () => apiClient.get('/api/v1/burnout/dashboard'),
    refetchInterval: 60000, // Refresh every minute
  });

  if (isLoading) return <div>Loading burnout risk data...</div>;

  const criticalCount = data?.risk_distribution?.CRITICAL || 0;
  const highCount = data?.risk_distribution?.HIGH || 0;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Burnout Risk Status</h3>

      {/* Alert banner if critical risks */}
      {criticalCount > 0 && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <strong>CRITICAL:</strong> {criticalCount} person(s) at immediate burnout risk
        </div>
      )}

      {/* Risk distribution */}
      <div className="grid grid-cols-4 gap-4 mb-4">
        <RiskCard level="CRITICAL" count={criticalCount} color="red" />
        <RiskCard level="HIGH" count={highCount} color="orange" />
        <RiskCard level="MODERATE" count={data?.risk_distribution?.MODERATE || 0} color="yellow" />
        <RiskCard level="LOW" count={data?.risk_distribution?.LOW || 0} color="green" />
      </div>

      {/* High-risk individuals */}
      {(criticalCount > 0 || highCount > 0) && (
        <div className="mt-4">
          <h4 className="font-semibold mb-2">Immediate Attention Required:</h4>
          <ul className="space-y-2">
            {data?.predictions
              ?.filter((p: BurnoutRisk) => ['CRITICAL', 'HIGH'].includes(p.risk_level))
              .map((p: BurnoutRisk) => (
                <li key={p.person_id} className="border-l-4 border-red-500 pl-3">
                  <span className="font-medium">{p.person_name}</span>
                  {' - '}
                  <span className="text-sm text-gray-600">
                    {Math.round(p.days_to_burnout)} days to burnout
                  </span>
                  {' - '}
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                    Damage: {(p.miner_damage * 100).toFixed(0)}%
                  </span>
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

---

## 8. Implementation Plan

### Phase 1: Core Models (Weeks 1-2)

**Tasks**:
1. Implement S-N Curve model
2. Implement Miner's Rule calculator
3. Create database schema (migrations)
4. Write unit tests for models

**Deliverables**:
- `sn_curve.py` with full implementation
- `miners_rule.py` with full implementation
- Alembic migration for `workload_history` table
- 90%+ test coverage

---

### Phase 2: Symptom Tracking (Week 3)

**Tasks**:
1. Implement Paris Law model
2. Create `symptom_records` table
3. Build symptom recording API endpoint
4. Integrate with existing MBI assessments (if any)

**Deliverables**:
- `paris_law.py` with crack growth tracking
- POST /api/v1/burnout/symptoms endpoint
- Dashboard widget for symptom progression

---

### Phase 3: Advanced Models (Week 4)

**Tasks**:
1. Implement Larson-Miller model
2. Implement Coffin-Manson model
3. Build ensemble predictor
4. Create calibration system

**Deliverables**:
- `larson_miller.py` and `coffin_manson.py`
- `ensemble.py` with weighted averaging
- `calibration.py` with parameter optimization

---

### Phase 4: Service Integration (Week 5)

**Tasks**:
1. Create main `BurnoutPredictionService`
2. Build all API endpoints
3. Integrate with ResilienceService
4. Add scheduling constraint

**Deliverables**:
- Complete service class
- All 5 API endpoints functional
- Integrated health checks
- Burnout protection constraint

---

### Phase 5: Validation & Refinement (Week 6)

**Tasks**:
1. Collect historical burnout data for calibration
2. Run retrospective validation
3. Tune ensemble weights
4. Build dashboard visualizations

**Deliverables**:
- Calibrated model parameters
- Validation report with accuracy metrics
- Production-ready dashboard

---

### Phase 6: Deployment (Week 7)

**Tasks**:
1. Performance testing
2. Documentation updates
3. User training materials
4. Production deployment

**Deliverables**:
- Load testing results
- Updated user documentation
- Training videos/guides
- Production deployment checklist

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Coverage Requirements**: ≥90% for all model classes

```python
# backend/tests/analytics/burnout_prediction/test_sn_curve.py

import pytest
from app.analytics.burnout_prediction.models.sn_curve import SNCurveModel
from app.analytics.burnout_prediction.service import BurnoutPredictionConfig


class TestSNCurveModel:
    """Test S-N curve model."""

    @pytest.fixture
    def model(self):
        config = BurnoutPredictionConfig()
        return SNCurveModel(config)

    def test_cycles_to_failure_high_intensity(self, model):
        """Test prediction for high-intensity workload."""
        cycles = model.cycles_to_failure(85.0)
        assert 40 < cycles < 60, "Expected ~52 cycles for 85% intensity"

    def test_cycles_to_failure_below_endurance(self, model):
        """Test that stress below endurance limit gives infinite cycles."""
        cycles = model.cycles_to_failure(45.0)
        assert cycles >= 1e6, "Expected infinite cycles below endurance limit"

    def test_stress_for_target_life(self, model):
        """Test finding safe stress for target duration."""
        # 3-year residency = 156 weeks
        safe_stress = model.stress_for_target_life(156)
        assert 60 < safe_stress < 75, "Expected moderate stress for 3-year duration"

    def test_parameter_calibration(self):
        """Test that parameters can be calibrated from observed data."""
        config = BurnoutPredictionConfig(
            sn_sigma_f_prime=95.0,  # Personalized value
            sn_b=-0.15,             # More susceptible to fatigue
        )
        model = SNCurveModel(config)

        cycles = model.cycles_to_failure(85.0)
        assert cycles < 52, "More susceptible person should have fewer cycles"
```

---

### 9.2 Integration Tests

```python
# backend/tests/analytics/burnout_prediction/test_service_integration.py

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.analytics.burnout_prediction.service import BurnoutPredictionService
from app.models.person import Person


@pytest.mark.asyncio
class TestBurnoutPredictionServiceIntegration:
    """Integration tests for burnout prediction service."""

    async def test_predict_with_workload_history(self, db, sample_person):
        """Test prediction with realistic workload history."""
        service = BurnoutPredictionService(db)

        # Create workload history (3 months of data)
        await self._create_workload_history(db, sample_person.id, days=90)

        # Generate prediction
        prediction = await service.predict_burnout(sample_person.id)

        assert prediction.person_id == sample_person.id
        assert prediction.ensemble_prediction_days > 0
        assert prediction.risk_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
        assert 0.0 <= prediction.miner_damage <= 2.0
        assert len(prediction.interventions) > 0

    async def test_predict_critical_risk(self, db, sample_person):
        """Test prediction for person at critical risk."""
        service = BurnoutPredictionService(db)

        # Create high-intensity workload history
        await self._create_high_intensity_history(db, sample_person.id)

        prediction = await service.predict_burnout(sample_person.id)

        assert prediction.risk_level in ["HIGH", "CRITICAL"]
        assert prediction.miner_damage > 0.7
        assert "URGENT" in " ".join(prediction.interventions)

    async def test_calibration_improves_accuracy(self, db, sample_person):
        """Test that calibration improves prediction accuracy."""
        service = BurnoutPredictionService(db)

        # Record observed burnout event
        burnout_date = date.today() - timedelta(days=30)
        await service.calibrate_personal_model(
            person_id=sample_person.id,
            observed_burnout_date=burnout_date,
            workload_at_burnout=78.0,
        )

        # Check that personal parameters were created
        calibration = await db.execute(
            select(PersonalCalibration).where(
                PersonalCalibration.person_id == sample_person.id
            )
        )
        cal = calibration.scalar_one_or_none()

        assert cal is not None
        assert cal.sigma_f_prime != 100.0  # Should be personalized
```

---

### 9.3 Performance Tests

```python
# backend/tests/performance/test_burnout_prediction_load.py

import pytest
import time
from concurrent.futures import ThreadPoolExecutor

from app.analytics.burnout_prediction.service import BurnoutPredictionService


@pytest.mark.performance
class TestBurnoutPredictionPerformance:
    """Performance tests for burnout prediction."""

    async def test_prediction_latency(self, db, sample_person):
        """Test that predictions complete within acceptable time."""
        service = BurnoutPredictionService(db)

        # Create realistic data
        await self._create_workload_history(db, sample_person.id, days=180)
        await self._create_symptom_history(db, sample_person.id, assessments=6)

        # Measure prediction time
        start = time.time()
        prediction = await service.predict_burnout(sample_person.id)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Prediction took {elapsed}s, expected < 0.5s"

    async def test_concurrent_predictions(self, db):
        """Test handling concurrent prediction requests."""
        service = BurnoutPredictionService(db)

        # Create 50 people with data
        people = await self._create_test_people(db, count=50)

        # Predict concurrently
        start = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(service.predict_burnout, person.id)
                for person in people
            ]
            results = [f.result() for f in futures]

        elapsed = time.time() - start

        assert len(results) == 50
        assert elapsed < 5.0, f"50 concurrent predictions took {elapsed}s, expected < 5s"
        assert all(r.risk_level is not None for r in results)
```

---

## 10. Performance Requirements

### 10.1 Latency Requirements

| Operation | Target | Maximum |
|-----------|--------|---------|
| **Single prediction** | < 200ms | < 500ms |
| **Fatigue score calculation** | < 100ms | < 250ms |
| **Dashboard (all residents)** | < 1s | < 2s |
| **Symptom recording** | < 50ms | < 100ms |
| **Calibration** | < 500ms | < 1s |

---

### 10.2 Throughput Requirements

| Metric | Target |
|--------|--------|
| **Predictions per second** | ≥100 |
| **Concurrent users** | ≥20 |
| **Database queries per prediction** | ≤5 |

---

### 10.3 Data Volume Assumptions

| Data Type | Volume Estimate |
|-----------|----------------|
| **People** | 50-100 (1 residency program) |
| **Workload records per person per year** | ~365 (daily) |
| **Symptom assessments per person per year** | 12 (monthly) |
| **Predictions per person per month** | 4 (weekly) |
| **Total database size (1 year)** | < 100 MB |

---

### 10.4 Optimization Strategies

1. **Database Indexing**:
   - Index on `(person_id, date DESC)` for all history tables
   - Composite index on `(person_id, prediction_date)` for predictions

2. **Caching**:
   - Cache calibrated parameters per person (invalidate on new burnout event)
   - Cache recent predictions (TTL: 1 hour)

3. **Batch Processing**:
   - Dashboard endpoint: Use single query with JOINs instead of N+1
   - Precompute ensemble weights at startup

4. **Async Operations**:
   - All database queries async
   - Parallel model execution where possible

---

## Appendix A: Sample Data for Testing

### A.1 Workload History Sample

```python
# backend/tests/fixtures/burnout_prediction.py

@pytest.fixture
async def sample_workload_history(db, sample_person):
    """Create sample workload history for testing."""
    from app.models.burnout import WorkloadHistory

    # 3 months of varied workload
    workload_data = [
        # Month 1: Moderate intensity
        {"cycle_type": "clinic", "intensity": 60, "duration": 8, "unrecoverable": 0.05},
        {"cycle_type": "clinic", "intensity": 65, "duration": 8, "unrecoverable": 0.08},
        # ... repeat for 4 weeks

        # Month 2: Increasing intensity
        {"cycle_type": "weekend_call", "intensity": 85, "duration": 28, "unrecoverable": 0.30},
        {"cycle_type": "night_float", "intensity": 75, "duration": 24, "unrecoverable": 0.20},
        # ... repeat for 4 weeks

        # Month 3: High intensity (risk building)
        {"cycle_type": "weekend_call", "intensity": 85, "duration": 28, "unrecoverable": 0.30},
        {"cycle_type": "night_float", "intensity": 75, "duration": 24, "unrecoverable": 0.20},
        {"cycle_type": "weekend_call", "intensity": 85, "duration": 28, "unrecoverable": 0.30},
        # ... repeat for 4 weeks
    ]

    records = []
    for i, data in enumerate(workload_data):
        record = WorkloadHistory(
            person_id=sample_person.id,
            date=date.today() - timedelta(days=90-i),
            **data
        )
        db.add(record)
        records.append(record)

    await db.commit()
    return records
```

---

## Appendix B: Calibration Procedure

### B.1 Initial Population Calibration

```python
"""Population-level calibration from historical burnout events."""
from scipy.optimize import minimize
import numpy as np


async def calibrate_population_parameters(
    db: Session,
    burnout_events: List[BurnoutEvent],
) -> BurnoutPredictionConfig:
    """
    Calibrate model parameters from historical burnout data.

    Args:
        db: Database session
        burnout_events: List of observed burnout events with workload data

    Returns:
        Optimized BurnoutPredictionConfig
    """

    def objective(params):
        """Minimize prediction error across all events."""
        sigma_f_prime, b = params

        errors = []
        for event in burnout_events:
            # Predicted cycles using these parameters
            N_pred = (event.average_workload_percent / sigma_f_prime) ** (1 / b)

            # Actual cycles
            N_actual = event.cycles_to_burnout

            # Log-scale error (more robust for wide range of values)
            error = (np.log10(N_pred) - np.log10(N_actual)) ** 2
            errors.append(error)

        return np.sum(errors)

    # Initial guess (default parameters)
    x0 = [100.0, -0.12]

    # Bounds (reasonable ranges from materials science)
    bounds = [(80, 120), (-0.20, -0.05)]

    # Optimize
    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')

    sigma_f_prime_opt, b_opt = result.x

    logger.info(
        f"Population calibration complete: "
        f"σ_f' = {sigma_f_prime_opt:.2f}, b = {b_opt:.3f}"
    )

    return BurnoutPredictionConfig(
        sn_sigma_f_prime=sigma_f_prime_opt,
        sn_b=b_opt,
    )
```

---

## Appendix C: Validation Metrics

### C.1 Model Validation Report Template

```python
"""Generate validation report for burnout prediction models."""
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    confusion_matrix,
    classification_report,
)


async def generate_validation_report(
    db: Session,
    validation_set: List[BurnoutEvent],
) -> Dict:
    """
    Generate comprehensive validation report.

    Args:
        db: Database session
        validation_set: Held-out burnout events for validation

    Returns:
        Validation metrics report
    """
    service = BurnoutPredictionService(db)

    # Generate predictions for validation set
    predictions = []
    actuals = []

    for event in validation_set:
        # Predict burnout at T-12 weeks
        prediction_date = event.burnout_date - timedelta(weeks=12)

        pred = await service.predict_burnout(
            person_id=event.person_id,
            current_date=prediction_date,
        )

        predictions.append(pred.ensemble_prediction_days / 7)  # Convert to weeks
        actuals.append(12)  # Actual was 12 weeks

    # Regression metrics
    mae = mean_absolute_error(actuals, predictions)
    rmse = np.sqrt(mean_squared_error(actuals, predictions))
    r2 = r2_score(actuals, predictions)

    # Classification metrics (binary: will burn out within 12 weeks?)
    y_true = [1] * len(validation_set)  # All did burn out
    y_pred = [1 if p <= 12 else 0 for p in predictions]

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0

    return {
        "validation_date": date.today().isoformat(),
        "sample_size": len(validation_set),
        "regression_metrics": {
            "mae_weeks": round(mae, 2),
            "rmse_weeks": round(rmse, 2),
            "r_squared": round(r2, 3),
        },
        "classification_metrics": {
            "sensitivity": round(sensitivity, 3),
            "specificity": round(specificity, 3),
            "ppv": round(ppv, 3),
            "confusion_matrix": {
                "true_positives": int(tp),
                "false_positives": int(fp),
                "true_negatives": int(tn),
                "false_negatives": int(fn),
            },
        },
        "performance_assessment": (
            "EXCELLENT" if mae < 1.5 and sensitivity >= 0.85 else
            "GOOD" if mae < 2.0 and sensitivity >= 0.80 else
            "FAIR" if mae < 3.0 and sensitivity >= 0.70 else
            "POOR"
        ),
    }
```

---

## Document Metadata

- **Authors**: AI Development Team
- **Reviewers**: Resilience Framework Team, Clinical Leadership
- **Target Implementation**: Q1 2026
- **Expected Development Time**: 7 weeks
- **Dependencies**:
  - Existing resilience framework
  - Person/workload tracking infrastructure
  - Email notification system

---

**Next Steps**:
1. Review specification with stakeholders
2. Collect 20-30 historical burnout cases for calibration
3. Begin Phase 1 implementation (S-N Curve + Miner's Rule)
4. Set up data collection for prospective validation
5. Plan pilot deployment in one residency service

---

*This specification bridges materials science and workforce psychology, providing quantitative tools to predict and prevent burnout using battle-tested engineering failure models.*
