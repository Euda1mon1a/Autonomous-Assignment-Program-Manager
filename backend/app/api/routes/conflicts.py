"""
Conflict Analysis API Routes.

Provides endpoints for comprehensive schedule conflict detection,
analysis, resolution suggestions, and visualization.
"""

import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import get_current_active_user
from app.db.session import get_async_db
from app.models.user import User
from app.scheduling.conflicts import (
    ConflictAnalyzer,
    ConflictVisualizer,
)
from app.scheduling.conflicts.types import ConflictSummary

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analyze")
async def analyze_conflicts(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    person_id: UUID | None = Query(
        None, description="Optional: analyze for specific person"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Perform comprehensive conflict analysis on schedule.

    Analyzes the schedule for the specified date range and detects:
    - Time overlaps (double booking)
    - Resource contentions (insufficient coverage)
    - ACGME violations (duty hours, consecutive days)
    - Supervision issues (inadequate ratios)

    Returns a list of all detected conflicts with severity scoring.

    Args:
        start_date: Start of analysis period
        end_date: End of analysis period
        person_id: Optional person ID to focus analysis on

    Returns:
        Dict with conflicts list and summary statistics
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )

    analyzer = ConflictAnalyzer(db)

    try:
        conflicts = await analyzer.analyze_schedule(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
        )

        summary = await analyzer.generate_summary(conflicts)

        # Convert conflicts to dict for JSON response
        conflicts_dict = [conflict.model_dump() for conflict in conflicts]

        return {
            "conflicts": conflicts_dict,
            "summary": summary.model_dump(),
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        }

    except (ValueError, KeyError, AttributeError) as e:
        logger.error(f"Error analyzing conflicts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing conflicts: {str(e)}",
        )


@router.get("/summary")
async def get_conflict_summary(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    person_id: UUID | None = Query(
        None, description="Optional: analyze for specific person"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
) -> ConflictSummary:
    """
    Get conflict summary statistics without full details.

    Provides a quick overview of conflicts in the specified period
    without returning the full conflict list. Useful for dashboards.

    Args:
        start_date: Start of analysis period
        end_date: End of analysis period
        person_id: Optional person ID to focus analysis on

    Returns:
        ConflictSummary with aggregate statistics
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )

    analyzer = ConflictAnalyzer(db)

    try:
        conflicts = await analyzer.analyze_schedule(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
        )

        summary = await analyzer.generate_summary(conflicts)
        return summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}",
        )


@router.get("/timeline")
async def get_conflict_timeline(
    start_date: date = Query(..., description="Start date for timeline"),
    end_date: date = Query(..., description="End date for timeline"),
    person_id: UUID | None = Query(
        None, description="Optional: timeline for specific person"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate conflict timeline visualization data.

    Creates a day-by-day timeline showing conflicts and their severity
    over the specified period. Useful for Gantt charts and calendar views.

    Args:
        start_date: Start of timeline
        end_date: End of timeline
        person_id: Optional person ID to focus on

    Returns:
        ConflictTimeline with visualization data
    """
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before or equal to end_date",
        )

    analyzer = ConflictAnalyzer(db)
    visualizer = ConflictVisualizer()

    try:
        conflicts = await analyzer.analyze_schedule(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
        )

        timeline = await visualizer.generate_timeline(
            conflicts=conflicts,
            start_date=start_date,
            end_date=end_date,
        )

        return timeline.model_dump()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating timeline: {str(e)}",
        )


@router.get("/visualizations/heatmap")
async def get_conflict_heatmap(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    person_id: UUID | None = Query(
        None, description="Optional: analyze for specific person"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate conflict heatmap data.

    Creates a calendar heatmap showing conflict intensity by date.
    Useful for identifying problem periods at a glance.

    Args:
        start_date: Start of analysis period
        end_date: End of analysis period
        person_id: Optional person ID to focus on

    Returns:
        Heatmap data structure with date -> intensity mapping
    """
    analyzer = ConflictAnalyzer(db)
    visualizer = ConflictVisualizer()

    try:
        conflicts = await analyzer.analyze_schedule(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
        )

        heatmap_data = await visualizer.generate_heatmap_data(conflicts)
        return heatmap_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating heatmap: {str(e)}",
        )


@router.get("/visualizations/gantt")
async def get_conflict_gantt(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    person_id: UUID | None = Query(
        None, description="Optional: analyze for specific person"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate Gantt chart data for conflicts.

    Creates bars showing conflict duration and overlap over time.

    Args:
        start_date: Start of analysis period
        end_date: End of analysis period
        person_id: Optional person ID to focus on

    Returns:
        List of Gantt chart entries
    """
    analyzer = ConflictAnalyzer(db)
    visualizer = ConflictVisualizer()

    try:
        conflicts = await analyzer.analyze_schedule(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
        )

        gantt_data = await visualizer.generate_gantt_data(conflicts)
        return {"gantt_entries": gantt_data}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating Gantt chart: {str(e)}",
        )


@router.get("/visualizations/distribution")
async def get_conflict_distribution(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    person_id: UUID | None = Query(
        None, description="Optional: analyze for specific person"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate conflict distribution charts.

    Shows breakdown of conflicts by type, severity, category, etc.
    Useful for pie charts and bar charts.

    Args:
        start_date: Start of analysis period
        end_date: End of analysis period
        person_id: Optional person ID to focus on

    Returns:
        Distribution data for multiple chart types
    """
    analyzer = ConflictAnalyzer(db)
    visualizer = ConflictVisualizer()

    try:
        conflicts = await analyzer.analyze_schedule(
            start_date=start_date,
            end_date=end_date,
            person_id=person_id,
        )

        distribution = await visualizer.generate_distribution_chart(conflicts)
        return distribution

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating distribution: {str(e)}",
        )


@router.get("/visualizations/person-impact")
async def get_person_impact(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Generate person impact analysis.

    Shows which people are most affected by conflicts.
    Useful for identifying high-impact individuals.

    Args:
        start_date: Start of analysis period
        end_date: End of analysis period

    Returns:
        List of people sorted by conflict impact
    """
    analyzer = ConflictAnalyzer(db)
    visualizer = ConflictVisualizer()

    try:
        conflicts = await analyzer.analyze_schedule(
            start_date=start_date,
            end_date=end_date,
        )

        impact_data = await visualizer.generate_person_impact_chart(conflicts)
        return {"person_impacts": impact_data}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating person impact: {str(e)}",
        )


@router.post("/resolve/{conflict_id}/suggestions")
async def get_resolution_suggestions(
    conflict_id: str,
    max_suggestions: int = Query(
        5, ge=1, le=10, description="Maximum suggestions to return"
    ),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get resolution suggestions for a specific conflict.

    Analyzes the conflict and generates intelligent suggestions
    for how to resolve it, with impact assessments.

    Args:
        conflict_id: ID of the conflict to resolve
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of resolution suggestions with implementation steps
    """
    # First, we need to re-analyze to find the specific conflict
    # In a real implementation, conflicts would be stored in the database
    # For now, we'll return a helpful error message

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Resolution suggestions require conflicts to be persisted. "
            "This feature will be available once conflict persistence is implemented."
        ),
    )


@router.post("/batch-analyze")
async def batch_analyze_conflicts(
    person_ids: list[UUID] = Query(..., description="List of person IDs to analyze"),
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Batch analyze conflicts for multiple people.

    Analyzes conflicts for a list of people and aggregates results.
    Useful for team-wide conflict analysis.

    Args:
        person_ids: List of person IDs to analyze
        start_date: Start of analysis period
        end_date: End of analysis period

    Returns:
        Aggregated conflict analysis for all specified people
    """
    if len(person_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 people per batch analysis",
        )

    analyzer = ConflictAnalyzer(db)
    all_conflicts = []

    try:
        for person_id in person_ids:
            conflicts = await analyzer.analyze_schedule(
                start_date=start_date,
                end_date=end_date,
                person_id=person_id,
            )
            all_conflicts.extend(conflicts)

        # Remove duplicates (conflicts affecting multiple people)
        unique_conflicts = {c.conflict_id: c for c in all_conflicts}.values()
        unique_conflicts_list = list(unique_conflicts)

        summary = await analyzer.generate_summary(unique_conflicts_list)

        return {
            "total_people_analyzed": len(person_ids),
            "conflicts": [c.model_dump() for c in unique_conflicts_list],
            "summary": summary.model_dump(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch analysis: {str(e)}",
        )
