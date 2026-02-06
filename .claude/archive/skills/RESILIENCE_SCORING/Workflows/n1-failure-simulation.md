# Workflow: N-1 Failure Simulation

## Overview

Simulate the impact of each resident being absent for a specified duration. Identifies "critical" residents whose absence causes coverage failures and quantifies the blast radius of single-point failures.

## Purpose

Answer the question: **"What happens if one person is suddenly absent?"**

This is the most practical failure scenario (illness, emergency leave, TDY). Understanding N-1 resilience enables:
- Identifying critical residents (single points of failure)
- Proactive cross-training plans
- Prioritizing backup coverage
- Informing supplemental staffing decisions

## Workflow Steps

### Step 1: Define Simulation Parameters

```python
simulation_params = {
    "duration_days": 7,  # 1-week absence (typical illness)
    "start_date": date.today(),  # When does absence start
    "residents_to_test": "all",  # Or specific subset: ["PGY2-03", "PGY3-01"]
    "coverage_threshold": 1.0  # Rotation fails if < 100% of min_residents
}
```

### Step 2: Baseline Assessment

Before simulating failures, establish baseline coverage:

```python
# Get current schedule state
baseline = {
    "rotations": {},
    "work_hours": {},
    "continuity": {}
}

for rotation in active_rotations:
    actual_count = count_assigned_residents(rotation, date_range)
    required_count = rotation.min_residents
    baseline["rotations"][rotation.id] = {
        "actual": actual_count,
        "required": required_count,
        "margin": actual_count - required_count
    }

for resident in active_residents:
    baseline["work_hours"][resident.id] = calculate_4week_hours(resident)
    baseline["continuity"][resident.id] = calculate_continuity_score(resident)
```

### Step 3: Simulate Each Resident Absent

For each resident in the roster:

```python
results = {}

for resident in active_residents:
    # Simulate removing this resident for duration_days
    simulation = simulate_absence(
        resident_id=resident.id,
        start_date=simulation_params["start_date"],
        duration_days=simulation_params["duration_days"]
    )

    # Analyze impact
    impact = analyze_impact(baseline, simulation)

    results[resident.id] = {
        "classification": classify_resident(impact),  # "critical", "high-impact", "low-impact"
        "rotations_affected": impact["failed_rotations"],
        "understaffing_hours": impact["total_understaffed_hours"],
        "residents_impacted": impact["residents_needing_reassignment"],
        "acgme_violations": impact["acgme_violations"],
        "recovery_time_estimate": impact["recovery_days"]
    }
```

### Step 4: Impact Analysis

```python
def analyze_impact(baseline, simulation):
    """Quantify the delta between baseline and failure scenario."""

    impact = {
        "failed_rotations": [],
        "total_understaffed_hours": 0,
        "residents_needing_reassignment": [],
        "acgme_violations": [],
        "recovery_days": 0
    }

    # Check rotation coverage failures
    for rotation_id, rotation_data in simulation["rotations"].items():
        baseline_margin = baseline["rotations"][rotation_id]["margin"]
        sim_margin = rotation_data["margin"]

        if sim_margin < 0:  # Understaffed
            impact["failed_rotations"].append({
                "rotation": rotation_id,
                "shortfall": abs(sim_margin),
                "days_affected": rotation_data["days_below_minimum"]
            })
            impact["total_understaffed_hours"] += abs(sim_margin) * 24 * rotation_data["days_affected"]

    # Check residents who need reassignment to cover gap
    for resident_id, work_hours in simulation["work_hours"].items():
        baseline_hours = baseline["work_hours"][resident_id]
        added_hours = work_hours - baseline_hours

        if added_hours > 0:
            impact["residents_needing_reassignment"].append({
                "resident_id": resident_id,
                "added_hours": added_hours,
                "new_total_hours": work_hours
            })

            # Check if added hours push into ACGME violation
            if work_hours > 80:
                impact["acgme_violations"].append({
                    "resident_id": resident_id,
                    "violation_type": "80_hour_rule",
                    "hours": work_hours
                })

    # Estimate recovery time
    if impact["failed_rotations"]:
        # Complex recovery (need to find replacement)
        impact["recovery_days"] = max([r["days_affected"] for r in impact["failed_rotations"]])
    elif impact["residents_needing_reassignment"]:
        # Simple recovery (internal shuffle)
        impact["recovery_days"] = 1
    else:
        # No recovery needed (fully absorbed)
        impact["recovery_days"] = 0

    return impact
```

### Step 5: Classify Residents

```python
def classify_resident(impact):
    """
    Classify resident based on impact of their absence.

    Returns: "critical", "high-impact", or "low-impact"
    """

    # Critical: Absence causes coverage failure
    if impact["failed_rotations"]:
        return "critical"

    # High-impact: Absence causes significant burden but no hard failure
    if impact["residents_needing_reassignment"]:
        max_added_hours = max([r["added_hours"] for r in impact["residents_needing_reassignment"]])
        if max_added_hours > 10:  # Adding >10 hours/week to someone
            return "high-impact"

    # Low-impact: Absence absorbed with minimal redistribution
    return "low-impact"
```

### Step 6: Generate N-1 Vulnerability Matrix

```python
# Categorize results
critical_residents = [r for r, data in results.items() if data["classification"] == "critical"]
high_impact_residents = [r for r, data in results.items() if data["classification"] == "high-impact"]
low_impact_residents = [r for r, data in results.items() if data["classification"] == "low-impact"]

# Build matrix
vulnerability_matrix = {
    "critical_count": len(critical_residents),
    "high_impact_count": len(high_impact_residents),
    "low_impact_count": len(low_impact_residents),
    "details": {
        "critical": [
            {
                "resident_id": r,
                "rotations_at_risk": results[r]["rotations_affected"],
                "understaffing_hours": results[r]["understaffing_hours"],
                "recovery_days": results[r]["recovery_time_estimate"]
            }
            for r in critical_residents
        ],
        "high_impact": [
            {
                "resident_id": r,
                "impacted_residents": results[r]["residents_impacted"],
                "max_added_burden": max([p["added_hours"] for p in results[r]["residents_impacted"]])
            }
            for r in high_impact_residents
        ]
    },
    "recommendations": generate_n1_recommendations(results)
}
```

### Step 7: Generate Recommendations

```python
def generate_n1_recommendations(results):
    """Generate actionable recommendations based on N-1 analysis."""

    recommendations = []

    critical_residents = [r for r, data in results.items() if data["classification"] == "critical"]

    if len(critical_residents) > 0:
        recommendations.append({
            "priority": "HIGH",
            "action": f"Critical: {len(critical_residents)} single points of failure detected",
            "details": "Cross-train backup residents or add supplemental staff for these rotations",
            "affected_residents": critical_residents
        })

    # Identify rotation-specific vulnerabilities
    rotation_vulnerability = {}
    for resident_id, data in results.items():
        if data["classification"] == "critical":
            for rotation in data["rotations_affected"]:
                rotation_id = rotation["rotation"]
                if rotation_id not in rotation_vulnerability:
                    rotation_vulnerability[rotation_id] = []
                rotation_vulnerability[rotation_id].append(resident_id)

    for rotation_id, resident_list in rotation_vulnerability.items():
        if len(resident_list) > 1:
            recommendations.append({
                "priority": "MEDIUM",
                "action": f"Rotation {rotation_id} vulnerable to multiple residents",
                "details": f"If any of {len(resident_list)} residents absent, coverage fails",
                "mitigation": "Increase minimum staffing or cross-train backups"
            })

    # Check for PGY-year imbalance
    pgy_critical_count = {}
    for resident_id in critical_residents:
        pgy_year = get_pgy_year(resident_id)
        pgy_critical_count[pgy_year] = pgy_critical_count.get(pgy_year, 0) + 1

    for pgy_year, count in pgy_critical_count.items():
        if count > len(critical_residents) / 2:
            recommendations.append({
                "priority": "MEDIUM",
                "action": f"PGY-{pgy_year} over-represented in critical residents",
                "details": "Consider more balanced rotation distribution across PGY years"
            })

    return recommendations
```

## Implementation Files

### Backend Service
```python
# backend/app/resilience/n_minus_analysis.py

from datetime import date, timedelta
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.person import Person
from app.models.rotation import Rotation
from app.schemas.resilience import N1AnalysisReport, ResidentImpact


class N1Simulator:
    """Simulate N-1 failure scenarios (single resident absence)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_n1_analysis(
        self,
        start_date: date,
        duration_days: int = 7,
        residents_to_test: Optional[List[str]] = None
    ) -> N1AnalysisReport:
        """
        Run N-1 failure simulation for all (or specified) residents.

        Args:
            start_date: When absence starts
            duration_days: How long absence lasts (default 7 days)
            residents_to_test: Specific residents to test, or None for all

        Returns:
            N1AnalysisReport with vulnerability matrix and recommendations
        """
        # Get baseline state
        baseline = await self._get_baseline(start_date, duration_days)

        # Determine which residents to test
        if residents_to_test is None:
            residents_to_test = await self._get_all_active_residents(start_date)

        # Run simulation for each resident
        results = {}
        for resident_id in residents_to_test:
            impact = await self._simulate_absence(
                resident_id, start_date, duration_days, baseline
            )
            results[resident_id] = impact

        # Analyze results
        vulnerability_matrix = self._build_vulnerability_matrix(results)
        recommendations = self._generate_recommendations(results)

        return N1AnalysisReport(
            simulation_date=start_date,
            duration_days=duration_days,
            residents_tested=len(residents_to_test),
            vulnerability_matrix=vulnerability_matrix,
            recommendations=recommendations,
            timestamp=datetime.utcnow()
        )

    async def _simulate_absence(
        self,
        resident_id: str,
        start_date: date,
        duration_days: int,
        baseline: Dict
    ) -> ResidentImpact:
        """Simulate removal of one resident and assess impact."""
        # Implementation details...
        pass
```

### API Endpoint
```python
# backend/app/api/routes/resilience.py

@router.post("/n-minus-analysis", response_model=N1AnalysisReport)
async def run_n1_analysis(
    request: N1AnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run N-1 failure simulation.

    Simulates each resident being absent and identifies critical residents.
    """
    simulator = N1Simulator(db)

    report = await simulator.run_n1_analysis(
        start_date=request.start_date or date.today(),
        duration_days=request.duration_days or 7,
        residents_to_test=request.residents_to_test
    )

    return report
```

## Usage Examples

### Example 1: Run Full N-1 Analysis
```bash
curl -X POST http://localhost:8000/api/resilience/n-minus-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-15",
    "duration_days": 7
  }'
```

**Expected Output:**
```json
{
  "simulation_date": "2025-01-15",
  "duration_days": 7,
  "residents_tested": 24,
  "vulnerability_matrix": {
    "critical_count": 2,
    "high_impact_count": 5,
    "low_impact_count": 17,
    "details": {
      "critical": [
        {
          "resident_id": "PGY2-03",
          "rotations_at_risk": ["EM Night Shift"],
          "understaffing_hours": 168,
          "recovery_days": 7
        },
        {
          "resident_id": "PGY3-01",
          "rotations_at_risk": ["Peds Clinic"],
          "understaffing_hours": 80,
          "recovery_days": 5
        }
      ]
    }
  },
  "recommendations": [
    {
      "priority": "HIGH",
      "action": "Critical: 2 single points of failure detected",
      "details": "Cross-train backup residents or add supplemental staff for these rotations",
      "affected_residents": ["PGY2-03", "PGY3-01"]
    }
  ]
}
```

### Example 2: Test Specific Residents
```bash
curl -X POST http://localhost:8000/api/resilience/n-minus-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "residents_to_test": ["PGY2-03", "PGY2-05", "PGY3-01"],
    "duration_days": 14
  }'
```

### Example 3: Programmatic Check
```python
from app.resilience.n_minus_analysis import N1Simulator

async def identify_critical_residents(db):
    simulator = N1Simulator(db)

    report = await simulator.run_n1_analysis(
        start_date=date.today(),
        duration_days=7
    )

    if report.vulnerability_matrix["critical_count"] > 0:
        print("ALERT: Critical residents detected:")
        for critical in report.vulnerability_matrix["details"]["critical"]:
            print(f"  - {critical['resident_id']}: {critical['rotations_at_risk']}")

    return report
```

## Interpretation Guide

### Critical Residents
**Definition**: Absence causes rotation to fall below minimum staffing

**Action Required**:
1. Immediate: Identify backup residents for these rotations
2. Short-term: Cross-train 1-2 residents as backups
3. Long-term: Increase rotation minimum staffing or add supplemental staff

**Example**:
```
PGY2-03 is critical for EM Night Shift
→ If PGY2-03 is absent, EM Night has only 1 resident (requires 2)
→ Action: Train PGY2-05 and PGY3-02 as EM Night backups
```

### High-Impact Residents
**Definition**: Absence requires significant redistribution (>10 hours/week added to others)

**Action Required**:
1. Document who can absorb their workload
2. Ensure absorbing residents are below 70 work hours (room for +10)
3. Consider rotating backup assignments monthly

### Low-Impact Residents
**Definition**: Absence absorbed with minimal redistribution (<10 hours/week)

**No Action Required**: Schedule has sufficient slack to handle these absences

## Troubleshooting

### Issue: All residents classified as "critical"
**Cause**: Schedule is over-constrained (too tight)
**Fix**: Reduce rotation minimum staffing or add more residents to pool

### Issue: No residents classified as "critical" (seems too good)
**Cause**: Minimum staffing requirements not configured properly
**Fix**: Verify `rotations.min_residents` is set correctly
```sql
SELECT name, min_residents FROM rotations WHERE min_residents IS NULL;
```

### Issue: Simulation times out
**Cause**: Too many residents or long duration
**Fix**: Test in batches or reduce duration_days from 14 → 7

## Success Criteria

- ✅ All active residents tested (or specified subset)
- ✅ Residents classified as critical/high-impact/low-impact
- ✅ Specific rotations at risk identified for each critical resident
- ✅ Recommendations are actionable (specific cross-training suggestions)
- ✅ Results saved to database for historical tracking

## Next Steps

After N-1 analysis:
1. If critical_count > 3: Run **multi-failure scenarios** (`Workflows/multi-failure-scenarios.md`)
2. Document critical residents in incident response plan
3. Schedule quarterly re-assessment (residents change rotations)
4. Track whether cross-training recommendations were implemented

---

*This workflow identifies single points of failure in the schedule and enables proactive mitigation.*
