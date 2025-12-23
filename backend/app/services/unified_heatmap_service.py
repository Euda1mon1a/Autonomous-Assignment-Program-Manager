"""Unified heatmap service combining residency and FMIT schedules."""

from collections import defaultdict
from datetime import date, timedelta
from typing import Any
from uuid import UUID

import plotly.graph_objects as go
import plotly.io as pio
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus


class UnifiedHeatmapService:
    """Generate combined heatmap visualizations for residency and FMIT schedules."""

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
    def _get_week_start(any_date: date) -> date:
        """Get the Monday of the week containing the given date."""
        days_since_monday = any_date.weekday()
        return any_date - timedelta(days=days_since_monday)

    def generate_coverage_heatmap(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        include_fmit: bool = True,
        include_residency: bool = True,
    ) -> dict:
        """
        Generate coverage heatmap data combining FMIT and residency schedules.

        Args:
            db: Database session
            start_date: Start date for heatmap
            end_date: End date for heatmap
            include_fmit: Include FMIT assignments
            include_residency: Include residency assignments

        Returns:
            Dictionary with heatmap data structure
        """
        dates = self._get_date_range(start_date, end_date)
        x_labels = [d.strftime("%Y-%m-%d") for d in dates]

        # Get all rotation templates
        rotations = db.query(RotationTemplate).order_by(RotationTemplate.name).all()

        # Filter rotations based on inclusion flags
        if not include_fmit and not include_residency:
            rotations = []
        elif not include_fmit:
            rotations = [r for r in rotations if r.name != "FMIT"]
        elif not include_residency:
            rotations = [r for r in rotations if r.name == "FMIT"]

        y_labels = [r.name for r in rotations]
        rotation_ids = [r.id for r in rotations]

        # Build coverage map: (rotation_id, date) -> count of people assigned
        coverage_map: dict[tuple[UUID, date], int] = defaultdict(int)

        # Get all assignments in range
        assignments = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date,
                (
                    Assignment.rotation_template_id.in_(rotation_ids)
                    if rotation_ids
                    else False
                ),
            )
            .all()
        )

        # Count assignments per rotation per date
        for assignment in assignments:
            if assignment.rotation_template_id:
                key = (assignment.rotation_template_id, assignment.block.date)
                coverage_map[key] += 1

        # Build z_values matrix (coverage count per day per rotation)
        z_values = []
        total_assignments = 0
        max_coverage = 0

        for rotation_id in rotation_ids:
            row = []
            for d in dates:
                count = coverage_map.get((rotation_id, d), 0)
                row.append(float(count))
                total_assignments += count
                max_coverage = max(max_coverage, count)
            z_values.append(row)

        # Include FMIT swap metadata if requested
        metadata: dict[str, Any] = {
            "total_assignments": total_assignments,
            "date_range_days": len(dates),
            "rotations_count": len(y_labels),
            "max_coverage": max_coverage,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        if include_fmit:
            # Get swap records in range
            swaps = (
                db.query(SwapRecord)
                .filter(
                    SwapRecord.source_week >= start_date,
                    SwapRecord.source_week <= end_date,
                    SwapRecord.status.in_([SwapStatus.APPROVED, SwapStatus.EXECUTED]),
                )
                .all()
            )
            metadata["fmit_swaps_count"] = len(swaps)
            metadata["swap_details"] = [
                {
                    "source_week": swap.source_week.isoformat(),
                    "target_week": swap.target_week.isoformat(),
                    "status": swap.status.value,
                }
                for swap in swaps
            ]

        return {
            "x_labels": x_labels,
            "y_labels": y_labels,
            "z_values": z_values,
            "color_scale": "Viridis",
            "metadata": metadata,
        }

    def generate_plotly_heatmap(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        include_fmit: bool = True,
        include_residency: bool = True,
    ) -> str:
        """
        Generate plotly heatmap as HTML string.

        Args:
            db: Database session
            start_date: Start date for heatmap
            end_date: End date for heatmap
            include_fmit: Include FMIT assignments
            include_residency: Include residency assignments

        Returns:
            HTML string with interactive plotly heatmap
        """
        # Get heatmap data
        data = self.generate_coverage_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
            include_fmit=include_fmit,
            include_residency=include_residency,
        )

        # Create plotly figure
        fig = go.Figure(
            data=go.Heatmap(
                z=data["z_values"],
                x=data["x_labels"],
                y=data["y_labels"],
                colorscale=data["color_scale"],
                hoverongaps=False,
                hovertemplate="<b>%{y}</b><br>Date: %{x}<br>Coverage: %{z}<extra></extra>",
            )
        )

        # Update layout
        title = "Unified Schedule Coverage Heatmap"
        if include_fmit and not include_residency:
            title = "FMIT Schedule Coverage Heatmap"
        elif include_residency and not include_fmit:
            title = "Residency Schedule Coverage Heatmap"

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Rotation",
            font={"size": 10},
            xaxis={"tickangle": -45},
            height=max(400, len(data["y_labels"]) * 25),
            width=max(800, len(data["x_labels"]) * 20),
        )

        # Convert to HTML
        html_str = pio.to_html(fig, include_plotlyjs="cdn", full_html=True)
        return html_str

    def export_heatmap_image(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        format: str = "png",
        include_fmit: bool = True,
        include_residency: bool = True,
        width: int = 1200,
        height: int = 800,
    ) -> bytes:
        """
        Export heatmap as static image using kaleido.

        Args:
            db: Database session
            start_date: Start date for heatmap
            end_date: End date for heatmap
            format: Export format ('png', 'svg', 'pdf')
            include_fmit: Include FMIT assignments
            include_residency: Include residency assignments
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Image bytes

        Raises:
            ValueError: If format is not supported
        """
        if format not in ["png", "svg", "pdf"]:
            raise ValueError(
                f"Unsupported format: {format}. Must be 'png', 'svg', or 'pdf'"
            )

        # Get heatmap data
        data = self.generate_coverage_heatmap(
            db=db,
            start_date=start_date,
            end_date=end_date,
            include_fmit=include_fmit,
            include_residency=include_residency,
        )

        # Create plotly figure
        fig = go.Figure(
            data=go.Heatmap(
                z=data["z_values"],
                x=data["x_labels"],
                y=data["y_labels"],
                colorscale=data["color_scale"],
                hoverongaps=False,
            )
        )

        # Update layout
        title = "Unified Schedule Coverage Heatmap"
        if include_fmit and not include_residency:
            title = "FMIT Schedule Coverage Heatmap"
        elif include_residency and not include_fmit:
            title = "Residency Schedule Coverage Heatmap"

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Rotation",
            font={"size": 10},
            xaxis={"tickangle": -45},
            width=width,
            height=height,
        )

        # Export to bytes
        img_bytes = pio.to_image(fig, format=format, width=width, height=height)
        return img_bytes

    def generate_person_coverage_heatmap(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        person_ids: list[UUID] | None = None,
        include_call: bool = False,
    ) -> dict:
        """
        Generate person-level coverage heatmap showing assignments per person per day.

        Args:
            db: Database session
            start_date: Start date for heatmap
            end_date: End date for heatmap
            person_ids: Optional filter by person IDs
            include_call: Include call assignments

        Returns:
            Dictionary with heatmap data structure
        """
        dates = self._get_date_range(start_date, end_date)
        x_labels = [d.strftime("%Y-%m-%d") for d in dates]

        # Get people
        query = db.query(Person).order_by(Person.name)
        if person_ids:
            query = query.filter(Person.id.in_(person_ids))
        people = query.all()

        y_labels = [p.name for p in people]
        person_id_list = [p.id for p in people]

        # Build assignment map: (person_id, date) -> count
        assignment_map: dict[tuple[UUID, date], int] = defaultdict(int)

        # Get regular assignments
        assignments = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date,
                Assignment.person_id.in_(person_id_list) if person_id_list else False,
            )
            .all()
        )

        for assignment in assignments:
            key = (assignment.person_id, assignment.block.date)
            assignment_map[key] += 1

        # Add call assignments if requested
        if include_call:
            call_assignments = (
                db.query(CallAssignment)
                .filter(
                    CallAssignment.date >= start_date,
                    CallAssignment.date <= end_date,
                    (
                        CallAssignment.person_id.in_(person_id_list)
                        if person_id_list
                        else False
                    ),
                )
                .all()
            )

            for call in call_assignments:
                key = (call.person_id, call.date)
                # Add extra weight for call assignments
                assignment_map[key] += 0.5

        # Build z_values matrix
        z_values = []
        total_assignments = 0

        for person_id in person_id_list:
            row = []
            for d in dates:
                count = assignment_map.get((person_id, d), 0)
                row.append(float(count))
                total_assignments += count
            z_values.append(row)

        metadata = {
            "total_assignments": total_assignments,
            "date_range_days": len(dates),
            "people_count": len(y_labels),
            "include_call": include_call,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        return {
            "x_labels": x_labels,
            "y_labels": y_labels,
            "z_values": z_values,
            "color_scale": "Blues",
            "metadata": metadata,
        }

    def generate_weekly_fmit_heatmap(
        self,
        db: Session,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Generate weekly FMIT assignment heatmap showing which faculty are assigned each week.

        Args:
            db: Database session
            start_date: Start date for heatmap
            end_date: End date for heatmap

        Returns:
            Dictionary with heatmap data structure
        """
        # Get FMIT rotation template
        fmit_template = (
            db.query(RotationTemplate).filter(RotationTemplate.name == "FMIT").first()
        )

        if not fmit_template:
            return {
                "x_labels": [],
                "y_labels": [],
                "z_values": [],
                "color_scale": "RdYlGn",
                "metadata": {
                    "error": "FMIT rotation template not found",
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            }

        # Generate week starts
        current_week = self._get_week_start(start_date)
        end_week = self._get_week_start(end_date)
        weeks = []
        while current_week <= end_week:
            weeks.append(current_week)
            current_week += timedelta(days=7)

        x_labels = [w.strftime("%Y-%m-%d") for w in weeks]

        # Get all faculty
        faculty = (
            db.query(Person)
            .filter(Person.type == "faculty")
            .order_by(Person.name)
            .all()
        )
        y_labels = [f.name for f in faculty]
        faculty_ids = [f.id for f in faculty]

        # Build assignment map: (faculty_id, week_start) -> has_assignment (1 or 0)
        assignment_map: dict[tuple[UUID, date], int] = defaultdict(int)

        # Get all FMIT assignments in range
        assignments = (
            db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.rotation_template_id == fmit_template.id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
            .all()
        )

        # Group by faculty and week
        for assignment in assignments:
            week_start = self._get_week_start(assignment.block.date)
            key = (assignment.person_id, week_start)
            assignment_map[key] = 1  # Binary: has assignment or not

        # Build z_values matrix
        z_values = []
        total_weeks_assigned = 0

        for faculty_id in faculty_ids:
            row = []
            for week in weeks:
                has_assignment = assignment_map.get((faculty_id, week), 0)
                row.append(float(has_assignment))
                total_weeks_assigned += has_assignment
            z_values.append(row)

        metadata = {
            "total_weeks": len(weeks),
            "total_weeks_assigned": total_weeks_assigned,
            "faculty_count": len(faculty_ids),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        return {
            "x_labels": x_labels,
            "y_labels": y_labels,
            "z_values": z_values,
            "color_scale": "RdYlGn",
            "metadata": metadata,
        }
