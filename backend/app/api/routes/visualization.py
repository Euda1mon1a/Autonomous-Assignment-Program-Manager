"""Visualization API routes for heatmap generation.

Provides endpoints for generating schedule heatmaps, coverage analysis,
and workload visualization.
"""

import io
import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.visualization import (
    CoverageHeatmapResponse,
    ExportRequest,
    HeatmapResponse,
    UnifiedHeatmapRequest,
)
from app.services.cached_schedule_service import CachedHeatmapService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_unified_heatmap(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    person_ids: list[UUID] | None = Query(None, description="Filter by person IDs"),
    rotation_ids: list[UUID] | None = Query(
        None, description="Filter by rotation template IDs"
    ),
    include_fmit: bool = Query(True, description="Include FMIT swap data"),
    group_by: str = Query(
        "person", description="Group by 'person', 'rotation', 'daily', or 'weekly'"
    ),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HeatmapResponse:
    """
    Generate unified heatmap showing both residency and FMIT schedules.

    Returns heatmap data as JSON suitable for frontend Plotly rendering.

    Args:
        start_date: Start date for heatmap
        end_date: End date for heatmap
        person_ids: Optional list of person IDs to filter
        rotation_ids: Optional list of rotation template IDs to filter
        include_fmit: Whether to include FMIT swap data
        group_by: Group heatmap by 'person', 'rotation', 'daily', or 'weekly'

    Returns:
        HeatmapResponse with visualization data
    """
    group_by_lower = group_by.lower()
    if group_by_lower not in ["person", "rotation", "daily", "weekly"]:
        raise HTTPException(
            status_code=400,
            detail="group_by must be 'person', 'rotation', 'daily', or 'weekly'",
        )

    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date must be before or equal to end_date"
        )

    # Use cached service for better performance
    service = CachedHeatmapService()
    return service.generate_unified_heatmap(
        db=db,
        start_date=start_date,
        end_date=end_date,
        person_ids=person_ids,
        rotation_ids=rotation_ids,
        include_fmit=include_fmit,
        group_by=group_by_lower,
    )


@router.post("/heatmap/unified", response_model=HeatmapResponse)
async def get_unified_heatmap_with_time_range(
    request: UnifiedHeatmapRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HeatmapResponse:
    """
    Generate unified heatmap with convenient time range specification.

    This endpoint provides an easier way to specify time ranges using
    predefined periods (week, month, quarter) instead of exact dates.
    Combines both residency and FMIT schedule data.

    Args:
        request: UnifiedHeatmapRequest with time range and filter options

    Returns:
        HeatmapResponse with visualization data

    Raises:
        HTTPException: If time range specification is invalid
    """
    group_by_lower = request.group_by.lower()
    if group_by_lower not in ["person", "rotation", "daily", "weekly"]:
        raise HTTPException(
            status_code=400,
            detail="group_by must be 'person', 'rotation', 'daily', or 'weekly'",
        )

    # Use cached service for better performance
    service = CachedHeatmapService()

    # Calculate date range from time_range specification
    try:
        start_date, end_date = service.calculate_date_range(request.time_range)
    except ValueError as e:
        logger.error(f"Invalid visualization parameters: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid request parameters")

    # Generate unified heatmap (cached)
    result = service.generate_unified_heatmap(
        db=db,
        start_date=start_date,
        end_date=end_date,
        person_ids=request.person_ids,
        rotation_ids=request.rotation_ids,
        include_fmit=request.include_fmit,
        group_by=group_by_lower,
    )

    # Add calculated date range to metadata
    if result.metadata is None:
        result.metadata = {}
    result.metadata["time_range_type"] = request.time_range.range_type
    result.metadata["calculated_start_date"] = start_date.isoformat()
    result.metadata["calculated_end_date"] = end_date.isoformat()

    return result


@router.get("/heatmap/image")
async def get_heatmap_image(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    person_ids: list[UUID] | None = Query(None, description="Filter by person IDs"),
    rotation_ids: list[UUID] | None = Query(
        None, description="Filter by rotation template IDs"
    ),
    include_fmit: bool = Query(True, description="Include FMIT swap data"),
    group_by: str = Query(
        "person", description="Group by 'person', 'rotation', 'daily', or 'weekly'"
    ),
    format: str = Query("png", description="Export format: png, pdf, or svg"),
    width: int = Query(1200, description="Width in pixels", gt=0),
    height: int = Query(800, description="Height in pixels", gt=0),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Generate unified heatmap and export as image.

    Returns the heatmap as a PNG, PDF, or SVG image file.

    Args:
        start_date: Start date for heatmap
        end_date: End date for heatmap
        person_ids: Optional list of person IDs to filter
        rotation_ids: Optional list of rotation template IDs to filter
        include_fmit: Whether to include FMIT swap data
        group_by: Group heatmap by 'person', 'rotation', 'daily', or 'weekly'
        format: Export format (png, pdf, svg)
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Image file as streaming response
    """
    if format not in ["png", "pdf", "svg"]:
        raise HTTPException(
            status_code=400, detail="format must be 'png', 'pdf', or 'svg'"
        )

    group_by_lower = group_by.lower()
    if group_by_lower not in ["person", "rotation", "daily", "weekly"]:
        raise HTTPException(
            status_code=400,
            detail="group_by must be 'person', 'rotation', 'daily', or 'weekly'",
        )

    # Use cached service for better performance
    service = CachedHeatmapService()

    # Generate heatmap data (cached)
    heatmap_response = service.generate_unified_heatmap(
        db=db,
        start_date=start_date,
        end_date=end_date,
        person_ids=person_ids,
        rotation_ids=rotation_ids,
        include_fmit=include_fmit,
        group_by=group_by_lower,
    )

    # Export as image
    try:
        image_bytes = service.export_heatmap_image(
            data=heatmap_response.data,
            title=heatmap_response.title,
            format=format,
            width=width,
            height=height,
        )
    except Exception as e:
        logger.error(f"Error generating visualization image: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred generating the image"
        )

    # Determine media type
    media_types = {
        "png": "image/png",
        "pdf": "application/pdf",
        "svg": "image/svg+xml",
    }
    media_type = media_types.get(format, "application/octet-stream")

    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=heatmap.{format}"},
    )


@router.get("/coverage", response_model=CoverageHeatmapResponse)
async def get_coverage_heatmap(
    start_date: date = Query(..., description="Start date for coverage analysis"),
    end_date: date = Query(..., description="End date for coverage analysis"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CoverageHeatmapResponse:
    """
    Generate coverage heatmap showing staffing levels per rotation.

    Analyzes schedule coverage and identifies gaps.

    Args:
        start_date: Start date for analysis
        end_date: End date for analysis

    Returns:
        CoverageHeatmapResponse with coverage data and identified gaps
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date must be before or equal to end_date"
        )

    # Use cached service for better performance
    service = CachedHeatmapService()
    return service.generate_coverage_heatmap(
        db=db, start_date=start_date, end_date=end_date
    )


@router.get("/workload", response_model=HeatmapResponse)
async def get_workload_heatmap(
    person_ids: list[UUID] = Query(..., description="Person IDs for workload analysis"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    include_weekends: bool = Query(False, description="Include weekends in analysis"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HeatmapResponse:
    """
    Generate workload heatmap for specific people.

    Shows daily workload distribution for selected staff members.

    Args:
        person_ids: List of person IDs to analyze
        start_date: Start date
        end_date: End date
        include_weekends: Whether to include weekends

    Returns:
        HeatmapResponse with workload data
    """
    if not person_ids:
        raise HTTPException(status_code=400, detail="At least one person_id required")

    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date must be before or equal to end_date"
        )

    # Use cached service for better performance
    service = CachedHeatmapService()
    return service.generate_person_workload_heatmap(
        db=db,
        person_ids=person_ids,
        start_date=start_date,
        end_date=end_date,
        include_weekends=include_weekends,
    )


@router.post("/export")
async def export_heatmap(
    request: ExportRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    Export heatmap with custom options.

    Generates and exports a heatmap based on the specified type and parameters.

    Args:
        request: Export request with heatmap type and parameters

    Returns:
        Image file as streaming response
    """
    if request.format not in ["png", "pdf", "svg"]:
        raise HTTPException(
            status_code=400, detail="format must be 'png', 'pdf', or 'svg'"
        )

    if request.heatmap_type not in ["unified", "coverage", "workload"]:
        raise HTTPException(
            status_code=400,
            detail="heatmap_type must be 'unified', 'coverage', or 'workload'",
        )

    # Use cached service for better performance
    service = CachedHeatmapService()

    # Generate appropriate heatmap based on type (cached)
    try:
        if request.heatmap_type == "unified":
            params = request.request_params
            heatmap_response = service.generate_unified_heatmap(
                db=db,
                start_date=date.fromisoformat(params["start_date"]),
                end_date=date.fromisoformat(params["end_date"]),
                person_ids=params.get("person_ids"),
                rotation_ids=params.get("rotation_ids"),
                include_fmit=params.get("include_fmit", True),
                group_by=params.get("group_by", "person"),
            )
        elif request.heatmap_type == "coverage":
            params = request.request_params
            heatmap_response = service.generate_coverage_heatmap(
                db=db,
                start_date=date.fromisoformat(params["start_date"]),
                end_date=date.fromisoformat(params["end_date"]),
            )
        else:  # workload
            params = request.request_params
            heatmap_response = service.generate_person_workload_heatmap(
                db=db,
                person_ids=[UUID(pid) for pid in params["person_ids"]],
                start_date=date.fromisoformat(params["start_date"]),
                end_date=date.fromisoformat(params["end_date"]),
                include_weekends=params.get("include_weekends", False),
            )
    except Exception as e:
        logger.error(f"Invalid export request parameters: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid request parameters")

    # Export as image
    try:
        image_bytes = service.export_heatmap_image(
            data=heatmap_response.data,
            title=heatmap_response.title,
            format=request.format,
            width=request.width,
            height=request.height,
        )
    except Exception as e:
        logger.error(f"Error generating visualization image: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred generating the image"
        )

    # Determine media type
    media_types = {
        "png": "image/png",
        "pdf": "application/pdf",
        "svg": "image/svg+xml",
    }
    media_type = media_types.get(request.format, "application/octet-stream")

    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={request.heatmap_type}_heatmap.{request.format}"
        },
    )


# =============================================================================
# 3D Voxel Visualization Endpoints (Novel)
# =============================================================================


@router.get("/voxel-grid")
async def get_3d_voxel_grid(
    start_date: date = Query(..., description="Start date for voxel grid"),
    end_date: date = Query(..., description="End date for voxel grid"),
    person_ids: list[UUID] | None = Query(None, description="Filter by person IDs"),
    activity_types: list[str] | None = Query(
        None, description="Filter by activity types"
    ),
    include_violations: bool = Query(True, description="Include ACGME violation data"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Generate 3D voxel grid representation of schedule data.

    This is a novel visualization approach that represents the schedule as
    a 3D space where:
    - X-axis: Time (blocks/dates)
    - Y-axis: People (residents, faculty)
    - Z-axis: Activity type (clinic, inpatient, procedures, etc.)

    Each voxel represents an assignment with properties:
    - Position (x, y, z) in the 3D grid
    - Color based on activity type or compliance status
    - Opacity based on confidence score
    - State flags (occupied, conflict, violation)

    This enables spatial reasoning about:
    - Collision detection = double-booking (same x,y position)
    - Empty space = coverage gaps
    - Layer analysis = supervision compliance
    - Volume distribution = workload balance

    Args:
        start_date: Start date for visualization
        end_date: End date for visualization
        person_ids: Optional filter for specific people
        activity_types: Optional filter for specific activity types
        include_violations: Whether to include ACGME violation markers

    Returns:
        3D voxel grid data structure ready for Three.js rendering
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.assignment import Assignment
    from app.models.block import Block
    from app.models.person import Person
    from app.visualization import transform_schedule_to_voxels

    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date must be before or equal to end_date"
        )

    # Fetch blocks in date range
    blocks_query = (
        select(Block)
        .where(
            Block.date >= start_date,
            Block.date <= end_date,
        )
        .order_by(Block.date, Block.time_of_day)
    )

    blocks_result = db.execute(blocks_query)
    blocks = blocks_result.scalars().all()

    if not blocks:
        return {
            "dimensions": {"x_size": 0, "y_size": 0, "z_size": 0},
            "voxels": [],
            "statistics": {"total_assignments": 0},
            "error": "No blocks found in date range",
        }

    block_ids = [b.id for b in blocks]
    blocks_data = [
        {"id": str(b.id), "date": b.date.isoformat(), "time_of_day": b.time_of_day}
        for b in blocks
    ]

    # Fetch persons (optionally filtered)
    persons_query = select(Person)
    if person_ids:
        persons_query = persons_query.where(Person.id.in_(person_ids))
    persons_query = persons_query.order_by(
        Person.type.desc(), Person.pgy_level, Person.name
    )

    persons_result = db.execute(persons_query)
    persons = persons_result.scalars().all()

    if not persons:
        return {
            "dimensions": {"x_size": len(blocks), "y_size": 0, "z_size": 0},
            "voxels": [],
            "statistics": {"total_assignments": 0},
            "error": "No persons found",
        }

    person_ids_list = [p.id for p in persons]
    persons_data = [
        {
            "id": str(p.id),
            "name": p.name,
            "type": p.type,
            "pgy_level": p.pgy_level,
        }
        for p in persons
    ]

    # Fetch assignments with related data
    assignments_query = (
        select(Assignment)
        .options(selectinload(Assignment.rotation_template))
        .where(
            Assignment.block_id.in_(block_ids),
            Assignment.person_id.in_(person_ids_list),
        )
    )

    assignments_result = db.execute(assignments_query)
    assignments = assignments_result.scalars().all()

    # Convert to dict format for transformer
    assignments_data = []
    for a in assignments:
        activity_type = "unknown"
        activity_name = "Unknown"

        if a.rotation_template:
            activity_type = a.rotation_template.activity_type or "unknown"
            activity_name = a.rotation_template.name
        elif a.activity_override:
            activity_name = a.activity_override
            # Try to infer activity type from override name
            override_lower = a.activity_override.lower()
            if "clinic" in override_lower:
                activity_type = "clinic"
            elif "inpatient" in override_lower or "ward" in override_lower:
                activity_type = "inpatient"
            elif "proc" in override_lower:
                activity_type = "procedure"
            elif "call" in override_lower:
                activity_type = "call"
            elif "leave" in override_lower or "off" in override_lower:
                activity_type = "leave"

        # Filter by activity type if specified
        if activity_types and activity_type not in activity_types:
            continue

        # Find person name
        person_name = next((p.name for p in persons if p.id == a.person_id), "Unknown")

        assignment_dict = {
            "id": str(a.id),
            "person_id": str(a.person_id),
            "person_name": person_name,
            "block_id": str(a.block_id),
            "activity_type": activity_type,
            "activity_name": activity_name,
            "role": a.role,
            "confidence": a.confidence or 1.0,
        }

        # Add ACGME warnings if requested
        if include_violations:
            # For now, we don't have warnings stored directly
            # This would be populated from validation service
            assignment_dict["acgme_warnings"] = []

        assignments_data.append(assignment_dict)

    # Transform to voxel grid
    voxel_grid = transform_schedule_to_voxels(
        assignments=assignments_data,
        persons=persons_data,
        blocks=blocks_data,
    )

    return voxel_grid.to_dict()


@router.get("/voxel-grid/conflicts")
async def get_3d_conflicts(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get schedule conflicts detected through 3D voxel collision analysis.

    This endpoint uses spatial collision detection to find double-bookings
    where multiple assignments occupy the same (time, person) coordinate.

    Returns:
        Dictionary with conflict details and voxel positions
    """
    # Get full voxel grid first
    grid_response = get_3d_voxel_grid(
        start_date=start_date,
        end_date=end_date,
        person_ids=None,
        activity_types=None,
        include_violations=True,
        db=db,
        current_user=current_user,
    )

    # Extract conflicts
    conflicts = []
    conflict_positions = set()

    for voxel in grid_response.get("voxels", []):
        if voxel.get("state", {}).get("is_conflict"):
            pos = voxel.get("position", {})
            conflict_positions.add((pos.get("x"), pos.get("y")))
            conflicts.append(
                {
                    "position": pos,
                    "identity": voxel.get("identity"),
                    "details": voxel.get("state", {}).get("violation_details", []),
                }
            )

    return {
        "total_conflicts": len(conflict_positions),
        "conflict_voxels": conflicts,
        "conflict_positions": [{"x": x, "y": y} for x, y in conflict_positions],
        "date_range": grid_response.get("date_range"),
    }


@router.get("/voxel-grid/coverage-gaps")
async def get_3d_coverage_gaps(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    required_activity_types: list[str] = Query(
        ["clinic"], description="Activity types that must be covered"
    ),
    db=Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Identify coverage gaps using 3D voxel space analysis.

    Finds empty regions in the voxel grid where assignments should exist.

    Returns:
        Dictionary with gap positions and suggested coverage needs
    """
    # Get full voxel grid
    grid_response = get_3d_voxel_grid(
        start_date=start_date,
        end_date=end_date,
        person_ids=None,
        activity_types=None,
        include_violations=True,
        db=db,
        current_user=current_user,
    )

    dimensions = grid_response.get("dimensions", {})
    x_size = dimensions.get("x_size", 0)
    y_size = dimensions.get("y_size", 0)

    # Build occupancy map
    occupied = set()
    for voxel in grid_response.get("voxels", []):
        pos = voxel.get("position", {})
        occupied.add((pos.get("x"), pos.get("y")))

    # Find gaps (time slots where no one is assigned)
    gaps = []
    x_labels = dimensions.get("x_labels", [])
    y_labels = dimensions.get("y_labels", [])

    for x in range(x_size):
        # Check if any person is assigned at this time
        coverage_at_time = sum(1 for y in range(y_size) if (x, y) in occupied)

        if coverage_at_time == 0:
            gaps.append(
                {
                    "x": x,
                    "time_label": x_labels[x] if x < len(x_labels) else f"Block {x}",
                    "coverage_count": 0,
                    "severity": "critical",  # No one assigned
                }
            )
        elif coverage_at_time < y_size * 0.2:  # Less than 20% coverage
            gaps.append(
                {
                    "x": x,
                    "time_label": x_labels[x] if x < len(x_labels) else f"Block {x}",
                    "coverage_count": coverage_at_time,
                    "severity": "warning",
                }
            )

    return {
        "total_gaps": len([g for g in gaps if g["severity"] == "critical"]),
        "total_warnings": len([g for g in gaps if g["severity"] == "warning"]),
        "gaps": gaps,
        "dimensions": dimensions,
        "date_range": grid_response.get("date_range"),
    }
