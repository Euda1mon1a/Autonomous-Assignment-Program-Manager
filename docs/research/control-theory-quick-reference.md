# Control Theory Quick Reference for Scheduling

**Quick decision guide for applying control theory to scheduling problems**

---

## Problem → Solution Matrix

| Your Problem | Use This | Why | Implementation Complexity |
|--------------|----------|-----|--------------------------|
| Utilization keeps drifting from 75% target | **PID Controller** | Automatic correction of sustained deviations | ⭐ Easy |
| Workload hours reports are inconsistent/noisy | **Kalman Filter** | Optimal estimate from multiple noisy sources | ⭐⭐ Medium |
| Need to optimize 4-week schedule with constraints | **Model Predictive Control** | Handles constraints naturally, looks ahead | ⭐⭐⭐ Hard |
| Optimal constraint weights keep changing | **Adaptive Control** | Self-tunes parameters from performance | ⭐⭐ Medium |
| Must maintain coverage during crisis | **Sliding Mode Control** | Robust to disturbances, guaranteed bounds | ⭐⭐⭐ Hard |
| ACGME violations only visible after 4 weeks | **Smith Predictor** | Predicts violations before they happen | ⭐⭐⭐ Hard |

---

## One-Liner Explanations

### PID Controller
**"Auto-pilot for metrics"** - Automatically adjusts system to maintain target values (like cruise control).

**Math in 10 seconds:**
```
correction = Kp·(current_error) + Ki·(accumulated_error) + Kd·(error_rate)
```

**When to use:** Any time you have a target value and want automatic tracking.

---

### Kalman Filter
**"Smart averaging under uncertainty"** - Optimally combines noisy measurements with predictions.

**Math in 10 seconds:**
```
best_estimate = prediction + K·(measurement - prediction)
where K = uncertainty_in_prediction / (uncertainty_in_prediction + uncertainty_in_measurement)
```

**When to use:** When measurements are noisy or incomplete (self-reported hours, surveys).

---

### Model Predictive Control
**"Chess player for scheduling"** - Plans multiple moves ahead, then executes first move and replans.

**Math in 10 seconds:**
```
Optimize: schedule for next 4 weeks
Subject to: all ACGME constraints
Execute: only first 2 weeks
Repeat: with updated information
```

**When to use:** Complex multi-objective optimization with constraints.

---

### Adaptive Control
**"Learning thermostat"** - Adjusts its own parameters based on performance.

**Math in 10 seconds:**
```
parameter_adjustment = learning_rate · performance_error
```

**When to use:** When optimal settings change over time (seasonal patterns, staff changes).

---

### Sliding Mode Control
**"Emergency override"** - Rapidly forces system to safe state and keeps it there.

**Math in 10 seconds:**
```
if (coverage < minimum):
    control = MAXIMUM  # Add all possible assignments
else:
    control = maintain
```

**When to use:** Crisis situations requiring guaranteed performance.

---

### Smith Predictor
**"Crystal ball for delayed feedback"** - Predicts current state from delayed measurements.

**Math in 10 seconds:**
```
current_state_estimate = model_prediction + (old_measurement - old_prediction)
```

**When to use:** When feedback is delayed (4-week ACGME windows, monthly surveys).

---

## Combination Recipes

### Recipe 1: "Smooth Autopilot"
**Problem:** Noisy utilization data with target tracking
**Solution:** Kalman Filter → PID Controller
```python
# Filter noisy measurement
estimated_util = kalman.update(noisy_measurement)
# Control on filtered value
action = pid.update(estimated_util)
```

### Recipe 2: "Adaptive Planner"
**Problem:** Multi-week scheduling with changing priorities
**Solution:** MPC + Adaptive Weights
```python
# Adapt weights from last schedule's performance
weights = adaptive.update(last_schedule_metrics)
# Use adapted weights in MPC
mpc.weights = weights
schedule = mpc.generate(horizon=4_weeks)
```

### Recipe 3: "Crisis Mode with Learning"
**Problem:** Emergency coverage with post-crisis improvement
**Solution:** Sliding Mode (crisis) + Adaptive (recovery)
```python
if crisis_detected:
    action = sliding_mode.update(coverage)  # Robust control
else:
    action = adaptive_pid.update(coverage)  # Learning control
```

### Recipe 4: "Early Warning System"
**Problem:** Predict ACGME violations before they happen
**Solution:** Smith Predictor + Kalman Filter
```python
# Filter noisy hours data
estimated_hours = kalman.update(reported_hours)
# Predict violation 4 weeks ahead
will_violate = smith.predict(estimated_hours, planned_schedule)
if will_violate:
    preemptive_action()
```

---

## Tuning Cheat Sheet

### PID Tuning Rules of Thumb

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Slow response | Kp too low | Increase Kp by 50% |
| Oscillation | Kp too high or Kd too low | Decrease Kp or increase Kd |
| Never reaches target | Ki too low | Increase Ki slowly |
| Overshoots badly | Kd too low | Increase Kd |

**Safe starting point:** Kp=1.0, Ki=0.0, Kd=0.0, then add Ki and Kd.

### Kalman Filter Tuning

| Parameter | Set to... | Reasoning |
|-----------|-----------|-----------|
| **Q (Process Noise)** | 10% of expected variance | Trust model moderately |
| **R (Measurement Noise)** | Sample variance from data | Use actual noise level |
| **P0 (Initial Uncertainty)** | 2× expected variance | Conservative start |

**Rule:** If filter is sluggish, increase Q. If filter is jumpy, increase R.

### MPC Tuning

| Parameter | Recommended | Trade-off |
|-----------|-------------|-----------|
| **Horizon** | 4 weeks | Longer = better but slower |
| **Control Horizon** | 2 weeks | Shorter = more responsive |
| **Solve Time** | 30 seconds | Real-time limit |
| **Coverage Weight** | 100 | Always highest priority |

---

## Implementation Checklist

### Before Implementing Any Control

- [ ] Define clear setpoint/target (what value should system maintain?)
- [ ] Identify measurable process variable (what can you observe?)
- [ ] Determine control action (what can you change?)
- [ ] Estimate typical disturbances (what pushes you off target?)
- [ ] Define update frequency (how often can you measure and act?)

### For PID Controllers

- [ ] Setpoint defined and justified
- [ ] Measurement available at regular intervals
- [ ] Control action can be quantified (e.g., "add N assignments")
- [ ] Integral windup protection implemented
- [ ] Tuning procedure documented
- [ ] Oscillation detection in place

### For Kalman Filters

- [ ] System dynamics model created (how state evolves)
- [ ] Measurement noise characterized from data
- [ ] Process noise estimated
- [ ] Multiple measurement sources identified
- [ ] Confidence intervals tracked
- [ ] Model validation on historical data

### For MPC

- [ ] Prediction horizon chosen (2-8 weeks)
- [ ] Control horizon chosen (1-4 weeks)
- [ ] All hard constraints encoded
- [ ] Objective function weights tuned
- [ ] Solve time acceptable (<60s for real-time)
- [ ] Fallback solver if optimization fails

---

## Common Pitfalls and Solutions

### Pitfall 1: "Set and Forget" PID
**Problem:** Tune PID once, never check again
**Solution:** Monitor diagnostics (oscillation, saturation), retune seasonally

### Pitfall 2: "Perfect Model" Assumption
**Problem:** Kalman filter or MPC assumes model is perfect
**Solution:** Validate model on data, update periodically, monitor innovation

### Pitfall 3: "Too Many Controllers"
**Problem:** Five different controllers fighting each other
**Solution:** Use hierarchical control - one master, others subordinate

### Pitfall 4: "Ignoring Delays"
**Problem:** Measure today, assume it reflects yesterday's action
**Solution:** Smith Predictor or account for delay in model

### Pitfall 5: "Over-Tuning"
**Problem:** Constantly tweaking gains chasing perfection
**Solution:** Define "good enough" performance, stop when reached

---

## Testing Strategies

### Test Your PID

```python
def test_pid_step_response():
    """PID should reach setpoint after step change."""
    pid = PIDController(setpoint=0.75)
    value = 0.50  # Start away from setpoint

    for i in range(50):
        control = pid.update(value)
        value += control['signal'] * 0.01  # Simplified plant

    assert abs(value - 0.75) < 0.05  # Within 5%
```

### Test Your Kalman Filter

```python
def test_kalman_noise_reduction():
    """Kalman should reduce measurement noise."""
    kf = KalmanFilter()
    true_value = 60.0

    measurements = [true_value + random.normal(0, 5) for _ in range(20)]
    estimates = [kf.update(m)['estimate'] for m in measurements]

    # Estimate variance should be lower than measurement variance
    assert np.var(estimates[-10:]) < np.var(measurements[-10:])
```

### Test Your MPC

```python
def test_mpc_respects_constraints():
    """MPC should never violate hard constraints."""
    mpc = MPCScheduler()
    schedule = mpc.generate(horizon=4_weeks, constraints=acgme_rules)

    # Validate all constraints
    for constraint in acgme_rules.hard_constraints:
        assert constraint.validate(schedule).satisfied
```

---

## Further Reading

### Beginner
- **"Feedback Control of Dynamic Systems" by Franklin et al.** - Classic textbook, very readable
- **"Model Predictive Control" by Camacho & Bordons** - Practical MPC introduction

### Intermediate
- **"Optimal State Estimation" by Simon** - Kalman filters explained clearly
- **"Adaptive Control" by Åström & Wittenmark** - Comprehensive adaptive control

### Advanced
- **"Sliding Mode Control and Observation" by Shtessel et al.** - Modern SMC techniques
- **"Predictive Control for Linear and Hybrid Systems" by Borrelli et al.** - State-of-the-art MPC

### For This Project
- **Start with:** PID section in main report
- **Then read:** Kalman filter section
- **Finally try:** MPC integration examples

---

## Contact and Support

For questions about implementing these techniques in the scheduling system:

1. Review the main research report (`exotic-control-theory-for-scheduling.md`)
2. Check existing implementations in `/backend/app/resilience/`
3. Look for similar patterns in homeostasis and Le Chatelier modules

**Remember:** Start simple (PID), validate thoroughly, then add complexity only if needed.
