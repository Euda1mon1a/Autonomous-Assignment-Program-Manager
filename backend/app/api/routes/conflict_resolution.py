"""Conflict Resolution API routes.

Exposes the ConflictAutoResolver service for analyzing and resolving
schedule conflicts with safety checks and impact assessment.
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.conflict_alert import ConflictAlert, ConflictAlertStatus, ConflictSeverity, ConflictType
from app.models.user import User
from app.schemas.conflict_resolution import (
    ConflictAnalysis,
    ResolutionOption,
    ResolutionResult,
    BatchResolutionReport,
)
from app.services.conflict_auto_resolver import ConflictAutoResolver

router = APIRouter()


# ============================================================================
# Schemas for list endpoint
# ============================================================================

class ConflictItem(BaseModel):
    """Schema for a conflict item in the list."""
    id: UUID
    conflict_type: str
    severity: str
    status: str
    description: str
    fmit_week: date
    faculty_id: UUID
    faculty_name: Optional[str] = None
    created_at: str
    acknowledged_at: Optional[str] = None
    resolved_at: Optional[str] = None

    class Config:
        from_attributes = True


class ConflictListResponse(BaseModel):
    """Schema for conflict list response."""
    items: List[ConflictItem]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================================================
# List Endpoint
# ============================================================================

@router.get("", response_model=ConflictListResponse)
def list_conflicts(
    types: Optional[str] = Query(None, description="Comma-separated conflict types"),
    severities: Optional[str] = Query(None, description="Comma-separated severities"),
    statuses: Optional[str] = Query(None, description="Comma-separated statuses"),
    person_ids: Optional[str] = Query(None, description="Comma-separated person IDs"),
    start_date: Optional[date] = Query(None, description="Filter conflicts from this date"),
    end_date: Optional[date] = Query(None, description="Filter conflicts until this date"),
    search: Optional[str] = Query(None, description="Search in description"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_dir: str = Query("desc", description="Sort direction (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List conflict alerts with filtering, sorting, and pagination.

    Returns conflict alerts from the database, supporting various filters
    for status, type, severity, date range, and affected person.
    """
    query = db.query(ConflictAlert).options(joinedload(ConflictAlert.faculty))

    # Apply filters with validation
    if types:
        try:
            type_list = [ConflictType(t.strip()) for t in types.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid conflict type value",
            )
        query = query.filter(ConflictAlert.conflict_type.in_(type_list))

    if severities:
        try:
            severity_list = [ConflictSeverity(s.strip()) for s in severities.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid severity value",
            )
        query = query.filter(ConflictAlert.severity.in_(severity_list))

    if statuses:
        try:
            status_list = [ConflictAlertStatus(s.strip()) for s in statuses.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status value",
            )
        query = query.filter(ConflictAlert.status.in_(status_list))

    if person_ids:
        try:
            person_id_list = [UUID(p.strip()) for p in person_ids.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid person_ids UUID value",
            )
        query = query.filter(ConflictAlert.faculty_id.in_(person_id_list))

    if start_date:
        query = query.filter(ConflictAlert.fmit_week >= start_date)

    if end_date:
        query = query.filter(ConflictAlert.fmit_week <= end_date)

    if search:
        query = query.filter(ConflictAlert.description.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Apply sorting (whitelist allowed fields)
    sortable_fields = {
        "created_at": ConflictAlert.created_at,
        "fmit_week": ConflictAlert.fmit_week,
        "severity": ConflictAlert.severity,
        "status": ConflictAlert.status,
    }
    sort_column = sortable_fields.get(sort_by, ConflictAlert.created_at)
    if sort_dir.lower() == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Apply pagination
    offset = (page - 1) * page_size
    conflicts = query.offset(offset).limit(page_size).all()

    # Convert to response items
    items = []
    for conflict in conflicts:
        items.append(ConflictItem(
            id=conflict.id,
            conflict_type=conflict.conflict_type.value if conflict.conflict_type else "unknown",
            severity=conflict.severity.value if conflict.severity else "warning",
            status=conflict.status.value if conflict.status else "new",
            description=conflict.description or "",
            fmit_week=conflict.fmit_week,
            faculty_id=conflict.faculty_id,
            faculty_name=conflict.faculty.name if conflict.faculty else None,
            created_at=conflict.created_at.isoformat() if conflict.created_at else "",
            acknowledged_at=conflict.acknowledged_at.isoformat() if conflict.acknowledged_at else None,
            resolved_at=conflict.resolved_at.isoformat() if conflict.resolved_at else None,
        ))

    # Calculate pages
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return ConflictListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{conflict_id}/analyze", response_model=ConflictAnalysis)
def analyze_conflict(
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
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing conflict",
        )


@router.get("/{conflict_id}/options", response_model=list[ResolutionOption])
def get_resolution_options(
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
def resolve_conflict(
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
def batch_resolve_conflicts(
    conflict_ids: list[UUID] | None = Query(None, description="Specific conflicts to resolve"),
    max_conflicts: int = Query(20, ge=1, le=100, description="Maximum conflicts to process"),
    severity_filter: str | None = Query(None, description="Filter by severity: HIGH, MEDIUM, LOW"),
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
def can_auto_resolve(
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
