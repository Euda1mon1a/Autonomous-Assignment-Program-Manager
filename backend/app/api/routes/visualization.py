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
from app.db.session import get_db
from app.models.user import User
from app.schemas.visualization import (
    CoverageHeatmapResponse,
    ExportRequest,
    HeatmapResponse,
    TimeRangeType,
    UnifiedHeatmapRequest,
)
from app.services.heatmap_service import HeatmapService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/heatmap", response_model=HeatmapResponse)
def get_unified_heatmap(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    person_ids: list[UUID] | None = Query(None, description="Filter by person IDs"),
    rotation_ids: list[UUID] | None = Query(
        None, description="Filter by rotation template IDs"
    ),
    include_fmit: bool = Query(True, description="Include FMIT swap data"),
    group_by: str = Query("person", description="Group by 'person' or 'rotation'"),
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
        group_by: Group heatmap by 'person' or 'rotation'

    Returns:
        HeatmapResponse with visualization data
    """
    if group_by not in ["person", "rotation"]:
        raise HTTPException(
            status_code=400, detail="group_by must be 'person' or 'rotation'"
        )

    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="start_date must be before or equal to end_date"
        )

    service = HeatmapService()
    return service.generate_unified_heatmap(
        db=db,
        start_date=start_date,
        end_date=end_date,
        person_ids=person_ids,
        rotation_ids=rotation_ids,
        include_fmit=include_fmit,
        group_by=group_by,
    )


@router.post("/heatmap/unified", response_model=HeatmapResponse)
def get_unified_heatmap_with_time_range(
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
    if request.group_by not in ["person", "rotation"]:
        raise HTTPException(
            status_code=400, detail="group_by must be 'person' or 'rotation'"
        )

    service = HeatmapService()

    # Calculate date range from time_range specification
    try:
        start_date, end_date = service.calculate_date_range(request.time_range)
    except ValueError as e:
        logger.error(f"Invalid visualization parameters: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid request parameters")

    # Generate unified heatmap
    result = service.generate_unified_heatmap(
        db=db,
        start_date=start_date,
        end_date=end_date,
        person_ids=request.person_ids,
        rotation_ids=request.rotation_ids,
        include_fmit=request.include_fmit,
        group_by=request.group_by,
    )

    # Add calculated date range to metadata
    if result.metadata is None:
        result.metadata = {}
    result.metadata["time_range_type"] = request.time_range.range_type
    result.metadata["calculated_start_date"] = start_date.isoformat()
    result.metadata["calculated_end_date"] = end_date.isoformat()

    return result


@router.get("/heatmap/image")
def get_heatmap_image(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    person_ids: list[UUID] | None = Query(None, description="Filter by person IDs"),
    rotation_ids: list[UUID] | None = Query(
        None, description="Filter by rotation template IDs"
    ),
    include_fmit: bool = Query(True, description="Include FMIT swap data"),
    group_by: str = Query("person", description="Group by 'person' or 'rotation'"),
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
        group_by: Group heatmap by 'person' or 'rotation'
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

    if group_by not in ["person", "rotation"]:
        raise HTTPException(
            status_code=400, detail="group_by must be 'person' or 'rotation'"
        )

    service = HeatmapService()

    # Generate heatmap data
    heatmap_response = service.generate_unified_heatmap(
        db=db,
        start_date=start_date,
        end_date=end_date,
        person_ids=person_ids,
        rotation_ids=rotation_ids,
        include_fmit=include_fmit,
        group_by=group_by,
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
        raise HTTPException(status_code=500, detail="An error occurred generating the image")

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
        headers={
            "Content-Disposition": f"attachment; filename=heatmap.{format}"
        },
    )


@router.get("/coverage", response_model=CoverageHeatmapResponse)
def get_coverage_heatmap(
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

    service = HeatmapService()
    return service.generate_coverage_heatmap(
        db=db, start_date=start_date, end_date=end_date
    )


@router.get("/workload", response_model=HeatmapResponse)
def get_workload_heatmap(
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

    service = HeatmapService()
    return service.generate_person_workload_heatmap(
        db=db,
        person_ids=person_ids,
        start_date=start_date,
        end_date=end_date,
        include_weekends=include_weekends,
    )


@router.post("/export")
def export_heatmap(
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

    service = HeatmapService()

    # Generate appropriate heatmap based on type
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
        raise HTTPException(
            status_code=400, detail="Invalid request parameters"
        )

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
        raise HTTPException(status_code=500, detail="An error occurred generating the image")

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
