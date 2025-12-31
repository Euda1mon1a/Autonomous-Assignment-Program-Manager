"""
Threshold Manager.

Manages dynamic thresholds for resilience metrics using:
- Statistical Process Control (SPC) - 3-sigma control limits
- Adaptive thresholds based on historical data
- Homeostatic feedback loops
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np


@dataclass
class Threshold:
    """Dynamic threshold definition."""

    name: str
    lower_bound: Optional[float]  # None = no lower limit
    upper_bound: Optional[float]  # None = no upper limit
    warning_lower: Optional[float]  # Warning zone
    warning_upper: Optional[float]  # Warning zone
    critical_lower: Optional[float]  # Critical zone
    critical_upper: Optional[float]  # Critical zone
    last_updated: datetime
    sample_count: int  # Number of samples used to calculate
    is_adaptive: bool  # Whether threshold adapts over time


@dataclass
class ThresholdViolation:
    """Threshold violation event."""

    threshold_name: str
    value: float
    bound_violated: str  # "lower", "upper", "warning_lower", etc.
    severity: str  # "warning", "critical"
    timestamp: datetime
    message: str


class ThresholdManager:
    """
    Manage dynamic thresholds with SPC and adaptive control.

    Uses 3-sigma control limits from Statistical Process Control:
    - Control limits: mean ± 3σ (99.7% of data)
    - Warning limits: mean ± 2σ (95% of data)

    Implements homeostatic feedback:
    - Thresholds adapt to changing baseline
    - Sudden shifts trigger alerts
    - Gradual drift is accommodated
    """

    def __init__(self):
        """Initialize threshold manager."""
        self.thresholds: dict[str, Threshold] = {}
        self._historical_data: dict[str, list[float]] = {}

    def create_static_threshold(
        self,
        name: str,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
        warning_lower: Optional[float] = None,
        warning_upper: Optional[float] = None,
        critical_lower: Optional[float] = None,
        critical_upper: Optional[float] = None,
    ) -> Threshold:
        """
        Create a static threshold (does not adapt).

        Args:
            name: Threshold identifier
            lower_bound: Hard lower limit
            upper_bound: Hard upper limit
            warning_lower: Warning lower limit
            warning_upper: Warning upper limit
            critical_lower: Critical lower limit
            critical_upper: Critical upper limit

        Returns:
            Threshold object
        """
        threshold = Threshold(
            name=name,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            warning_lower=warning_lower,
            warning_upper=warning_upper,
            critical_lower=critical_lower,
            critical_upper=critical_upper,
            last_updated=datetime.now(),
            sample_count=0,
            is_adaptive=False,
        )

        self.thresholds[name] = threshold
        return threshold

    def create_adaptive_threshold(
        self,
        name: str,
        initial_samples: list[float],
        sigma_multiplier: float = 3.0,
    ) -> Threshold:
        """
        Create adaptive threshold using SPC control limits.

        Control limits: mean ± (sigma_multiplier × std)
        Warning limits: mean ± (2 × std)

        Args:
            name: Threshold identifier
            initial_samples: Historical data for calculating limits
            sigma_multiplier: Multiplier for control limits (default 3.0)

        Returns:
            Threshold object with calculated limits
        """
        if len(initial_samples) < 5:
            raise ValueError(f"Need at least 5 samples, got {len(initial_samples)}")

        samples = np.array(initial_samples)
        mean = float(np.mean(samples))
        std = float(np.std(samples))

        # Calculate control limits (3-sigma)
        control_limit = sigma_multiplier * std
        warning_limit = 2.0 * std

        threshold = Threshold(
            name=name,
            lower_bound=mean - control_limit,
            upper_bound=mean + control_limit,
            warning_lower=mean - warning_limit,
            warning_upper=mean + warning_limit,
            critical_lower=mean - control_limit,
            critical_upper=mean + control_limit,
            last_updated=datetime.now(),
            sample_count=len(initial_samples),
            is_adaptive=True,
        )

        self.thresholds[name] = threshold
        self._historical_data[name] = list(samples)

        return threshold

    def update_adaptive_threshold(
        self,
        name: str,
        new_samples: list[float],
        max_history: int = 100,
        sigma_multiplier: float = 3.0,
    ) -> Threshold:
        """
        Update adaptive threshold with new data.

        Uses exponentially weighted moving average to balance
        responsiveness vs. stability (homeostatic control).

        Args:
            name: Threshold identifier
            new_samples: New data points
            max_history: Maximum samples to retain
            sigma_multiplier: Multiplier for control limits

        Returns:
            Updated threshold
        """
        if name not in self.thresholds:
            raise ValueError(f"Threshold {name} not found")

        threshold = self.thresholds[name]
        if not threshold.is_adaptive:
            raise ValueError(f"Threshold {name} is not adaptive")

        # Add new samples to history
        history = self._historical_data.get(name, [])
        history.extend(new_samples)

        # Keep only recent samples
        if len(history) > max_history:
            history = history[-max_history:]

        self._historical_data[name] = history

        # Recalculate limits
        samples = np.array(history)
        mean = float(np.mean(samples))
        std = float(np.std(samples))

        control_limit = sigma_multiplier * std
        warning_limit = 2.0 * std

        # Update threshold
        threshold.lower_bound = mean - control_limit
        threshold.upper_bound = mean + control_limit
        threshold.warning_lower = mean - warning_limit
        threshold.warning_upper = mean + warning_limit
        threshold.critical_lower = mean - control_limit
        threshold.critical_upper = mean + control_limit
        threshold.last_updated = datetime.now()
        threshold.sample_count = len(history)

        return threshold

    def check_threshold(self, name: str, value: float) -> Optional[ThresholdViolation]:
        """
        Check if value violates threshold.

        Args:
            name: Threshold identifier
            value: Value to check

        Returns:
            ThresholdViolation if violated, None otherwise
        """
        if name not in self.thresholds:
            raise ValueError(f"Threshold {name} not found")

        threshold = self.thresholds[name]

        # Check critical bounds first
        if threshold.critical_lower is not None and value < threshold.critical_lower:
            return ThresholdViolation(
                threshold_name=name,
                value=value,
                bound_violated="critical_lower",
                severity="critical",
                timestamp=datetime.now(),
                message=f"{name}={value:.2f} below critical lower bound {threshold.critical_lower:.2f}",
            )

        if threshold.critical_upper is not None and value > threshold.critical_upper:
            return ThresholdViolation(
                threshold_name=name,
                value=value,
                bound_violated="critical_upper",
                severity="critical",
                timestamp=datetime.now(),
                message=f"{name}={value:.2f} above critical upper bound {threshold.critical_upper:.2f}",
            )

        # Check warning bounds
        if threshold.warning_lower is not None and value < threshold.warning_lower:
            return ThresholdViolation(
                threshold_name=name,
                value=value,
                bound_violated="warning_lower",
                severity="warning",
                timestamp=datetime.now(),
                message=f"{name}={value:.2f} below warning lower bound {threshold.warning_lower:.2f}",
            )

        if threshold.warning_upper is not None and value > threshold.warning_upper:
            return ThresholdViolation(
                threshold_name=name,
                value=value,
                bound_violated="warning_upper",
                severity="warning",
                timestamp=datetime.now(),
                message=f"{name}={value:.2f} above warning upper bound {threshold.warning_upper:.2f}",
            )

        # Check hard bounds
        if threshold.lower_bound is not None and value < threshold.lower_bound:
            return ThresholdViolation(
                threshold_name=name,
                value=value,
                bound_violated="lower",
                severity="critical",
                timestamp=datetime.now(),
                message=f"{name}={value:.2f} below lower bound {threshold.lower_bound:.2f}",
            )

        if threshold.upper_bound is not None and value > threshold.upper_bound:
            return ThresholdViolation(
                threshold_name=name,
                value=value,
                bound_violated="upper",
                severity="critical",
                timestamp=datetime.now(),
                message=f"{name}={value:.2f} above upper bound {threshold.upper_bound:.2f}",
            )

        return None

    def get_threshold(self, name: str) -> Optional[Threshold]:
        """Get threshold by name."""
        return self.thresholds.get(name)

    def list_thresholds(self) -> list[Threshold]:
        """List all thresholds."""
        return list(self.thresholds.values())

    def delete_threshold(self, name: str) -> bool:
        """Delete threshold."""
        if name in self.thresholds:
            del self.thresholds[name]
            if name in self._historical_data:
                del self._historical_data[name]
            return True
        return False
