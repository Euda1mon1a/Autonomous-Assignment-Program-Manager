"""Unified heatmap API routes combining residency and FMIT schedules."""

import io
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.unified_heatmap import (
    HeatmapExportRequest,
    HeatmapRenderRequest,
    PersonCoverageRequest,
    PersonCoverageResponse,
    UnifiedCoverageRequest,
    UnifiedCoverageResponse,
    WeeklyFMITRequest,
    WeeklyFMITResponse,
)
from app.services.unified_heatmap_service import UnifiedHeatmapService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/heatmap/data", response_model=UnifiedCoverageResponse)
async def get_heatmap_data(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    include_fmit: bool = Query(True, description="Include FMIT assignments"),
    include_residency: bool = Query(True, description="Include residency assignments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UnifiedCoverageResponse:
    """
    Get unified heatmap matrix data for frontend rendering.

    Returns JSON data structure suitable for rendering with Plotly or other
    visualization libraries on the frontend.

    Args:
        start_date: Start date for heatmap
        end_date: End date for heatmap
        include_fmit: Whether to include FMIT assignments
        include_residency: Whether to include residency assignments
        db: Database session
        current_user: Authenticated user

    Returns:
        UnifiedCoverageResponse with heatmap data structure

    Raises:
        HTTPException: If date range is invalid or parameters are incorrect
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    if not include_fmit and not include_residency:
        raise HTTPException(
            status_code=400,
            detail="At least one of include_fmit or include_residency must be True",
        )

    service = UnifiedHeatmapService()
    try:
        data = service.generate_coverage_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
            include_fmit=include_fmit,
            include_residency=include_residency,
        )
        return UnifiedCoverageResponse(**data)
    except Exception as e:
        logger.error(f"Error generating heatmap data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred generating heatmap data",
        )


@router.post("/heatmap/data", response_model=UnifiedCoverageResponse)
async def post_heatmap_data(
    request: UnifiedCoverageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UnifiedCoverageResponse:
    """
    Get unified heatmap matrix data using POST request.

    Alternative to GET endpoint for more complex request parameters.

    Args:
        request: UnifiedCoverageRequest with heatmap parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        UnifiedCoverageResponse with heatmap data structure
    """
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    if not request.include_fmit and not request.include_residency:
        raise HTTPException(
            status_code=400,
            detail="At least one of include_fmit or include_residency must be True",
        )

    service = UnifiedHeatmapService()
    try:
        data = service.generate_coverage_heatmap(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
            include_fmit=request.include_fmit,
            include_residency=request.include_residency,
        )
        return UnifiedCoverageResponse(**data)
    except Exception as e:
        logger.error(f"Error generating heatmap data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred generating heatmap data",
        )


@router.get("/heatmap/render", response_class=HTMLResponse)
async def render_heatmap(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    include_fmit: bool = Query(True, description="Include FMIT assignments"),
    include_residency: bool = Query(True, description="Include residency assignments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HTMLResponse:
    """
    Render interactive plotly heatmap as HTML.

    Returns a complete HTML page with an interactive Plotly heatmap that can be
    displayed directly in a browser or embedded in an iframe.

    Args:
        start_date: Start date for heatmap
        end_date: End date for heatmap
        include_fmit: Whether to include FMIT assignments
        include_residency: Whether to include residency assignments
        db: Database session
        current_user: Authenticated user

    Returns:
        HTML page with interactive heatmap

    Raises:
        HTTPException: If date range is invalid or rendering fails
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    if not include_fmit and not include_residency:
        raise HTTPException(
            status_code=400,
            detail="At least one of include_fmit or include_residency must be True",
        )

    service = UnifiedHeatmapService()
    try:
        html_content = service.generate_plotly_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
            include_fmit=include_fmit,
            include_residency=include_residency,
        )
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering heatmap: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred rendering the heatmap",
        )


@router.post("/heatmap/render", response_class=HTMLResponse)
async def post_render_heatmap(
    request: HeatmapRenderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> HTMLResponse:
    """
    Render interactive plotly heatmap using POST request.

    Alternative to GET endpoint for more complex request parameters.

    Args:
        request: HeatmapRenderRequest with rendering parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        HTML page with interactive heatmap
    """
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    if not request.include_fmit and not request.include_residency:
        raise HTTPException(
            status_code=400,
            detail="At least one of include_fmit or include_residency must be True",
        )

    service = UnifiedHeatmapService()
    try:
        html_content = service.generate_plotly_heatmap(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
            include_fmit=request.include_fmit,
            include_residency=request.include_residency,
        )
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error rendering heatmap: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred rendering the heatmap",
        )


@router.get("/heatmap/export")
async def export_heatmap(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    format: str = Query("png", regex="^(png|svg|pdf)$", description="Export format"),
    include_fmit: bool = Query(True, description="Include FMIT assignments"),
    include_residency: bool = Query(True, description="Include residency assignments"),
    width: int = Query(1200, description="Image width in pixels", gt=0, le=4000),
    height: int = Query(800, description="Image height in pixels", gt=0, le=4000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Export unified heatmap as static image.

    Generates and returns a static image file (PNG, SVG, or PDF) of the heatmap.
    Useful for including in reports or presentations.

    Args:
        start_date: Start date for heatmap
        end_date: End date for heatmap
        format: Export format ('png', 'svg', or 'pdf')
        include_fmit: Whether to include FMIT assignments
        include_residency: Whether to include residency assignments
        width: Image width in pixels
        height: Image height in pixels
        db: Database session
        current_user: Authenticated user

    Returns:
        Image file as streaming response

    Raises:
        HTTPException: If date range is invalid or export fails
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    if not include_fmit and not include_residency:
        raise HTTPException(
            status_code=400,
            detail="At least one of include_fmit or include_residency must be True",
        )

    service = UnifiedHeatmapService()
    try:
        image_bytes = service.export_heatmap_image(
            db=db,
            start_date=start_date,
            end_date=end_date,
            format=format,
            include_fmit=include_fmit,
            include_residency=include_residency,
            width=width,
            height=height,
        )
    except ValueError as e:
        logger.error(f"Invalid heatmap export parameters: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid request parameters")
    except Exception as e:
        logger.error(f"Error exporting heatmap: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred exporting the heatmap",
        )

    # Determine media type
    media_types = {
        "png": "image/png",
        "pdf": "application/pdf",
        "svg": "image/svg+xml",
    }
    media_type = media_types.get(format, "application/octet-stream")

    # Generate filename
    filename = f"unified_heatmap_{start_date}_{end_date}.{format}"

    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/heatmap/export")
async def post_export_heatmap(
    request: HeatmapExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Export unified heatmap using POST request.

    Alternative to GET endpoint for more complex request parameters.

    Args:
        request: HeatmapExportRequest with export parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        Image file as streaming response
    """
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    if not request.include_fmit and not request.include_residency:
        raise HTTPException(
            status_code=400,
            detail="At least one of include_fmit or include_residency must be True",
        )

    if request.format not in ["png", "svg", "pdf"]:
        raise HTTPException(
            status_code=400,
            detail="format must be 'png', 'svg', or 'pdf'",
        )

    service = UnifiedHeatmapService()
    try:
        image_bytes = service.export_heatmap_image(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
            format=request.format,
            include_fmit=request.include_fmit,
            include_residency=request.include_residency,
            width=request.width,
            height=request.height,
        )
    except ValueError as e:
        logger.error(f"Invalid heatmap export parameters: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid request parameters")
    except Exception as e:
        logger.error(f"Error exporting heatmap: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred exporting the heatmap",
        )

    # Determine media type
    media_types = {
        "png": "image/png",
        "pdf": "application/pdf",
        "svg": "image/svg+xml",
    }
    media_type = media_types.get(request.format, "application/octet-stream")

    # Generate filename
    filename = (
        f"unified_heatmap_{request.start_date}_{request.end_date}.{request.format}"
    )

    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/person-coverage/data", response_model=PersonCoverageResponse)
async def get_person_coverage_data(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    include_call: bool = Query(False, description="Include call assignments"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PersonCoverageResponse:
    """
    Get person-level coverage heatmap data.

    Shows assignments per person per day, useful for workload analysis.

    Args:
        start_date: Start date for heatmap
        end_date: End date for heatmap
        include_call: Whether to include call assignments
        db: Database session
        current_user: Authenticated user

    Returns:
        PersonCoverageResponse with person-level heatmap data
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    service = UnifiedHeatmapService()
    try:
        data = service.generate_person_coverage_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
            person_ids=None,
            include_call=include_call,
        )
        return PersonCoverageResponse(**data)
    except Exception as e:
        logger.error(f"Error generating person coverage data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred generating person coverage data",
        )


@router.post("/person-coverage/data", response_model=PersonCoverageResponse)
async def post_person_coverage_data(
    request: PersonCoverageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PersonCoverageResponse:
    """
    Get person-level coverage heatmap data using POST request.

    Args:
        request: PersonCoverageRequest with parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        PersonCoverageResponse with person-level heatmap data
    """
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    service = UnifiedHeatmapService()
    try:
        data = service.generate_person_coverage_heatmap(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
            person_ids=request.person_ids,
            include_call=request.include_call,
        )
        return PersonCoverageResponse(**data)
    except Exception as e:
        logger.error(f"Error generating person coverage data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred generating person coverage data",
        )


@router.get("/weekly-fmit/data", response_model=WeeklyFMITResponse)
async def get_weekly_fmit_data(
    start_date: date = Query(..., description="Start date for heatmap"),
    end_date: date = Query(..., description="End date for heatmap"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WeeklyFMITResponse:
    """
    Get weekly FMIT assignment heatmap data.

    Shows which faculty members are assigned to FMIT duty for each week.

    Args:
        start_date: Start date for heatmap
        end_date: End date for heatmap
        db: Database session
        current_user: Authenticated user

    Returns:
        WeeklyFMITResponse with weekly FMIT assignment data
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    service = UnifiedHeatmapService()
    try:
        data = service.generate_weekly_fmit_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )
        return WeeklyFMITResponse(**data)
    except Exception as e:
        logger.error(f"Error generating weekly FMIT data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred generating weekly FMIT data",
        )


@router.post("/weekly-fmit/data", response_model=WeeklyFMITResponse)
async def post_weekly_fmit_data(
    request: WeeklyFMITRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> WeeklyFMITResponse:
    """
    Get weekly FMIT assignment heatmap data using POST request.

    Args:
        request: WeeklyFMITRequest with parameters
        db: Database session
        current_user: Authenticated user

    Returns:
        WeeklyFMITResponse with weekly FMIT assignment data
    """
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be before or equal to end_date",
        )

    service = UnifiedHeatmapService()
    try:
        data = service.generate_weekly_fmit_heatmap(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
        )
        return WeeklyFMITResponse(**data)
    except Exception as e:
        logger.error(f"Error generating weekly FMIT data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An error occurred generating weekly FMIT data",
        )
