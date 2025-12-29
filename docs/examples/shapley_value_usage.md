# Shapley Value Calculator - Usage Guide

## Overview

The Shapley Value Service implements cooperative game theory to ensure fair workload distribution among faculty based on their marginal contributions to schedule coverage.

**Mathematical Foundation:**
```
φᵢ(v) = Σ [|S|!(n-|S|-1)!/n!] × [v(S∪{i}) - v(S)]
```

Where:
- `φᵢ(v)` = Shapley value for faculty i (fair share of total workload)
- `S` = coalition of faculty (subset not containing i)
- `v(S)` = value function (total coverage provided by coalition S)
- `n` = total number of faculty

## Key Concepts

### 1. Shapley Value (0-1)
**Normalized proportion** of total workload based on marginal contribution.

Example: `0.35` means this faculty contributes 35% of total coverage value.

### 2. Marginal Contribution
**Value added** when this faculty joins the team (measured in blocks covered).

Example: `42.5 blocks` = this faculty uniquely covers 42.5 half-day blocks that wouldn't be covered otherwise.

### 3. Fair Workload Target
**Hours this faculty should work** based on their Shapley proportion of total workload.

Formula: `Fair Target = Shapley Value × Total Hours Worked`

### 4. Equity Gap
**Difference between actual and fair workload** in hours.
- **Positive gap** = Overworked (working more than fair share)
- **Negative gap** = Underworked (working less than fair share)

## Basic Usage

### Calculate Shapley Values

```python
from datetime import date
from app.services.shapley_values import get_shapley_value_service

# Initialize service (in route handler with dependency injection)
service = get_shapley_value_service(db)

# Calculate for Q1 2024
results = await service.calculate_shapley_values(
    faculty_ids=[fac1_id, fac2_id, fac3_id],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 3, 31),
    num_samples=2000  # Higher = more accurate (default: 1000)
)

# Access individual results
for faculty_id, result in results.items():
    print(f"{result.faculty_name}:")
    print(f"  Shapley Value: {result.shapley_value:.2%}")
    print(f"  Current: {result.current_workload:.1f} hours")
    print(f"  Fair Target: {result.fair_workload_target:.1f} hours")
    print(f"  Equity Gap: {result.equity_gap:+.1f} hours")
```

**Output Example:**
```
Dr. Smith:
  Shapley Value: 35.2%
  Current: 320.0 hours
  Fair Target: 280.5 hours
  Equity Gap: +39.5 hours  ← Overworked by 39.5 hours

Dr. Jones:
  Shapley Value: 32.8%
  Current: 240.0 hours
  Fair Target: 261.4 hours
  Equity Gap: -21.4 hours  ← Underworked by 21.4 hours
```

## Advanced Features

### Generate Comprehensive Equity Report

```python
report = await service.get_equity_report(
    faculty_ids=all_faculty,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    num_samples=3000
)

# Summary statistics
print(f"Total Workload: {report.total_workload:.0f} hours")
print(f"Equity Gap Std Dev: {report.equity_gap_std_dev:.1f} hours")
print(f"Overworked: {report.overworked_count} faculty")
print(f"Underworked: {report.underworked_count} faculty")

# Identify outliers
most_overworked = next(
    r for r in report.faculty_results
    if r.faculty_id == report.most_overworked_faculty_id
)
print(f"Most Overworked: {most_overworked.faculty_name} (+{most_overworked.equity_gap:.1f} hours)")
```

### Get Workload Adjustment Recommendations

```python
suggestions = await service.suggest_workload_adjustments(
    faculty_ids=all_faculty,
    start_date=date(2024, 7, 1),
    end_date=date(2024, 9, 30),
    threshold=10.0  # Only suggest if gap > 10 hours
)

for suggestion in suggestions:
    print(f"{suggestion['faculty_name']}: {suggestion['action']} by {suggestion['hours']:.1f} hours")
    print(f"  Reason: {suggestion['reason']}")
```

**Output Example:**
```
Dr. Smith: reduce by 39.5 hours
  Reason: Working 39.5 hours above Shapley-fair target based on marginal contribution

Dr. Williams: increase by 28.2 hours
  Reason: Working 28.2 hours below Shapley-fair target based on marginal contribution
```

## Integration with Scheduling Engine

### Use Shapley Values as Fairness Constraints

```python
# In schedule generator
from app.services.shapley_values import get_shapley_value_service

# Calculate historical Shapley values
shapley_service = get_shapley_value_service(db)
historical_results = await shapley_service.calculate_shapley_values(
    faculty_ids=all_faculty,
    start_date=academic_year_start - timedelta(days=90),  # Previous quarter
    end_date=academic_year_start,
    num_samples=2000
)

# Use as soft constraints for next period
for faculty_id, result in historical_results.items():
    # Target workload based on Shapley proportion
    target_hours = result.fair_workload_target

    # Add constraint: faculty i should get ~target_hours ± tolerance
    solver.add_constraint(
        f"shapley_fairness_{faculty_id}",
        abs(assigned_hours[faculty_id] - target_hours) <= tolerance
    )
```

### Detect Systematic Inequity Over Time

```python
from datetime import timedelta

# Calculate Shapley values for each quarter
quarters = [
    (date(2024, 1, 1), date(2024, 3, 31)),
    (date(2024, 4, 1), date(2024, 6, 30)),
    (date(2024, 7, 1), date(2024, 9, 30)),
    (date(2024, 10, 1), date(2024, 12, 31)),
]

equity_trends = {}
for start, end in quarters:
    results = await shapley_service.calculate_shapley_values(
        faculty_ids=all_faculty,
        start_date=start,
        end_date=end,
    )

    for fac_id, result in results.items():
        if fac_id not in equity_trends:
            equity_trends[fac_id] = []
        equity_trends[fac_id].append(result.equity_gap)

# Flag faculty with persistent inequity
for fac_id, gaps in equity_trends.items():
    avg_gap = sum(gaps) / len(gaps)
    if abs(avg_gap) > 15.0:  # Average gap > 15 hours
        print(f"⚠️  {fac_id} has persistent inequity: {avg_gap:+.1f} hours/quarter")
```

## Performance Considerations

### Monte Carlo Sample Size

| Samples | Accuracy | Runtime | Use Case |
|---------|----------|---------|----------|
| 100 | ~10% variance | <1s | Quick check |
| 1000 | ~3% variance | ~2s | **Default** (recommended) |
| 2000 | ~2% variance | ~4s | High-stakes decisions |
| 5000 | ~1% variance | ~10s | Research/validation |

**Rule of thumb:** Use 1000 samples for routine calculations, 2000+ for critical fairness decisions.

### Caching Recommendations

Shapley calculations are expensive. Cache results:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_shapley_cached(faculty_tuple, start_date, end_date):
    """Cache Shapley results for 1 hour."""
    return await shapley_service.calculate_shapley_values(
        faculty_ids=list(faculty_tuple),
        start_date=start_date,
        end_date=end_date
    )

# Use immutable types for caching
results = await get_shapley_cached(
    tuple(sorted(faculty_ids)),  # Tuple instead of list
    start_date,
    end_date
)
```

## Theoretical Properties

The Shapley value satisfies four key axioms:

1. **Efficiency**: Sum of all Shapley values = total value
   ```python
   assert abs(sum(r.shapley_value for r in results.values()) - 1.0) < 0.01
   ```

2. **Symmetry**: Identical players get identical payoffs
   ```python
   # If Faculty A and B have identical assignments:
   assert abs(results[fac_a].shapley_value - results[fac_b].shapley_value) < 0.05
   ```

3. **Linearity**: Linear in the value function
   (Handled automatically by Monte Carlo approximation)

4. **Null Player**: Zero contribution → zero Shapley value
   ```python
   # If faculty has no assignments:
   assert results[idle_faculty].shapley_value < 0.05
   ```

## Common Patterns

### 1. Quarterly Fairness Review

```python
# Run at end of each quarter
report = await shapley_service.get_equity_report(
    faculty_ids=active_faculty,
    start_date=quarter_start,
    end_date=quarter_end,
    num_samples=2000
)

# Flag if equity gap std dev > threshold (unfair distribution)
if report.equity_gap_std_dev > 15.0:
    send_alert(f"Quarterly inequity detected: σ={report.equity_gap_std_dev:.1f} hours")
```

### 2. Pre-Schedule Validation

```python
# Before finalizing next block's schedule
future_results = await shapley_service.calculate_shapley_values(
    faculty_ids=all_faculty,
    start_date=next_block_start,
    end_date=next_block_end,
    num_samples=1000
)

# Check if new schedule would create large gaps
max_gap = max(abs(r.equity_gap) for r in future_results.values())
if max_gap > 20.0:
    print(f"⚠️  New schedule creates {max_gap:.1f} hour inequity - consider revision")
```

### 3. Faculty Burnout Detection

```python
# Combine Shapley equity with resilience metrics
from app.services.resilience import get_resilience_service

resilience_service = get_resilience_service(db)
shapley_service = get_shapley_value_service(db)

for faculty in all_faculty:
    # Check resilience health
    health = await resilience_service.get_person_health(faculty.id)

    # Check Shapley equity
    shapley_result = shapley_results[faculty.id]

    # Alert if overworked AND showing burnout signs
    if shapley_result.equity_gap > 15.0 and health.tier >= 3:
        send_alert(
            f"{faculty.name} is overworked (+{shapley_result.equity_gap:.1f} hours) "
            f"and showing burnout signs (Tier {health.tier})"
        )
```

## API Routes (Example)

```python
# backend/app/api/routes/game_theory.py

from fastapi import APIRouter, Depends
from app.services.shapley_values import get_shapley_value_service
from app.schemas.game_theory import ShapleyValueRequest, FacultyShapleyMetrics

router = APIRouter()

@router.post("/shapley-values", response_model=dict)
async def calculate_shapley_values(
    request: ShapleyValueRequest,
    service: ShapleyValueService = Depends(get_shapley_value_service)
):
    """Calculate Shapley values for faculty workload fairness."""
    results = await service.calculate_shapley_values(
        faculty_ids=request.faculty_ids,
        start_date=request.start_date.date(),
        end_date=request.end_date.date(),
        num_samples=request.num_samples
    )
    return {fac_id: result.dict() for fac_id, result in results.items()}

@router.post("/shapley-values/equity-report", response_model=FacultyShapleyMetrics)
async def get_equity_report(
    request: ShapleyValueRequest,
    service: ShapleyValueService = Depends(get_shapley_value_service)
):
    """Generate comprehensive equity report."""
    return await service.get_equity_report(
        faculty_ids=request.faculty_ids,
        start_date=request.start_date.date(),
        end_date=request.end_date.date(),
        num_samples=request.num_samples
    )
```

## References

- **Game Theory Quick Reference**: `docs/research/GAME_THEORY_QUICK_REFERENCE.md`
- **Full Research**: `docs/research/GAME_THEORY_SCHEDULING_RESEARCH.md`
- **Service Implementation**: `backend/app/services/shapley_values.py`
- **Schemas**: `backend/app/schemas/game_theory.py`
- **Tests**: `backend/tests/services/test_shapley_values.py`

## Further Reading

- Shapley, L.S. (1953). "A Value for n-person Games"
- Algorithmic Game Theory (Nisan et al.) - Chapter 9: Cooperative Games
- [Wikipedia: Shapley Value](https://en.wikipedia.org/wiki/Shapley_value)
