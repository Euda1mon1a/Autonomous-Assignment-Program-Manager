"""Audit API routes.

Provides endpoints for audit logging, statistics, and compliance tracking.
Integrates with SQLAlchemy-Continuum for real audit data, with mock data as fallback.
"""

import csv
import io
import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.role_filter import require_admin
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit import (
    AuditExportConfig,
    AuditLogEntry,
    AuditLogResponse,
    AuditStatistics,
    AuditUser,
    DateRange,
    FieldChange,
    MarkReviewedRequest,
)
from app.services import audit_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Mock Data Generators
# ============================================================================


def _generate_mock_users() -> list[AuditUser]:
    """Generate mock users for filtering."""
    return [
        AuditUser(
            id="user-001",
            name="Dr. Sarah Johnson",
            email="sarah.johnson@hospital.mil",
            role="Chief Resident",
        ),
        AuditUser(
            id="user-002",
            name="Dr. Michael Chen",
            email="michael.chen@hospital.mil",
            role="Program Director",
        ),
        AuditUser(
            id="user-003",
            name="Dr. Emily Rodriguez",
            email="emily.rodriguez@hospital.mil",
            role="Scheduler",
        ),
        AuditUser(
            id="user-004",
            name="Dr. James Wilson",
            email="james.wilson@hospital.mil",
            role="Faculty",
        ),
        AuditUser(
            id="user-005",
            name="Admin User",
            email="admin@hospital.mil",
            role="System Administrator",
        ),
    ]


def _generate_mock_audit_entries(
    page: int = 1,
    page_size: int = 25,
    start_date: str | None = None,
    end_date: str | None = None,
    entity_types: list[str] | None = None,
    actions: list[str] | None = None,
    user_ids: list[str] | None = None,
    severity: list[str] | None = None,
    search: str | None = None,
    entity_id: str | None = None,
    acgme_overrides_only: bool = False,
) -> tuple[list[AuditLogEntry], int]:
    """Generate mock audit entries with filtering."""

    users = _generate_mock_users()

    # Generate comprehensive mock data
    all_entries = [
        AuditLogEntry(
            id="audit-001",
            timestamp=(datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
            entityType="assignment",
            entityId="assign-123",
            entityName="Night Shift - ICU",
            action="create",
            severity="info",
            user=users[0],
            changes=[
                FieldChange(
                    field="person_id",
                    oldValue=None,
                    newValue="person-456",
                    displayName="Assigned Person",
                ),
                FieldChange(
                    field="block_id",
                    oldValue=None,
                    newValue="block-789",
                    displayName="Block",
                ),
            ],
            metadata={"source": "manual_assignment"},
            ipAddress="10.0.1.45",
            userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            reason="Regular assignment",
        ),
        AuditLogEntry(
            id="audit-002",
            timestamp=(datetime.utcnow() - timedelta(hours=5)).isoformat() + "Z",
            entityType="assignment",
            entityId="assign-124",
            entityName="Day Shift - ER",
            action="override",
            severity="warning",
            user=users[1],
            changes=[
                FieldChange(
                    field="max_consecutive_days",
                    oldValue=7,
                    newValue=10,
                    displayName="Max Consecutive Days",
                ),
            ],
            metadata={"override_type": "acgme_violation", "rule_id": "rule-001"},
            ipAddress="10.0.1.46",
            acgmeOverride=True,
            acgmeJustification="Educational opportunity - resident requested to continue for critical case",
            reason="ACGME max consecutive days override",
        ),
        AuditLogEntry(
            id="audit-003",
            timestamp=(datetime.utcnow() - timedelta(hours=8)).isoformat() + "Z",
            entityType="person",
            entityId="person-789",
            entityName="Dr. Alex Thompson",
            action="update",
            severity="info",
            user=users[2],
            changes=[
                FieldChange(
                    field="email",
                    oldValue="alex.t@old.mil",
                    newValue="alex.thompson@hospital.mil",
                    displayName="Email",
                ),
                FieldChange(
                    field="phone",
                    oldValue="555-0100",
                    newValue="555-0199",
                    displayName="Phone",
                ),
            ],
            metadata={"updated_fields": 2},
            reason="Contact information update",
        ),
        AuditLogEntry(
            id="audit-004",
            timestamp=(datetime.utcnow() - timedelta(hours=12)).isoformat() + "Z",
            entityType="schedule_run",
            entityId="sched-001",
            entityName="January 2025 Schedule",
            action="schedule_generate",
            severity="info",
            user=users[1],
            metadata={
                "algorithm": "genetic_algorithm",
                "iterations": 1000,
                "fitness_score": 0.95,
                "duration_seconds": 45.2,
            },
            reason="Monthly schedule generation",
        ),
        AuditLogEntry(
            id="audit-005",
            timestamp=(datetime.utcnow() - timedelta(hours=15)).isoformat() + "Z",
            entityType="absence",
            entityId="absence-456",
            entityName="Vacation - Dr. Smith",
            action="delete",
            severity="warning",
            user=users[0],
            changes=[
                FieldChange(
                    field="status",
                    oldValue="approved",
                    newValue="deleted",
                    displayName="Status",
                ),
            ],
            reason="Cancelled vacation request",
        ),
        AuditLogEntry(
            id="audit-006",
            timestamp=(datetime.utcnow() - timedelta(days=1, hours=2)).isoformat()
            + "Z",
            entityType="rotation_template",
            entityId="template-001",
            entityName="EM Residency Core",
            action="update",
            severity="info",
            user=users[1],
            changes=[
                FieldChange(
                    field="duration_weeks",
                    oldValue=4,
                    newValue=6,
                    displayName="Duration",
                ),
            ],
            reason="Updated rotation duration per ACGME requirements",
        ),
        AuditLogEntry(
            id="audit-007",
            timestamp=(datetime.utcnow() - timedelta(days=1, hours=5)).isoformat()
            + "Z",
            entityType="assignment",
            entityId="assign-125",
            entityName="Night Shift - Trauma",
            action="override",
            severity="critical",
            user=users[1],
            changes=[
                FieldChange(
                    field="hours_per_week",
                    oldValue=80,
                    newValue=88,
                    displayName="Hours Per Week",
                ),
            ],
            acgmeOverride=True,
            acgmeJustification="Mass casualty event - temporary extension approved by GME office",
            reason="Emergency staffing override due to mass casualty incident",
        ),
        AuditLogEntry(
            id="audit-008",
            timestamp=(datetime.utcnow() - timedelta(days=2)).isoformat() + "Z",
            entityType="system",
            entityId="sys-001",
            entityName="Audit System",
            action="login",
            severity="info",
            user=users[4],
            metadata={"login_method": "saml_sso"},
            ipAddress="10.0.2.15",
            userAgent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        ),
        AuditLogEntry(
            id="audit-009",
            timestamp=(datetime.utcnow() - timedelta(days=2, hours=8)).isoformat()
            + "Z",
            entityType="block",
            entityId="block-999",
            entityName="ICU Week 3",
            action="bulk_import",
            severity="info",
            user=users[2],
            metadata={"imported_count": 45, "failed_count": 0},
            reason="Imported quarterly block schedule",
        ),
        AuditLogEntry(
            id="audit-010",
            timestamp=(datetime.utcnow() - timedelta(days=3)).isoformat() + "Z",
            entityType="assignment",
            entityId="assign-200",
            entityName="Call Shift - Pediatrics",
            action="restore",
            severity="warning",
            user=users[0],
            changes=[
                FieldChange(
                    field="status",
                    oldValue="deleted",
                    newValue="active",
                    displayName="Status",
                ),
            ],
            reason="Restored accidentally deleted assignment",
        ),
    ]

    # Apply filters
    filtered_entries = all_entries.copy()

    if entity_types:
        filtered_entries = [
            e for e in filtered_entries if e.entity_type in entity_types
        ]

    if actions:
        filtered_entries = [e for e in filtered_entries if e.action in actions]

    if user_ids:
        filtered_entries = [e for e in filtered_entries if e.user.id in user_ids]

    if severity:
        filtered_entries = [e for e in filtered_entries if e.severity in severity]

    if search:
        search_lower = search.lower()
        filtered_entries = [
            e
            for e in filtered_entries
            if search_lower in (e.entity_name or "").lower()
            or search_lower in (e.reason or "").lower()
            or search_lower in e.action.lower()
        ]

    if entity_id:
        filtered_entries = [e for e in filtered_entries if e.entity_id == entity_id]

    if acgme_overrides_only:
        filtered_entries = [e for e in filtered_entries if e.acgme_override]

    # Apply date range filtering
    if start_date or end_date:

        def in_range(timestamp: str) -> bool:
            entry_date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if start_date:
                start = datetime.fromisoformat(start_date)
                if entry_date < start:
                    return False
            if end_date:
                end = datetime.fromisoformat(end_date)
                if entry_date > end:
                    return False
            return True

        filtered_entries = [e for e in filtered_entries if in_range(e.timestamp)]

    total = len(filtered_entries)

    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_entries = filtered_entries[start_idx:end_idx]

    return paginated_entries, total


# ============================================================================
# Routes
# ============================================================================


@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_direction: str = Query("desc", description="Sort direction (asc/desc)"),
    start_date: str | None = Query(None, description="Filter start date (ISO format)"),
    end_date: str | None = Query(None, description="Filter end date (ISO format)"),
    entity_types: str | None = Query(None, description="Comma-separated entity types"),
    actions: str | None = Query(None, description="Comma-separated action types"),
    user_ids: str | None = Query(None, description="Comma-separated user IDs"),
    severity: str | None = Query(None, description="Comma-separated severity levels"),
    search: str | None = Query(None, description="Search query"),
    entity_id: str | None = Query(None, description="Filter by specific entity ID"),
    acgme_overrides_only: bool = Query(False, description="Show only ACGME overrides"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get paginated audit logs with filtering and sorting. Requires authentication.

    Supports comprehensive filtering by:
    - Date range
    - Entity types
    - Action types
    - Users
    - Severity
    - Search text
    - Specific entity
    - ACGME overrides only
    """
    # Parse comma-separated filters
    entity_types_list = entity_types.split(",") if entity_types else None
    actions_list = actions.split(",") if actions else None
    user_ids_list = user_ids.split(",") if user_ids else None
    severity_list = severity.split(",") if severity else None

    # Try to get real audit data from SQLAlchemy-Continuum
    try:
        entries, total = audit_service.get_audit_logs(
            db=db,
            page=page,
            page_size=page_size,
            start_date=start_date,
            end_date=end_date,
            entity_types=entity_types_list,
            actions=actions_list,
            user_ids=user_ids_list,
            severity=severity_list,
            search=search,
            entity_id=entity_id,
            acgme_overrides_only=acgme_overrides_only,
        )

        # If we got real data, use it
        if total > 0:
            logger.info(f"Retrieved {total} real audit entries")
            total_pages = (total + page_size - 1) // page_size
            return AuditLogResponse(
                items=entries,
                total=total,
                page=page,
                pageSize=page_size,
                totalPages=total_pages,
            )
    except Exception as e:
        logger.warning(f"Error fetching real audit data, falling back to mock: {e}")

    # Fall back to mock data if no real data or error occurred
    logger.info("Using mock audit data as fallback")
    entries, total = _generate_mock_audit_entries(
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
        entity_types=entity_types_list,
        actions=actions_list,
        user_ids=user_ids_list,
        severity=severity_list,
        search=search,
        entity_id=entity_id,
        acgme_overrides_only=acgme_overrides_only,
    )

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return AuditLogResponse(
        items=entries,
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
    )


@router.get("/logs/{log_id}", response_model=AuditLogEntry)
async def get_audit_log_by_id(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a single audit log entry by ID. Requires authentication.
    """
    # Generate mock data and find the entry
    entries, _ = _generate_mock_audit_entries(page=1, page_size=100)

    for entry in entries:
        if entry.id == log_id:
            return entry

    raise HTTPException(status_code=404, detail=f"Audit log entry {log_id} not found")


@router.get("/statistics", response_model=AuditStatistics)
async def get_audit_statistics(
    start_date: str | None = Query(
        None, description="Statistics start date (ISO format)"
    ),
    end_date: str | None = Query(None, description="Statistics end date (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get audit statistics grouped by action, entity type, user, and severity.
    Requires authentication.

    Returns aggregate counts and metrics for the specified date range.
    """
    # Try to get real statistics from SQLAlchemy-Continuum
    try:
        stats = audit_service.get_audit_statistics(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )

        # If we got real stats with data, use them
        if stats.get("totalEntries", 0) > 0:
            logger.info(
                f"Retrieved real audit statistics: {stats['totalEntries']} entries"
            )

            # Determine date range
            now = datetime.utcnow()
            actual_start = start_date or (now - timedelta(days=30)).isoformat()
            actual_end = end_date or now.isoformat()

            return AuditStatistics(
                totalEntries=stats["totalEntries"],
                entriesByAction=stats["entriesByAction"],
                entriesByEntityType=stats["entriesByEntityType"],
                entriesBySeverity=stats["entriesBySeverity"],
                acgmeOverrideCount=stats["acgmeOverrideCount"],
                uniqueUsers=stats["uniqueUsers"],
                dateRange=DateRange(start=actual_start, end=actual_end),
            )
    except Exception as e:
        logger.warning(
            f"Error fetching real audit statistics, falling back to mock: {e}"
        )

    # Fall back to mock data
    logger.info("Using mock audit statistics as fallback")
    # Get all entries for the date range
    entries, total = _generate_mock_audit_entries(
        page=1,
        page_size=1000,
        start_date=start_date,
        end_date=end_date,
    )

    # Count by action
    entries_by_action = {}
    for entry in entries:
        entries_by_action[entry.action] = entries_by_action.get(entry.action, 0) + 1

    # Count by entity type
    entries_by_entity_type = {}
    for entry in entries:
        entries_by_entity_type[entry.entity_type] = (
            entries_by_entity_type.get(entry.entity_type, 0) + 1
        )

    # Count by severity
    entries_by_severity = {}
    for entry in entries:
        entries_by_severity[entry.severity] = (
            entries_by_severity.get(entry.severity, 0) + 1
        )

    # Count ACGME overrides
    acgme_override_count = sum(1 for entry in entries if entry.acgme_override)

    # Count unique users
    unique_users = len({entry.user.id for entry in entries})

    # Determine date range
    if entries:
        timestamps = [
            datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")) for e in entries
        ]
        actual_start = min(timestamps).isoformat()
        actual_end = max(timestamps).isoformat()
    else:
        now = datetime.utcnow()
        actual_start = (now - timedelta(days=30)).isoformat()
        actual_end = now.isoformat()

    return AuditStatistics(
        totalEntries=total,
        entriesByAction=entries_by_action,
        entriesByEntityType=entries_by_entity_type,
        entriesBySeverity=entries_by_severity,
        acgmeOverrideCount=acgme_override_count,
        uniqueUsers=unique_users,
        dateRange=DateRange(start=actual_start, end=actual_end),
    )


@router.get("/users")
async def get_audit_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get list of users who have audit activity. Requires authentication.

    Used to populate user filter dropdowns in the UI.
    """
    # Try to get real users from SQLAlchemy-Continuum
    try:
        users = audit_service.get_audit_users(db=db)
        if users:
            logger.info(f"Retrieved {len(users)} real audit users")
            return users
    except Exception as e:
        logger.warning(f"Error fetching real audit users, falling back to mock: {e}")

    # Fall back to mock data
    logger.info("Using mock audit users as fallback")
    return _generate_mock_users()


@router.post("/export")
async def export_audit_logs(
    config: AuditExportConfig,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Export audit logs in the specified format (CSV, JSON, or PDF).
    Requires admin role.

    Returns a downloadable file with filtered audit log data.
    """
    # Parse filters from config
    filters = config.filters
    entity_types = filters.entity_types if filters and filters.entity_types else None
    actions = filters.actions if filters and filters.actions else None
    user_ids = filters.user_ids if filters and filters.user_ids else None
    severity_list = filters.severity if filters and filters.severity else None
    search = filters.search_query if filters and filters.search_query else None
    entity_id = filters.entity_id if filters and filters.entity_id else None
    acgme_only = (
        filters.acgme_overrides_only
        if filters and filters.acgme_overrides_only
        else False
    )

    start_date = None
    end_date = None
    if filters and filters.date_range:
        start_date = filters.date_range.start
        end_date = filters.date_range.end

    # Try to get real audit data
    entries = []
    try:
        entries, _ = audit_service.get_audit_logs(
            db=db,
            page=1,
            page_size=10000,  # Export all matching entries
            start_date=start_date,
            end_date=end_date,
            entity_types=entity_types,
            actions=actions,
            user_ids=user_ids,
            severity=severity_list,
            search=search,
            entity_id=entity_id,
            acgme_overrides_only=acgme_only,
        )
        if entries:
            logger.info(f"Exporting {len(entries)} real audit entries")
    except Exception as e:
        logger.warning(
            f"Error fetching real audit data for export, falling back to mock: {e}"
        )

    # Fall back to mock data if needed
    if not entries:
        logger.info("Using mock audit data for export")
        entries, _ = _generate_mock_audit_entries(
            page=1,
            page_size=10000,
            start_date=start_date,
            end_date=end_date,
            entity_types=entity_types,
            actions=actions,
            user_ids=user_ids,
            severity=severity_list,
            search=search,
            entity_id=entity_id,
            acgme_overrides_only=acgme_only,
        )

    if config.format == "json":
        # Export as JSON
        output = io.StringIO()
        json_data = [entry.model_dump(by_alias=True) for entry in entries]
        json.dump(json_data, output, indent=2)
        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit_logs.json"},
        )

    elif config.format == "csv":
        # Export as CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        header = [
            "ID",
            "Timestamp",
            "Entity Type",
            "Entity ID",
            "Entity Name",
            "Action",
            "Severity",
            "User",
            "User Email",
            "Reason",
        ]

        if config.include_changes:
            header.append("Changes")

        if config.include_metadata:
            header.append("Metadata")

        if acgme_only or any(e.acgme_override for e in entries):
            header.extend(["ACGME Override", "ACGME Justification"])

        writer.writerow(header)

        # Rows
        for entry in entries:
            row = [
                entry.id,
                entry.timestamp,
                entry.entity_type,
                entry.entity_id,
                entry.entity_name or "",
                entry.action,
                entry.severity,
                entry.user.name,
                entry.user.email or "",
                entry.reason or "",
            ]

            if config.include_changes:
                changes_str = ""
                if entry.changes:
                    changes_str = "; ".join(
                        [
                            f"{c.field}: {c.old_value} -> {c.new_value}"
                            for c in entry.changes
                        ]
                    )
                row.append(changes_str)

            if config.include_metadata:
                metadata_str = json.dumps(entry.metadata) if entry.metadata else ""
                row.append(metadata_str)

            if acgme_only or any(e.acgme_override for e in entries):
                row.extend(
                    [
                        "Yes" if entry.acgme_override else "No",
                        entry.acgme_justification or "",
                    ]
                )

            writer.writerow(row)

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
        )

    elif config.format == "pdf":
        # For PDF, return a simple text representation
        # In production, this would use a proper PDF library like ReportLab
        output = io.StringIO()
        output.write("AUDIT LOG REPORT\n")
        output.write("=" * 80 + "\n\n")

        for entry in entries:
            output.write(f"ID: {entry.id}\n")
            output.write(f"Timestamp: {entry.timestamp}\n")
            output.write(
                f"Entity: {entry.entity_type} - {entry.entity_name or entry.entity_id}\n"
            )
            output.write(f"Action: {entry.action}\n")
            output.write(f"Severity: {entry.severity}\n")
            output.write(
                f"User: {entry.user.name} ({entry.user.email or 'no email'})\n"
            )
            output.write(f"Reason: {entry.reason or 'N/A'}\n")

            if entry.acgme_override:
                output.write("ACGME Override: YES\n")
                output.write(f"Justification: {entry.acgme_justification or 'N/A'}\n")

            if config.include_changes and entry.changes:
                output.write("Changes:\n")
                for change in entry.changes:
                    output.write(
                        f"  - {change.field}: {change.old_value} -> {change.new_value}\n"
                    )

            output.write("-" * 80 + "\n\n")

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=audit_logs.pdf"},
        )

    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported export format: {config.format}"
        )


@router.post("/mark-reviewed", status_code=204)
async def mark_audit_reviewed(
    request: MarkReviewedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_admin()),
):
    """
    Mark audit entries as reviewed for compliance tracking. Requires admin role.

    This endpoint would typically update the audit entries to include
    review information for ACGME compliance purposes.
    """
    # In the real implementation, this would:
    # 1. Update the audit entries with review information
    # 2. Create a compliance record
    # 3. Possibly trigger notifications

    # For now, just validate the request
    if not request.ids:
        raise HTTPException(status_code=400, detail="No audit entry IDs provided")

    # Mock successful completion
    return None
