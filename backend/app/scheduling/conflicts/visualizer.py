"""
Conflict Visualization Data Generator.

This module generates data structures for visualizing conflicts in
timelines, heatmaps, and other graphical representations.
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from app.scheduling.conflicts.types import (
    Conflict,
    ConflictSeverity,
    ConflictTimeline,
)

logger = logging.getLogger(__name__)


class ConflictVisualizer:
    """
    Generates visualization data for conflicts.

    Provides methods to create timeline views, heatmaps, and other
    visual representations of conflict data for frontend display.
    """

    # Severity score mapping
    SEVERITY_SCORES = {
        ConflictSeverity.CRITICAL: 1.0,
        ConflictSeverity.HIGH: 0.75,
        ConflictSeverity.MEDIUM: 0.5,
        ConflictSeverity.LOW: 0.25,
    }

    def __init__(self):
        """Initialize the conflict visualizer."""
        pass

    async def generate_timeline(
        self,
        conflicts: list[Conflict],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> ConflictTimeline:
        """
        Generate a timeline visualization of conflicts.

        Creates a day-by-day timeline showing conflicts, their severity,
        and distribution over time.

        Args:
            conflicts: List of conflicts to visualize
            start_date: Optional start date (defaults to earliest conflict)
            end_date: Optional end date (defaults to latest conflict)

        Returns:
            ConflictTimeline with visualization data
        """
        if not conflicts:
            # Return empty timeline
            today = date.today()
            return ConflictTimeline(
                start_date=start_date or today,
                end_date=end_date or today,
            )

        # Determine date range
        if not start_date:
            start_date = min(c.start_date for c in conflicts)
        if not end_date:
            end_date = max(c.end_date for c in conflicts)

        # Initialize timeline
        timeline = ConflictTimeline(
            start_date=start_date,
            end_date=end_date,
        )

        # Group conflicts by date
        conflicts_by_date: dict[date, list[Conflict]] = defaultdict(list)

        for conflict in conflicts:
            # Add conflict to all dates in its range
            current_date = conflict.start_date
            while current_date <= conflict.end_date and current_date <= end_date:
                if current_date >= start_date:
                    conflicts_by_date[current_date].append(conflict)
                current_date += timedelta(days=1)

        # Build timeline entries
        current_date = start_date
        while current_date <= end_date:
            date_conflicts = conflicts_by_date.get(current_date, [])

            # Calculate severity score for this date
            severity_score = 0.0
            if date_conflicts:
                severity_score = max(
                    self.SEVERITY_SCORES.get(c.severity, 0.0)
                    for c in date_conflicts
                )

            # Create timeline entry
            entry = {
                "date": current_date.isoformat(),
                "conflict_count": len(date_conflicts),
                "severity_score": severity_score,
                "conflicts": [
                    {
                        "conflict_id": c.conflict_id,
                        "type": c.conflict_type.value,
                        "severity": c.severity.value,
                        "title": c.title,
                    }
                    for c in date_conflicts
                ],
            }

            timeline.timeline_entries.append(entry)
            timeline.severity_by_date[current_date.isoformat()] = severity_score
            timeline.count_by_date[current_date.isoformat()] = len(date_conflicts)

            current_date += timedelta(days=1)

        # Build person-specific timelines
        for conflict in conflicts:
            for person_id in conflict.affected_people:
                person_id_str = str(person_id)
                if person_id_str not in timeline.conflicts_by_person:
                    timeline.conflicts_by_person[person_id_str] = []

                # Add all dates in conflict range
                current_date = conflict.start_date
                while current_date <= conflict.end_date and current_date <= end_date:
                    if current_date >= start_date:
                        date_str = current_date.isoformat()
                        if date_str not in timeline.conflicts_by_person[person_id_str]:
                            timeline.conflicts_by_person[person_id_str].append(date_str)
                    current_date += timedelta(days=1)

        # Generate category timeline (weekly aggregation)
        timeline.category_timeline = self._generate_category_timeline(
            conflicts,
            start_date,
            end_date,
        )

        return timeline

    def _generate_category_timeline(
        self,
        conflicts: list[Conflict],
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Generate category distribution timeline (weekly aggregation).

        Args:
            conflicts: List of conflicts
            start_date: Start date
            end_date: End date

        Returns:
            List of weekly category distribution entries
        """
        category_timeline = []

        # Find start of first week (Monday)
        current_week_start = start_date - timedelta(days=start_date.weekday())

        while current_week_start <= end_date:
            week_end = current_week_start + timedelta(days=6)

            # Find conflicts in this week
            week_conflicts = [
                c for c in conflicts
                if not (c.end_date < current_week_start or c.start_date > week_end)
            ]

            # Count by category
            category_counts: dict[str, int] = defaultdict(int)
            for conflict in week_conflicts:
                category_counts[conflict.category.value] += 1

            # Create week entry
            entry = {
                "week_start": current_week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "total_conflicts": len(week_conflicts),
                "by_category": dict(category_counts),
            }

            category_timeline.append(entry)
            current_week_start += timedelta(days=7)

        return category_timeline

    async def generate_heatmap_data(
        self,
        conflicts: list[Conflict],
    ) -> dict[str, Any]:
        """
        Generate heatmap data for conflict visualization.

        Creates a matrix suitable for calendar heatmaps showing
        conflict intensity by date.

        Args:
            conflicts: List of conflicts to visualize

        Returns:
            Heatmap data structure
        """
        if not conflicts:
            return {
                "data": [],
                "min_value": 0.0,
                "max_value": 0.0,
                "color_scale": "red",
            }

        # Build date -> severity mapping
        date_severity: dict[str, float] = {}

        for conflict in conflicts:
            current_date = conflict.start_date
            severity_score = self.SEVERITY_SCORES.get(conflict.severity, 0.0)

            while current_date <= conflict.end_date:
                date_str = current_date.isoformat()
                # Use max severity if multiple conflicts on same date
                date_severity[date_str] = max(
                    date_severity.get(date_str, 0.0),
                    severity_score,
                )
                current_date += timedelta(days=1)

        # Convert to heatmap data points
        heatmap_data = [
            {
                "date": date_str,
                "value": severity,
                "level": self._severity_to_level(severity),
            }
            for date_str, severity in date_severity.items()
        ]

        # Sort by date
        heatmap_data.sort(key=lambda x: x["date"])

        return {
            "data": heatmap_data,
            "min_value": min(date_severity.values()) if date_severity else 0.0,
            "max_value": max(date_severity.values()) if date_severity else 0.0,
            "color_scale": "red",
            "levels": 4,  # LOW, MEDIUM, HIGH, CRITICAL
        }

    def _severity_to_level(self, severity_score: float) -> int:
        """
        Convert severity score to discrete level.

        Args:
            severity_score: Score from 0.0 to 1.0

        Returns:
            Level from 0 to 3 (0=none, 1=low, 2=medium, 3=high, 4=critical)
        """
        if severity_score == 0.0:
            return 0
        elif severity_score <= 0.25:
            return 1
        elif severity_score <= 0.5:
            return 2
        elif severity_score <= 0.75:
            return 3
        else:
            return 4

    async def generate_gantt_data(
        self,
        conflicts: list[Conflict],
    ) -> list[dict[str, Any]]:
        """
        Generate Gantt chart data for conflict visualization.

        Creates bars showing conflict duration and overlap.

        Args:
            conflicts: List of conflicts to visualize

        Returns:
            List of Gantt chart entries
        """
        gantt_data = []

        for conflict in conflicts:
            entry = {
                "id": conflict.conflict_id,
                "title": conflict.title,
                "start": conflict.start_date.isoformat(),
                "end": conflict.end_date.isoformat(),
                "severity": conflict.severity.value,
                "category": conflict.category.value,
                "type": conflict.conflict_type.value,
                "impact_score": conflict.impact_score,
                "urgency_score": conflict.urgency_score,
                "affected_people_count": len(conflict.affected_people),
                "color": self._get_severity_color(conflict.severity),
            }

            gantt_data.append(entry)

        # Sort by start date then severity
        gantt_data.sort(
            key=lambda x: (
                x["start"],
                -self.SEVERITY_SCORES.get(
                    ConflictSeverity(x["severity"]),
                    0.0,
                ),
            )
        )

        return gantt_data

    def _get_severity_color(self, severity: ConflictSeverity) -> str:
        """
        Get color code for severity level.

        Args:
            severity: Conflict severity

        Returns:
            Color hex code
        """
        colors = {
            ConflictSeverity.CRITICAL: "#DC2626",  # red-600
            ConflictSeverity.HIGH: "#EA580C",  # orange-600
            ConflictSeverity.MEDIUM: "#F59E0B",  # amber-500
            ConflictSeverity.LOW: "#FCD34D",  # amber-300
        }
        return colors.get(severity, "#9CA3AF")  # gray-400 default

    async def generate_distribution_chart(
        self,
        conflicts: list[Conflict],
    ) -> dict[str, Any]:
        """
        Generate distribution chart data.

        Shows breakdown of conflicts by type, severity, category, etc.

        Args:
            conflicts: List of conflicts to analyze

        Returns:
            Distribution chart data
        """
        # Count by severity
        by_severity: dict[str, int] = defaultdict(int)
        for conflict in conflicts:
            by_severity[conflict.severity.value] += 1

        # Count by category
        by_category: dict[str, int] = defaultdict(int)
        for conflict in conflicts:
            by_category[conflict.category.value] += 1

        # Count by type
        by_type: dict[str, int] = defaultdict(int)
        for conflict in conflicts:
            by_type[conflict.conflict_type.value] += 1

        return {
            "by_severity": dict(by_severity),
            "by_category": dict(by_category),
            "by_type": dict(by_type),
            "total": len(conflicts),
            "severity_chart": [
                {"label": severity, "count": count, "color": self._get_severity_color(ConflictSeverity(severity))}
                for severity, count in by_severity.items()
            ],
            "category_chart": [
                {"label": category, "count": count}
                for category, count in by_category.items()
            ],
        }

    async def generate_person_impact_chart(
        self,
        conflicts: list[Conflict],
    ) -> list[dict[str, Any]]:
        """
        Generate person impact chart data.

        Shows which people are most affected by conflicts.

        Args:
            conflicts: List of conflicts to analyze

        Returns:
            Person impact chart data
        """
        # Count conflicts per person
        person_conflict_count: dict[str, int] = defaultdict(int)
        person_severity_scores: dict[str, list[float]] = defaultdict(list)

        for conflict in conflicts:
            for person_id in conflict.affected_people:
                person_id_str = str(person_id)
                person_conflict_count[person_id_str] += 1
                severity_score = self.SEVERITY_SCORES.get(conflict.severity, 0.0)
                person_severity_scores[person_id_str].append(severity_score)

        # Build chart data
        impact_data = []
        for person_id_str, conflict_count in person_conflict_count.items():
            avg_severity = (
                sum(person_severity_scores[person_id_str]) / len(person_severity_scores[person_id_str])
                if person_severity_scores[person_id_str]
                else 0.0
            )

            impact_data.append({
                "person_id": person_id_str,
                "conflict_count": conflict_count,
                "average_severity": round(avg_severity, 2),
                "max_severity": max(person_severity_scores[person_id_str]),
            })

        # Sort by conflict count (descending)
        impact_data.sort(key=lambda x: x["conflict_count"], reverse=True)

        return impact_data
