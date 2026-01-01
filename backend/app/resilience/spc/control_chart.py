"""
Statistical Process Control Charts.

SPC from semiconductor manufacturing and Six Sigma.
Monitors process stability using control limits (mean ± 3σ).

Chart types:
- X-bar (Individual measurements)
- CUSUM (Cumulative sum for drift detection)
- EWMA (Exponentially weighted moving average)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class ControlChartType(str, Enum):
    """Control chart type."""

    XBAR = "xbar"  ***REMOVED*** Individual measurements
    CUSUM = "cusum"  ***REMOVED*** Cumulative sum
    EWMA = "ewma"  ***REMOVED*** Exponentially weighted moving average


@dataclass
class ControlLimits:
    """Control chart limits."""

    center_line: float  ***REMOVED*** Mean or target
    ucl: float  ***REMOVED*** Upper control limit (mean + 3σ)
    lcl: float  ***REMOVED*** Lower control limit (mean - 3σ)
    uwl: float  ***REMOVED*** Upper warning limit (mean + 2σ)
    lwl: float  ***REMOVED*** Lower warning limit (mean - 2σ)
    sigma: float  ***REMOVED*** Process standard deviation


@dataclass
class ControlChartPoint:
    """Point on control chart."""

    timestamp: datetime
    value: float
    is_in_control: bool
    violated_rule: str | None = None  ***REMOVED*** Which rule was violated
    zone: str = "A"  ***REMOVED*** Zone: A (within 1σ), B (1-2σ), C (2-3σ), Out (>3σ)


class ControlChart:
    """
    SPC control chart for monitoring resilience metrics.

    Implements Shewhart control charts with 3-sigma limits.
    """

    def __init__(
        self,
        chart_type: ControlChartType = ControlChartType.XBAR,
        sigma_multiplier: float = 3.0,
    ):
        """
        Initialize control chart.

        Args:
            chart_type: Type of control chart
            sigma_multiplier: Multiplier for control limits (default 3.0)
        """
        self.chart_type = chart_type
        self.sigma_multiplier = sigma_multiplier
        self.limits: ControlLimits | None = None
        self.data_points: list[float] = []

    def calculate_limits(
        self,
        baseline_data: list[float],
        target: float | None = None,
    ) -> ControlLimits:
        """
        Calculate control limits from baseline data.

        Args:
            baseline_data: Historical in-control data
            target: Optional target value (default: mean of baseline)

        Returns:
            ControlLimits object
        """
        logger.info("Calculating %s control limits from %d baseline points", self.chart_type, len(baseline_data))
        if len(baseline_data) < 5:
            logger.error("Insufficient baseline data: need >= 5 points, got %d", len(baseline_data))
            raise ValueError("Need at least 5 baseline points")

        data = np.array(baseline_data)
        mean = float(np.mean(data))
        sigma = float(np.std(data, ddof=1))  ***REMOVED*** Sample std dev

        center_line = target if target is not None else mean
        logger.debug("Control limits: center=%.2f, sigma=%.2f", center_line, sigma)

        ***REMOVED*** Calculate control limits
        ucl = center_line + self.sigma_multiplier * sigma
        lcl = center_line - self.sigma_multiplier * sigma

        ***REMOVED*** Warning limits (2σ)
        uwl = center_line + 2.0 * sigma
        lwl = center_line - 2.0 * sigma

        limits = ControlLimits(
            center_line=center_line,
            ucl=ucl,
            lcl=lcl,
            uwl=uwl,
            lwl=lwl,
            sigma=sigma,
        )

        self.limits = limits
        return limits

    def add_point(
        self,
        value: float,
        timestamp: datetime | None = None,
    ) -> ControlChartPoint:
        """
        Add point to control chart and check limits.

        Args:
            value: Measurement value
            timestamp: Timestamp (default: now)

        Returns:
            ControlChartPoint with analysis
        """
        if self.limits is None:
            raise ValueError("Must calculate limits before adding points")

        if timestamp is None:
            timestamp = datetime.now()

        self.data_points.append(value)

        ***REMOVED*** Determine zone
        zone = self._determine_zone(value)

        ***REMOVED*** Check if in control
        is_in_control = self.limits.lcl <= value <= self.limits.ucl
        violated_rule = None if is_in_control else "out_of_control"

        return ControlChartPoint(
            timestamp=timestamp,
            value=value,
            is_in_control=is_in_control,
            violated_rule=violated_rule,
            zone=zone,
        )

    def _determine_zone(self, value: float) -> str:
        """
        Determine which zone value falls in.

        Zones (from center line):
        - A: within 1σ
        - B: between 1σ and 2σ
        - C: between 2σ and 3σ
        - Out: beyond 3σ
        """
        if self.limits is None:
            return "unknown"

        distance = abs(value - self.limits.center_line)
        sigma = self.limits.sigma

        if distance > 3 * sigma:
            return "Out"
        elif distance > 2 * sigma:
            return "C"
        elif distance > sigma:
            return "B"
        else:
            return "A"

    def get_capability_indices(self) -> dict:
        """
        Calculate process capability indices (Cp, Cpk).

        Cp = (UCL - LCL) / (6σ) - process capability
        Cpk = min((UCL - μ)/(3σ), (μ - LCL)/(3σ)) - centered capability

        Returns:
            Dict with capability metrics
        """
        if self.limits is None or not self.data_points:
            return {"cp": 0.0, "cpk": 0.0, "interpretation": "insufficient_data"}

        sigma = self.limits.sigma
        if sigma == 0:
            return {
                "cp": float("inf"),
                "cpk": float("inf"),
                "interpretation": "no_variation",
            }

        ***REMOVED*** Process capability
        cp = (self.limits.ucl - self.limits.lcl) / (6.0 * sigma)

        ***REMOVED*** Process mean
        process_mean = float(np.mean(self.data_points))

        ***REMOVED*** Centered capability
        cpu = (self.limits.ucl - process_mean) / (3.0 * sigma)
        cpl = (process_mean - self.limits.lcl) / (3.0 * sigma)
        cpk = min(cpu, cpl)

        ***REMOVED*** Interpretation
        if cpk >= 2.0:
            interpretation = "excellent"  ***REMOVED*** Six Sigma
        elif cpk >= 1.33:
            interpretation = "good"  ***REMOVED*** Four Sigma
        elif cpk >= 1.0:
            interpretation = "adequate"
        else:
            interpretation = "poor"

        return {
            "cp": round(cp, 2),
            "cpk": round(cpk, 2),
            "cpu": round(cpu, 2),
            "cpl": round(cpl, 2),
            "interpretation": interpretation,
            "process_mean": round(process_mean, 2),
        }

    def detect_trends(self, window_size: int = 7) -> dict:
        """
        Detect trends in recent data.

        Args:
            window_size: Number of recent points to analyze

        Returns:
            Dict with trend analysis
        """
        if len(self.data_points) < window_size:
            return {"trend": "insufficient_data", "slope": 0.0}

        recent_data = self.data_points[-window_size:]
        x = np.arange(len(recent_data))
        y = np.array(recent_data)

        ***REMOVED*** Linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        ***REMOVED*** Determine trend
        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        return {
            "trend": trend,
            "slope": round(slope, 4),
            "recent_mean": round(float(np.mean(recent_data)), 2),
            "recent_std": round(float(np.std(recent_data)), 2),
        }


@dataclass
class CUSUMPoint:
    """CUSUM chart point."""

    timestamp: datetime
    value: float
    cusum_high: float  ***REMOVED*** Cumulative sum for upward drift
    cusum_low: float  ***REMOVED*** Cumulative sum for downward drift
    is_in_control: bool


class CUSUMChart:
    """
    CUSUM (Cumulative Sum) Control Chart.

    More sensitive to small shifts than Shewhart charts.
    Detects drift in process mean.
    """

    def __init__(
        self,
        target: float,
        sigma: float,
        k: float = 0.5,  ***REMOVED*** Allowable slack (0.5σ typical)
        h: float = 4.0,  ***REMOVED*** Decision interval (4-5σ typical)
    ):
        """
        Initialize CUSUM chart.

        Args:
            target: Target value (process mean)
            sigma: Process standard deviation
            k: Allowable slack (in σ units)
            h: Decision interval (in σ units)
        """
        self.target = target
        self.sigma = sigma
        self.k = k * sigma  ***REMOVED*** Convert to absolute units
        self.h = h * sigma
        self.cusum_high = 0.0  ***REMOVED*** Detect upward shifts
        self.cusum_low = 0.0  ***REMOVED*** Detect downward shifts

    def add_point(
        self,
        value: float,
        timestamp: datetime | None = None,
    ) -> CUSUMPoint:
        """
        Add point to CUSUM chart.

        Args:
            value: Measurement value
            timestamp: Timestamp

        Returns:
            CUSUMPoint with CUSUM values
        """
        if timestamp is None:
            timestamp = datetime.now()

        ***REMOVED*** Update CUSUM for upward shift
        self.cusum_high = max(0, self.cusum_high + (value - self.target) - self.k)

        ***REMOVED*** Update CUSUM for downward shift
        self.cusum_low = max(0, self.cusum_low + (self.target - value) - self.k)

        ***REMOVED*** Check if out of control
        is_in_control = (self.cusum_high < self.h) and (self.cusum_low < self.h)

        return CUSUMPoint(
            timestamp=timestamp,
            value=value,
            cusum_high=self.cusum_high,
            cusum_low=self.cusum_low,
            is_in_control=is_in_control,
        )

    def reset(self):
        """Reset CUSUM values."""
        self.cusum_high = 0.0
        self.cusum_low = 0.0


@dataclass
class EWMAPoint:
    """EWMA chart point."""

    timestamp: datetime
    value: float
    ewma: float  ***REMOVED*** Exponentially weighted moving average
    ucl: float  ***REMOVED*** Upper control limit
    lcl: float  ***REMOVED*** Lower control limit
    is_in_control: bool


class EWMAChart:
    """
    EWMA (Exponentially Weighted Moving Average) Chart.

    Smooths data and is sensitive to small shifts.
    Good for autocorrelated data.
    """

    def __init__(
        self,
        target: float,
        sigma: float,
        lambda_: float = 0.2,  ***REMOVED*** Weighting factor (0.2-0.3 typical)
        L: float = 3.0,  ***REMOVED*** Control limit multiplier
    ):
        """
        Initialize EWMA chart.

        Args:
            target: Target value
            sigma: Process standard deviation
            lambda_: Weighting factor (0 < λ ≤ 1)
            L: Control limit width (in σ units)
        """
        self.target = target
        self.sigma = sigma
        self.lambda_ = lambda_
        self.L = L
        self.ewma = target
        self.n = 0  ***REMOVED*** Number of observations

    def add_point(
        self,
        value: float,
        timestamp: datetime | None = None,
    ) -> EWMAPoint:
        """
        Add point to EWMA chart.

        Args:
            value: Measurement value
            timestamp: Timestamp

        Returns:
            EWMAPoint with EWMA value and limits
        """
        if timestamp is None:
            timestamp = datetime.now()

        self.n += 1

        ***REMOVED*** Update EWMA: z_t = λx_t + (1-λ)z_{t-1}
        self.ewma = self.lambda_ * value + (1 - self.lambda_) * self.ewma

        ***REMOVED*** Calculate control limits
        ***REMOVED*** σ_z = σ√[λ/(2-λ) × (1-(1-λ)^{2n})]
        variance_factor = (self.lambda_ / (2 - self.lambda_)) * (
            1 - (1 - self.lambda_) ** (2 * self.n)
        )
        sigma_ewma = self.sigma * np.sqrt(variance_factor)

        ucl = self.target + self.L * sigma_ewma
        lcl = self.target - self.L * sigma_ewma

        ***REMOVED*** Check control
        is_in_control = lcl <= self.ewma <= ucl

        return EWMAPoint(
            timestamp=timestamp,
            value=value,
            ewma=self.ewma,
            ucl=ucl,
            lcl=lcl,
            is_in_control=is_in_control,
        )
