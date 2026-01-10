"""Conflict Resolution API routes.

Exposes the ConflictAutoResolver service for analyzing and resolving
schedule conflicts with safety checks and impact assessment.
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus
from app.models.user import User
from app.schemas.conflict_resolution import (
    BatchResolutionReport,
    ConflictAnalysis,
    ConflictListResponse,
    ConflictResponse,
    ResolutionOption,
    ResolutionResult,
)
from app.services.conflict_auto_resolver import ConflictAutoResolver

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=ConflictListResponse)
async def list_conflicts(
    types: str | None = Query(
        None, description="Comma-separated conflict types to filter"
    ),
    severities: str | None = Query(
        None, description="Comma-separated severities to filter"
    ),
    statuses: str | None = Query(
        None, description="Comma-separated statuses to filter"
    ),
    person_ids: str | None = Query(
        None, description="Comma-separated person UUIDs to filter"
    ),
    start_date: date | None = Query(
        None, description="Filter conflicts from this date"
    ),
    end_date: date | None = Query(None, description="Filter conflicts up to this date"),
    search: str | None = Query(None, description="Search in conflict description"),
    sort_by: str = Query(
        "detected_at",
        description="Sort field: severity, date, type, status, detected_at",
    ),
    sort_dir: str = Query("desc", description="Sort direction: asc, desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List conflicts with pagination, filtering, and sorting.

    Retrieves conflicts from the ConflictAlert table with support for:
    - Filtering by type, severity, status, affected person, and date range
    - Text search in description
    - Sorting by various fields
    - Pagination

    Args:
        types: Comma-separated list of conflict types
        severities: Comma-separated list of severities (critical, high, medium, low)
        statuses: Comma-separated list of statuses (new, acknowledged, resolved, ignored)
        person_ids: Comma-separated list of person UUIDs
        start_date: Filter conflicts on or after this date
        end_date: Filter conflicts on or before this date
        search: Text to search for in conflict descriptions
        sort_by: Field to sort by
        sort_dir: Sort direction (asc or desc)
        page: Page number (1-based)
        page_size: Number of items per page (max 100)

    Returns:
        ConflictListResponse with paginated conflict items
    """
    # Build base query
    query = select(ConflictAlert)

    # Apply filters
    filters = []

    # Type filter
    if types:
        type_list = [t.strip() for t in types.split(",")]
        # Map frontend types to backend enum values if needed
        filters.append(ConflictAlert.conflict_type.in_(type_list))

    # Severity filter
    if severities:
        severity_list = [s.strip().lower() for s in severities.split(",")]
        filters.append(ConflictAlert.severity.in_(severity_list))

    # Status filter
    if statuses:
        status_list = [s.strip().lower() for s in statuses.split(",")]
        filters.append(ConflictAlert.status.in_(status_list))

    # Person filter
    if person_ids:
        try:
            person_uuid_list = [UUID(p.strip()) for p in person_ids.split(",")]
            filters.append(ConflictAlert.faculty_id.in_(person_uuid_list))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid person_ids format. Must be comma-separated UUIDs.",
            )

    # Date range filter (using fmit_week)
    if start_date:
        filters.append(ConflictAlert.fmit_week >= start_date)
    if end_date:
        filters.append(ConflictAlert.fmit_week <= end_date)

    # Search filter
    if search:
        filters.append(ConflictAlert.description.ilike(f"%{search}%"))

    # Apply all filters
    if filters:
        query = query.where(and_(*filters))

    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = db.execute(count_query)
    total = total_result.scalar_one()

    # Apply sorting
    sort_column = ConflictAlert.created_at  # default
    if sort_by == "severity":
        sort_column = ConflictAlert.severity
    elif sort_by == "date":
        sort_column = ConflictAlert.fmit_week
    elif sort_by == "type":
        sort_column = ConflictAlert.conflict_type
    elif sort_by == "status":
        sort_column = ConflictAlert.status
    elif sort_by == "detected_at":
        sort_column = ConflictAlert.created_at

    if sort_dir.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = db.execute(query)
    conflicts = result.scalars().all()

    # Convert to response schema
    items = []
    for conflict in conflicts:
        # Map ConflictAlert to ConflictResponse format
        items.append(
            ConflictResponse(
                id=conflict.id,
                type=conflict.conflict_type.value
                if hasattr(conflict.conflict_type, "value")
                else str(conflict.conflict_type),
                severity=conflict.severity.value
                if hasattr(conflict.severity, "value")
                else str(conflict.severity),
                status=conflict.status.value
                if hasattr(conflict.status, "value")
                else str(conflict.status),
                title=_get_conflict_title(conflict),
                description=conflict.description or "",
                affected_person_ids=[conflict.faculty_id]
                if conflict.faculty_id
                else [],
                affected_assignment_ids=[],
                affected_block_ids=[],
                conflict_date=conflict.fmit_week,
                conflict_session=None,
                detected_at=conflict.created_at,
                detected_by="system",
                rule_id=None,
                resolved_at=conflict.resolved_at,
                resolved_by=str(conflict.resolved_by_id)
                if conflict.resolved_by_id
                else None,
                resolution_method=None,
                resolution_notes=conflict.resolution_notes,
                details={
                    "leave_id": str(conflict.leave_id) if conflict.leave_id else None,
                    "swap_id": str(conflict.swap_id) if conflict.swap_id else None,
                },
            )
        )

    # Calculate total pages
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ConflictListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


def _get_conflict_title(conflict: ConflictAlert) -> str:
    """Generate a human-readable title for a conflict."""
    conflict_type = (
        conflict.conflict_type.value
        if hasattr(conflict.conflict_type, "value")
        else str(conflict.conflict_type)
    )

    type_titles = {
        "leave_fmit_overlap": "Leave/FMIT Overlap",
        "back_to_back": "Back-to-Back Assignment",
        "excessive_alternating": "Excessive Alternating Pattern",
        "call_cascade": "Call Cascade Issue",
        "external_commitment": "External Commitment Conflict",
        "scheduling_overlap": "Scheduling Overlap",
        "acgme_violation": "ACGME Violation",
        "supervision_missing": "Missing Supervision",
        "capacity_exceeded": "Capacity Exceeded",
        "absence_conflict": "Absence Conflict",
        "qualification_mismatch": "Qualification Mismatch",
        "consecutive_duty": "Consecutive Duty Violation",
        "rest_period": "Rest Period Violation",
        "coverage_gap": "Coverage Gap",
    }

    return type_titles.get(conflict_type, f"Conflict: {conflict_type}")


@router.get("/{conflict_id}/analyze", response_model=ConflictAnalysis)
async def analyze_conflict(
    conflict_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Perform deep analysis of a schedule conflict.

    Returns comprehensive analysis including:
    - Root cause determination
    - Complexity score
    - Safety check results
    - Recommended strategies
    - Estimated resolution time

    Args:
        conflict_id: UUID of the conflict alert to analyze

    Returns:
        ConflictAnalysis with full details
    """
    resolver = ConflictAutoResolver(db)
    try:
        return resolver.analyze_conflict(conflict_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict not found: {str(e)}",
        )
    except (KeyError, AttributeError) as e:
        logger.error(f"Error analyzing conflict {conflict_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing conflict - data integrity issue",
        )


@router.get("/{conflict_id}/options", response_model=list[ResolutionOption])
async def get_resolution_options(
    conflict_id: UUID,
    max_options: int = Query(5, ge=1, le=10, description="Maximum options to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate resolution options for a conflict.

    Returns up to max_options resolution strategies, sorted by overall
    effectiveness score. Each option includes:
    - Strategy type
    - Impact assessment
    - Safety validation status
    - Whether it can be auto-applied

    Args:
        conflict_id: UUID of the conflict to resolve
        max_options: Maximum number of options to generate (1-10)

    Returns:
        List of ResolutionOption objects
    """
    resolver = ConflictAutoResolver(db)
    options = resolver.generate_resolution_options(conflict_id, max_options)

    if not options:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict not found or no resolution options available",
        )

    return options


@router.post("/{conflict_id}/resolve", response_model=ResolutionResult)
async def resolve_conflict(
    conflict_id: UUID,
    strategy: str | None = Query(None, description="Specific strategy to use"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Automatically resolve a conflict if it passes safety checks.

    This endpoint will:
    1. Analyze the conflict
    2. Perform all safety checks
    3. If safe, apply the best resolution strategy
    4. Return the result with details

    If a specific strategy is provided, that strategy will be used.
    Otherwise, the best available strategy is selected automatically.

    Args:
        conflict_id: UUID of the conflict to resolve
        strategy: Optional specific strategy to apply

    Returns:
        ResolutionResult with outcome details
    """
    resolver = ConflictAutoResolver(db)
    return resolver.auto_resolve_if_safe(
        conflict_id=conflict_id,
        strategy=strategy,
        user_id=current_user.id,
    )


@router.post("/batch/resolve", response_model=BatchResolutionReport)
async def batch_resolve_conflicts(
    conflict_ids: list[UUID] | None = Query(
        None, description="Specific conflicts to resolve"
    ),
    max_conflicts: int = Query(
        20, ge=1, le=100, description="Maximum conflicts to process"
    ),
    severity_filter: str | None = Query(
        None, description="Filter by severity: HIGH, MEDIUM, LOW"
    ),
    dry_run: bool = Query(False, description="Simulate without applying changes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Batch auto-resolve multiple conflicts.

    Processes conflicts in priority order (highest severity first) and
    only resolves those that pass all safety checks.

    Args:
        conflict_ids: Optional list of specific conflicts to resolve
        max_conflicts: Maximum number to process (1-100)
        severity_filter: Optional filter by severity level
        dry_run: If True, simulate without making changes

    Returns:
        BatchResolutionReport with summary of all resolutions
    """
    resolver = ConflictAutoResolver(db)
    return resolver.batch_auto_resolve(
        conflict_ids=conflict_ids,
        max_conflicts=max_conflicts,
        severity_filter=severity_filter,
        dry_run=dry_run,
        user_id=current_user.id,
    )


@router.get("/{conflict_id}/can-auto-resolve")
async def can_auto_resolve(
    conflict_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Check if a conflict can be safely auto-resolved.

    Returns a quick check without performing the full resolution.
    Useful for UI to show "Auto-resolve" button enabled/disabled.

    Args:
        conflict_id: UUID of the conflict to check

    Returns:
        Dict with can_auto_resolve boolean and reason
    """
    resolver = ConflictAutoResolver(db)
    try:
        analysis = resolver.analyze_conflict(conflict_id)
        return {
            "conflict_id": conflict_id,
            "can_auto_resolve": analysis.auto_resolution_safe,
            "all_checks_passed": analysis.all_checks_passed,
            "complexity_score": analysis.complexity_score,
            "blockers": analysis.blockers,
            "recommended_strategies": analysis.recommended_strategies,
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conflict not found",
        )
