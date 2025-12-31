# Exotic Resilience API Documentation

**Tier 5: Exotic Frontier Concepts**

Advanced resilience analytics using cutting-edge cross-disciplinary concepts from physics, mathematics, and complex systems theory.

## Overview

The Exotic Resilience API exposes three advanced analytical modules:

1. **Metastability Detection** (Statistical Mechanics) - Detect when systems are trapped in local optima
2. **Spin Glass Model** (Condensed Matter Physics) - Generate diverse schedule replicas for frustrated constraints
3. **Catastrophe Theory** (Dynamical Systems) - Predict sudden failures from gradual parameter changes

All endpoints are prefixed with: `/api/v1/resilience/exotic/exotic/`

## Authentication

All endpoints require authentication via JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 1. Metastability Detection

Detect metastable states where a system is trapped in a local energy minimum (locally optimal but globally suboptimal).

#### `POST /exotic/metastability`

**Use Cases:**
- Solver trapped in suboptimal schedule
- Organization stuck in inefficient pattern
- Risk assessment for sudden reorganizations

**Request Body:**

```json
{
  "current_energy": 2.0,
  "energy_landscape": [1.0, 2.0, 3.0, 1.5],
  "barrier_samples": [0.5, 0.8, 0.3],
  "temperature": 1.0
}
```

**Parameters:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `current_energy` | float | Yes | - | Current state energy level (lower = better) |
| `energy_landscape` | array[float] | Yes | - | Energies of sampled nearby states |
| `barrier_samples` | array[float] | Yes | - | Energy barriers to reach nearby states |
| `temperature` | float | No | 0.1-10.0 | System temperature (default: 1.0) |

**Response:**

```json
{
  "energy": 2.0,
  "barrier_height": 0.5,
  "escape_rate": 0.606,
  "lifetime": 1.65,
  "is_metastable": true,
  "stability_score": 0.05,
  "nearest_stable_state": 1.0,
  "risk_level": "moderate",
  "recommendations": [
    "System trapped in local minimum (barrier height: 0.50)",
    "More stable state exists at energy 1.00",
    "High escape probability: 0.606 per time unit",
    "Consider proactive reorganization before spontaneous transition"
  ],
  "source": "backend"
}
```

**Risk Levels:**
- `low` - Barrier height > 2.0 (stable metastable state)
- `moderate` - Barrier height 1.0-2.0
- `high` - Barrier height 0.5-1.0
- `critical` - Barrier height < 0.5 (imminent escape)

**Theory:**

Uses Kramers escape rate theory from statistical mechanics:

```
k_escape = ω₀ * exp(-ΔE / kT)
lifetime = 1 / k_escape
```

Where:
- `ΔE` = barrier height
- `k` = Boltzmann constant (normalized to 1)
- `T` = temperature
- `ω₀` = attempt frequency (normalized to 1)

---

### 2. Reorganization Risk Prediction

Predict risk of sudden system reorganization due to external perturbations.

#### `POST /exotic/reorganization-risk`

**Use Cases:**
- Assess mass resignation risk
- Predict morale collapse
- Evaluate stress impact on stability

**Request Body:**

```json
{
  "current_stability": 0.7,
  "external_perturbation": 0.3,
  "system_temperature": 1.5
}
```

**Parameters:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `current_stability` | float | Yes | 0.0-1.0 | Current system stability score |
| `external_perturbation` | float | Yes | ≥ 0.0 | Magnitude of external stress |
| `system_temperature` | float | No | 0.1-10.0 | System agitation level (default: 1.0) |

**Response:**

```json
{
  "risk_level": "moderate",
  "risk_score": 0.5,
  "interpretation": "Moderate reorganization risk",
  "effective_barrier": 0.4,
  "estimated_time_to_reorganization": 0.67,
  "recommendations": [
    "Monitor stability trends",
    "Prepare contingency plans",
    "Maintain current stress reduction efforts"
  ],
  "source": "backend"
}
```

**Risk Levels:**
- `low` - Effective barrier > 0.5
- `moderate` - Effective barrier 0.2-0.5
- `high` - Effective barrier 0.05-0.2
- `critical` - Effective barrier ≤ 0 (immediate risk)

**Effective Barrier:**

```
effective_barrier = current_stability - external_perturbation
```

When effective barrier ≤ 0, reorganization is imminent.

---

### 3. Spin Glass Replica Generation

Generate diverse schedule replicas using frustrated constraint physics.

#### `POST /exotic/spin-glass`

**Use Cases:**
- Generate multiple equally-good but different schedules
- Explore solution space diversity
- Understand constraint frustration
- Ensemble averaging for robustness

**Request Body:**

```json
{
  "num_spins": 100,
  "num_replicas": 5,
  "temperature": 1.0,
  "frustration_level": 0.3,
  "num_iterations": 1000
}
```

**Parameters:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `num_spins` | int | No | 10-1000 | Number of binary variables (default: 100) |
| `num_replicas` | int | No | 1-20 | Number of replicas to generate (default: 5) |
| `temperature` | float | No | 0.1-10.0 | Sampling temperature (default: 1.0) |
| `frustration_level` | float | No | 0.0-1.0 | Degree of conflicting constraints (default: 0.3) |
| `num_iterations` | int | No | 100-10000 | Monte Carlo iterations per replica (default: 1000) |

**Response:**

```json
{
  "configurations": [
    {
      "energy": -45.2,
      "frustration": 0.28,
      "magnetization": 0.02,
      "overlap": 0.15
    },
    {
      "energy": -44.8,
      "frustration": 0.31,
      "magnetization": -0.04,
      "overlap": 0.12
    }
  ],
  "mean_energy": -45.0,
  "energy_std": 0.3,
  "mean_overlap": 0.13,
  "diversity_score": 0.87,
  "landscape_ruggedness": 0.42,
  "difficulty": "moderate",
  "source": "backend"
}
```

**Configuration Metrics:**

- `energy` - Schedule quality (lower = better). Range: -∞ to +∞
- `frustration` - Fraction of unsatisfied constraints. Range: 0.0-1.0
- `magnetization` - Overall bias (should be ~0 for balanced). Range: -1.0 to 1.0
- `overlap` - Similarity to reference configuration. Range: -1.0 to 1.0

**Ensemble Metrics:**

- `diversity_score` - 1 - mean_overlap (higher = more diverse). Range: 0.0-1.0
- `landscape_ruggedness` - Difficulty of optimization. Range: 0.0-1.0
- `difficulty` - `easy`, `moderate`, `hard`, `very_hard`

**Theory:**

Uses Edwards-Anderson spin glass model with simulated annealing:

```
E = -Σᵢⱼ Jᵢⱼ sᵢ sⱼ
```

Where:
- `Jᵢⱼ` = coupling matrix (randomly frustrated)
- `sᵢ` = spin state (+1 or -1)
- Frustration created by random sign flips in coupling matrix

---

### 4. Catastrophe Prediction

Predict sudden system failures using catastrophe theory (cusp catastrophe model).

#### `POST /exotic/catastrophe`

**Use Cases:**
- Predict sudden morale collapses from gradual stress
- Identify bifurcation points (tipping points)
- Model hysteresis effects
- Early warning for phase transitions

**Request Body:**

```json
{
  "current_a": 1.0,
  "current_b": 0.5,
  "da": -2.0,
  "db": 0.5,
  "num_steps": 100
}
```

**Parameters:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `current_a` | float | Yes | - | Current asymmetry parameter (splitting factor) |
| `current_b` | float | Yes | - | Current bias parameter (normal factor) |
| `da` | float | Yes | - | Change in asymmetry parameter |
| `db` | float | Yes | - | Change in bias parameter |
| `num_steps` | int | No | 10-1000 | Number of simulation steps (default: 100) |

**Response:**

```json
{
  "catastrophe_detected": true,
  "catastrophe_point": {
    "a_critical": -0.5,
    "b_critical": 0.3,
    "x_before": 1.2,
    "x_after": -0.8,
    "jump_magnitude": 2.0,
    "hysteresis_width": 0.15
  },
  "resilience_score": 0.35,
  "status": "vulnerable",
  "is_safe": false,
  "distance_to_catastrophe": 0.15,
  "current_distance_to_bifurcation": 1.73,
  "warning": "Catastrophe predicted at a=-0.50, b=0.30",
  "recommendations": [
    "System vulnerable to catastrophic transition",
    "Monitor stress parameters closely",
    "Plan contingency responses"
  ],
  "source": "backend"
}
```

**Status Levels:**
- `robust` - Resilience score > 0.8
- `stable` - Resilience score 0.5-0.8
- `vulnerable` - Resilience score 0.2-0.5
- `critical` - Resilience score < 0.2

**Catastrophe Point:**

When detected, describes the discontinuous jump:
- `a_critical`, `b_critical` - Parameter values where jump occurs
- `x_before` - System state before jump
- `x_after` - System state after jump
- `jump_magnitude` - Size of discontinuous transition
- `hysteresis_width` - Width of bistable region

**Theory:**

Uses cusp catastrophe potential:

```
V(x; a, b) = x⁴/4 + ax²/2 + bx
```

Equilibria satisfy:
```
dV/dx = 0  =>  x³ + ax + b = 0
```

Bifurcation set (catastrophe boundary):
```
a³ + 27b² = 0
```

System exhibits:
- **Sudden jumps** when crossing bifurcation set
- **Hysteresis** (forward/backward paths differ)
- **Divergence** (small parameter changes cause large state changes)

---

## Response Format

All endpoints return JSON with:

```json
{
  "...response-specific-fields...",
  "source": "backend"
}
```

The `source` field indicates the data comes from real backend calculations (not MCP placeholder data).

## Error Handling

### 422 Unprocessable Entity

Validation errors return detailed Pydantic error messages:

```json
{
  "detail": [
    {
      "loc": ["body", "temperature"],
      "msg": "ensure this value is greater than or equal to 0.1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

### 500 Internal Server Error

Calculation errors are caught and logged server-side. Generic error message returned to client:

```json
{
  "detail": "Internal server error during exotic analysis"
}
```

## Rate Limiting

Exotic endpoints are computationally intensive and subject to rate limiting:

- **Spin Glass**: Max 10 requests/minute per user
- **Metastability**: Max 30 requests/minute per user
- **Catastrophe**: Max 30 requests/minute per user

Rate limit headers included in response:

```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 28
X-RateLimit-Reset: 1640995200
```

## Example Usage

### Python (httpx)

```python
import httpx

client = httpx.AsyncClient(base_url="https://api.scheduler.example.com")

# Detect metastability
response = await client.post(
    "/api/v1/resilience/exotic/exotic/metastability",
    json={
        "current_energy": 2.0,
        "energy_landscape": [1.0, 2.0, 3.0],
        "barrier_samples": [0.5, 0.8],
        "temperature": 1.0,
    },
    headers={"Authorization": f"Bearer {token}"},
)

result = response.json()
if result["is_metastable"]:
    print(f"System trapped! Barrier height: {result['barrier_height']}")
    print(f"Recommendations: {result['recommendations']}")
```

### JavaScript (fetch)

```javascript
const response = await fetch(
  'https://api.scheduler.example.com/api/v1/resilience/exotic/exotic/spin-glass',
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      num_spins: 50,
      num_replicas: 5,
      temperature: 1.0,
      frustration_level: 0.3,
      num_iterations: 1000,
    }),
  }
);

const result = await response.json();
console.log(`Generated ${result.configurations.length} diverse replicas`);
console.log(`Diversity score: ${result.diversity_score}`);
```

### cURL

```bash
curl -X POST "https://api.scheduler.example.com/api/v1/resilience/exotic/exotic/catastrophe" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_a": 1.0,
    "current_b": 0.5,
    "da": -2.0,
    "db": 0.5,
    "num_steps": 100
  }'
```

## Performance Considerations

### Computational Complexity

| Endpoint | Complexity | Typical Runtime |
|----------|------------|-----------------|
| Metastability | O(N) | < 100ms |
| Reorganization Risk | O(1) | < 10ms |
| Spin Glass | O(N × M × I) | 1-10s |
| Catastrophe | O(S × R) | < 500ms |

Where:
- N = number of landscape samples
- M = number of replicas
- I = iterations per replica
- S = simulation steps
- R = root-finding complexity

### Optimization Tips

1. **Spin Glass**: Start with fewer replicas (3-5) and lower iterations (500-1000) for exploratory analysis
2. **Metastability**: Pre-sample energy landscape offline to reduce request payload
3. **Catastrophe**: Use adaptive step sizing (fewer steps for initial exploration)
4. **Batch Processing**: For bulk analysis, use async/parallel requests

## Scientific References

1. **Metastability**: Kramers, H. A. (1940). "Brownian motion in a field of force and the diffusion model of chemical reactions." *Physica* 7(4): 284-304.

2. **Spin Glass**: Edwards, S. F.; Anderson, P. W. (1975). "Theory of spin glasses." *Journal of Physics F: Metal Physics* 5(5): 965.

3. **Catastrophe Theory**: Thom, R. (1972). *Structural Stability and Morphogenesis*. Benjamin-Addison Wesley.

4. **Critical Phenomena**: Scheffer, M. et al. (2009). "Early-warning signals for critical transitions." *Nature* 461: 53-59.

## Related Endpoints

- [Thermodynamics API](./THERMODYNAMICS_API.md) - Entropy, phase transitions, free energy
- [Immune System API](./IMMUNE_API.md) - Anomaly detection, antibody selection
- [Time Crystal API](./TIME_CRYSTAL_API.md) - Rigidity, subharmonics, checkpoints
- [Resilience API](./RESILIENCE_API.md) - Core resilience metrics

## Support

For questions or issues:
- **Documentation**: [docs.scheduler.example.com](https://docs.scheduler.example.com)
- **GitHub Issues**: [github.com/your-org/scheduler/issues](https://github.com/your-org/scheduler/issues)
- **Email**: support@scheduler.example.com

---

**Last Updated**: 2025-12-31
**API Version**: v1
**Status**: Production
