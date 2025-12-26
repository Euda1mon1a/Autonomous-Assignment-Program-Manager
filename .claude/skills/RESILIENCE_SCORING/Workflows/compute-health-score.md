***REMOVED*** Workflow: Compute Health Score

***REMOVED******REMOVED*** Overview

Calculate the current resilience health score for an active schedule. This is the primary metric for schedule robustness assessment.

***REMOVED******REMOVED*** Health Score Formula

**Overall Health = 0.4×Coverage + 0.3×Margin + 0.3×Continuity**

Each component is normalized to [0, 1] range.

***REMOVED******REMOVED*** Workflow Steps

***REMOVED******REMOVED******REMOVED*** Step 1: Calculate Coverage Component

Coverage measures whether rotations are adequately staffed relative to minimum requirements.

```python
***REMOVED*** For each rotation
for rotation in active_rotations:
    actual_residents = count_assigned_residents(rotation, date_range)
    required_residents = rotation.min_residents

    if required_residents > 0:
        coverage_ratio = min(actual_residents / required_residents, 1.5)
        ***REMOVED*** Normalize: 1.0 = exactly minimum, 1.5 = 150% (capped for scoring)
        rotation_coverage = min(coverage_ratio, 1.5) / 1.5
    else:
        rotation_coverage = 1.0  ***REMOVED*** No requirement = perfect coverage

    coverage_scores.append(rotation_coverage)

***REMOVED*** Aggregate across all rotations
coverage_component = mean(coverage_scores)
```

**Interpretation:**
- `coverage = 1.0`: All rotations at 150%+ of minimum (excellent buffer)
- `coverage = 0.67`: All rotations at exactly minimum staffing (tight)
- `coverage = 0.5`: Average rotation at 75% of minimum (understaffed)
- `coverage < 0.67`: Flag as warning

***REMOVED******REMOVED******REMOVED*** Step 2: Calculate Margin Component

Margin measures constraint slack - how close residents are to ACGME work hour limits.

```python
***REMOVED*** For each resident
for resident in active_residents:
    ***REMOVED*** Calculate 4-week rolling work hours
    work_hours = calculate_4week_rolling_hours(resident, current_date)
    max_hours = 80 * 4  ***REMOVED*** 320 hours per 4 weeks

    ***REMOVED*** Slack calculation
    slack_hours = max_hours - work_hours
    slack_ratio = slack_hours / max_hours

    ***REMOVED*** Normalize: 1.0 = 0 hours worked (unrealistic), 0.0 = at 80-hour limit
    resident_margin = slack_ratio

    margin_scores.append(resident_margin)

***REMOVED*** Aggregate across all residents
margin_component = mean(margin_scores)
```

**Interpretation:**
- `margin = 1.0`: Residents averaging 0 hours/week (impossible in practice)
- `margin = 0.75`: Residents averaging 20 hours/week (very light load)
- `margin = 0.5`: Residents averaging 40 hours/week (moderate load)
- `margin = 0.25`: Residents averaging 60 hours/week (heavy load, low slack)
- `margin = 0.0`: Residents at 80-hour limit (zero slack, critical)
- `margin < 0.3`: Flag as warning

**Additional Margin Checks:**
- **1-in-7 rule margin**: Days since last 24-hour off period
- **Call frequency margin**: Calls per month vs maximum (6-7 per month)

***REMOVED******REMOVED******REMOVED*** Step 3: Calculate Continuity Component

Continuity measures rotation stability - fewer mid-block switches = better continuity.

```python
***REMOVED*** For each resident
for resident in active_residents:
    ***REMOVED*** Get all rotation assignments in evaluation period
    assignments = get_assignments(resident, date_range)

    ***REMOVED*** Count mid-block switches (rotation change not on block boundary)
    mid_block_switches = 0
    for i in range(len(assignments) - 1):
        current_end = assignments[i].end_date
        next_start = assignments[i+1].start_date

        if next_start == current_end and assignments[i].rotation != assignments[i+1].rotation:
            ***REMOVED*** Check if switch happens mid-block (not on 2-week boundary)
            if current_end.day not in [1, 15]:  ***REMOVED*** Example: blocks start on 1st and 15th
                mid_block_switches += 1

    ***REMOVED*** Normalize: fewer switches = better continuity
    expected_blocks = len(date_range) // 14  ***REMOVED*** Assuming 2-week blocks
    continuity_ratio = 1.0 - (mid_block_switches / expected_blocks)

    continuity_scores.append(max(continuity_ratio, 0.0))

***REMOVED*** Aggregate across all residents
continuity_component = mean(continuity_scores)
```

**Interpretation:**
- `continuity = 1.0`: Zero mid-block switches (ideal)
- `continuity = 0.8`: 20% of blocks have mid-block switch (acceptable)
- `continuity = 0.5`: 50% of blocks have switch (chaotic)
- `continuity < 0.7`: Flag as warning

***REMOVED******REMOVED******REMOVED*** Step 4: Aggregate and Flag Warnings

```python
***REMOVED*** Compute overall health
coverage = coverage_component
margin = margin_component
continuity = continuity_component

health_score = 0.4 * coverage + 0.3 * margin + 0.3 * continuity

***REMOVED*** Generate warnings
warnings = []
if coverage < 0.67:
    warnings.append(f"Coverage below target: {coverage:.2f} (rotations understaffed)")
if margin < 0.30:
    warnings.append(f"Margin critically low: {margin:.2f} (residents near work hour limits)")
if continuity < 0.70:
    warnings.append(f"Continuity poor: {continuity:.2f} (excessive mid-block switches)")

***REMOVED*** Identify specific problem areas
low_coverage_rotations = [r for r in rotations if rotation_coverage_score(r) < 0.67]
high_utilization_residents = [r for r in residents if resident_margin_score(r) < 0.30]
high_churn_residents = [r for r in residents if resident_continuity_score(r) < 0.70]

***REMOVED*** Generate recommendations
recommendations = []
if low_coverage_rotations:
    recommendations.append(f"Add supplemental staff to: {', '.join([r.name for r in low_coverage_rotations])}")
if high_utilization_residents:
    recommendations.append(f"Reduce workload for: {', '.join([r.id for r in high_utilization_residents])}")
if high_churn_residents:
    recommendations.append(f"Stabilize rotations for: {', '.join([r.id for r in high_churn_residents])}")

***REMOVED*** Return complete report
return {
    "overall_health": health_score,
    "components": {
        "coverage": coverage,
        "margin": margin,
        "continuity": continuity
    },
    "status": get_health_status(health_score),
    "warnings": warnings,
    "recommendations": recommendations,
    "details": {
        "low_coverage_rotations": low_coverage_rotations,
        "high_utilization_residents": high_utilization_residents,
        "high_churn_residents": high_churn_residents
    }
}
```

***REMOVED******REMOVED*** Implementation Files

***REMOVED******REMOVED******REMOVED*** Backend Service
```python
***REMOVED*** backend/app/resilience/health_metrics.py

from datetime import date, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.assignment import Assignment
from app.models.person import Person
from app.models.rotation import Rotation
from app.schemas.resilience import HealthScoreReport


class HealthScoreCalculator:
    """Calculate resilience health score for active schedule."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_health_score(
        self,
        start_date: date,
        end_date: date
    ) -> HealthScoreReport:
        """
        Compute overall health score for date range.

        Args:
            start_date: Start of evaluation period
            end_date: End of evaluation period

        Returns:
            HealthScoreReport with score, components, warnings, recommendations
        """
        ***REMOVED*** Calculate each component
        coverage = await self._calculate_coverage(start_date, end_date)
        margin = await self._calculate_margin(start_date, end_date)
        continuity = await self._calculate_continuity(start_date, end_date)

        ***REMOVED*** Aggregate
        health_score = 0.4 * coverage + 0.3 * margin + 0.3 * continuity

        ***REMOVED*** Generate warnings and recommendations
        warnings = self._generate_warnings(coverage, margin, continuity)
        recommendations = await self._generate_recommendations(
            coverage, margin, continuity, start_date, end_date
        )

        return HealthScoreReport(
            overall_health=round(health_score, 3),
            components={
                "coverage": round(coverage, 3),
                "margin": round(margin, 3),
                "continuity": round(continuity, 3)
            },
            status=self._get_status(health_score),
            warnings=warnings,
            recommendations=recommendations,
            timestamp=datetime.utcnow()
        )

    async def _calculate_coverage(self, start_date: date, end_date: date) -> float:
        """Calculate rotation coverage component."""
        ***REMOVED*** Implementation details...
        pass

    async def _calculate_margin(self, start_date: date, end_date: date) -> float:
        """Calculate constraint margin component."""
        ***REMOVED*** Implementation details...
        pass

    async def _calculate_continuity(self, start_date: date, end_date: date) -> float:
        """Calculate rotation continuity component."""
        ***REMOVED*** Implementation details...
        pass
```

***REMOVED******REMOVED******REMOVED*** API Endpoint
```python
***REMOVED*** backend/app/api/routes/resilience.py

@router.get("/health", response_model=HealthScoreReport)
async def get_health_score(
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current resilience health score.

    If dates not provided, uses current date + 30 days.
    """
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=30)

    calculator = HealthScoreCalculator(db)
    health_report = await calculator.compute_health_score(start_date, end_date)

    return health_report
```

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Example 1: Check Current Month Health
```bash
curl http://localhost:8000/api/resilience/health
```

**Expected Output:**
```json
{
  "overall_health": 0.78,
  "components": {
    "coverage": 0.85,
    "margin": 0.72,
    "continuity": 0.76
  },
  "status": "GOOD",
  "warnings": [
    "Margin low for PGY-2 cohort: 0.68 (approaching work hour limits)"
  ],
  "recommendations": [
    "Reduce PGY-2 call frequency by 1 shift per month"
  ],
  "timestamp": "2025-12-26T10:00:00Z"
}
```

***REMOVED******REMOVED******REMOVED*** Example 2: Check Specific Date Range
```bash
curl "http://localhost:8000/api/resilience/health?start_date=2025-01-01&end_date=2025-01-31"
```

***REMOVED******REMOVED******REMOVED*** Example 3: Programmatic Check (Python)
```python
from app.resilience.health_metrics import HealthScoreCalculator
from datetime import date, timedelta

async def check_schedule_health(db):
    calculator = HealthScoreCalculator(db)

    start = date.today()
    end = start + timedelta(days=30)

    report = await calculator.compute_health_score(start, end)

    if report.overall_health < 0.70:
        print(f"WARNING: Health score {report.overall_health} below threshold")
        print(f"Warnings: {report.warnings}")
        print(f"Recommendations: {report.recommendations}")
    else:
        print(f"Schedule health OK: {report.overall_health}")

    return report
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Issue: Coverage component = 0
**Cause**: No rotation coverage requirements defined
**Fix**: Populate `min_residents` field for all rotations
```sql
UPDATE rotations SET min_residents = 2 WHERE name = 'EM Night Shift';
```

***REMOVED******REMOVED******REMOVED*** Issue: Margin component = 1.0 (unrealistic)
**Cause**: No assignments found in date range
**Fix**: Verify schedule has active assignments
```sql
SELECT COUNT(*) FROM assignments
WHERE start_date >= '2025-01-01' AND end_date <= '2025-01-31';
```

***REMOVED******REMOVED******REMOVED*** Issue: Continuity component calculation error
**Cause**: Block boundaries not properly configured
**Fix**: Verify rotation length and block structure in `rotations` table

***REMOVED******REMOVED*** Success Criteria

- ✅ Health score computed with all 3 components (not NULL)
- ✅ Each component is in [0, 1] range
- ✅ Warnings generated for components < threshold
- ✅ Recommendations are actionable (specific residents/rotations identified)
- ✅ Result saved to `resilience_health_checks` table for historical tracking

***REMOVED******REMOVED*** Next Steps

After computing health score:
1. If score < 0.70: Run **N-1 failure simulation** (`Workflows/n1-failure-simulation.md`)
2. If score < 0.50: Run **multi-failure scenarios** (`Workflows/multi-failure-scenarios.md`)
3. Document findings in `Reference/historical-resilience.md`
4. Schedule follow-up assessment after implementing recommendations

---

*This workflow implements the primary health assessment for schedule resilience.*
