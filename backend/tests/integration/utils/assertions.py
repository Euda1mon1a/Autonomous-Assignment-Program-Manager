"""
Custom assertions for integration tests.

Provides domain-specific assertion helpers.
"""

from datetime import date, datetime
from typing import Any, Optional


def assert_valid_uuid(value: Any) -> None:
    """Assert value is a valid UUID string."""
    from uuid import UUID

    try:
        UUID(str(value))
    except (ValueError, AttributeError):
        raise AssertionError(f"'{value}' is not a valid UUID")


def assert_valid_date(value: Any) -> None:
    """Assert value is a valid ISO date string."""
    try:
        if isinstance(value, str):
            datetime.fromisoformat(value.replace('Z', '+00:00'))
        elif isinstance(value, date):
            pass  # Already a date
        else:
            raise ValueError
    except ValueError:
        raise AssertionError(f"'{value}' is not a valid date")


def assert_assignment_valid(assignment: dict) -> None:
    """
    Assert assignment has required fields and valid data.

    Args:
        assignment: Assignment dictionary from API
    """
    required_fields = ["id", "block_id", "person_id", "rotation_template_id", "role"]

    for field in required_fields:
        assert field in assignment, f"Assignment missing required field: {field}"

    assert_valid_uuid(assignment["id"])
    assert_valid_uuid(assignment["block_id"])
    assert_valid_uuid(assignment["person_id"])
    assert_valid_uuid(assignment["rotation_template_id"])
    assert assignment["role"] in ["primary", "backup", "supervisor"]


def assert_person_valid(person: dict) -> None:
    """
    Assert person has required fields and valid data.

    Args:
        person: Person dictionary from API
    """
    required_fields = ["id", "name", "type", "email"]

    for field in required_fields:
        assert field in person, f"Person missing required field: {field}"

    assert_valid_uuid(person["id"])
    assert person["type"] in ["resident", "faculty", "clinical_staff"]
    assert "@" in person["email"], "Invalid email format"


def assert_block_valid(block: dict) -> None:
    """
    Assert block has required fields and valid data.

    Args:
        block: Block dictionary from API
    """
    required_fields = ["id", "date", "time_of_day", "block_number"]

    for field in required_fields:
        assert field in block, f"Block missing required field: {field}"

    assert_valid_uuid(block["id"])
    assert_valid_date(block["date"])
    assert block["time_of_day"] in ["AM", "PM"]
    assert isinstance(block["block_number"], int)
    assert block["block_number"] > 0


def assert_acgme_compliant(compliance_data: dict) -> None:
    """
    Assert ACGME compliance data indicates compliant status.

    Args:
        compliance_data: Compliance check result from API
    """
    if "compliant" in compliance_data:
        assert compliance_data["compliant"] is True, "ACGME compliance violation detected"

    if "violations" in compliance_data:
        assert (
            len(compliance_data["violations"]) == 0
        ), f"ACGME violations found: {compliance_data['violations']}"


def assert_no_conflicts(conflicts: list) -> None:
    """
    Assert no scheduling conflicts exist.

    Args:
        conflicts: List of conflicts from API
    """
    assert len(conflicts) == 0, f"Scheduling conflicts found: {conflicts}"


def assert_swap_status(swap: dict, expected_status: str) -> None:
    """
    Assert swap has expected status.

    Args:
        swap: Swap dictionary from API
        expected_status: Expected swap status
    """
    assert "status" in swap, "Swap missing status field"
    assert (
        swap["status"] == expected_status
    ), f"Expected swap status '{expected_status}', got '{swap['status']}'"


def assert_pagination_valid(response: dict, expected_items: Optional[int] = None) -> None:
    """
    Assert pagination response is valid.

    Args:
        response: Paginated response from API
        expected_items: Optional expected number of items
    """
    required_fields = ["items", "total", "page", "size"]

    for field in required_fields:
        assert field in response, f"Pagination response missing field: {field}"

    assert isinstance(response["items"], list)
    assert isinstance(response["total"], int)
    assert isinstance(response["page"], int)
    assert isinstance(response["size"], int)

    if expected_items is not None:
        assert (
            len(response["items"]) == expected_items
        ), f"Expected {expected_items} items, got {len(response['items'])}"


def assert_datetime_recent(dt_string: str, max_age_seconds: int = 60) -> None:
    """
    Assert datetime is recent (within max_age_seconds).

    Args:
        dt_string: ISO datetime string
        max_age_seconds: Maximum age in seconds
    """
    dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    now = datetime.now(dt.tzinfo)
    age = (now - dt).total_seconds()

    assert (
        age <= max_age_seconds
    ), f"Datetime is {age}s old, expected <= {max_age_seconds}s"
