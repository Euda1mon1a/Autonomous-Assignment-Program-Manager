"""
Equity and Fairness Metrics.

This module provides statistical measures for workload equity and fairness
in schedule assignments, including the Gini coefficient and Lorenz curve.

The Gini coefficient quantifies inequality in a distribution, with values
ranging from 0 (perfect equality) to 1 (perfect inequality). For medical
scheduling, a Gini coefficient below 0.15 indicates equitable workload
distribution.

Functions:
    - gini_coefficient: Calculate Gini coefficient for a distribution
    - lorenz_curve: Generate Lorenz curve coordinates
    - equity_report: Comprehensive equity analysis with recommendations
"""

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def gini_coefficient(values: list[float], weights: list[float] | None = None) -> float:
    """
    Calculate the Gini coefficient for a distribution of values.

    The Gini coefficient is a measure of statistical dispersion intended to
    represent inequality in a distribution. It ranges from 0 (perfect equality,
    where all values are the same) to 1 (perfect inequality, where one entity
    has everything).

    Formula: G = (Σᵢ Σⱼ |xᵢ - xⱼ|) / (2n² * μ)

    Where:
        - xᵢ, xⱼ are individual values
        - n is the number of values
        - μ is the mean of values

    Args:
        values: List of numeric values (e.g., hours worked by each provider)
        weights: Optional weights for each value (e.g., intensity multipliers).
                If provided, must be same length as values.

    Returns:
        float: Gini coefficient between 0.0 and 1.0

    Raises:
        ValueError: If values is empty, contains negative values, or weights
                   length doesn't match values length

    Examples:
        >>> gini_coefficient([10, 10, 10, 10])  # Perfect equality
        0.0
        >>> gini_coefficient([0, 0, 0, 100])     # Maximum inequality
        0.75
        >>> gini_coefficient([20, 30, 40], weights=[1.0, 1.5, 2.0])
        # Weighted calculation
    """
    if not values:
        raise ValueError("values list cannot be empty")

    if any(v < 0 for v in values):
        raise ValueError("values cannot contain negative numbers")

    # Handle weights
    if weights is not None:
        if len(weights) != len(values):
            raise ValueError(
                f"weights length ({len(weights)}) must match values length ({len(values)})"
            )
        if any(w < 0 for w in weights):
            raise ValueError("weights cannot contain negative numbers")

        # Apply weights to values
        weighted_values = [v * w for v, w in zip(values, weights)]
        arr = np.array(weighted_values, dtype=np.float64)
    else:
        arr = np.array(values, dtype=np.float64)

    # Handle edge cases
    if len(arr) == 1:
        return 0.0

    # All values are the same (perfect equality)
    if np.allclose(arr, arr[0]):
        return 0.0

    # All values are zero
    if np.allclose(arr, 0.0):
        return 0.0

    # Calculate Gini coefficient using the standard formula
    # G = (Σᵢ Σⱼ |xᵢ - xⱼ|) / (2n² * μ)
    n = len(arr)
    mean_value = np.mean(arr)

    # Calculate sum of absolute differences
    # Using broadcasting for efficient computation
    differences = np.abs(arr[:, np.newaxis] - arr[np.newaxis, :])
    sum_diff = np.sum(differences)

    # Calculate Gini coefficient
    gini = sum_diff / (2 * n * n * mean_value)

    return float(gini)


def lorenz_curve(values: list[float]) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate Lorenz curve coordinates for visualizing inequality.

    The Lorenz curve plots cumulative share of population (x-axis) against
    cumulative share of total value (y-axis). Perfect equality is represented
    by the 45-degree line y=x. The Gini coefficient equals twice the area
    between the Lorenz curve and the equality line.

    Args:
        values: List of numeric values to analyze

    Returns:
        tuple[np.ndarray, np.ndarray]: (x_coords, y_coords) where:
            - x_coords: Cumulative population share [0, 1]
            - y_coords: Cumulative value share [0, 1]

    Raises:
        ValueError: If values is empty or contains negative values

    Examples:
        >>> x, y = lorenz_curve([10, 20, 30, 40])
        >>> # x = [0.00, 0.25, 0.50, 0.75, 1.00]
        >>> # y = [0.00, 0.10, 0.30, 0.60, 1.00]
    """
    if not values:
        raise ValueError("values list cannot be empty")

    if any(v < 0 for v in values):
        raise ValueError("values cannot contain negative numbers")

    # Sort values in ascending order
    sorted_values = np.sort(np.array(values, dtype=np.float64))

    n = len(sorted_values)
    total = np.sum(sorted_values)

    # Handle all-zero case
    if np.allclose(total, 0.0):
        # Perfect equality (flat line at y=x)
        x_coords = np.linspace(0, 1, n + 1)
        y_coords = np.linspace(0, 1, n + 1)
        return x_coords, y_coords

    # Calculate cumulative shares
    cumulative_values = np.concatenate(([0], np.cumsum(sorted_values)))
    cumulative_share = cumulative_values / total

    # Population shares (0 to 1, with n+1 points)
    population_share = np.linspace(0, 1, n + 1)

    return population_share, cumulative_share


def equity_report(
    provider_hours: dict[str, float], intensity_weights: dict[str, float] | None = None
) -> dict[str, Any]:
    """
    Generate comprehensive equity analysis report for provider workloads.

    This function analyzes workload distribution across providers and generates
    actionable recommendations for rebalancing. It accounts for intensity
    differences (e.g., night shifts, high-acuity rotations) when provided.

    Args:
        provider_hours: Mapping of provider ID to total hours worked
        intensity_weights: Optional mapping of provider ID to intensity
                          multiplier (default 1.0). Higher values indicate
                          more demanding assignments.

    Returns:
        dict[str, Any]: Equity analysis report containing:
            - gini (float): Gini coefficient (0=perfect equality, 1=max inequality)
            - target_gini (float): Recommended threshold (0.15 for medical scheduling)
            - is_equitable (bool): True if gini < target_gini
            - mean_hours (float): Average hours per provider
            - std_hours (float): Standard deviation of hours
            - min_hours (float): Minimum hours assigned
            - max_hours (float): Maximum hours assigned
            - most_overloaded (str): Provider ID with highest intensity-adjusted hours
            - most_underloaded (str): Provider ID with lowest intensity-adjusted hours
            - overload_delta (float): How many hours above mean for most overloaded
            - underload_delta (float): How many hours below mean for most underloaded
            - recommendations (list[str]): Suggested rebalancing actions

    Raises:
        ValueError: If provider_hours is empty, contains negative values,
                   or intensity_weights keys don't match provider_hours keys

    Examples:
        >>> hours = {"A": 40, "B": 45, "C": 35, "D": 50}
        >>> report = equity_report(hours)
        >>> print(f"Gini: {report['gini']:.3f}")
        >>> print(f"Equitable: {report['is_equitable']}")
        >>> for rec in report['recommendations']:
        ...     print(rec)
    """
    if not provider_hours:
        raise ValueError("provider_hours cannot be empty")

    if any(h < 0 for h in provider_hours.values()):
        raise ValueError("provider_hours cannot contain negative values")

    # Validate intensity_weights if provided
    if intensity_weights is not None:
        if set(intensity_weights.keys()) != set(provider_hours.keys()):
            raise ValueError(
                "intensity_weights keys must match provider_hours keys exactly"
            )
        if any(w < 0 for w in intensity_weights.values()):
            raise ValueError("intensity_weights cannot contain negative values")

    # Extract values and apply weights
    provider_ids = list(provider_hours.keys())
    hours_values = [provider_hours[pid] for pid in provider_ids]

    if intensity_weights is not None:
        weights = [intensity_weights[pid] for pid in provider_ids]
    else:
        weights = None

    # Calculate Gini coefficient
    gini = gini_coefficient(hours_values, weights=weights)

    # Calculate statistics (on raw hours, not intensity-adjusted)
    hours_array = np.array(hours_values, dtype=np.float64)
    mean_hours = float(np.mean(hours_array))
    std_hours = float(np.std(hours_array))
    min_hours = float(np.min(hours_array))
    max_hours = float(np.max(hours_array))

    # Find most overloaded and underloaded providers using the same values
    # used for delta calculations to keep recommendations consistent
    if weights is not None:
        # Use intensity-adjusted hours for identification
        adjusted_hours = {
            pid: provider_hours[pid] * intensity_weights[pid] for pid in provider_ids
        }
        std_adjusted_hours = float(np.std(np.array(list(adjusted_hours.values()))))
    else:
        adjusted_hours = {pid: provider_hours[pid] for pid in provider_ids}
        std_adjusted_hours = std_hours

    most_overloaded = max(adjusted_hours, key=adjusted_hours.get)
    most_underloaded = min(adjusted_hours, key=adjusted_hours.get)

    mean_adjusted_hours = float(np.mean(list(adjusted_hours.values())))
    overload_delta = adjusted_hours[most_overloaded] - mean_adjusted_hours
    underload_delta = mean_adjusted_hours - adjusted_hours[most_underloaded]

    # Target Gini coefficient for medical scheduling (based on research)
    # Values below 0.15 indicate equitable distribution
    target_gini = 0.15
    is_equitable = gini < target_gini

    # Generate recommendations
    recommendations = []

    if not is_equitable:
        recommendations.append(
            f"High inequality detected (Gini={gini:.3f}). "
            f"Target is below {target_gini:.2f}."
        )

        # Recommend specific actions
        if overload_delta > mean_adjusted_hours * 0.2:  # 20% above mean
            recommendations.append(
                f"Provider {most_overloaded} is {overload_delta:.1f} hours "
                f"({(overload_delta / mean_adjusted_hours * 100):.1f}%) above average. "
                "Consider reducing their assignments."
            )

        if underload_delta > mean_adjusted_hours * 0.2:  # 20% below mean
            recommendations.append(
                f"Provider {most_underloaded} is {underload_delta:.1f} hours "
                f"({(underload_delta / mean_adjusted_hours * 100):.1f}%) below average. "
                "Consider increasing their assignments."
            )

        if std_adjusted_hours > mean_adjusted_hours * 0.25:  # High variation
            recommendations.append(
                f"High variation in workload (σ={std_adjusted_hours:.1f}, "
                f"{(std_adjusted_hours / mean_adjusted_hours * 100):.1f}% of mean). "
                "Review assignment algorithm for bias."
            )

        # Suggest rebalancing between extremes
        transfer_hours = min(overload_delta, underload_delta) / 2
        if transfer_hours > 0:
            recommendations.append(
                f"Consider transferring ~{transfer_hours:.1f} hours from "
                f"{most_overloaded} to {most_underloaded}."
            )

    else:
        recommendations.append(
            f"Workload distribution is equitable (Gini={gini:.3f} < {target_gini:.2f})."
        )

        # Even if equitable, flag significant outliers
        if overload_delta > mean_adjusted_hours * 0.3:
            recommendations.append(
                f"Note: Provider {most_overloaded} is still {overload_delta:.1f} hours "
                "above average. Monitor for burnout risk."
            )

    # Add intensity-specific recommendations if weights were provided
    if weights is not None:
        avg_weight = np.mean(weights)
        max_weight = max(intensity_weights.values())
        max_weight_provider = max(intensity_weights, key=intensity_weights.get)

        if max_weight > avg_weight * 1.5:
            recommendations.append(
                f"Provider {max_weight_provider} has high intensity factor "
                f"({max_weight:.2f}x). Ensure adequate rest between shifts."
            )

    return {
        "gini": gini,
        "target_gini": target_gini,
        "is_equitable": is_equitable,
        "mean_hours": mean_hours,
        "std_hours": std_hours,
        "min_hours": min_hours,
        "max_hours": max_hours,
        "most_overloaded": most_overloaded,
        "most_underloaded": most_underloaded,
        "overload_delta": overload_delta,
        "underload_delta": underload_delta,
        "recommendations": recommendations,
    }
