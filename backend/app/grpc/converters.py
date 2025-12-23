"""
Protobuf <-> Pydantic converters for gRPC services.

This module provides bidirectional conversion between:
- Pydantic models (used in FastAPI and service layer)
- Protobuf messages (used in gRPC communication)

Design:
- Type-safe conversions with proper type hints
- Null/None handling for optional fields
- UUID <-> string conversion
- Datetime <-> timestamp conversion
- Nested object support
- List/repeated field support

Usage:
    from app.grpc.converters import to_proto_assignment, from_proto_assignment
    from app.schemas.assignment import AssignmentResponse

    # Pydantic -> Protobuf
    assignment_response = AssignmentResponse(...)
    proto_msg = to_proto_assignment(assignment_response)

    # Protobuf -> Pydantic
    assignment_data = from_proto_assignment(proto_msg)
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from google.protobuf.timestamp_pb2 import Timestamp


def uuid_to_string(uuid_obj: UUID | None) -> str:
    """
    Convert UUID to string for Protobuf.

    Args:
        uuid_obj: UUID object or None

    Returns:
        String representation of UUID, or empty string if None
    """
    if uuid_obj is None:
        return ""
    return str(uuid_obj)


def string_to_uuid(uuid_str: str) -> UUID | None:
    """
    Convert string to UUID from Protobuf.

    Args:
        uuid_str: String representation of UUID

    Returns:
        UUID object, or None if string is empty
    """
    if not uuid_str:
        return None
    return UUID(uuid_str)


def datetime_to_timestamp(dt: datetime | None) -> Timestamp | None:
    """
    Convert Python datetime to Protobuf Timestamp.

    Args:
        dt: Python datetime object or None

    Returns:
        Protobuf Timestamp, or None if input is None
    """
    if dt is None:
        return None

    timestamp = Timestamp()
    timestamp.FromDatetime(dt)
    return timestamp


def timestamp_to_datetime(ts: Timestamp | None) -> datetime | None:
    """
    Convert Protobuf Timestamp to Python datetime.

    Args:
        ts: Protobuf Timestamp or None

    Returns:
        Python datetime object, or None if input is None
    """
    if ts is None or not ts.seconds:
        return None
    return ts.ToDatetime()


def pydantic_to_dict(obj: Any, exclude_none: bool = True) -> dict:
    """
    Convert Pydantic model to dict for Protobuf conversion.

    Args:
        obj: Pydantic model instance
        exclude_none: Whether to exclude None values

    Returns:
        Dictionary representation suitable for Protobuf
    """
    if hasattr(obj, "model_dump"):
        # Pydantic v2
        return obj.model_dump(exclude_none=exclude_none)
    elif hasattr(obj, "dict"):
        # Pydantic v1
        return obj.dict(exclude_none=exclude_none)
    else:
        raise TypeError(f"Object {obj} is not a Pydantic model")


class AssignmentConverter:
    """
    Converter for Assignment messages.

    Handles conversion between:
    - app.schemas.assignment.AssignmentResponse (Pydantic)
    - AssignmentMessage (Protobuf)
    """

    @staticmethod
    def to_proto(assignment: Any) -> dict:
        """
        Convert Pydantic AssignmentResponse to Protobuf-compatible dict.

        Note: This returns a dict rather than actual Protobuf message,
        as the Protobuf classes are generated from .proto files.
        In production, you would import the generated classes.

        Args:
            assignment: AssignmentResponse Pydantic model

        Returns:
            Dict with Protobuf-compatible types
        """
        return {
            "id": uuid_to_string(assignment.id),
            "block_id": uuid_to_string(assignment.block_id),
            "person_id": uuid_to_string(assignment.person_id),
            "rotation_template_id": uuid_to_string(assignment.rotation_template_id),
            "role": assignment.role,
            "activity_override": assignment.activity_override or "",
            "notes": assignment.notes or "",
            "override_reason": assignment.override_reason or "",
            "created_by": assignment.created_by or "",
            "created_at": datetime_to_timestamp(assignment.created_at),
            "updated_at": datetime_to_timestamp(assignment.updated_at),
            "override_acknowledged_at": datetime_to_timestamp(
                assignment.override_acknowledged_at
            ),
            "confidence": assignment.confidence or 0.0,
            "score": assignment.score or 0.0,
        }

    @staticmethod
    def from_proto(proto_msg: dict) -> dict:
        """
        Convert Protobuf message to dict for Pydantic model creation.

        Args:
            proto_msg: Protobuf message (as dict)

        Returns:
            Dict suitable for AssignmentResponse(**dict)
        """
        return {
            "id": string_to_uuid(proto_msg.get("id", "")),
            "block_id": string_to_uuid(proto_msg.get("block_id", "")),
            "person_id": string_to_uuid(proto_msg.get("person_id", "")),
            "rotation_template_id": string_to_uuid(
                proto_msg.get("rotation_template_id")
            ),
            "role": proto_msg.get("role", ""),
            "activity_override": proto_msg.get("activity_override") or None,
            "notes": proto_msg.get("notes") or None,
            "override_reason": proto_msg.get("override_reason") or None,
            "created_by": proto_msg.get("created_by") or None,
            "created_at": timestamp_to_datetime(proto_msg.get("created_at")),
            "updated_at": timestamp_to_datetime(proto_msg.get("updated_at")),
            "override_acknowledged_at": timestamp_to_datetime(
                proto_msg.get("override_acknowledged_at")
            ),
            "confidence": proto_msg.get("confidence"),
            "score": proto_msg.get("score"),
        }


class PersonConverter:
    """
    Converter for Person messages.

    Handles conversion between:
    - app.schemas.person.PersonResponse (Pydantic)
    - PersonMessage (Protobuf)
    """

    @staticmethod
    def to_proto(person: Any) -> dict:
        """
        Convert Pydantic PersonResponse to Protobuf-compatible dict.

        Args:
            person: PersonResponse Pydantic model

        Returns:
            Dict with Protobuf-compatible types
        """
        return {
            "id": uuid_to_string(person.id),
            "name": person.name,
            "email": person.email or "",
            "type": person.type,
            "rank": person.rank or "",
            "pgy_year": person.pgy_year or 0,
            "specialty": person.specialty or "",
            "is_active": person.is_active if hasattr(person, "is_active") else True,
            "created_at": datetime_to_timestamp(getattr(person, "created_at", None)),
            "updated_at": datetime_to_timestamp(getattr(person, "updated_at", None)),
        }

    @staticmethod
    def from_proto(proto_msg: dict) -> dict:
        """
        Convert Protobuf message to dict for Pydantic model creation.

        Args:
            proto_msg: Protobuf message (as dict)

        Returns:
            Dict suitable for PersonResponse(**dict)
        """
        return {
            "id": string_to_uuid(proto_msg.get("id", "")),
            "name": proto_msg.get("name", ""),
            "email": proto_msg.get("email") or None,
            "type": proto_msg.get("type", ""),
            "rank": proto_msg.get("rank") or None,
            "pgy_year": proto_msg.get("pgy_year") or None,
            "specialty": proto_msg.get("specialty") or None,
            "is_active": proto_msg.get("is_active", True),
            "created_at": timestamp_to_datetime(proto_msg.get("created_at")),
            "updated_at": timestamp_to_datetime(proto_msg.get("updated_at")),
        }


class BlockConverter:
    """
    Converter for Block messages.

    Handles conversion between:
    - app.schemas.block.BlockResponse (Pydantic)
    - BlockMessage (Protobuf)
    """

    @staticmethod
    def to_proto(block: Any) -> dict:
        """
        Convert Pydantic BlockResponse to Protobuf-compatible dict.

        Args:
            block: BlockResponse Pydantic model

        Returns:
            Dict with Protobuf-compatible types
        """
        return {
            "id": uuid_to_string(block.id),
            "date": block.date.isoformat()
            if hasattr(block.date, "isoformat")
            else str(block.date),
            "period": block.period,
            "is_weekend": block.is_weekend if hasattr(block, "is_weekend") else False,
            "is_holiday": block.is_holiday if hasattr(block, "is_holiday") else False,
            "created_at": datetime_to_timestamp(getattr(block, "created_at", None)),
        }

    @staticmethod
    def from_proto(proto_msg: dict) -> dict:
        """
        Convert Protobuf message to dict for Pydantic model creation.

        Args:
            proto_msg: Protobuf message (as dict)

        Returns:
            Dict suitable for BlockResponse(**dict)
        """
        from datetime import date

        date_str = proto_msg.get("date", "")
        block_date = date.fromisoformat(date_str) if date_str else None

        return {
            "id": string_to_uuid(proto_msg.get("id", "")),
            "date": block_date,
            "period": proto_msg.get("period", ""),
            "is_weekend": proto_msg.get("is_weekend", False),
            "is_holiday": proto_msg.get("is_holiday", False),
            "created_at": timestamp_to_datetime(proto_msg.get("created_at")),
        }


class ScheduleConverter:
    """
    Converter for Schedule messages.

    Handles conversion for schedule generation results.
    """

    @staticmethod
    def to_proto(schedule_result: Any) -> dict:
        """
        Convert schedule generation result to Protobuf-compatible dict.

        Args:
            schedule_result: Schedule result from scheduling engine

        Returns:
            Dict with Protobuf-compatible types
        """
        return {
            "schedule_id": uuid_to_string(getattr(schedule_result, "id", None)),
            "status": getattr(schedule_result, "status", "unknown"),
            "created_at": datetime_to_timestamp(
                getattr(schedule_result, "created_at", None)
            ),
            "assignments_count": getattr(schedule_result, "assignments_count", 0),
            "is_compliant": getattr(schedule_result, "is_compliant", False),
            "violations_count": len(getattr(schedule_result, "violations", [])),
            "warnings": getattr(schedule_result, "warnings", []),
        }

    @staticmethod
    def from_proto(proto_msg: dict) -> dict:
        """
        Convert Protobuf message to dict for schedule result.

        Args:
            proto_msg: Protobuf message (as dict)

        Returns:
            Dict with schedule result data
        """
        return {
            "schedule_id": string_to_uuid(proto_msg.get("schedule_id", "")),
            "status": proto_msg.get("status", "unknown"),
            "created_at": timestamp_to_datetime(proto_msg.get("created_at")),
            "assignments_count": proto_msg.get("assignments_count", 0),
            "is_compliant": proto_msg.get("is_compliant", False),
            "violations_count": proto_msg.get("violations_count", 0),
            "warnings": list(proto_msg.get("warnings", [])),
        }


# Convenience functions for common conversions
def to_proto_assignment(assignment: Any) -> dict:
    """Convert Assignment to Protobuf dict."""
    return AssignmentConverter.to_proto(assignment)


def from_proto_assignment(proto_msg: dict) -> dict:
    """Convert Protobuf dict to Assignment data."""
    return AssignmentConverter.from_proto(proto_msg)


def to_proto_person(person: Any) -> dict:
    """Convert Person to Protobuf dict."""
    return PersonConverter.to_proto(person)


def from_proto_person(proto_msg: dict) -> dict:
    """Convert Protobuf dict to Person data."""
    return PersonConverter.from_proto(proto_msg)


def to_proto_block(block: Any) -> dict:
    """Convert Block to Protobuf dict."""
    return BlockConverter.to_proto(block)


def from_proto_block(proto_msg: dict) -> dict:
    """Convert Protobuf dict to Block data."""
    return BlockConverter.from_proto(proto_msg)


def to_proto_schedule(schedule_result: Any) -> dict:
    """Convert Schedule result to Protobuf dict."""
    return ScheduleConverter.to_proto(schedule_result)


def from_proto_schedule(proto_msg: dict) -> dict:
    """Convert Protobuf dict to Schedule result data."""
    return ScheduleConverter.from_proto(proto_msg)
