# Scenario Validation Workflow

Comprehensive guide for validating scenario execution results against expected outcomes.

## Validation Pipeline

```
┌──────────────────┐
│  Load Expected   │
│  Outcomes        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Load Actual     │
│  Results         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Compare Values  │ ←─── Tolerance Rules
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Check State     │
│  Consistency     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Run Custom      │
│  Validators      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Categorize      │
│  Failures        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Generate        │
│  Validation      │
│  Report          │
└──────────────────┘
```

## Validation Types

### 1. Boolean Validation

```python
def validate_boolean(
    actual: bool,
    expected: bool,
    critical: bool = False
) -> ValidationResult:
    """Validate boolean assertion."""

    passed = actual == expected

    return ValidationResult(
        validation_type="boolean",
        expected=expected,
        actual=actual,
        passed=passed,
        critical=critical,
        message=f"Expected {expected}, got {actual}" if not passed else "OK"
    )
```

### 2. Numeric Validation with Tolerance

```python
def validate_numeric(
    actual: float,
    expected: float,
    tolerance: Optional[float] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    critical: bool = False
) -> ValidationResult:
    """Validate numeric assertion with tolerance."""

    passed = True
    messages = []

    # Check exact match with tolerance
    if expected is not None:
        if tolerance is not None:
            # Absolute tolerance
            if abs(actual - expected) > tolerance:
                passed = False
                messages.append(
                    f"Expected {expected} ± {tolerance}, got {actual}"
                )
        else:
            # Exact match
            if actual != expected:
                passed = False
                messages.append(f"Expected {expected}, got {actual}")

    # Check min bound
    if min_value is not None and actual < min_value:
        passed = False
        messages.append(f"Value {actual} below minimum {min_value}")

    # Check max bound
    if max_value is not None and actual > max_value:
        passed = False
        messages.append(f"Value {actual} above maximum {max_value}")

    return ValidationResult(
        validation_type="numeric",
        expected=expected,
        actual=actual,
        passed=passed,
        critical=critical,
        message="; ".join(messages) if messages else "OK",
        metadata={
            "tolerance": tolerance,
            "min": min_value,
            "max": max_value
        }
    )
```

### 3. String Validation

```python
import re

def validate_string(
    actual: str,
    expected: str,
    match_type: str = "exact",  # exact | contains | regex | case_insensitive
    critical: bool = False
) -> ValidationResult:
    """Validate string assertion."""

    if match_type == "exact":
        passed = actual == expected
        message = f"Expected '{expected}', got '{actual}'"

    elif match_type == "contains":
        passed = expected in actual
        message = f"Expected to contain '{expected}', got '{actual}'"

    elif match_type == "regex":
        passed = bool(re.search(expected, actual))
        message = f"Expected to match pattern '{expected}', got '{actual}'"

    elif match_type == "case_insensitive":
        passed = actual.lower() == expected.lower()
        message = f"Expected '{expected}' (case-insensitive), got '{actual}'"

    else:
        raise ValueError(f"Unknown match_type: {match_type}")

    return ValidationResult(
        validation_type="string",
        expected=expected,
        actual=actual,
        passed=passed,
        critical=critical,
        message=message if not passed else "OK"
    )
```

### 4. Collection Validation

```python
def validate_collection(
    actual: list,
    expected: list,
    match_type: str = "exact",  # exact | subset | superset | contains_all
    order_matters: bool = True,
    critical: bool = False
) -> ValidationResult:
    """Validate collection (list/set) assertion."""

    if match_type == "exact":
        if order_matters:
            passed = actual == expected
        else:
            passed = set(actual) == set(expected)
        message = f"Expected {expected}, got {actual}"

    elif match_type == "subset":
        passed = set(actual).issubset(set(expected))
        message = f"Expected subset of {expected}, got {actual}"

    elif match_type == "superset":
        passed = set(actual).issuperset(set(expected))
        message = f"Expected superset of {expected}, got {actual}"

    elif match_type == "contains_all":
        passed = all(item in actual for item in expected)
        message = f"Expected to contain all of {expected}, got {actual}"

    else:
        raise ValueError(f"Unknown match_type: {match_type}")

    return ValidationResult(
        validation_type="collection",
        expected=expected,
        actual=actual,
        passed=passed,
        critical=critical,
        message=message if not passed else "OK"
    )
```

### 5. State Comparison Validation

```python
def validate_state_change(
    pre_state: dict,
    post_state: dict,
    field_path: str,
    expected_change: str,  # increased | decreased | unchanged | changed
    min_change: Optional[float] = None,
    max_change: Optional[float] = None,
    critical: bool = False
) -> ValidationResult:
    """Validate state change between pre and post execution."""

    # Extract field values using dot notation
    pre_value = get_nested_value(pre_state, field_path)
    post_value = get_nested_value(post_state, field_path)

    if expected_change == "increased":
        passed = post_value > pre_value
        message = f"{field_path}: {pre_value} → {post_value} (expected increase)"

        if passed and min_change is not None:
            change = post_value - pre_value
            if change < min_change:
                passed = False
                message += f" but change {change} < min {min_change}"

    elif expected_change == "decreased":
        passed = post_value < pre_value
        message = f"{field_path}: {pre_value} → {post_value} (expected decrease)"

    elif expected_change == "unchanged":
        passed = post_value == pre_value
        message = f"{field_path}: {pre_value} → {post_value} (expected no change)"

    elif expected_change == "changed":
        passed = post_value != pre_value
        message = f"{field_path}: {pre_value} → {post_value} (expected change)"

    else:
        raise ValueError(f"Unknown expected_change: {expected_change}")

    return ValidationResult(
        validation_type="state_change",
        expected={"type": expected_change, "from": pre_value},
        actual={"type": "changed" if post_value != pre_value else "unchanged", "to": post_value},
        passed=passed,
        critical=critical,
        message=message
    )

def get_nested_value(data: dict, path: str):
    """Get nested dictionary value using dot notation."""
    keys = path.split('.')
    value = data
    for key in keys:
        value = value[key]
    return value
```

## Output Comparison Strategies

### Strict Comparison

```python
class StrictComparator:
    """Exact match required for all fields."""

    def compare(self, expected: dict, actual: dict) -> ComparisonResult:
        """Compare with strict equality."""

        mismatches = []

        for key in expected.keys():
            if key not in actual:
                mismatches.append(f"Missing key: {key}")
            elif expected[key] != actual[key]:
                mismatches.append(
                    f"{key}: expected {expected[key]}, got {actual[key]}"
                )

        # Check for unexpected keys
        for key in actual.keys():
            if key not in expected:
                mismatches.append(f"Unexpected key: {key}")

        return ComparisonResult(
            passed=len(mismatches) == 0,
            mismatches=mismatches
        )
```

### Lenient Comparison

```python
class LenientComparator:
    """Allow extra fields and minor differences."""

    def __init__(self, tolerance_config: dict):
        self.numeric_tolerance = tolerance_config.get("numeric_percentage", 0.05)
        self.timestamp_tolerance = tolerance_config.get("timestamp_seconds", 1)
        self.allow_extra_fields = tolerance_config.get("allow_extra_fields", True)

    def compare(self, expected: dict, actual: dict) -> ComparisonResult:
        """Compare with lenient rules."""

        mismatches = []

        for key, expected_value in expected.items():
            if key not in actual:
                mismatches.append(f"Missing key: {key}")
                continue

            actual_value = actual[key]

            # Numeric comparison with tolerance
            if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                tolerance = abs(expected_value * self.numeric_tolerance)
                if abs(expected_value - actual_value) > tolerance:
                    mismatches.append(
                        f"{key}: expected {expected_value} ± {tolerance}, got {actual_value}"
                    )

            # Timestamp comparison with tolerance
            elif isinstance(expected_value, datetime) and isinstance(actual_value, datetime):
                diff = abs((expected_value - actual_value).total_seconds())
                if diff > self.timestamp_tolerance:
                    mismatches.append(
                        f"{key}: timestamp diff {diff}s > tolerance {self.timestamp_tolerance}s"
                    )

            # Exact comparison for other types
            elif expected_value != actual_value:
                mismatches.append(
                    f"{key}: expected {expected_value}, got {actual_value}"
                )

        # Extra fields are allowed in lenient mode
        if not self.allow_extra_fields:
            for key in actual.keys():
                if key not in expected:
                    mismatches.append(f"Unexpected key: {key}")

        return ComparisonResult(
            passed=len(mismatches) == 0,
            mismatches=mismatches
        )
```

### Custom Comparison

```python
class CustomComparator:
    """User-defined comparison logic."""

    def __init__(self, comparison_func: callable):
        self.comparison_func = comparison_func

    def compare(self, expected: dict, actual: dict) -> ComparisonResult:
        """Run custom comparison function."""

        try:
            result = self.comparison_func(expected, actual)

            if isinstance(result, bool):
                return ComparisonResult(
                    passed=result,
                    mismatches=[] if result else ["Custom comparison failed"]
                )
            elif isinstance(result, ComparisonResult):
                return result
            else:
                raise ValueError("Custom function must return bool or ComparisonResult")

        except Exception as e:
            return ComparisonResult(
                passed=False,
                mismatches=[f"Custom comparison error: {str(e)}"]
            )
```

## Tolerance Thresholds

### Configuration

```yaml
validation:
  tolerances:
    # Numeric tolerances
    numeric_percentage: 0.05      # 5% tolerance for numeric values
    numeric_absolute: 2           # ±2 for integer counts

    # Temporal tolerances
    timestamp_seconds: 1          # 1 second for timestamps
    date_days: 0                  # Exact date match

    # Collection tolerances
    collection_size_percentage: 0.1  # 10% size difference allowed
    collection_order_matters: false

    # Field-specific tolerances
    field_overrides:
      execution_time_seconds:
        numeric_percentage: 0.20  # 20% tolerance for execution time
      assignments_modified:
        numeric_absolute: 3       # ±3 assignments OK
```

### Applying Tolerances

```python
class ToleranceValidator:
    """Apply tolerance rules to validation."""

    def __init__(self, tolerance_config: dict):
        self.config = tolerance_config

    def get_tolerance(self, field_name: str, value_type: type) -> dict:
        """Get tolerance for specific field."""

        # Check field-specific overrides
        if field_name in self.config.get("field_overrides", {}):
            return self.config["field_overrides"][field_name]

        # Use type-based defaults
        if value_type in (int, float):
            return {
                "percentage": self.config.get("numeric_percentage", 0),
                "absolute": self.config.get("numeric_absolute", 0)
            }
        elif value_type == datetime:
            return {
                "seconds": self.config.get("timestamp_seconds", 0)
            }
        else:
            return {}

    def validate_with_tolerance(
        self,
        field_name: str,
        expected: any,
        actual: any
    ) -> ValidationResult:
        """Validate field value with appropriate tolerance."""

        tolerance = self.get_tolerance(field_name, type(expected))

        if isinstance(expected, (int, float)):
            return validate_numeric(
                actual=actual,
                expected=expected,
                tolerance=tolerance.get("absolute", 0),
                critical=False
            )
        elif isinstance(expected, datetime):
            # Convert to numeric seconds and validate
            expected_ts = expected.timestamp()
            actual_ts = actual.timestamp()
            return validate_numeric(
                actual=actual_ts,
                expected=expected_ts,
                tolerance=tolerance.get("seconds", 0),
                critical=False
            )
        else:
            # Exact match for non-numeric types
            passed = actual == expected
            return ValidationResult(
                validation_type="exact",
                expected=expected,
                actual=actual,
                passed=passed,
                critical=False
            )
```

## Partial Match Handling

### Partial Match Rules

```yaml
validation:
  partial_match:
    # Allow extra items in collections
    allow_extra_assignments: true
    allow_extra_persons: false

    # Allow missing items
    allow_missing_assignments: false
    allow_missing_persons: false

    # Order sensitivity
    require_exact_order: false
    require_sorted_order: true  # Can be different order if sortable
```

### Implementation

```python
class PartialMatchValidator:
    """Handle partial match validation."""

    def __init__(self, partial_match_config: dict):
        self.config = partial_match_config

    def validate_collection_partial(
        self,
        field_name: str,
        expected: list,
        actual: list
    ) -> ValidationResult:
        """Validate collection with partial match rules."""

        messages = []

        # Check for missing items
        allow_missing = self.config.get(f"allow_missing_{field_name}", False)
        missing_items = set(expected) - set(actual)
        if missing_items and not allow_missing:
            messages.append(f"Missing items: {missing_items}")

        # Check for extra items
        allow_extra = self.config.get(f"allow_extra_{field_name}", False)
        extra_items = set(actual) - set(expected)
        if extra_items and not allow_extra:
            messages.append(f"Extra items: {extra_items}")

        # Check order
        if self.config.get("require_exact_order", False):
            if expected != actual:
                messages.append("Order mismatch (exact order required)")
        elif self.config.get("require_sorted_order", False):
            if sorted(expected) != sorted(actual):
                messages.append("Order mismatch (sorted order required)")

        passed = len(messages) == 0

        return ValidationResult(
            validation_type="partial_match",
            expected=expected,
            actual=actual,
            passed=passed,
            critical=False,
            message="; ".join(messages) if messages else "OK"
        )
```

## Failure Categorization

### Failure Types

```python
class FailureCategory(Enum):
    """Categories for validation failures."""

    CRITICAL = "critical"              # Must-pass assertion failed
    ASSERTION_FAILED = "assertion"     # Expected outcome not met
    STATE_INCONSISTENCY = "state"      # Final state invalid
    PERFORMANCE = "performance"        # Performance threshold exceeded
    TIMEOUT = "timeout"                # Operation timed out
    ERROR = "error"                    # Execution error occurred
```

### Categorize Failures

```python
def categorize_failure(validation_result: ValidationResult) -> FailureCategory:
    """Categorize validation failure."""

    if validation_result.critical:
        return FailureCategory.CRITICAL

    if validation_result.validation_type in ["boolean", "numeric", "string", "collection"]:
        return FailureCategory.ASSERTION_FAILED

    if validation_result.validation_type == "state_change":
        return FailureCategory.STATE_INCONSISTENCY

    if "execution_time" in str(validation_result.metadata):
        return FailureCategory.PERFORMANCE

    return FailureCategory.ASSERTION_FAILED
```

### Failure Report

```python
def generate_failure_report(validation_results: list[ValidationResult]) -> dict:
    """Generate categorized failure report."""

    failures_by_category = defaultdict(list)

    for result in validation_results:
        if not result.passed:
            category = categorize_failure(result)
            failures_by_category[category].append(result)

    # Generate report
    report = {
        "total_validations": len(validation_results),
        "passed": sum(1 for r in validation_results if r.passed),
        "failed": sum(1 for r in validation_results if not r.passed),
        "critical_failures": len(failures_by_category[FailureCategory.CRITICAL]),
        "failures_by_category": {
            category.value: [
                {
                    "validation_type": r.validation_type,
                    "expected": r.expected,
                    "actual": r.actual,
                    "message": r.message
                }
                for r in failures
            ]
            for category, failures in failures_by_category.items()
        }
    }

    return report
```

## Complete Validation Function

```python
from typing import Optional
from app.testing.validation_result import ValidationResult, ScenarioValidationResult

async def validate_scenario_complete(
    scenario: dict,
    execution_result: dict,
    pre_snapshot: dict,
    post_snapshot: dict,
    tolerance_config: Optional[dict] = None
) -> ScenarioValidationResult:
    """
    Complete scenario validation.

    Args:
        scenario: Scenario specification
        execution_result: Execution result from scenario run
        pre_snapshot: Pre-execution state snapshot
        post_snapshot: Post-execution state snapshot
        tolerance_config: Optional tolerance configuration

    Returns:
        ScenarioValidationResult with all validation details
    """

    expected = scenario["expected_outcome"]
    tolerance_config = tolerance_config or scenario.get("validation", {}).get("tolerances", {})

    # Initialize validators
    tolerance_validator = ToleranceValidator(tolerance_config)
    partial_match_validator = PartialMatchValidator(
        scenario.get("validation", {}).get("partial_match", {})
    )

    validation_results = {}

    # Validate assertions
    for assertion_name, assertion_spec in expected.get("assertions", {}).items():
        actual_value = get_nested_value(execution_result, assertion_name)

        if assertion_spec["type"] == "boolean":
            result = validate_boolean(
                actual=actual_value,
                expected=assertion_spec["expected"],
                critical=assertion_spec.get("critical", False)
            )

        elif assertion_spec["type"] == "numeric":
            result = validate_numeric(
                actual=actual_value,
                expected=assertion_spec.get("expected"),
                tolerance=assertion_spec.get("tolerance"),
                min_value=assertion_spec.get("min"),
                max_value=assertion_spec.get("max"),
                critical=assertion_spec.get("critical", False)
            )

        elif assertion_spec["type"] == "string":
            result = validate_string(
                actual=actual_value,
                expected=assertion_spec["expected"],
                match_type=assertion_spec.get("match_type", "exact"),
                critical=assertion_spec.get("critical", False)
            )

        elif assertion_spec["type"] == "collection":
            result = validate_collection(
                actual=actual_value,
                expected=assertion_spec["expected"],
                match_type=assertion_spec.get("match_type", "exact"),
                order_matters=assertion_spec.get("order_matters", True),
                critical=assertion_spec.get("critical", False)
            )

        validation_results[assertion_name] = result

    # Validate state changes
    for state_check in expected.get("state_comparison", []):
        result = validate_state_change(
            pre_state=pre_snapshot,
            post_state=post_snapshot,
            field_path=state_check["field"],
            expected_change=state_check.get("change_type", "changed"),
            min_change=state_check.get("min_change"),
            max_change=state_check.get("max_change"),
            critical=state_check.get("critical", False)
        )

        validation_results[f"state_change_{state_check['field']}"] = result

    # Run custom validators
    for custom_validator_spec in expected.get("custom_validations", []):
        validator_func = import_function(custom_validator_spec["function"])

        try:
            custom_result = await validator_func(
                scenario=scenario,
                execution_result=execution_result,
                pre_state=pre_snapshot,
                post_state=post_snapshot,
                **custom_validator_spec.get("parameters", {})
            )

            result = ValidationResult(
                validation_type="custom",
                expected=custom_validator_spec.get("expected_result"),
                actual=custom_result,
                passed=custom_result == custom_validator_spec.get("expected_result"),
                critical=custom_validator_spec.get("critical", False),
                message=f"Custom validator: {custom_validator_spec['name']}"
            )

        except Exception as e:
            result = ValidationResult(
                validation_type="custom",
                expected=custom_validator_spec.get("expected_result"),
                actual=None,
                passed=False,
                critical=custom_validator_spec.get("critical", False),
                message=f"Custom validator error: {str(e)}"
            )

        validation_results[custom_validator_spec["name"]] = result

    # Determine overall pass/fail
    all_passed = all(r.passed for r in validation_results.values())
    critical_failed = any(
        not r.passed and r.critical
        for r in validation_results.values()
    )

    # Generate failure report
    failure_report = generate_failure_report(list(validation_results.values()))

    # Build final result
    return ScenarioValidationResult(
        scenario_id=scenario["id"],
        passed=all_passed and not critical_failed,
        validations=validation_results,
        failure_report=failure_report,
        critical_failures=critical_failed
    )
```

## Usage Examples

### Validate Single Assertion

```python
# Validate boolean assertion
result = validate_boolean(
    actual=execution_result["coverage_maintained"],
    expected=True,
    critical=True
)

if not result.passed:
    print(f"Validation failed: {result.message}")
```

### Validate with Tolerance

```python
# Validate numeric with tolerance
result = validate_numeric(
    actual=execution_result["assignments_modified"],
    expected=5,
    tolerance=2,  # Accept 3-7
    critical=False
)
```

### Custom Validator

```python
# Define custom validator
async def validate_backup_chain(
    scenario,
    execution_result,
    pre_state,
    post_state,
    require_full_coverage=True
):
    """Validate backup chain is intact after N-1 failure."""

    # Check all assignments have backup coverage
    assignments = post_state["assignments"]
    uncovered = [a for a in assignments if not has_backup(a)]

    if require_full_coverage and uncovered:
        return False

    return True

# Use in scenario
result = await validate_backup_chain(
    scenario=scenario,
    execution_result=result,
    pre_state=pre_snapshot,
    post_state=post_snapshot,
    require_full_coverage=True
)
```

## References

- See `scenario-definition.md` for defining expected outcomes
- See `scenario-execution.md` for execution details
- See `Reference/success-criteria.md` for criteria definitions
- See `backend/app/testing/validators.py` for validator implementations
