"""Heatmap service for schedule visualization using Plotly."""

from datetime import date, timedelta
from typing import Any
from uuid import UUID

import plotly.graph_objects as go
import plotly.io as pio
from sqlalchemy.orm import Session, joinedload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus
from app.schemas.visualization import (
    CoverageGap,
    CoverageHeatmapResponse,
    HeatmapData,
    HeatmapResponse,
    TimeRangeType,
)


class HeatmapService:
    """Service for generating heatmap visualizations."""

    @staticmethod
    def calculate_date_range(time_range: TimeRangeType) -> tuple[date, date]:
        """
        Calculate start and end dates from time range specification.

        Args:
            time_range: TimeRangeType specification

        Returns:
            Tuple of (start_date, end_date)

        Raises:
            ValueError: If range_type is invalid or required dates are missing
        """
        range_type = time_range.range_type
        reference = time_range.reference_date or date.today()

        if range_type == "custom":
            if not time_range.start_date or not time_range.end_date:
                raise ValueError("start_date and end_date required for custom range")
            return time_range.start_date, time_range.end_date

        elif range_type == "week":
            # Start from Monday of the week containing reference_date
            start_of_week = reference - timedelta(days=reference.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            return start_of_week, end_of_week

        elif range_type == "month":
            # Start from first day of the month
            start_of_month = reference.replace(day=1)
            # Calculate last day of month
            if reference.month == 12:
                end_of_month = reference.replace(
                    year=reference.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                end_of_month = reference.replace(
                    month=reference.month + 1, day=1
                ) - timedelta(days=1)
            return start_of_month, end_of_month

        elif range_type == "quarter":
            # Determine which quarter the reference date is in
            quarter_month = ((reference.month - 1) // 3) * 3 + 1
            start_of_quarter = reference.replace(month=quarter_month, day=1)

            # Calculate end of quarter (3 months later, minus 1 day)
            if quarter_month >= 10:
                end_month_start = start_of_quarter.replace(
                    year=reference.year + 1,
                    month=((quarter_month + 3) % 12) or 12,
                    day=1,
                )
            else:
                end_month_start = start_of_quarter.replace(
                    month=quarter_month + 3, day=1
                )
            end_of_quarter = end_month_start - timedelta(days=1)

            return start_of_quarter, end_of_quarter

        else:
            raise ValueError(
                f"Invalid range_type: {range_type}. Must be 'week', 'month', 'quarter', or 'custom'"
            )

    @staticmethod
    def _get_date_range(start_date: date, end_date: date) -> list[date]:
        """Generate list of dates in range."""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates

    @staticmethod
    def _get_blocks_in_range(
        db: Session, start_date: date, end_date: date
    ) -> list[Block]:
        """Get all blocks in date range."""
        return (
            db.query(Block)
            .filter(Block.date >= start_date, Block.date <= end_date)
            .order_by(Block.date, Block.time_of_day)
            .all()
        )

    @staticmethod
    def _get_assignments_in_range(
        db: Session,
        start_date: date,
        end_date: date,
        person_ids: list[UUID] | None = None,
        rotation_ids: list[UUID] | None = None,
    ) -> list[Assignment]:
        """Get all assignments in date range with optional filters."""
        query = (
            db.query(Assignment)
            .join(Block)
            .options(
                joinedload(Assignment.block),
                joinedload(Assignment.person),
                joinedload(Assignment.rotation_template),
            )
            .filter(Block.date >= start_date, Block.date <= end_date)
        )

        if person_ids:
            query = query.filter(Assignment.person_id.in_(person_ids))

        if rotation_ids:
            query = query.filter(Assignment.rotation_template_id.in_(rotation_ids))

        return query.all()

    @staticmethod
    def _get_swap_records_in_range(
        db: Session, start_date: date, end_date: date
    ) -> list[SwapRecord]:
        """Get all FMIT swap records in date range."""
        return (
            db.query(SwapRecord)
            .filter(
                SwapRecord.source_week >= start_date,
                SwapRecord.source_week <= end_date,
                SwapRecord.status.in_([SwapStatus.APPROVED, SwapStatus.EXECUTED]),
            )
            .all()
        )

    def _generate_daily_heatmap(
        self,
        db: Session,
        assignments: list[Assignment],
        start_date: date,
        end_date: date,
        include_fmit: bool = True,
    ) -> HeatmapResponse:
        """Generate heatmap grouped by day (showing assignment counts per day)."""
        dates = self._get_date_range(start_date, end_date)
        x_labels = [d.strftime("%Y-%m-%d") for d in dates]

        # Count assignments per day
        daily_counts = dict.fromkeys(dates, 0)
        for assignment in assignments:
            block_date = assignment.block.date
            if block_date in daily_counts:
                daily_counts[block_date] += 1

        # Create single row with daily counts
        z_values = [[float(daily_counts[d]) for d in dates]]
        y_labels = ["Total Assignments"]

        heatmap_data = HeatmapData(
            x_labels=x_labels,
            y_labels=y_labels,
            z_values=z_values,
            color_scale="Viridis",
            annotations=None,
        )

        metadata: dict[str, Any] = {
            "total_assignments": len(assignments),
            "date_range_days": len(dates),
            "grouping_type": "daily",
        }

        if include_fmit:
            swaps = self._get_swap_records_in_range(db, start_date, end_date)
            metadata["fmit_swaps_count"] = len(swaps)

        return HeatmapResponse(
            data=heatmap_data,
            title="Daily Assignment Heatmap",
            metadata=metadata,
        )

    def _generate_weekly_heatmap(
        self,
        db: Session,
        assignments: list[Assignment],
        start_date: date,
        end_date: date,
        include_fmit: bool = True,
    ) -> HeatmapResponse:
        """Generate heatmap grouped by week (showing assignment counts per week)."""
        # Generate week starts
        current_week = start_date - timedelta(days=start_date.weekday())
        weeks = []
        while current_week <= end_date:
            weeks.append(current_week)
            current_week += timedelta(days=7)

        x_labels = [w.strftime("%Y-%m-%d") for w in weeks]

        # Count assignments per week
        weekly_counts = dict.fromkeys(weeks, 0)
        for assignment in assignments:
            block_date = assignment.block.date
            # Find the week this assignment belongs to
            week_start = block_date - timedelta(days=block_date.weekday())
            if week_start in weekly_counts:
                weekly_counts[week_start] += 1

        # Create single row with weekly counts
        z_values = [[float(weekly_counts[w]) for w in weeks]]
        y_labels = ["Total Assignments"]

        heatmap_data = HeatmapData(
            x_labels=x_labels,
            y_labels=y_labels,
            z_values=z_values,
            color_scale="Viridis",
            annotations=None,
        )

        metadata: dict[str, Any] = {
            "total_assignments": len(assignments),
            "weeks_count": len(weeks),
            "grouping_type": "weekly",
        }

        if include_fmit:
            swaps = self._get_swap_records_in_range(db, start_date, end_date)
            metadata["fmit_swaps_count"] = len(swaps)

        return HeatmapResponse(
            data=heatmap_data,
            title="Weekly Assignment Heatmap",
            metadata=metadata,
        )

    def generate_unified_heatmap(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        person_ids: list[UUID] | None = None,
        rotation_ids: list[UUID] | None = None,
        include_fmit: bool = True,
        group_by: str = "person",
    ) -> HeatmapResponse:
        """
        Generate unified heatmap showing both residency and FMIT schedules.

        Args:
            db: Database session
            start_date: Start date for heatmap
            end_date: End date for heatmap
            person_ids: Optional filter by person IDs
            rotation_ids: Optional filter by rotation template IDs
            include_fmit: Whether to include FMIT swap data
            group_by: Group by 'person', 'rotation', 'daily', or 'weekly'

        Returns:
            HeatmapResponse with data and metadata
        """
        # Get assignments
        assignments = self._get_assignments_in_range(
            db, start_date, end_date, person_ids, rotation_ids
        )

        # Handle daily and weekly grouping (group by date instead of entity)
        if group_by == "daily":
            return self._generate_daily_heatmap(
                db, assignments, start_date, end_date, include_fmit
            )
        elif group_by == "weekly":
            return self._generate_weekly_heatmap(
                db, assignments, start_date, end_date, include_fmit
            )

        # Original person/rotation grouping logic
        dates = self._get_date_range(start_date, end_date)
        x_labels = [d.strftime("%Y-%m-%d") for d in dates]

        # Build assignment map: (person_id or rotation_id, date) -> count
        assignment_map: dict[tuple[Any, date], int] = {}

        for assignment in assignments:
            block_date = assignment.block.date
            if group_by == "person":
                key = (assignment.person_id, block_date)
            else:  # group_by == "rotation"
                key = (assignment.rotation_template_id, block_date)

            assignment_map[key] = assignment_map.get(key, 0) + 1

        # Get unique entities (people or rotations)
        if group_by == "person":
            if person_ids:
                entities = db.query(Person).filter(Person.id.in_(person_ids)).all()
            else:
                # Get all people with assignments in range
                entity_ids = {a.person_id for a in assignments}
                entities = (
                    db.query(Person).filter(Person.id.in_(entity_ids)).all()
                    if entity_ids
                    else []
                )
            y_labels = [p.name for p in entities]
            entity_ids_ordered = [p.id for p in entities]
        else:  # group_by == "rotation"
            if rotation_ids:
                entities = (
                    db.query(RotationTemplate)
                    .filter(RotationTemplate.id.in_(rotation_ids))
                    .all()
                )
            else:
                # Get all rotation templates with assignments in range
                entity_ids = {
                    a.rotation_template_id
                    for a in assignments
                    if a.rotation_template_id
                }
                entities = (
                    db.query(RotationTemplate)
                    .filter(RotationTemplate.id.in_(entity_ids))
                    .all()
                    if entity_ids
                    else []
                )
            y_labels = [r.name for r in entities]
            entity_ids_ordered = [r.id for r in entities]

        # Build z_values matrix
        z_values = []
        for entity_id in entity_ids_ordered:
            row = []
            for d in dates:
                count = assignment_map.get((entity_id, d), 0)
                row.append(float(count))
            z_values.append(row)

        # Include FMIT swap data if requested
        metadata: dict[str, Any] = {
            "total_assignments": len(assignments),
            "date_range_days": len(dates),
            "entities_count": len(y_labels),
        }

        if include_fmit:
            swaps = self._get_swap_records_in_range(db, start_date, end_date)
            metadata["fmit_swaps_count"] = len(swaps)

        heatmap_data = HeatmapData(
            x_labels=x_labels,
            y_labels=y_labels,
            z_values=z_values,
            color_scale="Viridis",
            annotations=None,
        )

        title = f"{'Person' if group_by == 'person' else 'Rotation'} Schedule Heatmap"

        return HeatmapResponse(
            data=heatmap_data,
            title=title,
            metadata=metadata,
        )

    def generate_coverage_heatmap(
        self, db: Session, start_date: date, end_date: date
    ) -> CoverageHeatmapResponse:
        """
        Generate coverage heatmap showing staffing levels per rotation.

        Args:
            db: Database session
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            CoverageHeatmapResponse with coverage data and gaps
        """
        dates = self._get_date_range(start_date, end_date)
        x_labels = [d.strftime("%Y-%m-%d") for d in dates]

        # Get all rotation templates
        rotations = db.query(RotationTemplate).all()
        y_labels = [r.name for r in rotations]
        rotation_ids = [r.id for r in rotations]

        # Get all blocks and assignments in range
        self._get_blocks_in_range(db, start_date, end_date)
        assignments = self._get_assignments_in_range(db, start_date, end_date)

        # Build coverage map: (rotation_id, date) -> assignment count
        coverage_map: dict[tuple[UUID, date], int] = {}
        for assignment in assignments:
            if assignment.rotation_template_id:
                key = (assignment.rotation_template_id, assignment.block.date)
                coverage_map[key] = coverage_map.get(key, 0) + 1

        # Build z_values matrix (coverage level: 0 = no coverage, 1+ = covered)
        # Normalize to 0-1 scale for visualization
        z_values = []
        gaps: list[CoverageGap] = []

        for rotation_id, rotation in zip(rotation_ids, rotations, strict=False):
            row = []
            for d in dates:
                count = coverage_map.get((rotation_id, d), 0)

                # Determine expected coverage (simplified - could be more sophisticated)
                expected = 1  # Assume 1 person minimum per day

                # Calculate coverage ratio
                coverage_ratio = min(count / expected, 1.0) if expected > 0 else 0.0
                row.append(coverage_ratio)

                # Identify gaps
                if coverage_ratio < 1.0:
                    severity = "high" if coverage_ratio == 0 else "medium"
                    gaps.append(
                        CoverageGap(
                            date=d,
                            time_of_day="ALL",
                            rotation=rotation.name,
                            severity=severity,
                        )
                    )

            z_values.append(row)

        # Calculate overall coverage percentage
        total_slots = len(rotation_ids) * len(dates)
        covered_slots = sum(1 for row in z_values for val in row if val >= 1.0)
        coverage_percentage = (
            (covered_slots / total_slots * 100) if total_slots > 0 else 0.0
        )

        heatmap_data = HeatmapData(
            x_labels=x_labels,
            y_labels=y_labels,
            z_values=z_values,
            color_scale="RdYlGn",  # Red-Yellow-Green for coverage
            annotations=None,
        )

        return CoverageHeatmapResponse(
            data=heatmap_data,
            coverage_percentage=coverage_percentage,
            gaps=gaps,
            title="Rotation Coverage Heatmap",
        )

    def generate_person_workload_heatmap(
        self,
        db: Session,
        person_ids: list[UUID],
        start_date: date,
        end_date: date,
        include_weekends: bool = False,
    ) -> HeatmapResponse:
        """
        Generate workload heatmap for specific people.

        Args:
            db: Database session
            person_ids: List of person IDs to include
            start_date: Start date
            end_date: End date
            include_weekends: Whether to include weekends

        Returns:
            HeatmapResponse with workload data
        """
        dates = self._get_date_range(start_date, end_date)

        if not include_weekends:
            # Filter out weekends (Saturday=5, Sunday=6)
            dates = [d for d in dates if d.weekday() < 5]

        x_labels = [d.strftime("%Y-%m-%d") for d in dates]

        # Get people
        people = db.query(Person).filter(Person.id.in_(person_ids)).all()
        y_labels = [p.name for p in people]

        # Get assignments for these people
        assignments = self._get_assignments_in_range(
            db, start_date, end_date, person_ids=person_ids
        )

        # Build workload map: (person_id, date) -> block count
        workload_map: dict[tuple[UUID, date], int] = {}
        for assignment in assignments:
            key = (assignment.person_id, assignment.block.date)
            workload_map[key] = workload_map.get(key, 0) + 1

        # Build z_values matrix
        z_values = []
        for person in people:
            row = []
            for d in dates:
                count = workload_map.get((person.id, d), 0)
                row.append(float(count))
            z_values.append(row)

        # Calculate workload statistics
        total_blocks = sum(sum(row) for row in z_values)
        avg_blocks_per_person = total_blocks / len(people) if people else 0

        heatmap_data = HeatmapData(
            x_labels=x_labels,
            y_labels=y_labels,
            z_values=z_values,
            color_scale="Blues",
            annotations=None,
        )

        return HeatmapResponse(
            data=heatmap_data,
            title="Person Workload Heatmap",
            metadata={
                "total_blocks": int(total_blocks),
                "avg_blocks_per_person": round(avg_blocks_per_person, 2),
                "people_count": len(people),
                "include_weekends": include_weekends,
            },
        )

    @staticmethod
    def export_heatmap_image(
        data: HeatmapData,
        title: str,
        format: str = "png",
        width: int = 1200,
        height: int = 800,
    ) -> bytes:
        """
        Export heatmap as image using Plotly.

        Args:
            data: HeatmapData to visualize
            title: Title for the heatmap
            format: Export format ('png', 'pdf', 'svg')
            width: Width in pixels
            height: Height in pixels

        Returns:
            Image bytes
        """
        # Create Plotly figure
        fig = go.Figure(
            data=go.Heatmap(
                z=data.z_values,
                x=data.x_labels,
                y=data.y_labels,
                colorscale=data.color_scale,
                hoverongaps=False,
            )
        )

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="",
            width=width,
            height=height,
            font={"size": 10},
            xaxis={"tickangle": -45},
        )

        # Export to bytes
        if format == "png":
            img_bytes = pio.to_image(fig, format="png", width=width, height=height)
        elif format == "pdf":
            img_bytes = pio.to_image(fig, format="pdf", width=width, height=height)
        elif format == "svg":
            img_bytes = pio.to_image(fig, format="svg", width=width, height=height)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return img_bytes

    @staticmethod
    def create_plotly_figure(data: HeatmapData, title: str) -> dict[str, Any]:
        """
        Create Plotly figure configuration for frontend rendering.

        Args:
            data: HeatmapData to visualize
            title: Title for the heatmap

        Returns:
            Plotly figure as JSON-serializable dict
        """
        fig = go.Figure(
            data=go.Heatmap(
                z=data.z_values,
                x=data.x_labels,
                y=data.y_labels,
                colorscale=data.color_scale,
                hoverongaps=False,
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="",
            font={"size": 10},
            xaxis={"tickangle": -45},
        )

        return fig.to_dict()
