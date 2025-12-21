# Complex Systems Implementation Quick Guide

**Purpose**: Quick reference for implementing exotic complex systems concepts in the scheduling system
**Full Report**: See `complex-systems-scheduling-research.md` for detailed analysis
**Date**: 2025-12-20

---

## 7 Concepts Summary

| Concept | Key Metric | Target | Current Implementation | Enhancement Needed |
|---------|-----------|--------|----------------------|-------------------|
| **1. Self-Organized Criticality** | Relaxation time, Variance, AC1 | τ < 48hrs, AC1 < 0.7 | None | Add SOC avalanche predictor |
| **2. Power Laws** | Exponent γ | 2.0 < γ < 3.0 | Hub detection exists | Track γ over time |
| **3. Emergence** | Pattern surprise (KL divergence) | - | Preference trails | Add pattern mining |
| **4. Edge of Chaos** | Order/chaos balance | -0.2 to 0.2 | Implicit | Add balance calculator |
| **5. Robustness-Fragility** | HOT paradox ratio | < 5.0 | None | Add stress testing |
| **6. Modularity** | Q-modularity | 0.4 - 0.6 | Zones exist | Measure Q score |
| **7. Redundancy vs Diversity** | Shannon entropy | > 0.7 | N-1 only | Add diversity metrics |

---

## Quick Implementation Checklist

### Week 1: Baseline Measurements (1-2 days each)

```python
# 1. Power Law Distribution Check
from scipy.stats import powerlaw
disruptions = get_disruption_history(days=180)
sizes = [d.faculty_affected for d in disruptions]
gamma = 1 + len(sizes) / sum(np.log(sizes / min(sizes)))
print(f"Power law exponent γ = {gamma:.2f}")
# ✓ Confirms SOC if 2.0 < γ < 3.0
```

```python
# 2. Shannon Entropy (Skill Diversity)
from scipy.stats import entropy
skill_counts = count_skills_per_faculty()
H = entropy(list(skill_counts.values()))
H_norm = H / np.log(len(skill_counts))
print(f"Shannon entropy = {H_norm:.2f}")
# ✓ Target: H_norm > 0.7
```

```python
# 3. Q-Modularity (Zone Structure)
import networkx as nx
from networkx.algorithms import community
G = build_faculty_network()
communities = get_zone_assignments()
Q = community.modularity(G, communities)
print(f"Q-modularity = {Q:.2f}")
# ✓ Target: 0.4 < Q < 0.6
```

```python
# 4. HOT Paradox Ratio
robustness = test_designed_scenarios()  # Normal failures
fragility = test_unexpected_scenarios()  # Novel failures
ratio = fragility / robustness
print(f"HOT ratio = {ratio:.1f}")
# ✓ Target: ratio < 5.0
```

### Month 1-2: Add to Existing Resilience Service

**File**: `/home/user/Autonomous-Assignment-Program-Manager/backend/app/resilience/service.py`

```python
class ResilienceService:
    def __init__(self, db: Session, config: ResilienceConfig):
        # ... existing initialization ...

        # NEW: Complex systems analyzers
        self.soc_predictor = SOCAvalanchePredictor(db)
        self.power_law_monitor = PowerLawMonitor(db)
        self.edge_analyzer = EdgeOfChaosAnalyzer(db)
        self.hot_analyzer = RobustnessFragilityAnalyzer(db)
        self.modularity_analyzer = ModularityAnalyzer(db)
        self.diversity_calculator = DiversityMetrics(db)

    def check_health(self, faculty, blocks, assignments) -> SystemHealthReport:
        # ... existing health checks ...

        # NEW: Add complex systems checks
        health_report.soc_avalanche_risk = self.soc_predictor.calculate_risk(assignments)
        health_report.power_law_gamma = self.power_law_monitor.calculate_gamma()
        health_report.edge_balance = self.edge_analyzer.calculate_balance(assignments)
        health_report.hot_ratio = self.hot_analyzer.get_paradox_ratio()
        health_report.modularity_Q = self.modularity_analyzer.calculate_Q()
        health_report.skill_diversity = self.diversity_calculator.shannon_entropy()

        # Add to warnings if thresholds exceeded
        if health_report.soc_avalanche_risk > 0.6:
            health_report.immediate_actions.append("SOC avalanche risk HIGH - activate preventive measures")

        if health_report.power_law_gamma < 2.5:
            health_report.watch_items.append(f"Hub concentration increasing (γ={health_report.power_law_gamma:.2f})")

        return health_report
```

---

## Critical Early Warning Signals

### 1. SOC Avalanche Warning (2-4 weeks advance notice)

**Signals to monitor**:
- ✋ **Relaxation time increasing**: Swap requests taking longer to resolve
- ✋ **Variance spike**: Daily workload variance up 50%+
- ✋ **High autocorrelation**: AC1 > 0.7 (today predicts tomorrow too well)

**Implementation**:
```python
def detect_soc_warning():
    # Get last 60 days of swap data
    swaps = get_swap_history(days=60)

    # Calculate relaxation time
    recent_tau = np.mean([s.resolution_hours for s in swaps[-15:]])
    baseline_tau = np.mean([s.resolution_hours for s in swaps[:30]])

    # Calculate variance change
    utilization = get_daily_utilization(days=60)
    baseline_var = np.var(utilization[:30])
    recent_var = np.var(utilization[30:])

    # Calculate autocorrelation
    ac1 = np.corrcoef(utilization[:-1], utilization[1:])[0, 1]

    warnings = []
    if recent_tau > 48:
        warnings.append(f"Relaxation time = {recent_tau:.1f}hrs (critical slowing down)")
    if recent_var > baseline_var * 1.5:
        warnings.append(f"Variance increased {(recent_var/baseline_var - 1)*100:.0f}% (instability)")
    if ac1 > 0.7:
        warnings.append(f"Autocorrelation = {ac1:.2f} (approaching phase transition)")

    if len(warnings) >= 2:
        return "AVALANCHE WARNING - Multiple SOC signals detected", warnings
    return "Normal", []
```

### 2. Hub Cascade Risk

**Signal**: Power law exponent γ decreasing (network centralizing)

**Implementation**:
```python
def track_gamma_trend():
    # Calculate γ monthly
    gamma_history = calculate_monthly_gamma(months=6)

    trend = np.polyfit(range(len(gamma_history)), gamma_history, 1)[0]
    current_gamma = gamma_history[-1]

    if trend < -0.05:  # Decreasing
        return f"WARNING: Network centralizing (γ trend = {trend:.3f})"
    if current_gamma < 2.0:
        return f"CRITICAL: Super-hub dominance (γ = {current_gamma:.2f})"
    return "Normal"
```

### 3. Edge of Chaos Imbalance

**Signal**: System drifting too far toward order or chaos

**Implementation**:
```python
def calculate_edge_balance():
    # Order metrics
    rotation_adherence = calculate_rotation_adherence()
    constraint_satisfaction = calculate_constraint_rate()
    order_score = (rotation_adherence + constraint_satisfaction) / 2

    # Chaos metrics
    swap_rate = calculate_swap_frequency()
    assignment_variance = calculate_assignment_variance()
    chaos_score = (swap_rate + assignment_variance) / 2

    balance = (chaos_score - order_score) / (chaos_score + order_score)

    if balance < -0.3:
        return "TOO ORDERED - Reduce constraints, allow more flexibility"
    if balance > 0.3:
        return "TOO CHAOTIC - Add structure, reduce swap frequency"
    return "OPTIMAL - At edge of chaos"
```

---

## Monthly Review Checklist

### Metrics Dashboard (15 minutes)

```markdown
## Complex Systems Health Check - [Month/Year]

### 1. Self-Organized Criticality
- [ ] Relaxation time: _____ hours (target: < 48)
- [ ] Variance change: _____% (target: < 50% increase)
- [ ] Lag-1 autocorrelation: _____ (target: < 0.7)
- [ ] **SOC Avalanche Risk**: [LOW / MODERATE / HIGH / CRITICAL]

### 2. Power Law Distribution
- [ ] Gamma exponent (γ): _____ (target: 2.0-3.0)
- [ ] Gamma trend: [INCREASING / STABLE / DECREASING]
- [ ] Hub concentration: [LOW / MODERATE / HIGH]
- [ ] **Action**: [None / Monitor / Diversify hubs]

### 3. Edge of Chaos
- [ ] Order score: _____
- [ ] Chaos score: _____
- [ ] Balance: _____ (target: -0.2 to 0.2)
- [ ] **Position**: [TOO ORDERED / OPTIMAL / TOO CHAOTIC]

### 4. Robustness-Fragility
- [ ] Designed-for robustness: _____
- [ ] Unexpected fragility: _____
- [ ] HOT paradox ratio: _____ (target: < 5.0)
- [ ] **Assessment**: [BALANCED / OVER-OPTIMIZED]

### 5. Modularity
- [ ] Q-modularity: _____ (target: 0.4-0.6)
- [ ] Average silhouette: _____ (target: > 0.5)
- [ ] Cross-zone density: ____%
- [ ] **Zone Structure**: [TOO ISOLATED / OPTIMAL / TOO COUPLED]

### 6. Diversity
- [ ] Shannon entropy: _____ (target: > 0.7)
- [ ] Simpson diversity: _____ (target: > 0.6)
- [ ] Skills with <2 faculty: _____
- [ ] **Cross-training Priority**: [None / Low / Medium / High]

### 7. Redundancy
- [ ] Services with N-1 pass: _____%
- [ ] Services with N-2 pass: _____%
- [ ] Single points of failure: _____
- [ ] **Redundancy Status**: [ADEQUATE / NEEDS IMPROVEMENT / CRITICAL]

### Composite Resilience Score
- [ ] **Overall Score**: _____ / 100 (target: > 75)

### Immediate Actions Required
1.
2.
3.

### Watch Items for Next Month
1.
2.
3.
```

---

## Integration with Existing Components

### How These Concepts Enhance Current Framework

| Current Component | Complex Systems Enhancement |
|------------------|---------------------------|
| **UtilizationMonitor** | + SOC avalanche predictor (early warning 2-4 weeks) |
| **ContingencyAnalyzer** | + Power law γ tracking (hub concentration) |
| **HubAnalyzer** | + Cascade simulation (impact of hub loss) |
| **BlastRadiusManager** | + Q-modularity (optimal zone isolation) |
| **HomeostasisMonitor** | + Edge of chaos balance (order/chaos tuning) |
| **DefenseInDepth** | + HOT analysis (fragility mapping) |
| **StigmergicScheduler** | + Emergence detection (implicit patterns) |
| **HubProtectionPlan** | + Diversity metrics (Shannon entropy) |

### Code Locations

Add new analyzers to:
```
backend/app/resilience/
├── soc_predictor.py          # NEW: Self-organized criticality
├── power_law_monitor.py      # NEW: Power law tracking
├── edge_analyzer.py           # NEW: Edge of chaos
├── hot_analyzer.py            # NEW: Robustness-fragility
├── modularity_metrics.py     # NEW: Q-modularity, silhouette
├── diversity_metrics.py      # NEW: Shannon, Simpson indices
└── service.py                # MODIFY: Integrate new analyzers
```

Add new models to:
```
backend/app/models/
└── complex_systems.py        # NEW: SOCMetrics, PowerLawHistory, EdgeBalance, etc.
```

Add new schemas to:
```
backend/app/schemas/
└── complex_systems.py        # NEW: Request/response schemas
```

Add new routes to:
```
backend/app/api/routes/
└── complex_systems.py        # NEW: GET /api/resilience/soc-risk, etc.
```

---

## Testing Strategy

### Unit Tests

```python
# tests/resilience/test_soc_predictor.py
def test_relaxation_time_calculation():
    """Test relaxation time increases near criticality."""
    swaps = generate_mock_swaps(approaching_criticality=True)
    predictor = SOCAvalanchePredictor()
    tau = predictor.calculate_relaxation_time(swaps)
    assert tau > 48, "Should detect long relaxation time"

def test_variance_spike_detection():
    """Test variance increase detection."""
    utilization = generate_mock_utilization(variance_spike=True)
    predictor = SOCAvalanchePredictor()
    result = predictor.detect_variance_spike(utilization)
    assert result["variance_increase_pct"] > 50

def test_autocorrelation_warning():
    """Test autocorrelation early warning."""
    time_series = generate_autocorrelated_series(ac1=0.75)
    predictor = SOCAvalanchePredictor()
    warning = predictor.check_autocorrelation(time_series)
    assert warning is not None
```

### Integration Tests

```python
# tests/integration/test_complex_systems_health_check.py
@pytest.mark.asyncio
async def test_health_check_includes_complex_systems_metrics(db):
    """Test health check includes all 7 complex systems metrics."""
    service = ResilienceService(db)

    faculty = await create_test_faculty(db, count=20)
    blocks = await create_test_blocks(db, count=100)
    assignments = await create_test_assignments(db, faculty, blocks)

    health = await service.check_health(faculty, blocks, assignments)

    # Verify all metrics present
    assert health.soc_avalanche_risk is not None
    assert health.power_law_gamma is not None
    assert health.edge_balance is not None
    assert health.hot_ratio is not None
    assert health.modularity_Q is not None
    assert health.skill_diversity is not None

    # Verify thresholds trigger warnings
    if health.soc_avalanche_risk > 0.6:
        assert any("avalanche" in action.lower() for action in health.immediate_actions)
```

### Load Tests

```python
# load-tests/complex-systems-metrics.js (k6)
export default function() {
  // Test SOC predictor performance
  let start = Date.now();
  let response = http.get('http://backend/api/resilience/soc-risk');
  let duration = Date.now() - start;

  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': () => duration < 500,  // Should be fast
    'includes risk_score': (r) => JSON.parse(r.body).risk_score !== undefined
  });

  sleep(1);
}
```

---

## Performance Considerations

### Computational Complexity

| Metric | Complexity | Frequency | Impact |
|--------|-----------|-----------|--------|
| Relaxation time | O(n) | 15 min | Low |
| Variance/AC1 | O(n) | 15 min | Low |
| Power law γ | O(n log n) | Monthly | Low |
| Q-modularity | O(n²) | Monthly | Medium |
| Shannon entropy | O(n) | Monthly | Low |
| Hub cascade simulation | O(n³) | Quarterly | High |

**Optimization strategies**:
1. **Cache expensive calculations**: Q-modularity, gamma exponent
2. **Incremental updates**: Variance and autocorrelation can be updated incrementally
3. **Background jobs**: Hub cascade simulation runs async (Celery)
4. **Sampling**: For large networks (>500 faculty), use sampling for Q calculation

### Caching Strategy

```python
from functools import lru_cache
from datetime import datetime, timedelta

class ComplexSystemsCache:
    """Cache expensive complex systems calculations."""

    def __init__(self):
        self.cache = {}
        self.cache_duration = {
            "power_law_gamma": timedelta(days=7),      # Weekly
            "q_modularity": timedelta(days=7),         # Weekly
            "shannon_entropy": timedelta(days=1),      # Daily
            "soc_risk": timedelta(minutes=15),         # Real-time
        }

    def get_cached(self, key, calculator_func):
        """Get cached value or calculate if stale."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            age = datetime.utcnow() - timestamp
            if age < self.cache_duration.get(key, timedelta(hours=1)):
                return value

        # Calculate and cache
        value = calculator_func()
        self.cache[key] = (value, datetime.utcnow())
        return value
```

---

## Database Schema Extensions

### New Tables (add to Alembic migration)

```sql
-- SOC metrics history
CREATE TABLE soc_metrics (
    id UUID PRIMARY KEY,
    calculated_at TIMESTAMP NOT NULL,
    relaxation_time_hours FLOAT NOT NULL,
    variance_baseline FLOAT NOT NULL,
    variance_recent FLOAT NOT NULL,
    lag1_autocorrelation FLOAT NOT NULL,
    risk_score FLOAT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    warnings TEXT[]
);

-- Power law history
CREATE TABLE power_law_metrics (
    id UUID PRIMARY KEY,
    calculated_at TIMESTAMP NOT NULL,
    gamma_exponent FLOAT NOT NULL,
    ks_test_pvalue FLOAT,
    follows_power_law BOOLEAN,
    fragility_index FLOAT
);

-- Edge of chaos measurements
CREATE TABLE edge_of_chaos_metrics (
    id UUID PRIMARY KEY,
    calculated_at TIMESTAMP NOT NULL,
    order_score FLOAT NOT NULL,
    chaos_score FLOAT NOT NULL,
    balance_score FLOAT NOT NULL,
    position VARCHAR(50) NOT NULL
);

-- Modularity measurements
CREATE TABLE modularity_metrics (
    id UUID PRIMARY KEY,
    calculated_at TIMESTAMP NOT NULL,
    q_modularity FLOAT NOT NULL,
    avg_silhouette FLOAT NOT NULL,
    cross_zone_density FLOAT NOT NULL,
    module_independence FLOAT NOT NULL
);

-- Diversity indices
CREATE TABLE diversity_metrics (
    id UUID PRIMARY KEY,
    calculated_at TIMESTAMP NOT NULL,
    shannon_entropy FLOAT NOT NULL,
    simpson_diversity FLOAT NOT NULL,
    skill_count INTEGER NOT NULL,
    single_point_skills TEXT[]
);
```

---

## Documentation Updates

Add to existing docs:

1. **`docs/architecture/complex-systems.md`**: Theoretical foundations
2. **`docs/operations/resilience-monitoring.md`**: Add complex systems metrics
3. **`docs/api/resilience-endpoints.md`**: New API endpoints
4. **`docs/user-guide/early-warnings.md`**: Understanding warning signals

---

## Success Criteria

### 3-Month Milestones

**Month 1**: Foundation
- [ ] All 7 metrics implemented
- [ ] Baseline measurements documented
- [ ] Integration tests passing

**Month 2**: Early Warnings
- [ ] SOC avalanche predictor active
- [ ] Critical slowing down alerts working
- [ ] At least 1 successful advance warning demonstrated

**Month 3**: Adaptive Systems
- [ ] Adaptive containment working (modularity adjusts with stress)
- [ ] Cross-training plans auto-generated from diversity metrics
- [ ] Composite resilience score calculated

### 6-Month Goals

- [ ] **50% reduction** in unexpected cascade failures
- [ ] **2-4 week advance warning** for major disruptions
- [ ] **Composite resilience score > 75**
- [ ] **Power law γ maintained** in optimal range (2.0-3.0)
- [ ] **Modularity Q stable** at 0.4-0.6
- [ ] **Skill diversity** improved to H > 0.7

---

## Contact & Resources

**Primary References**:
- Full research report: `/docs/research/complex-systems-scheduling-research.md`
- Implementation code: `/backend/app/resilience/`
- Tests: `/backend/tests/resilience/`

**Key Papers**:
- Self-Organized Criticality: Per Bak et al. (1987), "Self-organized criticality"
- Power Laws: Barabási & Albert (1999), "Emergence of scaling in random networks"
- Edge of Chaos: Carroll & Burton (2000), "Organizations and complexity"
- HOT: Carlson & Doyle (2002), "Complexity and robustness"

**Questions?** See `/docs/research/complex-systems-scheduling-research.md` Section 9 (References) for full bibliography.

---

*Last Updated: 2025-12-20*
*Version: 1.0*
*Status: Ready for Implementation*
