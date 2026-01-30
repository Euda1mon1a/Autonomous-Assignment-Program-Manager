"""
Metrics collection and statistical analysis for resilience simulations.

This module provides a comprehensive system for collecting, analyzing, and
summarizing metrics during simulation runs. It supports time series data,
counters, gauges, and events with statistical analysis capabilities.
"""

import statistics
from dataclasses import dataclass
from uuid import UUID


@dataclass
class TimeSeriesPoint:
    """A single data point in a time series."""

    time: float
    value: float
    label: str | None = None


@dataclass
class MetricsSummary:
    """Statistical summary of a metric."""

    name: str
    count: int
    mean: float
    std: float
    min_val: float
    max_val: float
    p25: float
    p50: float  # median
    p75: float
    p95: float
    p99: float


class MetricsCollector:
    """
    Core metrics collection engine supporting multiple metric types.

    Supports:
    - Time series: ordered (time, value) pairs
    - Counters: monotonically increasing integers
    - Gauges: current values that can increase or decrease
    - Events: timestamped occurrences with metadata
    """

    def __init__(self) -> None:
        """Initialize empty metrics storage."""
        self._time_series: dict[str, list[TimeSeriesPoint]] = {}
        self._counters: dict[str, int] = {}
        self._events: list[dict] = []
        self._gauges: dict[str, float] = {}

    def record_value(
        self, metric: str, time: float, value: float, label: str | None = None
    ) -> None:
        """
        Record a time series value.

        Args:
            metric: Name of the metric
            time: Timestamp
            value: Metric value
            label: Optional label for categorization
        """
        if metric not in self._time_series:
            self._time_series[metric] = []

        point = TimeSeriesPoint(time=time, value=value, label=label)
        self._time_series[metric].append(point)

    def increment(self, counter: str, amount: int = 1) -> None:
        """
        Increment a counter.

        Args:
            counter: Counter name
            amount: Amount to increment by (default: 1)
        """
        if counter not in self._counters:
            self._counters[counter] = 0
        self._counters[counter] += amount

    def decrement(self, counter: str, amount: int = 1) -> None:
        """
        Decrement a counter.

        Args:
            counter: Counter name
            amount: Amount to decrement by (default: 1)
        """
        if counter not in self._counters:
            self._counters[counter] = 0
        self._counters[counter] -= amount

    def set_gauge(self, name: str, value: float) -> None:
        """
        Set a gauge to a specific value.

        Args:
            name: Gauge name
            value: Value to set
        """
        self._gauges[name] = value

    def record_event(self, event_type: str, time: float, data: dict) -> None:
        """
        Record an event with metadata.

        Args:
            event_type: Type of event
            time: Timestamp
            data: Event metadata
        """
        event = {"type": event_type, "time": time, **data}
        self._events.append(event)

    def get_counter(self, name: str) -> int:
        """
        Get current counter value.

        Args:
            name: Counter name

        Returns:
            Counter value (0 if not found)
        """
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float | None:
        """
        Get current gauge value.

        Args:
            name: Gauge name

        Returns:
            Gauge value or None if not found
        """
        return self._gauges.get(name)

    def get_time_series(self, metric: str) -> list[TimeSeriesPoint]:
        """
        Get all time series points for a metric.

        Args:
            metric: Metric name

        Returns:
            List of time series points (empty if not found)
        """
        return self._time_series.get(metric, [])

    def get_summary(self, metric: str) -> MetricsSummary | None:
        """
        Calculate statistical summary for a metric.

        Args:
            metric: Metric name

        Returns:
            MetricsSummary or None if metric not found or empty
        """
        if metric not in self._time_series:
            return None

        points = self._time_series[metric]
        if not points:
            return None

        values = [p.value for p in points]
        count = len(values)

        # Handle edge case: single data point
        if count == 1:
            val = values[0]
            return MetricsSummary(
                name=metric,
                count=1,
                mean=val,
                std=0.0,
                min_val=val,
                max_val=val,
                p25=val,
                p50=val,
                p75=val,
                p95=val,
                p99=val,
            )

            # Calculate statistics
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        min_val = min(values)
        max_val = max(values)

        # Calculate percentiles
        sorted_values = sorted(values)
        p25 = statistics.quantiles(sorted_values, n=4)[0]  # 25th percentile
        p50 = statistics.median(sorted_values)
        p75 = statistics.quantiles(sorted_values, n=4)[2]  # 75th percentile

        # For 95th and 99th percentiles, use quantiles with n=100
        if count >= 100:
            percentiles = statistics.quantiles(sorted_values, n=100)
            p95 = percentiles[94]  # 95th percentile (index 94 of 99)
            p99 = percentiles[98]  # 99th percentile (index 98 of 99)
        else:
            # For smaller datasets, approximate with available data
            p95_idx = int(0.95 * count)
            p99_idx = int(0.99 * count)
            p95 = sorted_values[min(p95_idx, count - 1)]
            p99 = sorted_values[min(p99_idx, count - 1)]

        return MetricsSummary(
            name=metric,
            count=count,
            mean=mean_val,
            std=std_val,
            min_val=min_val,
            max_val=max_val,
            p25=p25,
            p50=p50,
            p75=p75,
            p95=p95,
            p99=p99,
        )

    def get_all_summaries(self) -> dict[str, MetricsSummary]:
        """
        Get statistical summaries for all metrics.

        Returns:
            Dictionary mapping metric names to summaries
        """
        summaries = {}
        for metric in self._time_series.keys():
            summary = self.get_summary(metric)
            if summary is not None:
                summaries[metric] = summary
        return summaries

    def get_events(self, event_type: str | None = None) -> list[dict]:
        """
        Get events, optionally filtered by type.

        Args:
            event_type: Optional event type filter

        Returns:
            List of events
        """
        if event_type is None:
            return self._events.copy()

        return [e for e in self._events if e.get("type") == event_type]

    def to_dict(self) -> dict:
        """
        Export all metrics data to a dictionary.

        Returns:
            Dictionary containing all metrics data
        """
        return {
            "time_series": {
                name: [
                    {"time": p.time, "value": p.value, "label": p.label} for p in points
                ]
                for name, points in self._time_series.items()
            },
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "events": self._events.copy(),
        }

    def reset(self) -> None:
        """Clear all metrics data."""
        self._time_series.clear()
        self._counters.clear()
        self._events.clear()
        self._gauges.clear()


class SimulationMetrics:
    """
    Higher-level metrics collection for resilience simulations.

    Provides convenience methods for tracking simulation-specific metrics
    like faculty counts, coverage rates, zone status, and cascade events.
    """

    def __init__(self, collector: MetricsCollector) -> None:
        """
        Initialize simulation metrics.

        Args:
            collector: Underlying metrics collector
        """
        self.collector = collector

    def record_faculty_count(self, time: float, count: int) -> None:
        """
        Record faculty count at a point in time.

        Args:
            time: Timestamp
            count: Number of faculty members
        """
        self.collector.record_value("faculty_count", time, float(count))

    def record_coverage_rate(self, time: float, rate: float) -> None:
        """
        Record coverage rate at a point in time.

        Args:
            time: Timestamp
            rate: Coverage rate (0.0 to 1.0)
        """
        self.collector.record_value("coverage_rate", time, rate)

    def record_zone_status(self, time: float, zone_id: UUID, status: str) -> None:
        """
        Record zone status change.

        Args:
            time: Timestamp
            zone_id: Zone identifier
            status: New status
        """
        self.collector.record_event(
            "zone_status_change", time, {"zone_id": str(zone_id), "status": status}
        )

    def record_cascade_event(self, time: float, zones_affected: int) -> None:
        """
        Record a cascade event.

        Args:
            time: Timestamp
            zones_affected: Number of zones affected
        """
        self.collector.increment("cascade_events")
        self.collector.record_event("cascade", time, {"zones_affected": zones_affected})

    def record_borrowing_attempt(self, time: float, approved: bool) -> None:
        """
        Record a faculty borrowing attempt.

        Args:
            time: Timestamp
            approved: Whether the attempt was approved
        """
        self.collector.increment("borrowing_attempts")
        if approved:
            self.collector.increment("borrowing_approved")

        self.collector.record_event("borrowing_attempt", time, {"approved": approved})

    def get_coverage_summary(self) -> MetricsSummary | None:
        """
        Get statistical summary of coverage rates.

        Returns:
            MetricsSummary or None if no data
        """
        return self.collector.get_summary("coverage_rate")

    def get_faculty_summary(self) -> MetricsSummary | None:
        """
        Get statistical summary of faculty counts.

        Returns:
            MetricsSummary or None if no data
        """
        return self.collector.get_summary("faculty_count")

    def cascade_count(self) -> int:
        """
        Get total number of cascade events.

        Returns:
            Number of cascade events
        """
        return self.collector.get_counter("cascade_events")

    def borrowing_success_rate(self) -> float:
        """
        Calculate borrowing success rate.

        Returns:
            Success rate (0.0 to 1.0), or 0.0 if no attempts
        """
        attempts = self.collector.get_counter("borrowing_attempts")
        if attempts == 0:
            return 0.0

        approved = self.collector.get_counter("borrowing_approved")
        return approved / attempts
