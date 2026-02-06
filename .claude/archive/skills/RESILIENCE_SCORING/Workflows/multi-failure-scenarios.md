# Workflow: Multi-Failure Scenarios

## Overview

Simulate multiple simultaneous resident absences to assess schedule robustness under compound failures. Uses Monte Carlo simulation to identify worst-case scenarios and quantify collapse probability.

## Purpose

Answer the questions:
- **"What happens if 2-3 people are sick at the same time?"** (flu season)
- **"What's our worst-case scenario?"** (which combination of absences is most damaging)
- **"How likely is schedule collapse?"** (probability of total coverage failure)
- **"Which rotations are most fragile?"** (fail in most scenarios)

## When to Use

Multi-failure scenarios should be run:
- ✅ Before deploying schedule for high-risk periods (flu season, deployment season)
- ✅ When N-1 analysis shows 3+ critical residents
- ✅ After major schedule changes (rotation realignment, staffing changes)
- ✅ Monthly during deployment season (Jun-Aug) or flu season (Nov-Feb)
- ✅ When validating schedule resilience claims

## Workflow Steps

### Step 1: Define Simulation Parameters

```python
simulation_config = {
    "trials": 10000,  # Number of Monte Carlo trials
    "min_failures": 2,  # Minimum simultaneous absences
    "max_failures": 3,  # Maximum simultaneous absences
    "duration_days": 7,  # How long absences last
    "start_date": date.today(),
    "failure_mode": "random"  # "random" or "worst_case" or "seasonal"
}
```

**Failure Mode Options**:
- `random`: Uniform random selection of residents
- `worst_case`: Systematically test all combinations to find worst case
- `seasonal`: Weight by historical absence rates (flu season: higher PGY-1 absence rate)

### Step 2: Run Monte Carlo Simulation

```python
def run_monte_carlo_simulation(config):
    """
    Run N trials of random multi-failure scenarios.

    Returns:
        - Time-to-failure distribution
        - Collapse probability
        - Fragile rotation ranking
        - Worst-case scenario details
    """
    results = {
        "trials": [],
        "collapse_count": 0,
        "time_to_failure": [],
        "rotation_failure_count": {},
        "worst_scenario": None,
        "worst_impact_score": 0
    }

    for trial in range(config["trials"]):
        # Randomly select 2-3 residents to be absent
        num_failures = random.randint(config["min_failures"], config["max_failures"])
        absent_residents = random.sample(active_residents, num_failures)

        # Simulate their simultaneous absence
        scenario = simulate_multi_absence(
            resident_ids=absent_residents,
            start_date=config["start_date"],
            duration_days=config["duration_days"]
        )

        # Assess impact
        impact = assess_scenario_impact(scenario)

        # Record results
        results["trials"].append({
            "trial_id": trial,
            "absent_residents": absent_residents,
            "impact_score": impact["score"],
            "failed_rotations": impact["failed_rotations"],
            "time_to_failure_days": impact["time_to_failure"],
            "collapsed": impact["collapsed"]
        })

        if impact["collapsed"]:
            results["collapse_count"] += 1
            results["time_to_failure"].append(impact["time_to_failure"])

        # Track rotation failures
        for rotation in impact["failed_rotations"]:
            rotation_id = rotation["rotation_id"]
            results["rotation_failure_count"][rotation_id] = \
                results["rotation_failure_count"].get(rotation_id, 0) + 1

        # Track worst-case scenario
        if impact["score"] > results["worst_impact_score"]:
            results["worst_scenario"] = {
                "absent_residents": absent_residents,
                "impact": impact
            }
            results["worst_impact_score"] = impact["score"]

    # Calculate statistics
    results["collapse_probability"] = results["collapse_count"] / config["trials"]
    if results["time_to_failure"]:
        results["median_time_to_failure"] = statistics.median(results["time_to_failure"])
        results["p95_time_to_failure"] = statistics.quantiles(results["time_to_failure"], n=20)[18]  # 95th percentile
    else:
        results["median_time_to_failure"] = None
        results["p95_time_to_failure"] = None

    # Rank rotations by fragility
    results["fragile_rotations"] = sorted(
        results["rotation_failure_count"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    return results
```

### Step 3: Assess Scenario Impact

```python
def assess_scenario_impact(scenario):
    """
    Quantify the impact of a multi-failure scenario.

    Returns impact score (0-100), where higher = more severe.
    """
    impact = {
        "score": 0,
        "failed_rotations": [],
        "time_to_failure": None,
        "collapsed": False,
        "acgme_violations": [],
        "residents_overworked": []
    }

    # Check rotation coverage failures
    for rotation_id, coverage_data in scenario["rotations"].items():
        if coverage_data["actual_residents"] < coverage_data["required_residents"]:
            shortfall = coverage_data["required_residents"] - coverage_data["actual_residents"]
            impact["failed_rotations"].append({
                "rotation_id": rotation_id,
                "shortfall": shortfall,
                "days_below_minimum": coverage_data["days_affected"]
            })
            # Add to impact score
            impact["score"] += shortfall * coverage_data["days_affected"] * 10

    # Check work hour violations
    for resident_id, work_hours in scenario["work_hours"].items():
        if work_hours > 80:
            impact["acgme_violations"].append({
                "resident_id": resident_id,
                "violation_type": "80_hour_rule",
                "hours": work_hours,
                "overage": work_hours - 80
            })
            impact["residents_overworked"].append(resident_id)
            # Add to impact score
            impact["score"] += (work_hours - 80) * 2

    # Determine time to failure (first day where any rotation fails)
    if impact["failed_rotations"]:
        impact["time_to_failure"] = min([
            r["days_below_minimum"] for r in impact["failed_rotations"]
        ])
        impact["collapsed"] = True
    else:
        impact["time_to_failure"] = None
        impact["collapsed"] = False

    # Check for cascading failures (>3 rotations affected)
    if len(impact["failed_rotations"]) > 3:
        impact["score"] *= 1.5  # Multiply by 1.5 for cascading failures
        impact["cascading"] = True

    return impact
```

### Step 4: Worst-Case Analysis

In addition to Monte Carlo, systematically test specific high-risk combinations:

```python
def find_worst_case_scenario(config):
    """
    Systematically test combinations to find absolute worst case.

    This is computationally expensive (C(n, k) combinations), so limit to:
    - Critical residents identified by N-1 analysis
    - PGY-year combinations (e.g., all PGY-2s absent)
    - Rotation-specific combinations (e.g., all EM-trained residents)
    """
    critical_residents = get_critical_residents()  # From N-1 analysis

    worst_case = None
    worst_score = 0

    # Test all pairs of critical residents
    for combo in itertools.combinations(critical_residents, 2):
        scenario = simulate_multi_absence(
            resident_ids=combo,
            start_date=config["start_date"],
            duration_days=config["duration_days"]
        )
        impact = assess_scenario_impact(scenario)

        if impact["score"] > worst_score:
            worst_case = {
                "absent_residents": combo,
                "impact": impact
            }
            worst_score = impact["score"]

    # Test PGY-year groupings
    for pgy_year in [1, 2, 3]:
        residents_in_year = get_residents_by_pgy_year(pgy_year)
        for combo in itertools.combinations(residents_in_year, 2):
            scenario = simulate_multi_absence(
                resident_ids=combo,
                start_date=config["start_date"],
                duration_days=config["duration_days"]
            )
            impact = assess_scenario_impact(scenario)

            if impact["score"] > worst_score:
                worst_case = {
                    "absent_residents": combo,
                    "impact": impact,
                    "note": f"PGY-{pgy_year} concentration"
                }
                worst_score = impact["score"]

    return worst_case
```

### Step 5: Rank Fragile Rotations

```python
def rank_fragile_rotations(monte_carlo_results):
    """
    Identify rotations that fail in the most scenarios.

    Returns ranked list with failure probability.
    """
    total_trials = monte_carlo_results["trials"]

    fragile_rotations = []
    for rotation_id, failure_count in monte_carlo_results["rotation_failure_count"].items():
        failure_probability = failure_count / total_trials

        fragile_rotations.append({
            "rotation_id": rotation_id,
            "failure_count": failure_count,
            "failure_probability": failure_probability,
            "severity": "CRITICAL" if failure_probability > 0.50 else
                       "HIGH" if failure_probability > 0.25 else
                       "MEDIUM" if failure_probability > 0.10 else "LOW"
        })

    # Sort by failure probability descending
    fragile_rotations.sort(key=lambda x: x["failure_probability"], reverse=True)

    return fragile_rotations
```

### Step 6: Generate Mitigation Recommendations

```python
def generate_mitigation_recommendations(monte_carlo_results, worst_case):
    """
    Generate actionable recommendations based on multi-failure analysis.
    """
    recommendations = []

    # Check collapse probability
    collapse_prob = monte_carlo_results["collapse_probability"]
    if collapse_prob > 0.10:
        recommendations.append({
            "priority": "CRITICAL",
            "finding": f"Collapse probability {collapse_prob:.1%} exceeds 10% threshold",
            "action": "DO NOT DEPLOY THIS SCHEDULE",
            "details": "Schedule cannot withstand typical multi-failure scenarios (2-3 absences)",
            "mitigations": [
                "Add 2-3 supplemental residents",
                "Reduce rotation minimum staffing requirements",
                "Implement cross-training program for critical rotations"
            ]
        })

    # Check median time to failure
    if monte_carlo_results["median_time_to_failure"]:
        median_ttf = monte_carlo_results["median_time_to_failure"]
        if median_ttf < 3:
            recommendations.append({
                "priority": "HIGH",
                "finding": f"Median time-to-failure {median_ttf} days is critically short",
                "action": "Increase schedule margin",
                "details": "Schedule fails within 3 days of multi-absence in 50% of scenarios"
            })

    # Check fragile rotations
    fragile = monte_carlo_results["fragile_rotations"]
    critical_fragile = [r for r in fragile if r["failure_probability"] > 0.50]

    if critical_fragile:
        for rotation in critical_fragile:
            recommendations.append({
                "priority": "HIGH",
                "finding": f"Rotation {rotation['rotation_id']} fails in {rotation['failure_probability']:.1%} of scenarios",
                "action": f"Increase staffing or add backups for {rotation['rotation_id']}",
                "details": "This rotation is a single point of failure under multi-absence scenarios"
            })

    # Analyze worst-case scenario
    if worst_case:
        recommendations.append({
            "priority": "MEDIUM",
            "finding": f"Worst-case scenario: {worst_case['absent_residents']} absent simultaneously",
            "action": "Document contingency plan for this specific scenario",
            "details": f"Impact score: {worst_case['impact']['score']}, "
                      f"Rotations affected: {len(worst_case['impact']['failed_rotations'])}"
        })

    return recommendations
```

## Implementation Files

### Backend Service
```python
# backend/app/resilience/monte_carlo_sim.py

import random
import statistics
import itertools
from datetime import date
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.person import Person
from app.schemas.resilience import MultiFailureReport


class MonteCarloSimulator:
    """Monte Carlo simulation for multi-failure scenarios."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_simulation(
        self,
        trials: int = 10000,
        min_failures: int = 2,
        max_failures: int = 3,
        duration_days: int = 7,
        start_date: Optional[date] = None
    ) -> MultiFailureReport:
        """
        Run Monte Carlo simulation for multi-failure scenarios.

        Args:
            trials: Number of random trials to run
            min_failures: Minimum simultaneous absences
            max_failures: Maximum simultaneous absences
            duration_days: How long absences last
            start_date: When absences start (default: today)

        Returns:
            MultiFailureReport with collapse probability, fragile rotations, worst case
        """
        # Implementation details...
        pass

    async def find_worst_case(
        self,
        duration_days: int = 7,
        start_date: Optional[date] = None
    ) -> Dict:
        """Find worst-case scenario through systematic testing."""
        # Implementation details...
        pass
```

### API Endpoint
```python
# backend/app/api/routes/resilience.py

@router.post("/simulate-failure", response_model=MultiFailureReport)
async def simulate_multi_failure(
    request: MultiFailureRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run Monte Carlo simulation for multi-failure scenarios.

    Tests schedule resilience under multiple simultaneous absences.
    """
    simulator = MonteCarloSimulator(db)

    report = await simulator.run_simulation(
        trials=request.trials or 10000,
        min_failures=request.min_failures or 2,
        max_failures=request.max_failures or 3,
        duration_days=request.duration_days or 7,
        start_date=request.start_date or date.today()
    )

    return report
```

## Usage Examples

### Example 1: Standard Monte Carlo (10,000 trials)
```bash
curl -X POST http://localhost:8000/api/resilience/simulate-failure \
  -H "Content-Type: application/json" \
  -d '{
    "trials": 10000,
    "min_failures": 2,
    "max_failures": 3,
    "duration_days": 7
  }'
```

**Expected Output:**
```json
{
  "trials_run": 10000,
  "collapse_count": 1234,
  "collapse_probability": 0.1234,
  "median_time_to_failure": 4.2,
  "p95_time_to_failure": 1.1,
  "fragile_rotations": [
    {
      "rotation_id": "EM Night Shift",
      "failure_count": 7800,
      "failure_probability": 0.78,
      "severity": "CRITICAL"
    },
    {
      "rotation_id": "Peds Clinic",
      "failure_count": 4500,
      "failure_probability": 0.45,
      "severity": "HIGH"
    }
  ],
  "worst_scenario": {
    "absent_residents": ["PGY2-03", "PGY3-01"],
    "impact_score": 245,
    "failed_rotations": ["EM Night Shift", "Peds Clinic"],
    "acgme_violations": 3
  },
  "recommendations": [
    {
      "priority": "CRITICAL",
      "finding": "Collapse probability 12.3% exceeds 10% threshold",
      "action": "DO NOT DEPLOY THIS SCHEDULE"
    }
  ]
}
```

### Example 2: Quick Assessment (1,000 trials)
```bash
curl -X POST http://localhost:8000/api/resilience/simulate-failure \
  -H "Content-Type: application/json" \
  -d '{
    "trials": 1000,
    "min_failures": 2,
    "max_failures": 2,
    "duration_days": 7
  }'
```

### Example 3: Worst-Case Analysis
```bash
curl -X POST http://localhost:8000/api/resilience/worst-case \
  -H "Content-Type: application/json" \
  -d '{
    "duration_days": 7
  }'
```

## Interpretation Guide

### Collapse Probability

| Probability | Status | Meaning | Action |
|-------------|--------|---------|--------|
| < 5% | EXCELLENT | Robust under multi-failure | Monitor quarterly |
| 5-10% | ACCEPTABLE | Some risk, but manageable | Monitor monthly |
| 10-20% | HIGH RISK | Likely to fail under stress | Mitigation required |
| > 20% | UNACCEPTABLE | Will fail | DO NOT DEPLOY |

### Time-to-Failure

| Median TTF | Interpretation |
|------------|----------------|
| > 7 days | Schedule can withstand 1 week of multi-absence |
| 3-7 days | Moderate resilience, requires active monitoring |
| 1-3 days | Fragile, failure imminent under stress |
| < 1 day | Critical, fails immediately |

### Fragile Rotation Severity

- **CRITICAL** (>50% failure rate): Single point of failure, must address
- **HIGH** (25-50% failure rate): Significant vulnerability, mitigation recommended
- **MEDIUM** (10-25% failure rate): Moderate risk, monitor closely
- **LOW** (<10% failure rate): Acceptable resilience

## Troubleshooting

### Issue: Simulation times out
**Cause**: Too many trials or complex schedule
**Fix**: Reduce trials from 10,000 → 1,000 for initial analysis

### Issue: Collapse probability = 0 (seems unrealistic)
**Cause**: Simulation parameters too lenient or schedule overstaffed
**Fix**: Verify min_failures/max_failures are realistic (try 3-4 simultaneous absences)

### Issue: All rotations marked as fragile
**Cause**: Schedule is fundamentally over-constrained
**Fix**: Reduce rotation minimum staffing or add more residents

## Success Criteria

- ✅ 10,000+ trials run (or 1,000+ for quick assessment)
- ✅ Collapse probability quantified
- ✅ Fragile rotations ranked by failure probability
- ✅ Worst-case scenario identified
- ✅ Actionable recommendations generated
- ✅ Results saved to database for historical tracking

## Next Steps

After multi-failure analysis:
1. If collapse probability > 10%: **DO NOT DEPLOY** → Re-generate schedule
2. If median TTF < 3 days: Run **recovery time analysis** (`Workflows/recovery-time-analysis.md`)
3. Document fragile rotations in incident response plan
4. Re-run after implementing mitigations to verify improvement

---

*This workflow stress-tests schedule resilience under realistic compound failure scenarios.*
