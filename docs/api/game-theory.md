# Game Theory API Endpoints

Game theory analysis endpoints for testing resilience configurations using Axelrod's Prisoner's Dilemma framework.

---

## Overview

The Game Theory API enables empirical testing of scheduling and resilience configurations by treating them as competing strategies in iterated games. Based on Robert Axelrod's famous computer tournaments, this system helps identify optimal configurations that are robust and evolutionarily stable.

**Base URL**: `/api/v1/game-theory`

---

## Strategies

### List Strategies

<span class="endpoint-badge get">GET</span> `/api/v1/game-theory/strategies`

Retrieve all defined configuration strategies.

#### Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `strategy_type` | string | Filter by type: `cooperative`, `aggressive`, `tit_for_tat`, `grudger`, `random`, `custom` |
| `skip` | integer | Pagination offset (default: 0) |
| `limit` | integer | Pagination limit (default: 100) |

#### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Conservative Config",
      "strategy_type": "cooperative",
      "description": "Always cooperates, leaves 30% buffer",
      "utilization_target": 0.70,
      "cross_zone_borrowing": true,
      "sacrifice_willingness": "high",
      "response_timeout_ms": 5000,
      "is_active": true,
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 5
}
```

---

### Create Strategy

<span class="endpoint-badge post">POST</span> `/api/v1/game-theory/strategies`

Create a new configuration strategy for tournament testing.

#### Request

```json
{
  "name": "Adaptive TFT Config",
  "strategy_type": "tit_for_tat",
  "description": "Mirrors opponent behavior, starts cooperatively",
  "utilization_target": 0.80,
  "cross_zone_borrowing": true,
  "sacrifice_willingness": "medium",
  "response_timeout_ms": 3000,
  "custom_logic": null
}
```

#### Response

```json
{
  "id": "uuid",
  "name": "Adaptive TFT Config",
  "strategy_type": "tit_for_tat",
  "description": "Mirrors opponent behavior, starts cooperatively",
  "utilization_target": 0.80,
  "cross_zone_borrowing": true,
  "sacrifice_willingness": "medium",
  "response_timeout_ms": 3000,
  "is_active": true,
  "created_at": "2025-01-15T10:00:00Z"
}
```

---

### Get Strategy

<span class="endpoint-badge get">GET</span> `/api/v1/game-theory/strategies/{strategy_id}`

Retrieve a specific strategy by ID.

---

### Update Strategy

<span class="endpoint-badge patch">PATCH</span> `/api/v1/game-theory/strategies/{strategy_id}`

Update an existing strategy.

#### Request

```json
{
  "utilization_target": 0.75,
  "description": "Updated description"
}
```

---

## Tournaments

### List Tournaments

<span class="endpoint-badge get">GET</span> `/api/v1/game-theory/tournaments`

Retrieve all tournament runs.

#### Query Parameters

| Name | Type | Description |
|------|------|-------------|
| `status` | string | Filter by status: `pending`, `running`, `completed`, `failed` |
| `skip` | integer | Pagination offset |
| `limit` | integer | Pagination limit |

#### Response

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Q1 Config Tournament",
      "status": "completed",
      "turns_per_match": 200,
      "repetitions": 50,
      "noise": 0.0,
      "strategy_count": 6,
      "started_at": "2025-01-15T10:00:00Z",
      "completed_at": "2025-01-15T10:05:00Z"
    }
  ],
  "total": 3
}
```

---

### Create Tournament

<span class="endpoint-badge post">POST</span> `/api/v1/game-theory/tournaments`

Create and start a new round-robin tournament.

#### Request

```json
{
  "name": "Resilience Config Tournament",
  "strategy_ids": [
    "uuid-1",
    "uuid-2",
    "uuid-3"
  ],
  "turns_per_match": 200,
  "repetitions": 50,
  "noise": 0.01
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Tournament name |
| `strategy_ids` | array | List of strategy UUIDs to include |
| `turns_per_match` | integer | Number of rounds per matchup (default: 200) |
| `repetitions` | integer | Number of times to repeat each matchup (default: 10) |
| `noise` | float | Probability of random action [0-1] (default: 0.0) |

#### Response

```json
{
  "id": "uuid",
  "name": "Resilience Config Tournament",
  "status": "pending",
  "turns_per_match": 200,
  "repetitions": 50,
  "noise": 0.01,
  "strategy_count": 3,
  "started_at": null,
  "message": "Tournament queued for execution"
}
```

---

### Get Tournament Results

<span class="endpoint-badge get">GET</span> `/api/v1/game-theory/tournaments/{tournament_id}/results`

Retrieve detailed results for a completed tournament.

#### Response

```json
{
  "tournament_id": "uuid",
  "name": "Resilience Config Tournament",
  "status": "completed",
  "rankings": [
    {
      "rank": 1,
      "strategy_id": "uuid",
      "strategy_name": "TFT Config",
      "total_score": 15234,
      "average_score": 2.87,
      "cooperation_rate": 0.89,
      "wins": 45,
      "losses": 5,
      "draws": 0
    },
    {
      "rank": 2,
      "strategy_id": "uuid",
      "strategy_name": "Cooperative Config",
      "total_score": 14100,
      "average_score": 2.65,
      "cooperation_rate": 1.0,
      "wins": 38,
      "losses": 12,
      "draws": 0
    }
  ],
  "payoff_matrix": {
    "TFT Config": {
      "TFT Config": 3.0,
      "Cooperative Config": 3.0,
      "Aggressive Config": 1.5
    },
    "Cooperative Config": {
      "TFT Config": 3.0,
      "Cooperative Config": 3.0,
      "Aggressive Config": 0.5
    },
    "Aggressive Config": {
      "TFT Config": 1.5,
      "Cooperative Config": 4.5,
      "Aggressive Config": 1.0
    }
  },
  "matches": [
    {
      "player1": "TFT Config",
      "player2": "Aggressive Config",
      "player1_score": 150,
      "player2_score": 145,
      "player1_cooperation_rate": 0.45,
      "player2_cooperation_rate": 0.0
    }
  ],
  "execution_time_ms": 5000,
  "completed_at": "2025-01-15T10:05:00Z"
}
```

---

## Evolution Simulations

### List Evolution Simulations

<span class="endpoint-badge get">GET</span> `/api/v1/game-theory/evolution`

Retrieve all evolution simulation runs.

---

### Create Evolution Simulation

<span class="endpoint-badge post">POST</span> `/api/v1/game-theory/evolution`

Start a Moran process evolutionary simulation.

#### Request

```json
{
  "name": "80% Rule Stability Test",
  "strategy_ids": [
    "uuid-1",
    "uuid-2",
    "uuid-3"
  ],
  "population_size": 100,
  "max_generations": 500,
  "turns_per_interaction": 100,
  "mutation_rate": 0.01
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Simulation name |
| `strategy_ids` | array | Initial strategy types in population |
| `population_size` | integer | Total population size (default: 100) |
| `max_generations` | integer | Max generations to run (default: 500) |
| `turns_per_interaction` | integer | Turns per pairwise interaction |
| `mutation_rate` | float | Probability of random mutation [0-1] |

#### Response

```json
{
  "id": "uuid",
  "name": "80% Rule Stability Test",
  "status": "running",
  "population_size": 100,
  "max_generations": 500,
  "current_generation": 0,
  "message": "Evolution simulation started"
}
```

---

### Get Evolution Results

<span class="endpoint-badge get">GET</span> `/api/v1/game-theory/evolution/{simulation_id}/results`

Retrieve results for a completed evolution simulation.

#### Response

```json
{
  "simulation_id": "uuid",
  "name": "80% Rule Stability Test",
  "status": "completed",
  "winner": {
    "strategy_id": "uuid",
    "strategy_name": "TFT Config",
    "final_population": 100,
    "percentage": 1.0
  },
  "generations_to_fixation": 234,
  "is_evolutionarily_stable": true,
  "population_history": [
    {
      "generation": 0,
      "populations": {
        "TFT Config": 34,
        "Cooperative Config": 33,
        "Aggressive Config": 33
      }
    },
    {
      "generation": 50,
      "populations": {
        "TFT Config": 45,
        "Cooperative Config": 40,
        "Aggressive Config": 15
      }
    },
    {
      "generation": 234,
      "populations": {
        "TFT Config": 100,
        "Cooperative Config": 0,
        "Aggressive Config": 0
      }
    }
  ],
  "execution_time_ms": 15000,
  "completed_at": "2025-01-15T10:10:00Z"
}
```

---

## Validation

### Validate Strategy Against TFT

<span class="endpoint-badge post">POST</span> `/api/v1/game-theory/validate`

Test a configuration against Tit for Tat benchmark validator.

#### Request

```json
{
  "strategy_id": "uuid",
  "rounds": 100
}
```

Or validate by config parameters:

```json
{
  "config": {
    "utilization_target": 0.85,
    "cross_zone_borrowing": true,
    "sacrifice_willingness": "medium"
  },
  "rounds": 100
}
```

#### Response

```json
{
  "passed": true,
  "average_score": 2.75,
  "cooperation_rate": 0.85,
  "mutual_cooperation_rate": 0.80,
  "recommendation": "cooperative",
  "details": {
    "score_vs_tft": 275,
    "tft_score": 275,
    "rounds_played": 100,
    "first_defection": null,
    "defection_count": 15
  },
  "assessment": "Configuration is cooperative and performs well against TFT. Suitable for production use."
}
```

---

## Analysis

### Analyze Current Configuration

<span class="endpoint-badge post">POST</span> `/api/v1/game-theory/analyze`

Analyze the current resilience configuration using game theory.

#### Request

```json
{}
```

#### Response

```json
{
  "current_config": {
    "utilization_target": 0.80,
    "cross_zone_borrowing": true,
    "sacrifice_willingness": "medium"
  },
  "strategy_classification": "tit_for_tat",
  "matchup_results": {
    "Cooperator": {
      "score": 300,
      "cooperation_rate": 1.0,
      "outcome": "mutual_cooperation"
    },
    "Defector": {
      "score": 145,
      "cooperation_rate": 0.01,
      "outcome": "retaliation"
    },
    "Tit For Tat": {
      "score": 299,
      "cooperation_rate": 0.99,
      "outcome": "mutual_cooperation"
    },
    "Random": {
      "score": 225,
      "cooperation_rate": 0.52,
      "outcome": "mixed"
    }
  },
  "overall_assessment": {
    "average_score": 2.42,
    "exploitation_resistance": 0.85,
    "cooperation_tendency": 0.63,
    "is_production_ready": true
  },
  "recommendations": [
    "Configuration exhibits TFT-like behavior which is optimal for shared environments",
    "High exploitation resistance protects against aggressive neighbors",
    "Consider enabling cross-zone borrowing for additional resilience"
  ]
}
```

---

### Get Summary Statistics

<span class="endpoint-badge get">GET</span> `/api/v1/game-theory/summary`

Get aggregate statistics across all tournaments and simulations.

#### Response

```json
{
  "total_strategies": 8,
  "total_tournaments": 15,
  "total_evolutions": 5,
  "tournaments_completed": 14,
  "evolutions_completed": 4,
  "most_successful_strategy": {
    "id": "uuid",
    "name": "TFT Config",
    "win_rate": 0.85,
    "avg_score": 2.87
  },
  "evolutionarily_stable_strategies": [
    "TFT Config",
    "Grudger Config"
  ],
  "strategy_type_distribution": {
    "tit_for_tat": 3,
    "cooperative": 2,
    "aggressive": 1,
    "grudger": 1,
    "custom": 1
  }
}
```

---

## Error Responses

### Common Errors

| Code | Description |
|------|-------------|
| `400` | Invalid request parameters |
| `404` | Strategy, tournament, or simulation not found |
| `409` | Conflict (e.g., tournament already running) |
| `422` | Validation error (e.g., invalid strategy type) |

### Example Error Response

```json
{
  "detail": "Strategy with ID 'uuid' not found",
  "code": "STRATEGY_NOT_FOUND"
}
```

---

## Webhooks

When configured, the system can send webhook notifications for:

- Tournament completion
- Evolution simulation completion
- Validation results

See [Webhooks Configuration](../admin-manual/webhooks.md) for setup instructions.
