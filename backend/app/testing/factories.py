"""
Factory utilities for creating mock API responses.

Provides factories for:
- Mock responses with common patterns
- Error responses
- Paginated responses
- ACGME validation responses
- Schedule generation responses
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.testing.mock_server import MockResponse


class MockResponseFactory:
    """
    Factory for creating mock API responses.

    Provides convenient methods for common response patterns.
    """

    @staticmethod
    def success(
        data: Any = None,
        status_code: int = 200,
        headers: Dict[str, str] = None,
    ) -> MockResponse:
        """
        Create a successful response.

        Args:
            data: Response data
            status_code: HTTP status code (default 200)
            headers: Response headers

        Returns:
            MockResponse with success status
        """
        return MockResponse(
            status_code=status_code,
            body=data or {"status": "ok"},
            headers=headers or {},
        )

    @staticmethod
    def error(
        message: str = "An error occurred",
        status_code: int = 400,
        error_type: str = "ValidationError",
        details: Dict[str, Any] = None,
    ) -> MockResponse:
        """
        Create an error response.

        Args:
            message: Error message
            status_code: HTTP status code
            error_type: Error type identifier
            details: Additional error details

        Returns:
            MockResponse with error status
        """
        body = {
            "detail": message,
            "type": error_type,
        }
        if details:
            body["details"] = details

        return MockResponse(
            status_code=status_code,
            body=body,
        )

    @staticmethod
    def paginated(
        items: List[Any],
        total: int = None,
        page: int = 1,
        page_size: int = 20,
        item_key: str = "items",
    ) -> MockResponse:
        """
        Create a paginated response.

        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page
            item_key: Key name for items list

        Returns:
            MockResponse with pagination metadata
        """
        total = total or len(items)

        return MockResponse(
            status_code=200,
            body={
                item_key: items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            },
        )

    @staticmethod
    def created(
        resource: Dict[str, Any],
        resource_id: str = None,
        location: str = None,
    ) -> MockResponse:
        """
        Create a 201 Created response.

        Args:
            resource: Created resource data
            resource_id: ID of created resource
            location: Location header value

        Returns:
            MockResponse with 201 status
        """
        headers = {}
        if location:
            headers["Location"] = location
        elif resource_id:
            headers["Location"] = f"/api/v1/resources/{resource_id}"

        return MockResponse(
            status_code=201,
            body=resource,
            headers=headers,
        )

    @staticmethod
    def accepted(
        job_id: str = None,
        message: str = "Request accepted",
    ) -> MockResponse:
        """
        Create a 202 Accepted response for async operations.

        Args:
            job_id: ID of background job
            message: Status message

        Returns:
            MockResponse with 202 status
        """
        job_id = job_id or str(uuid4())

        return MockResponse(
            status_code=202,
            body={
                "job_id": job_id,
                "status": "pending",
                "message": message,
            },
        )

    @staticmethod
    def no_content() -> MockResponse:
        """
        Create a 204 No Content response.

        Returns:
            MockResponse with 204 status
        """
        return MockResponse(
            status_code=204,
            body=None,
        )

    @staticmethod
    def not_found(
        resource_type: str = "Resource",
        resource_id: str = None,
    ) -> MockResponse:
        """
        Create a 404 Not Found response.

        Args:
            resource_type: Type of resource not found
            resource_id: ID of resource

        Returns:
            MockResponse with 404 status
        """
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"

        return MockResponse(
            status_code=404,
            body={"detail": message},
        )

    @staticmethod
    def validation_error(
        field: str,
        message: str,
        additional_errors: List[Dict[str, str]] = None,
    ) -> MockResponse:
        """
        Create a validation error response.

        Args:
            field: Field that failed validation
            message: Validation error message
            additional_errors: Additional validation errors

        Returns:
            MockResponse with 422 status
        """
        errors = [{"field": field, "message": message}]
        if additional_errors:
            errors.extend(additional_errors)

        return MockResponse(
            status_code=422,
            body={
                "detail": "Validation error",
                "errors": errors,
            },
        )


def create_mock_response(
    status_code: int = 200,
    body: Any = None,
    headers: Dict[str, str] = None,
    delay_ms: int = 0,
) -> MockResponse:
    """
    Create a basic mock response.

    Args:
        status_code: HTTP status code
        body: Response body
        headers: Response headers
        delay_ms: Response delay in milliseconds

    Returns:
        MockResponse instance
    """
    return MockResponse(
        status_code=status_code,
        body=body or {},
        headers=headers or {},
        delay_ms=delay_ms,
    )


def create_error_response(
    status_code: int = 400,
    message: str = "Bad Request",
    details: Any = None,
) -> MockResponse:
    """
    Create an error response.

    Args:
        status_code: HTTP error status code
        message: Error message
        details: Additional error details

    Returns:
        MockResponse with error status
    """
    body = {"detail": message}
    if details:
        body["details"] = details

    return MockResponse(
        status_code=status_code,
        body=body,
    )


def create_paginated_response(
    items: List[Any],
    total: int = None,
    page: int = 1,
    page_size: int = 20,
) -> MockResponse:
    """
    Create a paginated response.

    Args:
        items: Items for current page
        total: Total number of items
        page: Current page number
        page_size: Items per page

    Returns:
        MockResponse with pagination
    """
    return MockResponseFactory.paginated(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


def create_person_response(
    person_id: str = None,
    name: str = "Dr. Test Person",
    person_type: str = "resident",
    pgy_level: int = 2,
) -> Dict[str, Any]:
    """
    Create a person resource response.

    Args:
        person_id: Person ID
        name: Person name
        person_type: "resident" or "faculty"
        pgy_level: PGY level for residents

    Returns:
        Person resource dictionary
    """
    person_id = person_id or str(uuid4())

    person = {
        "id": person_id,
        "name": name,
        "type": person_type,
        "email": f"{name.lower().replace(' ', '.')}@hospital.org",
    }

    if person_type == "resident":
        person["pgy_level"] = pgy_level
    elif person_type == "faculty":
        person["performs_procedures"] = True
        person["specialties"] = ["General"]

    return person


def create_assignment_response(
    assignment_id: str = None,
    person_id: str = None,
    block_id: str = None,
    rotation_template_id: str = None,
) -> Dict[str, Any]:
    """
    Create an assignment resource response.

    Args:
        assignment_id: Assignment ID
        person_id: Person ID
        block_id: Block ID
        rotation_template_id: Rotation template ID

    Returns:
        Assignment resource dictionary
    """
    return {
        "id": assignment_id or str(uuid4()),
        "person_id": person_id or str(uuid4()),
        "block_id": block_id or str(uuid4()),
        "rotation_template_id": rotation_template_id or str(uuid4()),
        "role": "primary",
    }


def create_block_response(
    block_id: str = None,
    block_date: date = None,
    time_of_day: str = "AM",
) -> Dict[str, Any]:
    """
    Create a block resource response.

    Args:
        block_id: Block ID
        block_date: Block date
        time_of_day: "AM" or "PM"

    Returns:
        Block resource dictionary
    """
    block_date = block_date or date.today()

    return {
        "id": block_id or str(uuid4()),
        "date": block_date.isoformat(),
        "time_of_day": time_of_day,
        "block_number": 1,
        "is_weekend": block_date.weekday() >= 5,
        "is_holiday": False,
    }


def create_acgme_validation_response(
    is_compliant: bool = True,
    violations: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create ACGME validation response.

    Args:
        is_compliant: Whether schedule is ACGME compliant
        violations: List of violations if not compliant

    Returns:
        ACGME validation result dictionary
    """
    return {
        "is_compliant": is_compliant,
        "violations": violations or [],
        "summary": {
            "total_hours_checked": 100,
            "max_hours_per_week": 72 if is_compliant else 85,
            "one_in_seven_compliant": is_compliant,
            "supervision_ratios_met": is_compliant,
        },
        "checked_at": datetime.utcnow().isoformat(),
    }


def create_swap_request_response(
    swap_id: str = None,
    status: str = "pending",
    swap_type: str = "one_to_one",
) -> Dict[str, Any]:
    """
    Create swap request response.

    Args:
        swap_id: Swap request ID
        status: Swap status
        swap_type: Type of swap

    Returns:
        Swap request dictionary
    """
    return {
        "id": swap_id or str(uuid4()),
        "status": status,
        "swap_type": swap_type,
        "created_at": datetime.utcnow().isoformat(),
        "requester_id": str(uuid4()),
        "requested_assignment_id": str(uuid4()),
    }


def create_schedule_generation_response(
    job_id: str = None,
    status: str = "pending",
) -> Dict[str, Any]:
    """
    Create schedule generation job response.

    Args:
        job_id: Job ID
        status: Job status

    Returns:
        Schedule generation job dictionary
    """
    return {
        "job_id": job_id or str(uuid4()),
        "status": status,
        "created_at": datetime.utcnow().isoformat(),
        "message": f"Schedule generation {status}",
    }


def create_resilience_health_response(
    status: str = "operational",
    utilization: float = 0.65,
    defense_level: str = "GREEN",
) -> Dict[str, Any]:
    """
    Create resilience health check response.

    Args:
        status: System status
        utilization: Current utilization level (0.0-1.0)
        defense_level: Current defense level

    Returns:
        Resilience health dictionary
    """
    return {
        "status": status,
        "utilization": utilization,
        "defense_level": defense_level,
        "metrics_enabled": True,
        "components": [
            "utilization_monitor",
            "defense_in_depth",
            "contingency_analyzer",
            "fallback_scheduler",
            "sacrifice_hierarchy",
        ],
        "last_check": datetime.utcnow().isoformat(),
    }
