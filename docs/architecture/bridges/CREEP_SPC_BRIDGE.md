# Creep/Fatigue → SPC Bridge Specification

> **Bridge ID:** `CREEP_SPC_001`
> **Version:** 1.0
> **Status:** Implementation-Ready
> **Last Updated:** 2025-12-26

---

## Executive Summary

This bridge connects Materials Science creep/fatigue analysis with Statistical Process Control monitoring to provide **predictive burnout detection** through control chart analysis of cumulative damage accumulation.

**Key Integration:** Creep fatigue damage (Miner's Rule) is tracked as a time-series metric on SPC control charts, triggering Western Electric Rule violations when approaching material failure thresholds.

**Clinical Value:**
- **Early Warning:** Detect accelerating burnout 4-8 weeks before clinical manifestation
- **Trend Analysis:** Identify gradual vs. sudden damage accumulation patterns
- **Intervention Timing:** Precise alerts for when workload reduction is needed
- **Objective Metrics:** Replace subjective burnout assessment with quantitative SPC analysis

---

## Mathematical Foundation

### 1. Larson-Miller Parameter (Creep Analysis)

**Formula:**
```
LMP = workload_fraction × (C + log₁₀(duration_days))
```

Where:
- `workload_fraction` = Current workload as fraction of capacity (0.0-1.0)
- `duration_days` = Duration of sustained workload
- `C` = Material constant (default: 20.0)

**Thresholds:**
- `FAILURE_THRESHOLD = 45.0` → High burnout risk
- `SAFE_LMP = 31.5` → Sustainable workload (70% of failure)

**Creep Stages:**
| Stage | LMP Range | Percentage of Failure | Clinical Interpretation |
|-------|-----------|----------------------|-------------------------|
| **PRIMARY** | 0 - 22.5 | 0% - 50% | Adaptation phase, strain rate decreasing |
| **SECONDARY** | 22.5 - 36.0 | 50% - 80% | Steady-state, sustainable performance |
| **TERTIARY** | 36.0 - 45.0+ | 80% - 100%+ | Accelerating damage, approaching burnout |

### 2. Miner's Rule (Cumulative Fatigue Damage)

**Formula:**
```
D = Σ(n_i / N_i)
```

Where:
- `D` = Cumulative damage (failure occurs when D ≥ 1.0)
- `n_i` = Number of cycles at stress level i
- `N_i` = Cycles to failure at stress level i (from S-N curve)

**S-N Curve (Cycles to Failure):**
```
N = A × S^b
```
- `A` = Material constant (1×10¹⁰)
- `S` = Stress amplitude (0.0-1.0)
- `b` = Exponent (-3.0, typical for metals)

**Damage Interpretation:**
| Damage (D) | Remaining Life | Clinical State |
|------------|----------------|----------------|
| 0.0 - 0.3 | 70% - 100% | Healthy, primary creep |
| 0.3 - 0.5 | 50% - 70% | Caution zone, monitoring needed |
| 0.5 - 0.7 | 30% - 50% | Warning zone, intervention planning |
| 0.7 - 0.9 | 10% - 30% | Danger zone, immediate action |
| 0.9 - 1.0 | 0% - 10% | Critical, burnout imminent |
| > 1.0 | Negative | **FAILURE - Burnout occurred** |

### 3. SPC Control Limits

**Standard Control Chart:**
```
μ = Target damage level (centerline)
UCL₃σ = μ + 3σ  (Upper Control Limit)
LCL₃σ = μ - 3σ  (Lower Control Limit)
UCL₂σ = μ + 2σ  (Upper Warning Limit)
LCL₂σ = μ - 2σ  (Lower Warning Limit)
UCL₁σ = μ + 1σ  (Zone boundary)
LCL₁σ = μ - 1σ  (Zone boundary)
```

**For Creep Damage Monitoring:**
- `μ` (centerline) = 0.3 (target damage level for healthy residents)
- `σ` (standard deviation) = 0.15 (estimated from historical data)
- `UCL₃σ` = 0.3 + 3(0.15) = **0.75** (critical threshold)
- `UCL₂σ` = 0.3 + 2(0.15) = **0.60** (warning threshold)
- `UCL₁σ` = 0.3 + 1(0.15) = **0.45** (caution threshold)

### 4. Bridge Formula

**Mapping Creep Damage to Control Chart:**
```python
control_point = {
    "timestamp": datetime.now(),
    "value": D,  # Miner's damage from creep analysis
    "resident_id": resident_uuid,
    "metadata": {
        "lmp": larson_miller_parameter,
        "creep_stage": creep_stage.value,
        "strain_rate": strain_rate,
        "workload_fraction": workload_fraction
    }
}
```

**Time Series Tracking:**
- Sample frequency: Weekly snapshots of damage D
- Rolling window: Last 12 weeks for Western Electric Rules
- Trend detection: Linear regression on D over time (dD/dt)

---

## Creep Stage → SPC Alert Mapping

### Decision Matrix

| Creep Stage | Damage (D) | SPC Threshold | Western Electric Rule | Alert Severity | Response Time |
|-------------|------------|---------------|----------------------|----------------|---------------|
| **PRIMARY** | 0.0 - 0.3 | Below μ | No violation | None | Routine monitoring |
| **SECONDARY (Early)** | 0.3 - 0.45 | μ to μ+1σ | Rule 4 potential | INFO | Watch for trends |
| **SECONDARY (Late)** | 0.45 - 0.60 | μ+1σ to μ+2σ | Rule 3 check | WARNING | Intervention planning |
| **TERTIARY (Early)** | 0.60 - 0.75 | μ+2σ to μ+3σ | Rule 2 violation | **WARNING** | Schedule adjustment |
| **TERTIARY (Late)** | 0.75 - 1.0 | Beyond μ+3σ | **Rule 1 violation** | **CRITICAL** | Immediate intervention |
| **FAILURE** | > 1.0 | Well beyond UCL | Rule 1 + clinical alert | **EMERGENCY** | Crisis response |

### Western Electric Rule Triggers

#### Rule 1: One point beyond 3σ
```python
if D > (centerline + 3 * sigma):  # D > 0.75
    trigger_rule_1_alert(
        severity="CRITICAL",
        message=f"Damage {D:.2f} exceeds 3σ limit (0.75). Burnout imminent."
    )
```

#### Rule 2: 2 of 3 consecutive points beyond 2σ
```python
window_3_weeks = damage_values[-3:]
beyond_2sigma = [d for d in window_3_weeks if d > (centerline + 2 * sigma)]  # > 0.60

if len(beyond_2sigma) >= 2:
    trigger_rule_2_alert(
        severity="WARNING",
        message=f"2 of 3 weeks with D > 0.60. Sustained overload detected."
    )
```

#### Rule 3: 4 of 5 consecutive points beyond 1σ
```python
window_5_weeks = damage_values[-5:]
beyond_1sigma = [d for d in window_5_weeks if d > (centerline + 1 * sigma)]  # > 0.45

if len(beyond_1sigma) >= 4:
    trigger_rule_3_alert(
        severity="WARNING",
        message=f"4 of 5 weeks with D > 0.45. Gradual damage accumulation."
    )
```

#### Rule 4: 8 consecutive points on same side of centerline
```python
window_8_weeks = damage_values[-8:]
above_center = [d for d in window_8_weeks if d > centerline]  # > 0.30

if len(above_center) == 8:
    trigger_rule_4_alert(
        severity="INFO",
        message=f"8 weeks above baseline (0.30). Systematic workload increase."
    )
```

---

## Data Flow Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESIDENT SCHEDULE DATA                      │
│                                                                 │
│  - Weekly workload hours                                        │
│  - Rotation stress levels                                       │
│  - Sustained workload duration                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│             CreepFatigueModel.assess_combined_risk()            │
│                                                                 │
│  Inputs:                                                        │
│    - resident_id: UUID                                          │
│    - sustained_workload: float (0.0-1.0)                        │
│    - duration: timedelta                                        │
│    - rotation_stresses: list[float]                             │
│                                                                 │
│  Calculations:                                                  │
│    1. LMP = calculate_larson_miller(workload, duration)         │
│    2. stage = determine_creep_stage(LMP)                        │
│    3. D = calculate_fatigue_damage(rotation_stresses)           │
│    4. strain_rate = calculate_strain_rate(workload_history)     │
│                                                                 │
│  Outputs:                                                       │
│    - creep_analysis: CreepAnalysis                              │
│    - fatigue_curve: FatigueCurve                                │
│    - cumulative_damage: D                                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 CreepSPCBridge.map_to_control_chart()           │
│                                                                 │
│  Transformation:                                                │
│    damage_point = {                                             │
│      "timestamp": datetime.now(),                               │
│      "value": D,                                                │
│      "resident_id": resident_id,                                │
│      "metadata": {                                              │
│        "lmp": LMP,                                              │
│        "creep_stage": stage,                                    │
│        "strain_rate": strain_rate                               │
│      }                                                          │
│    }                                                            │
│                                                                 │
│  Storage:                                                       │
│    - Append to time_series_buffer (rolling 12-week window)      │
│    - Persist to database (damage_history table)                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│          WorkloadControlChart.detect_western_electric_violations()│
│                                                                 │
│  Inputs:                                                        │
│    - resident_id: UUID                                          │
│    - damage_values: list[float] (last 12 weeks of D)            │
│                                                                 │
│  Western Electric Rule Checks:                                  │
│    ✓ Rule 1: D > UCL₃σ (0.75)                                  │
│    ✓ Rule 2: 2/3 weeks D > UCL₂σ (0.60)                        │
│    ✓ Rule 3: 4/5 weeks D > UCL₁σ (0.45)                        │
│    ✓ Rule 4: 8 consecutive weeks D > centerline (0.30)         │
│                                                                 │
│  Outputs:                                                       │
│    - alerts: list[SPCAlert]                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Alert Escalation & Notification                 │
│                                                                 │
│  CRITICAL (Rule 1):                                             │
│    - Immediate email to Program Director                        │
│    - Dashboard red alert                                        │
│    - Auto-schedule intervention meeting                         │
│                                                                 │
│  WARNING (Rule 2/3):                                            │
│    - Email to Chief Resident                                    │
│    - Dashboard yellow/orange alert                              │
│    - Schedule review within 48 hours                            │
│                                                                 │
│  INFO (Rule 4):                                                 │
│    - Dashboard notification                                     │
│    - Weekly report inclusion                                    │
│    - Trend monitoring                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Sequence Diagram

```
Celery Beat   CreepFatigue    CreepSPCBridge   SPCMonitor   NotificationService
    │              │                 │              │                │
    │ Weekly job   │                 │              │                │
    ├─────────────>│                 │              │                │
    │              │                 │              │                │
    │              │ calculate_damage()             │                │
    │              │────────┐        │              │                │
    │              │        │        │              │                │
    │              │<───────┘        │              │                │
    │              │ D = 0.72        │              │                │
    │              │                 │              │                │
    │              │ map_to_chart()  │              │                │
    │              ├────────────────>│              │                │
    │              │                 │              │                │
    │              │                 │ add_point(D) │                │
    │              │                 ├─────────────>│                │
    │              │                 │              │                │
    │              │                 │              │ check_rules()  │
    │              │                 │              ├────────┐       │
    │              │                 │              │        │       │
    │              │                 │              │<───────┘       │
    │              │                 │              │ Rule 2 violation│
    │              │                 │              │                │
    │              │                 │   alerts[]   │                │
    │              │                 │<─────────────┤                │
    │              │                 │              │                │
    │              │                 │              │ send_alert()   │
    │              │                 │              ├───────────────>│
    │              │                 │              │                │
    │              │                 │              │   Email sent   │
    │              │                 │              │<───────────────┤
    │              │                 │              │                │
```

---

## Integration with Time Series

### Weekly Snapshot Collection

```python
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from app.resilience.creep_fatigue import CreepFatigueModel, FatigueCurve
from app.resilience.spc_monitoring import WorkloadControlChart, SPCAlert


class CreepSPCBridge:
    """
    Bridge between Creep/Fatigue analysis and SPC monitoring.

    Tracks cumulative damage over time and triggers SPC alerts
    when Western Electric Rules are violated.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.creep_model = CreepFatigueModel()

        # Control chart for damage monitoring
        # Centerline = 0.3 (healthy baseline)
        # Sigma = 0.15 (15% variation)
        self.damage_chart = WorkloadControlChart(
            target_hours=0.3,  # Repurpose as damage centerline
            sigma=0.15
        )

    async def collect_weekly_snapshot(
        self,
        resident_id: UUID,
        workload_fraction: float,
        duration: timedelta,
        rotation_stresses: List[float]
    ) -> dict:
        """
        Collect weekly creep damage snapshot and store for SPC analysis.

        Args:
            resident_id: UUID of resident
            workload_fraction: Current sustained workload (0.0-1.0)
            duration: How long workload has been sustained
            rotation_stresses: Historical rotation stress levels

        Returns:
            dict with snapshot data and any alerts generated
        """
        # Calculate current damage using Miner's Rule
        fatigue_curve = self.creep_model.calculate_fatigue_damage(rotation_stresses)
        D = 1.0 - fatigue_curve.remaining_life_fraction

        # Calculate Larson-Miller Parameter
        duration_days = int(duration.total_seconds() / 86400)
        lmp = self.creep_model.calculate_larson_miller(workload_fraction, duration_days)

        # Determine creep stage
        stage = self.creep_model.determine_creep_stage(lmp)

        # Create snapshot record
        snapshot = {
            "resident_id": str(resident_id),
            "timestamp": datetime.utcnow(),
            "damage": D,
            "lmp": lmp,
            "creep_stage": stage.value,
            "workload_fraction": workload_fraction,
            "remaining_life": fatigue_curve.remaining_life_fraction
        }

        # Store in database
        await self._persist_snapshot(snapshot)

        # Retrieve last 12 weeks for SPC analysis
        historical_damage = await self._get_damage_history(resident_id, weeks=12)

        # Check for Western Electric violations
        alerts = []
        if len(historical_damage) >= 3:  # Need minimum data for rules
            alerts = await self._check_spc_violations(
                resident_id,
                historical_damage
            )

        return {
            "snapshot": snapshot,
            "alerts": alerts,
            "trend": self._calculate_damage_trend(historical_damage)
        }

    async def _check_spc_violations(
        self,
        resident_id: UUID,
        damage_values: List[float]
    ) -> List[dict]:
        """
        Check damage values against Western Electric Rules.

        Converts damage values (0.0-1.0) to "hours" for compatibility
        with WorkloadControlChart API.
        """
        # Scale damage to "hours" range for control chart
        # Damage 0.0-1.0 → Hours 0-100
        scaled_values = [d * 100.0 for d in damage_values]

        # Adjust control chart to damage scale
        # Centerline = 30 (damage 0.3)
        # Sigma = 15 (damage 0.15)
        chart = WorkloadControlChart(target_hours=30.0, sigma=15.0)

        # Detect violations
        spc_alerts = chart.detect_western_electric_violations(
            resident_id=resident_id,
            weekly_hours=scaled_values
        )

        # Convert SPCAlert objects to dicts with damage-specific messaging
        alerts = []
        for alert in spc_alerts:
            # Unscale back to damage
            damage_values_in_alert = [h / 100.0 for h in alert.data_points]

            alerts.append({
                "rule": alert.rule,
                "severity": alert.severity,
                "message": self._translate_to_damage_message(
                    alert.rule,
                    damage_values_in_alert,
                    alert.severity
                ),
                "resident_id": str(alert.resident_id),
                "timestamp": alert.timestamp.isoformat(),
                "damage_values": damage_values_in_alert
            })

        return alerts

    def _translate_to_damage_message(
        self,
        rule: str,
        damage_values: List[float],
        severity: str
    ) -> str:
        """Translate SPC alert to damage-specific message."""
        if rule == "Rule 1":
            D = damage_values[0]
            return (
                f"CRITICAL: Cumulative damage {D:.2f} exceeds 3σ limit (0.75). "
                f"Burnout imminent - immediate workload reduction required."
            )
        elif rule == "Rule 2":
            return (
                f"WARNING: {len([d for d in damage_values if d > 0.60])} of 3 weeks "
                f"with damage > 0.60 (2σ limit). Sustained overload pattern detected."
            )
        elif rule == "Rule 3":
            return (
                f"WARNING: {len([d for d in damage_values if d > 0.45])} of 5 weeks "
                f"with damage > 0.45 (1σ limit). Gradual damage accumulation trend."
            )
        elif rule == "Rule 4":
            mean_D = sum(damage_values) / len(damage_values)
            return (
                f"INFO: 8 consecutive weeks with damage above baseline (0.30). "
                f"Mean damage: {mean_D:.2f}. Systematic workload increase detected."
            )
        else:
            return f"{severity}: {rule} violation with damage {damage_values}"

    def _calculate_damage_trend(self, damage_history: List[float]) -> dict:
        """
        Calculate rate of damage accumulation (dD/dt).

        Uses linear regression to determine if damage is:
        - Accelerating (positive slope, increasing)
        - Stable (near-zero slope)
        - Recovering (negative slope, decreasing)
        """
        if len(damage_history) < 2:
            return {"trend": "insufficient_data", "rate": 0.0}

        # Simple linear regression: y = mx + b
        n = len(damage_history)
        x_values = list(range(n))
        y_values = damage_history

        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return {"trend": "stable", "rate": 0.0}

        slope = (n * sum_xy - sum_x * sum_y) / denominator  # dD/dt per week

        # Interpret slope
        if slope > 0.05:
            trend = "accelerating"
            interpretation = "Damage accumulating rapidly"
        elif slope > 0.01:
            trend = "increasing"
            interpretation = "Gradual damage accumulation"
        elif slope > -0.01:
            trend = "stable"
            interpretation = "Steady-state damage level"
        elif slope > -0.05:
            trend = "recovering"
            interpretation = "Damage decreasing (recovery)"
        else:
            trend = "rapid_recovery"
            interpretation = "Rapid damage reduction"

        return {
            "trend": trend,
            "rate": slope,
            "interpretation": interpretation,
            "weeks_to_failure": self._estimate_weeks_to_failure(
                current_damage=damage_history[-1],
                rate=slope
            ) if slope > 0 else None
        }

    def _estimate_weeks_to_failure(
        self,
        current_damage: float,
        rate: float
    ) -> int:
        """
        Estimate weeks until failure (D=1.0) given current rate.

        Uses linear extrapolation: weeks = (1.0 - D) / rate
        """
        if rate <= 0:
            return 999  # Not approaching failure

        remaining_damage = 1.0 - current_damage
        weeks = remaining_damage / rate

        return max(0, int(weeks))

    async def _persist_snapshot(self, snapshot: dict):
        """Persist damage snapshot to database."""
        # Implementation: Insert into damage_history table
        pass

    async def _get_damage_history(
        self,
        resident_id: UUID,
        weeks: int
    ) -> List[float]:
        """Retrieve historical damage values from database."""
        # Implementation: Query damage_history table
        # Return list of D values in chronological order
        pass
```

---

## Alert Escalation Policy

### Severity Levels

#### CRITICAL (Rule 1 Violations)

**Trigger:** `D > 0.75` (beyond 3σ)

**Automated Actions:**
1. Immediate email to Program Director
2. SMS alert to Chief Resident
3. Dashboard displays red critical alert
4. Auto-create intervention task in system
5. Block future schedule assignments until resolved

**Human Actions Required:**
- Schedule emergency meeting within 24 hours
- Implement immediate workload reduction (≥20%)
- Review rotation assignment for next block
- Document intervention in resident file

**Example Alert:**
```
CRITICAL: Resident John Doe (PGY-2)

Cumulative Damage: 0.82 (82% of failure threshold)
Creep Stage: TERTIARY
Time to Burnout: 7-14 days (estimated)

Western Electric Rule 1 Violation:
Damage exceeded 3σ upper control limit (0.75)

IMMEDIATE ACTION REQUIRED:
- Reduce workload by 25% immediately
- Remove from call rotation this week
- Schedule wellness check-in
- Refer to counseling services if needed

Historical Trend:
Week -4: 0.58
Week -3: 0.64
Week -2: 0.71
Week -1: 0.78
Week  0: 0.82 ← CRITICAL

Rate of Accumulation: +0.06 per week (ACCELERATING)
```

#### WARNING (Rule 2/3 Violations)

**Trigger:**
- Rule 2: `2 of 3 weeks D > 0.60` (beyond 2σ)
- Rule 3: `4 of 5 weeks D > 0.45` (beyond 1σ)

**Automated Actions:**
1. Email to Chief Resident and Coordinator
2. Dashboard displays yellow/orange warning
3. Add to watch list for weekly review
4. Generate intervention recommendation

**Human Actions Required:**
- Review schedule within 48 hours
- Implement 10-15% workload reduction
- Schedule follow-up check-in in 1 week
- Monitor for escalation to CRITICAL

**Example Alert:**
```
WARNING: Resident Jane Smith (PGY-3)

Cumulative Damage: 0.67 (67% of failure threshold)
Creep Stage: SECONDARY (late)
Time to Burnout: 4-6 weeks (estimated)

Western Electric Rule 2 Violation:
2 of last 3 weeks exceeded 2σ threshold (0.60)
Week -2: 0.62
Week -1: 0.65
Week  0: 0.67

RECOMMENDED ACTIONS:
- Reduce call frequency by 1-2 shifts per block
- Transition to lighter rotation next block
- Monitor weekly for next 4 weeks

Trend: INCREASING (+0.025/week)
```

#### INFO (Rule 4 Violations)

**Trigger:** `8 consecutive weeks D > 0.30` (centerline)

**Automated Actions:**
1. Dashboard notification
2. Add to weekly report
3. Update resident performance metrics

**Human Actions Required:**
- Review during next scheduled meeting
- Assess if baseline has permanently shifted
- Consider re-centering control chart if sustained

**Example Alert:**
```
INFO: Resident Mike Johnson (PGY-1)

Cumulative Damage: 0.38 (38% of failure threshold)
Creep Stage: SECONDARY (early)

Western Electric Rule 4 Violation:
8 consecutive weeks above baseline (0.30)
Mean damage over period: 0.36

INTERPRETATION:
Systematic increase in workload baseline detected.
This may indicate:
- Transition to more demanding rotation
- Increased clinical responsibilities
- New baseline for PGY level

RECOMMENDATION:
Monitor for continuation. If sustained >12 weeks,
consider re-centering control chart to new baseline.

Trend: STABLE (±0.005/week)
```

---

## Test Cases

### Test Case 1: Steady State (Healthy Resident)

**Scenario:** Resident maintains stable workload in PRIMARY creep stage.

**Input Data:**
```python
weekly_damage = [0.22, 0.24, 0.23, 0.25, 0.22, 0.24, 0.23, 0.25]
workload_fraction = 0.65
duration = timedelta(days=56)  # 8 weeks
rotation_stresses = [0.5, 0.5, 0.6, 0.5]
```

**Expected Behavior:**
- No Western Electric violations
- Creep stage: PRIMARY
- LMP < 22.5 (< 50% threshold)
- D remains < 0.30 (centerline)
- Trend: STABLE
- Alert count: 0

**Assertions:**
```python
assert len(alerts) == 0
assert creep_stage == CreepStage.PRIMARY
assert all(D < 0.30 for D in weekly_damage)
assert trend["trend"] == "stable"
```

### Test Case 2: Gradual Accumulation (Rule 3 Trigger)

**Scenario:** Resident experiences gradual damage accumulation over 5 weeks.

**Input Data:**
```python
weekly_damage = [0.30, 0.35, 0.42, 0.48, 0.52, 0.55]
workload_fraction = 0.80
duration = timedelta(days=42)  # 6 weeks
rotation_stresses = [0.7, 0.7, 0.8, 0.75, 0.8, 0.85]
```

**Expected Behavior:**
- Rule 3 violation: 4 of 5 weeks > 0.45 (1σ)
- Creep stage: SECONDARY (late)
- Severity: WARNING
- Trend: INCREASING
- Alert count: 1

**Assertions:**
```python
assert len(alerts) == 1
assert alerts[0]["rule"] == "Rule 3"
assert alerts[0]["severity"] == "WARNING"
assert creep_stage == CreepStage.SECONDARY
assert 0.45 < D < 0.60
assert trend["trend"] == "increasing"
```

### Test Case 3: Sudden Spike (Rule 1 Trigger)

**Scenario:** Resident experiences sudden workload surge causing critical damage.

**Input Data:**
```python
weekly_damage = [0.35, 0.38, 0.40, 0.82]  # Sudden jump to 0.82
workload_fraction = 0.95
duration = timedelta(days=28)  # 4 weeks
rotation_stresses = [0.6, 0.6, 0.7, 0.95]  # Very high stress rotation
```

**Expected Behavior:**
- Rule 1 violation: D > 0.75 (3σ)
- Creep stage: TERTIARY
- Severity: CRITICAL
- Trend: ACCELERATING
- Alert count: 1
- Estimated time to failure: < 2 weeks

**Assertions:**
```python
assert len(alerts) == 1
assert alerts[0]["rule"] == "Rule 1"
assert alerts[0]["severity"] == "CRITICAL"
assert creep_stage == CreepStage.TERTIARY
assert D > 0.75
assert trend["trend"] == "accelerating"
assert trend["weeks_to_failure"] < 2
```

### Test Case 4: Sustained Overload (Rule 2 + Rule 4)

**Scenario:** Resident maintains elevated workload for extended period.

**Input Data:**
```python
weekly_damage = [0.35, 0.40, 0.62, 0.65, 0.68, 0.66, 0.64, 0.67, 0.69]
workload_fraction = 0.85
duration = timedelta(days=63)  # 9 weeks
rotation_stresses = [0.6] * 9  # Sustained high stress
```

**Expected Behavior:**
- Rule 2 violation: 2 of 3 weeks > 0.60 (2σ) at weeks 3-5
- Rule 4 violation: 8 consecutive weeks > 0.30 (centerline)
- Creep stage: TERTIARY (early)
- Severity: WARNING (both rules)
- Trend: INCREASING
- Alert count: 2

**Assertions:**
```python
assert len(alerts) == 2
assert any(a["rule"] == "Rule 2" for a in alerts)
assert any(a["rule"] == "Rule 4" for a in alerts)
assert creep_stage == CreepStage.TERTIARY
assert 0.60 < D < 0.75
assert trend["trend"] == "increasing"
```

### Test Case 5: Recovery After Intervention (Decreasing Trend)

**Scenario:** Resident's damage decreases after workload reduction.

**Input Data:**
```python
weekly_damage = [0.68, 0.65, 0.60, 0.55, 0.50, 0.45, 0.40, 0.35]
workload_fraction = 0.55  # Reduced from 0.85
duration = timedelta(days=56)  # 8 weeks
rotation_stresses = [0.8, 0.7, 0.6, 0.5, 0.5, 0.4, 0.4, 0.4]
```

**Expected Behavior:**
- No new violations (damage decreasing)
- Creep stage: SECONDARY → PRIMARY transition
- Trend: RECOVERING
- Alert count: 0 (no new violations)
- Rate: Negative (dD/dt < 0)

**Assertions:**
```python
assert len(alerts) == 0
assert trend["trend"] in ["recovering", "rapid_recovery"]
assert trend["rate"] < 0
assert weekly_damage[-1] < weekly_damage[0]
assert creep_stage == CreepStage.PRIMARY  # By end
```

### Test Case 6: Edge Case - Exact Threshold

**Scenario:** Damage values exactly at control limits.

**Input Data:**
```python
weekly_damage = [0.75, 0.60, 0.45, 0.30]  # Exact thresholds
workload_fraction = 0.70
duration = timedelta(days=28)
rotation_stresses = [0.65, 0.60, 0.55, 0.50]
```

**Expected Behavior:**
- D = 0.75 exactly → Rule 1 violation (≥ UCL₃σ)
- Boundary condition handled correctly
- No off-by-one errors

**Assertions:**
```python
assert weekly_damage[0] == 0.75
# Depends on > vs >= in implementation
# Document whether boundaries are inclusive/exclusive
```

---

## Implementation Checklist

### Phase 1: Core Bridge (Week 1-2)

- [ ] Create `CreepSPCBridge` class in `backend/app/resilience/creep_spc_bridge.py`
- [ ] Implement `collect_weekly_snapshot()` method
- [ ] Implement `_check_spc_violations()` method
- [ ] Implement `_translate_to_damage_message()` method
- [ ] Implement `_calculate_damage_trend()` method
- [ ] Add damage-to-hours scaling logic for `WorkloadControlChart` compatibility

### Phase 2: Data Persistence (Week 2-3)

- [ ] Create `damage_history` table schema:
  ```sql
  CREATE TABLE damage_history (
      id UUID PRIMARY KEY,
      resident_id UUID NOT NULL REFERENCES persons(id),
      timestamp TIMESTAMP NOT NULL,
      damage FLOAT NOT NULL,  -- Miner's damage (0.0-1.0)
      lmp FLOAT NOT NULL,     -- Larson-Miller Parameter
      creep_stage VARCHAR(20) NOT NULL,
      workload_fraction FLOAT NOT NULL,
      remaining_life FLOAT NOT NULL,
      created_at TIMESTAMP DEFAULT NOW()
  );

  CREATE INDEX idx_damage_history_resident_time
      ON damage_history(resident_id, timestamp DESC);
  ```
- [ ] Create Alembic migration for `damage_history` table
- [ ] Implement `_persist_snapshot()` method (INSERT query)
- [ ] Implement `_get_damage_history()` method (SELECT query)
- [ ] Add database cleanup job (retain 52 weeks of history)

### Phase 3: Celery Integration (Week 3)

- [ ] Create Celery task `calculate_weekly_creep_damage` in `backend/app/celery_app.py`
- [ ] Schedule weekly cron: `crontab(day_of_week=0, hour=1, minute=0)`  # Every Sunday 1 AM
- [ ] Add task for all active residents (role='RESIDENT', status='ACTIVE')
- [ ] Error handling and retry logic (max 3 retries, exponential backoff)
- [ ] Log task execution to monitoring system

### Phase 4: Alert System (Week 4)

- [ ] Integrate with `NotificationService` for email/SMS alerts
- [ ] Create alert templates:
  - `alerts/creep_rule1_critical.html` (CRITICAL)
  - `alerts/creep_rule2_warning.html` (WARNING)
  - `alerts/creep_rule3_warning.html` (WARNING)
  - `alerts/creep_rule4_info.html` (INFO)
- [ ] Implement escalation logic in `CreepSPCBridge.handle_alerts()`
- [ ] Add alert deduplication (don't re-send same alert within 7 days)
- [ ] Create dashboard widget for active creep alerts

### Phase 5: Testing (Week 4-5)

- [ ] Unit tests for `CreepSPCBridge`:
  - `test_collect_weekly_snapshot()`
  - `test_check_spc_violations_rule1()`
  - `test_check_spc_violations_rule2()`
  - `test_check_spc_violations_rule3()`
  - `test_check_spc_violations_rule4()`
  - `test_calculate_damage_trend()`
  - `test_estimate_weeks_to_failure()`
- [ ] Integration tests:
  - `test_end_to_end_damage_tracking()`
  - `test_alert_generation_and_notification()`
  - `test_database_persistence()`
- [ ] Performance tests:
  - `test_weekly_job_completes_within_5_minutes()` (for 100 residents)
  - `test_query_performance_damage_history()`

### Phase 6: Documentation (Week 5)

- [ ] API documentation for `CreepSPCBridge`
- [ ] User guide: "Understanding Creep/SPC Alerts"
- [ ] Admin guide: "Responding to Burnout Alerts"
- [ ] Update `CLAUDE.md` with new resilience bridge
- [ ] Create Grafana dashboard for creep monitoring

### Phase 7: Deployment (Week 6)

- [ ] Feature flag: `ENABLE_CREEP_SPC_MONITORING` (default: false)
- [ ] Deploy to staging environment
- [ ] Run weekly job manually and verify alerts
- [ ] A/B test: Compare burnout prediction accuracy vs. traditional methods
- [ ] Enable in production with gradual rollout (10% → 50% → 100%)

---

## API Reference

### Core Methods

#### `CreepSPCBridge.collect_weekly_snapshot()`

```python
async def collect_weekly_snapshot(
    resident_id: UUID,
    workload_fraction: float,
    duration: timedelta,
    rotation_stresses: List[float]
) -> dict:
    """
    Collect weekly creep damage snapshot and check for SPC violations.

    Args:
        resident_id: UUID of resident to analyze
        workload_fraction: Current sustained workload (0.0-1.0)
        duration: How long workload has been sustained
        rotation_stresses: Historical rotation stress levels (0.0-1.0)

    Returns:
        {
            "snapshot": {
                "resident_id": str,
                "timestamp": datetime,
                "damage": float,  # 0.0-1.0
                "lmp": float,
                "creep_stage": str,
                "workload_fraction": float,
                "remaining_life": float
            },
            "alerts": [
                {
                    "rule": str,
                    "severity": str,
                    "message": str,
                    "resident_id": str,
                    "timestamp": str (ISO),
                    "damage_values": list[float]
                }
            ],
            "trend": {
                "trend": str,  # "accelerating", "stable", "recovering"
                "rate": float,  # dD/dt per week
                "interpretation": str,
                "weeks_to_failure": int | None
            }
        }

    Raises:
        ValueError: If workload_fraction not in [0, 1]
        ValueError: If duration <= 0
        ValueError: If rotation_stresses contains invalid values
    """
```

#### `CreepSPCBridge.get_resident_damage_report()`

```python
async def get_resident_damage_report(
    resident_id: UUID,
    weeks: int = 12
) -> dict:
    """
    Generate comprehensive damage report for resident.

    Args:
        resident_id: UUID of resident
        weeks: Number of weeks of history to include (default: 12)

    Returns:
        {
            "resident_id": str,
            "current_damage": float,
            "current_stage": str,
            "damage_history": [
                {"week": int, "damage": float, "lmp": float},
                ...
            ],
            "trend": dict,
            "active_alerts": list[dict],
            "recommendations": list[str],
            "risk_level": str  # "low", "moderate", "high", "critical"
        }
    """
```

### Celery Tasks

#### `calculate_weekly_creep_damage`

```python
@celery_app.task(bind=True, max_retries=3)
def calculate_weekly_creep_damage(self, resident_id: str):
    """
    Celery task to calculate weekly creep damage for a resident.

    Scheduled: Every Sunday at 1:00 AM
    Cron: crontab(day_of_week=0, hour=1, minute=0)

    Args:
        resident_id: UUID string of resident

    Side Effects:
        - Inserts snapshot into damage_history table
        - Generates alerts if violations detected
        - Sends notifications to Program Director/Chief

    Retries:
        - Max 3 retries with exponential backoff
        - Retry on database connection errors
        - Retry on temporary API failures
    """
```

---

## Performance Considerations

### Computational Complexity

| Operation | Time Complexity | Space Complexity | Notes |
|-----------|----------------|------------------|-------|
| `calculate_damage()` | O(n) | O(1) | n = number of rotations |
| `check_spc_violations()` | O(m) | O(m) | m = number of weeks (typically 12) |
| `calculate_trend()` | O(m) | O(1) | Linear regression |
| Weekly job (all residents) | O(r × n) | O(r) | r = residents, n = rotations/resident |

### Scalability Analysis

**Assumptions:**
- 100 residents in program
- 12 weeks of history per resident
- Weekly job runtime

**Calculations:**
```
Per-resident time:
  - Damage calculation: 10ms
  - SPC rule checks: 5ms
  - Database writes: 20ms
  - Total: 35ms/resident

All residents:
  - 100 residents × 35ms = 3.5 seconds
  - With parallelization (10 workers): 0.35 seconds
```

**Bottlenecks:**
1. Database writes (20ms per resident) → Use batch INSERT
2. Email notifications (1-2s per alert) → Queue for async sending
3. Historical query (100ms if not indexed) → Ensure index on `resident_id, timestamp`

**Optimization Strategies:**
1. Batch database operations:
   ```python
   # Bad: Individual INSERTs
   for snapshot in snapshots:
       await db.execute(insert(DamageHistory).values(snapshot))

   # Good: Bulk INSERT
   await db.execute(insert(DamageHistory).values(snapshots))
   ```

2. Parallelize resident processing:
   ```python
   # Use Celery groups for parallel execution
   from celery import group

   job = group(
       calculate_weekly_creep_damage.s(str(resident.id))
       for resident in active_residents
   )
   result = job.apply_async()
   ```

3. Cache recent damage history:
   ```python
   # Redis cache for last 12 weeks per resident
   cache_key = f"damage_history:{resident_id}"
   cached = await redis.get(cache_key)

   if cached:
       return json.loads(cached)
   else:
       data = await db.query(...)
       await redis.setex(cache_key, 86400, json.dumps(data))  # 24h TTL
       return data
   ```

---

## Monitoring and Observability

### Metrics to Track

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# Alert counts by severity
creep_alerts_total = Counter(
    'creep_alerts_total',
    'Total creep/SPC alerts generated',
    ['severity', 'rule']
)

# Damage distribution across residents
resident_damage_gauge = Gauge(
    'resident_damage_current',
    'Current cumulative damage per resident',
    ['resident_id', 'creep_stage']
)

# Weekly job performance
creep_calculation_duration = Histogram(
    'creep_calculation_duration_seconds',
    'Time to calculate weekly creep damage',
    ['status']  # 'success' or 'failure'
)

# Trend distribution
damage_trend_gauge = Gauge(
    'damage_trend_rate',
    'Rate of damage accumulation (dD/dt)',
    ['resident_id', 'trend_category']  # 'accelerating', 'stable', etc.
)
```

### Grafana Dashboard

**Panels:**

1. **Alert Heatmap** - Severity by resident over time
2. **Damage Distribution** - Histogram of current damage values
3. **Creep Stage Breakdown** - Pie chart (PRIMARY/SECONDARY/TERTIARY)
4. **Trend Analysis** - Line chart showing dD/dt for all residents
5. **Alert Response Time** - Time from alert to intervention
6. **Weekly Job Status** - Success rate, duration, errors

### Logging

```python
# Structured logging for damage snapshots
logger.info(
    "Weekly creep snapshot collected",
    extra={
        "resident_id": str(resident_id),
        "damage": D,
        "lmp": lmp,
        "creep_stage": stage.value,
        "alerts_generated": len(alerts),
        "trend": trend["trend"],
        "rate": trend["rate"]
    }
)

# Alert generation
logger.warning(
    "SPC violation detected",
    extra={
        "resident_id": str(resident_id),
        "rule": alert["rule"],
        "severity": alert["severity"],
        "damage_values": alert["damage_values"],
        "control_limit_exceeded": control_limit
    }
)
```

---

## Future Enhancements

### Phase 2 Features (Post-MVP)

1. **Multi-Factor Damage Model**
   - Incorporate emotional labor (difficult patients, ethical dilemmas)
   - Add sleep debt accumulation
   - Factor in social support metrics

2. **Personalized Control Limits**
   - Learn individual baselines from historical data
   - Adjust σ based on resident resilience factors
   - Dynamic centerline based on rotation type

3. **Predictive Alerting**
   - Machine learning model to predict Rule 1 violations 2-3 weeks early
   - Feature inputs: current damage, trend, rotation schedule, historical patterns
   - Train on historical burnout cases

4. **Recovery Optimization**
   - Algorithm to suggest optimal workload reduction percentage
   - Schedule optimizer for post-intervention recovery
   - Track recovery success rate

5. **Cohort Analysis**
   - Compare damage patterns by PGY level
   - Identify high-risk rotation combinations
   - Benchmark program against national norms

---

## References

### Materials Science

1. Larson, F.R., Miller, J. (1952). "A Time-Temperature Relationship for Rupture and Creep Stresses." *Transactions of the ASME*, 74, 765-775.

2. Miner, M.A. (1945). "Cumulative Damage in Fatigue." *Journal of Applied Mechanics*, 12, A159-A164.

3. Wöhler, A. (1860). "Versuche über die Festigkeit der Eisenbahnwagenachsen." *Zeitschrift für Bauwesen*, 10, 160-161.

### Statistical Process Control

4. Western Electric Company (1956). *Statistical Quality Control Handbook*. Indianapolis: Western Electric Co.

5. Montgomery, D.C. (2019). *Introduction to Statistical Quality Control* (8th ed.). Wiley.

6. Wheeler, D.J., Chambers, D.S. (1992). *Understanding Statistical Process Control*. SPC Press.

### Medical Applications

7. Maslach, C., Jackson, S.E., Leiter, M.P. (1996). *Maslach Burnout Inventory Manual* (3rd ed.). Consulting Psychologists Press.

8. ACGME (2017). "Common Program Requirements." *Accreditation Council for Graduate Medical Education*.

9. Billings, M.E., et al. (2020). "Work-Hour Violations and Fatigue in Resident Physicians." *JAMA Internal Medicine*, 180(2), 180-189.

---

## Appendix: Configuration

### Environment Variables

```bash
# Enable/disable creep monitoring
ENABLE_CREEP_SPC_MONITORING=true

# Control chart parameters (optional overrides)
CREEP_DAMAGE_CENTERLINE=0.30  # Default baseline damage
CREEP_DAMAGE_SIGMA=0.15       # Standard deviation

# Alert thresholds (optional overrides)
CREEP_CRITICAL_THRESHOLD=0.75  # 3σ limit
CREEP_WARNING_THRESHOLD=0.60   # 2σ limit
CREEP_CAUTION_THRESHOLD=0.45   # 1σ limit

# Celery schedule
CREEP_WEEKLY_JOB_ENABLED=true
CREEP_WEEKLY_JOB_DAY=0         # 0=Sunday, 6=Saturday
CREEP_WEEKLY_JOB_HOUR=1        # Hour (0-23)
CREEP_WEEKLY_JOB_MINUTE=0      # Minute (0-59)

# Notification settings
CREEP_ALERT_EMAIL_ENABLED=true
CREEP_ALERT_SMS_ENABLED=false  # Requires Twilio integration
CREEP_ALERT_DEDUPE_HOURS=168   # Don't re-send same alert within 7 days
```

### Feature Flags (Launch Darkly / Database)

```python
# Progressive rollout
feature_flags = {
    "creep_monitoring_enabled": {
        "default": False,
        "rollout_percentage": 10,  # Start at 10%, increase to 100%
        "whitelist_resident_ids": [...]  # Pilot residents
    },
    "creep_critical_alerts_enabled": {
        "default": True,
        "requires": ["creep_monitoring_enabled"]
    },
    "creep_info_alerts_enabled": {
        "default": False,  # Enable WARNING/INFO alerts later
    }
}
```

---

**End of Bridge Specification**

This document is implementation-ready and should be used as the authoritative source for developing the Creep/SPC integration.
