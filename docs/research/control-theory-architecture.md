# Control Theory Architecture for Residency Scheduling

**Visual architecture showing how control theory integrates with existing systems**

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       RESIDENCY SCHEDULING SYSTEM                            │
│                    (Medical Workforce Resilience)                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          TIER 1: EXISTING SYSTEMS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│  │   HOMEOSTASIS    │  │  LE CHATELIER    │  │    STIGMERGY     │         │
│  │  Feedback Loops  │  │   Equilibrium    │  │ Preference Trails│         │
│  │   Setpoints      │  │    Stress →      │  │   Pheromones     │         │
│  │ Allostatic Load  │  │  Compensation    │  │   Evaporation    │         │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘         │
│           │                     │                     │                     │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            │                     │                     │
┌───────────┼─────────────────────┼─────────────────────┼─────────────────────┐
│           │   TIER 2: CONTROL THEORY ENHANCEMENTS    │                     │
├───────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│           ▼                     ▼                     ▼                     │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                    PID CONTROLLERS                               │      │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                │      │
│  │  │Utilization │  │  Workload  │  │  Coverage  │                │      │
│  │  │    PID     │  │ Balance PID│  │    PID     │                │      │
│  │  │ Kp=10, Ki=0.5│ │ Kp=5, Ki=0.3│ │ Kp=12, Ki=0.8│             │      │
│  │  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘                │      │
│  │         │                │                │                      │      │
│  │         └────────────────┴────────────────┘                      │      │
│  │                          │                                       │      │
│  │                          ▼                                       │      │
│  │                ┌──────────────────┐                             │      │
│  │                │  Integrated with │                             │      │
│  │                │   Homeostasis    │◄────────┐                   │      │
│  │                │  Feedback Loops  │         │                   │      │
│  │                └──────────────────┘         │                   │      │
│  └─────────────────────────────────────────────┼───────────────────┘      │
│                                                 │                          │
│  ┌─────────────────────────────────────────────┼───────────────────┐      │
│  │              KALMAN FILTERS                 │                   │      │
│  │  ┌──────────────────┐  ┌─────────────────┐ │                   │      │
│  │  │    Workload      │  │ Schedule Health │ │                   │      │
│  │  │  KF (Noisy hrs)  │  │  EKF (Multiple  │ │                   │      │
│  │  │  Q=0.02, R=0.10  │  │   indicators)   │ │                   │      │
│  │  └────────┬─────────┘  └────────┬────────┘ │                   │      │
│  │           │                     │           │                   │      │
│  │           └──────────┬──────────┘           │                   │      │
│  │                      │                      │                   │      │
│  │                      ▼                      │                   │      │
│  │            ┌───────────────────┐            │                   │      │
│  │            │  Filtered State   │────────────┘                   │      │
│  │            │   Estimates       │ (Feed to PID & MPC)            │      │
│  │            └───────────────────┘                                │      │
│  └──────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐      │
│  │         MODEL PREDICTIVE CONTROL (MPC)                           │      │
│  │                                                                   │      │
│  │  Horizon: 4 weeks  │  Control: 2 weeks  │  Update: Weekly       │      │
│  │                                                                   │      │
│  │  ┌────────────────────────────────────────────────┐             │      │
│  │  │  Optimization Problem:                         │             │      │
│  │  │                                                 │             │      │
│  │  │  minimize: Σ[ Q·(coverage - target)²          │             │      │
│  │  │             + R·(utilization - target)²        │             │      │
│  │  │             + S·workload_variance              │             │      │
│  │  │             + P·preference_mismatch ]          │             │      │
│  │  │                                                 │             │      │
│  │  │  subject to:                                   │             │      │
│  │  │    • ACGME duty hours                          │             │      │
│  │  │    • Faculty availability                      │             │      │
│  │  │    • Supervision ratios                        │             │      │
│  │  │    • Preference trails (stigmergy)             │◄───────┐    │      │
│  │  └────────────────────────────────────────────────┘        │    │      │
│  │         │                                                   │    │      │
│  │         ▼                                                   │    │      │
│  │  ┌────────────────────┐                                   │    │      │
│  │  │  Execute Week 1-2  │                                   │    │      │
│  │  │  Discard Week 3-4  │                                   │    │      │
│  │  │  Re-optimize next  │                                   │    │      │
│  │  └────────────────────┘                                   │    │      │
│  └──────────────────────────────────────────────────────────┼─────┘      │
│                                                              │            │
│  ┌──────────────────────────────────────────────────────────┼─────┐      │
│  │           ADAPTIVE CONTROL                               │     │      │
│  │                                                           │     │      │
│  │  ┌─────────────────────────────────────────┐            │     │      │
│  │  │  Self-Tuning Constraint Weights         │            │     │      │
│  │  │                                          │            │     │      │
│  │  │  Observe: schedule_performance           │            │     │      │
│  │  │  Error: target - actual                  │            │     │      │
│  │  │  Update: weight += α·error               │            │     │      │
│  │  │                                          │            │     │      │
│  │  │  Coverage: 100 → 110 (need more)        │            │     │      │
│  │  │  Preference: 20 → 18 (slightly less)    │            │     │      │
│  │  └─────────────────────────────────────────┘            │     │      │
│  │                      │                                   │     │      │
│  │                      ▼                                   │     │      │
│  │  ┌─────────────────────────────────────────┐            │     │      │
│  │  │  Adaptive PID Gains (Gain Scheduling)   │            │     │      │
│  │  │                                          │            │     │      │
│  │  │  Normal:   Kp=10, Ki=0.5, Kd=2.0       │            │     │      │
│  │  │  Stressed: Kp=15, Ki=1.0, Kd=3.0       │            │     │      │
│  │  │  Crisis:   Kp=20, Ki=2.0, Kd=1.0       │────────────┘     │      │
│  │  │  Recovery: Kp=5,  Ki=0.3, Kd=4.0       │                  │      │
│  │  └─────────────────────────────────────────┘                  │      │
│  └────────────────────────────────────────────────────────────────┘      │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│              TIER 3: CRISIS & ROBUSTNESS LAYER                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │              SLIDING MODE CONTROL                             │        │
│  │         (Activated during crisis conditions)                  │        │
│  │                                                               │        │
│  │  Sliding Surface: s = λ·e + ė = 0                           │        │
│  │                                                               │        │
│  │  ┌────────────────────────────────────────────────┐         │        │
│  │  │  Primary Surface (CRITICAL):                   │         │        │
│  │  │    Coverage ≥ 85%                              │         │        │
│  │  │    Control: u = -K·sign(coverage - 0.85)      │         │        │
│  │  └────────────────────────────────────────────────┘         │        │
│  │                                                               │        │
│  │  ┌────────────────────────────────────────────────┐         │        │
│  │  │  Secondary Surface (HIGH):                     │         │        │
│  │  │    Utilization ≤ 80%                           │         │        │
│  │  │    Control: u = -K·sign(util - 0.80)          │         │        │
│  │  └────────────────────────────────────────────────┘         │        │
│  │                                                               │        │
│  │  Advantages:                                                 │        │
│  │    • Finite-time convergence (fast)                         │        │
│  │    • Robust to faculty absences                             │        │
│  │    • Guaranteed bounds                                       │        │
│  └──────────────────────────────────────────────────────────────┘        │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────┐        │
│  │              SMITH PREDICTOR                                  │        │
│  │       (Compensation for delayed feedback)                     │        │
│  │                                                               │        │
│  │  Problem: ACGME violations measured over 4-week windows      │        │
│  │           (Feedback delayed by up to 4 weeks)                │        │
│  │                                                               │        │
│  │  ┌────────────────────────────────────────────────┐         │        │
│  │  │  Model Prediction (No Delay):                  │         │        │
│  │  │    ŷ(t) = predict_hours(current_schedule)      │         │        │
│  │  └──────────────────┬─────────────────────────────┘         │        │
│  │                     │                                         │        │
│  │  ┌─────────────────▼──────────────────────────────┐         │        │
│  │  │  Delayed Measurement Correction:               │         │        │
│  │  │    y_corrected = ŷ(t) + [y(t-4wk) - ŷ(t-4wk)] │         │        │
│  │  │                          └─────┬─────┘          │         │        │
│  │  │                          Model error            │         │        │
│  │  └────────────────────────────────────────────────┘         │        │
│  │                     │                                         │        │
│  │                     ▼                                         │        │
│  │  ┌────────────────────────────────────────────────┐         │        │
│  │  │  Early Warning (2-3 weeks in advance):         │         │        │
│  │  │    if predicted_hours > 80/week:               │         │        │
│  │  │      preemptive_action()                       │         │        │
│  │  └────────────────────────────────────────────────┘         │        │
│  └──────────────────────────────────────────────────────────────┘        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────┐
│                    DATA FLOW & INTEGRATION                                │
└───────────────────────────────────────────────────────────────────────────┘

  Raw Measurements          State Estimation         Control         Actuation
       │                          │                     │                │
       ▼                          ▼                     ▼                ▼
┌─────────────┐          ┌─────────────┐       ┌─────────────┐   ┌──────────┐
│ Noisy Hours │          │   Kalman    │       │     PID     │   │ Add/     │
│ Self-reports│─────────►│   Filter    │──────►│ Controller  │──►│ Remove   │
│ System logs │          │             │       │             │   │ Assign.  │
│ Peer est.   │          └─────────────┘       └─────────────┘   └──────────┘
└─────────────┘                 │                     │                │
       │                        │                     │                │
       │                        │                     │                │
       ▼                        ▼                     ▼                ▼
┌─────────────┐          ┌─────────────┐       ┌─────────────┐   ┌──────────┐
│ Schedule    │          │   Smith     │       │   Adaptive  │   │ Adjust   │
│ Performance │          │  Predictor  │       │   Weights   │   │ Weights  │
│ Metrics     │─────────►│ (Delayed FB)│──────►│             │──►│ for MPC  │
└─────────────┘          └─────────────┘       └─────────────┘   └──────────┘
       │                        │                     │                │
       │                        │                     │                │
       ▼                        ▼                     ▼                ▼
┌─────────────┐          ┌─────────────┐       ┌─────────────┐   ┌──────────┐
│ Crisis      │          │   Sliding   │       │     MPC     │   │ Generate │
│ Detected?   │─────────►│    Mode     │──────►│  Scheduler  │──►│ 4-week   │
│             │          │  (Robust)   │       │             │   │ Schedule │
└─────────────┘          └─────────────┘       └─────────────┘   └──────────┘

```

---

## Control Modes by System State

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM STATE DIAGRAM                         │
└─────────────────────────────────────────────────────────────────┘

                    Utilization (%)
                    0    25    50    75    80    90   100
    Coverage (%)    ├─────┼─────┼─────┼─────┼─────┼─────┤
         100%  ─────┼─────┼─────┼─────┼─────┼─────┼─────┤
                    │                 │                  │
          95%  ─────┼─────┼─────┼─────┼─────┼─────┼─────┤
                    │        NORMAL   │   STRESSED       │
                    │      (PID + MPC)│  (Adaptive PID)  │
          85%  ─────┼─────┼─────┼─────┼─────┼─────┼─────┤
                    │                 │                  │
                    │   DEGRADED      │    CRISIS        │
          75%  ─────┼   (Adaptive)    │ (Sliding Mode)   ┤
                    │                 │                  │
                    │                 │                  │
          50%  ─────┼─────┼─────┼─────┼─────┼─────┼─────┤
                    │    EMERGENCY (Sliding Mode + Fallback)   │
           0%  ─────┴─────┴─────┴─────┴─────┴─────┴─────┘

Control Strategy Selection:
┌──────────────┬────────────────────────────────────────────┐
│ NORMAL       │ • PID for utilization tracking            │
│              │ • MPC for weekly schedule optimization    │
│              │ • Kalman filtering for all measurements   │
├──────────────┼────────────────────────────────────────────┤
│ STRESSED     │ • Adaptive PID (higher gains)             │
│              │ • MPC with tighter constraints            │
│              │ • Increase measurement frequency          │
├──────────────┼────────────────────────────────────────────┤
│ DEGRADED     │ • Adaptive control (rapid weight adjust)  │
│              │ • Smith Predictor for early warnings      │
│              │ • Prepare fallback schedules              │
├──────────────┼────────────────────────────────────────────┤
│ CRISIS       │ • Sliding Mode Control (robust)           │
│              │ • Hard constraint enforcement             │
│              │ • Override preferences                    │
├──────────────┼────────────────────────────────────────────┤
│ EMERGENCY    │ • Sliding Mode + Fallback activation      │
│              │ • Load shedding (sacrifice hierarchy)     │
│              │ • Manual override enabled                 │
└──────────────┴────────────────────────────────────────────┘
```

---

## Information Flow Timeline

```
Week 1: Normal Operations
─────────────────────────────────────────────────────
07:00  Kalman Filter updates overnight (workload estimates)
09:00  PID checks utilization → within bounds → no action
12:00  MPC runs weekly optimization for weeks 2-5
       ├─ Uses filtered state estimates (Kalman)
       ├─ Incorporates preference trails (Stigmergy)
       └─ Adapts weights from last week performance
14:00  Schedule published for week 2
18:00  Smith Predictor updates ACGME violation forecast


Week 2: Stressed Conditions
─────────────────────────────────────────────────────
Monday    Faculty calls in sick (stress event)
          ├─ Le Chatelier: Apply stress (-20% capacity)
          ├─ Homeostasis: Trigger corrective action
          └─ PID: Detects utilization spike

Tuesday   Adaptive control switches to "stressed" regime
          ├─ PID gains: Kp=10→15, Ki=0.5→1.0
          └─ MPC: Tightens constraints

Wed-Fri   MPC re-optimizes daily (instead of weekly)
          ├─ Kalman: Filters noisy stress indicators
          └─ Smith: Predicts ACGME risk 3 weeks ahead


Week 3: Crisis Mode
─────────────────────────────────────────────────────
Monday    Coverage drops to 82% (below 85% threshold)
          CRISIS MODE ACTIVATED

          ├─ Sliding Mode Control takes over
          │  └─ Forces coverage back to surface (85%)
          │
          ├─ Defense-in-depth: Level ORANGE
          │  └─ Activate sacrifice hierarchy
          │
          └─ Fallback schedules prepared

Tue-Thu   Sliding Mode maintains coverage surface
          ├─ Rapid control switching (daily)
          ├─ Ignores preferences (survival mode)
          └─ Guaranteed 85% coverage maintained

Friday    Coverage restored to 87%
          Transition back to Adaptive PID


Week 4: Recovery
─────────────────────────────────────────────────────
Monday    Smith Predictor validates predictions
          ├─ Compare predicted vs actual hours
          └─ Update model for future predictions

          Adaptive control learns from crisis
          ├─ Adjust weights based on performance
          └─ Update regime thresholds

Wed-Fri   Gradual return to normal operations
          ├─ PID gains slowly return to normal
          ├─ MPC horizon extends back to 4 weeks
          └─ Preference considerations restored
```

---

## Performance Metrics Dashboard

```
┌────────────────────────────────────────────────────────────────┐
│                  CONTROL SYSTEM HEALTH                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  PID Controllers:                        Status                │
│  ├─ Utilization PID          [●●●●●○○○○○]  ⚠ Slight oscillation│
│  ├─ Workload Balance PID     [●●●●●●●●○○]  ✓ Tracking well    │
│  └─ Coverage PID              [●●●●●●●●●●]  ✓ At setpoint     │
│                                                                │
│  Kalman Filters:                                               │
│  ├─ Workload KF              Uncertainty: ±2.3 hrs            │
│  │                           Innovation: 0.8 (good)            │
│  └─ Health EKF               Uncertainty: ±0.05               │
│                              Innovation: 0.12 (acceptable)     │
│                                                                │
│  MPC Scheduler:                                                │
│  ├─ Last solve time:         18.3 seconds                     │
│  ├─ Objective achieved:      94.2%                            │
│  ├─ Constraints violated:    0                                │
│  └─ Coverage forecast:       [95%, 93%, 94%, 95%]            │
│                                                                │
│  Adaptive Control:                                             │
│  ├─ Coverage weight:         100 → 110 (adapting up)          │
│  ├─ Preference weight:       20 → 18 (adapting down)          │
│  ├─ Convergence:             83% (nearly converged)           │
│  └─ Performance error:       -0.03 (slight undershoot)        │
│                                                                │
│  Sliding Mode:               [STANDBY]                         │
│  └─ Ready for crisis activation                               │
│                                                                │
│  Smith Predictor:                                              │
│  ├─ ACGME violation risk:    Low (12% in 4 weeks)             │
│  ├─ Model accuracy (MAE):    3.2 hours                        │
│  └─ Prediction confidence:   88%                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority Matrix

```
       │ Implementation Complexity
Value  │  Low      Medium     High
───────┼────────────────────────────────
High   │  PID      Kalman     MPC
       │  ✓        ✓          ○
       │
Medium │  Adaptive            Smith
       │  ○                   △
       │
Low    │                      Sliding
       │                      Mode △
       │
───────┴────────────────────────────────

Legend:
✓ = Implement first (high value, low complexity)
○ = Implement second (high value, medium complexity)
△ = Implement last (specialized use cases)

Recommended Order:
1. PID Controllers (Week 1-2) - Immediate value
2. Kalman Filters (Week 2-3) - Enhances everything
3. MPC Integration (Week 3-4) - Major scheduling improvement
4. Adaptive Weights (Week 5) - Long-term optimization
5. Smith Predictor (Week 6) - ACGME early warning
6. Sliding Mode (Week 7) - Crisis robustness
```

---

## Key Takeaways

### For System Designers

1. **Layered Control:** Normal → Stressed → Crisis (PID → Adaptive → Sliding)
2. **State Estimation First:** Kalman filters improve all downstream control
3. **Complementary, Not Competing:** Each technique addresses different needs
4. **Test Thoroughly:** Control systems can destabilize without proper tuning

### For Operators

1. **Monitor Diagnostics:** Watch for oscillation, saturation, divergence
2. **Trust the Automation:** Let controllers handle normal variations
3. **Override When Needed:** Manual control available for emergencies
4. **Learn from History:** Adaptive control improves over time

### For Schedulers

1. **MPC Looks Ahead:** Plans 4 weeks, executes 2 weeks
2. **Preferences Matter:** Stigmergy trails integrated into MPC objective
3. **ACGME Predictive:** Smith Predictor warns 3-4 weeks early
4. **Robust in Crisis:** Sliding mode guarantees minimum coverage

---

## Next Steps

1. **Review main research document** (`exotic-control-theory-for-scheduling.md`)
2. **Start with PID implementation** (easiest, highest immediate value)
3. **Add Kalman filters** (improves measurement quality for everything)
4. **Validate on historical data** before deploying to production
5. **Monitor and tune** based on actual system performance
6. **Iterate and improve** using adaptive control principles

**Remember:** Control theory is powerful but requires careful engineering. Start simple, validate thoroughly, add complexity only when proven necessary.
