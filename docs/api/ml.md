# Machine Learning API

API endpoints for ML-based schedule scoring and predictions.

---

## Overview

The ML API provides machine learning capabilities for scheduling:
- **Schedule Scoring**: Evaluate schedule quality
- **Conflict Prediction**: Predict ACGME violations
- **Preference Prediction**: Predict faculty preferences
- **Workload Optimization**: Analyze and rebalance workload

**Base URL:** `/api/ml`

---

## Model Health

### Check Model Health

<span class="endpoint-badge get">GET</span> `/api/ml/health`

Check status of ML models.

**Requires:** Admin privileges

**Response:**

```json
{
  "ml_enabled": true,
  "models_available": "3/3",
  "models": [
    {
      "name": "preference",
      "available": true,
      "last_trained": "2024-01-10T08:00:00Z",
      "age_days": 5
    },
    {
      "name": "conflict",
      "available": true,
      "last_trained": "2024-01-10T08:00:00Z",
      "age_days": 5
    },
    {
      "name": "workload",
      "available": true,
      "last_trained": "2024-01-10T08:00:00Z",
      "age_days": 5
    }
  ],
  "recommendations": []
}
```

---

## Model Training

### Train Models (Synchronous)

<span class="endpoint-badge post">POST</span> `/api/ml/train`

Train ML models on historical data (synchronous).

**Requires:** Admin privileges

**Request Body:**

```json
{
  "model_types": ["preference", "conflict", "workload"],
  "lookback_days": 365,
  "force_retrain": false
}
```

**Response:**

```json
{
  "timestamp": "2024-01-15T10:00:00Z",
  "lookback_days": 365,
  "models_trained": 3,
  "results": {
    "preference": {
      "model_name": "preference",
      "status": "trained",
      "samples": 5000,
      "metrics": {
        "train_r2": 0.85,
        "validation_r2": 0.82
      }
    },
    "conflict": {
      "model_name": "conflict",
      "status": "trained",
      "samples": 3000,
      "metrics": {
        "accuracy": 0.92,
        "precision": 0.88,
        "recall": 0.85
      }
    },
    "workload": {
      "model_name": "workload",
      "status": "trained",
      "samples": 500,
      "metrics": {
        "train_r2": 0.78,
        "validation_r2": 0.75
      }
    }
  }
}
```

---

### Train Models (Async)

<span class="endpoint-badge post">POST</span> `/api/ml/train/async`

Trigger async model training via Celery.

**Requires:** Admin privileges

**Response:**

```json
{
  "status": "training_started",
  "task_id": "abc-123-def",
  "message": "Training task submitted. Check status via /jobs/{task_id}."
}
```

---

## Schedule Scoring

### Score Schedule

<span class="endpoint-badge post">POST</span> `/api/ml/score`

Score a schedule using ML models.

**Request Body:**

```json
{
  "schedule_data": {
    "assignments": [
      {
        "person_id": "uuid-1",
        "block_id": "uuid-block",
        "rotation_id": "uuid-rotation"
      }
    ]
  },
  "include_suggestions": true
}
```

**Response:**

```json
{
  "overall_score": 0.85,
  "grade": "B+",
  "components": [
    {
      "name": "preference",
      "score": 0.82,
      "weight": 0.4,
      "details": {
        "excellent": 45,
        "good": 30,
        "acceptable": 20,
        "poor": 5
      }
    },
    {
      "name": "workload",
      "score": 0.88,
      "weight": 0.3,
      "details": {
        "gini_coefficient": 0.15,
        "overloaded_count": 2
      }
    },
    {
      "name": "conflict",
      "score": 0.85,
      "weight": 0.3,
      "details": {
        "high_risk": 3,
        "medium_risk": 10
      }
    }
  ],
  "suggestions": [
    {
      "type": "workload_rebalance",
      "priority": "medium",
      "description": "Redistribute 2 assignments from Dr. Smith to reduce overload",
      "impact": 0.05,
      "affected_items": ["assignment-123", "assignment-456"]
    }
  ]
}
```

### Grade Scale

| Score Range | Grade | Description |
|-------------|-------|-------------|
| 0.95-1.00 | A+ | Excellent |
| 0.90-0.94 | A | Very Good |
| 0.85-0.89 | B+ | Good |
| 0.80-0.84 | B | Above Average |
| 0.70-0.79 | C | Average |
| 0.60-0.69 | D | Below Average |
| < 0.60 | F | Poor |

---

## Conflict Prediction

### Predict Conflict

<span class="endpoint-badge post">POST</span> `/api/ml/predict/conflict`

Predict conflict probability for a proposed assignment.

**Request Body:**

```json
{
  "person_id": "uuid-person",
  "block_id": "uuid-block",
  "rotation_id": "uuid-rotation",
  "existing_assignments": [
    {
      "block_id": "uuid-block-2",
      "hours": 10
    }
  ]
}
```

**Response:**

```json
{
  "conflict_probability": 0.72,
  "risk_level": "HIGH",
  "risk_factors": [
    "Weekly hours approaching 80-hour limit",
    "No day off in past 6 days"
  ],
  "recommendation": "Elevated conflict risk. Review carefully before proceeding."
}
```

### Risk Levels

| Probability | Level | Description |
|-------------|-------|-------------|
| >= 0.80 | CRITICAL | Very high conflict risk |
| >= 0.60 | HIGH | Elevated risk, review carefully |
| >= 0.40 | MEDIUM | Moderate risk, monitor |
| >= 0.20 | LOW | Low risk, proceed normally |
| < 0.20 | MINIMAL | Minimal conflict risk |

---

## Preference Prediction

### Predict Preference

<span class="endpoint-badge post">POST</span> `/api/ml/predict/preference`

Predict preference score for a proposed assignment.

**Request Body:**

```json
{
  "person_id": "uuid-person",
  "rotation_id": "uuid-rotation",
  "block_id": "uuid-block"
}
```

**Response:**

```json
{
  "preference_score": 0.85,
  "interpretation": "Highly preferred assignment",
  "contributing_factors": [
    {
      "factor": "rotation_type",
      "contribution": 0.3,
      "value": "clinic"
    },
    {
      "factor": "day_of_week",
      "contribution": 0.2,
      "value": "tuesday"
    }
  ]
}
```

---

## Workload Analysis

### Analyze Workload

<span class="endpoint-badge post">POST</span> `/api/ml/analyze/workload`

Analyze workload distribution across personnel.

**Request Body:**

```json
{
  "person_ids": null,
  "start_date": "2024-01-01",
  "end_date": "2024-03-31"
}
```

**Response:**

```json
{
  "total_people": 25,
  "overloaded_count": 3,
  "underutilized_count": 2,
  "fairness_score": 0.85,
  "gini_coefficient": 0.18,
  "people": [
    {
      "person_id": "uuid-1",
      "person_name": "Dr. Smith",
      "current_utilization": 0.92,
      "optimal_utilization": 0.80,
      "is_overloaded": true
    }
  ],
  "rebalancing_suggestions": [
    {
      "type": "transfer",
      "priority": "high",
      "description": "Transfer 2 clinic blocks from Dr. Smith to Dr. Jones",
      "impact": 0.08
    }
  ]
}
```

---

## Configuration

Configure ML settings in `.env`:

```bash
# Enable ML features
ML_ENABLED=true
ML_MODELS_DIR=models

# Training Configuration
ML_TRAINING_LOOKBACK_DAYS=365
ML_MIN_TRAINING_SAMPLES=100
ML_AUTO_TRAINING_ENABLED=false
ML_TRAINING_FREQUENCY_DAYS=7

# Scoring Weights (must sum to 1.0)
ML_PREFERENCE_WEIGHT=0.4
ML_WORKLOAD_WEIGHT=0.3
ML_CONFLICT_WEIGHT=0.3

# Thresholds
ML_TARGET_UTILIZATION=0.80
ML_OVERLOAD_THRESHOLD=0.85
ML_CONFLICT_RISK_THRESHOLD=0.70
```

---

## Model Artifacts

Models are saved as joblib files:

```
models/
├── preference_predictor/
│   ├── model.pkl          # RandomForestRegressor
│   ├── scaler.pkl         # StandardScaler
│   └── features.pkl       # Feature names
├── conflict_predictor/
│   ├── model.pkl          # GradientBoostingClassifier
│   ├── scaler.pkl
│   └── features.pkl
└── workload_optimizer/
    ├── workload_model.pkl # GradientBoostingRegressor
    ├── clusterer.pkl      # KMeans
    ├── scaler.pkl
    └── features.pkl
```

---

## Celery Tasks

Background tasks for ML operations:

| Task | Description | Schedule |
|------|-------------|----------|
| `train_ml_models` | Train models on historical data | On-demand |
| `score_schedule` | Score a schedule async | On-demand |
| `check_model_health` | Check model status | On-demand |
| `periodic_retrain` | Auto-retrain stale models | Weekly (if enabled) |

---

## Feature Requirements

### Preference Predictor Features (31+)
- Person: type, PGY level, faculty role
- Rotation: type encoding
- Block: temporal features (day, month, weekend)
- Historical: preference scores, swap rates

### Conflict Predictor Features (25+)
- ACGME: hours worked, days since off
- Supervision: ratio requirements
- Workload: assignment count, concentration

### Workload Optimizer Features (25+)
- Person: type, role, target blocks
- Workload: rotation distribution, weekend burden
- Historical: avg workload, conflict rate
