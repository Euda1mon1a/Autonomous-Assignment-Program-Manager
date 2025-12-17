"""
Academic blocks / block matrix API.

Provides program coordinator view of resident assignments grouped by rotation blocks.
Thin routing layer that connects URL paths to service layer.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.academic_blocks import BlockListResponse, BlockMatrixResponse
from app.services.academic_block_service import AcademicBlockService

router = APIRouter()


@router.get("/matrix/academic-blocks", response_model=BlockMatrixResponse)
def get_academic_block_matrix(
    academic_year: str = Query(..., description="Academic year (e.g., '2024-2025')"),
    pgy_level: int | None = Query(None, description="Filter by PGY level (1-3)", ge=1, le=3),
    db: Session = Depends(get_db),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating block matrix: {str(e)}",
        )


@router.get("/matrix/blocks", response_model=BlockListResponse)
def list_academic_blocks(
    academic_year: str = Query(..., description="Academic year (e.g., '2024-2025')"),
    db: Session = Depends(get_db),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing academic blocks: {str(e)}",
        )
