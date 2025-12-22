"""Prefetch and eager loading utilities.

Provides utility functions for efficiently loading related data
to prevent N+1 query problems.
"""

import json
import logging
import os
from datetime import date
from typing import Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.absence import Absence
from app.models.swap import SwapRecord
# Note: Certification, LeaveRequest, ProcedureLog, SwapRequest models don't exist
# Using Absence instead of LeaveRequest, SwapRecord instead of SwapRequest

logger = logging.getLogger(__name__)


def prefetch_assignments_with_relations(
    db: Session,
    assignment_ids: Optional[list[str]] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    person_id: Optional[str] = None,
) -> list[Assignment]:
    """
    Prefetch assignments with all related data in a single optimized query.

    This prevents N+1 queries by eagerly loading:
    - Person (requester)
    - Block (date/session)
    - Rotation template
    - Override information

    Args:
        db: Database session
        assignment_ids: Optional list of specific assignment IDs
        start_date: Optional start date filter
        end_date: Optional end date filter
        person_id: Optional person ID filter

    Returns:
        List of Assignment objects with relations loaded
    """
    query = select(Assignment).options(
        selectinload(Assignment.person),
        selectinload(Assignment.block),
        selectinload(Assignment.rotation_template),
    )

    # Apply filters
    if assignment_ids:
        query = query.where(Assignment.id.in_(assignment_ids))

    if person_id:
        query = query.where(Assignment.person_id == person_id)

    if start_date or end_date:
        query = query.join(Block)
        if start_date:
            query = query.where(Block.date >= start_date)
        if end_date:
            query = query.where(Block.date <= end_date)

        # Use contains_eager since we're joining
        query = query.options(contains_eager(Assignment.block))

    result = db.execute(query)
    return list(result.scalars().all())


def prefetch_persons_with_assignments(
    db: Session,
    person_ids: Optional[list[str]] = None,
    role: Optional[str] = None,
    include_leave: bool = False,
    include_certifications: bool = False,
    include_procedures: bool = False,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> list[Person]:
    """
    Prefetch persons with their related data.

    Args:
        db: Database session
        person_ids: Optional list of specific person IDs
        role: Optional role filter
        include_leave: Whether to load leave requests
        include_certifications: Whether to load certifications
        include_procedures: Whether to load procedure logs
        start_date: Optional date filter for assignments
        end_date: Optional date filter for assignments

    Returns:
        List of Person objects with relations loaded
    """
    # Build base query
    query = select(Person)

    # Apply filters
    if person_ids:
        query = query.where(Person.id.in_(person_ids))

    if role:
        query = query.where(Person.role == role)

    # Eager load assignments with blocks and rotations
    options = [
        selectinload(Person.assignments).selectinload(Assignment.block),
        selectinload(Person.assignments).selectinload(Assignment.rotation_template),
    ]

    # Optional relations (using actual model relationships)
    if include_leave:
        options.append(selectinload(Person.absences))

    # Note: certifications and procedures relationships may not exist on Person model
    # if include_certifications:
    #     options.append(selectinload(Person.certifications))
    # if include_procedures:
    #     options.append(selectinload(Person.procedure_logs))

    query = query.options(*options)

    result = db.execute(query)
    persons = list(result.scalars().all())

    # Filter assignments by date if needed
    if start_date or end_date:
        for person in persons:
            if person.assignments:
                filtered = []
                for assignment in person.assignments:
                    if assignment.block:
                        block_date = assignment.block.date
                        if start_date and block_date < start_date:
                            continue
                        if end_date and block_date > end_date:
                            continue
                        filtered.append(assignment)
                person.assignments = filtered

    return persons


def prefetch_blocks_with_assignments(
    db: Session,
    start_date: date,
    end_date: date,
    session: Optional[str] = None,
    include_person_details: bool = True,
) -> list[Block]:
    """
    Prefetch blocks with their assignments and related data.

    Args:
        db: Database session
        start_date: Start date
        end_date: End date
        session: Optional session filter (AM/PM)
        include_person_details: Whether to load full person details

    Returns:
        List of Block objects with assignments loaded
    """
    query = select(Block).where(
        and_(Block.date >= start_date, Block.date <= end_date)
    )

    if session:
        query = query.where(Block.session == session)

    # Eager load assignments
    if include_person_details:
        query = query.options(
            selectinload(Block.assignments).selectinload(Assignment.person),
            selectinload(Block.assignments).selectinload(
                Assignment.rotation_template
            ),
        )
    else:
        query = query.options(selectinload(Block.assignments))

    query = query.order_by(Block.date, Block.session)

    result = db.execute(query)
    return list(result.scalars().all())


def prefetch_schedule_data(
    db: Session,
    start_date: date,
    end_date: date,
    person_ids: Optional[list[str]] = None,
) -> dict[str, any]:
    """
    Prefetch all data needed for schedule display/analysis.

    Optimized single-pass loading of all schedule-related data.

    Args:
        db: Database session
        start_date: Start date
        end_date: End date
        person_ids: Optional list of person IDs to filter

    Returns:
        Dictionary with:
        - blocks: List of blocks
        - assignments: List of assignments
        - persons: List of persons
        - rotations: List of rotation templates
        - leave_requests: List of active leave requests
    """
    # Load blocks
    blocks = prefetch_blocks_with_assignments(
        db, start_date, end_date, include_person_details=False
    )

    # Load assignments with relations
    assignments_query = (
        select(Assignment)
        .join(Block)
        .options(
            selectinload(Assignment.person),
            selectinload(Assignment.block),
            selectinload(Assignment.rotation_template),
        )
        .where(and_(Block.date >= start_date, Block.date <= end_date))
    )

    if person_ids:
        assignments_query = assignments_query.where(
            Assignment.person_id.in_(person_ids)
        )

    assignments = list(db.execute(assignments_query).scalars().all())

    # Extract unique person IDs from assignments
    unique_person_ids = list(
        set(str(a.person_id) for a in assignments if a.person_id)
    )

    # Load persons with their leave requests
    persons = prefetch_persons_with_assignments(
        db,
        person_ids=unique_person_ids if unique_person_ids else None,
        include_leave=True,
        include_certifications=False,
        include_procedures=False,
        start_date=start_date,
        end_date=end_date,
    )

    # Load rotation templates used in this period
    rotation_ids = list(
        set(
            str(a.rotation_template_id)
            for a in assignments
            if a.rotation_template_id
        )
    )

    rotations = []
    if rotation_ids:
        rotations_query = select(RotationTemplate).where(
            RotationTemplate.id.in_(rotation_ids)
        )
        rotations = list(db.execute(rotations_query).scalars().all())

    # Load active absences (replaces leave_requests)
    absences_query = (
        select(Absence)
        .options(selectinload(Absence.person))
        .where(
            and_(
                Absence.start_date <= end_date,
                Absence.end_date >= start_date,
                Absence.status.in_(["approved", "pending"]),
            )
        )
    )

    if person_ids:
        absences_query = absences_query.where(
            Absence.person_id.in_(person_ids)
        )

    absences = list(db.execute(absences_query).scalars().all())

    return {
        "blocks": blocks,
        "assignments": assignments,
        "persons": persons,
        "rotations": rotations,
        "absences": absences,  # renamed from leave_requests
    }


def prefetch_swap_requests_with_details(
    db: Session,
    person_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> list[SwapRecord]:
    """
    Prefetch swap requests with all related data.

    Args:
        db: Database session
        person_id: Optional person ID filter
        status: Optional status filter
        limit: Maximum results

    Returns:
        List of SwapRecord objects with relations loaded
    """
    query = select(SwapRecord).options(
        selectinload(SwapRecord.requester),
        selectinload(SwapRecord.target),
    )

    if person_id:
        query = query.where(
            (SwapRecord.requester_id == person_id)
            | (SwapRecord.target_id == person_id)
        )

    if status:
        query = query.where(SwapRecord.status == status)

    query = query.order_by(SwapRecord.created_at.desc()).limit(limit)

    result = db.execute(query)
    return list(result.scalars().all())


def prefetch_person_workload_data(
    db: Session,
    person_id: str,
    start_date: date,
    end_date: date,
) -> dict[str, any]:
    """
    Prefetch all data needed for person workload analysis.

    Args:
        db: Database session
        person_id: Person ID
        start_date: Start date
        end_date: End date

    Returns:
        Dictionary with person, assignments, absences
    """
    # Load person with available relations
    person_query = (
        select(Person)
        .where(Person.id == person_id)
        .options(
            selectinload(Person.assignments)
            .selectinload(Assignment.block),
            selectinload(Person.assignments)
            .selectinload(Assignment.rotation_template),
            selectinload(Person.absences),
        )
    )

    result = db.execute(person_query)
    person = result.scalar_one_or_none()

    if not person:
        return {}

    # Filter assignments by date
    filtered_assignments = [
        a
        for a in person.assignments
        if a.block and start_date <= a.block.date <= end_date
    ]

    # Filter absences by date
    filtered_absences = [
        ab
        for ab in person.absences
        if ab.start_date <= end_date and ab.end_date >= start_date
    ]

    return {
        "person": person,
        "assignments": filtered_assignments,
        "absences": filtered_absences,
    }


def prefetch_rotation_coverage_data(
    db: Session,
    rotation_id: str,
    start_date: date,
    end_date: date,
) -> dict[str, any]:
    """
    Prefetch all data for rotation coverage analysis.

    Args:
        db: Database session
        rotation_id: Rotation template ID
        start_date: Start date
        end_date: End date

    Returns:
        Dictionary with rotation, assignments, persons
    """
    # Load rotation
    rotation_query = select(RotationTemplate).where(
        RotationTemplate.id == rotation_id
    )
    rotation = db.execute(rotation_query).scalar_one_or_none()

    if not rotation:
        return {}

    # Load assignments for this rotation
    assignments_query = (
        select(Assignment)
        .join(Block)
        .options(
            selectinload(Assignment.person),
            selectinload(Assignment.block),
        )
        .where(
            and_(
                Assignment.rotation_template_id == rotation_id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
        )
    )

    assignments = list(db.execute(assignments_query).scalars().all())

    # Extract unique persons
    person_ids = list(set(str(a.person_id) for a in assignments if a.person_id))

    persons = []
    if person_ids:
        persons_query = select(Person).where(Person.id.in_(person_ids))
        persons = list(db.execute(persons_query).scalars().all())

    return {
        "rotation": rotation,
        "assignments": assignments,
        "persons": persons,
    }


def prefetch_with_caching(
    db: Session,
    cache_key: str,
    fetch_function,
    ttl_seconds: int = 300,
    **kwargs,
) -> Any:
    """
    Prefetch with caching support using Redis.

    Attempts to retrieve data from Redis cache. If not found,
    fetches data using the provided function and caches it.

    Args:
        db: Database session
        cache_key: Cache key
        fetch_function: Function to fetch data if not cached
        ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
        **kwargs: Arguments to pass to fetch_function

    Returns:
        Fetched or cached data
    """
    # Try to get from Redis cache
    try:
        import redis.asyncio as redis_async
        import redis as redis_sync

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache_full_key = f"prefetch:{cache_key}"

        # Use sync Redis client (since this function is sync)
        client = redis_sync.from_url(redis_url, decode_responses=True)

        # Try to get cached data
        cached_data = client.get(cache_full_key)

        if cached_data:
            logger.debug(f"Cache hit for prefetch: {cache_key}")
            # Deserialize and return
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                logger.warning(
                    f"Failed to deserialize cached data for {cache_key}, fetching fresh data"
                )
                # Fall through to fetch fresh data

        # Cache miss - fetch fresh data
        logger.debug(f"Cache miss for prefetch: {cache_key}")
        data = fetch_function(db, **kwargs)

        # Try to cache the result
        try:
            # Serialize data - handle SQLAlchemy models
            serialized = _serialize_for_cache(data)
            client.setex(
                name=cache_full_key,
                time=ttl_seconds,
                value=json.dumps(serialized, default=str),
            )
            logger.debug(f"Cached prefetch data: {cache_key} (TTL: {ttl_seconds}s)")
        except Exception as e:
            logger.warning(f"Failed to cache prefetch data for {cache_key}: {e}")

        client.close()
        return data

    except ImportError:
        logger.debug("Redis not available, skipping cache")
        return fetch_function(db, **kwargs)
    except Exception as e:
        logger.warning(f"Redis cache error for {cache_key}: {e}, fetching directly")
        return fetch_function(db, **kwargs)


def _serialize_for_cache(data: Any) -> Any:
    """
    Serialize data for Redis cache storage.

    Handles SQLAlchemy model objects by converting them to dictionaries.

    Args:
        data: Data to serialize

    Returns:
        Serializable version of data
    """
    if data is None:
        return None

    # Handle lists
    if isinstance(data, list):
        return [_serialize_for_cache(item) for item in data]

    # Handle dictionaries
    if isinstance(data, dict):
        return {key: _serialize_for_cache(value) for key, value in data.items()}

    # Handle SQLAlchemy model instances
    if hasattr(data, "__table__"):
        # Convert to dict using column names
        result = {}
        for column in data.__table__.columns:
            value = getattr(data, column.name, None)
            # Skip relationships and other non-serializable attributes
            if value is not None and not hasattr(value, "__table__"):
                result[column.name] = value
        return result

    # Return as-is for primitives
    return data
