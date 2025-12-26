***REMOVED*** Scenario Execution Workflow

End-to-end guide for running test scenarios with proper monitoring, timeout handling, and artifact capture.

***REMOVED******REMOVED*** Execution Pipeline

```
┌─────────────┐
│  Load       │
│  Scenario   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validate   │
│  Structure  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Setup      │
│  Environment│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Capture    │
│  Pre-State  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Execute    │
│  Operations │ ←─── Timeout Monitor
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Capture    │
│  Post-State │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validate   │
│  Results    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Cleanup    │
│  & Report   │
└─────────────┘
```

***REMOVED******REMOVED*** Phase 1: Scenario Loading

***REMOVED******REMOVED******REMOVED*** Load Scenario from File

```python
from app.testing.scenario_loader import ScenarioLoader

loader = ScenarioLoader()

***REMOVED*** Load single scenario
scenario = loader.load_scenario("backend/tests/scenarios/n1_failures/holiday_coverage.yaml")

***REMOVED*** Load scenario by ID
scenario = loader.load_scenario_by_id("n1-holiday-coverage-001")

***REMOVED*** Load scenario suite
scenarios = loader.load_scenario_suite("n1_failures")
```

***REMOVED******REMOVED******REMOVED*** Scenario Structure Validation

```python
from app.testing.scenario_validator import ScenarioStructureValidator

validator = ScenarioStructureValidator()

***REMOVED*** Validate scenario structure
validation_result = validator.validate_structure(scenario)

if not validation_result.valid:
    print(f"Scenario structure invalid:")
    for error in validation_result.errors:
        print(f"  - {error.field}: {error.message}")
    raise ValueError("Invalid scenario structure")
```

***REMOVED******REMOVED******REMOVED*** Parse and Resolve Variables

```python
from app.testing.scenario_parser import ScenarioParser

parser = ScenarioParser()

***REMOVED*** Resolve variables in scenario
resolved_scenario = parser.resolve_variables(scenario)

***REMOVED*** Example:
***REMOVED*** Original: person_id: "${unavailable_person}"
***REMOVED*** Resolved: person_id: "resident-1"
```

***REMOVED******REMOVED*** Phase 2: Environment Setup

***REMOVED******REMOVED******REMOVED*** Database Preparation

```python
from app.testing.scenario_setup import ScenarioSetup

setup = ScenarioSetup()

async def prepare_database(scenario):
    """Prepare database for scenario execution."""

    ***REMOVED*** Clean database if required
    if scenario.setup.database.clean_state:
        await setup.clean_database()

    ***REMOVED*** Load fixtures
    for fixture_path in scenario.setup.database.load_fixtures:
        await setup.load_fixture(fixture_path)

    ***REMOVED*** Create persons
    for person_data in scenario.setup.persons:
        await setup.create_person(person_data)

    ***REMOVED*** Create rotations
    for rotation_data in scenario.setup.rotations:
        await setup.create_rotation(rotation_data)

    ***REMOVED*** Create initial assignments
    for assignment_data in scenario.setup.assignments:
        await setup.create_assignment(assignment_data)

    ***REMOVED*** Configure constraints
    await setup.configure_constraints(scenario.setup.constraints)
```

***REMOVED******REMOVED******REMOVED*** Precondition Verification

```python
async def verify_preconditions(scenario):
    """Verify all preconditions before execution."""

    precondition_checker = PreconditionChecker()

    for precondition in scenario.setup.preconditions:
        result = await precondition_checker.check(
            check_name=precondition.check,
            expected=precondition.expected
        )

        if not result.passed:
            raise PreconditionFailedError(
                f"Precondition failed: {precondition.check}\n"
                f"Expected: {precondition.expected}\n"
                f"Actual: {result.actual}"
            )
```

***REMOVED******REMOVED******REMOVED*** Backup Creation (for destructive operations)

```python
async def create_backup_if_required(scenario):
    """Create database backup for destructive scenarios."""

    if scenario.require_backup:
        from app.testing.backup_manager import BackupManager

        backup_mgr = BackupManager()

        backup_id = await backup_mgr.create_backup(
            scenario_id=scenario.id,
            description=f"Pre-execution backup for {scenario.name}"
        )

        return backup_id
    return None
```

***REMOVED******REMOVED*** Phase 3: Pre-Execution State Capture

***REMOVED******REMOVED******REMOVED*** Snapshot Creation

```python
from app.testing.state_capture import StateCaptureManager

async def capture_pre_state(scenario):
    """Capture system state before execution."""

    state_mgr = StateCaptureManager()

    snapshot = await state_mgr.create_snapshot(
        scenario_id=scenario.id,
        snapshot_type="pre_execution",
        capture_config=scenario.artifacts.capture
    )

    ***REMOVED*** Captures:
    ***REMOVED*** - All database tables relevant to scenario
    ***REMOVED*** - Current ACGME compliance status
    ***REMOVED*** - Coverage statistics
    ***REMOVED*** - Utilization metrics

    return snapshot
```

***REMOVED******REMOVED******REMOVED*** Snapshot Contents

```json
{
  "snapshot_id": "snap_001_pre",
  "scenario_id": "n1-holiday-coverage-001",
  "timestamp": "2024-12-26T10:30:00Z",
  "database_state": {
    "persons": [
      {"id": "resident-1", "status": "active", "weekly_hours": 48},
      {"id": "resident-2", "status": "active", "weekly_hours": 52}
    ],
    "assignments": [
      {"id": "assign-1", "person_id": "resident-1", "date": "2024-12-25", "hours": 12}
    ]
  },
  "compliance_status": {
    "overall": "compliant",
    "violations": [],
    "warnings": []
  },
  "coverage_stats": {
    "total_blocks": 730,
    "covered_blocks": 725,
    "coverage_percentage": 99.3
  }
}
```

***REMOVED******REMOVED*** Phase 4: Operation Execution

***REMOVED******REMOVED******REMOVED*** Execute with Timeout Protection

```python
import asyncio
from app.testing.scenario_executor import ScenarioExecutor

async def execute_scenario_with_timeout(scenario):
    """Execute scenario with timeout protection."""

    executor = ScenarioExecutor()
    timeout = scenario.timeout_seconds or 300  ***REMOVED*** Default 5 min

    try:
        ***REMOVED*** Execute with timeout
        result = await asyncio.wait_for(
            executor.execute_operations(scenario),
            timeout=timeout
        )
        return result

    except asyncio.TimeoutError:
        ***REMOVED*** Timeout exceeded
        return ScenarioResult(
            scenario_id=scenario.id,
            status="timeout",
            error=f"Scenario execution exceeded {timeout}s timeout",
            execution_time=timeout
        )

    except Exception as e:
        ***REMOVED*** Execution error
        return ScenarioResult(
            scenario_id=scenario.id,
            status="error",
            error=str(e),
            traceback=traceback.format_exc()
        )
```

***REMOVED******REMOVED******REMOVED*** Single Operation Execution

```python
async def execute_single_operation(operation, parameters):
    """Execute a single operation from scenario."""

    operation_registry = {
        "mark_unavailable": mark_person_unavailable,
        "request_swap": request_schedule_swap,
        "execute_swap": execute_schedule_swap,
        "run_contingency_analysis": run_n1_contingency,
        "activate_backup_assignments": activate_backup_coverage,
        "validate_acgme": validate_acgme_compliance,
        "generate_schedule": generate_schedule_period,
    }

    if operation not in operation_registry:
        raise ValueError(f"Unknown operation: {operation}")

    operation_func = operation_registry[operation]
    result = await operation_func(**parameters)

    return result
```

***REMOVED******REMOVED******REMOVED*** Sequential Operations

```python
async def execute_sequential_operations(operations):
    """Execute operations in sequence."""

    results = []

    for op in sorted(operations, key=lambda x: x.step):
        print(f"Executing step {op.step}: {op.operation}")

        result = await execute_single_operation(
            operation=op.operation,
            parameters=op.parameters
        )

        results.append({
            "step": op.step,
            "operation": op.operation,
            "result": result,
            "timestamp": datetime.utcnow()
        })

        ***REMOVED*** Stop on critical failure
        if not result.success and op.critical:
            break

    return results
```

***REMOVED******REMOVED******REMOVED*** Concurrent Operations

```python
async def execute_concurrent_operations(operations):
    """Execute operations concurrently (for race condition testing)."""

    tasks = [
        execute_single_operation(
            operation=op.operation,
            parameters=op.parameters
        )
        for op in operations
    ]

    ***REMOVED*** Execute all concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results
```

***REMOVED******REMOVED******REMOVED*** Progress Monitoring

```python
from app.testing.progress_monitor import ProgressMonitor

async def execute_with_progress_monitoring(scenario):
    """Execute scenario with progress monitoring."""

    monitor = ProgressMonitor()

    ***REMOVED*** Start monitoring
    monitor.start(
        scenario_id=scenario.id,
        total_operations=len(scenario.test_case.operations)
    )

    try:
        for i, operation in enumerate(scenario.test_case.operations):
            ***REMOVED*** Update progress
            monitor.update(
                current_operation=i + 1,
                operation_name=operation.operation,
                status="running"
            )

            ***REMOVED*** Execute operation
            result = await execute_single_operation(
                operation.operation,
                operation.parameters
            )

            ***REMOVED*** Mark complete
            monitor.mark_complete(i + 1, result.success)

    finally:
        monitor.finish()
```

***REMOVED******REMOVED*** Phase 5: Post-Execution State Capture

***REMOVED******REMOVED******REMOVED*** Capture Final State

```python
async def capture_post_state(scenario):
    """Capture system state after execution."""

    state_mgr = StateCaptureManager()

    snapshot = await state_mgr.create_snapshot(
        scenario_id=scenario.id,
        snapshot_type="post_execution",
        capture_config=scenario.artifacts.capture
    )

    return snapshot
```

***REMOVED******REMOVED******REMOVED*** Execution Log Capture

```python
from app.testing.log_capture import LogCaptureManager

async def capture_execution_logs(scenario):
    """Capture all logs generated during scenario execution."""

    log_mgr = LogCaptureManager()

    logs = await log_mgr.get_scenario_logs(
        scenario_id=scenario.id,
        include_sql_queries=True,
        include_debug_logs=True
    )

    await log_mgr.save_logs(
        scenario_id=scenario.id,
        logs=logs,
        format="json"
    )

    return logs
```

***REMOVED******REMOVED******REMOVED*** Performance Metrics Capture

```python
from app.testing.metrics_collector import MetricsCollector

async def capture_performance_metrics(scenario):
    """Capture performance metrics during execution."""

    collector = MetricsCollector()

    metrics = {
        "execution_time_seconds": collector.get_total_time(),
        "database_queries": {
            "total": collector.get_query_count(),
            "select": collector.get_query_count("SELECT"),
            "insert": collector.get_query_count("INSERT"),
            "update": collector.get_query_count("UPDATE"),
            "delete": collector.get_query_count("DELETE"),
        },
        "memory_usage_mb": collector.get_peak_memory_mb(),
        "operation_times": collector.get_operation_times(),
    }

    return metrics
```

***REMOVED******REMOVED*** Phase 6: Result Validation

***REMOVED******REMOVED******REMOVED*** Validate Against Expected Outcomes

```python
from app.testing.result_validator import ResultValidator

async def validate_scenario_results(scenario, execution_result, post_snapshot):
    """Validate execution results against expected outcomes."""

    validator = ResultValidator()

    validation_result = await validator.validate(
        scenario=scenario,
        execution_result=execution_result,
        post_state=post_snapshot,
        expected=scenario.expected_outcome
    )

    return validation_result
```

See `scenario-validation.md` for detailed validation process.

***REMOVED******REMOVED*** Phase 7: Cleanup

***REMOVED******REMOVED******REMOVED*** Rollback on Failure

```python
async def cleanup_after_scenario(scenario, execution_result, backup_id=None):
    """Cleanup after scenario execution."""

    ***REMOVED*** Rollback if scenario failed and rollback enabled
    if not execution_result.success and scenario.rollback_on_failure:
        if backup_id:
            await restore_from_backup(backup_id)
        else:
            ***REMOVED*** Manual rollback
            await rollback_database_changes(scenario.id)

    ***REMOVED*** Clean up temporary data
    await cleanup_temporary_data(scenario.id)

    ***REMOVED*** Delete backup if scenario passed
    if execution_result.success and backup_id:
        await delete_backup(backup_id)
```

***REMOVED******REMOVED******REMOVED*** Artifact Retention

```python
async def manage_artifacts(scenario, execution_result):
    """Manage artifact retention based on scenario config."""

    artifact_mgr = ArtifactManager()

    ***REMOVED*** Determine retention period
    retention_days = scenario.artifacts.retention_days

    ***REMOVED*** Always keep artifacts for failed scenarios
    if not execution_result.success:
        retention_days = max(retention_days, 90)

    ***REMOVED*** Set expiration
    await artifact_mgr.set_expiration(
        scenario_id=scenario.id,
        retention_days=retention_days
    )

    ***REMOVED*** Export artifacts in requested formats
    for export_format in scenario.artifacts.export_formats:
        await artifact_mgr.export(
            scenario_id=scenario.id,
            format=export_format
        )
```

***REMOVED******REMOVED*** Complete Execution Function

```python
from typing import Optional
from app.testing.scenario_result import ScenarioResult

async def run_scenario_full(
    scenario_id: str,
    timeout: Optional[int] = None
) -> ScenarioResult:
    """
    Complete scenario execution pipeline.

    Args:
        scenario_id: ID of scenario to run
        timeout: Optional timeout override in seconds

    Returns:
        ScenarioResult with full execution details
    """

    ***REMOVED*** Load scenario
    scenario = loader.load_scenario_by_id(scenario_id)

    ***REMOVED*** Override timeout if provided
    if timeout:
        scenario.timeout_seconds = timeout

    ***REMOVED*** Validate structure
    validator.validate_structure(scenario)

    ***REMOVED*** Resolve variables
    scenario = parser.resolve_variables(scenario)

    backup_id = None
    pre_snapshot = None
    post_snapshot = None

    try:
        ***REMOVED*** Setup environment
        await prepare_database(scenario)
        await verify_preconditions(scenario)

        ***REMOVED*** Create backup if needed
        backup_id = await create_backup_if_required(scenario)

        ***REMOVED*** Capture pre-state
        pre_snapshot = await capture_pre_state(scenario)

        ***REMOVED*** Execute scenario
        start_time = time.time()
        execution_result = await execute_scenario_with_timeout(scenario)
        execution_time = time.time() - start_time

        ***REMOVED*** Capture post-state
        post_snapshot = await capture_post_state(scenario)

        ***REMOVED*** Capture logs and metrics
        logs = await capture_execution_logs(scenario)
        metrics = await capture_performance_metrics(scenario)

        ***REMOVED*** Validate results
        validation_result = await validate_scenario_results(
            scenario,
            execution_result,
            post_snapshot
        )

        ***REMOVED*** Build final result
        final_result = ScenarioResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            status="passed" if validation_result.passed else "failed",
            success=validation_result.passed,
            execution_time_seconds=execution_time,
            validations=validation_result.validations,
            metrics=metrics,
            artifacts={
                "pre_snapshot": pre_snapshot.id,
                "post_snapshot": post_snapshot.id,
                "logs": logs.id
            },
            errors=validation_result.errors if not validation_result.passed else []
        )

        return final_result

    except Exception as e:
        ***REMOVED*** Handle execution failure
        return ScenarioResult(
            scenario_id=scenario.id,
            status="error",
            success=False,
            error=str(e),
            traceback=traceback.format_exc()
        )

    finally:
        ***REMOVED*** Cleanup
        await cleanup_after_scenario(scenario, execution_result, backup_id)
        await manage_artifacts(scenario, execution_result)
```

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Run Single Scenario

```python
***REMOVED*** Run by ID
result = await run_scenario_full("n1-holiday-coverage-001")

print(f"Status: {result.status}")
print(f"Execution Time: {result.execution_time_seconds}s")
print(f"Validations Passed: {sum(1 for v in result.validations.values() if v.passed)}/{len(result.validations)}")

if not result.success:
    print("Errors:")
    for error in result.errors:
        print(f"  - {error}")
```

***REMOVED******REMOVED******REMOVED*** Run Scenario Suite

```python
async def run_scenario_suite(suite_name: str):
    """Run all scenarios in a suite."""

    scenarios = loader.load_scenario_suite(suite_name)
    results = []

    for scenario in scenarios:
        print(f"\nRunning {scenario.name}...")
        result = await run_scenario_full(scenario.id)
        results.append(result)

        ***REMOVED*** Print summary
        status_icon = "✅" if result.success else "❌"
        print(f"{status_icon} {scenario.name}: {result.status}")

    ***REMOVED*** Overall summary
    passed = sum(1 for r in results if r.success)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"Suite Results: {passed}/{total} passed ({passed/total*100:.1f}%)")

    return results
```

***REMOVED******REMOVED******REMOVED*** Run with Custom Timeout

```python
***REMOVED*** Run with 10-minute timeout (for slow operations)
result = await run_scenario_full(
    "schedule-generation-full-year-001",
    timeout=600
)
```

***REMOVED******REMOVED******REMOVED*** Parallel Execution

```python
async def run_scenarios_parallel(scenario_ids: list[str]):
    """Run multiple scenarios in parallel."""

    tasks = [
        run_scenario_full(scenario_id)
        for scenario_id in scenario_ids
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results
```

***REMOVED******REMOVED*** Pytest Integration

***REMOVED******REMOVED******REMOVED*** Scenario as Pytest Test

```python
***REMOVED*** backend/tests/scenarios/test_n1_scenarios.py

import pytest
from app.testing.scenario_executor import run_scenario_full

@pytest.mark.scenario
@pytest.mark.asyncio
async def test_n1_holiday_coverage_001():
    """N-1 failure during holiday coverage."""
    result = await run_scenario_full("n1-holiday-coverage-001")
    assert result.success, f"Scenario failed: {result.errors}"

@pytest.mark.scenario
@pytest.mark.asyncio
async def test_n1_multi_absence_002():
    """N-1 failure with multiple simultaneous absences."""
    result = await run_scenario_full("n1-multi-absence-002")
    assert result.success, f"Scenario failed: {result.errors}"
```

***REMOVED******REMOVED******REMOVED*** Parametrized Scenario Tests

```python
@pytest.mark.scenario
@pytest.mark.parametrize("scenario_id", [
    "n1-holiday-coverage-001",
    "n1-multi-absence-002",
    "n1-cascade-failure-003",
    "n1-backup-chain-004",
])
@pytest.mark.asyncio
async def test_n1_scenarios(scenario_id):
    """Parametrized test for all N-1 scenarios."""
    result = await run_scenario_full(scenario_id)
    assert result.success, f"Scenario {scenario_id} failed: {result.errors}"
```

***REMOVED******REMOVED*** Monitoring and Debugging

***REMOVED******REMOVED******REMOVED*** Real-Time Progress

```python
***REMOVED*** Monitor execution in real-time
async def run_with_live_monitoring(scenario_id):
    monitor = ProgressMonitor()

    async def progress_callback(step, total, operation):
        print(f"[{step}/{total}] {operation}")

    monitor.on_progress = progress_callback

    result = await run_scenario_full(scenario_id)
    return result
```

***REMOVED******REMOVED******REMOVED*** Verbose Execution

```python
***REMOVED*** Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

result = await run_scenario_full("n1-holiday-coverage-001")
```

***REMOVED******REMOVED******REMOVED*** Debug Mode

```python
***REMOVED*** Run in debug mode (keeps artifacts, no cleanup)
scenario = loader.load_scenario_by_id("n1-holiday-coverage-001")
scenario.debug_mode = True
scenario.rollback_on_failure = False

result = await run_scenario_full(scenario.id)
```

***REMOVED******REMOVED*** Error Handling

***REMOVED******REMOVED******REMOVED*** Common Errors

```python
try:
    result = await run_scenario_full(scenario_id)

except ScenarioNotFoundError as e:
    print(f"Scenario {scenario_id} not found")

except PreconditionFailedError as e:
    print(f"Precondition failed: {e}")

except TimeoutError as e:
    print(f"Scenario timed out: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")
    traceback.print_exc()
```

***REMOVED******REMOVED******REMOVED*** Retry Logic

```python
async def run_scenario_with_retry(scenario_id, max_retries=3):
    """Run scenario with retry on transient failures."""

    for attempt in range(max_retries):
        try:
            result = await run_scenario_full(scenario_id)

            ***REMOVED*** Retry on timeout or transient errors
            if result.status == "timeout":
                print(f"Attempt {attempt + 1} timed out, retrying...")
                continue

            return result

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(2 ** attempt)  ***REMOVED*** Exponential backoff
            else:
                raise

    return result
```

***REMOVED******REMOVED*** Performance Optimization

***REMOVED******REMOVED******REMOVED*** Query Optimization

```python
***REMOVED*** Enable query caching for read-heavy scenarios
from app.testing.query_optimizer import enable_query_cache

async def run_with_query_cache(scenario_id):
    with enable_query_cache():
        result = await run_scenario_full(scenario_id)
    return result
```

***REMOVED******REMOVED******REMOVED*** Batch Operations

```python
***REMOVED*** Batch database operations for performance
scenario.setup.database.batch_operations = True
scenario.setup.database.batch_size = 100

result = await run_scenario_full(scenario.id)
```

***REMOVED******REMOVED*** References

- See `scenario-definition.md` for scenario spec format
- See `scenario-validation.md` for validation details
- See `Reference/scenario-library.md` for pre-built scenarios
- See `backend/app/testing/` for implementation details
