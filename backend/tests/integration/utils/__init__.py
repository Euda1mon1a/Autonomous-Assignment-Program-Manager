"""Integration test utilities package."""

from .api_client import TestAPIClient
from .assertions import (
    assert_acgme_compliant,
    assert_assignment_valid,
    assert_block_valid,
    assert_datetime_recent,
    assert_no_conflicts,
    assert_pagination_valid,
    assert_person_valid,
    assert_swap_status,
    assert_valid_date,
    assert_valid_uuid,
)
from .cleanup_helpers import (
    TestDataCleanup,
    cleanup_absences,
    cleanup_all_test_data,
    cleanup_assignments,
    cleanup_blocks,
    cleanup_people,
    cleanup_rotation_templates,
    cleanup_users,
)
from .setup_helpers import (
    create_academic_year_blocks,
    create_test_faculty,
    create_test_residents,
    create_test_rotation_templates,
    create_test_schedule,
    setup_minimal_schedule_scenario,
)

__all__ = [
    # API Client
    "TestAPIClient",
    # Assertions
    "assert_valid_uuid",
    "assert_valid_date",
    "assert_assignment_valid",
    "assert_person_valid",
    "assert_block_valid",
    "assert_acgme_compliant",
    "assert_no_conflicts",
    "assert_swap_status",
    "assert_pagination_valid",
    "assert_datetime_recent",
    # Setup Helpers
    "create_test_schedule",
    "create_test_residents",
    "create_test_faculty",
    "create_test_rotation_templates",
    "create_academic_year_blocks",
    "setup_minimal_schedule_scenario",
    # Cleanup Helpers
    "cleanup_assignments",
    "cleanup_blocks",
    "cleanup_people",
    "cleanup_rotation_templates",
    "cleanup_absences",
    "cleanup_users",
    "cleanup_all_test_data",
    "TestDataCleanup",
]
