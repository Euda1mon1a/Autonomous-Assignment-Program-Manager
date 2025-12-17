***REMOVED*** StabilityMetrics Usage Guide

***REMOVED******REMOVED*** Overview

The `stability_metrics.py` module provides comprehensive stability analysis for schedule changes, tracking churn rates, cascade effects, and vulnerability assessment.

***REMOVED******REMOVED*** Key Metrics

***REMOVED******REMOVED******REMOVED*** 1. Assignments Changed
Raw count of how many assignments differ from the previous version.

***REMOVED******REMOVED******REMOVED*** 2. Churn Rate (0.0 - 1.0)
Percentage of the schedule that changed from the previous version.
- **< 0.15**: Stable (good)
- **0.15 - 0.30**: Moderate churn (acceptable)
- **> 0.30**: High churn (major refactoring)

***REMOVED******REMOVED******REMOVED*** 3. Ripple Factor (average hops)
How far changes cascade through the dependency network. Uses NetworkX graph analysis to measure impact propagation.
- **< 2.0**: Changes are localized
- **2.0 - 4.0**: Moderate cascading
- **> 4.0**: Wide-ranging impact

***REMOVED******REMOVED******REMOVED*** 4. N-1 Vulnerability Score (0.0 - 1.0)
Single-point-of-failure risk. Measures how vulnerable the schedule is to losing any one person.
- **< 0.3**: Low vulnerability (good redundancy)
- **0.3 - 0.5**: Moderate risk
- **> 0.5**: High risk (critical dependencies)

***REMOVED******REMOVED******REMOVED*** 5. New Violations
Count of new constraint violations introduced by changes.

***REMOVED******REMOVED******REMOVED*** 6. Days Since Major Change
Time since last schedule refactoring (churn > 30%).

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Basic Usage

```python
from sqlalchemy.orm import Session
from app.analytics.stability_metrics import compute_stability_metrics

***REMOVED*** Simple computation
def analyze_schedule_stability(db: Session):
    metrics = compute_stability_metrics(db)

    print(f"Churn Rate: {metrics['churn_rate']:.1%}")
    print(f"Stability Grade: {metrics['stability_grade']}")
    print(f"Is Stable: {metrics['is_stable']}")

    return metrics
```

***REMOVED******REMOVED******REMOVED*** Date Range Analysis

```python
from datetime import date
from app.analytics.stability_metrics import StabilityMetricsComputer

def analyze_quarter_stability(db: Session):
    computer = StabilityMetricsComputer(db)

    metrics = computer.compute_stability_metrics(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
    )

    if not metrics.is_stable:
        print(f"⚠️ Schedule instability detected!")
        print(f"  - Churn: {metrics.churn_rate:.1%}")
        print(f"  - N-1 Vulnerability: {metrics.n1_vulnerability_score:.2f}")
        print(f"  - New Violations: {metrics.new_violations}")

    return metrics
```

***REMOVED******REMOVED******REMOVED*** Integration with API Endpoint

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.analytics import compute_stability_metrics

router = APIRouter()

@router.get("/analytics/stability")
async def get_stability_metrics(
    db: Session = Depends(get_db),
) -> dict:
    """
    Get current schedule stability metrics.

    Returns:
        Dictionary with stability analysis including:
        - churn_rate: Percentage of schedule that changed
        - ripple_factor: Cascade effect measurement
        - n1_vulnerability_score: Single-point-of-failure risk
        - stability_grade: Letter grade (A-F)
        - is_stable: Boolean stability indicator
    """
    return compute_stability_metrics(db)
```

***REMOVED******REMOVED******REMOVED*** Custom Analysis with StabilityMetricsComputer

```python
from app.analytics.stability_metrics import StabilityMetricsComputer

def detailed_stability_analysis(db: Session):
    computer = StabilityMetricsComputer(db)

    ***REMOVED*** Compute metrics
    metrics = computer.compute_stability_metrics()

    ***REMOVED*** Access individual components
    churn_data = computer._calculate_churn_rate(
        old_assignments=[],  ***REMOVED*** Would fetch from version history
        new_assignments=current_assignments,
    )

    print(f"Added: {len(churn_data['added'])}")
    print(f"Removed: {len(churn_data['removed'])}")
    print(f"Modified: {len(churn_data['modified'])}")

    ***REMOVED*** N-1 vulnerability breakdown
    vulnerability = computer._calculate_n1_vulnerability(current_assignments)
    print(f"Single-point-of-failure risk: {vulnerability:.2%}")

    return metrics
```

***REMOVED******REMOVED*** StabilityMetrics Object

The `StabilityMetrics` dataclass provides convenient properties:

```python
metrics = compute_stability_metrics(db)

***REMOVED*** Check stability status
if metrics.is_stable:
    print("✓ Schedule is stable")
else:
    print("✗ Schedule instability detected")

***REMOVED*** Get letter grade
grade = metrics.stability_grade  ***REMOVED*** "A", "B", "C", "D", or "F"

***REMOVED*** Convert to dictionary for JSON API responses
metrics_dict = metrics.to_dict()
```

***REMOVED******REMOVED*** Stability Grading System

| Grade | Criteria |
|-------|----------|
| **A** | Churn < 10%, Ripple < 1.5, Vulnerability < 0.2, No violations |
| **B** | Churn < 20%, Ripple < 2.5, Vulnerability < 0.4, No violations |
| **C** | Churn < 30%, Ripple < 3.5, Vulnerability < 0.6, No violations |
| **D** | Churn < 40%, Ripple < 4.5, Vulnerability < 0.8, No violations |
| **F** | High churn OR any violations |

***REMOVED******REMOVED*** Integration with Version History

The module is designed to work with SQLAlchemy-Continuum version tracking:

```python
***REMOVED*** Future integration (when version history is implemented)
from app.models.assignment import Assignment

def compare_versions(db: Session, version_a_id: str, version_b_id: str):
    """Compare stability between two schedule versions."""
    computer = StabilityMetricsComputer(db)

    ***REMOVED*** Would load assignments at specific versions
    ***REMOVED*** assignments_v1 = load_version(version_a_id)
    ***REMOVED*** assignments_v2 = load_version(version_b_id)

    ***REMOVED*** Calculate churn between versions
    churn_data = computer._calculate_churn_rate(
        old_assignments=assignments_v1,
        new_assignments=assignments_v2,
    )

    return churn_data
```

***REMOVED******REMOVED*** Dependencies

- **SQLAlchemy**: Database access
- **NetworkX** (optional): Enhanced dependency graph analysis for ripple factor
  - If not installed, falls back to basic methods
  - Install with: `pip install networkx`

***REMOVED******REMOVED*** Testing

Run the comprehensive test suite:

```bash
cd backend
pytest tests/test_stability_metrics.py -v
```

Test coverage includes:
- StabilityMetrics dataclass properties
- Churn rate calculation
- N-1 vulnerability scoring
- Ripple factor analysis (with/without NetworkX)
- Stability grading
- Edge cases (empty schedules, first versions)

***REMOVED******REMOVED*** Performance Considerations

- **Complexity**: O(n) for most operations, O(n²) for dependency graph with n assignments
- **NetworkX overhead**: Graph construction scales with assignment count
- **Version history**: Future implementation will query Continuum tables

***REMOVED******REMOVED*** Future Enhancements

1. **Version History Integration**
   - Query SQLAlchemy-Continuum transaction tables
   - Reconstruct historical assignment states
   - Automated major change detection

2. **Violation Integration**
   - Link to `ACGMEValidator` for real violation counting
   - Track violation trends over time

3. **Predictive Analysis**
   - Predict stability impact before applying changes
   - "What-if" analysis for proposed swaps

4. **Alerting**
   - Automated alerts for instability thresholds
   - Integration with notification system

***REMOVED******REMOVED*** Related Modules

- `app.analytics.metrics`: Other metric calculations (fairness, coverage)
- `app.resilience.hub_analysis`: N-1 vulnerability detailed analysis
- `app.scheduling.validator`: ACGME constraint validation
- `app.models.assignment`: Assignment model with version tracking

***REMOVED******REMOVED*** Support

For questions or issues, refer to:
- Main documentation: `PROJECT_STATUS_ASSESSMENT.md`
- Analytics module: `backend/app/analytics/`
- Test examples: `backend/tests/test_stability_metrics.py`
