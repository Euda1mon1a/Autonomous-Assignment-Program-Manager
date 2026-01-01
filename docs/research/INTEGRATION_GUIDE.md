# Thermodynamic Resilience - Integration Guide

**Purpose:** Show how new thermodynamic modules integrate with existing resilience framework
**Audience:** Developers implementing the thermodynamic enhancements
**Date:** 2025-12-20

---

## Current System Overview

### Existing Resilience Components

The resilience framework already has sophisticated monitoring:

```
backend/app/resilience/
├── homeostasis.py              # Volatility, jitter, distance-to-criticality
├── contingency.py              # N-1/N-2 analysis
├── defense_in_depth.py         # 5-level defense system
├── blast_radius.py             # Zone isolation
├── le_chatelier.py             # Equilibrium shift analysis
├── sacrifice_hierarchy.py      # Load shedding
├── static_stability.py         # Fallback schedules
├── utilization.py              # 80% threshold monitoring
└── service.py                  # Main resilience orchestrator
```

### Existing Early Warning in Homeostasis

`homeostasis.py` already implements:

```python
class VolatilityMetrics:
    """Existing volatility tracking."""
    volatility: float      # Coefficient of variation
    jitter: float          # Oscillation frequency
    momentum: float        # Directional trend
    distance_to_critical: float  # Margin before threshold
    level: VolatilityLevel
```

**What's Missing:**
- Theoretical foundations (why do these metrics work?)
- Entropy-based analysis
- Phase transition theory
- Free energy landscapes
- Information-theoretic optimization

---

## Integration Architecture

### New Thermodynamic Layer

```
backend/app/resilience/thermodynamics/
├── __init__.py                 # ✅ IMPLEMENTED
├── entropy.py                  # ✅ IMPLEMENTED
├── phase_transitions.py        # ✅ IMPLEMENTED
├── free_energy.py              # ✅ IMPLEMENTED
├── boltzmann.py                # ❌ NOT IMPLEMENTED
├── fluctuation.py              # ❌ NOT IMPLEMENTED
├── dissipative.py              # ❌ NOT IMPLEMENTED
└── maxwell_demon.py            # ❌ NOT IMPLEMENTED
```

### Integration Points

```python
# resilience/service.py - UPDATED
from app.resilience.thermodynamics import (
    ScheduleEntropyMonitor,
    PhaseTransitionDetector,
    CriticalPhenomenaMonitor,
    calculate_free_energy,  # When implemented
)

class ResilienceService:
    def __init__(self, db: Session):
        # Existing Tier 1 components
        self.utilization = UtilizationMonitor()
        self.defense = DefenseInDepth()
        self.contingency = ContingencyAnalyzer()

        # Existing Tier 2 components
        self.homeostasis = HomeostasisMonitor()
        self.blast_radius = BlastRadiusManager()
        self.le_chatelier = LeChatelierAnalyzer()

        # NEW: Thermodynamic foundation
        self.entropy_monitor = ScheduleEntropyMonitor()
        self.phase_detector = PhaseTransitionDetector()
        self.critical_monitor = CriticalPhenomenaMonitor()

    async def health_check(self) -> ResilienceHealth:
        """Enhanced with thermodynamic analysis."""
        # ... existing health check ...

        # NEW: Thermodynamic metrics
        entropy_metrics = self._analyze_entropy()
        phase_risk = self._detect_phase_transitions()

        # Integrate findings
        if phase_risk.overall_severity == TransitionSeverity.CRITICAL:
            # Escalate defense level
            self.defense.escalate("CRITICAL_THERMODYNAMIC_SIGNAL")

        return ResilienceHealth(
            # ... existing fields ...
            entropy_metrics=entropy_metrics,
            phase_transition_risk=phase_risk,
        )
```

---

## Enhancing Existing Modules

### 1. Homeostasis Monitor Enhancement

**Current Code:**
```python
# homeostasis.py - EXISTING
class HomeostasisMonitor:
    def detect_volatility_risks(self) -> list[VolatilityAlert]:
        """Existing volatility detection."""
        for loop in self.feedback_loops:
            metrics = loop.get_volatility_metrics()

            if metrics.volatility > 0.15:
                # Alert on high variance
                ...
```

**Enhanced with Thermodynamics:**
```python
# homeostasis.py - ENHANCED
from app.resilience.thermodynamics import (
    calculate_schedule_entropy,
    detect_critical_slowing,
)

class HomeostasisMonitor:
    def __init__(self):
        # ... existing initialization ...

        # NEW: Add entropy monitor
        self.entropy_monitor = ScheduleEntropyMonitor()

    def detect_volatility_risks(self) -> list[VolatilityAlert]:
        """Enhanced with entropy and phase transition theory."""
        # Existing volatility detection
        for loop in self.feedback_loops:
            metrics = loop.get_volatility_metrics()

            # NEW: Add entropy analysis
            entropy = self.entropy_monitor.get_current_metrics()

            # NEW: Theoretical interpretation
            # High variance + high entropy → disorder increasing
            # High variance + low entropy → concentrated instability
            if metrics.volatility > 0.15:
                if entropy["current_entropy"] > 3.0:
                    evidence.append(
                        "High disorder (entropy={:.2f}) with high variance - "
                        "system becoming chaotic".format(entropy["current_entropy"])
                    )
                else:
                    evidence.append(
                        "Low entropy with high variance - "
                        "concentrated instability (hub overload risk)"
                    )

            # NEW: Critical slowing down (thermodynamic early warning)
            if entropy["critical_slowing"]:
                evidence.append(
                    "Critical slowing detected - phase transition imminent "
                    "(thermodynamic early warning)"
                )
                severity = "CRITICAL"  # Escalate

        return alerts
```

### 2. Defense In Depth Integration

**Current Code:**
```python
# defense_in_depth.py - EXISTING
class DefenseInDepth:
    def assess_level(self, health: ResilienceHealth) -> DefenseLevel:
        """Determine appropriate defense level."""
        if health.utilization > 0.95:
            return DefenseLevel.EMERGENCY  # Level 5
        elif health.utilization > 0.85:
            return DefenseLevel.MITIGATION  # Level 4
        # ... etc
```

**Enhanced:**
```python
# defense_in_depth.py - ENHANCED
class DefenseInDepth:
    def assess_level(
        self,
        health: ResilienceHealth,
        phase_risk: PhaseTransitionRisk  # NEW
    ) -> DefenseLevel:
        """Determine defense level using thermodynamic early warnings."""

        # Existing utilization-based assessment
        if health.utilization > 0.95:
            base_level = DefenseLevel.EMERGENCY

        # NEW: Phase transition risk can escalate earlier
        if phase_risk.overall_severity == TransitionSeverity.IMMINENT:
            # Phase transition detected → escalate even if utilization OK
            logger.warning(
                "Escalating defense level due to imminent phase transition, "
                f"even though utilization={health.utilization:.1%}"
            )
            return DefenseLevel.EMERGENCY

        elif phase_risk.overall_severity == TransitionSeverity.CRITICAL:
            # Early warning → pre-emptive escalation
            return max(base_level, DefenseLevel.MITIGATION)

        return base_level
```

### 3. Contingency Analyzer Enhancement

**Current Code:**
```python
# contingency.py - EXISTING
class ContingencyAnalyzer:
    def analyze_n1_vulnerability(self) -> VulnerabilityReport:
        """N-1 analysis: can system survive losing any single faculty?"""
        # Graph-based centrality analysis
        ...
```

**Enhanced:**
```python
# contingency.py - ENHANCED
from app.resilience.thermodynamics import calculate_free_energy

class ContingencyAnalyzer:
    def analyze_n1_vulnerability(self) -> VulnerabilityReport:
        """Enhanced N-1 with free energy landscape analysis."""

        # Existing graph-based analysis
        centrality_scores = self._calculate_centrality()

        # NEW: Energy landscape analysis
        # For each potential faculty loss, calculate energy barrier
        energy_barriers = {}
        for person_id in self.faculty:
            # Simulate removal
            test_schedule = self._simulate_removal(person_id)

            # Calculate free energy (stability measure)
            current_F = calculate_free_energy(self.current_schedule)
            test_F = calculate_free_energy(test_schedule)

            # Energy barrier = cost of transition
            barrier = test_F - current_F

            energy_barriers[person_id] = barrier

        # Low barrier → vulnerable to losing this person
        critical_personnel = [
            pid for pid, barrier in energy_barriers.items()
            if barrier < 5.0  # Low barrier threshold
        ]

        return VulnerabilityReport(
            # ... existing fields ...
            energy_barriers=energy_barriers,
            thermodynamically_critical=critical_personnel,
        )
```

---

## Celery Task Integration

### New Background Tasks

```python
# resilience/tasks.py - ENHANCED

from app.resilience.thermodynamics import (
    CriticalPhenomenaMonitor,
    PhaseTransitionRisk,
)

@celery_app.task
def thermodynamic_health_check():
    """
    Background task: Monitor thermodynamic stability.
    Runs every 15 minutes.
    """
    db = get_db()

    # Collect current metrics
    metrics = {
        "utilization": get_utilization(db),
        "coverage": get_coverage_rate(db),
        "violations": count_violations(db),
        "workload_variance": calculate_workload_variance(db),
        # ... etc
    }

    # Update phase transition detector
    monitor = CriticalPhenomenaMonitor()
    risk = await monitor.update_and_assess(metrics)

    # Store in database
    await store_phase_transition_risk(db, risk)

    # Alert if critical
    if risk.overall_severity in (TransitionSeverity.CRITICAL, TransitionSeverity.IMMINENT):
        await send_alert(
            severity="CRITICAL",
            title="Phase Transition Risk Detected",
            message=f"{len(risk.signals)} early warning signals detected. "
                    f"Estimated time to transition: {risk.time_to_transition:.1f} hours",
            recommendations=risk.recommendations
        )

    db.close()


@celery_app.task
def entropy_analysis():
    """
    Background task: Analyze schedule entropy trends.
    Runs every hour.
    """
    db = get_db()

    assignments = get_current_assignments(db)

    from app.resilience.thermodynamics import calculate_schedule_entropy
    metrics = calculate_schedule_entropy(assignments)

    # Store in time series
    await store_entropy_metrics(db, metrics)

    # Check for critical slowing
    entropy_history = await get_entropy_history(db, hours=24)
    if detect_critical_slowing(entropy_history):
        await send_alert(
            severity="HIGH",
            title="Critical Slowing Down Detected",
            message="Entropy dynamics show critical slowing - phase transition approaching"
        )

    db.close()


# Schedule new tasks
celery_app.conf.beat_schedule.update({
    'thermodynamic-health-check': {
        'task': 'app.resilience.tasks.thermodynamic_health_check',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'entropy-analysis': {
        'task': 'app.resilience.tasks.entropy_analysis',
        'schedule': crontab(minute=0),  # Every hour
    },
})
```

---

## Database Schema Updates

### New Tables

```sql
-- Thermodynamic metrics time series
CREATE TABLE thermodynamic_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Entropy metrics
    person_entropy FLOAT,
    rotation_entropy FLOAT,
    joint_entropy FLOAT,
    mutual_information FLOAT,
    entropy_production_rate FLOAT,

    -- Free energy metrics (when implemented)
    free_energy FLOAT,
    internal_energy FLOAT,
    effective_temperature FLOAT,

    -- Phase transition risk
    phase_transition_severity VARCHAR(20),
    time_to_transition FLOAT,
    confidence FLOAT,

    -- Metadata
    computed_by VARCHAR(50),
    notes TEXT
);

CREATE INDEX idx_thermodynamic_timestamp ON thermodynamic_metrics(timestamp);

-- Phase transition signals
CREATE TABLE phase_transition_signals (
    id SERIAL PRIMARY KEY,
    metric_id INTEGER REFERENCES thermodynamic_metrics(id),
    detected_at TIMESTAMP NOT NULL DEFAULT NOW(),

    signal_type VARCHAR(50),  -- variance, autocorr, flicker, skew
    metric_name VARCHAR(100),
    severity VARCHAR(20),
    value FLOAT,
    threshold FLOAT,
    description TEXT
);

CREATE INDEX idx_signals_metric ON phase_transition_signals(metric_id);
CREATE INDEX idx_signals_severity ON phase_transition_signals(severity);
```

### Update Existing Resilience Metrics

```sql
-- Add thermodynamic columns to existing resilience_metrics table
ALTER TABLE resilience_metrics
ADD COLUMN schedule_entropy FLOAT,
ADD COLUMN free_energy FLOAT,
ADD COLUMN phase_transition_risk VARCHAR(20);
```

---

## API Endpoints

### New Routes

```python
# api/routes/resilience.py - NEW ENDPOINTS

from app.resilience.thermodynamics import (
    calculate_schedule_entropy,
    PhaseTransitionDetector,
)

@router.get("/resilience/thermodynamics/entropy")
async def get_schedule_entropy(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """
    Get schedule entropy metrics.

    Returns entropy analysis across multiple dimensions:
    - Person distribution entropy
    - Rotation distribution entropy
    - Mutual information (coupling)
    - Entropy production rate
    """
    assignments = await get_assignments(db, start_date, end_date)
    metrics = calculate_schedule_entropy(assignments)

    return {
        "person_entropy": metrics.person_entropy,
        "rotation_entropy": metrics.rotation_entropy,
        "joint_entropy": metrics.joint_entropy,
        "mutual_information": metrics.mutual_information,
        "entropy_production_rate": metrics.entropy_production_rate,
        "normalized_entropy": metrics.normalized_entropy,
        "computed_at": metrics.computed_at.isoformat(),
    }


@router.get("/resilience/thermodynamics/phase-transition-risk")
async def get_phase_transition_risk(
    db: Session = Depends(get_db),
):
    """
    Get current phase transition risk assessment.

    Returns early warning signals and risk level based on
    critical phenomena detection.
    """
    # Get recent risk assessment from database
    risk = await get_latest_phase_transition_risk(db)

    if not risk:
        return {"error": "No risk assessment available yet"}

    return {
        "overall_severity": risk.overall_severity,
        "signals": [
            {
                "type": s.signal_type,
                "metric": s.metric_name,
                "severity": s.severity,
                "value": s.value,
                "description": s.description,
            }
            for s in risk.signals
        ],
        "time_to_transition": risk.time_to_transition,
        "confidence": risk.confidence,
        "recommendations": risk.recommendations,
    }


@router.get("/resilience/thermodynamics/entropy/history")
async def get_entropy_history(
    hours: int = 24,
    db: Session = Depends(get_db),
):
    """
    Get historical entropy metrics.

    Returns time series of entropy measurements for trend analysis.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    results = db.query(ThermodynamicMetrics).filter(
        ThermodynamicMetrics.timestamp >= cutoff
    ).order_by(ThermodynamicMetrics.timestamp).all()

    return {
        "data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "person_entropy": r.person_entropy,
                "rotation_entropy": r.rotation_entropy,
                "mutual_information": r.mutual_information,
                "entropy_production_rate": r.entropy_production_rate,
            }
            for r in results
        ],
        "count": len(results),
    }
```

---

## Prometheus Metrics

### New Metrics

```python
# resilience/metrics.py - ENHANCED

class ResilienceMetrics:
    def __init__(self, registry=None):
        # ... existing metrics ...

        # NEW: Thermodynamic metrics
        self.schedule_entropy = Gauge(
            "resilience_schedule_entropy",
            "Shannon entropy of schedule assignment distribution (bits)",
            ["dimension"],  # person, rotation, time, joint
            registry=self._registry,
        )

        self.entropy_production_rate = Gauge(
            "resilience_entropy_production_rate",
            "Rate of entropy generation (bits/hour)",
            registry=self._registry,
        )

        self.free_energy = Gauge(
            "resilience_free_energy",
            "Schedule free energy (stability metric)",
            registry=self._registry,
        )

        self.phase_transition_risk = Gauge(
            "resilience_phase_transition_risk",
            "Phase transition risk level (0=normal to 4=imminent)",
            registry=self._registry,
        )

        self.critical_signals_count = Gauge(
            "resilience_critical_signals_count",
            "Number of detected early warning signals",
            ["severity"],
            registry=self._registry,
        )

    def update_thermodynamic_metrics(
        self,
        entropy_metrics: EntropyMetrics,
        phase_risk: PhaseTransitionRisk,
        free_energy: float = None,
    ):
        """Update thermodynamic metrics."""
        # Entropy
        self.schedule_entropy.labels(dimension="person").set(
            entropy_metrics.person_entropy
        )
        self.schedule_entropy.labels(dimension="rotation").set(
            entropy_metrics.rotation_entropy
        )
        self.schedule_entropy.labels(dimension="joint").set(
            entropy_metrics.joint_entropy
        )

        self.entropy_production_rate.set(
            entropy_metrics.entropy_production_rate
        )

        # Free energy (if available)
        if free_energy is not None:
            self.free_energy.set(free_energy)

        # Phase transition risk
        severity_map = {
            TransitionSeverity.NORMAL: 0,
            TransitionSeverity.ELEVATED: 1,
            TransitionSeverity.HIGH: 2,
            TransitionSeverity.CRITICAL: 3,
            TransitionSeverity.IMMINENT: 4,
        }
        self.phase_transition_risk.set(
            severity_map[phase_risk.overall_severity]
        )

        # Signal counts
        for severity in TransitionSeverity:
            count = sum(1 for s in phase_risk.signals if s.severity == severity)
            self.critical_signals_count.labels(severity=severity.value).set(count)
```

---

## Testing Strategy

### Unit Tests

```python
# tests/resilience/thermodynamics/test_entropy.py

import pytest
from app.resilience.thermodynamics import (
    calculate_shannon_entropy,
    calculate_schedule_entropy,
    mutual_information,
    ScheduleEntropyMonitor,
)

class TestShannonEntropy:
    def test_uniform_distribution(self):
        """Uniform distribution has maximum entropy."""
        dist = [1, 2, 3, 4]  # All different, uniform
        H = calculate_shannon_entropy(dist)
        assert H == 2.0  # log2(4) = 2.0

    def test_deterministic(self):
        """Single value has zero entropy."""
        dist = [1, 1, 1, 1]
        H = calculate_shannon_entropy(dist)
        assert H == 0.0

    def test_binary_distribution(self):
        """Binary distribution entropy."""
        dist = [0, 0, 1, 1]  # 50-50 split
        H = calculate_shannon_entropy(dist)
        assert abs(H - 1.0) < 0.01  # Should be ~1.0 bit

class TestScheduleEntropy:
    def test_empty_schedule(self):
        """Empty schedule has zero entropy."""
        metrics = calculate_schedule_entropy([])
        assert metrics.person_entropy == 0.0

    def test_concentrated_schedule(self):
        """One person doing everything has low entropy."""
        from app.models.assignment import Assignment

        assignments = [
            Assignment(person_id=1, rotation_template_id=i, block_id=i)
            for i in range(10)
        ]

        metrics = calculate_schedule_entropy(assignments)
        assert metrics.person_entropy == 0.0  # Single person

    def test_diverse_schedule(self):
        """Diverse schedule has higher entropy."""
        from app.models.assignment import Assignment

        assignments = [
            Assignment(person_id=i, rotation_template_id=1, block_id=i)
            for i in range(10)
        ]

        metrics = calculate_schedule_entropy(assignments)
        assert metrics.person_entropy > 2.0  # 10 people → high entropy

class TestEntropyMonitor:
    def test_critical_slowing_detection(self):
        """Detect critical slowing down."""
        monitor = ScheduleEntropyMonitor()

        # Simulate high autocorrelation (critical slowing)
        # values: 1.0, 1.1, 1.2, 1.3, ... (slow drift)
        for i in range(20):
            assignments = self._create_assignments_with_entropy(1.0 + i * 0.1)
            monitor.update(assignments)

        assert monitor.detect_critical_slowing()

    def _create_assignments_with_entropy(self, target_entropy):
        # Helper to create assignments with specific entropy
        ...
```

### Integration Tests

```python
# tests/resilience/thermodynamics/test_phase_integration.py

import pytest
from app.resilience.thermodynamics import CriticalPhenomenaMonitor

class TestPhaseTransitionIntegration:
    @pytest.mark.asyncio
    async def test_early_warning_escalation(self, db):
        """Test that early warnings trigger defense escalation."""
        from app.resilience.service import ResilienceService

        service = ResilienceService(db)

        # Simulate metrics approaching phase transition
        metrics = {
            "utilization": 0.75,  # Not critical yet
            "coverage": 0.95,
            "violations": 2,
        }

        # Update multiple times with increasing variance
        for i in range(50):
            metrics["utilization"] += 0.001 * i  # Accelerating increase
            await service.thermodynamic_update(metrics)

        # Check that phase transition was detected
        health = await service.health_check()
        assert health.phase_transition_risk.overall_severity in [
            TransitionSeverity.HIGH,
            TransitionSeverity.CRITICAL,
        ]

        # Defense should escalate even though utilization < 0.80
        assert service.defense.current_level >= DefenseLevel.DETECTION
```

---

## Migration Plan

### Step 1: Add Entropy Module (Week 1)

1. ✅ Create `thermodynamics/entropy.py`
2. ✅ Create `thermodynamics/__init__.py`
3. Write tests
4. Integrate with `HomeostasisMonitor`
5. Add Prometheus metrics
6. Deploy to staging

### Step 2: Add Phase Transition Detection (Week 2)

1. ✅ Create `thermodynamics/phase_transitions.py`
2. Write tests
3. Add Celery task
4. Create API endpoints
5. Add database tables
6. Deploy to staging

### Step 3: Add Free Energy (Week 3)

1. Create `thermodynamics/free_energy.py`
2. Implement energy landscape analyzer
3. Integrate with `ContingencyAnalyzer`
4. Add visualization endpoints
5. Deploy to staging

### Step 4: Validation and Tuning (Week 4)

1. Backtest on historical data
2. Calibrate thresholds
3. Compare with existing methods
4. Tune alert sensitivity
5. Deploy to production

---

## Deployment Checklist

- [ ] All unit tests passing (target: 90% coverage)
- [ ] Integration tests passing
- [ ] Performance benchmarks acceptable (<10ms overhead)
- [ ] Database migrations tested
- [ ] API documentation updated
- [ ] Prometheus dashboards created
- [ ] Grafana alerts configured
- [ ] Operator training completed
- [ ] Rollback plan prepared
- [ ] Monitoring in place
- [ ] Staged rollout to 10% traffic
- [ ] Full production deployment

---

## Troubleshooting

### Common Issues

**Issue:** Entropy calculations taking too long
- **Solution:** Enable caching, only recalculate on schedule changes
- **Code:** Add `@lru_cache` decorator

**Issue:** Phase transition false positives
- **Solution:** Increase window size, adjust thresholds
- **Code:** `PhaseTransitionDetector(window_size=100)`

**Issue:** Memory usage increasing
- **Solution:** Limit history window size
- **Code:** Set `history_window=50` instead of 100

---

## Support

**Questions:** Post in #resilience-framework Slack channel
**Documentation:** `/docs/research/thermodynamic_resilience_foundations.md`
**Issues:** File GitHub issue with `thermodynamics` label

---

**Author:** Claude (Anthropic)
**Last Updated:** 2025-12-20
