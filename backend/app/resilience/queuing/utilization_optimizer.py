"""
Utilization Optimizer.

Optimizes resource utilization while maintaining queue stability.

Key principle: Keep utilization below 80% to prevent queue explosion
(from queuing theory - M/M/c queue becomes unstable near ρ=1).
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.optimize import minimize_scalar

from app.resilience.queuing.erlang_c import ErlangC

logger = logging.getLogger(__name__)

# Default Optimization Targets
DEFAULT_TARGET_UTILIZATION = 0.75  # Conservative target
DEFAULT_MAX_WAIT_TIME = 0.5  # Hours
DEFAULT_MIN_SERVICE_LEVEL = 0.80  # 80% immediate service


@dataclass
class OptimizationResult:
    """Utilization optimization result."""

    recommended_servers: int
    target_utilization: float
    actual_utilization: float
    expected_wait_time: float
    expected_queue_length: float
    service_level: float
    cost_savings_pct: float  # vs. current
    rationale: str


class UtilizationOptimizer:
    """
    Optimize resource utilization for scheduling.

    Balances:
    - Utilization (want high to reduce costs)
    - Queue length (want low for patient satisfaction)
    - Service level (want high for quality)
    """

    def __init__(self, erlang_calculator: ErlangC | None = None):
        """Initialize optimizer."""
        self.erlang = erlang_calculator or ErlangC()

    def optimize_utilization(
        self,
        arrival_rate: float,
        service_rate: float,
        current_servers: int,
        target_utilization: float = DEFAULT_TARGET_UTILIZATION,  # Conservative target
        max_wait_time: float = DEFAULT_MAX_WAIT_TIME,  # Maximum acceptable wait (hours)
        min_service_level: float = DEFAULT_MIN_SERVICE_LEVEL,  # Minimum 80% immediate service
    ) -> OptimizationResult:
        """
        Find optimal server count balancing utilization and service.

        Args:
            arrival_rate: λ - requests per hour
            service_rate: μ - service rate per server
            current_servers: Current number of servers
            target_utilization: Target utilization ratio
            max_wait_time: Maximum acceptable average wait time
            min_service_level: Minimum acceptable service level

        Returns:
            OptimizationResult with recommendations
        """
        logger.info(
            "Optimizing utilization: arrival_rate=%.2f, service_rate=%.2f, current=%d",
            arrival_rate,
            service_rate,
            current_servers,
        )
        # Calculate minimum servers for stability (ρ < 1)
        min_servers = int(np.ceil(arrival_rate / service_rate)) + 1

        logger.debug(
            "Minimum servers for stability: %d, target utilization: %.2f",
            min_servers,
            target_utilization,
        )
        # Calculate servers needed for target utilization
        servers_for_util = int(
            np.ceil(arrival_rate / (service_rate * target_utilization))
        )

        # Search for optimal servers meeting all constraints
        optimal_servers = None
        best_score = -1.0

        for num_servers in range(
            max(min_servers, servers_for_util), max(min_servers, servers_for_util) + 20
        ):
            result = self.erlang.calculate(arrival_rate, service_rate, num_servers)

            # Check constraints
            if result.avg_wait_time > max_wait_time:
                continue  # Violates wait time constraint
            if result.service_level < min_service_level:
                continue  # Violates service level

            # Score: balance high utilization with low wait time
            # Score = utilization × (1 - normalized_wait_time)
            normalized_wait = min(1.0, result.avg_wait_time / max_wait_time)
            score = result.utilization * (1.0 - normalized_wait)

            if score > best_score:
                best_score = score
                optimal_servers = num_servers

        if optimal_servers is None:
            # No solution found, use minimum stable
            optimal_servers = servers_for_util

        # Calculate final metrics
        final_result = self.erlang.calculate(
            arrival_rate, service_rate, optimal_servers
        )
        current_result = self.erlang.calculate(
            arrival_rate, service_rate, current_servers
        )

        # Calculate cost savings
        if current_servers > 0:
            cost_savings = (current_servers - optimal_servers) / current_servers * 100
        else:
            cost_savings = 0.0

        # Generate rationale
        if optimal_servers < current_servers:
            rationale = f"Reduce servers from {current_servers} to {optimal_servers} (over-staffed)"
        elif optimal_servers > current_servers:
            rationale = f"Increase servers from {current_servers} to {optimal_servers} (under-staffed)"
        else:
            rationale = f"Current staffing optimal at {current_servers} servers"

        return OptimizationResult(
            recommended_servers=optimal_servers,
            target_utilization=target_utilization,
            actual_utilization=final_result.utilization,
            expected_wait_time=final_result.avg_wait_time,
            expected_queue_length=final_result.avg_queue_length,
            service_level=final_result.service_level,
            cost_savings_pct=cost_savings,
            rationale=rationale,
        )

    def optimize_for_time_varying_demand(
        self,
        hourly_arrival_rates: list[float],  # 24 hours of arrival rates
        service_rate: float,
        current_servers: int,
    ) -> dict:
        """
        Optimize for time-varying demand (e.g., day vs night).

        Args:
            hourly_arrival_rates: Arrival rate for each hour of day
            service_rate: Service rate per server
            current_servers: Current staffing

        Returns:
            Dict with recommended staffing by time period
        """
        recommendations = {}

        # Analyze peak vs. off-peak
        peak_rate = max(hourly_arrival_rates)
        offpeak_rate = min(hourly_arrival_rates)
        avg_rate = np.mean(hourly_arrival_rates)

        # Optimize for each period
        peak_opt = self.optimize_utilization(peak_rate, service_rate, current_servers)
        offpeak_opt = self.optimize_utilization(
            offpeak_rate, service_rate, current_servers
        )
        avg_opt = self.optimize_utilization(avg_rate, service_rate, current_servers)

        return {
            "peak_period": {
                "arrival_rate": peak_rate,
                "recommended_servers": peak_opt.recommended_servers,
                "utilization": peak_opt.actual_utilization,
            },
            "offpeak_period": {
                "arrival_rate": offpeak_rate,
                "recommended_servers": offpeak_opt.recommended_servers,
                "utilization": offpeak_opt.actual_utilization,
            },
            "average": {
                "arrival_rate": avg_rate,
                "recommended_servers": avg_opt.recommended_servers,
                "utilization": avg_opt.actual_utilization,
            },
            "recommendation": (
                f"Use {peak_opt.recommended_servers} during peak, "
                f"{offpeak_opt.recommended_servers} during off-peak"
            ),
        }

    def calculate_utilization_risk(self, utilization: float) -> dict:
        """
        Assess risk level based on utilization.

        Args:
            utilization: Current utilization ratio

        Returns:
            Dict with risk assessment
        """
        if utilization < 0.60:
            risk_level = "low"
            risk_description = "Under-utilized - consider reducing capacity"
            color = "green"
        elif utilization < 0.80:
            risk_level = "optimal"
            risk_description = "Optimal utilization - stable queuing"
            color = "green"
        elif utilization < 0.90:
            risk_level = "elevated"
            risk_description = "Elevated risk - queue growth accelerating"
            color = "yellow"
        elif utilization < 0.95:
            risk_level = "high"
            risk_description = "High risk - queue becoming unstable"
            color = "orange"
        else:
            risk_level = "critical"
            risk_description = "CRITICAL - queue explosion imminent"
            color = "red"

        # Estimate queue growth factor
        # At ρ=0.9, queue is ~9x longer than at ρ=0.5
        if utilization < 1.0:
            queue_multiplier = utilization / (1.0 - utilization)
        else:
            queue_multiplier = float("inf")

        return {
            "utilization": utilization,
            "risk_level": risk_level,
            "risk_description": risk_description,
            "color": color,
            "queue_growth_factor": queue_multiplier,
            "recommended_action": (
                "Reduce load or add capacity" if utilization >= 0.90 else "Monitor"
            ),
        }

    def simulate_capacity_reduction(
        self,
        arrival_rate: float,
        service_rate: float,
        current_servers: int,
        reduction_pct: float,
    ) -> dict:
        """
        Simulate effect of reducing capacity.

        Args:
            arrival_rate: Current arrival rate
            service_rate: Service rate per server
            current_servers: Current servers
            reduction_pct: Percentage reduction (e.g., 0.10 = 10% reduction)

        Returns:
            Dict with before/after comparison
        """
        reduced_servers = int(current_servers * (1.0 - reduction_pct))
        reduced_servers = max(1, reduced_servers)  # At least 1 server

        current = self.erlang.calculate(arrival_rate, service_rate, current_servers)
        reduced = self.erlang.calculate(arrival_rate, service_rate, reduced_servers)

        is_viable = (
            reduced.utilization < 0.90
            and reduced.avg_wait_time < 1.0
            and reduced.service_level >= 0.70
        )

        return {
            "current_servers": current_servers,
            "reduced_servers": reduced_servers,
            "reduction_pct": reduction_pct * 100,
            "current_utilization": current.utilization,
            "reduced_utilization": reduced.utilization,
            "current_wait_time": current.avg_wait_time,
            "reduced_wait_time": reduced.avg_wait_time,
            "wait_time_increase": reduced.avg_wait_time - current.avg_wait_time,
            "current_service_level": current.service_level,
            "reduced_service_level": reduced.service_level,
            "is_viable": is_viable,
            "recommendation": (
                "Safe to reduce capacity"
                if is_viable
                else "Reduction would degrade service unacceptably"
            ),
        }
