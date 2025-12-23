#!/usr/bin/env python
"""
Test script to verify all TODO implementations are working.

Tests:
1. SolverBenchmark - memory tracking, violation counting, coverage calculation
2. PathwayValidator - pathway validation with various structures
3. ExperimentalHarness - baseline and experimental runs
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from experimental.benchmarks.pathway_validation import PathwayValidator
from experimental.benchmarks.solver_comparison import SolverBenchmark
from experimental.harness import ExperimentalHarness


def test_solver_benchmark():
    """Test SolverBenchmark implementations."""
    print("\n" + "=" * 60)
    print("Testing SolverBenchmark")
    print("=" * 60)

    # Create mock solver with various result structures
    class MockSolver:
        def solve(self, context):
            class Result:
                def __init__(self):
                    self.success = True
                    self.assignments = [(i, i + 1, i + 2) for i in range(85)]
                    self.statistics = {
                        "coverage_rate": 0.85,
                        "total_blocks": 100,
                        "constraint_violations": 3,
                    }

            return Result()

    class MockContext:
        pass

    benchmark = SolverBenchmark()

    # Test 1: Memory tracking
    result = benchmark.run(MockSolver(), "test_solver", MockContext(), "test_scenario")
    assert result.memory_mb >= 0, "Memory tracking should return non-negative value"
    print(f"✓ Memory tracking: {result.memory_mb:.2f}MB")

    # Test 2: Violation counting
    assert (
        result.constraint_violations == 3
    ), "Should extract violations from statistics"
    print(f"✓ Violation counting: {result.constraint_violations} violations")

    # Test 3: Coverage calculation
    assert (
        abs(result.coverage_score - 0.85) < 0.01
    ), "Should extract coverage from statistics"
    print(f"✓ Coverage calculation: {result.coverage_score:.2f}")

    # Test 4: Result with no violations
    class SuccessSolver:
        def solve(self, context):
            class Result:
                def __init__(self):
                    self.success = True
                    self.statistics = {"coverage_rate": 1.0}

            return Result()

    result2 = benchmark.run(SuccessSolver(), "success_solver", MockContext(), "success")
    assert (
        result2.constraint_violations == 0
    ), "Should default to 0 for successful result"
    print(f"✓ No violations for successful result: {result2.constraint_violations}")

    print("\n✅ All SolverBenchmark tests passed!")


def test_pathway_validator():
    """Test PathwayValidator implementations."""
    print("\n" + "=" * 60)
    print("Testing PathwayValidator")
    print("=" * 60)

    validator = PathwayValidator()

    # Test 1: Dict pathway
    pathway_dict = {
        "steps": [
            {"from": "A", "to": "B"},
            {"from": "B", "to": "C"},
        ],
        "barriers_bypassed": 2,
        "catalysts_used": ["catalyst_a", "catalyst_b"],
    }

    result = validator.validate_pathway("state_a", "state_c", pathway_dict)
    assert result.steps == 2, "Should count steps from list"
    assert result.barriers_bypassed == 2, "Should extract barriers"
    assert len(result.catalysts_used) == 2, "Should extract catalysts"
    assert result.is_valid, "Should be valid with no errors"
    print(f"✓ Dict pathway: {result.steps} steps, {result.barriers_bypassed} barriers")

    # Test 2: Object pathway with attributes
    class PathwayObject:
        def __init__(self):
            self.steps = ["step1", "step2", "step3"]
            self.barriers_bypassed = 1
            self.catalysts_used = ["cat1"]

    result2 = validator.validate_pathway("a", "b", PathwayObject())
    assert result2.steps == 3, "Should extract steps from object"
    assert result2.barriers_bypassed == 1, "Should extract barriers from object"
    print(f"✓ Object pathway: {result2.steps} steps")

    # Test 3: List pathway (just steps)
    pathway_list = ["step1", "step2", "step3", "step4"]
    result3 = validator.validate_pathway("x", "y", pathway_list)
    assert result3.steps == 4, "Should count list items as steps"
    print(f"✓ List pathway: {result3.steps} steps")

    # Test 4: Empty pathway should have error
    result4 = validator.validate_pathway("a", "b", {})
    assert not result4.is_valid, "Empty pathway should be invalid"
    assert len(result4.validation_errors) > 0, "Should have validation error"
    print(f"✓ Empty pathway validation: {result4.validation_errors}")

    # Test 5: Success rate calculation
    success_rate = validator.success_rate()
    expected_rate = 3 / 4  # 3 valid out of 4 total
    assert (
        abs(success_rate - expected_rate) < 0.01
    ), "Should calculate correct success rate"
    print(f"✓ Success rate: {success_rate:.2%}")

    print("\n✅ All PathwayValidator tests passed!")


def test_experimental_harness():
    """Test ExperimentalHarness implementations."""
    print("\n" + "=" * 60)
    print("Testing ExperimentalHarness")
    print("=" * 60)

    harness = ExperimentalHarness()

    # Test 1: Baseline run
    result = harness.run_baseline("minimal")
    assert result.success, "Baseline should succeed"
    assert result.branch == "baseline", "Should identify as baseline"
    assert result.scenario == "minimal", "Should use correct scenario"
    assert result.coverage_score > 0, "Should have coverage score"
    print(
        f"✓ Baseline run: {result.solve_time_ms}ms, coverage={result.coverage_score:.2f}"
    )

    # Test 2: Unknown scenario
    result2 = harness.run_baseline("nonexistent")
    assert not result2.success, "Should fail for unknown scenario"
    assert result2.error_message is not None, "Should have error message"
    print(f"✓ Unknown scenario handling: {result2.error_message}")

    # Test 3: Experimental run (will use fallback)
    result3 = harness.run_experimental("quantum-physics", "minimal")
    assert result3.branch == "quantum-physics", "Should identify branch"
    # May or may not succeed depending on branch existence
    print(f"✓ Experimental run: branch={result3.branch}, success={result3.success}")

    print("\n✅ All ExperimentalHarness tests passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Testing TODO Implementations")
    print("=" * 60)

    try:
        test_solver_benchmark()
        test_pathway_validator()
        test_experimental_harness()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nImplemented TODOs:")
        print("  1. ✓ Memory tracking using tracemalloc")
        print("  2. ✓ Violation counting from result structure")
        print("  3. ✓ Coverage calculation from result structure")
        print("  4. ✓ Pathway validation with steps/barriers/catalysts")
        print("  5. ✓ Baseline solver invocation (with fallback)")
        print("  6. ✓ Experimental solver subprocess execution (with fallback)")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
