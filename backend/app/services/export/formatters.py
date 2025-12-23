"""
Data formatters for export services.

Provides utility functions for transforming database models into
export-friendly formats with field selection and custom transformations.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


def format_datetime(dt: datetime | None) -> str | None:
    """
    Format datetime for export.

    Args:
        dt: Datetime object to format

    Returns:
        ISO 8601 formatted string or None
    """
    if dt is None:
        return None
    return dt.isoformat()


def format_date(d: date | None) -> str | None:
    """
    Format date for export.

    Args:
        d: Date object to format

    Returns:
        ISO 8601 formatted string (YYYY-MM-DD) or None
    """
    if d is None:
        return None
    return d.isoformat()


def format_uuid(uuid_val: UUID | None) -> str | None:
    """
    Format UUID for export.

    Args:
        uuid_val: UUID object to format

    Returns:
        String representation or None
    """
    if uuid_val is None:
        return None
    return str(uuid_val)


def format_assignment(
    assignment: Assignment,
    fields: list[str] | None = None,
    include_relations: bool = False,
) -> dict[str, Any]:
    """
    Format assignment model for export.

    Args:
        assignment: Assignment model instance
        fields: List of fields to include (None = all fields)
        include_relations: Whether to include related objects

    Returns:
        Dictionary of assignment data
    """
    data = {
        "id": format_uuid(assignment.id),
        "block_id": format_uuid(assignment.block_id),
        "person_id": format_uuid(assignment.person_id),
        "rotation_template_id": format_uuid(assignment.rotation_template_id),
        "role": assignment.role,
        "activity_override": assignment.activity_override,
        "notes": assignment.notes,
        "override_reason": assignment.override_reason,
        "override_acknowledged_at": format_datetime(
            assignment.override_acknowledged_at
        ),
        "confidence": assignment.confidence,
        "score": assignment.score,
        "created_by": assignment.created_by,
        "created_at": format_datetime(assignment.created_at),
        "updated_at": format_datetime(assignment.updated_at),
    }

    # Add computed fields
    data["activity_name"] = assignment.activity_name
    data["abbreviation"] = assignment.abbreviation

    # Add related objects if requested
    if include_relations:
        if assignment.block:
            data["block"] = format_block(assignment.block, include_relations=False)
        if assignment.person:
            data["person"] = format_person(assignment.person, include_relations=False)
        if assignment.rotation_template:
            data["rotation_template"] = {
                "id": format_uuid(assignment.rotation_template.id),
                "name": assignment.rotation_template.name,
                "abbreviation": assignment.rotation_template.abbreviation,
            }

    # Filter fields if specified
    if fields:
        data = {k: v for k, v in data.items() if k in fields}

    return data


def format_person(
    person: Person, fields: list[str] | None = None, include_relations: bool = False
) -> dict[str, Any]:
    """
    Format person model for export.

    Args:
        person: Person model instance
        fields: List of fields to include (None = all fields)
        include_relations: Whether to include related objects

    Returns:
        Dictionary of person data
    """
    data = {
        "id": format_uuid(person.id),
        "name": person.name,
        "type": person.type,
        "email": person.email,
        "pgy_level": person.pgy_level,
        "target_clinical_blocks": person.target_clinical_blocks,
        "performs_procedures": person.performs_procedures,
        "specialties": person.specialties,
        "primary_duty": person.primary_duty,
        "faculty_role": person.faculty_role,
        "sunday_call_count": person.sunday_call_count,
        "weekday_call_count": person.weekday_call_count,
        "fmit_weeks_count": person.fmit_weeks_count,
        "created_at": format_datetime(person.created_at),
        "updated_at": format_datetime(person.updated_at),
    }

    # Add computed fields
    data["is_resident"] = person.is_resident
    data["is_faculty"] = person.is_faculty
    if person.is_resident:
        data["supervision_ratio"] = person.supervision_ratio
    if person.is_faculty:
        data["weekly_clinic_limit"] = person.weekly_clinic_limit
        data["block_clinic_limit"] = person.block_clinic_limit
        data["sm_clinic_weekly_target"] = person.sm_clinic_weekly_target
        data["avoid_tuesday_call"] = person.avoid_tuesday_call
        data["prefer_wednesday_call"] = person.prefer_wednesday_call
        data["is_sports_medicine"] = person.is_sports_medicine

    # Filter fields if specified
    if fields:
        data = {k: v for k, v in data.items() if k in fields}

    return data


def format_block(
    block: Block, fields: list[str] | None = None, include_relations: bool = False
) -> dict[str, Any]:
    """
    Format block model for export.

    Args:
        block: Block model instance
        fields: List of fields to include (None = all fields)
        include_relations: Whether to include related objects

    Returns:
        Dictionary of block data
    """
    data = {
        "id": format_uuid(block.id),
        "date": format_date(block.date),
        "time_of_day": block.time_of_day,
        "block_number": block.block_number,
        "is_weekend": block.is_weekend,
        "is_holiday": block.is_holiday,
        "holiday_name": block.holiday_name,
    }

    # Add computed fields
    data["display_name"] = block.display_name
    data["is_workday"] = block.is_workday

    # Filter fields if specified
    if fields:
        data = {k: v for k, v in data.items() if k in fields}

    return data


def format_schedule_row(assignment: Assignment, flat: bool = True) -> dict[str, Any]:
    """
    Format assignment as a flat schedule row for CSV export.

    Args:
        assignment: Assignment model instance
        flat: Whether to flatten related objects into single row

    Returns:
        Dictionary of flattened schedule data
    """
    if not flat:
        return format_assignment(assignment, include_relations=True)

    # Flatten all related data into single row
    data = {
        "assignment_id": format_uuid(assignment.id),
        "date": format_date(assignment.block.date) if assignment.block else None,
        "time_of_day": assignment.block.time_of_day if assignment.block else None,
        "block_number": assignment.block.block_number if assignment.block else None,
        "is_weekend": assignment.block.is_weekend if assignment.block else None,
        "is_holiday": assignment.block.is_holiday if assignment.block else None,
        "person_id": format_uuid(assignment.person_id),
        "person_name": assignment.person.name if assignment.person else None,
        "person_type": assignment.person.type if assignment.person else None,
        "pgy_level": assignment.person.pgy_level if assignment.person else None,
        "faculty_role": assignment.person.faculty_role if assignment.person else None,
        "role": assignment.role,
        "activity_name": assignment.activity_name,
        "abbreviation": assignment.abbreviation,
        "activity_override": assignment.activity_override,
        "notes": assignment.notes,
        "confidence": assignment.confidence,
        "score": assignment.score,
        "created_at": format_datetime(assignment.created_at),
        "updated_at": format_datetime(assignment.updated_at),
    }

    return data


def format_analytics_row(person: Person, metrics: dict[str, Any]) -> dict[str, Any]:
    """
    Format person with analytics metrics for export.

    Args:
        person: Person model instance
        metrics: Dictionary of calculated metrics

    Returns:
        Dictionary combining person data and metrics
    """
    data = {
        "person_id": format_uuid(person.id),
        "name": person.name,
        "type": person.type,
        "pgy_level": person.pgy_level,
        "faculty_role": person.faculty_role,
    }

    # Add all metrics
    data.update(metrics)

    return data


def sanitize_for_export(value: Any) -> Any:
    """
    Sanitize a value for safe export (remove sensitive data patterns).

    Args:
        value: Value to sanitize

    Returns:
        Sanitized value
    """
    # Convert common non-serializable types
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if value is None:
        return ""
    return value


def get_available_fields(model_type: str) -> list[str]:
    """
    Get list of available fields for export by model type.

    Args:
        model_type: Type of model ('assignment', 'person', 'block', 'schedule')

    Returns:
        List of field names available for export
    """
    fields_map = {
        "assignment": [
            "id",
            "block_id",
            "person_id",
            "rotation_template_id",
            "role",
            "activity_override",
            "notes",
            "override_reason",
            "override_acknowledged_at",
            "confidence",
            "score",
            "created_by",
            "created_at",
            "updated_at",
            "activity_name",
            "abbreviation",
        ],
        "person": [
            "id",
            "name",
            "type",
            "email",
            "pgy_level",
            "target_clinical_blocks",
            "performs_procedures",
            "specialties",
            "primary_duty",
            "faculty_role",
            "sunday_call_count",
            "weekday_call_count",
            "fmit_weeks_count",
            "created_at",
            "updated_at",
            "is_resident",
            "is_faculty",
            "supervision_ratio",
            "weekly_clinic_limit",
            "block_clinic_limit",
            "sm_clinic_weekly_target",
            "avoid_tuesday_call",
            "prefer_wednesday_call",
            "is_sports_medicine",
        ],
        "block": [
            "id",
            "date",
            "time_of_day",
            "block_number",
            "is_weekend",
            "is_holiday",
            "holiday_name",
            "display_name",
            "is_workday",
        ],
        "schedule": [
            "assignment_id",
            "date",
            "time_of_day",
            "block_number",
            "is_weekend",
            "is_holiday",
            "person_id",
            "person_name",
            "person_type",
            "pgy_level",
            "faculty_role",
            "role",
            "activity_name",
            "abbreviation",
            "activity_override",
            "notes",
            "confidence",
            "score",
            "created_at",
            "updated_at",
        ],
    }

    return fields_map.get(model_type, [])
