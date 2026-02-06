# Workflow: Recovery Time Analysis

## Overview

Model the time required to restore coverage after a disruption and identify the fastest recovery strategy. Quantifies recovery bottlenecks and evaluates mitigation options.

## Purpose

Answer the questions:
- **"How quickly can we recover from this disruption?"**
- **"What's the fastest recovery strategy?"**
- **"Which rotations are bottlenecks?"**
- **"Is supplemental staff effective?"**

## When to Use

Recovery time analysis should be run:
- ✅ After identifying critical residents (N-1 analysis shows collapse scenarios)
- ✅ When planning for known absences (deployment, medical leave)
- ✅ During incident response (resident suddenly absent)
- ✅ When evaluating supplemental staffing options
- ✅ To validate schedule resilience claims ("we can recover in 48 hours")

## Workflow Steps

### Step 1: Define Recovery Scenario

```python
recovery_scenario = {
    "disruption": {
        "absent_residents": ["PGY2-03", "PGY3-01"],  # Who is absent
        "start_date": date(2025, 1, 15),
        "duration_days": 14  # How long will they be gone
    },
    "available_mitigations": {
        "supplemental_staff": ["FAC-TEMP-01", "FAC-TEMP-02"],  # Available temps
        "cross_trained_residents": ["PGY2-05", "PGY3-04"],  # Can cover multiple rotations
        "overtime_budget": 40  # Max additional hours per week allowed
    },
    "recovery_goal": {
        "target_coverage": 1.0,  # 100% of rotation minimums
        "max_acgme_violations": 0,  # No violations allowed
        "max_recovery_time_hours": 48  # Must restore in 48 hours
    }
}
```

### Step 2: Baseline Impact Assessment

Before modeling recovery, assess the baseline impact of the disruption:

```python
def assess_baseline_impact(scenario):
    """
    Quantify the coverage gap without any mitigation.

    Returns:
        - Rotation coverage deficits
        - Duration of understaffing
        - Residents affected by redistribution
    """
    baseline = {
        "coverage_gaps": [],
        "total_understaffed_hours": 0,
        "residents_affected": []
    }

    # Simulate removing absent residents
    schedule_state = simulate_absence(
        absent_residents=scenario["disruption"]["absent_residents"],
        start_date=scenario["disruption"]["start_date"],
        duration_days=scenario["disruption"]["duration_days"]
    )

    # Identify coverage gaps
    for rotation_id, coverage in schedule_state["rotations"].items():
        if coverage["actual"] < coverage["required"]:
            shortfall = coverage["required"] - coverage["actual"]
            baseline["coverage_gaps"].append({
                "rotation_id": rotation_id,
                "shortfall": shortfall,
                "understaffed_days": scenario["disruption"]["duration_days"],
                "understaffed_hours": shortfall * 24 * scenario["disruption"]["duration_days"]
            })
            baseline["total_understaffed_hours"] += shortfall * 24 * scenario["disruption"]["duration_days"]

    # Identify residents who would need reassignment (naive internal shuffle)
    for resident_id, work_hours in schedule_state["work_hours"].items():
        if work_hours > 80:  # Would violate ACGME if we just redistribute
            baseline["residents_affected"].append({
                "resident_id": resident_id,
                "work_hours": work_hours,
                "overage": work_hours - 80
            })

    return baseline
```

### Step 3: Model Recovery Strategies

Test different recovery strategies and compare time-to-recovery:

```python
def model_recovery_strategies(scenario, baseline):
    """
    Test multiple recovery strategies and identify the fastest.

    Strategies:
        1. Internal redistribution (no supplemental staff)
        2. Supplemental staff only
        3. Cross-trained residents
        4. Hybrid (supplemental + cross-training)
    """
    strategies = []

    # Strategy 1: Internal Redistribution
    strategy_1 = model_internal_redistribution(scenario, baseline)
    strategies.append({
        "name": "Internal Redistribution",
        "recovery_time_hours": strategy_1["recovery_time_hours"],
        "feasible": strategy_1["feasible"],
        "cost": 0,  # No additional cost
        "acgme_violations": strategy_1["acgme_violations"],
        "details": strategy_1
    })

    # Strategy 2: Supplemental Staff
    if scenario["available_mitigations"]["supplemental_staff"]:
        strategy_2 = model_supplemental_staff(scenario, baseline)
        strategies.append({
            "name": "Supplemental Staff",
            "recovery_time_hours": strategy_2["recovery_time_hours"],
            "feasible": strategy_2["feasible"],
            "cost": strategy_2["supplemental_staff_count"] * 1000,  # $1000/week per temp
            "acgme_violations": 0,  # No violations (we add staff, not burden existing)
            "details": strategy_2
        })

    # Strategy 3: Cross-Trained Residents
    if scenario["available_mitigations"]["cross_trained_residents"]:
        strategy_3 = model_cross_training(scenario, baseline)
        strategies.append({
            "name": "Cross-Training",
            "recovery_time_hours": strategy_3["recovery_time_hours"],
            "feasible": strategy_3["feasible"],
            "cost": 0,  # Assuming residents already trained
            "acgme_violations": strategy_3["acgme_violations"],
            "details": strategy_3
        })

    # Strategy 4: Hybrid
    strategy_4 = model_hybrid_recovery(scenario, baseline)
    strategies.append({
        "name": "Hybrid (Supplemental + Cross-Training)",
        "recovery_time_hours": strategy_4["recovery_time_hours"],
        "feasible": strategy_4["feasible"],
        "cost": strategy_4["supplemental_staff_count"] * 1000,
        "acgme_violations": strategy_4["acgme_violations"],
        "details": strategy_4
    })

    # Find optimal strategy (fastest feasible strategy)
    feasible_strategies = [s for s in strategies if s["feasible"]]
    if feasible_strategies:
        optimal_strategy = min(feasible_strategies, key=lambda x: x["recovery_time_hours"])
    else:
        optimal_strategy = None

    return {
        "strategies": strategies,
        "optimal_strategy": optimal_strategy
    }
```

### Step 4: Internal Redistribution Model

```python
def model_internal_redistribution(scenario, baseline):
    """
    Model recovery using only existing residents (no additional staff).

    Approach:
        - Identify residents with slack (work hours < 70/week)
        - Reassign them to cover gaps
        - Calculate how long it takes to cover all gaps

    Returns:
        - Recovery time (hours)
        - Whether feasible without ACGME violations
        - Specific reassignments
    """
    recovery = {
        "recovery_time_hours": None,
        "feasible": False,
        "acgme_violations": [],
        "reassignments": []
    }

    # Get residents with slack capacity
    residents_with_slack = []
    for resident in active_residents:
        current_hours = get_4week_rolling_hours(resident)
        if current_hours < 70:  # Leave 10-hour buffer below 80-hour limit
            slack_hours = 70 - current_hours
            residents_with_slack.append({
                "resident_id": resident.id,
                "slack_hours": slack_hours,
                "current_rotations": get_resident_rotations(resident)
            })

    # Sort by slack descending (use residents with most slack first)
    residents_with_slack.sort(key=lambda x: x["slack_hours"], reverse=True)

    # Try to cover each gap
    for gap in baseline["coverage_gaps"]:
        rotation_id = gap["rotation_id"]
        shortfall = gap["shortfall"]

        # Find residents who can cover this rotation
        eligible_residents = [
            r for r in residents_with_slack
            if can_cover_rotation(r["resident_id"], rotation_id)
        ]

        if len(eligible_residents) >= shortfall:
            # We can cover this gap
            for i in range(int(shortfall)):
                resident = eligible_residents[i]
                recovery["reassignments"].append({
                    "resident_id": resident["resident_id"],
                    "rotation_id": rotation_id,
                    "hours_added": 40  # Assuming full-time rotation
                })
                resident["slack_hours"] -= 40

            # Recovery time = time to notify and reassign (assume 24 hours)
            recovery["recovery_time_hours"] = 24
        else:
            # Can't cover this gap with internal redistribution
            recovery["feasible"] = False
            return recovery

    # Check if any reassignments cause ACGME violations
    for reassignment in recovery["reassignments"]:
        new_hours = get_4week_rolling_hours(reassignment["resident_id"]) + reassignment["hours_added"]
        if new_hours > 80:
            recovery["acgme_violations"].append({
                "resident_id": reassignment["resident_id"],
                "violation_type": "80_hour_rule",
                "hours": new_hours
            })

    recovery["feasible"] = len(recovery["acgme_violations"]) == 0

    return recovery
```

### Step 5: Supplemental Staff Model

```python
def model_supplemental_staff(scenario, baseline):
    """
    Model recovery using supplemental (temporary) staff.

    Approach:
        - Assign temporary staff to cover gaps
        - Calculate onboarding time (credentialing, orientation)
        - No ACGME violations (we're adding staff, not burdening existing)

    Returns:
        - Recovery time (includes onboarding)
        - Number of supplemental staff required
        - Cost estimate
    """
    recovery = {
        "recovery_time_hours": None,
        "feasible": False,
        "supplemental_staff_count": 0,
        "supplemental_staff_assignments": []
    }

    available_supplemental = scenario["available_mitigations"]["supplemental_staff"]

    # Calculate how many supplemental staff needed
    total_shortfall = sum([gap["shortfall"] for gap in baseline["coverage_gaps"]])

    if len(available_supplemental) >= total_shortfall:
        recovery["supplemental_staff_count"] = int(total_shortfall)

        # Assign supplemental staff to gaps
        staff_idx = 0
        for gap in baseline["coverage_gaps"]:
            for i in range(int(gap["shortfall"])):
                recovery["supplemental_staff_assignments"].append({
                    "staff_id": available_supplemental[staff_idx],
                    "rotation_id": gap["rotation_id"]
                })
                staff_idx += 1

        # Recovery time = credentialing + orientation
        # Assume: Credentialing (24 hours) + Orientation (8 hours) = 32 hours
        recovery["recovery_time_hours"] = 32
        recovery["feasible"] = True
    else:
        # Not enough supplemental staff available
        recovery["feasible"] = False

    return recovery
```

### Step 6: Identify Bottlenecks

```python
def identify_recovery_bottlenecks(strategies):
    """
    Identify what's slowing down recovery.

    Common bottlenecks:
        - Credentialing time for supplemental staff
        - Lack of cross-trained residents for specialty rotations
        - Work hour constraints (can't add more to existing residents)
        - Rotation complexity (requires specific qualifications)
    """
    bottlenecks = []

    # Check if supplemental staff is delayed by credentialing
    supplemental_strategy = next((s for s in strategies if s["name"] == "Supplemental Staff"), None)
    if supplemental_strategy and supplemental_strategy["recovery_time_hours"] > 24:
        bottlenecks.append({
            "type": "Credentialing Delay",
            "impact_hours": supplemental_strategy["recovery_time_hours"] - 24,
            "description": "Temporary staff requires credentialing before deployment",
            "mitigation": "Maintain pre-credentialed pool of supplemental staff"
        })

    # Check if internal redistribution fails due to work hour constraints
    internal_strategy = next((s for s in strategies if s["name"] == "Internal Redistribution"), None)
    if internal_strategy and not internal_strategy["feasible"]:
        if internal_strategy["details"]["acgme_violations"]:
            bottlenecks.append({
                "type": "Work Hour Constraint",
                "description": "Cannot redistribute internally without ACGME violations",
                "mitigation": "Reduce baseline utilization (target 60-70 hours/week max)"
            })

    # Check if cross-training would help but isn't available
    cross_training_strategy = next((s for s in strategies if s["name"] == "Cross-Training"), None)
    if not cross_training_strategy or not cross_training_strategy["feasible"]:
        bottlenecks.append({
            "type": "Lack of Cross-Training",
            "description": "No residents cross-trained for affected rotations",
            "mitigation": "Implement cross-training program for high-risk rotations"
        })

    return bottlenecks
```

### Step 7: Generate Recovery Plan

```python
def generate_recovery_plan(scenario, strategies, bottlenecks):
    """
    Generate a detailed recovery plan with specific actions.

    Returns:
        - Optimal strategy
        - Step-by-step recovery actions
        - Timeline
        - Bottlenecks and mitigations
    """
    optimal = strategies["optimal_strategy"]

    if not optimal:
        return {
            "feasible": False,
            "message": "No feasible recovery strategy found",
            "bottlenecks": bottlenecks,
            "recommendations": [
                "Increase supplemental staff pool",
                "Reduce rotation minimum requirements",
                "Implement emergency cross-training program"
            ]
        }

    # Build step-by-step plan
    recovery_plan = {
        "strategy": optimal["name"],
        "estimated_recovery_time_hours": optimal["recovery_time_hours"],
        "cost_estimate": optimal["cost"],
        "steps": [],
        "timeline": [],
        "bottlenecks": bottlenecks
    }

    # Add specific steps based on strategy
    if optimal["name"] == "Supplemental Staff":
        recovery_plan["steps"] = [
            {"hour": 0, "action": "Contact supplemental staff agency"},
            {"hour": 1, "action": "Begin credentialing for temporary staff"},
            {"hour": 24, "action": "Credentialing complete"},
            {"hour": 24, "action": "Begin orientation"},
            {"hour": 32, "action": "Temporary staff deployed to rotations"},
            {"hour": 32, "action": "Coverage restored"}
        ]
    elif optimal["name"] == "Internal Redistribution":
        recovery_plan["steps"] = [
            {"hour": 0, "action": "Identify residents with slack capacity"},
            {"hour": 2, "action": "Notify affected residents of reassignments"},
            {"hour": 4, "action": "Process rotation changes in system"},
            {"hour": 24, "action": "Residents begin new assignments"},
            {"hour": 24, "action": "Coverage restored"}
        ]

    return recovery_plan
```

## Implementation Files

### Backend Service
```python
# backend/app/resilience/recovery_planner.py

from datetime import date, timedelta
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.schemas.resilience import RecoveryPlan, RecoveryScenario


class RecoveryPlanner:
    """Model recovery time and identify optimal recovery strategy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_recovery_plan(
        self,
        scenario: RecoveryScenario
    ) -> RecoveryPlan:
        """
        Generate recovery plan for disruption scenario.

        Args:
            scenario: Disruption details and available mitigations

        Returns:
            RecoveryPlan with optimal strategy, timeline, bottlenecks
        """
        # Implementation details...
        pass
```

### API Endpoint
```python
# backend/app/api/routes/resilience.py

@router.post("/recovery-plan", response_model=RecoveryPlan)
async def generate_recovery_plan(
    request: RecoveryScenario,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate recovery plan for disruption scenario.

    Models recovery time and identifies optimal strategy.
    """
    planner = RecoveryPlanner(db)
    plan = await planner.generate_recovery_plan(request)

    return plan
```

## Usage Examples

### Example 1: Plan for Known Absence
```bash
curl -X POST http://localhost:8000/api/resilience/recovery-plan \
  -H "Content-Type: application/json" \
  -d '{
    "disruption": {
      "absent_residents": ["PGY2-03"],
      "start_date": "2025-02-01",
      "duration_days": 14
    },
    "available_mitigations": {
      "supplemental_staff": ["FAC-TEMP-01"],
      "cross_trained_residents": ["PGY2-05"],
      "overtime_budget": 40
    }
  }'
```

**Expected Output:**
```json
{
  "strategy": "Cross-Training",
  "estimated_recovery_time_hours": 24,
  "cost_estimate": 0,
  "feasible": true,
  "steps": [
    {"hour": 0, "action": "Identify residents with slack capacity"},
    {"hour": 2, "action": "Notify PGY2-05 of EM Night Shift coverage"},
    {"hour": 24, "action": "Coverage restored"}
  ],
  "bottlenecks": []
}
```

### Example 2: Emergency Response (Immediate)
```bash
curl -X POST http://localhost:8000/api/resilience/recovery-plan \
  -H "Content-Type: application/json" \
  -d '{
    "disruption": {
      "absent_residents": ["PGY2-03", "PGY3-01"],
      "start_date": "2025-01-15",
      "duration_days": 7
    },
    "available_mitigations": {
      "supplemental_staff": ["FAC-TEMP-01", "FAC-TEMP-02"]
    }
  }'
```

## Success Criteria

- ✅ Recovery time estimated for all available strategies
- ✅ Optimal strategy identified (fastest feasible)
- ✅ Step-by-step recovery plan generated
- ✅ Bottlenecks identified with specific mitigations
- ✅ Cost estimate provided (if using supplemental staff)
- ✅ Plan is actionable (specific residents/staff assignments)

## Next Steps

After generating recovery plan:
1. Document plan in incident response playbook
2. Pre-credential supplemental staff to reduce recovery time
3. Implement cross-training for bottleneck rotations
4. Re-run analysis after implementing mitigations to verify improvement

---

*This workflow enables proactive recovery planning and identifies the fastest path to restore coverage after disruptions.*
