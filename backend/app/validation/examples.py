"""
Example usage of request validation decorators.

This file provides examples of how to use the validation decorators
in FastAPI route handlers.
"""
from datetime import date
from typing import Any

from fastapi import APIRouter, Request

from app.validation import (
    validate_request,
    validate_query,
    validate_body,
    validate_pagination,
    validate_date_range_params,
    validate_conditional_field,
    required,
    string_length,
    numeric_range,
    enum_values,
    email_format,
    uuid_format,
    pgy_level_rule,
    person_type_rule,
    faculty_role_rule,
    ValidationContext,
)


router = APIRouter()


# Example 1: Query parameter validation
@router.get("/people")
@validate_query({
    "type": [enum_values(["resident", "faculty"])],
    "pgy_level": [numeric_range(min_value=1, max_value=3)]
})
async def list_people(
    type: str | None = None,
    pgy_level: int | None = None
):
    """
    List people with validated query parameters.

    Query parameters are validated before the handler executes.
    """
    return {
        "type": type,
        "pgy_level": pgy_level,
        "message": "Query validation passed"
    }


# Example 2: Request body validation
@router.post("/people")
@validate_body({
    "name": [required, string_length(min_length=1, max_length=100)],
    "type": [required, person_type_rule()],
    "email": [email_format()],
    "pgy_level": []  # Validated conditionally
})
async def create_person(request: Request):
    """
    Create a person with validated request body.

    Body fields are validated before the handler executes.
    """
    body = await request.json()
    return {
        "message": "Person created successfully",
        "data": body
    }


# Example 3: Combined query and body validation
@router.put("/assignments/{assignment_id}")
@validate_request(
    query_rules={
        "assignment_id": [required, uuid_format()]
    },
    body_rules={
        "rotation_name": [required, string_length(min_length=1)],
        "score": [numeric_range(min_value=0, max_value=100)]
    }
)
async def update_assignment(assignment_id: str, request: Request):
    """
    Update assignment with both query and body validation.

    Both query parameters and request body are validated.
    """
    body = await request.json()
    return {
        "assignment_id": assignment_id,
        "updates": body,
        "message": "Assignment updated successfully"
    }


# Example 4: Cross-field validation
def validate_schedule_dates(data: dict[str, Any], ctx: ValidationContext) -> None:
    """
    Cross-field validator for schedule dates.

    Ensures end_date is after start_date.
    """
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if start_date and end_date:
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        if start_date > end_date:
            ctx.add_field_error("end_date", "End date must be after start date")


@router.post("/schedules")
@validate_request(
    body_rules={
        "name": [required, string_length(min_length=1, max_length=200)],
        "start_date": [required],
        "end_date": [required]
    },
    cross_field_validator=validate_schedule_dates
)
async def create_schedule(request: Request):
    """
    Create schedule with cross-field validation.

    Validates that end_date comes after start_date.
    """
    body = await request.json()
    return {
        "message": "Schedule created successfully",
        "data": body
    }


# Example 5: Pagination validation
@router.get("/assignments")
@validate_pagination(max_limit=100)
async def list_assignments(page: int = 1, limit: int = 20):
    """
    List assignments with pagination validation.

    Validates page >= 1 and 1 <= limit <= 100.
    """
    return {
        "page": page,
        "limit": limit,
        "message": "Pagination validation passed"
    }


# Example 6: Conditional field validation
@router.post("/staff")
@validate_body({
    "name": [required, string_length(min_length=1, max_length=100)],
    "type": [required, person_type_rule()],
    "email": [email_format()]
})
@validate_conditional_field(
    field="pgy_level",
    condition_field="type",
    condition_value="resident",
    rules=[required, pgy_level_rule()]
)
async def create_staff_member(request: Request):
    """
    Create staff member with conditional validation.

    pgy_level is only required when type is 'resident'.
    """
    body = await request.json()
    return {
        "message": "Staff member created successfully",
        "data": body
    }


# Example 7: Date range validation
@router.get("/reports")
@validate_date_range_params(
    start_param="start_date",
    end_param="end_date"
)
async def generate_report(
    start_date: date,
    end_date: date,
    format: str = "pdf"
):
    """
    Generate report with date range validation.

    Validates that start_date <= end_date.
    """
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "format": format,
        "message": "Report generated successfully"
    }


# Example 8: Complex validation with multiple rules
def validate_faculty_data(data: dict[str, Any], ctx: ValidationContext) -> None:
    """
    Cross-field validator for faculty-specific data.

    Ensures faculty members have required credentials.
    """
    if data.get("type") == "faculty":
        # Faculty must have specialties
        if not data.get("specialties") or len(data.get("specialties", [])) == 0:
            ctx.add_field_error("specialties", "Faculty must have at least one specialty")

        # Faculty with certain roles must perform procedures
        supervisory_roles = ["pd", "apd", "oic"]
        if data.get("faculty_role") in supervisory_roles:
            if not data.get("performs_procedures"):
                ctx.add_field_error(
                    "performs_procedures",
                    f"Faculty with role {data.get('faculty_role')} must perform procedures"
                )


@router.post("/faculty")
@validate_request(
    body_rules={
        "name": [required, string_length(min_length=1, max_length=100)],
        "type": [required, person_type_rule()],
        "email": [required, email_format()],
        "faculty_role": [faculty_role_rule()],
        "performs_procedures": [],
        "specialties": []
    },
    cross_field_validator=validate_faculty_data
)
async def create_faculty(request: Request):
    """
    Create faculty with complex validation.

    Validates faculty-specific requirements using cross-field validation.
    """
    body = await request.json()
    return {
        "message": "Faculty created successfully",
        "data": body
    }


# Example 9: List validation
from app.validation import list_items

@router.post("/bulk-create")
@validate_body({
    "people": [
        required,
        list_items(
            item_rule=lambda field, value, ctx: (
                string_length(min_length=1)(field + ".name", value.get("name"), ctx)
                if isinstance(value, dict)
                else False
            ),
            min_items=1,
            max_items=50
        )
    ]
})
async def bulk_create_people(request: Request):
    """
    Bulk create people with list validation.

    Validates list of people and each item in the list.
    """
    body = await request.json()
    return {
        "message": f"Created {len(body['people'])} people",
        "count": len(body["people"])
    }


# Example 10: Custom validation rule
from app.validation import custom

def is_valid_phone(value: str) -> bool:
    """Check if phone number is valid format."""
    import re
    pattern = r'^\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
    return bool(re.match(pattern, value))


@router.post("/contacts")
@validate_body({
    "name": [required, string_length(min_length=1)],
    "phone": [custom(is_valid_phone, "Invalid phone number format")],
    "email": [email_format()]
})
async def create_contact(request: Request):
    """
    Create contact with custom validation rule.

    Demonstrates using a custom validation function.
    """
    body = await request.json()
    return {
        "message": "Contact created successfully",
        "data": body
    }
