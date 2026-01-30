"""
Holographic Visualization Data Export for FRMS.

This module exports time-series fatigue predictions in JSON format
optimized for holographic/3D visualization in the hub dashboard.

Export Formats:
1. FatigueTimeSeries: Per-resident fatigue trajectory over time
2. TemporalDynamicsData: Aggregate temporal patterns (circadian, weekly)
3. SpatialFatigueMap: Team-level fatigue distribution
4. PredictiveWaves: Future fatigue predictions with confidence bands

Integration:
- Session 1-3: Coordinates with QUBO solver and core FRMS
- Holographic Hub: Provides data for 3D schedule visualization
- Voxel Grid: Fatigue values map to voxel colors/opacity
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Any
from uuid import UUID

from app.frms.three_process_model import (
    ThreeProcessModel,
    AlertnessState,
    CircadianPhase,
)
from app.frms.performance_predictor import PerformancePredictor

logger = logging.getLogger(__name__)


@dataclass
class FatigueTimeSeries:
    """
    Time-series fatigue data for a single resident.

    Optimized for visualization as a 3D trajectory through time.
    """

    person_id: str
    person_name: str
    pgy_level: int | None = None

    # Time series data points
    data_points: list[dict] = field(default_factory=list)
    # Each point: {timestamp, effectiveness, risk_level, circadian_phase, ...}

    # Metadata
    start_time: datetime | None = None
    end_time: datetime | None = None
    sample_interval_minutes: int = 30

    # Visualization parameters
    color_gradient: list[str] = field(default_factory=list)  # Colors for risk levels
    min_effectiveness: float = 100.0
    max_effectiveness: float = 100.0

    def to_dict(self) -> dict:
        """Serialize for JSON export."""
        return {
            "person_id": self.person_id,
            "person_name": self.person_name,
            "pgy_level": self.pgy_level,
            "time_range": {
                "start": self.start_time.isoformat() if self.start_time else None,
                "end": self.end_time.isoformat() if self.end_time else None,
                "sample_interval_minutes": self.sample_interval_minutes,
            },
            "statistics": {
                "min_effectiveness": round(self.min_effectiveness, 2),
                "max_effectiveness": round(self.max_effectiveness, 2),
                "data_points_count": len(self.data_points),
            },
            "color_gradient": self.color_gradient,
            "data_points": self.data_points,
        }


@dataclass
class TemporalDynamicsData:
    """
    Aggregate temporal dynamics for the entire program.

    Shows how fatigue patterns evolve across:
    - Circadian rhythm (24-hour cycle)
    - Weekly patterns (day-of-week effects)
    - Monthly/block patterns
    """

    export_time: datetime
    analysis_period_days: int

    # Circadian pattern (24 hourly bins)
    circadian_pattern: list[dict] = field(default_factory=list)
    # Each: {hour, avg_effectiveness, std_dev, sample_count}

    # Weekly pattern (7 daily bins)
    weekly_pattern: list[dict] = field(default_factory=list)
    # Each: {day_of_week, avg_effectiveness, std_dev}

    # Resonance detection (circadian-workload alignment)
    resonance_patterns: list[dict] = field(default_factory=list)

    # Aggregate time series
    aggregate_time_series: list[dict] = field(default_factory=list)

    # Heatmap data (hour x day matrix)
    heatmap_data: list[list[float]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for JSON export."""
        return {
            "export_time": self.export_time.isoformat(),
            "analysis_period_days": self.analysis_period_days,
            "patterns": {
                "circadian": self.circadian_pattern,
                "weekly": self.weekly_pattern,
                "resonance": self.resonance_patterns,
            },
            "aggregate_time_series": self.aggregate_time_series,
            "heatmap": {
                "data": self.heatmap_data,
                "x_labels": [f"{h:02d}:00" for h in range(24)],
                "y_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            },
        }


@dataclass
class SpatialFatigueMap:
    """
    Spatial mapping of fatigue across the program.

    Maps fatigue data to positions for 3D visualization:
    - X: Time (blocks/days)
    - Y: Person (sorted by PGY level or team)
    - Z: Rotation type
    - Color: Effectiveness score
    - Opacity: Confidence level
    """

    export_time: datetime
    grid_dimensions: dict = field(default_factory=dict)  # {x, y, z sizes}
    voxels: list[dict] = field(default_factory=list)

    # Axis labels
    x_labels: list[str] = field(default_factory=list)  # Dates/blocks
    y_labels: list[str] = field(default_factory=list)  # Person names
    z_labels: list[str] = field(default_factory=list)  # Rotation types

    def to_dict(self) -> dict:
        """Serialize for JSON export."""
        return {
            "export_time": self.export_time.isoformat(),
            "grid_dimensions": self.grid_dimensions,
            "axes": {
                "x_labels": self.x_labels,
                "y_labels": self.y_labels,
                "z_labels": self.z_labels,
            },
            "voxels": self.voxels,
            "voxel_count": len(self.voxels),
        }


class HolographicExporter:
    """
    Exports FRMS data for holographic/3D visualization.

    Transforms fatigue predictions and monitoring data into formats
    optimized for 3D rendering in the hub dashboard.

    Usage:
        exporter = HolographicExporter()

        # Export individual time series
        ts = exporter.export_time_series(person_id, assignments, hours=168)

        # Export temporal dynamics
        dynamics = exporter.export_temporal_dynamics(all_assignments, days=14)

        # Export spatial map
        spatial = exporter.export_spatial_map(assignments, persons, blocks)
    """

    # Color palette for effectiveness levels
    EFFECTIVENESS_COLORS = {
        "optimal": "#22c55e",  # green (95-100%)
        "acceptable": "#84cc16",  # lime (85-94%)
        "caution": "#eab308",  # yellow (77-84%)
        "high_risk": "#f97316",  # orange (70-76%)
        "critical": "#ef4444",  # red (<70%)
    }

    # Circadian phase colors
    PHASE_COLORS = {
        CircadianPhase.WOCL: "#7c3aed",  # violet
        CircadianPhase.MORNING_RISE: "#f59e0b",  # amber
        CircadianPhase.MORNING_PEAK: "#22c55e",  # green
        CircadianPhase.POST_LUNCH_DIP: "#3b82f6",  # blue
        CircadianPhase.AFTERNOON_RISE: "#10b981",  # teal
        CircadianPhase.EVENING: "#6366f1",  # indigo
        CircadianPhase.PRE_SLEEP: "#8b5cf6",  # purple
    }

    def __init__(self) -> None:
        """Initialize exporter."""
        self.model = ThreeProcessModel()
        self.predictor = PerformancePredictor()

    def export_time_series(
        self,
        person_id: UUID,
        person_name: str,
        assignments: list[dict],
        hours: int = 168,  # 1 week default
        sample_interval_minutes: int = 30,
        pgy_level: int | None = None,
    ) -> FatigueTimeSeries:
        """
        Export fatigue time series for a single resident.

        Args:
            person_id: Resident UUID
            person_name: Resident name
            assignments: Assignment history
            hours: Hours of data to export
            sample_interval_minutes: Sample interval
            pgy_level: Optional PGY level

        Returns:
            FatigueTimeSeries for visualization
        """
        now = datetime.now()
        start_time = now - timedelta(hours=hours)

        # Create initial state
        state = self.model.create_state(person_id, timestamp=start_time)

        # Generate time series
        data_points = []
        current_time = start_time
        min_eff = 100.0
        max_eff = 100.0

        while current_time <= now:
            # Update state
            hours_passed = sample_interval_minutes / 60.0
            state = self.model.update_wakefulness(state, hours_passed)

            # Get effectiveness
            tod = current_time.hour + current_time.minute / 60.0
            score = self.model.calculate_effectiveness(state, tod)

            min_eff = min(min_eff, score.overall)
            max_eff = max(max_eff, score.overall)

            # Create data point
            data_points.append(
                {
                    "timestamp": current_time.isoformat(),
                    "timestamp_epoch": current_time.timestamp(),
                    "effectiveness": round(score.overall, 2),
                    "homeostatic": round(score.homeostatic, 2),
                    "circadian": round(score.circadian, 2),
                    "sleep_inertia": round(score.sleep_inertia, 2),
                    "risk_level": score.risk_level,
                    "circadian_phase": state.circadian_phase.value,
                    "color": self._effectiveness_to_color(score.overall),
                    "position": {
                        "x": (current_time - start_time).total_seconds()
                        / 3600.0,  # hours
                        "y": score.overall / 100.0,  # normalized
                        "z": 0,  # can be used for 3D trajectory
                    },
                }
            )

            current_time += timedelta(minutes=sample_interval_minutes)

        return FatigueTimeSeries(
            person_id=str(person_id),
            person_name=person_name,
            pgy_level=pgy_level,
            data_points=data_points,
            start_time=start_time,
            end_time=now,
            sample_interval_minutes=sample_interval_minutes,
            color_gradient=list(self.EFFECTIVENESS_COLORS.values()),
            min_effectiveness=min_eff,
            max_effectiveness=max_eff,
        )

    def export_temporal_dynamics(
        self,
        all_effectiveness_data: dict[UUID, list[tuple[datetime, float]]],
        analysis_days: int = 14,
    ) -> TemporalDynamicsData:
        """
        Export aggregate temporal dynamics.

        Args:
            all_effectiveness_data: {person_id: [(timestamp, effectiveness), ...]}
            analysis_days: Days of data to analyze

        Returns:
            TemporalDynamicsData with patterns
        """
        now = datetime.now()
        cutoff = now - timedelta(days=analysis_days)

        # Collect all data points in analysis window
        hourly_bins: dict[int, list[float]] = {h: [] for h in range(24)}
        daily_bins: dict[int, list[float]] = {d: [] for d in range(7)}
        heatmap: dict[tuple[int, int], list[float]] = {}  # (hour, day) -> values

        for person_id, history in all_effectiveness_data.items():
            for timestamp, effectiveness in history:
                if timestamp < cutoff:
                    continue

                hour = timestamp.hour
                day = timestamp.weekday()

                hourly_bins[hour].append(effectiveness)
                daily_bins[day].append(effectiveness)

                key = (hour, day)
                if key not in heatmap:
                    heatmap[key] = []
                heatmap[key].append(effectiveness)

                # Calculate circadian pattern
        circadian_pattern = []
        for hour in range(24):
            values = hourly_bins[hour]
            if values:
                circadian_pattern.append(
                    {
                        "hour": hour,
                        "avg_effectiveness": round(sum(values) / len(values), 2),
                        "std_dev": round(self._std_dev(values), 2),
                        "sample_count": len(values),
                        "color": self._effectiveness_to_color(
                            sum(values) / len(values)
                        ),
                    }
                )

                # Calculate weekly pattern
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        weekly_pattern = []
        for day in range(7):
            values = daily_bins[day]
            if values:
                weekly_pattern.append(
                    {
                        "day_of_week": day,
                        "day_name": day_names[day],
                        "avg_effectiveness": round(sum(values) / len(values), 2),
                        "std_dev": round(self._std_dev(values), 2),
                        "sample_count": len(values),
                    }
                )

                # Build heatmap matrix
        heatmap_data = []
        for day in range(7):
            row = []
            for hour in range(24):
                values = heatmap.get((hour, day), [])
                if values:
                    row.append(round(sum(values) / len(values), 2))
                else:
                    row.append(None)
            heatmap_data.append(row)

            # Detect resonance patterns
        resonance_patterns = self._detect_resonance_patterns(circadian_pattern)

        return TemporalDynamicsData(
            export_time=now,
            analysis_period_days=analysis_days,
            circadian_pattern=circadian_pattern,
            weekly_pattern=weekly_pattern,
            resonance_patterns=resonance_patterns,
            heatmap_data=heatmap_data,
        )

    def export_spatial_map(
        self,
        assignments: list[dict],
        persons: list[dict],
        blocks: list[dict],
        effectiveness_data: dict[str, float] | None = None,
    ) -> SpatialFatigueMap:
        """
        Export spatial fatigue map for 3D visualization.

        Maps fatigue data to a voxel grid where:
        - X axis: Time (blocks sorted by date)
        - Y axis: People (sorted by PGY level)
        - Z axis: Rotation type
        - Color: Effectiveness score

        Args:
            assignments: List of assignments
            persons: List of persons
            blocks: List of blocks
            effectiveness_data: Optional pre-computed effectiveness by assignment

        Returns:
            SpatialFatigueMap for 3D rendering
        """
        now = datetime.now()

        # Sort blocks by date
        sorted_blocks = sorted(
            blocks,
            key=lambda b: (
                b.get("date")
                if isinstance(b.get("date"), (date, datetime))
                else date.fromisoformat(str(b.get("date", "2000-01-01")))
            ),
        )

        # Sort persons by PGY level
        sorted_persons = sorted(
            persons, key=lambda p: (p.get("pgy_level", 0), p.get("name", ""))
        )

        # Activity types
        rotation_types = sorted(
            list(set(a.get("rotation_type", "unknown") for a in assignments))
        )

        # Build index maps
        block_idx = {b.get("id"): i for i, b in enumerate(sorted_blocks)}
        person_idx = {p.get("id"): i for i, p in enumerate(sorted_persons)}
        rotation_idx = {t: i for i, t in enumerate(rotation_types)}

        # Generate voxels
        voxels = []
        for assignment in assignments:
            person_id = assignment.get("person_id")
            block_id = assignment.get("block_id")
            rotation_type = assignment.get("rotation_type", "unknown")

            x = block_idx.get(block_id)
            y = person_idx.get(person_id)
            z = rotation_idx.get(rotation_type, 0)

            if x is None or y is None:
                continue

                # Get effectiveness
            if effectiveness_data:
                effectiveness = effectiveness_data.get(assignment.get("id"), 85.0)
            else:
                effectiveness = 85.0  # Default

            voxels.append(
                {
                    "position": {"x": x, "y": y, "z": z},
                    "person_id": str(person_id),
                    "block_id": str(block_id),
                    "effectiveness": round(effectiveness, 2),
                    "color": self._effectiveness_to_color(effectiveness),
                    "opacity": min(1.0, effectiveness / 100.0),
                    "is_critical": effectiveness < 70,
                    "is_warning": 70 <= effectiveness < 77,
                }
            )

        return SpatialFatigueMap(
            export_time=now,
            grid_dimensions={
                "x": len(sorted_blocks),
                "y": len(sorted_persons),
                "z": len(rotation_types),
            },
            voxels=voxels,
            x_labels=[str(b.get("date", "")) for b in sorted_blocks],
            y_labels=[p.get("name", "Unknown") for p in sorted_persons],
            z_labels=rotation_types,
        )

    def export_predictive_waves(
        self,
        persons: list[dict],
        assignments: list[dict],
        forecast_hours: int = 168,  # 1 week
    ) -> dict:
        """
        Export predictive fatigue waves with confidence bands.

        Shows future fatigue predictions with uncertainty visualization.

        Args:
            persons: List of persons
            assignments: Current and future assignments
            forecast_hours: Hours to forecast

        Returns:
            Dict with wave data for each person
        """
        now = datetime.now()
        waves = {}

        for person in persons:
            person_id = person.get("id")
            person_name = person.get("name", "Unknown")

            # Get person's assignments
            person_assignments = [
                a for a in assignments if a.get("person_id") == person_id
            ]

            # Create initial state
            state = self.model.create_state(
                UUID(person_id) if isinstance(person_id, str) else person_id,
                timestamp=now,
            )

            # Generate predictions
            predictions = []
            confidence_high = []
            confidence_low = []

            current_time = now
            while current_time <= now + timedelta(hours=forecast_hours):
                hours_passed = 1.0
                state = self.model.update_wakefulness(state, hours_passed)

                tod = current_time.hour + current_time.minute / 60.0
                score = self.model.calculate_effectiveness(state, tod)

                # Confidence increases with prediction distance
                hours_ahead = (current_time - now).total_seconds() / 3600.0
                confidence_width = 5.0 + hours_ahead * 0.5  # Wider bands further out

                predictions.append(
                    {
                        "timestamp": current_time.isoformat(),
                        "effectiveness": round(score.overall, 2),
                        "hours_ahead": round(hours_ahead, 1),
                    }
                )

                confidence_high.append(
                    {
                        "timestamp": current_time.isoformat(),
                        "value": round(min(100, score.overall + confidence_width), 2),
                    }
                )

                confidence_low.append(
                    {
                        "timestamp": current_time.isoformat(),
                        "value": round(max(0, score.overall - confidence_width), 2),
                    }
                )

                current_time += timedelta(hours=1)

            waves[str(person_id)] = {
                "person_name": person_name,
                "predictions": predictions,
                "confidence_band": {
                    "high": confidence_high,
                    "low": confidence_low,
                },
                "risk_periods": self._identify_risk_periods(predictions),
            }

        return {
            "export_time": now.isoformat(),
            "forecast_hours": forecast_hours,
            "waves": waves,
        }

    def _effectiveness_to_color(self, effectiveness: float) -> str:
        """Map effectiveness score to hex color."""
        if effectiveness >= 95:
            return self.EFFECTIVENESS_COLORS["optimal"]
        elif effectiveness >= 85:
            return self.EFFECTIVENESS_COLORS["acceptable"]
        elif effectiveness >= 77:
            return self.EFFECTIVENESS_COLORS["caution"]
        elif effectiveness >= 70:
            return self.EFFECTIVENESS_COLORS["high_risk"]
        else:
            return self.EFFECTIVENESS_COLORS["critical"]

    def _std_dev(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance**0.5

    def _detect_resonance_patterns(
        self,
        circadian_pattern: list[dict],
    ) -> list[dict]:
        """
        Detect circadian-workload resonance patterns.

        Identifies when work patterns align badly with biological rhythms.
        """
        patterns = []

        # Find WOCL hours (2-6 AM)
        wocl_hours = [p for p in circadian_pattern if 2 <= p["hour"] < 6]
        if wocl_hours:
            wocl_avg = sum(p["avg_effectiveness"] for p in wocl_hours) / len(wocl_hours)
            if wocl_avg < 75:
                patterns.append(
                    {
                        "type": "wocl_fatigue",
                        "description": "Low effectiveness during WOCL (2-6 AM)",
                        "avg_effectiveness": round(wocl_avg, 2),
                        "severity": "high" if wocl_avg < 70 else "moderate",
                        "hours_affected": [p["hour"] for p in wocl_hours],
                    }
                )

                # Find post-lunch dip
        lunch_hours = [p for p in circadian_pattern if 13 <= p["hour"] < 16]
        if lunch_hours:
            lunch_avg = sum(p["avg_effectiveness"] for p in lunch_hours) / len(
                lunch_hours
            )
            # Compare to morning peak
            morning_hours = [p for p in circadian_pattern if 9 <= p["hour"] < 12]
            if morning_hours:
                morning_avg = sum(p["avg_effectiveness"] for p in morning_hours) / len(
                    morning_hours
                )
                if lunch_avg < morning_avg - 5:
                    patterns.append(
                        {
                            "type": "post_lunch_dip",
                            "description": "Significant post-lunch fatigue drop",
                            "morning_avg": round(morning_avg, 2),
                            "afternoon_avg": round(lunch_avg, 2),
                            "severity": "low" if lunch_avg > 80 else "moderate",
                        }
                    )

        return patterns

    def _identify_risk_periods(
        self,
        predictions: list[dict],
    ) -> list[dict]:
        """Identify periods of elevated risk in predictions."""
        risk_periods = []
        in_risk = False
        risk_start = None

        for p in predictions:
            effectiveness = p["effectiveness"]

            if effectiveness < 77 and not in_risk:
                # Start of risk period
                in_risk = True
                risk_start = p["timestamp"]
            elif effectiveness >= 77 and in_risk:
                # End of risk period
                in_risk = False
                risk_periods.append(
                    {
                        "start": risk_start,
                        "end": p["timestamp"],
                        "min_effectiveness": min(
                            x["effectiveness"]
                            for x in predictions
                            if risk_start <= x["timestamp"] <= p["timestamp"]
                        ),
                    }
                )

                # Close any open risk period
        if in_risk and predictions:
            risk_periods.append(
                {
                    "start": risk_start,
                    "end": predictions[-1]["timestamp"],
                    "min_effectiveness": predictions[-1]["effectiveness"],
                }
            )

        return risk_periods

    def export_to_json(self, data: Any, filepath: str) -> None:
        """Export data to JSON file."""
        with open(filepath, "w") as f:
            if hasattr(data, "to_dict"):
                json.dump(data.to_dict(), f, indent=2)
            else:
                json.dump(data, f, indent=2)
        logger.info(f"Exported FRMS data to {filepath}")
