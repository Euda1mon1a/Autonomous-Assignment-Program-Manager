# TypedDict Type Safety Guide

This document describes the TypedDict patterns used throughout the Residency Scheduler for improved type safety, IDE support, and self-documenting code.

## Overview

TypedDict provides a way to define dictionary types with specific keys and value types. Unlike regular `dict[str, Any]`, TypedDict enables:

- **Type checking**: Catch errors at development time
- **IDE autocomplete**: Better developer experience
- **Self-documentation**: Clear data structure contracts
- **Runtime compatibility**: Works with existing dict-based code

---

## Core Types (`backend/app/core/types.py`)

### Schedule Metrics

```python
class ScheduleGenerationMetrics(TypedDict):
    """Detailed metrics from schedule generation."""
    algorithm_used: str
    solver_time_seconds: float
    iterations: int
    assignments_created: int
    coverage_rate: float
    conflicts_resolved: int
    constraints_satisfied: int
    constraints_violated: int
    fairness_score: NotRequired[float]
    optimization_objective: NotRequired[str]
    memory_peak_mb: NotRequired[float]
    parallel_workers: NotRequired[int]
```

### Compliance Results

```python
class ComplianceResult(TypedDict):
    """ACGME compliance check result."""
    is_compliant: bool
    violations: list[str]
    warnings: NotRequired[list[str]]
    checked_at: str
    rule_type: str  # "80_hour", "1_in_7", "supervision"

class ValidationResultDict(TypedDict):
    """General validation result structure."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    field_errors: NotRequired[dict[str, list[str]]]
    validated_at: NotRequired[str]
    validator_version: NotRequired[str]
```

### Swap Operations

```python
class SwapDetails(TypedDict):
    """Comprehensive swap execution details."""
    success: bool
    swap_id: str
    swap_type: str
    source_faculty_id: str
    source_faculty_name: str
    target_faculty_id: str
    target_faculty_name: str
    source_assignment_id: str
    target_assignment_id: NotRequired[str]
    executed_at: str
    executed_by: str
    rollback_deadline: NotRequired[str]
    rollback_available: bool
    affected_blocks: list[str]
    compliance_verified: bool
```

### Coverage Reporting

```python
class CoverageReportItem(TypedDict):
    """Coverage statistics for a specific period."""
    period_start: str
    period_end: str
    total_blocks: int
    covered_blocks: int
    coverage_percentage: float
    understaffed_blocks: NotRequired[int]
    overstaffed_blocks: NotRequired[int]

class CoverageReport(TypedDict):
    """Schedule coverage statistics for a date range."""
    start_date: str
    end_date: str
    overall_coverage: float
    daily_breakdown: list[CoverageReportItem]
    rotation_coverage: dict[str, float]
    gap_count: int
    critical_gaps: NotRequired[list[str]]
    recommendations: NotRequired[list[str]]
    generated_at: str
```

### Resilience Framework

```python
class ResilienceAnalysisResult(TypedDict):
    """Extended resilience metrics with N-1/N-2 analysis."""
    health_score: float
    defense_level: Literal["GREEN", "YELLOW", "ORANGE", "RED", "BLACK"]
    n1_pass: bool
    n2_pass: bool
    single_point_failures: list[str]
    vulnerable_rotations: list[str]
    utilization_rate: float
    compensation_debt: float
    cascade_risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    recommendations: list[str]
    analyzed_at: str
    analysis_duration_ms: NotRequired[int]
```

---

## MTF Compliance Types (`backend/app/resilience/mtf_compliance.py`)

### System State

```python
class SystemStateDict(TypedDict):
    """Dictionary representation of system health state."""
    n1_pass: bool
    n2_pass: bool
    coverage_rate: float
    average_allostatic_load: float
    load_shedding_level: str
    equilibrium_state: str
    phase_transition_risk: str
    compensation_debt: float
    volatility_level: str
```

### Contingency Analysis

```python
class ContingencyAnalysisDict(TypedDict, total=False):
    """N-1/N-2 contingency analysis results."""
    n1_pass: bool
    n2_pass: bool
    single_point_failures: list[str]
    dual_point_failures: list[tuple[str, str]]
    vulnerable_rotations: list[str]
    risk_level: str
```

### Capacity Metrics

```python
class CapacityMetricsDict(TypedDict, total=False):
    """Capacity and utilization tracking."""
    capacity: int
    utilization: float
    deficit: int
    available_slots: int
    filled_slots: int
    coverage_percentage: float
```

### Cascade Prediction

```python
class CascadePredictionDict(TypedDict):
    """Cascade failure predictions for resource requests."""
    days_until_exhaustion: int
    probability: float
    trigger_event: str

class PositiveFeedbackRiskDict(TypedDict, total=False):
    """Positive feedback loop risk assessment."""
    confidence: float
    risk_type: str
    description: str
```

---

## Usage Patterns

### Creating TypedDict Instances

```python
from app.core.types import SwapDetails

def execute_swap(swap_id: str, ...) -> SwapDetails:
    return SwapDetails(
        success=True,
        swap_id=swap_id,
        swap_type="one_to_one",
        source_faculty_id="faculty-1",
        source_faculty_name="Dr. Smith",
        target_faculty_id="faculty-2",
        target_faculty_name="Dr. Jones",
        source_assignment_id="assignment-1",
        executed_at=datetime.now().isoformat(),
        executed_by="coordinator-1",
        rollback_available=True,
        affected_blocks=["block-1", "block-2"],
        compliance_verified=True
    )
```

### Type Checking with Optional Fields

```python
from typing import NotRequired

class MyResult(TypedDict):
    required_field: str
    optional_field: NotRequired[int]  # Can be omitted

# Valid usages:
result1: MyResult = {"required_field": "value"}
result2: MyResult = {"required_field": "value", "optional_field": 42}
```

### Using `total=False` for All-Optional

```python
class PartialUpdate(TypedDict, total=False):
    """All fields are optional."""
    name: str
    email: str
    status: str

# Any subset is valid:
update: PartialUpdate = {"name": "New Name"}
```

### Combining with Literal Types

```python
from typing import Literal

class StatusResult(TypedDict):
    status: Literal["pending", "approved", "rejected"]
    severity: Literal["low", "medium", "high", "critical"]
```

---

## Migration Guide

### From `dict[str, Any]`

**Before:**
```python
def get_metrics() -> dict[str, Any]:
    return {
        "coverage": 0.95,
        "violations": 2,
        "compliant": True
    }
```

**After:**
```python
from app.core.types import ComplianceResult

def get_metrics() -> ComplianceResult:
    return ComplianceResult(
        is_compliant=True,
        violations=["Minor violation 1", "Minor violation 2"],
        checked_at=datetime.now().isoformat(),
        rule_type="80_hour"
    )
```

### Gradual Migration

TypedDict is compatible with regular dicts, so you can migrate incrementally:

```python
# Old function still works
old_result: dict[str, Any] = old_function()

# New function returns TypedDict
new_result: ComplianceResult = new_function()

# Both can be used where dict is expected
process_result(old_result)  # Works
process_result(new_result)  # Also works
```

---

## IDE Support

### VS Code / Pylance

TypedDict provides full autocomplete and type checking:

```python
result = get_compliance()
result["is_compliant"]  # ✓ Autocomplete shows this
result["invalid_key"]   # ✗ Error: key not in TypedDict
result["violations"] = 5  # ✗ Error: expected list[str], got int
```

### mypy

Enable strict checking in `pyproject.toml`:

```toml
[tool.mypy]
plugins = ["pydantic.mypy"]
strict = true
```

Run type checking:

```bash
mypy backend/app/core/types.py
mypy backend/app/resilience/mtf_compliance.py
```

---

## Best Practices

1. **Use descriptive names**: `ComplianceResult` not `CR`
2. **Document with docstrings**: Explain the purpose of each TypedDict
3. **Use `NotRequired` for optional fields**: Clearer than `total=False`
4. **Use `Literal` for enum-like values**: Better than plain `str`
5. **Keep related types together**: Group by domain (compliance, resilience, etc.)
6. **Export from `__init__.py`**: Make types easily importable

---

## Files Reference

| File | TypedDicts | Purpose |
|------|------------|---------|
| `backend/app/core/types.py` | 31 | Core application types |
| `backend/app/resilience/mtf_compliance.py` | 6 | Resilience framework types |

---

## Testing Type Safety

```bash
# Run mypy on specific files
mypy backend/app/core/types.py --strict

# Run on entire codebase
mypy backend/app/ --config-file pyproject.toml

# Check with pytest
pytest backend/tests/ -v --mypy
```
