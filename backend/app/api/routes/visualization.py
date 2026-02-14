"""Visualization API routes for heatmap generation.

Provides endpoints for generating schedule heatmaps, coverage analysis,
and workload visualization.
"""

import io
import logging
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.visualization import (
    CoverageGap,
    CoverageHeatmapResponse,
    ExportRequest,
    HeatmapData,
    HeatmapResponse,
    UnifiedHeatmapRequest,
)
from app.services.cached_schedule_service import CachedHeatmapService

router = APIRouter()
logger = logging.getLogger(__name__)


def _as_mapping(value: object) -> dict:
    if isinstance(value, dict):
        return value
    raw = getattr(value, "__dict__", None)
    if isinstance(raw, dict):
        return raw
    return {}


def _as_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.utcnow()
    return datetime.utcnow()


def _normalize_heatmap_data(payload: dict) -> HeatmapData:
    nested = payload.get("data")
    if isinstance(nested, HeatmapData):
        return nested
    if isinstance(nested, dict):
        return HeatmapData(**nested)

    z_values = payload.get("z_values")
    if not isinstance(z_values, list):
        z_values = nested if isinstance(nested, list) else []

    x_labels = payload.get("x_labels")
    if not isinstance(x_labels, list):
        x_labels = []

    y_labels = payload.get("y_labels")
    if not isinstance(y_labels, list):
        y_labels = []

    color_scale = payload.get("color_scale")
    if not isinstance(color_scale, str):
        color_scale = "Viridis"

    return HeatmapData(
        x_labels=[str(label) for label in x_labels],
        y_labels=[str(label) for label in y_labels],
        z_values=z_values,
        color_scale=color_scale,
        annotations=None,
    )


def _normalize_heatmap_response(
    raw: object, *, default_title: str = "Schedule Heatmap"
) -> HeatmapResponse:
    if isinstance(raw, HeatmapResponse):
        data = raw.data
        return HeatmapResponse(
            data=data,
            x_labels=raw.x_labels or data.x_labels,
            y_labels=raw.y_labels or data.y_labels,
            z_values=raw.z_values or data.z_values,
            color_scale=raw.color_scale or data.color_scale,
            title=raw.title,
            generated_at=raw.generated_at,
            metadata=raw.metadata,
        )

    payload = _as_mapping(raw)
    data = _normalize_heatmap_data(payload)
    title_value = payload.get("title")
    title = title_value if isinstance(title_value, str) else default_title
    metadata_value = payload.get("metadata")
    metadata = metadata_value if isinstance(metadata_value, dict) else {}

    return HeatmapResponse(
        data=data,
        x_labels=data.x_labels,
        y_labels=data.y_labels,
        z_values=data.z_values,
        color_scale=data.color_scale,
        title=title,
        generated_at=_as_datetime(payload.get("generated_at")),
        metadata=metadata,
    )


def _normalize_coverage_heatmap_response(raw: object) -> CoverageHeatmapResponse:
    payload = _as_mapping(raw)
    data = _normalize_heatmap_data(payload)

    coverage_percentage = payload.get("coverage_percentage")
    if coverage_percentage is None and isinstance(payload.get("summary"), dict):
        coverage_rate = payload["summary"].get("coverage_rate")
        if isinstance(coverage_rate, (int, float)):
            coverage_percentage = (
                coverage_rate * 100.0 if float(coverage_rate) <= 1.0 else coverage_rate
            )
    if not isinstance(coverage_percentage, (int, float)):
        coverage_percentage = 0.0

    normalized_gaps = []
    raw_gaps = payload.get("gaps")
    if isinstance(raw_gaps, list):
        for gap in raw_gaps:
            if not isinstance(gap, dict):
                continue
            gap_date = gap.get("date")
            parsed_date = (
                gap_date
                if isinstance(gap_date, date)
                else (
                    date.fromisoformat(gap_date)
                    if isinstance(gap_date, str)
                    else datetime.utcnow().date()
                )
            )
            normalized_gaps.append(
                CoverageGap(
                    date=parsed_date,
                    time_of_day=(
                        gap.get("time_of_day")
                        if isinstance(gap.get("time_of_day"), str)
                        else "AM"
                    ),
                    rotation=gap.get("rotation")
                    if isinstance(gap.get("rotation"), str)
                    else None,
                    severity=(
                        gap.get("severity")
                        if isinstance(gap.get("severity"), str)
                        else "medium"
                    ),
                )
            )

    title_value = payload.get("title")
    title = title_value if isinstance(title_value, str) else "Coverage Heatmap"
    return CoverageHeatmapResponse(
        data=data,
        coverage_percentage=float(coverage_percentage),
        gaps=normalized_gaps,
        title=title,
        generated_at=_as_datetime(payload.get("generated_at")),
    )


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
    db: Session = Depends(get_db),
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
    result = service.generate_unified_heatmap(
        db=db,
        start_date=start_date,
        end_date=end_date,
        person_ids=person_ids,
        rotation_ids=rotation_ids,
        include_fmit=include_fmit,
        group_by=group_by_lower,
    )
    return _normalize_heatmap_response(result)


@router.post("/heatmap/unified", response_model=HeatmapResponse)
async def get_unified_heatmap_with_time_range(
    request: UnifiedHeatmapRequest,
    db: Session = Depends(get_db),
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
        raise HTTPException(status_code=400, detail="Invalid request parameters") from e

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

    normalized_result = _normalize_heatmap_response(result)

    # Add calculated date range to metadata
    if normalized_result.metadata is None:
        normalized_result.metadata = {}
    normalized_result.metadata["time_range_type"] = request.time_range.range_type
    normalized_result.metadata["calculated_start_date"] = start_date.isoformat()
    normalized_result.metadata["calculated_end_date"] = end_date.isoformat()

    return normalized_result


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
    db: Session = Depends(get_db),
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
        ) from e

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
    db: Session = Depends(get_db),
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
    result = service.generate_coverage_heatmap(
        db=db, start_date=start_date, end_date=end_date
    )
    return _normalize_coverage_heatmap_response(result)


@router.get("/workload", response_model=HeatmapResponse)
async def get_workload_heatmap(
    person_ids: list[UUID] = Query(..., description="Person IDs for workload analysis"),
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    include_weekends: bool = Query(False, description="Include weekends in analysis"),
    db: Session = Depends(get_db),
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
    result = service.generate_person_workload_heatmap(
        db=db,
        person_ids=person_ids,
        start_date=start_date,
        end_date=end_date,
        include_weekends=include_weekends,
    )
    return _normalize_heatmap_response(result, default_title="Workload Heatmap")


@router.post("/export")
async def export_heatmap(
    request: ExportRequest,
    db: Session = Depends(get_db),
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
        raise HTTPException(status_code=400, detail="Invalid request parameters") from e

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
        ) from e

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
            "Content-Disposition": (
                f"attachment; filename={request.heatmap_type}_heatmap.{request.format}"
            )
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
    rotation_types: list[str] | None = Query(
        None, description="Filter by rotation types"
    ),
    include_violations: bool = Query(True, description="Include ACGME violation data"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Generate 3D voxel grid representation of schedule data.

    This is a novel visualization approach that represents the schedule as
    a 3D space where:
    - X-axis: Time (blocks/dates)
    - Y-axis: People (residents, faculty)
    - Z-axis: Rotation type (clinic, inpatient, procedures, etc.)

    Each voxel represents an assignment with properties:
    - Position (x, y, z) in the 3D grid
    - Color based on rotation type or compliance status
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
        rotation_types: Optional filter for specific rotation types
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
        rotation_type = "unknown"
        rotation_name = "Unknown"

        if a.rotation_template:
            rotation_type = a.rotation_template.rotation_type or "unknown"
            rotation_name = a.rotation_template.name
        elif a.activity_override:
            rotation_name = a.activity_override
            # Try to infer rotation type from override name
            override_lower = a.activity_override.lower()
            if "clinic" in override_lower:
                rotation_type = "outpatient"
            elif "inpatient" in override_lower or "ward" in override_lower:
                rotation_type = "inpatient"
            elif "proc" in override_lower:
                rotation_type = "outpatient"
            elif "call" in override_lower:
                rotation_type = "call"
            elif "leave" in override_lower or "off" in override_lower:
                rotation_type = "leave"

        # Filter by rotation type if specified
        if rotation_types and rotation_type not in rotation_types:
            continue

        # Find person name
        person_name = next((p.name for p in persons if p.id == a.person_id), "Unknown")

        assignment_dict = {
            "id": str(a.id),
            "person_id": str(a.person_id),
            "person_name": person_name,
            "block_id": str(a.block_id),
            "rotation_type": rotation_type,
            "rotation_name": rotation_name,
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
    db: Session = Depends(get_db),
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
        rotation_types=None,
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
    required_rotation_types: list[str] = Query(
        ["clinic"], description="Rotation types that must be covered"
    ),
    db: Session = Depends(get_db),
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
        rotation_types=None,
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
