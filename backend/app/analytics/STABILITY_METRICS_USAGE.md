# StabilityMetrics Usage Guide

## Overview

The `stability_metrics.py` module provides comprehensive stability analysis for schedule changes, tracking churn rates, cascade effects, and vulnerability assessment.

## Key Metrics

### 1. Assignments Changed
Raw count of how many assignments differ from the previous version.

### 2. Churn Rate (0.0 - 1.0)
Percentage of the schedule that changed from the previous version.
- **< 0.15**: Stable (good)
- **0.15 - 0.30**: Moderate churn (acceptable)
- **> 0.30**: High churn (major refactoring)

### 3. Ripple Factor (average hops)
How far changes cascade through the dependency network. Uses NetworkX graph analysis to measure impact propagation.
- **< 2.0**: Changes are localized
- **2.0 - 4.0**: Moderate cascading
- **> 4.0**: Wide-ranging impact

### 4. N-1 Vulnerability Score (0.0 - 1.0)
Single-point-of-failure risk. Measures how vulnerable the schedule is to losing any one person.
- **< 0.3**: Low vulnerability (good redundancy)
- **0.3 - 0.5**: Moderate risk
- **> 0.5**: High risk (critical dependencies)

### 5. New Violations
Count of new constraint violations introduced by changes.

### 6. Days Since Major Change
Time since last schedule refactoring (churn > 30%).

## Usage Examples

### Basic Usage

```python
from sqlalchemy.orm import Session
from app.analytics.stability_metrics import compute_stability_metrics

# Simple computation
def analyze_schedule_stability(db: Session):
    metrics = compute_stability_metrics(db)

    print(f"Churn Rate: {metrics['churn_rate']:.1%}")
    print(f"Stability Grade: {metrics['stability_grade']}")
    print(f"Is Stable: {metrics['is_stable']}")

    return metrics
```

### Date Range Analysis

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

### Integration with API Endpoint

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

### Custom Analysis with StabilityMetricsComputer

```python
from app.analytics.stability_metrics import StabilityMetricsComputer

def detailed_stability_analysis(db: Session):
    computer = StabilityMetricsComputer(db)

    # Compute metrics
    metrics = computer.compute_stability_metrics()

    # Access individual components
    churn_data = computer._calculate_churn_rate(
        old_assignments=[],  # Would fetch from version history
        new_assignments=current_assignments,
    )

    print(f"Added: {len(churn_data['added'])}")
    print(f"Removed: {len(churn_data['removed'])}")
    print(f"Modified: {len(churn_data['modified'])}")

    # N-1 vulnerability breakdown
    vulnerability = computer._calculate_n1_vulnerability(current_assignments)
    print(f"Single-point-of-failure risk: {vulnerability:.2%}")

    return metrics
```

## StabilityMetrics Object

The `StabilityMetrics` dataclass provides convenient properties:

```python
metrics = compute_stability_metrics(db)

# Check stability status
if metrics.is_stable:
    print("✓ Schedule is stable")
else:
    print("✗ Schedule instability detected")

# Get letter grade
grade = metrics.stability_grade  # "A", "B", "C", "D", or "F"

# Convert to dictionary for JSON API responses
metrics_dict = metrics.to_dict()
```

## Stability Grading System

| Grade | Criteria |
|-------|----------|
| **A** | Churn < 10%, Ripple < 1.5, Vulnerability < 0.2, No violations |
| **B** | Churn < 20%, Ripple < 2.5, Vulnerability < 0.4, No violations |
| **C** | Churn < 30%, Ripple < 3.5, Vulnerability < 0.6, No violations |
| **D** | Churn < 40%, Ripple < 4.5, Vulnerability < 0.8, No violations |
| **F** | High churn OR any violations |

## Integration with Version History

The module is designed to work with SQLAlchemy-Continuum version tracking:

```python
# Future integration (when version history is implemented)
from app.models.assignment import Assignment

def compare_versions(db: Session, version_a_id: str, version_b_id: str):
    """Compare stability between two schedule versions."""
    computer = StabilityMetricsComputer(db)

    # Would load assignments at specific versions
    # assignments_v1 = load_version(version_a_id)
    # assignments_v2 = load_version(version_b_id)

    # Calculate churn between versions
    churn_data = computer._calculate_churn_rate(
        old_assignments=assignments_v1,
        new_assignments=assignments_v2,
    )

    return churn_data
```

## Dependencies

- **SQLAlchemy**: Database access
- **NetworkX** (optional): Enhanced dependency graph analysis for ripple factor
  - If not installed, falls back to basic methods
  - Install with: `pip install networkx`

## Testing

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

## Performance Considerations

- **Complexity**: O(n) for most operations, O(n²) for dependency graph with n assignments
- **NetworkX overhead**: Graph construction scales with assignment count
- **Version history**: Future implementation will query Continuum tables

## Future Enhancements

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

## Related Modules

- `app.analytics.metrics`: Other metric calculations (fairness, coverage)
- `app.resilience.hub_analysis`: N-1 vulnerability detailed analysis
- `app.scheduling.validator`: ACGME constraint validation
- `app.models.assignment`: Assignment model with version tracking

## Support

For questions or issues, refer to:
- Main documentation: `PROJECT_STATUS_ASSESSMENT.md`
- Analytics module: `backend/app/analytics/`
- Test examples: `backend/tests/test_stability_metrics.py`
