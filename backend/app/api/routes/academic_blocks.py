"""
Academic blocks / block matrix API.

Provides program coordinator view of resident assignments grouped by rotation blocks.
Thin routing layer that connects URL paths to service layer.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.schemas.academic_blocks import BlockListResponse, BlockMatrixResponse
from app.services.academic_block_service import AcademicBlockService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/matrix/academic-blocks", response_model=BlockMatrixResponse)
async def get_academic_block_matrix(
    academic_year: str = Query(..., description="Academic year (e.g., '2024-2025')"),
    pgy_level: int | None = Query(
        None, description="Filter by PGY level (1-3)", ge=1, le=3
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get academic block matrix for program coordinators.

    Groups daily assignments (730 half-day blocks) into rotation blocks (~4 weeks each).
    Shows which residents are assigned to which rotations per block.

    Returns a matrix with:
    - Columns: Academic blocks (typically 13 blocks per year)
    - Rows: Residents (optionally filtered by PGY level)
    - Cells: Rotation assignments with hours and ACGME compliance

    Args:
        academic_year: Academic year in format "YYYY-YYYY" (e.g., "2024-2025")
        pgy_level: Optional filter by PGY level (1, 2, or 3)
        db: Database session

    Returns:
        BlockMatrixResponse with complete matrix data
    """
    service = AcademicBlockService(db)

    try:
        matrix = service.get_block_matrix(
            academic_year=academic_year,
            pgy_level=pgy_level,
        )
        return matrix
    except ValueError as e:
        logger.error(f"Invalid block matrix request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request parameters",
        )
    except Exception as e:
        logger.error(f"Error generating block matrix: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred generating the block matrix",
        )


@router.get("/matrix/blocks", response_model=BlockListResponse)
async def list_academic_blocks(
    academic_year: str = Query(..., description="Academic year (e.g., '2024-2025')"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all academic blocks for the year with summary statistics.

    Returns block information including:
    - Block number, name, and date range
    - Total assignments and residents per block
    - ACGME compliance rate
    - Average hours per resident

    Args:
        academic_year: Academic year in format "YYYY-YYYY" (e.g., "2024-2025")
        db: Database session

    Returns:
        BlockListResponse with list of blocks and summaries
    """
    service = AcademicBlockService(db)

    try:
        blocks = service.list_academic_blocks(academic_year=academic_year)
        return blocks
    except ValueError as e:
        logger.error(f"Invalid academic blocks list request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request parameters",
        )
    except Exception as e:
        logger.error(f"Error listing academic blocks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred listing academic blocks",
        )
