# Scheduling Catalyst API

API endpoints for barrier analysis and schedule change optimization.

---

## Overview

The scheduling catalyst API applies chemistry concepts to scheduling:
- **Activation Energy**: Quantified difficulty of schedule changes
- **Barriers**: Obstacles preventing changes (freeze horizons, credentials, ACGME rules)
- **Catalysts**: Personnel or mechanisms that lower barriers
- **Pathways**: Optimal routes from current to target schedule state

**Base URL:** `/api/scheduling-catalyst`

---

## Barrier Detection

### Detect Barriers

<span class="endpoint-badge post">POST</span> `/api/scheduling-catalyst/barriers/detect`

Detect all barriers for a proposed schedule change.

**Request Body:**

```json
{
  "assignment_id": "uuid-of-assignment",
  "proposed_change": {
    "target_date": "2024-01-20",
    "reaction_type": "swap",
    "target_person_id": "uuid-of-target"
  },
  "reference_date": "2024-01-15"
}
```

**Response:**

```json
{
  "total_barriers": 3,
  "barriers": [
    {
      "barrier_type": "kinetic",
      "name": "Freeze Horizon",
      "description": "Assignment is within 14-day freeze period",
      "energy_contribution": 0.6,
      "is_absolute": false,
      "source": "freeze_horizon"
    },
    {
      "barrier_type": "regulatory",
      "name": "ACGME Hours",
      "description": "Would exceed 80-hour weekly limit",
      "energy_contribution": 0.8,
      "is_absolute": true,
      "source": "acgme_hours"
    }
  ],
  "activation_energy": {
    "value": 0.75,
    "components": {
      "kinetic": 0.3,
      "regulatory": 0.4,
      "thermodynamic": 0.05
    },
    "is_feasible": true,
    "effective_energy": 0.75
  },
  "has_absolute_barriers": true,
  "summary": "Found 3 barriers including 1 absolute barrier"
}
```

### Barrier Types

| Type | Description | Examples |
|------|-------------|----------|
| `kinetic` | Time-based barriers | Freeze horizons, notice periods |
| `thermodynamic` | Equilibrium barriers | Workload balance, preferences |
| `steric` | Structural barriers | Credential requirements |
| `electronic` | Authorization barriers | Role permissions, approvals |
| `regulatory` | Compliance barriers | ACGME rules, legal requirements |

---

## Pathway Optimization

### Optimize Pathway

<span class="endpoint-badge post">POST</span> `/api/scheduling-catalyst/pathways/optimize`

Find the optimal transition pathway for a schedule change.

**Request Body:**

```json
{
  "assignment_id": "uuid-of-assignment",
  "proposed_change": {
    "target_date": "2024-01-20",
    "target_person_id": "uuid-of-target"
  },
  "energy_threshold": 0.8,
  "prefer_mechanisms": true,
  "allow_multi_step": true
}
```

**Response:**

```json
{
  "success": true,
  "pathway": {
    "pathway_id": "path-123",
    "total_energy": 0.75,
    "catalyzed_energy": 0.45,
    "transition_states": [
      {
        "state_id": "state-1",
        "description": "Coordinator approval obtained",
        "energy": 0.5,
        "is_stable": true
      }
    ],
    "catalysts_used": ["coordinator_approval", "auto_matcher"],
    "success_probability": 0.85
  },
  "alternative_pathways": [],
  "blocking_barriers": [],
  "recommendations": [
    "Request coordinator approval to reduce freeze horizon barrier"
  ]
}
```

---

## Swap Analysis

### Analyze Swap Barriers

<span class="endpoint-badge post">POST</span> `/api/scheduling-catalyst/swaps/analyze`

Specialized analysis for swap operations.

**Request Body:**

```json
{
  "source_faculty_id": "uuid-source",
  "source_week": "2024-01-15",
  "target_faculty_id": "uuid-target",
  "target_week": "2024-01-22",
  "swap_type": "one_to_one"
}
```

**Response:**

```json
{
  "swap_feasible": true,
  "barriers": [...],
  "activation_energy": {
    "value": 0.45,
    "is_feasible": true
  },
  "catalyst_recommendations": [
    {
      "barrier": {...},
      "recommended_catalyst": "coordinator_approval",
      "confidence": 0.9
    }
  ],
  "blocking_barriers": [],
  "recommendations": [
    "Swap is feasible with current parameters"
  ]
}
```

---

## Catalyst Management

### Get Catalyst Capacity

<span class="endpoint-badge get">GET</span> `/api/scheduling-catalyst/capacity`

Get current system catalyst capacity.

**Requires:** Admin privileges

**Response:**

```json
{
  "person_catalysts_available": 5,
  "mechanism_catalysts_available": 8,
  "total_capacity": 4.2,
  "bottleneck_catalysts": [
    "coordinator_smith"
  ],
  "recommendations": [
    "Consider cross-training more coordinators"
  ]
}
```

### Catalyst Types

| Type | Description | Examples |
|------|-------------|----------|
| `homogeneous` | Personnel catalysts | Coordinators, hub faculty |
| `heterogeneous` | System catalysts | Auto-matcher, override codes |
| `enzymatic` | Role-specific | Credential-based permissions |
| `autocatalytic` | Self-reinforcing | Cross-training cascades |

---

## Batch Operations

### Batch Optimize

<span class="endpoint-badge post">POST</span> `/api/scheduling-catalyst/batch/optimize`

Optimize multiple schedule changes as a batch.

**Requires:** Admin privileges

**Request Body:**

```json
{
  "changes": [
    {
      "assignment_id": "uuid-1",
      "proposed_change": {"target_date": "2024-01-20"},
      "energy_threshold": 0.8
    },
    {
      "assignment_id": "uuid-2",
      "proposed_change": {"target_date": "2024-01-21"},
      "energy_threshold": 0.8
    }
  ],
  "find_optimal_order": true
}
```

**Response:**

```json
{
  "total_changes": 2,
  "successful_pathways": 2,
  "optimal_order": [1, 0],
  "results": [...],
  "aggregate_energy": 1.2,
  "catalyst_conflicts": []
}
```

---

## Integration with Swap Workflow

The scheduling catalyst module integrates with the swap validation service:

```python
from app.scheduling_catalyst import TransitionOptimizer

# In swap validation
optimizer = TransitionOptimizer(db)
result = await optimizer.optimize_swap(
    requester_id=source_faculty_id,
    target_id=target_faculty_id,
    assignment_id=assignment_id
)

if not result.success:
    # Return barrier information to user
    return {
        "valid": False,
        "barriers": result.blocking_barriers,
        "recommendations": result.recommendations
    }
```

---

## Chemistry Concept Mapping

| Chemistry Concept | Scheduling Equivalent |
|-------------------|----------------------|
| Activation Energy (Ea) | Difficulty of schedule change (0.0-1.0) |
| Catalyst | Personnel/mechanism that lowers barriers |
| Transition State | Intermediate schedule configuration |
| Reaction Pathway | Sequence of steps to achieve change |
| Absolute Barrier | Immutable constraint (e.g., ACGME violation) |
