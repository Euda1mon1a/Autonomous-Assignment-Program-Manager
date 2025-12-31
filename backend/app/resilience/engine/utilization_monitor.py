"""
Utilization Monitor.

Implements queuing theory-based utilization monitoring using M/M/c queue model.
Key threshold: 80% utilization where queue length begins exponential growth.

Based on:
- Erlang C formula for M/M/c queues
- Kingman's VUT equation
- Little's Law (L = λW)
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

import numpy as np
from scipy.special import factorial


@dataclass
class UtilizationSnapshot:
    """Point-in-time utilization measurement."""

    timestamp: datetime
    period_start: date
    period_end: date
    total_capacity: float  # Total available hours
    utilized_capacity: float  # Scheduled hours
    utilization_ratio: float  # utilized / total (0.0-1.0+)
    num_servers: int  # Number of residents/faculty (c in M/M/c)
    arrival_rate: float  # λ - requests per hour
    service_rate: float  # μ - service per hour per server
    traffic_intensity: float  # ρ = λ/(c*μ)
    queue_length: float | None = None  # Expected queue length (from Erlang C)
    wait_time: float | None = None  # Expected wait time (hours)


@dataclass
class UtilizationTrend:
    """Historical utilization trend analysis."""

    snapshots: list[UtilizationSnapshot]
    mean_utilization: float
    std_utilization: float
    trend_slope: float  # Linear trend coefficient
    is_increasing: bool
    days_above_80pct: int
    days_above_90pct: int
    days_above_95pct: int
    max_utilization: float
    max_utilization_date: date


class UtilizationMonitor:
    """
    Monitor utilization using queuing theory.

    Key concept: In M/M/c queue, when ρ (traffic intensity) approaches 1.0,
    queue length grows exponentially. The 80% threshold provides safety margin.
    """

    # Critical thresholds from queuing theory
    SAFE_UTILIZATION = 0.80  # Queue stable, manageable wait times
    WARNING_UTILIZATION = 0.90  # Queue growing, wait times increasing
    DANGER_UTILIZATION = 0.95  # Queue exploding, system unstable
    CRITICAL_UTILIZATION = 0.98  # System collapse imminent

    def calculate_snapshot(
        self,
        period_start: date,
        period_end: date,
        total_capacity: float,
        utilized_capacity: float,
        num_servers: int,
        arrival_rate: float | None = None,
        service_rate: float | None = None,
    ) -> UtilizationSnapshot:
        """
        Calculate utilization snapshot for a time period.

        Args:
            period_start: Start of measurement period
            period_end: End of measurement period
            total_capacity: Total available hours
            utilized_capacity: Scheduled hours
            num_servers: Number of residents/faculty (c in M/M/c)
            arrival_rate: Arrival rate λ (requests/hour) - optional
            service_rate: Service rate μ (service/hour/server) - optional

        Returns:
            UtilizationSnapshot with metrics and queue predictions
        """
        utilization_ratio = (
            utilized_capacity / total_capacity if total_capacity > 0 else 0.0
        )

        # Calculate traffic intensity if rates provided
        traffic_intensity = 0.0
        queue_length = None
        wait_time = None

        if arrival_rate is not None and service_rate is not None and service_rate > 0:
            traffic_intensity = arrival_rate / (num_servers * service_rate)

            # Calculate Erlang C (probability of queuing)
            if traffic_intensity < 1.0:  # System stable
                erlang_c = self._erlang_c(arrival_rate, service_rate, num_servers)
                # Expected queue length: L_q = Erlang_C * ρ/(1-ρ)
                queue_length = erlang_c * traffic_intensity / (1.0 - traffic_intensity)
                # Expected wait time: W_q = L_q / λ (Little's Law)
                wait_time = queue_length / arrival_rate if arrival_rate > 0 else 0.0

        return UtilizationSnapshot(
            timestamp=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            total_capacity=total_capacity,
            utilized_capacity=utilized_capacity,
            utilization_ratio=utilization_ratio,
            num_servers=num_servers,
            arrival_rate=arrival_rate or 0.0,
            service_rate=service_rate or 0.0,
            traffic_intensity=traffic_intensity,
            queue_length=queue_length,
            wait_time=wait_time,
        )

    def _erlang_c(
        self, arrival_rate: float, service_rate: float, num_servers: int
    ) -> float:
        """
        Calculate Erlang C formula - probability of queuing in M/M/c system.

        Erlang C = [A^c / c! * c/(c-A)] / [Σ(A^k/k!) + A^c/c! * c/(c-A)]
        where A = λ/μ (total offered load)

        Args:
            arrival_rate: λ - requests per hour
            service_rate: μ - service per hour per server
            num_servers: c - number of servers

        Returns:
            Probability that arriving customer must wait (0.0-1.0)
        """
        A = arrival_rate / service_rate  # Total offered load

        if num_servers <= A:
            return 1.0  # System unstable, queue infinite

        # Calculate numerator: A^c / c! * c/(c-A)
        numerator = (A**num_servers / factorial(num_servers)) * (
            num_servers / (num_servers - A)
        )

        # Calculate denominator: sum + numerator
        sum_terms = sum(A**k / factorial(k) for k in range(num_servers))
        denominator = sum_terms + numerator

        return numerator / denominator if denominator > 0 else 0.0

    def analyze_trend(
        self, snapshots: list[UtilizationSnapshot], window_days: int = 28
    ) -> UtilizationTrend:
        """
        Analyze utilization trend over time.

        Args:
            snapshots: Historical utilization snapshots
            window_days: Analysis window (default 28 days for ACGME)

        Returns:
            UtilizationTrend with statistical analysis
        """
        if not snapshots:
            return UtilizationTrend(
                snapshots=[],
                mean_utilization=0.0,
                std_utilization=0.0,
                trend_slope=0.0,
                is_increasing=False,
                days_above_80pct=0,
                days_above_90pct=0,
                days_above_95pct=0,
                max_utilization=0.0,
                max_utilization_date=date.today(),
            )

        # Sort by date
        sorted_snapshots = sorted(snapshots, key=lambda s: s.period_start)

        # Calculate statistics
        utilizations = np.array([s.utilization_ratio for s in sorted_snapshots])
        mean_util = float(np.mean(utilizations))
        std_util = float(np.std(utilizations))

        # Linear trend (slope of least squares fit)
        if len(utilizations) > 1:
            x = np.arange(len(utilizations))
            trend_slope = float(np.polyfit(x, utilizations, 1)[0])
            is_increasing = trend_slope > 0.001  # > 0.1% per day
        else:
            trend_slope = 0.0
            is_increasing = False

        # Count days above thresholds
        days_above_80 = sum(1 for u in utilizations if u >= 0.80)
        days_above_90 = sum(1 for u in utilizations if u >= 0.90)
        days_above_95 = sum(1 for u in utilizations if u >= 0.95)

        # Find maximum
        max_idx = int(np.argmax(utilizations))
        max_util = float(utilizations[max_idx])
        max_date = sorted_snapshots[max_idx].period_start

        return UtilizationTrend(
            snapshots=sorted_snapshots,
            mean_utilization=mean_util,
            std_utilization=std_util,
            trend_slope=trend_slope,
            is_increasing=is_increasing,
            days_above_80pct=days_above_80,
            days_above_90pct=days_above_90,
            days_above_95pct=days_above_95,
            max_utilization=max_util,
            max_utilization_date=max_date,
        )

    def predict_queue_explosion(
        self, current_utilization: float, growth_rate: float, days_ahead: int = 7
    ) -> tuple[bool, int]:
        """
        Predict when queue will explode (cross 95% utilization).

        Args:
            current_utilization: Current utilization ratio
            growth_rate: Daily growth rate (e.g., 0.01 = 1% per day)
            days_ahead: Prediction horizon

        Returns:
            (will_explode: bool, days_until: int)
        """
        if current_utilization >= 0.95:
            return True, 0

        if growth_rate <= 0:
            return False, days_ahead + 1

        # Project utilization forward
        for day in range(1, days_ahead + 1):
            projected = current_utilization * (1 + growth_rate) ** day
            if projected >= 0.95:
                return True, day

        return False, days_ahead + 1

    def recommend_capacity_adjustment(
        self, current_utilization: float, target_utilization: float = 0.75
    ) -> dict:
        """
        Recommend capacity adjustment to reach target utilization.

        Args:
            current_utilization: Current utilization ratio
            target_utilization: Desired target (default 75% for safety)

        Returns:
            Dict with adjustment recommendations
        """
        if current_utilization <= target_utilization:
            return {
                "action": "none",
                "current": current_utilization,
                "target": target_utilization,
                "capacity_change_pct": 0.0,
                "message": "Utilization within target range",
            }

        # Calculate required capacity increase
        # If util = used/capacity, and target_util = used/new_capacity
        # Then: new_capacity = used/target_util = capacity * (util/target_util)
        capacity_multiplier = current_utilization / target_utilization
        capacity_increase_pct = (capacity_multiplier - 1.0) * 100

        if capacity_increase_pct < 10:
            action = "monitor"
            message = (
                f"Increase capacity by {capacity_increase_pct:.1f}% or reduce load"
            )
        elif capacity_increase_pct < 25:
            action = "adjust"
            message = f"Recommend {capacity_increase_pct:.1f}% capacity increase"
        else:
            action = "urgent"
            message = f"URGENT: Need {capacity_increase_pct:.1f}% capacity increase"

        return {
            "action": action,
            "current": current_utilization,
            "target": target_utilization,
            "capacity_change_pct": capacity_increase_pct,
            "message": message,
        }
