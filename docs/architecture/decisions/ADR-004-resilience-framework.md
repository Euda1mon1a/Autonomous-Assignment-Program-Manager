# ADR-004: Cross-Disciplinary Resilience Framework

**Date:** 2025-12 (Sessions 15-20)
**Status:** Adopted

## Context

Medical residency programs face significant challenges:
- **Burnout epidemic**: 40-60% of residents experience burnout
- **Traditional metrics fail**: Utilization-based metrics miss early warning signs
- **Reactive approach**: Problems detected only after they manifest
- **Cascading failures**: One person's absence can ripple through schedules

Standard scheduling software treats burnout as an individual problem rather than a systemic risk requiring proactive detection.

## Decision

Apply **cross-industry resilience concepts** to medical residency scheduling:

### Five-Tier Framework

| Tier | Concepts | Source Discipline |
|------|----------|-------------------|
| 1 - Core | 80% utilization threshold, N-1/N-2 contingency, defense in depth | Queuing theory, power grids, security |
| 2 - Strategic | Homeostasis, blast radius isolation, Le Chatelier's principle | Biology, AWS, chemistry |
| 3 - Analytics | SPC monitoring, Erlang coverage, SIR epidemiology | Manufacturing, telecom, public health |
| 4 - Observability | OpenTelemetry export, circuit breaker health | Distributed systems |
| 5 - Exotic Frontier | Metastability, spin glass, circadian PRC | Statistical mechanics, chronobiology |

### Key Metrics

```python
# Core thresholds
MAX_UTILIZATION = 0.80  # 80% target prevents cascade failures
DEFENSE_LEVELS = ["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"]

# Epidemiological metrics
burnout_rt: float  # Reproduction number (>1 = spreading)
sir_state: dict    # Susceptible, Infected, Recovered counts

# Statistical process control
western_electric_violations: list  # Control chart rule violations
cp_index: float    # Process capability (target: >1.33)
```

## Consequences

### Positive
- **Early warning system**: Detect burnout precursors before manifestation
- **Evidence-based thresholds**: Queuing theory provides mathematical foundation
- **Multi-scale detection**: Different algorithms catch different patterns
- **Proactive intervention**: Act on leading indicators, not lagging symptoms
- **Cross-disciplinary insights**: Leverage proven concepts from other fields

### Negative
- **Complexity**: Requires cross-disciplinary expertise to maintain
- **Computational cost**: Resilience checks run every 15 minutes
- **Learning curve**: Unfamiliar concepts for medical schedulers
- **False positives**: Sensitive detection may trigger unnecessary alerts
- **Calibration effort**: Thresholds must be tuned per institution

## Implementation

### Resilience Hub Architecture
```
┌──────────────────────────────────────────────────────────────┐
│                    Resilience Hub                            │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Utilization │  │ Contingency │  │ Defense in Depth   │   │
│  │  Monitor    │  │  Analyzer   │  │    Evaluator       │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ SPC Charts  │  │ SIR Model   │  │  Burnout Rt        │   │
│  │ (Western    │  │ (Epidemic   │  │   Calculator       │   │
│  │  Electric)  │  │  Spread)    │  │                    │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐   │
│  │ Fire Index  │  │ Creep/      │  │  Seismic           │   │
│  │ (Burnout    │  │ Fatigue     │  │    STA/LTA         │   │
│  │  Danger)    │  │ (Materials) │  │                    │   │
│  └─────────────┘  └─────────────┘  └─────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Defense Levels
```python
class DefenseLevel(Enum):
    GREEN = "normal"      # Normal operations
    YELLOW = "caution"    # Elevated monitoring
    ORANGE = "elevated"   # Active intervention
    RED = "high"          # Emergency protocols
    BLACK = "critical"    # System failure imminent
```

### Celery Background Tasks
```python
# Run every 15 minutes
@celery_app.task
def check_resilience_health():
    """Periodic resilience health check."""
    hub = ResilienceHub()
    result = hub.compute_unified_health()
    if result.defense_level >= DefenseLevel.ORANGE:
        send_resilience_alert(result)
```

## References

- `docs/architecture/cross-disciplinary-resilience.md` - Detailed concept documentation
- `docs/architecture/EXOTIC_FRONTIER_CONCEPTS.md` - Tier 5 exotic concepts
- `backend/app/resilience/` - Implementation code
- `backend/app/analytics/` - Analytics modules
- `.claude/dontreadme/synthesis/CROSS_DISCIPLINARY_CONCEPTS.md` - LLM reference

## See Also

**Related ADRs:**
- [ADR-002: Constraint Programming](ADR-002-constraint-programming-ortools.md) - Solver used for fallback schedules
- [ADR-009: Time Crystal Scheduling](ADR-009-time-crystal-scheduling.md) - Stability concepts complement resilience

**Implementation Code:**
- `backend/app/resilience/hub.py` - Resilience hub orchestrator
- `backend/app/resilience/utilization.py` - 80% utilization threshold enforcement
- `backend/app/resilience/contingency.py` - N-1/N-2 contingency analysis
- `backend/app/resilience/defense_levels.py` - Defense in depth implementation
- `backend/app/analytics/burnout/` - SIR model and Rt calculation
- `backend/app/analytics/spc/` - Statistical process control
- `backend/app/analytics/erlang.py` - Erlang C queuing model

**Architecture Documentation:**
- [Cross-Disciplinary Resilience](../cross-disciplinary-resilience.md) - Full framework documentation
- [Exotic Frontier Concepts](../EXOTIC_FRONTIER_CONCEPTS.md) - Tier 5 advanced concepts
- [Resilience Defense Level Runbook](../RESILIENCE_DEFENSE_LEVEL_RUNBOOK.md) - Response procedures
- [Resilience Contingency Procedures](../RESILIENCE_CONTINGENCY_PROCEDURES.md) - Emergency protocols
- [Resilience SPC Configuration](../RESILIENCE_SPC_CONFIGURATION.md) - Control chart tuning

**API Documentation:**
- [Resilience API](../../api/RESILIENCE_API.md) - Health monitoring and crisis management endpoints
- [FMIT Health API](../../api/FMIT_HEALTH_API.md) - Coverage monitoring

**Background Tasks:**
- `backend/app/core/celery_app.py` - Periodic resilience health checks (every 15 min)
