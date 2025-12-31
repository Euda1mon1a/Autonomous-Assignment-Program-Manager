"""
Test scenarios for complex scheduling situations.

Provides pre-built scenarios for testing:
- ACGME compliance violations
- Coverage gaps and understaffing
- Swap conflicts
- Emergency situations
- Resilience framework stress tests

Usage:
    from tests.scenarios import ACGMEViolationScenarios

    # Create 80-hour violation scenario
    scenario = ACGMEViolationScenarios.create_80_hour_violation(db)

    # Validate that violation is detected
    validator = ACGMEValidator()
    violations = validator.validate_schedule(scenario["assignments"])
    assert len(violations) > 0
"""

from tests.scenarios.acgme_violation_scenarios import ACGMEViolationScenarios
from tests.scenarios.coverage_gap_scenarios import CoverageGapScenarios
from tests.scenarios.emergency_scenarios import EmergencyScenarios
from tests.scenarios.resilience_scenarios import ResilienceScenarios
from tests.scenarios.swap_conflict_scenarios import SwapConflictScenarios

__all__ = [
    "ACGMEViolationScenarios",
    "CoverageGapScenarios",
    "SwapConflictScenarios",
    "EmergencyScenarios",
    "ResilienceScenarios",
]
