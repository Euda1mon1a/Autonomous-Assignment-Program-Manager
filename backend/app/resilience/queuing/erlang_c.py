"""
Erlang C Queuing Calculator.

Erlang C formula from telecommunications/call center queuing theory.
Calculates probability of queuing in M/M/c system (Markovian arrivals,
Markovian service, c servers).

Key insight: Queue length grows exponentially as utilization approaches 1.0.
This is why 80% utilization is the safety threshold.

Application to scheduling:
- Arrivals = patient/consult requests
- Servers = residents/faculty on duty
- Service time = consultation duration
"""

from dataclasses import dataclass
from math import factorial
from typing import Optional

import numpy as np
from scipy.optimize import fsolve
from scipy.special import factorial as scipy_factorial


@dataclass
class ErlangCResult:
    """Erlang C calculation result."""

    arrival_rate: float  # λ - arrivals per hour
    service_rate: float  # μ - service per hour per server
    num_servers: int  # c - number of servers
    traffic_intensity: float  # ρ = λ/(c*μ)
    utilization: float  # Same as traffic intensity
    prob_wait: float  # Erlang C - probability of waiting
    avg_queue_length: float  # L_q - average queue length
    avg_wait_time: float  # W_q - average wait time (hours)
    avg_system_time: float  # W - average time in system
    service_level: float  # Probability served within target time


class ErlangC:
    """
    Erlang C queuing calculator for M/M/c systems.

    Classic queuing theory from A.K. Erlang (1917), originally developed
    for telephone exchanges, now used in call centers and healthcare.
    """

    def calculate(
        self,
        arrival_rate: float,
        service_rate: float,
        num_servers: int,
        target_wait_time: float = 0.25,  # Target wait time for service level (hours)
    ) -> ErlangCResult:
        """
        Calculate Erlang C metrics.

        Args:
            arrival_rate: λ - requests per hour
            service_rate: μ - service rate per server per hour
            num_servers: c - number of servers (residents/faculty)
            target_wait_time: Target wait time for service level calculation

        Returns:
            ErlangCResult with all metrics
        """
        # Traffic intensity (utilization)
        rho = arrival_rate / (num_servers * service_rate)

        if rho >= 1.0:
            # System unstable - queue infinite
            return ErlangCResult(
                arrival_rate=arrival_rate,
                service_rate=service_rate,
                num_servers=num_servers,
                traffic_intensity=rho,
                utilization=rho,
                prob_wait=1.0,
                avg_queue_length=float("inf"),
                avg_wait_time=float("inf"),
                avg_system_time=float("inf"),
                service_level=0.0,
            )

        # Calculate Erlang C
        erlang_c = self._erlang_c_formula(arrival_rate, service_rate, num_servers)

        # Average queue length: L_q = Erlang_C * ρ/(1-ρ)
        avg_queue_length = erlang_c * rho / (1.0 - rho)

        # Average wait time: W_q = L_q / λ (Little's Law)
        avg_wait_time = avg_queue_length / arrival_rate if arrival_rate > 0 else 0.0

        # Average system time: W = W_q + 1/μ
        avg_system_time = avg_wait_time + (1.0 / service_rate)

        # Service level: probability wait time < target
        # P(W < t) = 1 - Erlang_C * exp(-c*μ*(1-ρ)*t)
        service_level = 1.0 - erlang_c * np.exp(
            -num_servers * service_rate * (1.0 - rho) * target_wait_time
        )

        return ErlangCResult(
            arrival_rate=arrival_rate,
            service_rate=service_rate,
            num_servers=num_servers,
            traffic_intensity=rho,
            utilization=rho,
            prob_wait=erlang_c,
            avg_queue_length=avg_queue_length,
            avg_wait_time=avg_wait_time,
            avg_system_time=avg_system_time,
            service_level=service_level,
        )

    def _erlang_c_formula(
        self,
        arrival_rate: float,
        service_rate: float,
        num_servers: int,
    ) -> float:
        """
        Calculate Erlang C probability.

        Erlang C = [A^c / c! * c/(c-A)] / [Σ(A^k/k!) + A^c/c! * c/(c-A)]

        where A = λ/μ (total offered load)

        Args:
            arrival_rate: λ
            service_rate: μ
            num_servers: c

        Returns:
            Probability of waiting (0-1)
        """
        A = arrival_rate / service_rate  # Total offered load

        if num_servers <= A:
            return 1.0  # System overloaded

        # Calculate numerator: A^c / c! * c/(c-A)
        try:
            # Use log to avoid overflow
            log_numerator = num_servers * np.log(A) - np.sum(
                np.log(np.arange(1, num_servers + 1))
            )
            log_numerator += np.log(num_servers / (num_servers - A))
            numerator = np.exp(log_numerator)
        except (OverflowError, ValueError):
            return 1.0

        # Calculate denominator: sum + numerator
        sum_terms = 0.0
        for k in range(num_servers):
            try:
                term = A**k / scipy_factorial(k, exact=False)
                sum_terms += term
            except (OverflowError, ValueError):
                continue

        denominator = sum_terms + numerator

        if denominator == 0:
            return 0.0

        erlang_c = numerator / denominator
        return min(1.0, max(0.0, erlang_c))  # Clamp to [0,1]

    def calculate_required_servers(
        self,
        arrival_rate: float,
        service_rate: float,
        target_utilization: float = 0.80,
        target_service_level: float = 0.80,  # 80% served immediately
    ) -> int:
        """
        Calculate number of servers needed to meet targets.

        Args:
            arrival_rate: λ - requests per hour
            service_rate: μ - service rate per hour per server
            target_utilization: Maximum desired utilization
            target_service_level: Minimum acceptable service level

        Returns:
            Required number of servers
        """
        # Minimum servers to meet utilization constraint
        min_servers_util = int(
            np.ceil(arrival_rate / (service_rate * target_utilization))
        )

        # Search for servers that meet service level
        for num_servers in range(min_servers_util, min_servers_util + 20):
            result = self.calculate(arrival_rate, service_rate, num_servers)

            if result.service_level >= target_service_level:
                return num_servers

        # If can't meet service level, return minimum for stability
        return min_servers_util

    def compare_scenarios(
        self,
        arrival_rate: float,
        service_rate: float,
        server_counts: list[int],
    ) -> list[ErlangCResult]:
        """
        Compare multiple staffing scenarios.

        Args:
            arrival_rate: λ
            service_rate: μ
            server_counts: List of server counts to compare

        Returns:
            List of ErlangCResult for each scenario
        """
        results = []

        for num_servers in server_counts:
            result = self.calculate(arrival_rate, service_rate, num_servers)
            results.append(result)

        return results

    def calculate_scale_effect(
        self,
        arrival_rate: float,
        service_rate: float,
        current_servers: int,
        additional_servers: int,
    ) -> dict:
        """
        Calculate effect of adding servers.

        Args:
            arrival_rate: λ
            service_rate: μ
            current_servers: Current server count
            additional_servers: Servers to add

        Returns:
            Dict with before/after metrics
        """
        before = self.calculate(arrival_rate, service_rate, current_servers)
        after = self.calculate(
            arrival_rate, service_rate, current_servers + additional_servers
        )

        wait_time_reduction = before.avg_wait_time - after.avg_wait_time
        queue_reduction = before.avg_queue_length - after.avg_queue_length

        return {
            "before_utilization": before.utilization,
            "after_utilization": after.utilization,
            "before_wait_time": before.avg_wait_time,
            "after_wait_time": after.avg_wait_time,
            "wait_time_reduction": wait_time_reduction,
            "wait_time_reduction_pct": (
                (wait_time_reduction / before.avg_wait_time * 100)
                if before.avg_wait_time > 0
                else 0
            ),
            "before_queue_length": before.avg_queue_length,
            "after_queue_length": after.avg_queue_length,
            "queue_reduction": queue_reduction,
            "service_level_improvement": after.service_level - before.service_level,
        }

    def find_optimal_servers(
        self,
        arrival_rate: float,
        service_rate: float,
        cost_per_server: float,
        cost_per_wait_hour: float,
        max_servers: int = 50,
    ) -> tuple[int, float]:
        """
        Find optimal number of servers minimizing total cost.

        Total cost = (servers × cost_per_server) + (wait_time × arrivals × cost_per_wait_hour)

        Args:
            arrival_rate: λ
            service_rate: μ
            cost_per_server: Cost per server ($/hour)
            cost_per_wait_hour: Cost per customer wait hour ($/hour)
            max_servers: Maximum servers to consider

        Returns:
            (optimal_servers, total_cost)
        """
        min_servers = int(np.ceil(arrival_rate / service_rate)) + 1
        min_cost = float("inf")
        optimal_servers = min_servers

        for num_servers in range(min_servers, max_servers + 1):
            result = self.calculate(arrival_rate, service_rate, num_servers)

            # Total cost
            server_cost = num_servers * cost_per_server
            wait_cost = result.avg_wait_time * arrival_rate * cost_per_wait_hour
            total_cost = server_cost + wait_cost

            if total_cost < min_cost:
                min_cost = total_cost
                optimal_servers = num_servers

        return optimal_servers, min_cost
