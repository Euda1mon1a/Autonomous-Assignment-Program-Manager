# Volatility → Circuit Breaker Bridge Specification

> **Bridge Purpose**: Pre-emptively open circuit breakers when volatility signals system instability, BEFORE errors occur.
>
> **Status**: Design Specification (Implementation Ready)
>
> **Last Updated**: 2025-12-26

---

## Table of Contents

1. [Overview](#overview)
2. [Mathematical Foundation](#mathematical-foundation)
3. [Data Flow Diagram](#data-flow-diagram)
4. [Implementation Specification](#implementation-specification)
5. [Configuration](#configuration)
6. [Zone Isolation](#zone-isolation)
7. [Test Cases](#test-cases)
8. [Integration Points](#integration-points)
9. [Metrics and Monitoring](#metrics-and-monitoring)
10. [Edge Cases and Considerations](#edge-cases-and-considerations)

---

## Overview

### Problem Statement

Traditional circuit breakers are **reactive** — they open after failures occur. By that time, the system may have already:
- Exhausted connection pools
- Triggered cascading timeouts
- Degraded user experience
- Accumulated error logs

**Volatility signals** from homeostasis tracking provide **early warning** of impending instability. This bridge enables **pre-emptive circuit breaking** based on volatility trends, not just error counts.

### Key Insight

**High volatility precedes phase transitions** (bifurcations). By monitoring:
- Coefficient of variation (volatility)
- Oscillation frequency (jitter)
- Rate of change (momentum)
- Distance to critical thresholds

We can detect when a system is about to destabilize and **fail-fast before actual failures**, giving downstream services time to recover gracefully.

### Cross-Disciplinary Foundations

| Discipline | Concept | Application |
|------------|---------|-------------|
| **Control Theory** | Stability margins | Distance-to-criticality thresholds |
| **Seismology** | STA/LTA precursor detection | Sustained vs. transient volatility |
| **Biology** | Homeostasis disruption | Feedback loop instability detection |
| **Electrical Engineering** | Circuit protection | Pre-emptive fail-fast mechanisms |

---

## Mathematical Foundation

### Volatility Metrics

Volatility is assessed using four primary indicators (from `FeedbackLoop.get_volatility_metrics()`):

1. **Volatility** (σ/μ): Coefficient of variation
   ```
   volatility = std_dev(values) / mean(values)
   ```
   - Stable: < 0.1 (10%)
   - Elevated: 0.1 - 0.3
   - Critical: > 0.3

2. **Jitter** (J): Oscillation frequency
   ```
   jitter = direction_changes / (observations - 2)
   ```
   - Stable: < 0.3 (30% of values change direction)
   - High: > 0.5 (rapid oscillation)

3. **Momentum** (M): Normalized rate of change
   ```
   momentum = linear_regression_slope / tolerance_threshold
   ```
   - Neutral: |M| < 0.5
   - Concerning: |M| > 1.0 (changing faster than tolerance)

4. **Distance to Criticality** (D): Normalized margin
   ```
   D = 1 - (|current - target| / critical_threshold)
   ```
   - Safe: D > 0.7 (far from threshold)
   - Danger: D < 0.3 (approaching critical)

### Trip Signal Formula

The circuit breaker trips when volatility exceeds a sustained threshold:

```python
risk_score = (
    volatility * 2.0        # Primary indicator
    + jitter * 1.5          # Amplifies risk
    + (1.0 - distance) * 1.0  # Proximity to threshold
)

trip_condition = (
    risk_score > (baseline_risk * trip_multiplier)
    AND sustained_for >= sustain_duration_seconds
)
```

**Default Thresholds:**
- `baseline_risk` = 0.5 (NORMAL volatility level)
- `trip_multiplier` = 2.0 (trip at 2x baseline)
- `sustain_duration_seconds` = 300 (5 minutes)

**Rationale**: Requiring sustained high volatility (not just spikes) reduces false positives from transient fluctuations.

### Recovery Condition

Circuit breaker transitions from OPEN → HALF_OPEN when:

```python
recovery_condition = (
    risk_score < (baseline_risk * recovery_threshold)
    AND stable_for >= cooldown_period_seconds
)
```

**Default Recovery:**
- `recovery_threshold` = 1.2 (must drop to near-normal)
- `cooldown_period_seconds` = 600 (10 minutes)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Homeostasis Monitor                            │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │ Coverage     │    │ Utilization  │    │ Workload     │        │
│  │ Feedback     │    │ Feedback     │    │ Balance      │        │
│  │ Loop         │    │ Loop         │    │ Loop         │        │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│         │                   │                   │                 │
│         └───────────────────┼───────────────────┘                 │
│                             ▼                                      │
│                  get_volatility_metrics()                          │
│                             │                                      │
│                   ┌─────────▼─────────┐                           │
│                   │ VolatilityMetrics │                           │
│                   │ - volatility      │                           │
│                   │ - jitter          │                           │
│                   │ - momentum        │                           │
│                   │ - distance        │                           │
│                   │ - level (enum)    │                           │
│                   └─────────┬─────────┘                           │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   VolatilityCircuitBridge                           │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │  evaluate_trip_signal(zone_id, metrics)                   │    │
│  │    1. Calculate risk_score from metrics                   │    │
│  │    2. Check if sustained (time series analysis)           │    │
│  │    3. Return TripDecision(should_trip, reason, metadata)  │    │
│  └─────────────────────────┬─────────────────────────────────┘    │
│                            │                                        │
│  ┌─────────────────────────▼─────────────────────────────────┐    │
│  │  evaluate_recovery(zone_id, metrics)                      │    │
│  │    1. Check if volatility has stabilized                  │    │
│  │    2. Verify cooldown period elapsed                      │    │
│  │    3. Return RecoveryDecision(should_recover, reason)     │    │
│  └─────────────────────────┬─────────────────────────────────┘    │
│                            │                                        │
│  ┌─────────────────────────▼─────────────────────────────────┐    │
│  │  State Tracking (per zone)                                │    │
│  │    - risk_score_history: deque[tuple[datetime, float]]    │    │
│  │    - trip_timestamp: datetime | None                      │    │
│  │    - circuit_breaker_ref: CircuitBreaker                  │    │
│  └───────────────────────────────────────────────────────────┘    │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Circuit Breaker Registry                        │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │ Zone: "clinic"   │  │ Zone: "inpatient"│  │ Zone: "emergency"│ │
│  │ State: CLOSED    │  │ State: OPEN      │  │ State: CLOSED    │ │
│  │ Reason: normal   │  │ Reason: volatility│ │ Reason: normal   │ │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘ │
│                                                                     │
│  Actions:                                                           │
│    - pre_emptive_open(zone_id, reason)                             │
│    - allow_half_open(zone_id)                                      │
│    - get_circuit_state(zone_id) -> CircuitState                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Downstream Services                              │
│                                                                     │
│  - Schedule Generation (fails fast if circuit open)                │
│  - Assignment Creation (uses fallback schedule)                    │
│  - Swap Processing (deferred until recovery)                       │
│  - Notification Delivery (alert admins of reduced capacity)        │
└─────────────────────────────────────────────────────────────────────┘
```

### Sequence Diagram: Pre-emptive Trip

```
HomeostasisMonitor    VolatilityBridge    CircuitBreaker    ScheduleService
        │                     │                   │                 │
        │─ check_loops() ────▶│                   │                 │
        │                     │                   │                 │
        │◀─ get_volatility()──│                   │                 │
        │                     │                   │                 │
        │                     │ (risk_score > threshold for 5min)   │
        │                     │                   │                 │
        │                     │─ pre_emptive_open()───────▶         │
        │                     │                   │                 │
        │                     │                   │─ transition_to_open()
        │                     │                   │                 │
        │                     │                   │                 │
        │                     │                   │◀─ create_assignment()
        │                     │                   │                 │
        │                     │                   │─ CircuitOpenError ─▶│
        │                     │                   │                 │
        │                     │                   │                 │─ use_fallback()
```

---

## Implementation Specification

### New Class: `VolatilityCircuitBridge`

**Location**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/bridges/volatility_circuit_bridge.py`

**Estimated LOC**: ~75 lines (core logic)

```python
"""
Volatility-based pre-emptive circuit breaker bridge.

Monitors volatility metrics from homeostasis tracking and pre-emptively
opens circuit breakers BEFORE errors occur when instability is detected.
"""

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.resilience.circuit_breaker.registry import circuit_breaker_registry
from app.resilience.circuit_breaker.states import CircuitState
from app.resilience.homeostasis import VolatilityMetrics, VolatilityLevel

logger = logging.getLogger(__name__)


@dataclass
class VolatilityTripConfig:
    """Configuration for volatility-based circuit tripping."""

    # Trip thresholds
    volatility_multiplier: float = 2.0  # Trip at 2x baseline risk
    sustained_duration_seconds: int = 300  # Must sustain for 5 min

    # Recovery thresholds
    cooldown_period_seconds: int = 600  # 10 min cooldown before half-open
    recovery_volatility_threshold: float = 1.2  # Must drop to near-normal

    # Baseline risk (NORMAL volatility level)
    baseline_risk_score: float = 0.5

    # History tracking
    max_history_size: int = 100


@dataclass
class TripDecision:
    """Decision on whether to trip a circuit breaker."""

    should_trip: bool
    reason: str
    risk_score: float
    sustained_duration: float  # Seconds of sustained high volatility
    metrics: VolatilityMetrics


@dataclass
class RecoveryDecision:
    """Decision on whether to allow recovery."""

    should_recover: bool
    reason: str
    current_risk_score: float
    time_since_trip: float  # Seconds since circuit opened


@dataclass
class ZoneState:
    """Per-zone state tracking."""

    zone_id: str
    risk_score_history: deque  # deque[tuple[datetime, float]]
    trip_timestamp: Optional[datetime] = None
    last_check_timestamp: Optional[datetime] = None


class VolatilityCircuitBridge:
    """
    Bridge between homeostasis volatility tracking and circuit breakers.

    Pre-emptively opens circuit breakers when sustained volatility indicates
    approaching instability, preventing cascading failures before they occur.
    """

    def __init__(self, config: Optional[VolatilityTripConfig] = None):
        """
        Initialize the volatility circuit bridge.

        Args:
            config: Configuration for trip/recovery behavior
        """
        self.config = config or VolatilityTripConfig()
        self.zone_states: Dict[str, ZoneState] = {}

        logger.info(
            f"VolatilityCircuitBridge initialized: "
            f"trip_multiplier={self.config.volatility_multiplier}, "
            f"sustain={self.config.sustained_duration_seconds}s"
        )

    def evaluate_trip_signal(
        self,
        zone_id: str,
        metrics: VolatilityMetrics
    ) -> TripDecision:
        """
        Evaluate whether to pre-emptively trip circuit breaker.

        Args:
            zone_id: Scheduling zone identifier
            metrics: Current volatility metrics for the zone

        Returns:
            TripDecision with recommendation and reasoning
        """
        # Calculate current risk score
        risk_score = self._calculate_risk_score(metrics)

        # Get or create zone state
        if zone_id not in self.zone_states:
            self.zone_states[zone_id] = ZoneState(
                zone_id=zone_id,
                risk_score_history=deque(maxlen=self.config.max_history_size)
            )

        zone_state = self.zone_states[zone_id]
        now = datetime.utcnow()

        # Record current risk score
        zone_state.risk_score_history.append((now, risk_score))
        zone_state.last_check_timestamp = now

        # Check if risk sustained above threshold
        trip_threshold = self.config.baseline_risk_score * self.config.volatility_multiplier
        sustained_duration = self._calculate_sustained_duration(
            zone_state.risk_score_history,
            trip_threshold
        )

        # Determine if should trip
        should_trip = (
            sustained_duration >= self.config.sustained_duration_seconds
        )

        if should_trip:
            reason = (
                f"Volatility sustained at {risk_score:.2f} "
                f"(threshold: {trip_threshold:.2f}) "
                f"for {sustained_duration:.0f}s "
                f"(level: {metrics.level.value})"
            )
        else:
            reason = f"Risk score {risk_score:.2f} below trip threshold or not sustained"

        return TripDecision(
            should_trip=should_trip,
            reason=reason,
            risk_score=risk_score,
            sustained_duration=sustained_duration,
            metrics=metrics
        )

    def evaluate_recovery(
        self,
        zone_id: str,
        metrics: VolatilityMetrics
    ) -> RecoveryDecision:
        """
        Evaluate whether circuit should transition to HALF_OPEN.

        Args:
            zone_id: Scheduling zone identifier
            metrics: Current volatility metrics

        Returns:
            RecoveryDecision with recommendation
        """
        zone_state = self.zone_states.get(zone_id)
        if not zone_state or not zone_state.trip_timestamp:
            return RecoveryDecision(
                should_recover=False,
                reason="Zone not in tripped state",
                current_risk_score=0.0,
                time_since_trip=0.0
            )

        now = datetime.utcnow()
        time_since_trip = (now - zone_state.trip_timestamp).total_seconds()

        # Check cooldown period
        if time_since_trip < self.config.cooldown_period_seconds:
            return RecoveryDecision(
                should_recover=False,
                reason=f"Cooldown not elapsed ({time_since_trip:.0f}s / {self.config.cooldown_period_seconds}s)",
                current_risk_score=0.0,
                time_since_trip=time_since_trip
            )

        # Check if volatility has stabilized
        risk_score = self._calculate_risk_score(metrics)
        recovery_threshold = self.config.baseline_risk_score * self.config.recovery_volatility_threshold

        should_recover = risk_score < recovery_threshold

        if should_recover:
            reason = (
                f"Volatility stabilized at {risk_score:.2f} "
                f"(threshold: {recovery_threshold:.2f}) "
                f"after {time_since_trip:.0f}s"
            )
        else:
            reason = (
                f"Volatility still elevated: {risk_score:.2f} "
                f"(needs < {recovery_threshold:.2f})"
            )

        return RecoveryDecision(
            should_recover=should_recover,
            reason=reason,
            current_risk_score=risk_score,
            time_since_trip=time_since_trip
        )

    def process_zone(self, zone_id: str, metrics: VolatilityMetrics):
        """
        Process volatility metrics for a zone and manage circuit breaker.

        This is the main entry point for integrating with homeostasis monitoring.

        Args:
            zone_id: Scheduling zone identifier
            metrics: Current volatility metrics
        """
        # Get current circuit state
        breaker = circuit_breaker_registry.get(zone_id)
        if not breaker:
            logger.warning(f"No circuit breaker registered for zone: {zone_id}")
            return

        current_state = breaker.state

        if current_state == CircuitState.CLOSED:
            # Check if should pre-emptively trip
            decision = self.evaluate_trip_signal(zone_id, metrics)

            if decision.should_trip:
                logger.warning(
                    f"PRE-EMPTIVE TRIP for {zone_id}: {decision.reason}"
                )
                breaker.open(reason=f"Volatility: {decision.reason}")

                # Record trip timestamp
                if zone_id in self.zone_states:
                    self.zone_states[zone_id].trip_timestamp = datetime.utcnow()

        elif current_state == CircuitState.OPEN:
            # Check if should attempt recovery
            decision = self.evaluate_recovery(zone_id, metrics)

            if decision.should_recover:
                logger.info(
                    f"RECOVERY ATTEMPT for {zone_id}: {decision.reason}"
                )
                # Circuit breaker will auto-transition to HALF_OPEN on next request
                # We don't force it here to maintain proper state machine control

    def _calculate_risk_score(self, metrics: VolatilityMetrics) -> float:
        """
        Calculate composite risk score from volatility metrics.

        Mirrors the calculation in homeostasis.py for consistency.
        """
        return (
            metrics.volatility * 2.0        # Primary indicator
            + metrics.jitter * 1.5          # Oscillation amplifies risk
            + (1.0 - metrics.distance_to_critical) * 1.0  # Proximity to threshold
        )

    def _calculate_sustained_duration(
        self,
        history: deque,
        threshold: float
    ) -> float:
        """
        Calculate how long risk has been sustained above threshold.

        Uses sliding window to find longest recent sustained period.
        """
        if not history:
            return 0.0

        # Work backwards from most recent
        sustained_start = None
        for timestamp, risk_score in reversed(history):
            if risk_score >= threshold:
                sustained_start = timestamp
            else:
                break

        if sustained_start is None:
            return 0.0

        # Duration from earliest sustained point to now
        return (datetime.utcnow() - sustained_start).total_seconds()

    def get_zone_status(self, zone_id: str) -> dict:
        """Get current status for a zone."""
        zone_state = self.zone_states.get(zone_id)
        if not zone_state:
            return {"zone_id": zone_id, "status": "not_tracked"}

        recent_scores = list(zone_state.risk_score_history)[-10:]

        return {
            "zone_id": zone_id,
            "trip_timestamp": zone_state.trip_timestamp.isoformat() if zone_state.trip_timestamp else None,
            "last_check": zone_state.last_check_timestamp.isoformat() if zone_state.last_check_timestamp else None,
            "recent_risk_scores": [
                {"timestamp": ts.isoformat(), "score": score}
                for ts, score in recent_scores
            ]
        }
```

---

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Volatility Circuit Breaker Bridge
VOLATILITY_TRIP_MULTIPLIER=2.0          # Trip at 2x baseline risk
VOLATILITY_SUSTAIN_DURATION=300         # Seconds (5 min)
VOLATILITY_COOLDOWN_PERIOD=600          # Seconds (10 min)
VOLATILITY_RECOVERY_THRESHOLD=1.2       # Near-normal threshold
```

### Service Configuration

**File**: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Volatility Circuit Breaker Bridge
    volatility_trip_multiplier: float = Field(
        default=2.0,
        description="Risk score multiplier to trip circuit"
    )
    volatility_sustain_duration: int = Field(
        default=300,
        description="Seconds volatility must be sustained"
    )
    volatility_cooldown_period: int = Field(
        default=600,
        description="Seconds before recovery attempt"
    )
    volatility_recovery_threshold: float = Field(
        default=1.2,
        description="Multiplier for recovery threshold"
    )
```

### Zone-Specific Overrides

Different scheduling zones may need different sensitivity:

```python
# More sensitive for critical zones
ZONE_CONFIGS = {
    "emergency_coverage": VolatilityTripConfig(
        volatility_multiplier=1.5,  # Trip faster
        sustained_duration_seconds=180,  # 3 min
    ),
    "elective_procedures": VolatilityTripConfig(
        volatility_multiplier=2.5,  # More tolerant
        sustained_duration_seconds=600,  # 10 min
    ),
}
```

---

## Zone Isolation

### Blast Radius Containment

Circuit breakers are **zone-scoped** to prevent localized volatility from affecting the entire system:

```python
SCHEDULING_ZONES = [
    "clinic",           # Outpatient clinic scheduling
    "inpatient",        # Ward/floor assignments
    "emergency",        # ED coverage
    "procedures",       # Procedure room assignments
    "call",             # Call schedules
]
```

**Isolation Properties:**

1. **Independent Trip Conditions**: Each zone tracks its own volatility metrics
2. **No Cross-Zone Contamination**: Clinic volatility doesn't trip inpatient circuit
3. **Graceful Degradation**: System can operate with some zones open, others closed
4. **Fallback Strategies**: Zone-specific fallback schedules (static stability)

### Example: Cascading Prevention

```
Scenario: Clinic zone experiences high volatility

WITHOUT zone isolation:
  Clinic volatility → System-wide circuit trip → All scheduling stops

WITH zone isolation:
  Clinic volatility → Clinic circuit OPEN → Inpatient/Emergency continue normally
  Clinic uses fallback → Pre-computed static schedule
  Impact: Only elective clinic appointments deferred
```

### Defense in Depth Integration

Maps to **Level 3: Safety Systems**:

```python
defense_in_depth.register_action_handler(
    level=DefenseLevel.SAFETY_SYSTEMS,
    action_name="zone_circuit_protection",
    handler=volatility_bridge.process_zone
)
```

---

## Test Cases

### 1. Gradual Volatility Increase → Trip at Threshold

**Scenario**: Volatility gradually increases and sustains above threshold.

```python
async def test_gradual_volatility_increase_trips_circuit():
    """Sustained high volatility should pre-emptively trip circuit."""
    bridge = VolatilityCircuitBridge()
    zone_id = "clinic"

    # Simulate 6 minutes of increasing volatility
    base_time = datetime.utcnow()
    for minute in range(6):
        metrics = VolatilityMetrics(
            volatility=0.15 + (minute * 0.05),  # Increasing
            jitter=0.4,
            momentum=0.8,
            distance_to_critical=0.5,
            level=VolatilityLevel.ELEVATED if minute < 4 else VolatilityLevel.HIGH
        )

        with freeze_time(base_time + timedelta(minutes=minute)):
            decision = bridge.evaluate_trip_signal(zone_id, metrics)

        # Should trip after 5 minutes
        if minute >= 5:
            assert decision.should_trip
            assert decision.sustained_duration >= 300
        else:
            assert not decision.should_trip
```

### 2. Spike Then Recovery → No Trip (Transient)

**Scenario**: Brief volatility spike that doesn't sustain.

```python
async def test_transient_spike_does_not_trip():
    """Brief spikes shouldn't trip if not sustained."""
    bridge = VolatilityCircuitBridge()
    zone_id = "inpatient"

    # Spike for 2 minutes, then recover
    timeline = [
        (0, 0.5),   # Normal
        (1, 1.5),   # Spike (above threshold)
        (2, 1.6),   # Still spiked
        (3, 0.6),   # Recovered
        (4, 0.5),   # Normal
    ]

    base_time = datetime.utcnow()
    for minute, risk_level in timeline:
        metrics = create_metrics_with_risk_score(risk_level)

        with freeze_time(base_time + timedelta(minutes=minute)):
            decision = bridge.evaluate_trip_signal(zone_id, metrics)

        # Should never trip (not sustained)
        assert not decision.should_trip
```

### 3. Sustained High Volatility → Trip

**Scenario**: Volatility remains high for full sustain duration.

```python
async def test_sustained_high_volatility_trips():
    """Volatility sustained for 5+ minutes should trip."""
    bridge = VolatilityCircuitBridge()
    zone_id = "emergency"

    # High volatility for 6 minutes
    high_metrics = VolatilityMetrics(
        volatility=0.35,
        jitter=0.6,
        momentum=1.2,
        distance_to_critical=0.2,
        level=VolatilityLevel.HIGH
    )

    base_time = datetime.utcnow()
    for minute in range(7):
        with freeze_time(base_time + timedelta(minutes=minute)):
            decision = bridge.evaluate_trip_signal(zone_id, high_metrics)

        if minute >= 5:
            assert decision.should_trip
            assert "sustained at" in decision.reason.lower()
```

### 4. Post-Trip Recovery Conditions

**Scenario**: Circuit opens, then volatility stabilizes.

```python
async def test_recovery_after_stabilization():
    """Circuit should allow recovery after volatility stabilizes."""
    bridge = VolatilityCircuitBridge()
    zone_id = "procedures"

    # Trip the circuit
    high_metrics = create_high_volatility_metrics()
    for _ in range(6):
        bridge.evaluate_trip_signal(zone_id, high_metrics)

    # Mark as tripped
    bridge.zone_states[zone_id].trip_timestamp = datetime.utcnow()

    # Advance time past cooldown
    with freeze_time(datetime.utcnow() + timedelta(minutes=11)):
        # Stabilized metrics
        stable_metrics = VolatilityMetrics(
            volatility=0.08,
            jitter=0.2,
            momentum=0.1,
            distance_to_critical=0.8,
            level=VolatilityLevel.STABLE
        )

        decision = bridge.evaluate_recovery(zone_id, stable_metrics)

        assert decision.should_recover
        assert "stabilized" in decision.reason.lower()
```

### 5. Cooldown Period Enforcement

**Scenario**: Recovery attempted too soon.

```python
async def test_cooldown_period_prevents_early_recovery():
    """Circuit shouldn't recover before cooldown elapsed."""
    bridge = VolatilityCircuitBridge(
        config=VolatilityTripConfig(cooldown_period_seconds=600)
    )
    zone_id = "call"

    # Trip circuit
    bridge.zone_states[zone_id] = ZoneState(
        zone_id=zone_id,
        risk_score_history=deque(),
        trip_timestamp=datetime.utcnow()
    )

    # Try recovery after only 5 minutes
    with freeze_time(datetime.utcnow() + timedelta(minutes=5)):
        stable_metrics = create_stable_metrics()
        decision = bridge.evaluate_recovery(zone_id, stable_metrics)

        assert not decision.should_recover
        assert "cooldown not elapsed" in decision.reason.lower()
```

### 6. Zone Isolation Test

**Scenario**: One zone trips, others unaffected.

```python
async def test_zone_isolation():
    """Volatility in one zone shouldn't affect others."""
    bridge = VolatilityCircuitBridge()

    # High volatility in clinic
    high_metrics = create_high_volatility_metrics()
    for _ in range(6):
        bridge.evaluate_trip_signal("clinic", high_metrics)

    # Normal volatility in inpatient
    normal_metrics = create_normal_metrics()
    decision = bridge.evaluate_trip_signal("inpatient", normal_metrics)

    # Inpatient should not trip
    assert not decision.should_trip

    # Verify independent state tracking
    assert "clinic" in bridge.zone_states
    assert "inpatient" in bridge.zone_states
    assert bridge.zone_states["clinic"].risk_score_history != \
           bridge.zone_states["inpatient"].risk_score_history
```

---

## Integration Points

### 1. Homeostasis Monitor Integration

**Location**: `backend/app/resilience/homeostasis.py`

Add to `HomeostasisMonitor` class:

```python
class HomeostasisMonitor:
    def __init__(self):
        # ... existing init ...
        self.volatility_bridge = VolatilityCircuitBridge()

    def check_all_loops(self, current_values: dict[str, float]) -> list[CorrectiveAction]:
        """Check feedback loops and update circuit breakers."""
        actions = []

        for loop in self.feedback_loops.values():
            if loop.setpoint.name in current_values:
                value = current_values[loop.setpoint.name]
                action = self.check_feedback_loop(loop.id, value)
                if action:
                    actions.append(action)

                # NEW: Process volatility for circuit breakers
                metrics = loop.get_volatility_metrics()
                zone_id = self._map_loop_to_zone(loop.setpoint.name)
                if zone_id:
                    self.volatility_bridge.process_zone(zone_id, metrics)

        return actions

    def _map_loop_to_zone(self, setpoint_name: str) -> Optional[str]:
        """Map setpoint to scheduling zone."""
        mapping = {
            "coverage_rate": "clinic",
            "faculty_utilization": "inpatient",
            "acgme_compliance": "emergency",
        }
        return mapping.get(setpoint_name)
```

### 2. Circuit Breaker Registry

**Location**: `backend/app/resilience/circuit_breaker/registry.py`

Ensure zones are registered:

```python
# Initialize circuit breakers for all scheduling zones
for zone in SCHEDULING_ZONES:
    circuit_breaker_registry.register(
        name=zone,
        failure_threshold=5,
        timeout_seconds=60.0,
    )
```

### 3. Celery Task (Periodic Check)

**Location**: `backend/app/core/celery_tasks.py`

```python
@celery_app.task(name="check_volatility_circuit_breakers")
def check_volatility_circuit_breakers():
    """
    Periodic task to check volatility and manage circuit breakers.

    Runs every 1 minute to evaluate volatility trends.
    """
    from app.resilience.homeostasis import homeostasis_monitor

    # Get current metrics from database
    current_values = get_current_scheduling_metrics()

    # Check all feedback loops (includes circuit breaker processing)
    homeostasis_monitor.check_all_loops(current_values)

    logger.info("Volatility circuit breaker check completed")

# Schedule task
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run every 60 seconds
    sender.add_periodic_task(
        60.0,
        check_volatility_circuit_breakers.s(),
        name="check-volatility-circuits"
    )
```

### 4. API Endpoints

**Location**: `backend/app/api/routes/resilience.py`

```python
@router.get("/volatility-circuit-status")
async def get_volatility_circuit_status():
    """Get status of all volatility-based circuit breakers."""
    from app.resilience.homeostasis import homeostasis_monitor

    bridge = homeostasis_monitor.volatility_bridge
    zones = ["clinic", "inpatient", "emergency", "procedures", "call"]

    return {
        "zones": [
            bridge.get_zone_status(zone_id)
            for zone_id in zones
        ],
        "config": {
            "trip_multiplier": bridge.config.volatility_multiplier,
            "sustain_duration": bridge.config.sustained_duration_seconds,
            "cooldown_period": bridge.config.cooldown_period_seconds,
        }
    }
```

---

## Metrics and Monitoring

### Key Metrics to Track

```python
# Prometheus metrics
volatility_circuit_trip_total = Counter(
    "volatility_circuit_trip_total",
    "Pre-emptive circuit trips due to volatility",
    labelnames=["zone", "reason"]
)

volatility_circuit_recovery_total = Counter(
    "volatility_circuit_recovery_total",
    "Circuit recoveries after volatility stabilization",
    labelnames=["zone"]
)

volatility_risk_score = Gauge(
    "volatility_risk_score",
    "Current volatility risk score per zone",
    labelnames=["zone"]
)

volatility_sustained_duration = Histogram(
    "volatility_sustained_duration_seconds",
    "Duration volatility sustained above threshold",
    labelnames=["zone"]
)
```

### Grafana Dashboard Panels

1. **Circuit Breaker State Timeline**
   - Panel type: State timeline
   - Query: `circuit_breaker_state{zone=~".*"}`
   - Shows CLOSED/OPEN/HALF_OPEN transitions

2. **Volatility Risk Score**
   - Panel type: Time series
   - Query: `volatility_risk_score{zone=~".*"}`
   - Threshold line at trip level (default: 1.0)

3. **Pre-emptive Trips vs Actual Failures**
   - Panel type: Stat
   - Metric: `volatility_circuit_trip_total` vs `circuit_breaker_failure_total`
   - Goal: Pre-emptive trips should exceed actual failures (catching issues early)

4. **Zone Health Heatmap**
   - Panel type: Heatmap
   - X-axis: Time
   - Y-axis: Zone
   - Color: Risk score (green → yellow → red)

---

## Edge Cases and Considerations

### 1. Clock Skew / Time Precision

**Issue**: Distributed systems may have slight clock differences.

**Mitigation**:
- Use UTC consistently
- Tolerance of ±30s in sustain duration checks
- NTP sync on all nodes

### 2. Rapid Oscillation (Flapping)

**Issue**: Volatility might oscillate around threshold, causing rapid trip/close cycles.

**Mitigation**:
- **Hysteresis**: Recovery threshold (1.2x) lower than trip threshold (2.0x)
- **Cooldown period**: Minimum 10 minutes before recovery attempt
- **Rate limiting**: Max 1 trip per zone per 15 minutes

### 3. False Positives from Data Gaps

**Issue**: Missing data points could be misinterpreted as volatility.

**Mitigation**:
- Require minimum history size (5 data points)
- Distinguish "no data" from "high volatility"
- Alert on data pipeline failures separately

### 4. Bootstrap/Cold Start

**Issue**: No historical data when system first starts.

**Mitigation**:
- Grace period: Don't trip for first 30 minutes
- Pre-load historical data if available
- Default to CLOSED state

### 5. Cascading Zone Failures

**Issue**: If multiple zones trip simultaneously, entire system capacity drops.

**Mitigation**:
- **Defense in Depth Level 4**: Activate containment protocols
- **Minimum viable service**: Protect emergency coverage at all costs
- **Fallback schedules**: Static pre-computed schedules for all zones

### 6. Manual Override Conflicts

**Issue**: Admin manually closes circuit while volatility still high.

**Mitigation**:
- Log manual overrides prominently
- Re-evaluate on next check (might re-trip)
- Provide "suppress auto-trip" flag for maintenance windows

### 7. Metric Staleness

**Issue**: Volatility metrics calculated from stale data.

**Mitigation**:
- Timestamp all metrics
- Reject metrics older than 5 minutes
- Alert on metric staleness

---

## Success Criteria

The bridge is successful if:

1. **Pre-emptive Detection**: ≥80% of instability events detected before failures
2. **False Positive Rate**: <10% of trips are false positives
3. **Recovery Time**: Median time from trip to recovery <15 minutes
4. **Zone Isolation**: Localized volatility doesn't cascade (99.9% isolation)
5. **Performance**: Evaluation overhead <10ms per zone per check

---

## Future Enhancements

1. **Machine Learning**: Train model on historical volatility→failure correlations
2. **Adaptive Thresholds**: Self-tune thresholds based on zone characteristics
3. **Predictive Tripping**: Use momentum/trend analysis for earlier detection
4. **Cross-Zone Correlation**: Detect patterns where multiple zones destabilize together
5. **Auto-Remediation**: Trigger corrective actions (load shedding) on trip

---

## References

- **Homeostasis**: `/backend/app/resilience/homeostasis.py`
- **Circuit Breaker**: `/backend/app/resilience/circuit_breaker/breaker.py`
- **Defense in Depth**: `/backend/app/resilience/defense_in_depth.py`
- **Cross-Disciplinary Resilience**: `/docs/architecture/cross-disciplinary-resilience.md`
- **Release It! (Nygard)**: Circuit breaker pattern source
- **Chaos Engineering (Netflix)**: Hystrix circuit breaker design

---

**Implementation Checklist:**

- [ ] Create `VolatilityCircuitBridge` class (`~75 LOC`)
- [ ] Add configuration to `Settings`
- [ ] Integrate with `HomeostasisMonitor`
- [ ] Register zones in circuit breaker registry
- [ ] Create Celery periodic task
- [ ] Add API endpoints for status
- [ ] Write test suite (6 core tests)
- [ ] Configure Prometheus metrics
- [ ] Build Grafana dashboard
- [ ] Document operational runbook

---

*End of Specification*
