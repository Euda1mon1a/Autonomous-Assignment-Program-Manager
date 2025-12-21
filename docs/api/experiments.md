# Experiments API (A/B Testing)

API endpoints for managing A/B tests and experiments.

---

## Overview

The experiments API provides comprehensive A/B testing capabilities:
- Create and manage experiments with multiple variants
- Assign users to variants using consistent hashing
- Track metrics and conversions
- Get statistical analysis of results

**Base URL:** `/api/experiments`

---

## Experiment Management

### Create Experiment

<span class="endpoint-badge post">POST</span> `/api/experiments/`

Create a new A/B test experiment.

**Requires:** Admin privileges

**Request Body:**

```json
{
  "key": "schedule_optimizer_v2",
  "name": "Schedule Optimizer V2 Test",
  "description": "Testing new optimization algorithm",
  "hypothesis": "New algorithm improves schedule quality by 20%",
  "variants": [
    {
      "key": "control",
      "name": "Current Algorithm",
      "allocation": 50,
      "is_control": true
    },
    {
      "key": "treatment",
      "name": "New Algorithm",
      "allocation": 50
    }
  ],
  "targeting": {
    "roles": ["admin", "coordinator"],
    "percentage": 100
  },
  "config": {
    "sticky_bucketing": true,
    "min_sample_size": 100,
    "confidence_level": 0.95
  }
}
```

**Response (201 Created):**

```json
{
  "key": "schedule_optimizer_v2",
  "name": "Schedule Optimizer V2 Test",
  "status": "draft",
  "variants": [...],
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

### List Experiments

<span class="endpoint-badge get">GET</span> `/api/experiments/`

List all experiments with optional filtering.

**Query Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `status` | string | Filter by status: `draft`, `running`, `paused`, `completed`, `cancelled` |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Items per page (default: 50, max: 100) |

**Response:**

```json
{
  "experiments": [...],
  "total": 15,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

---

### Get Experiment

<span class="endpoint-badge get">GET</span> `/api/experiments/{key}`

Get a specific experiment by key.

**Response:**

```json
{
  "key": "schedule_optimizer_v2",
  "name": "Schedule Optimizer V2 Test",
  "status": "running",
  "variants": [
    {
      "key": "control",
      "allocation": 50,
      "is_control": true
    },
    {
      "key": "treatment",
      "allocation": 50
    }
  ],
  "start_date": "2024-01-15T10:00:00Z"
}
```

---

### Update Experiment

<span class="endpoint-badge put">PUT</span> `/api/experiments/{key}`

Update an experiment. Only DRAFT experiments can have variants updated.

**Request Body:**

```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

---

### Delete Experiment

<span class="endpoint-badge delete">DELETE</span> `/api/experiments/{key}`

Cancel/delete an experiment.

---

## Experiment Lifecycle

### Start Experiment

<span class="endpoint-badge post">POST</span> `/api/experiments/{key}/start`

Start a DRAFT or PAUSED experiment.

**Response:**

```json
{
  "key": "schedule_optimizer_v2",
  "status": "running",
  "start_date": "2024-01-15T10:00:00Z"
}
```

---

### Pause Experiment

<span class="endpoint-badge post">POST</span> `/api/experiments/{key}/pause`

Pause a RUNNING experiment.

---

### Conclude Experiment

<span class="endpoint-badge post">POST</span> `/api/experiments/{key}/conclude`

Conclude an experiment with a winning variant.

**Request Body:**

```json
{
  "winning_variant": "treatment",
  "notes": "Treatment showed 25% improvement in schedule quality"
}
```

---

## User Assignment

### Assign User

<span class="endpoint-badge post">POST</span> `/api/experiments/{key}/assignments`

Assign a user to an experiment variant.

**Request Body:**

```json
{
  "user_id": "user-123",
  "user_attributes": {
    "role": "coordinator"
  },
  "force_variant": null
}
```

**Response:**

```json
{
  "experiment_key": "schedule_optimizer_v2",
  "user_id": "user-123",
  "variant_key": "treatment",
  "assigned_at": "2024-01-15T10:30:00Z",
  "is_override": false
}
```

---

### Get User Assignment

<span class="endpoint-badge get">GET</span> `/api/experiments/{key}/assignments/{user_id}`

Get a user's assignment for an experiment.

---

## Metrics & Results

### Track Metric

<span class="endpoint-badge post">POST</span> `/api/experiments/{key}/metrics`

Track a metric for an experiment.

**Request Body:**

```json
{
  "user_id": "user-123",
  "variant_key": "treatment",
  "metric_name": "schedule_quality_score",
  "value": 0.92,
  "metric_type": "numeric"
}
```

---

### Get Variant Metrics

<span class="endpoint-badge get">GET</span> `/api/experiments/{key}/metrics/{variant_key}`

Get aggregated metrics for a variant.

**Response:**

```json
{
  "variant_key": "treatment",
  "user_count": 150,
  "metrics": {
    "schedule_quality_score": {
      "count": 150,
      "sum": 138.0,
      "mean": 0.92,
      "min": 0.75,
      "max": 0.99
    }
  }
}
```

---

### Get Experiment Results

<span class="endpoint-badge get">GET</span> `/api/experiments/{key}/results`

Get full experiment results with statistical analysis.

**Response:**

```json
{
  "experiment_key": "schedule_optimizer_v2",
  "status": "running",
  "total_users": 300,
  "variant_metrics": [...],
  "is_significant": true,
  "p_value": 0.023,
  "winning_variant": "treatment",
  "recommendation": "Treatment variant shows statistically significant improvement",
  "statistical_power": 0.85
}
```

---

### Get Lifecycle Events

<span class="endpoint-badge get">GET</span> `/api/experiments/{key}/events`

Get experiment lifecycle history.

---

## Statistics

### Get Experiment Stats

<span class="endpoint-badge get">GET</span> `/api/experiments/stats`

Get overall experiment statistics.

**Response:**

```json
{
  "total_experiments": 15,
  "running_experiments": 3,
  "completed_experiments": 10,
  "draft_experiments": 2,
  "total_users_assigned": 5000,
  "total_metrics_tracked": 25000
}
```

---

## Configuration

The experiments module uses Redis for storage. Configure via environment variables:

```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_password
```

### Experiment Config Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `sticky_bucketing` | bool | true | Keep users in same variant across sessions |
| `override_enabled` | bool | true | Allow manual variant assignment |
| `min_sample_size` | int | 100 | Minimum users per variant for valid results |
| `confidence_level` | float | 0.95 | Statistical confidence level (95%) |
