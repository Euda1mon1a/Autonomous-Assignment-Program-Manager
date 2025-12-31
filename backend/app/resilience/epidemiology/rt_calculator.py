"""
Effective Reproduction Number (Rt) Calculator.

Rt represents the average number of secondary burnout cases caused by each
primary case at time t.

- Rt < 1: Burnout declining
- Rt = 1: Steady state
- Rt > 1: Burnout growing

Uses Cori method (EpiEstim package) for real-time Rt estimation.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

import numpy as np
from scipy.stats import gamma

logger = logging.getLogger(__name__)

# Rt Interpretation Thresholds
RT_DECLINING_THRESHOLD = 0.9
RT_GROWING_THRESHOLD = 1.1
RT_STABLE_LOWER = 0.9
RT_STABLE_UPPER = 1.1

# Confidence Thresholds
MIN_CASES_FOR_CONFIDENCE = 10.0


@dataclass
class RtEstimate:
    """Rt estimate for a time period."""

    date: date
    rt_mean: float  # Mean Rt estimate
    rt_lower: float  # Lower 95% CI
    rt_upper: float  # Upper 95% CI
    confidence: float  # Confidence in estimate (0-1)
    interpretation: str  # "growing", "stable", "declining"


class RtCalculator:
    """
    Calculate effective reproduction number Rt.

    Estimates how many secondary burnout cases each case generates,
    accounting for current immunity (recovered) and interventions.
    """

    def __init__(
        self,
        serial_interval_mean: float = 7.0,  # Average time between successive cases
        serial_interval_std: float = 3.0,
    ):
        """
        Initialize Rt calculator.

        Args:
            serial_interval_mean: Mean serial interval (days)
            serial_interval_std: Std dev of serial interval (days)
        """
        self.serial_interval_mean = serial_interval_mean
        self.serial_interval_std = serial_interval_std

    def calculate_rt(
        self,
        incidence: list[int],  # Daily new cases
        window_size: int = 7,  # Sliding window for Rt estimation
    ) -> list[RtEstimate]:
        """
        Calculate Rt over time using Cori method.

        Args:
            incidence: List of daily new case counts
            window_size: Number of days for sliding window estimation

        Returns:
            List of RtEstimate objects, one per day
        """
        logger.info("Calculating Rt for %d days of incidence data (window=%d)", len(incidence), window_size)
        if len(incidence) < window_size:
            logger.warning("Insufficient data for Rt calculation: need >= %d days", window_size)
            return []

        estimates = []

        for t in range(window_size, len(incidence)):
            # Get window of recent cases
            window = incidence[max(0, t - window_size) : t]

            # Calculate Rt for this window
            rt_mean, rt_lower, rt_upper = self._estimate_rt_cori(window, t)

            # Determine confidence based on case counts
            total_cases = sum(window)
            confidence = min(1.0, total_cases / 10.0)  # Need ~10 cases for confidence

            # Interpret trend
            if rt_mean < 0.9:
                interpretation = "declining"
            elif rt_mean > 1.1:
                interpretation = "growing"
                logger.warning("Rt > 1.1 detected: burnout is spreading (Rt=%.2f)", rt_mean)
            else:
                interpretation = "stable"

            estimate = RtEstimate(
                date=date.today() + timedelta(days=t - len(incidence)),
                rt_mean=rt_mean,
                rt_lower=rt_lower,
                rt_upper=rt_upper,
                confidence=confidence,
                interpretation=interpretation,
            )

            estimates.append(estimate)

        return estimates

    def _estimate_rt_cori(
        self,
        incidence_window: list[int],
        t: int,
    ) -> tuple[float, float, float]:
        """
        Estimate Rt using Cori method (simplified).

        Rt(t) ≈ (new cases at t) / (expected cases based on serial interval)

        Args:
            incidence_window: Recent incidence counts
            t: Current time index

        Returns:
            (mean, lower_95, upper_95) Rt estimates
        """
        if not incidence_window or sum(incidence_window) == 0:
            return 1.0, 0.5, 2.0  # Default if no data

        # Calculate infectiousness (weighted sum of past cases)
        infectiousness = self._calculate_infectiousness(incidence_window)

        if infectiousness == 0:
            return 1.0, 0.5, 2.0

        # Current new cases
        current_cases = incidence_window[-1]

        # Rt estimate
        rt_mean = current_cases / infectiousness

        # Confidence interval using Gamma distribution
        # (Cori method uses Bayesian posterior with Gamma prior)
        shape = current_cases + 1  # Gamma shape parameter
        scale = 1.0 / infectiousness  # Gamma scale parameter

        # 95% CI
        rt_lower = gamma.ppf(0.025, shape, scale=scale)
        rt_upper = gamma.ppf(0.975, shape, scale=scale)

        return float(rt_mean), float(rt_lower), float(rt_upper)

    def _calculate_infectiousness(self, incidence: list[int]) -> float:
        """
        Calculate total infectiousness from past incidence.

        Uses discretized serial interval distribution to weight past cases.

        Args:
            incidence: Daily incidence counts

        Returns:
            Total infectiousness (expected new cases)
        """
        # Generate serial interval distribution
        serial_interval_dist = self._discretize_serial_interval(len(incidence))

        # Weight past cases by serial interval
        infectiousness = 0.0
        for i, cases in enumerate(incidence):
            # More recent cases have higher weight
            weight_idx = len(incidence) - 1 - i
            if weight_idx < len(serial_interval_dist):
                infectiousness += cases * serial_interval_dist[weight_idx]

        return infectiousness

    def _discretize_serial_interval(self, max_days: int) -> list[float]:
        """
        Create discrete serial interval distribution.

        Assumes Gamma distribution for serial interval.

        Args:
            max_days: Maximum days to discretize

        Returns:
            List of probabilities for each day
        """
        # Gamma distribution parameters from mean and std
        variance = self.serial_interval_std**2
        shape = self.serial_interval_mean**2 / variance
        scale = variance / self.serial_interval_mean

        # Discretize
        dist = []
        for day in range(max_days):
            # Probability mass for this day
            prob = gamma.cdf(day + 1, shape, scale=scale) - gamma.cdf(
                day, shape, scale=scale
            )
            dist.append(prob)

        # Normalize
        total = sum(dist)
        if total > 0:
            dist = [p / total for p in dist]

        return dist

    def calculate_rt_from_r0(
        self,
        r0: float,
        susceptible: int,
        total_population: int,
    ) -> float:
        """
        Calculate effective Rt from basic R0.

        Rt = R0 × (S / N)

        Where S/N is fraction still susceptible.

        Args:
            r0: Basic reproduction number
            susceptible: Current susceptible count
            total_population: Total population

        Returns:
            Effective reproduction number Rt
        """
        if total_population == 0:
            return 0.0

        susceptible_fraction = susceptible / total_population
        return r0 * susceptible_fraction

    def forecast_rt_trend(
        self,
        current_rt: float,
        intervention_effect: float,  # Multiplicative reduction (0-1)
        days_ahead: int = 14,
    ) -> list[float]:
        """
        Forecast Rt trend with intervention.

        Args:
            current_rt: Current Rt value
            intervention_effect: Reduction factor (e.g., 0.7 = 30% reduction)
            days_ahead: Days to forecast

        Returns:
            List of forecasted Rt values
        """
        forecast = []
        rt = current_rt

        for day in range(days_ahead):
            # Apply intervention effect with exponential decay
            decay_rate = 0.1  # Intervention takes ~10 days to full effect
            effective_reduction = 1.0 - (1.0 - intervention_effect) * (
                1.0 - np.exp(-decay_rate * day)
            )

            rt = rt * effective_reduction
            forecast.append(rt)

        return forecast

    def assess_outbreak_control(
        self,
        current_rt: float,
        rt_history: list[float],
        days_below_one: int = 7,
    ) -> dict:
        """
        Assess whether outbreak is under control.

        Args:
            current_rt: Current Rt value
            rt_history: Recent Rt values
            days_below_one: Required consecutive days Rt < 1

        Returns:
            Dict with control assessment
        """
        # Count consecutive days below 1
        consecutive_below = 0
        for rt in reversed(rt_history):
            if rt < 1.0:
                consecutive_below += 1
            else:
                break

        is_controlled = consecutive_below >= days_below_one and current_rt < 1.0

        # Calculate trend
        if len(rt_history) >= 7:
            recent_trend = np.mean(rt_history[-7:]) - np.mean(rt_history[-14:-7])
            trend_direction = (
                "decreasing"
                if recent_trend < -0.1
                else "increasing"
                if recent_trend > 0.1
                else "stable"
            )
        else:
            trend_direction = "insufficient_data"

        return {
            "is_controlled": is_controlled,
            "current_rt": current_rt,
            "consecutive_days_below_1": consecutive_below,
            "days_required": days_below_one,
            "trend_direction": trend_direction,
            "assessment": (
                "Outbreak under control"
                if is_controlled
                else f"Need {days_below_one - consecutive_below} more days Rt < 1"
            ),
        }
