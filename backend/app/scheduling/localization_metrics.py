"""
Localization Metrics for Schedule Update Scope Tracking.

Provides observability and monitoring for Anderson localization performance:
- Update scope histograms
- Localization length trends
- Barrier strength evolution
- Escape rate tracking

Integrates with resilience framework for health monitoring.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.scheduling.anderson_localization import (
    Disruption,
    DisruptionType,
    LocalizationRegion,
)

logger = logging.getLogger(__name__)


class LocalizationQuality(str, Enum):
    """Quality classification for localization regions."""

    EXCELLENT = "excellent"  # < 10% scope, strong barriers
    GOOD = "good"  # 10-20% scope, moderate barriers
    FAIR = "fair"  # 20-40% scope, weak barriers
    POOR = "poor"  # > 40% scope, cascade risk


@dataclass
class LocalizationEvent:
    """Record of a single localization computation."""

    timestamp: datetime
    disruption_type: DisruptionType
    region: LocalizationRegion
    computation_time_ms: float
    quality: LocalizationQuality
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LocalizationMetrics:
    """
    Aggregated metrics for localization performance.

    Tracks update scope efficiency and localization quality over time.
    """

    total_events: int = 0
    localized_count: int = 0  # Successfully localized (< 20% scope)
    extended_count: int = 0  # Extended regions (20-60% scope)
    global_count: int = 0  # Global cascades (> 60% scope)

    # Scope metrics
    avg_region_size: float = 0.0
    avg_localization_length: float = 0.0
    avg_barrier_strength: float = 0.0
    avg_escape_probability: float = 0.0

    # Performance metrics
    avg_computation_time_ms: float = 0.0
    p95_computation_time_ms: float = 0.0
    p99_computation_time_ms: float = 0.0

    # Quality distribution
    quality_distribution: dict[LocalizationQuality, int] = field(
        default_factory=lambda: defaultdict(int)
    )

    # Per-disruption-type metrics
    metrics_by_type: dict[DisruptionType, dict[str, float]] = field(
        default_factory=lambda: defaultdict(dict)
    )

    def __repr__(self) -> str:
        localization_rate = (
            (self.localized_count / self.total_events * 100)
            if self.total_events > 0
            else 0.0
        )
        return (
            f"LocalizationMetrics("
            f"total={self.total_events}, "
            f"localized_rate={localization_rate:.1f}%, "
            f"avg_size={self.avg_region_size:.0f}, "
            f"avg_length={self.avg_localization_length:.1f}d)"
        )


class LocalizationMetricsTracker:
    """
    Tracks and aggregates localization metrics over time.

    Provides insights into:
    - How well updates are being localized
    - Trends in localization quality
    - Performance characteristics
    """

    def __init__(self, window_size: int = 100):
        """
        Initialize metrics tracker.

        Args:
            window_size: Number of recent events to track for aggregation
        """
        self.window_size = window_size
        self.events: list[LocalizationEvent] = []
        self.metrics = LocalizationMetrics()

    def record_event(
        self,
        disruption: Disruption,
        region: LocalizationRegion,
        computation_time_ms: float,
    ) -> LocalizationEvent:
        """
        Record a localization event and update metrics.

        Args:
            disruption: Disruption that was localized
            region: Computed localization region
            computation_time_ms: Time to compute region

        Returns:
            Localization event record
        """
        # Classify quality
        quality = self._classify_quality(region)

        # Create event
        event = LocalizationEvent(
            timestamp=datetime.utcnow(),
            disruption_type=disruption.disruption_type,
            region=region,
            computation_time_ms=computation_time_ms,
            quality=quality,
            metadata={
                "person_id": str(disruption.person_id)
                if disruption.person_id
                else None,
                "num_blocks": len(disruption.block_ids),
            },
        )

        # Add to event history
        self.events.append(event)

        # Trim to window size
        if len(self.events) > self.window_size:
            self.events = self.events[-self.window_size :]

        # Update aggregated metrics
        self._update_metrics()

        logger.info(
            f"Recorded localization event: {disruption.disruption_type.value} -> "
            f"{quality.value} (size={region.region_size}, "
            f"length={region.localization_length:.1f}d)"
        )

        return event

    def _classify_quality(self, region: LocalizationRegion) -> LocalizationQuality:
        """
        Classify localization quality based on region characteristics.

        Criteria:
        - Region size (% of total schedule)
        - Barrier strength
        - Escape probability
        """
        # Estimate total schedule size (rough heuristic)
        # In real implementation, would get from context
        estimated_total_size = 1000  # assignments

        scope_fraction = region.region_size / estimated_total_size

        # Excellent: Small scope + strong barriers
        if (
            scope_fraction < 0.1
            and region.barrier_strength > 0.6
            and region.escape_probability < 0.2
        ):
            return LocalizationQuality.EXCELLENT

        # Good: Moderate scope, decent barriers
        if (
            scope_fraction < 0.2
            and region.barrier_strength > 0.4
            and region.escape_probability < 0.4
        ):
            return LocalizationQuality.GOOD

        # Fair: Larger scope or weaker barriers
        if scope_fraction < 0.4 and region.escape_probability < 0.6:
            return LocalizationQuality.FAIR

        # Poor: Large scope or high cascade risk
        return LocalizationQuality.POOR

    def _update_metrics(self) -> None:
        """Update aggregated metrics from event history."""
        if not self.events:
            return

        # Reset metrics
        self.metrics = LocalizationMetrics()
        self.metrics.total_events = len(self.events)

        # Count by region type
        for event in self.events:
            if event.region.region_type == "localized":
                self.metrics.localized_count += 1
            elif event.region.region_type == "extended":
                self.metrics.extended_count += 1
            elif event.region.region_type == "global":
                self.metrics.global_count += 1

            # Update quality distribution
            self.metrics.quality_distribution[event.quality] += 1

        # Compute averages
        total = len(self.events)
        self.metrics.avg_region_size = (
            sum(e.region.region_size for e in self.events) / total
        )
        self.metrics.avg_localization_length = (
            sum(e.region.localization_length for e in self.events) / total
        )
        self.metrics.avg_barrier_strength = (
            sum(e.region.barrier_strength for e in self.events) / total
        )
        self.metrics.avg_escape_probability = (
            sum(e.region.escape_probability for e in self.events) / total
        )
        self.metrics.avg_computation_time_ms = (
            sum(e.computation_time_ms for e in self.events) / total
        )

        # Compute percentiles for computation time
        sorted_times = sorted(e.computation_time_ms for e in self.events)
        p95_idx = int(0.95 * len(sorted_times))
        p99_idx = int(0.99 * len(sorted_times))
        self.metrics.p95_computation_time_ms = sorted_times[p95_idx]
        self.metrics.p99_computation_time_ms = sorted_times[p99_idx]

        # Per-disruption-type metrics
        by_type = defaultdict(list)
        for event in self.events:
            by_type[event.disruption_type].append(event)

        for disruption_type, events in by_type.items():
            if not events:
                continue

            self.metrics.metrics_by_type[disruption_type] = {
                "count": len(events),
                "avg_size": sum(e.region.region_size for e in events) / len(events),
                "avg_length": sum(e.region.localization_length for e in events)
                / len(events),
                "avg_barrier": sum(e.region.barrier_strength for e in events)
                / len(events),
                "localization_rate": sum(
                    1 for e in events if e.region.region_type == "localized"
                )
                / len(events),
            }

    def get_metrics(self) -> LocalizationMetrics:
        """Get current aggregated metrics."""
        return self.metrics

    def get_localization_rate(self) -> float:
        """
        Get localization success rate.

        Returns:
            Fraction of events successfully localized [0-1]
        """
        if self.metrics.total_events == 0:
            return 0.0

        return self.metrics.localized_count / self.metrics.total_events

    def get_quality_distribution(self) -> dict[str, float]:
        """
        Get quality distribution as percentages.

        Returns:
            Dict mapping quality levels to percentages
        """
        if self.metrics.total_events == 0:
            return {}

        total = self.metrics.total_events
        return {
            quality.value: (count / total * 100)
            for quality, count in self.metrics.quality_distribution.items()
        }

    def export_metrics(self) -> dict[str, Any]:
        """
        Export metrics as dictionary for API responses.

        Returns:
            Serializable metrics dictionary
        """
        return {
            "summary": {
                "total_events": self.metrics.total_events,
                "localization_rate": self.get_localization_rate(),
                "avg_region_size": self.metrics.avg_region_size,
                "avg_localization_length": self.metrics.avg_localization_length,
                "avg_barrier_strength": self.metrics.avg_barrier_strength,
            },
            "region_types": {
                "localized": self.metrics.localized_count,
                "extended": self.metrics.extended_count,
                "global": self.metrics.global_count,
            },
            "quality_distribution": self.get_quality_distribution(),
            "performance": {
                "avg_computation_time_ms": self.metrics.avg_computation_time_ms,
                "p95_computation_time_ms": self.metrics.p95_computation_time_ms,
                "p99_computation_time_ms": self.metrics.p99_computation_time_ms,
            },
            "by_disruption_type": {
                dtype.value: metrics
                for dtype, metrics in self.metrics.metrics_by_type.items()
            },
        }


# Pydantic schemas for API responses


class LocalizationRegionResponse(BaseModel):
    """API response for localization region."""

    region_size: int = Field(..., description="Number of assignments in region")
    epicenter_blocks: list[str] = Field(..., description="Origin blocks")
    localization_length: float = Field(
        ..., description="Characteristic decay distance (days)"
    )
    barrier_strength: float = Field(
        ..., ge=0.0, le=1.0, description="Constraint density"
    )
    escape_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of cascade"
    )
    region_type: str = Field(..., description="localized, extended, or global")
    is_localized: bool = Field(..., description="Successfully localized")
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "region_size": 42,
                "epicenter_blocks": ["123e4567-e89b-12d3-a456-426614174000"],
                "localization_length": 5.2,
                "barrier_strength": 0.68,
                "escape_probability": 0.15,
                "region_type": "localized",
                "is_localized": True,
                "metadata": {"disruption_type": "leave_request"},
            }
        }


class LocalizationMetricsResponse(BaseModel):
    """API response for localization metrics."""

    summary: dict[str, float] = Field(..., description="Summary metrics")
    region_types: dict[str, int] = Field(..., description="Distribution by region type")
    quality_distribution: dict[str, float] = Field(
        ..., description="Quality percentages"
    )
    performance: dict[str, float] = Field(..., description="Performance metrics")
    by_disruption_type: dict[str, dict[str, float]] = Field(
        ..., description="Per-disruption-type breakdown"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "total_events": 156,
                    "localization_rate": 0.78,
                    "avg_region_size": 38.5,
                    "avg_localization_length": 6.2,
                    "avg_barrier_strength": 0.54,
                },
                "region_types": {"localized": 122, "extended": 28, "global": 6},
                "quality_distribution": {
                    "excellent": 45.5,
                    "good": 32.1,
                    "fair": 15.4,
                    "poor": 7.0,
                },
                "performance": {
                    "avg_computation_time_ms": 125.3,
                    "p95_computation_time_ms": 350.0,
                    "p99_computation_time_ms": 680.0,
                },
                "by_disruption_type": {
                    "leave_request": {
                        "count": 89,
                        "avg_size": 35.2,
                        "avg_length": 5.8,
                        "avg_barrier": 0.56,
                        "localization_rate": 0.82,
                    }
                },
            }
        }
