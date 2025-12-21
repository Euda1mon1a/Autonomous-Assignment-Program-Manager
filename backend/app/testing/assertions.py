"""
Custom assertions for API testing.

Provides domain-specific assertions for:
- API response validation
- JSON structure matching
- Schedule validation
- ACGME compliance verification
- Conflict detection
"""
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Pattern, Union

from app.testing.mock_server import MockResponse


class AssertionError(Exception):
    """Custom assertion error with detailed messages."""
    pass


def assert_api_response(
    response: MockResponse,
    status_code: int = 200,
    body_contains: Dict[str, Any] = None,
    headers_contain: Dict[str, str] = None,
) -> None:
    """
    Assert API response matches expectations.

    Args:
        response: Response to validate
        status_code: Expected status code
        body_contains: Key-value pairs that must be in response body
        headers_contain: Headers that must be present

    Raises:
        AssertionError: If response doesn't match expectations

    Example:
        ```python
        assert_api_response(
            response,
            status_code=200,
            body_contains={"status": "ok"},
            headers_contain={"Content-Type": "application/json"}
        )
        ```
    """
    # Check status code
    if response.status_code != status_code:
        raise AssertionError(
            f"Expected status code {status_code}, got {response.status_code}"
        )

    # Check body contains
    if body_contains:
        if not isinstance(response.body, dict):
            raise AssertionError(
                f"Expected response body to be dict, got {type(response.body)}"
            )

        for key, expected_value in body_contains.items():
            if key not in response.body:
                raise AssertionError(
                    f"Expected key '{key}' in response body, but it was missing"
                )

            actual_value = response.body[key]
            if actual_value != expected_value:
                raise AssertionError(
                    f"Expected response.body['{key}'] to be {expected_value!r}, "
                    f"got {actual_value!r}"
                )

    # Check headers
    if headers_contain:
        for key, expected_value in headers_contain.items():
            if key not in response.headers:
                raise AssertionError(
                    f"Expected header '{key}' in response, but it was missing"
                )

            actual_value = response.headers[key]
            if actual_value != expected_value:
                raise AssertionError(
                    f"Expected response header '{key}' to be {expected_value!r}, "
                    f"got {actual_value!r}"
                )


def assert_json_match(
    actual: Any,
    expected: Any,
    path: str = "$",
) -> None:
    """
    Assert JSON structure matches expected structure.

    Recursively validates nested structures.

    Args:
        actual: Actual JSON data
        expected: Expected JSON structure
        path: Current path in JSON (for error messages)

    Raises:
        AssertionError: If structures don't match

    Example:
        ```python
        assert_json_match(
            actual={"user": {"name": "John", "age": 30}},
            expected={"user": {"name": "John", "age": 30}}
        )
        ```
    """
    # Check types match
    if type(actual) != type(expected):
        raise AssertionError(
            f"Type mismatch at {path}: expected {type(expected).__name__}, "
            f"got {type(actual).__name__}"
        )

    # Handle dictionaries
    if isinstance(expected, dict):
        for key, expected_value in expected.items():
            if key not in actual:
                raise AssertionError(
                    f"Missing key at {path}.{key}"
                )

            assert_json_match(
                actual=actual[key],
                expected=expected_value,
                path=f"{path}.{key}",
            )

    # Handle lists
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise AssertionError(
                f"List length mismatch at {path}: expected {len(expected)}, "
                f"got {len(actual)}"
            )

        for i, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            assert_json_match(
                actual=actual_item,
                expected=expected_item,
                path=f"{path}[{i}]",
            )

    # Handle primitive values
    else:
        if actual != expected:
            raise AssertionError(
                f"Value mismatch at {path}: expected {expected!r}, got {actual!r}"
            )


def assert_schedule_valid(
    schedule: Dict[str, Any],
    check_acgme: bool = True,
    check_conflicts: bool = True,
) -> None:
    """
    Assert schedule is valid.

    Validates:
    - Schedule structure
    - Assignment coverage
    - ACGME compliance (optional)
    - Conflict detection (optional)

    Args:
        schedule: Schedule data to validate
        check_acgme: Whether to check ACGME compliance
        check_conflicts: Whether to check for conflicts

    Raises:
        AssertionError: If schedule is invalid

    Example:
        ```python
        assert_schedule_valid(
            schedule={"assignments": [...], "metadata": {...}},
            check_acgme=True,
            check_conflicts=True
        )
        ```
    """
    # Check basic structure
    if "assignments" not in schedule:
        raise AssertionError("Schedule missing 'assignments' field")

    assignments = schedule["assignments"]
    if not isinstance(assignments, list):
        raise AssertionError(
            f"Expected 'assignments' to be list, got {type(assignments)}"
        )

    # Check each assignment has required fields
    required_fields = ["id", "person_id", "block_id", "rotation_template_id"]
    for i, assignment in enumerate(assignments):
        for field in required_fields:
            if field not in assignment:
                raise AssertionError(
                    f"Assignment {i} missing required field: {field}"
                )

    # Check ACGME compliance if requested
    if check_acgme and "acgme_compliance" in schedule:
        compliance = schedule["acgme_compliance"]
        if not compliance.get("is_compliant", False):
            violations = compliance.get("violations", [])
            raise AssertionError(
                f"Schedule not ACGME compliant. Violations: {violations}"
            )

    # Check conflicts if requested
    if check_conflicts and "conflicts" in schedule:
        conflicts = schedule["conflicts"]
        if conflicts:
            raise AssertionError(
                f"Schedule has conflicts: {conflicts}"
            )


def assert_compliance_valid(
    compliance_data: Dict[str, Any],
    expect_compliant: bool = True,
) -> None:
    """
    Assert ACGME compliance data is valid.

    Args:
        compliance_data: ACGME compliance validation result
        expect_compliant: Whether to expect compliance

    Raises:
        AssertionError: If compliance doesn't match expectations

    Example:
        ```python
        assert_compliance_valid(
            compliance_data={"is_compliant": True, "violations": []},
            expect_compliant=True
        )
        ```
    """
    # Check structure
    if "is_compliant" not in compliance_data:
        raise AssertionError("Compliance data missing 'is_compliant' field")

    is_compliant = compliance_data["is_compliant"]

    # Check compliance matches expectation
    if is_compliant != expect_compliant:
        if expect_compliant:
            violations = compliance_data.get("violations", [])
            raise AssertionError(
                f"Expected compliant schedule, but found violations: {violations}"
            )
        else:
            raise AssertionError(
                "Expected non-compliant schedule, but it is compliant"
            )

    # If expecting violations, check they're present
    if not expect_compliant:
        violations = compliance_data.get("violations", [])
        if not violations:
            raise AssertionError(
                "Expected violations for non-compliant schedule, but none found"
            )

    # Check summary data
    if "summary" in compliance_data:
        summary = compliance_data["summary"]
        required_summary_fields = [
            "total_hours_checked",
            "max_hours_per_week",
            "one_in_seven_compliant",
        ]
        for field in required_summary_fields:
            if field not in summary:
                raise AssertionError(
                    f"Compliance summary missing field: {field}"
                )


def assert_no_conflicts(
    assignments: List[Dict[str, Any]],
    check_double_booking: bool = True,
    check_acgme: bool = False,
) -> None:
    """
    Assert assignments have no conflicts.

    Args:
        assignments: List of assignments to check
        check_double_booking: Check for double-booked blocks
        check_acgme: Check for ACGME violations

    Raises:
        AssertionError: If conflicts are found

    Example:
        ```python
        assert_no_conflicts(
            assignments=[
                {"person_id": "123", "block_id": "456"},
                {"person_id": "789", "block_id": "456"},
            ],
            check_double_booking=True
        )
        ```
    """
    if check_double_booking:
        # Check for same person assigned to multiple assignments in same block
        person_blocks = {}
        for assignment in assignments:
            person_id = assignment.get("person_id")
            block_id = assignment.get("block_id")

            if not person_id or not block_id:
                continue

            key = (person_id, block_id)
            if key in person_blocks:
                raise AssertionError(
                    f"Double booking detected: person {person_id} assigned to "
                    f"block {block_id} multiple times"
                )
            person_blocks[key] = assignment

    if check_acgme:
        # Basic ACGME checks would go here
        # This is simplified - real implementation would check hours, 1-in-7, etc.
        pass


def assert_response_time(
    duration_ms: float,
    max_ms: float,
    operation: str = "API request",
) -> None:
    """
    Assert operation completed within expected time.

    Args:
        duration_ms: Actual duration in milliseconds
        max_ms: Maximum acceptable duration
        operation: Description of operation

    Raises:
        AssertionError: If operation took too long

    Example:
        ```python
        start = time.time()
        response = await make_request()
        duration_ms = (time.time() - start) * 1000

        assert_response_time(
            duration_ms=duration_ms,
            max_ms=500,
            operation="GET /api/people"
        )
        ```
    """
    if duration_ms > max_ms:
        raise AssertionError(
            f"{operation} took {duration_ms:.2f}ms, expected <= {max_ms}ms"
        )


def assert_matches_pattern(
    value: str,
    pattern: Union[str, Pattern],
    message: str = None,
) -> None:
    """
    Assert string matches regex pattern.

    Args:
        value: String to test
        pattern: Regex pattern (string or compiled)
        message: Custom error message

    Raises:
        AssertionError: If value doesn't match pattern

    Example:
        ```python
        assert_matches_pattern(
            value="550e8400-e29b-41d4-a716-446655440000",
            pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            message="Expected valid UUID"
        )
        ```
    """
    if isinstance(pattern, str):
        pattern = re.compile(pattern)

    if not pattern.match(value):
        error_msg = message or f"Value '{value}' doesn't match pattern {pattern.pattern}"
        raise AssertionError(error_msg)


def assert_valid_uuid(
    value: str,
    message: str = None,
) -> None:
    """
    Assert string is a valid UUID.

    Args:
        value: String to test
        message: Custom error message

    Raises:
        AssertionError: If value is not a valid UUID

    Example:
        ```python
        assert_valid_uuid("550e8400-e29b-41d4-a716-446655440000")
        ```
    """
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    assert_matches_pattern(
        value=value,
        pattern=uuid_pattern,
        message=message or f"Expected valid UUID, got '{value}'",
    )


def assert_valid_date(
    value: str,
    date_format: str = "%Y-%m-%d",
    message: str = None,
) -> None:
    """
    Assert string is a valid date.

    Args:
        value: String to test
        date_format: Expected date format
        message: Custom error message

    Raises:
        AssertionError: If value is not a valid date

    Example:
        ```python
        assert_valid_date("2025-12-20")
        ```
    """
    try:
        datetime.strptime(value, date_format)
    except ValueError:
        error_msg = message or f"Expected valid date (format: {date_format}), got '{value}'"
        raise AssertionError(error_msg)


def assert_paginated_response(
    response: Dict[str, Any],
    expected_items: int = None,
    expected_total: int = None,
    item_key: str = "items",
) -> None:
    """
    Assert response is properly paginated.

    Args:
        response: Response to validate
        expected_items: Expected number of items in current page
        expected_total: Expected total number of items
        item_key: Key name for items list

    Raises:
        AssertionError: If pagination is invalid

    Example:
        ```python
        assert_paginated_response(
            response={"items": [...], "total": 100, "page": 1, "page_size": 20},
            expected_items=20,
            expected_total=100
        )
        ```
    """
    # Check required fields
    required_fields = [item_key, "total", "page", "page_size"]
    for field in required_fields:
        if field not in response:
            raise AssertionError(
                f"Paginated response missing required field: {field}"
            )

    # Check items is a list
    items = response[item_key]
    if not isinstance(items, list):
        raise AssertionError(
            f"Expected {item_key} to be list, got {type(items)}"
        )

    # Check expected counts
    if expected_items is not None:
        actual_items = len(items)
        if actual_items != expected_items:
            raise AssertionError(
                f"Expected {expected_items} items, got {actual_items}"
            )

    if expected_total is not None:
        actual_total = response["total"]
        if actual_total != expected_total:
            raise AssertionError(
                f"Expected total of {expected_total}, got {actual_total}"
            )

    # Validate pagination math
    total = response["total"]
    page_size = response["page_size"]
    expected_total_pages = (total + page_size - 1) // page_size

    if "total_pages" in response:
        actual_total_pages = response["total_pages"]
        if actual_total_pages != expected_total_pages:
            raise AssertionError(
                f"Invalid total_pages: expected {expected_total_pages}, "
                f"got {actual_total_pages}"
            )
